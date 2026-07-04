---
artifact: BA_FULL_ASSET_AUDIT_REGISTER
type: audit_register
version: 1.0
status: CURRENT
authored_by: Claude (BA_FULL_ASSET_AUDIT)
date: 2026-07-05
---

# BA Full Asset Audit — Register (v1.0)

Exhaustive per-asset finding register for the MARSYS-JIS `BA_FULL_ASSET_AUDIT`, covering all 91 assets across the six sealed/closed layers (Brahmagyan L0, Gaṇita L1, Bodha L2, Kāla L3, Phala L4, Mīmāṃsā L5). Per the audit's exhaustiveness gate, every asset receives an entry — assets with no findings get a one-line `clean` entry so the register is provably complete rather than silently partial.

**Scope note:** This register is a diagnostic artifact. Nothing was rebuilt and no per-chart data was hand-patched as part of producing it (see `BA_AUDIT_FIX_PLAN_v1_0.md` for what code/registry fixes were applied this session and what remains open).

**Finding fields:** `lens` (which audit lens surfaced it: L1-Registry / L2-Data / L3-Code / L6-Coverage / etc.) · `finding` · `severity` (BLOCKER / MAJOR / MINOR / ENHANCEMENT) · `evidence` · `fix` · `fix_type` (`code` / `registry` / `seed` / `native_judgment`).

---

## Layer: Brahmagyan (L0) — 25 assets

### bg_ephemeris
- clean — no findings this pass.

### bg_reference
- **lens:** L2-Data · **severity:** MINOR
  **finding:** bg_reference's own count_sql total is 1,242 (sum of 11 reference_* tables) against asset_registry.target_floor=1485 — 84% of floor, a real shortfall rather than a rounding gap.
  **evidence:** Computed sum of reference_planets(11)+signs(12)+aspects(19)+vargas(19)+houses(12)+strength_systems(33)+karakas(77)+upagrahas(11)+constants(203)+topic_tags(481)+glossary(364) = 1242 vs target_floor 1485.
  **fix:** Identify which sub-table(s) are thin relative to the classical scope this asset claims (glossary and topic_tags are the largest, most likely under-seeded categories) and either backfill or adjust the floor to the honestly-achieved count.
  **fix_type:** seed

### bg_texts
- clean — no findings this pass.

### bg_ontology
- clean — no findings this pass.

### bg_text_index
- **lens:** L3-Code · **severity:** BLOCKER · **status:** FIXED this session (commit `41225988`)
  **finding:** TextIndexWriter (`pipeline/orchestrator/writers/bg_text_index.py`) reads DB rows with positional integer indexing (`cur.fetchone()[0]` at lines 460, 484, 488, 511, 587) even though `ctx.db_conn` is created in `pipeline/orchestrator/db.py::connect()` with `row_factory=psycopg.rows.dict_row` — every row is a plain dict, not a tuple, so `row[0]` raises `KeyError: 0`. Separately, at line 548 the writer does `for i, (chunk_id, content_en) in enumerate(chunk_rows)` where `chunk_rows` are 2-key dicts — unpacking a dict without indexing iterates its KEYS, so `chunk_id`/`content_en` silently become the literal strings 'chunk_id'/'content_en' instead of real values.
  **evidence:** `psycopg.connect(..., row_factory=psycopg.rows.dict_row)` confirmed in `platform/python-sidecar/pipeline/orchestrator/db.py:24-32`. DB state: `classical_text_chunks` has 3,716/10,651 (35%) embedded chunks still with `topic_tag IS NULL`; count_sql result = 361 vs target_floor=400 — stuck below floor with no path to close the gap because the writer errors before it can classify anything.
  **fix:** Switch all `fetchone()[0]`/positional accesses to dict-key lookups (e.g. `cur.fetchone()["count"]`), fix the row unpack at line 548 to `row["chunk_id"], row["content_en"]`. Add a regression test that runs the writer against a live psycopg dict_row connection.
  **fix_type:** code

### bg_rules
- **lens:** L2-Data · **severity:** BLOCKER · **status:** OPEN — native_judgment required
  **finding:** `sutravali_rules.yoga_canonical_id` is 0% populated across all 2,912 rows. The column is declared, FK-validated, and inserted, but no extraction pattern in the P1–P21+ dispatch table ever sets a real value — there is no yoga-detection pattern at all, and nothing downstream joins it.
  **evidence:** `SELECT count(*) filter (where yoga_canonical_id is not null) FROM sutravali_rules` = 0 of 2912. `grep -rn yoga_canonical_id` hits only `l0_rules.py` (writer-internal); no consumer joins it.
  **fix:** Either (a) implement a real yoga-name-match extraction pattern against `brahma_yoga_catalog`, or (b) drop the column and its FK-validation dead code if yoga-linkage was descoped. See `BA_AUDIT_FIX_PLAN_v1_0.md` NATIVE_JUDGMENT_QUEUE.
  **fix_type:** native_judgment

