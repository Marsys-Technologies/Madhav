---
canonical_id: W2_DETERMINISM_PRECHECK
version: 1.0
status: EVIDENCE-RECORD
campaign: ṢAḌ-DARŚANA
wave: W2
lane: w2-determinism-precheck
date: 2026-08-01
base_commit: 7190187c
base_branch: shad-darshana/integration
author: Claude Code (w2-determinism-precheck lane)
supersedes: null
---

# W2 Determinism Pre-Check — local evidence record

**Purpose.** A PRE-CHECK for the next session's Gate-W2 integration run, **not the gate
itself**. The question asked: now that the `N_e` priors have merged (PR #1007 →
integration @ `7190187c`), does the `ka_kshetra` field build actually produce rows, and
is it deterministic?

**Verdict in one line.** Steps 1–2 are **PROVEN** — the seed writer produces exactly 6 rows
at the reserved coordinate, and the 6/21 class split is confirmed arithmetically against
the live ontology. Steps 3–5 (the actual field build and the determinism double-run) were
**NOT REACHED** inside the time budget. One **latent determinism defect** was found by code
reading and is documented in §5 — it is directly in scope for this lane's question and
should be dispositioned before more `prior_version` sets land.

**No production code was changed.** This branch contains this report file only.

---

## 1. Environment — how the throwaway DB was stood up

Docker was **unavailable** (daemon not running: `Cannot connect to the Docker daemon at
unix:///Users/Dev/.docker/run/docker.sock`). `pg_tmp` is not installed. Fallback used:
Homebrew `postgresql@17` binaries with a scratch `initdb` cluster.

| Item | Value |
|---|---|
| Server | PostgreSQL 17.10 (Homebrew), aarch64-apple-darwin25.6.0 |
| Data dir | `<scratchpad>/pgdata` (throwaway, `--auth=trust`) |
| Port | 55432, `listen_addresses=127.0.0.1` |
| Database | `madhav_precheck` |

### TRAP for the next session — Unix socket path length

`initdb` into the session scratchpad succeeds, but `pg_ctl start` **fails** if the socket
directory defaults to the data dir, because the scratchpad path exceeds Postgres's limit:

```
LOG:  Unix-domain socket path ".../scratchpad/pgdata/.s.PGSQL.55432" is too long (maximum 103 bytes)
WARNING:  could not create Unix-domain socket in directory ".../scratchpad/pgdata"
FATAL:  could not create any Unix-domain sockets
```

Fix that worked — put the socket somewhere short with `-k`:

```bash
pg_ctl -D "$PGD" -o "-p 55432 -k /tmp/pgs55432 -c listen_addresses=127.0.0.1" -l "$PGD/server.log" start
```

This costs ~10 minutes if hit cold. Budget for it or pre-create `/tmp/pgs<port>`.

---

## 2. Migrations applied

The repo has **two** migration directories, both read by `migrate.ts`, de-duplicated by
**filename** (see `platform/supabase/migrations/README.md`):

| Directory | Files |
|---|---|
| `platform/migrations/` | 154 |
| `platform/supabase/migrations/` | 224 |
| **Unique by filename** | **378** |

All 378 were applied in filename-sorted order via `psql -v ON_ERROR_STOP=1`, one file per
invocation, continuing past failures:

| Outcome | Count |
|---|---|
| Applied OK | **251** |
| Failed | **127** |
| Tables in `public` afterwards | **179** |

**The 127 failures were not individually classified** — that is an honest gap in this
record, not a claim that they are benign. What *was* verified is that every object steps
1–2 depend on landed correctly (§3). See §6 for why this matters to step 3.

### Objects required by this lane — all present

All **21** `kala_field_*` tables exist:

```
kala_field_kinematics · kala_field_primitives · kala_field_promise_nodes
kala_field_promise_edges · kala_field_routes · kala_field_clocks
kala_field_boundaries · kala_field_weights · kala_field_weight_versions
kala_field · kala_field_salience · kala_field_windows
kala_field_snapshots · kala_field_provenance · kala_field_null
kala_field_skill · kala_field_gof
```

(plus `asset_registry`, `chart_facts`, `brahma_class_priors`, `brahma_event_ontology`.)

**Migration 522 landed intact** — `brahma_class_priors` carries both new columns and the
enforcing CHECK:

```
prior_basis | text
source_ref  | text
Check constraints:
  "brahma_class_priors_lifetime_basis_ck" CHECK (fact_kind <> 'lifetime_count_per_100y'::text
    OR (prior_basis = ANY (ARRAY['demographic_structural'::text,'derived_identity'::text]))
       AND source_ref IS NOT NULL)
PK: (prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)
```

---

## 3. STEP 2 — `bg_class_lifetime_counts` writer run: **PASS**

Invoked `brahmagyan.l0_class_lifetime_counts.seed_class_lifetime_counts(conn, autocommit=True)`
against the local DB.

