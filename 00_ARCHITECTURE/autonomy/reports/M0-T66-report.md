# M0-T66 — ONE shared `isDirectEntrypoint`, and a ratchet that fails on a NEW unguarded `main()`

**Agent:** KĀRAKA-M0-T66 · **Task:** `WORK_QUEUE` `M0-T66`
**Authority:** ruling **D-67 part 3** (F-2 + F-5 granted together), shaped by **D-67 part 4**
(ratchet conditions), **D-71 parts 5 & 7** (settled baseline + required detector shape),
**D-72** (prose-is-not-code), **D-77** (mutation windows), **D-79** (prove the branch)
**Branch:** `campaign/nirmana-autonomous` · **Written:** 2026-08-23T17:32Z
**Commits:** `cff6be47a` (part a) · `7372901d5` (part b)

**This is an observation report, not a verdict. I do not certify my own work (I16/H7).**
**I repaired none of the 76. Not one file in that population was edited by me.**

---

## 1 — The three things that matter, up front

1. **THE COPIES ARE GONE, NOT INSTRUMENTED.** `isDirectEntrypoint` was defined in **eight**
   production files; it is now defined in **one**. The other eight import and re-export it. F-2
   asked for a detector that the bodies agree; what landed is stronger — **they cannot disagree,
   because there is one body.** Measured, not asserted: §2.1.
2. **THE RATCHET IS GREEN ON THE EXISTING TREE AND RECONCILES EXACTLY WITH THE SETTLED
   BASELINE.** 71 unguarded files, every one of them inside D-71's authorised 76; the 5 that left
   are precisely M0-T65's five; 19 guarded across **all five** idioms including the three
   same-line ones; **0 files unparsed**. Exit code 0. §3.4.
3. **THE FIXTURES CAUGHT TWO DEFECTS IN MY OWN DETECTOR, AND THE SECOND ONE IS THE INTERESTING
   FAILURE.** A string-blanking bug made the scanner silently report **12 of the settled 76 as
   clean** — no error, no warning, a plausible number. I found it by reconciling the output
   *set* against the baseline, not its *count*. §3.3, and finding F-Q.

---

## 2 — Part (a): one shared implementation

### 2.1 — What changed, and the measurement that says it worked

**New: `platform/scripts/lib/entrypoint.ts`.** Its `isDirectEntrypoint` body is **byte-identical
(412 bytes) to the certified copy it replaces** — verified before anything was rewired, so the
extraction moved code rather than rewriting it.

```
$ git grep -ln "export function isDirectEntrypoint(" -- '*.ts' '*.mts' '*.cts'
platform/scripts/lib/entrypoint.ts                                        ← THE implementation
platform/scripts/__tests__/fixtures/entrypoint_guard_standin.fixture.ts   ← deliberate stand-in
platform/scripts/__tests__/destructive_entrypoint_guards.test.ts          ← inside a sample STRING
platform/scripts/__tests__/shared_entrypoint_module.test.ts               ← inside a sample STRING
```

**Production copies: 0. Before: 8.** All eight now carry
`import { isDirectEntrypoint } from '<rel>/lib/entrypoint'` plus `export { isDirectEntrypoint }`,
so every module's public surface is exactly what it was and the three existing suites that import
the symbol from `migrate.ts` / `asset_registry_seed.ts` / `ledger_writer_worker.ts` still resolve
it. **Every guard call site is untouched**; each of the eight still carries exactly one
`if (isDirectEntrypoint(import.meta.url, process.argv[1])) {` and it was never absent at any point
during the edit — the function definition was replaced by the import in a single write, so no
intermediate state removed a guard.

Also removed: the node-builtin imports each file had acquired **solely** for its private copy
(17 specifiers across 7 files, plus 3 in `_archived/seed-abhisek.ts` which eslint does not lint).
Each removal was driven by eslint's own unused-vars output, not by my reading.

### 2.2 — Why importing this is not what ruling D-9 forbids

