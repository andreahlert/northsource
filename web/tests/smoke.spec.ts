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
