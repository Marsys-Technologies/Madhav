---
artifact: MADHAV_DATA_PLANE_L1_COMPATIBILITY_CORRECTION_ROLLBACK
version: "1.0"
status: PRODUCER_CONTRACT_IMPLEMENTED_LOCAL
implementation_commits:
  - 7cabc0cfd1eae83f0a1054132d3c850c6b760153
  - 3cb1a84ae
  - bcda11997
  - 0fc45813e
  - b2c4f1d7f
  - a9c44c298
---

# L1 compatibility, correction and rollback

## Compatible generations

Semantic identity excludes build/generation; observation identity includes both. A later
generation is join-compatible only when subject, chart and complete semantic context match
and the consumer explicitly selects the intended build/generation. Formula, method, frame,
ayanāṃśa, node, house, varga/domain, engine or accepted-L0 pin changes rotate context or
variant identity.

## Correction and invalidation

The corrected producers stop generating new build-dependent/random identities. Existing
rows and delivered references are not rewritten. Migration 1033 captures new row versions
transactionally before active-table replacement can erase them. On a compatible rebuild,
normal writer idempotency still replaces only the writer's owned active scope while stable
fact/interval IDs and normalized row digests permit comparison. A semantic-input change invalidates that context and all derived
conditions/configurations/relations/clocks; unrelated contexts remain valid.

Cache keys must include the semantic `context_id` and exact generation/build. A cache may
reuse only byte-identical contract and accepted-L0 pins. Stale-before-use checks reject a
different generation; wrong-context joins fail closed.

## Dependency cascade

Positions feed vargas/nakshatra/conditions/strength/structure; those feed configurations,
judgments, annual/phase/anchor capital and later layers. Cascade marks dependent producer
artifacts stale; it does not delete another writer's rows or infer consumer invalidation
success. The generated writer inventory was deterministically regenerated and its own
`--check` passes. Transitive hashes moved by design. The protected
`nirmana-analysis-layer-pins.json` was not changed or given a fabricated convergence SHA;
that protected-delivery reconciliation is unreached.

## Replay and rollback

`l1_data_plane_generations` opens one generation per chart/asset/build and completes only
after all expected writer partitions have receipts. `l1_data_plane_row_snapshots` retains
bounded source rows with calculation context, natural-key grain, dependencies, epistemic,
missingness, verification, unit and normalized semantic digest. Daśā uses the exact typed
`chart_dashas` composite in `l1_data_plane_dasha_snapshots`, copied once per completed
partition; its final post-pass appends only changed revisions. Partition and both snapshot
stores reject update/delete. Eleven output-table triggers plus the set-based dasha path
cover all 12 L1 output tables; the shared `chart_facts` trigger uses the transaction-local
adapter identity. One canonical dasha semantic payload excludes only build/time observation
metadata, preserves stable row/parent hierarchy and normalizes timestamp values independently
of the PostgreSQL session timezone; its generated per-row digest supports exact replay and
generation hashing without row-trigger amplification.

`select_l1_data_plane_generation(chart, asset, generation)` returns only a complete exact
generation and chooses the latest snapshot for a logical row updated within that build.
`l1_data_plane_current_rows` and `l1_data_plane_current_dashas` follow the selected head.
`rollback_l1_data_plane_generation` can select any retained complete generation while
preserving the formerly selected head as `previous_generation_id`; it rewrites no producer
row. Local PostgreSQL proof retained two generations after active replacement, reproduced
an identical semantic digest for same-input replay, selected the old generation exactly,
and rolled the head back. The original 536,000-row dasha partition plus typed history,
generation digest and commit completed in 9.83 seconds locally. After canonical replay
correction, a fresh 536,000-row capture/digest completed in 15.09 seconds, completed replay
after changing every `computed_at` completed in 8.72 seconds, and the same stable semantic
rows under a second build completed in 14.58 seconds with the identical generation digest.
The selector returned all 536,000 rows in 7.24 seconds with no null digest or leaked
build/computed time, and emitted zero generic/fact child rows. The post-pass proof retained three updated
revisions plus two sentinels while recording the adapter receipt of two. Wrong-build rows,
non-finite numeric output, completed-generation mutation and snapshot deletion failed
closed. This is local persistence evidence, not deployed or end-to-end performance.
Migration reapplication was idempotent.

No migration was applied to a live database and no pre-1033 history is fabricated or
backfilled. Deployment order is migration first, adapters second. Code rollback removes
the adapter decorators while retaining append-only evidence; destructive schema removal
requires separate authorization.

## Field offer for DP10-DP12

Later integration may consume: context and generation keys; stable fact/occurrence/interval
IDs; typed values and units; missingness/reasons; epistemic and verification classes;
source dependencies; configuration clauses/participants/exceptions/cancellations; typed
relation actor/target/method/orb/roots; exact clock hierarchy; sensitivity classification;
and restricted-service posture. This is producer metadata, not registry or serving change.
