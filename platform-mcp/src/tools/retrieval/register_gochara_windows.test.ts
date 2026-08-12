/**
 * register_gochara_windows.test.ts — D-5 Lane G-4 serving-tool tests.
 *
 * Pure/structural tests (no DB): `dominantGraha` graha-resolution logic and
 * the §N.6 density_contract shapes. A DB-backed integration check
 * (`RUN_DB_INTEGRATION`-gated, skipped by default — same discipline as this
 * lane's Python `@pytest.mark.integration` tests) proves the three compute*
 * functions return real, shape-correct rows against the live platform DB proxy
 * (SARVA-SIDDHI W-1 T-1: these tools now proxy SELECT-only SQL through
 * POST ${PLATFORM_URL}/api/mcp/db/query — the MCP server holds no direct DB
 * connection — so the integration run requires a reachable platform, not a raw
 * DATABASE_URL).
 *
 * PARĪKṢAKA F1 fix (PR #1225, MR-12): `computeGocharaElectionAvoidance`'s
 * is_irreversibility_milestone serving fix had no output-asserting test — the
 * field appeared in `makeRow` fixtures (used only by the pure `dominantGraha`/
 * `derivePlateauDisclosure` tests above) but nothing ever exercised the real
 * per-row-object-construction code path and checked the field survived onto
 * the SERVED window. The `computeGocharaElectionAvoidance — MR-12 ...`
 * describe block below mocks `global.fetch` (same pattern as
 * `kala_views/priority.test.ts`) so that code path runs end-to-end without a
 * live DB.
 */
import { describe, it, expect, vi } from 'vitest'
import {
  dominantGraha,
  derivePlateauDisclosure,
  computeGocharaActivation,
  computeGocharaForecast,
  computeGocharaElectionAvoidance,
  computeGocharaCoverage,
  type GocharaWindowRow,
  type GocharaCoverage,
  buildNestedHierarchy,
  type GocharaWindowRow,
  type HierarchyNode,
  type ServedWindow,
} from './register_gochara_windows.js'
import type { Principal } from '../../types.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const TEST_PRINCIPAL: Principal = { user_uid: 'integration-test', key_id: 'integration-test', role: 'super_admin' }

function makeRow(overrides: Partial<GocharaWindowRow> = {}): GocharaWindowRow {
  return {
    id: 1,
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    event_class: 'marriage',
    temporal_shape: 'point',
    window_start: '2013-12-11',
    window_end: '2013-12-11',
    peak_date: '2013-12-11',
    milestone_id: null,
    is_irreversibility_milestone: false,
    signed_intensity: 1.2,
    raw_intensity: 1.2,
    valence: 'neutral',
    is_adverse: false,
    active_sentences: [],
    contributing_systems: [],
    suppression_state: {},
    peak_basis: 'gochara_lambda_e_v1',
    calibration_state: 'structural_prior',
    source: 'live',
    computed_at: '2026-07-19T00:00:00Z',
    continuity_state: null,
    plateau_disclosure: null,
    resolution: null,
    parent_window_id: null,
    ...overrides,
  }
}

// Helper: build a ServedWindow (GocharaWindowRow with resolution_disclosure attached)
function makeServedWindow(overrides: Partial<GocharaWindowRow> = {}): ServedWindow {
  return {
    ...makeRow(overrides),
    resolution_disclosure: null,
  }
}

describe('derivePlateauDisclosure', () => {
  it('is null for a point-shaped row (no continuity_state concept applies)', () => {
    expect(derivePlateauDisclosure(makeRow({ temporal_shape: 'point' }))).toBeNull()
  })

  it('is null for an interval row with no continuity_state (nothing to disclose)', () => {
    expect(derivePlateauDisclosure(makeRow({ temporal_shape: 'interval', continuity_state: null }))).toBeNull()
  })

  it('is null when neither edge is open (a genuinely closed, fully-resolved span)', () => {
    const row = makeRow({
      temporal_shape: 'interval',
      continuity_state: { raw_start: '2010-07-01', raw_end: '2011-03-01', left_active: false, right_active: false },
    })
    expect(derivePlateauDisclosure(row)).toBeNull()
  })

  it('flags window_start_open when left_active — the D-5 native-disposition finding-1 case', () => {
    const row = makeRow({
      temporal_shape: 'interval',
      window_start: '2010-01-01',
      window_end: '2011-01-01',
      continuity_state: { raw_start: '2010-01-01', raw_end: '2012-01-01', left_active: true, right_active: true },
    })
    const disclosure = derivePlateauDisclosure(row)
    expect(disclosure).not.toBeNull()
    expect(disclosure?.window_start_open).toBe(true)
    expect(disclosure?.window_end_open).toBe(true)
    expect(disclosure?.note).toContain('2010-01-01')
    expect(disclosure?.note).toContain('2011-01-01')
  })

  it('flags only the open edge when the other is genuinely closed', () => {
    const row = makeRow({
      temporal_shape: 'interval',
      continuity_state: { raw_start: '2010-07-01', raw_end: '2011-03-01', left_active: false, right_active: true },
    })
    const disclosure = derivePlateauDisclosure(row)
    expect(disclosure?.window_start_open).toBe(false)
    expect(disclosure?.window_end_open).toBe(true)
  })
})

