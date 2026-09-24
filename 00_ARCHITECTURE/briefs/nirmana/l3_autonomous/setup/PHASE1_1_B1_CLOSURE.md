---
artifact: PHASE1_1_B1_CLOSURE
canonical_id: PHASE1_1_B1_CLOSURE
version: "1.0"
status: CURRENT
date: 2026-09-22
phase: Kāla (L3) pre-elevation, Phase 1.1 — CLOSE B1
strategy_position: W0 "make the programme safe"
branch: l3/kala-p1-1-b1-clear-guard
closes: KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md §1 C4
production_state: MIGRATIONS AUTHORED AND PROVEN ON A DISPOSABLE POSTGRES; NOT YET APPLIED TO PRODUCTION
---

# Phase 1.1 / B1 — closing the live deletion path into the protected Gochara corpus

**What this closes.** A live, ordinary-user-reachable path by which the cockpit Clear
route deleted `kala_gochara_windows` rows at `generation='v1'` — the retired
`ka_gochara_sweep` snapshot that `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §4 declares
"retired, snapshot-protected and **never rebuildable**", and that has no registered writer
to regenerate it.

**What it does not claim.** Production is read-only to this session. Both migrations are
authored, applied and re-applied on a disposable Postgres with their fail-closed blocks
independently mutation-proved. **Production application happens at deploy and is therefore
NOT YET VERIFIED.** That is an honest pending, not a false "applied". The route-level
change ships with the same deploy.

---

## 1. The hazard, as measured

All figures measured read-only against production on **2026-09-22**, immediately before
authoring.

| Fact | Measured value |
|---|---|
| `kala_gochara_windows` `generation='v1'` | **38,287 rows across 3 charts** — `1c826d5a…` 19,323 · `482012f1…` 16,297 · `cb73cd3d…` 2,667 |
| `kala_gochara_windows` `generation='3.0'` | **1,830 rows across 2 charts** — `1c826d5a…` 916 · `482012f1…` 914 |
| `build_protected_assets` | **0 rows**, every chart |
| non-internal triggers on ANY `kala_*` table | **0** (positive control: **130** non-internal triggers exist elsewhere in `public`, so this is a real zero, not a query that finds nothing anywhere) |
| `asset_registry` rows with `is_active IS NOT TRUE` | **exactly 1** — `ka_gochara_sweep`. 0 NULL / 1 false / 128 true |
| assets whose `depends_on` names `ka_gochara_sweep` | **NONE** |

Why the v1 rows are irreplaceable, in the codebase's own words — migration 588's STANDING
CAUTION: *"ka_gochara_sweep's 38,287 generation='v1' rows have NO registered writer. Its
`@register` was removed at retirement (`writers/ka_gochara_sweep.py`), so the build system
CANNOT regenerate them. The snapshot above is their only recovery path."*

The database protection that once stood over them — migration 540's row/TRUNCATE triggers
and migration 566's gen-3.0 trigger — was **dropped by migration 588 on 2026-08-23**, and
`build_protected_assets` emptied in the same migration. Between that date and this change
there was no database-level enforcement of the standing ruling at all.

---

## 2. The live path, with line numbers

A **non-super-admin chart OWNER** reaches it. Chain:

1. `platform/src/app/api/cockpit/clear/route.ts:93` — `allowedScopes = ['per_chart']` for a
   non-super-admin. `authorizeChartAccess` at `:84-91` requires `permission === 'all'`, i.e.
   the chart's owner (or super_admin) — no higher bar.
2. `route.ts:113-118` — loads `asset_registry` with **no `is_active` filter**.
3. `platform/src/lib/cockpit/clearScopeFilter.ts:29-30` — the `layer` branch filters on
   `layer` and `scope` only. `ka_gochara_sweep` is `layer='kala'`, `scope='per_chart'`,
   `is_active=false` → **in scope**.
4. `clear/execute/route.ts:160-183` — clear-spec resolution order:
   - `:160` `EXPLICIT_CLEAR_OPS` — `ka_gochara_sweep` has **no entry** → skipped;
   - `:167-172` `count_sql` present and auto-transformable → **THIS BRANCH FIRES**;
   - `:175-183` `target_table` fallback → **never reached for this asset**.
5. `assetClearSpec.ts:29-46` `deriveDeleteSqlFromCountSql` transforms the live registry
   value
   `SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'`
   into
   **`DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='v1'`**,
   executed at `execute/route.ts:205`.