D-9's standing instruction is not "never import" — it is **"never acquire a module graph you did
not have"**. `migrate.ts` is a *program*; importing it used to apply migrations to production.
`scripts/lib/entrypoint.ts` is a *leaf*: only `node:fs`, `node:path`, `node:url` — the three
builtins every one of the eight already imported for its own copy — and **no module-scope effect
at all**. An importer's graph gains zero packages and zero side effects.

That is not a claim I am asking anyone to take. `scripts/__tests__/shared_entrypoint_module.test.ts`
§1 asserts it over the module's source: the import specifier set is a subset of exactly those
three; no top-level `main()`, no `process.exit`, no `Pool`/`Client`/`getPool`, no `fetch`, no
`execSync`, no `writeFileSync`, no `dotenv`, no `process.env`; exactly one exported symbol. If
someone adds a convenience to this module later, that test goes red.

### 2.3 — What happened to M0-T65's verification, and why the replacement is stronger

M0-T65's suite compared each of the five files' predicate **body text** against a certified copy.
With no copies left there is no text to compare, so the assertion became **identity**: the file
defines *no* private predicate and *does* import-and-re-export the shared one. Text equality
detects divergence after it happens; identity makes it impossible.

**Its own anchor test caught this change, which is the best evidence the anchor was worth having.**
When the predicate left `asset_registry_seed.ts`, `predicateBody(REFERENCE)` returned `null` and
every per-file `expect(predicateBody(src)).toBe(referenceBody)` would have compared `null` to
`null` and **passed vacuously** — 37 green tests asserting nothing. The anchor
(`expect(referenceBody).toBeTruthy()`) failed instead. That is the only test in the file that
failed, and it is the one whose comment says *"if this fails, every per-file comparison below is
vacuous."*

I did not weaken anything to make it pass (H3): the section gained assertions and kept all of its
existing ones — no unguarded top-level `main()`, exactly one `main()` invocation and only after
the guard, the exact guard form exactly once, no `IMPORT_ONLY`, no `NODE_ENV` sentinel, guard
block closes at EOF.

### 2.4 — F-O: both lists in the subsystem are now derived, never hand-typed

The conductor routed PARĪKṢAKA's **F-O** mid-task: the guard test's `TARGETS` was a five-element
literal, so Wave 2 would leave 58 guarded files of which 5 were checked — 9% coverage, and
hand-extending a 53-entry literal is itself an unverified step.

| list | was | now | today | after Wave 2 |
|---|---|---|---|---|
| `destructive_entrypoint_guards.test.ts` `TARGETS` | 5-element literal | `M0-T64-triage.json` tier-1 records (58), **filtered to files that carry the guard** | 5 | 58, no edit |
| `shared_entrypoint_module.test.ts` `CONSUMERS` | (I first wrote an 8-element literal) | tree scan of `platform/scripts/**/*.ts` for `isDirectEntrypoint` over **comment-blanked** source | 8 | 61, no edit |

Two properties make these safe rather than merely clever:

- **The `carriesGuard` filter is what stops `TARGETS` becoming the permanently-red list D-39
  part 2 forbids.** Deriving straight from tier-1 would assert the guard's presence on 53 files
  nobody is allowed to repair yet. An unrepaired file carries no guard, so it is simply not yet
  asserted about; the instant Wave 2 guards it, it enters the set and every assertion applies.
  The set can only grow.
- **Each carries a FLOOR** (`COVERAGE_FLOOR = 5`, `CONSUMER_FLOOR = 8`). A derivation that broke
  and returned `[]` would make every per-file block disappear — a green suite asserting nothing,
  §N.8's unearned signal. The floor fails instead.

**The `CONSUMERS` derivation went wrong exactly once, in the way D-72 predicted, and that is
recorded rather than smoothed over.** Written against raw text it matched
`scripts/ci/dispatch_gate.ts` and `scripts/ci/verify_migrations_deployed.ts`, which mention
`isDirectEntrypoint` **only in a comment** — one explaining why a CI gate correctly uses the
opposite `IMPORT_ONLY` contract — and then failed them for not importing a predicate they are
right not to use. Matching over comment-blanked source fixes it, and a §4 test pins the
distinction.

### 2.5 — Evidence for part (a)

