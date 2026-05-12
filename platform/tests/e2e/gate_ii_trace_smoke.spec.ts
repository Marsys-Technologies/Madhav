import { test, expect } from '@playwright/test'

/**
 * Gate II.5 — Trace UI smoke spec.
 *
 * Tests the production pipeline shape alignment introduced in Gate II.5:
 *   - Planning [classify + compose_bundle + plan_per_tool sub-rows]
 *   - Retrieval [21 inline sub-rows, unfired dimmed]
 *   - Audit [real data from audit_events JOIN; no placeholder]
 *
 * Requires:
 *   SMOKE_SESSION_COOKIE — Firebase __session cookie value (super_admin role)
 *   SMOKE_QUERY_ID       — UUID of a completed query with trace data in DB
 *
 * If either env var is absent the suite is skipped; set them then re-run:
 *   SMOKE_SESSION_COOKIE=<value> SMOKE_QUERY_ID=<uuid> npx playwright test tests/e2e/gate_ii_trace_smoke.spec.ts
 */

const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE
const QUERY_ID = process.env.SMOKE_QUERY_ID
const SKIP = !SESSION_COOKIE || !QUERY_ID

test.describe('Gate II.5 — Trace UI smoke', () => {
  test.skip(SKIP, 'SMOKE_SESSION_COOKIE or SMOKE_QUERY_ID not set; see spec header for re-run instructions')

  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: '__session', value: SESSION_COOKIE!, domain: 'localhost', path: '/' },
    ])
  })

  test('trace modal renders and lifecycle graph is visible', async ({ page }) => {
    await page.goto(`/admin/trace/${QUERY_ID!}`)
    await expect(page.getByTestId('trace-modal')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('lifecycle-graph')).toBeVisible()
  })

  test('Planning container has 3 inline sub-rows (D9)', async ({ page }) => {
    await page.goto(`/admin/trace/${QUERY_ID!}`)
    await expect(page.getByTestId('lifecycle-graph')).toBeVisible({ timeout: 15_000 })

    // Planning container header
    await expect(page.getByTestId('lifecycle-node-planner')).toBeVisible()

    // All 3 D9 sub-rows must be present in the DOM
    await expect(page.getByTestId('planning-subrow-classify')).toBeAttached()
    await expect(page.getByTestId('planning-subrow-compose_bundle')).toBeAttached()
    await expect(page.getByTestId('planning-subrow-plan_per_tool')).toBeAttached()
  })

  test('Retrieval container shows "of 21 tools fired" (D10)', async ({ page }) => {
    await page.goto(`/admin/trace/${QUERY_ID!}`)
    await expect(page.getByTestId('lifecycle-graph')).toBeVisible({ timeout: 15_000 })

    const retrievalHeader = page.getByTestId('lifecycle-node-retrieval')
    await expect(retrievalHeader).toBeVisible()
    await expect(retrievalHeader).toContainText('of 21 tools fired')

    // All 21 sub-rows are rendered (may be dimmed for unfired tools)
    const subrows = page.getByTestId('retrieval-subrows-graph').locator('li')
    await expect(subrows).toHaveCount(21)
  })

  test('Audit step renders AuditDetail with real data (not placeholder)', async ({ page }) => {
    await page.goto(`/admin/trace/${QUERY_ID!}`)
    await expect(page.getByTestId('lifecycle-graph')).toBeVisible({ timeout: 15_000 })

    // Click audit stage
    await page.getByTestId('lifecycle-node-audit').click()

    // AuditDetail must render
    await expect(page.getByTestId('audit-detail')).toBeVisible()

    // audit_event_id must show a real UUID (not '—')
    const auditId = page.getByTestId('audit-event-id')
    await expect(auditId).not.toContainText('—')
  })

  test('Clicking planner:compose_bundle sub-row opens PlannerDetail', async ({ page }) => {
    await page.goto(`/admin/trace/${QUERY_ID!}`)
    await expect(page.getByTestId('lifecycle-graph')).toBeVisible({ timeout: 15_000 })

    await page.getByTestId('planning-subrow-compose_bundle').click()

    // StepDetail must show the planner panel (compose_bundle section)
    await expect(page.getByTestId('planner-detail')).toBeVisible()
    await expect(page.getByTestId('planner-compose-bundle')).toBeAttached()
  })

  test('Clicking planner:plan_per_tool sub-row shows plan_per_tool section', async ({ page }) => {
    await page.goto(`/admin/trace/${QUERY_ID!}`)
    await expect(page.getByTestId('lifecycle-graph')).toBeVisible({ timeout: 15_000 })

    await page.getByTestId('planning-subrow-plan_per_tool').click()

    await expect(page.getByTestId('planner-detail')).toBeVisible()
    await expect(page.getByTestId('planner-plan-per-tool')).toBeAttached()
  })

  test('Audit: null D11 columns render as "—" with tooltip (R10)', async ({ page }) => {
    await page.goto(`/admin/trace/${QUERY_ID!}`)
    await expect(page.getByTestId('lifecycle-graph')).toBeVisible({ timeout: 15_000 })

    await page.getByTestId('lifecycle-node-audit').click()
    await expect(page.getByTestId('audit-detail')).toBeVisible()

    // audit-placeholder-note must NOT be visible (real data, not placeholder row)
    await expect(page.getByTestId('audit-placeholder-note')).not.toBeVisible()
  })
})
