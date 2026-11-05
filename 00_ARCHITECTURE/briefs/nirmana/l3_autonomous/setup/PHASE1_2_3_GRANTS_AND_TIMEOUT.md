---
artifact: PHASE1_2_3_GRANTS_AND_TIMEOUT
version: "1.0"
status: AUTHORED_NOT_YET_APPLIED_TO_PRODUCTION
phase: L3 Kāla pre-elevation setup, Phase 1.2 / 1.2b / 1.3
migrations: [1073, 1074]
measured_on: 2026-09-22
measured_against: production (READ-ONLY, as amjis_app) + disposable PostgreSQL 15.17
production_applied: false
---

# Phase 1.2 / 1.3 — Builder read grants and an explicit builder timeout

Two migrations against the `data_plane_builder` identity, one register amendment.

| # | Item | Artifact | State |
|---|---|---|---|
| 1.2 | Builder read grants | `platform/migrations/1073_data_plane_builder_l3_reference_read_grants.sql` | authored, proven on disposable PG, **not applied to production** |
| 1.2b | Undeclared upward read | `W0_REGISTER_AMENDMENT_001_KSHETRA_PHALA_RECTIFICATION.md` (this directory) | filed, awaiting fold-in by the W0 register owner |
| 1.3 | Explicit builder timeout | `platform/migrations/1074_data_plane_builder_explicit_session_timeouts.sql` | authored, proven on disposable PG, **not applied to production**, and carries a **DBA precondition** (§6) |

**Production is read-only for this session.** Nothing here was applied to production. Production
application happens at deploy via `platform/scripts/migrate.ts` and is therefore **not yet
verified**. §6 raises a precondition that must be satisfied before that deploy, or 1074 will
fail.

---

## 1. Measured privilege gaps (production, read-only, as `amjis_app`, 2026-09-22)

```sql
SELECT t, has_table_privilege('data_plane_builder', t, 'SELECT') FROM unnest(ARRAY[...]) t;
```

| table | builder SELECT | `amjis_app` SELECT | owner | RLS | rows |
|---|---|---|---|---|---|
| `public.bg_transit_moorti` | **f** | t | `amjis_app` | f | 27 |
| `public.bg_synthetic_cohort` | **f** | t | `amjis_app` | f | 10,000 |
| `public.bg_synthetic_cohort_md` | **f** | t | `amjis_app` | f | 100,000 |
| `public.phala_rectification` | **f** | t | `amjis_app` | f | 370 (185 × 2 charts) |
| `public.kala_gochara_windows_archive_20260805` | **f** | t | `amjis_app` | f | 35,620 (2 charts) |

The builder has **no** privilege of any kind on any of them — the full
`SELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES` matrix is `f` in all 30 cells.

**Why.** `role_orchestrator` holds `SELECT/INSERT/UPDATE/DELETE` on every one of these tables.
`data_plane_builder` is not a member of it — or of anything:

```sql
SELECT r.rolname FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid
  JOIN pg_roles g ON g.oid=m.member WHERE g.rolname='data_plane_builder';   -- 0 rows
```

The privileges exist; the identity is simply outside the role that has them. Migration 1070
restored the orchestrator *core* (`asset_registry`, `asset_provenance_receipts`,
`asset_freshness`, `charts`, `asset_output_digest_specs`) and did not reach the per-asset data
reads. 1073 closes exactly the three L3 needs.

---

## 2. Verb map — derived from actual source reads, with file:line

Grepped across `platform/`, `platform-mcp/`, `pipeline/` at this commit. Every L3 access is a
bare `SELECT`; `grep -c 'INSERT|UPDATE|DELETE' services/ka_kshetra/cohort_client.py` → **0**.

