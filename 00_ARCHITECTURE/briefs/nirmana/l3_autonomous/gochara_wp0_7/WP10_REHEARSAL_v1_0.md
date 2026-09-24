---
artifact: WP10_REHEARSAL
version: 1.0
status: EVIDENCE
sheet_item: GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §7.A
---

# WP10 — cutover-prep rehearsal (runbook as runnable artifacts)

Sheet item (§7.A): prepare the WP10 migration/cutover runbook
(`GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md` §9, steps 0–10) as runnable artifacts
and rehearse them against a disposable database. Nothing in this artifact was
run against a shared or production database; both tranche flags
(`PRODUCTION_TRANCHE_1_AUTHORIZED`, `PRODUCTION_TRANCHE_2_AUTHORIZED`) are
`false` in the brief frontmatter and remained so.

**Artifacts:** `platform/python-sidecar/scripts/kala_gochara_cutover/`
(steps 0–10 + `common.py` + evidence templates per step) and the rehearsal
gate `platform/python-sidecar/tests/l3/gochara/test_wp10_cutover.py`
(14 tests).

## Production-identification convention

`common.py::refuse_production` treats a DSN as production when the port is
5433 (the Cloud SQL proxy production port used across this repo's runbooks)
or the host is not loopback. Any such DSN exits 4 with `REFUSED` unless the
matching tranche env flag is exactly `"true"` (steps 0–5 → tranche 1,
steps 6–10 → tranche 2). The guard runs before any other failure mode in
every entry point (verified: refusal wins over a missing `--dump`).

## Rehearsal environment

Disposable Postgres 16 (`gochara-wp10-disposable`, localhost:55434, DSN
`postgresql://wp6:disposable@localhost:55434/wp6`, overridable via
`GOCHARA_REMAINDER_DSN`), stripped-down synthetic schema: windows
(460 + 527 generation + 556 era_slice_key), `kala_gochara_windows_v2`,
`kala_gochara_v2_build_state`, `kala_gochara_authority`,
`build_protected_assets`, `asset_registry`, `asset_output_digest_specs`,
overlay/consumer stubs, and the real-named archive table
`kala_gochara_windows_archive_20260805` (shape pinned by migration 670).
Seeded chart A with 3 `v1` + 2 `3.0` windows. The container is torn down at
closure; WP6's `gochara-wp6-disposable` (55433) left as found.

## Per-step outcome

| Step | Artifact | Rehearsal outcome |
|---|---|---|
| 0 | `step00_clear_guard.md` | **NOT_RUN** — cherry-pick instruction referencing `origin/l3/kala-p1-1-b1-clear-guard` head `eb00da67d` (never re-implemented); its gate is the TS route test, outside the disposable-DB scope |
| 1 | `step01_select_grant.sql` | **GREEN** — GRANT SELECT on `kala_gochara_windows` + `kala_gochara_windows_archive_20260805` to `data_plane_builder`; DO gate probes pass; REVOKE reversal documented |
| 2 | `step02_restore_drill.py` | **NOT_RUN** (by design) — no 2026-08-23 dump is available locally; the script exits 3 without `--dump` and carries the 38,287-row digest + 2,667 uncovered-id gates for tranche time |
| 3 | `step03_guard_n6a.sql` + `step03_reversal.sql` | **GREEN** — `kala_gochara_generation_guard()` refuses DELETE/UPDATE on `v1`/`3.0`, re-label into them, and TRUNCATE over protected rows (GUC override `app.allow_protected_sweep_rewrite=on`); build_protected_assets re-seed + century `is_active=false`; reversal restores and deliberately keeps re-seed rows |
| 4 | `step04_apply_verify.py` | **GREEN** — applies migrations 1080–1086 (1085 split at the `-- DOWN (manual rollback):` marker) and verifies information_schema columns/tables/trigger/indexes; idempotent across two runs |
| 5 | `step05_registry_repin.sql` + `step05_reversal.sql` | **GREEN** — ka_gochara re-pin (count_sql → `kala_gochara_windows … generation='4.0'`, 3-relation clear_tables display with the F-24 caveat, 8 depends_on, century clear_tables `[kala_gochara_windows, kala_gochara_windows_v2]`); conjuncts (a)–(k) re-scoped per plan §6.3, green on the fixture, red on an injected `2.0` window (conjunct f) and on authority `4.%` without a published manifest (conjunct k); snapshot-table reversal restores. The step is deliberately **unnumbered** (no migration number in the filename) — the number is assigned at tranche-1 start after the E-009 re-scan |
| 6 | `step06_candidate_build.py` | **GREEN** — ledger lifecycle on the candidate: register_convention → publish_candidate (input generation vector recorded: linear_no_box, moon separate, nodal_drishti removed, sade_sati testimony, kakshya_bindu_interim, orb_max_deg 5.0 M-1 fallback) → write_contacts/write_coverage; rebuild after publication refused with exit 6 per plan §4.7 |
| 7 | `step07_flip_gates.py` | **GREEN** — gates 1/2 (manifest ↔ coverage ↔ windows consistency) pass on the built candidate; gate 3 **NOT_RUN** (TS-only, outside this substrate); gate 4 rehearses rollback on a scratch generation `4.0-gate4-scratch` and cleans it up |
| 8 | `step08_flip.py` | **GREEN** — preconditions self-checked; ledger.publish + authority upsert with `evidence_ref=manifest_id`, `flipped_by` required; conjunct (k) red before the manifest exists and green after; `--reverse` rolls the ledger back and returns the authority to `3.0` |
| 9 | `step09_soak_checklist.md` | **GREEN** — soak checklist plus the #2534 birth-epoch detector exercised against the synthetic fixture (positive and negative chart) |
| 10 | `step10_n11_disposition.sql` | **GREEN** — refuses without `SET app.n11_ruling_ref` (N-11 is a native ruling); with the GUC, deletes `kala_gochara_windows_v2 WHERE generation='2.0'` + build_state `2.0` only (the `g3_utkarsha` and `v1` surfaces untouched) and retires digest 1018 sha `ac32bdd3…c596` via `retired_at` |

## Test gate

`test_wp10_cutover.py` — 14/14 passed on the disposable DB. Full
`tests/l3/gochara/` battery after landing: **266 passed** (252 at the
remainder-final-report baseline + these 14).

## NOT_RUN reasons (carried to tranche time)

- **Step 0:** cherry-pick + TS route test; nothing to rehearse on Postgres.
- **Step 2:** restore drill needs the real 2026-08-23 dump; the digest and
  gap-count gates are coded but unexercised against real bytes.
- **Step 7 gate 3:** serving-layer TS route gate; rehearsed only as a
  documented NOT_RUN.

## Standing-order acknowledgment

Every step's evidence template under
`platform/python-sidecar/scripts/kala_gochara_cutover/evidence/` opens with
the standing-order acknowledgment: merge lands code only; no builds run under
the 2026-08-21 standing order; the production instance is refused unless the
brief's tranche flag is `"true"`.
