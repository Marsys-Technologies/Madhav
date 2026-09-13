---
artifact: MADHAV_DATA_PLANE_L0_COMPATIBILITY_CORRECTION_ROLLBACK
version: "1.0"
status: IMPLEMENTED_FOR_CHANGED_COMPONENTS
produced_on: 2026-09-13
---

# L0 compatibility, correction and rollback record

## Generation set

| Component | New/current generation | Compatible predecessor | Invalidation and rollback |
|---|---|---|---|
| graha semantic release | `l0-semantic-g1` / digest `b5563e1e...ad2a7` | `legacy.local-vocabularies.pre-l0.semantic.2026-09-13.1` | identity/code change stales adapters and identity fixtures; alias-only addition does not stale computations; revert adapters/remove release to restore old local vocabulary |
| resource/config slice | `l0-resource-config-g1` / digest `ccd43845...1f9` | `legacy.bhavat-bhavam-map.1.0` | qualification/identity consumers stale; map values and historical rows do not; select prior adapter generation |
| ephemeris service context | `l0-ephemeris-service-context/v1` + registry generation `migration-624` | prior response without context | additive response metadata; revert router; Ketu speed correction requires consumer recalculation, never historical receipt rewrite |
| Panchanga service context | `l0-panchanga-service-context/v1` | prior permissive request contract | clients relying on guessed timezone must supply it; revert router to restore legacy behavior |
| gochara arcs | existing caller-selected `substrate_version` | prior stored substrate versions | current-generation rebuild cleans only current unknown bodies; prior versions retained and selected by version; revert scoped DELETE |
| L0 inventory description | generated 36 writers + generated four non-writers | historical 12-item literal | generated count drift fails module/test; revert adapter restores historical but incomplete literal |

All changed producer packages are content-addressed or pinned to existing
generation identifiers. Repeat validation produces the same digests. No current
cache, delivered reading or database row was selected or rewritten, so there is
no authorized cache purge or data rollback to perform.

## Typed correction map

| Correction type | Old → new | Affected | Not affected |
|---|---|---|---|
| identity/meaning | explicit true-node aliases collapsed/unknown → distinct physical identities | Python/TS identity adapters and identity fixtures | stored historical readings and numerical positions |
| computation | Ketu speed sign inverted → same signed speed as antipodal Rahu | future ephemeris response values | source corpus and prior immutable receipts |
| context/input | implicit timezone/default mixing → complete tuple or named pin | Panchanga callers | engine calculations under already complete context |
| compatibility | cross-generation arc deletion → current-generation cleanup only | rebuild retention behavior | current version rows and body set |
| discovery | frozen 12-asset description → generated 40-identity description | producer inventory visibility | campaign denominator and generated authority files |
| source qualification | label/map without status → explicit unresolved witness/state | slice-aware producer adapters | source text, map values, L1/L2 behavior |

## Residual generation limits

KP division, formula constants, sky-calendar, Muhūrta, Vidhi floors and some
other extant writers remain current-generation projections or use natural-key
upserts that do not by themselves retain every prior meaning. Their source and
method variants are documented but were not altered without a proved schema and
authority-safe migration. Rollback for those unchanged components remains source
revision + deterministic rebuild, not an unproved simultaneous-generation query.

The prior immutable source revision is `60a379d2dc7e2fbc05c95f425d9eacc7b2b6863c`.
No push, migration, rebuild, database mutation or deployment was performed.
