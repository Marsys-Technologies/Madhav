# E5.6 rehearsal environment — phase 1: the off-production PostgreSQL cluster

Suvarṇa Track E, item E5.6 (brief §7). A **local** PostgreSQL 15 cluster, run as the current OS user,
loopback only, used to rehearse waves, the F-3 proof and the E5.7 L0 rebuild drill without ever touching
production. **No production dump, no production credential, no production connection** is involved in
phase 1; seeding (via `suvarna_reader`) is a later phase and is not done here.

| | |
|---|---|
| Binaries | `/opt/homebrew/opt/postgresql@15/bin` (15.17; CI/production pin 15.x — `ci.yml` uses `postgres:15.18`) |
| Data dir | `/Users/Dev/suvarna/rehearsal/pg` — **outside the repo, never committed** |
| Listen | `127.0.0.1:55432` only (`listen_addresses='127.0.0.1'`), socket in `/Users/Dev/suvarna/rehearsal/sock` |
| Auth | `trust` on the owner-only unix socket and on `127.0.0.1/32` only (no password, no other rule) |
| Superuser | the current OS user (`Dev`); database `rehearsal` |
| Extensions | `pgcrypto`, `uuid-ossp`, `vector` (pgvector, Homebrew), `pg_trgm` |
| Local stand-in roles | `amjis_app`, `data_plane_builder`, `purna_inquiry_owner`, `service_role`, `anon`, `authenticated` — `NOLOGIN`, no password, no privileges (the migrations reference them) |
| Tuning | `fsync=off`, `synchronous_commit=off`, `shared_buffers=512MB` — a disposable cluster; **never** copy these to anything durable |

## Commands (all verified 2026-10-02 at origin/main `bf6fe712b`)

```bash
cd /Users/Dev/suvarna-engine-lane-e5-6/platform/scripts/governance/rehearsal   # or your worktree's copy

./rehearsal_cluster.sh init      # idempotent: initdb (first time only) + start + create db + extensions + roles
./rehearsal_cluster.sh start     # idempotent
./rehearsal_cluster.sh status    # data dir, port, version, state, live server_addr/port, table count
./rehearsal_cluster.sh url       # postgresql://Dev@127.0.0.1:55432/rehearsal
./rehearsal_cluster.sh stop      # idempotent (fast shutdown)
./rehearsal_cluster.sh reset --yes   # DESTROYS the cluster's data dir and re-inits. Refuses without --yes.

./apply_schema.sh replay         # baseline + best-effort replay of every migration file (see below); exit 3 if any file fails
./apply_schema.sh verify         # ledger sha256 vs files on disk; public base-table count
./apply_schema.sh migrate --dry-run   # the repo's real runner (migrate.ts) against the rehearsal URL only
```

Every PostgreSQL / Node / Python child process is started with `env -i` and an explicit environment
(`PATH`, `HOME`, and for the runner only `DATABASE_URL`). Nothing is inherited, so `PG*`, `DATABASE_URL`
or a sourced credential file in the calling shell can never redirect a command. Do not `source` any
`pgenv`/`dbenv` file in the shell you use for these scripts.

## The URL guard

`rehearsal_guard.py::check_rehearsal_url` is the single decision point. `apply_schema.sh` and
`replay_schema.py` both call it **before any process receives the URL**, then verify the live server
(`inet_server_port()`, `current_database()`, `data_directory` must equal 55432 / `rehearsal*` /
`/Users/Dev/suvarna/rehearsal/pg`). It refuses: empty URLs; any host other than `localhost` /
`127.0.0.1` (no IPv6, no `0.0.0.0`, no multi-host, no unix-socket paths); any port other than 55432 (a
missing port is refused); any database other than `rehearsal` / `rehearsal_<suffix>`; a password in the
URL; any libpq override (`host=`, `hostaddr=`, `port=`, `service=`, ...; only `application_name` is
allowed); and any URL containing a production-like marker (`cloudsql`, `amjis`, `supabase`, `prod`, ...).
`__tests__/test_e5_6_rehearsal_guard.py` proves each refusal and a mutation (guard disabled) that fails
the same table (56 tests; 48 fail when the guard is disabled). The shell-level tests substitute a stub
`psql`, so even a broken guard cannot open a connection from the test.

```bash
python -m pytest platform/scripts/governance/__tests__/test_e5_6_rehearsal_guard.py -q
```

## Schema: what `migrate.ts` can and cannot do on an empty database

