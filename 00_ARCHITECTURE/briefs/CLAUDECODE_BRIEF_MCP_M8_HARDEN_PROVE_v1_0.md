---
canonical_id: CLAUDECODE_BRIEF_MCP_M8_HARDEN_PROVE
version: 1.0
status: READY-FOR-EXECUTION — M8 production-grade + the final live proof of the whole goal
created: 2026-06-30
author: Cowork (planning) — detail-pass for the autonomous swarm
parent_charter: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER_v1_1 (PHASE M8 — the seal)
depends_on: M0–M7 (this proves them, live)
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT §4
verification_basis: live code + deploy.yml, read 2026-06-30
hard_constraints:
  - prove against PROD, not worktree (the seal-vs-prod-divergence scar); revision == merged SHA
  - rate-limit the 17/31 sidecar-direct tools that had none; VITEST
acceptance_criteria: see §4 — this IS the goal's acceptance test
---

# CLAUDE CODE BRIEF — MCP M8: HARDEN + PROVE (the seal)

> M8 makes the channel production-grade and PROVES the end-to-end goal live: an external LLM connects through
> MCP, accesses the retrieval system, and generates insight — securely, on ≥2 users × ≥2 charts, zero bleed.
> This is the gate that turns "built" into "done."

## §1 — M8.1 Rate limiting + observability
- **Rate limiting:** the registry/primitives path already calls `checkRateLimit(keyId)`; the sidecar-direct
  tools historically bypassed it (17/31 at audit time — recount post-keystone since most migrated). Add
  rate-limit middleware at MCP dispatch (`server.ts`) so EVERY tool is limited, including any remaining
  sidecar-direct ones. Key on `key_id` (or uid).
- **Observability:** add structured logging + request-ID propagation at the MCP layer (today `console.error`
  only); propagate the trace to the sidecar for the calls that still hit it; ensure the platform `traceEmitter`
  fires for MCP-originated calls. Enough to debug a real connector session.

## §2 — M8.2 Deployment + revision verification
Confirm the deployed `amjis-mcp` Cloud Run revision == sealed main HEAD (the verify-revision rule). Note the
deploy gate is conditional on `changes.outputs.mcp == 'true'` (`deploy.yml` deploy-mcp) — if a phase didn't
touch MCP-filtered paths, trigger a manual `workflow_dispatch`. Regenerate `/health` (dynamic count) and
`tool_list.json` if drifted.

## §3 — M8.3 Live E2E connector proof + M8.4 completeness
- **M8.3 (the headline proof):** a REAL Claude connector, ≥2 users × ≥2 charts, verifying: (a) connect +
  authenticate to a real profile (M5); (b) list + select entitled charts by name (M1/M2); (c) every per-chart
  call entitlement-gated — unentitled chart denied (M0); (d) session resume + memory scoped per user×chart
  (M3); (e) chart-switch advisory fires (M4); (f) declared-profile surface shaping (M6); (g) resources +
  guided-reading prompts available (M7); (h) reasoning-unit tools return grounded, cited, acharya-grade insight
  (the "superlative" clause); (i) ZERO native data or cross-chart bleed anywhere.
- **M8.4 completeness audit (live):** every asset/capability reachable through the connector; nothing
  silently unreachable; tool count truthful.

## §4 — Acceptance criteria (this is the GOAL's acceptance test)
- Every tool rate-limited; structured logging + request-ID + trace propagation live.
- Deployed revision == sealed main HEAD; `/health` truthful; tool_list current.
- The M8.3 live E2E proof passes on ≥2 users × ≥2 charts: connect→select→gated-access→session→advisory→
  profiled-surface→resources/prompts→grounded reasoning-unit insight, with ZERO native/cross-chart bleed.
- M8.4: every asset reachable; no silent gaps.
- **Goal met, proven live:** an external LLM connects through MCP, seamlessly accesses the retrieval system,
  uses the asset data, and generates superlative, grounded, entitlement-safe insight. Emit the
  `MCP_ELEVATION_AUTONOMOUS_RUN_REPORT` + the seal record; update CURRENT_STATE + tracker.