| table | verbs required | source evidence (file:line) |
|---|---|---|
| `bg_transit_moorti` | **SELECT** | `services/ka_moorti_nirnaya/writer.py:82-85` `_FETCH_MOORTI_TABLE_SQL` (`SELECT nakshatra_offset, moorti_name, quality_tier, phala_brief, classical_citation FROM bg_transit_moorti`) · executed `:169` in `_fetch_moorti_table` (`:164`) · called unconditionally from `KaMoortiNirnayaWriter.run()` `:195` |
| `bg_synthetic_cohort` | **SELECT** | `services/ka_kshetra/cohort_client.py:171` corpus fingerprint (count/digest) · `:317`, `:322` base-rate denominator/numerator · `:346`, `:365` md-joined variants · `services/ka_kshetra/writer.py:2304` `SELECT MAX(build_id::text)` (corpus pin for the snapshot hash) |
| `bg_synthetic_cohort_md` | **SELECT** | `services/ka_kshetra/cohort_client.py:179` corpus fingerprint · `:338` `JOIN bg_synthetic_cohort_md m ON m.synthetic_id = c.synthetic_id`, feeding `:346`/`:365` |

`services/ka_kshetra/stage1_symbolization.py:236` also names `bg_transit_moorti`, but as a
`source_table=` provenance literal on a `PrimitiveRow` — no SQL, no privilege required. It is
listed here so the next reader does not re-derive it as a fourth read.

Granted: **SELECT only, on exactly those three tables.** Nothing more.

---

## 3. What was deliberately NOT granted, and why

### 3.1 `phala_rectification` — held on Strategy §6.2 (the substantive decision)

`ka_kshetra` does read it today, unguarded:
`services/ka_kshetra/uncertainty.py:185-196` (`SELECT offset_minutes, lel_fit_score,
lagna_stable FROM phala_rectification WHERE chart_id = %s`), called unconditionally from
`services/ka_kshetra/stage3_clocks.py:1012`. A grant would make it succeed. It is held anyway:

