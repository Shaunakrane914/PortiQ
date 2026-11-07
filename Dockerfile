FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --extra web --no-editable --no-cache
COPY data ./data
COPY database_schema.sql ground_truth_dataset.json ./
COPY evaluation ./evaluation
COPY reports/v0.1.1/supplied.json \
    reports/v0.1.1/extended.json \
    reports/v0.1.1/semantic.json \
    reports/v0.1.1/ambiguity-regression.json \
    reports/v0.1.1/verification.json ./reports/v0.1.1/
COPY reports/v0.2.0/supplied.json \
    reports/v0.2.0/extended.json \
    reports/v0.2.0/semantic.json \
    reports/v0.2.0/ambiguity-regression.json \
    reports/v0.2.0/verification.json ./reports/v0.2.0/
RUN test ! -e /app/reports/local && test ! -e /app/.env \
    && test ! -e /app/node_modules && test ! -e /app/reports/v0.2.0/paired-outage
RUN groupadd --gid 10001 portiq && useradd --uid 10001 --gid portiq --no-create-home portiq \
    && mkdir /app/runtime && chown portiq:portiq /app/runtime
ENV PATH="/app/.venv/bin:${PATH}" PORTIQ_DB=/app/runtime/portfolio.db \
    PORTIQ_SOURCE=/app PORTIQ_QUOTA_DB=/app/runtime/quota.sqlite PORTIQ_DAILY_REQUESTS=100 \
    PORTIQ_HOST=0.0.0.0 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=2)"]
ENTRYPOINT ["python", "-m", "portiq.server"]
