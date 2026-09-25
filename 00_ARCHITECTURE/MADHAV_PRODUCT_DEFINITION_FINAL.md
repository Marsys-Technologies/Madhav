---
artifact: MADHAV_PRODUCT_DEFINITION_FINAL.md
canonical_id: MADHAV_PRODUCT_DEFINITION
tier: 1
kind: instance
chain: 00_ARCHITECTURE/briefs/nirmana/ELEVATION_DERIVATION_CHAIN_v1_0.md
inherits: []          # the root of the chain
produces: [MADHAV_DATA_PLANE_VALUE_ARCHITECTURE]
version: "FINAL"
status: CURRENT
produced_on: 2026-09-24
review_record: briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md  # verdict ACCEPT, 11 MAJOR + 14 MINOR, all folded
p_identifier_note: "P-identifiers renumbered at v3.1: v3.0 P20 (observation briefs) removed; v3.0 P21-P24 became v3.1 P20-P23. Any lineage citation of P20-P24 refers to v3.0 numbering. P24 at FINAL is a NEW need (present-tense), appended rather than renumbered."
decision_owner: Native
supersedes: "MADHAV_PRODUCT_DEFINITION_v3_0.md (CURRENT 2026-09-13 → SUPERSEDED). v3.0 is retained as the historical adopted master; its authority record CCD-010 is not retroactively withdrawn."
role: "Target product definition. Governing reference for data-plane and layer planning. Not a certification of implemented or deployed capability."
does_not_authorize: "Implementation, data changes, production deployment, merge or push."
changelog:
  - "FINAL (2026-09-24): review REVIEW_PRODUCT_DEFINITION_v3_1.md returned ACCEPT with 11 MAJOR and 14 MINOR findings; all folded. Native-directed before review: §1 differentiator restated against existing software rather than against a human (conventional Jyotish software computes each element on demand and presents it; Madhav computes the whole estate and the relationships between its parts, and no existing Jyotish software applies AI across that depth); §2 one voice with the acharya presentation carrying more technical machinery and the layperson less, with identical finding, confidence and uncertainty; learning output restored. From the review: `qualified` defined once as a four-part predicate; `permitted` replaced by `earned` where the cleanse left it without a referent; ablation named as the per-asset scoring method for the ten obligations; the §11 layer proof column joined to the §14 obligations; life-event switch state added to the forecast emission record; Delivery fidelity extended to test both presentation modes; named temporal instruments restored to §3.10; narration-vs-arithmetic verification restored; chronology-reset and reporter-hindsight leaks restored; out-of-scope research moved from §4.1 to a §13 boundary; four phrasings of the nearest-versus-better-supported obligation unified; governance residue, the duplicated rectification bullet and the mandatory-pass-count negation removed. P24 added as a NEW present-tense need, appended rather than renumbered."
  - "3.1 (2026-09-24, native-directed cleanse): §1 rewritten to lead with the differentiator. §2 primary audience corrected to serious layperson AND advanced acharya. Lifespan restored. Life Event Log placed behind a single switch. REMOVED: cross-subject hypothesis testing and the research observatory; lost-knowledge recovery and reconstruction; expert-panel assessment; the four-pathway life-event table; voluntary-practice/coercion/monetized-fear clauses; third-party, minors and consent-enforcement clauses; the death, illness and fertility exclusions; the scholarly-laboratory and research-workbench horizons. RETAINED deliberately: the prohibition on invented computation, source, detector, confidence or score, and ablation testing."
declined:
  - "Review removal candidate 2 (drop P14 relational/entity) and 3 (drop P20 method selection): DECLINED here — removing a consumer need is a product-scope decision for the native, not a copy-edit. Both rows stand pending a ruling."
  - "Review removal candidate 7 (§3.12 breadth-of-tradition paragraph): the review itself refers this to the native. Retained."
  - "Borderline restorations not taken: the completion manifest (v3.0 §5.3) and replay-vs-regeneration (v3.0 §6) are transport-layer detectors better specified in a layer plan than in the product definition; subject-substitution as generic-answer detector is covered by §14's Distinctive understanding row requiring ordinary as well as dramatic cases."
---

# Madhav — the product we intend to build

## 1. The defining promise

Madhav computes what no astrologer can compute by hand, at a volume and depth no single mind can
hold, and uses artificial intelligence to turn that computation into understanding.

That is the whole differentiator, and it has two halves that only work together:

- **Data engineering** performs chart computation at a depth, resolution and interconnection that
  existing software does not reach. Conventional Jyotish software computes each element on demand and
  presents it — a varga when asked for it, a daśā table when asked for it. Madhav computes the whole
  estate and, critically, the **relationships between its parts**: every graha in every relevant
  condition, across every applicable varga, relationship chain, clock and window, held together and
  cross-referenced rather than produced one panel at a time for a person to reconcile by eye.
