// USTAD_S3_3 — Budgets UI tests.
//
// 8 tests across BudgetStatusChip, BudgetRuleCard, and CreateBudgetRuleForm.
// Render the components with React Testing Library against a stubbed API
// client (createBudgetRule) — no fetches actually leave jsdom.

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

// API-client mock for the form's submit path.
const createBudgetRuleMock = vi.fn()
vi.mock('@/lib/api-clients/observatory', () => ({
  createBudgetRule: (...args: unknown[]) => createBudgetRuleMock(...args),
  evaluateBudgets: vi.fn(async () => ({ results: [] })),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}))

import { BudgetStatusChip } from '../../budget/BudgetStatusChip'
import { BudgetRuleCard } from '../../budget/BudgetRuleCard'
import { CreateBudgetRuleForm } from '../../budget/CreateBudgetRuleForm'
import { RunEvaluationButton } from '../../budget/RunEvaluationButton'
import type {
  BudgetEvaluationResult,
  BudgetRuleRow,
} from '@/lib/observatory/budget/types'

function makeRule(overrides: Partial<BudgetRuleRow> = {}): BudgetRuleRow {
  return {
    budget_rule_id: 'rule-test-1',
    name: 'Test Rule',
    scope: 'total',
    scope_value: null,
    period: 'monthly',
    amount_usd: 100,
    alert_thresholds: [{ pct: 80, channel: 'log' }],
    created_by_user_id: null,
    active: true,
    created_at: '2026-05-01T00:00:00Z',
    updated_at: '2026-05-01T00:00:00Z',
    ...overrides,
  }
}

function makeEval(
  overrides: Partial<BudgetEvaluationResult> = {},
): BudgetEvaluationResult {
  return {
    rule_id: 'rule-test-1',
    name: 'Test Rule',
    scope: 'total',
    scope_value: null,
    period: 'monthly',
    period_start: '2026-05-01',
    period_end: '2026-05-31',
    amount_usd: 100,
    current_spend_usd: 50,
    pct_used: 50,
    status: 'ok',
    alerts_triggered: [],
    ...overrides,
  }
}

describe('BudgetStatusChip', () => {
  it("1. status='ok' → emerald chip with 'OK'", () => {
    render(<BudgetStatusChip status="ok" pct_used={45} />)
    const chip = screen.getByTestId('budget-status-chip-ok')
    expect(chip).toHaveAttribute('data-status', 'ok')
    expect(chip.textContent).toMatch(/OK/)
    expect(chip.textContent).toMatch(/45%/)
    // New design: pill chip with border, no dot element.
    expect(chip.className).toMatch(/emerald/)
  })

  it("2. status='exceeded' → red chip with 'Exceeded'", () => {
    render(<BudgetStatusChip status="exceeded" pct_used={120} />)
    const chip = screen.getByTestId('budget-status-chip-exceeded')
    expect(chip).toHaveAttribute('data-status', 'exceeded')
    expect(chip.textContent).toMatch(/Exceeded/)
    expect(chip.textContent).toMatch(/120%/)
    // New design: pill chip styled with red-600 tokens.
    expect(chip.className).toMatch(/red/)
  })
})

describe('BudgetRuleCard', () => {
  it('3. renders skeleton when evaluation is undefined', () => {
    render(<BudgetRuleCard rule={makeRule()} onDeactivate={() => {}} />)
    expect(
      screen.getByTestId('budget-rule-skeleton-rule-test-1'),
    ).toBeInTheDocument()
    // Progress bar + spend line absent while loading.
    expect(
      screen.queryByTestId('budget-rule-progress-rule-test-1'),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByTestId('budget-rule-spend-rule-test-1'),
    ).not.toBeInTheDocument()
  })

  it('4. renders progress bar + spend line when evaluation is present', () => {
    render(
      <BudgetRuleCard
        rule={makeRule({ amount_usd: 200 })}
        evaluation={makeEval({
          amount_usd: 200,
          current_spend_usd: 175,
          pct_used: 87.5,
          status: 'warning',
        })}
        onDeactivate={() => {}}
      />,
    )
    const progress = screen.getByTestId('budget-rule-progress-rule-test-1')
    expect(progress).toBeInTheDocument()
    expect(progress).toHaveAttribute('aria-valuenow', '88')
    const spend = screen.getByTestId('budget-rule-spend-rule-test-1')
    // New design: spend and limit shown in two spans; combined textContent is "$175.00 spentof $200.00".
    expect(spend.textContent).toMatch(/\$175\.00/)
    expect(spend.textContent).toMatch(/\$200\.00/)
    // Status chip shows the evaluation status.
    expect(screen.getByTestId('budget-status-chip-warning')).toBeInTheDocument()
  })

  it('5. Deactivate button → confirm → triggers onDeactivate callback', () => {
    const onDeactivate = vi.fn()
    render(
      <BudgetRuleCard
        rule={makeRule()}
        evaluation={makeEval()}
        onDeactivate={onDeactivate}
      />,
    )
    const deactivateBtn = screen.getByTestId(
      'budget-rule-deactivate-rule-test-1',
    )
    fireEvent.click(deactivateBtn)
    // Confirmation appears.
    const confirmBtn = screen.getByTestId('budget-rule-confirm-rule-test-1')
    expect(confirmBtn).toBeInTheDocument()
    fireEvent.click(confirmBtn)
    expect(onDeactivate).toHaveBeenCalledTimes(1)
  })
})

