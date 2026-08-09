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

## MEASUREMENT #3 — POST-DB6-FIX — ATTEMPTED, BLOCKED BY DEGENERATE-INTERVAL TRIPWIRE

| Field | Value |
|---|---|
| Campaign | PRATIJÑĀ v4, Lane B6 |
| Status | **BLOCKED — NOT a valid skill measurement. Real live write; NOT rolled back. Live `kala_field_skill`/`kala_field_gof` tables now hold THIS run's numbers (they supersede MEASUREMENT #2's stale numbers in the table, per §N.3 delete-then-insert — MEASUREMENT #2's numbers above remain the register's permanent transcription of that prior state).** |
| Engine | `bo_pratijna` v4 + `ka_kshetra` (this campaign's Lanes B2/B5 rebuild) |
| Weights version | `v0_classical` (unchanged — no refit occurred; see diagnosis) |
| Field snapshot | `kfs_87484404af9d6fe9dc66a3d78812f8bc` (pin-identity hash — chart/corpus/weights/schema/config; unchanged from MEASUREMENT #2 because none of THOSE pins changed, even though the field's own computed rows did — confirmed by direct read, see diagnosis) |
| Writer invocation | Real live write via `ContextSpec`/`WriterBase.run(ctx)` + `conn.commit()` (same pattern twice-proven this campaign). `MiBharaWriter().run(ctx)` → `WriterResult(rows_inserted=13, rows_updated=0, rows_skipped=0, duration_seconds=10.39)`. Committed 2026-08-09T09:25:34Z. |
| Aggregate n_events | 7 (unchanged from MEASUREMENT #2 — same R15 event set: childbirth ×1, foreign_settlement ×1, marriage ×1, relocation ×2, separation ×1, surgery ×1) |

### Full row snapshot (verbatim, as freshly queried post-write, independent connection)

| event_class | n_events | n_prospective | skill_score | skill_lo | skill_hi | skill_state | degenerate? |
|---|---|---|---|---|---|---|---|
| childbirth | 1 | 0 | -1.7763568394002505e-15 | -1.7763568394002505e-15 | -1.7763568394002505e-15 | underpowered | YES (n=1) |
| foreign_settlement | 1 | 0 | 5.329070518200751e-15 | 5.329070518200751e-15 | 5.329070518200751e-15 | underpowered | YES (n=1) |
| marriage | 1 | 0 | -1.9984014443252818e-15 | -1.9984014443252818e-15 | -1.9984014443252818e-15 | underpowered | YES (n=1) |
| relocation | 2 | 0 | 5.551115123125783e-17 | 5.551115123125783e-17 | 5.551115123125783e-17 | underpowered | YES (n=2) |
| separation | 1 | 0 | -3.552713678800501e-15 | -3.552713678800501e-15 | -3.552713678800501e-15 | underpowered | YES (n=1) |
| surgery | 1 | 0 | -1.7208456881689926e-15 | -1.7208456881689926e-15 | -1.7208456881689926e-15 | underpowered | YES (n=1) |
| **(aggregate)** | 7 | 0 | -5.15460690004537e-16 | -2.038052266633323e-15 | 1.5146614121671778e-15 | underpowered | **no — `skill_lo != skill_hi`** |

### Goodness-of-fit (kala_field_gof), same run

| event_class | n | ks_statistic | ks_p | ljung_box_stat | ljung_box_p | gof_state |
|---|---|---|---|---|---|---|
| childbirth | 1 | 0.5125215391350215 | 0.974956921729957 | — | — | underpowered |
| foreign_settlement | 1 | 0.9967218389142283 | 0.006556322171543449 | — | — | underpowered |
| marriage | 1 | 0.8168694788266082 | 0.3662610423467836 | — | — | underpowered |
| relocation | 2 | 0.8937905624751672 | 0.022560889238682727 | 2 | 0.15729920705028105 | underpowered |
| separation | 1 | 0.9970813886288142 | 0.005837222742371528 | — | — | underpowered |
| surgery | 1 | 0.9594810383367165 | 0.08103792332656701 | — | — | underpowered |

### Degenerate-interval tripwire: FIRED (6 of 7 rows)

Every per-class row except the chart-level aggregate shows `skill_lo == skill_hi`. Per this
register's own discipline, that is the exact shape of MEASUREMENT #2's defining defect and
blocks publication as a valid measurement pending diagnosis. Diagnosis performed, root cause
identified, and it is **NOT the same defect as MEASUREMENT #2**:

**1. DB6 is confirmed fixed and live for this snapshot.** Direct read of `kala_field` for
`482012f1` (computed_at `2026-08-08T23:47:54Z`, i.e. after PR #1100 merged `2026-08-08T06:08:51Z`)
shows real, non-zero, PER-CLASS-DIFFERENTIATED hazard magnitudes — e.g. `alpha` = `-9.8664`
(childbirth) / `-15.1825` (foreign_settlement) / `-11.6504` (relocation), `promise_term` =
`0.61335` / `0.72165` / `0.84665` respectively, `lambda_start` ranging `1.9e-7` to `5.2e-5`
across classes. This is the opposite of MEASUREMENT #2's all-zero-by-construction field (every
`condition_grade` was `0.000`, every class's grade byte-identical). DB6's fix is real and live.

**2. The degenerate intervals have a DIFFERENT, separate root cause: the field carries zero
TIME VARIATION.** For every one of the 6 event classes, `gamma = 0` and `alpha` is IDENTICAL
across all 10 segments spanning the full observation window (confirmed by direct query:
`count(DISTINCT alpha) = 1`, `count(DISTINCT gamma) = 1` per class); `clock_term_start`,
`modifier_term_start`, `suppression_term_start` are the identity value `1` in every segment —
i.e. the transit/clock modulation terms are not populated, only the flat structural-prior
baseline is. A perfectly flat (non-time-varying) hazard, compared against `mi_bhara`'s own
null (the SAME field circularly shifted in time — §5.5), is mathematically indistinguishable
from its null: shifting a constant changes nothing, so the per-event advantage `d_k = ln
λ_model(t_k) − mean_r ln λ_null(t_k) ≈ 0` for every event, in every class, by construction —
independent of `n` and independent of whether the underlying promise magnitude is correct.
This is exactly what `mi_bhara.py`'s own docstring already names as a known, scoped limitation
("fitting needs the θ-INDEPENDENT per-segment basis... Until `kala_field` carries those
columns, this method publishes skill and GOF against the AS-BUILT field... It does not
fabricate a basis in order to look complete") — confirmed here as the live, current state:
`weights_version` stayed pinned at `v0_classical` (no refit occurred) and the field is being
served on structural priors only, with the time-varying clock/transit basis not yet wired into
`ka_kshetra`'s stage 4 output.

**3. The `n=1` singleton classes (5 of 6) are degenerate for a THIRD, purely mathematical
reason, independent of both 1 and 2 above:** `compute_skill`'s percentile bootstrap resamples
`n` events from a pool of `n`; for `n=1` every resample draws the same single observation, so
`skill_lo == skill_hi == skill_score` always, for any field, correct or not. This is intrinsic
to the current bootstrap harness at `n=1` and will recur on every future run while any class
has exactly one recorded event — it is not itself evidence of a defect, but it does mean the
tripwire as stated will always fire on singleton classes.

**4. The chart-level aggregate is the one row NOT degenerate** (`skill_lo = -2.038e-15 ≠
skill_hi = 1.515e-15`) — the pooled bootstrap over 7 events does show real (if minuscule)
spread — and its point estimate is honestly ~0, consistent with §7.3: "a field with no temporal
information produces `d_k ≈ 0`... that is a real detector, not a flag." Given the field is
genuinely flat, an aggregate skill of ~0 is the CORRECT answer, not a symptom of brokenness.

### Verdict

**MEASUREMENT #3 is NOT published as a certified skill score.** The pre-registered expectation
("classes will very likely still report `underpowered`... a non-zero field does not entitle the
platform to a skill number") is CONFIRMED — every row reports `underpowered`, correctly, since
`n < 8` everywhere. But the degenerate-interval tripwire additionally surfaced a second,
previously undiagnosed gap this register did not anticipate: DB6 fixed the field's MAGNITUDE
(occurrence/condition weights now resolve and differ correctly across classes), but the field's
TIME-VARYING basis (the clock/transit modulation that would let timing itself carry
information) is not yet wired into `ka_kshetra`'s stage 4 emission for this chart/snapshot.
Until that basis is populated and a real weights refit runs (`v0_classical` → a fitted version),
`mi_bhara`'s skill score cannot become anything other than machine-epsilon-near-zero, REGARDLESS
of event count — i.e. reaching `n≥8` alone will not be sufficient for a future measurement to
certify `established`/`not_established` on real information; the flat-field gap must close
first. This is a genuine, named, non-blocking follow-up for a future lane — not a regression
introduced by this run, and not something R13 (no tuning) permits this task to fix.

**R14 discipline preserved:** MEASUREMENT #1 remains the permanent baseline; MEASUREMENT #2
remains superseded and INVALID; this entry is retained as evidence about the instrument (a
second, distinct defect class found after the first was fixed), not deleted or hidden, per the
register's own stated purpose.

---

## Register discipline

1. Append only. Never delete or edit a published measurement.
2. Every supersession states a **reason**, not just a status flip.
3. An invalid measurement stays visible next to the valid ones.
4. R14's MEASUREMENT #1 remains the permanent baseline regardless of what follows.
5. `underpowered` is a legitimate terminal result, never a failure to be
   engineered away (§N.8 — a score without a real detector behind it is null,
   not green).
