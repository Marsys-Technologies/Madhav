---
canonical_id: CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4
version: 1.0
status: READY-FOR-EXECUTION — autonomous swarm campaign for audit fix Waves 1–4 (Wave 5 excluded)
created: 2026-07-01
author: Cowork (from the 360° MCP audit) — for autonomous execution by the Claude Code swarm in Antigravity
mode: FULLY AUTONOMOUS · bypass permissions · sub-agent swarm · worktree-isolated · no human gate
parent: MCP_SYSTEM_AUDIT_FIX_PLAN_v1_0 (Waves 1–4) · evidence MCP_SYSTEM_AUDIT_FINDINGS_v1_0
pattern_inherited_from: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (the validated M1–M8 pattern)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4 (retrieval FROZEN; MCP adapts)
native_rulings (2026-07-01):
  - Batch Waves 1–4 autonomously; Wave 5 (salience+synthesis) EXCLUDED — design-gated, done with the native.
  - MANDATORY per-wave verification BY THE SWARM (build+deploy+prod-prove) before any wave is marked done.
  - Full autonomy incl. merge + prod deploy + schema migrations (Brahma AUTONOMOUS_MODE §F); human-proxy makes
    all calls; native reviews the morning report.
scope_guard: this campaign does read-path/serving/wiring/schema/infra fixes ONLY. It MUST NOT attempt the
  salience re-model or synthesis step (Wave 5) — if a builder drifts toward changing how signals are RANKED or
  adding verdict-synthesis, the Goal-Keeper halts it. Those are native-design-gated.
---

# AUTONOMOUS SWARM CAMPAIGN — AUDIT FIX WAVES 1–4

> Fixes the deterministic findings from the 360° audit (the ones with a known-correct answer + an objective
> pass/fail). Wave 5 (the astrological salience+synthesis judgment work) is deliberately EXCLUDED — it's
> designed with the native separately. This campaign gets the system to "connects, accesses, retrieves cleanly
> and efficiently"; Wave 5 gets it to "superlative."

## §0 — The two invariants (every agent, always)
1. **Frozen §4 seam:** retrieval chart-agnostic + FROZEN; entitlement stays at the channel; consume the registry,
   don't re-implement it or run MCP-side chart SQL. On conflict retrieval wins.
2. **Read-path/serving fixes only:** do NOT rebuild stored data, do NOT change sealed signal counts, do NOT
   change how signals are RANKED (that's Wave 5). Confirm stored counts UNCHANGED after each wave (scorecard
   still 64,765) — we change serving/wiring/schema, not the data or the ranking.

## §1 — Swarm roster (inherited from the M1–M8 charter)
Conductor · Human-Proxy (expert, all irreversible calls) · Goal-Keeper (halts scope drift — esp. any drift
into Wave 5 ranking/synthesis) · independent Auditor (per-wave, prod-verified) · Builder agents (one per wave,
own worktree/branch).

## §2 — Autonomy rails
MAY autonomously: write/refactor + tests, worktrees/branches, builds/tests, read+mutating DB, schema migrations,
retire/repoint legacy under reverse-citation, merge to main, deploy to prod.
MUST auto (recovery rails, not pauses): snapshot at run-start + each wave boundary; reverse-citation before any
delete; chart-agnostic + contamination check each wave; prod-verify each wave.
MUST NOT: destroy prod DATA without snapshot+citation; push entitlement into retrieval; touch the salience/
synthesis model (Wave 5).

## §3 — The wave DAG (parallelize where independent; each ends in mandatory verification)