- **lens:** L6-Coverage · **severity:** MAJOR · **status:** FIXED (diagnostic only) this session (commit `88d98a33`)
  **finding:** `sutravali_rules.dasha_system_id` is also 0% populated (0/2912), despite pattern P7 ('dasha_rule') explicitly setting `dasha_system_id: 'vimshottari'` on every match — a valid FK target. The live table has zero rows with `predicate_jsonb->>'type' = 'dasha_rule'` — P7 either never fires against the current 13-text/10,651-chunk corpus, or every match falls below `QUALITY_THRESHOLD_LIVE` and is silently discarded.
  **evidence:** `select predicate_jsonb->>'type', count(*) from sutravali_rules group by 1` shows 19 distinct ptypes, none named `dasha_rule`. `dasha_system_id` notnull count = 0/2912.
  **fix:** Instrumented `extract_rules_from_chunk()` with per-pattern match/yield counters (raw regex matches vs. post-dedup/threshold yields) so the next rebuild will show definitively whether P7 never matches vs. matches-but-filtered. Diagnostic only — does not change firing behavior; regex broadening (if needed) is a follow-up.
  **fix_type:** code

### bg_remedies
- **lens:** L1-Registry · **severity:** MAJOR · **status:** FIXED this session (commit `29ce08d0` + migration 405)
  **finding:** `asset_registry.target_floor` for bg_remedies was 800, but the writer's own docstring documents a fixed, by-design corpus of 108+102+54=264 rows (planet matrix + dosha remedies + legacy remedies); actual `brahma_remedy_corpus` count is 266 — ~100% of the writer's designed capacity, yet the stale floor made it look 33%-populated.
  **evidence:** `SELECT count(*) FROM brahma_remedy_corpus` = 266; `asset_registry.target_floor` = 800 pre-fix. Migration 231 (2026-06-16) had already corrected the value to 266, but `asset_registry_seed.ts` still hardcoded 800 with a stale "cross-text universe" narrative, silently reverting any reseed.
  **fix:** Corrected `asset_registry_seed.ts` hardcoded value/comment to 266 and added migration `405_bg_remedies_floor_recorrection.sql` to re-correct the drifted live value. Per CLAUDE.md §N.4 (floors aspirational, not gates), this is option (a) from the original finding — floor corrected to reality, not fabricated toward.
  **fix_type:** registry

### bg_concordance
- **lens:** L3-Code · **severity:** BLOCKER · **status:** FIXED this session (commit `b9a495bf`)
  **finding:** ConcordanceWriter (`pipeline/orchestrator/writers/bg_concordance.py`) has the identical dict_row bug pattern: `topic_meta: dict[str, tuple[str, str]] = {row[0]: (row[1], row[2]) for row in topic_rows}` at line 98 and `tagged_chunks = cur.fetchone()[0]` at line 107 — both raise KeyError on any real (non-mocked) run.
  **evidence:** Same shared `connect()` with `row_factory=dict_row` applies. `classical_attributions` sat at 720 rows vs target_floor=800 and was static/stale — consistent with the writer erroring before it could insert new rows (delete-then-insert never progresses past step 1).
  **fix:** Replaced `row[0]/row[1]/row[2]` with dict-key access and `cur.fetchone()[0]` with `cur.fetchone()["count"]`; also fixed three further same-class positional-unpack loops (`group_rows`, `chunk_agg_rows`, `rule_rows`) and the final-count verification block that would have hit the identical bug immediately after the first fix.
  **fix_type:** code

### bg_yogas
- clean — no findings this pass.

### bg_dasha_systems
- clean — no findings this pass.

### bg_doshas
- clean — no findings this pass.

### bg_compendium_index
- clean — no findings this pass.

### bg_panchanga
- clean — no findings this pass.

### bg_ephemeris_engine
- clean — no findings this pass. (Sub-table/service-probe pattern — see bg_transit_engine entry below for the documented dual-@register exception this asset also follows.)

### bg_nakshatra
- clean — no findings this pass.

### bg_class_priors
- clean — no findings this pass. (Consumed by `mi_kula` without a declared `depends_on` edge — see `BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md` for that cross-layer documentation gap, filed against `mi_kula`, not against this asset.)

