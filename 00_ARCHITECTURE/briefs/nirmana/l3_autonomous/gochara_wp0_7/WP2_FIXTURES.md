---
artifact: WP2_FIXTURES
version: "1.0"
status: WP2_DELIVERED
date: 2026-09-23
executes: KIMI_AUTONOMOUS_EXECUTION_PROMPT_GOCHARA_v1_0.md §4 WP2 + GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §4.2 + WP1_CONTRACTS.md §7/§9/§10
branch: l3/gochara-autonomous-wp0-7
---

# WP2 — Synthetic fixture suite: derivations

**Every expected answer herein is independently derived; no legacy system output was consulted.**
`services/gochara_v3`, `services/w2g`, and `pipeline/transit_search.py` were never executed and never
read for values while producing these fixtures. Swiss-derived numbers were computed directly with
pyswisseph 2.10.03 against the sha256-verified `.run/se1` files; every other number is hand-specified
math shown below. All chart ids are synthetic `wp2-synth-*`. Machine-readable companions:
`platform/python-sidecar/tests/l3/gochara/fixtures/wp2_geometry.json` (cases 1–6, 12),
`platform/python-sidecar/tests/l3/gochara/fixtures/wp2_honesty.json` (cases 7–11),
`platform/python-sidecar/tests/l3/gochara/oracle.py` (the scorer oracle).

## 0. Ephemeris discipline (F-14) — applies to every Swiss number in this document

- `swe.set_ephe_path('/Users/Dev/madhav-l3/gochara-wp0-7/.run/se1')`; `swe.set_sid_mode(swe.SIDM_LAHIRI)`;
  flags `FLG_SWIEPH | FLG_SIDEREAL` (D-1) on every call; node sampling at noon-UT knot-compatible instants (F-15).
- After **every** `swe.calc_ut` / `swe.calc` call: `assert retflag & 2`. Observed on all calls here:
  `retflag = 65602` = `FLG_SIDEREAL(65536) + NONUT(64, added internally by Swiss under sidereal) + SWIEPH(2)`.
  A `retflag & 4` (Moshier) result would have made the affected case `NOT_RUN`, never a pass.
- `.se1` checksums (verified by `shasum -a 256` before any computation, matching WP1_CONTRACTS.md §10):
  `sepl_18.se1 ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66` ·
  `semo_18.se1 1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7` ·
  `seas_18.se1 a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2`.

## 1. Case 01 — Close-station cubic (three roots)

Synthetic curve, no ephemeris:

```
lambda(t) = 270.0 + 0.001*(t-3)*(t-6)*(t-9)   degrees,  t in days from 2026-01-01T00:00:00Z
```

f(t) = lambda(t) − 270.0 = 0.001·(t³ − 18t² + 99t − 162). Roots of f: exactly **t = 3, 6, 9**
(the factored form), i.e. **2026-01-04 / 2026-01-07 / 2026-01-10 T00:00:00Z**.

- **Direction:** f′(t) = 0.001·(3t² − 36t + 99); f′(3) > 0 (direct), f′(6) < 0 (retrograde), f′(9) > 0 (direct).
- **Station proximity:** f′ = 0 at t = 6 ± √3 = 4.267949 / 7.732051; f there = ±0.0103923° = **±37.4″**.
  The body reverses only 37″ from the target — far inside the 1.0° orb — so the orb is **never vacated**
  between roots. This is the close-station trap: three exact crossings inside one continuous in-orb span.
- **Orb boundaries** (orb_conj_slow = 1.0°, WP1 §7): |f| = 1 →
  t³ − 18t² + 99t + 838 = 0 → one real root **t = −4.29991269688132** → **2025-12-27T16:48:07Z** (entry, λ=269.0);
  t³ − 18t² + 99t − 1162 = 0 → one real root **t = +16.29991269688132** → **2026-01-17T07:11:52Z** (exit, λ=271.0).
  Verified by direct evaluation: λ(entry) = 269.000 exactly, λ(exit) = 271.000 exactly.
