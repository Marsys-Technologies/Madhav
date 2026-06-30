---
canonical_id: CLAUDECODE_BRIEF_MCP_TEST_TRIAGE
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-30
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — test-hygiene triage (33 platform-mcp Vitest failures, 3 categories)
priority: medium — test-hygiene, NOT product defects; restores platform-mcp to green so the signal is clean
context: There is NO jest/Babel issue (the project is Vitest). Platform is all-green. platform-mcp has 33
  failures in 3 categories, none of which are retrieval-engine defects. This brief triages them ON MERIT —
  delete dead, fix harness, decide the stale assertion — NOT "make green."
prereq: the Vitest diagnosis report (categories A/B/C with exact files)
hard_constraint: reverse-citation gate before deleting any test file; decide each on merit, do not mass-delete.
---

# CLAUDE CODE BRIEF — platform-mcp TEST TRIAGE (33 failures, 3 categories)

> The Vitest signal is healthy. platform-mcp's 33 failures are test-hygiene debris from the MCPT v3.2 teardown,
> a harness mock-wiring issue, and one stale governance assertion. Resolve each category on merit so
> platform-mcp returns to green and the test signal is clean. None of these are retrieval-engine bugs.

## §A — Category A: stale test files importing removed tools (9 files, "0 tests collected")
These test files import `src/tools/*` modules deleted in the MCPT v3.2 teardown (chart_summary, catalog,
data_coverage, tool_health, get_cgm_subgraph, kala_period_snapshot, query_chart_facts, _envelope,
description_builder). They can't even be collected.
- **Action:** for EACH file, run the reverse-citation gate — confirm the imported source module is genuinely
  gone (not moved/renamed) AND the test's coverage isn't uniquely valuable. If the tool is truly retired →
  **delete the test file** (dead code from the teardown). If the tool was MOVED/renamed → repoint the import
  instead of deleting. Produce a one-line disposition per file + a citation note in the PR.
- Files: chart_summary.test.ts, coverage_handler.test.ts, bodha_graph_gate1.test.ts, kala_period_snapshot.test.ts,
  query_chart_facts_batching.test.ts, _envelope.test.ts, tool_descriptions.test.ts,
  data_coverage.integration.test.ts, accuracy/cross_scenario.test.ts.

## §B — Category B: mimamsa_lel_intake fetch mock not intercepting (20 failures)
`mockFetch.mock.calls[0]` is undefined — the vi fetch mock never fires because the tool's `lel_query` calls
fetch via a path the global mock doesn't intercept (likely a non-global/imported fetch).
- **Action:** diagnose the tool's actual fetch import path; either (a) fix the TEST to mock the path the tool
  actually uses (preferred — it's a harness wiring bug), or (b) if the tool uses an inconsistent fetch import,
  normalize it to the standard path so it's mockable + consistent with the other tools. Do NOT change the
  tool's behavior to pass a test. Confirm the 20 failures clear.

## §C — Category C: stale phala_muhurta FORENSIC-grounding assertion (1 failure)
`description references FORENSIC grounding` expects `MUHURTA_FINDER_DESCRIPTION` to contain `'FORENSIC'`; it
doesn't. **Native decision needed — DEFAULT (pending native confirm): REMOVE the assertion as stale governance.**
Rationale: the description is already clean + purpose-focused; forcing a "FORENSIC" keyword into an LLM-visible
description is a governance artifact in the wrong place (it would bias/clutter the model-facing text). 
- **Action:** unless the native rules otherwise, **delete the stale assertion.** If the native instead wants
  the FORENSIC grounding surfaced, enrich the description with a brief, natural grounding reference (not a bare
  keyword) and keep the assertion. Do not bare-keyword-stuff to pass.

## §D — Acceptance
- platform-mcp returns to green (or only intentionally-skipped remain); report the new pass/fail.
- Category A: each file deleted-or-repointed with a disposition note + citation; nothing uniquely valuable lost.
- Category B: 20 failures cleared by fixing the harness/import (no tool behavior change).
- Category C: resolved per native decision (default: assertion removed); description stays clean + chart-agnostic.
- No assertion massaged to pass; no product/app logic changed; reverse-citation report for deletions.

*End of CLAUDECODE_BRIEF_MCP_TEST_TRIAGE v1.0 — triage on merit; the retrieval engine signal is already green.*
