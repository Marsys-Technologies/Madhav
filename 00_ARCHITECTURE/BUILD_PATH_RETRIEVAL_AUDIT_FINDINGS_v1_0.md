---
artifact: BUILD_PATH_RETRIEVAL_AUDIT_FINDINGS_v1_0.md
canonical_id: BUILD_PATH_RETRIEVAL_AUDIT_FINDINGS
version: 1.0
status: CURRENT
created: 2026-06-29
classification: audit findings — build-path defects + retrieval seam (85 writers, L0–L5)
changelog:
  - v1.0 (2026-06-29): Initial adversarially-verified defect report. 96 actionable findings
      (23 critical, 31 high, 29 medium, 13 low actionable + 31 low + 18 info).
---

# MARSYS-JIS Build-Path & Retrieval-Seam Audit — Confirmed Defect Report

**Scope:** 85 writers + the retrieval capability registry (L0–L5) + the python-sidecar router-wiring seam.
**Status:** All findings below are adversarially verified against `db_schema.json` and/or the live DB (port 5433). Behavioral validation (D9) has NOT yet run — see closing section.

---

## 1. Executive Summary

**Total confirmed defects (actionable):** 96 (excluding 18 `info`-severity "verified-good" / by-design entries, which are recorded but require no change).

### By severity
| Severity | Count |
|---|---|
| Critical | 23 |
| High | 31 |
| Medium | 29 |
| Low | 31 |
| Info (verified-good / by-design) | 18 |

(Severity counts above include the info tier for completeness; the 96 actionable figure is critical+high+medium+low.)

### By dimension
| Dimension | Theme | Actionable count |
|---|---|---|
| D3 | Wrong/non-existent SQL columns or tables | 26 |
| D7 | Swallowed errors / silent no-ops / dead code paths | 42 |
| D2 | count_sql vs writer-emit divergence (dark data) / destructive clear | 22 |
| D8 | Fabricated values / broken grounding / inert verification | 18 |
| D4 | Unmounted routers / undeclared deps / ctx-db wiring | 13 |
| D5 | Idempotency (accrete-not-replace) deviations | 11 |
| D1 | Dependency-graph / contract conformance | 3 |
| other | Vocabulary / spec mismatch | 4 |

(Many findings carry two dimensions, e.g. a D3 wrong-column bug whose error is then D7-swallowed; counted under the lead dimension above.)

### The 4 systemic patterns (the report is mostly these, repeated)

1. **The `_ctx.db` wiring bug — the dominant single class. 24 retrieval handlers** across L2/L3/L4/L5 destructure `const { db } = _ctx` and call `db.query(...)`, but `CapabilityContext` (types.ts:343-348) only ever carries `{chart_id?, request_id?}` — every dispatch site (tool_name_bridge.ts:215, router.ts:254, loop_engine.ts:113, synergy/orchestrator.ts) passes no `db`. So `db` is `undefined`, every call throws `Cannot read properties of undefined`, and the catch block laundered it into `is_error:true`. This is the already-fixed `call_dasha_eligibility` bug repeated 24×. The correct pattern (`import { query } from '@/lib/db/client'`) is used by the working L1 handlers and `traverse_chart_graph.ts`.

2. **Broken-column SQL — pervasive across the retrieval registry. ~30 handlers** SELECT/filter/ORDER-BY on columns that do not exist on their target table (the handlers were written against an imagined schema, not the live one). Notably **all 17 L1 `chart_facts` handlers** share one identical wrong SELECT list (`fact_value_numeric`/`fact_tags`/`epistemic_tier`/`source_asset_id` — none exist), and **all 4 L0 corpus handlers** + nearly **every L3/L4/L5 query handler** point at the wrong columns or wrong tables entirely. Even the no-filter path throws because the ORDER BY references a phantom column.

3. **The dark-data count_sql gap — ~18 writers.** A writer emits to N tables but `count_sql` counts ≤ N-1, so the cockpit count under-reports and (in the worst cases) a Clear leaves orphaned rows. Worst instance is **destructive**: `mi_seva`'s unscoped `DELETE FROM mimamsa_preferences` wipes ALL users' saved preferences on any Mimamsa clear. Migration 364 fixed this family for the per-chart L2/L5 writers but missed several global/L1 writers (`mi_kula`, `ga_nakshatra`, `ga_structural`, `ga_panchanga`, `bg_reference`, `bg_yogas`, etc.).

4. **The swallowed-error / inert-guard amplifier — ~40 sites.** Two sub-patterns: (a) writers wrap per-row INSERTs or upstream loads in `except Exception: log warning; continue/return []`, so schema breaks, missing upstreams, and constraint violations present as green 0-row "success"; (b) several "two-pass verification" / FORENSIC guards are tautologies (recompute the identical expression, or `1 <= sign <= 12` which is always true), so the halt gate the asset advertises can never fire. Several **unit tests fabricate the exact column/edge values the real producers never emit**, giving false-green coverage that hid these bugs.

A fifth, smaller cross-cutting class: **`rows_inserted` over-counting** — many writers do `inserted += len(batch)` regardless of `ON CONFLICT DO NOTHING` skips or per-row rollbacks, desyncing build telemetry from `count_sql`.

---

## 2. CRITICAL findings

### C-D3-1 · L1 chart_facts handlers all SELECT 4 non-existent columns (single root cause, 17 files)
**Dimension:** D3 · **Files:** `platform/src/lib/retrieval/registry/layers/L1_ganita/*.ts` — `get_positions.ts:64`, `get_strength.ts`, `get_ashtakavarga.ts:128`, `get_bhava_bala.ts:373`, `get_aspects.ts:213`, `get_yoga_dosha.ts`, `get_argala.ts:52`, `get_dispositors.ts:626`, `get_sade_sati.ts`, `get_panchanga.ts:85`, `get_sensitive_points.ts`, `get_karakas.ts`, `get_dignity.ts:547`, `get_avasthas.ts:293`, `get_tajik.ts:61`, `get_tara_chandra_bala.ts`, `get_eclipse_flags.ts:765`.
**Wrong:** Identical SELECT list references `fact_value_numeric`, `fact_tags`, `epistemic_tier`, `source_asset_id`. None exist on `chart_facts` (correct numeric column is `fact_value_num`; the other three are absent). Live DB: `ERROR: column "fact_value_numeric" does not exist`.
**Impact:** Every L1 retrieval handler throws on every invocation → zero rows, `is_error:true` swallowed → the entire L1 retrieval surface is dead.
**Fix:** Replace `fact_value_numeric`→`fact_value_num`; drop the three phantom columns (or substitute `fact_value_jsonb`, `unit`, `verification_pass_status`, `citation_ref`). One shared SELECT-list fix applied across all 17.

### C-D3-2 · get_dashas filters/orders on chart_dashas.dasha_system & .level (absent)
**Dimension:** D3 · **File:** `L1_ganita/get_dashas.ts:458,462,475`
**Wrong:** `dasha_system` (real: `system_id`) and `level` (real: `level_n`) do not exist. Unconditional `ORDER BY dasha_system` at :475 throws on every call even with no filters.
**Impact:** Every `get_dashas` call fails.
**Fix:** Use `system_id`/`level_n`; `ORDER BY system_id, ayanamsha_id, start_date`; map public input args onto the real columns.

