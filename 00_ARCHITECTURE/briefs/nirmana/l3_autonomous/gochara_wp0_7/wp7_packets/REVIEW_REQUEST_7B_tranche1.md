---
artifact: WP7_REVIEW_REQUEST_7B_T1
packet_id: "§7.B-tranche-1"
version: "1.0"
status: STOPPED_AWAITING_NATIVE
date: 2026-09-24
author: "subagent (l3/gochara-autonomous-wp0-7, §7.B tranche-1 run)"
design_file: "GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9 steps 0–5; GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md §3 (A-2 authorized)"
commit: 8c1fc0680
---

# REVIEW REQUEST — §7.B tranche 1 (steps 0–5): HALTED at step 3

## What happened

Both `PRODUCTION_TRANCHE_*` flags read TRUE from the brief frontmatter (native ruling
§3). Cloud SQL proxy up (127.0.0.1:5433). Run order per brief §12.15: **step 3 first**.

- **Step 3 — STOPPED.** `step03_guard_n6a.sql` aborted on its first statement
  (`CREATE OR REPLACE FUNCTION kala_gochara_generation_guard()`): `permission denied for
  schema public`. Verified read-only: `amjis_app` lacks CREATE on schema `public` (owner:
  `data_plane_schema_owner`), is not superuser, holds no role memberships; no other
  credential exists in any local env file. The transaction rolled back cleanly.
- **Production verified byte-identical to pre-state** afterwards: no guard function,
  0 triggers on `kala_gochara_windows`, generations `v1=38287 / 3.0=1830` unchanged,
  `build_protected_assets` 0 rows, century `is_active=false` (the strategic session's
  earlier fragile half) intact, both authority rows `'3.0'`.
- **Steps 0, 1, 2, 4, 5: NOT RUN** — the failed-gate rule halts the tranche; nothing was
  improvised around it. Step 2 would have been NOT_RUN regardless (no dump locally).
- **§7.C not started** — tranche-1 evidence green is a precondition and does not exist.

## Evidence and escalation

- `platform/python-sidecar/scripts/kala_gochara_cutover/evidence/step03_evidence.md`
  (standing order acknowledged in the header; DSN target and principal recorded).
- **ESCALATIONS.md E-015**: the native's operator path — run step 3 as
  `data_plane_schema_owner`/`postgres` (exact psql command and read-only verification
  queries included), or GRANT CREATE ON SCHEMA public TO `amjis_app` and the run
  re-attempts. E-015 also pre-records the step-4 discrepancy note (committed APPLY_SET
  1080–1084+1087 vs A-2's literal 1080/1081, E-010 open item) — no migration was
  attempted against production; none of 1080/1081/1082/1083/1084/1087 are applied there
  (verified).

## Pre-flight facts the reviewer can re-check

- Production pre-state snapshot taken before any write attempt (recorded in the evidence
  file's session narrative and reproduced above).
- The step-3 SQL itself is unchanged from the rehearsed artifact; the rehearsal gate
  `test_wp10_cutover.py` (16/16 green on the disposable DB) covers the guard's semantics
  — the halt is a privilege fact about the production principal, not a script defect.

Nothing marked REVIEWED. The cloud-sql-proxy on 5433 was left running deliberately for
the native's E-015 operator path (started by this session:
`cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres --port=5433`).