```
$ npx vitest run --project node scripts/__tests__/destructive_entrypoint_guards.test.ts
  Test Files  1 passed (1)     Tests  39 passed (39)

$ npx vitest run --project node scripts/__tests__/shared_entrypoint_module.test.ts
  Test Files  1 passed (1)     Tests  21 passed (21)

$ npx vitest run --project node scripts/__tests__          # whole directory
  Test Files  1 failed | 17 passed (18)     Tests  4 failed | 258 passed (262)
```

The one failing file is `nirmana_catalogue_disclosure.test.ts` (B/C/D/H) — **M0-T60's finding
F-3, pre-existing, in a file I did not touch.** Left red per H3.

```
$ npx eslint scripts/lib/entrypoint.ts scripts/__tests__/shared_entrypoint_module.test.ts \
             scripts/__tests__/destructive_entrypoint_guards.test.ts
  (clean)

$ npx eslint <the 8 rewired files>
  4 errors — ALL PRE-EXISTING (3 no-explicit-any, 1 prefer-const; each verified present at HEAD)
```

**`tsc`: the conductor's standing note applies and I cite no project-`tsc` green.**
`platform/tsconfig.json:33` excludes `scripts`, so the project typecheck does not cover any of
this. Invoked explicitly on the nine files:

```
$ npx tsc --noEmit --strict --skipLibCheck --esModuleInterop --resolveJsonModule \
      --target ES2022 --module esnext --moduleResolution bundler --lib ES2022,DOM <9 files>
  3 errors, ALL TS2344 in dedupe_charts.ts (61, 97, 125) — M0-T65's three pre-existing errors.
  They were at 63/99/127; my net −2 import lines account for the entire shift.
  The shared module and all 8 rewired files: 0 errors.
```

---

## 3 — Part (b): the ratchet

`platform/scripts/governance/check_entrypoint_guard_ratchet.py`, built to the same shape as
`check_earned_signal.py` and `check_fact_category_pinning.py`: stdlib only, no DB, no network,
bundled PASS/FAIL fixtures, `--self-test`, `--strict`, `--json`, `--regenerate`.

### 3.1 — The three ratchet clauses, each with a detector rather than a promise

| D-67 part 4 requires | mechanism | proven by |
|---|---|---|
| generated from the measurement, **never hand-typed** | `--regenerate` writes the list from this script's own scan. There is no code path that appends a name. | the file's `generated_by`; §3.5 M4 |
| **NOTHING IS EVER ADDED** | **every run** — not only `--regenerate` — asserts `files ⊆ baseline_files`, the baseline being M0-T64's settled 76 (`ratchet_allowlist.files`, authorised by D-71 part 5 after two independent derivations diffed IDENTICAL). Hand-adding an entry fails the run. `--regenerate` refuses outright if the scan finds anything outside the baseline. | §3.5 M4 |
| **count recorded so shrinkage is visible** | `baseline_count: 76`, `count: 71`, `paid_down_count: 5` and the itemised `paid_down` list, in the JSON and in `--json` | §3.4 |

Stale entries — allowlisted files that are now clean — are **reported loudly on every run and
fail only under `--strict`.** They are the good direction; gating on them would turn a repair
into a red build, which is D-39 part 2 again from the other side.

### 3.2 — The detector, against D-71 part 7's four requirements

**(a) Not line-anchored anywhere.** It is brace-aware: every `main(` call token is located, its
enclosing block stack computed, and the question asked is *"is this executable at module load?"*.
Indentation is never consulted. A call inside a function/class/arrow body is a call site, not a
top-level executor, and is not reported.

**(b) All five idioms, each a named rule** — `isDirectEntrypoint`, `IMPORT_ONLY`, argv-regex,
`isEntrypoint`/`isMain`, `require.main === module` (with `import.meta.main` / `import.meta.url ===`).
Guardedness is decided over the *guard context* = every enclosing block header **plus the
same-statement prefix**, which is what makes the three SAME-LINE guards visible. The self-test
asserts every declared idiom is exercised by a PASS fixture that names it, so an idiom silently
dropped from the table fails CI. The **retired `process.env.NODE_ENV` sentinel is deliberately
not a guard** and a FAIL fixture pins that.

