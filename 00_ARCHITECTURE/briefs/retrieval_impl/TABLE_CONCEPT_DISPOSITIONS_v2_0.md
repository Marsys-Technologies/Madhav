---
artifact: TABLE_CONCEPT_DISPOSITIONS_v2_0.md
canonical_id: TABLE_CONCEPT_DISPOSITIONS
version: 2.0
status: GENERATED + HAND-VERIFIED — W1 addendum (docs/w1-addendum-taxonomy)
supersedes: TABLE_CONCEPT_DISPOSITIONS_v1_0.md (retained in place, historical record — v1's
  DARK/INTERNAL-BY-DESIGN/NEEDS-OWNER labels are superseded by the §F gate ruling's five-state
  taxonomy; v1's own two corrections, bg_dignity_reference and chart_panchanga, are carried
  forward here verbatim under their new label, SERVED-DIRECT)
generator: platform/scripts/census/rescan_dark_tables_widened_surface.ts (mechanical hit-detection
  evidence layer only) + hand verification against migration DDL / writer source for every
  disposition call (see "Method" below)
generated_at: 2026-07-20
governing_ruling: 00_ARCHITECTURE/briefs/retrieval_impl/RULINGS_ADOPTED.md §F gate ruling
  (2026-07-19/20), amending RETRIEVAL_STRATEGY_v1_0.md §5.2 (v1.2)
---

# Table/Concept Lifecycle Dispositions v2.0 — W1 Addendum Re-scan (all 77 former-dark tables)

## 0. What changed since v1.0

The native's §F gate ruling (`RULINGS_ADOPTED.md`, adopted 2026-07-19/20) did three things
relevant to this document:

1. **Abolished the old three-way taxonomy** (SERVED / INTERNAL-BY-DESIGN / RETIRE /
   NEEDS-OWNER) in favor of a five-state taxonomy with **no unresolved terminal state**:
   **SERVED-DIRECT / SERVED-VIA / OPERATIONAL / GATED / RETIRED**. Full definitions:
   `RETRIEVAL_STRATEGY_v1_0.md` §5.2 (v1.2).
2. **Pre-ruled** `mimamsa_fact_adjustment` + `mimamsa_signal_adjustment` = **GATED** (L5
   structural seal + NO-LEAKAGE doctrine).
3. **Ordered a re-scan** with `platform-mcp/src/tools/` (and, this session's reading of the
   ruling's intent, `platform-mcp/src/resources/`, `platform/src/lib/tools/`,
   `platform/src/app/api/`) added to the scan surface, because the original L1b/L1d harvest
   scanned only `platform/src/lib/retrieval/registry/layers/**` + `synthesis/**` and missed
   two confirmed false-darks whose serving routes lived outside that scope.

This document is that re-scan. **Every one of the 77 tables below was individually
re-investigated** — not just re-labeled. Method:

- **Step 1 (mechanical):** `rescan_dark_tables_widened_surface.ts` greps the widened surface
  (`platform/src/lib/retrieval/`, `platform-mcp/src/tools/`, `platform-mcp/src/resources/`,
  `platform/src/lib/tools/`, `platform/src/app/api/`) for each table's literal name. Output:
  `platform/src/generated/harvest/widened_surface_rescan.json`. Result: **26/77 tables have
  ≥1 hit in the widened surface; 51 remain zero-hit even under the wider scan.**
- **Step 2 (hand verification, every row):** every hit was opened and read to determine
  whether it is a real `SELECT`/serving query, a write-only/admin path, a doc-comment, or a
  substring collision (e.g. the literal string `ganita_dashas` appearing only inside the
  unrelated capability name `ganita_dashas_get`). Every zero-hit table was additionally
  checked against its migration DDL (to read real column shapes / classical citations) and,
  for a subset, against `platform/python-sidecar/` (writer- vs. router-side) and a **full,
  unrestricted repo-wide grep** beyond the five specified directories — which is how
  `brahma_prospective_ledger` (served via `prospective_ledger_list` in
  `platform/src/app/api/mcp/writes/[action]/route.ts`, backed by
  `platform/src/lib/lel/prospective_ledger.ts` — a file outside the five listed directories
  but reachable from inside one of them) was caught as a genuine SERVED-DIRECT that the
  literal 5-directory scan alone would have missed too.

## 1. Headline numbers

| Disposition | Count | vs. v1.0 label |
|---|---:|---|
| **SERVED-DIRECT** | 15 | 2 carried from v1's "SERVED (corrected)"; 13 newly confirmed this addendum |
| **SERVED-VIA** | 1 | new this addendum (partial/narrow — see caveat in row) |
| **OPERATIONAL** | 13 | mostly ex-INTERNAL-BY-DESIGN, now with real evidence instead of naming-pattern guess |
| **GATED** | 4 | 2 pre-ruled by native; 2 more this session's doctrine-extension (see §3) |
| **RETIRED** | 2 | new this addendum — dead/superseded tables found during investigation |
| **Genuine SERVE gap (→ W2 dark-set)** | 42 | mostly ex-NEEDS-OWNER/INTERNAL-BY-DESIGN, reclassified with real evidence |
| **Total** | **77** | matches L1b's original DARK count exactly |

No table is left in an unresolved state. **42 of 77 (55%) are genuine, evidence-checked
coverage gaps** — a much larger number than v1.0's 2 corrections, and larger than the old
INTERNAL-BY-DESIGN naming-pattern heuristic implied (that heuristic auto-proposed 25 of the
77 as INTERNAL-BY-DESIGN on name-pattern alone; on individual re-investigation, **19 of those
25** turn out to hold real, un-served, citable astrological content — the L0 `bg_*` reference
stratum — not "no concept here").

## 2. The native's CGM-four expectation: 3 confirmed, 1 refuted

The native's ruling flagged the four CGM tables as "expected false-darks" the way
`bg_dignity_reference`/`chart_panchanga` were. **Mixed result, reported honestly:**

