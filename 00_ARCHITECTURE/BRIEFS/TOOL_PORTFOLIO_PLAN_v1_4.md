---
canonical_id: TOOL_PORTFOLIO_PLAN
version: 1.4
status: DRAFT — IMPLEMENTATION PLAN (multi-tenant aligned), READY FOR PER-PHASE EXECUTOR BRIEFS
supersedes: TOOL_PORTFOLIO_PLAN_v1_3.md (archive on approval); v1.3 facts/decisions PRESERVED except where noted
date: 2026-05-27
author: Cowork planning session (no implementation; plan only)
evidence_base:
  - 00_ARCHITECTURE/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md   # verified facts (authoritative)
  - 00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md           # multi-guest/multi-chart (§3,§5,§6,§7.5,§8)
  - 00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md           # deterministic data layer (removes redaction)
  - 00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE_v1_0.md            # chart_id data plane + charts registry
note: >
  v1.4 is a DELTA overlay on v1.3. v1.3 stands in full; this document changes only what
  multi-tenancy + the North-Star require, adds chart_id + authorizeChartAccess to the relevant
  phases, restates sequencing with the new cross-dependencies, and keeps each phase a standalone
  CLAUDECODE_BRIEF unit. Read v1.3 for the unchanged phase bodies.
---

# Tool Portfolio — Implementation Plan v1.4 (multi-tenant aligned)

## §0 — What v1.4 changes (and what it preserves)

**Preserved from v1.3 (unchanged):** every verified fact (40 registered / 17 ghost tools / null
`query_schema` / live B.11 gap / SURGICAL_TOOLS dups / dead code), and the locked decisions —
unified contract, shared Zod schema module as schema SoT, full canonical rename in one atomic batch,
B.11 hotfix pulled forward, gateway-now/native-later, control-model-B-surgical.

**Changed by multi-tenancy (this overlay):**
1. **`chart_id` becomes a first-class, *required* input** on chart-scoped tools, landed once in the
   shared contract (Phase 2/3). Chart-independent tools (ephemeris/classical/panchang) stay un-keyed.
2. **The gateway becomes the per-chart authorization chokepoint** — `invoke_tool` calls the single
   `authorizeChartAccess(principal, chart_id, action)` before dispatch, for *both* channels, co-located
   with the B.11 forced-first guarantee it already hosts (Phase 5).
3. **Tier excision (Phase 8) is reframed as overlap-removal and hard-gated** on the multi-tenant authz
   layer (North-Star Track A1) being live first. The deterministic data layer removes the
   disclosure/redaction rationale entirely — nothing left to redact.
4. **The gateway lives in `lib/pipelines/shared/`** (North-Star §5), consumed by both isolated
   pipelines — not a new inline branch in `consume/route.ts`. Coordinates with the pipeline-isolation arc.
5. **Tier-coupled controls become Command Center capability gates** (North-Star §8) — which tools are
   on, per-key scopes, chart-grant policy, data-source enablement via the manifest `data_dependency`
   graph — not tier redaction.
6. **Data-layer rebuild changes tool *semantics*, not contracts.** The loader projects deterministic
   JSONL → the existing Postgres schema, so retrieval tools keep working — but the synthesis tools now
   return deterministic structure + *computed salience* (no opinion prose). Descriptions update; B.11
   holistic-read is satisfied from the deterministic T1, not stored T2.

## §1 — Multi-tenant facts the plan honors (from North-Star)

- Two tenancy axes: multi-**guest** (`role: super_admin | guest`) + multi-**chart** (`chart_id uuid`).
  `charts.client_id` → `charts.owner_id` + subject birth-data; new `chart_grants` ACL (view-only).
- **One authz brain:** `authorizeChartAccess(principal, chart_id, action)` governs web AND MCP.
  Access = **role** (which portal surfaces) + **chart_grants** (which charts). **No tiers.**
- MCP per-chart is realized *through* the unified contract + gateway (North-Star §6) — not a separate
  MCP mechanism. Optional API-key `default_chart_id`; an explicit `chart_id` always overrides; authz is
  per-request, never assumed from the key.

## §2 — Chart-scoped vs chart-independent tool classification (required deliverable)

This is the authoritative `chart_id`-requirement map the shared contract encodes (`chart_scoped: bool`).

**Chart-scoped → `chart_id` REQUIRED** (synthesize/read over a specific chart):
`chart_summary`, `holistic_bundle`, `multi_school_bundle`, `query_chart_facts`, `query_signals`/`msr_sql`,
`query_dasha_periods`, `query_divisional_chart`, `kp_query`, `query_kp_ruling_planets`, `query_varshphal`,
`get_cgm_subgraph`, `query_ucn_walk`, `query_cdlm_lookup`, `query_rm_walk`, `pattern_register`,
`resonance_register`, `cluster_atlas`, `contradiction_register`, `lel_query`, `query_signal_state`,
`timeline_query`, `query_remedial_mantras` — **plus the wired ghost tools** `tara_balam_for_native`,
`chandra_balam_for_native`, `query_transits_over_natal`, `query_yogas_active_now`, `get_shadbala_full`,
`get_planet_avastha`, `interpret_current_dasha`, `query_dasamsha_career`, `query_shashtiamsha`,
`query_drekkana_drishti`, `saham_query`, `query_planetary_period_predictions`, `query_jaimini_chara_dasha`,
`query_remedies_prescribed`.