- **Artificial intelligence** reads across that computed depth to find the connections, relationships
  and patterns inside it, and derives interpretation, insight and prediction from them. No existing
  Jyotish software does this at all — it presents computation and leaves the reasoning to the reader.

Neither half is the product. A very large computation nobody can interpret is a database. A capable
model without that computation beneath it is a chatbot with astrological vocabulary. The product is
the join: **insight that was not previously derivable, because the depth it rests on was not
previously computable.**

An acharya holds a chart in working memory and reasons brilliantly over the part they can hold.
Madhav holds all of it, finds what connects across the whole, and explains what it found. The
ambition is extension of reach, not a claim that any individual reading is superior — the acharya is
the standard the instrument is measured against **and** one of the two people it is built for.

Three commitments define what a reading must do:

- **Understand:** reveal distinctive capacities, tensions, configurations, cross-domain relationships
  and their competing interpretations.
- **Navigate:** explain what persists, what changes, what may activate, how possible manifestations
  differ and what can responsibly be forecast or compared.
- **Account:** preserve the question, admitted evidence, interpretation, forecast and subsequent
  challenge; learn only through qualified, visible processes.

Prediction is central, not an ornament. A reading need not invent a forecast to justify itself;
scholarship and explained exact computation are valuable in their own right.

### 1.1 Quality before speed; completeness before polish

An interpretive question is an investigation. Processing speed is subordinate to depth, breadth,
concept coverage and predictive usefulness. Effort follows the question and the emerging evidence.

### 1.2 The unit of value: an earned distinction

The unit of value is something the person can now understand, discriminate, prepare for or test that
a competent simpler answer did not provide. More assets, obscurer techniques, higher agreement counts
or longer output are not intrinsically more value. Every addition must show what it contributes.

## 2. Who the product serves

Two primary audiences, one depth:

- **The serious layperson** — seeks real understanding of their own life, may know no Jyotish
  terminology, and receives the full depth expressed in plain language.
- **The advanced Jyotish acharya** — works in the tradition's own vocabulary, and receives the same
  analysis expressed in Jyotish terms with its conventions, prerequisites and exceptions explicit.

These are **two presentation modes over identical analytical depth**, not two products and not two
tiers of rigour. The analysis is one analysis and the portfolio below is written in one voice; what
differs is how much of the astrological machinery is exposed.

- **The acharya's presentation carries more technical detail** — the method and school, the
  prerequisites tested and the exceptions checked, the conventions and ayanāṃśa in force, the
  intermediate quantities, the dignity and strength components separately, the competing readings and
  which classical authority each rests on.
- **The layperson's presentation carries less** — the same finding, the same confidence and the same
  uncertainty, with the machinery behind it available on request rather than in the way.

Nothing is withheld from the layperson: the conclusion, its strength and its limits are identical,
and any technical layer can be opened. Nothing is simplified for the acharya: it is named correctly.
A difference in exposed detail is never a difference in what was computed or concluded.

A person is not a chart. An interpretation does not establish moral worth, fixed identity, another
person's thoughts or an inevitable destiny.

The following is a target portfolio, not a current availability list. Questions are written in the
subject's voice. The acharya asks the same questions of any chart whose subject has its own
foundation; the answers are the same analysis in the tradition's terms.