describe('dominantGraha', () => {
  it('returns null when no systems are active', () => {
    expect(dominantGraha(makeRow({ contributing_systems: [] }))).toBeNull()
  })

  it('returns null when active systems carry no graha detail', () => {
    const row = makeRow({
      contributing_systems: [{ system_id: 'av_threshold', active: true, weight: 0.06, detail: {} }],
    })
    expect(dominantGraha(row)).toBeNull()
  })

  it('resolves a lord_graha from an active system detail', () => {
    const row = makeRow({
      contributing_systems: [
        { system_id: 'vimshottari', active: true, weight: 0.16, detail: { lord_graha: 'Saturn' } },
      ],
    })
    expect(dominantGraha(row)).toBe('saturn')
  })

  it('ignores inactive systems even if they carry a graha', () => {
    const row = makeRow({
      contributing_systems: [
        { system_id: 'yogini', active: false, weight: 0.07, detail: { lord_graha: 'Mars' } },
      ],
    })
    expect(dominantGraha(row)).toBeNull()
  })
})

// ── computeGocharaElectionAvoidance — MR-12 F1 output-assertion fix ────────
// Mocks global.fetch to intercept the platformQuery(sql, params, principal)
// round trips this function makes, so the REAL per-row-object-construction
// code (register_gochara_windows.ts lines building `avoidWindows`) runs
// end-to-end without a live DB. This is the detector PARĪKṢAKA's F1 finding
// asked for: the previous test suite verified the fix only by inspection
// (the field appeared in unrelated fixtures), and reverting the fix left the
// suite green.
describe('computeGocharaElectionAvoidance — MR-12 is_irreversibility_milestone serving', () => {
  const CHAIN_ROW = {
    id: 99,
    chart_id: CHART_ID,
    event_class: 'business_launch',
    temporal_shape: 'chain',
    window_start: '2026-05-01',
    window_end: '2026-05-01',
    peak_date: '2026-05-01',
    milestone_id: 'first_revenue',
    is_irreversibility_milestone: true,
    signed_intensity: -0.4,
    raw_intensity: 0.4,
    valence: 'loss',
    is_adverse: true,
    active_sentences: [] as unknown[],
    contributing_systems: [] as unknown[],
    suppression_state: {},
    peak_basis: 'gochara_lambda_v3',
    calibration_state: 'structural_prior',
    source: 'live',
    computed_at: '2026-05-01T00:00:00Z',
    continuity_state: null,
    generation: '3.0',
    era_slice_key: 'g3_2024_2034',
    term_breakdown: null,
  }

  function mockFetchServing(row: Record<string, unknown>) {
    global.fetch = vi.fn(async (url: unknown, opts: unknown) => {
      const urlStr = String(url)
      if (urlStr.includes('/api/mcp/db/query')) {
        const body = JSON.parse((opts as { body: string }).body) as { sql?: string }
        const sql = body.sql ?? ''
        // The main SELECT (computeGocharaElectionAvoidance's own query) is the
        // only one that reads FROM kala_gochara_windows filtered on is_adverse.
        // computeGocharaCoverage's 4 queries (kala_gochara_authority,
        // gochara_resonance_map, brahma_event_ontology, build_substep_progress)
        // and any brahma_remedy_corpus lookup all fall through to honest-empty —
        // this test's assertion does not depend on their contents (no `domain`
        // filter is passed, so notCoveredFor short-circuits to null regardless;
        // dominantGraha(row) returns null for an empty contributing_systems,
        // so fetchMitigation never queries brahma_remedy_corpus at all).
        if (sql.includes('FROM kala_gochara_windows') && sql.includes('is_adverse')) {
          return { ok: true, json: async () => ({ rows: [row] }) }
        }
        return { ok: true, json: async () => ({ rows: [] }) }
      }
      return { ok: false, status: 500, text: async () => 'unexpected fetch call in test' }
    }) as unknown as typeof fetch
  }

  it('a chain-shaped adverse window serves is_irreversibility_milestone=true for its irreversibility milestone', async () => {
    mockFetchServing(CHAIN_ROW)

    const result = (await computeGocharaElectionAvoidance(
      CHART_ID,
      { start: '2020-01-01', end: '2030-01-01' },
      undefined,
      50,
      TEST_PRINCIPAL
    )) as { windows: Array<Record<string, unknown>> }

    expect(result.windows).toHaveLength(1)
    expect(result.windows[0]?.['milestone_id']).toBe('first_revenue')
    expect(result.windows[0]?.['is_irreversibility_milestone']).toBe(true)
  })

  it('a non-irreversibility chain milestone serves is_irreversibility_milestone=false (not just truthy-field-present)', async () => {
    mockFetchServing({ ...CHAIN_ROW, milestone_id: 'decision', is_irreversibility_milestone: false })

    const result = (await computeGocharaElectionAvoidance(
      CHART_ID,
      { start: '2020-01-01', end: '2030-01-01' },
      undefined,
      50,
      TEST_PRINCIPAL
    )) as { windows: Array<Record<string, unknown>> }

    expect(result.windows).toHaveLength(1)
    expect(result.windows[0]?.['milestone_id']).toBe('decision')
    expect(result.windows[0]?.['is_irreversibility_milestone']).toBe(false)
  })
})

