---
artifact: ASTRA_REVIEW_DESIGN_SPECS
version: "1.2"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra — independent adversarial review (round 3, closure)"
date: "2026-09-30"
verdict_specs: REWORK
verdict_protocol: REWORK
reviewed_packet: "design/reviews/CLOSURE_PACKET_DESIGN_SPECS_v1_2.md"
reviewed_packet_sha256: "962645273cdb3985f17581c704b2e2782c4ef74bd05fa44021364e3bc0f25cde"
hash_method: "Recomputed with shasum -a 256; packet and five reviewed files checked again at close."
reviewed_file_sha256:
  design/GOCHARA_DESIGN_SPECS_v1_2.md: "5bfe1553d404be59f9b0246fcf410fe5a09be6946b5d97da6d733ecede45b039"
  design/GOCHARA_TEST_ORACLES_v1_2.json: "c11a9d7e5ccf3a6c4a53569da5383ea7531ce840e48cfa6f7e0b8e2310143a43"
  measurement/EVALUATION_PROTOCOL_v2_1.md: "21de59943b335abb3df393810155c2a0d07315c5b1ae7fee5d54e93e7f5c7f1d"
  measurement/EVENT_REGISTRY_v2_1.md: "ec738020dd2fbbe492317089a8ac5723169756740de932cea408aeb5cde7f34c"
  measurement/BASELINE_3_0_v2_1.md: "b4c46222fe23fbd51b5028004d11a11cfafb422de124c23c4f4867bfb8a4ce60"
authority: "Review only; authorizes nothing."
---

**Specs v1.2 + oracles v1.2: REWORK.**

**Protocol v2.1 + registry v2.1: REWORK.**

The headline baseline figures reproduce. The freeze blockers concern incomplete contracts, contradictory fixtures, and unenforced validity rules. Of the fifteen requested closure judgments, **three are CLOSED and twelve are PARTLY CLOSED**.

This review is limited to the requested round-2 findings, C.1–C.4, and blocking regressions introduced by these changes. I compared the requested changes in [Astra round 2](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/reviews/ASTRA_REVIEW_DESIGN_SPECS_v1_1.md:371) and [Kimi NK-1/NK-2](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/reviews/KIMI_K3_REVIEW_DESIGN_SPECS_v1_1.md:112) against the artifacts themselves.

`[S]` means current local source inspection or independent in-memory calculation; `[J]` means review judgment. **[L] means the production evidence supplied by the steward**, not a database query performed by this reviewer.

Citation keys below identify exact files; `DS:80–95` denotes their repository line numbers.

| Key | File |
|---|---|
| DS | [design/GOCHARA_DESIGN_SPECS_v1_2.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_2.md) |
| O | [design/GOCHARA_TEST_ORACLES_v1_2.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_2.json) |
| P | [measurement/EVALUATION_PROTOCOL_v2_1.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTOCOL_v2_1.md) |
| ER | [measurement/EVENT_REGISTRY_v2_1.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVENT_REGISTRY_v2_1.md) |
| B | [measurement/BASELINE_3_0_v2_1.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/BASELINE_3_0_v2_1.md) |
| SC | [measurement/rerun_3_0_v2_1_scorer.py](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/rerun_3_0_v2_1_scorer.py) |
| X | [measurement/baseline_3_0_extract_v1_0.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/baseline_3_0_extract_v1_0.json) |
| CT | [measurement/random_controls_v1_1.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/random_controls_v1_1.json) |
| AV0 | [design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json) |
| AV1 | [design/L1_ASHTAKAVARGA_EXTRACT_v1_1.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/L1_ASHTAKAVARGA_EXTRACT_v1_1.json) |
| RC | [design/RECONCILIATION_DESIGN_SPECS_v1_1.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/RECONCILIATION_DESIGN_SPECS_v1_1.md) |
| LEL | [01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md](/Users/Dev/madhav-l3/pravaha/01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md) |

**Closure table — [S][J]**

