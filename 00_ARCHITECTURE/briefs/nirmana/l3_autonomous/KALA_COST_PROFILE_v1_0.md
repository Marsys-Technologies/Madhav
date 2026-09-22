---
artifact: KALA_COST_PROFILE
canonical_id: KALA_COST_PROFILE
version: "1.0"
status: MEASURED
date: 2026-09-22
phase: "L3 Kāla pre-elevation setup — Phase 0.3 (measure build cost properly)"
benchmark_contract: "MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md §5 Benchmark contract, adopted verbatim"
does_not_authorize: "any change; this is a measurement"
production_writes: "NONE — production was read-only throughout; every build ran on a disposable local Postgres that was torn down"
supersedes: none
raw_logs: "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/cost_runs/"
---

# Kāla (L3) cost profile — measured

> **What this document is.** A measurement of what the 22 active `ka_*` identities cost
> to compute, under the benchmark contract the Kāla strategy sets for itself, plus a
> retirement specification for `asset_registry.estimated_seconds` (F28).
>
> **What this document is not.** It is not a finding that any asset is too slow, and it
> authorizes no optimization. See §6, which is binding on every reader of §3 and §4.

## §1 — The benchmark contract as adopted, and the environment declaration it demands

### §1.1 The contract, adopted verbatim

Strategy §5 "Benchmark contract" is adopted in full, not in a thinner version. Its clauses
and this document's compliance:

| Contract clause (Strategy §5) | Where discharged | Status |
|---|---|---|
| "record the exact source/dependency/model versions, hardware, ephemeris files, workload dimensions, cache state, thread settings, storage and concurrency" | §1.2–§1.8 | **DISCHARGED** |
| "Use synthetic non-person cases and a bounded disposable database first" | §2.4 (case S1), §2.1 (disposable DB) | **DISCHARGED**, with a declared partial deviation — see §2.4 |
| "authorized real-chart builds follow at their own gate" | Not attempted. No production build was dispatched. | **RESPECTED** |
| "Measure wall and CPU time, peak RSS, time in Swiss calls/lock, SQL count and round-trip time, rows/bytes/WAL, serialization cost, checkpoint/recovery cost and time until the first qualified consumer result" | §2.3 instrument list; §3/§4 results | **DISCHARGED**, with two metrics honestly qualified — see §2.6 |
| "Use repeated matched runs and report spread; a single run cannot establish a tail percentile" | §2.5; every figure in §3/§4 carries n and spread | **DISCHARGED** |
| "Baseline/alternative comparisons must preserve the declared scope, methods, precision and input vector" | No alternative was built. This is a baseline-only measurement. | **N/A this pass** |
| "Test cold, warm, resume, horizon-extension, upstream-correction, no-window, dense-window and rare-boundary workloads" | §3 — eight workloads addressed; **three are NOT MEASURED and say so** | **PARTIAL — see §3.0** |
| "Prove geometry/interval parity, exact evidence identities and null semantics" | Not attempted — no alternative implementation exists to prove parity against. | **N/A this pass** |
| "declare tolerances before measurement" | §2.6, declared before the campaign ran | **DISCHARGED** |
| "For any intended semantic repair, compare to the qualified reference as well as the old version" | No semantic repair proposed. | **N/A this pass** |
| "Savings and runtime budgets will be set after the first measured profile. No specific factor or minutes-per-chart promise is made" | §6 restates this and binds it | **DISCHARGED** |

### §1.2 Hardware

| Property | Value | Command |
|---|---|---|
| CPU | Apple M5 Pro, 18 physical / 18 logical cores (6 performance + 12 efficiency) | `sysctl -n machdep.cpu.brand_string`, `sysctl -n hw.physicalcpu hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu` |
| Architecture | `arm64` | `uname -m` |
| RAM | 68,719,476,736 bytes (64 GiB) | `sysctl -n hw.memsize` |
| Page size | 16,384 bytes | `sysctl -n hw.pagesize` |
| Storage | APFS on internal SSD (`/dev/disk3s5`), 665 GiB free of 1.8 TiB | `df -h /tmp`, `diskutil info /` |

**Declared, load-bearing:** production runs on **`x86_64-pc-linux-gnu`** (see §1.4). This
harness is **arm64 Apple silicon**. Cross-ISA wall-clock figures are not transferable to
production by any constant factor. Every §3/§4 number is a harness number.

### §1.3 Operating system

| Property | Value |
|---|---|
| OS | macOS 26.5.1, build 25F80 |
| Kernel | `Darwin 25.5.0 / xnu-12377.121.6~2 RELEASE_ARM64_T6050` |

### §1.4 Postgres — harness and production

| Property | Harness | Production (read-only, authority) |
|---|---|---|
| Version | PostgreSQL **15.17** (Homebrew) | PostgreSQL **15.18** on `x86_64-pc-linux-gnu`, Debian clang 12.0.1 |
| `shared_buffers` | 16384 (128 MB) | not read (production config not queried) |
| `work_mem` | 4096 (4 MB) | not read |
| `maintenance_work_mem` | 65536 (64 MB) | not read |
| `effective_cache_size` | 524288 (4 GB) | not read |
| `max_worker_processes` / `max_parallel_workers` / `_per_gather` | 8 / 8 / 2 | not read |
| `wal_level` | `replica` | not read |
| **`fsync`** | **`off`** — see the limitation below | not read |
| `full_page_writes` | `on` | not read |
| `synchronous_commit` | `on` | not read |
| `checkpoint_timeout` / `max_wal_size` | 300 s / 1024 MB | not read |
| `jit` | `on` | not read |
| Connection | Unix domain socket `/tmp/kc0`, port 59520 | TCP to a managed instance |

**COULD NOT VERIFY: production's `postgresql.conf` settings.** The read-only role can
read `pg_settings`, but querying production tuning was outside what this phase needed and
was not run. Every harness-vs-production comparison in this document therefore compares an
**untuned local default instance** against an instance whose tuning is **unknown**, not
against a known-different one.

> ### ⚠ DECLARED LIMITATION — `fsync=off` (binding on every write/WAL figure)
>
> The harness runs with **`fsync=off`**, as the Phase 0.3 harness specification requires.
> This removes the cost of flushing WAL and data pages to durable storage. Consequently:
>
> * every **WAL bytes** figure in §3/§4 is a correct byte count but was produced without
>   durable-flush cost;
> * every **commit / serialization** figure is a **lower bound** on production commit cost,
>   potentially by a large and non-constant factor;
> * every **checkpoint** figure is a lower bound for the same reason;
> * **wall-clock figures for write-heavy assets are optimistic.** Read-heavy and
>   compute-heavy assets (where the cost is Swiss calls and Python, not `fdatasync`) are
>   much less affected.
>
> This limitation is restated inline in §3 and §4 and is **not** to be dropped when any
> figure from this document is quoted elsewhere.

Additionally: the harness socket is a **Unix domain socket on the same machine**, while
production is **TCP to a managed instance**. Every `sql_rtt_s` figure therefore **omits
network round-trip latency entirely** and is a lower bound on production SQL cost. For
assets whose cost is dominated by statement *count* rather than statement *work* — see
`ka_gochara_resonance` at 169 statements in §4 — this is the dominant unmodelled term.

### §1.5 Swiss ephemeris — files, versions, paths

