---
subsystem: prashna_l0
gate: Gate-1 PASS → entering Gate-2
timestamp: 2026-06-17
tier: Tier-1 (auto-resolved)
---

# Prashna-L0 Gate-1 Pass Notes

## What was built
- `bg_prashna_rules` writer: `@register('bg_prashna_rules')`, light `run(ctx)`, §5 conformance clean
- 5 Prashna-Lagna methods: tajik_moment_lagna, **kp_249 (primary)**, aarudha_based, chandra_lagna, swara_based
- 11 Tajik horary yogas: ithasala, eesarpha, nakta, yamaya, manaau, kambula, gairi_kambula, dutthottha, rudda, khallasara, duhphali_kuttha
- 12 significator question classes (marriage → enemy_conflict)
- 5 fructification timing rules (degree_to_hours → sign_quality_timing_matrix)
- 3 special techniques (nashta_jataka, tithi_nakshatra_yoga, omen_nimitta)
- Total: 36 rows across 5 tables

## Migrations
- 261: schema (5 `bg_prashna_*` tables, all `CREATE TABLE IF NOT EXISTS`)
- 262: asset_registry (count_sql aggregates all 5 tables = 36, target_floor=36, sort_order=5)

## Spec-review verdict: SPEC_COMPLIANT_MINOR_GAPS → resolved
- Gap found: count_sql counted only bg_prashna_tajik_yogas (11 rows) instead of all 36
- Fix: committed in fix commit e6be7384 — count_sql now aggregates all 5 tables

## Tier-2 decisions
1. Migration 263 not used (262 covered asset_registry) — slot 263 reserved for future prashna_charts plumbing
2. sign_quality_timing_matrix rule added (5th fructification rule) — legitimate Tajika Nīlakaṇṭhī Ch.5 rule, not padding
3. omen_nimitta scoped conservatively to only rules with explicit classical support

## Hard gate status
- PASS: every row has non-empty classical_citation
- PASS: no per-chart columns in any table (L0 chart-agnostic)
- PASS: all INSERTs ON CONFLICT DO NOTHING

## Gate-2 status
- PR to be created: feature/subsystem-prashna → main
- Pending: CI green + merge + surgical migration apply (261, 262 in order)
- Gate-3: bg_prashna_rules cockpit tile lit (no chart compute; just rule count)
