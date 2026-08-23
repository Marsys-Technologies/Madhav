# M0-T67 — HELD MID-TASK. `migrate.ts` reverted, then restored on SŪTRADHĀRA's pause; second eyes on V-55 angle 3 filed instead.

**Agent:** KĀRAKA-M0-T67 · **Task:** `WORK_QUEUE` `M0-T67`
**Authority:** ruling **D-83** (revert + put the retained copy under the divergence detector),
deciding fact **D-69** (CAMPAIGN BOUNDARY 1), bound by **D-77** (mutation windows) and **D-79**
(prove the branch)
**Branch:** `campaign/nirmana-autonomous` · **Written:** 2026-08-23T17:56Z
**Status: HELD, not complete.** `platform/` is clean; not one byte of `platform/` is committed.

**This is an observation report, not a verdict. I do not certify my own work (I16/H7).**
**I did not run `migrate.ts`. I did not apply, inspect or touch any migration.**

---

## 1 — What happened, in order

1. Read the binding set: `_common.md`, `karaka.md`, `CHARTER.md` §3, the `M0-T67` queue line,
   **D-83 in full**, **D-69**, **D-77**, **D-79**, `M0-T66-report.md` §7.1, `M0-T65`'s suite.
2. Established a **green baseline**: the three entrypoint suites, **63/63 pass**.
3. **Applied the revert** to `platform/scripts/migrate.ts` (part 1 of the task).
4. Verified it, and ran the suites: **2 failed / 61 passed**, and the two failures were exactly
   the two I predicted (§4.3).
5. **SŪTRADHĀRA's pause arrived** — PARĪKṢAKA's V-55 angle 3 closes the item by a route nobody
   had named (static module-resolution proof), which goes to D-83's factual predicate.
6. **Restored `migrate.ts` to the HEAD blob and proved the restore** (§2). Re-ran: **63/63**.
7. Spent the hold doing the one thing that is worth more than waiting: **independent second
   eyes on V-55 angle 3**, read-only. Filed to
   `mailbox/to_conductor/20260823T175400Z-M0-T67-second-eyes-on-V55-angle3.md`.

**Part (2) of the task — adding the retained local copy to M0-T65's divergence test — was never
started.** No test file was edited. I reached the pause before touching one.

---

## 2 — Tree state, sha-proved, one shell invocation

```
PRE-RESTORE  worktree sha256  fe765d82ebb0ef134625ee19d7681f4e6f25d5872e3e2df1d68336221b725d57
HEAD blob    sha256           0c4ddc8d1fd706a0a6d0be2516650c01c6795f42a77b872ffa813450ce161e06
POST-RESTORE worktree sha256  0c4ddc8d1fd706a0a6d0be2516650c01c6795f42a77b872ffa813450ce161e06
git rev-parse --abbrev-ref HEAD → campaign/nirmana-autonomous
git status --porcelain -- platform/ → (empty)
vitest ×3 entrypoint suites → 63/63, identical to the pre-change baseline
```

**No D-77 mutation window was ever opened.** My only edit was the revert itself; it was a
complete, valid, compiling state at every moment, and it no longer exists. Nothing was broken
on purpose, so there was nothing to announce.

**D-79 observed:** the branch was proved in the same invocation as the restore, and again in the
same invocation as the commit of this report.

---

## 3 — Second eyes on V-55 angle 3 (the substance of the hold)

Full detail in the conductor mailbox file. The short form:

**I agree with PARĪKṢAKA, and I reached it by a different route.** Replicated exactly: **248**
extensionless relative imports under `platform/scripts` (same number), and **all eight** rewired
files bundle under `esbuild --bundle --platform=node --format=esm --packages=external` with
`rc=0` and zero unresolved — with a **negative control** proving that detector can say
"Could not resolve", so the eight greens are earned.

Three things V-55 (as quoted to me) did not report:

