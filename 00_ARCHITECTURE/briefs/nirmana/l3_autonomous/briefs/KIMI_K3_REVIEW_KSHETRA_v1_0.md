---
artifact: KIMI_K3_REVIEW_KSHETRA
canonical_id: KIMI_K3_REVIEW_KSHETRA
version: "1.0"
status: CURRENT
date: 2026-09-23
kind: independent-review record (reviewer output, verbatim; not authored by the packet author)
reviewer: "Kimi K3, effort=max (k3 default_effort and [thinking].effort both max; resolution verified in the CLI binary)"
packet: KIMI_REVIEW_PACKET_KSHETRA_v1_0.md
reconciled_in: KIMI_RECONCILIATION_KSHETRA_v1_0.md
generated_via: "kimi -m kimi-code/k3 -p <packet>; cwd /Users/Dev/madhav-l3/kshetra (l3/kshetra-elevation)"
note: "Horizontal rules inside the reviewer output are rendered as *** so no fence-splitting reader mistakes one for a frontmatter opener."
---

# Kimi K3 (effort=max) review — Kṣetra brief v4.0 + ecosystem plan v1.0
# generated 2026-09-23T01:34:50+05:30 via: kimi -m kimi-code/k3 -p <KIMI_REVIEW_PACKET_KSHETRA_v1_0.md>; k3 default_effort=max, thinking.effort=max; cwd=/Users/Dev/madhav-l3/kshetra (branch l3/kshetra-elevation)

• I'll review the two documents in full, read the cited code, verify classical citations against the corpus, and then deliver the review. Starting with the documents and code sizes.

• Documents are compact. Reading both in full, plus the strategy doc.

• Both documents are read in full. Now the strategy contract and the code, in parallel.

• Now the remaining code ranges and a classical-corpus verification in the background.

• Code depth is sufficient. Now the product definition, the §N rails, and two last verifications.

• Confirmed at source: `FieldEvaluator.terms_at` passes **all** active obstructions unfiltered into `hazard.evaluate` (`stage4_field.py:866-873`), while `layer1.project_layer1` applies the SM-R-7 route filter — and `dhara_null.py` builds its replicates via `evaluator.ln_lambda`, the unfiltered path. That is Pūrṇa's G3 with a sharper consequence: the null is computed under chart-wide suppression while the field is written route-scoped. Two quick supporting checks while the citation agent runs.

• All technical reading is done. I need the classical-corpus verification to finalize citations — waiting on it now.

• All reading is complete: both documents in full, the strategy and product contracts, the nine cited code regions, the §N rails, the classical corpus (via a verification pass), and the source-level confirmation of Pūrṇa's G3. Here is the review.
***
  # Independent review — `ka_kshetra` elevation brief v4.0 + ecosystem plan v1.0

  **Review basis.** Brief and plan read in full; `layer1.py`, `hazard.py`, `dhara_null.py`, `contracts.py:100-297`, `stage2_promise.py:1-540`, `stage1_symbolization.py:200-384`, `stage3_clocks.py:940-1120`, `stage4_field.py:180-215, 866-876, 1140-1254`, `uncertainty.py:100-206`, `stage5_null.py:67-170`, `integrator.py:1-60`, `writers/mi_bhara.py:398-410` read at source. Classical citations verified against `00_ARCHITECTURE/SOURCE_DATA/classical_texts/` — whose actual inventory is BPHS Vol 1 (Santhanam, Ch. 1-45), BPHS Vol 2 (Kapoor, Ch. 46-97), KP Reader Vols 5-6, Jaimini (Adhyayas 1-2). **Phaladīpikā, Sarvārtha Cintāmaṇi, Jātaka Pārijāta, and all Tājika/Varṣaphala texts are NOT in the admitted corpus**; where the tradition is invoked from them, I tag it and note the project's own L0 disclosure route instead.
