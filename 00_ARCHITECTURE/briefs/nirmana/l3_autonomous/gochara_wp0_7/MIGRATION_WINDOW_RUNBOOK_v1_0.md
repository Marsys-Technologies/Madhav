---
artifact: MIGRATION_WINDOW_RUNBOOK
version: "1.0"
status: ACTIVE
date: 2026-09-30
owner: Stream A (Karma) — Pravāha A5.1 operational window
authority: steward message M20260930T175125-c011 (Stream A owns the merge/deploy pipeline)
scope: PR #2765 (pravaha/a5-migrations) — migrations 1153–1157, the FROZEN gochara contracts
---

# Migration window runbook — gochara contracts 1153–1157

The five migrations are **protected** (`PROTECTED_PUBLIC_SCHEMA_MIGRATIONS`,
`platform/scripts/migrate.ts:138–144`): the routine runner refuses them with an
actionable error; the only route that applies them is a manual `deploy.yml`
dispatch with `gochara_contracts_schema_migration=true` (deploy.yml:64, gated at
deploy.yml:952, executed via `APPLY_GOCHARA_CONTRACTS_SCHEMA_MIGRATION` at
deploy.yml:1037). The window is per-file atomic; a failure mid-window is
recovered by re-dispatching — an applied file is tracked by hash and never
re-run.

## 0. Preconditions (all must hold before dispatch)

1. **#2765 merged to main** and the merge SHA's CI is green (the dispatch gate,
   `platform/scripts/ci/dispatch_gate.ts`, requires CI green; the emergency
   override is not authorized for this window).
2. **Pending set is exactly 1153–1157.** Against production (read-only role),
   run:
   ```sql
   -- must return 0 rows: nothing in the protected set has leaked through the
   -- routine runner or any other path
   SELECT filename FROM _migrations_applied
   WHERE filename IN ('1153_gochara_sky_event_substrate.sql',
                      '1154_gochara_rule_path_registry.sql',
                      '1155_gochara_relationship_record.sql',
                      '1156_gochara_eval_window.sql',
                      '1157_gochara_av_polarity_declaration.sql');
   ```
   and confirm every earlier migration is applied (no gap below 1153; the
   runner enforces ordered application itself, but verify the immediately
   preceding recorded file is ≥ 1152 and no untracked gap exists).
3. **Routine-runner leakage = 0 beyond the set**: no routine deploy since the
   merge has applied or partially applied any of the five (the migrate.ts
   guard makes this impossible by construction; the query in (2) is the
   evidence).
4. **Preflights** (`platform/python-sidecar/scripts/kala_gochara_cutover/preflight_115{3..7}_*.sql`)
   are byte-identical to the gates embedded in the migrations themselves
   (asserted by `tests/unit/migrations/gochara_a5_1_contract_static.test.ts`),
   so the window runs them in-transaction. A pre-flight RAISE aborts that
   file's transaction; nothing half-applies. No separate manual preflight run
   is required, but running them read-only beforehand against production is
   encouraged and must end with `preflight 115N: all checks passed`.

## 1. Dispatch (after steward queues #2765 and it merges)

```bash
M=$(gh pr view 2765 --json mergeCommit -q .mergeCommit.oid)   # the merge SHA on main
gh workflow run deploy.yml --ref main \
  -f ci_gate=require-ci-green \
  -f gochara_contracts_schema_migration=true
```

- `DEPLOY_SHA` resolves to `github.sha` of `main` at dispatch time — dispatch
  immediately after the merge so `DEPLOY_SHA` == the merge commit `$M`; verify
  in the run log (`Deployment checkout mismatch` guard at deploy.yml:445/596
  fails loudly otherwise).
- GitHub may require the native to approve the environment; if the run sits
  `waiting`, report `--ref A5.1` and park — that approval is native-only.
- Never cancel the run mid-flight (deploy.yml header: the real deploy jobs
  serialise and queue; killing one can leave a half-applied state).

## 2. Post-checks (read-only, against production, after the run is green)

1. **All five recorded, in order, hash-tracked:**
   ```sql
   SELECT filename, applied_at FROM _migrations_applied
   WHERE filename LIKE '115_gochara_%' ORDER BY filename;
   -- expect exactly 1153..1157, applied_at ascending in filename order
   ```
