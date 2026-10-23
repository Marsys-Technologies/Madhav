---
version: 0.1
status: DESIGN NOTE — no code, no migration written; not binding until the owner surrogate rules on §12
item: NEAR-STATION-PEAK-INTERVAL (ky:arm, post-campaign; ruling SR-NEAR-STATION-TIE, madhav-44, 2026-10-22T16:25Z; started under SR-WRAP-NOW / OWNER-WRAP-NOW-20261022)
author: Claude Sonnet 5.5 (job X-20261022T200502Z-near-station-peak-interval)
baseline_read: kalayantra/od1-plateau-tie @ 42690d7667eb (the tie rule is NOT on origin/main 644a8e9ca; every code reference below is to that branch tip)
changelog:
  - 0.1 (2026-10-23): first draft.
---

# NEAR-STATION-PEAK-INTERVAL — an interval-valued peak instant, value kept, for near-station tie sets

## 0. Scope and limits

Design only. Nothing here is built, applied or merged. Every file the implementation must touch is on the trial-critical list of the job header
(`window_solver.py`, `window_solver_check.py`, `window_sweep.py`, `window_verifier.py`, `window_cert_check.py`, `window_store.py`, `numerical_window_gate.py` and the
migration that widens the shape check). So **this item cannot be implemented while those files are held**; §11 lists them so the implementer knows what to ask to have lifted.
No FROZEN path (§N.2 orchestrator contract) is needed: all changes are inside the window stage's own modules and one additive migration.

## 1. What is being replaced

SR-NEAR-STATION-TIE (option A) made a window whose earliest tie sits in a ≤120 s station zone the **named blank** `tie_isolation_unresolved`:

* builder: `window_solver._station_zone_tie` (ws:716-733) raises `REASON_TIE_ISOLATION` at `_solve` (ws:889-891) when a zone cluster's value is within `TIE + noise` of the maximum;
* checker: `window_solver_check._zone_tie` / `_isolation` (wsc:750-813) returns UNVERIFIED `tie_isolation_unresolved` — INCONCLUSIVE under R-6, demoted at the seal and counted
  toward the 0.5 % cap (`numerical_window_gate.INCONCLUSIVE_REASONS`, nwg:76); the builder's own count is `window_sweep.near_station_tie_report` (wsweep:1357-1372);
* stored: peak, score, evidence, valence **and `objective_value`** all NULL — enforced by CHECK `kgew_unqualified_no_result_ck` (migration 1240, lines 132-135).

The ruling's last sentence is the brief for this item: *"represent the peak instant of a near-station tie set as an interval with the value retained."*
What is thrown away today and is recoverable: **(a)** the maximum itself, which both sides do prove (the zone is not what makes the value uncertain, only the instant);
**(b)** where the earliest tie can lie — a ≤240 s span, instead of nothing.

## 2. Sources and the precision budget

| Source | What it fixes for this design |
|---|---|
| S0 K-2 (`S0_REPORT.md` §2.2, job X-20261021T105440Z-od1-S0-spike) | Swiss longitude is non-monotone next to a station by up to **3.9e-9°** (Mercury; Venus 1.05e-9, Mars 5.9e-10, Jupiter 4.0e-11, Saturn 1.6e-11); spline/Swiss station offset up to **16.7 s**; this exceeds the 1e-10 certificate by 39× (Mercury). Measured comb (test docstring `test_od1_near_station_tie.py`): 34-72 local maxima 0.27-1.3 s apart, all within TIE of the zone's top. |
| PLAN_v2 **G (v2)** (`PLAN_v2.md` line 145, job X-20261021T155211Z-od1-R9-plan) | Promises a number `(M̂, t̂)` with `M ≥ M̂ ≥ M − 1e-10` and `t̂` an actual qualifying extremum to 1 s, **or** no number with a named reason; premise H5 + its detector (`tie_isolation_unresolved`). An interval is a third outcome G (v2) does not yet state — §8 and §12 (I-3) say how it is fitted in without weakening (i)/(ii). |
| **R-3** (`RECONCILIATION.md` line 30, `fast/plan-reviews`) | "No isolation proof. Detect and blank." Close tied extrema (≤ 2×LEAF = 4 s) are *detected*, never resolved. This design keeps R-3 for non-station ties untouched and extends only the *representation* of the station-zone case. |
| **R-6** (`RECONCILIATION.md` line 36) | DISAGREEMENT blocks the seal always; INCONCLUSIVE is demoted to a named blank under a 0.5 % cap, each counted. Decides the checker classes in §6. |
| **Q12 / Q13** (`SOLVER-TOLERANCES`, owner decision, DECISIONS_SURROGATE.jsonl:334) | Q12: peaks exact to the second. Q13: a blank with a named reason, never an unproven number. §8 and §12 (I-3). |
| Constants in code | `TIE = 1e-9`, `EPS_M = 1e-11`, `NEAR_STATION_S = NEAR_END_S = 120`, `NEAR_STATION_NOISE_DEG = NEAR_END_NOISE_DEG = 3.9e-9` (ws:91-104; wsc:80-89); `PEAK_INSTANT_TOLERANCE_S = 1.0` (wsc:82); `ISOLATION_S = 4.0` (wsc:93). |