| Property | Harness | Production (authority: `platform/python-sidecar/Dockerfile.pipeline`) |
|---|---|---|
| Library | `pyswisseph` **2.10.3.2**, Swiss Ephemeris **2.10.03** | same package pinned in `requirements.txt` |
| `SWE_EPHE_PATH` | `/tmp/se1` | `/app/ephe` |
| `sepl_18.se1` | 484,061 B, sha256 `ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66` | **same sha256** — the Dockerfile asserts this exact digest |
| `semo_18.se1` | 1,304,771 B, sha256 `1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7` | **same sha256** |
| `seas_18.se1` | 223,004 B, sha256 `a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2` | **same sha256** |
| `sefstars.txt` | 136,618 B | present |
| `seleapsec.txt` | 306,891 B | present |

**This is a verified identity, not an assumption.** The three binary ephemeris files were
fetched from the same `gs://madhav-ephemeris/se1` source the production image build uses,
and their SHA-256 digests were computed locally (`shasum -a 256`) and match the digests the
production `Dockerfile.pipeline` asserts with `sha256sum -c`. **The harness computes
against byte-identical ephemeris data to production.**

**Why this matters and was worth doing:** `pipeline/transit_search.py:_resolved_ephemeris_path()`
probes `SWE_EPHE_PATH`, `SWISSEPH_EPHE_PATH`, `/app/ephe`, `/tmp/se1` in order and returns
`None` if `sepl_18.se1` is absent. Before the files were fetched the harness had **no** se1
files and would have silently fallen back to Swiss Ephemeris's built-in Moshier analytic
ephemeris — different code path, different cost, different precision, and **no error**.
A cost measurement taken in that state would have been measuring a different program.

### §1.6 Language runtimes and dependency versions

| Component | Version |
|---|---|
| Python | CPython **3.13.7** (`main`, Aug 14 2025) |
| Python interpreter | `/Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3` — used **read-only** (`PYTHONDONTWRITEBYTECODE=1`); no file in that path was written |
| `psycopg` | 3.3.4 (`psycopg-binary` 3.3.4) |
| `pyswisseph` | 2.10.3.2 |
| `numpy` | 2.4.6 |
| `scipy` | 1.17.1 |
| `pandas` | 3.0.3 |
| `python-dateutil` | 2.9.0.post0 |
| `pytz` | 2026.2 |
| `sqlalchemy` | 2.0.50 |
| `fastapi` | 0.115.0 |
| Node.js / npm | v24.14.0 / 11.9.0 (not exercised by this measurement) |

### §1.7 Source version — the exact code measured

| Property | Value |
|---|---|
| Worktree | `/Users/Dev/madhav-l3/setup` |
| Branch | `l3/kala-setup-phase01` |
| HEAD | `5ff0030f398dd1ef97ffc381005c8a1f2e600329` (`5ff0030f3`), committed 2026-09-22T10:27:33Z |
| Tracked-file modifications at measurement time | **0** — the tree was clean; nothing measured here was a local edit |

Per-file SHA-256 prefixes for all 23 `ka_*` writer modules, all 16 `services/ka_*` packages
(directory-aggregate digest), and the orchestrator core (`asset_runner.py`, `runner.py`,
`db.py`, `birth_params.py`, `writers/__init__.py`, `transit_search.py`) are recorded in
`setup/cost_runs/source_versions.txt`. Any future re-measurement that does not reproduce
those digests is not a matched comparison.

### §1.8 Thread settings, concurrency and cache state

| Dimension | Declared value |
|---|---|
| Writer concurrency | **1** — exactly one writer process at a time, serially. No two assets were ever measured concurrently. |
| Postgres backend concurrency | 2 connections per run (one writer connection, one admin probe connection); no other client active |
| Postgres parallel query | `max_parallel_workers_per_gather = 2` (default, not disabled) |
| Python threads | Single-threaded; no writer spawned threads during measurement (not asserted for `ka_kshetra`, which was not run to completion) |
| `OMP_NUM_THREADS` / BLAS threading | Not set; numpy/scipy defaults in effect |
| **Swiss lock span** | **NOT MEASURED as a distinct quantity.** Swiss call time and call count are measured (§2.3). The strategy's concern about "a global lock" and "the existing complete Swiss-state serialization span" (§5) concerns a *serialization boundary*, which a single-threaded, single-process harness cannot exercise. See §4's `swiss_lock_s` column. |
| Process cache state | **Cold per run.** Every run is a **fresh Python subprocess** — no `lru_cache` in `transit_search.py` (`_EPHEMERIS_CACHE_MAXSIZE = 400_000`), no module-level state and no Swiss file handle survives between runs. This is deliberate: an in-process warm cache would have made run 2..n of a repeated series unrepresentative of a real per-chart build. |
| Postgres cache state | **Warm and increasingly so.** `shared_buffers` and the OS page cache were *not* dropped between runs. For a repeated series this biases runs 2..n **faster** than run 1. This is reported as the cold/replay split in §3.1/§3.2 rather than hidden. |
| Ephemeris file cache | Warm after run 1 (OS page cache; the three `.se1` files total ~2 MB and stay resident). |

## §2 — Method

### §2.1 Harness construction

A disposable PostgreSQL instance, created and destroyed for this measurement only.

```
PGBIN=/opt/homebrew/opt/postgresql@15/bin
rm -rf /tmp/kc0 && mkdir -p /tmp/kc0
$PGBIN/initdb -D /tmp/kc0/data -U kxuser --auth=trust
$PGBIN/pg_ctl -D /tmp/kc0/data -o "-p 59520 -k /tmp/kc0 -c fsync=off" -l /tmp/kc0/pg.log start
$PGBIN/psql -h /tmp/kc0 -p 59520 -U kxuser -d postgres -c "CREATE DATABASE kcost OWNER kxuser;"
```

Schemas `auth` and `nirmana_evidence` were created to match production's non-`public`
schema set. Extensions `pg_trgm`, `pgcrypto`, `uuid-ossp` were installed and match
production's versions (1.6 / 1.3 / 1.1).

**Declared deviation — `pgvector`.** Production carries `vector 0.8.1` in `public`. The
local `postgresql@15` Homebrew formula has no pgvector build (pgvector 0.8.6 is present
but compiled only for `postgresql@17`/`@18`). The schema was therefore transformed before
restore: 11 `vector(N)` column typmods were rewritten to `text`, and 8 `ivfflat`/`hnsw`
index definitions were commented out and marked `HARNESS-DISABLED`.

*Why this is safe for this measurement, proven not assumed:*
```sql
SELECT count(*) FROM information_schema.columns
 WHERE udt_name='vector' AND table_schema='public'
   AND (table_name LIKE 'kala%' OR table_name LIKE 'ga\_%' OR table_name LIKE 'chart\_%');
-- → 0
```
No `kala_*`, `ga_*` or `chart_*` table carries a `vector` column, so **no `ka_*` write path
touches one**. Seven `bodha_*` tables do (`bodha_msr_signals`' companion
`bodha_signal_embeddings`, `bodha_cgm_nodes`, etc.). Those are **read** by `ka_yojaka` and
`ka_kshetra`. Consequence: any byte/size figure that includes a `bodha_*` embedding table
is **not** comparable to production, and no `ka_*` asset's own row storage is affected.
This is flagged again in §4.