**Chart-independent → NO `chart_id`** (general ephemeris / classical T0 / general panchang):
`query_ephemeris`, `query_transit_event`, `query_panchanga`, `muhurta_finder` (general electional),
`read_classical_text`, `read_asset`, `cross_school_lookup` (classical convergence on a claim),
`query_eclipse_transits` (general eclipse detection), `query_planet_war` (general graha-yuddha event).

**Hybrid → `chart_id` OPTIONAL (needs a design call — §6 open Q):**
`vector_search` (rag_chunks = classical-general + chart-derived chunks; `chart_id` scopes the
chart-derived subset while classical stays general), `domain_report_query` (likely chart-scoped after
the rebuild — confirm).

**Meta / governance (chart binding by purpose):** `log_prediction` (chart_id required — it's about a
chart), `record_outcome` (chart inferred from `prediction_id`), `flag_disagreement` (chart_id optional
tag), `get_trace`/`list_recent_queries` (keyed by trace/key — chart-independent), `tool_health`/
`data_coverage` (system-wide — chart-independent, super-admin).

## §3 — Per-phase deltas (only changed phases; others stand per v1.3)

- **Phase 0 (hygiene)** — unchanged. Independent of North-Star; ship immediately.
- **Phase 1 (B.11 hotfix)** — unchanged; still the interim fix. Note: the gateway (Phase 5) becomes the
  permanent B.11 home; the deterministic layer means holistic-read is satisfied from T1 (DATA_LAYER §4).
- **Phase 2 (canonical contract spine)** — **ADD**: `chart_id` as a required field in the shared Zod
  schema for every chart-scoped tool (§2 map); add `chart_scoped: bool` + `data_dependency` to the
  contract/manifest metadata (the latter powers Command Center data-source gating, §8). Backfill manifest
  `query_schema` to include `chart_id`. This is the "land `chart_id` once" point (North-Star §7.5).
- **Phase 3 (dual-channel generation + portal schema fix)** — **ADD**: both channels inherit `chart_id`
  from the contract. **Remove the `?? NATIVE_CHART_ID` fallback** in `query_signal_state.ts` +
  `muhurta_finder.ts` — but this removal is **gated on the data plane being `chart_id`-keyed** (Track B /
  PLATFORM_REBUILD). Until then, the contract carries `chart_id` and the resolver defaults to the native
  chart. So: add `chart_id` to the schema NOW; flip the fallback OFF when the data plane is keyed.
- **Phase 4 (wire ghost tools)** — unchanged, except each wired tool declares `chart_scoped: true` +
  `chart_id` per §2.
- **Phase 5 (gateway)** — **MAJOR ADD**: (a) place the gateway in `lib/pipelines/shared/` so both
  isolated pipelines consume it (North-Star §5) — **not** an inline `consume/route.ts` branch;
  (b) `invoke_tool` calls `authorizeChartAccess(principal, chart_id, action)` **before** dispatch — the
  single per-chart authz point for web + MCP, alongside the B.11 forced-first guarantee. **Failure
  contract:** no grant/ownership → reject; `super_admin` → all charts; chart-independent tools skip the
  chart check. Depends on `authorizeChartAccess` existing (Track A1) and pipeline seams (Track A0).
- **Phase 6 (control-model B)** — unchanged in intent; note the agentic pipeline is one of the two
  isolated pipelines (North-Star §5), so the catalog-widening modifies *that module* via the shared
  gateway. Depends on pipeline isolation (A0) + gateway (Phase 5).
- **Phase 7 (rename batch)** — unchanged scope, **coordinate timing**: the `consume → consult` rename
  (North-Star A0) and the role `client → guest` migration (A1) both touch `route.ts` / DB; sequence the
  tool-rename batch with them to avoid double-churning the same files. (Tool renames ≠ role/route renames;
  keep them distinct but batched-adjacent.)
- **Phase 8 (tier excision)** — **REFRAMED + HARD-GATED**: access model after tiers = **role +
  chart_grants** (North-Star §3.4). **Hard dependency: Phase 8 must NOT land before Track A1
  (role rename + `owner_id` + `chart_grants` + `authorizeChartAccess`) is live** — else there is a window
  with no access control. The disclosure/redaction subsystem deletion is now **clean** (DATA_LAYER makes
  the data deterministic → nothing to redact). The residual tier-coupled controls are **re-cast as
  Command Center capability gates** (which tools on, per-key scopes, chart-grant policy — North-Star §8.2),
  not deleted. **Write/ops authz** (log_prediction/record_outcome/flag_disagreement/tool_health/
  data_coverage) moves from tier to role + `authorizeChartAccess` (open Q §6).
- **Phase 9 (data backfills)** — **SUBSUMED/RE-SEQUENCED into Track B2**: the empty CGM graph + L5
  timeline get populated *and `chart_id`-keyed* by the deterministic data rebuild, not by a standalone TP
  task. TP's role here is to confirm `tool_health`/`data_coverage` read true post-rebuild.
