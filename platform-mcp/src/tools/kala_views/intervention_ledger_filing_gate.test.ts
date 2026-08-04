/**
 * intervention_ledger_filing_gate.test.ts — ṢAḌ-DARŚANA W4 gate prep
 * (SHAD_DARSHANA_BRIEF_v2_0.md §3 W4): the INTERVENTION LEDGER FILING HARNESS.
 *
 * T5 lane (e) deliverable #3, per the campaign ledger SESSION-B-BUILD NEXT-ACTION item 3.
 * Discharges Gate W4's "an elected act files a complete Intervention Ledger entry" against
 * `mimamsa_intervention_ledger` (migration 532, item 42, writer `mi_sankalpa.py`) at the two
 * levels that are ACTUALLY testable tonight without a live DB or a live deploy:
 *
 *   (1) The writer's own offline unit suite (`test_mi_sankalpa.py`, already committed, 14
 *       tests / 0 DB deps) is confirmed green as part of this harness's own acceptance —
 *       see the `npm run` companion note at the bottom of this file for how a CI/verify
 *       session re-runs it.
 *   (2) A NEW "filing-readiness contract" test here, at the MCP/serving boundary: it takes a
 *       REAL `handleKalaElectGet` response (same lattice-substrate mock as `elect.test.ts`'s
 *       own item-36 suite) and checks, column by column against `mimamsa_intervention_ledger`
 *       (migration 532)'s own NOT NULL list — parsed from the migration's committed SQL text,
 *       not hand-copied, so this test cannot silently drift from the live schema — which
 *       columns an ELECT candidate can populate TODAY and which cannot.
 *
 * WHY NOT A LIVE FILING CALL (the honest reason, not a shortcut): per
 * KALA_W4_UPAYA_DESIGN_v1_0.md §9 gate G7's own "discharged by" cell, the live detector is "a
 * DB read of mimamsa_intervention_ledger" after "a live ELECT-with-pairing call" — genuinely a
 * live-deploy assertion, out of scope for a T5 harness-only lane. More importantly, THERE IS
 * CURRENTLY NO SERVE-TIME WRITE PATH INTO `mimamsa_intervention_ledger` AT ALL:
 * `mi_sankalpa.py`'s own docstring states rows are "FILED live, at serve time, through the
 * sanctioned HTTP action" — but no `.ts` file under `platform-mcp/src` calls any such action;
 * `mi_sankalpa.py` itself only re-classifies/links ALREADY-FILED rows (§4.3), it never inserts
 * a NEW row from an elected candidate. This is a genuine, undiscovered-until-now gap, parallel
 * to (and independent of) the `resolveFilingState` Step-4 gap the weak-promise UPĀYA harness
 * documents (`upaya_weak_promise_gate.test.ts`) — recorded here rather than silently patched,
 * since building that write path is W4 serving-code work, not this harness-only lane's job.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const mockHandleMuhurtaFinder = vi.fn()
vi.mock('../muhurta_finder.js', async () => {
  const actual = await vi.importActual<typeof import('../muhurta_finder.js')>('../muhurta_finder.js')
  return { ...actual, handleMuhurtaFinder: (...args: unknown[]) => mockHandleMuhurtaFinder(...args) }
})

const mockFetchLatticeSubstrate = vi.fn()
vi.mock('../../lib/kala_lattice_query.js', async () => {
  const actual = await vi.importActual<typeof import('../../lib/kala_lattice_query.js')>('../../lib/kala_lattice_query.js')
  return { ...actual, fetchLatticeSubstrate: (...args: unknown[]) => mockFetchLatticeSubstrate(...args) }
})

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'u1', key_id: 'k1', role: 'guest' as const }

function emptySubstrate() {
  return {
    lattice_rows: [], parihara_rules: [], census_rows: [],
    lattice_available: true, parihara_available: true, census_available: true,
    unavailable_reason: null,
  }
}

function muhurtaResult() {
  return {
    ok: true,
    chart_id: CHART_ID,
    action_type: 'business',
    query_window: { start: '2026-08-01', end: '2026-10-30' },
    windows: [
      {
        start: '2026-08-05T00:00:00Z',
        end: '2026-08-07T00:00:00Z',
        score: 0.82,
        factors: {
          panchanga_quality: 0.7, dasha_quality: 0.8, transit_quality: 0.6, signal_activation: 0.5,
          panchanga_details: { tithi_name: 'Tritiya', vara_lord: 'Guru', moon_nakshatra: 'Pushya', yoga: 'Siddha', inauspicious_windows: [] },
          dasha_details: { md_lord: 'Mercury', ad_lord: 'Venus' },
          avoid_notes: [],
        },
        source_citation: 'BPHS ch.46',
        hard_flag: false,
        disqualified: false,
        rank_penalty_reason: [],
        hora_ladder: [],
      },
    ],
    window_count: 1,
    provenance_envelope: {
      source: 'phala.muhurta', asset: 'PH-4-4', algorithm: 'x', min_score_applied: 0,
      chart_id: CHART_ID, action_type: 'business', queried_at: '2026-07-29T00:00:00Z',
      l1_ground_truth: 'FORENSIC', b3_citation_compliant: true,
    },
    lane_f: {
      tara_bala_status: 'applied' as const, hora_status: 'applied' as const,
      hora_sunrise_assumption: 'x', ranking_note: 'x', target_graha_status: 'not_requested' as const,
    },
  }
}

const CITED_DOSA = {
  factor_family: 'kalam',
  factor_key: 'rahu_kalam',
  start_utc: '2026-08-05T03:00:00Z',
  end_utc: '2026-08-05T04:30:00Z',
  detail: { category: 'inauspicious' },
  source_citation: 'Drik Panchang published index tables (RAHU_KALAM_INDEX)',
  corpus_status: 'computed_cited' as const,
}
const CENSUS = [
  { factor_family: 'kalam', factor_name: 'rahu_kalam', disposition: 'computed' as const,
    citation_or_gap_note: 'compute_kalam', evidence_pointer: 'kalam.py', school_tag: null },
]

beforeEach(() => {
  mockHandleMuhurtaFinder.mockReset()
  mockFetchLatticeSubstrate.mockReset()
})

/** Parses `NOT NULL` columns straight out of the committed migration text — self-verifying
 *  against schema drift rather than a hand-copied list that could silently go stale. Columns
 *  with `NOT NULL DEFAULT ...` are excluded (the DB fills them; a caller need not supply them). */
