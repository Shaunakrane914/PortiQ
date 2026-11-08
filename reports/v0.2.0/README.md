# v0.2 evidence index

For the later CLI-only capture on `4b49d95`, see [8 November 2026 evidence](../cli-2026-11-08/README.md): **50/50 extended**, 92 SDK calls and 201,404 reported tokens. The assignment's supplied ten and this separate fifty are distinguished in the [current evaluation guide](../../docs/EVALUATION.md). The retained artifacts below remain historical captures.

The retained reports describe their recorded pre-cleanup runtime revisions. Cleanup commit `122dee6` intentionally removed the experimental planner and development artifacts. Do not interpret archived scores, test counts or manifests as fresh verification of the current code.

| Retained artifact | Meaning |
|---|---|
| `baseline.json`, `preservation.json` | Pre-upgrade baseline and preservation audit. |
| `supplied.json`, `extended.json` | Original-agent results from the completed pre-cleanup paired experiment: 10/10 and 50/50. |
| `semantic.json`, `ambiguity-regression.json` | Archived categorical 6/6 and targeted ambiguity 3/3 repetitions. |
| `web-live.json`, `web-live-final.json` | Earlier genuine uncached Gemini browser/API traces; screenshots removed from the current tree remain in Git history. |
| `final-ui/` | Retained offline browser checks and genuine local screenshots. |
| `clean-install.json`, `browser-final.json`, `replay-v011.json` | Earlier clean installation, browser and offline compatibility evidence. |
| `connectivity-probe.json`, `usage-summary.json` | Provider diagnostic and usage represented by archived reports. |
| `verification.json`, `evidence-audit.json`, `artifact-manifest.json`, `change-inventory.json` | Capture-time audit metadata for the earlier snapshot. The manifest includes intentionally removed files and is not a manifest of the current checkout. |

The complete earlier experiment (including 8/8 platform, experimental failures, failed provider run, raw records, local-cache samples and container checks) is preserved in the [pre-cleanup Git snapshot](https://github.com/Shaunakrane914/PortiQ/tree/ace58054c7a778817d68a7c1d81386b7dffd95e8/reports/v0.2.0). No deleted files need to be restored to run the supported application.

Current reproducible checks: `uv run pytest --cov=portiq`, `uv run ruff check .`, `uv run mypy src`, `npm run test:web`, and a fresh Docker build plus `scripts/container_smoke.py`. Local validation artifacts go under ignored `reports/local/`. Live model checks consume quota and must be identified separately from ordinary key-free tests.
