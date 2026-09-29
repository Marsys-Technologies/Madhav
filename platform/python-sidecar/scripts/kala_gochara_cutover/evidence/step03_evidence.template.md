# Step 3 evidence — Guard

Runbook step 3 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Guard — (table, generation) trigger for 'v1'/'3.0' + N-6a century is_active=false
- **Gate:** DELETE/UPDATE/TRUNCATE on protected generations fail loudly; '4.0' writes pass; century cannot dispatch
- **Reversal:** step03_reversal.sql (DROP trigger + restore is_active)
- **DSN target:** (record the exact instance this evidence covers)
- **Operator / principal:** (record)

<!-- Run outcomes are appended below by the step scripts (--evidence). -->
