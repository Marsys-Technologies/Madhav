---
artifact: LAYER_DEFINITION_AND_STRATEGY_TEMPLATE
canonical_id: LAYER_DEFINITION_AND_STRATEGY_TEMPLATE
tier: 3
kind: template          # fixes shape; never cited as authority for content
chain: ELEVATION_DERIVATION_CHAIN_v1_0.md
produces: ["one layer instance per L0-L5"]
version: "1.1"
status: READY_FOR_USE
produced_on: 2026-09-24
decision_owner: Native
inherits:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md            # tier 1
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md   # tier 2
  - 00_ARCHITECTURE/control/asset_elevation_tracker.py             # the eight gates + brief-shape scan, as run (sole tracker; kala_brief_tracker.py is L3-only and superseded)
role: >
  The tier-3 template. One instance per layer (L0-L5) produces that layer's definition, strategy
  and evaluation ladder. Every instance must be derivable from tiers 1-2 without inventing a
  criterion, and every asset brief (tier 4) must be derivable from the instance.
independent_review: NOT YET. This template has not been reviewed by a fresh-context session. Its first
  test is the L0 instance; a defect found there is fixed here before L1-L5 are instantiated.
changelog:
  - "1.1 (2026-09-25, native-directed simplification + K3 review fold): §5.2 rewritten — 33 criteria across five tiers replaced by THREE INSTRUMENTS of which only the first certifies: (a) eight gates, each a claim with a detector that could return false; (b) brief shape, scanned for presence and producing no records; (c) inheritance and ladder position, read not scored. `Fct` folded into `Ldgr`; `Narr`/`Dens` conditional; `Dom` runs one detector from a menu rather than four. §4.4 gains the two elements K3 found missing against product §16 (preserved kernel; relevant Jyotish concepts with the domain detector each invites) — its BLOCKER 1. §5.4 gains two tests K3 found demanded-but-unenforced: the gate map must EXIST (BLOCKER 2 — a 33-row map per asset is why it was never written; an eight-row map is enforceable), and THE REVIEWER ASSIGNS THE VERDICT, NOT THE AUTHOR (K3 finding 4 — the first instance carried a verdict its own author stamped with every acceptance test pending)."
  - "1.0 (elevated in place, 2026-09-25, fourth change): §2.7 Domain correctness added — is the astrology RIGHT, as distinct from §2.4's is the obligation APPLIED. Four autonomous checks (source correspondence, cross-witness agreement, independent re-derivation, negative cases), each able to return false; NO DETECTOR is never a pass. Verified autonomously and only autonomously: no human or acharya review exists in this system, by native ruling. The per-asset checklist reaches 33 criteria. §1.5 now states the layer identity as one instance of the compositional identity that holds at plane and product level too."
  - "1.0 (elevated in place, 2026-09-25, third change): three repairs from the first instance's independent review. (a) §5.4 gains a three-verdict scale — ACCEPT / ACCEPT_WITH_CORRECTIONS / REJECT — with the distinction that makes the middle tier safe: a finding about the DOCUMENT is fixed in the document and never deferred, a finding about the LAYER that the document correctly records is a work packet, and two guards so the middle tier cannot rot (every correction names the gate it blocks; ACCEPT_WITH_CORRECTIONS becomes ACCEPT only by re-verification). (b) `measured_by:` must name the POPULATION, not only the instrument, with the corollary that a join is not measured until its keys are — three of the first instance's nine wrong figures came from exactly this gap. (c) §5.2's 32 criteria must be mapped to §4.4's inheritance list before an instance is called ready; the review found six criteria with no feeding section. Also §1.5: the synergistic fraction is recorded only where a harness exists to produce it."
  - "1.0 (elevated in place, 2026-09-25, second change): reference-layer clause in §1.2, §1.5 and §5.1 — a layer whose assets are knowledge authorities measures its individual term by fidelity, is never retirement-scored by ablation, and receives ablation only cross-layer to verify consumers. The first case where the template's definition of value had to be layer-appropriate rather than uniform; raised by the native against the L0 instance."
  - "1.0 (elevated in place, 2026-09-25): §2.6 Vocabulary conformance added, inheriting the data plane's controlled-vocabulary principle (§4.1); the per-asset checklist gains a 32nd criterion, T4 `Vocab`; the adaptation table now says L0 OWNS the vocabulary and every other layer CONFORMS. Found missing by the L0 instance and repaired here, per this template's own rule."
  - "1.0 (2026-09-24): first version. Built on the native's two reframings: (1) a layer's definition begins from the value it contributes to the customer, and every later section either traces to that value or is struck; (2) a layer is the sum of its assets and services, so its value decomposes into individual, synergistic and cross-layer terms, each measurable by ablation, and the shortfall between that sum and the objective IS the elevation delta. Carries forward the earlier design decisions: definition / strategy / evaluation kept as separate parts because they change at different rates; traceability structural via `inherits:` on every section; baseline measured by a named instrument, never inherited; certification per criterion, not per definition revision, so a scale revision costs one re-test and not a re-freeze."