| ID | Consumer need | Intended value and necessary distinction |
|---|---|---|
| P01 | "What are my distinctive capacities and recurring patterns?" | Connected structure, vocation and tensions; not personality labels or invented biography. |
| P02 | "What gives this life direction or meaning?" | Dharma, purpose and spiritual inquiry grounded in attributed traditions; no spiritual ranking. |
| P03 | "When will I make substantial money or emerge from financial strain?" | Distinguish earnings, receipts, profit, liquidity, obligations, accumulation and retained prosperity. |
| P04 | "When will my business succeed or I receive a promotion?" | Distinguish commercial growth, resilience, recognition, title, responsibility, authority and compensation. |
| P05 | "How should I understand relationships and marriage?" | Personal interpretation and timing; another person's chart or inner life is not inferred without their own foundation. |
| P06 | "What can I understand about family, parenthood and legacy?" | Domain interpretation; no blame directed at a family member. |
| P07 | "What does the tradition say about wellbeing?" | The tradition's own testimony on constitution, vitality and vulnerability, with its sources and limits stated. |
| P08 | "What about education, home, movement, travel or relocation?" | Domain-specific interpretation and feasible comparison with practical constraints. |
| P09 | "Does this yoga form, and when might it manifest?" | Prerequisites, formation, exceptions, bhaṅga, qualified expression, multiple activation routes, nearest versus better-supported window. |
| P10 | "What chapter am I entering, and how is it unlike the previous one?" | Enduring structure versus temporal expression, recurrence with differences, connected cross-domain trajectories. |
| P11 | "When might I initiate something, or which practices can I explore?" | Timing context and attributed practices from the tradition. |
| P12 | "Which events fit this interpretation, and which do not?" | Fit, misfit, non-events and unknowns; hindsight is not prospective success. |
| P13 | "Does uncertain birth information or a different convention change this?" | Stable versus sensitive conclusions. Rectification is an explicit hypothesis process, never silent correction. |
| P14 | "How do two people, a shared undertaking or an organization relate?" | Horizon: requires each subject's own foundation; no invented entity birth moment. |
| P15 | "What supports this in the tradition, and where do schools disagree?" | Source testimony, method plurality and honest disagreement. |
| P16 | "Give me this exact fact," or "Help me investigate an open question." | Proportionate exact lookup or deep inquiry. Do not manufacture interpretation for a simple fact. |
| P17 | "What important question have I not asked?" | Consequence-ranked discovery of real tensions or missing distinctions; no invented crisis and no flattery. |
| P18 | "What would most efficiently resolve this uncertainty?" | The smallest admissible information or analysis step, its burden and residual limits. |
| P19 | "Show what changes if we examine this differently." | Controlled input, method or feasible-choice comparison, not two separately persuasive essays. |
| P20 | "Which form of Jyotish is appropriate to my question?" | Method selection and honest limits. |
| P21 | "What does this day or period mean in its proper context?" | Pañcāṅga and calendar with correct date, location and time zone; general context is not automatically personal relevance. |
| P22 | "Let me read and understand the texts themselves." | Passage, chapter and whole-text access where rights permit; editions, translation, context and variants. |
| P24 | "What is happening to me right now, and why does this period feel the way it does?" | The present-tense need: which mechanisms are active now, what they are doing, and how the current interval differs from the one before it. Neither a forecast nor a history. |
| P23 | "What does the tradition say about lifespan?" | Āyurdāya as the classical discipline it is: the applicable method, its inputs, the schools' disagreement, the cancellations and the genuine uncertainty. Presented as the tradition's computation and its limits, never as a bare date. |

Natal interpretation is the first proving centre, not the intellectual limit. An unanswered valuable
question is a build requirement when a missing capability is the reason.

## 3. The Jyotish substance: what depth actually requires

Coverage obligations, not a compulsory sequence. **Qualified**, throughout this document, means
exactly one thing: the method's sources, conventions, prerequisites and exceptions are on record
before it is applied. An unqualified method may be named and explained; it may not carry a finding.

### 3.1 Graha as a contextual participant

Distinguish natural significations, chart-specific functional role, house lordships, kāraka roles,
placement, relationships, condition and temporal participation. These roles can support opposing
conclusions and must not be flattened. Aliases, Sanskrit names and transliterations resolve to
canonical identities in Brahmagyan; a downstream asset must not invent its own Sun, house, nakshatra
or dignity vocabulary because a name looked similar.

### 3.2 Rāśi, bhāva, lord and kāraka as a relational architecture

Domain understanding must consider the relevant house, its occupants, lord, significators, associated
houses and connected domains under the selected method. Sign position and house position are distinct
where the method makes them so. Connect obtaining resources with retaining them, recognition with
authority and responsibility, a relationship with its wider life context — through an actual
qualified relationship, not thematic association.

### 3.3 Condition, dignity, bala and avasthā

Dignity, strength components, motion, combustion, proximity and planetary state retain separate
meanings, units and scope. A single score cannot silently collapse capacity, beneficence and
timing. Where a strength system's components disagree, preserve the disagreement. An exact calculated
number is not an exact life prediction. Missing computation is a named gap, never a neutral default.
**Narration of a number requires semantic verification separate from arithmetic verification:** a
correct figure can still be described wrongly, and the sentence that grades it is not covered by the
check that produced it.

### 3.4 Sambandha and chains of influence

Aspects, conjunctions, exchanges, dispositors, nakshatra-linked dependencies and argalā/virodha must
be typed and method-qualified. Follow material chains beyond one hop, handle cycles, identify decisive
intermediaries and test inhibiting or cancelling relationships.

Shared roots must remain visible: several assets derived from one placement are **not independent
confirmations**. Their differing interpretations may still add value — count the contribution without
manufacturing independent evidence.

### 3.5 Bhāvat Bhāvam and derived reference frames

Where a qualified method makes it relevant, investigate the actual derived-house relationship, its
basis, participating lords, conditions and interaction with the primary domain. Mentioning the term,
calling a tool or returning an empty result is not proof of application.