- **Independent root check:** bisection on f(t) over [2,4], [5,7], [8,10] reproduces 3.000000000 / 6.000000000 /
  9.000000000 (max |numpy.roots − bisection| = 3.2e-12 days); `numpy.roots` on the monic cubic agrees.

**Pinned episode rule (WP2 decision):** one episode per root; since the orb is never vacated, each
episode's t_in/t_out are the orb boundaries clipped at the neighbouring roots —
episode k spans [max(orb_entry, t_exactₖ₋₁), min(orb_exit, t_exactₖ₊₁)]. Expected: **3 episodes**
(t_in/t_exact/t_out = 2025-12-27T16:48:07Z→2026-01-04→2026-01-07 / 2026-01-04→2026-01-07→2026-01-10 /
2026-01-07→2026-01-10→2026-01-17T07:11:52Z), branches direct/retrograde/direct, dwells
10.2999 / 3.0 / 7.2999 days, tolerance_arcsec 2.0, bracket_seconds 300 (WP1 §9, slow exact roots).

## 2. Case 02 — True-node excursion under the mean-node convention

Exact Swiss snippet (pyswisseph 2.10.03):

```python
swe.set_ephe_path('/Users/Dev/madhav-l3/gochara-wp0-7/.run/se1')
swe.set_sid_mode(swe.SIDM_LAHIRI)
FLG = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
jd = swe.julday(2026, 1, 1, 0.0) + i * 0.25        # 6-hour sampling across 2026 (1465 samples)
lon_t, rf_t = swe.calc_ut(jd, swe.TRUE_NODE, FLG)   # assert rf_t & 2  (65602 observed)
lon_m, rf_m = swe.calc_ut(jd, swe.MEAN_NODE, FLG)   # assert rf_m & 2
sep = abs(lon_t[0] - lon_m[0]); sep = min(sep, 360 - sep)
```

**Computed result:** max |true − mean| over 2026 = **1.7642302810° = 6351.229″** at **2026-07-02T18:00:00Z**
(true node 306.5003912°, mean node 308.2646215°, sidereal Lahiri). The 6 h sampling resolves the
quasi-monthly true-node oscillation's maximum to better than 15″ (its period is ~27 days). The often-quoted
"~1.5°" is close but not the 2026 value; the actual computed figure is pinned in the fixture.

**Convention pin (N-4a(b″)):** all Rahu/Ketu contact solving consumes `swe.MEAN_NODE` under
`FLG_SIDEREAL`. A kernel using `TRUE_NODE` would misplace node contacts by up to ~1.76° = 6351″ —
three orders of magnitude above the §9 tolerance. Rahu/Ketu remain valid conjunction/ingress/kakṣyā/return
agents and targets (N-14 removes only their dṛṣṭi).

## 3. Case 03 — Seam tangency at a partition boundary

Synthetic monotone arc, hand-specified:

```
lambda(t) = 270.0 + 0.1*(t - 5)   deg, t in days from 2026-03-01T00:00:00Z  (direct, 0.1 deg/day)
Partition A = [2026-03-01T00:00Z, 2026-03-06T00:00Z];  Partition B = (2026-03-06T00:00Z, 2026-03-11T00:00Z]
Target 270.5°, orb 1.0° (orb_conj_slow).
```

Contact: λ = 270.5 → t = 5 exactly → **t_exact = 2026-03-06T00:00:00Z = the seam instant**.
Orb span: 1.0° / 0.1°/day = ±10 days → t_in = 2026-02-24T00:00:00Z, t_out = 2026-03-16T00:00:00Z
(the orb straddles both partitions even though t_exact sits exactly on the seam).

**Expected: exactly 1 episode** (t_in/t_exact/t_out above, branch direct). Pinned attribution rule: a
contact whose t_exact equals a partition seam belongs to the partition whose END it equals (A, end-closed).
**Zero** episodes (seam silently dropped) and **two** episodes (duplicated across partitions) are both
failures. This is the plan §10 "partition seam → same contact_id" positive control.