---

# Layer Definition and Strategy — Template

## How to use this template

**One instance per layer.** Copy this file to `MADHAV_DATA_PLANE_L<n>_<NAME>_STRATEGY_v<x>.md`, keep
every section heading, and fill each section in the order written. The order is not cosmetic: Part 0
is the origin, and every later section is admitted only if it traces to Part 0.

**Three kinds of content, kept apart because they change at different rates.**

| part | kind | changes when |
|---|---|---|
| 0, 2 | **Definition** — inherited from tiers 1-2 | only when a parent changes |
| 1, 3, 4 | **Strategy** — measured now → target | every campaign pass |
| 5 | **Evaluation** — how the layer and its assets are scored and certified | when the scale changes, without invalidating earned work |

**Every section carries three lines before its body:**

```
inherits:   <the tier-1 / tier-2 clause this section is derived from, by § number>
measured_by: <the instrument that produced any figure here, or "none — this section is definitional">
traces_to:  <the Part 0 item this section serves; a section that cannot name one is struck>
```

The `inherits` line is what makes the instance derivable. The `measured_by` line is what stops an
inferred number being written where a measured one belongs. The `traces_to` line is the alignment test
the native set: **anything not aligned to the layer's value is extraneous.**

**`measured_by:` must name the POPULATION, not only the instrument.** "grep over the codebase" is not
an instrument; "grep over `platform/python-sidecar/**/*.py`, excluding tests, migrations and scripts,
at commit X" is. A count must say what it counted *over*: which rows, which partition, which
directory, at which revision. This is not pedantry — in the first instance of this template, three of
its nine wrong figures came from exactly this gap: a regex whose scope was never stated matched a
neighbouring block; a count over a shared table was compared against a registry figure for one
partition of it; a join was reported without checking that its right-hand key was unique. An
instrument without a population cannot be re-run, and a figure that cannot be re-run is not measured.

**Corollary — a join is not measured until its keys are.** If a join reports more rows than its
left-hand table holds, the right-hand key is not unique, and *that* is the finding.

**Two words used in exactly one sense throughout**, inherited from the product definition:
*qualified* — the method's sources, conventions, prerequisites and exceptions are on record before it is
applied; *earned* — a claim carried by a detector that could have reported otherwise.

---

## Part 0 · VALUE — the origin

Everything below derives from this part. Write it first, and write it from the customer's side of the
screen. A layer is a cog in the wheel; this part says which turn of the wheel stops without it.

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional; but every P/V cited must exist in the parent under current numbering
traces_to:   —  (this IS the origin)
```

List the P-needs and V-journeys for which this layer is **necessary** — not "involved in", not
"contributes to", but *cannot be answered without*. For each, one line: the distinction the customer
would lose if this layer did not exist.

This is ablation at layer scale. Remove the layer; what the customer loses is its value. A layer that
is necessary to nothing has no value, however much it computes.

| P / V | the distinction that disappears without this layer |
|---|---|
| | |

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (this layer's row), Data plane §3.1 (this layer's row)
measured_by: none — definitional
traces_to:   0.1
```

