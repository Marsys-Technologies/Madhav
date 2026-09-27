---
artifact: W3-1_C1_REVIEW
canonical_id: W3-1_C1_REVIEW
version: "1.0"
reviewer: independent reviewer (Claude Opus 5.5, fresh context, read-only, not the implementer)
reviewed_on: 2026-09-28
reviews: nikasha_test/wave3/W3-1_REPORT.md v1.1 (CORRECTIONS_APPLIED_PENDING_FOLD) against W3-1_REVIEW.md (d5fd6aed1)
commits: "7 — 68044d4c8 (C2) · 2f00a6b45 (C1+C3) · 5fcc0989e (C4) · 8c279e23e (C5) · 04a9e8c93 (F7) · 383053e9c (F8+F9) · 0c9d90fc2 (report v1.1)"
base_commit: c8cdc0242
head_commit: 0c9d90fc2
verdict: ACCEPT_WITH_CORRECTIONS
---

# Nikaṣa wave 3 — W3-1 corrections review

## §1 — Verdict

**ACCEPT_WITH_CORRECTIONS.** The corrections are document-only. No code change is required, and
no ledger write is required.

**C2, the substantive fix, is correct.** I reproduced it with a real `emit_gaps()` run, not a
hand-built row. The run covered both the CLOSED and the RE-OPENED transition on a hand-owned id.
- The fixed discriminator correctly classifies both transition rows as machine-written.
- A genuine post-cutoff hand row on the same id is still flagged.
- The stated mutation fails exactly 1 of 9 tests, and restoring the code returns 9/9 green.

**Everything else checks out:**
- An isolated six-layer census, run alone, gives exactly 15 verdict changes (11 R60 + 4 R99).
- The suite reads 424 = 398 passed + 24 skipped + the same 2 pre-existing failures.
- Manifest: MATCH.
- Drift: exit 2, from the same two doc fingerprints only.
- The real ledger md5 is `f6b1d3c5…` throughout.
- The scope is clean.

**Four document findings must be fixed before the executor folds** (§7, K1–K4). Two of them
repeat the defect C4 was about: a claim stated as a citation or quotation that the cited source
does not support.
- **K1.** The C4 precedent commit is wrong. The error started in the original review (see §3).
- **K2.** §7 of the report quotes words and a "choice" from the review that the review never
  contained.

**The C2 collision attack found no live collision.** It did find a latent one (§2.3). I record it
as a named residual, not a blocker.

## §2 — C2 attack

### §2.1 The function, before and after

**Before (`02182bf2c`):** `is_hand_written(row) = row.get("owner") != "asset_census"`.

**After (`68044d4c8`):**
- `is_machine_written(row) = str(row.get("detector") or "").startswith("asset_census.py")`.
- `is_hand_written = not is_machine_written`.

**The premise holds at the source.** In `asset_census.py`, `emit_gaps` writes
`detector=f"asset_census.py --layer {census['layer']} ({crit})"` on all three write paths: the
first OPEN, the RE-OPENED and the CLOSED rows. It never carries `detector` forward from the prior
row. It carries only `change`, `owner` and `gate`.

### §2.2 Fixture reproduction, done with a real `emit_gaps()` call

This used a fresh copy of the real 857-line ledger, through `NIKASHA_CONTROL_DIR`, with the clock
patched after `CUTOFF_TS` (script `rev-w3b/c2_repro.py`, `c2_ext.py`).

**Starting state.** The real latest row for `bg_ontology-Dens.served` is line 835:
- owner `"layer packet"`;
- detector `"grep census over the L0 capability directory"`, which is the hand detector R81
  carried forward.

**1. A census PASS on `bg_ontology-Dens.served`**, with the clock at 2026-09-30:
- `emit_gaps` → `(0, 0, 1, 0)`.
- The new row: `state=CLOSED`, `owner="layer packet"` (carried forward),
  `detector="asset_census.py --layer L0 (Dens.served)"`, no `census_run_id`.