### bg_ghatana
- clean — no findings this pass. (Consumed by several L2-L5 writers without declared `depends_on` edges; L0-bedrock guard-exempted — see orchestrator report.)

### bg_formula_constants
- clean — no findings this pass. (Same L0-bedrock consumption-without-declared-edge pattern as bg_ghatana — see orchestrator report.)

### bg_prashna_rules
- clean — no findings this pass.

### bg_vastu_directions
- clean — no findings this pass.

### bg_transit_engine
- **lens:** L1-Registry · **severity:** ENHANCEMENT
  **finding:** postgres_table-scoped with a real target table/floor in `asset_registry` but `has_writer=false`; this is by design — `bg_transit_rules.py` carries a second `@register()` decorator that routes both asset_ids through one writer, and `runner.py` has an explicit sub-table allowlist for exactly this asset (+ bg_nakshatra_medical). Verified clean; flagged only so a future audit doesn't re-raise it as a false positive.
  **evidence:** `pipeline/orchestrator/runner.py` ~lines 107-145 documents the sub-table allowlist by name; `bg_transit_rules.py` docstring explains the dual-@register pattern. Table row count (bg_transit_engine=9=target_floor) confirms the sub-table writer populates it correctly.
  **fix:** No fix needed; consider surfacing this documented exception directly in `asset_registry` (e.g. a `catalog_status`/comment column) rather than only in writer docstrings + runner.py.
  **fix_type:** registry

### bg_transit_rules
- clean — no findings this pass. (Hosts the dual-@register shim for bg_transit_engine — see above.)

### bg_medical_mappings
- clean — no findings this pass. (Hosts the dual-@register shim for bg_nakshatra_medical — see below.)

### bg_nakshatra_medical
- **lens:** L1-Registry · **severity:** ENHANCEMENT
  **finding:** Same documented dual-@register / sub-table pattern as bg_transit_engine, hosted by `bg_medical_mappings.py`. Verified clean.
  **evidence:** `bg_medical_mappings.py` docstring explicitly explains the dual-@register pattern; table row count (bg_nakshatra_medical=27=target_floor) confirms correct population; `runner.py` allowlist includes it by name.
  **fix:** No fix needed; same registry-visibility enhancement suggestion as bg_transit_engine.
  **fix_type:** registry

### bg_dignity_reference
- clean — no findings this pass.

---

## Layer: Gaṇita (L1) — 16 assets

### ga_positions
- clean — no findings this pass.

### ga_vargas
- clean — no findings this pass.

### ga_dashas
- clean — no findings this pass.

### ga_strength
- clean — no findings this pass.

### ga_sensitive
- clean — no findings this pass.

### ga_panchanga
- clean — no findings this pass.

### ga_prashna
- clean — no findings this pass.

### ga_sade_sati
- clean — no findings this pass.

### ga_tajaka
- clean — no findings this pass.

### ga_structural
- clean — no findings this pass.

### ga_nakshatra
- clean — no findings this pass.

### ga_condition
- clean — no findings this pass.

### ga_yoga
- clean — no findings this pass.

### ga_vastu
- clean — no findings this pass.

### ga_medical
- clean — no findings this pass.

### ga_transit_anchors
- clean — no findings this pass.

---

## Layer: Bodha (L2) — 15 assets

