---
artifact: WP7_REVIEW_REQUEST_7B_T1
packet_id: "§7.B-tranche-1"
version: "2.0"
status: REVIEWED_BY_ADHIKARIN
disposition: "REVIEWED_BY_ADHIKARIN 2026-09-27 per ADK-0013 — ACCEPT as the record of a tranche completed GREEN under the native's 2026-09-24T11:39:01Z ruling; residual items disposed: (3) conjunct-(j)/1072 is merge-time information carried to the merger (HOLD_STATE); (4) standing-grant question remains the native's; (5) secret rotation remains the native's (transcript-scope, verified no-commit); harness fidelity fix (test_wp10_cutover.py clear_tables TEXT→text[]) assigned to this lane and DISPOSED 2026-09-27 (17 passed on disposable DB, negative check added; see residual line below). NOT marked REVIEWED: K3/O-2 is separate and unaffected."
date: 2026-09-24
author: "subagent (l3/gochara-autonomous-wp0-7, §7.B tranche-1 run, second attempt under E-015 authorization)"
design_file: "GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9 steps 0–5; GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md §3 (A-2 authorized); E-015 native 'go ahead'"
commit: a5d7a81e4
supersedes: "v1.0 (halted at step 3, pre-authorization)"
---

# REVIEW REQUEST — §7.B tranche 1 (steps 0–5): HALTED at step 5 — steps 0/1/3/4 GREEN, 2 NOT_RUN, 5 FAILED

## What happened (2026-09-24, second attempt)

