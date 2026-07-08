---
canonical_id: CLAUDECODE_BRIEF_BA_R4_WRAP_W2
version: 1.0
status: COMPLETE (2026-07-08) — W2 LEL churn code-complete (W2a+W2b); superseded by execution
created: 2026-07-08
author: Claude Code (BA-R4-WRAP W1 conductor) — hand-off brief for the W2 session
parent: CLAUDECODE_BRIEF_BA_R4_WRAP_v1_0.md (W2 section) + CLAUDECODE_BRIEF_BA_LEL_CHART_SCOPING_v1_0.md (v1.2, Steps 2–7)
program: BA_PHASE4_RUNWAY_PLAN_v1_0.md §R2.2 (remainder) + §R2.3 (JL-027 floor)
resume_state: >
  W1 CLOSED 2026-07-08 — PR #457 merged (main 4d036ca9); migration 423 DEPLOYED to prod and
  independently verified; JL-027 RULED ("Option A ratified, FLOOR now"). CURRENT_STATE v6.27.
  Native paced W2 into its own focused session so the native rebuild lands on settled, reviewed code.
common_rules: FROZEN orchestrator contract §N.2 · two-chart rule (Abhinandan 1c826d5a proves everything
  first) · native chart 482012f1 NEVER built/written until W4 · single writer stream · canonical-or-floor ·
  clear-safety on irreplaceable LEL data (JL-010 class) · each wave closes with ledger + CURRENT_STATE.
halt_conditions: any FORENSIC miss · any cross-chart contamination · any LEL row loss/mutation ·
  build_runs.state != completed · any grep-gate failure → STOP, restore from snapshot, report.
may_touch: [CLAUDECODE_BRIEF_BA_LEL_CHART_SCOPING_v1_0.md v1.2 may_touch verbatim + ga_structural_writer
  graha_yuddha builders (floor only) + a new migration for mimamsa_pool_contributions]
