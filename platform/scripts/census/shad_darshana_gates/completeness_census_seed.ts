#!/usr/bin/env tsx
/**
 * completeness_census_seed.ts — ṢAḌ-DARŚANA W0.6 CI skeleton, item 4
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.6.4 / §3 W0.6: "completeness census seed").
 *
 * "Seed of the ongoing census that will track registry items 1–44 + E1–E8 coverage"
 * (brief §0.6.4). This file is the machine-readable, CI-checkable counterpart to the
 * prose state ledger (`SHAD_DARSHANA_STATE.md`, brief §6) — a session updates the
 * `SHAD_DARSHANA_ITEM_REGISTRY` disposition below as items close, and this gate keeps the
 * registry itself honest at every commit:
 *
 *   1. Exactly 52 entries (44 registry items + 8 E-rows), unique ids, matching the brief
 *      §1 table and §12/§13/§14 E-row list verbatim (a drifted id here is a build error —
 *      registries must not disagree, CLAUDE.md §B.8).
 *   2. Every disposition is drawn from the CLOSED vocabulary the brief §6 ledger schema
 *      defines: `NOT-STARTED | IN-PROGRESS | VERIFIED-FIXED | VERIFIED-NO-DEFECT |
 *      PARKED-HONEST | FAILED-REOPENED`.
 *   3. `OUT-OF-SCOPE-BY-DESIGN` NEVER appears (brief §1: "RETIRED from the disposition
 *      vocabulary... no item may carry it" — a hard build error if found, not a warning).
 *   4. `PARKED-HONEST` entries carry a non-empty `reason` (brief §6: "PARKED-HONEST
 *      <reason, release condition>" — an unreasoned park is not honest).
 *
 * At W0 every item is seeded `NOT-STARTED` except the two already discharged by THIS
 * lane's own PR (item 43's tri-plane pointer SHAPE — not the full W1 wiring — and E7's
 * census mechanism existing at all) and by the W0.3 sibling lane already merged to main
 * (kala_envelope.ts + argument_composer.ts landing E3/E4/E5's skeleton shape). Real
 * per-item disposition tracking is the Conductor's job across the whole campaign (brief
 * §6: "Every session: first act read, last act update") — this seed's job is only to
 * exist, be structurally correct, and refuse to silently drift from the brief's item list.
 *
 * PLAN/LIVE split does not apply here (no MCP calls) — this is a pure static/self-check,
 * runnable anywhere, always. Exit 0 = registry structurally valid; exit 1 = FAIL.
 *
 * Run (from `platform/`):
 *   npx tsx scripts/census/shad_darshana_gates/completeness_census_seed.ts
 */
import { printGateReport, type GateResult } from './_report'

export type ItemDisposition = 'NOT-STARTED' | 'IN-PROGRESS' | 'VERIFIED-FIXED' | 'VERIFIED-NO-DEFECT' | 'PARKED-HONEST' | 'FAILED-REOPENED'

export type ItemKind = 'N' | 'J' | 'E' | 'gate'

export interface CensusItem {
  /** '1'..'44' for registry items, 'E1'..'E8' for E-rows. */
  id: string
  title: string
  kind: ItemKind
  wave: string
  disposition: ItemDisposition
  /** Required (non-empty) when disposition === 'PARKED-HONEST'. */
  reason?: string
}

const VALID_DISPOSITIONS: ReadonlySet<ItemDisposition> = new Set([
  'NOT-STARTED', 'IN-PROGRESS', 'VERIFIED-FIXED', 'VERIFIED-NO-DEFECT', 'PARKED-HONEST', 'FAILED-REOPENED',
])

/**
 * The 44 registry items, verbatim id/title/kind/wave from SHAD_DARSHANA_BRIEF_v2_0.md §1's
 * table. Every session that closes an item updates its `disposition` here (and in the
 * prose state ledger) — this array is the append-only-in-spirit, edit-disposition-in-place
 * source of truth for the CI structural check.
 */
