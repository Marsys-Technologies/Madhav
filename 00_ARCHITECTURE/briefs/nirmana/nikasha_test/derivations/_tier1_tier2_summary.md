Both documents were read in full (658 and 711 lines). Below is the structured extraction. All blockquotes are verbatim, with the section they came from. I make no edits, so the `00_ARCHITECTURE/AGENTS.md` note does not change anything here.

# Document 1 (Tier 1): `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md`

**Governance state:** tier 1, kind `instance`, chain `ELEVATION_DERIVATION_CHAIN_v1_0.md`, `inherits: []` (root of the chain), `produces: [MADHAV_DATA_PLANE_VALUE_ARCHITECTURE]`, status **SEALED 2026-09-25** (native decision 13). Frontmatter `still_open_below_the_seal: ["layer instance (L0-L5)", "asset template", "asset instance (per-asset briefs)"]` — the layer-instance documents you are to derive are the open work below this seal. `decision_owner: Native`. Reopen rule: changing "an obligation, a contract, a count or a scope" is a reopen requiring native ruling; typos are not.

## What the product is (§1 "The defining promise")

> Madhav computes what no astrologer can compute by hand, at a volume and depth no single mind can hold, and uses artificial intelligence to turn that computation into understanding.

Two halves that only work together: **Data engineering** ("Madhav computes the whole estate and, critically, the **relationships between its parts**") and **Artificial intelligence** ("reads across that computed depth to find the connections"). "The product is the join: **insight that was not previously derivable, because the depth it rests on was not previously computable.**"

Three commitments a reading must serve: **Understand** (distinctive capacities, tensions, cross-domain relationships), **Navigate** (what persists, changes, activates), **Account** (preserve question, evidence, forecast, challenge; "learn only through qualified, visible processes"). "Prediction is central, not an ornament."

## Statements that define/constrain the data plane's layers

### §1.3 — Compositional identity and the three planes

> ```
>     layer value  =  Σ its assets and services  +  Σ the synergies between them
>     plane value  =  Σ its layers               +  Σ the synergies between them
>   product value  =  Σ its planes               +  Σ the synergies between them
> ```
> At each level the **synergy term is what makes the level a thing rather than a collection.** ... The term is measurable ... and where it cannot yet be measured, that is recorded as an absent instrument, never as a number.

Plane table (verbatim rows):

| plane | what it owns | governing artefact |
|---|---|---|
| **Data plane** | the connected, qualified astrological basis — L0 Brahmagyan through L5 Mīmāṃsā | `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL` |
| **Retrieval plane** | discovery, hydration, capability contracts, coverage and the omission challenge — turning a question into the exact evidence that answers it | `RETRIEVAL_STRATEGY_v1_0` (CURRENT) |
| **Conversation plane** | Paripraśna and the managed MCP door — the surfaces a person or an external orchestrator actually meets, with their parity, continuity and delivery obligations | §10, §10.1; Paripraśna architecture |

> **the retrieval and conversation planes are named here as first-class and are not yet elevated to the standard the data plane now holds.**

### §11 — "The retained data plane and its contribution contracts" (the per-layer product responsibility + proof table)

| Layer | Product responsibility | Proof that matters |
|---|---|---|
| L0 — Brahmagyan | Qualified vocabulary, sources, rules, constants, reference systems, ephemeris and calendar foundations | **Source and domain fidelity** (§14): canonical identity, source fidelity, method boundaries. |
| L1 — Gaṇita | Reproducible subject calculations under declared inputs and conventions | **Computational correctness** (§14): fact identity, values, units, precision, provenance. Downstream consumers refer to L1 facts; they do not recompute them. |
| L2 — Bodha | Whole-chart structural understanding, configurations, relationships, mechanisms, tensions and alternatives | **Concept and relationship completeness + Interpretive fidelity** (§14) ... |
| L3 — Kāla | Which structures are engaged by which clocks, when, under what conditions and with which alternatives | **Temporal integrity** (§14): ... nearest versus better-supported under a named criterion; honest "none found" semantics. |
| L4 — Phala | Qualified manifestation and earned outcome interpretation | **Interpretive fidelity + Distinctive understanding** (§14): ... no unqualified composite score. |
| L5 — Mīmāṃsā | Challenge, adjudication, scope of validity and qualified learning | **Predictive performance + Operational honesty** (§14): preserved failures, independent evidence, correct denominators, leakage-free evaluation. |

