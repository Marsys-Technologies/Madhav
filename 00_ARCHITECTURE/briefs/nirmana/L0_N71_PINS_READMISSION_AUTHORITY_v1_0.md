---
artifact: L0_N71_PINS_READMISSION_AUTHORITY
decision_id: N-71
version: "1.0"
status: PINS_READMISSION_AUTHORIZED
produced_by: Exec Suvarṇa (recording the decision of Strategic Suvarṇa)
produced_on: 2026-10-02
---

# N-71: L0 analysis-receipts pin re-admission (authority record)

status: PINS_READMISSION_AUTHORIZED

## Authority

Decision made by Strategic Suvarṇa under the owner's delegation of campaign decisions (N-43); the owner was informed on 2026-10-02. This record does NOT state that the native ratified the decision personally; it states exactly who decided and under which delegation.

## Decision (verbatim)

> N-71: The L0 analysis-receipts pin test stays as a tripwire. An L0 writer digest moved only by an import-closure change is admitted by a transparent re-pin stating exactly which single L0 digest moved and that the others are byte-identical. Applies to Pravāha's #2882 (bg_gochara_arcs) and to Suvarṇa's bg_ephemeris mean-node change.

## Scope of this authorisation

Exactly one L0 successor admission over the `bg_gochara_arcs` digest move caused by PR #2882 (classification `derived_import_change`): no membership change; the other 39 L0 writer digests are byte-identical to the active predecessor pin. A separate admission of the same kind, under this same decision, is intended for Suvarṇa's `bg_ephemeris` mean-node change when it lands; it is not authorised by this record's scope line and will be admitted by its own successor with its own source commit.

## Procedure bound to this record

`python -m scripts.generate.nirmana_analysis_layer_pins --admit-successor --layer L0 ... --authority-decision N-71 --classification bg_gochara_arcs=derived_import_change`, with the standing L0 acceptance artifact as review artifact; verification with `--check` and `--check --delivery-topology`.