**Adjudication of the parallel lane's report: the parallel lane is CORRECT.** The live
vector is `ka_gochara_sweep`'s own `count_sql`, not `target_table`. `target_table` is never
consulted for this asset, because `count_sql` is non-null and transformable and wins at
`:168`. Correcting a `target_table` would not have closed anything. This is pinned in code
by `platform/src/lib/cockpit/__tests__/assetClearSpec.test.ts`'s new "B1 — the
ka_gochara_sweep live deletion vector" block, which asserts the exact derived SQL.

**Live caller:** yes. `CockpitShell.tsx`'s Clear control issues `scope: 'global'` and
layer-scoped clears for every caller the Nirmāṇa page guard admits with `canBuild === true`
— which is plain chart owners, not only super_admins (documented in `route.authz.test.ts`'s
own header). Scope searched: `platform/src/app/api/cockpit/clear/**`,
`platform/src/lib/cockpit/**`, `platform/src/lib/build/plan.ts`, and every caller of
`filterScopeAssets` / `deriveDeleteSqlFromCountSql` in `platform/src`.

**Also corrected — a stale comment asserting protection that no longer existed.** Both
Clear routes carried comments citing "a DB-level trigger guard (migration 540) as
defense-in-depth". That claim had been **false since 2026-08-23** (588). Verified against
both the migration file and the live catalog (0 `kala_*` triggers). Both comments now state
the real state and point at migration 1071.

---

## 3. Part A — the `ka_gochara.target_table` mismatch, and the W0 hold

### 3.1 What the hold was, mechanically

`CURRENT_STATE_AND_DISPOSITION §4.1` line 133 records `ka_gochara` as *"after resonance;
seed target mismatch held."* This is **not reported here as a discovery.** The hold was not
doubt about the correct value; it was a revert mechanism, which this session established at
the code before touching anything:

`platform/scripts/seed/asset_registry_seed.ts`'s `ASSET_REGISTRY_UPSERT_SQL`
(`ON CONFLICT (asset_id) DO UPDATE SET …`) treats the three columns differently:

| column | on conflict | owner |
|---|---|---|
| `count_sql` | `count_sql = asset_registry.count_sql` | migration-governed — a re-seed cannot revert it |
| `depends_on` | `depends_on = asset_registry.depends_on` | migration-governed |
| `target_floor`, `expected_volume_*` | `= asset_registry.<col>` | migration-governed |
| **`target_table`** | **`= EXCLUDED.target_table`** | **seed-owned** — the file's own comment: *"target_table is left seed-owned deliberately -- it is a structural declaration, not a measured quantity"* |

So a DB-only migration correcting `target_table` **would be silently reverted by the next
`runSeed()`**. That is the hold, exactly.

### 3.2 What the correct value is, on the writer's own authority

`platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara.py`:
- `:120` — `TABLE = "kala_gochara_windows_v2"`;
- `:336` — `DELETE FROM {TABLE} WHERE chart_id = %s AND event_class = %s AND generation = %s` with `GENERATION_V2`;
- `:362` — INSERT carrying `generation = GENERATION_V2`;
- module docstring, recording a **native ruling** ("native ruling point 2"): *"this writer's
  only DELETE/SELECT/INSERT target is `kala_gochara_windows_v2` -- there is no code path,
  error branch, or override that ever names `kala_gochara_windows`."*

W0 census #4 agrees: `ka_gochara` → `kala_gochara_windows_v2` (generation 2) +
`kala_gochara_v2_build_state`. Production's live `count_sql` already agrees
(`… FROM kala_gochara_windows_v2 … generation='2.0'`). Only `target_table` and the seed
literal had not caught up.

### 3.3 Decision: **(a) correct now, both halves in one change**

Chosen over leaving it held, because:

1. **The revert mechanism is disarmed by fixing both halves together**, which is the hold's
   own stated release condition. Migration 1072 corrects the DB; the seed literal is
   corrected in the same commit; and
   `platform/scripts/__tests__/gochara_seed_target_table_parity.test.ts` is the standing
   detector — it reads the writer's `TABLE = "…"` constant **out of the Python source** and
   refuses to let the two diverge again. A constant can drift from its source; a reference
   cannot (§N.7 item 3).
