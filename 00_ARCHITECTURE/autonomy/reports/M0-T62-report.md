# KĀRAKA M0-T62 → PARĪKṢAKA — report (observation, not verdict)

**Task:** Standing Queue **SQ-12** / WORK_QUEUE `M0-T62` (dispatched 2026-08-23T15:43Z).
Source ruling: **ADHIKĀRIN D-44 part 4**.
**Branch:** `campaign/nirmana-autonomous`. **Files changed:** two, both under
`00_ARCHITECTURE/control/`.

I do not certify anything below (I16 / H7). Every number is a measurement I ran; where I
could not measure something I say so.

---

## 0 — The answer, stated first

**I chose OPTION 1: the generator stops writing that path.**

`00_ARCHITECTURE/control/m0_deferral_register.py` no longer writes
`platform/scripts/governance/asset_catalogue_disclosed_residuals.json`. It now READS that
file and PRINTS the divergence, and its declared write scope is enforced at runtime by
`DECLARED_WRITES` + `_write()` rather than asserted in a docstring.

I was told to pick on the merits and not to default. The merits, in the order I established
them, are in §2. The short form: **nothing depends on the write, and the thing that used to
depend on it stopped depending on it three tasks ago without the generator noticing.**

---

## 1 — Baseline proof, taken BEFORE anything else (R2 / D-44 part 2)

```
$ git rev-parse --abbrev-ref HEAD
campaign/nirmana-autonomous

$ git diff --quiet HEAD -- platform/scripts/governance/asset_catalogue_disclosed_residuals.json
$ echo $?
0

$ shasum -a 256 platform/scripts/governance/asset_catalogue_disclosed_residuals.json
4a61c2e5fe97f3145f30d1a247464eabe8eb51aa1caba1447565936969b552b5

$ git show HEAD:platform/scripts/governance/asset_catalogue_disclosed_residuals.json | shasum -a 256
4a61c2e5fe97f3145f30d1a247464eabe8eb51aa1caba1447565936969b552b5
```

Re-checked at the end of the task, after all work: **identical, exit 0, same sha.**
`git status --porcelain` shows the file is not modified.

**I never ran the generator against the live tree.** Every run in this report happened
inside a throwaway copy. I did not need `git checkout --` at any point, which is the whole
point of SQ-12.

---

## 2 — Why option 1 and not option 2 — the evidence, in the order I gathered it

SQ-12 offers two acceptable answers and warns that choosing option 1 when a consumer
genuinely needs the write would be a worse defect than the one being fixed. So I looked for
that consumer first.

**(a) Who reads the file.** Exactly one code path, found by a repo-wide grep over `*.py`,
`*.ts`, `*.mjs`, `*.js`, `*.yml`, `*.yaml`, `*.json`, `*.sh` (excluding `node_modules`):

```
platform/scripts/governance/check_asset_catalogue_contract.py:136:
    RESIDUALS_PATH = HERE / "asset_catalogue_disclosed_residuals.json"
```

Nothing else in the repo reads it. Nothing else in the repo **writes** it —
`m0_deferral_register.py`'s `_write_disclosure_block()` was the only writer.

**(b) What the reader needs.** The guard reads `deferred_rule_disclosures` by rule id and
computes each rule's `effective_severity` from it. It therefore needs the **authorised**
content — D-54's fifteen disclosures on D-57's corrected ground. That content is NOT what
the generator produces.

**(c) The block has been detached from the generator since M0-T49.** Measured at
2026-08-23T15:5xZ by importing the module (import is side-effect-free — no module-level
I/O) and comparing against the live file:

| | live file | in-file `DISCLOSURE_DRAFT` |
|---|---|---|
| `deferred_rule_disclosures` entries | **19** | **16** |
| entries present only in live | `C-11`, `X-03`, `X-05` | — |
| entries present only in draft | — | none |
| entries present in both but DIFFERENT | **12** | (`C-01 C-02 C-03 C-04 C-06 C-07 C-08 C-15 C-17 C-20 C-21 C-28_residual`) |
| entries byte-equal in both | **4** (`C-22 C-25 C-26 C-27`) | |
| `deferred_rule_disclosures_not_drafted` values differing | **4 of 4** | |
| `deferred_rule_disclosures_count` | 19 | 16 |

**(d) The decisive one.** `grep -c 'm0_deferral_register\|hand-edit\|regenerate'` over the
live JSON returns **0**. The live file makes **no claim** that the generator owns it — the
"Source of truth: m0_deferral_register.py (DISCLOSURE_DRAFT); regenerate, do not hand-edit"
sentence exists only inside the generator's own would-be-written README string, and was
replaced in the live file when M0-T49 rewrote that README. The ownership claim survives
only in the writer, not in the thing written.

