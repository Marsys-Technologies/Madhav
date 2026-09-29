---
artifact: ASTRA_REVIEW_DESIGN_SPECS
version: "1.1"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra — independent adversarial review (round 2)"
date: "2026-09-29"
verdict_specs: REWORK
verdict_protocol: REWORK
reviewed_packet: "design/reviews/REVIEW_PACKET_DESIGN_SPECS_v1_1.md"
reviewed_packet_sha256: "145f7b1b2a4de9930ed8d866fbfbd1fd0aaa240e43498e7362bc619f608ef716"
hash_method: "Recomputed with shasum -a 256"
worktree_branch: "campaign/pravaha"
worktree_head: "0471400ce9c7edbabf483fb397d19031a8753cf4"
reviewed_file_sha256:
  design/GOCHARA_DESIGN_SPECS_v1_1.md: "6d08d29e8fff03cd2841c12b547a0eae1e9be77702942286a6c2a09adfdb0942"
  design/GOCHARA_TEST_ORACLES_v1_1.json: "6eb255460d83800d2c1cab755345bece46e462bd7fe11fb9ac89f2f429a3de05"
  design/RECONCILIATION_DESIGN_SPECS_v1_0.md: "f5f11c2f07068135dbe1e764dae34e381f6f38306f52e9a60458d79dd194c28c"
  measurement/EVALUATION_PROTOCOL_v2_0.md: "21fa3bc6fcad9cce140c2225fcff44ea84a8953229a533cacec9e391abc7e999"
  measurement/EVENT_REGISTRY_v2_0.md: "dcce07ff1247f68991f109e77b17e7739b007ac47ace22c838619ac2a2bd78de"
  measurement/BASELINE_3_0_v2_0.md: "9e1318e70e7ff5c09695baf6c537b6600dbe4d701eba32ba2b558ce473902964"
  measurement/baseline_3_0_extract_v1_0.json: "70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff"
  measurement/rerun_3_0_v2_0_scorer.py: "951f98034e155e45500f24eca794312aabed4746b227611bcbdab89f29bd6b5d"
  measurement/random_controls_v1_0.json: "ef6ad8a2dc40e0d622ef8ca72100e1fede96f4ce9537d87dbb12d0a1f559a2e6"
  measurement/rerun_per_event_v1_0.json: "e685ecb6a6d241022392f04d4e9e8b3a22f0073de555ff166e33df3c286ef9ad"
  design/GOCHARA_DESIGN_SPECS_v1_0.md: "c87919dbe06fc6828ee719805143a319898b6ebd4c0ae502d67deb14a5debea0"
  design/GOCHARA_TEST_ORACLES_v1_0.json: "4bd029feddf1ebc19b1f951ec5dc341eca80222666a981ce81b471c31dd1c95b"
  measurement/EVALUATION_PROTOCOL_v1_0.md: "c7c5a8370443c8d24b73336b3693ed7f63f793b838478e185f620724b0efbb0f"
  measurement/EVALUATION_PROTOCOL_v1_1.md: "e093010dff71b15b67629d6796227843632a894d73d7ab58b3dba7cef821bd2f"
  measurement/EVALUATION_PROTOCOL_v1_2-DRAFT.md: "8ab737edf0cdf931509171da79631bd3d22bce059fa1eb1e96fc98139ae50f16"
  measurement/BASELINE_3_0_v1_0.md: "8562c6c885d67a102723bc7949154e2ffb03973562e4a5f91ed7cee9f35d1a75"
  design/reviews/KIMI_K3_REVIEW_DESIGN_SPECS_v1_0.md: "7872f239d0127e48fbd2d20b1c1a52fde8ca69f1f078c6acfb244871f8e7c8c7"
  design/reviews/ASTRA_REVIEW_DESIGN_SPECS_v1_0.md: "536d2b1a0d50a733b3cdf0ab4f97fc9328c988cc67b5611a1a6c5e17a2b0a8ee"
lel_sha256: "8221b3cb92c1ca4a206435d5c3647610a5840e8ae6bfcba8ecdc4dbd949c410e"
authority: "Review only; authorizes nothing."
---

## Verdict lines

**[J] Specs + oracles: REWORK.**

[S][J] The inventory repair is real: **55 unique oracle IDs**, exactly matching the specification’s index. Several important boundaries are clearer. Nevertheless, essential schema and scoring semantics remain unspecified, numerous “literal” fixtures contain placeholders, some mutations need not fail, and new examples contradict the revised contract.

**[J] Protocol v2.0 + event registry: REWORK.**

[S][J] The pinned computation is reproducible, but reproducibility does not establish protocol conformance. I independently reproduce **31/46 coverage, 622/920 control hits, and a 182-day capped timing median**. The registry remains incomplete and misclassifies date precision. The scorer implements a different T-FP denominator, omits required degeneracy exclusions, and does not establish computation coverage. Under the protocol’s degeneracy rules, the qualifying T-rank count is **0/27**, not 1/27.

[S] All sixteen supplied artifact hashes match. Both round-1 review hashes match their supplied abbreviations. The packet and ten current review artifacts remained hash-identical at the closing check.

[S] Citation keys below denote exact files; `DS:74–97` means those repository lines. The closure and oracle tables are labelled **[S][J]** throughout: source inspection plus review judgment. Arithmetic tables are **[S]**, independently recomputed from the supplied data. No independent served-corpus `[D]` or live-production `[L]` verification is claimed.

| Key | File |
|---|---|
| DS | [design/GOCHARA_DESIGN_SPECS_v1_1.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_1.md) |
| O | [design/GOCHARA_TEST_ORACLES_v1_1.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_1.json) |
| RC | [design/RECONCILIATION_DESIGN_SPECS_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/RECONCILIATION_DESIGN_SPECS_v1_0.md) |
| P | [measurement/EVALUATION_PROTOCOL_v2_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTOCOL_v2_0.md) |
| ER | [measurement/EVENT_REGISTRY_v2_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVENT_REGISTRY_v2_0.md) |
| B | [measurement/BASELINE_3_0_v2_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/BASELINE_3_0_v2_0.md) |
| SC | [measurement/rerun_3_0_v2_0_scorer.py](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/rerun_3_0_v2_0_scorer.py) |
| X | [measurement/baseline_3_0_extract_v1_0.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/baseline_3_0_extract_v1_0.json) |
| CT | [measurement/random_controls_v1_0.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/random_controls_v1_0.json) |
| PE | [measurement/rerun_per_event_v1_0.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/rerun_per_event_v1_0.json) |
| LR | [measurement/LEL_CHART_STATE_RECONCILED_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/LEL_CHART_STATE_RECONCILED_v1_0.md) |
| LEL | [01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md](/Users/Dev/madhav-l3/pravaha/01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md) |
| P1 | [measurement/EVALUATION_PROTOCOL_v1_1.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTOCOL_v1_1.md) |
| RP | [design/reviews/REVIEW_PACKET_DESIGN_SPECS_v1_1.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/reviews/REVIEW_PACKET_DESIGN_SPECS_v1_1.md) |
| EA | [sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md) |

