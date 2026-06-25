---
artifact: GIT_RECONCILE_MAIN_PROD_SYNC_v1_0.md
canonical_id: GIT_RECONCILE_MAIN_PROD_SYNC
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
purpose: >
  Comprehensive git reconciliation before the regenerate-everything run. Give a COMPLETE view of every
  clone, every worktree, and all uncommitted / unmerged / unpushed work on the machine; surface it for
  an explicit keep-vs-discard decision; clear out the cruft; and PROVE main == origin == production
  (web + Cloud Run job image). Discovery is read-only; nothing is discarded or force-changed until the
  native approves the disposition list.
audience: Claude Code (Antigravity)
---

# Git reconciliation → main == production

## §0 — Why this is careful
Earlier this session, the Cowork mount and the Antigravity repo were proven to be DIFFERENT clones —
fix SHAs reported by the executor weren't visible in the other clone. Stranded work hides in (a) other
clones of the repo on disk, (b) git worktrees, (c) uncommitted working-tree changes, (d) local
commits not pushed, (e) feature branches not merged. This brief inventories ALL of them before
anything is cleared. NOTHING is discarded, reset, or force-pushed until the native approves the
disposition list (Phase 2). Treat every "discard" as destructive.

---

## PHASE 0 — DISCOVER EVERYTHING (READ-ONLY — no writes, no checkouts, no resets)

