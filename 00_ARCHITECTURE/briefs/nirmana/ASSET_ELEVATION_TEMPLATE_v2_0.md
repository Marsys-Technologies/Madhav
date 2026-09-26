---
artifact: ASSET_ELEVATION_TEMPLATE
canonical_id: ASSET_ELEVATION_TEMPLATE
version: "2.0"
status: DRAFT_PENDING_REVIEW
produced_on: 2026-09-26
decision_owner: Native
tier: 4
kind: template          # fixes shape; never cited as authority for content
chain: ELEVATION_DERIVATION_CHAIN_v1_0.md
produces: ["one asset instance per registered asset or service — 129 across L0-L5; 40 in L0"]
inherits:                                                                            # what THIS TEMPLATE inherits — all three SEALED 2026-09-25
  - 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md    # tier 3, FINAL — §4.4 is the hook §0.1 receives; §5.2 the eight gates; §5.3 the record shape
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md     # tier 2, FINAL — §13.3 asset-brief sentence; §4.1 vocabulary; §12.2 tests
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md                               # tier 1, FINAL — §16 what every brief states; §14 obligations
instance_inherits:                                                                   # what EACH ASSET INSTANCE inherits — four, not three
  - this template                                     # shape
  - "the layer instance of ITS OWN layer"             # content — the thirteen §0.1 rows come from the layer instance §4.4, row for row
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md
supersedes: "ASSET_ELEVATION_TEMPLATE_v1_0.md (v1.1) — rebuilt fresh against the sealed parents by native instruction (2026-09-26), not edited in place. v1.1's sound content is carried; what was stale against the seal is corrected: gate `Dom` becomes `Carr` (ruling 11); the §0.1 inheritance table matches the sealed layer template's thirteen rows (v1.1 had ten); the gap register is declared as the delta ledger the tracker already reads; signature follows ruling 9."
machine_read_surfaces:
  gap_register: 00_ARCHITECTURE/control/asset_gaps.jsonl     # §5 — THE DELTA LEDGER. Its _schema line is the field authority.
  certification: 00_ARCHITECTURE/control/asset_certs.jsonl   # §7 — the only thing that makes an asset ELEVATED
  tracker: 00_ARCHITECTURE/control/asset_elevation_tracker.py
role: >
  The tier-4 template. One instance per asset or service. It re-derives nothing the layer instance
  settled; it inherits, measures the asset, registers every gap as an executable ledger row with a
  detector, and ends in per-criterion certification records. An asset is ELEVATED when every gate its
  layer requires carries a current passing record and its gap rows are closed — never by assertion.