Writer log line, verbatim:

```
[L0/class_lifetime_counts] upserted 6 rows at fact_kind=lifetime_count_per_100y
prior_version=ne_v01; 21 ontology class(es) NOT seeded (no Tier N-i source —
ka_kshetra skips each with no_class_prior_row)

RESULT: {'brahma_class_priors': 6, 'classes_not_seeded': 21}
```

Rows as stored, read back at the reserved coordinate:

| prior_version | signal_type_class | fact_kind | src_sub | trad | class_prior | prior_basis | source (head) |
|---|---|---|---|---|---|---|---|
| ne_v01 | childbirth | lifetime_count_per_100y | `*` | `*` | 3.09 | demographic_structural | International Institute for Population Sciences … |
| ne_v01 | foreign_settlement | lifetime_count_per_100y | `*` | `*` | 0.0129 | demographic_structural | United Nations, Dept of Economic and Social … |
| ne_v01 | marriage | lifetime_count_per_100y | `*` | `*` | 0.984 | demographic_structural | Office of the Registrar General & Census Comm… |
| ne_v01 | relocation | lifetime_count_per_100y | `*` | `*` | 0.376 | demographic_structural | Office of the Registrar General & Census Comm… |
| ne_v01 | separation | lifetime_count_per_100y | `*` | `*` | 0.00806 | demographic_structural | Office of the Registrar General & Census Comm… |
| ne_v01 | surgery | lifetime_count_per_100y | `*` | `*` | 0.356 | demographic_structural | Wolters Kluwer / IJS Publishing Group — Int… |

Assertions, all confirmed:

- `count(*) WHERE fact_kind='lifetime_count_per_100y' AND prior_version='ne_v01'` = **6** ✅
- All 6 rows carry `prior_basis='demographic_structural'` and a non-null `source_ref` ✅
  (i.e. the ADJUDICATION-2 CHECK is satisfied by real data, not vacuously)
- `prior_version` is the zero-padded `ne_v01` as the migration requires ✅
- All 6 sit at `source_subsystem='*'`, `signal_tradition='*'` ✅

### The 6/21 split is confirmed against the live ontology

`select count(*) from brahma_event_ontology` → **27**.

