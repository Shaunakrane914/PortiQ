"""Opt-in deterministic checks of specific narrative claims, not a general prose judge."""

import math
import re
from typing import Any

NUMBER = re.compile(
    r"(?<![\w.])(?P<number>[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)"
    r"(?:\s*(?P<scale>million|billion|thousand|[mbk])\b)?",
    re.IGNORECASE,
)
SCALES = {"million": 1e6, "billion": 1e9, "thousand": 1e3, "m": 1e6, "b": 1e9, "k": 1e3}
NO_ROWS = re.compile(
    r"\b(?:there (?:are|is) (?:no|zero)\b[^.!?\n]{0,100}\bportfolios?\b|"
    r"no (?:matching )?portfolios?\b|(?:no|zero) results?\b|none (?:were )?found\b)",
    re.IGNORECASE,
)


def _plain(text: str) -> str:
    return " ".join(text.replace("*", "").replace("`", "").split())


def check_faithfulness(
    text: str,
    expected: list[dict[str, Any]],
    rules: list[str],
    portfolio_names: list[str],
    sector_names: list[str] | None = None,
) -> dict[str, Any]:
    """Check only configured claims; absent coverage is explicitly not_checked."""
    checks: list[dict[str, Any]] = []
    plain = _plain(text)

    def add(kind: str, truth: Any, actual: Any, passed: bool) -> None:
        checks.append({"kind": kind, "expected": truth, "actual": actual, "passed": passed})

    def mentions(term: str) -> bool:
        return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", plain, re.IGNORECASE))

    for rule in rules:
        if rule in {"scalar", "portfolio_count"}:
            scalar = next(
                (
                    e["rows"][0][0]
                    for e in expected
                    if "rows" in e
                    and len(e["rows"]) == 1
                    and len(e["rows"][0]) == 1
                    and isinstance(e["rows"][0][0], (int, float))
                ),
                None,
            )
            if scalar is None:
                raise ValueError("Scalar narrative assertion requires a numeric reference cell.")
            numbers: list[float | str] = []
            matching = []
            for match in NUMBER.finditer(plain):
                raw = match["number"].replace(",", "")
                scale = SCALES.get((match["scale"] or "").lower(), 1)
                value = float(raw) * scale
                precision = len(raw.partition(".")[2])
                tolerance = 0 if rule == "portfolio_count" else 0.5 * 10**-precision * scale
                numbers.append(value if math.isfinite(value) else match["number"])
                if math.isfinite(value) and abs(value - scalar) <= tolerance + 1e-6:
                    matching.append(value)
            add("numeric_claim_present", scalar, numbers, bool(matching))
            if rule == "portfolio_count":
                claims = re.findall(
                    r"(?<!\w)([+-]?\d+)\s+(?:total\s+)?portfolios?\b", plain, re.IGNORECASE
                )
                for claim in claims:
                    add("portfolio_count_claim", scalar, int(claim), int(claim) == scalar)
        elif rule == "portfolio_names":
            names = [
                row[0]
                for e in expected
                if e.get("columns") == ["portfolio_name"]
                for row in e["rows"]
            ]
            if not names:
                raise ValueError("Portfolio list assertion requires nonempty named reference rows.")
            for name in names:
                add("required_portfolio", name, mentions(name), mentions(name))
            for name in portfolio_names:
                if name not in names and mentions(name):
                    add("unexpected_portfolio", names, name, False)
        elif rule == "exposure":
            exposures = [e for e in expected if "sectors" in e]
            if len(exposures) != 1:
                raise ValueError("Exposure prose assertion supports one portfolio at a time.")
            exposure = exposures[0]
            for name in portfolio_names:
                if mentions(name):
                    add(
                        "portfolio_identity",
                        exposure["portfolio_name"],
                        name,
                        name == exposure["portfolio_name"],
                    )
            for sector in sector_names or list(exposure["sectors"]):
                pattern = re.compile(
                    r"(?<!\w)" + re.escape(sector) + r"(?!\w)[^\d%+\-\n]{0,60}"
                    r"([+-]?\d+(?:\.\d+)?)\s*%",
                    re.IGNORECASE,
                )
                for match in pattern.finditer(text):
                    claim = match[1]
                    tolerance = 0.5 * 10 ** -len(claim.partition(".")[2])
                    percentage = exposure["sectors"].get(sector)
                    add(
                        "sector_percentage",
                        {sector: percentage},
                        float(claim),
                        percentage is not None
                        and abs(float(claim) - percentage) <= tolerance + 1e-6,
                    )
        else:
            raise ValueError(f"Unknown narrative assertion: {rule}")
    nonempty = any(
        e.get("sectors") or (e.get("rows") and e["rows"] not in [[[0]], [[None]]]) for e in expected
    )
    if rules and nonempty and NO_ROWS.search(plain):
        add("contradictory_empty_claim", "nonempty reference", "claimed no results", False)
    failed = [c for c in checks if not c["passed"]]
    return {
        "status": "failed" if failed else "passed" if checks else "not_checked",
        "rules": rules,
        "checks": checks,
        "failures": [
            f"{c['kind']}: expected {c['expected']}, actual {c['actual']}" for c in failed
        ],
        "scope": "Limited configured assertions; unchecked prose is not certified.",
    }
