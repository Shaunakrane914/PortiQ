# Recorded CLI session

Runtime: `1c2cc5962de2d2c43c554bd7969ad372b84afbdc`. This is a genuine
Gemini-backed terminal call with local routing/cache disabled; no key is needed to read it.
The structural refactor has separate replay and regression evidence.

```powershell
portfolio-agent ask "How many portfolios do we have in total? Return just the count." --json
```

Selected fields from the complete [raw CLI output](cli-1.json):

```json
{
  "status": "answer",
  "answer": "Total portfolios: 13",
  "api_calls": 1,
  "tokens": 2422,
  "duration_ms": 1447.28,
  "cache": "disabled",
  "model": "gemini-3.1-flash-lite"
}
```

SQL executed:

```sql
SELECT count(*) FROM portfolios
```

Result: `13`. No API key or local username is included.