independent_review: NOT YET — native review before the pilot (native instruction 2026-09-26). The pilot on five L0 assets is its first practical test; a defect found there is fixed HERE.
changelog:
  - "2.0 (2026-09-26, third change — native ruling, decision 17): NINTH GATE `Build` — buildability. Can the orchestrator dispatch this asset, and does a triggered rebuild produce the correct result? Six static checks (registered · contract · dispatchable target · DAG resolvable · count/integrity · completion honesty) plus one runtime state proved by `ctx.dry_run` and, when authorized, a real rebuild. The gate set is 9 per asset, template-wide: 9 x 129 = 1,161 across L0-L5, not an L0 measure. THE BOUNDARY RULE, which the native asked be decided here: the gate asks DOES IT WORK; §9 asks COULD IT WORK BETTER. A passing gate writes a certification record and NO ledger row — rows come only from FAIL / PARTIAL / NO_DETECTOR. Making a working rebuild faster, cheaper or incremental is a §9 opportunity under the build-cost column and never blocks certification. One boundary case sits on the gate side: a rebuild that works only after a manual step is a Build gap, because `seamlessly when triggered` is part of the claim. A buildability gap is fixed in the ASSET or the REGISTRY, never in the orchestrator — the freeze is why any of this is checkable. Requires the tier-3 reopen of layer template §5.2 (decision 17)."
  - "2.0 (2026-09-26, second change — native review folded, same day): (h) §9 OPPORTUNITY REGISTER added — the 'beyond' half of the delta: algorithm/architecture (three outcome columns: output, inputs, BUILD COST), concept completeness (width and depth against a DECLARED universe), retrieval reachability (fields and rows exposed, requirement [TRANSFERS] to the retrieval plane), and synergy (joint value neither asset carries alone; shared roots are not confirmations). One admission rule: no measurement-after, no entry. Opportunities NEVER block certification. (i) §1 gains three measured items: build-cost baseline ('not instrumented' is a legal value), completeness census, reachability census. (j) §4 Vocab row names which of the six §4.1 rules apply to the asset. (k) §5 is the DELTA LEDGER, both kinds: asset_gaps.jsonl gains `kind: gap | opportunity`; the four states are reused with CLOSED meaning 'proven by its measurement' for either kind; the tracker filters on kind and prints conforms (gaps) and could-be-better (opportunities) separately. Ledger schema lines and tracker aligned in the same commit."
  - "2.0 (2026-09-26): rebuilt from the sealed tiers 1-3. (a) RULING 11 — gate `Dom` (is the astrology right) becomes `Carr` (source carriage and reproduction): the three mechanical checks stay, the seeded negative case leaves with the verdict framing, and the sentence that made `Dom` a certification blocker is replaced by the carriage framing. (b) §0.1 now carries the sealed layer template's thirteen inherited items row for row — v1.1 had ten; missing were the preserved kernel, the Jyotish concepts with the carriage check each invites, and the individual/synergistic/cross-layer terms as three rows. (c) THE DELTA LEDGER: §5's gap register IS `asset_gaps.jsonl`, whose `_schema` line fixes the fields; a brief's delta section is those rows rendered, never retyped, and `what` carries `measured … / required …` so the delta is a re-run, not a claim. (d) Every section carries the layer template's three lines (inherits / measured_by / traces_to). (e) PILOT clause — a brief derived from a layer instance that is not yet ACCEPTED may register gaps and may not certify. (f) RULING 9 — §8 verdict may be signed by reviewer, native or session once a review has happened; §7's verified_by records who ran the detector, and the independence that matters is the detector's. (g) Change packet gains the frozen orchestrator contract conformance lines (§N.2/§N.3). Three alignment items outside this document are listed at the end, not done silently."
---

# Asset elevation — template (tier 4, v2.0)

One instance per asset or service. **Nothing here is re-derived from tiers 1–3.** If a section cannot be
filled from the layer instance, that is a defect in the layer instance and is raised there.

**Every section carries three lines**, as the layer template does — `inherits:` (which parent clause),
`measured_by:` (the instrument *and the population*, or "none — definitional"), `traces_to:` (which
layer-instance item this serves; a section that cannot name one is struck).

**Three things this template insists on:**

1. **Brief completeness and asset conformance are different, and only the second certifies.** A brief that
   *mentions* idempotency is not an asset that *is* idempotent. §2 checks the brief's shape and produces
   no record; §4 evaluates the asset with a detector per gate; §7 reads §4 only.
2. **Every gap is a ledger row, not a note.** §5 is the asset's rows of the delta ledger. A gap without a
   detector is a question, not a gap.
3. **The layer's scoring mode carries down.** A reference-layer asset is scored on **fidelity** and is never
   retired for lack of a reader; a chart-product asset is scored on **contribution** by ablation. §0 states
   which, and the rest follows.

---

## §0 · Identity and inheritance

```
inherits:    layer instance §4.4 (the thirteen inherited items); Data plane §13.3 (the asset-brief sentence); Product §16
measured_by: none — definitional; every row is copied, with its source section named
traces_to:   layer §0.1 (the P/V rows this asset serves)
```

```
asset_id:         <bg_x | ga_x | bo_x | ka_x | ph_x | mi_x>
layer:            <L0 Brahmagyan | … | L5 Mīmāṃsā>
layer_instance:   <path, version, status, commit>
pilot:            <yes | no>   # yes if the layer instance is not yet ACCEPTED — see the pilot clause
kind:             data | service (no table by design) | multi-table | rider (producer_covered) | static (migration-seeded)
scoring_mode:     fidelity (reference layer) | contribution (chart-product layer)
role:             manifestation | temporal | neither (supplies what both rest on)   # from layer §4.4
measured_on:      <date>
measured_against: <registry · seed · production · code at commit · evidence ledger>
```

