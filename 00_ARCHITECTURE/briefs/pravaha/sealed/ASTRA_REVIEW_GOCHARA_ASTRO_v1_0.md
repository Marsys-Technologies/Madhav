---
artifact: ASTRA_REVIEW_GOCHARA_ASTRO
version: "1.0"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra — independent adversarial review"
date: 2026-09-29
verdict: REWORK
reviewed_document_sha256: "270184f735c793b7ad69087c9a677233971a500fe2d9b37d4a00da174169ceb0"
authority: "Review only; authorizes nothing."
---

## A. Independent verification of the 27 findings

**The review identifies serious implementation defects, but its proposed replacement is not ready to become sealed doctrine.** Its strongest findings concern geometry, frames, lost residence intervals, static permission, and vedha handling. Its principal doctrinal error is turning a useful sequence of investigation into a universally necessary cascade. Several proposed repairs also contradict existing rulings. [J; R:49–60, 198–202, 237–245; SHEET:33–39, 46–53]

This review examined the worktree at HEAD `507a759bf5ef2289f10f139f2aa48fd2189bb9a6`. The document hash was independently computed with:

```text
shasum -a 256 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v2_0.md
270184f735c793b7ad69087c9a677233971a500fe2d9b37d4a00da174169ceb0
```

No files were written. No database, build, migration, container, or publication operation was used. Verification consisted of source and artifact inspection, primary-text inspection, arithmetic, and isolated, read-only Python probes of selected pure functions.

**Citation notation.** Paths below are relative to `/Users/Dev/madhav-l3/gochara-wp0-7`:

- `BRIEFS/` = `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/`
- `PY/` = `platform/python-sidecar/`
- `OCR/` = `00_ARCHITECTURE/SOURCE_DATA/classical_texts/`
- `R` = [FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v2_0.md](/Users/Dev/madhav-l3/gochara-wp0-7/00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v2_0.md)
- `V1` = `BRIEFS/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v1_0.md`
- `PLAN` = `BRIEFS/GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md`
- `SHEET` = `BRIEFS/GOCHARA_RULING_SHEET_v2_0.md`
- `NATIVE` = `BRIEFS/GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md`
- `DELTA` = `.run/wp10_tranche2/prod_link3_delta_report_482012f1.md`
- `RUN` = `.run/wp10_tranche2/prod_link3_step06b_runreport_482012f1.json`
- `CTX` = `.run/wp10_tranche2/link3_class_context_482012f1.json`
- `LEL` = `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`
- `BPHS1` / `BPHS2` = `OCR/BPHS/bphs_vol1_rsanthanam_djvu.txt` / `bphs_vol2_rsanthanam_djvu.txt`

**Evidence boundary.** Every production `[L]` measurement remains the author’s attributed measurement. Reading its saved report confirms what that report records, not the present database state. The OCR directories are a subset of the served corpus. Neither an unsuccessful file search nor an inspected edition establishes absence from `classical_text_chunks`. [U; PLAN:156; R:368–371]

| # | Verdict | Independent finding and evidence |
|---|---|---|
| 1 | **CONFIRMED** | [C] Noisy-OR saturates at 1 whenever any target weight is 1; the writer supplies unit weights for ordinary bhāva/lord/kāraka targets. The saved report records promise 1 for all 27 classes. This measures target presence, not natal promise strength. `PY/services/gochara_intensity/promise.py:61–74`; `PY/services/ka_gochara_resonance/writer.py:405–445`; `DELTA:18–44`. |
| 2 | **CONFIRMED** | [C] Step06a unions system activity across candidate instants; Step06b reuses the resulting class constant. A system active somewhere in the horizon becomes permission everywhere in it. `PY/scripts/kala_gochara_cutover/step06a_class_context.py:112–135`; `step06b_windows_projection.py:237–252`; `CTX:1–41`. |
| 3 | **PARTLY** | [C] The audited Gochara loading path defaults to level 1, and the portfolio query explicitly selects mahādaśās. “Anywhere” overstates the finding: this does not establish that the wider project lacks AD/PD data or readers. `PY/services/gochara_grammar/dasha_data.py:32–55`; `PY/services/gochara_v3/context.py:258–261`; `PY/services/ka_gochara_resonance/writer.py:836–841`. |
| 4 | **CONFIRMED** | [C] The engine’s Sade-Sati interval construction uses an open-ended terminal date. The pinned Step06b semantics retain its 0.10 weight despite the recorded testimony flag. Distinguish this from the current v3 engine, which contains an actual removal-and-renormalization implementation when testimony mode is applied. `PY/services/gochara_v3/engine.py:1978–2013, 1891–1937`; `PY/services/gochara_kernel/legacy_semantics.py:109–129`; `step06b_windows_projection.py:137–144, 237–252`. |
| 5 | **CONFIRMED** | [C] The natal loader preserves subjects such as `MOON`; w23 requests `Moon`. Step06b independently disables the mechanism by supplying missing operands. The asserted absence of tārā values from all served rows remains **UNVERIFIABLE_HERE**. `PY/services/gochara_v3/context.py:358–377`; `PY/services/gochara_intensity/enrichment.py:19–30`; `PY/services/gochara_v3/mechanisms/w23_tara_bala.py:213–244`; `step06b_windows_projection.py:237–252`. |
| 6 | **PARTLY** | [C] A zero-width episode contributes exactly zero through Step06b’s decay function, including at its exact instant. But ingress is legitimately an instant; the repair is to retain its resulting state or residence, not arbitrarily broaden every boundary into activity. The 98.6% and 253+369+29 figures are attributed chart-2 proxy measurements, not independently verified canonical-chart counts. `PY/services/gochara_kernel/episodes.py:367–414`; `step06b_windows_projection.py:209–228`; `R:134, 371`. |
| 7 | **CONFIRMED** | [C] The kernel computes genuine `ResidenceSpan` intervals, but enumeration stores only each span’s `ingress_episode`. Thus the repair is principally a lost-data contract repair, not invention of a residence solver. House occupation and house-level aspect support also require distinct relations. `PY/services/gochara_kernel/episodes.py:428–519`; `step06_enumerate_episodes.py:650–658`. |
| 8 | **PARTLY** | [C] Saved evidence records 647 unresolved targets: 595 yoga constituents and 52 lords. The lord resolver exists; missing required facts cause its failure. “Unimplemented lord resolution” would be an incorrect diagnosis. Current production counts remain **UNVERIFIABLE_HERE**. `PY/scripts/kala_gochara_cutover/evidence/step06_evidence.md:213–222`; `step06_enumerate_episodes.py:324–338`. |
| 9 | **UNVERIFIABLE_HERE** | [U] The asserted production map generation cannot be established without its database generation or a complete map export. Current writer code explicitly filters negative sensitive checks; that establishes intended behavior, not whether production was rebuilt. `PY/services/ka_gochara_resonance/writer.py:466–486`; `R:137`. |
| 10 | **CONFIRMED** | [C] There are **two** frame errors: Moon-relative rule houses are first matched against Lagna-based class house numbers, and the selected mechanism target is then resolved from Lagna. Merely adding `frame="moon"` to the resolver leaves the wrong rule selection intact. The actual legacy migration is under `platform/migrations/`, not the packet’s stated directory. `platform/migrations/266_bg_transit_tables.sql:53–56`; `PY/services/ka_gochara_resonance/writer.py:799–803, 939–950`; `step06_enumerate_episodes.py:386–419`. |
| 11 | **CONFIRMED** | [C] Rule polarity is copied directly into target weights, while activity clamps negative weights to zero. Negative weights can still enter the separate afflicting channel; they cannot independently generate activity magnitude. A favorable sixth-house rule is not automatically positive evidence for illness occurrence. `PY/services/ka_gochara_resonance/writer.py:304–309`; `PY/services/gochara_v3/engine.py:1189–1235`; `PY/services/gochara_kernel/legacy_semantics.py:481–531`; `PY/services/gochara_intensity/configuration_activity.py:133`. |
| 12 | **PARTLY** | [C] All **1,435 era rows** in the saved delta report are favorable. The run reports **4,415 total rows**, including month/day tiers; 1,435 is not the total window count. The resolver declares favorable whenever the supportive channel dominates, using class valence only when both channels vanish. `DELTA:18–44` and its era tables; `RUN:40–45`; `PY/services/gochara_kernel/legacy_semantics.py:535–552`; `step06b_windows_projection.py:489–511`. |
| 13 | **CONFIRMED** | [C][D] Directed aspects are solved at `target + angle`; the required transiter longitude is `target − angle`. Saturn and Mars are materially wrong. Jupiter’s 5th/9th labels interchange, although their union of physical root locations remains the same. Arithmetic follows below. `PY/services/gochara_kernel/contacts.py:204–212`; `PY/pipeline/transit_search.py:311–320`; BPHS ch.26, `BPHS1:16496–16529, 16559–16575`. |
| 14 | **CONFIRMED** | [C] Sign boundaries omit 0°; nakṣatra boundaries omit 0°; internal kakṣyā boundaries delegate cusps to the sign relation. Aries/Aśvinī therefore has no genuine boundary root from these lists. This does **not** imply that no Aries-labelled row can appear: the residence code can fabricate one at the horizon start, a separate defect. `PY/services/gochara_kernel/contacts.py:256–271`; `episodes.py:486–508`. |
| 15 | **CONFIRMED** | [C][D] Only full aspect angles are represented. The quarter/half/three-quarter scheme appears in BPHS ch.26 **vv.2–5**; vv.6–8 give further angular graduation. Neither is equivalent to an arbitrary 5° triangular neighborhood around selected exact aspects. `PY/services/gochara_grammar/primitives.py:189–199`; `PY/services/gochara_kernel/convention.py:45–60`; `BPHS1:16496–16529`. |
| 16 | **CONFIRMED** | [C] `failure`, `killing`, and `death` miss the dictionary keys `grade_2`, `grade_3`, `grade_4`, falling to 0.35. Laṭṭā is assigned an artificial three-malefic equivalent and reaches the same fallback when the scale is populated; without the scale it takes 0.70. Fixing the keys alone would preserve an unjustified generalization from battle doctrine. `PY/services/gochara_kernel/legacy_semantics.py:93–104, 690–693, 732–743`; `PY/services/ka_vedha_gochara/writer.py:551–558`. |
| 17 | **CONFIRMED** | [C] The gate checks outer row overlap but ignores `obstruction_active`, cancellation intervals, `suppression_factor`, and independence grouping. A clean row with zero malefics multiplies by 0.85. Two duplicates multiply twice. The writer itself also misrepresents obstruction timing; see C. `PY/services/gochara_kernel/legacy_semantics.py:696–783`; `PY/services/gochara_v3/engine.py:460–603`; `PY/services/ka_vedha_gochara/writer.py:505–536, 567–568, 609–645`. |
| 18 | **PARTLY** | [C] The frame mismatch and unevaluated bindu threshold are confirmed. The caller treats a returned sentence as a passed gate even though its detail explicitly says the bindu count was not resolved. “Never a positive factor” is too broad: favorable mechanism weights and an AV permission contribution exist, but neither constitutes correctly evaluated, residence-dependent gochara-phala. `PY/services/gochara_v3/context.py:405–411`; `engine.py:2093–2112`; `PY/services/gochara_grammar/primitives.py:779–809`; resonance `writer.py:304–309`. |
| 19 | **CONFIRMED** | [C] Readers expect subjects shaped as `planet.index`; the producer writes `KAKSHYA_1`…`KAKSHYA_8`. The primitive does not use donor identity. Its real-data branch would also need to translate sign-local boundary degrees into zodiac longitude. Contributor data must not be described as wholly unbuilt: the current strength writer contains a 672-row prastāra emission. `PY/services/gochara_v3/context.py:657–686`; `PY/services/gochara_grammar/primitives.py:631–721`; `PY/ga_writers/ga_strength_writer.py:1131–1167`. |
| 20 | **PARTLY** | [C] These distinctions are absent from the audited score assembly and target-weight contract, not necessarily from the project or L1 computations. “Anywhere” should be replaced with “not consumed by this Gochara scoring path.” `PY/services/ka_gochara_resonance/writer.py:405–445, 939–961`; `PY/services/gochara_v3/engine.py:1166–1254`; `step06b_windows_projection.py:274–310`. |
| 21 | **PARTLY** | [C] The writer reads houses/lords/kārakas while ignoring the ontology’s richer trigger, varga, and daśā fields. Point-target enumeration is broadly Cartesian, but interval targets restrict the agent, returns require the same body, and nodal dṛṣṭi is excluded. “Every body against every target” needs these exceptions. `PY/services/ka_gochara_resonance/writer.py:939–961`; `step06_enumerate_episodes.py:621–658`; `PY/services/gochara_kernel/convention.py:45–60`. |
| 22 | **PARTLY** | [C] Yoga attachment uses house-or-planet overlap and does not select yoga strength. The exact production prevalence of Kedāra remains **UNVERIFIABLE_HERE**. An overlap join cannot establish an event-specific yoga’s meaning. `PY/services/ka_gochara_resonance/writer.py:820–834`; `R:150`. |
| 23 | **CONFIRMED** | [C] “Afflicted” is parsed and attached as a qualifier; the scoring path does not test whether the specified lord is afflicted. A condition embedded in a target name is not an evaluated predicate. `PY/services/ka_gochara_resonance/writer.py:357–362, 412–434`; `step06b_windows_projection.py:274–310`. |
| 24 | **PARTLY** | [C] Plateau behavior and artificial day rows are real, but “13 × 0.6272” is wrong. Of the 13 childbirth rows shown for 2020–2022, **11** equal 0.6272; two are 0.637928 and 0.628875. Across all 41 childbirth era rows, values range from 0.066911 to 0.639888; 27 equal 0.6272. The day tier is still a numerical refinement of the same curve, without an independent day mechanism. `DELTA:493–533`; `step06b_windows_projection.py:410–471`. |
| 25 | **UNVERIFIABLE_HERE** | [U] The exact 1.26% and 99/127 production figures cannot be independently established. Saved evidence records 127 house-vedha, 24 SBC, 20 laṭṭā, and 74 mūrti rows. The more consequential confirmed defect is that missing overlay coverage produces a factor of 1 rather than an unavailable state. `PY/scripts/kala_gochara_cutover/evidence/step06_evidence.md:116`; `PY/services/gochara_kernel/legacy_semantics.py:715–718, 720–783`. |
| 26 | **CONFIRMED** | [C] Mūrti is absent from the inspected λ assembly; w21 explicitly uses the rule’s `min_sav_score` as a proxy. Do not generalize this to every AV-related function: another engine path does read sign-level BAV for the kakṣyā interim. `PY/services/gochara_v3/mechanisms/w21_av_gating.py:126–169, 186–192`; `PY/services/gochara_v3/engine.py:877, 1434–1478`; `step06b_windows_projection.py:300–303`. |
| 27 | **PARTLY** | [C] Global boundary events are enumerated inside each point-target loop, confirming structural duplication. The exact 31,401×3 ledger measurement remains attributed. The correct physical event identity must be independent of the class and target labels subsequently attached to it. `step06_enumerate_episodes.py:621–645`; `R:155`. |