// ── computeGocharaCoverage — C3 coverage_quality.tier ──────────────────────
// Tests for the coverage_quality field added in SAMPŪRTI-γ C3.
// Mocks global.fetch to intercept platformQuery calls — same pattern as the
// MR-12 block above. The four queries computeGocharaCoverage issues are:
//   1. kala_gochara_authority  → authority generation (returns [] → v1 path)
//   2. gochara_resonance_map   → targeted classes + domains (classesResp)
//   3. brahma_event_ontology   → universe domains (universeResp)
//   4. build_substep_progress  → substeps + swept classes (substepResp)
//
// For tier tests we care about covered_class_count (= eventClasses.length),
// so we wire classesResp and substepResp to agree on exactly N classes.
// universeResp always returns 5 domains so domains_not_covered is non-empty
// and does not interfere with the tier assertions.

function makeClassRows(eventClasses: string[], domainMap: Record<string, string> = {}): Record<string, unknown>[] {
  return eventClasses.map((ec) => ({ event_class: ec, domain: domainMap[ec] ?? 'career' }))
}

function mockCoverageFetch(
  classRows: Record<string, unknown>[],
  sweptClasses: string[],
  universeDomains: string[] = ['career', 'health', 'finance', 'relationship', 'spirituality'],
): void {
  global.fetch = vi.fn(async (url: unknown, opts: unknown) => {
    const urlStr = String(url)
    if (!urlStr.includes('/api/mcp/db/query')) {
      return { ok: false, status: 500, text: async () => 'unexpected' }
    }
    const body = JSON.parse((opts as { body: string }).body) as { sql?: string }
    const sql = body.sql ?? ''

    // Query 1: kala_gochara_authority → empty (v1 path)
    if (sql.includes('kala_gochara_authority')) {
      return { ok: true, json: async () => ({ rows: [] }) }
    }
    // Query 2: gochara_resonance_map → classRows
    if (sql.includes('gochara_resonance_map')) {
      return { ok: true, json: async () => ({ rows: classRows }) }
    }
    // Query 3: brahma_event_ontology universe
    if (sql.includes('brahma_event_ontology') && sql.includes('DISTINCT domain')) {
      return { ok: true, json: async () => ({ rows: universeDomains.map((d) => ({ domain: d })) }) }
    }
    // Query 4: build_substep_progress
    if (sql.includes('build_substep_progress')) {
      return {
        ok: true,
        json: async () => ({
          rows: [{
            substeps_committed: sweptClasses.length,
            swept_event_classes: sweptClasses,
          }],
        }),
      }
    }
    return { ok: true, json: async () => ({ rows: [] }) }
  }) as unknown as typeof fetch
}