### §2.2 Schema transfer — and the trigger-function trap

The documented trap: a table-scoped `pg_dump --schema-only -t public.<tables>` **drops the
trigger functions**, so a harness built that way runs *without production's guard layer* and
its numbers are not comparable. A prior pathfinder lane hit exactly this.

**What was done instead.** A whole-schema dump (`-n public`, no `-t` filter), which carries
functions, triggers, views, matviews and indexes:

```
pg_dump --schema-only --no-owner --no-acl -n public \
  --exclude-table=public.planner_inquiry_action_reservations \
  --exclude-table=public.planner_inquiry_evidence_receipts \
  --exclude-table=public.planner_inquiry_lifecycles \
  --exclude-table=public.planner_managed_prashna_jobs \
  -f /tmp/kc0/schema/public_schema.sql
```
(The four exclusions are the only `public` tables the read-only role lacks `SELECT` on;
without excluding them `pg_dump` aborts on `LOCK TABLE … permission denied`.)

Restored objects: **389 tables, 126 triggers, 155 functions, 13 views, 25 materialized
views, 1,195 indexes**, including all 41 `kala_*` tables.

#### The trigger functions carried — named, and verified

Production has **26** distinct trigger functions in `public` across **130** trigger
attachments. The harness carries **22** functions across **126** attachments. The
**complete carried set**, by name:

```
_assert_throughput_global_no_chart_id      l2_data_plane_capture_row
_record_asset_throughput_state_change      l2_data_plane_guard_active_mutation
bmpl_freeze_confirmed                      l2_data_plane_guard_completed_run_rows
brahma_prospective_ledger_enforce_shape    l2_data_plane_guard_generation_change
chart_subject_append_only_guard            l2_data_plane_reject_immutable_change
conversations_set_updated_at               nirmana_elevation_prevent_monitor_observation_mutation
l1_data_plane_capture_row                  nirmana_invalidate_chart_receipts
l1_data_plane_guard_active_mutation        nirmana_invalidate_registry_receipts
l1_data_plane_guard_generation_change      pariprashna_safety_append_only_guard
l1_data_plane_reject_immutable_change      phala_anchors_set_identity
reject_build_run_manifest_mutation         update_capability_tool_registry_updated_at
```

**The four NOT carried, and why:** `planner_inquiry_action_reservation_guard`,
`planner_inquiry_immutable_guard`, `planner_managed_prashna_job_credential_guard`,
`planner_managed_prashna_job_immutable_guard`. These are the triggers on exactly the four
`planner_*` tables the read-only role cannot `SELECT`. They guard the planner-inquiry
surface. **No `ka_*` writer reads or writes any `planner_*` table** (verified: no
`planner_` reference appears in the table-dependency extraction of §2.7). This is a bounded,
declared gap, not an unknown one.

#### Verification that the trap is closed — existence is not the proof

Per §N.8, a carried-function *list* is not evidence the guard layer works — the signal must
have a detector behind it. Two proofs were run:

**(a) Set identity.** Production's trigger-function set and attachment set were dumped and
diffed against the harness's. The only differences are the four `planner_*` entries above:
```
comm -23 prod_trigfuncs.txt harness_trigfuncs.txt   → the 4 planner_* functions, nothing else
comm -23 prod_trigs.txt     harness_trigs.txt        → the 4 planner_* attachments, nothing else
```
(Raw output: `setup/cost_runs/trigger_proof.txt` and the `*_trigfuncs.txt` / `*_trigs.txt` pairs.)

**(b) Live firing.** After seeding, with triggers re-enabled, guarded writes were attempted
and **refused**:
```
INSERT INTO chart_facts (chart_id) VALUES ('1111…');
  ERROR:  protected L1 INSERT requires direct data_plane_builder authentication
  CONTEXT: PL/pgSQL function l1_data_plane_guard_active_mutation() line 15 at RAISE

INSERT INTO bodha_msr_signals (chart_id) VALUES ('1111…');
  ERROR:  protected L2 INSERT requires direct data_plane_builder authentication
  CONTEXT: PL/pgSQL function l2_data_plane_guard_active_mutation() line 16 at RAISE
```
This is the detector: a code path that *would* have produced a different result had the
guard been absent, and did not.

**Post-seed trigger state, proven:** all **126 / 126** attachments report `tgenabled = 'O'`
(enabled), and `session_replication_role = origin`. No trigger was left disabled.

#### A finding that falls out of the trap check

```sql
SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
 WHERE NOT t.tgisinternal AND c.relname LIKE 'kala\_%';   -- production → 0
```
**The `kala_*` tables carry zero triggers.** L1's `ga_*`/`chart_*` tables carry 14
attachments and L2's `bodha_*` carry 56; L3 carries none. So the trigger-carry trap bites on
the **seed** side (getting L1/L2 data *in*), not on the L3 **write** path being measured.
Stated plainly: the guard layer is **present and firing** in this harness, and it does not
sit on the code path whose cost §3/§4 reports. Both halves of that sentence matter — the
first because the prior pathfinder lacked it, the second because it bounds what the guard
layer could have cost.

### §2.3 Instrumentation — what each contract metric actually measures

`setup/cost_runs/` contains the harness (`kbench.py` runner, `drive.py` repeated-run driver).

| Contract metric | Instrument | Honest scope |
|---|---|---|
| Wall time | `time.perf_counter()` around writer construction → last commit | Excludes process start and module import (measured separately as subprocess wall) |
| CPU time | `resource.getrusage(RUSAGE_SELF)` `ru_utime`/`ru_stime` delta | Writer process only; Postgres backend CPU is **not** included |
| Peak RSS | `ru_maxrss` | Process high-water mark, includes interpreter + imports baseline (~100 MB) |
| Time in Swiss calls | Monkey-patched wrapper over 16 `swisseph` entry points (`calc_ut`, `calc`, `houses*`, `rise_trans`, eclipse fns, `get_ayanamsa*`, `julday`, `revjul`, `deltat`, `sidtime`, `nod_aps_ut`) accumulating `perf_counter` deltas + a call counter | Measures **call time**, and the instrumented name list is recorded per run. Any Swiss entry point not in that list is invisible. |
| Time in Swiss **lock** | **NOT MEASURED** | See §1.8 and the `swiss_lock_s` column in §4 |
| SQL count + round-trip | Monkey-patched `psycopg.Cursor.execute`/`executemany` accumulating count + `perf_counter` | **Excludes COPY-protocol traffic**, which bypasses `Cursor.execute`. Assets using `COPY` under-report. Counters are reset *after* all pre-run probes so only the measured window counts. |
| Rows | `count(*)` on the asset's `target_table`, chart-scoped, before and after | Reported as **`rows_after`** (rows the asset produced), not delta — the §N.3 delete-then-insert idempotency standard makes delta 0 on a replay even though full work was done |
| Bytes | `pg_total_relation_size` on `target_table`, before/after | Includes indexes and TOAST |
| WAL | `pg_wal_lsn_diff(pg_current_wal_lsn() after, before)` | Whole-instance WAL in the window; the harness is otherwise idle, so this is attributable — **subject to the `fsync=off` limitation** |
| Serialization cost | `perf_counter` around each `conn.commit()` | **Lower bound** — `fsync=off` |
| Checkpoint / recovery cost | Explicit `CHECKPOINT` timed before and after each run | **Lower bound** — `fsync=off`. **Crash-recovery cost was NOT measured** (no crash was induced). |
| Time until first qualified consumer result | `perf_counter` at the first `INSERT INTO <target_table>` / `COPY <target_table>` statement, minus run start | Measures **first write**, which is the earliest a consumer could see anything. It is *not* a full "first qualified consumer result" — no consumer query was run against a partially-built table. Declared as a proxy, labelled `ttf_first_target_write_s`. |