In one paragraph: the distinctions this layer makes **earnable** that were not earnable before it.
Name what it computes that existing software does not, and what it hands the reasoning layer to read
across. Then the owned question, the contribution handed onward, and **what it must not claim** —
inherited from the data plane's six-contributions table, not restated in new words.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement
traces_to:   0.2
```

- **Receives from:** upstream layers, by edge type, by DP contract.
- **Hands onward to:** downstream layers, by edge type, by DP contract.
- **What the join needs from it:** the computed depth this layer adds, and the fields the reasoning
  layer needs exposed to read across it.

State the three sources of the dependency graph separately. Today they disagree for several assets;
an instance that reads only one has not measured its place in the wheel.

### 0.4 · The alignment test

Every section from Part 1 onward carries `traces_to:` naming a 0.1 row or 0.2/0.3 item. The author
runs the test on their own draft before review: a section, a contract, an asset, a work packet that
cannot name what it serves is **struck, not kept for completeness.** The reviewer runs it again.

---

## Part 1 · VALUE DECOMPOSITION — the layer is the sum of its assets and services

A layer's value is realised only through its assets and services, jointly. This part measures how.
Its output is an accounting: three terms whose sum is compared against 0.2, and the shortfall is the
elevation delta. Nothing in this part is inherited; all of it is measured.

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: asset_registry (live, read-only) · the registry seed · the migration-governed pin · asset_throughput · the production probe (asset_elevation_tracker.py --layer <L> --env-file)
traces_to:   0.3
```

Every asset and service the layer owns: registered, writer-backed, service (no table by design),
residual, shared, historical. For each: target table(s) — a **set**, not one pointer, for multi-table
assets — row counts in production, columns, contract fields live, last build, and whether current code
on any live head differs from what is deployed.

Three sources are reconciled, not one read: registry vs seed vs pin. Where they disagree, say so; the
disagreement is itself a finding.

### 1.2 · Individual contribution — ablate one

```
inherits:    Product §14.1 (ablation), Data plane §12.2
measured_by: ablation of the single asset against the layer's served reading; where no served path exists, state "unmeasurable — not reached" and cite the six-state position from 1.4
traces_to:   0.1 (which rows this asset serves)
```

For each asset and service: the reading with it against the reading without it, scored against the
product's ten obligations. The ablated reading *is* the "competent simpler baseline". Record the
difference including any error or burden the asset introduces.

An asset that cannot be ablated because nothing reads it has already answered the question for this
term. Do not invent a contribution; record ≈ 0 and let 1.5 decide.

**Reference-layer clause.** Where the layer is a knowledge authority — its assets are the tradition,
not products of a chart (L0) — the individual term is **fidelity**, not contribution: identity
correct, source present and qualified, method boundary stated, provenance carried. Ablation is not
the measure, because an unread piece of authentic knowledge is not worth zero. Record fidelity per
asset here; ablation for such a layer appears only in 1.4, aimed at consumers.

### 1.3 · Synergistic contribution — ablate the group

```
inherits:    Data plane §3.4 (presentation contract), §7 (DP contracts), the layer's synergy binding if one exists
measured_by: ablation of the shared contracts / vocabulary / ordering against the layer's served reading, holding individual assets in place
traces_to:   0.2
```

What exists only when assets are combined: shared field vocabulary, cross-asset contracts, the
ordering that lets one asset's output be another's input, the interplay a consumer reads as one
reading rather than several. Measure it as the difference between the layer's value and the sum of
1.2 — the part no single asset accounts for.

**This term is the department test.** A layer whose synergistic term is near zero is several assets
that happen to share a prefix. The L3 audit measured exactly that. The elevation target for a layer
is to make this term large; record its current size honestly.

### 1.4 · Cross-layer handoff — what it produces for downstream

```
inherits:    Data plane §11 (six evidence states), §7 (DP contracts this layer PRODUCES)
measured_by: for each produced contract, its position on source-present → qualified → consumed → traceably transformed → served → value evaluated, verified at the consumer
traces_to:   0.3 (hands onward)
```

An asset can contribute nothing to this layer's own served value and be essential because a downstream
layer reads it. This term is what stops a pure producer scoring zero and looking retirable. For each
DP contract the layer produces: which downstream consumer, which fields, which evidence state it has
actually reached — verified at the consumer, not asserted by the producer.

### 1.5 · The accounting

