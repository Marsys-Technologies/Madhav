---
canonical_id: R11B_MERGE
session_id: R11B-MERGE
title: R11.B terminal — push branch, open PR, auto-merge to main
phase: R11.B — Look-and-Feel
depends_on: [B-S0, B-S1, B-S2, B-S3, B-S4, B-S5, B-S6, B-S7, B-S8]
flag: —
authored: 2026-05-22
---

# R11B-MERGE — Auto PR + Auto Merge

## Context

Terminal R11.B entry. Pushes branch, opens PR, auto-merges to main per NATIVE_RULINGS §6 override.

## Acceptance Criteria

1. All 9 R11.B implementation sessions PASS.
2. Amendment 5 deploy.yml coverage: `NEXT_PUBLIC_MARSYS_FLAG_R11B_*` flags from source are subset of deploy.yml --build-arg block.
3. Branch pushed: `git push -u origin chat-v2/round11-b-look-and-feel`
4. PR opened to main with R11B_PLAN as body.
5. Auto-merge enabled: `gh pr merge --auto --squash --delete-branch`.
6. CAPABILITY_MATRIX cells updated: R11.B-affected rows flip from 🚧 to ✓ R11.B.

## Gate command

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B
SOURCE_FLAGS=$(grep -rn "NEXT_PUBLIC_MARSYS_FLAG_R11B" platform/src --include="*.ts*" -o 2>/dev/null | awk -F: '{print $NF}' | sort -u)
YML_FLAGS=$(grep -oE "NEXT_PUBLIC_MARSYS_FLAG_R11B_[A-Z_]+" .github/workflows/deploy.yml 2>/dev/null | sort -u)
for f in $SOURCE_FLAGS; do echo "$YML_FLAGS" | grep -q "^$f$" || { echo "FAIL: $f not in deploy.yml"; exit 1; }; done &&
gh pr view chat-v2/round11-b-look-and-feel --json state,number 2>/dev/null | grep -q '"number"' &&
gh pr view chat-v2/round11-b-look-and-feel --json autoMergeRequest,state | grep -E '"state":"MERGED"|"autoMergeRequest":\{'
```

## Decision Log

*(Conductor sub-agent: paste PR URL + auto-merge enable output.)*
