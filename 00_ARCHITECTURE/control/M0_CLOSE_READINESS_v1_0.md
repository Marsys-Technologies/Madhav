---
canonical_id: M0_CLOSE_READINESS
version: 1.0
status: LIVE-ASSESSMENT
task: M0-T36
authored_by: KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)
certified_by: null   # I16 / charter H7 — a KĀRAKA never certifies its own work
measured_at: 2026-08-23T08:00:51Z (contract guard --live) · 08:0xZ (direct read-only SQL) · 07:59Z (scorecard reading 4)
db_access: READ-ONLY throughout (SET default_transaction_read_only=on; SELECT only). Nothing written to asset_registry, asset_throughput or any guard.
applies: DECISIONS.jsonl D-30 (all five parts), D-29, D-31; VERDICTS.jsonl V-8, V-9, V-10, V-11
companion: 00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.md v1.1 (the per-entry classification this document totals)
---

# NIRMĀṆA M0 — Close Readiness v1.0

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

---

## 2 — Where the twelve criteria stand

Measured live, this task, READ-ONLY. `bucket` is the deferral register v1.1's classification
after D-30 was applied.

| # | criterion | reads now | bucket | why / whose |
|---|---|---|---|---|
| 1 | three-way diff = 0 | scorecard `5` · shipped parity guard `0` | UNEXAMINED | two detectors, two meanings of zero, no ruling says which is the criterion |
| 2 | contract violations per kind = 0 | 16 rules fail · 4 not_checkable | UNEXAMINED | **ill-formed as worded** — C-25/26/27 have no detector and the contract forbids reporting them as passing, so it can never read zero |
| 3 | prefix mismatches = 0 | `1` (lel_events) | **DEFERRED** | ruling **D-23** → R5; C-01 exempts source rows, so the SOURCE reclassification *is* the repair |
| 4 | dangling / DRAFT-targeted edges = 0 | `3` | REPAIRABLE-IN-M0 | needs the G1 rung-bound reconciliation (step 5 below), then 3 dispositions |
| 5 | multi-producer partitions = 0 | C-25 `not_checkable` · X-01 `0` | UNEXAMINED *(narrowed)* | D-30's own rule now says the work is **M0's** (Phase 0.4 names it) — but no column exists and creating one is P5 |
| 6 | throughput rows on inactive assets = 0 | `1` asset / `3` rows | **RESERVED** | charter **P1** asset `ka_gochara_sweep`; deferred to R3 by **D-12 part 4** and plan §14.2 |
| 7 | retired without data_disposition = 0 | `1` | **DEFERRED** | plan §14.2 names this asset's disposition as R3 work; **D-12 part 4** quotes it |
| 8 | active without coverage or dead flag = 0 | scorecard `NOT-MEASURABLE` · guard `2` | UNEXAMINED *(narrowed)* | D-30's rule now says the dead flag is **M0's** (Phase 0.8a names the work *and* the asset) — but there is no column and no ruling on the `has_writer` proxy |
| 9 | unresolved zero-consumer findings = 0 | `23` packets, `0` dispositions | REPAIRABLE-IN-M0 | 23 charter-G1 rulings; a KĀRAKA may not resolve a packet |
| 10 | CI guards merged and blocking | merged `false` · blocking `false` · runs `0` | **EXCLUDED / PARKED** | **D-30 part 2(a)** excludes it from its own precondition; **part 2(b)** parks the merged half (PARK-6, H2) |
| 11 | every asset carrying `domain` and `rung` | `0` / `0` across 128 | **AT ZERO** (with exposure) | migration 590, certified **V-8**. Exposure: `domain` was derived from seed-owned `scope`, and one row (`mi_jivanaghatana`) disagrees with the seed |
| 12 | §11 CI domain-coherence assertion green | X-04 exists, returns `0`, **has never run** | REPAIRABLE-IN-M0 | **D-30 part 5**: the assertion *does* exist; criterion 12 reduces entirely to criterion 10 |

**Totals.** At zero: **one** (criterion 11, with a named exposure). Deferred with a reason and a
ruling: **two** (3, 7) plus one reserved (6). Excluded/parked: **one** (10). Repairable but not
done: **three** (4, 9, 12). **Still UNEXAMINED: four** — criteria 1, 2, 5, 8. D-24 part 3, as
amended, forbids flipping on any of those four.

### 2.1 — The deferred rules and the rulings that grant them

After D-30 part 1 was applied, **15 of 20** classified contract/extension rules are
DEFERRED-WITH-REASON — up from 10. **13 of the 15 carry `BLOCKING` severity** in the guard's rule
table (up from 8). Each names its ruling; the full text is the register's §10.

