/**
 * Y-S8 — Validator Per-Gate Expander
 *
 * Click-path: Chat V2 → validator failure band appears → click it →
 *   per-gate list expands (FAIL/WARN/PASS badges + reason) → click → collapses.
 *
 * Amendment 2: parent-context integration test mounts ValidatorFailureBand
 *   inside a shell that mirrors the ConsumeChatV2 usage pattern.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act, fireEvent } from '@testing-library/react'
import React from 'react'
import { ValidatorFailureBand } from '@/components/chat/ValidatorFailureBand'
import type { GateVerdict } from '@/lib/streams/data_parts'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const sampleGates: GateVerdict[] = [
  { name: 'citation_exists', verdict: 'FAIL', reason: 'Signal SIG.MSR.001 not found in store' },
  { name: 'layer_match', verdict: 'WARN', reason: 'Layer L2.5 declared but signal is L1' },
  { name: 'snippet_non_empty', verdict: 'PASS', reason: 'Snippet present' },
]

// ── Parent-context shell ──────────────────────────────────────────────────────

function FailureBandShell({
  gates,
  isSuperAdmin = false,
}: {
  gates?: GateVerdict[]
  isSuperAdmin?: boolean
}) {
  const [detailsOpen, setDetailsOpen] = React.useState(false)
  return (
    <div data-testid="v2-chat-shell">
      <ValidatorFailureBand
        issues={['Signal SIG.MSR.001 not found']}
        isSuperAdmin={isSuperAdmin}
        onOpenDetails={() => setDetailsOpen(true)}
        gates={gates}
      />
      {detailsOpen && <div data-testid="v2-details-drawer">Details drawer</div>}
    </div>
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('ValidatorFailureBand per-gate expander — parent-context (Y-S8)', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES', 'true')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
  })

  it('renders the failure band (collapsed by default)', () => {
    const { getByTestId, queryByTestId } = render(
      <FailureBandShell gates={sampleGates} />,
    )
    expect(getByTestId('v2-validator-failure-band')).toBeTruthy()
    expect(queryByTestId('v2-validator-gate-list')).toBeNull()
  })

  it('clicking the header expands per-gate list', async () => {
    const { getByTestId } = render(<FailureBandShell gates={sampleGates} />)

    await act(async () => {
      fireEvent.click(getByTestId('v2-validator-failure-header'))
    })

    expect(getByTestId('v2-validator-gate-list')).toBeTruthy()
  })

  it('shows all gates with correct verdicts when expanded', async () => {
    const { getByTestId, getAllByTestId } = render(
      <FailureBandShell gates={sampleGates} />,
    )

    await act(async () => {
      fireEvent.click(getByTestId('v2-validator-failure-header'))
    })

    const verdictBadges = getAllByTestId(/^v2-gate-verdict-/)
    expect(verdictBadges).toHaveLength(3)
    expect(verdictBadges[0].textContent).toBe('FAIL')
    expect(verdictBadges[1].textContent).toBe('WARN')
    expect(verdictBadges[2].textContent).toBe('PASS')
  })

  it('clicking header again collapses the gate list', async () => {
    const { getByTestId, queryByTestId } = render(
      <FailureBandShell gates={sampleGates} />,
    )

    const header = getByTestId('v2-validator-failure-header')
    await act(async () => { fireEvent.click(header) })
    expect(getByTestId('v2-validator-gate-list')).toBeTruthy()

    await act(async () => { fireEvent.click(header) })
    expect(queryByTestId('v2-validator-gate-list')).toBeNull()
  })

  it('Details button still works when gate list is shown', async () => {
    const { getByTestId } = render(<FailureBandShell gates={sampleGates} />)

    await act(async () => {
      fireEvent.click(getByTestId('v2-validator-failure-header'))
    })
    await act(async () => {
      fireEvent.click(getByTestId('v2-validator-failure-details-btn'))
    })

    expect(getByTestId('v2-details-drawer')).toBeTruthy()
  })

  it('gate list is NOT shown when flag is disabled (regression guard)', async () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES', 'false')
    const { getByTestId, queryByTestId } = render(
      <FailureBandShell gates={sampleGates} />,
    )

    await act(async () => {
      fireEvent.click(getByTestId('v2-validator-failure-header'))
    })

    expect(queryByTestId('v2-validator-gate-list')).toBeNull()
  })

  it('gate list is NOT shown when gates array is empty (regression guard)', async () => {
    const { getByTestId, queryByTestId } = render(
      <FailureBandShell gates={[]} />,
    )

    await act(async () => {
      fireEvent.click(getByTestId('v2-validator-failure-header'))
    })

    expect(queryByTestId('v2-validator-gate-list')).toBeNull()
  })

  it('band renders normally when no gates prop is passed (backward-compat)', () => {
    const { getByTestId, queryByTestId } = render(
      <FailureBandShell />,
    )
    expect(getByTestId('v2-validator-failure-band')).toBeTruthy()
    expect(queryByTestId('v2-validator-gate-list')).toBeNull()
  })
})