### The decisive arithmetic and behavioral checks

**Directed dṛṣṭi.** With forward zodiacal aspect angle \(a\), transiter longitude \(b\), and target longitude \(t\):

\[
t=(b+a)\bmod360^\circ
\quad\Longrightarrow\quad
b=(t-a)\bmod360^\circ.
\]

- **Saturn:** target Sagittarius 24°15′ = 264.25°. Saturn’s third aspect is +60°, so Saturn must be at **Libra 24°15′ = 204.25°**. The code’s +60° root is **Aquarius 24°15′ = 324.25°**.
- **Mars:** target Cancer 10° = 100°. Mars’s fourth aspect is +90°, so Mars must be at **Aries 10° = 10°**. The code instead solves **Libra 10° = 190°**.
- Opposition survives the error because +180° and −180° coincide. Jupiter’s ±120° pair survives only as an unlabelled set; its directed aspect labels reverse. [C][D; `contacts.py:204–212`; `convention.py:45–60`; BPHS ch.26, `BPHS1:16496–16529, 16559–16575`]

Read-only probes of the selected source functions returned:

| Probe | Result | Consequence |
|---|---|---|
| `linear_no_box_decay(100,100,100,100)` | `0.0` | A boundary instant never activates this decay path. |
| `boundary_degrees(...)` | 11 sign, 26 nakṣatra, 84 internal kakṣyā boundaries; no 0° | The missing circular seam is confirmed. |
| Inactive house-vedha row, zero malefics | `0.85` | An unobstructed transit is attenuated. |
| Cancelled two-malefic row, supplied `suppression_factor=1.0` | `0.35` with the supplied grade scale | Cancellation is ignored. |
| `failure`, `killing`, `death` grade names | Each resolves to `0.35` | Severity distinctions collapse. |

These are isolated source-function checks, not database or production tests. Their implementing lines are those cited in A6, A14, A16, and A17.

## B. The timing hierarchy

**AMEND the decomposition; REJECT its universal combination law.** Promise → period → transit → finer timing is a useful order of inquiry. Classical rules do not establish that every event requires one interchangeable factor from each of these four bins, or that every finer rule is valid only inside a Jupiter/Saturn window. KP’s nested daśā/bhukti/antara and transit account supports hierarchical investigation within its school; BPHS’s AV rules include distinct solar-month, Jovian-year, and event-specific Saturn-transit procedures. These are different rule structures. [D][J; `OCR/KP_Reader/vol5/kp_reader_5_transits_djvu.txt:1293–1307`; BPHS ch.70 vv.7–9, 19–20, 24–27, 30–33, `BPHS2:40799–40809, 41041–41049, 41248–41259, 41537–41558`]

### Factor-by-factor adjudication

