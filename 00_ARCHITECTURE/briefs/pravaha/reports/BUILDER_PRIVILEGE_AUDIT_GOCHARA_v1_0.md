---
artifact: BUILDER_PRIVILEGE_AUDIT_GOCHARA
version: "1.0"
status: CURRENT
date: 2026-10-02
author: Stream C (Kimi), TASK C2 (steward M20261001T221019-7dbe)
writes: "NONE — every production query below was a SELECT through the read-only credential (amjis_app, default_transaction_read_only=on)"
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

None — all 24 relations referenced by the in-scope SQL exist in production.

## Out-of-scope note

The steward's scope excluded the helper services the w2g ka_gochara writer
imports for its read path (`services/gochara_grammar/*`,
`services/gochara_intensity/*`, `services/ka_gochara_sweep/*` — see
`pipeline/orchestrator/writers/ka_gochara.py:102-112` and
`services/w2g/materialize.py:58-68`). Their SQL was not audited here; if the
steward wants the full transitive read path covered, that is a follow-up task.