2. **Tables present** (one row per name):
   `ka_gochara_sky_convention`, `ka_gochara_physical_object`,
   `ka_gochara_sky_event`, `ka_gochara_contact_identity`,
   `ka_gochara_generation_seal`, `ka_gochara_convention_bridge`,
   `ka_gochara_contact` (1153); `ka_gochara_predicate`, `ka_gochara_factor`,
   `ka_gochara_rule_path`, `ka_gochara_rule_path_prerequisite`,
   `ka_gochara_rule_path_soft_factor`, `ka_gochara_rule_path_seal` (1154);
   `ka_gochara_relationship_record`, `ka_gochara_record_prerequisite` (1155);
   `ka_gochara_eval_window`, `ka_gochara_eval_window_record` (1156);
   `ka_gochara_av_polarity_declaration` (1157).
   ```sql
   SELECT tablename FROM pg_tables
   WHERE schemaname='public' AND tablename LIKE 'ka\_gochara\_%' ORDER BY 1;
   ```
3. **Constraints present and convalidated** — no constraint left `NOT VALID`:
   ```sql
   SELECT conrelid::regclass, conname FROM pg_constraint
   WHERE connamespace='public'::regnamespace AND NOT convalidated
     AND conrelid::regclass::text LIKE 'ka\_gochara\_%';
   -- expect 0 rows
   ```
4. **Triggers present** on the new tables (guards:
   `ka_gochara_insert_only`, `ka_gochara_global_write_guard`,
   `ka_gochara_chart_statement_lock`, `ka_gochara_substrate_chart_lock`,
   supersede/seal/coverage/membership guards per migration):
   ```sql
   SELECT tgrelid::regclass, tgname FROM pg_trigger
   WHERE NOT tgisinternal AND tgrelid::regclass::text LIKE 'ka\_gochara\_%'
   ORDER BY 1,2;
   ```
   Compare against the `CREATE TRIGGER` statements in the five files.
5. **Read-only smoke query** (helpers callable, seal predicate answers):
   ```sql
   SELECT public.ka_gochara_generation_is_sealed(
            '482012f1-710e-4a25-994a-93821f5871aa'::uuid, '3.0');  -- expect f
   SELECT count(*) FROM public.ka_gochara_sky_event;      -- expect 0
   SELECT count(*) FROM public.ka_gochara_rule_path;      -- expect 0
   ```
6. **Existing data untouched — ka_gochara integrity still t.** Evaluate the
   11-conjunct `integrity_check_sql` registered for asset `ka_gochara` in
   `asset_registry` (post-1150 UTC date-compare text; see step09 soak
   evidence); it must return `t` under the session default (UTC). The
   `kala_gochara_windows` rows for generations 'v1' and '3.0' must be
   byte-unchanged (count and a checksum before/after the window if a baseline
   was captured).

## 3. Failure handling

- A migration RAISES (preflight or DDL): the file's transaction rolls back;
  files before it stay applied. Fix the environment (ADK-0026: fix the data,
  not the detector), then **re-dispatch the same command** — applied files are
  hash-tracked and skipped.
- Any unexpected diff in post-check 6: stop, `pravaha block A5.1 --detail …`,
  and do not proceed to A5.2.

## 4. FU-1 — docs note (never edit an applied migration)

ASTRA v1.6 FU-1: the 1153 wording "every chart-scoped table CHECKs the
canonical chart" is imprecise. Correct description of the enforcement, as
applied: the generation seal has **no direct CHECK** — its guard routes
through the restricted lock helper `ka_gochara_lock_chart` (1153:441–456),
which binds the transaction to one canonical chart at the lock boundary;
prerequisites and window memberships **inherit chart scope through their
composite FKs** (1155:647–649, 1156:346–353). Enforcement is sufficient for
N18 (one chart per transaction, canonical-only under D-SCOPE); only the
prose in the 1153 header comment and the `ka_gochara_lock_chart` refusal
message is imprecise. Because 1153 will by then be applied, this correction
lives here and must **not** be made by editing the migration.
