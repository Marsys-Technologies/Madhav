# M0-T65 — WAVE 1 of F-4 tier 1: entrypoint guards on the five destructive-on-import scripts

**Agent:** KĀRAKA-M0-T65 · **Task:** WORK_QUEUE `M0-T65` · **Authority:** ruling **D-74 part 1**
**Branch:** `campaign/nirmana-autonomous` · **Written:** 2026-08-23T16:53:15Z
**This is an observation report, not a verdict.** I do not certify my own work (I16/H7).

---

## 1 — Outcome in one line

**All five repaired with `isDirectEntrypoint`, and none of the five was executed — not once, not
"just the import", not with a stub env.** Verification is deliberately split into a structural half
over the real files and a behavioural half over a harmless stand-in I wrote. **I could not prove any
of the five actually fires its guard at runtime, and I do not claim it.** §5 states exactly which
properties are proven and which are not.

I read each file before applying the pattern. All five fit M0-T60's derivation: their hazard is
**RUNNING when they should not**, so the safe default is **DO NOT RUN** (A3.4 operator rule 5).
**None of them needed a deviation from the default idiom**, so D-74 part 5's prove-and-flag route
was not used.

---

## 2 — What each file does, read not assumed (the per-file hazard, D-67's criterion)

| File | What `main()` does on an incidental import | tier-1 because |
|---|---|---|
| `platform/scripts/probe/ask.ts` | `execSync`s `gcloud secrets versions access` / `firebase apps:sdkconfig` when env vars are unset, authenticates as `PROBE_UID`, POSTs a question at `DEFAULT_SERVICE_URL` (a **production** Cloud Run URL), `UPDATE conversations SET title`, writes a transcript into `scripts/probe/out/`; 5 `process.exit` paths | a + c |
| `platform/scripts/dedupe_charts.ts` | re-points every FK to `charts`, then `DELETE FROM charts WHERE chart_id = $1` per duplicate (line 196). `--apply` is read from `process.argv` at **module scope** (line 38), so an importer carrying `--apply` in its own argv committed the deletes; `process.exit(1)` in the tail | a + c |
| `platform/scripts/_archived/seed-abhisek.ts` | `INSERT … ON CONFLICT (id) DO UPDATE SET role='super_admin'` (line 196), inserts a `charts` row (the duplicate-chart hazard it was archived for), `pyramid_layers`, `documents`, uploads to GCS | a + c |
| `platform/scripts/dev/mint_session_cookie.ts` | mints a Firebase custom token for `SUPER_ADMIN_UID`, exchanges it over the network, POSTs to `${SERVICE_URL}/api/auth/session` (default localhost, routinely pointed at prod), writes the `__session` cookie to stdout or to the path in `COOKIE_OUTPUT_FILE`; 4 `process.exit(1)` paths | a + c |
| `platform/scripts/set-password.ts` | `auth.updateUser(uid, { password })` against the `SUPER_ADMIN_EMAIL` account — a live credential **mutation**. Both inputs resolve at module scope (lines 15, 18 — the latter from `process.argv[2]`) | a + c |

That matches `M0-T64-triage.json` exactly for all five (`tier: 1`, `tier1_because: "a+c"`).

**Direction test, per file, done individually rather than inherited:** for every one of the five the
cost of *running wrongly* is a live mutation or a credential acquisition, and the cost of *not
running* is that a human's explicit `npx tsx …` prints nothing and does nothing — loud, recoverable,
and repeatable. `IMPORT_ONLY` (default = RUN on any load) would have been actively wrong for all
five, for M0-T60's reason. Nothing here is a gate.

---

## 3 — What I changed

**Five files repaired** (each: three node-builtin imports added or extended, an exported
`isDirectEntrypoint`, and the existing top-level `main().catch(…)` moved inside the guard —
**its body unchanged**, so direct-run behaviour is byte-for-byte what it was):

- `platform/scripts/probe/ask.ts`
- `platform/scripts/dedupe_charts.ts`
- `platform/scripts/_archived/seed-abhisek.ts` — **repaired, not deleted** (D-74 part 3)
- `platform/scripts/dev/mint_session_cookie.ts`
- `platform/scripts/set-password.ts`

