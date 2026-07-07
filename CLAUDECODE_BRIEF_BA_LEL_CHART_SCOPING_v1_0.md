---
canonical_id: CLAUDECODE_BRIEF_BA_LEL_CHART_SCOPING
version: 1.2
status: IN-EXECUTION — Phase R2.2 of BA_PHASE4_RUNWAY_PLAN_v1_0.md (before the native rebuild). Step 1 in
  progress: migration 423 reviewed + banked on WIP branch aa3a65e2 (NOT deployed); coupled Step-1 code
  (2 Python lel_query chart_id filters, EXPLICIT_CLEAR_OPS + destructive test, capability-spec/tool_metadata,
  ASSET_NAMES) pending in the SAME PR. Then Step 2 first-intake. Execute against THIS (v1.2).
created: 2026-07-07
changelog:
  - v1.2 (2026-07-07): PREMISE CORRECTION from R2.2 Step-1 recon — prod `life_events` is EMPTY (0 rows),
    not 57. The 57 events are safe in the canonical markdown + lel_intake.py corpus (assert len==57).
    Step 1's "backfill existing rows" is void; the corrected path is Step 2 FIRST-INTAKE of the 57 into
    the new chart-scoped table @ 482012f1. Every "native = 57 rows" sanity/exit gate is true only AFTER
    Step-2 intake — gates re-tagged accordingly. Migration 423 (reviewed) banked on WIP branch aa3a65e2.
  - v1.1 (2026-07-07): re-sequenced BEFORE Phase-4 per native decision — the native rebuild lands on the
    final LEL architecture (one build, no post-rebuild recalibration pass). Validated-config claim is
    re-earned via the R3 Abhinandan revalidation run (see runway plan). Step 0 precondition updated.
author: Cowork (Beyond-Acharya program) — native-directed LEL re-architecture, ratified in sitting 2026-07-07
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — governed by 00_ARCHITECTURE/BA_PHASE4_RUNWAY_PLAN_v1_0.md
  (Phase R2; runs together with the JL-026 dual-write audit, before the native rebuild)
slots: Step-1 migration = 423 (banked, WIP aa3a65e2); ⟦NEXT_MIGRATION_NUMBERS for Steps 2+⟧ ⟦HEAD_SHA⟧
common_rules: FROZEN orchestrator contract §N.2 (no contract changes — the trigger uses standard
  asset-scoped runs) · surgical migrations · two-chart rule (Abhinandan first for every verification) ·
  shrinkage-never-gates (MIMAMSA_V2 doctrine) · LEL is irreplaceable user-authored data (JL-010 class).
sanity_values: native 482012f1 life_events = 57 rows before AND after every step; FORENSIC 7/7 untouched
  (this brief must not touch L1); Abhinandan 1c826d5a life_events = 0 rows and calibration_state='structural'.
may_touch: ["life_events/event_chart_state_index schema + lel_query() SQL fn", "brahmagyan/mimamsa/lel_intake.py + l5_lel_intake.py + outcome.py", "mi_jivanaghatana.py + LEL-consuming mi_* writers", "ph_rectification (writer + services/engine) + ph_pramana LEL sourcing", "NEW LEL save/intake API + recalibration trigger", "asset_registry rows for life_events (register) + clear-safety allowlist", "MCP lel_query / mimamsa_lel_query handlers", "portal LEL entry surface (minimal)"]
must_not_touch: ["orchestrator/planner core (trigger = standard asset-scoped run enqueue only)", "L1 ga_* writers + chart_facts", "L2 bodha stored data", "salience/priors (frozen)", "the native's 57 LEL events (content) — scoping only, never edits", "ph_pramana rectification logic that validates 10:43"]
---

# BRIEF BA-LEL — LEL AS A LIVING PER-CHART ASSET (availability-driven calibration)