describe('computeGocharaCoverage — C3 coverage_quality field', () => {
  it('0 covered classes → tier thin, covered_class_count 0, covered_domain_count 0', async () => {
    mockCoverageFetch([], [])
    const { coverage } = await computeGocharaCoverage(CHART_ID, TEST_PRINCIPAL)
    expect(coverage.coverage_quality).toBeDefined()
    expect(coverage.coverage_quality.tier).toBe('thin')
    expect(coverage.coverage_quality.covered_class_count).toBe(0)
    expect(coverage.coverage_quality.covered_domain_count).toBe(0)
  })

  it('3 covered classes → tier thin', async () => {
    const classes = ['career_advancement', 'marriage_formation', 'major_gain']
    mockCoverageFetch(makeClassRows(classes), classes)
    const { coverage } = await computeGocharaCoverage(CHART_ID, TEST_PRINCIPAL)
    expect(coverage.coverage_quality.tier).toBe('thin')
    expect(coverage.coverage_quality.covered_class_count).toBe(3)
  })

  it('4 covered classes → tier moderate', async () => {
    const classes = ['career_advancement', 'marriage_formation', 'major_gain', 'health_crisis']
    mockCoverageFetch(makeClassRows(classes), classes)
    const { coverage } = await computeGocharaCoverage(CHART_ID, TEST_PRINCIPAL)
    expect(coverage.coverage_quality.tier).toBe('moderate')
    expect(coverage.coverage_quality.covered_class_count).toBe(4)
  })

  it('9 covered classes → tier moderate', async () => {
    const classes = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9']
    mockCoverageFetch(makeClassRows(classes), classes)
    const { coverage } = await computeGocharaCoverage(CHART_ID, TEST_PRINCIPAL)
    expect(coverage.coverage_quality.tier).toBe('moderate')
    expect(coverage.coverage_quality.covered_class_count).toBe(9)
  })

  it('10 covered classes → tier rich', async () => {
    const classes = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'c10']
    mockCoverageFetch(makeClassRows(classes), classes)
    const { coverage } = await computeGocharaCoverage(CHART_ID, TEST_PRINCIPAL)
    expect(coverage.coverage_quality.tier).toBe('rich')
    expect(coverage.coverage_quality.covered_class_count).toBe(10)
  })

  it('covered_domain_count counts distinct domains across covered classes', async () => {
    // 4 classes across 3 distinct domains
    const classRows = [
      { event_class: 'career_advancement', domain: 'career' },
      { event_class: 'job_loss', domain: 'career' },
      { event_class: 'marriage_formation', domain: 'relationship' },
      { event_class: 'major_gain', domain: 'finance' },
    ]
    const swept = ['career_advancement', 'job_loss', 'marriage_formation', 'major_gain']
    mockCoverageFetch(classRows, swept)
    const { coverage } = await computeGocharaCoverage(CHART_ID, TEST_PRINCIPAL)
    expect(coverage.coverage_quality.covered_domain_count).toBe(3)
  })

  it('reason string is non-empty and contains the tier name', async () => {
    const classes = ['career_advancement', 'marriage_formation', 'major_gain']
    mockCoverageFetch(makeClassRows(classes), classes)
    const { coverage } = await computeGocharaCoverage(CHART_ID, TEST_PRINCIPAL)
    expect(typeof coverage.coverage_quality.reason).toBe('string')
    expect(coverage.coverage_quality.reason.length).toBeGreaterThan(0)
    expect(coverage.coverage_quality.reason).toContain('thin')
  })

  it('reason string for rich tier contains "rich"', async () => {
    const classes = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'c10']
    mockCoverageFetch(makeClassRows(classes), classes)
    const { coverage } = await computeGocharaCoverage(CHART_ID, TEST_PRINCIPAL)
    expect(coverage.coverage_quality.reason).toContain('rich')
  })
})

