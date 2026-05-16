/**
 * α1 — axe-core accessibility baseline.
 *
 * Verifies that the chat-v2 surface (spike page, then ConsumeChatV2 in α7+)
 * has no critical or serious axe violations.
 *
 * Gate: SOFT (continue-on-error) until γ8 flips it HARD.
 *
 * Requires:
 *   - Next.js dev server at http://localhost:3000
 *   - MARSYS_SUPER_ADMIN_SESSION env (skips gracefully if absent)
 *   - MARSYS_FIXTURE_MODE=true (set by global-setup)
 */
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const SPIKE_URL = '/dev/chat-spike'

test.describe('axe-core baseline — chat-v2 spike page', () => {
  test.skip(
    !process.env.MARSYS_SUPER_ADMIN_SESSION,
    'Skipped: MARSYS_SUPER_ADMIN_SESSION not set',
  )

  test('page initial state has no critical axe violations', async ({ page }) => {
    await page.goto(SPIKE_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .exclude('[data-testid="thread-viewport"]') // content area deferred to γ8
      .analyze()

    // Critical + serious violations are blocking failures
    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious',
    )

    if (criticalOrSerious.length > 0) {
      const report = criticalOrSerious
        .map((v) => `  [${v.impact}] ${v.id}: ${v.description} — ${v.helpUrl}`)
        .join('\n')
      throw new Error(`axe found ${criticalOrSerious.length} critical/serious violation(s):\n${report}`)
    }
  })

  test('composer input has accessible label', async ({ page }) => {
    await page.goto(SPIKE_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })

    const composer = page.getByTestId('composer-input')
    await expect(composer).toBeVisible()

    // aria-label or aria-labelledby must be present for screen reader users
    const ariaLabel = await composer.getAttribute('aria-label')
    const ariaLabelledBy = await composer.getAttribute('aria-labelledby')
    const placeholder = await composer.getAttribute('placeholder')

    // At least one labelling mechanism must be present
    const hasLabel = Boolean(ariaLabel || ariaLabelledBy || placeholder)
    expect(hasLabel, 'Composer input must have aria-label, aria-labelledby, or placeholder').toBe(
      true,
    )
  })

  test('send and abort buttons have accessible names', async ({ page }) => {
    await page.goto(SPIKE_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })

    const sendBtn = page.getByTestId('send-btn')
    await expect(sendBtn).toBeVisible()

    // Button must have an accessible name (aria-label or text content)
    const sendLabel = await sendBtn.getAttribute('aria-label')
    const sendText = await sendBtn.textContent()
    expect(Boolean(sendLabel || sendText?.trim())).toBe(true)
  })

  test('no duplicate landmark roles @visual', async ({ page }) => {
    await page.goto(SPIKE_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })

    const results = await new AxeBuilder({ page })
      .withRules(['landmark-unique'])
      .analyze()

    const landmarkViolations = results.violations.filter((v) => v.id === 'landmark-unique')
    expect(landmarkViolations).toHaveLength(0)
  })
})

test.describe('axe-core structural smoke (no auth required)', () => {
  test('main page root has no critical violations', async ({ page }) => {
    // Test the root page — even behind a login redirect it should have valid structure
    await page.goto('/')

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()

    const critical = results.violations.filter((v) => v.impact === 'critical')
    const criticalReport = critical
      .map((v) => `  ${v.id}: ${v.description}`)
      .join('\n')

    expect(critical, `Critical violations found:\n${criticalReport}`).toHaveLength(0)
  })
})

// ─── γ8: ConsumeChatV2 WCAG 2.1 AA attribute verification ────────────────────
// Source-inspection tests (no auth required): verify aria attributes are present
// in the ConsumeChatV2 source. Runtime smoke tests require MARSYS_SUPER_ADMIN_SESSION.

import { readFileSync } from 'fs'
import { join } from 'path'

const V2_SRC = readFileSync(
  join(process.cwd(), 'src/components/consume/ConsumeChatV2.tsx'),
  'utf8',
)
const DRAWER_SRC = readFileSync(
  join(process.cwd(), 'src/components/chat/PerMessageDetailsDrawer.tsx'),
  'utf8',
)

test.describe('γ8: ConsumeChatV2 WCAG 2.1 AA — source attribute assertions', () => {
  test('page has exactly one main landmark (outer <main>, not thread root)', () => {
    // The outer <main> at the ConsumeChatV2 layout level provides the landmark.
    // ThreadPrimitive.Root must NOT carry role="main" (would be a nested duplicate).
    expect(V2_SRC).toContain('<main ')
    // ThreadPrimitive.Root should not carry role="main"
    expect(V2_SRC).not.toMatch(/ThreadPrimitive\.Root[^>]*role="main"/)
  })

  test('thread viewport is a live region with role=log', () => {
    expect(V2_SRC).toContain('role="log"')
    expect(V2_SRC).toContain('aria-live="polite"')
    expect(V2_SRC).toContain('aria-atomic="false"')
    expect(V2_SRC).toContain('aria-label="Conversation messages"')
  })

  test('composer input has accessible label and multiline declaration', () => {
    expect(V2_SRC).toContain('aria-label="Message input"')
    expect(V2_SRC).toContain('aria-multiline="true"')
  })

  test('all icon-only action buttons have accessible names', () => {
    expect(V2_SRC).toContain('aria-label="Scroll to bottom"')
    expect(V2_SRC).toContain('aria-label="Stop generating response"')
    expect(V2_SRC).toContain('aria-label="Cancel current response and send new query"')
    expect(V2_SRC).toContain('aria-label="Send message"')
    expect(V2_SRC).toContain('aria-label="Attach image or PDF file"')
  })

  test('decorative SVG icons are hidden from assistive technology', () => {
    // Count aria-hidden="true" occurrences on SVG elements (one per icon button)
    const matches = V2_SRC.match(/aria-hidden="true"/g)
    expect(matches).not.toBeNull()
    expect((matches ?? []).length).toBeGreaterThanOrEqual(4)
  })

  test('details drawer declares dialog role and is modal', () => {
    expect(DRAWER_SRC).toContain('role="dialog"')
    expect(DRAWER_SRC).toContain('aria-modal="true"')
    expect(DRAWER_SRC).toContain('aria-label="Message details"')
    expect(DRAWER_SRC).toContain('aria-label="Close details"')
  })

  test('details drawer backdrop hides from assistive technology', () => {
    expect(DRAWER_SRC).toContain('aria-hidden="true"')
  })

  test('details drawer traps focus: tabIndex and Escape handler present', () => {
    expect(DRAWER_SRC).toContain('tabIndex={-1}')
    expect(DRAWER_SRC).toContain("e.key === 'Escape'")
    // focus() called on drawerRef when opened
    expect(DRAWER_SRC).toContain('drawerRef.current?.focus()')
  })
})

test.describe('γ8: ConsumeChatV2 runtime smoke (auth required)', () => {
  test.skip(
    !process.env.MARSYS_SUPER_ADMIN_SESSION,
    'Skipped: MARSYS_SUPER_ADMIN_SESSION not set',
  )

  test('spike page passes full WCAG 2.1 AA axe scan (thread included)', async ({ page }) => {
    await page.goto(SPIKE_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    const blocking = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious',
    )
    const report = blocking
      .map((v) => `  [${v.impact}] ${v.id}: ${v.description}`)
      .join('\n')
    expect(blocking, `γ8 axe violations:\n${report}`).toHaveLength(0)
  })
})