| Table | Verdict | Evidence |
|---|---|---|
| `bodha_cgm_nodes` | **SERVED-DIRECT — confirmed** | `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts` (30 hits: real `SELECT ... FROM bodha_cgm_nodes` at lines 447, 518, 553, 684, 732, 804; the CGM traversal tool, exposed as `get_cgm_subgraph`/`bodha_graph_subgraph_get`/`bodha_graph_traverse_get`/`cgm_graph_walk` per `registry_bridge.ts:1577` and `tool_name_bridge.ts:137`) |
| `bodha_cgm_edges` | **SERVED-DIRECT — confirmed** | same file, real `SELECT ... FROM bodha_cgm_edges` at lines 529, 696, 1041 |
| `bodha_cgm_chart_topology_summary` | **SERVED-DIRECT — confirmed** | same file, line 820: `FROM bodha_cgm_chart_topology_summary` (the tool's `topology` mode) |
| `bodha_cgm_sub_graphs` | **REFUTED — genuinely dark, not a false-dark** | Zero references anywhere in the entire TS codebase (not just the widened surface — a full unrestricted repo grep also returns zero). Only 2 references exist in the whole repo, both build-side: `platform/supabase/migrations/226_bodha_spec_tables.sql:531` (the `CREATE TABLE`) and `platform/python-sidecar/pipeline/orchestrator/writers/bo_cgm_motifs.py` (the writer). `traverse_chart_graph.ts`'s CGM tool — which DOES serve the other three CGM tables — queries `bodha_cgm_nodes`/`bodha_cgm_edges`/`bodha_cgm_chart_topology_summary` but never `bodha_cgm_sub_graphs`. This is a real, un-served concept (pre-computed chart sub-graph motifs/clusters) and the most important single correction in this document: **the native's expectation was right for 3 of the 4 siblings and wrong for the 4th** — reported honestly rather than rounded up to "confirmed." |

**Recommendation for W2:** `bodha_cgm_sub_graphs` is a natural fifth mode on the existing
CGM traversal tool (`traverse_chart_graph.ts` already has the query infrastructure for
sibling tables in the same migration) — likely a small (S) wiring item, not a new tool.

## 3. GATED — doctrine-extension beyond the two pre-ruled tables

The native pre-ruled `mimamsa_fact_adjustment` + `mimamsa_signal_adjustment` = GATED by name.
Investigating their writer (`platform/python-sidecar/pipeline/orchestrator/writers/
mi_adhilepa.py`, "mi_adhilepa — Calibration-Based Overlays + Load-Bearing Map") found it
writes **five** tables from one pass, not two: `mimamsa_signal_adjustment`,
`mimamsa_fact_adjustment`, `mimamsa_convergence_adjustment`, `mimamsa_anchor_adjustment`,
`mimamsa_load_bearing`. The first four share byte-identical schema (`multiplier`,
`raw_multiplier`, `applied_bound`, `evidence_n`, **`leakage_status`**,
**`applies_to_reading`**, `derived_from_pramana_ids`) — the same per-fact/per-signal
calibration-overlay shape, just keyed to a different origin layer (fact / signal /
kala_convergence / phala_anchors). `mimamsa_load_bearing` does **not** share this schema (no
`leakage_status`/`applies_to_reading` columns — see §4).

Per the ruling's own text ("Only a table requiring a genuinely NEW gate reason... returns to
the native" — applying an *already-cited* reason to a sibling is not a new reason), this
addendum extends GATED to the two schema-identical siblings:

- **`mimamsa_convergence_adjustment`** — GATED. Same reason (L5 structural seal +
  NO-LEAKAGE), same writer (`mi_adhilepa.py`), same public face (`mimamsa_calibration_get`,
  see §5 sanity check), same revisit condition as the two pre-ruled tables.
- **`mimamsa_anchor_adjustment`** — GATED. Same reasoning.

`mimamsa_load_bearing` is **not** extended to GATED — see §4 (genuine SERVE gap instead).

## 4. Sanity check: is `mimamsa_calibration_get` real, and does it aggregate over the GATED tables?

Task instruction: verify `mimamsa_calibration_get` exists and actually aggregates over the
withheld tables, as a check on the GATED disposition's "named served aggregate" requirement.

**Result: PARTIAL CONFIRM, with an important nuance the ruling's phrasing glosses over.**

- **Real and live, confirmed:** `mimamsa_calibration_get` resolves (`tool_name_bridge.ts:125`,
  `query_calibration: 'marsys://tool/L5/query_calibration'`) to
  `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_calibration.ts`, which runs
  real queries: `FROM mimamsa_calibration` (line 80), `FROM mimamsa_reliability` (line 89),
  `FROM mimamsa_multipliers` (line 98), `FROM mimamsa_qa_eval` (line 105).
- **But it does NOT literally aggregate over `mimamsa_fact_adjustment`/
  `mimamsa_signal_adjustment`/`mimamsa_convergence_adjustment`/`mimamsa_anchor_adjustment`.**
  Those are four *different*, similarly-named tables. Tracing the write-side data flow: the
  calibration writer (`mi_pramana.py`) computes `mimamsa_calibration`/`mimamsa_reliability`
  independently; the overlay writer (`mi_adhilepa.py`) then **applies** those already-computed
  multipliers **onto** the withheld per-fact/per-signal/per-convergence/per-anchor adjustment
  tables as overlay rows. The causal direction is calibration → overlay application, not
  overlay-rows → calibration-aggregate. So `mimamsa_calibration_get` is genuinely the correct
  and only public face for the *calibration multiplier* concept, and its existence does
  legitimately justify GATED for the four withheld tables (a real aggregate stands in for the
  concept), but the ruling's phrase "aggregates over these tables" is technically imprecise —
  the correct phrase is "is the calibration source these tables' overlay rows apply." Recorded
  here rather than silently corrected, since the underlying GATED disposition still holds on
  its merits.

## 5. RETIRED — two tables found dead during investigation (new since v1.0)

Neither v1.0 nor the original 77-count considered a RETIRED disposition for any of these
tables (that label was reserved, pre-ruling, for the already-carried-forward GT-52
`reference_*` five). This addendum found two more, independent of GT-52:

- **`ganita_dashas`** — RETIRED. A legacy, pre-`chart_dashas`-standardization dasha table
  (`platform/supabase/migrations/0001_brahma_baseline.sql:1804`, part of the pre-squash
  baseline schema). `chart_dashas` is the canonical, actively-built L1 dasha table (536,471
  rows per `L1_GANITA_CLOSURE`); `get_dashas.ts:204` reads `FROM chart_dashas`, never
  `ganita_dashas`. **Correction (independent verification, 2026-07-20):** it is false that
  zero writers insert into `ganita_dashas` — `brahmagyan/ganita/engine.py::write_dashas()`
  (lines ~364/380/397) contains three real `INSERT INTO ganita_dashas` statements, called from
  `run_ganita()` (engine.py:528). The accurate claim is that no LIVE/REACHABLE writer path
  inserts into `ganita_dashas`: `write_dashas()`/`run_ganita()` are only reachable via
  `pipeline/brahma_pipeline.py`'s `_l1_ganita()` → `run_pipeline()` → `main()`, and that module
  has zero live callers — verified directly: no `Dockerfile`, Cloud Run Job config, or
  `platform/python-sidecar/main.py` reference invokes `pipeline.brahma_pipeline` anywhere in the
  repo; the actual deployed pipeline image (`platform/python-sidecar/Dockerfile.pipeline`,
  backing the `brahma-build-pipeline-job` Cloud Run Job) has `ENTRYPOINT ["python", "-m",
  "pipeline.orchestrator.main"]` — the FROZEN orchestrator, a different module — and the
  orchestrator's registered dasha writer (`ga_writers/ga_dashas_writer.py`, GA3) writes to
  `chart_dashas`, never calling `engine.py`'s `run_ganita()`/`write_dashas()`. (A related but
  separate piece of dead code was also found: `pipeline/writers/__init__.py` imports submodules
  — `forensic_writer`, `vargas_writer`, `dashas_writer`, `t1_structural_writer`, `msr_writer`,
  `cdlm_writer`, `cgm_writer`, `rm_writer`, `ucn_digest_writer` — none of which exist on disk in
  `pipeline/writers/`, making that package unimportable; however `brahma_pipeline.py` does not
  import `pipeline.writers`, so this is corroborating dead-code evidence, not the operative
  reachability chain for `write_dashas()`.) `ganita_dashas` currently holds 0 rows on the native
  chart. The 6 widened-surface "hits" this session's mechanical scan found for `ganita_dashas`
  are all false-positive substring matches inside the unrelated capability name
  `ganita_dashas_get` (`register_p1_aliases.ts:657` etc.) — that capability is itself an alias
  for `get_dashas`, which reads `chart_dashas`, not `ganita_dashas`.
