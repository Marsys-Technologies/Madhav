---
artifact: BUILDER_PRIVILEGE_AUDIT_GOCHARA
version: "1.2"
status: CURRENT
date: 2026-10-02
author: Stream C (Kimi), TASK C2 (steward M20261001T221019-7dbe); v1.1 extension TASK C3 PART B (steward M20261001T222338-763f); v1.2 extension TASK C4 (steward M20261001T224706-93e2)
writes: "NONE — every production query below was a SELECT through the read-only credential (amjis_app, default_transaction_read_only=on)"
changelog: "v1.1 (2026-10-02): C3 PART B — helper services; 0 new gaps; 1 NOT PRESENT relation. v1.2 (2026-10-02): C4 — FUNCTION EXECUTE audit over the writer-DML tables + the 1153–1157 contract tables; 22 function gaps; sequence addendum to v1.0."
---

# data_plane_builder privilege audit — Gochara writer family

**Purpose.** The production build job runs as Postgres role `data_plane_builder`;
four builds failed on 2026-10-01 because that role lacked a privilege a writer
needed (migration 1211 fixed the asset_throughput_state_audit case). This audit
finds the remaining gaps for the GOCHARA family **before** a build does.

**Method.** (1) Every SQL string in each in-scope writer on `origin/main` was
read; relations and operations are listed with `file:line` — nothing guessed.
(2) Each (relation, operation) was checked read-only in production with
`has_table_privilege('data_plane_builder', …)`; row-level security recorded from
`pg_class.relrowsecurity`; owned sequences of every INSERT target checked via
`pg_get_serial_sequence` (the 1211 failure mode was a missing USAGE grant on an
identity sequence). (3) No writer SQL calls `nextval`/`setval` directly, and no
INSERT-target table owns a sequence — the sequence column is therefore empty
throughout and omitted from the per-writer tables.

**Result: 1 gap.** `bg_transit_av_gates` SELECT is not granted. All 24
relations exist in production (none NOT PRESENT). RLS is OFF on every relation
— no policy-reference chase was required.

## Per-writer surface

granted? = production `has_table_privilege` for `data_plane_builder` (2026-10-02).
ops: S=SELECT, I=INSERT, U=UPDATE, D=DELETE.

### ka_gochara_resonance — `services/ka_gochara_resonance/writer.py`

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| brahma_event_ontology | S | writer.py:808 | yes | off |
| bg_transit_rules | S | writer.py:814 | yes | off |
| chart_facts | S | writer.py:821, 828, 861, 877, 889, 899, 909 | yes | off |
| ga_yoga_firings | S | writer.py:835 | yes | off |
| chart_dashas | S | writer.py:851 | yes | off |
| reference_signs | S | writer.py:870 | yes | off |
| gochara_resonance_map | S | writer.py:919 | yes | off |
| gochara_resonance_map | D | writer.py:923 | yes | off |
| gochara_resonance_map | I | writer.py:926 | yes | off |

### ka_moorti_nirnaya — `services/ka_moorti_nirnaya/writer.py`

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| chart_facts | S | writer.py:86 | yes | off |
| ephemeris_daily | S | writer.py:93 | yes | off |
| bg_transit_moorti | S | writer.py:100 | yes | off |
| kala_moorti_nirnaya | D | writer.py:103 | yes | off |
| kala_moorti_nirnaya | I | writer.py:106 | yes | off |

### ka_vedha_gochara — `services/ka_vedha_gochara/writer.py`, `freshness.py`

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| chart_facts | S | writer.py:147 | yes | off |
| bg_transit_rules | S | writer.py:154 | yes | off |
| ephemeris_daily | S | writer.py:160, 189 | yes | off |
| bg_sarvatobhadra_grid | S | writer.py:169 | yes | off |
| bg_phaladeepika_latta | S | writer.py:177 | yes | off |
| bg_vedha_malefic_scale | S | writer.py:182 | yes | off |
| kala_vedha_gochara | D | writer.py:194 | yes | off |
| kala_vedha_gochara | I | writer.py:197 | yes | off |
| kala_vedha_gochara | S | freshness.py:57 | yes | off |
| information_schema.columns | S | freshness.py:93 | n/a (system catalog) | — |
| kala_moorti_nirnaya | S | freshness.py:99, 102 | yes | off |

