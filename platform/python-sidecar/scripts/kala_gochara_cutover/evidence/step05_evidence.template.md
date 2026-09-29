# Step 5 evidence — Registry re-pin (plan §6.3)

Runbook step 5 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Registry re-pin (plan §6.3) — count_sql/clear_tables/conjuncts (a)-(k)/depends_on; century clear_tables (F-30)
- **Gate:** count_sql relation = target_table; cockpit reads new count; Clear-proof test green; cockpit-0-between-5-and-6 is EXPECTED
- **Reversal:** step05_reversal.sql (snapshot restore)
- **DSN target:** (record the exact instance this evidence covers)
- **Operator / principal:** (record)

<!-- Run outcomes are appended below by the step scripts (--evidence). -->
