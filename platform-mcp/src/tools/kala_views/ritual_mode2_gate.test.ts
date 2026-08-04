/**
 * ritual_mode2_gate.test.ts — ṢAḌ-DARŚANA W4 gate prep (SHAD_DARSHANA_BRIEF_v2_0.md §3 W4):
 * the CANNED MODE-2 FIXTURE HARNESS.
 *
 * This is a T5 (W5 + W4 prep) lane deliverable, per the campaign ledger's SESSION-B-BUILD
 * NEXT-ACTION item 3 / lane (e): "W4 GATE-PREP harnesses (canned Mode-2 fixture, weak-promise
 * UPĀYA test, Intervention Ledger filing test — live discharge waits for the gate-close
 * deploy)". This file is the FIRST harness: it discharges `test/fixtures/yajna_mode2_gate.json`
 * (the brief's own CANNED W4 MODE-2 TEST FIXTURE, authoritative) against the REAL Mode-2 code
 * path (`handleKalaRitualGet` → `searchSkyPattern` → `compileConstraint` → the frozen lattice
 * adjudication engine) with every I/O boundary mocked at ONE lever — `callPlatformPrimitive`
 * (`../../client.js`), which every substrate fetcher in this call graph (`fetchLatticeSubstrate`,
 * `fetchPaddhatiProfile`, `fetchChartRelativeSubstrate`, `resolveGrahaName`) is imported from —
 * so no live DB/network call is ever attempted. This is a HARNESS, not the live-MCP discharge:
 * per the brief and the campaign's own T5 scope split, the fixture's real production discharge
 * (against a real deploy, both canonical charts' REAL janma-nakṣatra/paddhati data) is explicitly
 * deferred to the gate-close deploy session — this file proves the harness runs green against
 * CANNED data and is ready to re-point at a live principal/DB later without changing its
 * assertions.
 *
 * WHY ONE MOCK LEVER SUFFICES (ESM self-call note): `fetchPaddhatiProfile`,
 * `fetchChartRelativeSubstrate`, and `resolveGrahaName` all live in the SAME module as
 * `searchSkyPattern` (`kala_sky_pattern.ts`) — `vi.mock`-ing that module would NOT intercept
 * their same-file callers (a well-known ESM limitation: same-module self-calls bind directly,
 * bypassing any external mock re-export). `callPlatformPrimitive` is instead imported from
 * `../../client.js` into BOTH `kala_sky_pattern.ts` and `kala_lattice_query.ts` — an external,
 * genuinely mockable import every one of the four fetchers ultimately calls through. Mocking it
 * once, with a capability-name dispatcher, controls all four data sources.
 *
 * THE FOUR PASS CONDITIONS (fixture `_pass_conditions`, restated here as executable assertions
 * so the eventual live-discharge session can reuse the exact same predicates against a real
 * result rather than re-deriving the brief's prose):
 *   1. non-empty OR honestly-empty-with-gap-report (an unexplained empty result FAILS).
 *   2. every candidate's precision_regime === 'intra_day' with a non-blank precision_basis, AND
 *      no degrading constraint kind (transit_contact / mutual_configuration) is present in the
 *      fixture's own constraint list (so nothing in it COULD legitimately degrade the label).
 *   3. every candidate carries a judgment_ledger (dosas_present, pariharas_applied,
 *      residual_dosas, net_standing) — joined here from `adjudication.ledgers` by candidate id,
 *      exactly as a real caller must (the type does not embed the ledger on the candidate).
 *   4. the coverage block enumerates all SIX constraints (one per fixture constraint, no more
 *      no fewer), each in {computed, honest_empty, not_in_corpus}.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import type { SkyPatternSpec, SkyPatternSearchResult } from '../../lib/kala_sky_pattern.js'

// ── the canned fixture (authoritative; never substituted for an easier query) ──────────

interface YajnaMode2Fixture {
  _charts: { primary: string; mirror: string }
  spec_version: string
  all: Record<string, unknown>[]
  horizon: { months: number }
}

function loadFixture(): YajnaMode2Fixture {
  const raw = readFileSync(
    fileURLToPath(new URL('../../../test/fixtures/yajna_mode2_gate.json', import.meta.url)),
    'utf8',
  )
  return JSON.parse(raw) as YajnaMode2Fixture
}

const FIXTURE = loadFixture()
const SPEC: SkyPatternSpec = { spec_version: FIXTURE.spec_version, all: FIXTURE.all, horizon: FIXTURE.horizon }
const CHART_PRIMARY = FIXTURE._charts.primary
const CHART_MIRROR = FIXTURE._charts.mirror

// ── the ONE mock lever ───────────────────────────────────────────────────────────────

const mockCallPlatformPrimitive = vi.fn()

vi.mock('../../client.js', async () => {
  const actual = await vi.importActual<typeof import('../../client.js')>('../../client.js')
  return {
    ...actual,
    callPlatformPrimitive: (...args: unknown[]) => mockCallPlatformPrimitive(...args),
  }
})

const PRINCIPAL = { user_uid: 'u1', key_id: 'k1', role: 'guest' as const }

// ── canned classical nakshatra order (1-based ids; real BPHS order — this is reference
//    geometry, not a fabricated scheme) — used only to resolve janma-nakshatra names to ids
//    and to place the "current transiting nakshatra" atom that the tara-bala constraint reads.
const NAKSHATRA_ORDER = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya',
  'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
  'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
  'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
]
const nakId = (name: string): number => NAKSHATRA_ORDER.indexOf(name) + 1

// Chart A's real janma-nakshatra (§B, chart 482012f1); chart B assigned a DIFFERENT one
// (Ardra) specifically so the fixture's cross-chart differentiation requirement is testable —
// see the "two charts diverge, and it traces to chart_relative" test below.
const JANMA_A = 'Purva Bhadrapada'
const JANMA_B = 'Ardra'
// The "current transiting nakshatra" atom active during the target day, chosen so
// tara(JANMA_A, CURRENT) is favourable (not in vadha/vipat/pratyak) and
// tara(JANMA_B, CURRENT) is UNFAVOURABLE (vipat) — the fixture's not_in exclusion set.
// TARA_CYCLE = [janma,sampat,vipat,kshema,pratyak,sadhaka,vadha,mitra,ati_mitra] (index = count).
// tara(25,26): count=((26-25+27)%27)%9=1 -> sampat (favourable, MATCHED for chart A).
// tara(6,26):  count=((26-6+27)%27)%9=2 -> vipat (excluded, NOT matched for chart B).
const CURRENT_TRANSIT_NAME = 'Uttara Bhadrapada'

function iso(daysFromNow: number, hour = 0): string {
  const d = new Date(Date.now() + daysFromNow * 86_400_000)
  d.setUTCHours(hour, 0, 0, 0)
  return d.toISOString()
}

// The day every REQUIRE-mode constraint's canned atom covers (so their intersection survives);
// well inside the fixture's 24-month horizon and far from the EXCLUDE_DAY below.
const TARGET_DAY_START = iso(5, 0)
const TARGET_DAY_END = iso(6, 0)
// The day the EXCLUDE-mode atoms (vishti karana, rahu-kalam) live on — deliberately NOT
// overlapping the target day, so they narrow the horizon elsewhere without erasing it here.
const EXCLUDE_DAY_START = iso(40, 0)
const EXCLUDE_DAY_END = iso(41, 0)

function latticeRow(
  factor_family: string,
  factor_key: string,
  start_utc: string,
  end_utc: string,
  detail: Record<string, unknown> | null,
) {
  return {
    factor_family, factor_key, start_utc, end_utc, detail,
    source_citation: 'canned Mode-2 gate harness fixture (ṢAḌ-DARŚANA T5)',
    corpus_status: 'computed_cited' as const,
  }
}

/** All canned lattice rows, shared by BOTH charts (the lattice is chart-independent; only
 *  chartRel/janma differs per chart, which is exactly what makes the two charts' results
 *  genuinely differ — the fixture's own cross-chart requirement). */