```
inherits:    —
measured_by: 1.2 + 1.3 + 1.4 against 0.2
traces_to:   0.2
```

> **layer value = Σ individual + Σ synergistic + Σ cross-layer handoff**

This is the layer-level instance of the identity in product §1.3, which holds at every level:
`plane = Σ layers + Σ synergies`, `product = Σ planes + Σ synergies`. The synergy term is what makes
a level a thing rather than a collection, and it is the term this layer's elevation must grow.

- Compare the sum against the objective in 0.2. **The shortfall is the elevation delta**; Part 3
  itemises it.
- Any asset ≈ 0 on all three terms is a candidate for disposition **R** or **H** in Part 3 — a
  candidate, not a verdict; "lack of a caller in a bounded search is not redundancy." **This rule does
  not apply to a reference layer:** there, an asset is retired only for failed fidelity (inauthentic,
  unsourced, wrongly identified, superseded by a corrected authority), never for lack of a reader.
- Any asset with a large individual term and no synergistic term is a candidate for **I** (integrate).
- Record the synergistic term as a fraction of the total **only where an ablation harness exists to
  produce it**. Where none does, record the seam-by-seam measurement as the value and say the harness
  is a packet. Do not invent a fraction to fill the field.

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

These are not governance and not compliance. They are the conditions without which the figures in
Part 1 are not trustworthy — a wrong number does not reduce the value, it destroys it. Each traces to
Part 0 on those terms.

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (this layer's row), §13; Data plane §9.2 (the switch and the storage separation)
measured_by: a detector per rule, named here, that can report the rule violated
traces_to:   0.2 — the value is real only if these hold
```

The product's per-layer "what must not happen" row, verbatim. The life-event switch: what this layer
may do when ON, what it emits when OFF, and the storage separation that makes OFF a selection rather
than a rebuild. The prohibition on invented computation, source, detector, confidence or score. **For
each rule, the detector.** A rule with no detector is a wish.

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (the field → contract mapping)
measured_by: presentation-parity test (Data plane §12.2): both renderings from the consumed reading package, no recomputation, identical finding / confidence / uncertainty
traces_to:   0.1 — the acharya rows are unservable if these fields are not carried
```

Which §3.4 fields **this layer** must retain and hand onward so the acharya rendering is derivable
from the same computation: method and school, prerequisites tested and exceptions checked, conventions
in force, intermediate quantities, dignity/strength components separately, competing readings with
their authorities, and — for temporal layers — clock geometry, activation rule, the named criterion,
the bridge or falsifier. A layer that collapses these has made the audience commitment underivable.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1 (common envelope)
measured_by: for each contract, the fields and grain actually present in the producer's table and actually read by the consumer — verified both ends
traces_to:   0.3
```

Two tables: DP contracts this layer **produces** (consumer, fields, grain, identity, generation) and
DP contracts it **consumes** (producer, fields, declared use). Every consumed input declares its use
— calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation,
evaluation. **A citation with no declared use is not a contract.**

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5 (domain obligations)
measured_by: per obligation: applied / inapplicable-with-reason / unavailable / unqualified / unresolved — the five states, never a blank
traces_to:   0.1
```

Which of the product's coverage obligations this layer owns, with prerequisites, variants, exceptions,
negative cases and uncertainty. Each ends in one of the five states. A tool name, an empty result or a
populated confidence field is not "applied".

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (the controlled vocabulary — six rules with detectors)
measured_by: alias-set coverage per entity class the layer touches · independent-map census per class · interface-parameter census (enum / resolver-validated / free) · presence of a parity test for every code-side snapshot the layer relies on
traces_to:   0.2 — the value is real only if the layer speaks the plane's one language
```

Which of the sixteen entity classes this layer emits or accepts; for each, whether every name resolves
through the controlled set, whether an unlisted name is raised, how many independent maps the layer's
code carries (permitted: one), and whether each Python/TypeScript snapshot it depends on is generated
from the authority, pinned by release id and digest, and joined to it by a parity test.

**For L0 the section inverts:** L0 does not conform to the vocabulary; it **owns** it. Its 2.6 states
the authority, its releases, the classes covered, the classes not yet covered, and the detectors
that stand between the authority and every consumer.

### 2.7 · Domain correctness — is the astrology right?

```
inherits:    Product §14 (Domain correctness), §3 (the twelve coverage obligations); Data plane §5
measured_by: the four autonomous checks below, each named per obligation this layer owns
traces_to:   0.1 — a layer whose astrology is wrong serves no P-need, however well it is engineered
```

§2.4 asks whether a coverage obligation is **applied**. This section asks whether it is **right**.
They are different questions and a layer can pass the first while failing the second: a catalogue can
carry perfect provenance, unique identifiers, complete alias sets and a detector on every claim, and
still encode the configuration wrongly. Nothing else in this template would catch it.

**Verified autonomously, and only autonomously.** No human, acharya or expert review is part of this
system. The check is these four detectors or it does not exist:

| # | check | what it compares | fails when |
|---|---|---|---|
| a | **source correspondence** | the encoded rule against the passage it cites — including prerequisites, exceptions and cancellations, not only the headline claim | the encoding says more, less or other than its own cited source |
| b | **cross-witness agreement** | two admitted sources defining the same configuration | the encodings disagree and the disagreement is not recorded as school disagreement |
| c | **independent re-derivation** | a classical quantity computed a second way, from different inputs | the two results differ beyond a declared tolerance |
| d | **negative cases** | seeded counterexamples the tradition says do NOT satisfy the rule | the rule fires on one |

For each obligation the layer owns (§2.4), state which of a–d applies, the detector, and its current
result — `PASS` / `FAIL` / `PARTIAL` / **`NO DETECTOR`**. `NO DETECTOR` is never a pass; it is a gap.

**A reference layer is where this matters most.** L0 holds the tradition itself, so an error here
propagates into every reading built on it and is invisible at every later layer — each of which will
faithfully compute the wrong thing.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: topological sort of the reconciled depends_on from 0.3; cycle check; cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision
traces_to:   0.3
```

Intra-layer build order, cross-layer gates, and the edge type of every edge. State the frozen
definition revision the gate was evaluated against; a freeze under a superseded revision does not
carry.

---

## Part 3 · THE DELTA

```
inherits:    —
measured_by: 1.5's shortfall, itemised
traces_to:   0.2
```

### 3.1 · Per obligation

For each of the product's ten proof obligations this layer is scored on (0.2 / product §11): where
the layer stands today, measured, and what closes the gap.

### 3.2 · Per asset — disposition

For every asset and service in 1.1, one of the data plane's eight dispositions, with the evidence from
Part 1 that justifies it:

**P** preserve · **I** integrate · **E** enrich/correct · **Q** qualify/limit authority ·
**C** consolidation candidate · **H** historical/restricted · **R** retire after migration ·
**U** unresolved use

No quota for keeping or removing. Smallest sufficient change. A whole asset can be preserved while one
score, fallback or narration rule is replaced.

### 3.3 · Per asset — what it must add

The contract fields (2.3), presentation fields (2.2) and coverage states (2.4) each asset must add to
close its share of the delta. This is the list an asset brief's "exact delta" section inherits.

### 3.4 · Intra-layer interplay

The input/output/use matrix between the layer's own assets — which reads which, on which fields —
and the boundary with adjacent layers. This is where the synergistic term (1.3) is either built or
found missing.

---

## Part 4 · STRATEGY

### 4.1 · Order

```
inherits:    2.5
measured_by: the DAG; the three-way baseline per asset (deployed / current code / target)
traces_to:   0.2
```

The sequence assets are elevated in: upstream before downstream within the layer, cross-layer gates
honoured, and — within a depth level, where no dependency constrains — chosen for learning value, not
alphabet. State the three-way baseline per asset: **deployed** (production schema and rows), **current
code** (newest on any live head, including unmerged), **target** (the brief). The delta is target −
current code; the *risk* is current code − deployed, and they are different numbers.

### 4.2 · Work packets

```
inherits:    Data plane §13.1, §13.3 item 8
measured_by: each packet's proof — a detector that fails when the packet has not landed
traces_to:   3.x — every packet closes a named delta item
```

Bounded packets with dependencies, proof, consumer cutover and the decisions that remain open. A
packet that closes no delta item is struck.

### 4.3 · Generation, invalidation, rollback

```
inherits:    Data plane §11, §4.4, DP16
measured_by: the generation pins each consumer records; the invalidation path exercised, not described
traces_to:   2.1 — a rebuild that resets chronology is a hindsight leak
```

### 4.4 · What each asset brief inherits

```
inherits:    Product §16 (what every brief states); Data plane §13.3 (asset brief sentence)
measured_by: derivability — a brief author must be able to fill these from this instance alone
traces_to:   0.1
```

The fixed content every tier-4 brief for this layer receives from this instance, so that briefs are
derived rather than written from scratch:

- the P-needs and V-journeys the asset serves (from 0.1, narrowed)
- the ten obligations it is scored on (from 0.2)
- its correctness rules and switch behaviour (2.1)
- its presentation fields (2.2)
- its contracts produced and consumed, with declared use (2.3)
- its coverage obligations and their current states (2.4)
- its position in the order and its three-way baseline (4.1)
- its disposition and its "must add" list (3.2, 3.3)
- its individual / synergistic / cross-layer contribution, measured (1.2-1.4)
- its manifestation or temporal role
- **the preserved kernel** — what of the asset must survive any rebuild unchanged (from 3.2)
- **the relevant Jyotish concepts** the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)