| Finding | Status | Evidence against the original requested change |
|---|---|---|
| **R2-S01 — typed contract** | **PARTLY CLOSED** | `generation`, `contact_id`, and `signature_house` exist. However, `record_id` remains a sole PK whose hash excludes **both generation and contact_id**, despite generation-scoped records and multiple contact episodes. Two otherwise identical episode records therefore collide. Path/predicate/factor PKs remain unversioned, and their references are not composite version-bound FKs. `temporal_support=[]` still means only uncomputed; computed-empty support and unknown-admission handling remain unspecified. Source-fact lineage is not supplied by `source_text`. **DS:80–105,143–172,294–299.** |
| **R2-S02 — episode identity** | **PARTLY CLOSED** | Contact identity now includes an ordinal, resolving repeated crossings within a fixed crossing set. But the set has no fixed origin/domain: extending a partition backwards can insert an earlier crossing and renumber published contacts. Canonical serialization, null-centre ordering, seam association, and publication-safe extension remain unspecified; “updates the row in place” does not establish publication immutability. O-RX-1 supplies no partition-extension or alias fixture. **DS:454–471; O:59–64.** |
| **R2-S03 — scoring algebra and P4** | **PARTLY CLOSED** | Product composition and factor-null propagation are added. Actual factor functions, compatible ranges/units, evidence accumulation, shared-root aggregation, and exhaustive class/agent/target sets remain absent. The father test narrows its target set while calling it the actual table set; that table still includes 2/7/8 from the ninth. Its new same-target requirement conflicts with O-RP-3’s house-plus-lord admission. **DS:102–105,143–185,214–235; O:122–134.** |
| **R2-S04 — AV comparator/availability/G-10** | **PARTLY CLOSED** | G-10 now includes reductions/piṇḍas, and O-BP-5’s 24/28 values cross a band. But “doctrine’s stated expectations” still supplies no nonzero BAV comparator or explicit unresolved qualification. The new table records current operand availability rather than the requested missing-input matrix. The contradiction survives: missing SAV affects P5b independently, while missing BAV still supposedly disables P5b. **DS:244–275,541–565; O:318–344; AV1:8–26.** |
| **R2-S05 — scored residence versus testimony** | **PARTLY CLOSED** | The eighth-house calculation is correct, and the two mechanisms are separated. The requested **named native adverse class** is still replaced by “the chart’s ADVERSE classes”; this does not enforce P2’s native-only scope. The testimony test asserts zero score effect but supplies no concrete scored baseline and does not assert unchanged admission. **DS:189–196,320–336; O:143–155.** |
| **R2-S06 — complete, discriminating fixtures** | **PARTLY CLOSED** | Cancer is corrected; inventory equality passes at 57; numerical operands and nonempty audit assertions were added. Many original placeholders remain, PD expectations are still absent, generators are generally not complete, and no explicit unknown-applicability admission fixture was added. O-SM-1’s newly printed formula leaves Δ undefined. C.4 details the remaining failures. **O:13–15,52–64,87–113,199–211,283–302; DS:648–655.** |
| **R2-M01 — source-complete registry and observation meaning** | **PARTLY CLOSED** | All **57 source IDs occur exactly once**: 3 dev + 47 held-out + 7 excluded. SPR.D and the three finer grains are restored. But the expressly identified 2007–2008 and 2021–2022 ranges are still flattened to 2007 and 2021. Vertigo’s note acknowledges a peak but retains `point`/`chronic_onset`, while `point` is defined as dated onset. The requested source-reconciliation invariant is still replaced by “any differing scorer has a bug.” **ER:30–39,78–110,155–156; LEL:427–435,1105–1113,1679–1687; P:171–172.** |
| **R2-M02 — T-FP estimand** | **CLOSED** | Burden is the union of admitted days divided by H; the budget uses the same H. Prediction-dependent exemptions are removed. Zero-event allowance and engineering-policy constants are explicit; code uses `max(n_c,1)`. **P:118–127; ER:133–148; SC:228–236.** |
| **R2-M03 — validity before rank** | **PARTLY CLOSED** | Two-horns exclusions and peak-diversity are implemented; **0/30** is correct here. But `era_indiscriminate` is calculated and printed without controlling the rank block. A generation-wide void can therefore still produce a rank median. Validity failures are printed, not emitted as the requested machine-readable failure; saved per-event percentiles lack eligibility/void status. **P:157–166; SC:160–180,183–187,208–226,267.** |
| **R2-M04 — ranking and aggregation contract** | **PARTLY CLOSED** | Interval N now uses the start year, signed ordering replaces absolute values, percentile asymmetry is stated, and endpoint aggregation is explicit. Merge representative selection remains only in code; tie tolerances differ between ranking and peak-diversity. Partial-year observation-mask treatment is not frozen. The asserted sign-convention stop is absent. **P:64–65,69–84,111–117,176–178; SC:93–109,148–153,179,101–105.** |
| **R2-M05 — matched controls** | **PARTLY CLOSED** | Grandfather controls are 61 days, the other interval is 59, and the final valid start is included. However, controls remain rolling spans rather than the requested matched calendar units. Moreover, P specifies month=30/year=365, while SC uses actual source-month/source-year lengths: **20 events differ**, including 31-day months and 366-day years. The stored controls reproduce the code, not that prose. **P:141–147; SC:247–261; CT.** |
| **R2-M06 — operational input contracts** | **PARTLY CLOSED** | T-honesty is correctly declared unverifiable without a manifest, and manual enforcement is disclosed. The requested machine-readable registry, complete class/polarity/eligibility table, prediction-tier selector, and coverage-manifest contract are still absent. P points to a nonexistent complete DS class table; SC still derives its universe from emitted rows. DS still claims an ER per-row verification state that ER does not contain. **P:49–56,128–132,150–155; DS:214–224,680–681; ER:51–52,88–89; SC:28–30,161,239–245.** |
| **R2-M07 — baseline narrative** | **PARTLY CLOSED** | “No observed separation,” 22/5/0, 15/16 misses, and unavailable T-honesty are corrected. The newly printed dedup account is still wrong: the nine “denser” classes named at B:30–32 each merge to **10**, not 27/29/30. Independent recomputation and the scorer’s own merge block agree. **B:27–35,45,53–77; SC:84–99.** |
| **NK-1 — omitted event/arithmetic** | **CLOSED** | SPR.D is restored; exact ID reconciliation passes; 57=3+47+7, T-cover=32/47, and the revised 30-event rank cohort/floor 16 are stated with amendment disclosure. The broader observation-meaning residual remains R2-M01. **ER:12–21,100–110,150–154; P:11–22,103–117; B:41–43.** |
| **NK-2 — distinguish recurring contacts** | **CLOSED** | The requested occurrence ordinal is explicit, and O-RX-1 provides three dated crossings under one physical tuple with ordinals 1/2/3. This closes NK-2’s narrower same-set recurrence request; extension stability remains open under R2-S02. **DS:460–471; O:59–64.** |