0.1 — Find every clone of this repo on the machine:
```
# all .git dirs under the dev roots (adjust roots if needed)
find ~ -type d -name .git -not -path '*/node_modules/*' 2>/dev/null
# for each, show its remote + HEAD so duplicates/clones are obvious
for g in $(find ~ -type d -name .git -not -path '*/node_modules/*' 2>/dev/null); do
  d=$(dirname "$g"); echo "=== $d ==="; git -C "$d" remote -v | head -1;
  git -C "$d" rev-parse --abbrev-ref HEAD; git -C "$d" log --oneline -1; done
```
List every clone whose remote is the Madhav repo. The canonical working clone is
`/Users/Dev/Vibe-Coding/Apps/Madhav` — any OTHER clone of the same remote is a candidate for
consolidation or deletion (report, don't delete yet).

0.2 — Worktrees (run in EACH clone found in 0.1):
```
git -C <clone> worktree list --porcelain
```
List every linked worktree, its branch, and its path (the `.claude/worktrees/*`, `.claire/worktrees/*`
style dirs seen earlier). For each, note whether its branch is merged to main.

0.3 — Uncommitted work (each clone + each worktree):
```
git -C <path> status --short
git -C <path> stash list
```
Capture untracked files, modified-but-uncommitted files, and any stashes.

0.4 — Unpushed local commits (each clone/worktree, vs origin):
```
git -C <path> fetch --all --prune
git -C <path> log --oneline @{u}..HEAD 2>/dev/null      # commits ahead of upstream
git -C <path> log --oneline origin/main..HEAD 2>/dev/null
```
List every local commit not on origin.

0.5 — Unmerged branches (local + remote):
```
git -C <canonical> branch --no-merged main
git -C <canonical> branch -r --no-merged origin/main
```
For each unmerged branch, one line: ahead/behind counts vs main + last commit date + a 5-word summary
of what it is.

0.6 — origin/main vs local main vs production:
```
git -C <canonical> rev-parse main origin/main
# production commits:
gcloud run services describe amjis-web --region=asia-south1 --project=madhav-astrology \
  --format='value(spec.template.metadata.annotations)'   # find the deployed revision/commit
gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1 --project=madhav-astrology \
  --format='value(template.template.containers[0].image)'  # job image → digest → commit
```
Record: local main SHA, origin/main SHA, deployed WEB commit, deployed JOB-image commit.

DELIVER (Phase 0) — a single consolidated report:
- Table of clones (path, branch, HEAD, is-canonical).
- Table of worktrees (path, branch, merged-to-main?).
- Table of uncommitted/untracked/stashed work (path → files).
- Table of unpushed commits (path → SHAs → 1-line each).
- Table of unmerged branches (name → ahead/behind → date → what it is).
- The 4 SHAs: local main / origin/main / web-deployed / job-image-deployed, and whether they match.
STOP and report. Do NOT proceed to Phase 1 until the native has seen this.

---

## PHASE 1 — CLASSIFY (read-only; propose a disposition for each item)
For every item found in Phase 0, propose ONE disposition (the native confirms in Phase 2):
- **KEEP+MERGE** — real work that belongs on main (e.g. a fix branch not yet merged). → commit if
  loose, push, open/merge PR.
- **KEEP+COMMIT** — uncommitted work worth keeping → commit on the right branch, push.
- **DISCARD** — cruft, superseded experiments, throwaway worktrees, stale branches already shipped via
  a different commit → delete worktree / drop stash / delete branch / `git clean` untracked.
- **SECRET-RISK** — anything with a credential (e.g. `run_abhinandan_sensitive_nakshatra.py` hardcodes
  a DB password) → do NOT commit as-is; move secret to env or delete the file.
For DISCARD items, cross-check first: is the work already on main via a different SHA? (`git cherry`,
`git log --all --oneline | grep`-style content check). Only classify as DISCARD if its content is
already shipped OR the native confirms it's throwaway. Reversible-where-possible: prefer `git branch
-D` over worktree dir `rm` you can't undo, keep a `git bundle` backup of anything discarded that had
unique commits.
DELIVER (Phase 1): the disposition list (every item → KEEP+MERGE / KEEP+COMMIT / DISCARD / SECRET-RISK
+ a one-line reason + the reversal/backup note). STOP — native approves before any action.

---

## PHASE 2 — EXECUTE the approved disposition (only after native sign-off)
In the order: back up → keep → discard → sync.
2.1 — BACKUP: `git bundle create ~/madhav-reconcile-backup-$(date +%Y%m%d).bundle --all` in the
  canonical clone so nothing unique is unrecoverable.
2.2 — KEEP+COMMIT / KEEP+MERGE: commit loose work on the correct branch, push, merge to main (PR or
  fast-forward per repo norm). Run CI; keep main green.
2.3 — DISCARD: remove approved worktrees (`git worktree remove <path>` / `git worktree prune`), delete
  approved branches (`git branch -D` / `git push origin --delete`), drop approved stashes, `git clean
  -nd` (DRY RUN first, show output) then `git clean -fd` only on confirmed-cruft untracked files.
  SECRET-RISK files: scrub secret → env, or delete; never commit the plaintext credential.
2.4 — Consolidate to ONE canonical clone: if other clones of the remote exist and hold no unique work
  (proven in Phase 1), report them for the native to delete the directories (don't rm a whole clone
  dir without explicit ok).
DELIVER (Phase 2): what was committed/merged/pushed, what was discarded (+ the bundle path), final
`git status` clean on the canonical clone.

---

## PHASE 3 — PROVE main == production (the sync gate)
3.1 — `git -C <canonical> fetch && git rev-parse main origin/main` → local main == origin/main (push if
  ahead; if behind, reconcile).
3.2 — Resolve deployed WEB commit and JOB-image commit (Phase 0.6) → assert BOTH == origin/main HEAD.
  If either lags, trigger the deploy (web auto-deploys on push→main; the JOB image is a SEPARATE build
  — rebuild + push it from main HEAD and re-verify the digest→commit == HEAD).
3.3 — Full GREEN CI on main HEAD.
PARITY VERDICT (the clearance): local main == origin/main == web-deployed == job-image-deployed ==
green CI. Only a full match clears the gate. Record all SHAs.
DELIVER (Phase 3): the parity table (5 values, all equal) + green-CI link. This is the "main is in sync
with production, safe to proceed" sign-off.

---

## §4 — Guardrails
- Phase 0 + 1 are READ-ONLY. No reset/checkout/clean/delete/force-push until native approves Phase 1.
- BACKUP (git bundle) before any discard. Prefer reversible deletes; never `rm -rf` a clone/worktree
  with unique unpushed commits.
- NEVER commit a plaintext secret (the hardcoded DB password file).
- The canonical clone is `/Users/Dev/Vibe-Coding/Apps/Madhav`; reconcile others into it, don't fork
  work across them.
- This brief is git/deploy hygiene ONLY — it does NOT touch DB data or trigger any chart build. It is
  the gate that PRECEDES the bug-class audit + regenerate-everything run.
- Output the 5-value parity table as the final clearance artifact; the next step (full NATIVE_BIRTH
  bug-class sweep, then regen) starts only once this shows all-equal.
