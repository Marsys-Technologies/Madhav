---
artifact: A14_UCN_RETIRED_TO_UCD_v1_0.md
document: A14 UCN retirement + rename to UCD (Unified Chart Digest)
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: Option α; UCN retired as separate asset; rename to UCD; 5 truly-new items fold into A8/A11/A12 chart_summaries)
---

# A14 — Retirement decision + rename to UCD

## §1 — Decision

A14 (formerly UCN — Unified Chart Narrative) is **retired as a separate per-chart writer asset**. The conceptual chart-digest surface is **renamed UCD — Unified Chart Digest** to reflect:
- Narrative removal per prime directive (no narration / no opinion)
- Retention of "Unified" — the surface still unifies across systems, traditions, domains
- "Digest" — pure computed structural digest, no LLM at write time

## §2 — Rationale

A14 as originally proposed was ~70% redundant with A8-A13. Component-by-component overlap audit found:
- 10 fields duplicating A8/A11/A12/A13 (dominant/weakest grahas + domains, chart typology, cross-system convergence, time-arrow profile, pattern fingerprints, multi-channel render priorities, per-tradition views, M6 calibration anchors, validity anchors, life arc phases)
- 2 fields derivable from existing aggregates (master convergence index, fragmentation aggregation)
- 1 architectural layer violation (audience-tier renders — house-rules concern, not data-layer)
- 5 truly-new items that justify computation

Per the LLM-information-transfer lens: an LLM querying A8 + A11 + A12 + A13 chart_summaries already gets a structurally complete chart read. A14 as a 6,700-row-per-chart layer is fat without function.

## §3 — The 5 truly-new items + where they land

| Truly-new field | Folds into |
|---|---|
| `classical_archetype_assignments_jsonb` (G8 archetype library matching) | A11 chart_summary (new column) |
| `karmic_signature_jsonb` (Rahu+Ketu+12H+outer planet aggregation as one structural argument) | A12 chart_topology_summary (new column) |
| `purushartha_quadrant_strengths_jsonb` (dharma/artha/kama/moksha balance from bhava bala) | A8 chart_summary (new column) |
| `arudha_lagna_divergence_score` + `arudha_lagna_divergence_jsonb` (Arudha vs Lagna structural comparison) | A12 chart_topology_summary (new columns) |
| `master_convergence_index` (single 0-1 chart coherence score with decomposition) | A11 chart_summary (new column + decomposition jsonb) |

Net change: 5-6 column additions across 3 existing summary tables. Zero new writer pipeline. ~50 extra rows per chart total (vs ~6,700 in original A14 proposal).

## §4 — UCD as a conceptual surface, not a writer

UCD is now the **read-side conceptual surface** that the LLM queries to get the "chart digest." Under the hood, UCD = the join of A8 chart_summary + A11 chart_summary + A12 chart_topology_summary + A13 chart_summary (plus the 5 folded fields).

Implementation: a single MCP retrieval tool `query_ucd(chart_id, ayanamsha_id, snapshot_type)` that:
1. Joins the 4 chart_summary rows for the requested snapshot
2. Returns one wide row containing all chart-level fields
3. Optionally materialized as a Postgres view `vw_chart_digest` for retrieval speed

This preserves the LLM ergonomics of "one tool call → chart digest" without the architectural bloat of a separate writer.

## §5 — Audience-tier renders explicitly out-of-scope

The original A14 proposed audience-tier renders (super_admin / acharya / client) at write time. This was a layer violation. Tier-conditioned presentation lives at READ time via the house-rules system + system prompt + tier-conditioned tool gating. NOT at write time. The data layer remains tier-agnostic.

## §6 — Cross-tradition synthesis layer explicitly out-of-scope

The original A14 proposed a "unified read" cross-tradition synthesis. A13 already does this via `cross_tradition_convergence_jsonb` and A12 via `present_in_traditions_array` on every node/edge. LLM at read time can compose the synthesis.

## §7 — Brief track impact

Per-chart asset count: 13 (A1-A13) + 2 new (A15 Time-Synchronicity + A16 Phase-Locked Event Anchors) = 15 actual writer assets. A14 retired; UCD is the conceptual digest surface.

## §8 — Outcome

A14 marked `retired_with_rationale` in state.json tracker. UCD documented as conceptual surface. A8 + A11 + A12 spec amendments queued for the 5 folded columns.

---

*End of A14_UCN_RETIRED_TO_UCD_v1_0.md — LOCKED 2026-05-29. Native sign-off complete.*
