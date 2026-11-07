# Engineering experiments

All current live work uses `gemini-3.1-flash-lite`, genuine typed function calling and static supplied data. Source revisions, suite/data/prompt hashes and exact request records are stored with each run. Author-created questions already observed are regression tests, not unseen validation.

## Existing orchestration versus one-call planning

**Hypothesis:** a single validated tool graph plus deterministic rendering can avoid a synthesis call while preserving correctness.

**Baseline:** original PortfolioAgent. **Alternative:** experimental OneCallAgent with bounded fallback for unusable plans. **Conditions:** paired supplied ten, frozen extended fifty and separate platform eight; alternating strategy order; one shared 6.5-second-paced SDK backend; no local path, cache or model fallback. Independent original reference/result/routing and limited narrative checks are retained.

The one-question preflight passed both strategies. The first broader attempt completed 131 records and stopped at its explicit 250-attempt budget after sustained provider/transport failures. Its supplied segment passed 10/10 existing and 9/10 experimental, using 21 and 11 SDK calls respectively. The experimental Technology-sector valuation query returned thirteen rows rather than eight: this is a semantic failure, not a routing-only penalty. Extended/platform failures in that operationally degraded attempt do not establish reasoning accuracy.

The fresh post-circuit comparison is stored separately in `paired-final/`; use its complete per-suite reports for current scores and latency. Never combine successes across runs. The same Technology-sector valuation regression has reproduced. **Decision:** original remains default; experimental remains opt-in regardless of call reduction. Security tests reject unsafe graphs/SQL for both paths. **Limits:** one trial per question, no isolated inference timer and no controlled historical-release speedup claim.

## Deterministic rendering versus synthesis

The existing strategy uses model synthesis with authoritative tool tables; the alternative renders validated results in Python. Scalar, list, exposure and hybrid cases exercise the difference. Rendering is explicit in response metadata. This comparison is coupled to planning strategy, so it does not isolate renderer-only token or latency effects. Wrong plan semantics remain wrong even with faithful deterministic formatting. No separate renderer speedup is claimed.

## Exact cache and local execution

**Hypothesis:** explicit deterministic capabilities and exact repeats need no model. **Baseline:** uncached local count/exposure/holdings/metadata. **Alternative:** exact same successful answers from the cache. Twenty paired repeats per capability, independent CSV references, warm filesystem; zero mocked or live backend calls.

Both modes passed 80/80 checks. Median/p95 Python wall time: local 3.90/5.15 ms; cache 2.06/2.84 ms. Samples and scope are in `local-cache.json`. This does not compare arbitrary model questions or include network/browser time. **Decision:** enable the small registry/cache visibly in the dashboard; leave original CLI/evaluation defaults unchanged. Version and session isolation tests protect correctness.

## Provider resilience

The initial comparison measured 36 successful SDK calls, 27 provider-transient errors, one timeout and 186 connection errors. A fresh-client diagnostic then succeeded in about 7.86 seconds. The root cause is unknown; neither provider outage nor poisoned connection pool is proven.

The response is a bounded consecutive-failure circuit, cooldown and client refresh, covered by deterministic fake-transport tests. Live later runs are separate operational observations, not proof of fault recovery under a controlled injected outage. Actual failed invocations are charged conservatively. Daily/auth failures suppress pointless retries; short-term quota/transient errors use bounded hints/backoff. No per-provider billing receipt is inferred.

## Deferred comparisons

| Experiment | Decision and evidence limit |
|---|---|
| Alternative Gemini models | Explicit configured sequential fallback implemented and fake-SDK tested; no fresh alternate-model accuracy/latency comparison. Availability/account quota is not assumed. |
| Full schema versus focused metadata | Existing focused SQL path preserved; no new isolated ablation. Nine tables do not justify retrieval infrastructure without evidence. |
| Sequential fallback versus hedging | Sequential behavior tested with actual-invocation instrumentation against fake SDKs; hedging deferred to avoid parallel quota spend. No live latency superiority claim. |
| Raw versus pacing-inclusive latency | Both recorded per SDK call and question; service wall time includes transport. Observational summaries only. |
| Public deployment | Local and CI Docker smoke verified; hosted service, external identity and multi-user cost controls deferred. |

Failed browser assertions, CI setup failures, the preflight and incomplete provider runs remain visible in history/evidence. Corrections are accompanied by regression checks; reports are not rewritten to look successful.