This §11 table is what tier 2 §13.3 item 1 calls "its §11 layer table" — the per-layer proof assignments are inherited from here, not invented per layer.

### §8.1 — per-layer life-event correctness rules

A table (Layer / Valuable use where enabled / What must not happen) for each of L0–L5. Load-bearing prohibitions: L1 must not alter birth facts to fit biography; L2 must not make biography-dependent support appear event-free; **"L3 — Kāla ... **Using the observed event to choose the supposedly prior trigger.**"**; L4 must not rewrite the original forecast; L5 no outcome leakage into prospective generation. Preface: "These are **correctness rules**. Violating one makes the output wrong, not merely inappropriate."

### §13 — binding boundaries

> **No invented computation, source, detector, confidence, empirical score, or claim of exhaustive coverage.**

Also: no outcome laundering, no association-as-causation, no cross-population hypothesis testing or source reconstruction, no automatic rectification.

### §14 — the proof scorecard (eleven rows in the table, of which "Domain correctness" is discharged above the plane)

Rows: Source and domain fidelity; **Domain correctness**; Computational correctness; Concept and relationship completeness; Interpretive fidelity; Distinctive understanding; Consumer understanding; Temporal integrity; Predictive performance; Delivery fidelity; Operational honesty.

Domain correctness row (key excerpt):

> The astrology is *right*, not merely well-sourced. Verified autonomously and only autonomously, by four checks that can each return false: (a) **source correspondence** ... (b) **cross-witness agreement** ... (c) **independent re-derivation** ... (d) **negative cases** ... **Discharged above the data plane, in the reasoning layer** (native ruling, 2026-09-25): the data plane ... carries the cited passage, the witness set with its recorded disagreement and the second derivation, and does not judge them ... the seeded negative case ... no data-plane layer may author for itself.

§14.1 names **ablation** as "the per-asset scoring method" for the §14 obligations; the ablated reading is the "competent simpler baseline."

### §16 — governance sequence (the instruction under which layer instances are derived)

> **product definition → data-plane plan → L0–L5 layer plans → asset and interface deltas → authorized execution → consumer-level verification.**
> - **L0–L2 semantics and reachability come first** ...
> - Every layer and asset brief states: **the P-needs (§2) it serves and the §14 obligations it is scored on**, the relevant Jyotish concepts, the preserved kernel, the exact delta, its authoritative dependencies, and its manifestation or temporal role.

## Named entities/pillars/engines the layers must serve

- **The six layers by name:** L0 Brahmagyan, L1 Gaṇita, L2 Bodha, L3 Kāla, L4 Phala, L5 Mīmāṃsā (§11, §1.3, §8.1).
- **P-needs P01–P24** (§2 table; note P24 present-tense need is a NEW appended need; see frontmatter `p_identifier_note` about v3.0→v3.1 renumbering).
- **Surfaces** (§10 table): Paripraśna, managed MCP door, answer-shaping instruments, living pañcāṅga, timelines, exports, operator assurance, etc.
- **Named instruments/engines in substance (§3):** graha roles, sambandha chains, Bhāvat Bhāvam, varga, yoga/doṣa/bhaṅga, nakshatra/KP, ārūḍha/special lagnas, Kāla (daśā, gochara, aṣṭakavarga/vedha, Tājaka, tithi-praveśa, Sudarśana), Pañcāṅga/Praśna/Muhūrta, remedies, āyurdāya (P23).
- **Life-event switch** (§8): one switch, two states, no third; switch state recorded in the forecast emission record.
- Two audiences, one analysis (§2): acharya and layperson presentations over identical depth.

---

# Document 2 (Tier 2): `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md`