### w2g — bg_gochara_arcs writer (`pipeline/orchestrator/writers/bg_gochara_arcs.py`, `services/w2g/db_source.py`)

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| ephemeris_daily | S | db_source.py:80, 178 | yes | off |
| bg_gochara_arcs | S | db_source.py:170; bg_gochara_arcs.py:188 | yes | off |
| bg_gochara_arcs | I | bg_gochara_arcs.py:76 | yes | off |
| bg_gochara_arcs | D | bg_gochara_arcs.py:149, 156 | yes | off |

### w2g — ka_gochara writer (`pipeline/orchestrator/writers/ka_gochara.py`)

Writes `kala_gochara_windows_v2` at generation `'2.0'` (TABLE, :120).

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| gochara_resonance_map | S | ka_gochara.py:193 | yes | off |
| bg_gochara_arcs | S | ka_gochara.py:412 | yes | off |
| kala_gochara_windows_v2 | I | ka_gochara.py:141 | yes | off |
| kala_gochara_windows_v2 | D | ka_gochara.py:336 | yes | off |
| kala_gochara_v2_build_state | S | ka_gochara.py:421 | yes | off |
| kala_gochara_v2_build_state | I + U | ka_gochara.py:437 (ON CONFLICT DO UPDATE, :442) | yes / yes | off |

### ka_gochara_v3_century_materialize (`pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py` + `services/gochara_v3/`)

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| brahma_event_ontology | S | ka_gochara_v3_century_materialize.py:950, 1057; gochara_v3/threshold.py:172 | yes | off |
| gochara_resonance_map | S | ka_gochara_v3_century_materialize.py:1253, 1313 | yes | off |
| kala_gochara_v2_build_state | S | ka_gochara_v3_century_materialize.py:1415 | yes | off |
| kala_gochara_v2_build_state | I + U | ka_gochara_v3_century_materialize.py:1476 (ON CONFLICT DO UPDATE, :1482) | yes / yes | off |
| kala_gochara_windows_v2 | S | ka_gochara_v3_century_materialize.py:1429 | yes | off |
| kala_gochara_windows_v2 | I | ka_gochara_v3_century_materialize.py:517 | yes | off |
| kala_gochara_windows_v2 | D | ka_gochara_v3_century_materialize.py:2279 | yes | off |
| kala_gochara_windows | I | ka_gochara_v3_century_materialize.py:554 | yes | off |
| kala_gochara_windows | D | ka_gochara_v3_century_materialize.py:2289 | yes | off |
| chart_facts | S | gochara_v3/context.py:379, 494, 688, 765, 829 | yes | off |
| **bg_transit_av_gates** | **S** | **gochara_v3/context.py:444** | **NO — GAP** | off |
| kala_vedha_gochara | S | gochara_v3/context.py:535 | yes | off |
| kala_moorti_nirnaya | S | gochara_v3/context.py:599 | yes | off |
| bg_vedha_malefic_scale | S | gochara_v3/context.py:644 | yes | off |

### gochara_kernel ledger (`services/gochara_kernel/ledger.py`) — the '4.x' candidate-build write path

`record_store` is not present in `services/gochara_kernel/` (steward's scope
said "if present"). No other gochara_kernel module executes SQL.

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| kala_gochara_convention | I | ledger.py:362 | yes | off |
| kala_gochara_convention | S | ledger.py:398 | yes | off |
| kala_gochara_publication | S | ledger.py:228 | yes | off |
| kala_gochara_publication | I | ledger.py:471 | yes | off |
| kala_gochara_publication | U | ledger.py:491, 570, 588, 607, 705 | yes | off |
| kala_gochara_contacts | I | ledger.py:341 | yes | off |
| kala_gochara_contacts | D | ledger.py:407, 623 | yes | off |
| kala_gochara_contacts | S | ledger.py:506, 544 | yes | off |
| kala_gochara_coverage | D | ledger.py:441, 619 | yes | off |
| kala_gochara_coverage | I | ledger.py:449 | yes | off |
| kala_gochara_coverage | S | ledger.py:511, 549 | yes | off |
| kala_gochara_windows | S | ledger.py:558 (+ `to_regclass` probe :563) | yes | off |
| kala_gochara_windows | D | ledger.py:676 | yes | off |
| kala_gochara_authority | S | ledger.py:666 | yes | off |