**(c) Code paths only.** `.ts` under `platform/scripts`; no `.md`, no `00_ARCHITECTURE/**`, no
`99_ARCHIVE/**`. Within a file, comment bodies, string bodies, template-literal bodies **and
regex-literal bodies** are blanked to spaces (offsets and newlines preserved) before anything is
matched. A dedicated PASS fixture is nothing but the defective form written in a line comment, a
block comment, a string, a template literal, a nested function body and a `forEach` callback —
and must produce zero violations.

**(d) Paired fixtures**, including the two D-71 names explicitly:
`fail/indented_unguarded.ts` and `pass/guarded_same_line_require_main.ts`.

### 3.3 — Two defects the fixtures found IN THE DETECTOR (F-Q)

**(1) A detector that SKIPS a construct looks identical to one that APPROVES it.** My first
`OPAQUE_HEADER` listed `\btest\s*\(` so a vitest `test(...)` body would not count as top level.
It also matched `.test(process.argv[1])` — the *guard expression* of the argv-regex idiom — so
the entire guarded block of the three `shad_darshana` gates became an "opaque callback" and its
`main()` was never examined. **A PASS fixture asserting only "produced no violation" would have
been green.** It was caught solely because each PASS fixture declares `EXPECT-GUARD: <idiom>` and
the self-test asserts the detector *attributed that idiom*. A positive assertion about **why**
something passed is the only thing that separates approval from blindness.

**(2) A scanner whose failure mode is "reports nothing" silently reported 12 of the settled 76 as
clean.** The blanker had no regex-literal awareness. `scripts/audit/replay.ts:27` contains
`replace(/^["']|["']$/g, '')` — four quote characters inside a regex literal — so it treated them
as string delimiters, desynchronised, and blanked the rest of the file. Twelve files came back
with zero occurrences and the run looked healthy. **I found it only because I reconciled the
output SET against the settled baseline, not its COUNT** — D-71 part 3's own discipline paying
for itself a second time.

Fixed two ways, and the second matters more than the first: regex-literal awareness, **and the
scanner now reports when it could not parse a file.** A file whose brace stack does not return to
empty is UNKNOWN, is blocking, and is never reported as clean (§N.8: a detector that cannot
answer must not return the answer that happens to look green). Today: **0 unparsed.**

### 3.4 — The reconciliation, which is the acceptance test for the whole task

```
files with a top-level main() under platform/scripts : 90
  unguarded                                          : 71
  guarded                                            : 19
M0-T64 settled baseline (D-71 part 5)                : 76

unguarded NOT in the baseline  (must be empty)       : []            ✔
baseline now clean  (paid down)                      : 5             ✔
  platform/scripts/_archived/seed-abhisek.ts
  platform/scripts/dedupe_charts.ts
  platform/scripts/dev/mint_session_cookie.ts
  platform/scripts/probe/ask.ts
  platform/scripts/set-password.ts                   ← exactly M0-T65's five
files the scanner could not parse                    : 0             ✔
```

**The 19 guarded reconcile to D-71 part 4's settled 13, exactly**: the 13, plus M0-T65's five,
plus the stand-in fixture. All five idioms appear on real files, and **all three same-line guards
are recognised** — `audit/tap/sc_pointer_validation.ts`, `ci/migration_number_guard.ts`,
`generate_signal_glossary_mirror.ts`, the three that sit in neither the 86 nor the 76.

**`fixtures/entrypoint_guard_standin.fixture.ts` is classified GUARDED, not flagged** — M0-T65's
F-4 warning discharged: a guard-unaware detector would have reported the very fixture written to
test the guard.

```
$ python platform/scripts/governance/check_entrypoint_guard_ratchet.py
check_entrypoint_guard_ratchet: 90 file(s) with a top-level main() under platform/scripts — 71 unguarded, 19 guarded.
  ratchet: 71 allowlisted of M0-T64's 76 baseline (5 paid down).
  NOTE — 3 file(s) ... OUTSIDE this ratchet's gated population ... (finding F-P)
check_entrypoint_guard_ratchet: 0 new unguarded top-level main(). PASS.
exit=0

$ python ... --self-test
check_entrypoint_guard_ratchet: SELF-TEST PASS (6 pass fixture(s) silent, 4 fail fixture(s) caught, 5/5 guard idioms exercised).
```