* **It is L3 reading L4 — a dependency pointing upward.**
* **`MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §6.2:** *"Rectification and L5 weight inputs
  require separately admitted, purpose-compatible immutable artifacts. An earlier timestamp does
  not make an event-derived rectification posterior admissible under the event-free prospective
  contract."* A **live table read** of a mutable, delete-then-insert L4 table
  (`writers/ph_rectification/__init__.py:291,:336`) is not a separately admitted immutable
  artifact, and no grant can make it one.
* **The correct disposition is a design change, not a privilege change:** replace the live read
  with an admitted immutable artifact. That belongs in the Kshetra brief. Full argument, the
  measured contribution, and the recommended interim behaviour are in
  `W0_REGISTER_AMENDMENT_001_KSHETRA_PHALA_RECTIFICATION.md` §9.
* **It costs nothing measured.** Re-verified at the authority (§4): 0 of 370 rows have
  `lel_fit_score > 0`, so the filter at `uncertainty.py:176-178` never admits anything,
  `compute_sigma_t_days` always returns the instrumental default, and 511,320 of 511,320
  `kala_field_boundaries` rows carry `sigma_t_source = 'default_120s_assumption'`.

The hold is **enforced, not merely stated**: 1073's verification block raises if the privilege is
present (proven by mutation, §5.3).

### 3.2 Write privileges on the three granted tables

`bg_cohort` (`writers/bg_cohort.py:470`) and `bg_transit_rules` (`writers/bg_transit_rules.py:11`)
**are** orchestrator-registered writers, both `is_active = true`, whose DML
(`bg_cohort.py:588,:593,:642,:673`; `brahmagyan/l0_transit.py:1023`) would need INSERT/UPDATE/
DELETE if `data_plane_builder` ever dispatches them. That is a **real, separate L0
reference-corpus seed gap**, recorded here for the L0 grants owner rather than silently widened:
L3 reads these corpora, it does not reseed them, and a builder able to rewrite a cited 27-row
Phaladeepika reference table or a 10,000-chart synthetic reference population has a far larger
blast radius than one able to read them.

### 3.3 `kala_gochara_windows_archive_20260805` — investigated; a separate item

**The report is CONFIRMED.** `has_table_privilege('data_plane_builder',
'public.kala_gochara_windows_archive_20260805', 'SELECT')` → **f**. A restore drill executed as
`data_plane_builder` cannot read its own recovery source (35,620 rows, 2 charts).

**It does not belong in this migration.** Justification, three independent reasons:

1. **No live caller.** `grep -rn 'kala_gochara_windows_archive_20260805' platform/ platform-mcp/
   pipeline/` returns **zero hits outside `*/migrations/`** (only 646, 670, 674 and 1073's own
   comment); every other mention is governance markdown under `00_ARCHITECTURE/`. Both tables
   1073 does grant are on the live build path with confirmed failing assets behind them. Mixing a
   no-caller table into a build-unblocking migration muddies what the migration is for.
2. **The open question is a design decision, not a missing grant.**
   `KALA_ELEVATION_READINESS_PACKAGE_v1_0.md` A-3 states it as a binary: *"Does the R6 restore
   drill run as `data_plane_builder` or as a privileged operator?… Either grant SELECT … or
   declare the drill an operator-role activity and say so in the gate."* Landing the grant here
   answers that question **silently, as a side effect of an unrelated migration**, and the
   question stops being asked. That is the §N.8 failure mode in reverse — a capability cemented
   so nothing has to decide.
3. **Blast-radius asymmetry.** The three granted tables are L0 reference corpora the build reads
   every run. This is the **recovery source** for protected generation-1 Gochara capital. Giving
   the identity that performs destructive rebuilds standing read access to the backup it would
   restore from is a decision with an audit story, not plumbing.

**Recommended disposition:** the R6 gate owner declares the drill's identity. If the answer is
"operator", nothing is needed and the gate says so. If it is "builder", it gets its own one-line
migration whose comment records *that ruling* as the reason.

### 3.4 Also not granted

No sequence grants (SELECT needs none, nothing here writes). No column-level UPDATE. No
ownership, RLS, trigger or table-shape change. No role membership — in particular
`data_plane_builder` is **not** added to `role_orchestrator`, which would hand it that role's
full DML on every table at once; the zero-membership topology is preserved deliberately.

---

## 4. Measured contribution of the held read (re-verified, one correction)

Reported by a parallel lane, re-measured here independently, read-only:

| claim | reported | measured | disposition |
|---|---|---|---|
| `phala_rectification` rows | 185 | **185 per chart**, 370 total across 2 charts | correct **per chart** (matches `ph_rectification`'s own `37*5 = 185` per chart, `writers/ph_rectification/__init__.py:13`); table-wide total is 370 |
| rows with `lel_fit_score > 0` | 0 | **0** (95 non-NULL, none `> 0`) | **confirmed exactly** |
| boundary rows on `default_120s_assumption` | 261,998 | **261,998** for canonical chart `482012f1-…`; **511,320 of 511,320 (100%)** table-wide, no other value present | correct **for the canonical chart**; table-wide it is stronger than reported |

Consequence, stated exactly: the upward read's measured contribution to L3's published output is
**zero** — confirmed from both ends. It is nonetheless **not dead code** (it executes every
stage-3 run and hard-fails the build when denied) and **not permanently inert** (one positive
`lel_fit_score` flips it on silently). Details and queries: the register amendment §7.

---

## 5. Proof — migration 1073

Disposable PostgreSQL **15.17** on port 59540, dir `/tmp/kg2`, socket `/tmp` — same major version
as production (**15.18**). The fixture reproduces the production **role topology and table
identity**, which is what a GRANT migration depends on: database `amjis`, role `amjis_app` (owner
of all five tables, carrying production's `idle=600s / statement=1800s` rolconfig), role
`data_plane_builder` (LOGIN, **zero memberships, no rolconfig**), and the five tables created
with their real production column lists pulled from `information_schema`. It does not reproduce
row data; no proof here depends on row data. No `pg_dump` was taken, so the table-scoped
schema-only trigger-function hazard does not arise.

### 5.1 Before — the check FAILS

```
public.bg_transit_moorti SELECT=false
public.bg_synthetic_cohort SELECT=false
public.bg_synthetic_cohort_md SELECT=false
public.phala_rectification SELECT=false
-- fail-closed gate:
ERROR:  GATE FAIL — builder still lacks SELECT on: bg_transit_moorti bg_synthetic_cohort bg_synthetic_cohort_md
-- the two real build statements, as data_plane_builder:
ERROR:  permission denied for table bg_transit_moorti
ERROR:  permission denied for table bg_synthetic_cohort
```

### 5.2 Apply, after, re-apply — the check PASSES, twice

```
=== APPLY 1073 (as amjis_app, the real runner identity) ===
BEGIN GRANT GRANT GRANT DO COMMIT | exit=0

