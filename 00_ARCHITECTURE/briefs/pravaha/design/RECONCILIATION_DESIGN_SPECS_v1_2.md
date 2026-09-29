---
artifact: RECONCILIATION_DESIGN_SPECS
canonical_id: RECONCILIATION_DESIGN_SPECS
version: "1.2"
status: CURRENT — B3.8b reconciliation of the round-3 review
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
supersedes: "design/RECONCILIATION_DESIGN_SPECS_v1_1.md (round-2; retained as history)"
review_reconciled: "design/reviews/ASTRA_REVIEW_DESIGN_SPECS_v1_2.md (sha256 c980fc8a7cf8c7cd17ed04ee811d25c6e3ccf5c2c837b132f5bbf79da05bba82 — Codex round 3: REWORK / REWORK; 3 closed, 12 partly closed, 4 new blocking)"
artifacts_reworked: "design/GOCHARA_DESIGN_SPECS_v1_3.md (sha256 727d174a…) + design/GOCHARA_TEST_ORACLES_v1_3.json (sha256 5a7258ad…) — contract side; protocol side deferred to B4.5 (registry/protocol/scorer/baseline v2.2) per the native's split ruling"
disclosure: "No '4.1' or other candidate is scored; D-PROTO gates scoring only (native, 2026-09-30). A reviewed file is never edited — all changes are in the next version."
---

# Reconciliation v1.2 — round-3 review (B3.8b)

Every finding of `ASTRA_REVIEW_DESIGN_SPECS_v1_2.md` dispositioned: **accepted → closed in
v1.3 (contract)** or **accepted → deferred to B4.5 (protocol, D-PROTO track)**. Nothing is
refuted; two statements of mine from earlier rounds are corrected (§B38-F1 below, and the
dedup narrative already flagged for B4.5).

## 1. The three CLOSED findings — confirmed

| finding | disposition |
|---|---|
| R2-M02 (T-FP estimand) | Confirmed closed in v2.1; carried forward unchanged into v2.2. |
| NK-1 (omitted event/arithmetic) | Confirmed closed in v2.1; carried forward. |
| NK-2 (distinguish recurring contacts) | Confirmed closed for the same-set case; its residual (extension stability, R2-S02) is now closed in v1.3 §6.1 + O-RX-1 (partition-extension case added). |

## 2. The twelve PARTLY CLOSED findings

### Contract side — closed in v1.3

