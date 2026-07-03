---
canonical_id: CLAUDECODE_BRIEF_MCP_M0_5_INFRA_UNBLOCK
version: 1.0
status: READY-FOR-EXECUTION — fixes the 3 pre-existing infra gaps the M0 proof surfaced
created: 2026-06-30
author: Cowork (planning) — detail-pass for the autonomous swarm (inserted between M0 and M1)
parent_charter: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (PHASE M0.5 — new)
depends_on: M0 (proven)
discovered_by: M0 isolation-matrix verification (2026-06-30) — F1/F2/F3
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4
verification_basis: M0 prod verification report + live code
hard_constraints:
  - these are NOT M0 regressions — they are pre-existing; fix without touching M0's gate logic
  - reverse-citation before any delete; prod-verify after merge; VITEST
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — MCP M0.5: INFRA UNBLOCK (F1/F2/F3)

> The M0 security proof passed — but it surfaced three pre-existing infra gaps that mean an authenticated LLM
> currently gets AUTH-OK-then-no-DATA on most tools. M0 proved the gate; M0.5 makes data actually flow.
> **F1 + F2 are GOAL-BLOCKING** (without them, "the LLM accesses the retrieval system and gets data" fails at
> M8). F3 is hygiene. None touches M0's entitlement logic.

## §1 — F1 (BLOCKING): registry_bridge's 14 tools 401 in prod — TWO-PART FIX (order matters)
**Symptom:** all registry-bridge MCP tools (`get_chart_orientation`, `get_domain_reading`, `list_assets`,
`get_signals`, `traverse_graph`, `get_positions`, `get_dashas`, `get_temporal_windows`, `get_projections`,
`get_remedies`, `get_chart_quality`, `get_classical_citation`, etc.) return 401 in prod.
**Root cause:** `/api/retrieval/capability` is NOT in the `isPublic` allowlist in `platform/src/proxy.ts:36-45`,
so the middleware rejects the service-to-service call (no session cookie) before the route runs.
**⚠️ VERIFIED DANGER — do NOT just allowlist it.** `platform/src/app/api/retrieval/capability/route.ts` has
**NO auth of its own** (the POST handler validates only the JSON body + `uri`, then dispatches straight to
`getCapability(uri).handler(args)` — no internal-token check, no key gate). It relies ENTIRELY on the proxy
session gate today. Blanket-adding `/api/retrieval/` to `isPublic` would expose the entire retrieval layer
UNAUTHENTICATED to the internet. **This is a NEW auth bypass if done naively.**
**Fix (two parts, IN ORDER):**
1. FIRST add an internal-token check at the top of `capability/route.ts` (mirror the `X-MCP-Internal-Token`
   pattern already used in `resources/chart_snapshot.ts:36` — `fetchPrimitive` sends that header). The route
   must reject any call lacking the valid internal token.
2. THEN add `pathname.startsWith('/api/retrieval/')` to the `isPublic` set in `proxy.ts` — now safe, because
   the route self-authenticates.
**Verify:** a registry-bridge tool returns 200 with a valid MCP key + internal token in prod; AND an
unauthenticated/no-internal-token call to `/api/retrieval/capability` returns 401/403 (not data). Both must hold.

## §2 — F2 (BLOCKING): Python sidecar unreachable from MCP Cloud Run
**Symptom:** `holistic_bundle`, `phala_event_anchors`, `phala_outlook`, `kala_temporal_bundle`, `mimamsa_*` (the
sidecar-backed tools) pass auth then fail the data fetch to `${PYTHON_SIDECAR_URL}/api/compute/…`. L0
Brahmagyan, L1 PyJHora, L0 Ephemeris (non-sidecar) are unaffected.
**Root cause (investigate — one of):** (a) `PYTHON_SIDECAR_URL` not set / wrong on the `amjis-mcp` Cloud Run
service env; (b) the sidecar (`amjis-sidecar`) not deployed or scaled to zero; (c) network/IAM: amjis-mcp's
runtime SA can't invoke the sidecar (if sidecar is IAM-gated, amjis-mcp needs `roles/run.invoker` on it).
**Fix:** diagnose which, then: set/correct `PYTHON_SIDECAR_URL` (deploy.yml already sets
`PYTHON_SIDECAR_URL=https://amjis-sidecar-938361928218.asia-south1.run.app` for the sidecar job — confirm
amjis-mcp gets it too), confirm the sidecar is deployed + reachable, grant invoker if IAM-gated. Verify:
`holistic_bundle` returns real data for an entitled chart in prod.
**NOTE the §4 seam:** the long-term direction is that sidecar-backed tools migrate to the registry path
(keystone, M6/M7) — but F2 is the near-term unblock so they work NOW; don't conflate.

