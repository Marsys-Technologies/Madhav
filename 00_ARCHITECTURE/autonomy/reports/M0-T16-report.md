# M0-T16 — MERGE `origin/main` INTO `campaign/nirmana-autonomous`

**Agent:** KĀRAKA-M0-T16 · **Task:** `WORK_QUEUE` `M0-T16` · **Authority:** ruling **D-93**
**Branch:** `campaign/nirmana-autonomous` · **Merge commit:** `016b0ccdc` · **Written:** 2026-08-23T18:38:17Z

**This is an observation report, not a verdict. I do not certify my own work (I16/H7).**
**I wrote nothing to `main` (H2). No rebase, no force, no squash, no history rewrite. No
`git checkout` was run in the shared tree (PARK-9). `platform/scripts/probe/ask.ts` was READ,
never RUN (P4).**

---

## 1 — The three things that matter, up front

1. **ZERO CONFLICTS. Not three — zero.** D-93 predicted a conflict surface of up to three files.
   Git auto-merged all three without a single conflict hunk. **I did not treat the clean exit as
   the answer**: each of the three was inspected against BOTH parents, and `probe/ask.ts` was
   read on both sides in full. §3.
2. **AND YET THE RATCHET WENT RED — WHICH IS THE REAL FINDING, AND IT IS EXACTLY THE FAILURE MODE
   D-93 PART 6 NAMED.** `check_entrypoint_guard_ratchet.py` was **exit 0 before the merge and
   exit 1 after**. Not one line of that came from a conflict resolution. **`main` contributed
   three new scripts carrying an unguarded top-level `main()`**, none of which exists on our
   pre-merge HEAD and none of which is in M0-T64's 76-file baseline. A semantic conflict between
   files git considers independent is invisible to a `--name-only` intersection; ADHIKĀRIN said
   the three-file count was a lower bound on difficulty, and it was. §5.
3. **THE ENTRYPOINT GUARD ON `probe/ask.ts` SURVIVED, AND I PROVED IT AGAINST BOTH PARENTS RATHER
   THAN BY GREP.** `git diff origin/main -- probe/ask.ts` shows our guard block whole and
   unmodified; `git diff <pre-merge-HEAD> -- probe/ask.ts` shows main's hunk and nothing else.
   Neither side was taken wholesale. Wave-1 guard tests: **74/74 before, 74/74 after.** §4.

---

## 2 — Pre-merge evidence (step a)

| item | value |
|---|---|
| branch (proven in the same shell as every git write, D-79) | `campaign/nirmana-autonomous` |
| pre-merge HEAD | `509b74a5e1ccc26e02b23aab04306f8f26af99e9` |
| `origin/main` tip after `git fetch` | `84c3c903578ee0cf6ce5830568859266810bbfd9` (2026-08-23T14:12:30Z) — **unchanged from ADHIKĀRIN's measurement**, so D-93 was ruled on the same two tips I merged |
| divergence | **27 behind / 396 ahead** (D-93 measured 385 ahead; the campaign grew 11 commits between the ruling and the merge, exactly as D-93 part 1 says it should) |
| `sha256(platform/scripts/probe/ask.ts)` before | `34a0599a8153484bb9e806030b35a360c768318795073c3311bc11c5de642d4b` |
| `sha256(platform/scripts/probe/ask.ts)` after | `e799c0d6191ea857b88ae7637dba4b50f628e4f601c3a0657465c6328655fbc3` |

**Working-tree state at step (a): `00_ARCHITECTURE/autonomy/state/.merge-lease` (mine, untracked)
and NOTHING ELSE.** The dispatch told me to expect `HEARTBEAT.jsonl` dirty; it was not — it had
been committed. **`CAMPAIGN_STATE.json` appeared dirty shortly after I took the lease.
SŪTRADHĀRA TOLD ME THIS EXPLICITLY, mid-task, before I could trip over it — I did not infer it.**
It is the conductor's file, it exists only on the campaign branch so `origin/main` cannot touch
it, and I neither staged, committed nor resolved anything in it. **No commit landed under me
during the lease.**