=== AFTER ===
public.bg_transit_moorti SELECT=true
public.bg_synthetic_cohort SELECT=true
public.bg_synthetic_cohort_md SELECT=true
public.phala_rectification SELECT=false      <-- the hold, intact
NOTICE:  GATE PASS — builder has SELECT on all three
-- real build statements, as data_plane_builder:  0 / 0   (succeed; empty fixture)
-- the held table, as data_plane_builder:  ERROR: permission denied for table phala_rectification

=== RE-APPLY (idempotency) ===
BEGIN GRANT GRANT GRANT DO COMMIT | exit=0
public.bg_transit_moorti SELECT=true … public.phala_rectification SELECT=false   (unchanged)
```

### 5.3 The §6.2 hold is a real detector, not a comment

Mutation test — grant the held table out-of-band, then re-run 1073:

```
GRANT SELECT ON TABLE public.phala_rectification TO data_plane_builder;
\i 1073_data_plane_builder_l3_reference_read_grants.sql
ERROR:  migration 1073: data_plane_builder has SELECT on phala_rectification, which Strategy
        §6.2 holds (L3 reading L4 live; rectification inputs require separately admitted,
        purpose-compatible immutable artifacts). Resolve the design change in the Kshetra
        brief before granting.
-- transaction rolled back; revoke and re-run:
REVOKE … ; \i 1073…  ->  COMMIT, exit=0
```

The assertion can genuinely read false, and does. It is ordering-safe: no migration numbered
below 1073 grants that privilege, so a fresh-database rebuild cannot trip it, and `migrate.ts`
does not re-run applied migrations. A future migration that legitimately grants it (after the
design change) runs *after* 1073 and is unaffected.

---

## 6. Proof — migration 1074, and its DBA precondition

### 6.1 The measured before-state

```sql
SELECT rolname, rolconfig FROM pg_roles WHERE rolname IN ('data_plane_builder','amjis_app');
  amjis_app           -> {idle_in_transaction_session_timeout=600s, statement_timeout=1800s}
  data_plane_builder  -> NULL          -- no rolconfig at all
```

Cluster `boot_val` for both GUCs is `0` (disabled) on PG 15.18, and the builder holds no
memberships, so **a new builder connection that sets nothing runs with both killers off.**
Confirmed on the fixture: `new builder conn: idle=0 stmt=0`.

### 6.2 A real blocker found while proving it — `amjis_app` cannot run `ALTER ROLE`

Measured live:

| rolname | rolsuper | rolcreaterole |
|---|---|---|
| `amjis_app` (migration runner) | f | **f** |
| `data_plane_builder` | f | f |
| `postgres` | f | t |
| `cloudsqlsuperuser` | f | t |

`ALTER ROLE <other> SET …` requires SUPERUSER or CREATEROLE. Reproduced all three cases on the
disposable:

```
amjis_app -> ALTER ROLE data_plane_builder SET statement_timeout='86400s';   ERROR: permission denied
amjis_app -> ALTER ROLE amjis_app          SET lock_timeout='1s';            ALTER ROLE   (a role may always alter ITSELF —
                                                                              this is why migration 241 worked)
