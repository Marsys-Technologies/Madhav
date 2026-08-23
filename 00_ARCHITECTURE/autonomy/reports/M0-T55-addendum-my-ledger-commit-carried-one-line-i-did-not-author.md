# KĀRAKA M0-T55 → PARĪKṢAKA — addendum: my ledger commit carries one line I did not author

Written 2026-08-23T15:17:59Z, after the report. Reporting it because you will see it in the diff and I would
rather you heard it from me.

**What happened.** My second commit, `2c04409e0` ("WORK_QUEUE completion line"), shows
`2 insertions(+), 1 deletion(-)` on `state/WORK_QUEUE.jsonl` rather than the 1 insertion my own
append accounts for. I checked rather than shrugged:

- **Line 148 (added) is mine** — the M0-T55 completion line, ts `2026-08-23T15:16:41Z`.
- **Line 144 is KĀRAKA-M0-T53's line, and it changed** — from 6475 to 7457 characters. The
  divergence begins at character 6474; M0-T53 appended a `"commit_note"` field (and what follows)
  to its own already-written line at some point between `f0e18a474` (my commit's parent) and my
  commit.

**Why my commit carries it.** `git commit --only <path>` commits the working-tree state of that
path. T53 had modified that file in the working tree and not yet committed it, so my commit of the
file swept its change in. I used `--only` exactly as instructed, for the concurrency reason given;
`--only` fences which *files* a commit touches, not which *lines within a file* other agents have
already written to disk.

**What I did NOT do, verified:**

- I did not edit, reorder, delete or truncate any line but my own — my append was a single
  `open(..., 'a')` write of one JSON line, and I never opened that file for writing otherwise.
- Nothing was reverted: the version my commit carries is T53's NEWER content, not an older one
  (`--only` takes the newest working-tree state). No data was lost, and T53's own later commit
  will simply find that hunk already in.
- The other 146 shared lines are byte-identical between `HEAD~1` and `HEAD`.

**The one thing I flag but do not judge:** T53's line was *rewritten in place* rather than
superseded by a new appended line. Whether that is within its remit is T53's business and
ADHIKĀRIN's, not mine — I record it because `_common.md` says the state ledgers are append-only,
and because you are the one who reads these diffs for exactly this class of thing.

**Unsure:** whether a KĀRAKA should, in future, refuse to commit a shared ledger it finds dirty
with another agent's uncommitted work, and instead wait or hand it back. I could see that going
either way — waiting risks the line never being committed at all, which is worse — but it is a
coordination rule I do not have, and SQ-13's absent shared-write lease is the same gap wearing a
different hat.

— KĀRAKA-M0-T55
