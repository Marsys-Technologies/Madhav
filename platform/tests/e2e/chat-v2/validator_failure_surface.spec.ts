/**
 * γ4 — Validator failure surface E2E tests
 *
 * Verifies that:
 *   1. Hard-fail (citation_gate status=fail) renders ValidatorFailureBand above message body
 *   2. Soft-fail (citation_gate status=warn) renders ValidatorFooterChip below message body
 *   3. "Details" buttons open the per-message details drawer (β6)
 *   4. Pass status renders neither band nor chip
 *
 * Requires:
 *   - MARSYS_SUPER_ADMIN_SESSION: super-admin auth session fixture
 *   - MARSYS_FIXTURE_MODE=true: fixture provider returning prepared citation_gate parts
 *
 * data-testid inventory (from γ4 components):
 *   v2-validator-failure-band, v2-validator-failure-details-btn
 *   v2-validator-footer-chip, v2-validator-chip-details-btn
 *   v2-details-drawer, v2-details-citation-gate
 */

import { test, expect } from '@playwright/test'

const CONSUME_URL = '/clients/test-client-id/consume'

test.describe('γ4 — validator failure surface', () => {
  test.skip(
    !process.env.MARSYS_SUPER_ADMIN_SESSION,
    'Skipped: MARSYS_SUPER_ADMIN_SESSION not set — requires auth session fixture',
  )
  test.skip(
    !process.env.MARSYS_FIXTURE_MODE,
    'Skipped: MARSYS_FIXTURE_MODE not set — requires fixture provider',
  )

  test.describe('hard-fail (status=fail) — ValidatorFailureBand', () => {
    test('failure band is visible above the message body', async ({ page }) => {
      await page.goto(`${CONSUME_URL}?fixture=citation_gate_fail`)
      // Wait for assistant message to complete
      await page.waitForSelector('[data-testid="v2-validator-failure-band"]', { timeout: 15_000 })
      await expect(page.getByTestId('v2-validator-failure-band')).toBeVisible()
      // Band appears before the message text in DOM order
      const band = page.getByTestId('v2-validator-failure-band')
      const messageText = page.getByTestId('v2-message-text').first()
      const bandBox = await band.boundingBox()
      const textBox = await messageText.boundingBox()
      expect(bandBox?.y).toBeLessThan(textBox?.y ?? Infinity)
    })

    test('failure band shows "Details" button that opens drawer', async ({ page }) => {
      await page.goto(`${CONSUME_URL}?fixture=citation_gate_fail`)
      await page.waitForSelector('[data-testid="v2-validator-failure-details-btn"]', { timeout: 15_000 })
      await page.getByTestId('v2-validator-failure-details-btn').click()
      await expect(page.getByTestId('v2-details-drawer')).toBeVisible()
    })

    test('drawer shows FAIL status in citation gate section', async ({ page }) => {
      await page.goto(`${CONSUME_URL}?fixture=citation_gate_fail`)
      await page.waitForSelector('[data-testid="v2-validator-failure-details-btn"]', { timeout: 15_000 })
      await page.getByTestId('v2-validator-failure-details-btn').click()
      await expect(page.getByTestId('v2-details-citation-gate')).toContainText('FAIL')
    })
  })

  test.describe('soft-fail (status=warn) — ValidatorFooterChip', () => {
    test('footer chip is visible below the message body', async ({ page }) => {
      await page.goto(`${CONSUME_URL}?fixture=citation_gate_warn`)
      await page.waitForSelector('[data-testid="v2-validator-footer-chip"]', { timeout: 15_000 })
      await expect(page.getByTestId('v2-validator-footer-chip')).toBeVisible()
      // Chip appears after the message text in DOM order
      const chip = page.getByTestId('v2-validator-footer-chip')
      const messageText = page.getByTestId('v2-message-text').first()
      const chipBox = await chip.boundingBox()
      const textBox = await messageText.boundingBox()
      expect(chipBox?.y).toBeGreaterThan(textBox?.y ?? 0)
    })

    test('footer chip "Details" button opens drawer', async ({ page }) => {
      await page.goto(`${CONSUME_URL}?fixture=citation_gate_warn`)
      await page.waitForSelector('[data-testid="v2-validator-chip-details-btn"]', { timeout: 15_000 })
      await page.getByTestId('v2-validator-chip-details-btn').click()
      await expect(page.getByTestId('v2-details-drawer')).toBeVisible()
    })

    test('drawer shows WARN status in citation gate section', async ({ page }) => {
      await page.goto(`${CONSUME_URL}?fixture=citation_gate_warn`)
      await page.waitForSelector('[data-testid="v2-validator-chip-details-btn"]', { timeout: 15_000 })
      await page.getByTestId('v2-validator-chip-details-btn').click()
      await expect(page.getByTestId('v2-details-citation-gate')).toContainText('WARN')
    })
  })

  test.describe('pass (status=pass) — no validator surface', () => {
    test('neither band nor chip is shown when gate passes', async ({ page }) => {
      await page.goto(`${CONSUME_URL}?fixture=citation_gate_pass`)
      // Wait for the message to stream completely (no band/chip should appear)
      await page.waitForSelector('[data-testid="v2-message-text"]', { timeout: 15_000 })
      await expect(page.getByTestId('v2-validator-failure-band')).not.toBeVisible()
      await expect(page.getByTestId('v2-validator-footer-chip')).not.toBeVisible()
    })
  })
})
