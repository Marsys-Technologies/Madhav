# D6 plan: create the node-series unique index on `ephemeris_daily` (migration 1227's DDL, owner path)

Status: DESIGNED, NOT RUN. For SS hash review. Nothing here has touched production; the executor has only ever run against a
disposable local PostgreSQL (39 tests). Never run without SS approval of the plan hash.

## Why an owner path (finding, 2026-10-02)
- `ephemeris_daily` is owned by `amjis_app` (read as `suvarna_reader`), 825,084 rows, 494 MB with indexes.
- The routine migration login is `amjis_app` (`PROD_DATABASE_URL`, `platform/scripts/validate-migration-database-routes.ts:12`). It owns the table
  but holds USAGE only on schema `public` (`has_schema_privilege('amjis_app','public','CREATE') = false`; schema owner `data_plane_schema_owner`).
- PostgreSQL requires CREATE on the schema for `CREATE INDEX` and for `ALTER TABLE ... ADD CONSTRAINT UNIQUE` alike. Reproduced on a disposable
  PostgreSQL 15 with the live topology: both fail with `permission denied for schema public`
  (`platform/python-sidecar/tests/test_ephemeris_node_index_1227_sql.py::test_amjis_app_owns_the_table_but_cannot_create_an_index_or_a_unique_constraint`).
- So a plain migration 1227 cannot apply in production. The index is created here; migration 1227 then verifies it (schema-of-record, no DDL).

## What changes
Exactly one new index: `ephemeris_daily_date_body_ayanamsha_node_mode_uq` = UNIQUE btree `(date, body, ayanamsha_id, node_mode) NULLS NOT DISTINCT`.
No data, column, constraint, grant, owner or policy changes. The old key `ephemeris_daily_date_body_ayanamsha_id_key` stays until migration 1250.
The DDL is the text of `platform/migrations/1227_ephemeris_daily_node_series_unique_index.sql` itself (guards + structure verification included);
the plan hash binds that file's sha256.

## Lock and writers
`CREATE UNIQUE INDEX` (not CONCURRENTLY: one transaction) takes SHARE on the table: reads proceed, writes wait. The only writers are the L0 `bg_ephemeris`
rebuild and `scripts/build_ephemeris_1900_2150.py`. Measured on a disposable PG 15 with 825,084 rows: about 0.35 s. `lock_timeout 5s`, `statement_timeout 120s`.
Pre-check P6 refuses if another backend holds a write-level lock on the table (a rebuild in flight), and `run_gated.sh` refuses unless no deploy-workflow run
on `main` is non-completed and no `build_runs` row is planned/running/paused.

## Mechanism (same as `ChartGrants/cg_exec.py`)
The Cloud SQL admin (`postgres`, CREATEROLE, not superuser; proxy `127.0.0.1:5433`, secret read in-process, never printed) becomes a TRANSIENT member of `amjis_app`
(ownership of the table) and `data_plane_schema_owner` (CREATE on `public`) inside ONE transaction, runs the DDL, and `REVOKE`s exactly what it granted before the
post-snapshot. Proved on PostgreSQL 15 with a CREATEROLE-only admin (`tests/test_node_index_exec.py`); on PostgreSQL >= 16 a CREATEROLE-only admin cannot grant an arbitrary
role (live is 15.18).

## Checks (any failure: no DDL, ROLLBACK)
Pre: P1 PG >= 15; P2 table owner = `amjis_app`; P3 index name free; P4 old key present exactly as `UNIQUE (date, body, ayanamsha_id)`; P5 zero `node_mode='mean'` rows;
P6 no foreign write-level lock on the table. Check E (apply only): `--expect-evidence` equals the digest of the PRE-DDL state computed in this transaction.
Post (commit only if all): relacl + owner of every public relation, public schema owner + ACL, RLS flags, policies and `pg_auth_members` equal snapshot A; the index
catalog differs by exactly `+ephemeris_daily_date_body_ayanamsha_node_mode_uq`; the constraint catalog is equal; row count, an order-free hash of every row and the mean-row
count are equal; the index is unique, valid, ready, btree, NULLS NOT DISTINCT, on the four columns in order with default operator classes and collations.

## How to run (SS approves the hash first)
```bash
D=00_ARCHITECTURE/briefs/suvarna/exec/node_series/d6_index
python3 $D/make_plan.py                                  # offline: prints the hashes (no database)
$D/run_gated.sh --dry-run                                # gate (both counts 0) -> executor; always rolls back; prints plan hash + evidence digest
$D/run_gated.sh --apply --expect-plan <plan hash> --expect-evidence <digest the dry run printed>
```
Evidence (before snapshot, reversal SQL, SHA256SUMS; 0700/0600) is written to `/Users/Dev/suvarna-evidence/NodeSeries/d6_index/<UTC ts>/` BEFORE the DDL; if it cannot be
written the run aborts. After a commit, verify read-only as `suvarna_reader` with the structure query in the header of migration 1227.

## Reversal
`reversal.sql` (in the evidence directory): `DROP INDEX public.ephemeris_daily_date_body_ayanamsha_node_mode_uq;` through the same owner path, and only while no writer
relies on the new key (before 1228, the writer change and 1250). After 1250 the new index is the only uniqueness guard and must stay.

## Order relative to the migration PR
1. SS approves the plan hash; the dry run is read; the apply commits; verify by structure.
2. THEN the migration PR (1227) may merge: at the next deploy it finds the index, verifies it, records itself applied. Merged earlier, it fails closed
   (`has no CREATE on schema public`), fails the deploy's migrate job and holds back every later pending migration.

## Hashes (pinned by a test; re-run `make_plan.py --write` after any edit)
- plan hash: `f7bfd19febaf988355101dd1454cc3697b075b22732e028f1477f08600999697`
- executor sha256: `52b2061f92dd36b6d413d37d722fe39748609777c530379040dc1f445a7a7dfc`
- migration 1227 sha256: `0387da94dd7e7efc56afb5f0427e0007658e36bf45669e95bdf077c110fedd8e`

## What the dry run can and cannot show
It runs every check and the real DDL against production inside a transaction that is then rolled back (the index build holds SHARE for the build's duration, ~seconds).
It cannot show how the committed index behaves under a concurrent writer (none should run: the gate and P6). It does not prove the apply-time state equals the dry-run state:
check E refuses an apply whose pre-DDL state differs from the dry run's.
