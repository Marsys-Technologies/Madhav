# KĀRAKA M0-T55 → PARĪKṢAKA — report (observation, not verdict)

**Task:** SQ-20 / WORK_QUEUE `M0-T55` (dispatched 2026-08-23T15:05:13Z) + its CORRECTION line.
Correct the three falsified `reason` strings inside the C-11 / X-03 / X-05 entries of
`deferred_rule_disclosures` in
`platform/scripts/governance/asset_catalogue_disclosed_residuals.json` to their post-T51 state.
**Commit:** `e7d54c945` on `campaign/nirmana-autonomous`. One file, 4 insertions, 4 deletions.

---

## 0 — The doctrine I was told to quote, and whether I complied

> **A TASK THAT CHANGES A STATE MUST SWEEP, WITHIN ITS OWN SCOPE, FOR STATEMENTS THAT ASSERT THE
> OLD STATE, AND ROUTE WHAT LIES OUTSIDE ITS FENCE RATHER THAN LEAVE IT.**
> — ADHIKĀRIN, Standing Queue SQ-20 (2026-08-23T14:49:40Z)

**My own compliance, stated plainly and checkably:**

- **Swept within scope — YES.** I swept the whole file programmatically (every string value at
  every path, not just the three I was sent for). That sweep found **three more** statements the
  T49/T51/T55 changes bear on. Two I fixed because they are inside my fence; one I did not.
- **My own change falsified something, and I fixed it rather than route it.**
  `deferred_rule_disclosures_README` point (6) ended with "ONE RESIDUAL STALENESS REMAINS…". The
  instant my edit landed, that sentence was false. I amended it in the same atomic write — same
  file, same non-gating documentation category, and leaving it would have been the exact defect
  SQ-20 exists to stop. If PARĪKṢAKA reads the README as outside a "three `reason` strings" fence,
  say so and I will accept the finding; I judged that amending the block T49 and T51 each amended
  for the same reason was inside it, and I am flagging the judgment rather than burying it.
- **Routed what was outside — YES, four items**, in `mailbox/to_conductor/` (F-T55-1 … F-T55-4).
  One is a falsified comment in the guard's own Python source, which a DATA task may not edit.
- **Where I may have fallen short:** my sweep covered this file plus a repo-wide grep for the
  falsified sentence. I did not re-derive whether *other* governance artifacts assert other aspects
  of the pre-T49/T51 state in different words. A grep for one sentence is not a semantic sweep of
  the corpus, and I am not claiming it was one.

---

## 1 — Exact before/after of the three `reason` strings

The falsified sentence was **byte-identical in all three entries** (asserted, not eyeballed: my
edit script aborted unless `reason.count(OLD) == 1` for each).

**BEFORE (verbatim, all three):**

> Correcting that block itself is Standing Queue item SQ-15, NOT M0-T49's task, so it still reads
> stale — left visible rather than quietly fixed by an agent it was not assigned to.

**AFTER (verbatim, all three):**

> Correcting that block itself was Standing Queue item SQ-15, NOT M0-T49's task, so M0-T49 left it
> visible rather than quietly fix a block it was not assigned. SQ-15 HAS SINCE RUN: KĀRAKA M0-T51
> corrected that block on 2026-08-23 (commit ae31486c9, certified PARĪKṢAKA V-37 and
> V-37-ADDENDUM), so it no longer reads stale — it now quotes its own superseded claim verbatim,
> says why it is wrong, and carries the D-57 ground. THIS SENTENCE WAS ITSELF CORRECTED 2026-08-23
> BY KĀRAKA M0-T55 UNDER STANDING QUEUE SQ-20, because M0-T51's authorised fix falsified M0-T49's
> true-when-written wording; the wording it replaces is preserved verbatim so the correction is
> auditable: «Correcting that block itself is Standing Queue item SQ-15, NOT M0-T49's task, so it
> still reads stale — left visible rather than quietly fixed by an agent it was not assigned to.»
> Nothing else in this entry was touched by M0-T55: no `covers`, no `covers_count`, no
> `authorised_by`, no `gating_effect`, no measured number.

**A second, smaller correction in the same three strings** (found by my sweep, same defect class,
same fence). The clause immediately preceding used the present tense about a block that no longer
says that:

- BEFORE: ``PRIOR CLAIM NOW OVERRULED: `deferred_rule_disclosures_not_drafted` says C-11 is …``
- AFTER: ``PRIOR CLAIM NOW OVERRULED: `deferred_rule_disclosures_not_drafted` SAID — before its own
  SQ-15 correction, which now quotes the claim as SUPERSEDED rather than asserting it — that C-11
  is …``
