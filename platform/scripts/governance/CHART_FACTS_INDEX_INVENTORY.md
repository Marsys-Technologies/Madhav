# Chart Facts Index Inventory
Generated: 2026-05-29
Session: B-10 — reflects all B-series migrations (124–132)

## chart_facts indexes

| Index name | Columns | Type | Unique | Partial / Notes |
|---|---|---|---|---|
| `chart_facts_pkey` | `(id)` | btree | YES (PK) | — |
| `chart_facts_category_divchart_idx` | `(category, divisional_chart)` | btree | no | `WHERE is_stale = false` — hot-path read for non-stale facts |
| `chart_facts_source_section_idx` | `(source_section)` | btree | no | `WHERE is_stale = false` |
| `chart_facts_value_json_gin` | `(value_json)` | gin | no | GIN for JSONB containment queries |
| `idx_chart_facts_category` | `(category, divisional_chart)` | btree | no | General lookup, no stale filter |
| `idx_chart_facts_chart_ayan` | `(chart_id, ayanamsha_id)` | btree | no | Multi-ayanamsha per-chart lookup — **B-series new** |
| `idx_chart_facts_fact_id` | `(fact_id)` | btree | no | SHA-256 `fact_id` point lookup — **B-series new** |
| `uq_chart_facts_engine` | `(fact_id, chart_id, ayanamsha_id)` | btree | YES | `WHERE chart_id IS NOT NULL` — engine-gen dedup |
| `uq_chart_facts_legacy` | `(fact_id)` | btree | YES | `WHERE chart_id IS NULL` — pre-chart_id backwards compat |

### Foreign-key constraints on chart_facts
| Constraint | Column | References |
|---|---|---|
| `chart_facts_build_id_fkey` | `build_id` | `build_manifests(build_id)` |
| `chart_facts_chart_id_fkey` | `chart_id` | `charts(chart_id)` |

### Trigger on chart_facts
| Trigger | Timing | Function |
|---|---|---|
| `trg_chart_facts_audit` | AFTER INSERT OR DELETE OR UPDATE (per row) | `fn_chart_facts_audit()` → writes to `chart_facts_history` |

---

## New Build Orchestrator Tables (migrations 124–132)

### builds
Primary key: `build_id` (uuid)

| Index | Columns | Notes |
|---|---|---|
| `builds_pkey` | `(build_id)` | PK |
| `builds_chart_idx` | `(chart_id, queued_at DESC)` | per-chart build history |
| `builds_status_idx` | `(status)` | `WHERE status IN ('queued','running','cancelling')` — active-build filter |

Check constraints: `builds_status_check` (queued/running/complete/failed/cancelled/cancelling), `builds_triggered_by_role_check` (super_admin/guest)

---

### build_steps
Primary key: `step_id` (uuid)

| Index | Columns | Notes |
|---|---|---|
| `build_steps_pkey` | `(step_id)` | PK |
| `build_steps_build_idx` | `(build_id, ayanamsha_id)` | per-build per-ayanamsha step lookup |
| `build_steps_category_idx` | `(category)` | category-based step query |
| `build_steps_status_idx` | `(status)` | `WHERE status IN ('queued','running')` — active steps |

Check constraint: `build_steps_status_check` (queued/running/complete/failed/skipped)

---

### build_notifications
Primary key: `notif_id` (uuid)

| Index | Columns | Notes |
|---|---|---|
| `build_notifications_pkey` | `(notif_id)` | PK |
| `build_notif_build_idx` | `(build_id, created_at DESC)` | SSE event stream ordered by time |
| `build_notif_undelivered_idx` | `(build_id)` | `WHERE delivered_at IS NULL` — pending delivery |

Check constraint: `build_notifications_event_type_check` (8 event types: build_queued/started/complete/failed/cancelled; step_started/complete/failed)

---

### engine_versions
Primary key: `version_id` (uuid)

| Index | Columns | Notes |
|---|---|---|
| `engine_versions_pkey` | `(version_id)` | PK |
| `engine_versions_engine_name_version_str_key` | `(engine_name, version_str)` | UNIQUE — dedup engine registry |

---

### build_engine_versions  *(junction table)*
Primary key: `(build_id, version_id)` composite

| Index | Columns | Notes |
|---|---|---|
| `build_engine_versions_pkey` | `(build_id, version_id)` | PK |
| `bev_version_idx` | `(version_id)` | reverse lookup: which builds used an engine version |

---

### chart_facts_history  *(audit trail)*
Primary key: `history_id` (uuid)