- **Fixed** `missing_census_run_id` → `[]`.
- **Owner-only** check → `['bg_ontology-Dens.served']`. This is the original false positive,
  reproduced.

**2. A census FAIL on the same id**, with the clock at 2026-10-01:
- `emit_gaps` → `(0, 0, 0, 1)`, a RE-OPENED row with the owner carried.
- Fixed check → `[]`. Correct.

**3. A genuine post-cutoff hand row on the same id**, with a hand detector and no
`census_run_id`: it is flagged, `['bg_ontology-Dens.served']`. The fix did not blind the rule to
real hand rows.

**4. The real-emit cross-check.** The 26 `Idem.pattern` rows produced by a real
`--layer L0 --emit-gaps` on a fresh copy (§5) give `[]` even with the cutoff forced to `"2000"`.

**One note on the committed test.** The committed fixture's first row, the R81 survivor, carries a
census detector with the hand owner. The real row (line 835) carries the hand detector. This does
not affect the result, because that row is pre-cutoff and the transition row is what is under
test. It does mean the fixture is not a faithful transcription of the real row. See §7, D2.

### §2.3 The mutation, and my own detector-field collision attack

**Mutation,** run in a temporary HEAD worktree (since removed):
- `return not is_machine_written(row)` → `return row.get("owner") != "asset_census"`.
- Result: **1 failed, 8 passed**. The failure is exactly
  `test_owner_only_discriminator_would_have_flagged_a_census_transition_on_a_hand_owned_id`.
- Restored (`cmp` identical): **9 passed**. The claim reproduces exactly.

**Collision attack on the real ledger (all 857 rows): no live collision.**
- 781 rows have a detector beginning `asset_census.py`. **All 781** are in the exact
  `emit_gaps` shape `asset_census.py --layer X (<criterion>)`, their criterion equals the row's
  own criterion, their `gap_id` equals `<asset>-<criterion>`, and their owner is `asset_census`.
- **Zero** rows pair a census-prefixed detector with a non-census owner. **Zero** rows are
  owner=`asset_census` without the prefix.
- The 75 other rows with a `gap_id` (56 gap, 19 opportunity; owners `layer packet`, the pilot
  briefs, `native`, and so on) all carry free-text detectors. None begins with the prefix.

**Latent collision, demonstrated on synthetic rows: real in principle.** The prefix test is
looser than the `emit_gaps` shape, and two plausible hand-authored strings pass it:
- **`asset_census.py:measure()`.** This is the literal `detector` value of all 21 auto-measured
  entries in R78's `CRITERION_REGISTRY`. D4 tells hand rows to use a registered criterion, so an
  author copying the registry entry's detector is a natural slip. **Result:
  `is_machine_written=True`, and the row escapes the check.**
