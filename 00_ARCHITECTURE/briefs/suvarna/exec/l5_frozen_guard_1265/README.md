# 1265: L5 frozen-history guards (owner-path package, HELD)

Not a migration. The SQL lives here and is applied only by `l5_frozen_guard_exec.py` (GATE_V2, plan hash, dry run, apply, rollback leg). It must never be copied
under `platform/migrations` or `platform/supabase/migrations`. SS rulings N-104, N-107, N-108.

| file | what |
|---|---|
| `l5_frozen_guard_exec.py` | the executor (modes `--count --dry-run --apply --rollback-dry-run --rollback`; every mode needs `--expect-plan`) |
| `sql/1265_l5_frozen_row_guards.sql` | forward script, run as `amjis_app` inside the executor's transaction |
| `sql/1265_l5_frozen_row_guards.ROLLBACK.sql` | the exact inverse (drops the 8 triggers and 6 functions) |
| `sql/verify_before_apply.sql`, `sql/verify_after_apply.sql` | read-only checks for the operator (hash-bound in the plan) |
| `make_plan.py`, `plan.txt` | regenerates / holds the exact plan text; prints executor sha256, unbound and bound plan hash |

## The chart-delete allowance (N-108), exact location for migration 1275's author
* Discriminator: `public.l5_frozen_chart_cascade_authorizes(p_chart uuid)`, section **C1b** of `sql/1265_l5_frozen_row_guards.sql` (dollar tag `$cascade$`):
  true only when `pg_trigger_depth() >= 2` (the child delete runs as an action of the parent's AFTER trigger; a direct DELETE is depth 1, measured on PG 15 and 17)
  **and** no row of `public.charts` has that id (in the cascade the parent row is already deleted). Fails closed if `charts` is absent or unreadable by the invoker.
* It is called by the four DELETE guards right after the consent-withdrawal exception (`l5_frozen_withdrawal_authorizes`, same file, `$helper$`).
* Residual, pinned by `test_known_limit_a_user_created_trigger_can_reach_depth_two_for_a_chart_id_that_does_not_exist`: a role that can CREATE a trigger can reach
  depth 2, but the chart must still be absent, so a chart that exists is never bypassable; orphan rows (no chart) are what the 1275 FKs eliminate.
* Reusable fixture: `platform/python-sidecar/tests/l5_frozen_guard_world.py` (`make_world`, `add_chart_fks` = the 1275 `chart_id -> charts(id) ON DELETE CASCADE`
  on the four tables, `seed_sql`, the mirrored roles). The acceptance test is `test_ONE_FIXTURE_direct_delete_refused_then_chart_delete_removes_every_row_of_that_chart_only`
  in `platform/python-sidecar/tests/test_l5_frozen_guard_1265_guards.py` (fixture `cascaded`).
* The cascade runs as the owner of the referencing table (`amjis_app`), whoever deletes the chart; the guard sees that.

## Order
1. S-L1 done. 2. the append-only `mi_bhavisya` writer and the `assetClearSpec` change deployed (`--writer-commit` is checked). 3. 1275 (the cascade FKs) in the same window.
4. dry run, then apply with the dry run's `--expect-evidence`, same interpreter. RLS is not armed by this package.
