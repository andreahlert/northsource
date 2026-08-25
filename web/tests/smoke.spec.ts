import { expect, test } from "@playwright/test";

test("home search leads to the HS6 result page", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("data-version")).toContainText("2026-06");
  const box = page.getByPlaceholder("What do you import from the US? e.g. cheese, steel coils, 8471");
  await box.fill("cheese");
  const first = page.getByTestId("search-result").first();
  await expect(first).toContainText("040610");
  await first.click();
  await expect(page).toHaveURL(/\/hs\/040610$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("040610");
});

test("result page pins the US row and filters alternatives", async ({ page }) => {
  await page.goto("/hs/040610");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("040610");
  await expect(page.getByTestId("surtax-badge")).toContainText("25%");
  const us = page.getByTestId("us-row");
  await expect(us).toHaveCount(1);
  await expect(us).toContainText("current source");
  await expect(page.locator("tbody tr").first()).toHaveAttribute("data-testid", "us-row");
  await expect(page.getByTestId("alt-row")).toHaveCount(4);
  await page.getByTestId("filter-fta").check();
  await expect(page.getByTestId("alt-row")).toHaveCount(3);
  await page.getByTestId("filter-supplies").check();
  await expect(page.getByTestId("alt-row")).toHaveCount(1);
  await expect(page.getByTestId("alt-row").first()).toContainText("France");
  await expect(us).toHaveCount(1);
  await expect(page.getByTestId("find-suppliers").first()).toHaveAttribute("href", "/hs/040610/FRA");
  await expect(page).toHaveTitle("Alternatives to US cheese suppliers for Canada | HS 040610");
});

test("country page renders chart, tariff card and external links", async ({ page }) => {
  await page.goto("/hs/040610/FRA");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("France");
  await expect(page.getByTestId("import-chart").locator("svg.recharts-surface")).toBeVisible();
  await expect(page.getByTestId("tariff-card")).toContainText("CEUT");
  await expect(page.getByTestId("tariff-card")).toContainText("CETA");
  const links = page.getByTestId("external-link");
  await expect(links).toHaveCount(4);
  for (const a of await links.all()) {
    expect(await a.getAttribute("href")).toMatch(/^https:\/\//);
    expect(await a.getAttribute("target")).toBe("_blank");
  }
  await expect(page.getByText("northsource does not verify suppliers")).toBeVisible();
  await page.goto("/hs/040610/USA");
  await expect(page.getByTestId("tariff-card")).toContainText("CUSMA");
  await page.goto("/hs/040610/ZZZ");
  await expect(page.getByText("404")).toBeVisible();
});
