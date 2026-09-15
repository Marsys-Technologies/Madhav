---
artifact: MADHAV_PRODUCT_DEFINITION_v1_1_REVIEW
canonical_id: MADHAV_PRODUCT_DEFINITION_v1_1_REVIEW
version: "1.0"
status: CLOSED
authorization: independent read-only audit of MADHAV_CONSUMER_PRODUCT_VISION_AND_DEFINITION v1.1 (PROPOSED); complete as issued; authorizes nothing and changes no governed rule
produced_on: 2026-09-12
produced_by: Claude (Claude Code, Fable 5.1) at the native's request, for return to GPT-5.6 "Astra" (Codex)
subject: 00_ARCHITECTURE/briefs/nirmana/MADHAV_CONSUMER_PRODUCT_VISION_AND_DEFINITION_v1_0.md (frontmatter v1.1, 2026-09-12), as it exists in the Codex worktree
repo_baseline: campaign/nirmana-autonomous @ badc3f9bc; the vision's own source_baseline 0955849d is the production-deployed SHA, not protected main
companion: MADHAV_PRODUCT_DEFINITION_v2_0_PROPOSAL.md — the elevated alternative this review led to
method_note: ten independent review lenses over eleven grounding briefs; 99 raw findings; clustered to 69; each cluster adversarially tested by three verifiers (textual accuracy, governance/codebase grounding, materiality); a finding survives only if at least two of three verifiers fail to refute it. Four competing vision drafts and three judges informed the alternative. Details in §1.
changelog:
  - "1.0 (2026-09-12): first issue."
---

# Review of the Madhav consumer product vision and definition, v1.1

## 0. What this is

The native asked for a thorough, unbiased audit of the product definition authored with Astra, with critique and elevation wherever warranted, and for an alternative version to take back. This document is the audit. It states what v1.1 gets right and must keep, what it gets wrong or leaves out, which of those findings survived adversarial verification, and where each surviving finding is answered in the alternative definition (`MADHAV_PRODUCT_DEFINITION_v2_0_PROPOSAL.md`). It changes nothing in the repository, the campaign or governance.

The short verdict: **v1.1 is a strong statement of values and a weak definition.** Its design order (promise → experiences → obligations → components), its earned-insight standard, its authenticity chain, its separate proof obligations and its rejections table are correct and should survive any rewrite. But it demotes the one mission leg that can be checked (calibrated, frozen prediction), states boundaries weaker than the governance already in force, names no unit of value, no wedge, no baseline step and no measurable standard, describes the existing system inaccurately in several places (the three request paths, the maturity states, the Paripraśna successor set), over-designs for a hypothetical public while under-serving the native's actual next year, and hides the decisions the native must make. Every one of those statements is tied below to a specific finding, its verification votes and its answer in v2.0.

## 1. How the audit was done

**Grounding first.** Eleven readers produced briefs, with file:line citations, over: PROJECT_ARCHITECTURE_v2_2 (§A/§B/§H/§J); MACRO_PLAN_v2_0 (mission, Learning Layer, M1–M10, Ethical Framework §3.5, §3.7, §3.10); PARIPRASHNA_TARGET_ARCHITECTURE_v0_1 (v0.11, now SUPERSEDED) and, separately confirmed, its CURRENT successor set (PARIPRASHNA_ARCHITECTURE_v1_0, the Decision Register with D-01…D-19 and NCD-1…11, the As-Built Baseline v1.3, the Acharya Reading Contract); RETRIEVAL_STRATEGY_v1_0 (v1.3); the three L3 studies and the stocktake the vision cites; the live serving code (registry, MCP tools, Paripraśna modules, planner, receipts, safety, consent, no-leakage, Samīkṣā); the live layer and Nirmāṇa campaign state; the L0 corpus and L1–L5 technique coverage; and the learning loop, ledgers and Life Event Log schema (schema and mechanism only — no private event content was read into any brief).

**Ten lenses.** Consumer/experience design; senior Jyotish acharya; epistemics and forecasting science; engineering alignment with the real system; product strategy; writing and structure; ethics, safety, consent and culture; an adversary of the "beyond-Acharya" claim; a completeness critic; an internal-and-governance contradiction hunter. Each was capped at ten ranked findings with a concrete proposed change, and asked for up to five strengths to preserve. Result: 99 findings (25 critical, 68 major, 6 minor), 50 strengths.

**Clustering.** Two automated clustering passes stalled on output size; the clustering was then done by hand from the finding titles (69 clusters, every one of the 99 findings assigned exactly once, none dropped). The mapping is recorded in the audit's working files and reproduced in §3 as `merged_from`.

**Adversarial verification.** Each cluster was handed to three independent verifiers instructed to *refute* it, each under a different lens — *textual* (does v1.1 actually say or omit this?), *grounding* (is the finding consistent with governance and the codebase, and would its proposed change itself violate a principle?), *materiality* (would adopting it materially improve a whole-product reference?). Verifiers default to "refuted" when they cannot confirm. A finding survives only when at least two of three fail to refute it. Verification was interrupted twice by account session limits. The first seventeen clusters received all three lenses; the remaining clusters were verified with two lenses (textual and grounding) in an economical mode that constrained reading to the document, the critic file and at most two grounding briefs. Votes are reported per finding in §3 and Appendix A. A consolidated revision brief compiled from the verified findings, the strengths and the candidate grafts also exists (scratchpad working file, not placed in the repository); its top changes agree with §7.