**Value precision.** In kernel units the zone noise is `δ_F = NEAR_STATION_NOISE_DEG / orb` per record (ws:528; wsc:446), summed over the records of an overlapping zone cluster for the
sum objective, the larger leg for the min objective (`_zone_clusters`, ws:703-713; wsc:788-798). For a window whose zone cluster hosts the tie, the builder's `top = M̂` is a value the curve
**attains** (a read at a piece end), and the zone is read monotone only within `δ_F`, so the true maximum satisfies

    M̂  ≤  M  ≤  M̂ + EPS_M + δ_F          (value bracket, width EPS_M + δ_F)

(a zone that does not host the tie has real values < `M̂ − TIE`, by the hosting predicate itself, and cannot raise `M`). This is **wider than G (v2)'s 1e-10** whenever `δ_F` > ~1e-10 — i.e. at
orb 1.0 for Mercury, Venus and Mars (S0 table) — and the certificate must say so rather than inherit the 1e-10 wording. It is below the stored REAL's own resolution (half a float4 spacing is
2^-27 ≈ 3.7e-9 for values in [0.0625, 0.125) and 3.0e-8 in [0.5, 1)) when `δ_F` ≲ that, so for large values the bracket is invisible after rounding; for small values it is not. The
checker's float4-interval comparison (R-1 a) stays as it is; the bracket is an **additional**, explicit field, not a loosened tolerance.

## 3. Representation

A window whose earliest tie is station-zone-ambiguous carries a **peak interval** — a closed interval of instants `[lo, hi]` that contains the earliest distinct maximum within TIE of the top,
plus the retained value bracket. It is a **set-valued claim "t* ∈ [lo, hi]"**, never a point claim: there is no `peak_instant`, no midpoint, no "representative" instant anywhere (a midpoint
would be an invented number — N.7.6).

**Interval rule v0.1** (deliberately narrow; everything else stays the named blank):

1. Let `top = M̂`, and let the *hosting clusters* be the merged zone clusters `[zl, zh] = ∪ [max(lo, st−120), min(hi, st+120)]` whose value `zone_top ≥ top − TIE − δ_F` (exactly the shipped predicate).
2. **Exactly one** hosting cluster, **and** no tied extremum outside all zones (value ≥ `top − TIE`), **and** no R-3 close pair outside zones ⇒ the interval is that cluster: `lo = zl`, `hi = zh`
   (right end taken at `b − QUANT` when clipped by the half-open window end, as everywhere in the solver).
3. Otherwise (several hosting clusters, or a tied extremum elsewhere, or an R-3 pair) ⇒ **no interval; the shipped blank, unchanged**.