- **A near-miss that already exists in the ledger.** `_layer_all-BT03`'s hand detector is
  `"asset_census --layer L2,L3 reports Build.registered PASS for all five"`. Only the missing
  `.py` keeps it out. The five L0 pilot briefs write "Measured against `asset_census.py --layer
  L0`" as their standard phrasing. The same string with `.py` → **`is_machine_written=True`,
  and the row escapes.**

Both are false negatives. A hand row would silently pass R29, which is the §N.8 defect class: a
PASS with no detector behind it. Neither is live today. The builder's docstring says "a
hand-authored `detector` string … never begins with that literal prefix". That is true of the
ledger today, but it is an unenforced convention stated as a fact.

**A cheap hardening, verified.** Change the test to `re.fullmatch(r"asset_census\.py --layer
(\S+) \((.+)\)", detector)` and require group 2 to equal the row's `criterion`:
- It **disagrees with the current prefix check on 0 of 857 real rows**.
- It rejects both collision shapes.
- It still accepts every real `emit_gaps` row.

A residual would remain: a hand author could copy a census row's exact detector verbatim, as a
fold might do. The only complete fix is the review's own alternative, which is to have
`emit_gaps` stamp `census_run_id` (or an explicit writer marker) on every row it writes. I
recommend both for the next ledger-identity row (§7, D1). This does not block the fold, because
there is no live instance and R29 has no runtime caller yet. Its only enforcement is the test
suite, as the original review noted.

## §3 — C1 / C3 / C4 / C5 spot-checks

**C1, three claims re-measured:**
- **(a) R218's cause: ✓.** `producer_provenance.derived.json`:
  - `scu.catalog.assess_career`, `assess_marriage`, `compose_large_n`, `graha_portrait` carry
    `NO_DETECTOR — no_contract…`;
  - `scu.catalog.call_priority_ranking` carries `NO_DETECTOR — no_relation_in_range…`.
  - All 5 are `editorial: True` in `capability_knowledge.snapshot.json`.
- **(b) The ASSET_ELEVATION_TEMPLATE fingerprint is new this wave: ✓.**
  - sha256 at base `c8cdc0242` is `4927436c17760254…`.
  - `CAPABILITY_MANIFEST.json` at base declares `4927436c177602541dbe…`, so it **matched at
    base**.
  - The HEAD sha is `ff91138491b75ca0…`, and drift at HEAD shows declared `4927436c…` against
    observed `ff911384…`.
  - `bb341cc1` was rotated away earlier, by `23e6844ca`/`090bd9aaa`.
- **(d) 21 criteria: ✓.** `CRITERION_REGISTRY` has 26 entries: 21 `asset_census.py:measure()` and
  5 `NONE`.
- **Stale phrases are gone from the body:** "3 stub", "editorial=false", "20 criteria", "still
  unrotated". They appear only in the §7 history column.

**C3, R99: the PARTIAL status is correctly stated; the follow-up is incomplete.**
- The R99 paragraph opens "folds as PARTIAL, not CLOSED". The report's §7 C3 row says the same.
- **The `has_writer` overclaim is removed from the report: ✓.** The report now states that it
  "does not, and the row does not claim to, distinguish" legitimately-empty from broken.
- **The live census sentences are still identical.** In my HEAD census, ga_prashna and
  mi_abhilekha read the same PARTIAL text after the scope prefix: "…with no layer-plan claim that
  the emptiness is by design — indistinguishable from a writer that has never produced a row".
- The report now states this sameness honestly as a known limit, not as solved. ✓
- **Gaps (→ K3):**
  - The paragraph says the finer distinction is "a named, carried finding for a future row (§3)".
    **§3 has no R99 item.**
  - Two of the three follow-ups C3 required appear nowhere in the report: ga_prashna's latent case
    (ii) (2 prashna charts, 0 positions, never built), and the correction to bg_sarvatobhadra_grid's
    PASS gloss.
  - That gloss still ships in census output today: "(has_writer=false — no writer at all, the
    signal honest enough to read as by-design)". It contradicts the asset's own G01, "blocked on
    an input" (§N.7 item 6).
  - The code comment at `asset_census.py` ~2497–2499 still says `has_writer` is "honest enough to
    distinguish the two". That is a comment, not output. The report correctly says the code is
    unchanged.

**C4, the docstring: fixed as to doc text, wrong as to precedent (→ K1).**
- The apply-script docstring no longer claims the `_schema` doc scopes append-only. It now calls
  line 1 "the one disclosed exception".
- **But the cited precedent is false.** `a72cdf460` ("First production emit") touches
  `asset_gaps.jsonl` only through the hunk `@@ -261,3 +261,570 @@`: 567 appended lines. Line 1 is
  unchanged, and `kind` was already in `_doc` before it.
- I traced every commit that changed line 1. There are exactly three:
  - `63acc0320` created it.
  - **`5973d0132` (2026-09-26) rewrote it in place** to add `kind`, and it also changed line 1's
    key set. At that moment the ledger held **only** the `_schema` line, with zero data rows.
  - `67d5d1aa2` is this wave's R81 write.
- So the real precedent is `5973d0132`, and it is weaker than presented. R81's is the first
  in-place line-1 rewrite made with data rows present.
