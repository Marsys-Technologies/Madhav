• I'll begin by verifying the packet SHAs and reading the artifacts.

• All 18 SHAs verify against the packet table. Now reading the artifacts.

• Now the in-memory recomputation of the '3.0' re-run, plus structural checks on the extract and controls.

• Registry arithmetic needs an independent count against the LEL itself. Counting EVT ids in the LEL:

• One LEL event — `EVT.2015.XX.XX.01` — appears nowhere in the registry (not held-out, dev, or excluded). Checking what it is:

• All verification complete. The full review follows — printed only, no file written.

  ---

  ```yaml
  ---
  artifact: KIMI_K3_REVIEW_DESIGN_SPECS
  version: "1.1"
  status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
  reviewer: "Kimi K3 (effort=max) — independent review (round 2)"
  date: 2026-09-29
  verdict_specs: FREEZE_WITH_AMENDMENTS
  verdict_protocol: ACCEPT_WITH_AMENDMENTS
  reviewed_packet_sha256:
    design/reviews/REVIEW_PACKET_DESIGN_SPECS_v1_1.md: 145f7b1b2a4de9930ed8d866fbfbd1fd0aaa240e43498e7362bc619f608ef716
    recomputed_with: "shasum -a 256 on campaign/pravaha, 2026-09-29; all 18 packet-table artifact hashes re-verified individually and all match (including both round-1 reviews: 7872f239…c8c7, 536d2b1a…a8ee)"
  authority: "Review only; authorizes nothing."
  ---
  ```

  # KIMI K3 REVIEW (ROUND 2) — Gochara specs v1.1 + oracles v1.1 + protocol v2.0 + registry v2.0 (B3.7)

  ## 1. Verdict lines

  **Specs + oracles: FREEZE_WITH_AMENDMENTS.** The v1.1 rework is substantively excellent: every doctrine correction round 1 demanded is landed and verified (O-RP-5 is one test, prose ≡ JSON; aspect-direction invariant + O-AD-1…4 recomputed correct; provenance/operator-role separation real; P5a–e independent with honest missing-data states; the sign-mean comparator is gone; all 55 oracles parse, match the §11.2 index exactly, and carry a mutation each). What remains is contract-level, not doctrinal: the §6.1 identity tuple still cannot distinguish recurring physical contacts, invariant 3 references a `contact_id` the schema never declares, the within-path score algebra is unstated, and four named fixtures are not literal enough to build. None of these changes a ruling; all must land before D-SPECS because the freeze standard is "build-complete contract".

  **Protocol v2.0 + event registry: ACCEPT_WITH_AMENDMENTS.** The protocol's constructions are sound and every headline figure of the '3.0' re-run reproduces exactly under my independent recomputation (§6 below). But the registry — whose entire purpose (Codex M-01) was a complete, row-level, explicitly-dispositioned event inventory — **silently drops one in-horizon LEL event** (`EVT.2015.XX.XX.01`, SPR.D), and its printed completeness arithmetic double-counts CURRENT.01 in a way that masks the omission. One missing row, mechanically fixable, with known consequences (denominator 46→47, T-cover floor restatement, 20 more control draws); that is an amendment, not a redesign. It must land before D-PROTO, and the re-run must be re-touched under protocol §9.6's own amendment machinery.

  ---

  ## 2. Round-1 closure table (both reviewers, every finding; verified against the v1.1/v2.0 artifacts, not the reconciliation's labels)

  ### Kimi K3 round 1

  | Finding | Status | Evidence |
  |---|---|---|
  | F1 (JSON 25 vs 35 named; 14 oracles absent) | **Resolved** | Oracles v1.1 JSON: 55 entries, 0 dupes, header `oracle_count: 55`; set equality with the §11.2 index verified programmatically in both directions; every oracle has non-empty given/when/then/mutation/operands_source/tolerance/guards/defects |
  | F2 (#13 aspect direction: no invariant, no oracle) | **Resolved** | Specs v1.1 §6.2 inv 6 (GOCHARA_DESIGN_SPECS_v1_1.md:439-444) pins the forward count; O-AD-1…4 are first in the JSON; I recomputed all four roots (Mars 4th → 270°, Mars 8th → 150°, Saturn 3rd → 300°, Saturn 10th → 90° for target 0°) — all correct, and the mirrored `target+angle` implementation fails each fixture as claimed |
  | F3 (#24/#5/#19 oracles; #18/#20/#21/#23/#26 dispositions) | **Resolved** | O-GR-PLATEAU, O-P6-TARA (fixture verified: star indices 24/20 → nine-fold class 6 ✓), O-BP-4, O-RP-6/7/8, O-RR-5/6, O-BP-5 all present with mutations; #18 folded into O-BP-1's wrong-frame mutation (specs §11.2, lines 618-620) |
  | F4 (§9 stale vs B3.3; P2 node line) | **Resolved** | §9.2 inv 3 (lines 530-536): three separate [D] activation modes, no synthesised conjunction, Mudda labelling [U] retained, P9 still behind D-T2; P2 carries the XXVI.1–2/XXVI.24 node line with N-14 restated (lines 175-178) |
  | F5 (10,592; "22 vs 25"; Moon count) | **Resolved** | Masked H = 10,334 and full horizon 10,592 both recomputed by me and correct; count stated truthfully as 55 |
  | F6 (relation enum mixing; unscaled evidence; role/relation overlap) | **Resolved** | §1.1: `relation` split into transit vs natal-fact relations with the never-mix rule (line 80); evidence fields declared rank-only, scale at calibration (line 94); `object_role` authoritative for role, `relation` for physical relation (line 83) |
  | F7 (O-PP-2 tests non-constancy) | **Resolved** (with a new fixture-literalness gap, NK-7) | O-PP-2 replaced: related vs unrelated period, direction asserted, boundary case, variance demoted to labelled smoke check |
  | Q-M1 (do not re-run '3.0') | **Overridden** (directive; correctly recorded — see §3 Q1) | Reconciliation §A Q-M1, §C |
  | Q-M2 (floor denominator 26 → 14) | **Resolved** | Protocol v2.0 §6.3: floor = floor(27/2)+1 = 14 computed from the audited registry cohort of 27; cohort of 27 itself verified against the LEL (Q3b below) |
  | Q-M3 (aggregate bar applied per class) | **Resolved** | Protocol v2.0 §6.4 per-class budgets `min(1, 3·n_c·90/H)` with printed arithmetic; recomputed by me (§4 Q5) |
  | Q-M4 (single capped median; 182 d) | **Resolved** | §5: all errors capped at 182, misses and uncapped hits reported separately — both mandatory disclosures present in BASELINE_3_0_v2_0.md §2 |
  | Q-M5 (failability + load-bearing gaps) | **Resolved** | All 55 oracles carry a fail-able mutation; arithmetic spot-recomputed across 20 checks (§5) — all pass |

  ### Codex (Astra) round 1

  | Finding | Status | Evidence |
  |---|---|---|
  | S-01 (schemas not build-complete) | **Partly resolved** | Typed contracts landed (§1.1, §2.1: keys, FKs, null states, `unknown_is_false: false`, max-aggregation, evidence-not-netted). **Residuals (new findings NK-3, NK-4):** invariant 3 (line 104) references `contact_id`, which §1.1's table never declares (nor `generation`, despite the reconciliation claiming both were added); within-path factor→score algebra is still unstated (the reconciliation's "per-path product" appears nowhere in the spec); `record_id`'s natural key omits prerequisites/source, so two records differing only there collide |
  | S-02 (identity/lineage unreconciled) | **Partly resolved** | Rounded-`t_exact` hashing forbidden, truncated-contact identity stable, invalidation dependency-driven (§6.1, §10.1) — all good. **Residual (new finding NK-2):** the printed identity tuple `hash(body, relation_kind, canonical_target, convention_id)` contains no occurrence/time component; annual recurring contacts (e.g. Sun–natal-Sun conjunction every year) share one tuple, and the stated collision rule ("build fails loudly") would then halt every multi-year build. S-02's core case is not closed |
  | S-03 (O-RP-5 reversed; prose≠JSON; mixed≠uncertain; P3 Boolean) | **Resolved** | O-RP-5 is one test, prose (lines 288-294) ≡ JSON, direction verified: Saturn 288.01° → Capricorn = 12th from the Aquarius Moon (recomputed), evidence FOR adverse classes, nothing on childbirth; §3 keeps contested occurrence distinct from `mixed` valence; P3 rewritten as explicit Boolean with per-class truth table (lines 188-210) |
  | S-04 (source/admission/scoring conflated) | **Resolved** | §0 two-field separation (lines 43-55); every D-PADMIT element + all P6 operators testimony-only with a named measurement promotion gate; O-RR-7 bitwise-equal-score fixture; O-AO-3 keeps P9 testimony pre-D-T2 |
  | S-05 (AV: unruled mean; contradictory fallback; P5d conventions; no #26 fixture) | **Resolved** | Sign-mean removed (§8.1, lines 492-494); P5a–e independent with per-form missing-data states (missing donor matrix ⇒ P5c alone unqualified, O-BP-2 case B); P5d pins `mod 27`, remainder 0 ⇒ 27th nakṣatra; O-BP-5 measured-SAV-vs-config fixture present |
  | S-06 (corpus-read overstatement) | **Resolved** | Chart-specific AV operands `unresolved` pending G-10 (lines 241-244, 496-498); three saham modes kept separate; OCR uncertainty recorded per-clause (Aṣṭottarī pakṣa, MC PG67:C1); annotation guard in protocol §7 (LEL_CHART_STATE_RECONCILED exists — verified present) |
  | S-07 (inventory/falsifiability; O-AO-1 impossible; O-PP-2 proxy; O-CF-N5 bad fixture) | **Partly resolved** | Inventory complete and count-consistent; O-AO-1 rewritten correctly (broken kind-only join is now the defect on test); O-CF-N5 has a real two-peaks-60-days fixture; O-CF-N6 a non-empty control. **Residual (NK-7):** O-SM-1/O-SM-2/O-RR-5/O-PP-2 fixtures still not literal (values asserted as "pinned" but absent) |
  | S-08 (arithmetic errors) | **Resolved** | 3°38′24″ ✓, 0°33′36″ ✓, 1°49′12″ ✓, 2°08′24″ ✓, 0°19′12″ ✓, 3°57′ ✓, Venus 259.19 (259.1882 half-up) ✓, full hashes throughout ✓ — all independently recomputed |
  | M-01 (event population loses observation meaning) | **Partly resolved** | Registry exists and 6 of 7 judgment calls verify at the LEL (see §3 Q3). **Residual (new finding NK-1, blocking):** `EVT.2015.XX.XX.01` (SPR.D, spiritual_turn, year-approx, in-horizon, LEL:1766) has no registry row and no exclusion; the header arithmetic "57 − 3 dev − 7 excluded − 1 status = 46" double-counts CURRENT.01 (it is one of the 7 excluded rows *and* the 1 status) and thereby masks the omission: my independent count of the LEL gives 57 real EVT blocks; 57 − 3 dev − 46 held-out − 7 excluded = **1 leftover = EVT.2015** |
  | M-02 (horizon/counts/floor wrong) | **Resolved, contingent on NK-1** | Mask 2026-04-17 ✓ (LEL:13 `date_range_covered … to 2026-04-17`); H = 10,334 ✓; counts recomputed from the registry ✓ — but the registry itself is short one row |
  | M-03 (metrics not reproducible) | **Resolved with notes** | Class universe fixed ex ante; one tier policy; IST/18:30-UTC convention stated; ties/misses defined; controls materialised (I reproduced them byte-for-byte). Notes NK-6/NK-10 on scorer-vs-protocol residuals |
  | M-04 (T-rank selective validity) | **Resolved with note** | Worst-rank-100 misses, dedup-before-N, average-rank ties all in §4 and in the scorer. Note NK-9 on the percentile asymmetry |
  | M-05 (T-FP denominator switching; adverse membership) | **Resolved** | Adverse classes frozen (§2); per-class budgets with printed arithmetic; burden vs budget kept distinct |
  | M-06 (asymmetric 182 cap) | **Resolved** | All errors capped; uncapped hits (686/998/327 d) and miss count (2/5) both printed |
  | Q-M1 (re-run from pinned extract) | **Accepted** — done | BASELINE_3_0_v2_0.md + pinned 914-row extract + deterministic scorer, all reproduced by me |
  | Q-M2 (majority floor policy) | **Accepted** | "Majority of the audited cohort" is the stated policy; floor printed as a formula |
  | Q-M3 (pick one budget form; show arithmetic; mask) | **Accepted with a wording residual (NK-8)** | Per-class form chosen and arithmetic printed; but §6.4's derivation still says "a true event justifies at most a ±45-day footprint (the T-time tolerance)" — the peak-error-vs-window-width conflation Codex explicitly warned against |
  | Q-M4 (cap consistently; even-cohort median) | **Accepted** | Cap consistent; median convention stated in the reconciliation; cohort is 5 (odd) so the convention is untested but harmless |
  | Q-M5 (per-oracle corrections) | **Partly resolved** | Table implemented row-by-row except the literalness residuals above (O-SM-1 pinned values absent; O-SS-2's "stated interval" never stated numerically) |
  | Ranked amendments 1–10 | 1,2,3,5,8,9,10 **resolved**; 4,6,7 **partly** (same residuals as S-01/S-02, S-07/Q-M5, M-01) | as itemised above |
  | Defect-coverage rows #1, #5, #19–#24, #26, N9 | **Resolved** | O-RP-6, O-P6-TARA, O-BP-4, O-RP-7, O-RP-8, O-RR-5, O-RR-6, O-GR-PLATEAU, O-BP-5; N9 via protocol §7 + registry verification state (specs line 622) |

  **Regressions: none found.** Nothing that was correct in v1.0 is broken in v1.1.

  ---

  ## 3. Answers to packet §4

  **Q1 — the override.** Correctly recorded. Reconciliation §A marks Kimi Q-M1 `overridden` naming the native's instruction #7, and §C states explicitly "Recorded as OVERRIDDEN (Kimi) / ACCEPTED (Codex), not adjudicated on merit." That is directive-supersession labelling, not adjudication. I audited every other non-"accepted-as-requested" disposition for a disguised override and found none: Q-M2/Q-M3/Q-M4 are "accepted with amendment" where the amendment is a construction one of the two reviewers themselves offered (Q-M3's per-class form is Codex's alternative 2; Q-M4's universal cap is Codex M-06; Q-M2's cohort-derived floor is what both reviewers recomputed); F4's amendment (three separate saham modes) is Codex S-06's own demand, not a contrary judgment. No other override in substance.

  **Q2 — fixture literalness.** 51 of 55 oracles are buildable without asking a question (the synthetic generators among them — O-RP-6, O-RP-7, O-VI-1, O-CF-N5, O-RR-4 — are constrained enough to construct deterministically). **Not literal (builder must ask):**
  - **O-SM-1** — "pinned start/end, target longitude, orb; Swiss longitudes at 6-hour samples": none of the pinned values is in the JSON.
  - **O-SM-2** — "δλ stated": it is not.
  - **O-RR-5** — "e.g. a named 7th-house combination": no yoga named, no strength value, no cancellation predicate; "both pinned" is asserted, not done.
  - **O-PP-2** — "a named period whose lords carry NO 7th-house relationship": the period is never named.

  **Falsely labelled literal (buildable as constraint generators, but the prose claims "literal timestamps" that are not printed):** O-VI-2, O-VI-4, O-SS-2 ("a stated interval" — unnumbered), O-SS-3. Borderline: O-TV-2 (the "natal 7th affliction condition" supplying evidence_against is unspecified — which affliction, what weight?).

  **Q3 — registry judgment calls.** (a) EVT.2026.03.20 → major_gain: LEL:1500–1508 confirms a project closure "with enormous profits," valence `mixed`, revenue accrued 2023–2026. "The dated point is a realised gain" is a defensible reading [J], and it is disclosed as a judgment call — acceptable. I note for the record that the equally defensible alternative (the dated point is the *termination of the income stream* → career_setback) exists; the disclosure is what makes this a judgment call rather than an error, and under either mapping the event is in the adverse-or-gain census of exactly one class, so T-FP exposure moves between two classes but no count changes. (b) MBA enrolment restored, cohort 27: **correct**. LEL:674–682 is a month-exact enrolment event (`date_confidence: month-exact`, "Joined in June 2011"), and the LEL itself distinguishes it from admission ("Admission-event distinct from enrollment-event", LEL:~670; admission row LEL:643 verified). The round-1 count of 26 was made without this row; 27 is right against the LEL as written. **However**, while verifying the cohort I found the registry is nonetheless not complete — see NK-1 (EVT.2015.XX.XX.01, SPR.D, missing entirely).

  **Q4 — instant-class misses: settlement verified, with two factual corrections.** I confirm the substance: the misses are '3.0''s served behaviour, not a scorer artefact. The extract's five chain classes (education_milestone 40, career_change 30, business_launch 30, foreign_settlement 30, separation 30) serve only zero-width rows; dedup merges only abutting/overlapping rows; containment requires an exact day match (month proxy = 15th, protocol §5). I cannot construct a reading of §5 under which the scorer is wrong: §5 defines timing error only *for containing windows*, so no tolerance reading manufactures containment; and under the most lenient month-overlap reading, **zero** of the 12 month-grain instant-class events has any served day in its event month (I enumerated them all). Two corrections to the packet/baseline wording: (i) EVT.2004.XX.XX.02 (education_milestone, **year**-grain) is a **hit**, not a miss — three instant days fall in 2004 (02-05, 04-05, 07-04) and year-grain containment is year-overlap; the baseline §2 sentence "the five zero-width instant classes … miss every event in them" is therefore false as stated (15 of 16 instant-class events miss, not 16); (ii) the packet's "2004-07: one day" holds only under a proxy-month reading — the year contains three served days. Neither correction disturbs the conclusion: all 15 T-cover misses are instant-class events, and the one instant-class hit exists only because year-grain overlap is coarse.

  **Q5 — horizon and budgets.** Recomputed: 1998-01-01 → 2026-04-17 inclusive = **10,334 d** ✓; full horizon to 2026-12-31 = **10,592 d** ✓; post-mask = 258 d ✓. Budgets: n_c=1 → 270/10,334 = **2.6128 %** ✓; n_c=2 → 540/10,334 = **5.2255 %** ✓; major_loss allowance 2.61 % ✓. The n_c=0 allowance rule is sound as a declared policy [J]: the alternatives are budget 0 (forbids any admission of a class the log may simply not have recorded — too strong given the disclosed LEL-completeness limit) or an arbitrary floor; treating an unfalsifiable class as if it had one event is the minimal honest convention and its rationale is printed. The factor-3 slack is defensible **as a declared policy multiplier** — but not as currently derived: §6.4's "a true event justifies at most a ±45-day footprint (the T-time tolerance)" conflates a peak-error tolerance with a window width (a 120-day window can legitimately have its peak within 45 d of the event). Codex's Q-M3 caution ("explicitly a chosen allowance, not a discovered duration") is only half-heeded. Fix the sentence, keep the number (NK-8).

  ---

  ## 4. Fresh defect hunt — new findings (round 2)

  **NK-1 — BLOCKING (registry) · claim:** the registry silently omits an in-horizon LEL event. **Evidence:** `EVT.2015.XX.XX.01` (LEL:1766–1782: spiritual / devata_adoption, year-approx 2015, in-horizon, `valence: positive`) appears in no registry table — not §2, §3, or §4. My independent count: 57 real EVT blocks in the LEL (grep `^EVT\.` minus the `EVT.YYYY.MM.DD.XX` template); 57 − 3 dev − 46 held-out − 7 excluded = 1 leftover, exactly this row. The registry's own completeness line (EVENT_REGISTRY_v2_0.md:102-103) "57 logged − 3 dev − 7 excluded − 1 status" double-counts CURRENT.01 (it is simultaneously one of the 7 excluded rows and the "1 status"), which is how the omission balances. LEL:32 lists SPR.D in the spiritual series; the registry includes SPR.A/B/C/E/F/G but not D. **Consequences:** held-out = 47 (or an explicit exclusion with reason); T-cover denominator and the 31-hit floor move (SPR.D is year-grain spiritual_turn, an era class in '3.0' — almost certainly a hit, making the re-run ~32/47 = 68.1 %); 20 more control draws; spiritual_turn census; protocol §9.2's "mismatch with the registry's §6 table is a scorer bug" would currently ratify the omission. **Requested change:** add the row with its disposition (or an explicit, reasoned exclusion), re-run, restate the floor via the protocol's own amendment mechanism, and correct the header arithmetic.

  **NK-2 — BLOCKING (specs §6.1, S-02 residual) · claim:** the physical-identity tuple cannot distinguish recurring contacts. **Evidence:** `physical_object_id = hash(body, relation_kind, canonical_target, convention_id)` (lines 412-414) contains no occurrence component. A Sun–natal-Sun conjunction recurs every year under one (body, relation, target, convention); the tuple is identical for all ~30 in-horizon occurrences, and the stated collision rule (line 421: "on collision the build fails loudly") would then halt every multi-year build — or, worse, silently dedup distinct crossings. The rounded-`t_exact` prohibition implies full-precision `t_exact` may be hashed, but the tuple never includes any time or occurrence index. An implementer must guess. **Requested change:** pin occurrence identity explicitly (e.g. add the full-precision solved `t_exact`, or an occurrence ordinal over the ordered crossing set of the tuple) and state which; add an oracle fixture with two same-tuple crossings in one horizon.

  **NK-3 — SHOULD-FIX (specs §1) · claim:** invariant 3 references an undeclared field. **Evidence:** §1.2 inv 3 (line 104) keys role-alias sharing on `contact_id`; the §1.1 table declares no `contact_id` (and no `generation`, though reconciliation §B S-01 claims both were added). Also `record_id`'s natural key omits `prerequisites`/`source_text`, so records differing only there hash-collide. **Requested change:** declare `contact_id` FK (and `generation` if intended) in §1.1, or rewrite invariant 3; extend the natural key or state why the omitted fields cannot differ within it.

  **NK-4 — SHOULD-FIX (specs §2.1) · claim:** within-path score algebra is still unstated. **Evidence:** `factor` declares direction/range/null_state/effect-text but no combination rule; cross-path aggregation is pinned (max, line 153) while per-path composition is not; the reconciliation's "per-path product" (§B S-01) appears nowhere in the spec. **Requested change:** one sentence pinning the within-path combination (and its null propagation), matching whatever the reconciliation meant.

  **NK-5 — SHOULD-FIX (baseline §1/§2 factual) · claim:** the dedup mechanism description is wrong. **Evidence (my recomputation from the pinned extract):** era classes merge to **10 candidates per class**, not "1 merged candidate per class spanning 1984–2084" (BASELINE_3_0_v2_0.md:27-28); the decade windows are non-abutting (small gaps), which is also why the base rate is 99.87 % rather than 100 %; foreign_settlement merges 30 rows → 20 candidates. Endpoint results are unaffected (per-year N stays 1 for era classes, so T-rank's 1/27 stands; all T-cover/T-FP figures reproduce). **Requested change:** correct the mechanism paragraph; the conclusions stand.

  **NK-6 — SHOULD-FIX (scorer vs protocol) · claim:** two latent divergences that don't move '3.0' but will move future generations. **Evidence:** (a) scorer `rerun_3_0_v2_0_scorer.py:182-184` approximates T-FP hit days as 1 day per hit event; protocol §6.4 defines negative days as days not inside a *containing-window hit* (for era windows that is ~the whole horizon). For '3.0' both readings give FAIL at ~99.87 %; for a future tight-window generation the scorer's approximation overstates burden. (b) Scorer ranks by `abs(si)` (line 118); protocol §4.3 ranks by *signed* intensity (descending for gain, most-adverse first). These coincide only if adverse si is negative with magnitude ∝ adversity; the extract's sign convention is not asserted. **Requested change:** compute actual covered hit days per event (with the month/interval overlap rule stated in the protocol); assert the si sign convention and rank per §4.3.

  **NK-7 — SHOULD-FIX (oracles, S-07/Q-M5 residual) · claim:** four fixtures not literal, four mislabelled. **Evidence:** as itemised in §3 Q2 (O-SM-1, O-SM-2, O-RR-5, O-PP-2 not buildable without asking; O-VI-2/O-VI-4/O-SS-2/O-SS-3 claim "literal" values they do not print). **Requested change:** print the values (or relabel as generators with full constraints).

  **NK-8 — NOTE (protocol §6.4)**: the derivation sentence conflates peak-error tolerance with window footprint; the multiplier is fine as declared policy — say so (Codex Q-M3's caution). **Requested change:** wording only.

  **NK-9 — NOTE (protocol §4.4 / scorer line 124)**: percentile formula `100(r−1)/N` caps any real worst rank below 100 (e.g. 66.7 at N=3) while misses enter at exactly 100 — a miss ranks strictly worse than the worst served candidate. Declared and acceptable as a convention; state the asymmetry explicitly.

  **NK-10 — NOTE (controls)**: the grandfather interval event draws its 20 controls at 365-day span (scorer line 200's else-branch; committed file confirms `span_days: 365`), though the event's resolution is a 61-day interval — inflating that event's control hit rate. Immaterial here (20 of 920 draws; era-class bereavement admits everything anyway); fix the span map before candidate scoring.

  **NK-11 — NOTE (baseline §2 / packet Q4 wording)**: "miss every event in them" is false (EVT.2004 year-grain edu is a hit via 3 served days in 2004); "2004-07: one day" is proxy-month-only. Settlement substance unchanged.

  **NK-12 — NOTE (packet §5)**: G-10 blocks more than named — O-BP-1 (`operands_source: L1 ashtakavarga_bindu*`) and O-BP-4 (donor matrix) also cannot run against this chart until the extract lands; only O-BP-5 is named.

  **NK-13 — NOTE (legacy evidence)**: the extract contains `birth_anchor` rows (10 merged candidates, 99.87 % base rate) — O-CF-N6 would fail '3.0'. Correctly treated as history via two-horns, but worth naming as confirmation that the N6 kill-switch defect was real in the served generation.

  ---

  ## 5. Fresh oracle verification (all 55)

  Structure: 55 entries, unique ids, set-equal to the §11.2 index (both directions), every required field non-empty, every oracle carries a `mutation_that_must_fail` — the F1/S-07 inventory defect is fully closed. Arithmetic: I recomputed every longitude → sign → house → aspect → separation in the JSON and §11.3 independently (20 checks): Moon/Jupiter both Aquarius (1st from Moon, 11th from Aries) ✓; natal Saturn Libra = 7th ✓; bhavat_bhavam:9 frames (2nd = Capricorn/Saturn, 7th = Gemini/Mercury, 8th = Cancer/Moon) ✓; Jupiter 220.31° Scorpio aspects {Pisces, Taurus, Cancer}, Sagittarius absent ✓; Saturn 288.01° = 12th from Aquarius ✓; Rāhu Taurus = 8th from lagna-lord Mars Libra ✓; Δ values 3.95° = 3°57′, 3.64° = 3°38′24″, 1.82° = 1°49′12″, 2.14° = 2°08′24″, 0.32° = 0°19′12″, 0.56° = 0°33′36″ ✓; O-AD-1…4 roots (270°/150°/300°/90°) ✓; Venus 259.1882 → 259.19 half-up ✓; tārā fixture (natal 24, transit 20, inclusive cyclic 24 → class 6) ✓; father-date Saturn 253.43° = 11th from the Moon ✓; marriage Jupiter 84.57° 5th aspect → Libra ✓. Every oracle can fail — each mutation names a concrete broken implementation and the fixture's expected values distinguish it.

  ## 6. Recomputation of the '3.0' re-run (in memory, /opt/homebrew/bin/python3, nothing written)

  Re-derived from `baseline_3_0_extract_v1_0.json` (914 rows asserted) + the registry as written + re-implemented protocol v2.0 rules:

  | Figure | Baseline v2.0 claim | My recomputation | Δ |
  |---|---|---|---|
  | T-cover | 31/46 = 67.4 %, 15 named misses | 31/46 = 67.4 %, identical miss list | none |
  | T-time | capped median 182 d; misses 2; uncapped 686/998/327 | 182 d; misses 2 (2008-06-09, 2024-02-16); uncapped 686/998/327 | none |
  | T-rank | 1/27 reach N ≥ 3 (EVT.2024.02.16.01, N=3, miss at 100); floor 14 → rank-unproven | identical | none |
  | Era fingerprint | 210/351 = 59.8 % | 210/351 = 59.8 % | none |
  | T-FP | 8/9 adverse FAIL at 99.87 %; separation 0.09 % PASS | identical, per class | none |
  | Two-horns | 17 gain classes degenerate-high; 5 instant classes degenerate-low | identical (plus birth_anchor degenerate-high — NK-13) | naming only |
  | Random controls | 622/920 = 67.6 %, seed 482012, materialised | 622/920 = 67.6 %, control dates **byte-identical** to the committed file, zero mismatches | none |
  | Dedup mechanism | "1 merged candidate per class spanning 1984–2084" | 10 merged candidates per era class; foreign_settlement 20 | **NK-5** (endpoints unaffected) |
  | Instant-class pattern | "miss every event in them" | 15 of 16 miss; EVT.2004 year-grain edu is a hit | **NK-11** |

  ## 7. Ranked amendments

  **Must land before the specs freeze (D-SPECS), in order:**
  1. **NK-2** — pin occurrence identity in §6.1 (time/occurrence component in the tuple) + a two-crossings-same-tuple oracle fixture. The contract is otherwise unbuildable for any multi-year horizon.
  2. **NK-3** — declare `contact_id` (and `generation`, or strike it from the reconciliation claim) in §1.1; repair the `record_id` natural key.
  3. **NK-4** — one sentence pinning the within-path score algebra.
  4. **NK-7** — make O-SM-1, O-SM-2, O-RR-5, O-PP-2 literal (print the pinned values / name the period); correct the "literal timestamps" wording in O-VI-2/O-VI-4/O-SS-2/O-SS-3.

  **Must land before protocol acceptance (D-PROTO), in order:**
  1. **NK-1** — disposition EVT.2015.XX.XX.01 (SPR.D) in the registry with its LEL anchor, fix the 57-event header arithmetic, re-run the baseline under protocol §9.6's amendment path, and restate the T-cover floor that the re-run defines.
  2. **NK-6** — scorer: real hit-day computation for T-FP negative days; signed-intensity ranking per §4.3 (with the si sign convention asserted).
  3. **NK-10** — control span map: interval-grain events draw at their interval length.
  4. **NK-8** — rewrite the §6.4 derivation sentence as a declared allowance (keep 3× and 90 d).

  NK-5 and NK-11 are baseline-text corrections that should ride with amendment 1 of the protocol list (the re-run re-touches that file anyway). NK-9/NK-12/NK-13 are disclosure-level.

  ## 8. Disclosure — what I could not verify

  - **E8's underlying ephemeris values** (the L0 longitudes themselves) and L1's natal chart (build 1c092ffb): taken as pinned inputs per the ground rules; I verified all arithmetic *on* them, not their correctness against an ephemeris. UNVERIFIABLE_HERE.
  - **"Sun/Jupiter/retrograde Mercury in the native's 8th" (§11.3, father event)**: plausible (Sun ~Scorpio on 2018-11-28 = 8th from Aries) but not recomputed from an ephemeris here; the retrograde-Mercury and Venus-retrograde (twins) claims rest on B4.1/LEL corrections cited, not re-derived.
  - **The sealed doctrine file** (per packet instruction) and **served-corpus locators** (`BPHS2:35666-35684`, PG pages): membership of the corpus not re-queried.
  - **`platform/python-sidecar/**` code**: read permission noted but not exercised — the review surface is the design/measurement artifacts; no claim in the packet required code-level confirmation beyond what the pinned extract + scorer already provide.
  - **The scorer's committed outputs**: verified by re-implementation (controls byte-identical; per-event results identical), not by executing `rerun_3_0_v2_0_scorer.py` itself, which writes two files and was therefore not run (read-only mandate).
  - **Whether EVT.2015.XX.XX.01's omission was deliberate**: if a disposition exists somewhere outside the registry, it is not referenced there; the registry as written is incomplete either way.

  *End of round-2 review. Read-only throughout: no file created, edited, moved or deleted; no git write command; no database connection; the tracker paths were not touched. Every figure attributed to me was recomputed in memory with /opt/homebrew/bin/python3.*

