---
status: COMPLETE
unit: 3.dejudge
wave: 3
title: De-judgment — remove query-time scoring from the retrieval tools
stream: C
worktree: ../MadhavStreamC
blockedBy: [G3_contract, 2a]
on_red: rollback
file_fence: "touches lib/retrieve/msr_sql.ts + MCP query_signals.ts — serialize after 2a; not concurrent with 3.gateway / 3.tool_asset_recon"
---

## Context (self-contained)
Clean data through a tool that still applies a 0.6 floor is still dropped data (audit §6-A). Now that 2a built
the L2.5 **computed coefficient** (3 columns), remove the query-time judgment so the tool returns everything
and the pick lives in the data (`computed_salience`) + serve-time panel.

## Scope
- Strip from `platform/src/lib/retrieve/msr_sql.ts`: `DEFAULT_CONFIDENCE_FLOOR` (line ~20),
  `FINANCE_WEALTH_CONFIDENCE_FLOOR` (~24), `PANCHA_MP_CLIQUE` (~33), `LL1_PRODUCTION_WEIGHTS` (~44) and their
  application. Same for the MCP-side `platform-mcp/src/tools/query_signals.ts` floors/clique.
- Tools now return the **never-dropped** signal set + the computed coefficient columns; ranking/salience is the
  `computed_salience` column (2a) + serve-time panel — NOT a query-time floor.

## Acceptance criteria (all automated)
1. Grep: zero `CONFIDENCE_FLOOR|PANCHA_MP_CLIQUE|LL1_PRODUCTION_WEIGHTS` in `lib/retrieve` + MCP tools.
2. `msr_sql` / `query_signals` return all matching signals with coefficient columns (no silent drop).
3. **Golden-transcript with re-baseline note:** previously-floored weak signals now surface — this is INTENDED;
   record it in CONDUCTOR_LOG as a re-baseline, not a regression. Don't run `answer:eval` per-PR (native discipline).
4. Both channels (portal + MCP) de-judged identically.

## must_not_touch
`chart_facts`/`l25_*` (2a), `platform/src/lib/pipelines/**` (gateway), `platform/src/app/**`, `platform/python-sidecar/**`.

## Commit cadence / rollback
Commits: (1) portal msr_sql de-judge, (2) MCP query_signals de-judge. Rollback = revert (floors restored).
