---
artifact: L2_STATE.md
canonical_id: NIRMANA_V21_L2_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
session: L2
layer: L2 — Bodha
owner: the L2 session (this file is yours alone — charter C5)
last_updated: (none yet — stub created by CONDUCTOR at v2.1 bootstrap)
---

# L2 — Bodha — SESSION STATE

Stub created by the CONDUCTOR so this session has a file to rebase onto. **Everything below is
yours to overwrite.** Charter C9: this file is your memory — update it every loop, commit it with
every PR and at every milestone, so re-pasting your prompt into a fresh session is safe at any
moment.

**Read order on ANY start:** `SESSION_CHARTER_V21.md` → this file → `git fetch origin main` →
your `nirmana-adjudication` issues → continue.

- **Coordination issue:** #1713 (run-slot claims, freeze-ordering acks, monster scheduling)
- **Adjudication:** open a new issue labeled `nirmana-adjudication`, then keep working (C3)
- **Migration range:** 660–669 (yours alone, collision-free by construction)
- **Branch namespace:** `codex/nirmana-l2-*` · **PR title prefix:** `L2:`
- **Worktree:** `~/nirmana-s/l2`
- **Standing ruling D-CND-01 (read before your first Conform-stage check):** a `count(*) = N` is
  permitted only as a conjunct of something that can fail on corruption it cannot see — a total
  content fingerprint, or named invariants (contiguity, tiling, distinctness, cross-table
  FULL-JOIN consistency, NULL/range guards). Alone it is forbidden (C12). `expected_volume_formula`
  is REQUIRED when a count equality is the volume assertion; not required alongside a total-content
  digest. Full reasoning + the L0 evidence: `CAMPAIGN_STATE.md` → CONDUCTOR standing audit A-01.
- **Freeze predecessor:** L1 Gaṇita must be frozen before your W6 ceremony (C2; asset work is never held)

## LAYER CONVENTIONS ADOPTED FROM THE STUB

The CONDUCTOR's bootstrap stub is superseded by the live content below, with two things carried
forward verbatim rather than overwritten: the orientation block above, and **standing ruling
D-CND-01** — a `count(*) = N` is permitted only as a conjunct of something that can fail on
corruption it cannot see. That ruling binds every `integrity_check_sql` L2 authors in W3/W5, and
the invariant sketches in `L2_W2_DECIDE_v1_0.md` were written to satisfy it.

## POSITION

`L2-W2 complete → L2-W3 open` (opened 2026-09-04T22:30Z). 22 assets, none terminal.
W1 deliverable `L2_W1_ANALYSIS_v1_0.md`; W2 ruling `L2_W2_DECIDE_v1_0.md` (22 routes, 14 MUST,
25 NOW, 8 LATER). W4 gated on L1 freezes — `bo_sudarshana` is the frontier at 1 unfrozen
ancestor (`ga_positions`) and is the designated canary.

## HEARTBEAT

