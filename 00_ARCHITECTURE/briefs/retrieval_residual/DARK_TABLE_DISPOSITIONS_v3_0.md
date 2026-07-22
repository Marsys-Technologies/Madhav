---
artifact: DARK_TABLE_DISPOSITIONS_v3_0.md
canonical_id: DARK_TABLE_DISPOSITIONS
version: 3.0
status: TERMINAL — RC-09 (R-8) closure
supersedes: TABLE_CONCEPT_DISPOSITIONS_v2_0.md (retained in place, not superseded in
  substance — this document is a confirmation + terminal ledger over the SAME 51 rows,
  re-verified against current `main`, not a re-derivation)
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-09
authored_by: Claude (Native-Proxy Resolver, per brief §D.5(iv)), 2026-07-22
taxonomy: SERVED-DIRECT / SERVED-VIA / OPERATIONAL / GATED / RETIRED (five-state,
  default-bias SERVE) — RULINGS_ADOPTED.md §F gate ruling, 2026-07-19/20
verification_method: >
  Every row below traces to TABLE_CONCEPT_DISPOSITIONS_v2_0.md's hand-verified §6 table
  (file:line evidence), independently re-confirmed this session by (a) listing the actual
  files on disk at current `main` HEAD (2df42b61) for every claimed capability file,
  (b) grepping the four GATED tables across the full registry/tools/resources surface to
  confirm zero serving queries exist against them, (c) running the full L0-L5 registry test
  suite fresh (`npx vitest run src/lib/retrieval/registry` — 97 files / 987 tests passed,
  17 files / 125 tests skipped, 0 failed, at this session's HEAD). No code was written or
  changed by this residual — RC-09 confirmed the wiring already landed in earlier W1/W2/W2b
  campaign lanes is real, merged, registered, and tested; this is a documentation/disposition
  closure, not a fresh feature build.
---

# Dark Table Dispositions v3.0 — RC-09 (R-8) Terminal Closure

## 0. What this document is

`FINAL_REPORT.md` §H.6 R-8 named an open question: W2's dark-set wiring addressed the
top-priority items from the original 51 NEEDS-OWNER tables (W1 census,
`TABLE_CONCEPT_DISPOSITIONS_v1_0.md`), but no session had independently confirmed **all 51**
now carry a terminal disposition. `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` (dated 2026-07-20,
its own §9/§10/§11 addenda) already carries that confirmation in substance — its running
total lands at "genuine SERVE-gap 0 (was 36)" — but it was never re-checked against the
actual committed `main` branch by an independent pass, and R-8 was never formally closed.

This document is that independent re-check, performed as the RC-09 residual under the
Native-Proxy Resolver authority granted by `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md`
§D.5(iv): "disposition dark tables using the native's already-ruled five-state taxonomy
(SERVED-DIRECT / SERVED-VIA / OPERATIONAL / GATED / RETIRED, default-bias SERVE)."

**Result: all 51 confirmed terminal. Zero remain NEEDS-OWNER. Zero code changes were
required — every SERVE-gap flip TABLE_CONCEPT_DISPOSITIONS_v2_0.md §11 claims is real,
present, registered, and passing tests on current `main`.**

## 1. Headline count

| Disposition | Count |
|---|---:|
| SERVED-DIRECT | 40 |
| SERVED-VIA | 1 |
| OPERATIONAL | 4 |
| GATED | 4 |
| RETIRED | 2 |
| **Total** | **51** |

(This is the 51-table subset of `TABLE_CONCEPT_DISPOSITIONS_v2_0.md`'s full 77-table
universe — the 51 that were NEEDS-OWNER in the original W1 census,
`TABLE_CONCEPT_DISPOSITIONS_v1_0.md`. The other 26 of 77 were never NEEDS-OWNER — they were
already SERVED/INTERNAL-BY-DESIGN-corrected at W1 and are out of R-8's scope.)

## 2. The 51 tables, terminal disposition, rationale, evidence

Evidence column cites the capability file (verified present on disk at this session's `main`
HEAD, 2df42b61) or the specific non-serving reason. Full citation detail (file:line,
migration DDL, writer source) lives in `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §6 — this table
is the terminal disposition + one-line rationale per RC-09's brief; it does not re-derive
evidence already hand-verified there, only re-confirms it is real and merged.

### L0 — Brahmagyan (`bg_*`, 6 tables)

| Table | Disposition | Rationale | Evidence |
|---|---|---|---|
| `bg_prashna_lagna_methods` | **SERVED-DIRECT** | Real classical Prashna-lagna-method reference content, wired W2b Batch 1 as a citable lookup, same pattern as its siblings. | `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_prashna_lagna_methods.ts` (confirmed on disk, registered in layer `index.ts`) — capability `query_prashna_lagna_methods` |
| `bg_prashna_significators` | **SERVED-DIRECT** | Same class as above. | `.../L0_brahmagyan/query_prashna_significators.ts` (confirmed on disk) |
| `bg_prashna_special_techniques` | **SERVED-DIRECT** | Same class as above. | `.../L0_brahmagyan/query_prashna_special_techniques.ts` (confirmed on disk) |
| `bg_prashna_tajik_yogas` | **SERVED-DIRECT** | Same class as above. | `.../L0_brahmagyan/query_prashna_tajik_yogas.ts` (confirmed on disk) |
| `bg_transit_av_gates` | **SERVED-DIRECT** | Independent read-only reference path; deliberately does not touch/wrap `kala_gochara_windows`'s internal use of the same table (must_not_touch respected). | `.../L0_brahmagyan/query_transit_av_gates.ts` (confirmed on disk) |
| `bg_transit_engine` | **SERVED-DIRECT** | Same class as `bg_prashna_*`. | `.../L0_brahmagyan/query_transit_engine.ts` (confirmed on disk) |

### L0 — Brahmagyan (`brahma_*`, 8 tables)

| Table | Disposition | Rationale | Evidence |
|---|---|---|---|
| `brahma_activity_ontology` | **SERVED-DIRECT** | Already served (pre-existing route the W1 mechanical scan missed — outside the originally-scanned two directories). | `platform-mcp/src/tools/register_p1_synthesis.ts:807` — `prashna_undertaking_get` |
| `brahma_class_priors` | **SERVED-DIRECT** | Wired as a citable reference surface distinct from `composite_ranker.ts`'s internal at-query-time read. | `.../L0_brahmagyan/query_class_priors.ts` (confirmed on disk) — `query_class_priors` |
| `brahma_compendium_index` | **SERVED-DIRECT** | Wired; also fixed a `coverage_matrix.ts` drift bug (was pointing at the wrong table, `query_classical_texts`). | `.../L0_brahmagyan/query_compendium_index.ts` (confirmed on disk) — `query_compendium_index` |
| `brahma_dasha_systems` | **SERVED-DIRECT** | Reference dasha-system catalog, wired. | `.../L0_brahmagyan/query_dasha_systems.ts` (confirmed on disk) |
| `brahma_event_ontology` | **SERVED-VIA (partial, flagged)** | Read at write-time for event-class validation and cited as `base_rate_source` provenance in `query_predictive_anchors.ts`, but full row content has no dedicated retrieval capability yet. Honest partial, not a fabricated full-cover claim. | `platform/src/lib/lel/event_ontology_shapes.ts:205`; `platform/src/lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts:164` (base_rate_by_age surfaced with citation) |
| `brahma_formula_constants` | **SERVED-DIRECT** | Wired as citable reference (same borderline resolution as its two constants-table siblings). | `.../L0_brahmagyan/query_formula_constants.ts` (confirmed on disk) |
| `brahma_prospective_ledger` | **SERVED-DIRECT** | Real read/list path, permission-gated. | `platform/src/app/api/mcp/writes/[action]/route.ts` (`prospective_ledger_list` action) backed by `platform/src/lib/lel/prospective_ledger.ts:628,703` |
| `brahma_vichara_constants` | **SERVED-DIRECT** | Same class as `brahma_class_priors`/`brahma_formula_constants`. | `.../L0_brahmagyan/query_vichara_constants.ts` (confirmed on disk) |

### L1 — Gaṇita (`chart_*`/`ga_*`/`ganita_*`, 6 tables)

| Table | Disposition | Rationale | Evidence |
|---|---|---|---|
| `chart_grants` | **OPERATIONAL** | Access-control/permission table (chart-sharing). No astrological concept. | Read/written throughout `platform/src/app/api/clients/`, `admin/`, `charts/`, `build/` |
| `ga_condition_composite` | **SERVED-DIRECT** | Unified planetary-condition rollup (dignity, avasthas, motion/combustion, friendship, graha yuddha, condition_score, dasha-trajectory windows) — highest single-item value of the whole SERVE-gap set, wired. | `platform/src/lib/retrieval/registry/layers/L1_ganita/get_condition_composite.ts` (confirmed on disk, imported in layer `index.ts`) — `get_condition_composite` |
| `ga_prashna_judgment` | **SERVED-DIRECT** | Already served (pre-existing route). | `platform-mcp/src/tools/register_p1_synthesis.ts:764` — `prashna_undertaking_get` |
| `ga_prashna_lagna` | **SERVED-DIRECT** | Wired. | `platform/src/lib/retrieval/registry/layers/L1_ganita/get_prashna_lagna.ts` (confirmed on disk) — `get_prashna_lagna` |
| `ganita_dashas` | **RETIRED** | Legacy pre-`chart_dashas`-standardization table. No live/reachable writer path (only reachable via `pipeline/brahma_pipeline.py`, which has zero live callers — the deployed pipeline image's entrypoint is the FROZEN orchestrator, a different module, whose registered dasha writer targets `chart_dashas`). 0 rows on the native chart. `get_dashas.ts` reads `chart_dashas`, never this table. | `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §5 (full reachability-chain citation) |
| `ganita_graha_sthana` | **RETIRED** | PyJHora-computed positions table; its writer sits outside the FROZEN orchestrator's registered-writer directory (not part of the current build DAG). `get_positions.ts` reads canonical positions from `chart_facts`, not this table. Consistent with the dead `pyjhora_adapter` build-target deletion (`RULINGS_ADOPTED.md` §F item 6). | `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §5 |

### L2 — Bodha (`bodha_*`, 16 tables)

| Table | Disposition | Rationale | Evidence |
|---|---|---|---|
| `bodha_anomalies` | **SERVED-DIRECT** | Already served (pre-existing route, `include_anomalies` flag). | `platform/src/lib/retrieval/registry/layers/L2_bodha/query_contradictions.ts:137` |
| `bodha_cdlm_domain_rollups` | **SERVED-DIRECT** | Wired as `query_cdlm_summary.ts`'s `tier` facet. | `.../L2_bodha/query_cdlm_summary.ts` (confirmed on disk) |
| `bodha_cdlm_evolution_gradients` | **SERVED-DIRECT** | Same facet, same file. 0 rows on the live chart today — served, honestly reported empty (not a gap). | `.../L2_bodha/query_cdlm_summary.ts` (confirmed on disk) |
| `bodha_cdlm_pattern_clusters` | **SERVED-DIRECT** | Same facet, same file. | `.../L2_bodha/query_cdlm_summary.ts` (confirmed on disk) |
| `bodha_cgm_chart_topology_summary` | **SERVED-DIRECT** | Already served (CGM tool `topology` mode). | `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts:820` |
| `bodha_cgm_edges` | **SERVED-DIRECT** | Already served. | `.../L2_bodha/traverse_chart_graph.ts:529,696,1041` |
| `bodha_cgm_nodes` | **SERVED-DIRECT** | Already served. | `.../L2_bodha/traverse_chart_graph.ts:447,518,553,684,732,804` |
| `bodha_cgm_sub_graphs` | **SERVED-DIRECT** | Genuinely un-served at W1-addendum time (confirmed the one CGM sibling that was NOT a false-dark); wired this campaign as a natural 5th mode on the existing CGM traversal tool. | `.../L2_bodha/traverse_chart_graph.ts` `sub_graphs` mode (confirmed on disk) |
| `bodha_contradictions` | **SERVED-DIRECT** | Already served. | `.../L2_bodha/query_contradictions.ts:98`; also `traverse_chart_graph.ts:884` |
| `bodha_convergence` | **SERVED-DIRECT** | Already served. | `.../L2_bodha/query_ucd.ts:314` |
| `bodha_rm_chart_summary` | **SERVED-DIRECT** | Wired. | `.../L2_bodha/query_rm_chart_summary.ts` (confirmed on disk) |
| `bodha_rm_dasha_windowed_prescriptions` | **SERVED-DIRECT** | Wired; real writer contract + FK to a 270-row live parent table confirmed before wiring (0 rows on native chart = genuinely not-yet-populated, not fabricated — served with honest `empty_reason`). | `.../L2_bodha/query_rm_dasha_windowed_prescriptions.ts` (confirmed on disk) |
| `bodha_rm_dosha_remedy_bundles` | **SERVED-DIRECT** | Same B.10 empty-table honesty discipline as its sibling above. | `.../L2_bodha/query_rm_dosha_remedy_bundles.ts` (confirmed on disk) |
| `bodha_rm_pattern_remedies` | **SERVED-DIRECT** | Wired. | `.../L2_bodha/query_rm_pattern_remedies.ts` (confirmed on disk) |
| `bodha_signal_embeddings` | **SERVED-DIRECT** | Already served via `query_signals`'s dedicated semantic-search mode (NOT the generic `vector_search` alias). | `.../L2_bodha/query_signals.ts` line 290 |
| `bodha_triangulation` | **SERVED-DIRECT** | Wired standalone (not a facet) after confirming `signal_ids` has no FK constraint to `bodha_discoveries`/`bodha_msr_signals` — a bare `UUID[]`. | `.../L2_bodha/query_triangulation.ts` (confirmed on disk) |

### L3 — Kāla (`kala_*`, 2 tables)

| Table | Disposition | Rationale | Evidence |
|---|---|---|---|
| `kala_activation_predicates` | **SERVED-DIRECT** | Already served. | `platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:268` |
| `kala_gochara_windows` | **SERVED-DIRECT** | Already served, 3 real tools. Read-only confirmed this session — serving semantics untouched (owned by the D-4b doctrine campaign per this campaign's must_not_touch). | `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` |

### L5 — Mīmāṃsā (`mimamsa_*`, 13 tables)

| Table | Disposition | Rationale | Evidence |
|---|---|---|---|
| `mimamsa_anchor_adjustment` | **GATED** | Doctrine-extension of the native's pre-ruled `mimamsa_fact_adjustment`/`mimamsa_signal_adjustment` GATED reason (L5 structural seal + NO-LEAKAGE) — same writer (`mi_adhilepa.py`), byte-identical calibration-overlay schema (`leakage_status`, `applies_to_reading` columns), same public-face aggregate. Applying an already-cited reason to a schema-identical sibling is not a new gate reason. **Revisit condition: calibration-loop maturity or a Samīkṣā drill requirement** (`RULINGS_ADOPTED.md` §F item 3). | Grep-confirmed this session: zero serving queries against this table anywhere in `registry/`/`tools/`/`resources/`; public face `mimamsa_calibration_get` → `.../L5_mimamsa/query_calibration.ts` confirmed real (`FROM mimamsa_calibration/mimamsa_reliability/mimamsa_multipliers`) |
| `mimamsa_attribution` | **SERVED-DIRECT** | Confirmed schema-distinct from the GATED overlay tables (no `leakage_status` column) — explainability surface, wired. | `.../L5_mimamsa/query_attribution.ts` (confirmed on disk) |
| `mimamsa_convergence_adjustment` | **GATED** | Same doctrine-extension reasoning as `mimamsa_anchor_adjustment` — same writer, same schema, same revisit condition. | Grep-confirmed zero serving queries this session |
| `mimamsa_discoveries` | **SERVED-DIRECT** | Named distinctly (`query_mimamsa_discoveries`, not `query_discoveries`) to avoid conflation with L2 `bodha_discoveries`. | `.../L5_mimamsa/query_mimamsa_discoveries.ts` (confirmed on disk) |
| `mimamsa_event_provenance` | **OPERATIONAL** | Evidence vault for held-out validation-set bookkeeping (scientific-methodology/QA infrastructure for the calibration system's internal validity) — not user-facing astrological content. | `platform/supabase/migrations/345_mimamsa_jivanaghatana.sql` |
| `mimamsa_fact_adjustment` | **GATED** (native pre-ruled) | L5 structural seal + NO-LEAKAGE. Public face: `mimamsa_calibration_get`. **Revisit condition: calibration-loop maturity or a Samīkṣā drill requirement.** | `RULINGS_ADOPTED.md` §F item 3; grep-confirmed zero serving queries this session |
| `mimamsa_insight_embeddings` | **SERVED-DIRECT** | Genuine new path — confirmed the blanket "embeddings = SERVED-VIA(vector_search)" pre-ruling does not hold here (`vector_search` resolves only to `query_classical_texts`); two non-fabricated modes (lookup / nearest-cosine), no arbitrary-text-embed mode built (no live embed-at-query-time call exists in the codebase — B.10). | `.../L5_mimamsa/query_insight_embeddings.ts` (confirmed on disk) |
| `mimamsa_journal` | **SERVED-DIRECT** | Wired. | `.../L5_mimamsa/query_journal.ts` (confirmed on disk) |
| `mimamsa_load_bearing` | **SERVED-DIRECT** | Deliberately NOT GATED — confirmed schema-distinct from its `mi_adhilepa.py` overlay siblings (no `leakage_status`/`applies_to_reading` columns). | `.../L5_mimamsa/query_load_bearing.ts` (confirmed on disk; header comment explicitly distinguishes it from the GATED siblings) |
| `mimamsa_manifestation_sets` | **SERVED-DIRECT** | Wired. | `.../L5_mimamsa/query_manifestation_sets.ts` (confirmed on disk) |
| `mimamsa_negative_controls` | **OPERATIONAL** | QA test-harness table (`known_false_basis`, `expected_score`, harness pass/FAIL) — internal calibration self-test infrastructure, not astrological content. | `platform/supabase/migrations/346_mimamsa_kula.sql:36` |
| `mimamsa_preferences` | **OPERATIONAL** | Per-user UI saved-state (`saved_state`, `channel_id`). No astrological concept. | `platform/supabase/migrations/354_mimamsa_seva_abhilekha.sql:6` |
| `mimamsa_signal_adjustment` | **GATED** (native pre-ruled) | Same as `mimamsa_fact_adjustment`. **Revisit condition: calibration-loop maturity or a Samīkṣā drill requirement.** | `RULINGS_ADOPTED.md` §F item 3; grep-confirmed zero serving queries this session |

## 3. The two mimamsa calibration ledgers — standing ruling confirmed verbatim

Per the brief's own instruction, `mimamsa_fact_adjustment` and `mimamsa_signal_adjustment`
carry the native's pre-existing ruling, re-confirmed rather than re-litigated:

> `mimamsa_fact_adjustment` + `mimamsa_signal_adjustment` = **GATED** (reason: L5 STRUCTURAL
> seal + NO-LEAKAGE; public face: `mimamsa_calibration_get`; revisit: calibration-loop
> maturity or a Samīkṣā drill requirement).
> — `RULINGS_ADOPTED.md` §F item 3 (native ruling, 2026-07-19/20)

This maps directly onto CLAUDE.md §E's L5 note: "sealed in STRUCTURAL mode — empirical
calibration values fill in as prediction→outcome data accrues (this is by design, not
unfinished work)." The revisit condition fires when that empirical maturation (or a
Samīkṣā drill) produces a reason to re-open the gate — not on any fixed calendar date.

Two schema-identical siblings (`mimamsa_convergence_adjustment`, `mimamsa_anchor_adjustment`)
were doctrine-extended to the same GATED disposition in `TABLE_CONCEPT_DISPOSITIONS_v2_0.md`
§3, on the ruling's own text ("applying an already-cited reason to a sibling is not a new
reason"). Re-confirmed this session, not re-derived.

## 4. Zero code changes required — why

RC-09's brief anticipates a possible minimal-wiring step (§5 of the task). None was needed:
`TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §11 (W2b lane, 2026-07-20) already wired all 36 genuine
SERVE-gap tables from the original 51, with real `CapabilityDescriptor` code + real mocked-DB
unit tests, verified at the time via `tsc --noEmit` (clean), `eslint` (clean), and
`vitest run` (890 passed / 125 skipped in the registry suite; 6172 passed in the full
platform suite). This session independently re-confirmed that work is genuinely merged to
`main` (not just documented) by:

1. Listing every claimed capability file on disk at current `main` HEAD (2df42b61) — all
   present (see per-row Evidence columns above).
2. Confirming each is imported/registered in its layer's `index.ts` (spot-checked
   `query_prashna_lagna_methods`, `query_class_priors`, `get_condition_composite`; all
   registered).
3. Re-running the full L0-L5 registry test suite fresh this session:
   `npx vitest run src/lib/retrieval/registry` → **97 files / 987 tests passed, 17 files /
   125 tests skipped, 0 failed.**
4. Grepping the full `registry/`/`tools/`/`resources/` surface for the four GATED tables to
   confirm zero serving queries exist against any of them (comment-only references in
   `query_load_bearing.ts`, which explicitly distinguishes itself from them).

No table required a code change to reach its correct terminal disposition. RC-09 closes as
a documentation/verification residual, per the brief's own §D.5(iv)/§E RC-09 framing.

## 5. NEEDS-OWNER count: 51 → 0

Every one of the 51 W1-census NEEDS-OWNER tables now carries a terminal five-state
disposition, confirmed against live `main`. No table remains open. No new gate reason was
required beyond the ones already on doctrine record (A-19 NO-LEAKAGE / L5 structural seal).

---

*End of DARK_TABLE_DISPOSITIONS v3.0. Predecessor `TABLE_CONCEPT_DISPOSITIONS_v2_0.md`
(and v1.0) retained in place per governance hygiene policy — this document confirms and
terminally closes R-8/RC-09 over the same 51-table set, it does not supersede their
evidence. Source: `TABLE_CONCEPT_DISPOSITIONS_v1_0.md` (the 51-table W1 NEEDS-OWNER list),
`TABLE_CONCEPT_DISPOSITIONS_v2_0.md` (the hand-verified dispositions + wiring log),
`RULINGS_ADOPTED.md` §F (taxonomy + pre-ruled GATED tables), this session's fresh
file-existence + registration + test-suite re-verification.*