**C.1 — Do the claimed closures actually close the requested changes?**

Only the three marked CLOSED above do so fully. Added columns do not establish version-bound keys; a product operator does not define numerical factors; disclosure of manual enforcement does not supply the requested input contracts.

The calculations themselves reproduce as follows. I independently parsed ER, loaded X and CT, and calculated in memory with `/opt/homebrew/bin/python3 -B -c`.

| Measure | Independent result [S] | Difference from B |
|---|---:|---|
| Held-out population | **47 = 5 exact + 23 month + 2 interval + 17 year** | None |
| Observed horizon | **10,334 days** | None |
| T-cover | **32/47 = 68.085106%**, 15 misses | None |
| T-time | **182 days**, 2/5 misses | None |
| Uncapped exact-event hit errors | **686, 998, 327 days** | None |
| Valid T-rank | **0/30**, floor **16**, no valid median | None |
| Era fingerprint | **210/351 = 59.829060%**; generation-wide void | None |
| Two-horns | **22 high / 5 low / 0 in-band** | None |
| Materialised controls | **645/940 = 68.617021%** | None |
| T-honesty | **UNVERIFIABLE** | No computation-coverage manifest |

All stored control dates and per-event control hit counts reproduce. All saved per-event baseline outputs also reproduce under the scorer’s current semantics. Controls exceed event coverage by **0.531915 percentage points**; this is descriptive, not an inferential finding.

The per-class T-FP recalculation is:

| Adverse class | \(n_c\) | Admitted days | Burden % | Budget % | Result |
|---|---:|---:|---:|---:|---|
| bereavement | 1 | 10,321 | 99.874202 | 2.612735 | FAIL |
| career_setback | 1 | 10,321 | 99.874202 | 2.612735 | FAIL |
| chronic_onset | 2 | 10,321 | 99.874202 | 5.225469 | FAIL |
| financial_deception | 1 | 10,321 | 99.874202 | 2.612735 | FAIL |
| illness_acute | 1 | 10,321 | 99.874202 | 2.612735 | FAIL |
| parental_event | 1 | 10,321 | 99.874202 | 2.612735 | FAIL |
| separation | 1 | 9 | 0.087091 | 2.612735 | PASS |
| surgery | 1 | 10,321 | 99.874202 | 2.612735 | FAIL |
| major_loss | 0 | 10,321 | 99.874202 | 2.612735 | FAIL |