### §2.4 Seeding, and the synthetic-case deviation

Two cases were built.

**Case S1 — synthetic non-person** (strategy-preferred). A fabricated `public.charts` row:
`SYNTHETIC-KBENCH-S1`, born 2000-01-01 12:00:00 UTC at 0.0°N 0.0°E ("Null Island"), with
**no L1 and no L2 upstream data whatsoever**. This is a real synthetic case, and it turned
out to measure exactly one of the contract's required workloads — **no-window** (§3.6).

**Case D — canonical chart, real seeded upstream.** `482012f1-710e-4a25-994a-93821f5871aa`,
with its production L0/L1/L2 rows copied read-only into the harness.

> **DECLARED DEVIATION from the strategy's "use synthetic non-person cases first".**
> Case D is **not** a synthetic non-person case. It is the canonical native's real computed
> upstream data, copied into a disposable local database. This deviation was taken
> deliberately and is declared rather than concealed, because:
> * a genuinely synthetic case with real upstream requires a full L0→L1→L2 build for that
>   synthetic chart — `ga_dashas` alone has a production `estimated_seconds` of 1,118 s and
>   `ga_sensitive` 407 s, and L2 Bodha is a further multi-asset build. That is hours of
>   compute and is itself out of Phase 0's budget;
> * without it, Case S1 shows (correctly) that every `ka_*` writer returns 0 rows in ~2–25 ms,
>   which is a true measurement of the no-window workload and a **useless** measurement of
>   what a chart build costs.
>
> **Handling.** No chart narrative or interpretive content was read, printed, logged or
> written to any artifact. The harness was destroyed (§2.8). Only row counts, byte counts
> and timings left the harness. A future pass that wants a strictly synthetic dense case
> must budget the upstream build; this document does not claim to have done so.

**Seed mechanics.** Streamed `psql \copy … TO STDOUT | psql \copy … FROM STDIN`, prod → harness,
never the reverse. 50 global/reference tables whole; 156 per-chart tables filtered to Case D's
`chart_id`; `charts`/`profiles` by primary key. User triggers were disabled for the seed
window and **re-enabled and re-proved firing afterwards** (§2.2b). `kala_*` output tables were
deliberately **not** seeded — they are what the measured builds produce.

Volumes actually landed (from `setup/cost_runs/seed_report.txt`):

| Table | Rows | Note |
|---|---|---|
| `ephemeris_daily` | 825,084 | 1900-01-01 → 2150-12-31, all bodies |
| `chart_dashas` | 483,870 | Case D, L1 |
| `chart_facts` | 143,299 | Case D, L1 |
| `bodha_msr_signals` | 50,678 | Case D, L2 |
| `bodha_signal_embeddings` | 50,678 | Case D, L2 (vector→text, see §2.1) |
| `bodha_grounding_matches` | 50,731 | Case D, L2 |
| `chart_vichara` | 8,524 | Case D, L1 |
| `bg_*` / `brahma_*` reference | 50 tables | incl. `bg_gochara_arcs` 33,933, `bg_sky_calendar` 31,081, `bg_synthetic_cohort_md` 100,000 |
| `kala_field_weight_versions` / `kala_field_weights` | 1 / 29 | L3 **config**, not chart output — required by `ka_kshetra` |

**Seed gaps, declared.** Six source tables failed to transfer and were left empty:
`bg_muhurta_lattice` (239 MB, deliberately skipped — not in the `ka_*` dependency
extraction), `brahma_yoga_source_chunks`, `brahma_mimamsa_prediction_ledger`,
`phala_rectification_best`, `asset_provenance_receipts` (all four: foreign keys to rows
outside the chart-scoped slice), and `chart_divisionals` (0 rows for Case D **in production
itself** — not a seed failure). Any asset that depends on one of these is measured against a
*thinner* input vector than production and is flagged in §4.

**A seed finding worth recording.** Four tables initially failed with
`extra data after last expected column` under both TEXT and CSV `COPY`. Root cause:
`ephemeris_daily.sign_number`, `.degree_in_sign`, `.nakshatra_number`,
`bg_sky_calendar.secondary_body_key`, `asset_freshness.scope_key` and
`asset_provenance_receipts.scope_key` are **`GENERATED ALWAYS` (stored) columns**, which
`COPY FROM` refuses to accept values for. Fixed by copying an explicit non-generated column
list; the harness then recomputes those columns from **the same generation expressions**
carried by the schema dump — a fidelity gain, not a loss.

### §2.5 Repeated matched runs and how spread is reported

The contract is explicit: *"Use repeated matched runs and report spread; a single run cannot
establish a tail percentile."*

* Every run is a **fresh subprocess** (`drive.py` → `subprocess.run`). No Python-level state,
  `lru_cache`, Swiss handle or connection survives between runs.
* Run counts: **n = 5** for service and light assets, **n = 5** for mid assets, **n = 3** for
  heavy assets, **n = 2** for `ka_gochara_v3_century_materialize`, **n = 3 plan-only** for
  `ka_kshetra`. Every figure in §3/§4 carries its own `n`.
* Reported spread per metric: **min / median / max / mean / stdev**. Where n ≤ 2 the document
  says so and **does not** present a median as if it were a distribution.
* **No percentile beyond the median is claimed from harness runs.** At n = 3–5 a p95 is not
  identifiable. Where a tail figure appears in this document it comes from production's
  `build_run_assets` history (§3.7), which has n = 15–53 per asset, and is labelled as such.
* A run that errors is recorded with its error and the series is **stopped** rather than
  repeated — a deterministic failure repeats identically and burning n runs on it would
  misrepresent the spread of the successful population.

### §2.6 Tolerances, declared before measurement

| Quantity | Declared tolerance / treatment |
|---|---|
| Wall time | No tolerance claimed below **1 ms**. Timer resolution is far finer, but process scheduling on a shared laptop is not. Figures below 10 ms are reported to 4 dp for reproducibility and should be read as "sub-10 ms", not as precise. |
| Wall time, run-to-run | Accepted as noise up to **±20 %** for runs under 100 ms; above 1 s, spread is reported and interpreted. |
| CPU time | Writer process only. Postgres backend CPU is **excluded** and is *not* estimated. |
| Peak RSS | Includes a ~100 MB interpreter+import baseline (measured: `ka_tulana`, which does almost nothing, peaks at 96.7 MB). Subtract that baseline before reading an asset's own memory cost. |
| Swiss time | Only the 16 instrumented entry points. Wrapper overhead (one `perf_counter` pair per call) is real and is **not** subtracted; for `ka_tithi_pravesha` at 132,004 calls this inflates measured Swiss time by an unquantified amount. Declared. |
| SQL RTT | Unix socket, no network. **Lower bound** on production. COPY traffic excluded. |
| WAL / commit / checkpoint | `fsync=off`. **Lower bounds.** |
| Row counts | Exact (`count(*)`), not estimated. |
| Extrapolation | Any number this document extrapolates rather than measures is labelled **EXTRAPOLATION**, states its method, and states its error bound. |

