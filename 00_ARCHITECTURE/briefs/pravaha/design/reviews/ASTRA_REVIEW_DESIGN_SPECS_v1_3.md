---
artifact: ASTRA_REVIEW_DESIGN_SPECS
version: "1.3"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra — independent adversarial review (round 4, contract closure)"
date: "2026-09-30"
verdict_specs: REWORK
reviewed_packet: "design/reviews/CLOSURE_PACKET_DESIGN_SPECS_v1_3.md"
reviewed_packet_sha256: "b9a1701ed7baad8b7852f9df8113eb049d5f633632a29c6dc21c6f8751557517"
reviewed_file_sha256:
  design/GOCHARA_DESIGN_SPECS_v1_3.md: "727d174a01060226e05e78cc6b3c264e241069bae652f5c2727c1a4d8988af2d"
  design/GOCHARA_TEST_ORACLES_v1_3.json: "5a7258ad14f1f167530a12e122c392e4b3a6ce2595cd0c5973ff64f6d11fb981"
  design/RECONCILIATION_DESIGN_SPECS_v1_2.md: "398166666e67ba0e0cd564d20a132eb6e04c7c807a4ad544b8e88633475a2a99"
supporting_file_sha256:
  design/reviews/ASTRA_REVIEW_DESIGN_SPECS_v1_2.md: "c980fc8a7cf8c7cd17ed04ee811d25c6e3ccf5c2c837b132f5bbf79da05bba82"
  design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json: "312de09e791e34e58377b7c0956e39f6691490bd2cfd0a27b415a7055c88fe83"
  design/L1_ASHTAKAVARGA_EXTRACT_v1_1.json: "e9e5d4d3f48c0588036d0e837eb3d5077e0e2f85e7da22c1ac866f131a5c3224"
hash_method: "Recomputed with shasum -a 256; packet, reviewed files and supporting files checked again at close."
authority: "Review only; authorizes nothing."
---

**Specs v1.3 + oracles v1.3: REWORK under the native’s split freeze standard.**

Remaining contract gaps affect enumeration, evidence aggregation, permission and identity. Some `literal` labels also remain inaccurate. Completion of honestly deferred fixtures stays at A5.5. Protocol v2.2 is outside this verdict.

Citation keys identify exact files; `DS:180–184` means repository line numbers.

| Key | File |
|---|---|
| DS | [design/GOCHARA_DESIGN_SPECS_v1_3.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_3.md) |
| O | [design/GOCHARA_TEST_ORACLES_v1_3.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_3.json) |
| RC | [design/RECONCILIATION_DESIGN_SPECS_v1_2.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/RECONCILIATION_DESIGN_SPECS_v1_2.md) |
| R3 | [design/reviews/ASTRA_REVIEW_DESIGN_SPECS_v1_2.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/reviews/ASTRA_REVIEW_DESIGN_SPECS_v1_2.md) |
| AV0 | [design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/L1_ASHTAKAVARGA_EXTRACT_v1_0.json) |

**Closure table**

| Item | Status | Evidence against the round-3 requested change |
|---|---|---|
| **D-SPECS amendment 1 — identity/lineage; R2-S01/S02** | **PARTLY CLOSED** | Generation/contact-safe record keys, source-fact lineage, tagged support states and unknown-admission behavior are added. Composite registry PKs and path FKs are explicit. Predicate/factor lists still contain bare IDs without explicit version binding. Full-domain ordinals address partition-local renumbering, but null-centre association and publication-safe reconciliation remain unspecified. **DS:86–105,150–171,524–548; O:60–65.** |
| **D-SPECS amendment 2 — numerical scoring and class/path sets** | **PARTLY CLOSED** | Function/range/units fields are added, but actual factor functions and compatible numerical scales are still absent. Contact-based deduplication has no deterministic reduction for unequal role contributions or distinct natal records with NULL contact IDs. “Fixed 27 classes” is not an enumeration; the nine grouped target-table rows contain no karaka sets. **DS:109–110,162–196,206–211,238–248.** |
| **D-SPECS amendment 3 — daśā read contract** | **PARTLY CLOSED** | Full chart/ayanamsha/system/build/tier pin, half-open boundaries, parent linkage, conflicting-duplicate rejection and the correct PD lords are present. Identical qualified duplicates still lack deterministic handling. General event-instant/timezone normalization and complete selected-row identity handling remain unspecified. The repaired negative control remains unsound at its asserted scope. **DS:415–448,468–477; O:200–212.** |
| **D-SPECS amendment 4 — P5 semantics** | **PARTLY CLOSED** | P5a’s nonzero comparator is honestly unresolved, and §2.2 independently describes missing BAV and SAV. But §8.2 still says missing BAV disables **P5a/P5b**, directly contradicting the new matrix. **DS:272–292,643–644; O:319–324.** |
| **R3-S01 — O-PP-2 controls** | **PARTLY CLOSED** | Mars’s scored seventh-house occupancy, Rahu’s testimony-only dispositor chain and the AD boundary are repaired. Absence of an AD-level route does not prove absence of class permission across nested MD/AD/PD. The same packet supplies a Venus PD inside the supposedly unlicensed Rahu AD. **DS:201–211,441–448,468–477; O:201–211.** |
| **R3-S02 — one P4 rule** | **PARTLY CLOSED** | Both fixtures now use the same Boolean rule; their restricted arithmetic is correct. The father fixture still misidentifies its restricted H as the truth-table set, and retains “any P4 row for this frame-date” rejection. The actual H column includes additional houses that change the result. **DS:238–263; O:123–135.** |
| **R3-S03 — synthetic AV provenance** | **CLOSED** | O-BP-1 explicitly identifies synthetic `fixture=true` operands and separates real contrast data. O-BP-5 uses the actual Aquarius SARVA row, value 23 and matching fact ID. Extract hashes remain unchanged. **O:28,312–317,340–345; AV0:224–239,595–599.** |
| **Q8 / amendment 5 — limited fixture-policy check** | **PARTLY CLOSED** | Inventory and 24/33 label counts reproduce. The deferred-fixture policy is explicit. Several retained `literal` entries still require unspecified inputs, including O-RP-3’s peak trajectory and O-RP-5b’s scored baseline. Their completion may be deferred, but their labels must become truthful. **DS:728–742; O:130–135,151–156,200–212,319–324.** |