must_not_touch: ["orchestrator/planner core", "L1 ga_* writers EXCEPT the graha_yuddha winner/loser floor",
  "native chart 482012f1 builds", "salience/priors (frozen)", "the native's markdown 57 LEL events (content)",
  "ph_pramana rectification logic that validates 10:43 (de-hardcode the NATIVE_CHART_ID anchor without
   changing what validates 10:43 for the native's OWN data)"]
---

# BRIEF BA-R4-WRAP W2 — LEL churn close (Steps 2–7) + JL-027 floor

> W1 is done and deployed. This session finishes ALL remaining R2.2 code churn + implements the JL-027
> floor, verifies every LEL exit gate on Abhinandan + native DATA (native chart still NOT rebuilt), and
> closes. W3 (Abhinandan re-zero + freeze) and W4 (native rebuild, explicit-GO-gated) follow in later
> session(s). Nothing new enters scope — non-HALT findings → R5 punch-list.

## Native rulings already made (bind this session)
1. **JL-027 = Option A ratified, FLOOR now.** Implement the floor: `winner=NULL`, `loser=NULL`,
   `reason='no_ratified_classical_rule'` on ALL `graha_yuddha` winner/loser rows in BOTH
   `_build_graha_yuddha_rows` (ga_structural_writer ~L4815) AND `_build_graha_yuddha_per_varga_rows`
   (~L5198). Keep `orb_deg` (true computed fact). Mark graha_yuddha provisional/non-load-bearing in
   judgment_flags. NEVER ship the longitude proxy. Option A (Swiss Ephemeris latitude L1 fact + verified
   citation) is deferred to R5. JL-027 CLOSES in the ledger when the floor ships (before W3).
2. **NATIVE_CHART_ID grep-gate = STRICT ZERO everywhere under `brahmagyan/mimamsa`** (native ruling
   2026-07-08). Not just the LEL-path files — eradicate every occurrence, including the L5 export/learning
   subsystems. Each removal must preserve behavior via chart-scoped parameters/config, not identity
   defaults. Files with live NATIVE_CHART_ID at W1 close (verified via grep):
   - `services/ph_rectification/engine.py` (L82, L105 constant, L511 comment; + hardcoded 10:43/1984-02-05
     anchor at L92) — de-hardcode: derive dasha sequence from the chart's own `chart_dashas`, candidate
     window from stored `birth_params`; the native's 10:43 stays validated for the native's OWN data, but
     via its stored params, not a literal.
   - `brahmagyan/mimamsa/outcome.py` (L56 constant; L214/L397/L487 `chart_id or NATIVE_CHART_ID`
     identity-defaults — kill the fallback; chart_id becomes required).
   - `brahmagyan/mimamsa/l5_learning_multiplier.py` (L63), `answer_quality.py` (L74–75),
     `l5_bigquery_export.py` (L59, L81 — writes NATIVE_CHART_ID into export rows). Re-scope to the
     chart being processed.
   - Confirm none remain under `services/ph_*` or `writers/ph_*` either.

## Remaining implementation surface (what W1 did NOT do — verified at W1 close)
W1 (#457) landed: migration 423 (schema), the `ph_rectification` WRITER wrapper presence-branch
(`writers/ph_rectification/__init__.py`), the calibration state-machine MODULE
(`services/mimamsa/lel_calibration.py`), intake chart_id args, clear-safety allowlist + test,
asset_registry `lel_events`. It did NOT do the following — this session must:

- **Step 2 source-of-truth flip:** `mi_jivanaghatana.py` STILL reads the markdown at runtime
  (`_resolve_lel_markdown_path` L41, `_parse_lel_markdown` L196, read at L336). DELETE the markdown path;
  reads become `WHERE chart_id=$1` from `life_events`. Markdown consumed exactly once by the Step-2
  reconciliation, then never at runtime.
- **Step 2 first-intake (irreversible prod write of 57 irreplaceable events):**
  1. PROVE clear-safety against PROD schema first — run the destructive-op test against the live schema
     (Clear/rebuild on 482012f1 leaves LEL rows intact). This must pass BEFORE any intake write.
  2. Intake the 57 events @ 482012f1 from the `lel_intake.py` LEL_CORPUS (assert `len==57`), chart-scoped,
     `recorded_at` = `pre_instrument` sentinel.
  3. Markdown reconciliation: count 57 + spot-5 content vs `LIFE_EVENT_LOG_v1_2.md` (canonical v1.7).
  4. Gate `[verify-against: prod db]`: native life_events = 57 @ 482012f1; Abhinandan = 0.
- **Step 3 presence-branching in the ENGINE** (writer wrapper done; engine not): see the strict-zero list
  above — `ph_rectification/engine.py` de-hardcode + `outcome.py`/retrodiction chart-scoping.
- **Step 4 calibration state machine WIRING:** the module exists; wire `calibration_state`
  (structural/sparse/calibrated, n_min seed 15 → brahma_formula_constants) into `judgment_flags` on every
  L4/L5 envelope; served on a sampled L4 + L5.
- **Step 5 trigger:** ONE intake surface (API + portal form + MCP `mimamsa_outcome_record` unified),
  owner/super_admin-only; on save enqueue a STANDARD asset-scoped orchestrator run (no contract change) for
  the LEL-dependent subset for THAT chart; debounce (quiet-window seed 10 min → brahma_formula_constants) +
  explicit "Recalibrate now"; skip enqueue if identical pending run exists. **Leakage routing in CODE:**
  the calibration writer partitions events on `recorded_at` vs frozen-snapshot timestamps (before=training,
  after=outcome→two-key blind path). Not convention — code + unit/integration test.
- **Step 6 pool capture:** NEW migration — create `mimamsa_pool_contributions` (chart_id, event classes,
  weights, priors_version, consent flag, contributed_at). Every per-chart recalibration writes a
  contribution record even while gated. The pooled-prior SURFACE sits behind `MIMAMSA_CROSS_CHART_POOL`
  (env var already referenced in lel_calibration.py:146) = **off**; NO serving path reads pooled values
  while off (grep + probe). Charts contribute only with `pool_consent=true` (default false).
- **Step 7 retrieval + governance close-out:** `lel_query`/`mimamsa_lel_query` MCP chart_id required AND
  bound end-to-end (probe both charts). Entitlement denial distinct from empty. SESSION_LOG + CURRENT_STATE
  + ledger; schema_validator + drift_detector clean; version bumps per B.8.

## Exit gates (all must be green before W3) — from the LEL brief v1.2 §Exit gates
- [ ] Schema live + native=57 @ 482012f1 + Abhinandan=0 + `lel_query(p_chart_id)` + old fn gone [prod db]
      (schema half already TRUE at W1 close; the 57-row half is this session's intake)
- [ ] Clear-safety: Clear/rebuild on 482012f1 leaves 57 rows intact (destructive-op test vs prod) [prod db]
- [ ] Grep-gates: **zero** NATIVE_CHART_ID under brahmagyan/mimamsa + ph_*/writers/ph_* (STRICT — native
      ruling); zero markdown reads at runtime [repo]
- [ ] Presence-branching: Abhinandan rectification lagna-stability-only `structural_no_lel`; native LEL-fit
      still validates 10:43 [prod db]
- [ ] State machine: native `calibrated`, Abhinandan `structural`, both in judgment_flags on sampled
      L4 + L5 [prod]
- [ ] Trigger E2E on Abhinandan: insert 2 synthetic events via intake API → debounced targeted run →
      state → `sparse` → provenance/rectification rows for 1c826d5a only → DELETE synthetics + re-fire →
      state → `structural` (both ways; native untouched) [prod db]
- [ ] Leakage: recorded_at-AFTER-snapshot routes to outcome not training (unit + integration) [repo+db]
- [ ] Pool: contributions captured; `MIMAMSA_CROSS_CHART_POOL=off`; no serving path reads pooled [repo+prod]
- [ ] MCP probes: lel_query(Abhinandan)=empty-with-reason, lel_query(native)=57, entitlement≠empty [prod]
- [ ] **JL-027 floor:** all graha_yuddha winner/loser rows = NULL + reason (both builders); zero longitude
      proxy; orb_deg kept; JL-027 CLOSED in ledger [repo + Abhinandan rebuild]
- [ ] FORENSIC 7/7 unchanged on 482012f1 (this brief must not touch L1 chart_facts); golden-eval
      non-regression [prod]

## Execution model
Conductor + subagent swarm. Implementers write code (per-step scoped worktrees); a SEPARATE verifier
subagent re-runs each gate (never the implementer). Land as CI-gated PR(s). First-intake is a data op —
prove clear-safety vs prod schema FIRST, then intake, then reconcile. After all gates green + JL-027 floor
shipped + ledger/CURRENT_STATE/SESSION_LOG written → W2 closes; W3 (Abhinandan re-zero + FREEZE) opens next.

## Anti-goals
No orchestrator/WriterBase change. No full-chart rebuild as the trigger (targeted subset). No identity
branching anywhere (STRICT grep-gate). No pooled consumption while flag off. No edits to the native's 57
events. No native-chart writes before W4. No longitude-proxy graha_yuddha. No W2→W4 straight-through — W4
fires only on explicit native GO in a later session.