**Pilot clause.** A brief derived from a layer instance that is not yet ACCEPTED is a **pilot**: it
exists to test derivability (layer §5.4 test 1). It may register gaps in §5; it **may not** write
certification records in §7. When the instance is accepted, the pilot is re-verified against it and
the flag is removed.

### 0.1 · Inherited, not re-derived — thirteen rows, from the layer instance §4.4

| # | what | value | from |
|---|---|---|---|
| 1 | P-needs and V-journeys this asset serves | | layer §0.1, narrowed |
| 2 | the obligations it is scored on — the layer's subset of the product's ten (**ten, not eleven**: domain correctness is discharged above the plane, ruling 11) | | layer §0.2 |
| 3 | correctness rules and switch behaviour | | layer §2.1 |
| 4 | presentation fields it must carry | | layer §2.2 |
| 5 | contracts produced and consumed, with declared use | | layer §2.3 |
| 6 | coverage obligations it owns, and their current state | | layer §2.4 |
| 7 | position in the order, and its three-way baseline | | layer §2.5, §4.1 |
| 8 | disposition (P/I/E/Q/C/H/R/U) and must-add list | | layer §3.2, §3.3 |
| 9 | individual term — fidelity or contribution, measured | | layer §1.2 |
| 10 | synergistic term — which seam it sits on, measured | | layer §1.3 |
| 11 | cross-layer term — which produced contract, at which evidence state | | layer §1.4 |
| 12 | **the preserved kernel** — what must survive any rebuild unchanged | | layer §3.2 |
| 13 | **the Jyotish concepts it touches**, named, each with the carriage check it invites (a/b/c) | | layer §2.7, §4.4 |

**A row you cannot fill is a defect in the layer instance — raise it there and stop; do not invent it
here.** Row 13 is the one v1.1 lacked and the one a carriage gate cannot run without.

### 0.2 · What this asset is for

One paragraph, in the layer's terms, written so a reader who knows the product but not this asset can
say why removing it would cost something — or, for a reference-layer asset, what it holds that nothing
else holds. If the paragraph cannot be written, the disposition is in question and §5 says so.

---

## §1 · Measured current state

```
inherits:    layer §1.1 (inventory rules), §4.1 (three-way baseline)
measured_by: one instrument per figure, each naming its POPULATION — which rows, which partition, which directory, at which revision
traces_to:   layer §0.3
```

A count without a population cannot be re-run, and a figure that cannot be re-run is not measured. A
join is not measured until its keys are: more rows than the left side holds means the right key is not
unique, and *that* is the finding.

- **Storage:** table(s) — a *set*, not one pointer; rows by the asset's **own `count_sql`** (the cockpit
  instrument), floor, delta; columns; whether `count_sql` and `target_table` are truthful.
- **Producer:** writer module and `@register` id · or the asset it rides on · or "static, migration N" ·
  or "service".
- **Consumers, declared vs actual:** `depends_on` edges in; code that actually reads it, writer-side and
  serving-side, grep population stated. **The gap between the two is a finding, not a footnote** — the
  registry has been measured to understate consumption.
- **Served surface:** which capability modules expose it; whether each declares a `density_contract`.
- **Three-way baseline:** deployed (production structure — never the migration ledger) · current code
  (newest on any live head, including unmerged) · target (this brief). **Delta = target − current code;
  risk = current code − deployed.** Different numbers; state both.
- **Evidence-state position:** source-present → qualified → consumed → traceably transformed → served →
  value-evaluated — verified *at the consumer*, never asserted by the producer.
- **Build-cost baseline:** last build duration, rows per second, compute cost where known, and rebuild
  scope (global once vs per chart — a per-chart cost is multiplied by the number of charts). From the
  orchestrator's run records. **"not instrumented" is a legal value** and is honest; where it is the
  value, the instrument is the first efficiency opportunity (§9).

### 1.1 · Concept completeness — width and depth

```
inherits:    Data plane §5 (completeness = applied / inapplicable / unavailable / unqualified / unresolved, never a blank)
measured_by: a census against a DECLARED universe — width = instances present ÷ instances the source or ontology declares; depth = dimensions populated ÷ dimensions declared, per dimension
traces_to:   layer §2.4
```

Not the same question as density. Density (`Dens`) is about *serving* — confirmed rows kept apart from
catalog-only rows. Completeness is about *build* — is the concept the asset stands on covered.