## 4. Case 04 — Start-inside / end-inside at the horizon edge (truncated, never dropped)

Horizon [2026-04-01T00:00Z, 2026-05-01T00Z), target 268.0°, orb 1.0°.

**4a — start-inside, t_exact BEFORE the horizon.** λ(t) = 268.5 + 0.05·(t − horizon_start).
At horizon start λ = 268.5 (0.5° inside the orb). t_exact (λ = 268) would be at t = −10 d =
2026-03-22T00:00Z — before the horizon. Orb exit (λ = 269) at t = +10 d = 2026-04-11T00:00Z — inside.
Expected: 1 episode, t_in = **2026-04-01T00:00Z** (= horizon start), t_exact = **absent**, t_out =
**2026-04-11T00:00Z**, truncated_at_horizon = **'start'**, exact_crossing = false, orb overlap = **10.0 days**.
This is also the required "t_exact outside horizon but orb overlaps" case: dropping the episode, or
fabricating a t_exact inside the horizon, is a failure.

**4b — end-inside, t_exact INSIDE the horizon.** λ(t) = 269.5 − 0.06·(t − horizon_start).
Orb entry (λ = 269) at t = 25/3 d = **2026-04-09T08:00:00Z**; t_exact (λ = 268) at t = +25 d =
**2026-04-26T00:00:00Z**; orb exit (λ = 267) would be at t = 125/3 d = 2026-05-12T16:00:00Z — beyond the
horizon. Expected: 1 episode, t_in = 2026-04-09T08:00:00Z, t_exact = 2026-04-26T00:00:00Z, t_out =
**2026-05-01T00:00Z** (= horizon end), truncated_at_horizon = **'end'**, orb overlap into horizon =
**21.6667 days**; the remaining 11.67 days beyond the horizon is reported as unsearched, never folded
into t_out (H-3).

## 5. Case 05 — Noon/midnight epoch conversion (F-15)

Exact Swiss snippet:

```python
jd_noon = swe.julday(2026, 6, 15, 12.0)   # NOON knot abscissa (F-15 convention)
jd_mid  = swe.julday(2026, 6, 15, 0.0)    # midnight — the wrong-abscissa detector
lon_n, rf_n = swe.calc_ut(jd_noon, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)  # assert rf_n & 2
lon_m, rf_m = swe.calc_ut(jd_mid,  swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)  # assert rf_m & 2
```

**Computed result (sidereal, Lahiri, D-1):**

| instant | Moon sidereal longitude |
|---|---|
| 2026-06-15T12:00:00Z (correct noon knot) | **65.62028774757364°** ← pinned substrate value |
| 2026-06-15T00:00:00Z (midnight) | **57.96929397808918°** ← wrong-answer detector |
| **difference** | **7.650993769484458° = 27543.578″** |

**Honest note on the "~332″ class":** WP1_CONTRACTS.md §1 records a historical "spurious 332.3″" from a
midnight abscissa. That figure is a case-specific residual, NOT the 12-hour abscissa shift: the actual
noon-vs-midnight lunar longitude difference computed here is **27,543.6″ (~6.5°)** — the true magnitude of
the F-15 trap for the Moon, and the value pinned in the fixture. A kernel treating noon knots as midnight
(or vice versa) shifts lunar positions by ~27,544″ against the substrate, dwarfing every §9 tolerance
(2–5″). The fixture pins the correct noon-knot longitude as the expected substrate value and the midnight
longitude as the wrong-answer detector.

## 6. Case 06 — Per-graha special dṛṣṭi angles (table case)

Hand-specified per WP1_CONTRACTS.md §7 and the §2.2 N-14 note (doctrine: BPHS ch.26,
`bphs_vol1:16496-16505`; dṛṣṭi-koṇa graduation ch.26 śl.6–8 at `:16514-16529`):

