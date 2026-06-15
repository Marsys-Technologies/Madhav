---
artifact: L2_BODHA_ASSET_TABLE_BRIEF_MAP_v1_0.md
canonical_id: L2_BODHA_ASSET_TABLE_BRIEF_MAP
version: 1.0
status: CURRENT
authored_by: Cowork (verified against repo) 2026-06-12
authored_for: the L2 Bodha campaign — the master asset↔table↔brief reconciliation index
purpose: >
  The single authoritative answer to "is the asset→table→brief mapping reconciled, correct, and
  complete?" Every Bodha asset, its verified built tables, its depends_on, its planned writer
  brief, and the live status of each link. Verified against the repo at main HEAD; updated as
  briefs are authored and the seed correction lands.
verification_basis: >
  Tables: grep of migration 226 (CREATE TABLE). Asset→table: asset_registry_seed.ts (live).
  depends_on: asset_registry_seed.ts (live). Briefs: ls of 00_ARCHITECTURE/BRIEFS/. All as read
  2026-06-12. DATA-PLANE (is it applied to prod?) is NOT confirmed here — that is Phase G (V1/V5/V6).
read_in_combination_with:
  - 00_ARCHITECTURE/L2_BODHA_BUILD_CAMPAIGN_v1_0.md (§14 locked map, §9 brief batches, §0.0 decisions)
  - 00_ARCHITECTURE/L2_BODHA_PHASE0_ALIGNMENT_ROADMAP_v1_0.md (the A–G phase runway)
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BODHA_P0E_SEED_CORRECTION_v1_0.md (the pending seed fix)
---

# L2 Bodha — Asset ↔ Table ↔ Brief Master Map v1.0

## §0 — Reconciliation verdict (verified 2026-06-12)

| Layer | Status | Note |
|---|---|---|
| **Tables ↔ migration DDL** | ✅ COMPLETE & CORRECT | All 23 tables in migration 226 match the §14 locked set exactly (20 spec `bodha_*` + 3 §13.1 extensions + `synthesis_quality_scorecard` + `signal_type_registry`) + 8 MVs. |
| **Asset → tables (design)** | ✅ LOCKED & CORRECT | §14 + the v1.1 specs define every asset's full table set. |
| **Asset → tables (live seed)** | ⚠️ 2 fixes PENDING | Seed correct except `bo_samvada` (still points at `bodha_rm_resonances`; should be UCD/none) and `bo_upaya` (needs to OWN `bodha_rm_resonances` + sum 6 tables). Both in the authored-but-not-yet-applied `BODHA_P0E_SEED_CORRECTION` brief. |
| **Asset → writer briefs** | ❌ INCOMPLETE (0 of 8 writer briefs) | Only the seed-correction brief exists. The 8 per-asset writer briefs are the post-alignment step (campaign §9) and are not yet written. |

**Bottom line:** the *table* layer is fully reconciled; the *asset→table* mapping is design-locked
and awaits the seed correction landing (2 rows); the *asset→brief* mapping is **not complete** —
the writer briefs do not exist yet. This is on-plan (briefs follow alignment), but the honest
answer to "complete?" is **no, not yet** — and this index is the thing that will make it complete.

## §1 — The master map (verified)

Legend: ✅ done/correct · ⚠️ pending a known fix · ❌ not yet created. "Tables built" = confirmed
in migration 226. "Seed" = current `target_table` in `asset_registry_seed.ts`. MVs are NOT counted
in `count_sql` (derived).