## Round-1 closure table

### Kimi F1–F7 and Q-M1–Q-M5

| Finding | Closure [S][J] | Evidence in the revised artifacts |
|---|---|---|
| F1 — missing oracle inventory | **Resolved** | O:26–410 contains 55 unique entries; DS:599–628 names exactly the same set. This resolves inventory completeness, not fixture adequacy. |
| F2 — directed-aspect guards | **Partly resolved** | DS:439–444 and O:27–53 add the correct four numerical Mars/Saturn roots. O:51 incorrectly calls 90° “Gemini”; explicit Jupiter directed-root cases remain absent. |
| F3 — unguarded defects | **Partly resolved** | New guards are named at DS:603–622. O:314–325 and 377–381 still lack critical fixture values/keys. The claimed protocol peak-diversity guard is absent from P:132–137. |
| F4 — stale saham/node status | **Resolved at specification level** | DS:175–178 records node residence results while excluding nodal dṛṣṭi; DS:530–536 separates the three activation modes and preserves D-T2. Corpus verification remains outside this review. |
| F5 — horizon/oracle arithmetic | **Resolved** | P:31–33 correctly states 10,334 masked days; O:8 and DS:624–628 correctly state 55. Full-horizon arithmetic independently gives 10,592. |
| F6 — schema ambiguity | **Partly resolved** | Relation usage and role authority are clarified at DS:80–83. Rank-only labels at DS:94–97 do not supply compatible scales, ranges, null handling or complete keys. |
| F7 — permission variance proxy | **Not resolved as an executable oracle** | O:189–191 replaces the assertion conceptually, but the “named” unrelated period is unnamed; the transition instant and transition rule are absent. |
| Q-M1 — no rerun | **Resolved by directive-supersession** | RC:42 and 105–108 explicitly record the native override; B:10–14 supplies the rerun and preserves historical status. |
| Q-M2 — rank denominator/floor | **Partly resolved** | P:99 correctly computes 14 from the declared 27. ER:97–100 downgrades three more precisely dated events, so 27 is not a settled audited cohort. |
| Q-M3 — FP derivation/disclosures | **Partly resolved** | Per-class numerators and masked H are present at P:103–112. The endpoint nevertheless switches to prediction-dependent negative days, while the budget is derived using all observed days. |
| Q-M4 — capped timing rule | **Resolved for the loss calculation** | P:80–84 caps all errors and requires separate disclosure; SC:137–148 implements that consistently. Registry validity remains a separate issue. |
| Q-M5 — oracle coverage/failability | **Partly resolved** | The inventory is complete. O:182–192, 238–268 and 322–325 still do not supply the promised determinate fixtures; the new O-AD-4 sign label is wrong. |

### Codex S-01–S-08 and M-01–M-06

| Finding | Closure [S][J] | Evidence in the revised artifacts |
|---|---|---|
| S-01 — typed evaluator contracts | **Partly resolved** | DS:74–97 adds fields, but still omits `contact_id` and relationship generation. DS:135–151 does not bind versioned FKs or actual factor definitions; DS:153–158 defines `max` without comparable path scores. |
| S-02 — physical identity/lineage | **Partly resolved** | Dependency-based invalidation is corrected at DS:553–559. DS:412–421 supplies an object/contact-family tuple, not a complete identity for repeated contact episodes or partition extension. |
| S-03 — valence/P3/O-RP-5 | **Partly resolved** | Occurrence conflict is correctly separated at DS:312–327, and P3’s OR is explicit at DS:191–198. DS:288–294 still introduces an eighth-house test but supplies a twelfth-house fixture; O-RP-2 conflicts with the expanded father target set. |
| S-04 — provenance/admission/use | **Partly resolved** | DS:43–55, 250–258, 380–383 and 530–536 substantially repair the boundaries. O:133–136 still conflates scored adverse residence with Sade-Sati testimony, without proving the zero-score boundary. |
| S-05 — AV semantics | **Not resolved sufficiently for implementation** | The mean comparator is replaced by an undefined “sign’s own count baseline” at DS:225–229. DS:505–506 contradicts independent P5b availability. O-BP-5 still has no values that guarantee a wrong band under mutation. |
| S-06 — unresolved corpus/chart operands | **Partly resolved** | DS:237–244, 250–253, 345–348 and 530–536 preserve the required uncertainty distinctions. P:128–130 states an annotation guard, but ER has no per-row verification state and SC implements no such validation. |
| S-07 — fixture/falsifiability contract | **Not resolved** | DS:592–597 promises literal fixtures or complete generators. Numerous O rows instead say “pinned,” “stated,” “named,” or “literal” without providing the data. See the complete oracle audit below. |
| S-08 — arithmetic/metadata | **Partly resolved** | DS:60–62 and 632–645 repair DMS/Venus arithmetic; full packet hashes match. O:51 introduces the 90°/Gemini error. EA:33 still prints 136,887; the correct 136,883 is acknowledged in RC:61 but not repaired in that source. |
| M-01 — event meaning/registry | **Partly resolved** | ER:56, 59, 74 and 113–115 implement several requested dispositions. ER omits EVT.2015.XX.XX.01, downgrades three date grains, and calls the 2002 vertigo peak an onset. |
| M-02 — counts/horizon/floor | **Partly resolved** | The masked horizon and current-table arithmetic are correct. ER:102–103 and 143–146 claim a source-complete census that the actual LEL IDs and dates refute. |
| M-03 — reproducible estimands/controls | **Partly resolved** | P:45–67 defines dates and ties; controls are materialised. P:88–114 conflicts with P:147–148 on aggregation, and SC lacks coverage validation, uses an output-derived universe and mismatched control resolutions. |
| M-04 — selective rank validity | **Partly resolved** | Dedup and worst-rank misses are implemented at SC:72–125 and 150–158. Degenerate classes are not excluded; interval-event N is counted over the event interval instead of its year. |
| M-05 — FP denominator/adverse membership | **Not resolved** | Membership and per-class budgets are fixed, but P:104–110 again derives one estimand and applies it to another. SC:180–184 implements a third definition. |
| M-06 — asymmetric miss cap | **Resolved** | SC:143–147 caps hits and misses at 182, while retaining uncapped hit errors. B:36 reports the results correctly. |