| Index | Columns | Notes |
|---|---|---|
| `chart_facts_history_pkey` | `(history_id)` | PK |
| `chart_facts_hist_fact_idx` | `(fact_id, changed_at DESC)` | per-fact change timeline |
| `chart_facts_hist_chart_ayan_idx` | `(chart_id, ayanamsha_id, changed_at DESC)` | `WHERE chart_id IS NOT NULL` — per-chart-ayanamsha audit |
| `chart_facts_hist_change_type_idx` | `(change_type, changed_at DESC)` | filter by insert/update/delete |

Check constraint: `chart_facts_history_change_type_check` (insert/update/delete)
Populated by: `trg_chart_facts_audit` trigger on `chart_facts`

---

### chart_facts_supersedence
Primary key: `supersedence_id` (uuid)

| Index | Columns | Notes |
|---|---|---|
| `chart_facts_supersedence_pkey` | `(supersedence_id)` | PK |
| `cfs_chart_ayan_idx` | `(chart_id, ayanamsha_id, superseded_at DESC)` | per-chart-ayanamsha supersedence history |
| `cfs_superseded_build_idx` | `(superseded_build_id)` | reverse lookup by old build |
| `cfs_current_build_idx` | `(current_build_id)` | reverse lookup by new build |

Check constraint: `cfs_different_builds` (superseded_build_id ≠ current_build_id)

---

### chart_ayanamsha_reports
Primary key: `report_id` (uuid)

| Index | Columns | Notes |
|---|---|---|
| `chart_ayanamsha_reports_pkey` | `(report_id)` | PK |
| `car_unique_pair` | `(chart_id, build_id, ayanamsha_id_1, ayanamsha_id_2)` | UNIQUE — one report per chart×build×ayanamsha-pair |
| `car_chart_build_idx` | `(chart_id, build_id)` | per-chart-build lookup |
| `car_divergence_idx` | `(chart_id, divergence_score DESC)` | `WHERE divergence_score IS NOT NULL` — rank by divergence |
| `car_report_json_gin` | `(report_json)` | GIN for JSONB queries |

Check constraint: `car_different_ayanamshas` (ayanamsha_id_1 ≠ ayanamsha_id_2)

---

### chart_documents
Primary key: `document_id` (uuid)

| Index | Columns | Notes |
|---|---|---|
| `chart_documents_pkey` | `(document_id)` | PK |
| `chart_docs_unique` | `(chart_id, ayanamsha_id, document_type, build_id)` | UNIQUE — one doc per chart×ayanamsha×type×build |
| `chart_docs_chart_ayan_idx` | `(chart_id, ayanamsha_id, document_type)` | primary read path |
| `chart_docs_build_idx` | `(build_id)` | all docs for a build |
| `chart_docs_embedding_pending_idx` | `(chart_id, ayanamsha_id)` | `WHERE is_embedded = false` — embedding backfill queue |
| `chart_docs_content_json_gin` | `(content_json)` | `WHERE content_json IS NOT NULL` — GIN for JSONB |

Check constraint: `chart_documents_document_type_check` (forensic_render/ucn_digest/msr_export/cdlm_export/cgm_export/rm_export/cross_ayanamsha_report)

---

### ayanamsha_registry
Primary key: `ayanamsha_id` (text)

| Index | Columns | Notes |
|---|---|---|
| `ayanamsha_registry_pkey` | `(ayanamsha_id)` | PK |
| `ayan_reg_canonical_idx` | `(is_canonical)` | `WHERE is_canonical = true` — list canonical ayanamshas |

Seeded ayanamshas (expected): lahiri, true_chitra, kp, raman, surya_siddhanta (per `builds.ayanamshas` default)

---

## Summary

| Table | PK type | Index count | Key new column(s) |
|---|---|---|---|
| `chart_facts` | uuid | 9 | `ayanamsha_id`, `engine_version`, `computed_at_iso`, `chart_id`, `fact_id` (sha256) |
| `builds` | uuid | 3 | `ayanamshas` (jsonb), `engine_version`, `status` |
| `build_steps` | uuid | 4 | `ayanamsha_id`, `category`, `row_count`, `duration_ms` |
| `build_notifications` | uuid | 3 | `event_type`, `payload` (jsonb), `subscriber_id` |
| `engine_versions` | uuid | 2 | `engine_name`, `version_str`, `git_sha`, `swisseph_ver` |
| `build_engine_versions` | composite | 2 | junction: `builds` × `engine_versions` |
| `chart_facts_history` | uuid | 4 | `change_type`, `old_value`/`new_value` (jsonb) |
| `chart_facts_supersedence` | uuid | 4 | `superseded_build_id`, `current_build_id`, `reason` |
| `chart_ayanamsha_reports` | uuid | 5 | `divergence_score`, `max_position_delta_deg`, `report_json` |
| `chart_documents` | uuid | 6 | `document_type`, `content_md`, `content_json`, `is_embedded` |
| `ayanamsha_registry` | text | 2 | `formula_type`, `derivative_per_tropical_year`, `is_canonical` |
