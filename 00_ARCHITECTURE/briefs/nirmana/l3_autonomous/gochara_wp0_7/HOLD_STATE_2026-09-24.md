---
artifact: HOLD_STATE
version: 1.0
date: 2026-09-24
branch: l3/gochara-autonomous-wp0-7
status: HELD — awaiting consolidation merge; do not resume without explicit release
---

<!-- Changelog: amended 2026-09-26 on native review — added "Migration-ledger gap
     (owed backfill)" section (docs-only verification, read-only production probes,
     zero production writes) and corrected the "Security follow-up" line from
     repository-scope to transcript-scope. No other content changed. -->

# HOLD STATE — Gochara WP0-7 session (2026-09-24)

Held per native HOLD REQUEST of 2026-09-24 for the layer-wide consolidation merge.
This branch must not move until released.

## Where the campaign stopped

- §12 delta of `briefs/GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md`: 12.5, 12.3 (4.13a–i),
  12.4 DONE and pushed. 12.9 and 12.10a/12.10b DONE by the parallel L3 session on this
  same branch. 12.10c is merge-time work for whoever merges second.
- WP10 §7.A rehearsal: GREEN (16/16, re-verified).
- WP10 §7.B tranche 1 (production): **COMPLETE, GREEN** — steps 0, 1, 3, 4, 5 green;
  step 2 restore-drill honestly NOT_RUN (no dump locally).