- **I probed tsx's OWN resolver**, which is what the deploy actually runs — `esbuild --bundle` is
  a *different* resolver and is corroborating, not identical. In a `/tmp` directory with **no
  tsconfig at all**, this repo's `tsx` resolved `'./lib/entrypoint'` → `lib/entrypoint.ts`
  (exit 0), and failed loudly on a missing one (`ERR_MODULE_NOT_FOUND`, pipeline exit 1 under
  `pipefail`). A tsconfig-free directory resolving it means **tsconfig cannot be what makes it
  work, so `tsconfig.json:33`'s `exclude` cannot be what breaks it.**
- **The deploy's `migrate` job is a full `actions/checkout@v4`** — no image build, no artifact
  packaging. The hazard I went hunting for first was *presence* (does a brand-new file even ship?),
  not resolution. The checkout closes it.
- **The feared failure mode is already detected.** D-83 weighed this change against §N.4's
  "migrations silently doing nothing while the deploy reports success". An unresolved import kills
  tsx **before user code runs**: no output, non-zero exit. `deploy.yml`'s `set -o pipefail` fails
  the step on the exit code, M0-T44's `MIGRATE_RUNNER_COMPLETE` grep fails it independently, and
  `deploy-web` gates on `needs: [migrate]`. The worst case is **loud and blocking on the first
  deploy**, not silent.

**And one new finding that cuts the other way — F-T67-1.** Before M0-T66, **no `npx tsx` step in
`deploy.yml` resolved a single relative TypeScript import**: `dispatch_gate.ts` has none,
`verify_migrations_deployed.ts` has none, `migrate.ts` now has exactly one. So "the tree already
does this 248 times" is true of *the tree* and **not of the deploy job**. I do not think it
overturns the above, but it is the honest residue and it is the strongest surviving form of
T66's original worry. **F-T67-2:** `deploy.yml:324` installs `tsx` **unpinned** — pre-existing,
but M0-T66 is what makes tsx's resolver semantics load-bearing at deploy time for the first time.

---

## 4 — What I established about the revert, for whoever resumes

### 4.1 — The revert is mechanically exact, and the divergence assertion would be green on day one

Restoring the pre-T66 predicate produces a body **byte-identical (423 bytes) to the certified
copy M0-T66 removed**, and it **normalises equal** to `scripts/lib/entrypoint.ts`'s reference
under M0-T65's own `predicateBody()` (which strips `fs.`/`path.` qualifiers; 423 − 412 = the 11
bytes of `fs.`×2 + `path.`×1). So D-83 part 4's divergence assertion needs neither side adjusted
to fit — measured, not assumed.

### 4.2 — T66's "three-line change" is right about edit SITES, not about lines

I was told to verify this rather than assume it, so: the forward T66 diff on `migrate.ts` was
**16 insertions / 31 deletions**; a bare mechanical revert is ~31/16 across exactly **3 hunks**
(add the `fileURLToPath` import, drop the shared import, swap the comment block for the
function). **Three places, not three lines** — a ~47-line diff. This does not change the
difficulty; it is still trivial and still exact. I record it only because a decision costed at
"three lines" should know its actual size.

### 4.3 — Both detectors are non-vacuous about `migrate.ts` specifically, and they proved it

With the revert applied, **exactly two** tests went red out of 63, and they were the two I
predicted before running:

| suite | test | why |
|---|---|---|
| `destructive_entrypoint_guards.test.ts` | *"the shared predicate is readable, and NOBODY else defines one"* | its `FORMER_COPIES` names `scripts/migrate.ts` |
| `shared_entrypoint_module.test.ts` | *"scripts/migrate.ts imports and re-exports the shared predicate, and defines none of its own"* | derived `CONSUMERS` |

This is real evidence and it is worth keeping regardless of the ruling: **both suites noticed a
change to `migrate.ts`'s predicate the moment it happened.** That is exactly the property D-83
part 4 wanted guaranteed, demonstrated by observation rather than argued.

### 4.4 — `migrate.ts` is not one of D-77's five, but I judge it equivalent