Three differences matter despite unchanged headlines:

- **Dedup narrative:** career_setback, financial_deception, major_gain, major_loss, chronic_onset, parental_event, relocation and spiritual_turn are **70→10**; psychological_arc is **64→10**. B:30–32’s 27/29/30 counts are incorrect.
- **Control specification:** 15 month events use 31 days and five year events use 366 days, contrary to P:142. Regenerating with the prose’s 30/365 lengths coincidentally also yields **645 hits**, but produces a different experiment. Equal headline totals do not reconcile the definitions.
- **Validity enforcement:** in-memory execution of SC’s rank block with `era_indiscriminate=True` and an otherwise eligible cohort still prints a rank median. The historical **0/30** result does not prove enforcement of the generation-wide void.

**C.2 — O-PP-1 and the daśā source discrepancy**

**[L][J] O-PP-1’s MD/AD expectations are correct under the declared Lahiri convention. They must not be replaced with Mercury/Sun, Mercury/Rahu and Mercury/Saturn.**

The steward’s supplied production evidence gives:

| Date | `lahiri_chitrapaksha`, Vimshottari MD / AD / PD |
|---|---|
| 2013-12-11 | **Mercury / Ketu / Mercury** |
| 2018-11-28 | **Mercury / Moon / Venus** |
| 2022-01-03 | **Mercury / Rahu / Venus** |

The reconciliation’s alternatives match **`surya_siddhanta_classical`**, as the steward states. RC:109–110’s assertion that no ayanamsha variant explains the discrepancy is therefore contradicted by [L].

O-PP-1 still does not print the PD expectations: “PD lord asserted exactly” and “+ PD” are placeholders, not expected values (**O:199–204**).

Before freeze, the daśā-read contract must pin:

1. Canonical chart ID; **`ayanamsha_id='lahiri_chitrapaksha'`**; **`system_id='vimshottari'`**.
2. The complete daśā build identifier corresponding to supplied **`1f89fd4c`**, separately from natal-position build `1c092ffb` and AV build `aa9602ce`.
3. Event instant/timezone, period-boundary convention, hierarchy level, parent MD/AD linkage, and selected row IDs.
4. **A duplicate-row selection rule.** Within the pinned build and period identity, select the qualified `two_pass_verified` record rather than an arbitrary `single` duplicate. Specify deterministic handling of identical duplicates and reject conflicting equally qualified records; an unordered first row is insufficient.

The supplied [L] evidence establishes the expected lords at these dates. Full period boundaries and row identifiers remain unavailable in this review.

**C.3 — G-10 caveats**

**[S][J] The four requested caveats are carried honestly in the specification and extract metadata:**

- `single_pass` is preserved verbatim: **DS:246–249,255–256,546–550; AV0:8–12; AV1:9–12**.
- The `aa9602ce`/`1c092ffb` relationship is supported by a **reported recomputation**, not asserted common lineage: **DS:550–553; AV0:608–611**.
- The `pinda_sarva` per-subject split remains explicitly outside recompute coverage: **DS:249,273–274,553–555; AV1:19–26**.
- P5c is disabled as **rebuild-pending**, with #2731 named, rather than described as sourceless: **DS:248,262–266,555–556; AV0:613**.

I verified 96 AV0 rows, 200 AV1 rows, the stated category counts, and the SAV sum **337**. I did not independently rerun PyJHora or verify production lineage.

There is a separate new oracle-provenance defect: O-BP-1 and O-BP-5 attribute synthetic test values to AV0 when those values are absent there. See R3-S03 below.

**C.4 — Are all `given` fields now buildable, and are the labels truthful?**

**No.** The inventory is sound: **57 unique IDs**, exact equality with the DS index, **44 `literal`** and **13 `constrained_generator`** labels. The universal buildability claim is not sound.

Several local tests are materially improved: O-AD-4, the fixed-set recurrence case, O-SM-2’s refinement trigger, O-BP-1’s competing values, O-BP-5’s band crossing, and O-SM-3/O-AO-2’s nonempty assertions. These do not close the remaining round-2 fixture requirements.