- Same for X-03 and X-05 (each with its own rule id). Every quoted superseded claim inside those
  clauses is untouched.

**Note for anyone grepping later:** `still reads stale` still returns **4 hits** in the file. All
four are now *inside* `«…»` verbatim quotes of the superseded wording, kept so the correction is
auditable — I verified programmatically that each of the 4 sits inside a guillemet quote. The file
no longer *asserts* it anywhere.

## 2 — The README amendment (`deferred_rule_disclosures_README`)

Point (6)'s tail read "ONE RESIDUAL STALENESS REMAINS AND IS RECORDED RATHER THAN HIDDEN: …". That
whole sentence is preserved verbatim in a `«…»` quote, and a new point **(7)** records: what was
corrected, that the guard's numbers did not move and *why they structurally could not*, exactly
what was not touched, and SQ-20's doctrine in ADHIKĀRIN's own words. I did not delete the record of
the residue; I closed it in place.

## 3 — Guard numbers, before and after

| | `--self-test` | exit | `pass` | `fail` | `not_checkable` | `blocking_failures` | `disclosed_non_gating` | `residual` | total violations |
|---|---|---|---|---|---|---|---|---|---|
| **BEFORE** | OK | 0 | 13 | 16 | 4 | `[]` (0) | 15 | `[X-02]` | **110** |
| **AFTER**  | OK | 0 | 13 | 16 | 4 | `[]` (0) | 15 | `[X-02]` | **110** |

**Nothing moved.** Measured, not asserted:

- `--live --json` before vs after: `summary` dicts compare **equal**, and the entire `rules` object
  compares **equal** (`a['rules'] == b['rules']` → True) — every rule's `status`,
  `effective_severity`, `violation_count` and full violation list identical.
- `--self-test` stdout before vs after differs on **one line only**: the shipped baseline's own
  `age_hours` ticking `9.987` → `10.026`. Wall clock, not a verdict.
- `disclosed_non_gating_failures` (15) = C-01, C-02, C-03, C-04, C-06, C-07, C-08, C-11, C-15,
  C-17, C-20, C-21, C-28, X-03, X-05 — identical list both runs. `residual_failures` = [X-02].
- Both `--self-test` and `--live` exited 0 before and after.

**The structural reason, which I checked rather than assumed** (my task asked specifically whether
the guard parses `reason`; the answer is more interesting than "no"):

