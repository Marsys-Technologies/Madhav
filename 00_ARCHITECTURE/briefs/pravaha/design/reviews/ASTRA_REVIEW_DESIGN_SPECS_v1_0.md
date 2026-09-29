---
artifact: ASTRA_REVIEW_DESIGN_SPECS
version: "1.0"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra — independent adversarial review"
date: "2026-09-29"
verdict_specs: REWORK
verdict_protocol: REWORK
reviewed_document: "design/GOCHARA_DESIGN_SPECS_v1_0.md"
reviewed_document_sha256: "c87919dbe06fc6828ee719805143a319898b6ebd4c0ae502d67deb14a5debea0"
authority: "Review only; authorizes nothing."
---

## 1. Verdict

**[J] Design specs: REWORK. Evaluation protocol: REWORK. Do not freeze the reviewed versions.**

[S][J] The specs preserve much of the sealed architecture: union-based admission, explicit frames, physical-contact deduplication, interval vedha, angular activity, coverage disclosure, and manifest-driven publication. They do not yet constitute an unambiguous build contract. Several load-bearing repairs lack guards; source qualification and scoring permission remain conflated; some normative examples contradict their own contracts.

[S][J] The protocol requires substantive correction. Its event inventory, timing denominator, baseline hit count, observation horizon, and false-positive derivation disagree with the supplied evidence. The disclosed premature scoring should remain recorded, but the baseline must be recomputed under the corrected, reviewed protocol.

[S] All twelve packet documents were read. Their SHA-256 hashes were recomputed with `shasum -a 256` and remained unchanged between the initial and closing checks. The reviewed spec matches the requested post-erratum hash.

## 2. Conformance table

[S] Citation abbreviations below identify exact files; a suffix such as `DS:186–188` denotes repository line numbers.

| Key | File |
|---|---|
| D | [sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md) |
| DS | [design/GOCHARA_DESIGN_SPECS_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_0.md) |
| A | [design/GOCHARA_PLAN_V3_AMENDMENT_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_PLAN_V3_AMENDMENT_v1_0.md) |
| F | [design/L3_FAMILY_COORDINATION_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/L3_FAMILY_COORDINATION_v1_0.md) |
| N | [NATIVE_DECISION_PACKET_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/NATIVE_DECISION_PACKET_v1_0.md) |
| C | [design/CORPUS_READS_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/CORPUS_READS_v1_0.md) |
| E | [sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md) |
| P0 / P1 / P2 | [protocol v1.0](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTOCOL_v1_0.md) / [v1.1](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTOCOL_v1_1.md) / [v1.2 draft](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTOCOL_v1_2-DRAFT.md) |
| B | [measurement/BASELINE_3_0_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/BASELINE_3_0_v1_0.md) |
| O | [design/GOCHARA_TEST_ORACLES_v1_0.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_0.json) |
| LR | [measurement/LEL_CHART_STATE_RECONCILED_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/LEL_CHART_STATE_RECONCILED_v1_0.md) |
| LEL | [01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md](/Users/Dev/madhav-l3/pravaha/01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md) |
| PLAN | [inherited engineering plan v2.1](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md) |

### Sealed model and implementation contract

[S][J] “Carried” means an explicit contractual statement survives; it does not certify implementation or a passing test. Qualifications identify incomplete operationalisation.

| Sealed element | Disposition | Spec/evidence |
|---|---|---|
| Union of source-qualified paths; prerequisites intersect within each path | **Carried** | DS §2, lines 108–109, 159–164. Cross-path score aggregation and unknown-state semantics remain unspecified. |
| Relationship record; physical geometry, interpretation and windows separate | **Distorted** | DS §1/§10 retains the concept but lacks essential identity, path, version and join fields. See S-01/S-02. |
| P1 daśā-lord path | **Carried** | DS:114–120, §4. Exact predicates, operands and MD/AD/PD use still require specification. |
| P2 Moon-frame gochara-phala | **Distorted** | Catalogue is carried; O-RP-5 assigns adverse-class evidence to the wrong channel, DS:186–188. |
| P3 lagna/relative-frame transit | **Distorted** | DS:129–132 leaves “house **and** its lord” ambiguous as a prerequisite, and uses practice-level relative edges without a complete admission/use contract. |
| P4 double transit, `[P]`, D-P4 | **Carried** | DS:134–138. The worked admission lacks a pinned orb candidate and an executable definition of “tightest overlap.” |
| P5 AV forms and polarity | **Distorted** | DS §8 introduces a sign-mean comparator absent from the cited ruling; contributor fallback and missing operands are inconsistent. |
| P6 on-demand Moon channel | **Distorted** | On-demand scope is carried, but D-PADMIT’s testimony-first restriction is not operationalised for scored day rows. |
| Independent occurrence evidence and native outcome valence | **Distorted** | DS:206–209 derives `mixed` from opposing occurrence evidence, conflating separate meanings. |
| Shared sky substrate; physical deduplication; Moon on demand | **Carried** | DS §6. Inherited identity needs reconciliation with alias-free and truncated contacts. |
| Necessary-predicate pruning; unknown ≠ false | **Carried** | DS:159–164, 463–467. Predicate/state schema and a falsifying oracle are missing. |
| Certified lazy refinement; station handling | **Carried** | DS §7. Required numerical bounds, certification method and failure handling remain incomplete. |
| Interval sweep; interior extrema and threshold roots | **Carried** | DS:362–363, 463–465. No corresponding numerical extremum/threshold oracle is supplied. |
| Re-solve versus re-score; downstream lineage | **Carried** | DS §10 and F §4. Identity and invalidation mechanics remain incomplete. |
| Benchmark contract without promised speedup | **Carried** | DS:474–476. Actual benchmark results are appropriately not claimed. |
| `[U]` exclusion from scoring | **Distorted** | DS states the rule, but C promotes unverified chart operands and overgeneralises some reads. |
| Kṣetra/Saṅgam receiving contract | **Carried** | F §§2–5 supplies direction, coverage and lineage requirements. F:8 and 87–96 explicitly leave sibling commitments open. |