### 3.6 Varga: domain-specific resolution with sensitivity

Divisional charts are used with their qualified domain, construction method, reference conventions and
input sensitivity. A varga is not an interchangeable magnifying glass or another independent vote on
the same natal input. Explain convergence and tension between rāśi and varga findings, including what
changes when an uncertain birth input crosses a boundary.

### 3.7 Yoga, doṣa, cancellation and manifestation

Each named configuration requires its actual formation conditions, participants, strengths,
limitations, exceptions, cancellations and source identity. **A catalog label is not a confirmed
formation.** Ordinary combinations, conflicting indications and periods without spectacular yogas
deserve equally serious analysis. No doṣa label becomes a moral verdict or a frightening identity.

### 3.8 Nakshatra, pada, symbolic meaning and specialized significators

Nakshatra and pada connect to qualified roles, relationships, timing and interpretation rather than
remaining decorative labels. Symbolic, deity-related or mythic material retains source context; it is
not literal biography. KP and other sub-lord approaches operate on their own conventions and complete
prerequisites — shared vocabulary does not authorize importing one school's machinery into another.

### 3.9 Ārūḍha, special lagnas and alternative perspectives

These distinguish resources, appearance, standing and other facets a single view conceals. Reveal
meaningful differences between underlying capacity, perceived status and realized circumstance where
qualified support exists. Do not force agreement across frames.

### 3.10 Kāla: structure meeting time

The temporal layer is a major source of distinctive value: which enduring structures are engaged, how
and when. Daśā systems and nested periods, gochara, transit conditions with their aṣṭakavarga and
vedha qualifications, annual and return methods, Tājaka, tithi-praveśa and Sudarśana.

Compute boundaries, calendars, location and time-zone conventions, hierarchy and reference frames
correctly. Distinguish a background period, an enabling interval, a specific contact, an inhibiting
condition, recurrence and inferred manifestation. Compare nearest versus better-supported later windows under a
**named criterion**. Explain why several apparent triggers differ, what they share and what remains
unknown. Support cross-domain trajectories across a chapter.

### 3.11 Pañcāṅga, Praśna and Muhūrta are distinct practices

Calendar context, personalized relevance, casting a question-moment chart and selecting an initiation
interval are different operations with different inputs and applicability. Electional work
incorporates the actual undertaking, constraints, location and method, and distinguishes initiation
suitability from eventual outcome.

### 3.12 Remedies and the breadth of the tradition

Attributed remedial and spiritual practices help someone understand the tradition and make an informed
choice. Distinguish source testimony, symbolic significance and practical burden. The product studies
Jyotish across its mathematical, natal, interrogational and electional traditions; Siddhānta, Horā and
Saṃhitā supply a wider horizon than a natal report.

## 4. Sources, method plurality and grounding

Six kinds of knowledge remain distinguishable throughout: source testimony; qualified rule; computed
configuration; interpretive inference; real-world claim; and evaluation.

Build a coherent reading within each applicable method before comparing methods. Preserve conventions,
sources, exceptions and disagreements. Do not average incompatible schools or treat them as
interchangeable votes.

### 4.1 From a source to its actual interpretive consequence

The person can move from a rights-permitted passage, chapter or whole text to its language,
transliteration, context, edition, translation, variants and commentary. An inspectable rule dossier
joins textual testimony, scope, prerequisites, exceptions, disputed readings, implementation
qualification and worked examples.

## 5. The investigator: from a question to an earned reading

Understand and where useful reformulate the question; identify the intended outcome and horizon; ask
only consequential clarifications; consult the whole chart before domain detail. New evidence must be
able to trigger further retrieval or qualified computation, not merely another paragraph. Adjacency is
justified by a relationship to the question, not unlimited exploration.

Interpretive queries retain the governed whole-chart Bodha consultation before domain detail.
Pinpointed factual lookups retain the frame-check and escalation valve rather than a full synthesis.

### 5.1 A coverage discipline that challenges the initial planner

Maintain an explicit, expandable map of question obligations, applicable concepts, facts, relationship
paths, candidate findings and unresolved frontiers. An independent omission check asks what the
planner never considered.

Each material obligation ends as **applied, inapplicable with reason, unavailable, unqualified,
contradictory, or still unexplored**. These states are not interchangeable. This is accountable
completeness against an explicit scope, not exhaustiveness over an open-ended tradition.

### 5.2 Competing interpretations and typed confidence

Significant interpretive judgments carry material alternatives rather than a single asserted reading.
Do not fabricate alternatives. Keep deterministic fact, structural prior, classical
prior, empirically calibrated claim and unresolved interpretation distinct. A probability, a
comparative grade, an astronomical timestamp and a reliability statement are different objects.

