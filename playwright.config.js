const { defineConfig } = require("@playwright/test");
module.exports = defineConfig({
  testDir: "tests/browser",
  outputDir: "reports/local/playwright",
  reporter: [["list"], ["json", { outputFile: "reports/local/browser-results.json" }]],
  timeout: 45000,
  workers: 1,
  use: { baseURL: "http://127.0.0.1:8000", viewport: { width: 1440, height: 1000 }, trace: "retain-on-failure" },
  webServer: [{
    command: "uv run portfolio-agent serve --port 8000",
    url: "http://127.0.0.1:8000/api/health",
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
    env: { ...(process.env.PORTIQ_WEB_LIVE === "1" ? {} : {GEMINI_API_KEY: ""}), PORTIQ_REQUEST_INTERVAL: "6.5", PORTIQ_RATE_LIMIT: "300" }
  },{
    command: "uv run portfolio-agent serve --port 8011",
    url: "http://127.0.0.1:8011/api/health",
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
    env: { GEMINI_API_KEY: "", PORTIQ_DEMO_TOKEN: "browser-test-token", PORTIQ_RATE_LIMIT: "300" }
  }]
});
