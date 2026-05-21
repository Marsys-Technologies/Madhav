---
artifact: GH_DRIFT_HIGH_TRIAGE_BRIEF_v1_0.md
canonical_id: GH_DRIFT_HIGH_TRIAGE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork (Claude Sonnet 4.6) 2026-05-21
authored_for_session: GH-DRIFT-HIGH-TRIAGE
purpose: >
  Categorize every HIGH finding from drift_detector.py by check type (H.3.1
  through H.3.8) and record a suggested fix per finding — without applying any
  fixes. Produces a durable triage report at
  00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/REPORT.md that
  subsequent fix sessions can consume one check-class at a time. This is the
  fourth governance-hygiene follow-up from the chat-v2/pr-111-remediation arc.
launch_instructions: >
  When ready, copy this file to /Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF.md
  and launch Claude Code with --dangerously-skip-permissions and a one-line
  "execute this brief autonomously" prompt. Only one CLAUDECODE_BRIEF.md may
  exist at root at a time per CLAUDE.md §C.0. Alternatively, this brief is
  dispatched by the Chat V2 wrap-up orchestrator as Packet E.2 — in that case
  the worktree override in the E.2 dispatch prompt supersedes Step 1 below.
active_phase: Governance Hygiene (post-PR-111 follow-up; concurrent workstream; not a macro-phase change)
may_touch:
  - 00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/**
  - 00_ARCHITECTURE/governance_hygiene_briefs/GH_DRIFT_HIGH_TRIAGE_BRIEF_v1_0.md
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  - 00_ARCHITECTURE/SESSION_LOG.md
  - .gemini/project_state.md
  - CLAUDECODE_BRIEF.md
must_not_touch:
  - platform/**
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/CONDUCTOR/**
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
  - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
  - 00_ARCHITECTURE/MACRO_PLAN_*.md
  - 00_ARCHITECTURE/PROJECT_ARCHITECTURE_*.md
  - 00_ARCHITECTURE/PHASE_*.md
  - CLAUDE.md
  - .geminirules
acceptance_criteria:
  - AC.1: Run drift_detector.py and capture the full HIGH finding list. Command — `python3 platform/scripts/governance/drift_detector.py 2>&1 | tee /tmp/dd_high_triage.log`. Confirm exit code = 2 (HIGH findings present). If exit = 4 (crash), halt immediately — this brief is blocked on the crash being pre-fixed; see GH_DRIFT_DETECTOR_FIX_BRIEF.
  - AC.2: Parse every HIGH-severity line from the output. Extract (finding_id, check_code, artifact_path, finding_message) for each. Store the raw parsed list as 00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/RAW_HIGH_FINDINGS.txt (plain text, one finding per line) so it is auditable independently of REPORT.md.
  - AC.3: Produce 00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/REPORT.md. The report must contain — (a) a header with run timestamp, drift_detector exit code, total HIGH count, and breakdown table by H.3.N check; (b) one section per check class (H.3.1 path-table parity, H.3.2 fingerprint mismatch, H.3.3 MACRO_PLAN/PHASE_B_PLAN alignment, H.3.5 FILE_REGISTRY staleness, H.3.6 GOVERNANCE_STACK desync, H.3.7 phantom references, H.3.8 unreferenced artifacts); (c) within each section, a Markdown table with columns [finding_id | artifact_path | finding_message | suggested_fix]; (d) a final §Notes section flagging any ambiguous findings that could not be cleanly categorized into a single check class.
  - AC.4: Every HIGH finding must appear in REPORT.md exactly once (no omissions, no duplicates). If a finding is ambiguous, assign it to the primary check class and note the ambiguity in REPORT.md §Notes — do NOT halt on ambiguity unless the finding is completely unclassifiable (see §5 halt conditions).
  - AC.5: Suggested fixes must be specific and actionable — e.g., "Update CAPABILITY_MANIFEST.json path entry from X to Y", "Add frontmatter `fingerprint: sha256_of_file` to artifact Z", "Remove phantom ref SIG.MSR.999 from CGM_v9_0.md line N". Generic suggested fixes ("fix the manifest") are not acceptable.
  - AC.6: Standard governance trail — CURRENT_STATE changelog entry (next version after the most recent entry at session open); SESSION_LOG append per SESSION_CLOSE_TEMPLATE_v1_0.md; .gemini/project_state.md adapted-parity mirror noting the triage report was produced and its finding count by class.
  - AC.7: All three validators run at session close. Capture exit codes in REPORT.md §Appendix. No regression is permitted — drift_detector must exit ≤ 3 (same as at session open; this session applies NO fixes), schema_validator must exit ≤ 2, mirror_enforcer must exit 0. If any validator regresses, halt and do NOT claim close.
  - AC.8: Work on branch `governance-hygiene/drift-high-triage` in this worktree (or a fresh worktree per Step 1 if not dispatched by the orchestrator). Push, open PR against main via `gh pr create`. PR body lists AC.1–AC.10 statuses and REPORT.md finding totals per check class. Do NOT merge.
  - AC.9: This brief's `status:` flipped from `STORED` to `COMPLETE` (or `ACTIVE → COMPLETE` if it was copied to CLAUDECODE_BRIEF.md at root).
  - AC.10: Final summary emitted — worktree path (or branch), commits, PR URL, total HIGH finding count, breakdown by H.3.N, any §Notes ambiguous findings, validator triple exit codes. Under 400 words.
hard_constraints:
  - CATEGORIZE ONLY. No fixes applied in this session. Do not patch CAPABILITY_MANIFEST.json, do not update fingerprints, do not remove phantom refs, do not add frontmatter. The sole output artifact is REPORT.md + RAW_HIGH_FINDINGS.txt + governance trail.
  - Do NOT touch the must_not_touch paths above even if a finding directly implicates them. Log the finding in REPORT.md with its suggested fix and leave the file untouched.
  - If drift_detector exits 4 (crash), halt immediately — this brief requires exit ≤ 3 at session open as a pre-condition. Write HUMAN_GATE_<session>.md and stop.
  - Do NOT merge the PR. Stop at "PR opened". Native reviews and merges.
  - Commit messages carry the Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com> trailer.
  - Session-close REPORT.md finding counts must match RAW_HIGH_FINDINGS.txt line count exactly. Any mismatch is a blocking error.
session_open_obligations:
  - Read CLAUDE.md fully.
  - Read 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2.
  - Read 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §H (drift checks H.3.1–H.3.8 + exit codes §H.4). This section defines the check taxonomy that REPORT.md sections must map to.
  - Read this brief in full.
  - Read 00_ARCHITECTURE/governance_hygiene_briefs/dr_detector_fix/_DIAGNOSIS.md for context on the pre-existing crash fix (the crash must be resolved before this brief executes).
  - Emit SESSION_OPEN handshake per SESSION_OPEN_TEMPLATE_v1_0.md.
session_close_obligations:
  - All three validators at their expected thresholds (AC.7).
  - REPORT.md and RAW_HIGH_FINDINGS.txt committed and pushed.
  - SESSION_LOG entry appended per SESSION_CLOSE_TEMPLATE_v1_0.md.
  - CURRENT_STATE updated (AC.6).
  - .gemini/project_state.md mirror updated (AC.6).
  - PR opened (AC.8).
  - This brief's status flipped to COMPLETE (AC.9).
  - Final summary emitted (AC.10).
---

# Governance Hygiene: drift_detector HIGH Finding Triage Brief

## §1 — Context

`drift_detector.py` currently exits code 2 (HIGH findings present) with approximately 86+ HIGH findings — the pre-existing baseline as of Packet D of the Chat V2 wrap-up arc. These findings span multiple check classes (H.3.1 through H.3.8) and have accumulated across the M2–M5 arc. No single prior session has catalogued them systematically.

This brief prescribes a **categorize-only** session: run the detector, parse every HIGH finding, classify it by its `H.3.N` check code, annotate it with a specific suggested fix, and produce a durable triage report. Subsequent fix sessions consume the report one check-class at a time, using this triage as their input.

`drift_detector` exit codes per §H.4: 0 clean, 1 CRITICAL, 2 HIGH, 3 MEDIUM/LOW, 4 script error. The crash fix (exit 4 → ≤ 3) was applied in GH_DRIFT_DETECTOR_FIX_BRIEF. This brief requires that fix to already be merged.

## §2 — Check taxonomy reference

Per `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §H`, the HIGH-tier checks are:

| Check | Name | What it verifies |
|---|---|---|
| H.3.1 | path-table parity | Every artifact in the canonical path table has a real file at the declared path. |
| H.3.2 | fingerprint match | The SHA-256 fingerprint stored in the registry matches the current on-disk file. |
| H.3.3 | MACRO_PLAN/PHASE_B_PLAN alignment | Phase plan artifacts referenced in MACRO_PLAN are consistent with the declared phase plan file. |
| H.3.5 | FILE_REGISTRY staleness | FILE_REGISTRY entries disagree with CAPABILITY_MANIFEST paths or statuses. |
| H.3.6 | GOVERNANCE_STACK desync | GOVERNANCE_STACK entries disagree with the manifest or with each other. |
| H.3.7 | phantom references | A reference in a canonical artifact points to an artifact_id or path that does not exist in the registry. |
| H.3.8 | unreferenced artifacts | An artifact exists on disk (or in the manifest) but is not referenced by any other canonical artifact. |

REPORT.md sections must use these check codes verbatim as headings.

## §3 — REPORT.md schema

```
# drift_detector HIGH Finding Triage Report

**Run timestamp:** YYYY-MM-DDTHH:MM:SSZ
**drift_detector exit code:** 2
**Total HIGH finding count:** NNN
**Breakdown by check:**

| Check | Count |
|---|---|
| H.3.1 path-table parity | N |
| H.3.2 fingerprint match | N |
| H.3.3 MACRO_PLAN alignment | N |
| H.3.5 FILE_REGISTRY | N |
| H.3.6 GOVERNANCE_STACK | N |
| H.3.7 phantom refs | N |
| H.3.8 unreferenced | N |
| Unclassified | N |

---

## H.3.1 — Path-table parity

| finding_id | artifact_path | finding_message | suggested_fix |
|---|---|---|---|
| ... | ... | ... | ... |

## H.3.2 — Fingerprint match
...

[one section per check class present in the findings; omit sections with zero findings]

---

## §Notes — Ambiguous findings

[List any finding that spans multiple check classes or could not be
 cleanly categorized; include reasoning for primary-class assignment]

---

## §Appendix — Validator triple at session close

| Validator | Exit code |
|---|---|
| drift_detector.py | 2 |
| schema_validator.py | ≤ 2 |
| mirror_enforcer.py | 0 |
```

## §4 — Step-by-step

### Step 1 — Branch setup
```bash
# If dispatched by orchestrator (Packet E.2), skip worktree creation;
# the branch is created inside the MadhavCV2Wrap worktree:
cd /Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap
git fetch origin
git checkout -b governance-hygiene/drift-high-triage origin/main
mkdir -p 00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage
```

If NOT dispatched by orchestrator (standalone launch):
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavGH4 -b governance-hygiene/drift-high-triage origin/main
cd /Users/Dev/Vibe-Coding/Apps/MadhavGH4
mkdir -p 00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage
```

### Step 2 — SESSION_OPEN handshake
Emit per `SESSION_OPEN_TEMPLATE_v1_0.md` before any substantive work.

### Step 3 — AC.1 + AC.2 — Run detector and parse findings
```bash
python3 platform/scripts/governance/drift_detector.py 2>&1 | tee /tmp/dd_high_triage.log
echo "Exit code: $?"
```
If exit = 4: **HALT** — write `00_ARCHITECTURE/CONDUCTOR/wrapup/HUMAN_GATE_E2.md` (if in orchestrator) or `SESSION_HALT.md` (if standalone), report crash, stop. The crash pre-fix is a prerequisite.

Filter HIGH lines and write `RAW_HIGH_FINDINGS.txt`:
```bash
grep -E "^\s*(HIGH|FINDING.*HIGH)" /tmp/dd_high_triage.log > \
  00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/RAW_HIGH_FINDINGS.txt
wc -l 00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/RAW_HIGH_FINDINGS.txt
```

### Step 4 — AC.3–AC.5 — Classify findings and write REPORT.md
For each finding in `RAW_HIGH_FINDINGS.txt`:
1. Identify the `H.3.N` check code from the finding line (e.g., `[H.3.2]` tag or check function name in the message).
2. Extract `artifact_path` and `finding_message`.
3. Determine `suggested_fix` — specific and actionable per AC.5.
4. Assign to the correct section in REPORT.md.
5. If ambiguous, assign to primary class + note in §Notes.

Write `REPORT.md` at `00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/REPORT.md` per the schema in §3.

Verify: line count of `RAW_HIGH_FINDINGS.txt` == total row count across all REPORT.md finding tables. Any mismatch = blocking error.

### Step 5 — AC.6 — Governance trail
- Append `CURRENT_STATE_v1_0.md` changelog entry (next version after the highest entry at session open).
- Append `SESSION_LOG.md` entry per `SESSION_CLOSE_TEMPLATE_v1_0.md`.
- Update `.gemini/project_state.md` with adapted-parity note: triage report produced; total HIGH count by class; no fixes applied.

### Step 6 — AC.7 — Validator triple
```bash
python3 platform/scripts/governance/schema_validator.py; echo "schema exit: $?"
python3 platform/scripts/governance/drift_detector.py; echo "drift exit: $?"
python3 platform/scripts/governance/mirror_enforcer.py; echo "mirror exit: $?"
```
Capture exit codes. Append to REPORT.md §Appendix. If any validator regresses vs. session-open baseline, **HALT** — do NOT claim close.

### Step 7 — AC.8–AC.10 — Commit, PR, summary
```bash
git add 00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/ \
        00_ARCHITECTURE/CURRENT_STATE_v1_0.md \
        00_ARCHITECTURE/SESSION_LOG.md \
        .gemini/project_state.md \
        00_ARCHITECTURE/governance_hygiene_briefs/GH_DRIFT_HIGH_TRIAGE_BRIEF_v1_0.md
git commit -m "$(cat <<'EOF'
feat(governance): drift_detector HIGH triage report — categorize-only

Classifies every HIGH drift finding by H.3.N check class with
suggested fix per finding. No fixes applied. Produces REPORT.md
at 00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
git push -u origin governance-hygiene/drift-high-triage
gh pr create \
  --title "governance(hygiene): drift HIGH triage — categorize only [GH-DRIFT-HIGH-TRIAGE]" \
  --body "$(cat <<'EOF'
## Summary

Categorize-only triage of all drift_detector HIGH findings. No fixes applied.

Produces `00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/REPORT.md`
classifying every HIGH finding by H.3.N check class (H.3.1–H.3.8) with a
specific suggested fix per finding. Subsequent per-class fix PRs consume this
report as input.

## AC statuses

- [ ] AC.1 — detector run, exit code captured
- [ ] AC.2 — RAW_HIGH_FINDINGS.txt written
- [ ] AC.3 — REPORT.md written per schema
- [ ] AC.4 — all findings present exactly once
- [ ] AC.5 — all suggested_fixes specific and actionable
- [ ] AC.6 — governance trail (CURRENT_STATE + SESSION_LOG + .gemini mirror)
- [ ] AC.7 — validator triple no-regression
- [ ] AC.8 — PR opened (this PR)
- [ ] AC.9 — brief status COMPLETE
- [ ] AC.10 — final summary emitted

## Finding totals (from REPORT.md)

<!-- Sub-agent fills in after writing REPORT.md -->
| Check | Count |
|---|---|
| H.3.1 | TBD |
| H.3.2 | TBD |
| H.3.3 | TBD |
| H.3.5 | TBD |
| H.3.6 | TBD |
| H.3.7 | TBD |
| H.3.8 | TBD |
| Total HIGH | TBD |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Flip this brief's `status:` from `STORED` to `COMPLETE`.

Return to main (if dispatched by orchestrator):
```bash
git checkout main && git pull --ff-only origin main
```

Emit final summary per AC.10.

## §5 — Halt conditions

- drift_detector exits 4 (crash) at session open → halt with `HUMAN_GATE_E2.md` (orchestrator) or `SESSION_HALT.md` (standalone); triage session is blocked on crash fix being merged.
- A finding's check code is not in the H.3.1–H.3.8 taxonomy AND cannot be mapped to any check class → log in REPORT.md §Notes as `UNCLASSIFIABLE`, include the raw finding line verbatim, count toward the total, and continue. Do NOT halt on ambiguity; only halt if the entire run produces zero classifiable findings (indicating a breaking change in detector output format).
- Any validator regresses at Step 6 → halt without claiming close.
- `git push` or `gh pr create` fails with a non-transient error → halt with gate file.

## §6 — Out of scope

- Applying any suggested fix (even "obvious" ones like a trivially wrong path) — deferred to per-class fix sessions.
- `schema_validator.py` violations (separate brief series: GH_CORPUS_FRONTMATTER_BACKFILL).
- MEDIUM or LOW drift findings.
- Any application code under `platform/src/**`.
- Any Chat V2, M5, or Learning Layer work.