**Two files added:**

- `platform/scripts/__tests__/destructive_entrypoint_guards.test.ts` — 37 tests, three sections.
- `platform/scripts/__tests__/fixtures/entrypoint_guard_standin.fixture.ts` — the harmless
  stand-in. `.fixture.ts` so vitest does not collect it as a suite.

The predicate body is **textually identical in all five** and identical to the certified copy in
`scripts/seed/asset_registry_seed.ts` (and, after stripping `fs.`/`path.` namespace qualifiers, to
`scripts/migrate.ts`'s original). It is **mirrored, not imported** — D-9 forbids importing from
`migrate.ts`, and none of these five may acquire a module graph it did not have.

---

## 4 — How I verified WITHOUT executing any of the five

D-74 parts 2 and 3 forbid running them. The proof is split, and the split is stated in the test
file's own docstring so a later reader cannot mistake one half for the other.

**§1 STRUCTURAL — over the five real files' source text.** Per file: no unguarded top-level `main()`
call; exactly one `main()` invocation and it sits after the guard line; the guard is the exact
`if (isDirectEntrypoint(import.meta.url, process.argv[1])) {` form, present exactly once; no
`IMPORT_ONLY` and no `NODE_ENV`-keyed entrypoint form; the `isDirectEntrypoint` body equals the
certified reference; the file's last non-blank line is the guard block's `}`.

**§2 BEHAVIOURAL — over the stand-in only, never the five.** Five subprocess cells under this repo's
own `tsx`, from a `platform/scripts/**` ESM `.ts` file, env constructed from scratch (never spread
from `process.env`): side-effect import with `NODE_ENV` unset → does not run, exit 0; import with
`NODE_ENV=test` → does not run, exit 0; direct run → runs; direct run under `NODE_ENV=test` → runs
(the cell the retired sentinel got wrong); `./`-prefixed direct run → runs.

**§3 THE DETECTORS THEMSELVES — paired positives, so §1 cannot pass vacuously.** The same helpers
are run against inline samples: an unguarded top-level `main()` is rejected; an **indented**
unguarded `main()` is rejected (the case a column-0 grep misses); the guarded shape is accepted;
`predicateBody` returns null where there is no predicate and differs where a body differs. Plus the
predicate's own unit cases against the stand-in (true on a genuine direct path, false on `undefined`
and on a malformed URL).

```
$ npx vitest run --project node scripts/__tests__/destructive_entrypoint_guards.test.ts
  Test Files  1 passed (1)        Tests  37 passed (37)
```

### 4.1 — Mutation proofs (D-41 part 3 standing requirement)

| # | Mutation | Result |
|---|---|---|
| **M1** | strip the guard from `set-password.ts`, restoring its exact pre-repair tail | **4 failed**, all in that file's §1 block; nothing else moved. File restored **byte-identical** (sha256 `3bcfe4a4…` before and after) |
| **M2** | stand-in predicate always **false** (signal never fires) | **4 failed** — C, D, E and G |
| **M3** | stand-in predicate always **true** — **the inverse direction**, fires when it must not | **suite failed to load**: `Error: process.exit unexpectedly called with "7"` at the stand-in's guard line. Restored byte-identical (sha256 `7afeff28…`) |
| **M4** | one operator flipped inside `probe/ask.ts`'s predicate body (`===` → `!==`) | **1 failed** — that file's body-equality test, and only it. Restored byte-identical (sha256 `e454764b…`) |

**M3 is the direction that matters** — "fires when it should not" is precisely this class's hazard —
and I am flagging honestly that it is detected as a **suite-load failure, not a named failing test**:
the in-process import of the stand-in evaluates it, the always-true guard runs `main()`, and
`process.exit(7)` kills the vitest worker before any assertion runs. The run is unambiguously red and
the error names the guard line, but it is a crash, not an assertion. It is also a miniature
demonstration of the exact defect the five files carried: a wrongly-true guard hijacks its
importer's process.

**What the mutation set does NOT establish** (D-41 part 3 (d)): it proves these tests fail for guard
defects reachable by these four edits. It does **not** prove any of the five files behaves correctly
when actually run — nothing here runs them — and it does not touch their business logic, which I did
not change and did not test.