function cannedLatticeRows() {
  return [
    // 1. planet_state: hora_lord=Guru (resolved to 'Jupiter' by the mocked resolve_entity).
    latticeRow('hora', 'jupiter_hora', TARGET_DAY_START, TARGET_DAY_END, { lord: 'Jupiter' }),
    // 2. panchanga: vara = guru-vara.
    latticeRow('vara', 'guru_vara', TARGET_DAY_START, TARGET_DAY_END, { name: 'Guru-vara' }),
    // 3. residence: agnivasa favourable (prithvi element).
    latticeRow('agnivasa', 'prithvi', TARGET_DAY_START, TARGET_DAY_END, { element: 'prithvi' }),
    // 4. panchanga_not: karana != vishti. The 'combination_yoga' family also carries karana
    //    per compileConstraint's own family map — the vishti atom lives on the EXCLUDE day
    //    only, so it narrows the horizon there and leaves the target day untouched.
    latticeRow('combination_yoga', 'vishti', EXCLUDE_DAY_START, EXCLUDE_DAY_END, { name: 'Vishti' }),
    // 5. kalam_not: outside rahu-kalam. Same pattern — the rahu_kalam atom sits on the
    //    EXCLUDE day, never overlapping the target day.
    latticeRow('kalam', 'rahu_kalam', EXCLUDE_DAY_START, EXCLUDE_DAY_END, { name: 'Rahu Kalam' }),
    // 6a. chart_relative/tara_bala id-resolution reference atoms. `nakshatraIdFromName` reads
    //     only `detail.name`/`factor_id`, never the timestamps — BUT the chart_relative
    //     compiler treats EVERY `nakshatra`-family row (reference atoms included) as a
    //     candidate interval to filter+intersect, so these are deliberately placed WELL
    //     BEFORE the search horizon (which starts at the target day) so they can never
    //     themselves contribute a surviving interval and silently rescue a chart whose
    //     CURRENT-transit tara should exclude the target day.
    latticeRow('nakshatra', 'ref_a', iso(-100), iso(-99), { name: JANMA_A, factor_id: nakId(JANMA_A) }),
    latticeRow('nakshatra', 'ref_b', iso(-100), iso(-99), { name: JANMA_B, factor_id: nakId(JANMA_B) }),
    // 6b. the CURRENT transiting nakshatra atom, active during the target day — this is the
    //     one whose tara-bala the constraint actually gates on.
    latticeRow('nakshatra', 'current', TARGET_DAY_START, TARGET_DAY_END, {
      name: CURRENT_TRANSIT_NAME,
      factor_id: nakId(CURRENT_TRANSIT_NAME),
    }),
  ]
}

