import { expect, test, type Page } from '@playwright/test'

const viewports = [
  { width: 1440, height: 900 },
  { width: 1280, height: 720 },
  { width: 390, height: 667 },
  { width: 320, height: 568 },
]

async function expectFullViewport(page: Page) {
  await expect.poll(() => page.evaluate(() => {
    const root = document.scrollingElement!
    return Math.max(root.scrollHeight - root.clientHeight, root.scrollWidth - root.clientWidth)
  })).toBeLessThanOrEqual(1)
  await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeInViewport({ ratio: 1 })
  await expect(page.getByRole('link', { name: 'Forgotten password' })).toBeInViewport({ ratio: 1 })
  await expect(page.getByRole('link', { name: 'Request access' })).toBeInViewport({ ratio: 1 })
}

for (const viewport of viewports) {
  test(`sign-in fits ${viewport.width}×${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport)
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/login')
    await page.evaluate(() => document.fonts.ready)
    await expectFullViewport(page)

    await page.getByRole('button', { name: 'Email', exact: true }).click()
    await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toHaveAttribute('type', 'email')
    await expectFullViewport(page)
  })
}

for (const viewport of viewports) {
  test(`sign-in error fits ${viewport.width}×${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport)
    await page.route('**/api/auth/resolve-username', (route) => route.fulfill({ status: 404, json: {} }))
    await page.goto('/login')
    await page.evaluate(() => document.fonts.ready)
    await page.getByRole('textbox', { name: 'Username', exact: true }).fill('layout-fixture')
    await page.getByLabel('Password', { exact: true }).fill('fixture-password')
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    const error = page.getByRole('alert').filter({ hasText: 'Invalid username or password.' })
    await expect(error).toBeInViewport({ ratio: 1 })
    await expectFullViewport(page)
  })
}

test('a keyboard-height viewport leaves the sign-in form keyboard reachable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 360 })
  await page.goto('/login')
  const password = page.getByLabel('Password', { exact: true })
  await password.focus()
  await expect(password).toBeInViewport({ ratio: 1 })
  const submit = page.getByRole('button', { name: 'Sign in', exact: true })
  await submit.focus()
  await expect(submit).toBeInViewport({ ratio: 1 })
})