export const SHAD_DARSHANA_ITEM_REGISTRY: CensusItem[] = [
  { id: '1', title: 'Daśā-sandhi calendar, all levels, both directions', kind: 'N', wave: 'W3 (serve W1-lite from existing spans)', disposition: 'NOT-STARTED' },
  { id: '2', title: 'Recurrence-ladder serving (activation_predicted_dates_jsonb)', kind: 'J', wave: 'W1', disposition: 'NOT-STARTED' },
  { id: '3', title: 'Sky-event calendar: ingresses, stations, eclipse-to-natal, returns, Guru-Śani double-transit', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '4', title: 'Moorti-nirṇaya per ingress per chart', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '5', title: 'Vedha application + REAL Sarvatobhadra grid (closes R-19)', kind: 'J+N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '6', title: 'Activity-specific muhūrta rule tables (keyed to brahma_activity_ontology)', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '7', title: 'Muhūrta-lagna computation + strength check', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '8', title: 'Gochara dual-reference (Moon + lagna) serving', kind: 'J', wave: 'W1', disposition: 'NOT-STARTED' },
  { id: '9', title: 'Health/adverse event class in sweep grammar (closes DP-4; S4-05 re-test)', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '10', title: 'Per-chapter LEL pinning + retrodiction fit', kind: 'J', wave: 'W1', disposition: 'NOT-STARTED' },
  { id: '11', title: 'Provenance edges persisted at field-write + citation join', kind: 'N', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: '12', title: 'Daśā-system applicability evaluation per chart (Law 1)', kind: 'J', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: '13', title: 'Tithi-Praveśa (lunar-return annual)', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '14', title: 'Janma-anchored election micro-rules', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '15', title: 'Rarity axis from cohort', kind: 'J', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: '16', title: 'Kota-Chakra transit fortress', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '17', title: 'Sudarśana-Chakra year-wheel (bo_sudarshana.py collision check required before naming)', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '18', title: 'KP sub-lord clock (CR-75) — FULL BUILD', kind: 'E', wave: 'W3K', disposition: 'NOT-STARTED' },
  { id: '19', title: 'GOCHARA-2.0 sub-day substrate — FULL BUILD (the D-6 wave)', kind: 'E', wave: 'W2G', disposition: 'NOT-STARTED' },
  { id: '20', title: 'Auto-filed prospective ledger entries per AHEAD window (VIDHI E-2)', kind: 'J', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: '21', title: 'Per-tradition per-chart calibration weights (matures as outcomes accrue)', kind: 'E', wave: 'W2 harness, ongoing', disposition: 'NOT-STARTED' },
  { id: '22', title: 'Synthetic reference cohort (~10⁴⁺) + matched sub-cohort (E7.3)', kind: 'N', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: '23', title: 'Circular-shift null calibration', kind: 'N', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: '24', title: 'Uncertainty-budget propagation (intervals below PD; robustness vector)', kind: 'N', wave: 'W1-lite, W2-full', disposition: 'NOT-STARTED' },
  { id: '25', title: 'Salience vector + submodular selection', kind: 'N', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: '26', title: 'UPĀYA-SETU (diagnosis · alternate routing · efficacy tiers · auto-filed falsifiers · efficacy reporting E6)', kind: 'N', wave: 'W4', disposition: 'NOT-STARTED' },
  { id: '27', title: 'kala_timeline_spec v1 + Pariprashna widget contract', kind: 'N', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: '28', title: 'Daśā-lord transit-condition (current + forward)', kind: 'J', wave: 'W1', disposition: 'NOT-STARTED' },
  { id: '29', title: 'Chandrāṣṭama + horā + janma-resonance day flags', kind: 'J', wave: 'W1', disposition: 'NOT-STARTED' },
  { id: '30', title: 'Mudda daśā joined to varsha plane', kind: 'J', wave: 'W1', disposition: 'NOT-STARTED' },
  { id: '31', title: 'Period-echo mining (hypothesis-framed)', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '32', title: 'Diśā-śūla + gulika-kālam election joins', kind: 'J', wave: 'W1', disposition: 'NOT-STARTED' },
  { id: '33', title: 'Absence-of-expected detector', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '34', title: 'Contrastive EXPLAIN (field diffs)', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '35', title: 'Planner wiring verified LIVE via real MCP calls (HARD GATE)', kind: 'gate', wave: 'W5', disposition: 'NOT-STARTED' },
  { id: '36', title: 'Contender lattice + adjudication engine (ONE engine for ELECT + YAJÑA)', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '37', title: 'Ritual-resonance mapping + personal paddhati profile', kind: 'N', wave: 'W3/W4', disposition: 'NOT-STARTED' },
  { id: '38', title: 'ELECT ritual-pairing + grading unification (closes only when rite-pairing lands at W4)', kind: 'J', wave: 'W1 facade · W3 depth · W4 pairing', disposition: 'NOT-STARTED' },
  { id: '39', title: 'Living-LEL incremental calibration plane (Circularity Guard · maturity index · weights versioning)', kind: 'N', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: '40', title: 'kala_ritual_get registration + planner wiring', kind: 'J', wave: 'W0 stub · W4 real · W5 wiring', disposition: 'NOT-STARTED' },
  { id: '41', title: 'Muhūrta Factor Census + corpus-gap register + parihāra rule-table extraction', kind: 'N', wave: 'W3', disposition: 'NOT-STARTED' },
  { id: '42', title: 'Unified Intervention Ledger (L5-seated; three-armed study)', kind: 'N', wave: 'W4', disposition: 'NOT-STARTED' },
  {
    id: '43', title: 'Tri-plane traversability contract + no-dead-end CI battery', kind: 'J', wave: 'W0–W1',
    disposition: 'IN-PROGRESS',
    reason: undefined,
    // NOT PARKED — no reason field required (only PARKED-HONEST requires one). IN-PROGRESS:
    // this lane's own PR lands the CI battery half (this file's sibling gates +
    // shad_darshana_w0_tri_plane_no_dead_end.test.ts) and the envelope SHAPE
    // (kala_envelope.ts's TriPlanePointers/noLeverPointer, already merged at W0.3). Full
    // closure needs the eight facades wiring real pointers, which is W1 per the brief.
  },
  { id: '44', title: 'Single-temporal-authority enforcement: authority_basis on every temporal claim + CI authority-basis census', kind: 'J', wave: 'W0 seed · W2 populate · W6 HARD gate', disposition: 'IN-PROGRESS' },
  // E-series (brief §12/§13/§14 E-row list, tracked as ledger rows E1..E8).
  { id: 'E1', title: 'Point-process formalization + skill score + weight-learning harness', kind: 'E', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: 'E2', title: 'Insight synthesis stage + 8-type catalog', kind: 'E', wave: 'W2', disposition: 'NOT-STARTED' },
  { id: 'E3', title: 'Argument-shaped reading + specificity gate', kind: 'E', wave: 'W0 skeleton, W2 hard-gate', disposition: 'IN-PROGRESS' },
  { id: 'E4', title: 'Question_frame compiler', kind: 'E', wave: 'W0', disposition: 'NOT-STARTED' },
  { id: 'E5', title: 'field_snapshot_id', kind: 'E', wave: 'W0 field stub, W2 real hash', disposition: 'NOT-STARTED' },
  { id: 'E6', title: 'Per-view elevations: state_delta, decision_value, digest preset, frontier, developmental thesis, attention ledger, pedagogy/counterfactual EXPLAIN', kind: 'E', wave: 'W1–W3', disposition: 'NOT-STARTED' },
  { id: 'E7', title: 'Substrate: completeness census CI, freshness attestation, matched sub-cohort, argument-composer lib, skill-score CI', kind: 'E', wave: 'W0-seed, W2-full', disposition: 'IN-PROGRESS' },
  { id: 'E8', title: 'Non-elevations register (standing constraints; verified respected at every gate)', kind: 'E', wave: 'held, never built', disposition: 'NOT-STARTED' },
]

const EXPECTED_COUNT = 44 + 8

function validate(): GateResult[] {
  const results: GateResult[] = []

  results.push({
    id: 'census-count',
    title: 'Registry has exactly 52 entries (44 items + 8 E-rows)',
    status: SHAD_DARSHANA_ITEM_REGISTRY.length === EXPECTED_COUNT ? 'PASS' : 'FAIL',
    detail: `count=${SHAD_DARSHANA_ITEM_REGISTRY.length}, expected=${EXPECTED_COUNT}`,
  })

  const seen = new Map<string, number>()
  for (const item of SHAD_DARSHANA_ITEM_REGISTRY) seen.set(item.id, (seen.get(item.id) ?? 0) + 1)
  const dupes = [...seen.entries()].filter(([, n]) => n > 1).map(([id]) => id)
  results.push({
    id: 'census-unique-ids',
    title: 'Every item id is unique',
    status: dupes.length === 0 ? 'PASS' : 'FAIL',
    detail: dupes.length === 0 ? 'unique' : `duplicate ids: ${dupes.join(', ')}`,
  })

  const expectedIds = [...Array.from({ length: 44 }, (_, i) => String(i + 1)), ...Array.from({ length: 8 }, (_, i) => `E${i + 1}`)]
  const missing = expectedIds.filter((id) => !seen.has(id))
  const unexpected = [...seen.keys()].filter((id) => !expectedIds.includes(id))
  results.push({
    id: 'census-id-set',
    title: 'Item ids match the brief §1/§12-§14 set exactly (1-44 + E1-E8)',
    status: missing.length === 0 && unexpected.length === 0 ? 'PASS' : 'FAIL',
    detail: `missing=${JSON.stringify(missing)}, unexpected=${JSON.stringify(unexpected)}`,
  })

  const retiredVocab = SHAD_DARSHANA_ITEM_REGISTRY.filter((item) => (item.disposition as string) === 'OUT-OF-SCOPE-BY-DESIGN')
  results.push({
    id: 'census-no-retired-vocab',
    title: 'No item carries the RETIRED "OUT-OF-SCOPE-BY-DESIGN" disposition (brief §1, native ruling 2026-07-29)',
    status: retiredVocab.length === 0 ? 'PASS' : 'FAIL',
    detail: retiredVocab.length === 0 ? 'clean' : `RETIRED vocabulary found on: ${retiredVocab.map((i) => i.id).join(', ')}`,
  })

  const invalidDisposition = SHAD_DARSHANA_ITEM_REGISTRY.filter((item) => !VALID_DISPOSITIONS.has(item.disposition))
  results.push({
    id: 'census-valid-dispositions',
    title: 'Every disposition is drawn from the closed vocabulary',
    status: invalidDisposition.length === 0 ? 'PASS' : 'FAIL',
    detail: invalidDisposition.length === 0 ? 'clean' : `invalid dispositions: ${invalidDisposition.map((i) => `${i.id}=${i.disposition}`).join(', ')}`,
  })

  const parkedWithoutReason = SHAD_DARSHANA_ITEM_REGISTRY.filter((item) => item.disposition === 'PARKED-HONEST' && !(item.reason && item.reason.trim().length > 0))
  results.push({
    id: 'census-parked-honest-has-reason',
    title: 'Every PARKED-HONEST item carries a non-empty reason',
    status: parkedWithoutReason.length === 0 ? 'PASS' : 'FAIL',
    detail: parkedWithoutReason.length === 0 ? 'clean' : `unreasoned parks: ${parkedWithoutReason.map((i) => i.id).join(', ')}`,
  })

  const notStarted = SHAD_DARSHANA_ITEM_REGISTRY.filter((i) => i.disposition === 'NOT-STARTED').length
  const inProgress = SHAD_DARSHANA_ITEM_REGISTRY.filter((i) => i.disposition === 'IN-PROGRESS').length
  const closed = SHAD_DARSHANA_ITEM_REGISTRY.filter((i) => i.disposition === 'VERIFIED-FIXED' || i.disposition === 'VERIFIED-NO-DEFECT').length
  results.push({
    id: 'census-scoreboard',
    title: 'Scoreboard (informational — not a pass/fail gate)',
    status: 'PASS',
    detail: `NOT-STARTED=${notStarted}, IN-PROGRESS=${inProgress}, CLOSED=${closed}, PARKED-HONEST=${SHAD_DARSHANA_ITEM_REGISTRY.filter((i) => i.disposition === 'PARKED-HONEST').length}, FAILED-REOPENED=${SHAD_DARSHANA_ITEM_REGISTRY.filter((i) => i.disposition === 'FAILED-REOPENED').length}`,
  })

  return results
}

function main(): void {
  process.exit(printGateReport('completeness_census_seed', validate()))
}

main()