### 4.2 — Lint and types

```
$ npx eslint <the 5 repaired files + the 2 new files>
  3 errors — ALL PRE-EXISTING @typescript-eslint/no-explicit-any:
    mint_session_cookie.ts:96, probe/ask.ts:217, probe/ask.ts:327
  Verified pre-existing: the identical lines are present in `git show HEAD:<file>`.
  My two new files: clean. Left red per H3.
```

**`tsc` — the conductor's standing note applies.** `platform/tsconfig.json:33` excludes `scripts`,
so a project-`tsc` run does not typecheck any of these files and **I cite no project-`tsc` green
here.** I invoked `tsc` explicitly on the seven files:

```
$ npx tsc --noEmit --strict --skipLibCheck --esModuleInterop --resolveJsonModule \
      --target ES2022 --module esnext --moduleResolution bundler --lib ES2022,DOM <the 7 files>
  3 errors, ALL in dedupe_charts.ts (TS2344 at 63, 99, 127) — PRE-EXISTING, not mine.
  Proven: the same 3 errors appear at lines 60/96/124 of `git show HEAD:…dedupe_charts.ts`
  run through the identical command; my +3 import lines account for the entire shift.
  The five guards and both new files: 0 errors.
```

### 4.3 — Direction of change (D-41 part 2)

**Could this cause a build or deploy that previously failed to now pass? No.** Measured: no workflow,
no `package.json` script, no Dockerfile invokes any of the five. Every documented invocation is a
direct `npx tsx <file>` (including `scripts/probe/ask.sh:22`'s `exec npx tsx …ask.ts "$@"`), which
the guard preserves. The change only ever **refuses** execution it previously performed. This is a
strengthening; under D-41 part 2 it is machinery, proceed-and-report.

### 4.4 — Regression surface

```
$ npx vitest run --project node scripts/__tests__
  Test Files  1 failed | 16 passed (17)     Tests  4 failed | 235 passed (239)
```
The 4 failures are `nirmana_catalogue_disclosure.test.ts` B/C/D/H — **the same four M0-T60 reported
as its finding F-3**, in a file that touches none of my seven. Left red per H3, not investigated.

---

## 5 — What is proven, and what is NOT (read this before grading the task)

**PROVEN**
1. Each of the five carries the exact `isDirectEntrypoint` guard, exactly once, with its only
   `main()` invocation inside it and nothing executing after it.
2. Each of the five carries an `isDirectEntrypoint` body identical to the certified copy.
3. The detectors behind 1 and 2 can fail — shown on paired negative fixtures **and** by mutating
   real files (M1, M4).
4. The idiom itself resolves correctly under this repo's `tsx`, for a `platform/scripts/**` ESM
   `.ts` file, in both directions and under `NODE_ENV=test` (M0-T64/D-74 part 5 left per-file idiom
   correctness as an open per-file obligation; §2 discharges the *ESM-under-tsx* part of it for this
   directory tree, by demonstration rather than by assumption).

**NOT PROVEN — and I am not claiming any of it**
1. **That any of the five actually fires its guard when run.** No process ever evaluated any of
   them. The chain is: identical guard text + identical predicate body + the idiom demonstrated on a
   stand-in. That is strictly weaker than running the real file, and it is the trade D-74
   anticipated when it wrote "an honest 'the guard is present and shaped correctly, and I could not
   execute this file to prove it fires' is a complete result."
2. **That the five still work when invoked directly.** Their `main()` bodies are untouched, but I
   ran nothing.
3. **That nothing else in the tree imports them.** I did not measure importers. (Nothing imports
   them *today* by simple grep, but I did not do that measurement rigorously and do not claim it.)

I did **not** hit the "verifying appears to require executing it" condition. If I had, I would have
parked it — nothing was parked, and `mailbox/to_adhikarin/` carries only the P4-adjacent observation
in §7 F-3, which is an observation, not a park.

---

## 6 — What I did NOT do

- **Did not run any of the five.** Not directly, not via import, not in a sandbox, not with a stub
  env. No `gcloud`, no `firebase`, no database connection, no network call to any service.
- **Did not read, echo, log, rotate or relocate any secret value**, and **added no logging anywhere
  near `probe/ask.ts`'s secret path** (D-74 part 2). The only edits to that file are two import
  lines at 104–105 and the appended guard block; the `envOrSecret` region is untouched.
- **Did not delete `_archived/seed-abhisek.ts`** — repaired in place, per D-74 part 3.
- **Did not touch** the other 53 tier-1 files (wave 2, not dispatched), any tier-2/3 file, any of the
  13 grandfathered guards, `tsconfig.json`, `A3_env_matrix.md`, any migration, any asset data, any
  registry row, or `main`.
- **Did not build the ratchet** (D-74 part 7 — a different agent, and PARĪKṢAKA certifies it).
- **Did not fix** the 3 pre-existing `no-explicit-any` errors, the 3 pre-existing `TS2344` errors, or
  the 4 pre-existing `nirmana_catalogue_disclosure` failures (H3 — left red).
- **Did not extract** a shared `isDirectEntrypoint` module — that is F-2 / D-67 part 3's grant, not
  mine. My body-equality assertion covers only my five against the reference.

---

## 7 — Findings routed to `mailbox/to_conductor/`

- **F-1 — the guard does not close module-scope effects, and two of the five have them.**
  `dedupe_charts.ts` (`dotenv.config(…)` at line 34, `new Pool({connectionString: DATABASE_URL})` at
  line 42) and `_archived/seed-abhisek.ts` (same pair) still execute those on import **after** this
  repair. `new Pool()` opens no socket (node-postgres connects lazily) and `dotenv.config` is a
  filesystem *read*, so neither is a tier-1 property — but `dotenv.config` **mutates the importing
  process's `process.env`**, which is a real side effect nobody has graded. I deliberately did not
  move them: that is a runtime-behaviour change, not entrypoint discipline. This does not contradict
  T64's population measurement (which measured credential acquisition / connection open / write /
  network / exit at module scope), but it is the nearest thing to it, and wave 2 will meet it again.