Why the whole cluster and not the hull of the comb's measured maxima: the builder reads a zone by its ends and does not enumerate the comb; whether the first/last comb maximum clears the
threshold `top − TIE` is itself decided at the 1e-9 noise level (and the checker's ±2e-10 grey band, wsc:81), so a comb-hull end is only good to about one comb spacing (0.3-1.3 s), i.e. to
about Q12's own second — not robust. The zone cluster is a closed-form function of station instants, window ends and one constant, which both sides can derive independently. (I-1.)

Why not a union of intervals: it makes every consumer handle a list and every oracle a combinatorial shape, for windows (two hosting stations in one window, or a tie elsewhere as well) that the
campaign has not yet shown to exist. They stay blank and are *counted*, which is what the 0.5 % cap needs anyway. (I-2.)

## 4. Storage — "needs migration number"

No migration number is allocated to this item (`MIGRATION_ALLOCATION.json`, `next_free` 1409 at read time; nothing under this item). **Needs migration number.** Two stages:

### Stage 1 (recommended): enrich the blank, change no typed column

* The window stays exactly what it is today: `qualification.unqualified_reason = 'tie_isolation_unresolved'`; `peak_instant`, `score`, `evidence_for`, `evidence_against`, `objective_value` NULL;
  valence `unqualified`. CHECK `kgew_unqualified_no_result_ck` stays true and untouched; census (`numerical_window_gate.census`, nwg:121) still sees a blank with a reason and no number; the
  INCONCLUSIVE accounting is unchanged.
* New optional member of `qualification`: **`peak_interval`**, a closed JSON object (§7), schema `near_station_peak_interval/1`. Only a tie-blank window may carry it.
* One additive migration, in the 1402 pattern: `CREATE OR REPLACE` of `ka_gochara_window_qualification_ok(jsonb)` to admit the key and a new `ka_gochara_peak_interval_ok(jsonb)` (closed keys,
  types, `lo ≤ hi`, `hi − lo` ≤ a stored cap, `value ≤ value_upper`, the key permitted only when `unqualified_reason = 'tie_isolation_unresolved'`), with 1402's guarded builder EXECUTE grant.
  No row changes; every existing row still satisfies the new body; second application is a no-op; gate refuses when 1240/1402 objects are missing. Applied and **verified applied** in the guarded
  local fixture (§N.4 "surgical migrations, verified"); a migration file is never edited after it has been applied.
* Why not a column now: `peak_instant` is the key that `census` (nwg:121), `serving_reader` (lines 254, 532, 567), the verifier's `GOVERNED_FIELDS` and every `peak_instant IS NOT NULL` reader use as
  "this window has a number". A new typed state would change all of them at once. Stage 1 changes none; it is fail-safe — a reader that has never heard of `peak_interval` still sees the blank.
* The verifier's provenance check compares `qualification` with its own re-derivation **except** `solver_certificate` (wver:603). `peak_interval` joins that exemption and is checked by the
  checker instead (§6) — otherwise every enriched window would read as a provenance mismatch. This is the only verifier-side change.

### Stage 2 (optional, separate ruling): typed promotion

Only if a consumer needs the interval served as data: add `peak_interval tstzrange` (closed bounds) + `objective_value` retained on that state, relax `kgew_unqualified_no_result_ck` for the one
reason, teach `census` a third class ("interval-numbered", neither point-numbered nor blank), `serving_reader`, `GOVERNED_FIELDS`, and the 0.5 % accounting. This changes what "numbered" means and is
adjacent to owner decision Q13 — **owner-level, not surrogate-level** (§12, I-3). Not designed further here.

## 5. Builder semantics (`window_solver`, `window_sweep`)

* `_station_zone_tie` is extended to return, besides the description, the structured finding it already computes: cluster `[zl, zh]`, `zone_top`, `δ_F`, the combine mode, the stations that formed
  the cluster, and how many clusters host. `_solve` applies rule v0.1 (§3): single hosting cluster, no outside tie → blank **with** the interval; else the shipped blank.
* The blank still goes out as `SolveResult(BLANK, …, REASON_TIE_ISOLATION, …)`. Today that result has no `tree`, so `stored_certificate` returns `None` (ws:815) and a tie blank carries *no*
  certificate; the interval object is therefore carried by the result itself (a new optional field), not hung on the piece tree. `window_sweep` copies it into `qualification()` (wsweep:774-784) next to
  `solver_certificate`.
* `value` = `top` (the attained maximum); `value_upper = top + EPS_M + δ_F`.
* Unchanged: the rule fires only after `_prove_max` has proven `top` (so `value` is never a best-found number), the per-window budget (R-6), the order-independence of windows.
* `near_station_tie_report` gains `near_station_tie_interval` (blanks that carry an interval) next to `near_station_tie_blanked` (all tie blanks, interval or not — the name and meaning of the
  existing field do not change). The 0.5 % cap stays on **`near_station_tie_blanked`**, i.e. converting a blank into an enriched blank does not lower the count the TR stop is built on.

## 6. Checker semantics (`window_solver_check`, `window_cert_check`, `window_verifier`; K12)

The checker derives the interval **from its own code and its own constants** (`NEAR_END_S`, `NEAR_END_NOISE_DEG`, its own station finder `_near_cache`), never from the builder or the stored
object. Nothing is imported from `window_solver`; the two constants stay literals, pinned equal by a test that reads source text (the N-3b pattern). `confirm_tie_isolation` (wsc:964) /
`_Engine.probe_isolation` return, besides the description, the checker's own enclosure `E_chk = [lo_c, hi_c]`, `top_c`, `δ_c`.

Comparison of a stored `peak_interval` `I = [lo, hi]`, value `v`, `v_up` with the checker's `E_chk`, `top_c`:

| Situation | Status | Class (R-6) | Code (proposal) |
|---|---|---|---|
| `E_chk` is one cluster and `I` equals it at both ends within `END_TOL_S`; `v` within `δ_c` plus the float4 interval of `top_c`; `v ≤ v_up`, and `v_up` covers the checker's own upper bound `top_c + EPS_M + δ_c` | VERIFIED, `claim_kind = interval` | AGREED | — |
| `I` leaves out part of `E_chk` (unsound: the true tie could lie outside the claim) | REFUTED | DISAGREEMENT | `peak_interval_excludes_earliest_tie` |
| `I` is wider than `E_chk` by more than `END_TOL_S` at either end (the vacuous claim; the analogue of "a blank where the table yields a value") | REFUTED | DISAGREEMENT | `peak_interval_wider_than_rule` |
| Checker finds no hosting zone (the tie is isolated) but an interval is stored | REFUTED | DISAGREEMENT | `peak_interval_where_tie_isolated` |
| Checker finds several hosting clusters, an outside tie or an R-3 pair, but an interval is stored | REFUTED | DISAGREEMENT | `peak_interval_where_rule_does_not_apply` |
| Stored value outside `[top_c − δ_c, top_c + δ_c]` ∪ float4 interval, or `v_up` below the checker's upper bound | REFUTED | DISAGREEMENT | `peak_interval_value_mismatch` |
| Budget exhausted before `E_chk`/`top_c` is settled | UNVERIFIED | INCONCLUSIVE | `verifier_budget_exhausted` (existing) |
| Stored blank **without** an interval, checker says the rule would have produced one | VERIFIED as the shipped blank | AGREED | (not an error: Stage 1 is additive; an un-enriched legacy blank stays valid) |
| Stored **point** peak in/near a zone (legacy number) | unchanged: UNVERIFIED `tie_isolation_unresolved`, or REFUTED `peak_instant_mismatch` outside every zone (shipped B-1, wsc:917-935) | unchanged | — |

* `claim_kind` is a new field of `CheckReport` ("point" | "interval" | "blank"); `satisfies_gate` (wsc:974) is unchanged and `window_cert_check.classify` (wcc:89) maps it as before. A gate that
  counts point-numbered windows must read `claim_kind`, so an interval VERIFIED can never be mistaken for a verified point (N.8: the signal measures the claim it asserts).
* `END_TOL_S` — **not Q12's 1 s by assumption.** The interval ends are `station ± 120 s`, so they move one-for-one with the station instant. The builder lists Swiss stations from its sweep; the
  checker finds its own (centred-difference speed with `VEL_H_S = 600 s`, wsc:90). S0 measured spline-vs-Swiss offsets (up to 16.7 s) but **not Swiss-vs-Swiss between two derivations**, which
  is what these ends compare. If the two derivations differ by more than 1 s the ends cannot agree to Q12. **Measurement required in the implementation item** (spec: for every Mercury, Venus
  and Jupiter Swiss station that has a zone inside any century-build window, locate it by the builder's method and by the checker's method on the pinned corpus
  `/Users/Dev/kalayantra/ephe`; report the max |Δ|). `END_TOL_S` = that max rounded up, **ruled by the surrogate**, with the rule that over-width is tolerated up to it and under-width
  (soundness) is tolerated by nothing. Until measured it is `[EXTERNAL_COMPUTATION_REQUIRED]` (B.10) — this note invents no value. (I-4.)

## 7. Certificate fields — `qualification.peak_interval` (`near_station_peak_interval/1`, closed object)

| Field | Type | Meaning |
|---|---|---|
| `schema` | string | `near_station_peak_interval/1` |
| `rule` | string | `SR-NEAR-STATION-TIE` |
| `objective` | string | `sum_of_group_max` \| `min_of_group_max` |
| `t0` | ISO string | origin of the second-offsets, as in `solver_certificate` |
| `lo_s`, `hi_s` | number | interval ends, seconds from `t0` (float, as the solver works) |
| `lo`, `hi` | ISO strings | the same, µs-quantised; `hi` is the closed end (`b − QUANT` when clipped by the half-open window end) |
| `clipped_lo`, `clipped_hi` | boolean | the end is the window's, not the zone's |
| `stations` | array of `{body, t_s}` | the listed stations whose zones merged into the cluster |
| `value` | number | `M̂`, the attained, proven maximum |
| `value_upper` | number | `M̂ + EPS_M + δ_F` |
| `value_width` | number | `EPS_M + δ_F` (stated, so a reader never takes 1e-10) |
| `zone_top` | number | the cluster's value as read (hosting predicate input) |
| `tie_margin` | number | `zone_top − (M̂ − TIE − δ_F)` ≥ 0; how far inside the hosting predicate the cluster is (0 ⇒ borderline) |
| `limits` | object | `TIE`, `EPS_M`, `NEAR_STATION_S`, `NEAR_STATION_NOISE_DEG`, `noise_F`, `combine` ("sum"\|"max"), `END_TOL_S`, `PEAK_INSTANT_TOLERANCE_S` — the constants the claim assumes, as `solver_certificate.limits` does |
| `claim` | string | the literal `earliest_tie ∈ [lo, hi]; not a point claim` |

Deliberately absent: any `peak_instant`, `mid`, `score`, `evidence_*`, `valence`. Those are functions of the instant; in Stage 1 they stay NULL. Whether they can be carried as ranges (constant over
`[lo, hi]` within float4 ⇒ number; otherwise NULL with a reason) is a Stage 2 question (§12, I-5).

## 8. Q12 interaction — not relaxed

* The point claim keeps Q12 (exact to the second) wherever it is made: a stored **point** is checked as before, including shipped B-1 (a point outside every zone and at no qualifying extremum is
  still REFUTED `peak_instant_mismatch`).
* The interval is **not** a point with a loose tolerance. It is a different claim type with its own detector, whose ends are checked to `END_TOL_S` (§6) and whose width is **not a free
  parameter**: it is the closed-form zone cluster, so a builder cannot widen it to rescue a hard window (that is `peak_interval_wider_than_rule`, a DISAGREEMENT).
* It can never turn a Q12 failure into a pass: an interval is produced only where the ruling already declared the point undecidable. A window the checker finds outside that condition and carrying an
  interval is REFUTED, not tolerated.
* G (v2) wording to add at the next PLAN revision (for the surrogate; not edited here): *"(iii) for a window whose earliest tie lies in a station zone: no point; a named blank
  `tie_isolation_unresolved`, optionally carrying an enclosure `[lo, hi]` of the earliest tie and a value bracket `M̂ ≤ M ≤ M̂ + EPS_M + δ_F`; it never returns a best-found value."* Clauses (i)/(ii) are untouched.
* Q13 (blank with a named reason, never an unproven number): Stage 1 keeps the window a blank with its reason, and the value in the interval is *proven* (bracketed), not best-found. Stage 2, which makes
  it a typed state, is the step to put to the owner.

## 9. Cap and reporting

* TR report: `near_station_tie_blanked` (unchanged meaning, per class, 0.5 % integer cap stays as the stop condition) and the new `near_station_tie_interval` (how many of them carry an interval),
  plus the count of tie blanks that carry none because rule v0.1 did not apply (several clusters / outside tie / R-3) — the last number says whether v0.1 is too narrow.
* Checker side: nothing changes in `INCONCLUSIVE_REASONS`; an enriched blank is demoted exactly like a bare one.

## 10. Oracles — one distinct production claim each, one planted reversion each (D-OWNER-TESTS-20261016; reviewer re-enumerates)

Real-sky cases are the six measured Venus/Mercury windows (the test file's case list; "case 3" = Venus 2029-12-16, window ending 3 ms after the station) on the pinned corpus; analytic worlds are closed-form.

| # | Claim | Oracle (source) | Planted reversion that must FAIL |
|---|---|---|---|
| PI-1 | Single hosting cluster ⇒ interval = the cluster `[max(lo, st−120), min(hi, st+120)]` | case 3: expected ends from S0/N-3b zone definition, computed in the test from the station instant | return the old lone candidate as a point-width interval |
| PI-2 | Every tied comb maximum the real curve has (34-72 on the measured cases) lies inside the interval | enumerate the real Swiss maxima ≥ `top − TIE` on each of the six cases (S0 K-2 comb) | cut the interval at the station (drop one side of the zone) |
| PI-3 | Value bracket `M̂ ≤ M ≤ M̂ + EPS_M + δ_F` is true | analytic world: tent + planted ripple of amplitude `δ_F` with known sup (closed form) | drop `δ_F` from `value_upper` |
| PI-4 | A near-station window with ONE isolated maximum numbers as a point and carries no interval (SR text; NST-3) | Venus level 1e-4° short of the station (NST-3 world) | emit an interval for every zone |
| PI-5 | Several hosting clusters / an outside tie / an R-3 pair ⇒ no interval, shipped blank | analytic world with two stations both within TIE+δ of the top | take the hull of the clusters |
| PI-6 | Checker derives its own enclosure and AGREES with the builder on the six cases within `END_TOL_S` | six cases, both sides run | checker takes `NEAR_END_S/2` (ends disagree ⇒ must not be VERIFIED) |
| PI-7 | Checker REFUTES an interval that excludes part of `E_chk` | stored interval shifted 300 s | delete the containment test |
| PI-8 | Checker REFUTES an interval wider than the rule (e.g. the whole window) | stored interval = window | delete the width test |
| PI-9 | Checker REFUTES an interval stored where the tie is isolated (NST-3 world) | PI-4 world with an interval planted in the row | treat any stored interval as acceptable |
| PI-10 | Q12 untouched: a stored point outside every zone and at no extremum is still REFUTED `peak_instant_mismatch` after the change; a point inside a zone is still UNVERIFIED, never VERIFIED | Venus case 3 with instant 200.003 s before the end (the shipped B-1 oracle) | let a present interval upgrade a point to VERIFIED |
| PI-11 | A VERIFIED interval is distinguishable from a VERIFIED point (`claim_kind`) | a gate that counts point-numbered windows must not count it | omit `claim_kind` (default "point") |
| PI-12 | Storage: the shape function admits the closed object and only on a `tie_isolation_unresolved` blank; refuses an unknown member, `lo > hi`, `value > value_upper`, and the object on a numbered window; typed columns stay NULL under `kgew_unqualified_no_result_ck` | guarded local fixture (127.0.0.1:55433), migration applied then verified applied | admit any key (unknown member accepted) |
| PI-13 | Verifier provenance check exempts `peak_interval` but a tampered interval is still caught by the checker | stored window with `peak_interval`; then tampered ends | drop the exemption (every enriched window reads as a provenance mismatch) |
| PI-14 | Reporting: `near_station_tie_blanked` keeps counting every tie blank (cap unchanged), `near_station_tie_interval` counts enriched ones | drafts with and without interval | count only enriched blanks toward the cap |
| PI-15 | K12: checker imports nothing of the builder and vice-versa; the two noise constants and `END_TOL_S` are literals pinned equal by source text | the N-3b source-text test | import the builder's constant into the checker |

Not claimed by any oracle, on purpose: that a *midpoint* or *representative* instant is anything (there isn't one); anything about windows the rule does not cover.

## 11. Migration path from the current named blank

0. **Now:** `tie_isolation_unresolved` is a bare blank (od1-plateau-tie; not yet on main). Nothing in this item is needed for the trial.
1. **Prerequisites:** od1-plateau-tie merged; trial-critical files released by the wrap (job header HARD LIMITS); a migration number allocated to this item; the `END_TOL_S` measurement (§6) done and ruled.
2. **Stage 1:** builder + checker + verifier exemption + report field + one additive migration, in one PR, reviewed with the claim table above. Old rows and old readers are unaffected; a
   rollback is "stop writing the key" (existing enriched rows remain valid) or, for a full revert, the 1402 recipe (re-apply the previous function body after stripping the key).
   Re-build of the century is **not** required for correctness: un-enriched legacy blanks stay valid (§6 row 8); enrichment appears when a grain is rebuilt.
3. **Stage 2 (only on demand):** typed promotion, §4. Needs its own design pass and an owner-level decision (Q13).

Files Stage 1 touches (all currently held): `window_solver.py`, `window_solver_check.py`, `window_sweep.py`, `window_verifier.py`, `window_cert_check.py` (class map only), `numerical_window_gate.py`
(no change expected; confirm by test PI-12/PI-14), new migration (number to be allocated), tests under `tests/l3/gochara/`. Not touched: `window_store.py` (the `qualification` JSON is already written whole),
`record_store.py`, `ka_gochara_v5.py`, `input_vector*.py`, `fleet/trial_harness/` (a later harness edit may read the new report field — separate item), golden pins (a pin that includes a tie blank's
`qualification` would be re-derived by the implementer — to be checked, not assumed).

## 12. Interpretations and open points for the surrogate

* **I-1** Interval = the whole zone cluster, not the hull of measured comb maxima. Alternative: comb hull — tighter, but its ends are only good to ~1 comb spacing and need the grey-band logic.
* **I-2** v0.1 covers exactly one hosting cluster; everything else stays blank. Alternative: a list of intervals (more windows enriched, more consumer/oracle surface).
* **I-3** Stage 1 keeps the window a blank at the typed-column level, with the value in provenance. Alternative: the typed state now (Stage 2 straight away) — larger change across gate, serving and verifier, and touches Q13 (an owner decision).
* **I-4** `END_TOL_S` is measured, not assumed to be 1 s; over-width tolerated up to it, under-width not at all. Alternative: assume Q12's 1 s — fails if the two station derivations differ by more.
* **I-5** Score / evidence / valence at the peak stay NULL in Stage 1. Alternative: carry them as ranges over `[lo, hi]` where constant within float4 (needs a range evaluator on the existing piece structure).
* **I-6** One noise constant (3.9e-9, Mercury's) is used for every body, as shipped. S0's per-body table (Venus 1.05e-9 … Saturn 1.6e-11) would give a tighter `value_width` and a smaller hosting predicate (fewer enriched/blanked windows), but changes shipped behaviour and the cap count — a separate ruling, not part of this item.
* **O-1 (observation, no change proposed)** The shipped zone rule blanks whenever a zone can host a tie, even if a certain isolated tie lies *before* the zone (then the earliest tie is that isolated point and cannot be in the zone). The ruling's text ("a tie set that lies inside a ≤120 s station zone") is narrower than the code (ws:716-733, wsc:800-813). Numbering those windows as points would be a rule change to SR-NEAR-STATION-TIE, so it is left to the surrogate.
* **O-2** The doctrine sources are outside the repository (`S0_REPORT.md`, `PLAN_v2.md`, `RECONCILIATION.md`, `ANSWERS.md` under `fast/…`); the implementer should cite them by those paths or have the relevant paragraphs copied into the PR.
