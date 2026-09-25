---
artifact: ASSET_ELEVATION_TEMPLATE
canonical_id: ASSET_ELEVATION_TEMPLATE
version: "1.0"
status: READY_FOR_USE
produced_on: 2026-09-25
decision_owner: Native
tier: 4
kind: template          # fixes shape; never cited as authority for content
chain: ELEVATION_DERIVATION_CHAIN_v1_0.md
produces: ["one asset instance per asset or service — 129 across L0-L5"]
inherits:                                                                           # what THIS TEMPLATE inherits
  - 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md   # tier 3 template — §4.4 is the hook §0.1 receives
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md    # tier 2
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md                              # tier 1
instance_inherits:                                                                  # what EACH ASSET INSTANCE inherits — FOUR, not three
  - this template                                     # shape
  - "the layer instance of ITS OWN layer"             # content: P-needs narrowed, obligations, correctness rules, contracts, scoring mode, disposition
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md
role: >
  The tier-4 template. One instance per asset or service. It does not re-derive anything the layer
  instance already settled; it inherits, measures the asset, registers every gap as an executable
  item with a detector, and ends in a per-criterion certification record. An asset is ELEVATED when
  every criterion its layer requires carries a current passing record — never by assertion.
independent_review: NOT YET. First test is one L0 instance; defects found there are fixed HERE.
changelog:
  - "1.0 (elevated in place, 2026-09-25, native-directed): 33rd criterion added — T4 `Dom`, domain correctness: is the astrology right, as distinct from well-sourced. Four autonomous detectors from product §14; NO DETECTOR on `Dom` blocks certification outright. Recorded explicitly: no human or acharya review exists in this system, so a check that cannot be automated does not exist rather than waiting for a person. An earlier draft of this dimension proposed a human verifier and was wrong on a decision the native had already taken."
  - "1.0 (2026-09-25): first version, derived from the L0 layer instance rather than invented. Three refinements the native's framing required and this template adopts: (1) BRIEF COMPLETENESS and ASSET CONFORMANCE are two different measurements and only the second certifies — a brief that mentions idempotency is not an asset that is idempotent; (2) the 32 criteria are evaluated against the ASSET, with a named detector per criterion, not by marker-detection over the brief's prose; (3) the layer-appropriate clause carries down — a reference-layer asset is scored on fidelity and is never retired for lack of a reader. Gap register and certification ledger are the two machine-read surfaces the tracker consumes."
---

# Asset elevation — template (tier 4)

One instance per asset or service. **Nothing here is re-derived from tiers 1–3.** If a section cannot
be filled from the layer instance, that is a defect in the layer instance and is raised there.

**Four inputs, not three.** This template fixes the *shape*. Each asset instance takes its *content*
from **the layer instance of its own layer** — the P-needs narrowed to that layer, the obligations it
is scored on, its correctness rules, its contracts, its scoring mode and this asset's disposition —
on top of the data plane and the product definition. The layer instance is what makes an asset brief
specific rather than generic; without it the brief would re-derive the layer, which is the invention
the chain exists to prevent. The hook is **layer instance §4.4 → this template §0.1**, written to
match row for row.

## Three things this template insists on, and why

**1 · Brief completeness and asset conformance are different, and only the second certifies.**
A brief that *mentions* idempotency is not an asset that *is* idempotent. §2 records what the brief
covers (cheap, marker-level, useful for spotting holes). §4 records what the asset actually satisfies,
each with a detector that could return false. **Certification (§6) reads §4 only.** This is the
§N.8 earned-signal rule applied to the elevation ladder itself.

**2 · Every gap is an executable item, not a note.** §5's register gives each gap an id, a detector,
an owner and the gate it blocks. A gap without a detector is a wish; a gap without a gate defaults to
blocking this asset's certification.

**3 · The layer's own rules carry down.** A reference-layer asset (L0) is scored on **fidelity** and is
**never retired for lack of a reader**. A chart-product asset (L1–L5) is scored on contribution, and
ablation is its measure. The instance states which it is in §0 and the rest follows.

---

## §0 · Identity and inheritance

```
asset_id:        <bg_x | ga_x | bo_x | ka_x | ph_x | mi_x>
layer:           <L0 Brahmagyan | … | L5 Mīmāṃsā>
layer_instance:  <path to the tier-3 document, with its version and commit>
kind:            data | service | multi-table | rider (producer_covered) | static
scoring_mode:    fidelity (reference layer)  |  contribution (chart-product layer)
measured_on:     <date>
measured_against: <registry | seed | pin | production | code at commit | evidence ledger>
```

### 0.1 · Inherited, not re-derived

