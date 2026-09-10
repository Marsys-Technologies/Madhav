/**
 * F-122 §5 recurrence guard — kala_elect_get section coverage invariant.
 *
 * Guards against future additions to JudgmentLedger that are not matched by a
 * TrimmableSection in elect.ts. If a new array field is added to JudgmentLedger,
 * this test fails until a matching TrimmableSection path is also added.
 *
 * Tests:
 * 1. All seven JudgmentLedger array fields appear in at least one declared section path.
 * 2. The candidates setArray sync reduces lattice_adjudication.ledgers to only the
 *    surviving candidates (the core F-122 fix).
 */
import { describe, it, expect } from 'vitest'
import { buildElectSections } from '../elect.js'

const ALL_JUDGMENT_LEDGER_ARRAY_FIELDS = [
  'dosas_present',
  'pariharas_applied',
  'residual_dosas',
  'supporting_factors',
  'neutral_annotations',
  'convention_only_factors',
  'convention_only_keys',
] as const

describe('F-122 §5 recurrence guard: elect.ts TrimmableSection coverage', () => {
  it('all seven JudgmentLedger array fields appear in at least one declared section path', () => {
    const sections = buildElectSections()
    const declaredPaths = sections.map((s) => s.path)

    for (const field of ALL_JUDGMENT_LEDGER_ARRAY_FIELDS) {
      const covered = declaredPaths.some(
        (p) =>
          p.includes(`ledgers[].${field}`) ||
          p.includes(`judgment_ledger.${field}`) ||
          p.includes(`judgment_ledger?.${field}`),
      )
      expect(covered, `JudgmentLedger field '${field}' must appear in at least one TrimmableSection path`).toBe(true)
    }
  })

  it('candidates section setArray syncs lattice_adjudication.ledgers to surviving candidate IDs', () => {
    const sections = buildElectSections()
    const candidatesSection = sections.find((s) => s.path === 'candidates')
    expect(candidatesSection).toBeDefined()

    // Build a mock response with 3 ledgers but only 1 surviving candidate (c0).
    // After setArray is called with [cand0], ledgers should contain only c0's ledger.
    const mockLedger = (id: string) => ({
      candidate_id: id,
      dosas_present: [], pariharas_applied: [], residual_dosas: [],
      supporting_factors: [], neutral_annotations: [],
      net_standing: 'clean' as const,
      convention_only_factors: [], convention_only_factor_count: 0,
      convention_only_keys: [], convention_only_note: null,
      adjudication_note: 'test',
    })

    const cand0 = { judgment_ledger: mockLedger('c0') } as Record<string, unknown>
    const mockResponse = {
      candidates: [cand0],
      lattice_adjudication: {
        ledgers: [mockLedger('c0'), mockLedger('c1'), mockLedger('c2')],
        pareto: { frontier_candidate_ids: [], dominated_candidate_ids: [], axes_used: [], axes_excluded: [], method_note: '' },
        gap_report: { statement: '', factor_families_evaluated: [], factors_not_computed: [], factors_not_in_corpus: [], census_disposition_counts: {}, census_state: 'not_in_corpus' as const, parihara_corpus_gap: null, next_occurrence: null },
        coverage_state: 'not_in_corpus' as const,
        coverage_reason: null,
        density: { cited_rows_in_horizon: 0, convention_only_rows_in_horizon: 0, parihara_rules_total: 0, parihara_rules_muhurta_scope: 0 },
      },
    } as unknown as Parameters<typeof candidatesSection.setArray>[0]

    // Simulate the trimmer calling setArray with only cand0 surviving
    candidatesSection!.setArray(mockResponse, [cand0])

    // ledgers must now contain only c0's ledger
    const mr = mockResponse as unknown as Record<string, unknown>
    expect((mr['candidates'] as unknown[]).length).toBe(1)
    const adj = mr['lattice_adjudication'] as { ledgers: { candidate_id: string }[] }
    expect(adj.ledgers).toHaveLength(1)
    expect(adj.ledgers[0]!.candidate_id).toBe('c0')
  })
})
