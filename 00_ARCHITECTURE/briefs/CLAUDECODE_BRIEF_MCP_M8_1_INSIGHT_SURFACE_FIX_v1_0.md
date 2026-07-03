---
canonical_id: CLAUDECODE_BRIEF_MCP_M8_1_INSIGHT_SURFACE_FIX
version: 1.0
status: READY-FOR-EXECUTION — fixes the 3 defects the live G9/G10 connector probe surfaced
created: 2026-07-01
author: Cowork (planning) — detail-pass after the live Claude-Code-connector witness
parent_charter: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (post-seal fix wave M8.1)
discovered_by: live connector probe 2026-07-01 (Claude Code → prod amjis-mcp, 45 tools) — G9/G10 not witnessed
verification_basis: live code read 2026-07-01 (all file:line below from the live tree)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4
hard_constraints:
  - build gate (platform-mcp + platform tsc exit 0); prod-verify after merge; VITEST not jest
  - retrieval stays FROZEN + chart-agnostic; entitlement unchanged; reverse-citation on any delete
acceptance_criteria: see §5
---

# CLAUDE CODE BRIEF — MCP M8.1: INSIGHT-SURFACE FIX (D-B / D-C / test-gap)

> The live connector probe proved the CHANNEL (connect, 45 tools, list_my_charts by name, entitlement gate,
> real ephemeris data) but G9/G10 were NOT witnessed: the insight tools return empty or 404. Root causes are now
> code-verified. This wave fixes the two MCP-side defects and writes the real integration tests. The THIRD gap
> (L2 MSR data empty) is NOT an MCP defect — it routes to the retrieval fork (§4 below).

## §1 — What the probe found (evidence)
- ✅ Channel works: `list_my_charts` → 4 charts by name; `query_planet_position` → real Swiss-Ephemeris data.
- ❌ `get_chart_orientation` / `get_signals` → `is_error:false` but EMPTY (`digest:{}`, 0 signals) on 2 charts.
  Tool provenance self-reports: `DEFECT-001 OPEN: bodha_msr_signals 0 rows / constituent_facts_array 91.5%
  orphan — expected until L2 rebuild`. → **D-A, retrieval-fork's, not this wave.**
- ❌ `get_positions` / `get_dashas` / `get_classical_citation` → 404 `Unknown capability URI`. → **D-B.**
- ❌ `holistic_bundle_chart_facts` → `Tool not in surgical whitelist: holistic_bundle`. → **D-C.**

