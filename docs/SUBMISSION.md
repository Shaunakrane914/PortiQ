# Reviewer quick start

Repository: https://github.com/Shaunakrane914/PortiQ

The mandatory deliverable is the independent Python CLI. The original assignment is
preserved in `docs/assignment/README.md`. Runtime version is 0.1.0.

From a fresh clone, with Python 3.11+ and uv:

```powershell
uv sync --frozen --extra dev
Copy-Item .env.example .env
# Add your own GEMINI_API_KEY to .env; do not commit it.
uv run portfolio-agent init-db
uv run portfolio-agent doctor --live
uv run portfolio-agent ask "How many portfolios do we have in total?" --show-sql
uv run portfolio-agent exposure "Balanced Portfolio"
uv run portfolio-agent chat
```

On Linux/macOS substitute `cp .env.example .env`. Environment variables can be used
instead of a file. Run `--help` for configurable database/source/model paths.

Review in this order:

1. `src/portiq/agent.py`: genuine Gemini function calling and bounded orchestration.
2. `src/portiq/sql.py`: parsed SQL, authorizer and read-only resource boundary.
3. `src/portiq/exposure.py`: deterministic equity weight normalization and rounding.
4. `src/portiq/database.py`: validated, atomic source ingestion.
5. `src/portiq/evaluation.py`: independently executed result/financial references.
6. `tests/`, `reports/supplied-release.json`, `reports/extended-final.json` and acceptance notes.

The supplied benchmark passed 10/10 in each of two fresh release trials. The first
frozen 50-case extended suite scored 49/50. Full intermediate failures remain available.
Reports score structured tool evidence and strict routing, not every sentence of model
prose. The additional questions are author-created, not externally blind validation.

Run local checks without API credentials:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov=portiq
```

Live evaluations consume API quota and can take several minutes due to deliberate request
pacing. See README and EVALUATION.md for exact commands, model/configuration and limitations.
No web server, frontend or prebuilt database is needed. Optional dashboard/API work is deferred.