### Ruled items

[S][J] These findings concern implementation of the rulings, not reconsideration of them.

| Ruling | Disposition |
|---|---|
| D-RQ1 | **Distorted:** zero/unresolved distinction survives, but the new mean threshold and donor-matrix fallback are not settled by this ruling. |
| D-RQ2 | **Carried:** angular M-1 and separately versioned calibration study; DS §7, A:93. |
| D-RQ3 | **Carried at documentary level:** C:121–137 records the node recount; N-14 remains. Exact node-result rows and negative aspect tests must enter the path contract. |
| D-RQ4 | **Carried:** mūrti testimony and auto-stamp removal, DS:526–529/O-CF-N7. Non-use in scoring still needs a guard. |
| D-RQ5 | **Distorted in the prose oracle:** the JSON correctly excludes Sade-Sati from childbirth; DS O-RP-5 instead generalises the ruling to another mechanism and reverses evidence direction. |
| D-RQ6 | **Carried:** producer separation filter removed; serve-time policy retained. O-CF-N5 needs a valid fixture. |
| D-RQ7 | **Carried:** Aṣṭottarī absent on this chart with failed conditions disclosed. |
| D-RQ8 | **Carried through A/C:** Venus ordering note and P4 citation correction survive. DS:276 incorrectly invokes this citation-hygiene ruling beside generalised battle-scale attenuation. |
| D-P4 | **Carried:** practice admission, house-or-lord, occupation-or-aspect. |
| D-PADMIT | **Distorted:** some practice edges are explicitly testimony, but Moon-channel practices and generalised numeric modifiers lack a complete testimony/weight boundary. |

### Findings #1–#27 and N1–N9: guard coverage

[S][J] The following assesses the actual guard, not merely whether a defect number appears in the master index.

| Defect | Disposition | Guard or gap |
|---|---|---|
| #1 Promise saturation | **Lost** | DS:77–78 prohibits alias noisy-OR; nothing requires promise to consume strength **and** condition or rejects a different constant-presence implementation. |
| #2 Constant permission | **Carried** | DS §4; O-PP-2 is an inadequate proxy test. |
| #3 Missing AD/PD use | **Carried** | DS:232–237; O-PP-1 checks AD and PD presence, not actual PD influence. |
| #4 Sade-Sati licence/weight | **Carried** | DS:237; JSON O-RP-5. Complete phase boundaries and no-weight assertions remain needed. |
| #5 Tārā key/`None` defect | **Lost** | P6 mentions tārā; no key-normalisation, non-null operand or actual-use oracle. |
| #6 Zero-width boundary contribution | **Carried** | DS:328–329 requires residence/state intervals. |
| #7 Discarded residence spans | **Carried** | DS §6.2; no numeric contribution fixture yet. |
| #8 Unresolved lords/yogas | **Carried, partial** | DS §1, O-RR-2/3; inherited PLAN §5.3 supplies target-resolution states. Yoga/event qualification remains missing. |
| #9 Negative sensitive checks as targets | **Carried** | DS:79–81, O-RR-4; inherited R-1…R-6 survive through A:121. |
| #10 Selection and resolution frames | **Carried** | DS:74–85, O-RR-1/2. Both stages need separate mutations. |
| #11 Class-blind polarity/clamping | **Distorted** | DS §3 is contradicted by DS O-RP-5. |
| #12 Universal favourable valence | **Distorted** | O-TV-1 guards bereavement; DS §3.2 conflates occurrence conflict with outcome valence. |
| #13 Mirrored directed aspects | **Carried, weakly guarded** | DS:486–488 and A:118 state the repair; no Mars/Saturn direction oracle in JSON. |
| #14 Missing 0° root | **Carried** | DS §6.2/O-SS-2; fixture lacks a complete trajectory and horizon. |
| #15 Graduated aspects | **Carried** | DS:528–529/O-CF-DRISHTI; “every graha” must explicitly exclude node dṛṣṭi. |
| #16 Vedha grade mismatch/generalisation | **Distorted** | DS:275–276 supplies neither the grade-key mapping nor admission for generalised numeric attenuation. |
| #17 Inactive/cancelled/duplicate suppression | **Carried** | DS §5; inactive/cancelled cases in JSON, duplicate-root mutation missing. |
| #18 AV frame/bindu resolution | **Carried, partial** | P5 requires the transiting graha’s BAV; no two-frame operand-selection oracle. |
| #19 Kakṣyā key/donor use | **Distorted** | Donor requirement survives, but sign-level fallback is not donor evaluation; no concrete key/donor fixture. |
| #20 Strength/dignity/nature/maitrī consumption | **Lost** | No complete input-to-effect contract or mutation guard. P1 dignity prose does not cover this inventory. |
| #21 Ignored ontology fields/Cartesian agents | **Lost** | No guard proving `transit_triggers`, `vargas`, `dasha_rules` or equivalent qualified restrictions control enumeration. |
| #22 Yoga overlap/ignored strength | **Lost** | DS §11 claims coverage, but O-RR-1…4 do not test a cited yoga→event relation, cancellation or strength use. |
| #23 “Afflicted” as label | **Lost** | Carrying the qualifier is inherited; no evaluable affliction predicate is defined. |
| #24 Plateau/clipped day tier | **Carried, partial** | DS:165–169 and §7.2 prohibit the shape; no score-variation or independent day-channel fixture. |
| #25 Missing overlay coverage as 1.0 | **Carried** | DS:288–289, 484–485; absent from JSON’s vedha cases. |
| #26 Mūrti/w21 proxy | **Lost in part** | Mūrti is legitimately testimony under D-RQ4; the `min_sav_score`-as-measured-SAV proxy has no explicit guard. |
| #27 Repeated physical boundaries | **Carried** | DS §6.2/O-SS-1; contact-key reconciliation remains necessary. |
| N1 Angular versus time kernel | **Carried** | DS §7/O-SM-1; fixture/comparator incomplete. |
| N2 Fabricated ingress/retrograde boundary | **Carried** | DS §6/O-SS-2. |
| N3 Dropped off-horizon exact centre | **Carried** | DS §6/O-SS-3; residence and degree-contact fixtures must be separated. |
| N4 Collapsed vedha temporal structure | **Carried** | DS §5/O-VI-2/4, but both are missing from JSON. |
| N5 Producer 90-day filter | **Carried** | DS §11/O-CF-N5; current fixture can reject a correct producer. |
| N6 `birth_anchor` kill-switch | **Carried** | DS §11/O-CF-N6; needs a positive control against an empty build. |
| N7 Automatic mūrti source verification | **Carried** | DS §11/O-CF-N7; row existence and scoring exclusion need guards. |
| N8 Bindu/rekhā polarity | **Carried** | DS §8; declaration-use/inversion mutation missing from JSON. |
| N9 Unreliable LEL chart annotations | **Lost as a completion guard** | LR corrects the three examples but explicitly leaves other transits and daśās unverified, LR:164–183. DS has no rejection test for raw/unverified annotations entering evaluation. |