### cutover step06 scripts (`scripts/kala_gochara_cutover/step06*.py`)

`step06_candidate_build.py` contains no direct SQL; it drives the ledger
functions above (`register_convention` → `publish_candidate` →
`write_contacts`/`write_coverage`, step06_candidate_build.py:210-218), so its
surface is the ledger's. The other three:

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| gochara_resonance_map | S | step06_enumerate_episodes.py:185; step06a_class_context.py:320 (JOIN); step06b_windows_projection.py:1704 | yes | off |
| chart_facts | S | step06_enumerate_episodes.py:192, 199, 206, 219; step06a_class_context.py:133, 178 | yes | off |
| ga_yoga_firings | S | step06_enumerate_episodes.py:213 | yes | off |
| kala_gochara_contacts | S | step06a_class_context.py:319; step06b_windows_projection.py:1670 | yes | off |
| information_schema.columns | S | step06b_windows_projection.py:1657 | n/a (system catalog) | — |
| kala_vedha_gochara | S | step06b_windows_projection.py:1721 | yes | off |
| bg_vedha_malefic_scale | S | step06b_windows_projection.py:1737 | yes | off |
| kala_gochara_windows | S | step06b_windows_projection.py:2125 | yes | off |
| kala_gochara_windows | D | step06b_windows_projection.py:1810 | yes | off |
| kala_gochara_windows | I | step06b_windows_projection.py:1863 | yes | off |
| kala_gochara_publication | U | step06b_windows_projection.py:1882 | yes | off |

## GAPS

| relation | operation | needed by |
|---|---|---|
| `bg_transit_av_gates` | SELECT | `services/gochara_v3/context.py:444` (`_fetch_all_av_gate_rows`, the AV-gating pre-fetch on the ka_gochara_v3_century_materialize path) |

Note on severity: that fetch runs inside a `savepoint_scope` with a
`try/except` that logs at ERROR and returns the error to the caller
(context.py:441-470), so a build degrades AV gating loudly rather than dying —
but the privilege is genuinely absent and the gate's data would be silently
empty for `data_plane_builder` until granted. **This report prescribes no fix;
no migration was written** (per the task).

## NOT PRESENT

None in the v1.0 scope — all 24 relations referenced by the in-scope SQL exist
in production. (v1.1 adds one NOT PRESENT relation; see below.)

---

# v1.1 extension (TASK C3 PART B) — helper services and the full kernel

Same method and read-only credential as v1.0. Scope added:
`services/gochara_grammar/*`, `services/gochara_intensity/*`,
`services/ka_gochara_sweep/*`, `services/gochara_rules/*`, and **every** module
of `services/gochara_kernel/*` (not only ledger.py — the other kernel modules
carry no SQL at all; verified by reading each). `services/gochara_rules/*`
executes **no SQL** (no `execute`/`executemany` call sites; its registry is
pure Python) — recorded so the scope is provably covered, not skipped.

## Per-module surface added in v1.1

### gochara_grammar

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| gochara_resonance_map | S | resonance_map.py:50 | yes | off |
| chart_facts | S | primitives.py:721, 790, 1347 | yes | off |
| bg_transit_av_gates | S | primitives.py:949 | **NO — same gap as v1.0 (gochara_v3/context.py:444); C3 PART A migration 1225 closes it** | off |
| bg_transit_rules | S | primitives.py:1053 | yes | off |
| chart_dashas | S | dasha_data.py:53, 208 | yes | off |
| brahma_event_ontology | S | event_class_scope.py:167 | yes | off |
| l1_sarvatobhadra_vedha | S | sarvatobhadra.py:112, 114 | **NOT PRESENT** (relation absent in production — presumably an unapplied migration; listed per the task, not a grant gap) | — |