2. **Collision risk is currently nil, and was checked, not assumed.** All 16 open PRs were
   enumerated and their file lists inspected: **no open PR touches
   `platform/scripts/seed/asset_registry_seed.ts`, `platform/src/app/api/cockpit/clear/**`,
   or `clearScopeFilter.ts`.** If that changes before merge, the collision is a one-line
   literal in a single object — trivially rebasable.
3. **The stale seed `count_sql` literal was a loaded gun.** The seed said
   `SELECT COUNT(*) FROM kala_gochara_windows … generation='3.0'`. It is harmless on an
   existing row (migration-governed) — but a **brand-new** row takes the literal verbatim,
   and `deriveDeleteSqlFromCountSql` would then hand the Clear path
   `DELETE FROM kala_gochara_windows WHERE chart_id=$1 AND generation='3.0'` — the
   century materialiser's protected production rows. Harmless only by accident is not a
   reason to leave it standing. Corrected in the same edit.

**What released the hold:** the mechanism was identified (`target_table = EXCLUDED.target_table`),
both halves are fixed together, a cross-source parity test now prevents re-divergence, and
the cross-campaign collision the hold feared was measured to be absent today.

**Honest scoping:** Part A is **registry truth**, not the hole B1 closes. `target_table` is
never reached for `ka_gochara` on the Clear path. It matters because it is the row a future
clear-spec, digest, freshness or census reader consumes, and because it declares the
protected corpus as an asset's output in direct contradiction of a standing native ruling.

### 3.4 Proof

**BEFORE** (`platform/scripts/__tests__/gochara_seed_target_table_parity.test.ts`, on
unmodified seed):

```
× the seed row target_table equals the writer TABLE constant
× the seed row never declares the protected v1 corpus table as its output
× the seed count_sql also reads the writer's own relation, not the protected one
AssertionError: expected 'kala_gochara_windows' to be 'kala_gochara_windows_v2'
 Test Files  1 failed (1)
      Tests  3 failed | 2 passed (5)
```

**AFTER** (whole `scripts/__tests__` directory, so `catalog_reconciliation` and
`asset_registry_seed_dag_parity` are re-proved too):

```
 Test Files  9 passed (9)
      Tests  118 passed (118)
```

---

## 4. Part B — the `is_active` filter on the Clear route

### 4.1 The fix

Two independent layers, so neither is load-bearing alone:

- **Query layer** — `clear/route.ts` and `clear/execute/route.ts` both now
  `SELECT … COALESCE(is_active, TRUE) AS is_active … WHERE COALESCE(is_active, TRUE)`.
  Re-derived **identically** in both routes: they compute `affectedAssetIds` independently
  and hash it, so a filter on only one side would either break the hash or — worse — hide
  the asset from the preview while the execute loop still deleted its rows.
- **Filter layer** — `clearScopeFilter.ts` gains `isClearable(r) => r.is_active !== false`,
  applied to all four branches (`global`, `layer`, `asset_set`, `asset`).

`COALESCE` because the column is nullable with `DEFAULT true`: production holds zero NULLs
today, and a future NULL must mean "active", not "silently unclearable". The TS filter
excludes only an **explicit** `false` so it can only narrow a set the route already
filtered.

This was a **convention violation, not a design choice**: every sibling cockpit route
already filters this column — `refresh/route.ts:49`, `status/route.ts:11`,
`runs/route.ts:243`, `stats/route.ts:257`. The BUILD path could not touch the retired asset
while the DELETE path could.

### 4.2 Proof

**BEFORE** (tests written first, against unmodified route/filter code):

```
 ❯ scope_filter.test.ts (13 tests | 4 failed)
 ❯ route.authz.test.ts  (17 tests | 10 failed)
   × (B1-a) preview: a RETIRED asset is not in scope for a layer Clear an owner can issue
   × (B1-c) preview: a DIRECT asset-scope Clear naming the retired asset resolves to nothing
   × (B1-d) execute: NO DELETE naming kala_gochara_windows is ever issued
   × (B1-f) the registry SELECT itself carries an is_active predicate — the query half
   …
 Test Files  2 failed | 1 passed (3)
      Tests  14 failed | 18 passed (32)
```

