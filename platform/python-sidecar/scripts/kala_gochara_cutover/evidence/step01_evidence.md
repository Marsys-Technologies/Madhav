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
- **DSN target:** production via Cloud SQL proxy 127.0.0.1:5433 (madhav-astrology:asia-south1:amjis-postgres), database amjis
- **Operator / principal:** subagent (l3/gochara-autonomous-wp0-7, §7.B tranche 1) as `amjis_app` (table owner)

<!-- Run outcomes are appended below by the step scripts (--evidence). -->

## 2026-09-24 — GREEN

Run: `psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -v ON_ERROR_STOP=1 -f step01_select_grant.sql`
→ BEGIN … GRANT ×2 … in-transaction DO gate probe passed … COMMIT. Both archive
relations existed in the live catalog (grant on `kala_gochara_windows_archive_20260805`
did not fail).

Gate verification:
- As `amjis_app`: `has_table_privilege('data_plane_builder', public.kala_gochara_windows, SELECT)` = **t**; same for `kala_gochara_windows_archive_20260805` = **t**.
- Independently as the grantee `data_plane_builder` (credential from Secret Manager
  `data-plane-builder-db-url`, value never printed): `SELECT count(*) FROM
  kala_gochara_windows` → **40117** (38287 v1 + 1830 3.0); `SELECT count(*) FROM
  kala_gochara_windows_archive_20260805` → **35620**. Read-only verification only.

**Verdict: step 1 GREEN.** Reversal: the two REVOKEs in the step header.
