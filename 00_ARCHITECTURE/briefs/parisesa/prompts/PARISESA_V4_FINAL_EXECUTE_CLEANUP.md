# PARIŚEṢA-V4 — Execute the Three Authorized Cleanup Actions

The owner has explicitly authorized all three actions below, based on a prior
investigation (F-192 confirmed absent from origin; the two local-only commits
confirmed fully superseded by origin's closure record at seq 1098; the staged
`register_p1_aliases.ts` diff confirmed byte-identical to merged PR #1387,
F-125 already `SERVICE_CLOSED`). You do not need to re-ask permission for
these three specific actions — verify state before/after each one and report,
but proceed. Do **not** extend this authorization to anything else: no
DATA_PARKED/EXTERNAL_HOLD finding work, no watchdog/caffeinate reload, no
STOP.flag removal.

## Step 1 — Preserve F-192, then reset the state worktree

Run in `/Users/Dev/par-night/parisesa-v4-state`.

1. Confirm `UNRECORDED_FINDING_F192_PRESERVED.md` exists and is untracked
   (`git status`) before doing anything else. If it's missing, stop — don't
   proceed to the reset without it safely present.
2. `git fetch origin`
3. `git reset --hard origin/parisesa/campaign-state` — this discards the 2
   local-only commits and the 3 stale uncommitted file changes
   (`heartbeat.json`, `journal.ndjson`, `ledger.json`), matching this worktree
   exactly to origin's closed state (seq 1098). This does **not** remove
   untracked files, so the F-192 preservation file survives this step
   automatically — confirm that with `git status` immediately after.
4. `git log --oneline -3` — confirm HEAD is now `186a99879` (the owner-close
   commit).
5. `git add 00_ARCHITECTURE/briefs/parisesa/state/UNRECORDED_FINDING_F192_PRESERVED.md`
   and commit it alone, with a message making clear this is a preservation-only
   record, not new campaign work — e.g. "docs(parisesa): preserve F-192 (never
   recorded on origin) as a standalone note; campaign remains closed, no
   ledger/journal mutation." Do not touch any other file in this commit.
6. Push this one commit to `origin/parisesa/campaign-state`.
7. Confirm: `git status` is clean, `git log --oneline -2` shows your new
   commit directly on top of `186a99879`, and re-fetch to confirm origin now
   has it too.

## Step 2 — Discard the stray staged diff

Run in `/Users/Dev/par-night/parisesa-v4-conductor`.

8. `git status` — confirm the only change is the staged (not unstaged) diff
   on `platform-mcp/src/tools/register_p1_aliases.ts`, matching what the prior
   investigation found.
9. Discard it: `git restore --staged --worktree -- platform-mcp/src/tools/register_p1_aliases.ts`
   (if this git version doesn't support `restore`, use
   `git reset HEAD -- platform-mcp/src/tools/register_p1_aliases.ts` followed
   by `git checkout -- platform-mcp/src/tools/register_p1_aliases.ts` instead).
10. Confirm: `git status` shows a clean working tree, `git diff --cached`
    and `git diff` both empty for this file.
11. Do not touch the detached HEAD state itself (`cefb6077e`) — it was already
    confirmed content-safe (squash-merged via PR #1384) and nothing authorizes
    changing which commit this worktree points at. Leave it exactly as found
    otherwise.

## Final report

Confirm, in plain language: the new commit SHA from Step 1 (and that it's
live on origin), that the state worktree now matches origin plus that one
preservation commit, and that the conductor worktree's working tree is clean
with the stray diff gone. Note explicitly that no other files, findings, or
worktree state were touched.