| asset | spec | tables it OWNS (built ✅) | primary | seed target_table now | depends_on (live ✅) | writer brief | brief status |
|---|---|---|---|---|---|---|---|
| `bg_signal_type_registry` | A10 §5 (G52) | `signal_type_registry` ✅ | `signal_type_registry` | `signal_type_registry` ✅ | `[]` | `CLAUDECODE_BRIEF_BODHA_G52_PREDICATE_AUTHORING` | ❌ (table+starter seed done; full 500–700 authoring brief not written) |
| `bo_laksana` | A10 | `bodha_msr_signals` ✅ (+3 MVs ✅) | `bodha_msr_signals` | `bodha_msr_signals` ✅ | `['bg_signal_type_registry','ga_structural','bg_rules']` ✅ | `CLAUDECODE_BRIEF_BO_LAKSANA` | ❌ not written (Batch 1 root) |
| `bo_sangati` | A11 | `bodha_cdlm_cells` ✅, `_domain_rollups` ✅, `_chart_summary` ✅, `_pattern_clusters` ✅, `_evolution_gradients` ✅, `bodha_convergence` ✅ | `bodha_cdlm_cells` | `bodha_cdlm_cells` ✅ | `['bo_laksana']` ✅ | `CLAUDECODE_BRIEF_BO_SANGATI` | ❌ not written (Batch 2) |
| `bo_bimba` | A12 (nodes) | `bodha_cgm_nodes` ✅ | `bodha_cgm_nodes` | `bodha_cgm_nodes` ✅ | `['bo_laksana']` ✅ | `CLAUDECODE_BRIEF_BO_BIMBA` | ❌ not written (Batch 2) |
| `bo_karanajala` | A12 (edges+struct) | `bodha_cgm_edges` ✅, `_sub_graphs` ✅, `_motifs` ✅, `_chart_topology_summary` ✅, `bodha_cgm_paths` ✅, `bodha_contradictions` ✅ | `bodha_cgm_edges` | `bodha_cgm_edges` ✅ | `['bo_laksana']` ✅ | `CLAUDECODE_BRIEF_BO_KARANAJALA` | ❌ not written (Batch 2 — deepest-built) |
| `bo_upaya` | A13 | `bodha_rm_resonances` ✅, `_remedy_prescriptions` ✅, `_dasha_windowed_prescriptions` ✅, `_dosha_remedy_bundles` ✅, `_pattern_remedies` ✅, `_chart_summary` ✅ | `bodha_rm_resonances` | `bodha_rm_remedy_prescriptions` ⚠️ (needs to own resonances + sum) | `['bo_laksana','bo_sangati']` ✅ | `CLAUDECODE_BRIEF_BO_UPAYA` | ❌ not written (Batch 3) |
| `bo_samskara` | embeddings | `bodha_signal_embeddings` ✅ | `bodha_signal_embeddings` | `bodha_signal_embeddings` ✅ | `['bo_laksana']` ✅ | `CLAUDECODE_BRIEF_BO_SAMSKARA` | ❌ not written (Batch 2) |
| `bo_samvada` | A14 (Option A) | **NONE** — UCD = read-side `vw_chart_digest` + `query_ucd` | n/a | `bodha_rm_resonances` ⚠️ (must clear → UCD) | `['bo_laksana']` ✅ | (no writer brief; UCD read-tool spec instead) | ⚠️ seed fix pending; not a writer |
| `bo_pramana_mapa` | scorecard | `synthesis_quality_scorecard` ✅ (global) | same | `synthesis_quality_scorecard` ⚠️ (drop `WHERE chart_id`) | `[]` ✅ | `CLAUDECODE_BRIEF_BO_PRAMANA_MAPA` | ❌ not written (Batch 3) |

**Table accounting:** 20 distinct `bodha_*` tables owned across the writers + `synthesis_quality_scorecard`
+ `signal_type_registry` = **22 tables**; plus `bodha_signal_embeddings` is the 21st `bodha_*`. Migration
226 = **23 tables total + 8 MVs**. (`bodha_contradictions` + `bodha_convergence` + `bodha_cgm_paths`
are the 3 §13.1 extensions.) The earlier "21" recount omitted the two non-`bodha_`-prefixed tables.

## §2 — The 3 open links (what makes it NOT-yet-complete) + who closes each

1. **`bo_upaya` seed row** (⚠️) — re-point to own `bodha_rm_resonances` (primary) + summed count_sql
   across all 6 RM tables. → `BODHA_P0E_SEED_CORRECTION` brief, Antigravity applies (Phase E).
2. **`bo_samvada` seed row** (⚠️) — clear off `bodha_rm_resonances`; set to UCD/Option-A (view, no
   count). → same correction brief.
3. **8 writer briefs + the G52 authoring brief** (❌) — do not exist yet. → Cowork authors them
   post-alignment, campaign §9 batch order: Batch 1 `bo_laksana` → Batch 2 (`bo_sangati`,
   `bo_bimba`, `bo_karanajala`, `bo_samskara`, + the UCD read-tool spec for `bo_samvada`) →
   Batch 3 (`bo_upaya`, `bo_pramana_mapa`). G52 full-predicate authoring brief is its own item
   (gates `bo_laksana`).

## §3 — What IS fully reconciled (no action)
- All 23 tables built to spec (migration 226) — names, the 3 §13.1 extensions, the scorecard, G52.
- 6 of 8 `bo_` seed `target_table`s correct; `bo_laksana.depends_on` corrected (G52 + ga_structural).
- A10–A14 specs at v1.1 — text matches built tables.
- The §14 design map — authoritative and complete.

---

*End of L2_BODHA_ASSET_TABLE_BRIEF_MAP_v1_0. Verdict: tables COMPLETE; asset→table design LOCKED,
2 seed rows pending the correction brief; asset→brief INCOMPLETE (0 of 8 writer briefs written).
This index makes every open link explicit and is updated as the seed correction lands and briefs
are authored.*