**Governance state:** tier 2, `inherits: [00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md]`, `produces: [LAYER_DEFINITION_AND_STRATEGY_TEMPLATE, "six layer instances L0-L5"]`, **SEALED 2026-09-25**, then **REOPENED AND AMENDED 2026-09-26** (native ruling, decision 16 — §4.1 rule 1 identity detector corrected to test the authority's declared key; rule unchanged). Companions: `MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md` (provisional), `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` (the tier-3 template). Source review record: `MADHAV_DATA_PLANE_V2_REVIEW_RECORD_v1_0.md`.

## The layer model

Six layers, L0–L5, retained (§1):

> The retained six-layer architecture is appropriate. ... L0 remains the global foundation; L1–L5 retain principally chart/subject-scoped responsibilities. ... No seventh layer, universal truth graph or new parallel registry is proposed.

### §3.1 "The six contributions" (the defining per-layer table — question owned, contribution handed onward, what it must not claim)

| Layer | The question it owns | Contribution it hands onward | What it must not claim |
|---|---|---|---|
| L0 — Brahmagyan | What does a term, rule, method or reference quantity mean, and when is it applicable? | Canonical identities; source-qualified doctrine; constants; astronomy/calendar foundations; method/prerequisite/exception vocabulary. | Personal fate, raw private biography as global truth, source count as probability. |
| L1 — Gaṇita | What is actually calculated for this subject and context? | Reproducible facts, configuration membership, conditions, divisions, clocks and uncertainty, with fact identities and conventions. | A newly invented downstream value or interpretation disguised as computation. |
| L2 — Bodha | What does the chart's connected structure permit us to interpret? | Whole-chart context, qualified structural propositions, signed relationships, configurations, contradictions, alternate routes and candidate mechanisms. | Graph centrality as causation, catalog matches as confirmed formation, temporal hooks as independent clock evidence. |
| L3 — Kāla | Which of those structures are engaged, how, when and under what conditions? | Structure–time mechanisms, background/enablement/contact/inhibition intervals, recurrence, comparisons and coverage-qualified windows. | Activity/intensity as event probability; precise geometry as equally precise life timing. |
| L4 — Phala | What could that structure-in-time mean in the person's stated life domain? | Qualified manifestation alternatives, earned outcome propositions, falsifiers and action constraints. | Automatic certainty or calibration; a generic domain score as a specific outcome. |
| L5 — Mīmāṃsā | What withstands challenge, observation and independent evaluation? | Preserved claims/outcomes, fit/misfit, admissible performance evidence, study candidates and separately approved future model artifacts. | Feedback capture as learning, retrospective fit as prediction, evaluation outcomes as serving context. |

Per-layer narrative sections exist at §6.1–§6.6 (Brahmagyan / Gaṇita / Bodha / Kāla / Phala / Mimamsa), each describing the asset families and the target interplay. The closing paragraph gives the one-line identity of each: "Brahmagyan makes knowledge usable; Gaṇita makes the chart reproducible; Bodha makes it intelligible; Kāla gives that same structure temporal expression; Phala makes the implications specific; Mīmāṃsā makes the whole instrument answerable to evidence."

### Reference layer vs chart-product layer — the distinction exists (§12.2)

> **Reference layers are the exception, and the exception is principled.** Where a layer's assets are knowledge authorities rather than chart products — L0 today — an asset's right to exist comes from **fidelity**: is it authentic, sourced, correctly identified and within its method boundary. It does not come from what removing it does to a reading ... For such a layer the individual term is measured by fidelity, not ablation; ablation applies only in its cross-layer flavour, to verify that *consumers* use the knowledge correctly, and is never grounds to disposition the asset itself.

### §3.2 — five edge types (verbatim names)

1. **Definition edge** — shared identity/unit/method/rule meaning; need not trigger rebuild on display-alias change.
2. **Computational edge** — reproducible dependency pinned producer→consumer; follows the actual governed DAG.
3. **Serving-context edge** — hydration, source drill, whole-chart context, query relevance; a query may revisit L0 after L3; not a reverse build dependency.
4. **Evaluation edge** — frozen claims and purpose-admitted observations into protected comparison.
5. **Next-generation artifact edge** — separately admitted immutable rule/model/qualification release; "No live outcome table, personal weight or cached retrospective summary becomes an implicit predictor input."

Plus the feedback rule: L4's outcome vocabulary may inform *design* of L0/L3, but "A chart-specific L4 conclusion must not feed back into the L3 computation as independent evidence."

## The "ten obligations"

**Clarification first:** the phrase "ten obligations" appears in this document in two places, and the "Dom→Carr" you recalled is the changelog shorthand for native ruling 11 — "`Domain correctness` ... gate Dom -> Carr" in the parent's changelog means the Domain correctness obligation was moved from the data plane ("Dom") to the reasoning layer / Source **carriage** row ("Carr"). The ten load-bearing sets are:

### (A) The product's proof obligations — "ten, not eleven" (§13.3 item 1)

> **Ten, not eleven, and deliberately so:** `Domain correctness` — whether the astrology is *right* — is **not** a data-plane obligation (native ruling, 2026-09-25). This plane computes faithfully and carries the tradition's testimony, its witnesses and their disagreements intact; the verdict is formed above it, in the reasoning layer. Carriage of that evidence is required of every layer (§12.2, Source carriage and reproduction); judgement of it is not, and a layer plan that awards itself a doctrinal verdict has exceeded its plane.

So the ten data-plane-scored obligations are the parent's §14 table **minus Domain correctness**, whose mechanical half survives as the **§12.2 "Source carriage and reproduction"** test row (assigned to every layer):

> The cited passage is present beside the encoding and they agree; where two admitted witnesses differ, the difference is **carried unresolved** and never averaged or silently settled; a classical quantity re-derived from different inputs reproduces within a declared tolerance. This plane proves faithful transmission and reproduction; **whether the astrology is right is judged above it** (native ruling, 2026-09-25) — no verdict on doctrine is reached here, and no human verification step exists or is implied.

The per-layer assignment of the ten comes from parent §11's layer table (L0→Source/domain fidelity; L1→Computational correctness; L2→Concept/relationship completeness + Interpretive fidelity; L3→Temporal integrity; L4→Interpretive fidelity + Distinctive understanding; L5→Predictive performance + Operational honesty).

### (B) The seventeen DP cross-layer contracts (§7.1) — "exactly how the value moves"

These are the other numbered obligation set (DP01–DP17, note DP15 splits into DP15a/DP15b). Verbatim table rows:

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

### (C) The controlled-vocabulary rules (§4.1) — six rules with detectors, owned by L0

> Every entity, concept, method, convention, unit and event class the plane names has **exactly one canonical identifier and one closed alias set**, and that set is the only permitted surface for the thing — in every writer, every service, every prompt, every export, and every **external** interface.

Rule 1 (as amended 2026-09-26, decision 16): "One canonical id, one closed alias set, per thing... owned by L0 (`bg_ontology` is the identity owner; specialized `bg_*` assets own their specialized semantics)"; detector now tests `count(*) = count(DISTINCT <the authority's DECLARED key>)` — for `brahma_ontology`, `(entity_class, canonical_id)`. Rules 2–6: set is the only permitted surface (fail-closed `UnknownIdentity`/`AmbiguousIdentity`); one-directional deterministic resolution; code-side snapshots generated/pinned/parity-tested ("A hand-maintained mirror is a second authority, and a second authority is a defect"); external inputs typed to the set; independent maps counted, permitted count one per class. Scope: "all sixteen entity classes."

## The `[TRANSFERS]` convention

Defined in §1:

> Where this document says "the plane", it means the data plane; obligations that cross into retrieval or conversation are stated here too, because there is nowhere else yet to state them: **the retrieval and conversation planes are not built** and have no governing artefact of their own (parent §1.3 records exactly this). Every obligation in this document that belongs to one of them is marked **[TRANSFERS]** — it moves to that plane's artefact, unchanged in substance, when that plane is elevated. A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work.

Marked [TRANSFERS]: **all of §8** ("Intermediaries are part of the data-plane value chain" — retrieval/conversation plane obligations, with the one permanent data-plane exception: "what a producer owes **about itself**: DP10 capability metadata, its real scope, and its honest gaps"), and two §12.2 test rows: **Presentation parity** and **Delivery sentinel**. The changelog (third FINAL change, item c) confirms: "§8 plus two §12.2 rows are marked [TRANSFERS], moving to those planes' artefacts unchanged when they are elevated."

## Shared tables, carriage checks, asset-vs-layer responsibilities

- §3.3: "Do not require every L1–L5 resource to have a chart row. Shared L5 qualification/model resources and global services retain registered scope." And "Layer ownership is not epistemic type" — L1 contains judged structure (`ga_vichara`) etc.; each output must be typed (astronomical calculation, classical-rule application, engineered/native judgment, approximation, observation, empirical/model result).
- §4.1: within L0, identity ownership is split asset-by-asset — `bg_ontology` owns identity; `bg_reference`, `bg_formula_constants`, specialized references own specialized semantics; "the L0 plan binds that boundary asset by asset, it does not reopen who owns identity."
- §3.4 presentation contract assigns "carriage" of each acharya-rendering field to specific DP contracts (method/school→DP02; passed clauses→DP05; conventions→DP01/DP03; intermediate quantities→DP03/DP04; dignity components→DP04; competing readings→DP06+DP02; typed chains→DP06; clock geometry/activation/manifestation bridge→DP07/DP08/DP09). §13.3 item 6 requires each layer plan to state "which §3.4 presentation rows this layer carries and which fields it hands onward for them."
- §9.1 names the concrete observation-ownership starting point (`life_events`/`lel_events`, `mi_jivanaghatana`, `ph_nimitta`/`mi_bhavisya`, `brahma_prospective_ledger` vs `brahma_mimamsa_prediction_ledger`) — an asset-vs-asset responsibility split the L5/intake brief must resolve.
- §6.4: `ka_kshetra` contributes "as a mechanism-qualified candidate substrate, not ... a universal authority."

## Counts the document states (verbatim, with section)

- **Six layers**: "The retained six-layer architecture is appropriate" (§1); "No seventh layer, universal truth graph or new parallel registry is proposed" (§1).
- **Three planes**: "This is one plane among three" (§1).
- **129 assets**: "It is not six completed layer audits or 129 completed asset certifications." (§1.2)
- **Five edge types** (§3.2 heading "Five edge types—not an all-to-all build").
- **Six rules** of the controlled vocabulary (§4.1: "Six rules, each with a detector").
- **Sixteen entity classes** (§4.1: "all sixteen entity classes of the ontology — planets, signs, houses, nakshatras, vargas, karakas, aspect types, upagrahas, yogas, doṣas, daśā systems, domains, concepts, remedy types, texts, schools").
- **Six semantic families** (§4.2 table).
- **Four synergy seams** (§3.5: controlled vocabulary, DP contracts, edge ordering, presentation contract).
- **Ten proof obligations, not eleven** (§13.3 item 1, quoted above).
- **§13.3 is "Ten elements"** with items 1, 1a, 1b, 2–8 (lettered rather than renumbered "because the template and the L0 instance cite these numbers"). Note the changelog's (f) says "§13.3 is nine elements and says so (1a kept rather than renumbered...)" at the FINAL fold, and the later 1b elevation made the section header read "Ten elements" — the header text is current; treat "10 elements = 1, 1a, 1b, 2..8" as authoritative.
- **Eight-disposition hierarchy** P/I/E/Q/C/H/R/U (§10.1); changelog confirms "the eight-disposition hierarchy."
- **Six evidence states** (§11: "source present → qualified → consumed → effect traced → served → value evaluated"; also §12.2 references "§11's six evidence states").
- **Thirteen V-journeys** V01–V13 (§2 table; V13 = P24 present interval).
- **Seventeen DP contracts** DP01–DP17 with DP15a/DP15b (§7.1).
- **Ten work packets** W01–W10 (§13.1).
- **Three proving stories** (§12.1) plus additional proofs listed after them.
- **18 test rows** in §12.2's "Tests that demonstrate use and value" table (Qualification/source; Numeric/context; Source carriage and reproduction; Presentation parity [TRANSFERS]; Vocabulary conformance; Relevant perturbation; Irrelevant control; Dependence control; Missingness control; Omission challenge; Delivery sentinel [TRANSFERS]; Temporal boundary; Historical/firewall; Revision; Incremental value; Empirical performance; Synergy — count them as 17 rows in the table; I count 17).
- Frontmatter review counts: REVIEW_DATA_PLANE_FINAL_v1_0 "REJECT, 2 BLOCKER + 9 MAJOR + 10 MINOR; all folded ... 1 restated and 1 withdrawn by native ruling 11"; earlier REVIEW_DATA_PLANE_v3_0 "2 BLOCKER + 10 MAJOR + 11 MINOR; 10 folded at FINAL, 6 partly, 5 outstanding."
- `qualified` "used 71 times here" (changelog 3.0 entry).

## Per-layer guidance feeding the layer-instance skeleton (§13.3, verbatim — the ten elements)

> 1. Consumer value and distinctive layer responsibility; the inherited P-needs, V-journeys and DP contracts; and **which of the product definition's ten proof obligations this layer is scored on**, per its §11 layer table. A layer plan that names its own criteria instead of inheriting these is not derived from the product definition. [+ the "Ten, not eleven" paragraph quoted above]
> 1a. **Vocabulary conformance (§4.1):** which entity classes the layer emits or accepts; that every one resolves through the controlled set; the independent-map census per class; and, for L0 only, that it *owns* the set and its releases.
> 1b. **The three value terms (§3.5):** the layer's individual, synergistic and cross-layer-handoff terms, each with the instrument that measured it, or an explicit absent instrument. A synergy figure without a harness is an invented computation.
> 2. Complete owned inventory including accepted, residual, service, shared and historical capital; source/runtime evidence levels separated.
> 3. Internal asset interplay, exact input/output/use matrix and boundary with adjacent layers and answer authorities.
> 4. Qualified Jyotish coverage: prerequisites, variants, exceptions, negative cases, uncertainty and source rights where relevant.
> 5. Component-level preserve/integrate/enrich/qualify/consolidate/restrict/retire decisions, with unknowns retained honestly.
> 6. Upstream demand and downstream offers with field/grain/context/lineage contracts, named owners and tests, **including which §3.4 presentation rows this layer carries and which fields it hands onward for them**.
> 7. Generation/invalidation, compatibility, retained history, cost and rollback.
> 8. Bounded work packets, dependencies, focused proof, consumer cutover and remaining activation decisions.

And the asset-brief level (§13.3 closing):

> Each **asset brief** then supplies the P-needs it serves and the parent's ten proof obligations it is scored on (item 1), its manifestation or temporal role, actual tables/services/columns, current algorithm and consumers, preserved kernels/tests, exact delta and expected semantic difference. No new field is considered "used" until its transformation and receiving answer obligation are proved.

**Adoption and derivation order** (§15): "The L0 plan is derived from it; L1–L5 follow in dependency-aware order ... and each begins by backcasting the named consumer distinctions into exact obligations rather than by surveying its own assets."

## Inheritance lists (frontmatter)

- Tier 1: `inherits: []`, `produces: [MADHAV_DATA_PLANE_VALUE_ARCHITECTURE]`.
- Tier 2: `inherits: [00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md]`, `produces: [LAYER_DEFINITION_AND_STRATEGY_TEMPLATE, "six layer instances L0-L5"]`.

## Where deriving L1–L5 layer instances from this summary alone is impossible

1. **The tier-3 template itself** (`LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`, now v1.2 per parent changelog — "§2.7 rescoped, gate Dom -> Carr") defines the actual skeleton parts (your "parts 0, 1.1, 2.1–2.7" numbering comes from there, not from either sealed document; neither sealed document uses those part numbers). Must be read directly.
2. **Per-asset membership and provisional dispositions** live in the companion `MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md` — only named selectively in tier 2.
3. **Source-grounded evidence** ([S01]–[S05] findings, inspected paths, the 129-asset universe) lives in `MADHAV_DATA_PLANE_V2_REVIEW_RECORD_v1_0.md`.
4. **Per-layer asset family detail** in §6.1–§6.6 is summarized above only at the level tier 2 states it; the register and live repository are the authority for actual tables/writers.
5. The **L0 layer instance already exists** (frontmatter `authority:` says "the L0 layer instance is derived from it"; §4.1 references "the L0 plan") — L1–L5 should follow its realized shape; read it before drafting.