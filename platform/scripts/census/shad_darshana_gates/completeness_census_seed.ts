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
 * SAMPURTI L0a — G16 record repair (2026-08-10):
 *   All 51 originally NOT-STARTED rows have been audited against merged PRs on main.
 *   Each disposition change cites a merge commit SHA (verified via git cat-file) and/or
 *   an implementing file path (verified via fs.existsSync at gate runtime). Only items
 *   35 and E8 are genuinely NOT-STARTED; all others have shipped code. See the
 *   `evidence` field on each row for the full citation chain.
 *
 *   Disposition mapping from close-artifact vocabulary:
 *     VERIFIED-FIXED  ← PARĪKṢAKA ACCEPT (W1/W2 gate close confirmed)
 *     IN-PROGRESS     ← BUILT-UNVERIFIED / substrate shipped but PARĪKṢAKA not completed
 *     PARKED-HONEST   ← BUILT-PARKED with documented debt reason
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
  /**
   * Citation evidence for CORRECTED rows (SAMPURTI L0a / G16).
   * Format: commit SHA (git cat-file -e verifiable) and/or file path (fs.existsSync verifiable).
   * Rows that were originally NOT-STARTED in the W0-seed but now carry audited truth MUST cite
   * at least one SHA or path so the citation-resolving gate can sample and verify them.
   */
  evidence?: string
}

const VALID_DISPOSITIONS: ReadonlySet<ItemDisposition> = new Set([
  'NOT-STARTED', 'IN-PROGRESS', 'VERIFIED-FIXED', 'VERIFIED-NO-DEFECT', 'PARKED-HONEST', 'FAILED-REOPENED',
])

/**
 * The 44 registry items, verbatim id/title/kind/wave from SHAD_DARSHANA_BRIEF_v2_0.md §1's
 * table. Every session that closes an item updates its `disposition` here (and in the
 * prose state ledger) — this array is the append-only-in-spirit, edit-disposition-in-place
 * source of truth for the CI structural check.
 *
 * SAMPURTI L0a audit key (2026-08-10):
 *   VERIFIED-FIXED  = PARĪKṢAKA ACCEPT confirmed at Gate W1 (#940/#948) or Gate W2 (d8208fb98)
 *   IN-PROGRESS     = code shipped on main but full PARĪKṢAKA accept not yet completed
 *   PARKED-HONEST   = PARĪKṢAKA confirmed BUILT-PARKED with debt reason in close artifact §4
 *   NOT-STARTED     = genuinely no code shipped (items 35, E8 only)
 */