```
SNAPSHOT(run-start) + prod-revision baseline

WAVE 1 ✅ DONE + PROD-VERIFIED (2026-07-01): AYANAMSHA UNBLOCK — ayanamsha default/alias fixed; insight
  surface serves on default. (F-006/F-011/F-031 closed.)

WAVE 2 ✅ DONE + PROD-VERIFIED (2026-07-01, PRs #372/#377/#378/#379/#380, revision amjis-web-00796-9nb):
  SERVING WIRING. Root cause = catalog import (capabilities not registered at module load) + migration 365
  blocker (VIEW→TABLE guard) + mitigation_map whitelist. list_assets/resolve_entity/query_signals/
  mitigation_map/query_dasha_periods/lel_query all confirmed live. (F-001/002/003/004/015/016/018 closed.)

WAVE 2.5 (NEW — folded in; the INCOMPLETE part of the Wave 2 catalog fix): REASONING-UNIT REGISTRATION + TIER LEAK
  - **F-032 [CRIT — gates G10]:** PR #380 imported L1–L5 layer indexes into `catalog.ts` but NOT
    `register_d7_channel.ts` NOR `register_d8_assess_domain.ts`. d8 holds the APEX reasoning-unit tools
    (`assess_marriage`/`career`/`health`/`wealth` + `yoga_activation_by_dasha`); d7 holds channel caps. So
    query_chart_facts / vector_search / get_cgm_subgraph + the assess_* tools still 404 (Unknown capability URI).
    **Fix:** add the d7 + d8 registration imports to `catalog.ts` (same mechanism as the L1–L5 imports PR #380
    added — self-register on import). Confirm no double-registration with anything already loaded by the D5/D8
    bootstrap path (`register_d5_fanout` / `ensureBootstrapped`) — dedupe if needed.
  - **F-033 [MED]:** the served MCP envelope leaks `"audience_tier":"client"` (seen in resolve_entity) —
    violates the no-audience-tier doctrine. Strip `audience_tier` from the response envelope on this path.
  → VERIFY → MERGE → DEPLOY → prod-prove → SNAPSHOT. **This is the last serving-fix gating the G10 witness.**

WAVE 3 (parallel-capable): OUTPUT BOUNDING
  - Make response_format actually branch (digest=counts / summary=top-k / full) — currently inert (F-026).
  - Bound + paginate big synthesis tools: get_domain_reading must not return 17 MB (F-021); dedup signal_id_refs
    (F-023); bound get_projections (F-008). Default to a token-safe cap (~25k), paginate the rest.
  - Standardize the error envelope across all tools (F-028).
  NOTE: this is PAYLOAD SHAPING/SIZE only — NOT changing which signals rank top (that's Wave 5). Bounding =
  "return fewer/paged rows + real verbosity levels," not "re-rank."
  → VERIFY → MERGE → DEPLOY → prod-prove → SNAPSHOT.

WAVE 4 (parallel-capable): L4 PHALA + SIDECAR REPAIR
  - L4 schema drift: missing columns id/anchor_id; phala_get_rectification PL/pgSQL candidate_time field;
    missing panchanga_daily relation (F-005, F-014). - Re-provision corrupted ephe file sepl_18.se1 + sidecar
    image integrity pass (F-012, F-030). - Root-cause L5 mimamsa 500s (F-013).
  → VERIFY → MERGE → DEPLOY → prod-prove → SNAPSHOT.

FINAL: campaign re-audit sweep (re-run the retrievability matrix) + morning report.
```
Waves 2/3/4 are largely independent of each other and MAY run in parallel after Wave 1 lands (they touch
different surfaces: registration/whitelist vs response-shaping vs L4/infra). The Conductor parallelizes where
the Goal-Keeper confirms no file overlap.

## §4 — MANDATORY PER-WAVE VERIFICATION (native-ruled; the swarm proves each wave itself)
No wave is done until its Auditor passes ALL of, on PROD:
- **Build gate:** `cd platform-mcp && npm run build` AND `cd platform && npm run build` exit 0; typecheck-mcp CI green.
- **Deploy + revision match (BOTH services — the migration-desync lesson):** deployed amjis-mcp AND amjis-web
  revision image SHAs == merged SHA. A wave is NOT done if only one service rolled — a FAILED migration silently
  froze amjis-web 3 merges behind amjis-mcp in Wave 2 while "MCP deployed ✅" read true. ALWAYS check both
  services' live revisions; if the Web deploy's "Run database migrations" step failed, the wave is BLOCKED
  regardless of MCP status. Report both SHAs.