### Codex Q-M1–Q-M5

| Finding | Closure [S][J] | Evidence |
|---|---|---|
| Q-M1 — preserve history and recompute | **Partly resolved** | The pinned rerun exists and reproduces the stored outputs: B:10–21, SC:12–14. Its protocol and population defects prevent acceptance as the corrected comparison baseline. |
| Q-M2 — audited majority floor | **Partly resolved** | P:97–102 states the intended policy. The denominator remains defective, and SC:151–158 does not enforce all eligibility exclusions or the floor as a verdict. |
| Q-M3 — coherent FP alternative | **Not resolved** | P:103–110 selects a per-class formula but applies it to negative-time burden; the accepted recommendation explicitly distinguished these quantities. |
| Q-M4 — consistent capped median | **Resolved for the calculation** | P:80–84 and SC:137–148 implement a uniform cap, ordinary `statistics.median`, uncapped hit disclosure and miss counts. This does not validate event mapping. |
| Q-M5 — determinate falsifying oracles | **Not resolved** | O:182–192, 238–268, 294–325 and 350–402 retain missing operands, missing controls and mutations that need not change the asserted result. |

### Each Codex ranked amendment

[S] The numbered amendments are those in the [round-1 Codex review, lines 457–466](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/reviews/ASTRA_REVIEW_DESIGN_SPECS_v1_0.md:457).

| Rank | Closure [S][J] | Evidence |
|---|---|---|
| 1. Correct operators/valence | **Partly resolved** | DS:191–214, 288–294, 312–327; O:112–136. Occurrence/valence separation is repaired; target and operator contradictions remain. |
| 2. Enforce source/admission/use | **Partly resolved** | DS:43–55, 225–229, 380–383, 530–536. Main boundaries improved; AV comparator and testimony/evidence interaction remain unclear. |
| 3. Exclude unresolved operands | **Partly resolved** | DS:241–244, 495–506; P:128–130. Honest holds exist, but operand-state consistency and the operational annotation guard remain incomplete. |
| 4. Complete evaluator/identity contracts | **Partly resolved** | DS:74–97, 135–158, 412–421, 553–559. Added structures do not yet determine joins, episode identity or scoring. |
| 5. Close load-bearing guard gaps | **Partly resolved** | DS:603–622; O:83–158, 293–325, 370–382. Names were added, but fixtures and mutation discrimination remain inadequate. Peak-diversity protection regressed. |
| 6. Reconcile oracle inventory/fixtures | **Partly resolved** | Inventory equality passes; the fixture contract at DS:592–597 does not. |
| 7. Rebuild registry/observation mask | **Partly resolved** | ER:23–34, 48–115. Mask is corrected; source completeness, uncertainty and observation meaning are not. |
| 8. Consolidate fixed estimands | **Partly resolved** | P is consolidated, but P:88–114, 121–130 and 147–148 conflict with one another and with SC. |
| 9. Recompute corrected baseline | **Partly resolved** | The deterministic rerun exists. B:26–64 contains both reproducible numbers and incorrect descriptions/eligibility claims. |
| 10. Correct arithmetic/manifests | **Partly resolved** | Hashes and worked DMS values pass; O:51 and EA:33 remain incorrect. |

## Answers to packet §4 Q1–Q5

### Q1. Overrides and disguised reversals

[S][J] **The Kimi Q-M1 override is correctly recorded as directive-supersession.** RC:105–108 expressly says it was not adjudicated on merit. The supplied native instruction independently establishes the authority for that supersession.

[S][J] Two additional substantive departures are concealed by acceptance/retention language:

1. **Codex M-05/Q-M3 and ranked amendment 8:** RC:71 and 80 claim acceptance of the per-class, all-observed-time derivation. P:104–110 instead defines a prediction-dependent negative-time denominator. This changes the recommended estimand without recording an amendment or override.
2. **Peak-diversity protection:** RC:37 and 95 claim the guard survives. P:132 says the degeneracy tests are unchanged from v1.1, but P1:61–62’s third test has disappeared. This reverses a claimed closure for Kimi F3 and Codex’s #24 guard work.

[J] These are undocumented departures, not evidence of additional authorised native overrides. The reconciliation should identify and adjudicate them explicitly. Other incomplete implementations should remain open findings rather than be relabelled overrides.

### Q2. All 55 oracle fixtures and their ability to fail

[S][J] **The count passes; the universal fixture claim does not.** “Yes” below means the supplied values determine the stated local unit fixture. It does not certify an executable production harness. “No” means the promised fixture requires missing data, an unresolved semantic choice, or a further generator definition.

