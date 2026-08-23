# M0-T60 — the third `NODE_ENV` entrypoint guard (`ledger_writer_worker.ts:159`)

**Agent:** KĀRAKA-M0-T60 · **Task:** WORK_QUEUE `M0-T60` · **Source:** Standing Queue `SQ-24`
**Branch:** `campaign/nirmana-autonomous` · **Written:** 2026-08-23T15:42:27Z
**This is an observation report, not a verdict.** I do not certify my own work (I16/H7).

---

## 1 — The outcome in one line

**I changed it, to `isDirectEntrypoint`, not to `IMPORT_ONLY`** — because the re-derived hazard
analysis says this module's hazard is **RUNNING when it should not**, and because the old guard was
wrong in *both* directions, of which only `isDirectEntrypoint` fixes both. M0-T50's hypothesis is
**CONFIRMED**; its severity grading is **confirmed with one refinement** (§4).

---

## 2 — What the module actually does (read, not assumed)

`platform/scripts/pariprashna/ledger_writer_worker.ts`, 161 lines before the change. NO-LEAKAGE
arm-3, the out-of-process ledger writer. Measured facts:

| Fact | Evidence |
|---|---|
| It **mutates**. `main()` → `drainOutbox()` drains `pariprashna_ledger_outbox` and applies intents to `brahma_mimamsa_prediction_ledger` | lines 45, 71, 95–135 |
| It holds **the only** `role_ledger_write` credential in the system | header lines 8–12; `migrations/576_pariprashna_roles_rls_arm3.sql:156–159` names this file in the role's own `COMMENT ON ROLE` |
| It opens a **pg `Pool`** (`max: 2`) and, in `--interval` mode, **never terminates** (`while (!stopping)`) | lines 109, 145–152 |
| It calls **`process.exit()`** on three paths — 1 (no credential), 1 (connect failed), 0/2 (drained) | lines 106, 127, 134 |
| It exported **nothing at all** before this change | `grep -n "^export\|export " …` → no matches |
| **Nothing imports it.** The only test that references it (`src/lib/pariprashna/arm3/__tests__/arm3_out_of_process.test.ts:30`) reads it as **text** via `readFileSync` for structural assertions | `grep -rn ledger_writer_worker platform/ .github/` → 3 hits, all prose/`readFileSync` |
| **Nothing invokes it.** No workflow, no `package.json` script, no Dockerfile. Its only documented invocation is a manual `npx tsx …` line in `00_ARCHITECTURE/briefs/pariprashna_swarm/G1_C_ROLES_RLS_CUTOVER_RUNBOOK_v1_0.md:110` | header lines 32–34 say so explicitly ("No deployment manifest is added by this lane") |

The old guard, verbatim:

```ts
// Guard: only run when invoked directly, so a test may import this file.
if (process.env.NODE_ENV !== 'test') {
  void main()
}
```

Note the comment's claim — *"so a test may import this file"* — against the fact that the file
exported nothing. The invitation was real and the thing it invited could only ever have been a
side-effect import.

---

## 3 — The direction analysis, re-derived from scratch

A3.4's governing question: **what is this module's hazard — running when it shouldn't, or failing
to run when it should?**

**Answer: RUNNING.** And it is the same hazard, in the same words, as the two files ruling D-9
already repaired:

| | `migrate.ts` (D-9 / F-2) | `asset_registry_seed.ts` (M0-T15) | **this worker** | the two CI gates (D-49) |
|---|---|---|---|---|
| What `main()` does | applies migrations to prod | upserts `asset_registry` | **drains the outbox into the prediction ledger** | computes a verdict and exits |
| Credential | `DATABASE_URL` | `DATABASE_URL` | **the sole `role_ledger_write` login** | read-only / none |
| Cost of running wrongly | production schema mutated | control-plane rows rewritten | **prediction ledger mutated; importer's process killed by `process.exit`** | none — a gate is idempotent and read-only |
| Cost of not running | loud: nothing migrated | loud: nothing seeded | **quiet-ish: nothing drained; residue visible in outbox depth** | **an unearned green — the whole product is the verdict** |
| Safe default | DO NOT RUN | DO NOT RUN | **DO NOT RUN** | RUN |