## 3. Findings

### S-01 — blocking · The new evaluator and relationship schemas are not build-complete

**Claim — [S][J].** An engineer must invent consequential semantics to implement this document.

**Evidence.** DS:45–70 specifies one relationship row per class/person/frame/agent/relation/object/role, but provides no `path_id`, rule/version identity, explicit `contact_id` relation, generation key, or source-fact lineage fields. The declared role enum does not include a signature house itself, although P3/P4 require that object. The claimed “natural key below” is not defined beyond the introductory tuple.

DS §2 supplies prose catalogues rather than a path schema. It does not define:

- Concrete prerequisite operators, operand selectors and true/false/unknown states.
- Factor ranges, units, null handling or the score for each path.
- Aggregation of overlapping paths into the class-year score required by the protocol.
- Treatment of conflicting evidence and shared physical roots across paths.
- Promise strength/condition, yoga→event qualification or affliction evaluation.

The inherited PLAN:174–214 supplies useful contact, coverage and publication contracts. Its legacy scoring algebra is expressly superseded by A:65–77, so it cannot silently fill these gaps.

**Requested change — [J].** Freeze typed relationship, path, predicate, factor, evaluation and window contracts, including keys, foreign keys, versions, null states and score aggregation. Give every required L1 input a named selector and a declared effect. Distinguish admission from a zero ranking score and from an unavailable score.

### S-02 — blocking · Physical identity and lineage are not reconciled with the inherited contract

**Claim — [S][J].** The new alias-independent identity requirement conflicts with unresolved parts of the surviving ledger design.

**Evidence.** DS:77–78 requires role aliases to share one physical `contact_id`. PLAN:176 hashes `target_kind` and `target_fact_id-or-ref`, which can distinguish two role-derived references to the same physical point. It also hashes rounded `t_exact`; DS:324–327 expressly retains contacts with no in-horizon exact centre. No successor identity algorithm resolves these cases.

DS:482–483 says a path change must not rebuild geometry, while DS:459–462 also requires re-solving changes to target generation or support domain. A new path can require previously unsearched relations or targets. The dependency, rather than the label “path change,” must decide.

**Requested change — [J].** Define canonical physical-object identity, role-edge identity, truncated-episode identity, and stability across partition extension. Pin hash canonicalisation and collision handling. Add invalidation rules based on changed geometry requirements, plus tests for aliases, null exact times, partition seams, re-scoring and newly required contact domains.

### S-03 — blocking · Valence and admission examples contradict the stated doctrine

**Claim — [S][J].** The prose can reverse adverse-event evidence or deny legitimate admission.

**Evidence.**

- DS:186–188 makes Saturn-in-eighth evidence **against** adverse classes. DS:199–202 correctly says adverse conditions may be evidence **for** an adverse occurrence.
- JSON O-RP-5 instead tests phase-one Sade-Sati exclusion from childbirth, O:57–61. The same oracle ID represents different mechanisms and assertions.
- DS:206–209 makes high evidence both for and against occurrence imply outcome `mixed`. Uncertainty about whether bereavement occurs does not establish mixed consequences for the native if it occurs.
- DS:131 says residence/aspect on a signature house **and its lord**. The specification does not distinguish “both categories are supported targets” from “both contacts are necessary.”

**Requested change — [J].** Correct O-RP-5, synchronise its two representations, and publish an event-class-relative truth table. Keep occurrence conflict separate from native outcome valence. Express P3’s predicates with explicit Boolean/set operators; do not introduce a simultaneous house-and-lord gate through prose.