- **F-2 — `isDirectEntrypoint` now exists in EIGHT production copies** (migrate.ts,
  asset_registry_seed.ts, ledger_writer_worker.ts, my five) — plus a ninth, deliberate, in my test
  fixture. M0-T60 filed the triplicate as F-2 and D-67 part 3 granted a
  shared implementation; this wave took the count from 3 to 8 because D-74 part 5 mandated the idiom
  and D-9 forbids importing from `migrate.ts`. My new test asserts my five agree with the reference,
  so five of the eight now have a divergence detector — the other three still do not. **Wave 2 will
  take this to ~61 copies if the shared implementation does not land first**, and that ordering is
  worth a decision.
- **F-3 — P4-adjacent, PRE-EXISTING, NOT TOUCHED: `set-password.ts` prints the password it just
  set.** Line 72 (post-repair numbering): `console.log(\`  Login with: ${EMAIL} / ${PASSWORD}\`)`.
  That is a credential written to stdout by design. I did not change it — removing it is not
  entrypoint discipline and P4 is close enough that it is not mine to decide. Copied to
  `mailbox/to_adhikarin/` as an observation. **I did not run the file, so I have never seen a value
  of `PASSWORD`.**
- **F-4 — for whoever builds the ratchet (D-74 part 7).** My five should now LEAVE the 76-file
  allowlist (pay-down; the list may never grow). I also added one new file with a top-level `main()`
  call — `scripts/__tests__/fixtures/entrypoint_guard_standin.fixture.ts` — which is **guarded**, so
  it does not belong on an unguarded-population list, but a detector that keys on "top-level `main()`
  call" without being guard-aware would flag it. Flagging it now so it is not a surprise.
- **F-6 — a concurrent agent committed my in-flight working tree** (`a7204cf68`, 54s before my
  own commit). It caught a clean state and the committed content is correct and passing — but my
  mutation proofs leave a real destructive script knowingly broken for ~10s at a time, so the same
  sweep firing in that window would have committed an UNGUARDED `set-password.ts` under a KĀRAKA's
  name with a confident message. Full account in §9. D-66 §7's shape: two correct mechanisms, no
  detector for their interaction.