**AFTER**:

```
 Test Files  4 passed (4)
      Tests  52 passed (52)
```

Note on the extension: `route.authz.test.ts` is the suite whose fixture was literally
`target_table: 'kala_gochara_windows'`; it was extended, not duplicated. Its fixture now
carries the RETIRED row exactly as production does (`is_active: false`, real
generation-scoped `count_sql`). Its existing test (d) previously asserted
`affected_assets` **contained** `ka_gochara_sweep` — i.e. the suite asserted the hazard.
That assertion is inverted deliberately, with the reason recorded inline.

### 4.3 Disclosed behavioural consequence

An inactive asset is now also absent from `computeDownstreamClosure` and the label map.
That is correct — a retired asset is never rebuilt, so marking it "stale" would prompt a
rebuild that cannot happen — and it is measurably inert here: **no asset's `depends_on`
names `ka_gochara_sweep`**. Second consequence: a Clear no longer resets the sweep's
`asset_throughput` row. Those rows currently read `state='error'` for all three charts, and
`stats/route.ts` filters `is_active = true`, so they are not displayed. Cosmetic, recorded
rather than silently changed.

---

## 5. Part C — a real guard on the protected rows

### 5.1 Scope decision, with evidence

The kickoff's framing ("a generation-blind DELETE destroys both") is right about the
danger and under-specified about the remedy. What the guard must cover, and why exactly
that:

**COVERED — `generation='v1'` DELETE/UPDATE, unconditionally, for every chart.**
No legitimate writer exists (no `@register`), so the guard's false-positive rate is
structurally zero. Deliberately **not** keyed on a `build_protected_assets` row: migration
540's guard was, and was therefore **fail-OPEN** for any chart absent from the registry —
which is not hypothetical. Chart `cb73cd3d…` ("Kiran Shenoy") holds **2,667 v1 rows** and
was never seeded by 540 or 566. A corpus that cannot be rebuilt must fail closed by
default, including for charts created after this migration.

**COVERED — TRUNCATE, unconditionally.** Always generation-blind; a row trigger cannot see
it.

**NOT COVERED — a `generation='3.0'`-pinned DELETE/UPDATE.**
`ka_gochara_v3_century_materialize` is the live, legitimate writer of those rows and its
idempotent rebuild is literally
`DELETE FROM kala_gochara_windows WHERE … generation='3.0' …`
(`ka_gochara_v3_century_materialize.py:2257`; INSERT at `:540`). Blocking it is **Defect
D-02 — the exact reason migration 588 removed the protection**: *"The trigger could not
tell a legitimate write from a destructive one, and left that writer in a permanent
BUILD-PROTECTED error."* Migration 588's own closing instruction is the design followed
here: *"If protection is ever reinstated, key it on (table, generation) rather than
asset_id, so it cannot again block the writer it is meant to protect."*

Gen-3.0 rows are still protected from **generation-blind** destruction — the fence the W0
register names (fence 2: v1 and century v3 coexist; generation-blind mutation forbidden) —
because a statement with no `generation` predicate sweeps v1 rows too and the v1 rule
aborts the whole statement before any row is removed. **That transitive coverage rests on a
measured fact, not a structural one**: both charts holding gen-3.0 rows also hold v1 rows.
The migration says so in those words rather than claiming a protection it does not enforce.
TRUNCATE, the one generation-blind statement the row rule cannot see, is separately
refused.

### 5.2 Mechanism chosen: DB trigger **primary**, plus two route layers

| Layer | What it is | Why |
|---|---|---|
| **1. DB trigger (migration 1071)** | `BEFORE DELETE OR UPDATE FOR EACH ROW` + `BEFORE TRUNCATE FOR EACH STATEMENT` on `kala_gochara_windows`, keyed on `OLD.generation` | **Preferred, and the only one that cannot be bypassed by a future caller** — a manual `psql` session, a mis-scoped script, a writer bug, a route that has not been written yet. None of the route layers see those. |
| **2. Route `is_active` filter (Part B)** | query + scope filter | Stops the specific live vector before it reaches SQL, and gives the operator an honest preview rather than a DB error. |
| **3. `build_protected_assets` rows (migration 1072)** | data-driven re-population for `ka_gochara_sweep` only | Restores the route-level withholding that 588 emptied, and surfaces the asset in `preview.protected_assets` with its message rather than silently dropping it (§N.6 honest-empty discipline). |

