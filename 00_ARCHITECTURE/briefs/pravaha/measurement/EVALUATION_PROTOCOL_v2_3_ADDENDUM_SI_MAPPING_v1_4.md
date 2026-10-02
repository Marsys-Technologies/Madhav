---
artifact: EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING
version: "1.4"
status: "PRE-REGISTRATION — declared before any '4.1' or '5.0' candidate output is inspected; supersedes v1.3, which is NOT edited (its sha256 stays valid for every document that cites it). v1.4 = v1.3 with ONE addition: §1a (the generation-'4.1' mapping). Every other word, rule, worked case and the §5 freeze are v1.3's, unchanged; references to v1.3 for the governed '5.x' rules remain correct verbatim."
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 — steward M20261002T042015-7bff answer (3)
amends: "EVALUATION_PROTOCOL_v2_3 §4 (window identity, ranking) — v1.3's stored-field mapping for governed '5.x' PLUS the stored-field mapping for the legacy-kernel '4.1' candidate; changes NO existing rule, threshold, floor, denominator rule or '3.0' figure"
---


# Addendum — the ranking intensity `si`, and what an unknown intensity does

## 1. Mapping (unchanged since v1.0)
**`si := evidence_for`** (the stored `evidence_for` of the merged candidate's highest member, ties per §4.2). `score` is **not** the ranking key — it is constrained by the schema CHECK to [0,1] and many exact-contact windows tie at the ceiling (the plateau shape §8.3 exists to catch); `evidence_for` is the §2.1 per-channel sum over independent roots, finite ≥ 0 and not bounded above.
**Provenance, stated plainly.** Chosen **after** the '3.0' baseline was seen and **before any candidate output is inspected**: a pre-registration, **not blind validation**.

## 1a. Generation `'4.1'` — its OWN mapping (added in v1.4; pre-registered before any `'4.1'` output exists)
**`'4.1'` (legacy-kernel chain; table `kala_gochara_windows`): `si := raw_intensity`, exactly as stored.** No absolute value, no polarity transform, no per-class sign handling, no other column.
**Why this and not `signed_intensity`.** Protocol §4.5 requires `si` to be stored **non-negative for every class** ("most adverse first" and "most gainful first" are both `si` descending) and rejects any raw row with `si < 0`. The 4.x writer (`step06b_windows_projection.py`, the row builder) stores `signed_intensity = raw_intensity × (−1 if is_adverse else +1)` — **negative on every adverse window**. Extracting `signed_intensity` would make the §4.5 adapter stop on the first adverse window; negating it back would be an unstated transform. `raw_intensity` is the unsigned magnitude the convention assumes (`NUMERIC NOT NULL`, the writer's `lambda_raw`).
**Like-for-like with `'3.0'`.** The pinned `'3.0'` extract's `si` was `signed_intensity`; in generation `'3.0'` that column equals `raw_intensity` on **all 914 rows**, none negative, all 330 adverse rows positive (read-only production check 2026-10-02; `3.0|914|914|0|330|0|0` = rows, signed=raw, signed<0, adverse, adverse∧signed<0, raw<0). So `raw_intensity` is the **same quantity in both generations**, and the `'3.0'` figures do not move under this mapping (re-dumped with `si := raw_intensity` and re-scored: identical, see `STAGE1_FREEZE_PREP_4_1_v1_0.md`).
**Enforced, not asserted.** The extract command stops (`INPUT_REJECTED`) if any row has `|signed_intensity| ≠ raw_intensity` or `raw_intensity < 0`; the scorer's §4.5 adapter additionally rejects any negative or non-finite raw `si`.
**Unknown competitors.** `raw_intensity` is `NOT NULL`, so a `'4.1'` extract can contain **no unknown `si`**: §4's machinery is not exercised by `'4.1'` (it is exercised on synthetic extracts and reserved for governed `'5.x'`); the run asserts `unknown_si_rows = 0` and discloses any other value.
**Provenance, stated plainly.** Chosen **after** the `'3.0'` baseline was seen and **before any `'4.1'` output exists** — derived from the writer's code, the table definition and the `'3.0'` data only; no `'4.1'` row was read. A pre-registration, **not blind validation**. It changes no endpoint, bar, tolerance or candidate rule. The §1 `si := evidence_for` mapping above is for governed `'5.x'` eval-window rows and is untouched.

## 2. Three concepts kept apart
| concept | what it is | where defined |
|---|---|---|
| **admission** | a window exists because its prerequisite-satisfied support exists | spec §2.3 / AM-17, AM-21 — independent of any score |
| **computation coverage** | which (class, year) cells the engine computed | P §6.5 |
| **score qualification** | whether a window's `evidence_for` (and peak) is a *known* number | spec §2.1; `NULL` = unqualified, never 0 |

## 3. NULL policy (frozen before any candidate inspection) — unchanged
Admitted supports stay in the admission union and T-FP burden regardless of qualification; unknown necessary-predicate admission is not admitted. Known zero is a numeric value; NULL is never a number. A merged candidate whose own representative cannot be determined has an unqualified ranking/timing result.

## 4. THE UNKNOWN-COMPETITOR RULE (governing text unchanged from v1.2; the OPERATIONAL form is replaced)
> **Score qualification does not remove admitted merged candidates from the frozen candidate set or from N.** If an unknown competitor can alter a relevant representative, rank, timing choice or plateau-validity conclusion, that result is **unqualified** and cannot establish a passing endpoint, **unless the conclusion is proved for every admissible value of the unknown inputs.**

**Operational form (replaces v1.2 §4 items 3–4; the claim that two selected assignments — "all unknowns below / all unknowns above" — bound every endpoint is WITHDRAWN).**
1. Candidate set and N are fixed by admission only; an unknown candidate is a member and counted in N for every event in its class-year; never dropped, zero-filled or imputed.
2. **Admissible values of an unknown `si`: every finite real ≥ 0** — **including the boundary 0** and every value that **ties with or bridges** known values under the protocol's tolerance (`|a−b| < 1e-9`, **adjacent-gap grouping**: a chain of values each within tolerance of its neighbour is one group, so an unknown can **bridge two groups** into one).
3. **Bounds range over ALL admissible assignments**, with **average ranks for ties** and `percentile = 100·(r−1)/N`. An unknown can sit *below* a matched candidate only if the matched value exceeds the tolerance above 0; at `a = 0` it can only tie or exceed.
4. **Checking selected assignments qualifies an endpoint only where a proof establishes that those assignments bound that endpoint.** Where no proof exists the adapter **enumerates the placement classes** (the model `measurement/unknown_competitor_bounds_model.py`: per unknown — the boundary 0, "above everything", every known value, points within and just outside tolerance of each known value, and every gap midpoint) and qualifies the endpoint only if its verdict is the **same for every attainable assignment**. Otherwise the endpoint is **unqualified**, cannot establish a pass, and the affected events and candidates are reported by identity.
5. Representative / timing: a merged candidate whose representative could be changed by an unknown member has an unqualified peak date and `si`.
6. Nothing is relaxed: the §6.3 validity floor, every denominator rule (§6.5 C3, the worst-rank convention for eligible misses), the `1e-9` tolerance and every threshold are unchanged; unqualified results reduce eligibility, they never relax a floor.

### Worked cases (arithmetic reproduced by `unknown_competitor_bounds_model.py`)
**(a) Codex round 7 — matched above the unknowns' reach.** Matched `si = 2`; known others `1, 0`; two admitted candidates NULL. N = 5. Both unknown below 2 ⇒ rank 1 ⇒ percentile **0**; both above ⇒ rank 3 ⇒ **40**. Range **[0, 40]** — not the single value 0 that dropping the unknowns (N = 3) would give.
**(b) Codex round 8 — the zero boundary.** Matched `si = 0`; known others `2, 1`; two admitted candidates NULL. N = 5. The unknowns cannot be strictly below 0. Both strictly above ⇒ rank 5 ⇒ percentile **80**; both tied with the matched (value 0) ⇒ a three-way tie at positions 3–5 ⇒ average rank 4 ⇒ **60**; one tied, one above ⇒ average rank 4.5 ⇒ **70**. Range **[60, 80]**. (The v1.2 "best case = strictly below" would have claimed 40.)
**(c) Codex round 8 — a tie-group bridge.** Known `0, 0, 1.5e-9, 1.5e-9, 1, 2, 3`; one admitted candidate NULL; N = 8. Unknown = 0 ⇒ largest tie group 3/8; unknown far from every known value ⇒ 2/8 — **both look non-void**. Unknown = 0.75e-9 ⇒ the adjacent gaps are < 1e-9, so `0, 0, 0.75e-9, 1.5e-9, 1.5e-9` chain into **one group of 5 ⇒ 5/8 = 62.5 % ≥ 50 % ⇒ void under §8.3**. The plateau verdict is **not invariant** over admissible values ⇒ **unqualified**. (Checking only "0" and "far" would have qualified it.)

## 5. FREEZE — two stages (the v1.2 single record was circular: a file cannot hold extract hashes before the extracts exist)
**Stage 1 — configuration freeze (commit BEFORE any extract is generated).** A committed file `measurement/FREEZE_STAGE1_<run_id>.json` carrying **actual values**: the amendments draft version **and its sha256** (AM-17/AM-21/AM-22 text as then current — the previous "v0.15" pointer was stale); this addendum's sha256; selected registry versions and the orb state (ND-ORB-ADMISSION / ND-ORB-SCALE as ruled or "unqualified points"); UTC→IST conversion; merge implementation; stored-value precision; the `1e-9` tolerance; candidate-set construction; **the adapter commit id and the scorer commit id** and the **extract-generation command** (so the extract is reproducible from the freeze); cohort; thresholds; controls; rerun policy; and the sha256 of every pre-extract input already frozen — event registry `23633a244c97275f9005983e61f2243919d626088e560101f240dce3b176edee`, random controls `eea40fe8ba743a15291c8ec885b1f9dc0c5591a03ebf8bfb70cbefe414f6cb94`, '3.0' baseline extract `70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff`, '3.0' scorer `rerun_3_0_v2_3_scorer.py` `4456efa548d8551faa66c54d09c4cc0721fed19104a10e3ce6c282b59a846e71`, protocol v2.3 `a8353dc48563e08710f1fc6815ace2f15b7e9db5eec5d4ebea1e6dde1120514e`, specs v1.4 `d5097ca18a721d8005cab593f3c3865227d22ff1435b8adc9973275d3f786a47`, oracles v1.4 `19951b06ce672ac4cff82d74fb6c7bb7babe4315582ec1c142a0a7871752c277`.
**Stage 2 — extract seal (before inspection).** Generate the candidate extracts **with the Stage-1 adapter**; write their sha256 into `measurement/FREEZE_STAGE2_<run_id>.json` and commit it **before any extract is opened for inspection**; the scorer **verifies** each extract hash against Stage 2 and refuses a mismatch or a missing record. No measurement without both stages.
A change to any frozen item after a candidate result has been inspected is a **protocol violation** and must be disclosed as such. **Status today:** no Stage-1 file exists (the adapter and scorer for candidate generations do not exist yet); measurement is **blocked**.

## 6. What it does not do
It changes no endpoint, bar, tolerance, candidate rule or '3.0' figure. If a later review prefers `score`, that is a new addendum dated before the run it governs.
