---
canonical_id: CLAUDECODE_BRIEF_MCP_LATENCY
version: 1.0
status: READY-FOR-EXECUTION — diagnose + fix MCP query latency (much slower than the legacy MCP)
created: 2026-07-02
author: Cowork (live latency probe over the MCP connector) — for execution by Claude Code
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4 (do NOT reintroduce direct-SQL to "go fast" —
  that breaks the single-source seam the whole campaign bought; fix latency WITHIN the registry architecture)
verification_basis: live MCP connector probes 2026-07-02
hard_constraints:
  - keep the single-source registry path (no per-tool direct pg.Pool); build gate; both-services SHA; VITEST
  - measure latency BEFORE and AFTER each fix (p50/p95 wall-clock) — this brief is judged on numbers, not code presence
acceptance_criteria: see §5
---

# CLAUDE CODE BRIEF — MCP QUERY LATENCY (modernized MCP is much slower than legacy)

> The native reports MCP queries are markedly slower than the legacy MCP. Live probes show the SERVER-SIDE
> compute is trivial (latency_ms 5–14), so the slowness is NOT the query — it's the caching + hop + cold-start
> overhead the modernization added. Fix WITHIN the registry architecture (do not revert to direct SQL).

## §1 — Live evidence (from the connector, 2026-07-02)
- **Caching is INEFFECTIVE (the smoking gun):** called resolve_entity("Shani") twice — identical args, identical
  `result_hash` (sha256:781bfbbe…) — and BOTH returned `served_from_cache: false`. An exact-repeat query
  re-executes the full path every time. The cache exists in the envelope contract but is not hitting.
- **Server compute is trivial:** `latency_ms` 5 then 14 for the same tool. The query itself is fast; the
  wall-clock the user feels is dominated by everything AROUND the query.
- **Architecture changed (legacy → modernized):**
  - LEGACY (fast): MCP tool → its own pg.Pool → DB. ONE hop, direct, warm pool.
  - MODERNIZED (slower): MCP Cloud Run → HTTP → platform Cloud Run `/api/mcp/primitives/[tool]` →
    `ensureBootstrapped()` (registry init) → getToolByName → tool.retrieve → HTTP → sidecar OR DB. Plus the M0
    entitlement gate (profiles role lookup + authorizeChartAccess: charts + chart_grants queries) on every
    chart-scoped call. MULTIPLE hops + bootstrap + gate + ineffective cache.
  The single-source registry (which we WANTED for correctness) inherently added the MCP→platform hop; legacy was
  fast precisely because of the direct-SQL anti-pattern we removed. So this is a correctness-vs-latency tradeoff
  to be paid down WITHOUT undoing the seam.

## §2 — Investigate (confirm the contributors; measure each)
Before fixing, instrument + measure so each fix is proven. For a representative set (resolve_entity — cheap;
get_signals — heavy; get_dashas — registry; a sidecar tool like phala_outlook), capture wall-clock p50/p95 and
break it into: MCP-server time, MCP→platform network, ensureBootstrapped time, gate time, tool.retrieve time,
platform→sidecar/DB time, serialization time. Confirm which dominate. Likely order (from evidence): cold start >
no-cache re-execution > extra hop > bootstrap-per-request > gate lookups > serialization.

## §3 — The fixes (highest-leverage first; keep the registry seam)
1. **FIX THE CACHE (highest leverage — proven broken).** served_from_cache is always false on exact repeats.
   Find the cache layer (the envelope has served_from_cache + result_hash — the machinery exists). Root-cause
   why it never hits: wrong cache key (is it keyed on something request-unique like trace_id?), not written on
   miss, TTL=0, per-instance memory cache lost across Cloud Run instances, or disabled. Make identical
   (tool + params + chart + ayanamsha) queries hit cache. Consider a shared cache (Redis/Memorystore or the DB)
   so it survives across instances + restarts, not per-process memory. **Prove: 2nd identical call →
   served_from_cache:true + materially lower wall-clock.**
2. **KILL COLD STARTS.** Confirm amjis-mcp AND amjis-web min-instances. The charter shows conflicting values
   (min-1 vs min-0). If either is 0, every post-idle query pays a container boot — and the W2.5 catalog-import
   made the platform bootstrap HEAVIER (it now imports ALL L0–L5 registration files at module load). Set
   min-instances ≥1 on both services (cost-bounded). **Prove: first-call-after-idle latency drops to warm levels.**
3. **MEMOIZE ensureBootstrapped().** If registry init runs per-request (not once-per-process), every
   /api/mcp/primitives call re-registers router+maro+D6+D7+D8+D5+L0/L1. Confirm it's memoized to run exactly
   once per process; if not, cache it. **Prove: bootstrap time ~0 on all calls after the first.**
4. **CONNECTION KEEP-ALIVE / POOLING across the hop chain.** Ensure MCP→platform and platform→sidecar reuse
   HTTP keep-alive connections (agent with keepAlive) rather than a fresh TCP+TLS handshake per call; ensure the
   platform→DB pool is warm + sized. **Prove: per-call network overhead drops.**
5. **ENTITLEMENT GATE — cache the principal resolution.** The gate does profiles-role + owner/grant lookups per
   call. Cache principal role + entitlement per (uid, chart) for the request/session lifetime so repeated calls
   in a session don't re-query. (Keep the gate — just don't re-pay it every call.) **Prove: gate time drops on
   repeat calls.**
6. **PAYLOAD SIZE (already partly done).** Large payloads (get_domain_reading, get_signals, get_projections)
   cost serialize + transfer time; the W3R bounding helps. Ensure default response_format is token/byte-bounded
   everywhere (ties to G-I). **Prove: heavy-tool wall-clock drops with bounded defaults.**

## §4 — Do NOT
- Do NOT reintroduce per-tool direct pg.Pool / bypass the registry to "go fast" — that re-breaks the
  single-source seam (the entire retrieval campaign's core invariant). Latency is paid down via cache + warm
  instances + keep-alive + memoized bootstrap, NOT by undoing the architecture.

## §5 — Acceptance criteria (numbers, not code presence)
- Baseline captured (p50/p95 wall-clock per representative tool, with the per-segment breakdown).
- Cache hits on identical repeats (served_from_cache:true) + measurable wall-clock drop.
- No cold-start penalty (min-instances ≥1 both services); bootstrap memoized (once/process).
- Keep-alive/pooling across MCP→platform→sidecar/DB; gate resolution cached per session.
- AFTER numbers show a materially lower p50/p95 vs baseline (target: approach legacy-era latency; report the
  actual before/after). Registry seam intact (no direct-SQL reintroduced); both services on merged SHA; Vitest.

*End of CLAUDECODE_BRIEF_MCP_LATENCY v1.0 — the modernization added correctness (single source) at a latency
cost; pay it down with caching + warm instances + keep-alive, not by undoing the seam.*