| finding | round-3 residual | disposition in v1.3 |
|---|---|---|
| **R2-S01** typed contract | record_id hash excluded generation/contact_id; unversioned PKs/FKs; `temporal_support=[]` ambiguous; no source-fact lineage | **Closed.** §1.1: `record_id` natural key now includes `generation` + `contact_id`; §2.1: composite `(path_id, rule_version)` / `(predicate_id, rule_version)` / `(factor_id, rule_version)` PKs with version-bound FKs; `temporal_support` is a tagged state `{uncomputed \| computed_empty \| computed}` with unknown-admission behaviour stated; new `source_fact_ids` lineage field (with `fixture=true` escape for synthetic rows). |
| **R2-S02** episode identity | no fixed ordinal origin/domain; partition extension could renumber published contacts; no canonical serialization or extension fixture | **Closed.** §6.1: ordinal domain pinned in `convention_id`; ordinals over the full-domain ordered crossing set; partition extension inside the domain appends only; published contact ids immutable (never renumbered/reused; corrections mint new ids with supersedes edges); canonical serialization `body\|relation_kind\|canonical_target\|convention_id\|ordinal`. O-RX-1: identity bytes printed + partition-extension case (appends as ordinal 4; ids 1–3 unchanged). |
| **R2-S03** scoring algebra / P4 | factor functions, ranges/units, evidence accumulation, shared-root aggregation, exhaustive sets absent; O-RP-2 same-target requirement conflicted with O-RP-3 | **Closed.** §2.1: factor fields now carry `function`/`range`/`units`; evidence = sum over records deduped by `contact_id` per path (shared-root handling); exhaustive agent/class/target sets stated. P4: ONE rule (R3-S02 below). The father target-set scope is the §2.2 truth-table set (9th house + lord Jupiter; 2/7/8 from the 9th named as the māraka *testimony* set). |
| **R2-S04** AV comparator / availability / G-10 | no nonzero BAV comparator or explicit unresolved state; table recorded availability, not a missing-input matrix; BAV/SAV contradiction survived | **Closed.** §2.2 P5: full missing-input matrix — each operand gates exactly its own form; whole-build-absent is the only cross-form case (contradiction removed; O-BP-2 case C tests SAV-missing ⇒ P5b alone). P5a's nonzero comparator is explicitly **`unresolved`** (no cited threshold exists); scored output = known-zero detection only. |
| **R2-S05** scored residence vs testimony | "chart's ADVERSE classes" unnamed; testimony test had no concrete baseline / no admission assertion | **Closed.** O-RP-5a asserts on the named class **`illness_acute`**; its `then` adds "testimony-role admission of the same interval is unchanged". O-RP-5b's concrete baseline is the bit-identical score with vs without the testimony row (scored-baseline equality asserted). |
| **R2-S06** complete discriminating fixtures | placeholders remained; PD expectations absent; generators not complete; O-SM-1 Δ undefined; labels overstated completeness | **Closed by policy, not by expansion** (native's amendment 5: do NOT make every fixture literal). The four named wrongs are fixed (O-VI-2 half-open boundary day; O-SM-1 clean parabola with per-sample expected values printed; O-RX-1 identity bytes; O-RP-5a named class). Labels are now honest: **24 literal / 33 executable_at_A5.5** — every fixture with any placeholder or build-derived input is `executable_at_A5.5`, where Stream A writes it with literal inputs and the A5.5 review checks the mutation fails. Remaining placeholder completion is A5.5 work by design, stated in §11.1. |

### Protocol side — deferred to B4.5 (D-PROTO track; native's split ruling)

| finding | disposition |
|---|---|
| **R2-M01** observation meaning / ranges | **Accepted → B4.5.** Registry v2.2: 2007–08 sleep-disorder onset and 2021–22 quarry acquisition become 2-year grain-interval rows; vertigo gets an unscored `exacerbation` annotation row distinct from onset; "table is infallible" replaced by a source-reconciliation invariant (a count mismatch triggers registry-vs-scorer diff reconciliation, not an automatic scorer-bug verdict). |
| **R2-M03** validity before rank | **Accepted → B4.5.** Generation-wide rank void enforced in code: `era_indiscriminate` ⇒ T-rank status VOID in a machine-readable result file; no rank median printed for a voided generation; per-event percentiles carry eligibility/void status. |
| **R2-M04** ranking/aggregation contract | **Accepted → B4.5.** Protocol v2.2 prose states merge-representative selection (max si, ties → earliest peak) and one tie tolerance (1e-9) used by both ranking and peak-diversity; observed-year masking frozen; sign-convention adapter enforced on raw inputs (R3-P01). |
| **R2-M05** matched controls | **Accepted → B4.5.** ONE control experiment frozen: rolling spans at the event's own actual span length in days (the existing code), prose corrected to the code (not code to prose); domain, overlap semantics (any shared day), and weighting (unweighted) stated; controls re-materialised under seed 482012. |
| **R2-M06** operational input contracts | **Accepted → B4.5.** Machine-readable registry (`event_registry_v2_2.json`) is the scorer's input; protocol v2.2 carries the full 27-class polarity/adverse/eligibility table; coverage-manifest contract stated as a build requirement; annotation guard withdrawn to its honest scope (this historical scorer is restricted to annotation-free inputs; broader guard claims withdrawn). |
| **R2-M07** baseline narrative | **Accepted → B4.5.** Baseline v2.2 carries the corrected dedup account (the nine denser classes each merge to **10**, per the scorer's own merge block — my v2.1 "27/29/30" was an ad-hoc script bug, verified wrong) and distinguishes preliminary percentiles from valid ranks. |

## 3. The four new BLOCKING findings

| finding | disposition |
|---|---|
| **R3-S01** O-PP-2 controls unsound | **Closed in v1.3 (oracles).** Controls replaced and Lahiri-pinned: positive = Mercury/**Mars** AD (row `b1e4d515-6a94-4054-89ff-1ed2487f66ae`, 2019-02-17T06:50:23Z → 2020-02-14T11:47:23Z) — Mars occupies the natal 7th (Libra), a **scored** occupancy relationship. Negative = Mercury/**Rahu** AD (row `25a4b815-39bb-4b4a-b922-84a71778bb4f`) — Rahu (Taurus, 2nd) owns nothing and casts no dṛṣṭi (N-14); the Venus-dispositor chain exists (Rahu in Taurus IS Venus-ruled — the fixture says so) but is **testimony-only** per D-PADMIT and cannot licence. Boundary 2020-02-14T11:47:23Z under the §4.0 half-open convention. The v1.2 fixture's 2016–2019 Rahu interval is corrected: 2018-11-28 is Mercury/**Moon** under Lahiri (verified [L]). |
| **R3-S02** incompatible P4 rules | **Closed in v1.3 (specs §2.2 + O-RP-2/O-RP-3).** ONE rule: `infl(g) := (∃h∈H: contact(g,h)) ∨ (∃ℓ∈L(H): contact(g,ℓ))`; `P4_admit := infl(Jupiter) ∧ infl(Saturn)` — union within each agent, AND across agents, no shared-target requirement. O-RP-2 evaluates the father case with real transit-to-natal geometry (transit Jupiter 220.31° vs natal Jupiter 249.79°: Δ = 29.48°, no conjunction; aspects from Scorpio hit Pisces/Taurus/Cancer, not Sagittarius ⇒ infl(Jupiter) = FALSE ⇒ P4 false) as a labelled restricted negative test. O-RP-3 obeys the same rule (infl(J) via aspect on the 5th; infl(S) via conjunction with 5L within 5°). |
| **R3-S03** synthetic AV values attributed to extract | **Closed in v1.3 (oracles).** Verified against AV0: the extract has **no zero BAV** (Mars minimum = 1 at Sagittarius/Aquarius) and **no SAV 24** (SARVA: Aries 29, Taurus 29, Gemini 27, Cancer 32, Leo 30, Virgo 26, Libra 34, Scorpio 32, Sagittarius 25, Capricorn 27, Aquarius 23, Pisces 23). O-BP-1 keeps a known-zero case as **synthetic fixture rows** with explicit `fixture=true` keys, real extract rows cited for contrast, and a provenance mutation ("attributing the synthetic rows to the L1 extract fails"). O-BP-5 now uses the **real** Aquarius SARVA = 23 (fact_id `36b81039eeb707a7`) against config 28. The extract is unchanged. |
| **R3-P01** sign-convention assertion false and unenforced | **Accepted → B4.5.** Verified: the extract carries 70 `parental_event` rows with valence `mixed` and 10 `surgery` rows with `neutral` (X:6291–6299, 9855–9863); the scorer only prints the diagnostic. Protocol/registry v2.2: raw rows carry valence ∈ {gain, loss, mixed, neutral}; si stored non-negative; the adapter is enforced on **raw** inputs (si < 0 ⇒ machine-readable rejection before merging), and the input-description claim is corrected to the actual class/score semantics. |

## 4. C.1–C.4 dispositions

- **C.1** (do the claimed closures close?) — At round 3, correctly: only three did. This file +
  v1.3 close the six contract findings (§2 above); the six protocol findings are B4.5-scoped
  with named dispositions, not silently dropped.
- **C.2** (daśā read contract) — **Closed in v1.3 §4.0**: chart / ayanamsha
  `lahiri_chitrapaksha` / system `vimshottari` / build `1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb`
  (distinct from natal build `1c092ffb` and AV build `aa9602ce`) / tier `two_pass_verified`;
  half-open `[start_iso, end_iso)` boundary convention; parent linkage by row id;
  duplicate-row rule (select `two_pass_verified`; conflicting equally-qualified rows rejected
  loudly). Reference rows printed, PD lords **Mercury, Venus, Venus** at the three event
  instants — O-PP-1's original assertion, confirmed against the pinned build.
  **B38-F1 correction:** my v1_1 reconciliation asserted that no ayanamsha variant explains
  the discrepancy between O-PP-1 and the alternatives I had queried. That claim was **wrong**
  and is withdrawn: my earlier query was unpinned and matched rows of other systems
  (`surya_siddhanta_classical`, as the steward's [L] evidence shows). Under the pinned Lahiri
  build there is no discrepancy — O-PP-1 was right. The freeze lesson is the §4.0 contract
  itself: an unpinned read is a defect.
- **C.3** (G-10 caveats) — Acknowledged and carried unchanged into v1.3 §2.2 P5 and the
  oracle constants: `single_pass` verbatim; the `aa9602ce`/`1c092ffb` relationship stated as
  a reported recomputation, not asserted lineage; `pinda_sarva` per-subject split flagged not
  recompute-covered; P5c disabled as rebuild-pending (#2731 named).
- **C.4** (buildability / truthful labels) — **Closed by the amendment-5 policy**: fixture
  kinds now honest (24 literal / 33 executable_at_A5.5); the four specifically named defects
  fixed (O-VI-2 boundary convention stated and boundary day assigned to the clean interval;
  O-SM-1 replaced by a clean parabola with per-sample expected values — Δ is gone as a
  parameter; O-RX-1 identity bytes printed plus an extension case; O-RP-5a names
  `illness_acute`). Placeholder completion for the 33 executable fixtures is A5.5 work,
  checked there with the mutation-fails requirement.

## 5. Codex's ranked D-SPECS amendments 1–5 → where v1.3 closes each

1. **Typed identity** → §1.1 (generation+contact_id in the key; tagged support states;
   unknown-admission; `source_fact_ids`), §2.1 (version-qualified PKs/FKs), §6.1 (stable
   occurrence indexing + publication immutability).
2. **Numerical scoring and class/path definitions** → §2.1 (factor functions/ranges/units,
   evidence aggregation with shared-root dedup, exhaustive sets), §2.2 P4 (one rule).
3. **Daśā read contract + fixtures** → §4.0 + O-PP-1/O-PP-2/O-RR-2; B38-F1 conclusion
   corrected (§4 C.2 above).
4. **P5 semantics** → §2.2 P5 missing-input matrix; P5a nonzero comparator explicitly
   `unresolved`; synthetic-vs-L1 provenance fixed in O-BP-1/O-BP-5.
5. **Fixture contract** → §11.1 fixture-kind policy + honest labels (24/33) + the four named
   repairs; O-BP-2 case C.

## 6. Codex's ranked D-PROTO amendments 1–5 → B4.5 mapping (not worked here)

1. Observation meanings/ranges → registry v2.2 (R2-M01 row above).
2. Validity + input contracts → protocol v2.2 + machine-readable registry (R2-M03/M06).
3. Prose = implementation → protocol v2.2 (R2-M04) + raw-input adapter (R3-P01).
4. One matched-control experiment → protocol v2.2 + controls re-materialised (R2-M05).
5. Regenerated baseline → scorer v2.2 re-run + baseline v2.2 (R2-M07).

## 7. Artifact hashes

| artifact | sha256 |
|---|---|
| ASTRA_REVIEW_DESIGN_SPECS_v1_2.md (round 3) | c980fc8a7cf8c7cd17ed04ee811d25c6e3ccf5c2c837b132f5bbf79da05bba82 |
| GOCHARA_DESIGN_SPECS_v1_3.md | 727d174a01060226e05e78cc6b3c264e241069bae652f5c2727c1a4d8988af2d |
| GOCHARA_TEST_ORACLES_v1_3.json | 5a7258ad14f1f167530a12e122c392e4b3a6ce2595cd0c5973ff64f6d11fb981 |
| GOCHARA_DESIGN_SPECS_v1_2.md (superseded) | 5bfe1553d404be59f9b0246fcf410fe5a09be6946b5d97da6d733ecede45b039 |
| GOCHARA_TEST_ORACLES_v1_2.json (superseded) | c11a9d7e5ccf3a6c4a53569da5383ea7531ce840e48cfa6f7e0b8e2310143a43 |
| L1_ASHTAKAVARGA_EXTRACT_v1_0.json (unchanged) | 312de09e…88fe83 |
| L1_ASHTAKAVARGA_EXTRACT_v1_1.json (unchanged) | e9e5d4d3…3224 |
| EVALUATION_PROTOCOL_v2_1.md (B4.5 input) | 21de59943b335abb3df393810155c2a0d07315c5b1ae7fee5d54e93e7f5c7f1d |
| EVENT_REGISTRY_v2_1.md (B4.5 input) | ec738020dd2fbbe492317089a8ac5723169756740de932cea408aeb5cde7f34c |
| BASELINE_3_0_v2_1.md (B4.5 input) | b4c46222fe23fbd51b5028004d11a11cfafb422de124c23c4f4867bfb8a4ce60 |

*Dispositions are mine as Stream B; "closed" means closed against the round-3 evidence as
computed and cited here — the native (and any further review round the native orders) judges
whether the closure holds. status: FROZEN is not set anywhere; D-SPECS and D-PROTO remain
native decisions.*
