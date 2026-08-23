---
canonical_id: M0_CLOSE_READINESS
version: 1.1
status: LIVE-ASSESSMENT
task: M0-T46 (v1.0 authored by M0-T36; v1.1 applies D-38/D-39/D-40/D-41/D-42 and re-measures)
authored_by: KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36 for v1.0, M0-T46 for v1.1)
certified_by: null   # I16 / charter H7 — a KĀRAKA never certifies its own work
measured_at: 2026-08-23T08:00:51Z (contract guard --live) · 08:0xZ (direct read-only SQL) · 07:59Z (scorecard reading 4) — v1.0; v1.1 (M0-T46) re-reads the guard/DB figures unchanged from v1.0 (no writer, migration or guard code moved between the two) and re-runs `m0_exit_scorecard.py` fresh (reading 5, this task) and `m0_deferral_register.py` fresh (v1.2) for the classification changes
db_access: READ-ONLY throughout (SET default_transaction_read_only=on; SELECT only). Nothing written to asset_registry, asset_throughput or any guard.
applies: DECISIONS.jsonl D-30 (all five parts), D-29, D-31, D-38, D-39, D-40, D-41, D-42; VERDICTS.jsonl V-8, V-9, V-10, V-11
companion: 00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.md v1.2 (the per-entry classification this document totals); 00_ARCHITECTURE/control/M0_EXIT_SCORECARD_v1_0.md reading 5 (the live re-measurement this document reads from)
---

# NIRMĀṆA M0 — Close Readiness v1.1

**What this document is.** The ordered list of what must become true before the CI blocking
switch can flip, now that D-30 part 2(a) has untied criterion 10's circularity — and, separately,
an honest assessment of whether M0 can close on its own acceptance criteria.

**What this document is not.** It contains **no recommendation to close M0**. Readiness is
ADHIKĀRIN's to judge (charter G8/G9) and a freeze requires PARĪKṢAKA's independent evidence
(I16 / charter H7). Nothing here is certified. Nothing here was flipped, wired, or written to
production. `.github/` was not touched.

---

## 1 — The headline, stated plainly

**M0 cannot close on its own acceptance criteria, and the reason is structural rather than
unfinished work.**

M0's exit criteria (plan §14.1) require *"CI guards merged and **blocking**"*. **Merged** means
present on the default branch. Charter **H2** prohibits *"Force-push, history rewrite, or **any
write to main**"* — a §3 hard prohibition, which every agent *refuses* rather than parks, and
which is not appealable. ADHIKĀRIN ruled this at **D-30 part 2(b)**: the merged half is
**PARKED (PARK-6)**, and the ruling makes explicit that no reading of the charter's
"the plan wins" clause authorises the merge.

So M0's exit is satisfiable only by an act outside this campaign — a merge performed elsewhere,
or the native waiving the criterion. Neither has happened. **Re-verified by this task at
2026-08-23T08:0xZ:** `origin/main` @ `2670e61e2` does not contain
`.github/workflows/nirmana-m0-guards.yml`, `check_asset_catalogue_contract.py` or
`check_asset_source_parity.py`. All three exist only on `campaign/nirmana-autonomous`.

A clean statement that M0 cannot close yet is more useful than a checklist that implies it can.
Everything below is what remains *inside* that constraint.

**v1.1 (M0-T46) restates this from the current data, after six further ADHIKĀRIN rulings
(D-37–D-42).** The headline is unchanged — M0 still cannot close, still on the identical
criterion-10 / PARK-6 / H2 collision — but three of the "treated as finished but never ran"
items from v1.0's §4.2 have genuinely moved: Phase 0.8b now carries a real decision (REMAIN
DRAFT, D-38), Phase 0.8c's 23 packets are now adjudicated (D-38, 17 closed outright, 6 routed
to their owning rungs), and the X-03 / criterion-8 dead-flag question has its ownership and
column-authorisation settled (D-39) even though the column itself does not exist yet. See §2
and §4.2 below for the re-measured detail.

---

## 2 — Where the twelve criteria stand

v1.0's figures were measured live by M0-T36; v1.1 (M0-T46) re-ran `m0_exit_scorecard.py` fresh
(reading 5) and confirms none of the underlying counts moved — criterion 4 is still `3`,
criterion 9's packet count is still `23`. `bucket` is the deferral register **v1.2**'s
classification, after D-30 AND D-38/D-39/D-42 were applied (§12.1 of that document has the
full before/after tally).