// ── buildNestedHierarchy — C2 era⊃month⊃day nesting ───────────────────────
describe('buildNestedHierarchy', () => {
  it('returns empty roots and empty legacy_flat for an empty input', () => {
    const result = buildNestedHierarchy([])
    expect(result.roots).toEqual([])
    expect(result.legacy_flat).toEqual([])
    expect(result.coverage_note).toContain('0 windows')
  })

  it('places an era-tier window as a root with empty children', () => {
    const era = makeServedWindow({ id: 10, resolution: 'era', parent_window_id: null })
    const result = buildNestedHierarchy([era])
    expect(result.roots).toHaveLength(1)
    expect(result.roots[0]?.resolution).toBe('era')
    expect(result.roots[0]?.window.id).toBe(10)
    expect(result.roots[0]?.children).toEqual([])
    expect(result.legacy_flat).toEqual([])
  })

  it('nests a month window under its era parent', () => {
    const era = makeServedWindow({ id: 10, resolution: 'era', parent_window_id: null })
    const month = makeServedWindow({ id: 20, resolution: 'month', parent_window_id: 10 })
    const result = buildNestedHierarchy([era, month])
    expect(result.roots).toHaveLength(1)
    const eraNode = result.roots[0] as HierarchyNode
    expect(eraNode.children).toHaveLength(1)
    expect(eraNode.children[0]?.resolution).toBe('month')
    expect(eraNode.children[0]?.window.id).toBe(20)
    expect(eraNode.children[0]?.children).toEqual([])
    expect(result.legacy_flat).toEqual([])
  })

  it('nests a day window under its month parent', () => {
    const era = makeServedWindow({ id: 10, resolution: 'era', parent_window_id: null })
    const month = makeServedWindow({ id: 20, resolution: 'month', parent_window_id: 10 })
    const day = makeServedWindow({ id: 30, resolution: 'day', parent_window_id: 20 })
    const result = buildNestedHierarchy([era, month, day])
    expect(result.roots).toHaveLength(1)
    const eraNode = result.roots[0] as HierarchyNode
    expect(eraNode.children).toHaveLength(1)
    const monthNode = eraNode.children[0] as HierarchyNode
    expect(monthNode.children).toHaveLength(1)
    expect(monthNode.children[0]?.resolution).toBe('day')
    expect(monthNode.children[0]?.window.id).toBe(30)
    expect(monthNode.children[0]?.children).toEqual([])
    expect(result.legacy_flat).toEqual([])
  })

  it('handles multiple era roots each with their own month/day subtrees', () => {
    const era1 = makeServedWindow({ id: 1, resolution: 'era', parent_window_id: null })
    const era2 = makeServedWindow({ id: 2, resolution: 'era', parent_window_id: null })
    const month1 = makeServedWindow({ id: 11, resolution: 'month', parent_window_id: 1 })
    const month2 = makeServedWindow({ id: 12, resolution: 'month', parent_window_id: 2 })
    const day1 = makeServedWindow({ id: 21, resolution: 'day', parent_window_id: 11 })
    const result = buildNestedHierarchy([era1, era2, month1, month2, day1])
    expect(result.roots).toHaveLength(2)
    const node1 = result.roots.find((n) => n.window.id === 1) as HierarchyNode
    const node2 = result.roots.find((n) => n.window.id === 2) as HierarchyNode
    expect(node1.children).toHaveLength(1)
    expect(node1.children[0]?.children).toHaveLength(1)
    expect(node1.children[0]?.children[0]?.window.id).toBe(21)
    expect(node2.children).toHaveLength(1)
    expect(node2.children[0]?.children).toEqual([])
    expect(result.legacy_flat).toEqual([])
  })

  it('puts resolution=null windows into legacy_flat, not roots', () => {
    const legacy = makeServedWindow({ id: 99, resolution: null, parent_window_id: null })
    const result = buildNestedHierarchy([legacy])
    expect(result.roots).toEqual([])
    expect(result.legacy_flat).toHaveLength(1)
    expect(result.legacy_flat[0]?.id).toBe(99)
  })

  it('mixes era/month/day tree with legacy_flat correctly', () => {
    const era = makeServedWindow({ id: 10, resolution: 'era', parent_window_id: null })
    const month = makeServedWindow({ id: 20, resolution: 'month', parent_window_id: 10 })
    const legacy = makeServedWindow({ id: 5, resolution: null, parent_window_id: null })
    const result = buildNestedHierarchy([era, month, legacy])
    expect(result.roots).toHaveLength(1)
    expect(result.legacy_flat).toHaveLength(1)
    expect(result.legacy_flat[0]?.id).toBe(5)
    expect(result.coverage_note).toContain('2 windows organized')
    expect(result.coverage_note).toContain('1 legacy')
  })

  it('places a window with a parent_window_id pointing to a non-present parent into legacy_flat (defensive)', () => {
    // month claims parent 999 which is not in the array
    const orphan = makeServedWindow({ id: 20, resolution: 'month', parent_window_id: 999 })
    const result = buildNestedHierarchy([orphan])
    expect(result.roots).toEqual([])
    expect(result.legacy_flat).toHaveLength(1)
    expect(result.legacy_flat[0]?.id).toBe(20)
  })

  it('coverage_note counts only nested windows, not legacy', () => {
    const era = makeServedWindow({ id: 1, resolution: 'era', parent_window_id: null })
    const month = makeServedWindow({ id: 2, resolution: 'month', parent_window_id: 1 })
    const legacy = makeServedWindow({ id: 3, resolution: null, parent_window_id: null })
    const result = buildNestedHierarchy([era, month, legacy])
    expect(result.coverage_note).toContain('2 windows organized')
    expect(result.coverage_note).toContain('1 legacy')
    expect(result.coverage_note).toContain('migration 567')
  })
})