### 5.3 The answer carries the findings

The delivered reading begins with a clear synthesis and includes every identified relevant fact and
its interpreted contribution. Where significance is conjoint, explain what the connected facts mean
together. Detail may sit beneath, but a follow-up question must never be required to discover an
already identified material finding.

The person receives evidence, derivations and rationale — not private internal deliberation. Plain
language must preserve conceptual precision.

### 5.4 The question compass

Suggest a few consequential next investigations: a real uncertainty, a sensitive input, an unqualified
exception, a contradictory relation. Rank by probable information value and practical consequence, not
emotional intensity or retention. Sometimes the right answer is that more analysis will not add value.

## 6. Controlled comparison and two states of understanding

All comparison in this product is **within a chart**. Three kinds remain distinct:

| Comparison | What changes | What it can establish |
|---|---|---|
| Input sensitivity | A declared uncertain input or computational convention | Which findings survive, weaken, disappear, reverse or cannot be assessed. |
| Method comparison | A qualified rule, school or interpretive operator | Dependence on that method. Removing a method does not simulate removing a planet's influence. |
| Feasible-choice comparison | Actual options, objectives, constraints and timing assumptions | Differences in supported interpretation and uncertainty alongside practical considerations. |

Each requires real alternate computation, pinned inputs and versions, and matched claim identities.
**Two unconstrained AI essays are not a controlled comparison.**

The person can also compare two states of understanding: what changed because of corrected birth
input, a different question, new source knowledge, a changed method or newly available computation.

## 7. Prediction: specific when earned, accountable when emitted

The central chain is:

**formation and condition → eligible structural mechanism → applicable temporal activation →
qualified manifestation alternatives → earned external-outcome forecast.**

Every link needs its own support. The chain may stop before the last link; say precisely where. A
catalog match is not formation, formation is not manifestation, and temporal activity is not proof of
an event.

### 7.1 Manifestation and temporal precision

A promotion inquiry distinguishes title, authority, workload, recognition and pay. A financial inquiry
distinguishes receiving money from retaining it, and temporary relief from structural recovery.
Compare nearest versus better-supported later windows under explicit criteria.
"Strongest" is not an unexplained scalar. **"None found" must state the searched horizon, resolution
and method coverage.**

### 7.2 Preserve the forecast actually delivered

An external-outcome forecast is structured at emission with its proposition, outcome definition,
timing, assumptions, information cutoff, **life-event switch state (§8)**, evidence, method versions and original wording. Computed
dates, retrodictions and external-outcome forecasts are different claim types. **A real prediction
cannot escape accountability by later being called "symbolic" or "only an activation."**

### 7.3 Evaluate without hindsight

Freeze the evaluated proposition before the outcome is known. Keep partial, lapsed, disputed and
unverifiable outcomes visible; a missing observation is not an automatic success or failure, nor
permission to drop a difficult case. A rebuild must not reset chronology: re-stamping emission time
turns a frozen claim into a hindsight leak. An observation reported after the person has seen the
forecast is not automatically independent. A functioning feedback loop proves lifecycle behaviour, not
forecast accuracy.

**What learning produces.** Learning's output is a visible change to a claim family's scope,
confidence or availability, with the reason stated: a family may be revised, narrowed, demoted or
withdrawn where the evidence warrants it. Evidence that cannot change what the product says is not
learning. Attributed traditional interpretation may remain available where a restriction applies to
the product's own forward claim rather than to the tradition's testimony.

## 8. Life-event evidence sits behind a switch

Life-event information supplied at chart creation or in a Paripraśna session may enrich the product's
computation — but its use is governed by **one explicit switch**, not by scattered policy.

- **Switch ON.** Life-event-derived computations, enrichments and comparisons are available. The
  product may align reported intervals with independently computed mechanisms, examine fit and misfit,
  and show life events in the inquiry surface.
- **Switch OFF.** No life-event-derived computation is available anywhere in the product. Every
  reading emits only what the chart, sources and methods produce on their own. The chat and inquiry
  surfaces show no life events. Nothing silently degrades to a partially-conditioned answer.

There is no third state. A reading is either produced with life-event enrichment or without it, and
which one must be knowable from the reading itself.

### 8.1 Layer-specific contribution without contamination

These are **correctness rules**. Violating one makes the output wrong, not merely inappropriate.