**Answers to the packet’s questions**

**Q1 — The corrected AD facts are sound internally; the negative permission claim is not proven.**

From the printed natal operands, Mars 198.52° is in Libra, the seventh sign from Aries. Rahu 49.03° is in Taurus, the second. The Venus-dispositor chain is now acknowledged and correctly restricted to testimony. The quoted Mars and Rahu AD intervals meet at **2020-02-14T11:47:23Z**; under the stated half-open convention, that instant belongs to Rahu. **DS:468–477; O:208–211.**

However, O-PP-2 evaluates `permission(class=marriage,t)` and denies it throughout Mercury/Rahu. The permission contract consumes nested MD/AD/PD relationships, and P1 expressly includes PD lords. O-PP-1 supplies **Venus PD, 2021-10-04 → 2022-03-08**, inside that Rahu AD; Venus is explicitly identified elsewhere as **7L**. Therefore “Rahu has no scored AD relationship” does not establish “no scored period relationship exists.” The fixture also supplies neither chosen interior instants nor the transit prerequisites needed for full P1 admission. **DS:201–211,441–448; O:84,201,208–210.**

The control must distinguish **AD-specific relationship eligibility** from **complete class permission**. For the latter, define the MD/AD/PD composition and show that every relevant scored route fails at the selected negative instant. The current blanket denial cannot serve as that proof.

These are checks against the supplied rows and contract; I did not independently verify the rows against the live Lahiri build.

**Q2 — The restricted geometry and single Boolean rule are correct; the target-set contradiction survives.**

Independent arithmetic gives:

| Case | Calculation | Result |
|---|---|---|
| Father, Jupiter conjunction | 249.79° − 220.31° | **29.48°** |
| Father, Jupiter full aspect roots | 220.31° + 120°/180°/240°, modulo 360° | **340.31° Pisces; 40.31° Taurus; 100.31° Cancer** |
| Father, restricted H = Sagittarius | Jupiter has no listed contact; Saturn 253.43° occupies Sagittarius | **FALSE ∧ TRUE = FALSE** |
| Childbirth, Jupiter | 306.87° + 180°, modulo 360° | **126.87° Leo** |
| Childbirth, Saturn–Sun | 291.96° − 288.01° | **3.95° ≤ 5°**, hence admitted |

Thus both fixtures obey the one rule **for their expressly supplied H sets**. **O:124–134.**

But DS:242’s signature-house column includes the ninth **and 2/7/8 from it**: Sagittarius, Capricorn, Gemini and Cancer. Jupiter’s ninth aspect reaches Cancer while Saturn occupies Sagittarius. The same union-within-agent rule therefore admits P4 over that printed full set.

DS:262 incorrectly describes those entries as residing in the testimony set; the actual testimony column lists only 2/7 from the ninth. O:126 also retains an unrestricted “any P4 row for this frame-date” failure statement. Reconcile the table and restrict the negative assertion to the intended subset.

**Q3 — Yes, the provenance distinction is now clear.**

I independently parsed AV0:

- **96 rows = 84 BAV + 12 SARVA**.
- No BAV zero.
- Mars minimum **1**, at Sagittarius and Aquarius.
- SARVA vector **[29,29,27,32,30,26,34,32,25,27,23,23]**, sum **337**.
- Aquarius SARVA **23**, fact ID **`36b81039eeb707a7`**.

O-BP-1’s synthetic values are explicitly separated from those real rows. O-BP-5’s measured **23 → adverse** versus configuration **28 → medium** is discriminating. The provenance blocker is closed. **O:28,312–317,340–345; AV0:224–239,536–605.**

This does not upgrade `single_pass` or independently establish production extraction fidelity.

**Q4 — Some R2-S01/S02 residuals remain.**

The record-key, lineage and support-state repairs close their respective subparts. Fixed-domain ordinals also address the original backward-extension renumbering problem **provided the full-domain crossing index is available**. Identity serialization is now printed. **DS:86–105,539–548.**

Remaining contract decisions are:

1. **Predicate/factor reference versions.** Their PKs are composite, but `prerequisites: [predicate_id]` and `soft_factors: [factor_id]` do not state whether they inherit the owning path’s version or carry independently selected versions. The explicit composite-FK sentence concerns `(path_id,rule_version)`. **DS:100,150–167.**
2. **Null-centre and seam association.** Ordering remains by solved `t_exact`; the contract does not say how a truncated, not-yet-associated episode receives its stable ordinal, or when publication must wait for that association. **DS:530–542.**
3. **Published enrichment versus correction.** Revealing a centre updates the row in place, while correcting a physical reading requires a new ID. The boundary and identity-version mechanism need to be explicit so published references remain reproducible. **DS:535–548.**

O-RX-1 now provides identity strings and a forward-extension case. Its executable completion may remain at A5.5; these underlying identity rules must close before freeze.

**Q5 — No: the shared-root reduction is not deterministic as written.**

The new rule says to sum records after deduplicating by `contact_id`, making the “second role” annotation. It never determines which role supplies the contribution when values differ. **DS:180–184.**

A reviewer-constructed example permitted by the schema illustrates the gap: two same-contact records have evidence pairs **(0.2, 0)** and **(0.8, 0.5)**. Keeping either record counts the contact once, but gives different results. No equal-contribution invariant, precedence rule or channel-preserving reduction selects the result.

Moreover, natal-fact records legitimately have **`contact_id=NULL`**. Contact-only grouping can collapse unrelated natal evidence unless a separate natal-root rule or explicit exclusion is defined. **DS:89,94,109–110,180–184.**

The numerical and set requirements also remain incomplete:

- `function`, `range` and `units` are schema slots; the P1 inventory still gives directional prose and names strength/maitrī without numerical definitions. **DS:162–167,206–211.**
- The exhaustive-set claim supplies neither 27 explicit class mappings nor karaka sets. Its new outside-set exclusion also conflicts with required occupant targets. **DS:192–196,238–248; O:81–85.**

**Q6 — The original ayanamsha mistake is addressed; the requested read contract is not fully closed.**

The complete build pin, Lahiri/Vimshottari selection, verified-tier requirement, parent linkage and half-open intervals directly address the original unpinned-read failure. The PD expectations **Mercury, Venus, Venus** are now explicit, and the reconciliation withdraws the incorrect ayanamsha conclusion. **DS:417–442; O:200–205; RC:67–79.**

The round-3 request also expressly required deterministic handling of **identical** qualified duplicates and event instant/timezone treatment. The new duplicate rule handles conflicting duplicates only. Date-only examples do not define how future date inputs become instants, and several reference row IDs remain abbreviated or absent. **R3:125–130; DS:424–442; O:201.**

Freeze a deterministic identical-duplicate policy, including parent-reference handling; require timezone-qualified input or an explicit date-conversion rule; and specify retention of the selected MD/AD/PD row identities. Full literal test materialization can remain at A5.5.

**Q7 — The unresolved comparator is honest; the BAV/SAV contradiction is still present.**

P5a now explicitly limits scored numeric output to known-zero detection and leaves nonzero comparison unresolved. That closes the comparator subpart. **DS:281–289.**

The contradiction is exact:

- **DS:274:** missing BAV makes **P5a alone** unqualified.
- **DS:643–644:** missing BAV makes **P5a/P5b** unqualified.

O-BP-2 case C tests **missing SAV with BAV present**. It cannot settle the opposite case—missing BAV with SAV present—or override the contradictory invariant. **O:320–323.**

Align §8.2 with the independent operand matrix. No invented nonzero threshold is required.

**Q8 — The counts are correct; not every remaining literal label is truthful.**

