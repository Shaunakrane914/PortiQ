"""Actual HTTP soak and session-isolation checks; provider stub and live modes are explicit."""

import argparse
import hashlib
import json
import os
import secrets
import socket
import statistics
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import uvicorn
from google.genai import types
from pydantic import SecretStr

from portiq.agent import AgentResponse
from portiq.api import create_app
from portiq.config import Settings
from portiq.database import initialize
from portiq.evaluation import score_answer


def stub_response(**kwargs):
    time.sleep(0.1)
    contents = kwargs["contents"]
    if len(contents) == 1:
        name, args = "exposure_calculator", {"portfolio": "Balanced Portfolio"}
    else:
        name, args = (
            "respond",
            {
                "status": "answer",
                "answer": "Balanced Portfolio: Technology 61.11%; Financials 22.22%; "
                "Healthcare 16.67%.",
            },
        )
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(
                    role="model",
                    parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))],
                )
            )
        ],
        model_version="explicit-test-stub",
        usage_metadata=types.GenerateContentResponseUsageMetadata(total_token_count=5),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 600:
        parser.error("--seconds must be 1..600.")
    if args.output.exists():
        parser.error("Select a fresh output file; evidence is never replaced.")
    source = Path.cwd()
    token = secrets.token_urlsafe(32)
    rows = []
    health_times = []
    source_hashes = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path("src/portiq").glob("*.py")
    }
    started = datetime.now(UTC).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="portiq-soak-") as temporary:
        database = Path(temporary) / "portfolio.db"
        initialize(source, database)
        settings = (Settings.from_env() if args.live else Settings()).model_copy(
            update={
                "source": source,
                "database": database,
                "environment": "production",
                "max_concurrent_analyses": 4,
            }
        )
        if args.live:
            settings.require_key()
            settings = settings.model_copy(update={"request_interval": 6.5, "fallback_models": ()})
        else:
            settings = settings.model_copy(
                update={
                    "api_key": SecretStr("explicit-test-stub"),
                    "quota_path": Path(temporary) / "quota.db",
                    "rpm_limit": 120,
                    "rpm_window": 1.0,
                    "rpm_cooldown_seconds": 0.0,
                    "daily_requests": 10000,
                }
            )
        cases = json.loads((source / "evaluation/extended.json").read_text())["questions"]
        cases = (
            [c for c in cases if c["category"] == "hybrid"]
            if args.live
            else [
                {
                    "id": "soak",
                    "question": "Calculate sector exposure for Balanced Portfolio",
                    "ground_truth": {"parameters": {"portfolio_name": "Balanced Portfolio"}},
                }
            ]
            * 8
        )
        sessions = [None] * len(cases)

        def stub_client(**kw):
            return SimpleNamespace(
                models=SimpleNamespace(generate_content=stub_response), close=lambda: None
            )

        env = {"PORTIQ_ALLOWED_HOSTS": "127.0.0.1", "WEB_CONCURRENCY": "1", "UVICORN_WORKERS": "1"}
        with (
            patch.dict(os.environ, env),
            patch("portiq.model.genai.Client", stub_client)
            if not args.live
            else patch.dict(os.environ, {}),
        ):
            app = create_app(settings, token=token, rate_limit=10000)
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            address = f"http://127.0.0.1:{sock.getsockname()[1]}"
            server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False))
            thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
            thread.start()
            try:
                deadline = time.monotonic() + 15
                while not server.started:
                    if time.monotonic() > deadline:
                        raise RuntimeError("HTTP server startup timed out.")
                    time.sleep(0.05)
                analysis = app.state.analysis
                before = analysis.budget.used()
                headers = {"Authorization": "Bearer " + token}
                with httpx.Client(base_url=address, headers=headers, timeout=120) as client:
                    assert (
                        client.get(
                            "/api/portfolios", headers={"Authorization": "Bearer invalid"}
                        ).status_code
                        == 401
                    )
                    assert (
                        client.post("/api/ask", json={"question": "x", "unknown": 1}).status_code
                        == 422
                    )

                    def ask(index, turn):
                        case = cases[index]
                        question = case["question"]
                        if args.live and turn > 1:
                            name = case["references"][0]["parameters"]["portfolio_name"]
                            question = question.replace(name, "the selected portfolio")
                        start = time.perf_counter()
                        try:
                            response = client.post(
                                "/api/conversation",
                                json={
                                    "question": question,
                                    "session_id": sessions[index],
                                    "local": False,
                                    "cache": False,
                                },
                            )
                        except httpx.HTTPError as exc:
                            return {
                                "turn": turn,
                                "actor": index,
                                "case": case["id"],
                                "http_status": 0,
                                "passed": False,
                                "duration_ms": (time.perf_counter() - start) * 1000,
                                "error_type": type(exc).__name__,
                                "usage": "delivery unknown",
                            }
                        record = {
                            "turn": turn,
                            "actor": index,
                            "case": case["id"],
                            "http_status": response.status_code,
                            "duration_ms": (time.perf_counter() - start) * 1000,
                            "question_kind": "context follow-up"
                            if args.live and turn > 1
                            else "explicit identity",
                        }
                        if response.status_code == 200:
                            body = response.json()
                            sessions[index] = body["session_id"]
                            answer = AgentResponse.model_validate(body["response"])
                            scored = score_answer(settings, case, answer, profile_io=args.live)
                            record.update(
                                passed=scored["passed"],
                                failures=scored["failures"],
                                sdk_attempts=answer.api_calls,
                                reported_tokens=answer.tokens,
                                provider_metrics=answer.provider_metrics,
                                cache=answer.cache,
                                context_portfolio=answer.context_portfolio,
                                session_hash=hashlib.sha256(
                                    body["session_id"].encode()
                                ).hexdigest(),
                            )
                            if args.live:
                                record.update(
                                    actual=answer.model_dump(mode="json"),
                                    answer_verification=scored["answer_verification"],
                                    sql_efficiency=scored["sql_efficiency"],
                                )
                        else:
                            record.update(
                                passed=False, retry_after=response.headers.get("Retry-After")
                            )
                            body = response.json()
                            if "response" in body:
                                actual = body["response"]
                                record.update(
                                    sdk_attempts=actual["api_calls"],
                                    reported_tokens=actual["tokens"],
                                    provider_metrics=actual["provider_metrics"],
                                    error_kind=actual.get("error_kind"),
                                )
                        return record

                    start = time.perf_counter()
                    turn = 0
                    with ThreadPoolExecutor(max_workers=len(cases)) as pool:
                        while turn < 3 if args.live else time.perf_counter() - start < args.seconds:
                            turn += 1
                            futures = [pool.submit(ask, i, turn) for i in range(len(cases))]
                            probe = time.perf_counter()
                            assert client.get("/api/ready").status_code == 200
                            health_times.append((time.perf_counter() - probe) * 1000)
                            wave = [f.result() for f in futures]
                            rows.extend(wave)
                            args.output.with_suffix(".progress.json").write_text(
                                json.dumps({"complete": False, "rows": rows}, indent=2) + "\n",
                                encoding="utf-8",
                            )
                            print(
                                f"wave={turn} responses={len(wave)} "
                                f"answers={sum(r['passed'] for r in wave)}",
                                flush=True,
                            )
                            if args.live and any(not r["passed"] for r in wave):
                                break
                    recovered = ask(0, turn + 1) if not args.live else None
                    if recovered:
                        rows.append(recovered)
                    success = [r for r in rows if r["http_status"] == 200]
                    attempts = sum(r.get("sdk_attempts", 0) for r in rows)
                    active_sessions = [s for s in sessions if s]
                    checks = {
                        "all_accepted_answers_correct": bool(success)
                        and all(r["passed"] for r in success),
                        "only_expected_statuses": all(r["http_status"] in {200, 503} for r in rows),
                        "overflow_retry_after": all(
                            r.get("retry_after") == "1" for r in rows if r["http_status"] == 503
                        ),
                        "sessions_isolated": len(active_sessions) == len(set(active_sessions)),
                        "same_actor_session_stable": all(
                            len({r["session_hash"] for r in success if r["actor"] == i}) <= 1
                            for i in range(len(cases))
                        ),
                        "pool_bounded": len(analysis.backend_pool) <= 4,
                        "session_store_bounded": len(analysis.sessions.items) <= 100,
                        "ledger_matches_sdk_attempts": analysis.budget.used() - before == attempts,
                        "cache_disabled": all(r["cache"] == "disabled" for r in success),
                        "runtime_unchanged": all(
                            hashlib.sha256((Path("src/portiq") / p).read_bytes()).hexdigest() == h
                            for p, h in source_hashes.items()
                        ),
                        "recovered_after_load": recovered is None or recovered["passed"],
                        "live_protocol_complete": not args.live
                        or len(rows) == 9
                        and len(success) == 9,
                    }
                    durations = sorted(r["duration_ms"] for r in rows)
                    report = {
                        "mode": "real Gemini HTTP concurrency"
                        if args.live
                        else "real HTTP with explicit deterministic SDK stub; no provider calls",
                        "source_commit": subprocess.check_output(
                            ["git", "rev-parse", "HEAD"], text=True
                        ).strip(),
                        "runtime_sha256": source_hashes,
                        "started_utc": started,
                        "finished_utc": datetime.now(UTC).isoformat(),
                        "wall_ms": (time.perf_counter() - start) * 1000,
                        "model": settings.model if args.live else "explicit-test-stub",
                        "actors": len(cases),
                        "capacity": 4,
                        "checks": checks,
                        "passed": all(checks.values()),
                        "answers": len(success),
                        "busy_responses": sum(r["http_status"] == 503 for r in rows),
                        "quota_responses": sum(r["http_status"] == 429 for r in rows),
                        "non_success_responses": len(rows) - len(success),
                        "sdk_attempts": attempts,
                        "ledger_before": before,
                        "ledger_after": analysis.budget.used(),
                        "reported_tokens": sum(r.get("reported_tokens", 0) for r in rows),
                        "provider_calls": analysis.budget.used() - before if args.live else 0,
                        "p50_http_ms": statistics.median(durations),
                        "p95_http_ms": durations[int(0.95 * (len(durations) - 1))],
                        "max_readiness_ms": max(health_times),
                        "rows": rows,
                    }
            finally:
                server.should_exit = True
                thread.join(timeout=15)
                sock.close()
            report["checks"]["clean_shutdown"] = not thread.is_alive()
            report["passed"] = all(report["checks"].values())
            args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            args.output.with_suffix(".progress.json").unlink(missing_ok=True)
            print(
                json.dumps(
                    {k: v for k, v in report.items() if k not in {"rows", "runtime_sha256"}},
                    indent=2,
                )
            )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
