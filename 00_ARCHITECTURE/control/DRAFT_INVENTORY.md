# NIRMĀṆA M0-T7 — DRAFT-but-served inventory (Phase 0.8b)

**Generated:** 2026-08-23T04:47:24.526215+00:00  
**Generators:** `00_ARCHITECTURE/control/draft_reachability.py` (facts) · `render_m0t7.py` (this page)  
**Git:** `campaign/nirmana-autonomous` @ `11e714838b1c21202fcae32d205414f9eced718d`  
**Database access:** READ-ONLY (SELECT only, autocommit, statement_timeout 60s)  
**Credential handling:** DATABASE_URL read from platform/.env.local; never emitted  
**Native chart:** `482012f1-710e-4a25-994a-93821f5871aa`  
**Status:** observations only. This document issues no verdict, decides no disposition and
certifies nothing. Catalogue disposition is charter power **G1 (ADHIKĀRIN)**; this is the
evidence it rests on (I16 / charter H7).

## 0 — The four facts, kept apart

The plan's exit criterion says "DRAFT-but-served". *Served* has four different readings and
they do not agree with each other. Each asset below is reported against all four, separately.

| # | Fact | What produced it | What it does NOT establish |
|---|---|---|---|
| **F1** | `registry_active` — the registry claims the asset is active | `asset_registry.is_active` (live DB) | Nothing about whether any code reads its output. It is the registry's claim about itself. |
| **F2** | `rows_exist` — the asset's target table(s) hold rows | `SELECT count(*)` on each table, plus the asset's own `count_sql` run for the native chart | That the rows are correct, current, or built by this asset rather than a co-writer of the same table. |
| **F3** | `surface_references` — a non-test serving-side source file issues a SQL read of one of those tables | regex over comment-stripped source in `platform/src`, `platform-mcp/src`, the FastAPI sidecar; occurrence classified `sql_read` / `sql_write` / `mention` by its immediately preceding SQL context | That the reading file is reachable, or that the read is on a live code path. Dynamic SQL (`FROM ${table}`) is flagged `dynamic_sql_candidate`, not counted as a confirmed read. |
| **F4** | `caller_reachable` — that file sits in the transitive import closure of a caller-facing entrypoint, and (for a retrieval capability) its descriptor is passed to `registerCapability()` from a module in that closure | TS import graph over 2523 files from 241 entrypoint roots (`app/**/route.ts`, `page.tsx`, `platform-mcp/src/server.ts`, `instrumentation.ts`) → 1353 reachable files; Python import graph over 1033 sidecar files from `main.py` → 92 reachable | **That a live HTTP call succeeds.** It is static reachability plus registration. It does not evaluate per-profile MCP allowlists, auth gates, feature flags, or runtime errors. A capability can be registered and reachable and still return an error to every caller. |

Reading them together is what the exit criterion actually needs: F1 alone is the registry
talking about itself; F1+F2 is "built"; F1+F2+F3 is "wired"; all four is "wired and callable".

## 1 — Headline counts (re-derived, not inherited)

- `asset_registry` rows: **128**
- `catalog_status = 'DRAFT'`: **47**
- **F1** registry says active: **47 / 47**
- **F2** rows exist: **39** yes · 4 no (all-zero tables) · 4 no table declared
- **F3** a serving surface references the table: **39** yes · 4 no · 4 no table declared
- **F4** that surface is reachable from a caller entrypoint: **38** yes · 5 no · 4 UNKNOWN (no table to trace)

The four UNKNOWNs are the four `asset_kind = service` DRAFT assets that declare no
`target_table` and no `count_sql` (`ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`,
`ka_tulana`). There is no table for the table-tracing method to follow, and they carry no
`provides_apis` and no `health_probe` either — so the F3/F4 method cannot establish their
reachability in **either** direction. They are UNKNOWN, not "unserved".

**But they are not evidence-free.** All four carry a populated `selftest_detail` written by a
real self-test in their own writer (`services/ka_dasha_kala/writer.py`,
`services/ka_tulana/writer.py`, `writers/ka_graha_sancara.py`, and the FORENSIC-anchored
muhurta probe) — so their `service_health` is an EARNED signal in the §N.8 sense, with a
detector that demonstrably can and does return a non-green verdict: `ka_graha_sancara` reads
`unhealthy` with the failing check recorded verbatim. Each of the four packets below quotes
its `selftest_detail`. That establishes the service *runs and self-checks*; it still does not
establish that any caller reaches it.

## 2 — The matrix

| asset_id | layer | kind | F1 active | F2 rows | F3 refs | F4 reachable | native rows | reachable capabilities |
|---|---|---|:--:|:--:|:--:|:--:|--:|---|
| `bg_vidhi_floors` | brahmagyan | data | Y | Y | · | · | 286 | — |
| `bg_vidhi_primitives` | brahmagyan | data | Y | Y | · | · | 52 | — |
| `bo_arudha` | bodha | data | Y | Y | Y | Y | 25 | `call_priority_ranking`, `judgment_query`, `query_domain_reading`, `query_signals`, `query_temporal_activation`, `query_ucd`, `traverse_chart_graph`, `yoga_activation_by_dasha` |
| `bo_cdlm_summary` | bodha | data | Y | Y | Y | Y | 5 | `query_cdlm_summary` |
| `bo_chart_gestalt` | bodha | data | Y | Y | Y | Y | 5 | `query_chart_gestalt` |
| `bo_laksana_rerank` | bodha | data | Y | Y | Y | Y | 10824 | `call_priority_ranking`, `judgment_query`, `query_domain_reading`, `query_signals`, `query_temporal_activation`, `query_ucd`, `traverse_chart_graph`, `yoga_activation_by_dasha` |
| `bo_nakshatra_semantic` | bodha | data | Y | Y | Y | Y | 45 | `call_priority_ranking`, `judgment_query`, `query_domain_reading`, `query_signals`, `query_temporal_activation`, `query_ucd`, `traverse_chart_graph`, `yoga_activation_by_dasha` |
| `bo_special_lagna` | bodha | data | Y | Y | Y | Y | 20 | `call_priority_ranking`, `judgment_query`, `query_domain_reading`, `query_signals`, `query_temporal_activation`, `query_ucd`, `traverse_chart_graph`, `yoga_activation_by_dasha` |
| `bo_sudarshana` | bodha | data | Y | Y | Y | Y | 45 | `call_priority_ranking`, `judgment_query`, `query_domain_reading`, `query_signals`, `query_temporal_activation`, `query_ucd`, `traverse_chart_graph`, `yoga_activation_by_dasha` |
| `bo_vargottama_dhana` | bodha | data | Y | Y | Y | Y | 14 | `call_priority_ranking`, `judgment_query`, `query_domain_reading`, `query_signals`, `query_temporal_activation`, `query_ucd`, `traverse_chart_graph`, `yoga_activation_by_dasha` |
| `bo_yantra_mechanism` | bodha | data | Y | Y | Y | Y | 615 | `judgment_query`, `query_mechanisms` |
| `ga_vichara` | ganita | data | Y | Y | Y | Y | 8249 | `get_dasha_lord_capability`, `get_vichara`, `query_remedies` |
| `ka_bhavishya_lekha` | kala | artifact | Y | Y | Y | Y | 100 | `query_projections`, `query_temporal_activation` |
| `ka_dasha_kala` | kala | service | Y | — | — | ? | — | — |
| `ka_graha_sancara` | kala | service | Y | — | — | ? | — | — |
| `ka_jivana_parva` | kala | artifact | Y | Y | Y | Y | 100 | `query_life_arc` |
| `ka_kala_darshana` | kala | artifact | Y | Y | Y | Y | 750 | `query_temporal_view` |
| `ka_kalasutra` | kala | artifact | Y | Y | Y | Y | 335403 | `call_priority_ranking`, `query_temporal_activation`, `yoga_activation_by_dasha` |
| `ka_muhurta_seva` | kala | service | Y | — | — | ? | — | — |
| `ka_sangam` | kala | artifact | Y | Y | Y | Y | 14868 | `query_convergence_windows` |
| `ka_tulana` | kala | service | Y | — | — | ? | — | — |
| `ka_vighnakara` | kala | artifact | Y | Y | Y | Y | 536 | `query_obstruction_periods` |
| `ka_yojaka` | kala | artifact | Y | Y | Y | Y | 50104 | `query_temporal_activation` |
| `lel_events` | mimamsa | data | Y | Y | Y | Y | 64 | `lel_intake_checklist`, `lel_query`, `mechanism_retrodiction_get`, `prediction_lifecycle_sweep` |
| `mi_abhilekha` | mimamsa | service | Y | 0 | Y | Y | 0 | `query_journal` |
| `mi_adhilepa` | mimamsa | data | Y | Y | Y | Y | 112270 | `query_load_bearing` |
| `mi_bhara` | mimamsa | data | Y | Y | Y | Y | 7 | — |
| `mi_bhavisya` | mimamsa | data | Y | Y | Y | Y | 278 | `prediction_lifecycle_sweep`, `query_calibration`, `query_manifestation_sets`, `query_predictions` |
| `mi_darshana` | mimamsa | data | Y | Y | Y | Y | 115 | `query_insight_embeddings`, `query_insights` |
| `mi_gunanaka` | mimamsa | data | Y | Y | Y | Y | 13 | `query_calibration` |
| `mi_jivanaghatana` | mimamsa | data | Y | Y | · | · | 64 | — |
| `mi_kula` | mimamsa | data | Y | Y | Y | Y | 15 | `query_signal_families` |
| `mi_pariksha` | mimamsa | data | Y | Y | Y | Y | 1664 | `query_attribution`, `query_calibration`, `query_mimamsa_discoveries` |
| `mi_pramana` | mimamsa | data | Y | Y | Y | Y | 63 | `query_calibration`, `query_insights` |
| `mi_sambandha` | mimamsa | data | Y | Y | Y | Y | 24 | `query_manifestation_grammar`, `query_manifestation_sets` |
| `mi_sankalpa` | mimamsa | data | Y | 0 | Y | Y | 0 | — |
| `mi_seva` | mimamsa | service | Y | 0 | · | · | 0 | — |
| `mi_vistara` | mimamsa | data | Y | 0 | Y | · | 0 | — |
| `ph_muhurta` | phala | artifact | Y | Y | Y | Y | 134 | `query_auspicious_windows` |
| `ph_nimitta` | phala | artifact | Y | Y | Y | Y | 139 | `query_predictive_anchors`, `query_remedy_program` |
| `ph_phaladesa` | phala | artifact | Y | Y | Y | Y | 13 | `query_domain_result` |
| `ph_pramana` | phala | artifact | Y | Y | Y | Y | 139 | `query_falsifiers` |
| `ph_pratikara` | phala | artifact | Y | Y | Y | Y | 536 | `query_remedy_program` |
| `ph_rectification` | phala | artifact | Y | Y | Y | Y | 186 | `query_rectification` |
| `ph_sankrama` | phala | artifact | Y | Y | Y | Y | 2510 | `query_spillover_cascades` |
| `ph_sodhana` | phala | artifact | Y | Y | Y | Y | 97 | `query_anomaly_flags` |
| `ph_suddha_sodhana` | phala | artifact | Y | Y | Y | Y | 139 | `query_cleansed_anchors` |

`Y` = established · `·` = established absent · `?` = UNKNOWN, this method cannot tell · `—` = not applicable · `0` = table exists, zero rows

**Shared-table caveat, read before using the last column.** `bodha_msr_signals` is the declared table of more than one DRAFT asset, so those assets necessarily show the SAME capability list — the capability reads the table, not the asset. Seven DRAFT assets share `bodha_msr_signals` alone. Use each asset's own `count_sql` figure (the "native rows" column) for the asset-scoped quantity; the capability column establishes that the TABLE is served, not that this asset's rows are the ones being read.

## 3 — The DRAFT assets this method finds NOT reachable

**5** DRAFT assets are built (rows present, or table present) but no reachable
serving surface issues a SQL read against their table:

- **`bg_vidhi_floors`** — Vidhi Registry — Intent Floors. Table(s) `vidhi_floor_items`; native rows 286. No serving-side reference of any kind.
- **`bg_vidhi_primitives`** — Vidhi Registry — Primitives. Table(s) `vidhi_primitives`; native rows 52. No serving-side reference of any kind.
- **`mi_jivanaghatana`** — Life event log (held-out). Table(s) `mimamsa_event_provenance`; native rows 64. No serving-side reference of any kind. Build-side readers exist: `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py`, `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py`.
- **`mi_seva`** — Serve-time apply. Table(s) `mimamsa_preferences`; native rows 0. No serving-side reference of any kind.
- **`mi_vistara`** — Export log. Table(s) `mimamsa_export_log`; native rows 0. Only unreachable references: `platform/python-sidecar/brahmagyan/mimamsa/export_to_bigquery.py`

**4** are UNKNOWN (no table, no `provides_apis`, no `health_probe`): `ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`, `ka_tulana`.

## 4 — Per-asset evidence packets (for the G1 ruling)

Each packet states what the asset is, what it produces, whether it is served and **how that
was established**, its DAG neighbourhood, and the *factual* consequence of each of the three
dispositions. It does not recommend one. `promote to CURRENT` / `retire with a
`data_disposition`` / `reclassify as SOURCE` are ADHIKĀRIN's (G1).

> **Schema note that binds all three options.** Re-derived live this session: the
> `asset_registry_catalog_status_check` CHECK permits only `CURRENT | DRAFT | RETIRED`, and
> `asset_registry_asset_kind_check` permits only `data | service | artifact`. There is no
> `SOURCE` value in either column today, and `data_disposition` **does not exist as a column
> in the live database** — migration `590_nirmana_m0_catalogue_contract_columns.sql` (staged
> on this branch, verified NOT applied) would add it. So "retire with a `data_disposition`"
> requires 590 to be applied first, and "reclassify as SOURCE" requires a CHECK-constraint
> change that no migration in this plan names (charter P5).
>
> **CORRECTION — 2026-08-23 (M0-T32).** The `data_disposition` half of the paragraph above is
> now FALSE. Migration 590 **applied at 2026-08-23T05:36:13.833986+00:00**
> (`_migrations_applied` id 450); `data_disposition` exists live as `text` and so do `domain`,
> `rung` and `superseded_by`. The first blocker on "retire with a `data_disposition`" is
> therefore cleared — though 0 rows carry a non-NULL `data_disposition` today (read-only,
> 2026-08-23T07:25Z), and the single RETIRED asset (`ka_gochara_sweep`) is still C-08's one
> violation. **The `SOURCE` half stands and has hardened:** the CHECKs still permit only
> `CURRENT|DRAFT|RETIRED` and `data|service|artifact`, and D-21 (which granted the widening)
> was REVERSED IN FULL by D-23 — `lel_events` → SOURCE is assigned to **R5** by plan §8.4, not
> to M0. So of the two options this note called inexpressible, one is now expressible and the
> other has been deferred out of M0 entirely. Only this correction was added; the analysis
> above and the per-asset packets below are untouched. This is a mechanical fact about
> the schema, not an argument for or against any option; it is stated because two of the
> three options are not currently expressible. It independently corroborates
> `ASSET_CATALOGUE_CONTRACT_v1_0.md` §10.1.

### `bg_vidhi_floors`

**What it is.** Vidhi Registry — Intent Floors · layer `brahmagyan` (`layer_index`=None) · kind `data` · scope `global`.
> Per-intent-class acharya floor + machine band header + ordered floor items — the compiled scope_tuple->contract input (D-2 Lane V-1).

**What it produces.** `target_table` = `vidhi_floor_items`. Tables touched: `vidhi_floor_items` (exists=True, view=False, total=286, native=None).
`count_sql` for the native chart returns **286**; `target_floor` = 11.
`asset_throughput`: lit×1 (last 2026-08-02 13:50:03.732998+00:00, rows_written 77).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **no** · F4 **no**.

_No serving-side SQL read of this asset's table was found in any non-test source file._

**Depends on.** `bg_vidhi_primitives`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `bg_vidhi_primitives`. `integrity_check_sql` is **NULL** and `target_floor` is 11.
- *Retire with a `data_disposition`* — 0 reachable serving surface(s) would be reading a table whose producer is retired (none found); 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bg_vidhi_primitives`

**What it is.** Vidhi Registry — Primitives · layer `brahmagyan` (`layer_index`=None) · kind `data` · scope `global`.
> Versioned vidhi primitive atoms — definition, live-tool mapping+args, fallback face, known_gap CR pointer. Global, chart-agnostic (D-2 Lane V-1).

**What it produces.** `target_table` = `vidhi_primitives`. Tables touched: `vidhi_primitives` (exists=True, view=False, total=52, native=None).
`count_sql` for the native chart returns **52**; `target_floor` = 48.
`asset_throughput`: lit×1 (last 2026-08-02 13:50:02.693503+00:00, rows_written 37).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **no** · F4 **no**.

_No serving-side SQL read of this asset's table was found in any non-test source file._

**Depends on.** _nothing_.
**Depended on by.** `bg_vidhi_floors` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 48.
- *Retire with a `data_disposition`* — 0 reachable serving surface(s) would be reading a table whose producer is retired (none found); 1 registry dependent(s) would name a RETIRED upstream: `bg_vidhi_floors`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bo_arudha`