- **Declare the universe first**, from a source or from the ontology: how many instances the concept has
  (27 nakshatras; the vargas a text names; the yogas a catalogue defines) and which dimensions each
  instance should carry (per yoga: definition, participants, cancellation, grade, source, school variant).
  A universe assumed rather than declared is the first gap.
- **Measure** width and depth as fractions against it.
- **Everything missing ends in one of the five states.** A shortfall against a declared universe is a
  §5 gap of kind `gap` — its detector is this census.

### 1.2 · Retrieval reachability — everything built, reachable

```
inherits:    Data plane DP10 (capability discovery: fields, access path, scope; question→data AND field→consumer), DP12 (complete delivery); §1's [TRANSFERS] convention
measured_by: exposure census over the capability modules that serve this asset — fields exposed ÷ fields built; rows reachable through declared filters and pagination ÷ rows built
traces_to:   layer §1.4 (the served state), §0.1 (the rows this asset serves)
```

That an asset is served says nothing about whether its twelfth column or its rare rows can be reached.
Two fractions, measured now against the capability modules that exist. **The requirement — that all of
the width and depth be reachable — is a [TRANSFERS] obligation on the retrieval plane**, which is not yet
built: the asset is measured against it today and cannot be blocked by it today. A shortfall is recorded
in §9 as a reachability opportunity, not in §5 as a gap, until that plane has an artefact of its own.

---

## §2 · Brief shape — one check, no records

```
inherits:    layer §5.2 (b) — brief shape, scanned for presence
measured_by: marker scan over this document (asset_elevation_tracker.py SHAPE — the ten markers below, verbatim)
traces_to:   —  (a self-check; it serves no value row and certifies nothing)
```

identity · inputs/DAG · correctness · data sufficiency · consumers · value/target · synergy ·
knowledge-time · change packet · evidence

A present section is not a verified claim about the asset. Inheritance is the layer instance's property,
declared once in its §4.4; ladder positions are registry status fields. Neither is scored here.

---

## §3 · The asset's own obligations, specialised

```
inherits:    §0.1 row 2; Product §14 rows
measured_by: none until §4 — this section says what "satisfied" MEANS for this asset; §4 measures it
traces_to:   layer §3.1
```

| obligation | what satisfied means for this asset specifically | detector (named here, run in §4) |
|---|---|---|

An obligation inherited but not specialised is an obligation nobody can test.

---

## §4 · Asset conformance — the eight gates

```
inherits:    layer §5.2 (a) — the eight gates; CLAUDE.md §N.3, §N.6-§N.8
measured_by: one detector per gate, evaluated against the ASSET, each able to return false
traces_to:   layer §3.1 and §3.3 — the gates are what the delta is measured against
```

**This is the only section certification reads.** Where no detector exists the verdict is
`NO_DETECTOR` — a gap, never a pass.

| gate | applies | the claim | detector | verdict | evidence |
|---|---|---|---|---|---|
| **Ldgr** derivation ledger | always | every derived value names the upstream `fact_id` it reads, and those ids resolve; for a reference layer, every row names its *source* | | | |
| **Idem** idempotency | always | a rebuild replaces its own rows, never accretes (§N.3 — L0 upsert; L1+ delete-then-insert on chart × natural key) | | | |
| **Earn** earned signal | always | every status, grade or PASS the asset emits has a detector measuring that specific claim (§N.8) | | | |
| **Null** honest null | always | an underivable value is emitted as null, not as a plausible default (§N.7 item 6) | | | |
| **Vocab** vocabulary conformance | always | one canonical id per thing, one closed alias set, every name resolved through the set, no local map — **stating which of §4.1's six rules apply to this asset**: 1–3 for any data asset; 4 if it ships a code-side snapshot; 5 if it exposes an interface parameter; 6 if its code carries a local name→id map | | | |
| **Carr** source carriage and reproduction | always | what the asset restates from a source matches that source; what it computes reproduces a second way; a witness disagreement is carried, not settled — **one** applicable check from §4.1, run | | | |
| **Narr** narration fidelity | if it emits prose | prose restates cited facts and never re-derives them (§N.7) | | | |
| **Dens** serving density | if it reaches a served surface | confirmed and catalog-only rows counted separately; the dense layer survives a trim (§N.6) | | | |
| **Build** buildability | always | the orchestrator can dispatch this asset and a triggered rebuild produces the correct result — the six checks of §4.2 | | | |