### S-04 — blocking · Source status, practice admission and scoring permission are conflated

**Claim — [S][J].** A source label or an available corpus passage can presently be mistaken for permission to affect a score.

**Evidence.** N:226–237 settles D-PADMIT: Moon-channel practices and other listed practice elements enter as testimony first. DS:170–171 names only node-dispositor and māraka edges in its testimony invariant; P6 at DS:151–155 lacks an explicit ruling reference and scored-versus-testimony contract.

DS:64–66 uses one qualification enum for `verse_cited`, `uncited_extension` and `testimony`. These express different dimensions: provenance and computational role. A practice item can require both an uncited-extension declaration and testimony-only use.

DS:275–276 associates generalised PG353 battle-scale grading with D-RQ8. N:196–209 authorises citation corrections, not a general suppression multiplier.

DS:433–445 makes the corpus read the activation-weight boundary for P9, although N:264–274 separately requires path-by-path D-T2 admission.

**Requested change — [J].** Separate source verification, admission ruling, operator role, and scoring permission. Encode the current testimony-only state of D-PADMIT elements and the D-T2 gate. Define ablation evaluation without allowing a testimony term into production scoring prematurely. A source read must not automatically promote an operator.

### S-05 — blocking · AV semantics introduce an unruled threshold and contradictory fallback behaviour

**Claim — [S][J].** P5 is not sufficiently specified to preserve the ruled distinctions.

**Evidence.**

1. DS:392–395 compares a sign’s BAV count against “the sign mean.” Neither the sealed P5 definition nor D-RQ1 specifies that comparator, its population, equality case or threshold.
2. DS:405–406 permits sign-level BAV as a coarser qualification while donor data is unavailable. O-BP-2, O:112–116, instead makes missing contributor data sufficient to render “P5” unqualified. That can erase a valid P5a known-zero result from O-BP-1.
3. DS:146–147 states piṇḍa × marks ÷ 27 → nakṣatra without identifying the remainder operation, zero-remainder convention, exact mark-selection frame, reductions or operand provenance.
4. No fixture tests measured SAV against the rule’s `min_sav_score`, the actual #26 regression.

**Requested change — [J].** Remove the mean rule unless supported and admitted explicitly. Specify P5a–e independently, including exact operands, polarity, boundaries, remainder conventions and missing-data states. Missing donor data makes donor-level P5c unavailable; it must neither manufacture donor evidence nor invalidate independently available P5a/P5b results.

### S-06 — blocking · The corpus-read register overstates what its evidence settles

**Claim — [S][J].** Some `[U]` material can cross the scoring boundary through the supplement.

**Evidence.**

- D:200–201 expressly leaves the canonical chart’s Sun-AV father operands unverified. C:182–188 reads a textbook worked example using mark count 2 and Yoga-piṇḍa 148, then describes the chart investigation’s operand sets as `[D]`. A textbook’s example values do not establish this chart’s computed AV values.
- C:111–119 presents several annual-chart passages and concludes a general combined delivery rule. The quoted passages have different conditions and contexts; the evidence does not establish a universal conjunction of sahameśa daśā and varṣeśa/munthā contact.
- C:87 contains an explicit uncertainty marker in the cycle/thirds wording, while C:95–97 treats the refinement as implementation-ready.
- C:149 acknowledges partially illegible pakṣa wording. This does not reopen D-RQ7, but the surviving text must not be represented as a fully verified transcription.
- LR:164–183 says daśā boundaries and most event-date transits remain unverified. It is not a completed regeneration of the evaluation annotation set.

**Requested change — [J].** Preserve chart-specific AV operands as unresolved until a pinned L1 extract supplies them. Separate each source rule and alternative instead of synthesising a new universal operator. Record OCR uncertainty at the affected clause. Keep Tier-2 activation disabled pending its existing admission gate. Add a measurement-input guard that rejects unverified chart annotations.

### S-07 — blocking · Oracle coverage and falsifiability do not meet the stated contract

**Claim — [S][J].** The JSON is neither the claimed inventory nor a complete operationalisation of DS §11.

**Evidence.** Parsing O yields **25 oracles**, not 22. DS contains **35 individually named section oracles**; fourteen are absent from JSON:

`O-RP-1`, `O-TV-2`, `O-TV-3`, `O-PP-3`, `O-VI-2`, `O-VI-4`, `O-SS-4`, `O-SM-2`, `O-SM-3`, `O-BP-3`, `O-AO-2`, `O-AO-3`, `O-RW-2`, `O-RW-3`.

Some obligations have alternative coverage, but critical union, temporal vedha, refinement and coverage cases are missing. The defect-coverage table above identifies further obligations without an adequate spec guard.

O-AO-1 requires a join on `kind` alone to produce no cross-year match. With two same-kind annual rows, that join necessarily permits cross-year matches. O-PP-2 tests variance rather than correct permission. O-CF-N5 assumes arbitrary producer data must contain peaks less than 90 days apart.

**Requested change — [J].** Establish one authoritative oracle inventory. For each oracle, freeze literal inputs or a fully specified fixture generator, the system operation invoked, expected output, comparator/tolerance, and a mutation that must fail it. Actual harness execution belongs to B5.3/A5.5; the design must make those future tests determinate now.

### S-08 — should-fix · Arithmetic and evidence metadata contain reproducible errors

**Evidence — [S][J].**