// ── computeGocharaForecast — nested_hierarchy field presence ───────────────
describe('computeGocharaForecast — nested_hierarchy in response', () => {
  function mockFetchForecast(rows: Record<string, unknown>[]) {
    let mainQueryServed = false
    global.fetch = vi.fn(async (url: unknown, opts: unknown) => {
      const urlStr = String(url)
      if (urlStr.includes('/api/mcp/db/query')) {
        const body = JSON.parse((opts as { body: string }).body) as { sql?: string }
        const sql = body.sql ?? ''
        // The main forecast SELECT is the only query that: (a) reads kala_gochara_windows,
        // (b) filters on window_start/window_end, and (c) has no is_adverse clause.
        // Serve `rows` exactly once for this query; everything else (coverage, verse refs) returns [].
        if (!mainQueryServed && sql.includes('kala_gochara_windows') && sql.includes('window_start')) {
          mainQueryServed = true
          return { ok: true, json: async () => ({ rows }) }
        }
        return { ok: true, json: async () => ({ rows: [] }) }
      }
      return { ok: false, status: 500, text: async () => 'unexpected fetch in test' }
    }) as unknown as typeof fetch
  }

  it('response includes nested_hierarchy with roots and legacy_flat', async () => {
    const eraRow = {
      id: 10, chart_id: CHART_ID, event_class: 'marriage',
      temporal_shape: 'point', window_start: '2026-01-01', window_end: '2026-01-01',
      peak_date: '2026-01-01', milestone_id: null, is_irreversibility_milestone: false,
      signed_intensity: 1.0, raw_intensity: 1.0, valence: 'gain', is_adverse: false,
      active_sentences: [], contributing_systems: [], suppression_state: {},
      peak_basis: 'gochara_lambda_e_v1', calibration_state: 'structural_prior',
      source: 'live', computed_at: '2026-01-01T00:00:00Z',
      continuity_state: null, generation: 'g3_utkarsha',
      era_slice_key: 'g3_2024_2034', term_breakdown: null,
      resolution: 'era', parent_window_id: null, shape_conformance: null,
    }
    mockFetchForecast([eraRow])

    const result = (await computeGocharaForecast(
      CHART_ID,
      { start: '2026-01-01', end: '2027-01-01' },
      undefined, undefined, 50, TEST_PRINCIPAL
    )) as { nested_hierarchy: { roots: HierarchyNode[]; legacy_flat: unknown[]; coverage_note: string } }

    expect(result.nested_hierarchy).toBeDefined()
    expect(Array.isArray(result.nested_hierarchy.roots)).toBe(true)
    expect(Array.isArray(result.nested_hierarchy.legacy_flat)).toBe(true)
    expect(typeof result.nested_hierarchy.coverage_note).toBe('string')
    expect(result.nested_hierarchy.roots).toHaveLength(1)
    expect(result.nested_hierarchy.roots[0]?.resolution).toBe('era')
  })

  it('response nested_hierarchy.legacy_flat contains windows with resolution=null', async () => {
    const legacyRow = {
      id: 5, chart_id: CHART_ID, event_class: 'marriage',
      temporal_shape: 'point', window_start: '2026-06-01', window_end: '2026-06-01',
      peak_date: '2026-06-01', milestone_id: null, is_irreversibility_milestone: false,
      signed_intensity: 0.8, raw_intensity: 0.8, valence: 'neutral', is_adverse: false,
      active_sentences: [], contributing_systems: [], suppression_state: {},
      peak_basis: 'gochara_lambda_v1', calibration_state: 'structural_prior',
      source: 'live', computed_at: '2026-06-01T00:00:00Z',
      continuity_state: null, generation: null,
      era_slice_key: null, term_breakdown: null,
      resolution: null, parent_window_id: null, shape_conformance: null,
    }
    mockFetchForecast([legacyRow])

    const result = (await computeGocharaForecast(
      CHART_ID,
      { start: '2026-01-01', end: '2027-01-01' },
      undefined, undefined, 50, TEST_PRINCIPAL
    )) as { nested_hierarchy: { roots: unknown[]; legacy_flat: Array<{ id: number }> } }

    expect(result.nested_hierarchy.roots).toHaveLength(0)
    expect(result.nested_hierarchy.legacy_flat).toHaveLength(1)
    expect(result.nested_hierarchy.legacy_flat[0]?.id).toBe(5)
  })
})