| # | criterion | reads now | bucket | why / whose |
|---|---|---|---|---|
| 1 | three-way diff = 0 | scorecard `5` · shipped parity guard `0` | UNEXAMINED | two detectors, two meanings of zero, no ruling says which is the criterion |
| 2 | contract violations per kind = 0 | 16 rules fail · 4 not_checkable | UNEXAMINED | **ill-formed as worded** — C-25/26/27 have no detector and the contract forbids reporting them as passing, so it can never read zero |
| 3 | prefix mismatches = 0 | `1` (lel_events) | **DEFERRED** | ruling **D-23** → R5; C-01 exempts source rows, so the SOURCE reclassification *is* the repair |
| 4 | dangling / DRAFT-targeted edges = 0 | `3` | **DEFERRED** *(moved)* | **D-38**: Phase 0.8b's disposition is REMAIN DRAFT for all three dependencies (ga_vichara R1; ka_dasha_kala, ka_sangam R3) — none is named by a rung-specific promotion clause, so promotion in M0 is refused and the edges are deferred to R1/R3 |
| 5 | multi-producer partitions = 0 | C-25 `not_checkable` · X-01 `0` | **REPAIRABLE-IN-M0** *(moved)* | **D-39** confirms M0's ownership outright and settles the column is authorised under D-4, not reserved by P5 — a known repair (add column, backfill, verify) now exists; nobody has executed it |
| 6 | throughput rows on inactive assets = 0 | `1` asset / `3` rows | **RESERVED** | charter **P1** asset `ka_gochara_sweep`; deferred to R3 by **D-12 part 4** and plan §14.2 |
| 7 | retired without data_disposition = 0 | `1` | **DEFERRED** | plan §14.2 names this asset's disposition as R3 work; **D-12 part 4** quotes it |
| 8 | active without coverage or dead flag = 0 | scorecard `NOT-MEASURABLE` · guard `2` | **REPAIRABLE-IN-M0** *(moved)* | **D-39** confirms M0's ownership and the column is authorised, not reserved by P5 — no column exists yet; separately **D-42** ranks `build_run_assets` authoritative for this criterion's build-coverage half |
| 9 | unresolved zero-consumer findings = 0 | `23` packets, all adjudicated, `0` unresolved | **AT-ZERO-WITH-EXPOSURE** *(moved)* | **D-38** adjudicates all 23 by reading class (8 INPUT-ONLY + 2 BY-DESIGN closed, 7 METHOD-BLIND closed-as-unknown, 1 retirement candidate + 5 SHADOWED routed to owning rungs); adjudication IS resolution per the ruling, but 6 of 23 carry follow-on rung work |
| 10 | CI guards merged and blocking | merged `false` · blocking `false` · runs `0` | **EXCLUDED / PARKED** | **D-30 part 2(a)** excludes it from its own precondition; **part 2(b)** parks the merged half (PARK-6, H2) |
| 11 | every asset carrying `domain` and `rung` | `0` / `0` across 128 | **AT ZERO** (with exposure) | migration 590, certified **V-8**. Exposure: `domain` was derived from seed-owned `scope`, and one row (`mi_jivanaghatana`) disagrees with the seed |
| 12 | §11 CI domain-coherence assertion green | X-04 exists, returns `0`, **has never run** | REPAIRABLE-IN-M0 | **D-30 part 5**: the assertion *does* exist; criterion 12 reduces entirely to criterion 10 |

**Totals, re-measured (v1.1 / M0-T46).** At zero, in the scorecard's own PASS sense:
**two** (criterion 9 — adjudicated, exposure noted; criterion 11, with a named exposure).
Deferred with a reason and a ruling: **three** (3, 4, 7) plus one reserved (6). Excluded/parked:
**one** (10). Repairable but not done: **three** (5, 8, 12). **Still UNEXAMINED: two** — criteria
1 and 2. D-24 part 3, as amended by D-30/D-39/D-40, forbids flipping on either of those two.