- **F-5 — a shape worth naming.** M3's inverse mutation was caught as a *crash*, not an assertion,
  because the test imports the stand-in in-process and the mutated guard's `process.exit(7)` killed
  the vitest worker. M0-T60's §9.1 unsureness — "the tests catch it, but only *after* the module has
  already evaluated" — is confirmed live here. Any in-process import of a guarded entrypoint module
  is safe **only because the guard is correct**; that circularity is now precedent in two files.

---

## 8 — What I am unsure about

1. **Whether structural equality is enough for `probe/ask.ts` specifically.** It is the file I am
   least able to reason about empirically, because it is the one I am most strongly barred from
   running. Everything I know about its post-repair behaviour comes from reading it.
2. **Whether the stand-in is faithful enough.** It shares directory tree, extension, module system,
   runtime and guard text, but it has no `pg`, no `firebase-admin` and no `dotenv` in its module
   graph. If any of those packages did something exotic at import time that changed how `tsx`
   resolves `import.meta.url`, my §2 evidence would not cover it. I have no reason to think they do,
   and no way to check without executing a real file.
3. **Whether `_archived/seed-abhisek.ts` should also be quarantined further.** Guarding it removes
   the import hazard; a direct `npx tsx` still grants `super_admin`. D-74 says repair, not delete,
   and I did exactly that — but "guarded" and "safe to have in the tree" are different claims and
   only the first is now true.
4. **Whether `dedupe_charts.ts`'s module-scope `--apply` read is fully defanged.** Post-repair an
   importer's `--apply` still sets `APPLY = true`; it just never reaches `processGroup`. If a future
   edit exports anything from that file and a caller invokes an exported function, the module-scope
   flag is live again. The guard is not a substitute for moving that read inside `main()`.
5. **Whether the eight-copy divergence (F-2) is now the larger risk than the thing I fixed.** I lean
   yes, but that is a judgement for ADHIKĀRIN, not for me.

---

## 9 — Addendum (written after my own commit): a concurrent agent committed my working tree

**What happened, measured.** At `22:25:50 +0530` commit **`a7204cf68`** — "Nirmāṇa KĀRAKA-M0-T65:
entrypoint guards on Wave 1 tier-1 destructive scripts (D-74 part 1)", co-authored `Claude Sonnet 5`,
body citing "Committing immediately per D-66's lesson: this work was sitting uncommitted in the
tree" — committed all seven of my files plus this report. **I did not author that commit.** My own
`git commit --only` ran 54 seconds later at `22:26:44` (`400bbda0f`) and therefore carried only the
`WORK_QUEUE.jsonl` line, because everything else was already committed.

**The outcome was fine, and that is the point.** I re-verified after the fact: `git diff HEAD` is
empty for all seven files, the committed content is my final state (the corrected line references
`line 196` / `lines 15 and 18` are present in HEAD), and the suite still reports **37/37 passing on
the committed tree**.

**But it was fine by timing, not by construction — and this is a finding, not a complaint.** My
mutation proofs (§4.1) work by temporarily writing a *defective* version of a real file — M1 strips
`set-password.ts`'s guard outright, M4 flips an operator inside `probe/ask.ts`'s predicate — running
the suite, then restoring and checking sha256. Each mutation leaves a real, tracked, **destructive
script in a knowingly-broken state for roughly ten seconds**. Had that sweep fired during one of
those windows it would have committed, under a KĀRAKA's name and with a confident message, either a
`set-password.ts` with **no guard at all** (i.e. the exact defect this task exists to remove, landed
by the task that was removing it) or an `ask.ts` whose predicate answers backwards. Nothing in the
commit path would have noticed: the message is written from the task's intent, not from the diff.

This is D-66 §7's shape again — **two individually correct mechanisms whose interaction nobody has a
detector for.** "Commit uncommitted work immediately" is right (D-66 exists because ~50 reports were
lost). "Prove your repair with mutations on the real file" is right (D-41 part 3 requires the
inverse-direction mutation, and M1/M4 are the only way to prove the detector fires on the real
files). Their intersection is a window in which a sweeper can commit a deliberately-broken tree. I
have routed it to the conductor and to ADHIKĀRIN as **F-6** rather than inventing a rule for it,
which is not mine to do.