- O:63 asserts `3.64° = 3°39′`. It equals **3°38′24″**.
- DS:538 gives Ketu–lagna separation as 0°33′ from printed operands 12.99° and 12.43°. Their difference is **0°33′36″**, or 0°34′ rounded to the nearest minute.
- E:33 states 136,887 zero-width rows. Its table sums to **136,883**, also `138,836 − 1,953`. The rounded 98.6% conclusion is unchanged.
- LR:38–41 says the natal values match E8 exactly, but its Venus 259.1882° rounds to 259.19°, not E8’s 259.17°.
- The packet’s abbreviated hash suffixes for the amendment and coordination document do not match the recomputed files; full hashes are disclosed below.

**Requested change — [J].** Correct the arithmetic and manifest references. Pin rounding rules and numerical tolerances. Where E8’s rounded data cannot establish an arcminute claim, use the rounded value honestly or provide the higher-precision source.

### M-01 — blocking · The scored event population does not preserve observation meaning

**Claim — [S][J].** Some evaluation targets are incorrectly timed or mapped, and the advertised mechanical partition is incomplete.

**Evidence.**

- P0:39 and P2:53–56 treat 2026-04-17 as an exact separation event. LEL:1558–1584 explicitly describes an **ongoing status as of the log date**. LEL:22 excludes it from the point-event count.
- B:81 maps 2026-03-20 to `business_launch`; LEL:1500–1508 describes a project **closure**.
- The same baseline mapping treats 2026-04-08 as a launch. LEL:1529–1537 records a public-hearing clearance and says operation is expected later.
- P0:31 says every other eligible point event is held out, but the inventory omits, for example, the month-exact MBA enrolment at LEL:674–682 without an exclusion disposition.
- The grandfather’s death is described as **June or July** at LEL:549–553, whereas the metric uses June alone.
- P0:66 assigns quarry acquisition to `business_launch`; B:90 assigns it to `property_acquisition`. P1:66–68 nevertheless says the mapping is unchanged.

**Requested change — [J].** Freeze a row-level event registry with observation type, date/interval, semantic class, inclusion status, reason, uncertainty and provenance. Separate status observations from onset events. Record class mappings before examining candidate scores; do not force an unsupported observation into an available engine class.

### M-02 — blocking · The horizon, counts and inherited acceptance floor are wrong

**Evidence — [S][J].**

Recounting B’s SQL inventory and per-event table gives:

| Quantity | Recomputed from printed artifact |
|---|---:|
| Listed events | 36 |
| Exact / month / year-grain | 7 / 19 / 10 |
| Timing-usable under the artifact’s current labels | **26**, not 23 |
| Events with a containing window | **21**, not 22 |
| Misses | **15**, not 14 |
| Events with zero candidates | 13 |
| Misses despite candidates | 2: business launch 2024 and major gain 2025 |
| Timing-usable hits | **12/26** |
| All-grain hits | **21/36** |

[S][J] Evidence: B:113–149 and 211–246. Its reported 22/36 at B:274–278 and 383 is not supported by its own table. P1:35–38 calls T-cover a timing-usable endpoint but uses the all-grain 36-event denominator.

[S][J] The inclusive horizon 1998-01-01 through 2026-12-31 contains **10,592 days**, not 10,587. More consequentially, LEL:13 declares observation coverage only through **2026-04-17**: the protocol adds **258 unobserved days**. It also scores the 1995 event despite starting its scored horizon in 1998, B:141/222.

**Requested change — [J].** Reconcile event and observation coverage first, then regenerate every numerator, denominator and inherited floor. The 26-event count above is an audit of the current inventory, not endorsement of that inventory after M-01.

### M-03 — blocking · Metric definitions and controls are not reproducible or comparable

**Claim — [S][J].** The procedure changes the object measured between metrics and can confuse silence with missing computation.

**Evidence.**

- P0:85 requires per-class metrics followed by macro-averaging; its rank text and B’s reported median pool event rows.
- B:103–110 chooses the resolution tier based on available rows in the event year. B:286–335 computes burden over **all** tiers. A hit/rank and its accompanying burden therefore need not describe the same prediction surface.
- B:482–483 calls sparse admitted windows “coverage far below 50%.” Search completion and admitted-time fraction are different quantities. A fully searched year can correctly contain few windows.
- B:327 constructs the class universe from existing output rows. A completely missing class disappears from burden evaluation.
- P0:75–76 requires twenty random controls per event. B does not provide the control draws or resulting random-control metrics.
- B:64–66 relies on an unspecified database-session timezone. Casting stored timestamps and comparing them with plain dates does not make an IST date and a UTC-derived date equivalent.
- Missing rank observations, ties, uncertain event intervals and the relationship between signed intensity and occurrence ranking are not resolved by the protocol.

**Requested change — [J].** Freeze the class universe, event universe, observation mask, prediction-resolution policy, score direction, interval semantics, timezone, aggregation and missing-value rules. Read computation coverage from its manifest. Materialise reproducible control definitions and report every declared metric. Keep occurrence ranking separate from native-benefit polarity.

### M-04 — blocking · Restored T-rank needs protection against selective validity

**Claim — [S][J].** The restoration is directionally correct, but the population contributing to the floor and median is underspecified.

**Evidence.** P2:24–35 requires N≥3 and twelve events. It does not fully settle whether an event with sufficient candidates but **no containing window** contributes a failure or disappears from the median. B’s percentile expression at 191–197 returns null for such a miss.

A generator can also increase N by duplicating or subdividing one prediction unless candidate identity and segmentation are fixed independently of this threshold.

**Requested change — [J].** Define candidate deduplication and maximal-window/peak identity. Keep eligible misses in the rank endpoint with an explicit worst-rank convention. Specify ties without claiming that chronological tie-breaking measures discrimination. Compute the floor from the adjudicated cohort, after degeneracy exclusions, and report class coverage.

