# E5.6 rehearsal environment — phase 1: the off-production PostgreSQL cluster

Suvarṇa Track E, item E5.6 (brief §7). A **local** PostgreSQL 15 cluster, run as the current OS user,
loopback only, used to rehearse waves, the F-3 proof and the E5.7 L0 rebuild drill without ever touching
production. **No production dump, no production credential, no production connection** is involved in
phase 1; seeding (via `suvarna_reader`) is a later phase and is not done here.

| | |
|---|---|
| Binaries | `/opt/homebrew/opt/postgresql@15/bin` (15.17; CI/production pin 15.x — `ci.yml` uses `postgres:15.18`) |
| Data dir | `/Users/Dev/suvarna/rehearsal/pg` — **outside the repo, never committed** |
| Listen | `127.0.0.1:55432` only (`listen_addresses='127.0.0.1'`); unix socket in `/Users/Dev/suvarna/rehearsal/sock` (directory `0700`, `unix_socket_permissions = 0700`, `unix_socket_group = ''`) |
| Auth | `trust` on the unix socket (reachable only by the owner: mode 0700) and on `127.0.0.1/32` (reachable by **any local process of any local user**); no password, no other rule. **Accepted residual:** anything running on this machine can connect over loopback as superuser `Dev`, and a superuser can run programs as `Dev` (`COPY ... PROGRAM`). Tolerated only because the cluster is disposable, holds no production data and no secrets, and the machine is single-user; do not run it on a shared host. |
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

Every PostgreSQL / Node / Python child process is started with `env -i`, an explicit environment and a
**private empty `HOME`** (a fresh temp dir, so no `~/.pgpass`, `~/.pg_service.conf` or `~/.psqlrc`;
`PGPASSFILE`/`PGSERVICEFILE` point at nonexistent files inside it). `psql` alone gets
`PGOPTIONS=-c client_min_messages=warning`; the migration runner gets only `PATH`, `HOME` and
`DATABASE_URL`. Nothing else is inherited, so `PG*`, `DATABASE_URL` or a sourced credential file in the
calling shell can never redirect a command. Do not `source` any
`pgenv`/`dbenv` file in the shell you use for these scripts.

## The URL guard

`rehearsal_guard.py` is the single decision point. `apply_schema.sh` and `replay_schema.py` call it
**before any process receives the URL**, and from then on use only the **normalised URL it returns**
(rebuilt from validated components), never the original string. Rules (exact text, nothing fuzzy):
no whitespace/control character/backslash anywhere; lower-case `postgres`/`postgresql` scheme; at most one
`@`, a plain user name, **no password**; the host is exactly `127.0.0.1` (`localhost` is refused: it can
resolve to `::1`, which an ssh tunnel or another listener could own; so are `127.1`, decimal/hex/octal,
IPv6 and `%`-encoded spellings); the port is exactly `55432`; the database fullmatches `rehearsal` or
`rehearsal_<suffix>`; the only query parameter is one `application_name` (`host=`, `hostaddr=`, `port=`,
`service=`, `sslmode=`, `options=`, any case or `%`-encoding, is refused); and no production-like marker
(`cloudsql`, `amjis`, `supabase`, `prod`, ...). After that the live server is verified
(`inet_server_port()`, `current_database()`, `data_directory` = 55432 / `rehearsal*` /
`/Users/Dev/suvarna/rehearsal/pg`); `rehearsal_cluster.sh` also verifies `inet_server_addr()` before every
statement.

`replay_schema.py` additionally **refuses to execute** (`REFUSED_UNSAFE` in the report, exit 3) any
migration file containing a psql meta-command (a line starting with a backslash), `COPY ... PROGRAM`,
`dblink`, `*_fdw`, `CREATE SERVER`, `ALTER SYSTEM` or `lo_import`/`lo_export` (none of the 883 files
today). `rehearsal_cluster.sh` refuses any symlink in the data dir's path, fails closed when `lsof`
cannot prove the port is free, and `reset --yes` deletes only `<rehearsal home>/pg`.