| rule | deferred to | reason cited |
|---|---|---|
| C-01 | R5 | D-23 |
| C-02 | R5 | D-28 part 1 (deliberate NULL) + D-23 |
| C-03 | R5 | D-28 part 1 + D-23 |
| C-04 | R0/R1/R2/R5 per row | **D-30 part 1** (+ D-23, D-28 part 4) |
| C-06 | R5 | **D-30 part 1** |
| C-07 | R3/R5 | **D-30 part 1** + D-19 part 1 + D-27 part 2a |
| C-08 | R3 | D-12 part 4 + plan §14.2 (charter P1 asset) |
| C-15 | R3/R5 | **D-30 part 1** + §8.4's R3 probe assignment |
| C-17 | R3 | D-13 part 2 **as corrected and extended by D-29** |
| C-20 | R0 | D-19 part 1 + D-27 part 2a |
| C-21 | owning rung | D-19 part 1 + charter G4 |
| C-22 | each rung | structural: vacuous — 0 rungs frozen; **0 of 128 assets carry an `integrity_check_sql`** |
| C-25 | undecided (see criterion 5) | contract mandate §4.9/§6/§10.3 — no column, never green |
| C-26 | owning rung | contract mandate §4.11 — and no Phase-0 step names an authority pointer |
| C-27 | M2 | contract mandate + plan §4.8 — the p95 it compares against does not exist |

Plus **C-28's residual of 31 rows**, deferred by **D-30 part 3** under G7 and indexed as a G7 by
D-31 part 2 — *partial*, covering 31 of C-28's 105 rows and not the other 74.

---

## 3 — The ordered list to flip the blocking switch

**The condition, as amended.** D-24 part 3, amended twice by D-30: *the switch flips when every
criterion **other than 10** is at zero or explicitly deferred with a recorded reason, **and every
deferred rule carries its disclosure entry**, itemised and dated.*

Steps 1–5 are rulings, 6–8 are execution, 9–10 are mechanism, 11 is the flip itself. **9 and 10
were not on any prior list, and without them the flip does not do what it says.**

### Rulings (ADHIKĀRIN)

1. **Rule what criterion 1 counts.** The scorecard's detector (every registry row needs a
   production `@register` → 5 violations) or the shipped parity guard's (services and source rows
   legitimately writerless → 0)? The guard is what a blocking flip gates on. Under its reading
   criterion 1 is already at zero; under the scorecard's it needs 4 exemptions and 1 G1
   disposition. *Unblocks criterion 1.*

2. **Rule criterion 2's wording.** As written it can never read zero. Re-word it to *"every
   checkable rule at zero, the un-checkable ones reported `not_checkable` with their reason"*, or
   make C-25/26/27 checkable. This is not a repair question. *Unblocks criterion 2.*