Copied verbatim from the layer instance's §4.4 list. Each line names its source section. **A line you
cannot fill is a defect in the layer instance — raise it there and stop; do not invent it here.**

| what | value | from |
|---|---|---|
| P-needs and V-journeys this asset serves | | layer §0.1, narrowed |
| Proof obligations it is scored on | | layer §0.2 |
| Correctness rules that bind it | | layer §2.1 |
| Presentation fields it must carry | | layer §2.2 |
| Contracts it produces / consumes, with declared use | | layer §2.3 |
| Coverage obligations it owns, and their state | | layer §2.4 |
| Position in the build order; upstream and downstream | | layer §2.5, §4.1 |
| Disposition (P/I/E/Q/C/H/R/U) and must-add list | | layer §3.2, §3.3 |
| Measured contribution or fidelity | | layer §1.2–1.4 |
| Manifestation or temporal role | | layer §4.4 |

### 0.2 · What this asset is for, in one paragraph

Its own job, in the layer's terms, written so a reader who knows the product but not this asset can
say why removing it would cost something. If that paragraph cannot be written, the disposition is
already in question and §5 should say so.

---

## §1 · Measured current state

```
measured_by: <one instrument per figure, each naming its POPULATION — which rows, which partition, which directory, at which revision>
```

Every figure names its instrument **and what it counted over**. A count without a population cannot
be re-run, and a figure that cannot be re-run is not measured. A join is not measured until its keys
are: if it returns more rows than its left side holds, the right key is not unique and that is a
finding.

- **Storage:** table(s) — a *set*, not one pointer; rows (exact, or `~` for an estimate with the
  estimator named); columns; the registry's `target_table`, `count_sql` and whether it is truthful.
- **Producer:** writer module and `@register` id, or the asset it rides on, or "static / migration-
  seeded", or "service".
- **Consumers, declared vs actual:** registered `depends_on` edges in; code that actually reads it,
  writer-side and serving-side, with the grep population stated. **The gap between the two is a
  finding, not a footnote.**
- **Served surface:** which capabilities expose it; whether each declares a `density_contract`.
- **Three-way baseline:** deployed (production structure — never the migration ledger, which has been
  measured to disagree with production) · current code (newest on any live head, including unmerged) ·
  target (this brief). The delta is target − current code; the **risk** is current code − deployed.
- **Evidence-state position:** source-present → qualified → consumed → traceably transformed → served
  → value-evaluated, verified *at the consumer*, not asserted by the producer.

---

## §2 · Brief completeness — does this brief address the 32?

```
measured_by: marker scan over this document
```

A tick means this brief *addresses* the criterion. It is not evidence about the asset and it does not
certify anything. It exists to catch holes in the brief before review.

**T1 · Ten analysis lenses** — A identity · B inputs/DAG · C correctness · D data sufficiency ·
E consumers · F AI/product · G efficiency · H reliability · I change packet · J final evidence

**T2 · Six elevation lenses** — value extraction · target-state design · efficiency with quality ·
synergy obligations · consumer walkthrough · knowledge-time discipline

**T3 · Strategy alignment** — Product Definition · data-plane VA · layer strategy · synergy binding ·
upstream/downstream · serving contract

**T4 · Discipline gates** — facts/interpretation · derivation ledger · idempotency · earned signal ·
narration fidelity · serving density · honest null · vocabulary conformance · **domain correctness**

**T5 · Two ladders** — data-plane ladder position · campaign ladder position

---

## §3 · The asset's own obligations, stated

The subset of the product's ten proof obligations this asset is scored on (from §0.1), each with what
"satisfied" means *for this asset specifically*. An obligation inherited but not specialised here is
an obligation nobody can test.

| obligation | what satisfied means for this asset | detector |
|---|---|---|

---

## §4 · Asset conformance — the evaluation matrix

**This is the section certification reads.** Each of the 32 criteria is evaluated against the asset,
not against this brief. Every row carries a detector that could return false; where none exists, the
verdict is **NO DETECTOR** — which is a gap (§5), never a pass.

| # | criterion | what it means for this asset | detector (query, test, or script) | verdict | evidence |
|---|---|---|---|---|---|
| A | identity | | | PASS / FAIL / PARTIAL / NO DETECTOR / N-A | |
| … | | | | | |

**Verdict vocabulary, used strictly:**

- **PASS** — the detector ran and returned the passing result.
- **FAIL** — the detector ran and returned failing.
- **PARTIAL** — the detector ran; the criterion holds for a named subset and not the rest. The subset
  is stated, not implied.
- **NO DETECTOR** — nothing exists that could distinguish pass from fail. **Never recorded as PASS.**
- **N/A** — the criterion does not apply to this asset kind, *with the reason*. A bare N/A is a gap.