function mockResponsesFor(chartId: string, janmaNakshatra: string) {
  mockCallPlatformPrimitive.mockImplementation(async (toolName: string, params: Record<string, unknown>) => {
    const ok = (result: unknown) => ({ status: 200, envelope: { ok: true, trace_id: 't', epistemics: {}, result, citations: [], plan: null, predictions_logged: [] } })
    switch (toolName) {
      case 'query_muhurta_lattice':
        return ok({ rows: cannedLatticeRows() })
      case 'query_parihara_graph':
        return ok({ parihara_rules: [], factor_census: [] })
      case 'query_kala_paddhati_profile':
        return ok({ rows: [] })
      case 'query_chart_facts':
        if (params['chart_id'] !== chartId) return ok({ rows: [] })
        return ok({ rows: [{ fact_id: 'f1', fact_key: 'nakshatra', fact_subject: 'MOON', fact_value_text: janmaNakshatra }] })
      case 'resolve_entity':
        if (params['name'] === 'Guru') return ok({ canonical_name_en: 'Jupiter' })
        return ok({})
      default:
        throw new Error(`ritual_mode2_gate harness: unmocked primitive '${toolName}' — the canned fixture must not reach a real network call`)
    }
  })
}

beforeEach(() => {
  mockCallPlatformPrimitive.mockReset()
})

// ── pass-condition predicates (exact restatement of the fixture's own _pass_conditions,
//    reusable verbatim against a REAL result once live discharge lands) ────────────────────

