/**
 * Lane G3-E (PPR-05) — proves the three `interpretation_sets` statuses
 * (`generated`, `waived`, `unavailable`) each render an honest, distinct
 * state (never silently hidden, never fabricated — §N.6/§N.7 item 6), and
 * proves the affordances genuinely live in the right dock rather than the
 * prose flow (PPR-05's own "MUST be affordances, never forced into the
 * prose flow" requirement).
 */
import { describe, it, expect } from 'vitest'
import { render, screen, within, fireEvent } from '@testing-library/react'
import { InterpretationSetsSection } from '../InterpretationSetsSection'
import { RightDock } from '../RightDock'
import { DockControllerProvider } from '../DockController'
import { FrozenBlock } from '../../answer/FrozenBlock'
import { makeInitialTurnState } from '../../state/reducer'
import type { TurnState, CommittedBlock } from '../../state/types'
import type { ReceiptInterpretationSets, InterpretationSetEntry } from '@/lib/pariprashna/interpretation/schema'

const GENERATED_ENTRY: InterpretationSetEntry = {
  judgment_id: 'sig-domain_verdict-1',
  category: 'domain_verdict',
  status: 'generated',
  detection_basis: 'block role === verdict',
  candidates: [
    { reading: 'The tenth house strength favors a steady climb rather than a sudden leap.', rationale: 'Saturn aspects the tenth from a position of dignity.' },
    { reading: 'A change of direction around the current period reads as more likely than continuity.', rationale: 'The dasha lord sits in a house of change.' },
    { reading: 'The outcome depends heavily on which divisional chart is weighted more.', rationale: 'D-10 and D-1 disagree on lordship strength.' },
  ],
  selected_index: 0,
  selected_rationale: 'The D-1/D-10 agreement plus dignity favors the steady-climb reading.',
  falsifier: 'A confirmed abrupt career change within the window would falsify this reading.',
  waiver_reason: null,
}

const WAIVED_ENTRY: InterpretationSetEntry = {
  judgment_id: 'sig-remedial-1',
  category: 'remedial',
  status: 'waived',
  detection_basis: 'turn consulted remedial_codex_query',
  candidates: null,
  selected_index: null,
  selected_rationale: null,
  falsifier: null,
  waiver_reason: 'The structured-output call could not produce 3 genuinely distinct candidates for this remedy.',
}

const MEASURED_SETS: ReceiptInterpretationSets = {
  status: 'measured',
  interpretation_sets_schema_version: 2,
  detected_count: 1,
  covered_count: 1,
  truncated_count: 0,
  waived_count: 0,
  sets: [GENERATED_ENTRY],
  unavailable_reason: null,
}

const WAIVED_SETS: ReceiptInterpretationSets = {
  ...MEASURED_SETS,
  detected_count: 1,
  covered_count: 1,
  waived_count: 1,
  sets: [WAIVED_ENTRY],
}

const UNAVAILABLE_SETS: ReceiptInterpretationSets = {
  status: 'unavailable',
  interpretation_sets_schema_version: null,
  detected_count: null,
  covered_count: null,
  truncated_count: null,
  waived_count: null,
  sets: null,
  unavailable_reason: 'PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED was off this turn',
}

const MEASURED_EMPTY_SETS: ReceiptInterpretationSets = {
  ...MEASURED_SETS,
  detected_count: 0,
  covered_count: 0,
  sets: [],
}

const ALTERNATE_READING_TEXT = 'A change of direction around the current period reads as more likely than continuity.'
const FALSIFIER_TEXT = 'A confirmed abrupt career change within the window would falsify this reading.'

