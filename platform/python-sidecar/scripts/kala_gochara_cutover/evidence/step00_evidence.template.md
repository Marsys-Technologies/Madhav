# Step 0 evidence — Phase 1.1

Runbook step 0 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Phase 1.1 — Clear is_active filter + (table, generation) guard (consumes origin/l3/kala-p1-1-b1-clear-guard, cherry-pick eb00da67d with attribution)
- **Gate:** route test green; stale migration-540 comment at clear/route.ts:95-96 gone
- **Reversal:** revert cherry-pick
- **DSN target:** (record the exact instance this evidence covers)
- **Operator / principal:** (record)

<!-- Run outcomes are appended below by the step scripts (--evidence). -->
