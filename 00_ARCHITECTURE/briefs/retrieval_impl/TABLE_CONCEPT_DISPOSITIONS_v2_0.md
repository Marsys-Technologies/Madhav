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
| `bg_avastha_schemes` | 35 | **SERVE gap** | Real classical reference table (5 avastha schemes, `determination_rule`, `classical_citation` columns — `platform/migrations/250_bg_dignity_reference.sql:239-256`), same migration file as the now-served `bg_dignity_reference`. `ganita_condition_get`'s `avasthas` facet (`get_avasthas.ts:59-68`) reads COMPUTED avastha-per-planet from `chart_facts`, not this reference/rules table — the rules/citations content itself is unserved. Zero references anywhere in `register_p1_reference.ts` (the file that DOES serve its sibling `bg_dignity_reference`). |
| `bg_combustion_orbs` | 8 | **SERVE gap** | Same migration file as `bg_dignity_reference`; real classical content (combustion + deep-combustion orb thresholds per graha, `BPHS`/`JP`/`PD`/`UK`/`SS` citations). Zero serving route found anywhere. |
| `bg_dignity_reference` | 9 | **SERVED-DIRECT** (carried from v1) | `platform-mcp/src/tools/register_p1_reference.ts:290` (`FROM bg_dignity_reference`) — `ref_dignity_reference_get` |
| `bg_graha_dik` | 9 | **SERVE gap** | Dig-bala (directional strength) reference table, own migration (`304_bg_graha_dik.sql`). Zero hits anywhere, including python-sidecar routers. |
| `bg_graha_naisargika_friendship` | 72 | **SERVE gap** | Natural friendship/enmity matrix, real classical content with `classical_citation` column (`250_bg_dignity_reference.sql:134-143`). Zero serving route. |
| `bg_medical_mappings` | 21 | **SERVE gap** | Own migration (`276_bg_medical_mappings.sql`); real reference content (planet↔body-part/ailment mappings per classical medical astrology). Zero serving route. |
| `bg_motion_state_thresholds` | 27 | **SERVE gap** | Same migration file as `bg_dignity_reference`; retrograde/direct/stationary speed thresholds per graha, cited. Zero serving route. |
| `bg_nakshatra_medical` | 27 | **SERVE gap** | Own migration (`277_bg_nakshatra_medical.sql`). Zero serving route. |
| `bg_prashna_fructification_rules` | 5 | **SERVE gap** | `261_bg_prashna_rules_schema.sql`. Zero serving route (prashna synthesis tool `prashna_undertaking_get` reads `ga_prashna_judgment`/`brahma_activity_ontology`, not this table). |
| `bg_prashna_lagna_methods` | 5 | **SERVE gap** | Same migration. Zero serving route. |
| `bg_prashna_significators` | 12 | **SERVE gap** | Same migration. Zero serving route. |
| `bg_prashna_special_techniques` | 3 | **SERVE gap** | Same migration. Zero serving route. |
| `bg_prashna_tajik_yogas` | 16 | **SERVE gap** | Same migration. Zero serving route. |
| `bg_shashtiamsha_deities` | 60 | **SERVE gap** | `430_bg_shashtiamsha_deities.sql` (D60 divisional-chart deities). Zero serving route. |
| `bg_transit_av_gates` | 8 | **SERVE gap** | `397_bg_transit_av_gates.sql` — Ashtakavarga kakshya/SAV gate thresholds, `classical_citation` column, comment states "Transit service reads this table on demand to gate convergence window scoring" — i.e. it likely informs the already-served `kala_gochara_windows` output as internal scoring logic, but its own rows/citations are not independently retrievable by the caller. Not classified SERVED-VIA because no served capability exposes this table's actual rows (the taxonomy's SERVED-VIA bar requires CI-verified per-concept cover in `concept_ledger`, which is still empty). |
| `bg_transit_engine` | 9 | **SERVE gap** | `266_bg_transit_tables.sql` §1 — per-graha average daily motion/period data, BPHS-cited. Zero serving route (its migration sibling `bg_transit_rules` IS served, this one isn't). |
| `bg_transit_moorti` | 27 | **SERVE gap** | `401_bg_transit_moorti.sql`. Zero serving route. |
| `bg_transit_rules` | 57 | **SERVED-DIRECT** (not previously in the 77's "corrected" set, but confirmed served this addendum) | `platform-mcp/src/tools/register_p1_reference.ts:436` (`FROM bg_transit_rules`) — `ref_transit_rules_get` |
| `bg_transit_vedha` | 33 | **SERVE gap** — **+ governance anomaly** | Real live table (confirmed via E2 DB-truth extraction), but **no `CREATE TABLE` for it exists anywhere in this repo's migration history** (`platform/supabase/migrations/`, `platform/migrations/`, including `_archive/` and `_pre_squash_schema_snapshot.psql`) — flagged for the conductor as a separate provenance gap, independent of its SERVE-gap disposition. |
| `bg_vastu_direction_remedials` | 24 | **SERVE gap** | `284_bg_vastu_directions.sql`. Zero serving route. |
| `bg_vastu_directions` | 8 | **SERVE gap** | Same migration. Zero serving route. |

### L0 — Brahmagyan (`brahma_*`, 8 tables)

| Table | Rows | Disposition | Evidence |
|---|---:|---|---|
| `brahma_activity_ontology` | 12 | **SERVED-DIRECT** | `platform-mcp/src/tools/register_p1_synthesis.ts:807` (`FROM brahma_activity_ontology`) — `prashna_undertaking_get` |
| `brahma_class_priors` | 164 | **SERVE gap** (borderline) | `387_brahma_class_priors.sql` — versioned graha×domain salience-prior weights, read by `composite_ranker.ts` "at query time" per its own migration comment (an internal ranking-computation input, not independently retrievable). Flagged as a case where reasonable readers might instead argue OPERATIONAL ("internal computation config"); the taxonomy's OPERATIONAL bucket is narrowly scoped to bookkeeping/journal/export/cosign/embedding-infra and doesn't cleanly cover "tunable ranking weights," so this addendum defaults to SERVE gap per the ruling's own bias, flagged for W2 to confirm. |
| `brahma_compendium_index` | 9538 | **SERVE gap** — **+ drift finding** | Classical-text index/table-of-contents structure (`text_id`/`topic_id` linking, per `parity_check.ts:36-37`'s design comment). `coverage_matrix.ts:383` **claims** `brahma_compendium_index` is covered by `marsys://tool/L0/query_classical_texts`, but `query_classical_texts.ts` actually queries `classical_text_chunks` (a different table) — verified, zero `FROM brahma_compendium_index` anywhere. This coverage_matrix.ts entry is a stale/incorrect assertion (a coverage-map drift defect, distinct from this table's own disposition) — flagged separately for whoever owns `coverage_matrix.ts` accuracy. |
| `brahma_dasha_systems` | 18 | **SERVE gap** | `176_l0_phase_alpha_new_content_tables.sql:31` — real classical dasha-system definitions (`computation_pseudocode`, `classical_citations`, `school`). Only reference anywhere is a design-comment in `parity_check.ts:35` (a proposed, not live, parity rule). Zero real serving route. |
| `brahma_event_ontology` | 27 | **SERVED-VIA (partial)** — flagged, not full coverage | Read at write-time for event-class validation (`platform/src/lib/lel/event_ontology_shapes.ts:205`, `lel_event_writer.ts:122` — outside the widened surface but reachable from `app/api/mcp/writes/[action]/route.ts`). Also cited as `base_rate_source` provenance in `query_predictive_anchors.ts:164` (L4 `phala_predictive_anchors_get`) — the `base_rate_by_age` VALUE is surfaced through that capability's output with citation. But the full row content (`temporal_shape`, `duration_prior`, `milestone_template`, `evidence_requirements`, `kill_switch_criteria`) has no dedicated retrieval capability. Recommend W2 add a proper `ref_event_ontology_get` for full coverage; until then this is a narrow, partial SERVED-VIA, not full concept coverage. |
| `brahma_formula_constants` | 18 | **SERVE gap** (borderline, same reasoning as `brahma_class_priors`) | `389_brahma_formula_constants.sql` — mixed CLASSICAL/NATIVE_JUDGMENT/ENGINEERING constants registry. One confirmed live reader: `platform/src/lib/build/recalibrationEnqueue.ts:90` reads the `mimamsa_recalibration_debounce_seconds` row — an internal scheduling-timing lookup, unrelated to the table's CLASSICAL-tagged rows. The classical content itself is not independently retrievable. |
| `brahma_prospective_ledger` | 7 | **SERVED-DIRECT** | `platform/src/app/api/mcp/writes/[action]/route.ts` — `prospective_ledger_list` action (real read/list path, permission-gated `view`), backed by `platform/src/lib/lel/prospective_ledger.ts:628,703` (`FROM brahma_prospective_ledger`). Caught only by a full-repo check beyond the 5-directory literal surface — the file living the query is outside the 5 named directories, but its caller (the route) is inside `platform/src/app/api/`, which is in scope. |
| `brahma_vichara_constants` | 7 | **SERVE gap** (borderline, same reasoning as the other two constants tables) | `platform/migrations/435_ga_vichara.sql:83` — "registry data, not literals" (ratification_step, ratification_clamp), DOCTRINE_CAMPAIGN_DESIGN-cited. Zero live TS reader found. |

### L2 — Bodha (`bodha_*`, 16 tables)

| Table | Rows | Disposition | Evidence |
|---|---:|---|---|
| `bodha_anomalies` | 4954 | **SERVED-DIRECT** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_contradictions.ts:137` (`FROM bodha_anomalies`, `include_anomalies` flag) — `query_contradictions` |
| `bodha_cdlm_domain_rollups` | 60 | **SERVE gap** | `226_bodha_spec_tables.sql`. Already named a "reading-impact priority" dark item in `RETRIEVAL_STRATEGY_v1_0.md` §5.3 itself. Zero serving route. |
| `bodha_cdlm_evolution_gradients` | 0 | **SERVE gap** | Same migration file; same §5.3 priority-item citation. Zero serving route, currently 0 rows on native chart. |
| `bodha_cdlm_pattern_clusters` | 10 | **SERVE gap** | Same migration file; same §5.3 citation. Zero serving route. |
| `bodha_cgm_chart_topology_summary` | 10 | **SERVED-DIRECT** | `traverse_chart_graph.ts:820` (`FROM bodha_cgm_chart_topology_summary`) — CGM tool `topology` mode |
| `bodha_cgm_edges` | 1573 | **SERVED-DIRECT** | `traverse_chart_graph.ts:529,696,1041` |
| `bodha_cgm_nodes` | 649 | **SERVED-DIRECT** | `traverse_chart_graph.ts:447,518,553,684,732,804` |
| `bodha_cgm_sub_graphs` | 10 | **SERVE gap** — **refutes the native's expectation** | See §2. Zero references anywhere in the TS codebase; only migration DDL + Python writer. |
| `bodha_contradictions` | 23 | **SERVED-DIRECT** | `query_contradictions.ts:98` (`FROM bodha_contradictions`) — `query_contradictions`; also read by `traverse_chart_graph.ts:884` (`contradictions` mode of the CGM tool) |
| `bodha_convergence` | 60 | **SERVED-DIRECT** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts:314` (`FROM bodha_convergence`) |
| `bodha_rm_chart_summary` | 10 | **SERVE gap** | `226_bodha_spec_tables.sql`. Zero serving route. |
| `bodha_rm_dasha_windowed_prescriptions` | 0 | **SERVE gap** | Same migration. Explicitly named the single highest reading-impact dark item in `RETRIEVAL_STRATEGY_v1_0.md` §5.2 itself ("the time-targeted remedy slice!"). Zero serving route, 0 rows on native chart. |
| `bodha_rm_dosha_remedy_bundles` | 0 | **SERVE gap** | Same migration. Zero serving route, 0 rows on native chart. |
| `bodha_rm_pattern_remedies` | 90 | **SERVE gap** | Same migration. Zero serving route. |
| `bodha_signal_embeddings` | 85997 | **SERVED-DIRECT** | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts` (semantic-search mode; "Requires bodha_signal_embeddings to be populated", line 290). NOTE: NOT served via the generic `vector_search` alias (see `mimamsa_insight_embeddings` row below for why that distinction matters) — served via `query_signals`'s own dedicated semantic path. |
| `bodha_triangulation` | 200 | **SERVE gap** | `392_bodha_triangulation.sql`, own dedicated migration. Named a §5.2 dark-set priority item. Zero serving route. |

### L1 — Gaṇita (`chart_*` / `ga_*` / `ganita_*`, 10 tables)

| Table | Rows | Disposition | Evidence |
|---|---:|---|---|
| `chart_facts_history` | 0 | **OPERATIONAL** | Append-only audit trail — "Every chart_facts INSERT fires a copy here. Retention: 30 days" (`platform/supabase/migrations/206_ga3_supporting_tables.sql:71-72`). No astrological concept beyond mirroring the already-served `chart_facts`. |
| `chart_facts_supersedence` | 0 | **OPERATIONAL** | Build-transition audit trail ("Records build transitions: old_build → new_build for same logical fact", same migration file, line 95). |
| `chart_grants` | 9 | **OPERATIONAL** | Access-control/permission table (`chart_grants` schema, migration 081) — read/written throughout `platform/src/app/api/clients/`, `admin/`, `charts/`, `build/` routes for chart-sharing permissions. No astrological concept. |
| `chart_panchanga` | 0 | **SERVED-DIRECT** (carried from v1) | `platform/src/lib/tools/brahma/l1/query_panchanga.ts:119` (`FROM chart_panchanga`) |
| `chart_panchanga_cache` | 0 | **SERVE gap** (not OPERATIONAL, despite the `_cache` suffix) | Per-date panchanga cache (`081_l0fr_schema.sql:60`) — a genuinely distinct concept from `chart_panchanga` (natal-only): date-parameterized panchanga lookups. Zero read/write route anywhere, including python-sidecar. Notably, a REAL date-parameterized panchanga compute service DOES exist (`platform/python-sidecar/routers/panchang.py` — `/panchanga`, `/panchanga/refresh`, `/panchanga/range` endpoints) but is not wired into `call_service_wrappers.ts` (zero references) — the same "dark service" shape already named for `ka_graha_sancara`/`ka_muhurta_seva` (GT-50). Recommend folding this table + its backing service into the same W2 dark-service-wiring lane as those two. |
| `ga_condition_composite` | 90 | **SERVE gap** | `251_ga_condition_composite.sql` — a real, substantive, actively-built unified planetary-condition rollup (dignity composite, avasthas, motion/combustion state, friendship, graha yuddha, unified 0-1 condition score, dasha-trajectory refs — 45 rows/chart×2 ayanamshas). Only references anywhere in TS are cockpit cache-clear admin tooling (`assetClearSpec.ts`), not a serving route. `ganita_condition_get`'s three facets (dignity/avasthas/karakas) all read `chart_facts` directly, not this composite rollup. Real, substantive gap — likely a valuable, higher-priority W2 wiring target given its richness. |
| `ga_prashna_judgment` | 5 | **SERVED-DIRECT** | `platform-mcp/src/tools/register_p1_synthesis.ts:764` (`FROM ga_prashna_judgment gj`) — `prashna_undertaking_get` |
| `ga_prashna_lagna` | 5 | **SERVE gap** | `289_ga_prashna_lagna.sql` — real content (prashna-lagna per method, `classical_citation` column). Zero references anywhere in the TS codebase, including comments. |
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
| `mimamsa_attribution` | 0 | **SERVE gap** | `351_mimamsa_pariksha.sql:6` — per-signal credit/blame attribution for matched predictions (`credit_blame`, `dimension` ∈ timing/magnitude/domain/falsifier/manifestation). No `leakage_status` column (schema-distinct from the GATED overlay tables) — a genuine explainability concept with no serving route. |
| `mimamsa_calibration_snapshot` | 0 | **OPERATIONAL** | Read/written only inside the portal learning-loop backend (`learning/route.ts:229,236,369` — UPDATE + admin-UI SELECT for the cosign flow), never by any MCP/retrieval capability. |
| `mimamsa_convergence_adjustment` | 1000 | **GATED** (this addendum's doctrine-extension) | See §3. |
| `mimamsa_discoveries` | 45 | **SERVE gap** | `351_mimamsa_pariksha.sql` — `discovery_class` ∈ emergent_law/contradiction_dominance/temporal_rhythm/residual_candidate, `statement` text, `evidence_refs`. Distinct from the already-served L2 `bodha_discoveries` (confirmed by reading `register_p1_synthesis.ts:665-671`'s `discResult` query, which is `FROM bodha_discoveries`, not `mimamsa_discoveries` — do not conflate the two). High research-value, zero serving route — directly relevant to CLAUDE.md §A's "research tool for astrology as a discipline" goal. |
| `mimamsa_event_provenance` | 57 | **OPERATIONAL** | `345_mimamsa_jivanaghatana.sql` — "evidence vault" for held-out validation-set bookkeeping (`held_out`, `admissible_clean`, `admissibility_reason`, `partition_seed_version`) — scientific-methodology/QA infrastructure for the calibration system's internal validity, not user-facing astrological content. |
| `mimamsa_export_log` | 0 | **OPERATIONAL** | "mi_vistara — export-integrity ledger" (`355_mimamsa_vistara.sql:1`). Pure export bookkeeping. |
| `mimamsa_fact_adjustment` | 121100 | **GATED** (pre-ruled by native) | See §3, §4. |
| `mimamsa_insight_embeddings` | 0 | **SERVE gap — flags a discrepancy with the native's own pre-ruling** | `353_mimamsa_darshana.sql:42` — 768-dim insight embeddings, ivfflat index. The native's ruling pre-classified "Embedding tables = SERVED-VIA (vector_search)" as a blanket rule. Checked against real code: `vector_search` resolves (`tool_name_bridge.ts:78`) to `marsys://tool/L0/query_classical_texts` **only** — a classical-texts corpus search, hardcoded to a different table, not a generic embedding-search alias. It does not and cannot reach `mimamsa_insight_embeddings`. (Compare `bodha_signal_embeddings`, which genuinely IS served — but via its own dedicated semantic-search code path in `query_signals.ts`, not via `vector_search`.) Reported honestly as a genuine gap rather than silently applying the blanket rule, per the task's explicit instruction that a wrong disposition is worse than an honest escalation. |
| `mimamsa_journal` | 0 | **SERVE gap** | `354_mimamsa_seva_abhilekha.sql:17` — native Q&A journal (`prompt_shown`, `native_answer`, `resulting_event_id`). Zero references anywhere in `mimamsa_outcome.ts`/`mimamsa_lel_intake.ts` (the natural homes) or anywhere else; only reference in the whole repo is cockpit cache-clear tooling. |
| `mimamsa_load_bearing` | 10 | **SERVE gap** (deliberately NOT extended to GATED) | `350_mimamsa_adhilepa.sql:95` — "which signal_id is load_bearing/supporting/redundant for conclusion_id" with a `sensitivity` score. Written by the same `mi_adhilepa.py` writer as the GATED overlay tables, but its own schema carries no `leakage_status`/`applies_to_reading` columns — it is explanatory/interpretability metadata, not raw calibration-multiplier internals. A genuine, valuable "why does this conclusion hold" concept with no serving route — recommend distinguishing it from its GATED siblings in W2, not lumping it in. |
| `mimamsa_manifestation_sets` | 384 | **SERVE gap** | `347_mimamsa_bhavisya.sql:36` — which channel/domain a frozen prediction manifested through, with `citation_ref`. Zero serving route (not read by `query_predictions.ts` or any outcome tool checked). |
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

*End of TABLE_CONCEPT_DISPOSITIONS v2.0. Predecessor `TABLE_CONCEPT_DISPOSITIONS_v1_0.md`
retained in place as historical record per governance hygiene policy — its DARK/
INTERNAL-BY-DESIGN/NEEDS-OWNER labels are superseded here, not deleted. Source evidence:
`platform/src/generated/harvest/adjudication_queue.json` (L1b, table list + row counts),
`platform/src/generated/harvest/widened_surface_rescan.json` (this addendum's mechanical
hit-detection layer), plus hand-verified migration DDL / writer source citations inline above
for every disposition this document assigns.*
