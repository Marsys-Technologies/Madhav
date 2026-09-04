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

`L2-W1` (opened 2026-09-04T22:30Z). 22 assets, none terminal.

## HEARTBEAT

| loop | UTC | position | note |
|---|---|---|---|
| 1 | 2026-09-04T22:30Z | L2-W1 | worktree created; charter + plan 4/5 read; 22-asset roster pulled from frozen definition; first census run; 5 read-only W1 subagents dispatched |

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
  routes are still ruled in `L2_W2_DECIDE_v1_0.md` before any W4 dispatch.

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

## HELD ITEMS

None. Charter C6: L2 has **no inbound** capability dependency -- L2 is the publisher others wait on.

## CAPABILITIES LANDED

*(charter C6 -- one line per capability the moment its PR merges; L1/L3/L4/L5 poll this section)*

Expected publications: consensus columns populated - grounding fields populated - `tail_watch`
shipped - adjudication table live.

- *(none yet)*

## COST LEDGER

| item | wall-clock | notes |
|---|---|---|
| session open + bootstrap + first census | ~15 min | worktree, charter, roster, 15 findings |

## ADDENDA ON RECORD

- Charter C12 / freeze-exception 3.5 addendum (native-granted 2026-09-05): a `service` asset's
  dependency-assert is satisfied by a current GREEN probe / `service_health`. No L2 asset is
  `asset_kind='service'` (all 22 are `data`), so this addendum binds no L2 gate -- recorded as
  required, not applied.