| Layer | Valuable use where enabled | What must not happen |
|---|---|---|
| L0 — Brahmagyan | Shared event vocabulary, precision and provenance definitions | Private observations becoming global doctrine or reference truth. |
| L1 — Gaṇita | Event-time astronomical calculation from supplied dates | Altering birth facts or chart calculations to fit biography. |
| L2 — Bodha | Historical comparison of proposed structural interpretations and rival expressions | Making biography-dependent support appear to be event-free chart structure. |
| L3 — Kāla | Align reported intervals with independently established temporal mechanisms; inspect unmatched windows | **Using the observed event to choose the supposedly prior trigger.** |
| L4 — Phala | Refine manifestation distinctions; preserve exact forecast outcome definitions | Rewriting the original forecast to fit the eventual story. |
| L5 — Mīmāṃsā | Adjudication, misfit analysis and qualified calibration | Outcome leakage into prospective generation, or unqualified learning promotion. |

### 8.2 A fair reading of history

Invite peak events, ordinary periods and relevant non-events; do not assume an incomplete history is a
complete one. Preserve uncertain dates. Corrections propagate to the consumers of the corrected
evidence while retaining version history.

## 9. The experiences the person should be able to live through

Connected experiences, not a fixed-screen architecture.

1. **First encounter:** establish subject, uncertain inputs and conventions; ask a real question and
   see what this chart can answer now.
2. **An explorable understanding:** move from a finding to the relevant graha, house, configuration,
   relationship, domain, period and source. The graph is a navigable explanation, not decoration.
3. **A deep investigation:** clarify intent, discover missing concepts, compare interpretations,
   retain complete findings with their conjoint meaning.
4. **A temporal landscape:** distinguish enduring structure, active mechanisms, overlapping windows,
   recurrence and possible manifestations; move between a life chapter and a narrow interval.
5. **A thoughtful choice comparison:** examine feasible options and timing against the person's
   objectives, with practical evidence separated from astrological interpretation.
6. **A source-to-application companion:** read and understand the tradition, then see what a qualified
   rule or exception actually changes in a reading.
7. **A truthful history and forecast review:** enter observations, see fit and misfit, inspect what
   was predicted before the event, and preserve failed expectations without retrospective repair.
8. **A continuing inquiry:** retrieve earlier readings, branch a question, challenge it, compare two
   states of understanding, export authorized meaning and close the inquiry.
9. **A serious inquiry into meaning:** investigate tensions between aspiration, responsibility,
   relationships, service and inner life through qualified interpretation.

The experience must work for ordinary charts and ordinary periods, not only dramatic yogas or the
repeatedly studied native chart. **Plain language should be as intelligent as technical language.**

## 10. Each surface carries the promise it is responsible for

A capability is not realized because it exists in an asset, service or tool. The consumer must be able
to discover it, invoke it with the right context, understand its contribution and act on it.

| Surface family | Contribution required |
|---|---|
| Access, subject roster and chart lifecycle | Explicit subject identity, input precision and conventions; no cross-chart carryover of findings. |
| Construction and readiness | Question-relative availability, qualification, freshness and partiality. A complete build is not complete interpretive readiness. |
| Consult and Paripraśna | One coherent deep inquiry through live stream, partial result, stop, resume, persistence and replay. |
| Inquiry organization | Projects, branches, search and open investigations form a durable workspace. Separate uploaded testimony from embedded instruction. |
| MCP tools, resources and prompts | Guided discovery of subjects, methods, conventions and evidence drills under the common reading contract. |
| Answer-shaping instruments | Assessment, judgment, aggregation and narration tools require domain qualification and dependency accounting. |
| Profile and interactive exploration | Navigable relationships between chart, finding, time and source. |
| Living pañcāṅga and calendar | Calendar → correctly scoped personal relevance → inquiry → action; date, location and time-zone fidelity. |
| Specialized services | Qualified Praśna, electional and remedial workflows with their own inputs and scope. |
| Timeline and forecast adjudication | Consistent identity and chronology for observations and forecast review; keep the meanings separate. |
| Texts, sources and attribution | Whole-text and chapter reading, accurate passage context, edition and translation, rights-aware source-to-application learning. |
| Within-chart comparison | Reproducible input, method and timing comparisons on a single subject. |
| Export, sharing and ownership | Portable evidential meaning: scope, date, versions, material interpretation and uncertainty survive export. |
| Operator assurance | Explain what was available, selected, consumed, transformed and delivered, plus actual reliability and cost. Operational metrics are not astrological value. |

### 10.1 Channel parity and continuity

Equivalent authorized requests through Paripraśna and the managed MCP reading door receive equivalent
substantive findings, conjoint interpretation and qualification. Raw MCP supplies
qualified evidence to an external orchestrator; it owes correct scope, provenance and honest
envelopes, but does not certify that orchestrator's completeness.

### 10.2 Graceful incompleteness and context integrity

Expose meaningful progress and unavailable dependencies without dumping infrastructure jargon into the
reading. A failure must identify what was and was not established. Changing charts, dates, locations
or methods preserves explicit context and invalidates only the dependent work.