**Domain correctness (`Dom`) is the criterion this template exists to stop anyone skipping.** It asks
whether the astrology this asset carries is *right*, not whether it is well-sourced, well-identified
or well-served. Its detector is one or more of the four autonomous checks in product §14 — source
correspondence against the cited passage; cross-witness agreement or a recorded school disagreement;
independent re-derivation from different inputs; seeded negative cases that must not fire. **No human
or acharya review exists in this system.** An asset with `NO DETECTOR` on `Dom` is not certifiable,
however many of the other 32 it passes: a component can be structurally immaculate and astrologically
wrong, and nothing else here would notice.

**Scoring-mode clause.** Where `scoring_mode: fidelity`, criteria that measure contribution
(consumers, efficiency, value extraction) are evaluated as *reachability and correctness of handoff*,
and a low reading is never grounds for disposition **R**. Retirement in a reference layer happens only
for failed fidelity — inauthentic, unsourced, wrongly identified, or superseded by a corrected
authority.

---

## §5 · Gap register — every gap is executable

Each FAIL, PARTIAL and NO DETECTOR in §4, plus every must-add inherited from the layer's §3.3.

| gap id | criterion | what is wrong | the change | detector that closes it | owner | gate it blocks | state |
|---|---|---|---|---|---|---|---|
| `<asset>-G01` | | | | | | this asset's certification / a named layer packet / a downstream gate | OPEN / IN PROGRESS / CLOSED |

**Rules.** A gap with no detector is not registered — it is written as a question and raised. A gap
with no gate defaults to blocking **this asset's certification**, never to blocking nothing. A gap
closed is closed by its detector passing, recorded in §6 — not by assertion that the work was done.

---

## §6 · Change packet

```
may_touch:      <exact globs>
must_not_touch: <exact globs, with the reason each is fenced>
base:           <commit>
```

- **Preserved kernel** — the data, rules, computation, interface, identity, tests and evidence that
  survive unchanged. Named explicitly, because the disposition vocabulary's default is preserve.
- **Exact delta** — what changes, field by field.
- **Migration** — if one is needed: the number chosen by scanning **every** `origin/*` head across
  **both** `platform/migrations/` and `platform/supabase/migrations/`, confirmed at execution and not
  trusted from any document including this one. Never edit an applied migration. Verify it *actually*
  applied by checking production structure, not the runner's report.
- **Idempotency** — the layer's convention, stated: L0 upsert; L1+ per-chart delete-then-insert scoped
  to `(chart_id × natural key)`.
- **Rollback** — what undoes it, and what cannot be undone.
- **Consumer impact** — who reads this asset today (§1), what each sees change, and whether any
  consumer must change with it.

---

## §7 · Certification records

One record per criterion. **This is the ledger, and it is the only thing that makes an asset
elevated.**

```
asset · criterion · criterion_version · detector · evidence (path, query or run id) · verdict · verified_by · verified_on
```

- A revised criterion invalidates **only** its own records, across affected assets. It never re-opens
  the rest. This is what lets the scale improve without wiping earned work — the failure that cost 73
  freezes when a campaign definition was re-frozen.
- **An asset is ELEVATED when every criterion its layer requires carries a current record with a
  passing verdict, and every gap in §5 is CLOSED.** Not before, and not by anyone's summary.
- `verified_by` is never the party that made the change. A builder does not certify their own build.

---

## §8 · Review

Verdict is one of three, inherited from the layer template's §5.4:

| verdict | meaning |
|---|---|
| **ACCEPT** | derivable from the layer instance with zero inventions; every measured figure reproduced; no gap left unregistered |
| **ACCEPT_WITH_CORRECTIONS** | direction and method sound; named corrections remain, **each bound to the gate it blocks**; execution may proceed |
| **REJECT** | a measurement does not reproduce, an inheritance cannot be followed, or a gap is recorded without a detector |

**The distinction that keeps the middle tier honest:** a finding about *this brief* — a figure that
does not reproduce, an inheritance that cannot be followed — is fixed in the brief and never deferred.
A finding about *the asset* that the brief correctly records is not a brief defect at all; it is a
gap in §5 with a detector, fixed during execution.

Reviewer is fresh-context, read-only, and not the author. One independent review discharges the gate
(native ruling, 2026-09-25).

---

## Filling order

§0 (inherit) → §1 (measure) → §4 (evaluate) → §5 (register gaps) → §3 (specialise obligations) →
§6 (change packet) → §2 (completeness check, last, as a self-check before review) → §8 (review) →
§7 (certify, after execution).

§7 is written **after** execution, never with it. A certification record created alongside the change
it certifies is the builder certifying their own build.