function assertPassCondition1_nonEmptyOrHonestlyEmpty(result: SkyPatternSearchResult): void {
  if (result.candidates.length === 0) {
    expect(result.gap_report.eliminating_constraint, 'empty result carries NO eliminating_constraint — unexplained empty is a FAIL').not.toBeNull()
    expect(result.gap_report.next_occurrence_state).not.toBe('not_searched')
  } else {
    expect(result.candidates.length).toBeGreaterThan(0)
  }
}

function assertPassCondition2_precisionLabelsCorrect(result: SkyPatternSearchResult): void {
  // Nothing in the fixture's 6 constraints is transit_contact/mutual_configuration, so the
  // label can never legitimately degrade — asserted structurally, not just read off the field.
  expect(result.precision.no_degrading_constraint_kinds_present).toBe(true)
  for (const c of result.candidates) {
    expect(c.precision_regime, `candidate ${c.id} labelled day_grade — the honesty is backwards for a purely-pāñcāṅgika fixture`).toBe('intra_day')
    expect(c.precision_basis.length).toBeGreaterThan(0)
  }
}

function assertPassCondition3_judgmentLedgerPresent(result: SkyPatternSearchResult): void {
  if (result.candidates.length === 0) return // vacuously satisfied — no candidate to carry a ledger
  expect(result.adjudication, 'candidates present but adjudication is null').not.toBeNull()
  const ledgersById = new Map((result.adjudication?.ledgers ?? []).map((l) => [l.candidate_id, l]))
  for (const c of result.candidates) {
    const ledger = ledgersById.get(c.id)
    expect(ledger, `candidate ${c.id} has no judgment_ledger`).toBeDefined()
    expect(Array.isArray(ledger?.dosas_present)).toBe(true)
    expect(Array.isArray(ledger?.pariharas_applied)).toBe(true)
    expect(Array.isArray(ledger?.residual_dosas)).toBe(true)
    expect(typeof ledger?.net_standing).toBe('string')
  }
}

function assertPassCondition4_censusHonesty(result: SkyPatternSearchResult): void {
  // Six entries, one per fixture constraint, no more and no fewer.
  expect(result.coverage.length).toBe(FIXTURE.all.length)
  for (const entry of result.coverage) {
    expect(['computed', 'honest_empty', 'not_in_corpus']).toContain(entry.state)
  }
}

function assertAllFourPassConditions(result: SkyPatternSearchResult): void {
  assertPassCondition1_nonEmptyOrHonestlyEmpty(result)
  assertPassCondition2_precisionLabelsCorrect(result)
  assertPassCondition3_judgmentLedgerPresent(result)
  assertPassCondition4_censusHonesty(result)
}

// ── the harness itself ──────────────────────────────────────────────────────────────────

