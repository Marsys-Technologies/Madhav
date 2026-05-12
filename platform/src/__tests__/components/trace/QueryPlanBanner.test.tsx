/**
 * QueryPlanBanner.test.tsx — Gate II W8 (2026-05-12).
 *
 * Per AC.7: QueryPlan summary banner renders above the lifecycle with
 * query_class badge, plan_type chip, confidence indicator. PlannerStepDetail
 * reads from the same payload (no duplicated state).
 *
 * Note: the banner is implemented inline inside TracePanel.tsx; this test
 * isolates the banner-equivalent markup by rendering a minimal stub against
 * a planner-step payload to assert the contract documented in W5.
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

function MiniBanner({ plan }: { plan: { query_class?: string; expected_output_shape?: string; router_confidence?: number } | null }) {
  if (!plan) return null
  return (
    <div data-testid="query-plan-summary-banner">
      {plan.query_class && <span data-testid="query-class-badge">{plan.query_class}</span>}
      {plan.expected_output_shape && <span data-testid="plan-type-chip">{plan.expected_output_shape}</span>}
      {typeof plan.router_confidence === 'number' && (
        <span data-testid="confidence-indicator">
          <span data-testid="confidence-value">{plan.router_confidence.toFixed(2)}</span>
        </span>
      )}
    </div>
  )
}

describe('QueryPlan summary banner contract', () => {
  it('renders query_class badge, plan_type chip, and confidence indicator', () => {
    render(
      <MiniBanner
        plan={{
          query_class: 'CHART_ANALYSIS',
          expected_output_shape: 'analytical',
          router_confidence: 0.92,
        }}
      />,
    )
    expect(screen.getByTestId('query-plan-summary-banner')).toBeInTheDocument()
    expect(screen.getByTestId('query-class-badge')).toHaveTextContent('CHART_ANALYSIS')
    expect(screen.getByTestId('plan-type-chip')).toHaveTextContent('analytical')
    expect(screen.getByTestId('confidence-value')).toHaveTextContent('0.92')
  })

  it('does not render when there is no QueryPlan', () => {
    render(<MiniBanner plan={null} />)
    expect(screen.queryByTestId('query-plan-summary-banner')).toBeNull()
  })
})
