---
artifact: ELEVATION_DERIVATION_CHAIN
canonical_id: ELEVATION_DERIVATION_CHAIN
version: "1.0"
status: CURRENT
tier: 0
produced_on: 2026-09-25
decision_owner: Native
role: >
  The map of the elevation document system: what derives from what, which documents are templates and
  which are instances, and what each instance must inherit rather than invent. It is the index for the
  chain, not a member of it — it governs no content and settles no astrology.
produces: [LAYER_DEFINITION_AND_STRATEGY_TEMPLATE, ASSET_ELEVATION_TEMPLATE]
changelog:
  - "1.0 (2026-09-25): written at the native's direction to log the process after the chain was built. Records one correction found while writing it: an ASSET INSTANCE inherits from FOUR sources, not three — the asset template supplies its shape, and its own layer's instance supplies its content, alongside the data plane and the product definition. The asset template declared only three, naming the layer TEMPLATE where it should also name the layer INSTANCE."
---

# The elevation derivation chain

## The shape, in one picture

```
                    TEMPLATES                              INSTANCES
                  (shape: how)                          (content: what)

  tier 1                                    ┌──  MADHAV_PRODUCT_DEFINITION_FINAL
                                            │      what the product is for
  tier 2                                    ├──  MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL
                                            │      how the six layers hand work to each other
                                            │
  tier 3   LAYER_DEFINITION_AND_STRATEGY ───┼──▶ six layer instances, one per L0…L5
             _TEMPLATE                      │      L0 = MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY
                                            │
  tier 4   ASSET_ELEVATION_TEMPLATE ────────┴──▶ 129 asset instances, one per asset or service
                                                   + the layer instance of ITS OWN layer
```

**The rule that makes it a chain and not a pile:** an instance **inherits, and does not re-derive**.
Anything it cannot fill from its parents is a defect in a parent, raised there — never invented in
the child.

## What each thing inherits

| document | kind | tier | inherits from | produces |
|---|---|---|---|---|
| `MADHAV_PRODUCT_DEFINITION_FINAL` | instance | 1 | — (the root) | the data plane |
| `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL` | instance | 2 | product | the layer template + six layer instances |
| `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE` | **template** | 3 | product, data plane | six layer instances |
| a layer instance (e.g. L0 Brahmagyan) | instance | 3 | **layer template** (shape) + data plane + product | its own assets' instances |
| `ASSET_ELEVATION_TEMPLATE` | **template** | 4 | layer template, data plane, product | 129 asset instances |
| an asset instance (e.g. `bg_ontology`) | instance | 4 | **asset template** (shape) + **its own layer's instance** (content) + data plane + product | the executed change, and its certification |

**The fourth input at tier 4, stated plainly because it was the thing missing.** A layer instance has
three inputs: the layer template for shape, the data plane and the product for content. An **asset
instance has four**: the asset template for shape, and *its own layer's instance* for content, on top
of the data plane and the product. The layer instance is the input that makes an asset brief specific
— it carries the P-needs narrowed to that layer, the obligations that layer is scored on, that layer's
correctness rules, its contracts, its scoring mode, and the per-asset disposition. Without it an asset
brief would have to re-derive the layer, which is exactly the invention the chain exists to prevent.

The hook is concrete: **layer instance §4.4** lists what an asset brief takes, and **asset template
§0.1** is the table that receives it. They are written to match, row for row.

## Templates versus instances

A **template** is never filled in and never cited as authority for content. It fixes the shape: which
sections exist, what each must contain, what the acceptance test is. It is elevated in place when an
instance finds it wanting — the L0 instance found ten such defects and they were repaired in the
template, not worked around in the instance.

An **instance** is filled in, carries measured figures, and is reviewed independently before anything
below it inherits from it.

## The rules that travel down the whole chain

1. **Inherit, do not re-derive.** A section that cannot be filled from a parent is a defect in the
   parent.
2. **`measured_by:` names the population, not only the instrument.** A count says what it counted
   over — which rows, which partition, which directory, at which revision. A figure that cannot be
   re-run is not measured. A join is not measured until its keys are.
3. **`traces_to:` or it is struck.** Everything traces to the value at the top of its own document.
4. **A signal needs a detector that could return false.** NO DETECTOR is a verdict and is never a pass.
5. **Scoring mode carries down.** A reference layer (L0) scores on fidelity and never retires an asset
   for lack of a reader; chart-product layers score on contribution, measured by ablation.
6. **Three verdicts.** ACCEPT / ACCEPT_WITH_CORRECTIONS / REJECT. A finding about the *document* is
   fixed in the document; a finding about the *thing it describes*, correctly recorded, is a gap with
   a detector. One independent review discharges the gate (native ruling, 2026-09-25).
7. **Certification is per criterion, never per revision.** A revised criterion re-opens only its own
   records. This is what lets the scale improve without wiping earned work.

## Current state of the chain

| tier | document | status |
|---|---|---|
| 1 | product definition | **FINAL**, reviewed ACCEPT, registered |
| 2 | data plane | **FINAL**, reviewed REJECT→folded, registered |
| 3 | layer template | READY_FOR_USE — not independently reviewed; repaired ten times by its first instance |
| 3 | L0 Brahmagyan instance | **ACCEPT_WITH_CORRECTIONS**, six corrections with gates |
| 3 | L1–L5 instances | not written — the native ruled L0 is wrapped before L1 begins |
| 4 | asset template | READY_FOR_USE — not independently reviewed, no instance yet |
| 4 | 129 asset instances | none written; 0 of 4,128 criterion cells certified |

The tracker that reads tiers 3–4 is `00_ARCHITECTURE/control/asset_elevation_tracker.py`, with its two
append-only ledgers `asset_gaps.jsonl` and `asset_certs.jsonl`.
