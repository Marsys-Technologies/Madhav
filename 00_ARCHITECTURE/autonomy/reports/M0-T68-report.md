# M0-T68 — THE PAWL: the allowlist may only SHRINK, checked against its own previous committed value

**Agent:** KĀRAKA-M0-T68 · **Task:** `WORK_QUEUE` `M0-T68`
**Authority:** ruling **D-87** (the pawl; parts 1–6), with **D-71 part 7** / amended **SQ-29**
(the allowlist may only shrink), **D-67 part 4** (ratchet conditions), **D-39 part 2** / **D-73**
(a permanently-red gate is worse than none), **D-77** (mutation windows), **D-79** (branch proof),
and — landing mid-task and general by its own terms — **D-89** (a two-sided comparison needs an
anchor on EACH side).
**Branch:** `campaign/nirmana-autonomous` · **Written:** 2026-08-23T18:25Z
**Commits:** `bfe4ce659` (the pawl) · `93c88c8b8` (D-89's anchor on the current side)

**This is an observation report, not a verdict. I do not certify my own work (I16/H7).**
**I repaired none of the 71. I did not touch `--strict`. `set-password.ts` was never mutated.**

---

## 1 — The three things that matter, up front

1. **THE GATE NOW HAS TWO ASSERTIONS AND THE SECOND ONE IS THE PAWL.** (i) current population ⊆
   committed allowlist — unchanged, catches a NEW unguarded file. (ii) committed allowlist ⊆ **its
   own previous committed value**, read from git — new, and it is what catches an already-REPAIRED
   file returning. Proven A/B against **T66's shipped script on the identical tree**: the F-T
   attack commit is **exit 0 under the old gate and exit 1 under the new one** (§4.2).
2. **IT IS GREEN ON THE CLEAN TREE TODAY, WITH ALL 71 RESIDUAL ENTRIES PRESENT AND UNTOUCHED**, in
   the exact shape CI runs it (clean checkout ⇒ `HEAD` vs `HEAD^`). D-87 part 3's claim reproduces:
   (ii) never looks at the residual, only at the delta. No `--strict`, no permanently-red hazard
   (§4.1).
3. **I INTRODUCED D-89's OWN DEFECT WHILE IMPLEMENTING THE RULING THAT NAMES IT, AND IT WAS THE
   END-TO-END TEST THAT FOUND IT, NOT THE CODE READING.** My first anchor caught a *malformed*
   `files` key but not an *absent file* — because `load_allowlist` substitutes an empty list for a
   missing file, and an empty list is a well-formed operand. **Deleting the allowlist compared ∅ ⊆
   previous and PASSED.** §5.

---

## 2 — What changed

| file | change |
|---|---|
| `platform/scripts/governance/check_entrypoint_guard_ratchet.py` | +the PAWL section (assertion (ii)), its hermetic self-test (7 cases), the current-side anchor, `--regenerate` preconditions, reporting. +536/−14 then +110/−3. |
| `platform/scripts/governance/entrypoint_ratchet_allowlist.json` | **`$comment` only.** `files[]`, `count`, `paid_down`, `baseline_*` byte-identical — verified against `HEAD` by key-wise diff, not by eye. Written by `--regenerate`, never hand-typed (D-67 part 4). |
| `.github/workflows/nirmana-m0-guards.yml` | `fetch-depth: 2` on the ratchet job's checkout + the two comment blocks that now name assertion (ii). Job stays **blocking** (no `continue-on-error`). YAML re-parsed after editing. |

**Not touched:** `--strict` (D-87 part 2), any of the 71, any of wave 1's five repaired files, any
asset/registry/migration/credential, `main`, branch protection.

---

## 3 — The design question D-87 left open: where "its own previous committed value" comes from

**From git, never from the working tree, and which ref depends on what is being compared.** The
three cases are the three places this script actually runs:

| situation | previous value | why |
|---|---|---|
| working tree **differs** from `HEAD` (an agent has edited the list, not yet committed) | `HEAD` | catches the growth **before it is ever committed** |
| working tree **equals** `HEAD` — a clean checkout, i.e. **every CI run** | **`HEAD^`** (first parent) | comparing against `HEAD` here would compare a value with itself: vacuous, the exact shape the ruling exists to remove. On a `pull_request` run `HEAD` is the ephemeral merge commit and `HEAD^` is the **base branch tip**, so the assertion made is "this change may not grow the allowlist relative to the branch it merges into" |
| `--regenerate` (writing a new value) | `HEAD` | without this, `--regenerate` **is the exploit in one command** — see §4.3 |

If the path is absent at that ref, the lookup **walks back** to the newest ancestor commit that
carries it. Without the walk-back, deleting the allowlist in one commit and re-adding a grown one
in the next would present "no previous value" and read as a birth. Self-test case 5 pins it.

**What it assumes about CI, verified rather than inherited.** I read **this job's own checkout
step** (`.github/workflows/nirmana-m0-guards.yml`, the `entrypoint-guard-ratchet` job): it was
`uses: actions/checkout@v4` with **no `with:` block at all** — i.e. the shallow `fetch-depth: 1`
default, under which `HEAD^` does not exist. (M0-T67's finding that `deploy.yml`'s migrate job is a
full checkout says nothing about this job; I did not inherit it.) The job now sets `fetch-depth: 2`.

**And the assumption is not load-bearing on a comment.** If that line is ever removed, the guard
does **not** go quietly green: the pawl reports UNDETERMINED and exits 1, naming fetch-depth as the
likely cause. **An unavailable baseline is UNKNOWN, never clean** — §N.8, the shape M0-T66 applied
to unparsed files and the shape that caught M0-T67 when a reference went `null`. Proven, not
asserted: §4.4.

---

## 4 — Proofs. The negative directions are the ones that matter

Everything below ran against **an isolated git repo in scratch** built from copies of the real
script, the real allowlist and the real baseline, with **T66's shipped script extracted by
`git show 7372901d5:…`** (no checkout — D-79 part 4) sitting beside it so every claim is an A/B on
the *identical tree*. The stand-in at `platform/scripts/set-password.ts` in that repo is
**synthetic**: D-77 part 4 forbids mutating wave 1's five destructive/credential files, and a copy
of the real body with its guard stripped is exactly the artefact that rule exists to prevent.

### 4.1 — Green on the clean tree today, residual present (the required non-regression)

```
$ python platform/scripts/governance/check_entrypoint_guard_ratchet.py       # real repo, clean
  90 file(s) with a top-level main() under platform/scripts — 71 unguarded, 19 guarded.
  ratchet: 71 allowlisted of M0-T64's 76 baseline (5 paid down).
  pawl: allowlist (71) ⊆ its previous committed value (HEAD^ bfe4ce659, 71) — it did not grow.
  0 new unguarded top-level main(). PASS.                                            exit=0
$ python … --self-test
  SELF-TEST PASS (6 pass fixture(s) silent, 4 fail fixture(s) caught, 5/5 guard idioms
  exercised, 7 pawl case(s) proven in both directions).                              exit=0
```

Run **after** the commit, so the comparison really was `HEAD` vs `HEAD^` — the CI shape — and not
the dirty-tree shortcut.

### 4.2 — RED when a repaired file is re-added: PARĪKṢAKA's F-T, both halves

**Committed direction (the CI shape).** `C3` re-adds `platform/scripts/set-password.ts` to the
allowlist and commits it; working tree clean:

```
OLD (T66 shipped) · the attack commit                                    exit=0   ← F-T
NEW (T68)         · the attack commit                                    exit=1
  1 allowlist entry/entries are NOT in the PREVIOUS COMMITTED allowlist (HEAD^ 339079877,
  71 entries). THE ALLOWLIST MAY ONLY SHRINK … + platform/scripts/set-password.ts
```

and on that same tree, what each assertion says:

```
assertion (i)  new_violations              : []
assertion (i)  hand_added_allowlist_entries: []   ← SILENT: set-password IS in the settled 76
assertion (ii) pawl.added                  : ['platform/scripts/set-password.ts']   ← CAUGHT
assertion (ii) pawl.comparison             : HEAD-vs-parent HEAD^
```

**Uncommitted direction, in the real repo** (inside the announced D-77 window, allowlist restored
by `--regenerate` afterwards and the `files[]` re-verified identical): re-adding `set-password.ts`
to the working-tree allowlist → `exit=1`, `hand_added_allowlist_entries: []`,
`pawl.comparison: worktree-vs-HEAD`, `added_since_previous_commit: ['platform/scripts/set-password.ts']`.

**The other ordering — strip the guard first, allowlist untouched** — was already red and still is:
`1 NEW unguarded top-level main()` … `platform/scripts/set-password.ts:4 [~ void]`, both gates
exit 1. Assertion (i) is unchanged by this task.

### 4.3 — `--regenerate` was the third route, and it was the worst one

Strip a repaired file's guard, then ask the tool to rebuild the list: every name it adds is inside
the settled baseline, so assertion (i) has nothing to say.

```
OLD (T66) --regenerate   exit=0   "wrote … 1 allowlisted / 76 baseline / 75 paid down"
                                   set-password back on the list: True
NEW (T68) --regenerate   exit=1   REFUSING to regenerate — the scan would ADD 1 file(s) that the
                                   PREVIOUS COMMITTED allowlist (…, 71 entries) does not carry …
                                   file on disk after the refusal: 71 entries, unchanged
```

### 4.4 — The vacuous case, in the exact form CI would produce it

Not simulated — a real `git clone --depth N` of the isolated repo, on a tree where **everything
else is green**:

```
clone --depth 1 : commits=1  NEW exit=1   THE PAWL COULD NOT RUN — … `HEAD^` did not resolve …
                                          In CI this is almost always a SHALLOW checkout:
                                          actions/checkout@v4 defaults to fetch-depth 1 …
                                          UNKNOWN, never clean (§N.8) … FAILURE and not a skip.
clone --depth 2 : commits=2  NEW exit=0   pawl: allowlist (71) ⊆ its previous committed value …
```

That is the workflow's `fetch-depth: 2` proven **necessary and sufficient**, by measurement.

### 4.5 — Mutations: the detector can fail, and each failure names itself

Run on **copies** in scratch (the script is not hazardous when broken, but the copies cost nothing
and the real file's sha256 was re-verified identical afterwards).

| # | mutation | result |
|---|---|---|
| **M-A** | the pawl always reports OK — i.e. the state D-87 found | self-test **FAILS**: GROWTH, DIRTY and DELETE-THEN-READD each named |
| **M-B** | UNDETERMINED treated as clean | self-test **FAILS**: VACUOUS named |
| **M-C** | clean tree compared against `HEAD` instead of `HEAD^` — i.e. against itself | self-test **FAILS**: GROWTH + VACUOUS named |
| **M-D** | current side's anchor removed (D-89 (ii)'s one-sided mutation) | self-test **FAILS**: ABSENT-CURRENT named |
| **M-E** | "absent" collapsed back into "empty" in `read_current_side` — the real defect of §5 | self-test **FAILS**: CURRENT-SIDE named |
| **M-F** | `--regenerate`'s new UNPARSED refusal deleted | self-test **PASSES — NOT CAUGHT.** Disclosed, not implied: the self-test cannot safely invoke `--regenerate` (it writes the real allowlist), so that refusal is proven end-to-end in the isolated repo and has no fixture. |

### 4.6 — Assertion (i) still fires in the real tree

A temporary probe with an **indented** unguarded `main()` (D-71 7(d)'s named case) under
`platform/scripts`: `exit=1`, `1 NEW unguarded top-level main()` at
`_m0t68_probe_new_unguarded.ts:4 [if (process.env.ANYTHING) ~]`, while the pawl reported green in
the same run. Probe deleted; the following run is `exit=0`.

---

## 5 — The defect I introduced, and how it was caught

D-89 landed while I was working and is general by its own terms: *"a two-sided comparison requires
an anchor on EACH side independently … the test asserts BOTH extractions SUCCEEDED — non-null,
well-formed — BEFORE it compares them."* The pawl is a two-sided comparison. It anchored the
previous side from the first line. **It did not anchor the current one.**

My first fix anchored a *malformed* `files` key — and the end-to-end test showed it did nothing:

```
OLD (T66), allowlist DELETED : exit=0 — silently green
NEW (T68), allowlist DELETED : exit=0 — silently green    ← my anchor, not firing
```

Because `load_allowlist` substitutes `{"files": []}` for a missing file, and **an empty list is a
well-formed operand**. ∅ ⊆ previous is true, so the pawl passed on a deleted allowlist: D-89's
`null == null` shape, reproduced by me, in the file implementing the ruling that names it, within
the hour. Fixed by putting the absent/empty distinction in one function (`read_current_side`) with
self-test cases on **the derivation** rather than on the branch — case 6 alone would have passed
against the defective version, because it hands `None` in directly. After the fix:

```
NEW (T68), allowlist DELETED : exit=1   THE PAWL COULD NOT RUN — the CURRENT allowlist could not
                                        be read … CANNOT RETURN FALSE (D-89) … UNDETERMINED
```

**The lesson I would want carried forward is not "add anchors".** It is that the case-6 style test
— feed the failure value straight to the function and assert it reacts — is the test that agrees
with you. The one that found this fed the *system* the real-world event (delete the file) and
watched the exit code.

---

## 6 — What is PROVEN, and what is NOT

**PROVEN**

1. On the identical tree, T66's shipped gate exits 0 and this one exits 1 for: an allowlist that
   grew by a repaired file (committed **and** uncommitted), and a `--regenerate` that would put one
   back.
2. It is green on the real tree, clean, with all 71 residual entries present and `--strict` off.
3. `fetch-depth: 1` makes it fail loudly and `fetch-depth: 2` makes it pass — measured on real
   shallow clones, not reasoned.
4. Five of six mutations are caught and each names its own case; the sixth is disclosed as uncaught.
5. Assertion (i) and the unparsed/UNKNOWN behaviour are unchanged and still fire.
6. The allowlist's `files[]` is byte-identical to `HEAD`'s and was written by `--regenerate`.

**NOT PROVEN — and I claim none of it**

1. **That any of this gates a merge.** The job blocks a merge only once it is in the repository's
   **branch protection** required checks. That is a repo-settings change, it is not in the file, and
   I did not make it. M0-T66's F-R stands unchanged.
2. **That CI has ever run this workflow with `fetch-depth: 2`.** No workflow run was triggered by
   me. The depth behaviour is proven by local clones, which is the same question but not the same
   machine. Also: `push.branches` is `[main]` only, so the campaign branch's commits do not run this
   job at all (deliberate, per the workflow's own duplicate-trigger note) — the first real exercise
   will be the PR into `main`.
3. **That the pawl fires for a growth that lands without a run of the gate.** It fires **at** the
   growth commit. One commit later, `HEAD` and `HEAD^` both carry the growth and the gate is green
   again — I reproduced exactly that (§4.2's C3 followed by a no-change commit → `pass: true`). Two
   things mitigate it and neither is a proof: the PR into `main` compares against the base tip, so a
   growth anywhere on the branch is caught at the gate to `main`; and the **non-gating**
   `committed_history_growth_steps` observation names the growth commit on every subsequent run
   (verified: `! 8134b80ea added platform/scripts/set-password.ts`). Whether that observation should
   ever gate is ADHIKĀRIN's call and I did not make it one — a growth already in history stays in
   history, so gating it would be permanently red from the next commit, D-39 part 2 from the other
   side.
4. **That the allowlist cannot be widened by a sufficiently determined agent.** An authorized future
   growth (e.g. F-P's three `.mts` files) will make this gate RED at the commit that lands it. I
   deliberately built **no exemption flag and no bypass**: a "declared growth" field would be a hole
   with a ruling-id painted on it. The disposition belongs to ADHIKĀRIN.
5. **That the scanner is correct.** Unchanged from M0-T66, including its stated blind spots.

---

## 7 — What I did NOT do

- Did not touch `--strict`, in either direction (D-87 part 2).
- Did not repair, edit, or even read-modify any of the 71, and did not dispatch or begin Wave 2.
- Did not mutate `set-password.ts` or any of wave 1's five files — **D-77 part 4 requires copies**,
  and every reproduction used a synthetic stand-in in an isolated repo.
- Did not run `git checkout` in the shared directory (D-79 part 4); T66's shipped script was read
  with `git show`.
- Did not touch `main`, branch protection, asset data, a registry row, a migration or a credential.
- Did not weaken any existing check: the diff adds assertions and removes none.

## 8 — What I am unsure about

1. **Whether `HEAD^` is the right previous value on a `push` to `main` that is a fast-forward
   rather than a merge.** For a merge commit `HEAD^` is the previous `main` tip and the semantics
   are exactly right; for a squashed or fast-forwarded push it is the commit before, which is still
   "the previous committed value" but compares a narrower step. I could not construct the
   repository's real merge policy from the workflow file and did not guess.
2. **Whether the non-gating history observation will be read.** It is the only thing standing
   between a growth committed on a non-CI'd branch and silence, and non-gating output is exactly
   what D-39 part 2 says people learn to ignore. I would rather ADHIKĀRIN rule on it than have built
   it into a gate unasked.
3. **`HISTORY_SCAN_LIMIT = 200`.** Bounded so the guard's cost cannot grow with history; a growth
   older than 200 revisions of this one file would drop out of the observation. Arbitrary, and I
   have no measurement to justify the number.
4. **Whether `--regenerate`'s UNPARSED refusal belongs in this task at all.** It is the same defect
   class one path over and it is a strengthening (D-41's direction test: it makes something fail
   that previously passed), but it is not what D-87 asked for, it has no self-test case, and I am
   reporting it plainly rather than letting it ride inside a bigger diff.