GRANT data_plane_builder TO amjis_app WITH ADMIN OPTION; then the ALTER:     ERROR: permission denied   (PG15: membership does not confer it)
a CREATEROLE role -> the same ALTER:                                         ALTER ROLE
```

So **migration 1074 cannot be applied by the ordinary runner.** Rather than land green having
done nothing, it declares the requirement and fails loudly with an actionable code — the same
DBA-preflight shape migrations 1035/1036 already use (`E1035_PREFLIGHT_EXTENSION`):

```
$ psql -U amjis_app -f 1074_…sql
ERROR:  E1074_PREFLIGHT_ROLE_ADMIN: current_user=amjis_app has neither SUPERUSER nor CREATEROLE,
        so it cannot ALTER ROLE data_plane_builder (PG15: role membership, even WITH ADMIN
        OPTION, does not confer this). A privileged role must first run either
        "ALTER ROLE amjis_app CREATEROLE;" or, preferred, the two ALTER ROLE
        data_plane_builder SET statements this migration contains. See the PRIVILEGE
        PRECONDITION header of migration 1074.
```

**Action required before the deploy that carries 1074** — a role with CREATEROLE (`postgres` or
`cloudsqlsuperuser`) runs ONE of:

```sql
-- preferred: apply the two statements directly, then re-run the deploy so 1074 verifies and records
ALTER ROLE data_plane_builder SET idle_in_transaction_session_timeout = '1800s';
ALTER ROLE data_plane_builder SET statement_timeout = '86400s';
-- or: widen the runner (needs a native ruling; larger blast radius)
ALTER ROLE amjis_app CREATEROLE;
```

Doing it by hand and *skipping* the migration is not an option — then nothing records that it
happened. Either path leaves 1074's verification block as the thing that decides whether it may
be called applied.

### 6.3 The crux — why the two GUCs need different values

They measure different things, and the orchestrator's execution shape puts its worst case
squarely in one and nowhere near the other:

* **`idle_in_transaction_session_timeout`** bounds time in an **open transaction with no
  statement running**. A long CPU-bound Python substep is exactly this: the last statement has
  returned, the transaction is open, and the server sees an idle session while Python computes.
  `pipeline/orchestrator/db.py:46-70` documents "legitimately slow ayanamsha substeps (up to ~20
  min of pure CPU with no DB traffic)". That is a **1200-second idle gap, not a 1200-second
  statement.** This is the GUC that must clear it.
* **`statement_timeout`** bounds a **single statement's execution**. Python CPU time is not
  counted — the statement already finished. It never sees the 20-minute gap at all. What it must
  clear is the longest single SQL statement a sanctioned build may legitimately issue.

Proven on the disposable, role-level settings, a new connection per cell:

| | ACTIVE 5 s statement | 5 s client-side idle gap inside a txn |
|---|---|---|
| `idle_in_txn = 2s` | **SURVIVES** (`cell1 active statement finished`) | **KILLED** — `FATAL: terminating connection due to idle-in-transaction timeout` |
| `statement_timeout = 2s` | **KILLED** — `ERROR: canceling statement due to statement timeout` | **SURVIVES** (`cell4 second stmt after 5s idle`) |

Getting this backwards is how a build dies: a 600 s `statement_timeout` would not have protected
the 2026-09-11 run, and a 600 s **idle** bound is what killed it.

### 6.4 The failure modes, and the values chosen against them

**Failure mode A — the bound that kills a legitimate build.** Verified at the authority:

```
asset_throughput: ka_kshetra / 482012f1-710e-4a25-994a-93821f5871aa
  state      = 'error'
  last_error = 'worker_crash: OperationalError: the connection is lost'
  last_built_at = 2026-09-11 03:31:31.774943+00
```

2026-09-11 is a week **before** the identity cutover (migrations 1035/1036, 2026-09-18), so that
run authenticated as `amjis_app`, whose `idle_in_transaction_session_timeout = 600s`. A 1200 s
pure-CPU substep against a 600 s idle killer is a 2× overrun; the crash is the expected outcome.
**Copying `amjis_app`'s values would re-import that bug.**

Scaled 1:200 on the disposable — identical workload, only the bound changes:

```
real:  1200s CPU gap  |  amjis_app idle=600s  |  chosen idle=1800s
×1/200:   6s gap      |          3s           |          9s