### §2.7 Dependency extraction

Table dependencies per asset were extracted statically from
`services/ka_*/**.py` and `pipeline/orchestrator/writers/ka_*.py` by matching
`FROM|JOIN|INTO|UPDATE <table>`. This is a **lower bound** on real reads: dynamically
constructed SQL and `format()`-built identifiers are invisible to it. It is used in this
document only to (a) decide what to seed and (b) bound the `planner_*` trigger gap in §2.2 —
never to assert a complete dependency graph. Strategy §6.3's own warning applies: registry
`depends_on` and implementation reads disagree, and neither is certified here.

### §2.8 Teardown — proof

See §7. The instance was stopped, its port proved unbound, and its data directory removed.

## §5 — `asset_registry.estimated_seconds`: what it is, who reads it, and how to retire it

### §5.1 The F28 claim, tested

F28 holds that `estimated_seconds` claims roughly 24.3 minutes for the whole Kāla layer
while `ka_kshetra` alone measures ~7.5 hours, and that there is no detector behind the number.

**The 24.3-minute figure is exactly right.** Measured read-only at the authority:

```sql
SELECT count(*), sum(estimated_seconds), round(sum(estimated_seconds)/60.0,2)
  FROM asset_registry WHERE asset_id LIKE 'ka\_%' AND is_active;
-- → 22 | 1459 | 24.32
```
22 active `ka_*` rows, **1,459 s = 24.32 minutes**. (Including the retired inactive
`ka_gochara_sweep` at 1,000 s: 23 rows, 2,459 s = 41.0 min.)

**But the number is not fabricated, and that changes the retirement argument.** A stronger
and more useful result emerged: `estimated_seconds` is a **stale cached snapshot of a live
query** — specifically `ceil(median duration of `state='complete'` runs in `build_run_assets`)`.
Tested directly:

```sql
WITH m AS (SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY
             EXTRACT(EPOCH FROM (ended_at-started_at))) AS med
           FROM build_run_assets
           WHERE ended_at IS NOT NULL AND started_at IS NOT NULL AND state='complete'
           GROUP BY asset_id)
SELECT r.asset_id, r.estimated_seconds, round(m.med::numeric,2), ceil(m.med)::int,
       CASE WHEN r.estimated_seconds = ceil(m.med)::int THEN 'MATCH' ELSE 'differs' END
FROM asset_registry r LEFT JOIN m ON m.asset_id=r.asset_id
WHERE r.asset_id LIKE 'ka\_%' ORDER BY 5, 1;
```

**18 of 23 `ka_*` rows match `ceil(live median)` to the integer**, including every large one:
`ka_sangam` 463 vs 462.87, `ka_kshetra` 237 vs 236.74, `ka_gochara_v3_century_materialize`
614 vs 613.49, `ka_gochara_sweep` 1000 vs 999.52, `ka_kalasutra` 33 vs 32.98, `ka_yojaka`
36 vs 35.50. The five that differ (`ka_kota_chakra`, `ka_moorti_nirnaya`,
`ka_sudarshana_varsha`, `ka_tithi_pravesha`, `ka_vedha_gochara`) are the newest, lowest-run-count
assets whose medians have moved since the snapshot was taken. Across **all** layers the same
rule matches 53 of 94 non-null rows.

**And yet the number has no write provenance in version control.** Independently verified:

* `platform/scripts/seed/asset_registry_seed.ts` inserts **`estimated_seconds: null`** for
  **all 23** `ka_*` rows (`awk "/asset_id: 'ka_/,/^  }/" … | grep estimated_seconds` → 20×
  `per_chart, is_active: true, estimated_seconds: null`, 2× `global … null`, 1× `is_active:
  false … null`), and deliberately omits the column from its `ON CONFLICT DO UPDATE SET`.
* **No migration sets a literal `estimated_seconds` for any `ka_*` asset.** The seven
  migrations that write the column (179, 223, 690, 847, 879, 899 and the seed) target `bg_*`,
  `ga_*`, `mi_*` and `bo_grounding`. The only `ka_*` touch is migration
  `563_utkarsha_w64_asset_rename.sql:82,94`, which **copies** the old row's value verbatim
  during the `ka_gochara_v2_materialize` → `ka_gochara` rename and sets nothing.

So the live values were written **outside migration and seed control**, by a process not
recorded in the repository. They are auditable only by reverse-engineering them from the
telemetry they were snapshotted from — which is what §5.1 just did.

**The methodological defect — and this is the part that matters.** The snapshotted statistic
is a **median over a bimodal population contaminated by no-op completions**. §3 measured
both modes directly. `ka_gochara`'s production `complete` durations sort as:

```
0.04  0.04 … 1.30 … 125.97  140.88  142.53      (n=37)
```

and this harness reproduced both modes on demand: **75.33 s** for the real build (27 substeps,
30,173 SQL statements, 45,430 Swiss calls) and **0.013 s** for the immediately following
replay (`plan_substeps` → **0** substeps). The median of that mixture is 0.20 s, and
`estimated_seconds = 1`. **The registry is reporting the no-op mode as the cost of the asset.**

That is §N.8 exactly, one layer out from where SATYA-DĪPA found it: the promotion predicate
that lets a no-op run land in `build_run_assets` as `state='complete'` is the same defect that
poisons the statistic derived from that table. The number is not a lie about intent; it is a
detector measuring the wrong population.

### §5.2 The comparison table

`estimated_seconds` against this harness's measurement and against production's own history.
Harness figures are **Case D cold** (arm64 / `fsync=off` / socket — §1.2, §1.4); production
history figures are `build_run_assets` `state='complete'`, which is the population the
registry value was snapshotted from.

