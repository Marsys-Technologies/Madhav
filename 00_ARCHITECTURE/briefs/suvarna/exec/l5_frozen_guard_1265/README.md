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
  `NOT EXISTS (SELECT 1 FROM public.charts WHERE id = p_chart)`. Inside the RI cascade of `DELETE FROM charts` the parent row is already gone; for a direct
  DELETE of a row whose chart exists it never is. It is checked FIRST in each of the four DELETE guards, before the consent-withdrawal exception
  (`l5_frozen_withdrawal_authorizes`, `$helper$`). `pg_trigger_depth()` is deliberately not used (2 in the cascade AND in any trigger a role can create).
* **SECURITY DEFINER (owner `amjis_app` = owner of `charts`) on purpose**: `charts` has row-level security ON; under the invoker's rights a role that no policy lets
  see the chart (e.g. `data_plane_builder`) would read "absent" and be authorized. The post-check asserts the definer flag and the owner.
* Residual, pinned by tests: rows whose chart is not in `charts` (orphans) and rows of a chart deleted earlier in the same transaction are deletable directly;
  the 1275 FKs leave no orphans. Not spoofable by a setting, a role name, a decoy trigger (refused while the chart exists), a SECURITY DEFINER function or a DO block.
* `brahma_prospective_ledger` and `brahma_mimamsa_prediction_ledger` are guarded here but are NOT in 1275's table list: a chart delete leaves their rows (no FK) and
  they are then deletable only through the orphan residual above or the consent exception; give them the same `chart_id -> charts(id) ON DELETE CASCADE` in 1275.
* Reusable fixture: `platform/python-sidecar/tests/l5_frozen_guard_world.py` (`make_world`, `add_chart_fks` = the `chart_id -> charts(id) ON DELETE CASCADE`
  on the four tables, `seed_sql`, the mirrored roles, `charts` with RLS on). The acceptance test is `test_ONE_FIXTURE_direct_delete_refused_then_chart_delete_removes_every_row_of_that_chart_only`
  in `platform/python-sidecar/tests/test_l5_frozen_guard_1265_guards.py` (fixture `cascaded`). The 1275 PR's own fixture was run against this SQL in both orders (26/26).
* The cascade runs as the owner of the referencing table (`amjis_app`), whoever deletes the chart.

## Order
1. S-L1 done. 2. the append-only `mi_bhavisya` writer and the `assetClearSpec` change deployed (`--writer-commit` is checked). 3. 1275 (the cascade FKs) right after, same window (either order works; tested).
4. dry run, then apply with the dry run's `--expect-evidence`, same interpreter. RLS is not armed by this package.