## §2 — D-B: register L0 + L1 capabilities at runtime (SINGLE root cause; the bridge URIs are already correct)
**Verified:** the registry-bridge URIs are IDENTICAL to the registered URIs — NOT a typo/case/layer bug:
`registry_bridge.ts:347` sends `marsys://tool/L1/get_positions`, and
`registry/layers/L1_ganita/get_positions.ts:10` registers exactly `marsys://tool/L1/get_positions`. Same for
`get_dashas` (`:373` ↔ `L1_ganita/get_dashas.ts:10`) and `get_classical_citation`
(`:454` `marsys://tool/L0/query_classical_texts` ↔ `L0_brahmagyan/query_classical_texts.ts:9`).
**Root cause (type-d, not-registered-at-runtime):** the capability dispatcher
`platform/src/app/api/retrieval/capability/route.ts` `ensureBootstrapped()` (~:59-72) registers ONLY router +
maro + D6 + D7 + D8 + D5-fanout. `register_d5_fanout.ts:60-67` dynamically imports ONLY L2/L3/L4/L5 indexes.
**L0 and L1 indexes are never imported at runtime** — the only file that imports them (`registry/catalog.ts:34,41`)
has ZERO runtime importers. So L2 URIs resolve (worked, empty) and L0/L1 URIs 404.
**Fix (surgical):** in `ensureBootstrapped()` (or extend `register_d5_fanout.ts`), add runtime imports of
`./layers/L0_brahmagyan/index` and `./layers/L1_ganita/index`. Both self-register on import (L0 via
`registerL0Capabilities()` at its index.ts:68; L1 via top-level `registerCapability(...)` at its index.ts:27-45).
Two `await import(...)` lines is the minimal fix. Do NOT change the bridge URIs (they're correct); do NOT change
the frozen retrieval capabilities themselves — only ensure they LOAD.
**Verify:** `get_positions`, `get_dashas`, `get_classical_citation` return real data (not 404) via the connector
on an entitled chart; confirm no L2/L3/L4/L5 capability regressed (still registered).

## §3 — D-C: holistic_bundle rejected by the surgical whitelist (routing decision)
**Verified:** `holistic_bundle_chart_facts` (`platform-mcp/src/tools/retrieval/holistic_bundle.ts:70`) calls
`callPlatformPrimitive('holistic_bundle', …)` → POSTs `/api/mcp/primitives/holistic_bundle` → the route checks
`isAllowedSurgicalTool()` (`tool_name_bridge.ts:378-382`, = key in `MCP_TO_RETRIEVAL_TOOL` :328-371) →
`holistic_bundle` is NOT a key → 400 "not in surgical whitelist". The `grounding_status:SCAFFOLD,
b11_floor_passed:false` are stamped by the MCP-side error handler (`holistic_bundle.ts:83-86`) on any non-200.
**It's a gap, not an intentional gate.** `holistic_bundle` is a COMPOSITE/bundle tool, not one of the ~39
surgical primitives; it was repointed through `callPlatformPrimitive` on 2026-06-30 but never whitelisted.
**Fix — choose (b), the architecturally-clean one:** route `holistic_bundle_chart_facts` through the BUNDLE
endpoint `/api/mcp/bundles/[name]` (which exists — `platform/src/app/api/mcp/bundles/[name]/route.ts`) instead
of the surgical primitives endpoint, since it IS a bundle. Fallback (a) if (b) is more than a small change: add a
`holistic_bundle` entry to `MCP_TO_RETRIEVAL_TOOL` — ONLY valid if a real backing retrieval capability exists;
do not map it to a non-existent tool. Keep entitlement: the bundle endpoint must still call `authorizeChartAccess`.
**Verify:** `holistic_bundle_chart_facts` returns real chart_facts for an entitled chart; denies an unentitled one.

## §4 — D-A: L2 MSR data empty — ROUTE TO RETRIEVAL FORK (not this wave)
`bodha_msr_signals` = 0 rows; `constituent_facts_array` 91.5% orphan (DEFECT-001 / ISSUE-4 — the documented
MSR-vs-L1-epoch drift). This is why `get_chart_orientation`/`get_signals`/`get_domain_reading` return empty and
why "superlative insight" (G10) can't yet be witnessed. **The MCP channel is behaving correctly — it faithfully
returns what the data layer has (nothing).** File/confirm the REQUEST to the retrieval / L2 Bodha fork: rebuild
MSR against the current L1 epoch so signals populate and constituent_facts resolve. **G10 is GATED on this; it is
NOT an MCP fix.** This brief does not touch L2 data.

## §5 — Test-gap: write the real G-series integration tests (un-skip is not enough — they're empty stubs)
**Verified:** `platform-mcp/src/__tests__/m8_e2e_proof.test.ts:615` `describe.skip('INTEGRATION — G1/G3/G6/G9/G10…')`
contains 7 EMPTY-STUB `@integration` its (G1:616, G3:621, G6:626, G9:631, G10:636, V2:641, V3:646) — bodies say
"Proven manually". Un-skipping alone proves nothing. **Write real assertions** driven by env (`MCP_BASE_URL` +
`MCP_API_KEY_CLIENT`, mirroring `integration/mcp_visibility.integration.test.ts:9`), gated to run against live
prod (skipIf env absent), so CI stays green but the suite is real when pointed at prod:
- G3: `list_my_charts` → names present, no raw-UUID-only. (Can assert NOW — data-independent.)
- G9: `get_positions` (post-§2) → real data via registry path, not 404. (Can assert once §2 lands.)
- G1/G6: connector-dependent — write the assertion; may stay env-gated until a connector token is wired.
- **G10: assert `get_domain_reading`/`get_signals` return NON-empty grounded signals with resolving
  constituent_facts.** This test will legitimately FAIL until D-A (retrieval MSR rebuild) lands — that's correct:
  it becomes the living proof-of-fix for G10. Mark it `skipIf(!process.env.RUN_G10)` with a comment that it gates
  on the MSR rebuild, so it doesn't red CI but is ready to witness the moment data lands.

## §6 — Acceptance criteria
- **Build gate:** `platform-mcp` + `platform` both `npm run build` exit 0; `typecheck-mcp` CI green.
- **D-B:** L0 + L1 capabilities register at runtime; `get_positions`/`get_dashas`/`get_classical_citation`
  return real data (not 404) via the live connector on an entitled chart; no L2–L5 capability regressed.
- **D-C:** `holistic_bundle_chart_facts` returns real chart_facts for an entitled chart and denies an unentitled
  one (entitlement preserved through whichever route chosen).
- **D-A:** REQUEST filed to the retrieval fork (MSR rebuild); NOT fixed here; G10 explicitly documented as gated on it.
- **Tests:** real G3 + G9 integration assertions pass against prod; G10 test written + env-gated as the
  proof-of-fix-once-data-lands; CI stays green.
- **Deploy + prove:** merged, deployed, revision SHA == merged SHA; re-run the live connector probe — G9 tools
  now return data; G10 still-empty-but-for-the-known-D-A-reason (documented).
- Retrieval FROZEN; chart-agnostic gate green; entitlement unchanged; reverse-citation on any delete; Vitest.

*End of CLAUDECODE_BRIEF_MCP_M8_1_INSIGHT_SURFACE_FIX v1.0. After this + the retrieval-fork MSR rebuild (D-A),
re-run the connector G9/G10 witness — that is the true seal of the goal.*