| Oracle | Literal enough? [S][J] | Missing information or failure limitation | Evidence |
|---|---|---|---|
| O-AD-1 | Yes | Correct 270° positive/90° negative directional cases. | O:27–32 |
| O-AD-2 | Yes | Correct 150° positive/210° negative cases. | O:34–39 |
| O-AD-3 | Yes | Correct 300° positive/60° negative cases. | O:41–46 |
| O-AD-4 | Yes, but expected label wrong | 90° is **Cancer**, not Gemini. The numerical root is correct. | O:48–53 |
| O-RR-1 | Yes, for the geometric resolution test | Supplied Moon/Jupiter/lagna values distinguish the wrong frame and require the positive lagna record. | O:55–60 |
| O-RR-2 | No | Supply the period-context rows/intervals used to assert MD/AD at the event, plus explicit scored versus testimony role assignments. | O:62–67 |
| O-RR-3 | Yes, for occupant resolution | Natal Saturn and Aries lagna determine the seventh-house occupant. | O:69–74 |
| O-RR-4 | No | Positive fact has no degree, fact kind, ID or owning graha. “A real degree” is not a literal fixture. | O:76–81 |
| O-RR-5 | No | No named yoga, source rule, class, strength value or cancellation predicate. Both supposedly “pinned” operands are absent. | O:83–88 |
| O-RR-6 | No | Object X, longitudes, orb and evaluated/missing coverage cases are unspecified. | O:90–95 |
| O-RR-7 | No | No actual window, baseline score, scored records or testimony row. Annotation behavior after removal also needs clarification. | O:97–102 |
| O-RP-1 | No | No specific event class, contacts, intervals or operator roles; “own-fortune class” does not identify a registry class. | O:104–109 |
| O-RP-2 | No | Freeze the exact father target set and complete P1/P3 operands. The unconditional “NO P4” conflicts with DS’s broader target set. | O:111–116 |
| O-RP-3 | No | The 5° admission example is concrete, but no trajectories, overlap interval or expected peak can reject endpoint-only peak detection. | O:118–123 |
| O-RP-4 | Yes, for the ruled applicability predicate | Supplied natal positions and day/Śukla condition determine the stated failed conditions. Source transcription is not independently verified. | O:125–130 |
| O-RP-5 | No | Separate P2 residence from Sade-Sati testimony; name the adverse class and scoring assertion. The advertised eighth-house case is absent. | O:132–137; DS:288–294 |
| O-RP-6 | No as the promised literal fixture | Supply a numeric strength and condition/path record, or define an explicit quantified property and input domain. | O:139–144 |
| O-RP-7 | No | Period lord, sign, other factors and qualifier mapping are unspecified; the inventory still lacks complete effects. | O:146–151 |
| O-RP-8 | No | No actual allowed tuple set, excluded tuples, ontology rows or expected count. | O:153–158 |
| O-TV-1 | No for the complete test | Geometry is concrete; the admitted path, score/evidence inputs and their positive expected contribution are not. | O:160–165 |
| O-TV-2 | No as a literal fixture | Supply the evidence values/records and exact affliction condition, or freeze this explicitly as a quantified valence property. | O:167–172 |
| O-TV-3 | No | Name the unresolved operand/form, other available paths and expected contribution versus whole-window valence. | O:174–179 |
| O-PP-1 | No | **No expected PD lord is supplied for any date**, nor a pinned nested daśā fixture or transition-use assertion. | O:181–186 |
| O-PP-2 | No | Unrelated period, supporting relationships, transition instant and boundary convention are absent. | O:188–193 |
| O-PP-3 | Yes, for applicability | Common constants and stated birth conditions determine the local predicate. | O:195–200 |
| O-VI-1 | No | Supply literal intervals, coverage, primary/obstructor identities, grade keys and active attenuation value. | O:202–207 |
| O-VI-2 | No | `t0/t1/t2` are not timestamps. Both displayed closed intervals include `t1`, where “attenuated” and “clean” conflict. | O:209–214 |
| O-VI-3 | No | Supply actual primary/obstructor houses, instants and rule rows; “the vedha house” leaves the computation unstated. | O:216–221 |
| O-VI-4 | No | No timestamps, grade or endpoint convention; the promised literal intervals are symbolic. | O:223–228 |
| O-VI-5 | No | Supply requested horizon, primary context and the expected unavailable-coverage object. | O:230–235 |
| O-SS-1 | No | “Flags pinned” supplies no flags, backend/data version or exact endpoint convention. A year label alone is not the promised pin. | O:237–242 |
| O-SS-2 | No | No interval, time-dependent trajectory/interpolation, horizon or root times; “expected roots stated” is false. | O:244–249 |
| O-SS-3 | No | No endpoints, horizon or centre; residence and degree-contact cases are still not actually separated. | O:251–256 |
| O-SS-4 | No | No 30-day dates, ephemeris fixture, expected events or cache/prefetch state. | O:258–263 |
| O-SM-1 | No | No station interval, target, orb, sample values or numeric tolerance. Every purported pin is missing. | O:265–270 |
| O-SM-2 | No | No bracket, uncertainty value, orb or refined expected result. | O:272–277 |
| O-SM-3 | No | “The built substrate” supplies no positive station control. An empty/no-station substrate passes. | O:279–284 |
| O-SM-4 | Yes | Complete function, interval, expected peak and time tolerance; endpoint-only evaluation is distinguishable. | O:286–291 |
| O-BP-1 | No for its advertised selector mutation | Mars’s zero is given, but competing BAV/SAV values are not. Another graha’s BAV can also be zero, allowing the wrong selector to pass. | O:293–298 |
| O-BP-2 | No | Supply actual independent BAV/SAV values and availability records for both cases. | O:300–305 |
| O-BP-3 | No | Supply declaration rows/IDs, a real evaluation, missing-declaration case and polarity-inversion case; an empty citation audit can pass. | O:307–312 |
| O-BP-4 | No | No degree, canonical donor-key spelling, matrix cells or mismatched-key input. Allowing declared absence does not test donor-key resolution. | O:314–319 |
| O-BP-5 | No | Neither value is given; merely different values can occupy the same SAV band, so the stated mutation need not fail. | O:321–326 |
| O-AO-1 | No | Corrected join assertion, but no two literal rows, years, longitudes, chart ID or query fixture. | O:328–333 |
| O-AO-2 | No | No nonempty rows or explicit valid/invalid locator set. Empty input passes. | O:335–340 |
| O-AO-3 | No | No actual P9 row/gate fixture or positive annotation control; absence of P9 rows can pass. | O:342–347 |
| O-RW-1 | No | No ledger, old/new rule, expected changed window or newly required geometry case. A no-op reevaluation is not excluded by the prose alone. | O:349–354 |
| O-RW-2 | No | No response fixtures, manifest data or expected confirmed/context counts. | O:356–361 |
| O-RW-3 | No | No manifests, labels, authority states or expected provenance payloads. | O:363–368 |
| O-GR-PLATEAU | No | No actual curves/rows or quantitative comparator. Correct lineage labels do not prove that scores were independently computed. | O:370–375 |
| O-P6-TARA | No for the key-regression test | Star indices determine class 6, but the canonical key and mismatched-case key are absent. | O:377–382 |
| O-CF-N5 | No | Supply two dated, distinct eligible windows/peaks, their eligibility inputs and served policy. “60 days apart” alone does not define them. | O:384–389 |
| O-CF-N6 | No | Control class and its “known rows” are unnamed and absent. The intended positive control is only a promise. | O:391–396 |
| O-CF-N7 | No | No mūrti rows or nonzero baseline scored window. Empty rows or a constant-zero scorer can satisfy the stated comparison. | O:398–403 |
| O-CF-DRISHTI | Yes, for the finite strength table | Seven permitted bodies, ordinary fractions, specials and node exclusions determine the unit cases. Jupiter directed roots are not supplied by O-AD-1…4. | O:405–410 |

[S][J] Every entry contains mutation prose, but that is not proof that its mutation fails. Concrete counterexamples include:

- **O-BP-5:** measured SAV 28 and config 29 are different but both “medium”; substituting config for measurement preserves the asserted band.
- **O-BP-1:** Mars BAV 0 and another graha’s BAV 0 preserve the adverse result under a wrong-selector mutation.
- **O-SM-3/O-AO-2:** an empty row set satisfies the universal audit.
- **O-RP-3:** one dated snapshot cannot distinguish an interior-peak solver from endpoint-only evaluation.
- **O-PP-1:** “PD asserted exactly” supplies no expected PD against which an incorrect constant could be rejected.

#### Independent geometry and arithmetic