A gate's *entire product is its verdict*, so a gate that does not run leaves nothing behind and its
silence reads as a pass. A mutating worker's product is *state*, so a worker that does not run
leaves a queryable residue (`pariprashna_ledger_outbox` depth) and mutates nothing. The hazards
genuinely point opposite ways, exactly as M0-T50 said they might.

**And `IMPORT_ONLY` would have been actively wrong here.** Its whole contract is "default = RUN
whenever loaded any way at all" (A3.4.1). Applied to this file that means: any import, from any
process, in any environment, opens the ledger-write pool and drains the outbox. That is the F-2
defect re-armed with a fresh sentinel. I did not choose `isDirectEntrypoint` because a rule in a
table said "worker"; I chose it because `IMPORT_ONLY`'s default is the wrong one for a module that
writes.

### The finding M0-T50 did not have: the old guard was wrong in BOTH directions

Measured on the unmodified file before I touched it, all four cells, real subprocesses
(`env -i`, credential pointed at `127.0.0.1:1`, nothing listening — no database was ever reached):

| # | Invocation | exit | bytes out | meaning |
|---|---|---|---|---|
| BEFORE-1 | direct run, `NODE_ENV` unset | 1 | 443 | `ARM3_CONNECT_FAILED` — correct, main ran |
| BEFORE-2 | direct run, **`NODE_ENV=test`** | **0** | **0** | **silent no-op** — the documented operator invocation drained nothing and said nothing |
| BEFORE-3 | **side-effect `import`**, `NODE_ENV` unset | **1** | **462** | `IMPORT_RETURNED_OK` then `ARM3_CONNECT_FAILED` — **`main()` ran as an import side effect and `process.exit(1)` killed the importer** |
| BEFORE-4 | side-effect `import`, `NODE_ENV=test` | 0 | 18 | did not run |

BEFORE-3 is the one that decides the task. In any shell with `NODE_ENV` unset — every ordinary
developer and agent shell — importing this file connected as `role_ledger_write` and drained. It is
harmless *today* only because the module exports nothing to import; the moment a future test author
accepts the invitation in line 158's own comment (and adding an export is the obvious next step for
a file with testable `parseArgs`/`drainOnce` logic), it is live. That is D-49 part 3's "the trap is
pre-laid at the exact destination" in a second location.

`isDirectEntrypoint` closes both cells. `IMPORT_ONLY` would close BEFORE-2 and leave BEFORE-3 wide
open. "No change" leaves both.

---

## 4 — Where I confirm M0-T50, and where I refine it

- **CONFIRMED — graded LOWER than R-28.1.** Right, and for a reason I can now state precisely: the
  gates' silent exit 0 *substitutes for* a verdict a human will act on; this worker's silent exit 0
  leaves an observable residue in a table. Different blast radius, different urgency.
- **CONFIRMED — the direction analysis genuinely differs**, and it lands on `isDirectEntrypoint`,
  exactly as M0-T50 guessed without deciding.
- **REFINED — "a worker that declines to start fails loudly" is too strong for the exit code
  itself.** Measured, BEFORE-2 exits **0 with zero bytes of output**. A scheduler would have
  recorded a success. What is loud is the *consequence* (an outbox that stops draining), not the
  *signal*. I flag this because the sentence, taken at face value, is the one thing that could
  justify "no change", and it does not survive measurement.
- **NEW, not in M0-T50's analysis:** the import direction. M0-T50 weighed "gate vs worker" and did
  not measure that the existing guard was already firing `main()` on import. That is the finding
  that moved this from "arguable" to "repair".

---

## 5 — What I changed

Two files, both control plane.

**(a) `platform/scripts/pariprashna/ledger_writer_worker.ts`** (+69 lines, net)
- Added `realpathSync` / `resolve` / `fileURLToPath` imports (node builtins only — the module's
  design premise of an empty app-module graph is preserved, and the structural assertions in
  `arm3_out_of_process.test.ts` that forbid `lib/db` and `@/` specifiers still hold; that file
  still passes, §6).
