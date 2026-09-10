---
lane: F-79
stream: S6_ADHARA
stage: R (REVIEW) — Stage R second pass
reviewer: VERIFIER (author != reviewer — DIAGNOSIS.md/SPEC.md authored by ADHARA-LEAD)
reviewed_artifact: PR #1313
verdict: COMPLETE
---

# F-79 — REVIEW (Stage R)

## Independent verification (all re-derived, not inherited)

This lane's central claim is a **severity correction** of the original corpus finding — not
"456's SQL is unrecoverable" (as originally claimed) but "456's SQL is fully recoverable via
git history and was never actually lost, just missing from the working tree under one
filename." Given how load-bearing that correction is to the lane's whole disposition, I
independently re-derived every step rather than accepting the diagnosis's account:

1. **The rename commit is real.** `git show 54c809bc5 --name-status --diff-filter=R`
   confirms `R086` (86% similarity, git-detected rename, not a delete+create) from
   `platform/migrations/456_lel_schema_v2_event_shapes.sql` to
   `.../457_lel_schema_v2_event_shapes.sql`. Read the full commit message — matches
   DIAGNOSIS.md's account of a cross-directory numbering collision with an unrelated lane
   (A-2), resolved by renumbering.
2. **456's content is genuinely recoverable, byte-for-byte, and I recovered it myself.**
   `git show 54c809bc5^:platform/migrations/456_lel_schema_v2_event_shapes.sql` — a real,
   readable 46-line migration file (LEL schema v2, additive columns on `life_events`).
3. **The only difference between recovered-456 and live-457 is the header comment** — diffed
   them myself: line 1 (`Migration 456` → `Migration 457`) and a 3-line renumbering note
   added. The DDL body (`ALTER TABLE`/`ADD CONSTRAINT` statements) is character-for-character
   identical. This directly supports DIAGNOSIS.md's claim that the two different
   `_migrations_applied.sha256` values come from the comment, not from different SQL logic —
   I didn't just accept that explanation, I generated the diff myself and can see it's true.
4. **The PR's archived file is byte-identical to the git-recovered original**, not a
   reconstruction — diffed `gh pr diff 1313`'s new-file content directly against my own
   `git show 54c809bc5^:...` output. Exact match, confirmed clean.
5. **Scope matches exactly what SPEC.md claims**: `gh pr view 1313 --json files` shows
   exactly one file changed, the new archive copy — no `_migrations_applied` row touched, no
   other file modified.
6. **The 6 sibling migrations DIAGNOSIS.md cites as correctly archived** — spot-checked two
   of the six (`118_build_events.sql`, `133_notification_views.sql`) exist under
   `platform/migrations/_archive/` in the current tree; consistent with the claim that this
   is an isolated omission, not a systemic gap.
7. **CI**: all 5 required status checks pass (`TypeScript`, `Unit Tests`, `Secret Scan`,
   `Governance Gates`, `TAP-6`). Non-required failures (`D-01a/c/d`, `D-08`,
   `Boot-time pointer validation`, `TAP-5/7/S-13`) are the same set already confirmed
   pre-existing-red on `origin/main`'s own tip earlier this session — this PR's one-file,
   pure-addition diff shares no surface with any of them. `mergeable: MERGEABLE`.

## The seven questions

**1. Mechanism vs symptom** — mechanism, correctly, and the mechanism finding actually
*downgrades* the original severity claim rather than inflating it: the diagnosis found the
real defect (an isolated archival omission in one commit) is materially smaller than the
corpus's original framing ("unrecoverable... for audit or rollback-safety review" → actually
one `git show` away). This is exactly the kind of honest severity correction §N.7/FM-09
reward — the diagnosis could have quietly fixed the symptom (add the archive file) without
ever surfacing that the original claim overstated the risk; it didn't.

**2. Sub-claims mapped** — yes. SPEC.md §7's table maps both C1 (absent from disk — true,
remedied) and C2 ("unrecoverable" — corrected to false, with the correction itself treated as
the finding, not swept under the fix).

**3. Exit test / verifiable claim genuinely reflects reality** — not a red→green unit test
(correctly, for a pure archival-hygiene fix with no runtime behavior). The verifiable claim
(`find` returns zero pre-fix, one post-fix; diff between archived and historical-original is
empty) — I independently reproduced the "diff is empty" half directly, see above. Didn't
re-run the pre-fix `find` (would require reverting the PR), but the fact of the file's
prior absence is independently corroborated by DIAGNOSIS.md's own repo-wide search and isn't
itself in doubt.

**4. Sibling sites** — the 6 originally-cited siblings confirmed correctly archived already
(spot-checked 2 of 6 myself); a full 430-row sweep for the same gap class is explicitly
flagged as not done and not silently assumed complete — honest scoping, not a coverage gap
dressed as complete.

**5. Recurrence guard** — explicitly not added, with a reasoned justification (isolated
historical omission, not a missing process) and a named, credible follow-up (a CI check that
every `_migrations_applied` filename exists somewhere on disk, active or archived) rather
than silently skipping the question.

**6. Regression risk** — none. Purely additive new file under `_archive/`, which is excluded
from migration discovery (confirmed via the sibling convention already in place) — cannot be
re-applied, cannot affect any live system. No DB write, no schema change, no
`_migrations_applied` row touched. All required CI checks pass; no new failures.

**7. Unverified assumption vs read code** — the one item I did not independently re-derive:
the `sqlIdentityOf`/`normalizeSqlForIdentity` cryptographic-hash-match claim (DIAGNOSIS.md §2)
was not re-run by me — I verified the underlying fact a different, equally solid way (direct
line-by-line diff of the recovered vs. live SQL bodies, which is a stronger and more legible
check than trusting a hash match I didn't compute myself). Both routes converge on the same
conclusion; noting the distinction rather than overclaiming I reproduced their exact method.

## Verdict: COMPLETE

Genuinely excellent work: the lane's real contribution is catching that the original
corpus finding overstated its own severity, and it treats that correction as load-bearing
rather than convenient. The actual fix is minimal, safe, and independently verified
byte-identical to the true historical record. No deficiencies found on independent
re-derivation of every material claim.