A brief that has to invent any of these has found a defect in this instance, not in the brief.

---

## Part 5 · EVALUATION AND CERTIFICATION

### 5.1 · The score is ablation, in three flavours

```
inherits:    Product §14, §14.1; Data plane §12.2
measured_by: ablation deltas
traces_to:   0.2
```

| flavour | what is removed | what is measured |
|---|---|---|
| individual | one asset | its contribution to each of the ten obligations |
| synergistic | a shared contract, vocabulary or ordering | what only the combination provided |
| cross-layer | this layer's produced contract, at the consumer | what downstream loses |

For a reference layer the individual flavour is replaced by a fidelity score, and only the
cross-layer flavour runs — to verify consumers, never to judge the asset (see 1.2).

The ten obligations are the product's, not the layer's: source and domain fidelity · computational
correctness · concept and relationship completeness · interpretive fidelity · distinctive
understanding · consumer understanding · temporal integrity · predictive performance · delivery
fidelity · operational honesty. A layer scores on the subset its 0.2 row names.

### 5.2 · What is certified, and what is merely checked

```
inherits:    Product §14; CLAUDE.md §N.6-N.8; the t3 lesson (certification is expensive to re-earn)
measured_by: the certification ledger (asset_certs.jsonl) for gates; the tracker's marker scan for shape
traces_to:   4.4 — the gates are what an asset brief is certified against
```

