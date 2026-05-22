---
canonical_id: R11A_MERGE
session_id: R11A-MERGE
title: R11.A terminal — push branch, open PR, auto-merge to main
phase: R11.A — Foundation
depends_on: [A-S0, A-S1, A-S2, A-S3, A-S4, A-S5, A-S6, A-S7, A-S8, A-S9, A-S10, A-S11, A-S12]
flag: —
client_side: "no — git/gh CLI only"
authored: 2026-05-22
---

# R11A-MERGE — Auto PR + Auto Merge

## Context

Terminal entry in the R11.A queue. After all 13 implementation sessions PASS, the Conductor runs this entry to push the branch, open a PR to main, wait for CI, and auto-merge.

Per native ruling carry-forward from R11 v1 NATIVE_RULINGS §6: `requires_human_approval: false` is an explicit native override of the Wave 1 Conductor invariant "PR-to-main always human-gated". The override is local to R11 v2 phases.

## Files in Scope

Shell commands only. No source edits.

- Optional: `STREAM_R11A_COMPLETE.md` in `00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A/` summarizing close state.

## Acceptance Criteria

1. All 13 R11.A implementation sessions have `status: passed` in `session_queue_R11A.yaml`.
2. Amendment 5 deploy.yml coverage check passes:
   ```
   grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R11V2" platform/src --include="*.ts*" -o | awk -F: '{print $NF}' | sort -u
   grep -oE "NEXT_PUBLIC_MARSYS_FLAG_R11V2_[A-Z_]+" .github/workflows/deploy.yml | sort -u
   ```
   First set must be subset of second.
3. Branch pushed: `git push -u origin chat-v2/round11-a-foundation`
4. PR opened:
   ```
   gh pr create \
     --base main \
     --head chat-v2/round11-a-foundation \
     --title "feat(chat-v2): R11.A — Foundation (capability adapter substrate across 5 providers)" \
     --body-file 00_ARCHITECTURE/chat_v2_briefs/round11_v2/phase-A/R11A_PLAN_v1_0.md
   ```
5. Auto-merge enabled:
   ```
   gh pr merge --auto --squash --delete-branch
   ```
6. `STREAM_R11A_COMPLETE.md` authored with each session close-state + merge SHA when available.
7. `CAPABILITY_MATRIX.md` cells flip from 🚧 R11.A to ✓ R11.A (shipped DATE).
8. `MULTI_PROVIDER_PARITY_ROADMAP.md §5` updates R11.A row with close date + merge SHA.

## Gate command (Conductor)

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A

# Amendment 5 coverage
SOURCE_FLAGS=$(grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R11V2" platform/src --include="*.ts*" -o 2>/dev/null | awk -F: '{print $NF}' | sort -u)
YML_FLAGS=$(grep -oE "NEXT_PUBLIC_MARSYS_FLAG_R11V2_[A-Z_]+" .github/workflows/deploy.yml 2>/dev/null | sort -u)
for f in $SOURCE_FLAGS; do
  echo "$YML_FLAGS" | grep -q "^$f$" || { echo "FAIL: flag $f not in deploy.yml"; exit 1; }
done

# PR exists
gh pr view chat-v2/round11-a-foundation --json state,number 2>/dev/null | grep -q '"number"' || { echo "FAIL: PR not found"; exit 1; }

# Auto-merge enabled or already merged
gh pr view chat-v2/round11-a-foundation --json autoMergeRequest,state | grep -E '"state":"MERGED"|"autoMergeRequest":\{' || { echo "FAIL: auto-merge not enabled"; exit 1; }

echo "PASS: R11.A — branch pushed, PR opened, auto-merge enabled (or merged)"
exit 0
```

## Commit Template

No commits. This session opens a PR.

## Decision Log

*(Conductor sub-agent: paste branch push output, PR URL, auto-merge enable output, merge commit SHA when available, and updated CAPABILITY_MATRIX cell statuses.)*