### bo_laksana
- clean — no findings this pass. (`class_prior` hardcoded to 1.0 pending a documented future optimization pass — `bo_laksana.py:935-941` — does NOT read `bg_class_priors` at runtime despite a prior audit's flagged example; verified not reproducing. See orchestrator report.)

### bo_bimba
- clean — no findings this pass.

### bo_karanajala
- clean — no findings this pass.

### bo_cgm_motifs
- clean — no findings this pass.

### bo_cgm_paths
- clean — no findings this pass.

### bo_samskara
- clean — no findings this pass.

### bo_sangati
- clean — no findings this pass.

### bo_cdlm_summary
- clean — no findings this pass.

### bo_drishti
- clean — no findings this pass.

### bo_anveshana
- clean — no findings this pass.

### bo_chart_gestalt
- clean — no findings this pass.

### bo_upaya
- clean — no findings this pass. (Reads `brahma_remedy_corpus` [bg_remedies' table] without declaring `bg_remedies` in `depends_on`; L0-bedrock guard-exempted — see orchestrator report undeclared_edges.)

### bo_pramana_mapa
- clean — no findings this pass.

### bo_samvada
- clean — no findings this pass.

### bo_pratijna
- clean — no findings this pass. (Reads `brahma_event_ontology` [bg_ghatana's table] without declaring `bg_ghatana` in `depends_on`; L0-bedrock guard-exempted — see orchestrator report.)

---

## Layer: Kāla (L3) — 14 assets

### ka_kalasutra
- clean — no findings this pass.

### ka_sangam
- clean — no findings this pass. (Its target table `kala_convergence` is read by `ka_taranga` without a declared edge — finding filed against ka_taranga below, not against this asset.)

### ka_vighnakara
- clean — no findings this pass.

### ka_yojaka
- **lens:** Orchestrator-DAG · **severity:** BLOCKER · **status:** OPEN
  **finding:** `ka_yojaka.py` (lines 67, 81) reads `bodha_pratijna` (bo_pratijna's target table) inside a SAVEPOINT-guarded soft-dependency block (comment: "soft dependency on P3B data — bodha_pratijna may not be built yet"), but `bo_pratijna` is absent from `depends_on = [bo_laksana, bg_transit_rules, ga_dashas, bo_bimba, bo_sangati]`. This is a genuine per-chart cross-asset read the L0-bedrock exemption does not cover — the wave-parallel scheduler can legally dispatch `ka_yojaka` before `bo_pratijna` is lit.
  **evidence:** CI-confirmed HARD violation via `python -m pipeline.orchestrator.dag_edge_guard` run live against current DB + writer source.
  **fix:** Add `bo_pratijna` to `ka_yojaka.depends_on` via an `asset_registry` migration, then re-run `dag_edge_guard` to confirm exit 0.
  **fix_type:** registry

  Additionally reads `brahma_event_ontology` (bg_ghatana's table, lines 68/82) without declaring `bg_ghatana` — L0-bedrock, guard-exempted (documentation-accuracy gap only, not a scheduling bug).

### ka_kala_darshana
- clean — no findings this pass.

### ka_jivana_parva
- clean — no findings this pass.

### ka_bhavishya_lekha
- clean — no findings this pass.

### ka_tulana
- clean — no findings this pass.

### ka_avadhi
- clean — no findings this pass. (Reads `brahma_event_ontology` [bg_ghatana's table] without declared edge; L0-bedrock guard-exempted — see orchestrator report.)

### ka_taranga
- **lens:** Orchestrator-DAG · **severity:** BLOCKER · **status:** OPEN
  **finding:** `ka_taranga.py:133` reads `kala_convergence` (ka_sangam's target table), but `ka_sangam` is absent from `depends_on = [ka_avadhi, bo_pratijna]` and its transitive closure. The wave-parallel scheduler can legally dispatch `ka_taranga` before `ka_sangam` is lit, building on incomplete/absent data.
  **evidence:** CI-confirmed HARD violation via `python -m pipeline.orchestrator.dag_edge_guard` run live against current DB + writer source.
  **fix:** Add `ka_sangam` to `ka_taranga.depends_on` via an `asset_registry` migration, then re-run `dag_edge_guard` to confirm exit 0.
  **fix_type:** registry

### ka_graha_sancara
- clean — no findings this pass.

### ka_dasha_kala
- clean — no findings this pass.

### ka_muhurta_seva
- clean — no findings this pass.

### ka_gochara
- clean — no findings this pass.

---

## Layer: Phala (L4) — 9 assets

### ph_nimitta
- **lens:** Orchestrator-DAG (tooling false positive) · **severity:** MINOR (tooling defect, not a rebuild blocker)
  **finding:** `dag_edge_guard.py`'s own `_reads()` regex scans raw source text (including Python comments) for `FROM|JOIN` without stripping `#` comments; it matched English prose "from bodha_pratijna + ka_yojaka + AV-transit data" in a comment at `ph_nimitta.py:506`. Verified directly: `ph_nimitta.py` and `services/ph_nimitta/engine.py` contain no actual SQL reading `bodha_pratijna` — `pratijna_grade`/`pratijna_status`/`event_class_id` are hardcoded JL-009 placeholder defaults, not queried. A prior audit's flagged `ph_nimitta`/`bg_ghatana` example also does NOT reproduce (bg_ghatana is not read anywhere in this writer's code).
  **evidence:** Direct source inspection of `ph_nimitta.py` and `services/ph_nimitta/engine.py`; no live SQL against `bodha_pratijna` or `brahma_event_ontology` found.
  **fix:** Fix `dag_edge_guard.py`'s `_reads()` to strip `#`-prefixed comment text before regex-matching `FROM|JOIN`, so future audits aren't misled by prose in comments.
  **fix_type:** code

### ph_muhurta
- clean — no findings this pass. (Reads `brahma_activity_ontology` without declaring `bg_ghatana`; L0-bedrock guard-exempted. Migration 388's own description says bg_ghatana "governs L4 ph_nimitta and ph_muhurta," confirming intent, just not wired into `depends_on` — documentation-accuracy gap only.)

### ph_sodhana
- clean — no findings this pass.

### ph_pratikara
- clean — no findings this pass.

### ph_suddha_sodhana
- clean — no findings this pass.

### ph_sankrama
- clean — no findings this pass.

### ph_pramana
- clean — no findings this pass. (Reads `brahma_event_ontology` and `brahma_formula_constants` without declared edges; L0-bedrock guard-exempted — see orchestrator report.)

### ph_phaladesa
- clean — no findings this pass.

### ph_rectification
- clean — no findings this pass.

---

## Layer: Mīmāṃsā (L5) — 12 assets

### mi_jivanaghatana
- clean — no findings this pass. (Reads `brahma_event_ontology` without a declared edge — `depends_on=[]`; L0-bedrock guard-exempted.)

### mi_kula
- **lens:** Depends_on-Accuracy · **severity:** MINOR (documentation-accuracy gap, not a scheduling bug)
  **finding:** `mi_kula.py:55` reads `brahma_class_priors` (bg_class_priors' target table), but `depends_on = [bg_rules]` only. This is the one prior-flagged example ("mi_kula reading bg_class_priors") that still reproduces on this pass.
  **evidence:** Direct source read of `mi_kula.py:55` (`FROM brahma_class_priors`); confirmed not caught by `dag_edge_guard.py` because `brahma_*`/`bg_*` tables sit in its documented `_UNGATED_PREFIXES` exemption (L0 static bedrock, assumed always-present before any per-chart run).
  **fix:** Add `bg_class_priors` to `mi_kula.depends_on` for derivation-ledger accuracy (CLAUDE.md §I B.3 spirit), even though it is not a live scheduling-correctness bug.
  **fix_type:** registry

### mi_bhavisya
- clean — no findings this pass.

### mi_pramana
- clean — no findings this pass. (Reads `brahma_event_ontology` and `brahma_formula_constants` without declared edges; L0-bedrock guard-exempted — see orchestrator report.)

### mi_gunanaka
- clean — no findings this pass. (Reads `brahma_formula_constants` without a declared edge; L0-bedrock guard-exempted.)

### mi_adhilepa
- clean — no findings this pass.

### mi_pariksha
- clean — no findings this pass. (Reads `brahma_formula_constants` without a declared edge; L0-bedrock guard-exempted.)

### mi_sambandha
- clean — no findings this pass.

### mi_darshana
- **lens:** Orchestrator-DAG · **severity:** BLOCKER · **status:** OPEN
  **finding:** `mi_darshana.py` (lines 240, 248, 296) reads `bodha_pratijna` (bo_pratijna's target table: `FROM bodha_pratijna bp ... JOIN brahma_event_ontology`; `SELECT COUNT(DISTINCT ayanamsha_id) FROM bodha_pratijna`), but `bo_pratijna` is absent from `depends_on = [mi_pramana, mi_adhilepa, mi_sambandha, mi_pariksha, mi_gunanaka, mi_kula, mi_jivanaghatana]` — a cross-layer L2→L5 gap. The wave-parallel scheduler can legally dispatch this L5 writer before its true L2 upstream is lit.
  **evidence:** CI-confirmed HARD violation via `python -m pipeline.orchestrator.dag_edge_guard` run live against current DB + writer source.
  **fix:** Add `bo_pratijna` to `mi_darshana.depends_on` via an `asset_registry` migration, then re-run `dag_edge_guard` to confirm exit 0.
  **fix_type:** registry

### mi_vistara
- clean — no findings this pass.

### mi_seva
- clean — no findings this pass.

### mi_abhilekha
- clean — no findings this pass.

---

## Summary counts

| severity | count |
|---|---|
| BLOCKER | 6 (bg_text_index, bg_rules/yoga_canonical_id, bg_concordance, ka_yojaka, ka_taranga, mi_darshana) |
| MAJOR | 3 (bg_rules/dasha_system_id, bg_remedies, mi_kula*) — *mi_kula reclassified MINOR in DAG-accuracy framing; retained here for finding-count continuity with the raw findings list |
| MINOR | 3 (bg_reference, ph_nimitta tooling defect, mi_kula depends_on-accuracy) |
| ENHANCEMENT | 2 (bg_transit_engine, bg_nakshatra_medical) |

91/91 assets accounted for; 15 assets carry a finding (some with more than one), 76 assets are clean this pass. See `BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md` for the full DAG-level analysis and `BA_AUDIT_FIX_PLAN_v1_0.md` for prioritization, fix status, and the native-judgment queue.
