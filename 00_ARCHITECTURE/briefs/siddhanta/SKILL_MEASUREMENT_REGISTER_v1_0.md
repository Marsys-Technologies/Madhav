---
artifact: SKILL_MEASUREMENT_REGISTER
canonical_id: SKILL_MEASUREMENT_REGISTER
version: 1.0
status: LIVE — append-only. Measurements are NEVER deleted or edited, only superseded.
created: 2026-08-08
campaign: SIDDHANTA (arc-finishing run)
governing_rulings: R14 (permanent baseline), R16 (scope-stated claims)
chart: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty, native)
---

# Skill Measurement Register

The platform's temporal skill score is an **irreversible published artifact**
(FIRST-SCORE-BECOMES-BASELINE). `kala_field_skill` is rebuilt delete-then-insert
per §N.3, so the live table holds only the MOST RECENT measurement. This register
is the durable record of every measurement ever published, including invalid ones.

**Append-only. A measurement is never deleted and never edited — only superseded,
with a stated reason.**

---

## Why an invalid measurement is kept

An invalid measurement is evidence about the instrument, not noise to be hidden.
Deleting MEASUREMENT #2 would erase the only proof that the platform once
published a number it should not have. It is retained, clearly labelled, and
must never be read as a real measurement of the chart.

---

## MEASUREMENT #1 — R14 PERMANENT BASELINE

| Field | Value |
|---|---|
| Campaign | PRATIJÑĀ-SATYA |
| Status | **VALID — R14 permanent baseline** |
| Engine | bo_pratijna v2 lineage |
| Aggregate n_events | 6 |
| All classes | `underpowered` |
| Scope | chart 482012f1 |

**Interpretation:** honestly underpowered. The scoring machinery ran and correctly
declined to produce a score from insufficient events. This is the baseline R14
declares permanent; it is not superseded by anything below.

**Provenance note (R16 scope-stated):** the row-level detail is recorded in the
SIDDHANTA ledger's Baselines table, not captured here row-by-row — by the time
this register was created the live table had already been overwritten by
MEASUREMENT #2. The aggregate figure (n=6, all underpowered) is the surviving
attested value.

---

## MEASUREMENT #2 — INVALID (DB6 DEFECT) — SUPERSEDED

| Field | Value |
|---|---|
| Campaign | SIDDHANTA Phase 4 |
| Status | **INVALID — SUPERSEDED. NEVER READ AS A REAL MEASUREMENT.** |
| Superseded reason | **DB6**: `_match_signal_to_class` compared bhava/karaka/divisional patterns against raw fact_id digests instead of resolved fact_keys, so it matched NOTHING. All occurrence/condition weights were 0.0 by construction. |
| Engine | `bo_pratijna_v3.0` |
| Weights version | `v0_classical` |
| Field snapshot | `kfs_87484404af9d6fe9dc66a3d78812f8bc` |
| Aggregate n_events | 7 (6→7 via R15 foreign_settlement) |
| Released | 2026-08-08 00:42:00 UTC |
| Captured to this register | 2026-08-08, before the DB6 rebuild overwrote it |

### Full row snapshot (verbatim, as published)

| event_class | n_events | n_prospective | skill_score | skill_state |
|---|---|---|---|---|
| childbirth | 1 | 0 | -8.881784197001252e-16 | underpowered |
| foreign_settlement | 1 | 0 | -3.557917849228431e-15 | underpowered |
| marriage | 1 | 0 | 2.220446049250313e-16 | underpowered |
| relocation | 2 | 0 | -4.6157522248790883e-14 | underpowered |
| separation | 1 | 0 | -5.325601071248798e-15 | underpowered |
| surgery | 1 | 0 | 6.938893903907228e-18 | underpowered |
| **(aggregate)** | 7 | 0 | -1.4551108334132883e-14 | underpowered |

### Goodness-of-fit (kala_field_gof), same snapshot

| event_class | n | ks_statistic | ks_p | gof_state |
|---|---|---|---|---|
| childbirth | 1 | 0.6900829237787935 | 0.6198341524424129 | underpowered |
| foreign_settlement | 1 | 0.9954602824227211 | 0.00907943515455778 | underpowered |
| marriage | 1 | 0.745496525865683 | 0.5090069482686339 | underpowered |
| relocation | 2 | 0.8757963334342765 | 0.030853101576738824 | underpowered |
| separation | 1 | 0.9966047988144918 | 0.0067904023710163575 | underpowered |
| surgery | 1 | 0.9958511546362478 | 0.008297690727504303 | underpowered |

### How to read these numbers

**Every `skill_score` above is machine epsilon — i.e. exactly zero.** They are not
small real skill values; they are floating-point residue from arithmetic over an
all-zero hazard field. `skill_lo == skill_hi == skill_score` on every per-class
row (degenerate interval, no bootstrap spread).

The `skill_state = underpowered` label is **correct and honest** — the machinery
did refuse to certify a score. But the underlying field was broken, not merely
sparse. So this measurement is uninformative about the chart in two independent
ways at once, and the register records both.

---