- **`ganita_graha_sthana`** — RETIRED. A PyJHora-computed positions table
  (`platform/migrations/174_ganita_graha_sthana.sql`, "Engine: PyJHora... Source:
  pyjhora_adapter.compute.compute_chart()"). The live writer for this table
  (`platform/python-sidecar/brahmagyan/ganita/graha_sthana_writer.py`) sits outside
  `pipeline/orchestrator/writers/` — the FROZEN orchestrator's registered-writer directory —
  meaning it is not part of the current build DAG. `get_positions.ts:128` reads canonical
  natal positions `FROM chart_facts`, not this table. Consistent with `RULINGS_ADOPTED.md`
  §F item 6's note that the `pyjhora_adapter` Docker build target is "dead/orphaned build
  infra... deleted" — this table is the DB-schema half of the same abandoned PyJHora
  integration path.

## 6. Full 77-table disposition table

Legend: **evidence** cites file:line for SERVED-DIRECT/VIA; the concrete OPERATIONAL/GATED/
RETIRED reason; or "no route found anywhere — genuine SERVE gap, W2 dark-set item."

### L0 — Brahmagyan (`bg_*`, 21 tables)

| Table | Rows | Disposition | Evidence |
|---|---:|---|---|
| `bg_avastha_schemes` | 35 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_avastha_schemes.ts:63` (`FROM bg_avastha_schemes`) — `query_avastha_schemes`. Test: `__tests__/query_avastha_schemes.test.ts`. |
| `bg_combustion_orbs` | 8 | **SERVED-DIRECT (W2 wired)** | Same migration file as `bg_dignity_reference`; real classical content (combustion + deep-combustion orb thresholds per graha, `BPHS`/`JP`/`PD`/`UK`/`SS` citations). Wired this W2 dark-set wiring pass: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_combustion_orbs.ts` (new capability, `marsys://tool/L0/query_combustion_orbs`), registered `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts`. Test: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/query_combustion_orbs.test.ts` (6/6 pass). |
| `bg_dignity_reference` | 9 | **SERVED-DIRECT** (carried from v1) | `platform-mcp/src/tools/register_p1_reference.ts:290` (`FROM bg_dignity_reference`) — `ref_dignity_reference_get` |
| `bg_graha_dik` | 9 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_graha_dik.ts:55` (`FROM bg_graha_dik`) — `query_graha_dik`. Test: `__tests__/query_graha_dik.test.ts`. |
| `bg_graha_naisargika_friendship` | 72 | **SERVED-DIRECT (W2 wired)** | Natural friendship/enmity matrix, real classical content with `classical_citation` column (`250_bg_dignity_reference.sql:134-143`). Wired this W2 dark-set wiring pass: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_graha_naisargika_friendship.ts` (new capability, `marsys://tool/L0/query_graha_naisargika_friendship`), registered `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts`. Test: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/query_graha_naisargika_friendship.test.ts` (6/6 pass). |
| `bg_medical_mappings` | 21 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_medical_mappings.ts:58` (`FROM bg_medical_mappings`) — `query_medical_mappings`. Test: `__tests__/query_medical_mappings.test.ts`. |
| `bg_motion_state_thresholds` | 27 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_motion_state_thresholds.ts:64` (`FROM bg_motion_state_thresholds`) — `query_motion_state_thresholds`. Test: `__tests__/query_motion_state_thresholds.test.ts`. |
| `bg_nakshatra_medical` | 27 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_nakshatra_medical.ts:56` (`FROM bg_nakshatra_medical`) — `query_nakshatra_medical`. Test: `__tests__/query_nakshatra_medical.test.ts`. |
| `bg_prashna_fructification_rules` | 5 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_fructification_rules.ts:57` (`FROM bg_prashna_fructification_rules`) — `query_prashna_fructification_rules`. Test: `__tests__/query_prashna_fructification_rules.test.ts`. |
| `bg_prashna_lagna_methods` | 5 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_lagna_methods.ts:58` (`FROM bg_prashna_lagna_methods`) — `query_prashna_lagna_methods`. Test: `__tests__/query_prashna_lagna_methods.test.ts`. |
| `bg_prashna_significators` | 12 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_significators.ts:54` (`FROM bg_prashna_significators`) — `query_prashna_significators`. Test: `__tests__/query_prashna_significators.test.ts`. |
| `bg_prashna_special_techniques` | 3 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_special_techniques.ts:53` (`FROM bg_prashna_special_techniques`) — `query_prashna_special_techniques`. Test: `__tests__/query_prashna_special_techniques.test.ts`. |
| `bg_prashna_tajik_yogas` | 16 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_tajik_yogas.ts:59` (`FROM bg_prashna_tajik_yogas`) — `query_prashna_tajik_yogas`. Test: `__tests__/query_prashna_tajik_yogas.test.ts`. |
| `bg_shashtiamsha_deities` | 60 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_shashtiamsha_deities.ts:64` (`FROM bg_shashtiamsha_deities`) — `query_shashtiamsha_deities`. Test: `__tests__/query_shashtiamsha_deities.test.ts`. |
| `bg_transit_av_gates` | 8 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_av_gates.ts:70` (`FROM bg_transit_av_gates`) — `query_transit_av_gates`, a NEW independent read-only reference path; does not touch, wrap, or modify `kala_gochara_windows`/`register_gochara_windows.ts`/`query_temporal_activation.ts`, which remain frozen-as-found per this campaign's D-5 hard constraint (kala_* internal-scoring use of this table is unaffected). Test: `__tests__/query_transit_av_gates.test.ts`. |
| `bg_transit_engine` | 9 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_engine.ts:60` (`FROM bg_transit_engine`) — `query_transit_engine`. Test: `__tests__/query_transit_engine.test.ts`. |
| `bg_transit_moorti` | 27 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_moorti.ts:68` (`FROM bg_transit_moorti`) — `query_transit_moorti`. Test: `__tests__/query_transit_moorti.test.ts`. |
| `bg_transit_rules` | 57 | **SERVED-DIRECT** (not previously in the 77's "corrected" set, but confirmed served this addendum) | `platform-mcp/src/tools/register_p1_reference.ts:436` (`FROM bg_transit_rules`) — `ref_transit_rules_get` |
| `bg_transit_vedha` | 33 | **SERVED-DIRECT (W2b wired)** — **governance anomaly still open** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_vedha.ts:75` (`FROM bg_transit_vedha`) — `query_transit_vedha`, wired directly against the live table per this pass's instruction (the missing-migration anomaly is a governance/provenance gap, not a blocker to serving). **Anomaly NOT fixed, still flagged for the conductor:** no `CREATE TABLE bg_transit_vedha` exists anywhere in this repo's migration history (`platform/supabase/migrations/`, `platform/migrations/`, `_archive/`, `_pre_squash_schema_snapshot.psql`) — confirmed again this pass, unchanged from the W1 addendum's finding. Test: `__tests__/query_transit_vedha.test.ts`. |
| `bg_vastu_direction_remedials` | 24 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_vastu_direction_remedials.ts:59` (`FROM bg_vastu_direction_remedials`) — `query_vastu_direction_remedials`. Test: `__tests__/query_vastu_direction_remedials.test.ts`. |
| `bg_vastu_directions` | 8 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_vastu_directions.ts:63` (`FROM bg_vastu_directions`) — `query_vastu_directions`. Test: `__tests__/query_vastu_directions.test.ts`. |

### L0 — Brahmagyan (`brahma_*`, 8 tables)

| Table | Rows | Disposition | Evidence |
|---|---:|---|---|
| `brahma_activity_ontology` | 12 | **SERVED-DIRECT** | `platform-mcp/src/tools/register_p1_synthesis.ts:807` (`FROM brahma_activity_ontology`) — `prashna_undertaking_get` |
| `brahma_class_priors` | 164 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_class_priors.ts:70` (`FROM brahma_class_priors`) — `query_class_priors`. The W1-addendum borderline judgment call (SERVE-gap vs. OPERATIONAL) is resolved by wiring it as a citable reference surface distinct from `composite_ranker.ts`'s internal at-query-time read — the same posture already taken for `bg_transit_av_gates`. Test: `__tests__/query_class_priors.test.ts`. |
| `brahma_compendium_index` | 9538 | **SERVED-DIRECT (W2b wired)** — **drift bug also fixed** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_compendium_index.ts:79` (`FROM brahma_compendium_index`) — `query_compendium_index`. The `coverage_matrix.ts:383` drift (claimed coverage via `query_classical_texts`, which actually queries the different `classical_text_chunks` table) is corrected in the same pass as the direct byproduct of closing this gap — `coverage_matrix.ts`'s `brahma_compendium_index` entry now points at the new `query_compendium_index` capability. Test: `__tests__/query_compendium_index.test.ts`. |
| `brahma_dasha_systems` | 18 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_dasha_systems.ts:64` (`FROM brahma_dasha_systems`) — `query_dasha_systems`. Test: `__tests__/query_dasha_systems.test.ts`. |
| `brahma_event_ontology` | 27 | **SERVED-VIA (partial)** — flagged, not full coverage | Read at write-time for event-class validation (`platform/src/lib/lel/event_ontology_shapes.ts:205`, `lel_event_writer.ts:122` — outside the widened surface but reachable from `app/api/mcp/writes/[action]/route.ts`). Also cited as `base_rate_source` provenance in `query_predictive_anchors.ts:164` (L4 `phala_predictive_anchors_get`) — the `base_rate_by_age` VALUE is surfaced through that capability's output with citation. But the full row content (`temporal_shape`, `duration_prior`, `milestone_template`, `evidence_requirements`, `kill_switch_criteria`) has no dedicated retrieval capability. Recommend W2 add a proper `ref_event_ontology_get` for full coverage; until then this is a narrow, partial SERVED-VIA, not full concept coverage. |
| `brahma_formula_constants` | 18 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_formula_constants.ts:66` (`FROM brahma_formula_constants`) — `query_formula_constants`, wired as a citable reference surface (same borderline resolution as `brahma_class_priors` above); `recalibrationEnqueue.ts`'s unrelated internal scheduling read of one ENGINEERING-tagged row is untouched. Test: `__tests__/query_formula_constants.test.ts`. |
| `brahma_prospective_ledger` | 7 | **SERVED-DIRECT** | `platform/src/app/api/mcp/writes/[action]/route.ts` — `prospective_ledger_list` action (real read/list path, permission-gated `view`), backed by `platform/src/lib/lel/prospective_ledger.ts:628,703` (`FROM brahma_prospective_ledger`). Caught only by a full-repo check beyond the 5-directory literal surface — the file living the query is outside the 5 named directories, but its caller (the route) is inside `platform/src/app/api/`, which is in scope. |
| `brahma_vichara_constants` | 7 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_vichara_constants.ts:57` (`FROM brahma_vichara_constants`) — `query_vichara_constants` (same borderline resolution as its two sibling constants tables above). Test: `__tests__/query_vichara_constants.test.ts`. |

### L2 — Bodha (`bodha_*`, 16 tables)

| Table | Rows | Disposition | Evidence |
|---|---:|---|---|
| `bodha_anomalies` | 4954 | **SERVED-DIRECT** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_contradictions.ts:137` (`FROM bodha_anomalies`, `include_anomalies` flag) — `query_contradictions` |
| `bodha_cdlm_domain_rollups` | 60 | **SERVED-DIRECT** (§6 row corrected to match §10's addendum — see below) | `query_cdlm_summary.ts`'s `tier` facet. See §10. |
| `bodha_cdlm_evolution_gradients` | 0 | **SERVED-DIRECT** (§6 row corrected to match §10's addendum — see below) | Same facet, same file. 0 rows on the live chart — served, honestly reported empty. See §10. |
| `bodha_cdlm_pattern_clusters` | 10 | **SERVED-DIRECT** (§6 row corrected to match §10's addendum — see below) | Same facet, same file. See §10. |
| `bodha_cgm_chart_topology_summary` | 10 | **SERVED-DIRECT** | `traverse_chart_graph.ts:820` (`FROM bodha_cgm_chart_topology_summary`) — CGM tool `topology` mode |
| `bodha_cgm_edges` | 1573 | **SERVED-DIRECT** | `traverse_chart_graph.ts:529,696,1041` |
| `bodha_cgm_nodes` | 649 | **SERVED-DIRECT** | `traverse_chart_graph.ts:447,518,553,684,732,804` |
| `bodha_cgm_sub_graphs` | 10 | **SERVED-DIRECT** (§6 row corrected to match §10's addendum — see below) | Via `traverse_chart_graph.ts`'s `sub_graphs` mode. See §2 for the original refutes-the-native's-expectation finding (still correct as the read at the time) and §10 for the subsequent wiring. |
| `bodha_contradictions` | 23 | **SERVED-DIRECT** | `query_contradictions.ts:98` (`FROM bodha_contradictions`) — `query_contradictions`; also read by `traverse_chart_graph.ts:884` (`contradictions` mode of the CGM tool) |
| `bodha_convergence` | 60 | **SERVED-DIRECT** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts:314` (`FROM bodha_convergence`) |
| `bodha_rm_chart_summary` | 10 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_chart_summary.ts:80` (`FROM bodha_rm_chart_summary`) — `query_rm_chart_summary`. Test: `__tests__/query_rm_chart_summary.test.ts`. |
| `bodha_rm_dasha_windowed_prescriptions` | 0 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_dasha_windowed_prescriptions.ts:94` (`FROM bodha_rm_dasha_windowed_prescriptions`) — `query_rm_dasha_windowed_prescriptions`. B.10 check performed before wiring: the table + its writer contract exist for real (FK to `bodha_rm_remedy_prescriptions`, which has 270 live rows) and are simply not yet populated for this chart — a genuine, not-yet-populated concept, not a fabrication; served with honest `empty_reason` discipline, live the moment the writer populates it. Test: `__tests__/query_rm_dasha_windowed_prescriptions.test.ts`. |
| `bodha_rm_dosha_remedy_bundles` | 0 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_dosha_remedy_bundles.ts:88` (`FROM bodha_rm_dosha_remedy_bundles`) — `query_rm_dosha_remedy_bundles`. Same B.10 empty-table honesty discipline as its dasha-windowed sibling above (0 rows on the native chart currently; served with `empty_reason`, not a fabrication). Test: `__tests__/query_rm_dosha_remedy_bundles.test.ts`. |
| `bodha_rm_pattern_remedies` | 90 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_rm_pattern_remedies.ts:73` (`FROM bodha_rm_pattern_remedies`) — `query_rm_pattern_remedies`. Test: `__tests__/query_rm_pattern_remedies.test.ts`. |
| `bodha_signal_embeddings` | 85997 | **SERVED-DIRECT** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts` (semantic-search mode; "Requires bodha_signal_embeddings to be populated", line 290). NOTE: NOT served via the generic `vector_search` alias (see `mimamsa_insight_embeddings` row below for why that distinction matters) — served via `query_signals`'s own dedicated semantic path. |
| `bodha_triangulation` | 200 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_triangulation.ts:84` (`FROM bodha_triangulation`) — `query_triangulation`. Standalone-vs-facet decision (per `DARK_SET_WIRING_PLAN_v1_0.md`'s own note): checked the FK shape first — `signal_ids` is a bare `UUID[]` with NO foreign-key constraint to `bodha_discoveries`/`bodha_msr_signals` (confirmed via migration 392's DDL), so this is wired as a standalone leaf tool, not a facet. Test: `__tests__/query_triangulation.test.ts`. |

### L1 — Gaṇita (`chart_*` / `ga_*` / `ganita_*`, 10 tables)

| Table | Rows | Disposition | Evidence |
|---|---:|---|---|
| `chart_facts_history` | 0 | **OPERATIONAL** | Append-only audit trail — "Every chart_facts INSERT fires a copy here. Retention: 30 days" (`platform/supabase/migrations/206_ga3_supporting_tables.sql:71-72`). No astrological concept beyond mirroring the already-served `chart_facts`. |
| `chart_facts_supersedence` | 0 | **OPERATIONAL** | Build-transition audit trail ("Records build transitions: old_build → new_build for same logical fact", same migration file, line 95). |
| `chart_grants` | 9 | **OPERATIONAL** | Access-control/permission table (`chart_grants` schema, migration 081) — read/written throughout `platform/src/app/api/clients/`, `admin/`, `charts/`, `build/` routes for chart-sharing permissions. No astrological concept. |
| `chart_panchanga` | 0 | **SERVED-DIRECT** (carried from v1) | `platform/src/lib/tools/brahma/l1/query_panchanga.ts:119` (`FROM chart_panchanga`) |
| `chart_panchanga_cache` | 0 | **SERVED-DIRECT (W2b wired)** — **via the real backing compute service, not the literal table** | B.10 finding this pass: `chart_panchanga_cache` itself has ZERO writer anywhere in the repo (exhaustive grep — no INSERT, no reference outside its own DDL); `panchang.py`'s own docstring says its per-chart cache design was superseded by the different, global `panchanga_daily` table (already served elsewhere). Wiring a capability against the literal dead table would always return nothing. Instead wired the real underlying compute service: `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/call_panchanga_service.ts` — `call_panchanga_service`, calling `panchang.py`'s `/api/compute/panchanga` + `/api/compute/panchanga/range` endpoints (Swiss-Ephemeris, engine-direct), the same "compute service, not a dead table" shape as `ka_graha_sancara`. Deliberately placed in L0, not L3_kala (hard constraint). Test: `__tests__/call_panchanga_service.test.ts`. |
| `ga_condition_composite` | 90 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L1_ganita/get_condition_composite.ts:82` (`FROM ga_condition_composite`) — `get_condition_composite`, exposing the full rollup (dignity composite, avasthas, motion/combustion, friendship, graha yuddha, condition_score, dasha-trajectory windows). Test: `__tests__/get_condition_composite.test.ts`. |
| `ga_prashna_judgment` | 5 | **SERVED-DIRECT** | `platform-mcp/src/tools/register_p1_synthesis.ts:764` (`FROM ga_prashna_judgment gj`) — `prashna_undertaking_get` |
| `ga_prashna_lagna` | 5 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L1_ganita/get_prashna_lagna.ts:74` (`FROM ga_prashna_lagna`) — `get_prashna_lagna`. Test: `__tests__/get_prashna_lagna.test.ts`. |
| `ganita_dashas` | 0 | **RETIRED** | See §5. |
| `ganita_graha_sthana` | 0 | **RETIRED** | See §5. |

### L3 — Kāla (`kala_*`, 3 tables)

| Table | Rows | Disposition | Evidence |
|---|---:|---|---|
| `kala_activation_predicates` | 78996 | **SERVED-DIRECT** | `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:268` (`FROM kala_activation_predicates`) — `query_temporal_activation` |
| `kala_convergence_staging` | 0 | **OPERATIONAL** | "Staging mirror (idempotent swap pattern), LIKE kala_convergence INCLUDING ALL" (`platform/migrations/brahma_kala_convergence.sql:56-58`) — a build-time double-buffer of the already-served `kala_convergence` table ("queried by kala_convergence.ts MCP tool" per that migration's own `COMMENT ON TABLE`). No independent concept. |
| `kala_gochara_windows` | 5 | **SERVED-DIRECT** | `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` — 3 real tools (active-on-date, forward date-range, adverse-only), all with `FROM kala_gochara_windows` queries. **This must_not_touch table's serving semantics were read-only inspected, never modified**, per this campaign's scope constraint (D-5 owns `kala_*` serving semantics while both campaigns are active). |

### L5 — Mīmāṃsā (`mimamsa_*`, 19 tables)

| Table | Rows | Disposition | Evidence |
|---|---:|---|---|
| `mimamsa_adjudication_log` | 0 | **OPERATIONAL** | Write path of the native's portal outcome-adjudication loop (BA-P7B, `platform/src/app/api/clients/[id]/learning/route.ts:64` INSERT, :331 LEFT JOIN) — journal/audit-log for the learning-loop backend, not an LLM-retrieval concept. |
| `mimamsa_anchor_adjustment` | 384 | **GATED** (this addendum's doctrine-extension) | See §3. |
| `mimamsa_attribution` | 0 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_attribution.ts:75` (`FROM mimamsa_attribution`) — `query_attribution`. Confirmed schema-distinct from the GATED overlay tables (no `leakage_status` column) — not extended to GATED. Test: `__tests__/query_attribution.test.ts`. |
| `mimamsa_calibration_snapshot` | 0 | **OPERATIONAL** | Read/written only inside the portal learning-loop backend (`learning/route.ts:229,236,369` — UPDATE + admin-UI SELECT for the cosign flow), never by any MCP/retrieval capability. |
| `mimamsa_convergence_adjustment` | 1000 | **GATED** (this addendum's doctrine-extension) | See §3. |
| `mimamsa_discoveries` | 45 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_mimamsa_discoveries.ts:78` (`FROM mimamsa_discoveries`) — `query_mimamsa_discoveries`, named distinctly (not `query_discoveries`) and documented in its own header to avoid conflation with the already-served L2 `bodha_discoveries`. Test: `__tests__/query_mimamsa_discoveries.test.ts`. |
| `mimamsa_event_provenance` | 57 | **OPERATIONAL** | `345_mimamsa_jivanaghatana.sql` — "evidence vault" for held-out validation-set bookkeeping (`held_out`, `admissible_clean`, `admissibility_reason`, `partition_seed_version`) — scientific-methodology/QA infrastructure for the calibration system's internal validity, not user-facing astrological content. |
| `mimamsa_export_log` | 0 | **OPERATIONAL** | "mi_vistara — export-integrity ledger" (`355_mimamsa_vistara.sql:1`). Pure export bookkeeping. |
| `mimamsa_fact_adjustment` | 121100 | **GATED** (pre-ruled by native) | See §3, §4. |
| `mimamsa_insight_embeddings` | 0 | **SERVED-DIRECT (W2b wired)** — **genuine new path, not the `vector_search` alias** | `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insight_embeddings.ts:93` (`FROM mimamsa_insight_embeddings`) — `query_insight_embeddings`. Confirms and closes the W1-addendum finding that the native's blanket "embedding tables = SERVED-VIA(vector_search)" pre-ruling does not hold here (`vector_search` resolves only to `query_classical_texts`, a different hardcoded table). Two real, non-fabricated modes: `mode=lookup` (embedding provenance, never the raw vector) and `mode=nearest` (pgvector `<=>` cosine-distance search between two already-computed embeddings — no live text-embedding-at-query-time call exists anywhere in this codebase, so an arbitrary-text-embed mode was deliberately not built, per B.10). 0 rows on the native chart currently (sibling `mimamsa_insight_units` also unpopulated) — served with honest `empty_reason`, not a fabrication. Test: `__tests__/query_insight_embeddings.test.ts`. |
| `mimamsa_journal` | 0 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_journal.ts:71` (`FROM mimamsa_journal`) — `query_journal`. Test: `__tests__/query_journal.test.ts`. |
| `mimamsa_load_bearing` | 10 | **SERVED-DIRECT (W2b wired)** — deliberately NOT GATED, distinguished from its siblings as recommended | `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_load_bearing.ts:75` (`FROM mimamsa_load_bearing`) — `query_load_bearing`, wired distinctly from the GATED `mi_adhilepa.py` overlay siblings per its schema-difference (no `leakage_status`/`applies_to_reading`). Test: `__tests__/query_load_bearing.test.ts`. |
| `mimamsa_manifestation_sets` | 384 | **SERVED-DIRECT (W2b wired)** | `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_manifestation_sets.ts:79` (`FROM mimamsa_manifestation_sets`) — `query_manifestation_sets`. Test: `__tests__/query_manifestation_sets.test.ts`. |
| `mimamsa_negative_controls` | 4 | **OPERATIONAL** | `346_mimamsa_kula.sql:36` — QA test-harness table (`known_false_basis`, `expected_score`, `last_harness_score`, `last_harness_status` ∈ pass/FAIL) — internal calibration-system self-test infrastructure, not astrological content. |
| `mimamsa_pool_contributions` | 0 | **OPERATIONAL** | `425_ba_lel_r2_2_step6_pool_contributions.sql` — explicitly documented as "capture-only for now... Nothing reads this table to serve pooled values while the flag is off" (own migration comment) — a feature-flagged, not-yet-activated capture buffer, declared not-served by design rather than an accidental gap. |
| `mimamsa_preferences` | 0 | **OPERATIONAL** | `354_mimamsa_seva_abhilekha.sql:6` — per-user UI saved-state (`saved_state`, `channel_id`). No astrological concept. |
| `mimamsa_resonance_feedback` | 0 | **OPERATIONAL** | Explicit "QUARANTINE: write ONLY to mimamsa_resonance_feedback — no join or FK to weight tables" (`learning/route.ts:260-262`) — a deliberately isolated feedback-capture ledger, write-only by design. |
| `mimamsa_signal_adjustment` | 97504 | **GATED** (pre-ruled by native) | See §3, §4. |
| `mimamsa_snapshot_cosign` | 0 | **OPERATIONAL** | Cosign ledger — native approve/revoke of a calibration snapshot (`learning/route.ts:217`, portal learning-loop Step 4). Matches the ruling's own pre-ruled class ("cosign ledgers = OPERATIONAL"). |

## 7. What this addendum did NOT do

- Did not touch `kala_*` serving semantics (read-only inspection of `register_gochara_windows.ts`
  and `query_temporal_activation.ts` to confirm existing routes — no edits).
- Did not touch `chart_facts` semantics or FROZEN orchestrator/writer logic anywhere.
- Did not populate `concept_ledger` (still 0 rows) — the per-concept CI-verified cover the
  taxonomy's SERVED-VIA bar formally requires does not exist yet; the one SERVED-VIA call in
  this document (`brahma_event_ontology`) is flagged partial/narrow precisely because that bar
  isn't met yet, not because the underlying evidence is weak.
- Did not verify the 44 tables this document could reach conclusively were the only possible
  evidence — a small number of the "borderline SERVE gap" config/constants tables
  (`brahma_class_priors`, `brahma_formula_constants`, `brahma_vichara_constants`) are flagged
  explicitly as judgment calls where a reasonable reader could argue OPERATIONAL instead; W2
  should treat those three as lower-confidence than the other 39 SERVE-gap rows.
- Did not re-run the mechanical scan against `platform/python-sidecar/routers/` exhaustively for
  every table — did so only for the tables where it materially changed the disposition
  (`chart_panchanga_cache`'s tie to the unwired `panchang.py` service).

## 8. For W2 — genuine SERVE-gap set (42 tables, ranked informally by evidenced value)

High-value (rich, already-built, zero-wiring-cost candidates):
`ga_condition_composite` (unified condition rollup), `bodha_rm_dasha_windowed_prescriptions`
(the time-targeted remedy slice, named a priority in the strategy doc itself),
`bodha_cgm_sub_graphs` (natural 5th mode on an existing, working tool), `mimamsa_discoveries`
(research-tool value), `mimamsa_load_bearing` (interpretability), `mimamsa_attribution`
(explainability), `bodha_triangulation`, `bodha_cdlm_*` (3 tables), `bodha_rm_*` (3 more),
`chart_panchanga_cache` (fold into the same dark-service wiring as `ka_graha_sancara`/
`ka_muhurta_seva` — the backing `panchang.py` sidecar service already exists).

L0 classical reference stratum (19 `bg_*` tables + `brahma_dasha_systems` +
`brahma_compendium_index`): uniformly real, citation-bearing classical content with zero
serving route — the single largest coherent gap this document found, and the strongest
evidence that the old INTERNAL-BY-DESIGN naming-pattern heuristic was systematically wrong
for this table class specifically (not just the 2 tables v1.0 caught).

Lower-confidence / judgment-call (flag for W2 triage, not auto-wire): `brahma_class_priors`,
`brahma_formula_constants`, `brahma_vichara_constants` (config/weights, arguably OPERATIONAL);
`mimamsa_journal`, `mimamsa_manifestation_sets`, `mimamsa_insight_embeddings`, `ga_prashna_lagna`
(smaller, more niche tables — real gaps, lower evidenced urgency).

---

## 9. W2 addendum (2026-07-20) — first two SERVE-gap flips, real wiring

W2's dark-set wiring lane picked its top-2 S-effort candidates from §8 and wired them for
real this pass (see `DARK_SET_WIRING_PLAN_v1_0.md`'s W2 wiring log for the fuller picture,
including the two compute-service items `ka_graha_sancara`/`ka_muhurta_seva`, which are not
rows in this table — they're compute services, not DB tables, and were always tracked in
`DARK_SET_WIRING_PLAN_v1_0.md` instead of here):

- **`bg_combustion_orbs`** (row above, §4) flipped **SERVE gap → SERVED-DIRECT**.
- **`bg_graha_naisargika_friendship`** (row above, §2) flipped **SERVE gap → SERVED-DIRECT**.

Both wired as new `CapabilityDescriptor`s in `platform/src/lib/retrieval/registry/layers/
L0_brahmagyan/` (`query_combustion_orbs.ts`, `query_graha_naisargika_friendship.ts`),
registered in that layer's `index.ts`, each with a dedicated mocked-DB unit test suite (6
tests each, all passing) plus swept by the registry-wide `chart_agnostic_gate_registry.test.ts`
invariant. Both follow the existing `query_sign_medical.ts` single-table reference-lookup
pattern exactly (no new pattern introduced).

**Running §7 table count after this addendum: SERVED-DIRECT 17 (was 15) / genuine SERVE-gap
40 (was 42).** The other 40 SERVE-gap rows in §8 are unchanged and remain open — this pass
did not attempt the higher-effort items (`ga_condition_composite`, the `bodha_*` items, the
remaining 17 L0 `bg_*`/`brahma_*` reference tables, the `mimamsa_*` research-value items).
See `DARK_SET_WIRING_PLAN_v1_0.md` for the honest still-open list.

## 10. W2 addendum, part 2 (2026-07-20) — disclosure correction: 3 more flips

The same W2 dark-set wiring lane also wired `bodha_cdlm_domain_rollups`,
`bodha_cdlm_pattern_clusters`, `bodha_cdlm_evolution_gradients`, and `bodha_cgm_sub_graphs` —
but its own report to the conductor never mentioned these four, and this document (§2/§4 above)
simultaneously still listed `bodha_cgm_sub_graphs` as a confirmed genuine gap with no note that
it had been closed. The W2 phase-1 independent verifier caught the discrepancy via `git diff`
(all four real, DB-backed, tested — 50/50 relevant tests pass under independent re-run).
Corrected here rather than left standing:

- **`bodha_cdlm_domain_rollups`** (§4/line 238) flipped **SERVE gap → SERVED-DIRECT** — via
  `query_cdlm_summary.ts`'s new `tier` facet. `platform/src/lib/retrieval/registry/layers/
  L2_bodha/query_cdlm_summary.ts`.
- **`bodha_cdlm_pattern_clusters`** (§4/line 240) flipped **SERVE gap → SERVED-DIRECT** — same
  facet, same file.
- **`bodha_cdlm_evolution_gradients`** (§4/line 239) flipped **SERVE gap → SERVED-DIRECT** — same
  facet, same file. (0 rows on the live chart today — served, but currently empty; the tool
  reports this honestly via its existing empty-state discipline, not a new gap.)
- **`bodha_cgm_sub_graphs`** (§2/§4, the "refutes the native's expectation" row above) flipped
  **SERVE gap → SERVED-DIRECT** — via `traverse_chart_graph.ts`'s new `sub_graphs` mode. The §2
  finding that it was genuinely un-served (not a false-dark, unlike its 3 siblings) still stands
  as the correct evidence-based READ at the time it was written — it has since been closed by
  real wiring, not retroactively reclassified as having been wrong.

**Running §7 table count after this correction: SERVED-DIRECT 19 (was 17) / genuine SERVE-gap
36 (was 40).** §8's "high-value" list should be read with these four struck through — they are
no longer open items.

---

## 11. W2b addendum (2026-07-20) — closure of the remaining 36-item SERVE-gap set

The W2b lane (`impl/wave-2b`, batch-wiring pass over this document's §8 list) wired all 36
remaining genuine SERVE-gap rows carried forward from §9/§10 above. Per-batch breakdown (all
real `CapabilityDescriptor` code + real mocked-DB unit tests + this row-level disposition
flip, no design docs substituted for implementation):

- **Batch 1 — 17 L0 `bg_*` classical reference tables** (the single largest coherent gap §8
  identified): `bg_avastha_schemes`, `bg_graha_dik`, `bg_medical_mappings`,
  `bg_motion_state_thresholds`, `bg_nakshatra_medical`, `bg_prashna_fructification_rules`,
  `bg_prashna_lagna_methods`, `bg_prashna_significators`, `bg_prashna_special_techniques`,
  `bg_prashna_tajik_yogas`, `bg_shashtiamsha_deities`, `bg_transit_av_gates`,
  `bg_transit_engine`, `bg_transit_moorti`, `bg_transit_vedha`,
  `bg_vastu_direction_remedials`, `bg_vastu_directions` — all wired, all 17/17. All follow the
  established `query_sign_medical.ts`/`query_combustion_orbs.ts`/
  `query_graha_naisargika_friendship.ts` single-table citation-bearing reference-lookup shape
  mechanically, no new pattern invented. `bg_transit_av_gates` wired as an independent
  read-only reference path that does not touch, wrap, or modify `kala_gochara_windows`'s own
  internal use of the same table (must_not_touch respected). `bg_transit_vedha`'s missing-
  migration-DDL governance anomaly is wired-around, not fixed (still flagged, unchanged).
- **Batch 2 — 5 borderline constants/config tables**: `brahma_class_priors`,
  `brahma_compendium_index`, `brahma_dasha_systems`, `brahma_formula_constants`,
  `brahma_vichara_constants` — all wired, 5/5, same pattern. `brahma_compendium_index`'s
  wiring also fixed the `coverage_matrix.ts:383` drift bug this document itself flagged (was
  pointing at `query_classical_texts`, which queries a different table) — a trivial, direct
  byproduct of closing this exact gap, not a separate fix.
- **Batch 3 — 8 substantive L1/L2 items**: `ga_condition_composite` (the unified
  planetary-condition rollup, highest single-item value per §8), `ga_prashna_lagna`,
  `bodha_triangulation` (FK-shape checked first — no FK to `bodha_discoveries`/
  `bodha_msr_signals`, wired standalone per the plan's own fallback), `bodha_rm_chart_summary`,
  `bodha_rm_dasha_windowed_prescriptions` (0 rows — B.10-checked before wiring: real writer
  contract + FK to a 270-row live table, genuine not-yet-populated concept, not a fabrication),
  `bodha_rm_dosha_remedy_bundles` (same 0-row caution, same conclusion),
  `bodha_rm_pattern_remedies`, `chart_panchanga_cache` (wired via the real backing
  `panchang.py` compute service, not the literal table — B.10 finding this pass: the literal
  table has zero writers anywhere in the repo and would always return nothing if queried
  directly) — all wired, 8/8.
- **Batch 4 — 6 L5 Mīmāṃsā research/explainability items**, deliberately distinct from the
  GATED calibration-overlay siblings: `mimamsa_attribution`, `mimamsa_discoveries` (confirmed
  distinct from L2 `bodha_discoveries`, not conflated), `mimamsa_insight_embeddings` (a
  genuinely NEW serving path — confirmed the native's blanket "embeddings = SERVED-VIA
  (vector_search)" pre-ruling does not hold here, `vector_search` only reaches
  `query_classical_texts`; two non-fabricated modes, no live text-embedding-at-query-time call
  exists anywhere in this codebase so an arbitrary-embed mode was deliberately not built),
  `mimamsa_journal`, `mimamsa_load_bearing` (confirmed schema-distinct from its GATED siblings,
  no `leakage_status`/`applies_to_reading` columns — not extended to GATED, per §3/§4's own
  caution), `mimamsa_manifestation_sets` — all wired, 6/6. `mimamsa_fact_adjustment` /
  `mimamsa_signal_adjustment` / `mimamsa_convergence_adjustment` / `mimamsa_anchor_adjustment`
  (GATED, §3) were correctly left untouched.

**Also fixed as part of this pass (real bugs found while landing this batch, not silently
worked around):**
1. A `*/`-inside-comment premature-block-comment-close bug in `call_panchanga_service.ts`
   (literal "kala_*/gochara" text) — the exact same failure class this campaign's own
   descriptor-migration lane hit twice before (STATE.md, W2 descriptor migration lane entry).
   Cascaded into ~30 TS1xxx syntax errors across the file; fixed by rewording, no semantic
   change.
2. `cost_class: 'moderate'` in two files (`call_panchanga_service.ts`,
   `query_insight_embeddings.ts`) — not a valid value of the `'cheap' | 'medium' | 'expensive'`
   union (`types.ts:391`); corrected to `'medium'`.
3. `call_panchanga_service.ts` had no test file at all — added
   `__tests__/call_panchanga_service.test.ts` (9 tests: mode=single/range dispatch, optional
   chart_id native_context hydration, required-field validation, sidecar-error surfacing,
   unknown-mode rejection, descriptor shape).
4. Four rows in §6 above (`bodha_cdlm_domain_rollups`, `bodha_cdlm_evolution_gradients`,
   `bodha_cdlm_pattern_clusters`, `bodha_cgm_sub_graphs`) were still marked "SERVE gap" in the
   table despite §10's own addendum text already documenting them as wired — a stale-row bug
   from the prior lane's pass, not introduced here. Corrected in place (pointing at §10) while
   fixing this document for this pass's own 36 flips.

**Verification (re-run after the two bugfixes above, real commands, real output):**
- `npx tsc --noEmit --skipLibCheck` (platform) — clean, 0 errors.
- `npx tsc --noEmit` (platform-mcp) — clean, 0 errors.
- `npx eslint` on all touched/created files — 0 errors (4 pre-existing `_ctx`-unused warnings
  in 4 files this lane did not touch, left as found — a concurrent session's work in this
  shared worktree).
- `npx vitest run src/lib/retrieval/registry` — **890 passed / 125 skipped, 0 failed**.
- `npx vitest run` full `platform` suite — **6172 passed / 317 skipped / 1 todo, 0 failed**
  (574 files) — no regression anywhere in the estate.
- `platform-mcp`: `npx tsc --noEmit` clean; `npx vitest run` shows 75 failing / 528 passing
  (18 failed files) — confirmed pre-existing and unrelated (zero platform-mcp files touched
  by this lane; this is the same baseline STATE.md's W2-phase-1 lane already documented and
  investigated).

**Running total after this addendum: SERVED-DIRECT 55 (was 19) / genuine SERVE-gap 0 (was
36).** All 36 items in §8's list are closed. The only remaining un-served tables in the
original 77-table W1b/W1-addendum universe are the deliberately-excluded classes: OPERATIONAL
(13), GATED (4), RETIRED (2), and SERVED-VIA (1, `brahma_event_ontology`, still partial/narrow
per its own row — full coverage recommended as a future `ref_event_ontology_get`, not part of
this lane's scope).

---

*End of TABLE_CONCEPT_DISPOSITIONS v2.0 (+ W2 addenda §9-10, W2b addendum §11). Predecessor
`TABLE_CONCEPT_DISPOSITIONS_v1_0.md` retained in place as historical record per governance
hygiene policy — its DARK/INTERNAL-BY-DESIGN/NEEDS-OWNER labels are superseded here, not
deleted. Source evidence: `platform/src/generated/harvest/adjudication_queue.json` (L1b, table
list + row counts), `platform/src/generated/harvest/widened_surface_rescan.json` (this
addendum's mechanical hit-detection layer), plus hand-verified migration DDL / writer source
citations inline above for every disposition this document assigns. §9's two flips are hand-
verified against real landed code (file:line + passing test run), not regenerated.*