**Verdict vocabulary, closed set, these spellings exactly** (they are the tracker's and the ledger's):
`PASS` · `FAIL` · `PARTIAL` (holds for a *named* subset) · `NO_DETECTOR` (never recorded as PASS) ·
`N/A` (the gate does not apply to this asset kind, *with the reason* — a bare N/A is a gap).

A conditional gate that does not apply is disposed of with an explicit `N/A` and one line of reason. It is
never silently dropped.

### 4.2 · Buildability — the six checks, and what is NOT a gap

```
inherits:    CLAUDE.md §N.2 (the FROZEN orchestrator contract), §N.3 (idempotency per layer), §N.8 (a status needs a detector that could read false); ORCHESTRATOR_CONVERGENCE_CLOSE §2
measured_by: six static checks over the writer, the registry and the build record — all read-only; plus the runtime state below
traces_to:   0.1 — an asset that cannot be rebuilt serves no P-need, whatever it holds today
```

An asset's content is worth nothing if the orchestrator cannot rebuild it on demand. All six checks run
read-only, and all six can return false:

| # | check | asserts |
|---|---|---|
| 1 | **registered** | exactly one `@register('<asset_id>')`, and the id matches the registry **exactly** — both quote styles searched, because an ad-hoc grep that misses one is not a detector |
| 2 | **contract** | a `WriterBase` subclass; `run(ctx)` **XOR** `plan_substeps` + `run_substep`; never commits or closes `ctx.db_conn`; never writes `asset_throughput`; takes `chart_id` / `birth_params` from `ctx.config` |
| 3 | **dispatchable target** | a `target_table` set, **or** service / multi-table declared explicitly, so the orchestrator's clear and count steps have something to aim at |
| 4 | **DAG resolvable** | every `depends_on` entry exists in the registry; no cycle; every dependency is itself buildable; and the declared edges match what the asset actually reads |
| 5 | **count and integrity** | `count_sql` present, correctly scoped, and `integrity_check_sql` present — each able to fail |
| 6 | **completion honesty** | the build record agrees with the live count. `rows_written = 0` against a populated table is a status with no measurement behind it, and for a service it is indistinguishable from a writer that produced nothing |

**Runtime state, recorded and never assumed:** `never_rebuilt` · `dry_run_ok` · `rebuilt_ok` ·
`rebuild_failed`. `ctx.dry_run` is part of the frozen contract, so **dispatchability can be proved end to
end with no production write** — that is the cheap proof and it is always available. A real rebuild proof
needs authorization and is a different state. **`state = 'lit'` is never itself the proof** (§N.8 records
the promotion predicate that asserted completion while only checking row presence).

**What is a gap and what is an opportunity — the line, decided by native ruling:**

- **Gap (blocks certification):** the orchestrator cannot dispatch it · the contract is violated · the DAG
  is wrong · a rebuild produces the wrong result or accretes · the build record asserts a completion that
  did not happen · **or the rebuild works only after a manual step** — "seamlessly when triggered" is part
  of the claim.
- **Opportunity (§9, never blocks):** the rebuild works correctly and could be **faster, cheaper,
  incremental rather than full, or smaller in blast radius.** That belongs in §9's build-cost column.
- **A passing `Build` gate produces a certification record and no ledger row at all.** Ledger rows come
  only from FAIL / PARTIAL / NO_DETECTOR and inherited must-adds.

**Fixes go in the asset or the registry — never in the orchestrator.** The contract is frozen, and it is
the reason every check above is decidable at all. If an asset appears to need the contract changed, stop
and raise it (§6).

### 4.1 · The carriage menu — pick one, run it

```
inherits:    layer §2.7; Data plane §12.2 (Source carriage and reproduction)
measured_by: the chosen check, run
traces_to:   §0.1 row 13
```

`Carr` asks whether the asset **transmitted faithfully** — not whether the astrology is right. That
verdict is formed above the data plane (native ruling 11) and no gate here reaches it.

