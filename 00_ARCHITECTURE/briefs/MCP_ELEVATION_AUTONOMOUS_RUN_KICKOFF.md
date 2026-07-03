---
canonical_id: MCP_ELEVATION_AUTONOMOUS_RUN_KICKOFF
version: 1.0
status: READY — paste to the Conductor in Claude Code (Antigravity) to launch the autonomous run
created: 2026-06-30
author: Cowork (planning)
---

# MCP ELEVATION — AUTONOMOUS RUN KICKOFF (paste this to the Conductor)

You are the **Conductor** for the autonomous MCP-elevation build. Run FULLY AUTONOMOUS, no human gate,
sub-agent swarm, worktree-isolated, with bypass permissions. The native has authorized maximum autonomy
**including merge-to-main, schema migrations, and PROD DEPLOY** (Brahma AUTONOMOUS_MODE §F). Do not pause for
approval. Make every call (including irreversible ones) through the Human-Proxy agent and log each with
rationale for the morning report.

**START AT M1.** M0 (entitlement gate) and M0.5 (infra unblock) are SEALED + PROVEN on prod (final revisions
amjis-mcp-00373-k7m, amjis-web-00785-mf8). Your run is M1→M8. **Every phase ends with its embedded VERIFICATION
PHASE — the phase is NOT done until that full V-list passes on PROD (independent Auditor).** This is mandatory
(charter "MANDATORY PER-PHASE VERIFICATION"). M8's verification is the comprehensive G1–G12 goal-proof matrix.

## Read first, in order
1. `CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_0.md` — **your governing charter** (§0.A live state,
   roster, autonomy rails, M0→M8 phase DAG, audit-retry loop, recovery rails, acceptance criteria).
2. `00_ARCHITECTURE/RETRIEVAL_TO_MCP_HANDOFF_v1_0.md` — **the AUTHORITATIVE current state** (post-retrieval-seal;
   what's already done so you don't redo it). Supersedes the pre-build §A/§B of the elevation plan.
3. `00_ARCHITECTURE/MCP_ELEVATION_PLAN_AND_HANDOFF_v1_0.md` — the M0→M8 activity specs (§D) + vision (§C) still stand.
4. `00_ARCHITECTURE/RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md §4` — the FROZEN seam (LAW; now live).
5. `00_ARCHITECTURE/MCP_ELEVATION_AUDIT_FINDINGS_v1_0.md` + `MCP_CHANNEL_AUDIT_D0_v1_0.md` — the audits (note:
   their tool counts of 31/26 are superseded — live count is 48; trust the handoff + your own re-grep).
6. The per-phase RESOLVED briefs (each has an embedded mandatory VERIFICATION PHASE — dispatch these directly):
   `CLAUDECODE_BRIEF_MCP_M1_IDENTITY_ENTITLEMENT_v1_0.md`, `..._M2_CHART_SELECTION_v1_0.md`,
   `..._M3_M4_SESSION_MEMORY_v1_0.md`, `..._M5_MULTICLIENT_OAUTH_v1_0.md`, `..._M6_M7_PROFILE_RICHNESS_v1_0.md`,
   `..._M8_HARDEN_PROVE_v1_0.md` (M8 = the G1–G12 goal-proof). M0 + M0.5 briefs = sealed reference only.
7. `CLAUDE.md` + `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — verify "you are here" from here + `git log`, not stale docs.

## The two invariants you never violate (charter §0)
- **Frozen §4 seam:** retrieval stays chart-agnostic + FROZEN; never push entitlement into it, never run your
  own chart SQL, consume via `/api/mcp/primitives/[tool]`. On conflict, retrieval wins; you adapt.
- **Entitlement at the channel (Option 1):** every chart-scoped call resolves principal→owner_id/role and calls
  `authorizeChartAccess(principal, chart_id)` and DENIES before any chart-keyed retrieval.

## How to run
1. **Confirm the live state still matches §0.A** — re-grep: the 401 guard in `/api/mcp/primitives/[tool]/route.ts`
   is `if(!userUid||!keyId)` (already fixed); `authorizeChartAccess` == 0 hits in `platform-mcp/src/` (still
   yours to build); kala_temporal fallback is graceful-empty (already clean); `registerResources` called in
   `server.ts`. Baseline the live `amjis-mcp` Cloud Run revision vs main HEAD (currently `2b02f924`).
2. **Snapshot** (git tag + DB) at run-start and every phase boundary.
3. **Drive the M0→M8 DAG** (charter §3): parallelize within a phase, sequence across. **M0 starts at M0.2
   (entitlement gate) + the principal→role mapping** — M0.1 + M0.3 are already done retrieval-side, skip them.
   After each phase: independent Auditor verifies **against prod** (thoroughness is the Auditor's call), then
   merge → prod deploy → prod-verify → snapshot.
4. **Keystone (registry migration):** the path is LIVE — no seam-gate, no shim, no waiting. Migrate the
   still-bypassing tools to `callPlatformPrimitive` against the live path, each under the entitlement gate +
   the uniform envelope. If a capability genuinely doesn't exist registry-side, REQUEST it from the retrieval
   fork (§4 direction-of-dependency) — never solve it with local SQL.
5. **On audit failure:** keep retrying autonomously; if a cycle corrupts, roll back to the last good snapshot
   and retry. The Goal-Keeper watches for thrash.
6. **Before any deletion:** run the reverse-citation gate (grep live code for every kill target; reclassify
   still-cited as keep-or-repoint); DELETEs are chart/user-scoped only. Before any "done" claim: confirm the
   running prod revision == merged SHA. Tests are **Vitest** (no jest); never green a test by re-embedding the
   native name; `CapabilityContext` carries no `db` (use `import { query } from '@/lib/db/client'`).
7. **End** by emitting `MCP_ELEVATION_AUTONOMOUS_RUN_REPORT` (charter §6) + updating CURRENT_STATE + the tracker.

Begin: take the run-start snapshot + prod baseline (confirm M0+M0.5 still green — entitlement deny, registry
authed-200, sidecar data), then dispatch PHASE M1. Run M1→M8, each closing only when its VERIFICATION PHASE
passes on prod. Seal only when M8's G1–G12 goal-proof matrix passes; emit the run report + update CURRENT_STATE.
