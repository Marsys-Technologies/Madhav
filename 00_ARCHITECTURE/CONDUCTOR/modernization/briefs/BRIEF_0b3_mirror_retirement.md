---
status: COMPLETE
unit: 0b.3
wave: 0b
title: Retire the Gemini mirror-discipline governance (one atomic PR, 5 surfaces)
stream: C
worktree: ../MadhavStreamC
blockedBy: []
on_red: rollback
---

## Context (self-contained)
Native decision 2026-05-27: the Gemini/multi-agent collaboration is inactive; retire the mirror discipline.
Audit MUST-RESOLVE #6: the retirement cascades across FIVE surfaces and MUST land as ONE atomic change or
`drift_detector.py` fails on a half-state. (Lean-transform governance — remove overhead that no longer protects.)

## Scope (all in one commit)
- `CLAUDE.md`: remove §C item 11 (mirror reads) + the §K mirror-discipline clauses; drop mirror references.
- `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`: remove §K.3 mirror arbitration + the
  `DIS.class.mirror_desync` class.
- `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md`: remove §2 mirror-pair inventory (MP.1–MP.8).
- `00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md`: close ND.1 (Mirror Discipline) as RETIRED.
- Delete `.geminirules`, `.gemini/project_state.md`, and `platform/scripts/governance/mirror_enforcer.py`
  (+ remove any CI/script invocation of mirror_enforcer).

## Acceptance criteria (all automated)
1. `python platform/scripts/governance/drift_detector.py` exits 0 (no dangling mirror references anywhere).
2. `grep -rn "mirror_enforcer\|DIS.class.mirror_desync\|MP\.[1-8]\|\.geminirules" --include=*.md --include=*.py .`
   returns only historical/archive hits (none in live governance/CI).
3. CI still green (no workflow invokes the deleted enforcer).

## must_not_touch
`platform/src/**`, `platform-mcp/src/**`, `platform/migrations/**`.

## Commit cadence / rollback
EXACTLY ONE commit touching all five surfaces (atomicity is the requirement). Rollback = revert the single
commit restores the prior governance state cleanly.
