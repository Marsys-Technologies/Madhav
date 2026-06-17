---
brief_id: M2_G1_REDTEAM_SMOKE
karn_session_name: KARN-W8-R1-REDTEAM-SMOKE
wave: 8
stream: G
status: READY
authored_by: Claude (Cowork) 2026-04-30 — Wave 8 open
authored_for: Claude Code execution (autonomous, long-running)
session_type: validation (mandatory red-team pass + thin UI smoke before M2 close)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md §IS.8
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: |
    W7 all COMPLETE (W7-R1 audits, W7-R2 manifest, W7-R3 eval harness).
    KARN-W6-POSTFIX: Audit 1 PASS.
    Per MACRO_PLAN §IS.8: "A macro-phase does not close without its red-team."
    This session is the mandatory red-team pass before W8-R2 can author the
    M2 CLOSE artifact.
  blocks: KARN-W8-R2-M2-CLOSE (cannot close M2 without this session's verdict)
sequence_note: |
  W8 is SEQUENTIAL (not parallel):
    W8-R1 (this brief) → native reviews verdict → W8-R2
  W8-R2 is blocked until this session produces a verdict of PASS or
  PASS_WITH_FIXES (fixes applied). FAIL halts the wave and requires
  native decision before proceeding.
estimated_time: 2 days single Claude Code session
---

# CLAUDECODE_BRIEF_M2_G1_REDTEAM_SMOKE
## Wave 8-R1 — Mandatory M2 Red-Team Pass + Thin UI Smoke

---

## §0 — Pre-flight (read before any tool call)

```
ROOT = ~/Vibe-Coding/Apps/Madhav
PLATFORM = ~/Vibe-Coding/Apps/Madhav/platform
```

Read in order before any action:
1. This brief (complete)
2. `00_ARCHITECTURE/MACRO_PLAN_v2_0.md §IS.8` — red-team cadence mandate
3. `00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` — last 200 lines (W6+W7 state)
4. `00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md` — audit outcomes
5. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — manifest v1.7 state
6. `platform/src/lib/config/feature_flags.ts` — active flags
7. `platform/src/app/api/chat/consume/route.ts` — pipeline stages (for smoke)

Emit session-open handshake per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`.

---

## §1 — Mandate

Per `MACRO_PLAN_v2_0.md §IS.8`: every macro-phase close requires a red-team
pass before the SESSION_LOG is sealed. M2 is closing in W8-R2. This session
performs the IS.8-mandated red-team.

A red-team pass has PASS / PASS_WITH_FIXES / FAIL verdicts:
- **PASS:** No material flaws found. W8-R2 may proceed.
- **PASS_WITH_FIXES:** Flaws found and repaired in this session. W8-R2 may proceed.
- **FAIL:** Material unfixable flaw. Halt — report to native before W8-R2.

---

## §2 — Scope

```
MAY TOUCH (for fixes only — do not pre-emptively edit):
  platform/src/**                          (if red-team uncovers a code defect)
  00_ARCHITECTURE/BRIEFS/**                (append finding notes only)
  025_HOLISTIC_SYNTHESIS/**                (if red-team finds a corpus defect)
  platform/scripts/eval/fixtures.json      (if a fixture is factually wrong)

CREATES:
  00_ARCHITECTURE/EVAL/REDTEAM_M2_v1_0.md (red-team report artifact)

MUST NOT TOUCH:
  00_ARCHITECTURE/CAPABILITY_MANIFEST.json (W7-R2 is sealed — no manifest edits)
  platform/migrations/**                   (no schema changes)
  Any W7-R1 DB work (l25_cgm_nodes)       (already verified; no re-backfill)
```

---

## §3 — Red-team axes (execute all)

For each axis: state the question, investigate, record finding (PASS / FINDING),
and if FINDING: apply fix or escalate to FAIL.

### Axis RT.1 — Layer separation (B.1)
**Question:** Does any L2.5+ artifact assert a chart fact that is not traceable
to a specific FORENSIC ID? Sample 10 MSR signals at random; check their
`v6_ids_consumed` fields against FORENSIC_ASTROLOGICAL_DATA_v8_0.md.
Target: 100% of sampled signals have valid FORENSIC IDs (given overall 98.99%).

### Axis RT.2 — Derivation ledger (B.3)
**Question:** Does any retrieval tool response produced by the pipeline include
an interpretive claim without a signal or fact citation? Read the consume
route's synthesize step prompt. Verify the synthesis system prompt requires
the model to cite source signals.
Check: `platform/src/app/api/chat/consume/route.ts` — synthesize step.
Check: `platform/src/lib/claude/consume-tools.ts` — tool descriptions.

### Axis RT.3 — Versioning discipline (B.8)
**Question:** Are all recently-touched canonical artifacts carrying correct
`version`, `status`, and changelog entries?
Check these files for frontmatter compliance:
- `platform/scripts/integrity/audit_ucn_msr.py` (W7-R1 — check docstring)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (W7-R2 — version 1.7, count 109)
- `platform/scripts/eval/fixtures.json` (W7-R3 — check version field)
- `00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md` (has Post-W7-R1 section)

### Axis RT.4 — No fabricated computation (B.10)
**Question:** Do any of the 24 eval fixtures (`fixtures.json`) claim expected
signal IDs or chart facts that cannot be verified in the corpus?
For each `expected_signals` and `expected_keywords` in fixtures.json: spot-check
5 fixtures at random against MSR_v3_0.md and FORENSIC_ASTROLOGICAL_DATA_v8_0.md.

### Axis RT.5 — Whole-chart-read protocol (B.11)
**Question:** Does the query pipeline route holistic queries through L2.5
(MSR + UCN + CGM + CDLM + RM) before producing a synthesis?
Check: the composition rules in `platform/src/lib/bundle/composition_rules.ts`.
Verify that for a `holistic` query type, the rule set includes MSR, UCN, CGM,
and CDLM tools in the authorized bundle.

### Axis RT.6 — Mirror discipline (MP.1 + ND.1)
**Question:** Do `.geminirules` and `.gemini/project_state.md` reflect the
M2 corpus activation state at adapted parity?
Read both files. Check that they acknowledge M2 work (composition rules, provenance
audits, per-tool planner, eval harness) at the Gemini-side level.
A full mirror update is W8-R2 scope; this axis only checks for gross desync.

### Axis RT.7 — Pipeline integrity (new query pipeline default)
**Question:** Is `NEW_QUERY_PIPELINE_ENABLED` default true, and does the
pipeline function end-to-end without fatal errors in the codebase?
Check: `platform/src/lib/config/feature_flags.ts`
Run: `cd platform && npm run typecheck` (TypeScript must pass clean).
Run: `cd platform && npm run test -- --testPathPattern "composition_rules|per_tool_planner" --verbose`
Target: all tests pass; no new TypeScript errors introduced in W6/W7.

### Axis RT.8 — Scope boundary (no M3 pre-build)
**Question:** Has any W6/W7 session introduced infrastructure for macro-phases
later than M2?
Search for any new files under `07_`, `08_`, `09_`, `10_` directories, or any
code importing from a not-yet-active phase layer.
```bash
find ~/Vibe-Coding/Apps/Madhav -path "*/07_*" -newer ~/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md 2>/dev/null
```
Any hit is a scope violation and must be deleted.

### Axis RT.9 — Eval fixture factual accuracy
**Question:** Are the 24 eval fixture `gold_answer_summary` fields factually
correct per the corpus?
For each of the 6 fixture types, verify 1 fixture per type (6 total) against
the relevant corpus file (FORENSIC, MSR, UCN, or domain report).
Record any factual errors found.

---

## §4 — Thin UI smoke

After red-team axes are complete, run a thin UI smoke of the consume pipeline:

**Step S.1 — TypeScript build:**
```bash
cd ~/Vibe-Coding/Apps/Madhav/platform
npm run typecheck
```
Must: exit 0.

**Step S.2 — Unit test suite:**
```bash
npm run test -- --passWithNoTests 2>&1 | tail -20
```
Must: no new failures beyond the 13 known-residual Jest failures established
at W5 end-state. Record exact failure count.

**Step S.3 — Composition rules coverage:**
```bash
npm run test -- --testPathPattern "composition_rules" --verbose 2>&1 | tail -30
```
Must: all W6-R1 tests pass (17 new tests + pre-existing suite).

**Step S.4 — Per-tool planner coverage:**
```bash
npm run test -- --testPathPattern "per_tool_planner" --verbose 2>&1 | tail -30
```
Must: all W6-R2 tests pass (15 tests).

**Step S.5 — Integrity audit scripts:**
```bash
cd ~/Vibe-Coding/Apps/Madhav
python3 platform/scripts/integrity/audit_msr_forensic.py 2>&1 | tail -5
python3 platform/scripts/integrity/audit_ucn_msr.py 2>&1 | tail -5
```
Must: both print PASS. Record percentages.
(audit_cgm_supports.py requires live DB — record as SKIP if DB unreachable.)

---

## §5 — Red-team report artifact

After all axes and smoke steps, create:
`00_ARCHITECTURE/EVAL/REDTEAM_M2_v1_0.md`

```markdown
---
artifact: REDTEAM_M2_v1_0.md
canonical_id: REDTEAM_M2_v1_0
version: 1.0
status: CURRENT
authored_by: KARN-W8-R1-REDTEAM-SMOKE
authored_at: <ISO date>
verdict: PASS | PASS_WITH_FIXES | FAIL
---

# M2 Red-Team Report

**Session:** KARN-W8-R1-REDTEAM-SMOKE
**Verdict:** <PASS | PASS_WITH_FIXES | FAIL>

## Axis findings

| Axis | Description | Result | Action taken |
|---|---|---|---|
| RT.1 | Layer separation | PASS/FINDING | ... |
| RT.2 | Derivation ledger | ... | ... |
| RT.3 | Versioning discipline | ... | ... |
| RT.4 | No fabricated computation | ... | ... |
| RT.5 | Whole-chart-read protocol | ... | ... |
| RT.6 | Mirror discipline | ... | ... |
| RT.7 | Pipeline integrity | ... | ... |
| RT.8 | Scope boundary | ... | ... |
| RT.9 | Fixture factual accuracy | ... | ... |

## Smoke results

| Step | Command | Result |
|---|---|---|
| S.1 TypeScript | npm run typecheck | PASS/FAIL |
| S.2 Unit tests | npm run test | N passing, M known residuals |
| S.3 Comp rules | composition_rules tests | N/N PASS |
| S.4 Planner | per_tool_planner tests | N/N PASS |
| S.5 Audit scripts | audit_msr_forensic + audit_ucn_msr | xx.xx% / xx.xx% |

## Fixes applied (if any)
<list any inline fixes made under PASS_WITH_FIXES>

## Verdict rationale
<one paragraph>

## W8-R2 gate
<CLEARED | BLOCKED — reason>
```

---

## §6 — Acceptance criteria

| # | Criterion |
|---|---|
| AC.1 | All 9 red-team axes executed and recorded |
| AC.2 | `REDTEAM_M2_v1_0.md` created with all table rows populated |
| AC.3 | TypeScript typecheck exits 0 |
| AC.4 | Composition rules + per-tool planner tests all pass |
| AC.5 | audit_msr_forensic.py and audit_ucn_msr.py both print PASS |
| AC.6 | Verdict is PASS or PASS_WITH_FIXES (if FAIL: brief's halt condition applies) |
| AC.7 | No M3+ scope introduced (RT.8 clean) |
| AC.8 | W8-R2 gate declared in REDTEAM artifact |
| AC.9 | SESSION_LOG appended |

---

## §7 — Halt conditions

Stop and report to native if:
- TypeScript typecheck exits non-zero and cannot be fixed in <30 min
- Any composition_rules or per_tool_planner test is newly failing (regression)
- RT.8 finds unreachable M3+ pre-build artifacts (delete + report)
- Red-team verdict is FAIL (material unfixable flaw found)

---

## §8 — Closing summary template

```
=== KARN-W8-R1 CLOSE ===
Red-team verdict: <PASS | PASS_WITH_FIXES | FAIL>
Axes: 9/9 executed
Findings: <N findings, N fixes applied>
Smoke: TypeScript PASS | tests N/N | audits xx.xx% / xx.xx%
REDTEAM_M2_v1_0.md: created
W8-R2 gate: <CLEARED | BLOCKED>
SESSION_LOG: appended
```