describe('InterpretationSetsSection — status rendering', () => {
  it('generated: shows the Read it another way and What would change my mind affordances, collapsed by default', () => {
    render(<InterpretationSetsSection interpretationSets={MEASURED_SETS} />)
    expect(screen.getByText('Read it another way')).toBeInTheDocument()
    expect(screen.getByText('What would change my mind')).toBeInTheDocument()
    // Collapsed by default — the candidate/falsifier text is not yet in the DOM.
    expect(screen.queryByText(ALTERNATE_READING_TEXT)).not.toBeInTheDocument()
    expect(screen.queryByText(FALSIFIER_TEXT)).not.toBeInTheDocument()
  })

  it('generated: expanding "Read it another way" reveals the non-selected candidates only', () => {
    render(<InterpretationSetsSection interpretationSets={MEASURED_SETS} />)
    fireEvent.click(screen.getByText('Read it another way'))
    // The two non-selected candidates appear...
    expect(screen.getByText(ALTERNATE_READING_TEXT)).toBeInTheDocument()
    expect(screen.getByText(/depends heavily on which divisional chart/)).toBeInTheDocument()
    // ...but the SELECTED candidate (index 0) does not — it is the turn's
    // main reading, not an "another way" alternate.
    expect(screen.queryByText(/steady climb rather than a sudden leap/)).not.toBeInTheDocument()
  })

  it('generated: expanding "What would change my mind" reveals the falsifier', () => {
    render(<InterpretationSetsSection interpretationSets={MEASURED_SETS} />)
    fireEvent.click(screen.getByText('What would change my mind'))
    expect(screen.getByText(FALSIFIER_TEXT)).toBeInTheDocument()
  })

  it('waived: shows an honest no-alternatives state with the real waiver reason, no fabricated candidates/falsifier', () => {
    render(<InterpretationSetsSection interpretationSets={WAIVED_SETS} />)
    expect(screen.getByText(/No alternate readings available this turn/)).toBeInTheDocument()
    expect(screen.getByText(/could not produce 3 genuinely distinct candidates/)).toBeInTheDocument()
    // No click-to-expand affordance exists for a waived entry — there is
    // nothing generated to disclose.
    expect(screen.queryByText('Read it another way')).not.toBeInTheDocument()
    expect(screen.queryByText('What would change my mind')).not.toBeInTheDocument()
  })

  it('unavailable: shows an honest "check did not run" state, never a stale/fake affordance', () => {
    render(<InterpretationSetsSection interpretationSets={UNAVAILABLE_SETS} />)
    expect(screen.getByText(/did not run this turn/)).toBeInTheDocument()
    expect(screen.getByText(/PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED was off this turn/)).toBeInTheDocument()
    expect(screen.queryByText('Read it another way')).not.toBeInTheDocument()
    expect(screen.queryByText('What would change my mind')).not.toBeInTheDocument()
  })

  it('measured but zero sets: shows an honest "nothing to check" state, distinct from unavailable', () => {
    render(<InterpretationSetsSection interpretationSets={MEASURED_EMPTY_SETS} />)
    expect(screen.getByText(/No significant judgments this turn needed an alternate-reading check/)).toBeInTheDocument()
    // Distinct wording from the unavailable case — never conflated.
    expect(screen.queryByText(/did not run this turn/)).not.toBeInTheDocument()
  })
})

function turnWithInterpretationSets(id: string, interpretationSets: ReceiptInterpretationSets | null): TurnState {
  return { ...makeInitialTurnState(id, 'A question about career timing.'), status: 'settled', interpretationSets }
}

describe('InterpretationSetsSection — affordance placement (never inline in prose)', () => {
  it('renders inside the right dock, not inside the prose block, even when both mount side by side', () => {
    const turn = turnWithInterpretationSets('t1', MEASURED_SETS)
    const proseBlock: CommittedBlock = {
      id: 'b1',
      kind: 'paragraph',
      role: 'verdict',
      html: 'The reading settles on a steady professional trajectory this year.',
    }

    render(
      <div>
        <div data-testid="pp-prose-column">
          <FrozenBlock turnId="t1" block={proseBlock} citations={{}} />
        </div>
        <DockControllerProvider defaultOpen={true}>
          <RightDock turns={[turn]} />
        </DockControllerProvider>
      </div>,
    )

    const dock = screen.getByTestId('pp-right-dock')
    const prose = screen.getByTestId('pp-prose-column')

    // The affordance headers exist in the document at all...
    expect(screen.getByText('Read it another way')).toBeInTheDocument()
    // ...but ONLY inside the dock, never inside the prose column the reading
    // actually streams into.
    expect(within(dock).getByText('Read it another way')).toBeInTheDocument()
    expect(within(prose).queryByText('Read it another way')).not.toBeInTheDocument()
    expect(within(prose).queryByText('What would change my mind')).not.toBeInTheDocument()

    // Expand both affordances and confirm the actual candidate/falsifier
    // prose lands in the dock only, never leaking into the prose column.
    fireEvent.click(within(dock).getByText('Read it another way'))
    fireEvent.click(within(dock).getByText('What would change my mind'))
    expect(within(dock).getByText(ALTERNATE_READING_TEXT)).toBeInTheDocument()
    expect(within(dock).getByText(FALSIFIER_TEXT)).toBeInTheDocument()
    expect(within(prose).queryByText(ALTERNATE_READING_TEXT)).not.toBeInTheDocument()
    expect(within(prose).queryByText(FALSIFIER_TEXT)).not.toBeInTheDocument()
  })

  it('RightDock renders nothing interpretation-related for a turn whose interpretationSets is null (honest absence, not a placeholder affordance)', () => {
    const turn = turnWithInterpretationSets('t2', null)
    render(
      <DockControllerProvider defaultOpen={true}>
        <RightDock turns={[turn]} />
      </DockControllerProvider>,
    )
    expect(screen.queryByTestId('pp-interpretation-sets')).not.toBeInTheDocument()
    expect(screen.queryByText('Read it another way')).not.toBeInTheDocument()
  })

  it('RightDock surfaces the waived honest state for a turn that only has interpretation_sets (no citations/predictions)', () => {
    const turn = turnWithInterpretationSets('t3', WAIVED_SETS)
    render(
      <DockControllerProvider defaultOpen={true}>
        <RightDock turns={[turn]} />
      </DockControllerProvider>,
    )
    const dock = screen.getByTestId('pp-right-dock')
    expect(within(dock).getByText(/No alternate readings available this turn/)).toBeInTheDocument()
  })
})
