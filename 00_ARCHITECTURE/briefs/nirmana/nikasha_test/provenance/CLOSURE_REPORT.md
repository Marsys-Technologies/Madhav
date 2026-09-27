---
artifact: NIKASHA_WAVE1_B2_CLOSURE_REPORT
version: "1.0"
generated_at: 2026-09-27T05:52:17.150840+00:00
generator: platform/scripts/governance/catalog_provenance.py --closure
---

# Nikaṣa wave 1 — B-2 necessity closure report

Population: `SELECT count(*) FROM asset_registry WHERE is_active AND dead_flag IS NOT TRUE` = **127** (R220). NOTE: `dead_flag` is NULL on every production row today, so a literal `is_active AND NOT dead_flag` reads 0 rows (three-valued-logic trap) — `dead_flag IS NOT TRUE` is the correct predicate and reproduces the documented population of 127.

## Before (reviewed producers only — the D5 rev. 2.1 ruling's own baseline)

- Named producer assets: **14**
- Necessary (closure ∩ active population): **63 / 127**

## After (reviewed ∪ derived producers — this session's B-1 output)

- Named producer assets: **94**
- Necessary (closure ∩ active population): **111 / 127**

## Still outside the closure, by layer

### brahmagyan (7)

- `bg_cohort` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_concordance` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_gochara_arcs` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_gochara_citation_resolution` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_prashna_rules` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_vidhi_floors` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_vidhi_primitives` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)

### bodha (1)

- `bo_grounding` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)

### ganita (1)

- `ga_prashna` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)

### kala (2)

- `ka_kshetra` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `ka_tulana` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)

### mimamsa (5)

- `lel_events` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `mi_bhara` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `mi_sankalpa` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `mi_seva` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `mi_vistara` — no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)

