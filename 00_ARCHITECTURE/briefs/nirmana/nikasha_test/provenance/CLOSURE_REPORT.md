---
artifact: NIKASHA_WAVE1_B2_CLOSURE_REPORT
version: "1.0"
generated_at: 2026-09-27T06:15:33.887999+00:00
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

- `bg_cohort` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_concordance` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_gochara_arcs` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_gochara_citation_resolution` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_prashna_rules` — table_unregistered (bg_prashna_fructification_rules, bg_prashna_lagna_methods, bg_prashna_significators, bg_prashna_special_techniques, bg_prashna_tajik_yogas, ga_prashna_lagna): a catalog unit queries a table this asset's writer likely owns under a same-domain name, but no asset_registry row claims it as target_table — a registry-coverage gap, not a true absence of a producing unit
- `bg_vidhi_floors` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `bg_vidhi_primitives` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)

### bodha (1)

- `bo_grounding` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)

### ganita (1)

- `ga_prashna` — table_unregistered (bg_prashna_fructification_rules, bg_prashna_lagna_methods, bg_prashna_significators, bg_prashna_special_techniques, bg_prashna_tajik_yogas, ga_prashna_lagna): a catalog unit queries a table this asset's writer likely owns under a same-domain name, but no asset_registry row claims it as target_table — a registry-coverage gap, not a true absence of a producing unit

### kala (2)

- `ka_kshetra` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `ka_tulana` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)

### mimamsa (5)

- `lel_events` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `mi_bhara` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `mi_sankalpa` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `mi_seva` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)
- `mi_vistara` — no_unit_names_it: no catalog unit names this asset as a producer, and no unit-producing asset depends on it (transitively)

## Still-outside reason class counts (C-6)

`table_unregistered` is distinct from `no_unit_names_it`: the former means a catalog unit DOES read a same-domain table this asset's writer likely produces, just under a name `asset_registry.target_table` doesn't record (a registry-coverage gap — D5 part 3 merge/retire candidate); the latter means no catalog unit resolves to this asset at all.

- `no_unit_names_it`: **14**
- `table_unregistered`: **2**