D-77 part 4's five are `_archived/seed-abhisek.ts`, `dedupe_charts.ts`, `dev/mint_session_cookie.ts`,
`probe/ask.ts`, `set-password.ts` — I derived that list from `M0-T64-triage.json`, not from memory.
`migrate.ts` is not among them, **but it is the archetype of the class D-77 was protecting**
(importing it used to apply migrations to production — ruling D-9's founding incident). Under
D-77's own "any file a KĀRAKA judges equivalent" clause I judge it equivalent. **So if I resume,
the RED proof for the divergence detector runs on a COPY, never in place** — the mutated bytes
will never touch `platform/scripts/migrate.ts` on disk.

### 4.5 — The vacuous-case check, which survives either ruling

`destructive_entrypoint_guards.test.ts:204` already asserts `expect(referenceBody).toBeTruthy()`
— the anchor that caught M0-T66 when its reference went `null`. **It protects only the reference
side.** Any assertion of the form `expect(predicateBody(read(LOCAL))).toBe(referenceBody)` passes
vacuously when **both** sides are `null`, and the current anchor would not catch that. The check
I would write asserts **both** sides truthy, both non-trivially long, and adds a **paired mutation
control** (real bytes, drifted, on a copy) proving the comparator can return false. If D-83 is
revised and there is no retained copy to watch, **the "both sides, not one side" widening still
applies** and I would file it as a small standalone follow-on rather than lose it.

---

## 5 — What I did NOT do

- **Did not run `migrate.ts`.** Did not apply, inspect, or query any migration. Did not open a
  DB connection. I never went looking for pending migrations, because finding out would have
  required exactly the execution the brief forbids.
- **Did not touch the other seven consolidated files, `lib/entrypoint.ts`, or the ratchet.**
  (I read the ratchet to confirm it has no dependency on the shared-import shape — it gates on
  guarded `main()`, not on where the predicate lives. Read-only, no edit.)
- **Did not edit any test file.** Part (2) was never started.
- **Did not commit anything under `platform/`.** This report and the mailbox finding are the
  only committed artefacts.
- **Did not run `git checkout <branch>`** anywhere (D-79 part 4). `git checkout -- <path>` was
  used once to restore a file; it does not move HEAD, and the branch was proved before and after.
- **No `tsc` was run**, and I want to be explicit rather than let silence imply coverage:
  `platform/tsconfig.json:33` excludes `scripts`, so **no project-`tsc` green would be evidence
  about `migrate.ts` at all.** My evidence is `esbuild` resolution, a live `tsx` resolver probe,
  and vitest — **type coverage for `scripts/**` is ABSENT**, and that is a property of the repo,
  not of this task.

---

## 6 — What I am unsure about

1. **Whether §3's "the failure is already loud" argument is as strong as it reads.** It leans on
   `pipefail` **and** M0-T44's sentinel grep — and **that grep is itself inside D-69's
   unverifiable set** ("the anchored sentinel grep behaves under GNU grep on ubuntu-latest"). My
   defence is that the **exit-code** path is independent of grep semantics entirely, so loudness
   survives even if the grep behaves differently. I believe that; I also do not want it read as
   clean when one of its two legs has an open boundary item against it.
2. **Whether my tsx probe generalises to the runner.** I ran **tsx v4.21.0 on Node v24**; the
   runner is **Node 20** with an **unpinned** tsx. Extensionless-`.ts` resolution is tsx's core
   advertised behaviour and 248 files here depend on it — but it is a different Node major than
   the one that matters, and I could not test the one that matters. Same class D-69 named; I am
   not re-opening it, I am naming which of my own evidence sits inside it.
3. **Whether reporting agreement is worth anything.** I was asked to be a second pair of eyes and
   I went in expecting to find a gap (file presence). I did not find one. I report that as a
   result of looking from a different angle, not as agreement-by-default — but a reader should
   weight it knowing I found no disagreement, which is weaker evidence than finding one.
4. **Whether I should have paused before applying the revert at all.** I applied part (1) before
   the pause arrived, exactly as briefed, and the restore is sha-proved — so nothing was lost.
   But the window between "KĀRAKA edits a production-path file" and "the coordinator learns
   something that moots it" is real, and this is the second time today an interaction cost has
   shown up in the gap between two correct behaviours.

**I am holding. I will resume exactly as briefed if D-83 is upheld, or file §4.5's follow-on and
stand down if it is revised.**
