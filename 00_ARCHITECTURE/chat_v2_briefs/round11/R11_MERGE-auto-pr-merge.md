---
canonical_id: R11_MERGE
version: 1.0
status: CURRENT
session_id: R11-MERGE
title: Push branch, open PR, auto-merge to main (terminal queue entry)
depends_on: ["V-S1", "V-S2", "V-S3", "V-S4", "V-S5", "V-S6", "S-S1", "S-S2", "S-S3", "S-S4", "S-S5", "O-S1", "O-S2", "O-S3", "O-S4", "O-S5"]
blocked_on: []
flag: —
flag_default: —
client_side: "no — git/gh CLI only"
authored: 2026-05-21
---

# R11-MERGE — Auto PR + Auto Merge

## Context

Terminal entry in the R11 queue. Per `NATIVE_RULINGS_v1_0.md §6`, after all 16
R11 sessions close PASS, the Conductor runs this entry to push the branch, open
a PR to main, wait for CI, and auto-merge.

**Native override note:** This entry has `requires_human_approval: false`, an
explicit override of the Wave 1 Conductor invariant "PR-to-main always
human-gated". The override is local to R11 only and is logged in
`NATIVE_RULINGS_v1_0.md §6`.

## Files in Scope

This session runs shell commands only. It does NOT edit source files.

- Optional: `STREAM_R11_COMPLETE.md` (new) at `00_ARCHITECTURE/chat_v2_briefs/round11/`
  summarizing the run: each session's close timestamp, gate result, commit SHA;
  the Amendment 5 deploy.yml coverage check output; final auto-merge SHA.

## Files Must NOT Touch

- Any source file in `platform/src/`
- Any other R11 brief
- Phase 4C files

## Acceptance Criteria

1. **All 16 R11 sessions PASS:** Conductor confirms each depends_on entry has
   `status: passed` before invoking this session. (Conductor enforces this via
   the queue's depends_on logic.)
2. **Amendment 5 deploy.yml coverage gate PASSES:**
   ```
   grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R11" platform/src --include="*.ts*" -o | awk -F: '{print $NF}' | sort -u
   grep -oE "NEXT_PUBLIC_MARSYS_FLAG_R11_[A-Z_]+" .github/workflows/deploy.yml | sort -u
   ```
   First set must be subset of second. If not, HALT.
3. **Branch pushed to remote:**
   `git push -u origin chat-v2/round11-claude-parity`
4. **PR opened against main:**
   ```
   gh pr create \
     --base main \
     --head chat-v2/round11-claude-parity \
     --title "feat(chat-v2): R11 — Chat V2 Claude parity (16 sessions)" \
     --body-file 00_ARCHITECTURE/chat_v2_briefs/round11/R11_MASTER_PLAN_v1_0.md
   ```
5. **Auto-merge enabled:**
   `gh pr merge --auto --squash --delete-branch`
   Waits for CI checks then merges. If checks fail, PR sits — Conductor halts
   with a clear message ("PR opened but CI failed; auto-merge waiting").
6. **STREAM_R11_COMPLETE.md authored** with the merge commit SHA after the merge
   completes (this happens asynchronously; for the Conductor's purpose, opening
   the PR + enabling auto-merge is sufficient to claim PASS).
7. **CLAUDE.md §E append:** Optional — Conductor does NOT amend CLAUDE.md; the
   native runs the §E amendment in a follow-up Cowork session after merge lands.

## Pre-commit Gates

This session runs gate commands only; there is no commit step.

## Gate command (run by Conductor after sub-agent terminates)

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11

# (a) Amendment 5 coverage
SOURCE_FLAGS=$(grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R11" platform/src --include="*.ts*" -o 2>/dev/null | awk -F: '{print $NF}' | sort -u)
YML_FLAGS=$(grep -oE "NEXT_PUBLIC_MARSYS_FLAG_R11_[A-Z_]+" .github/workflows/deploy.yml 2>/dev/null | sort -u)
for f in $SOURCE_FLAGS; do
  if ! echo "$YML_FLAGS" | grep -q "^$f$"; then
    echo "FAIL: flag $f not in deploy.yml --build-arg block"
    exit 1
  fi
done

# (b) PR exists
gh pr view chat-v2/round11-claude-parity --json state,number 2>/dev/null | grep -q '"number"' || { echo "FAIL: PR not found"; exit 1; }

# (c) Auto-merge is set (or already merged)
gh pr view chat-v2/round11-claude-parity --json autoMergeRequest,state | grep -E '"state":"MERGED"|"autoMergeRequest":\{' || { echo "FAIL: auto-merge not enabled"; exit 1; }

echo "PASS: branch pushed, PR opened, auto-merge enabled (or already merged)"
exit 0
```

## Commit Template

No commits. This session opens a PR.

## Decision Log

*(Conductor sub-agent: paste branch push output, PR URL, auto-merge enable output,
final merge commit SHA when available.)*
