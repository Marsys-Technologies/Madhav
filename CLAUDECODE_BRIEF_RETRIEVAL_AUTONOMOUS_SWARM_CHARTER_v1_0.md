---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_AUTONOMOUS_SWARM_CHARTER
version: 1.0
status: READY-FOR-EXECUTION — the governing charter for the autonomous overnight retrieval build
created: 2026-06-27
author: Cowork (planning) — for autonomous execution by the Claude Code agentic swarm in Antigravity
classification: CLAUDECODE_BRIEF — autonomous swarm execution charter (conductor reads this first)
mode: FULLY AUTONOMOUS · bypass permissions · overnight · sub-agent swarm · worktree-isolated
parent_plan: RETRIEVAL_IMPLEMENTATION_MASTER_PLAN_v1_1 (the runway this charter executes autonomously)
governs_briefs: runtime-validation, D0.5 cleanup, D1 contract, D2 router, D3 grounding, D4 graph,
  D-PROFILES/MARO, D5 fan-out, D6/D7 channels, D8 eval/seal, parallel-coordination
relevant_memory (autonomy precedents + scars):
  - feedback_full_autonomy_works_for_brahma (+ the seal-vs-prod-divergence amendment)
  - feedback_two_stream_branch_policy / Brahma AUTONOMOUS_MODE (self-decided gates under rails)
  - feedback_ac_must_verify_target_environment (prod-verify, not worktree-complete)
  - feedback_destructive_brief_reverse_citation_gate (auto-grep before any delete)
  - feedback_degenerate_distribution_guard (distribution checks)
  - project_pyjhora_engine_validation_deferred (snapshot-before-rebuild discipline)