| Factor in §1.1–1.2 | Assignment verdict | Required amendment and reason |
|---|---|---|
| Natal houses, their lords, natural kārakas → L0 | **AGREE** | These establish event relevance. Add occupants and relationships rather than treating the house/lord/kāraka list as complete. The marriage example itself depends on a seventh-house occupant absent from the marriage signature. [P][J; `V1:97`; `R:87–101`] |
| Bhāva-bala, ṣaḍbala, dignity, varga strength → L0 | **AMEND** | Strength is capacity to deliver the planet’s significations, not a universal probability of a desirable event. An afflicted marriage configuration can promise marriage with difficulty; it must not simply suppress marriage occurrence. Preserve strength, condition, and outcome quality separately. [D][J; BPHS ch.34 discussion, `BPHS1:26040–26081`; `R:56, 169`] |
| Natal yogas → L0 | **AMEND** | Require a yoga-to-event predicate and the yoga’s actual conditions and cancellation. A strong yoga sharing one planet with childbirth does not thereby signify childbirth. [C][J; resonance `writer.py:820–834`] |
| Jaimini kārakas and padas → L0 | **AMEND** | Appropriate within a declared Jaimini rule path, including its kāraka convention, reference signs, rāśi-dṛṣṭi, and daśā variant. Do not silently treat every Jaimini sign as a Parāśari degree target. UL doctrine is locally attested; a generic UL transit rule is not thereby established. [D][U; Jaimini Abhyankar edition pp.55–56, `OCR/Jaimini_Sutram/jaimini_kva_abhyankar_djvu.txt:3193–3220`] |
| Sahams → lifetime, time-invariant L0 | **REJECT** | Annual-chart sahams belong to the annual chart and its year-specific rule context. Natal and annual saham calculations require distinct identities. The exact admitted Tājaka activation predicate is **UNVERIFIABLE_HERE**. [P][U; `R:56, 173, 283–285`] |
| Vimśottarī MD/AD/PD → L1 | **AGREE** | Use actual nested intervals and event-relevant relationships. PD is not inherently restricted to “month grain”; its duration follows its containing periods. Mere membership of a period lord in the natural-kāraka list is insufficient. [C][P; `writer.py:836–841`; `dasha_data.py:32–55`; KP5:1293–1307] |
| Chara daśā → L1 | **AGREE** | As the period mechanism of an admitted Jaimini path, not a fixed numerical vote interchangeable with Vimśottarī. Variant and applicability remain explicit. [J; `R:57`; `V1:135–139`] |
| Slow-body residence from Lagna → L1 licence | **AMEND** | It is broad **transit support**, normally a coarse L2 interval. It does not substitute for daśā licence merely because both last months or years. Its class meaning needs an explicit rule. [J; `R:57–58`; `V1:84–90`] |
| Slow-body residence from Moon → L1 licence | **AMEND** | Retain the Moon frame and the actual phala rule. Generic favorable residence is not an event-specific licence; generic unfavorable residence is not proof of a particular adverse event. [D][J; Phaladīpikā XXVI.1–2, [p.286](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/321)] |
| Sade-Sati, Kaṇṭaka, Aṣṭama Śani → adverse-class licences | **REJECT** as a blanket assignment | This reinstates an occurrence gate under a different name. N-15 removes the Sade-Sati composite from scoring. Individually sourced Saturn house results may remain distinct testimony or admitted rules; they do not license every adverse class. [J; `SHEET:46`; `R:57, 200, 239–240`] |
| Jupiter/Saturn degree conjunction and dṛṣṭi → L2 | **AGREE** | Usually useful for transit narrowing. Exactitude, residence, and graduated aspect strength are separate quantities. Saturn can have an exact day; that does not establish day-level predictive sufficiency. [D][J; BPHS ch.26, `BPHS1:16496–16529`; `R:33`] |
| Rahu/Ketu transits → L1/L2 | **AMEND** | Their daśās belong to the period layer; their residences and conjunctions to transit support/narrowing. Preserve dispositors/associations and N-14’s exclusion of nodal dṛṣṭi. [D][P; BPHS ch.34 v.16, `BPHS1:26213–26230`; `SHEET:39, 63`] |
| Double transit → L2 | **AGREE**, as a named practice rule | Specify “house or lord,” occupation/aspect, frame, conjunction of the two agents’ support intervals, and event scope. Do not make it necessary for every event or claim all three worked examples exhibit it. [P][J; `R:165`; D3 and F below] |
| Śodhya-/yoga-piṇḍa stars → L2 | **AMEND** | Preserve the particular AV, reference house, reduction procedure, transiting agent, and predicted result. BPHS’s father and progeny examples are specific Saturn adversity rules, not generic auspicious Jupiter/Saturn contacts. [D; BPHS ch.70 vv.7–9, 30–33; `BPHS2:40799–40809, 41537–41558`] |
| Retrograde passes → L2 | **AMEND** | Retain pass identity, station, and repeated opportunity as geometry/testimony. “The retrograde pass intensifies; the third delivers” is not admitted doctrine and conflicts with M-2 if converted into weight. [P][J; `R:175`; `SHEET:35`] |
| Mars → L2 only for adverse classes | **REJECT** | BPHS expressly associates Mars’s transit through suitably qualified AV signs with land gains and familial happiness. Mars can be a meaningful agent for constructive classes; adverse/beneficial outcome does not determine its temporal level. [D; BPHS ch.70 vv.24–27, p.888, `BPHS2:41248–41259`] |
| Mars → L3 always | **REJECT** | Temporal support depends on the rule, motion, and requested resolution. A categorical day-only restriction has no source demonstrated here. [J; same BPHS passage; `R:348–349`] |
| Tājaka year-lord, munthā, annual activation → L2 | **AMEND** | An annual path has its own annual context, narrowing relationships, and applicability. It need not be squeezed into a Vimśottarī-first path. Precise activation rules remain **UNVERIFIABLE_HERE** pending corpus adjudication. [P][U; `R:173, 354`] |
| Running AD/PD lord as target and transiting agent → L2 | **AGREE**, conditionally | Retain both relationships, with their actual period intervals and event-specific significance. Avoid counting target and agent aliases of one physical contact as independent evidence. [P][J; `R:166`; resonance `writer.py:836–841`] |
| Moon over house/lord/kāraka/period lord and trines → L3 | **AMEND** | Useful finer timing practice, not a universally sufficient OR-list. “Trines to anything relevant” needs a specific rule; otherwise it covers too much of every month. [P][J; `R:59, 170`; KP5:13056–13084] |
| Tārā-bala → L3 trigger | **AMEND** | It ordinarily qualifies lunar timing; a favorable tārā alone does not identify marriage, childbirth, or bereavement. Numerical modifiers such as 1.05 are implementation conventions, not textual quantities. [P][C; `w23_tara_bala.py:78–96, 213–244`] |
| Tithi–nakṣatra quality → L3 | **AMEND** | Appropriate to day qualification and particular election rules. It is not an event-class trigger merely because it is favorable. [P][J; `R:59, 177`; KP5:13056–13084] |
| Sun/Mercury/Venus → L3 only | **REJECT** | BPHS explicitly uses the Sun’s sign to select a **month** in an AV election rule. A fixed planet-to-grain assignment also ignores Mercury/Venus stations and retrograde intervals. [D][P; BPHS ch.70 vv.19–20, `BPHS2:41041–41049`] |
| Eclipses → L3 | **AMEND** | The astronomical instant is precise; the rule’s claimed effect interval need not be one day. Target relevance, source-defined sensitivity and, where required, visibility must be separate predicates. A real eclipse instant alone supplies no occurrence weight. [D][J; Phaladīpikā XXVI.26–29, pp.296–298, [chapter text](https://www.wisdom.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621598.html); `R:176`] |
| Moon’s own vedha → L3 | **AGREE** | As a qualifier of the Moon’s own transit result. Distinguish it from the Moon temporarily obstructing another planet’s transit. [J; `PY/services/ka_vedha_gochara/writer.py:455–483`; `SHEET:39`] |
| House vedha, exceptions, viparīta → Q | **AMEND** | Scope the obstruction to the specific primary transit, with simultaneous occupancy and cancellation intervals. It is not a global multiplier on unrelated class evidence. Preserve M-8’s source grading of commentary. [D][J; `BPHS1:24410–24442`; `SHEET:34`] |
| BAV → Q | **AMEND** | Use the specified graha’s AV and the rule’s correct raw/reduced marks. Classical BAV for the seven grahas does not justify inventing Rahu/Ketu BAV weights. [D; BPHS ch.66 vv.13–15, `BPHS2:35666–35684`; ch.70 vv.24–27] |
| SAV → Q | **AMEND** | Retain as a distinct aggregate. It does not replace graha-specific BAV, and a threshold cannot pass without the chart’s count. [C][J; `engine.py:2093–2112`; `w21_av_gating.py:126–169`] |
| Kakṣyā contributor → Q | **AMEND** | Use donor-specific data and the admitted source tier. N-21 does not permit medium-provenance testimony to become a weight simply because G-10 data exists. [J; `SHEET:38, 52–53`; `ga_strength_writer.py:1145–1167`] |
| Natural/functional nature and friendship → Q | **AMEND** | These modify interpretation of an agent–target relationship. They are not universal positive/negative coefficients. Dual lordship and association matter. [D][J; BPHS ch.34, `BPHS1:26040–26081, 26213–26230`] |
| Transit dignity → Q | **AGREE**, with rule scope | Phaladīpikā explicitly discusses dignity and combustion altering transit results. Implement those predicates in their stated context rather than a general “strong means favorable” multiplier. [D; Phaladīpikā XXVI.30–32, [p.299](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/334)] |
| Mūrti → multiplicative Q | **REJECT** pending adjudication | The implemented rule form is unverified, and M-4/N-21 permit a qualifier/testimony rather than an automatic score weight. [C][U; `PY/services/ka_moorti_nirnaya/logic.py:8–20, 81–86, 146–154`; `SHEET:37, 52`] |
| Laṭṭā → Q | **AMEND** | Preserve its own graha/star/result rules. The text does not make every laṭṭā equivalent to three malefics in a battle scale. [D][C; Phaladīpikā XXVI.44–48, [p.304](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/339); `legacy_semantics.py:104, 732–743`] |
| Koṭa → Q | **AMEND** | Testimony unless separately admitted; an unwired computation is not an omitted mandatory multiplier. [J; `SHEET:37`; `R:82, 194`] |
| Era/month/day → L1/L2/L3 | **AMEND** | These are output resolutions, not proof of distinct doctrinal mechanisms. A calendar-month clipping operation is not L2 astrology, and an argmax is not L3 astrology. [C][J; `step06b_windows_projection.py:407–471`] |

### The combination rule

**“OR within a level, AND across levels” is not adequate.** It permits unrelated factors to substitute for each other: an irrelevant slow residence can replace a relevant daśā, and a favorable tārā can replace a class-specific lunar trigger. It also excludes any valid method whose necessary conditions do not include every proposed level. [J; `R:49–60`]

The safer model is a union of **complete, source-qualified rule paths**:

\[
W_e
=
\bigcup_{r\in R_e^{\mathrm{admitted}}}
\left(
\bigcap_{p\in \mathrm{prerequisites}(r)}
I_p
\right).
\]

A double-transit path intersects Jupiter and Saturn support. A nested-daśā path intersects its relevant MD/AD/PD intervals and its specified transit conditions. A separate AV procedure retains its own conditions. Neither conjunction nor disjunction is inferred merely from the planet’s speed. **Unknown applicability is not false applicability.** [J; source-specific structures in BPHS ch.70 cited above]

Multiplication of Boolean indicators can represent an intersection. Multiplication of arbitrary normalized scores is an additional scoring convention; it is not equivalent to set intersection or a classical probability law. Likewise, noisy-OR assumes an independence structure not justified by aliases such as “Jupiter as kāraka,” “Jupiter as lord,” and “Jupiter as yoga constituent” sharing one physical contact. [J][C; `promise.py:61–74`; `engine.py:1232–1235`; resonance `writer.py:405–445`]

**Valence also needs three distinct fields:** evidence for occurrence, evidence against occurrence, and the outcome’s valence for the native. Evidence supporting bereavement occurrence is not a favorable bereavement. Surgery may be an adverse intervention with a beneficial outcome. The proposed `supports_class` correction is necessary but insufficient if its sign still becomes the window’s lived valence. [J; `R:62–64`; `legacy_semantics.py:535–552`; ontology shapes in `platform/supabase/migrations/456_brahma_event_ontology_dr13_shapes.sql:131–155`]

### What an ācārya does at L3 that the table omits

An ācārya does not merely search for the Moon touching any one of many targets. The finer inquiry can include narrower period subdivisions, the particular transit lord/star relationship prescribed by the school, the Sun’s month, the Moon’s condition, and—when electing an action—the local ascendant and the election’s actual requirements. KP’s transit volume explicitly discusses Moon star/sub significators together with daśā/bhukti/antara and election timing; that is a school-specific example, not authorization to mix KP cusp/sub calculations into the present Lahiri convention. [D][P; KP5 pp.218–219, `OCR/KP_Reader/vol5/kp_reader_5_transits_djvu.txt:13056–13084`; BPHS ch.70 vv.19–20]

Birth-time uncertainty, event-time uncertainty, and civil-day boundaries must also constrain the advertised precision. A precisely solved contact cannot repair an uncertain natal target or turn a date-only event record into an hour-level validation target. [J; `NATIVE:33–36`; `LEL:983–985, 1134–1136`]

## C. Missing and overkill audit

### M1–M13

| Item | Verdict | Adjudication |
|---|---|---|
| **M1: Double transit** | **AMEND** | Make it a first-class, explicitly modern-practice mechanism. Remove “produced all three worked events”: the father example supplies no Jupiter–Saturn double influence on the ninth house/lord. Do not make it universally necessary. [P][J; `R:112–119, 165`; F below] |
| **M2: Lords and running AD/PD lords** | **AGREE** | High priority. Extend the repair to occupants, dispositors, associations, and relationship roles; simply adding 7L does not recover the marriage example’s seventh-house Saturn. [C][P; `V1:97`; `R:95–101`; resonance `writer.py:405–445`] |
| **M3: AV weight of every contact** | **AMEND** | Correct the data consumption, but reject “every contact.” Preserve graha-specific BAV, SAV, contributor qualification, raw/reduced marks, and named piṇḍa procedures separately. No universal numerical contact multiplier has been established. [D][J; BPHS chs.66,70, `BPHS2:35666–35684, 40799–40809, 41248–41259`] |
| **M4: Promise from natal strength** | **AMEND** | Use event-specific promise and condition rather than a scalar measuring generalized strength. Distinguish absence, denial under a specified rule, unavailable evidence, and difficult realization. The proposed `(0,1]` range cannot express these states. [J; `R:56`; `promise.py:51–74`] |
| **M5: Agent nature and valence** | **AMEND** | Essential, but “Saturn on 7L and Jupiter on 7L are opposite events” is not a defensible universal rule. Functional role, association, period, natal condition, and the particular event must govern interpretation. [D][J; `R:169`; BPHS ch.34, `BPHS1:26040–26081`] |
| **M6: Moon pinpoint** | **AMEND** | Implement the ruled on-demand channel. Reject “the only classical source of day precision,” and do not require a universal slow-body precondition. [D][J; `R:170`; KP5:13056–13084; `SHEET:39`] |
| **M7: Slow residence as L1 licence** | **AMEND** | Restore residences as transit intervals, with explicit frames and phala. Do not promote generic residence into an interchangeable period licence. “Oldest transit doctrine in the corpus” is **UNVERIFIABLE_HERE** and unnecessary. [D][J; Phaladīpikā XXVI.1–2; `R:171`; A7/A10] |
| **M8: Graduated dṛṣṭi** | **AMEND** | The omission is real. Correct the verse attribution and distinguish BPHS’s aspect-strength function from M-1’s compact orb kernel before implementation. [D][C; `BPHS1:16496–16529`; `SHEET:33`] |
| **M9: Tājaka** | **AMEND** | A valuable separate annual path if the precise rules are admitted. Computing sahams does not establish an activation rule. Annual regeneration and year-specific identities must enter the cost model. [P][U; `R:173, 283–290`] |
| **M10: Jaimini** | **AMEND** | Natal kārakas/padas and Chara timing deserve a coherent school-specific path. A natal UL verse does not validate a Jupiter-to-UL transit rule, and argalā is not a universal numeric obstruction gate. [D][U; Jaimini Abhyankar pp.55–56, local lines3193–3220; `R:174`] |
| **M11: Retrograde passes** | **AMEND** | Keep physical pass structure. Do not admit “second intensifies/third delivers” as a score or assured event sequence; it conflicts with M-2 without further ruling. [P][J; `R:175`; `SHEET:35`] |
| **M12: Eclipses** | **AMEND** | Wire real instants and actual source-defined sensitivity. An eclipse on any target is not automatically a day-level event trigger. [D][J; Phaladīpikā XXVI.26–29, pp.296–298; `R:176`] |
| **M13: Day quality** | **AMEND** | Appropriate on demand, distinguishing election from description of an involuntary event. Separate Moon-as-primary transit from Moon-as-obstructor. [P][J; `R:177`; `ka_vedha_gochara/writer.py:455–483`; `SHEET:39`] |

### O1–O12

| Item | Verdict | Adjudication |
|---|---|---|
| **O1: Twelve-system weighted vote** | **AGREE** on removal; **AMEND** replacement | Fixed averaging is unsupported. However, a conditional classical daśā is not intrinsically “testimony only” forever. It can be an independent timing path when applicability and method are established. [D][J; BPHS ch.46 vv.17–23; `legacy_semantics.py:109–129`] |
| **O2: Fast bodies at L2** | **REJECT** the blanket demotion | Restrict by actual rule and duration. Sun’s monthly AV role directly contradicts day-only assignment; Mars can deliver gains. Per-agent orbs remain evidence-gated under M-1. [D; BPHS ch.70 vv.19–20,24–27; `SHEET:33`] |
| **O3: Fast-body kakṣyās are noise** | **AMEND** | Remove duplicated enumeration and keep unadmitted weighting out. Do not declare fast-body contributor qualification astrologically meaningless without a source or ablation. On-demand evaluation can preserve it cheaply where admitted. [J][U; `SHEET:38,52`; `R:185`] |
| **O4: Global ingress attached to each target** | **AGREE** | Store the physical boundary once; separately represent target-specific sign/star relevance and residence. [C][J; `step06_enumerate_episodes.py:621–645`] |
| **O5: Sensitive-degree targets** | **AMEND** | Fold duplicate natal-condition checks into the graha’s interpretation and enforce ruled exclusions. Do not erase explicitly admitted derived sensitive targets such as M-6’s Māndi/Gulika-based sign distances. [J; `SHEET:36`; resonance `writer.py:466–486`] |
| **O6: Static daśā portfolio** | **AGREE** | It duplicates natural kārakas and ignores the running period. Replace with actual period relationships, not another permanently expanded target list. [C; resonance `writer.py:836–841`] |
| **O7: Yoga attachment by overlap** | **AGREE** | Require a cited or explicitly provisional yoga→class relation, strength/condition, and relevant constituents. [C][J; resonance `writer.py:820–834`] |
| **O8: Fast-body returns** | **AMEND** | Retain the solar return as the annual-chart anchor. Do not infer that every other return is either annual or muhūrta-only. Generic return weights are unproven; cheap physical return records can remain available without scoring authority. [P][J; `R:190`; kernel `convention.py:45–60`] |
| **O9: Approximate SBC gate** | **AGREE** | A cyclic-opposite approximation is not a named Sarvatobhadra grid. Testimony only until the actual school, geometry, and rule are established. [J; `R:191`; `ka_vedha_gochara/writer.py:445`; `SHEET:37`] |
| **O10: Moon vedha in century gate** | **AMEND** | Remove broad, undifferentiated attenuation. A lunar primary transit belongs in the Moon channel; a lunar obstruction of a slow primary transit is a different relation requiring explicit scope and, under M-3, admission before scoring. [C][J; `writer.py:455–483`; `SHEET:39`] |
| **O11: Three century-wide tiers** | **AGREE**, with coverage safeguards | On-demand day computation is sound. “Top-N” must be a prefetch policy, not an exclusion of other requested periods or an assumption that an uncomputed interval is empty. [J; `R:309–312`; `NATIVE:34–36`] |
| **O12: Nodal dṛṣṭi, other daśā votes, koṭa** | **AMEND** | Keep N-14 and remove unsupported votes/weights. Do not conflate a ruled rejection of nodal aspects with the doctrinal status of an independently applicable daśā method. [J; `SHEET:37,46,52`; `R:194`] |

### Higher-leverage omissions

**1. The missing object is an event-specific relationship model, not another list of points.**

The review’s marriage example relies on Saturn because it occupies the natal seventh house. Yet its proposed principal target repair adds lords and period lords, not a general occupant relationship. Its father example requires “father’s longevity/loss” relationships rather than the native’s generic eighth-house symbolism. Its node-period examples require associations and dispositors. A flat weighted set cannot express these differences. [C][P][J; `V1:97–110`; resonance `writer.py:405–445, 939–961`; BPHS ch.34 v.16 and commentary, `BPHS1:26213–26230`]

The required rule record should identify at least:

```text
event class and affected person
reference frame / reference object
agent → relation → object
natal and period prerequisites
applicability and source qualification
temporal support and coverage
evidence for/against occurrence
outcome valence and severity
```

This has higher leverage than adding a universal double-transit multiplier: it determines which double transit, whose event, and why that contact is relevant. [J; A10–A12, A21–A23]

**2. The supposed M-1 implementation is linear in time, not angular separation.**

Step06b interpolates from ingress time to exact time to egress time. M-1 requires \(1-|\Delta(t)|/\mathrm{orb}\). They coincide only under constant angular speed on each side. For a synthetic approach \(\Delta(t)=-5+5t^2\), at \(t=0.5\) the time triangle is 0.5 while the ruled angular factor is 0.25. This matters especially around stations and retrograde loops. [C][J; `step06b_windows_projection.py:209–228, 284–292`; `SHEET:33`; compare correct angular computation in `engine.py:1198–1209`]

**3. The residence helper fabricates exact ingress claims.**

When no ingress root matches a clipped residence start, it assigns `t_exact=ca`, `branch="direct"`, and `exact_crossing=True`. It searches only the lower sign boundary even though retrograde entry occurs through the upper boundary. A read-only synthetic probe, entirely resident within Aries and with no boundary roots, nevertheless emitted an applied exact Aries ingress at the horizon start. This violates computation fidelity and can misgrade mūrti. [C; `episodes.py:443–447, 468–473, 486–508`; `CLAUDE.md:223, 314–336`; `SHEET:59`]

Enumeration also drops episodes with `t_exact=None`, although a contact may overlap the requested horizon while its exact center lies outside it. Such coverage must remain a truncated span, not become absence. [C; `episodes.py:299–337`; `step06_enumerate_episodes.py:614–619`; `PLAN:171`]

**4. Vedha needs an interval relation, not one row per primary residence.**

The writer collects every obstructor overlapping any part of a residence, counts their union as though simultaneous, records only the first obstruction interval, finds only the first cancellation, and emits the outer row across the entire primary residence. Repairing the consumer’s cancellation check cannot recover the discarded temporal structure. [C; `ka_vedha_gochara/writer.py:455–512, 524–536, 567–568`]

Furthermore, the one-to-five-malefic fear/failure/killing/death/ignominy scale is presented in the inspected text **in a battle context**. The writer explicitly acknowledges extending it to ordinary transit vedha. Its numeric suppressions therefore remain unsupported even after the grade-key repair. [D][C; Phaladīpikā commentary, [p.318](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/353); `writer.py:551–558`]

**5. Two supposedly settled exclusion rules still fail in the projection.**

- N-17 moves the 90-day separation filter to serve time; Step06b retains it in production of peaks. [C; `SHEET:48`; `step06b_windows_projection.py:417–424`]
- `birth_anchor` is documented as an epoch-tautology kill-switch exclusion, yet the saved report records 43 era, 43 month, and 43 day windows for it. The kill-switch is descriptive text, not enforced behavior. [C; resonance `writer.py:290–296`; `DELTA:20`]

**6. Numerical success is being mistaken for source verification.**

The mūrti helper returns `verse_cited` and `corpus_verifiable=true` whenever a grade was computed. These flags must follow a verified rule and its source—not the success of a calculation using an unverified table. [C; `ka_moorti_nirnaya/logic.py:70–86`; `NATIVE:356–368`; `CLAUDE.md:344–372`]

### Classical mechanisms missing from the reviewed proposal and audited scoring path

The following deserve explicit adjudication. They do not all need immediate implementation.

| Mechanism | Source and significance |
|---|---|
| **Sign-third fruition** | [D] Phaladīpikā XXVI.25 assigns different portions of a sign to the fruition of different planets. This is an explicit within-residence timing mechanism omitted by a pure exact-contact model. It deserves attention before inventing per-agent narrow orbs. |
| **Transit-to-transit modification of phala** | [D] Phaladīpikā XXVI.30–32 treats aspects from benefics/malefics, dignity, and combustion as modifying transit results. This requires moving-body relationships, not merely transits to natal points. [p.299](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/334) |
| **Saptashalākā and specified sensitive stars** | [D] Phaladīpikā XXVI.26–29 discusses Janma/Karma/Ādhāna and a scheme including Abhijit. A universal 27-equal-nakṣatra grid is not a sufficient substrate for every such rule. |
| **Aṅga-gochara** | [D] Phaladīpikā XXVI.35–40 gives body-specific results from natal-star counting. This is distinct from ninefold tārā-bala and cannot be represented by relabelling w23. |

The first, third, and fourth passages are in the inspected [Phaladīpikā chapter XXVI](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621598.html), pp.296–303. Their admission in the served corpus remains **UNVERIFIABLE_HERE**.

The code-side scope of this finding is the audited Gochara scoring path, supported by its relation set and factor assembly, plus a read-only `rg -n -i` search for `anga.?gochara|anga.?gocara|sapt.?shal|sapta.?śal|saptasal|decan|drekk|combust|itthas|dispositor|sukshma|sookshma` across the five Gochara service families. That search found only a `dispositor_strong` test fixture. It is not a claim that no related computation exists elsewhere in Madhav. [C; `convention.py:45–78`; `step06b_windows_projection.py:274–310`]

## D. Answers to the nine doctrine questions

### D1. Hierarchy and Mars

Use the hierarchy as an explanatory workflow and a computation strategy, not a universal necessary-condition theorem. Mars belongs wherever the admitted event-specific rule places its temporal support; neither “L2 only for adversity” nor “L3 always” survives BPHS’s Mars-AV gain rules. Slow residence is transit support, not a substitute daśā licence. Nodes retain period, residence, conjunction, association, and dispositor roles without reopening N-14. [D][J; B above; BPHS ch.70 vv.24–27; BPHS ch.34 v.16]

### D2. Direction, frames, and Aries

All three defects are confirmed. Required corrections are:

1. Directed root equation \(b=t-a\), with separate Saturn and Mars regression cases.
2. Frame-correct **rule selection and target resolution**.
3. A circular boundary set including 0°, with crossing direction and horizon clipping preserved.

The existing false-ingress fallback must be repaired alongside the boundary list; otherwise an Aries-labelled synthetic row can mask the missing-root defect. [C; A10, A13, A14; `episodes.py:486–508`]

### D3. The six source adjudications and required corpus counts

**Mūrti-nirṇaya.** The inspected code implements a 27-nakṣatra offset table repeating four grades. The proposed rāśi procedure counts the Moon’s sign at the transiting planet’s ingress from the natal Moon sign, with groups:

| Grade | Rāśi count from natal Moon |
|---|---|
| Gold | 1, 6, 11 |
| Silver | 2, 5, 9 |
| Copper | 3, 7, 10 |
| Iron | 4, 8, 12 |

These are different functions, not alternate encodings. I recognize the rāśi form as **[P] practice**, but its primary-text admission is **UNVERIFIABLE_HERE**. The code’s citations do not establish the nakṣatra-mod-4 form: BPHS ch.28 in the inspected volume concerns Iṣṭa/Kaṣṭa, and the named mūrti passage was not verified in the inspected Phaladīpikā chapter. Preserve true-ingress timing under A-1; quarantine the rule-form and provenance claims pending source adjudication. [C][U; `ka_moorti_nirnaya/logic.py:8–20, 146–154`; `platform/supabase/migrations/401_bg_transit_moorti.sql:30–116`; `BPHS1:229`; `SHEET:59`]

**Venus vedha.** The coded **11→3 and 12→6 are correct** in the inspected Phaladīpikā passage. Its ordered favorable positions are `1,2,3,4,5,8,9,12,11`; the corresponding vedha positions are `8,7,1,10,9,5,11,6,3`. Sorting one list without preserving pair correspondence creates the alleged reversal. Do not “repair” these two pairs. [D; Phaladīpikā XXVI.6–8, [p.288](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/323)]

**Double transit.** “Phaladīpikā ch.26 §double-gochara” is not a verified citation for the modern Jupiter–Saturn rule. No such named prescription was identified in the inspected chapter; that does not prove absence from all classical literature. K. N. Rao’s own account describes the research he called the double-transit phenomenon, providing primary evidence of modern codification. The inspected book identifies 1995/1996 editions. Classify the mechanism as **[P] modern practice**, not a Phaladīpikā verse. [P][U; K. N. Rao, *Yogis, Destiny and the Wheel of Time*, PDF pp.167,184, [primary text](https://storage.yandexcloud.net/j108/library/5tgvew7s/K.N._Rao_-_Yogis,_Destiny_and_the_Wheel_of_Time.pdf)]

The database seed is additionally narrower/different: it describes both planets occupying the same Moon-relative house, not the proposed occupation-or-aspect of a house-or-lord network. The repair needs a method-definition change, not merely a new citation string. [C; `platform/supabase/migrations/397_bg_transit_av_gates.sql:56–85`]

**Aṣṭottarī.** BPHS ch.46 vv.17–20 states the condition involving Rahu in a kendra or trikoṇa **from the Lagna lord**, with Rahu excluded from Lagna. The quoted natal chart has Lagna lord Mars in Libra and Rahu in Taurus: Taurus is the **eighth** from Libra, so it fails that condition. Verse 23 also gives the day/Kṛṣṇa-pakṣa or night/Śukla-pakṣa recommendation; its relation to the first condition must be declared as an adopted interpretive variant rather than silently ignored. I have not independently verified the birth’s day/night and pakṣa operands. [D][U; BPHS ch.46 vv.17–23, pp.513–514 onward, `BPHS2:3256–3266, 3595–3598`; natal positions `R:87–90`]

**Jaimini UL/DK transit rules.** Local text confirms natal Upapada-related rules, including its second-house conditions. That does not confirm a generic “Jupiter/Saturn transits UL or DK, therefore marriage” predicate. The transit-specific proposition remains **UNVERIFIABLE_HERE**. [D][U; Jaimini Abhyankar pp.55–56, local lines3193–3220]

**Tājaka saham activation.** Saham definitions, a computed coordinate, a year-lord, and an activated event are separate claims. The precise admitted activation rule remains **UNVERIFIABLE_HERE**; it must include the annual context and whatever lordship/aspect/application conditions the source actually specifies. [P][U; `R:173, 354`; `SHEET:37`]

**Required read-only corpus queries—not executed here.**

The repository schema provides `text_id`, `chunk_id`, `verse_ref`, chapter/verse fields, Sanskrit, English, summary, and source citation. [C; `platform/migrations/ws2_l0_texts.sql:42–55`]

Use this base:

```sql
WITH c AS (
  SELECT
    text_id, chunk_id, verse_ref, chapter, verse_start, verse_end,
    source_citation,
    concat_ws(' ', content_sa, content_en, content_summary) AS txt
  FROM classical_text_chunks
)
SELECT text_id, count(*) AS candidate_chunks
FROM c
WHERE /* one predicate below */
GROUP BY text_id
ORDER BY text_id;
```

For every count, retrieve the matching text and neighboring chunks before declaring a rule confirmed. Candidate count is not doctrine count.

| Question | Exact candidate predicate | Expected result and limit |
|---|---|---|
| Mūrti form | `txt ~* '(m[ūu]rti|moorti|moorthi|मूर्ति|suvar[nṇ]|swar[nṇ]|gold|silver)'` | Count **unknown**. Inspect ordered groups and whether the operand is rāśi or nakṣatra; do not accept a generic gold/silver mention. |
| Venus ordered pairs | `text_id = 'phaladeepika' AND verse_ref ~ '^PG323(:|$)'` | Expect the relevant passage if the author’s page inventory is current; actual count **unknown**. External primary-text confirmation is positive. |
| Double transit | `txt ~* '(jupiter|guru|brihaspati|bṛhaspati|गुरु)' AND txt ~* '(saturn|shani|śani|sani|शनि)' AND txt ~* '(transit|gochar|gocar|गोचर)'` | Co-mentions may occur. Count and count of an exact modern-style rule are **unknown**; co-mention does not establish conjunction of necessary influences. |
| Aṣṭottarī | `text_id ~* '(bphs|parashara|parāśara)' AND (txt ~* '(ashtottari|astottari|aṣṭottar|अष्टोत्तर)' OR (chapter = 46 AND verse_start <= 23 AND verse_end >= 17))` | Expect positive candidates corresponding to the local text; exact count **unknown**. Read vv.17–23 together. |
| UL/DK transit | `txt ~* '(upapad|dara.?karak|dārakārak|उपपद|दारकारक)' AND txt ~* '(transit|gochar|gocar|गोचर)'` | Exact-rule presence **unknown**. Broaden to separate target-term searches and neighboring chunks so a split passage is not missed. Natal-only hits do not qualify. |
| Tājaka saham | `text_id ~* '(tajak|tājak|nilakan|nīlaka)' AND txt ~* '(saham|sahama|सहम)'` | Definitions are expected if the attributed inventory is current; activation-rule count **unknown**. Read associated year-lord, munthā, and applying-relationship passages. |

A separate Moon/node recount should begin with `text_id='phaladeepika' AND verse_ref ~ '^PG(321|331)(:|$)'`, then retrieve neighboring pages. Phaladīpikā XXVI.2 explicitly gives Moon-relative transit positions and treats the nodes with the Sun; XXVI.24 gives Rahu results. This corrects a broad absence premise, **not** every node-specific vedha pair or nodal aspect rule. [D][U; [XXVI.1–2, p.286](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/321); `SHEET:39,63`]

### D4. Which daśās are licences?

| System | Adjudication |
|---|---|
| Vimśottarī | Primary configured path is reasonable; use nested periods and actual significations. [P][J] |
| Chara/Jaimini | A separate school-specific path when its exact variant and target grammar are admitted. [J] |
| Aṣṭottarī | Conditional; applicability must be evaluated. The quoted chart fails the Rahu-relative-to-Lagna-lord condition. [D] |
| Mudda | Consider within an admitted annual Tājaka path, not as a generic lifetime voter. [P][U] |
| Yoginī, Kālacakra, Nārāyaṇa | No fixed cross-system vote. Testimony under the current admission state; potentially independent paths after explicit method/applicability adjudication. [J][U] |
| Naisargika | Do not treat generic age-period symbolism as an interchangeable class-event licence without an admitted event rule. [J][U] |

This removes the unsupported weighted average without declaring that one chosen school invalidates all other timing methods. [J; `legacy_semantics.py:109–129`; `R:183`; BPHS ch.46 applicability passage cited above]

### D5. BAV-bindu → weight

**I would admit no universal numerical BAV-to-λ mapping on the evidence available.**

First normalize the mark convention. In the inspected Santhanam BPHS edition, **bindu/dot denotes the inauspicious mark and rekhā the auspicious mark**. Much software uses “bindu” for the favorable point. A source citation can therefore support the opposite polarity from the column’s informal name. [D; BPHS ch.66 vv.13–15, p.844, `BPHS2:35666–35684`]

The data contract must distinguish:

- the graha whose BAV is evaluated;
- donor-specific prastāra versus aggregate BAV versus SAV;
- favorable versus unfavorable marks;
- unreduced versus the particular reduced AV required by the rule;
- **known zero**, missing, unavailable, and not applicable.

Known zero favorable marks cannot simply mean “unqualified”: BPHS gives a substantive adverse result for Mars transiting a sign without rekhās. [D; BPHS ch.70 vv.24–27, `BPHS2:41248–41259`]

The M-7 bands—0 unqualified, 1–3 damp, 4 neutral, ≥5 amplify—are explicitly a WP8 hypothesis, not a sourced multiplier schedule. Preserve that status. Initially admit the verified count and rule-specific interpretation; promote a numeric map only through the required source review and non-vacuous ablation. [J; `SHEET:38,52–53`]

A corpus candidate predicate is:

```sql
txt ~* '(ashtakavarg|aṣṭakavarg|अष्टकवर्ग)'
AND txt ~* '(bindu|rekh|रेखा|बिन्दु|point|dot)'
AND txt ~* '(transit|gochar|gocar|गोचर)'
```

Expected: relevant AV passages; actual count **UNVERIFIABLE_HERE**. No supplied evidence establishes a universal multiplier such as `bindus/4`.

### D6. Day tier at build time or on demand?

**On demand by default; optional explicit prefetch.** The request must identify the class, interval, rule set, chart/input generations, civil-time convention, and required precision. Cache the result with its own searched coverage.

Do not require that the interval already appear among top-ranked coarse windows if the requested admitted method does not require that coarse mechanism. Do not call an uncomputed interval “no signal.” [J; `R:309–312`; `SHEET:39`; `NATIVE:34–36`]

### D7. Class-signature corrections

The five examples named in §7 all need work, but not merely larger lists.

| Signature | Required correction |
|---|---|
| `career_change` | Rahu alone is not an adequate kāraka model. Express changes in role, employer, vocation, status, or location as distinct relationships involving the actual tenth-house network and relevant period lords. Do not equate every Rahu contact with change. [P][J; `V1:100`; ontology seed `388_brahma_ghatana_ontology.sql:39–120`] |
| `property_acquisition` | Retain fourth house/lord and Mars, but add the actual acquisition predicate and relevant natal relationships. A single adverse mechanism cannot represent purchase versus loss. Mars’s favorable AV transit rule supplies a concrete source-based avenue. [D][J; `V1:104`; BPHS ch.70 vv.24–27] |
| `bereavement` | Separate the native’s own longevity from loss of father, mother, spouse, child, or another person. The native’s 2/7 māraka set is not automatically a relative’s death signature. Use the affected-person frame and named significator rules. [D][P][J; `V1:108`; BPHS ch.70 vv.7–9] |
| `marriage` | Include relevant natal occupants and relationships, plus UL/DK only within an admitted Jaimini path. Saturn’s seventh-house occupation matters in the worked chart; adding only Venus/7L leaves the example unrecovered. [P][J; `V1:97`; `R:87–101`; Jaimini pp.55–56] |
| `childbirth` | Distinguish fifth from Lagna, fifth from Moon, fifth from Jupiter, and their lords. BPHS explicitly supplies the Jupiter-reference AV procedure. “5L-of-5L” is ambiguous: fifth-from-fifth is the ninth house, whereas fifth from the fifth lord’s occupied sign is another construction. State the exact operand. [D][J; `V1:98`; BPHS ch.70 vv.30–33] |
| `parental_event` | Mother/father and gain/illness/loss cannot share an undifferentiated activation-to-valence mapping. [J; `V1:108`; ontology shape migration456:131–155] |
| `separation`, illness classes, surgery, loss/deception | Evaluate the written affliction predicates. Separate occurrence, severity, recovery, and outcome; mere contact with a listed malefic is insufficient. [J][C; `V1:97–108`; resonance `writer.py:357–362,412–434`] |
| `birth_anchor` | Enforce its existing exclusion from predictive λ. It documents the epoch and must not produce later-life birth windows. [C; resonance `writer.py:290–296`; `DELTA:20`] |
| Remaining broad/provisional classes | Retain explicit provisional status until their event definition, evidence requirements, and source-specific predicates are adequate. Overlap-based target expansion is not a substitute. [J][C; resonance `writer.py:278–300,820–834`] |

### D8. Does sparse evaluation lose admissible mechanisms?

**Sparse evaluation need not; the proposed pruning does.** A compulsory slow-residence/double-transit window would exclude admitted routes whose conditions differ, including Sun-month AV selection, Mars’s favorable AV transits, and independently applicable annual procedures. Restricting all day computation to the current L2 union would preserve those omissions indefinitely. [D][J; BPHS ch.70 vv.19–20,24–27; `R:268–272,309–312`]

Pruning must be justified separately for each rule path: an interval may be discarded only when a necessary predicate for that path is demonstrably false. [J]

### D9. Expected retrodictive gain

This ranking is a **judgment about likely error reduction**, not a measured gain:

1. Correct frames, directed aspects, and residence/coverage integrity.
2. Recover lords, occupants, relationships, and dynamic MD/AD/PD relevance.
3. Repair vedha timing/cancellation and remove unsupported global attenuation.
4. Separate occurrence evidence from lived valence.
5. Consume correctly interpreted AV data and event-specific procedures.
6. Add explicit double-transit and graduated-dṛṣṭi methods.
7. Add source-qualified day timing.
8. Add coherent Jaimini/Tājaka paths and further qualified techniques.

The first four repair invalid inputs and meanings; additional mechanisms cannot compensate for them. [J; A10–A18, C1–C6]

Move measurement preparation ahead of implementation, rather than leaving it as Tier 3. The three showcased events have already influenced the hypothesis and cannot serve as untouched held-out confirmation. [J; `R:85–121,250–253`]

## E. Efficient implementation

**The architectural direction is sound; the claimed losslessness, algebra, and cost bounds are not established.**

### E1. Global physical events

A shared sky-event substrate is appropriate for sign, nakṣatra, kakṣyā boundaries, stations, and eclipse instants. Index it by ephemeris/convention generation, ayanāṃśa, node convention, body, grid definition, branch, and physical relation. Keep chart interpretations separate. [J; `R:276–281`; kernel `convention.py:45–78`]

The substrate must distinguish a 27-star grid from a source-specific scheme involving Abhijit. Moving-body aspects, combustion, and tithi require relative-body geometry; local election or visibility predicates additionally require location/time context. One natal-point contact table cannot answer all of these. [D][J; Phaladīpikā XXVI.26–32; BPHS ch.46 note on Abhijit, `BPHS2:3600–3603`]

### E2. Deduplicate geometry without deleting meaning

Solve a physical coordinate/relation once, then retain separate role edges: lord, occupant, kāraka, period lord, yoga constituent. Those edges may support different interpretations but do not become independent physical observations. [J; `R:282–287`; resonance `writer.py:405–445`]

“Approximately ten points” is an observation about the collapsed current map, not a bound on the corrected model. M-6 derived points and annual sahams expand the target domain; annual points are not necessarily constant across a century. Preserve interval targets as intervals rather than converting their cusps into points. [J; `SHEET:36`; `episodes.py:429–434`; `R:283–285`]

### E3. Lazy refinement

Lazy Swiss refinement is reasonable if each approximation carries a certified error bound and the computation refines whenever that uncertainty could change membership, ordering, boundary identity, or a reported peak. [J]

Do **not** replace the existing `precision_regime` values with `spline|swiss`: the ratified field means `instant_grain|date_grain`. Add a separate solver-method field and angular/time uncertainty bounds. [C][J; `NATIVE:36`; `R:292–295`; `ka_moorti_nirnaya/logic.py:74–78`]

A one-arcsecond longitude error is not a one-second time error. Away from stations, the approximate relationship is:

\[
\delta t \approx \frac{\delta\lambda}{|\dot{\lambda}|}.
\]

Near zero speed, that conversion becomes unstable; grazing contacts and root multiplicity need explicit treatment. Precision must be established for the claimed temporal result, not inferred from the spline’s angular accuracy alone. [J; `R:294`; `PLAN:171`]

### E4. Interval algebra

Replace daily Cartesian sampling with indexed interval joins and an event sweep. Include changes in period, residence, contact branch, exactitude, station, AV cell, obstruction, cancellation, and other applicable predicates.

But **λ is not piecewise-linear merely because individual factors are**. Even \(f(t)=t\) and \(g(t)=1-t\) produce \(f(t)g(t)=t-t^2\), whose interior maximum is missed by endpoint-only evaluation. Noisy-OR likewise creates products. The ruled angular decay is also not linear in time under nonuniform motion. [J][C; `R:300–305`; `engine.py:1232–1235`; `step06b_windows_projection.py:209–228`]

Use:

1. Exact interval operations for categorical prerequisites.
2. Factor segments with explicit functional forms.
3. Interior-extremum and threshold-root solving where scores are retained.
4. Certified adaptive refinement when a closed form is unavailable.

A sweep can approach \(O(B\log B+\text{output})\) for categorical interval construction, where \(B\) is the number of relevant boundaries. Score extrema add their own numerical cost; they are not automatically free. [J]

### E5. Cost model

Several estimates need correction before they are cited as engineering evidence:

| Claim | Assessment |
|---|---|
| L1 uses OR, but cost uses daśā fraction × residence fraction | Inconsistent. Multiplying 25–40% by 25–35% assumes an intersection, and its estimated size additionally requires information about dependence. It cannot price the stated OR model. [J; `R:49–57,268–270`] |
| Sun has approximately 33 nakṣatra crossings/year | Incorrect for a 27-equal-star zodiac and one sidereal circuit. Use 27, with the grid convention explicit. [C][J; `contacts.py:261–262`; `R:278`] |
| All global boundary rows over 250 years total \(10^4–10^5\) | Not plausible if it includes the Moon. An illustrative calculation using a 27.32166-day lunar circuit gives about \(250(365.25/27.32166)(12+27+84)\approx411{,}082\) labelled boundary crossings for the Moon alone, before merging coincident labels. If Moon events are excluded or generated on demand, say so. [J; read-only arithmetic probe; `R:276–279`; `contacts.py:256–271`] |
| Approximately 40,000 contact roots | **UNVERIFIABLE_HERE** as a corrected-system count. It depends on actual targets, retrograde recrossings, additional aspect levels, annual points, and admitted methods. [J; `R:282–290`] |
| Sub-minute ledger; low-single-digit-minute build | **UNVERIFIABLE_HERE**. Large savings are plausible from eliminating duplicated solves, but no corrected implementation benchmark supports this bound. [J; `R:321–335`] |
| Every doctrine change is projection-only | False. Aspect-direction repair, additional partial-aspect levels, frame-dependent targets, larger support domains, and target-generation changes can require new geometry. [C][J; A10/A13/A15; `R:316–319`] |

Benchmark cold and warm shared caches separately. Report physical root count, Swiss calls, unresolved spans, coverage, peak preservation, and wall time. Correctness must be compared against independently evaluated rule cases, not merely against the old pipeline’s erroneous output. [J; A13–A17; C2–C5]

### E6. Recommended data separation

A better implementation retains three distinct objects:

1. **Physical geometry:** immutable, convention-versioned events and spans.
2. **Interpretive rules:** event roles, frames, prerequisites, source status, and method version.
3. **Evaluated windows:** rule-path evidence, coverage, uncertainty, optional score, and output resolution.

This permits incremental recomputation without pretending that every change is only a reweighting. Preserve the ruled external identity contract and generation lineage; coordinate invalidation with Kṣetra, Saṅgam, and downstream consumers. An artifact can be structurally fresh while its doctrine is wrong. [J; `NATIVE:33–37`; `CLAUDE.md:221,291–293,314–372`]

## F. The three worked events

The event dates and quoted positions are treated as attributed project records. I independently checked the arithmetic and doctrinal interpretation; I did not independently retrieve L1 facts or rerun the project’s L0 ephemeris.

### F1. Marriage — 2013-12-11

**The slow-transit reading is substantially useful; the hierarchy claim and L3 dismissal are not established.**

From the quoted positions:

- Transit Saturn Libra 24°15′ versus natal Saturn Libra 22°26′ gives a return separation of **1°49′**.
- Jupiter Gemini 24°34′ casts its fifth aspect to Libra 24°34′: **2°08′** from natal Saturn and **0°19′** from transit Saturn.
- Ketu Aries 12°59′ versus Lagna Aries 12°26′ gives **0°33′**.

These support a modern double-transit reading of the seventh-house complex, conditional on the practice rule’s admission. They do not establish that the exact degree convergence is a classical probability or that only those months were possible. [P][J; `R:87–101`; `V1:223–224`]

The more important target lesson is **Saturn as natal seventh-house occupant**. The current marriage signature has 7/2, 7L, and Venus. Simply resolving 7L therefore does not recover the example. Mercury MD may be investigated through its dispositor Saturn in the seventh; Ketu AD through its occupied-sign lord Mars in the seventh. These are relationship-based practice readings, not direct-kāraka membership. [P][J; `V1:97`; `R:87–90`; `LEL:886–913`; BPHS node association discussion, `BPHS1:26213–26230`]

The claim that the date was a chosen muhūrta is not established by the cited event-log entry. Even if established, election would not justify “the engine should report L2 and stop”: an election can itself be analyzed. Moon in Pisces is twelfth from Lagna but **second from the natal Moon**, a distinction the review should preserve. Exact Moon degree, event time, relevant finer periods, and election constraints remain **UNVERIFIABLE_HERE**. [D][U; `R:98–99`; `LEL:886–913`; Phaladīpikā XXVI.1–2]

Finally, the saved candidate report covers 2020–2030. Statements about what that particular build “sees” in 2013 are deductions from its grammar, not observed output for the marriage date. [C][U; `DELTA:6`; `R:100–101`]

### F2. Twin daughters — 2022-01-03

**The “fifth from Moon” assertion is false and must be corrected before sealing.**

Natal Moon is Aquarius. Transit Jupiter in Aquarius is **first from Moon**, not fifth. The fifth from Aquarius is **Gemini**, whose lord is **Mercury**, not Jupiter. This changes the stated basis of the L1 licence and supplies a relevant Mercury-MD relationship the author missed. [C][J; arithmetic from `R:87–90,104–105`; contradictory annotation `LEL:1158`]

The Lagna-based transit reading is more defensible:

- Jupiter in Aquarius aspects Leo, the natal fifth, by its seventh aspect.
- Saturn Capricorn 18°01′ lies **3°57′** from natal Sun Capricorn 21°58′, the fifth lord.

This is a house-plus-lord double-transit pattern under the modern practice definition. It is not simultaneous degree contact with one physical target, and must be represented accordingly. [P][J; `R:106–107`]

At the quoted Moon position, Sagittarius 29° lies in Uttarāṣāḍhā. Natal Moon Aquarius 27°03′ lies in Pūrvabhādrapadā. Counting inclusively from natal star 25 to transit star 21 gives 24, hence the sixth tārā, Sādhana, in the ninefold practice scheme. This is a qualification of the **quoted instant**, not the entire birth date; Moon near a sign boundary and absent birth timestamps prohibit a whole-day assertion. [P][C; `R:87,108`; `w23_tara_bala.py:78–96`; independent integer arithmetic]

Do not infer twin daughters from “Rahu multiplies” alone. The event log’s interpretation is not a verified doctrine predicate. A fuller natal/progeny inquiry could inspect the admitted divisional and Jupiter-reference rules, but their required facts are not available in this review. [P][U; `LEL:1158–1161`; BPHS ch.70 vv.30–33, `BPHS2:41537–41558`]

The event log itself contains incompatible annotations: Rahu/Ketu in Aries/Libra rather than the review’s Taurus/Scorpio; Moon in Pisces rather than the quoted Sagittarius; natal Ketu in Leo rather than the quoted Scorpio. Preserve the native’s event observation while reconciling these computed annotations against authoritative L1/L0. They cannot serve as benchmark ground truth. [C][U; `LEL:1152,1155,1159`; `R:87–90,108–109`]

### F3. Father’s passing — 2018-11-28

**The Saturn–ninth-lord contact is relevant to investigate; the asserted universal double-transit pattern is not present.**

Saturn Sagittarius 13°26′ is **3°39′** from natal Jupiter Sagittarius 9°47′, the native’s ninth lord. The quoted Scorpio cluster occupies the native’s eighth sign. These are observations; “Saturn in ninth is the strongest classical father-death trigger” is not established by them. [P][J; `R:112–117`; `LEL:1001,1008–1009`]

Jupiter in Scorpio aspects Pisces, Taurus, and Cancer by the admitted full Parāśari aspects. It does not thereby aspect Sagittarius or the ninth lord’s Sagittarius location. Consequently the statement that **all three events** were produced by L2 double transit is refuted for this worked presentation. [C][J; `R:114–119`; `convention.py:45–60`]

A more discriminating practice inquiry uses the father reference:

- Father’s ninth-house reference: Sagittarius.
- Eighth from Sagittarius: Cancer, ruled by **Moon**, the reported AD lord.
- Seventh from Sagittarius: Gemini, ruled by **Mercury**, the reported MD lord.
- Natal Mercury in Capricorn occupies the second from that father reference.

This does not establish a death prediction, but it is a more specific period relationship than “the native’s eighth house contains several planets.” Its applicability and natal corroboration must be evaluated explicitly. [P][J; natal arithmetic from `R:87–90`; periods `LEL:993–995`]

A separate, textually precise investigation is BPHS’s Sun-AV procedure: the **ninth from the natal Sun**, which is Virgo for the quoted Capricorn Sun, and its specified piṇḍa calculation and Saturn-star transit. The required AV operands are **UNVERIFIABLE_HERE**. [D][U; BPHS ch.70 vv.7–9, `BPHS2:40799–40809`]

Saturn in Sagittarius is **eleventh from the natal Moon**. Phaladīpikā’s Saturn-ninth result belongs to its Moon-relative frame and cannot be imported as Saturn-ninth-from-Lagna. The inspected eleventh-house Saturn result is favorable; that generic phala neither proves nor disproves this specific family event. [D][J; Phaladīpikā XXVI.22–23, [p.295](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/ocr/1621570/330); `LEL:1001`]

The event log also says January 2020 is approximately two months after November 2018; it is approximately fourteen months. This reinforces the need to validate computed annotations separately from the native’s dated observation. The saved 2020–2030 candidate report does not directly demonstrate the 2018 output. [C; `LEL:1000`; `DELTA:6`]

## G. Verdict and mandatory amendments

**Verdict: REWORK.**

The document is valuable as a defect inventory and an architectural proposal. It should not be sealed as doctrine until its universal cascade, source attributions, worked-example errors, ruling conflicts, and newly identified implementation defects are corrected. No demonstrated runtime improvement or retrospective fit currently establishes the proposed amended engine’s accuracy. [J; A–F above]

### Ranked amendments before sealing

| Rank | Required amendment | Evidence and acceptance condition |
|---|---|---|
| **1** | **Repair physical geometry and coverage before interpreting another score.** | Correct directed Saturn/Mars aspects, the 0° seam, lost residence spans, synthetic ingress instants, and dropped truncated contacts. Demonstrate direct/retrograde, station, circular-seam, and horizon-edge cases. `contacts.py:204–212,256–271`; `episodes.py:443–508`; `step06_enumerate_episodes.py:614–658`. |
| **2** | **Replace the flat signature list with explicit event relationships and frames.** | Correct both rule selection and resolution; add occupants and period relationships; separate native/relative references. Distinguish occurrence evidence from lived valence. A10–A12, A21–A23; C1; F. |
| **3** | **Restore genuinely temporal permission.** | Evaluate nested MD/AD/PD and applicability at the relevant instant. Remove union-over-horizon permission and enforce N-15 on the actual projection path. `step06a_class_context.py:112–135`; `step06b_windows_projection.py:237–252`; `SHEET:46`. |
| **4** | **Rebuild vedha semantics as simultaneous, scoped interval relations.** | Preserve all obstruction/cancellation subintervals, exceptions, independence, and unknown coverage. Remove battle-derived universal suppressions unless separately admitted. `writer.py:455–568`; `legacy_semantics.py:696–783`; M-8; Phaladīpikā commentary p.318. |
| **5** | **Correct the review’s doctrine and example errors.** | Venus pairs stay 11→3/12→6; Jupiter Aquarius is first from Aquarius Moon; father example is not demonstrated double transit; modern double transit loses the false Phaladīpikā citation; mūrti provenance is unresolved. D3 and F. |
| **6** | **Replace universal level gating with source-qualified rule paths.** | Keep coarse-to-fine evaluation, but specify necessary predicates per method and union complete alternatives. Reject fixed planet-to-grain rules and unsupported global multiplication. B; BPHS ch.70 vv.19–20,24–27. |
| **7** | **Define AV and aspect semantics before assigning weights.** | Normalize bindu/rekhā polarity, raw/reduced status, donor identity, and known-zero versus unknown. Distinguish full classical dṛṣṭi strength from the ruled compact orb kernel. D5; BPHS chs.26,66,70; `SHEET:33,38,52–53`. |
| **8** | **Bring the projection back into conformance with existing rulings.** | Implement angular M-1 rather than a time triangle; move the 90-day filter to serve time; enforce `birth_anchor` exclusion; preserve precision-field semantics. C2/C5; `SHEET:33,48`; `NATIVE:36`; resonance `writer.py:290–296`. |
| **9** | **Replace the cost promise with a measurable algorithm contract.** | Correct OR/intersection pricing, Moon boundary counts, nonlinear extrema, geometry invalidation, and annual target generation. Benchmark cold/warm cost with coverage and rule-level correctness. E; `R:268–335`. |
| **10** | **Prepare validation and downstream migration evidence before adding mechanisms.** | Reconcile event-log annotations; predeclare evaluation rules and negative/control intervals; measure recall, active duration, false-positive burden, timing error, and per-mechanism contribution. The showcased examples are development cases. Version changed methods and propagate lineage to dependent assets. `LEL:1000,1152–1161`; `R:250–253`; `CLAUDE.md:221,291–293,314–372`. |

### Rulings the native should be asked to revisit or clarify

| Ruling or premise | Recommendation |
|---|---|
| **M-7 known-zero interpretation; N-22 missing-data boundary** | **Clarify and, if necessary, amend.** A known zero favorable AV count can be doctrinally meaningful; it is not unavailable data. Preserve N-22’s treatment of an unresolved operand, while separating it from observed zero and normalizing source polarity. BPHS ch.66 vv.13–15 and ch.70 vv.24–27; `SHEET:38,53`. |
| **M-1’s claimed classical warrant** | **Revisit the source rationale, not silently the authorized implementation.** The compact linear orb kernel is an explicit method convention; BPHS’s graduated dṛṣṭi is a different angular function. Implement the currently ruled angular kernel faithfully while asking whether a separately versioned classical profile should be studied. `SHEET:33`; `BPHS1:16496–16529`. |
| **M-3/G-9 absence premises concerning Moon/node house results** | **Revisit the source premise.** The inspected Phaladīpikā passage provides positive evidence that the earlier broad absence statement was too strong. Recount the served pages. This does not authorize nodal aspects or automatically source every nodal vedha pair. `SHEET:39,63`; Phaladīpikā XXVI.1–2,24. |
| **Mūrti rule form and source admission** | **Request an explicit adjudication.** Keep A-1’s true-ingress requirement. Do not treat that ruling as approval of the nakṣatra-mod-4 table or its automatically generated `verse_cited` stamp. `SHEET:59`; `ka_moorti_nirnaya/logic.py:8–20,81–86,146–154`. |

**No reopening is recommended for** Lahiri/Swiss consistency, mean-node consistency, persisted identity and coverage, M-8’s exceptions and honestly graded commentary, N-14’s nodal-aspect exclusion, N-15’s removal of Sade-Sati weighting, M-2’s testimony-only retrograde state, or N-17’s producer/serve-time separation. The review should comply with those rulings. Its proposed adverse-class Sade-Sati licence, retrograde intensification, automatic mūrti weighting, and retention of a producer peak-separation filter must not enter through ambiguous wording. [J; `SHEET:33–39,46–53`; `NATIVE:33–37`; `R:175,198–202,239–245`]