**6 seeded + 21 unseeded = 27.** The expected disposition ("6 classes compute, 21 skip with
`no_class_prior_row`") is therefore confirmed *arithmetically* and the writer's own
`classes_not_seeded=21` is a measured query result, not an assumption. What this does
**not** prove is that `ka_kshetra` actually emits those skips at runtime with exactly that
reason string — that requires step 3, which was not reached.

### Coordinate match — reader vs. writer (verified by reading, not by running)

The N_e read, `platform/python-sidecar/services/ka_kshetra/stage4_field.py:711-720`:

```sql
SELECT prior_version, class_prior
  FROM brahma_class_priors
 WHERE fact_kind = 'lifetime_count_per_100y'
   AND signal_type_class = %s
 ORDER BY prior_version DESC
 LIMIT 1
```

The seed write, `platform/python-sidecar/brahmagyan/l0_class_lifetime_counts.py:722-741`,
inserts `signal_type_class = r.event_class_id`, `fact_kind = 'lifetime_count_per_100y'`,
`source_subsystem='*'`, `signal_tradition='*'`.

**The coordinates match** on both predicates the reader actually uses. The previously
universal `ClassSkipped(e, 'no_class_prior_row')` (raised at `stage4_field.py:626` via
`require_baseline`, `stage4_field.py:614`) will therefore now be bypassed for these 6
classes. This is the mechanism by which the field build should become non-empty — but see
the defect in §5, which lives in exactly this query.

---

## 4. DETERMINISM VERDICT: **NOT ESTABLISHED (not reached)**

No double-run was performed. **No determinism claim is made in either direction.** The
next session must treat determinism as *untested*, not as *presumed passing*.

Groundwork done for the next session: `kala_field_snapshots` **exists** as a table, so a
snapshot/hash-replay surface is present in the schema. Whether the writer populates a real
hash or leaves it stubbed was **not** determined — resolving that is the first task of
step 4 (see §7).

---

## 5. DEFECT FOUND — latent non-determinism in the N_e read

**Severity:** low today, **rising the moment a second prior set or tradition lands.**
Directly in scope for a determinism pre-check. **Documented, not fixed**, per lane scope.

**File:** `platform/python-sidecar/services/ka_kshetra/stage4_field.py`
**Function:** `load_class_lifetime_count` (defined at **line 684**)
**Docstring:** lines **688–691**
**Offending SQL:** lines **711–720**

The docstring states the read is taken at the coordinate

```
fact_kind = 'lifetime_count_per_100y'
signal_type_class = <event_class>
source_subsystem = '*'  ·  signal_tradition = '*'
```

but the SQL **filters only on `fact_kind` and `signal_type_class`**. The
`source_subsystem='*'` and `signal_tradition='*'` predicates the docstring promises are
**absent from the query**.

**Why it is harmless right now:** the seed writes exactly one row per class, at
`('*','*')`. With one candidate row per class, `LIMIT 1` is unambiguous.

**Why it is a determinism bug in waiting:** the PK is
`(prior_version, signal_type_class, fact_kind, source_subsystem, signal_tradition)`, so
multiple rows for the *same class and same `prior_version`* may legally coexist at
different `source_subsystem` / `signal_tradition` values. `ORDER BY prior_version DESC
LIMIT 1` then has **no tiebreaker** among them — Postgres may return any of them, and the
choice can change between runs (physical order, plan change, autovacuum). That is a
silently non-deterministic `N_e`, which would feed straight into the hazard and break
hash-replay while every row involved looks individually correct. It would also be a
*wrong-value* bug, not merely an unstable one.

**Repro sketch (not executed):** seed a second row at
`('ne_v01', 'marriage', 'lifetime_count_per_100y', 'some_subsystem', 'some_tradition')`
with a different `class_prior`, then call `load_class_lifetime_count(conn, 'marriage')`
repeatedly across sessions and/or after `VACUUM FULL brahma_class_priors`.

**Suggested disposition (for the owning lane, not applied here):** add the two equality
predicates the docstring already promises, so query and contract agree:

```sql
   AND source_subsystem = '*'
   AND signal_tradition = '*'
```

and/or make the ordering total (`ORDER BY prior_version DESC, source_subsystem, signal_tradition LIMIT 1`).
Cheapest while only 6 rows exist and nothing depends on the current behaviour.

**Secondary observation (documentation drift, no action needed beyond awareness):** the
same docstring's "HONEST GAP" paragraph still asserts *"this returns None for every class
until an L0 lane seeds the rows"*. As of `7190187c` that L0 lane **has** landed, so the
paragraph is now stale and reads as though the field were still universally empty. Worth a
comment refresh when the query above is touched.

---

## 6. NOT REACHED

Stated plainly, with no partial credit claimed:

- **Step 3 — seed upstream fixtures + run the `ka_kshetra` field build.** Not started. No
  per-stage-table row counts were collected. The claim "the 6 seeded classes compute and 21
  skip" is confirmed only *arithmetically* (§3), **never observed at runtime**.
- **Step 4 — determinism double-run.** Not started. See §4.
- **Step 5 — real `field_snapshot_id` (E5) wiring.** Not investigated.

**Known risk carried into step 3:** the 127 failed migrations were not classified. Steps
1–2 needed only `brahma_class_priors` + `brahma_event_ontology`, both of which landed
clean. A full `ka_kshetra` run touches many more upstream tables (`chart_facts`,
`chart_dashas`, `kala_*`, `bodha_*`), and **some of those may be among the 127 failures.**
The next session should classify the failure list *before* concluding that any empty
result from the field build is a code problem rather than a missing-schema artifact.
The failure list is reproducible by re-running the §2 loop.

---

## 7. Checklist for the next session (Gate-W2 integration run)

1. **Pre-create a short socket dir** (`mkdir -p /tmp/pgs55432`) and pass `-k` to `pg_ctl`,
   or start Docker. Saves ~10 min (§1).
2. **Classify the 127 migration failures** — at minimum, confirm every table `ka_kshetra`
   reads and writes exists before running it. Do this *first*; it disambiguates every
   downstream empty result.
3. **Re-run the §3 seed** (idempotent — `ON CONFLICT … DO UPDATE`) and re-assert 6 rows.
4. **Locate `ka_kshetra`'s test fixtures** — `platform/python-sidecar/tests/l3/ka_kshetra/fixtures.py`
   and `fake_db.py` exist; determine whether they fabricate against a fake in-memory DB or
   a real one, and reuse them rather than inventing fixture data.
5. **Run the field build for ONE chart.** Record rows per stage table, and capture the
   per-class disposition. **Assert the skip reason string is exactly `no_class_prior_row`**
   for the 21, and that the 6 seeded classes do **not** appear in the skip set.
6. **Determine whether `kala_field_snapshots` carries a real content hash** or a stub. If
   real, use its own mechanism for step 4; if stubbed, fall back to row-level dumps
   `ORDER BY` natural key.
7. **Double-run and diff.** Byte-identical or report the diff.
8. **Disposition the §5 defect** before any second `prior_version` / tradition is seeded.

---

*End of W2_DETERMINISM_PRECHECK v1.0 — evidence record, ṢAḌ-DARŚANA W2 lane
`w2-determinism-precheck`, against integration `7190187c`. Steps 1–2 proven; steps 3–5 not
reached; one latent determinism defect documented at `stage4_field.py:711-720`.*
