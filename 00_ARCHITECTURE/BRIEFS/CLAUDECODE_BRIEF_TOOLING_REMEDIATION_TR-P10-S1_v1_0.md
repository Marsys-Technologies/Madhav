---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P10-S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Conductor (2026-05-25)
session_id: TR-P10-S1
---

# CLAUDECODE_BRIEF — TR-P10-S1
## Phase 10.1–10.5: PLANNER_PROMPT v2.1 — R-TD.1, R-NDE.1, R-LP.1, R-FD.1, R-CS.1

## §0 — Start

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean
```

## §1 — Scope

may_touch: 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md
must_not_touch: platform/**, platform-mcp/**, python-sidecar/**, 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, .geminirules, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**

**This session touches ONLY the PLANNER_PROMPT document. No application code.**

## §2 — Task

Read `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` fully first. Find the existing R-rule naming convention and the section structure (Parts I–IV or equivalent). Then add the 5 new R-rules below.

### R-TD.1 — Session-start diagnostic

```
R-TD.1 — Session-start diagnostic
Before any substantive chart reading, call data_coverage({tier: 'super_admin'}) and
tool_health({days: 30}). If either tool errors, log with flag_disagreement and proceed
noting the gap. Do not skip this step even in short sessions.
```

### R-NDE.1 — No date estimation

```
R-NDE.1 — No date estimation
All future-dated claims (e.g. 'Jupiter will transit X around mid-2027') MUST be sourced
from query_ephemeris({date_range:{from:...,to:...}}) or query_transit_event(). Never
extrapolate from mean motion. Mark any date claim that lacks an ephemeris source as
[DATE_UNVERIFIED].
```

### R-LP.1 — log_prediction mandatory

```
R-LP.1 — log_prediction mandatory
Every substantive predictive claim — defined as a claim about a future event, its timing,
or its quality — MUST be followed immediately by a log_prediction() call with:
confidence (0.0–1.0), horizon (months), falsifier (what observable outcome would refute it).
Predictions without log_prediction() violate B.3.
```

### R-FD.1 — flag_disagreement on broken tools

```
R-FD.1 — flag_disagreement on broken tools
When a tool returns an error or suspicious output (0 rows, silent coverage), call
flag_disagreement() to log it formally before proceeding with a workaround. Silent
workarounds are governance violations.
```

### R-CS.1 — Cross-school before high-confidence

```
R-CS.1 — Cross-school before high-confidence
Before asserting any predictive claim with confidence ≥ 0.75, call cross_school_lookup()
for that claim. If cross_school_lookup returns silent or data_empty for all schools,
lower the stated confidence to ≤ 0.65 and note the gap explicitly.
[Activates after Phase 2 ships a populated school_convergence_index; until then,
annotate claims as [PRE-PHASE-2].]
```

### Version bump + changelog

1. Update the frontmatter: `version: 2.0` → `version: 2.1`
2. Add a changelog entry:
   ```
   ## Changelog
   ### v2.1 — 2026-05-25 (TR-P10-S1)
   Added R-TD.1 (session-start diagnostic), R-NDE.1 (no date estimation),
   R-LP.1 (log_prediction mandatory), R-FD.1 (flag_disagreement on broken tools),
   R-CS.1 (cross-school before high-confidence). Five methodology rules from the
   MARSYS-JIS Tooling Remediation Phase 10.1–10.5.
   ```
3. Place the 5 new R-rules in the appropriate methodology section (Part IV or wherever existing R-rules live).

### Commit

```bash
git add 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md
git commit -m "feat(TR-P10-S1): PLANNER_PROMPT v2.1 — R-TD.1, R-NDE.1, R-LP.1, R-FD.1, R-CS.1"
```

## §3 — Acceptance criteria

| ID | Criterion |
|---|---|
| AC.1 | `PLANNER_PROMPT_v2_0.md` frontmatter version is `2.1` |
| AC.2 | File contains `R-TD.1` and `session_start_diagnostic` (or `session-start diagnostic`) |
| AC.3 | File contains `R-NDE.1` and `no_date_estimation` (or `no date estimation`) |
| AC.4 | File contains `R-LP.1`, `R-FD.1`, `R-CS.1` |
| AC.5 | Changelog entry for v2.1 present |

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
grep -q 'R-TD.1\|session_start_diagnostic' 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md && \
grep -q 'R-NDE\|no_date_estimation' 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md && \
echo "GATE_PASS"
```

## §5 — FINAL_SUMMARY

```
---FINAL_SUMMARY---
session_id: TR-P10-S1
status: PASS | HALT_NEEDS_HUMAN
tests_passed: 0  # no code tests — governance doc only
files_changed: [00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md]
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <section where rules were placed; any structural observations>
---
```