idle=3s  (models 600s),  6s gap -> FATAL: terminating connection due to idle-in-transaction timeout
idle=9s  (models 1800s), 6s gap -> BEGIN / substep stmt 1 / substep stmt 2 AFTER 6s CPU gap / COMMIT
```

**Failure mode B — the bound that never fires.** Today both GUCs are `0` on this role: a wedged
connection or a runaway statement on any path that sets nothing runs **forever**.

**The values:**

| GUC | value | justified against |
|---|---|---|
| `idle_in_transaction_session_timeout` | **1800s (30 min)** | **Floor:** must exceed the documented ~20 min (1200 s) pure-CPU substep (`db.py:46-70`); 600 s does not — that is failure mode A, excluded by construction. 1800 s clears it with 1.5× headroom. **Ceiling:** finite, so a wedged connection auto-recovers instead of needing manual `pg_terminate_backend` (the S7459 finding `db.py:8-10` records against the prior `= 0`). **Choice of exactly 1800:** it is the value the orchestrator already sets for itself (`db.py:62`, `:75`; likewise `run_ka_sangam_prod.py:49`, `run_ph_pratikara_prod.py:48`), so a connection whose SET is stripped or never issued degrades to the *same* bound the orchestrator intended, not to unbounded. No build behaviour changes; the floor stops being absent. |
| `statement_timeout` | **86400s (24 h)** | **Floor:** never tighter than the largest budget the system sanctions. `asset_registry.writer_timeout_seconds` for `ka_kshetra` is **86,400** — the maximum across all 129 assets carrying a value (verified live) — and it is read by a **live detector** at `pipeline/orchestrator/runner.py:741`, which builds `timeouts_of` from that column for the per-asset watchdog. A tighter server-side bound would let the server kill a build the registry and the watchdog both authorize: failure mode A again. **Headroom:** the real measured worst case is `ka_kshetra` ~7.5 h — and that is the whole multi-statement asset, so the longest *single* statement is far smaller again. **It still fires:** the current value is 0 (forever); this makes it at most one day. It is deliberately the **outer** backstop — looser than the per-asset watchdog and than `lock_timeout='300s'` (`db.py:79`) — the last line, not the first. |

### 6.5 Honest scope — what 1074 does NOT bound

`pipeline/orchestrator/db.py:75-76` issues `SET idle_in_transaction_session_timeout = 1800000`
and `SET statement_timeout = 0` as **real statements** on every connection from `connect()`, and
`runner.py`'s `worker()` (`:750`) gives every asset a dedicated `connect()` connection. A
session-level SET beats a role default. **So for an orchestrator build session that reaches those
SETs, 1074 changes nothing** — the idle bound is already the same 1800 s and `statement_timeout`
is deliberately 0 there. It must not be claimed that this bounds those sessions.

What it genuinely covers, all verified in source:

* **The pre-SET window.** `db.py:62-76` states in-file that the `options=` startup parameter is
  not guaranteed to survive a pooler ("a local Cloud SQL Auth Proxy — or any intermediate pooler
  — may not forward arbitrary libpq startup options"). Between connect and the explicit SETs the
  role default is the only bound in force.
* **Paths that set only SOME GUCs.** `run_ka_sangam_prod.py:49` and `run_ph_pratikara_prod.py:48`
  are production build runners on bare `psycopg.connect()` that set
  `idle_in_transaction_session_timeout` and **not** `statement_timeout` (they only read it, for
  the smoke-log, at `:54`/`:53`). Those sessions are unbounded on statements today.
* **Paths that set NEITHER:** `run_bo_samskara_parallel.py:86`,
  `backfill_missing_signal_embeddings.py:37,:68,:119`, `pipeline/brahma_pipeline.py:52`.
* **psql / ad-hoc / cron** sessions as `data_plane_builder`, and any future runner that forgets
  the factory — the exact recurrence class MR-39 already had to fix once (`db.py:10-18`).

Deliberately not set: **`lock_timeout`** (`connect()` sets '300s' per session with its own
rationale; a *role*-level 300 s would also hit migration/maintenance sessions under this identity
where a legitimate lock wait can exceed 5 minutes, and lock-wait hangs are not the failure mode
this item names); **`transaction_timeout`** (PG17+; production is 15.18); **any change to
`amjis_app`**, whose 600 s/1800 s stay as they are.

### 6.6 Before / after / re-apply

```
=== BEFORE (true production state) ===
rolconfig: (NULL)
new builder conn: idle=0 stmt=0
ERROR:  GATE FAIL — data_plane_builder has NO rolconfig (unbounded)