- Added an **exported** `isDirectEntrypoint(moduleUrl, argv1)`, **mirrored not imported** from
  `scripts/migrate.ts` / `scripts/seed/asset_registry_seed.ts`. Mirrored because ruling **D-9**
  standing-instructs agents not to import from `scripts/migrate.ts`, and because importing the
  migrator into this worker would wire it into exactly the module graph its header exists to keep
  it out of. This is now the module's **first export**, which is what makes line 158's original
  comment true for the first time.
- Replaced the guard with `if (isDirectEntrypoint(import.meta.url, process.argv[1])) { void main() }`,
  with a comment recording both failure directions, and stating explicitly that this is **not** the
  `IMPORT_ONLY` contract and why.
- **The worker's runtime behaviour is untouched**: `parseArgs`, `drainOnce`, `main`, the SQL path,
  the exit codes, the credential handling and the signal handlers are byte-identical.

**(b) `platform/scripts/__tests__/ledger_writer_worker_entrypoint_guard.test.ts`** (new, 7 tests)
— a real detector, mirroring `asset_registry_seed_entrypoint_guard.test.ts`. Child environments are
**constructed from scratch, never spread from `process.env`**, so a real
`LEDGER_WRITER_DATABASE_URL` in a developer or CI shell can never reach a process this file
deliberately causes to run the writer.

### Scope check — SQ-24's own stop condition

SQ-24 says to STOP and report if the change would alter the subsystem's **runtime behaviour**
rather than only its **entrypoint discipline**. It does not, and here is the whole matrix:

| Invocation | before | after | changed? |
|---|---|---|---|
| documented `npx tsx …ledger_writer_worker.ts --once` | runs | runs | **no** |
| same, in an env exporting `NODE_ENV=test` | silent exit 0 | runs | yes — a *defect* cell |
| import, `NODE_ENV` unset | **runs, mutates, exits** | does not run | yes — a *defect* cell |
| import, `NODE_ENV=test` | does not run | does not run | **no** |

Only the two wrong cells move. The one documented invocation path is unchanged. **D-41 part 2
direction test:** could this cause a build or deploy that previously failed to now pass? **No** —
nothing in `.github/workflows/` or `package.json` invokes this worker at all (measured, §2), and
the change only ever adds execution or refuses it, never converts a failure into a pass. This is a
**strengthening**; under D-41 part 2 it is machinery, proceed-and-report.

---

## 6 — Evidence (every number below was run, not reasoned about)

### 6.1 — The repair, both directions, by direct run

| # | Invocation | exit | bytes | observed |
|---|---|---|---|---|
| AFTER-1 | direct, `NODE_ENV` unset | 1 | 443 | `ARM3_CONNECT_FAILED` |
| AFTER-2 | direct, **`NODE_ENV=test`** | **1** | **443** | `ARM3_CONNECT_FAILED` — **the cell BEFORE-2 got wrong** |
| AFTER-3 | **import**, `NODE_ENV` unset | **0** | **18** | `IMPORT_RETURNED_OK` only — **the cell BEFORE-3 got wrong** |
| AFTER-4 | import, `NODE_ENV=test` | 0 | 18 | `IMPORT_RETURNED_OK` only |
| AFTER-5 | direct via `./`-prefixed spelling | 1 | 443 | `ARM3_CONNECT_FAILED` — normalisation holds |
| AFTER-6 | direct, no credential at all | 1 | 337 | `ARM3_NO_CREDENTIAL` — the honest pre-existing path, intact |

### 6.2 — Tests

```
$ npx vitest run --project node scripts/__tests__/ledger_writer_worker_entrypoint_guard.test.ts
  Test Files  1 passed (1)        Tests  7 passed (7)

$ npx vitest run src/lib/pariprashna/arm3          # incl. arm3_out_of_process structural test
  Test Files  2 passed | 1 skipped (3)   Tests  19 passed | 20 skipped (39)
  # the skip is roles_rls.db.test.ts — needs a live Postgres, pre-existing, unrelated

$ npx vitest run --project node scripts/__tests__   # the whole scripts test surface
  Test Files  1 failed | 15 passed (16)   Tests  4 failed | 192 passed (196)
```

