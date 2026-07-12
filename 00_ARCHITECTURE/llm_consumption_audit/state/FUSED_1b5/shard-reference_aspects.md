# FUSED 1b+5 shard — reference_aspects (1 family)

| family_key | channel | retrievability_verdict (1b) | fidelity_verdict (5) | derivation |
|---|---|---|---|---|
| `__table_row_count__=19` | truly-UNREACHABLE | NOT RETRIEVABLE — internal L0 graha-drishti reference table (planet_id, aspect_house, aspect_strength, strength_value, is_special). No consumer tool in the surgical whitelist serves it; consumed by L1 `ga_*` aspect writers only. | N/A (internal reference, never on wire) | path-grade(exemplar=`__table_row_count__=19`) + member-confirmation (single family) |

## Evidence
- DB truth: `SELECT count(*) FROM reference_aspects` = 19 (matches ledger). Global reference (no chart_id): special-drishti strengths per planet/aspect-house.
- No surgical-whitelist tool targets reference_aspects. The Jaimini-drishti front `query_jaimini_drishti` is itself in DEAD-19; and it would not serve this Parashari-aspect reference regardless.

## Findings
- **[lane 1b][class 1 UNREACHABLE][LOW] Graha-drishti reference unreachable.** The 19-row special-aspect strength reference is a build-time input to L1 aspect computation, not consumer-served. Its aspect_strength / strength_value (which house a graha aspects and how strongly) is never independently retrievable to justify an aspect verdict; consumers see only the L1-derived aspects, not this rulebook. Likely acceptable-by-design (internal reference), logged for coverage honesty. Repro: no tool in whitelist targets it.
