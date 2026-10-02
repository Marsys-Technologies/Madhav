---
artifact: MADHAV_DATA_PLANE_VALUE_ARCHITECTURE
canonical_id: MADHAV_DATA_PLANE_VALUE_ARCHITECTURE
tier: 2
kind: instance
chain: ELEVATION_DERIVATION_CHAIN_v1_0.md
inherits: [00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md]
produces: [LAYER_DEFINITION_AND_STRATEGY_TEMPLATE, "six layer instances L0-L5"]
version: "FINAL"
status: SEALED        # was CURRENT; sealed 2026-09-25 (native decision 13)
seal:
  state: SEALED
  sealed_on: 2026-09-25
  sealed_by: "Native — NATIVE_DECISIONS_2026-09-25_v1_0.md v1.4, decision 13"
  signed_under: "Native ruling 9 — a review happened; the reviewer, the native or the session may sign"
  seal_record: 00_ARCHITECTURE/briefs/nirmana/ELEVATION_CHAIN_SEAL_2026-09-25_v1_0.md
  reopen_rule: >
    A sealed document is not edited in place on a session's own judgement. It reopens only by native
    ruling, and the reopen is recorded in this changelog as such, with the ruling named. Correcting a
    typo is not a reopen; changing an obligation, a contract, a count or a scope is.
  still_open_below_the_seal: ["layer instance (L0-L5)", "asset template", "asset instance (per-asset briefs)"]
  review_backing: "reviews/REVIEW_DATA_PLANE_FINAL_v1_0.md — verdict REJECT on the version reviewed; all 22 findings discharged in the third FINAL change below, 1 restated and 1 withdrawn by native ruling 11. Predecessor review reviews/REVIEW_DATA_PLANE_v3_0.md (REJECT) audited finding-by-finding in the same pass."
produced_on: 2026-09-25  # FINAL elevations + review fold; v3.0 realignment 2026-09-24; v2.0 2026-09-13
session_id: MADHAV-DATA-PLANE-FINAL-20260925  # v2.0 origin session was MADHAV-DATA-PLANE-V2-20260913
parent_definition: ../../MADHAV_PRODUCT_DEFINITION_FINAL.md  # v3.0 superseded 2026-09-24
source_revision: 45120d72dd4e968234d5e77cc1d665e74bc595d6      # repo revision the source research in §15 was read at
application_source_base: 731e311f0b8f5f84db2f152b93951e1d3d50d89a  # application code base the [S0x] source findings were read at
role: "Consumer and Jyotish-domain data-plane definition, target value architecture and preserve-first elevation master plan; basis for subsequent layer and asset proposals."
authority: "ADOPTED. This document governs the data plane: the parent definition §1.3 names it as the data plane's governing artefact, CAPABILITY_MANIFEST carries it as CURRENT, and the L0 layer instance is derived from it. Adoption is of the architecture; it is not implementation authority, and it does not authorize application, database, deployment or model changes."
scope: "L0-L5 assets, supporting/non-writer capital and data-to-answer interfaces; no application, database, deployment, model activation or campaign-state changes."
lineage: "Successor planning synthesis of the conversation-issued earlier data-plane proposal, v1.0 deep-inquiry companion and L3 cross-layer research. No repository copy of the earlier cohesive inline plan was located; it is not presented as a recoverable verbatim predecessor."
companions:
  - MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md            # scoped asset membership; provisional per §1.2
  - LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md                   # the tier-3 template this document produces
source_review_record: MADHAV_DATA_PLANE_V2_REVIEW_RECORD_v1_0.md     # the SOURCE research record: inspected files, [S0x] findings and their limits
document_reviews:                                                    # independent reviews OF this document
  - reviews/REVIEW_DATA_PLANE_v3_0.md      # REJECT, 2 BLOCKER + 10 MAJOR + 11 MINOR; 10 folded at FINAL, 6 partly, 5 outstanding
  - reviews/REVIEW_DATA_PLANE_FINAL_v1_0.md  # REJECT, 2 BLOCKER + 9 MAJOR + 10 MINOR; all folded by this revision, 1 restated and 1 withdrawn by native ruling 11
changelog:
  - "REOPENED AND AMENDED (2026-09-26, native ruling — NATIVE_DECISIONS_2026-09-25 decision 16). The seal's reopen rule invoked for the first time, and by a finding from below rather than a governance pass: §4.1 rule 1's identity DETECTOR is corrected. It required `count(DISTINCT canonical_id)` across entity classes and therefore reported FAIL on `brahma_ontology`'s 741 rows, which satisfy their own live constraint `UNIQUE (entity_class, canonical_id)` — 741 distinct composites, zero duplicates. Found by the first tier-4 pilot brief. The RULE is unchanged; the detector now tests the authority's declared key, and a consumer resolving on a partial key is the defect rule 2 already names. Native ruling: keep the composite key and make resolvers class-aware. No other clause touched."
  - "SEALED (2026-09-25, native decision 13): tier 2 of the elevation chain is sealed, together with tier 1 and the tier-3 template. What remains open below it is the layer instance, the asset template and the asset instance. No content changed in this entry — the seal is a governance state, not an edit."
  - "FINAL (elevated in place, 2026-09-25, third change — REVIEW_DATA_PLANE_FINAL_v1_0 folded under native rulings 9/10/11 of NATIVE_DECISIONS_2026-09-25 v1.2): (a) NATIVE RULING 11 — `Domain correctness` is NOT a data-plane obligation. This plane is data engineering, mathematical computation and faithful carriage; whether the astrology is RIGHT is formed above it, in the reasoning layer. The `ten` obligations of §13.3 are therefore correct and now carry their reason, so no later session `corrects` them to eleven; §12.2's Domain correctness row is replaced by a SOURCE CARRIAGE row that tests transmission and reproduction (cited passage present, witness disagreement carried unresolved, second derivation reproduces) and reaches no astrological verdict. (b) NATIVE RULING 10 — the medical/mortality exclusions stay removed; §5's last hook for them (`Horizon qualification cannot bypass exclusions`) is deleted. (c) THE PLANE BOUNDARY, corrected per the native: the retrieval and conversation planes are not built yet, so §1 no longer promises DEMANDS that have no recipient — it states plainly that this document legislates their data-facing obligations for now, and §8 plus two §12.2 rows are marked [TRANSFERS], moving to those planes' artefacts unchanged when they are elevated. (d) THE SYNERGY TERM, previously assigned to nobody: new §3.5 defines it in the native's own terms — to the naked eye a layer is the sum of its assets and services, but value also arises from those assets working together, and that delta IS the synergy, which must be tracked — names the four plane-level seams that carry it, names cross-layer ablation as its instrument, and forbids a number where no harness exists; §12.2 gains a Synergy row and §13.3 a required element. (e) Contract repairs: DP02 no longer asks L0 for a per-chart record (tested-and-passed clauses move to DP05, where the chart-scoped ledger lives); §3.4's competing-readings row cites DP02 for the source witness it claimed DP06 carried; DP08 and §6.4 gain the present interval and its predecessor, so P24 has a contract and not only an obligation. (f) §13.3 is nine elements and says so (1a kept rather than renumbered, because the template and the L0 instance cite these numbers); item 6 gains the §3.4 binding the parity test needs. (g) Residue swept: `permitted` and `purpose-qualified` given referents or removed, §4.1's duplicated Sun paragraph and its already-taken authority decision cut, the lost-doctrine reconstruction clause replaced (parent §13 forbids reconstruction), §14's v2.0 delta table cut to its closing paragraph, `the review record` split into the source record and the document reviews, the unlocatable six-view and previous-Kala-plan references made self-contained or removed, frontmatter dates and adoption state corrected. Signed under native ruling 9: reviewed by an independent fresh-context session, folded and signed in the same session."
  - "FINAL (elevated in place, 2026-09-25, native-directed, second change): §12.2 gains the reference-layer carve-out — for a layer whose assets are knowledge authorities (L0), the individual term is fidelity, not ablation; ablation there verifies consumers and never dispositions the asset. Raised by the native against the L0 instance: judging perennial knowledge by today's readers would retire the tradition one unread chunk at a time."
  - "FINAL (elevated in place, 2026-09-25, native-directed): §4.1 raised from an illustration (the Sun problem) to a governing principle — the CONTROLLED VOCABULARY. Every entity, concept, method, convention, unit and event class has exactly one canonical identifier and one closed alias set, owned by L0; the closed set is the only permitted surface for that thing, internally and externally; an unlisted name is an error to raise, never a synonym to guess; code-side representations are generated from the authority with a release id and digest and joined to it by a parity test, so a hand-maintained mirror is a forbidden second authority; external inputs are typed to the set. Detectors named. Scope is all sixteen entity classes, not graha alone. Wired into §3.4 (the alias set is what lets one identity render two ways), §12.2 (a test row) and §13.3 (a required layer-plan element). Version unchanged by native instruction: this is an elevation of a FINAL document, recorded as such."
  - "FINAL (2026-09-24): review returned REJECT on two blockers, both orphans of the surgical realignment: §12.1 still carried 'Excluded medical/mortality requests must remain excluded through every intermediary', re-imposing the exclusion the parent removed and contradicting this document's own V12; and four V-journey P-citations were stale under FINAL numbering while the text asserted they were current. Both blockers fixed. CORRECTED 2026-09-25: this entry originally claimed all 21 findings were folded; REVIEW_DATA_PLANE_FINAL_v1_0 checked each against the file and found 10 fully folded, 6 partial or folded in a weaker place, and 5 not folded at all. The remainder are folded by the third change above. Notable: §3.4's mapping cited DP05 for clauses that PASSED when DP05 carries only failing clauses, and cited DP17 (a second computation) for competing readings; DP02 amended to carry school/tradition and tested-and-passed prerequisites; a temporal/manifestation row added, without which no L3 or L4 acharya rendering was derivable. P24 given a real obligation beneath its V-row. The storage-separation clause restored - without it OFF was ambiguous between deselect and rebuild. Parent obligations that had no data obligation here added: narration-vs-arithmetic verification, and the rebuild chronology-reset leak."
  - "3.0 (2026-09-24): Realigned to MADHAV_PRODUCT_DEFINITION_FINAL, which superseded v3.0 the same day. ELIMINATED: V12 excluded-outputs (it enforced the death/illness/fertility exclusions FINAL removed, and contradicted P23); the four life-event purpose paths, replaced by FINAL's single switch; voluntary observation briefs and the cross-population research framing in DP14 and V11; DP18 future-qualification; PPR-/C3 compliance scaffolding; `permitted` where the cleanse left it without a referent. ADDED: the presentation contract (§3.4) — the data obligations that exist because FINAL promises one analysis rendered at two levels of exposed detail; āyurdāya as a domain obligation; V13 for FINAL's new present-tense need P24; LEL switch semantics; binding of the layer stories and the layer-plan template to FINAL §14's ten obligations; ablation as the per-asset scoring method; learning's defined output; the inherited definition of `qualified`, used 71 times here and previously undefined. RETAINED deliberately: DP01-DP17, the eight-disposition hierarchy, the five edge types, the six evidence states, §13.3's eight layer-plan elements, `a citation with no declared use is not a contract`, and `lack of a caller in a bounded search is not redundancy`."
  - "2.0: Aligns the entire data plane to final Product Definition v3.0; adds consumer-to-asset contribution, qualified Jyotish operators, cross-layer use contracts, source-grounded preservation dispositions, delivery obligations and upstream-first execution design. Proposed, not implemented or canonically adopted."