### C-D3-3 · query_classical_texts points at the wrong table entirely
**Dimension:** D3 · **File:** `L0_brahmagyan/query_classical_texts.ts:45-50`
**Wrong:** Queries `brahma_compendium_index` for `text_en`/`text_source`/`topic_tags`/`graha_refs`/`chapter`/`shloka_num` — none exist. The verse/shloka corpus actually lives in `classical_text_chunks` (10,651 rows: `content_en`, `content_sa`, `chapter`, `verse_ref`, `topics`, `tradition_school`). ORDER BY phantom columns → even no-filter path throws.
**Impact:** Every classical-text query returns nothing.
**Fix:** Repoint to `classical_text_chunks`; map keyword→`content_en ILIKE`, text_source→`text_id`, topic→`ANY(topics)`; `ORDER BY text_id, chapter, verse_start`.

### C-D3-4 · query_remedy_corpus & query_yoga_catalog SELECT non-existent columns (2 files)
**Dimension:** D3 · **Files:** `L0_brahmagyan/query_remedy_corpus.ts:42-45`, `query_yoga_catalog.ts:43-47`
**Wrong:** remedy: `target_graha`/`remedy_category` (real: `planet`, `remedy_type`/`category`). yoga: `yoga_name`/`tradition`/`domain_tags` (real: `name_en`, `school`, `category`). Both ORDER BY phantom columns → every call (incl. unfiltered) throws.
**Impact:** Every remedy/yoga catalog query throws → swallowed to empty.
**Fix:** Map to real columns; fix ORDER BY to `planet, remedy_type` and `school, name_en`.

### C-D7-5 · L2 Bodha core handlers read db from _ctx — undefined at runtime (3 files)
**Dimension:** D7 · **Files:** `L2_bodha/query_ucd.ts:126`, `query_signals.ts:132`, `query_domain_reading.ts:91`
**Wrong:** `const { db } = _ctx` then `db.query(...)`; `_ctx` is `{chart_id}`. `query_signals` is the primary MSR/LEL signal query (bridge routes `msr_sql` + `lel_query` here) — dead at runtime. `query_ucd` is the L2 synthesis surface.
**Impact:** Throws on every call → swallowed `is_error`. The L2 retrieval surface is dead.
**Fix:** `import { query } from '@/lib/db/client'`; replace `db.query(...)` with `query(...)` (match `traverse_chart_graph.ts`).

### C-D3-6 · query_remedies & query_domain_reading SELECT ~20+40 non-existent columns (2 files)
**Dimension:** D3 · **Files:** `L2_bodha/query_remedies.ts:97-122`, `query_domain_reading.ts:96-151`
**Wrong:** `query_remedies` — on `bodha_rm_resonances` only `resonance_id` exists of 9 SELECTed; on `bodha_rm_remedy_prescriptions` only `prescription_id`/`tradition` exist. There is **no `signal_id`** on resonances, so `emits_references=true` cannot be satisfied as written. `query_domain_reading` — `bodha_question_lenses` has **no domain column at all** (the entire domain-keyed lens design is invalid against the schema); `bodha_cdlm_cells` SELECTs `relationship_type`/`signal_count`/`net_valence`/… that don't exist (real: `domain_relationship_class`, `shared_signal_count`, `net_linkage_strength`).
**Impact:** Even with the _ctx fix, every call errors. The domain-reading lens feature is architecturally mismatched to its table.
**Fix:** Rewrite both SELECT lists against real columns (listed in evidence); reconcile the lens model with `question_type`/`template_element_ids_jsonb`.

### C-D7-7 · L3 Kala primary timing handlers read db from _ctx (2 critical of the L3 set)
**Dimension:** D4 · **Files:** `L3_kala/query_convergence_windows.ts:96`, `query_temporal_activation.ts:105`
**Wrong:** Same `_ctx.db` undefined class. `query_temporal_activation` is the L3 "primary temporal entry point" (umbrella tool + drill_children) — its failure dead-ends the whole L3 timing surface.
**Impact:** Entire L3 retrieval timing surface dead.
**Fix:** `import { query } from '@/lib/db/client'` (`call_dasha_eligibility` already does this in the same dir).

### C-D3-8 · L3 query handlers SELECT against almost-entirely-wrong column sets (4 tables)
**Dimension:** D3 · **Files:** `query_temporal_activation.ts:131` (kala_activation), `query_convergence_windows.ts:98-114` (kala_convergence), `query_life_arc.ts:105-126` (kala_jivana_parva), `query_projections.ts:91-107` (kala_bhavishya), `call_service_wrappers.ts:290` (chart_dashas via call_dasha_eligibility)
**Wrong:** Each handler filters/SELECTs `ayanamsha_id`, `window_*`, `domain_primary`, `*_lord`, `signal_id_refs`, etc. that do not exist on the target table. E.g. `kala_jivana_parva` has none of the queried columns except `chart_id`; `kala_bhavishya` real columns are `peak_date`/`window_start`/`falsifiability`/`narrative`; `call_dasha_eligibility` assumes per-row MD/AD/PD/SP lord columns but `chart_dashas` is a flat `level_n` + `lord_graha` model. Several add an `ayanamsha_id` WHERE clause to a table that has no such column → fails on every call.
**Impact:** Every L3 query fails on column resolution even once db is wired.
**Fix:** Rewrite each against the real schema (column maps enumerated in the findings); drop the `ayanamsha_id` filters where the column is absent.

### C-D3-9 · L4 Phala query handlers SELECT non-existent columns (6 tables)
**Dimension:** D3 · **File:** `L4_phala/query_predictive_anchors.ts:95-117`, `query_domain_result.ts:73-87`, `query_phala_calibration.ts:65-79/144-157/294-306/369-383/447-458/526-533`
**Wrong:** Across `phala_anchors`, `phala_phaladesa`, `phala_muhurta`, `phala_sodhana`, `phala_mitigation`, `phala_suddha_sodhana`, `phala_rectification` — the handlers SELECT ~10-17 columns each (axis scores, `ayanamsha_id`, `event_class`, `feasibility_tier`, `disposition`, `cascade_id`, etc.) that do not exist; several input_schema enums (detector_type, feasibility_tier, disposition) don't match real domains. `query_rectification`'s `WHERE disposition='staged'` references a column that doesn't exist → always errors; there is no staging workflow column at all.
**Impact:** Every L4 query errors (on top of the L4 _ctx.db bug below). Asset-registry docstrings advertise row counts (150/100/73/200) the handlers are structurally incapable of producing.
**Fix:** Rewrite all SELECT/WHERE/ORDER against real columns (full maps in the findings); drop `ayanamsha_id` filters; if a staging gate is needed it must be added to `phala_rectification` schema first.