***
  ## K-1 — Value proposition and the ablation

  **Recommendation.** Keep **Q06 as the primary home, but narrowed to the claim that is actually unique**: not "mechanism change" (Sangam's witness lists already gesture at that), but (i) **continuous sub-threshold shape** — the background/enabling/contact trichotomy that Strategy §2 Q01 names and no window can express, since a window only exists where found; and (ii) **driver decomposition** — two intervals at equal λ with different clock/modifier/suppression composition are *different chapters* in Q06's own sense ("recurrence with changes in participants, conditions, clocks, relationships"), and no window field distinguishes them. Q07 stays "strong, not unique" (shared knot grid). Q08 is earnable **within class only** — the plan says this correctly; do not let it drift. **Strengthen the ablation**: three arms (A: Sangam windows; A′: Sangam + Taranga's monthly waveform; B: A′ + segments/term composition), several class/chapter pairs including an ordinary undramatic period, a pre-registered rubric keyed to Q06's own distinction text, and a named judge. Sangam+Taranga is the right *stronger* baseline: Taranga supplies a monthly shape (so "Sangam has no shape" stops being the argument) but no per-term composition and no null — exactly the gap B must earn.

  **Classical basis.** An ācārya's framing: a window list is a register of *sparśa* (contacts); the segment is the **graha-cāra** — the whole course: entry, approach, culmination, exit. Gochara is classically read as a course, not a threshold-crossing, and daśā is read as a continuous state: BPHS Vol 2 Ch. 47 (Effects of Daśās) judges a *period's* quality from the lord's condition "at the commencement of the Dasa" (vv 5-6), and Ch. 52-60 read antardaśās as sustained climates, not events. Thresholding a course at q_e amputates exactly the approach/separation gradient an ācārya reads. The honest unique sentence: *"the window list names the storms; the field shows the season's daily weather and who brought it — including the days no storm came."* **[D]** BPHS Vol 2 Ch. 47 vv 5-6, Ch. 51-63 (corpus-verified); **[J]** the cāra/sparśa framing.

  **Engineering basis.** Sangam windows carry `mode`, `witnesses`, `tier_basis`, `independent_current_count` — enough that a lax ablation would declare "mechanism conveyed" and park a real capability, or a lax judge the reverse. The falsifier must be operationalized or it is §N.7 item 5 (prose ≠ test). Taranga: `kala_taranga` chart × month × scope, 1950-2100 — monthly shape, no terms, no null (Strategy §6.1 L3-A18).

  **Cost.** The ablation as sharpened: a few days of fixture builds + a rubric session; cheap relative to P1.

  **Falsifier.** Arm A′ conveys the driver change (which classical operand moved), not merely which witnesses, across the pre-registered pairs ⇒ the segment earns nothing; park-with-preservation; P1 never funded.

  **Not decided here.** Whether the judge is the native, an independent reviewer, or a scored ensemble — that is the native's to name before the test runs.

  **Confidence.** High that Q06-narrowed is the right claim **[J]**; high that the current ablation text is under-specified **[P]**; medium that B wins the ablation — the honest prior is genuinely uncertain **[U]**.
***
  ## K-2 — The model form, term by term, from an ācārya's chair

  **Recommendation — (a) λ⁰ actuarial constant: tolerable engineering departure, correctly tagged; the constant-over-life part is the weak joint.** A chart-independent base rate is the right "null Jyotiṣa" floor *if and only if* it stays a tagged structural prior (Product §5.2 keeps structural prior, classical prior, and calibrated claim distinct). Age-variation has both actuarial and classical warrant; E3 is justified.

  **Classical basis (a).** No classical text gives an event base rate — so λ⁰ must never be *called* classical. But age-conditioning exists: Naisargika/Nisarga daśā is enumerated in BPHS Vol 2 Ch. 46 (vv 6-11, 201-202) and Saturn's maximal naisargika years at Vol 1 Ch. 3 v 48; the life-stage doctrine (childhood/youth/old-age thirds) appears in Vol 2 Ch. 72, and the āyus taxonomy (8/20/32/64/120) in Vol 1 Ch. 43 vv 52-54. So a constant λ⁰ is a modeling convenience sitting on a real classical intuition that life-stage conditions manifestation. **[D]** corpus-verified.

  **Recommendation — (b) noisy-OR promise with adṛṣṭa floor: the OR-form is defensible; the floor is an honest named residual; the sign loss is a distortion and the deepest classical defect in the model.** Two distinct wrongs compound: `bodha_pratijna` 'denied' rows become weak *positive* `class_signification` edges (status dropped at `stage2_promise.py:474-516`), and cancelled CGM edges vanish entirely (`cancelled_flag = FALSE` filter at `:336-341`). Denial-as-weak-support and cancellation-as-absence are both contrary to niṣedha/bhaṅga doctrine.

  **Classical basis (b).** Concordance-as-OR: multiple independent yogas each sufficing for a result is the texture of BPHS's yoga chapters — a defensible formalization **[D]** (general), **[J]** (the noisy-OR independence assumption — classical yogas are not conditionally independent). The floor: *adṛṣṭa* is precisely the residual no visible combination explains; a 5% floor *named* adṛṣṭa and never allowed to dominate is defensible **[J]**. Sign: BPHS Vol 1 Ch. 9 ("estimate the evils *and the checking factors thereof*") and Ch. 10 ("Antidotes For Evils") make cancellation a first-class signed operation; a denied indication is not a small promise **[D]** corpus-verified.

  **Recommendation — (c) the clock term: graded, depth-discounted, continuous relevance is a defensible formalization — but it is blind where the texts are explicit.** `relevance()` is graph reachability of the lord to the class, signed via suppression, tanh-bounded, MD>AD>PD discounted. Two corpus-verified classical conditions it ignores: (i) **the daśā lord's dignity/placement at the commencement of the daśā** — BPHS Vol 2 Ch. 47 vv 5-6: favourable if the lord is in lagna/exaltation/own/friend's sign, unfavourable in 6/8/12 or debilitation/inimical — i.e., the lord's condition *at the time*; (ii) **transits during the antardaśā** — Ch. 57 vv 24-27A. Bhāva-placement-relative-to-kāraka enters adequately through L2 routes; do not duplicate it in the clock. PrD absence is honest; the dead `d:PrD=0.15` weight is harmless. Sandhi: inherit L1's `sandhi_flag` + hour grain (seam repair); and note the ±3-day band has **no corpus anchor** — daśā-sandhi as junction doctrine is NOT in the admitted corpus; keep it a declared engineering band, never cite doctrine for it, and if a period-scaled sandhi is wanted, that needs source admission.

  **Recommendation — (d) additive log-linear covariates: a legitimate first-order form that becomes a distortion exactly where the tradition is loudest.** "Transit Saturn over the MD lord" is NOT "transit Saturn elsewhere" in this corpus: Ch. 47 vv 5-6 and Ch. 57 vv 24-27A make gochara conditional on the running period. E5 (x·r interaction) is justified with those citations; flag the identifiability cost to `mi_bhara` (parameter count vs ~57 events).

  **Recommendation — (e) multiplicative thinning, route-scoped, inhibiting-only: the form is right; the missing half is ariṣṭa-bhaṅga; and there is a live semantics split the documents do not disclose (see K-8 #1).** Route-scoping is *more* disciplined than common practice. Protection: Ch. 9's "checking factors" and Ch. 10's antidotes are the ariṣṭa-bhaṅga basis; E6's channel is a suppression-release, not a negative ρ.

  **Ranking the plan's nine gaps by classical weight (my re-ranking):**
  1. **[Missing from the plan's list] The G3 suppression-semantics split** — correctness, ranks above all (K-8 #1).
  2. **Unsigned cancellation** (plan #3) — doctrinal core; *model change*, anchored Ch. 9-10.
  3. **Missing varṣa/annual layer** (folded into plan #1) — a whole classical limb; *model change requiring source admission* — no Tājika text is in the corpus; `ka_tithi_pravesha` needs its own qualification first (the plan's C8 is right).
  4. **AV gating empty** (plan #2) — *seam*, but gated on the corpus's bindu/rekha polarity inversion (Vol 1: bindus auspicious; Vol 2: dots inauspicious) and on the fact that **kakṣyā is not in the corpus** — only SAV thresholds exist (Ch. 72 vv 3-5: >30 favourable, 25-30 medium, <25 adverse). Reconcile polarity before any β is pointed at it.
  5. **Daśā×gochara additivity** (plan #6) — *model change*, anchored Ch. 47/57.
  6. **Layer's vedha/moorti unread; two verdicts per instant** (plan #1) — *seam*, with the citation correction of K-8 #2.
  7. **λ⁰ age-flatness** (plan #5) — *model enrichment*, anchors above.
  8. **No ariṣṭa-bhaṅga** (plan #7) — *model change*, anchored Ch. 9-10.
  9. **Sandhi not inherited** (plan #4) — *seam*; band itself doctrine-free.
  10. **Null single-witness** (plan #8) — *method change* (K-4).
  11. **Lattā** (plan #9) — *partly stale*: `bg_phaladeepika_latta` (8 rows) exists at L0; see K-8 #3.

  **Cost.** Seams: small (one stage packet each). Model changes: each a new `config_pin`, a cited source, a weights version, and — per the plan's own discipline — ablation-gated.

  **Falsifier.** For each term: the A2 zero-clock test (the only classical operand must do work); a denied-route fixture (sign); a Ch. 47-style fixture (lord dignity at commencement flips the chapter); an unnamed-obstruction fixture (G3).

  **Not decided here.** The functional form of the interaction (product in log space vs gated); the bhaṅga channel's exact placement; naisargika-vs-actuarial weighting inside E3.

  **Confidence.** [D] for the Ch. 47/57/9-10/46/72 anchors (corpus-verified); [J] for the re-ranking; [U] for Phaladīpikā/Sarvārtha Cintāmaṇi specifics (not in corpus).
***
  ## K-3 — The covariate set and the varṣa layer

  **Recommendation.** The twelve are a defensible v0 set — the plan is right that this is a classical vector, not "transit intensity". What an ācārya would insist on, in order: (i) **the daśā lord's own transit state/dignity during the period** (Ch. 47 vv 5-6 — the single strongest omission; it is neither x1/x2 contact geometry nor clock relevance); (ii) **AV gating live**, same source as Sangam E2, after the polarity reconciliation (K-2 #4); (iii) **sade-sati as a named duration arc** — its classical identity is a 7.5-year *arc*, not a contact; x1 sees the peak but nothing names the arc — corpus anchor is only KP Reader Vol 5 (modern), so admit it as a declared convention, not as cited classical doctrine **[U]** for a classical source; (iv) **lattā via the existing `bg_phaladeepika_latta`** with per-kind qualification, not corpus extraction; (v) **the varṣa layer as applicability gates** — Sudarśana is anchored (BPHS Vol 2 Ch. 74, sole corpus occurrence); **Kota has no corpus occurrence**; muntha/varṣeśa need a Tājika source admission — none exists in the corpus; tithi-praveśa rides `ka_tithi_pravesha` after its own qualification; (vi) transit-over-natal-lord and transit-over-daśā-lord as *named contacts* (these are the interaction terms of K-2(d), not new covariates).

  **Consume the layer's assets: yes, exactly as the plan proposes** — one verdict per instant, per-`vedha_kind` qualification (house_vedha → `applied`; sarvatobhadra/lattā → `unqualified` until separately qualified), the internal derivations demoted to one-generation cross-checks then retired. Add one note the plan misses: **moorti is currently split across two term families** — svarṇa/rajata/tāmra are modifier dummies (x5-x7) while loha-moorti's primitive polarity is `obstructive` (`stage1_symbolization.py:229-230`), i.e., the same doctrine acts as both modifier and suppression. When `ka_moorti_nirnaya` is ingested, keep one moorti family with declared term placement.

  **Orthogonality (L3-U02).** Genuinely distinct origins: x1 vs x2 (Moon vs Lagna reference — the dual-reference convention itself is anchored at BPHS Vol 1 Ch. 12 v 11: "base the effects on the Moon also as are applicable to the ascendant" **[D]**), station, panchanga affinity. **Same origin twice**: `dual_reference_agreement` = min(x1,x2) — declared derived, fine, but it must never count as an independent witness (the code's own docstring agrees); `eclipse_contact` = syzygy × flag — a product of x10 with a label, same-origin; sandhi shares its boundary origin with the clock ladders (mild). β-fit collinearity among x1/x2/x3 is `mi_bhara`'s to declare, not Kshetra's.

  **Cost.** Ingestion packet + cross-check generation; sade-sati arc: one primitive builder; varṣa: gated on source admissions upstream of Kshetra.

  **Falsifier.** Two verdicts for one instant after ingestion ⇒ fail; polarity flip on the AV gate changes the window set in the predicted direction; a sade-sati arc that never alters any served row ⇒ the covariate does no work (A2-style).

  **Not decided here.** Which AV bindu/rekha convention the layer ratifies (hub-level); the Tājika source admission.

  **Confidence.** [D] Ch. 12 v 11, Ch. 74, Ch. 72 thresholds; [P] the moorti term-split (source-verified); [U] Kota/muntha/lattā-as-doctrine; [J] the insistence ordering.
***
  ## K-4 — The null: is "surprise vs a re-phased sky" a Jyotiṣa claim?

  **Recommendation.** Yes, with its scope stated exactly: a low `null_p` licenses *"within this chart's fixed natal structure and daśā ladder, the actual phase of the transit stream carries timing information that no rigid re-phasing of the sky reproduces"* — in classical terms, **the gochara-krama (the sky's actual order) is load-bearing, not merely the daśā texture**. It does NOT license: event probability, reliability, mechanism truth, or daśā-vs-gochara attribution — and it currently says nothing about the ladder, which is held fixed. The **two-factor null is the right next step, but as specified it delivers two marginals, not the conjunction**. The actual "daśā AND gochara concur" claim needs the **third arm: both shifted independently** — observed λ exceeding the transit-only null, the ladder-only null, *and* the both-shifted null is the alignment-concurrence statement; the ladder-shift oracle is its own enumeration (piecewise ladder — enumerable), not the brief's transit-shift one. `q_threshold` (95th pct of pooled replicate λ): it is a **detection screen, not an exceedance bar** — the bar is the duration-bucketed `max_stats`; the two should be named as such wherever served, because a pooled pointwise quantile conflates slow clock variation with sharp envelope peaks (acceptable for screening since the test is on window maxima). The exhaustive 36,525-shift enumeration is the right independent oracle — and it matters more than the brief says: at R=1024 the shift step is ~35.7 days, so narrow features (1.5-3-day syzygy/station bands) are coarsely sampled in the null; the enumeration, never the estimator, settles the grid question. P1's "full shift set" must mean the declared R-grid (brief is right).

  **Classical basis.** The concurrence claim is the tradition's own: Ch. 47 vv 5-6 (period quality from the lord's condition) conjoined with Ch. 57 vv 24-27A (transit results *during* the antardaśā) is precisely "daśā and gochara concur" **[D]**. What an ācārya wants *in addition* is not more permutation machinery but the held-out-event check — and that belongs to `mi_bhara` under the Circularity Guard; Kshetra's restraint here is correct, not a gap **[J]**. Optional fourth arm [J]: re-phase supportive and obstructive envelopes separately, to test whether *vighna timing* (not just benefic timing) is load-bearing.

  **Engineering basis.** The null's current independence from RNG, its C/E decomposition (2·n evaluator calls), and the F-01 grid correction are sound. But note the null inherits the G3 semantics split (K-8 #1): replicates are built on `FieldEvaluator.ln_lambda`, which does not route-filter — **the null is computed under chart-wide suppression while the served field is route-scoped**; wherever an active obstruction is not route-named, `null_p` compares two different models and is biased (replicates depressed ⇒ p optimistically small). The G3 fix is a precondition for the null contract's validity, not an enrichment.

  **Cost.** Third arm ≈ one more S5-scale pass (ladder shifts are cheap); oracle: a reduced-horizon enumeration, once.

  **Falsifier.** A class dominated by C(t) shows no discrimination under the transit null (declared in the brief — keep); a synthetic known-λ process: the three-arm null must recover the planted alignment arm-by-arm.

  **Not decided here.** The multiple-comparison posture across 10 duration buckets × classes (propose: declared, not invented — a native ratification).

  **Confidence.** [D] the concurrence doctrine; [P] the G3-null mechanism (source-verified); [J] the three-arm design; [U] bucket-multiplicity policy.
***
  ## K-5 — Baseline honesty and the 6-vs-25 configuration

  **Recommendation.** Ratify the plan: **the calibrated 6-class run is the product**; the 25-class run is substrate until priors are sourced. Serve shape-only classes **within-class rank only** — and upgrade A1 from "untested" to what it actually is: **provable by construction**. λ⁰ enters as a constant multiplier of λ(t); every replicate scales identically; therefore q_threshold, window bounds (α+γ(t−t_i)=ln q), and window maxima all scale by the same constant, and `null_p` — a rank statistic — is invariant up to float64 rounding. The honest statement is "invariant by construction; asserted on a fixture," not "should be invariant." Absolute fields (`expected_count`) stay suppressed on synthetic rows per the `stage8_spec.py:136` precedent. **A demographic life-table λ⁰(t) is a legitimate structural prior, not a category error** — provided it is tagged structural, never merged into classical promise, and never silently double-counts age effects the classical operands also carry (declared at fit time, mi_bhara's lane). Product §5.2's tier discipline is exactly this.

  **Classical basis.** The age-shape warrant: naisargika daśā (Vol 2 Ch. 46 vv 201-202), life-stage thirds (Ch. 72), āyus classes (Vol 1 Ch. 43 vv 52-54) **[D]**. The *values* remain actuarial — the corpus supplies no rates; the classical warrant justifies the shape's existence, not its numbers **[J]**.

  **Engineering basis.** 6-of-25 sourced; the pinned four-coordinate selection at `stage4_field.py:1155-1168` is the right pattern; `baseline_rate` raising on a non-positive count is the right refusal. The A1 fixture: one aggregate query + one hash compare.

  **Cost.** A1: negligible. E3: a sourced life table per class (upstream lane) + new weights version + new generation.

  **Falsifier.** Flip one class calibrated↔shape-only: tags change; λ geometry, windows, `null_p` byte-stable (already in the proof matrix — keep, with the invariance proof-sketch attached).

  **Not decided here.** Who sources the 19 priors and on what citation standard (the documents say "Pūrṇa P4" without defining it — K-8 #9).

  **Confidence.** [P] the invariance mechanism (form verified in `hazard.py`/`stage5_null.py`/`integrator.py`); [D] the age-warrant; [J] the legitimacy call.
***
  ## K-6 — The ecosystem: upstream and downstream guarantees

  **Recommendation.** The guarantee lists are strong; add: **(In)** (a) a **class-set reconciliation receipt** — the 25 discovered classes vs the 27 ontology classes — as a standing detector, not a §10 "one query" item; (b) `kala_gochara_authority` gets an owner and the `'v1'` COALESCE default is removed — a COALESCE to a literal is precisely the implicit fall-through Strategy §4 step 3 forbids; (c) the **G3 convergence guarantee**: field path ≡ evaluator path suppression semantics, tested, before any null is served (K-8 #1); **(Out)** (d) served rows carry `weights_version`/`x_schema_version` alongside the listed fields (comparability); (e) a **standing detector for `null_resolution` = 1/R** against the register — a prose delta rots (§N.8); (f) `mi_bhara` must *consume* `baseline_is_synthetic`: synthetic classes excluded from absolute-skill scoring, admissible to rank-based skill only.

  **σ_T: yes — L1 birth-time precision is the right admitted artifact.** Birth-time precision is a property of the *record* (event-free by construction). A rectification posterior is **never admissible into the event-free prospective field**: it is LEL-fitted (event-derived) and doubly circular — boundaries fitted to the LEL would later be evaluated against the same LEL. It is admissible only into a purpose-gated retrospective comparison arm (L3-Q11) as a separately admitted artifact. The interim `default_120s_assumption` + F06 `unavailable` branch is correct and already exists (`uncertainty.py:170-173`).

  **Node disposition (b): right as the interim — with one correction the plan omits.** "Derive mean at read" must land **in the L0 ephemeris service**, with `node_mode`/`epoch_convention` declared on the row beside the existing `ayanamsha_id` (the schema's own pattern). If Kshetra derives mean-node internally, that is a new §N.5 shadow — the identical defect class as its internal vedha/moorti re-derivation. Under a mean ruling, L1's natal facts remain the authority (the plan's §6a.1(i) is exactly right and should govern §7's wording).

  **Expose the per-term decomposition downstream: yes.** First consumers: `explain.ts`/`kala_story` (experience 4 — the mechanism prose), then `mi_bhara` as *separate* feature families (clock-skill vs modifier-skill vs suppression-skill — a materially better calibration target than one pooled skill). Only after the tag rides every row.

  **Cost.** Receipts/detectors: small standing tests. L0 row-level frame: one additive migration upstream.

  **Falsifier.** A chart with 25 discovered vs 27 ontology classes fails the receipt loudly; a build binding to a manifest-absent snapshot refuses; a synthetic class reaching L5 unlabelled fails the U10 sentinel.

  **Not decided here.** The hub node ruling itself; the L1 amendment scope for birth-time precision.

  **Confidence.** [P] the COALESCE/authority mechanics; [J] the L0-placement of the mean derivation; [D] n/a (plumbing), except the §N.5 principle.
***
  ## K-7 — Technical: identity, publication, efficiency order, serving

  **Recommendation.** **P6 → P2 → P1 is right**, and the reasoning (pin rule ⇒ publication preserves capital) is sound. Three contract additions: (1) the P1 equivalence contract must pin **`_EXCEEDANCE_REL_TOL` (1e-12) and the shift-grid construction itself** (`range(1,R)`, δ = r·H/R) — both are semantics, and neither currently appears in the equivalence text (brief §4.6); (2) U11's material fields add `weights_version`/`x_schema_version`; (3) U10's interim behavior should be **refusal, not a degraded bind**: L5 binds via the manifest with content-hash verification, `ORDER BY built_at DESC`, and when no manifest exists it reports not-built (the current unordered `LIMIT 1` on the canonical chart binds to a dangling id — a silent wrong answer, worse than none). **Physical representation: keep the full-horizon lossless segment store.** It is not a "dense sample"; it is the *definition* of the field — log-linear segments with closed-form integrals, monotone-per-segment peaks at breakpoints, `expm1`-stable arithmetic, and a `refinement_residual` bound field (`integrator.py:1-59`, `contracts.py:143-160`). Strategy §5's "qualified compact substrate with explicit refinement semantics" is the right model for **serving projections**, not for the store; P2's direct segment reader is that answer. **Do not dedupe breakpoints** — 343k segments/class is dense, but thinning the knot set is exactly the "coarser grid as optimisation" the binding constraints forbid. Storage cost is a P2/P6 problem.

  **Cost.** Contract text edits; U10/U11 packet work (Pūrṇa-implemented, L3-tested — correct split).

  **Falsifier.** P1: `max_stats`/`q_threshold`/`null_p` bit-equal per bucket, *including* a planted tie at the exceedance tolerance. U10: a build with no manifest leaves L5 unbound and loud.

  **Not decided here.** Whether P6's "optional exact complement" is needed in v1 (declare at packet time); the manifest schema itself (W7).

  **Confidence.** [P] throughout; the representation judgment is [J] but anchored in Strategy §5's own three-representation rule.
***
  ## K-8 — Defects in the two documents

  1. **Omission — the G3 suppression-semantics split (both documents).** *Section:* brief §3 rank list, plan §2 gap list. *What is wrong:* neither discloses that `FieldEvaluator.terms_at` (`stage4_field.py:866-873`) passes **all** active obstructions into `hazard.evaluate` with no route filter, while `layer1.project_layer1` (`:143-159`) applies SM-R-7 Option B — and `dhara_null.py:145-163` builds every replicate through the **unfiltered** evaluator path. The served field is route-scoped; the null and any re-evaluation are chart-wide. Pūrṇa's G3 is therefore not an open wording question: **the null is computed under a different model than the field it tests**, biasing `null_p` low wherever an active obstruction is not route-named. *Replacement:* a §3 rank-0 defect; hoist the `suppressed_keys` filter into `hazard.evaluate` (passed explicitly), add a proof row "an obstruction named by no route's `suppressed_by` is inert," and gate the W7 null layer on the field/evaluator byte-equality test.
  2. **Miscitation — "ka_vedha_gochara (BPHS Ch.29 …)" (plan §2 item 1, §6a).** In the admitted corpus, BPHS Ch. 29 is **Bhāva Padas (Ārūḍha)**; BPHS has no gochara chapter; vedha appears only as **translator commentary** at Ch. 31 (Argala). The actual admitted source chain is L0: `bg_phaladeepika_vedha`/`bg_vedha_malefic_scale` (Phaladīpikā PG353, ADJUDICATION-11, per `bg_phaladeepika_vedha.py`). *Replacement:* cite the L0 disclosure and its tier; strike "BPHS Ch.29" wherever it appears.
  3. **Internal contradiction + staleness — lattā (plan §2 item 9, §5 E8 vs §6a).** §2/E8 say lattā rules are absent and need "corpus extraction"; §6a lists `latta` as an existing `ka_vedha_gochara` vedha_kind. Fact: `bg_phaladeepika_latta` (8 rows) exists at L0 and feeds `ka_vedha_gochara`. Phaladīpikā is not in the corpus, so "extraction" cannot be the path anyway. *Replacement:* lattā = present at L0 at a disclosed tier; E8 becomes "admit `bg_phaladeepika_latta` with `unqualified` qualification"; the `stage1_symbolization.py:357-362` comment is stale and should be re-dated.
  4. **Under-operationalized falsifier — the ablation (brief §4.1).** No judge, no rubric, no pre-registered pass bar, one class, one chapter pair, weakest admissible baseline. §N.7 item 5. *Replacement:* K-1's protocol.
  5. **Underclaim — A1 (brief §4.1, §3 Non-claim).** "Rank *should* be invariant; never run" — invariance is exact by construction (K-5). *Replacement:* proof-sketch + fixture assertion.
  6. **Editing artifact + self-hedge violation — plan §7 item 7.** A duplicated fragment ("…lean **(b)**. applies. This plan and two peer streams lean **(b)**…"), an e6/fc peer inconsistency with §6a.1, and the pāda move presented as "verified … measured fact" while §6a.1(i) rules the true side an author computation that must not become authority. *Replacement:* carry the §N.5 hedge into the recommendation sentence itself.
  7. **Omission — owner of the mean-derivation in node disposition (b) (plan §6a, §7).** "Derive mean at read" without saying *where* invites a Kshetra-side shadow. *Replacement:* L0 service, frame declared on the row (K-6).
  8. **Citation-precision defect — `mi_bhara.py:403` (brief §2.4).** By the brief's own path convention the bare name resolves under `services/ka_kshetra/`; the file is `pipeline/orchestrator/writers/mi_bhara.py`. In a document whose thesis is citation discipline, foreign files need full paths. (The bind itself verifies at that file.)
  9. **Undefined load-bearing citation — "Pūrṇa P4" (brief §4.2, plan §3.1, §7).** Used to assign the 19-prior lane, never defined in either document, and collides with Strategy §5's P4 (Sangam redesign). *Replacement:* define once or rename.
  10. **Overclaim — plan §2 item 5 "…the entire age structure must be carried by promise and clock terms, which cannot."** A multiplicative field *can* carry age shape; what it cannot carry is an age-shaped *level* independent of classical operands. *Replacement:* "can in shape, not in level; absolute expected counts by age are distorted."
  11. **Missing falsifier arm + missing contract pin — plan §5 E2 / brief §4.6.** E2's two-factor null omits the both-shifted arm (the actual "concur" test) and a ladder-shift oracle; P1's equivalence contract omits `_EXCEEDANCE_REL_TOL` and the grid construction. *Replacement:* K-4 and K-7 texts.
  12. **Missing comparability fields — brief §4.7.** U11 material fields omit `weights_version`/`x_schema_version`. *Replacement:* K-7 (2).
  13. **Overclaim — brief §4.1 Q07 proof ("removing a bridge removes a route… the inference must disappear").** With noisy-OR over K=5 routes, bridge removal may attenuate without removing. *Replacement:* the proof row asserts disappearance, or attenuation is declared a failure of the proof (not of the asset).
  14. **Superlative without audit — plan §0 "the most disciplined in L3."** No comparator audit is cited. *Replacement:* the brief's own defensible wording: "against VA §10.2, otherwise unusually clean."
***
  ## K-9 — The offensive question

  **Recommendation. The missing comparison operator: window-versus-counterfactual-self — "what the vighna costs."** For every window, serve λ̂(t) = λ(t) with the suppression term removed — derivable today from the stored per-segment `suppression_term_start` (ln λ − ln S), no new storage. Consumer: **`explain.ts` / `kala_story` (experience 4)**, answering the one L3-Q nobody owns: **Q04 — "why can activity coexist with strain?"** A chapter whose peak is clock-driven with suppression active ("the period is strong *despite* the obstruction, and here is the magnitude it is costing") reads completely differently from a chapter weak *because* of suppression — and that is a distinction an ācārya makes constantly and no current surface can show.

  **Classical basis.** Vedha is a *suspension* of an otherwise operative transit — the question "how much is being suspended" is intrinsic to the doctrine (L0-disclosed Phaladīpikā vedha rules, PG353/ADJUDICATION-11; the corpus's Ch. 31 translator note even records viparīta-vedha as vedha-cancellation); ariṣṭa and its checking factors (BPHS Vol 1 Ch. 9-10) frame strain and relief as two measurable quantities, not one net score. **[D]** Ch. 9-10; **[D-via-L0-disclosure]** the vedha rules.

  **Cost.** A query over existing columns in the U11 projection; one derived material field; no model change, no new pin.

  **Falsifier / test.** Relevant-influence: zero the suppression term and rebuild — the counterfactual series must equal the recomputed field byte-for-byte; plus a planted window whose peak is suppression-dominated must surface a large delta (sentinel-shaped).

  **Not decided here.** Whether the counterfactual is ever shown for synthetic-baseline classes (recommend: rank-qualified only); the served name.

  **Confidence.** [P] the derivability (columns verified in brief §4.2 and `hazard.py`); [J] that Q04 is the highest-value unowned question; [U] consumer-side presentation.
***
  ## Overall verdict

  **Astrological (value proposition).** The skeleton is genuinely Jyotiṣa: a daśā-lord clock scored against stored causal routes, a classical covariate vector (dual-reference concordance, moorti, station, syzygy, panchanga), route-scoped vighna, an honest refusal to invent confidence. That is more disciplined than most human readings. But the flesh is missing where the tradition is explicit: the clock is blind to the daśā lord's dignity at the time (BPHS Ch. 47 vv 5-6, corpus-verified), gochara is additive where the texts are conditional (Ch. 57 vv 24-27A), denial reads as weak support against the niṣedha/bhaṅga doctrine (Vol 1 Ch. 9-10), the annual limb is absent with no Tājika source admitted, and the AV gate is an empty slot over a corpus whose two BPHS volumes invert bindu/rekha polarity. The plan's §2 ranking is right in spirit; I re-rank sign loss above the transit-suite and add the G3 split above everything. As formalized Jyotiṣa the hazard form is defensible *once* sign, interaction, and the annual gate land — all correctly gated behind the ablation.

  **Technical (value proposition).** The arithmetic discipline is real: pinned selections, raising on missing priors, provenance that reconciles by construction, a hash-replayable closed-form segment representation, a deterministic null with a corrected denominator. The defects are exactly where the documents say — seams and publication — **plus one they do not say**: the field and its own null implement two suppression semantics (K-8 #1), which quietly invalidates `null_p` wherever they diverge. That must rank above the synthetic-baseline tag, because the tag is a qualification defect and this is a correctness defect in the asset's only significance test. The staging (seams → ingestion → publish → capability → ablation-gated enrichment) is the right shape; two corrections: run the sharpened ablation before paying the S1-ingestion cost beyond a cross-check, and split S1 ingestion into its own packet. Re-scoping to the calibrated 6-class configuration at W7 and holding the 8.57M rows by refusal are both correct.

  **Cross-question coherence check.** The plan is internally coherent on the big arcs; the seams are: (i) G3 (K-2e/K-8#1) gates the null contract (K-4) and therefore Q08 — it must be fixed before the S5 packet means anything; (ii) A1's promotion to by-construction (K-5) strengthens Q08's within-class claim (K-1); (iii) the vedha citation correction (K-8#2) is a precondition for the S1 ingestion packet (K-3) and for §6a's shared-vedha ruling; (iv) U11 fields (K-7) must include what U10's sentinel and Q05 comparability require (K-6); (v) the node ruling (K-6) sits upstream of S0/S1 values and the W7 build's identity; (vi) the ablation (K-1) gates §5's E1-E8 and P1 — so funding S1 ingestion in stage 3 before the ablation runs in stage 6 spends money the park-disposition might waste; the cross-check-first ordering resolves it. No contradictions beyond K-8 #3 (lattā) and #6 (§7).

  **Three things to ask the native before ruling.**
  1. **G3:** which suppression semantics is the contract — route-scoped Option B (the docstring, my recommendation) or chart-wide (the evaluator)? And will you require the field/evaluator byte-equality test as a precondition for serving any `null_p` from the W7 build?
  2. **Product configuration and the prior lane:** do you ratify the calibrated 6-class run as the product with shape-only classes served rank-only — and what exactly is "Pūrṇa P4": its owner, its citation standard for the 19 remaining priors, and its relation to Strategy §5's P4?
  3. **The ablation's judge and timing:** who reads the arms, under what pre-registered rubric, with Taranga admitted as a third arm — and should the ablation run *before* the S1-ingestion packet so a failed ablation parks the asset without that spend?

  **Ranked top-ten elevations I would put before the native.**
  1. **Fix the G3 suppression-semantics split** — hoist the SM-R-7 filter into `hazard.evaluate`; field ≡ evaluator ≡ null. *Why:* the served model and the tested model currently differ. *Classical basis:* n/a (correctness); preserves vedha's route discipline. *Cost:* one function change + tests; new `config_pin`. *Falsifier:* an active obstruction named by no route moves ln λ ⇒ fail.
  2. **Thread `baseline_is_synthetic` to `kala_field`** (+ one migration, 1071+). *Why:* calibrated vs fabricated hazard must be distinguishable on the row (F04/F06). *Cost:* additive nullable column. *Falsifier:* proof-matrix positive/negative rows.
  3. **Replace the σ_T read; scope `chart_dashas` by ayanāṃśa + third sort key.** *Why:* §6.2 firewall + the QX `rows[0]` ambiguity in the same chain. *Cost:* small. *Falsifier:* five-copy disagreement fixture selects the pinned copy; no admitted artifact ⇒ `default_120s_assumption`/`unavailable`.
  4. **S1 ecosystem ingestion with one verdict per instant** — `ka_vedha_gochara`/`ka_moorti_nirnaya` in, internal derivations as one-generation cross-checks then retired; per-`vedha_kind` qualification. *Classical basis:* Phaladīpikā via the L0 disclosure (PG353, ADJUDICATION-11) — citing that, not "BPHS Ch.29". *Cost:* one packet + a cross-check generation. *Falsifier:* two verdicts for one instant ⇒ fail.
  5. **Fill `av_kaksha_gate` from the same AV source as Sangam E2** — after reconciling the corpus's bindu/rekha polarity inversion; kakṣyā unanchored in corpus, SAV thresholds only (Ch. 72 vv 3-5). *Cost:* S1 row + polarity detector. *Falsifier:* polarity flip moves the window set in the predicted direction.
  6. **Signed promise/cancellation (L3-U01 downstream half)** — sign + occurrence/condition on edges/routes; natural edge key first (closes the routes QX). *Classical basis:* BPHS Vol 1 Ch. 9-10 (evils and their checking factors/antidotes). *Cost:* S2 packet + upstream half. *Falsifier:* a denied route must depress, never weakly support (Q07 bridge-destruction row).
  7. **L3-U10: L5 binds via manifest + content hash; reads the tag; refuses when no manifest.** *Why:* the unordered `LIMIT 1` currently binds L5 to a dangling id. *Cost:* interface packet. *Falsifier:* synthetic class reaches L5 still labelled; manifest-absent ⇒ loud refusal.
  8. **L3-U11 `query_field_trajectory` + L3-owned sentinel**, with `weights_version`/`x_schema_version` and the tag on every row. *Cost:* Pūrṇa implements, L3 tests. *Falsifier:* the §4.7 sentinel.
  9. **Three-arm null + exhaustive-shift oracle** — transit-shifted, ladder-shifted, both-shifted; contract prose on the row. *Classical basis:* daśā×gochara concurrence (Ch. 47 vv 5-6 + Ch. 57 vv 24-27A). *Cost:* ~2-3× S5. *Falsifier:* a planted-alignment synthetic is recovered arm-by-arm; a C(t)-dominated class declared undiscriminating.
  10. **Run the sharpened ablation early; promote A1 to by-construction; then E1** (mechanism fingerprint from the four stored columns) as the first consumer-facing derivative — with E5 (interaction, Ch. 57) and E7 (varṣa gate, Ch. 74 + Tājika admission) first in the post-ablation queue. *Falsifier:* Arm A′ conveys the driver change ⇒ park-with-preservation, P1 never funded.

  One boundary I respected throughout: every threshold, weight, and band mentioned above (P_FLOOR, depth weights, ±3-day sandhi, R=1024, q=0.95, ρ bounds) is a **proposal already pinned in code or in these documents for the native to ratify** — none is asserted here as classically sourced fact, and where the admitted corpus could not support a doctrine (kakṣyā, Kota, daśā-sandhi, Tājika, Phaladīpikā-as-text), I have said so rather than borrow authority from outside the corpus.