## PRE-DB6 PRODUCTION BASELINE (bodha_pratijna, captured 2026-08-08)

Captured from live production while the **v3 engine was deployed but DB6 was
NOT**. This isolates DB6's effect: any change after the rebuild is attributable
to the dereference fix alone, not to the v3 rewrite (already live here).

Chart 482012f1, ayanamsha `lahiri_chitrapaksha`:

| event_class | status | grade | occurrence_grade | condition_grade |
|---|---|---|---|---|
| childbirth | promised | 5.941 | 8.487 | **0.000** |
| foreign_settlement | promised | **6.231** | **8.901** | **0.000** |
| marriage | promised | **6.231** | **8.901** | **0.000** |
| relocation | promised | 6.259 | 8.942 | **0.000** |
| separation | promised | **6.231** | **8.901** | **0.000** |
| surgery | conditional | 2.210 | 3.157 | **0.000** |

**Two defects visible in one table:**

1. **DB7 is platform-wide, not sample-scoped.** `condition_grade` is `0.000` for
   **135 of 135** rows on this chart across all ayanamshas — not merely the
   4,000-signal sample originally examined. The condition half of the
   two-judgment architecture was contributing nothing, anywhere.

2. **The identity collapse is live.** `marriage`, `separation`, and
   `foreign_settlement` are byte-identical (6.231 / 8.901). These are
   classically distinct — marriage keys on 7H/Venus/Jupiter/D9, separation
   additionally requires dusthana involvement (6/8/12) with Saturn/Ketu. With
   fact-key matching dead, the classes could not diverge because the evidence
   that distinguishes them was never read.

This is the state the native's chart is in as of this capture: `separation` and
`marriage` are the *same promise*, and nothing in the promise register can tell
them apart.

---

## MEASUREMENT #3 — POST-DB6-FIX

| Field | Value |
|---|---|
| Campaign | SIDDHANTA arc-finishing run |
| Status | **PENDING** — awaiting merge of PR #1100, deploy, and rebuild |
| Prerequisite | DB6 fix live in production code |

**Pre-registered expectation (recorded BEFORE the measurement, so it cannot be
retrofitted):** the hazard field will become non-degenerate — 21/21 event classes
match on live data and condition weights are nonzero for 20/21 (verified
read-only, 4,000-signal sample, chart 482012f1). Whether that yields a *certifiable*
skill score is a separate question entirely: with aggregate n=7 events, classes
will very likely still report `underpowered`. **A non-zero field does not entitle
the platform to a skill number.** If the machinery reports `underpowered` again,
that is the correct and expected result, and it must be published as such.

### OUTCOME: **PARKED — not measured this run**

The DB6 fix is **merged and live in production** (squash `ac0545c2d`, Deploy to
Cloud Run SUCCESS, 2026-08-08T06:17Z). MEASUREMENT #3 was NOT taken, because the
rebuild that would produce it could not be run honestly within this session.

**What was attempted, and what happened:**

A bounded scoped rebuild of `bo_pratijna` alone (`scope='asset'`, run
`c796689e`) was created and executed. The orchestrator **refused it**:

> `BLOCKED: upstream dependency(ies) bo_laksana, bo_sangati did not complete in
> this run; skipped to avoid building on incomplete data`

That guard is correct and should not be worked around — it is the orchestrator
refusing to build on stale upstream data, which is the same discipline this
whole arc is about. The attempt was clean: **`bodha_pratijna` still holds its
135 rows, untouched** (the guard fires before the writer's delete-then-insert).

**Disclosed side effect:** the blocked attempt moved `bo_pratijna`'s
`asset_throughput.state` from `stale` to `error` (chart error count 5 → 6). The
recorded reason is accurate and self-describing. It was left in place rather
than hand-reverted — editing production state to look tidier would erase a real
event.

**Why the full rebuild was not launched instead:** a full-DAG rebuild is 60+
minutes (`ga_sensitive` alone ~45), and the six most recent build runs on this
chart are all `failed` or `stopped`, several with
`orphan-watchdog: run never dispatched`. Starting a multi-hour production
rebuild that could not be supervised to completion — on a chart whose recent
rebuild history is entirely failures — risked leaving it in a worse partial
state than it is now. PARKED-HONEST with evidence beats a half-finished rebuild.

**Resume condition (precise):** run a full-DAG rebuild of chart 482012f1 with
the now-deployed DB6 code, supervised to completion, then re-score
`kala_field_skill`/`kala_field_gof` and record the result here as MEASUREMENT #3
— whatever it is, including `underpowered`.

**The pre-registered expectation above stands unmodified and unconsumed.** It
was written before any measurement and is still the prediction to be tested.

---

## Register discipline

1. Append only. Never delete or edit a published measurement.
2. Every supersession states a **reason**, not just a status flip.
3. An invalid measurement stays visible next to the valid ones.
4. R14's MEASUREMENT #1 remains the permanent baseline regardless of what follows.
5. `underpowered` is a legitimate terminal result, never a failure to be
   engineered away (§N.8 — a score without a real detector behind it is null,
   not green).
