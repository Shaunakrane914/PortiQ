const { defineConfig } = require("@playwright/test");
module.exports = defineConfig({
  testDir: "tests/browser",
  outputDir: "reports/local/playwright",
  reporter: [
    ["list"],
    ["json", { outputFile: "reports/local/browser-results.json" }],
  ],
  timeout: 45000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8020",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "uv run --extra gui portfolio-agent gui --port 8022",
      url: "http://127.0.0.1:8022/_stcore/health",
      reuseExistingServer: false,
      timeout: 30000,
      env: {
        GEMINI_API_KEY: "",
        STREAMLIT_SERVER_HEADLESS: "true",
        PORTIQ_DB: "portfolio_database.db",
        PORTIQ_QUOTA_DB: "reports/local/streamlit-quota.sqlite",
      },
    },
    {
      command: "uv run portfolio-agent serve --port 8020",
      url: "http://127.0.0.1:8020/api/health",
      reuseExistingServer: false,
      timeout: 30000,
      env: {
        ...(process.env.PORTIQ_WEB_LIVE === "1" ? {} : { GEMINI_API_KEY: "" }),
        PORTIQ_REQUEST_INTERVAL: "6.5",
        PORTIQ_RATE_LIMIT: "300",
      },
    },
    {
      command: "uv run portfolio-agent serve --port 8021",
      url: "http://127.0.0.1:8021/api/health",
      reuseExistingServer: false,
      timeout: 30000,
      env: {
        GEMINI_API_KEY: "",
        PORTIQ_DEMO_TOKEN: "browser-test-token",
        PORTIQ_RATE_LIMIT: "300",
      },
    },
  ],
});