**Competing drafts and judges.** Four independent authors wrote competing definitions from different angles (the acharya's working memory; inquiry-first; accountable research instrument; radical clarity), and three judges scored them against v1.1 from the native's, an acharya's and an engineer's seat. Their strongest passages were grafted into v2.0 and are credited in §6.

**What this audit is not.** It is not a deployment audit, a readiness certification or a claim about predictive accuracy. Where it reports what exists in code, that is a read of the repository at `badc3f9bc` on 2026-09-12; code defaults are not production configuration.

## 2. The verdict in one page

Sixty-nine clusters were tested. **58 were verified** (at least two of three independent verifiers could not refute them), **9 are contested** (the verifiers split, typically because v1.1 already carries part of the point at a vision level of abstraction and the critic overstated the gap), and **2 were refuted** (v1.1 already says what the critic said it lacked). The full table is §3; the split and refuted cases are §4. Ten findings carry the verdict:

1. **The mission was silently re-weighted** (F-01, verified 3/3). MACRO_PLAN's third numbered obligation — time-indexed, probabilistic, *calibrated* prediction testable against life — became "a major capability within" understanding, and the Ethical Framework's "no output without a band" became "calibration where justified". Either change may be right; neither may be made by omission. v2.0 restores the obligation and states the band rule as the ratified typed-confidence contract.
2. **The boundaries are weaker than the governance already in force** (F-02, F-04, F-10, verified). §10 says "do not guarantee … death"; MACRO_PLAN §3.5.C forbids any date-of-death output, any individualized mortality window and any suicide-adjacent output, and gates health-crisis and mental-health readings behind a seal and sign-off. §3.5.F's exclusion of minors is absent while a family chart already exists in the system. The system computes three āyurdāya methods and v1.1 has no stance on them. v2.0 carries the hard stops verbatim, each with its detector status.
3. **The audience falls under no admitted disclosure class** (F-03, verified). "No intelligence tiers" is half of the settled two-axis rule; the other half — disclosure classes as consent and access — is missing, and a personalised reading for a consenting adult who is not the native fits no existing class. v2.0 states both axes and asks the native to create the missing class as a declared scope event.
4. **The tradition's own reading architecture is absent** (F-19, contested→verified on grounding; F-20, F-23). "Whole-chart discipline" names no lagna, kāraka, varga hierarchy, daśā applicability, gochara confirmation or aṣṭakavarga gate, and the register is psychologized where the tradition is phala-oriented. v2.0 adds the śāstric spine the compiled floor must encode.
5. **"Beyond-Acharya" is unfalsifiable framing over a stricter, already-ratified test** (F-21, F-51, verified). PROJECT_ARCHITECTURE's three-conclusion test is the standard; the phrase adds nothing testable. v2.0 retires it from product language and names the axes on which the instrument honestly exceeds a human as mechanisms with tests.
6. **The document describes the existing system inaccurately in places that matter for alignment** (F-34, F-38, F-49, verified): the two managed doors do not share investigation semantics today; the retrieval strategy is never cited and its hard targets are omitted; the superseded Paripraśna architecture is cited as authority; six maturity states are collapsed to three; the evidence basis points into a Codex worktree.
7. **It has no wedge, no baseline step and no measurable standard** (F-42, F-43, F-32, verified). Six experiences, twenty-one needs, seven "core targets" and thirteen evaluation rows are co-equal; nothing says what must be excellent first, and no step measures the current product before elevating it. v2.0 names the wedge, three north-star instruments with existing detectors, and a baseline-first sequence.
8. **The decisions the native must make are hidden** (F-44, F-66, verified). The frontmatter disclaims superseding governance while the body amends the mission, the M10 gate, the natal thesis and the subject scope. v2.0 lists eighteen decisions with recommendations and makes its own supersession conditional on ratification.
9. **Absent or flag-OFF capabilities are presented as substrate** (F-36, F-31, F-55, verified). The living atlas, question compass, stable core, observation briefs, method-native families and the observatory are named by their virtues before any operator, input or test exists; the receipt, typed confidence and interpretation-set machinery that would make claims checkable is default OFF in code. v2.0 gives every need a disposition (IN / IN-GATED / DEFER / OUT), names the missing operator, and says what kind of thing each deferred capability is.
10. **Twelve-month reality is under-served while a hypothetical public is over-designed for** (F-03, F-58, F-59, verified). The personas the system already serves — the native as operator, a consenting relative, a practitioner on raw MCP, an external AI via `prashna_ask`, a reviewer — are unnamed, and the operator instrument the native runs daily has no row while the portal row's failure column condemns it.

What v1.1 gets right is not small, and §5 lists it. The design order, the earned-insight standard, the authenticity chain, the separate proofs, the person-is-not-the-chart rule and the rejections table are the skeleton any successor must keep — v2.0 keeps all of them.

## 3. All findings, with verification status

Votes are textual / grounding / materiality: **S** = the verifier could not refute (stands), **R** = refuted, **–** = lens not run (clusters verified after the quota interruption ran two lenses, textual and grounding, in economical mode). Severity is the critics' assessment before verification. The full per-finding ledger — claim, evidence, each verifier's reasoning and the adopted proposal — is Appendix A.

| # | Status | Sev | Finding (v1.1 section) | Votes (t/g/m) | Answered in v2.0 |
|---|---|---|---|---|---|
| F-01 | VERIFIED | crit | Calibrated prediction demoted; 'band or nothing' inverted to 'band where justified'; emission-time rules omitted *(§1, §3, §7.6, §11.2, E3/E5)* | S/R/S | §1.1, §11.2, §10 B-8/B-9, §13 D-1/D-3 |
| F-02 | VERIFIED | crit | §3.5.C/§3.5.F hard stops omitted: date-of-death, mortality windows, suicide-adjacent, health/mental-health sign-off; āyurdāya/māraka/santāna stance absent; fertility & mental-health classes unassigned *(§10, P01/P06/P07, §8 L4 row)* | S/S/S | §10 B-1…B-4, §5 P06/P07/P24, §2.1 |
| F-03 | VERIFIED | crit | Audience falls under no admitted disclosure class; 'no audience tier' stated on one axis only (two-axis rule missing); 12-month user over-served by public-product design *(§2.1, §10, §14)* | S/S/S | §1.4, §2.1 rings, §13 D-2 |
| F-07 | VERIFIED | crit | No stance on fatalistic, casteist or misogynistic classical content; 'fidelity to sources' has no harm rule *(§6.1–§6.3, §10)* | S/S/S | §6.3, §10 B-12, §13 D-6 |
| F-11 | REFUTED | crit | No consumer-legible promise; unit of value never named; the definition sentence is three products *(§1, §14)* | R/S/R | headline, §0, §1.3 unit of value |
| F-19 | VERIFIED | crit | The tradition's judgment architecture (śāstric spine) is absent: lagna/kāraka primacy, varga hierarchy, daśā–gochara double confirmation, aṣṭakavarga gating, daśā-system applicability *(§3, §4, §7.1, §8 L1–L3 rows, E3, P10)* | S/S/– | §3.4 śāstric spine; E3 |
| F-21 | VERIFIED | crit | 'Beyond-Acharya' is unfalsifiable and never names what the master does vs what the machine exceeds; wrong operating benchmark; expert agreement ≠ validity *(§1, §3, §11.1, §11.2)* | S/S/– | §3.1–§3.3, §13 D-8 |
| F-25 | VERIFIED | crit | Null-result behaviour never stated; served classical doctrine is grandfathered *(§11, §6.4, §10, E3)* | S/S/– | §6.4, §13 D-7 |
| F-26 | VERIFIED | crit | 'Personal specificity' is mere input-sensitivity; blinded chart-discrimination and Barnum control absent; volume and category-heuristic valence make generic readings the default risk *(§3 row, §11.2 row)* | S/S/– | §11.3 blinded specificity row; §11.1 structural falsifiers |
| F-33 | VERIFIED | crit | §13.2 is not executable under live Nirmāṇa authority, holds and PARKED pillars; 'does not reopen' vs concrete new demands on frozen L0/L1/L2; step four reinstates an upstream-first programme the frozen layers already completed *(§13.2, §8 closing, §1.1/§13.3)* | S/S/– | §14; §13 D-16 |
| F-34 | VERIFIED | crit | §7.3 and the §8 MCP row misdescribe the three request paths and, under one reading, reverse D-05/OT-6 *(§7.3, §8 MCP row, §9 durable identity)* | S/S/– | §7.1 doors table |
| F-42 | VERIFIED | crit | No wedge and no product sequence; ten co-equal 'cores'; four simultaneous core targets create layer-wide demands against a frozen manifest and three lack their enabling operator *(§4 preamble, §12.1, §13.2, §8 closing)* | S/S/– | §1.1 wedge; §14 |
| F-43 | VERIFIED | crit | No north-star measure; acceptance criteria cannot be derived *(§11)* | S/S/– | §11.2 three instruments |
| F-44 | VERIFIED | crit | The decisions the native must actually make are hidden; only the easy ones are deferred *(§14, §15)* | S/S/– | §13 sixteen decisions |
| F-46 | VERIFIED | crit | 'The user' denotes both the consumer and the native/decision-owner, including in the authorization sentences *(§1, §11.3, §13.2, §14)* | S/S/– | 'the person' / 'the native' throughout |
| F-51 | VERIFIED | crit | The five mechanisms that could deliver 'not seen on first pass' are not named specifically enough to build or test *(§3 table, §8 L1/L2/L3/registry rows)* | S/S/– | §3.2 mechanism table |
| F-52 | VERIFIED | crit | The served discovery surface already asserts what §3 says does not qualify, and the vision does not name it as something to supersede *(§3 discovery row, §6.3–6.4, §8 living-atlas row)* | S/S/– | §13 D-12 (discovery surface relabelled as candidates) |
| F-58 | VERIFIED | crit | Only 'the consumer' is a defined persona; six personas the system already serves are assumed or absent *(§2.1, §8 subject/security rows)* | S/S/– | §2.1 rings table |
| F-59 | VERIFIED | crit | Operator instrument (build cockpit, Nirmāṇa tracker, review/sign-off/intake) has no §8 row; the portal row's failure column condemns the console the native runs daily *(§8 portal row; missing row)* | S/S/– | §8 operator instrument row |
| F-66 | VERIFIED | crit | Frontmatter disclaims superseding governance while the body amends the mission, the M10 gate, the natal thesis and the subject scope *(frontmatter, §1.1, §5.1, §11.2, §14)* | S/S/– | frontmatter supersedes_if_ratified; §13 |
| F-04 | VERIFIED | majo | Consent for related subjects, family charts and minors unaddressed (§3.5.F absent; a family chart exists) *(§5 P05/P14, §8 subject row, §10)* | S/S/S | §2.1, §10 B-7 |
| F-05 | VERIFIED | majo | Deletion vs protected historical integrity left to a future author; governance already resolves it *(§9 long-term, §8 L5/personal-history rows)* | S/S/S | §9 year three, §12 table, §13 D-5 |
| F-06 | VERIFIED | majo | The native as proving subject — self-experimentation, an intimate life record in a hosted repo, provider data flows — nowhere addressed *(§1.2, §2.1, §8 security row)* | S/S/S | §2.1 (ring 0 obligation), §10 B-15 |
| F-08 | VERIFIED | majo | Remedy/upāya line stops short of the settled attributive-register rule; commerce, unsolicited prescription and cost unaddressed; upāya ethics and muhūrta strictness not stated as doctrine *(E4, §10, §12.2, §8 L4 row, missing §8 row)* | S/S/S | E4, §8 remedies row, §10 B-11 |
| F-09 | VERIFIED | majo | 'Spiritually moving' aspiration and living portrait lack emotional-register obligations and a non-dependence rule *(§1, §2.3, E1, §9)* | S/S/S | §7.3 emotional-register sentence, §9 long-term |
| F-10 | VERIFIED | majo | The eight 'do nots' are behaviours without detectors; several cannot read false; §3.5.A/E/G obligations omitted *(§10)* | S/S/S | §10 detector column |
| F-12 | VERIFIED | majo | Day one / day thirty / year three never storyboarded; §9 is prohibitions *(§9)* | S/S/S | §9 storyboard |
| F-13 | VERIFIED | majo | §7.4 sample dialogue is a cautious system describing its method, not a great experience *(§7.4)* | S/S/S | §7.4 rewritten as ask-back + sealable claim |
| F-14 | VERIFIED | majo | E1–E6 blur; v1.1 additions bolted onto nearest experience; every capability listed three times; coined terms drift and multiply *(§4, §8 rows 386-388, §12.1)* | S/R/S | §4 three pairs; Appendix A glossary |
| F-15 | VERIFIED | majo | Accountable continuity depends on an undesigned user act; after-answer list misses the one real continuation (the window closing) *(§9 after the answer, E6, E3, §11.3)* | S/S/S | E6, §9 day thirty |
| F-16 | VERIFIED | majo | Hedging density hides the product (~31% negated sentences; non-claims repeated up to ten times) *(whole document)* | S/S/S | §0 'what it is not' box; §10 single boundaries section; hedges consolidated |
| F-18 | VERIFIED | majo | Structure: product should read before policy; a quarter of the document is decision record/changelog; replacement outline with a ~40% cut *(document order, §1.1, §1.2, §12–§15)* | S/S/– | document order: product before policy; decision record moved to §12–§13; appendices |
| F-20 | VERIFIED | majo | Hierarchy of testimony among texts and classical adjudication rules absent from 'productive disagreement' *(§6.2, §8 L0 row, §11.2)* | S/S/– | §6.2 hierarchy of testimony |
| F-22 | VERIFIED | majo | Inquiry families invented as product categories rather than the tradition's divisions; Praśna admitted without doctrine; method-native expansion is v3.X scope creep that contradicts B.11 as stated in §8 *(§5.1, P21, §8 inquiry-family row, §7)* | S/S/– | §5.1, P21, §13 D-9 |
| F-23 | VERIFIED | majo | Psychologized register displaces the tradition's phala orientation and its own importance instrument (bala) *(§1.2, E1, P01, §12)* | S/S/– | §3.4 phala-orientation paragraph |
| F-27 | VERIFIED | majo | Knowledge-time is a value, not a machine-checked admissibility predicate; nothing enforces emission-before-event *(§11.2 closing, E5, §8 personal-history row)* | S/S/– | §8 L5 row invariant (emission-before-event); §8 personal-history row |
| F-28 | VERIFIED | majo | Retrodiction and the event log require a denominator; the live corpus (memorable-event log, 25/21/0) shows why *(E5, §11.2, §10)* | S/S/– | E6 (unmatched activations and non-events counted; LEL bias named) |
| F-29 | VERIFIED | majo | Multiple-testing control and pre-registration are named, not mechanised, against thousands of hypotheses on one subject *(§6.4, §6.5, §11.2)* | S/S/– | §6.5 hypothesis registry clause |
| F-30 | VERIFIED | majo | n=1 and population extension: no sample-size reasoning and no case supply behind the observatory and laboratory horizons *(§6.5, §12.1)* | S/S/– | §6.6 |
| F-31 | VERIFIED | majo | 'Stable core under uncertainty' has no perturbation grid, sampling design, stability criterion or claim-matching unit; L1 has no birth-time-uncertainty input *(§2.2, §9, §12.1)* | S/S/– | E2(c); §5 P13 DEFER; Appendix C kinds |
| F-32 | VERIFIED | majo | §11.2 rows are aspirational (no unit, metric, baseline, n, judge, pass criterion); M10 composite gate contradicted without declaration *(§11, §11.2)* | S/S/– | §11.3 harness table; §13 D-4 |
| F-35 | VERIFIED | majo | 'Inspectable insight' names neither its grain nor the existing claim/receipt objects; alignment will build a parallel store; the scripted reference investigation is never the unit of acceptance *(§7.5, §8 synthesis row, E6, §11.3)* | S/S/– | §1.3 unit of value; receipt (NCD-3) |
| F-36 | VERIFIED | majo | Three new cross-cutting rows require interfaces that do not exist; the document does not say what kind of thing each is (registry change, service asset, stored asset) *(§8 rows 374/385/387, §9, P13/P19/P21, §5.1)* | S/S/– | Appendix C 'what kind of thing' |
| F-37 | CONTESTED | majo | 'Protected histories' and 'restore evidence' promised but the storage model does not provide them; 'two states of understanding' only as a diff of persisted artefacts *(§8 orchestration row, E6, §9)* | R/S/– | §8 orchestration row |
| F-38 | VERIFIED | majo | Registry row uses synonyms for existing mechanisms, misuses 'flattened', omits RETRIEVAL_STRATEGY's numeric targets and never cites it *(§8 registry row, §7.1, §7.6, §15)* | S/S/– | §8 registry row; §11.2 RS targets |
| F-39 | CONTESTED | majo | Planner row misreads the acharya floor as a failure mode and omits the planner's existing contract (floor + band; three-way outcome; one-question rule) *(§8 planner row, E2, §7)* | R/S/– | §8 planner row; E2(a) |
| F-40 | CONTESTED | majo | L5 / personal-history / observation rows and E5 do not state the NO-LEAKAGE and COLLECT-ONLY invariants that already bound them *(§8 L5 row, personal-history row, observation row, E5, §7, §6.4)* | R/S/– | §8 L5 row; §10 B-10; E6 |
| F-41 | VERIFIED | majo | Add a 'binding interfaces and invariants' appendix so per-component alignment is conformance-checking; §13.1 should reuse existing evidence vocabularies *(§8, §13.1, §13.2)* | S/S/– | §8 invariant column |
| F-45 | VERIFIED | majo | Operating realities (cost, latency, model identity, provider substitution, degraded mode, spend ceilings, restore posture) unconstrained, so 'align every component' has no envelope *(§7.6, §8 orchestration/security rows, §9)* | S/S/– | §7.5 spend caps; §8 orchestration/security rows (model identity, degraded mode) |
| F-47 | VERIFIED | majo | Four voices: imperatives to an unnamed agent, first-person essay, third-person description, AI-process provenance *(§1.2, §4, §6.5, §13.1, §15)* | S/S/– | single definitional voice |
| F-48 | VERIFIED | majo | File name, version label and status disagree with each other and with B.8 / hygiene §A *(frontmatter, §15)* | S/S/– | consistent v2.0 naming |
| F-49 | VERIFIED | majo | Evidence basis non-portable (Codex worktree paths), one dead anchor, superseded/incomplete sources (cites superseded Paripraśna v0.1; never cites RETRIEVAL_STRATEGY or ethics); Q01–Q18 mislabelled as 'temporal tests'; six maturity states collapsed to three *(§15, §5, §8, §7)* | S/S/– | Appendix D repo-relative; CURRENT successor set cited; maturity states restored |
| F-53 | CONTESTED | majo | Complexity theatre: no operational definition of discrimination, while served concordance/priority/outlook surfaces are averages that erase it *(§3 rows, §6.2, §8 L4 row)* | R/S/– | §3.4 discriminating-distinction definition |
| F-54 | CONTESTED | majo | 'Authentic depth' rests on rules whose validity is untested and mostly unmodelled; fidelity and validity must be separated *(§3, §6.1 item 2, §8 L0 row)* | R/S/– | §6.1 fidelity vs validity |
| F-55 | VERIFIED | majo | LLM fluency can masquerade as judgment: §3 does not constrain what synthesis may add, and claim-checking machinery is off by default *(§3 human clarity row, §7, §8 synthesis row, §12)* | S/S/– | §8 synthesis row; E1 'Today' |
| F-56 | CONTESTED | majo | Structural (non-event) claims cannot be validated by outcomes; the vision never says how they can be wrong *(§3, §11.1, §2.3)* | R/S/– | §11.1 'How a structural claim can be wrong' |
| F-60 | VERIFIED | majo | Served modalities have no IN/DEFERRED/EXCLUDED disposition; P01–P21 omit daily pañcāṅga, varṣaphala, sāḍe-sātī, kūṭa, vāstu, mundane, āyurdāya and never name the five ayanāṃśas *(§5, §5.1)* | S/S/– | §5 dispositions incl. P22–P24; Appendix B |
| F-61 | VERIFIED | majo | No input contract: birth-data quality tiers, time standards/historical clocks, location precision undefined; no such field exists for 'stable core' to compute over *(§9 first use, §8 subject row)* | S/S/– | §9 subject lifecycle; §8 subject row |
| F-62 | VERIFIED | majo | Subject and reading lifecycle missing: creation, build/rebuild rights, build duration, unbuilt-asset visibility; a rebuild makes E6's 'same evidence context' irrecoverable *(§9, E6, §8 orchestration/subject rows)* | S/S/– | §9 subject lifecycle; §8 orchestration row |
| F-63 | VERIFIED | majo | Language, script and register policy is one sentence; settled mechanisms not cited; corpus is English-translation-only *(§7.2, §9, §14)* | S/S/– | §9 language; §13 D-14 |
| F-64 | CONTESTED | majo | Reading the classical texts is undecided as a consumer feature; the rights obligation has no owner while the licensing record is PARTIAL and contradicts the registry *(§5, §6.1, §6.3, §8 corpus row)* | R/S/– | §5 P23; §13 D-15 |
| F-65 | VERIFIED | majo | Outputs have no contract: chart rendering, timelines, export, sharing, notes exist in code but the vision only says visuals are 'not prerequisites' *(§8 portal row, §9, §12.2)* | S/S/– | §8 rendering/outputs row |
| F-67 | CONTESTED | majo | 'No intelligence tiers' vs 'research facilities add operators': under D-15's own test an operator that changes what is produced is a tier *(§2.1, E6, §6.5, §7.5, §14)* | S/R/– | §1.4 research-operators sentence; §7.1 |
| F-68 | VERIFIED | majo | §7.1's 'useful partial answer' permits the softened claim B.12 forbids; missing-vs-computed-absence applied only to Kāla *(§5, §7.1, §8 L3 row)* | S/S/– | §7.2 pause rule |
| F-69 | CONTESTED | majo | The living atlas and 'a saved prior reading can guide retrieval' re-open the B.1 laundering path; J.5 chart-first ordering ambiguous *(§2.2, E1, §2.3, §9, §12, §8 atlas row)* | R/S/– | §1.3; §2.3 |
| F-17 | REFUTED | mino | Question compass names no ranking rule or constraint; should replace the existing LLM-suggestion anti-pattern with a consequence rule *(E2, §8 row 386, §12.1)* | R/S/R | E2(d) consequence rule |
| F-24 | VERIFIED | mino | Sanskrit layer names and Paripraśna/Praśna used without gloss; transliteration inconsistent *(§7.2, §8 preamble, lexicon)* | S/S/– | Appendix A; PPR-04 inline gloss |
| F-50 | VERIFIED | mino | Numbering, ID schemes, table forms and counts internally inconsistent *(§5, §8, §9, §12, §13.1)* | S/S/– | consistent numbering |
| F-57 | VERIFIED | mino | Proving journeys are all natal, shaped to the native's own questions, and contain no null case *(§11.3, §3)* | S/S/– | §11.4 null cases |


| id | finding | strongest refutation (lens, confidence) | reason |
|---|---|---|---|
| F-11 | No consumer-legible promise; unit of value never named; the definition sentence is three products | materiality (0.75) | Materiality lens verdict: the merged finding at "critical" with the C1 proposal is refuted. The claim's central assertion is false on the document's own text, the alignment risk it predicts is already addressed by the document's actual alignment instruments, and the proposed replacement would make t… |
| F-17 | Question compass names no ranking rule or constraint; should replace the existing LLM-suggestion anti-pattern  | textual (0.70) | Lens: textual accuracy only. The finding makes three textual claims about VISION_v1_1.md: (a) the compass "names no ranking rule or constraint"; (b) the document should say an empty compass is valid; (c) it should say the compass replaces the existing suggestion mechanism. Claims (a) and (b) misread… |

## 5. Strengths to preserve

Named independently by the ten critics; a rewrite must keep these in substance.

- **The design order.** Consumer promise → signature experiences → intelligence obligations → component contributions → contracts → separately authorized execution (v1.1 §1.1). Correct, and v2.0 keeps it.
- **Earned insight over volume.** "Show which additional connection changed the understanding; if a simpler competent reading is equally informative, extra complexity has not earned its place" (§1, §3). This is the right anti-verbosity acceptance principle and matches the retrieval plane's distillation boundary. v2.0 builds the discrimination test on it.
- **The six-link authenticity chain** (§6.1) and the **four separate proof obligations** with the refusal of any weighted composite score (§11.1–§11.2). These mirror the six maturity states of the cross-layer research and are the document's spine. v2.0 keeps both and gives the chain the tradition's own names.
- **"The person is not the chart"** (§2.3), recognition without stereotyping, valence-neutral chart-first reveal, circumstances never laundered into evidence, disagreement as investigation. All correct and consistent with J.5 and the sycophancy defences.
- **One standard, no tiers, audit as affordance, proportionate lookups, a rich answer need not be a long answer** (§2.1, §7.1, §7.2). Carries D-15 and RS-4 into consumer language without weakening them. v2.0 adds the missing second axis (disclosure classes).
- **The §7.4 dialogue's fork** — opportunity vs realization vs profitability, with the earlier answer recorded with its original meaning. A genuine reference investigation; v2.0 moves it to the front door as the ask-back.
- **The six "revealing moment" lines** — the only sentences in the person's voice, each a testable felt outcome. v2.0 keeps one per experience.
- **The rejections table** (§12.2): no life simulator, no universal score, no omen feed, no AI council as evidence, no indiscriminate capture, no default adaptation after events, no remedies as engagement. Each consistent with the Learning Layer non-negotiables and the typed-quantity rule. Kept verbatim in substance; two hardened.
- **"Unknown is not false; event time is not knowledge time; repeated readings are not independent trials"** (§11.2 close) and the refusal to claim present superiority ("cannot be demonstrated by engineering scale", §1). Correct epistemic posture; v2.0 makes it operational.
- **The three proving journeys as literal test prompts** (§11.3) and the stance that an ordinary result, a tie or an inability to conclude are valid outcomes (§3). Kept, with null cases added.

## 6. Where v2.0 answers each finding

The right-hand column of the §3 table is the traceability: every verified or contested cluster names the v2.0 section that answers it. The two refuted clusters are answered as elevations, not corrections (§4.1).

## 7. Notes for Astra

**Keep from v1.1, verbatim in substance.** The design order; earned insight over volume; the six-link authenticity chain; the separate proof obligations and the refusal of a composite score; "the person is not the chart"; one register, no tiers, audit as affordance; the rejections table; the three proving journeys; "unknown is not false, event time is not knowledge time, repeated readings are not independent trials".

**Change in v1.1, whichever document goes forward.** Restore calibrated prediction as one of the three numbered obligations and state the band rule as typed confidence (F-01). Carry MACRO_PLAN §3.5.C/§3.5.F and the NCD-4/ND.2 interstitial verbatim into the boundaries, with a stance on āyurdāya (F-02, F-04, F-10). State the two-axis rule and declare the missing disclosure class as a scope event (F-03). Name the śāstric spine the floor encodes and keep the register phala-oriented (F-19, F-23). Retire "beyond-Acharya" from product language; keep the three-conclusion test and name the superiority mechanisms (F-21, F-51). Correct the three-door description, cite RETRIEVAL_STRATEGY and the CURRENT Paripraśna set, restore the six maturity states, make citations repo-relative (F-34, F-38, F-49). Name a wedge, three measurable instruments and a baseline step (F-42, F-43, F-32). List the decisions the native must rule on and make supersession conditional (F-44, F-66). Give every need a disposition and name each deferred capability's missing operator and kind (F-36, F-60). Add the operator instrument, rendering/outputs and remedies rows; name the personas (F-58, F-59, F-65, F-08). Storyboard first use, day thirty and year three; rewrite the dialogue as the ask-back (F-12, F-13). State the null-result behaviour, the harmful-content rule, and the deletion-vs-immutability rule (F-25, F-07, F-05).

**Take from v2.0 if v1.1 remains the base.** §1.3 (unit of value), §2.1 (rings of consent), §3.2–§3.4 (superiority mechanisms, the śāstric spine, the discrimination definition), §5 (dispositions), §8 (binding invariants with honest status), §10 (boundaries with detectors), §11.1–§11.3 (structural falsifiers, north-star instruments, "why the number is null today", operational evaluation table), §13 (decisions), §14 (baseline-first sequence), Appendix C (kinds of deferred capability).

**Where v2.0 chose differently from the critics.** It did not take the 40% cut (F-18): it judged that the binding content a component-alignment reference needs — dispositions, invariants, detectors, decisions — is worth the length, and put a one-page front (§0 and the headline) in place of brevity. It kept the unit-of-value model despite F-11's refutation, as an elevation. It folded the "living atlas" and "question compass" into E1/E2 rather than dropping them (V4 would drop them; V1/V2 would keep them) because their served kernels exist (`bodha_contradictions`, `bodha_discoveries`, the escalation valve) and only the *importance ranking* is unearned.

**Questions only the native can settle** — v2.0 §13, eighteen decisions. The three that gate everything else: D-1 (mission weighting), D-2 (a disclosure class for consenting individuals), D-13 (turn the machinery on for the native's chart and measure the baseline before any elevation brief).

**Astra's reconciliation (2026-09-12, 04:57).** While this audit was being finalized, Astra produced `MADHAV_PRODUCT_DEFINITION_RECONCILIATION_v1_0.md` and a v2.1 synthesis from the earlier copy of v2.0. Its §2 corrections were checked against the sources and three were confirmed as factual errors in v2.0 — settled readings are reproducible after rebuilds by snapshot-on-consume (PPR-20); life events and birth data are class C1 while ledgers, outcomes and calibration are C3; OT-4 and OT-6 are proposed leans awaiting ruling — and fixed in v2.0.1 together with the overstatements it named ("every claim" vs "every significant claim"; prediction as the only checkable obligation; an unverifiable market claim; flag activation as a baseline step). v2.0.1's changelog records each. The reconciliation's remaining points are matters of emphasis that the native's ratification will settle.

**Method caveat.** Ten lenses and up to three verifiers per finding reduce bias; they do not remove it. Every verifier had the same governing documents and the same codebase; agreement among them is evidence of consistency with those sources, not of truth about the product's future. The native's judgment, and an eventual blinded acharya panel, remain the arbiters.


---

## Appendix A — Full per-finding ledger

Each entry: the representative critic's claim and evidence, the other critics who raised the same point, each verifier's verdict with confidence and reasoning (truncated), the adopted proposal, and where v2.0 answers it. Refuted clusters are listed in §4.1 and omitted here.

*Status counts: {'VERIFIED': 58, 'REFUTED': 2, 'CONTESTED': 9} of 69 clusters.*

### F-01 · VERIFIED · CRITICAL · contradiction · v1.1 §1, §3, §7.6, §11.2, E3/E5

**Calibrated prediction demoted; 'band or nothing' inverted to 'band where justified'; emission-time rules omitted**

*Claim (internal and governance contradiction hunter):* MACRO_PLAN §3.5.A.1/§3.5.G and PA B.6 make a calibration band mandatory on every probabilistic output ('Outputs without a calibration band attached are not valid outputs'); the vision inverts the default ('calibration where justified', 'appear only where their evidential basis supports') without declaring the amendment, and omits CW.PPL's log-at-emission rule and §3.5.E's never-modifiable windows while E5 'accepts corrections' unscoped. The code sides with the vision's anti-fabrication instinct (L5 STRUCTURAL, judgment_query capped at structural_prior, human-committed bands) but also with MP's rules (every detected forward claim captured at turn commit and DB-frozen), so the vision must state the rule as a bi-conditional and declare it as the amendment.

*Evidence:* VIS:148 'Event probabilities or narrow dates appear only where their evidential basis supports that meaning'; VIS:356 'do not invent numerical ... confidence scores'; VIS:460 'calibration where justified'; VIS:162 'accepts corrections'. MP:592 §3.5.A.1 'confidence bands are always attached'; MP:636-640 §3.5.G point estimate, interval, method pointer, failure modes, 'not valid outputs' otherwise; PA:144-146 B.6 'Every RPT-level claim carries a confidence score (0.00–1.00)'; MP:521 CW.PPL 'Every falsifiable claim the system surfaces logged at emission with a verification window'; MP:626-628 'never modifiable. Native cannot revise a prediction after outcome is known'. Reality: 00_ARCHITECTURE/L5_SEAL_AND_SHIP_REPORT_v1_0.md:23-26 STRUCTURAL; platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:49-53 structural_prior never a probability; PTA:3506-3518 T-8 precision theater; pla…

*Also raised by:* C3_epistemics_research-02, C8_beyond_acharya_adversary-09

*Verification:*

- textual: **stands** (confidence 0.80) — TEXTUAL CHECK OF THE DOCUMENT (VIS = scratchpad/inputs/VISION_v1_1.md; MP = 00_ARCHITECTURE/MACRO_PLAN_v2_0.md; PA = 00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md).

CORE OF THE FINDING SURVIVES — the document does say and omit what is claimed:
1. VIS:148 literally reads "Event probabilities or narrow dates appear only where their evidential basis supports that meaning." This is an emission-side statement (E3 "reveali…
- grounding: **refuted** (confidence 0.80) — REFUTED as stated (critical / undeclared inversion of governance). A low-severity citation-completeness residual survives and is given in revised_proposal.

1. The governance citations are accurate but incomplete. MP:592 §3.5.A.1 "confidence bands are always attached"; MP:636-643 §3.5.G "All M5/M6 outputs carry calibration band disclosure ... Outputs without a calibration band attached are not valid outputs; the PPL …
- materiality: **stands** (confidence 0.78) — MATERIALITY VERDICT: the finding survives in substance but its severity is overstated and its proposed text would make the definition LESS grounded if adopted verbatim; a revised proposal is supplied.

WHY IT IS MATERIAL (not stylistic). (1) The vision decides the single question that most shapes E3/E4 output across L4, L5, the registry, Paripraśna and managed prashna_ask — when a number may be emitted and what it mu…

*Adopted proposal:* Keep VIS:356 (§7.6) unchanged — it governs prioritization of distinctions, not claim confidence. Make the following edits instead.

(1) §6.1, insert a new paragraph immediately after VIS:233 ("...without drowning every answer in a disclaimer."):
"Confidence rule (proposed amendment of MP §3.5.A.1/§3.5.G and PA B.6, restated as a bi-conditional). Every claim of kind 4 or 5 carries a confidence type — structural prior · corroborated · contested · unvalidated. A prospective claim (kind 5) is stated as a probability, interval or narrow date only when it carries the full calibration disclosure: point estimate, interval, pointer to the calibration cell/method that produced it, and that cell's known failure modes (MP §3.5.G). A number without those four elements is not a valid output; a prospective claim without a number is valid and is typed unvalidated. Words that function as probabilities ('likely', 'strong', tier labels) fall under the same rule. Until this amendment is ratified, MP §3.5.A.1/§3.5.G and PA B.6 govern as written."

(2) E3, VIS:148, append after "...supports that meaning.": "— under the confidence rule in §6.1. Every falsifiable forward claim emitted in E3 or E4 is logge…

*Answered in v2.0:* §1.1, §11.2, §10 B-8/B-9, §13 D-1/D-3 — adopted.


### F-02 · VERIFIED · CRITICAL · gap · v1.1 §10, P01/P06/P07, §8 L4 row

**§3.5.C/§3.5.F hard stops omitted: date-of-death, mortality windows, suicide-adjacent, health/mental-health sign-off; āyurdāya/māraka/santāna stance absent; fertility & mental-health classes unassigned**

*Claim (ethics, safety, consent and cultural responsibility):* The only mention of death in §10 is 'Do not guarantee … disease, death'. The absolute rules — no date-of-death under any class, no individualized mortality windows (aggregate framing only), suicide-adjacent hard stop with no plan built, health-crisis/mental-health seal + double red-team + native sign-off, and the native's own ND.2 native-self interstitial bifurcation — are absent, even though the system computes āyurdāya by three methods plus māraka significators and serves it. P01 'psychological patterns' and P07 'health-related inquiry' enter the HS-3 class with no stated control.

*Evidence:* Vision V:426 'Do not guarantee wealth, marriage, childbirth, disease, death…'; V:192 P07 'not illness prediction'. MP §3.5.C at 00_ARCHITECTURE/MACRO_PLAN_v2_0.md:610–613; PA protection clause PROJECT_ARCHITECTURE_v2_2.md:1077. Runtime translation: SAFETY_PRIVACY_TENANCY_v0_1_PROPOSAL.md:57–86 (HS-1…HS-4); platform/src/lib/pariprashna/safety/types.ts:20–31; safety/gate.ts:60–84 (resolveAction: HS-2 hard_stop, HS-4 seal always, HS-3 interstitial only for native_self); safety/fixed_responses.ts:31–52; safety/sensitive_capabilities.ts:37–55 (MORTALITY_CLASS = get_ayurdaya/ganita_ayurdaya_get); platform/src/app/api/mcp/prashna_ask/route.ts:270–300, 470–482; platform/src/app/api/pariprashna/safety/review/route.ts:36–44 ('MP §3.5.C requires … explicit native sign-off'); platform-mcp/src/tools/kala_views/upaya.ts:15–22 ('native_self does NOT unlock it'). ND.2 bifurcation: NATIVE_DIRECTIVES_FOR_…

*Also raised by:* C10_contradiction_hunter-02, C2_jyotish_acharya-02, C7_ethics_safety_culture-10, C1_consumer_ux-06

*Verification:*

- textual: **stands** (confidence 0.93) — TEXTUAL ACCURACY VERDICT: the finding correctly describes what VISION_v1_1.md says and omits; I could not refute it.

What the document actually says (scratchpad/inputs/VISION_v1_1.md): the word "death" occurs exactly once in the whole 609-line document, V:426 "Do not guarantee wealth, marriage, childbirth, disease, death, a partner's intentions or other external outcomes from a chart." Line-greps return zero hits fo…
- grounding: **stands** (confidence 0.90) — GROUNDING VERDICT: the finding survives; every load-bearing claim checks out against governance and the checkout, and the one refutation angle that looked promising (the vision's blanket non-supersession clause) does not hold.

VERIFIED TRUE (governance):
- The vision's only mortality text is V:426 "Do not guarantee wealth, marriage, childbirth, disease, death…" and V:427 "Do not diagnose health or fertility…". Grep …
- materiality: **stands** (confidence 0.85) — MATERIALITY VERDICT: the finding survives; the change is substantive, not stylistic, and the definition is weaker than the governance it must serve on the one point where governance is absolute. The proposal's FORM needs tightening (see revised_proposal).

1. The gap is real and total. grep of VISION_v1_1.md for suicide / self-harm / mortality / longevity / āyurdāya / māraka / minor / mental returns zero hits. "death…

*Adopted proposal:* Keep the finding; adopt a tighter form than C7 §4 (cite governance by reference, no inline enforcement map, one dated status line, and mark the one genuinely new boundary as proposed). Concretely:

(1) Insert after V:434 a new subsection:

"### 10.1 Death, longevity, health and progeny — the absolute boundaries
These restate MACRO_PLAN §3.5.C and the PROJECT_ARCHITECTURE §K protection clause as product behavior; the governing text is theirs, not this document's.
- Madhav never produces a date, year or age of death for anyone — not as an estimate, a range, a probability or indirectly — under any use context, on any channel. Classical longevity doctrine (āyurdāya by all three methods, māraka significators) is computed and method-attributed at L1 and may be served only as the classical band class and as aggregate period-quality framing; an individualized mortality window is never composed, and mortality-class capabilities are excluded from any plan that reaches for one and from the default consult surface.
- A question carrying suicide or self-harm signals receives a fixed, calm, non-analytic response with support-resource framing; no retrieval plan is built.
- Health-crisis and menta…

*Answered in v2.0:* §10 B-1…B-4, §5 P06/P07/P24, §2.1 — adopted verbatim from governance.


### F-03 · VERIFIED · CRITICAL · contradiction · v1.1 §2.1, §10, §14

**Audience falls under no admitted disclosure class; 'no audience tier' stated on one axis only (two-axis rule missing); 12-month user over-served by public-product design**

*Claim (ethics, safety, consent and cultural responsibility):* The vision correctly preserves the D-15 register axis ('use contexts, not intelligence tiers') but never states the MACRO_PLAN §3.5.B disclosure-class axis, never restates the binding MP:107 sentence ('for consenting audiences under stated disclosure tiers'), and defines the product for 'consenting people with varied astrological knowledge' — an audience that is not native, cohort, acharya-reviewer or the fail-closed public class. Under MP §3.10.D a consumer subject is a v3.X scope-redefining event that the vision must declare rather than leave implicit.

*Evidence:* V:69 'designed to be reusable for consenting people with varied astrological knowledge'; V:71 'use contexts, not intelligence tiers'; V:602 cites MP:103 but not MP:107. MP §3.5.B four audiences with per-audience obligations, public = 'Redacted; aggregated; calibration bands mandatory; no individual-fate-adjacent claims' (MACRO_PLAN_v2_0.md:601–606); MP §3.10.D v3.X = 'new primary subject … commercialization' (:797–801); §3.9.E (:768). SAFETY_PRIVACY_TENANCY_v0_1_PROPOSAL.md:32–56 closes the PTA open check: 'register is never plural; disclosure class is never called a tier of quality'; 'public is FAIL-CLOSED — the class exists in the enum but serves nothing until the §3.9.B publication protocol is built'. Schema: migration 575 subject_kind = native_self | cohort | test (platform/supabase/migrations/575_pariprashna_chart_subject_consent.sql:30–40) — no public/consumer class. audience_tier …

*Also raised by:* C4_engineering_alignment-09, C5_product_strategy-04

*Verification:*

- textual: **stands** (confidence 0.85) — TEXTUAL CHECK — the finding's core omission claims are literally true, so it cannot be refuted; but its framing (kind=contradiction, severity=critical, 'leave implicit') overstates what the document fails to say, because the vision already hedges audience expansion explicitly.

Confirmed as stated (whole-document grep of VISION_v1_1.md):
1. No disclosure-class axis anywhere. 'disclosure' appears only at V:358 ('perso…
- grounding: **stands** (confidence 0.82) — GROUNDING VERDICT: the finding's factual core survives verification; its kind ("contradiction") and severity ("critical") are over-graded, and its proposed text has three grounding defects that must be corrected before it is adopted.

CONFIRMED against source:
1. MP:107 is the binding sentence ("for consenting audiences under stated disclosure tiers"); the vision cites MP:103 (the "## Ultimate goal" heading) at V:602…
- materiality: **stands** (confidence 0.80) — MATERIALITY VERDICT: the change is material and survives, but the finding is over-graded: it is a load-bearing GAP, not a contradiction, and 'major' not 'critical'.

Why it is material for this document's purpose (a whole-product reference every component aligns to, taken back to another AI author):
1. The audience is the premise of a 'consumer product vision', and the vision names only one of the two governed axes. …

*Adopted proposal:* Replace V:69-71 with the following, and update S3 (V:603) to cite PARIPRASHNA_ARCHITECTURE_v1_0.md (PPR-24) and PARIPRASHNA_DECISION_REGISTER_v1_0.md (D-15), retaining PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md:2277 only as the rationale record.

"### 2.1 Who this is for — one register, several disclosure classes

The immediate proving context remains the authorized native and existing permitted use. The target experience is designed to be reusable for consenting people with varied astrological knowledge, and useful to authorized practitioners and researchers. Two governed axes apply, and this document keeps them distinct.

**One register.** Everyone entitled to a reading receives the same standard of investigation and grounding: acharya-grade, plain-language, with technical evidence available through inspection rather than reserved as a better answer for experts. There is no depth parameter and no quality tier (D-15; PPR-24). 'Register' is never plural in this document.

**Several disclosure classes.** Who may receive which output classes, under which consent, redaction, anonymization and calibration-disclosure obligations, is governed by MACRO_PLAN §3.5.B and is an access-control ax…

*Answered in v2.0:* §1.4, §2.1 rings, §13 D-2 — adopted; two-axis rule stated; fifth class proposed.


### F-07 · VERIFIED · CRITICAL · gap · v1.1 §6.1–§6.3, §10

**No stance on fatalistic, casteist or misogynistic classical content; 'fidelity to sources' has no harm rule**

*Claim (senior Jyotish acharya (Parāśari, Jaimini, KP, Tājaka, Nāḍī, Praśna, Muhūrta, Upāya)):* The corpus ingests verbatim the varṇa attributions of planets and nakṣatras, strī-jātaka judgments and fatalistic phala, models Varṇa-kūṭa as a marriage doṣa, and carries no content-class tag on chunks; the vision forbids framing a person as morally inferior but never says what the instrument does when the source itself does so. A faithful retrieval plus a faithful synthesis will reproduce the passage. The tradition supplies its own warrant for adaptation (deśa-kāla-pātra; varṇa read as vṛtti/svabhāva; strī-jātaka read symmetrically) and the vision's §6.1 chain has the right slot (link 4, modern lineage) but does not use it.

*Evidence:* V:428 'Do not frame suffering, identity or family circumstances as proof of moral inferiority'; V:37 'explore it with seriousness and respect'; V:237 'fidelity to sources'. Repo: platform/python-sidecar/brahmagyan/l0_texts.py:392-396 (BPHS 2.7-9 'Planetary castes and social classes', tags planetary_caste/social_class); platform/python-sidecar/brahmagyan/l0_nakshatra.py:44-364 (varna='Mleccha', 'Butcher', 'Shudra' on nakṣatra rows); platform/python-sidecar/brahmagyan/l0_doshas.py:680-694 (varna_dosha: 'groom's varna lower than bride's'); platform/migrations/ws2_l0_texts.sql:42-56 (chunk schema has no content-class field); platform/migrations/465_classical_text_chunks_ocr_cleanup.sql:32-52 (adds OCR-quality fields only); pipeline/orchestrator/writers/bg_text_index.py:1-15 (keyword-only topic classifier).

*Also raised by:* C7_ethics_safety_culture-06

*Verification:*

- textual: **stands** (confidence 0.90) — TEXTUAL LENS — the finding reads the document correctly and the point is not covered elsewhere.

1. Omission confirmed by whole-document search. VISION_v1_1.md (609 lines) contains no occurrence of caste, varṇa/varna, jāti, gender, woman/women, strī, widow, misogyn-, fatalis-, deśa-kāla-pātra/desha, "historical setting", "modern" lineage or "content class". The only "adapt"/"reinterpret" hits are V:526 ("Automatic pe…
- grounding: **stands** (confidence 0.90) — I tried to refute F-07 on three fronts (false codebase claim, contradiction with settled governance, proposal violating CLAUDE.md) and failed on all three; every factual claim verified, with one trivial citation-path error.

CODEBASE CLAIMS — all CONFIRMED:
- Caste attributions ingested verbatim: platform/python-sidecar/brahmagyan/l0_texts.py:392-396 (BPHS 2.7-9 "Sun: Kshatriya ... Saturn: Shudra. Planetary castes", …
- materiality: **stands** (confidence 0.85) — MATERIALITY: not refuted. The change is neither stylistic nor trivial; it closes a real hole in the definition that alignment would otherwise propagate into every component.

1. The exposure is live, not hypothetical. Repo: platform/python-sidecar/brahmagyan/l0_texts.py:392-396 (BPHS 2.7-9 planetary castes, tags planetary_caste/social_class); l0_nakshatra.py:44-914 (varna="Mleccha"/"Butcher"/"Shudra"/"Farmer" on naks…

*Adopted proposal:* Insert a new §6.6 after §6.5 (V:275), and make three small consequential edits:

### 6.6 Reading the tradition's hard passages
Some authentic passages and rules encode social hierarchy (varṇa/jāti attributions of grahas, nakṣatras and Moon-signs; varṇa-kūṭa), gendered worth (strī-jātaka judgments of chastity, "high birth", widowhood or a husband's death), disability, or flat fatalism ("will die", "will be poor", "fated"). The instrument neither deletes nor recites them. Fidelity means the source is never misquoted; responsibility means it is never applied to a person as a finding.
1. In the source lane (§6.1 link 1) the passage is preserved verbatim, with edition, date and setting, and stays reachable to anyone studying the tradition.
2. Such content is never applied to a person as a personal finding in any reading: a caste- or gender-hierarchical rule does not enter a personal reading, a relationship/kūṭa compatibility verdict, a remedy prescription or a question-compass suggestion. Where a rule of this class would otherwise have been consulted, the reading records its exclusion as a declared omission (§7.1), not a hidden one. This is a claim-type rule, not an audience tier (§2.1)…

*Answered in v2.0:* §6.3, §10 B-12, §13 D-6 — adopted as a proposal.


### F-19 · VERIFIED · CRITICAL · gap · v1.1 §3, §4, §7.1, §8 L1–L3 rows, E3, P10

**The tradition's judgment architecture (śāstric spine) is absent: lagna/kāraka primacy, varga hierarchy, daśā–gochara double confirmation, aṣṭakavarga gating, daśā-system applicability**

*Claim (senior Jyotish acharya (Parāśari, Jaimini, KP, Tājaka, Nāḍī, Praśna, Muhūrta, Upāya)):* The document never names lagna/lagneśa, candra-lagna, kārakas, bhāva/bhāveśa, the varga hierarchy with D9 and domain-varga ratification and vargottama, bala as arbiter, yoga bhaṅga, argalā, or KP sub-lords; it speaks in method-agnostic abstractions, so an alignment exercise reading it as the definition has nothing binding a 'complete reading' to the consultations a master performs. The codebase already encodes this spine as the executable per-intent acharya floor, which the vision does not mention and so cannot protect.

*Evidence:* V:102 'Relevant divisions, relationships, systems, domains and time scales are connected'; V:369 L1 row 'Canonical facts, precise hierarchies, divisions, relationships, conditions and sensitivity'; V:304 'the system identifies the supported evidence families'. Repo: platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_floors.py:54-98 (wealth_deepdive acharya floor: bhava_condition, bhavesha_condition, karaka_condition, from_moon_view, chalit_cusp_read, bhava_bala_scan, ashtakavarga_scan, sensitive_degree_check, divisional_facts D2/D1/D9/D11, varga_ratification, karakamsa_read, kp_cusp_sublord_read, special_lagna_read, chara_karaka_read, dhana_yoga_scan, nbry_scan, sudarshana_agreement_check, bhavat_bhavam_check, argala_read, dispositor_closure_read); platform/src/lib/pipeline/compiled_floor_adapter.ts:31-36 (ensureB11WholeChartReadFloor, ensureDashaContextFloor); PROJECT_ARCHIT…

*Also raised by:* C2_jyotish_acharya-06

*Verification:*

- textual: **stands** (confidence 0.82) — TEXTUAL LENS — the finding's factual claims about what the document says and omits are accurate, with two overstatements that lower severity but do not refute it.

VERIFIED OMISSIONS (grep over all 609 lines of scratchpad/inputs/VISION_v1_1.md): zero occurrences of lagna, lagneśa, candra-lagna, kāraka/karaka, bhāva/bhava, bhāveśa, varga, D9, navāṃśa, vargottama, ṣaḍbala/shadbala, vimśopaka, bhāva-bala, aṣṭakavarga, b…
- grounding: **stands** (confidence 0.62) — Factual core holds. VISION_v1_1 contains no occurrence of lagna, kāraka, varga, bhāva, aṣṭakavarga, sub-lord, argalā, daśā, or gochara (grep over the file: only "divisions" at V:102, "whole-chart" at V:132/218/300/308/377). It never names the acharya floor either. The repo does encode the spine as a per-intent floor: `bg_vidhi_floors.py:54-98` (WEALTH_DEEPDIVE_ITEMS: bhava_condition, bhavesha_condition, karaka_condit…

*Adopted proposal:* 1) At V:300, replace "For current natal interpretation those completeness obligations include the governed whole-chart protocol." with: "For current natal interpretation those completeness obligations are the governed whole-chart protocol (B.11/H.4) and its executable form, the compiled per-intent acharya floor (PARIPRASHNA_ARCHITECTURE PPR-15; vidhi registry `vidhi_intent_floors` / `vidhi_floor_items`). A complete natal investigation consults, and reports as served, empty or unavailable, the tradition's evidence families: lagna and lagneśa with the Moon and Sun frames (Sudarśana agreement); the naisargika and cara kārakas of the domain and the karakāṃśa; the domain bhāva and bhāveśa from lagna and from the Moon, in rāśi and chalit; the varga hierarchy — D1, D9 for every planet, the domain varga as ratifier, vargottama noted; strength as arbiter — ṣaḍbala, vimśopaka, bhāva-bala, aṣṭakavarga; yogas and doṣas with formation, cancellation (bhaṅga) and partial-formation status; argalā and dispositor closure; the KP cuspal sub-lord and significator ladder as an independent witness; and the daśā spine with gochara as E3 defines. The floor is compiled per question, not a fixed order. A co…

*Answered in v2.0:* §3.4 śāstric spine; E3 — adopted.


### F-21 · VERIFIED · CRITICAL · gap · v1.1 §1, §3, §11.1, §11.2

**'Beyond-Acharya' is unfalsifiable and never names what the master does vs what the machine exceeds; wrong operating benchmark; expert agreement ≠ validity**

*Claim (C8_beyond_acharya_adversary — adversary of the "beyond-Acharya" claim: Barnum effect, complexity theatre, false precision, averaging incompatible schools, LLM fluency as judgment, unvalidatable structural claims, dependence on unproven classical rules; then rebuild the claim at exactly the strength that can be tested.):* The document never defines the comparator, unit of comparison, budget, reviewer pool, baseline, pre-registration rule or the result that withdraws the claim; 'simpler competent reading' (VIS:112) is undefined. It also conflates a head-to-head protocol with the §J/PA:94 review protocol ('reveals things I would not have seen on first pass'), which is vulnerable to hindsight and persuasion unless the acharya's first pass is recorded before the reveal.

*Evidence:* VIS:97 'a demonstrated improvement in the quality of understanding' (no comparator); VIS:458 blinded judgments with no n, independence or pre-registration. The project already ratified the missing pieces and VIS cites none: PROJECT_ARCHITECTURE_v2_2.md:92 '(k) External validation … acharya-reviewer panel of n ≥ 3'; PA:94 three-conclusion test; MACRO_PLAN_v2_0.md:685 '≥ 15 years practice … no prior commercial or personal relationship with native … n ≥ 3'; MP:699 disagreements 'logged … (not averaged)'; 00_ARCHITECTURE/ACHARYA_ENGAGEMENT_KIT.md:1-6 (CLOSED v1.0). Conflict: MP:492 M10 gate is an 'acharya-grade composite score'; VIS:469 rejects any weighted score. Only a self-review exists: 08_CLASSICAL_CROSS_REFERENCE/ACHARYA_REVIEW_SAMPLE_v1_0.md:8.

*Also raised by:* C2_jyotish_acharya-05, C5_product_strategy-03, C3_epistemics_research-10

*Verification:*

- textual: **stands** (confidence 0.72) — CORE OF THE FINDING SURVIVES TEXTUALLY. VISION_v1_1.md:97 states the beyond-Acharya benchmark with no comparator ("It is a demonstrated improvement in the quality of understanding"). The only expert-comparison specification is VISION_v1_1.md:458: "Blinded judgments of source fidelity, interpretation, discrimination and missed connections. | Qualified reviewers, common case/context, transparent rubric and disagreement…
- grounding: **stands** (confidence 0.80) — Every governance citation verifies: PROJECT_ARCHITECTURE_v2_2.md:92 "(k) External validation ... acharya-reviewer panel of n ≥ 3"; :94 three-conclusion test (a quality test, not a validity test); MACRO_PLAN_v2_0.md:685 "≥ 15 years practice ... no prior commercial or personal relationship ... n ≥ 3"; :699 "both verdicts are logged ... (not averaged)"; :492 M10 gate "acharya-grade composite score"; ACHARYA_ENGAGEMENT_K…

*Adopted proposal:* Four bounded edits, keeping VISION:11 (does_not_supersede canonical governance) and VISION:439 (protocols established before numeric targets) intact:

(1) Replace VISION_v1_1.md:97 with: "The benchmark is not a longer reading or a larger technique inventory. 'Beyond-Acharya' is a comparative claim about readings, made per dimension of the table below and per question class, never globally: for a frozen set of questions on charts the reviewers have not previously read, a Madhav reading under a declared budget contains correct, source-faithful, chart-specific distinctions that (a) a qualified independent reviewer's own reading, recorded before any Madhav output is shown, and (b) a simpler competent reading under the same budget did not contain — while adding no more incorrect or unsupported claims than either. A dimension's claim is withdrawn wherever that test fails. Until the first such comparison has been run and reported, the operative standard is acharya-grade (PROJECT_ARCHITECTURE §A.3/§H), and no served field, surface or text asserts 'beyond'."

(2) After VISION_v1_1.md:112, define the comparator by pointing to the document's own source rather than leaving it abstract: "'Simpl…

*Answered in v2.0:* §3.1–§3.3, §13 D-8 — adopted; phrase retired.


### F-25 · VERIFIED · CRITICAL · gap · v1.1 §11, §6.4, §10, E3

**Null-result behaviour never stated; served classical doctrine is grandfathered**

*Claim (epistemics, forecasting science and research methodology):* The document says the instrument must be able to find that a proposed rule contributes nothing (V:259) and that E4 can conclude astrology does not distinguish alternatives (V:152), but both apply to new candidates or one question. It never states what the served product does when an already-served claim family (financial-relief windows, marriage timing, yoga activation) evaluates null or negative: no per-family status, no demotion or withdrawal rule, no statement that the mainstream null result is a legitimate product outcome.

*Evidence:* V:148 'Event probabilities or narrow dates appear only where their evidential basis supports that meaning' and V:460 'calibration where justified' have a currently-false antecedent for every family: L5 sealed STRUCTURAL, all 9 multipliers prior_only, evidence_grade='structural_no_calibration' (00_ARCHITECTURE/L5_SEAL_AND_SHIP_REPORT_v1_0.md:23-26, 107-110); R6 SRC:25 'Neither the source audit nor these contracts demonstrates reliable prediction of wealth, illness, marriage'. Governance rules the vision drops: MP §3.5.A.6 'Every output is rescindable if calibration data reveals it was unfounded' (MACRO_PLAN_v2_0.md:597) and §3.9.D review-not-publication after two cycles below floor (MP:764). External prior is null: Carlson, Nature 318 (1985) 419-425; Dean & Kelly, JCS 10(6-7) (2003); Dean et al., Astrology Under Scrutiny (2016). The only anti-manufacturing rule (V:271) sits at the researc…

*Verification:*

- textual: **stands** (confidence 0.85) — Textually the finding holds. VISION_v1_1.md never states what a served claim family does after a null/negative evaluation: grep for rescind/reversib/review-not-publication/demot/withheld/base rate returns nothing in the body (only "withholding a false precision" at V:416 and "misses matter as much as hits" at V:381, both principles, not rules). V:148 and V:460 are conditionals ("appear only where their evidential bas…
- grounding: **stands** (confidence 0.80) — Evidence checks out. VISION §11 contains only 11.1–11.3 (V:437-473); grep for null/withdraw/rescind/demote/collect-only finds nothing beyond research-layer text (V:255-271) and E4's per-question "does not distinguish" (V:152). V:148 and V:460 ("calibration where justified") do have a currently false antecedent for every family: L5 seal confirms all 9 multipliers `prior_only`, `evidence_grade='structural_no_calibratio…

*Adopted proposal:* Insert §11.4 "Null-result behaviour and claim-family status" as the critic drafts it, with three grounding corrections: (1) keep per-claim confidence (PROJECT_ARCHITECTURE B.6, numeric 0.00–1.00) distinct from event probabilities/narrow dates — the status governs the latter only, so the rule does not silently repeal B.6; (2) a family status must be an earned signal per CLAUDE.md §N.8 — "evaluated: supported/null/negative" may only be set by a detector over resolved ledger rows with a stated n and minimum-n gate, otherwise the field reads collect-only; today that is exactly L5's `evidence_grade='structural_no_calibration'` / `promotion_status='prior_only'` (L5_SEAL_AND_SHIP_REPORT_v1_0.md:23-26, 107-110), so ratification changes no served output; (3) cite the rules being restated rather than inventing them: MACRO_PLAN §3.5.A.6 rescindability (MP:597), §3.9.D review-not-publication after two cycles below floor (MP:764), and the existing collect-only NO-LEAKAGE regime (serving_path_manifest.ts, calibration_leak_guard.ts) which already forbids annotating served readings with outcomes — the null finding is shown as family-status data, never as a calibration write into serving.

*Answered in v2.0:* §6.4, §13 D-7 — adopted.


### F-26 · VERIFIED · CRITICAL · weakness · v1.1 §3 row, §11.2 row

**'Personal specificity' is mere input-sensitivity; blinded chart-discrimination and Barnum control absent; volume and category-heuristic valence make generic readings the default risk**

*Claim (epistemics, forecasting science and research methodology):* 'A meaningful change in this person's configuration produces an appropriately different interpretation' (V:103) and 'Blinded different-chart and irrelevant-input comparisons' (V:456) test only that output changes when input changes — a pipeline printing planetary positions passes. The honest test of specificity to the person is blinded discriminability (subject picks own reading from k decoys; blinded judges match readings to profiles), the design used since Carlson 1985 and always at chance. The Forer/Barnum effect is exactly the E1 'revealing moment' (V:128); V:462 disclaims satisfaction as a metric but gives no control that could detect a Barnum reading.

*Evidence:* No harness in code: grep -rli 'ablation\|blinded' platform/src platform-mcp/src evals → none; the 12-fixture corpus runner is 'SCAFFOLDING, explicitly … does NOT itself talk to the deployed route' (platform/src/lib/pariprashna/corpus/runner.ts:5-19). Decoy supply exists: bg_cohort 110,000 synthetic charts 'NOT real people' with lagna and graha sign/nakshatra (writers/bg_cohort.py:11-21). Carlson, Nature 318 (1985); McGrew & McFall, JSE 4 (1990); Nanninga, Correlation 15 (1996); Forer, JASP 44 (1949). §3's 'Statements that fit almost any person' (V:103) names the failure without a detector.

*Also raised by:* C8_beyond_acharya_adversary-07

*Verification:*

- textual: **stands** (confidence 0.62) — Textually the finding is partly overstated but its core stands. Overstated: V:456's control column already says "Blinded different-chart ... comparisons", and "blinded" is meaningless for a mere output-changes-when-input-changes diff — it implies a blinded party judging which reading belongs to which chart, i.e. a discriminability design in embryo. The document also already disqualifies "Statements that fit almost an…
- grounding: **stands** (confidence 0.82) — Grounding checks confirm the finding rather than refute it. (1) The vision text is as quoted: §3 row "Personal specificity | A meaningful change in this person's configuration produces an appropriately different interpretation | Statements that fit almost any person" (VISION_v1_1.md:103) and §11.2 "Blinded different-chart and irrelevant-input comparisons under equal budgets" (V:456) — both are input-sensitivity crite…

*Adopted proposal:* Keep the §11.2 "Personal specificity" row but rewrite it: "| Personal specificity | (1) Input sensitivity: material configuration changes alter the appropriate claims (claim-id diff, not prose diff) while irrelevant-input perturbations leave them unchanged. (2) Blinded discriminability: a blinded party (the subject, or a judge holding a vetted profile) identifies the reading belonging to a given chart among k matched decoys at better than 1/k, with a confidence interval at a pre-declared n. | Decoys matched on birth-year/sex/place drawn from the synthetic cohort or consented charts; a generic-reading comparison condition so perceived accuracy of the specific reading is measured as a difference from the generic one, not in isolation; no feedback before study close; null results published. |". Append to §3 row "Personal specificity", "What does not qualify": "a reading that merely differs textually from other charts' readings, or the subject's own sense of recognition."

*Answered in v2.0:* §11.3 blinded specificity row; §11.1 structural falsifiers — adopted.


### F-33 · VERIFIED · CRITICAL · contradiction · v1.1 §13.2, §8 closing, §1.1/§13.3

**§13.2 is not executable under live Nirmāṇa authority, holds and PARKED pillars; 'does not reopen' vs concrete new demands on frozen L0/L1/L2; step four reinstates an upstream-first programme the frozen layers already completed**

*Claim (C4_engineering_alignment — engineering and architecture alignment with the real system (three request paths, D-15, density/hardFloor, planner floor as B.11 enforcement, FROZEN orchestrator, build/serve/evaluate separation, generation coherence, NO-LEAKAGE, consent, provenance stamp, memory, receipts/claims)):* Step four ('review L0, then L1, then L2') and the new demands on those layers (VISION:392) address layers that are ceremonially FROZEN under a 128-asset manifest whose supersession rule hard-asserts the same 128 ids; the E5/E6/§6.4/§11 learning-loop demands fall under pillar P7, ruled PARKED ('do not work, do not weaken, do not foreclose'); step five's 'bounded execution briefs' names no authority mechanism while two incompatible ones exist (Nirmāṇa full-delegation Execution Prompt with NIRMANA_HOLD kill switch vs CLAUDE.md §C item 0 root CLAUDECODE_BRIEF.md, currently status COMPLETE). The vision's own 'does not reopen or redirect any execution task' is only true if step four yields specs and deferred-register entries, which it never says.

*Evidence:* VISION:558 'review L0, then L1, then L2'; VISION:392 'L0 must expose method scope and exceptions; L1 must make permitted sensitivity computations reproducible; L2 must preserve competing relationships'. NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md:5-14 (NATIVE-RATIFIED), :46-53 (P2/P7 PARKED), :318-321 (deferred register incl. LEL data-ization, outcome intake, multi-chart). NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md:48-63 (full delegation; NIRMANA_HOLD absence = standing authorization; no such file exists in repo or /Users/Dev/nirmana-s/* as of 2026-09-12), :65-83 hard floor, :30-34 'Two previous campaigns died by optimizing the machinery of proof'. NIRMANA_CODEX_HANDOFF_v1_0.md:97-107 (D-NATIVE-14: 'same 128 asset ids (hard-assert)'), :47-62 (L0 40/40, L1 19/19 frozen with W6 transitions; L3 13/23 critical path), :213-216 (fleet stopped). CLAUDECODE_BRIEF.md:1-25 status COMPLETE with documen…

*Also raised by:* C10_contradiction_hunter-09, C5_product_strategy-08

*Verification:*

- textual: **stands** (confidence 0.60) — Partially misreads the text; survives only as an omission/ambiguity, not a contradiction. The document already frames step four as contract work, not asset work: heading "qualify upstream contracts in dependency order" (VISION:558), pipeline "layer/asset contracts → separately authorized execution" (:45), :392 itself says the demands are "cross-cutting responsibilities, not ... new services or assets", frontmatter "n…
- grounding: **stands** (confidence 0.80) — Grounding confirms the factual spine. NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md:5-14 is NATIVE-RATIFIED with "P2 and P7 PARKED"; :46-53 says "do not work, do not weaken, do not foreclose" and routes "LEL data-ization, outcome intake" to the §7.3 deferred register (:318-321, which also lists "multi-chart modalities"). NIRMANA_CODEX_HANDOFF_v1_0.md:104-107 hard-asserts "same 128 asset ids". Execution Prompt :48-63 grants …

*Adopted proposal:* Keep steps four and five; append to step four: "This step produces contract deltas and specifications only. L0, L1 and L2 are frozen under the Nirmāṇa elevation campaign (Unified Plan v2.0, native-ratified) and this review changes no freeze receipt; any demand that would require a new or changed @register writer or a manifest change (D-NATIVE-14) is recorded in the campaign's deferred register, and any learning-loop demand under the PARKED P7 pillar is neither started, weakened nor foreclosed while the campaign is open." Append to step five: "Each brief runs under one named authority (a root CLAUDECODE_BRIEF.md per CLAUDE.md §C item 0, or an explicit native ruling), with may_touch/must_not_touch globs that exclude the Nirmāṇa scope." Add to :392: "None of these demands is executed against a frozen asset outside the sequencing in §13.2 step four."

*Answered in v2.0:* §14; §13 D-16 — adopted.


### F-34 · VERIFIED · CRITICAL · error · v1.1 §7.3, §8 MCP row, §9 durable identity

**§7.3 and the §8 MCP row misdescribe the three request paths and, under one reading, reverse D-05/OT-6**

*Claim (C4_engineering_alignment — engineering and architecture alignment with the real system (three request paths, D-15, density/hardFloor, planner floor as B.11 enforcement, FROZEN orchestrator, build/serve/evaluate separation, generation coherence, NO-LEAKAGE, consent, provenance stamp, memory, receipts/claims)):* (1) 'Direct MCP tools expose the same qualified evidence identities, operators, provenance and limits' is factually imprecise: raw tools are an OAuth-profile projection (full / compact ≤20 / consult safe-default) minus the sensitive class minus every calibration_context_only capability. (2) 'authorized context and evidence portability' and §9's 'durable reading identity' contradict D-05 (cross-channel transcript portability dropped) and the OT-6 lean (MCP durable memory: none; the ledger is the one channel-agnostic memory) unless 'portability' means stable evidence identities, which the vision never defines. (3) 'share investigation and evidence semantics' is stated with no baseline: prashna_ask today is a deterministic pre-fetch plus one non-agentic synthesis call without register-lint/sentinel gates, versus Paripraśna's 8-iteration gated loop — so the row's failure 'Two inconsistent answer authorities' is the current state.

*Evidence:* PTA:780-792 ('Only stages 2, 4 and 7 are common to all three'; raw tools = 'we expose our retrieval plane; someone else's brain uses it'); PTA:793-817 (B.11 unenforceable, D-14 undeliverable, envelope the only defense); PTA:848-855 (engine never branches on door; callable headlessly). PARIPRASHNA_DECISION_REGISTER_v1_0.md:22-35 (D-04, D-05), :49-53 (OT-6 → none). platform-mcp/src/lib/mcp_profile.ts:1-40 (profile gate patches .tool() registration; consult is safe default); platform-mcp/src/lib/sensitive_capability_class.ts:1-35; platform/src/lib/retrieval/registry/types.ts:372-381 (calibration_context_only 'excluded from ALL projections and the prashna_ask tool set'); platform/src/lib/pipeline/no_leakage_filter.ts:1-30. platform/src/lib/pipeline/prashna_ask_synthesis.ts:16-27 ('SINGLE, non-agentic LLM call'; 'DETERMINISTIC pre-fetch'); platform/src/lib/synthesis/agentic_loop.ts:19-27 (MAX…

*Verification:*

- textual: **stands** (confidence 0.70) — Textual check of VISION_v1_1.md:322-326, 379-380, 410, 418. The finding survives only in reduced form. (a) The D-05/OT-6 "reversal" is not in the text: VISION:379 assigns "durable history" to the Portal/Paripraśna row only, and VISION:410 ("durable reading identity") sits in the portal's "After the answer" section; VISION:418's "portable reading" is about sharing a reading with its evidence and limits, not cross-chan…
- grounding: **stands** (confidence 0.80) — Grounding confirms all three legs. (3) VISION:324 says Paripraśna and prashna_ask "should share investigation and evidence semantics" with no baseline, while `platform/src/lib/pipeline/prashna_ask_synthesis.ts:16-27` states prashna_ask is a "DETERMINISTIC pre-fetch" plus "a SINGLE, non-agentic LLM call" versus `agentic_loop.ts:27` MAX_ITERATIONS = 8; R3:80 records register-lint/sentinel gates NOT on its route; R8:35 …

*Adopted proposal:* Adopt the critic's replacement §7.3 and §8 row with two tightenings: (a) define "portability" explicitly as stable evidence identities (fact_id, signal id, build_id, computed_at, provenance stamp) and state that no conversational transcript or memory crosses channels (D-05; OT-6 resolved "none" per DECISION_REGISTER:53); (b) say the calibration-context exclusion is enforced at profile build time (`mcp_surface_profile_builder.ts:205-206`) and the sensitive class at request time, so the projection is "by construction, not by convention". Keep the explicit baseline sentence: prashna_ask today = deterministic pre-fetch + one synthesis call without register-lint/sentinel gates; closing that gap is a named obligation.

*Answered in v2.0:* §7.1 doors table — adopted.


### F-42 · VERIFIED · CRITICAL · gap · v1.1 §4 preamble, §12.1, §13.2, §8 closing

**No wedge and no product sequence; ten co-equal 'cores'; four simultaneous core targets create layer-wide demands against a frozen manifest and three lack their enabling operator**

*Claim (product strategy and prioritization):* The document never states which experience must be undeniably excellent first: §4 makes the six experiences co-equal obligations, §12.1 adds four more items each labelled 'Core target', and §13.2's sequence is a governance process in which the first consumer proof arrives at step five. A team cannot derive a priority order from it.

*Evidence:* VIS:118 ('obligations, not six mandatory screens'), VIS:506-512 (four 'Core target' rows plus horizon/conditional rows), VIS:548-560 (process sequence), VIS:477-479 (three journeys with no order, though VIS:478 calls journey 2 'the user's central L3 expectation'). Readiness makes the choice obvious: L0 40/40, L1 19/19, L2 22/22 frozen vs L3 13/23, L4 0/9, L5 4/15 (NIRMANA_CODEX_HANDOFF_v1_0.md:47-62); kala_convergence/activation/obstruction/darshana/bhavishya at 0 rows for the canonical chart (L3_STRATEGIC_STOCKTAKE_v1_0.md:96-104); ka_sangam gates 24 unfinished assets (ST:150). The structural path is live now: the B.11 floor is compiled in the production Paripraśna route (platform/src/lib/pipeline/compiled_floor_adapter.ts:1-38; PTA:298) and Samīkṣā captures temporal claims at every turn commit (platform/src/lib/pariprashna/pipeline/persistence_stage.ts:56,665-670).

*Also raised by:* C5_product_strategy-07

*Verification:*

- textual: **stands** (confidence 0.80) — Textually the core claim holds. VIS:118 makes the six experiences co-equal "obligations"; §12.1 (VIS:506-509) labels four additions "Core target" with no rank among them; §11.3 (VIS:475) explicitly declines a single wedge ("should include more than one temporal example") and lists three journeys unordered; §13.2 (VIS:550-560) is a governance sequence whose first bounded consumer proof is step five. The document never…
- grounding: **stands** (confidence 0.80) — Grounding checks pass. VISION:118 makes the six experiences co-equal "obligations"; VIS:506-509 label four additions "Core target" with VIS:503 explicitly declining readiness ordering; VIS:548-560 is a governance sequence whose first consumer proof is step five; VIS:477-479 gives three journeys unordered. No wedge is stated anywhere. Repo facts the finding relies on verify: NIRMANA_CODEX_HANDOFF_v1_0.md:47-62 (L0 40/…

*Adopted proposal:* Adopt the critic's §4.0 with two edits: (1) replace "every temporal claim it happens to make is already captured for later evaluation" with "and Samīkṣā capture of temporal claims at turn commit exists in code (persistence_stage) — the wedge's acceptance requires PARIPRASHNA_ENABLED, durable persistence and receipt emission switched ON in the proving deployment, since all three default OFF today"; (2) add "Any addition needing a new build writer enters via the D-NATIVE-14 manifest-amendment ruling (NIRMANA_CODEX_HANDOFF §4.1), never by implication from this document" and correct ka_sangam's downstream count to 25.

*Answered in v2.0:* §1.1 wedge; §14 — adopted.


### F-43 · VERIFIED · CRITICAL · gap · v1.1 §11

**No north-star measure; acceptance criteria cannot be derived**

*Claim (product strategy and prioritization):* §11 declines to assert any number and rejects a weighted composite, but also never defines the metric unit, the gate order, owners or cadence, so its twelve evaluation rows cannot become acceptance criteria. It silently discards the one quantitative gate governance holds (M10's composite threshold) and never cites the retrieval plane's existing hard targets.

*Evidence:* VIS:439 ('No current accuracy percentage… Establish baselines… before setting quantitative improvement targets'), VIS:453-467 (twelve rows, no threshold shape), VIS:469 (rejects weighted score) vs MACRO_PLAN_v2_0.md:492 (composite acharya-grade score gate). RETRIEVAL_STRATEGY_v1_0.md:450-466 already sets ≤10 umbrella calls, ≤2,000-token orientation, ≤25KB median response, ≤3 calls to first verdict, 100% receipt coverage, ≤2-hop drill, ruled as gate criteria (RS-3, :488-489) — never cited by VISION. The document's own best north-star candidate is one row among twelve ('Incremental depth… beyond competent simpler readings', VIS:457) and its unit already exists as the inspectable insight (VIS:348); counting machinery exists but is default-off: AcharyaReadingReceipt (platform/src/lib/pariprashna/receipt/schema.ts:4-25), typed confidence (platform/src/lib/pariprashna/confidence/type_claim.ts:…

*Verification:*

- textual: **stands** (confidence 0.70) — Textually the finding holds. VIS:439 states "No current accuracy percentage, superiority score or delivery date is asserted here"; the §11.2 table (VIS:453-467) gives "what to measure" and "essential control" columns but no unit, threshold shape, order, owner or cadence; VIS:469 rejects a weighted score. `grep RETRIEVAL_STRATEGY` on VISION returns nothing, so RS §7 targets (RS:450-466, ruled gate criteria at RS:488) …
- grounding: **stands** (confidence 0.80) — Evidence verified: VISION_v1_1.md:439 asserts no number; :453-467 gives twelve rows with no unit, threshold shape, order or owner; :469 rejects a weighted score. MACRO_PLAN_v2_0.md:492 does hold a quantitative gate ("acharya-grade composite score at M10 close meets native-approved threshold") which the vision drops silently — though MP:491/§3.7.E (:701, "not averaged") already sit in tension with a composite, so the …

*Adopted proposal:* Insert §11.0 'North star and gates' before §11.1 as the critic drafts (BVD defined on the §7.5 inspectable insight, threshold set from the first W0 baseline run, fabrication count zero, lexicographic gates: safety-boundary violations, fabricated numerics, internal-register leaks, completeness receipt on every planned investigation), with two adjustments: (1) state that the gate list is the §11.2 closing sentence made explicit, i.e. rewrite VIS:469 to "Tracked separately and read in order: gates, then BVD, then the diagnostics. No weighted composite is ever formed." and keep its existing "not compensated by a beautiful answer" clause; (2) add one sentence reconciling with existing governance: "Retrieval-plane gates adopt RETRIEVAL_STRATEGY_v1_0 §7 targets as-is (RS-3). This replaces MACRO_PLAN M10's composite acharya-grade score gate; that replacement is a ratification item, not assumed by this document." Add that ratification item to §14.

*Answered in v2.0:* §11.2 three instruments — adopted.


### F-44 · VERIFIED · CRITICAL · gap · v1.1 §14, §15

**The decisions the native must actually make are hidden; only the easy ones are deferred**

*Claim (product strategy and prioritization):* VIS:595 defers audience, method admissions, language, commercialization, budgets and dates, but the decisions that determine whether component alignment is possible are either made silently (prediction demoted, calibration bands softened, M10 score rejected) or never surfaced (B.4/B.6, MACRO_PLAN v3.0 trigger, UCN parentage, prashna_ask re-base, relation to Nirmāṇa, Q/D freeze, reading re-derivability, provider policy).

*Evidence:* Silent changes: VIS:585 vs MACRO_PLAN_v2_0.md:105 (prediction a co-equal leg); VIS:460 'calibration where justified' vs MACRO_PLAN_v2_0.md:636-643 (bands mandatory); VIS:469 vs MACRO_PLAN_v2_0.md:492. Unsurfaced: PROJECT_ARCHITECTURE_v2_2.md:136-138, 144-146 (B.4/B.6); MACRO_PLAN_v2_0.md:781-782, 797-801 (v3.X trigger); PROJECT_ARCHITECTURE_v2_2.md:304, 316-317 and CLAUDE.md:156 (UCN→UCD); platform/src/lib/pipeline/prashna_ask_synthesis.ts:16-27 (single-pass); L3_KALA_CONSUMER_FIRST_MASTER_PLAN_v1_0.md:477 (W0 freeze of Q/D) vs VIS:208; PTA:1621-1640, 1673-1680 (readings not reproducible); platform/src/lib/models/registry.ts:872-873, 1449-1452 (Gemini-primary, DeepSeek fallback) and CLAUDE.md:407 (Anthropic key unprovisioned).

*Verification:*

- textual: **stands** (confidence 0.70) — Textually the core claim holds but "silent" is overstated in two places. Confirmed in the text: §14 (VIS:582-593) is a recommendation list with no options/alternatives, and VIS:595 defers only audience, method admissions, language, commercialization, budgets, dates. VIS:585 "treat prediction as a major capability within it", VIS:460 "calibration where justified", VIS:469 rejection of a weighted score are all present;…
- grounding: **stands** (confidence 0.82) — Grounding confirms the core claim. VIS:49 asserts the document "does not silently amend the canonical architecture," yet: VIS:585 makes prediction "a major capability within" understanding while MACRO_PLAN_v2_0.md:105 lists calibrated prediction as leg (3) of a three-leg goal; VIS:460 says "calibration where justified" while MP:636-643 states "Outputs without a calibration band attached are not valid outputs"; VIS:46…

*Adopted proposal:* Keep §14's recommendation bullets but append a "§14.1 Decisions requiring explicit ratification" table (ID / Decision / Options / Recommended / Governing source it touches) limited to the decisions the text currently makes without naming their source or omits entirely: D3 governance relation (declare whether this is a MACRO_PLAN §3.10.D v3.x trigger or a subordinate amendment; extend VIS:218's charter-amendment clause to the audience change); D4 prediction's place — cite MACRO_PLAN_v2_0.md:105 co-equal leg and state that VIS:585/491 is a deliberate re-weighting for prose while the ledgered path stays co-equal; D5 calibration — replace VIS:460 "calibration where justified" with "mandatory band on every emitted number, otherwise no number" or explicitly amend MACRO_PLAN §3.5.G; D6 B.4/B.6 — state whether min-three-interpretations/falsifier and 0.00–1.00 confidence still bind (PROJECT_ARCHITECTURE_v2_2.md:136-146); D7 UCN mother-document role (PROJECT_ARCHITECTURE_v2_2.md:304,316-317) — currently unmentioned; D8 prashna_ask — disclose single-pass today (prashna_ask_synthesis.ts:16-27) under VIS:324; D9 Nirmāṇa sequencing (wait for 128/128 vs parallel) — VIS:11/562 already bind gates, …

*Answered in v2.0:* §13 sixteen decisions — adopted.


### F-46 · VERIFIED · CRITICAL · error · v1.1 §1, §11.3, §13.2, §14

**'The user' denotes both the consumer and the native/decision-owner, including in the authorization sentences**

*Claim (writing, structure and clarity):* 'The user' appears 18 times: at 122/126/172/176/344/350/406 it is the consumer, but at 37, 478, 550 and 595 it is the native who commissioned the document (the AI author's 'user'), while 481 says 'the native' and the frontmatter says decision_owner: Native. The sentence that carries the document's authority (595) and the one that assigns the proving journey's expectation (478) will be misread by any aligning agent that resolves 'user' the way the rest of the document does.

*Evidence:* VISION:37 'The user's aspiration for a profound, even spiritually moving experience belongs in the vision'; VISION:478 'Proves the user's central L3 expectation'; VISION:550 'Refine its promise ... with the user'; VISION:595 'The user's request authorizes this stronger strategic pass, not execution of the additions'; VISION:481 'not readings of the native's chart'; VISION:7 'decision_owner: Native'; consumer uses at VISION:122, 126, 172, 176, 344, 350, 406; 'the person' for the consumer at VISION:55, 57, 82, 87, 93, 166, 418. This is the D-14 register-leak class (PTA:259 per grounding/R3_pariprashna_architecture.md:35) applied to the definition itself.

*Verification:*

- textual: **stands** (confidence 0.85) — Text confirms the finding. VISION:37 "The user's aspiration for a profound, even spiritually moving experience", VISION:478 "Proves the user's central L3 expectation", VISION:550 "Refine its promise ... with the user", VISION:595 "The user's request authorizes this stronger strategic pass" all denote the commissioning native, while VISION:481 says "not readings of the native's chart" and frontmatter VISION:7 says "de…
- grounding: **stands** (confidence 0.72) — Factual claims verified: VISION:37, 478, 550, 595 use "the user" for the commissioning owner ("The user's request authorizes this stronger strategic pass", 595; "Refine ... with the user", 550), while 122/172/176/344/350/406 use it for the consumer, and the document itself uses "the native" for Abhisek only at VISION:69 ("the authorized native") and 481 ("the native's chart") with frontmatter `decision_owner: Native`…

*Adopted proposal:* Add a short terminology note (e.g. in §1 or a new §0) fixing three nouns: "the person" = consumer receiving a reading; "the native" = Abhisek Mohanty, subject of the canonical chart and decision owner; "practitioner/researcher" = authorized non-consumer roles. Rewrite VISION:37 -> "The native's aspiration..."; VISION:478 -> "Proves the native's stated central expectation of Kāla without conflating money, activation and relief."; VISION:550 -> "...quality bar with the native."; VISION:595 -> "The native's request authorized this strategic pass, not execution of the additions." Replace every remaining consumer-sense "user/users/user's" (approx. 25 occurrences, including 89, 91, 93, 118, 122, 144, 158, 172, 176, 308, 344, 350, 358, 381, 406, 418, 429, 465, 467, 506, 508, 576) with "the person/people". At VISION:587 replace "across users and managed channels" with "across the web (Paripraśna) and managed-MCP channels" to remove the third, channel-sense use.

*Answered in v2.0:* 'the person' / 'the native' throughout — adopted.


### F-51 · VERIFIED · CRITICAL · gap · v1.1 §3 table, §8 L1/L2/L3/registry rows

**The five mechanisms that could deliver 'not seen on first pass' are not named specifically enough to build or test**

*Claim (C8_beyond_acharya_adversary — adversary of the "beyond-Acharya" claim: Barnum effect, complexity theatre, false precision, averaging incompatible schools, LLM fluency as judgment, unvalidatable structural claims, dependence on unproven classical rules; then rebuild the claim at exactly the strength that can be tested.):* §3 names qualities and §8 names components, but neither specifies joint-pattern enumeration across vargas × daśā × gochara × aṣṭakavarga with exceptions and cancellations, a typed contradiction register, a concordance/discordance map, longitudinal frozen-claim memory, or calibration cells as buildable, testable mechanisms; each is absent, partial or lossy in code today and the vision does not say which.

*Evidence:* VIS:102 'connected without losing their identities' (no mechanism). Cancellation logic exists for one yoga: platform/python-sidecar/ga_writers/ga_yoga_writer.py:19-21 'currently Neecha Bhanga Raja Yoga (5 classical rules…). All other yogas keep the honest NULL floor'; near-miss band unbuilt: platform/src/lib/retrieval/registry/layers/register_d9_judgment.ts:41-44 'That column does not exist yet on any canonical chart. bhanga_checked … is honestly false'. Contradiction register is one class: writers/bo_karanajala.py:18-20 'A yoga signal and a dosha signal share the same domain AND same graha → yoga_vs_dosha'. Upstream depth flattened (re-verified via grounding R6): ga_strength_writer.py:1031 emits sign-keyed AV while services/ka_kshetra/stage1_symbolization.py:336-344 serves it as not_in_corpus; pyjhora_adapter/strength.py:209 discards _prastara; writers/ka_sangam.py:333 keeps domains_aff…

*Verification:*

- textual: **stands** (confidence 0.68) — Textually the gap is real but overstated. Searched the whole document: "concordance", "contradiction register", "joint", "enumerat", "minimum-n", "calibration cell", "not_testable" occur nowhere (grep over VISION_v1_1.md). §3 (VIS:99-110) lists dimensions only; §8 L1/L2/L3/registry rows (VIS:369-371,376) list qualities ("divisions, relationships, conditions", "tensions and alternatives", "graph/interval traversal") w…
- grounding: **stands** (confidence 0.78) — Evidence verified in repo: ga_yoga_writer.py:19-21 ("currently Neecha Bhanga Raja Yoga … All other yogas keep the honest NULL floor"); register_d9_judgment.ts:41-44 ("That column does not exist yet on any canonical chart. bhanga_checked … honestly false"); bo_karanajala.py:18-20 (only 'yoga_vs_dosha' same domain+graha); bo_sangati.py:125-136 stores a scalar concordance_score; R6:38-39 confirms ka_sangam.py:333 domain…

*Adopted proposal:* In §3, after the table, add one paragraph: "The beyond-working-memory claim rests on five named mechanism families, each to be declared built/partial/absent in the elevation plan (§13.2) before any §3 dimension is scored: (1) joint-pattern enumeration of each fired or near-fired configuration across computed vargas, daśā-lord eligibility, gochara contacts and aṣṭakavarga gating, with cancellation/exception state and explicit not_computed; (2) a typed contradiction register with two fact-linked poles and more than one class (rule-vs-rule, tradition-vs-tradition, varga-vs-rāśi, daśā-vs-gochara); (3) a per-question-class × tradition concordance/discordance map recording verdict, jurisdiction, facts used and divergence premise, where agreement counts as independent only on disjoint facts; (4) claim-level diff between two stamped readings attributing each change to input, evidence, build, priors or model (extends §12.1 'claim-level diffs' and §8 L5); (5) calibration cells (technique × ayanāṃśa × question class) with a minimum-n gate below which a claim carries calibration: none." In §11.2 change "calibration where justified" to "calibration only from cells above a declared minimum n" an…

*Answered in v2.0:* §3.2 mechanism table — adopted.


### F-52 · VERIFIED · CRITICAL · contradiction · v1.1 §3 discovery row, §6.3–6.4, §8 living-atlas row

**The served discovery surface already asserts what §3 says does not qualify, and the vision does not name it as something to supersede**

*Claim (C8_beyond_acharya_adversary — adversary of the "beyond-Acharya" claim: Barnum effect, complexity theatre, false precision, averaging incompatible schools, LLM fluency as judgment, unvalidatable structural claims, dependence on unproven classical rules; then rebuild the claim at exactly the strength that can be tested.):* VIS:105 excludes graph centrality and rarity alone and VIS:255 requires candidate → examination → rival testing → independent review; the live L2 discovery writer is exactly centrality/outlier/anomaly heuristics and emits, into a served column, a template sentence claiming why an acharya would miss the pattern, an invented confidence, a boilerplate falsifier and a rank boosted by counting its own correlated primitives as corroboration. Because §3 is silent on current state, alignment will treat this as an implementation of Discovery rather than a candidate generator to be demoted under §N.8.

*Evidence:* platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py:6-8 'the insight no acharya can hold'; :10-15 four primitives (non-obviousness, embedding outliers, Nσ anomalies, brokers); :497 why_misses=f"Low surface salience ({…}) masks high structural consequence ({…}); falls below acharya's attentional threshold"; :408-410 "confidence": round(min(consequence + 0.1, 1.0), 3); :419-421 boilerplate falsifier 'Compare against L3 Kāla LEL event outcomes for predicted domain'; :391-392 rank_composite = rank * (1.0 + corr_count * 0.2) over the writer's own primitives; :423 novelty_class hardcoded 'instance_of_known_class'. Served to every LLM: platform/src/lib/retrieval/registry/layers/L2_bodha/query_discoveries.ts:44, 59. CLAUDE.md §N.8: a signal without a detector 'is null, not green' — there is no acharya-miss detector.

*Verification:*

- textual: **stands** (confidence 0.70) — Textually the finding is accurate on the omission: a whole-document grep for "bodha_discoveries", "anveshana", "heuristic", "candidate generator" or any current-state statement about discovery returns nothing. The only discovery-current-state language is generic: VIS:47 "Existing assets and layer plans supply evidence... They do not define the ceiling", VIS:251 "A surprising correlation remains a candidate", VIS:255 …
- grounding: **stands** (confidence 0.85) — Code claims verified verbatim: bo_anveshana.py:6-8 ("the insight no acharya can hold"), :10-15 four heuristic primitives, :391-392 `rank_composite = rank * (1.0 + corr_count * 0.2)` over the writer's own `corroborating_methods`, :408-410 `"confidence": round(min(consequence + 0.1, 1.0), 3)` plus hardcoded `"ayanamsha_fragility": "low"`, :419-421 boilerplate falsifier, :423 `novelty_class` fixed to "instance_of_known_…

*Adopted proposal:* §3 Discovery row, "What does not qualify" cell: "Novel-sounding prose, graph centrality, embedding outliers, distributional anomalies or rarity alone — including any existing build-time discovery or salience primitives, which are candidate generators, not findings." After VIS:114 add one paragraph, kept scope-consistent with VIS:10: "Existing served discovery, salience or 'why an expert would miss this' fields are treated as candidates under §6.4 until a real detector or independent review exists; under the earned-signal principle [S1] their confidence, falsifier and reviewer-miss text are served as null or relabelled hypothesis, never as measurements. The specific audit of each such surface belongs to component alignment after ratification (§10)." Add to the §8 "Living atlas and question compass" failure cell: "or existing heuristic outputs relabelled as discoveries."

*Answered in v2.0:* §13 D-12 (discovery surface relabelled as candidates) — adopted.


### F-58 · VERIFIED · CRITICAL · gap · v1.1 §2.1, §8 subject/security rows

**Only 'the consumer' is a defined persona; six personas the system already serves are assumed or absent**

*Claim (completeness):* §2.1 names only 'the authorized native', 'consenting people' and 'authorized practitioners and researchers' (V:69) plus 'the integrating client' (V:326); it never enumerates personas or states per persona what they may do, must consent to, and are owed. The native-as-operator/super-admin, the consenting guest (PTA D-09), the practitioner entering a third party's chart, the acharya reviewer (MP §3.5.B/§3.7), the post-M10 public consumer (whose MP tier is redacted/aggregated, not E1-E6), and the excluded (minors <18, consent-incapable, MP §3.5.F) are absent, so consent, entitlement, safety sign-off, LEL intake and build-rights alignment have no reference.

*Evidence:* V:69-71 are the only audience sentences. PTA:585-591 (guest sees 'No cockpit, no observatory, no admin, no other charts'); PTA:876-884 (raw tools = practitioner surface). MP:599-606 (four audiences; public consumer 'Redacted; aggregated … no individual-fate-adjacent claims'); MP:632 (minors excluded absolutely; excluded-subject register); MP:685-701 (acharya pool n>=3, independence, verdicts not averaged). Operator-only acts in code: platform/src/app/api/lel/route.ts:8-23 (super_admin); platform/src/app/api/pariprashna/safety/review/route.ts:36-44 ('MP §3.5.C requires the sign-off to be an explicit native sign-off', super-admin). Consent inert: platform/src/lib/pariprashna/consent/index.ts:4-9 (SUBJECT_CONSENT_ENFORCEMENT default OFF); consent/minor_exclusion.ts:98; consent/register.ts:4. platform/migrations/001_baseline.sql charts.role CHECK IN ('native','tertiary','fixture'). R2 §4 con…

*Verification:*

- textual: **stands** (confidence 0.80) — Textually the finding is accurate. §2.1 is two paragraphs (VISION_v1_1.md:69-71); the only audience nouns are "the authorized native", "consenting people with varied astrological knowledge", "authorized practitioners and researchers", plus "the integrating client" at :326. A whole-document grep for guest, minor, operator, super-admin, sign-off, reviewer-as-persona, excluded, crisis returns nothing persona-shaped: :45…
- grounding: **stands** (confidence 0.82) — Finding survives grounding. VISION_v1_1.md:69-71 is indeed the only audience text ("authorized native… consenting people… authorized practitioners and researchers"); no persona, entitlement, consent or exclusion row exists anywhere else (grep of consent/minor/guest/practitioner/operator yields only V:11 deferral, V:374/384 responsibility rows, V:431). Governance the vision omits is binding via CLAUDE.md §A: MACRO_PLA…

*Adopted proposal:* Keep V:69-71 but insert between them a short persona enumeration that cites governance by reference rather than restating policy: (1) Native as subject; (2) Native as operator — chart create/rebuild, prediction confirmation, outcome adjudication, MP §3.5.C health-crisis sign-off, LEL curation, consent/exclusion administration — performed on an operator surface, logged, never by the model; (3) Consenting subject/guest — own chart only, no other charts or admin (PTA D-09); (4) Practitioner as intermediary — subject consent artifact required before interpretive output (a horizon persona until consent enforcement is on); (5) Acharya reviewer — blind review under MP §3.7; (6) Researcher — §6.5 operators under separate authority; (7) Integrating AI client — §7.3 limits. State explicitly that the post-validation public consumer is not a persona of this definition (MP §3.5.B redacted/aggregated tier; personalized public service is a scope-redefining event per MP §3.10.D) and that minors under 18 and persons unable to consent or in crisis are excluded from interpretive output (MP §3.5.F), with exclusion logged. Retain V:71 unchanged as the closing sentence; add "audience/consent policy rema…

*Answered in v2.0:* §2.1 rings table — adopted.


### F-59 · VERIFIED · CRITICAL · contradiction · v1.1 §8 portal row; missing row

**Operator instrument (build cockpit, Nirmāṇa tracker, review/sign-off/intake) has no §8 row; the portal row's failure column condemns the console the native runs daily**

*Claim (completeness):* §8 has eighteen rows but none for the operator's instrument; the only portal row is consumer-shaped and names 'A dashboard or diagnostics console substitutes for understanding' as its invalidating failure. Read literally, that condemns the 14 /cockpit/* pages, 10 observatory pages, /admin/tracker, the per-chart Nirmāṇa build cockpit, Pratikruti's five learning loops, the Samīkṣā review tab and the file-based campaign tracker - the surfaces through which every build, freeze, confirmation, outcome resolution, LEL entry, calibration co-sign and health-crisis release actually happens. The 'Orchestration…' row covers mechanism, not the human surface driving it.

*Evidence:* V:379. Portal inventory (find platform/src/app -name page.tsx): /cockpit/{activity,atlas,command-center,health,interventions,parallel,plan,registry,sessions}, /(super-admin)/observatory/*, /admin/{foundation,mcp/health,mcp/keys,tracker,trace}, /clients/[id]/{nirmana,pratikruti,samiksha,edit,cockpit}, /clients/new. platform/src/app/admin/tracker/page.tsx:1-11 ('Build orchestrator status page for super_admin … per-chart, per-ayanamsha build matrix'); platform/src/app/clients/[id]/nirmana/page.tsx:1-4 (BuildControlsBar, AssetTable); platform/src/app/clients/[id]/pratikruti/page.tsx:1-9 (five loops 'for the native'); 00_ARCHITECTURE/control/nirmana_tracker_generate.py:1-20 (campaign tracker, PASS/FAIL/NOT-MEASURABLE/BLOCKED kept distinct). PTA:585-591 (guests see no cockpit); PTA:375 OT-4 (rebuild 'destroys the prior build irrecoverably … its failure modes land on the operator'). R8 §5 fact …

*Verification:*

- textual: **stands** (confidence 0.72) — Textually the core omission is confirmed: the §8 table (VISION_v1_1.md:369-388) has no row for build/freeze cockpit, campaign tracker, review/confirmation, LEL intake or sign-off surfaces; grep for "operator|cockpit|tracker|console|confirm|promot|sign-off|co-sign" finds no human-sign-off mechanism anywhere in the document (only V:375 "human adjudication where necessary" for corpus, V:381 user-side "review and export"…
- grounding: **stands** (confidence 0.70) — Evidence checks out: the operator surfaces exist exactly as cited (find platform/src/app -name page.tsx: 14 /cockpit/*, 10 /(super-admin)/observatory/*, /admin/{tracker,foundation,mcp/*,trace}, /clients/[id]/{nirmana,pratikruti,samiksha,cockpit,edit}); platform/src/app/admin/tracker/page.tsx:1-11 and clients/[id]/pratikruti/page.tsx:1-9 headers match the critic's quotes. Governance makes these human acts load-bearing…

*Adopted proposal:* (a) At V:379, qualify the failure cell minimally: "In the consumer surface, a dashboard or diagnostics console substitutes for understanding (operator surfaces are covered by the row below)." (b) Insert after the Portal row: | Operator and steward instrument (build/freeze cockpit, campaign and asset tracker, review, confirmation, intake and sign-off surfaces) | "The people who keep this instrument honest can see what is built, stale, blocked or waiting on a human, and act without the model acting for them." | Build and freeze state per chart, asset and generation with pass/fail/not-measurable/blocked kept distinct; human-only prediction confirmation, outcome resolution and dismissal with reason; life-event intake; consent and exclusion administration; sensitive-release as a separate human act; cost and quality observability; every operator act attributed. | Operator surfaces are mistaken for consumer surfaces or dropped as "diagnostics"; an automated caller performs a human sign-off; build state is inferred from row counts rather than the receipt chain. | (c) Add one sentence after V:388 noting this row does not supersede campaign authority per the frontmatter does_not_supersede cl…

*Answered in v2.0:* §8 operator instrument row — adopted.


### F-66 · VERIFIED · CRITICAL · contradiction · v1.1 frontmatter, §1.1, §5.1, §11.2, §14

**Frontmatter disclaims superseding governance while the body amends the mission, the M10 gate, the natal thesis and the subject scope**

*Claim (internal and governance contradiction hunter):* The frontmatter says the document supersedes no canonical governance and §1.1 says it does not 'silently' amend the architecture, yet the body re-weights a governed mission leg (prediction becomes 'a major capability within' understanding), rejects the M10 composite-score gate, replaces the natal-centred thesis with a 'method-native and question-led' architecture, and extends the subject to 'consenting people'. Under MACRO_PLAN's own version semantics these are v3.X scope-redefining events, and the document never names the clauses it proposes to amend or the version trigger, so a reader aligning every component cannot tell which authority wins where.

*Evidence:* VIS:11 'does_not_supersede: Canonical governance, audience/consent policy, campaign authority...'; VIS:49 'does not silently amend the canonical architecture'; VIS:585 'treat prediction as a major capability within it' vs MP:105 / CLAUDE.md:109 three co-equal legs incl. 'time-indexed, probabilistic, calibrated predictions'; VIS:469 rejects a weighted score vs MP:492 'acharya-grade composite score at M10 close meets native-approved threshold'; VIS:218 'method-native and question-led' vs PA:59-61 thesis 'centered on the natal chart of Abhisek Mohanty'; VIS:69 'consenting people'. MP:799-801 'v3.X scope-redefining — new primary subject; ... commercialization; project-purpose change. Ambiguity resolves upward'; MP:768 'commercialization path' triggers MP v3.0; PA:112 last refresh recorded itself as 'a minor bump, not a v3.0 rewrite'. Real contradiction.

*Verification:*

- textual: **stands** (confidence 0.70) — Text check: VIS:11 and VIS:49 read as the critic quotes them. VIS:585 does say "treat prediction as a major capability within it", VIS:469 rejects "A weighted 'beyond-Acharya score'", VIS:218 says "The proposed architecture is method-native and question-led", VIS:69 targets "consenting people". Grep for "supersede|amend|MACRO_PLAN|PROJECT_ARCHITECTURE|v3" finds no clause list or version trigger anywhere; S1/S2 (VIS:6…
- grounding: **stands** (confidence 0.82) — Every citation checks out. VIS:11 `does_not_supersede: Canonical governance…`; VIS:49 "does not silently amend"; VIS:585 "treat prediction as a major capability within it"; VIS:469 rejects a weighted score; VIS:218 "method-native and question-led"; VIS:69 "consenting people". Governance side: MACRO_PLAN_v2_0.md:105 states the three-part goal incl. "(3) makes time-indexed, probabilistic, calibrated predictions"; MP:49…

*Adopted proposal:* Frontmatter, add:
proposes_amendments_to:
  - MACRO_PLAN_v2_0 §Ultimate goal (MP:105): the three mission obligations delivered as earned understanding — see §0; prediction is not demoted
  - MACRO_PLAN_v2_0 M10 quality gate (MP:492): composite score replaced by separately tracked dimension gates — see §11.2
  - MACRO_PLAN_v2_0 §3.5.G / §3.5.A.1: "calibration where justified" (VIS:460) reconciled with the mandatory calibration band — see §7.6
governance_relation: Ratification opens a MACRO_PLAN v3.0 revision spec (MP §3.9.E / §3.10.D — consumer/commercial scope is v3.X; ambiguity resolves upward) and a PROJECT_ARCHITECTURE amendment for §5.1 inquiry families. Until ratified per MP §3.10.C, every canonical clause governs as written.

Add §0 "Governance relation" before §1 (critic's text, retaining the sentence that the mission remains three co-equal obligations delivered in the form of earned understanding), and cross-reference the existing deferrals at §2.1, §5.1 and §14 so a reader finds all amendment points in one place.

§14 bullet 2: "Deliver all three mission obligations — reading, pattern surfacing and calibrated prediction — in the form of earned, personally specific understa…

*Answered in v2.0:* frontmatter supersedes_if_ratified; §13 — adopted.


### F-04 · VERIFIED · MAJOR · gap · v1.1 §5 P05/P14, §8 subject row, §10

**Consent for related subjects, family charts and minors unaddressed (§3.5.F absent; a family chart exists)**

*Claim (ethics, safety, consent and cultural responsibility):* The vision never says who may create a chart for whom, what happens to a chart whose subject has not consented, that minors are served only to a named guardian and never enter research, that relationship/compatibility readings require the second subject's consent, or that vulnerable subjects are excluded and logged. Abhinandan Mohanty's chart (1c826d5a) is a non-native subject with full L1→L5 output already produced; the consent schema that would govern it is built but flag-OFF and chart creation is ungated.

*Evidence:* V:190 'no unsupported claims about another person's thoughts'; V:199 'Explicit permission and method applicability'; V:374 'Identity, permissions, consent'; V:431. MP §3.5.A.4 (MACRO_PLAN_v2_0.md:595), §3.5.D (:617–622), §3.5.F minors <18 excluded absolutely, excluded-subject register (:632), M7 'no public figures without consent' (:440). Migration header: 'the native (or any entitled user) creates a chart for a non-consenting adult — spouse, colleague, public figure — and reads them without their knowledge … today entirely undefended: chart creation is ungated and MACRO_PLAN §3.5.A.4 is unenforced' (platform/supabase/migrations/575_pariprashna_chart_subject_consent.sql:5–11); strict native_self + guardian_principal_id carve-out 'a minor chart serves ONLY to this principal, and NEVER enters a cohort' (:30–40). platform/src/lib/pariprashna/consent/index.ts:4–9 (inert until flag ON); minor…

*Verification:*

- textual: **stands** (confidence 0.85) — Textual re-read of VISION_v1_1.md (609 lines) against each sub-claim, plus a whole-document term search.

WHAT THE DOCUMENT ACTUALLY SAYS ON CONSENT (exhaustive): V:11 frontmatter `does_not_supersede: … audience/consent policy`; V:61 "Personal data does not automatically move into that research programme; permission and study design are part of its legitimacy"; V:69 "reusable for consenting people … Expanding audienc…
- grounding: **stands** (confidence 0.86) — GOVERNANCE CHECK — the finding restates settled, binding rules, it does not contradict them. MP §3.5.A.4 "Any M7 cohort subject requires explicit informed consent before any L2+ output is produced about them" (MACRO_PLAN_v2_0.md:595); §3.5.D written consent/withdrawal/verified deletion/default-anonymous/minor exclusion (:617–622); §3.5.F minors <18 excluded absolutely, active crisis/cognitive impairment excluded, exc…
- materiality: **stands** (confidence 0.80) — MATERIALITY VERDICT: the finding survives — the gap is material for a definition every component will align to — but the proposed text must be revised because two of its clauses would make the definition LESS honest, not more.

WHY IT IS MATERIAL (not refuted):
1. The vision's deferral is insufficient for the scope the vision itself introduces. Frontmatter defers consent policy ("does_not_supersede: … audience/consen…

*Adopted proposal:* Claim wording (tighten): "The vision establishes that caller authorization is distinct from subject consent (V:384) and that relationship readings are between 'authorized subjects' with 'explicit permission' (V:199, V:212), but it never states who may create a chart for whom, what state results when a subject has not consented, whose permission a relationship reading needs and how a one-consent reading is bounded, that minors are served only to a named guardian and never enter research, or that vulnerable subjects are excluded and logged; it defers to an 'audience/consent policy' (V:11) it never names or cites."

Text change (three edits, not one):
(a) Add to §2.1 after V:69, or as a preamble paragraph to §10 before the bullet list: "Subjects and consent. A chart is read only for a subject who is the account holder (strict native_self), a consented adult whose consent record names method, retention, withdrawal and deletion, or a minor served solely to a named guardian and never admitted to research or cohorts. A chart created for a non-consenting adult — spouse, colleague, public figure — reaches a designed refusal state, not an error. A relationship or compatibility reading requir…

*Answered in v2.0:* §2.1, §10 B-7 — adopted.


### F-05 · VERIFIED · MAJOR · gap · v1.1 §9 long-term, §8 L5/personal-history rows

**Deletion vs protected historical integrity left to a future author; governance already resolves it**

*Claim (internal and governance contradiction hunter):* The one sentence every retention, consent and ledger component will be aligned to is an unresolved instruction ('Reconcile ... do not promise both unconditional erasure and universal immutability'), framed as a trade-off. MACRO_PLAN already resolves it orthogonally — §3.5.D grants subjects verified deletion, §3.5.E forbids revision-in-place of frozen claims and windows — and reality shows immutability is ledger-specific (mi_bhavisya deletes pending/due predictions on rebuild; only the Samīkṣā ledger has a DB freeze trigger). Left as written, the rewrite is invited to weaken subject deletion, the one direction MP forbids.

*Evidence:* VIS:420 'Reconcile protected historical integrity with explicit retention/deletion policy; do not promise both unconditional erasure and universal immutability.' MP:620 'right to withdraw and to request deletion of their L2+ corpus; withdrawal is logged, deletion is verified'; MP:626-628 'the verification window is fixed at emission and never modifiable. Native cannot revise a prediction after outcome is known'; PA:255 'L1 is append-only by default. Corrections produce new versions'; PTA:263 D-16 stamp 'copied, never referenced, into every ledger row'; platform/supabase/migrations/470_pariprashna_samiksha_prediction_ledger.sql:41,201-202 trg_bmpl_freeze_confirmed; platform/python-sidecar/pipeline/orchestrator/writers/mi_bhavisya.py:215-223 deletes lifecycle_status IN ('pending','due') on rebuild; SRC:265 immutability 'a target requiring ledger-specific proof, not a universal existing gua…

*Also raised by:* C7_ethics_safety_culture-04

*Verification:*

- textual: **stands** (confidence 0.80) — CONFIRMED on the textual lens, with two corrections that lower severity.

What the document actually says: VIS:420 reads verbatim "Reconcile protected historical integrity with explicit retention/deletion policy; do not promise both unconditional erasure and universal immutability." It is an instruction to a future author, not a rule. The preceding sentence ("Remembering a preference, preserving a reading, recording …
- grounding: **stands** (confidence 0.85) — GROUNDING VERDICT: the finding's core survives; its proposed replacement text needs correction.

Every cited fact verifies against the repo at badc3f9bc:
- VIS:420 is verbatim: "Reconcile protected historical integrity with explicit retention/deletion policy; do not promise both unconditional erasure and universal immutability." It is an imperative, not a rule; VIS:384 lists "deletion/retention policy" as a control w…
- materiality: **stands** (confidence 0.70) — DIAGNOSIS SURVIVES (material, not stylistic). VIS:420 reads "Reconcile protected historical integrity with explicit retention/deletion policy; do not promise both unconditional erasure and universal immutability" — an instruction to a future author, in the one section every retention/consent/ledger component will be aligned to. The vision never states deletion as a subject right and never cites MP §3.5: grep of VISIO…

*Adopted proposal:* Replace the third sentence of VIS:420 ("Reconcile protected historical integrity ... universal immutability.") with:

"Immutability and deletion are different operations governed by different rules, and this document changes neither (see frontmatter `does_not_supersede`). Immutability forbids revision in place: a frozen claim, its verification window, its provenance stamp and its recorded outcome are never edited after emission (MACRO_PLAN §3.5.E); today this is database-enforced only on the Samīkṣā ledger, and every other ledger must prove its own freeze before it is described as immutable. Deletion is a subject right (MACRO_PLAN §3.5.D): on withdrawal the subject's L2+ corpus — readings, derived summaries, recall vectors, exports and caches included — is removed, the removal is verified by re-count, and a dispute over the scope of deletion pauses destruction and opens a disagreement-register entry rather than deciding it. What may survive a verified deletion is today a content-free receipt (row count and content hash, no subject-identifying content). Whether an anonymized evaluation record (claim hash, window, outcome class, model version) may also survive so that calibration his…

*Answered in v2.0:* §9 year three, §12 table, §13 D-5 — adopted; rule stated.


### F-06 · VERIFIED · MAJOR · gap · v1.1 §1.2, §2.1, §8 security row

**The native as proving subject — self-experimentation, an intimate life record in a hosted repo, provider data flows — nowhere addressed**

*Claim (ethics, safety, consent and cultural responsibility):* The vision writes as if a consenting population exists; today the only real subject is the author, whose LEL (57 events incl. health/psychological/loss under J.3 'no privacy boundaries') is committed in a repository with a GitHub remote, whose chart facts, signals and conversation prose leave to Gemini (default), OpenAI, DeepSeek and NVIDIA endpoints under a provider posture governance calls 'currently UNSTATED anywhere', and who is simultaneously subject, operator, sole adjudicator of outcomes and the person who releases sealed health readings. §10 bullet 6 protects others' data; the native's own posture and the provider posture are not product obligations.

*Evidence:* V:61 'Personal data does not automatically move into that research programme'; V:69; V:384 'provider/data handling'; V:431. PA J.3 (PROJECT_ARCHITECTURE_v2_2.md:964–971: 'health (physical and mental), relationships, family, finances, failures, losses, addictions … shame/pride episodes'). LEL in repo: 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md:1–23 (57 events); git remote origin github.com/Marsys-Technologies/Madhav. Provider posture: SAFETY_PRIVACY_TENANCY_v0_1_PROPOSAL.md:164–175 ('currently UNSTATED anywhere … chart facts, signal text, conversation history, summaries — C1/C2 — to Gemini (default), OpenAI-class, DeepSeek, NVIDIA'); platform/src/lib/models/registry.ts:872 DEFAULT_STACK_ID = 'gemini'; platform/src/lib/providers/{anthropic,deepseek,google,nvidia,openai}; NCD-6 'document now, strict allowlist on first cohort subject' (PARIPRASHNA_DECISION_REGISTER_v1_0.md:64); PPR-25 (PARIPRASHN…

*Verification:*

- textual: **stands** (confidence 0.78) — TEXTUAL-ACCURACY VERDICT: the finding survives, but only on a narrowed core; two of its four sub-claims misread the document.

REFUTED sub-claim 1 — "writes as if a consenting population exists" / "the 'consenting people' framing hides that the only real subject today is the author". The document says the opposite, explicitly: VISION_v1_1.md:69 "The immediate proving context remains the authorized native and existing…
- grounding: **stands** (confidence 0.72) — GROUNDING VERDICT: the core gap survives, but three of the finding's evidence claims are wrong or stale, one is materially understated, and the proposed change's most concrete new obligation contradicts both the actual system and two resolved native decisions. Severity should drop from major to minor and the proposal must be rewritten.

CONFIRMED (file:line):
- PA J.3 text as quoted: `00_ARCHITECTURE/PROJECT_ARCHITEC…
- materiality: **stands** (confidence 0.80) — MATERIALITY VERDICT: the finding survives, with corrections to its claim and a tightened proposal.

Attempted refutation and why it fails:
(1) "The vision already covers it." V:69 does say "The immediate proving context remains the authorized native and existing permitted use," and V:595 defers audience expansion, so the critic's "writes as if a consumer population already exists" is overstated. But that clause only …

*Adopted proposal:* Narrowed fix in three places (do not add the critic's first sentence — V:69 already states the native is the immediate proving context and that expansion needs separate policy):

1. Amend §2.1 V:69, appending after "existing permitted use": "The native's standing self-consent is recorded as a consent record like any other subject's (strict native_self) and is not an exemption from the consent controls in §8; the native's J.3 redaction right is exercised as a flagged edit, not a silent deletion."

2. Add one bullet to §10 (after V:433, which already covers the memorable-event bias — do not restate it): "Where the proving subject is also the operator and the person who resolves outcomes, that conflict is recorded on every claim resolution it touches; held-out events already separated under §6.4/§11.2 are never re-adjudicated by the subject; and any calibration or accuracy figure derived from a single subject carries a single-subject (n=1) qualification verbatim wherever it is shown. ND.2's interstitial for the native's own sensitive readings is a personal choice of an informed subject, not a template for any other chart."

3. Sharpen the §8 security row (V:384) column "What it must p…

*Answered in v2.0:* §2.1 (ring 0 obligation), §10 B-15 — adopted.


### F-08 · VERIFIED · MAJOR · weakness · v1.1 E4, §10, §12.2, §8 L4 row, missing §8 row

**Remedy/upāya line stops short of the settled attributive-register rule; commerce, unsolicited prescription and cost unaddressed; upāya ethics and muhūrta strictness not stated as doctrine**

*Claim (ethics, safety, consent and cultural responsibility):* The vision says practices are 'not sold as guaranteed causal interventions' and 'decline guarantees and sales pressure' but never states the settled line — 'the tradition prescribes X' vs 'you should do X' — nor that remedies are never volunteered, never ranked by price or product, never linked to a vendor or commission, never a condition of a reading, and never offered for a mortality/crisis question. Meanwhile the build layer computes 1–3 prescriptions per graha for every chart unasked, the corpus carries cost tiers and gemstone rows, and the imperative-voice detector is telemetry-only behind a flag defaulting OFF.

*Evidence:* V:154 'not sold as guaranteed causal interventions'; V:430 'Do not coerce practice, spending, disclosure or dependence'; V:527. PTA §13.8 (PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md:2507–2534): 'the tradition prescribes X versus you should do X … where an astrology product becomes exploitative'; citation gate platform/src/lib/synthesis/citation_check.ts:91, 129 (PRESCRIPTIVE_CLASSES, hard-fail zero-citation). Imperative detector: platform/src/lib/pariprashna/voice/voice_lint.ts:16–27 ('TELEMETRY ONLY (never rewrites reader prose)'); feature_flags.ts:575 PARIPRASHNA_VOICE_ENFORCEMENT_ENABLED: false. Corpus cost tiers and gemstones: platform/python-sidecar/brahmagyan/l0_remedy_corpus.py:19, 266–288. Unasked build-time prescriptions: platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py:1–25; resonance score collapses to weakness score: BA_FULL_ASSET_AUDIT_REGISTER_v1_0.md:378. Mor…

*Also raised by:* C2_jyotish_acharya-07, C9_completeness_critic-09

*Verification:*

- textual: **stands** (confidence 0.88) — TEXTUAL ACCURACY VERDICT: the finding correctly quotes what VISION_v1_1 says and correctly identifies what it omits; the omissions are not covered elsewhere in the document. I tried to refute on three fronts and could not.

1. What the document actually says about practices/remedies (exhaustive; grep for remed|upāya|practice|gem|ritual|sell|sold|sale|commerc|price|cost|vendor|prescri|spending|mortality|crisis over al…
- grounding: **stands** (confidence 0.86) — Verdict: the finding SURVIVES grounding. Every load-bearing repo/governance claim checks out, the "settled" register rule is in fact stronger than the critic cited, and the proposed change does not collide with CLAUDE.md principles — but the proposal needs three corrections (status accuracy under §N.8, a dropped clause, and anchoring "crisis" to §3.5.C), and two of the merged 'also' sub-claims overstate the code.

VE…
- materiality: **stands** (confidence 0.85) — Under the materiality lens the finding survives; I could not refute it. (1) The vision is weaker than the binding architecture it will govern: PARIPRASHNA_ARCHITECTURE_v1_0.md:149 (PPR-04, CURRENT) already requires "remedies attributive ('the tradition prescribes'), never imperative", yet VISION_v1_1 never states the register rule — V:154 says only "not sold as guaranteed causal interventions", V:430 "Do not coerce p…

*Adopted proposal:* (a) §10 bullet 5 (V:430) — keep the first sentence, replace the second: "Do not coerce practice, spending, disclosure or dependence. Traditional practices are voiced in the tradition's register — 'the text prescribes', never 'you should' — with their source, intent, burden and cost stated and the honest statement that efficacy is not established. Madhav does not volunteer a practice the person did not ask about (remedial computations made at build time are evidence for an asked question, not a feed), does not rank practices by price or product, and — whatever commercial model is later decided (§14) — never sells, links to, or earns from a gemstone, ritual, service or practitioner. A practice is never a condition of a reading or of a better answer, and none is offered for a mortality or crisis question."

(b) E4 (V:154) — append one sentence: "Election applies the act-specific vetoes and their classical cancellations before ranking the surviving intervals, and a strengthening practice is checked against this chart's functional malefics and māraka lords before it is mentioned; a practice is matched to the afflicted mechanism in this chart, not to a planet's name."

(c) §8 — insert a …

*Answered in v2.0:* E4, §8 remedies row, §10 B-11 — adopted.


### F-09 · VERIFIED · MAJOR · weakness · v1.1 §1, §2.3, E1, §9

**'Spiritually moving' aspiration and living portrait lack emotional-register obligations and a non-dependence rule**

*Claim (ethics, safety, consent and cultural responsibility):* The vision endorses 'a profound, even spiritually moving experience' and invites 'what is most distinctive here?' without a domain question, but never carries the PTA §13.9 obligations — pacing and uncertainty-first for hard findings, calibrated probability words, gaps calm not ominous, and above all no unsolicited severity (an unprompted atlas is the exact path by which a health or mortality finding gets volunteered) — nor the §14.9 sycophancy-drift defenses. 'Emotional intensity is not a correctness metric' appears only as an evaluation rule (§11.2), not as a serving behavior, and nothing says the product must not perform profundity.

*Evidence:* V:37 'The user's aspiration for a profound, even spiritually moving experience belongs in the vision'; V:126 'A person can ask "what is most distinctive here?" without first supplying a domain question'; V:416 'no compulsory alerts, omen feeds or fear-based re-engagement'; V:462. PTA §13.9 (PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md:2536–2554): pacing, probability framing, 'Honest gaps must read calm, never ominous', 'No unsolicited severity — an answer about career does not volunteer a health finding because a signal fired. Cross-domain surfacing is a B.11 retrieval discipline, not a licence to alarm'; §14.9 sycophancy drift (:2783–2803: synthesis stateless w.r.t. user reactions, identical-question diffing, optimism-bias tracking). MP §3.5.H exhaustive coverage relaxes no ethics (MACRO_PLAN_v2_0.md:647). voice_lint.ts:29–40 implements probability framing and uncertainty-before-severity as …

*Verification:*

- textual: **stands** (confidence 0.70) — Verdict under the textual-accuracy lens: the finding SURVIVES in a narrowed form. Its headline claim — that the PTA §13.9 emotional-register obligations are absent — is textually accurate; roughly half of its other assertions misread the document or are already covered, so the finding as written is overstated and its proposal duplicates existing text.

CITATIONS VERIFIED. PTA §13.9 is exactly where the finding says (…
- grounding: **stands** (confidence 0.72) — GROUNDING VERDICT: the finding survives only in a narrowed form. Its citations are accurate, but two of its three headline claims are contradicted by the vision text, and it overstates the governance status of PTA §13.9/§14.9. What survives is real, code-grounded, and has no other living home.

CITATIONS VERIFIED (all exact):
- PTA §13.9 "Emotional register — a design input, not a disclaimer" at 00_ARCHITECTURE/PARIP…
- materiality: **stands** (confidence 0.72) — PARTIALLY REFUTED, NARROWED. Roughly two-thirds of the critic's proposed text is duplicative of the vision or would weaken it; one core element is genuinely missing, unenforced anywhere in governance or code, and directly created by v1.1's headline features — that element makes the finding material.

REFUTED PORTIONS (would not improve the definition):
1. The V:37 replacement. The original (scratchpad/inputs/VISION_v…

*Adopted proposal:* Narrow the finding to the PTA §13.9 register obligations (plus the two §14.9 mechanisms) and drop the duplicated material. Concretely:

1. Do NOT replace V:37 (it already holds the divine-authority and metaphysics-as-interpretation clauses). Append one sentence: "That response is never performed: the register is calm and specific, and difficult findings are paced and led by what is uncertain."

2. Add ONE new bullet to §10, between V:429 (no supernatural access) and V:430 (no coercion): "Do not volunteer severity. The living atlas, the question compass and any cross-domain expansion never push a health, mortality, loss or crisis finding outside the domain the person asked about; such findings are reachable on request, not surfaced unasked. Difficult findings lead with what is uncertain and are paced; probability is expressed in calibrated words with the number available on expansion; an honest gap reads neutral, never ominous."

3. Extend the V:386 atlas row's failure column from "salience based on emotional impact" to "salience based on emotional impact, or unsolicited severity" so the rule binds to the component row.

4. Add one row to the §11.2 table (after "Understanding and ag…

*Answered in v2.0:* §7.3 emotional-register sentence, §9 long-term — adopted.


### F-10 · VERIFIED · MAJOR · weakness · v1.1 §10

**The eight 'do nots' are behaviours without detectors; several cannot read false; §3.5.A/E/G obligations omitted**

*Claim (ethics, safety, consent and cultural responsibility):* §10 claims 'product behaviors' but binds none of its eight sentences to an enforcement point, a detector or an honest status. Bullet 7 ('do not hide … behind a reassuring score') is contradicted by live scalar roll-ups; bullet 5 has no detector; the §3.5.A.5 red-team obligation is a sample pool with no runner. Missing entirely: §3.5.G bands-mandatory-for-any-number (or no number), §3.5.A.6 reversibility/retraction, §3.5.E windows-never-modifiable/no-revision-after-outcome, §3.5.A.4 no output for non-consented subjects, and §3.5.C (finding 01).

*Evidence:* V:424 'These are product behaviors, not a disclaimer'; V:426–433. CLAUDE.md §N.8 (a status without a detector 'is null, not green'). Scalar roll-ups: platform-mcp/src/tools/phala_outlook.ts:13–21 (summary_confidence = mean(anchor.confidence), R8 §2); kala_priority_get self-disclosed salience monoculture (R8 §2). Red-team cadence: platform/src/lib/pariprashna/safety/predictive_sampling.ts:11–30 ('§IS.8 is a GOVERNANCE cadence, not a piece of software … there is no mechanism to wire into'). MP §3.5.G (MACRO_PLAN_v2_0.md:636–643: 'Outputs without a calibration band attached are not valid outputs'); §3.5.A.6 (:597) and HS-5 retraction (SAFETY_PRIVACY_TENANCY_v0_1_PROPOSAL.md:74–79); §3.5.E (:626–628); §3.5.A.4 (:595). Vision's inverted default: V:148, V:460 'calibration where justified' (R2 §4).

*Verification:*

- textual: **stands** (confidence 0.62) — TEXTUAL CHECK OF EACH SUB-CLAIM (document = /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/b9e23c51-556d-4d50-9b36-c75b52f28c1b/scratchpad/inputs/VISION_v1_1.md, cited as V:line).

1. "Binds none of its eight sentences to an enforcement point, a detector or an honest status." — Literally true of §10 in isolation (V:424-435 contains no cross-reference, mechanism, check or status). OVERSTATED at document le…
- grounding: **stands** (confidence 0.72) — CORE OF THE FINDING SURVIVES. (1) V:424 does say "These are product behaviors, not a disclaimer" and V:426-433 bind none of the eight bullets to an enforcement point, detector or status; nothing elsewhere in the vision supplies that mapping (grep of VISION_v1_1.md for detector/enforce/flag/unenforced returns nothing relevant; S1 at V:601 cites CLAUDE.md "earned signals" but §10 never applies it). Because the vision i…
- materiality: **stands** (confidence 0.72) — MATERIAL CORE CONFIRMED (two of four bullets + the enforcement-point framing). (1) §3.5.G reconciliation: VISION V:148 ("Event probabilities or narrow dates appear only where their evidential basis supports that meaning") and V:460 ("calibration where justified") invert MACRO_PLAN_v2_0.md:636-643 ("Point estimate; Confidence interval; Method pointer; Known failure modes. Outputs without a calibration band attached ar…

*Adopted proposal:* Restate the claim as: "§10 (V:424-435) restates the boundaries as prohibitions on claims but names no check class, no §8 owner and no evaluation binding; bullets 3–4 have no home anywhere in the document; §11.2 has no row that measures boundary compliance despite V:469; and three Ethical-Framework rules are not carried as product behaviours — §3.5.A.5 adversarial sampling/emission logging (absent from the whole document), the §3.5.G conjunction (V:148/348/356/447 forbid invented numbers and require material uncertainty, but nothing says an emitted number must carry interval, method and failure modes, and V:460 'calibration where justified' reads conditional against MP:643), and HS-5 retraction-as-appended-record with recipient notification (V:342/410/418/420 cover explained, non-silent revision but only via opt-in updates). §3.5.E and §3.5.A.4 are covered in substance (V:164, 205, 294, 373, 388, 460, 509; V:69, 162, 199, 384) and need only a §10 cross-reference, not new text." Drop the assertions that bullet 7 is "contradicted" by live roll-ups (the vision already classes them as failures at V:104/110/370) and that A.6/E/A.4 are "missing entirely".

Concrete edits: (1) After V:424 …

*Answered in v2.0:* §10 detector column — adopted.


### F-12 · VERIFIED · MAJOR · gap · v1.1 §9

**Day one / day thirty / year three never storyboarded; §9 is prohibitions**

*Claim (C1_consumer_ux — consumer and experience design):* §9 never says what appears on screen, what the person does first, or what record they own after a year. It omits that a chart must be built before any question can be asked, never places the chart-first reveal (already defined in PA J.5 and RS S-1) at first use, never names the reference surface, and never fixes the reference persona even though day one differs materially between the native (who builds) and a guest (who requests).

*Evidence:* VISION:398-402 is eight sentences, six of them constraints ('Do not make a long biography or flawless birth time a universal entrance requirement', 'they are not prerequisites for asking a question'); none describes a screen. A guest actually sees 'Login → dashboard listing their charts → per chart: Paripraśna, Nirmāṇa, Timeline, Panchang, Pratikruti, Edit, Samīkṣā' (PTA:585-587); platform/src/app/clients/[id]/ contains cockpit consult consume edit nirmana panchang pariprashna pratikruti samiksha timeline. A question cannot be asked until the 128-asset DAG has built the chart (R9), and OT-4's lean is 'build execution stays super-admin-only; guests read build state … Offer guests "request a rebuild"' (PTA:376) — the vision has no build step or waiting state. The reveal pattern exists twice already: PA J.5 'Chart-first reveal across all domains; goal-calibration on-demand post-reveal' (PA:…

*Verification:*

- textual: **stands** (confidence 0.78) — Core textual claims hold. (1) No build precondition or waiting state anywhere: 'build/built/ready' appear only at VISION:320, :374, :386, :463, :558, none a first-use step; §9:398-402 implies the first act is a question, while PTA:376 (OT-4) and R9 establish request→build→reveal for a guest. (2) The chart-first reveal is never placed at first use: §2.3:91 keeps it 'available', E1:126 lets a person 'ask what is most d…
- grounding: **stands** (confidence 0.72) — GROUNDING VERDICT: the finding's core gap claim survives; three evidence statements are wrong or misleading and the proposed text has three governance/vision collisions, so it survives with a revised proposal.

WHAT IS CONFIRMED LINE-EXACT
- VISION:396-402 (§9 First use) contains no build/preparation step, no placement of a chart-first reveal, no reference surface, no reference persona. VISION:118 says "not six manda…
- materiality: **stands** (confidence 0.62) — VERDICT: survives on its day-one core; two-thirds of the proposal is duplicative or would weaken the definition, so severity is narrowed and the text must be rewritten.

WHY IT IS MATERIAL (not refuted):
1. The gap is real and unique to this finding. VISION §9 "First use" (inputs/VISION_v1_1.md:396-402) is constraint sentences only; a full keyword sweep shows "guest", "operator", "portal", "consult", "waiting", "is r…

*Adopted proposal:* Keep §9's four sub-headings and their existing sentences (they are obligations, not prohibitions, and VISION:23/:118/:500 deliberately decline to define the product by screens). Retitle the finding "§9 is obligations, not a storyboard; first use omits the build precondition, the reveal as opening, the reference surface and the persona split." Insert, after VISION:402 and before "### During an investigation":

### Reference first-use sequence (target sequence, not a screen specification)

Reference persona: a consenting guest whose chart has been prepared for them; the native is that guest with operator rights (§2.1). Reference channel: the Paripraśna conversation, with managed `prashna_ask` sharing its investigation semantics (§7.3). Which surface is the production default, and when the legacy consult page is retired, remain standing rulings outside this document (frontmatter `does_not_supersede`).

1. **Birth details.** Date, time, place. Madhav states what each affects and how much precision matters for the questions this person is likely to ask. An uncertain time is held as an interval (stable core first, above), never corrected silently.
2. **Chart preparation.** No question is…

*Answered in v2.0:* §9 storyboard — adopted.


### F-13 · VERIFIED · MAJOR · weakness · v1.1 §7.4

**§7.4 sample dialogue is a cautious system describing its method, not a great experience**

*Claim (C1_consumer_ux — consumer and experience design):* The one passage meant to make the experience tangible shows Madhav narrating its methodology with no chart content, no timeframe, no likelihood language and no question back; the user has to volunteer the disambiguation Madhav should have asked for; 'The earlier answer remains recorded with its original meaning' is ledger-speak to the reader; and the sample demonstrates none of the six §12.1 core-target additions nor the tracked-claim offer.

*Evidence:* VISION:334 first reply: 'The nearest opening would not, by itself, justify saying the strain is over. The important distinction in this reading is between an opportunity arriving and money becoming reliably available. We should compare…' — meta-commentary, zero evidence shape. VISION:340 the user corrects the premise ('Actually, by strain I meant low profitability, not cash collection'), which is exactly the material fork PTA §6.6 says the instrument asks about first: 'the engine returns one clarifying question instead of guessing … at most one question, never two in a row, and always offer "just read it as asked"' (PTA:903-909); the planner already has the ClarificationRequest outcome (R8: pipeline_planner.ts:9-27). VISION:342 'The earlier answer remains recorded with its original meaning' violates D-15 rule 2 'Internal ids, asset names, layer numbers and acronyms never appear in prose …

*Verification:*

- textual: **stands** (confidence 0.72) — TEXTUAL ACCURACY verdict: the finding's load-bearing core is confirmed by the text; several of its supporting claims are overreaches that should be dropped, and one sub-point is already addressed elsewhere in the document.

CONFIRMED (verbatim checks on /private/tmp/.../scratchpad/inputs/VISION_v1_1.md):
1. §7.4 is the only place the document shows a response shape. §7.4's own heading is "Make the experience tangible…
- grounding: **stands** (confidence 0.80) — VERDICT: the finding survives on its primary claim; three of its evidence sub-claims are overstated or misattributed and the proposal needs four grounding corrections.

WHAT HOLDS (verified against source):
1. PTA citations are verbatim-correct: §6.6 "Below threshold on a material axis, the engine returns one clarifying question instead of guessing ... at most one question, never two in a row, and always offer 'just …
- materiality: **stands** (confidence 0.80) — MATERIAL, not stylistic. §7.4 is the document's sole exemplar of the consumer register, titled "Make the experience tangible" (VISION:328), and §14 says the next refinement "should make the experience concrete through representative reference investigations" (VISION:595) — so Astra and every downstream prompt/UX author will build on this passage. Its 151 words (VISION:332-342) currently contradict the definition's ow…

*Adopted proposal:* Amend §7.4 (VISION:330-344) rather than replace it, keeping the VISION:330 disclaimer verbatim. Concretely:

1. Make the first Madhav turn ask the one material clarification with the escape valve, so §7.4 matches E2 (VISION:132), the §7 pipeline (VISION:282) and PTA:903-911 / pipeline_planner.ts:10-19:
> **User:** "When will my financial strain get over?"
> **Madhav:** "One clarification first, because it changes what I compare: by strain, do you mean money not arriving when it is needed, or the work not earning enough? If you would rather I read it as asked, I will take the broader question."
> **User:** "Profit — the business is not earning enough."

2. Render the second Madhav turn in the §7.2 answer shape (VISION:312-318) with bracketed template slots and no dates, numbers or chart facts (consistent with VISION:148 and :330), keeping the D04 substance (temporary relief vs sustained change; opportunity vs realization):
> **Madhav:** "Then this is about profitability, not cash. [The earning configuration and its present condition] supports earning but is currently held back by [the active period and its qualifying condition]. Two intervals matter. [The nearer interval] is better …

*Answered in v2.0:* §7.4 rewritten as ask-back + sealable claim — adopted.


### F-14 · VERIFIED · MAJOR · weakness · v1.1 §4, §8 rows 386-388, §12.1

**E1–E6 blur; v1.1 additions bolted onto nearest experience; every capability listed three times; coined terms drift and multiply**

*Claim (C1_consumer_ux — consumer and experience design):* The six experiences read as question types, but the v1.1 capabilities were distributed across whichever E was nearest, then re-listed as four §8 component rows and seven §12.1 rows. Controlled variation lives in seven places, the living record lives in E1 (atlas) and E6 (continuing inquiry) under two names, and a reader cannot tell whether E1 and E6 are two experiences or one at two moments.

*Evidence:* Controlled variation: E2 'uncertainty-resolution step' (VISION:136); E4 'Vary one permitted input, disputed method, practical constraint or actual alternative' (156); E6 'vary a permitted assumption' (172); §9 'establish the stable core first' (400); P13/P18/P19 (198, 203-204); §8 row 387; §12.1 rows 507-508. Living record: E1 atlas 'navigable set of supported relationships, open contradictions, temporal episodes and questions' (126) vs E6 'retain its central questions, settled distinctions, disagreements and next useful tests' (176) — same object. The document says the additions 'strengthen the existing six experiences rather than multiplying screens or products' (VISION:500) and are 'not four automatically new services or assets' (392), yet §8 adds four rows (385-388) and §12.1 seven. E3/E4 are defensibly distinct, though E4's 'Action timing uses action-specific doctrine and actual can…

*Also raised by:* C6_writing_structure-03

*Verification:*

- textual: **stands** (confidence 0.75) — Textual-accuracy check of F-14 against VISION_v1_1.md (scratchpad/inputs/VISION_v1_1.md; all line refs are to that file).

WHAT THE TEXT REFUTES (the C1 headline: "E1–E6 blur", "bolted onto nearest E", "listed three times", "E1/E6 same object", self-contradiction with 392/500):

1. The document already implements exactly the one-capability-per-experience mapping the critic proposes as the fix. Actual placement: E1 ow…
- grounding: **refuted** (confidence 0.72) — GROUNDING VERDICT: the finding's load-bearing claims contradict the governing sources and the served system; only a small terminology kernel survives, and the proposed change would itself relocate or delete governance-grounded guards.

1. "E1 atlas and E6 continuing inquiry are the same object" — refuted. E1:126's atlas ("navigable set of supported relationships, open contradictions, temporal episodes and questions")…
- materiality: **stands** (confidence 0.72) — VERDICT: the C1 half (E1–E6 blur, bolted-on additions, restructure §4/§8/§12.1) is REFUTED; the C6 half (terminology drift) SURVIVES at minor with a narrowed proposal. Adopting the finding's proposed_change as written would make the definition weaker, internally contradictory and in one place less honest.

1. The 'blur' is not confirmed; the document already does what the crosswalk asks. Each experience already owns …

*Adopted proposal:* Replace the crosswalk/deletion proposal with a terminology pass only; keep §4 E1–E6, §8 rows 385-388 and §12.1's three columns as they are.

1. One name per concept, applied in place:
   - "inquiry contract" everywhere for the method-native contract; at first use (214) write "its own inquiry contract (subject; which instant/location or records matter; how inputs are established; what completeness means; which techniques apply; what kind of claim can be made)" and use "inquiry contract" at 218, 298, 300, 385, 466, 483, 510 (keep "completeness" as a named element of it where 218/300 need it).
   - "case observatory" only for the consented multi-subject research store (263, 511, 590). Retitle E6 (170) "An enduring inquiry: 'Go deeper. Challenge this. What changed?'" and, in 174, say the return experience is the person's entry into the case observatory's sources, competing interpretations and research questions.
   - "conditional map" at 392 and 508 (row title "Interactive contrast and the conditional map"; mechanism cell "qualified conditional rules behind the map").
   - "stable core": bind the term where the concept first appears, at 83: "Stable understanding under uncertainty (the …

*Answered in v2.0:* §4 three pairs; Appendix A glossary — adopted.


### F-15 · VERIFIED · MAJOR · gap · v1.1 §9 after the answer, E6, E3, §11.3

**Accountable continuity depends on an undesigned user act; after-answer list misses the one real continuation (the window closing)**

*Claim (C1_consumer_ux — consumer and experience design):* The vision presents 'compare', 'challenge this' and 'this did not happen' as natural continuations although none is built, while the continuation that is live — the tracked claim the person confirms with a likelihood band, watches, and resolves (including 'can't tell') — is absent from E3, E6 and §9. §11.3's third journey is only possible if the person performed that act months earlier, and the 'quiet, no compulsory alerts' posture then works against compliance decay unless the two conversational moments PTA designs for it (in-stream 'log this' and the return question) are included.

*Evidence:* VISION:410 lists 'compare', 'challenge this', 'what changed?', 'this did not happen'. Dispute capture is 'Still fully unbuilt, and the feedback endpoint still discards every rating at HEAD' (PTA:2776-2779); no reading-vs-reading diff exists (R8 §2: semantic_compare is replay-vs-persistence); no method-exclusion operator exists (R8 §2 'Uncertainty resolution' row). The live object: the human must confirm and commit a band — 'REQUIRED — the ledger confidence is always a band, never a point' (platform/src/lib/pariprashna/samiksha/confirm.ts:62-68); card eyebrow 'TIME-INDEXED READING · AWAITING CONFIRMATION / WINDOW OPEN / WINDOW CLOSING / AWAITING OUTCOME / RESOLVED — …' (lifecycle_label.ts:46-66); badge 'NEVER red, and is never framed as a debt/shame counter. A badge of 5 means "five items you could act on"' (badge.ts:11-14); 'can't tell' Brier-excluded (R11 §3.1). Compliance decay is 'the…

*Verification:*

- textual: **stands** (confidence 0.72) — TEXTUAL CHECK OF EACH CLAIM (VISION = /private/tmp/claude-504/.../scratchpad/inputs/VISION_v1_1.md).

(1) "presents compare / challenge this / this did not happen as natural continuations" — accurate: VISION:410 "Make 'why?', 'show the source,' 'compare,' 'challenge this,' 'what changed?' and 'this did not happen' natural continuations."

(2) "although none is built" — the document does NOT imply readiness: VISION:50…
- grounding: **stands** (confidence 0.85) — GROUNDING VERDICT: the finding survives. Every code/PTA citation verifies line-exact and the proposed change is compatible with governance once corrected on one point (whose confidence the band represents). Attempts to refute:

(1) Are the cited facts true? Yes. `platform/src/lib/pariprashna/samiksha/confirm.ts:62-68` reads "REQUIRED — the ledger confidence is always a band, never a point ... the human still commits …
- materiality: **stands** (confidence 0.75) — VERDICT: NOT REFUTED (severity kept at major; proposal revised for as-built honesty and correct classification).

Attempted refutations and why they fail:

1. "The vision is deliberately not bounded by code, so listing unbuilt continuations is not a defect." True as far as it goes (VISION:47, 63), but the finding's core is not "unbuilt things are listed" — it is that the one act on which the vision's own continuity p…

*Adopted proposal:* (a) E3, after VISION:146 (not a new object; the single-claim form of E5's brief): "Any statement Madhav makes with a window can, at the person's choice, become a held claim — the single-claim form of the observation brief in E5: the claim, its window, the likelihood Madhav stated (which the person confirms or adjusts as a range, never a point), and the time the person saw it. Nothing is held without that choice; unheld statements are never scored, and a held claim is never rewritten." (b) E5, append to VISION:166: "'Cannot tell' and 'I did not look' are ordinary resolutions. Coverage of held claims is reported as a neutral count, never as a score against the person." (c) §9 After the answer, replace VISION:410 first sentence with: "Reference continuations: 'why?', 'show the source', 'what is strongest, what is speculative, what would change this?' and 'hold this'. Continuations the definition commits to but which need new operators (see §12.1): 'compare with my earlier reading', 'what survives without this method', and 'this did not happen' as a durable dispute rather than a rating." (d) §9 Long-term, after VISION:416: "The preferred form of review is conversational and in scope: w…

*Answered in v2.0:* E6, §9 day thirty — adopted.


### F-16 · VERIFIED · MAJOR · weakness · v1.1 whole document

**Hedging density hides the product (~31% negated sentences; non-claims repeated up to ten times)**

*Claim (C1_consumer_ux — consumer and experience design):* The document spends more words on what Madhav will not do than on what a person will see: constraints are stated in four places (inside each E, §10, §12.2, the §12.1 'principal unknown' column) and the six revealing-moment lines are one sentence each and placed last.

*Evidence:* Counts in 10,793 words: 'not' 172, 'Do not' 22, 'cannot' 14, 'not a' 28, 'must not' 6. E3 (VISION:140-148, nine lines) carries five negations/qualifiers before its revealing moment: 'where supported', 'only when a qualified model supports that sequence; do not force every event into four stages', 'This is a map of interpretive possibilities, not a simulation of destiny or proof that a graph path causes an outcome', 'only where their evidential basis supports that meaning'. E5:166 'This is an inquiry aid, not a self-experiment proving astrological causation or an obligation to document life continuously.' §12.1 column heading 'First discriminating test and principal unknown' (504); §10 eight 'Do not' bullets (426-433); §12.2 eight rejected ideas (520-527). 'Not a simulation of destiny' recurs at E3:146, §12.2:520 and §8:387 ('counterfeit causal simulation'). Each revealing moment (128, 13…

*Also raised by:* C6_writing_structure-04

*Verification:*

- textual: **stands** (confidence 0.85) — Re-measured against /private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/b9e23c51-556d-4d50-9b36-c75b52f28c1b/scratchpad/inputs/VISION_v1_1.md (609 lines, 10,793 words incl. frontmatter; 10,292 body words). Token counts reproduce exactly: 'not' 172 (case-insensitive), 'do not' 22 (15 'Do not' + 7 'do not'), 'cannot' 14, 'not a' 28, 'must not' 6, 'does not' 23, 'rather than' 21, 'silently' 10, 'separately' 9; on…
- grounding: **stands** (confidence 0.80) — GROUNDING VERDICT: the finding's factual basis holds; the proposed change is partly ungrounded and must be revised.

1. Counts reproduce. A script over /private/tmp/.../scratchpad/inputs/VISION_v1_1.md (10,793 words) gives: 'not' 172 (case-insensitive), 'do not' 22 (15 capitalized), 'cannot' 14, 'not a' 28, 'must not' 6, 'does not' 23, 'rather than' 21, 'are not' 13 (critic: 14), 'silently' 10 (lines 49,80,199,216,27…
- materiality: **stands** (confidence 0.70) — Survives in reduced form; the kernel (C6's numbered invariants with pointer references) is a material clarity improvement, but three of C1's specific edits would make the definition weaker or less honest and must be dropped.

CONFIRMED EVIDENCE. Independent count on scratchpad/inputs/VISION_v1_1.md (10,793 words, 797 sentence units incl. table cells): 251 units (31.5%) match a broad negation regex, 185 (23.2%) a stri…

*Adopted proposal:* Apply four rules, recorded in the changelog: (1) §10 becomes the single home for ethical boundaries and non-claims, numbered I-1..I-n, one sentence each; COMPLETE it by adding the binding items currently absent: MACRO_PLAN §3.5.C (no date-of-death; no individualized mortality windows; no suicide-adjacent output; health-crisis and mental-health output double red-team plus native sign-off — MP:610-613), §3.5.F (minors under 18, active crisis and cognitive impairment excluded, excluded-subject register — MP:632) and §3.5.E (windows fixed at emission, never modifiable; no revision after outcome; LEL post-hoc edits flagged — MP:626-628). Every later restatement of an I-item elsewhere in the document becomes a parenthetical pointer '(I-n)'. (2) Do NOT apply a mechanical 'every not-a/do-not sentence in §4 moves out' rule. Classify each of the 27 negated sentences in VISION:118-178 as (a) ethical boundary → replace with a pointer to §10; (b) value-defining distinction that restates a settled ruling → keep inline (VISION:124 B.1/§N.5; 144 master plan D04; 152 honest tie §N.7 item 6; 164 MP:627-628; 172 PTA:2766-2770; 174 D-15); (c) pure repetition of an I-item or of another E → delete. Cap …

*Answered in v2.0:* §0 'what it is not' box; §10 single boundaries section; hedges consolidated — adopted in part — v2.0 is longer than v1.1 but carries binding content, not hedges.


### F-18 · VERIFIED · MAJOR · elevation · v1.1 document order, §1.1, §1.2, §12–§15

**Structure: product should read before policy; a quarter of the document is decision record/changelog; replacement outline with a ~40% cut**

*Claim (writing, structure and clarity):* The document can be cut by 40% in the body without losing substance by front-loading the definition, deduplicating hedges, converting imperatives to declaratives, and moving record/changelog/provenance to appendices; every current section maps to a slot in the outline below, and a newcomer reading §1, §3, §4 and §10 (~1,900 words) reaches the five-sentence statement.

*Evidence:* Measured 10,793 words; largest sections §12 1,162 / §4 1,146 / §8 1,044 / §7 1,022 / §6 986; §12-§15 = 2,459 words; ~192 negated sentences; ~54 imperatives; the companion master plan's fourteen-section structure (L3_KALA_CONSUMER_FIRST_MASTER_PLAN_v1_0.md:19-542) already leads with 'The decision this plan proposes' and 'What the consumer is actually buying', which the vision does not.

*Also raised by:* C1_consumer_ux-09, C6_writing_structure-08

*Verification:*

- textual: **stands** (confidence 0.78) — Textual facts verified against VISION_v1_1.md: total 10,793 words; per-section counts match the critic exactly (§12 1,162, §4 1,146, §8 1,044, §7 1,022, §6 986; §12–§15 = 1,162+750+244+303 = 2,459). §1.1 (lines 39–49) is history ("The previous work asked what Kāla should deliver"), §1.2 (51–63) is first-person aspiration, §13.3 (564–578) is a prior-vs-revised diff table, §14 (580–593) restates §12/§13 decisions, §15 …
- grounding: **stands** (confidence 0.72) — Grounding checks hold. (1) The structural evidence is accurate: VISION_v1_1.md measures 10,793 words; §12–§15 run VISION:485-610; §13.2:550 says "Do not start by debating asset names" while the component table precedes the experience section (§8 at 362, §9 at 394). The companion master plan does lead with "## 1. The decision this plan proposes" (L3_KALA_CONSUMER_FIRST_MASTER_PLAN_v1_0.md:19) and "## 2. What the consu…

*Adopted proposal:* Adopt the outline as proposed, with three grounding constraints: (a) the "Invariants and non-claims" body section (I-1..I-12) must carry, verbatim and in the body not an appendix, the honest non-claims from the cited studies — no demonstrated reliable prediction of external events, no operational learned model (calibration collect-only, L5 STRUCTURAL), no guaranteed claim immutability, non-diagnostic health framing, MP §3.5.C self-harm and §3.5.F minors/vulnerable exclusions — so hedge deduplication never removes a B.12/§N.7-item-6 obligation; (b) frontmatter version must equal the filename version (VISION:609 currently records a v1_0 filename carrying v1.1 content — a B.8 registry disagreement) with the changelog kept in frontmatter; (c) Appendix C must convert the absolute /Users/Dev/.codex/worktrees/... links (VISION:601-605) to repo-relative paths and add S6 (RETRIEVAL_STRATEGY_v1_0.md) and S7 (MACRO_PLAN §3.5/§3.7/§3.10.D) as named sources.

*Answered in v2.0:* document order: product before policy; decision record moved to §12–§13; appendices — adopted in part — the 40% cut was not taken; v2.0 chose completeness of binding content (§5 dispositions, §8 invariants, §10 detectors, §13 decisions); a one-page front (§0 + headline) is provided instead.


### F-20 · VERIFIED · MAJOR · weakness · v1.1 §6.2, §8 L0 row, §11.2

**Hierarchy of testimony among texts and classical adjudication rules absent from 'productive disagreement'**

*Claim (senior Jyotish acharya (Parāśari, Jaimini, KP, Tājaka, Nāḍī, Praśna, Muhūrta, Upāya)):* The vision asks that divergences be located on their premise and that derivative sources not be double-counted, but never states how a master decides: tiered testimony (BPHS/Bṛhat Jātaka primary, Sārāvalī/Phaladīpikā/Jātaka Pārijāta/Uttara Kālāmṛta secondary, moderns tertiary — the schema already has tier 1-3), the adjudicators (specific over general, bala decides, period-lord condition governs, contradiction between tier-1 texts is a finding), non-blending of schools with different jurisdiction (KP rejects Parāśari yogas/vargas; its verdict is timing testimony), and that the hierarchy is a classical prior which learning modulates but never overwrites.

*Evidence:* V:237-241 'identify the precise premise on which interpretations diverge, what each method is entitled to address ... Do not average incompatible meanings'; V:392 'L0 must expose method scope and exceptions'. MACRO_PLAN_v2_0.md:474 ('inter-school weights learned, not assigned; native arbitrates'); MACRO_PLAN_v2_0.md:449-457 (M8 classical-claim-holds/fails). Repo: platform/migrations/ws2_l0_texts.sql:25-26 (tier 1-3); platform-mcp/src/resources/school_conventions.ts:14-17 (four authoritative schools with jurisdictions); platform/migrations/330_bg_dignity_variant_traditions.sql:11-13 (variant traditions for Rāhu/Ketu only); platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog.ts:72 (stored school parashari only); platform/python-sidecar/brahmagyan/l0_sutravali_extractor.py:8-20 (confidence = 1.0 for all regex matches, no scope/exception/school field); pipeline/orches…

*Verification:*

- textual: **stands** (confidence 0.60) — Textually the core claim holds: VISION_v1_1.md nowhere names a hierarchy of testimony (no "tier", "primary/secondary", BPHS, Bṛhat Jātaka) nor the tradition's adjudicators (specific-over-general, bala, period-lord); grep confirms none of these terms appear. But the finding overstates the omission — several elements of the proposed paragraph already exist: jurisdiction ("what each method is entitled to address", V:241…
- grounding: **stands** (confidence 0.78) — Evidence checks out. VISION:237-241 names "source adjudication that could discriminate" and V:375 "human adjudication where necessary", but no adjudication rule or testimony hierarchy is stated anywhere (grep for hierarch/adjudicat/jurisdiction yields only those lines). Repo: `platform/migrations/ws2_l0_texts.sql:25-26` defines `tier 1..3` ("1=primary canonical, 2=secondary classical, 3=modern/derivative") and `l0_te…

*Adopted proposal:* Insert after V:241 in §6.2 one short paragraph, avoiding duplication of V:237/249/257: "Testimony is tiered, not flat: primary texts (e.g. BPHS, Bṛhat Jātaka with commentary), classical systematizers, and modern authors carry different default authority (the corpus registry already records tier 1–3). Where qualified rules conflict, the tradition's own adjudication principles — the specific rule over the general, strength (bala) between competing indications, the period lord's condition for the period — are the stated classical prior applied as explicit qualitative rules; a genuine conflict between primary texts is recorded as a finding with both citations rather than resolved by fiat. Methods with different jurisdictions (e.g. KP timing, Jaimini cara-daśā/ārūḍha) are reported in their own terms as corroborating or dissenting testimony. This prior is subject to the versioned-release rule above and to native arbitration of inter-school weights; it is never silently overwritten by learning."

*Answered in v2.0:* §6.2 hierarchy of testimony — adopted.


### F-22 · VERIFIED · MAJOR · contradiction · v1.1 §5.1, P21, §8 inquiry-family row, §7

**Inquiry families invented as product categories rather than the tradition's divisions; Praśna admitted without doctrine; method-native expansion is v3.X scope creep that contradicts B.11 as stated in §8**

*Claim (senior Jyotish acharya (Parāśari, Jaimini, KP, Tājaka, Nāḍī, Praśna, Muhūrta, Upāya)):* Jyotiṣa already divides itself (Horā/Jātaka, Praśna, Muhūrta including vivāha/kūṭa-milāna, Saṃhitā, Gaṇita); the vision's list maps onto these but does not say so, losing what each family prescribes — relationship comparison is a muhūrta/vivāha method, organizational inquiry is Saṃhitā and the muhūrta of founding (Bṛhat Saṃhitā is already in the corpus), and Praśna has admission rules (praśna-lagna methods, nimitta, refusal conditions) beyond the one the vision states. Mapping to the classical divisions also exposes that the intent classifier is natal-shaped.

*Evidence:* V:212 'Praśna/question or event inquiry; election of an action time; authorized relationship or multi-subject comparison; appropriately founded organizational or collective inquiry; and source-only or empirical research'; V:216 repeated question times. Repo: platform/python-sidecar/ga_writers/ga_prashna_writer.py:5-12 (prashna_lagna_method, question_class, significators, ithasala/eesarpha, fructification); L0 five prashna tables, 41 rows (catalog_assets_l0); platform/python-sidecar/brahmagyan/l0_prashna.py:640-641 (omen_nimitta); platform/python-sidecar/brahmagyan/l0_texts.py (brihat_samhita 1,171 chunks); platform-mcp/src/tools/intent_scope_classifier.ts:24-37 (intents carry no prashna/muhurta/relationship family).

*Also raised by:* C10_contradiction_hunter-04

*Verification:*

- textual: **stands** (confidence 0.60) — Textually the finding is half right. (1) Mapping omission is real: VISION_v1_1.md:212 lists families in product language ("Praśna/question or event inquiry; election of an action time; authorized relationship or multi-subject comparison; appropriately founded organizational or collective inquiry; and source-only or empirical research") and a whole-document grep finds no "Jātaka", "Muhūrta", "Saṃhitā", "vivāha" or "kū…
- grounding: **stands** (confidence 0.72) — Repo citations verified: `ga_prashna_writer.py:1-12` (prashna_lagna_method, question_class, significators, Ithasala/Eesarpha, fructification); `l0_prashna.py:640-653` omen_nimitta citing Prashna Mārga ch.2 and Bṛhat Saṃhitā; `l0_texts.py:232` brihat_samhita (R10:25 = 1,171 chunks); `intent_scope_classifier.ts:24-37` INTENTS carry no prashna/muhurta/relationship family. R8:45 and R10:144 independently confirm "no per-…

*Adopted proposal:* §5.1 paragraph 2 (V:212): keep the existing list but prefix it with the tradition's own map so no family reads as a novel product category: "These families are the discipline's own divisions, not new product categories: Jātaka/Horā (natal and temporal — the proving centre); Praśna (a chart for the moment of sincere inquiry, judged by its own praśna-lagna, significator and fructification rules, with nimitta and refusal conditions where the contract admits them); Muhūrta (election of an act, including vivāha and kūṭa comparison of two charts); Saṃhitā (collective/organizational inquiry, including a founding chart); and source-only scholarship." Retain V:214's sentence that these are horizon capabilities whose contracts are not yet ratified. §8 row (V:385) failure column: append "; or an interpretive natal question is re-labelled into another family to evade the whole-chart floor". Kind: weakness, not contradiction — V:218/300/308/574 already bind the natal floor today.

*Answered in v2.0:* §5.1, P21, §13 D-9 — adopted; v3.X event.


### F-23 · VERIFIED · MAJOR · weakness · v1.1 §1.2, E1, P01, §12

**Psychologized register displaces the tradition's phala orientation and its own importance instrument (bala)**

*Claim (senior Jyotish acharya (Parāśari, Jaimini, KP, Tājaka, Nāḍī, Praśna, Muhūrta, Upāya)):* E1's 'distinctive capacities, tensions, competing tendencies', §1.2's 'tension between recognition, independence and security' and P01's 'psychological patterns' are the vocabulary of modern psychological astrology, not classical Jyotiṣa, which answers 'what is distinctive' concretely (lagna/lagneśa/candra, yoga inventory with bhaṅga, strongest/weakest graha, yogakāraka, daśā-krama). This is permissible only as a labelled modern lineage under §6.1 link 4 and under the mental-health gate; and E1's dismissal of 'a global strength rank' invites demoting ṣaḍbala/bhāva-bala, which are the tradition's importance instrument.

*Evidence:* V:122 'distinctive capacities, tensions, competing tendencies and possible expressions ... understand a paradox'; V:55 'deeper tension between recognition, independence and security'; V:186 P01 'psychological patterns'; V:126 'Importance comes from ... not from positivity, rarity or a global strength rank'. Classical basis: bala as arbiter ('the strongest gives the result'); MACRO_PLAN_v2_0.md:613 (mental health domain gated as health-crisis). Repo: ga_strength_writer (ṣaḍbala, vimśopaka, bhāva-bala computed) and bg_vidhi_floors.py:60-61 (bhava_bala_scan, ashtakavarga_scan on the acharya floor).

*Verification:*

- textual: **stands** (confidence 0.60) — Quotes verified: V:55 ("deeper tension between recognition, independence and security"), V:122 ("distinctive capacities, tensions, competing tendencies … understand a paradox rather than merely labeling a planet strong or weak"), V:126 ("not from positivity, rarity or a global strength rank"), V:186 P01 ("psychological patterns"). Omission confirmed: grep finds no "bala", "ṣaḍbala", "strength instrument", "lagna", "y…
- grounding: **stands** (confidence 0.70) — Grounding checks hold. VISION_v1_1.md:122 ("distinctive capacities, tensions, competing tendencies"), :55 ("deeper tension between recognition, independence and security"), :186 (P01 "psychological patterns") and :126 ("not from positivity, rarity or a global strength rank") are quoted accurately. Repo: `platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_floors.py:60-61` puts `bhava_bala_scan` and `ashtak…

*Adopted proposal:* E1 (V:126): amend to "Importance comes from explanatory reach, relevance, counterevidence and robustness, informed by the tradition's own condition instruments (lagna/lagneśa and Moon condition, ṣaḍbala and bhāva-bala, yogas actually formed and their bhaṅga) — never from positivity, rarity or a single composite strength score." P01 (V:186): append to the distinction column "psychological/characterological framing is labelled as a modern interpretive lineage (§6.1 links 1 and 4), never attributed to a classical source." §10 (V:427): extend the health bullet to "Do not diagnose health, mental health or fertility…".

*Answered in v2.0:* §3.4 phala-orientation paragraph — adopted.


### F-27 · VERIFIED · MAJOR · gap · v1.1 §11.2 closing, E5, §8 personal-history row

**Knowledge-time is a value, not a machine-checked admissibility predicate; nothing enforces emission-before-event**

*Claim (epistemics, forecasting science and research methodology):* 'Event time is not knowledge time' (V:471) and 'Record when the person saw the interpretation' (V:166) are correct, but §8 lists knowledge time as something to 'preserve' (V:381) rather than as a precondition for a claim to count as prospective. Without the predicate a stored retrodiction is indistinguishable from a prediction.

*Evidence:* 'knowledge time' appears nowhere in platform code (R11 §4). mi_pramana pairs predictions to events by window containment only, never checking emission precedes the event (writers/mi_pramana.py:309-327). mi_pariksha: 'the cutoff is computed but never applied … a deterministic structural probe, not adjudicated evidence' (writers/mi_pariksha.py:141-149). Retroactive blinding 'self-enforced and must be declared' (01_FACTS_LAYER/PPL_RETROACTIVE_PROTOCOL_v1_0.md:38). Exposure time exists only as disclosure_timing relative to the framework (platform/migrations/345_mimamsa_jivanaghatana.sql:6-18), not per claim; sole hard cut is a single sealed 2020-01-01 split. R6 SRC:310 five-time lineage envelope: 'a timestamp or hash without those semantics is insufficient'. Kaufman et al., ACM TKDD 6(4) (2012) on temporal leakage.

*Verification:*

- textual: **stands** (confidence 0.60) — Partly a misread, partly real. The critic overstates the omission: the §8 column header is "What it must preserve" for every row, so V:381's wording carries no implication that knowledge time is merely archival. The document already states the precondition in principle in several places: V:164 "A story that used the outcome to select its explanation cannot later be advertised as a successful prior prediction"; V:257 …
- grounding: **stands** (confidence 0.80) — Code citations verified. `writers/mi_pramana.py:309-327` pairs predictions to `mimamsa_event_provenance` rows purely by `lo <= ev_date <= hi` window containment; no `emitted_at`-precedes-event check exists. `writers/mi_pariksha.py:135-150` docstring states verbatim "the cutoff is computed but never applied … a deterministic structural probe, not adjudicated evidence". `PPL_RETROACTIVE_PROTOCOL_v1_0.md:38`: "the disci…

*Adopted proposal:* Add one definition after V:471 rather than the critic's full predicate: "Admissible prospective evidence means a frozen claim whose emission time is recorded and machine-verified to precede the earliest observability of the outcome, whose window was fixed at emission, and whose subject exposure time is recorded or marked unknown. Claims that fail this are retrodictions: reported separately, labelled, never pooled with prospective claims. Declared blinding is not admissibility." Leave §8 row V:381 as is; the column header already reads "must preserve".

*Answered in v2.0:* §8 L5 row invariant (emission-before-event); §8 personal-history row — adopted.


### F-28 · VERIFIED · MAJOR · weakness · v1.1 E5, §11.2, §10

**Retrodiction and the event log require a denominator; the live corpus (memorable-event log, 25/21/0) shows why**

*Claim (epistemics, forecasting science and research methodology):* V:433 and E5's 'capture non-events and ordinary periods' (V:166) are right, but §11.2's 'false alarms, misses and observation coverage' (V:460) are computable only from a full contingency table, and the vision never requires the two cells a memorable-event log cannot supply (fired ∧ nothing happened; silent ∧ nothing happened). Without them hit rates are uninterpretable and every retrodictive tally reads as confirmation.

*Evidence:* LEL gap audit: 'Calibration weights computed from a non-uniformly sampled corpus encode the sampling bias as if it were chart truth' (06_LEARNING_LAYER/OBSERVATIONS/LEL_GAP_AUDIT_v1_0.md:22). Live retrodictive tally 25 yes / 21 partial / 0 no (grep predicted_by_chart in 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md; schema :100). Negative controls all not_implemented because the prior check 'derives a null_score directly from expected itself, so the comparison is a tautology that can never fail' (writers/mi_pariksha.py:588-614). Climatology null already exists to build on (mi_pramana.py:386-392). Meehl 1954; Kahneman & Tversky outside view; Tetlock 2005.

*Verification:*

- textual: **stands** (confidence 0.60) — Textually the finding is accurate in its core claim but overstates the omission. The document already contains most ingredients the critic asks for: E5 "Capture non-events and ordinary periods where relevant, not only memorable peaks" (VISION_v1_1.md:166); §11.2 Temporal row's control "simple baselines, knowledge-time controls, false alarms, misses and observation coverage" (:460) — "false alarms" is the fired-and-ab…
- grounding: **stands** (confidence 0.82) — Every factual claim checks out. VISION E5 (:166) says "Capture non-events and ordinary periods where relevant", §10 (:433) forbids treating "a selected log of memorable events" as proof, and §11.2 (:460) lists "false alarms, misses and observation coverage" as Essential controls — but nowhere does the vision require the contingency cells or declare an all-events log inadmissible for hit rates. Repo reality supports t…

*Adopted proposal:* In §11.2 Temporal row, extend the Essential control after "observation coverage" with: "...including silent control windows (pre-registered periods in which no claim fired) so that false alarms and misses have a denominator; an event record with no recorded non-events supports coverage and gap reporting only, never a hit-rate or accuracy figure." In E5, after "Capture non-events and ordinary periods where relevant" add: "and report, per period and domain, whether the person's record is dense, sparse or absent — an empty period is unobserved, not a period in which nothing happened (cf. §8 L3 failure mode 'missing coverage looks like relief')."

*Answered in v2.0:* E6 (unmatched activations and non-events counted; LEL bias named) — adopted.


### F-29 · VERIFIED · MAJOR · gap · v1.1 §6.4, §6.5, §11.2

**Multiple-testing control and pre-registration are named, not mechanised, against thousands of hypotheses on one subject**

*Claim (epistemics, forecasting science and research methodology):* 'Register searches and hypotheses sufficiently to account for multiple testing' (V:257) and 'Fix primary case-selection and similarity rules before revealing the evaluation outcomes' (V:271) state the principle at a level nobody can build: no hypothesis registry, no error-rate budget, no search-denominator disclosure, no replication gate, no lock-before-outcome artifact.

*Evidence:* Candidate space: 3,002 regex rules all at confidence = 1.0 (platform/python-sidecar/brahmagyan/l0_sutravali_extractor.py:20); ~13k MSR signals per ayanāṃśa; 170 CGM edges; four deterministic discovery primitives mining 'consequential NON-OBVIOUS patterns' (writers/bo_anveshana.py:6-15) — against one subject and 57 events. Governance already has the mechanism shape: ≥ 3 independent observations, variance ≤ 0.3, match_rate ≥ 0.4, two-pass approval, shadow-only otherwise (06_LEARNING_LAYER/SHADOW_MODE_PROTOCOL_v1_0.md:74-109; MACRO_PLAN_v2_0.md:169-178). Gelman & Loken 2013 garden of forking paths; Benjamini & Hochberg 1995; Nosek et al., PNAS 115 (2018).

*Verification:*

- textual: **stands** (confidence 0.60) — The finding overstates the omission. VISION_v1_1.md already names most of the mechanisms the critic says are absent: a "separated sequence" (V:255); "Register searches and hypotheses ... multiple testing. Separate exploratory cases from held-out or prospective evidence. Include failed discoveries, comparison baselines" (V:257); lock-before-outcome ("Fix primary case-selection and similarity rules before revealing the…
- grounding: **stands** (confidence 0.62) — Factual basis checks out: `l0_sutravali_extractor.py:20` ("confidence = 1.0 for all regex matches"); `bo_anveshana.py:6-15` (four deterministic primitives mining "NON-OBVIOUS patterns"); `SHADOW_MODE_PROTOCOL_v1_0.md:74-109` (N≥3, variance ≤0.3, two-pass, match_rate ≥0.4, shadow-only otherwise); `MACRO_PLAN_v2_0.md:169-178`. VISION:257/271 do state registration/lock-before-outcome without any artifact, and R11 confir…

*Adopted proposal:* Keep §6.4 paragraphs 1-2 as written; append one sentence to paragraph 2 (after V:257): "Each reported discovery states the number of candidates the search examined and its significance or posterior adjusted for that campaign-wide budget; while the corpus holds a single consenting subject, discovery remains exploratory and no candidate is admitted to serving." In §11.2 "Discovery quality" (V:461), change the control cell to "Multiple-search accounting with declared candidate denominator and error-rate budget, negative results and independent cases."

*Answered in v2.0:* §6.5 hypothesis registry clause — adopted at definition level.


### F-30 · VERIFIED · MAJOR · weakness · v1.1 §6.5, §12.1

**n=1 and population extension: no sample-size reasoning and no case supply behind the observatory and laboratory horizons**

*Claim (epistemics, forecasting science and research methodology):* §6.5 handles dependence, similarity and rights carefully and §12.1 lists 'adequate observations, selection bias and generalization' as unknowns (V:511), but never states what N its own questions require (V:265), where consented cases would come from, or what the product asserts about populations meanwhile. Without the arithmetic, components will build observatory surfaces before a case supply exists.

*Evidence:* Live supply: one consenting subject with an LEL; a second built chart; 110,000 synthetic charts 'NOT real people' (writers/bg_cohort.py:11). DBN fitted on 37 training events, 'should not be used for population-level inference' (06_LEARNING_LAYER/M5_CLOSE_v1_0.md:306-319). Per-case entry cost under governance: written consent, ≥ A-grade rectification, no public figures without consent, minors/vulnerable excluded (MACRO_PLAN_v2_0.md:433-445, 632). V:271 concedes public biography is not a reliable record. Detecting a modest lift on a binary life outcome at conventional power needs hundreds of independent rectified longitudinally-logged subjects per family; Dean et al. 2016 report near-zero effects with thousands. Related cases add no independent n (V:273).

*Verification:*

- textual: **stands** (confidence 0.70) — Textually the core omission is real. A whole-document search for sample/power/n=/cohort/synthetic/population finds no statement of required N, no source of consented cases, and no declaration of the current supply (one consenting subject + synthetic cohort): "n=1" and "one consenting" appear nowhere; "synthetic" only at V:216 and V:520. The nearest text is generic: "sampling needs and leakage risks" (V:269), "sample …
- grounding: **stands** (confidence 0.72) — Grounding checks confirm the finding's factual base: bg_cohort.py:11 states the ~10^4+ cohort is "SYNTHETIC birth charts (NOT real people)" and :12-20 that rarity scoring is a later-wave consumer not yet built; 06_LEARNING_LAYER/M5_CLOSE_v1_0.md:306-319 records the DBN at n=37 "should not be used for population-level inference"; MACRO_PLAN_v2_0.md:433-445 and :632 impose consent, ≥A-grade rectification, no-public-fig…

*Adopted proposal:* Add to §6.5 before its final paragraph: "Case supply is the gating constraint. Today the observatory's real evidence base is a single consenting subject with a life-event log; the synthetic cohort supplies configuration base rates for rarity only, never outcome evidence. Until a consented, rectified, longitudinally logged case set exists under its own approved policy (§2.1), the product makes no population-level claim and research-facing surfaces state the current case-supply tier explicitly. Each observatory study declares its required sample and power in its pre-registration (§6.4); the acceptance portfolio (§13.2) records the current tier rather than fixing numeric thresholds in advance, consistent with §11's rule that baselines precede quantitative targets."

*Answered in v2.0:* §6.6 — adopted.


### F-31 · VERIFIED · MAJOR · gap · v1.1 §2.2, §9, §12.1

**'Stable core under uncertainty' has no perturbation grid, sampling design, stability criterion or claim-matching unit; L1 has no birth-time-uncertainty input**

*Claim (epistemics, forecasting science and research methodology):* 'What survives plausible input or method changes' (V:83), 'establish the stable core first … across the permitted range' (V:400) and 'Bounded sensitivity runs' (V:507) name an outcome without a design: what is perturbed, over what ranges and steps, factorial or sampled, what 'stable' means, how claims are matched across runs.

*Evidence:* No birth-time-uncertainty input: grep -rn -E 'birth_time_uncertain|time_uncertainty|birth_precision' over platform/src, platform/migrations, platform/supabase/migrations, platform-mcp/src → none. The only propagation file disclaims the job: 'It does NOT compute birth-time uncertainty or cross-ayanāṁśa boundary drift … It does NOT claim statistical coverage' (platform-mcp/src/lib/kala_uncertainty.ts:27-31). Existing substrates unconnected to claim survival: five real ayanāṃśas (platform/src/lib/vidhi/ayanamsha_variation.ts:60-74); rectification candidates '±90 min range, 5-min steps × 5 ayanamshas' (layers/L4_phala/query_phala_calibration.ts:533-534). Steegen et al., Perspect. Psychol. Sci. 11 (2016) multiverse analysis; Saltelli global sensitivity.

*Verification:*

- textual: **stands** (confidence 0.60) — Textually the core claim holds: VISION_v1_1.md nowhere defines what "stable" means, which dimensions are perturbed, or over what range. §9 (V:400) says only "hold across the permitted range"; §12.1 (V:507) only "Bounded sensitivity runs … comparison of diverging claim requirements"; P13 (V:198) and §11.2 (V:465) name outcomes, not designs. No occurrence of a threshold, sampling or grid anywhere (grep for perturb/mult…
- grounding: **stands** (confidence 0.75) — All codebase claims verified: grep for birth_time_uncertain|time_uncertainty|birth_precision over platform/src, platform-mcp/src and both migration dirs returns nothing; platform-mcp/src/lib/kala_uncertainty.ts:27-31 literally disclaims "It does NOT compute birth-time uncertainty or cross-ayanāṁśa boundary drift … does NOT claim statistical coverage"; platform/src/lib/vidhi/ayanamsha_variation.ts:60-74 defines exactl…

*Adopted proposal:* In §9, after "Show which relevant conclusions hold across the permitted range and which do not." (V:400), add: "The permitted range is declared, not assumed: it is spanned at least by the subject's stated birth-time precision (captured as an input, per §8 'birth precision'), the stored ayanāṃśa set, and any method or convention variants the cited rule admits. A conclusion is reported as stable only against a declared criterion over that declared range, claims are matched across variations by their evidence identity rather than by prose (cf. §7.5, §12.1 'claim-level diffs'), and a conclusion that depends on finer timing than the declared precision is reported as sensitive, never folded into a stable-sounding summary." Leave grid density, sampling design and thresholds to the executing spec, as §12.1 (V:502, V:507) already reserves.

*Answered in v2.0:* E2(c); §5 P13 DEFER; Appendix C kinds — adopted at definition level — grid to be specified with the operator.


### F-32 · VERIFIED · MAJOR · weakness · v1.1 §11, §11.2

**§11.2 rows are aspirational (no unit, metric, baseline, n, judge, pass criterion); M10 composite gate contradicted without declaration**

*Claim (epistemics, forecasting science and research methodology):* 'Establish baselines and evaluation protocols before setting quantitative improvement targets' (V:439) is right, but the table supplies neither protocol nor harness fields. Buildable today: Source/calculation fidelity, Evidence delivery, Continuity. No harness, unit or judge: Personal specificity, Incremental depth, Expert comparison, Discovery quality, Understanding and agency, Contrast/stable-core, Observation. Separately, MP M10's 'acharya-grade composite score … meets native-approved threshold' gate is rejected by V:469 without being declared an amendment.

*Evidence:* platform/src/lib/pariprashna/corpus/runner.ts:5-19 (scaffolding with injected runTurn); grep for ablation/blinded → none; MACRO_PLAN_v2_0.md:494 (M10 composite gate); PA:92 done criterion (k) requires a blind-test panel n ≥ 3, which the rows never name.

*Verification:*

- textual: **stands** (confidence 0.62) — Partly confirmed, partly overstated. (1) Table structure: §11.2 (V:451-467) has only "What to measure" and "Essential control" columns; no row carries unit, metric, baseline value, minimum n or pass criterion — confirmed. But the critic's row list is inaccurate: "Expert comparison" names blinding, "Qualified reviewers" and "transparent rubric" (V:458); "Personal specificity" names "Blinded ... comparisons under equal…
- grounding: **stands** (confidence 0.80) — Grounding checks confirm the finding's factual base. (1) VISION §11.2 (V:451-467) has only two columns, "What to measure" and "Essential control"; no row carries unit, baseline, n, judge or pass criterion, and V:469 rejects any weighted composite. (2) MACRO_PLAN_v2_0.md:492 quality gate literally reads "acharya-grade composite score at M10 close meets native-approved threshold"; MP is still status CURRENT (R2 brief i…

*Adopted proposal:* (a) In §13.2 step two (V:552), after "proof requirements", add: "Every portfolio row must state unit of evaluation, metric, baseline, minimum n, judge and blinding (or 'automated'), and whether the rubric is registered before generation; a row without these fields is not frozen." Optionally include the critic's two exemplar rows (Incremental depth; Evidence delivery) there as the template. (b) After V:469 add: "This departs from MACRO_PLAN M10's 'acharya-grade composite score' quality gate (MACRO_PLAN_v2_0.md:492): the proposed replacement is per-dimension gates in which safety, identity, faithful-evidence and no-fabrication failures are non-compensable. This is a proposed amendment for ratification under §13.3/§14, not a silent one." (c) Correct the critic's row attribution: Expert comparison and Personal specificity already name blinding/judges; the gap there is n and pass criterion only.

*Answered in v2.0:* §11.3 harness table; §13 D-4 — adopted.


### F-35 · VERIFIED · MAJOR · gap · v1.1 §7.5, §8 synthesis row, E6, §11.3

**'Inspectable insight' names neither its grain nor the existing claim/receipt objects; alignment will build a parallel store; the scripted reference investigation is never the unit of acceptance**

*Claim (C4_engineering_alignment — engineering and architecture alignment with the real system (three request paths, D-15, density/hardFloor, planner floor as B.11 enforcement, FROZEN orchestrator, build/serve/evaluate separation, generation coherence, NO-LEAKAGE, consent, provenance stamp, memory, receipts/claims)):* The vision says the unit should 'extend existing claim/receipt mechanisms where suitable' but never names them or their grain. Existing objects: per-turn AcharyaReadingReceipt (PPR-01) with interpretation sets (PPR-02: ≥3 candidates + selected + falsifier) and typed confidence (PPR-03); per-citation parts {marker_n, ref_id, grade, reader_label, audit_detail} with grades verified/corroborating/catalog_only/prior_reading/unverified; the per-turn D-16 stamp; and the only durable addressable claim identity — the Samīkṣā ledger row — which exists only for predictions. Disputes are already designed to key on (message_id, claim_span). All receipt-side mechanisms ship flag-OFF. 'Pratijñā' already names bo_pratijna, the L2 build-time promise/denial ledger, so a serving-time claim object must not reuse that word unqualified.

*Evidence:* PARIPRASHNA_ARCHITECTURE_v1_0.md:146-148 (PPR-01/02/03); platform/src/lib/pariprashna/receipt/schema.ts:1-32 (measured/unavailable per field); confidence/type_claim.ts:1-40; interpretation/assemble.ts:24-30 (cap 8, disclosed truncation); platform/src/lib/config/feature_flags.ts:558-581 (RECEIPT_EMISSION, INTERPRETATION_SETS, TYPED_CONFIDENCE, SEMANTIC_BLOCKS, DURABLE_PERSISTENCE all false); citations/floor_gate.ts:10-28 (prior_reading can never satisfy a floor item); samiksha/schema.ts:26-36, 85-97 (nine states; stamp fields copied; settled claim fields frozen); samiksha/capture.ts:14-65 (detected rows paired to message_parts by claim text; no stamp/confidence until human confirm); pipeline/persistence_stage.ts:55-57; PTA:2750-2770 (disputes keyed to (message_id, claim_span), unbuilt); platform/src/lib/retrieval/registry/layers/L2_bodha/query_pratijna.ts:1-8 (bo_pratijna = per-event-clas…

*Also raised by:* C5_product_strategy-09

*Verification:*

- textual: **stands** (confidence 0.72) — Textually the C4 half holds. VISION_v1_1.md:348 says the inspectable insight "should extend existing claim/receipt mechanisms where suitable, not automatically create a parallel store" but a whole-document grep for AcharyaReadingReceipt, PPR-0x, "interpretation set", "typed confidence", D-16, "provenance stamp", Samīkṣā/ledger, "flag" returns nothing; §8's synthesis row (VIS:378) lists "Typed claims... citations, mat…
- grounding: **stands** (confidence 0.82) — Grounding confirms the finding. VISION:348 says the insight "should extend existing claim/receipt mechanisms where suitable" without naming any; §7.5 (VISION:346-352) names no grain. The existing objects the critic cites are real: AcharyaReadingReceipt with measured/unavailable per field (platform/src/lib/pariprashna/receipt/schema.ts:13-25); interpretation-set cap 8 with disclosed truncation (interpretation/assemble…

*Adopted proposal:* Append to §7.5 (or as a normative annex cross-referenced from §7.5, §8 synthesis row and §11.3): "Grain and lineage of the inspectable insight. An inspectable insight is not a new store. It is addressed as (message_part_id, claim_span) inside a persisted managed-door turn (Paripraśna today; prashna_ask once it carries a durable reading identity, which it does not yet), and its fields resolve to existing objects: claim = the semantic block/part text; relationships and source/derivation = the turn's citation parts (ref_id, grade in verified/corroborating/catalog_only/prior_reading/unverified) and the receipt's derivation chains (PPR-01); alternatives = the receipt's interpretation set for that judgment (PPR-02: candidates, selected reading, falsifier, or an explicit disclosed truncation/waiver); material uncertainty = typed confidence (PPR-03) plus the completeness receipt's served/empty/dark for the floor items it rests on; context/version = the turn's D-16 provenance stamp, copied never referenced; ways to compare or challenge = a dispute row keyed to the same (message_part_id, claim_span) and, for time-indexed claims only, the Samīkṣā ledger row. Only prediction-class claims gain …

*Answered in v2.0:* §1.3 unit of value; receipt (NCD-3) — adopted.


### F-36 · VERIFIED · MAJOR · gap · v1.1 §8 rows 374/385/387, §9, P13/P19/P21, §5.1

**Three new cross-cutting rows require interfaces that do not exist; the document does not say what kind of thing each is (registry change, service asset, stored asset)**

*Claim (C4_engineering_alignment — engineering and architecture alignment with the real system (three request paths, D-15, density/hardFloor, planner floor as B.11 enforcement, FROZEN orchestrator, build/serve/evaluate separation, generation coherence, NO-LEAKAGE, consent, provenance stamp, memory, receipts/claims)):* Birth-precision input, birth-time perturbation, 'what survives if that method is excluded', reading-vs-reading diff, and an inquiry-family contract object all have no implementation. The assurance that the additions are 'not four automatically new services or assets' (VISION:392) holds only if each is classified: perturbation over L1 is either a computed service asset (data_source: computed, computed_at) or a stored asset (a §N.2 writer + manifest amendment) — opposite governance costs. The planner's intent enum is natal-shaped, yet a dormant Praśna substrate already exists (/api/prashna, prashna_undertaking_get, ga_prashna with 0 rows by design, five L0 rule tables) that §5.1 never mentions, so an aligner would miss or rebuild it.

*Evidence:* R8 §2 L1: grep for birth_time_uncertain|time_uncertainty|birth_precision across lib/app/migrations returns nothing; platform-mcp/src/lib/kala_uncertainty.ts:1-35 ('does NOT compute birth-time uncertainty or cross-ayanāṁśa boundary drift'; placeholder convention); rectification = ±90-min L4 candidates only. platform/src/lib/pariprashna/store/semantic_compare.ts:1-16 (replay-vs-persistence, not reading-vs-reading); R8 §2 'Uncertainty resolution' (no method-exclusion or reading diff operator). platform-mcp/src/tools/intent_scope_classifier.ts:24-37 (12 natal-shaped intents). types.ts:326-337 and RS §5.3 (data_source stored|computed|hybrid; computed_at). R8 §2 'Inquiry-family' and R9 §1 (ga_prashna dormant, 0 rows by design). platform/src/lib/pariprashna/consent/index.ts:1-9 and feature_flags.ts:527-531 (consent inert, flag OFF); PARIPRASHNA_ARCHITECTURE_v1_0.md:127 (PPR-14).

*Verification:*

- textual: **stands** (confidence 0.60) — Textually the finding is half-right. (1) Classification: VISION:392 does say the three rows are "cross-cutting responsibilities, not four automatically new services or assets" and assigns a layer demand ("L1 must make permitted sensitivity computations reproducible"), and §12.1 (VISION:507-510) names "plausible enabling mechanisms" (bounded sensitivity runs, constrained recomputation, claim-level diffs, "qualified me…
- grounding: **stands** (confidence 0.72) — Every factual premise checks out in the repo. `platform-mcp/src/tools/intent_scope_classifier.ts:24-37` lists 12 natal-shaped intents with no praśna/muhūrta/relational family. A grep for `birth_time_uncertain|time_uncertainty|birth_precision` over platform/src, platform-mcp/src and migrations returns nothing; `platform-mcp/src/lib/kala_uncertainty.ts:27-30` states it "does NOT compute birth-time uncertainty" and is a…

*Adopted proposal:* Append to VISION:392: "Before any of these responsibilities is built, its alignment task must classify it as one of: a scope/input axis on existing planner and registry contracts (e.g. birth-time precision, inquiry family), a computed service operator carrying computed provenance (e.g. sensitivity perturbation, method exclusion, reading-vs-reading diff), or a stored asset under the frozen writer/manifest contract. The vision does not choose; it forbids building without choosing." Append to §5.1 after VISION:214: "Where a substrate for a family already exists (the current praśna question-moment path and its L0 rule tables), qualification of that substrate precedes any rebuild."

*Answered in v2.0:* Appendix C 'what kind of thing' — adopted.


### F-37 · CONTESTED · MAJOR · contradiction · v1.1 §8 orchestration row, E6, §9

**'Protected histories' and 'restore evidence' promised but the storage model does not provide them; 'two states of understanding' only as a diff of persisted artefacts**

*Claim (C4_engineering_alignment — engineering and architecture alignment with the real system (three request paths, D-15, density/hardFloor, planner floor as B.11 enforcement, FROZEN orchestrator, build/serve/evaluate separation, generation coherence, NO-LEAKAGE, consent, provenance stamp, memory, receipts/claims)):* L1+ storage is delete-then-insert per chart (§N.3): a rebuild replaces rows, there is no build archive, and a past reading cannot be re-derived — the D-16 stamp records that it cannot. 'Coherent generations' is a serve-time property (one response = one build_id; mid-session drift → judgment_flag), not a storage guarantee; 'protected histories' can only mean the conversation store and prediction ledger; 'restore evidence' was last verified as PITR disabled with no restore drill ever executed. E6's comparison must be specified as a diff over persisted stamps, receipts and parts, never a recomputation of the earlier state.

*Evidence:* CLAUDE.md:278-281 (§N.3 delete-then-insert); platform/src/lib/retrieval/provenance_stamp.ts:27-35 ('a chart rebuild REPLACES rows in place; there is no retained historical snapshot … surface that drift HONESTLY as a judgment_flag + a refreshed stamp'); PTA:1673-1680 ('Because builds are not archived, a past reading cannot be re-derived'); platform/src/lib/pariprashna/provenance/stamp.ts:4-18 (immutable per-turn stamp; copied into ledger rows); platform/src/lib/retrieval/spine/materialize.ts:1-30 (re-materialize on source_asset_marker staleness; source disclosed); platform/src/lib/retrieval/provenance/freshness_notes.ts:1-30 (as_of/expires_on); PTA:2909-2925 ('PITR disabled, daily backups ×7, no restore drill ever executed', dated 2026-07-19, not re-verified); R8 §2 L3 / R7 (several kala_* tables at zero rows for the canonical chart at the stocktake).

*Verification:*

- textual: **refuted** (confidence 0.70) — The finding reads a prescriptive responsibility map as a current-state promise and reads a recomputation mechanism into E6 that the text never states. VISION:364 frames §8 explicitly as "the target responsibility map—not a fresh certification of each component"; column 3 is "What it must preserve or supply". So "protected histories … restore evidence" (VISION:383) is a demand on the component — and "restore evidence"…
- grounding: **stands** (confidence 0.60) — Facts check out: CLAUDE.md:279-280 (§N.3 "Rebuild REPLACES, never accretes"); platform/src/lib/retrieval/provenance_stamp.ts:27-35 ("there is no retained historical snapshot … surface that drift HONESTLY as a judgment_flag + a refreshed stamp"); PTA:1673-1674 ("Because builds are not archived, a past reading cannot be re-derived"); PTA:3105 F-25t (PITR disabled, no restore drill, 2026-07-19, not re-verified per PTA:2…

*Adopted proposal:* Keep the §8 row but add one clarifying clause: "…protected histories (a reading is preserved as its persisted answer, evidence citations and provenance record; chart data is rebuilt in place and is not archived, so an earlier reading is never re-derived), service reliability and a verified, drilled restore posture for the conversation record and prediction ledger." In E6 (VISION:176) append: "Both states are compared from what was persisted at the time; the earlier state is never recomputed, and if its evidence is no longer available the comparison says so."

*Answered in v2.0:* §8 orchestration row — adopted.


### F-38 · VERIFIED · MAJOR · gap · v1.1 §8 registry row, §7.1, §7.6, §15

**Registry row uses synonyms for existing mechanisms, misuses 'flattened', omits RETRIEVAL_STRATEGY's numeric targets and never cites it**

*Claim (C4_engineering_alignment — engineering and architecture alignment with the real system (three request paths, D-15, density/hardFloor, planner floor as B.11 enforcement, FROZEN orchestrator, build/serve/evaluate separation, generation coherence, NO-LEAKAGE, consent, provenance stamp, memory, receipts/claims)):* The row's failure clause treats flattening as a defect, whereas RS rules data stays layered, access is flat, and the required flattening is horizontal (spine bundles, 'the single biggest productivity upgrade available'). 'Deduplication' is not a registry concept. §7.1's compression and budget obligations are already enforced by named mechanisms — hardFloor + dissent quota, trim_report/recover_via, density_contract, demand_ranking, the served/empty/dark completeness receipt, reading_checklist, the ≤2-hop drill rule — none named; RS itself is never cited (the frame-check rule is attributed to CLAUDE.md/PROJECT_ARCHITECTURE copies, not RS §3.6). RS §7's hard targets (≤10 umbrella calls, ≤2,000-token orientation, ≤25 KB median with verdict intact, ≤3 calls to first verdict, 100% receipt coverage, ≤2 hops) are neither adopted nor consciously superseded.

*Evidence:* RS:129-136 (one real cross-layer join; spine bundles); RS:239-260 (librarian/scholar; 'Tools never summarize generatively'; trim lossy in context, lossless in reachability; dissent quota); RS:262-282 (§3.6 proportionality, RS-4); RS:450-466 (§7 targets); RS:58-61 (invariant). platform/src/lib/retrieval/registry/types.ts:207-214 (density_contract), :361-371 (demand_ranking); platform-mcp/src/lib/response_budget.ts:165-175, 285-296 (hardFloor semantics and trim-order tiers); CLAUDE.md:300-304 (§N.6 item 2); register_spine_bundle.ts:1-17; platform/src/lib/vidhi/completeness_receipt.ts:20-30 (served ∪ empty ∪ dark = floor, disjoint); reading_checklist.ts:30-38 (six checklist states). VISION:601-605 lists S1–S5 with no RS entry.

*Verification:*

- textual: **stands** (confidence 0.72) — Textually the core of the finding holds. (1) RETRIEVAL_STRATEGY is never cited: grep for "RETRIEVAL_STRATEGY|hardFloor|density_contract|demand_ranking|spine|receipt" in VISION_v1_1.md returns no RS mention; §15 lists only S1–S5 (VISION:601-605) and the frame-check/escalation rule at VISION:308 is tagged "[S1, S2]" (CLAUDE.md / PROJECT_ARCHITECTURE), not RS §3.6. (2) No numeric retrieval targets appear anywhere; §11's…
- grounding: **stands** (confidence 0.80) — Grounding confirms the finding's factual core. RS (version 1.3, CURRENT) is the retrieval plane's governing doctrine and is absent from VISION §15's S1–S5 (VISION:601-605); §7.1's frame-check rule is tagged [S1, S2] (VISION:308), not RS §3.6. RS:129-136 makes horizontal spine bundles "the single biggest productivity upgrade"; RS:239-260 fixes the librarian/scholar boundary, trim_report/recover_via and dissent quota; …

*Adopted proposal:* (a) §15: add "S6 — Retrieval doctrine: RETRIEVAL_STRATEGY_v1_0.md (§3.5 distillation boundary, §3.6 proportionality, §5.2 coverage disposition, §7 targets)". (b) §7.1: re-tag the frame-check/escalation sentence "[S6 §3.6; S1, S2]" and add one sentence: "RETRIEVAL_STRATEGY §7's measurable targets (≤10 umbrella calls per deep investigation, ≤2,000-token orientation, ≤25 KB median response with verdict intact, ≤3 calls to a first grounded verdict, completeness receipts on 100% of planned investigations, ≤2-hop drill to facts for every claim) remain the retrieval acceptance criteria of this definition unless a later ratified revision supersedes them." (c) §8 row: replace "coverage, deduplication and drill paths" with "coverage accounting, repetition control and ≤2-hop drill paths to facts, with pre-joined cross-layer bundles where one question spans layers"; replace failure clause with "Rich data exists but is collapsed into an undifferentiated list, trimmed away without a receipt, or never supplied to synthesis." Keep code identifiers out of the row per §7.2.

*Answered in v2.0:* §8 registry row; §11.2 RS targets — adopted.


### F-39 · CONTESTED · MAJOR · weakness · v1.1 §8 planner row, E2, §7

**Planner row misreads the acharya floor as a failure mode and omits the planner's existing contract (floor + band; three-way outcome; one-question rule)**

*Claim (C4_engineering_alignment — engineering and architecture alignment with the real system (three request paths, D-15, density/hardFloor, planner floor as B.11 enforcement, FROZEN orchestrator, build/serve/evaluate separation, generation coherence, NO-LEAKAGE, consent, provenance stamp, memory, receipts/claims)):* The failure clause 'A fixed tool menu determines the answer' can be read as indicting the Vidhi floor, which is by design a fixed minimum — the B.11 enforcement point (PPR-15) — that the LLM may add to but never subtract from. 'Competing explanations' names no planner object; the nearest mechanism is the receipt-side interpretation set (PPR-02, flag-OFF); dissent today is tool-level only. E2's clarification behaviour already has a contract (scope-tuple confidence → PlanReceipt | ClarificationRequest | PlannerFault; at most one question, never two in a row, 'read it as asked' always offered) that the vision restates informally. The synthesis row's 'explicit validation failure' must be reconciled with the settled defanged design: gates never fail the turn; a validator that cannot run reports unavailable, never PASS (seam E35).

*Evidence:* platform/src/lib/vidhi/compiler.ts:1-18 ('contract = floor(intent) + machine_band(depth) + LLM_extensions'; deterministic; never drops floor items by entitlement); platform/src/lib/pipeline/compiled_floor_adapter.ts:1-38 (ensureB11WholeChartReadFloor, ensureDashaContextFloor; unmappedPrimitives reported, not faked); PARIPRASHNA_ARCHITECTURE_v1_0.md:137 (PPR-15); PTA §9.2 / R3 §4 ('may ADD … may NEVER subtract below the acharya floor'); platform/src/lib/pipeline/pipeline_planner.ts:9-27 (three-way outcome; deterministic classifier short-circuits to clarification); PTA:892-912 (one question, never two, always 'read it as asked'); platform/src/lib/pariprashna/pipeline/validation_stage.ts:6-16 ('The gate NEVER fails the turn'); PTA §13.5 (rewrite/redact/telemetry, never fail-the-turn); inputs/L3_KALA_CONSUMER_FIRST_MASTER_PLAN_v1_0.md:351 (E35); R8 §2 'Planner' (no hypothesis object).

*Verification:*

- textual: **refuted** (confidence 0.72) — Textually the finding overreads. (1) "A fixed tool menu determines the answer" (VISION:377) cannot fairly be read as indicting the acharya floor: the same row's positive column lists "whole-chart obligations", and the document repeatedly binds the floor — "Existing natal whole-chart-read obligations remain binding today" (:218), "those completeness obligations include the governed whole-chart protocol" (:300), "An in…
- grounding: **stands** (confidence 0.60) — Evidence verified: compiler.ts:1-18 ("contract = floor(intent) + machine_band(depth) + LLM_extensions", never drops floor items), pipeline_planner.ts:10-21 (plan/clarification_needed/fault; deterministic classifier short-circuits), validation_stage.ts:10-16 ("gate NEVER fails the turn... outcome stays at its PASS default" — itself flagged as a gap), PARIPRASHNA_ARCHITECTURE_v1_0.md:137 (PPR-15), master plan:351 (E35)…

*Adopted proposal:* Minimal edit to VISION:377 only: in the "must preserve or supply" column, change "whole-chart obligations" to "whole-chart obligations as a never-subtracted minimum that adaptive expansion adds to"; in the failure column append "or a clarification asked when the answer would not change." Leave :378 unchanged.

*Answered in v2.0:* §8 planner row; E2(a) — adopted.


### F-40 · CONTESTED · MAJOR · gap · v1.1 §8 L5 row, personal-history row, observation row, E5, §7, §6.4

**L5 / personal-history / observation rows and E5 do not state the NO-LEAKAGE and COLLECT-ONLY invariants that already bound them**

*Claim (C4_engineering_alignment — engineering and architecture alignment with the real system (three request paths, D-15, density/hardFloor, planner floor as B.11 enforcement, FROZEN orchestrator, build/serve/evaluate separation, generation coherence, NO-LEAKAGE, consent, provenance stamp, memory, receipts/claims)):* The vision's separation of evaluation from serving is right but unnamed: (1) life_events never feeds prediction generation — four arms (DB role separation 0% built/flag OFF, calibration_context_only registry flag, out-of-process ledger writer flag OFF, CI canary); (2) COLLECT-ONLY — no calibration write may bump priors_version or annotate a serving envelope, enforced by a grep gate, a runtime leak guard on the emitter and the prashna_ask final body, and a byte-identity probe; (3) promotion only by an authenticated human under a CI manifest; (4) unverifiable is Brier-excluded by DB CHECK. E5's 'with permission, a person can supply an event log' is a new multi-user write path — /api/lel is super-admin-only and LEL entry is native-only — subject to PPR-14 consent; 'record when the person saw the interpretation' has no event-level field; the aggregate calibration write is PARKED and record_outcome is retired; 'can learn what is supported' is a horizon (STRUCTURAL mode, P7 PARKED).

*Evidence:* platform/src/lib/retrieval/registry/types.ts:372-381 (calibration_context_only excluded from all projections and prashna_ask); platform/src/lib/pipeline/no_leakage_filter.ts:1-30; feature_flags.ts:536-540 (PARIPRASHNA_ROLE_SEPARATION: false; PARIPRASHNA_LEDGER_OUT_OF_PROCESS: false); platform/src/lib/pariprashna/no_leakage/serving_path_manifest.ts:1-14 (collect-only grep gate; 'No priors bump, no envelope annotation, no minimum-n exception'); no_leakage/calibration_leak_guard.ts:13-28 (wired at emitter and prashna_ask final body); L5_mimamsa/query_mechanism_retrodiction.ts:38-48 (sealed 2020-01-01 split; CONFIRMATION ONLY); samiksha/capture.ts:40-52 (detected rows without stamp/confidence; promotion only on explicit human act); samiksha/outcome_recorder.ts:16-36 (CALIBRATION_PARK_REASON; calibration_persisted always false); platform/src/app/api/lel/route.ts:8-23 (assertSuperAdmin); R11 §…

*Verification:*

- textual: **refuted** (confidence 0.62) — Under the textual lens the finding overstates the gap. The vision already states the evaluation/serving boundary the critic says is "unnamed", repeatedly and at the level a vision document operates: VISION:257 "New models, reconstructed rules or learned parameters enter serving only through separately approved, versioned releases"; :294-295 "Separate path: frozen claims + admissible observations → evaluation → indepe…
- grounding: **stands** (confidence 0.70) — Factual basis verified: COLLECT-ONLY is code-enforced with "No priors bump, no envelope annotation, no minimum-n exception" (platform/src/lib/pariprashna/no_leakage/serving_path_manifest.ts:6-12); aggregate calibration write is PARKED, `calibration_persisted` always false (samiksha/outcome_recorder.ts:16-28); `/api/lel` is `assertSuperAdmin` (platform/src/app/api/lel/route.ts:8-23); `calibration_context_only` exclude…

*Adopted proposal:* Optionally add one sentence after VISION:295 or in the L5 row (:373): "The current instantiation of this boundary is the Samīkṣā ledger's NO-LEAKAGE / collect-only contract (human-confirmed promotion, unverifiable Brier-excluded, no priors bump or envelope annotation); alignment extends it rather than replacing it." Do not rewrite the L5, personal-history or E5 text as the critic proposes.

*Answered in v2.0:* §8 L5 row; §10 B-10; E6 — adopted.


### F-41 · VERIFIED · MAJOR · elevation · v1.1 §8, §13.1, §13.2

**Add a 'binding interfaces and invariants' appendix so per-component alignment is conformance-checking; §13.1 should reuse existing evidence vocabularies**

*Claim (C4_engineering_alignment — engineering and architecture alignment with the real system (three request paths, D-15, density/hardFloor, planner floor as B.11 enforcement, FROZEN orchestrator, build/serve/evaluate separation, generation coherence, NO-LEAKAGE, consent, provenance stamp, memory, receipts/claims)):* Every §8 row is a natural-language obligation, yet the system already has machine-checked contracts for most of them; naming them once, normatively, converts alignment into conformance checking. §13.1's six contribution questions overlap with Nirmāṇa's W1 ANALYZE / W2 DECIDE capsules (100% complete for all 128 assets) and with the value-architecture study's nine value-record questions; step three's 'capability and gap map' should reuse RS §5.2's five-state coverage disposition and the cross-layer study's six maturity states rather than a fresh scale.

*Evidence:* Engine signature and no depth/tier (PTA §13.4; D-15); platform/src/lib/vidhi/compiler.ts:1-18; pipeline_planner.ts:9-27; vidhi/completeness_receipt.ts:20-30; types.ts:7-11, 207-214, 326-381; response_budget.ts:165-175; citations/floor_gate.ts:10-28; PARIPRASHNA_ARCHITECTURE_v1_0.md:116 (PPR-11), :146-148 (PPR-01..03); provenance/stamp.ts:4-18; samiksha/schema.ts:26-36, 85-97; serving_path_manifest.ts:1-14; calibration_leak_guard.ts:13-28; CLAUDE.md:265-270 (§N.2), :287 (count_sql); ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md:96-120; PTA:848-855 (engine invariants); mcp_profile.ts:1-40; platform-mcp/src/lib/authz.ts:19-31 (fail-closed per-chart); pariprashna/lexicon.ts:1-20 (closed lexicon); NIRMANA_CODEX_HANDOFF_v1_0.md:61-62 (W1/W2 100%); RS §5.2 five-state disposition (R4 §9); R6 six maturity states.

*Verification:*

- textual: **stands** (confidence 0.72) — Textually the finding holds. VISION §8 (inputs/VISION_v1_1.md:362-392) is a 22-row prose table with no named machine contract: a whole-file grep for D-15, PPR-, density_contract, hardFloor, receipt vocabularies, SERVED-DIRECT/SERVED-VIA/GATED, five-state, maturity, W1/W2, capsule, census or Nirmāṇa returns nothing (only 'receipt' at :348, :11). §13.1 (:533-546) lists six fresh questions and nowhere says to answer the…
- grounding: **stands** (confidence 0.80) — Spot-checks confirm the finding's factual base. VISION §8 (VISION:362-393) and §13.1 (VISION:535-546) are pure natural-language obligations naming none of the live contracts. The contracts exist as cited: scope tuple + `floor(intent) + machine_band(depth) + LLM_extensions` (platform/src/lib/vidhi/compiler.ts:4-5, entitlement-as-metadata :15-17); `prior_reading`/`unverified` excluded by construction from floor satisfa…

*Adopted proposal:* Keep the finding but shrink the remedy. (a) Add a short "Appendix A — Existing binding contracts (normative pointers)" that does NOT restate mechanisms; it lists by name and source the contracts §8 rows must be conformance-checked against: engine ask(chart_id, question) with no depth/tier (PTA §13.4, D-15); Vidhi floor + completeness receipt as B.11 enforcement (PPR-15, PPR-01..03); envelope density_contract/hardFloor/trim_report (RS §5, response_budget); per-turn provenance stamp copied into ledger rows (D-16); Samīkṣā ledger states and unverifiable Brier-exclusion; NO-LEAKAGE/collect-only arms; §N.2 frozen writer contract, 128-asset manifest, count_sql; MCP authz fail-closed and OAuth profiles; RS §5.2 coverage disposition and the S5 six maturity states; RS §7 numeric targets as acceptance criteria. (b) In §13.1 after the six questions add: "Answer these from evidence already on record wherever it exists — the Nirmāṇa W1 analysis and W2 verdict capsules per asset, registry census rows, and the six-state utilization maturity of each cross-layer input — rather than re-interviewing the asset." (c) In §13.2 step three replace "Reconcile current evidence" with "Reconcile current evide…

*Answered in v2.0:* §8 invariant column — adopted.


### F-45 · VERIFIED · MAJOR · gap · v1.1 §7.6, §8 orchestration/security rows, §9

**Operating realities (cost, latency, model identity, provider substitution, degraded mode, spend ceilings, restore posture) unconstrained, so 'align every component' has no envelope**

*Claim (product strategy and prioritization):* Cost per investigation, latency, model dependency, multi-tenancy and generation coherence are the realities that decide whether a component alignment is real or nominal; the document mentions only 'resource controls' and 'coherent generations' and constrains none of them.

*Evidence:* VIS:358, VIS:383. Cost: agentic loop capped at 8 iterations (platform/src/lib/synthesis/agentic_loop.ts:27); CostCapTracker on prashna_ask can skip synthesis (platform/src/app/api/mcp/prashna_ask/route.ts:89, 205, 611-612, 681-688) but no request-blocking middleware or daily ceiling (no platform/src/middleware.ts; PTA:2854-2874); in-process 60 RPM per instance (platform-mcp/src/lib/rate_limiter.ts:1-17). Latency: no TTFT/streaming metrics (PTA:3072). Model dependency: DEFAULT_STACK_ID='gemini', Gemini 2.5 Pro primary, DeepSeek fallback (platform/src/lib/models/registry.ts:872-873, 1449-1452); Anthropic key unprovisioned in production (CLAUDE.md:407); five adapters in platform/src/lib/llm/providers/. Multi-tenancy: guest build rights open (PTA:372-383); stale non-native rows break canonical integrity checks (NIRMANA_CODEX_HANDOFF_v1_0.md:109-113). Generation coherence: readings not re-der…

*Also raised by:* C9_completeness_critic-06

*Verification:*

- textual: **stands** (confidence 0.70) — Textually the gap is real but the finding overstates it. The document mentions more than "resource controls" and "coherent generations": VIS:384 lists "tenant isolation, provider/data handling, deletion/retention policy, injection resistance and bounded resource use"; VIS:383 lists "invalidation, lineage, protected histories, service reliability and restore evidence"; VIS:374 names "build/model context" and the failu…
- grounding: **stands** (confidence 0.72) — Factual claims verified: no platform/src/middleware.ts exists; platform-mcp/src/lib/rate_limiter.ts:10-13 is an in-process 60 RPM per-instance guard ("Global RPM ... limit × instance_count"); registry.ts:872 DEFAULT_STACK_ID='gemini'; agentic_loop.ts:27 MAX_ITERATIONS=8; prashna_ask/route.ts:89,204 cost caps resolved per role but nothing blocks before dispatch daily; provenance/stamp.ts:66-71 interface carries exactl…

*Adopted proposal:* Do not add a new §7.7; tighten existing cells so each operating noun has an invariant (numbers deferred per VIS:595). §8 Orchestration row, "must preserve or supply": append "each served claim stamped with its evidence generation; answers that would mix generations are flagged or declined; a stated recovery objective for the conversation store and prediction ledgers demonstrated by an executed restore drill, not configuration; degraded modes that name what is unreachable rather than answering around it." §8 Security row: append "a per-turn and per-day resource ceiling enforced before dispatch and reported as a designed stop (cf. §7.6/§9 partial-answer rule); provider access through one governed model plane with a declared substitution policy so no evidence contract depends on one provider; chart entitlement re-authorized on every call and never inferred from question text." §9 after VIS:410: "The provenance carried with every answer names the evidence generation, priors and formula versions, knowledge date and the model identity/version used for synthesis." §11.2 (VIS:463): add "time-to-first-verdict and time-to-complete measured on every reference investigation." Note in E6/§9 tha…

*Answered in v2.0:* §7.5 spend caps; §8 orchestration/security rows (model identity, degraded mode) — adopted.


### F-47 · VERIFIED · MAJOR · weakness · v1.1 §1.2, §4, §6.5, §13.1, §15

**Four voices: imperatives to an unnamed agent, first-person essay, third-person description, AI-process provenance**

*Claim (writing, structure and clarity):* About 54 sentences open with an imperative whose addressee is never named ('Give that portrait...', 'Include a question compass', 'Show a conditional map', 'Make comparison interactive', 'Fix primary case-selection', 'Use the layer-value-elevation skill'), §1.2 is first-person singular beside 'we' elsewhere, meta-sentences about the document recur, and §15 records which AI skills produced the text. A definition should be declarative; imperatives read as the execution brief the document insists it is not, and skill provenance belongs in SESSION_LOG or an appendix.

*Evidence:* Imperatives at VISION:126, 136, 146, 156, 216, 271, 546 ('Use the layer-value-elevation skill to perform that research'); 'I would want Madhav to make a life intelligible' VISION:53 vs 'we' at 19, 27, 35, 63, 334, 437; meta-sentences VISION:49, 578, 595; process provenance VISION:607-609 ('the product-brainstorming skill drove deliberate divergence... the layer-value-elevation skill required changes...'); self-denial of execution status VISION:4, 49.

*Verification:*

- textual: **stands** (confidence 0.85) — Textually confirmed. Sentence-initial imperatives are pervasive: a conservative verb-list count over VISION prose (tables/blockquotes excluded) yields 35 imperative-opening sentences, incl. VISION:126 "Give that portrait…", 136 "Include a **question compass**", 146 "Show a **conditional map…**", 156 "Make comparison interactive. Vary…", 216 "Do not invent a birth time…", 271 "Fix primary case-selection…", 546 "Use th…
- grounding: **stands** (confidence 0.80) — The textual evidence verifies: VISION:53 is first-person singular ("I would want Madhav to make a life intelligible…") against document "we" at :19, :27, :437; lines 126/136/146/156/216/271 open with unaddressed imperatives ("Give that portrait…", "Include a question compass…", "Show a conditional map…", "Make comparison interactive.", "Do not invent a birth time…", "Fix primary case-selection…"); :546 reads "Use the…

*Adopted proposal:* Keep the critic's declarative rewrites for §4–§7 and the §1.2 attribution/move. For VISION:546, do not delete the line: move "Use the layer-value-elevation skill to perform that research" to the provenance appendix, but retain in the body, in document voice, "That research is performed under the existing asset-elevation execution process only in separately authorized implementation tasks; this document authorizes no execution." Move VISION:607-609 to an Appendix "Provenance" alongside the frontmatter changelog (B.8), not to SESSION_LOG, since the vision lives in a Codex worktree outside the governed SESSION_LOG flow.

*Answered in v2.0:* single definitional voice — adopted.


### F-48 · VERIFIED · MAJOR · error · v1.1 frontmatter, §15

**File name, version label and status disagree with each other and with B.8 / hygiene §A**

*Claim (writing, structure and clarity):* The artifact is stored as ..._v1_0.md while frontmatter says version 1.1 (the document admits this at 609); the v1.1 changelog describes a scope expansion, which B.8 classifies as a major bump, not minor; no successor path was created and v1.0 was overwritten rather than retained per hygiene §A; the status field is a free-text sentence outside the schema's enumerated set; the file sits under briefs/ where no validator covers it; and there is no canonical_id although it is meant to govern every component. The same defect exists in the companion master plan, so §15's 'Master plan v1.1' links a _v1_0 filename.

*Evidence:* Codex worktree listing: /Users/Dev/.codex/worktrees/0ee2/Madhav/00_ARCHITECTURE/briefs/nirmana/MADHAV_CONSUMER_PRODUCT_VISION_AND_DEFINITION_v1_0.md (80,127 bytes, byte-identical to the v1_1 copy); VISION:3 version: "1.1"; VISION:609 'The stable artifact filename retains v1_0'; VISION:13 changelog 'living atlas, question discovery, stable-core/uncertainty resolution, controlled contrast, observation design, method-native expansion, contrastive research'; PROJECT_ARCHITECTURE_v2_2.md:152-156 (Major = scope expansion; Minor = 'clarifications without analytical change'); PROJECT_ARCHITECTURE_v2_2.md:1185 (in-place amendment only when 'meaning is preserved'); ONGOING_HYGIENE_POLICIES_v1_0.md:101-104 (bump creates successor; predecessor retained with SUPERSEDED banner); platform/scripts/governance/schemas/artifact_schemas.yaml:15-16 (glob 00_ARCHITECTURE/*.md only) and :29-31 (status enum DRA…

*Verification:*

- textual: **stands** (confidence 0.85) — Textual check confirms every document-level claim. VISION:3 reads `version: "1.1"`; VISION:4 `status: PROPOSED — product definition for iterative ratification; no implementation authorization` (a free-text sentence, not a bare enum token); no `canonical_id` key exists anywhere in the frontmatter (VISION:1-16, grep confirms). VISION:13's v1.1 changelog lists "living atlas, question discovery, stable-core/uncertainty r…
- grounding: **stands** (confidence 0.70) — Core facts confirmed: VISION frontmatter `version: "1.1"` (line 3) with free-text `status: PROPOSED — …` (line 4) while the on-disk file is `..._v1_0.md` (Codex worktree listing, 80,127 bytes) and VISION:609 admits "The stable artifact filename retains `v1_0`". artifact_schemas.yaml:15-16 globs only `00_ARCHITECTURE/*.md` and :29-31 enumerates DRAFT_PENDING_REDTEAM/CURRENT/LIVE/LIVING/CLOSED/SUPERSEDED, so a briefs/ …

*Adopted proposal:* Keep the proposed change, with two textual precisions: (1) delete the VISION:609 sentence "The stable artifact filename retains `v1_0`; frontmatter and this changelog identify the revised content as **v1.1**." rather than leaving any filename-vs-version note in prose; (2) at VISION:604, make the S4 link text and path agree (either "Master plan v1.1" pointing to a `_v1_1.md` path once the companion is renamed, or cite the file as it is actually named); (3) add `canonical_id: PRODUCT_VISION` and a bare enumerated `status:` token (e.g. `DRAFT_PENDING_REDTEAM`) with the free-text qualifier moved to a separate `authorization:` key.

*Answered in v2.0:* consistent v2.0 naming — adopted.


### F-49 · VERIFIED · MAJOR · error · v1.1 §15, §5, §8, §7

**Evidence basis non-portable (Codex worktree paths), one dead anchor, superseded/incomplete sources (cites superseded Paripraśna v0.1; never cites RETRIEVAL_STRATEGY or ethics); Q01–Q18 mislabelled as 'temporal tests'; six maturity states collapsed to three**

*Claim (writing, structure and clarity):* All five §15 links are absolute paths into one machine's Codex worktree and break for every other reader and for the repo copy; the PTA:2750 anchor resolves to a blank line; the vision cites only the SUPERSEDED PTA v0.11 rather than its normative successors; only five [S#] markers exist in 10,793 words; the frame-check/escalation rule is attributed to [S1, S2] rather than its source RETRIEVAL_STRATEGY §3.6, and MACRO_PLAN §3.5 (the consent/disclosure authority §2.1 and §10 paraphrase) is never cited.

*Evidence:* VISION:601-605 links begin /Users/Dev/.codex/worktrees/0ee2/Madhav/...; the four companion studies carry 38/42/21/8 absolute links and zero repo-relative ones; PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md:2750 is blank in both worktree and main, with §14.8 'Capturing disagreement' at line 2751 and §14.9 'Sycophancy drift' at 2783; the other six anchors resolve (CLAUDE.md:107 §A; PA:57, :857, :983; MP:103; PTA:2277 §13.4); PTA is SUPERSEDED-by-decomposition with PARIPRASHNA_ARCHITECTURE_v1_0 + DECISION_REGISTER normative (grounding/R3_pariprashna_architecture.md header); grep '[S' yields only lines 71, 208, 308, 326, 390; RS never cited and §7.1's rule tagged [S1, S2] (grounding/R4_retrieval_strategy.md:10); MP §3.5 never cited (grounding/R2_macro_plan.md:101-108).

*Also raised by:* C10_contradiction_hunter-10

*Verification:*

- textual: **stands** (confidence 0.90) — Every textual claim verified against the document. (1) VISION:601-605: all five §15 links are `/Users/Dev/.codex/worktrees/0ee2/Madhav/...` absolute paths; no repo-relative form anywhere. (2) PTA:2750 (VISION:603) is a blank line in the main checkout; `### §14.8 Capturing disagreement` is 2751 — dead anchor confirmed. (3) Only PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md is cited; grep for PARIPRASHNA_ARCHITECTURE / DECIS…
- grounding: **stands** (confidence 0.90) — Every factual leg verifies. VISION:601-605 links all begin `/Users/Dev/.codex/worktrees/0ee2/Madhav/...` (non-portable). `grep '\[S'` on VISION yields exactly lines 71, 208, 308, 326, 390. VISION cites PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md:2277 and :2750; the file's frontmatter reads `status: SUPERSEDED — superseded-by-decomposition 2026-08-19 ... frozen forensic/history record`, and its successors (PARIPRASHNA_ARC…

*Adopted proposal:* Keep the proposed §15→Appendix C rewrite with repo-relative links and section anchors (S1–S7 as listed, PTA v0.11 cited as forensic record only, fix the :2750 anchor to §14.8/§14.9) and add [S#] markers on every governance-asserting paragraph. For VISION:208 and :390, adopt the C10 language in principle but mark the Q→P crosswalk as "proposed, to be confirmed against the Master Plan's W0 freeze" rather than as settled text, and restate the six maturity states verbatim from the cross-layer research (present → semantically qualified → consumed in an operator → effect traceable → served → incremental value evaluated). For VISION:376, replace "flattened" with "dropped, vertically collapsed or never supplied to synthesis", noting that horizontal spine-bundle flattening per RETRIEVAL_STRATEGY §5 is required, not a failure.

*Answered in v2.0:* Appendix D repo-relative; CURRENT successor set cited; maturity states restored — adopted.


### F-53 · CONTESTED · MAJOR · weakness · v1.1 §3 rows, §6.2, §8 L4 row

**Complexity theatre: no operational definition of discrimination, while served concordance/priority/outlook surfaces are averages that erase it**

*Claim (C8_beyond_acharya_adversary — adversary of the "beyond-Acharya" claim: Barnum effect, complexity theatre, false precision, averaging incompatible schools, LLM fluency as judgment, unvalidatable structural claims, dependence on unproven classical rules; then rebuild the claim at exactly the strength that can be tested.):* More relationships produce more prose, not more discrimination. The vision's own rule against averaging incompatible meanings (VIS:237) is contradicted by what is served today, §3 gives no test that would catch it, and it never states that convention-robustness across five ayanāṃśas is one witness, not five.

*Evidence:* writers/bo_sangati.py:150 'Per (domain × tradition) concordance: mean salience of top-5 signals' → served at platform/src/lib/retrieval/registry/layers/L2_bodha/query_triangulation.ts:33-36 as 'concordance_score (mean salience of the top-5 signals from that tradition's signal pool) … Use to see whether the four classical traditions agree or diverge' — no discordance is computed. platform-mcp/src/tools/phala_outlook.ts:13,22 summary_confidence = mean(anchors[].confidence). platform-mcp/src/tools/kala_views/priority.ts:16-19 priority_score is 'a salience-monoculture — a single opaque scalar'. platform/src/lib/vidhi/ayanamsha_variation.ts:60-74 AYANAMSHA_AGREEMENT_DENOMINATOR = 5; writers/bo_pratijna.py:5 varga_confirmation 'populated as cross-ayanamsha consensus'; bo_anveshana.py:391-392 corroboration boosts rank. VIS:104 'explains why one interpretation or period differs from a plausible …

*Verification:*

- textual: **refuted** (confidence 0.60) — Textual lens. (1) "§3 gives no test that would catch it" misreads the document. §3 itself imposes a complexity-theatre test: "The product must nevertheless show which additional connection changed the understanding. If a simpler competent reading is equally informative, extra complexity has not earned its place" (VISION_v1_1.md:112). §12 operationalizes discrimination: "Explanatory and discriminative value: does the …
- grounding: **stands** (confidence 0.60) — Code citations verify: bo_sangati.py:150 "Per (domain × tradition) concordance: mean salience of top-5 signals" (no discordance term; grep finds none); query_triangulation.ts:33-36 serves it as "agree or diverge"; phala_outlook.ts:22 "summary_confidence = mean(anchors[].confidence)"; priority.ts:16-19 admits "salience-monoculture"; ayanamsha_variation.ts:74 denominator 5; bo_anveshana.py:391-392 rank_composite booste…

*Adopted proposal:* Optional one-clause tightening at VISION_v1_1.md:237, after "count derivative sources as independent corroboration": "— including the same rule applied to the same facts under several conventions (e.g. ayanāṃśas), several discovery primitives over one signal set, or a mean of per-item confidences: each is one witness and no served count, rank or score may present it otherwise." No change to §3 or §8; the discrimination test already lives at :112/:241/:445/:458.

*Answered in v2.0:* §3.4 discriminating-distinction definition — adopted.


### F-54 · CONTESTED · MAJOR · weakness · v1.1 §3, §6.1 item 2, §8 L0 row

**'Authentic depth' rests on rules whose validity is untested and mostly unmodelled; fidelity and validity must be separated**

*Claim (C8_beyond_acharya_adversary — adversary of the "beyond-Acharya" claim: Barnum effect, complexity theatre, false precision, averaging incompatible schools, LLM fluency as judgment, unvalidatable structural claims, dependence on unproven classical rules; then rebuild the claim at exactly the strength that can be tested.):* The rule store has no exception/scope/applicability fields, every extracted rule is stored at confidence 1.0, the yoga catalogue's school is Parāśari only, cancellation is implemented for one yoga, and the only record of a classical claim contradicting a signal is an LLM-judged registry that is 75% silent. A reading can be perfectly faithful and deeply integrated while resting on a rule with zero empirical support; an acharya who ignores that rule from experience would score worse on §3 while being right. A beyond-Acharya claim under an untested rule is a claim about reading skill, not truth, and §3 must say so.

*Evidence:* platform/python-sidecar/brahmagyan/l0_sutravali_extractor.py:8-10 'pure Python regex, ZERO LLM calls. Rules not matching known templates are SKIPPED'; :20 'sutravali_rules — accepted rules (confidence = 1.0 for all regex matches)'; no exception/scope/school column at rule level (grounding R10 §2); query_yoga_catalog.ts:72 stored school parashari only; school variants modelled for Rahu/Ketu exaltation only (migrations/330_bg_dignity_variant_traditions.sql). 08_CLASSICAL_CROSS_REFERENCE/CLASSICAL_ATTRIBUTION_REGISTRY_v1_0.md:14-20: 2,330 attributions — confirms 72, contradicts 36, silent 1,752 (LLM-judged). ga_yoga_writer.py:19-21 cancellation for one yoga. VIS:239 concedes 'a faithful implementation may still have unproven empirical significance' but §3 does not carry it into the benchmark.

*Verification:*

- textual: **refuted** (confidence 0.72) — The finding's core textual claim — that the vision does not separate source fidelity from rule validity and "§3 does not carry it into the benchmark" — misreads the document. The separation is already explicit and load-bearing: §6.1 (VISION_v1_1.md:222-233) lists six distinct links, with item 2 "what a qualified rule means: prerequisites, exceptions, scope, conventions and disagreements" separate from item 6 "what ev…
- grounding: **stands** (confidence 0.82) — Repo evidence confirms the finding's factual base: `platform/python-sidecar/brahmagyan/l0_sutravali_extractor.py:8-10` ("pure Python regex, ZERO LLM calls. Rules not matching known templates are SKIPPED") and `:20` ("confidence = 1.0 for all regex matches"); R10 §2 row bg_rules: no exception/scope/school column at rule level; `query_yoga_catalog.ts:72` "Stored tradition (school): parashari"; `CLASSICAL_ATTRIBUTION_RE…

*Adopted proposal:* Add one sentence after the §3 table (before VISION_v1_1.md:112): "Every dimension above measures fidelity, integration and quality of understanding under §11.1's first two proof obligations; none asserts that a faithfully applied rule is empirically valid, which is a separate obligation (§6.1 item 6, §11.1) and may remain untested for a given rule class." Optionally rename the row "Authentic depth" to "Source fidelity and qualified depth". No second row or per-claim validity-status mechanism is needed at the vision level.

*Answered in v2.0:* §6.1 fidelity vs validity — adopted.


### F-55 · VERIFIED · MAJOR · weakness · v1.1 §3 human clarity row, §7, §8 synthesis row, §12

**LLM fluency can masquerade as judgment: §3 does not constrain what synthesis may add, and claim-checking machinery is off by default**

*Claim (C8_beyond_acharya_adversary — adversary of the "beyond-Acharya" claim: Barnum effect, complexity theatre, false precision, averaging incompatible schools, LLM fluency as judgment, unvalidatable structural claims, dependence on unproven classical rules; then rebuild the claim at exactly the strength that can be tested.):* The vision says retrieval plus fluency is not investigation, but §3 has no rule that every graded, ranked or relational sentence must restate a served row, and no test separating correctness contributed by the model from readability. A blinded panel judging a fluent reading against a terse baseline will reward prose unless the test prevents it.

*Evidence:* CLAUDE.md §N.7 item 1 'Narration is a deterministic restatement of L1-referenced facts'; RETRIEVAL_STRATEGY §3.5 'Tools never summarize generatively' (grounding R4 §5). Code (grounding R8, §2): citation gate never fails the turn (platform/src/lib/pariprashna/pipeline/validation_stage.ts:10-15); receipt emission, typed confidence, interpretation sets, semantic blocks, honest controls are flag-gated default OFF (platform/src/lib/config/feature_flags.ts:314-422); managed prashna_ask is one non-agentic synthesis call over a pre-fetch (platform/src/lib/pipeline/prashna_ask_synthesis.ts:16-27). VIS:457 'verbosity and jargon not rewarded' is a grader instruction, not a design.

*Verification:*

- textual: **stands** (confidence 0.60) — Textually the finding is half right. The document already carries much of the "synthesis constraint": §8 Synthesis row requires "Typed claims, faithful explanation, alternatives, citations" and names the failure "Polished narration conceals an unsupported leap or unavailable validator" (VIS:378); §7.5 forbids improvising "a second persuasive explanation" (VIS:350); §3 requires showing "which additional connection cha…
- grounding: **stands** (confidence 0.80) — Factual basis verified in repo: `platform/src/lib/pariprashna/pipeline/validation_stage.ts:10-15` ("The gate NEVER fails the turn... outcome stays at its PASS default"); `platform/src/lib/config/feature_flags.ts:558-581` sets PARIPRASHNA_SEMANTIC_BLOCKS/HONEST_CONTROLS/RECEIPT_EMISSION/INTERPRETATION_SETS/TYPED_CONFIDENCE all `false`; `platform/src/lib/pipeline/prashna_ask_synthesis.ts:16-27` confirms a "SINGLE, non-…

*Adopted proposal:* (a) In §3, after VIS:112, add one sentence cross-referencing the existing rule rather than restating it: "Every graded, ranked or relational sentence in a reading restates a served, cited row (CLAUDE.md §N.7; §8 Synthesis row); model-originated material appears only as typed hypotheses." (b) In §11.2 "Incremental depth" essential-control cell (VIS:457), append: "fluency ablation — the same served evidence rendered by a deterministic template and by the model, graded blind for correctness and distinctions found; a model advantage counts for depth or discovery only if it traces to a cited row the template omitted, otherwise only for clarity." (c) In §11.2 preamble or §12, add: "Evaluated readings must be produced with receipt, typed-confidence and interpretation-set mechanisms enabled on the evaluated channel; readings produced with them disabled are recorded as not_testable, not as passes."

*Answered in v2.0:* §8 synthesis row; E1 'Today' — adopted.


### F-56 · CONTESTED · MAJOR · gap · v1.1 §3, §11.1, §2.3

**Structural (non-event) claims cannot be validated by outcomes; the vision never says how they can be wrong**

*Claim (C8_beyond_acharya_adversary — adversary of the "beyond-Acharya" claim: Barnum effect, complexity theatre, false precision, averaging incompatible schools, LLM fluency as judgment, unvalidatable structural claims, dependence on unproven classical rules; then rebuild the claim at exactly the strength that can be tested.):* E1's living portrait and most of P01/P02 are structural claims that no event can refute. VIS:445 rightly separates explanatory value from outcome performance but states no validation route, leaving the understanding half of the product unfalsifiable and giving alignment nothing to test E1 against; VIS:89 says disagreement is not proof but does not say resonance is not proof either.

*Evidence:* VIS:122 'an integrated, revisable portrait of distinctive capacities, tensions'; VIS:445 names 'supported, personally specific distinction' with no validation route; VIS:433 excludes emotional response only as evidence of prospective accuracy. PROJECT_ARCHITECTURE_v2_2.md:136-138 (B.4) requires three candidate interpretations and a published falsifier for every significant interpretive claim — for a structural claim the falsifier cannot be an event, so the vision must say what it is.

*Verification:*

- textual: **refuted** (confidence 0.70) — The finding misreads the document as stating "no validation route" for structural claims. The four checks the critic proposes are already in §11.2 (VISION_v1_1.md:455-458, 464): (1)+(2) "Source and calculation fidelity — Passage-to-rule support, conventions, reproducibility ... Wrong/ambiguous source ... cases" (:455); (3) "Expert comparison — Blinded judgments of source fidelity, interpretation, discrimination and m…
- grounding: **stands** (confidence 0.60) — Partially grounded. The critic's central factual claim — VIS "states no validation route" for structural claims — is overstated: §11.2 (VIS:452-466) already lists "Source and calculation fidelity", "Personal specificity … Blinded different-chart and irrelevant-input comparisons", "Expert comparison … Blinded judgments of source fidelity, interpretation, discrimination", and "Understanding and agency … Satisfaction an…

*Adopted proposal:* Do not add a new §3.3. Append one sentence to §11.1 "Explanatory and discriminative value" (VISION_v1_1.md:445): "A structural (non-event) claim is validated, and can fail, only on the source/calculation-fidelity, personal-specificity, incremental-depth and blinded expert-comparison evaluations in §11.2 — never on the subject's agreement or resonance; its published falsifier (PROJECT_ARCHITECTURE B.4) is derivational: the fact, condition or convention change under which the claim would no longer be derivable."

*Answered in v2.0:* §11.1 'How a structural claim can be wrong' — adopted.


### F-60 · VERIFIED · MAJOR · gap · v1.1 §5, §5.1

**Served modalities have no IN/DEFERRED/EXCLUDED disposition; P01–P21 omit daily pañcāṅga, varṣaphala, sāḍe-sātī, kūṭa, vāstu, mundane, āyurdāya and never name the five ayanāṃśas**

*Claim (completeness):* §5 is a consumer-need portfolio, not a modality portfolio; a component cannot tell whether a served method is in scope, deferred, or excluded. The daily/'today' pañcāṅga and transit lookup exists as a page and service asset but is neither in P01-P21 nor distinguished from the daily-omen feed §12.2 rejects; varṣaphala (annual return) and sāḍe-sātī are nowhere; kūṭa/compatibility is unimplemented and neither claimed nor excluded; vāstu is served with no P home; mundane is undeclared; āyurdāya is served, consult-excluded as a mortality class and bound by MP §3.5.C, but §10 says only 'do not guarantee … death'; the five ayanāṃśas - the principal existing robustness mechanism - are never named under P13. Q13 rarity from the Kāla portfolio has no P home (R5 §10).

*Evidence:* V:184-206 (P01-P21), V:212, V:522. R8 §3 modality table; R10 §3 (five ayanāṃśas at ga_positions_writer.py:46-52; ga_tajaka_writer.py:4-15; ga_sade_sati_writer.py:3-6; ga_vastu_writer.py:19-21; praśna 0 rows for natal; no relationship/synastry/organizational writer). platform/src/app/clients/[id]/panchang/page.tsx:1-12 ('Today's tithi/vara/nakshatra are still global'); /panchang/page.tsx; RS:402-418 (service assets answer 'now' queries). grep -rli 'kuta|synastry|ashtakoot|guna_milan' platform/python-sidecar → none. platform-mcp/src/lib/sensitive_capability_class.ts:36-40 MORTALITY_CLASS_CAPABILITIES = ['get_ayurdaya','ganita_ayurdaya_get']; MP:610-613.

*Verification:*

- textual: **stands** (confidence 0.78) — Textually the finding holds. VISION_v1_1.md never contains the strings ayanāṃśa/ayanamsha, pañcāṅga/panchanga, varṣaphala/tājaka, sāḍe-sātī, kūṭa/compatibility, vāstu, mundane or āyurdāya (grep over the whole file returns only §5.1's Praśna/electional/relational/organizational families at V:212-214 and one "death" at V:426). P13 (V:198) speaks only of "different conventions versus errors"; §8 rows (V:374, V:385) say …
- grounding: **stands** (confidence 0.75) — Core gap confirmed: VISION §5 (V:182-208) is a consumer-need table with no per-method disposition; grep of VISION for ayan/sade/tajak/varsha/vastu/ayurdaya/panch/kuta/mundane returns zero hits except V:426 ("Do not guarantee ... death") and V:374 ("conventions"). Governance/code cited by the critic checks out: five canonical ayanāṃśas at ga_positions_writer.py:46-52; MORTALITY_CLASS_CAPABILITIES = ['get_ayurdaya','ga…

*Adopted proposal:* Keep §5 as a need portfolio but (a) add one paragraph after V:208: "Served techniques carry an explicit disposition — in scope, in scope but bounded, horizon (§5.1), or excluded from readings — maintained in a companion modality register that every component reads; absence from P01–P21 is not a disposition." (b) Extend P13's distinction: "...different conventions (including the five computed ayanāṃśas, which are part of chart identity and the first robustness test) versus errors." (c) Add to §10: "Do not emit a date of death or an individualized mortality window under any persona or method (MP §3.5.C); longevity computations exist for research and are excluded from readings." (d) Add to §12.2's daily-omen row: "A user-requested pañcāṅga or transit lookup is a proportionate fact answer (P16), not a feed." (e) Fold Kāla Q13 into P17: "rarity is never importance or event probability."

*Answered in v2.0:* §5 dispositions incl. P22–P24; Appendix B — adopted.


### F-61 · VERIFIED · MAJOR · gap · v1.1 §9 first use, §8 subject row

**No input contract: birth-data quality tiers, time standards/historical clocks, location precision undefined; no such field exists for 'stable core' to compute over**

*Claim (completeness):* §9 promises to establish the stable core across 'the permitted range' and §8 lists 'birth precision, location/time, conventions', but the definition never says what a birth record consists of, what precision tiers exist, how time standards (IST, LMT before standardization, wartime, foreign DST) and place are captured, or that the tier is part of chart identity shown on every reading. The charts table has birth_time TIME NOT NULL, nullable lat/lng and timezone_id, and no precision/source/uncertainty column; the only sensitivity is ±90-min rectification candidates and a serve-time placeholder that explicitly does not model birth-time × ayanāṃśa propagation; the LEL carries three divergent date-confidence vocabularies. E4's 'vary one permitted input', P13, §11.2's 'uncertain input' controls and §12.1's 'bounded sensitivity runs' have no input to vary.

*Evidence:* platform/migrations/001_baseline.sql CREATE TABLE public.charts (birth_date DATE NOT NULL, birth_time TIME NOT NULL, birth_place TEXT NOT NULL, birth_lat NUMERIC, birth_lng NUMERIC, ayanamsa TEXT DEFAULT 'lahiri', timezone_id TEXT; comment :164 'IANA timezone identifier … Sourced from explicit TZ select'); no precision field. grep -rn 'birth_time_uncertain|time_uncertainty|birth_precision|rodden' platform/src platform/migrations platform-mcp/src → nothing. platform-mcp/src/lib/kala_uncertainty.ts:24-30 ('does NOT compute birth-time uncertainty … a documented placeholder convention, not a probability interval'). R6 F04: writers/ph_rectification/__init__.py:141 hardcodes date_confidence='month-exact'. R11 §7: three date-confidence vocabularies (markdown, migration 457, observation records). R7 VA F11 ('timezone, ayanāṃśa, reference frame … are part of identity'); MP:436 (M7 requires ≥A-gra…

*Verification:*

- textual: **stands** (confidence 0.70) — Textual check of VISION_v1_1.md. The document does touch the topic more than the finding admits: V:83 ("what survives plausible input or method changes"), V:214 (each inquiry family's method contract must state "which instant/location or records matter, how those inputs are established"), V:216 ("Pin the meaning and origin of each input"), V:228 ("method identity and input precision"), V:374 (§8 row names "birth prec…
- grounding: **stands** (confidence 0.82) — Factual claims verified in-repo: `platform/migrations/001_baseline.sql:134-159` defines `charts` with `birth_time TIME NOT NULL`, nullable `birth_lat/birth_lng`, `timezone_id TEXT` (comment at `_archive/161_charts_preferred_name_tz_id.sql:16` "Sourced from explicit TZ select") and no precision/source/uncertainty column; grep for `birth_time_uncertain|time_uncertainty|birth_precision|rodden|birth_accuracy` across plat…

*Adopted proposal:* Insert after V:400: "A subject's birth record is a typed input: date, clock time and the time standard actually in force at that place and date (resolved explicitly, never assumed), place with coordinate precision, the source of the time, and a declared precision tier. The tier and source are part of chart identity and travel with every reading; they define the permitted range over which the stable core is established and bound which fine techniques are reported as supported. Changing the record creates a new generation with visible lineage rather than editing the old one. Life-event dates carry one declared confidence vocabulary across entry, storage and evaluation." Leave the tier enumeration to the acceptance portfolio (§12).

*Answered in v2.0:* §9 subject lifecycle; §8 subject row — adopted.


### F-62 · VERIFIED · MAJOR · gap · v1.1 §9, E6, §8 orchestration/subject rows

**Subject and reading lifecycle missing: creation, build/rebuild rights, build duration, unbuilt-asset visibility; a rebuild makes E6's 'same evidence context' irrecoverable**

*Claim (completeness):* E6 promises continuation 'from the same evidence context' and comparison with an earlier reading; §9 promises no silent alteration of earlier answers and deletion reaching caches. The definition never states the lifecycle those promises live inside: who creates a chart and enters consent; who may trigger a build/rebuild (settled lean: super-admin only, guests request); that a chart is unreadable for hours after creation and some layers may be unbuilt/held per chart - and what the consumer sees then; that delete-then-insert with no build archive means a rebuild destroys the prior generation so an earlier reading's evidence context is not reproducible (only frozen claims and the stamp survive); that a birth-time correction or accepted rectification is such a rebuild; and how verified deletion coexists with immutable confirmed-prediction rows (V:420 names the tension, does not resolve it).

*Evidence:* V:172-176, V:410, V:420. PTA:375 (OT-4: rebuild 'destroys the prior build irrecoverably (§N.3, no archive - every open conversation silently drifts)'); PTA:1673-1680 (readings cannot be re-derived); CLAUDE.md §N.3 ('Rebuild REPLACES, never accretes'). platform/src/app/clients/[id]/edit/page.tsx gates on access.canBuild; /clients/new exists; clients/[id]/nirmana/page.tsx exposes BuildControlsBar. R7/ST:96-108 (kala_convergence, kala_activation, kala_obstruction, kala_darshana, kala_bhavishya, kala_field_snapshots all 0 rows for the canonical chart; 'An empty obstruction table must not be narrated as nothing obstructs'); R9 §4 (ka_kshetra 81 failed runs; century EXTERNAL_HOLD; L4 0/9 frozen); ST:187 (6h18 field build). MP:617-622 (verified deletion). platform/src/lib/pariprashna/provenance/stamp.ts:4-5, 66-71 (what survives a rebuild).

*Verification:*

- textual: **stands** (confidence 0.72) — Textually the finding largely holds. E6 (V:172) promises the user can "compare an earlier reading and continue from the same evidence context" with no qualification, and §9 (V:410) promises "Preserve a durable reading identity, material assumptions, evidence/version context". A whole-document grep for rebuild/archive/unbuilt/held/hours/operator/super-admin/build-rights finds nothing: the document never says who creat…
- grounding: **stands** (confidence 0.75) — Every repo claim verified. PTA:375 (OT-4) reads: "a rebuild is expensive, destroys the prior build irrecoverably (§N.3, no archive — every open conversation silently drifts)" and marks build rights "Undecided … [PROPOSED v0.11] (b) super-admin-only"; PTA:1673-1680 records "Because builds are not archived, a past reading cannot be re-derived." stamp.ts:66-71 confirms only the five-field stamp survives. clients/[id]/ed…

*Adopted proposal:* Add §9 subsection "Subject and reading lifecycle" after "After the answer": "A subject enters the instrument by a recorded act (the native, a consenting person, or an entitled intermediary with the subject's consent) that captures the birth record and the consent artifact. Building a chart's evidence is a governed operator act: it is expensive, takes hours, and its failures belong to the operator; who may trigger a rebuild is an open governance decision (current lean: super-admin executes, subjects request). Between creation and completion, and wherever a layer is unbuilt, held or failed for this chart, the consumer surface says so plainly and never lets an empty table read as a finding. A rebuild replaces the evidence generation (delete-then-insert). Today no computed generation is archived; what survives is the frozen record — confirmed claims, their provenance stamp, the conversation and its citations. The product obligation is therefore: any comparison or continuation that crosses a rebuild must say what it can and cannot reproduce, and the platform should pursue the cheap reproducibility mitigations already identified (a per-build manifest; snapshotting the envelopes a turn co…

*Answered in v2.0:* §9 subject lifecycle; §8 orchestration row — adopted.


### F-63 · VERIFIED · MAJOR · gap · v1.1 §7.2, §9, §14

**Language, script and register policy is one sentence; settled mechanisms not cited; corpus is English-translation-only**

*Claim (completeness):* The vision says terms are 'explained inline', 'precise technical meaning must survive translation', and defers 'language rollout'. It never states the settled Sanskrit policy (Sanskrit where it is the substance, always glossed inline, for everyone; never asset ids/layer numbers/table names for anyone - D-14), that reader-facing labels come from a closed lexicon, the LOCKED rule that layer numbers are never shown externally, a transliteration standard, target languages/scripts (the native's languages include Odia and Hindi; the product is English-only with no i18n layer), or that the corpus holds one English translation per verse with Sanskrit mostly null - so any non-English or 'read the original' feature has no corpus basis yet. Renderer, register lint, corpus reader and translation work cannot align without these.

*Evidence:* PTA:2428-2436 (§13.6: 'always glossed inline … This holds for everyone … Never, for anyone - asset ids, layer numbers, table names, artifact acronyms'); PTA:259 (D-14). platform/src/lib/pariprashna/lexicon.ts:9-20 ('HARD RULE: nothing outside this module may ever be rendered as a band/activity label. No internal tool name, asset id … table name, or layer name (L0-L5) may leak'), :27-29 (Sanskrit only as the facet name that IS the object). CLAUDE.md §N.1 ('Never show L0-L5 externally'). grep -rli 'i18n|next-intl|locale|hindi|odia|devanagari|translit' platform/src → nothing. R10 §1 (content_sa nullable, content_en NOT NULL, one translation per verse; Muhūrta-Cintāmaṇi and Tājaka-Nīlakaṇṭhī machine-translated from Hindi OCR with provenance). PTA:3081-3082 (mobile/accessibility PARTIAL).

*Verification:*

- textual: **stands** (confidence 0.60) — Partially misread, partially valid. The register policy is not "one sentence": V:71 states the one-register rule ("Plain language is the default. Technical evidence is available through inspection… preserves the settled one-reading principle. [S3]"), V:320 states "Technical terms are used where they carry meaning and are explained inline… Internal asset names and build diagnostics stay out of ordinary prose" (i.e. th…
- grounding: **stands** (confidence 0.80) — Core evidence verified. The Sanskrit-glossed-inline / never-internal-ids-for-anyone policy is settled and survived PTA's supersession: PARIPRASHNA_ARCHITECTURE_v1_0.md:149 (PPR-04: "one register, zero internal identifiers, Sanskrit glossed inline", citing D-14/D-15) and PTA:2426-2436; lexicon.ts:9-11 hard rule; CLAUDE.md §N.1. No i18n hits in platform/src (only CSS/zodiac icon/generated files). R10:34-36 confirms con…

*Adopted proposal:* Amend V:320 (not V:402) to read: "Technical terms are used where they carry meaning and are explained inline on first use, for every reader, under one consistent transliteration standard that matches the cited sources. Reader-facing labels come from one closed vocabulary; no internal name — asset, layer name or number, table, build diagnostic — ever appears in a reading, for any reader." Add one sentence to §6.1 after item 1: "Today the corpus holds one English translation per verse with the original-language text only partly present; original-language reading and translation alternatives exist only where such text is actually held, and are recorded as a corpus gap, not a display option." Leave V:402 and the V:595 deferral of language rollout unchanged.

*Answered in v2.0:* §9 language; §13 D-14 — adopted as a deferred decision.


### F-64 · CONTESTED · MAJOR · gap · v1.1 §5, §6.1, §6.3, §8 corpus row

**Reading the classical texts is undecided as a consumer feature; the rights obligation has no owner while the licensing record is PARTIAL and contradicts the registry**

*Claim (completeness):* Sources are treated as a drill-down from a reading (E6) and as a research horizon (scholarship laboratory), but the vision never decides whether browsing and reading the corpus itself - by chapter, by theme, the verse behind a rule, with one's own chart as worked example - is a consumer feature, though the tools exist over 16 texts / 10,651 chunks. A consumer reader makes rights load-bearing: §6.1 requires 'rights to use it' in the authenticity chain and §8 lists 'source rights', but no component owns clearance; today the per-text audit is PARTIAL while the live registry declares every text cleared, and Saravali is CC BY-ND.

*Evidence:* 08_CLASSICAL_CROSS_REFERENCE/LICENSING_AUDIT_v1_0.md:5 ('status: PARTIAL - requires operator completion per text'), :8-11 ('hard-blocker for the brahmagyan.texts acceptance gate … must have one row here with status CLEARED'). platform/python-sidecar/brahmagyan/l0_texts.py:69-349 ('license_cleared': True on every entry), :164 ('license': 'cc_by_nd_30'). R10 §1 (audit marks Phaladeepika Kapoor BLOCKED, several PENDING; registry uses a different edition; one translation per verse; OCR-confidence fields). R8 §3 'Classical text reading' row (read_chapter, read_classical_text, search_classical_texts, find_verses_about, list_classical_texts served). V:172-174, V:224-225, V:249, V:375.

*Verification:*

- textual: **refuted** (confidence 0.72) — Textual lens: the finding misreads the document on both halves. (1) "never decides whether reading the corpus itself is a consumer feature": VISION_v1_1.md:200 already lists P15 in the §5 consumer-need portfolio — "Source learning, tradition comparison and discovery | Exact source evidence, qualified interpretation, proposed reconstruction and experimental hypothesis" — i.e. source learning is declared a consumer nee…
- grounding: **stands** (confidence 0.72) — Repo facts check out: LICENSING_AUDIT_v1_0.md:5 is "status: PARTIAL — requires operator completion per text" and :8-11 says every text needs a CLEARED row; l0_texts.py sets "license_cleared": True on all 15 entries (:69,88,...,349) and Saravali is "cc_by_nd_30" (:164) with provenance MEDIUM (:171). The audit is also misaligned with what was ingested, not merely incomplete: it clears Saravali as "B.V. Raman translatio…

*Adopted proposal:* Drop proposed P22 (duplicates P15 at V:200). Amend only the §8 corpus row (V:375): "must preserve or supply" → prepend "A per-text rights record, cleared before the text is served;" and "Failure" → append "; a registry flag says cleared while the clearance record says otherwise." Optionally add to P15's required-distinction cell: "passages served with edition, translation provenance and recorded rights."

*Answered in v2.0:* §5 P23; §13 D-15 — adopted.


### F-65 · VERIFIED · MAJOR · gap · v1.1 §8 portal row, §9, §12.2

**Outputs have no contract: chart rendering, timelines, export, sharing, notes exist in code but the vision only says visuals are 'not prerequisites'**

*Claim (completeness):* The vision says 'useful charts/visuals', that visuals and timelines 'are not prerequisites', that a portable reading 'should carry the relevant evidence and limits', and rejects the 3-D cosmos. It never defines the baseline: that a rāśi/varga chart in North and South Indian styles is a first-class object (it exists), what a daśā/transit timeline shows, what an exported reading contains (the sealed-reading export with the stamp as colophon is designed, not built; conversation export exists in md/json/pdf but is super-admin-only), what a share link may hide (hide_reasoning, hide_methodology exist), that MCP transcripts are structurally not portable (D-05), and what a 'note' on a reading is. A chart-first product (PA J.5) whose definition never mentions the chart drawing will be aligned by guesswork.

*Evidence:* platform/src/components/charts/RasiChartSVG.tsx:1-10 (style?: 'north' | 'south'); platform/src/app/share/[slug]/page.tsx:1-20 (conversation_shares with revoked_at, expires_at, hide_reasoning, hide_methodology); platform/src/app/api/conversations/[id]/export/route.ts:1-15 (VALID_FORMATS = ['md','json','pdf'], super_admin only); platform/src/app/clients/[id]/timeline/page.tsx (life-event timeline). PTA:334 (A-47 'The reading returns as an artifact … the natural home of the D-16 stamp as a colophon' - proposed, unbuilt); PTA:250 (D-05 cross-channel transcript portability dropped); R8 (reading_notes_get on MCP). PA:985-991 (J.5 chart-first reveal).

*Verification:*

- textual: **stands** (confidence 0.60) — Textually the core gap is real but the finding overstates it. Confirmed omissions: the document never mentions the chart drawing as an object (no rāśi/varga figure, no style); the only references are generic — V:379 "useful charts/visuals", V:402 "Chart visuals, tables and timelines serve comprehension; they are not prerequisites", V:320 "a timeline, comparison or graph should be inspectable", V:352 "focused relation…
- grounding: **stands** (confidence 0.62) — Code evidence verifies: `platform/src/components/charts/RasiChartSVG.tsx:8` (`style?: 'north' | 'south'`); `platform/src/app/share/[slug]/page.tsx:18-23,49-50` (conversation_shares with revoked_at/expires_at/hide_reasoning/hide_methodology, though hide_* is gated by `selectiveShareEnabled`); `platform/src/app/api/conversations/[id]/export/route.ts:10,18,63` (md/json/pdf, super_admin only); `clients/[id]/timeline/page…

*Adopted proposal:* Insert a §8 row after "Portal and Paripraśna": "| Rendering, export and sharing (chart figures, timelines, portable readings, notes) | \"I can see my configuration, see time laid out, take a reading with me, and show it to someone I choose.\" | Rāśi and varga charts as inspectable figures in the reader's preferred style, drawn from the same computed facts the reading cites; timelines that place periods, windows and open claims on one axis with their stated uncertainty; a portable reading carrying its claims, citations, limits and provenance stamp; a share that is revocable, expiring, may withhold method detail but never presents a cleaner reading than was given; the person's own notes kept distinct from the instrument's claims. Portability applies to Paripraśna readings; MCP client transcripts are not recoverable by the instrument. | A figure disagrees with the reading's facts; an export drops limits or provenance; a share exposes another subject's data; a note is later read as evidence. |" Amend V:402 to: "Chart figures, tables and timelines are first-class ways to inspect the same evidence a reading cites; they are never prerequisites for asking a question and never a substitute …

*Answered in v2.0:* §8 rendering/outputs row — adopted.


### F-67 · CONTESTED · MAJOR · contradiction · v1.1 §2.1, E6, §6.5, §7.5, §14

**'No intelligence tiers' vs 'research facilities add operators': under D-15's own test an operator that changes what is produced is a tier**

*Claim (internal and governance contradiction hunter):* The vision asserts one standard of intelligence for everyone and simultaneously says research facilities 'add operators', gating them by facility rather than by data. PTA D-15's test is explicit — a tier changes what gets produced for the same chart and question; an affordance discloses more of one thing produced — so an operator set unavailable to ordinary users is a tier by definition, and §7.5 already lists 'What survives if that method is excluded?' as a consumer question. Resolvable by pinning that entitlement governs data (other subjects, cohorts, hidden-outcome partitions, model promotion), never operators on one's own chart, and that research adds obligations on the researcher rather than a second engine. None of the operators exists yet, so nothing must be un-built.

*Evidence:* VIS:71 'not intelligence tiers. Everyone entitled to a reading receives the same standard'; VIS:174 'Research facilities add operators and study controls, not a higher-quality consumer tier'; VIS:269 'Cohorts, protected data access and model promotion need separate authority'; VIS:350 consumer asks 'What survives if that method is excluded?'. PTA:260 D-15 'No audience tier. No depth parameter. Acharya-grade by default, always'; PTA:2290-2311 three rules ending 'a tier changes what gets produced; an affordance is progressive disclosure over one thing that was produced'; PTA:2320 signature ask(chart_id, question); CLAUDE.md:284 build-layer twin. Reality: grep -rliE '\bablation\b|\bblinded\b' platform/src platform-mcp/src platform/evals returns nothing; no method-exclusion or reading-vs-reading diff operator exists. Resolvable tension.

*Verification:*

- textual: **stands** (confidence 0.62) — Textually the finding is accurate but overstated. VIS:174 does say "Research facilities add operators and study controls, not a higher-quality consumer tier" — a literal reading makes some operators facility-gated, and under PTA D-15's test (a tier changes what is produced) an operator on one's own chart withheld from ordinary readers would be a tier. The document never states the resolving rule (entitlement governs …
- grounding: **refuted** (confidence 0.62) — The "contradiction" does not hold on the texts. D-15's own rule 3 (PTA:2298-2301) permits gating "only by entitlement to the underlying data", and VIS:269 gates exactly that ("Cohorts, protected data access and model promotion need separate authority") — not operators on one's own chart. VIS:350 already gives the consumer "What survives if that method is excluded?" and "What would help us settle this?", and VIS:172 g…

*Adopted proposal:* Replace VIS:174's second sentence with: "Every operator this document names on a person's own chart — show the relationship, exclude a method, vary a permitted assumption, compare two states, ask what would settle it — is available to anyone entitled to that chart. Research facilities add study controls and access to other subjects' data, cohorts and hidden-outcome partitions under separate authority (§6.5); they never add a higher-quality reading or a second engine." Optionally append to VIS:71: "(a tier changes what is produced for the same chart and question; inspection only discloses more of what was produced) [S3]".

*Answered in v2.0:* §1.4 research-operators sentence; §7.1 — adopted.


### F-68 · VERIFIED · MAJOR · contradiction · v1.1 §5, §7.1, §8 L3 row

**§7.1's 'useful partial answer' permits the softened claim B.12 forbids; missing-vs-computed-absence applied only to Kāla**

*Claim (internal and governance contradiction hunter):* Both texts forbid invention, but the vision emits the gap-consuming conclusion in weakened form ('how that limits the conclusion') where PA B.12 requires the claim to be withheld ('name the gap and pause', never 'likely'). The vision states the missing-computation-versus-computed-absence rule only for the L3 row, although the stocktake found five Kāla output tables at zero rows for the canonical chart — the exact condition under which a 'limited conclusion' becomes 'probably nothing obstructs'. The completeness-receipt mechanism that resolves this already exists.

*Evidence:* VIS:306 'The system can stop with a useful partial answer, showing what remains unexamined and how that limits the conclusion'; VIS:182; VIS:371 only 'missing coverage looks like relief'. PA:180-182 B.12 'explicitly flags the gap and waits for resolution. Interpretation shall not paper over a missing fact with "likely" or "probably" — it shall name the gap and pause'. ST:108 'An empty obstruction table must not be narrated as "nothing obstructs this period" ... Missing computation and computed absence are different results'; ST:96-104 kala_convergence/activation/obstruction/darshana/bhavishya at 0 rows. Mechanism: RS:222-227 receipt served/empty/dark; platform/src/lib/retrieval/registry/layers/reading_checklist.ts:1-52 served/empty/not_computed/not_joined/salience_floored. Resolvable tension.

*Verification:*

- textual: **stands** (confidence 0.60) — Half of the finding misreads the text. VIS:306 ("showing what remains unexamined and how that limits the conclusion") does not state that a gap-consuming claim may be emitted in weakened form; "limits the conclusion" is at least as naturally read as scoping (withholding) as softening, and the document nowhere licenses "likely/probably". Multiple passages already forbid the softened claim: VIS:182 "explicit supported …
- grounding: **stands** (confidence 0.60) — Partially grounded, overstated. PA B.12 (PROJECT_ARCHITECTURE_v2_2.md:180-182) is scoped to L2 work consuming a Completeness-Guarantee cell marked TBD/EXTERNAL_REQUIRED/MISSING: "name the gap and pause". VIS:306 addresses budget/Top-K truncation, and "showing what remains unexamined and how that limits the conclusion" is scope-limitation, not "likely/probably" papering; VIS:182 already says "never invention". So the …

*Adopted proposal:* Keep VIS:306 and append one sentence: "A partial answer withholds, rather than softens, any claim that would consume an unexamined, unverified or uncomputed input, and names the gap and what would resolve it (PA B.12), reusing the existing completeness-receipt states." Move the missingness rule from the L3 row only to the §8 table preamble (before VIS:366): "For every component, 'not computed' and 'computed absent' are different results; an empty or unbuilt table is never narrated as 'nothing found'." Retain VIS:371 as the Kāla instance.

*Answered in v2.0:* §7.2 pause rule — adopted.


### F-69 · CONTESTED · MAJOR · weakness · v1.1 §2.2, E1, §2.3, §9, §12, §8 atlas row

**The living atlas and 'a saved prior reading can guide retrieval' re-open the B.1 laundering path; J.5 chart-first ordering ambiguous**

*Claim (internal and governance contradiction hunter):* An atlas that persists 'supported relationships' and a prior reading that 'can guide retrieval' are stored interpretations feeding later readings — the B.1 laundering PTA built the prior_reading firewall against — and the atlas is functionally the successor to the UCN as parent narrative, which the vision neither admits nor denies while naming 'a new narrative authority' as its failure mode. Separately, §2.3 makes chart-first and goal-conditioned inquiry peers inside a question-led architecture, whereas PA J.5 makes chart-first the default with goal-calibration post-reveal; without that ordering the §2.3 'not laundered' rule is unenforceable. The vision has the right guardrails in outline but not the operative sentences.

*Evidence:* VIS:126 'living atlas ... navigable set of supported relationships'; VIS:412 'A saved prior reading can guide retrieval but cannot serve as independent corroboration of itself'; VIS:492 'does not become a self-confirming biography'; VIS:386 failure 'A new narrative authority'; VIS:91 'chart-first exploration remains available ... Goal-conditioned inquiry is also available'; VIS:45/218/282 question-led. PTA:1700-1704 'A past reading is not an L1 fact ... prior_reading ... must never satisfy an acharya-floor requirement'; PTA:1712-1716 floor_gate enforces, 'Zero production callers'; platform/src/lib/pariprashna/recall/index.ts:4-8 prior_reading weakest grade; PTA:2792-2796 'Synthesis is stateless with respect to the user's reactions'; MP:178 n=1 overfit; PA:304 'UCN is the mother document every Domain Report cites'; PA:316-317; PA:985 J.5 'Chart-first reveal across all domains; goal-calibr…

*Verification:*

- textual: **refuted** (confidence 0.65) — Textually, the vision already carries the operative guardrails the finding says are missing. (1) B.1 laundering: VIS:124 "A prior summary is navigation into evidence, not a replacement for it"; VIS:412 "A saved prior reading can guide retrieval but cannot serve as independent corroboration of itself"; VIS:273 "repeated readings must retain their dependence; they cannot silently become additional independent corrobora…
- grounding: **stands** (confidence 0.60) — Citations verified: PTA:1701-1706 (prior_reading weaker than verified, never satisfies floor), PTA:1710-1716 (floor_gate built, zero callers), recall/index.ts:4-7, PA:985 J.5. But the headline is overstated. (1) "Guide retrieval" is exactly what PTA recall does (rank prior conclusions, surface as prior_reading citations); VIS:124 "A prior summary is navigation into evidence, not a replacement" and VIS:412 "cannot ser…

*Adopted proposal:* If retained at all, reduce to one sentence appended to VIS:126: "Atlas entries are prior readings in the recall sense (PTA §11.5): they point to evidence and never enter grounding or satisfy a whole-chart floor item; the Unified Chart Narrative's parent-document role (PA §C) is superseded by claim-level parentage only upon ratification of this definition." Leave VIS:91 unchanged; optionally add "by default" after "remains available" to make the J.5 ordering explicit.

*Answered in v2.0:* §1.3; §2.3 — adopted.


### F-24 · VERIFIED · MINOR · weakness · v1.1 §7.2, §8 preamble, lexicon

**Sanskrit layer names and Paripraśna/Praśna used without gloss; transliteration inconsistent**

*Claim (senior Jyotish acharya (Parāśari, Jaimini, KP, Tājaka, Nāḍī, Praśna, Muhūrta, Upāya)):* The vision mandates inline gloss of technical terms and governance requires Sanskrit 'always glossed inline, for everyone', yet Brahmagyan, Gaṇita, Bodha, Kāla, Phala, Mīmāṃsā, Paripraśna and Praśna appear unglossed; 'Brahmagyan' is Hindi-style romanization beside IAST (IAST: Brahmajñāna; the locked lexicon spells it Brahmagyan and the vision should adopt that knowingly or gloss it). Usages are otherwise correct (Mīmāṃsā for evaluation is a defensible extension worth one clause; Paripraśna correctly distinguished from horary Praśna).

*Evidence:* V:320 'Technical terms are used where they carry meaning and are explained inline'; V:368-373 layer names unglossed; V:214 Paripraśna vs Praśna. PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md:2428-2436 (Sanskrit 'always glossed inline ... for everyone'); :246 (D-01 Praśna reserved for horary); 00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md:40-42 (locked external lexicon 'Brahmagyan · Gaṇita · Bodha · Kāla · Phala · Mīmāṃsā').

*Verification:*

- textual: **stands** (confidence 0.60) — Textually confirmed: VISION_v1_1.md:368-373 lists "L0 — Brahmagyan … L5 — Mīmāṃsā" and :214/:324/:379 use Paripraśna/Praśna; a whole-document grep finds no gloss of any of the six names (no "calculation", "understanding", "Brahmajñāna", etc. attached to them). The §8 first-person "contribution" quotes describe each layer's function but never explain the Sanskrit word, so they do not already cover the point. The mixed…
- grounding: **stands** (confidence 0.70) — Evidence checks out line-exact. VISION_v1_1.md:320 states "Technical terms are used where they carry meaning and are explained inline"; lines 368-373 use Brahmagyan/Gaṇita/Bodha/Kāla/Phala/Mīmāṃsā with no gloss; line 214 uses Paripraśna vs Praśna unglossed; PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md:2428-2436 requires Sanskrit "always glossed inline" and "for everyone"; L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md:40-42 locks the …

*Adopted proposal:* Add to §8's preamble: "The six layer names are the locked external lexicon and are Sanskrit, glossed once here: Brahmagyan (IAST Brahmajñāna) — foundational knowledge: texts, rules, reference; Gaṇita — calculation; Bodha — understanding: the synthesized reading of one chart; Kāla — time: periods and transits; Phala — result: what may manifest; Mīmāṃsā — examination: what the instrument said and whether it held. The chat is Paripraśna, respectful inquiry (Gītā 4.34); Praśna is reserved for the horary method (D-01)." Keep the locked spelling "Brahmagyan" as primary throughout; cite the gloss rule to PARIPRASHNA_ARCHITECTURE_v1_0 / DECISION_REGISTER rather than the superseded PTA.

*Answered in v2.0:* Appendix A; PPR-04 inline gloss — adopted.


### F-50 · VERIFIED · MINOR · weakness · v1.1 §5, §8, §9, §12, §13.1

**Numbering, ID schemes, table forms and counts internally inconsistent**

*Claim (writing, structure and clarity):* §9's subsections are the only unnumbered ### headings; five parallel ID schemes (E, P, S, Q/D, plus unlabelled §12.1/§12.2/§13.1 rows) have no index; §5's 'Consumer need' column switches from topic labels (P01-P16) to quoted questions (P17-P21); §12's third-column header 'Why it is insufficient' does not describe rows 4-5 ('Recommended center/companion'); the additions are counted as seven, four and five in different places; the 'missing coverage looks like relief' rule is stated only for the L3 row; and line 208 under-describes Q13-Q18 as 'detailed temporal tests'.

*Evidence:* Unnumbered headings VISION:396, 404, 408, 414 vs numbered 1.1, 2.1, 6.1, 7.1, 11.1, 12.1, 13.1; §5 rows VISION:186-206 (P17-P21 quoted); §12 header VISION:487 vs cells VISION:492-493; 'seven distinct directions' VISION:500 vs 'not four automatically new services' VISION:392 vs five items at VISION:589 vs 'the fourth and fifth approaches' VISION:496; L3-only honesty rule VISION:371 (grounding/R7_l3_value_and_stocktake.md:141); VISION:208 vs Q13-Q18 content (grounding/R5_l3_master_plan.md:114); table shapes verified by awk: 8 tables, no column-count mismatches.

*Verification:*

- textual: **stands** (confidence 0.80) — Most textual claims confirmed: §9's four ### headings (VISION:396,404,408,414) are the only unnumbered ones apart from the ID-labelled E1–E6; §5 rows P17–P21 (VISION:202-206) switch to quoted questions while P01–P16 use topic labels; §12's third-column header "Why it is insufficient as the product definition" (VISION:487) is contradicted by rows 4–5 reading "**Recommended center**"/"**Recommended companion capability…
- grounding: **stands** (confidence 0.80) — Every factual anchor checks out against the document: §9's four ### headings (VISION:396,404,408,414) are the only unnumbered ones; P17–P21 switch to quoted questions (VISION:202-206); §12's third column is headed "Why it is insufficient as the product definition" (VISION:487) while rows 4–5 read "Recommended center"/"Recommended companion capability" (VISION:492-493); "seven distinct directions" (VISION:500) vs "not…

*Adopted proposal:* Keep the critic's structural fixes (number §9 as 9.1–9.4; ID §12.1 rows A1–A7, §12.2 rows X1–X8, §13.1 questions CC-1..CC-6; uniform topic labels for P17–P21; re-head §12 column 3 "Decision" and reword rows 1–3 and 6 as "Supporting instrument — ..."), but correct the count sentence to match §14: after §12.1 add "Five of the seven (A1–A5: living atlas, question compass, stable-core/uncertainty resolution, controlled comparison, observation briefs) become cross-cutting responsibilities in §8; A6 (scholarship/contrastive observatory) joins method-native expansion in the long-term horizon; A7 (selective, quiet continuity) is an experience rule in §9." Change VISION:392 from "not four automatically new services" to "not seven". Promote "missing computation is not computed absence" (ST:108) to a global invariant in §8's preamble, applying to retrieval, chat, MCP and portal, and remove it from the L3-only cell. Rewrite VISION:208 as: "The existing Kāla Q01–Q18 (temporal, rarity, disagreement, robustness, continuity, open-investigation and lookup/cross-chart questions) and D01–D10 cases remain the detailed test suite beneath this portfolio; their W0 freeze [S4] survives subordination to P0…

*Answered in v2.0:* consistent numbering — adopted.


### F-57 · VERIFIED · MINOR · elevation · v1.1 §11.3, §3

**Proving journeys are all natal, shaped to the native's own questions, and contain no null case**

*Claim (C8_beyond_acharya_adversary — adversary of the "beyond-Acharya" claim: Barnum effect, complexity theatre, false precision, averaging incompatible schools, LLM fluency as judgment, unvalidatable structural claims, dependence on unproven classical rules; then rebuild the claim at exactly the strength that can be tested.):* VIS:114 makes ordinary results, ties and inability to conclude valid outcomes, but no benchmark journey tests that; all three are natal and two are the native's own recurrent questions, and the canonical chart is not excluded from scoring — inviting tuning to one biography, which the cited L3 study explicitly warns against.

*Evidence:* VIS:477-479 journeys 1-3; VIS:481 'not readings of the native's chart' but the question shapes are the native's and there is no exclusion of chart 482012f1… from scoring; L3_KALA_VALUE_ARCHITECTURE VA:388 'Do not tune to the canonical chart's lived outcomes and then call that prospective validation' (grounding R7 §5); cross-layer study SRC:35 'five contexts ≠ five subjects; single chart' (R6 §4).

*Verification:*

- textual: **stands** (confidence 0.70) — Textually the finding mostly holds. §11.3 (VIS:477-479) lists three journeys, all natal; the non-natal case is explicitly deferred to "a future non-natal case" (VIS:483). VIS:481 says "not readings of the native's chart", but nowhere in the document is the canonical chart excluded from scoring or reserved for development (grep for "482012f1", "canonical chart", "development only", "non-native" returns nothing), and V…
- grounding: **stands** (confidence 0.70) — Core claims check out. VIS:114 makes ordinary/tie/inconclusive outcomes valid; §11.3 (VIS:473-483) lists three natal journeys plus "evidence-poor or premise-false variant and a precise lookup control" — no null case. Journey 2 self-describes as "the user's central L3 expectation" (VIS:478). The cited study text is verbatim: "Include multiple synthetic/consented chart fixtures chosen to expose non-Aries frames ... gen…

*Adopted proposal:* Add to §11.3 after journey 3: "4. Ordinary result: 'Does my chart distinguish between these two options?' / 'Is there anything unusual here?' on a chart-and-question pair pre-registered as ordinary, where the correct answer is a tie, an unremarkable result or 'the evidence does not settle it' (§3, VIS:114). A reading that manufactures a distinction fails." Then amend VIS:481 to: "These are test prompts, not readings of the native's chart. Each journey runs on at least one consented or synthetic non-native chart; the canonical chart (482012f1…) is a development fixture and is excluded from any beyond-Acharya scoring [S4/VA:388]. Each must include an evidence-poor or premise-false variant, a precise lookup control, and the blinded different-chart control already required in §11.2 (Personal specificity)."

*Answered in v2.0:* §11.4 null cases — adopted.