### M-05 — blocking · The T-FP density derivation changes its denominator mid-argument

**Claim — [S][J].** Pooling adverse events across classes does not justify assigning that pooled allowance to every class.

**Evidence.** P2:39–48 uses eight events across multiple classes divided by one subject’s horizon, then applies approximately triple that rate **per adverse class**. It also changes from all-horizon admitted fraction to negative-year burden.

The listed events omit `parental_event` from the density list even though B:381 includes it among adverse classes; surgery appears in the density list but not that baseline adverse-class summary.

**Requested change — [J].** Freeze adverse-class membership and observation exposure. Either derive a pooled union-of-adverse-days budget or derive class-specific budgets. Keep all-time burden, negative-time burden and statistical false-positive rate distinct. The exact alternatives and arithmetic appear in Q-M3 below.

### M-06 — should-fix · The miss cap is a convention, not a calibrated timing penalty

**Claim — [S][J].** The seven-event median gate has a defensible shape, but 182 is not uniquely justified.

**Evidence.** P2:53–59 inserts 182 only for misses. B reports observed-hit timing errors of 686 and 998 days. Consequently, a miss receives a numerically smaller loss than those hits.

**Requested change — [J].** If a capped loss is desired, cap **all** errors at 182 and separately report uncapped hit errors and miss count. First repair the exact-event cohort under M-01. Do not present 182 as evidence-derived.

### Explicit measurement answers

#### Q-M1 — deviation and rerun

**[J] The disclosure is necessary and appropriate, but insufficient for acceptance. Preserve the historical pass and rerun the evaluation after review.**

[S][J] The premature pass need not be erased or condemned solely because it preceded review: its declared v1.0 thresholds existed before that pass, and subsequent baseline-informed amendments are disclosed. However, M-01–M-03 show substantive population, arithmetic and metric defects. Its current aggregates cannot serve as the acceptance baseline.

[J] The corrective run should use a pinned extract of the same `'3.0'` generation and the corrected protocol, with a reproducible event/control manifest. Recompute `'4.1'` and `'5.0'` under that same protocol and population. Reprocessing an immutable extract is sufficient; rerunning the astrological producer is not inherently required.

[J] This rerun does not restore blindness. The historical pass remains labelled as conducted before review, and all baseline-informed amendments remain disclosed.

#### Q-M2 — T-rank restoration and floor

**[J] Restore T-rank and retain “rank-unproven blocks the flip.” Do not ratify twelve on the current denominator.**

[S][J] For an actual population of 23, twelve is the smallest strict majority: 52.17%. That is an intelligible governance floor, not a demonstrated statistical precision or power threshold.

[S][J] The printed baseline contains **26** timing-labelled events. Twelve is only 46.15%; a strict-majority floor would be **14**. After correcting status observations, omitted events, class mappings and uncertain dates, the denominator must be recomputed again.

[J] Use `floor(M/2)+1` only if “a majority of the audited timing cohort” is the intended policy. Also require the miss handling and candidate-identity repairs in M-04. N≥3 is a minimum discrimination condition; it does not itself prove useful ranking or independent evidence.

#### Q-M3 — T-FP derivation

**[J] No: the arithmetic is approximately right, but the per-class derivation is not fair as stated.**

[S][J] For the protocol’s proposed full horizon:

\[
H=10{,}592,\qquad
100\frac{8\times90}{H}=6.7976\%,\qquad
3\times=20.3927\%.
\]

[J] Rounding down to 20% is a defensible policy choice. Applying that pooled allowance independently to every adverse class is not the same derivation.

[J] Two coherent alternatives are:

1. **Pooled burden:** compare the union of days carrying any adverse-class prediction with a pooled budget. Do not count an overlapping day repeatedly.
2. **Per-class density budget:** for class \(c\), use its own event count and observed exposure:

\[
B_c=\min\left(1,\frac{3n_cL}{H_c}\right),
\]

where \(L=90\) days is explicitly a chosen allowance, not a discovered duration.

[S][J] On the proposed 10,592-day horizon, a class with one event gets **2.5491%** and a class with two gets **5.0982%** under the second rule—not 20% each.

[J] These are **all-observed-time burden budgets**. They do not automatically derive a negative-year false-positive threshold. A perfect 90-day interval can spill across calendar-year boundaries, while an entirely negative year has no true-event density to estimate. A negative-time budget needs its own declared operational tolerance or an explicitly defined control model.

[J] Recompute after applying the actual observation mask. Unlogged future days must not count as verified negatives.

#### Q-M4 — T-time and the 182-day cap

**[J] Conditionally sound shape; invalid current population; 182 is an arbitrary but usable cap.**

[J] For exactly seven observations, median ≤45 means at least four errors are ≤45. Any miss penalty **greater than 45** gives the same pass/fail result. Thus 182 has no unique mathematical justification for this gate.

[S][J] Applying the draft mechanically to the printed baseline gives:

\[
\operatorname{median}(182,182,182,182,182,686,998)=182,
\]

so the baseline fails as intended.

[J] Retain the single median rule if that is the chosen policy, cap hits and misses consistently, and disclose the miss count alongside it. A pass can coexist with three misses; it is not proof of comprehensive event recovery. After adjudicating the actual exact-date cohort, specify the median convention, especially if its size becomes even.

#### Q-M5 — oracle falsifiability, coverage and arithmetic