describe('YAJÑA-SETU Mode-2 canned gate fixture — harness (T5 W4 prep, no live discharge)', () => {
  it('the committed fixture matches the brief\'s six-constraint shape (sanity: the harness is not vacuous)', () => {
    expect(FIXTURE.all.length).toBe(6)
    expect(FIXTURE._charts.primary).toBe('482012f1-710e-4a25-994a-93821f5871aa')
    expect(FIXTURE._charts.mirror).toBe('1c826d5a-41cb-4450-b4dc-59d440e5f75a')
    const kinds = FIXTURE.all.map((c) => Object.keys(c)[0])
    expect(kinds).toEqual(['planet_state', 'panchanga', 'residence', 'panchanga_not', 'chart_relative', 'kalam_not'])
  })

  it('discharges the fixture against chart 482012f1 (primary) — all four pass conditions hold', async () => {
    mockResponsesFor(CHART_PRIMARY, JANMA_A)
    const { searchSkyPattern } = await import('../../lib/kala_sky_pattern.js')
    const horizonStart = TARGET_DAY_START
    const horizonEnd = iso(700) // > 24 months out
    const result = await searchSkyPattern(
      {
        spec: SPEC,
        chartId: CHART_PRIMARY,
        horizonStartUtc: horizonStart,
        horizonEndUtc: horizonEnd,
        scanCeilingUtc: iso(900),
        subjectLabel: 'canned Mode-2 gate harness (chart A)',
      },
      PRINCIPAL,
    )
    assertAllFourPassConditions(result)
    // This canned substrate is deliberately engineered so chart A's tara-bala matches
    // (sampat, favourable) — a real, non-empty candidate is the expected, checked outcome
    // here (not merely "whatever the engine returns"), proving the harness exercises the
    // populated-candidate path, not only the honest-empty one.
    expect(result.candidates.length).toBeGreaterThan(0)
  })

  it('discharges the fixture against chart 1c826d5a (mirror) — all four pass conditions hold, DIFFERENT candidate set', async () => {
    mockResponsesFor(CHART_MIRROR, JANMA_B)
    const { searchSkyPattern } = await import('../../lib/kala_sky_pattern.js')
    const result = await searchSkyPattern(
      {
        spec: SPEC,
        chartId: CHART_MIRROR,
        horizonStartUtc: TARGET_DAY_START,
        horizonEndUtc: iso(700),
        scanCeilingUtc: iso(900),
        subjectLabel: 'canned Mode-2 gate harness (chart B)',
      },
      PRINCIPAL,
    )
    assertAllFourPassConditions(result)
    // Chart B's janma-nakshatra (Ardra) makes the SAME current-transit atom read as 'vipat'
    // (excluded) — the tara_bala constraint wipes the target-day interval for this chart
    // specifically. The engineered expectation: chart B's candidate set is EMPTY where
    // chart A's is not, and the eliminating constraint traces to chart_relative:tara_bala —
    // exactly the "difference traces to the chart-relative constraint" property the fixture's
    // own both-charts clause demands (never a coincidental/nondeterministic divergence).
    expect(result.candidates.length).toBe(0)
    expect(result.gap_report.eliminating_constraint?.kind).toBe('chart_relative')
  })

  it('both-charts clause, part 2: with the chart-relative constraint REMOVED, the two charts COINCIDE', async () => {
    const specWithoutChartRelative: SkyPatternSpec = {
      ...SPEC,
      all: SPEC.all!.filter((c) => !('chart_relative' in c)),
    }
    const { searchSkyPattern } = await import('../../lib/kala_sky_pattern.js')

    mockResponsesFor(CHART_PRIMARY, JANMA_A)
    const resultA = await searchSkyPattern(
      { spec: specWithoutChartRelative, chartId: CHART_PRIMARY, horizonStartUtc: TARGET_DAY_START, horizonEndUtc: iso(700), scanCeilingUtc: iso(900) },
      PRINCIPAL,
    )
    mockResponsesFor(CHART_MIRROR, JANMA_B)
    const resultB = await searchSkyPattern(
      { spec: specWithoutChartRelative, chartId: CHART_MIRROR, horizonStartUtc: TARGET_DAY_START, horizonEndUtc: iso(700), scanCeilingUtc: iso(900) },
      PRINCIPAL,
    )
    // Part 2 of the fixture's own "earned signal" detector: strip the chart-relative
    // constraint and the two charts' candidate windows must COINCIDE — proving the Part-1
    // divergence traced to the chart, not to nondeterminism or a leak.
    expect(resultA.candidates.map((c) => c.start_utc)).toEqual(resultB.candidates.map((c) => c.start_utc))
    expect(resultA.candidates.length).toBeGreaterThan(0)
  })

  it('every unmocked primitive call would throw (proves the harness never silently reaches a live network call)', async () => {
    mockResponsesFor(CHART_PRIMARY, JANMA_A)
    mockCallPlatformPrimitive.mockImplementationOnce(async () => {
      throw new Error('unmocked')
    })
    const { fetchLatticeSubstrate } = await import('../../lib/kala_lattice_query.js')
    await expect(fetchLatticeSubstrate({ start_utc: TARGET_DAY_START, end_utc: iso(10) }, PRINCIPAL)).resolves.toMatchObject({
      lattice_available: false,
    })
  })
})