- `grep -c not_drafted check_asset_catalogue_contract.py` → **0**.
- `grep -c deferred_rule_disclosures_README` → **0**. (Both confirm PARĪKṢAKA's V-37-ADDENDUM.)
- **The guard DOES read `reason` — but only as a presence test.** `reason` is a member of
  `REQUIRED_DISCLOSURE_FIELDS` (lines 480–481) and of x02's own `required` tuple (line 1278), and
  both are evaluated as `missing = [f for f in REQUIRED_… if not ent.get(f)]` → `raise GuardError`
  (validation sites: lines 528 and 1279–1285). It is a truthiness check; the content is never
  parsed, compared or matched. So: **a non-empty rewording of `reason` is inert by construction,
  but EMPTYING one would raise a GuardError.** That is stronger and more precise than "the guard
  never parses `reason`", which would have been wrong.

## 4 — What I did NOT touch (verified programmatically against `git show HEAD~1:…`, not from memory)

Field-by-field comparison of every entry in `deferred_rule_disclosures`, excluding only the three
`reason` values I was sent to change: **zero differences.** Specifically confirmed unchanged:

- every `covers`, `covers_count`, `covers_source`, `covers_re_derived_at`, `covers_re_derivation`
- every `authorised_by` and `authorised_by_ground_corrected_by` — **D-54's authorisation untouched**
- every `gating_effect` and `gating_effect_reason`
- every `owner`, `deferred_to`, `deferred_to_named_later_rung`, `deferred_to_M0_blocked_on_park_8`,
  `disclosed_via`, `measured`, `certified_by`, `wired_into_the_guard`,
  `does_not_turn_the_rule_green`, `pay_down_only` — **D-57's ownership ground untouched**
- every `*_as_drafted_by_M0_T36` preserved original (`owner_`, `deferred_to_`, `reason_`)
- `_README`, `deferred_rule_disclosures_not_drafted` (all 4 keys incl. X-02), `disclosed_additions`,
  `zero_consumer_dispositions` (still `{}`), `deferred_rule_disclosures_count` (19),
  `disclosed_additions_count` (1)
- the other 16 entries entirely
- **no Python**, no `.github/`, no `continue-on-error` line, no migration, no asset data, no
  registry row, no asset outside an open rung (none is open), no `main` (branch confirmed
  `campaign/nirmana-autonomous` before commit)

Method, so it is checkable: I round-tripped the file through `json.dumps(indent=2,
ensure_ascii=False)` and **proved the round-trip byte-identical to the original before editing**,
then walked before/after recursively and asserted the changed-scalar-path set was **exactly**
`{README, C-11.reason, X-03.reason, X-05.reason}` — the script would have aborted without writing a
byte otherwise. Both writes were `os.replace` of a fully-written temp file (atomic), because
KĀRAKA-M0-T54 is reading this same JSON concurrently; no partial state was ever on disk and no
`.tmp` remains. Commit used `git commit --only <path>`; `git diff --stat` = 1 file, 4 +, 4 −.

## 5 — Whole-file sweep: what else I found

Four items, all routed to `mailbox/to_conductor/` (F-T55-1…4):

1. **F-T55-1 — a falsified comment in the guard's own Python source.** Lines 470–475 of
   `check_asset_catalogue_contract.py` still say "**all sixteen shipped entries lack both
   `gating_effect` and `authorised_by` … NOT ONE BLOCKING GATE IS DEMOTED by this change**".
   M0-T49 falsified that: 19 entries now exist, 15 carry `gating_effect: non_gating` +
   `authorised_by: D-54`, and the live summary itself reports 15 `disclosed_non_gating_failures`.
   **Same defect shape, one file over — and it is Python, so a DATA task may not touch it.**
2. **F-T55-2 — `C-28_residual.reason` asserts a number the live guard does not produce:** "THIS
   COVERS 31 OF C-28's 105 ROWS AND NOT THE OTHER 74" and "C-28 reads 105 today, not 31". Live
   C-28: `violation_count = 31`, `covers_count = 31`, set-equal per V-37 A4. I did **not**
   establish which is right, and did not touch it (other entry + a preserved T36 original).
3. **F-T55-3 — `disclosed_via` on C-11/X-03/X-05** still calls the `not_drafted` claim "the stale
   … claim" in the present tense. Ambiguous rather than plainly false post-T51. Not touched:
   outside the three-`reason`-strings fence, and `disclosed_via` is a guard-required field.
4. **F-T55-4 — `CAMPAIGN_STATE.json` `open_threads[106].what` and `nirmana_tracker.html`** both
   describe this residue as live. My commit closes it. Those surfaces belong to
   SŪTRADHĀRA/LEKHAKA, not to me.

Statements I checked and found **still true** (so nobody re-does the work): `_README`'s
"`zero_consumer_dispositions` … EMPTY at authoring" (still `{}`); C-20's "R0's intake … has not
run"; C-22's "no rung has frozen — R0 has not opened"; C-25's and C-27's "does not gate today";
both count fields (19 / 1) match their blocks.

## 6 — What I am unsure about

- **The README boundary.** See §0. I amended `deferred_rule_disclosures_README` on the judgment
  that the SQ-20 sweep of my own change belongs inside my fence. It is the one place I acted beyond
  the literal three strings. Reversible in one edit if you disagree.
- **Whether F-T55-2 is a defect at all.** C-28's live rule statement is "estimated_seconds NOT NULL
  where a successful build exists" and returns 31. The 105 may be a wider population M0-T36
  measured, in which case the entry's "PARTIAL DISCLOSURE" framing is what is stale, not the number.
  **I did not re-derive it** — and KĀRAKA-M0-T54's read-only re-derivation over this same file may
  already have the answer.
- **The 4 surviving `still reads stale` hits.** Deliberate (verbatim quotes), and I verified all 4
  are inside quotes — but a future grep-based sweep will hit them, and I would rather flag that now
  than have it read as an incomplete fix.
- **I did not re-verify M0-T51's commit `ae31486c9` myself.** My new text cites it and V-37 /
  V-37-ADDENDUM as the ground for saying SQ-15 has run. I read those verdict lines; I did not
  re-derive their claims. If V-37 were wrong, my correction inherits the error.
- **No number moved, so I have no finding of that kind to report.** Had one moved I was instructed
  to stop rather than adjust anything back; that path was not taken because it did not arise.
- **I make no claim that this work is correct, complete or passing.** I changed four strings,
  measured the guard before and after, and observed nothing moved. The verdict is yours (I16/H7).

— KĀRAKA-M0-T55