**Read against the scorecard's own PASS/FAIL/NOT-MEASURABLE/BLOCKED enum instead of the
deferral register's five buckets**, reading 5 shows PASS=2 (criteria 9, 11), FAIL=6,
NOT-MEASURABLE=3 (criteria 2, 5, 8 — still not-measurable *as detectors*, even though 5 and 8
are now classified REPAIRABLE-IN-M0 in the deferral register: "repairable" is an
ownership/mechanism classification, "not-measurable" is a detector-existence fact, and the two
are not in tension — see the register's crit-8 entry), BLOCKED=1 (criterion 6). The two enums
answer different questions and neither supersedes the other; both are reported so a reader does
not mistake one for the other.

### 2.1 — The deferred rules and the rulings that grant them

After D-30 part 1 was applied, **15 of 20** classified contract/extension rules were
DEFERRED-WITH-REASON — up from 10. **v1.1 (M0-T46): 16 of 20**, after D-38 adds `C-11` (X-05
moves to AT-ZERO-WITH-EXPOSURE instead, having been resolved rather than deferred — see §2).
**14 of the 16 carry `BLOCKING` severity** in the guard's rule table (up from 8 in v1.0). Each
names its ruling; the full text is the register's §9/§12.

| rule | deferred to | reason cited |
|---|---|---|
| C-01 | R5 | D-23 |
| C-02 | R5 | D-28 part 1 (deliberate NULL) + D-23 |
| C-03 | R5 | D-28 part 1 + D-23 |
| C-04 | R0/R1/R2/R5 per row | **D-30 part 1** (+ D-23, D-28 part 4) |
| C-06 | R5 | **D-30 part 1** |
| C-07 | R3/R5 | **D-30 part 1** + D-19 part 1 + D-27 part 2a |
| C-08 | R3 | D-12 part 4 + plan §14.2 (charter P1 asset) |
| **C-11** | **R1 (ga_vichara) / R3 (ka_dasha_kala, ka_sangam)** | **D-38 (new in v1.1)** — Phase 0.8b's disposition is REMAIN DRAFT; none of the three is named by a rung-specific promotion clause |
| C-15 | R3/R5 | **D-30 part 1** + §8.4's R3 probe assignment |
| C-17 | R3 | D-13 part 2 **as corrected and extended by D-29** |
| C-20 | R0 | D-19 part 1 + D-27 part 2a |
| C-21 | owning rung | D-19 part 1 + charter G4 |
| C-22 | each rung | structural: vacuous — 0 rungs frozen; **0 of 128 assets carry an `integrity_check_sql`** |
| C-25 | M0 *(ownership settled by D-39, via criterion 5)* | contract mandate §4.9/§6/§10.3 — no column, never green; D-39 authorises a column under D-4, not P5 — but none has been created |
| C-26 | owning rung | contract mandate §4.11 — and no Phase-0 step names an authority pointer |
| C-27 | M2 | contract mandate + plan §4.8 — the p95 it compares against does not exist |

Plus **C-28's residual of 31 rows**, deferred by **D-30 part 3** under G7 and indexed as a G7 by
D-31 part 2 — *partial*, covering 31 of C-28's 105 rows and not the other 74. **D-42 (v1.1)
reframes the residual**: it is not "31 missing an estimate", it is "31 assets read `lit` with no
completed `build_run_assets` record behind them" — the deferral's destination and scope are
unchanged, only the honest description of what is being deferred.

**Moved out of this table in v1.1:** `X-03` and, via criterion 8 and criterion 5, the two
criteria that named it — all three CONFIRMED M0's and REPAIRABLE-IN-M0 by D-39, not deferred to
a rung (§2 above). `X-05` moved to AT-ZERO-WITH-EXPOSURE, resolved by adjudication (D-38), not
deferred.

---

## 3 — The ordered list to flip the blocking switch

**The condition, FINAL FORM (v1.1 / M0-T46).** D-24 part 3, amended by D-30 part 2(a)+4, then
by D-39 part 1 (its CI clause since **withdrawn**) and **D-40 part 1 (final)**: *the switch flips
when every criterion other than 10 is at zero or explicitly deferred with a recorded reason, AND
the disclosure mechanism is demonstrably in effect — proven by a two-direction fixture: a
disclosed rule's violation is still reported while no longer gating, and an undisclosed rule
still blocks — AND CI detects and refuses a stale baseline.* D-40 explicitly WITHDREW "CI must
gate against live state": M0-T40 root-caused that CI Actions carries no database credential, so
`--live` is a job that cannot run there at all. The stale-baseline requirement is a DB-free
substitute (age, and schema-behind: declared columns minus baseline columns), not a weaker
version of "gate live" — see step 10 below.

Steps 1–5 are rulings (**3 of 5 now resolved**, v1.1), 6–8 are execution, 9–10 are mechanism
(9 unchanged, 10 re-shaped by D-40), 11 is the flip itself.

### Rulings (ADHIKĀRIN)

1. **Rule what criterion 1 counts.** The scorecard's detector (every registry row needs a
   production `@register` → 5 violations) or the shipped parity guard's (services and source rows
   legitimately writerless → 0)? The guard is what a blocking flip gates on. Under its reading
   criterion 1 is already at zero; under the scorecard's it needs 4 exemptions and 1 G1
   disposition. *Unblocks criterion 1.* **STILL OPEN.**