The native authorized the E-015 operator path ("You have my authorization, please go
ahead"). Privilege resolution: no Secret Manager/local credential existed for
`data_plane_schema_owner`/`data_plane_migrator`/`postgres`; `postgres` is itself locked
out of schema public (Sept cutover). Path used: rotated `data_plane_migrator` password,
updated the `data-plane-production-cutover` env secret `DATA_PLANE_MIGRATOR_DATABASE_URL`
to the pinned proxy format; as migrator with `SET ROLE data_plane_schema_owner`,
**temporary** `GRANT CREATE ON SCHEMA public TO amjis_app`. Also rotated `postgres` and
set the previously-unset `DATA_PLANE_OWNERSHIP_ADMIN_DATABASE_URL`.

Per-step outcomes (evidence under
`platform/python-sidecar/scripts/kala_gochara_cutover/evidence/`):

- **Step 0 — GREEN** (`cacc72440`): cherry-pick `-x eb00da67d`; no migration collision
  (origin/main head 1070); protected-assets route test 2/2; MIG-1 guard PASS.
- **Step 1 — GREEN** (`e8cbce231`): SELECT grants to `data_plane_builder`; verified as
  grantee (40117 / 35620 rows).
- **Step 2 — NOT_RUN** (`9a786de9e`): no 2026-08-23 dump locally; recorded, not waived.
- **Step 3 — GREEN** (`8a7f5e692`): guard function + both triggers live; all four gate
  probes behave; generations v1=38287 / 3.0=1830 unchanged; century `is_active=false`.
- **Step 4 — GREEN, scoped** (`4670bebab`): only **1080/1081** applied, through the
  script's own machinery with APPLY_SET/EXPECTED_COLUMNS scoped. **1082/1083/1084/1087
  NOT applied — E-016, native ruling needed.**
- **Step 5 — FAILED → tranche HALT (E-017).** Migration 1091 aborted on
  `malformed array literal: "[kala_gochara_windows, ...]"` — production
  `asset_registry.clear_tables` is `text[]`, the script wrote `'[...]'`, and the
  rehearsal harness (`test_wp10_cutover.py` ~line 137) declares the column TEXT, so the
  16/16 rehearsal could not see the defect. Single-transaction abort; production verified
  unchanged. Corrected 1091 (`'{...}'` ×2 + header note) **prepared but NOT re-run** —
  the authorization covered the privilege path, not script surgery.

## What the reviewer is asked to rule on

1. **E-017 / step 5 resume:** approve applying the corrected 1091 (requires re-granting
   CREATE to `amjis_app` first — one command, recorded in ESCALATIONS.md), and approve
   fixing the rehearsal harness's `clear_tables` column type to `text[]`.
2. **E-016:** disposition of 1082/1083/1084/1087 (follow-up tranche vs post-merge deploy
   pipeline); note tranche 2's step-6 writer may need 1087's columns.
3. **Merge-time interplay:** unapplied cherry-picked 1072 would set ka_gochara
   `target_table='kala_gochara_windows_v2'` and break step-5 conjunct (j) if it lands
   after a successful step 5 (see step05 evidence §12.14 sweep).
4. **Grant posture:** the temporary CREATE grant to `amjis_app` was revoked at halt
   (verified `has_schema_privilege=f`). Residual E-015 question: should it become
   standing? (Sept cutover design says no; default held.)
5. **Incident disclosure:** an early malformed `export PW_<name-with-dashes>=...` line
   echoed four secret values (`nirmana-campaign-control-db-password`,
   `nirmana-evidence-ingress-db-password`, `retrieval-census-ro-db-password`,
   `amjis-inquiry-db-password`) to stderr in the session transcript. No values were
   committed anywhere; consider rotating those four secrets.

## Guards never weakened

Step 0 still builds the (table,generation) guard; step 5 keeps the Clear is_active
filter and EXPLICIT_CLEAR_OPS; the failed gate stopped the tranche; evidence was written
before each next step. Nothing marked REVIEWED. The cloud-sql-proxy on 5433 was left
running for the native (`cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres
--port=5433`).

---

## v2.1 addendum (2026-09-24, second session) — tranche 1 COMPLETE, GREEN

The native ruled on every open point (verbatim, 2026-09-24T11:39:01Z:
**"Approved on point number two. Go ahead to everything."** — recorded in
ESCALATIONS.md). Outcomes under that ruling:

- **Step 5 RESUMED → GREEN** (`3fcf6a586`): grant re-established, corrected 1091
  applied as `amjis_app` (clean: snapshot ×2, 3 UPDATEs, DO probe, COMMIT), all
  gates pass — conjunct (j) holds, new count executes (0 for both authority
  charts, EXPECTED pre-step-6), rehearsal Clear-proof 16/16 on a fresh
  disposable DB, production integrity contract evaluates `integrity_passed=t`.
  Grant revoked and verified (`=f`). **E-017 RESOLVED.**
- **E-016 RESOLVED** (`5ee6280bd`): full committed APPLY_SET applied —
  1082/1083/1084/1087 now live; 1084 as committed (`ka_kshetra → ka_gochara`
  edge verified absent); information_schema diff empty; generations
  v1=38287/3.0=1830 and both '3.0' authorities untouched.

Reviewer items still open from v2.0: (3) conjunct-(j)/1072 merge-time interplay
(1072 remains unapplied — the note now describes a live production state);
(4) grant posture (revoked; standing-grant question still the native's);
(5) the secret-echo disclosure.
**Step-5 harness fix — DISPOSED 2026-09-27 (ADK-0013, this lane):**
`test_wp10_cutover.py` `clear_tables` now declared `text[]` (production's real
type); step-5 rehearsal applies the corrected numbered migration 1091 (`'{...}'`
form) instead of the preparation copy; new negative check
`test_step05_preparation_copy_malformed_literal_now_fails` proves the fixed
harness catches the original `'[...]'` defect (`malformed array literal`
raised). The fidelity fix also exposed a second latent defect the old harness
hid: `step05_reversal.sql`'s text→text[] restore would fail against production —
the (never-applied) reversal script now parses the snapshot's text form back to
`text[]`, with a comment. Re-run on a fresh disposable DB: **17 passed**
(16 original + 1 negative check); container torn down.
Nothing marked REVIEWED.