**[J] No: the JSON does not establish that every oracle is a valid falsifying test. It contains 25 entries, fourteen omissions from the prose index, an impossible join expectation, proxy tests and unresolved fixture choices. Several sealed defects remain unguarded, as enumerated in §2.**

[S][J] Per-oracle assessment:

| Oracle | Assessment and necessary correction |
|---|---|
| O-RR-1 | Concrete sign/house expectations are correct. Exercise both selection and resolution; assert the positive lagna record. |
| O-RR-2 | Relative-house arithmetic is correct. Distinguish relationship existence from permission to weight practice edges. |
| O-RR-3 | Correct occupant expectation; supply pinned natal fixture and assert actual emitted record. |
| O-RR-4 | Can pass vacuously on no records. Inject negative and positive sensitive facts and assert both exclusion and retained positive output. |
| O-RP-2 | Listed Jupiter aspect signs are correct. Scope the negative to the declared father target set; P1/P3 admission requires their full operands. |
| O-RP-3 | 3.95° arithmetic is correct. Admission depends on a pinned orb: inside 5°, outside 1°. Specify candidate and peak objective. |
| O-RP-4 | Rahu is correctly eighth from Libra. The B3.3 citation does not itself demonstrate an L1 pakṣa read; keep the settled ruling and correct provenance. |
| O-RP-5 | JSON’s Sade-Sati case is sensible; it is a different oracle from DS O-RP-5. Synchronise and test scoring exclusion. |
| O-TV-1 | The adverse-outcome expectation is meaningful; the degree-to-minute equality is wrong. |
| O-PP-1 | Exact MD/AD expectations are stated; “PD present” permits an incorrect constant PD. Supply expected PD and transition/use assertions. |
| O-PP-2 | Variance is not a correctness oracle. It can reject legitimate constancy or accept arbitrary variation. Use known related/unrelated periods and boundary cases. |
| O-VI-1 | Needs explicit known coverage and literal inactive/cancelled fixtures. Otherwise an always-1 implementation passes. Add an active positive control. |
| O-VI-3 | Add a non-exception obstructor control; an implementation producing no vedhas otherwise passes. |
| O-SS-1 | Finite count assertions are falsifiable, but backend, flags, UTC interval and expected crossing fixtures must be pinned. |
| O-SS-2 | Starting longitude and direction alone do not establish a crossing. Supply trajectory, horizon and expected roots. |
| O-SS-3 | Split residence clipping from degree-contact exact-centre clipping; verify both retained support and absence of fabricated exact times. |
| O-SM-1 | Specify station interval, target, orb, expected sample values and tolerance. Symmetry in absolute separation alone is not an independent computation check. |
| O-BP-1 | Useful known-zero test. Also mutate polarity/declaration presence and prove the declaration is consumed. |
| O-BP-2 | Separate missing BAV from missing contributor data; do not make all P5 forms unavailable together. |
| O-AO-1 | **Invalid as written:** joining on kind alone permits cross-year matches. Test the correct year-qualified join and a deliberately broken join. |
| O-RW-1 | Digests alone do not prove that re-solving was avoided. Assert solver invocation/invalidation and known changed outputs as appropriate. |
| O-CF-N5 | Arbitrary output need not contain close peaks. Supply two eligible peaks less than 90 days apart and assert both survive production. |
| O-CF-N6 | Add nonempty control-class output and inspect every resolution; an empty/no-op build must fail the suite. |
| O-CF-N7 | Supply actual mūrti rows, assert testimony and zero scoring effect. A row audit alone cannot establish source-verification provenance. |
| O-CF-DRISHTI | Enumerate permitted bodies. “Every graha” must not reintroduce nodal seventh aspects contrary to N-14. Add directed numeric roots. |

[S][J] Independent arithmetic from the supplied longitudes confirms:

| Check | Recomputed result |
|---|---|
| Twins: Moon 327.06°, Jupiter 306.87° | Both Aquarius; Jupiter is **1st from Moon**, **11th from Aries lagna**. |
| Twins: Jupiter’s seventh aspect | Aquarius → Leo, the fifth from Aries. |
| Twins: Saturn–natal Sun | `291.96−288.01=3.95°=3°57′`. |
| Father frame from Sagittarius | Second Capricorn; seventh Gemini; eighth Cancer. |
| Father-date Jupiter in Scorpio | Fifth Pisces; seventh Taurus; ninth Cancer; no Sagittarius in this set. |
| Father-date Saturn | Sagittarius, ninth from Aries and eleventh from Aquarius. |
| Father: Saturn–natal Jupiter | `253.43−249.79=3.64°=3°38′24″`. |
| Marriage: Saturn return separation | `204.25−202.43=1.82°=1°49′12″`. |
| Marriage: Jupiter fifth-aspect point | `84.57+120=204.57°`; 2°08′24″ from natal Saturn, 0°19′12″ from transit Saturn. |
| Marriage: Ketu–lagna | `12.99−12.43=0.56°=0°33′36″`. |
| Rahu from lagna lord | Taurus counted from Libra is eighth. |
| Natal lunar elongation | `327.06−291.96=35.10°`: Śukla, third tithi, conditional on the supplied natal values. |
| Twins’ tārā count | Natal star index 24, transit index 20, zero-based: inclusive cyclic distance 24, nine-fold class **6**. |

[J] Essential missing numeric regressions should include directed roots. For a target at 0°, `body = target − 30(h−1) mod 360` gives:

| Body/aspect | Correct body longitude |
|---|---:|
| Mars fourth | 270° |
| Mars eighth | 150° |
| Saturn third | 300° |
| Saturn tenth | 90° |