### C-D2-10 · mi_seva clear runs UNSCOPED `DELETE FROM mimamsa_preferences` — wipes all users' preferences
**Dimension:** D2 · **Files:** `writers/mi_seva.py:11,34`, `cockpit/assetClearSpec.ts:11-20`, `api/cockpit/runs/route.ts:225-241`
**Wrong:** `mi_seva` is registered `scope=per_chart`, `count_sql='SELECT count(*) FROM mimamsa_preferences'` (no WHERE). It is not in `EXPLICIT_CLEAR_OPS`, so the clear path derives `DELETE FROM mimamsa_preferences` with no WHERE and no `$1`. `mimamsa_preferences` is a **global per-user** table `(user_id, channel_id, saved_state, updated_at)` — no `chart_id`. The writer emits zero rows and never writes this table.
**Impact:** A Mimamsa-layer or global Clear destroys EVERY user's saved preferences — cross-user data the writer doesn't own and the build never recreates. **Most dangerous finding in the set.**
**Fix:** Set `count_sql=NULL` + add `EXPLICIT_CLEAR_OPS` entry of `null` (skip-clean), OR re-scope to `global`. Never leave a per_chart asset pointing count_sql/target at the unscoped global table. (See also M-D2 mi_seva scope/registry-drift findings below — same asset, multiple defects.)

### C-D3-11 · ph_nimitta SELECTs non-existent column d.detected_at — whole asset aborts
**Dimension:** D3 + D7 · **File:** `writers/ph_nimitta.py:218` (query) / `:55` (call site)
**Wrong:** `_load_discoveries` SELECTs `d.detected_at` from `bodha_discoveries`; the column is `computed_at` (verified live). Raises `UndefinedColumn`.
**Impact (critical, not just the discovery subset):** The call at `ph_nimitta.py:55` is NOT savepoint-guarded (unlike its 3 sibling loaders which each wrap in SAVEPOINT/ROLLBACK). So the error poisons the orchestrator per-substep transaction and **fails the entire ph_nimitta asset** (zero `phala_anchors` written) — a total spine-asset outage on every chart.
**Fix:** `d.computed_at AS detected_at`. Defense-in-depth: wrap the load in the same SAVEPOINT pattern the sibling loaders use.

### C-D7-12 · ph_pramana LEL evidence permanently dead (wrong table + swallowed)
**Dimension:** D3 + D7 · **File:** `writers/ph_pramana.py:170-202`
**Wrong:** `_load_lel` queries `life_event_log` (does not exist; real table `life_events`) and columns `domain_primary`/`event_summary`/`outcome_valence` (none exist on `life_events`). The query is wrapped in SAVEPOINT/`except → logger.debug('LEL load skipped')` with a comment misattributing the cause to "table seeded separately." Commit 7a86e796 added the SAVEPOINT but did not fix the table/columns — converting a hard failure into a silent no-op.
**Impact:** `lel_match` is always None → `life_event_match` evidence never fires; every anchor yields only `pending_observation`/`life_event_miss`. The writer's central purpose (life events as falsifiability evidence) produces zero matches on every build.
**Fix:** Point at `life_events`, remap columns (`id` uuid, `event_date`, `domain`, `description AS event_summary`, `outcome_observed`); narrow the except to `UndefinedTable` and log the real cause.

---

## 3. HIGH findings

### Group H-A · The `_ctx.db` undefined-handler class (remaining instances)
**Dimension:** D7/D4 · One root cause; fix is identical for all (`import { query } from '@/lib/db/client'`, drop `_ctx.db`):
- **L2_bodha (2):** `query_remedies.ts:89`, `query_quality_scorecard.ts:74`
- **L3_kala (3):** `query_life_arc.ts:103`, `query_projections.ts:89`, `call_muhurta_score.ts`→`call_service_wrappers.ts:401`
- **L4_phala (9 query points, 3 files):** `query_predictive_anchors.ts:93`, `query_domain_result.ts:71`, `query_phala_calibration.ts:64,143,215,293,368,446,524` — no L4 file imports `@/lib/db/client` at all.
- **L5_mimamsa (5):** `query_calibration.ts:110`, `query_insights.ts:126`, `query_manifestation_grammar.ts:81`, `query_predictions.ts:75`, `query_signal_families.ts:62`.

**Impact:** Every one of these handlers throws and is swallowed to `is_error`. Combined with the L2/L3 criticals above, retrieval is dead across L2–L5.

### Group H-B · Broken-column query handlers (high-tier, remaining)
**Dimension:** D3 · One class (handler written against imagined schema):
- `L0_brahmagyan/query_dosha_catalog.ts:44-48` — `dosha_name`/`severity_tier`/`domain_tags` absent (real: `name_en`, `severity_grades` jsonb, `category`); ORDER BY phantom → every call throws. (Table has 79 rows, not 50.)
- `L1_ganita/get_divisionals.ts:700,708` — `varga_code` (real: `varga`); unconditional ORDER BY throws every call.
- `L1_ganita/get_tajik.ts:78-81` — `year_num` (real: `varsha_year`); ORDER BY throws on every `include_varsha` call. (Also carries the chart_facts bug.)
- `L2_bodha/query_contradictions.ts:99-141` — `resolution_approach`/`resolution_status` (real: `resolution_hint_jsonb`); `bodha_discoveries` columns all wrong (`discovery_class`, `hypothesis_text`, `non_obviousness_score`, `computed_at`); `bodha_anomalies` `severity`/`description`/`signal_id_ref` absent.
- `L2_bodha/query_quality_scorecard.ts:76-85` — `total_signals`/`quality_score`/`quality_tier`/`created_at` none exist (real: `msr_signal_count`, `two_pass_verified_pct`, `trap1_authority_inversion_count`, `scored_at`).
- `L2_bodha/traverse_chart_graph.ts:325,456,519` — `bodha_cgm_nodes.valence` does not exist (valence lives on edges); neighbors/paths/convergence node SELECTs all error. **This handler is otherwise correctly wired** (uses `query()`), so the column bug is its sole blocker.
- `L3_kala call_ephemeris_at_t` (`call_service_wrappers.ts:204`) — queries non-existent `ka_graha_sancara_snapshot` (service has `target_table=null`); and `call_muhurta_score:407` — non-existent `ka_muhurta_scores`. Both should hit a compute sidecar, not a table.
- `L5_mimamsa/query_manifestation_grammar.ts:93-102` (11 cols), `query_predictions.ts:85-93` (7 cols), `query_signal_families.ts:74-82` (6 cols incl. the entire `is_negative_control` concept) — all SELECT a fabricated schema; live tables use `origin_kind`/`channel_propensity`, `outcome_claim`/`lifecycle_status`, `display_name`/`binding_kind`. Input_schema even advertises `outcome_status` enum where the column is `lifecycle_status`.