**It is not green because it is blind: `--strict` exits 1 on the 71 residuals.** The default run
is green because the backlog is carried openly and itemised, which is D-54's disclosure shape and
D-67 part 4 says so in terms.

### 3.5 — Mutation proofs (D-41 part 3), and the D-77 window they ran inside

**Window announced OPEN in the heartbeat before the first mutation and CLOSED after the last**,
naming every file: the temporary probe file, the allowlist JSON, and the guard script.
**None of the three is destructive-or-credential-touching on import**, so D-77 part 4's
copy-only rule did not apply; the five files it does apply to were not mutated at all.

| # | mutation | result |
|---|---|---|
| **M1** | a NEW file with a column-0 unguarded `main()` | **FAIL**, exit 1, file and line named |
| **M2** | the same file, `main()` **INDENTED** inside `if (process.env.ANYTHING) {` (D-71 7(d)) | **FAIL**, exit 1, and the report prints the non-guard context it rejected |
| **M3** | the same file, `if (require.main === module) void main()` — same-line guard | **PASS**, exit 0 |
| **M3b** | the same file, `isDirectEntrypoint` guard | **PASS**, exit 0 |
| **M4** | hand-add one entry to the allowlist | **FAIL**, exit 1: *"1 allowlist entry ... NOT in M0-T64's settled baseline. The list may only SHRINK."* |
| **M5** | delete the `require.main===module` idiom from the detector — **the inverse direction** | self-test **FAILS** naming the fixture *and* the missing idiom; the repo scan goes **red on the two real same-line-guarded files** |

Probe file deleted; allowlist and guard script restored and **sha256-verified byte-identical**
(`0f9a3f27…`, `23b2236…`); the guard re-run green after each restore.

**What the mutation set does NOT establish:** that the guard catches every possible reintroduction
form. It proves the detector fires on these six edits and on the ten fixtures. §5 lists the shapes
I know it cannot see.

### 3.6 — CI

`entrypoint-guard-ratchet` added to `.github/workflows/nirmana-m0-guards.yml`, **deliberately
without `continue-on-error`** unlike its two siblings — they are non-blocking because their
criteria are legitimately non-zero, and this one is green. Two steps: `--self-test`, then the
repo scan. YAML parse-validated.

---

## 4 — Findings routed to `mailbox/to_conductor/`

Full text: `00_ARCHITECTURE/autonomy/mailbox/to_conductor/20260823T173205Z-M0-T66-findings.md`.

- **F-O (answered, measured)** — production copies **8 → 0**. F-O's arithmetic does not shrink,
  it collapses: two copies are needed for two copies to disagree. Both lists in the subsystem are
  now derived and floored.
- **F-P (needs ADHIKĀRIN)** — **three `.mts` files with an unguarded top-level `main()` that the
  baseline structurally cannot see**, because M0-T64's population command ends `| grep '\.ts$'`
  and `.mts` does not match it: `d4a/file_baseline_predictions.mts`,
  `d4a/fix_item3_spiritual_arc_correction.mts`, `retrieval/test_router.mts`. Same *kind* of cause
  as D-71 part 2's glob pathspec — a filter that silently drops files. **I did not add them and
  the guard refuses to**; they are scanned, reported by name on every run, and **not gated**.
  The hole: a new unguarded `.mts` today is reported but does not fail.
- **F-Q** — §3.3's two detector defects, both doctrine-shaped.
- **F-R** — the CI job gates a merge only once it is in **branch protection**, which is a
  repository-settings change **I did not make**. Written into the job's own comment block too.
- **F-S** — pre-existing red, left red per H3 (3 `no-explicit-any`, 1 `prefer-const`, 3 `TS2344`,
  4 `nirmana_catalogue_disclosure`).

---

## 5 — What is PROVEN, and what is NOT

**PROVEN**

1. `isDirectEntrypoint` is defined in exactly one production file; the other eight import and
   re-export it; every guard call site is intact and unchanged.