[S] I recomputed the supplied longitudes using `floor(longitude/30)`, inclusive cyclic house counts and the declared forward aspect offsets.

| Check | Recomputed result |
|---|---|
| Natal sign sequence | Sun Capricorn; Moon Aquarius; Mars Libra; Mercury Capricorn; Jupiter Sagittarius; Venus Sagittarius; Saturn Libra; Rāhu Taurus; Ketu Scorpio. |
| Natal houses from Aries | Sun 10; Moon 11; Mars 7; Mercury 10; Jupiter 9; Venus 9; Saturn 7; Rāhu 2; Ketu 8. |
| Directed root, target 0° | Mars fourth: **270° Capricorn**; Mars eighth: **150° Virgo**; Saturn third: **300° Aquarius**; Saturn tenth: **90° Cancer**. |
| Additional Jupiter roots | Fifth: 240° Sagittarius; ninth: 120° Leo. |
| Father frame | Sagittarius; second Capricorn, seventh Gemini, eighth Cancer. |
| Twins’ Jupiter 306.87° | Aquarius: first from Aquarius Moon, eleventh from Aries; seventh aspect Leo, fifth from Aries. |
| Twins’ Saturn 288.01° | Capricorn: twelfth from Aquarius Moon; `291.96 − 288.01 = 3.95° = 3°57′00″`. |
| Father-date Jupiter 220.31° | Scorpio; fifth Pisces, seventh Taurus, ninth Cancer. |
| Father-date Saturn 253.43° | Sagittarius: ninth from Aries, eleventh from Aquarius; separation from natal Jupiter **3°38′24″**. |
| Marriage Saturn | `204.25 − 202.43 = 1.82° = 1°49′12″`. |
| Marriage Jupiter | 84.57° Gemini; fifth-aspect point 204.57° Libra; **2°08′24″** from natal Saturn and **0°19′12″** from transit Saturn. |
| Marriage nodes | Ketu 12.99° Aries, **0°33′36″** from lagna; Rāhu 192.99° Libra, seventh from Aries. |
| Rāhu from lagna lord | Taurus is eighth from Libra. |
| Natal lunar elongation | `327.06 − 291.96 = 35.10°`: third tithi within the stated Śukla half. |
| Tārā | `(20−24) mod 27 + 1 = 24`; nine-fold class **6**. Transit-star provenance remains unverified here. |
| P5d textbook arithmetic | `148 × 2 = 296`; `296 mod 27 = 26`, consistent with the stated Uttarabhādrapadā example. |
| Second kakṣyā division | Within-sign interval **[3.75°, 7.5°)** under the stated equal eight-division order. |
| Boundary arithmetic | `8×12=96`; `(12+27+96)×13.37×250 = 451,237.5` approximate lunar crossings. This is an estimate, not a Swiss count verification. |

[S] The fresh longitude/sign error is **O-AD-4’s Gemini label**. The worked-event DMS corrections otherwise pass. Missing trajectories, PD values, AV operands and Swiss pins prevent independent numerical execution of the corresponding complete oracles.

### Q3. Registry judgment calls

**(a) EVT.2026.03.20.01**

[S] LEL:1500–1508 dates a **project closure**. It says revenue was generated steadily during 2023–2026 and profits accumulated; it also records cessation of that revenue stream.

[J] Rejecting `business_launch` is correct. Mapping the closure to `major_gain` is a **plausible disclosed proxy**, not a source-proven exact-date realised-gain observation. The LEL does not establish that the accumulated gain was realised on March 20. Accept that mapping only with an explicit class definition covering profitable project completion, a proxy qualification and a sensitivity report; otherwise retain the closure as unmapped rather than manufacture an exact gain date.

**(b) EVT.2011.06.XX.01**

[S][J] Restoring MBA enrolment is correct. LEL:643–670 explicitly separates admission from enrolment, and LEL:674–682 gives June 2011 enrolment independently.

[S][J] **The resulting 27-event cohort is nevertheless not complete.** ER:97–100 assigns year grain to:

- EVT.2025.06.XX.01: LEL:1824–1826 says June, month-approx.
- EVT.2025.11.XX.01: LEL:1854–1856 says November, month-approx.
- EVT.2026.01.XX.01: LEL:1472–1480 describes January–February 2026, a bounded two-month interval.

[S] EVT.2015.XX.XX.01 at LEL:1766–1774 appears in neither the held-out nor excluded tables.

[S][J] Merely restoring that omitted year-proxy event and the three date grains—without adjudicating other mapping and uncertainty problems—would produce **47 held-out events: 30 timing-usable and 17 year-grain**, with majority floor **16**. That is a sensitivity calculation, not an approved replacement registry.

### Q4. Instant-class misses: behavior or scorer artifact?

[S] The extract confirms the raw counts and zero-width shape:

| Class | Raw rows | Admitted days within H |
|---|---:|---:|
| education_milestone | 40 | 12 |
| career_change | 30 | 9 |
| business_launch | 30 | 9 |
| foreign_settlement | 30 | 9 |
| separation | 30 | 9 |

[S][J] **The thirteen timing-usable events in these classes really miss on this extract.** Replacing the month-15th containment check with full calendar-month overlap does not rescue any of those month-grain events. The February 5, 2024 business instant does not hit the exact February 16 event.

[S] Three qualifications invalidate the settlement’s broader wording:

1. The sixteen events include **three year-grain events**, so “sixteen event-months” treats year proxies as observed months.
2. EVT.2004.XX.XX.02 **is a hit** under year overlap: education instants exist on February 5, April 5 and July 4, 2004 (X:2969–3000). B:45–47’s claim that these classes miss every event is false.
3. Some foreign-settlement instants abut: February 5 and 6 are separate raw rows that merge into a two-day candidate (X:4267–4287). They do not all survive as separate one-day candidates.

[S][J] The scorer is also not generally conformant: **P:76 defines a fifteenth-day proxy for timing error, whereas P:88–90 expressly says month-grain T-cover uses the month.** A one-day prediction on March 10 for a March-grain event illustrates the difference: month-overlap coverage hits; SC:111–114’s fifteenth-day test misses. This inconsistency does **not** change current T-cover, but must be settled before candidate scoring.

### Q5. Horizon and budgets

[S] Inclusive civil-date arithmetic gives:

\[
H=10{,}334,\qquad H_{\mathrm{full}}=10{,}592,\qquad
H_{\mathrm{full}}-H=258.
\]

\[
100\frac{270}{10{,}334}=2.6127346623\%,\qquad
100\frac{540}{10{,}334}=5.2254693246\%.
\]

[J] The zero-event allowance can be an explicit policy tolerance. It does **not** follow from the printed formula, which gives zero when \(n_c=0\). The implemented formula is:

\[
B_c=\min\!\left(1,\frac{270\max(n_c,1)}{H}\right).
\]

[J] Factor-three slack is defensible as a declared engineering allowance on **all-observed-time admitted burden**. It is not derived from the T-time gate: a peak within 45 days does not restrict the containing window’s duration. It also does not justify applying the same number to a different negative-time denominator.

[S][J] In inclusive daily counting, \([d-45,d+45]\) contains **91 days**. If that is the intended footprint, the one-/two-event budgets become **2.641765% / 5.283530%**. Retaining 90 is reasonable only as an explicitly chosen approximation or continuous-duration convention.

## Independent rerun of “3.0”

[S] I parsed events from ER itself, independently loaded X and CT, and computed interval unions, containment, ranks, controls and burdens in memory with `/opt/homebrew/bin/python3 -B`. I did not run SC’s write-producing top level. Selected pure functions were separately executed in memory for counterexamples.

### Reproduced results and differences

| Measure | Independent result [S] | Assessment |
|---|---|---|
| Registry as currently written | 46 = 5 exact + 21 month + 1 interval + 19 year | Reproduces the table, not its asserted fidelity to LEL. |
| T-cover, scorer’s proxy interpretation | **31/46 = 67.391304%**, 15 misses | Matches B and PE. |
| T-cover, calendar-month overlap | **31/46 = 67.391304%** | Same current result despite the definition conflict. |
| T-cover, equal-class macro average | **76.666667%**, over 21 event-bearing classes | Different estimand required by P:147–148’s general aggregation instruction. |
| Materialised controls | **622/920 = 67.608696%** | Every stored hit count and every seed-generated date reproduces. |
| Controls, equal-class macro average | **76.809524%** | Again differs from the reported event-weighted figure. |
| T-time | **182 days**, 2 misses | Matches B. |
| T-rank before degeneracy exclusions | One event reaches N≥3; its miss percentile is 100 | Reproduces SC’s preliminary result. |
| T-rank after required exclusions | **0/27 qualifying events; no valid median** | The sole preliminary event is degenerate-low. The generation-wide fingerprint also voids T-rank. |
| Era-boundary fingerprint | **210/351 = 59.829060%** | Matches B. |
| Two-horns classes | **22 high, 5 low** | B’s “17 gain classes degenerate-high” is wrong. Under SC’s non-adverse grouping, 14 are high and 4 low. |
| T-honesty | **UNVERIFIABLE_HERE** | X contains no computation-coverage manifest. Admitted-day fraction cannot establish searched coverage. |

[S] The exact-event timing calculations are:

| Event | Result | Uncapped error | Capped error |
|---|---|---:|---:|
| EVT.1998.02.16.01 | Hit; peak 2000-01-03 | 686 | 182 |
| EVT.2007.06.10.01 | Hit; peak 2004-09-15 | 998 | 182 |
| EVT.2008.06.09.01 | Miss | — | 182 |
| EVT.2024.02.16.01 | Miss | — | 182 |
| EVT.2026.03.20.01 | Hit under current mapping; peak 2025-04-27 | 327 | 182 |

[S] These give median `(182,182,182,182,182) = 182`.

[S] The fifteen misses are the seven timing-grain education events; both career-change events; foreign settlement; separation; both business launches; and year-grain education events EVT.2000.XX.XX.01 and EVT.2021.XX.XX.02. The 2004 education event is the instant-class year-grain hit.

### T-FP: the scorer and protocol measure different quantities

[S] SC:180–184 subtracts **one day per hit event**. P:104–105 instead removes **the containing-window hit’s days**. Applying those two definitions separately to the same extract gives:

| Adverse class | \(n_c\) | Budget % | SC burden % | Literal P §6.4 burden % |
|---|---:|---:|---:|---:|
| bereavement | 1 | 2.612735 | 99.874189 | 99.805564 |
| career_setback | 1 | 2.612735 | 99.874189 | 99.805564 |
| chronic_onset | 2 | 5.225469 | 99.874177 | 99.708781 |
| financial_deception | 1 | 2.612735 | 99.874189 | 99.863603 |
| illness_acute | 1 | 2.612735 | 99.874189 | 99.805564 |
| parental_event | 1 | 2.612735 | 99.874189 | 99.805564 |
| separation | 1 | 2.612735 | 0.087091 | 0.087091 |
| surgery | 1 | 2.612735 | 99.874189 | 99.805564 |
| major_loss | 0 | 2.612735 | 99.874202 | 99.874202 |

[S] For example, the scorer’s one-hit era-class burden is `10,320/10,333`. Under the literal containing-window exclusion, bereavement removes 3,648 admitted days, giving `6,673/6,686`.

[S][J] **Eight of nine fail under either calculation**, so the baseline’s adverse-burden failure is robust. Its exact claimed estimand is not. Using the recommended all-observed-time measure instead gives **10,321/10,334 = 99.874202%** for the eight broad adverse classes and **9/10,334 = 0.087091%** for separation.

[S] The broad classes retain **ten distinct decade candidates over the extract**, not one century candidate. They have gaps between decades; for example, one window ends January 30, 1994 and the next begins February 5 (X:22–34). Four decade candidates intersect the masked horizon. B:26–29 is therefore incorrect even though many event years contain only one candidate.

## New findings

### R2-S01 — blocking · The typed contract remains incomplete

**Claim — [S][J].** The added schemas do not determine a version-safe, generation-safe evaluator.

**Evidence.** DS:74–97 has neither `contact_id` nor relationship `generation`, although DS:104–105 requires the former and DS:561–563 prescribes generation-scoped replacement. `object_role` still has no role for a signature house itself. `rule_path` is keyed only by `path_id`, while historical versions are referenced separately; predicate/factor lists likewise omit version-qualified FK semantics (DS:135–151). Empty `temporal_support.intervals` is defined only as uncomputed (DS:87), leaving computed-empty support unrepresentable there.

**Requested change — [J].** Publish actual keys/FKs and version binding; choose explicit shared versus generation-scoped records; add the contact relation and source-fact lineage; use tagged availability/completeness states. Define how unknown predicates affect admission, unresolved scores and stored windows.

### R2-S02 — blocking · Physical-object identity does not replace episode identity

**Claim — [S][J].** The new identity tuple cannot by itself identify recurring contacts.

**Evidence.** DS:412–421 hashes body, relation, target and convention. Repeated crossings of the same target under the same convention have that identical tuple. If it identifies only an object, the replacement episode key remains unspecified; if treated as the contact key, distinct episodes collapse. “Fail on hash collision” does not solve two legitimate episodes having identical input tuples. Partition extension is promised to preserve identity without an episode-association algorithm.

