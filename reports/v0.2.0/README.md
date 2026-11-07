# v0.2 evidence index

Runtime source `2bef3c4314b6132344c1709589afe1f0cc0878de`; release/evidence revision is recorded separately. Fresh baseline: `83e43d4e7bf0f83c606ccdc330056ab7f3719265` (v0.1.1). Historical evidence and the original report index remain unchanged.

| Artifact | Meaning |
|---|---|
| `baseline.json` | Fresh pre-edit 148-pass baseline, 94.04% coverage, no pre-existing failures and canonical protected-file blobs. |
| `preservation.json` | All 78 protected files, original tests/workflow and v0.1.1 tag checked unchanged. |
| `paired-final/` | Separate fresh live paired run after circuit implementation; six complete per-suite reports. Original 10/10, 50/50, 8/8; experimental 9/10, 50/50, 7/8. No provider failures; 201 SDK calls, 535,073 reported tokens. |
| `paired-outage/progress.json`, `summary.json` | Incomplete initial run: 131 records, 250 SDK calls (36 success, 27 transient, one timeout, 186 connection errors). Not a completed accuracy comparison. |
| `planner-preflight/` | Earlier one-question genuine live check, not the full benchmark. |
| `connectivity-probe.json` | Fresh-client successful diagnostic after failed transport run; does not establish the failure's cause. |
| `local-cache.json` | Independent CSV verification of four capabilities, twenty paired repeats, 160 correct checks, zero model calls. |
| `clean-install.json` | Fresh Git archive, isolated Python 3.11, key-free base CLI without FastAPI, full tests/static checks. |
| `container-acceptance.json` | Corrected explicit-allowlist image, UID 10001, healthy HTTP/archive scores, exclusions and graceful shutdown. Earlier container records are intermediate development checks. |
| `browser-final.json`, `screenshots/` | Genuine local Chromium checks/captures, including safe labels/context/cache/mobile. No model call in the offline run. |
| `web-live.json` | Separate genuine uncached Gemini question through browser and API; revision and actual SQL/call/token evidence included. |
| `browser-development.json`, `container-development.json` | Earlier development evidence, including failed browser selectors; not final acceptance. |

Source report hashes describe captured bytes. Windows checkouts may normalize new JSON line endings; final manifests also record canonical Git blobs. Model service time is SDK wall time including transport, separate from actual pacing and retry backoff. Unknown token usage is not inferred. Case scores, routing and limited narrative checks remain separate.

`supplied.json` and `extended.json` are byte-identical aliases of this paired run's existing-strategy reports for the read-only API allowlist; they are not additional runs. `paired-analysis.json` supplies summary tables and separates the one focused planning step from repair. The combined raw record file retained a progress-only false completion marker; authoritative per-suite reports are complete. Raw evidence is preserved; future helper output fixes the marker and metric names.

The experimental planner is deliberately not default: Technology-sector valuation returned thirteen rows versus the reference eight in both broader attempts. The new platform ambiguity question also triggered an unjustified portfolio guess. Lower request counts do not override a demonstrated semantic failure. The original planner remains available and default. No answers are stitched between failed and later runs. See `docs/EXPERIMENTS.md` and the final acceptance audit for decisions and limitations.


Additional evidence: `semantic.json` (fresh categorical repeats), `ambiguity-regression.json` (targeted repetitions), `ambiguity-precheck.json` (separate initial check), `replay-v011.json` (59 old tool results, zero mismatches, offline only), `verification.json` (test/coverage/CI), and `final-ui/` (latest composition/archived-evidence captures). Earlier captures remain unchanged. Final genuine UI evidence uses `web-live-final.json` and distinct screenshot names.


`evidence-audit.json` verifies all 136 paired records, contiguous actual SDK attempts, current Python/source hashes and aliases. `artifact-manifest.json` records captured bytes and canonical Git blobs; `verification.json` is the mutable final audit metadata. No existing release evidence is overwritten.
