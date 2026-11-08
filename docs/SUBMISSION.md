# Submission and demonstration

The mandatory assessment is the CLI. Review README -> CLI quick start -> frozen evaluator -> optional dashboard. Keep v0.1.1 available as the verified historical release; do not present its scores as fresh v0.2 evidence.

1. Clone the repository and run `uv sync --frozen`.
2. Copy `.env.example` to `.env`, set a local Gemini key, and run `uv run portfolio-agent init-db`.
3. Run `exposure "Balanced Portfolio"`, a read-only `sql` query, and `ask "List the names of Passive portfolios, alphabetically." --show-sql`.
4. Run `evaluate --output reports/local/supplied.json`; use `--suite extended` for the separate 50-question regression. These are genuine model calls; allow quota and service time.
5. Optionally run `uv sync --frozen --extra web` and `uv run portfolio-agent serve`, then open http://127.0.0.1:8000. Show reconciliation bases and warnings, a zero-call local answer, a cache hit, and an uncached genuine Gemini answer with visible SQL.

`chat --context --local --cache` demonstrates selected-portfolio follow-ups. Bare `chat` retains independent-question behavior. The experimental planner and its CLI flag were removed during cleanup; use the original orchestration.

For a credential-free container demo:

```powershell
docker build -t portiq:0.2 .
docker run --rm --name portiq-demo -p 127.0.0.1:8000:8000 portiq:0.2
```

For model access, pass a private runtime env file containing `GEMINI_API_KEY`, `PORTIQ_DEMO_TOKEN` and account-appropriate limits. If a token is configured, enter it through the small access-code dialog. Use a writable `/app/runtime` volume if a persistent quota ledger is required. Never publish `.env` or expose an unauthenticated model endpoint.

Public hosting is deferred. A real deployment needs an account, TLS/reverse proxy, explicit hosts/origins, external identity and per-user cost controls. No hosted URL or availability claim is supplied.

The [v0.2 evidence index](../reports/v0.2.0/README.md) identifies source revisions, complete and partial runs, actual requests/tokens, browser captures, Docker checks and final verification. The acceptance audit determines release readiness; do not infer it from a screenshot or a historical score.