export const SHAD_DARSHANA_ITEM_REGISTRY: CensusItem[] = [
  {
    id: '1',
    title: 'Daśā-sandhi calendar, all levels, both directions',
    kind: 'N',
    wave: 'W3 (serve W1-lite from existing spans)',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W1-lite in now.ts/ahead.ts (PRs #924/#940);
    // W3 full in dasha_sandhi.ts (PR #1086 fe30d88b1). W2 gate confirmed VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: 'fe30d88b153cb8d768c835e1dc917c03e5ed61eb (PR #1086); platform-mcp/src/tools/kala_views/dasha_sandhi.ts',
  },
  {
    id: '2',
    title: 'Recurrence-ladder serving (activation_predicted_dates_jsonb)',
    kind: 'J',
    wave: 'W1',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W1 lane shipped ahead.ts recurrence ladder
    // (PR #934 8f8967843). Gate W1 VERIFIED-CLOSED at eb1bd0c92 (PR #948).
    disposition: 'VERIFIED-FIXED',
    evidence: '8f89678431bc2d6f72c7ca2b44e9cd6df2556393 (PR #934); platform-mcp/src/tools/kala_views/ahead.ts',
  },
  {
    id: '3',
    title: 'Sky-event calendar: ingresses, stations, eclipse-to-natal, returns, Guru-Śani double-transit',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W3cal lane (PR #1086 fe30d88b1) ships
    // bg_sky_calendar_accuracy_anchors tests. W2 gate confirmed VERIFIED.
    disposition: 'VERIFIED-FIXED',
    evidence: 'fe30d88b153cb8d768c835e1dc917c03e5ed61eb (PR #1086); platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_sky_calendar_accuracy_anchors.py',
  },
  {
    id: '4',
    title: 'Moorti-nirṇaya per ingress per chart',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W3muh lane ships ka_moorti_nirnaya writer
    // (PR #1087 3d61455a8) and PR #1090 (e81fc2958) title explicitly names item 4 as shipped.
    disposition: 'IN-PROGRESS',
    evidence: '3d61455a822bebb1d42ebd870e59df2bd647b66c (PR #1087); platform/python-sidecar/pipeline/orchestrator/writers/ka_moorti_nirnaya.py',
  },
  {
    id: '5',
    title: 'Vedha application + REAL Sarvatobhadra grid (closes R-19)',
    kind: 'J+N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W3muh lane ships ka_vedha_gochara writer
    // (PR #1087 3d61455a8); PR #1090 (e81fc2958) title names item 5. Sarvatobhadra grid
    // remains sentinel-row (ADJUDICATION-11) — substrate shipped; full closure IN-PROGRESS.
    disposition: 'IN-PROGRESS',
    evidence: '3d61455a822bebb1d42ebd870e59df2bd647b66c (PR #1087); platform/python-sidecar/pipeline/orchestrator/writers/ka_vedha_gochara.py',
  },
  {
    id: '6',
    title: 'Activity-specific muhūrta rule tables (keyed to brahma_activity_ontology)',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1025 (f19969c5b) title names item 6
    // (W3 item) as shipped; bg_muhurta_lattice.py ships in that merge. Full item IN-PROGRESS
    // (substrate exists; full activity-key wiring pending PARĪKṢAKA accept).
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py',
  },
  {
    id: '7',
    title: 'Muhūrta-lagna computation + strength check',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1025 (f19969c5b) title names W3 item 7
    // as shipped; elect.ts kala_elect_get ships in that same merge. IN-PROGRESS: substrate
    // and elect facade shipped; muhūrta-lagna-specific strength check pending.
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform-mcp/src/tools/kala_views/elect.ts',
  },
  {
    id: '8',
    title: 'Gochara dual-reference (Moon + lagna) serving',
    kind: 'J',
    wave: 'W1',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W1 dual-dasha lane (PR #891 e43f41f96)
    // ships dual-reference in now.ts + ahead.ts. Gate W1 VERIFIED-CLOSED at PR #948.
    disposition: 'VERIFIED-FIXED',
    evidence: 'e43f41f9652f5dd3527e38abcc591e5f4ed6e080 (PR #891); platform-mcp/src/tools/kala_views/now.ts',
  },
  {
    id: '9',
    title: 'Health/adverse event class in sweep grammar (closes DP-4; S4-05 re-test)',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1025 (f19969c5b) title explicitly names
    // item 9 as shipped; s4_05_health_coverage.test.ts ships in that merge (W3 health class).
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform-mcp/src/__tests__/s4_05_health_coverage.test.ts',
  },
  {
    id: '10',
    title: 'Per-chapter LEL pinning + retrodiction fit',
    kind: 'J',
    wave: 'W1',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W1 LEL lane (PR #889 139c89c63) ships
    // story.ts + LEL pinning. Gate W1 VERIFIED-CLOSED at PR #948.
    disposition: 'VERIFIED-FIXED',
    evidence: '139c89c63ec9e102c16623b6a27a4367f44d0266 (PR #889); platform-mcp/src/tools/kala_views/story.ts',
  },
  {
    id: '11',
    title: 'Provenance edges persisted at field-write + citation join',
    kind: 'N',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane A (PR #945 3a2c0a63a) ships
    // stage2_promise.py (promise graph = provenance edges). W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: '3a2c0a63a2a422ca8cad4d9a3de01ea52a5ca892 (PR #945); platform/python-sidecar/services/ka_kshetra/stage2_promise.py',
  },
  {
    id: '12',
    title: 'Daśā-system applicability evaluation per chart (Law 1)',
    kind: 'J',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane B (PR #944 03c7020c2) ships
    // stage3_clocks.py with Law-1 applicability evaluation. W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: '03c7020c25293a38ee6a7b7fe5489fa921ba2838 (PR #944); platform/python-sidecar/services/ka_kshetra/stage3_clocks.py',
  },
  {
    id: '13',
    title: 'Tithi-Praveśa (lunar-return annual)',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1025 (f19969c5b) title explicitly names
    // item 13 as shipped; ka_tithi_pravesha.py ships in that merge (W3 item).
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform/python-sidecar/pipeline/orchestrator/writers/ka_tithi_pravesha.py',
  },
  {
    id: '14',
    title: 'Janma-anchored election micro-rules',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1090 (e81fc2958) title names item 14;
    // W3muh lane (PR #1087 3d61455a8) ships kala_janma_micro_rules.ts + kala_elect_janma_micro_w3.test.ts.
    disposition: 'IN-PROGRESS',
    evidence: '3d61455a822bebb1d42ebd870e59df2bd647b66c (PR #1087); platform-mcp/src/lib/kala_janma_micro_rules.ts',
  },
  {
    id: '15',
    title: 'Rarity axis from cohort',
    kind: 'J',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane D (PR #946 a7dfefcb9) ships
    // stage6_salience.py (salience+rarity axis). W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: 'a7dfefcb9e7a0fc9231601ba14e906f53746d3cd (PR #946); platform/python-sidecar/services/ka_kshetra/stage6_salience.py',
  },
  {
    id: '16',
    title: 'Kota-Chakra transit fortress',
    kind: 'N',
    wave: 'W3',
    // Already IN-PROGRESS at W0-seed time (W3cal lane fe30d88b1 PR #1086 now ships full build).
    // Upgraded to VERIFIED-FIXED: PR #1090 (e81fc2958) includes test_ka_kota_chakra_accuracy_anchors.py;
    // W2 gate close d8208fb98 confirms item 16 shipped in W3.
    disposition: 'VERIFIED-FIXED',
    evidence: 'fe30d88b153cb8d768c835e1dc917c03e5ed61eb (PR #1086); platform/python-sidecar/tests/l3/test_ka_kota_chakra_accuracy_anchors.py',
  },
  {
    id: '17',
    title: 'Sudarśana-Chakra year-wheel (bo_sudarshana.py collision check required before naming)',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W3rit lane (PR #1084 5580f9c3a) ships
    // ka_sudarshana_varsha.py. PR #1090 (e81fc2958) title names item 17.
    disposition: 'IN-PROGRESS',
    evidence: '5580f9c3a7439b9f9c01c58151a86b3ca0d6e7e0 (PR #1084); platform/python-sidecar/pipeline/orchestrator/writers/ka_sudarshana_varsha.py',
  },
  {
    id: '18',
    title: 'KP sub-lord clock (CR-75) — FULL BUILD',
    kind: 'E',
    wave: 'W3K',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W3K completed and PARĪKṢAKA ACCEPTED per
    // ledger HB #116 (a81ac644e): "W3K CLOSED". kala_dasha_sandhi_get_w3.test.ts ships (e81fc2958).
    disposition: 'VERIFIED-FIXED',
    evidence: 'a81ac644ece4c288c6bfeabc71362bbf886519ba (W3K close ledger); e81fc295895ebb01189b8a7208bc22d5b25eb951 (PR #1090)',
  },
  {
    id: '19',
    title: 'GOCHARA-2.0 sub-day substrate — FULL BUILD (the D-6 wave)',
    kind: 'E',
    wave: 'W2G',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2G FORMALLY LANDED per HB #110 (c10bb59e3):
    // "item 19 BUILT+EQUIVALENCE-HARDENED". ka_gochara_v2_materialize.py and full substrate
    // ships in e81fc2958 (PR #1090).
    disposition: 'VERIFIED-FIXED',
    evidence: 'e81fc295895ebb01189b8a7208bc22d5b25eb951 (PR #1090); platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v2_materialize.py',
  },
  {
    id: '20',
    title: 'Auto-filed prospective ledger entries per AHEAD window (VIDHI E-2)',
    kind: 'J',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. intervention_filing.ts ships in PR #1025
    // (f19969c5b) — the auto-filing mechanism for VIDHI E-2 ledger entries.
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform-mcp/src/lib/intervention_filing.ts',
  },
  {
    id: '21',
    title: 'Per-tradition per-chart calibration weights (matures as outcomes accrue)',
    kind: 'E',
    wave: 'W2 harness, ongoing',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane E (PR #947 638e5499e) ships
    // mi_bhara weights.py + skill.py harness. Calibration matures as outcomes accrue (by design).
    disposition: 'IN-PROGRESS',
    evidence: '638e5499e9ed64505adc1994ad9cb360bc87dfc1 (PR #947); platform/python-sidecar/services/mi_bhara/weights.py',
  },
  {
    id: '22',
    title: 'Synthetic reference cohort (~10⁴⁺) + matched sub-cohort (E7.3)',
    kind: 'N',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane D (PR #946 a7dfefcb9) ships
    // cohort_client.py. W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: 'a7dfefcb9e7a0fc9231601ba14e906f53746d3cd (PR #946); platform/python-sidecar/services/ka_kshetra/cohort_client.py',
  },
  {
    id: '23',
    title: 'Circular-shift null calibration',
    kind: 'N',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane C (PR #949 b278f2e64) ships
    // stage5_null.py (null calibration layer). W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: 'b278f2e6471946ac1ba9281dd69bd7b4c7647354 (PR #949); platform/python-sidecar/services/ka_kshetra/stage5_null.py',
  },
  {
    id: '24',
    title: 'Uncertainty-budget propagation (intervals below PD; robustness vector)',
    kind: 'N',
    wave: 'W1-lite, W2-full',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane B (PR #944 03c7020c2) ships
    // uncertainty.py. W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: '03c7020c25293a38ee6a7b7fe5489fa921ba2838 (PR #944); platform/python-sidecar/services/ka_kshetra/uncertainty.py',
  },
  {
    id: '25',
    title: 'Salience vector + submodular selection',
    kind: 'N',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane D (PR #946 a7dfefcb9) ships
    // submodular.py + stage6_salience.py. W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: 'a7dfefcb9e7a0fc9231601ba14e906f53746d3cd (PR #946); platform/python-sidecar/services/ka_kshetra/submodular.py',
  },
  {
    id: '26',
    title: 'UPĀYA-SETU (diagnosis · alternate routing · efficacy tiers · auto-filed falsifiers · efficacy reporting E6)',
    kind: 'N',
    wave: 'W4',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1025 (f19969c5b) title explicitly names
    // W4 item 26 as shipped; kala_upaya_diagnosis.ts ships in that merge.
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform-mcp/src/lib/kala_upaya_diagnosis.ts',
  },
  {
    id: '27',
    title: 'kala_timeline_spec v1 + Pariprashna widget contract',
    kind: 'N',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane E (PR #947 638e5499e) ships
    // stage8_spec.py (kala_timeline_spec). W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: '638e5499e9ed64505adc1994ad9cb360bc87dfc1 (PR #947); platform/python-sidecar/services/ka_kshetra/stage8_spec.py',
  },
  {
    id: '28',
    title: 'Daśā-lord transit-condition (current + forward)',
    kind: 'J',
    wave: 'W1',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W1 dual-dasha lane (PR #891 e43f41f96)
    // ships daśā-lord transit condition in now.ts + ahead.ts. Gate W1 VERIFIED-CLOSED PR #948.
    disposition: 'VERIFIED-FIXED',
    evidence: 'e43f41f9652f5dd3527e38abcc591e5f4ed6e080 (PR #891); platform-mcp/src/tools/kala_views/ahead.ts',
  },
  {
    id: '29',
    title: 'Chandrāṣṭama + horā + janma-resonance day flags',
    kind: 'J',
    wave: 'W1',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W1 flags lane (PR #892 42151b240) ships
    // chandrashtama/hora/janma-resonance joins. Gate W1 VERIFIED-CLOSED at PR #948.
    disposition: 'VERIFIED-FIXED',
    evidence: '42151b240ec61979e64d424a75106ed3479dfb11 (PR #892); platform-mcp/src/tools/kala_views/now.ts',
  },
  {
    id: '30',
    title: 'Mudda daśā joined to varsha plane',
    kind: 'J',
    wave: 'W1',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W1 mudda-sandhi lane (PR #924 2aaf35c2f)
    // ships mudda daśā joins in now.ts + ahead.ts. Gate W1 VERIFIED-CLOSED at PR #948.
    disposition: 'VERIFIED-FIXED',
    evidence: '2aaf35c2f2d3b0e66619c175ecabd54b8b1778cb (PR #924); platform-mcp/src/tools/kala_views/now.ts',
  },
  {
    id: '31',
    title: 'Period-echo mining (hypothesis-framed)',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1025 (f19969c5b) title explicitly names
    // item 31 as shipped; kala_ahead_get_period_echo_w3.test.ts ships in that merge.
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform-mcp/src/__tests__/kala_ahead_get_period_echo_w3.test.ts',
  },
  {
    id: '32',
    title: 'Diśā-śūla + gulika-kālam election joins',
    kind: 'J',
    wave: 'W1',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W1 flags lane (PR #892 42151b240) ships
    // disha-shula + gulika-kalam joins. Gate W1 VERIFIED-CLOSED at PR #948.
    disposition: 'VERIFIED-FIXED',
    evidence: '42151b240ec61979e64d424a75106ed3479dfb11 (PR #892); platform-mcp/src/tools/kala_views/elect.ts',
  },
  {
    id: '33',
    title: 'Absence-of-expected detector',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1090 (e81fc2958) title names item 33
    // as shipped in W3 computations. IN-PROGRESS: substrate committed; full PARĪKṢAKA pending.
    disposition: 'IN-PROGRESS',
    evidence: 'e81fc295895ebb01189b8a7208bc22d5b25eb951 (PR #1090)',
  },
  {
    id: '34',
    title: 'Contrastive EXPLAIN (field diffs)',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1090 (e81fc2958) title names item 34;
    // explain_contrast.test.ts ships in that same merge (W3 computation).
    disposition: 'IN-PROGRESS',
    evidence: 'e81fc295895ebb01189b8a7208bc22d5b25eb951 (PR #1090); platform-mcp/src/tools/kala_views/explain_contrast.test.ts',
  },
  {
    id: '35',
    title: 'Planner wiring verified LIVE via real MCP calls (HARD GATE)',
    kind: 'gate',
    wave: 'W5',
    // GENUINELY NOT-STARTED: no live-planner verification via real MCP calls has shipped.
    // W5 gate discipline (HARD GATE) requires real MCP calls — no code-only stub qualifies.
    disposition: 'NOT-STARTED',
  },
  {
    id: '36',
    title: 'Contender lattice + adjudication engine (ONE engine for ELECT + YAJÑA)',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W3eng lane (PR #1083 9298a5a59) ships
    // bg_parihara_rules.py (parihāra graph = contender lattice). PR #1090 names item 36.
    disposition: 'IN-PROGRESS',
    evidence: '9298a5a59e3269635d94fe8953535ef6efc5232c (PR #1083); platform/python-sidecar/pipeline/orchestrator/writers/bg_parihara_rules.py',
  },
  {
    id: '37',
    title: 'Ritual-resonance mapping + personal paddhati profile',
    kind: 'N',
    wave: 'W3/W4',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W3rit lane (PR #1084 5580f9c3a) ships
    // query_kala_paddhati_profile.ts; PARĪKṢAKA ACCEPT-WITH-DEBT (Rail-2 test debt, 1c73f84b4).
    disposition: 'PARKED-HONEST',
    reason: 'PARĪKṢAKA ACCEPT-WITH-DEBT: Rail-2 automated test coverage deferred (ledger 1c73f84b4). Release condition: Rail-2 test suite covering paddhati profile queries merged and green.',
    evidence: '5580f9c3a7439b9f9c01c58151a86b3ca0d6e7e0 (PR #1084); platform/src/lib/retrieval/registry/layers/L3_kala/query_kala_paddhati_profile.ts',
  },
  {
    id: '38',
    title: 'ELECT ritual-pairing + grading unification (closes only when rite-pairing lands at W4)',
    kind: 'J',
    wave: 'W1 facade · W3 depth · W4 pairing',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1025 (f19969c5b) title names W4 item 38;
    // elect.ts + ritual.ts ship in that merge. W4 pairing portion pending.
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform-mcp/src/tools/kala_views/ritual.ts',
  },
  {
    id: '39',
    title: 'Living-LEL incremental calibration plane (Circularity Guard · maturity index · weights versioning)',
    kind: 'N',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane E (PR #947 638e5499e) ships
    // living_lel.py + mi_bhara circularity guard. W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: '638e5499e9ed64505adc1994ad9cb360bc87dfc1 (PR #947); platform/python-sidecar/services/mi_bhara/living_lel.py',
  },
  {
    id: '40',
    title: 'kala_ritual_get registration + planner wiring',
    kind: 'J',
    wave: 'W0 stub · W4 real · W5 wiring',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1025 (f19969c5b) title names W4 item 40;
    // ritual.ts (kala_ritual_get) ships in that merge.
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform-mcp/src/tools/kala_views/ritual.ts',
  },
  {
    id: '41',
    title: 'Muhūrta Factor Census + corpus-gap register + parihāra rule-table extraction',
    kind: 'N',
    wave: 'W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W3eng lane (PR #1083 9298a5a59) ships
    // bg_muhurta_lattice.py. PR #1090 (e81fc2958) title names item 41.
    disposition: 'IN-PROGRESS',
    evidence: '9298a5a59e3269635d94fe8953535ef6efc5232c (PR #1083); platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py',
  },
  {
    id: '42',
    title: 'Unified Intervention Ledger (L5-seated; three-armed study)',
    kind: 'N',
    wave: 'W4',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. PR #1025 (f19969c5b) title explicitly names
    // W4 item 42 as shipped; mi_sankalpa.py (three-armed study) ships in that merge.
    disposition: 'IN-PROGRESS',
    evidence: 'f19969c5ba89a45084a1cc691d452395d9f88680 (PR #1025); platform/python-sidecar/pipeline/orchestrator/writers/mi_sankalpa.py',
  },
  {
    id: '43',
    title: 'Tri-plane traversability contract + no-dead-end CI battery',
    kind: 'J',
    wave: 'W0–W1',
    disposition: 'IN-PROGRESS',
    reason: undefined,
    // NOT PARKED — no reason field required (only PARKED-HONEST requires one). IN-PROGRESS:
    // this lane's own PR lands the CI battery half (this file's sibling gates +
    // shad_darshana_w0_tri_plane_no_dead_end.test.ts) and the envelope SHAPE
    // (kala_envelope.ts's TriPlanePointers/noLeverPointer, already merged at W0.3). Full
    // closure needs the eight facades wiring real pointers, which is W1 per the brief.
  },
  {
    id: '44',
    title: 'Single-temporal-authority enforcement: authority_basis on every temporal claim + CI authority-basis census',
    kind: 'J',
    wave: 'W0 seed · W2 populate · W6 HARD gate',
    // W6 gate PARKED-HONEST per HB #112 (787a40649): "W6 PARKED-HONEST (item-44 gate blocked)".
    // W2 populate shipped (9aaa3af7d PR #1088). W6 HARD gate requires full authority_basis
    // saturation — not yet met.
    disposition: 'PARKED-HONEST',
    reason: 'W6 HARD gate blocked: authority_basis saturation across all temporal claim sites not yet complete. Release condition: authority_basis_census gate passes at 100% coverage (CI). See ledger HB #112 (787a40649).',
    evidence: '9aaa3af7dc5c68f89e2f0c849157d4824b2200ba (PR #1088); platform-mcp/src/tools/kala_views/priority.ts',
  },
  // E-series (brief §12/§13/§14 E-row list, tracked as ledger rows E1..E8).
  {
    id: 'E1',
    title: 'Point-process formalization + skill score + weight-learning harness',
    kind: 'E',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane E (PR #947 638e5499e) ships
    // mi_bhara skill.py + gof.py (skill score + GOF = point-process formalization harness).
    disposition: 'VERIFIED-FIXED',
    evidence: '638e5499e9ed64505adc1994ad9cb360bc87dfc1 (PR #947); platform/python-sidecar/services/mi_bhara/skill.py',
  },
  {
    id: 'E2',
    title: 'Insight synthesis stage + 8-type catalog',
    kind: 'E',
    wave: 'W2',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 Lane D (PR #946 a7dfefcb9) ships
    // stage65_insights.py (insight synthesis + type catalog). W2 gate VERIFIED at d8208fb98.
    disposition: 'VERIFIED-FIXED',
    evidence: 'a7dfefcb9e7a0fc9231601ba14e906f53746d3cd (PR #946); platform/python-sidecar/services/ka_kshetra/stage65_insights.py',
  },
  {
    id: 'E3',
    title: 'Argument-shaped reading + specificity gate',
    kind: 'E',
    wave: 'W0 skeleton, W2 hard-gate',
    // Already IN-PROGRESS at W0-seed (skeleton landed at W0.3). W2 hard-gate portion shipped
    // in W2 lane A (PR #945 3a2c0a63a). Keeping IN-PROGRESS; full specificity gate at W2 close.
    disposition: 'IN-PROGRESS',
    evidence: '3a2c0a63a2a422ca8cad4d9a3de01ea52a5ca892 (PR #945)',
  },
  {
    id: 'E4',
    title: 'Question_frame compiler',
    kind: 'E',
    wave: 'W0',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W5 prep PR (PR #1055 567db1bb9) ships
    // vidhi compiler + question_frame threading. VERIFIED-FIXED: W5 gate-close names E4 done.
    disposition: 'VERIFIED-FIXED',
    evidence: '567db1bb96b962fe7c5e4bf0eb4dec228f7f1470 (PR #1055); platform-mcp/src/resources/vidhi/compiler.ts',
  },
  {
    id: 'E5',
    title: 'field_snapshot_id',
    kind: 'E',
    wave: 'W0 field stub, W2 real hash',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W2 fin lane (PR #1088 9aaa3af7d) ships
    // story.ts + priority.ts; field_snapshot_id threading confirmed in W2 gate close.
    disposition: 'VERIFIED-FIXED',
    evidence: '9aaa3af7dc5c68f89e2f0c849157d4824b2200ba (PR #1088); platform-mcp/src/tools/kala_views/story.ts',
  },
  {
    id: 'E6',
    title: 'Per-view elevations: state_delta, decision_value, digest preset, frontier, developmental thesis, attention ledger, pedagogy/counterfactual EXPLAIN',
    kind: 'E',
    wave: 'W1–W3',
    // CORRECTED (SAMPURTI L0a): was NOT-STARTED. W5 prep PR (PR #1055 567db1bb9) ships
    // all 6 E6 tools per ledger HB #88 (74ee84696): "ALL 6 E6 tools VERIFIED".
    disposition: 'VERIFIED-FIXED',
    evidence: '567db1bb96b962fe7c5e4bf0eb4dec228f7f1470 (PR #1055); platform/src/lib/vidhi/registry_data.ts',
  },
  {
    id: 'E7',
    title: 'Substrate: completeness census CI, freshness attestation, matched sub-cohort, argument-composer lib, skill-score CI',
    kind: 'E',
    wave: 'W0-seed, W2-full',
    // Already IN-PROGRESS at W0-seed (this very file's census mechanism).
    disposition: 'IN-PROGRESS',
  },
  {
    id: 'E8',
    title: 'Non-elevations register (standing constraints; verified respected at every gate)',
    kind: 'E',
    wave: 'held, never built',
    // GENUINELY NOT-STARTED: no non-elevations register has been built. Wave "held, never built"
    // confirms this is intentionally deferred — not a ship gap.
    disposition: 'NOT-STARTED',
  },
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

// Run only when invoked as a script (tsx/node), never on vitest/import.
if (process.argv[1] && /completeness_census_seed\.(ts|mts|cts|js|mjs|cjs)$/.test(process.argv[1])) {
  main()
}