| | applies when | the check | fails when |
|---|---|---|---|
| **D1** source correspondence | the asset restates a cited classical source | the restatement against the passage — prerequisites, exceptions and cancellations included | the encoding says more, less or other than its own source |
| **D2** witness carriage | two admitted authorities cover the same claim | the disagreement is carried forward as school disagreement | it is averaged, silently resolved or dropped |
| **D3** independent re-derivation | the value is computable a second way | compute it that way and compare | the results differ beyond a declared tolerance |

*A fourth check — seeding a case the tradition says must NOT fire — was on v1.1's menu and is removed:
deciding what must not fire is a doctrinal act, placed above the data plane by ruling 11.*

Name the one that fits. Running three where one applies is theatre; running none is an unearned signal.
Where none applies, the record is `NO_DETECTOR` with the reason.

**Scoring-mode clause.** Where `scoring_mode: fidelity`, contribution-flavoured readings are evaluated as
reachability and correctness of handoff, and a low reading is **never** grounds for disposition **R**.
Retirement in a reference layer happens only for failed fidelity — inauthentic, unsourced, wrongly
identified, or superseded by a corrected authority.

---

## §5 · The delta ledger — this asset's rows, both kinds

```
inherits:    layer §3.3 (must-add), §4.2 (packets); the ledger's own _schema line
measured_by: the ledger — 00_ARCHITECTURE/control/asset_gaps.jsonl — rendered, never retyped
traces_to:   layer §3.x — every row closes a named delta item
```

**The delta is a ledger, not a document, and it has two halves in one file.** One row per (asset,
criterion). This section is those rows for this asset, in the ledger's own fields:

`asset · gap_id · kind · criterion · what · change · detector · owner · gate · state · ts`

- **`kind: gap`** — the shortfall against a requirement. Blocks certification.
- **`kind: opportunity`** — the beyond (§9). **Never blocks certification**; `gate` is `NONE` and the row
  names the layer packet it feeds. The tracker filters on `kind` and prints the two counts separately:
  *conforms* (gaps) and *could be better* (opportunities). One file, because two registries that must
  agree are worse than one that is incomplete.

- `what` is written as **`measured: <figure, instrument, population> / required: <the gate's claim>`** —
  so the gap is a re-run, not an assertion. The delta is whatever the measurement reports against a
  fixed requirement; it is recomputed, never remembered.
- `gate` is what the gap blocks: this asset's certification (the default), a named layer packet, or a
  downstream gate. Never nothing.
- `state ∈ OPEN · IN_PROGRESS · CLOSED · WITHDRAWN`, the same four words for both kinds. For a gap,
  **CLOSED means the detector passed**, recorded in §7. For an opportunity, OPEN = proposed,
  IN_PROGRESS = accepted and being built, **CLOSED = realised and proven by its measurement**,
  WITHDRAWN = rejected. Never closed by assertion, either kind.
- Two kinds of row, and **detector gaps close before data gaps**: you cannot measure a data gap (53
  placeholder citations) without its detector (source correspondence). Layer-scope rows — the ones no
  single asset owns — carry the layer's id and are settled by the layer packet, not by any brief.

A gap with no detector is not registered; it is written as a question and raised against the layer
instance.

---

## §6 · Change packet

```
inherits:    Data plane §13.1, §13.3 item 8; CLAUDE.md §N.2 (frozen orchestrator), §N.3 (idempotency), §N.4 (migrations)
measured_by: each packet's proof — a detector that fails when the packet has not landed
traces_to:   §5 — a packet that closes no ledger row is struck
```

```
may_touch:      <exact globs>
must_not_touch: <exact globs, each with the reason it is fenced>
base:           <commit>
```

- **Preserved kernel** (from §0.1 row 12) — named explicitly; the disposition vocabulary's default is
  preserve, so what survives is stated before what changes.
- **Exact delta** — field by field, with the **expected semantic difference** a consumer will observe.
- **Writer conformance** — a `@register('<asset_id>')` `WriterBase` subclass; `run(ctx)` or
  `plan_substeps` + `run_substep`; runs on `ctx.db_conn` and **never commits or closes it**; never writes
  `asset_throughput`; takes `chart_id` and `birth_params` from `ctx.config`. If the change seems to need
  the contract changed, **stop and raise** — the freeze is deliberate.