---

# Madhav Data Plane — Value Architecture and Elevation Master Plan

## 1. The definition

**The data plane is the connected, qualified astrological basis from which Madhav can explain a person's chart, investigate its implications, identify what may activate over time, distinguish possible manifestations, and account for what it claimed.**

Its product is not a collection of tables or six independently impressive layers. Its product is a usable body of knowledge: the right fact, relationship, exception, temporal condition or contrary indication can be found, interpreted in its proper context, joined with other relevant evidence and carried faithfully into the person's reading.

The retained six-layer architecture is appropriate. The main elevation is in semantic fidelity, domain coverage, relationships and actual utilization—not a replacement architecture. L0 remains the global foundation; L1–L5 retain principally chart/subject-scoped responsibilities. Legitimate shared models, services and evaluation resources keep their correct semantic owners. No seventh layer, universal truth graph or new parallel registry is proposed.

The ambition is inherited from the product definition and is specific: **the data plane exists so that
computation can reach a depth and interconnection existing astrological software does not reach, and so
that artificial intelligence has something worth reading across.** Conventional Jyotish software computes
each element on demand and presents it — a varga when asked, a daśā table when asked. This plane computes
the whole estate *and the relationships between its parts*, and holds them together so a reasoning layer
can find what connects. Neither half is the product: an estate nobody can interpret is a warehouse, and a
model without it has nothing to reason over. Every obligation below exists to serve that join — more
relevant concepts and chains examined correctly, more meaningful alternatives distinguished, more precise temporal discrimination where earned, and fewer important omissions. This is a design ambition, not a demonstrated claim of astrological or predictive superiority. Engineering verification, interpretive value and empirical outcome performance remain different proofs.

**"Qualified" is the load-bearing word in this document and it is used in exactly one sense**,
inherited from the product definition: a method's sources, conventions, prerequisites and exceptions are
on record before it is applied. An unqualified method may be named and explained; it may not carry a
finding. Every "qualified rule", "qualified fact", "qualified relationship" and "qualified manifestation"
below means that and nothing more.

**This is one plane among three.** Product §1.3 names the data plane, the **retrieval plane**
(discovery, hydration, capability contracts, coverage, the omission challenge) and the **conversation
plane** (Paripraśna and the managed MCP door). This document governs the data plane only. Its value
composes by the identity in product §1.3 — `plane = Σ layers + Σ synergies between them` — and the
synergy term between planes belongs to the product definition, not here. Where this document says
"the plane", it means the data plane; obligations that cross into retrieval or conversation are
stated here too, because there is nowhere else yet to state them: **the retrieval and conversation
planes are not built** and have no governing artefact of their own (parent §1.3 records exactly this).
Every obligation in this document that belongs to one of them is marked **[TRANSFERS]** — it moves to
that plane's artefact, unchanged in substance, when that plane is elevated. A [TRANSFERS] obligation is
not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work.

### 1.1 What the person should gain

The person should be able to understand:

- What the chart actually contains, under which inputs and conventions.
- Which configurations matter to their question, how their participants relate, and what changes their expression.
- Why apparently favourable indications can coexist with strain, or prominence with poor retention or difficult delivery.
- Which relevant concepts and alternative explanations were examined, including important conditions against the conclusion.
- Which clocks engage the same structural participants, how windows differ, and what is closest versus better supported later.
- What is supported as interpretation, what can responsibly become a specific earned forecast, and which bridge is still missing.
- What changes under another qualified method or uncertain input, and what remains stable.
- How their reported history fits, fails to fit or cannot fairly test the interpretation—without hindsight becoming prediction.
- What the sources actually say, how their rules were qualified, and what those rules change in the reading.

The unit of value is an **earned distinction**, not an asset count, a longer answer or a larger agreement score. A cancellation that prevents an unjustified forecast is as valuable as additional supporting evidence.

### 1.2 Scope and adoption

This is the master for deriving six layer definitions and then asset/interface briefs. It is not six completed layer audits or 129 completed asset certifications. The companion register covers the known writer/non-writer universe with provisional component dispositions and named investigation needs. Representative source paths have been examined; no production population, deployment, private event history, source rights or predictive accuracy is certified here.

The [Product Definition FINAL](../../MADHAV_PRODUCT_DEFINITION_FINAL.md) governs the target. Root architecture, frozen writer contracts, access/safety decisions and active campaign authorities remain binding. Existing L0/L1/L2 closures are historical evidence to preserve, not a prohibition on value review and not automatically revoked by it.

## 2. Consumer requirements translated into data obligations

The P identifiers below refer to the product master. Citations follow the parent's FINAL numbering (see its
`p_identifier_note`). Any V-journey citation of P20–P24 written before 2026-09-24 referred to superseded
numbering and has been remapped here. The examples are requirements, not personal readings.

| Value journey | Product needs | Data obligations and resulting distinction |
|---|---|---|
| V01 Connected self-understanding and meaning | P01–02, P17 | Qualified graha roles, house/lord/kāraka relationships, condition, varga, cross-domain structure and rivals. Explain tensions, capacities and attributed dharma/artha/kāma/mokṣa lenses without fixed identity, spiritual rank or invented biography. |
| V02 Resources and business | P03–04 | Separate income, receipts, profit, liquidity, debt burden and retained prosperity; business growth, resilience, recognition, authority and remuneration. Structural routes and timing must retain these distinctions. |
| V03 Relationships, family and life circumstances | P05–08 | Relevant qualified domains, reference frames, event definitions and temporal contexts. Personal marriage/family interpretation is not another person's inner life, fertility diagnosis or guaranteed conception. |
| V04 Configuration and activation | P09–10 | Formation ledger, partial/failed prerequisites, actual cancellation and strength/condition; whole configuration identity; multiple qualified temporal routes, recurrence, inhibition and horizon coverage. Nearest contact is not automatically full manifestation. |
| V05 Calendar, action and method selection | P11, P20–21 | General time/location context, personal relevance and undertaking-specific constraints kept distinct; qualified Praśna/Muhūrta inputs and operators. Suitability of initiation is not a guarantee of success. |
| V06 Honest history and forecast review | P12 | Subject observations with event and knowledge clocks; independently established mechanisms; original claim definitions and exposure; fit, misfit, unknowns and observed non-events. Retrodiction is not prospective proof. |
| V07 Sensitivity and controlled comparison | P13, P19 | Actual alternate calculations/operators, conventions, stable identity matching and dependency-aware differences. Input sensitivity, method sensitivity and feasible choice remain separate. |
| V08 Source learning and scholarly depth | P15, P22 | Rights-permitted text/chapter/passage context, edition/translation, source relationships, qualified rules, exceptions and worked application. Source agreement does not establish empirical probability. |
| V09 Exact lookup and open inquiry | P16–18 | A precise fact contract or expandable question/concept/relationship map. Correctly scoped lookup; otherwise whole-chart consultation, omission challenge, relevant adjacency and explicit gaps. |
| V10 Continuing and portable understanding | P12–13, P19; master §§5–6,10 | Stable evidence/claim/reading identities, consumed snapshots, corrections and versioned comparisons. Replay, regeneration and a changed interpretation are distinguishable across authorized channels. |
| V11 Relational and entity inquiry | P14; master §15 | Horizon only. Reuse qualified subject/reference foundations; add distinct relationship/entity contracts only after separate authority. No invented entity birth. |
| V12 Lifespan and constitution | P07, P23 | Āyurdāya as the classical discipline: the applicable method and school, its inputs, the cancellations, the disagreement between authorities and the genuine uncertainty. The corpus and its computation are served as the tradition's method and its limits, never as a bare date. |
| V13 The present interval | P24 | Which mechanisms are active now, what each is doing, and how this interval differs from the one before it. Requires the active-clock set, its participants and the preceding interval for contrast — neither a forecast nor a history. |

These journeys are a proving portfolio, not an exhaustive list of future human questions. Newly revealed material concepts must expand the obligation map instead of being rejected because an initial template omitted them.

## 3. Architecture: preserve ownership, connect meaning

### 3.1 The six contributions