Three instruments, not one. Only the first produces certification records.

**(a) The gates — certified, per asset.** Six always, plus at most two that apply conditionally.
Each is a claim with a detector that could return false; a gate without one is `NO DETECTOR`, which
is an honest null, never a pass.

| gate | the claim | conditional on |
|---|---|---|
| **Ldgr** · derivation ledger | every derived value names the upstream `fact_id` it reads, and those ids resolve | — |
| **Idem** · idempotency | a rebuild replaces its own rows; it never accretes (§N.3) | — |
| **Earn** · earned signal | every status/grade/PASS the asset emits has a detector measuring that specific claim (§N.8) | — |
| **Null** · honest null | where a value cannot be derived, the asset emits null — not a plausible default (§N.7 item 6) | — |
| **Vocab** · vocabulary conformance | one canonical id per thing, one closed alias set, no free-text synonym | — |
| **Dom** · domain correctness | what the asset asserts about Jyotish is checked by **one** applicable detector below | — |
| **Narr** · narration fidelity | prose restates cited facts and does not re-derive them (§N.7) | the asset emits prose |
| **Dens** · serving density | confirmed and catalog-only rows are counted separately; the dense layer survives a trim (§N.6) | the asset reaches a served surface |

`Ldgr` absorbs the former facts/interpretation gate: a ledger entry naming its upstream ids **is**
the separation test, and the separate gate had no detector of its own.

**The domain menu.** Name the one detector that fits what the asset actually asserts, and run it.
Running four where one applies is theatre; running none is an unearned signal.