### 6.3 — The 4 failures are PRE-EXISTING and NOT MINE, and I left them red (H3)

`scripts/__tests__/nirmana_catalogue_disclosure.test.ts` — cases B, C, D, H. I verified this
rather than asserting it: I stashed the worker change, moved my new test file out of the tree,
re-ran that file alone, and got **the identical 4 failures** (`4 failed | 8 passed (12)`), then
restored both and confirmed the worker file was byte-identical to my version. **Not touched, not
investigated, reported to the conductor as a finding.**

### 6.4 — Mutation proofs, including two inverse-direction mutations (D-41 part 3 standing requirement)

| Mutation | What it does | Result |
|---|---|---|
| **M1** — revert the guard to `if (process.env.NODE_ENV !== 'test')` | restores the exact defect | **2 failed** — A (import ran it) and C (direct run under `NODE_ENV=test` went silent). Nothing else moved, so the tests fail for the right reason |
| **M2** — `isDirectEntrypoint` always returns **false** (inverse: signal never fires) | worker becomes unrunnable | **4 failed** — C, D, E and G |
| **M3** — `isDirectEntrypoint` always returns **true** (inverse: signal fires when it must not) | fires on every import | **4 failed** — A, B, F and G |

M3 is the direction D-41 part 3 (c) requires and the one that matters most here, since "fires when
it should not" *is* this module's hazard. The file was restored byte-identical after each mutation
(`diff` → identical, verified).

**What the mutation set does NOT establish** (stated per D-41 part 3 (d)): it proves the tests can
fail for guard defects reachable by these three edits. It does not prove the *pure* logic of
`drainOnce`/`parseArgs` is correct — I did not test those and did not change them — and it does not
prove the worker behaves correctly against a real Postgres, which no test here ever reaches.

### 6.5 — Lint and types

```
$ npx eslint scripts/pariprashna/ledger_writer_worker.ts \
             scripts/__tests__/ledger_writer_worker_entrypoint_guard.test.ts   → exit 0, no output
$ npx tsc --noEmit -p tsconfig.json    → 0 errors repo-wide (grep -c "error TS" = 0)
```

### 6.6 — Class residue, measured rather than presumed (D-49 part 4's discipline)

```
$ git grep -nE "^\s*if \(process\.env\.NODE_ENV" -- '*.ts' '*.tsx' '*.js' '*.mjs'
(no matches)
```

**Zero live `NODE_ENV`-keyed entrypoint guards remain anywhere in the repository.** All eleven
remaining textual matches for `NODE_ENV !== 'test'` are *comments* in the five repaired files and
their tests, documenting the defect. With migrate.ts (M0-T11), asset_registry_seed.ts (M0-T15), the
two CI gates (M0-T50) and this one, the class is empty. **I am reporting that as a measurement, not
declaring the class closed — that is PARĪKṢAKA's call, not mine.**

---

## 7 — What I did NOT do

- **Did not edit `platform/scripts/audit/A3_env_matrix.md`** (explicitly out of bounds — M0-T59's,
  just landed). **Its operator rule 5 is now stale**: it says this worker "still carries the
  `NODE_ENV !== 'test'` form and is a known open item". Filed to the conductor, §8 F-1.
- **Did not touch** `platform/scripts/ci/verify_migrations_deployed.ts` or
  `scripts/ci/dispatch_gate.ts` (V-36 certified).
- **Did not fix** the pre-existing `nirmana_catalogue_disclosure.test.ts` failures (H3 — left red).
- **Did not extract** a shared `isDirectEntrypoint` module; that would edit `migrate.ts` and the
  seed, is a mechanism change, and is out of SQ-24. Third duplication filed as §8 F-2.
