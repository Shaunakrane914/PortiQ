const { test, expect } = require("@playwright/test");

test.beforeEach(async ({ page }) => {
  await page.goto("http://127.0.0.1:8022");
  await expect(page.getByRole("heading", { name: "AI Analyst", exact: true })).toBeVisible();
});

test("Streamlit matches the workspace and keeps model controls explicit", async ({ page }) => {
  await expect(page.getByText("PORTFOLIO INTELLIGENCE", { exact: true })).toBeVisible();
  await expect(page.getByRole("checkbox", { name: "Local fast path" })).not.toBeChecked();
  await expect(page.getByRole("checkbox", { name: "Exact cache" })).not.toBeChecked();
  await expect(page.getByRole("checkbox", { name: "Detailed AI explanation", exact:true })).not.toBeChecked();
  await page.getByText("Local fast path", { exact: true }).click();
  await page.getByRole("textbox", { name: "Ask PortiQ", exact: true }).fill("Count all portfolios");
  await page.getByRole("button", { name: /^Analyze/ }).click();
  await expect(page.getByText("Total portfolios: 13", { exact: true })).toBeVisible();
  await expect(page.getByText(/0 SDK calls/)).toBeVisible();
  await page.getByRole("button", { name: "New conversation", exact: true }).click();
  await expect(page.getByText("Total portfolios: 13", { exact: true })).toHaveCount(0);
});

test("Streamlit smarter mode disables local/cache while preserving the question", async ({ page }) => {
  await page.getByText("Local fast path",{exact:true}).click();
  await page.getByRole("textbox",{name:"Ask PortiQ",exact:true}).fill("Count all portfolios");
  await page.getByText("Detailed AI explanation",{exact:true}).click();
  await expect(page.getByRole("checkbox",{name:"Local fast path"})).toBeDisabled();
  await expect(page.getByRole("checkbox",{name:"Exact cache"})).toBeDisabled();
  await expect(page.getByRole("checkbox",{name:"Local fast path"})).not.toBeChecked();
  await expect(page.getByRole("textbox",{name:"Ask PortiQ",exact:true})).toHaveValue("Count all portfolios");
  await page.getByRole("button",{name:/^Analyze/}).click();
  await expect(page.getByText("Analysis is temporarily unavailable. Please try again later.",{exact:true})).toBeVisible();
  await page.getByText("Detailed AI explanation",{exact:true}).click();
  await expect(page.getByRole("checkbox",{name:"Local fast path"})).toBeEnabled();
});

test("Streamlit shares portfolio selection across all four views", async ({ page }) => {
  await page.getByText("02 Overview", { exact: true }).click();
  await expect(page.getByTestId("stDataFrame")).toBeVisible();
  await page.getByTestId("stSelectbox").getByRole("button", { name: "Open", exact: true }).click();
  await page.getByRole("option", { name: "Balanced Portfolio", exact: true }).click();
  await page.getByText("03 Portfolio Explorer", { exact: true }).click();
  await expect(page.getByRole("heading", { name: "Equity sector exposure", exact: true })).toBeVisible();
  await expect(page.getByRole("combobox")).toHaveValue("Balanced Portfolio");
  await page.getByText("04 Reconciliation", { exact: true }).click();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Export reconciliation CSV", exact: true }).click(),
  ]);
  expect(download.suggestedFilename()).toBe("reconciliation.csv");
  await page.getByText("01 AI Analyst", { exact: true }).click();
  await expect(page.getByRole("combobox")).toHaveValue("Balanced Portfolio");
});

test("Streamlit supports mobile navigation and renders questions as text", async ({ page, browser }) => {
  await page.getByRole("textbox", { name: "Ask PortiQ", exact: true }).fill("<img src=x onerror=alert(1)>");
  await page.getByRole("button", { name: /^Analyze/ }).click();
  await expect(page.getByText("Analysis is temporarily unavailable. Please try again later.", { exact: true })).toBeVisible();
  await expect(page.locator(".message img")).toHaveCount(0);
  const text = await page.locator("body").innerText();
  for (const privateValue of ["Shaunak", "PL Capital", "GEMINI_API_KEY"]) expect(text).not.toContain(privateValue);
  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  try {
    await mobile.goto("http://127.0.0.1:8022");
    await mobile.getByRole("heading", { name: "AI Analyst", exact: true }).waitFor();
    expect(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
    await mobile.getByRole("button", { name: "Expand sidebar", exact: true }).click();
    await mobile.getByText("02 Overview", { exact: true }).click();
    await expect(mobile.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
  } finally {
    await mobile.close();
  }
});