### gochara_intensity

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| chart_facts | S | enrichment.py:164, 199, 245 | yes | off |
| reference_signs | S | enrichment.py:224 | yes | off |
| brahma_event_ontology | S | engine.py:81; valence.py:96 | yes | off |

(`_dbutil.py` holds the savepoint machinery only — no relation references.)

### ka_gochara_sweep

| relation | op | file:line | granted? | RLS? |
|---|---|---|---|---|
| brahma_event_ontology | S | sweep.py:151 | yes | off |
| kala_gochara_windows | D | writer.py:337, 554 | yes | off |
| kala_gochara_windows | S | writer.py:506 | yes | off |
| kala_gochara_windows | I | writer.py:710 | yes | off |
| build_substep_progress | D | writer.py:342 | yes | off |
| build_substep_progress | S | writer.py:651 | yes | off |
| build_substep_progress | I + U | writer.py:666 (ON CONFLICT DO UPDATE) | yes / yes | off |
| gochara_resonance_map | S | writer.py:563 | yes | off |
| public.charts | S | writer.py:608 | yes | **ON** — see RLS chase below |
| chart_dashas | S | writer.py:626 | yes | off |

### gochara_kernel (all modules)

Only `ledger.py` executes SQL — already covered in v1.0 (all privileges
granted). `__init__.py`, `arcs.py`, `contacts.py`, `convention.py`,
`coverage.py`, `episodes.py`, `fingerprint.py`, `ids.py`, `knots.py`,
`legacy_semantics.py`, `lifecycle.py`, `overlays.py`, `peaks.py` carry no SQL
(verified module by module). `record_store` does not exist.

## RLS chase — public.charts