- **Phase 10 (native listChanged)** — unchanged (deferred enhancement).
- **Phase 11 (prompts + eval + re-baseline)** — **ADD**: eval becomes multi-chart aware (`chart_id` in
  the harness); `answer:eval` re-baselined per-chart. The deterministic data layer shifts what synthesis
  tools return (computed salience, no opinion prose) → baselines move; re-baseline after both the contract
  and the data cutover.

## §4 — Cross-plan dependency table (Tool Portfolio ↔ North-Star)

| TP phase | Depends on / coordinates with | Relationship |
|---|---|---|
| Phase 0 (hygiene) | — | Independent. Ship now. |
| Phase 1 (B.11 hotfix) | — | Independent. Ship now (parallel). |
| Phase 2 (contract + `chart_id`) | North-Star A1 (chart_id concept) | Adds `chart_id` to contract; lands once. Parallel-safe with A1. |
| Phase 3 (dual-channel + fallback removal) | **Track B / PLATFORM_REBUILD** (data plane `chart_id`-keyed) | Schema adds `chart_id` now; **fallback removal gated on keyed data plane.** |
| Phase 4 (wire ghosts) | Phase 3 | Sequenced after contract. |
| Phase 5 (gateway + authz) | **North-Star A0** (pipeline seams `lib/pipelines/shared/`) + **A1** (`authorizeChartAccess`) | Gateway lives in shared seam; authz fn must exist. Co-arc with A0/A1. |
| Phase 6 (control-model B) | A0 (agentic pipeline isolated) + Phase 5 | Sequenced. |
| Phase 7 (rename batch) | North-Star A0 (consult rename) + A1 (role rename) | Coordinate on `route.ts`/DB to avoid double churn. |
| Phase 8 (tier excision) | **North-Star A1 (HARD gate — authz live first)** + A2 (Command Center) + DATA_LAYER (redaction gone) | **Blocked until A1 live.** Residual controls → A2 capability gates. |
| Phase 9 (backfills) | **Track B2** (deterministic rebuild populates + keys CGM/timeline) | Subsumed; TP verifies post-rebuild. |
| Phase 10 (native listChanged) | Phase 5 | Deferred. |
| Phase 11 (eval/prompts) | Phases 4, 7 + DATA_LAYER cutover | Re-baseline after contract + data cutover; multi-chart aware. |

## §5 — Restated sequencing

**Immediate / parallel-safe (no North-Star dependency):** Phase 0 (hygiene), Phase 1 (B.11 hotfix).
**Contract arc:** Phase 2 → 3 → 4 (chart_id lands once; fallback removal waits on Track B keying).
**Gateway arc (co-arc with North-Star A0 + A1):** Phase 5 → 6. Gateway in `pipelines/shared/`; authz
chokepoint needs `authorizeChartAccess` (A1) and the pipeline seams (A0).
**Heavy/sequenced (own PRs, never concurrent):** Phase 7 (rename — coordinate with A0/A1 renames) →
Phase 8 (tier excision — **hard-gated on A1 live**).
**Data-coupled:** Phase 9 folded into Track B2; Phase 11 re-baseline after contract + data cutover.
**Deferred:** Phase 10.

Critical insight: **Phase 8 is the one hard cross-plan gate** — tier excision cannot precede the
multi-tenant authz going live, or access control vanishes in the gap. Everything else is parallel-safe or
softly coordinated.

## §6 — Open questions for the native (v1.3 §6 carried + new multi-tenant)

Carried from v1.3:
1. `answer:eval` existence + scoring (confirm `scripts/answer_eval.ts`).
2. `query_remedies_prescribed` vs `remedial_codex_query` relationship before any merge.
3. Wire-vs-retire for `list_assets` + `list_canonical_artifact_versions`.

New (multi-tenant):
4. **Write/ops authz model:** with tiers gone, who may call `log_prediction`/`record_outcome`/
   `flag_disagreement` (chart owner + super_admin, or super_admin only?) and `tool_health`/`data_coverage`
   (super_admin only, per the Cockpit model?). Replaces the old `flag_disagreement` super_admin tier gate.
5. **Hybrid tools:** confirm `vector_search` and `domain_report_query` as `chart_id`-optional, and the
   rule for scoping chart-derived rag_chunks vs general classical chunks after the data rebuild.
6. **API-key `default_chart_id`:** implement in Phase 5, or defer? (Convenience only; per-request
   `chart_id` + authz is the contract.)
7. **Pipeline isolation timing:** is North-Star A0 a *precondition* for Phase 5, or a *co-arc* (build the
   gateway into the seams as they're created)? (Recommend co-arc.)
8. **Phase 8 hard-gate confirmation:** accept that tier excision is blocked until Track A1 (authz) is live.

---

*End of TOOL_PORTFOLIO_PLAN v1.4 (DRAFT — multi-tenant aligned delta on v1.3). Grounded in the reality
report + North-Star + data-layer specs. No implementation performed. Each phase remains a CLAUDECODE_BRIEF
unit; v1.3 holds the unchanged phase bodies.*