- **Behavioral prod-prove (the wave's specific acceptance):**
  - W1: a DEFAULT (no-ayanamsha) get_signals/get_chart_orientation returns >0 signals on ≥2 charts; all
    ayanamsha spellings resolve to the same non-empty result; stored counts unchanged (64,765).
  - W2 ✅ (done): previously-❌ tools now return structured responses; list_assets returns the full 85-asset
    catalog; resolve_entity/mitigation_map/query_signals live.
  - W2.5: the reasoning-unit tools (assess_marriage/career/health/wealth, yoga_activation_by_dasha) +
    query_chart_facts/vector_search/get_cgm_subgraph return a structured response (NOT 404 "Unknown capability
    URI") — d7+d8 registered. AND no tool's envelope contains `audience_tier`. **This is the G10-gating check.**
  - W3: no tool returns >~25k-token default payload; response_format demonstrably changes size; get_domain_reading
    is bounded + no longer 17 MB; uniform error envelope.
  - W4: phala_outlook/event_anchors/query_special_lagnas/query_calibration return data (not 500/schema-error) on prod.
- **Invariants:** retrieval FROZEN (git diff lib/retrieval minimal + only serving-normalization if any);
  chart-agnostic gate green; reverse-citation report for any delete; stored data/counts unchanged; NO Wave-5
  ranking/synthesis change crept in (Goal-Keeper signs off).
- **Verification tooling:** provision a test MCP key via POST /api/mcp/keys (the code path, not SQL) for the
  behavioral prod-proves; use a guest key for any deny-check.
On ANY verification failure: keep-retrying autonomously; roll back to last good snapshot if a cycle corrupts;
Goal-Keeper watches for thrash. Every retry + irreversible call logged.

## §5 — Morning report
Emit `MCP_AUDIT_FIX_W1_W4_RUN_REPORT`: per-wave outcome + the prod-prove evidence (the retrievability matrix
before→after: how many tools ❌→✅), every irreversible decision + rationale, any rollbacks, stored-counts-
unchanged confirmation, the final 45-tool status, restore points, and a clear verdict. Update CURRENT_STATE +
MCP_SYSTEM_AUDIT_FINDINGS (mark fixed findings closed). Explicitly note that Wave 5 (salience+synthesis) remains
open + native-design-gated.

## §6 — Acceptance criteria (whole campaign)
- All Wave 1–4 findings closed + prod-verified (F-001,002,003,004,005,006,008,011,012,013,014,015,016,018,021,
  023,026,028,030,031) PLUS Wave 2.5 (F-032 reasoning-units registered → G10-unblocked; F-033 tier leak stripped).
  The retrievability matrix is 45/45 reachable INCLUDING the assess_* reasoning units; insight surface serves on
  default; payloads bounded; phala/sidecar restored; both services (web+mcp) on the merged SHA.
- Stored data + seal counts UNCHANGED; retrieval FROZEN; chart-agnostic green; no Wave-5 work performed.
- Morning report emitted; findings register updated; CURRENT_STATE updated.

## §7 — Kickoff
Open Claude Code in Antigravity, bypass permissions, point the Conductor here. It reads this charter + the Wave 1
brief + the findings register + the fix plan + the frozen §4 seam, snapshots, and drives Waves 1→4 with mandatory
per-wave prod-verification. Native reviews the morning report; Wave 5 is designed separately with the native.

*End of CLAUDECODE_BRIEF_AUDIT_FIX_SWARM_W1_W4 v1.0. Waves 1–4 = deterministic, batched, self-verified. Wave 5
= the astrological judgment layer, native-design-gated, out of scope here.*