| Layer | The question it owns | Contribution it hands onward | What it must not claim |
|---|---|---|---|
| L0 — Brahmagyan | What does a term, rule, method or reference quantity mean, and when is it applicable? | Canonical identities; source-qualified doctrine; constants; astronomy/calendar foundations; method/prerequisite/exception vocabulary. | Personal fate, raw private biography as global truth, source count as probability. |
| L1 — Gaṇita | What is actually calculated for this subject and context? | Reproducible facts, configuration membership, conditions, divisions, clocks and uncertainty, with fact identities and conventions. | A newly invented downstream value or interpretation disguised as computation. |
| L2 — Bodha | What does the chart's connected structure permit us to interpret? | Whole-chart context, qualified structural propositions, signed relationships, configurations, contradictions, alternate routes and candidate mechanisms. | Graph centrality as causation, catalog matches as confirmed formation, temporal hooks as independent clock evidence. |
| L3 — Kāla | Which of those structures are engaged, how, when and under what conditions? | Structure–time mechanisms, background/enablement/contact/inhibition intervals, recurrence, comparisons and coverage-qualified windows. | Activity/intensity as event probability; precise geometry as equally precise life timing. |
| L4 — Phala | What could that structure-in-time mean in the person's stated life domain? | Qualified manifestation alternatives, earned outcome propositions, falsifiers and action constraints. | Automatic certainty or calibration; a generic domain score as a specific outcome. |
| L5 — Mīmāṃsā | What withstands challenge, observation and independent evaluation? | Preserved claims/outcomes, fit/misfit, admissible performance evidence, study candidates and separately approved future model artifacts. | Feedback capture as learning, retrospective fit as prediction, evaluation outcomes as serving context. |

### 3.2 Five edge types—not an all-to-all build

```text
L0 qualified meanings and reference releases
     ├──→ L1 canonical facts ──→ L2 structure ──→ L3 time ──→ L4 manifestation
     └──→ direct qualified reference use by L2, L3, L4 and L5

Authorized inquiry ↔ qualified views of relevant layers ↔ source/evidence drills
Completed reading → frozen claim → protected L5 evaluation ← admitted observations
Approved future model release → explicitly named later consumers (never same-claim feedback)
```

The claim is captured and protected at issuance, independently of a later outcome; only subsequent evaluation joins admitted observations. The diagram is a responsibility map, not a requirement to run every asset or a claim that every existing dependency follows a strict adjacent-layer sequence.

1. **Definition edge:** shared identity, unit, method or rule meaning. It need not trigger a chart rebuild when only a display alias changes.
2. **Computational edge:** a reproducible dependency from pinned producer output to consumer output. It follows the actual governed DAG, not this explanatory diagram alone.
3. **Serving-context edge:** hydration, source drill, whole-chart context or query relevance. A query may revisit L0 after L3 reveals an exception; this is not a reverse build dependency.
4. **Evaluation edge:** frozen claims and purpose-admitted observations into protected comparison. Evaluation can reference all needed layers without injecting outcomes into their event-free builds.
5. **Next-generation artifact edge:** a separately admitted immutable rule/model/qualification release. No live outcome table, personal weight or cached retrospective summary becomes an implicit predictor input.

L4's outcome vocabulary may inform the *design* of L0 shared semantics and L3 output requirements. A chart-specific L4 conclusion must not feed back into the L3 computation as independent evidence. Distinguish conceptual design backcasting from runtime feedback.

### 3.3 Physical structure and operational preservation

Preserve existing tables, fact IDs, writer IDs, useful numerical kernels, source corpus, graph relationships, APIs, historical readings and accepted evidence where they satisfy the new contract. A richer logical object can be assembled from existing rows; it does not need a new materialization by default.

Retain the frozen `WriterBase` interface, orchestrator-owned transactions/build state, `ctx.db_conn`, and current layer-specific idempotency conventions. An asset writer must not own orchestration or silently commit a partial interpretation. Any requirement that truly cannot fit the frozen contract needs a separate architecture decision; this plan does not amend it.

Do not require every L1–L5 resource to have a chart row. Shared L5 qualification/model resources and global services retain registered scope. Conversely, a global lookup must not absorb a personal diary merely because many consumers need it.

**Layer ownership is not epistemic type.** Existing L1 includes judged structure (`ga_vichara`), specialized rule applications and temporal products as well as astronomical calculations. Preserve these registered responsibilities, but type each output as astronomical calculation, classical-rule application, engineered/native judgment, approximation, observation or empirical/model result. Being in L1 does not make every field an equally verified numerical fact. Its canonical value still must not be silently re-derived downstream.

### 3.4 The presentation contract: why the plane carries more than a reading shows

The product definition serves two audiences from **one analysis at one depth**: the serious layperson in
plain language, the advanced acharya in the tradition's own vocabulary with more of the machinery exposed.
That promise is not a rendering concern. It is a **data obligation**, and it is the reason several
contracts below demand more than a plain-language answer would ever display.

For the acharya presentation to be derivable from the same computation, the plane must **retain and hand
onward**, not merely use internally:

