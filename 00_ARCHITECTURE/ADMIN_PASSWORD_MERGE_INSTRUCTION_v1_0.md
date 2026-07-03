---
artifact: ADMIN_PASSWORD_MERGE_INSTRUCTION
canonical_id: ADMIN_PASSWORD_MERGE_INSTRUCTION
version: 1.0
status: READY
target_executor: Claude Code in Antigravity
date: 2026-06-25
purpose: Merge the already-built in-portal password feature into main so localhost serves it
---

# Merge `feature/admin-password-mgmt` → `main`

## Context
The in-portal password feature (set password at creation + "Set password" Actions
menu item) was built, tested (4,607 passing), and committed on
`feature/admin-password-mgmt` — but never merged. localhost runs `main`, so the
"Set password" option doesn't appear yet. This merge fixes that. **No migration
is involved** (verified: the feature touches no file under `platform/migrations/`).

## Pre-flight (verified from Cowork, re-confirm before merging)
- `main` is only 1 commit ahead of the branch, and that commit is a **docs file
  only** (`ADMIN_PASSWORD_MANAGEMENT_BRIEF`). No code divergence → clean merge.
- The `main` working tree has **unrelated uncommitted/untracked files** (conductor
  logs, build-tracker briefs). **Do NOT commit or stash-pop these into the merge.**
  Leave them exactly where they are.

## Steps

```bash
# 1. Make sure you're on main with the unrelated dirty files left alone.
git checkout main
git status            # confirm only the unrelated conductor/build-tracker files are dirty

# 2. Merge the feature branch. Expect a clean merge (no code conflicts).
git merge --no-ff feature/admin-password-mgmt -m "merge(admin): in-portal password management (set-at-create + Set password action)"

# 3. If git reports a conflict ONLY in platform/src/app/api/admin/users/route.ts,
#    it is a false alarm from identical content — open it, confirm there are no
#    <<<<<<< markers left, and that both the password-on-create logic AND any
#    existing main logic are present. Then:  git add <file> && git commit --no-edit
#    (In the verified state there should be NO conflict at all.)
```

## Verify on localhost (dev server already running on main)
The dev server hot-reloads after the merge. Then, in the browser:

1. `/admin?tab=users` → open the **Actions** menu on any non-self user.
   - **PASS:** a **"Set password"** item appears (placed just above "Send
     password reset link").
2. Click **"Set password"** → the SetPasswordDialog opens with Password + Confirm
   fields and a show/hide toggle. Entering < 8 chars or mismatched confirm is
   blocked client-side.
3. Click **+ New User** → the dialog now has an optional **"Initial password"**
   field with helper text "Min 8 chars. Leave blank to send a reset link instead."

If all three show, the merge succeeded and the feature is live on localhost.

## Notes
- Reminder for later (NOT part of this merge): the FIRST admin overhaul's
  migrations **332** (`profiles.updated_at`) and **333** (`admin_audit_log`) must
  be applied to **prod** surgically (psql via the Cloud SQL proxy, never bulk
  migrate.ts). Until then, disable/enable/edit and the audit log won't work in
  prod — but this does not affect the password merge or localhost.
- This branch needs no migration of its own, so once merged it ships with a normal
  deploy.

*End ADMIN_PASSWORD_MERGE_INSTRUCTION v1.0.*