**The lease.** Taken as my first action (`state/.merge-lease`, agent name + `date -u`), released
as my last. No lease binary exists in `bin/`; the dispatch said so and I did not hunt for one.

---

## 3 — The three predicted conflicts, and why each auto-resolution is correct

**"Git did it" is not a reason. Each is stated on its merits.**

### 3.1 `.gitignore` — auto-merged, both-sides-added, disjoint

Main added `.codex/worktrees/`, `.codex/config.toml` (agent runtime state that can carry a live
MCP key) and `platform/scripts/probe/fixtures/p4k/*/report.json`. The additions sit in different
regions from anything our side carries; nothing contradicts.

**Why taking both is correct, not merely convenient:** the union of two ignore sets ignores strictly
more, never less, and **no added rule un-ignores anything another rule protects** — I checked for
negation (`!`) patterns in the incoming hunks; there are none. The riskiest direction for a
`.gitignore` merge is silently *un*-ignoring a credential path, and that direction did not occur.

### 3.2 `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_SWEEP_RESOLUTION_PLAN_v1_0.md` — did not conflict, and did not even require a content merge

It is not in the unmerged set and git printed no `Auto-merging` line for it, meaning the two sides
did not both present a changed blob to reconcile at this pair of tips. **No content from either
side was dropped** — the file is present and non-empty in the merged tree. I note honestly that
D-93 listed it in the both-sides-changed set; at the tips actually merged it required no
resolution.

### 3.3 `platform/scripts/probe/ask.ts` — THE ONE THAT MATTERED

**P4 posture, stated first:** the file was **read, never executed**. No logging was added, moved or
removed anywhere near its secret path. No secret value was read, printed, echoed or copied.
`DATABASE_URL` and every credential were used by the code, never displayed by me.

**What OUR side contributes** (M0-T65 / M0-T66, ruling D-74 part 1) — verified by diffing the
merged tree against `origin/main`:

- `import { isDirectEntrypoint } from '../lib/entrypoint'` (the ONE shared implementation, M0-T66)
- `export { isDirectEntrypoint }` — the module's public surface preserved
- the pre-existing `main().catch(…)` **moved inside**
  `if (isDirectEntrypoint(import.meta.url, process.argv[1])) { … }`, body unchanged
- the guard's full rationale comment block

**What MAIN's side contributes** — an unrelated scoping fix inside `tagConversationAsHarness()`.
Credential resolution and `Client` construction moved from above the `try` to **inside** it, with
`client?.end()` in the `finally`. Main's own comment gives the reason: `envOrSecret` shells out
when the env var is unset and **throws on any runner without gcloud auth**, so resolving it above
the guard killed an entire probe run over telemetry the function's own docstring calls
"best-effort". Main cites a live CI run that died this way after a successful turn.

**Why the auto-resolution is correct:** the two edits are **in different functions roughly 200
lines apart** and share no symbol, no control flow and no ordering constraint. Our guard governs
whether `main()` runs at module load; main's fix governs error scope inside a helper that only
runs once `main()` already has. **Neither side was taken wholesale** — both diffs confirm each
side's contribution is present in full and unmodified. **THE GUARD SURVIVED.**

**One honest observation on main's hunk, reported and deliberately NOT fixed (H3, D-41 part 2
direction test):** the `catch` returns `{ tagged: false, error: String(err) }`. That catch and
that `String(err)` **pre-existed on both sides** — main did not add them. What main's change does
is widen which errors reach it, now including `execSync` failures from the `gcloud secrets` call,
whose stringified error can carry the **command line** (i.e. a secret *name*, not a *value*). I did
not touch it. It is out of my grant and it is a Wave-2-shaped question, not a merge question.
**Flagging it, not fixing it.**

---

## 4 — Before/after measurement (steps b and e)