| What the acharya presentation renders | Which contract must carry it |
|---|---|
| The method and school a finding rests on, and where authorities disagree | DP02 rule qualification, amended to carry school/tradition and unresolved alternatives |
| The prerequisites actually tested and the exceptions actually checked, including those that passed silently | DP02 (the clause set that must be tested), DP05 (each clause's actual result — passed, partial, failed) |
| Conventions in force - ayanamsha, node, house system, varga construction | DP01 identity/release, DP03 chart facts |
| Intermediate quantities, not only the graded result | DP03, DP04 condition decomposition |
| Dignity, strength and condition components **separately**, with their units and their disagreements | DP04 |
| The competing readings and which classical authority each rests on | DP06 structural relationship (variants and ancestry), DP02 (the source witness each variant rests on) |
| The chain of influence with its typed relations, not a summarized verdict | DP06 |
| The clock geometry, the activation rule, the named nearest-versus-better-supported criterion, and the manifestation bridge or its falsifier | DP07 clocks/contacts, DP08 temporal mechanism, DP09 manifestation |

A layer that collapses these into a single grade has not merely lost detail - it has made the acharya
presentation **underivable**, and with it the audience commitment. A component may present less; it may
not *compute* less or *hand onward* less. The difference between the two presentations is what is shown,
never what was computed or concluded.

This also sets the acceptance test: for any finding, both renderings must be producible from the consumed
reading package (§11) without recomputation, and must agree on the finding, its confidence and its uncertainty.

### 3.5 The synergy term: what the plane is worth beyond its six layers

To the naked eye a layer is the sum of the things it holds — its data assets and its services. It is
not. Value also arises from those assets **working together**, and that difference is the **synergy
term**. It is the thing this architecture exists to create, and it must be tracked, not assumed.

The identity is the parent's (§1.3), and it holds at every level:

```text
  layer value  =  Σ its assets and services  +  Σ the synergies between them
  plane value  =  Σ its six layers           +  Σ the synergies between them
```

**This document owns the plane-level term.** Four seams carry it, and they are the four places where
breaking a connection destroys value that no single asset accounts for:

| seam | what it joins | what is lost when it breaks |
|---|---|---|
| The controlled vocabulary (§4.1) | every layer's names to one identity | a chart's evidence fragments into pieces that cannot be joined; the estate stops being one estate |
| The DP contracts (§7) | each producer's fields to the consumer that needs them | a distinction is computed and never received — the defining failure this plan exists to prevent |
| The edge ordering (§3.2) | one layer's output as the next layer's input | facts, structure, time and manifestation stop composing into a chain and become four separate answers |
| The presentation contract (§3.4) | what was computed to what is handed onward | the acharya rendering becomes underivable from the same analysis |

**The instrument is cross-layer ablation:** hold every asset in place and break the seam — remove the
shared identity, withhold the contract field, reorder the chain, collapse the handed-onward detail — then
measure the served reading. What the reading loses is the seam's contribution. It is measured **at the
consumer**, never asserted by the producer.

**The honesty rule is the parent's and it is absolute:** where the term cannot yet be measured, that is
recorded as an **absent instrument**, never as a number. A synergy figure with no harness behind it is an
invented computation under parent §13.

Each layer plan states its own three terms — individual, synergistic, cross-layer handoff — per §13.3;
the plane-level term is the sum of the seams above, and a plane whose synergy term is near zero is six
layers sharing a repository.

## 4. The shared semantic foundation: standardize L0 through the whole plane

### 4.1 The controlled vocabulary — one authority, one closed set, everywhere

**This is a governing principle of the data plane, not an illustration.** Every entity, concept,
method, convention, unit and event class the plane names has **exactly one canonical identifier and
one closed alias set**, and that set is the only permitted surface for the thing — in every writer,
every service, every prompt, every export, and every **external** interface. The reason is not
tidiness. It is that a system which calls Venus "Venus" in one place, "Shukra" in another and
"VENUS" in a third will, somewhere, fail to find a Venus it was looking for, and will do so silently.
The product's entire differentiator is reading across the whole computed estate; a vocabulary that
fragments the estate defeats it at the root. One language across the plane is what makes it *one*
plane, and what lets external systems work with it without a translation layer of their own.

Six rules, each with a detector, because a rule without one is a wish:

| # | rule | detector |
|---|---|---|
| 1 | **One canonical id, one closed alias set, per thing.** The set is owned by L0 (`bg_ontology` is the identity owner; specialized `bg_*` assets own their specialized semantics) and changed only by governed release, never by local invention. | **both halves, because the rule has two:** (i) identity — `count(*) = count(DISTINCT <the authority's DECLARED key>)`, which for `brahma_ontology` is `(entity_class, canonical_id)`, its live `UNIQUE` constraint. **Corrected 2026-09-26 (native ruling, decision 16):** this detector previously required uniqueness of `canonical_id` *across* classes and so reported FAIL against data satisfying its own constraint — a school and a concept sharing a name are two things. The rule is unchanged, "one canonical id per thing"; the detector must test the key the authority declares, and a consumer resolving on a partial key is the defect, which rule 2 covers. (ii) aliases — every entity carries a non-empty alias set, and a class with none is a finding |
| 2 | **The set is the only permitted surface.** An unlisted name is an error to be **raised**, never a synonym to be guessed at. This holds for internal code, served answers, prompts and exports alike. | a fail-closed adapter (`UnknownIdentity`, `AmbiguousIdentity`) on every resolution path; a term that resolves by fuzzy match has not resolved |
| 3 | **Resolution is one-directional and deterministic.** Any listed alias → the canonical id; normalization (case, diacritics, whitespace) is declared once; ambiguous aliases are listed as ambiguous, not silently assigned. | the normalization rule and the ambiguous-alias list are part of the release, not of a consumer |
| 4 | **Code-side representations are generated, pinned and joined.** A Python or TypeScript snapshot of the vocabulary is legitimate only if it is generated from the authority, carries the release id and content digest, and is joined to the authority by a **parity test** that fails when they diverge. A hand-maintained mirror is a second authority, and a second authority is a defect. | parity test per snapshot per language; a snapshot without one is untrusted |
| 5 | **External inputs are typed to the set.** An interface parameter that names an entity is an enum over the canonical ids, or a free string that is validated through the resolver *before* any comparison. A free string compared raw against a stored label is the exact mechanism by which a Venus goes missing. | a census of interface parameters: enum-typed or resolver-validated, per parameter |
| 6 | **Independent maps are counted, and the permitted count is one per class.** Adoption is measured by the *removal* of local dictionaries, not by the existence of a canonical module. | a census detector per entity class that scans code for independent name→id maps and fails above one |

**Scope.** All six semantic families of §4.2 and all sixteen entity classes of the ontology — planets,
signs, houses, nakshatras, vargas, karakas, aspect types, upagrahas, yogas, doṣas, daśā systems,
domains, concepts, remedy types, texts, schools. A principle implemented for eleven planets and
nothing else has not been implemented.

**The presentation contract depends on this.** One canonical id rendering as *Śukra* for the acharya
and *Venus* for the layperson (§3.4) is possible only because both are members of one closed set
bound to one identity. Two audiences, one depth, one vocabulary.

**The identity problem, concretely.** A user may say Sun, Surya, Sūrya, Ravi or another qualified
alias; Python, TypeScript, ingestion, computation, retrieval and rendering must resolve every one of
them to the same identity, and must refuse the ones they do not know.

Layers may use different physical representations of an identity through explicit adapters; they must not
independently invent its meaning. Under rule 1 the identity owner is `bg_ontology`, and `bg_reference`,
`bg_formula_constants` and the specialized references supply distinct specialized semantics: the L0 plan
binds that boundary asset by asset, it does not reopen who owns identity. Do not indiscriminately merge
these assets, and do not replace every local constant with a runtime database request — rule 4's
generated, pinned, parity-tested snapshot is the sanctioned middle. Canonicalizing a node label must not
erase true/mean-node conventions; canonicalizing a rule name must not erase school variants or disputed
readings.

### 4.2 What a qualified shared definition must carry

| Semantic family | Required content | Primary consumers |
|---|---|---|
| Entity and role | Stable entity ID, aliases/script/transliteration, typed identity, role vocabulary, ambiguity and deprecation mapping. Natural kāraka, functional role and house lordship are roles—not interchangeable entity names. | Every parser, writer, join, source reader and channel. |
| Calculation convention | Units, frame, ayanāṃśa, node and house convention, varga construction, time/location requirements, constants and version. | L1 calculations, L3 contacts/calendar, controlled comparisons. |
| Rule and concept | Rule ID/version, source witnesses, tradition, scope, prerequisites, operators, conjunction/disjunction, exceptions/cancellations, output meaning and unresolved alternatives. | L1 formation; L2 interpretation; L3 activation; L4 manifestation; inquiry applicability. |
| Evidence and epistemics | Source testimony, qualified rule, computed fact, inference, forecast, evaluation; verification method/scope; dependence ancestry; missingness and confidence units. | All transformations and answer shapers. |
| Domain/outcome/activity | Distinguish event, ongoing state, intention and action; outcome subtype/criterion; resource creation versus retention; title versus workload/pay; culturally/contextually qualified mappings. | L2–L4, observation intake, claims and evaluation. |
| Temporal and geographic | Instants versus uncertain intervals, calendar/time-zone/location conventions, inclusivity, hierarchy, horizon coverage, precision and provenance. | L1/L3 services, timelines, forecasts, event comparisons and exports. |

The first released subset should cover the selected vertical slice completely; the contract must extend without incompatible local inventions. Reuse existing ontologies/catalogues and their release machinery before introducing a new field or registry.

### 4.3 Source depth is a usable rule graph, not just more text

Preserve complete texts and exact passages, edition/translation context, source rights, concordance and competing witnesses. Link each executable interpretation to its actual supporting rule clauses. Distinguish supported, readable-but-not-executable, disputed, unsupported and method-inapplicable rules.

A source may support formation but not the proposed timing operator or manifestation claim. Those are separate qualification gaps. Ten derivative quotations of one source are not ten independent authorities. A doctrine known only by report is recorded as unsupported with its witnesses named; reconstruction of lost knowledge is out of scope (parent §13), and an AI-composed verse is never a source.

Build rule dossiers as views over existing source/rule/computation/evaluation owners. Their consumer value is concrete: “This exception changes the qualified interpretation in this way.” Whole-text access, local context and a source-to-application drill are core; a complete manuscript laboratory is a separately scoped horizon.

### 4.4 Propagation and compatibility

Classify each L0 revision before propagation: display/alias correction; identity mapping; semantic rule change; calculation constant/method change; source provenance/rights correction; evaluation qualification change. Generate affected adapters, report consumer compatibility and invalidate only dependent outputs. A new alias normally should not recompute the chart; a changed computational constant may require affected facts and downstream derivatives to rebuild.

Old readings retain their consumed release. New work must not mix incompatible rule/fact/model generations silently. An obsolete or withdrawn rule is visible as such; it is not silently rewritten inside an earlier forecast.

Global scope also does not mean location-free. For example, the inspected Muhūrta lattice uses a reference location and a disclosed midpoint approximation. Its consumers must preserve location/horizon/precision or compute the properly qualified local context; a globally shared table must not be mistaken for a universally valid election calendar.

## 5. Domain depth: the information that must survive every handoff

These are qualified obligations, not a requirement to run every method on every question or an assertion that every listed operator is implemented. The layer plans must bind each applicable obligation to exact source clauses, supported operator scope and tests.

Construct a coherent qualified bundle **within each method before comparing methods**. Then compare input differences, shared ancestry, meaningful disagreement and missing support. Do not assemble an apparently coherent result from incompatible school prerequisites or average them into a universal consensus score.

| Domain obligation | Data that must survive | Cross-asset contribution |
|---|---|---|
| Graha contextual roles | Natural/functional role, lordship, kāraka, placement, condition and relevant relations separately. | L0 meaning → L1 computed roles/placements → L2 mechanism → L3 participating roles → L4 domain-specific interpretation. |
| Rāśi/bhāva/lord/kāraka | Reference frame, occupants, lord/associated houses and significators; sign is not silently house. | Combine primary-domain evidence with qualified adjacent domains; do not reduce to occupant lists. |
| Bala/dignity/avasthā | Components, units, condition causes, verification, positive/negative contributions and missingness. | Capacity, ease, prominence and inhibition remain separate; no universal favourability or probability conversion. |
| Sambandha | Actor → typed relation → target; aspect school/orb where applicable; conjunction, exchange, dispositors, nakshatra chains, argalā/virodha; source and fact IDs. | Investigate decisive chains, cycles, alternative routes and shared dependencies. A path's meaning must survive graph compression. |
| Bhāvat Bhāvam | Qualified derived-house scope, primary/derived identities, prerequisites, relevant participants, exceptions and actual application status. | Limited existing amplifier and shared derived-house map remain qualified parts, not assumed full concept coverage. No removal of doctrine limits without review. |
| Varga and reference perspectives | Varga method, domain, sensitivity, relationship to D1, reference lagna and exceptions; arūḍha/special-lagna meaning. | Distinguish resources from appearance/standing and stable versus input-sensitive support; multiple views of one input are not independent votes. |
| Yoga/doṣa/bhaṅga | Catalog definition, actual formed/partial/not-formed states, participants, failed clauses, cancellation conditions and further manifestation qualifications. | Nīcha-bhaṅga is not automatically a fully effective Rāja Yoga; temporalize the configuration and its conditions, not just a planet label. |
| Nakshatra/KP | Nakshatra/pada relationships and scope; symbolic/source layer distinct from calculated chains; method-native cusp/sub-lord/nodal-agency prerequisites. | Specialized evidence joins only within qualified contexts, then compares coherently with other methods. |
| Present interval (P24) | The active clock set at `as_of`, each active clock's participants and what it is doing, and the immediately preceding interval retained for contrast. Activation is L3; expression of what it is doing is L4. | L3 owns the interval set and its boundaries; L4 owns the expression; neither may infer the other's half. |
| Kāla | Daśā hierarchy, contact geometry, reference sign/house, transit conditions, applicable AV/vedha, annual/return conventions and precise coverage. | Background period, enablement, trigger, inhibition and recurrence are distinct contributors to the same structural mechanism. |
| Praśna/Muhūrta/calendar | Correct question/undertaking, location/time, method eligibility and constraints. | Preserve existing services; do not relabel conversational Paripraśna as a completed Praśna method or birth pañcāṅga as arbitrary future election data. |
| Ayurdaya and constitution | Method and school identity, its required inputs, the cancellations and exceptions each school applies, the disagreement between authorities, and the uncertainty carried by each step. Retain the computation and its limits together; a bare figure without its method and its cancellations is not a qualified result. | L0 method/source -> L1 ayurdaya computed under each applicable school -> L2 constitutional structure -> L3 applicable intervals -> L4 expression, with the tradition's own caveats preserved at every hop. |
| Voluntary practice and wider tradition | Attributed practice, scope, burden, suitability, contraindication and evidence class; proper spatial/collective/non-natal inputs. | Attributed guidance only; source testimony is not demonstrated remedial efficacy. |

Completeness means the relevant qualified concept was applied, was found inapplicable, or has an explicit unavailable/unqualified/unresolved state. A tool name, an empty result or a populated confidence flag does not prove application.

## 6. The layer stories and the assets that tell them

The [asset contribution register](MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md) names every known writer/non-writer, its preserved contribution and provisional delta. The groupings below express complementary jobs, not a proposed renaming or forced consolidation.

### 6.1 Brahmagyan: a shared language that can be applied

Source assets (`bg_texts`, indexes, concordance and compendium) preserve the tradition and its context. Ontology/reference/constant assets establish stable identity and meaning. Rule/yoga/doṣa and specialized method references qualify what may be computed or interpreted. Astronomy/calendar services supply the shared celestial substrate. Event/activity and cohort/prior resources have distinct purposes: a vocabulary is not a private event store; an incidence baseline is not a personal forecast.

The interplay must run from a source witness to a qualified rule, its prerequisites, the exact fields a calculation emits and the consumer distinction it enables. Improve source-to-rule coverage and generated semantic adapters before asking downstream layers to invent missing interpretations. Enrich only where a named consumer needs an absent qualified clause, relationship, precision level or source family.

### 6.2 Gaṇita: the reproducible chart, not a bag of placements

Position and chart-service kernels establish the subject/frame. Varga, strength, condition, structural, sensitive, nakshatra and yoga assets add different computed dimensions. Daśā, transit-anchor, pañcāṅga, Tājaka and specialized services provide time and method-specific foundations.

Join these dimensions by canonical fact/configuration identity and context. Preserve the constituents of strength and condition, formation failures and exceptions, precise clock boundaries and relevant target geometry. A downstream consumer must not select whichever row first matches a category or substitute zero/neutral for missing computation.

L1's deliverable is a qualified fact package, including what was not computed or is too sensitive to uncertain birth inputs. It is not an event-free justification manufactured to match biography. Event-time calculations, where authorized, use separate context identities and do not overwrite natal truth.

### 6.3 Bodha: turn facts into a coherent structural reading

`bo_laksana` and grounded signals provide chart-specific propositions. Relationship and graph assets preserve typed interactions; paths/motifs and mechanisms organize connected configurations. Cross-domain, contradiction and whole-chart synthesis assets reveal how several life facets can support or oppose each other. Pratijñā, discovery and frame-specific assets add qualified hypotheses and alternative perspectives; reranking and summaries help navigation.

The target is a structural mechanism with participants, roles, configuration membership, relevant domains, supporting/opposing conditions, original fact references, source rules and alternatives. Keep occurrence support separate from delivery condition. Cancellation of an inhibitor and cancellation of support have opposite implications; preserve original polarity.

Summaries, salience, embeddings and graph centrality are navigation aids. They cannot replace the relevant ledgers or certify a causal mechanism. A low-ranked bridge can be decisive to a question and must remain discoverable. Whole-chart Bodha consultation is the floor for an interpretive query, not permission to answer from a gestalt alone.

### 6.4 Kāla: temporalize the same structure

Preserve the expensive useful capital in transit engines/sweeps, precise daśā timelines, annual and return methods, temporal joins and materializations. Distinguish raw celestial motion, chart-relative contacts, eligible activation, convergence/comparison, scenario publication and consumer projection. Similar names may represent different stages of this chain rather than redundant assets.

`ka_kshetra` should contribute its useful search/temporal-integration engineering as a mechanism-qualified candidate substrate, not become a universal authority that all questions accept without reconstructing its inputs. Other Kāla assets contribute applicable clocks, obstruction/support, recurrence, envelope precision, domain coupling and explanatory joins.

For every candidate window, retain the structural/configuration IDs and actual activated participants. Ask whether the clock engages a relevant support route, an inhibiting route or merely a correlated participant. Do not make shared graph nodes necessary timing gates without a qualified rule.

**The present interval** is served from these same mechanisms, not from a separate surface: the clock set
active at `as_of`, each active clock's engaged participants, and the immediately preceding interval
retained for contrast. What each mechanism is *doing* is L3's activation state; what it may *mean* is
L4's, and neither may infer the other's half (§5, Present interval).

Rank closest and better-supported later windows separately, using declared criteria and shared-dependence accounting. Return the search horizon, covered methods, temporal precision and missing inputs with no-window results. Coarse search can nominate a candidate; exact refinement is justified by that candidate and must preserve its identity. Chapter→year→interval→contact navigation must not invent a new story at each scale.

Preserve useful views as projections where they help consumers; do not maintain rival scoring authorities simply to preserve screen boundaries.

### 6.5 Phala: from activation to a discriminating manifestation

Use the Phala asset family to distinguish named life expressions, competing manifestations, qualified support, falsifiers and permissible action. An outcome taxonomy alone is not the missing inferential bridge: the bridge requires a qualified operator and its limitations.

Preserve existing deterministic manifestation and purification/provenance kernels. Investigate overlaps among `ph_phaladesa`, `ph_nimitta`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana` and `ph_pramana` by exact responsibility and consumers before deciding consolidation. The goal is a coherent publication chain, not multiple wrappers that each reinterpret probability or confidence.

Electional/remedial/rectification assets keep their separate method and authority gates. L4 does not calibrate itself. If an affirmative, specific forecast is earned, emit it with the exact outcome and temporal scope. If not, retain the useful interpretation/activation and explain the absent bridge rather than making every question permanently unanswerable or inventing a claim.

### 6.6 Mimamsa: challenge without contaminating the answer

**Learning's output is defined, and it is what makes this layer a producer rather than an observer:** a
visible change to a claim family's scope, confidence or availability, with the reason stated - a family
may be revised, narrowed, demoted or withdrawn where the evidence warrants it. Evidence that cannot change
what the product says is not learning. Attributed traditional interpretation may remain available where a
restriction applies to the product's own forward claim rather than to the tradition's testimony.

Preserve evidence ledgers, original predictions, observations, audits, comparison/discovery kernels and legitimately shared services/models. Differentiate stored evidence, structural estimates, actual measured performance and service readiness. Learning is a separately admitted outcome, not the automatic consequence of data arriving.

A family of interpretations must be able to lose authority after a fair evaluation. Ordinary periods, counterexamples, unmatched activations and failures belong in the evaluation design. Neither satisfaction nor a subjective sense that a reading resonates becomes a prediction weight.

L5 may identify source/computation defects for a future owned fix, and may publish a qualified future artifact through existing gates. It must not feed the observed outcome, a derived personal multiplier, rectification selection or cached retrospective narrative back into the prospective generation being evaluated.

## 7. Cross-layer contracts: exactly how the value moves

The following DP identifiers are logical integration contracts, not new assets or tables. Existing identifiers and schema fields should be retained wherever semantically adequate. Names not present in source are **target semantic fields**, to bind in layer/asset briefs rather than assumed database columns.

### 7.1 Common contract envelope

Every material use records: consumer question/distinction; producer/consumer owners; stable row/fact/relationship identity and generation; exact fields and grain; units, polarity, roles and membership; subject/tenant and calculation/method context; source/verification/applicability and missingness; transformation and output affected; original evidence-family lineage and knowledge cutoffs; relevant/irrelevant/duplicate/context/delivery tests; baseline and incremental-value result; compatibility, invalidation and rollback.

Every consumer declares whether an input contributes to calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation or evaluation. A citation with no declared use does not prove utilization. Not every useful input changes a score.

| Contract | Producer → consumer | Required use and preserved distinction |
|---|---|---|
| DP01 Identity/release | L0 → all adapters and writers | Canonical entities, qualified aliases, units and released definitions; local representations cannot diverge in meaning. |
| DP02 Rule qualification | L0 → calculation, interpretation and investigator | Exact rule clauses, method, school/tradition, the prerequisites and exceptions that **must be** tested, the source witness behind each variant reading, unresolved alternatives and executable scope; invocation is not application. The clause *set* is doctrine and belongs here; each clause's *result* for a chart is DP05. |
| DP03 Chart facts | L1 → L2–L4/services | `fact_id`, grain/value/unit, chart/build, ayanāṃśa/frame/varga, input precision and verification; no downstream re-derivation. |
| DP04 Condition decomposition | L1 → L2/L3/L4 | Separate condition/bala/benefit/functional role, constituents and reasons. Retain zeros as zeros and unavailable as unavailable. |
| DP05 Configuration | L0+L1 → L2 → L3 | Formation, participants, **every clause tested with its result — passed, partial, failed** — and cancellation; hydrate actual configuration before timing. A clause that passed silently is as required as one that failed: it is what the acharya rendering (§3.4) shows. |
| DP06 Structural relationship | L2 → L3 and inquiry | Actor/relation/target, all relevant domains, constituent facts/signals, signed support/opposition, condition/occurrence ledgers, variants and ancestry. |
| DP07 Precise clocks/contacts | L0/L1/L3 primitives → temporal integrators | Parent/child clocks, actual interval boundaries, geometry, reference frame, coverage and uncertainty; retain exact data until final presentation. |
| DP08 Temporal mechanism | L2+qualified clocks → L3 consumers | Same mechanism/configuration ID, engaged participants, qualified necessary/optional conditions, enablement/inhibition, alternate routes, horizon, and **for the present-tense need (P24) the interval now active and the one immediately preceding it**, each with its engaged participants. No topology-only gating. |
| DP09 Manifestation | L3+qualified structural/rule evidence → L4 | Outcome subtype, competing expressions, required bridge, falsifier, constraints and temporal scope; intensity is not event probability. |
| DP10 Capability discovery | All producers → registry/investigator/build consumers | Concepts/fields, prerequisites, exact access path, scope, permission, qualification, pagination/freshness and gaps. Support both question→data and field→actual consumer. |
| DP11 Investigation completeness and question compass | Capabilities/evidence → planner/omission audit | Expandable concept and relationship obligations; real application states; low-ranked decisive evidence; independent challenge; consequential uncertainty → smallest admissible discriminating next step and burden. |
| DP12 Complete delivery | Findings → managed channels/export/replay | Every relevant authorized fact and conjoint interpretation mapped to delivered parts; material counter-evidence survives budgets and resumption. |
| DP13 Observation intake | Creation/import/chat → canonical subject-observation owner | Original testimony, subject, source, deduplication, event/knowledge/confirmation clocks, precision, purpose and revisions. Canonical owner/path must be resolved, not a new competing diary. |
| DP14 Historical comparison | Admitted observations + independent L1/L2/L3/L4 context → comparison | Fit/misfit/unassessable and unmatched activations; rival propositions with predeclared distinguishing criteria/window/ambiguity, burden and exposure. Classify retrospective versus prospective use before routing; no chart-fact rewrite. |
| DP15a Claim issuance protection | Completed reading → protected claim authority, without outcomes | A rebuild never re-stamps an issued claim's emission time; re-stamping turns a frozen claim into a hindsight leak. Capture/seal original proposition, wording, model probability, window, cutoff and actual consumed evidence at issuance; preserve operator-band freeze point separately. Required before a forecast is exposed as a completed issued claim. |
| DP15b Later evaluation | Already-protected claim + eligible observation revision → protected L5 | Independent adjudication, valid eligibility/observation denominators and versioned correction; admitted outcomes never enter provider synthesis. Score frozen forecast probability against independent outcome—not a match score against its own derived verdict. |
| DP16 Version/correction | Changed authorized input/source → dependent current products | Dependency-specific stale marking, coherent publication and cache invalidation; retain consumed snapshots and original forecasts. |
| DP17 Controlled comparison | Alternate qualified input/method/options → matched findings | Real changed computation/application, shared ancestry, changed/unchanged/unsupported findings and reason—not two unconstrained essays. |

### 7.2 Worked structural-to-temporal contract

For a financial configuration, retain its complete `domains_affected_array`, `configuration_jsonb`, `constituent_facts_array`, `constituent_signals_array`, conditioning/epistemic information and qualified signed relationships where actually produced. Current source exposes many of these through explicit projection, but a compact default is not proof that consumers receive them [S02].

The temporal consumer must identify the configuration, participating graha/roles, activation rule and precise applicable intervals. A retention-related opposition must remain an opposition even if a receipts-related route is active. Reordering domains must not change meaning. A repeated summary or a second wrapper around the same fact must not increase independent support.

The manifestation consumer then distinguishes nearer receipts from durable relief. If that distinction lacks a qualified rule, return a named gap—not a synthetic promise. If the distinction is supported, both managed channels receive the actual relevant facts and their conjoint interpretation, not only the winning window label.

Tests: change a relevant cancellation; preserve geometry while condition changes; reorder domains; duplicate an evidence path; alter an unrelated configuration; seed a decisive second-domain finding beyond default top-K; compare richer versus simpler projection under the same question. Assert the declared consequence at each stage and in the delivered reading.

## 8. Intermediaries are part of the data-plane value chain

**[TRANSFERS] — read this before the section.** Almost everything below belongs to the **retrieval plane**
(discovery, hydration, capability contracts, coverage, the omission challenge) or the **conversation
plane** (Paripraśna, the managed MCP door, their parity and delivery obligations). Neither plane is built
yet and neither has a governing artefact, so their data-facing obligations are stated here — and they move
to those artefacts, unchanged in substance, when those planes are elevated (§1). A layer plan does not
inherit this section as its own build work. The one permanent data-plane obligation inside it is what a
producer owes **about itself**: DP10 capability metadata, its real scope, and its honest gaps.

### 8.1 Discover, hydrate, apply, deliver

Preserve the current capability registry, retrieval tools, whole-chart floor, adaptive inquiry, evidence envelopes, provenance, reading parts, persistence and MCP transport protections. Extend their contracts where needed; do not build an unrelated second investigator.

Each capability must expose what it can actually supply and what it cannot. Concept applicability is not just a tool description. Hydrate the exact relevant records after candidate discovery; do not infer completeness from a default projection, rank or successful response. Trace the decisive value through SQL, adapters, aggregation, caching, adaptive passes and final synthesis.

The investigator may expand beyond the original plan when a relation, exception or source uncertainty warrants it. Maintain durable evidence references, finding identities and unresolved frontiers across passes. Cycles and diminishing information gain can guide work; they cannot conceal a known material omission. Existing spend limits remain binding until separately changed; a limit produces an incomplete/resumable result, not a false complete reading.

The question compass turns a gap into a useful next step: identify the competing findings; classify input uncertainty, missing computation, source ambiguity, disputed method or weak manifestation support; name the smallest admissible fact/comparison/source investigation that could distinguish them; and state what would change, expected information value, burden and remaining limits. Sometimes further analysis is unlikely to help. This is an optional projection of existing inquiry/capability/finding records, not a new registry and not a default request for more biography.

### 8.2 Judgment and assessment tools are domain authorities

`assess_domain`, `judgment_query`, pact, synergy and spine/bundle tools can select, grade or halt an interpretation. They need domain qualification just like writer algorithms. For example, the inspected pact maps a `contested` composite judgment to denied promise and halts later stages, while pointing to an unbuilt/manual bhaṅga check [S01]. This is a source-level reason to review that semantic gate—not proof of the user's reported missed-chain incident or a current production defect.

The proposed target distinguishes unsupported, disputed, incomplete and genuinely ruled-out cases. A heuristic composite must not acquire universal doctrinal authority from its wrapper. Conversely, a properly qualified negative condition should constrain the answer. Preserve the useful staged chain, explicit partiality and provenance; qualify or replace the inadequate decision operator only after source/consumer tests.

### 8.3 Two managed doors and a raw evidence door

Paripraśna and managed MCP owe equivalent authorized substantive findings, qualification and completion semantics for equivalent requests—not identical prose. Direct MCP owes correct scoped evidence, discoverability, provenance, honest gaps and pagination; it cannot certify an external orchestrator's complete reading.

A complete managed reading contains its clear synthesis plus every identified relevant authorized finding and conjoint interpretation. Details may expand in the same artifact; already-known findings must not require a new question. Preserve contradictory evidence under budgets. Durable numbered parts and completion manifests handle transport limits. Existing protected fields/reading-part machinery are capital to reuse, not evidence that all desired findings already survive [S04–S05].

Source exploration, chart/profile views, calendar, timelines, specialized services and export/sharing consume the same qualified meanings. A calendar does not gain a personal prediction from chart-page placement. Replay retains original consumed evidence; a regenerated reading has a new identity and explanation of changes. No silent cross-chart or cross-purpose reuse is permissible.

## 9. Life observations: maximum justified use, no circular forecasts

### 9.1 Intake and ownership

Treat user testimony as a subject-scoped resource with explicit purpose, not as unrestricted chat memory and not as global doctrine. Reconcile chart-creation, import, timeline and conversational routes against existing observation authorities. Choose the canonical owner in the L5/intake contract; retain legitimate observation versus prediction-ledger separation. No new universal event database is prescribed.

Preserve original account, reporter/source, event versus state/intention, domain/outcome subtype, event interval and precision, time/location where material, when the system learned it, confirmation/dispute, prior exposure, duplicates and corrections. A parser's inferred event is not a confirmed autobiography. User significance is not independent reliability. A quiet or unrecorded period is not an observed non-event.

The existing ownership starting point is concrete: `life_events`/registered `lel_events` hold observation testimony with channel adapters; `mi_jivanaghatana` is its qualified evidence projection. `ph_nimitta`/`mi_bhavisya` produce rebuildable candidates, not protected issuance history. `brahma_prospective_ledger` is an explicit-filing authority, while `brahma_mimamsa_prediction_ledger` has the distinct Samīkṣā detection/confirmation lifecycle. Preserve both legitimate lifecycles; define cross-ledger claim identity/deduplication before scoring. The exact adapter/revision migration still needs a scoped intake brief.

### 9.2 One switch, two states

Life-event use across the plane is governed by the product definition's single switch, not by a table of
purposes. There are two states and no third.

| Switch | What the plane may do | What every reading must carry |
|---|---|---|
| **ON** | L0 event vocabulary; L1 separate event-time context; L2 structural alternatives compared against reported history; L3 alignment of reported intervals against independently established mechanisms, and inspection of unmatched windows; L4 manifestation distinctions; L5 adjudication of frozen claims against admitted observations. | The switch state, recorded in the emission record beside the information cutoff. |
| **OFF** | Nothing derived from life events, anywhere. Every reading emits only what the chart, sources and methods produce on their own. No life events appear in any inquiry surface. | The switch state, as above. |

"Across all layers" means every justified consumer receives the minimum complete projection **its declared
use requires** when the switch is ON. It does not mean every table gets the raw diary.

Conditioning a forecast on pre-cutoff practical context is **not** a data obligation of this plan. If it
is ever proposed, it is a switch-ON overlay under the correctness rules below, and it needs its own
authority; no useful-data argument activates it silently.

**Storage separation, which is what makes OFF a selection rather than a rebuild:** event-conditioned
overlays are kept separate from event-free structural and temporal products. Turning the switch OFF
deselects the overlays; it never requires recomputing the event-free products.

**The correctness rule that survives regardless of switch state** is the product definition's per-layer
prohibition list: biography must never alter a chart fact; a biography-dependent support must never be
presented as event-free chart structure; and **L3 must never use an observed event to choose the
supposedly prior trigger.** Violating these makes the output wrong, not merely inappropriate.

### 9.3 Corrections, snapshots and evaluation

An event correction invalidates affected historical comparisons/evaluation candidates, not the natal chart automatically. A birth-input correction has a distinct dependency path. In both cases, current projections and caches must reflect staleness before reuse; publish a coherent new generation after accepted rebuilds. Keep original consumed readings and forecast contexts under the applicable retention policy.

Retain the forecast actually delivered. A predicted formal promotion does not become a success because workload increased. Interrupted turns remain retained exposure but excluded from prediction detection. Model-stated probability and later operator bands have separate immutability points. Uncertain observation is not an automatic hit or miss.

Eligibility distinguishes pre-window forecasts, forecasts of the still-future remainder, nowcasts and retrodictions. Retaining an original `recorded_at` while overwriting event content cannot make a later revision known earlier. Use the actual observation revision and its knowledge-time lineage. Score the frozen forecast probability against independently adjudicated outcomes, never a composite match score against a verdict derived from that score.

Withdrawal, deletion and restriction propagate to derived views, caches and affected evaluation artifacts under DP16. The remaining details belong in the intake/correction execution brief and its actual owner contracts.

## 10. Preservation and rationalization decisions

### 10.1 The decision hierarchy

Use the smallest sufficient change, with no quota for keeping or removing assets:

1. **P — Preserve:** exact useful kernel/interface already meets the requirement; reuse its accepted proof within scope.
2. **I — Integrate:** preserve producer depth; repair discovery, projection, join, ranking, explanation or delivery.
3. **E — Enrich/correct:** preserve working portions; add missing qualified fields, relations, clauses, precision or computation.
4. **Q — Qualify/limit authority:** retain source/computation, correct its permissible interpretation or method scope; keep unsupported outputs explicit.
5. **C — Consolidation candidate:** two components appear to share authority; trace exact callers/semantics and choose a successor only after proof. A useful projection/service can survive consolidation of its judgment kernel.
6. **H — Historical/research/restricted:** retain valuable capital with current gates; no automatic consumer activation.
7. **R — Retire after migration:** only after identified successor, caller/runtime/audit/history analysis, compatibility, provenance transfer and reversible migration. No asset receives unconditional R in this master.
8. **U — Unresolved use:** evidence is incomplete. Lack of a caller in a bounded search is not redundancy.

The register uses combinations. A whole asset can be mostly preserved while one score, fallback, duplicated map or narration rule is replaced. Asset identity and historical receipts need not disappear because a kernel changes.

### 10.2 What should be cast away

The initial removal targets are **inadequate behaviours**, subject to exact source verification and separate implementation: independently authored conflicting definitions; forced favourable defaults for missing data; aggregation that erases material domains/roles/polarity; duplicate-evidence counting; unqualified conversion of strength/agreement into probability; misleading “applied/served/complete” detectors; unsupported categorical denial; and wrappers that repeat expensive work without a distinct responsibility.

Do not cast away raw source evidence, contrary findings, historical failed predictions, accepted kernels, rare-but-valid methods or useful compatibility views. Do not delete an asset because it lacks a current screen or because its name resembles another.

### 10.3 What should be brought in

Prefer these missing *capabilities* within existing owners: qualified rule/applicability dossiers; exact entity/convention adapters; full structural/temporal mechanism views; scope-aware capability metadata; evidence-dependence and omitted-concept checks; precise outcome/manifestation contracts; observations carrying their declared use; correction and coherent-generation propagation; complete reading delivery; and controlled comparison operators.

Only propose a new asset when its semantic responsibility has no adequate owner, a new boundary materially improves correctness/value, and extension/composition would be worse. Require source/method qualification, named consumers and migration cost before deciding its name or physical storage.

### 10.4 Source-grounded priorities that change the work order

The reviewed source supports prioritizing: L0 alias/constant semantic reconciliation; fail-honest numerical facts rather than plausible fallback positions; complete signed/multidomain structural joins; actual precise interval overlap; proposition-specific event-class/method joins; subject-scoped observation revision paths; candidate-versus-issued-claim separation; and indirect historical-lineage controls on serving/model overlays. The source review record (§15) names exact paths and the limits of each finding.

These are not blanket replacement instructions. Existing Samvāda strength/remedy separation and Pramāṇa-Māpa reference detectors have improved relative to historical observations and must be preserved. AV sign grids already exist; contributor prastāra is a specific computed-but-discarded opportunity, not a missing AV system. Mīmāṃsā has useful fit libraries/version pinning even where the current writer explicitly does not refit. Diagnose the exact gap before choosing a fix.

## 11. Generation, freshness, access and efficient computation

Source, calculation, graph, temporal search, manifestation, model and serving/catalog versions must remain visible through the consumed evidence package. Pin the actual generation selected; selecting one `fact_key` is not by itself a coherent build-generation check.

A reading selects a **compatible dependency set** for its required inquiry, binding each producer generation to the dependencies it actually consumed. Layers need not share one global build ID. Independently choosing each layer's latest rows is insufficient. Preserve reference date/horizon, conventions and historical/prospective purpose. Capture actual admitted values and material provenance in the consumed reading package, not only mutable references. A partial refresh cannot silently publish mixed generations; an older retained qualified result carries its age, scope and limitations. Use existing snapshot/materialization machinery, not a long database transaction held across AI passes.

Build only the dependencies needed by the authorized asset slice, subject to stricter campaign layer gates. Use existing global astronomy materializations and chart-specific joins; avoid copying global data into every chart. Coarse temporal search followed by relevant exact refinement, reusable facts, indexed relationship hydration and idempotent work are preferred to repeated exhaustive rebuilds.

Question-relative readiness must identify the missing prerequisite that limits an answer. Distinguish source present → qualified → consumed → effect traced → served → value evaluated. These are separate states, not one quality percentage. Service/source-only assets need applicable service/source proofs, not fabricated row floors.

Cache on subject, context/conventions, generation, purpose/access scope, relevant query and policy/model version. Withdrawn permissions and changed meanings invalidate appropriate entries. Runtime fallback must preserve the true reason—unavailable, inapplicable, empty, failed, stale or unqualified—not a plausible neutral value.

Quality precedes latency, but unlimited work is not the design. Measure cost at the meaningful join and consumer distinction. Prefer precision where it changes the question, not universal expensive granularity. Report progress, cancellation and resumability for deep investigations; do not substitute a hidden cap for conceptual closure.

## 12. Proving journeys and acceptance

### 12.1 Three end-to-end stories

**Financial promise and relief.** Identify the intended outcome and horizon. L0 supplies qualified meanings/rules; L1 supplies actual positions, conditions, divisions, formation and clocks; L2 constructs the relevant resource-creation and retention mechanisms, including applicable derived-house relations and counter-evidence; L3 searches the same configuration's qualified activation routes; L4 distinguishes possible manifestations and emits a forecast only when earned. Both managed doors deliver the full connected finding. L5 later evaluates the original claim without feeding outcomes into it. Earlier/later windows are illustrative labels, not invented native dates.

**Named yoga, including Nīcha-bhaṅga Rāja Yoga.** Validate formation and cancellation first, then any additional qualifications for the stronger interpretation. Temporalize actual configuration participants and conditions. Explain partial expression, dispute and alternate routes. A nearby transit of one participant is not sufficient by label alone. The test must reject a flattering unsupported premise while still explaining the actual chart configuration.

**Historical challenge.** Preserve an event-free structural/temporal analysis independently before comparing it with an admitted historical log when the study requires blindness. Match stated outcomes and uncertainty; inspect non-matching events and unmatched activations. For a prior forecast, retrieve its frozen definition, not a new interpretation from today's rules. Failed formal promotion is not reclassified as responsibility. Route adjudication separately from provider-facing historical explanation.

Also prove a deep structural/meaning question without a forced forecast; exact lookup and escalation; a source exception's worked effect; method/input comparison; and correct calendar-to-inquiry context. An ayurdaya request is answered as V12 requires - method, inputs, cancellations, disagreement, uncertainty - through every intermediary; never a bare date.

### 12.2 Tests that demonstrate use and value

**Ablation is the scoring method.** For any single asset, its contribution to a product obligation is the
difference between the reading produced with it and the reading produced without it. The ablated reading
is the "competent simpler baseline" the product definition's Distinctive understanding obligation names,
and the difference — including any error or burden the asset introduces — is the asset's score on that
obligation. An asset that cannot be ablated because nothing reads it has already answered the question - it has not
reached the 'consumed' state of §11's six evidence states. Ablation is how the last state, 'value
evaluated', is measured; 'served' is measured by the Delivery sentinel row below.
The tests below are the shapes that difference is measured in.

**Reference layers are the exception, and the exception is principled.** Where a layer's assets are
knowledge authorities rather than chart products — L0 today — an asset's right to exist comes from
**fidelity**: is it authentic, sourced, correctly identified and within its method boundary. It does
not come from what removing it does to a reading, because the tradition is not worth less for being
unread this quarter. For such a layer the individual term is measured by fidelity, not ablation;
ablation applies only in its cross-layer flavour, to verify that *consumers* use the knowledge
correctly, and is never grounds to disposition the asset itself.

| Test | Required result |
|---|---|
| Qualification/source | Clause supports actual operator and scope; competing witness retained; unsupported timing or manifestation not borrowed from a formation rule. |
| Numeric/context | Reproducible fact, unit/frame/varga/time precision and real verification scope; cross-chart/build mismatch rejected or isolated; the sentence that grades or labels the number is verified separately from the arithmetic that produced it. |
| Source carriage and reproduction | The cited passage is present beside the encoding and they agree; where two admitted witnesses differ, the difference is **carried unresolved** and never averaged or silently settled; a classical quantity re-derived from different inputs reproduces within a declared tolerance. This plane proves faithful transmission and reproduction; **whether the astrology is right is judged above it** (native ruling, 2026-09-25) — no verdict on doctrine is reached here, and no human verification step exists or is implied. |
| Presentation parity **[TRANSFERS]** | Both renderings produced from the consumed reading package without recomputation; identical finding, confidence and uncertainty; the acharya rendering exposes every §3.4 field its layer owns. |
| Vocabulary conformance | Every name the component emits or accepts resolves through the controlled set (§4.1); an unlisted name is raised; the independent-map census for each entity class it touches is one; every code-side snapshot it relies on is generated, pinned and parity-tested against the authority. |
| Relevant perturbation | Change a qualifying condition/cancellation and observe the declared consequence while unrelated geometry remains stable. |
| Irrelevant control | Array order, a cosmetic alias or unrelated configuration cannot change evidential meaning. |
| Dependence control | Duplicate wrappers, graph paths sharing roots, total/components and repeated texts do not inflate independent support. |
| Missingness control | Computed absence/zero, inapplicable, failed, unavailable, unqualified and unexplored remain distinguishable. |
| Omission challenge | Missing Bhāvat Bhāvam where applicable, severed chain, absent cancellation or decisive second domain is detected even if the original planner omitted it. |
| Delivery sentinel **[TRANSFERS]** | A decisive low-ranked/non-default field reaches synthesis and appears with its conjoint interpretation in all completed managed parts, replay and permitted export. |
| Temporal boundary | Adjacent intervals, timezone/day boundaries, birth uncertainty, parent/child clocks, horizon clipping and nearest/strongest comparisons preserve semantics. |
| Historical/firewall | Late-entered or revised observations, outcome-encoded summaries/weights/selectors and rectification cannot cross prohibited purposes. Unknown is not a non-event. |
| Revision | Current derivatives invalidate correctly, original consumed forecast stays unchanged, wrong-subject caches cannot survive. |
| Incremental value | Against a competent simpler baseline, measure correct added distinctions, prevented errors, uncertainty and consumer comprehension, alongside added error, burden and cost. |
| Empirical performance | Separately admitted frozen eligible claims, appropriate baselines, observation denominators, held-out/prospective evaluation and uncertainty; engineering fixtures are not real-life evidence. |
| Synergy (§3.5) | For each of §3.5's four seams: break the seam with every asset held in place and measure the served reading at the consumer. The loss is the seam's contribution. Where no harness exists the result is recorded as an **absent instrument** — never as a number. |

Do not set arbitrary universal accuracy thresholds or fabricate current results. Layer/asset briefs predeclare appropriate thresholds from the claimed contract and available evidence. Relevant-input influence proves software use; it does not prove astrological causation. All tests listed here are planned unless the source review record (§15) explicitly reports a documentation check actually run.

## 13. Elevation programme: backcast requirements, implement forward

### 13.1 Work packets

| Packet | Purpose and bounded deliverable | Depends on / exit distinction |
|---|---|---|
| W01 Demand and preservation baseline | Adopt target decisions; bind P/V/DP IDs to known assets and answer authorities; retain histories and unknowns. | Strategy agreement only; no reopen/build authority. |
| W02 L0 semantic release slice | Canonical identities/aliases, units/conventions, relevant qualified rules/exceptions and outcome definitions for first journeys; generated adapter contract. | Source/method qualification and producer tests; not every future L0 feature. |
| W03 L1 factual-use slice | Bind condition/configuration/precision/clock facts to W02; preserve numerical kernels; expose genuine gaps and uncertain inputs. | Producer-ready after focused facts/context tests; not downstream completion. |
| W04 L2 connected-meaning slice | Full participants/domains/signs/ledgers; relevant Bhāvat Bhāvam scope; configuration and contradiction hydration. | Accepted required W02/W03 contracts, source-qualified operator; no unlimited upstream perfection. |
| W05 L3 mechanism slice | Reconcile the Kāla layer's existing temporal plan and its recorded gap assertions against accepted upstream outputs, re-validating each assertion against its actual producer; one structure–time route with proper clocks, counterconditions and alternative windows. | Real producer dependency pins; broader campaign layer gates remain binding. |
| W06 L4 manifestation slice | Outcome-specific bridge and rivals, ordinary expressions, supported forward claim or exact unresolved bridge. | Accepted W04/W05 inputs/method scope; DP15a issuance/eligibility/firewall proof before forecast cutover; no calibration takeover. |
| W07 Serving/complete-reading slice | Capability discovery, omission challenge/question compass, answer-shaper qualification, complete findings and managed parity/replay. | Interface research from W01; execution binds accepted slice. Forecast exposure requires scoped DP15a proof, not the entire L5 rebuild. |
| W08 Observation/history slice | Canonical intake/revision ownership, purpose/chronology, one historical comparison/protected review. | Own intake/firewall contracts; can be designed in parallel, no automatic future conditioning. |
| W09 L5 challenge and value | Frozen comparison sets, independently adjudicated outcomes, misfit/unknowns, explanatory and empirical tests; qualified future artifact procedure. | DP15a already protected at issuance; DP15b evaluates later. No dormant fitting/service activation without existing gates and separate authority. |
| W10 Portfolio propagation | Extend proven contracts to every relevant accepted/residual/supporting asset and service; resolve consolidation candidates and unknown use. | Governed dependency order; reuse unchanged evidence; retirement only after migration proof. |

### 13.2 The first implementable brief—not implementation here

The recommended first slice is **canonical meaning → qualified structural distinction → faithful delivered finding**, using the financial/configuration journey and a source-qualified Bhāvat Bhāvam/cancellation case. This exposes high-fanout semantic and projection failures before expensive temporal work is redesigned.

Its entry needs: the approved L0 subset and actual operator scope; exact L1 fact/context fixtures; known L2 input/output fields and source-qualified negative cases; identified retrieval and both managed consumer paths. Its exit first distinguishes producer-ready from end-to-end-served. A separate Kāla/Phala extension then proves qualified activation and manifestation; do not pretend the first structural slice already answers “when.”

No need to wait for every L0 method or years of outcome evidence to correct a dropped signed relationship. No permission to waive a stricter live campaign layer gate because a narrow slice is technically possible. Prepare the narrow brief and reconcile execution authority in its separate session.

### 13.3 What each layer plan must contain

**Ten elements.** Item 1a is the vocabulary element added by the 2026-09-25 elevation and item 1b the
value-terms element added by the review fold; both are lettered rather than renumbered because the
template and the L0 instance cite these numbers.

1. Consumer value and distinctive layer responsibility; the inherited P-needs, V-journeys and DP
   contracts; and **which of the product definition's ten proof obligations this layer is scored on**,
   per its §11 layer table. A layer plan that names its own criteria instead of inheriting these is
   not derived from the product definition.
   **Ten, not eleven, and deliberately so:** `Domain correctness` — whether the astrology is *right* — is
   **not** a data-plane obligation (native ruling, 2026-09-25). This plane computes faithfully and carries
   the tradition's testimony, its witnesses and their disagreements intact; the verdict is formed above
   it, in the reasoning layer. Carriage of that evidence is required of every layer (§12.2, Source
   carriage and reproduction); judgement of it is not, and a layer plan that awards itself a doctrinal
   verdict has exceeded its plane.
1a. **Vocabulary conformance (§4.1):** which entity classes the layer emits or accepts; that every
   one resolves through the controlled set; the independent-map census per class; and, for L0
   only, that it *owns* the set and its releases.
1b. **The three value terms (§3.5):** the layer's individual, synergistic and cross-layer-handoff terms,
   each with the instrument that measured it, or an explicit absent instrument. A synergy figure without
   a harness is an invented computation.
2. Complete owned inventory including accepted, residual, service, shared and historical capital; source/runtime evidence levels separated.
3. Internal asset interplay, exact input/output/use matrix and boundary with adjacent layers and answer authorities.
4. Qualified Jyotish coverage: prerequisites, variants, exceptions, negative cases, uncertainty and source rights where relevant.
5. Component-level preserve/integrate/enrich/qualify/consolidate/restrict/retire decisions, with unknowns retained honestly.
6. Upstream demand and downstream offers with field/grain/context/lineage contracts, named owners and tests, **including which §3.4 presentation rows this layer carries and which fields it hands onward for them**.
7. Generation/invalidation, compatibility, retained history, cost and rollback.
8. Bounded work packets, dependencies, focused proof, consumer cutover and remaining activation decisions.

Each **asset brief** then supplies the P-needs it serves and the parent's ten proof obligations it is scored on (item 1), its manifestation or temporal role, actual tables/services/columns, current algorithm and consumers, preserved kernels/tests, exact delta and expected semantic difference. No new field is considered “used” until its transformation and receiving answer obligation are proved.

## 14. Decision delta from earlier planning

The deep-inquiry companion C01–C06/C16 is carried into DP01–DP12 and W02–W07; C07–C14 into DP13–DP16
and W08–W09, under the parent's switch and §9.2's correctness rules. Earlier Kāla cross-layer contracts
and view groupings are reusable kernels and hypotheses, not a permanent screen count or a mandate to
rename or delete assets; revalidate each against its actual producer before reusing an old gap assertion.
Historical accepted assets keep their receipts, and a changed serving seam is reviewed without relabeling
a historical closure as absent.

The earlier cohesive data-plane proposal was issued inline; no saved source was located during the product publication lineage check. This document reconstructs the aligned plan from the adopted master, preserved companion, supplied requirements and current bounded source research—not a claim of verbatim migration from a missing file.

## 15. Sources, unresolved decisions and adoption

Source evidence is revision-bounded and distinguished from proposed targets. See the [source review record](MADHAV_DATA_PLANE_V2_REVIEW_RECORD_v1_0.md) for inspected files/findings and the [asset register](MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md) for the full scoped membership. Historical L3 research remains preserved in the original strategic worktree; it is not overwritten or relabeled fresh runtime evidence.

Unresolved decisions belong to specific later briefs: exact canonical observation owner; doctrinal scope of broader derived-house/method operators; per-field release bindings; which same-purpose kernels genuinely warrant consolidation; applicable production population/coverage; qualification of specific manifestation operators; source rights; and model activation. These do not block proposing the architecture or preparing the first producer contracts. They do block unsupported implementation or “ready” claims.

**Adoption.** This value architecture is adopted as the basis for the six layer plans (frontmatter
`authority:`), with the asset register explicitly provisional until each layer's source/consumer audit is
complete. The L0 plan is derived from it; L1–L5 follow in dependency-aware order, keeping the serving and
observation contracts visible from the start, and each begins by backcasting the named consumer
distinctions into exact obligations rather than by surveying its own assets.

The resulting data plane should feel like one coherent astrological instrument: Brahmagyan makes knowledge usable; Gaṇita makes the chart reproducible; Bodha makes it intelligible; Kāla gives that same structure temporal expression; Phala makes the implications specific; Mīmāṃsā makes the whole instrument answerable to evidence. Their value is realized only when the person receives the connected understanding.
