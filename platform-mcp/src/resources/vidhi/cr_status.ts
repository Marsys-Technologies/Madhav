/**
 * CR register status allowlist — D-2 Lane V-1; re-derived from the live registers in W4
 * Lane CR-55 (2026-07-21). This is the verifier/Binder reconciliation the original V-1
 * header asked a later pass to perform.
 *
 * Source of truth: BRIEF_D2.md §B0.1 ("known_gap reconciliation", 2026-07-16) was the
 * bind-time snapshot. It has been RE-DERIVED at W4 merge time against the current live
 * registers:
 *   - POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md v1.5 §G (row-level CR status column), and
 *   - MARSYS_DEFECT_GAP_REGISTER_v2_0.md v3.7 (authoritative exhaustive register).
 * The 2026-07-16 brief snapshot had gone STALE in two places since D-2/D-3 closed CRs after
 * it froze (CR-54, CR-59 — corrected below), and carries two brief-scoped instance closes
 * that the register-body still lists OPEN (CR-51, CR-72 — annotated inline). All actively
 * cited known_gaps in registry_data.ts were spot-checked OPEN against the register.
 *
 * CR-55 — RESOLVED: CLOSED-WITH-RESIDUAL (W4 CR-55 lane, verified live 2026-07-21).
 *   Subject: `vw_chart_digest.weakest_graha` reported the wrong graha ("Mercury") at the top
 *   of every orientation surface. Root cause: the view/writer (bo_samvada.py →
 *   bodha_rm_resonances.weakest_rank_in_chart) ranks by resonance_score_v1 — an RM ranking,
 *   NOT a strength measure.
 *   FIX (D-1.6 S-7, serving-side): query_ucd.ts::deriveShadbalaWeakestGraha re-derives the
 *   honest answer LIVE from L1 graha_shadbala_total (MIN → weakest) with a
 *   `weakest_graha_source` provenance disclosure, feeding bodha_chart_digest_get /
 *   get_chart_orientation / synergy-ucd. judgment_query serves no weakest_graha field.
 *   VERIFIED LIVE (postgres, chart 482012f1): shadbala MIN = Venus (0.8436) → served
 *   correctly; the raw `vw_chart_digest.weakest_graha` STILL returns "Mercury" (RESIDUAL:
 *   writer/view unfixed, only the serving layer overrides). This matches MARSYS register
 *   D-5 note ("CR-55 appears already fixed live") + BRIEF_D2 §B0.1 (CLOSED), and SUPERSEDES
 *   POST_REMEDIATION v1.5 §G row CR-55 "OPEN — ELEVATED" (that row predates the D-1.6 S-7
 *   serving fix). CR-55 is therefore correctly in CLOSED_CRS.
 *   RESIDUAL follow-up for the conductor (NOT a known_gap here): the writer/view still emits
 *   the mislabeled value; any NEW consumer reading vw_chart_digest.weakest_graha directly
 *   (bypassing query_ucd) would still get "Mercury". The writer-level fix + the S-1
 *   vargottama-join surface defect remain separately OPEN in the register.
 */

/** CRs the brief re-verified OPEN at register HEAD 2026-07-16 (BRIEF_D2.md §B0.1). */
export const OPEN_CRS = [
  'CR-9',
  'CR-14',
  'CR-39',
  'CR-15',
  'CR-16',
  'CR-24',
  'CR-25',
  'CR-26',
  'CR-64',
  'CR-28',
  'CR-30',
  'CR-36',
  'CR-44',
  'CR-61',
  'CR-62',
  'CR-73',
  'CR-76',
  'CR-77',
  'CR-78',
  'CR-84',
  'CR-85',
  'CR-86',
  'CR-90',
  // Not explicitly re-verified by BRIEF_D2.md §B0.1 (only CRs the brief's §F1 lane text
  // cites were reconciled there) but confirmed OPEN by direct inspection of
  // POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md v1.5 §G row text; re-verified OPEN at W4
  // (2026-07-21). NOTE: CR-54 and CR-59 were in this list at bind time but the register has
  // since CLOSED both (D-2 GATE GREEN 2026-07-17) — moved to CLOSED_CRS below (W4 CR-55 lane).
  // NOTE: CR-56 was ALSO in this list until VIDHI-PŪRṆATĀ (2026-07-23) reconciled it — the
  // house-lord dhana/raja yoga family DOES fire live via ganita_yoga_firings_get (F9); moved to
  // CLOSED_CRS below (same stale-register-drift precedent as CR-54/CR-59).
  'CR-63',
  'CR-65',
  'CR-66',
  'CR-67',
  'CR-68',
  'CR-69',
  'CR-37',
  // CR-130 — NEW, minted by VIDHI-PŪRṆATĀ P-2 (2026-07-23; next free slot after CR-129, the
  // highest in MARSYS_DEFECT_GAP_REGISTER_v2_0.md at wave open). DATA GAP: the Jaimini
  // spiritual / renunciate yoga family (pravrajyā, sannyāsa, tāpasa yogas) is NOT surfaced as a
  // family key by `ganita_yoga_firings_get` (P-0 F-probe: all firing rows carry `family_ids:[]`;
  // no 'spiritual' family). The `spiritual_yoga_scan` primitive (spirituality_deepdive floor)
  // asks for it AND flags it dark — planner-honest per brief §0's honesty line, never faked.
  // FOLLOW-UP (conductor / P-4): file the formal CR-130 row in MARSYS_DEFECT_GAP_REGISTER — that
  // register is outside this lane's may_touch, so it is flagged here rather than edited.
  'CR-130',
  // CR-131 — NEW, minted by VIDHI-PŪRṆATĀ P-3b (E-1, 2026-07-23; next free slot after CR-130).
  // DATA-REACHABILITY GAP: the D-5 Gochara-Chitra window engine (kala_gochara_windows, served by
  // gochara_activation_get / gochara_forecast_get / gochara_election_avoidance_get) is REGISTERED
  // and LIVE with a correct DR-16 honest-clarity envelope, but its rows are NOT reachable through
  // the standard MCP capability path — every probe (P-0 and the P-3b re-probe of chart 482012f1,
  // 2026-07-23) returns `backing_data_reachable:false, empty_reason:"DATABASE_URL not set — require
  // direct DB access"`. The three E-1 primitives (gochara_activation_read / gochara_forecast_read /
  // election_read) ask for the temporal engine in every deepdive's machine band AND flag it dark —
  // brief §0 honesty line: added, never faked, surfaced in the completeness receipt's `dark` bucket
  // until DB-direct reachability is confirmed in a DATABASE_URL-equipped serving runtime. This is a
  // reachability/verification gap, NOT a claim the tools are absent.
  // FOLLOW-UP (conductor / P-4): file the formal CR-131 row in MARSYS_DEFECT_GAP_REGISTER (that
  // register is outside this lane's may_touch); when DB reachability is confirmed live, retire the
  // three primitives' known_gap to null (the CR-56/CR-59 stale-correction precedent).
  'CR-131',
] as const;