| graha | dṛṣṭi angles (deg) |
|---|---|
| Mars | 90, 180, 210 |
| Jupiter | 120, 180, 240 |
| Saturn | 60, 180, 270 |
| Sun, Moon, Mercury, Venus | 180 |
| **Rahu** | **{} (EMPTY — N-14: no dṛṣṭi at all, not even the 7th)** |
| **Ketu** | **{} (EMPTY — same)** |

Rahu/Ketu **remain** valid agents and targets for conjunction, sign-ingress, nakṣatra-ingress,
kakṣyā-cell crossing and return; only `drishti_contact` is excluded from their relation set. Any
dṛṣṭi_contact episode with body or target Rahu/Ketu is a test failure (this supersedes the served
`SPECIAL_DRISHTI_DEG` nodal entries — F-29).

## 7. Cases 07–11 — Honesty fixtures (state-based, no ephemeris)

Machine-readable in `wp2_honesty.json`; logic per WP1_CONTRACTS.md §2:

- **07 — negative sensitive-degree check → zero targets.** The four negative predicates
  (`not_gandanta`, `mrityu_bhaga=not_fired`, `not_pushkara`, `kartari=none`) are removed at the
  resonance layer (N-12, WP3c R-1). Expected: 0 resolved targets, 0 carried targets, nothing stored as
  'inapplicable' — the honest outcome is the row's absence, not a negative row.
- **08 — cusp-placeholder arudha.** Stored `longitude_sidereal` = 270.0000 = 30·(10−1) exactly. Expected:
  target resolves as the Capricorn interval [270, 300) (sign_ingress/residence only); **zero** degree-level
  contacts against 270.0000 — any such contact is a failure (the cited fact does not carry that degree; F-20).
- **09 — dangling yoga id.** `ardhachandra` with no live `ga_yoga_firings` row →
  `target_resolution_state='unavailable'`, stored by R-6 on `gochara_resonance_map` and counted in the
  coverage manifest; never a silent skip, never an invented degree (F-21).
- **10 — missing overlay.** Query 2028 interval vs overlay coverage ending 2027 → `quality_gates = None`,
  completeness_state 'unavailable', `unavailable_inputs` recorded in `kala_gochara_coverage`; **never**
  quality_gates = 1.0 by default. The oracle (§13) returns state 'unavailable' for this input.
- **11 — solver exception.** A primitive raising mid-evaluation propagates as
  `completeness_state='unqualified'` + failure_detail on the row (and is additionally visible as a raised
  EvaluationFailure); λ on the failed row is null — never a 0.0 that a `>=` threshold certifies (F-08/H-2).

## 8. Case 12 — Plateau ties in peak detection

Synthetic daily series (base 2026-01-01T00:00Z): ramp 0.5→0.94 over days 0–11, then **flat 1.0 for
k = 4 days (indices 12–15 = 2026-01-13 … 2026-01-16)**, then ramp down. max = 1.0 attained at exactly
4 consecutive days.

**Pinned tie-break rule:** ALL tied maxima are admitted with the SAME rank — no first-day-wins, no
arbitrary single pick, no "duplicate" drops. Expected peak set: the 4 plateau days, each with rank 1.
With H-5 (fixed cap removed), all 4 admitted peaks persist in storage; trimming happens only at serve time.

## 9. The scorer oracle (oracle.py) — pinned specification + hand-worked examples

Pinned formula: `lambda_raw = clamp(PROMISE · PERMISSION · activity · tara_modifier · w30_modifier ·
quality_gates, [0,1])`; sign applied separately (`±lambda_raw` by channel). All factors are explicit
arguments; no DB, no Swiss, no `services/` imports — definitionally independent of the system under test.

**Activity (span-aware legacy ±5-day box, `orb_legacy_box`, WP1 §7):** per episode i, window
Wᵢ = [max(t_in, t_exact−5d), min(t_out, t_exact+5d)] (clipped by the query span if given); with linear
motion through exact, sep(t) = speed·|t − t_exact| and decay(t) = max(0, 1 − sep/orb); contribution
cᵢ = max over Wᵢ of decay(t) (0 if Wᵢ empty). **Combination rule (pinned): noisy-OR** —
`activity = 1 − Π(1 − cᵢ)`. Noisy-OR is pinned over summation because legacy semantics saturate at 1.0
and summation would need an un-pinned renormalization; noisy-OR is order-independent, idempotent
(duplicate episodes count once — H-6), and monotone.