- **Idempotency** — the layer's convention: L0 `ON CONFLICT` upsert; L1+ delete-then-insert scoped to
  `(chart_id × natural key)`.
- **Migration** — if one is needed: number = max+1 scanned across **every** `origin/*` head and **both**
  migration directories at execution time, trusted from no document including this one; never edit an
  applied migration; verify it applied by production structure, never by the runner's report.
- **Rollback** — what undoes it, and what cannot be undone.
- **Consumer impact** — who reads the asset today (§1), what each sees change, which must change with it.
- **Decisions still open** — named, with who owns each.

---

## §7 · Certification records

```
inherits:    layer §5.3; the ledger's own _schema line
measured_by: the ledger — 00_ARCHITECTURE/control/asset_certs.jsonl — one record per criterion
traces_to:   —  (the property that lets the scale improve without destroying earned work)
```

`asset · criterion · criterion_version · detector · evidence (path, query or run id) · verdict · verified_by · verified_on`
— verdict from the closed set in §4, these spellings exactly.

- A revised criterion invalidates **only its own records** across affected assets; the rest stand. This
  is what stops a scale revision from evaporating a layer's earned work, as one re-freeze once cost 90
  assets.
- **An asset is ELEVATED when every gate its layer requires carries a current PASS or N/A record and every
  §5 row is CLOSED.** The tracker computes it; nobody's summary does.
- `verified_by` records who ran the detector. **The independence that matters is the detector's** — it
  must be able to fail — not the runner's identity (native ruling 9; one operator runs this system).
  A record without a run id or query is not a record.
- §7 is written **after** execution, never alongside it.

---

## §8 · Review and signature

```
inherits:    layer §5.4; native ruling 9
measured_by: the six acceptance tests of layer §5.4, applied to this brief
traces_to:   —
```

| verdict | meaning |
|---|---|
| **ACCEPT** | derivable from the layer instance with zero inventions; every figure reproduced; no gap unregistered |
| **ACCEPT_WITH_CORRECTIONS** | direction and method sound; named corrections remain, **each bound to the gate it blocks**; execution may proceed |
| **REJECT** | a figure does not reproduce, an inheritance cannot be followed, or a gap is recorded without a detector |

A finding about **this brief** is fixed in the brief and never deferred. A finding about **the asset**
that the brief correctly records is a §5 row with a detector, fixed in execution. A brief with open
brief-level findings is REJECT however sound its direction.

**Signature (ruling 9):** the reviewer, the native or the session may sign, once a review has happened.
A verdict with no review behind it, or signed with acceptance tests pending, is void — and a **pilot**
brief carries no verdict at all until its layer instance is accepted.

---

## §9 · Opportunity register — the beyond half of the delta

```
inherits:    Product §1.2 (the unit of value is an earned distinction), §14.1 (ablation proves a contribution), §14 operational honesty (actual cost); Data plane §10.1 dispositions E/I/C, §11 (cost at the meaningful join)
measured_by: for every entry, the measurement that would prove it afterward — ablation of the new version against the old, plus the cost delta; an entry with no measurement-after is not admitted
traces_to:   layer §3 and §4 — accepted opportunities flow UP into the layer instance as candidate packets
```

Every asset is an algorithm: inputs → outputs, and the output's distinction is its value. Conformance
(§4) asks whether it does that correctly. This section asks whether it does it **the best way** — the
same value or more, for less, or a value it does not deliver today. Four dimensions, one admission rule.

**Admission rule.** An entry is recorded only with: the distinction it would add or the cost it would
remove · the evidence today · the expected delta · cost and risk · **the measurement that proves it
afterward**. No measurement, no entry. Opportunities never block certification: an asset can be ELEVATED
(conforms) and still have open opportunities (could be better), and those are two different words.