| check | BEFORE the merge | AFTER the merge | reading |
|---|---|---|---|
| Wave-1 guard suites (5 files: `destructive_entrypoint_guards`, `shared_entrypoint_module`, `migrate_entrypoint_guard`, `asset_registry_seed_entrypoint_guard`, `ledger_writer_worker_entrypoint_guard`) | **exit 0 — 5 files / 74 tests PASS** | **exit 0 — 5 files / 74 tests PASS** | **no regression. The guard was not silently dropped.** |
| `check_entrypoint_guard_ratchet.py` assertion (i) — no NEW unguarded `main()` | **exit 0. PASS.** 90 files with a top-level `main()`, 71 unguarded / 19 guarded | **exit 1. FAIL — 3 NEW unguarded.** 94 files, 74 unguarded / 20 guarded | **REAL new red, from main's content. §5.** |
| ratchet assertion (ii), the pawl | allowlist (71) ⊆ previous committed value (`HEAD^` `aa9c2ce4b`, 71) — did not grow | allowlist (71) ⊆ previous committed value (`HEAD^` `509b74a5e`, 71) — did not grow | **pawl GREEN both sides.** §6 — but read §6, its greenness on a merge commit is narrower than it looks |
| `tests/unit/migrations/migration_number_guard.test.ts` | **25/26, RED** — recorded in M0-T16's own `WORK_QUEUE` line, not measured by me | **exit 0 — 26/26 PASS** | **healed by the merge. §7** |
| `nirmana_catalogue_disclosure.test.ts` (known pre-existing red B/C/D/H) | 4 failed (documented) | **4 failed / 8 passed — unchanged** | **pre-existing red stayed red (H3).** I fixed nothing. |

---

## 5 — THE FINDING: three new unguarded `main()` entrypoints arrived from `main` (F-T16-1)

```
platform/scripts/probe/p4k_narration_analyzer.ts:376    [~ process.exit(]
platform/scripts/probe/p4k_sequence_driver.ts:193       [~ process.exit(]
platform/scripts/probe/post_deploy_behavior_smoke.ts:546 [~]
```

**Provenance measured per file, not assumed:** each is **absent from our pre-merge HEAD
`509b74a5e`**, **present on `origin/main` `84c3c903`**, and **absent from M0-T64's settled
76-file baseline** (zero occurrences in `entrypoint_ratchet_allowlist.json`). They are new work
that landed on main while the campaign branch was building the detector that catches them.

**This is the ratchet doing precisely its job.** Assertion (i) exists to fail on a NEW unguarded
top-level `main()`, and a merge from an upstream branch is one of the two ways new ones enter. It
did not need `--strict` and it did not need the allowlist.

**Why it did not show in D-93's three-file surface:** `git diff --name-only` over the both-sides
intersection reports files *both* sides changed. These three were changed by **one** side only, so
they are structurally invisible to that measurement while being exactly the kind of change that
breaks a whole-tree invariant. **ADHIKĀRIN's part-6 caveat was correct and load-bearing.**

**NOT FIXED, deliberately, on three independent grounds:** (a) repairing them is Wave 2, which my
dispatch forbids me to begin; (b) D-67 part 4 forbids adding anything to the allowlist, so
`--regenerate` is not mine to run — and M0-T68 built `--regenerate` to refuse exactly this;
(c) D-41 part 2's direction test — making a red thing green is presumptively out of scope.
**ROUTED TO ADHIKĀRIN. The decision is whether these three are a Wave-2 repair, a baseline
extension, or a `main`-side problem — and none of those three is a KĀRAKA's call.**

