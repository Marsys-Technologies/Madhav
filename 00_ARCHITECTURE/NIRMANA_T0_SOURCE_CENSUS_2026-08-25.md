---
artifact: NIRMANA_T0_SOURCE_CENSUS_2026-08-25.md
canonical_id: NIRMANA_T0_SOURCE_CENSUS
status: SOURCE-EVIDENCE-ONLY
campaign_id: nirmana-elevation
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
observed_on: 2026-08-25
---

# Nirmāṇa T0 source census — 2026-08-25

## Scope and limitation

This is a read-only static census of current source intent. It is not a campaign
definition, denominator, execution plan, or acceptance receipt. T0 may freeze none
of its counts until it reconciles the production registry, planner filter, runtime
evidence, migrations, and campaign evidence tables described in the v6 plan.

## Reproducible source result

The `ASSETS` catalogue in `platform/scripts/seed/asset_registry_seed.ts` contains
127 distinct asset IDs and 226 declared dependency edges:

| Layer | Registry layer | Candidate assets |
| --- | --- | ---: |
| L0 | `brahmagyan` | 39 |
| L1 | `ganita` | 19 |
| L2 | `bodha` | 22 |
| L3 | `kala` | 23 |
| L4 | `phala` | 9 |
| L5 | `mimamsa` | 15 |

The current source graph has 77 cross-layer edges. Its declared dependencies have
no duplicate asset IDs, dangling references, backward-layer edges, or cycles under
the source layer ordering. This is a source-graph assertion only; it says nothing
about the rows deployed in Cloud SQL, their active status, their writer state, or
their outputs.

The source extraction must read each top-level `ASSETS` object lexically (rather
than import/execute the seed) and emit at least `asset_id`, `layer`, `scope`,
`target_table`, `asset_kind`, and `depends_on`. Writer discovery must then scan the
production writer and service paths only, excluding tests, docs, comments, and
tombstone shims.

## Reconciliation findings

1. Runtime planning and dispatch select `asset_registry` rows where both
   `is_active=true` and `has_writer=true`; the tracker source at this census selected
   all active rows. A tracker denominator cannot be frozen until this mismatch is
   removed and live rows are reconciled.
2. `bg_panchanga` and `bg_ephemeris_engine` are service probes, not decorated
   writers; `bg_sarvatobhadra_grid` is intentionally empty; and `lel_events` is
   user-authored source. They require explicit v6 obligations/dispositions, not an
   inference from a missing decorator.
3. `ka_gochara_sweep` retains a historical shim but migration 563 retires it;
   retained source cannot establish it as a build candidate. Conversely,
   `bo_anveshana` remains a buildable source candidate despite a parked retirement
   note.
4. Planner topological waves are execution mechanics. Campaign `wave_index` must
   be assigned and frozen in the reconciled manifest, never inferred from
   `sort_order` or a source-only planner calculation.

## Required live T0 evidence

For every candidate, collect the current `asset_registry` identity, layer,
sort-order, scope, target table, dependency array, active/writer/catalog/kind state,
count and health contracts. Reconcile those rows with table existence, scoped
throughput, protected assets, runs, run assets, substep progress, applied migrations,
and the latest campaign definition/events. Validate the frozen manifest digest,
unique IDs, DAG, and the same planner eligibility filter before it can define any
campaign total.
