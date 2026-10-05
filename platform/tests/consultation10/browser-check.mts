import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
const browser = await chromium.launch({ headless: true });
const errors: string[] = [];
const results: unknown[] = [];
for (const viewport of [
  { width: 1440, height: 1000 },
  { width: 390, height: 844 },
]) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/api/**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ conversations: [] }),
    }),
  );
  await page.goto(
    "http://127.0.0.1:3188/tests/consultation10/browser/index.html",
  );
  await page
    .getByRole("textbox", { name: "Ask the chart" })
    .fill("When should I take on a new commitment?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await page
    .locator('[data-testid="pp-turn"][data-turn-status="settled"]')
    .waitFor();
  const bounds = await page
    .locator('[data-testid="pp-main-column"]')
    .boundingBox();
  const input = await page
    .getByRole("textbox", { name: "Ask the chart" })
    .boundingBox();
  assert(bounds && input);
  assert(bounds.width >= (viewport.width < 900 ? 330 : 1000));
  assert(input.y + input.height < viewport.height);
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
  assert.equal(await page.locator(".pp-workspace-panel:visible").count(), 0);
  await page.screenshot({
    path: `../Assets/screenshots/consultation10/${viewport.width}-closed.png`,
    fullPage: true,
  });
  await page
    .locator('.pp-page-actions button[aria-label="Open evidence"]')
    .click();
  assert.deepEqual(await page.getByRole("tab").allTextContents(), [
    "Grounding",
    "Windows",
    "History",
  ]);
  await page.getByRole("tab", { name: "Windows", exact: true }).click();
  assert((await page.locator(".pp-prediction-card").count()) > 0);
  await page.getByRole("tab", { name: "Grounding", exact: true }).click();
  await page.screenshot({
    path: `../Assets/screenshots/consultation10/${viewport.width}-grounding.png`,
    fullPage: true,
  });
  if (viewport.width < 900) {
    assert.equal(
      await page.getByRole("dialog", { name: "Evidence" }).count(),
      1,
    );
    await page.keyboard.press("Escape");
  } else
    await page
      .getByRole("button", { name: "Close evidence", exact: true })
      .click();
  assert.equal(await page.locator(".pp-workspace-panel:visible").count(), 0);
  await page.getByLabel("Grounding placement").selectOption("inline");
  assert(await page.locator(".pp-inline-grounding").isVisible());
  await page
    .getByRole("button", { name: "Show page titles in English" })
    .click();
  assert.match(
    (await page.getByRole("heading", { level: 1 }).textContent()) ?? "",
    /^Consultation/,
  );
  if (viewport.width >= 900) {
    await page
      .locator('.pp-page-actions button[aria-label="Open evidence"]')
      .click();
    await page.getByRole("button", { name: "Pin evidence open" }).click();
    await page.reload();
    assert.equal(
      await page.locator('.pp-panel-right[data-pinned="true"]').count(),
      1,
    );
    assert.equal(
      await page.locator(".pp-panel-right .pp-workspace-panel:visible").count(),
      1,
    );
    await page.getByRole("button", { name: "Release evidence pin" }).click();
  }
  if (viewport.width < 900) {
    await page.setViewportSize({ width: 390, height: 480 });
    await page.getByRole("textbox", { name: "Ask the chart" }).focus();
    await page.waitForFunction(
      () =>
        document
          .querySelector(".pp-consultation")
          ?.getAttribute("data-compact-viewport") === "true",
    );
    const compactInput = await page
      .getByRole("textbox", { name: "Ask the chart" })
      .boundingBox();
    assert(compactInput && compactInput.y + compactInput.height < 480);
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
    );
    await page.screenshot({
      path: "../Assets/screenshots/consultation10/390-keyboard-sized.png",
      fullPage: true,
    });
  }
  results.push({
    viewport,
    mainWidth: bounds.width,
    composerVisible: true,
    noOverflow: true,
    defaultClosed: true,
    threeTabs: true,
    inlineGrounding: true,
    languageToggle: true,
    compactViewport: viewport.width < 900,
  });
  await context.close();
}
await browser.close();
assert.deepEqual(errors, []);
await writeFile(
  "../00_ARCHITECTURE/briefs/consultation10/BROWSER_VERIFICATION.json",
  JSON.stringify(
    { testOnlyFictionalData: true, actualComponents: true, results, errors },
    null,
    2,
  ),
);
console.log(JSON.stringify(results));
