# Step 2 evidence — Restore drill

Runbook step 2 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Restore drill — 2026-08-23 dump into disposable DB, 38,287 v1 rows content-checked
- **Gate:** row-by-row digest equality; 2,667-uncovered-id report attached
- **Reversal:** none needed
- **DSN target:** (record the exact instance this evidence covers)
- **Operator / principal:** (record)

<!-- Run outcomes are appended below by the step scripts (--evidence). -->