| | applies when | the check |
|---|---|---|
| D1 · source correspondence | the asset restates a cited classical source | the restatement against the source text |
| D2 · cross-witness agreement | two independent authorities cover the same claim | they agree; where they don't, the disagreement is recorded, not averaged |
| D3 · independent re-derivation | the value is computable a second way | compute it that way and compare |
| D4 · seeded negative case | the asset classifies or fires | feed a case that must not fire; check it doesn't |

**(b) Brief shape — checked once, not certified.** The §4.4 inheritance list fixes what an asset
brief contains. A brief either carries those sections or it is not yet a brief. The tracker reports
this as one boolean per brief, by marker scan. It produces no certification records, because a
present section is not a verified claim.

**(c) Inheritance and ladder position — read, not scored.** That an asset brief descends from this
instance, and this instance from the data plane and the product, is a property of **this instance**,
declared once in §4.4 — not re-litigated per asset. Ladder positions (data-plane and campaign) are
status fields read from the registry and the campaign events table; a status is not a verdict.

**The gate map — fixed here, not re-derived per instance.** The gates are fixed by this template and
the sections are fixed by this template, so the map between them is template content and is written
once, below. An instance does not invent it; an instance **fills the right-hand column** and reports
any row it cannot fill.

| gate | the section a brief author reads to answer it | what the instance must supply there |
|---|---|---|
| **Ldgr** | §2.3 contracts produced and consumed, with declared use | the asset's upstream `fact_id` sources, named |
| **Idem** | §2.5 edges and order; §4.1 order and baseline | the asset's natural key, so "replaces its own rows" is decidable |
| **Earn** | §2.4 coverage obligations and their states | which of the asset's emitted states are claims, and what would falsify each |
| **Null** | §2.4 (the state vocabulary); §1.4 evidence states | the asset's own convention for an underivable value |
| **Vocab** | §2.6 vocabulary conformance | the classes this asset owns or consumes, and the authority for each |
| **Dom** | §2.7 domain correctness; §4.4's Jyotish-concepts row | the concepts the asset asserts, and which menu item each invites |
| **Narr** | §2.2 presentation fields | whether the asset emits prose, and which fields carry it |
| **Dens** | §2.2 presentation fields; §3.4 the served boundary | whether the asset reaches a served surface, and which |

A row an instance cannot fill is a hole in **that instance**, not a gap in the brief — the brief
author would have to invent it. Report unfillable rows in §7 as corrections with gates.

*(This table answers K3 finding 2. Its earlier form demanded a 33-row map of every instance, which
is why no instance ever wrote one; the map is template-fixed content and had holes by construction.)*

### 5.3 · Certification is per criterion, not per definition revision

```
inherits:    the t3 lesson — 90 assets' freezes evaporated when the campaign definition re-froze
             asset_certs.jsonl's `_schema` line — the as-run record shape, which this section follows
             (measured 2026-09-25 over nirmana_elevation_campaign_events, event_type='asset_frozen':
              98 assets ever frozen, 8 frozen under t3, 90 not; 103 events under superseded revisions.
              Assets and events are different populations — 90 is assets.)
measured_by: the certification record itself
traces_to:   —  (this is the property that lets the scale improve without destroying earned work)
```

Each certification is one record, in the shape the ledger that stores it actually uses
(`00_ARCHITECTURE/control/asset_certs.jsonl`, whose `_schema` line is the authority — this template
previously specified the record WITHOUT `detector` and without a closed verdict set, i.e. worse than
its own storage layer; K3 finding 8):

```
asset · criterion · criterion_version · detector · evidence (path, query or run id) · verdict ·
verified_by · verified_on

verdict ∈ { PASS | FAIL | PARTIAL | NO_DETECTOR | N/A }     — closed set, these spellings exactly
```

A revised criterion invalidates **only** the records for that criterion, across affected assets; it
never re-opens the rest. An asset is *elevated* when every criterion its layer requires has a current
record with a passing verdict. A definition revision that changes no criterion changes nothing.

### 5.4 · Acceptance of the instance itself

Before an instance is called ready:

1. **Derivability test.** A fresh-context reader attempts to derive one asset brief from the instance
   plus tiers 1-2, and reports every place they had to invent something. Zero inventions, or the
   instance is revised.
