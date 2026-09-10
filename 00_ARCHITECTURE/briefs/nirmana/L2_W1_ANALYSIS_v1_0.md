---
canonical_id: L2_W1_ANALYSIS
version: 1.0
status: CURRENT
layer: L2 (Bodha)
session: L2
last_updated: 2026-09-05
rubric: NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §4 (W1 ANALYZE)
charter: SESSION_CHARTER_V21.md v2.1
---

# L2-W1 ANALYZE — all 22 Bodha assets

Five read-only lanes, fanned out per charter C8 item 4, every claim carried back with a `file:line`
or a live `SELECT`. Measured against production on 2026-09-04/05. Canonical chart
`482012f1-710e-4a25-994a-93821f5871aa` (50,104 signals; 150,150 across three charts).

Rubric coverage, per plan §4: (1) pillar/doctrine fit · (2) real vs declared dependencies ·
(3) **leverage — consumers reading NULL where the asset already computed the answer** ·
(4) **grounding labelability** · (5) temporal identity (L3's axis, N/A here) · (6) service:
consumer, floor, density, drill · (7) measured build + serve cost · (8) findings → W2.

---

## §0 — The headline

**L2 is the payoff layer, and almost none of the payoff is switched on.**

`salience_formula_v2` (`bodha_writers/formulas.py:541`) has thirteen multiplicands. **Seven are
constants on every one of the 150,150 rows**: `orb_tightness` ≡ 1.0 · `av_mult` ≡ 1.15 ·
`(1 + vargottama)` ≡ 1.0 · `neechabhanga` ≡ 1.0 · `cancellation` ≡ 1.0 · `specificity` ≡ 1.0 ·
`class_prior` ≡ 1.0. The one surviving non-unit constant, 1.15, is a pure scale factor that
**cancels out of every ordering**. The chart's 50,104 signals are therefore ranked by
`dignity × shadbala × house_weight × varga_weight × verification_rescale × bala_gate ×
functional_context` and nothing else — and `composite_ranker.ts:255` already carries an in-code
note that fired rows are being buried below not-fired ones.

Every doctrine the plan asked L2 to serve is measurably unserved:

| doctrine | state on the canonical chart |
|---|---|
| **D-SALIENCE** | all four static terms inert (above); `bodha_anomalies` (2,918 rows, 125 of them `low_salience_high_consequence`) reachable only behind a parameter defaulting to `false` that **no call site sets**, on a capability the live MCP surface does not expose; `tail_watch` does not exist anywhere in the codebase |
| **D-SYNTHESIS** | `system_convergence_count`, `cross_system_consensus_count`, `contradicts_signals_array` — all three 100% NULL; the adjudication-rule table does not exist |
| **D-GROUNDING** | `classical_sources_array` on 156 of 150,150 rows; `source_corroboration_count_by_text` fabricated on 149,706; `grounding_tier` is not a column anywhere; and **the corpus has no verse numbers** (§4 below) |
| **D-SERVICE** | 22/22 assets do have a consumer — the one pillar in decent shape — but all five `tool_role: 'umbrella'` L2 capabilities lack both a hand-authored `density_contract` and any `empty_reason` implementation, and they are exactly the envelopes the tail clause designates |
| **C12 (integrity)** | **0 of 22 assets have an `integrity_check_sql`.** 19 of 22 have no `expected_volume_formula`; the 3 that do are all wrong or unevaluable |

---

## §1 — Lane A: the D-SALIENCE static-term chain

Formula home `bodha_writers/formulas.py:541`, called from `bo_laksana.py:1942` via
`_compute_salience` (`:1864`). All five static-term columns are nullable `NUMERIC` with **no DB
default** (`platform/migrations/325_l2_bodha_enriched_schema.sql:93-107`).

| id | defect | class |
|---|---|---|
| **A1** | `_av_multiplier` thresholds (7/5/3/1) are **bhinnāṣṭakavarga** scale; the feed is **sarvāṣṭakavarga** (measured 23–33/house). Saturates at 1.15 on 149,375 rows | correctness — units mismatch (`formulas.py:90-99` vs `bo_laksana.py:957-983`) |
| **A2** | `int(fact_value_num or 28)` — the NULL fallback itself lands in the top AV bucket | §N.7 item 6 |
| **A3** | `argala_modifier` was dropped from `SalienceInputsV2` at the v1→v2 upgrade; 41,760 L1 argala facts unconsumed | dead column (`formulas.py:512-539`; 9 hardcoded `None` sites) |
| **A4** | `tags["vargottama_amp"\|"neechabhanga"\|"cancellation"\|"orb_tightness"]` — **0 of 139,471** L1 facts carry any of those `fact_value_jsonb` keys | §N.8 — four detectors that cannot fire |
| **A5** | `bo_vargottama_dhana` hardcodes `vargottama_amplification=0.0` while expressing the amplification through `class_prior=1.15` | §N.7 item 3 (`vargottama_dhana_emitter.py:125` vs `:285`) |
| **A6** | `cancellation_modifier` has **no detector anywhere**; the documented "0.1 = cancelled yoga" semantic was never implemented | §N.8 — should be NULL |
| **A7** | `neechabhanga_modifier` has exactly one real detector (`bo_laksana.py:2738-2742`, off L1 `ga_yoga_firings`) reaching 135 of 150,150 rows | honest where it fires, dead on the main path |
| **A8** | `specificity` is passed `1.0` with the comment *"filled in second pass by percentile UPDATE"* — **that pass does not exist** | §N.8 (`bo_laksana.py:1937`) |
| **A9** | `salience_robustness` is selected by serving (`query_signals.ts:120`) and written by nobody | dead column |
| **A10** | `salience_inputs_complete = false` on **100%** of rows | honest flag, alarming value |
| **A11** | `class_prior` = 1.0 with **1 distinct value** on all three charts, against a `brahma_class_priors` holding 177 rows with real variance (`childbirth/*`=3.09, `graha_domain/progeny`=1.5, `configuration/*`=1.4, `yoga/*`=1.4). Observed lookup hit rate **0%** — and `bo_laksana.py:3282-3299` is a guard that *warns* below 50% and ships anyway | §N.8 — a guard that does not gate |
| **A12** | dead duplicates `_av_mult` / `_HOUSE_WEIGHT` shadow `formulas.py`, zero call sites | drift hazard (`bo_laksana.py:1831,1835`) |
| **A13** | `bo_karanajala` re-derives argala from house offsets (`ARGALA_POSITIONS` 2/4/11) rather than reading L1's `argala_natal_matrix` | **§N.5 — L2 re-deriving an L1 authority** (`bo_karanajala.py:502-601`) |

**L1 sources are all present and unread** (canonical chart): `argala_natal_matrix` 20,880 +
`virodha_argala_natal_matrix` 20,880 (= the plan's 41,760), `fact_value_num` already a normalised
0..1 strength · `net_argala_per_varga` 1,740 · `ashtakavarga_bindu_per_varga` **6,720**, shaped
`fact_subject='<GRAHA>-HOUSE_<n>'`, `fact_key='<varga>'`, `fact_value_num` = bhinna bindus 0–8 —
i.e. **exactly the scale `_av_multiplier` was written for** · `graha_vargottama_amplification_factor`
35 rows, `fact_value_num ∈ {1, 1.25}`, so `vargottama_amplification = factor − 1` gives an honest
non-constant 0 or 0.25.

**Cascade and cost trap.** Nothing after `bo_laksana` recomputes salience — `top_k_salience_rank`,
`salience_pctl_in_class`, `strength_normalized_to_chart_max` and `signature_tier` are all computed
in memory pre-INSERT inside `run_substep`. `bo_laksana_rerank` is the wrong vehicle (it only
UPDATEs `graph_node_strength_contribution_jsonb` and `valence`). So the fix requires a **full
`bo_laksana` rebuild** → `bo_karanajala` (reads `computed_salience` for edge strength) →
`bo_laksana_rerank` (its rows were deleted) → `bo_samskara` (FK `signal_id`s change). Two traps
on that path: `bo_samskara`'s reuse key is `signal_id` (`bo_samskara.py:139`), so **new UUIDs mean
100% Vertex AI re-embedding cost** unless reuse is re-keyed on `embedding_input_summary`; and
`bo_laksana.py:2941-2947` records that a post-insert UPDATE of one scalar salience column over
~28K rows took **600 s+** against 20 indexes (3 GIN) — any backfill-by-UPDATE design pays that.

---

## §2 — Lane B: the D-SYNTHESIS rollups

| id | finding |
|---|---|
| **B1** | `contradicts_signals_array` is a **denormalisation gap, not a missing computation** — the data is in `bodha_contradictions` (15 rows canonical). A pure join reaching **22 of 50,104** rows |
| **B2** | B1 turns on a downstream term that is currently and *correctly* disabled: `bo_upaya.py:741-770` probes the column, finds zero populated, sets `source_available=False` and stores NULL rather than a 0.0 a reader could not distinguish from a measured zero (`:1636-1646`) |
| **B3** | Non-participating rows must stay **NULL, never `'{}'`** — `bo_upaya` would read `'{}'` as a measured "no contradictions" |
| **B4** | `cross_system_consensus_count` is computable and discriminative at `chart_facts.fact_subject` level (§N.5-clean): 188 of 4,699 subjects carry >1 tradition; **2,808 signal-rows** would carry ≥2; range 1–3 |
| **B5** | Fact-**level** cross-tradition overlap is nil — 2 facts touched by >1 tradition. Any definition keyed on shared `fact_id` is dead on arrival |
| **B6** | `system_convergence_count`: the only domain-level definition available yields **mean 5.93, max 6** on 50,044 rows — near-constant, and it measures the *domain*, not the signal → **adjudication #1720** |
| **B7** | `bodha_cgm_edges.cross_system_consensus_count` is the literal constant `1` on all 849 canonical rows (`bo_karanajala.py:587,663,776,1011,1131,1180,1246,1551`) while the honest source `present_in_traditions_array` sits populated beside it | §N.8 |
| **B8** | `bo_samvada` is a **DDL-only writer** — drops and recreates the `vw_chart_digest` VIEW, computes nothing per chart. Its `count_sql` returns 5 for any chart with any signal row, **so it cannot read false on writer failure** | §N.8 proxy |
| **B9** | `bo_samvada.py:7-17` docstring names 8 columns the view does not have |
| **B10** | `bo_pramana_mapa`: all six previously-unearned flags now have real detectors, proven by the stored `notes.n8_detectors` terms on the live row; three columns are correctly **NULL, not green**. **No work needed** |
| **B11** | `unresolved_constituent_facts_count = 49` — 49 constituent refs do not resolve to `chart_facts` | §N.5 |
| **B12** | Adjudication-table precedent found: `kala_paddhati_profile` (`school_tag` / `constraint_role` / `provenance` / `native_confirmed` triple) is the direct model; `kala_gochara_authority` models the stored-ruling audit half |

---

## §3 — Lane D: the tail lane and the serving plane

| id | finding |
|---|---|
| **D1** | `bodha_anomalies` — **confirmed built-but-unplugged.** 2,918 rows/canonical chart (125 `low_salience_high_consequence`, max σ 6.17). Sole reader `query_contradictions.ts:134-146` is gated by `include_anomalies` (default `false`); repo-wide grep finds **six hits, all definition-site, zero call sites**; and `query_contradictions` is **not registered on the live MCP surface** |
| **D2** | `tail_watch` — **zero occurrences** in `*.ts`/`*.tsx`/`*.py`/`*.sql`. `synth_tail_divergence_get` is a separate, unprotected tool, not an in-envelope section |
| **D3** | `hardFloor: true` alone does **not** satisfy "no budget trim may zero it". It requires `minKeep ≥ 1` (hardFloor imposes no floor of its own); `autoDetectTrimmableSections` never sets it and skips arrays of ≤10 elements; and it does not protect against `finalizeMcpBudget`'s last-resort `truncateLongStringsInPlace`. The stronger guarantee is **`IMMUNE_HONESTY_FIELDS`** membership (`response_budget.ts:56-81`, which the file itself calls *"stronger than hardFloor, not weaker"*) |
| **D4** | Rare-class leaders **are** computable today from `salience_pctl_in_class` (honestly computed — in-memory `PERCENT_RANK` per chart×ayanamsha×class, 1,308 distinct values) — **51 rows verified** on canonical/lahiri with `class_n ≤ 300 AND salience_pctl_in_class ≥ 0.90 AND top_k_salience_rank > 100` |
| **D5** | …but the six **rarest** classes (149 rows: `sudarshana_agreement`, `nakshatra_semantic`, `arudha`, `special_lagna`, `dhana_axis`, `vargottama_amplification`) have **NULL percentile**, because their satellite writers never run the setter. The rare-class predicate silently excludes exactly the population it most wants |
| **D6** | All five `tool_role: 'umbrella'` L2 capabilities (`query_chart_gestalt`, `query_cdlm_summary`, `query_discoveries`, `query_question_lenses`, `query_ucd`) have **neither** a hand-authored `density_contract` **nor** any `empty_reason` implementation. `deriveDensityContract()` auto-stamps `empty_reason: true` by archetype — an unbacked claim wherever the handler never sets `content.empty_reason`, which is a §N.8 instance at scale |
| **D7** | `resolve_grounding` does not exist under that name. The spine is `resolveSignals` (`grounding/resolver.ts:154`) + `resolveMetric` (`:332`). `grounding_tier` would not flow through today twice over: it is not in the SELECT (`:76-77`) and `GroundedSignal` has no such field (`types.ts:139-162`) |
| **D8** | A lens drill partially exists (`query_question_lenses.ts`, 60 rows = 12 question types × 5 ayanamshas) but drills into *question lenses*, not adjudication rulings; and no `only_on_explicit_request` gating primitive exists anywhere |
| **D9** | `bodha_signal_embeddings` (50,104 rows) has **zero serving readers**, and `coverage_matrix.ts:428` points at `marsys://tool/L2/get_signal_embeddings` — a tool that does not exist. A coverage claim with no detector behind it |
| **D10** | `bodha_pratijna.varga_confirmation` (135/135 populated) is the **only real consensus substrate** in the layer today — the honest basis for a consensus chip while B4/B6 are pending |

---

## §4 — Lane C: grounding — the corpus has no verse numbers

**The finding that reshapes the lane.** `classical_text_chunks.chapter` is a **page number**;
`verse_start`/`verse_end` are **column indices**. Two independent proofs: `classical_texts`
declares `bphs.total_chapters = 97` while chunk `chapter` runs **1…1034** (same everywhere —
`nadi_navamsa_patel` 2550, `brihat_samhita` 1105, `brihat_jataka` 583 against 27 declared); and
`verse_start`/`verse_end` take only `{1,2}` for 13 of 15 texts. The identifiers say it outright:
`chunk_id='bphs_pg0211_c01'`, `verse_ref='PG211:C1'`, `chapter=211`,
`source_citation='[HIGH] BPHS — Trans. R. Santhanam, Ranjan Publications … | PG211'`.

Nominal coverage is 100% on every addressability column, which is exactly what makes it
dangerous: a coverage check passes and the values are not what their names say. Composing
`text_id + chapter + verse` yields **"BPHS 211.1"** — well-formed, canonical-looking, checkable,
and wrong. **D-GROUNDING's `sruti` tier as literally defined ("verse refs") is not emittable.**
Raised as adjudication **#1726**; `yukti` and `pratyaksa` proceed meanwhile.

| id | finding |
|---|---|
| **C1** | **The live fabrication, located exactly:** `bo_laksana.py:2265` — `"source_corroboration_count_by_text": 5 if vpass == "two_pass_verified" else 2`. A claim that *N texts corroborate this* whose only detector asks whether the **fact** was double-checked. §N.8 verbatim, on 149,706 rows |
| **C2** | The sutrāvalī matcher is **partially feasible and was proven, not sketched**: `sutravali_rules` = 3,003 rows (1,904 single-clause, 1,099 two-clause, none deeper). A prototype join scored **70 rule-hits on (planet, house) and 79 on (planet, sign)** across 10 of 14 texts — from single-clause antecedents, one ayanamsha, D1 only, with only 4/9 grahas carrying a sign |
| **C3** | Three obstacles, all closed-set lookups, none hand-waved: a vocabulary bridge on every axis (graha code→name, sign name→ordinal, `"9.0"`→`9`); `sign` sparsely populated in `graha_position`; and — the largest correctness trap — **`graha_dignity_per_varga` is graha-anonymous**: its `configuration_jsonb` carries sign/house/varga and *no graha key*, so any matcher keying off it alone silently mis-attributes 1,057 rows. The graha must be recovered via `constituent_facts_array → chart_facts.fact_subject` |
| **C4** | Two hard gates for the matcher: **never match a rule against a varga other than D1** (nothing in `antecedent_jsonb` scopes to a divisional; applying a D1 rule to D60 fabricates authority), and `confidence`/`quality_score` are **regex-extraction** confidences (`extracted_by='python_regex_v2'` on 100% of rules), never to be re-served as scholarly ones |
| **C5** | **`bg_concordance` cannot be wired as-is.** `classical_attributions.source_chunk_ids` is `bigint[]` while `classical_text_chunks.chunk_id` is `text` — type-incompatible with its target, empty on 100% of 720 rows, by documented design (`bg_concordance.py:8-10`). Its `rule_ids` resolve 100% but are grouped by `text_id` **only, not by topic** (237,120 pointers ÷ 477 rows ≈ **497 rules/row**), so topic `rahu_in_7th` carries every Phaladeepika rule. `match_confidence = min(1.0, n_chunks/5.0)` — a monotone function of chunk count wearing confidence's name |
| **C6** | **The real substrate is one level down and is in good shape**: `classical_text_chunks.topic_tag`, **7,010 tagged chunks across 361 topics**, in exactly L2's vocabulary (`lord_7th_in_1st`, `sun_in_1st`, `saturn_in_7th`, `marriage_general`). Plug the substrate, not the aggregate |
| **C7** | Output should extend the **existing** `classical_sources_jsonb` shape (`bo_laksana.py:1539-1548`: `{catalog_ids[], rule_ids[], text_chunk_ids[], citations[]}`) with a `concordance_topic_ids[]` member — that shape is **already read by the serving layer** (`resolver.ts:481-490`), so output flows to callers with no serving change |
| **C8** | Honest tier assignment across ~20,600 interpretive rows (of 50,104): **~2,000 text-direct · ~5,300 `yukti` · ~13,300 `pratyaksa`.** Per the doctrine that majority is a success — contradiction pairs, kāraka webs, cross-varga divergence and graph centrality are `pratyaksa` because no classical author could compute them |
| **C9** | `signal_type_class` is **not a usable scope axis** — `composite_state` swallows 37,215 of 50,104 rows and mixes Ṣaḍbala arithmetic with dignity grading. The usable axis is `split_part(signal_type_id,':',1)` (200+ families) |

---

## §5 — Lane E: registry, floors, hygiene

**All 22 `count_sql` execute cleanly.** Full truth table in the W2 doc; the load-bearing results:

| id | finding |
|---|---|
| **E1** | **19 of 22 have no `expected_volume_formula`** (C12: a NULL formula is itself the defect), and **all 3 that do are wrong or unevaluable**: `bo_bimba` `ACTUAL(bo_laksana)` → 385 vs 49,955, wrong by 130× · `bo_karanajala` `ACTUAL(bo_laksana) * EDGE_DENSITY` → `EDGE_DENSITY` is an unbound free symbol and `expected_volume_inputs` is NULL on all 22 · `bo_samskara` `ACTUAL(bo_laksana)` → off by exactly 149. The populated cases are **worse than the NULL ones**, because they read as done |
| **E2** | `bo_samskara`'s 149-row delta is **fully attributed**, not guessed: the six satellite MSR emitters outside `bo_laksana`'s 15-class `count_sql` filter contribute 45+45+25+20+10+4 = 149; 49,955+149 = 50,104 ✓. The correct derived formula is `COUNT(bodha_msr_signals WHERE chart_id)` — a real cross-table invariant |
| **E3** | Two assets below floor: `bo_laksana` **−10,045** and `bo_samskara` −9,896 (the latter is E2's consequence, not an independent defect). `bo_laksana`'s shortfall has a **named lead**: the `medical` and `vastu` classes are in its own `count_sql` class list and produce **zero rows** |
| **E4** | 13 of 22 floors are not the achieved count — §N.4 says floors are set to achieved after build |
| **E5** | **All 9 DRAFT assets are unpromoted, not incomplete** — one mechanical defect, not nine judgments. `asset_registry.catalog_status` defaults to `'DRAFT'` and eight registry migrations (358, 438, 445, 446, 450–453) omitted the column entirely. This is the **identical already-diagnosed bug** that `platform/migrations/294_catalog_status_current.sql:3-7` swept; migrations 358 and 438–453 landed after it and reintroduced it. Zero `TODO`/`stub` markers in 8 of 9 writers; the 9th's single hit is a documented optional-field comment |
| **E6** | `bo_cdlm_summary` / `bo_chart_gestalt` NULL `target_table` **has teeth**: `CHECK asset_registry_natural_key_partition_needs_table` makes `natural_key_partition` structurally unsettable, so C12 conform work is blocked at constraint level; and both are **un-clearable from the cockpit** (`clear/route.ts:186` — `clear_tables` NULL, no `assetClearSpec` entry, no `target_table`: all three fallbacks absent) |
| **E7** | Two `sort_order` collisions (`bo_yantra_mechanism`/`bo_nakshatra_semantic` both 20; `bo_arudha`/`bo_laksana_rerank` both 21). Ordering contiguity is exactly the invariant class C12 names |
| **E8** | `asset_throughput.rows_written` disagrees with live `count_sql` on 6 assets — loudest `bo_cdlm_summary` 70→5 and `bo_sangati` 535→280 |
| **E9** | **The C12 exhibit.** `bodha_cgm_edges` canonical chart: **849 rows in both the live table and its `__ssv_` snapshot, and different row sets** — `md5(edge_id set)` `bc600bf3…` live vs `c055914f…` snapshot. A `count(*) = 849` check passes across a *total identity change of the row set*. This is the cleanest available demonstration of why C12 forbids equality pins, and belongs in the C12 rationale verbatim |
| **E10** | `__ssv_*` — **RETAIN all 6, DROP none.** Provenance found: ŚUDDHA-VĀCA Phase D `CTAS` rollback anchors (PR #846), restore tested byte-identical. 4 of 6 differ materially from live, and the 49,563-row `bodha_msr_signals` snapshot is the direct witness for E3's investigation. They carry **zero self-describing metadata** — which is what let an earlier drain script miscount them. L2's six are 571 MB of a ~1.2 GB campaign-wide shadow footprint |
| **E11** | **UCN→UCD retirement is PARTIAL.** Complete at the data layer (no writer, no asset, `l25_ucn_digests` exists with 0 rows), but UCN survives as live vocabulary in ≥6 non-test source files. The sharpest residual: `A14_ucn_digest` is still a UI-visible build-DAG node (`AssetNode.tsx:89`) **pinned by a passing test** (`build/start/__tests__/route.test.ts:368` asserts `DAG_ASSETS` contains it) — a green that should be false |
| **E12** | **Consumer map: 22/22 have a consumer. Zero ZERO-CONSUMER assets** — D-SERVICE's one healthy pillar. Two weak links reach consumers only via the generic `query_signals(signal_type_class=…)` parameter with no pinned primitive: `bo_special_lagna` and `bo_arudha` |
| **E13** | **Real cost data exists — in `build_run_assets`, not `asset_throughput`** (whose `rows_per_second`/`measurement_count`/`history` are NULL/0/`[]` on all 22). ~1,690 recorded L2 asset runs. Serial sum of averages ≈ **3,406 s (57 min)** per full L2 pass against a registry `estimated_seconds` sum of 1,571 s — the registry under-states L2 by ~2.2× overall and **7.1× on `bo_laksana`** (avg 1,376 s, max 69,159 s = 19.2 h) |
| **E14** | **20 of 22 assets are `state='stale'` on the canonical chart**; only `bo_sudarshana` and `bo_vargottama_dhana` are `lit`. Last builds span 2026-08-08 → 2026-08-21. The layer has never been rebuilt coherently as a unit |

---

## §6 — Leverage summary (rubric item 3)

Consumers reading NULL where the answer already exists:

| consumer | reads | currently gets | the answer already exists in |
|---|---|---|---|
| `bo_upaya` `contradiction_factor` | `contracts_signals_array` | disabled, `source_available=False` | `bodha_contradictions` (15 rows) |
| `salience_formula_v2` argala term | `argala_modifier` | term deleted from the contract | `argala_natal_matrix` + `virodha_argala_natal_matrix` (41,760 facts) |
| `salience_formula_v2` AV term | `ashtakavarga_bindus` (sarva) | saturated constant | `ashtakavarga_bindu_per_varga` (6,720, correct scale) |
| `salience_formula_v2` vargottama term | `tags['vargottama_amp']` | key never present | `graha_vargottama_amplification_factor` (35, values 1 / 1.25) |
| `salience_formula_v2` class_prior | `brahma_class_priors` join | 0% hit rate | `brahma_class_priors` (177 rows, real variance) |
| `resolve_metric` | `cross_ayanamsha_consistency_score` | `null` on every call | nothing — genuinely uncomputed |
| serving | `salience_robustness` | NULL | nothing — no writer exists |

---

## §7 — Residual UNDETERMINEDs carried into W2

1. Whether `medical`/`vastu` emitting zero rows is chart-conditional or a dead code path (E3). Settled by a DB-wide `SELECT DISTINCT signal_type_class`.
2. Whether the 6 `rows_written` vs `count_sql` divergences (E8) are pre-dedup counting, stale-generation accretion, or post-report shrinkage. Settled by a `GROUP BY build_id` per table.
3. Two-clause sutrāvalī matcher yield — 1,099 rules of arity 2 unmeasured (C2 measured arity 1 only).
4. Whether `graha_dignity_per_varga`'s graha is recoverable for all 1,057 rows via `constituent_facts_array`. If below 100%, that slice drops to `yukti` unconditionally (C3).
5. Whether `sarvartha_chintamani`'s 342 chunks (`chapter=1`, `verse_start` 1…342) are true verse numbers — the lone possible exception to §4.
6. Exact interpretive row total; the family enumeration was output-truncated (C8's ~20,600 is a close estimate, not a census).

*End L2_W1_ANALYSIS v1.0.*