Rows are re-established for `ka_gochara_sweep` **only** — never `ka_gochara`, which is the
row that caused D-02. This does not contradict 588's native instruction ("the Nirmāṇa
elevation campaign rebuilds every asset by design, so a guard that must be overridden on
every legitimate write is no longer wanted"): `ka_gochara_sweep` is retired and is *never*
built, so withholding it costs no build and blocks only deletion. **Flagged for the native
as a judgment call, not assumed.**

The INSERT is `SELECT DISTINCT chart_id … WHERE generation='v1'` rather than the two
hardcoded canonical UUIDs of 540/566 — that is what picks up `cb73cd3d…`.

Override GUC is deliberately the historical `app.allow_protected_sweep_rewrite`, so the
vocabulary in operator runbooks and in the existing
`build_protected_assets_sweep_guard.db.test.ts` is not stranded.

### 5.3 The `protected_generations` §N.8 instance — recorded, NOT closed

`build_protected_assets.protected_generations TEXT[]` exists (migration 556) and **neither
Clear route reads it** — both `SELECT asset_id` only. Route-level withholding is therefore
asset-level while the column's claim is generation-level: a detector measuring a coarser
claim than the one asserted. For `ka_gochara_sweep` the two coincide (every row it ever
wrote is `generation='v1'`), so nothing is currently mis-protected — but the gap is real.

**It is not closed here.** Making the routes generation-aware means rewriting clear-spec
resolution, which is a materially larger change than B1 and would risk the very path being
made safe. Migration 1071's trigger is the generation-precise detector at the layer that
matters. Recorded as open item **O-1** below, and stated in both route comments and in
migration 1072's header rather than left for someone to rediscover.

### 5.4 Proof

**BEFORE** — disposable Postgres, schema without migration 1071, the exact SQL the Clear
route derives:

```
--- non-internal triggers on the table (expect NONE) ---
 NONE — no guard
--- rows before ---   3.0 | 10   v1 | 100
--- the EXACT SQL the Clear route derives from ka_gochara_sweep.count_sql ---
DELETE 100
--- rows after: the protected snapshot is GONE ---   3.0=10
--- and a generation-blind TRUNCATE also succeeds ---
TRUNCATE TABLE
 0 rows remain
```

**AFTER** — same statements, migration 1071 applied:

```
--- 1. the exact Clear-route-derived v1 DELETE ---
ERROR:  BUILD-PROTECTED: kala_gochara_windows generation='v1' row(s) … DELETE is refused.
--- 2. generation-blind per-chart DELETE ---
ERROR:  BUILD-PROTECTED: … DELETE is refused.
--- 3. TRUNCATE ---
ERROR:  BUILD-PROTECTED: kala_gochara_windows cannot be TRUNCATEd. …
--- 4. v1 UPDATE ---
ERROR:  BUILD-PROTECTED: … UPDATE is refused.
--- 5. LEGITIMATE century-writer gen-3.0 DELETE (must SUCCEED) ---
DELETE 10
--- 6. INSERT is never gated ---
INSERT 0 1
--- rows after all of the above: v1 snapshot INTACT ---   v1 | 101
--- 7. explicit native override still works ---
BEGIN / SET / DELETE 101 / ROLLBACK
--- rows after the rolled-back override ---   v1 | 101
```

**Suite** — `platform/tests/integration/kala_gochara_windows_generation_guard.db.test.ts`
executes the REAL migration file against the disposable Postgres:
`Test Files 1 passed (1) · Tests 12 passed (12)`.

**Mutation proof that the suite is a detector, not decoration** — neuter the row rule in
the migration (`IF OLD.generation = 'v1'` → `IF FALSE`) and re-run the same suite:

```
× (a) the exact DELETE the Clear route derives from the retired sweep count_sql is REFUSED
× (b) a v1 DELETE is refused for a chart NO protection registry ever listed
× (c) a v1 UPDATE is refused too — not just DELETE
× (d) a GENERATION-BLIND per-chart DELETE is refused and removes NOTHING, gen-3.0 included
× (i) the override releases the guard for one transaction only
× (k) re-applying migration 1071 is a clean no-op — idempotency, against the real file
 Tests  6 failed | 6 passed (12)
```
File restored byte-identical; suite back to 12/12.

---

## 6. Migrations — apply, re-apply, and earned fail-closed blocks

Numbers **1071** and **1072**, authored at `platform/migrations/`. Both verified free in
**both** `platform/migrations/` and `platform/supabase/migrations/` (max in either = 1070),
which `platform/scripts/migrate.ts:832-835` reads as one numeric sequence. L3 Kāla reserved
range 1070–1119 (DP-SD-021).

Apply and re-apply against the disposable Postgres, with a fixture mirroring production's
three v1 charts (including the never-registered one) plus gen-3.0 rows:

```
############ APPLY #1 ############
--- 1071 ---  BEGIN … CREATE TRIGGER ×2 … DO … DO … COMMIT      1071 exit=0
--- 1072 ---  BEGIN / SET / UPDATE 1 / INSERT 0 3 / DO / COMMIT  1072 exit=0

############ APPLY #2 (idempotency) ############
--- 1071 ---  BEGIN … CREATE TRIGGER ×2 … DO … DO … COMMIT      1071 exit=0
--- 1072 ---  BEGIN / SET / UPDATE 0 / INSERT 0 0 / DO / COMMIT  1072 exit=0

############ RESULTING STATE ############
triggers=2
ka_gochara.target_table=kala_gochara_windows_v2
protected: ka_gochara_sweep 1c826d5a-… gens={v1}
protected: ka_gochara_sweep 482012f1-… gens={v1}
protected: ka_gochara_sweep cb73cd3d-… gens={v1}
```

**The fail-closed blocks are earned signals, proved by mutation** — each was shown to
genuinely read false:

```
M1: 1071 with the v1 rule neutered (triggers still install):
  ERROR: migration 1071 self-test FAILED: a generation='v1' UPDATE was permitted;
         the guard is installed but inert
M2: 1072 with PART 1 removed:
  ERROR: migration 1072 did not take effect: ka_gochara.target_table is
         kala_gochara_windows, expected kala_gochara_windows_v2
M3: 1072 with PART 2 removed:
  ERROR: migration 1072 did not take effect: 3 chart(s) hold generation=v1 rows but
         only 0 carry a ka_gochara_sweep protection row
```

Migration 1071 carries **two** verification blocks on purpose: a catalog check (are the
triggers and functions there?) and a **behavioural** check (does the guard actually
refuse?). An installed-but-inert trigger passes the first and fails the second — that is
§N.8 instance 3's exact shape, and M1 proves the second block catches it. When no v1 row
exists the behavioural block emits an explicit `NOTICE … NOT RUN (honest skip, not a pass)`
rather than reporting a check it never ran.

**A real defect was caught by this discipline during authoring:** 1072's first draft wrote
`'{v1}'` into a `text[]` column from an `INSERT … SELECT`, which Postgres refuses without
an explicit cast. Because the migration is transactional and fails loudly, the apply
aborted instead of half-applying. Fixed to `'{v1}'::text[]` and re-proved from a clean
fixture.

---

## 7. Full quality gate

```
npx tsc --noEmit                 → clean
npx eslint <all touched paths>   → clean
npx vitest run (whole platform)  → Test Files 1143 passed | 79 skipped (1222)
                                   Tests 12433 passed | 719 skipped | 2 todo (13154)
```

---

## 8. What was deliberately NOT done, and why

1. **No migration applied to production.** Read-only session. Deploy applies them; until a
   deploy is verified, the production state of both migrations is **PENDING**, stated as
   such (§N.8: no green without a detector that ran).
2. **Migration 566 not touched.** It is the origin of the century BUILD-PROTECTED guard and
   is not this task's to reopen. Migration 1071 does not re-create 566's trigger and does
   not modify 540's function.
3. **Migration 540's asset_id-keyed guard not resurrected.** It was fail-open for unlisted
   charts and it is what D-02 arose from. 1071 is generation-keyed instead, per 588's own
   instruction.
