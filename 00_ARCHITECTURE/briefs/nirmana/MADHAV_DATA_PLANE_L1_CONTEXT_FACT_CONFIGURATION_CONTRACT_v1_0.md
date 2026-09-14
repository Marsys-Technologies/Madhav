---
artifact: MADHAV_DATA_PLANE_L1_CONTEXT_FACT_CONFIGURATION_CONTRACT
version: "1.0"
status: IMPLEMENTED_LOCAL
implementation_commits:
  - 7cabc0cfd1eae83f0a1054132d3c850c6b760153
  - 3cb1a84ae
  - bcda11997
  - 0fc45813e
  - b2c4f1d7f
  - a9c44c298
contract_version: l1.data-plane.contract.1.0
---

# L1 context, fact and configuration contract

The executable authority is
`platform/python-sidecar/ga_writers/data_plane_contracts.py`. This record explains
its compatibility and later-consumer obligations; it does not authorize retrieval or
serving.

Runtime authority is shared by `ga_writers/data_plane_runtime.py` and migration
`1035_data_plane_l1_producer_history.sql`. Exactly the 19 registered GA adapters open a
transaction-local generation partition before computation and complete it only after the
writer returns. Eleven bounded output surfaces use transaction-local row capture. Daśā is
the high-volume exception: each completed system/ayanāṃśa partition is copied set-wise into
an append-only typed composite history table, and the final post-pass adds only changed
revisions, preserving COPY throughput and the active adapter identity.

## Calculation context

A context contains subject and chart identity; observation build and generation; aware
ISO instant; latitude, longitude, timezone and input precision; tropical/sidereal frame;
ayanāṃśa; explicit mean/true node; house convention; varga, formula and domain; karaka
school; engine version; and exact accepted-L0 semantic/configuration pins.

`context_id` hashes the semantic calculation context and deliberately excludes build and
generation. `generation_key` adds both observation dimensions. A join fails closed on
subject, chart, semantic context, build or generation mismatch. Unknown L0 pins, naive
timestamps, invalid coordinates, ambiguous nodes and unknown frames are rejected.

## Stable fact identity and value state

The semantic key is category + subject + key + chart + ayanāṃśa + complete semantic
`context_id` + legitimate formula or method variants. Build/generation never redefine the fact. Existing storage may retain
build in an observation uniqueness constraint and history; that is compatible because the
stable `fact_id` names what was observed while the generation key names when/how it was
observed.

Each `FactEnvelope` carries grain, unit, exactly one typed value when present, epistemic
class, verification class, dependencies and optional reason. Missingness is closed:
`present`, real numeric `zero`, `unavailable`, `floored`, `inapplicable`,
`unqualified_source`, `failed`, `unexplored`. Non-value states cannot serialize a normal
value and require a reason. Numerical failure therefore cannot become zero, empty success
or Aries/0°.

The runtime projection carries source table and exact natural-key grain, accepted L0 pins,
calculation context, dependencies, typed source row, unit, epistemic/missingness/
verification classes and a normalized semantic digest. Only an explicit material-field
registry decomposes the 45-row condition composite: each field has its own unit, epistemic
class, verification method, actual constituent fact IDs, source-row identities and named
reference relations. Other denormalized rows remain bounded typed row envelopes; they are
not multiplied into generic field facts. Daśā numeric values are checked before COPY.
Wrong chart/build values and non-finite values abort the writer transaction. A failed writer
never completes a partition or advances the selected generation.

Daśā history uses one canonical semantic payload for replay, generation digest and
selection. It retains deterministic interval and parent UUIDs, excludes only observation
`build_id`/`computed_at`, and normalizes material timestamps to UTC epoch values. A stored
generated digest keeps full-cardinality comparison set-wise. Condition peak/weak-period
ancestry is selected and surfaced only at exact chart, ayanāṃśa, build, lord and level.
The upstream build remains in the enclosing observation context rather than the nested
semantic period value, so compatible rebuilds retain equal condition semantics.

Epistemic classes are astronomical, deterministic derivation, rule-derived, judged,
documented approximation, engineering fixture and restricted scholarly. Later consumers
must retain the producer class and may add interpretation only in their own layer.

## Configuration occurrence

Every occurrence carries configuration/version, exact source rule/version/qualification,
participants with roles, satisfied and failed clauses, exceptions, cancellations and
identity-deduplicated constituent facts. States are `formed`, `partial`, `not_formed`,
`failed`, `method_inapplicable`, `unqualified_source`.

A positive doctrinal state requires `QUALIFIED_EXECUTABLE`. An unqualified source can
produce only `unqualified_source`, and its positive arm is `NOT_REACHABLE`. A positive
engineering state must be non-doctrinal and `ENGINEERING_ONLY`. Catalog labels, citations
and fixtures cannot elevate qualification.

Runtime yoga rows preserve observed firing/partial state separately from admitted rule
state. The observed catalog rule is identified by `catalog:yoga:<id>` and a SHA-256 content
version; participants are typed graha/house roles and the observed rule/ancestry plus failed
qualification clauses are explicit. Because the active schema has no admitted L0
qualification witness, the projection records `UNQUALIFIED_SOURCE`,
`unqualified_source` and a missing-witness clause rather than turning an observed firing
into doctrinal authority.

The accepted Bhāvat Bhāvam package remains L2-owned, unapplied and
`UNQUALIFIED_SOURCE`; this contract creates no dossier or doctrinal authority.

## Compatibility rules

Existing stored rows are not rewritten. Corrected IDs apply to new/replayed observations;
the append-only store preserves every post-migration generation and every within-build
revision while latest-row projections select one final logical row. Completed generations
admit only canonical semantic replay of the same stable identities; new or changed rows require
a distinct correction generation. Active tables retain their existing interfaces. Consumers may
join only on an exact context/generation key or an explicitly versioned compatibility
projection. Aliases and row order are irrelevant; method/formula variants are material.