## 11. The retained data plane and its contribution contracts

| Layer | Product responsibility | Proof that matters |
|---|---|---|
| L0 — Brahmagyan | Qualified vocabulary, sources, rules, constants, reference systems, ephemeris and calendar foundations | **Source and domain fidelity** (§14): canonical identity, source fidelity, method boundaries. |
| L1 — Gaṇita | Reproducible subject calculations under declared inputs and conventions | **Computational correctness** (§14): fact identity, values, units, precision, provenance. Downstream consumers refer to L1 facts; they do not recompute them. |
| L2 — Bodha | Whole-chart structural understanding, configurations, relationships, mechanisms, tensions and alternatives | **Concept and relationship completeness + Interpretive fidelity** (§14): contributions beyond isolated placements; shared roots visible (§3.4); complete prerequisites and exceptions. |
| L3 — Kāla | Which structures are engaged by which clocks, when, under what conditions and with which alternatives | **Temporal integrity** (§14): structure–time intersections, hierarchy, inhibiting and enabling factors, recurrence; nearest versus better-supported under a named criterion; honest "none found" semantics. |
| L4 — Phala | Qualified manifestation and earned outcome interpretation | **Interpretive fidelity + Distinctive understanding** (§14): the explicit bridge from configuration and timing to named life distinctions; no unqualified composite score. |
| L5 — Mīmāṃsā | Challenge, adjudication, scope of validity and qualified learning | **Predictive performance + Operational honesty** (§14): preserved failures, independent evidence, correct denominators, leakage-free evaluation. |

### 11.1 Preserve first, then identify the value delta

Inventory the complete useful capital: registered assets, writers, services, rules and corpus,
deterministic answer shapers, retrieval, adapters and consumer surfaces. For each component record:

- The consumer distinction and astrological concept it enables.
- Its authoritative inputs, qualified transformation, outputs and downstream consumers.
- The useful kernel to preserve: data, rules, computation, interface, identity, tests and evidence.
- Missing depth, semantic conflict, overlap, unreachable value or unnecessary duplication.
- Disposition: preserve, wrap, enrich, qualify, consolidate, replace only the inadequate part, or
  retire after dependency analysis.
- A discriminating test showing the value difference and any new error or burden.

No compromise on needed value; no rework for its own sake. Two similar assets can be complementary;
conversely, different names can hide the same computation.

### 11.2 Eliminate stranded knowledge

The discoverable path must connect **question → concept → qualified rule → canonical fact →
relationship or temporal mechanism → manifestation → delivered finding.**

Trace six evidence states: source-present; method-qualified; consumed by the intended downstream
component; traceably transformed; actually served through the intended channel; and evaluated.
Answer-shaping aggregation deserves the same scrutiny as writers — a score, ranked finding, bundle or
final synthesis can lose domain meaning even when every input was correct.

## 12. Concrete readings that define the standard

Fictional acceptance sketches. Window A/B are placeholders; no real prediction is asserted.

### 12.1 "When does my financial promise activate — and when does strain end?"

Clarify whether the question concerns receipts, retained surplus or durable relief from obligations.
Examine the qualified structural relationships, strength and condition, and varga support. Then ask
which qualified clocks engage those same participants. Window A might support nearer receipts while
carrying an unresolved retention constraint; Window B might have better structural support later. The
delivered finding contains the connected interpretation, not ten isolated favourable factors.

### 12.2 "When does my Nīcha-bhaṅga Rāja Yoga trigger?"

Check the actual formation, the cancellation condition and the further qualifications for the stronger
interpretation **before searching time**. List eligible activation routes, closest contact,
better-supported windows and opposing conditions. A participant's nearest transit contact is not
automatically the activation.

### 12.3 "You predicted a promotion. It did not happen."

Retrieve the original completed reading and its frozen claim. If it forecast a formal promotion,
later increased responsibility alone does not turn it into a hit. Investigate an input error, a missed
cancellation, an overstated manifestation bridge or a weak temporal specification. Do not repair the
record retrospectively.

### 12.4 "What would remain if we excluded this disputed method?"

Run the actual controlled comparison. Report what survives, what weakens or reverses, and what cannot
be recomputed. Show which assumption made the difference.

## 13. Boundaries that remain binding

- **No invented computation, source, detector, confidence, empirical score, or claim of exhaustive
  coverage.** Every number traces to a real calculation and every status to a detector that could have
  reported otherwise. This is the product's credibility: an instrument whose whole purpose is
  computing what a person cannot verify by hand must never emit a figure it did not compute.
- No outcome laundering into prospective generation — a result known after the fact must not re-enter
  as though it were foreseen.
