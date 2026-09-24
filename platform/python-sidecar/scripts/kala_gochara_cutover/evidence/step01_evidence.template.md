# Step 1 evidence — Phase 1.2

Runbook step 1 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Phase 1.2 — SELECT on both v1 archives for data_plane_builder
- **Gate:** has_table_privilege true on kala_gochara_windows and kala_gochara_windows_archive_20260805
- **Reversal:** REVOKE
- **DSN target:** (record the exact instance this evidence covers)
- **Operator / principal:** (record)

<!-- Run outcomes are appended below by the step scripts (--evidence). -->
