---
artifact: GH_DRIFT_DETECTOR_FIX_BRIEF_v1_0.md
canonical_id: GH_DRIFT_DETECTOR_FIX_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork (Claude Opus 4.7) 2026-05-21
authored_for_session: GH-DRIFT-DETECTOR-FIX
purpose: >
  Resolve drift_detector.py exit-4 crash (IsADirectoryError on
  08_CLASSICAL_CROSS_REFERENCE) that has been a pre-existing failure on main since
  before PR #111. SESSION_HALT.md on branch chat-v2/pr-111-remediation §AC.7
  documents the failure mode. This brief is one of three governance-hygiene
  follow-ups spawned from that HALT.
launch_instructions: >
  When ready, copy this file to /Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDECODE_BRIEF.md
  and launch Claude Code with --dangerously-skip-permissions and a one-line "execute
  this brief autonomously" prompt. Only one CLAUDECODE_BRIEF.md may exist at root at
  a time per CLAUDE.md §C.0.
active_phase: Governance Hygiene (post-PR-111 follow-up; concurrent workstream; not a macro-phase change)
may_touch:
  - platform/scripts/governance/drift_detector.py
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/manifest_overrides.yaml
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
  - 00_ARCHITECTURE/governance_hygiene_briefs/**
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  - 00_ARCHITECTURE/SESSION_LOG.md
  - CLAUDE.md
  - .gemini/project_state.md
  - .geminirules
  - CLAUDECODE_BRIEF.md
must_not_touch:
  - platform/src/**
  - platform/migrations/**
  - platform/tests/**
  - platform/scripts/governance/schema_validator.py
  - platform/scripts/governance/mirror_enforcer.py
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
  - 00_ARCHITECTURE/PHASE_*.md
  - 00_ARCHITECTURE/MACRO_PLAN_*.md
  - 00_ARCHITECTURE/PROJECT_ARCHITECTURE_*.md
  - 00_ARCHITECTURE/CONDUCTOR/**
acceptance_criteria:
  - AC.1: Diagnose the crash. Run drift_detector.py once and capture the full traceback into 00_ARCHITECTURE/governance_hygiene_briefs/dr_detector_fix/_DIAGNOSIS.md. Identify whether the offending path comes from (a) CAPABILITY_MANIFEST.json, (b) manifest_overrides.yaml, (c) CANONICAL_ARTIFACTS_v1_0.md, or (d) drift_detector's own path-resolution logic. Note the §H.3.N check that triggers it.
  - AC.2: Apply the smallest sufficient fix. Three valid shapes — pick whichever the diagnosis warrants — (a) correct the malformed path entry in the source-of-truth registry; (b) update drift_detector to skip directory entries with a logged WARNING rather than crash; (c) add an explicit `is_directory_allowed: true` flag in manifest_overrides for entries that intentionally point to a folder.
  - AC.3: drift_detector.py exits ≤ 3 after the fix (per §H.4 exit-code semantics — 4 means script error; ≤ 3 means findings-only, no crash). Capture the new exit code and finding count into _DIAGNOSIS.md.
  - AC.4: No regression in schema_validator.py or mirror_enforcer.py. Both must still exit with the same code as on main pre-fix (schema_validator ≤ 2 per current corpus state; mirror_enforcer 0).
  - AC.5: One-paragraph append to 00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md §F (CI / cron cadence) documenting the fix and reaffirming the exit-code-3 known_residuals discipline. Do NOT relax the threshold globally; only document the fix path.
  - AC.6: Standard governance trail — CURRENT_STATE v5.29 changelog entry; SESSION_LOG entry; CLAUDE.md no-op (do NOT amend CLAUDE.md unless the diagnosis itself requires a §C item update); .gemini/project_state.md adapted-parity mirror.
  - AC.7: All three validators run cleanly at session close — drift_detector exits ≤ 3 (the goal), schema_validator exits ≤ 2 (no regression), mirror_enforcer exits 0.
  - AC.8: Work on branch `governance-hygiene/drift-detector-fix` in a fresh worktree at /Users/Dev/Vibe-Coding/Apps/MadhavGH1/. PR opened against main via `gh pr create`. Body lists AC.1–AC.10 statuses. Not auto-merged.
  - AC.9: This brief's `status:` flipped from `STORED` to `COMPLETE` (or `ACTIVE → COMPLETE` if it was copied to CLAUDECODE_BRIEF.md at root).
  - AC.10: Final summary emitted per §4 Step 10 pattern (worktree path, commits, PR URL, AC statuses, residuals).
hard_constraints:
  - Single-purpose session. Do NOT bundle other validator fixes here. If schema_validator violations surface during this work, log them in _DIAGNOSIS.md as out-of-scope and defer to GH_CORPUS_FRONTMATTER_BACKFILL or GH_SESSION_LOG_STRUCTURE briefs.
  - Do NOT relax exit-code thresholds. The point is to make drift_detector pass the threshold it already has, not to lower the bar.
  - Do NOT merge the PR. Stop at "PR opened". Native reviews and merges.
  - Work in a worktree; do NOT operate in the main checkout.
  - Commit messages carry the Co-Authored-By: Claude Sonnet 4.6 trailer.
session_open_obligations:
  - Read CLAUDE.md fully.
  - Read 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2.
  - Read 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §H (drift checks H.3.1–H.3.8 + exit codes §H.4).
  - Read this brief in full.
  - Read SESSION_HALT.md from branch chat-v2/pr-111-remediation for context: `git show origin/chat-v2/pr-111-remediation:SESSION_HALT.md`.
  - Read 00_ARCHITECTURE/CAPABILITY_MANIFEST.json and 00_ARCHITECTURE/manifest_overrides.yaml to understand the manifest-vs-CANONICAL_ARTIFACTS cutover (per CLAUDE.md §C item 2, manifest is now authoritative since 2026-04-27).
  - Emit SESSION_OPEN handshake per SESSION_OPEN_TEMPLATE_v1_0.md.
session_close_obligations:
  - All three validators pass their thresholds (AC.7).
  - Append SESSION_LOG entry per SESSION_CLOSE_TEMPLATE_v1_0.md.
  - Update CURRENT_STATE_v1_0.md to v5.29.
  - Flip this file's `status:` to COMPLETE.
  - Push branch and open PR.
  - Emit final summary.
---

# Governance Hygiene: drift_detector Fix Brief

## §1 — Context

`drift_detector.py` crashes with `IsADirectoryError: [Errno 21] Is a directory: .../08_CLASSICAL_CROSS_REFERENCE` on `main`. This has been a pre-existing failure since before PR #111 and was surfaced (not introduced) by the PR-111-REMEDIATION session. SESSION_HALT.md on branch `chat-v2/pr-111-remediation` documents the diagnosis: a canonical artifact path resolves to a directory instead of a file, in one of the §H drift checks (most likely H.3.2 or H.3.7).

`drift_detector` exit codes per §H.4: 0 clean, 1 CRITICAL, 2 HIGH, 3 MEDIUM/LOW, 4 script error. Goal: get from 4 to ≤ 3.

## §2 — Diagnosis path

Step 1 — Reproduce. Run `python3 platform/scripts/governance/drift_detector.py 2>&1 | tee /tmp/dd_baseline.log` and confirm IsADirectoryError + the exact path.

Step 2 — Trace the path source. The crashing path is `08_CLASSICAL_CROSS_REFERENCE` (a folder). Find which check loaded that path:

```bash
grep -n "08_CLASSICAL_CROSS_REFERENCE" 00_ARCHITECTURE/CAPABILITY_MANIFEST.json 00_ARCHITECTURE/manifest_overrides.yaml 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
grep -n "08_CLASSICAL_CROSS_REFERENCE\|is_dir\|stat\|read_text\|read_bytes" platform/scripts/governance/drift_detector.py
```

The CAPABILITY_MANIFEST cutover (2026-04-27 per CLAUDE.md §C.2) means the manifest is the new source of truth. If the bad entry is in CANONICAL_ARTIFACTS_v1_0.md (now `SUPERSEDED`), the fix is to ensure drift_detector reads from the manifest, not the archive.

Step 3 — Classify the fix shape per AC.2 (registry data fix vs. detector hardening vs. opt-in directory flag) and apply.

## §3 — Out of scope

- schema_validator HIGH/MEDIUM frontmatter violations (separate brief: GH_CORPUS_FRONTMATTER_BACKFILL).
- SESSION_LOG structural HIGH violations (separate brief: GH_SESSION_LOG_STRUCTURE).
- Any application code under `platform/src/**`.
- Any chat-v2 work.
- Lowering the §F exit-code threshold globally.

## §4 — Step-by-step

### Step 1 — Worktree
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
if [ -d /Users/Dev/Vibe-Coding/Apps/MadhavGH1 ]; then
  git worktree remove --force /Users/Dev/Vibe-Coding/Apps/MadhavGH1 || true
fi
git branch -D governance-hygiene/drift-detector-fix 2>/dev/null || true
git push origin --delete governance-hygiene/drift-detector-fix 2>/dev/null || true
git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavGH1 -b governance-hygiene/drift-detector-fix origin/main
cd /Users/Dev/Vibe-Coding/Apps/MadhavGH1
mkdir -p 00_ARCHITECTURE/governance_hygiene_briefs/dr_detector_fix
```

### Step 2 — SESSION_OPEN handshake.

### Step 3 — AC.1 diagnose + write _DIAGNOSIS.md.

### Step 4 — AC.2 apply the fix per the diagnosis. Re-run drift_detector after the fix; confirm exit ≤ 3.

### Step 5 — AC.4 regression check — schema_validator and mirror_enforcer must hold their existing exit codes.

### Step 6 — AC.5 append to ONGOING_HYGIENE_POLICIES_v1_0.md §F.

### Step 7 — AC.6 governance trail (CURRENT_STATE v5.29 + SESSION_LOG + .gemini mirror).

### Step 8 — AC.7 final validator triple-run; if anything regresses, halt.

### Step 9 — AC.8/9/10 brief close + commits + PR + summary.

## §5 — Halt conditions

- Diagnosis reveals the fix requires touching `06_LEARNING_LAYER/**`, `01_FACTS_LAYER/**`, or `025_HOLISTIC_SYNTHESIS/**` → halt via SESSION_HALT.md and escalate. Those paths are out of scope.
- Drift_detector exit code can't be brought below 4 with any in-scope fix → halt with full diagnosis.
- schema_validator or mirror_enforcer regresses (exit code rises vs. baseline) → halt and revert.