**Requested change — [J].** Specify separate target, contact-family and episode identities, canonical serialization, retrograde/multiple-pass distinction, null-centre handling and seam reconciliation. Preserve publication immutability during extension. Supply concrete alias, repeated-crossing and partition-extension fixtures.

### R2-S03 — blocking · Score aggregation and path operators remain underdetermined

**Claim — [S][J].** A named `score_rule` and cross-path `max` do not define comparable scores.

**Evidence.** DS:144–158 supplies placeholders for ranges, selectors and effects; evidence scales are deferred to L5 at DS:94–97. P1 strength and maitrī are named without complete effects (DS:169–173). Accumulating occurrence evidence across records/paths lacks an aggregation and shared-root rule.

The P3 table is also a partial target catalogue, not an exhaustive class predicate table. Its father targets include Sagittarius, Capricorn, Gemini and Cancer (DS:200–210). Jupiter in Scorpio aspects Cancer while Saturn occupies Sagittarius. Consequently, the house-or-lord P4 wording at DS:212–218 does not justify O-RP-2’s unconditional rejection of every father-frame P4 row.

**Requested change — [J].** Define each path’s numerical function, units, missing-input handling, evidence aggregation and class polarity. Freeze exact per-class target/agent sets and P4’s shared-target requirement, if any. Scope O-RP-2 to the actual intended target set.

### R2-S04 — blocking · AV comparator and missing-data semantics still conflict

**Claim — [S][J].** Removing the words “sign mean” did not supply a valid replacement comparator.

**Evidence.** DS:226 compares the count to an undefined “sign’s own count baseline”; DS:491–495 refers to unspecified doctrinal expectations. DS:231 makes P5b depend independently on SAV, but DS:505–506 says missing BAV makes both P5a and P5b unqualified. O-BP-5’s merely different numbers need not yield different bands.

**Requested change — [J].** Name a supported comparator or leave the relevant nonzero P5a qualification unresolved; provide an availability matrix for P5a–e; make the proxy mutation cross a band boundary. Extend the G-10 interface to include the required piṇḍa/reduction provenance: RP:124–128 requests BAV, donor rows and SAV but does not explicitly request the piṇḍas required at DS:237–244 and 497.

[J] Actual G-10 chart values may remain unavailable. That does not prevent freezing a complete synthetic regression fixture or a precise input contract.

### R2-S05 — blocking · O-RP-5 still conflates mechanisms and does not test the advertised case

**Claim — [S][J].** The wording change does not establish the intended eighth-house adverse-evidence repair.

**Evidence.** DS:288–294 starts with Saturn eighth from Moon, then supplies Saturn twelfth from Moon/Sade-Sati phase 1. O:133–136 uses the twelfth-house fixture and simultaneously demands positive occurrence evidence and a testimony row. DS:47 and 102–103 prohibit testimony from contributing to scores, weights or gates.

**Requested change — [J].** Create distinct fixtures for scored P2 adverse residence and testimony-only Sade-Sati. Include an actual eighth-house case, name a native adverse class, assert the correct occurrence channel, and separately prove testimony has no score or admission effect.

### R2-S06 — blocking · Fixture and mutation promises are not fulfilled

**Claim — [S][J].** Numerous guards remain specifications for future test authoring rather than frozen test fixtures.

**Evidence.** The complete Q2 table identifies each oracle. Particularly consequential omissions are PD expectations, unrelated-period boundaries, solver trajectories/tolerances, AV donor keys, competing operand values and nonempty audit controls. O:51 additionally mislabels Cancer as Gemini.

**Requested change — [J].** Replace each placeholder with actual records/numbers or a complete deterministic generator. For each claimed mutation, show that the supplied fixture changes the asserted output. Add an explicit unknown-applicability admission case and positive controls for universal audits.

### R2-M01 — blocking · Registry completeness and observation meaning remain false

**Claim — [S][J].** The registry cannot yet serve as the frozen scoring population.

**Evidence.** The ID audit finds **57 actual LEL event/status blocks, including one status**, versus 56 registry IDs; EVT.2015.XX.XX.01 is missing. ER:97–100 loses three finer date grains. ER:84 labels the 2002 event “vertigo onset,” while LEL:1683–1687 describes peak debilitation and explicitly says onset was likely earlier. Other uncertainty ranges—such as 2007–2008 sleep onset and 2021–2022 quarry acquisition—are flattened without structured uncertainty fields.

**Requested change — [J].** Reconcile every source ID exactly once; preserve observation type, source precision and ranges; distinguish onset, exacerbation, completion and proxy mapping. Regenerate cohort sizes, budgets, controls and floors after adjudication. Replace ER:145–146’s “any mismatch is a scorer bug” with a source reconciliation invariant.

### R2-M02 — blocking · T-FP has three incompatible definitions and a prediction-dependent exclusion

**Claim — [S][J].** The protocol both changes denominator and lets predictions define which time is exempt.

**Evidence.** P:104–110 defines negative time by containing prediction windows but budgets using all H. P:121–122 describes negatives by registry events. SC:180–184 approximates them by one day per hit event.

A concrete counterexample: with H=1,000, one event on day 500 and a prediction covering days 100–900, the literal §6.4 exclusion leaves 199 negative days and **zero admitted negative days**. An 80.1%-of-horizon prediction therefore receives **0% negative burden**, against a 27% budget.

**Requested change — [J].** Prefer the accepted all-observed-time per-class budget. If a negative-time endpoint is retained, define its truth mask independently of predictions and derive a corresponding budget. Count unions of days, not event rows, and encode the zero-event policy explicitly.

### R2-M03 — blocking · Rank eligibility is not implemented, and peak-diversity protection regressed

**Claim — [S][J].** The scorer can report rank evidence the protocol forbids.

**Evidence.** SC:151–158 filters only on N≥3; it does not exclude degenerate classes or void the generation before ranking. P:101–102 and 132–137 require both. The current sole eligible event is in degenerate-low `business_launch`.

P1:61–62’s peak-diversity test is absent despite P:132 claiming unchanged tests. Three candidates with scores `1, 1, 0.5` give a top tied event average rank 1.5 and percentile **16.6667**, passing the rank threshold while two-thirds of candidates share a score.

**Requested change — [J].** Restore or explicitly adjudicate the removed test; run all degeneracy checks first; exclude invalid classes before calculating the floor and median; emit machine-readable failure for unmet validity floors and generation-wide voids.

### R2-M04 — blocking · Candidate ranking and aggregation diverge from the protocol

**Claim — [S][J].** These defects affect future candidates even where the current baseline verdict remains failure.