### Group H-C · Unmounted python-sidecar routers with live callers (transit_search bug class)
**Dimension:** D4 ·
- **mimamsa_outcome** MCP tool (`mimamsa_outcome.ts:177,198`, registered `server.ts:139`) fetches `/api/compute/mimamsa/record_outcome` and `/query_calibration`. Both handlers live only in `outcome.py:734,766`, never `include_router`'d in `main.py`. The mounted `prediction_ledger.py:614` defines a `record_outcome` but under `/api/brahma` (wrong path); `query_calibration` has no mounted equivalent. **Both calls 404.**
- **holistic_bundle** MCP tool (`bo_2-8.ts:105`, registered `server.ts:123`) fetches `/api/compute/brahma/bodha/holistic_bundle`; handler exists only in `bo_2-8.py:323`, unmounted. The parallel `holistic_bundle_chart_facts` tool is a different MCP name and does not rescue it. **404 on a live registered tool.**
**Fix:** Mount the routers OR repoint/deprecate the tools — but never leave a registered tool fetching an unmounted route. Resolve the duplicate `record_outcome` definitions to one source of truth.

### Group H-D · Dead detectors — upstream never emits the inputs they filter on (bo_cgm_motifs / bo_cgm_paths / bo_karanajala / bo_bimba chain)
**Dimension:** D7 · A connected producer/consumer contract break centered on `bo_bimba.py:162` writing `position_in_chart_jsonb=None` for every graha node, and `bo_karanajala` never emitting dispositor edges or `relationship_basis`:
- `bo_cgm_motifs.py:155` **stellium detector** — drops every graha (`pos is None: continue`) → zero stellium motifs ever.
- `bo_cgm_motifs.py:103,223` **mutual_reception + parivartana_chain** — filter on `relationship_basis in ('dispositor',...)` / `edge_type in ('dispositor',...)`; `bo_karanajala` only emits `{argala, yoga_domain, dosha_domain, conjunction, aspect}` and never sets `relationship_basis`. → 2 of 3 motif classes dead; combined with stellium, the writer can only ever emit 0 rows.
- `bo_cgm_paths.py:101-116` **is_final_dispositor** — `_is_self_ruling` reads `position_in_chart_jsonb['sign']` which is always None → `is_final_dispositor=False` for ALL rows. Downstream `bo_chart_gestalt.py:179` (`WHERE is_final_dispositor=true`) and `ph_nimitta.py:286` (`any(...)`) silently get nothing. This is a CONTRACT-3 (A7→A5) required-but-wrong field.
- `bo_karanajala.py:156-177` **argala** — `_fetch_graha_sign_numbers` queries `fact_category='graha_position' AND fact_key='sign_number'` reading `fact_value_text`; live L1 (`ga_positions_writer.py:285`) emits `fact_category='graha_sign_attributes'`, `fact_key='sign_num'`, value in `fact_value_num`, subject in UPPER_SNAKE codes (`SUN`/`MOON`/…). **Four independent mismatches**, each alone returns `{}` → argala edges always empty, no error raised.
- **False-green tests:** `test_bo_a7_writers.py:331` and `:255,300` feed fabricated `relationship_basis:'dispositor'` and `{"sign":...}` that the real producers never emit, so the suite passes while production yields 0.
**Fix:** Populate `position_in_chart_jsonb` (house/sign) for graha nodes in `bo_bimba`, add dispositor-edge construction in `bo_karanajala`, fix the argala fact query (category/key/value-column/subject), and add integration tests built from real upstream output. Add guard-raises when these fetches return empty.

### Group H-E · bo_laksana main-path salience graha resolution silently always fails
**Dimension:** D7 · **File:** `bo_laksana.py:631-638` vs `:713`
**Wrong:** `_FETCH_SQL` omits `fact_subject` from its SELECT, but `_compute_salience` reads `fact_row.get('fact_subject')` → always None → `primary_graha` None → `shadbala_norm` defaults to 1.0 / `dignity_score` to 0.50 for every graha-centric fact. The B2-fix comments claim a fallback that is dead because the column isn't fetched.
**Impact:** `computed_salience`, `signature_tier`, `top_k_salience_rank` systematically under-weighted for the bulk of signals — silent degradation feeding all of L2/L3.
**Fix:** Add `fact_subject` to `_FETCH_SQL`.

### H-D1 · bo_chart_gestalt depends_on=[] but reads 5 upstream Bodha tables
**Dimension:** D1 · **File:** migration `358_…:6-18` / `asset_registry.json`
**Wrong:** `depends_on=[]` while the writer reads `bodha_msr_signals`, `bodha_cdlm_cells`, `bodha_cgm_nodes`, `bodha_cgm_paths`, `bodha_discoveries`. Orchestrator may run it before inputs exist; all SELECTs return `[]`, writer returns 0 with no error (`target_floor=1`).
**Fix:** UPDATE-migration `depends_on` to `[bo_laksana, bo_bimba, bo_sangati, bo_anveshana]`.

### H-D5 · bo_pramana_mapa scorecard accretes one row per build
**Dimension:** D5 + D2 · **File:** `bo_pramana_mapa.py:202`, `_idempotency.py:354`
**Wrong:** `replace_prior_scorecard` deletes `WHERE chart_id AND build_id`, but `build_id=run_id` is fresh per build → DELETE matches 0 prior rows → N rebuilds leave N rows (PK is `scorecard_id` only). `count_sql` then counts cumulative builds instead of 1.
**Fix:** Scope the delete to `chart_id` only (or add `UNIQUE(chart_id)` + ON CONFLICT).

### H-D8 · bo_pramana_mapa leaves 8 grounding columns NULL
**Dimension:** D8 · **File:** `bo_pramana_mapa.py:37-46,165-200`
**Wrong:** `_SCORECARD_INSERT` omits `lel_zero_leak_pass`, `no_pre_answer_pass`, `pillars_meet_reachability_pass`, `ledger_independence_pass`, `discovery_not_fabricated_pass`, `l1_assets_projected_count/_array`, `unresolved_constituent_facts_count` — the central B.11/N.5 grounding assertions the scorecard exists to record.
**Fix:** Populate them; at minimum compute `unresolved_constituent_facts_count` (the trap1 logic already inspects that array).

### High-tier writer/grounding defects (one-line each)