2. **Rule criterion 2's wording.** As written it can never read zero. Re-word it to *"every
   checkable rule at zero, the un-checkable ones reported `not_checkable` with their reason"*, or
   make C-25/26/27 checkable. This is not a repair question. *Unblocks criterion 2.* **STILL
   OPEN.**

3. **Rule the partition-declaration mechanism (criterion 5).** ~~D-30's own rule now places the
   work in M0 … no prior ruling breaks the tie.~~ **RESOLVED by D-39 (2026-08-23T09:25:50Z):**
   confirmed M0's outright, and the column is authorised under D-4's reasoning, NOT reserved by
   P5. C-25 itself stays `not_checkable` regardless (no column exists yet — that is now the
   remaining work, not an open ruling). *Criterion 5 moved to REPAIRABLE-IN-M0.*

4. **Rule the dead-flag mechanism (criterion 8 / X-03).** ~~Same shape … define one (P5), rule
   the proxy sufficient, or defer.~~ **RESOLVED by D-39:** confirmed M0's, column authorised
   under D-4, not reserved by P5 — D-25's finding that `has_writer` is wrong on 2 rows still
   means that proxy is not itself the answer; a real column is. *Criterion 8 and X-03 moved to
   REPAIRABLE-IN-M0.*

5. **Reconcile G1's rung bound with Phase 0.8b and 0.8c.** ~~G1's charter bound reads "only
   assets in the current rung" and no rung is open, while 0.8b/0.8c assign work to M0.~~
   **RESOLVED by D-38 (2026-08-23T09:24:48Z):** 0.8b's disposition is REMAIN DRAFT — a G1
   decision, not a further deferral, and not a bulk promotion; 0.8c's 23 packets are adjudicated
   per reading class, not per individual G1 ruling. *Criteria 4 and C-11 moved to
   DEFERRED-WITH-REASON (R1/R3); criteria 9 and X-05 moved to AT-ZERO-WITH-EXPOSURE, unresolved
   = 0.*

### Execution (KĀRAKA)

6. **Criterion 4 / C-11 — 3 CURRENT→DRAFT edges.** `bo_laksana→ga_vichara`,
   `ka_kshetra→ka_dasha_kala`, `ka_taranga→ka_sangam`. **NO LONGER AN M0 EXECUTION STEP.** D-38
   rules REMAIN DRAFT for all three — there is nothing to promote in M0, and the edges are
   deferred to R1 and R3's own §8.6 stage-2 Conform. Removed from this list; carried in the
   register as a DEFERRED entry instead.

7. **Criterion 9 / X-05 — 23 zero-consumer dispositions.** **NO LONGER AN M0 EXECUTION STEP,
   AND MOSTLY DONE.** D-38 adjudicates all 23 by reading class: 17 close outright (8 INPUT-ONLY,
   2 BY-DESIGN, 7 METHOD-BLIND-as-unknown); 6 (1 retirement candidate, 5 SHADOWED) are routed to
   their owning rungs (3 to R0, 3 to R3) as recorded determinations, not open questions. The
   `zero_consumer_dispositions` block in the residuals JSON stays deliberately empty — D-38's
   adjudication is by class, not by a per-packet `decision_ref` — and that emptiness is now
   correct, not outstanding.

