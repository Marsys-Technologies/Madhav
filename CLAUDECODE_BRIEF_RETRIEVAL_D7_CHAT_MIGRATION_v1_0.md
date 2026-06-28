---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D7_CHAT_MIGRATION
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-28
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — the scoped chat-channel migration the autonomous swarm asked for
session_type: implementation — migrate /api/chat/consult off lib/retrieve onto the sealed registry
parent: RETRIEVAL_AUTONOMOUS_RUN_OUTCOME_v1_0 (ISSUE-1, BLOCKING) ; CLAUDECODE_BRIEF_RETRIEVAL_D1_CONTRACT §4
why_this_exists: the overnight swarm correctly REFUSED to migrate the chat channel mid-run (40+ callers of
  lib/retrieve/msr_sql across chat route + pipelines + gateway + contract + MCP primitives + tests). This is
  the scoped brief it requested. Treat as destructive + high-blast-radius — strictest discipline.
prereq_reading:
  - RETRIEVAL_AUTONOMOUS_RUN_OUTCOME_v1_0.md (what's sealed; ISSUE-1)
  - RETRIEVAL_DESIGN_D0_FOUNDATIONS_v1_0.md (DG1 convergence ruling: build on lib/retrieval, retire lib/retrieve)
  - RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md (the two/three-systems map; §H contamination)
hard_constraints:
  - reverse-citation gate before ANY removal (feedback_destructive_brief_reverse_citation_gate)
  - per-caller repoint with a parity test vs CURRENT behavior BEFORE retiring anything
  - chart-agnostic (#14) preserved; tier stripped during migration; no native contamination introduced
  - prod-verify after merge (feedback_ac_must_verify_target_environment) — not worktree-complete
acceptance_criteria: see §5
---

# CLAUDE CODE BRIEF — D7 CHAT-CHANNEL MIGRATION

> Migrate the chat channel (`/api/chat/consult` + its ~40-file `lib/retrieve`/`msr_sql` surface) onto the
> sealed D1–D8 registry, so the chat UI gets the same chart-agnostic, grounded, de-duplicated retrieval the
> MCP channel already has — eliminating the last instance of the two-systems split (DG1). This is the highest-
> blast-radius change in the campaign; the swarm wisely deferred it. Do it scoped, per-caller, parity-tested.

## §0 — Embedded decisions (RULED)
- DG1: build on `lib/retrieval`; migrate the valuable `lib/retrieve` query logic (esp. `msr_sql` filters) into
  registry capabilities (chart_id required, tier stripped), repoint callers, THEN retire `lib/retrieve` + fold
  `mcp/primitives_registry`.
- The MCP channel is already sealed on the registry — the goal is for chat to consume the SAME registry source,
  making MCP→chat drift impossible (single query logic).

## §1 — Caller inventory (Step 0 — do first, do not skip)
Produce the authoritative caller map: grep the live tree for `lib/retrieve`, `msr_sql`, and the
`mcp/primitives_registry` bridge. Classify each of the ~40 references as: (a) chat-path runtime (must repoint),
(b) other runtime (pipelines/gateway/contract — repoint or confirm registry-equivalent exists), (c) test
(update to the registry path), (d) already-registry (no-op). This map is the migration's work-list and the
reverse-citation baseline.

## §2 — Port query logic → registry capabilities
For each piece of `lib/retrieve` logic the chat path needs (signal filtering via `msr_sql`, chart_facts query,
remedy tools, classical disclosure filter), ensure an equivalent registry capability exists (D1–D5 likely built
most); where a gap exists, add a contract-conformant capability (chart_id required, tier stripped, chart-agnostic
gate green). Do NOT carry `audience_tier` forward.

## §3 — Repoint callers, per-caller, parity-tested
For EACH caller (chat route first, then pipelines/gateway/contract): repoint to the registry capability, and
add/run a **parity test** comparing the new path's output to the current `lib/retrieve` output for representative
queries on ≥2 distinct charts (never native-only). Repoint only when parity holds (or the difference is an
intended improvement, documented). Tests get updated to the registry path.

## §4 — Retire legacy (only after all callers repointed) — reverse-citation gate
Once every caller is repointed + parity-green: run the reverse-citation grep for `lib/retrieve` +
`mcp/primitives_registry` (zero live citations expected now); produce the citation report; retire them. No
deletion lands without the report. Strip the residual `audience_tier` in `lib/retrieve/types.ts` as part of this.

## §5 — Acceptance criteria
- Caller map produced; every chat-path + runtime caller repointed to the registry; tests updated.
- Per-caller parity tests green (≥2 charts, never native-only); intended differences documented.
- `lib/retrieve` + `mcp/primitives_registry` retired with a clean reverse-citation report in the PR; zero `audience_tier` remains.
- Chat channel consumes the SAME registry source as MCP; a drift test proves identical filter behavior both channels.
- chart-agnostic gate + parity_check + drift/schema validators green; prod-verified after merge (not worktree-only).
- No native contamination introduced; no caller left on the legacy path.

## §6 — Fold-in: ISSUE-4 faithfulness eval (optional, recommended here)
Once the chat path is live on the registry, run the existing D8 faithfulness/groundedness harness against the
populated prod DB with a judge model (Gemini Pro primary per policy; ≥2 charts). This closes the deferred
answer-quality eval end-to-end. Can be this session's tail or an immediate follow-on.

## §7 — Close
Set `status: COMPLETE` when all callers are migrated, legacy retired with citation report, both channels share
one source, and (if folded in) faithfulness eval has run. Report back so the run-outcome record + campaign
tracker update to "chat channel SEALED" — retrieval system fully complete end-to-end.

*End of CLAUDECODE_BRIEF_RETRIEVAL_D7_CHAT_MIGRATION v1.0.*