// §N.6 density_contract presence is asserted directly on each tool's
// provenance_envelope in the live-integration checks below (the contract
// consts are module-private; the served INVARIANT — every response carries
// one — is what actually matters and is checked against real output).

// ── Integration (live platform DB proxy; gated on RUN_DB_INTEGRATION) ──────
// SARVA-SIDDHI W-1 T-1: these tools proxy through POST ${PLATFORM_URL}/api/mcp/db/query
// (the MCP server holds no direct DB connection), so the integration run needs a
// reachable platform (PLATFORM_URL + MCP_INTERNAL_TOKEN) and a valid principal — not a
// raw DATABASE_URL DSN.

const describeIntegration = process.env['RUN_DB_INTEGRATION'] === '1' ? describe : describe.skip

describeIntegration('gochara_*_get — live DB integration', () => {
  it('gochara_activation_get returns a shape-correct envelope for the marriage specimen date', async () => {
    const result = (await computeGocharaActivation(CHART_ID, '2013-12-11', TEST_PRINCIPAL, 'marriage')) as {
      windows: GocharaWindowRow[]
      provenance_envelope: Record<string, unknown>
    }
    expect(result.provenance_envelope.density_contract).toBeDefined()
    expect(Array.isArray(result.windows)).toBe(true)
    for (const w of result.windows) {
      expect(w.window_start).toBe(w.window_end)
    }
  })

  it('gochara_forecast_get returns rows overlapping the windfall interval specimen', async () => {
    const result = (await computeGocharaForecast(
      CHART_ID,
      { start: '2010-06-01', end: '2011-04-01' },
      'major_gain',
      undefined,
      50,
      TEST_PRINCIPAL
    )) as { windows: GocharaWindowRow[]; provenance_envelope: Record<string, unknown> }
    expect(result.provenance_envelope.shape_breakdown).toBeDefined()
    for (const w of result.windows) {
      expect(w.temporal_shape).toBe('interval')
      expect(w.window_start < w.window_end).toBe(true)
    }
  })

  it('gochara_election_avoidance_get carries all 5 DR-16 properties on any adverse row', async () => {
    const result = (await computeGocharaElectionAvoidance(
      CHART_ID,
      { start: '1950-01-01', end: '2050-01-01' },
      undefined,
      50,
      TEST_PRINCIPAL
    )) as { windows: Array<Record<string, unknown>>; provenance_envelope: Record<string, unknown> }
    expect(result.provenance_envelope.dr16_properties).toEqual([
      'honest_clarity',
      'probabilistic_never_fatalistic',
      'falsifier_bearing',
      'mitigation_paired',
      'confidence_honest',
    ])
    for (const w of result.windows) {
      expect(w['clarity_statement']).toBeDefined()
      expect(w['framing']).toBeDefined()
      expect(w['falsifier']).toBeDefined()
      expect(w['mitigation']).toBeDefined()
      expect(w['confidence_disclosure']).toBeDefined()
    }
  })
})