**What it is.** Jaimini Arudha (Perception Layer) · layer `bodha` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Arudha Lagna bhava-relation, AL conjunctions, and A2/A11 (dhana/labha arudha) tenancy — pure L2 derivation over existing ga_structural/ga_positions facts; emits arudha MSR signals

**What it produces.** `target_table` = `bodha_msr_signals`. Tables touched: `bodha_msr_signals` (exists=True, view=False, total=150150, native=50104).
`count_sql` for the native chart returns **25**; `target_floor` = 15.
`asset_throughput`: lit×3 (last 2026-08-12 16:27:33.489037+00:00, rows_written 69).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/schools/chart_data_adapter.ts` | platform_lib | yes | — | L286 `FROM bodha_msr_signals s` |
| `platform/src/lib/retrieval/grounding/resolver.ts` | platform_lib | no | — | L78 `FROM bodha_msr_signals`<br>L99 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/provenance/freshness_notes.ts` | platform_lib | yes | — | L94 `FROM bodha_msr_signals m`<br>L165 `FROM bodha_msr_signals WHERE chart_id = $1 AND ayanamsha_id = $2` |
| `platform/src/lib/retrieval/eval/harness.ts` | platform_lib | no | — | L195 `description: 'CGM graph traversal with salience filter — values from bodha_msr_signals; non-native',` |
| `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts` | platform_lib | yes | `yoga_activation_by_dasha` (marsys://tool/L-TIMING/yoga_activation_by_dasha) — registered_from_reachable=True | L950 `FROM bodha_msr_signals`<br>L1953 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts` | platform_lib | yes | `judgment_query` (marsys://tool/L-JUDGMENT/judgment_query) — registered_from_reachable=True | L1313 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | platform_lib | yes | — | L649 `SELECT count(*)::int AS c FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` | platform_lib | yes | `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True | L78 `description: 'Optional filter: only return activations for these signal_ids (from bodha_msr_signals).',`<br>L160 ``EXISTS (SELECT 1 FROM bodha_msr_signals ms WHERE ms.signal_id = kala_activation.signal_id AND $${ap++} = ANY(`<br>L185 `(SELECT ms.domains_affected_array FROM bodha_msr_signals ms` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts` | platform_lib | yes | `call_priority_ranking` (marsys://tool/L3/call_priority_ranking) — registered_from_reachable=True | L654 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts` | platform_lib | yes | `query_domain_reading` (marsys://tool/L2/query_domain_reading) — registered_from_reachable=True | L193 `FROM bodha_msr_signals`<br>L363 ``SELECT signal_id::text AS signal_id FROM bodha_msr_signals`<br>L412 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts` | platform_lib | yes | `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True | L460 ``SELECT COUNT(*)::text AS total FROM bodha_msr_signals m WHERE ${filters.join(' AND ')}`,`<br>L495 `FROM bodha_msr_signals m`<br>L503 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts` | platform_lib | yes | `traverse_chart_graph` (marsys://tool/L2/traverse_chart_graph) — registered_from_reachable=True | L945 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts` | platform_lib | yes | `query_ucd` (marsys://tool/L2/query_ucd) — registered_from_reachable=True | L305 `FROM bodha_msr_signals` |
| `platform/src/lib/pariprashna/pipeline/citation_resolver.ts` | platform_lib | yes | — | L71 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa`<br>L102 `audit_detail: `resolved from bodha_msr_signals where signal_id='${ref}' (this turn's retrieved evidence)`,` |
| `platform/src/lib/pariprashna/pipeline/persistence_stage.ts` | platform_lib | yes | — | L92 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform/src/app/api/chat/consult/route.ts` | next_api | yes | — | L22 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L1838 `"description": "Optional filter: only return activations for these signal_ids (from bodha_msr_signals).",` |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | mcp_tool | yes | — | L807 `FROM bodha_msr_signals` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2069 `'(Note: the L2 bodha_msr_signals.activation_predicted_dates_jsonb hook of the same name remains genuinely ' +`<br>L2072 `'(neither the L3 kala_activation column this join reads, nor the L2 bodha_msr_signals hook of the same name, '`<br>L2257 `response; never re-derived). NOTE: the differently-scoped bodha_msr_signals L2 hook of the \` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/bodha_writers/_idempotency.py` (`bodha_msr_signals` L[57, 67, 113]); `platform/python-sidecar/pipeline/orchestrator/writers/bo_pramana_mapa.py` (`bodha_msr_signals` L[511, 514, 529]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py` (`bodha_msr_signals` L[68]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py` (`bodha_msr_signals` L[230, 235]); `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py` (`bodha_msr_signals` L[297]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py` (`bodha_msr_signals` L[92, 97]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` (`bodha_msr_signals` L[343]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`bodha_msr_signals` L[772, 776]).

**Depends on.** `ga_positions`, `ga_structural`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 15.
- *Retire with a `data_disposition`* — 16 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/schools/chart_data_adapter.ts`, `platform/src/lib/retrieval/provenance/freshness_notes.ts`, `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`, `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`, `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts`, `platform/src/lib/pariprashna/pipeline/citation_resolver.ts`, `platform/src/lib/pariprashna/pipeline/persistence_stage.ts`, `platform/src/app/api/chat/consult/route.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`; 0 registry dependent(s) would name a RETIRED upstream; 8 other writer(s) SELECT from its table at build time: `_idempotency.py`, `bo_pramana_mapa.py`, `ka_bhavishya_lekha.py`, `mi_adhilepa.py`, `ph_phaladesa.py`, `mi_bhavisya.py`, `ka_sangam.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bo_cdlm_summary`

**What it is.** CDLM Summary · layer `bodha` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Per-chart cross-domain linkage strength summary aggregated from bodha_cdlm_cells

**What it produces.** `target_table` = `None`. Tables touched: `bodha_cdlm_chart_summary` (exists=True, view=False, total=15, native=5).
`count_sql` for the native chart returns **5**; `target_floor` = 1.
`asset_throughput`: lit×2 (last 2026-08-12 16:27:32.675234+00:00, rows_written 110); stale×1 (last 2026-07-27 11:37:38.189853+00:00, rows_written 40).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_cdlm_summary.ts` | platform_lib | yes | `query_cdlm_summary` (marsys://tool/L2/query_cdlm_summary) — registered_from_reachable=True | L35 `chart_summary:       'bodha_cdlm_chart_summary',`<br>L84 `"'chart_summary' (default) — bodha_cdlm_chart_summary, one row per ayanamsha:",` |

**Depends on.** `bo_sangati`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 1.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L2_bodha/query_cdlm_summary.ts`; 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bo_chart_gestalt`

**What it is.** Chart Gestalt · layer `bodha` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Per-chart gestalt: defining threads, central dynamics, domain verdict map, zoom spine — pointer-only, no verdicts stored

**What it produces.** `target_table` = `None`. Tables touched: `bodha_chart_gestalt` (exists=True, view=False, total=15, native=5).
`count_sql` for the native chart returns **5**; `target_floor` = 1.
`asset_throughput`: lit×2 (last 2026-08-12 23:44:26.973022+00:00, rows_written 10); stale×1 (last 2026-07-27 11:44:35.947020+00:00, rows_written 5).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/synthesis/instrument.ts` | platform_lib | yes | — | L88 `disclosures.push('bodha_chart_gestalt returned no row for this chart/ayanamsha — orientation stage thin.')` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_chart_gestalt.ts` | platform_lib | yes | `query_chart_gestalt` (marsys://tool/L2/query_chart_gestalt) — registered_from_reachable=True; `query_chart_gestalt` (marsys://tool/L2/query_chart_gestalt) — registered_from_reachable=True; `query_chart_gestalt` (marsys://tool/L2/query_chart_gestalt) — registered_from_reachable=True | L24 `'Retrieve the whole-chart gestalt digest from bodha_chart_gestalt — one row per',`<br>L74 `FROM bodha_chart_gestalt`<br>L82 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_chart_gestalt WHERE ${where}`, params),` |

**Depends on.** `bo_anveshana`, `bo_bimba`, `bo_cgm_paths`, `bo_laksana`, `bo_sangati`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 1.
- *Retire with a `data_disposition`* — 2 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/synthesis/instrument.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_chart_gestalt.ts`; 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bo_laksana_rerank`

**What it is.** Lakṣaṇa Re-rank (post-CGM) · layer `bodha` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Post-CGM structural re-rank pass: writes real CGM centrality (pagerank/eigenvector/betweenness/harmonic) onto each MSR signal's graph_node_strength_contribution_jsonb hook column, closing the CR-84 dead link. UPDATE-only, never touches row ownership.

**What it produces.** `target_table` = `bodha_msr_signals`. Tables touched: `bodha_msr_signals` (exists=True, view=False, total=150150, native=50104).
`count_sql` for the native chart returns **10824**; `target_floor` = 1.
`asset_throughput`: lit×2 (last 2026-08-12 16:47:24.459323+00:00, rows_written 21701); stale×1 (last 2026-07-27 11:37:34.932365+00:00, rows_written 10951).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/schools/chart_data_adapter.ts` | platform_lib | yes | — | L286 `FROM bodha_msr_signals s` |
| `platform/src/lib/retrieval/grounding/resolver.ts` | platform_lib | no | — | L78 `FROM bodha_msr_signals`<br>L99 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/provenance/freshness_notes.ts` | platform_lib | yes | — | L94 `FROM bodha_msr_signals m`<br>L165 `FROM bodha_msr_signals WHERE chart_id = $1 AND ayanamsha_id = $2` |
| `platform/src/lib/retrieval/eval/harness.ts` | platform_lib | no | — | L195 `description: 'CGM graph traversal with salience filter — values from bodha_msr_signals; non-native',` |
| `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts` | platform_lib | yes | `yoga_activation_by_dasha` (marsys://tool/L-TIMING/yoga_activation_by_dasha) — registered_from_reachable=True | L950 `FROM bodha_msr_signals`<br>L1953 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts` | platform_lib | yes | `judgment_query` (marsys://tool/L-JUDGMENT/judgment_query) — registered_from_reachable=True | L1313 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | platform_lib | yes | — | L649 `SELECT count(*)::int AS c FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` | platform_lib | yes | `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True | L78 `description: 'Optional filter: only return activations for these signal_ids (from bodha_msr_signals).',`<br>L160 ``EXISTS (SELECT 1 FROM bodha_msr_signals ms WHERE ms.signal_id = kala_activation.signal_id AND $${ap++} = ANY(`<br>L185 `(SELECT ms.domains_affected_array FROM bodha_msr_signals ms` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts` | platform_lib | yes | `call_priority_ranking` (marsys://tool/L3/call_priority_ranking) — registered_from_reachable=True | L654 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts` | platform_lib | yes | `query_domain_reading` (marsys://tool/L2/query_domain_reading) — registered_from_reachable=True | L193 `FROM bodha_msr_signals`<br>L363 ``SELECT signal_id::text AS signal_id FROM bodha_msr_signals`<br>L412 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts` | platform_lib | yes | `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True | L460 ``SELECT COUNT(*)::text AS total FROM bodha_msr_signals m WHERE ${filters.join(' AND ')}`,`<br>L495 `FROM bodha_msr_signals m`<br>L503 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts` | platform_lib | yes | `traverse_chart_graph` (marsys://tool/L2/traverse_chart_graph) — registered_from_reachable=True | L945 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts` | platform_lib | yes | `query_ucd` (marsys://tool/L2/query_ucd) — registered_from_reachable=True | L305 `FROM bodha_msr_signals` |
| `platform/src/lib/pariprashna/pipeline/citation_resolver.ts` | platform_lib | yes | — | L71 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa`<br>L102 `audit_detail: `resolved from bodha_msr_signals where signal_id='${ref}' (this turn's retrieved evidence)`,` |
| `platform/src/lib/pariprashna/pipeline/persistence_stage.ts` | platform_lib | yes | — | L92 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform/src/app/api/chat/consult/route.ts` | next_api | yes | — | L22 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L1838 `"description": "Optional filter: only return activations for these signal_ids (from bodha_msr_signals).",` |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | mcp_tool | yes | — | L807 `FROM bodha_msr_signals` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2069 `'(Note: the L2 bodha_msr_signals.activation_predicted_dates_jsonb hook of the same name remains genuinely ' +`<br>L2072 `'(neither the L3 kala_activation column this join reads, nor the L2 bodha_msr_signals hook of the same name, '`<br>L2257 `response; never re-derived). NOTE: the differently-scoped bodha_msr_signals L2 hook of the \` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/bodha_writers/_idempotency.py` (`bodha_msr_signals` L[57, 67, 113]); `platform/python-sidecar/pipeline/orchestrator/writers/bo_pramana_mapa.py` (`bodha_msr_signals` L[511, 514, 529]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py` (`bodha_msr_signals` L[68]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py` (`bodha_msr_signals` L[230, 235]); `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py` (`bodha_msr_signals` L[297]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py` (`bodha_msr_signals` L[92, 97]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` (`bodha_msr_signals` L[343]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`bodha_msr_signals` L[772, 776]).

**Depends on.** `bo_karanajala`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 1.
- *Retire with a `data_disposition`* — 16 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/schools/chart_data_adapter.ts`, `platform/src/lib/retrieval/provenance/freshness_notes.ts`, `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`, `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`, `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts`, `platform/src/lib/pariprashna/pipeline/citation_resolver.ts`, `platform/src/lib/pariprashna/pipeline/persistence_stage.ts`, `platform/src/app/api/chat/consult/route.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`; 0 registry dependent(s) would name a RETIRED upstream; 8 other writer(s) SELECT from its table at build time: `_idempotency.py`, `bo_pramana_mapa.py`, `ka_bhavishya_lekha.py`, `mi_adhilepa.py`, `ph_phaladesa.py`, `mi_bhavisya.py`, `ka_sangam.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bo_nakshatra_semantic`

**What it is.** Nakshatra-Semantic Profile · layer `bodha` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Own-star identity, dispositor chain, tara bala, and gandanta/end-degree flagging per graha — pure L2 derivation over existing ga_positions/ga_nakshatra facts; emits nakshatra_semantic MSR signals

**What it produces.** `target_table` = `bodha_msr_signals`. Tables touched: `bodha_msr_signals` (exists=True, view=False, total=150150, native=50104).
`count_sql` for the native chart returns **45**; `target_floor` = 45.
`asset_throughput`: lit×3 (last 2026-08-12 16:27:46.833919+00:00, rows_written 135).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/schools/chart_data_adapter.ts` | platform_lib | yes | — | L286 `FROM bodha_msr_signals s` |
| `platform/src/lib/retrieval/grounding/resolver.ts` | platform_lib | no | — | L78 `FROM bodha_msr_signals`<br>L99 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/provenance/freshness_notes.ts` | platform_lib | yes | — | L94 `FROM bodha_msr_signals m`<br>L165 `FROM bodha_msr_signals WHERE chart_id = $1 AND ayanamsha_id = $2` |
| `platform/src/lib/retrieval/eval/harness.ts` | platform_lib | no | — | L195 `description: 'CGM graph traversal with salience filter — values from bodha_msr_signals; non-native',` |
| `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts` | platform_lib | yes | `yoga_activation_by_dasha` (marsys://tool/L-TIMING/yoga_activation_by_dasha) — registered_from_reachable=True | L950 `FROM bodha_msr_signals`<br>L1953 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts` | platform_lib | yes | `judgment_query` (marsys://tool/L-JUDGMENT/judgment_query) — registered_from_reachable=True | L1313 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | platform_lib | yes | — | L649 `SELECT count(*)::int AS c FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` | platform_lib | yes | `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True | L78 `description: 'Optional filter: only return activations for these signal_ids (from bodha_msr_signals).',`<br>L160 ``EXISTS (SELECT 1 FROM bodha_msr_signals ms WHERE ms.signal_id = kala_activation.signal_id AND $${ap++} = ANY(`<br>L185 `(SELECT ms.domains_affected_array FROM bodha_msr_signals ms` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts` | platform_lib | yes | `call_priority_ranking` (marsys://tool/L3/call_priority_ranking) — registered_from_reachable=True | L654 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts` | platform_lib | yes | `query_domain_reading` (marsys://tool/L2/query_domain_reading) — registered_from_reachable=True | L193 `FROM bodha_msr_signals`<br>L363 ``SELECT signal_id::text AS signal_id FROM bodha_msr_signals`<br>L412 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts` | platform_lib | yes | `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True | L460 ``SELECT COUNT(*)::text AS total FROM bodha_msr_signals m WHERE ${filters.join(' AND ')}`,`<br>L495 `FROM bodha_msr_signals m`<br>L503 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts` | platform_lib | yes | `traverse_chart_graph` (marsys://tool/L2/traverse_chart_graph) — registered_from_reachable=True | L945 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts` | platform_lib | yes | `query_ucd` (marsys://tool/L2/query_ucd) — registered_from_reachable=True | L305 `FROM bodha_msr_signals` |
| `platform/src/lib/pariprashna/pipeline/citation_resolver.ts` | platform_lib | yes | — | L71 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa`<br>L102 `audit_detail: `resolved from bodha_msr_signals where signal_id='${ref}' (this turn's retrieved evidence)`,` |
| `platform/src/lib/pariprashna/pipeline/persistence_stage.ts` | platform_lib | yes | — | L92 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform/src/app/api/chat/consult/route.ts` | next_api | yes | — | L22 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L1838 `"description": "Optional filter: only return activations for these signal_ids (from bodha_msr_signals).",` |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | mcp_tool | yes | — | L807 `FROM bodha_msr_signals` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2069 `'(Note: the L2 bodha_msr_signals.activation_predicted_dates_jsonb hook of the same name remains genuinely ' +`<br>L2072 `'(neither the L3 kala_activation column this join reads, nor the L2 bodha_msr_signals hook of the same name, '`<br>L2257 `response; never re-derived). NOTE: the differently-scoped bodha_msr_signals L2 hook of the \` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/bodha_writers/_idempotency.py` (`bodha_msr_signals` L[57, 67, 113]); `platform/python-sidecar/pipeline/orchestrator/writers/bo_pramana_mapa.py` (`bodha_msr_signals` L[511, 514, 529]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py` (`bodha_msr_signals` L[68]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py` (`bodha_msr_signals` L[230, 235]); `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py` (`bodha_msr_signals` L[297]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py` (`bodha_msr_signals` L[92, 97]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` (`bodha_msr_signals` L[343]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`bodha_msr_signals` L[772, 776]).

**Depends on.** `ga_nakshatra`, `ga_positions`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 45.
- *Retire with a `data_disposition`* — 16 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/schools/chart_data_adapter.ts`, `platform/src/lib/retrieval/provenance/freshness_notes.ts`, `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`, `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`, `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts`, `platform/src/lib/pariprashna/pipeline/citation_resolver.ts`, `platform/src/lib/pariprashna/pipeline/persistence_stage.ts`, `platform/src/app/api/chat/consult/route.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`; 0 registry dependent(s) would name a RETIRED upstream; 8 other writer(s) SELECT from its table at build time: `_idempotency.py`, `bo_pramana_mapa.py`, `ka_bhavishya_lekha.py`, `mi_adhilepa.py`, `ph_phaladesa.py`, `mi_bhavisya.py`, `ka_sangam.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bo_special_lagna`

**What it is.** Special Lagna (Indu/Sree/Ghati/Hora) · layer `bodha` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Domain-scoped corroboration from the four canonical special/upapada lagnas (Indu, Sree, Ghati, Hora) — pure L2 derivation over existing ga_sensitive facts; emits special_lagna MSR signals with per-signal domain_salience

**What it produces.** `target_table` = `bodha_msr_signals`. Tables touched: `bodha_msr_signals` (exists=True, view=False, total=150150, native=50104).
`count_sql` for the native chart returns **20**; `target_floor` = 20.
`asset_throughput`: lit×3 (last 2026-08-12 15:24:34.915920+00:00, rows_written 60).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/schools/chart_data_adapter.ts` | platform_lib | yes | — | L286 `FROM bodha_msr_signals s` |
| `platform/src/lib/retrieval/grounding/resolver.ts` | platform_lib | no | — | L78 `FROM bodha_msr_signals`<br>L99 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/provenance/freshness_notes.ts` | platform_lib | yes | — | L94 `FROM bodha_msr_signals m`<br>L165 `FROM bodha_msr_signals WHERE chart_id = $1 AND ayanamsha_id = $2` |
| `platform/src/lib/retrieval/eval/harness.ts` | platform_lib | no | — | L195 `description: 'CGM graph traversal with salience filter — values from bodha_msr_signals; non-native',` |
| `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts` | platform_lib | yes | `yoga_activation_by_dasha` (marsys://tool/L-TIMING/yoga_activation_by_dasha) — registered_from_reachable=True | L950 `FROM bodha_msr_signals`<br>L1953 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts` | platform_lib | yes | `judgment_query` (marsys://tool/L-JUDGMENT/judgment_query) — registered_from_reachable=True | L1313 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | platform_lib | yes | — | L649 `SELECT count(*)::int AS c FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` | platform_lib | yes | `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True | L78 `description: 'Optional filter: only return activations for these signal_ids (from bodha_msr_signals).',`<br>L160 ``EXISTS (SELECT 1 FROM bodha_msr_signals ms WHERE ms.signal_id = kala_activation.signal_id AND $${ap++} = ANY(`<br>L185 `(SELECT ms.domains_affected_array FROM bodha_msr_signals ms` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts` | platform_lib | yes | `call_priority_ranking` (marsys://tool/L3/call_priority_ranking) — registered_from_reachable=True | L654 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts` | platform_lib | yes | `query_domain_reading` (marsys://tool/L2/query_domain_reading) — registered_from_reachable=True | L193 `FROM bodha_msr_signals`<br>L363 ``SELECT signal_id::text AS signal_id FROM bodha_msr_signals`<br>L412 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts` | platform_lib | yes | `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True | L460 ``SELECT COUNT(*)::text AS total FROM bodha_msr_signals m WHERE ${filters.join(' AND ')}`,`<br>L495 `FROM bodha_msr_signals m`<br>L503 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts` | platform_lib | yes | `traverse_chart_graph` (marsys://tool/L2/traverse_chart_graph) — registered_from_reachable=True | L945 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts` | platform_lib | yes | `query_ucd` (marsys://tool/L2/query_ucd) — registered_from_reachable=True | L305 `FROM bodha_msr_signals` |
| `platform/src/lib/pariprashna/pipeline/citation_resolver.ts` | platform_lib | yes | — | L71 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa`<br>L102 `audit_detail: `resolved from bodha_msr_signals where signal_id='${ref}' (this turn's retrieved evidence)`,` |
| `platform/src/lib/pariprashna/pipeline/persistence_stage.ts` | platform_lib | yes | — | L92 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform/src/app/api/chat/consult/route.ts` | next_api | yes | — | L22 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L1838 `"description": "Optional filter: only return activations for these signal_ids (from bodha_msr_signals).",` |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | mcp_tool | yes | — | L807 `FROM bodha_msr_signals` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2069 `'(Note: the L2 bodha_msr_signals.activation_predicted_dates_jsonb hook of the same name remains genuinely ' +`<br>L2072 `'(neither the L3 kala_activation column this join reads, nor the L2 bodha_msr_signals hook of the same name, '`<br>L2257 `response; never re-derived). NOTE: the differently-scoped bodha_msr_signals L2 hook of the \` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/bodha_writers/_idempotency.py` (`bodha_msr_signals` L[57, 67, 113]); `platform/python-sidecar/pipeline/orchestrator/writers/bo_pramana_mapa.py` (`bodha_msr_signals` L[511, 514, 529]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py` (`bodha_msr_signals` L[68]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py` (`bodha_msr_signals` L[230, 235]); `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py` (`bodha_msr_signals` L[297]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py` (`bodha_msr_signals` L[92, 97]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` (`bodha_msr_signals` L[343]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`bodha_msr_signals` L[772, 776]).

**Depends on.** `ga_sensitive`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 20.
- *Retire with a `data_disposition`* — 16 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/schools/chart_data_adapter.ts`, `platform/src/lib/retrieval/provenance/freshness_notes.ts`, `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`, `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`, `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts`, `platform/src/lib/pariprashna/pipeline/citation_resolver.ts`, `platform/src/lib/pariprashna/pipeline/persistence_stage.ts`, `platform/src/app/api/chat/consult/route.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`; 0 registry dependent(s) would name a RETIRED upstream; 8 other writer(s) SELECT from its table at build time: `_idempotency.py`, `bo_pramana_mapa.py`, `ka_bhavishya_lekha.py`, `mi_adhilepa.py`, `ph_phaladesa.py`, `mi_bhavisya.py`, `ka_sangam.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bo_sudarshana`

**What it is.** Sudarśana Chakra · layer `bodha` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Tri-frame (Lagna/Chandra/Sūrya) house assignment per graha — pure L2 derivation over existing ga_positions facts; emits sudarshana_agreement MSR signals (confirmed-in-3-frames amplifies, contradicted flags)

**What it produces.** `target_table` = `bodha_msr_signals`. Tables touched: `bodha_msr_signals` (exists=True, view=False, total=150150, native=50104).
`count_sql` for the native chart returns **45**; `target_floor` = 45.
`asset_throughput`: lit×3 (last 2026-08-08 00:21:37.357375+00:00, rows_written 135).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/schools/chart_data_adapter.ts` | platform_lib | yes | — | L286 `FROM bodha_msr_signals s` |
| `platform/src/lib/retrieval/grounding/resolver.ts` | platform_lib | no | — | L78 `FROM bodha_msr_signals`<br>L99 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/provenance/freshness_notes.ts` | platform_lib | yes | — | L94 `FROM bodha_msr_signals m`<br>L165 `FROM bodha_msr_signals WHERE chart_id = $1 AND ayanamsha_id = $2` |
| `platform/src/lib/retrieval/eval/harness.ts` | platform_lib | no | — | L195 `description: 'CGM graph traversal with salience filter — values from bodha_msr_signals; non-native',` |
| `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts` | platform_lib | yes | `yoga_activation_by_dasha` (marsys://tool/L-TIMING/yoga_activation_by_dasha) — registered_from_reachable=True | L950 `FROM bodha_msr_signals`<br>L1953 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts` | platform_lib | yes | `judgment_query` (marsys://tool/L-JUDGMENT/judgment_query) — registered_from_reachable=True | L1313 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | platform_lib | yes | — | L649 `SELECT count(*)::int AS c FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` | platform_lib | yes | `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True | L78 `description: 'Optional filter: only return activations for these signal_ids (from bodha_msr_signals).',`<br>L160 ``EXISTS (SELECT 1 FROM bodha_msr_signals ms WHERE ms.signal_id = kala_activation.signal_id AND $${ap++} = ANY(`<br>L185 `(SELECT ms.domains_affected_array FROM bodha_msr_signals ms` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts` | platform_lib | yes | `call_priority_ranking` (marsys://tool/L3/call_priority_ranking) — registered_from_reachable=True | L654 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts` | platform_lib | yes | `query_domain_reading` (marsys://tool/L2/query_domain_reading) — registered_from_reachable=True | L193 `FROM bodha_msr_signals`<br>L363 ``SELECT signal_id::text AS signal_id FROM bodha_msr_signals`<br>L412 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts` | platform_lib | yes | `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True | L460 ``SELECT COUNT(*)::text AS total FROM bodha_msr_signals m WHERE ${filters.join(' AND ')}`,`<br>L495 `FROM bodha_msr_signals m`<br>L503 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts` | platform_lib | yes | `traverse_chart_graph` (marsys://tool/L2/traverse_chart_graph) — registered_from_reachable=True | L945 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts` | platform_lib | yes | `query_ucd` (marsys://tool/L2/query_ucd) — registered_from_reachable=True | L305 `FROM bodha_msr_signals` |
| `platform/src/lib/pariprashna/pipeline/citation_resolver.ts` | platform_lib | yes | — | L71 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa`<br>L102 `audit_detail: `resolved from bodha_msr_signals where signal_id='${ref}' (this turn's retrieved evidence)`,` |
| `platform/src/lib/pariprashna/pipeline/persistence_stage.ts` | platform_lib | yes | — | L92 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform/src/app/api/chat/consult/route.ts` | next_api | yes | — | L22 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L1838 `"description": "Optional filter: only return activations for these signal_ids (from bodha_msr_signals).",` |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | mcp_tool | yes | — | L807 `FROM bodha_msr_signals` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2069 `'(Note: the L2 bodha_msr_signals.activation_predicted_dates_jsonb hook of the same name remains genuinely ' +`<br>L2072 `'(neither the L3 kala_activation column this join reads, nor the L2 bodha_msr_signals hook of the same name, '`<br>L2257 `response; never re-derived). NOTE: the differently-scoped bodha_msr_signals L2 hook of the \` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/bodha_writers/_idempotency.py` (`bodha_msr_signals` L[57, 67, 113]); `platform/python-sidecar/pipeline/orchestrator/writers/bo_pramana_mapa.py` (`bodha_msr_signals` L[511, 514, 529]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py` (`bodha_msr_signals` L[68]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py` (`bodha_msr_signals` L[230, 235]); `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py` (`bodha_msr_signals` L[297]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py` (`bodha_msr_signals` L[92, 97]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` (`bodha_msr_signals` L[343]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`bodha_msr_signals` L[772, 776]).

**Depends on.** `ga_positions`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 45.
- *Retire with a `data_disposition`* — 16 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/schools/chart_data_adapter.ts`, `platform/src/lib/retrieval/provenance/freshness_notes.ts`, `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`, `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`, `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts`, `platform/src/lib/pariprashna/pipeline/citation_resolver.ts`, `platform/src/lib/pariprashna/pipeline/persistence_stage.ts`, `platform/src/app/api/chat/consult/route.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`; 0 registry dependent(s) would name a RETIRED upstream; 8 other writer(s) SELECT from its table at build time: `_idempotency.py`, `bo_pramana_mapa.py`, `ka_bhavishya_lekha.py`, `mi_adhilepa.py`, `ph_phaladesa.py`, `mi_bhavisya.py`, `ka_sangam.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bo_vargottama_dhana`

**What it is.** Vargottama Amplification + Dhana Axis · layer `bodha` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Cross-frame (D1/D9) vargottama confirmation and complete 2nd/11th-house (dhana/labha) tenancy analysis — pure L2 derivation over existing ga_vargas/ga_positions facts; emits vargottama_amplification + dhana_axis MSR signals

**What it produces.** `target_table` = `bodha_msr_signals`. Tables touched: `bodha_msr_signals` (exists=True, view=False, total=150150, native=50104).
`count_sql` for the native chart returns **14**; `target_floor` = 10.
`asset_throughput`: lit×3 (last 2026-08-08 00:22:51.583173+00:00, rows_written 45).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/schools/chart_data_adapter.ts` | platform_lib | yes | — | L286 `FROM bodha_msr_signals s` |
| `platform/src/lib/retrieval/grounding/resolver.ts` | platform_lib | no | — | L78 `FROM bodha_msr_signals`<br>L99 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/provenance/freshness_notes.ts` | platform_lib | yes | — | L94 `FROM bodha_msr_signals m`<br>L165 `FROM bodha_msr_signals WHERE chart_id = $1 AND ayanamsha_id = $2` |
| `platform/src/lib/retrieval/eval/harness.ts` | platform_lib | no | — | L195 `description: 'CGM graph traversal with salience filter — values from bodha_msr_signals; non-native',` |
| `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts` | platform_lib | yes | `yoga_activation_by_dasha` (marsys://tool/L-TIMING/yoga_activation_by_dasha) — registered_from_reachable=True | L950 `FROM bodha_msr_signals`<br>L1953 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts` | platform_lib | yes | `judgment_query` (marsys://tool/L-JUDGMENT/judgment_query) — registered_from_reachable=True | L1313 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | platform_lib | yes | — | L649 `SELECT count(*)::int AS c FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` | platform_lib | yes | `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True | L78 `description: 'Optional filter: only return activations for these signal_ids (from bodha_msr_signals).',`<br>L160 ``EXISTS (SELECT 1 FROM bodha_msr_signals ms WHERE ms.signal_id = kala_activation.signal_id AND $${ap++} = ANY(`<br>L185 `(SELECT ms.domains_affected_array FROM bodha_msr_signals ms` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts` | platform_lib | yes | `call_priority_ranking` (marsys://tool/L3/call_priority_ranking) — registered_from_reachable=True | L654 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts` | platform_lib | yes | `query_domain_reading` (marsys://tool/L2/query_domain_reading) — registered_from_reachable=True | L193 `FROM bodha_msr_signals`<br>L363 ``SELECT signal_id::text AS signal_id FROM bodha_msr_signals`<br>L412 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts` | platform_lib | yes | `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True; `query_signals` (marsys://tool/L2/query_signals) — registered_from_reachable=True | L460 ``SELECT COUNT(*)::text AS total FROM bodha_msr_signals m WHERE ${filters.join(' AND ')}`,`<br>L495 `FROM bodha_msr_signals m`<br>L503 `FROM bodha_msr_signals m` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts` | platform_lib | yes | `traverse_chart_graph` (marsys://tool/L2/traverse_chart_graph) — registered_from_reachable=True | L945 `FROM bodha_msr_signals` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts` | platform_lib | yes | `query_ucd` (marsys://tool/L2/query_ucd) — registered_from_reachable=True | L305 `FROM bodha_msr_signals` |
| `platform/src/lib/pariprashna/pipeline/citation_resolver.ts` | platform_lib | yes | — | L71 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa`<br>L102 `audit_detail: `resolved from bodha_msr_signals where signal_id='${ref}' (this turn's retrieved evidence)`,` |
| `platform/src/lib/pariprashna/pipeline/persistence_stage.ts` | platform_lib | yes | — | L92 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform/src/app/api/chat/consult/route.ts` | next_api | yes | — | L22 ``SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signa` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L1838 `"description": "Optional filter: only return activations for these signal_ids (from bodha_msr_signals).",` |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | mcp_tool | yes | — | L807 `FROM bodha_msr_signals` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2069 `'(Note: the L2 bodha_msr_signals.activation_predicted_dates_jsonb hook of the same name remains genuinely ' +`<br>L2072 `'(neither the L3 kala_activation column this join reads, nor the L2 bodha_msr_signals hook of the same name, '`<br>L2257 `response; never re-derived). NOTE: the differently-scoped bodha_msr_signals L2 hook of the \` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/bodha_writers/_idempotency.py` (`bodha_msr_signals` L[57, 67, 113]); `platform/python-sidecar/pipeline/orchestrator/writers/bo_pramana_mapa.py` (`bodha_msr_signals` L[511, 514, 529]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_bhavishya_lekha.py` (`bodha_msr_signals` L[68]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py` (`bodha_msr_signals` L[230, 235]); `platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py` (`bodha_msr_signals` L[297]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py` (`bodha_msr_signals` L[92, 97]); `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` (`bodha_msr_signals` L[343]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`bodha_msr_signals` L[772, 776]).

**Depends on.** `ga_positions`, `ga_vargas`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 10.
- *Retire with a `data_disposition`* — 16 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/schools/chart_data_adapter.ts`, `platform/src/lib/retrieval/provenance/freshness_notes.ts`, `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`, `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`, `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts`, `platform/src/lib/pariprashna/pipeline/citation_resolver.ts`, `platform/src/lib/pariprashna/pipeline/persistence_stage.ts`, `platform/src/app/api/chat/consult/route.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`; 0 registry dependent(s) would name a RETIRED upstream; 8 other writer(s) SELECT from its table at build time: `_idempotency.py`, `bo_pramana_mapa.py`, `ka_bhavishya_lekha.py`, `mi_adhilepa.py`, `ph_phaladesa.py`, `mi_bhavisya.py`, `ka_sangam.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `bo_yantra_mechanism`

**What it is.** Mechanism (Yantra) · layer `bodha` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Named, valenced CGM subgraph — promotes CGM motifs + dispositor/house-lordship chain-and-circuit detection into first-class mechanisms with real edge-strength provenance (DR-7) and a centrality summary (CR-24/CR-25/CR-86)

**What it produces.** `target_table` = `bodha_mechanisms`. Tables touched: `bodha_mechanisms` (exists=True, view=False, total=1868, native=615).
`count_sql` for the native chart returns **615**; `target_floor` = 1.
`asset_throughput`: lit×2 (last 2026-08-12 16:30:55.841002+00:00, rows_written 1318); stale×1 (last 2026-07-27 11:39:30.948892+00:00, rows_written 620).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts` | platform_lib | yes | `judgment_query` (marsys://tool/L-JUDGMENT/judgment_query) — registered_from_reachable=True | L1335 `FROM bodha_mechanisms` |
| `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | platform_lib | yes | — | L652 `SELECT count(*)::int AS c FROM bodha_mechanisms`<br>L656 `SELECT unnest(domains_affected_array) AS d FROM bodha_mechanisms` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_mechanisms.ts` | platform_lib | yes | `query_mechanisms` (marsys://tool/L2/query_mechanisms) — registered_from_reachable=True; `query_mechanisms` (marsys://tool/L2/query_mechanisms) — registered_from_reachable=True; `query_mechanisms` (marsys://tool/L2/query_mechanisms) — registered_from_reachable=True; `query_mechanisms` (marsys://tool/L2/query_mechanisms) — registered_from_reachable=True | L160 `'Retrieve named, valenced Mechanism (Yantra) objects from bodha_mechanisms — the',`<br>L251 `FROM bodha_mechanisms`<br>L264 `FROM bodha_mechanisms` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L502 `"description": "Retrieve named, valenced Mechanism (Yantra) objects from bodha_mechanisms — the first-class CG` |
| `platform-mcp/src/tools/registry_bridge.ts` | mcp_tool | yes | — | L1462 `return { family: 'all_chart_mechanisms_and_chains', label: 'L2 mechanisms (dispositor chains/cycles, yoga clus`<br>L1467 `return { family: 'all_chart_mechanisms_and_chains', label: 'L2 mechanisms (dispositor chains/cycles, yoga clus`<br>L1497 `return { family: 'full_dispositor_closure', label: 'Dispositor chain/cycle closure', status: 'domain_block_not` |
| `platform-mcp/src/tools/register_p1_aliases.ts` | mcp_tool | yes | — | L1491 `'L2 named, valenced Mechanism (Yantra) objects from bodha_mechanisms — the first-class ' +` |

**Depends on.** `bo_cgm_motifs`, `bo_cgm_paths`, `bo_karanajala`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 1.
- *Retire with a `data_disposition`* — 5 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts`, `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_mechanisms.ts`, `platform-mcp/src/tools/registry_bridge.ts`, `platform-mcp/src/tools/register_p1_aliases.ts`; 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `ga_vichara`

**What it is.** Gaṇita — Vichāra (judged structure) · layer `ganita` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Judgment layer over ga_structural: functional-lordship valence pass, varga-ratification matrix + divergence signals, continuous varga-consistency index, and leverage_index (remedy/intervention-timing rank).

**What it produces.** `target_table` = `chart_vichara`. Tables touched: `chart_vichara` (exists=True, view=False, total=24736, native=8249).
`count_sql` for the native chart returns **8249**; `target_floor` = 0.
`asset_throughput`: lit×3 (last 2026-08-10 01:30:11.496209+00:00, rows_written 24736).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | platform_lib | yes | — | L366 ``SELECT subject, value_jsonb FROM chart_vichara` |
| `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dasha_lord_capability.ts` | platform_lib | yes | `get_dasha_lord_capability` (marsys://tool/L1/get_dasha_lord_capability) — registered_from_reachable=True; `get_dasha_lord_capability` (marsys://tool/L1/get_dasha_lord_capability) — registered_from_reachable=True | L193 `FROM chart_vichara, LATERAL unnest(constituent_fact_ids) AS cf`<br>L201 `FROM chart_vichara` |
| `platform/src/lib/retrieval/registry/layers/L1_ganita/get_vichara.ts` | platform_lib | yes | `get_vichara` (marsys://tool/L1/get_vichara) — registered_from_reachable=True; `get_vichara` (marsys://tool/L1/get_vichara) — registered_from_reachable=True; `get_vichara` (marsys://tool/L1/get_vichara) — registered_from_reachable=True; `get_vichara` (marsys://tool/L1/get_vichara) — registered_from_reachable=True | L79 `'Retrieve ga_vichara ("judged structure") rows for a chart from chart_vichara — the',`<br>L182 `FROM chart_vichara`<br>L186 `const countSql = `SELECT COUNT(*)::text AS total FROM chart_vichara WHERE ${where}`` |
| `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts` | platform_lib | yes | `query_remedies` (marsys://tool/L2/query_remedies) — registered_from_reachable=True | L136 `FROM chart_vichara WHERE ${conds.join(' AND ')} ORDER BY value_num DESC``<br>L303 `'(read from chart_vichara, §N.5). Pair with `domain` for a domain-specific ' +` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L678 `"description": "When true, rank resonance targets by L1 leverage_index = (domain load-bearing weight ÷ graha c` |
| `platform-mcp/src/tools/registry_bridge.ts` | mcp_tool | yes | — | L990 ``(chart_vichara, §N.5 — never restated/recomputed here). Full per-row breakdown + ` +` |

**Depends on.** `ga_dashas`, `ga_strength`, `ga_structural`, `ga_yoga`.
**Depended on by.** `bo_laksana` (CURRENT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — the 1 CURRENT dependent(s) `bo_laksana` would stop being CURRENT-on-DRAFT edges. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 5 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`, `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dasha_lord_capability.ts`, `platform/src/lib/retrieval/registry/layers/L1_ganita/get_vichara.ts`, `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`, `platform-mcp/src/tools/registry_bridge.ts`; 1 registry dependent(s) would name a RETIRED upstream: `bo_laksana`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Sum of valence_pass + varga_ratification (+ divergence) + varga_consistency + leverage_index rows across 5 ayanamshas

---

### `ka_bhavishya_lekha`

**What it is.** Probabilistic forward projections · layer `kala` (`layer_index`=L3) · kind `artifact` · scope `per_chart`.
> Probabilistic forward projections (3-year horizon). Assigns probability tiers (tier_1_high/tier_2_moderate/tier_3_speculative), domain labels, falsifiability hooks, and calibration records. The testable-prediction artifact per §A mission.

**What it produces.** `target_table` = `kala_bhavishya`. Tables touched: `kala_bhavishya` (exists=True, view=False, total=200, native=100).
`count_sql` for the native chart returns **100**; `target_floor` = None.
`asset_throughput`: error×1 (last 2026-08-07 14:56:29.475823+00:00, rows_written 0); lit×2 (last 2026-08-13 01:15:54.314753+00:00, rows_written 200).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` | platform_lib | yes | `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True | L348 `FROM kala_bhavishya` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_projections.ts` | platform_lib | yes | `query_projections` (marsys://tool/L3/query_projections) — registered_from_reachable=True; `query_projections` (marsys://tool/L3/query_projections) — registered_from_reachable=True; `query_projections` (marsys://tool/L3/query_projections) — registered_from_reachable=True | L42 `'Returns probabilistic forward projections for a chart from kala_bhavishya.',`<br>L143 `FROM kala_bhavishya`<br>L166 `FROM kala_bhavishya` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L1765 `"description": "Returns probabilistic forward projections for a chart from kala_bhavishya. Source: kala_bhavis` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2241 `verbatim from kala_bhavishya, never re-graded. W1 adds dasha_lord_transit_condition_forward \` |

**Depends on.** `bo_laksana`, `ka_kala_darshana`, `ka_sangam`, `ka_vighnakara`.
**Depended on by.** `ph_nimitta` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_kala_darshana`, `ka_sangam`, `ka_vighnakara`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 3 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/query_projections.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`; 1 registry dependent(s) would name a RETIRED upstream: `ph_nimitta`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Up to 50 ranked projections per chart over a 3-year forward horizon; depends on ka_kala_darshana output

---

### `ka_dasha_kala`

**What it is.** Daśā Eligibility Service · layer `kala` (`layer_index`=L3) · kind `service` · scope `per_chart`.
> Lazy-pruning tree-walk over chart_dashas (level-4 Sookshma) with cross-system agreement scoring. Serves all 7 daśā systems; KP as Vimśottarī sub-level via kp_sublevel column. Nārāyaṇa absent.

**What it produces.** `target_table` = `None`. Tables touched: **none declared**.
`count_sql` for the native chart returns **None**; `target_floor` = 0.
`asset_throughput`: lit×3 (last 2026-08-08 00:28:57.200368+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=healthy, `last_invoked_at`=None, `last_selftest_at`=2026-08-08 00:28:56.606583+00:00. F2 **n/a_no_table_declared** · F3 **n/a_no_table_declared** · F4 **UNKNOWN_no_table_to_trace**.

**`selftest_detail`** (a real detector's own output, quoted verbatim — not a status this audit assigned): `{"systems_found": ["ashtottari", "chara_karaka", "kalachakra", "mudda", "naisargika", "narayana", "vimshottari", "vimshottari_kp", "yogini"], "systems_queried": ["ashtottari", "chara_karaka", "kalachakra", "mudda", "naisargika", "vimshottari", "yogini"], "systems_expected": ["ashtottari", "chara_karaka", "kalachakra", "mudda", "naisargika", "vimshottari", "yogini"], "windows_returned": 57, "high_agreement_count": 0}`

_No serving-side SQL read of this asset's table was found in any non-test source file._

**Depends on.** `ga_dashas`.
**Depended on by.** `ka_jivana_parva` (DRAFT), `ka_kshetra` (CURRENT), `ka_sangam` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — the 1 CURRENT dependent(s) `ka_kshetra` would stop being CURRENT-on-DRAFT edges. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 0 reachable serving surface(s) would be reading a table whose producer is retired (none found); 3 registry dependent(s) would name a RETIRED upstream: `ka_jivana_parva`, `ka_kshetra`, `ka_sangam`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Service asset — no stored rows; eligibility bands computed on demand from chart_dashas

---

### `ka_graha_sancara`

**What it is.** Ephemeris service · layer `kala` (`layer_index`=L3) · kind `service` · scope `global`.
> Ephemeris-at-T service: sidereal positions for all 9 grahas at any datetime. Two read paths: bg_ephemeris (1900–2150) and live swisseph fallback. Per-call memo cache keyed on (T, ayanamsha). TRUE_NODE throughout.

**What it produces.** `target_table` = `None`. Tables touched: **none declared**.
`count_sql` for the native chart returns **None**; `target_floor` = None.
`asset_throughput`: lit×1 (last 2026-08-02 13:50:52.041520+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=unhealthy, `last_invoked_at`=None, `last_selftest_at`=2026-08-02 13:50:52.009718+00:00. F2 **n/a_no_table_declared** · F3 **n/a_no_table_declared** · F4 **UNKNOWN_no_table_to_trace**.

**`selftest_detail`** (a real detector's own output, quoted verbatim — not a status this audit assigned): `{"checks": [{"check": "ephemeris_computes", "error": "0", "passed": false}], "errors": ["ephemeris computation failed: 0"]}`

_No serving-side SQL read of this asset's table was found in any non-test source file._

**Depends on.** `bg_ephemeris`.
**Depended on by.** `ka_muhurta_seva` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 0 reachable serving surface(s) would be reading a table whose producer is retired (none found); 1 registry dependent(s) would name a RETIRED upstream: `ka_muhurta_seva`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Service asset — no stored rows; returns computed positions on demand

---

### `ka_jivana_parva`

**What it is.** Life-arc biographical chapter · layer `kala` (`layer_index`=L3) · kind `artifact` · scope `per_chart`.
> Life-arc biographical chapter artifact. Segments native life into daśā-anchored parvas with theme keywords, quality labels (building/peak/consolidating/receding/transitional), and convergence density. Historical characterization, not prediction.

**What it produces.** `target_table` = `kala_jivana_parva`. Tables touched: `kala_jivana_parva` (exists=True, view=False, total=309, native=100).
`count_sql` for the native chart returns **100**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:15:55.070135+00:00, rows_written 200); stale×1 (last 2026-07-27 14:21:45.709931+00:00, rows_written 109).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts` | platform_lib | yes | `query_life_arc` (marsys://tool/L3/query_life_arc) — registered_from_reachable=True; `query_life_arc` (marsys://tool/L3/query_life_arc) — registered_from_reachable=True | L26 `'Returns biographical life-arc chapters (parvas) for a chart from kala_jivana_parva.',`<br>L158 `FROM kala_jivana_parva` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L1693 `"description": "Returns biographical life-arc chapters (parvas) for a chart from kala_jivana_parva. Each parva`<br>L3461 `"description": "Returns biographical life-arc chapters (parvas) for a chart from kala_jivana_parva. Each parva` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2165 `'query_life_arc (L3, kala_jivana_parva — item 31 birth-year floor)',` |
| `platform-mcp/src/tools/kala_views/story.ts` | mcp_tool | yes | — | L624 ``${dedupReport.collapses.length} exact-duplicate span group(s) collapsed at serving — see dedup_report; kala_j`<br>L809 `'biographical life-arc (kala_jivana_parva) as a clean chapter hierarchy: each chapter ' +`<br>L816 `'the source kala_jivana_parva table itself is unchanged. Each chapter also carries ' +` |

**Depends on.** `ga_dashas`, `ka_dasha_kala`, `ka_kala_darshana`, `ka_sangam`, `ka_yojaka`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_dasha_kala`, `ka_kala_darshana`, `ka_sangam`, `ka_yojaka`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 3 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L3_kala/query_life_arc.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`, `platform-mcp/src/tools/kala_views/story.ts`; 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per mahadasha (typically 9 for a full Vimshottari cycle)

---

### `ka_kala_darshana`

**What it is.** Display-ready temporal view · layer `kala` (`layer_index`=L3) · kind `artifact` · scope `per_chart`.
> Display-ready temporal view. Synthesizes kala_convergence + kala_obstruction into effective_score (convergence × obstruction discount), net_label, and structured narrative. Serve-time layer for UI.

**What it produces.** `target_table` = `kala_darshana`. Tables touched: `kala_darshana` (exists=True, view=False, total=1500, native=750).
`count_sql` for the native chart returns **750**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:15:53.303027+00:00, rows_written 1500); stale×1 (last 2026-07-27 14:21:43.649004+00:00, rows_written 750).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_view.ts` | platform_lib | yes | `query_temporal_view` (marsys://tool/L3/query_temporal_view) — registered_from_reachable=True; `query_temporal_view` (marsys://tool/L3/query_temporal_view) — registered_from_reachable=True; `query_temporal_view` (marsys://tool/L3/query_temporal_view) — registered_from_reachable=True | L27 `'Returns the temporal Kāla-Darshana view for a chart from kala_darshana (ka_kala_darshana)',`<br>L87 `FROM kala_darshana`<br>L95 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_darshana WHERE ${where}`, params),` |

**Depends on.** `ka_kalasutra`, `ka_sangam`, `ka_vighnakara`.
**Depended on by.** `ka_bhavishya_lekha` (DRAFT), `ka_jivana_parva` (DRAFT), `ka_tulana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_kalasutra`, `ka_sangam`, `ka_vighnakara`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_view.ts`; 3 registry dependent(s) would name a RETIRED upstream: `ka_bhavishya_lekha`, `ka_jivana_parva`, `ka_tulana`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One display row per convergence window (up to 300 per chart); count depends on ka_sangam output

---

### `ka_kalasutra`

**What it is.** Bounded Activation · layer `kala` (`layer_index`=L3) · kind `artifact` · scope `per_chart`.
> Bounded activation artifact (1 row per signal×ayanamsha). Fills L2 null hooks (active_dasha_periods, activation_predicted_dates, dasha_activation_proximity_score) at L3. Retires row-per-day kala_timeline. Upstream: ka_yojaka + ka_sangam.

**What it produces.** `target_table` = `kala_activation`. Tables touched: `kala_activation` (exists=True, view=False, total=672551, native=335403).
`count_sql` for the native chart returns **335403**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:15:50.567754+00:00, rows_written 671496); stale×1 (last 2026-07-27 14:20:55.256702+00:00, rows_written 335447).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts` | platform_lib | yes | `yoga_activation_by_dasha` (marsys://tool/L-TIMING/yoga_activation_by_dasha) — registered_from_reachable=True | L1954 `JOIN kala_activation ka ON ka.signal_id = m.signal_id` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` | platform_lib | yes | `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True; `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True | L189 `FROM kala_activation`<br>L300 `FROM kala_activation` |
| `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts` | platform_lib | yes | `call_priority_ranking` (marsys://tool/L3/call_priority_ranking) — registered_from_reachable=True | L655 `JOIN kala_activation a ON m.signal_id = a.signal_id` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2255 `strength, trigger, graha} points read verbatim from kala_activation's own \` |

**Depends on.** `bo_laksana`, `ka_sangam`, `ka_yojaka`.
**Depended on by.** `ka_kala_darshana` (DRAFT), `ph_muhurta` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_sangam`, `ka_yojaka`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 4 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`, `platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`; 2 registry dependent(s) would name a RETIRED upstream: `ka_kala_darshana`, `ph_muhurta`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per signal × ayanamsha; count grows with number of active MSR signals in kala_activation_predicates

---

### `ka_muhurta_seva`

**What it is.** Panchāṅga-Muhūrta Service · layer `kala` (`layer_index`=L3) · kind `service` · scope `global`.
> Deterministic panchāṅga/muhūrta scoring service. Wraps panchang_engine; Tāra Bala native-chart overlay wired (birth_nakshatra_id=25 Purva Bhadrapada). Location mandatory — no silent Bhubaneswar default. 8 event classes including upaya_ritual and sadhana_initiation.

**What it produces.** `target_table` = `None`. Tables touched: **none declared**.
`count_sql` for the native chart returns **None**; `target_floor` = None.
`asset_throughput`: lit×1 (last 2026-08-02 13:50:52.126596+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=healthy, `last_invoked_at`=None, `last_selftest_at`=2026-08-02 13:50:52.061909+00:00. F2 **n/a_no_table_declared** · F3 **n/a_no_table_declared** · F4 **UNKNOWN_no_table_to_trace**.

**`selftest_detail`** (a real detector's own output, quoted verbatim — not a status this audit assigned): `{"checks": ["FORENSIC tithi: 3 == 3 PASS  (tithi.id=3 name=Shukla Tritiya)", "FORENSIC vara: 1 == 1 PASS  (vara.id=1 name=Ravivara)", "FORENSIC nakshatra: 25 == 25 PASS  (nakshatra.id=25 name=Purva Bhadrapada)", "FORENSIC yoga: 20 == 20 PASS  (yoga.id=20 name=Shiva)", "FORENSIC karana: 5 == 5 PASS  (karana.id=5 name=Garaja)", "tara_bala live: birth_nak=25 same-day score=0.5 (Janma=0.5 PASS)", "tara_bala overlay changes score: without=41.00 with=41.80", "knockout: compound inauspicious \u2192 score=0.0 PASS"], "health": "healthy", "failures": []}`

_No serving-side SQL read of this asset's table was found in any non-test source file._

**Depends on.** `ka_graha_sancara`.
**Depended on by.** `ka_sangam` (DRAFT), `ka_vighnakara` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_graha_sancara`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 0 reachable serving surface(s) would be reading a table whose producer is retired (none found); 2 registry dependent(s) would name a RETIRED upstream: `ka_sangam`, `ka_vighnakara`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Service asset — no stored rows; panchāṅga computed live per (date, location)

---

### `ka_sangam`

**What it is.** Convergence engine · layer `kala` (`layer_index`=L3) · kind `artifact` · scope `per_chart`.
> Rigor-scored intersection windows (Mode A daśā-prior funnel + Mode B off-daśā sweep). Extends kala_convergence with convergence_score (I-16 multiplicative+saturating), orb-strength (I-17 cos²), rarity_years, confidence_score (I-21), independent_current_count (I-22). THE VALUABLE CORE.

**What it produces.** `target_table` = `kala_convergence`. Tables touched: `kala_convergence` (exists=True, view=False, total=35365, native=14868).
`count_sql` for the native chart returns **14868**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:07:13.494312+00:00, rows_written 32825); stale×1 (last 2026-07-27 14:13:13.206855+00:00, rows_written 32845).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_convergence_windows.ts` | platform_lib | yes | `query_convergence_windows` (marsys://tool/L3/query_convergence_windows) — registered_from_reachable=True; `query_convergence_windows` (marsys://tool/L3/query_convergence_windows) — registered_from_reachable=True | L126 `FROM kala_convergence`<br>L135 ``SELECT COUNT(*)::text AS total FROM kala_convergence WHERE ${countWhere}`,` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/dag_edge_guard.py` (`kala_convergence` L[247, 248, 258]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py` (`kala_convergence` L[294, 297]).

**Depends on.** `bg_transit_rules`, `bo_laksana`, `ga_dashas`, `ga_positions`, `ga_strength`, `ga_tajaka`, `ka_dasha_kala`, `ka_gochara`, `ka_muhurta_seva`, `ka_yojaka`.
**Depended on by.** `ka_bhavishya_lekha` (DRAFT), `ka_jivana_parva` (DRAFT), `ka_kala_darshana` (DRAFT), `ka_kalasutra` (DRAFT), `ka_taranga` (CURRENT), `ka_tulana` (DRAFT), `ka_vighnakara` (DRAFT), `mi_adhilepa` (DRAFT), `ph_muhurta` (DRAFT), `ph_nimitta` (DRAFT), `ph_pratikara` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — the 1 CURRENT dependent(s) `ka_taranga` would stop being CURRENT-on-DRAFT edges. It would itself become a CURRENT asset resting on DRAFT: `ka_dasha_kala`, `ka_muhurta_seva`, `ka_yojaka`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L3_kala/query_convergence_windows.ts`; 11 registry dependent(s) would name a RETIRED upstream: `ka_bhavishya_lekha`, `ka_jivana_parva`, `ka_kala_darshana`, `ka_kalasutra`, `ka_taranga`, `ka_tulana`, `ka_vighnakara`, `mi_adhilepa`, `ph_muhurta`, `ph_nimitta`, `ph_pratikara`; 2 other writer(s) SELECT from its table at build time: `dag_edge_guard.py`, `mi_adhilepa.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Runtime-derived from dasha + transit cluster analysis; count depends on alignment density

---

### `ka_tulana`

**What it is.** Cross-pattern prioritization · layer `kala` (`layer_index`=L3) · kind `service` · scope `per_chart`.
> Serve-time QT-4 ranking engine. Ranks windows ACROSS patterns and life-domains by I-11 composite (convergence×0.40 + rarity×0.25 + confidence×0.20 + proximity×0.15). Provides head-to-head compare(A,B) with dissonance-aware verdicts (proceed/defer/proceed_with_mitigation) and multi-domain attention map. Pure serve-time: no stored rows.

**What it produces.** `target_table` = `None`. Tables touched: **none declared**.
`count_sql` for the native chart returns **None**; `target_floor` = 0.
`asset_throughput`: lit×2 (last 2026-08-13 01:15:55.289687+00:00, rows_written 0); stale×1 (last 2026-07-27 14:21:47.638205+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=healthy, `last_invoked_at`=None, `last_selftest_at`=2026-08-13 01:15:55.114916+00:00. F2 **n/a_no_table_declared** · F3 **n/a_no_table_declared** · F4 **UNKNOWN_no_table_to_trace**.

**`selftest_detail`** (a real detector's own output, quoted verbatim — not a status this audit assigned): `{"n": 2, "top": "t_a", "test": "tulana_rank_order"}`

_No serving-side SQL read of this asset's table was found in any non-test source file._

**Depends on.** `ka_kala_darshana`, `ka_sangam`, `ka_vighnakara`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_kala_darshana`, `ka_sangam`, `ka_vighnakara`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 0 reachable serving surface(s) would be reading a table whose producer is retired (none found); 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Serve-time service — no stored rows; rankings computed on demand over kala_convergence + kala_darshana.

---

### `ka_vighnakara`

**What it is.** Obstruction periods · layer `kala` (`layer_index`=L3) · kind `artifact` · scope `per_chart`.
> Obstruction/counter-indicator detector. Identifies malefic transits, daśā veto, panchāṅga obstructions, papakartari that suppress convergence windows. Writes kala_obstruction with severity + override_score.

**What it produces.** `target_table` = `kala_obstruction`. Tables touched: `kala_obstruction` (exists=True, view=False, total=1283, native=536).
`count_sql` for the native chart returns **536**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:08:12.911241+00:00, rows_written 1277); stale×1 (last 2026-07-27 14:21:19.010742+00:00, rows_written 623).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_obstruction_periods.ts` | platform_lib | yes | `query_obstruction_periods` (marsys://tool/L3/query_obstruction_periods) — registered_from_reachable=True; `query_obstruction_periods` (marsys://tool/L3/query_obstruction_periods) — registered_from_reachable=True; `query_obstruction_periods` (marsys://tool/L3/query_obstruction_periods) — registered_from_reachable=True | L27 `'Returns obstruction (vighna) periods for a chart from kala_obstruction (ka_vighnakara)',`<br>L81 `FROM kala_obstruction`<br>L89 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_obstruction WHERE ${where}`, params),` |
| `platform/python-sidecar/brahmagyan/kala/obstruction.py` | sidecar_serve | no | — | L634 `"SELECT COUNT(*) FROM kala_obstruction WHERE chart_id = %s",`<br>L651 `"SELECT COUNT(*) FROM kala_obstruction "` |

**Depends on.** `ga_positions`, `ka_gochara`, `ka_muhurta_seva`, `ka_sangam`.
**Depended on by.** `ka_bhavishya_lekha` (DRAFT), `ka_kala_darshana` (DRAFT), `ka_tulana` (DRAFT), `ph_muhurta` (DRAFT), `ph_pratikara` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_muhurta_seva`, `ka_sangam`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L3_kala/query_obstruction_periods.ts`; 5 registry dependent(s) would name a RETIRED upstream: `ka_bhavishya_lekha`, `ka_kala_darshana`, `ka_tulana`, `ph_muhurta`, `ph_pratikara`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Runtime-derived from transit analysis over sensitive points; count depends on graha configuration

---

### `ka_yojaka`

**What it is.** Activation bridge · layer `kala` (`layer_index`=L3) · kind `artifact` · scope `per_chart`.
> Classifies each L2 signal into a signature_class, binds the RATIFIED class template, stores concrete activation predicates for ka_sangam/ka_vighnakara to search. NEVER writes into L2 tables. Per-chart artifact; delete-then-insert idempotency.

**What it produces.** `target_table` = `kala_activation_predicates`. Tables touched: `kala_activation_predicates` (exists=True, view=False, total=150150, native=50104).
`count_sql` for the native chart returns **50104**; `target_floor` = None.
`asset_throughput`: error×1 (last 2026-08-07 15:11:36.452223+00:00, rows_written 49875); lit×2 (last 2026-08-12 16:31:26.111601+00:00, rows_written 100275).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts` | platform_lib | yes | `query_temporal_activation` (marsys://tool/L3/query_temporal_activation) — registered_from_reachable=True | L270 `FROM kala_activation_predicates` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L1765 `'kala_activation / kala_activation_predicates (forward-dated) / kala_bhavishya (L3 Kāla, ' +` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py` (`kala_activation_predicates` L[450]).

**Depends on.** `bg_ghatana`, `bg_transit_rules`, `bo_bimba`, `bo_laksana`, `bo_pratijna`, `bo_sangati`, `ga_dashas`.
**Depended on by.** `ka_jivana_parva` (DRAFT), `ka_kalasutra` (DRAFT), `ka_sangam` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 2 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`; 3 registry dependent(s) would name a RETIRED upstream: `ka_jivana_parva`, `ka_kalasutra`, `ka_sangam`; 1 other writer(s) SELECT from its table at build time: `ph_nimitta.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One predicate per L2 signal per ayanamsha; total ≈ 66,738 for native chart

---

### `lel_events`

**What it is.** Life Event Log (user-authored source data) · layer `mimamsa` (`layer_index`=None) · kind `data` · scope `per_chart`.
> Per-chart user-authored life-event corpus (occurrence + recording dates, chart-state index). Source data, NOT a built asset (has_writer=false); intaken via the LEL save API. Availability-driven calibration input; never a prediction-generation source (no-leakage).

**What it produces.** `target_table` = `None`. Tables touched: `life_events` (exists=True, view=False, total=64, native=64).
`count_sql` for the native chart returns **64**; `target_floor` = 0.
`asset_throughput`: **no rows**.

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=False, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/router/retrieval_capability_spec.ts` | platform_lib | no | — | L503 `'L1 — table life_events, chart-scoped since migration 423 (BA-LEL R2.2 Step 1): per-chart, ' +` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_mechanism_retrodiction.ts` | platform_lib | yes | `mechanism_retrodiction_get` (marsys://tool/L5/mechanism_retrodiction_get) — registered_from_reachable=True | L236 `FROM life_events` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/prediction_lifecycle_sweep.ts` | platform_lib | yes | `prediction_lifecycle_sweep` (marsys://tool/L5/prediction_lifecycle_sweep) — registered_from_reachable=True; `prediction_lifecycle_sweep` (marsys://tool/L5/prediction_lifecycle_sweep) — registered_from_reachable=True | L293 `FROM life_events`<br>L391 `FROM life_events` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/lel_intake_checklist.ts` | platform_lib | yes | `lel_intake_checklist` (marsys://tool/L5/lel_intake_checklist) — registered_from_reachable=True | L287 `FROM life_events` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_life_events.ts` | platform_lib | yes | `lel_query` (marsys://tool/L5/lel_query) — registered_from_reachable=True; `lel_query` (marsys://tool/L5/lel_query) — registered_from_reachable=True | L167 ``SELECT COUNT(*)::text AS total FROM life_events WHERE ${where}`,`<br>L190 `FROM life_events` |
| `platform/src/lib/tools/structured/query_life_events.ts` | platform_lib | no | — | L52 `FROM life_events` |
| `platform-mcp/src/tools/kala_views/ahead.ts` | mcp_tool | yes | — | L2166 `'lel_query (L5, life_events — item 31 LEL corroboration, native-only)',` |
| `platform/python-sidecar/scripts/backfill_lel_event_class_resolution.py` | sidecar_serve | no | — | L54 `"FROM life_events "` |
| `platform/python-sidecar/services/mimamsa/lel_calibration.py` | sidecar_serve | no | — | L280 `"SELECT COUNT(*) FROM life_events WHERE chart_id = %s",` |
| `platform/python-sidecar/brahmagyan/mimamsa/lel_intake.py` | sidecar_serve | yes | — | L1636 `row = conn.execute("SELECT COUNT(*) FROM life_events").fetchone()`<br>L1657 `"SELECT COUNT(*) FROM life_events WHERE source_citation IS NULL OR source_citation = ''"` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_jivanaghatana.py` (`life_events` L[186, 194, 198]).

**Depends on.** _nothing_.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 6 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_mechanism_retrodiction.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/prediction_lifecycle_sweep.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/lel_intake_checklist.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_life_events.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`, `platform/python-sidecar/brahmagyan/mimamsa/lel_intake.py`; 0 registry dependent(s) would name a RETIRED upstream; 1 other writer(s) SELECT from its table at build time: `mi_jivanaghatana.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently has NO a registered writer — consistent with the SOURCE reading.

---

### `mi_abhilekha`

**What it is.** Journal · layer `mimamsa` (`layer_index`=L5) · kind `service` · scope `per_chart`.
> Journal + re-sync service: surfaces due predictions for native feedback, ingests answers as LEL events, triggers L5-only recompute

**What it produces.** `target_table` = `mimamsa_journal`. Tables touched: `mimamsa_journal` (exists=True, view=False, total=0, native=0).
`count_sql` for the native chart returns **0**; `target_floor` = 0.
`asset_throughput`: lit×1 (last 2026-08-12 17:11:53.816939+00:00, rows_written 0); stale×1 (last 2026-08-13 01:16:30.108068+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **no** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_journal.ts` | platform_lib | yes | `query_journal` (marsys://tool/L5/query_journal) — registered_from_reachable=True; `query_journal` (marsys://tool/L5/query_journal) — registered_from_reachable=True; `query_journal` (marsys://tool/L5/query_journal) — registered_from_reachable=True | L24 `'Retrieve the native Q&A journal from mimamsa_journal (mi_seva_abhilekha). Each row:',`<br>L71 `FROM mimamsa_journal`<br>L79 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_journal WHERE ${where}`, params),` |

**Depends on.** `mi_bhavisya`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `mi_bhavisya`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_journal.ts`; 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One journal entry per prediction answered; accumulates with native engagement

---

### `mi_adhilepa`

**What it is.** Overlay · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> L5 learned-weight overlay on L1–L4 base values; 4 adjustment tables + load-bearing sensitivity map (G3)

**What it produces.** `target_table` = `mimamsa_load_bearing`. Tables touched: `mimamsa_anchor_adjustment` (exists=True, view=False, total=195, native=139); `mimamsa_convergence_adjustment` (exists=True, view=False, total=1000, native=500); `mimamsa_fact_adjustment` (exists=True, view=False, total=123272, native=61523); `mimamsa_load_bearing` (exists=True, view=False, total=9, native=4); `mimamsa_signal_adjustment` (exists=True, view=False, total=100275, native=50104).
`count_sql` for the native chart returns **112270**; `target_floor` = 0.
`asset_throughput`: error×2 (last 2026-08-21 02:36:53.708535+00:00, rows_written 112270); lit×1 (last 2026-08-12 17:12:27.453927+00:00, rows_written 112481).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_load_bearing.ts` | platform_lib | yes | `query_load_bearing` (marsys://tool/L5/query_load_bearing) — registered_from_reachable=True; `query_load_bearing` (marsys://tool/L5/query_load_bearing) — registered_from_reachable=True; `query_load_bearing` (marsys://tool/L5/query_load_bearing) — registered_from_reachable=True | L29 `'Retrieve conclusion interpretability rows from mimamsa_load_bearing (mi_adhilepa —',`<br>L75 `FROM mimamsa_load_bearing`<br>L83 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_load_bearing WHERE ${where}`, params),` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` (`mimamsa_load_bearing` L[392]).

**Depends on.** `bo_laksana`, `ga_positions`, `ka_sangam`, `mi_gunanaka`, `ph_nimitta`.
**Depended on by.** `mi_darshana` (DRAFT), `mi_seva` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_sangam`, `mi_gunanaka`, `ph_nimitta`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_load_bearing.ts`; 2 registry dependent(s) would name a RETIRED upstream: `mi_darshana`, `mi_seva`; 1 other writer(s) SELECT from its table at build time: `mi_darshana.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One overlay row per (origin_id × weight_id); starts sparse, grows with evidence

---

### `mi_bhara`

**What it is.** Field Weight Calibration · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> Stage 9 of the temporal-field pipeline: fits the hazard field's weights against this chart's recorded life events (blocked forward-chaining CV, shrinkage to the classical structural priors), publishes a new versioned weights artifact, and reports the temporal skill score and the time-rescaling goodness-of-fit. The ONLY stage permitted to read the LEL (CIRCULARITY GUARD). ṢAḌ-DARŚANA items 21/39.

**What it produces.** `target_table` = `kala_field_weight_versions`. Tables touched: `kala_field_skill` (exists=True, view=False, total=7, native=7); `kala_field_weight_versions` (exists=True, view=False, total=1, native=None).
`count_sql` for the native chart returns **7**; `target_floor` = None.
`asset_throughput`: error×2 (last 2026-08-21 02:28:16.524173+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform-mcp/src/lib/kala_envelope.ts` | mcp_tool | yes | — | L553 `FROM kala_field_skill`<br>L556 `FROM kala_field_skill agg` |
| `platform/python-sidecar/services/mi_bhara/db.py` | sidecar_serve | no | — | L212 `for table in ("kala_field_skill", "kala_field_gof"):` |
| `platform/python-sidecar/services/ka_kshetra/stage4_field.py` | sidecar_serve | no | — | L1099 `"SELECT version_id FROM kala_field_weight_versions "` |

**Depends on.** `ka_kshetra`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform-mcp/src/lib/kala_envelope.ts`; 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One skill row per scored event class plus one chart-level aggregate; grows only as the LEL grows. A chart with no LEL correctly produces the structural-prior state with skill_state = underpowered — an honest zero, not an error.

---

### `mi_bhavisya`

**What it is.** Predictions · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> Time-indexed prospective predictions with confidence + falsifiers

**What it produces.** `target_table` = `mimamsa_predictions`. Tables touched: `mimamsa_manifestation_sets` (exists=True, view=False, total=195, native=139); `mimamsa_predictions` (exists=True, view=False, total=195, native=139).
`count_sql` for the native chart returns **278**; `target_floor` = 0.
`asset_throughput`: error×1 (last 2026-08-21 02:36:53.672507+00:00, rows_written 278); lit×1 (last 2026-08-12 17:11:48.712531+00:00, rows_written 112).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_manifestation_sets.ts` | platform_lib | yes | `query_manifestation_sets` (marsys://tool/L5/query_manifestation_sets) — registered_from_reachable=True; `query_manifestation_sets` (marsys://tool/L5/query_manifestation_sets) — registered_from_reachable=True; `query_manifestation_sets` (marsys://tool/L5/query_manifestation_sets) — registered_from_reachable=True | L28 `'Retrieve prediction-manifestation-channel records from mimamsa_manifestation_sets',`<br>L79 `FROM mimamsa_manifestation_sets`<br>L87 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_manifestation_sets WHERE ${where}`, para` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts` | platform_lib | yes | `query_predictions` (marsys://tool/L5/query_predictions) — registered_from_reachable=True; `query_predictions` (marsys://tool/L5/query_predictions) — registered_from_reachable=True | L21 `'Returns logged predictions for a chart from mimamsa_predictions (mi_bhavisya).',`<br>L89 `FROM mimamsa_predictions` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts` | platform_lib | yes | `query_calibration` (marsys://tool/L5/query_calibration) — registered_from_reachable=True | L101 `? `JOIN mimamsa_predictions p` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/prediction_lifecycle_sweep.ts` | platform_lib | yes | `prediction_lifecycle_sweep` (marsys://tool/L5/prediction_lifecycle_sweep) — registered_from_reachable=True | L254 `FROM mimamsa_predictions` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_sambandha.py` (`mimamsa_manifestation_sets` L[120]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py` (`mimamsa_manifestation_sets` L[350, 353]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py` (`mimamsa_predictions` L[285, 288, 292]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_gunanaka.py` (`mimamsa_predictions` L[110]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`mimamsa_predictions` L[460]).

**Depends on.** `bo_laksana`, `mi_jivanaghatana`, `mi_kula`, `ph_nimitta`, `ph_phaladesa`, `ph_pramana`.
**Depended on by.** `mi_abhilekha` (DRAFT), `mi_pramana` (DRAFT), `mi_sambandha` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `mi_jivanaghatana`, `mi_kula`, `ph_nimitta`, `ph_phaladesa`, `ph_pramana`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 4 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_manifestation_sets.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/prediction_lifecycle_sweep.ts`; 3 registry dependent(s) would name a RETIRED upstream: `mi_abhilekha`, `mi_pramana`, `mi_sambandha`; 5 other writer(s) SELECT from its table at build time: `mi_sambandha.py`, `mi_pramana.py`, `mi_pramana.py`, `mi_gunanaka.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Accumulates as predictions are logged — not a deterministic target

---

### `mi_darshana`

**What it is.** Insight surface · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> LLM-ready pre-composed insight units with embeddings + provenance chains + trust metadata (R1–R6)

**What it produces.** `target_table` = `mimamsa_insight_units`. Tables touched: `mimamsa_insight_embeddings` (exists=True, view=False, total=0, native=0); `mimamsa_insight_units` (exists=True, view=False, total=150, native=115).
`count_sql` for the native chart returns **115**; `target_floor` = 0.
`asset_throughput`: error×2 (last 2026-08-21 02:36:53.753400+00:00, rows_written 115); lit×1 (last 2026-08-12 17:12:35.426490+00:00, rows_written 35).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insight_embeddings.ts` | platform_lib | yes | `query_insight_embeddings` (marsys://tool/L5/query_insight_embeddings) — registered_from_reachable=True; `query_insight_embeddings` (marsys://tool/L5/query_insight_embeddings) — registered_from_reachable=True; `query_insight_embeddings` (marsys://tool/L5/query_insight_embeddings) — registered_from_reachable=True | L114 `FROM mimamsa_insight_embeddings`<br>L140 `FROM mimamsa_insight_embeddings n`<br>L141 `JOIN mimamsa_insight_embeddings s` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts` | platform_lib | yes | `query_insights` (marsys://tool/L5/query_insights) — registered_from_reachable=True | L211 `FROM mimamsa_insight_units` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insight_embeddings.ts` | platform_lib | yes | `query_insight_embeddings` (marsys://tool/L5/query_insight_embeddings) — registered_from_reachable=True | L143 `LEFT JOIN mimamsa_insight_units u` |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | mcp_tool | yes | — | L865 `FROM mimamsa_insight_units` |

**Depends on.** `bo_pratijna`, `mi_adhilepa`, `mi_gunanaka`, `mi_jivanaghatana`, `mi_kula`, `mi_pariksha`, `mi_pramana`, `mi_sambandha`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `mi_adhilepa`, `mi_gunanaka`, `mi_jivanaghatana`, `mi_kula`, `mi_pariksha`, `mi_pramana`, `mi_sambandha`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 4 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insight_embeddings.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insight_embeddings.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`; 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One insight unit per promoted/supported discovery + calibration stratum + grammar cell with evidence

---

### `mi_gunanaka`

**What it is.** Multipliers · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> Empirical multiplier weights learned from calibration outcomes

**What it produces.** `target_table` = `mimamsa_multipliers`. Tables touched: `mimamsa_calibration_snapshot` (exists=True, view=False, total=5, native=4); `mimamsa_multipliers` (exists=True, view=False, total=18, native=9).
`count_sql` for the native chart returns **13**; `target_floor` = 0.
`asset_throughput`: error×1 (last 2026-08-21 02:36:53.690124+00:00, rows_written 9); lit×1 (last 2026-08-12 17:12:00.657519+00:00, rows_written 9).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/app/api/clients/[id]/learning/route.ts` | next_api | yes | — | L369 `FROM mimamsa_calibration_snapshot` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts` | platform_lib | yes | `query_calibration` (marsys://tool/L5/query_calibration) — registered_from_reachable=True | L134 `FROM mimamsa_multipliers` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py` (`mimamsa_multipliers` L[145]).

**Depends on.** `bg_formula_constants`, `mi_kula`, `mi_pramana`.
**Depended on by.** `mi_adhilepa` (DRAFT), `mi_darshana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `mi_kula`, `mi_pramana`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 2 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/app/api/clients/[id]/learning/route.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`; 2 registry dependent(s) would name a RETIRED upstream: `mi_adhilepa`, `mi_darshana`; 1 other writer(s) SELECT from its table at build time: `mi_adhilepa.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per multiplier type — small, stable catalog; grows only when new signal categories are added

---

### `mi_jivanaghatana`

**What it is.** Life event log (held-out) · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> LEL — held-out event log isolated from generation; ground truth for prediction calibration

**What it produces.** `target_table` = `mimamsa_event_provenance`. Tables touched: `mimamsa_event_provenance` (exists=True, view=False, total=64, native=64).
`count_sql` for the native chart returns **64**; `target_floor` = 0.
`asset_throughput`: lit×2 (last 2026-08-08 00:18:13.998786+00:00, rows_written 64).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **no** · F4 **no**.

_No serving-side SQL read of this asset's table was found in any non-test source file._

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py` (`mimamsa_event_provenance` L[300]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`mimamsa_event_provenance` L[154, 295]).

**Depends on.** `bg_ghatana`.
**Depended on by.** `mi_bhavisya` (DRAFT), `mi_darshana` (DRAFT), `mi_pramana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 0 reachable serving surface(s) would be reading a table whose producer is retired (none found); 3 registry dependent(s) would name a RETIRED upstream: `mi_bhavisya`, `mi_darshana`, `mi_pramana`; 2 other writer(s) SELECT from its table at build time: `mi_pramana.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Deterministic given the source-of-truth file. Re-runs MUST match the file count exactly; divergence is a bug.

---

### `mi_kula`

**What it is.** Signal families · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `global`.
> Signal-family registry + negative-control battery — the governing catalogue of what influences a reading

**What it produces.** `target_table` = `mimamsa_signal_families`. Tables touched: `mimamsa_negative_controls` (exists=True, view=False, total=4, native=None); `mimamsa_signal_families` (exists=True, view=False, total=11, native=None).
`count_sql` for the native chart returns **15**; `target_floor` = 0.
`asset_throughput`: lit×1 (last 2026-08-02 13:50:52.227555+00:00, rows_written 15).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_signal_families.ts` | platform_lib | yes | `query_signal_families` (marsys://tool/L5/query_signal_families) — registered_from_reachable=True; `query_signal_families` (marsys://tool/L5/query_signal_families) — registered_from_reachable=True | L22 `'Returns the signal-family registry from mimamsa_signal_families (mi_kula).',`<br>L86 `FROM mimamsa_signal_families` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`mimamsa_negative_controls` L[565]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_gunanaka.py` (`mimamsa_signal_families` L[120]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`mimamsa_signal_families` L[368]).

**Depends on.** `bg_class_priors`, `bg_rules`.
**Depended on by.** `mi_bhavisya` (DRAFT), `mi_darshana` (DRAFT), `mi_gunanaka` (DRAFT), `mi_pariksha` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_signal_families.ts`; 4 registry dependent(s) would name a RETIRED upstream: `mi_bhavisya`, `mi_darshana`, `mi_gunanaka`, `mi_pariksha`; 3 other writer(s) SELECT from its table at build time: `mi_pariksha.py`, `mi_gunanaka.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Fixed global catalogue of signal families + negative controls; grows only when new families are registered

---

### `mi_pariksha`

**What it is.** QA evaluation · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> Answer quality evaluation runs — automated + human QA over synthesis outputs

**What it produces.** `target_table` = `mimamsa_qa_eval`. Tables touched: `mimamsa_attribution` (exists=True, view=False, total=1425, native=1425); `mimamsa_discoveries` (exists=True, view=False, total=71, native=71); `mimamsa_qa_eval` (exists=True, view=False, total=174, native=168).
`count_sql` for the native chart returns **1664**; `target_floor` = 0.
`asset_throughput`: error×2 (last 2026-08-21 02:36:53.655163+00:00, rows_written 1664); lit×1 (last 2026-08-12 17:12:06.095182+00:00, rows_written 6).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_attribution.ts` | platform_lib | yes | `query_attribution` (marsys://tool/L5/query_attribution) — registered_from_reachable=True; `query_attribution` (marsys://tool/L5/query_attribution) — registered_from_reachable=True; `query_attribution` (marsys://tool/L5/query_attribution) — registered_from_reachable=True | L24 `'Retrieve per-signal credit/blame attribution rows from mimamsa_attribution (mi_pariksha).',`<br>L75 `FROM mimamsa_attribution`<br>L83 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_attribution WHERE ${where}`, params),` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_mimamsa_discoveries.ts` | platform_lib | yes | `query_mimamsa_discoveries` (marsys://tool/L5/query_mimamsa_discoveries) — registered_from_reachable=True; `query_mimamsa_discoveries` (marsys://tool/L5/query_mimamsa_discoveries) — registered_from_reachable=True; `query_mimamsa_discoveries` (marsys://tool/L5/query_mimamsa_discoveries) — registered_from_reachable=True | L29 `'Retrieve L5 research-value discoveries from mimamsa_discoveries (mi_pariksha) —',`<br>L80 `FROM mimamsa_discoveries`<br>L88 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_discoveries WHERE ${where}`, params),` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts` | platform_lib | yes | `query_calibration` (marsys://tool/L5/query_calibration) — registered_from_reachable=True | L141 `FROM mimamsa_qa_eval` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` (`mimamsa_discoveries` L[349]).

**Depends on.** `bg_formula_constants`, `mi_kula`, `mi_pramana`.
**Depended on by.** `mi_darshana` (DRAFT), `mi_sambandha` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `mi_kula`, `mi_pramana`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 3 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_attribution.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_mimamsa_discoveries.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`; 2 registry dependent(s) would name a RETIRED upstream: `mi_darshana`, `mi_sambandha`; 1 other writer(s) SELECT from its table at build time: `mi_darshana.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Accumulates as eval runs are executed — not a deterministic target

---

### `mi_pramana`

**What it is.** Calibration · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> Prediction outcome calibration records — confidence score vs outcome mapping

**What it produces.** `target_table` = `mimamsa_calibration`. Tables touched: `mimamsa_calibration` (exists=True, view=False, total=57, native=57); `mimamsa_reliability` (exists=True, view=False, total=6, native=6).
`count_sql` for the native chart returns **63**; `target_floor` = 0.
`asset_throughput`: error×1 (last 2026-08-21 02:36:53.627032+00:00, rows_written 63); lit×1 (last 2026-08-12 17:11:55.334107+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts` | platform_lib | yes | `query_insights` (marsys://tool/L5/query_insights) — registered_from_reachable=True | L226 `FROM mimamsa_calibration` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts` | platform_lib | yes | `query_calibration` (marsys://tool/L5/query_calibration) — registered_from_reachable=True | L115 `FROM mimamsa_calibration c` |
| `platform/src/app/api/clients/[id]/learning/route.ts` | next_api | yes | — | L329 `LEFT JOIN mimamsa_calibration mc ON mc.prediction_id = pa.prediction_id` |
| `platform-mcp/src/tools/mimamsa_outcome.ts` | mcp_tool | yes | — | L219 `'phantom phala_anchors/mimamsa_calibration columns disconnected from the real pipeline. ' +`<br>L276 `'target phala_anchors/mimamsa_calibration columns that do not exist on the live schema, ' +` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts` | platform_lib | yes | `query_calibration` (marsys://tool/L5/query_calibration) — registered_from_reachable=True | L125 `FROM mimamsa_reliability` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_sambandha.py` (`mimamsa_calibration` L[121]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_gunanaka.py` (`mimamsa_calibration` L[109]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`mimamsa_calibration` L[377, 459, 583]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` (`mimamsa_reliability` L[211]).

**Depends on.** `bg_formula_constants`, `bg_ghatana`, `mi_bhavisya`, `mi_jivanaghatana`.
**Depended on by.** `mi_darshana` (DRAFT), `mi_gunanaka` (DRAFT), `mi_pariksha` (DRAFT), `mi_sambandha` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `mi_bhavisya`, `mi_jivanaghatana`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 5 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`, `platform/src/app/api/clients/[id]/learning/route.ts`, `platform-mcp/src/tools/mimamsa_outcome.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`; 4 registry dependent(s) would name a RETIRED upstream: `mi_darshana`, `mi_gunanaka`, `mi_pariksha`, `mi_sambandha`; 4 other writer(s) SELECT from its table at build time: `mi_sambandha.py`, `mi_gunanaka.py`, `mi_pariksha.py`, `mi_darshana.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Accumulates as prediction outcomes are recorded — not a deterministic target

---

### `mi_sambandha`

**What it is.** Manifestation grammar · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> Per-native grammar of how each signal/house/karaka expresses — which channel fires for THIS person (G2)

**What it produces.** `target_table` = `mimamsa_manifestation_grammar`. Tables touched: `mimamsa_manifestation_grammar` (exists=True, view=False, total=47, native=24).
`count_sql` for the native chart returns **24**; `target_floor` = 0.
`asset_throughput`: error×1 (last 2026-08-21 02:36:53.726749+00:00, rows_written 24); lit×1 (last 2026-08-12 17:12:13.400823+00:00, rows_written 23).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_manifestation_grammar.ts` | platform_lib | yes | `query_manifestation_grammar` (marsys://tool/L5/query_manifestation_grammar) — registered_from_reachable=True; `query_manifestation_grammar` (marsys://tool/L5/query_manifestation_grammar) — registered_from_reachable=True | L22 `'Returns the manifestation grammar for a chart from mimamsa_manifestation_grammar (mi_sambandha).',`<br>L97 `FROM mimamsa_manifestation_grammar` |
| `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_manifestation_sets.ts` | platform_lib | yes | `query_manifestation_sets` (marsys://tool/L5/query_manifestation_sets) — registered_from_reachable=True | L101 `provenance: { tables: ['mimamsa_manifestation_sets'], source: 'L5 Mīmāṃsā prediction-manifestation-channel rec` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` (`mimamsa_manifestation_grammar` L[262]).

**Depends on.** `mi_bhavisya`, `mi_pariksha`, `mi_pramana`.
**Depended on by.** `mi_darshana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `mi_bhavisya`, `mi_pariksha`, `mi_pramana`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 2 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_manifestation_grammar.ts`, `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_manifestation_sets.ts`; 1 registry dependent(s) would name a RETIRED upstream: `mi_darshana`; 1 other writer(s) SELECT from its table at build time: `mi_darshana.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Structural baseline from classical priors; empirical cells accumulate with event outcomes

---

### `mi_sankalpa`

**What it is.** Intervention Ledger · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `per_chart`.
> Unified intervention ledger — every elected act (upāya · yajña · elected activity) with its adjudication record, predicted differential, performance attestation and outcome linkage; the three-armed study of election itself. Prediction spine is brahma_prospective_ledger by FK (ruling S-1) — this writer never inserts into it directly.

**What it produces.** `target_table` = `mimamsa_intervention_ledger`. Tables touched: `mimamsa_intervention_ledger` (exists=True, view=False, total=0, native=0).
`count_sql` for the native chart returns **0**; `target_floor` = None.
`asset_throughput`: dormant×1 (last 2026-08-13 01:02:38.387443+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **no** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/mcp/intervention_ledger_writer.ts` | platform_lib | yes | — | L110 ``SELECT intervention_id FROM mimamsa_intervention_ledger` |
| `platform-mcp/src/lib/kala_upaya_diagnosis.ts` | mcp_tool | yes | — | L1064 `'No resolved intervention outcomes recorded yet — mimamsa_intervention_ledger (mi_sankalpa, ' +` |
| `platform/python-sidecar/services/mi_sankalpa/db.py` | sidecar_serve | no | — | L161 `"SELECT DISTINCT event_class FROM mimamsa_intervention_ledger "`<br>L192 `"SELECT outcome_event_id FROM mimamsa_intervention_ledger "` |

**Depends on.** `ka_kshetra`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 2 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/mcp/intervention_ledger_writer.ts`, `platform-mcp/src/lib/kala_upaya_diagnosis.ts`; 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

---

### `mi_seva`

**What it is.** Serve-time apply · layer `mimamsa` (`layer_index`=L5) · kind `service` · scope `per_chart`.
> Serve-time contribution-control gateway: effective-value resolution, toggle gates, transit-current binding, MCP parity

**What it produces.** `target_table` = `mimamsa_preferences`. Tables touched: `mimamsa_preferences` (exists=True, view=False, total=0, native=None).
`count_sql` for the native chart returns **0**; `target_floor` = 0.
`asset_throughput`: lit×1 (last 2026-08-12 17:12:32.641922+00:00, rows_written 0); stale×1 (last 2026-08-13 01:17:19.317030+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **no** · F3 **no** · F4 **no**.

_No serving-side SQL read of this asset's table was found in any non-test source file._

**Depends on.** `mi_adhilepa`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `mi_adhilepa`. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 0 reachable serving surface(s) would be reading a table whose producer is retired (none found); 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Preference table rows per user × channel; service has no build-time data volume

---

### `mi_vistara`

**What it is.** Export log · layer `mimamsa` (`layer_index`=L5) · kind `data` · scope `global`.
> Audit log of all synthesis export events (PDF, JSON, MCP bundles). SCOPE EXCEPTION (PD-6 / BA-P0): scope=global is correct — the writer generates zero rows and only verifies the table; actual rows are written by mi_seva on export delivery. Migrating to per_chart would cause delete-then-insert to wipe audit records on chart rebuild, which is wrong. Known exception: table is chart_id-keyed but the b

**What it produces.** `target_table` = `mimamsa_export_log`. Tables touched: `mimamsa_export_log` (exists=True, view=False, total=0, native=0).
`count_sql` for the native chart returns **0**; `target_floor` = 0.
`asset_throughput`: lit×1 (last 2026-08-02 13:50:52.267777+00:00, rows_written 0).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **no** · F3 **yes** · F4 **no**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/python-sidecar/brahmagyan/mimamsa/export_to_bigquery.py` | sidecar_serve | no | — | L589 `"SELECT COUNT(*) FROM mimamsa_export_log"`<br>L636 `"SELECT COUNT(*) FROM mimamsa_export_log "`<br>L658 `"SELECT COUNT(*) FROM mimamsa_export_log "` |

**Depends on.** _nothing_.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge. `integrity_check_sql` is **NULL** and `target_floor` is 0.
- *Retire with a `data_disposition`* — 0 reachable serving surface(s) would be reading a table whose producer is retired (none found); 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Accumulates with each export event — operational audit log

---

### `ph_muhurta`

**What it is.** Auspicious windows · layer `phala` (`layer_index`=L4) · kind `artifact` · scope `per_chart`.
> Personalized auspicious windows: chart-strength + live-transit scored, personal-danger-avoiding, prediction-fused (rides ph_nimitta windows), honest no-good-window verdict

**What it produces.** `target_table` = `phala_muhurta`. Tables touched: `phala_muhurta` (exists=True, view=False, total=183, native=134).
`count_sql` for the native chart returns **134**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:16:03.105166+00:00, rows_written 195).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` | platform_lib | yes | `query_auspicious_windows` (marsys://tool/L4/query_auspicious_windows) — registered_from_reachable=True; `query_auspicious_windows` (marsys://tool/L4/query_auspicious_windows) — registered_from_reachable=True | L42 `'Returns personalized auspicious windows for a chart from phala_muhurta (ph_muhurta).',`<br>L90 `FROM phala_muhurta` |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | mcp_tool | yes | — | L1023 `FROM phala_muhurta pm` |

**Depends on.** `ga_condition`, `ga_panchanga`, `ga_positions`, `ka_gochara`, `ka_kalasutra`, `ka_sangam`, `ka_vighnakara`, `ph_nimitta`.
**Depended on by.** `ph_phaladesa` (DRAFT), `ph_pramana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_kalasutra`, `ka_sangam`, `ka_vighnakara`, `ph_nimitta`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 2 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`; 2 registry dependent(s) would name a RETIRED upstream: `ph_phaladesa`, `ph_pramana`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per scored muhurta candidate window in query range

---

### `ph_nimitta`

**What it is.** Predictive anchors · layer `phala` (`layer_index`=L4) · kind `artifact` · scope `per_chart`.
> Predictive anchors: 8 derivation axes (graph-causal, discovery-seeded, embedding-precedent, dāśā+school consensus, ayanāṃśa-robustness, subsystem) + 5 elevations (magnitude, ranged-confidence, karmic-arc, actionability, contradiction); inherits kala_bhavishya

**What it produces.** `target_table` = `phala_anchors`. Tables touched: `phala_anchors` (exists=True, view=False, total=195, native=139).
`count_sql` for the native chart returns **139**; `target_floor` = None.
`asset_throughput`: error×1 (last 2026-08-07 14:56:30.882245+00:00, rows_written 0); lit×2 (last 2026-08-13 01:16:00.435155+00:00, rows_written 195).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` | platform_lib | yes | `query_remedy_program` (marsys://tool/L4/query_remedy_program) — registered_from_reachable=True | L393 `FROM phala_anchors a` |
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts` | platform_lib | yes | `query_predictive_anchors` (marsys://tool/L4/query_predictive_anchors) — registered_from_reachable=True; `query_predictive_anchors` (marsys://tool/L4/query_predictive_anchors) — registered_from_reachable=True; `query_predictive_anchors` (marsys://tool/L4/query_predictive_anchors) — registered_from_reachable=True | L35 `'Returns predictive anchors for a chart from phala_anchors (ph_nimitta).',`<br>L133 `FROM phala_anchors`<br>L161 `'SELECT count(*)::int AS n FROM phala_anchors WHERE chart_id = $1',` |
| `platform/src/app/api/clients/[id]/learning/route.ts` | next_api | yes | — | L328 `FROM phala_anchors pa` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L2135 `"description": "Returns predictive anchors for a chart from phala_anchors (ph_nimitta). Source: phala_anchors ` |
| `platform-mcp/src/tools/register_p1_synthesis.ts` | mcp_tool | yes | — | L1038 `FROM phala_anchors pa` |
| `platform-mcp/src/tools/mimamsa_outcome.ts` | mcp_tool | yes | — | L287 `'anchor_id from phala_anchors (e.g. "PH-4-1.2026H1.CAREER"). ' +` |
| `platform-mcp/src/tools/phala_outlook.ts` | mcp_tool | yes | — | L315 `'PH-4-1 (phala_anchors), PH-4-2 (phala_mitigation), ' +` |
| `platform/python-sidecar/brahmagyan/mimamsa/outcome.py` | sidecar_serve | yes | — | L555 `description="anchor_id from phala_anchors (e.g. 'PH-4-1.2026H1.CAREER')",` |
| `platform/python-sidecar/brahmagyan/phala/mitigation.py` | sidecar_serve | yes | — | L1060 `cur.execute("SELECT DISTINCT chart_id FROM phala_anchors")` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py` (`phala_anchors` L[314, 317]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py` (`phala_anchors` L[62, 67, 73]); `platform/python-sidecar/pipeline/orchestrator/writers/ph_suddha_sodhana.py` (`phala_anchors` L[123]); `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py` (`phala_anchors` L[184, 189, 230]).

**Depends on.** `bo_anveshana`, `bo_bimba`, `bo_cgm_paths`, `bo_karanajala`, `bo_laksana`, `bo_samskara`, `bo_sangati`, `ka_bhavishya_lekha`, `ka_sangam`.
**Depended on by.** `mi_adhilepa` (DRAFT), `mi_bhavisya` (DRAFT), `ph_muhurta` (DRAFT), `ph_phaladesa` (DRAFT), `ph_pramana` (DRAFT), `ph_pratikara` (DRAFT), `ph_rectification` (DRAFT), `ph_sankrama` (DRAFT), `ph_sodhana` (DRAFT), `ph_suddha_sodhana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_bhavishya_lekha`, `ka_sangam`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 8 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`, `platform/src/lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts`, `platform/src/app/api/clients/[id]/learning/route.ts`, `platform-mcp/src/tools/register_p1_synthesis.ts`, `platform-mcp/src/tools/mimamsa_outcome.ts`, `platform-mcp/src/tools/phala_outlook.ts`, `platform/python-sidecar/brahmagyan/mimamsa/outcome.py`, `platform/python-sidecar/brahmagyan/phala/mitigation.py`; 10 registry dependent(s) would name a RETIRED upstream: `mi_adhilepa`, `mi_bhavisya`, `ph_muhurta`, `ph_phaladesa`, `ph_pramana`, `ph_pratikara`, `ph_rectification`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`; 4 other writer(s) SELECT from its table at build time: `mi_adhilepa.py`, `mi_bhavisya.py`, `ph_suddha_sodhana.py`, `mi_pariksha.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per predictive anchor; count depends on convergence density and multi-axis derivation

---

### `ph_phaladesa`

**What it is.** Domain result declaration · layer `phala` (`layer_index`=L4) · kind `artifact` · scope `per_chart`.
> Domain result declaration: 7 domains × 1 row. B.11-compliant (Bodha synthesis read first). Deterministic scaffold (anchor inventory, spillover, mitigation/muhurta coverage). Narration pending via Gemini/DeepSeek only (Anthropic BANNED by DB CHECK)

**What it produces.** `target_table` = `phala_phaladesa`. Tables touched: `phala_phaladesa` (exists=True, view=False, total=26, native=13).
`count_sql` for the native chart returns **13**; `target_floor` = None.
`asset_throughput`: error×1 (last 2026-08-07 14:56:31.248928+00:00, rows_written 0); lit×1 (last 2026-08-12 17:11:40.333705+00:00, rows_written 13); stale×1 (last 2026-08-13 01:16:27.343582+00:00, rows_written 13).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_domain_result.ts` | platform_lib | yes | `query_domain_result` (marsys://tool/L4/query_domain_result) — registered_from_reachable=True; `query_domain_result` (marsys://tool/L4/query_domain_result) — registered_from_reachable=True | L30 `'Returns the L4 domain result map for a chart from phala_phaladesa (ph_phaladesa).',`<br>L92 `FROM phala_phaladesa` |

**Depends on.** `bo_laksana`, `ph_muhurta`, `ph_nimitta`, `ph_pramana`, `ph_pratikara`, `ph_sankrama`, `ph_suddha_sodhana`.
**Depended on by.** `mi_bhavisya` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ph_muhurta`, `ph_nimitta`, `ph_pramana`, `ph_pratikara`, `ph_sankrama`, `ph_suddha_sodhana`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L4_phala/query_domain_result.ts`; 1 registry dependent(s) would name a RETIRED upstream: `mi_bhavisya`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: Seven rows per chart (one per domain)

---

### `ph_pramana`

**What it is.** Falsifiability scaffolding · layer `phala` (`layer_index`=L4) · kind `artifact` · scope `per_chart`.
> Unified machine-evaluable falsifiers for every L4 prediction + the L5 onboarding contract + evaluation-staging (no scoring) + portfolio/reverse-calibration channel. Strictly non-scoring (L5 owns calibration)

**What it produces.** `target_table` = `phala_pramana`. Tables touched: `phala_pramana` (exists=True, view=False, total=195, native=139).
`count_sql` for the native chart returns **139**; `target_floor` = None.
`asset_throughput`: lit×1 (last 2026-08-12 17:11:31.591088+00:00, rows_written 56); stale×1 (last 2026-08-13 01:16:22.481143+00:00, rows_written 139).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` | platform_lib | yes | `query_falsifiers` (marsys://tool/L4/query_falsifiers) — registered_from_reachable=True; `query_falsifiers` (marsys://tool/L4/query_falsifiers) — registered_from_reachable=True | L201 `'Returns machine-evaluable falsifiers for L4 predictions from phala_pramana (ph_pramana).',`<br>L232 `FROM phala_pramana` |

**Depends on.** `ph_muhurta`, `ph_nimitta`, `ph_pratikara`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`.
**Depended on by.** `mi_bhavisya` (DRAFT), `ph_phaladesa` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ph_muhurta`, `ph_nimitta`, `ph_pratikara`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`; 2 registry dependent(s) would name a RETIRED upstream: `mi_bhavisya`, `ph_phaladesa`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per L4 prediction across all ph_* prediction-emitting assets

---

### `ph_pratikara`

**What it is.** Mitigation · layer `phala` (`layer_index`=L4) · kind `artifact` · scope `per_chart`.
> Managed remedy program: economics/feasibility tiers, sequenced+conflict-free schedule, muhūrta-timed initiation, severity-proportional, cross-tradition choice, outcome loop

**What it produces.** `target_table` = `phala_mitigation`. Tables touched: `phala_mitigation` (exists=True, view=False, total=1277, native=536).
`count_sql` for the native chart returns **536**; `target_floor` = None.
`asset_throughput`: lit×1 (last 2026-08-12 17:11:21.361862+00:00, rows_written 741); stale×1 (last 2026-08-13 01:16:05.883214+00:00, rows_written 536).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` | platform_lib | yes | `query_remedy_program` (marsys://tool/L4/query_remedy_program) — registered_from_reachable=True; `query_remedy_program` (marsys://tool/L4/query_remedy_program) — registered_from_reachable=True; `query_remedy_program` (marsys://tool/L4/query_remedy_program) — registered_from_reachable=True | L341 `'Returns the managed remedy program for a chart from phala_mitigation (ph_pratikara).',`<br>L412 `FROM phala_mitigation`<br>L420 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM phala_mitigation WHERE ${where}`, params),` |
| `platform-mcp/src/tools/phala_outlook.ts` | mcp_tool | yes | — | L315 `'PH-4-1 (phala_anchors), PH-4-2 (phala_mitigation), ' +` |
| `platform-mcp/src/lib/kala_upaya_diagnosis.ts` | mcp_tool | yes | — | L328 `intervention_class: 'phala_mitigation' \| 'bodha_rm_prescription' \| 'remedy_corpus'`<br>L462 ``${scheduledIds.length} scheduled remedy step(s) — see phala_mitigation.program_jsonb.scheduled_ids ` +`<br>L474 `id: `phala_mitigation:${row.mitigation_id}`,` |
| `platform/python-sidecar/brahmagyan/phala/mitigation.py` | sidecar_serve | yes | — | L860 `f"SELECT COUNT(*) FROM phala_mitigation WHERE {where}",` |

**Build-side readers** (other writers that SELECT from this asset's table — not a serving
surface, but a real consumer a retirement would break): `platform/python-sidecar/pipeline/orchestrator/dag_edge_guard.py` (`phala_mitigation` L[253, 254, 258]).

**Depends on.** `bo_upaya`, `ka_sangam`, `ka_vighnakara`, `ph_nimitta`.
**Depended on by.** `ph_phaladesa` (DRAFT), `ph_pramana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ka_sangam`, `ka_vighnakara`, `ph_nimitta`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 4 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`, `platform-mcp/src/tools/phala_outlook.ts`, `platform-mcp/src/lib/kala_upaya_diagnosis.ts`, `platform/python-sidecar/brahmagyan/phala/mitigation.py`; 2 registry dependent(s) would name a RETIRED upstream: `ph_phaladesa`, `ph_pramana`; 1 other writer(s) SELECT from its table at build time: `dag_edge_guard.py`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per remedy recommendation, sequenced by feasibility tier

---

### `ph_rectification`

**What it is.** Birth-time rectification · layer `phala` (`layer_index`=L4) · kind `artifact` · scope `per_chart`.
> Birth-time rectification via PyJHora ascendant scan (±90 min, 5-min steps, 5 ayanamshas) scored against pre-2020 LEL events. LEAKAGE-FIREWALL: post-2020 + LEL v1.7 M5-A-S1 enrichment events held out. NO-AUTO-OVERRIDE (D43): auto_action=stage_for_review only; canonical chart never auto-mutated. Best candidate staged for native adoption.

**What it produces.** `target_table` = `phala_rectification`. Tables touched: `phala_rectification` (exists=True, view=False, total=370, native=185); `phala_rectification_best` (exists=True, view=False, total=2, native=1).
`count_sql` for the native chart returns **186**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:16:06.163083+00:00, rows_written 372).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` | platform_lib | yes | `query_rectification` (marsys://tool/L4/query_rectification) — registered_from_reachable=True; `query_rectification` (marsys://tool/L4/query_rectification) — registered_from_reachable=True; `query_rectification` (marsys://tool/L4/query_rectification) — registered_from_reachable=True | L534 `'Returns birth-time rectification candidates from phala_rectification (ph_rectification).',`<br>L598 `FROM phala_rectification`<br>L606 `query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM phala_rectification WHERE ${rectWhere}`, qp),` |
| `platform-mcp/src/generated/mcp_surface_profiles.generated.ts` | mcp_tool | no | — | L2181 `"description": "Returns birth-time rectification candidates from phala_rectification (ph_rectification). Expec` |
| `platform-mcp/src/tools/phala_outlook.ts` | mcp_tool | yes | — | L316 `'PH-4-3 (phala_rectification), PH-4-4 (panchanga_daily). ' +` |
| `platform/python-sidecar/brahmagyan/phala/rectification.py` | sidecar_serve | no | — | L759 `"SELECT COUNT(*) FROM phala_rectification WHERE chart_id = %s",` |
| `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts` | platform_lib | yes | — | L1256 `FROM phala_rectification_best WHERE chart_id = $1`,` |
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` | platform_lib | yes | `query_rectification` (marsys://tool/L4/query_rectification) — registered_from_reachable=True | L633 `FROM phala_rectification_best` |

**Depends on.** `ph_nimitta`.
**Depended on by.** _nothing_.

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ph_nimitta`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 4 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`, `platform-mcp/src/tools/phala_outlook.ts`, `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`, `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`; 0 registry dependent(s) would name a RETIRED upstream. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per (candidate offset × ayanamsha): 37 offsets × 5 ayanamshas = 185 rows; plus one staged-best row in phala_rectification_best

---

### `ph_sankrama`

**What it is.** Cross-domain spillover · layer `phala` (`layer_index`=L4) · kind `artifact` · scope `per_chart`.
> Grounded multi-hop cross-domain dynamics: lag from real activation windows + graph-bridge mechanism, A→B→C cascades, cross-domain conflicts, trajectory + mitigation routing

**What it produces.** `target_table` = `phala_sankrama`. Tables touched: `phala_sankrama` (exists=True, view=False, total=2985, native=2510).
`count_sql` for the native chart returns **2510**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:16:21.621682+00:00, rows_written 2985).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` | platform_lib | yes | `query_spillover_cascades` (marsys://tool/L4/query_spillover_cascades) — registered_from_reachable=True; `query_spillover_cascades` (marsys://tool/L4/query_spillover_cascades) — registered_from_reachable=True | L122 `'Returns cross-domain spillover cascades for a chart from phala_sankrama (ph_sankrama).',`<br>L170 `FROM phala_sankrama` |

**Depends on.** `bo_sangati`, `ph_nimitta`.
**Depended on by.** `ph_phaladesa` (DRAFT), `ph_pramana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ph_nimitta`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`; 2 registry dependent(s) would name a RETIRED upstream: `ph_phaladesa`, `ph_pramana`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per (anchor × target-domain × relationship); count depends on linkage density

---

### `ph_sodhana`

**What it is.** Anomaly detection · layer `phala` (`layer_index`=L4) · kind `artifact` · scope `per_chart`.
> Anomaly registry: 5 deterministic detectors (confidence inflation, magnitude drift, falsifier absent, ledger gap, layer leakage). LEAKAGE-FIREWALL halts build on L5 calibration contamination. auto_action=stage_for_review only.

**What it produces.** `target_table` = `phala_sodhana`. Tables touched: `phala_sodhana` (exists=True, view=False, total=138, native=97).
`count_sql` for the native chart returns **97**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:16:07.622477+00:00, rows_written 138).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` | platform_lib | yes | `query_anomaly_flags` (marsys://tool/L4/query_anomaly_flags) — registered_from_reachable=True | L310 `FROM phala_sodhana` |

**Depends on.** `bo_laksana`, `ph_nimitta`.
**Depended on by.** `ph_pramana` (DRAFT), `ph_suddha_sodhana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ph_nimitta`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`; 2 registry dependent(s) would name a RETIRED upstream: `ph_pramana`, `ph_suddha_sodhana`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per candidate rectification hypothesis in the search space

---

### `ph_suddha_sodhana`

**What it is.** Cleansed anchor disposition · layer `phala` (`layer_index`=L4) · kind `artifact` · scope `per_chart`.
> Cleansed disposition: one row per phala_anchors entry, classified as clean/flagged/staged_revision. D43 safety rail — revision_approved_by + revision_applied_at never set by writer; staged revisions require native sign-off before apply.

**What it produces.** `target_table` = `phala_suddha_sodhana`. Tables touched: `phala_suddha_sodhana` (exists=True, view=False, total=195, native=139).
`count_sql` for the native chart returns **139**; `target_floor` = None.
`asset_throughput`: lit×2 (last 2026-08-13 01:16:09.082588+00:00, rows_written 195).

**Is it served, and how do I know.** F1 `is_active`=True, `has_writer`=True, `provides_apis`=NULL, `health_probe`=NULL, `service_health`=None, `last_invoked_at`=None, `last_selftest_at`=None. F2 **yes** · F3 **yes** · F4 **yes**.

| surface file | class | reachable | capability (registered?) | evidence |
|---|---|:--:|---|---|
| `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts` | platform_lib | yes | `query_cleansed_anchors` (marsys://tool/L4/query_cleansed_anchors) — registered_from_reachable=True; `query_cleansed_anchors` (marsys://tool/L4/query_cleansed_anchors) — registered_from_reachable=True | L453 `'Returns cleansed anchor disposition rows from phala_suddha_sodhana (ph_suddha_sodhana).',`<br>L499 `FROM phala_suddha_sodhana` |

**Depends on.** `ph_nimitta`, `ph_sodhana`.
**Depended on by.** `ph_phaladesa` (DRAFT), `ph_pramana` (DRAFT).

**What each disposition would mechanically change.**

- *Promote to CURRENT* — no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. It would itself become a CURRENT asset resting on DRAFT: `ph_nimitta`, `ph_sodhana`. `integrity_check_sql` is **NULL** and `target_floor` is None.
- *Retire with a `data_disposition`* — 1 reachable serving surface(s) would be reading a table whose producer is retired: `platform/src/lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts`; 2 registry dependent(s) would name a RETIRED upstream: `ph_phaladesa`, `ph_pramana`. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.
- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only `data|service|artifact`. Would additionally void the writer/count/floor/integrity requirements for this asset; it currently HAS a registered writer, which is what a SOURCE asset by definition does not have.

_`volume_explanation`_: One row per rectification verdict (decisive/probable/unresolved); accumulates across runs

---

## 5 — What this inventory does NOT establish

- **It does not prove any capability actually returns rows to a caller.** F4 is static import
  reachability plus a `registerCapability()` call. No HTTP request was issued and no MCP tool
  was invoked in producing this document.
- **It cannot see dynamic SQL it did not flag.** A read assembled as `FROM ${tableVar}` is
  detected only when the table name also appears as a literal in the same file; a name built
  by concatenation or fetched from another module is invisible. `bo_cdlm_summary` is the
  worked example: its table is read through a `TIER_TABLE` lookup map, so the occurrence is a
  string literal, not a `FROM <table>` match.
- **It does not attribute rows to producers.** Seven assets share `bodha_msr_signals` and five
  share `chart_facts`; a serving surface reading that table is reading *the table*, not
  necessarily this asset's rows. Each asset's own `count_sql` (reported per asset) is the
  narrower figure.
- **It does not evaluate auth, feature flags, MCP surface-profile allowlists, or runtime
  health.** A reachable, registered capability can still be denied to every caller.
- **It does not evaluate correctness of any row.**
- **It certifies nothing.** Verification belongs to PARĪKṢAKA (I16); disposition to ADHIKĀRIN (G1).
