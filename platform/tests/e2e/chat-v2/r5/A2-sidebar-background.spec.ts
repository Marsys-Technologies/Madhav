import { test, expect } from '@playwright/test'

const CONSUME_URL = '/clients/482012f1-710e-4a25-994a-93821f5871aa/consume'

test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, 'requires super-admin session')

test('A.2 — sidebar background shows brand gradient (NOT solid black)', async ({ page }) => {
  await page.goto(CONSUME_URL)

  // Ensure sidebar is expanded (default collapsed=false, but guard against it)
  const sidebar = page.getByTestId('v2-conversation-sidebar')
  const expandBtn = page.getByTestId('v2-sidebar-expand')

  if (await expandBtn.isVisible()) {
    await expandBtn.click()
  }

  await expect(sidebar).toBeVisible()

  // Visual regression: sidebar should show through to the gradient
  await expect(page).toHaveScreenshot('a2-sidebar-with-gradient.png', { fullPage: false })

  // Programmatic check: sidebar computed background should NOT be solid zinc-950 (rgb(9,9,11))
  const computedBg = await sidebar.evaluate(el =>
    window.getComputedStyle(el).backgroundColor
  )

  // bg-zinc-950 resolves to rgb(9, 9, 11). Our fix uses rgba with alpha < 1.
  expect(computedBg).not.toBe('rgb(9, 9, 11)')
  expect(computedBg).toMatch(/rgba\(.*,.*0\.\d+\)/)
})