2. **Alignment test.** Every section names its `traces_to:`; a reviewer strikes any that cannot.
3. **Measured, not inherited.** Every figure names its `measured_by:`; a reviewer rejects any that
   cannot be re-run.
4. **Presentation parity** holds for the layer's served surface.
5. **The gate map exists.** §5.2's eight-row map from gate to feeding section is written out in the
   instance. An instance missing the map fails this test outright — the map is the derivability test
   in tabular form, and demanding it without checking for it is how it goes unwritten.
6. **Independent review**, fresh context, findings folded, before the instance is cited by anything
   below it. **The reviewer assigns the verdict, not the author** — an instance carrying a verdict its
   own author stamped is unreviewed, whatever the verdict says, and nothing may inherit from it.
   Three verdicts:

| verdict | meaning | may the tier below inherit from it? |
|---|---|---|
| **ACCEPT** | derivable with zero inventions; every re-run figure reproduced; no parent contradiction; no correction outstanding | yes |
| **ACCEPT_WITH_CORRECTIONS** | the direction and the method are sound; named corrections remain, **each bound to the gate it must close before** | yes, and the corrections are tracked as blocking that named gate |
| **REJECT** | the direction or the method is wrong; the instance is reworked before anything inherits from it | no |

**The distinction that makes the middle tier safe — a finding is about the DOCUMENT or about the
LAYER, and they are not the same thing:**

- A finding **about the document** — a figure that does not reproduce, a section that contradicts a
  parent, an inheritance a brief author cannot follow — is a defect *in the instance*. It is fixed in
  the document. It is never deferred to implementation, because a wrong number does not become right
  by being built on.
- A finding **about the layer** that the document *correctly records* — a duplicate identifier, a
  missing alias set, an unlinked rule corpus — is not a defect in the instance at all. It is the
  instance doing its job. It becomes a work packet with a detector, and it is fixed during
  implementation.

An instance is ACCEPT_WITH_CORRECTIONS when its document-level findings are closed and its
layer-level findings are packets. An instance with open document-level findings is REJECT, however
sound its direction.

**Two guards, because a middle tier is where things rot:**

1. **A correction with no named gate is not a correction.** Every correction names the gate it blocks
   — the next instance, the first asset brief, the first build, the layer's certification. A
   correction recorded without one defaults to blocking the *next* gate, never to none.
2. **ACCEPT_WITH_CORRECTIONS does not decay into ACCEPT.** It becomes ACCEPT only by re-verifying
   each correction closed, recorded per §5.3. It never becomes ACCEPT by the passage of time or by
   assertion that the corrections were handled.

---

## Adapting the template per layer

What changes per layer is the *content* of Parts 0-4, never the headings, never the three lines per
section, never the accounting in 1.5, never the checklist in 5.2. Specifically:

| layer | what is distinctive to fill |
|---|---|
| L0 Brahmagyan | 0.1 is mostly *indirect* — L0 is necessary to everything and directly served to little; 1.4 (cross-layer handoff) dominates; 2.1's "private observations must not become global doctrine"; **2.6 inverts: L0 owns the controlled vocabulary, every other layer conforms to it** |
| L1 Gaṇita | computational correctness dominates 5.1; "downstream consumers refer to L1 facts, they do not recompute them" is the load-bearing 2.3 rule; L1 holds judged structure too — "layer ownership is not epistemic type" |
| L2 Bodha | shared roots visible (several assets from one placement are not independent confirmations); 1.3 is where whole-chart reading lives or fails |
| L3 Kāla | temporal integrity; nearest-versus-better-supported under a named criterion; honest "none found"; the switch rule that the observed event never chooses the trigger; 2.2's temporal row |
| L4 Phala | the manifestation bridge and its falsifier; no unqualified composite score; earned outcome interpretation |
| L5 Mīmāṃsā | learning's defined output (a visible change to a claim family, with reasons); leakage-free evaluation; correct denominators |

**First instance: L0.** Not because it is first, but because a template defect is cheapest to find
there and most expensive to inherit. A defect found while instantiating L0 is fixed *here*, then L1-L5
are instantiated from the corrected template.
