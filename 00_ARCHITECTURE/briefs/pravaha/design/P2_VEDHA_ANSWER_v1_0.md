---
artifact: P2_VEDHA_ANSWER
version: "1.0"
status: ANSWER TO STEWARD QUESTION (not a spec version; no code); recommendations marked MINE are not rulings
date: 2026-10-02
author: stream-B (Exec B)
question: steward M20261002T004315-1d70 — Stream A's P2 sweep: (Q1) the vedha-overlay source for ka_gochara_v5; (Q2) the value mapping of vedha_attenuation
sources: >
  S = GOCHARA_DESIGN_SPECS_v1_4 §5 / §2.3 · O = GOCHARA_TEST_ORACLES_v1_4 (O-VI-1…5) · R = services/gochara_rules/{registry,vedha}.py ·
  L0 = production bg_transit_rules (read-only, 2026-10-02; 76 rows) · L3 = production kala_vedha_gochara (read-only; schema + counts) ·
  corpus (served, read verbatim this pass): phaladeepika:PG322:C1 (Adh. XXVI śl.3–5), phaladeepika:PG323:C1 (śl.6–8).
---

# P2 vedha — answers

## Q2 first (it decides Q1's scope): what vedha does to the result
**The served corpus says vedha NULLIFIES the good result of a favourable-house transit.** Phaladīpikā XXVI.3 (`PG322:C1`): the Sun "is
declared auspicious" in the 11th/3rd/10th/6th "if, at the time, the corresponding (Vedha) places … are not marred by the transit of any of
the planets other than Saturn" — and the translator's note: "if other planets transit them, they **nullify the good effect** that would
otherwise be caused by the Sun's transit." The same shape recurs: Moon śl.4 (obstructors "other than Mercury"), Mars/Saturn śl.5 (Saturn's
exception: the Sun), Mercury śl.6 (`PG323:C1`, "not occupied by any of the planets other than the Moon"), Jupiter śl.7 ("void of planets"),
Venus śl.8 (served translation: "bad effects … if he is marred by planets in the corresponding (Vedha) places"). L0 stores it the same way:
42 vedha rows, each with `classical_citation`, all `rule_type='favourable'`, notes "Vedha from Nth **nullifies result**". Nothing in the
read text grades it (no ½, no ¼) — so a graded attenuation is **uncited** (and D-PG353 already removed the one generalised scale).
**Mapping that is cited:** active ⇒ the favourable result is **nullified (0.0)**; no active obstruction ⇒ **1.0** — a cited step, not a calibration.
**Conflict I must flag:** S §2.3 inv 3 says "no soft factor zeroes an admitted window; vedha … qualify" and §5.2 inv 1 "never excludes a
window". Reconciliation (**MINE → AM-18**): the *window stays admitted* (admission is by predicates only); the cited nullification sets the
**record's for-channel value to 0.0** and the record carries `qualification: vedha_active` — "zeroes" in inv 3 read as *excludes*. If the
steward prefers the strict reading, the fallback is value 1.0 with the nullification carried **only as a qualification annotation** (no score
effect). Not adverse residence (12/8/1): the corpus attaches vedha to *favourable* houses only.
**Vipareeta:** **no served citation found.** The verbatim PG322–323 slokas contain no vipareeta clause; L0's notes carry exceptions (Sun↔Saturn,
Moon↔Mercury) but no vipareeta; two corpus searches returned nothing. S §5/O-VI-4 specify the carve-out mechanics without a source. **MINE:**
until cited, `cancelled_vipareeta` is **not produced** (state stays `active`); recording it as a native decision / human corpus read.
**Rāhu/Ketu pairs:** 9 L0 rows are marked **UNSOURCED** by L0 itself ("no house-transit vedha doctrine for Rahu/Ketu … in the served corpus") —
**must not be used** as primary-transit vedha.

## Q1: the overlay source
* **What the frozen spec says:** §5.1 `vedha_interval(… t_in, t_out, state ∈ {active, cancelled_vipareeta, inactive} …)` with half-open
  intervals; O-VI-2/-4 use whole-second timestamps; O-VI-5: absent overlay coverage reads `unavailable`, never 1.0. It does **not** name a source asset.
* **(a) read `kala_vedha_gochara`:** its windows are `window_start/window_end` **`date`** columns (+ truncation flags; 171 rows for this chart:
  `house_vedha` 127, `latta` 20, `sarvatobhadra` 24 — only `house_vedha` is this rule). A date-grain source cannot give instant-precision half-open
  intervals: mapping a date to `[00:00Z, next-00:00Z)` is a ±1-day error at every edge, and the `unavailable`/completeness claim would rest on
  another generation's coverage. Staleness detection exists only as the 4.x pattern — `vedha_upstream_fingerprint` in the manifest vector
  (`step06_candidate_build.py`: `reports["house_vedha"].current`, refuse when stale) — i.e. AM-16 would have to carry it.
* **(b) derive inside v5 from stored residence spans** — **MINE, agrees with your leaning.** Vedha is, by the sloka, an **interval
  intersection**: [primary graha resident in house h from janma-rāśi] ∩ [an obstructor resident in vedha house v]. Both are residence spans of
  grahas, already substrate in the same generation, at solved-instant precision, **one substrate, one generation, no cross-generation staleness**
  (the snapshot's `input_digest` already covers it). The pairs table **is in L0** with citations: `bg_transit_rules` (above), 42 vedha rows
  incl. exception notes — use the 33 cited rows (7 grahas), not the 9 node rows.
* **Oracle:** O-VI-1…5 exist but are fixtures over already-built `vedha_interval` rows; **no oracle derives them from residence spans**
  (**MINE:** add O-VI-6 — two literal residence spans + the Sun↔Saturn / Moon↔Mercury exception cases → exact half-open vedha interval).
* **Two scope limits (b) cannot hide (→ AM-18):** (i) **The Moon is never a stored agent** (M-3/AM-14) yet the corpus lists "planets other than
  X", which includes the Moon (except in the Moon↔Mercury case) — so a stored vedha state can be **`active`** (proved by a stored obstructor) but
  never fully **`inactive`**; `inactive` must be scoped "excluding the on-demand Moon tier", exactly like AM-14. (ii) Whether Rāhu/Ketu *obstruct*
  is **silent** in the read slokas — **native/corpus decision**; the 4.x overlay's choice is not a citation.
* **Recommendation: (b)**, with the nullification mapping above, `cancelled_vipareeta` not produced until cited, node obstruction an open decision,
  and `inactive` scoped. (c) "named-missing" remains the honest fallback for P2 until AM-18 is ruled.

**Constrained by the 3.0-vs-controls measurement?** No — vedha never excludes a window (admission unchanged), so T-cover/T-FP are unaffected; it
moves scores (T-rank) only, and only in the nullified direction.
