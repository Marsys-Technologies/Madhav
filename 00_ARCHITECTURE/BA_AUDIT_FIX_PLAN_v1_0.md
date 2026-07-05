---
artifact: BA_AUDIT_FIX_PLAN
type: audit_fix_plan
version: 1.0
status: CURRENT
authored_by: Claude (BA_FULL_ASSET_AUDIT session)
date: 2026-07-05
---

# BA Audit Fix Plan (v1.0)

Prioritized remediation plan for the `BA_FULL_ASSET_AUDIT`. Consumes `BA_FULL_ASSET_AUDIT_REGISTER_v1_0.md` (91-asset, 68-finding register) and `BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md` (DAG integrity + rebuild-readiness verdict).

**IMPORTANT — session-scope statement.** Nothing was rebuilt this session. No per-chart data was hand-patched. All fix-phase work was (a) source-code bug fixes to writers/services, (b) registry/seed-script corrections + accompanying SQL migration files, and (c) one diagnostic-instrumentation-only change — all committed to git on this branch. **Five of the thirteen fix commits require a migration-apply step that has not been run against the live database** — re-verified by direct live-DB query while writing this plan (see §"Fixed this session" for the per-commit breakdown). Until those migrations are applied, `asset_registry.target_floor`/`depends_on` and `phala_sodhana`'s CHECK constraint still show their pre-fix state live, even though the corrective code is committed.

---

## BLOCKERS — confirmed, NOT YET fixed (must resolve before any full six-layer rebuild)

### DAG edge-completeness (3 real HARD violations — `BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md` §2.1/§4)

The corrective migration (`406_kala_mimamsa_dag_edge_completeness.sql`) is **committed** (`c68e65c4`) but **not applied to the live DB** — re-verified this session, all three edges still show pre-fix values live.