## §5 — VERIFICATION PHASE (the comprehensive final proof — this IS the goal's acceptance test)
M8 is itself the verification wave, so its bar is the highest. The independent Auditor proves the GOAL clause by
clause on PROD, end-to-end, with a real external LLM client. Nothing is asserted; everything is demonstrated and
logged with evidence into the run report.

**V0 — Foundations green:** both packages build; full Vitest suite green (platform + platform-mcp); the standing
platform-mcp test debris (the ~33 pre-existing failures noted in the retrieval handoff) is either fixed or
explicitly enumerated as pre-existing-not-introduced — M8 must NOT mask a real regression behind them.
**V1 — Rate limiting universal:** every tool (incl. any remaining sidecar-direct) is rate-limited; prove by
exceeding the limit on a sample tool → throttled response. No unlimited tool remains.
**V2 — Observability:** a real connector session produces structured logs with request-IDs traceable
MCP→platform→sidecar; demonstrate one trace end-to-end.
**V3 — Deploy truth:** deployed amjis-mcp revision SHA == sealed main HEAD; `/health` count truthful; tool_list current.

**V4 — THE GOAL PROOF MATRIX (real Claude connector, ≥2 users × ≥2 charts — every row demonstrated on prod):**
| # | Goal clause | Proof | Pass condition |
|---|---|---|---|
| G1 | Connect | real Claude connector completes OAuth | authenticates to a real profile (not 'anonymous') |
| G2 | Identity+entitlement | guest A vs guest B vs super_admin | each reaches exactly their entitled chart set |
| G3 | Seamless access | list_my_charts → select_chart by name | picks among entitled charts by name, not UUID |
| G4 | Gated every call | guest A → B's chart | AUTHZ_DENIED (no per-chart tool leaks) |
| G5 | Session+memory | resume a prior session | memory scoped per user×chart; no cross-user bleed |
| G6 | Switch advisory | switch active chart mid-session | advisory fires (warn, not block) |
| G7 | Per-model surface | declared vs undeclared key | profiled vs universal-best surfaces differ |
| G8 | Richness | resources/list + prompts/list | 9 resources + 3 guided prompts served; per-chart gated |
| G9 | Utilizes retrieval | a registry-served tool returns data | real grounded data via the single registry path (no MCP SQL) |
| G10 | SUPERLATIVE insight | a reasoning-unit tool (assess_marriage / yoga_activation_by_dasha) on an entitled chart | returns grounded, fact-cited (§N.5 references resolve), acharya-grade output — not generic |
| G11 | Zero bleed | sweep all of the above | NO native data, NO cross-chart data anywhere in any response |
| G12 | Completeness | every asset/capability reachable via the connector | no silent unreachable surface; tool count truthful |

**V5 — Anti-regression of the whole arc:** re-run the M0 isolation matrix + the M0.5 F1/F2 probes — confirm M8's
changes didn't regress the security gate, the registry-bridge auth, or the sidecar data path.
**V6 — Invariants:** retrieval FROZEN across the entire arc (git diff lib/retrieval over M1→M8 = only
requested+published seam changes, if any); chart-agnostic CI gate green; every deletion across the arc has a
citation report; all snapshots/restore points recorded.

**SEAL condition:** ALL of G1–G12 + V0–V6 pass on prod. Only then emit `MCP_ELEVATION_AUTONOMOUS_RUN_REPORT` +
the seal record + update CURRENT_STATE + tracker. If any goal clause cannot be proven, the run reports NOT-SEALED
with the specific clause + reason — it does not claim the goal met.

*End of CLAUDECODE_BRIEF_MCP_M8_HARDEN_PROVE v1.0 — the final wave. When V4's full goal-proof matrix passes on
prod, the MCP elevation goal is met and proven: an external LLM connects through MCP, seamlessly accesses the
retrieval system, uses the asset data, and generates superlative, grounded, entitlement-safe insight.*