native_rulings (this run's authority level — explicit):
  - human-proxy makes ALL calls autonomously INCLUDING irreversible (delete/freeze) — NO queue to native
  - swarm may apply SCHEMA MIGRATIONS autonomously (hits prod)
  - on audit failure, KEEP RETRYING autonomously until green
  - snapshot/restore recovery rails enabled (pure recovery infra; never pauses the swarm)
---

# AUTONOMOUS SWARM EXECUTION CHARTER — RETRIEVAL SYSTEM BUILD

> **What this is.** The single governing document the conductor reads to drive the ENTIRE D0→D8 retrieval
> build autonomously, overnight, with a sub-agent swarm under bypass permissions. The native has authorized
> maximum autonomy: the human-proxy agent makes every call including irreversible ones, schema migrations run
> autonomously, audits retry until green. Two recovery rails (snapshots + auto reverse-citation) are RECOVERY
> INFRASTRUCTURE, not decision gates — they never pause the swarm; they make the autonomy recoverable.
>
> **The goal (the Goal-Keeper's north star):** a best-in-class, chart-agnostic retrieval system implementing
> the full design (RETRIEVAL_SYSTEM_DESIGN_APPROACH v1.4 + the 4 D-GROUNDTRUTH deliverables), serving both
> the MCP and chat channels across all 4 LLM families, built per the master plan, sealed by the eval harness.

## §1 — The swarm roster

- **Conductor** — orchestrates the phase DAG (§3); spawns/sequences builder agents; owns the run state;
  honors serial-spine + two-fan-out parallelism (coordination brief). Does not write feature code itself.
- **Human-Proxy (expert)** — stands in for the native at EVERY gate the briefs define. Full authority,
  autonomous, no queue: makes DG-style calls, the eliminate-vs-integrate-vs-build-around calls on surprising
  legacy code, contract-freeze posture in practice, and all irreversible/destructive approvals. Decides per
  the design intent + the 14 principles + the relevant memory scars. Records every consequential call with
  rationale in the run log (for the native's morning review — recorded, not gated).
- **Goal-Keeper** — one agent whose sole job is ensuring every wave drives to the end goal; detects scope
  drift, gold-plating, or a wave solving the wrong problem; can redirect a builder or flag the Conductor.
- **Auditor (independent, per-phase)** — after each phase, independently verifies the phase was built per
  plan + per acceptance criteria, **verified against prod** (not worktree). Distinct agent from the builders.
  On failure → triggers remediation (§4). Also runs the contamination + distribution + reverse-citation checks.
- **Builder agents** — one per parallel wave (D2/D3/D4; D-PROFILES; D5 layer sub-waves), each in its own
  worktree/branch, building only its new files per the coordination brief's Gate A.

## §2 — Autonomy rails (what the swarm may do without the native)

**MAY, autonomously:** write/refactor code + tests; create worktrees/branches; run builds + tests;
read-only AND mutating DB queries; **apply schema migrations** (native-ruled); **delete/retire/integrate/
build-around legacy code** per the Human-Proxy's call; freeze the contract; merge to main; deploy as needed
for prod-verification.

**MUST, automatically (recovery rails — not pauses):**
- **Snapshot before the run and at every phase boundary:** git tag + DB snapshot (per snapshot-before-rebuild).
  These are restore points; the Auditor may roll back to the last good one and retry rather than compounding
  corruption. The swarm does not wait for anyone to snapshot — it's automatic.
- **Reverse-citation before ANY deletion:** the swarm itself greps the live codebase for active citations of
  every delete target, reclassifies still-cited targets as keep-or-repoint, and records the citation report.
  This is automatic and self-executed — full autonomy means the swarm DECIDES, not that it SKIPS checking.
- **Chart-agnostic + contamination check on every wave:** no native defaults, chart_id required, no native in
  descriptions; verified by the Auditor each phase.

**MUST NOT, ever (the one hard floor):** destroy prod DATA without a current snapshot + a passed reverse-
citation report. Schema changes are allowed; unrecoverable data loss is not. (Snapshots make even aggressive
changes recoverable — that's the point.)

## §3 — The phase DAG (what the conductor drives)

```
SNAPSHOT(run-start)
  PHASE 0 (serial): runtime-validation → D0.5 cleanup        → AUDIT-0 → SNAPSHOT
  PHASE 1 (serial): D1 contract + chart-agnostic gate (FREEZE+MERGE) → AUDIT-1 → SNAPSHOT
  PHASE 2 (parallel fan-out 1): D2 ∥ D3 ∥ D4 → integration smoke → AUDIT-2 → SNAPSHOT
  PHASE 3 (parallel fan-out 2): D-PROFILES ∥ D5 (∥ L0/L1/L2 sub-waves) → roster smoke → AUDIT-3 → SNAPSHOT
  PHASE 4 (serial): D6 synergy + D7 channels (+ old-MCP remediation under auto reverse-citation) → AUDIT-4 → SNAPSHOT
  PHASE 5 (serial): D8 eval harness + profile-hardening + governance + red-team → SEAL → AUDIT-5 (final)
```

Each builder wave follows its own brief (the §0 embedded decisions + acceptance criteria). Parameterized
briefs (D-PROFILES, D5, D6/D7, D8): the **Conductor runs the detail-pass** (fills the §0 `[resolved from …]`
markers from now-available upstream outputs) before dispatching that wave — replacing Cowork's detail-pass with
an autonomous one, using the same upstream artifacts.

## §4 — Audit + remediation loop (keep-retrying, native-ruled)

After each phase, the Auditor verifies per the phase's acceptance criteria, **against prod** (`[verify-against:
prod]`), plus: chart-agnostic/contamination clean, F1 dedup, distribution non-degenerate, reverse-citation
reports present for any deletion, no contract drift, no cross-branch edits.

- **Pass** → snapshot, advance.
- **Fail** → the swarm **keeps retrying autonomously** (native-ruled): bounded remediation cycles; if a cycle
  regresses or corrupts, the Auditor **rolls back to the last good snapshot** and retries from there (this is
  what makes infinite-retry safe — it can't compound on corruption). The Goal-Keeper watches for thrash and
  can redirect the approach. Independent parallel waves continue meanwhile.
- Every retry + every Human-Proxy irreversible call is logged for the morning report.

## §5 — Surprises with existing code (the Human-Proxy's mandate)

The codebase has known landmines (two/three retrieval systems, contaminated old MCP tools, stale manifests,
service-vs-table assets). When a builder hits surprising legacy code, the **Human-Proxy decides** eliminate /
integrate / build-around, guided by: the DG1 ruling (build on `lib/retrieval`, migrate+retire `lib/retrieve`,
remediate old MCP tools), the 14 principles, the contamination findings (validation §H), and the memory scars.
Deletions always run the auto reverse-citation gate first. The decision + rationale is logged.

## §6 — The morning report (what the native wakes to)

The Conductor emits a single `RETRIEVAL_AUTONOMOUS_RUN_REPORT` covering: phases completed + sealed; every
irreversible/destructive decision the Human-Proxy made + its rationale + the citation report; every audit
result + any rollbacks; what was eliminated vs integrated vs built-around; the final eval/seal numbers
(per-model); any phase that could not be completed + why; the restore points available; and a clear
"state of the system" verdict against the goal. Also updates CURRENT_STATE + the campaign tracker.

## §7 — Acceptance criteria for the whole run

- Full D0→D8 built per the master plan; sealed by D8's eval harness; all 14 principles satisfied (esp. #3
  cited-numbers, #14 chart-agnostic, F1 dedup).
- Both channels (MCP + chat) served from the single registry source; no drift; works across all 4 LLM families.
- Every phase prod-verified by the independent Auditor; every deletion has a citation report; zero native
  contamination; snapshots/restore points at every boundary.
- Morning report emitted with every irreversible decision logged; CURRENT_STATE + tracker updated.

## §8 — Kickoff (how the native launches this)

Open Claude Code in Antigravity with bypass permissions; point the Conductor at THIS charter. The Conductor
reads the charter + the master plan + all wave briefs + the design artifacts, takes the run-start snapshot, and
drives the DAG autonomously to seal. The native reviews the morning report.

*End of CLAUDECODE_BRIEF_RETRIEVAL_AUTONOMOUS_SWARM_CHARTER v1.0 — the governing charter for the autonomous
overnight build. Maximum autonomy per native ruling; recovery rails make it recoverable, not gated.*
