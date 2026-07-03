---
canonical_id: CLAUDECODE_BRIEF_BA_P1_WIRING_AND_NAMING
version: 1.0
status: READY-FOR-EXECUTION — gated on BA-P0 final AC (assess_career ≤100k on prod, post-merge #395)
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program) — for execution by Claude Code in Antigravity
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P1 (tool estate: wiring + naming)
grounding_authority: 00_ARCHITECTURE/BA_GROUNDING_REPORT_v1_0.md (esp. §2 G-4 wiring matrix, PD-1/3/7)
substance_authority: RETRIEVAL_MODERNIZATION_MASTER_PLAN_v1_0.md §3 (tool census, groups, dedup) + §5
  (envelope, as amended by BA_RATIFICATION_GUIDANCE §2.2)
objective: >
  Make the ENTIRE astrological data estate reachable: wire the uncovered assets as MCP tools, adopt the
  naming standard (Phase-1 aliases), collapse duplicates — from the grounded 53-tool baseline to full
  coverage with ≤6 documented deferrals. No ranking changes (P2), no writer/data changes (P3).
may_touch: ["platform-mcp tool registration/bridge files", "retrieval capability registration (NEW capabilities only — no changes to existing capability logic)", "ONE new handler (ga_transit_anchors)", "tool descriptions", "MCP_E2E test additions", "governance docs"]
must_not_touch: ["ranking/salience logic", "any pipeline writer", "any migration (PD-1: mimamsa_insight_units EXISTS — no DDL needed)", "orchestrator/planner/cockpit", "existing tool response logic beyond adding aliases"]
---

# BRIEF BA-P1 — WIRING + NAMING (the estate becomes whole)

## Step 0 — Ground on the wiring matrix
Read BA_GROUNDING_REPORT §2 G-4 (the 4-column matrix: handler / registry / MCP-exposed / serving) and
re-verify at HEAD. The 53-tool census is the baseline (PD-3). Work items = every row where
MCP-exposed=false. Per PD-7 the Group-1 gap is MCP-exposure only (bridge entries: TOOL_NAME_TO_URI +
SURGICAL_TOOLS/MCP_TO_RETRIEVAL_TOOL + tool registration), EXCEPT ga_transit_anchors (new handler needed).

## Step 1 — Group 1: computed-chart tools (highest value)
Expose per RM §3.2 Group-1 table: `ganita_strength_get` (shadbala/ishta-kashta/vimsopaka/bhava-bala/AV),
`ganita_structural_get` (ONE tool, facet param: aspects|argala|dispositors|parivartana|yoga_fires|
dosha_fires|conjunctions|sambandha|functional|graha_yuddha), `ganita_condition_get`,
`ganita_sade_sati_get`, `ganita_tajaka_get`, `ganita_nakshatra_get`, `ganita_yogas_get`,
`phala_rectification_get`, and `ganita_transit_anchors_get` (NEW handler — read ga_transit_anchors
fact_categories; follow the get_sade_sati handler as template).

## Step 2 — Group 2: reference-layer tools (citability)
`ref_rules_search`, `ref_yogas_get`, `ref_doshas_get`, `ref_dignity_reference_get`,
`ref_dasha_systems_get`, `ref_nakshatra_get`, `ref_transit_rules_get` — thin read tools over the L0
tables; global scope (no chart_id), bounded, cited.

## Step 3 — Group 3: synthesis-adjacent surfaces
`mimamsa_insight_get` (mimamsa_insight_units — EXISTS per PD-1, 14 rows; serve honestly with
`calibration: prior_only` flag), `bodha_discoveries_get` (bodha_discoveries), `kala_life_arc_get`
(ka_jivana_parva view). Defer (document in close report): medical/vastu/prashna (subsystem waves),
remaining mi_* internals (P6), ka_tulana if non-trivial.

## Step 4 — Naming Phase 1 + dedup
Register `<layer>_<topic>_<type>` aliases for all 53 existing tools per MCP_TOOL_NAMING_STANDARD §3
(BOTH names call one handler; deprecation notes on old names; NO removals — Phase 3 stays gated).
Dedup per ratified dispositions: `bodha_remedies_get` primary; `bodha_remedies_search` → alias;
`ref_remedies_search` retained. Sweep for further same-topic duplicates; consolidate by aliasing only.

## Step 5 — Envelope v1 on NEW tools only
Every NEW tool returns the RetrievalEnvelope (RM §5 as amended: structured-verdict slot [null for now],
ranking_basis [null until P2], grounding block with fact_ids + citations + grounding_score, pagination,
drill_pointers, judgment_flags, dual insight_type/query_class tags). Existing tools: untouched (P2
retrofits). Token cap ≤25k default on every new tool.

## Step 6 — Verify + close
(a) E2E: every new tool + every alias returns structured data on prod for 482012f1 AND 1c826d5a
`[verify-against: prod]`; (b) the four-measure smoke (Volume/Relevance/Accuracy/Ranking-n/a) recorded per
new tool; (c) coverage recount vs the 31-uncovered list → ≤6 remaining, each with a named deferral reason;
(d) no regression on the P0 baseline latency table (spot-check 3 tools); (e) PD-5 check: if ANY
asset_registry row was touched (should be none), ASSET_NAMES.ts + ASSET_MAP updated; (f) CURRENT_STATE +
SESSION_LOG close per governance; status → COMPLETE.

**Exit gate:** the 38-topic checklist (RM §7) shows every topic REACHABLE via a named primary tool
(topics awaiting P3+ data — bhava arudhas, karakamsha, promise register — marked "reachable-pending-data,"
not dark); zero tools over cap; both charts verified.
