---
artifact: EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING
version: "1.2"
status: "SUPERSEDED by v1.3 (Codex round 8 R8-8: the two-extremes rule is unsound at the zero boundary and across tie-group bridges; the freeze ordering was circular) — do not pre-register from this version"
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 — corrected per Codex round 7 [10] (steward M20261002T015923-4738 adopts the closing text)
amends: "EVALUATION_PROTOCOL_v2_3 §4 (window identity, ranking) — adds the stored-field mapping, the NULL policy and the unknown-competitor rule the protocol left silent; changes NO existing rule, threshold, floor, denominator rule or '3.0' figure"
---

# Addendum — the ranking intensity `si`, and what an unknown intensity does

## 1. Mapping (unchanged from v1.0/v1.1)
**`si := evidence_for`** (the stored `evidence_for` of the merged candidate's highest member, ties per §4.2). `score` is **not** the ranking key — it is **constrained** by the schema CHECK to [0,1] (1156 `kgew_score_unit_interval_ck`) and many exact-contact windows tie at the ceiling (the plateau shape §8.3 and v3.0's defect #24/E5 exist to catch); `evidence_for` is the §2.1 per-channel sum over independent roots, finite ≥ 0 and **not bounded above**.
**Provenance, stated plainly.** Chosen **after** the '3.0' baseline was seen and **before any candidate output is inspected**: a pre-registration, **not blind validation** (the protocol already discloses that its authors have seen the LEL). The absence of '4.1'/'5.0' result files supports only a repository observation.

## 2. Three concepts kept apart
| concept | what it is | where defined |
|---|---|---|
| **admission** | a window exists because its prerequisite-satisfied support exists | spec §2.3 / AM-17 — independent of any score |
| **computation coverage** | which (class, year) cells the engine computed | P §6.5 — coverage, not score qualification |
| **score qualification** | whether a window's `evidence_for` (and peak) is a *known* number | spec §2.1; Codex R1 — `NULL` = unqualified, never 0 |

## 3. NULL policy (frozen before any candidate inspection)
* Admitted supports **remain in the admission union and in T-FP's admitted-day burden** regardless of score qualification; unknown necessary-predicate admission is **not** treated as admitted.
* **Known zero is a numeric value. NULL is never a number** — not 0, not the minimum, not the mean.
* **Merged candidate whose own highest-`si` representative cannot be determined** (a contributing intensity is unknown): do not invent a numeric `si` or peak; the candidate's own ranking/timing result is **unqualified**.

## 4. THE UNKNOWN-COMPETITOR RULE (new in v1.2 — closing text, Codex round 7 [10])
> **Score qualification does not remove admitted merged candidates from the frozen candidate set or from N.** If an unknown competitor can alter a relevant representative, rank, timing choice or plateau-validity conclusion, that result is **unqualified** and **cannot establish a passing endpoint**, **unless the conclusion is proved for every admissible value of the unknown inputs.**

**Operational form (what the adapter implements).**
1. **Candidate set and N are fixed by admission only.** A candidate with an unknown `si` is a member of the set and counted in N for **every** event in its class-year; it is never dropped, never zero-filled, never replaced by a median.
2. **Admissible values of an unknown `si`:** any finite real **≥ 0** (the schema bound on `evidence_for`; nothing above). It is *not* assumed to be below any known value.
3. **Rank interval.** For a candidate with known `si = a` and `k` unknown competitors, the rank under the percentile rule of §4.3/§4.4 (`percentile = 100·(r−1)/N`, ties average) is an **interval**: best case = every unknown competitor strictly below `a`; worst case = every unknown competitor strictly above `a`. A single numeric percentile is reported **only if the two bounds coincide** (`k = 0`, or no admissible assignment changes the rank — e.g. `a` is already unreachable from above because every unknown competitor is provably ≤ `a`, which the schema never provides).
4. **Endpoint conclusion.** Each endpoint (T-rank median ≤ 25; T-time; the §8.3 plateau test; the validity floor) is evaluated at **both extreme assignments** (all unknowns best-case / all unknowns worst-case). The conclusion is **qualified only if both give the same verdict**; otherwise it is `unqualified`, **cannot establish a passing endpoint**, and the **events and the affected candidates are reported by identity**. For plateau detection the two extremes are "every unknown equals the modal known value" and "every unknown differs from it".
5. **Representative / timing.** A merged candidate whose representative could be changed by an unknown member (an unknown member could exceed the known maximum, or tie it earlier) has an unqualified peak date and `si`.
6. **Nothing is relaxed.** The §6.3 validity floor (≥ floor(32/2)+1 eligible events), every denominator rule (§6.5 C3, the worst-rank convention for eligible misses), the `1e-9` tie tolerance and every threshold are unchanged; an unqualified result reduces eligibility, it never relaxes a floor.

### Worked case (Codex's counterexample, as arithmetic)
One fixed candidate set, class c, event e's year:

| candidate | `si` |
|---|---|
| matched (the one overlapping e's scored span) | **2** |
| other known candidates | 1, 0 |
| two further **admitted** candidates | NULL, NULL |

* **v1.1's wrong reading** (drop the unknowns): N = 3, matched ranks 1 → percentile **100·(1−1)/3 = 0**, "qualified".
* **v1.2:** N = **5** (the unknowns stay). Best case (both unknowns < 2): rank 1 → percentile **0**. Worst case (both > 2): rank 3 → percentile **100·(3−1)/5 = 40**. The interval is **[0, 40]**. The matched event's percentile is **not a number**; against the `≤ 25` median bar the verdict at the two extremes can differ, so — unless the median conclusion is the same at both extremes over all events — the T-rank endpoint is `unqualified` and cannot pass. (Removing the unknowns would also have changed N for every *other* event in the class-year.)

## 5. FREEZE RECORD — the completed freeze, not a list of fields
Measurement is **blocked** until a file `measurement/FREEZE_RECORD_<run_id>.json` exists, is committed, and **its sha256 is recorded in a commit made before the first candidate extract is generated or inspected**. It must carry every item below with an **actual value** (a hash, a commit id, a constant) — never "see code".

| item | state today |
|---|---|
| AM-17 window/peak rules (components; P4 max–min objective; `act_g` = max over the agent's live admitted records; per-root-reduced `evidence_for` objective for other paths; earliest attained maximum; NULL peak when unqualified; peak-tie `1e-9`; separate storage-comparison tolerance) | text frozen in amendments draft **v0.15** (hash recorded at freeze) |
| qualification policy (this addendum §3–§4) | this file's sha256 recorded at freeze |
| selected registry versions + orb state (ND-ORB-ADMISSION / ND-ORB-SCALE, or "unqualified points") | **to be written at freeze** |
| UTC→IST conversion; merge implementation; stored-value precision | **to be written at freeze** (adapter commit) |
| candidate-set construction | **to be written at freeze** (adapter commit) |
| **scorer commit** and **adapter commit** (candidate generations) | **do not exist yet — written at freeze; no measurement before** |
| '3.0' scorer `rerun_3_0_v2_3_scorer.py` | sha256 `4456efa548d8551faa66c54d09c4cc0721fed19104a10e3ce6c282b59a846e71` (already frozen) |
| event registry `event_registry_v2_3.json` | sha256 `23633a244c97275f9005983e61f2243919d626088e560101f240dce3b176edee` |
| random controls `random_controls_v1_3.json` | sha256 `eea40fe8ba743a15291c8ec885b1f9dc0c5591a03ebf8bfb70cbefe414f6cb94` |
| '3.0' baseline extract `baseline_3_0_extract_v1_0.json` | sha256 `70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff` |
| protocol v2.3 / specs v1.4 / oracles v1.4 | sha256 `a8353dc48563e08710f1fc6815ace2f15b7e9db5eec5d4ebea1e6dde1120514e` / `d5097ca18a721d8005cab593f3c3865227d22ff1435b8adc9973275d3f786a47` / `19951b06ce672ac4cff82d74fb6c7bb7babe4315582ec1c142a0a7871752c277` (D-SPECS/D-PROTO decisions) |
| candidate **extract hashes** (per generation) | **written at freeze, over the extract produced by the frozen adapter, before inspection** |
| cohort, thresholds, controls, rerun policy | as in protocol v2.3 (unchanged), restated in the record |

A change to any frozen item after a candidate result has been inspected is a **protocol violation** and must be disclosed as such.

## 6. What it does not do
It changes no endpoint, bar, tolerance, candidate rule or '3.0' figure (the '3.0' re-run uses its own `si`, unchanged). If a later review prefers `score`, that is a new addendum dated before the run it governs.