- The error started in W3-1_REVIEW.md itself (§2 "There is precedent. Commit `a72cdf460`…" and
  §10 C4). The builder copied it faithfully into the docstring (:19) and the report (:158, :165,
  §7 C4 row).
- The disclosure of the rewrite is honest. Only the SHA and the "same thing" claim are wrong.

**C5, R81: ✓, and 30 is the correct figure.**
- Register R81 (v2.6, status column): "all 30 hand gap rows across the five pilots (ontology 10,
  rules 8, ephemeris 6, panchanga 4, sarvatobhadra 2)".
- Re-counted on the pre-write ledger (`c8cdc0242`): **exactly 10/8/6/4/2 = 30** pilot hand
  `kind=gap` rows, all G-numbered, 30 distinct ids. The four `_layer_all` BT gap rows are outside
  "the five pilots".
- T5 §A's own scope is the 11 overlap pairs out of 53 hand rows. The wave-3 prompt (:57) narrows
  R81 to those 11.
- "PARTIAL (11 of 30)" and "19 remaining" are both correct.

## §4 — F7 / F8 / F9

- **F7: ✓.** `grep 320` over the whole of `MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md`
  finds **no match**. Line 526 now reads "40 briefs, 360 gates". The new test asserts
  `"320 gates" not in text` over the whole file, so it guards every occurrence, not only line 526.
- **F8: ✓.** The comment is honest and now reads 5 capabilities, `editorial=true`. The assertion
  itself is unchanged.
  - I re-ran the CLI: **17/24**, with the same per-need table as report §4, and P16 still PASS
    (`scu.bodha.mechanism.network`, 21/32).
  - vitest: 5/5.
- **F9: ✓.** P16 now equals T1 line 171 verbatim, quotes included.
- The report's §6 remark that `finance.prosperity_assessment` accounts for the PASS of
  P09/P10/P15/P22/P24 matches the CLI output.

## §5 — Isolated census re-run

I ran it alone, with no other DB job in flight:
- base `c8cdc0242` in a temporary worktree, then HEAD `0c9d90fc2` in a temporary worktree;
- each with its own scratch `NIKASHA_CONTROL_DIR` and `--out`;
- `--layer all`, read-only proxy.

Both runs exit 2, with **ERRORED 0 in every layer** (so there was no pool exhaustion).

**Result: exactly 15 verdict changes, the same list as the original review.**
- **R60 (11), `Ldgr.source_presence`:**
  - `None→PASS` on bg_dignity_reference, bg_medical_mappings, bg_nakshatra_medical,
    bg_sign_medical, bg_transit_engine, bg_transit_rules, bg_vastu_directions, ga_medical,
    ga_vastu and ka_vedha_gochara;
  - `None→PARTIAL` on ka_gochara_resonance (539/1595).
- **R99 (4), `Build.completion` PASS→PARTIAL:** ga_prashna, mi_abhilekha, mi_seva, mi_vistara.

**The builder's 43-change first attempt.** I cannot reproduce that run. The diagnosis is
consistent with my own clean run: a contention artefact, not a code change.

**emit_gaps dry run,** on a fresh copy, run twice:
- First run: `0 appended, 184 present, 26 closed, 0 re-opened`. All 26 are `Idem.pattern` with
  owner `asset_census`.
- Second run: `0, 184, 0, 0`.
- The report says the second run was `0/183/0/0`. That is a one-off discrepancy in the "already
  present" count, not a change in behaviour (§7, D3).

## §6 — Suite and scope

**Governance suite** (HEAD worktree, no DB credentials): **424 collected = 398 passed +
24 skipped + 2 failed.** The two failures are `test_drift_detector_h35_h38.py::
test_f163_current_row_flagged_predecessor_row_is_not` and
`::test_h35_critical_when_canonical_artifacts_missing`, the same pair as base. ✓

**Manifest:** `manifest_fingerprint.py --check` → MATCH (`1812a4ede55e0b69`). ✓

**Drift,** with no DB credentials in the shell:

| revision | exit | findings |
|---|---|---|
| base | 3 | 2 LOW (DB unreachable) |
| HEAD | 2 | the same 2 LOW, plus exactly 2 HIGH `fingerprint_mismatch` |

The two HIGHs:
- `ASSET_ELEVATION_TEMPLATE`: declared `4927436c…`, observed `ff911384…`;
- `MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY`: declared = base sha `2233d00a…`, observed
  `e577ffe3…`. This moved after F7, as disclosed.

Nothing else is flagged. The report's "1 LOW (`a3_category_not_yet_populated`)" comes from a shell
with DB credentials, so the LOW set is environment-dependent and not a difference in kind.

**Real ledger:** md5 `f6b1d3c5eeff7ec5d56d45448df69d80`, 857 lines, at every checkpoint.
`asset_certs.jsonl` is `514cbdfc…`. I made no writes to either.

**Scope:** `git diff --name-only d5fd6aed1 0c9d90fc2` covers 8 files:
- the report;
- the L0 v3.0 doc;
- `hand_row_provenance.py`;
- the `apply_r80_r81_ledger_migration.py` docstring;
- 2 governance tests;
- the R218 lib and its test.

All of them are wave-3-authored or wave-3-touched surface.

**Forbidden paths:** `git diff --quiet` passes for the ledger, the certs file, all three sealed
tiers, the register, and `asset_census.py`. None of the 7 commits touches `asset_census.py`, so the
brief's allowance for it went unused.

Both temporary worktrees were clean and have been removed.

## §7 — Remaining findings

**Blocking the executor's fold (document corrections only; no code, no ledger).**

**K1 — Wrong C4 precedent** (this started in W3-1_REVIEW.md, not with the builder).
- **Replace `a72cdf460` with `5973d0132`** in four places:
  - the apply-script docstring (:19);
  - W3-1_REPORT.md (:158, :165);
  - the §7 C4 row;
  - the register or decision line the executor writes for R80/R81.
- **State the precedent accurately.** `5973d0132` rewrote line 1, including its key set, when
  the ledger held only the schema row. R81 is the first in-place line-1 rewrite made with data rows
  present.
- **Correct the original review.** W3-1_REVIEW.md §2/§10 carries the same wrong SHA. This review
  supersedes it on that point.
- **Blocks:** the R80/R81 fold.

**K2 — Unsupported quotation in report §7.**
- The report's closing "Not done" paragraph (:450) says the review offered a choice between "add
  the one-query by-design distinction" and "leave the code as-is and correct the report".
- The §7 C3 row quotes: "if that's a larger change than fits here, leave the code as-is and just
  correct the report".
- **Neither text exists in W3-1_REVIEW.md**, at HEAD or at `d5fd6aed1`.
- The path taken (report-only, PARTIAL) is consistent with what C3 actually asked for. The
  attribution is not.
- **Fix:** remove the quotation marks and the attribution, or cite the text's real source.
- **Blocks:** the fold of the report.

**K3 — The C3 follow-up is not registered.**
- Add a §3 item that the R99 fold carries, covering:
  - (1) a per-asset by-design detector; for ga_prashna, `SELECT count(*) FROM prashna_charts
    WHERE chart_id=…`;
  - (2) ga_prashna's latent case (ii): 2 prashna charts with 0 `graha_position` facts, never built;
  - (3) bg_sarvatobhadra_grid's PASS text "honest enough to read as by-design". It still ships and
    contradicts its own G01 "blocked on an input". The stale `has_writer` comment at
    `asset_census.py` ~2497 goes with it.
- **Blocks:** R99's register row, which must fold PARTIAL with these three named.

**K4 — F6 wording errors.**
- **§7 F6 row.** It cites `bg_rules-Complete.detector`→`Complete.depth`. No such id exists. The
  actual supersessions are:
  - `bg_rules-Carr.detector` → `bg_rules-Carr.D1`;
  - `bg_rules-Complete.depth` → `bg_rules-Completeness.depth.dasha_link`.