Independent parsing confirms **57 unique IDs**, exact equality with the spec index, and **24 literal / 33 executable_at_A5.5**. Every oracle retains assertion and mutation text.

The four highlighted repairs make real progress: O-VI-2 assigns March 1 to the clean interval; O-SM-1’s five printed sample values recompute to **0.8, 0.5, 0.4, 0.5, 0.8**; O-RX-1 supplies identity strings and extension expectations; O-RP-5a names `illness_acute`. **O:60–65,144–149,228–233,284–289.**

These retained literal claims still overstate their inputs:

| Oracle | Remaining literalness/discrimination problem |
|---|---|
| **O-RP-3** | A single instant’s positions prove admission, but provide no trajectories or overlap function for the asserted peak or endpoint-only mutation. **O:130–135.** |
| **O-RP-5b** | Saturn’s position is supplied; the scored window, contributing records and concrete baseline needed for bit-identical score comparison are not. **O:151–156.** |
| **O-PP-1** | The expected lords are explicit, but complete period-row identities, parent inputs and exact event instants are not a literal read-contract fixture. **O:200–205.** |
| **O-PP-2** | Interior test instants and nested period/transit inputs are missing; its broad negative assertion also requires the contract repair in Q1. **O:207–212.** |
| **O-BP-2** | Availability cases are named, but operand values and baseline results needed to assert that P5a/P5b results “stand” are not supplied. **O:319–324.** |
| **O-SM-1** | The numerical samples are now sound, but “beyond tolerance” still references a nonnumeric tolerance field: “curve comparison per pinned samples.” Pin the comparison tolerance or defer the executable comparison honestly. **O:285–289.** |

These findings **do not require completing those fixtures before freeze**. Relabel incomplete fixtures—or separate their complete arithmetic subcases—while retaining their assertions and mutation obligations. A5.5 must supply the literal inputs and demonstrate the failures. Mere presence of a mutation string is not a demonstrated discriminating test.

**New blocking regressions introduced by v1.3**

| ID / severity | Claim | Evidence | Requested change |
|---|---|---|---|
| **R4-S01 · BLOCKING** | The new contact-only evidence deduplication leaves unequal role contributions order-dependent and can collapse distinct natal evidence under NULL. | **DS:89,109–110,180–184; Q5 counterexample.** | Define an order-independent per-root reduction, explicit handling of both evidence channels, and a natal-root identity or explicit natal-record exclusion from this aggregation. |
| **R4-S02 · BLOCKING** | The new exhaustive-target exclusion can suppress occupant targets that the existing contract requires. | **DS:192–196** allows signature houses, lords and unspecified karakas only; **O:81–85** requires natal Saturn as a seventh-house occupant target. **DS:786–789** also uses that occupant’s return. | Supply exact per-class/per-path selectors covering every admitted target role, including occupants where required. Remove the contradictory exclusion until the complete inventory defines it correctly. |

The other findings above are unclosed round-3 requests, not additional protocol findings.

**Ranked amendments required before D-SPECS**

1. **Finish scoring and enumeration:** actual factor functions/scales, deterministic shared-root aggregation including natal records, and exhaustive class/path selectors. Reconcile the father target table with the restricted P4 assertion. **Amendment 2; R3-S02; R4-S01/S02.**
2. **Finish daśā selection and controls:** deterministic identical-duplicate handling, instant/timezone and selected-row identity rules, and an O-PP-2 assertion whose scope matches the complete period-permission contract. **Amendment 3; R3-S01.**
3. **Finish identity reconciliation:** explicit predicate/factor version binding, null-centre/seam association, and publication-safe enrichment/correction behavior. **Amendment 1.**
4. **Remove the surviving P5 contradiction:** make §8.2 agree with the independent BAV/SAV matrix and preserve the explicit unresolved nonzero comparator. **Amendment 4.**
5. **Correct remaining literal labels and comparison declarations:** preserve assertions and discriminating mutation obligations; defer executable fixture completion to A5.5 as ruled. **Q8 under the split standard.**

**Disclosure**

The supplied spec and oracle hashes match. All hashes reported above were recomputed with `shasum -a 256` and remained unchanged at the closing check.

I performed local source inspection, JSON inventory checks, extract-value checks and independent arithmetic using `/opt/homebrew/bin/python3 -B -c` in memory. The shared-root examples are reviewer-constructed counterexamples, not extracted production records.

No file was created, edited, moved or deleted. No git command, database connection or network lookup was used. Neither forbidden tracker directory was accessed. No sub-agents were used.

I did not independently verify production daśā rows, extraction fidelity, reported PyJHora recomputations, solver execution, executable oracle results or mutation receipts. Protocol v2.2, D-PROTO closure, scoring, deployment and native acceptance were not reviewed.

**Review only; authorizes nothing.**