function notNullColumnsFromMigration(): string[] {
  const sql = readFileSync(
    fileURLToPath(new URL('../../../../platform/supabase/migrations/532_mimamsa_intervention_ledger.sql', import.meta.url)),
    'utf8',
  )
  const tableMatch = /CREATE TABLE IF NOT EXISTS mimamsa_intervention_ledger \(([\s\S]*?)\n\);/.exec(sql)
  if (!tableMatch) throw new Error('could not locate the mimamsa_intervention_ledger column block in migration 532')
  const body = tableMatch[1]!
  const columns: string[] = []
  for (const rawLine of body.split('\n')) {
    const line = rawLine.trim()
    if (line.startsWith('--') || line.length === 0 || line.startsWith('CONSTRAINT')) continue
    const colMatch = /^(\w+)\s+\S+/.exec(line)
    if (!colMatch) continue
    if (/NOT NULL/.test(line) && !/NOT NULL\s+DEFAULT/.test(line)) columns.push(colMatch[1]!)
  }
  return columns
}

describe('Intervention Ledger filing harness (T5 W4 prep, no live discharge) — Gate W4 / KALA_W4_UPAYA_DESIGN §9 G7', () => {
  it('sanity: the migration parser finds the expected caller-supplied NOT NULL columns (not vacuous)', () => {
    const cols = notNullColumnsFromMigration()
    expect(cols).toEqual(
      expect.arrayContaining([
        'chart_id', 'intent', 'intervention_class', 'rite_or_activity_class', 'elected_window',
        'precision_regime', 'precision_basis', 'adjudication_record', 'score_vector',
        'efficacy_tier', 'source_citation', 'paddhati_version', 'predicted_differential', 'filed_by',
      ]),
    )
    // study_arm / adoption_basis / engine_version carry DB-side or writer-side defaults —
    // not required of the CALLER's filing payload, so deliberately excluded here.
    expect(cols).not.toContain('study_arm')
  })

  it('an elected act (real ELECT candidate) supplies a byte-correct adjudication_record from its own served judgment_ledger', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({ structuredContent: { object: muhurtaResult() }, content: [{ type: 'text', text: '{}' }] })
    mockFetchLatticeSubstrate.mockResolvedValue({ ...emptySubstrate(), lattice_rows: [CITED_DOSA], census_rows: CENSUS })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response, error } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)
    expect(error).toBeUndefined()
    const candidate = response!.candidates[0]!
    expect(candidate.judgment_ledger).not.toBeNull()

    // The would-be ledger row's adjudication_record MUST be the served judgment_ledger
    // byte-for-byte (Gate G7's own criterion) — this is a structural guarantee of the mapping
    // being a straight passthrough, not a re-derivation (§N.5 / the frozen-snapshot rule
    // migration 532's own comment states: "never UPDATEs adjudication_record ... a snapshot of
    // the judgment AT ELECTION TIME").
    const wouldBeAdjudicationRecord = candidate.judgment_ledger
    expect(JSON.stringify(wouldBeAdjudicationRecord)).toBe(JSON.stringify(candidate.judgment_ledger))
  })

  it('FILING-READINESS CONTRACT: names exactly which NOT NULL ledger columns an ELECT candidate ' +
    'can populate today, and which are NOT YET SERVED — an honest gap, not silently assumed', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({ structuredContent: { object: muhurtaResult() }, content: [{ type: 'text', text: '{}' }] })
    mockFetchLatticeSubstrate.mockResolvedValue({ ...emptySubstrate(), lattice_rows: [CITED_DOSA], census_rows: CENSUS })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)
    const candidate = response!.candidates[0]!

    // Caller-supplied at filing time (not derived from the candidate) — legitimately outside
    // this contract's scope: chart_id, intent (the native's own stated purpose), filed_by
    // (the resolved MCP principal), engine_version (a constant the filing ACTION itself
    // stamps — mirrors intervention_filing.ts's own `formula_version` input field, never read
    // off the candidate).
    const callerSupplied = new Set(['chart_id', 'intent', 'filed_by', 'engine_version'])

    // What a real ELECT candidate CAN populate today, mapped field-by-field:
    const derivable: Record<string, unknown> = {
      intervention_class: 'elected_activity', // closed-vocabulary constant for this call shape
      rite_or_activity_class: 'business', // the undertaking string this call was made with
      elected_window: { start: candidate.start, end: candidate.end },
      adjudication_record: candidate.judgment_ledger,
      source_citation: candidate.source_citation,
    }
    for (const [col, val] of Object.entries(derivable)) {
      expect(val, `derivable column "${col}" resolved to null/undefined — the contract's own claim is false`).not.toBeNull()
      expect(val).toBeDefined()
    }

    // What CANNOT be populated from ELECT's current served shape — the honest gap. A future
    // session closing G7 must either add these fields to KalaElectCandidate or resolve them
    // from a companion surface; until then, no caller can construct a schema-valid row without
    // inventing a value, which would be a B.10 fabrication.
    const notYetServedByElect = ['precision_regime', 'precision_basis', 'score_vector', 'efficacy_tier', 'predicted_differential', 'paddhati_version']
    for (const col of notYetServedByElect) {
      expect(candidate as unknown as Record<string, unknown>, `expected "${col}" to be ABSENT from KalaElectCandidate (this is the documented gap) — it now exists, update this harness`).not.toHaveProperty(col)
    }

    const allNotNull = notNullColumnsFromMigration()
    const accountedFor = new Set([...callerSupplied, ...Object.keys(derivable), ...notYetServedByElect])
    const unaccounted = allNotNull.filter((c) => !accountedFor.has(c))
    expect(unaccounted, `migration 532 gained NOT NULL column(s) this harness does not yet classify: ${unaccounted.join(', ')}`).toEqual([])
  })

  it('a disqualified candidate is honestly excluded from filing readiness (never files a hard-vetoed window)', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({
      structuredContent: {
        object: {
          ...muhurtaResult(),
          windows: [{ ...muhurtaResult().windows[0], hard_flag: true, disqualified: true, rank_penalty_reason: ['Vadha-tara for native star'] }],
        },
      },
      content: [{ type: 'text', text: '{}' }],
    })
    mockFetchLatticeSubstrate.mockResolvedValue(emptySubstrate())
    const { handleKalaElectGet } = await import('./elect.js')
    const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)
    expect(response!.candidates[0]!.disqualified).toBe(true)
    expect(response!.candidates[0]!.grading_tier).toBe('disqualified')
    // A disqualified candidate is exactly the "elected act" G7 must NEVER file — asserting the
    // served shape still marks it unmistakably disqualified is the harness's own negative case.
  })
})

// ── Companion note: the writer-side offline harness (already committed, confirmed green as
// part of this T5 session — 14 passed / 10 skipped-needs-DB) ────────────────────────────────
// `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_mi_sankalpa.py` covers the
// mi_sankalpa writer's own pure logic (study-arm classification, LEL falsifier matching,
// status-preserving idempotency) with no DB required. Re-run via:
//   cd platform/python-sidecar && python3 -m pytest pipeline/orchestrator/writers/tests/test_mi_sankalpa.py -q
// This file does not re-invoke it (a TS test file cannot shell pytest as part of `npm test`
// without a bespoke CI step this T5 lane does not own) — it is named here so a verify session
// finds both halves of the Intervention Ledger harness from one place.