| dimension | the question | what the entry states | proof afterward |
|---|---|---|---|
| **Algorithm and architecture** | Is this the most productive way to deliver this value — more or fewer inputs, a different algorithm, a different architecture? | inputs today → algorithm → outputs today; the alternative; and **three outcome columns**: output delta (same / better / elevated), input delta (more / fewer / different), **build-cost delta** (time, compute, and for per-chart assets cost × charts) | **two measurements, not one**: output parity or improvement (the new version's reading against the old — ablation with two variants) **and** the cost delta against the §1 baseline. Faster-but-different is a change to evaluate, not an efficiency win. |
| **Concept completeness** | Is the concept covered in width and depth (§1.1)? | the declared universe; the width and depth fractions; which missing instances or dimensions are worth adding and for which P-need | the census re-run; the added instance or dimension reached by a consumer |
| **Retrieval reachability** | Can everything the asset built be reached (§1.2)? | the two exposure fractions; which fields or rows are unreachable and which P-need would reach them | the census re-run against the capability modules; marked **[TRANSFERS]** — the requirement belongs to the retrieval plane |
| **Synergy** | Could this asset deliver a bigger distinction jointly with another, in its layer or beyond? | the candidate pairing; the seam that would join them (shared key, contract field); the distinction neither carries alone | ablation: both together against each alone. **Guardrail:** several assets derived from one placement are not independent confirmations — a pairing that restates one root is double counting, not synergy. |

**Bounds on the first dimension, so the search stays honest:** the orchestrator contract is frozen — an
asset may change its algorithm freely inside `WriterBase` and may not change how it is driven; a proposal
that needs the contract changed is a native decision, not an asset opportunity. Deterministic-first — a
kernel swapped for a generative model is not an optimisation. For a reference-layer asset, "better
algorithm" usually means better extraction and qualification of the source, not faster computation.

**Where entries go:** §5, as rows of kind `opportunity`, with `gate: NONE` and the layer packet they feed.
Accepted entries are how the layer instance's Part 3 grows its "beyond" half.

---

## Filling order

§0 (inherit) → §1 (measure, including §1.1 and §1.2) → §4 (evaluate) → §5 (register gap rows) →
§9 (opportunities, once the measured picture exists) → §3 (specialise obligations) → §6 (change packet)
→ §2 (shape self-check, last before review) → §8 (review) → §7 (certify, after execution, never with it).

---

## Adapting per layer

What changes per layer is the *content*, never the headings, the three lines, the eight gates or the
ledger fields.

| layer | what is distinctive |
|---|---|
| L0 Brahmagyan | `scoring_mode: fidelity`; `Ldgr` reads as source-presence; **`Vocab` inverts — the asset *is* part of the set, so the gate tests uniqueness and alias completeness of what it owns**; `Carr` D1 dominates; never R for lack of a reader; **`Build`**: rebuild is a global re-seed with `ON CONFLICT` upsert, no chart involved, so blast radius is the whole reference table and the dry-run proof is cheap |
| L1 Gaṇita | contribution; `Idem` is delete-then-insert on chart × natural key; the load-bearing rule is "consumers refer to L1 facts, they do not recompute them"; `Carr` D3 dominates; **`Build`**: rebuild is per chart, so check 6 (completion honesty) is per `(asset, chart_id)` and a rebuild's blast radius is one chart — the opportunity side is usually incremental-versus-full |
| L2 Bodha | shared roots visible — several signals from one placement are not independent confirmations; `Ldgr` must resolve to `chart_facts.fact_id` |
| L3 Kāla | the switch rule that the observed event never chooses the trigger; nearest-vs-better-supported under a named criterion; honest "none found" |
| L4 Phala | no self-calibration; a forecast is emitted only when earned; the bridge or its falsifier is a carried field |
| L5 Mīmāṃsā | the firewall — admitted outcomes never enter provider synthesis; a rebuild never re-stamps emission time |

---

## Alignment outside this document — done in the same commit as this fold

Three surfaces carried v1.1's vocabulary and moved with this template, so the three never disagree:

1. `asset_elevation_tracker.py` — `GATES` key `Dom` → `Carr`; the menu is D1–D3 (D4 removed with its
   reason); lifecycle filters ledger rows on `kind` so an open opportunity never withholds ELEVATED; the
   layer line prints *gaps open* and *opportunities open* separately; the L0 entry points at the v3.0
   instance (DRAFT — briefs derived from it are pilots by §0's clause).
2. `asset_certs.jsonl` `_schema` line — `verified_by` restated per ruling 9: it records who ran the
   detector, and the independence that matters is the detector's.
3. `asset_gaps.jsonl` `_schema` line — gains `kind: gap | opportunity`, the `what` convention
   (`measured … / required …`), and the meaning of the four states per kind.
