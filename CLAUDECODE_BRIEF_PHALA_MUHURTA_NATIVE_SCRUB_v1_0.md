---
canonical_id: CLAUDECODE_BRIEF_PHALA_MUHURTA_NATIVE_SCRUB
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-30
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — native-contamination fix (mis-triaged test + LLM-visible description)
priority: correctness (principle #14 / chart-agnostic) — small but NOT cosmetic
parent: RETRIEVAL_ENGINE_SEAL_RECORD_v1_0 §3 item 2 (correction)
hard_constraint: do NOT "make the test pass" — that re-embeds the native name. Scrub + invert.
---

# CLAUDE CODE BRIEF — PHALA_MUHURTA NATIVE-NAME SCRUB

> A test pins native contamination green: `platform-mcp/src/__tests__/phala_muhurta.test.ts:243-245` asserts
> `MUHURTA_FINDER_DESCRIPTION` MUST CONTAIN `'Abhisek Mohanty'`. The description is LLM-visible — embedding the
> native name biases every connecting model toward the native chart, the exact contamination class principle
> #14 forbids. The R-series purged this from `kala_timeline`; this stray instance was left. Fix it the RIGHT
> way (scrub + invert), not by making the assertion pass.

## §1 — Scrub the description (the actual contamination)
- Find `MUHURTA_FINDER_DESCRIPTION` (the muhurta_finder tool). If it contains `Abhisek Mohanty` (or the native
  birth details / native chart_id), **remove the native reference** and replace any example with a neutral
  placeholder (`<chart_uuid>`), per the chart-agnostic contract. The description must teach the tool's purpose
  without naming any person/chart.

## §2 — Invert the test (assert ABSENCE, don't require presence)
- Replace the `it('description references native chart ID for Abhisek Mohanty', …) → toContain('Abhisek
  Mohanty')` test with an assertion that the description does **NOT** contain the native name / native chart_id:
  `expect(MUHURTA_FINDER_DESCRIPTION).not.toContain('Abhisek Mohanty')` (and not the native UUID). Keep the
  legitimate behavioral assertions (e.g. schema rejects missing chart_id).

## §3 — Sweep for siblings (don't fix one and miss ten)
- Grep ALL MCP tool descriptions + tests for the native name + native chart_id (`Abhisek`, `Mohanty`,
  `482012f1`) — `platform-mcp/src` and `platform/src/lib/retrieval`. Scrub any other LLM-visible description
  that embeds them; invert any other "must contain native" test.

## §4 — Gate coverage (prevent recurrence)
- Confirm the chart-agnostic CI gate already scans MCP tool descriptions for native identifiers (it was
  extended to `platform-mcp/src/tools/` in ISSUE-7). If `MUHURTA_FINDER_DESCRIPTION` lives somewhere the gate
  doesn't scan, extend the gate to cover it, so a native name in any description fails CI going forward.

## §5 — Acceptance
- `MUHURTA_FINDER_DESCRIPTION` (and any sibling) contains no native name / native chart_id.
- The test asserts ABSENCE, not presence; it passes for the right reason.
- The chart-agnostic gate covers tool descriptions and would catch a re-introduction.
- No behavioral change to muhurta_finder beyond the description text.
- Reverse-citation not needed (no deletion of code paths) — but note the change in the PR.

*End of CLAUDECODE_BRIEF_PHALA_MUHURTA_NATIVE_SCRUB v1.0 — fix the contamination, don't make it green.*