**Conclusion.** Option 2 (declare the path and keep the write) would require declaring a
write whose content is *known-wrong and known-destructive*. It would make the declaration
honest and leave the destruction in place — a documented landmine is still a landmine, and
SQ-12's acceptance criterion is that no agent should need git to undo it again. Option 1
removes the destruction; the ownership it removes was already gone in fact. **The live file
is the source of truth for its own block.**

---

## 3 — The damage a run would have done, DEMONSTRATED rather than argued

I ran the **pre-change** generator (`git show HEAD:…/m0_deferral_register.py`) inside a
throwaway tree seeded with byte-copies of the live register outputs and the live residuals
JSON, and diffed the result against the live file. The live tree was never involved.

```
residuals JSON, live                          4a61c2e5fe97f3145f30d1a247464eabe8eb51aa…
residuals JSON, after OLD generator run       6900d1b4297088fbefb577dcf550e42bbe0e70ff…   ← CHANGED
residuals JSON, after NEW generator run       4a61c2e5fe97f3145f30d1a247464eabe8eb51aa…   ← byte-identical
```

What the old run did to D-54's authorisations, measured on the copy:

| measure | live | after OLD generator run |
|---|---|---|
| `deferred_rule_disclosures` entries | 19 | **16** |
| entries **deleted outright** | — | `C-11`, `X-03`, `X-05` |
| entries silently rewritten | — | 12 |
| entries carrying `authorised_by` | **15** | **0** |
| entries with `gating_effect: "non_gating"` | **15** | **0** |
| `deferred_rule_disclosures_count` | 19 | 16 |
| `deferred_rule_disclosures_README` | T49/T51/T55 text | reverted to M0-T36 text |
| `_README`, `authored_by`, `authored_at`, `certified_by`, `disclosed_additions*`, `zero_consumer_dispositions` | — | **preserved byte-for-byte** |

So the function's own docstring claim ("PRESERVES every other key byte-for-byte") was TRUE
and entirely beside the point: the four keys it owned had stopped being its own output, so
"preserving the others" was never the safety property that mattered.

**All fifteen of D-54's authorised disclosures lose their authorisation in a single run** —
three deleted, twelve reverted to `gating_effect: "none"` with no `authorised_by`. The
generator prints a success line and a tally while doing it. That is the hazard SUTRADHĀRA
recorded as the SQ-12→SQ-14 ordering constraint, and it is real; I have now seen it happen
on a copy.

**A second-order effect I did not measure and am flagging rather than asserting:** the
guard's `disclosed_non_gating` count would presumably go 15→0 and the fifteen BLOCKING
failures would gate again. I did NOT run the guard `--live` to confirm this — that needs a
DB credential and is outside my task. It could be a reversion in either direction
(un-demoting rather than demoting); either way it is invisible, which is the defect.

---

## 4 — Exactly what I changed

### 4.1 `00_ARCHITECTURE/control/m0_deferral_register.py` (modified)

1. **`DECLARED_WRITES` + `_write()` + `ScopeViolation`** (new, after `OUT_MD`/`OUT_JSON`).
   `DECLARED_WRITES = (OUT_MD, OUT_JSON)` is the declaration; `_write(path, text)` is its
   detector and is now the module's ONLY write path. It compares **resolved** paths (so a
   relative or symlinked spelling cannot slip through) and raises **before** opening the
   file, so a refused write leaves nothing partially written. The declaration and the
   detector are the same object — which is the §N.8 point SQ-12 makes.
2. **`_write_disclosure_block()` DELETED**, and its body deleted with it — not commented
   out. A commented-out write is a landmine; there is an in-place comment saying so where
   the body used to be, plus a `_DELETED_write_disclosure_block__M0_T62()` tombstone whose
   docstring records what it used to do and which raises `NotImplementedError` if called.
3. **`_report_disclosure_divergence()`** (new, read-only) replaces it. It reads the live
   file and returns a one-line report of the divergence (entry counts, only-live,
   only-draft, differing, identical, `not_drafted` mismatches) plus the statement that the
   live file is authoritative. It **reconciles nothing in either direction** — reconciling
   is a charter G-power (catalogue-gate disposition), not a generator's and not a KĀRAKA's.
   It returns a plain note rather than raising if the file is missing or unparseable,
   because this module's outputs do not depend on it.
4. **`main` routes both writes through `_write()`** and calls the read-only reporter.
5. **`RESIDUALS_JSON` declaration** carries a comment saying it is READ ONLY and
   deliberately not in `DECLARED_WRITES`.
