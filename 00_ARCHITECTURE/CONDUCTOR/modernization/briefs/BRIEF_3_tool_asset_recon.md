---
status: COMPLETE
unit: 3.tool_asset_recon
wave: 3
title: Tool ↔ asset reconciliation — coverage, no redundancy, no orphans (sets G6)
stream: C
worktree: ../MadhavStreamC
blockedBy: [G3_contract, 2a]
sets_gate: G6_tool_coverage
on_red: rollback
file_fence: "touches lib/contract + lib/retrieve + manifest — serialize after 2a; not concurrent with 3.gateway / 3.dejudge"
---

## Context (self-contained)
The data assets changed shape in 2a (new T1 structural layer; UCN → computed digest; CDLM/CGM → deterministic
graphs; everything chart_id + ayanamsha_id keyed). Tools mapped to the OLD assets would silently read the wrong
thing. Re-map every tool to the new assets and prove the portfolio is complete + non-redundant + orphan-free
(MASTER_PLAN §15.2; native-raised). Done AFTER 2a (assets settled) + 2b (contract exists).

## Scope
- For every retrieval/MCP tool, set its `data_dependency` to the NEW asset(s) it serves and confirm it reads the
  correct chart_id + ayanamsha_role (canonical Parashari/MSR; kp for KP tools).
- Audit: (a) **coverage** — every live asset (incl. T1 structural facts, UCN-digest, deterministic CDLM/CGM) has
  ≥1 appropriate tool; (b) **no redundancy** — no two tools serve the same asset+intent (collapse per §3.3);
  (c) **no orphans** — no tool reads a retired/changed asset shape; (d) **LLM-client fit** — surfaced set matches
  §13 (gateway + bundles + real schemas).

## Acceptance criteria (all automated)
1. **G6 gate:** `npx vitest run platform/src/lib/contract/__tests__/tool_asset_coverage.test.ts` — `data_coverage`
   reports 100% asset coverage + 0 orphaned tools + 0 redundant duplicates.
2. Every ayanamsha-dependent tool declares its `ayanamsha_role`; none reads across roles.
3. `data_coverage` / `tool_health` report all assets functional post-2a.

## must_not_touch
`chart_facts`/`l25_*` (2a owns the data), `platform/src/app/**`, `platform/python-sidecar/**`,
`platform/src/lib/pipelines/**` (gateway).

## Commit cadence / rollback
Commits: (1) data_dependency re-map across tools, (2) coverage/redundancy audit + G6 test. Rollback = revert.
