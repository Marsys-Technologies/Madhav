---
artifact: WP6_LEDGER
version: "1.0"
status: WP6_COMPLETE
date: 2026-09-23
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §4.3, §4.4, §4.7, §5.5, §6.4 (Clear);
          WP1_CONTRACTS.md §1.2, §3.1, §3.2, §4.1, §5.2, §5.4 (schema source, lifted + refined);
          GOCHARA_RULING_SHEET_v1_0.md N-7 (conditions incl. publish-refusal), N-10
branch: l3/gochara-autonomous-wp0-7 @ /Users/Dev/madhav-l3/gochara-wp0-7
database: postgresql://wp6:disposable@localhost:55433/wp6 (docker gochara-wp6-disposable) — ONLY
---

# WP6 — Ledger, coverage, publication: implementation report

## 1. Deliverables

| item | path |
|---|---|
| Migration (one file, four relations) | `platform/migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql` (renumbered 1072 → 1076 → 1081; E-007 addendum) |
| Writer layer | `platform/python-sidecar/services/gochara_kernel/ledger.py` |
| Package init (created when absent; since replaced by the WP3a sibling — left untouched) | `platform/python-sidecar/services/gochara_kernel/__init__.py` |
| Tests | `platform/python-sidecar/tests/l3/gochara/test_wp6_ledger.py` |
| Test fixture (schema create/drop on the disposable DB; NOT_RUN skip) | `platform/python-sidecar/tests/l3/gochara/conftest.py` — **shared**: WP6's `wp6_schema`/`conn` fixtures merged below the WP3a sibling's F-14 `.se1` harness (their content untouched) |
| This report | `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/WP6_LEDGER.md` |

## 2. Migration numbering — no collision

Both directories of the shared global sequence were listed, plus `git status`
for untracked concurrent files:

- `platform/migrations/` — highest 10xx: **1070** (`1070_data_plane_builder_orchestrator_grants.sql`, applied) and **1071** (now `1080_nirmana_l3_gochara_resonance_target_resolution_state.sql`, untracked, owned by the concurrent WP3c agent — not touched).
- `platform/supabase/migrations/` — highest 10xx: 1041 (`1035`/`1036`/`1038`/`1041` present; 1033–1036 are must_not_touch and were not modified).
- `git status --short` at run start showed exactly one untracked migration (1071, sibling's).

**1072 is the first free block; this run used exactly one file: 1072.**

## 3. Schema as applied

Applied with `psql -v ON_ERROR_STOP=1` against a fresh schema (DROP IF EXISTS
first in test setup only; the file itself is idempotent — BEGIN/COMMIT,
`CREATE … IF NOT EXISTS`, idempotent `DROP TRIGGER IF EXISTS` + `CREATE OR
REPLACE FUNCTION`). Applied twice in verification to prove idempotency.

Four relations, per WP1_CONTRACTS.md §1.2 / §3.1 / §4.1 / §5.2, with these
deliberate refinements (each recorded in the migration header):

1. `kala_gochara_contacts.input_generation_vector_id` is **UUID** with a real
   FK to `kala_gochara_publication(manifest_id)` — WP1 §3.1 drafted it TEXT,
   but TEXT cannot FK to a UUID primary key, and WP1's own join-ability
   argument for `convention_id` applies equally here.
2. `kala_gochara_convention` is insert-only **by trigger**
   (`kala_gochara_convention_immutable`, WP1 §1.2: "WP6 enforces: no
   UPDATE/DELETE") — enforced in the database, not just the writer. Verified:
   an UPDATE raises.
3. N-10 one-published invariant: partial unique index
   `kala_gochara_publication_one_published (chart_id, generation) WHERE
   status='published'`, alongside the plain `UNIQUE (chart_id, generation)`
   (candidate rebuilds replace the candidate in place; two published
   manifests never coexist).
4. `(chart_id, generation)` scope on all three owned relations is served by
   PK/UNIQUE leading columns (contacts PK, coverage PK, publication UNIQUE);
   the explicit serving indexes created on top are the ones the P-4 read
   shapes use.

CHECK constraints from WP1, all verified present in `pg_constraint`:
`comparable_with` 4-value enum, `status` 4-value enum, `partition_kind`
3-value enum, `target_resolution_state` 3-value enum, `branch`,
`truncated_at_horizon` (with NULL allowed). FKs: contacts/coverage →
convention; contacts → publication(manifest_id); publication → convention.
`target_resolution_state` is deliberately absent here (it belongs to the
sibling's 1071 on `gochara_resonance_map`, per the task brief).

Indexes (all confirmed live in `pg_indexes`):
`idx_kgc_serve_p4 (chart_id, generation, body, relation, t_exact) INCLUDE
(target_type, target_ref, contact_id, independence_group, completeness_state,
comparable_with, target_resolution_state)`; `idx_kgc_independence
(chart_id, generation, independence_group)`; `idx_kgc_target (chart_id,
generation, target_type, target_ref)`; `idx_kgcov_chart (chart_id,
generation, partition_kind)`; `idx_kgpub_chart (chart_id, status,
generation)`; plus the PK/UNIQUE/partial-unique set above.

## 4. Writer layer (`services/gochara_kernel/ledger.py`)

psycopg 3, pure SQL, no ORM; no function COMMITs (the caller owns the
transaction — the crash/resume gate depends on it). API: `register_convention`,
`write_contacts`, `write_coverage`, `publish_candidate`, `publish`,
`supersede`, `rollback`, `clear_generation`, `compute_contact_id`,
`reference_digest`, `CLEAR_OP_ORDER`, `PublishedGenerationRefusal`.

- **contact_id** implemented locally per WP1 §3.2 (canonical sorted-keys JSON,
  sha256, minute-floor UTC quantization, `fact:`/`ref:` identity prefix,
  `method_version` hashed in). A sibling module `services/gochara_kernel/ids.py`
  (WP3a) now exists; the test cross-check requires **byte-identical ids**
  between the two implementations on a sample episode — PASS
  (`sha256:e3420115…`). The duplication is noted in `ledger.py` for
  consolidation; `ledger.py` prefers `.ids` when importable.
- **Refusal**: every row-mutating entry point checks the manifest first and
  raises `PublishedGenerationRefusal` against a `published` generation (N-7).
- **Clear** (`clear_generation`): C-1 dependency order over the two OWNED
  relations — coverage, then contacts — and exposes
  `CLEAR_OP_ORDER = (kala_gochara_coverage, kala_gochara_contacts,
  kala_gochara_windows)`; the windows DELETE is the cockpit/projection
  owner's op and is deliberately not executed here. Clear of a `published`
  generation is refused (release-authority rollback path, plan §6.4).
- `near_station` honesty: an episode flagged `station_unresolved` must carry
  `completeness_state='unqualified'` or the writer raises (WP1 §3.1).
- Input generation vector per WP1 §5.3: `reference_digest()` pins **content
  digests** (sha256 over the canonical row set) for the small reference
  tables, not counts.

Import-isolation note: the tests load `ledger.py` by file path (importlib),
not via the package, because the WP3a sibling owns `gochara_kernel/__init__.py`
and its imports; WP6 DB tests must not depend on that package's transient
state. When the package is complete the module still prefers `.ids`.

## 5. Lifecycle gates — all PASS

Command:
`cd platform/python-sidecar && /Users/Dev/madhav-l3/gochara-wp0-7/.venv/bin/python -m pytest tests/l3/gochara/test_wp6_ledger.py -q`
Result: **9 passed** (whole `tests/l3/gochara/` directory: **68 passed, 1
skipped, 6 failed — the 6 failures are all in the WP3a sibling's
`test_wp3a_kernel.py` episode-geometry golden tests, which import none of the
WP6 code; they are the sibling's in-progress state, verified independent of
this run). If the disposable DB is unreachable the WP6 module skips NOT_RUN
(fixture `wp6_schema`).

| # | gate | test | result |
|---|---|---|---|
| 0 | convention idempotent; insert-only trigger fires | (in test 1's setup + crash test) | PASS |
| 1 | crash mid-write, resume cleanly | `test_crash_mid_write_resume_cleanly` — half the rows inserted then `RuntimeError`; transaction abort leaves **0** partial rows; full re-run yields ids byte-identical to `compute_contact_id` | PASS |
| 2 | horizon extension without duplicate contacts | `test_horizon_extension_no_duplicate_contacts` — [2020,2025) build extended to [2030]; all 10 first-build ids unchanged and present, 5 new ids, 15 rows, no duplicates; candidate manifest rebuilt **in place** (same manifest_id) | PASS |
| 3 | upstream correction propagation | `test_upstream_correction_propagation` — changed partition's contacts replaced (old ids absent, new disjoint), untouched partition's ids identical; `input_generation_vector` records the new resonance `computed_at`/row_count | PASS |
| 4 | concurrent read during a write | `test_concurrent_read_during_write` — writer's uncommitted candidate rows invisible to a READ COMMITTED reader (0 rows), prior published state fully visible (1 row); visible after commit | PASS |
| 5 | full rollback of a candidate | `test_full_rollback_of_candidate` — contacts 0, coverage 0, manifest `rolled_back` (row retained, marked never deleted); superseded refuses re-rollback | PASS |
| 6 | **N-7 publish refusal** | `test_refuses_delete_then_insert_on_published` — `write_contacts`, `write_coverage`, and `publish_candidate` all raise `PublishedGenerationRefusal` against the published generation; contact ids and `content_digest` byte-identical after the attempts; the sanctioned rebuild under a new label `'4.1'` succeeds | PASS |
| 7 | **F-24 Clear leaves ZERO rows** | `test_clear_leaves_zero_rows` — after `clear_generation`: contacts 0, coverage 0, manifest `rolled_back`; `CLEAR_OP_ORDER` correct (coverage → contacts → windows-for-cockpit-owner); Clear of a published generation refused and data intact | PASS |
| 8 | ids stable under re-partitioning (§10 identity) | `test_contact_ids_stable_under_repartitioning` — same chart, same instants, two partitionings (split 2023 vs 2024, different t_in/t_out spans, generations 4.0/4.1) → identical contact_id sets; cross-implementation check vs WP3a `ids.py` byte-identical | PASS |
| 9 | storage + latency **measured** | `test_storage_and_latency_measured` + post-restart cold/warm run (§6) | PASS |

Reconciliation note (test 7 vs plan wording): the execution prompt asks that
Clear leave zero rows in "all three owned relations (contacts, coverage,
publication)" while plan §6.4 says the manifest is *marked* `cleared`/
`rolled_back`, not deleted. Implemented: **rows** in contacts and coverage go
to exactly zero; the publication row is retained with `status='rolled_back'`
(zero candidate/published state remains). WP1 §5.2's status enum has no
`cleared` value, so `rolled_back` is the coherent mark. The manifest row is
the audit anchor that makes the Clear reviewable (conjunct (k) of §6.3 is its
detector) — deleting it would defeat the detector.

## 6. Measured storage and serving latency (measured, not assumed)

Scale actually used: **20 synthetic charts × 10,000 contacts = 200,000
contact rows** (+ 60 coverage partitions + 20 manifests + 1 convention row).
The plan's §4.3 steady-state estimate is 2–5×10⁵ rows per chart; this run
used 10⁴/chart (~2–5% of that range) on the disposable container within its
time budget — state this when extrapolating. Synthetic chart ids
`00000000-0000-4000-8000-0000000000NN` (wp6-synth tagged); no real chart id
anywhere.

Environment: PostgreSQL 16.15 (docker, aarch64), disposable container,
single connection, `executemany` batch inserts.

### Storage (`pg_total_relation_size`, after load + ANALYZE)

| relation | total | heap | indexes |
|---|---|---|---|
| kala_gochara_contacts (200k rows) | 308,207,616 B (293.9 MiB) | 182,091,776 B (173.6 MiB) | 126,042,112 B (120.2 MiB) |
| kala_gochara_coverage (62 rows) | 98,304 B | 32,768 B | 32,768 B |
| kala_gochara_publication (34 rows) | 139,264 B | 40,960 B | 65,536 B |
| kala_gochara_convention (1 row) | 32,768 B | 8,192 B | 16,384 B |

Per-row economics, contacts: **≈910 B/row heap** (the WP1 row is wide: ~40
columns incl. two jsonb and three TEXT sha256 ids), **≈1.54 kB/row with all
four contacts indexes**. Index split at 200k rows: `idx_kgc_serve_p4`
82.9 MB, `kala_gochara_contacts_pkey` 32.5 MB, `idx_kgc_independence` 9.0 MB,
`idx_kgc_target` 1.7 MB. Extrapolated to the plan's 5×10⁵ rows/chart: ≈0.45
GB heap, ≈0.77 GB indexed per chart — the plan's "[I] 100–200 MB per chart at
~400 B" estimate is optimistic on bytes/row by ~2.3× (measured 910 B vs
assumed 400 B); the design is unaffected but the cost model should take the
measured figure. Load throughput: 200k rows in **9.9 s** (≈20k rows/s
single-connection batched, contacts+coverage+manifest per chart).

### Serving-query latency (EXPLAIN ANALYZE, planning + execution ms)

**Cold** measured after `docker restart gochara-wp6-disposable` (genuine empty
buffer cache; the restart is disclosed — it briefly drops all connections to
this disposable container). **Warm** = steady-state repeat.

| query shape | cold (plan + exec) | warm (plan + exec) | plan |
|---|---|---|---|
| P-4: chart+generation+body+relation, `t_exact` range (187 rows) | 0.595 + 0.510 | 0.023–0.038 + 0.061–0.072 | **Index Only Scan on `idx_kgc_serve_p4`, heap fetches 0** |
| `independence_group` lookup (2 rows) | 0.022 + 0.041 | 0.014–0.026 + 0.014–0.018 | Index Scan on `idx_kgc_independence` |

Both serving shapes are sub-millisecond cold and ~0.07 ms warm at 200k rows;
the covering index does its job (zero heap fetches on the P-4 shape).

## 7. Safety compliance

- Only the disposable DSN was used; no credentials in any file (DSN appears
  only as the documented disposable URL in conftest, overridable by env).
- All test data uses synthetic wp6-synth UUIDs; no real chart id.
- No `must_not_touch` path touched; migration 1080 (sibling, renumbered 1071 → 1075 → 1080) untouched; no
  commits, nothing staged; `kala_gochara_authority` not touched (WP10-only
  authority flip).
- One deliberate disposable-container restart (for the cold measurement) —
  disclosed above; schema/data re-verified intact afterwards.

## 8. Open items for follow-on owners

- `services/gochara_kernel/ids.py` (WP3a) and `ledger.py` both implement
  WP1 §3.2; verified byte-identical today, but consolidate to one owner.
- `content_digest` currently hashes contacts+coverage canonical rows; when
  the projection starts writing `kala_gochara_windows` (WP7+), extend
  `row_counts["windows"]` and the digest inputs to the third relation.
- Cockpit C-1 owner: `CLEAR_OP_ORDER` is exported for the
  `EXPLICIT_CLEAR_OPS['ka_gochara']` entry; the refusal condition for the
  chart's authoritative generation is implemented here as the published /
  not-candidate refusal — mirror it in the cockpit spec.
