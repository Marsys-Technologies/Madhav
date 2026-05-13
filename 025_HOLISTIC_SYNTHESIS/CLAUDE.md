# 025_HOLISTIC_SYNTHESIS — Instructions

**This layer is the answer to domain-segregated context-collapse.** Every query routes through here before reaching L3 Domain Reports (per **PROJECT_ARCHITECTURE_v2_2** §C.3 / §H.4 Whole-Chart-Read discipline).

## Current artifacts (authoritative)

| Artifact | Role |
|---|---|
| **`UCN_v4_0.md`** | **Unified Chart Narrative — canonical single-file mother document** (merged v1.0→v1.1→v2.0→v3.0). **Cite this** for new L3 work. |
| **`CGM_v9_0.md`** | Chart Graph Model v9.0 — nodes/edges feeding MSR, CDLM, RM |
| **`MSR_v3_0.md`** | Master Signal Register (**514** signals v3.1) |
| **`CDLM_v1_1.md`** | Cross-Domain Linkage Matrix (9×9, v8.0-corrected cells) |
| **`RM_v2_0.md`** | Resonance Map |
| **`RED_TEAM_L2_5_v1_0.md`** | Red-team audit of the L2.5 stack |

Prior **`UCN_v1_0.md` … `UCN_v3_0.md`** remain as **archival slices** referenced by the merge; do not cite them ahead of **`UCN_v4_0.md`** for new writing.

## Build sequence (historic)

CGM → MSR → CDLM → RM → UCN — see Architecture §I for session history. **L2.5 stack for this chart is CLOSED at CURRENT versions above**; further work is **expansion** (MSR §VII.4, CGM divisional depth), not foundational build-out.

## Critical principle

The UCN reads the chart as **one organism**. Every Domain Report (L3) must cite **UCN_v4_0** (and MSR/CDLM/RM/CGM as needed). Nothing siloed.

## Completeness guarantee

Mode B matrices and CGP audit completed per **SESSION_LOG** — see **`01_FACTS_LAYER/CGP_AUDIT_v1_0.md`** in Facts Layer.

## STRUCTURED projection (Phase 14D — 2026-04-28)

All five L2.5 source files now have a parallel structured Postgres projection (`l25_*` tables) queryable by the LLM router as deterministic tools. The markdown files remain the canonical authoring source; the structured tables are a read-only projection updated by the pipeline on each build.

| Table | Rows | LLM Tool |
|---|---|---|
| `l25_msr_signals` | 499 | `query_msr_signals` |
| `l25_ucn_sections` | 134 | `query_ucn_section` |
| `l25_cdlm_links` | 81 | `query_cdlm_link` |
| `l25_cgm_nodes` | 234 | `query_cgm` |
| `l25_cgm_edges` | 21 | `query_cgm` (joined) |
| `l25_rm_resonances` | 28 | `query_resonance` |

Spec: `00_ARCHITECTURE/L2_5_STRUCTURED_LAYER_v1_0.md`. Report: `00_ARCHITECTURE/PHASE_14D_L2_5_PARITY_REPORT_v1_0.md`.

**Query routing guideline:** Use the structured tools for attribute-filtered lookups (planet=SATURN, house=7, domain=career). Use `rag_chunks` vector search for open semantic queries. Both surfaces serve the same source data; the router selects per query type.

## L2 Archival Notice

**L2 (`02_ANALYTICAL_LAYER/`) was archived in Phase 14F (2026-04-28).** All `MATRIX_*` and `DEEP_ANALYSIS_*` files are preserved at `99_ARCHIVE/02_ANALYTICAL_LAYER/` for historical audit only. Do not cite L2 artifacts in new work; the L2.5 stack above supersedes them entirely.
