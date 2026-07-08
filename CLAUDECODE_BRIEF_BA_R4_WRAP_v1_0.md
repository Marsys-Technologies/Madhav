---
canonical_id: CLAUDECODE_BRIEF_BA_R4_WRAP
version: 1.1
status: COMPLETE (2026-07-08) — W1-W4 executed; native rebuilt on final config (image 98a570ac); FORENSIC 7/7 + all gates PASS; runway CLOSED
created: 2026-07-07
changelog:
  - v1.1 (2026-07-07): W3→W4 gate HARDENED — "proceed on silence" is REVOKED (it defaulted to
    authorizing an irreversible native write in a non-interactive session). W4 now requires an EXPLICIT
    native GO recorded in the ledger. Also registered the execution-environment reality: sessions may be
    read-only/non-interactive; deploy + build steps route through the runbook + the native's cockpit
    access where the session lacks write creds.
author: Cowork (Beyond-Acharya program) — native-requested consolidation of all pre-rebuild activities
program: BA_PHASE4_RUNWAY_PLAN_v1_0.md — this brief EXECUTES its remaining phases (R2.2 → JL-027 → R3 → R4)
  and closes the runway. Supersedes nothing; incorporates CLAUDECODE_BRIEF_BA_LEL_CHART_SCOPING v1.2 by
  reference for W1/W2 detail.
resume_state: CURRENT_STATE v6.26 · checkpoint #456 on main · WIP branch
  origin/ba-p4/r2-2-step1-lel-chart-scope-WIP (aa3a65e2, reviewed migration 423, not deployed) ·
  ledger: JL-009 CLOSED · JL-026 RESOLVED · JL-027 OPEN (graha_yuddha winner rule)
common_rules: FROZEN orchestrator contract §N.2 · two-chart rule (Abhinandan 1c826d5a proves EVERYTHING
  before native 482012f1) · canonical-or-floor · clear-safety on irreplaceable data (JL-010 class) ·
  single writer stream · each wave closes with ledger + CURRENT_STATE entries before the next opens.
halt_conditions: any FORENSIC miss · any cross-chart contamination · any LEL row loss/mutation ·
  build_runs.state != completed at W3/W4 · any grep-gate failure → STOP, restore from the wave's
  snapshot, report to native. No iteration on the native chart, ever.
may_touch: [per-wave scopes below; W1/W2 inherit the LEL brief v1.2 may_touch verbatim]
must_not_touch: ["orchestrator/planner core", "native chart 482012f1 builds before W4", "salience/priors (frozen)", "the native's 57 LEL events (content)", "ph_pramana rectification logic validating 10:43", "anything at all between W3 freeze and W4 close"]
---

# BRIEF BA-R4-WRAP — EVERYTHING TO THE NATIVE REBUILD, ONE PHASED RUN

> Four waves, strictly sequential. W1+W2 = the remaining code churn. JL-027 rules (or floors) inside W2.
> W3 re-zeroes the rifle and freezes. W4 is the one shot. Nothing else enters this runway — any new
> finding that is not a HALT condition goes to the R5 punch-list, not into these waves.

## W1 — R2.2 STEP 1: LEL SCHEMA, ONE COHERENT PR (from WIP aa3a65e2)

Execute per `CLAUDECODE_BRIEF_BA_LEL_CHART_SCOPING_v1_0.md` **v1.2** (first-intake premise). One PR:
1. Migration 423 (reviewed, blocker-fixed — deploy as banked unless CI says otherwise).
2. The two Python `lel_query` fns → chart_id filter (lel_intake.py:1416, l5_lel_intake.py:307).
3. `EXPLICIT_CLEAR_OPS` entries for `life_events` + `event_chart_state_index` + the destructive-op test
   (Clear on a chart leaves LEL rows intact) — merged BEFORE any intake writes real data.
4. retrieval_capability_spec / tool_metadata chart_id reconcile (kills the tool↔SQL impedance mismatch).
5. ASSET_NAMES / ASSET_MAP entry for `lel_events` (PD-5).

**Verify on the EMPTY state + Abhinandan first:** lel_query(1c826d5a) = empty-with-reason;
lel_query(482012f1) = empty-with-reason (57 not yet intaken — this is CORRECT at W1);
entitlement denial distinct from empty. Registry row live, count_sql binds $1, cockpit renders.
**Exit:** PR merged CI-green; migration applied prod; destructive-op test in the suite and passing.

## W2 — R2.2 STEPS 2–7 + JL-027 (the rest of the churn)

**W2.1 — Step 2 first-intake:** clear-safety PROVEN (run the destructive-op test against prod schema)
BEFORE intake → intake the 57 events @ 482012f1 from the lel_intake corpus (assert len==57) → markdown
reconciliation (count + spot-5 content vs LIFE_EVENT_LOG canonical) → recorded_at backfilled to the
`pre_instrument` sentinel. Gate: native=57 rows, Abhinandan=0 `[verify-against: prod db]`.

