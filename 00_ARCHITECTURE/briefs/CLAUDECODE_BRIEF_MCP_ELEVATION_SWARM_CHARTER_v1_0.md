---
canonical_id: CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER
version: 1.1
status: READY-FOR-EXECUTION — the governing charter for the autonomous MCP elevation build (M0→M8)
created: 2026-06-30
updated: 2026-06-30 (v1.1 — post-retrieval-seal: M0 shrunk, keystone seam-gate moot, live seams real, 48 tools, traps added)
author: Cowork (planning) — for autonomous execution by the Claude Code agentic swarm in Antigravity
classification: CLAUDECODE_BRIEF — autonomous swarm execution charter (conductor reads this first)
mode: FULLY AUTONOMOUS · bypass permissions · sub-agent swarm · worktree-isolated · no human gate
parent_plan: MCP_ELEVATION_PLAN_AND_HANDOFF_v1_0 (the M0→M8 runway; its §C/§D vision+phases stand)
authoritative_current_state: RETRIEVAL_TO_MCP_HANDOFF_v1_0 (post-seal live reality — supersedes the
  pre-build §A/§B of the elevation plan) · CURRENT_STATE v6.07 · git HEAD 2b02f924
frozen_seam: RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT (§4 — LAW; retrieval owns it, MCP adapts) — now LIVE, not aspirational
grounded_in:
  - RETRIEVAL_TO_MCP_HANDOFF_v1_0.md (post-seal handoff — the AUTHORITATIVE current-state; code-verified)
  - MCP_ELEVATION_AUDIT_FINDINGS_v1_0.md (Claude Code 3-agent LIVE audit — P0s, 5 new findings)
  - MCP_CHANNEL_AUDIT_D0_v1_0.md (Cowork D0 current-state map — corroborating, pre-seal counts now superseded)
  - RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md (the keystone + frozen §4 seam)
pattern_inherited_from: CLAUDECODE_BRIEF_RETRIEVAL_AUTONOMOUS_SWARM_CHARTER_v1_0 (the validated overnight
  pattern that sealed the retrieval build; this charter is its MCP-arc adaptation)