describe('CreateBudgetRuleForm', () => {
  beforeEach(() => {
    createBudgetRuleMock.mockReset()
  })

  it('6. scope=total (global) hides scope_value field', () => {
    render(<CreateBudgetRuleForm onCreated={() => {}} />)
    // Default scope is `total` — scope_value input must not be in the DOM.
    expect(
      screen.queryByTestId('create-budget-rule-scope-value'),
    ).not.toBeInTheDocument()
  })

  it('7. scope=provider shows provider select with PROVIDER_OPTIONS', () => {
    render(<CreateBudgetRuleForm onCreated={() => {}} />)
    const scopeSelect = screen.getByTestId(
      'create-budget-rule-scope',
    ) as HTMLSelectElement
    fireEvent.change(scopeSelect, { target: { value: 'provider' } })
    const valueField = screen.getByTestId(
      'create-budget-rule-scope-value',
    ) as HTMLSelectElement
    expect(valueField).toBeInTheDocument()
    expect(valueField).toHaveAttribute('data-scope-value-type', 'provider')
    // PROVIDER_OPTIONS = anthropic, openai, gemini, deepseek, nim → 5 options
    // (plus the initial blank "Select provider…" placeholder).
    expect(valueField.querySelectorAll('option')).toHaveLength(6)
    expect(valueField.querySelector('option[value="anthropic"]')).not.toBeNull()
    expect(valueField.querySelector('option[value="openai"]')).not.toBeNull()
  })

  it('8. Submit calls createBudgetRule with correct payload + onCreated fires', async () => {
    createBudgetRuleMock.mockResolvedValueOnce({
      budget_rule_id: 'rule-new',
      name: 'Test',
      scope: 'provider',
      scope_value: 'anthropic',
      period: 'monthly',
      amount_usd: 200,
      alert_thresholds: [{ pct: 80, channel: 'log' }],
      created_by_user_id: null,
      active: true,
      created_at: '2026-05-03T00:00:00Z',
      updated_at: '2026-05-03T00:00:00Z',
    })
    const onCreated = vi.fn()
    render(<CreateBudgetRuleForm onCreated={onCreated} />)

    const nameInput = screen.getByTestId('create-budget-rule-name')
    fireEvent.change(nameInput, { target: { value: 'Anthropic monthly cap' } })

    const scopeSelect = screen.getByTestId('create-budget-rule-scope')
    fireEvent.change(scopeSelect, { target: { value: 'provider' } })

    const valueField = screen.getByTestId('create-budget-rule-scope-value')
    fireEvent.change(valueField, { target: { value: 'anthropic' } })

    const amountInput = screen.getByTestId('create-budget-rule-amount')
    fireEvent.change(amountInput, { target: { value: '200' } })

    const submit = screen.getByTestId('create-budget-rule-submit')
    fireEvent.click(submit)

    // Wait one microtask for the async submit handler to resolve.
    await Promise.resolve()
    await Promise.resolve()

    expect(createBudgetRuleMock).toHaveBeenCalledTimes(1)
    const payload = createBudgetRuleMock.mock.calls[0][0]
    expect(payload.name).toBe('Anthropic monthly cap')
    expect(payload.scope).toBe('provider')
    expect(payload.scope_value).toBe('anthropic')
    expect(payload.amount_usd).toBe(200)
    expect(payload.period).toBe('monthly')
    expect(Array.isArray(payload.alert_thresholds)).toBe(true)
    // The default seeded thresholds (80/log, 95/email) should round-trip.
    expect(payload.alert_thresholds).toHaveLength(2)
    expect(onCreated).toHaveBeenCalledTimes(1)
  })
})

// USTAD_S3_4 — closes S3.3 AC.6: the button now POSTs the scheduled-run
// endpoint that both evaluates AND dispatches alerts, instead of the GET
// endpoint that only evaluated.
describe('RunEvaluationButton — wired to POST /evaluate/run (USTAD_S3_4)', () => {
  let originalFetch: typeof globalThis.fetch
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    originalFetch = globalThis.fetch
    fetchMock = vi.fn()
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('9. clicking the button fires POST /evaluate/run and shows evaluated/fired counts', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          evaluated_count: 3,
          alerts_fired_count: 2,
          dispatch_results: [
            {
              rule_id: 'rule-A',
              outcomes: [{ channel: 'log', success: true }],
            },
            {
              rule_id: 'rule-B',
              outcomes: [{ channel: 'log', success: true }],
            },
          ],
          evaluated_at: '2026-05-03T10:00:00Z',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    render(<RunEvaluationButton />)
    fireEvent.click(screen.getByTestId('budgets-run-evaluation'))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/admin/observatory/budget-rules/evaluate/run')
    expect((init as RequestInit).method).toBe('POST')

    await waitFor(() => {
      const fb = screen.getByTestId('budgets-run-feedback')
      expect(fb.textContent).toMatch(/Evaluated 3 rules/)
      expect(fb.textContent).toMatch(/2 alerts fired/)
    })
    // No dispatch errors → secondary line is absent.
    expect(
      screen.queryByTestId('budgets-run-dispatch-errors'),
    ).not.toBeInTheDocument()
  })
})
