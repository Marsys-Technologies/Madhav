# PARIŚEṢA-V4 — Close Out the Remaining Loose Ends (investigate + report, don't auto-fix)

The campaign itself is already closed by explicit owner decision (see
`RESUME.md` / journal seq 1098 on `parisesa/campaign-state` — read it first so
you have the same context). **This prompt is not a resume of campaign work.**
Do not touch, triage, or advance any `DATA_PARKED`/`EXTERNAL_HOLD` finding, and
do not reload the watchdog/caffeinate launchd jobs. Your job here is narrow:
three loose operational ends from the crash/recovery incident, each of which
needs investigation and a clear report — not a unilateral fix. Nothing in this
prompt authorizes discarding data, resetting git history, or force-pushing.
Where a step would be destructive or irreversible, stop and report instead of
doing it.

## Part 1 — The out-of-sync `parisesa-v4-state` worktree

Run this in `/Users/Dev/par-night/parisesa-v4-state`.

1. `git status` and `git log --oneline origin/parisesa/campaign-state..HEAD`
   (the 2 commits ahead) and `git log --oneline HEAD..origin/parisesa/campaign-state`
   (the 9 commits behind) — report both lists in full, don't summarize away
   any commit.
2. `git diff` on the uncommitted changes to `heartbeat.json`, `journal.ndjson`,
   `ledger.json` (the stale seq-1011 snapshot) — report what's actually
   different from a fresh checkout, in plain language, not just "3 files
   changed."
3. For the 2 local-only commits: read each one's actual diff
   (`git show <sha>`) and report whether it contains anything not already
   present on `origin/parisesa/campaign-state` at its current head (seq 1098)
   — i.e., is there any real content here that would be lost if this worktree
   were reset to match origin, or does origin's later work already supersede
   everything in these 2 commits?
4. **Do not run `git reset`, `git checkout --`, `git clean`, or discard
   anything.** Present the findings from 1-3 and stop. The decision to
   discard, cherry-pick, or reconcile this worktree is the owner's to make
   once they see what's actually in it.

## Part 2 — F-192 (exists locally, not on origin)

5. Locate F-192's full entry in this worktree's local `journal.ndjson` (the
   uncommitted/local-only version, not origin's). Quote its complete content
   verbatim — don't paraphrase a finding you're about to potentially preserve
   or lose.
6. Confirm it's genuinely absent from origin: check origin's `ledger.json`
   `findings` dict for an `F-192` key (it should not exist there, per the
   prior session's report — verify rather than assume).
7. **Do not append F-192 to the closed campaign's ledger/journal on
   `origin/parisesa/campaign-state`** — the campaign is closed, and adding a
   new finding there would be new work on a paused campaign, which is exactly
   what the owner's closure record says not to do without fresh authorization.
8. Instead, write F-192's full content to a standalone file, e.g.
   `00_ARCHITECTURE/briefs/parisesa/state/UNRECORDED_FINDING_F192_PRESERVED.md`
   in this worktree, so it survives and is easy to find later — but do **not**
   commit or push it without checking with the owner first, since even this
   is a judgment call about how "hands off the closed campaign" should be
   interpreted. Present the drafted file content and stop.

## Part 3 — The stray staged diff on `register_p1_aliases.ts`

Run this in `/Users/Dev/par-night/parisesa-v4-conductor` (confirm which branch
it's actually on first — a previous session found it in detached HEAD).

9. `git status` and `git diff -- platform-mcp/src/tools/register_p1_aliases.ts`
   — show the actual diff content in full.
10. Investigate provenance: `git log --oneline -- platform-mcp/src/tools/register_p1_aliases.ts`,
    check for any stash entries (`git stash list`) that might relate, and check
    whether this matches any known in-flight finding (F-125's
    `requiresOrientation`/B.11 orientation-gate work, per RESUME.md's own
    note) by reading F-125's ledger entry on origin for comparison.
11. Report: what the diff actually does, whether it looks complete or
    half-finished, and your best evidence-based read on whether it's safe to
    discard, safe to commit, or needs the owner's own judgment call. **Do not
    commit, stash-drop, checkout-discard, or otherwise act on this diff** —
    report and stop.

## Final report

One plain-language summary covering Parts 1-3: what each investigation found,
and for each of the three items, a clear recommendation plus an explicit
statement that no destructive action was taken and none will be without the
owner's own go-ahead on each one individually.