| Remaining fixture problem | Evidence |
|---|---|
| **Period records and expectations remain incomplete.** O-RR-2 supplies no pinned period rows; O-PP-1 supplies no PD values; O-PP-2 still invokes an undefined transition rule and introduces incorrect controls. | **O:73–78,199–211** |
| **Relationship/path fixtures still use placeholders.** Examples include “a real degree,” “object X,” “declared orb,” “pinned score,” unnamed strength/condition records and an unspecified qualified tuple set. O-RR-5 adds 0.8 and a cancellation description but not a complete yoga/rule/input record. | **O:87–120,157–176** |
| **The scored/testimony split lacks the requested complete cases.** No named native adverse class, concrete nonzero baseline or admission comparison is supplied. Evidence/valence fixtures also retain unspecified contributing records and values. | **O:143–155,178–197** |
| **Vedha fixtures lack complete rule/grade/coverage inputs.** O-VI-2 assigns March 1 to both its closed attenuated interval and its closed clean interval. Adding timestamps did not settle the boundary convention. | **O:220–253**, especially **228–230** |
| **Solver fixtures remain underdetermined.** O-SS-1 says flags are pinned without printing them. O-SS-2 gives endpoint longitudes without interpolation or exact expected roots. O-SS-3 does not actually supply separate residence and degree-contact cases. | **O:255–274** |
| **O-SM-1’s “full” formula is incomplete.** Δ has no value and the comparison tolerance is not numerical. With Δ=30 days, its endpoint activity is 0, not 0.6. With Δ=60 days, endpoint activity is 0.6 but interior activity reaches 1, contradicting the asserted endpoint maximum. These are illustrative completions of an unspecified parameter, not assumed intended values. | **O:283–288** |
| **AV declaration/donor tests remain incomplete.** O-BP-2 omits independent BAV/SAV availability cases; O-BP-3 supplies no nonempty declaration/evaluation fixture; O-BP-4 still omits the actual degree, donor key and matrix cells. | **O:318–337** |
| **Generator labels do not supply generators.** “The built substrate,” “the annual object row set,” “a built contact ledger,” “the authority-generation manifest,” and “a non-empty control class with known rows” leave inputs, identifiers and expected outputs unspecified. Nonempty assertions help audits but do not define deterministic fixture construction. | **O:276–281,297–302,346–393,402–421** |
| **Some claimed mutations remain nondiscriminating.** O-RX-1’s three crossings occur on different dates, so day-rounded hashes can still produce three contacts; no expected identity bytes or refinement/extension comparison detects that mutation. O-RP-3 still supplies no trajectory capable of rejecting endpoint-only peak selection. The tārā key-regression test still omits the canonical and mismatched keys. | **O:59–64,129–134,395–400** |

The labels therefore overstate both literal completeness and generator completeness. This is the original R2-S06 requirement remaining open, not a new request to expand the oracle inventory.

**New blocking regressions introduced by v1.2/v2.1 — [S][J]**

| ID / severity | Claim | Evidence | Requested change |
|---|---|---|---|
| **R3-S01 · BLOCKING** | **O-PP-2’s new positive and negative controls are unsound.** Its positive case licenses marriage through Ketu’s dispositor chain although node-dispositor delivery is testimony-only. Its negative case denies any Rahu dispositor connection to Venus/7L, despite Rahu being in Taurus, ruled by Venus. Its 2016–2019 Rahu interval also conflicts with Lahiri’s Moon AD on 2018-11-28 in [L]. | **O:207–210; DS:56–59,177–187; [L].** | Replace the controls with fully pinned periods and complete relationships under the selected ayanamsha. Use an authorized scored path for the positive case; prove the negative case lacks that path. Specify the transition boundary. |
| **R3-S02 · BLOCKING** | **The rewritten P4 fixture introduces incompatible admission rules.** O-RP-2 now requires both agents on one target, while O-RP-3 requires admission through Jupiter’s house contact plus Saturn’s different lord contact. O-RP-2 also retains a frame-wide rejection after purporting to restrict its target subset. | **O:123–133; DS:214–235.** | Freeze one precise shared-target/house-and-lord rule and make both fixtures obey it. Label any restricted negative-test subset accurately. Replace the general “Jupiter-self” exclusion with the actual transit-to-natal geometry. |
| **R3-S03 · BLOCKING** | **New synthetic AV operands are falsely attributed to the pinned chart extract.** AV0’s Mars BAV has no zero, and its SAV vector has no 24. Yet O-BP-1 cites AV0 for Mars=0 and O-BP-5 cites AV0 for measured SAV=24. | **O:311–316,339–344; AV0:176–245,536–605.** | Identify these as synthetic fixture records with explicit keys and polarity declaration, or select actual extract rows and recompute expectations. Preserve the real extract unchanged. |
| **R3-P01 · BLOCKING** | **The new sign-convention assertion is false and unenforced.** P says adverse rows have `valence=loss` and that violations stop scoring. The extract includes **70 parental_event rows with `mixed`** and **10 surgery rows with `neutral`**. SC merely prints whether merged scores are nonnegative and continues even when false. | **P:74–79; SC:101–105; X:6291–6299,9855–9863.** | Define the adapter from actual class/score semantics, correct the input-description claim, and enforce the declared rejection rule on raw inputs before merging. Do not use a diagnostic print as an assertion. |