**Ratified design (native sitting 2026-07-07):** LEL is chart-specific, may arrive at ANY time
(pre-build, mid-build, or post-build during portal usage), and whenever LEL for a chart is saved,
calibration re-fires for that chart. Calibration keys on DATA AVAILABILITY, never on chart identity
and never on build moment. Cross-chart pooling: CAPTURE now, CONSUME gated behind a feature flag.

**Audit findings this brief fixes (Cowork audit 2026-07-07, file:line evidence in the audit log):**
- `life_events` + `event_chart_state_index` have NO chart_id (brahma_mimamsa_lel_intake.sql:45,:97) — global.
- `lel_query()` SQL fn has NO chart_id param (:176); MCP tool requires chart_id (mimamsa_lel_intake.ts:102)
  but the binding is silently dropped — impedance mismatch.
- `mi_jivanaghatana` writes per-chart but READS the native markdown for all charts (mi_jivanaghatana.py:40–62,
  195–278); intake scripts hardcode NATIVE_CHART_ID (lel_intake.py:53, l5_lel_intake.py:53).
- `ph_rectification` uses an identity firewall `if chart_id != NATIVE_CHART_ID: return []`
  (writers/ph_rectification/__init__.py:81–84, PR #448 stopgap) + hardcoded native Vimshottari sequence
  and 10:43 nominal time (services/…/rectification.py:70–72, 116–127).
- `life_events` absent from asset_registry — no scope declaration, no count_sql, unprotected from Clear.

## Step 0 — Preconditions + snapshot
Runway plan Phase R1 CLOSED (JL-009 glance done; native inputs recorded — see BA_PHASE4_RUNWAY_PLAN §R1).
Dump `life_events` + `event_chart_state_index` +
`mimamsa_event_provenance` + `phala_rectification` (both charts) → record snapshot id in RUN_LEDGER.

## Step 1 — Schema: chart-scope the storage (migrations ⟦NEXT_MIGRATION_NUMBERS⟧, surgical)
1. `ALTER TABLE life_events ADD COLUMN chart_id uuid REFERENCES charts(id)`; (v1.2: prod table is
   EMPTY — no backfill; if any rows exist at execution time, backfill them to
   `482012f1-710e-4a25-994a-93821f5871aa`); SET NOT NULL; re-key PK/uniques to `(chart_id, event_id)`;
   index on chart_id. Same for `event_chart_state_index` (chart_id + re-key `UNIQUE(chart_id, event_id)`).
2. `ADD COLUMN occurred_at date` (rename/verify existing event_date semantics = occurrence) +
   `ADD COLUMN recorded_at timestamptz NOT NULL DEFAULT now()`; backfill recorded_at for the 57 native
   rows to a sentinel `pre_instrument` timestamp (their recording predates all predictions — pure training).
3. `ADD COLUMN pool_consent boolean NOT NULL DEFAULT false` + `contributed_to_pool_at timestamptz NULL`.
4. `lel_query()` → new signature `lel_query(p_chart_id uuid, p_domain, p_date_start, p_date_end, p_limit)`
   with `WHERE chart_id = p_chart_id`; drop/replace the old fn (grep all callers). This closes the MCP
   impedance mismatch — verify the tool's chart_id now binds end-to-end.
5. Register in `asset_registry`: `asset_id='lel_events'`, layer=mimamsa (source-data), `scope='per_chart'`,
   **`has_writer=false`** (user-authored source data, NOT a built asset),
   `count_sql='SELECT count(*) FROM life_events WHERE chart_id=$1'`. PD-5: ASSET_NAMES/ASSET_MAP same PR.
6. **Clear-safety:** add `life_events` + `event_chart_state_index` to the explicit-clear allowlist
   (EXPLICIT_CLEAR_OPS, mirroring the mi_abhilekha/JL-010 fix). No rebuild, Clear, or cascade may EVER
   delete LEL rows. Add a destructive-op test proving Clear on the chart leaves LEL intact.

## Step 2 — Source-of-truth flip (FORENSIC precedent: DB live, markdown archived)
- DB `life_events` becomes the live per-chart LEL authority. `LIFE_EVENT_LOG_v1_2.md` (canonical v1.7)
  remains the NATIVE'S provenance archive — consumed exactly once by a one-time intake reconciliation:
  verify the 57 DB rows match the markdown (count + spot-5 content), record the reconciliation, then
  markdown is never read at build/serve time again.
- `mi_jivanaghatana`: DELETE the markdown path resolution (`_resolve_lel_markdown_path`,
  `MI_LEL_MARKDOWN_PATH` env, `_parse_lel_markdown`) — reads become `WHERE chart_id = $1` from
  life_events for EVERY chart, native included.
- `lel_intake.py` / `l5_lel_intake.py`: remove hardcoded NATIVE_CHART_ID module constants; intake takes
  chart_id as a required argument. The hardcoded train/holdout boundary date moves to
  brahma_formula_constants (class=engineering, calibratable).
- Update CANONICAL_ARTIFACTS/CAPABILITY_MANIFEST: LEL markdown status → ARCHIVED-PROVENANCE (native only);
  live source = life_events table. CLAUDE.md §D cached snapshot note appended (version bump per B.8).

## Step 3 — Identity-branching → presence-branching (L4 + L5)
- `ph_rectification`: DELETE the `chart_id != NATIVE_CHART_ID → []` firewall. Replace with:
  `events = load_lel(chart_id)`; if `len(events) >= min_events_for_lel_fit` (constant →
  brahma_formula_constants, seed 5) run LEL-fit scoring; else lagna-stability-only with
  `rectification_basis='structural_no_lel'` flag. DELETE the hardcoded `VIMSHOTTARI_MD_SEQUENCE` and
  10:43-anchored candidate logic — derive the dasha sequence from the CHART'S OWN `chart_dashas`
  (ga_dashas rows) and the candidate window from the chart's stored birth_params. Grep-gate: zero
  occurrences of `NATIVE_CHART_ID` under services/ph_* and writers/ph_* after this step.
- `ph_pramana`: LEL evidence lookup goes through the chart-scoped path; fix the orphaned
  `lel_entry_id` reference (point it at life_events' real key or add the FK; NULL stays legal = pending).
- L5 `outcome.py` + retrodiction writers: every life_events read carries `WHERE chart_id = $1`.
  Native's markdown-era assumptions removed. Grep-gate: zero `NATIVE_CHART_ID` under brahmagyan/mimamsa.

## Step 4 — Per-chart calibration state machine
New derived state per chart (computed, stored on the calibration summary surface, served in
judgment_flags of every L4/L5 envelope):
`calibration_state = 'structural'` (0 events) | `'sparse'` (1 to n_min−1) | `'calibrated'` (≥ n_min);
n_min → brahma_formula_constants (seed 15, calibratable). Shrinkage weight scales continuously with n —
states are LABELS for honesty, never gates on computation (a 4-event chart gets weak calibration, not none).
Native enters 'calibrated' (57); Abhinandan enters 'structural' (0). Serving: any L4 anchor or L5
calibration answer on a 'structural' chart carries `judgment_flags.calibration='structural_prior_only'`.

## Step 5 — The trigger: LEL save → debounced targeted recalibration
- ONE intake surface (API + portal form + MCP write tool `mimamsa_outcome_record` unified): validates
  against brahma_event_ontology event classes, writes life_events row(s) with occurred_at + recorded_at,
  chart-scoped, owner/super_admin-only (Nirmāṇa access rule).
- On save: enqueue a **standard asset-scoped orchestrator run** for the LEL-dependent subset ONLY —
  `mi_jivanaghatana` + the LEL-consuming mi_* calibration writers + `ph_rectification` + `ph_pramana` —
  for THAT chart. NO orchestrator contract change: this is a normal partial build enqueue.
- **Debounce:** quiet-window (seed 10 min → brahma_formula_constants) so a 15-event entry session fires
  ONE recalibration; plus an explicit "Recalibrate now" affordance. Guard: skip enqueue if an identical
  pending run exists.
- **Leakage discipline (MIMAMSA_V2):** at recalibration, events route by recorded_at — events recorded
  BEFORE a frozen prediction snapshot = training; recorded AFTER = outcome evidence → two-key blind
  protocol path ONLY (they judge predictions; they never retro-feed the priors that generated them).
  This routing must be code, not convention: the calibration writer partitions on recorded_at vs
  snapshot timestamps.

## Step 6 — Cross-chart: capture now, consume gated
- Every per-chart recalibration ALSO writes a pooled-contribution record (provenance-tagged: chart_id,
  event classes contributed, weights, priors_version, consent flag honored) to a new
  `mimamsa_pool_contributions` table — even while the pool is gated.
- The pooled-prior SURFACE (any read path that blends cross-chart calibration into serving) sits behind
  feature flag `MIMAMSA_CROSS_CHART_POOL` = **off**. No serving path may read pooled values while off.
  When the native opens the gate later, the pool computes retroactively from captured contributions —
  zero data loss from gating. Charts contribute only with pool_consent=true (native sets; default false).

## Step 7 — Retrieval + governance close-out
- `lel_query` / `mimamsa_lel_query` MCP tools: chart_id required AND bound end-to-end (probe: query
  Abhinandan → 0 rows + honest empty-with-reason, NOT native's events; query native → 57).
- Entitlement: LEL reads/writes respect chart entitlement (an unentitled caller gets denied, not empty).
- SESSION_LOG + CURRENT_STATE + BA_JUDGMENT_LEDGER (log this brief's rulings as JL-⟦next⟧: LEL
  availability-driven calibration architecture, native-ratified 2026-07-07). schema_validator +
  drift_detector clean. Version bumps per B.8 on every touched canonical artifact.

## Anti-goals
NO orchestrator/WriterBase contract change. NO full-chart rebuild as the trigger (targeted subset only).
NO identity branching anywhere (grep-gated). NO pooled consumption while the flag is off. NO edits to the
native's 57 events. NO gates-instead-of-shrinkage. Markdown never read at runtime after Step 2.

## Exit gates
- [ ] Schema: life_events/event_chart_state_index chart-keyed; native=57 rows @ 482012f1; Abhinandan=0;
      lel_query(p_chart_id) live; old fn gone `[verify-against: prod db]`
- [ ] Clear-safety: Clear/rebuild on 482012f1 leaves 57 LEL rows intact (destructive-op test)
      `[verify-against: prod db]`
- [ ] Grep-gates: zero NATIVE_CHART_ID in ph_*/mi_* engines+writers; zero markdown reads at runtime
      `[verify-against: repo]`
- [ ] Presence-branching proof: Abhinandan rectification runs lagna-stability-only w/
      `structural_no_lel`; native runs LEL-fit and STILL validates 10:43 `[verify-against: prod db]`
- [ ] State machine: native calibration_state='calibrated', Abhinandan='structural'; both served in
      judgment_flags on a sampled L4 + L5 envelope `[verify-against: prod]`
- [ ] Trigger E2E: insert 2 synthetic test events on Abhinandan via the intake API → debounced targeted
      run fires → state flips to 'sparse' → provenance/rectification rows appear for 1c826d5a only →
      DELETE the synthetic events + re-fire → state returns to 'structural' (proves the loop both ways;
      native chart untouched throughout) `[verify-against: prod db]`
- [ ] Leakage: synthetic event with recorded_at AFTER a frozen snapshot routes to outcome path, not
      training (unit + integration test) `[verify-against: repo+db]`
- [ ] Pool: contributions captured for native recalibration; MIMAMSA_CROSS_CHART_POOL=off; no serving
      path reads pooled values (grep + probe) `[verify-against: repo+prod]`
- [ ] MCP probes: lel_query(Abhinandan)=empty-with-reason, lel_query(native)=57, entitlement denial
      distinct from empty `[verify-against: prod]`
- [ ] FORENSIC 7/7 unchanged on 482012f1; golden-eval non-regression `[verify-against: prod]`