Hand-worked arithmetic (also in the oracle docstring):

- **E1:** promise 0.8, permission 1.0, tara 1.0, w30 1.0, qg 1.0, benefic; one episode with t_exact
  inside the window, speed 0.05°/d, orb 1.0° → c₁ = 1 (sep 0 at t_exact) → activity = 1 →
  **lambda_raw = 0.8, signed +0.8**.
- **E2:** same factors, query window = [t_exact+8d, t_exact+10d] → W₁ empty (8 d > 5 d box) →
  c₁ = 0 → activity = 0 → **lambda_raw = 0.0**.
- **E3:** two episodes each with c = 0.5 → activity = 1 − (1−0.5)² = **0.75** (not 1.0 — noisy-OR, not
  saturation-by-sum; not 0.5 — the two independent contributions combine). With promise 0.8, qg 1.0,
  benefic: lambda_raw = 0.8 · 1 · 0.75 · 1 · 1 · 1 = **0.6**.
- **E4 (unavailable):** quality_gates = None → state 'unavailable', lambda None — never 1.0-by-default
  (case 10).

## 10. Second pass — independent cross-check of the Swiss-derived numbers

Three Swiss-derived expected values were re-derived by a genuinely different call path —
`swe.calc` at **ephemeris time** with explicit ΔT (`jd_et = jd_ut + swe.deltat(jd_ut)`) instead of
`swe.calc_ut`:

| value | primary (calc_ut) | cross-check (calc at JD_ET) | agreement |
|---|---|---|---|
| Case 05 Moon longitude 2026-06-15T12:00Z | 65.62028774757364° | 65.62028774757364° | **0.000″** |
| Case 05 Moon longitude 2026-06-15T00:00Z | 57.96929397808918° | 57.96929397808918° | **0.000″** |
| Case 02 max node separation | 6351.229011″ | 6351.229011″ | **0.000″** |

(ΔT at both instants ≈ 0.000796845 d; all four cross-check calls returned retflag 65602, `retflag & 2`
asserted.) A third, frame-level check on the case-05 noon value — tropical longitude minus
`get_ayanamsa_ut` — gives 65.6223320°, agreeing within **7.36″**, exactly the expected
nutation-in-longitude-of-date difference between the two sidereal paths documented in WP1_CONTRACTS.md
§1 (D-1 note); this confirms the Lahiri frame independently at the arcsecond level.

The synthetic numbers were cross-checked by direct evaluation: case-1 orb boundaries reproduce λ = 269.0 /
271.0 exactly; bisection vs numpy.roots agree to 3.2e-12 days; case-3/4 contact instants reproduce the
target longitudes exactly from the stated linear curves.

## 11. WP1 contract cross-check (exit gate)

- Orb values used: `orb_conj_slow` = 1.0° (cases 1, 3, 4) ✓ against WP1 §7.
- Tolerances quoted: slow exact roots 2.0″ / 300 s (case 1) ✓ against WP1 §9.
- Node convention: mean node, `swiss_mean_node_flg_sidereal` (case 2) ✓ N-4a(b″).
- Dṛṣṭi table incl. empty nodal sets (case 6) ✓ N-14.
- Noon-UT knot abscissa (case 5) ✓ F-15. F-14 retflag discipline: asserted on every Swiss call ✓.
- JSON parses (validated with `json.load`); both fixture files and the oracle module are byte-written
  and re-readable.

## 12. Exit-gate statement

Every case 1–12 has a written expected answer with its derivation shown **before any kernel code exists**
(`services/gochara_kernel` does not exist; nothing in this WP created it). No stop condition from the
execution prompt §6 was hit. No file outside the three WP2 deliverable paths was modified. Nothing was
staged or committed.
