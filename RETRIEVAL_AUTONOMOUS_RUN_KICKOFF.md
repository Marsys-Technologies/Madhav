---
canonical_id: RETRIEVAL_AUTONOMOUS_RUN_KICKOFF
version: 1.0
status: READY — paste the §2 prompt into Claude Code (bypass permissions) to launch the overnight run
created: 2026-06-27
author: Cowork
---

# RETRIEVAL AUTONOMOUS RUN — KICKOFF

## §1 — Pre-launch checklist (native, ~2 min)
1. Open Claude Code in Antigravity with **bypass permissions** enabled.
2. Confirm the localhost→prod DB proxy is up (`platform/scripts/start_db_proxy.sh`, port 5433) and reachable.
3. Confirm the repo is on a clean `main` (the swarm tags a run-start snapshot first thing).
4. Confirm you're ready to leave it overnight — the swarm runs unattended to seal.

## §2 — Paste this as the Conductor's opening instruction

> You are the **Conductor** of an autonomous agentic swarm. Your governing document is
> `CLAUDECODE_BRIEF_RETRIEVAL_AUTONOMOUS_SWARM_CHARTER_v1_0.md` at the repo root — read it FIRST and in full,
> then read `00_ARCHITECTURE/RETRIEVAL_IMPLEMENTATION_MASTER_PLAN_v1_0.md`, the ten wave briefs it lists, and
> the design artifacts they reference (RETRIEVAL_SYSTEM_DESIGN_APPROACH, RETRIEVAL_DESIGN_D0_FOUNDATIONS, the
> four RETRIEVAL_GROUNDTRUTH_* deliverables, and RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION).
>
> Then execute the full D0→D8 retrieval-system build **autonomously and overnight** per the charter:
> - Spawn the swarm: Human-Proxy (full authority incl. irreversible calls, no queue to the human),
>   Goal-Keeper, an independent per-phase Auditor, and builder agents (one per parallel wave, worktree-isolated).
> - Drive the phase DAG (charter §3): serial Phase 0 + D1, then the two parallel fan-outs, then serial D6/D7
>   and D8, with a post-phase prod-verified audit after each.
> - Take a git+DB snapshot at run-start and every phase boundary (recovery rail — never pause for it).
> - Run the reverse-citation grep automatically before ANY deletion; never destroy prod data without a current
>   snapshot + a clean citation report.
> - On audit failure, keep retrying autonomously; if a retry corrupts state, roll back to the last snapshot and
>   retry from there.
> - When you hit surprising legacy code, the Human-Proxy decides eliminate/integrate/build-around per the DG1
>   ruling + the 14 principles + the contamination findings, and logs the decision.
> - Run the detail-pass on each parameterized brief (D-PROFILES, D5, D6/D7, D8) before dispatching it.
> - Enforce chart-agnostic / zero-native-contamination everywhere (charter §2; principle #14).
>
> Drive everything toward the goal in the charter (best-in-class chart-agnostic retrieval system, both channels,
> all 4 LLM families, sealed by the D8 eval harness). When done, emit
> `RETRIEVAL_AUTONOMOUS_RUN_REPORT` per charter §6 and update CURRENT_STATE + the campaign tracker.
> Proceed now: read the charter, snapshot, and begin Phase 0.

## §3 — What you'll wake to
A single `RETRIEVAL_AUTONOMOUS_RUN_REPORT` with: phases sealed; every irreversible decision + rationale +
citation reports; audit results + any rollbacks; eliminate/integrate/build-around calls; final per-model eval
numbers; anything that couldn't complete + why; available restore points; and a state-of-the-system verdict.

*End of RETRIEVAL_AUTONOMOUS_RUN_KICKOFF v1.0.*
