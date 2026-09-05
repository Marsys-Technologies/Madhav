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

`L2-W3 in flight` (was: `L2-W2 complete -> L2-W3 open`) (opened 2026-09-04T22:30Z). 22 assets, none terminal.
W1 deliverable `L2_W1_ANALYSIS_v1_0.md`; W2 ruling `L2_W2_DECIDE_v1_0.md` (22 routes, 14 MUST,
25 NOW, 8 LATER). W4 gated on L1 freezes — `bo_sudarshana` is the frontier at 1 unfrozen
ancestor (`ga_positions`) and is the designated canary.

## HEARTBEAT

| loop | UTC | position | note |
|---|---|---|---|
| 1 | 2026-09-04T22:30Z | L2-W1 | worktree created; charter + plan 4/5 read; 22-asset roster pulled from frozen definition; first census run; 5 read-only W1 subagents dispatched |
| 2 | 2026-09-04T23:20Z | L2-W2 | all 5 W1 lanes returned; `L2_W1_ANALYSIS_v1_0.md` + `L2_W2_DECIDE_v1_0.md` written; 3 adjudications filed (#1716 tooling, #1720 system_convergence_count, #1726 sruti/verse-addressability); PR #1717 (state bootstrap) in queue |
| 3 | 2026-09-05T00:10Z | L2-W3 | five W3 PRs open (#1741 salience truth, #1752 registry accuracy + CI guard, #1755 tail-lane percentile, #1760 tail_watch trim-proofing, #1767 L1-handoff fixes); rulings received on all three of my adjudications; cross-layer DRAFT finding filed (#1753) |
| 4 | 2026-09-05T00:45Z | L2-W3 | **W4 HELD** -- verified L4's #1748 and found its grading wrong in the dangerous direction: a `bo_laksana` rebuild CASCADE-deletes 710,899 L3 rows. Filed #1770 TIME-CRITICAL. Replied to #1748 and #1750 |
| 5 | 2026-09-05T01:15Z | L2-W3 | #1770 RULED: upheld, blast radius re-measured at **864,733 rows / 12 tables / 3 layers** (the `kala_convergence -> phala_anchors -> phala_*` leg I missed), **campaign-wide HOLD** issued, **D-CND-15** recorded. Shipped the owed docstring fix (#1777). Three more W3 PRs: #1776 tail population, #1779 umbrella density. **#1741 MERGED** -- first L2 batch on main. Corroborated L5's seed-revert finding (#1757) |

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

## W3 SHIPPED (five PRs)

| PR | what | W2 items |
|---|---|---|
| #1776 | **tail population** -- `buildTailWatch`: rare-class leaders (51 verified live) + the `low_salience_high_consequence` anomalies that had three independent reasons never to reach a caller | N-14 (population), N-15 |
| #1777 | **the comment was the defect** -- `_idempotency.py` said `NO ACTION`; every FK is `CASCADE`. Owed under #1770 item 2 | D-CND-15 |
| #1779 | **four umbrellas earn their density contracts** -- hand-authored `density_contract` + a real `empty_reason` + the tail, with a test that checks the CLAIM rather than the field | N-17 |
| #1741 | **salience truth** -- bind 6 computed-but-never-written columns; AV scale fix at the feed; argala reinstated; vargottama from L1; honest NULLs for cancellation/neechabhanga; corroboration fabrication removed; dead shadow tables deleted | M-01, M-02, M-04, M-08, N-01..N-06 |
| #1752 | **registry accuracy** -- `catalog_status` sweep (9), `target_table` (2), `sort_order` collisions (2), `expected_volume_formula` (2 wrong cleared, 6 derived) + a **static CI guard** so the DRAFT bug cannot return | M-09, M-11, N-20, N-21 |
| #1755 | **tail-lane percentile** -- one shared `salience_rank` module; the five satellite writers now set `salience_pctl_in_class`, so the six rarest classes stop shipping NULL on the column the tail predicate ranks on | N-16 |
| #1760 | **`tail_watch` trim-proofing** -- hardFloor section declared once in both budget entry points + `IMMUNE_HONESTY_FIELDS` membership; both are needed and they guard different paths | N-14 |
| #1767 | **L1 handoff (#1750)** -- shadbala selector pinned to `fact_key='rupa'`; `salience_formula_version` literals unified to the constant | (L1 handoff) |

## CORRECTIONS TO MY OWN W1 FINDINGS

Recorded because W1 shipped them as findings and the close report must not repeat them.

- **A9/A10/A11 were all one defect, and a different one than I reported.** Six salience
  columns (`class_prior`, `salience_inputs_complete`, `present_but_enfeebled`, `bala_gate`,
  `functional_context_score`, `verification_rescale`) are computed by `_build_signal_row` and
  were **never bound into `_INSERT_SQL`**. Every stored row carried the DB default. Proof: the
  writer hardcodes `class_prior: 1.2` for `varga_ratification_divergence` and all 16 such rows
  read 1.000000 -- a literal cannot miss a lookup.
  - **A10 was wrong.** `salience_inputs_complete = false` on 100% of rows was reported as an
    alarming measurement; it is the column DEFAULT on an unbound column. Never a measurement.
  - **A11 was wrong about the cause.** The 0% `class_prior` variance was attributed to the
    join key convention -- which is what the in-code guard itself speculates. The join may be
    fine. And because that guard reads the in-memory dict, it can report a healthy hit rate
    while the stored column stays 1.0: a guard measuring something other than what ships.
- **L1's #1750 item 3 was off by three orders of magnitude**, and I verified rather than
  relayed it: `v2.0` 149,391 / `v2` 444 / `v1.0` 315 -- not "150,150 rows at v1.0". The real
  defect is smaller and in two parts; one fixed, one deliberately deferred as a vocabulary
  question with a live consumer.

## ADJUDICATIONS

### Raised by L2

| # | subject | state |
|---|---|---|
| #1716 | shared evidence-submission helper (`nrec`) -- Conductor-owned tooling | RULED, Option 1: `platform/scripts/nirmana/nrec` landed (PR #1731). **L2 uses it; the inline fallback is void.** It requires `--as` and CHECKS it rather than inferring, so a session cannot mint a verifier capsule for work it implemented without noticing it crossed the line |
| #1720 | `system_convergence_count` has no honest per-signal definition as plan 5 specifies | RULED, Option 1 conditionally; Option 2 the mandated fallback. **All four pre-committed tests PASSED** -- see below |
| #1726 | D-GROUNDING's `sruti` = "verse refs" is not emittable | RULED, Option 1: `sruti` scoped to text-direct + `citation_granularity`. Option 3 **rejected on the record**. Precedent **D-CND-06**: writer fix and data correction ship together |
| #1753 | cross-layer: 46 assets are `catalog_status='DRAFT'`, L3/L4/L5 entirely so | filed for routing; not L2's to fix |
| #1770 | **TIME-CRITICAL** -- an L2 rebuild CASCADE-deletes 710,899 L3 rows | OPEN. **W4 held on this** |

### Addressed to L2

| # | from | outcome |
|---|---|---|
| #1750 | L1 | 2 of 3 fixed in PR #1767; item 2 (AV multiplier) already fixed independently in #1741, and at the feed rather than by re-banding; item 3 verified and found 3 orders of magnitude smaller than reported. Replied in full |
| #1748 | L4 | Verified against my own table; **grading corrected** -- the table replaces rather than accretes, and the FKs are CASCADE not NO ACTION. Escalated as #1770. Its identity-instability point and its "stale-but-resolving is harder to detect than an orphan" framing both stand and are what prompted me to check the delete path |

## DEGENERACY THRESHOLD FOR `system_convergence_count` -- AND ITS RESULT

**Threshold pre-committed and pushed at 2026-09-04T23:14:31Z (commit `d13ef67f4`), before any
measurement of the proposed definition ran** -- ruling #1720 condition 2, on the reasoning that a
threshold chosen after seeing the numbers is not a test. Verifiable in git rather than asserted.

Definition under test: for each signal, the count of OTHER signals in the same
`(chart_id, ayanamsha_id)` sharing at least one `constituent_facts_array -> chart_facts.fact_subject`.

| # | test | degenerate if | measured (canonical chart, lahiri) | verdict |
|---|---|---|---|---|
| T1 | spread | CV < 0.25 | **CV = 2.0020** (mean 29.82, sd 59.70) | PASS |
| T2 | dominant value | any value > 60% of populated rows | top value `1` at **21.24%** | PASS |
| T3 | resolution | fewer than 8 distinct values | **74**, range 1-997 | PASS |
| T4 | within-class variation | fewer than 5 distinct inside `composite_state` | **52** across 5,497 rows, range 1-345 | PASS |

T4 is the one that decides it: the variation lives INSIDE the largest class, not merely between
classes, which is what makes it a per-signal quantity rather than a class proxy -- the exact
property the rejected domain-level definition lacked. I also committed to abandoning the
definition if a coarser grouping explained a passing distribution; I looked and could not find
one, and reported that as a negative result I searched for rather than an absence I assumed.

**Three-way storage split the measurement forced** (one ayanamsha, 10,003 signals):
7,012 rows get the count · **2,860 get a measured `0`** (facts resolve, no sharing neighbour --
real information about the signal) · **131 get `NULL`** (no resolvable constituent facts --
nothing checked, nothing claimed). Collapsing the last two would repeat the defect the standing
NULL-not-`'{}'` convention exists to prevent.

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

- **`bo_laksana` W4 dispatch -- HELD. RULED 2026-09-05: upheld and made CAMPAIGN-WIDE policy.**
  The Conductor traced the closure one hop further than I did and found the leg I missed:
  `kala_convergence` is itself a CASCADE parent of `phala_anchors`, which cascades to
  `phala_pramana` / `phala_sankrama` / `phala_sodhana` / `phala_suddha_sodhana`. **True blast
  radius: 864,733 rows across 12 tables in three layers** -- including the very table D-CND-04
  holds `ph_nimitta` rebuilds to protect. My own finding would have failed D-CND-15's own rule:
  I enumerated `pg_constraint` at depth 1 and stopped, and "transitive" is the load-bearing word.
  Hold lifts only when a fresh snapshot of the 12 tables is confirmed **restorable**, not merely
  taken. Ruled order: L2's MSR rebuild goes FIRST, L3 re-runs after as scheduled work.
  **Route correction owed to W6:** L2-W2 routed `bo_laksana` as `changed` believing its rebuild
  was in-layer. The route stands; the belief about its blast radius did not.
  *(original finding, retained)* -- Not a capability
  hold (C6) and not an E-gate hold (C2): a hard-floor hold. Verifying L4's #1748 against my own
  table showed its grading wrong in the direction that matters. `bodha_msr_signals` REPLACES
  (explicit `DELETE` in `replace_prior_msr_for_chart`; the canonical chart's three `build_id`s
  hold 49,955/104/45 rows, not nine accumulated generations), and all eight FKs onto it are
  **`ON DELETE CASCADE`**, not `NO ACTION` as `_idempotency.py`'s own docstring claims. So an
  ordinary L2 rebuild silently destroys **710,899 L3 rows** (`kala_activation` 672,551 +
  `kala_convergence` 35,365 + `kala_darshana` 1,500 + `kala_obstruction` 1,283 +
  `kala_bhavishya` 200) and orphans ~152,000 more in the five referencing tables that carry no
  FK. The DAG models ancestors; the exposure here is descendants.
  **Nothing else is held** -- all W3 work continues; none of it writes a row.
- Charter C6: L2 still has **no inbound** capability dependency. L2 is the publisher others
  wait on.

## CAPABILITIES LANDED

*(charter C6 -- one line per capability the moment its PR merges; L1/L3/L4/L5 poll this section)*

Expected publications: consensus columns populated - grounding fields populated - `tail_watch`
shipped - adjudication table live.

- **2026-09-05 -- `bo_laksana` salience writer corrected (PR #1741, MERGED).** Stated honestly,
  because C6 is about what a consumer may rely on: this lands the **writer**, not the data. The
  six previously-unwritten columns (`class_prior`, `salience_inputs_complete`,
  `present_but_enfeebled`, `bala_gate`, `functional_context_score`, `verification_rescale`) are
  now bound into the INSERT; the AV multiplier reads the correct bhinna feed; argala is live in
  the formula; vargottama reads its L1 authority; cancellation and neechabhanga store honest
  NULLs; the corroboration-count fabrication is gone. **None of it reaches stored data until
  `bo_laksana` re-runs, and that rebuild is HELD campaign-wide under #1770.** A downstream layer
  should not begin consuming corrected salience values yet -- only the guarantee that the next
  rebuild produces them.
- *(the other eight W3 PRs are in the merge queue; each is announced here the moment it merges)*

**Ruled definition, to be carried here verbatim when the grounding lane lands (#1726 condition 3):**
`sruti` means **text-direct at the finest granularity the corpus supports** -- NOT verse-direct.
`classical_text_chunks.chapter` is a page number and `verse_start`/`verse_end` are column
indices, so a chapter-verse citation cannot be honestly composed from this corpus. The
limitation is carried machine-readably by `citation_granularity IN ('page_column',
'chapter_verse')`, NOT NULL with no writer default, and the rendered citation string is
self-describing ("p.211 col.1", never "211.1"). Plan §2's D-GROUNDING wording says "verse
refs"; this is the ruled reading of it.

## COST LEDGER

| item | wall-clock | notes |
|---|---|---|
| session open + bootstrap + first census | ~15 min | worktree, charter, roster, 15 findings |

## ADDENDA ON RECORD

- Charter C12 / freeze-exception 3.5 addendum (native-granted 2026-09-05): a `service` asset's
  dependency-assert is satisfied by a current GREEN probe / `service_health`. No L2 asset is
  `asset_kind='service'` (all 22 are `data`), so this addendum binds no L2 gate -- recorded as
  required, not applied.