1. **`ka_taranga` missing `ka_sangam` in `depends_on`.** Evidence: `ka_taranga.py:133` reads `kala_convergence` (ka_sangam's target table) without ka_sangam in its dependency closure. Blocks: L3 Kāla REBUILD-READY.
2. **`ka_yojaka` missing `bo_pratijna`/`bg_ghatana` in `depends_on`.** Evidence: `ka_yojaka.py:67,81` reads `bodha_pratijna`/`brahma_event_ontology` inside a SAVEPOINT-guarded soft-dependency block, neither declared. Blocks: L3 Kāla REBUILD-READY.
3. **`mi_darshana` missing `bo_pratijna` in `depends_on`.** Evidence: `mi_darshana.py:240,248,296` reads `bodha_pratijna` (cross-layer L2→L5) without it declared. Blocks: L5 Mīmāṃsā REBUILD-READY.

**Action:** run migration `406_kala_mimamsa_dag_edge_completeness.sql` against the live database, then re-run `python -m pipeline.orchestrator.dag_edge_guard` to confirm exit 0. Only then is global REBUILD-READY = YES per the orchestrator report.

### Data-completeness / correctness BLOCKERs (confirmed, code-level, not yet touched this session)

4. **`ga_sade_sati` — `natal_facts` scaffold is a hardcoded-False/`'PENDING_*'` constant, never enriched from GA4/GA6/GA7/GA8** despite the writer gating its own build on those tables' presence and stamping `verification_pass_status='two_pass_verified'` on the result. Needs real dispositor/tara-bala/argala/dasha-lord lookups wired in. `fix_type: code`.
5. **`bo_pramana_mapa` (embedding-count facet) — scorecard reports `embedding_count=66816` while live `bodha_signal_embeddings=13383`** (22% of signals). The underlying writer bug (`bo_samskara`'s `_embed_batch` silently dropping a whole ayanamsha on exception) is now fixed (`a8a786a2`, PARTIALLY — see below), but the scorecard itself still needs `bo_pramana_mapa` re-run to refresh once the embeddings are backfilled — that re-run is a rebuild action, explicitly out of scope this session. `fix_type: code` (rerun after ayanamsha backfill).
6. **`ka_vighnakara`/`ka_kala_darshana`/`ka_bhavishya_lekha` — all 0 rows live for Abhinandan** despite `kala_convergence` (71 rows) existing to feed them, and `asset_throughput` still claiming stale nonzero historical counts. Re-run in DAG order once diagnosed; add a post-build integrity check that fails the build if convergence rows exist but the derived table is empty. `fix_type: dag` (rebuild action, out of scope).
7. **`ka_sangam`/`ka_vighnakara`/`ka_kalasutra`/`ka_kala_darshana`/`ka_bhavishya_lekha`/`ka_avadhi` — `asset_throughput.rows_written` is stale/inflated** relative to live target tables for 6 of 14 Kāla assets (e.g. `ka_kalasutra` claims 66,816 vs live 13,383). Treat `asset_throughput` as informational only (count_sql is the source of truth per CLAUDE.md §N.4); add a drift check at build close. `fix_type: dag`.
8. **`ph_nimitta` — posterior model (`compute_posterior`) fed entirely from hardcoded literal defaults**, collapsing `confidence_high`/`posterior` to a single constant (0.211) across 100% of an entire chart's anchors. Needs real `bodha_pratijna`/`ka_yojaka`/AV-transit-gate wiring. `fix_type: code`.
9. **`ph_pratikara` — `phala_mitigation` has 642 stale rows (100% `afflicting_graha='saturn'`)** while its source table `kala_obstruction` is now 0 rows live — a stale aggregate never rebuilt after upstream emptied. `fix_type: code` (rebuild action).
10. **`ph_phaladesa` — stale relative to current `phala_anchors`** (career anchor_count=66/transition=270 in the aggregate vs. 22/78 live) — same stale-aggregate class as #9. `fix_type: code` (rebuild action).
11. **`ph_rectification` — hardcodes the ORIGINAL native's (Abhisek Mohanty) 19-event life log + dasha-lord natal sign positions as module constants**, so every OTHER chart's rectification scan (including Abhinandan's) is scored against the wrong native's biography, structurally incapable of discriminating any candidate. `fix_type: code`.
12. **`mi_jivanaghatana` — YAML-parse silent-drop content gap.** Code-side instrumentation (skip-count logging) is now FIXED (`d8dc7ed0`), but the underlying malformed YAML in `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (33 of 63 blocks, unquoted colons in narrative text) was deliberately **not** hand-edited this session (altering a versioned canonical fact artifact requires native review + version bump per CLAUDE.md §B.8). 33/63 blocks still fail to parse. `fix_type: code` (content edit, native-reviewed).

---

## Fixed this session (13 commits total)

| # | asset | finding | commit SHA | migration required? | live-DB status |
|---|---|---|---|---|---|
| 1 | `bg_text_index` | L3-Code BLOCKER — positional `fetchone()[0]`/tuple-unpack against a `dict_row` cursor → `KeyError` on every real run | `41225988` | No (pure code) | **Live** — fix takes effect on next run of this writer. |
| 2 | `bg_concordance` | L3-Code BLOCKER — identical `dict_row` bug pattern | `b9a495bf` | No (pure code) | **Live.** |
| 3 | `bg_rules` (`dasha_system_id` coverage gap) | L6-Coverage MAJOR — P7 pattern never fires against the live corpus, root cause unknown | `88d98a33` | No (pure code) | **Live** — diagnostic instrumentation only; does not change firing behavior. Underlying 0%-population finding remains OPEN pending native regex-broadening decision (see NATIVE_JUDGMENT_QUEUE). |
| 4 | `bg_remedies` `target_floor` drift | L1-Registry MAJOR | `29ce08d0` + migration `405` | **Yes** | **NOT applied.** Live `asset_registry.target_floor` for `bg_remedies` still `800` (re-verified this session). |
| 5 | `ka_yojaka`/`ka_avadhi`/`ka_taranga` `depends_on` gaps | L1-Registry MAJOR ×3 (also the 3 orchestrator-report HARD blockers) | `c68e65c4` + migration `406` | **Yes** | **NOT applied.** Live `depends_on` for all 3 assets still pre-fix (re-verified this session). |
| 6 | `mi_vistara` `EXPLICIT_CLEAR_OPS` gap | L1-Registry BLOCKER — unscoped-DELETE risk on the export ledger | `e306c475` | No (TS array constant, no schema change) | **Live.** |
| 7 | `mi_bhavisya`/`mi_gunanaka`/`mi_pariksha` `family_id` | L3-Code BLOCKER ×2 — hierarchical-shrinkage pooling degenerates to n=1 per signal | `1e5cc686` | No (pure code, fixed at source `mi_bhavisya`) | **Live** for future writer runs; does not retroactively fix already-written `driving_signals` JSON on existing rows (requires rerun). |
| 8 | `ph_muhurta` `_load_condition_scores` dict-row bug | L3-Code MAJOR — flat `chart_personalization_score=0.5` fallback | `4cfdeefd` | No (pure code) | **Live.** |
| 9 | `ka_sangam` predicate ranking | L3-Code MAJOR — `ORDER BY` a never-populated column was a no-op | `b9bb8b7c` | No (pure code) | **Live.** |
| 10 | `bo_pramana_mapa` scorecard stub gates | L3-Code MAJOR — 3 hardcoded `True` pass-gates + degenerate `l1_assets_projected_count` | `7295f1ff` | No (pure code) | **Live** for future runs; existing scorecard rows still stale until `bo_pramana_mapa` is re-run. |
| 11 | `mi_pariksha` ablation/tail_only stub status | L3-Code MAJOR — non-functional stubs reported `status='pass'` | `7c91265b` | No (pure code) | **Live.** |
| 12 | `mi_jivanaghatana` LEL path + fail-loud | L5-DataEng BLOCKER + L3-Code BLOCKER (partial) | `d8dc7ed0` | No (pure code) | **Live** — path bug and fail-loud behavior fixed; content-quoting defect in the LEL markdown itself remains (see BLOCKERS #12). |
| 13 | `bo_samskara` `_embed_batch` exception isolation | L2-Data/L5-DataEng BLOCKER (partial) | `a8a786a2` | No (pure code) | **Live** for future runs — prevents a *future* silent ayanamsha drop; does **not** retroactively backfill the 4 ayanamshas already missing for Abhinandan (that backfill is a rebuild action). |
| 14 | `ph_sodhana` confidence-degenerate detector | L2-Data/L6-Coverage MAJOR | `4d4f3adc` + migration `407` | **Yes** | **NOT applied.** Live `phala_sodhana.anomaly_type` CHECK constraint still excludes the new value — the new detector will raise a constraint violation on insert until migration 407 runs. |

**Net:** 8 of 14 fixes are fully live (pure code/TS, no migration). 4 fixes are code-committed but blocked on an unapplied SQL migration (`405`, `406`, `407`). 2 are partial (mi_jivanaghatana content gap; bo_samskara/bo_pramana_mapa need a rebuild-time rerun to realize the benefit on existing data).

**Action required before any of #4, #5, #14 above can be considered actually fixed:** run migrations 405, 406, 407 against the live database (in that order is fine — they touch disjoint tables), then re-verify via direct query.

---

## MAJOR fast-follow (confirmed, not yet fixed, not a rebuild-blocker in themselves)

1. **`bg_reference` under target_floor.** count_sql total = 1,242 vs target_floor = 1,485 (84%). Glossary (364) and topic_tags (481) are the largest, most likely under-seeded categories. `fix_type: seed`.
2. **`ga_condition` — `weak_dasha_periods` permanently NULL** (`_load_dasha_periods()` returns `None` unconditionally) while `peak_dasha_periods` is fully populated — an asymmetric stub. `fix_type: code`.
3. **`ga_yoga` — `activation_dasha_periods` never written; `family_ids` sourced from an empty reference table** (`yoga_family_members` has 0 rows platform-wide). `fix_type: code`.
4. **`bo_upaya` — `resonance_score_v1` fed 5 hardcoded 0.0 inputs**, collapsing `resonance_score` to equal `weakness_score` for every graha; RM prioritization never reflects dispositor-chain weakness or dasha-timing proximity. `fix_type: code`.
5. **`bo_pratijna` — `varga_confirmation` hardcoded to `None`** for 100% of rows; the classical Parashari D9/D10-corroboration check this asset exists to adjudicate is never computed. `fix_type: code`.
6. **`ph_nimitta` — domain concentration.** Only 2 of 7 canonical domains (career, transition) have any anchors for Abhinandan; the `_SUBSYSTEM_DOMAIN` fallback map likely over-collapses `bodha_discoveries` diversity. `fix_type: code`.
7. **`ph_pramana` — `life_events` table is 0 rows platform-wide (global, not chart-scoped).** LEL v1.7 markdown was never loaded into the DB fallback table; ph_pramana's code path is correct and fails safe. `fix_type: seed` (ops/ingestion gap, not a writer bug).
8. **`mi_adhilepa` — fact-overlay slice thin/nondeterministic.** `WHERE fact_category IN ('graha','yoga') LIMIT 200`, no ORDER BY — dasha/divisional/ashtakavarga categories never receive a `mimamsa_fact_adjustment` row at all (0 rows live vs. 66,816 on the sibling `mimamsa_signal_adjustment`). `fix_type: code`.
9. **11 non-blocking `depends_on` documentation-accuracy gaps** against L0-bedrock tables (`BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md` §2.3): `mi_kula`→`bg_class_priors`, `bo_pratijna`→`bg_ghatana`, `ka_yojaka`→`bg_ghatana` (partly covered by migration 406, not yet applied), `ka_avadhi`→`bg_ghatana`, `mi_pramana`→`bg_ghatana`+`bg_formula_constants`, `mi_jivanaghatana`→`bg_ghatana`, `ph_muhurta`→`bg_ghatana`, `mi_pariksha`→`bg_formula_constants`, `mi_gunanaka`→`bg_formula_constants`, `bo_upaya`→`bg_remedies`. All guard-exempted (not scheduling bugs) but violate the derivation-ledger spirit of CLAUDE.md §I B.3. Recommend one consolidated follow-up migration. `fix_type: registry`.
10. **`dag_edge_guard.py` comment-stripping tooling defect.** `_reads()` matched English prose inside a Python comment as a false-positive `ph_nimitta`/`bo_pratijna` violation. Strip `#`-prefixed lines before regex-matching `FROM|JOIN`. `fix_type: code`.

---

## MINOR / ENHANCEMENT backlog

1. `bg_transit_engine`/`bg_nakshatra_medical` — verified-clean sub-table exception, only documented in writer docstrings + `runner.py`; add registry-visible `catalog_status` note. (ENHANCEMENT)
2. `ga_sade_sati` — row count 9,790 vs target_floor 11,019; re-baseline after the natal_facts fix lands. (MINOR)
3. `ga_tajaka` — 235 vs target_floor 240, 5 rows with empty `applicable_tajik_yogas_array`; likely edge-year boundary effect. (MINOR)
4. `ga_structural` — hand-maintained count_sql category allow-list has already silently drifted twice (migrations 364/368); consider a single source-of-truth category-ownership table. (ENHANCEMENT, `native_judgment`)
5. `ga_yoga` — `strength`/`is_partial`/`bhanga_active` NULL/false for 100% of firings; may be correctly-scoped per B.10, needs native confirmation of formula scope. (MINOR, `native_judgment`)
6. `bo_laksana`/`bo_pramana_mapa` — `verification_pass_status` vocabulary inconsistent (8 raw values, only 2 bucketed in scorecard); normalize + report full histogram. (MINOR)
7. `bo_bimba` — 2 bare `except Exception: pass` blocks swallow errors with no logging. (MINOR)
8. `bo_cdlm_summary`/`bo_chart_gestalt` — `asset_registry.target_table` NULL despite working count_sql/live tables. (MINOR)
9. `ka_sangam` — convergence_score magnitudes (0.04–0.16) sit far below downstream tier thresholds (0.45/0.70); native review of formula scale vs. threshold calibration. (MINOR, `native_judgment`)
10. `ph_muhurta` — tarabala/chandrabala/gochara hardcoded 0.5 neutral defaults (documented L4-campaign gap, gochara service wiring pending). (MINOR, `native_judgment`)
11. `ph_rectification` — sign-level scan is documented-by-design (B.10-compliant); compounds with the TRAINING_EVENTS BLOCKER above. (ENHANCEMENT, `native_judgment`)
12. `mi_seva` — registry/seed-script drift on `count_sql`/`target_floor`/`scope` for the same asset_id. (MINOR)
13. `mi_pariksha` — discovery-mining substep truncates to top-20 without sorting by `mean_credit` first — an arbitrary, not-strongest, subset. (MINOR)
14. `mi_sambandha` — dead/unused `covered_domains` local variable, harmless leftover. (ENHANCEMENT)
15. No live-`dict_row`-cursor regression test exists in the repo (`tests/test_ga3_writers.py`, `tests/l2/test_bo_a7_writers.py` both use mocked/tuple cursors) — the `bg_text_index`/`bg_concordance` bug class could silently recur. Flagged as a good follow-up; building one needs new DB test fixtures, out of scope this session.

---

## NATIVE_JUDGMENT_QUEUE

Ten findings require a native scope/formula/data decision before a deterministic code fix can be written — deferred per CLAUDE.md §L (no fabricated computation, no architecture change without native approval).

### 1. `bg_rules` — `yoga_canonical_id` 0% populated (BLOCKER, L2-Data)

**Finding:** No extraction pattern in the P1–P21+ dispatch table ever sets a real `yoga_canonical_id`; the column is declared, FK-validated, inserted, and referenced nowhere downstream.
**Options:** (a) implement a real yoga-name-match extraction pattern against `brahma_yoga_catalog` — a substantive Jyotish-domain design choice (which aliases, false-positive tolerance, corpus phrasing); (b) drop the column and its FK-validation dead code if yoga-linkage was descoped.
**Recommendation:** Lean (a) — yoga-based rule citation is core to the acharya-grade bar (§J) this project targets, and sutravali_rules exists to ground classical citations. But do not build a regex without native sign-off on which catalog entries/aliases are safe to match deterministically. If native concludes yoga-linkage isn't a near-term priority, (b) is the lower-risk immediate action (removes an actively-misleading always-null column; can be re-added later without loss).

### 2. `ga_structural` — fragile hand-maintained count_sql category allow-list (ENHANCEMENT, L1-Registry & DAG)

**Options:** (a) leave as-is, rely on migration-comment discipline; (b) derive the category list from a registered category-ownership table (single source of truth).
**Recommendation:** (b) — this has already silently drifted twice (migrations 364, 368); a third incident is a when-not-if. Low urgency, schedule as a hygiene pass.

### 3. `ga_yoga` — `strength`/`is_partial`/`bhanga_active` NULL/false for all solar/positional yogas (MINOR, L4-Astro/L6-Coverage)

**Options:** (a) widen `compute_yoga_strength_v1()`'s classical scope to cover vasi/vesi/anapha/budha_aditya/pasha/ubhayachari per a cited weighting rule; (b) confirm NULL-for-these-types is correct scoped behavior (B.10-compliant).
**Recommendation:** Needs an acharya-level read on whether these yoga types have a citable classical strength formula. Do not guess a weighting scheme.

### 4. `bo_cgm_paths` — `path_strength` is a flat 0.5 placeholder for every path (MAJOR, L4-Astro/L3-Code)

**Options:** (a) compute `path_strength` per-path from constituent edges' `computed_strength` (already present on `bodha_cgm_edges`) now that L4 Phala is sealed/closed; (b) leave deferred to a later calibration phase, but mark clearly non-authoritative in the API response.
**Recommendation:** (a) — L4 is CLOSED, the input data (`computed_strength`) already exists; there is no longer a structural reason to defer this. Low-risk to implement; flagging as native_judgment only because it changes a live-served numeric field's values.

### 5. `ka_sangam` — convergence_score scale sits far below downstream tier thresholds (MINOR, L4-Astro/L7-Optim)

**Options:** (a) recalibrate convergence_score's constituent-factor weights to top out nearer the 0.45/0.70 tier thresholds; (b) confirm 0.04–0.16 is the intended scale for this chart and lower the downstream thresholds instead.
**Recommendation:** Needs a side-by-side native review across multiple charts (not just Abhinandan) before touching either side — a one-chart sample isn't enough to recalibrate a formula used platform-wide.

### 6. `ph_muhurta` — tarabala/chandrabala/gochara hardcoded 0.5 defaults (MINOR, L4-Astro)

**Options:** (a) prioritize the gochara-service wiring + tarabala/chandrabala serve-time computation (already a documented, known L4-campaign gap); (b) leave as-is until a dedicated muhurta-quality pass.
**Recommendation:** (a), on priority — this makes `ph_muhurta` currently non-discriminating (2 near-identical composite_quality values) for any chart, which undercuts the entire asset's purpose.

### 7. `ph_rectification` — sign-level scan limitation compounding the TRAINING_EVENTS BLOCKER (ENHANCEMENT, L4-Astro)

**Options:** (a) once TRAINING_EVENTS is chart-scoped (BLOCKER #11 above), prioritize the documented D41 sub-degree tiered scorer (bhava cusps, navamsa, dasha sub-period alignment); (b) leave as sign-level only.
**Recommendation:** (a), but only after the TRAINING_EVENTS parameterization BLOCKER is resolved — no point refining a scorer that's currently scoring against the wrong native's data.

### 8. `mi_pramana` — `_score_manifestation()` hardcoded `0.5, None` for every match (MINOR, L3-Code)

**Options:** (a) wire manifestation-channel scoring to `mimamsa_manifestation_grammar`'s learned propensities once `n_support>=5` exists; (b) exclude the manifestation dimension from the weighted composite (re-normalize the other four weights) until real data exists.
**Recommendation:** (b) in the near term — averaging in a silent constant is worse than temporarily dropping the dimension; revisit (a) once enough outcome data accrues (this is explicitly the calibration-loop-maturing state CLAUDE.md §E describes for L5).

### 9. `mi_pariksha` — negative-control QA substep is a tautology that can never fail (MAJOR, L3-Code/L4-Astro)

**Options:** (a) implement the real simulations described in `mi_kula`'s `binding_spec_json` (random_uniform_window, shuffle_chart_id, backdated_signal_post_event, invert_yoga_combination) against real calibration data; (b) mark `status` as `'not_implemented'` rather than `'pass'` until implemented.
**Recommendation:** (b) immediately (cheap, stops a misleading green check), then (a) as a proper follow-up — this is exactly the kind of QA-gate-that-can't-fail defect the audit's own exhaustiveness mandate exists to catch.

### 10. `mi_abhilekha` — per-chart clear destructively wipes the native's real journal answers (MAJOR, L1-Registry/L5-DataEng)

**Options:** (a) add `mi_abhilekha: null` to `EXPLICIT_CLEAR_OPS` (mirrors the `mi_seva`/`mi_vistara` stopgap already applied this session) since the writer never repopulates `mimamsa_journal`; (b) leave as-is (current default-derive behavior).
**Recommendation:** (a) — this is irreplaceable, user-authored serve-time data, not a rebuildable artifact; every routine per-chart Mīmāṃsā clear currently destroys it with no compensating rebuild. This is the same danger class as the `mi_vistara` fix already applied this session (`e306c475`); flagged as native_judgment rather than auto-fixed only because it touches the clear-safety allowlist for a second time in one session and the native may want to review the whole allowlist at once rather than one-off patches.

---

## Summary

- **Confirmed findings:** 68 total (24 BLOCKER · 22 MAJOR · 17 MINOR · 5 ENHANCEMENT) across 45 assets with findings (46 of 91 assets clean). 4 findings were independently REFUTED during the verify pass (2 already-fixed historical bugs re-flagged stale; 2 ph_nimitta findings whose stated root-cause mechanism did not reproduce, though the underlying symptom is real — see register for full refutation rationale).
- **Fixed this session:** 14 commits. 8 are fully live (pure code/TS, no migration dependency). 4 are code/migration-committed but **not yet applied to the live database** (`bg_remedies` floor, `ka_yojaka`/`ka_avadhi`/`ka_taranga` depends_on, `ph_sodhana` CHECK constraint) — this is the single most important immediate action item below. 2 are partial fixes that prevent *future* recurrence but do not retroactively repair already-written data (`mi_jivanaghatana` LEL content, `bo_samskara` missing ayanamsha embeddings).
- **BLOCKERS still open (12 items, see §BLOCKERS above):** 3 are the DAG depends_on gaps pending migration-apply; 9 are confirmed code-level data-completeness/correctness defects not touched this session.
- **10 items queued for native judgment** (§NATIVE_JUDGMENT_QUEUE) — each with options + a recommendation, none decided or fixed without native sign-off per CLAUDE.md §L.
- **Nothing was rebuilt. No per-chart data was hand-patched.** Every change this session is a source/config diff committed to git; the DAG-edge and floor/constraint migrations additionally require a migration-apply step (not run this session) before their corresponding registry-level BLOCKERs can be considered actually resolved.

**Immediate next action (before anything else):** apply migrations `405`, `406`, `407` to the live database and re-verify via direct query (or via `dag_edge_guard.py` exit code for 406) that the fixes actually took effect — the corrected values exist only in committed SQL files as of this writing.