**W2.2 — Steps 3–7 per the LEL brief v1.2:** presence-branching in L4/L5 (kill NATIVE_CHART_ID +
hardcoded Vimshottari; grep-gates), calibration state machine (structural/sparse/calibrated →
judgment_flags), debounced save→targeted-recalibration trigger + intake surface, recorded_at leakage
routing (code, not convention), pool capture-now/consume-gated (`MIMAMSA_CROSS_CHART_POOL=off`),
retrieval + governance close-out. ALL of the LEL brief's exit gates verified — including the synthetic
two-event round-trip on Abhinandan (structural→sparse→structural).

**W2.3 — JL-027 sitting (gates W4, resolved here so nothing dangles):** surface the graha_yuddha
winner-rule OPTIONS to the native/Ācārya-Pratinidhi — per option: criterion, source text, verse
(candidates to research honestly: BPHS graha-yuddha chapter; Surya Siddhanta yuddha rules; brightness /
northern-latitude / lower-longitude formulations — cite, don't assert). Ruling protocol
(canonical-or-floor): a CITED method is adopted and implemented with derivation ledger; if no ruling or
no citable winner by W2 close → **FLOOR: winner=NULL + reason='no_ratified_classical_rule'** on all
graha_yuddha rows, never the longitude proxy. Either way JL-027 CLOSES in the ledger before W3.

**Exit:** all LEL exit gates green · JL-027 CLOSED (ruled or floored) · main clean · migrations applied ·
CURRENT_STATE + SESSION_LOG entries written.

## W3 — RE-ZERO: ABHINANDAN REVALIDATION + FREEZE

One clean **full Abhinandan rebuild** on the new HEAD, WORKER_LIMIT=2. Record the NEW canonical asset
count (66 + any W1-registered assets) — expect complete/0-error/0-queued, `build_runs.state=completed`.
Then, all `[verify-against: prod db]`:
- Abhinandan identity: Sun=Aquarius, Lagna=Aries 23°32′ Bharani-4; zero native values under 1c826d5a.
- LEL presence-branching live post-rebuild: calibration_state='structural',
  rectification_basis='structural_no_lel', 57 native rows UNTOUCHED by the Abhinandan build.
- graha_yuddha rows reflect the JL-027 disposition (cited method or NULL+reason; zero longitude-proxy).
- Degeneracy sweep on all L2–L5 scored columns; retrieval smoke (bodha_signals_get ranking-clean,
  one apex tool within cap).

**Exit → FREEZE:** record run id + HEAD SHA in RUN_LEDGER as the NEW validated configuration. From this
moment to W4 close: no merges, no migrations, no env changes, no deploys, nothing. Report the freeze to
the native — **W4 fires ONLY on an explicit native GO recorded in the ledger** (v1.1: silence never
authorizes the native rebuild; a non-interactive session holds at this line and hands off).

## W4 — PHASE-4: THE NATIVE REBUILD (the one shot)

1. **Fresh snapshot** of native 482012f1 L1–L5 chart-scoped rows INCLUDING life_events; snapshot id +
   documented restore path in RUN_LEDGER (belt: snapshot; braces: clear-safety allowlist).
2. **Rebuild native L1→L5**, standard cockpit path, full fresh rebuild (JL-024), WORKER_LIMIT=2, on the
   W3-frozen configuration.
3. **Gates, all `[verify-against: prod db]`:**
   - FORENSIC 7/7: Sun Cap · Moon Purva Bhadrapada · Lagna Aries ×5 ayanamshas · Shukla Tritiya ·
     Ravivara · Shiva yoga · Garaja karana.
   - Contamination: Abhinandan values unchanged and ≠ native.
   - bhava_arudha 12×5 present → closes the P3A deferred gate; flip P3A brief status → COMPLETE.
   - LEL: 57 rows intact post-rebuild; calibration_state='calibrated'; rectification ran LEL-fit and
     STILL validates 10:43; ph_pramana attestations reference chart-scoped rows.
   - JL-009 v1.1 values in effect: spot-5 native anchors' lift_vectors trace base_rate to ontology v1.1
     ROW-NORMALIZED lookups (mig 421 + 422 both biting).
   - JL-027 disposition visible in native graha_yuddha rows.
   - Degeneracy: min(posterior)<0.2 · signature_tier chart_defining>0 · contradictions>0 w/ domains ·
     no scored column collapsed to a constant.
   - Retrieval smoke: bodha_signals_get(482012f1, career, 10) ranking-clean; one apex tool within cap;
     an L5 surface serves judgment_flags.calibration='calibrated'.
4. **Close-out:** ledger entry (JL-⟦next⟧: Phase-4 executed per BA_PHASE4_RUNWAY_PLAN, native-ratified) ·
   CURRENT_STATE (runway CLOSED; next-objective = R5 punch-list + Retrieval 3.0 ratification) ·
   SESSION_LOG atomic close · runway plan status → COMPLETE · this brief status → COMPLETE ·
   final report to native with headline numbers.

## Anti-goals
NO scope additions mid-run (new findings → R5 punch-list unless HALT-class). NO native-chart writes
before W4. NO longitude-proxy graha_yuddha under any circumstances. NO un-frozen W4. NO close claims
without the wave's ledger + CURRENT_STATE entries (a wave without its close block is not closed).
