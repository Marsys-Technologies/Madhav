---
artifact: TOOL_PORTFOLIO_MULTITENANT_REPLAN_PROMPT_v1_0.md
purpose: Pasteable prompt for the planning session that revises TOOL_PORTFOLIO_PLAN to factor in the multi-tenant + North-Star architecture
status: prompt (planning-only; no implementation)
date: 2026-05-27
expose_to_chat: false
version: "1.0"
---

# Prompt — Re-plan the Tool Portfolio to factor in multi-tenancy + the North-Star architecture

Paste everything below the line into the Tool-Portfolio planning conversation.

---

You are continuing the **Tool Portfolio** planning work for MARSYS-JIS. This is a **planning-only**
session (no implementation; produce a revised plan + per-phase brief deltas). `TOOL_PORTFOLIO_PLAN_v1_3.md`
was written **before** the portal's move to multi-tenancy was decided, so it does not account for it.
Your job is to revise it into **v1.4** so that every phase factors in multi-tenancy and the unifying
architecture, without losing any of v1.3's verified groundwork.

## Read first (in order), then reconcile — do not re-derive facts already established
1. `00_ARCHITECTURE/TOOL_PORTFOLIO_PLAN_v1_3.md` — the current plan you are revising.
2. `00_ARCHITECTURE/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md` — v1.3's evidence base (authoritative).
3. `00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md` — the unifying multi-guest / multi-chart
   architecture, **especially §3 (identity/RBAC/sharing), §5 (two-pipeline isolation), §6 (MCP per-chart),
   §7.5 (Tool Portfolio convergence), §8 (Command Center).**
4. `00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE_v1_0.md` and `DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md` —
   the multi-chart data plane (`chart_id`) and the deterministic data rebuild.
5. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` + `00_ARCHITECTURE/manifest_overrides.yaml` — the metadata SoT.

## The multi-tenant facts the revision must honor
- **Two tenancy axes:** multi-**guest** (logins; role `super_admin` | `guest`) and multi-**chart**
  (subjects; canonical key `chart_id uuid`). `charts.client_id` is being split into `charts.owner_id`
  (the guest who created it) + subject birth-data; a new `chart_grants` table is the cross-guest ACL
  (view-only on shared charts).
- **One authorization brain:** `authorizeChartAccess(principal, chart_id, action)` governs web AND MCP.
  Access = **role** (portal surfaces) + **chart_grants** (which charts). There are **no tiers**.

## Required reconciliations — bake these into v1.4, do not leave them implicit
1. **`chart_id` joins the unified tool contract (Phase 2/3).** Make `chart_id` a first-class, **required**
   input in the shared Zod schema module, inherited by both channels. Remove the `?? NATIVE_CHART_ID`
   fallback once the data plane is keyed. Update the manifest `query_schema` backfill + the dual-channel
   generation (Phase 3) accordingly. State exactly which tools are chart-scoped vs chart-independent
   (ephemeris / classical T0 stay un-keyed).
2. **Gateway becomes the per-chart authorization chokepoint (Phase 5).** `invoke_tool` must call
   `authorizeChartAccess()` before dispatch — one enforcement point for both channels, co-located with
   the B.11 forced-first guarantee it already hosts. Specify the failure contract (no grant/ownership →
   reject; `super_admin` → all).
3. **Tier excision (Phase 8) is REFRAMED as overlap-removal and RE-SEQUENCED.** Confirm the access model
   after tiers = role + chart_grants only. Add a hard dependency: **Phase 8 must not land before the
   multi-tenant authz layer (North-Star Track A1: role rename + `owner_id` + `chart_grants` +
   `authorizeChartAccess`) is live**, or there is a window with no access control. Note that the
   deterministic data layer removes the disclosure/redaction rationale entirely (nothing left to redact).
4. **Coordinate the gateway/control-model-B with two-pipeline isolation (Phase 5/6 ↔ North-Star §5).**
   The agentic ("Claude-style") pipeline is one of the two pipelines being isolated; place the gateway in
   `lib/pipelines/shared/` so both isolated pipelines consume it, rather than adding another inline branch
   inside `consume/route.ts`. State whether pipeline isolation is a precondition or a co-arc.
5. **Command Center alignment (North-Star §8).** The tool contract, resident core, gateway flags, and
   tool-enablement become governable surfaces in the super-admin Command Center. Re-cast v1.3's
   tier-coupled controls as **capability gates** (which tools on, per-key scopes, chart-grant policy) —
   not tier redaction. Identify which Tool-Portfolio gates should be runtime-configurable.

## Deliverable
- A revised **TOOL_PORTFOLIO_PLAN_v1.4** (or a v1.3→v1.4 delta) that: (a) preserves every verified fact +
  locked decision from v1.3 except where multi-tenancy/tier-excision changes them, (b) adds `chart_id` +
  `authorizeChartAccess` into the relevant phases, (c) re-states the sequencing with the new
  cross-dependencies on North-Star Track A1 and the pipeline-isolation arc, (d) keeps each phase a
  standalone CLAUDECODE_BRIEF unit.
- A short **cross-plan dependency table** mapping Tool-Portfolio phases ↔ North-Star tracks/phases
  (which gates which, what is parallel-safe, what is sequenced).
- An **open-questions** list for the native (carry forward v1.3 §6 + any new multi-tenant ones).

## Discipline
- Planning only — no code. Output is a committed plan/brief, ready to hand to Claude Code for code-level
  validation (the established Cowork→Claude-Code→finalize loop).
- Cite the reality report + live code for any new claim; do not invent.
- Honor CLAUDE.md governance (versioning, no canonical duplication, mirror discipline where relevant).