The pre-existing `.mts`/`.cts` NOTE (finding F-P: three `.mts` files outside the gated population
because M0-T64's baseline used a `.ts$` filter) is **unchanged by this merge** — same three files
before and after.

---

## 6 — THE PAWL ON A MERGE COMMIT: what it actually did (the measurement ADHIKĀRIN asked for)

**It ran, it was determined, and it was GREEN — and it is ONE-SIDED, which is the part worth
recording.**

```
merge commit 016b0ccdc
  HEAD^  (parent 1) = 509b74a5e  ← the CAMPAIGN branch, our pre-merge tip
  HEAD^2 (parent 2) = 84c3c903  ← origin/main
pawl output: allowlist (71) ⊆ its previous committed value (HEAD^ 509b74a5e, 71) — it did not grow.
```

**M0-T68 defined "its own previous committed value" as `HEAD^`, first parent. On a merge commit
`HEAD^` is parent 1 only.** So on this tree the pawl compared the allowlist against **the campaign
side and never looked at main's side at all.** Here that is harmless and the answer is right — the
allowlist file is byte-unchanged by the merge, so both operands are the same 71 and no growth is
possible in either direction.

**But the general shape is narrower than "green" suggests, and I am recording it rather than
grading it:** if `main` had ever shipped a *grown* allowlist, a merge commit's `HEAD^` would still
resolve to the campaign side, and the pawl would not compare against the value main brought. This
is **not a defect I observed firing** — the allowlist does not exist on `main` in a grown form and
this merge did not exercise the case. It is an **untested edge in a two-parent situation** that
M0-T68's three-case table (working-tree-dirty / clean-checkout / `--regenerate`) does not name.
D-89's own principle — a two-sided comparison needs an anchor on each side — arguably suggests a
merge commit has two "previous committed values" and the pawl consults one. **Filed as F-T16-2.
Undetermined, not red. ADHIKĀRIN's call whether it is worth an assertion.**

Also worth stating plainly: **the pawl was GREEN while the overall exit was 1.** The failure came
entirely from assertion (i). The two assertions are independent and reported independently, which
is what let me attribute the red to main's three files rather than to my resolution.

---

## 7 — The merge healed a red that was M0-T16's own stated reason to exist

`migration_number_guard.test.ts` was **25/26 red on this branch** — recorded in M0-T16's own
`WORK_QUEUE` line, because its baseline named a collision on `588_samiksha_digest_journal.sql`,
a migration that was on `origin/main` (PR #1497) but not visible to this tree. **It is now 26/26.**

**I want to be precise that this is not an out-of-scope fix under D-41 part 2.** I changed no code
and edited no test. The missing FILE arrived, and the test that was correctly complaining about its
absence stopped complaining. The red was a *consequence* of the drift this task was dispatched to
remove; removing the drift removed the red. **If PARĪKṢAKA reads this as a scope breach, the
evidence is that my diff touches zero test files and zero source files — the merge commit's entire
content is `origin/main`'s.**

---

## 8 — I14 (Track M is data-neutral)

**No asset data, no chart row, no registry row, no applied migration was changed.** Measured, not
asserted:

- **Migrations:** main brings **one new migration FILE**,
  `platform/supabase/migrations/588_samiksha_digest_journal.sql`, plus a
  `verification_artifacts/…/rehearsal_schema.sql`. **Neither is an edit to an already-applied
  migration** — 588 is a new file arriving, and it was already on `main`. **Nothing was run
  against any database.** No `migrate.ts`, no seed, no writer, no orchestrator.
- **Asset registry / seed / census data:** the merge's name-status contains **zero** files matching
  `asset_registry`, `seed`, or `census.json`.
- Main's 598 added / 41 modified files are predominantly `pariprashna` source, tests, route-port
  baselines and a STASH_ARCHIVE — inert with respect to chart data.

**This did not meet any of my abort criteria**, all three of which I checked explicitly: the
conflict set was not materially larger in a way that touches asset data or migrations (it was
*empty*); `probe/ask.ts` was resolvable without running it; and no resolution required dropping
the guard.

---

## 9 — What I did NOT do

- **No write to `main`.** No push at all. No PR, no merge to main, no force-push, no history
  rewrite anywhere (H2).
- **No `git checkout` in the shared tree** (PARK-9). No branch switch. Nothing needed one, because
  there were no conflicts to resolve by editing.
- **No rebase, no `--force`, no squash.** A real merge commit with two parents (D-93 condition d).
- **Did not run `platform/scripts/probe/ask.ts`** or any of wave 1's five repaired files (P4,
  D-74 parts 2/3).
- **Did not begin Wave 2**, did not repair any of the 71, did not touch `--strict`, did not
  regenerate any allowlist.
- **Did not fix** the three new unguarded files main brought, the `String(err)` widening in
  `ask.ts`, or any of the known pre-existing reds (3 × `no-explicit-any`, `prefer-const` in
  `asset_registry_seed.ts`, 3 × TS2344 in `dedupe_charts.ts`, 4 × `nirmana_catalogue_disclosure`).
- **Did not stage or commit** `CAMPAIGN_STATE.json`, `HEARTBEAT.jsonl`, `SPEND.jsonl` or the lease
  file. The merge commit's index is `origin/main`'s content and nothing else.

---

## 10 — Findings

| id | finding |
|---|---|
| **F-T16-1** | `origin/main` carries **three new scripts with an unguarded top-level `main()`** (`probe/p4k_narration_analyzer.ts`, `probe/p4k_sequence_driver.ts`, `probe/post_deploy_behavior_smoke.ts`), turning the ratchet red on merge. Outside M0-T64's 76 baseline. **Not repaired — ADHIKĀRIN's call.** |
| **F-T16-2** | **The pawl reads only parent 1 on a merge commit.** `HEAD^` is the campaign side; main's side is never consulted. Harmless on this merge (allowlist byte-unchanged, both operands 71) and **not observed failing** — but an untested edge M0-T68's three-case table does not name. |
| **F-T16-3** | **A `--name-only` both-sides intersection is a weak predictor of merge difficulty in the direction that matters.** It said three files; the actual conflict count was zero and the actual *damage* was a whole-tree invariant broken by three files only one side touched. D-93 part 6 predicted this class; this is a confirmed instance. |
| **F-T16-4** | `ask.ts`'s `catch` now receives `gcloud` `execSync` failures it previously could not, and returns `String(err)` — which can carry a command line naming a secret. Pre-existing code on both sides; main widened what reaches it. **Reported, not touched (P4 + H3).** |
| **F-T16-5** | (process) **The merge healed a red the task was dispatched to heal** (`migration_number_guard` 25/26 → 26/26) **and created a red nobody predicted** (the ratchet). Both were invisible to the conflict-surface measurement that authorised the timing. The measurement that decided *when* to merge could not have decided *whether* it was safe. |

---

## 11 — Certification

**NONE.** I performed this merge; I may not verify it (**I16 / charter H7**). Everything above is
an observation with the command that produced it. **PARĪKṢAKA decides.**

The specific things most worth an independent check: (a) that the entrypoint guard in
`platform/scripts/probe/ask.ts` is intact and semantically equivalent to M0-T65's, by **reading the
file** rather than trusting my two diffs; (b) that the three new unguarded files are genuinely
main's and genuinely new; (c) F-T16-2 — whether the pawl reading only parent 1 on a merge commit
is worth an assertion, which is ADHIKĀRIN's call and not mine.

**On (c)'s original form, and a correction I am recording rather than quietly fixing.** My first
draft of this section proposed checking "the merge introduced no edit of mine" by comparing
`git diff 509b74a5e 016b0ccdc` against `git diff 509b74a5e origin/main`. **That check is wrong and
I ran it before I noticed.** A two-way diff against `origin/main` also reports every file the
CAMPAIGN side added — they show as deletions in that direction — so the two sets differ by
hundreds of files for a reason that has nothing to do with correctness. It would have produced an
alarming-looking discrepancy that means nothing.

**The correct check, which I then ran:** a merge introduced no third-party content iff every file
in the result is byte-identical to at least one parent, except the files genuinely 3-way merged.

```
$ git diff --name-only HEAD^  HEAD | sort > /tmp/vs_p1
$ git diff --name-only HEAD^2 HEAD | sort > /tmp/vs_p2
$ comm -12 /tmp/vs_p1 /tmp/vs_p2      # differs from BOTH parents
.gitignore
platform/scripts/probe/ask.ts
```

**Exactly the two auto-merged files, and nothing else.** Every other file in the merge commit is
byte-identical to one parent or the other. Combined with §3.3's two directional diffs on `ask.ts`
— which show each side's contribution present and unmodified — this is the strongest statement I
can make that **the merge carries no content I authored**. (merge-base `6326cda7a`.)