/** LOGGED = inputs, not defects (BRIEF_D2.md §B0.1). Citable as known_gap context, never as a "fix this" CR. */
export const LOGGED_CRS = ['CR-27', 'CR-38', 'CR-71', 'CR-80'] as const;

/**
 * CRs CLOSED per BRIEF_D2.md §B0.1 + the live registers (re-derived W4, 2026-07-21) — a
 * known_gap MUST NEVER cite these. The registry completeness test below enforces "never CLOSED".
 */
export const CLOSED_CRS = [
  'CR-7',
  // CR-51: brief-scoped close. BRIEF_D2 §B0.1 closes the calibration-alias INSTANCE
  // (query_calibration↔mimamsa_calibration_get unification, D-1.6 S-1 — see mimamsa_outcome.ts).
  // POST_REMEDIATION v1.5 §G still lists the general CR-51 row OPEN; no primitive cites it as a
  // known_gap, so keeping it non-citable here is safe. Flagged for the conductor.
  'CR-51',
  // CR-55: RESOLVED CLOSED-WITH-RESIDUAL — verified live 2026-07-21 (served weakest_graha=Venus
  // via shadbala re-derivation; raw view still emits "Mercury"). See header block for full record.
  'CR-55',
  'CR-57',
  'CR-58',
  'CR-60',
  // CR-72: brief-scoped close (the shared-stub half, D-1.6 S-2). POST_REMEDIATION v1.5 §G still
  // lists CR-72 "OPEN — ELEVATED"; the OPEN continuation is CR-73 (bespoke detection +
  // cancellation), which IS in OPEN_CRS above. Keeping CR-72 non-citable here matches the brief.
  'CR-72',
  // CR-54: STALE-corrected. Was in OPEN_CRS at bind time; register now CLOSED (D-2 GATE GREEN
  // 2026-07-17, DR-9/DIS.022 — functional-lordship valence live). registry_data.ts already set
  // its known_gap to null. Residual granular-surface asymmetry carried to D-3, not a route gap.
  'CR-54',
  // CR-59: STALE-corrected. Was in OPEN_CRS at bind time; register now "detection CLOSED"
  // (D-2, 2026-07-17 — NBRY per-varga detection live since D-1.6 S-3, grounds-carried).
  // registry_data.ts already set its known_gap to null. RESIDUAL: L2 salience ranking of NBRY
  // signals routed to D-3 (a narrower surfacing issue, not the original detection defect).
  'CR-59',
  // CR-56: STALE-corrected (VIDHI-PŪRṆATĀ, 2026-07-23). Was in OPEN_CRS at bind time, tagged the
  // dhana_yoga_scan known_gap ("house-lord yoga detector family absent"). RECONCILED on live data:
  // ganita_yoga_firings_get fires dhana_yoga_house_lords (F9 — confirmed by P-0's probe AND the
  // yoga_firings_read primitive, which marks the same tool known_gap:null). The house-lord dhana/
  // raja family is confirmed firing live; the tag was stale register drift. registry_data.ts has
  // set dhana_yoga_scan's known_gap to null. Same precedent as CR-54/CR-59.
  'CR-56',
  'A7',
  'R-17',
  'R-47',
  'D15b-F2',
  'D15b-F3',
] as const;

export type CrId = (typeof OPEN_CRS)[number] | (typeof LOGGED_CRS)[number];

const CITABLE = new Set<string>([...OPEN_CRS, ...LOGGED_CRS]);
const CLOSED = new Set<string>(CLOSED_CRS);

/** True iff `crId` (e.g. "CR-56") is safe to cite as a primitive's `known_gap`. */
export function isCitableKnownGap(crId: string): boolean {
  return CITABLE.has(crId) && !CLOSED.has(crId);
}

/** True iff `crId` is a CLOSED CR that must never be cited as a known_gap. */
export function isClosedCr(crId: string): boolean {
  return CLOSED.has(crId);
}