- No representation of astrological association as established practical causation.
- **No cross-population hypothesis testing and no source reconstruction.** Discovery means what is
  true within a chart that was not previously visible — not discovering new astrology. Recovery of
  lost knowledge and the proposing and testing of new astrological hypotheses across populations of
  subjects are not features of this product.
- No automatic rectification, no outcome-driven personal tuning, and no autonomous decisions taken on
  the person's behalf.

## 14. Proof of the product, not merely proof of its machinery

A balanced scorecard; one high score cannot conceal failure elsewhere.

| Obligation | Required evidence |
|---|---|
| Source and domain fidelity | Correct source and context, method identity, applicability, exceptions, and genuine source-to-rule-to-application correspondence. |
| Computational correctness | Authoritative inputs, reproducible calculations, units and conventions, sensitivity, independent verification where required. |
| Concept and relationship completeness | Seeded and novel omission cases; detect a missing Bhāvat Bhāvam application, a lost cancellation, a severed chain or an unsupported generalization. |
| Interpretive fidelity | Material rivals, qualified manifestation bridge, counter-evidence, dependence accounting, and no unsupported prose added after synthesis. |
| Distinctive understanding | Correct useful distinctions against competent simpler baselines, on ordinary as well as dramatic cases, with added errors counted alongside added insight. |
| Consumer understanding | Can the person explain the important distinction, what depends on an assumption, and what would change the conclusion? |
| Temporal integrity | Correct boundaries, zones, hierarchy, horizons, nearest versus better-supported separation, and absence-versus-unavailable semantics. |
| Predictive performance | Frozen claims, valid baselines, observation coverage, discrimination and calibration without leakage or selective denominators. |
| Delivery fidelity | Complete findings survive stream, save, resume, replay, export **and both presentation modes** — the same material findings and qualifications in plain language and in the tradition's terms. No wrong-chart carryover. |
| Operational honesty | Earned statuses, recovery under failure, actual cost and reliability; no operational metric misrepresented as astrological value. |

### 14.1 Ablation testing

Test changes by ablation wherever a component claims to contribute value: remove a relationship, a
concept, a source exception or an answer-shaping component, and observe what correctly changes.

This is the only honest test that a component **earns its place**. If removing an asset changes
nothing a consumer would notice, that asset is contributing nothing — however many rows it holds. A
legitimate contribution can be small, but it must be demonstrable.

**Ablation is the per-asset scoring method for the table above.** For a single asset, its
contribution to any obligation is shown by comparing the reading with the asset against the reading
without it. The ablated reading *is* the "competent simpler baseline" of the Distinctive
understanding row, and the difference between the two — including any error or burden the asset
introduces — is the asset's score on that obligation. An asset that cannot be ablated because nothing
reads it has already answered the question.

### 14.2 The first proving set

Three reference cases the product must handle before it claims to work:

1. A **deep structural** question with no forced forecast — proving the product does not fake
   prediction to appear useful.
2. A **structure–time** question with accountable forward claims where they are earned.
3. A **historical** case, examined without retrospective repair.

## 15. Horizons beyond today's product

Valuable directions, not currently activated and not a reason to delay core build work.

- **Relational inquiry:** distinguish each individual's structure from qualified interaction,
  complementary capacities, asymmetries and the timing of a shared undertaking.
- **Entity inquiry:** distinguish an entity's own qualified foundation from its founders. Competing
  definitions of an organizational beginning remain explicit.
- **Specialized Jyotish:** deepen qualified Praśna, Muhūrta and other method-native practice from the
  existing partial services.

Promote a horizon only when its consumer value, qualified method, necessary data and evaluation route
are concrete.

## 16. How this master governs subsequent work

The sequence is:

**product definition → data-plane plan → L0–L5 layer plans → asset and interface deltas →
authorized execution → consumer-level verification.**

- **L0–L2 semantics and reachability come first** where downstream value depends on them. If a lower
  layer's field means two things, or the data cannot be reached by what needs it, everything built
  above inherits the defect.
- **Consumer-level verification is the final check** — not that the code passes or the asset built,
  but that a person can now answer a question they could not answer before.
- Every layer and asset brief states: **the P-needs (§2) it serves and the §14 obligations it is
  scored on**, the relevant Jyotish concepts, the preserved kernel, the exact delta, its authoritative
  dependencies, and its manifestation or temporal role.
- **Execute with velocity: one record, not parallel ledgers.** Reuse working data, code, contracts and
  tests; automate mechanical checks; keep one source of truth per thing. Two registries that disagree
  are worse than one that is incomplete.

**The standard:** astrological depth without invented certainty; breadth without indiscriminate
accumulation; prediction with accountability; and a person who genuinely understands more than they
did before.