## §2.5 — Native-contamination cleanup (same class as the gate work; fold in)
**(a) `ephemeris_cache_native_lifetime` — STILL OPEN (verified `l0_ephemeris.ts:241-276`).** Empty input schema
(`z.object({})`, takes no chart_id), description hardcodes "the native's lifetime window (1984-2070)", hits
`/brahmagyan/ephemeris/native_lifetime_meta`. Registered via `registerEphemerisTools` (`server.ts:125` →
`l0_ephemeris.ts:275`). **Fix:** retire it (drop `registerEphemerisCacheNativeLifetimeTool` from the convenience
fn) OR reparametrize to a generic date-window tool using the sibling `ephemeris_cache_year` (`:214`) as the
clean date-parametrized pattern. Reverse-citation gate before removal. Verify: no tool leaks the native window;
chart-agnostic CI gate green.
**(b) `chart-snapshot` leak — ALREADY FIXED by M0 (verified `chart_snapshot.ts:288-306`).** Now
`marsys://chart-snapshot/{chart_id}`, requires chart_id from URI, calls `remoteAuthorize(principal, chartId)`
before any fetch, threads chartId into every primitive — no default/native resolution. **M0.5 action = VERIFY
ONLY** (confirm on prod it denies an unentitled chart). Residual cosmetic (optional): `chart_snapshot.ts:39`
still hardcodes `'X-MCP-Audience-Tier':'super_admin'` (contradicts no-tier doctrine; harmless to isolation) and
`:224` references the deleted FORENSIC_v8_0 file — clean up if trivial.

## §2.6 — CI merge gate: make platform-mcp non-compiling un-mergeable (the M0-broken root cause)
**Verified:** `.github/workflows/ci.yml` ("CI — Ganga Quality Gate", runs on PR to main) typechecks ONLY
`platform/` (`working-directory: platform`, `npx tsc --noEmit --skipLibCheck`). It NEVER builds/typechecks
`platform-mcp` — that only happens post-merge inside the Docker build in `deploy.yml`'s `deploy-mcp` job. AND
`deploy.yml` gates on this same workflow (`workflow_run: ["CI — Ganga Quality Gate"]`, success). So a broken
platform-mcp passes CI, merges, and only breaks at deploy — exactly what happened to M0.
**Fix:** add a PR-triggered job to `ci.yml` with `working-directory: platform-mcp` running `npm ci` +
`npx tsc --noEmit` (or `npm run build`). Now a non-compiling MCP package fails the PR check before merge, and
(because deploy keys off this workflow) protects deploys too. **Verify:** intentionally-broken MCP TS fails the
new CI job on a throwaway PR (then revert).

## §3 — F3 (hygiene): dead provisioning artifacts
- `mcp-native-claude-chat-key` exists in Secret Manager (`mcp_prod_9WTqQGKJ…`) but `key_id=mcp_prod_9WTqQGKJ`
  is absent from `mcp_api_keys` → dead (401 if any client uses it). Either provision it properly via
  `POST /api/mcp/keys` (bind to the intended user) or remove the stale secret. Decide + act.
- (Already done in M0 verification: the legacy UUID `brahma-smoke` key was deleted.)
- Update stale docs: `amjis-mcp` is `allUsers:roles/run.invoker` (publicly invokable; app-level Bearer is the
  gate) — the `--no-allow-unauthenticated` note in older briefs/D0 is outdated; document the intentional posture.

## §4 — Acceptance criteria
- **F1:** registry-bridge tools return 200 (not 401) with a valid MCP key + internal token in prod; AND an
  unauthenticated / no-internal-token call to `/api/retrieval/capability` returns 401/403 (route self-auth
  added BEFORE allowlisting — no new bypass). Both proven on prod.
- **F2:** at least one sidecar-backed tool (`holistic_bundle`) returns real data for an entitled chart in prod;
  root cause (env / deploy / IAM) documented + fixed.
- **F3:** the dead native-chat-key is provisioned-or-removed; the `--no-allow-unauthenticated` posture doc updated.
- **§2.5(a):** `ephemeris_cache_native_lifetime` retired or reparametrized — no tool leaks the native window;
  reverse-citation report present for any removal.
- **§2.5(b):** `chart-snapshot` confirmed (verify-only) to deny an unentitled chart on prod.
- **§2.6:** `ci.yml` now typechecks `platform-mcp` on PR; a broken MCP TS fails the PR check (proven on a
  throwaway PR, then reverted). The M0-merged-broken class can no longer reach main.
- No change to M0's entitlement logic; reverse-citation on any delete; every claim prod-verified; Vitest;
  retrieval FROZEN; chart-agnostic gate green.

*End of CLAUDECODE_BRIEF_MCP_M0_5_INFRA_UNBLOCK v1.0. These gate the M8 live-prove; fix before relying on
data-returning tools. Then M1→M8.*