- **Did not touch** any asset data, registry row, migration, or `.env*` file. No credential was
  read, set, logged or relocated (P4 untouched). No process ever reached a real database:
  `LEDGER_WRITER_DATABASE_URL` was **unset in my shell** (verified) and every child got an
  explicitly-built env pointing at `127.0.0.1:1`.
- **Did not wire** the worker into any schedule, workflow or manifest. It remains shipped dark, as
  its header intends.
- **Did not run** the full repo test suite — only the three surfaces above.

## 8 — Findings routed to the conductor

- **F-1 — `A3_env_matrix.md` Addendum A3.4 operator rule 5 is now stale.** It documents this file
  as an open item carrying the old form. Someone other than me should update it; I was barred from
  the file. Also `§A3.4.3`'s comparison table would now gain a fourth row.
- **F-2 — `isDirectEntrypoint` now exists in triplicate** (`migrate.ts:941`,
  `asset_registry_seed.ts:3718`, `ledger_writer_worker.ts`), each with its own tests, each
  deliberately a copy because D-9 forbids importing from `migrate.ts`. Three copies is the point at
  which "deliberate mirror" starts to look like drift-in-waiting. There is no detector asserting
  the three bodies agree.
- **F-3 — pre-existing red:** `scripts/__tests__/nirmana_catalogue_disclosure.test.ts` B/C/D/H fail
  on the tree without my changes (`c01_effective` expected `DISCLOSED_NON_GATING`, received
  `BLOCKING`). Left red per H3. It reads like a Nirmāṇa control-plane test out of step with a
  ruling, so it may be this campaign's own.
- **F-4 — the larger unguarded population, measured and NOT investigated:** **81 files** under
  `platform/scripts/**` call `main()` at top level with **no guard at all**
  (`git grep -lE "^\s*(void )?main\(\)"`). Those are a different question from this defect class —
  most are one-off CLIs nothing imports — but the population is large and nobody has measured which
  of them mutate. Recorded so it is a number rather than an impression.

## 9 — What I am unsure about

1. **Whether the new test's in-process `import { isDirectEntrypoint }` is a risk worth taking.**
   It loads the worker module inside the vitest worker. It is safe *because the guard is correct* —
   which is precisely the circularity `asset_registry_seed_entrypoint_guard.test.ts` already
   accepted by precedent, and I followed that precedent rather than inventing a different trade. If
   a future edit breaks the guard toward "always true", that import would fire `main()` inside
   vitest with whatever `LEDGER_WRITER_DATABASE_URL` is ambient. Mutation M3 demonstrates the tests
   catch it — but they catch it *after* the module has already evaluated. I measured that my own
   shell has the variable unset, so nothing was at risk today; I cannot say the same for CI.
2. **Whether `--interval` mode has a *different* answer.** The long-running poll shape never
   terminates. Under the old guard, an import in interval mode would have hung the importer
   forever rather than exiting. I did not test interval mode (it would need a reachable DB), and my
   argument does not depend on it — but it makes the import hazard worse, not better, so I note it
   as an unexplored strengthening of my own conclusion rather than a counterweight.
3. **Whether a future containerised invocation is still "direct".** If the cutover runbook is
   later implemented with a Docker `CMD` or a Cloud Run job that does not put this file at
   `process.argv[1]` — e.g. a wrapper module that imports it — the guard answers false and the
   worker silently does nothing. That is the `isDirectEntrypoint` idiom's known cost (migrate.ts's
   own docstring names it), and the runbook's documented invocation is a direct `npx tsx`, so it
   holds today. I could not test a deployment shape that does not exist yet.
4. **Whether "the class is now empty" is durable.** §6.6 is a measurement with a short shelf life,
   the same weakness A3.4 INV-1 discloses about itself. Nothing greps for a reintroduced
   `NODE_ENV`-keyed entrypoint guard. A `migration_number_guard`-shaped CI assertion would close
   it; I did not build one and did not have a task for one.
5. **I have not verified the worker works.** Everything above is about *when it starts*. Whether
   `drainOutbox` correctly applies intents against a real ledger is untested by me and unchanged by
   me.