relevant_memory (autonomy precedents + scars):
  - feedback_full_autonomy_works_for_brahma (+ the seal-vs-prod-divergence amendment)
  - feedback_ac_must_verify_target_environment (prod-verify, not worktree-complete)
  - feedback_destructive_brief_reverse_citation_gate (auto-grep before any delete)
  - feedback_two_stream_branch_policy / Brahma AUTONOMOUS_MODE (self-decided gates under rails)
  - feedback_verify_cloud_run_revision_before_chrome_probe (revision==SHA before any prod conclusion)
  - feedback_next_public_build_arg_baking + needs_dockerfile_arg (deploy-config traps)
  - project_mcp_elevation_workstream (this workstream's frame)
native_rulings (this run's authority level — explicit, from the 2026-06-30 conversation):
  - FULL M0→M8 in ONE charter, one kickoff, no human gate.
  - human-proxy makes ALL calls autonomously INCLUDING irreversible (delete/migrate/deploy) — NO queue to native.
  - FULL AUTONOMY incl. PROD DEPLOY (Brahma AUTONOMOUS_MODE §F): swarm self-decides merge-to-main AND prod
    deploy AND DB migrations under the §2 rails. Native reviews retrospectively via the morning report.
  - verification THOROUGHNESS is decided by the Auditor agent itself, per phase (not prescribed here).
  - SEAM POSTURE (Cowork recommendation, native-accepted): build everything NOT blocked by the retrieval
    fork autonomously; GATE only the keystone 31-tool registry migration (P0-C) on the retrieval fork's
    "R2 registry-path green" signal. If that signal is absent at the time the keystone wave is reached, the
    swarm builds a thin §4-conformant shim and proceeds, flagging it for reconciliation (never blocks the run).
---

# AUTONOMOUS SWARM EXECUTION CHARTER — MCP ELEVATION (M0 → M8)

> **What this is.** The single governing document the conductor reads to drive the ENTIRE MCP elevation arc
> (M0→M8) autonomously, with a sub-agent swarm under bypass permissions, no human gate. The native has
> authorized maximum autonomy: the human-proxy agent makes every call including irreversible ones; schema
> migrations and PROD DEPLOYS run autonomously; audits retry until green; verification thoroughness is the
> Auditor's own call per phase. Recovery rails (snapshots + auto reverse-citation) are RECOVERY INFRASTRUCTURE,
> not decision gates — they never pause the swarm; they make the autonomy recoverable.
>
> **The goal (the Goal-Keeper's north star):** the MCP channel elevated into a secure, multi-user,
> multi-chart, portal-equivalent product — entitlement-enforced, registry-served (single source per the frozen
> §4 seam), session-aware, multi-client (Claude first; ChatGPT/Gemini/DeepSeek provisioned), per-model-profiled,
> resource/prompt-rich, rate-limited, observable — proven live against real connectors on ≥2 users × ≥2 charts
> with zero native/cross-chart bleed. Chart-agnostic principle #14 holds throughout; retrieval stays FROZEN.

## §0.A — LIVE current state (post-retrieval-seal; code-verified 2026-06-30; START HERE)

The retrieval engine is SEALED + elevated (CURRENT_STATE v6.07, git HEAD `2b02f924`). Per
`RETRIEVAL_TO_MCP_HANDOFF_v1_0` — **code-verified, authoritative over earlier pre-build audits** — the
following are ALREADY DONE retrieval-side. **Do NOT redo them; build on them:**

- ✅ **M0.1 (401 fix) DONE.** `/api/mcp/primitives/[tool]/route.ts` guard is now `if(!userUid||!keyId)` —
  no `x-mcp-audience-tier` requirement. Registry-path tools return 200.
- ✅ **M0.3 (kala_temporal native contamination) DONE.** FORENSIC fallback removed; `DEFAULT_SNAPSHOT_DATE`
  = today (runtime); `FALLBACK_SNAPSHOT_TEMPLATE` is graceful-empty (`mode:'fallback_empty'`).
  `bodha_contradictions` now POPULATED (commit 2b02f924).
- ✅ **Keystone registry path is LIVE.** The 5 pg.Pool bypass tools (`remedy_tools`, `read_classical_text`,
  `kala_timeline`, `holistic_bundle`, + `audit.ts` at `platform-mcp/src/audit.ts`) are repointed to
  `callPlatformPrimitive`. There is ONE retrieval surface. **The MCP MUST NOT run its own chart SQL** — the
  anti-pattern is removed; do not reintroduce it. (This makes the old "keystone seam-gate" largely MOOT —
  the path exists NOW; remaining un-migrated tools migrate against a live path, not a future one.)
- ✅ **Live seams to consume (not build):** `/api/mcp/surface-spec` route + `callPlatformSurfaceSpec`
  (`platform-mcp/src/client.ts:348`) for `getMcpSurfaceSpec(family)`; `response_format`
  minimal|standard|detailed live in `platform/src/lib/mcp/bundle_adapters.ts`; reasoning-unit tools
  `assess_marriage/career/health/wealth` + `yoga_activation_by_dasha` in
  `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`; `registerResources()` now
  CALLED (`server.ts:149` — 9 resources live + 3 prompts: `orient_chart`, `assess_domain`, `find_active_yogas`).

**➜ The MCP build effectively STARTS at: M0.2 (the `authorizeChartAccess` entitlement gate — still 0 hits in
`platform-mcp/src/`, the remaining P0 security keystone) + the principal→role/owner_id mapping that gates it.**
Then M1→M8. Tool count is **48** wired `.tool()` registrations (earlier 26/31 counts are superseded);
`/health` still hardcodes `tools: 13` (stale — fix in M0.4).

## §0.B — The two non-negotiable invariants (every agent honors these before anything else)

1. **The frozen §4 seam is LAW.** Retrieval (`platform/src/lib/retrieval/`) is chart-agnostic and FROZEN:
   `chart_id` required, never defaulted, ZERO entitlement awareness. The MCP fork (a) NEVER pushes entitlement
   into retrieval; (b) NEVER runs its own chart SQL or re-implements retrieval; (c) consumes capabilities via
   the platform seam (`/api/mcp/primitives/[tool]` → `getToolByName` → `tool.retrieve`), `getMcpSurfaceSpec(family)`,
   and the `response_format` elasticity param. On any conflict, retrieval wins and MCP adapts. A seam change is
   REQUESTED from the retrieval fork, never made unilaterally.
2. **Entitlement lives at the channel (Option 1, ruled).** Every chart-scoped MCP call MUST resolve the
   principal to `owner_id`/role and call `authorizeChartAccess(principal, chart_id)`
   (`platform/src/lib/auth/authorizeChartAccess.ts`) and DENY before any chart-keyed retrieval. The built
   chokepoint `invokeTool` (`platform/src/lib/gateway/invoke_tool.ts`) is the reference pattern.

## §1 — The swarm roster

- **Conductor** — orchestrates the M0→M8 phase DAG (§3); spawns/sequences builder agents; owns run state;
  runs the detail-pass on parameterized waves (fills `[resolved from …]` from now-available upstream outputs);
  honors parallelize-within-phase / sequence-across-phase. Does not write feature code itself.
- **Human-Proxy (expert in the MCP/auth/retrieval-seam space)** — stands in for the native at EVERY decision a
  human would gate. Full authority, autonomous, no queue: the declaration-mechanism choice (M6.1: config vs
  OAuth-scope vs per-key vs client-hint), the session-store location call (M3.1), the eliminate/integrate/
  build-around call on surprising legacy code, the keystone shim-vs-wait call (per the seam posture), and all
  irreversible approvals (deletes, schema migrations, merges, PROD DEPLOYS). Decides per the §4 seam, the 14
  principles, the audit findings, and the memory scars. Logs every consequential call + rationale.
- **Goal-Keeper** — sole job: every wave drives to the end goal (§ goal above). Detects scope drift,
  gold-plating, or a wave solving the wrong problem (e.g. re-implementing retrieval, pushing entitlement into
  the frozen layer, over-building session memory). Can redirect a builder or flag the Conductor.
- **Auditor (independent, per-phase)** — after each phase, independently verifies the phase was built per the
  plan + acceptance criteria, **verified against PROD** (not worktree), with thoroughness the Auditor itself
  decides per phase. **HARD GATE (mandatory, every phase — added after M0 merged non-compiling):** before any
  merge/deploy claim, run `cd platform-mcp && npm run build` (tsc) AND `cd platform && npm run build` — both
  must exit 0; then confirm a SUCCESSFUL Cloud Run deploy AND `revision image SHA == merged SHA` AND the
  behavioral prove-step (e.g. the isolation matrix for security phases) BEFORE marking the phase done. A phase
  that compiles in a worktree but fails `tsc` on the full package, or deploys but isn't behaviorally proven, is
  NOT done. (M0 lesson: a brief that changes a shared type/signature MUST update all call sites; the build gate
  catches the ones it didn't.) Always also runs: the security battery (entitlement isolation), the
  chart-agnostic/contamination check, reverse-citation reports for any deletion. Distinct agent from the
  builders. On failure → remediation loop (§4). **Behavioral proofs need a test key** — provision via
  `POST /api/mcp/keys` (the code path), never hand-SQL; for deny-tests, use a guest key not entitled to the
  target chart (a super_admin key returns 'all' and can't prove deny).
- **Builder agents** — one per parallel wave, each in its OWN worktree/branch, building only its scoped files.
  Never edit another wave's branch (cherry-pick-to-main to recover contamination per the branch-isolation scar).

## §2 — Autonomy rails (what the swarm may do without the native)

**MAY, autonomously:** write/refactor code + tests; create worktrees/branches; run builds + tests; read AND
mutating DB queries; **apply schema migrations** (new tables: `mcp_oauth_tokens`, `mcp_oauth_clients`, MCP
session/memory tables — native-ruled); **delete/retire/integrate/build-around legacy code** per the Human-Proxy's
call; **merge to main**; **deploy to PROD** (amjis-mcp + amjis-web as the entitlement/route changes require);
make the M6.1 declaration-mechanism + M3.1 session-store decisions.

**MUST, automatically (recovery rails — not pauses):**
- **Snapshot before the run and at every phase boundary:** git tag + DB snapshot (snapshot-before-rebuild).
  Restore points; the Auditor may roll back to the last good one and retry rather than compound corruption.
- **Reverse-citation before ANY deletion:** the swarm itself greps live code for active citations of every
  delete target (the kala_temporal native fallback, the in-memory OAuth Maps, `bo_2-7.ts` dead code, stale
  `tool_list.json`), reclassifies still-cited targets as keep-or-repoint, records the citation report.
- **Chart-agnostic + contamination check every wave:** no native defaults, `chart_id` required, no native in
  descriptions, no native-data fallbacks (the kala_temporal class of bug). Verified by the Auditor each phase.
- **Prod-verify every phase:** every acceptance criterion tagged `[verify-against: prod]`; the headline
  numbers (tool count, entitlement-deny on unentitled chart, 401-fix 200s) re-checked on live prod, and the
  running Cloud Run revision confirmed == the merged SHA before any "done" claim.

**MUST NOT, ever (the one hard floor):** destroy prod DATA without a current snapshot + a passed reverse-
citation report. Schema additions/changes are allowed; unrecoverable data loss is not. Also MUST NOT violate
§0 (push entitlement into retrieval / run own chart SQL / unilaterally change the seam).

## §3 — The phase DAG (what the conductor drives)

```
SNAPSHOT(run-start) + prod-revision baseline (amjis-mcp current revision == main HEAD?)

PHASE M0 (serial — SECURITY; do FIRST). NOTE: M0.1 + M0.3 ALREADY DONE retrieval-side (§0.A) — skip them.
   M0.4-a principal→role/owner_id mapping (extend Principal; DB lookup user_uid→owner_id+role at auth)
        ∥  M0.4-b dynamic /health (48 not 13) + regenerate stale tool_list.json   [independent — parallel]
   → then M0.2 authorizeChartAccess entitlement gate on every chart-scoped path (REMAINING P0; depends on
        M0.4-a). Confirm-on-start: re-grep `authorizeChartAccess` in platform-mcp/src/ == 0 hits before building.
   → AUDIT-M0 (security battery: ≥2 users × ≥2 charts isolation; registry-path tools 200 [already true];
        no native data reachable by a non-native chart [already true — re-verify]) → MERGE → PROD DEPLOY →
        prod-verify → SNAPSHOT

PHASE M0.5 (NEW — infra unblock; surfaced by the M0 proof): F1 proxy.ts isPublic allowlist for /api/retrieval/
   (registry_bridge 401 fix) ∥ F2 PYTHON_SIDECAR_URL / sidecar reachability ∥ F3 dead-key hygiene
   → AUDIT-M0.5 (a registry-bridge tool 200s; holistic_bundle returns real data for an entitled chart) →
   MERGE → DEPLOY → SNAPSHOT. NOTE: F1+F2 GATE the M8 live-prove (no data without them).

PHASE M1 (serial): M1.1 identity core (uid+role resolver) → M1.2 getEntitledCharts(uid) → M1.3 enforce on
   every call → AUDIT-M1 (reachable set == portal entitlement; cross-user isolation proven on prod) →
   MERGE → DEPLOY → SNAPSHOT

PHASE M2 (parallel fan-out): M2.1 list_my_charts ∥ M2.2 select_chart/active-chart ∥ M2.3 charts-as-resources
   → integration smoke → AUDIT-M2 → MERGE → DEPLOY → SNAPSHOT

PHASE M3 (serial — M3.1 store decision gates the rest): M3.1 session-state store (Human-Proxy picks location)
   → M3.2 conversation memory + recall_session/list_my_sessions ∥ M3.3 per-chart continuity
   → AUDIT-M3 (resume works; memory scoped per user×chart) → MERGE → DEPLOY → SNAPSHOT

PHASE M4 (serial): M4.1 chart-switch advisory (warn, not block) → AUDIT-M4 → MERGE → DEPLOY → SNAPSHOT

PHASE M5 (parallel fan-out — may overlap M2/M3 if conductor has capacity):
   M5.1 auth architecture (one core, many front-doors) → then M5.2 production OAuth (DB-backed token/code/
   client store, real Firebase identity binding, dynamic client registration) ∥ M5.3 Claude connector E2E
   → M5.4 provision ChatGPT/Gemini/DeepSeek paths (design + scaffold)
   → AUDIT-M5 (Claude connector E2E with real identity+entitlement; OAuth survives restart + multi-instance)
   → MERGE → DEPLOY → SNAPSHOT

PHASE M6 (serial): M6.1 declaration mechanism (Human-Proxy decides) → M6.2 consume getMcpSurfaceSpec(family)
   (declared→profiled / undeclared→universal-best) → AUDIT-M6 → MERGE → DEPLOY → SNAPSHOT

PHASE M7 (parallel fan-out — consumes retrieval R5): M7.1 registerResources() + chart catalog/vocab/schema
   ∥ M7.2 expose guided-reading prompts as MCP prompts → AUDIT-M7 → MERGE → DEPLOY → SNAPSHOT

KEYSTONE (the registry migration; NO LONGER SEAM-GATED — the path is LIVE and SUBSTANTIALLY LANDED per §0.A):
   ground-truth (live code, 2026-06-30) shows `platform-mcp/src/tools/registry_bridge.ts` already exposes 12
   registry-served tools (get_chart_orientation, get_domain_reading, get_signals, traverse_graph, get_positions,
   get_dashas, get_temporal_windows, get_projections, get_remedies, get_chart_quality, get_classical_citation,
   list_assets) + 5 prior pg.Pool tools repointed. Remaining wave = migrate the still-direct sidecar/REST tools
   (the phala_*, bo_2-8 holistic_bundle, kala_temporal_bundle, mimamsa_* sidecar callers) to the registry path,
   each under the entitlement gate + uniform envelope. No shim, no waiting. Any capability genuinely missing
   registry-side is REQUESTED from the retrieval fork (§4), not solved with local SQL.

PHASE M8 (serial — production-grade + PROVE): M8.1 rate limiting (the 17/31 sidecar-direct tools) +
   observability (request-ID + trace propagation) → M8.2 deployment + revision verification (deployed ==
   sealed main) → M8.3 E2E connector test (real Claude, ≥2 users × ≥2 charts: access control + selection +
   isolation + no native/cross-chart bleed) → M8.4 completeness audit (every asset reachable via connector)
   → FINAL AUDIT-M8 → SEAL → morning report.
```

**Each phase now has a RESOLVED, code-grounded brief — the Conductor dispatches these directly (no per-wave
detail-pass needed; the key decisions are already made in them):**
- M0 → `CLAUDECODE_BRIEF_MCP_M0_ENTITLEMENT_GATE_v1_0.md` (✅ SEALED + PROVEN on prod 2026-06-30, HEAD dbc047ba;
  isolation matrix passed — 5b AUTHZ_DENIED fired; /health=43)
- M0.5 → `CLAUDECODE_BRIEF_MCP_M0_5_INFRA_UNBLOCK_v1_0.md` (NEW — F1 registry_bridge proxy 401 [BLOCKING] +
  F2 sidecar unreachable [BLOCKING] + F3 dead key hygiene; surfaced by the M0 proof; gates M8 live-prove)
- M1 → `CLAUDECODE_BRIEF_MCP_M1_IDENTITY_ENTITLEMENT_v1_0.md`
- M2 → `CLAUDECODE_BRIEF_MCP_M2_CHART_SELECTION_v1_0.md`
- M3+M4 → `CLAUDECODE_BRIEF_MCP_M3_M4_SESSION_MEMORY_v1_0.md`
- M5 → `CLAUDECODE_BRIEF_MCP_M5_MULTICLIENT_OAUTH_v1_0.md`
- M6+M7 (+keystone) → `CLAUDECODE_BRIEF_MCP_M6_M7_PROFILE_RICHNESS_v1_0.md`
- M8 → `CLAUDECODE_BRIEF_MCP_M8_HARDEN_PROVE_v1_0.md` (the live goal-proof)

Resolved decisions baked into the briefs (Human-Proxy may revise, but defaults are set): M3.1 store = new
`mcp_sessions` table (migration 382, cross-dir-checked); M6.1 mechanism = per-key binding + client-hint
override; keystone = migrate-against-the-live-path (substantially landed via `registry_bridge.ts`, no shim).
Each wave still follows its activity spec from `MCP_ELEVATION_PLAN_AND_HANDOFF §D` for anything the brief
leaves open.

**MANDATORY PER-PHASE VERIFICATION (charter-level, native-ruled 2026-06-30):** EVERY phase M1→M8 ends with the
embedded "VERIFICATION PHASE" section in its brief. A phase is NOT done — no merge-claim, no advance — until its
full V-list passes, run by the independent Auditor, **proven on PROD**, thoroughness Auditor-decided but never
below the brief's floor. The V-lists always include: the build gate (`platform-mcp` + `platform` tsc exit 0 +
`typecheck-mcp` CI green — the M0-merged-broken catch), deploy + revision-SHA-match, the behavioral prod proof
(deny-tests use a GUEST key since super_admin returns 'all'), and the invariants (retrieval FROZEN,
chart-agnostic green, reverse-citation on deletes). M8's verification is the comprehensive G1–G12 goal-proof
matrix. This is the lesson of the manual waves: every one found a defect that passed review but failed on prod —
the per-phase verification closes that gap for the autonomous run.

## §4 — Audit + remediation loop (keep-retrying, native-ruled; thoroughness Auditor-decided)

After each phase the Auditor verifies, against PROD, per the phase's acceptance criteria PLUS the standing
battery: entitlement isolation (no key reads an unentitled chart), chart-agnostic/contamination clean, no
native-data fallback, reverse-citation reports for any deletion, no §0 seam violation, no contract drift, no
cross-branch edits, prod-revision == merged SHA. **The Auditor decides how thorough each phase's verification
must be** (a security phase like M0/M1 warrants a deeper battery than M4's advisory).

- **Pass** → snapshot, advance.
- **Fail** → swarm **keeps retrying autonomously**: bounded remediation cycles; if a cycle regresses or
  corrupts, roll back to the last good snapshot and retry from there (this makes infinite-retry safe — it can't
  compound on corruption). The Goal-Keeper watches for thrash and can redirect the approach. Independent
  parallel waves continue meanwhile.
- Every retry + every Human-Proxy irreversible call (delete/migrate/merge/deploy) is logged for the report.

## §5 — Surprises with existing code (the Human-Proxy's mandate)

Known landmines for this arc: 29/31 tools bypass the registry (keystone); in-memory OAuth issuing `anonymous`
tokens; the kala_temporal native fallback; `bo_2-7.ts` dead code; stale `/health` + `tool_list.json`;
Principal carrying no role/owner_id; `house_rules_variants/{client,acharya,super_admin}.md` audience-tier
residue (strip per no-tier doctrine). When a builder hits surprising legacy code, the **Human-Proxy decides**
eliminate / integrate / build-around, guided by §0, the 14 principles, the audit findings, and the scars.
Deletions always run the auto reverse-citation gate first. Decision + rationale logged.

**Hard-won traps every builder carries (from the retrieval build; `RETRIEVAL_TO_MCP_HANDOFF §5`):**
- **VERIFY LIVE, don't trust reports.** "Done" claims were contradicted by live data repeatedly. Run the
  read-only check yourself before acting (the Auditor enforces this; builders adopt it too).
- **Test framework is VITEST, not jest.** platform v4.1.x, platform-mcp v2.1.9. There is NO jest/Babel — any
  brief or fix assuming jest is wrong.
- **The `_ctx.db` trap.** `CapabilityContext` carries only `{chart_id?, request_id?}` — destructuring
  `{db}=_ctx` yields `undefined`. Correct pattern: `import { query } from '@/lib/db/client'`.
- **Native contamination is a recurring CLASS.** It re-appears in fallback paths, LLM-visible `description:`
  strings, AND tests that assert the native name. The CI gate catches tool-file identifiers; builders must
  also watch descriptions + test assertions. **Never make a test green by re-embedding the native name.**
- **Scoped DELETE only.** A prior unscoped `DELETE FROM mimamsa_preferences` wiped all users' prefs. Every
  DELETE is chart/user-scoped, behind the reverse-citation gate.
- **Known non-blocking debris:** ~33 platform-mcp Vitest failures are test-hygiene (stale teardown files,
  fetch-mock wiring, one stale FORENSIC assertion) being triaged retrieval-side — NOT MCP-build regressions.
  Do not chase them as if the swarm caused them; do not mask a real regression behind them either.

## §6 — The morning report (what the native wakes to)

The Conductor emits a single `MCP_ELEVATION_AUTONOMOUS_RUN_REPORT` covering: phases completed + sealed; every
irreversible decision (delete/migrate/merge/PROD-DEPLOY) + rationale + citation report; the M3.1 + M6.1 +
keystone shim-vs-wait decisions made + why; every audit result + any rollbacks; what was eliminated vs
integrated vs built-around; the live E2E connector proof (users × charts, isolation result); the final prod
state (revision SHA, tool count, entitlement-deny proof); any phase not completed + why; restore points
available; and a clear "state of the MCP channel" verdict against the goal. Also updates CURRENT_STATE + this
workstream's tracker. If the keystone migration was shimmed (retrieval R2 not green), it is flagged for the
retrieval fork's reconciliation.

## §7 — Acceptance criteria for the whole run

- M0→M8 built per the plan; chart entitlement enforced on every chart-scoped path (no key reads an unentitled
  chart — proven on prod, ≥2 users × ≥2 charts); the 401 keystone-blocker fixed; no native data reachable by a
  non-native chart.
- Registry-served single source honored per §4 wherever the path exists (keystone migrated, or shimmed +
  flagged); retrieval stayed FROZEN and chart-agnostic (zero MCP-side entitlement leaked into it).
- Multi-client: Claude connector works E2E with real identity + entitlement; OAuth DB-backed, survives restart
  + multi-instance; ChatGPT/Gemini/DeepSeek paths provisioned.
- Per-model declared profile wired (declared→profiled / undeclared→universal-best); resources + prompts served
  live; rate limiting + observability across the surface.
- Every phase prod-verified by the independent Auditor; every deletion has a citation report; snapshots at every
  boundary; the live E2E proof passes; morning report emitted with every irreversible decision logged;
  CURRENT_STATE + tracker updated.

## §8 — Kickoff (how the native launches this)

Open Claude Code in Antigravity with bypass permissions; point the Conductor at THIS charter (the one-page
launch text is `MCP_ELEVATION_AUTONOMOUS_RUN_KICKOFF.md`). The Conductor reads this charter + the elevation
plan + the frozen §4 seam + the two audit findings + the design artifacts, takes the run-start snapshot +
prod-revision baseline, and drives the M0→M8 DAG autonomously to seal. The native reviews the morning report.

*End of CLAUDECODE_BRIEF_MCP_ELEVATION_SWARM_CHARTER v1.0 — the governing charter for the autonomous MCP
elevation build. Maximum autonomy per native ruling (incl. prod deploy); recovery rails make it recoverable,
not gated; the frozen §4 seam keeps it in sync with the retrieval fork.*