6. **Prose swept for statements that assert the old state** (SQ-20 doctrine):
   - module docstring: gains an explicit **DECLARED WRITE SCOPE** section with the full
     history, the measured divergence and the reason the write was removed;
   - `PROVENANCE`: the `guard_files_read_not_written` list — which the module used to
     **falsify**, since it named the residuals JSON while writing it — gains a sibling
     `write_scope_enforced_by` naming `DECLARED_WRITES`/`_write()` and the test. **The list
     itself needed no edit: removing the write is what made it true.**
   - §9 header comment: now states plainly that `DISCLOSURE_DRAFT` is the M0-T36
     **historical draft** and is written nowhere;
   - `render()` §10: adds a paragraph saying the same in the rendered register;
   - `render()` §12.7: the clause that memorialised the defect —
     *«so a re-run of this generator's `_write_disclosure_block()` should not change …; if
     it does, M0-T46 reverted that file…»* — is removed from the live text and **preserved
     verbatim in an M0-T62 amendment paragraph**, because it is the defect's own confession
     written by the agent that hit it. That sentence describes an agent planning to reach
     for `git checkout --`;
   - the "tension this task found" paragraph, which cited
     `_write_disclosure_block()`'s docstring by name, re-worded to point at where that text
     now lives. **Its substance (the D-39/F-T36-3 evidence-timing question) is untouched.**

**No classification changed.** Proved by running the old and new generators in two separate
sandboxes and comparing outputs: the JSON payload differs **only** in `_meta`
(timestamp/`regenerated_count`); the tally is identical both sides —
`REPAIRABLE-IN-M0=5 · DEFERRED-WITH-REASON=19 · RESERVED=2 · UNEXAMINED=3 ·
AT-ZERO-WITH-EXPOSURE=3`. The `.md` differs in exactly the three prose locations listed
above plus the timestamp line (12 diff lines total).

### 4.2 `00_ARCHITECTURE/control/test_m0_deferral_register_scope.py` (new)

The detector SQ-12 asked for. `python3 00_ARCHITECTURE/control/test_m0_deferral_register_scope.py`
→ exit 0 pass / 1 fail. No DB, no network, no live-tree writes.

| id | what it proves |
|---|---|
| T1 | `DECLARED_WRITES` exists and names exactly the two register outputs; `_write` and `_report_disclosure_divergence` exist; `_write_disclosure_block` is gone; the residuals path is NOT declared |
| T2 | a **real run** inside a throwaway copy of the tree changes ONLY the two declared paths |
| T3 | the residuals JSON is **byte-identical** after that run (the specific regression) |
| T4 | `_write()` raises `ScopeViolation` on an undeclared path **and leaves no file on disk** |
| T5 | static AST scan: every `write_text`/`write_bytes`/`open(…,'w')` call in the module is inside `_write()` — plus a non-vacuity assertion that the scanner found at least one write call at all |
| T6 | **MUTATION CONTROL** |

**T6 is the part that earns the green** (§N.8: a test never shown to fail is an unearned
signal). It rebuilds the generator twice, deliberately broken, and **fails unless the checks
above go red**:

- **M1** — a raw `RESIDUALS_JSON.write_text(...)` appended, bypassing the guard entirely.
  T6 asserts the sandbox byte-comparison detects it AND that the T5 AST scan detects it.
- **M2** — `_write(RESIDUALS_JSON, …)`, i.e. an undeclared path routed *through* the guard.
  T6 asserts the run exits non-zero, that `ScopeViolation` appears in its output, and that
  the residuals copy was left untouched (refused before writing).

**Verbatim result on the shipped code — 16/16:**

```
T1 … PASS ×6      T2/T3 … PASS ×4      T4 … PASS ×2      T5 … PASS ×2      T6 … PASS ×4
ALL CHECKS PASSED. The generator's declared write scope is enforced, the residuals JSON is
untouched by a run, and the detector was shown to go red on two deliberately broken copies.
EXIT=0
```

---

## 5 — What I did NOT do

- **I did not edit `platform/scripts/governance/asset_catalogue_disclosed_residuals.json`.**
  Baseline sha proven equal to HEAD before and after; `git status` clean for that path.
  Its contents are D-54/D-57 authorised and are not mine. **I found nothing wrong with its
  contents** — the wrongness was entirely in the writer.
- **I did not edit** `check_asset_catalogue_contract.py`, `platform/scripts/migrate.ts`, or
  `platform/scripts/pariprashna/ledger_writer_worker.ts` (M0-T56/T61/T60 are live in them).
- **I did not run the generator against the live tree**, and I did not regenerate
  `M0_DEFERRAL_REGISTER_v1_0.md` / `.json`. See finding F-T62-1 — this is a deliberate
  choice I could have made the other way, and I say why there rather than burying it.
- **I did not run any guard `--live`**, touch the DB, read any credential (P4), touch
  `ka_gochara_sweep` (P1), touch `.github/`, or touch any asset, registry row or layer
  (I13/I14 — nothing in this task goes near one).
