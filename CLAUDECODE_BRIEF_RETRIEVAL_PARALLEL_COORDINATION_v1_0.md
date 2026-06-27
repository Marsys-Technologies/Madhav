---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_PARALLEL_COORDINATION
version: 1.0
status: READY-FOR-EXECUTION — governs all parallel waves; read before spawning any parallel agent
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — coordination governance for parallel multi-agent retrieval build
parent_plan: RETRIEVAL_IMPLEMENTATION_MASTER_PLAN_v1_0 (this brief operationalizes its parallelism)
applies_to:
  - FAN-OUT 1 (skeleton): D2 router ∥ D3 grounding spine ∥ D4 graph
  - FAN-OUT 2 (model+assets): D-PROFILES ∥ D5 fan-out ∥ D5's layer sub-waves (L0/L1/L2…)
relevant_memory (the scars this brief prevents):
  - feedback_ac_must_verify_target_environment (worktree-complete ≠ prod; ACs must verify against prod)
  - feedback_two_stream_branch_policy (branch isolation per stream; cherry-pick to recover contamination)
  - feedback_destructive_brief_reverse_citation_gate (no deletion on faith)
  - feedback_degenerate_distribution_guard (distribution checks, not just per-row)
hard_constraints: the THREE GATES in §2 are non-negotiable for any parallel work
---

# CLAUDE CODE BRIEF — PARALLEL-BUILD COORDINATION

> Parallel multi-agent build compresses the campaign, but it is exactly where this project has been bitten:
> worktree-complete-but-not-prod, merge contamination, incompatible assumptions across branches. This brief
> makes parallel safe BY CONSTRUCTION. **Read it before spawning any parallel agent.** If any of the three
> gates cannot hold, do NOT parallelize that wave — run it serially.

## §1 — Precondition (absolute)

**D1 must be FULLY FROZEN AND MERGED TO MAIN before any parallel wave starts.** The RetrievalSurface contract
+ the chart-agnostic CI gate are the shared interface every parallel wave conforms to. Parallelizing before D1
is merged is not speed — it is the contract-drift / multiple-systems bug with more agents. No exceptions.
(Phase 0 + D1 are serial; parallelism begins only at the fan-out points.)

## §2 — The three gates (non-negotiable)

**GATE A — No-shared-file rule (escalate, don't edit).** Each parallel wave owns ONLY its own NEW files. The
shared surfaces — `registry/types.ts` (the frozen contract) and the central `registry/index.ts` (capability
registration) — are OFF LIMITS to parallel agents. A wave registers its capabilities through an
append-only/per-wave registration file, not by editing the central index. **If a wave believes it needs a
contract change → it STOPS and escalates to the native** (per DG3 freeze discipline) — it does not edit the
contract in its branch. This is what prevents incompatible parallel extensions of the same surface.

**GATE B — Post-MERGE prod-verification (not worktree-complete).** A wave is NOT "done" when its worktree/branch
tests pass. Every wave's acceptance criteria are tagged `[verify-against: prod]`. After a branch merges to main,
a mandatory prod-verification step re-checks the wave's headline outcomes against the live (localhost→prod)
environment. Worktree-green is necessary, not sufficient. Divergence triggers a delta-fix session, not a
"complete" claim. (This is the specific lesson from the Brahma worktree-complete-only incident.)

**GATE C — Reverse-citation on any removal.** Any deletion/retirement in a parallel branch (e.g. D5 collapsing
sibling tools, D6/D7 remediating old MCP tools) greps the live codebase for active citations of every target
first, reclassifies anything still cited as keep-or-repoint, and ships the citation report in the PR. No
deletion on faith — and especially not in a branch where the auditor might check the wrong tree.

## §3 — Branch + worktree isolation

- One branch (and worktree, per the repo's worktree workflow) PER WAVE: `feature/retrieval-d2-router`,
  `…-d3-grounding`, `…-d4-graph`, `…-dprofiles`, `…-d5-l0`, `…-d5-l1`, `…-d5-l2`, etc.
- A wave NEVER modifies another wave's branch (per two-stream branch policy; recover contamination by
  cherry-pick to main, never cross-branch edits).
- Each branch rebases on the latest main (which includes frozen D1) before starting.

## §4 — Merge order + integration smoke

- **Fan-out 1 (D2/D3/D4):** independent new files; merge in any order. After ALL THREE are merged, run an
  **integration smoke**: a query that exercises router→grounding→graph end-to-end on TWO distinct charts,
  confirming the interfaces agreed (no incompatible result-shape assumptions; no native bleed). Only then is
  fan-out 1 "integrated."
- **Fan-out 2 (D-PROFILES ∥ D5 ∥ layer sub-waves):** D-PROFILES and D5 merge independently; D5's layer
  sub-waves (L0/L1/L2…) merge as each completes. After D5 sub-waves merge, run a **roster-completeness smoke**
  (every asset reachable through some tool path; F1 dedup gate; chart-agnostic gate). D-PROFILES merges with the
  MARO core intact.
- Each merge passes the standard per-PR gates: chart-agnostic CI gate + parity_check + drift/schema validators.

## §5 — What stays SERIAL (do not parallelize)

- Phase 0 (runtime + cleanup) and D1 — the serial spine.
- D6/D7 — composes the D5 roster; needs it to exist.
- D8 — evaluates the assembled system; last by definition.
- Within a single wave, anything that edits a shared file (forced serial by Gate A).

## §6 — Per-wave agent kickoff (the pattern each parallel agent follows)

1. Rebase branch on main (incl. frozen D1).
2. Read: this coordination brief + the wave's own brief + the wave's prereq artifacts.
3. Build ONLY new files for the wave; register via the per-wave registration file (Gate A).
4. Worktree tests green + chart-agnostic gate green.
5. PR with: the wave's deliverable, reverse-citation report if anything was removed (Gate C),
   and ACs tagged `[verify-against: prod]`.
6. After merge: run the prod-verification step (Gate B). Report result to Cowork.

## §7 — Acceptance criteria (for the parallel campaign as a whole)

- D1 frozen+merged before any parallel agent spawned.
- Every parallel wave: own branch/worktree, no shared-file edits, escalate-don't-edit on the contract.
- Every wave: prod-verified after merge (not worktree-only); divergence handled as a delta-fix.
- Every removal: reverse-citation report in PR.
- Integration smoke after each fan-out; roster-completeness smoke after D5.
- Zero contract drift; zero native contamination; zero cross-branch edits.

*End of CLAUDECODE_BRIEF_RETRIEVAL_PARALLEL_COORDINATION v1.0 — read before any parallel agent.*