**Ranked amendments required before D-SPECS**

1. **Complete the typed identity contract:** generation/contact-safe relationship keys, version-qualified FKs, source-fact lineage, tagged support/completeness states, unknown-admission behavior, stable occurrence indexing and publication-safe partition reconciliation. **R2-S01/S02.**
2. **Complete numerical scoring and class/path definitions:** factor functions and scales, evidence aggregation/shared-root handling, exhaustive target/agent sets, and one consistent P4 rule. **R2-S03; R3-S02.**
3. **Pin the daśā read contract and repair its fixtures:** retain O-PP-1’s correct Lahiri MD/AD values, add the supplied PD expectations, specify build/row selection, and replace O-PP-2’s invalid controls. Correct the reconciliation’s ayanamsha conclusion. **C.2; R3-S01; R2-S06.**
4. **Finish P5 semantics:** define supported nonzero BAV qualification or keep it explicitly unresolved; provide the independent operand-availability matrix; remove the surviving BAV/SAV contradiction; correct synthetic-versus-L1 fixture provenance. **R2-S04; R3-S03.**
5. **Finish the existing fixture contract:** complete the remaining literal inputs or deterministic generators, name a native adverse class for O-RP-5a, test testimony’s admission boundary, define Δ/tolerances and interval endpoints, and demonstrate that each designated mutation changes an asserted result. **R2-S05/S06; C.4.**

**Ranked amendments required before D-PROTO**

1. **Preserve the already-identified observation meanings and ranges:** resolve the two multi-year uncertainties, represent vertigo’s exacerbation separately from onset, explicitly qualify proxy mappings, and replace the table-is-infallible rule with source reconciliation. Recompute cohorts if those dispositions change them. **R2-M01.**
2. **Make validity and inputs operationally explicit:** pin the machine-readable registry and complete class/polarity/eligibility/tier contract; specify the future coverage manifest; enforce generation-wide rank voids and machine-readable failure. Either implement annotation rejection or explicitly restrict this historical scorer to annotation-free inputs and withdraw broader guard claims. **R2-M03/M06.**
3. **Make prose and ranking implementation identical:** merge representatives, tie equivalence, observed-year masking, score adaptation and actual input rejection must be defined and enforced together. **R2-M04; R3-P01.**
4. **Freeze one matched-control experiment:** settle calendar versus rolling units, month/year lengths, sampling domain, overlap semantics and weighting; regenerate the materialised controls under that exact declaration. **R2-M05.**
5. **Regenerate the baseline and its descriptive counts after those amendments:** correct the dedup narrative, distinguish preliminary percentiles from valid ranks, and retain historical T-honesty as unverifiable unless genuine coverage evidence becomes available. **R2-M07 and the affected rerun.**

**Disclosure and verification limits**

All five packet-listed hashes match their supplied values and remained unchanged at the closing check. Supporting extract, scorer, control and AV hashes also match their recorded values.

No file was created, edited, moved or deleted; no git write command or database connection was used. Neither forbidden tracker directory was accessed. An initial shell here-document was rejected because it required a temporary file; subsequent Python used in-memory `-B -c` execution.

I did not execute the scorer’s write-producing top level. Independent arithmetic and selected read-only scorer statements were executed in memory.

Not independently verified here: production extraction fidelity; the reported PyJHora recomputations; Swiss solver/backend results; served-corpus provenance; full daśā row IDs and boundaries; actual computation coverage; runtime execution of all oracles or mutation receipts; historical authoring order; or whether another session scored candidates. The steward’s supplied production table is the sole **[L]** evidence used.

**Review only; authorizes nothing.**