- **§3 item 5.** It says "any of the four other Carr-superseded assets". There are four
  Carr-superseded assets in total (ontology, ephemeris, panchanga, rules), so it should read "three
  other".
- **Blocks:** the fold of the report (F6 is raised to the native from this text).

**Non-blocking, carried as named residuals.**

**D1 — Latent detector-prefix collision in R29's discriminator (§2.3).**
- Recommended: tighten to the exact `emit_gaps` shape bound to the row's criterion (0 real-row
  disagreement), and/or have `emit_gaps` stamp `census_run_id` on its own rows.
- Also soften the docstring's "never begins with that literal prefix" to "none does today; not
  enforced".
- The R15/R29 fold may read CLOSED for the demonstrated C2 defect, with D1 registered as the next
  hardening row.

**D2 — The C2 test fixture's first row is not transcribed from the real row.** The real row
carries the hand detector. Cosmetic.

**D3 — The report's emit second-run "183 present" reproduces as 184.** Cosmetic.

**Carried unchanged from the first review:** F6 (the D4 muting of superseded generic ids) and F10
remain as recorded there.

## §8 — Fact spot-check (report v1.1 and the commit claims, re-measured)

| # | claim | result |
|---|---|---|
| 1 | C2 mutation → 1/9 red, exactly the new test; restore 9/9 | ✓ reproduced |
| 2 | emit_gaps transition rows carry `asset_census.py …` regardless of carried owner | ✓ real CLOSED and RE-OPENED rows, owner `layer packet` |
| 3 | "No hand-authored detector begins with that prefix" | ✓ today (0 of 75), but ✗ as a guarantee: two plausible shapes collide (§2.3) |
| 4 | R218 FAIL cause: 5 capabilities, `editorial=true`, `no_contract` ×4 / `no_relation_in_range` ×1 | ✓ |
| 5 | ASSET_ELEVATION_TEMPLATE fingerprint new this wave (matched at `c8cdc0242`) | ✓ |
| 6 | CRITERION_REGISTRY: 21 auto-measured criteria | ✓ 21 + 5 NONE |
| 7 | R81 PARTIAL, 11 of 30 (10/8/6/4/2) | ✓ re-counted |
| 8 | `a72cdf460` rewrote `_schema` line 1 in place to add `kind` | ✗ append-only commit; the real precedent is `5973d0132` |
| 9 | The review sanctioned "leave the code as-is and just correct the report" | ✗ not in W3-1_REVIEW.md |
| 10 | L0 v3.0 no longer says "320 gates" anywhere | ✓ 0 matches |
| 11 | R218 still 17/24; P16 PASS, same SCU, 21/32; vitest 5/5 | ✓ |
| 12 | P16 now verbatim T1 | ✓ equals T1 :171 |
| 13 | Isolated census: exactly 15 changes (11 R60 + 4 R99) | ✓ ERRORED 0, exact list |
| 14 | emit dry run 0/184/26/0 then 0/183/0/0 | ~ first ✓; second reproduces as 0/184/0/0 |
| 15 | Suite 424 = 398 + 24 + 2 pre-existing | ✓ |
| 16 | Manifest MATCH; drift exit 2 from the 2 doc fingerprints only | ✓ (LOW set is environment-dependent) |
| 17 | The real ledger was never touched by any correction commit | ✓ `git diff --quiet`; md5 `f6b1d3c5…` |
| 18 | ga_prashna and mi_abhilekha still read the identical PARTIAL sentence | ✓ disclosed honestly as a known limit |
| 19 | The R99 finer distinction is "a named, carried finding … (§3)" | ✗ no R99 item in §3 |

Reviewer scratch (not committed): the scratchpad `rev-w3b/` directory holds `collide.py`,
`c2_repro.py`, `c2_ext.py`, `census_base.json`/`census_head.json` and their logs, `diff_census.py`,
`drift_{base,head}.json`, `r218.out`, and the `ctrl_*` scratch copies. The temporary worktrees
`wt-base` and `wt-head` were clean and have been removed.