| loop | UTC | position | note |
|---|---|---|---|
| 1 | 2026-09-04T22:30Z | L2-W1 | worktree created; charter + plan 4/5 read; 22-asset roster pulled from frozen definition; first census run; 5 read-only W1 subagents dispatched |
| 2 | 2026-09-04T23:20Z | L2-W2 | all 5 W1 lanes returned; `L2_W1_ANALYSIS_v1_0.md` + `L2_W2_DECIDE_v1_0.md` written; 3 adjudications filed (#1716 tooling, #1720 system_convergence_count, #1726 sruti/verse-addressability); PR #1717 (state bootstrap) in queue |

## ASSET TABLE (22)

Routes assigned in W2. `--` = not yet ruled.

| asset_id | deps | route | status | capsule |
|---|---|---|---|---|
| bo_laksana | bg_rules, ga_condition, ga_nakshatra, ga_panchanga, ga_positions, ga_sade_sati, ga_sensitive, ga_strength, ga_structural, ga_vargas, ga_vichara | -- | W1 | -- |
| bo_bimba | bo_laksana | -- | W1 | -- |
| bo_samskara | bo_laksana | -- | W1 | -- |
| bo_karanajala | bo_bimba, bo_laksana, ga_positions | -- | W1 | -- |
| bo_sangati | bo_karanajala, bo_laksana | -- | W1 | -- |
| bo_drishti | bo_karanajala, bo_laksana, bo_sangati | -- | W1 | -- |
| bo_laksana_rerank | bo_karanajala | -- | W1 | -- |
| bo_cgm_motifs | bo_bimba, bo_karanajala | -- | W1 | -- |
| bo_cgm_paths | bo_bimba, bo_karanajala | -- | W1 | -- |
| bo_anveshana | bo_bimba, bo_drishti, bo_karanajala, bo_laksana, bo_samskara, bo_sangati | -- | W1 | -- |
| bo_upaya | bo_cgm_motifs, bo_laksana, bo_sangati, ga_dashas, ga_structural | -- | W1 | -- |
| bo_pramana_mapa | bo_anveshana, bo_bimba, bo_drishti, bo_karanajala, bo_laksana, bo_samskara, bo_sangati, bo_upaya | -- | W1 | -- |
| bo_samvada | bo_karanajala, bo_laksana, bo_pramana_mapa, bo_sangati, bo_upaya | -- | W1 | -- |
| bo_chart_gestalt | bo_anveshana, bo_bimba, bo_cgm_paths, bo_laksana, bo_sangati | -- | W1 | -- |
| bo_cdlm_summary | bo_sangati | -- | W1 | -- |
| bo_pratijna | bo_laksana, bo_sangati | -- | W1 | -- |
| bo_yantra_mechanism | bo_cgm_motifs, bo_cgm_paths, bo_karanajala | -- | W1 | -- |
| bo_arudha | ga_positions, ga_structural | -- | W1 | -- |
| bo_nakshatra_semantic | ga_nakshatra, ga_positions | -- | W1 | -- |
| bo_special_lagna | ga_sensitive | -- | W1 | -- |
| bo_sudarshana | ga_positions | -- | W1 | -- |
| bo_vargottama_dhana | ga_positions, ga_vargas | -- | W1 | -- |

## DECISIONS LOG

- **D-L2-001** (2026-09-04T22:35Z) -- **No L2 asset has an L0-only ancestor set.** The prompt
  anticipated "early candidates among bo_* whose ancestors are L0-only"; the frozen definition
  shows every one of the 22 depends on at least one `ga_*` (L1) asset, directly or transitively.
  Consequence: **my entire W4 is gated on L1 asset freezes**, not L0. Shallowest E-gate
  candidates (single/double L1 leaf dep) are `bo_sudarshana` (ga_positions), `bo_special_lagna`
  (ga_sensitive), `bo_nakshatra_semantic`, `bo_arudha`, `bo_vargottama_dhana`. The W4 canary
  will be whichever of these clears C10 first. Re-derived each loop; never assumed.
- **D-L2-002** (2026-09-04T22:40Z) -- W3 opens ahead of a completed per-asset W2 for the four
  lanes plan 5 already names (salience terms, synthesis rollups, grounding matcher, tail lane).
  Justification: plan 5 IS the pre-ruled route for those lanes, W3 needs no upstream (charter
  C6: no inbound capability holds on L2), and L2 is the campaign critical path. Per-asset W2
  routes are still ruled in `L2_W2_DECIDE_v1_0.md` before any W4 dispatch. **Superseded in
  practice at 23:20Z**: W2 completed before W3 began, so no route was implemented ahead of its
  ruling. Kept on the record because it was the operating assumption for ~40 minutes.
- **D-L2-003** (2026-09-04T23:05Z) -- **Registry migrations must land BEFORE W2 evidence is
  recorded.** `registry_fingerprint_sha256` is computed over `REGISTRY_CONTRACT_FIELDS`, which
  includes `integrity_check_sql`, `count_sql`, `catalog_status` and `target_table`
  (`dispatch_nirmana_campaign_wave.py:36-49`, `:246-269`), and the dispatcher rejects any
  `asset_analysis_accepted` whose recorded fingerprint no longer matches live (`:325`). Since L2's
  W3 adds `integrity_check_sql` to all 22 and corrects floors/`catalog_status`/`target_table`,
  recording analysis first would invalidate all 22 and force a full delta re-review. Ordering:
  registry migrations -> analysis/verdict events -> W4 dispatch.
- **D-L2-004** (2026-09-04T23:10Z) -- **Plug the concordance substrate, not the aggregate.**
  Plan 5 (L0) rules `bg_concordance`'s disposition as WIRE with its consumer landing at L2. It
  cannot be wired as-is: `classical_attributions.source_chunk_ids` is `bigint[]` while
  `classical_text_chunks.chunk_id` is `text` -- type-incompatible with its target, empty on 100%
  of 720 rows by documented design (`bg_concordance.py:8-10`) -- and its `rule_ids` are grouped by
  `text_id`, not topic (497 rules per row). L2 consumes `classical_text_chunks.topic_tag` (7,010
  chunks / 361 topics) directly and hands `bg_concordance`'s own repair back as a named backlog
  item rather than silently routing around it. `bg_concordance.py` is L0's write-set (C5).
  Recorded in adjudication #1726 in case the Conductor prefers to rule on it.

## FINDINGS LEDGER (W1, measured -- not yet triaged)

Census run 2026-09-04T22:40Z against production. `bodha_msr_signals` = 150,150 rows across 3
charts (50,104 for canonical `482012f1-...`).

| id | finding | evidence | doctrine |
|---|---|---|---|
| F-L2-01 | `argala_modifier` is 0/150,150 non-NULL -- the term does not exist in data | SQL census | D-SALIENCE |
| F-L2-02 | `ashtakavarga_support_multiplier` is the **constant 1.15** on 149,375 rows (1.0 on 331, NULL on 444) -- populated-looking, information-free | SQL census | D-SALIENCE; N.7 item 3 (wrapper-local constant shadowing an L1 value) |
| F-L2-03 | `vargottama_amplification` = **0 on all 150,150 rows** -- never computed; if it multiplies into salience, 0 annihilates | SQL census | D-SALIENCE; N.8 |
| F-L2-04 | `cancellation_modifier` = 1 on all 150,150 rows -- no code path yet observed that varies it | SQL census | N.8 Earned-Signal |
| F-L2-05 | `system_convergence_count` 0/150,150 non-NULL | SQL census | D-SYNTHESIS |
| F-L2-06 | `cross_system_consensus_count` 0/150,150 non-NULL | SQL census | D-SYNTHESIS |
| F-L2-07 | `contradicts_signals_array` 0/150,150 non-NULL | SQL census | D-SYNTHESIS |
| F-L2-08 | `classical_sources_array` populated on **156 of 150,150** rows, and only for `yoga_label:yoga_name` (125) + `dosha_label:dosha_name` (31) | SQL census | D-GROUNDING |
| F-L2-09 | `source_corroboration_count_by_text` is a **hardcoded 2 (135,042 rows) or 5 (14,664)** while `classical_sources_array` is empty on 99.9% of those rows -- a corroboration count with no sources behind it | SQL census | N.8 Earned-Signal; N.7 item 4 |
| F-L2-10 | `source_corroboration_count_by_verse` > 0 on **zero** rows | SQL census | D-GROUNDING |
| F-L2-11 | `citation_ref` is populated on all rows but carries **internal work-package refs** (`WP-2.5/LCA-10/pushkara`), not classical citations -- a field whose name promises grounding and whose content is provenance | SQL census | D-GROUNDING; N.7 |
| F-L2-12 | `divisional_corroboration_count` > 0 on zero rows | SQL census | D-SYNTHESIS |
| F-L2-13 | **All 22 L2 assets have `integrity_check_sql` = NULL.** L2 has no data-correctness gate at all | asset_registry | C12 |
| F-L2-14 | Only 3 of 22 have `expected_volume_formula` (`bo_bimba`, `bo_karanajala`, `bo_samskara`) -- per C12 a NULL formula is itself the defect | asset_registry | C12 |
| F-L2-15 | 9 of 22 are `catalog_status = DRAFT`; `bo_cdlm_summary` and `bo_chart_gestalt` carry **NULL `target_table`** despite `bodha_cdlm_chart_summary` / `bodha_chart_gestalt` existing | asset_registry | D-SERVICE |

## W1 DEEP FINDINGS -- SALIENCE CHAIN (subagent A, 2026-09-04T22:52Z)

Source of truth for salience: `bodha_writers/formulas.py:541` `salience_formula_v2`, called from
`bo_laksana.py:1942` via `_compute_salience` (`:1864`). All static terms are plain nullable
`NUMERIC` with **no DB default** (`platform/migrations/325_l2_bodha_enriched_schema.sql:93-107`).

| id | defect | class | evidence |
|---|---|---|---|
| D1 | `_av_multiplier` thresholds (7/5/3/1) are **bhinnashtakavarga** scale but the feed is **sarvashtakavarga** (measured 23-33 per house) -- saturates at the top bucket 1.15 on 149,375/150,150 rows | correctness, units mismatch | `formulas.py:90-99` vs `bo_laksana.py:957-983` |
| D2 | `int(fact_value_num or 28)` -- the NULL fallback itself lands in the top AV bucket | N.7 item 6 (favorable-sounding default) | `bo_laksana.py:981` |
| D3 | `argala_modifier` is absent from `SalienceInputsV2` entirely -- dropped at the v1->v2 formula upgrade; 41,760 L1 argala facts unconsumed | dead column + unused L1 authority | `formulas.py:512-539`; 9 hardcoded `None` write sites |
| D4 | `tags["vargottama_amp"|"neechabhanga"|"cancellation"|"orb_tightness"]` -- **0 of 139,471** L1 facts carry any of those `fact_value_jsonb` keys. Four detectors that cannot fire | N.8 | `bo_laksana.py:1912-1915`, `:2023-2030` |
| D5 | `bo_vargottama_dhana` hardcodes `vargottama_amplification=0.0` while expressing the amplification through `class_prior=1.15` -- the named column misreports what the writer computed | N.7 item 3 | `vargottama_dhana_emitter.py:125` vs `:285` |
| D6 | `cancellation_modifier` has **no detector anywhere**; the documented "0.1 = cancelled yoga" semantic was never implemented | N.8 unearned green -- should be NULL | every write site literal `1.0`/`None` |
| D7 | `neechabhanga_modifier` has exactly one real detector (D9 cross-check, `bo_laksana.py:2738-2742`, L1 `ga_yoga_firings`) wired to 135 of 150,150 rows | near-dead detector, but honest where it fires | 14 rows at 1.3, all `varga_pattern` |
| D8 | `specificity` is passed as `1.0` with the comment "filled in second pass by percentile UPDATE" -- **that second pass does not exist** | N.8 | `bo_laksana.py:1937`, no other reference |
| D9 | `salience_robustness` is selected by serving (`query_signals.ts:120`) and written by nobody | dead column | migration `393_bodha_msr_signals_v2_cols.sql:10` |
| D10 | `salience_inputs_complete = false` on **100%** of 150,150 rows | honest flag, alarming value | SQL census |
| D11 | Dead duplicates `_av_mult` / `_HOUSE_WEIGHT` in the writer shadow `formulas.py`, zero call sites | drift hazard | `bo_laksana.py:1831,1835` |
| D12 | `bo_karanajala` re-derives argala from house offsets (`ARGALA_POSITIONS` 2/4/11) instead of reading L1's `argala_natal_matrix` | **N.5 -- L2 re-deriving an L1 authority** | `bo_karanajala.py:502-601`, zero refs to the fact categories |
| D13 | `asset_throughput.rows_per_second` / `measurement_count` / `history` -- a throughput-measurement facility with no measurement behind it (NULL/0/`[]` on every L2 asset) | N.8 | SQL census |

**Net effect, and the reason this is the payoff layer:** with `orb_tightness == 1.0`,
`av_mult == 1.15`, `(1+vargottama) == 1.0`, `neechabhanga == 1.0`, `cancellation == 1.0`,
`specificity == 1.0`, six of thirteen multiplicands in `salience_formula_v2` are constants, and
the surviving constant 1.15 is a pure scale factor that **cancels out of every ordering**. The four
D-SALIENCE static terms contribute exactly zero discriminating power to the current 50,104-row
ranking. `composite_ranker.ts:255` already documents a live consequence: fired rows rank BELOW
not-fired ones.

**L1 sources confirmed present** (canonical chart): `argala_natal_matrix` 20,880 +
`virodha_argala_natal_matrix` 20,880 (= the plan's 41,760) with `fact_value_num` already a
normalised 0..1 strength; `net_argala_per_varga` 1,740; `ashtakavarga_bindu_per_varga` 6,720 (the
correct 0..8 bhinna feed); `ashtakavarga_kakshya_boundary` 120;
`graha_vargottama_amplification_factor` 35 (name-for-name the authority for D5's column, unread).

**Cascade + cost trap.** Nothing after `bo_laksana` recomputes salience -- `top_k_salience_rank`,
`salience_pctl_in_class`, `strength_normalized_to_chart_max`, `signature_tier` are all computed
in memory pre-INSERT inside `run_substep`. `bo_laksana_rerank` is the WRONG vehicle (it only
UPDATEs `graph_node_strength_contribution_jsonb` and `valence`). So populating the static terms
requires a **full `bo_laksana` rebuild**, then `bo_karanajala` (reads `computed_salience` for edge
strength), then `bo_laksana_rerank` (its rows were deleted). `bo_samskara` needs re-run only
because its FK `signal_id`s change -- and its reuse path is keyed on `signal_id`
(`bo_samskara.py:139`), so **new UUIDs mean 100% Vertex AI re-embedding cost** unless reuse is
re-keyed on `embedding_input_summary`. Separately, `bo_laksana.py:2941-2947` records that a
post-insert UPDATE of one scalar salience column over ~28K rows took **600 s+** against 20 indexes
(3 GIN) -- any backfill-by-UPDATE design pays that, multiplied.

## W1 DEEP FINDINGS -- SYNTHESIS ROLLUPS (subagent B, 2026-09-04T22:52Z)

| id | finding | verdict |
|---|---|---|
| S1 | `contradicts_signals_array` is a **denormalisation gap, not a missing computation** -- the data exists in `bodha_contradictions.signal_a_id/signal_b_id` (15 rows canonical). Back-fill is a pure join reaching **22 of 50,104** rows | NOW, highest value in the lane |
| S2 | Back-filling S1 **turns on a real downstream term that is currently and correctly disabled**: `bo_upaya.py:741-770` probes the column, finds 0 populated, sets `source_available=False`, and stores NULL rather than a 0.0 a reader could not distinguish from a measured zero (`:1636-1646`) | the reason S1 is worth doing at 22 rows |
| S3 | Non-participating rows must stay **NULL, never `'{}'`** -- `bo_upaya` would read an empty array as a measured "no contradictions" | binding constraint on the fix |
| S4 | `cross_system_consensus_count` is computable and discriminative at `chart_facts.fact_subject` level (N.5-clean -- references an L1 fact, does not re-derive): 188 of 4,699 subjects carry >1 tradition, **2,808 signal-rows** would get >=2, range 1-3 | NOW |
| S5 | Fact-**level** cross-tradition overlap is effectively nil (2 facts touched by >1 tradition). Any definition keyed on shared `fact_id` is dead on arrival | rules out the obvious design |
| S6 | `system_convergence_count`: the only available domain-level definition populates 50,044 rows with **mean 5.93, max 6** -- near-constant, and a reader would rationally misread "6" as "six systems agree about this signal" | N.7 item 6 risk -- see adjudication |
| S7 | **New N.8 defect:** `bodha_cgm_edges.cross_system_consensus_count` is the literal constant `1` on all 849 canonical-chart rows (`bo_karanajala.py:587,663,776,1011,1131,1180,1246,1551`) -- worse than NULL, an unearned signal wearing a measured value's clothes. The honest source `present_in_traditions_array` is already populated on all 849 | MUST |
| S8 | `bo_samvada` is a **DDL-only writer** -- it drops and recreates the `vw_chart_digest` VIEW and computes nothing per chart. Its `count_sql` returns 5 for any chart with any signal row, whether or not the writer ever ran: **it cannot read false on writer failure** | N.8 proxy -- MUST under C12 |
| S9 | `bo_samvada.py:7-17` docstring names 8 columns the view does not have | NOW, cheap |
| S10 | `bo_pramana_mapa`: all six previously-unearned flags now have real detectors, proven by the stored `notes.n8_detectors` terms on the live row. Three columns (`no_pre_answer_pass`, `ledger_independence_pass`, `discovery_not_fabricated_pass`) are correctly **NULL, not green** | no work -- N.8 already satisfied |
| S11 | `unresolved_constituent_facts_count = 49` on the canonical chart -- 49 constituent refs do not resolve to `chart_facts` | N.5 -- investigate in W2 |
| S12 | Adjudication-table precedent found: `kala_paddhati_profile` (school_tag / constraint_role / provenance / native_confirmed triple) is the direct model; `kala_gochara_authority` models the stored-ruling audit half. Full DDL sketch captured for W3 | design settled |

## HELD ITEMS

None. Charter C6: L2 has **no inbound** capability dependency -- L2 is the publisher others wait on.

## CAPABILITIES LANDED

*(charter C6 -- one line per capability the moment its PR merges; L1/L3/L4/L5 poll this section)*

Expected publications: consensus columns populated - grounding fields populated - `tail_watch`
shipped - adjudication table live.

- *(none yet -- W3 in progress)*

## COST LEDGER

| item | wall-clock | notes |
|---|---|---|
| session open + bootstrap + first census | ~15 min | worktree, charter, roster, 15 findings |

## ADDENDA ON RECORD

- Charter C12 / freeze-exception 3.5 addendum (native-granted 2026-09-05): a `service` asset's
  dependency-assert is satisfied by a current GREEN probe / `service_health`. No L2 asset is
  `asset_kind='service'` (all 22 are `data`), so this addendum binds no L2 gate -- recorded as
  required, not applied.
