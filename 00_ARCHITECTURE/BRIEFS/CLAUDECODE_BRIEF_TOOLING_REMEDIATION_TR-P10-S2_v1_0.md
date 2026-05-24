---
artifact: CLAUDECODE_BRIEF_TOOLING_REMEDIATION_TR-P10-S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Conductor (2026-05-25)
session_id: TR-P10-S2
---

# CLAUDECODE_BRIEF — TR-P10-S2
## Phase 10.6–10.10: PLANNER_PROMPT next-version + MP.1 mirror to .geminirules

## §0 — Start

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
git status  # must be clean
```

## §1 — Scope

may_touch: 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md, .geminirules
must_not_touch: platform/**, platform-mcp/**, python-sidecar/**, 025_HOLISTIC_SYNTHESIS/**, 01_FACTS_LAYER/**, CLAUDE.md, 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/**

**This session touches ONLY the PLANNER_PROMPT document and .geminirules. No application code.**

## §2 — Task

First read `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` to see the current version (should be 2.5 after TR-P10-S1) and the section structure. Then add 5 more R-rules and bump to the next minor version.

### R-CS.2 — Pre-compute chart summary

```
R-CS.2 — Pre-compute chart summary
At session start, after the R-TD.1 diagnostic, call chart_summary() to cache the overview.
Reference this cached summary throughout the session rather than re-calling. Avoids the
0-rows bug exposing itself mid-reading (flag it if chart_summary returns 0 — do not silently skip).
```

### R-CGM.1 — CGM + vector proactive use

```
R-CGM.1 — CGM + vector proactive use
For every signal with confidence ≥ 0.7, walk get_cgm_subgraph() 2 hops to find connected
signals. For every domain-boundary question, call vector_search() with the domain as the query.
Do not reserve these tools for explicit user requests — they are part of the default B.11 read.
```

### R-TRI.1 — Triangulate before asserting

```
R-TRI.1 — Triangulate before asserting
Every substantive claim follows the triangulation chain: MSR signal → chart_facts confirmation
→ ephemeris timing. A claim that skips any leg is annotated
[PARTIAL-TRIANGULATION: missing <leg>].
```

### R-PER.1 — Mark permanence

```
R-PER.1 — Mark permanence
Every clause in a reading is explicitly tagged:
  (permanent — natal disposition)
  (dasha-tied — active for <period>)
  (transit-tied — window <date_from> to <date_to>)
Untagged clauses are governance violations equivalent to a B.1 layer collapse.
```

### R-SCH.1 — Read schemas before use

```
R-SCH.1 — Read schemas before use
Before the first invocation of any tool in a session, read its full schema description.
If the tool is new (added in a phase post-P0), call list_assets() to confirm availability.
```

### Version bump + changelog

Bump from current version (2.5) to next minor (2.6). Add changelog entry for v2.6.

### MP.1 mirror to .geminirules

Read the current `.geminirules`. Add a `TOOLING_REMEDIATION_RULES` section with adapted-parity versions of all 10 methodology rules (R-TD.1 through R-SCH.1) in Gemini idiom. Tag the section:
```
# TOOLING_REMEDIATION_RULES — Added TR-P10-S2 (2026-05-25), mirror pair MP.1
```

The mirror is semantic, not byte-identical. Adapt language for Gemini's working style while preserving intent. Keep the section clearly delimited with a comment header and footer.

### Commit

```bash
git add 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md .geminirules
git commit -m "feat(TR-P10-S2): PLANNER_PROMPT v2.6 — R-CS.2, R-CGM.1, R-TRI.1, R-PER.1, R-SCH.1 + MP.1 mirror"
```

Push is handled by the conductor after FINAL_SUMMARY (wave 1 push boundary).

## §3 — Acceptance criteria

| ID | Criterion |
|---|---|
| AC.1 | `PLANNER_PROMPT_v2_0.md` contains `R-CGM` or `cgm_subgraph` |
| AC.2 | `PLANNER_PROMPT_v2_0.md` version bumped (one minor above 2.5) |
| AC.3 | `.geminirules` contains `tooling.remediation` or `R-TD` or `session_start_diagnostic` |
| AC.4 | `.geminirules` contains `TOOLING_REMEDIATION_RULES` section header |
| AC.5 | Commit exists with the correct message |

## §4 — Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix && \
grep -q 'R-CGM\|cgm_subgraph' 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md && \
grep -q 'tooling.remediation\|R-TD\|session_start_diagnostic' .geminirules && \
echo "GATE_PASS"
```

## §5 — FINAL_SUMMARY

```
---FINAL_SUMMARY---
session_id: TR-P10-S2
status: PASS | HALT_NEEDS_HUMAN
tests_passed: 0
files_changed: [00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md, .geminirules]
commit_sha: <git log --format=%H -1>
notes_for_orchestrator: <section where rules were placed, .geminirules section details>
---
```
