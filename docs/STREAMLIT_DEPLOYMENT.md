# Deploy the Streamlit interface

Use [Streamlit Community Cloud](https://share.streamlit.io/) for the existing native
Streamlit application. This is separate from the HTML dashboard on Render.

## Community Cloud settings

Sign in, select **Create app**, and use:

| Setting | Value |
| --- | --- |
| Repository | `Shaunakrane914/PortiQ` |
| Branch | `main` |
| Main file path | `deploy/streamlit/app.py` |
| Python version (Advanced settings) | `3.11` |
| App URL | Choose an available name, such as `portiq-analyst` |

The entry point uses the existing application and services. Its adjacent
`requirements.txt` installs `-e .[gui]` from the repository root, including the PortiQ
package and Streamlit. The editable install uses the checked-out source when code updates
arrive, rather than retaining an older installed package copy. Community Cloud checks
this directory before the root dependency
files, so it does not accidentally install only the base CLI from `uv.lock` or the
unchanged original-assignment `requirements.txt`.
See [dependency discovery](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

In **Advanced settings → Secrets**, enter the following TOML, replacing the placeholder
with the Gemini key already stored in your local `.env`. Do not publish the actual key
in GitHub, chat, screenshots or logs.

```toml
GEMINI_API_KEY = "replace-with-your-existing-key"
GEMINI_MODEL = "gemini-3.1-flash-lite"
PORTIQ_REQUEST_INTERVAL = "0"
PORTIQ_RPM_LIMIT = "12"
PORTIQ_DAILY_REQUESTS = "200"
```

Keep these as root-level entries; Streamlit exposes root secrets as environment
variables used by `Settings.from_env()`. The daily number is an application guard,
not a Google quota setting. Choose a guard appropriate to your Google project; deployments
sharing a key also share its provider quota. This app does not require a dashboard token
or an additional password. A public app lets visitors spend its configured provider quota.

Click **Deploy**. Follow the build log until the AI Analyst page opens. The host assigns
the public URL; no live deployment is claimed until that page has been verified.
See [deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
and [secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Troubleshoot analysis failures

The hosted application cannot access the `.env` on your computer. Copy the contents
of your private local `.streamlit/secrets.toml` into **Settings → Secrets**, save, and
reboot the app to replace the cached analytical service. Do not commit the secrets file.

Streamlit distinguishes a missing deployment key, rejected credentials/permissions,
rate limits, provider quota, the local daily guard and connection failures using fixed
messages. It never renders raw SDK exception text. An unclassified failure retains a
generic message. Cloud logs include a request ID/error category or exception class,
without keys, questions or provider payloads.

Browser-console Permissions-Policy warnings and blocked analytics requests are not
Gemini response diagnostics. Use **Manage app → Cloud logs** to investigate server
failures; browser logs alone cannot establish an API authentication or quota failure.

## Verify after deployment

1. Confirm AI Analyst opens first and all 13 portfolios are selectable.
2. With Local fast path and Exact cache off, ask **Count all portfolios**. It should
   return **13**, with a validated SQL result and genuine Gemini usage.
3. Enable **Detailed AI explanation** and repeat. It should retain the correct count
   and use Gemini to review the tool result; two SDK calls are typical.
4. Select Balanced Portfolio and ask for sector exposure. Check the Stock-only basis
   and that bonds are excluded from the exposure denominator.
5. Open the URL in a separate private window and confirm conversation history is isolated.

The entry point builds the database automatically from the supplied schema and CSVs.
Portfolio and quota files default to `.portiq/` in the checkout; there are no secrets
in those configured paths. Sessions/cache live in the single application process.
Community Cloud storage is not a durable quota ledger: replacement/redeployment can lose
local runtime files, and Google quotas still apply. Use the persistent-volume deployment
in [Operations](OPERATIONS.md) if durable accounting is required.

## Reproduce the cloud entry point locally

From the repository root:

```powershell
uv sync --frozen --extra gui
uv run --no-sync streamlit run deploy/streamlit/app.py
```

Keep `.env` local. If you use `.streamlit/secrets.toml` locally instead, it is ignored
by Git. Never commit that file. The existing `portfolio-agent gui` command remains available.