[J] These reject the mirrored `target + angle` implementation directly. Likewise, an interior-extremum fixture such as \(f(t)=t(1-t)\) on \([0,1]\), with endpoint values zero and peak \(0.25\) at \(t=0.5\), can reject endpoint-only peak detection. Neither regression is supplied in the JSON.

## 4. Ranked amendment list

[J] The following must land before freezing the corresponding design or evaluation contract:

1. **Correct contradictory doctrine operators and valence.** Repair O-RP-5, separate occurrence conflict from outcome valence, and specify P3’s Boolean semantics. Evidence: S-03; DS:129–132, 186–214.
2. **Enforce source/admission/use boundaries.** Implement D-PADMIT and D-T2 explicitly; remove unsupported numeric authority from the PG353 reference and the new AV mean rule. Evidence: S-04/S-05; N:196–237, 264–274.
3. **Prevent unresolved operands from entering scores.** Separate textbook examples from canonical-chart data; retain OCR and annotation uncertainty; specify independent P5 operand states. Evidence: S-05/S-06; C:182–188; LR:164–183.
4. **Complete typed evaluator and identity contracts.** Resolve relationship/path/window schemas, score aggregation, canonical physical IDs, truncated episodes and dependency-based invalidation. Evidence: S-01/S-02; DS §§1–2/10; PLAN §§4.3–4.8.
5. **Close every load-bearing guard gap.** In particular #1, #5, #19–#23, #26 and N9; add explicit directed-aspect, unknown-applicability, donor, proxy-operand and interior-extremum cases. Evidence: §2 coverage table and S-07.
6. **Reconcile the oracle inventory.** Repair impossible/proxy assertions, supply deterministic fixtures and mutation expectations, restore required missing cases, and state the actual count. Evidence: S-07 and Q-M5.
7. **Rebuild the evaluation registry and observation mask.** Adjudicate event meaning, onset versus status, uncertainty, exclusions, class mapping and actual follow-up. Evidence: M-01/M-02.
8. **Issue one consolidated protocol with fixed estimands.** Define prediction surface, class universe, score direction, misses, ties, aggregation, computation coverage, random controls, timezone and endpoint populations. Repair rank and FP derivations. Evidence: M-03–M-06 and Q-M2–Q-M4.
9. **Recompute the baseline under that reviewed protocol.** Preserve the premature pass as history; generate a corrected comparable baseline from a pinned extract before evaluating candidates. Evidence: Q-M1 and the independently recounted discrepancies in M-02.
10. **Correct arithmetic and evidence-manifest errors.** Publish consistent rounding, operand provenance and full hashes. Evidence: S-08.

[J] Tier-2 rules need not be implemented to close these amendments. Their interfaces may remain explicitly unavailable or testimony-only under the existing gates. Silence, an unresolved operand, or a source read must not be converted into admission or a score.

## 5. Disclosure

[S] This was an independent read-only review on `campaign/pravaha`; the branch HEAD observed at opening was `6a7fff0f36d9d7718c7954adaf51134db53310fd`. No file was created, edited, moved or deleted; no git write command, database connection, production access or tracker operation was performed. No other reviewer’s current design-spec review was consulted.

[L][S] Production figures were taken on the evidence appendix’s authority. Baseline figures were treated as documentary claims and checked against the artifact’s own SQL, tables and arithmetic—not remeasured against production.

**UNVERIFIABLE_HERE — [S][J]:**

- Actual served-corpus membership and completeness of absence predicates. The corpus-read document supplies extracts and reported queries, not independently queryable evidence in this review.
- Actual L1 AV/contributor/piṇḍa operands, precise event-time daśā rows and unreconciled LEL chart annotations.
- Exact Swiss crossing counts, certified solver errors, backend provenance and the higher-precision instants behind E8’s rounded date-only table.
- Actual runtime oracle execution, mutation sensitivity, writer conformance, publication safety and sibling consumption. These require the future implementation and its scoped test receipts.
- The original row-level `'3.0'` snapshot and random-control outputs. A pinned extract plus the corrected deterministic evaluator would settle the reproducibility questions.

[S][J] No ruled item is reopened as a veto. The required corrections implement the existing rulings and distinguish their authority from unsettled implementation and measurement choices.

[S] Additional hash disclosure, recomputed with `shasum -a 256`:

| Artifact | SHA-256 |
|---|---|
| Plan amendment | `bb5bc981419ff9b33de4490b90a1849da52c3e60d78975b4b50f5b4fd804f9d9` |
| Family coordination | `2476f2ccb7fcd6ebbaa4e472ffe8e17726d3fb0a62dc8e603fe2931d6dd926aa` |
| Corpus reads | `818debe3a65487dd60618a543ddebff5a3ddd14927908146c9b6e3b6112128b5` |
| Protocol v1.0 | `c7c5a8370443c8d24b73336b3693ed7f63f793b838478e185f620724b0efbb0f` |
| Protocol v1.1 | `e093010dff71b15b67629d6796227843632a894d73d7ab58b3dba7cef821bd2f` |
| Protocol v1.2 draft | `8ab737edf0cdf931509171da79631bd3d22bce059fa1eb1e96fc98139ae50f16` |
| Baseline `'3.0'` | `8562c6c885d67a102723bc7949154e2ffb03973562e4a5f91ed7cee9f35d1a75` |
| JSON oracles | `4bd029feddf1ebc19b1f951ec5dc341eca80222666a981ce81b471c31dd1c95b` |

[S] Historical memory was used only for checkout caution; the review’s findings rest on the files read and arithmetic recomputed in this session.