| asset_id | registry `estimated_seconds` | harness measured (cold, Case D) | ratio measured ÷ registry | prod hist n | prod median | prod p95 | prod max |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ka_tulana` | 1 | 0.0222 s | **0.02×** | 44 | 0.08 | 1.3 | 1.4 |
| `ka_graha_sancara` | 1 | 0.0117 s | **0.01×** | 32 | 0.14 | 1.5 | 2.0 |
| `ka_dasha_kala` | 2 | 0.0315 s | **0.02×** | 48 | 1.22 | 6.5 | 25.9 |
| `ka_muhurta_seva` | 1 | 0.0246 s | **0.02×** | 32 | 0.33 | 1.3 | 4.2 |
| `ka_gochara_resonance` | 1 | 0.0362 s | **0.04×** | 22 | 0.25 | 16.9 | 17.1 |
| `ka_moorti_nirnaya` | 3 | 0.0183 s | **0.01×** | 8 | 0.75 | 3.7 | 4.5 |
| `ka_kota_chakra` | 3 | 0.0234 s | **0.01×** | 7 | 0.70 | 3.0 | 3.2 |
| `ka_vedha_gochara` | 4 | 0.0232 s | **0.01×** | 8 | 0.05 | 3.3 | 3.4 |
| `ka_tithi_pravesha` | 3 | 0.6278 s | **0.21×** | 8 | 1.04 | 2.4 | 2.4 |
| `ka_sudarshana_varsha` | 2 | 0.0086 s | **0.004×** | 7 | 0.30 | 2.3 | 2.4 |
| `ka_avadhi` | 14 | 0.0936 s | **0.007×** | 43 | 13.13 | 27.1 | 60.6 |
| `ka_yojaka` | 36 | 4.8404 s | **0.13×** | 53 | 35.50 | 87.0 | 111.5 |
| **`ka_gochara`** | **1** | **75.3296 s** | **75.3×** | 37 | 0.20 | **128.6** | 142.5 |
| `ka_gochara_v3_century_materialize` | 614 | see §4 | see §4 | 3 | 613.49 | 3203.8 | 3491.6 |
| `ka_sangam` | 463 | see §4 | see §4 | 50 | 462.87 | **2840.3** | 4389.8 |
| `ka_kalasutra` | 33 | see §4 | see §4 | 49 | 32.98 | **644.7** | 1040.8 |
| `ka_vighnakara` | 14 | see §4 | see §4 | 47 | 13.88 | 30.3 | 86.5 |
| `ka_taranga` | 23 | see §4 | see §4 | 43 | 22.33 | 48.0 | 82.5 |
| `ka_kala_darshana` | 1 | see §4 | see §4 | 48 | 0.37 | 3.4 | 4.2 |
| `ka_jivana_parva` | 1 | see §4 | see §4 | 45 | 0.62 | 2.8 | 3.2 |
| `ka_bhavishya_lekha` | 1 | see §4 | see §4 | 48 | 0.23 | 2.2 | 2.3 |
| **`ka_kshetra`** | **237** | NOT RUN TO COMPLETION — §3.8 | see §3.8 | 15 | 236.74 | **5331.7** | **7129.4** |
| `ka_gochara_sweep` (retired, inactive) | 1000 | not measured — retired, no writer | — | 9 | 999.52 | 7828.5 | 8022.8 |

**Read the ratio column carefully, and do not read it as "the registry over-estimates."**
Most ratios are far *below* 1, which means the registry over-states the cost of light assets
on this hardware. The two that matter run the other way and they are the whole point:

* **`ka_gochara`: registry 1 s, measured 75.33 s — a 75× understatement**, and production's
  own p95 for the same asset is 128.6 s, a 129× understatement. The registry integer is the
  no-op mode of a bimodal distribution.
* **`ka_kshetra`: registry 237 s.** Production's own history for this asset reaches
  **7,129 s (1 h 59 m)** at max and **5,331 s** at p95 among `complete` runs, and **121,757 s
  (33.8 h)** among runs that ended in `error`. The prior lane's ~7.5 h figure sits inside that
  range. **The registry's own `writer_timeout_seconds` for `ka_kshetra` is 86,400 (24 hours)**
  — the same row simultaneously asserts that the asset takes 4 minutes and budgets a day for
  it. That internal contradiction is, on its own, sufficient to disqualify the column as a
  planning input.

The layer total tells the same story from the other end. The registry's 1,459 s (24.3 min)
is the sum of 22 medians, most of which are no-op medians. Production's own history, summed
at p95 over the same 22 assets, is **≈ 12,500 s ≈ 3 h 28 m** — and that still excludes
`ka_kshetra`'s error-state tail.

### §5.3 Every consumer site, with live-path status

Search scope, stated so the absences below are bounded: `platform/src/**`,
`platform/scripts/**`, `platform/migrations/**`, `platform/supabase/migrations/**`,
`platform/tests/**`, `platform-mcp/**`, `platform/python-sidecar/**`, top-level `scripts/`,
`tests/`, `infra/`, `evals/`, `bench/`, `accuracy/`, `00_ARCHITECTURE/**`, `docs/**`,
`99_ARCHIVE/**`, and every non-directory file at the repository root. **Excluded:**
`node_modules/`, `dist/`, `.next/`, build output, `.git/`, `coverage/`. Spellings searched:
`estimated_seconds`, `estimatedSeconds`, `estimated_sec`, `estimatedSecs`, `eta_seconds`,
`etaSeconds`, plus `SELECT * FROM asset_registry` and `.from('asset_registry')` for implicit
carry. There is **no top-level `pipeline/` directory**; the orchestrator is at
`platform/python-sidecar/pipeline/orchestrator/`.

#### The one computation

| file:line | what it computes | live path? |
|---|---|---|
| `platform/src/lib/build/plan.ts:399-407` | `estimateSeconds(ids, registry)` — sums `entry.estimated_seconds` across the resolved plan; **all-or-nothing**: `if (!entry \|\| entry.estimated_seconds == null) return null`. Called at `plan.ts:544` (update), `:568` (cascade), `:622` (build/rebuild); produces `BuildPlan.estimated_seconds`. Types at `plan.ts:60`, `:96`. | **Reached, then discarded at all three callers — see below.** |

#### Sites that SELECT the column

| file:line | what it does | live path? |
|---|---|---|
| `platform/src/app/api/cockpit/plan/route.ts:49` | SELECTs the column, feeds `resolveBuildPlan` at `:87` | **LIVE** — `POST /api/cockpit/plan`, reached from `PlanModal.tsx:55` ← `BuildActionButton.tsx:107` ← `LayerPanel` ← `DataAssetsView.tsx:309` ← `v2/CockpitShell.tsx:210` ← `app/clients/[id]/nirmana/page.tsx:74`; also `AssetRow.tsx:206`. **Value discarded — see §5.4.** |
| `platform/src/app/api/cockpit/runs/route.ts:239` | SELECTs the column, feeds `resolveBuildPlan` at `:334` | **LIVE** (the real build-dispatch route) — but the 201 body at `:704-716` returns `run_id`, `plan`, `asset_count`, `job_image_tag`, optional `protected_assets`/`dispositions`. `buildPlan.estimated_seconds` is **never read and never returned**. |
| `platform/src/lib/build/recalibrationEnqueue.ts:139` | SELECTs the column, feeds `resolveBuildPlan` at `:152` | **LIVE** (via `lib/mcp/lel_recalibration_dispatch.ts`) — only `.plan_waves` (`:159`) and `.status` (`:161`) are read. Value dropped. |
| `platform/src/app/api/cockpit/clear/route.ts:115` | SELECTs it to satisfy the `RegistryEntry` type | LIVE read, **value never referenced** |
| `platform/src/app/api/cockpit/clear/execute/route.ts:86` | same | LIVE read, value never referenced. `preview_hash` (`:112-116`) is computed over `affectedAssetIds` only, so a change to this column **cannot** cause a `HASH_MISMATCH` 409. |
| `platform/src/app/api/cockpit/registry/route.ts:28, :67` | returns the raw per-asset value in `GET /api/cockpit/registry` JSON | **LIVE — the value genuinely crosses to the browser** via `hooks/useAssetRegistry.ts:32`. But `AtlasView.tsx`, `v2/LiveDependencyGraph.tsx`, `v2/LayerPanel.tsx`, `v2/AssetRow.tsx` contain **zero** `estimated` references. Nothing renders it. |
| `platform/src/app/cockpit/atlas/page.tsx:15` | server component SELECT → `<AtlasView assets=…>` | LIVE read; `AtlasView.tsx` never renders it |
| `platform/src/lib/cockpit/clearScopeFilter.ts:8` | `estimated_seconds?: number \| null` on `RegistryRow` | type declaration only; `filterScopeAssets` never reads it |

#### Sites that render an ETA — from a different source

| file:line | source of its value |
|---|---|
| `platform/src/app/api/cockpit/plan/route.ts:123-143, :156` | **`PERCENTILE_CONT(0.5)` over `build_run_assets` where `state='complete'`** — computed fresh, then spread **after** `...buildPlan` in the response literal, so it **shadows** the registry-derived sum |
| `platform/src/lib/components/cockpit/v2/PlanModal.tsx:18, :129-133` | the plan route's median field — renders `'unknown'` / `~Ns` / `~Nm` |
| `platform/src/lib/components/cockpit/v2/AssetRow.tsx:173, :217, :230, :464` | the plan route's median field |
| `platform/src/components/cockpit/BuildConfirmModal.tsx:9, :21, :99` | the plan route's median field, guarded `!= null` |

#### Dead or unreached

| file:line | why |
|---|---|
| `platform/src/components/cockpit/CascadePreviewModal.tsx:24, :54, :249, :258` | its only renderer, `AssetTable.tsx:149-155`, never passes `estimatedSeconds`; the prop is permanently `undefined` and the block never renders |
| `platform/src/components/cockpit/OverallProgress.tsx:23, :46, :74-75` | the component has **no non-test importer**; `v2/CockpitShell.tsx` does not import it (the mention in `app/clients/[id]/nirmana/page.tsx:9` is inside a code comment) |
| `platform/src/hooks/useBuildProgress.ts:21, :38, :55` | polls `/api/build/active`, which is an 11-line route returning **HTTP 410 `ENDPOINT_GONE`**; and its `eta_seconds` never came from `asset_registry` anyway |

#### Not consumers

`platform/src/app/api/build/cascade/route.ts:48` and `cascade-preview/route.ts:51` hardcode
`estimated_seconds: null` as a type shim (their SQL does not select the column).
`00_ARCHITECTURE/CONDUCTOR/build_orchestrator/data_progress/poll_daemon.py:770`
(`eta_seconds_remaining`) computes from a live rows-per-second rate and never touches
`asset_registry`. `platform/migrations/848_…sql:8` is a comment.

#### Write sites

Migrations `179` (INSERT, all NULL), `223` (`ga_dashas`=2400, `ga_vargas`=600,
`ga_sensitive`/`ga_structural`/`ga_sade_sati`=120, `ga_positions`/`ga_strength`/`ga_panchanga`/`ga_tajaka`=60),
`563` (verbatim copy on the `ka_gochara` rename — the only `ka_*` touch),
`690` (`mi_adhilepa`=31, `mi_bhara`=17, `mi_pariksha`=4, `mi_bhavisya`=3, `mi_jivanaghatana`=2),
`847` (`ga_positions`=17, `ga_nakshatra`=59, `ga_condition`=71, `ga_sade_sati`=142, `ga_vichara`=307),
`879` (`ga_ayurdaya`=9, `ga_dashas`=1118, `ga_panchanga`=10, `ga_sensitive`=407, `ga_strength`=132,
`ga_vargas`=256, `ga_tajaka`=19, `ga_transit_anchors`=2, `ga_vastu`=2, `ga_yoga`=10),
`899` (`bo_grounding`=120), and `platform/scripts/seed/asset_registry_seed.ts` (all NULL,
omitted from `ON CONFLICT DO UPDATE SET`).

#### Tests

`platform/src/lib/build/__tests__/plan.test.ts:152-169` is the **only behavioural assertion**
(`toBe(180)` from three 60-second in-memory fixtures; `toBeNull()` when any is null).
`platform/tests/unit/migrations/nirmana_l1_estimated_seconds_rebaseline{,_2}.test.ts` assert
migration **SQL file text** by regex and never touch a database. ~14 further files use the
field only in fixtures.

#### Implicit carry, orchestrator, MCP, DDL — bounded absences

* **`SELECT *` implicit carry: none.** No `SELECT * FROM asset_registry` and no
  `.from('asset_registry')` exists in the scope above. Every read enumerates its columns.
* **Orchestrator: no live caller found within scope**, where scope is every `.py` under
  `platform/python-sidecar/`, specifically including `pipeline/orchestrator/asset_runner.py`,
  `runner.py`, `global_runner.py`, `main.py`, `db.py`, `events.py`, `staleness.py`, `locks.py`,
  `dag_edge_guard.py`, `provenance.py`, `provenance_inventory.py`, `service_probes.py`,
  `output_digest.py`, `birth_params.py`, `kala_derivation_completeness_guard.py`,
  `writers/**` and `run_heavy_writer_standalone.py`. Zero matches on all six spellings.
  What the orchestrator *does* read from `asset_registry`: `has_writer` (`runner.py:190`),
  **`writer_timeout_seconds`** (`runner.py:741`, documented at `:539` as "per-writer watchdog
  budget" — **this**, not `estimated_seconds`, is the real time budget), `depends_on`
  (`asset_runner.py:63,:268`), `count_sql` (`:491`), `integrity_check_sql` (`:1031`),
  `target_floor` (`:1091`), `has_substeps` (`:1122`), `health_probe` (`service_probes.py`).
* **MCP: no live caller found within scope** `platform-mcp/{src,test,scripts,resources}/`.
  Positively verified: the `asset_registry_all` / `_l0` tools
  (`platform-mcp/src/tools/l0_brahmagyan.ts:169-215`) delegate to
  `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/asset_registry_all.ts:155-158`,
  whose SELECT list does **not** include the column.
* **DDL: no constraint, trigger, view, or generated column depends on it.** The column is
  declared at `platform/supabase/migrations/167_asset_registry.sql:25` as plain nullable
  `int` — no `NOT NULL`, no `DEFAULT`, no `CHECK`, not `GENERATED`. No `ALTER TABLE
  asset_registry` touches it. **Independently confirmed at the live authority**, not only in
  migration files: `information_schema.columns` reports `estimated_seconds | integer | YES`
  (nullable), and **35 `asset_registry` rows already carry NULL**, so a NULL is an ordinary,
  already-occurring state for this column — not a new one.

### §5.4 The finding that decides the retirement

`estimateSeconds()` (`plan.ts:399-407`) is a working whole-plan estimator whose result is
**shadowed or dropped at every one of its three callers**. On the only route that renders an
ETA, `plan/route.ts` computes the registry sum at `:87`, then computes
`PERCENTILE_CONT(0.5) … build_run_assets … state='complete'` at `:123-143`, then writes
`estimated_seconds` **after** `...buildPlan` in the response literal at `:153-158` so the
median wins. Verified by reading both files at the authority.

So the situation is:

1. The column's **value** is a stale snapshot of `ceil(median of build_run_assets)`.
2. The only surface that could show a user an ETA **recomputes that exact median live**, from
   the same table, and ignores the column.
3. No migration in version control ever wrote a `ka_*` value, and the seed writes NULL.
4. The statistic itself measures the wrong population — the no-op mode (§5.1, §3.2).

The column is therefore a **cached copy of a query its only consumer already runs**, taken
at an unrecorded time, by an unrecorded process, over a contaminated population. Seven
migrations across three campaigns — two of them titled "re-baseline" — have been carefully
maintaining the accuracy of a value nothing reads.

**This is a §N.8 Earned-Signal case.** Asking the §N.8 question directly — *"what does this
signal claim, and what code path would have to run and fail for it to correctly read false?"*
— the answer is that **no code path could**: nothing consumes it, so nothing can detect that
it is wrong. Under §N.8 the signal is null, not green.

### §5.5 Retirement specification — the exact change, for the native to rule on

**NOT APPLIED. Phase 0 changes nothing.** This is the specification a later phase would execute.

**Recommendation: set `estimated_seconds` to NULL for all `ka_*` rows** (F28 null-worthy), and
**separately decide** whether to wire the column to a real detector or drop it entirely.

#### R1 — the migration (authored, not applied)

`platform/migrations/<next>_kala_estimated_seconds_null_f28.sql`:

```sql
-- F28: `asset_registry.estimated_seconds` for ka_* rows is a stale, unattributed
-- snapshot of ceil(median(build_run_assets duration WHERE state='complete')) over a
-- population contaminated by no-op completions. Its only live consumer
-- (platform/src/lib/build/plan.ts:399-407) has its result shadowed at every caller by
-- a fresh recomputation of that same median (plan/route.ts:123-143,156).
-- Per CLAUDE.md §N.8 a signal with no detector behind it is null, not green.
-- Evidence: KALA_COST_PROFILE_v1_0.md §5.
UPDATE asset_registry
   SET estimated_seconds = NULL
 WHERE asset_id LIKE 'ka\_%'
   AND estimated_seconds IS NOT NULL;
-- Expected: 23 rows (22 active + the retired ka_gochara_sweep).
```

Reversal block, for the migration's own rollback record — the exact current values:
```
ka_avadhi 14 · ka_bhavishya_lekha 1 · ka_dasha_kala 2 · ka_gochara 1 ·
ka_gochara_resonance 1 · ka_gochara_sweep 1000 · ka_gochara_v3_century_materialize 614 ·
ka_graha_sancara 1 · ka_jivana_parva 1 · ka_kala_darshana 1 · ka_kalasutra 33 ·
ka_kota_chakra 3 · ka_kshetra 237 · ka_moorti_nirnaya 3 · ka_muhurta_seva 1 ·
ka_sangam 463 · ka_sudarshana_varsha 2 · ka_taranga 23 · ka_tithi_pravesha 3 ·
ka_tulana 1 · ka_vedha_gochara 4 · ka_vighnakara 14 · ka_yojaka 36
```

Note the `AND estimated_seconds IS NOT NULL` guard: per migration 690's own documented
hazard, `=` comparisons against this column are NULL-unsafe, so the guard uses a form that
is correct when the value is already NULL (idempotent re-run).

#### R2 — the one code change the NULL forces

`platform/src/lib/build/plan.ts:399-407` is **all-or-nothing**: one NULL in the plan collapses
the whole sum to `null`. After R1, **any** plan containing a Kāla asset — including a mixed
L1+L3 plan — returns `BuildPlan.estimated_seconds = null`.

Today that is invisible, because all three callers discard the value. It becomes visible the
moment anyone removes the median override at `plan/route.ts:138-143` or starts returning
`buildPlan.estimated_seconds` from `runs/route.ts`. **The native should rule on one of:**

* **(a) Leave `plan.ts` unchanged.** The all-or-nothing NULL is then the *correct* behaviour —
  "I do not know this plan's duration" is an honest null, which is what §N.7 item 6 asks for.
  *Recommended.* No code change at all; R1 alone.
* **(b) Delete `estimateSeconds()` and `BuildPlan.estimated_seconds` entirely**, and have
  `plan/route.ts` return only its `build_run_assets` median. This removes the shadowing and
  the dead computation. Requires deleting `plan.ts:60`, `:96`, `:399-407`, `:536`, `:544`,
  `:560`, `:568`, `:605`, `:613`, `:622`, and updating `plan.test.ts:152-169`.
* **(c) Wire the column to a real detector** — recompute it from `build_run_assets` on a
  schedule, **excluding no-op runs**. This is the only option that makes the column mean
  something, and it is the largest: it needs a defensible no-op predicate first (see D1 below),
  and it would still duplicate a query the consumer already runs live.

#### R3 — what would then have to be NULL, and what would break

**Nothing breaks.** Verified file by file:

| Surface | Effect of NULL |
|---|---|
| DB layer | **None.** Nullable `int`, no `NOT NULL`/`CHECK`/trigger/view/generated column; 35 rows are already NULL. |
| `plan.ts:403` | `BuildPlan.estimated_seconds` → `null` for any plan containing a `ka_*` asset. **The only behaviour change in the codebase.** No `NaN` possible — the null guard fires before arithmetic. |
| `plan/route.ts` | **No observable change** — overwritten at `:156` by the median. Response byte-identical. |
| `runs/route.ts`, `recalibrationEnqueue.ts` | **No observable change** — field never read. |
| `PlanModal.tsx`, `BuildConfirmModal.tsx`, `AssetRow.tsx` | **No change** — they read the median, not the registry. (`BuildConfirmModal:99` is `!= null`-guarded; it omits the sentence rather than printing `NaN`.) |
| `registry/route.ts`, `atlas/page.tsx` | JSON carries `null` for `ka_*`; **no component reads the field**. No `NaN`, no `undefined` rendered. |
| `clear/route.ts`, `clear/execute/route.ts` | **No change**; `preview_hash` does not cover the column, so **no `HASH_MISMATCH` 409 is possible**. |
| `cascade/route.ts`, `cascade-preview/route.ts` | **No change** — already hardcode `null`. |
| Python orchestrator | **No change** — does not read the column. `writer_timeout_seconds` is untouched. |
| MCP | **No change** — not in any tool's SELECT list. |
| Tests | **Zero failures.** Every value assertion is against an in-memory fixture or against migration SQL text; no test reads `asset_registry` live and asserts a `ka_*` duration. |

#### R4 — what this specification explicitly does NOT authorize

* It does **not** authorize changing any other layer's `estimated_seconds`. The same defect
  very likely applies to `bg_*`, `ga_*`, `bo_*` and `mi_*` (41 of 94 non-null rows already
  differ from `ceil(live median)`, i.e. are stale by the column's own implied rule), but this
  phase measured Kāla and should rule on Kāla.
* It does **not** authorize touching `writer_timeout_seconds`. That column **is** read by a
  live detector (`runner.py:741`) and is the real budget. Note for the record that
  `ka_kshetra`'s value (86,400 s) is the registry's own honest statement of that asset's
  scale, and it disagrees with `estimated_seconds` (237 s) by **365×** in the same row.
* It does **not** authorize any optimization of any `ka_*` asset. See §6.

#### D1 — the open question a later phase must answer first

If the native chooses **(c)**, a no-op predicate is required, and it does not exist yet.
`build_run_assets` has `disposition` and `output_changed` columns — but they are **NULL for
676 of 708** `ka_*` `complete` rows (populated only: `build`/`true` 17, `skip_no_delta`/`false`
12, `build`/`false` 3). Until that instrumentation has backfilled, **no statistic over
`build_run_assets` can separate a real build from a no-op**, and any re-baselined
`estimated_seconds` would reproduce exactly the defect this section documents.

