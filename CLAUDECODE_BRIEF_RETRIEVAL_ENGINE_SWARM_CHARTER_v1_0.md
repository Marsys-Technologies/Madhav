---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_ENGINE_SWARM_CHARTER
version: 1.0
status: READY-FOR-EXECUTION — the governing charter for the autonomous retrieval-engine build (R-1 → R6)
created: 2026-06-29
author: Cowork (planning) — for autonomous execution by the Claude Code agentic swarm in Antigravity
classification: CLAUDECODE_BRIEF — autonomous swarm execution charter (retrieval engine)
mode: FULLY AUTONOMOUS · bypass permissions · sub-agent swarm · worktree-isolated · data-gated
grounded_in:
  - RETRIEVAL_RECONFIRM_FINDINGS_v1_0.md (LIVE re-confirmation — what's already fixed vs what remains)
  - RETRIEVAL_ELEVATION_PLAN_v1_0.md (the R0–R6 phase definitions)
  - RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_0.md (the FROZEN seam — §4)
  - RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY_v1_0.md / _TRAVERSAL_MODEL_v1_0.md (astrological tool design)
  - BUILD_PATH_RETRIEVAL_AUDIT_FINDINGS_v1_0.md (defect detail for the residual fix)
relevant_memory: feedback_full_autonomy_works_for_brahma (+seal-vs-prod amendment); feedback_ac_must_verify_target_environment (prod-verify); feedback_destructive_brief_reverse_citation_gate (auto-grep before delete); feedback_degenerate_distribution_guard; project_pyjhora_engine_validation_deferred (snapshot-before-rebuild)
native_rulings (this run's authority):
  - retrieval charter OWNS both cross-cutting blockers: the 401 seam fix + the bo_samvada contradictions re-run
  - R3.1/R3.2 proceed NOW on healthy grounding; R3.3 (contradiction-as-output) gated on bo_samvada
  - human-proxy makes all calls incl. irreversible (per the prior overnight-build precedent); snapshots enable rollback
hard_constraint: honor the FROZEN sync contract — retrieval stays chart-agnostic + FROZEN; entitlement stays at the channel (NEVER pushed into retrieval); single registry source.
---

# RETRIEVAL ENGINE — AUTONOMOUS SWARM CHARTER (R-1 → R6)

> The governing charter the conductor reads to drive the retrieval-engine build autonomously. Grounded in the
> LIVE re-confirmation: the runtime is 94+/96 already repaired, MSR grounding is HEALTHY (98.88%), and the build
> is gated by exactly two things — the contradictions data (`bodha_contradictions` = 0) and the 401 seam — both
> of which THIS charter owns and fixes. The goal: a working, acharya-grade, multi-LLM retrieval engine, served
> as the single registry source to both channels, in sync with the MCP fork via the frozen contract.

## §1 — The swarm roster
- **Conductor** — drives the R-1→R6 DAG; spawns/sequences builders; owns run state; honors the data gate.
- **Human-Proxy (expert)** — makes every gate/architecture/irreversible call autonomously, logging rationale.
  Decides per the topology + traversal model + the 14 principles + the frozen contract.
- **Goal-Keeper** — ensures every wave drives to the goal (acharya-grade, multi-LLM, single-source); flags drift.
- **Auditor (independent, per-phase)** — verifies each phase per acceptance criteria, **prod-verified** (not
  worktree); runs the chart-agnostic + contamination + distribution + reverse-citation checks.
- **Builders** — one per parallel wave, worktree-isolated, building only their wave's files.

## §2 — Autonomy rails (recovery, not gates)
- **Snapshot** (git tag + DB snapshot) at run-start + each phase boundary → rollback-and-retry on corruption.
- **Auto reverse-citation** before ANY deletion (self-executed grep; citation report in PR).
- **Chart-agnostic + contamination check** every phase (no native defaults/fallbacks; chart_id required).
- **Hard floor:** never destroy prod DATA without a current snapshot + passed citation report. (Note the prior
  `mi_seva` unscoped-DELETE class — any DELETE must be chart/user-scoped + snapshotted.)
- **MAY autonomously:** code, tests, worktrees, read+write DB, schema migrations, the bo_samspada re-run,
  deletions (under citation gate), merges, prod-verify deploys.

## §3 — The phase DAG (grounded in re-confirmation)

```
SNAPSHOT(run-start)
  R-1  RUNTIME REPAIR (tiny): the single residual defect — call_service_wrappers.ts:485,512
       callPriorityRankingCapability _ctx.db → import { query } (the fix applied 23× elsewhere). → AUDIT → SNAPSHOT
  R0   DATA GATES:
       R0.1 MSR grounding — ALREADY HEALTHY (98.88%, re-confirmed). VERIFY-ONLY, no rebuild. ✓
       R0.2 bodha_contradictions = 0 → diagnose the bo_samvada writer, fix, re-run, populate for ≥2 charts.
            (THIS charter owns it.) → AUDIT (contradictions non-empty) → SNAPSHOT
  R1   CONTAMINATION/HYGIENE: confirm kala_temporal fallback fixed (re-confirm said largely remediated —
       verify); remove any residual dead code under citation gate; extend chart-agnostic gate to fallback paths. → AUDIT → SNAPSHOT
  R2   KEYSTONE — REGISTRY = SERVED SURFACE:
       R2.0 Fix the 401 seam (remove x-mcp-audience-tier from the /api/mcp/primitives guard). (THIS charter owns it.)
       R2.1 Repoint the 5 bypassing MCP tools (audit.ts, remedy_tools.ts, read_classical_text.ts, kala_timeline.ts,
            holistic_bundle.ts) to the registry via the seam; retire own-pool SQL under citation gate.
       R2.2 Expose getMcpSurfaceSpec(family) as the published seam output the MCP fork consumes.
       → AUDIT (every MCP tool resolves to a registry capability; single-source drift test MCP==chat, ≥2 charts) → SNAPSHOT
  R3   ASTROLOGICAL ELEVATION (heart):
       R3.1 reasoning-unit tools (assess_marriage/career/health/…) — PROCEED NOW (grounding healthy);
            reconciled house+lord+kāraka+varga+afflictions+yogas+activating-dasha+citations; judgment calls
            flagged for acharya validation.
       R3.2 yoga-activation-by-dasha bridge — PROCEED NOW.
       R3.3 contradiction/convergence as first-class output — GATED on R0.2 (bo_samvada); build after it lands.
       R3.4 whole-chart-read ENFORCEMENT (orient-before-domain structural).
       R3.5 make synergy tools real (no stubs).
       → AUDIT (reconciled, grounded, cited bundle on ≥2 charts; orient-first enforced) → SNAPSHOT
  R4   MULTI-LLM EXPOSURE: bundle-elasticity (response_format minimal/standard/detailed, real branching);
       cross-model conclusion-consistency test (4 families, same verdict different paths); behavioral_overrides
       populate-or-amend; MARO surface wired. → AUDIT → SNAPSHOT
  R5   RICHNESS: register resources (call registerResources — currently dead); guided-reading prompts (zero today);
       astrologically-teaching descriptions. → AUDIT → SNAPSHOT
  R6   RE-SEAL: re-validate live; eval the elevated surface (14 principles hold; reasoning-units grounded +
       contradiction-aware); consolidate acharya-validation flags; red-team; version bump + re-seal; update CURRENT_STATE.
```

## §4 — Gating logic (precise, from re-confirmation)
- **R0.1 is SATISFIED** (98.88% grounding) — do NOT re-run MSR; verify-only.
- **R0.2 (contradictions) is the ONE data blocker** — it gates ONLY R3.3, not all of R3. R3.1/R3.2/R3.4/R3.5
  proceed in parallel with the bo_samvada fix.
- **R2.0 (401 fix) unblocks the keystone** — do it early; notify the MCP fork it's green (seam coordination).
- **R-1 is a single one-liner** — fold it into the R2 prep, not a standing phase.

## §5 — Frozen-contract obligations (the seam with the MCP fork)
- Retrieval stays chart-agnostic + FROZEN; entitlement is NEVER added to retrieval (the MCP fork wires
  `authorizeChartAccess` at the channel). 
- The 401 fix + `getMcpSurfaceSpec` exposure + `response_format` elasticity are the seam outputs the MCP fork
  consumes — publish them; do not redefine the contract unilaterally.
- After R2, there is ONE registry surface; both channels consume it; the single-source drift test proves it.

## §6 — Per-phase audit + remediation
Auditor verifies each phase against prod (`[verify-against: prod]`) + chart-agnostic + distribution +
citation-report-present. Pass → snapshot, advance. Fail → bounded autonomous remediation; if a retry corrupts,
roll back to the last snapshot and retry. Goal-Keeper watches for thrash.

## §7 — Morning report
Conductor emits `RETRIEVAL_ENGINE_RUN_REPORT`: phases sealed; the bo_samvada diagnosis+fix; the 401 fix; the 5
tools repointed; reasoning-units built (+ acharya-validation flags); multi-LLM consistency results; every
irreversible decision + citation reports; any rollback; final eval + re-seal; CURRENT_STATE bump. Flag anything
that diverged from this charter's expectations.

## §8 — Acceptance (whole run)
- R-1 residual defect fixed; runtime green (no swallowed handler errors on ≥2 charts).
- bo_samvada re-run; contradictions populated ≥2 charts; 401 fixed; 5 tools on the registry; single-source drift test passes.
- Reasoning-unit tools return reconciled/grounded/cited bundles; contradiction-aware once R3.3 lands; orient-first enforced.
- Multi-LLM elasticity + cross-model consistency verified across 4 families.
- Resources + prompts live; re-sealed; 14 principles hold; chart-agnostic + no contamination throughout.
- Frozen contract intact (entitlement never in retrieval; single source); seam outputs published for the MCP fork.

## §9 — Kickoff
Open Claude Code with bypass permissions; point the Conductor at THIS charter. It reads the charter + the
re-confirmation findings + the elevation plan + the topology/traversal models + the frozen contract, snapshots,
and drives R-1→R6 to re-seal. Native reviews the morning report.

*End of CLAUDECODE_BRIEF_RETRIEVAL_ENGINE_SWARM_CHARTER v1.0 — the autonomous retrieval-engine build, grounded
in live re-confirmation, gated precisely, in sync with the MCP fork via the frozen contract.*