3. **Rule the partition-declaration mechanism (criterion 5).** D-30's own rule now places the
   *work* in M0 (Phase 0.4 names it; §14.1's M0 content line names it again), but §8.6 stage 2
   also lists "partitions declared" as every rung's Conform work, and no prior ruling breaks the
   tie. Then: authorise a column under D-4's reasoning, or reserve it under P5, or defer the work
   to the rungs. C-25 stays `not_checkable` either way. *Unblocks criterion 5, C-25's ownership.*

4. **Rule the dead-flag mechanism (criterion 8 / X-03).** Same shape: D-30's rule places it in M0
   unambiguously (Phase 0.8a names the work *and* the asset), but there is no column. Define one
   (P5), rule the guard's self-designated `has_writer` proxy sufficient — noting D-25 found that
   column wrong on 2 rows — or defer the criterion. *Unblocks criterion 8, X-03.*

5. **Reconcile G1's rung bound with Phase 0.8b and 0.8c.** G1's charter bound reads *"only assets
   in the current rung"* and **no rung is open**, while Phase 0.8b assigns DRAFT-but-served
   promotions and 0.8c assigns zero-consumer dispositions to M0. Until this is settled, the two
   largest repairable items cannot be executed by anyone. *Unblocks criteria 4 and 9, C-11, X-05.*

### Execution (KĀRAKA, after the rulings above)

6. **Criterion 4 / C-11 — 3 CURRENT→DRAFT edges.** `bo_laksana→ga_vichara`,
   `ka_kshetra→ka_dasha_kala`, `ka_taranga→ka_sangam`. Needs step 5 first.

7. **Criterion 9 / X-05 — 23 zero-consumer dispositions.** The mechanism already exists and is
   correct: `zero_consumer_dispositions` in the residuals JSON, deliberately empty, where a packet
   resolves **only** by an entry carrying a `decision_ref` into `DECISIONS.jsonl`. Needs 23 G1
   rulings; no KĀRAKA may resolve a packet by writing a justification into that block.

8. **C-28 — execute the authorised telemetry backfill (Phase 0.9, D-6 statement T-5).**
   **Nothing has executed.** M0-T3 produced the proposal with `writes_executed: NONE`. Measured by
   this task read-only: of the 105 rows the guard reports, **74 are backfillable** from the median
   of their completed `build_run_assets` rows and **31 have none at all** — all 31 R0, deferred by
   D-30 part 3. Until T-5 runs, C-28 reads **105, not 31**, and calling C-28 "deferred" is
   premature by 74 rows. Snapshot → `verify` dry run → one partition → verified → widen (I2/I8).

### Mechanism — the two prerequisites nobody had recorded

9. **Make a disclosure entry mean something (finding `F-T36-3`).** M0-T36 has drafted all fifteen
   deferred-rule disclosures plus C-28's residual, into a new inert block
   `deferred_rule_disclosures` in
   `platform/scripts/governance/asset_catalogue_disclosed_residuals.json`. **They are inert, and
   that must be said before flip time rather than discovered at it.** Two mechanical facts:
   (i) `disclosed_additions` is keyed by **asset_id** and is read in exactly one function,
   `x02()`; no other rule reads a disclosure at all. (ii) Severity is a **hardcoded constant** in
   the guard's `RULES` table — `Rule("X-02", RESIDUAL, …)`. X-02 is non-gating because someone
   typed `RESIDUAL`, not because it carries a disclosure; its own docstring says a disclosure does
   **not** turn a rule green. So writing the entries satisfies D-30 part 4's letter and changes
   nothing the guard does. Making them honourable needs a guard code change — a per-rule
   disclosure reader and a disclosure-conditioned severity — which is **a demotion of thirteen
   BLOCKING gates** and therefore exactly the shape charter **H3** exists to scrutinise. It is
   **not a KĀRAKA's change and M0-T36 did not make it.**

10. **Make the gate measure production (finding `F-T36-2`).** Every number in this document, in
    the register, in the scorecard, in V-11 and in D-30 comes from `--live`. **The workflow does
    not run `--live`.** `.github/workflows/nirmana-m0-guards.yml` invokes `--self-test` and
    `--baseline`, and `--baseline` is shorthand for `--snapshot
    asset_catalogue_baseline_20260823.json` — a file captured at **05:09:17Z**, before migration
    590 applied (05:36:13Z) and before the Phase 0.5a layer repair (~06:51Z). Run today it exits 1
    with **17 BLOCKING failures**, not 15: it still fails **C-05, C-14 and C-23**, all three of
    which pass in production, and reports C-08/C-09/C-10/C-18/C-19 as `not_checkable` because 590's
    columns do not exist in the snapshot. Flipping today would gate the branch on a three-hour-old
    file — a signal that does not measure the claim it makes (CLAUDE.md §N.8) — and would red the
    branch on three rules PARĪKṢAKA has already certified as repaired. Refresh the snapshot, or
    change what CI invokes. **No `.github/` file and no baseline snapshot was written by M0-T36.**

### The flip

11. **Remove the two `continue-on-error: true` lines** — ADHIKĀRIN's own act, per the register's
    §6 step 1. **Not before steps 1–10.** V-11's `F-GUARD-NOT-ON-MAIN` adds the ordering
    constraint: *merge* and *flip* are two acts in that order, and a switch flipped before the
    merge is a green with no detector behind it on the branch that matters (H4). The merge itself
    is **PARK-6** and is not this campaign's to perform.

### What is left gating, in numbers

The guard returns **15 BLOCKING failures** live at 08:00:51Z: `C-01 C-02 C-03 C-04 C-06 C-07
C-08 C-11 C-15 C-17 C-20 C-21 C-28 X-03 X-05`. Of those:

- **11** are now DEFERRED-WITH-REASON (`C-01 C-02 C-03 C-04 C-06 C-07 C-08 C-15 C-17 C-20 C-21`)
  — drafted disclosures exist, and they gate anyway until step 9;
- **1** is REPAIRABLE with a deferred residual (`C-28`: 74 repairable at step 8, 31 deferred);
- **2** are REPAIRABLE and need real work (`C-11` 3 rows, `X-05` 23 packets) — steps 6 and 7;
- **1** is still UNEXAMINED (`X-03`) — step 4.

**So: with steps 1–10 all discharged, 0 blockers remain that a disclosure or a repair cannot
clear. With steps 1–8 discharged but 9 and 10 not, 11 rules still red the branch on deferrals
that are correctly recorded and mechanically unreadable.** That gap is the whole reason this
section exists.

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
  target tables, no declaration and no column to hold one. Named as M0 content; now known by
  D-30's own rule to be arguably M0's; still undecided.
- **Phase 0.8a — registered-but-dead flagged: NOT DONE.** And it is now known to be M0's, not a
  rung's (§3 step 4).
- **Phase 0.8b — DRAFT-but-served promotions: NOT DONE.** **47 of 128 rows are DRAFT and all 47
  are `is_active`.** Zero promotions or written justifications recorded. Only the 3 `C-11`
  CURRENT→DRAFT edges have been *counted*; the promotion sweep itself has not started.
- **Phase 0.8c — zero-consumer review: 23 packets built, 0 dispositions recorded.**
- **Phase 0.10 — CI enforcement: guards exist, are non-blocking, are ABSENT from `origin/main`,
  and have RUN ZERO TIMES.** Per D-28 part 4, *a guard that has never had to choose is not yet a
  detector.*
- **Phase 0.11 — freeze the baseline: NOT DONE — and the artefact named "baseline" is
  pre-repair.** `asset_catalogue_baseline_20260823.json` was captured at 05:09:17Z, *before*
  migration 590 and *before* the layer repair. It is not the reconciled catalogue M0 is meant to
  freeze, and CI currently gates against it (§3 step 10). Anything reading the word "baseline" as
  "the frozen M0 catalogue" is reading it wrong.
- **`integrity_check_sql`: 0 of 128 assets carry one.** Correctly rung work (§8.6 stage 2), and
  C-22 correctly reads `not_checkable` rather than pass — but `not_checkable` on a vacuous rule
  should not be read as "fine".
- **Criteria 2 and 8 are ill-formed, not merely unmet.** Criterion 2 cannot read zero as worded;
  criterion 8's two instruments disagree about whether it is measurable at all. Neither is a
  repair question and neither has been ruled.

### 4.3 — The structural stops, in order

1. **Criterion 10's "merged" half — unsatisfiable by this campaign, absolutely.** §1 above.
   PARK-6. Not a matter of effort or sequencing; H2 is a §3 prohibition and D-30 part 2(b)
   declines to bend it.
2. **The disclosure mechanism does not exist** (`F-T36-3`). D-30 part 4's amended condition can be
   satisfied on paper today and cannot be satisfied in effect without a guard code change that is
   itself an H3-shaped decision.
3. **The gate would not measure production even if flipped** (`F-T36-2`).
4. **Four criteria remain UNEXAMINED** (1, 2, 5, 8) and D-24 part 3 forbids flipping on any of
   them. Two of the four are definition questions, not repairs.

### 4.4 — What this task did not do

No `asset_registry` row was written. No guard file was edited. No `.github/` file was touched. The
CI switch was **not** flipped and nothing was wired blocking. No severity was changed. No rule was
turned green — every drafted disclosure carries `does_not_turn_the_rule_green: true`. No
`DECISIONS.jsonl` or `state/*.jsonl` line was edited. `ka_gochara_sweep` (charter P1) was not
touched, and `migrate.ts` / `asset_registry_seed.ts` were not imported (D-13). No UNEXAMINED entry
was resolved by this agent, and nothing here is certified — that is PARĪKṢAKA's (I16 / H7).

---

## 5 — Open questions this document raises and does not answer

| # | question | whose |
|---|---|---|
| Q1 | Does §8.6 stage 2 override Phase 0.4 and 0.7, as it would override 0.6a if read as specific? The `has_substeps` case is forced by D-30's own verification property; partitions and the consumer map are not. | ADHIKĀRIN (G9) |
| Q2 | Should the two C-28 detectors be reconciled? The guard filters to `asset_kind IN (data, artifact)`; the scorecard does not. The 7 rows in the gap are all services. The residual D-30 part 3 deferred (31) was measured under the guard's definition. | ADHIKĀRIN (G9) |
| Q3 | Is a per-rule disclosure reader plus a disclosure-conditioned severity a legitimate mechanism, or is it H3 by another name? | ADHIKĀRIN (G9 / H3) |
| Q4 | Should the CI baseline snapshot be refreshed, or should the workflow invoke `--live`? A refreshed snapshot is a frozen claim about a moving registry; `--live` needs a credential in CI. | ADHIKĀRIN (G9) |
| Q5 | With criterion 10's merged half parked, what does M0 "closing" mean — closed-with-a-parked-criterion, or held open? | ADHIKĀRIN, and possibly the native |

---

*Authored by KĀRAKA M0-T36 on `campaign/nirmana-autonomous`. Certified by nobody: a KĀRAKA
reports observations, not verdicts (I16 / charter H7).*