**`migrate.ts` cannot bootstrap an empty database.** This is a known, parked finding
(`.github/workflows/fresh_chart_smoke.yml` header; `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/
INHERITED_EMPTY_BOOTSTRAP_FINDING_v1.json`, PA-R10): `0000_seed_legacy_applied.sql` /
`0000b_seed_legacy_v2.sql` mark ~87 foundational migrations as applied without executing them, the
squashed `0001_brahma_baseline.sql` is not valid through the `pg` driver, and `1035`/`1036` (data-plane)
and `1153`-`1157`/`1202` (public-schema) are refused by the general runner by design. CI therefore starts
from a production `pg_dump --schema-only`; **that is not permitted here** (no production access, no dump).

`apply_schema.sh replay` is the bounded, non-invasive substitute (`replay_schema.py`; it edits no migration
and does not touch the runner): the baseline through psql (stream-rewriting only `CREATE SCHEMA public;`
to `IF NOT EXISTS`), the runner's own `_migrations_applied` tracker, the two seed files recorded as
applied-**not**-executed, then every other file in `migrate.ts`'s own order (numeric prefix + its two
closed repairs) through psql to a fixed point (a failed file is retried after the rest ran). Each success
is recorded with the exact sha256 `migrate.ts` computes. The report goes to
`/Users/Dev/suvarna/rehearsal/replay_report.json`. It is idempotent: a second run applied 0 and left the
same 126 failures.

**Result at origin/main `bf6fe712b`:** 883 migration files on disk; 757 applied and recorded (754
executed + baseline + 2 seeds), **126 fail**, 362 public base tables, 0 sha256 mismatches between the
ledger and the files, 0 ledger rows without a file. The 126 failures, by class:

| class | files | meaning |
|---|---|---|
| contract guard vs registry content | 38 | `refuses unknown ... registry contract`, DAG-edge, `has_writer` and count sanity checks: the replay's `asset_registry` has 93 rows (production has 128 active), because the legacy generation inserts them in an order that cannot be reproduced |
| FK: registry / digest-spec rows missing | 35 | `asset_output_digest_specs_asset_id_fkey` etc., same root cause |
| schema / object ordering | 30 | the PA-R10 conflict: `158_classical_texts_schema.sql` creates `classical_texts(text_key)` before `ws2_l0_texts.sql` (which owns `classical_texts(text_id)` + `classical_text_chunks`), so **`classical_text_chunks`, `bg_transit_rules`, `gochara_resonance_map`, `remedy_review_queue` and the `brahma_mimamsa_*` extensions do not exist** |
| role-gated | 12 | `E1035/E1036_WRONG_ACTOR`, `must run as nirmana_migrator`, `purna_inquiry_owner` temporary-membership checks, `amjis_app` grant preflights: they require production's role topology and attested actors |
| other | 11 | NOT NULL / registry-shape mismatches in the legacy registry inserts |

Consequence: the schema is **a faithful catalog for foreign keys, tables and most of the L1-L5 DDL**
(the E5.9 closure below reproduces the brief's measured numbers), but it is **not** a complete production
replica, and the L0 text tables are missing (see E5.7 notes). Closing this is a separately chartered
baseline rebuild (PA-R10 `required_follow_up`), not phase-1 work. `apply_schema.sh migrate --dry-run`
stops at the first pending protected migration (`1035`), exactly as production's runner does; after a
future baseline repair the same command applies increments.

## E5.9 SQL on the real catalog (verification the E5.9 PR still needed)

`fk_edges_from_catalog` and `tables_from_catalog` from `suvarna_level_wave.py` (branch
`suvarna/engine-E5.9`, run from a scratch copy) were run against this cluster through psycopg 3
(`env -i`, explicit host/port/dbname). Both SQL statements run unchanged on PostgreSQL 15.17 (192 FK
edges, 362 tables, no partition clones, no error). `transitive_footprint(['public.bodha_msr_signals'])`:
status `COMPLETE`, 3 FKs into the table (all `CASCADE`) from 2 tables — `bodha_contradictions` (x2) and
`bodha_signal_embeddings` — because migration `1214` (F-3, drop the five `kala_*` FKs) is already in the
replayed history. To check the pre-F-3 shape, the five constraints were re-added **inside a transaction
that was rolled back**: 8 FKs from 7 tables, closure of 12 cascade tables (the two bodha tables, the
five kala tables, `phala_anchors` and its four children), which is the brief's 2026-09-30 measurement.
`kala_convergence` and `phala_anchors` closures also match §4a (cascades and `SET NULL` lists identical).

## Safety summary

* Binds `127.0.0.1:55432` only; trust auth is reachable only from this machine's loopback/socket.
* No production dump, credential, URL, or environment variable is read, copied or referenced.
* `reset --yes` deletes only the literal path `/Users/Dev/suvarna/rehearsal/pg`.
* `init` twice is a no-op; `replay` twice is a no-op; `stop`/`start` are idempotent.
* Disposable by design (`fsync=off`): never place anything of value here.
