# v0.2 engineering acceptance audit

Runtime source: `2bef3c4314b6132344c1709589afe1f0cc0878de`. Final evidence/release revision is recorded separately in the verification manifest. The original v0.1.1 release remains historical evidence, not a score inherited by changed code.

| Area | Evidence and decision |
|---|---|
| Preserve assessment | 78 baseline-protected files match canonical Git blobs; every original test file and original four-job workflow unchanged; v0.1.1 annotated tag unchanged. |
| Mandatory CLI | Fresh isolated Python 3.11 install initializes data, runs doctor/exposure with no key and no FastAPI; all original tests retained. Genuine Gemini evaluated separately. |
| SQL safety | Existing policy unchanged; additive timings only. Read-only/authorizer/parser/resource tests plus malicious one-call graph checks pass. |
| Financial correctness | Shared original stock-only exposure; independent CSV reconciliation checks across all thirteen portfolios and malformed/mixed-currency cases. No inferred FX/cash/AUM basis. |
| Rendering | Deterministic scalar/table/list/exposure/hybrid output from validated results; original synthesis still available; authority remains structured tools. |
| Efficient planning | Experimental one-call implemented and measured; reproduced Technology-sector valuation error means it remains opt-in. Valid SQL is insufficient for semantic promotion. |
| Local/cache | Explicit four-capability registry; 160 independent CSV checks pass with zero SDK calls. Cache TTL/LRU/deep-copy/context/data/rebuild isolation tests pass; model evaluation bypasses both paths. |
| Provider resilience | Actual SDK invocations charged, reported usage separated from unknowns, bounded retries/hints and optional fallback; atomic shared-file reservations tested across connections. Consecutive-failure circuit tested. No global provider-quota claim. |
| Conversation | Opt-in bounded history, validated selected portfolio, clarification/ordinal handling and session isolation; browser fragment-switch/follow-up regression passes. Ephemeral capability sessions are not user authentication. |
| API | Typed bounds, token/origin/host/rate/request IDs, generic redacted errors and allowlisted reports; key-free HTTP tests pass. Single-worker demo scope explicit. |
| Dashboard | Eight offline Playwright checks pass; all six views captured from real local backend. Malicious labels remain text, mobile view has no page overflow, stale view and token restoration regressions covered. Genuine model/browser evidence is separately labeled. |
| Docker | Actual image built and healthy; UID 10001; no embedded `.env`; dashboard, portfolios, exposure/reconciliation and missing-key 503 verified over HTTP. Public deployment deferred. |
| Quality | 204 tests passed, two live skips; 91.80% line coverage; Ruff and strict mypy clean. One TestClient deprecation warning remains. Four Python/OS CI jobs plus platform browser/container job pass at runtime source. |
| Live acceptance | Fresh paired run and categorical/ambiguity checks must finish before a release decision. Partial operational-failure evidence is retained and never stitched. |
| Documentation | Assignment-first README, CLI/API/dashboard/Docker commands, experiments, security, performance and limitations updated; historical report index remains unchanged. |

Coverage declined from 94.04% to 91.80% as optional API/server/services were added; no old test was deleted or weakened. Browser/container checks cover integration paths outside unit line coverage. This is a disclosed measurement, not proof of completeness.

The first comparison's extended failures were dominated by provider/transport errors, while its supplied one-call error was genuinely semantic. A fresh-client probe succeeded; cause remains unproven. The new circuit is a conservative bounded response. The final live audit must distinguish operational failures, wrong results, routing penalties and unchecked prose.

Deferred: public deployment, multi-user identity/per-user quotas, hedging, alternative-model live comparison, isolated schema-context ablations and externally authored blind questions. These do not replace the mandatory assessment. No release readiness is declared until fresh core live targets, final CI and evidence preservation are checked.