- **I did not certify** that this is correct, complete or sufficient. That is PARĪKṢAKA's.

---

## 6 — What I am unsure about, plainly

1. **Whether not regenerating the register outputs was the right call.** SQ-20's doctrine
   says sweep for statements asserting the old state. Two on-disk artifacts
   (`M0_DEFERRAL_REGISTER_v1_0.md` §10 and §12.7, and its `.json`) still carry the pre-T62
   prose, and one safe command would fix them. I chose not to, because a regeneration also
   rewrites `_meta.generated` and `reading_history` — a governance-record claim that SQ-14
   is dispatched to make — and because keeping my change to two files keeps it atomic and
   trivially revertible if PARĪKṢAKA rejects it. **I could be wrong about this.** Routed as
   F-T62-1 rather than decided quietly.
2. **`M0_CLOSE_READINESS_v1_0.md:220`** names `_write_disclosure_block()` in the present
   tense. It is another task's dated record, true when written, so I routed it (F-T62-2)
   instead of editing it. If PARĪKṢAKA reads that as inside my fence, say so and I will
   accept the finding.
3. **The test is not wired into CI.** I deliberately did not touch
   `.github/workflows/nirmana-m0-guards.yml`: the register itself records an unresolved
   "CI edit scope" question, and D-41's CI-edit-by-direction rule is a strengthening/
   weakening test I am not the one to apply here. Routed as F-T62-3. **Until it is wired,
   the detector only runs when someone runs it** — that is a real limitation of this fix
   and I am not going to describe it as anything else.
4. **My sweep was this file plus targeted greps** (`_write_disclosure_block`,
   `asset_catalogue_disclosed_residuals`, `m0_deferral_register`). It was not a semantic
   sweep of the corpus. There may be prose elsewhere asserting that this generator maintains
   that block; I did not find any, which is not the same as there being none.
5. **The `_DELETED_write_disclosure_block__M0_T62()` tombstone is a judgment call.** It is a
   dead function that exists only to be legible to someone grepping. If that reads as clutter
   rather than clarity, deleting it changes no behaviour and breaks no test.

---

## 7 — Commands a verifier can re-run

```bash
cd <repo>
# the detector, including its own mutation controls
python3 00_ARCHITECTURE/control/test_m0_deferral_register_scope.py; echo "exit=$?"

# the residuals file is untouched by this task
git diff --quiet HEAD -- platform/scripts/governance/asset_catalogue_disclosed_residuals.json; echo $?
shasum -a 256 platform/scripts/governance/asset_catalogue_disclosed_residuals.json
# expect 0 and 4a61c2e5fe97f3145f30d1a247464eabe8eb51aa1caba1447565936969b552b5

# reproduce §3 — the old generator's damage, on copies only
T=$(mktemp -d); for v in old new; do mkdir -p $T/$v/00_ARCHITECTURE/control $T/$v/platform/scripts/governance;
  cp 00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.{md,json} $T/$v/00_ARCHITECTURE/control/;
  cp platform/scripts/governance/asset_catalogue_disclosed_residuals.json $T/$v/platform/scripts/governance/; done
git show HEAD:00_ARCHITECTURE/control/m0_deferral_register.py > $T/old/00_ARCHITECTURE/control/m0_deferral_register.py
cp 00_ARCHITECTURE/control/m0_deferral_register.py $T/new/00_ARCHITECTURE/control/
(cd $T/old && python3 00_ARCHITECTURE/control/m0_deferral_register.py >/dev/null)
(cd $T/new && python3 00_ARCHITECTURE/control/m0_deferral_register.py >/dev/null)
shasum -a 256 $T/{old,new}/platform/scripts/governance/asset_catalogue_disclosed_residuals.json \
             platform/scripts/governance/asset_catalogue_disclosed_residuals.json
# expect: old differs; new == live
```

*(Note: the HEAD referenced above is the commit before this task's. After M0-T62 lands,
substitute that commit's parent to reproduce the "old" side.)*

---

## 8 — Findings routed to `mailbox/to_conductor/`

- **F-T62-1** — `M0_DEFERRAL_REGISTER_v1_0.{md,json}` on disk still carry pre-T62 §10/§12.7
  prose; SQ-14's run will refresh them. Exact strings quoted in the finding.
- **F-T62-2** — `M0_CLOSE_READINESS_v1_0.md:220` names the removed function in the present
  tense.
- **F-T62-3** — the new test is not in CI; wiring it needs the unresolved CI-edit-scope
  question answered.
- **F-T62-4** — the SQ-12 → SQ-14 ordering hazard is now **removed**, with the proof; SQ-14
  can run the generator without clobbering the authorised disclosures.

---

**KĀRAKA M0-T62** · report is observation, not verdict (I16 / H7).
