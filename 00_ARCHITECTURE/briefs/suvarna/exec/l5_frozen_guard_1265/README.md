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
* `brahma_prospective_ledger` and `brahma_mimamsa_prediction_ledger` are guarded here; the 1275 worker's current tree adds them to its list (chart delete then empties them; verified 28/28 against that tree). If 1275 ships without them, a chart delete leaves their rows.
* Reusable fixture: `platform/python-sidecar/tests/l5_frozen_guard_world.py` (`make_world`, `add_chart_fks` = the `chart_id -> charts(id) ON DELETE CASCADE`
  on the four tables, `seed_sql`, the mirrored roles, `charts` with RLS on). The acceptance test is `test_ONE_FIXTURE_direct_delete_refused_then_chart_delete_removes_every_row_of_that_chart_only`
  in `platform/python-sidecar/tests/test_l5_frozen_guard_1265_guards.py` (fixture `cascaded`). The 1275 PR's own fixture was run against this SQL in both orders (26/26).
* The cascade runs as the owner of the referencing table (`amjis_app`), whoever deletes the chart.

## STANDING CONSTRAINT (SS): no FORCE ROW LEVEL SECURITY on `charts` without first revisiting this guard
The chart-deletion discriminator is `SECURITY DEFINER` (owner `amjis_app` = owner of `charts`) and relies on the owner bypassing the row security `charts` has today
(`relrowsecurity` true, `relforcerowsecurity` false). With `FORCE ROW LEVEL SECURITY` the owner is subject to the policies too, the definer would not see an existing chart, and a
DIRECT delete of frozen rows would read "chart absent" and be authorized. So it is machine-checked, not prose only:
* the SQL script's gate and post-check RAISE if `charts.relforcerowsecurity` is true; the discriminator itself RAISES at run time (every delete then fails loudly);
* the executor refuses in the preconditions (`pre_standing_constraint_charts_not_force_rls`, with a `WARN: STANDING CONSTRAINT VIOLATED` line in the dry run) and again after (`post_...`);
* `sql/verify_charts_rls_constraint.sql` (read-only, as the reader) returns `verdict = OK` or a `FAIL: ...` row; items 6 of `verify_before_apply.sql` / `verify_after_apply.sql` report the same. Run it in every dry run and in every W-step read-back.
Revisiting means: re-derive the discriminator for an owner that is subject to row security (e.g. a `BYPASSRLS` owner role for the helper, or a policy for it), re-run the tests, re-approve the plan hash.

**Is this README inside the bound hash inputs? No.** The plan hash covers: the plan text rendered by the executor, `EXPECTED_DIFF`, the sha256 of the forward and rollback SQL, of the verify files, of the executor itself, and the GATE_V2 pins. This README and `plan.txt` (a printed copy) are not inputs. The constraint's CODE (script gate/post-check/discriminator, executor checks, the new verify file) IS in the inputs.

## Review round 2 (REVIEW_3033) in one place: residuals and invariants an operator must know
* **Helper ACL (LOW-2).** `l5_frozen_withdrawal_authorizes` and `l5_frozen_chart_cascade_authorizes` are REVOKEd from PUBLIC (the SECURITY DEFINER one would be an RLS-bypassing chart-existence oracle). EXECUTE is granted only to the non-owner roles that hold DELETE on a frozen table at apply time (today `role_orchestrator`, `data_plane_builder`). The guards are SECURITY INVOKER, so a role granted DELETE LATER gets a loud `permission denied for function l5_frozen_...` until it is granted EXECUTE too. The post-check asserts PUBLIC false and every such role true.
* **Consent-exception invariant (LOW-4).** The exception reads `chart_subject_consent` / `chart_subject_deletion_disputes` with the INVOKER's rights. Invariant, RAISED by the script's gate and post-check (and queryable in `verify_before_apply.sql` item 7 / `verify_after_apply.sql` item 8): no non-owner, non-superuser role holds a write on those tables AND DELETE on a frozen table (otherwise it could forge a `withdrawn` row and delete). Today only `amjis_app` (owner) holds both. Side effect: the consent sweep can only run as the owner.
* **Chart-id rename residual (LOW-3).** Before 1275's FKs exist, a role holding UPDATE on `charts` and DELETE on a frozen table (`role_orchestrator`) can `UPDATE charts SET id = <new> WHERE id = <old>` and then delete the old chart's rows directly (NOT EXISTS reads "chart gone"). After 1275 the rename is refused by the FK (NO ACTION). Hence: apply 1275 in the same window, right after 1265 (either order works).
* **1275 coverage (LOW-5).** The 1275 worker's current tree adds `brahma_prospective_ledger` and `brahma_mimamsa_prediction_ledger`; if it ships without them a chart delete leaves their rows and the owner can then delete them as orphans.
* **`session_replication_role = replica` (NIT-8, superuser only):** bypasses the two ORIGIN-enabled triggers this package does not own (the captured builder guard, `trg_bmpl_freeze_confirmed`); the 8 new triggers are ENABLE ALWAYS and are not bypassed.
* **Jsonb representation (NIT-2, cosmetic, accepted):** `base_rate 0.5 -> 0.50` and jsonb `1.0 -> 1.00` pass the jsonb comparison.
* **TRUNCATE self-test (NIT-9):** skipped for `mimamsa_predictions` when the invoker (`amjis_app`) has no TRUNCATE privilege; that guard is covered by the post-check (trigger existence and ENABLE ALWAYS) and the mirrored-role tests.
* **Executor exit codes:** 92 interpreter/driver differs from the dry run, 93 no verifying GATE_V2 marker, 94 wrong target (administrator, database, server major, superuser, `current_user <> session_user`), 95 test env outside pytest, 96 `commit()` itself raised (state unknown: read `outcome.json`, check the database). The administrator must be a member of `pg_read_all_stats` (`pre_admin_can_see_all_sessions`); a builder session whose state is hidden counts as busy.

## Order
1. S-L1 done. 2. the append-only `mi_bhavisya` writer and the `assetClearSpec` change deployed (`--writer-commit` is checked). 3. 1275 (the cascade FKs) right after, same window (either order works; tested).
4. dry run, then apply with the dry run's `--expect-evidence`, same interpreter. RLS is not armed by this package.
