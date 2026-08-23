# KĀRAKA M0-T69 → PARĪKṢAKA — report (observation, not verdict)

**Task:** WORK_QUEUE `M0-T69`, on **F-T63-2** (M0-T63's finding against its own work) and
**D-89** (two-sided anchors mandatory).
**Branch:** `campaign/nirmana-autonomous`.
**Files changed:** ONE — `00_ARCHITECTURE/control/test_m0_deferral_register_scope.py`.

I certify nothing below (I16 / charter H7). Every figure is a measurement, with the command
that produced it. Where a claim rests on argument rather than measurement I say so.

---

## 0 — The answer, stated first

M0-T63's 15/15 cross-check now has a detector. It is **T7** in the scope test, and it fails
if `origin_tally()`'s reconstruction and `_meta.reading_history[0]`'s recorded snapshot
disagree in any of the 15 bucket cells.

**D-89 was the whole difficulty and it is where the estimate broke.** This is a two-sided
comparison whose two sides can each evaporate, so the comparison alone is not the test:
each side is anchored independently on its **shape**, and **T8 proves each anchor and each
side of the comparison fires on its own** — four one-sided mutations, two per side.

**The `~6 lines` estimate is wrong, and I measured rather than inherited it: `git diff
--numstat` reads `229 4`.** The bare comparison really is about six lines — and six lines
is exactly the artifact D-89 was written about, because those six lines pass when both
sides are absent. §5 breaks the 229 down and says what each part bought.

---

## 1 — Preconditions, in the order the dispatch required

```
$ git rev-parse --abbrev-ref HEAD                       campaign/nirmana-autonomous
$ python3 00_ARCHITECTURE/control/test_m0_deferral_register_scope.py
ALL CHECKS PASSED…                                      PRE-EDIT SCOPE TEST EXIT: 0
                                                        (T1–T6: 20 PASS, 0 FAIL)
$ shasum -a 256 platform/scripts/governance/asset_catalogue_disclosed_residuals.json
4a61c2e5fe97f3145f30d1a247464eabe8eb51aa1caba1447565936969b552b5
$ git diff --quiet HEAD -- <that file>                  exit 0 (equal to its HEAD blob)
$ shasum -a 256 …/M0_DEFERRAL_REGISTER_v1_0.md          b846926588476614967cc898d8bda3ac…
$ shasum -a 256 …/M0_DEFERRAL_REGISTER_v1_0.json        58867addad0e17ce075625567ff79e62…
```

T62's guard passed **before** I touched anything, as the dispatch required.

---

## 2 — What I added, exactly

All of it in `test_m0_deferral_register_scope.py`; the generator itself is **untouched**.

### 2.1 — T7, the 15-cell cross-check with an anchor on each side

Four pure helpers plus the test:

| symbol | what it is |
|---|---|
| `origin_side(mod)` | **Side A** — reconstructed NOW from per-entry stamps: `origin_tally(CRITERIA)`, `origin_tally(RULES)`, and their sum as `total` |
| `recorded_side(doc)` | **Side B** — recorded THEN by M0-T31: `_meta.reading_history[0].tally`, read from the live JSON, read-only |
| `anchor_problems(side, …)` | the D-89 anchor, run on **each side separately** |
| `cell_divergences(a, b, …)` | the 15 cells; **pure and deliberately unanchored**, so T8 can demonstrate what it does on two empty sides |

**The anchor asserts shape, not truthiness** (D-89's explicit requirement): three splits ×
five buckets present; bucket keys exactly `BUCKETS`; every cell a non-bool `int`; each
split's cells summing to the population it covers (12 / 20 / 32 — every entry lands in
exactly one bucket); and `total == criteria + rules` per bucket. If either anchor fails,
T7 **abandons the comparison and records a failure** rather than comparing.

`T7b` additionally asserts the arithmetic M0-T63 reported as "closing unaided": 11
originally UNEXAMINED − 8 since classified = 3, and `tally()` counts 3 today. This is
**not** a tautology — it is false the moment any entry is reclassified *into* UNEXAMINED.

### 2.2 — T8, the mutation control, one-sided in both directions

| mutation | side | what must catch it |
|---|---|---|
| **M3** `origin_bucket()` forgets the stamps (returns `e["bucket"]`) | derived | passes ANCHOR A (wrong but well-formed), then **the comparison** — 11/15 cells diverge |
| **M4** one entry moved between buckets in reading 1, all sums preserved | recorded | passes ANCHOR B, then **the comparison** — 4/15 cells diverge |
| **M5** `origin_tally()` returns `{}` | derived | **ANCHOR A**; ANCHOR B asserted still green, so the failure is attributable to side A alone |
| **M6** ×4: no `_meta` / no `reading_history` / empty list / reading 1 carries no `tally` | recorded | **ANCHOR B**; ANCHOR A asserted still green |

**M5 also reproduces D-89 in place, as an assertion:** `cell_divergences({}, {}, BUCKETS)`
returns **zero divergences** — a vacuous pass — and the test asserts that it does, so the
file itself records that the anchors, not the comparison, are what stand between the
campaign and a green comparing nothing to nothing.

### 2.3 — D-77: no mutation window was opened

**Every mutation is on a copy.** Generator mutations are written into a `tempfile`
sandbox and imported from there (`load_mutated_generator()`, following M0-T62's own
sandbox precedent); tally mutations are `copy.deepcopy`'d in memory. **No live file was
broken at any point, so there is no window to announce.** My heartbeats say so explicitly.
I stayed entirely out of `platform/scripts/governance/check_entrypoint_guard_ratchet.py`
(KĀRAKA-M0-T68's open window).

### 2.4 — One honesty fix inside my own new lines

`check()` prints its `detail` on **PASS as well as FAIL**. Written in the file's existing
idiom my details read as counterfactual claims on a green line (`"11 − 8 != 3"` printed
next to `PASS`). I rewrote **my own** details to be true in both directions
(`"11 − 8 = 3; tally() counts 3"`, `"4 of 15 cells diverge under M4"`). I did **not**
touch T1–T6's existing lines, which have the same quirk — filed as F-T69-3 instead.

---

## 3 — What I observed (verbatim)

### 3.1 — The suite, live

```
T7 — 15-cell cross-check: origin_tally() reconstruction vs reading_history[0] (F-T63-2)
  PASS  ANCHOR A — the DERIVED side extracted 3×5 well-formed cells over 12+20 entries
  PASS  ANCHOR B — the RECORDED side (reading_history[0]) extracted 3×5 well-formed cells
  PASS  T7 — all 15 bucket cells agree: the reconstruction from per-entry stamps equals
              M0-T31's v1.0 snapshot
        criteria: {REPAIRABLE 3, DEFERRED 2, RESERVED 1, UNEXAMINED 5, AT-ZERO 1}
           rules: {REPAIRABLE 3, DEFERRED 10, RESERVED 1, UNEXAMINED 6, AT-ZERO 0}
           total: {REPAIRABLE 6, DEFERRED 12, RESERVED 2, UNEXAMINED 11, AT-ZERO 1}
  PASS  T7b — the arithmetic closes unaided … — 11 − 8 = 3; tally() counts 3

T8 — MUTATION CONTROL for T7: each side must turn it RED on its own (D-89)
  PASS  M3 … still passes ANCHOR A (must reach the COMPARISON, not be swallowed)
  PASS  M3 turns T7 RED …            — 11 of 15 cells diverge under M3
  PASS  M4 … still passes ANCHOR B
  PASS  M4 turns T7 RED …            — 4 of 15 cells diverge under M4
  PASS  M5 (origin_tally returns nothing) is caught by ANCHOR A — derived.criteria: absent
        or empty; derived.rules: absent or empty; derived.total: cells sum to 0, expected 32
  PASS  M5 — and ANCHOR B stayed green, so the failure is attributable to side A alone
  PASS  M5 — D-89 REPRODUCED: the bare 15-cell comparison of two ABSENT sides is a VACUOUS
        PASS … — bare comparison of {} vs {}: 0 divergences reported
  PASS  M6 (no _meta) / (no reading_history) / (empty reading_history) / (reading 1 carries
        no tally) — each caught by ANCHOR B
  PASS  M6 — and ANCHOR A stayed green, so the failure is attributable to side B alone

ALL CHECKS PASSED. …
POST-EDIT SUITE EXIT: 0        (33 PASS, 0 FAIL — was 20 PASS)
```

### 3.2 — The wired-up test really goes red (T8 proves the predicates; this proves the test)

T8 exercises the pure helpers. That is not the same as proving `t7_origin_cross_check()`
itself fails, so I proved that separately, **out of band and uncommitted**, by driving the
test module with one side patched at a time (scratchpad script, not added to the repo):

```
[A1 derived: origin_bucket ignores stamps]   FAILURES=1  → T7 (11 cells diverge)
[A2 derived: origin_tally returns {}]        FAILURES=2  → ANCHOR A + "comparison ABANDONED"
[B1 recorded: one entry moved between buckets] FAILURES=1 → T7 (4 cells diverge)
[B2 recorded: reading_history absent]        FAILURES=2  → ANCHOR B + "comparison ABANDONED"
[HARNESS main() with the recorded side alone mutated]     main() EXIT = 1
```

**The harness returns 1.** A suite that cannot return 1 is an unearned green (§N.8); this
one has now been shown to return 1 from a *one-sided* fault, which is the D-89 property.

### 3.3 — Nothing else moved

```
$ shasum -a 256 platform/scripts/governance/asset_catalogue_disclosed_residuals.json
4a61c2e5fe97f3145f30d1a247464eabe8eb51aa1caba1447565936969b552b5   ← IDENTICAL to §1
$ git diff --quiet HEAD -- <that file>                                exit 0
$ shasum -a 256 …/M0_DEFERRAL_REGISTER_v1_0.md    b846926588476614967cc898d8bda3ac…  ← same
$ shasum -a 256 …/M0_DEFERRAL_REGISTER_v1_0.json  58867addad0e17ce075625567ff79e62…  ← same
$ git status --porcelain 00_ARCHITECTURE/control/ platform/scripts/governance/
 M 00_ARCHITECTURE/control/nirmana_tracker.html          ← NOT MINE (modified before I
 M 00_ARCHITECTURE/control/test_m0_deferral_register_scope.py   started; LEKHAKA's surface)
```

**I did not run the generator against the live tree and did not regenerate the register.**
The register's `.md`/`.json` shas are bit-for-bit what they were before I started. The only
generator runs were inside T2/T3's throwaway sandbox, which is what that test has always done.

---

## 4 — What I did NOT do

- Did not touch `m0_deferral_register.py` — the generator is unmodified.
- Did not regenerate `M0_DEFERRAL_REGISTER_v1_0.{md,json}` (dispatch prohibition).
- Did not touch `asset_catalogue_disclosed_residuals.json`; verified byte-identical after.
- Did not touch `check_entrypoint_guard_ratchet.py` (M0-T68's open D-77 window) or anything
  else under `platform/scripts/governance/`.
- Did not edit T1–T6's existing checks or their strings, only appended after them.
- Did not commit `nirmana_tracker.html`, which another agent had already modified.
- No `main` (H2), no migration, no DB, no credential (P4), no asset data (I14), no asset
  outside the open rung (I13 — none is open), no `state/*.jsonl` beyond my own heartbeat
  and the WORK_QUEUE completion line.
- Did not weaken, skip or bypass any existing check to make anything pass (H3).

---

## 5 — The estimate, verified rather than inherited

The dispatch told me to verify T63's `~6 lines` rather than inherit it, citing T66's
"three-line change" that became ~47. **Measured: `git diff --numstat` → `229 4`.** Of the
229 added lines: 33 comment, 28 blank, 168 code-or-string.

Where the 229 went, and why none of it is optional under D-89:

| part | ~lines | could it have been dropped? |
|---|--:|---|
| the bare comparison + one `check()` — **T63's ~6 lines, and they are right** | 6 | no |
| `anchor_problems()` — the D-89 anchor, both sides | 34 | **no: without it the 6 lines pass on two absent sides** |
| `origin_side()` / `recorded_side()` extractors | 12 | no — needed to have two sides to anchor |
| `load_mutated_generator()` (sandboxed, D-77-clean) | 15 | only by mutating in place, which D-77 makes costlier |
| **T8**, four one-sided mutations + the vacuity assertion | 60 | **no: D-89 requires each side proven independently** |
| T7b, the arithmetic closure | 10 | yes — it is the one genuinely additive part |
| docstring/comments recording why (F-T63-2, D-89, D-77) | 61 | yes, at the cost of the next reader |

**The estimate was not careless — it correctly sized the assertion and did not size the
anchor or its proof.** That is the same shape as D-89's own finding about D-86 part 4:
the oracle was specified and the anchor was forgotten, and the anchor is ~10× the oracle.

---

## 6 — Findings (routed to `mailbox/to_conductor/`)

- **F-T69-1 — the anchor's population sums will fire on a legitimate change.** ANCHOR A
  and B both assert each split sums to 12/20/32. If a future task **adds an entry** to
  `CRITERIA` or `RULES`, side A (reconstructed from today's entries) counts it and side B
  (M0-T31's frozen v1.0 snapshot) cannot — so both the sum anchor and the cell comparison
  go red on a correct change. **I consider this the right behaviour and chose it
  deliberately**: an honest red saying "these two sides are no longer comparable, decide
  what reading 1 means now" beats a silent pass. But it is a decision, whoever hits it
  should know it was made on purpose, and the fix is a reconciliation rule, not a
  loosened anchor.
- **F-T69-2 — `origin_bucket()`'s key ordering is still unexercised** (M0-T63's own §6.2).
  No entry carries both `prior_bucket_m0t31` and `prior_bucket_v1_1`, so T7 does not test
  the "earlier stamp wins" rule; it would pass under either ordering today. Not fixable
  without a synthetic entry, which I did not invent (H6).
- **F-T69-3 — `check()` prints its `detail` on PASS as well as FAIL**, so several existing
  green lines print statements that are false of the passing run ("the comparison stayed
  green while the reconstruction was broken", printed next to `PASS`). Cosmetic, but this
  campaign's whole subject is signals that say more than their detector checked. I fixed
  it in my own lines only; T1–T6 are M0-T62's certified work and outside my grant.
- **F-T69-4 — T7 compares 15 cells but only 10 are independent.** `total` is
  `criteria + rules` on side A by construction, and the anchor now asserts the same
  identity on side B, so the `total` row can only diverge if a split row already did.
  15/15 is the honest count of cells compared; **10 is the honest count of independent
  agreements.** M0-T63's corroboration is not weakened by this — it is just worth stating
  precisely, since "15 cells agree" reads stronger than what is actually being claimed.

---

## 7 — What I am unsure about

1. **Whether T7 belongs in this file at all.** It is a *cross-check on the register's
   content*, living in a test whose subject is the generator's *write scope*. I put it
   here because the dispatch named this file and because it is the file that already
   loads the generator and owns the mutation-control idiom — but the module docstring now
   describes two different jobs, and someone may reasonably want the cross-check split out.
2. **Whether the sum anchor is too strong** — see F-T69-1. I argued myself into it; I did
   not measure my way into it, and it is the one part of this that is judgement.
3. **The out-of-band harness proof (§3.2) is not committed.** It monkeypatches the test
   module from a scratchpad script. T8 covers the same ground through committed code, but
   the *wired-up-test-goes-red* evidence specifically exists only in this report. I chose
   not to commit a script that patches a test's internals; that may be the wrong call.
4. **I did not re-derive M0-T63's underlying claim** that `prior_bucket_*` stamps are
   complete and correct. T7 proves the reconstruction agrees with the v1.0 snapshot; if
   both were wrong in the same way, T7 would be green. Two mechanisms agreeing is strong
   evidence, not proof, and the dispatch's own framing ("by a completely different
   mechanism") is the reason it is strong.

---

## 8 — Certification

**None.** I built this; I may not verify it (I16 / charter H7). PARĪKṢAKA decides.
