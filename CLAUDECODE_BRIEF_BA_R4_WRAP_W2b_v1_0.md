---
canonical_id: CLAUDECODE_BRIEF_BA_R4_WRAP_W2b
version: 1.0
status: COMPLETE (2026-07-08) — W2b built+verified+deployed (PR #460); calibration serving + intake API + pool live
created: 2026-07-08
author: Claude Code (BA-R4-WRAP W2a conductor) — hand-off brief for the W2b session
parent: CLAUDECODE_BRIEF_BA_R4_WRAP_W2_v1_0.md (Steps 4–6) + CLAUDECODE_BRIEF_BA_LEL_CHART_SCOPING_v1_0.md
program: BA_PHASE4_RUNWAY_PLAN_v1_0.md §R2.2 (remainder) — the last LEL churn before W3
resume_state: >
  W2a CLOSED 2026-07-08 — PR #459 (chart-scoped intake + strict-zero NATIVE_CHART_ID + graha_yuddha floor)
  independently verified + merged. 57 LEL events LIVE @ 482012f1 (recorded_at=pre_instrument sentinel).
  Both grep-gates EMPTY. JL-027 floor implemented in code (prod rows reflect it at next build).
  What's LEFT for W2 = D (Step 4 persistence+wiring) + E (Steps 5–6: intake write API + pool). These are
  net-new builds; the native paced them here so they land on reviewed code (not minutes-old code).
common_rules: FROZEN orchestrator contract §N.2 (trigger = standard asset-scoped run enqueue, NO contract
  change) · two-chart rule (Abhinandan proves everything first) · native chart 482012f1 NEVER built until W4 ·
  single writer stream · clear-safety on LEL (JL-010 class) · shrinkage-never-gates (MIMAMSA_V2).
halt_conditions: any LEL row loss/mutation on 482012f1 · any cross-chart contamination · build_runs.state
  != completed · grep-gate regression → STOP, restore, report.
may_touch: ["services/mimamsa/lel_calibration.py (judgment_flags is built — wire it)", "ph_*/mi_* writer
  envelopes (stamp judgment_flags)", "a NEW migration for the judgment_flags/calibration-summary surface",
  "a NEW migration for mimamsa_pool_contributions", "NEW LEL intake write API (platform/src route + MCP tool)
  + debounced recalibration trigger", "recorded_at leakage-routing wiring in the calibration writer",
  "asset_registry/feature-flag wiring for MIMAMSA_CROSS_CHART_POOL"]
must_not_touch: ["orchestrator/planner core", "L1 ga_* writers + chart_facts", "the native's 57 LEL rows
  (content — scoping/reading only)", "ph_pramana rectification logic that validates 10:43", "salience/priors",
  "anything already de-hardcoded in W2a (grep-gates must stay EMPTY — no NATIVE_CHART_ID reintroduced)"]
---

# BRIEF BA-R4-WRAP W2b — the two net-new LEL builds (Steps 4–6)

> W2a landed the de-hardcode + intake + JL-027 floor. W2b builds the two features that don't exist yet,
> then closes W2. After W2b's exit gates are green, W3 (Abhinandan re-zero + FREEZE) opens.

## Already built (W2a) — do NOT rebuild
- Chart-scoped `seed_lel_intake` + 57 rows live @ 482012f1 (recorded_at = PRE_INSTRUMENT_SENTINEL 2000-01-01).
- `services/mimamsa/lel_calibration.py`: `calibration_state()`, `judgment_flags()`, `rectification_basis()`,
  `recorded_at_partition()`, `pool_enabled()`/`may_consume_into_pool()`, `should_recalibrate()` debounce,
  `count_chart_lel_events()`. **`judgment_flags()` has ZERO callers — that's D's job.**
- `ph_rectification/__init__.py` writer already derives per-chart from `chart_dashas`/`chart_facts`.
- `mi_jivanaghatana` reads life_events chart-scoped (no markdown). graha_yuddha floored. Strict-zero done.

## D — Step 4: calibration_state persistence + judgment_flags wiring
1. **Migration (surgical):** add the persistence surface for calibration state. Either a `judgment_flags jsonb`
   column on the relevant L4/L5 envelope table(s) OR a small `mimamsa_calibration_summary(chart_id PK,
   calibration_state, lel_event_count, rectification_basis, load_bearing, updated_at)` table. Pick the one
   that matches how L4/L5 envelopes are served (read the ph_rectification + mi_* result shapes first).
2. **Wire `judgment_flags(count_chart_lel_events(conn, chart_id))`** into every L4/L5 envelope build site
   (ph_rectification writer near the phala_rectification_best emit; the mi_* calibration writers; the
   outcome.py calibration read). Serve `calibration='structural_prior_only'` for a 0-event chart and
   `'calibrated'` for the native (57 ≥ n_min).
3. **Gate [verify-against: prod]:** native calibration_state='calibrated', Abhinandan='structural', both
   visible in judgment_flags on a sampled L4 + L5 envelope.

## E — Steps 5–6: LEL intake write API + debounce + leakage routing + gated pool
1. **ONE intake write surface** (new): a platform/src API route + an MCP write tool (`mimamsa_outcome_record`
   or `lel_event_record`), owner/super_admin-only (Nirmāṇa access), validates against
   `brahma_event_ontology` event classes, writes `life_events` row(s) chart-scoped with `occurred_at` +
   `recorded_at=now()`. (W2a proved NO such write API exists yet — build it; assetClearSpec already assumes it.)
2. **Debounced trigger:** on save, enqueue a STANDARD asset-scoped orchestrator run (NO contract change) for
   the LEL-dependent subset for THAT chart (`mi_jivanaghatana` + LEL-consuming mi_* + `ph_rectification` +
   `ph_pramana`). Debounce with `should_recalibrate()` (quiet-window seed 10 min → brahma_formula_constants);
   explicit "Recalibrate now"; skip if identical pending run exists.
3. **Leakage routing in CODE:** wire `recorded_at_partition()` into the calibration writer — events with
   recorded_at BEFORE a frozen prediction snapshot = training; AFTER = outcome evidence (two-key blind path).
   Unit + integration test proving an after-snapshot event routes to outcome, not training.
4. **Pool (Step 6):** NEW migration `mimamsa_pool_contributions` (chart_id, event classes, weights,
   priors_version, consent flag, contributed_at). Every per-chart recalibration writes a contribution record
   even while gated. Pooled-prior SURFACE behind `MIMAMSA_CROSS_CHART_POOL` = **off**; no serving path reads
   pooled values while off (grep + probe). pool_consent default false.

## Exit gates (all green before W3) — the LEL brief v1.2 gates that W2a did NOT yet satisfy
- [ ] State machine served: native calibration_state='calibrated', Abhinandan='structural' in judgment_flags
      on a sampled L4 + L5 envelope [verify-against: prod]
- [ ] Trigger E2E on Abhinandan: insert 2 synthetic events via the intake API → debounced targeted run →
      state → 'sparse' → provenance/rectification rows for 1c826d5a only → DELETE synthetics + re-fire →
      state → 'structural' (both ways; native 57 rows UNTOUCHED throughout) [verify-against: prod db]
- [ ] Leakage: recorded_at-AFTER-snapshot routes to outcome not training (unit + integration) [repo+db]
- [ ] Pool: contributions captured on a recalibration; MIMAMSA_CROSS_CHART_POOL=off; no serving path reads
      pooled values (grep + probe) [repo+prod]
- [ ] MCP probes: lel_query(Abhinandan)=empty-with-reason, lel_query(native)=57, entitlement denial distinct
      from empty [verify-against: prod]  (lel_query already chart-scoped in W1 — just probe)
- [ ] Grep-gates still EMPTY (no NATIVE_CHART_ID reintroduced); FORENSIC 7/7 unchanged on 482012f1 [prod]
- [ ] JL-027: after an Abhinandan build, graha_yuddha rows show winner/loser NULL + reason (floor visible) —
      this also closes JL-027 in the ledger.

## Execution model
Conductor + subagent swarm; separate verifier per gate. Land as CI-gated PR(s). The intake-API E2E is the
centerpiece — build it TDD. After all gates green + JL-027 confirmed floored in an Abhinandan build + ledger/
CURRENT_STATE/SESSION_LOG written → W2 (a+b) CLOSES; W3 opens on the native's word.

## Anti-goals
No orchestrator/WriterBase contract change. No full rebuild as the trigger (targeted subset). No pooled
consumption while flag off. No native-chart writes before W4. No NATIVE_CHART_ID reintroduced. No longitude
proxy. No W3/W4 straight-through — W3 on the native's word, W4 only on explicit ledger-recorded GO.