- **H-D8 · bg_remedies** (`l0_remedy_corpus.py:405,3384`) — `dosha_target` on every DOSHA_REMEDIES row is silently dropped (no such column; INSERT omits it; no back-link UPDATE). The advertised dosha→remedy linkage does not exist in the DB (0/79 `associated_remedies` populated) despite being the asset's stated purpose.
- **H-D3 · bg_ephemeris** (`bg_ephemeris.py:94`) — calls `_compute_positions_for_date(current)` with 1 arg; signature requires 3 (`d, swe, ephe_path`) → `TypeError` on every non-dry-run build. Compounded by **H-D7** (`bg_ephemeris.py:64-70`): never imports swisseph / resolves ephe_path / sets `swe.set_ephe_path` — even with arity fixed it cannot compute. Masked only because `ephemeris_daily` is pre-populated (825,084 rows) so `ON CONFLICT DO NOTHING` would touch 0 rows — but `run()` crashes first.
- **H-D8 · ga_sensitive** (`ga_sensitive_writer.py:2129,1381,2165`) — `is_day_birth=True` hardcoded (native's day/night) → wrong day/night Saham + Tajik formula for every non-native chart; `day_lord='Sun'` hardcoded → wrong KP `RP_DAY_LORD` for any non-Sunday birth; Hora Lagna always uses `sun+15` fallback → Trisphuta/Chatushphuta/Panchasphuta built on a fabricated Hora Lagna for every chart incl. native.
- **H-D8 · ga_strength** (`ga_strength_writer.py:1564,715`) — shadbala/bhava-bala are ad-hoc Python approximations (hardcoded `{0.75,0.375,0.625}`, literal `0.5/1.0`, `lord_total*30.0`) but every row is stamped `source_calculation='pyjhora_adapter.…'`; PyJHora's strength module is never invoked. B.10 violation: stored numbers carry an engine attribution that did not produce them.
- **H-D7 · ga_sade_sati** (`ga_sade_sati_writer.py:1432`) — missing per-ayanamsha Moon sign silently falls back to literal `"Aquarius"`, fabricating an entire Sade Sati timeline that reads `two_pass_verified`. B.10/N.5 violation.
- **H-D7 · ga_tajaka** (`ga_tajaka_writer.py:350`) — `row["fact_value_text"]` dict-access on a non-`dict_row` connection in the legacy CLI path → `TypeError` swallowed → TriRashipati Vārṣeśa silently degrades to a Lagnesa duplicate. (Orchestrator path is fine.)
- **H-D8 · ka_muhurta_seva** (`services/ka_muhurta_seva/writer.py:184,206`) — `from muhurat.finder import …` unresolvable in orchestrator runtime (`No module named 'muhurat'`); self-test Checks 3&4 fail, `service_health='unhealthy'`, yet `run()` swallows and returns success → build marks asset BUILT-OK. Path/wiring break hidden behind a soft column flag.
- **H-D7 · ka_vighnakara** (`ka_vighnakara.py:393`) — real-tithi path reads `tithi_raw.number`; the `Anga` field is `.id`, so `int(Anga)` throws, is swallowed, and the day-mod proxy `(peak_date.day % 15)` is used on EVERY run — directly contradicting the "real tithi, not day-mod" docstring. (Companion **M-D8**: emits `severity_score=0.35` obstruction rows mislabeled `source='panchang_engine'` from that fake tithi.)
- **H-D7 · ka_yojaka** (`services/ka_yojaka/classifier.py:6-17`) — `SIGNAL_CLASS_MAP` omits live MSR classes `medical` and `vastu` (emitted by `bo_laksana.py:282,284`) → routed to `CLASSIFY_RESIDUAL` stub with empty activation logic; rows count but carry no actionable predicate.
- **H-D8 · ga_medical** (`ga_medical_writer.py:270-296`) — FORENSIC guard covers only `lahiri_chitrapaksha` + Sun/Saturn; the other 4 ayanamshas and 7 grahas can build all-`unknown`/wrong without tripping; the documented Moon=`left_side` anchor is logged but never asserted.
- **H-D8 · ga_vastu** (`ga_vastu_writer.py:170-175`) — guard asserts Sun must be `'weakened'` "because Sun debilitated in Capricorn" — astrologically false (Sun debilitates in **Libra**; native's Sun in Capricorn is enemy/neutral). If Sun's composite ≥0.4 the `AssertionError` hard-fails every canonical build on every ayanamsha.
- **H-D3 · ph_pratikara** (`ph_pratikara.py:203-216`) — `_load_prescriptions` SELECTs 6 non-existent columns (`requires_acharya_review`, `recommended_hora`, `graha`, …; real names carry `_flag`/`_array`/`target_graha`). Companion **H-D7** (`:199-245`): SAVEPOINT/`except→debug` swallows it → `prescriptions_by_graha` always empty → every mitigation program structurally hollow while build "succeeds." (Asymmetric vs `_load_obstructions` which fails loud by design.)
- **H-D8 · ph_rectification** (`__init__.py:56,61,83`) — ignores `ctx.config` birth params; hardcodes the native's birth time/coords. Every non-native chart gets 185 candidate rows + 1 best row computed against the WRONG birth data, tagged with the foreign `chart_id`. Companion **M-D8** (`engine.py:219`): natal Saturn/Mercury signs hardcoded as constants (N.5 violation).
- **H-D8 · ph_sankrama** (`ph_sankrama.py:79`) — anchor domain vocabulary {career,relationship,financial,spiritual,health,transition,psychological} vs CDLM {career,wealth,health,relationship,spirituality,character,general}; only 3 overlap → ~4/7 of anchors produce zero spillover, silently skipped. Companion **H-D7** (`engine.py:208`): natural key omits `cdlm_cell_id` → distinct cells linking the same domain pair collapse, only first survives non-deterministically.
- **H-D7 · ph_sodhana** (`ph_sodhana.py:58-89`) — per-row INSERT in a bare `except → warning`; CHECK-constraint violations on `anomaly_type`/`severity`/`leakage_class`/`auto_action` are swallowed, build records SUCCESS with silently dropped anomaly flags.
- **H-D7 · mi_darshana** (`mi_darshana.py:121,158,186`) — `horizon`/`question_lens` hardcoded None and `is_negative_knowledge` hardcoded False on every insert; the 3 views filtered `WHERE … IS NOT NULL` / `= true` are structurally always-empty; `views_verify` reports success regardless. The `negative_knowledge` insight_type is never produced.
- **H-D8 · mi_bhavisya** (`mi_bhavisya.py:128-133`) — `outcome_claim` reads `anchor.get('outcome_claim'|'prediction_text'|'summary')`, none of which exist on `phala_anchors` → `outcome_claim` is the literal `'unspecified'` for 100% of frozen predictions. Companion **M-D7** test (`test_ka_bhavishya_a4_fixes.py:289`) mocks the non-existent columns → false green.

---

## 4. MEDIUM findings

### Dark-data count_sql gaps (D2) — same class, distinct assets
- **mi_kula** (`mi_kula.py:249-272`) — emits `mimamsa_signal_families` + `mimamsa_negative_controls`; count_sql counts only the first. **Companion D2 (clear gap):** not in `EXPLICIT_CLEAR_OPS`, so a Clear leaves `mimamsa_negative_controls` orphaned. Fix: explicit clear ops for both + summed count_sql.
- **ga_nakshatra** (`asset_registry` vs `ga_structural_writer.py:5366,5386,5405`) — count_sql includes `nakshatra_lord_relationship`/`tara_bala`/`nakshatra_co_tenancy` which are emitted/cleared by **ga_structural**, not ga_nakshatra → double-counts another asset's rows. Migration-364 mis-assigned them. Move them to `ga_structural.count_sql`.
- **ga_structural** (`asset_registry` vs writer) — count_sql **undercounts 9 categories** the writer emits (`ashtakavarga_anubindu`, `graha_saptavargaja_bala_component`, `vimsopaka_bala_per_graha`, `parivartana_pairs`, `retrograde_aspect_modification`, `nakshatra_co_tenancy`, `tara_bala`, `nakshatra_lord_relationship`, `bhava_chalit_rasi_divergence`). Clear IS covered (delete derives from row categories), so count-only gap. New surgical migration to add the 9.
- **ga_panchanga** (`asset_registry` vs writer) — `LIKE 'panchanga%'` misses 5 emitted categories (`bhadra_flag`, `panchaka_flag`, `eclipse_proximity_natal`, `tara_bala_natal_baseline`, `chandra_bala_natal_baseline`) ≈ 195+ dark rows/chart. Clear covered; count-only.
- **ga_prashna** (`ga_prashna_writer.py:307` vs registry) — writes `ga_prashna_lagna` + `ga_prashna_judgment`; only the judgment table is registered/counted. `ga_prashna_lagna` rows invisible to count and unowned by registry clear.
- **bg_reference** (`l0_reference.py` vs registry) — count_sql sums `reference_yogas`/`reference_doshas`/`reference_dasha_systems` (~272 rows) owned by **bg_yogas/bg_doshas/bg_dasha_systems**, not this writer → cross-asset count entanglement. Remove the three.
- **bg_yogas** (`l0_yogas.py:2123,2145,1734`) — count_sql counts only `brahma_yoga_catalog`; ontology + `reference_yogas` writes invisible; `seed_yoga_families()` (4th table) never called from production → `yoga_families` is 0 rows / dead taxonomy.
- **bg_dasha_systems** (`l0_dasha_systems.py:206` vs `l0_ontology.py:193`) — Chara dasha written to `brahma_ontology` under two divergent `canonical_id`s (`chara_jaimini` vs `jaimini_chara`); `ON CONFLICT DO NOTHING` never collides → phantom duplicate row, invisible to this asset's count_sql. Unify the canonical_id and delete the orphan.
- **bg_texts** (`bg_texts.py:315,322`) — populates `classical_texts` (16 rows) that no count_sql counts; full rebuild deletes only chunks + one hardcoded `lal_kitab` row → other `classical_texts` rows survive a "full" rebuild as orphans.
- **bg_transit_rules** (`l0_transit.py:602`) — count_sql `COUNT(*)`=50 but writer's authoritative content is 47; 5 stale venus/`unfavourable` orphan rows (key change with no delete path) are indistinguishable from live rows. Paired D5 below.
- **mi_adhilepa** (`mi_adhilepa.py:198,223`) — emits 5 tables; count_sql counts 3; `mimamsa_signal_adjustment` + `mimamsa_fact_adjustment` (potentially the largest contributors) are dark. Clear covers all 5.
- **mi_seva** (registry) — additional D2 facets beyond the critical: `count_sql` is unscoped on a `chart_id`-less table (per-chart count structurally impossible); `scope='per_chart'` contradicts the writer's own GLOBAL/service design; seed (`asset_registry_seed.ts:1783`) sets `count_sql=null` but live DB has non-null → registry drift (B.8 / GA.1). Fix scope→global and reconcile seed vs live.

### Idempotency accrete-not-replace (D5)
- **bg_compendium_index** (`bg_compendium_index.py:170,279`) — `ON CONFLICT DO NOTHING`, no DELETE; staleness fields never refreshed; orphans for deleted chapters/topics persist. (Companion **M-D8** `:169,278`: `chunk_ids` always written `ARRAY[]::BIGINT[]` → navigational index can't resolve to source chunks; all 9538 rows empty.)
- **bg_rules** (`l0_rules.py:1245`) — `ON CONFLICT (rule_id) DO NOTHING`, no DELETE; `rule_id` is a content-hash that shifts when regex patterns or source content change → stale rules orphan forever and inflate count_sql. Fix: scope-delete `WHERE extracted_by='python_regex_v2'` before reinsert.
- **bg_transit_rules** (`l0_transit.py:606`) — upsert-only, no DELETE; unstable natural keys leak orphans (see paired D2). Fix: `DELETE FROM bg_transit_rules` before re-seed.

### Other medium writer defects
- **ga_dashas** (`ga_dashas_writer.py:2437`) — orchestrator path never writes the 2 `scope_cap` sentinel rows (CLI-only) → orchestrator-built charts have 2 fewer rows than CLI charts. Companion **M-D7** (`:470`): `_verify_vimshottari` Pass-1 duration check is a `pass` no-op → always returns `two_pass_verified` for non-native charts. Companion **M-other** (`:2593`): concurrency post-pass ignores `ayanamsha_id` → `concurrent_system_lords_jsonb` mixes ayanamshas.
- **ga_condition** (`ga_condition_writer.py:708`) — `_load_graha_positions` swallows all exceptions → empty positions become a 0-row "success" masking a failed `ga_positions` upstream.
- **ga_structural** (`ga_structural_writer.py:5327…`) — builders swallow query exceptions → partial build looks complete; the orchestrator substep path lacks the `check_upstream_presence` gate the legacy path has.
- **ga_vargas** (`ga_vargas_writer.py:2277`) — `_write_halt_log(chart_id, build_id, gate, msg)` called with 4 args; helper takes 2 → `TypeError` crashes the FORENSIC-fail path, masking the real FORENSIC failure. Companion **M-D7** (`:2140`): `_write_rows_batch` swallows every per-row INSERT exception and still reports PASS.
- **ga_yoga** (`ga_yoga_writer.py:236`) — reads degrees on `fact_key in ('degree_absolute','longitude')`; the only key actually written is `longitude_sidereal` → `planet_degree` always empty → Budha-Aditya combustion gate silently bypassed (yoga fires even when Mercury deeply combust). Companion **M-D7** (`:1060`): per-yoga INSERT failures swallowed/undercounted.
- **ga_prashna** (`ga_prashna_writer.py:181-193`) — `compute_prashna_judgment` returns None with no log on two real-failure paths for an actual prashna chart → indistinguishable from a legitimate "not a prashna chart" skip.
- **ga_transit_anchors** (`ga_transit_anchors.py:153-185`) — missing Moon for a non-native chart only logs an error then writes `natal_house_from_moon=1` for all 8 grahas into a NOT NULL column (fabricated Gochara house). FORENSIC AssertionError protects only the canonical chart.
- **bg_concordance** (`bg_concordance.py:91`) — upstream-missing returns a "successful" `rows_inserted=0` WriterResult with a `HALT:`-prefixed note that does not actually halt.
- **bg_texts** (`bg_texts.py:90-103`) — `_download_gcs` swallows all exceptions → real auth/network errors mislabeled `AWAITING_MANUAL_UPLOAD`; build reports success with a silently-incomplete corpus.
- **bo_anveshana** (`bo_anveshana.py:746-766`) — `_batch_insert` per-row recovery loop is unreachable: no SAVEPOINT precedes `executemany`, so the aborted transaction kills every retry, and the swallowed exception lets `run()` continue into the next ayanamsha on a poisoned transaction (orchestrator's outer savepoint RELEASEs over it).
- **bo_samvada** (`asset_registry` vs `bo_samvada.py`) — count_sql points at `bodha_msr_signals` (a different asset's table); the writer creates `vw_chart_digest` and writes 0 rows. Migration 327's intended fix is neither in the live registry nor reverted to 326's value — live diverges from both migrations.
- **bo_upaya** (`bo_upaya.py:531` vs registry) — count_sql sums `bodha_rm_dasha_windowed_prescriptions` which the writer never writes or clears → 3rd summand always 0. Companion **M-D3** (`:483`): `prescription_detail_jsonb` persists null mantra/gemstone/charity/deity because `_fetch_remedies_for_graha` never SELECTs those (real) corpus columns.
- **mi_jivanaghatana** (`mi_jivanaghatana.py:37-44`) — admissibility "Leakage Firewall" reads `disclosure_timing`/`disclosure_type`/`magnitude`/`domain_primary`/`domain_secondary` — none exist on `life_events` → firewall degenerates to "admissible iff event_date not NULL"; the shaped-predictor protections are dead code.
- **mi_pariksha** (`mi_pariksha.py:189-214`) — negative-control QA emits hardcoded placeholder scores (0.05/0.50); computed baseline never influences pass/FAIL → harness can never surface a real leakage failure.
- **ph_muhurta** (`ph_muhurta.py:82,132`) — `_DOMAIN_TO_ACTION` maps many anchors → one `action_class`; with `UNIQUE(chart_id, action_class, window_start) ON CONFLICT DO NOTHING`, same-domain anchors sharing a window collapse to one row, the rest silently dropped (`linked_anchor_id` keeps only the first). Companion **M-D7** (`:149`): `rows_inserted += 1` unconditional despite the conflicts.
- **ph_phaladesa** (`ph_phaladesa.py:181-217`) — docstring claims B.11 reads of `bodha_cdlm_cells` + `bodha_cgm_edges`; `_load_bodha_synthesis` only ever queries `bodha_msr_signals` → `b11_cdlm_link_count`/`b11_cgm_path_count` always 0; the ledger overstates what was read. Companion **M-D7** (`:98-176`): per-row INSERT loop has no savepoint → first failure aborts the txn and silently drops all remaining rows.
- **ph_suddha_sodhana** (`ph_suddha_sodhana.py:112,169`) — per-row INSERT failures swallowed → partial replace of a complete prior build; flags-load failure swallowed at debug → every anchor silently classified `clean` (opposite of the asset's purpose).
- **ph_pramana** (companion to the critical) — see C-D7-12.

---

## 5. LOW findings (grouped; one-line each)

**rows_inserted over-counting (D7) — same class across writers** (`+= len(batch)` / `+= 1` regardless of `ON CONFLICT DO NOTHING` skips or per-row rollbacks; corrupts telemetry, not count_sql): `bo_anveshana.py:765`, `bo_laksana.py:1313`, `bo_samskara.py:145` (also defeats the G3 all-failed guard), `ga_condition_writer.py:1332` (omits per-varga chart_facts rows), `ph_sankrama.py:137`, `ph_sodhana.py:87`, `mi_pramana.py:249` (phantom in-memory match count reported as inserted rows). Fix uniformly: increment by real `cur.rowcount`.

**Idempotency / shared-helper deviations (D5):** `bo_cdlm_summary.py:235` and `ga_transit_anchors.py:163` inline a raw DELETE instead of the shared `_idempotency.py` helper (functionally correct, consistency only); `bo_drishti.py:65` carries `ON CONFLICT DO NOTHING` on top of delete-then-insert (latent masker); `bg_ontology.py:944` / `bg_concordance.py:227` `DO NOTHING` (not `DO UPDATE`) so source edits never propagate on rebuild; `bg_remedies` sweep rows (`l0_remedy_corpus.py:3242`) keyed by content-hash accrete on content change; `bg_text_index.py:522` fill-forward-only (already-tagged chunks never re-evaluated on vocab change); `mi_darshana.py:237` clear omits `mimamsa_insight_embeddings` → index-suffixed ids orphan stale embeddings; `ka_sangam.py:181` stale lifetime-tier rows not cleared when a rebuild yields zero lifetime predicates.

**Dead/unused projections & branches (D3/D7):** `bo_cdlm_summary.py:105` (`top_k_rank_in_snapshot` selected, never used) and `:142` (bridge_link_count ≡ asymmetric_link_count, redundant column); `bo_drishti.py:83` (`configuration_jsonb` selected, unused); `ga_positions_writer.py:298` (dead INVARIANT branch → retrograde/combustion stored 5× redundantly); `ga_condition_writer.py:733` (`dignity_score` fact_key never emitted upstream); `ka_kalasutra.py:25,66` (MSR `deterministic_strength` read into a local that no output column consumes); `ga_sade_sati` / `ga_structural` dormant `_telemetry`/`asset_throughput` writers gated off the orchestrator path (latent contract hazard, D1).

**Inert / tautological verification (D8):** `ga_strength_writer.py:344` (`_verify_shadbala` compares `total` to the sum that defines `total` — always passes); `ga_sensitive_writer.py:968` (two-pass = byte-identical recompute, divergence impossible); `bg_ephemeris_engine` probe `service_probes.py:130,145` (defines `expected_sun_sign`/`expected_mean_node_rahu_sign` but never asserts them — Sun check passes if `calc_ut` merely doesn't raise; Rahu check is `1<=sign<=12`, always true). These probes go GREEN regardless of ephemeris correctness — the FORENSIC anchors they exist to guard are decorative.

**Misc low (D2/D3/D7/D8/other):** `query_signals.ts:167` semantic branch is dead duplicate SQL (no pgvector path); L2/L3/L4/L5 "sparse/design/reassurance notes" are unreachable because the handler always lands in catch (`query_phala_calibration.ts:389`, `query_domain_result.ts:105`, L2/L5 catch-laundering); `ka_kala_darshana.py:178` f-string ternary truncates narrative when `orb_strength` is falsy; `ka_dasha_kala/service.py:239` default `ayanamsha_id='lahiri'` ≠ canonical `'lahiri_chitrapaksha'` (latent footgun); `ka_yojaka/binder.py:50…` hardcoded `bg_transit_rules_ids` literal arrays (N.5, unverified); `mi_abhilekha.py:66` binary yes/denied classification forces every non-"yes" answer (incl. "partially", empty) to `denied`, can never emit the valid `partial` status; `mi_adhilepa.py:33` declared `_MULTIPLIER_BOUND_MIN=0.2` never enforced; `mi_sambandha.py:83` channel-vocabulary mismatch can freeze `fire_count=0` while grading `empirical`; `mi_vistara.py:7` + `export_to_bigquery.py:347` export-log INSERT targets a dropped schema and is misattributed to `mi_seva` (dead/test-only); `ph_muhurta.py:107` panchanga_score is a hardcoded proxy; `ph_muhurta.py:87` null-window rows escape the unique key; `ph_rectification engine.py:449` `lel_training_matched` stores one ayanamsha's count under an aggregate-sounding name; `ph_sodhana engine.py:135` magnitude_drift checks `confidence_high`, not the documented convergence quartile; `bg_reference` / `bg_vastu_directions` stale row-count docstrings; `ga_condition_writer.py:894` stale docstring (`dignity_status` vs real `dignity`); `ka_gochara/writer.py:94` self-test not try/except-wrapped (health-row staleness on failure).

**D7 silent-degradation (low, by-asset):** `bo_chart_gestalt.py:140` (0-row success despite target_floor=1), `bo_upaya.py:256` (neutral defaults on empty upstream), `bo_laksana.py:1429` (O3 navamsha cross-check swallowed), `ga_yoga_writer.py:990` / `ga_strength_writer.py:1606` (empty upstream → 0-row success), `ka_sangam.py:560` (broken C11 vedha query swallowed at debug → vedha_cancellation permanently disabled; paired low **D3** `ka_sangam.py:544` wrong column `transit_to_house`→`primary_house`), `ka_sangam` lifetime clear gap.

---

## 6. Prioritized remediation order

**Tier 0 — destructive / data-loss (do first, smallest blast radius to fix):**
1. **C-D2-10 mi_seva unscoped DELETE** — make count_sql NULL + skip-clean / re-scope global. Protects all users' saved preferences.

**Tier 1 — total-surface outages (high leverage, mechanical fixes):**
2. **Group H-A + criticals C-D7-5/C-D7-7 — the `_ctx.db` class (24 handlers).** Single shared edit pattern (`import { query }`, drop `_ctx.db`). Revives all of L2–L5 retrieval. Do in one sweep; add a CI smoke test that each handler returns `is_error:false` against the canonical chart.
3. **C-D3-1/2/3/4 + Groups H-B + C-D3-8/9 — broken-column handlers (~30).** Mechanical column re-maps per the findings. Pair with: surface `is_error:true` to the agent as a tool error instead of laundering to an empty bundle (D7 masking class, `tool_name_bridge.ts:100`), so future schema drift fails loud.
4. **C-D3-11 ph_nimitta `detected_at`** + savepoint-guard the loader (spine-asset outage).
5. **C-D7-12 ph_pramana LEL** (wrong table + columns + un-narrow the except).

**Tier 2 — build-breaking writer bugs:**
6. `bg_ephemeris` arity + ephe-path (crashes every real build); `ga_vargas` `_write_halt_log` arity; `ga_vastu` false debilitation assertion (hard-fails canonical builds); `ka_muhurta_seva` muhurat path.
7. Dead-detector producer/consumer chain (Group H-D: `bo_bimba` node jsonb, `bo_karanajala` dispositor + argala-fact fix, `bo_cgm_motifs`/`bo_cgm_paths`), then replace the false-green fixtures with real-producer integration tests.
8. `bo_laksana` `fact_subject` fetch (systematic salience degradation feeding all downstream layers).

**Tier 3 — fabricated values / grounding (acharya-grade correctness):**
9. `ga_sensitive` (is_day_birth / day_lord / Hora Lagna), `ga_strength` (engine attribution), `ga_sade_sati` (Aquarius fallback), `ph_rectification` (native birth-param hardcode), `mi_bhavisya` (`unspecified` outcome_claim), `ph_sankrama` (domain vocab), `ka_vighnakara` (tithi).
10. Inert verification/probes (`_verify_shadbala`, ga_sensitive two-pass, `bg_ephemeris_engine` Sun/Rahu asserts) — make the guards real or stop claiming verification.

**Tier 4 — dark-data count_sql + idempotency (cockpit truth):**
11. Surgical migrations for the D2 count gaps (`mi_kula`, `ga_nakshatra`→`ga_structural`, `ga_structural` 9 cats, `ga_panchanga` 5 cats, `ga_prashna`, `bg_reference`, `bg_yogas`, `bg_dasha_systems`, `bg_texts`, `mi_adhilepa`, `bo_samvada` re-apply 327, `bo_upaya`). Pair the clear-gap ones (`mi_kula` negative_controls) so Clear stops orphaning.
12. D5 accrete-not-replace converts (`bg_compendium_index`, `bg_rules`, `bg_transit_rules`, `bg_ontology`/`bg_concordance` DO UPDATE, `mi_darshana` embeddings clear).

**Tier 5 — low/telemetry/docstring:**
13. The `rows_inserted` over-count sweep (`cur.rowcount`), dead-projection cleanups, stale docstrings, latent footguns.

**Cross-cutting (do alongside Tier 1):** Stop the swallow-and-launder pattern. Two changes pay for themselves: (a) `tool_name_bridge`/handler catches must distinguish a thrown SQL/programming error from a genuine empty result instead of returning an empty bundle; (b) writer per-row `except → warning; continue` blocks should re-raise (or track a failed-row count and fail the substep) so the orchestrator savepoint rolls back rather than committing a partial build as green.

---

## 7. Remaining un-run tier — D9 behavioral validation

Everything above is **static** verification: column existence against `db_schema.json` / live DB, call-site ctx shapes, router mount tables, count_sql vs writer-emit reconciliation by code reading. The final tier — **D9 behavioral validation** — has not been run. D9 is a **full chart build (canonical `482012f1-710e-4a25-994a-93821f5871aa`) followed by per-asset row/count/clear/retrieval reconciliation**: build every asset, assert `count_sql(chart_id)` equals the writer's actual emitted rows for each of the 85 assets, exercise each retrieval handler against the built chart and assert `is_error:false` with non-empty results where rows exist, and run a clear→rebuild cycle to confirm delete-then-insert REPLACE semantics and no orphaned/accreted rows.

D9 should run **after** the Tier 0–2 fixes land — running it against the current tree would simply re-confirm that L1–L5 retrieval is dead and that several writers crash or silently no-op, which static analysis has already established. Once the column/ctx/router/arity fixes are in, D9 becomes the authoritative behavioral gate that the static fixes actually hold end-to-end.

---

## Appendix — dropped on synthesis

No findings were dropped as false positives. On re-reading, all 96 actionable findings hold; the disagreements between a finding and its own scope note (e.g. a table's live row count differing from a docstring's claimed count) are themselves corroborating evidence, not contradictions.

The following are intentionally **not** counted as defects (recorded `info` / verified-good, no change required), and are listed here only so the count is auditable:
- **Verified-good multi-table clear:** `assetClearSpec.ts:39-97` exemplars (bo_karanajala, bo_sangati, bo_anveshana, ph_rectification, mi_* family) clear exactly what they emit; `bo_upaya` over-clear of an empty set is harmless.
- **Verified-good idempotency/contract:** `bo_laksana` (delete-then-insert + count_sql + INSERT column existence all confirmed), `ga_structural` (D1 contract conformance, D5 scoped delete, D3 schema, D8 grounding all confirmed on the live orchestrator path), `ka_jivana_parva` (contract, count_sql, columns, grounding all confirmed).
- **By-design service assets** (NULL `target_table`/`count_sql` is correct because they write zero chart rows): `bg_ephemeris_engine` (probe-only), `bg_panchanga` (service asset, completeness via health probe), `ka_dasha_kala` (stale-but-by-design health row over an emptied table — an environment artifact, not a writer bug).
- **Clean grounding self-tests** (`bg_ephemeris`, `bg_panchanga`, `bg_remedies` build_id-unused, `ga_structural` forensic gate) — checked and clean; the canonical chart_id is correct (not the `362f9f17` phantom) wherever it appears.