2. The shared module is a leaf — only three node builtins, no module-scope effect — and a test
   fails if that stops being true.
3. The ratchet reproduces the settled 76-file baseline **as a set**: 71 unguarded all inside it,
   5 paid down and they are exactly M0-T65's five, 19 guarded reconciling to D-71's 13 + 5 + the
   fixture, 0 unparsed.
4. It goes red on a new unguarded `main()` at column 0 **and** indented, stays green on a
   same-line guard **and** on `isDirectEntrypoint`, and rejects a hand-added allowlist entry.
5. Its detectors can fail: 10 fixtures in both directions, 5/5 idioms positively attributed, and
   6 mutations including the inverse one.

**NOT PROVEN — and I claim none of it**

1. **That the guard fires at runtime in any of the eight files.** No process evaluated any of
   them outside the vitest suites. M0-T65's limit is inherited unchanged.
2. **That `migrate.ts` still runs correctly under the deploy's `npx tsx scripts/migrate.ts`.**
   I did not run it. What I have is: the relative extensionless import form is already used in
   this tree (`ledger_writer_worker.ts` imports `'../../src/lib/pariprashna/arm3/drain'`), the
   deploy runs from a full checkout so the new file is present, explicit `tsc` reports 0 errors
   on it, and three existing suites import these modules and pass. **That is not the same as a
   deploy.**
3. **That the ratchet catches every reintroduction form.** Known blind spots, stated: `.mts` /
   `.cts` (F-P); anything outside `platform/scripts`; an entrypoint whose function is not named
   `main`; a program invoked through a dynamic `import()` or an indirect reference; a
   sufficiently exotic file the brace scanner mis-reads — though that class is now *loud* rather
   than silent.
4. **That "fails the build" is true of the build.** It is true of the job. See F-R.
5. **That the 71 residual files are safe.** They are the same hazard M0-T64 triaged; the ratchet
   carries them openly, it does not improve them.

---

## 6 — What I did NOT do

- **Did not repair any of the 76.** The 5 that left the allowlist were repaired by M0-T65 before
  I started; my scan measured that, it did not cause it.
- **Did not touch** `tsconfig.json`, `main`, any migration, any asset data, any registry row, any
  credential, `A3_env_matrix.md`, or any of Wave 2's 53 files.
- **Did not execute** any of M0-T65's five destructive scripts — not directly, not by import, not
  with a stub env — and did not mutate any of them.
- **Did not add anything to the allowlist**, and built the guard so that I could not have.
- **Did not weaken any test to make something pass.** The two suites I edited each gained
  assertions and kept all their existing ones.
- **Did not change branch protection**, and did not claim the effect of doing so.

---

## 7 — What I am unsure about

1. **Whether `migrate.ts` should have been rewired at all.** It is the deploy-time migrator and
   the only one of the eight whose failure lands on production. The reasoning for including it is
   in §5 NOT-PROVEN item 2, and the honest position is that I traded a *small, unmeasured* new
   risk (a module specifier that must resolve at deploy time) for the removal of a *large,
   measured* one (a security-relevant predicate in eight divergeable copies). If ADHIKĀRIN would
   rather `migrate.ts` kept its private copy, reverting that one file is a three-line change and
   the `CONSUMERS` test will then correctly fail until its exclusion is written down.
2. **Whether `EXTENDED_SUFFIXES` reporting is the right disposition for F-P**, or whether the
   three `.mts` files should simply have been left unmentioned until ADHIKĀRIN rules. I chose to
   report because an unstated hole reads as coverage, but reporting a defect the ratchet may not
   gate on is a shape I have not seen elsewhere in this campaign.
3. **Whether `COVERAGE_FLOOR = 5` will actually be raised at Wave 2.** The floor stops the list
   shrinking; nothing forces it to rise when the population does. That is a ratchet on the wrong
   quantity and I could not think of a way to close it that did not itself need hand-maintenance.
4. **Whether the brace scanner has a false negative I have not found.** Its worst failure mode is
   now loud rather than silent, and it reconciles exactly against the one baseline available to
   check it against — but "reconciles against the only list I can check" is weaker than "is
   correct", and the 12-file bug is what taught me to say so.