`charts` has `relrowsecurity = true` (the only RLS relation in the whole audit).
Its three policies (`chart_service_policy`, `chart_owner_policy`,
`chart_grant_policy`, all PERMISSIVE, role `{public}`) reference exactly one
other relation: `chart_grants` (in `chart_grant_policy`'s qual). Checks:
`chart_grants` exists; builder SELECT on `chart_grants` = **granted**;
`chart_grants` itself has RLS **off**. Additionally `charts` is owned by
`amjis_app` with `relforcerowsecurity = false`, and `chart_service_policy`
passes when `app.principal_id` is unset — the build job sets no such GUC, and
the builder holds plain SELECT regardless. **No gap.**

`build_substep_progress` has no owned identity/serial sequence
(`pg_get_serial_sequence` over identity columns: none), so its INSERT/upsert
needs no sequence USAGE.

## v1.1 totals

- New relations checked: 3 (`l1_sarvatobhadra_vedha`, `build_substep_progress`,
  `charts`) + `chart_grants` via the RLS chase.
- **New gaps: 0.** The running total stays **1** (`bg_transit_av_gates` SELECT
  — which PART B confirmed is also read by `gochara_grammar/primitives.py:949`;
  C3 PART A's migration 1225 closes it).
- NOT PRESENT: 1 — `l1_sarvatobhadra_vedha` (gochara_grammar/sarvatobhadra.py
  fallback-pair reads). Note: `sarvatobhadra.py` reads it through
  `_vedha_pairs_from_db`, whose callers treat a missing table as the
  no-DB-fallback path; flagged here so the migration that eventually creates it
  also grants the builder SELECT.

---

# v1.2 extension (TASK C4) — FUNCTION EXECUTE privileges on the writer-DML path

Codex found the class v1.0/v1.1 missed: **function EXECUTE**. Production
baseline (steward-verified, re-verified here): `data_plane_builder` holds
EXECUTE on **0 of 42** `public.ka_gochara*` user functions — all owned by
`amjis_app`, all SECURITY INVOKER; the deployment bootstrap revokes PUBLIC
execute.

**Method.** For every table the gochara-family writers INSERT/UPDATE/DELETE
(the v1.1 list — `gochara_resonance_map`, `kala_moorti_nirnaya`,
`kala_vedha_gochara`, `bg_gochara_arcs`, `kala_gochara_windows_v2`,
`kala_gochara_v2_build_state`, `kala_gochara_windows`,
`kala_gochara_convention`, `kala_gochara_publication`, `kala_gochara_contacts`,
`kala_gochara_coverage`, `build_substep_progress` — plus the 18 contract tables
of migrations 1153–1157, `ka_gochara_*`), SELECT-only probes listed every
function reached by that DML: CHECK constraints (`pg_get_constraintdef` →
function references), column DEFAULT expressions, row triggers (`pg_trigger` →
`tgfoid`), and one level of functions named in those functions' `prosrc`
(callees of callees **not traced** — noted where relevant). For each function:
owner, `prosecdef`, `has_function_privilege('data_plane_builder', oid,
'EXECUTE')`. All 30 tables exist in production (MISSING: none). No function
reference failed to resolve.

**Interpretation rule (per the task, stated for the reader):** a trigger
function itself does NOT need EXECUTE by the DML role — but functions called
from CHECK constraints, from column defaults, and from inside SECURITY INVOKER
functions DO. Every trigger function below is INVOKER, so their callees need
EXECUTE.

## Functions that NEED builder EXECUTE and do NOT have it — 22 gaps

All: owner `amjis_app`, SECURITY INVOKER, `EXECUTE = false` for
`data_plane_builder`.

| function | reached via | from tables |
|---|---|---|
| ka_gochara_finite_nonneg_ok(double) | check | ka_gochara_contact, ka_gochara_eval_window, ka_gochara_relationship_record, ka_gochara_sky_event |
| ka_gochara_finite_ok(double) | check | ka_gochara_eval_window, ka_gochara_factor, ka_gochara_relationship_record |
| ka_gochara_frame_ok(text,text) | check | ka_gochara_relationship_record, ka_gochara_rule_path |
| ka_gochara_generation_governed(text) | check + callee | ka_gochara_contact, ka_gochara_eval_window, ka_gochara_eval_window_record, ka_gochara_generation_seal, ka_gochara_record_prerequisite, ka_gochara_relationship_record |
| ka_gochara_horizon_finite_ok(tstzrange) | check + callee | ka_gochara_eval_window, ka_gochara_relationship_record |
| ka_gochara_intervals_ok(tstzrange[]) | check + callee | ka_gochara_relationship_record |
| ka_gochara_named_operands_ok(jsonb) | check | ka_gochara_factor, ka_gochara_predicate |
| ka_gochara_object_selector_consistent_ok(jsonb,jsonb,jsonb) | check | ka_gochara_rule_path |
| ka_gochara_precision_ok(jsonb) | check + callee | ka_gochara_relationship_record |
| ka_gochara_string_array_ok(jsonb) | check + callee | ka_gochara_factor, ka_gochara_relationship_record, ka_gochara_rule_path |
| ka_gochara_text_array_ok(text[],integer) | check | ka_gochara_av_polarity_declaration, ka_gochara_eval_window |
| ka_gochara_vocab_array_ok(jsonb,text[]) | check | ka_gochara_rule_path |
| ka_gochara_generation_is_sealed(uuid,text) | callee | ka_gochara_contact, ka_gochara_eval_window, ka_gochara_eval_window_record, ka_gochara_record_prerequisite, ka_gochara_relationship_record |
| ka_gochara_lock_chart(uuid) | callee | all 12 chart-scoped contract tables (av_polarity_declaration, contact, contact_identity, convention_bridge, eval_window, eval_window_record, generation_seal, physical_object, record_prerequisite, relationship_record, sky_convention, sky_event) |
| ka_gochara_lock_global() | callee | ka_gochara_factor, ka_gochara_predicate, ka_gochara_rule_path, ka_gochara_rule_path_prerequisite, ka_gochara_rule_path_seal, ka_gochara_rule_path_soft_factor |
| ka_gochara_lock_global_shared() | callee | ka_gochara_eval_window, ka_gochara_relationship_record |
| ka_gochara_coverage_drift(uuid,text) | callee | ka_gochara_generation_seal |
| ka_gochara_coverage_facts(text,tstzrange,text[]) | callee | ka_gochara_eval_window, ka_gochara_relationship_record |
| ka_gochara_membership_violation(jsonb,uuid,text,jsonb,tstzrange[]) | callee | ka_gochara_eval_window_record |
| ka_gochara_membership_violations(uuid,text) | callee | ka_gochara_generation_seal |
| ka_gochara_object_selector_ok(jsonb) | callee | ka_gochara_rule_path |
| ka_gochara_selector_token_ok(text) | callee | ka_gochara_factor, ka_gochara_predicate |

(Generation-lock callees' own callees were not traced beyond one level; if
`ka_gochara_lock_chart`/`ka_gochara_generation_is_sealed` call further user
functions, those need EXECUTE too — Stream B's grant migration should prefer a
complete `ka_gochara%` function grants over this checklist alone.)

## Trigger functions — reached directly, do NOT need EXECUTE (20)

`ka_gochara_chart_statement_lock`, `ka_gochara_chart_write_guard`,
`ka_gochara_contact_guard`, `ka_gochara_contact_identity_supersede_guard`,
`ka_gochara_contact_propagate_precision`, `ka_gochara_generation_seal_guard`,
`ka_gochara_global_write_guard`, `ka_gochara_insert_only`,
`ka_gochara_membership_guard`, `ka_gochara_record_coverage_guard`,
`ka_gochara_record_finalize_check`, `ka_gochara_refuse_truncate`,
`ka_gochara_require_sealed_rule_path`, `ka_gochara_sky_event_guard`,
`ka_gochara_sky_event_supersede_guard`, `ka_gochara_substrate_chart_lock`,
`ka_gochara_window_coverage_guard`, `ka_gochara_window_membership_guard`,
`kala_gochara_convention_no_mutation`, `kala_gochara_generation_guard`.

(Also owner `amjis_app`, INVOKER, EXECUTE=false — no gap per the
interpretation rule, but listed because any DML fires them.)

## Non-gochara functions reached (no gap)

- `public.gen_random_uuid()` — owner `postgres`, INVOKER, builder EXECUTE =
  **true** (used in defaults, e.g. manifest ids).
- pg_catalog builtins (`now()`, `nextval(regclass)`, `lower`, `upper`,
  `isempty`, `lower_inf`, `upper_inf`, `jsonb_*`, `array_length`,
  `array_position`, `cardinality`, `btrim`, `count`, `current_setting`,
  `set_config`, `to_jsonb`, `to_regprocedure`, `unnest`, `version`, `format`):
  EXECUTE to PUBLIC by default — no gap.

## Sequence addendum to v1.0 (correction of method, not of result)

v1.0's `pg_get_serial_sequence` probe found no owned sequences on INSERT
targets. C4's default-expression scan shows five INSERT targets DO have
`nextval` column defaults — the sequences exist but are not OWNED BY the
columns, which is why the ownership-based probe missed them. Direct
`has_sequence_privilege` checks: **USAGE granted** on all five
(`gochara_resonance_map_id_seq`, `kala_gochara_windows_id_seq`,
`kala_gochara_windows_v2_id_seq`, `kala_moorti_nirnaya_id_seq`,
`kala_vedha_gochara_id_seq`). No gap; the v1.0 conclusion stands, now for the
right reason.

## v1.2 GAPS

**22 function-EXECUTE gaps** (the table above), all on the 1153–1157 contract
tables' DML path: 12 reached via CHECK constraints, 15 via callees of INVOKER
trigger functions (overlap 5). No function gaps on the v1.0/v1.1 writer-owned
tables (their checks/defaults/triggers reference builtins only, plus the two
trigger-only `kala_gochara_*` guards). No migration written — Stream B owns
the grant; this section is its checklist.

## Running totals (v1.0 + v1.1 + v1.2)

- Table-privilege gaps: 1 (`bg_transit_av_gates` SELECT — C3-A migration 1225,
  PR #2879).
- Function-EXECUTE gaps: 22.
- Sequence gaps: 0. NOT PRESENT relations: 1 (`l1_sarvatobhadra_vedha`).