- WP10 §7.C tranche 2: **ENTERED under the native ruling of 2026-09-24 ("Approved on
  point number two. Go ahead to everything."), then HALTED at step 6 — E-018.**
  Steps 6–10 NOT RUN.

## Production surface — frozen by the hold

Migrations applied to production this campaign: **1080, 1081, 1082, 1083, 1084, 1087,
1091**. 1084 applied as committed (the `ka_kshetra→ka_gochara` edge deliberately held
out per K-1). 1085 is RETIRED (E-010, `G9_DISPOSITION_v1_0.md`) — never apply it.
1086 was renamed to the L1 lane (`l1_…`). Generations `v1=38287` and `3.0=1830`
untouched; both chart authorities remain `'3.0'`; century writer `is_active=false`;
no `'4.0'` rows exist. Registry re-pin (1091) is live. No temporary grants outstanding
(the step-3 CREATE grant to `amjis_app` was revoked and verified revoked).

**Per the hold: apply NO further migrations. The §12.9 staleness gate on production
overlays (135/135 + 72/72 and 132/132 + 71/71 rows with NULL upstream_fingerprint,
0 mismatched) is RED BY DESIGN — do not weaken, bypass, or re-scope it.**

## Migration-ledger gap (owed backfill)

Added 2026-09-26, docs-only amendment: verified from primary sources (production
probes were read-only `SELECT`s via `amjis_app` over the cloud-sql-proxy on
127.0.0.1:5433; zero production writes).

**The gap.** The eight campaign migrations were applied through
`00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/apply_migration.sh` (or the
step04/direct-`psql -f` machinery), which runs raw `psql -f` (lines 17, 22, 27) and
**never writes `_migrations_applied`** (grep count of `_migrations_applied` in the
script: 0). The ledger writer is `platform/scripts/migrate.ts`
(`INSERT INTO _migrations_applied` per applied file), which these applies bypassed.
Application commits: `5ee6280bd` (1082/1083/1084/1087, step-4 E-016 scope) and the
tranche-1 apply commits for 1080/1081/1091. Verified against production: **zero
rows** in `_migrations_applied` for each of the eight — by filename
(`filename ~ '^(1080|1081|1082|1083|1084|1086|1087|1091)_'` → 0 rows), by sha256,
and by sql_identity (both hash sets → 0 rows). Ledger schema (needed for backfill):
`_migrations_applied(id serial, filename text unique, applied_at timestamptz,
sha256 text, sql_identity text)`; 869 rows present, highest applied id 871
(filename `1079_…`).

**Structural liveness — each effect probed live in production:**

| File | Verified-live effect | Probe |
|---|---|---|
| 1080 | `gochara_resonance_map.target_resolution_state`, `target_qualifier` | `information_schema.columns` → both present |
| 1081 | tables `kala_gochara_convention`/`kala_gochara_publication`/`kala_gochara_coverage` + trigger `kala_gochara_convention_immutable` | `to_regclass` ×3 + `pg_trigger` → all present |
| 1082 | `kala_vedha_gochara.source_qualification`/`precision_regime`; `kala_moorti_nirnaya.source_qualification`/`precision_regime`/`upstream_fingerprint` | `information_schema.columns` → all present |
| 1083 | `brahma_prospective_ledger.contact_id`, `mimamsa_predictions.contact_id` | `information_schema.columns` → both present |
| 1084 | `asset_registry.depends_on @> ARRAY['ka_vedha_gochara']` for `ka_kshetra` and `ka_sangam` | probe → both `t` |
| 1087 | `kala_gochara_contacts` at 41 columns (incl. `inclusivity`, `tier_basis`) | `information_schema.columns` count → 41 |
| 1091 | `ka_gochara.count_sql` re-scoped to `generation='4.0'`; `clear_tables` text[] on both rows; snapshot table `kala_gochara_cutover_step05_snapshot` | direct row reads + `to_regclass` → all as committed |

**1086 — ambiguous case, NOT cleanly applied.** Current filename:
`1086_nirmana_l1_gochara_g10_ga_strength_contributor_digest_spec.sql`
(`platform/migrations/`; renamed into the L1 lane by name only, number kept).
Its two declared spec hashes: retire `3743484c…b07a`, insert
`52a0d253…7a97`. Production `asset_output_digest_specs` for `ga_strength`: the OLD
spec `3743484c…b07a` is still **active** (`retired_at IS NULL`) and the new spec
`52a0d253…7a97` is **absent** (the one other row, `7251b119…77c3`, is retired
pre-history). So production matches 1086's PRE-state: the migration never ran here.
**It must not be recorded as cleanly applied** — its backfill triple is listed only
for completeness; the L1 lane owns its disposition.

**Per-file idempotency (verified from the committed SQL):**

- 1080, 1082, 1083: `ADD COLUMN IF NOT EXISTS` + `COMMENT ON COLUMN` only; no
  INSERT/UPDATE/DELETE/CREATE — safely re-appliable.
- 1081: all `CREATE … IF NOT EXISTS` / `CREATE OR REPLACE FUNCTION` /
  `DROP TRIGGER IF EXISTS` + `CREATE TRIGGER` — safely re-appliable.
- 1084: both UPDATEs guarded by `AND NOT (depends_on @> ARRAY['ka_vedha_gochara'])`
  (verified in the committed file); the `ka_kshetra→ka_gochara` edge is deliberately
  absent per K-1 — safely re-appliable (no-op).
- 1087: `ADD COLUMN IF NOT EXISTS`; every constraint is `DROP CONSTRAINT IF EXISTS`
  then `ADD CONSTRAINT` — safely re-appliable.
- 1091: snapshot `CREATE TABLE IF NOT EXISTS` + `INSERT … ON CONFLICT DO NOTHING`;
  plain re-runnable UPDATEs; DO gate passes on the live state — safely re-appliable.
- 1086: guarded DO block + `ON CONFLICT DO NOTHING` — idempotent, but NOT APPLIED
  (see above); do not backfill as applied.

**Backfill triples (filename, sha256 of file bytes, sql_identity per
`migrate.ts` `sqlIdentityOf`):**

- `1080_nirmana_l3_gochara_resonance_target_resolution_state.sql` | `a1e0b3aec7f826cf3e0cb3a5f665f109990b7121181f0c43db6e13d51acb9afb` | `5064a3d2e7437ca325ce2e76d94b32b579fd4f202a269371fcb3a14ab2f13656`
- `1081_nirmana_l3_gochara_ledger_coverage_publication.sql` | `2e9f8724e43c9e347024150c47a4d5e2e3809fff28ffe20e98923c28e4595a96` | `f8c61881642007b3673ce4365da6330923a803c22ca472eaef4e2fdcb41b74e2`
- `1082_nirmana_l3_vedha_moorti_stamp_columns.sql` | `2656ee32d4b672e4a611f96e670206576e0bf153293b17121be115b00878bfa3` | `978f52ca8f9c516af0da84977116e89738d73fbd7b69ec15501fbc3bf2b91d85`
- `1083_l5_ledger_contact_id.sql` | `61a652e23a1a15c4e7f34b24112575e68e75d65393417f17752971d1b0df79e8` | `7dc9a24e9755aa8f5a45cb384a60f180044a90fd9bc04f300eb75405a5424c2c`
- `1084_wp7_k1_v1_registry_edges.sql` | `f349e26a0c9fb8ad5cc77a8c1c4456b8f3ee35d100e9b0689691f2f7660f560c` | `2d921b6aff07069b3a5fab49bec7b63352c1650ccb7bcdc6fb21304eed8148f9`
- `1086_nirmana_l1_gochara_g10_ga_strength_contributor_digest_spec.sql` | `4494419206050cdea3df63061fcfe07bad39329b8e92a4b005bec267c86eebf2` | `38df2b11e50a559265212559e1939dd51bbdda43b547754bb8fff2aef01aea38` — **NOT APPLIED; excluded from any backfill**
- `1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis.sql` | `de8e5dfc0171d9c4aa700852c5254cf15d3796247742508c1450cd10e4ffbdda` | `ff49af900a968993aee5428a54f942318f25d8094cc8fbb4515d8cf9f48e0dc9`
- `1091_wp10_ka_gochara_registry_repin.sql` | `5514a5406a0fc74a80e33ba9a5d22d6e5933e5aa755f6a2df4bad47a29495030` | `125abe90de0cf35e9968c9af88b746699e76dab0eb42f70002494cdd3de0389c`

**The backfill is a PRODUCTION WRITE and therefore a native escalation (Part 5 hard
stop)** — owed for the seven applied files (1080, 1081, 1082, 1083, 1084, 1087,
1091), with the triples above ready. It was NOT performed by this session. Until it
lands, `migrate.ts` treats the seven as unapplied: any runner invocation would
attempt re-apply (safe per the idempotency verification above, but a write) — keep
the runner out of production until the native rules.

## Open gates / escalations awaiting the native

- **E-018** (blocks 7.C): (1) §12.9 gate RED on production — the prescribed overlay
  rebuild rewrites live-served rows and must be its own reviewed change; (2) the step-6
  episode-enumeration driver (`--episodes-json`/`--coverage-json`) does not exist —
  it is the '4.0' writer's core and must not be improvised; (3) **E-012** still in
  force: no windows projection writer, so step 7's `windows_present` gate is RED by
  design and the authority flip is physically unreachable.
- **E-016 resolved** (1082–1084/1087 applied under the ruling); **E-017 resolved**
  (corrected 1091 applied; defect was `'[...]'` vs `text[]`, root-caused to a
  rehearsal-harness fidelity gap — rehearsal declared the column TEXT).
- **Security follow-up (native ops call):** four secrets were echoed to a **session
  transcript** early in the E-015 work (`nirmana-campaign-control-db-password`,
  `nirmana-evidence-ingress-db-password`, `retrieval-census-ro-db-password`,
  `amjis-inquiry-db-password`) — the exposure is **transcript-scope, not
  repository-scope**. Verified 2026-09-26 that no secret *values* were committed to
  git: branch-wide `git grep` for the four secret names and for literal password
  assignments finds only name/version references (e.g. `deploy.yml`
  `DB_PASSWORD=amjis-db-password:3` pins) and the intentional fakes under
  `platform/scripts/governance/secret_scan_fixtures/fail/`. Rotation remains a native
  action, unrotated; precedent:
  `00_ARCHITECTURE/briefs/samapti/SAMAPTI_SECURITY_INCIDENT_DB_CREDENTIAL_v1_0.md`.
- Review requests in `wp7_packets/` (12.3, 12.4, 12.5, 7.B v2.1, 7.C v1.0) are all
  IMPLEMENTED_AWAITING_REVIEW / STOPPED_AWAITING_NATIVE — **nothing marked REVIEWED**.
  O-2 (K3 review) belongs to the native's session.

## What a merger needs to know that is not obvious from the diff

- PR **#2731** targets `main` and carries P-1, WP9 §5.2, N-19, and all §12 work.
  The 7.C merge-state preconditions were **ruled satisfied by the native's verbal
  ruling** (recorded in ESCALATIONS.md and the step-4/5/6 evidence) — the consolidation
  merge itself now satisfies them literally.
- 12.10c merge hygiene: whoever merges second regenerates `nirmana-writer-digests.json`,
  re-admits the L3 pin, and regenerates `capability_estate_census.json` under
  `NATIVE-2026-09-24-L0-REPAIR-REPIN`.
- The step04 APPLY_SET machinery has a REFUSED-migrations guard (1085/1086) that exits 3 —
  do not "fix" it by re-adding those numbers.
- Migration numbering: 1088–1090 belong to the Saṅgam stream; 1091 is ours (registry
  re-pin). Next free number requires a fresh cross-branch scan + `npm run guard:migration-numbers`.
- A `cloud-sql-proxy` (`madhav-astrology:asia-south1:amjis-postgres --port=5433`) was left
  running on the workstation for native use; log `/tmp/cloud-sql-proxy-5433.log`.
  Both disposable rehearsal DB containers were torn down; both temp password files shredded.
- Session close for the pre-tranche phase: `SESSION_CLOSE_WP07_REMAINDER_v1_1.yaml`
  (schema_validator exit 0). A supplementary close note for the tranche phase is due
  when the hold is released and the campaign actually ends — none written now because
  the campaign is held, not closed.