4. **No `ka_gochara` row inserted into `build_protected_assets`.** That row is exactly what
   left the century writer in a permanent BUILD-PROTECTED error. Only the retired sweep is
   registered.
5. **No `generation='3.0'` blanket block.** It would break the live century writer. The
   protection for gen-3.0 is the transitive one described in §5.1, stated with its
   dependence on a measured fact.
6. **No writer touched.** Nothing under `platform/python-sidecar/pipeline/orchestrator/writers/`
   was modified; the orchestrator contract is FROZEN and `ka_gochara_sweep` stays retired,
   snapshot-protected, never rebuilt.
7. **No `platform-mcp/src/tools/kala_views/` file touched** (Pūrṇa-owned).
8. **`.github/workflows/deploy.yml` not touched**; migrations `1035`/`1036` in
   `supabase/migrations` not touched; no applied migration (≤1070) edited.
9. **The clear-spec resolution order not restructured.** Making the routes generation-aware
   is a materially larger change that would put the path being secured at risk. See O-1.
10. **No credential, connection string or `DATABASE_URL` echoed, logged or committed.**
    `redact.py --scrub` run over the worktree before commit.

---

## 9. What remains open

| id | item | owner |
|---|---|---|
| **O-1** | `build_protected_assets.protected_generations` is still unread by both Clear routes (`SELECT asset_id` only) — asset-level withholding standing in for a generation-level claim. Harmless for `ka_gochara_sweep` (all its rows are v1); a §N.8 coarseness that a future generation-aware clear-spec pass should close. | L3 / cockpit |
| **O-2** | **Production application of migrations 1071 and 1072 is UNVERIFIED.** Happens at deploy. The verification to run afterwards: `SELECT tgname FROM pg_trigger … relname='kala_gochara_windows'` returns both triggers; `SELECT target_table FROM asset_registry WHERE asset_id='ka_gochara'` returns `kala_gochara_windows_v2`; `SELECT count(*) FROM build_protected_assets` equals the number of distinct charts holding v1 rows (3 at time of writing). | deploying session |
| **O-3** | Re-registering `ka_gochara_sweep` in `build_protected_assets` partially reverses a native instruction of 2026-08-23. The reasoning is §5.2 (a retired asset is never built, so the D-02 failure mode cannot recur) but it is a **judgment call surfaced for native confirmation**, not an authorisation this session granted itself. | native |
| **O-4** | The gen-3.0 corpus has no direct guard of its own — only the transitive coverage of §5.1, which depends on the measured fact that both gen-3.0 charts also hold v1 rows. If a chart ever holds gen-3.0 rows and no v1 rows, a generation-blind per-chart DELETE against it would not be refused. A gen-3.0 guard needs a second override the century writer sets, i.e. a writer change, which is out of B1's scope. | L3 |
| **O-5** | `asset_throughput` holds `state='error'` rows for `ka_gochara_sweep` on all three charts — a retired asset stuck in a permanent error state. Not displayed (`stats/route.ts` filters `is_active = true`) and not touched here. | cockpit |

---

## 10. Files changed

**New**
- `platform/migrations/1071_kala_gochara_windows_generation_guard.sql`
- `platform/migrations/1072_kala_b1_registry_truth_and_sweep_protection.sql`
- `platform/tests/integration/kala_gochara_windows_generation_guard.db.test.ts`
- `platform/scripts/__tests__/gochara_seed_target_table_parity.test.ts`
- this file

**Modified**
- `platform/src/app/api/cockpit/clear/route.ts` — `is_active` filter; stale migration-540 comment corrected
- `platform/src/app/api/cockpit/clear/execute/route.ts` — same, re-derived identically
- `platform/src/lib/cockpit/clearScopeFilter.ts` — `is_active` exclusion on all four branches
- `platform/scripts/seed/asset_registry_seed.ts` — `ka_gochara` `target_table`/`count_sql`/description corrected; two stale "migration 540 guard" pointers corrected
- `platform/src/app/api/cockpit/clear/__tests__/route.authz.test.ts` — fixture matches production; B1 block added
- `platform/src/app/api/cockpit/clear/__tests__/scope_filter.test.ts` — B1 block added
- `platform/src/lib/cockpit/__tests__/assetClearSpec.test.ts` — live-vector evidence block added