**Evidence.** SC:103–106 counts interval-event candidates only inside the uncertainty interval, unlike P:97–99’s event-year population. Executing the pure function on three candidates in January, June and December with a June–July event returns **N=1**, where the protocol requires **N=3**.

SC:83 and 118–124 use absolute intensity. A gain-class containing score of `−0.9` ranks above `+0.4` and `+0.2`, contrary to signed-descending P:61–63. The protocol also leaves merged-window peak/score selection and the percentile formula unstated. P:147–148’s macro average conflicts with the pooled endpoint reports.

**Requested change — [J].** Freeze candidate-year membership, merge representatives, signed-score adaptation, ties, percentile formula, observation-mask treatment and endpoint-specific aggregation. Implement those rules identically in the scorer.

### R2-M05 — blocking · Controls are reproducible but not matched to event resolution

**Claim — [S][J].** The 622/920 figure is reproducible under the code, but the comparison is not the protocol’s promised matched-resolution experiment.

**Evidence.** SC:200 assigns 365 days to the grandfather’s **61-day** interval. Month controls are rolling 30-day spans, year controls rolling 365-day spans, while real month events use a fifteenth-day proxy and year events calendar-year overlap. `randrange(0, H-span)` at SC:204 excludes the last valid start; inclusive complete-fit sampling requires `H-span+1` possibilities.

**Requested change — [J].** Define matched calendar/interval control units and identical hit semantics, correct the start-domain boundary, preserve the grandfather’s interval length, and version the resulting materialised controls. Report the selected weighting scheme.

### R2-M06 — blocking · Coverage, class universe and input guards are not operationally pinned

**Claim — [S][J].** The measurement stack cannot distinguish absence of predictions from incomplete computation.

**Evidence.** X:8–17 has no coverage fields or manifest. B:39 substitutes base rate for T-honesty. SC:161 derives its universe from emitted classes, and SC:189 treats every non-adverse output class as a gain class. P:40 references a fixed 27-class list that DS does not enumerate with polarity, eligibility and disabled-class policy.

DS:621–622 and RC:97 claim per-row annotation verification in ER, but no such column exists. SC reads neither ER nor LR; its event list is hard-coded.

**Requested change — [J].** Pin a machine-readable registry, class/polarity/eligibility table, prediction-tier selector and computation-coverage manifest. Validate IDs and inputs against them. Either implement the annotation rejection path or explicitly constrain this scorer to inputs that contain no chart annotations and withdraw the broader guard claim.

### R2-M07 — should-fix · Baseline narrative overstates what the computed results establish

**Claim — [S][J].** Several conclusions are not supported by the stored rows.

**Evidence.** B:26–29 claims one century candidate per broad class; the actual result is ten decade candidates. B:45–47 says every instant-class event misses, overlooking the 2004 education hit. B:54 miscounts high-rate gain classes. B:60–62 calls **67.608696%** and **67.391304%** “exactly” equal and infers no information without a specified inferential test.

**Requested change — [J].** Generate descriptive counts from the calculation; distinguish preliminary and valid rank results; report “no observed separation in this diagnostic” rather than mathematical equality or a proved information-theoretic conclusion. T-honesty must remain unverified until coverage evidence exists.

## Ranked amendments required before the specs freeze

[J] These concern D-SPECS; they do not authorise implementation or freezing.

1. **Complete the typed evaluator and versioned identity contracts**: generation ownership, contact FK, source lineage, tagged null states, episode keys and partition reconciliation.
2. **Define the actual scoring algebra and class/path predicates**, including comparable scales, shared-root evidence handling and the father-target/P4 contradiction.
3. **Separate scored adverse residence from Sade-Sati testimony**, with distinct eighth- and twelfth-house fixtures and explicit zero-score assertions.
4. **Finish P5’s operand/comparator/availability contracts** and the G-10 payload definition; retain unavailable real-chart operands honestly.
5. **Replace every incomplete oracle fixture identified in Q2**, prove the designated mutations are discriminating, and correct 90° to Cancer.
6. **Restore the claimed plateau protection or record its explicit disposition**, removing nonexistent “protocol §B” references and unsupported closure labels.
7. **Issue an accurate closure/errata record**, including the remaining E1 count discrepancy without silently rewriting sealed history.

## Ranked amendments required before protocol acceptance

[J] These concern D-PROTO; they do not authorise candidate scoring or a flip.

1. **Repair and independently reconcile the event registry against every LEL ID**, including omitted events, date grains, uncertainty ranges and semantic proxies; then recompute all denominators.
2. **Choose one coherent T-FP estimand and independent truth mask**, with an explicit zero-event allowance and consistent civil-day convention.
3. **Fix rank eligibility, restored peak-diversity protection, interval-event N and signed ordering**; calculate validity before endpoint results.
4. **Resolve pooled versus macro aggregation, month containment, merge representatives and percentile semantics** in both prose and code.
5. **Supply computation coverage and the fixed class/tier/input contracts**; distinguish unavailable, absent, disabled and degenerate states.
6. **Regenerate matched-resolution controls** under a complete sampling specification.
7. **Rerun the pinned baseline under the corrected protocol**, regenerate its narrative and closure claims, and only then establish the candidate comparison floor.

## Disclosure and verification limits

[S] This review created, edited, moved or deleted no file; ran no git write command; connected to no database; and performed no tracker operation. Neither forbidden tracker directory was accessed. No candidate generation was scored.

[S] The shell rejected an initial here-document’s implicit temporary-file creation, and Git’s read-only reference queries emitted denied cache-creation warnings. I switched to `python3 -B -c`; no file writes succeeded. SC’s write-producing top level was not executed.

[S] Arithmetic was independently recomputed in memory. The stored control draws/hit counts and per-event outputs reproduce under the scorer’s current semantics. Selected scorer functions were executed only after extracting their pure definitions into an in-memory namespace.

**UNVERIFIABLE_HERE — [S][J]:**

- Whether the extract faithfully represents the live database, beyond its supplied predicate, metadata and verified hash.
- Actual searched coverage, unresolved search partitions and production manifest lineage.
- Served-corpus membership or doctrinal correctness; the sealed doctrine was not re-reviewed.
- Canonical-chart AV/donor/piṇḍa values, exact PD expectations and unreconciled LEL chart annotations.
- Swiss backend/data pins, actual crossing counts and certified solver bounds absent from the fixtures.
- Runtime execution of all 55 oracles, mutation-test receipts, writer behavior and sibling consumption.
- Historical authoring order or the claim that no candidate was scored elsewhere; these remain documentary assertions.

[S] A preliminary memory lookup provided historical checkout orientation only. All findings and numerical conclusions above rest on current file reads and this review’s computations.