`__tests__/test_e5_6_rehearsal_guard.py` (143 tests, no database or network) runs the guard cases, a static
"guard precedes every psql/python/tsx call" check for all subcommands, env-leak checks (a stub `psql`/`tsx`
dumps its argv and environment while the caller sets `PGHOST`, `PGSERVICE`, `PGPASSFILE`, `DATABASE_URL`, ...),
sandboxed tests of `rehearsal_cluster.sh` against stub binaries, and **47 per-rule mutants** (each removes or
weakens one rule: port, host, query key, userinfo, whitespace, env, symlink, identity, ... in the guard, the
three scripts; each must make a check fail, and does). Shell tests use stub binaries, so even a broken guard
cannot open a connection from the test.

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

* Binds `127.0.0.1:55432` only. Trust auth on loopback means any local process can connect as `Dev` (accepted residual, see above); the unix socket is `0700`.
* No production dump, credential, URL, or environment variable is read, copied or referenced.
* `reset --yes` deletes only `/Users/Dev/suvarna/rehearsal/pg` (and refuses symlinked paths).
* `init` twice is a no-op; `replay` twice is a no-op; `stop`/`start` are idempotent.
* Disposable by design (`fsync=off`): never place anything of value here.

## E5.7 L0 rebuild drill — cost estimate (not run; research only, 2026-10-02)

* **Assets:** the 2026-09-04 registry snapshot (`00_ARCHITECTURE/briefs/nirmana/L0_ASSET_REGISTRY_SNAPSHOT_2026-09-04.json`)
  has 40 `bg_*` rows. Writers are `@register` / `WriterBase` classes in
  `platform/python-sidecar/pipeline/orchestrator/writers/bg_*.py` over `brahmagyan/l0_*.py`. No writer uses an LLM.
  No writer at all: `bg_panchanga`, `bg_ephemeris_engine` (service probes), `bg_sarvatobhadra_grid` (empty by
  design), `bg_gochara_citation_resolution` (migration seed, 14 rows).
* **Sources:** ~25 assets are hard-coded constants or DB-derived (seconds each). `bg_ephemeris` (825,084 rows),
  `bg_sky_calendar`, `bg_muhurta_lattice`, `bg_cohort` (110k rows) and `bg_gochara_arcs` need Swiss Ephemeris
  (`.se1` files exist locally under `/Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/se1/`; set `SWE_EPHE_PATH`).
  `bg_texts` needs 20 pinned objects in a private GCS bucket plus Vertex embeddings (credentials: not obtainable here).
* **Runtime (estimates; only `bg_gochara_arcs` ~1 min is measured):** ephemeris 4-10 min, muhurta lattice 15-60 min
  (longest), cohort 3-8 min, sky calendar 1-10 min, text-derived assets 1-5 min each; **30-90 min serial if
  `classical_text_chunks` is seeded, 45-135 min if `bg_texts` is rebuilt.** Disk < 1 GB (+0.5 GB source PDFs), RAM 1-2 GB peak.
* **Seed from production (read-only, as `suvarna_reader`):** `classical_text_chunks` (10,651 rows with 768-d
  embeddings; the practical alternative to rebuilding `bg_texts`), optionally `classical_texts`, the 14-row
  `bg_gochara_citation_resolution`, and every asset's production fingerprint for the comparison.
* **Blockers:** (1) the schema replay above lacks `classical_text_chunks`, `bg_transit_rules`,
  `gochara_resonance_map`, `remedy_review_queue` and has 93 of ~128 registry rows (PA-R10 baseline repair first);
  (2) `bg_sky_calendar` refuses to write off Linux/x86_64 (`_require_reproducible_write_runtime`) — this Mac is
  arm64, so a linux/amd64 container with pyswisseph 2.10.3.2 is needed; (3) rolling horizons (`bg_muhurta_lattice`
  today..+5y, `bg_sky_calendar` ..+10y) need a pinned as-of window for fingerprints; (4) `bg_texts` is not exactly
  reproducible offline (embeddings, PyMuPDF version); (5) the orchestrator entry point needs a digest-verified
  `build_runs` plan created by an evidence-gated dispatcher — practical path is `get_writer(asset)().run(ContextSpec(...))`
  in DAG order, as `run_heavy_writer_standalone.py` does; (6) the E5.5 fingerprint code lives on branch
  `suvarna/e5.5-stale-certs` (`nikasha_stale_certs.py`), per-asset declarations are in the L0 asset briefs §5.