8. **C-28 — execute the authorised telemetry backfill (Phase 0.9, D-6 statement T-5).**
   **Nothing has executed; unchanged since v1.0.** M0-T3 produced the proposal with
   `writes_executed: NONE`. Of the 105 rows the guard reports, **74 are backfillable** from the
   median of their completed `build_run_assets` rows and **31 have none at all** — all 31 R0,
   deferred by D-30 part 3, **reframed by D-42 (v1.1)** as "31 assets read `lit` with no
   completed `build_run_assets` record", not "31 missing an estimate". Until T-5 runs, C-28 reads
   **105, not 31**. Snapshot → `verify` dry run → one partition → verified → widen (I2/I8). D-42
   additionally forbids, explicitly, re-pointing the detector at `build_run_assets` to make this
   read zero — that would be H3, not a repair.

### Mechanism — the two prerequisites, one amended

9. **Make a disclosure entry mean something (finding `F-T36-3`).** M0-T36 drafted sixteen
   deferred-rule disclosures (fifteen plus C-28's residual) into a new block
   `deferred_rule_disclosures` in
   `platform/scripts/governance/asset_catalogue_disclosed_residuals.json`. D-39's ruling (as of
   2026-08-23T09:25:50Z) still characterises this block as **inert** — read by no rule but
   `X-02`. **A tension this task found and does not resolve:** the register's own
   `_write_disclosure_block()` README (unchanged, present before this task) and this task's own
   read-only check of `check_asset_catalogue_contract.py` both show the guard NOW loads
   `deferred_rule_disclosures` **by rule id** and computes an `effective_severity` from it — work
   attributed there to "M0-T40". D-39 is timestamped after that work would have landed but cites
   pre-M0-T40 evidence. Whether `F-T36-3` is closed or still open is therefore genuinely unclear
   from the ledger as it stands, and it is not a KĀRAKA's call to settle (I13/I16) — flagged to
   ADHIKĀRIN, not resolved here. Separately and regardless: even if the reader now works,
   **nothing today carries `gating_effect: "non_gating"` plus an `authorised_by` decision id**,
   so no BLOCKING gate is demoted either way — the four safeguards D-39/the guard's own docstring
   describe (never green, itemised `covers`, G-power-gated demotion, disclosure ≠ gate-off) are
   unaffected by which reading of `F-T36-3` is correct.

10. **CI must detect and refuse a stale baseline — NOT "measure production" (D-40, replacing the
    withdrawn `F-T36-2` fix).** v1.0 filed this as "make the gate measure production" via
    `--live`; **D-40 part 1 withdrew that as impossible** — CI Actions has no database
    credential, so `--live` cannot run there regardless of how many `.github/` lines change.
    D-40's replacement, not yet built: two DB-free detectors — **AGE** ("an unmeasurable age is
    not a young age") and **SCHEMA-BEHIND** (declared `asset_registry` columns in the checkout
    minus the baseline snapshot's columns; today that difference is exactly migration 590's four
    columns). `.github/workflows/nirmana-m0-guards.yml` still invokes `--self-test` and
    `--baseline` against `asset_catalogue_baseline_20260823.json`, captured **05:09:17Z**, before
    migration 590 (05:36:13Z) and the Phase 0.5a repair (~06:51Z); run today it still exits 1
    with **17 BLOCKING failures** including three (`C-05`, `C-14`, `C-23`) that pass live. Neither
    AGE nor SCHEMA-BEHIND has been implemented by this task or, so far as this task's read-only
    check of the guard found, by any prior one. **No `.github/` file and no baseline snapshot was
    written by M0-T36 or M0-T46.**

### The flip

11. **Remove the two `continue-on-error: true` lines** — ADHIKĀRIN's own act, per the register's
    §6 step 1. **Not before steps 1–10.** V-11's `F-GUARD-NOT-ON-MAIN` adds the ordering
    constraint: *merge* and *flip* are two acts in that order, and a switch flipped before the
    merge is a green with no detector behind it on the branch that matters (H4). The merge itself
    is **PARK-6** and is not this campaign's to perform.

### What is left gating, in numbers (re-measured, v1.1)

The guard's own code, unchanged since v1.0, still returns **15 BLOCKING failures** on the same
15 rule ids: `C-01 C-02 C-03 C-04 C-06 C-07 C-08 C-11 C-15 C-17 C-20 C-21 C-28 X-03 X-05`. What
changed is the REGISTER's classification of what each one now needs:

- **12** are DEFERRED-WITH-REASON (`C-01 C-02 C-03 C-04 C-06 C-07 C-08 C-11 C-15 C-17 C-20 C-21`
  — `C-11` newly joined by D-38) — drafted disclosures exist for 11 of the 12 (not `C-11`, out of
  this task's scope — see the register §12.7), and all 12 gate anyway until step 9's mechanism
  question is settled either way;
- **1** is REPAIRABLE with a deferred residual (`C-28`: 74 repairable at step 8, 31 deferred and
  reframed by D-42);
- **1** is REPAIRABLE-IN-M0, ownership and column now confirmed, not yet executed (`X-03` —
  D-39; no execution step exists yet because the column does not);
- **1** is RESOLVED by adjudication, no longer gating-relevant in the register's own terms
  (`X-05` — D-38; the guard's raw exit code is unaffected because no guard code changed).

**So: with steps 1–10 all discharged, 0 blockers remain that a recognised disclosure or a
completed repair cannot clear — the same conclusion as v1.0, reached with three fewer open
rulings.** With 3 and 4 resolved (v1.1) but 1, 2, 9 and 10 still open, the guard still reds the
branch on 15 rules, all now correctly classified but none of them mechanically readable as
non-gating by the guard itself. That gap is the whole reason this section exists.

---

## 4 — Close readiness, honestly

### 4.1 — What is genuinely done

Stated first so the rest is fair, and every item names its independent verification:

- **Migrations 588 / 589 / 590 registered and applied** with the tracked runner — ledger moved
  447→450, **+1 per run**, sha256 MATCH ×3 (**V-8**). The P1 gochara corpus is **unmoved**:
  v1 = 38,287, gen-3.0 = 1,884, identical to D-5's pre-campaign measurement.
- **`domain` and `rung` present on 128/128 rows**, and the database now **reproduces the plan's own
  §8.4 census without being told it** — R0 40, R1 19, R2 22, R3 23, R4 9, R5 15; shared 44 /
  chart 84 (**V-8**). Criterion 11 is the one criterion at zero.
- **`has_substeps` repaired on 12 rows**, verified against an independent AST derivation with a
  negative control (**V-9**).
- **Layer position repaired on 39 cells**, codepoint-pinned against a lexicon typed from
  CLAUDE.md §N.1; `layer` cells changed = 0; `lel_events` correctly held NULL/NULL (**V-10**).
- **The §3 contract authored and shipped as an executable guard** — 33 contract + extension rules
  and 6 parity rules, every assertion with a proven failing fixture, `--self-test` exit 0 today.
- **Census, consumer map, DAG audit, zero-consumer evidence packets, seed-durability register,
  deferral register** (**V-11**), plan-figure reconciliation, gating-field sweep.

That is Phase 0 steps **0.1, 0.2, 0.3 (columns), 0.5a, 0.6a, 0.6b, 0.7** substantially complete.

### 4.2 — What is NOT done, including what has been treated as finished

- **Phase 0.9 — telemetry repair: NEVER EXECUTED.** Named in M0's own §14.1 content line. M0-T3
  produced an analysis; `writes_executed: NONE`. **9 of 128 assets carry an `estimated_seconds`.**
  This is the single largest unexecuted piece of authorised M0 work.
- **Phase 0.4 — declare co-writer partitions: NO WORK DONE AT ALL.** 16 co-writer rows across 5
  target tables, no declaration and no column to hold one. **v1.1: D-39 confirms M0's ownership
  and authorises the column under D-4 (not P5) — the ruling is no longer undecided, the column
  and backfill are simply unexecuted.**
- **Phase 0.8a — registered-but-dead flagged: NOT DONE, but no longer undecided.** **v1.1: D-39
  confirms this is M0's and the column is authorised, not reserved by P5** (§3 step 4). The flag
  itself does not exist; execution (add the column, backfill, verify) is the remaining work.
- **Phase 0.8b — DRAFT-but-served promotions: DECIDED, NOT PROMOTED.** **v1.1: D-38 rules the
  general disposition REMAIN DRAFT — a G1 decision, not a further deferral.** **47 of 128 rows
  are DRAFT and all 47 are `is_active`; zero were promoted.** Where a rung clause names an asset
  by name (R2's nine, R3's ka_graha_sancara/ka_muhurta_seva, R4's nine, R5's lel_events),
  promotion is that rung's to decide when it opens; the rest — including the three assets behind
  the `C-11` edges — stay DRAFT on the record, not silently unexamined. Read D-38 as closing the
  *decision*, not as promoting anything: "47 DRAFT, 0 promoted" remains the honest count.
- **Phase 0.8c — zero-consumer review: 23 packets adjudicated, D-38 (v1.1).** No longer "0
  dispositions recorded" — every packet now carries a determination by reading class: 8
  INPUT-ONLY + 2 BY-DESIGN + 7 METHOD-BLIND (17) close with no action; 1 NO-CONSUMER-FOUND + 5
  SHADOWED (6) are routed to their owning rung (3 to R0, 3 to R3) as retirement candidates /
  real defects, not resolved by mutation and not yet acted on by any rung.
- **Phase 0.10 — CI enforcement: guards exist, are non-blocking, are ABSENT from `origin/main`,
  and have RUN ZERO TIMES.** Per D-28 part 4, *a guard that has never had to choose is not yet a
  detector.* **v1.1: unchanged** — D-41 authorised a separate, unrelated deploy.yml edit
  (RES-1/SQ-08), not touched by this document.
- **Phase 0.11 — freeze the baseline: NOT DONE — and the artefact named "baseline" is
  pre-repair.** `asset_catalogue_baseline_20260823.json` was captured at 05:09:17Z, *before*
  migration 590 and *before* the layer repair. It is not the reconciled catalogue M0 is meant to
  freeze, and CI currently gates against it (§3 step 10). Anything reading the word "baseline" as
  "the frozen M0 catalogue" is reading it wrong.
- **`integrity_check_sql`: 0 of 128 assets carry one.** Correctly rung work (§8.6 stage 2), and
  C-22 correctly reads `not_checkable` rather than pass — but `not_checkable` on a vacuous rule
  should not be read as "fine".
- **Criterion 2 is ill-formed, not merely unmet — unchanged, still UNEXAMINED.** It cannot read
  zero as worded (C-25/26/27 have no detector); not a repair question, not yet ruled.
- **Criterion 8's measurability disagreement is UNCHANGED even though its ownership is now
  settled.** The scorecard still reads NOT-MEASURABLE (no dead-flag column exists) and the guard
  still returns `2` from the `has_writer` proxy — D-39 answered *whose* this is (M0's) and
  *whether a column is allowed* (yes, D-4, not P5), not *what the detector reads until the column
  exists*. Reading D-39 as having made criterion 8 measurable would be the mistake; it made it
  REPAIRABLE, which is a narrower claim.

### 4.3 — The structural stops, in order (re-measured, v1.1)

1. **Criterion 10's "merged" half — unsatisfiable by this campaign, absolutely. UNCHANGED.** §1
   above. PARK-6. Not a matter of effort or sequencing; H2 is a §3 prohibition and D-30 part 2(b)
   declines to bend it. None of D-38/D-39/D-40/D-41/D-42 touches this.
2. **The disclosure mechanism's status is now GENUINELY UNCLEAR, not simply "does not exist"**
   (`F-T36-3`). D-39 (2026-08-23T09:25:50Z) still characterises it as inert, using evidence
   timestamped before a later task ("M0-T40") that this register's own unedited text says closed
   `F-T36-3` by making the guard read disclosures by rule id. This task verified, read-only, that
   `check_asset_catalogue_contract.py` does contain that code path. Which is current is a question
   for ADHIKĀRIN (§3 step 9), not settled here. Either way, D-40's amended condition additionally
   requires a two-direction FIXTURE proving the mechanism works — and no such fixture exists yet,
   so the flip condition is not met under either reading of `F-T36-3`.
3. **The gate cannot measure production, and D-40 says it never will — replaced by a
   detect-and-refuse-stale-baseline requirement that also does not exist yet.** `F-T36-2`'s
   original fix ("make CI run `--live`") is WITHDRAWN as impossible (D-40 part 1: no DB credential
   in CI Actions). The replacement (AGE + SCHEMA-BEHIND detectors) is specified but unbuilt.
4. **Two criteria remain UNEXAMINED** (1, 2) — down from four in v1.0. D-39 resolved criteria 5
   and 8's ownership/mechanism question, moving them to REPAIRABLE-IN-M0; criteria 1 and 2 remain
   genuine definition questions, not repairs, and D-24 part 3 (as amended) forbids flipping on
   either.

### 4.4 — What this task did not do

**v1.0 (M0-T36):** No `asset_registry` row was written. No guard file was edited. No `.github/`
file was touched. The CI switch was not flipped and nothing was wired blocking. No severity was
changed. No rule was turned green. No `DECISIONS.jsonl` or `state/*.jsonl` line was edited.
`ka_gochara_sweep` (charter P1) was not touched, and `migrate.ts` / `asset_registry_seed.ts` were
not imported (D-13). No UNEXAMINED entry was resolved by that agent.

**v1.1 (M0-T46), additionally:** No `asset_registry` row was written (read-only throughout; the
live re-measurement ran entirely through `m0_exit_scorecard.py`, which also touches nothing but
the database in `SELECT`s). No guard file (`check_asset_catalogue_contract.py`,
`check_asset_source_parity.py`) was edited — `c28()` and every other detector are byte-for-byte
what M0-T36 left them; this task's own read of the guard for the `F-T36-3` tension (§4.3 item 2)
was read-only. No `.github/` file was touched. No entry was added to the register's
`DISCLOSURE_DRAFT`, and this task explicitly reverted
`platform/scripts/governance/asset_catalogue_disclosed_residuals.json` after each generator run
to keep its footprint inside `00_ARCHITECTURE/control/`, per its own scope instruction. No
`DECISIONS.jsonl` or `state/*.jsonl` line was edited — D-38 through D-42 were read, not written,
by this task. `ka_gochara_sweep` (charter P1) was not touched. No criterion this task did not
name (1, 2, 10) had its bucket changed. Nothing here is certified — that remains PARĪKṢAKA's
(I16 / H7), and a KĀRAKA reports observations, not verdicts.

---

## 5 — Open questions this document raises and does not answer

| # | question | status (v1.1) | whose |
|---|---|---|---|
| Q1 | Does §8.6 stage 2 override Phase 0.4 and 0.7, as it would override 0.6a if read as specific? The `has_substeps` case is forced by D-30's own verification property; partitions and the consumer map are not. | **PARTIALLY MOOT** — D-39 confirms criterion 5 (partitions) M0's outright regardless of how the §8.6-vs-0.4 tiebreak would otherwise resolve. The consumer map (0.7) question is untouched and still open. | ADHIKĀRIN (G9) |
| Q2 | Should the two C-28 detectors be reconciled? The guard filters to `asset_kind IN (data, artifact)`; the scorecard does not. The 7 rows in the gap are all services. The residual D-30 part 3 deferred (31) was measured under the guard's definition. | **STILL OPEN** — D-42 reframes what the 31-row residual means but does not reconcile the 105-vs-112 count disagreement, and explicitly forbids using its own ranking to make the two detectors agree by re-pointing either one. | ADHIKĀRIN (G9) |
| Q3 | Is a per-rule disclosure reader plus a disclosure-conditioned severity a legitimate mechanism, or is it H3 by another name? | **STILL OPEN, AND SHARPER** — this task found the reader may already exist (§4.3 item 2), which does not answer whether it is H3-legitimate, only that the question is no longer hypothetical. | ADHIKĀRIN (G9 / H3) |
| Q4 | Should the CI baseline snapshot be refreshed, or should the workflow invoke `--live`? | **ANSWERED — NEITHER, by D-40.** `--live` is impossible in CI (no credential). A refreshed snapshot alone is a tautology (D-39 part 3: "everything matches, both guards go green, and the green is a tautology rather than a measurement"). D-40's answer is a third option: DB-free staleness detectors (AGE, SCHEMA-BEHIND), unbuilt. | closed by D-40; building the detectors is open |
| Q5 | With criterion 10's merged half parked, what does M0 "closing" mean — closed-with-a-parked-criterion, or held open? | **STILL OPEN.** Untouched by any of D-37–D-42. | ADHIKĀRIN, and possibly the native |

---

*v1.0 authored by KĀRAKA M0-T36; v1.1 by KĀRAKA M0-T46, on `campaign/nirmana-autonomous`.
Certified by nobody: a KĀRAKA reports observations, not verdicts (I16 / charter H7).*