=== APPLY #1 (as a CREATEROLE role) ===
NOTICE:  migration 1074 applied: data_plane_builder idle_in_txn=1800s statement_timeout=86400s
COMMIT | exit=0

=== AFTER ===
rolconfig: idle_in_transaction_session_timeout=1800s | statement_timeout=86400s
new builder conn: idle=30min stmt=1d          <-- takes effect on a NEW connection
NOTICE:  GATE PASS — idle=1800s statement=86400s

=== APPLY #2 (re-apply / idempotency) ===
NOTICE:  migration 1074 applied: … COMMIT | exit=0
rolconfig: idle_in_transaction_session_timeout=1800s | statement_timeout=86400s   (unchanged)
```

### 6.7 The detector fires, and does not kill legitimate work

```
-- the kill is real (role-level default, new connection):
statement_timeout=2s, SELECT pg_sleep(5)   ->  ERROR: canceling statement due to statement timeout
idle_in_txn=2s,       5s idle gap in txn   ->  FATAL: terminating connection due to idle-in-transaction timeout

-- at the CHOSEN values, legitimate work is untouched:
idle=30min stmt=1d, CPU-bound ACTIVE aggregate over 8,000,000 rows -> 8000000|15084946079.32, 1.39 s, completes
idle=30min stmt=1d, 6 s idle-in-transaction gap                    -> stmt 1 / stmt 2 after 6s idle / COMMIT
```

### 6.8 Mutation matrix — every check in 1074 is reachable and fires

```
M_noop      (ALTER ROLE statements neutered)  -> ERROR: migration 1074 did not take effect: data_plane_builder still has no rolconfig
M_idle600   (idle set to amjis_app's 600s)    -> ERROR: idle_in_transaction_session_timeout=600s does not clear the documented ~20 min
                                                        (1200s) pure-CPU substep …; 600s is the 2026-09-11 ka_kshetra worker_crash failure mode
M_idlezero  (idle set to 0)                   -> ERROR: … does not clear the documented ~20 min (1200s) pure-CPU substep …
M_stmt1800  (statement set to 1800s)          -> ERROR: statement_timeout=1800s is tighter than the largest sanctioned writer budget
                                                        (asset_registry.writer_timeout_seconds max = 86400s, read at runner.py:741)
M_stmtzero  (statement set to 0)              -> ERROR: statement_timeout=0 is tighter than the largest sanctioned writer budget …
real migration                                -> NOTICE: applied … COMMIT, exit=0   (and again on re-apply)
```

**A §N.8 defect found in this session's own work and fixed.** The first draft of 1074 asserted
`idle = '1800s'` exactly *and then* that it cleared the 1200 s floor. The mutation run showed the
floor check could never be reached — the equality check caught everything first. That is an
unearned signal: a check with no code path that could make it read false. It was replaced by
invariant checks (presence + floor + budget), which are reachable in both directions, as the
matrix above shows. A third "is it 0?" check was then also removed for the same reason: `'0'`
already fails the floor and budget comparisons, so it too would have been dead.

---

## 7. Live-path test — does a live caller reach each gap today?

| gap | live caller? | call chain |
|---|---|---|
| `bg_transit_moorti` | **YES** | Cloud Run `brahma-build-pipeline-job` (as `data_plane_builder` since the 2026-09-18 cutover) → `pipeline/orchestrator/runner.py` `execute_run` → `worker()` `:750` → `db.py connect()` `:52` → `run_asset` → `@register('ka_moorti_nirnaya')` (`writers/ka_moorti_nirnaya.py:23`) → `KaMoortiNirnayaWriter.run()` (`services/ka_moorti_nirnaya/writer.py:180`) → `_fetch_moorti_table()` `:195` → `cur.execute(_FETCH_MOORTI_TABLE_SQL)` `:169`. Registry `is_active = true`; `asset_throughput` `lit` on both charts (last built 2026-09-07, pre-cutover as `amjis_app`). Audit verdict: **CONFIRMED HARD FAIL** under the new identity — no try/except, LIGHT writer, no substep boundary. A second, non-builder caller exists on the serving side (`platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_transit_moorti.ts:68`), which runs as the web/serve role and is unaffected. |
| `bg_synthetic_cohort` / `_md` | **YES** | same job → `@register('ka_kshetra')` → `services/ka_kshetra/writer.py:108` imports `cohort_client` → stage-6 `writer.py:1755` `cohort_client.cohort_base_rate(...)` → `cohort_client.py:317,:322,:338,:346,:365`; plus the corpus pin at `writer.py:2304`. Registry `is_active = true`; `asset_throughput` `error` on the canonical chart (§6.4). The stage-6 path has a `try/except` (`writer.py:1754-1770`) but **no `SAVEPOINT`**, so the caught privilege error still poisons the ambient transaction and the *next* statement fails with an unrelated-looking error. That savepoint gap is a real code fix, **independent of this grant and not fixed here.** |
| `phala_rectification` | **YES** — reachable, and deliberately left blocked | `stage3_clocks.py:1012` → `uncertainty.py:185-196`, unconditional, unguarded. This is why the hold is a decision rather than a shrug: the read is live, it is the current cause of an `ka_kshetra` stage-3 hard failure, and the right fix is to remove it (register amendment §9), not to permit it. |
| `kala_gochara_windows_archive_20260805` | **NO** — *no live caller found within scope:* `grep -rn 'kala_gochara_windows_archive_20260805'` over `platform/`, `platform-mcp/`, `pipeline/` (all file types, `node_modules` excluded) → 0 hits outside `*/migrations/` (646, 670, 674, and 1073's own comment). Every other mention is governance markdown under `00_ARCHITECTURE/`. | — |

---

## 8. Disposable Postgres — teardown proof

Instance: PostgreSQL 15.17, port **59540**, data dir **/tmp/kg2**, socket dir `/tmp` (short path).
No other agent's port or directory was touched. No `pg_dump` was taken. Teardown proof is
recorded in §9.

---

## 9. What remains open

1. **Production application of both migrations is NOT verified.** It happens at deploy via
   `platform/scripts/migrate.ts`. Everything above is proven on a disposable PG 15.17 against a
   fixture reproducing the measured production role topology.
2. **1074 has a hard DBA precondition (§6.2).** Without it, the deploy carrying 1074 fails with
   `E1074_PREFLIGHT_ROLE_ADMIN`. 1073 is unaffected — `amjis_app` owns the tables and can GRANT —
   so a deploy carrying both lands the grants and fails on the timeout, visibly.
3. **`phala_rectification` remains a build blocker for `ka_kshetra` stage-3** by deliberate
   choice. It is not closed by 1073 and cannot be closed by a grant. Owner: Kshetra brief /
   design change (register amendment §9).
4. **The `ka_kshetra` cohort-path `SAVEPOINT` gap** (`writer.py:1754-1770`) is untouched. The
   grant removes the privilege error that currently poisons the transaction, but the missing
   savepoint remains a latent defect for the next error that path catches.
5. **L0 seed write privileges** for `bg_cohort` / `bg_transit_rules` under `data_plane_builder`
   (§3.2) — real, separate, owner: L0 grants.
6. **The archive table / R6 restore-drill identity question** (§3.3) — owner: R6 gate.
7. **The W0 register amendment is filed, not folded in.** Owner: the W0 FIELD_CONTRACT_REGISTER
   campaign.
8. **Not verified by this session:** whether the deploy's `DATABASE_URL` authenticates as
   `amjis_app` — 1070's header asserts it and this session's read-only production access does,
   but the deploy's own credential was not inspected (and must not be). If the deploy runs as a
   CREATEROLE role, item 2 dissolves and 1074 applies unaided.

---

**Companion:** `W0_REGISTER_AMENDMENT_001_KSHETRA_PHALA_RECTIFICATION.md` (same directory).
