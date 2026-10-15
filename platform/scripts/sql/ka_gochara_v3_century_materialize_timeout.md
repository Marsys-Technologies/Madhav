# J-GOCHARA-TIMEOUT preparation (SR-A4-01)

Status: **code preparation only; no approved value, migration or production execution**.

The adjacent `.sql.in` file is intentionally outside both migration directories and
has unresolved integer tokens. `platform/scripts/migrate.ts:586` discovers only
`.sql` files in those directories. This file cannot silently become a routine migration.

(I) INTERPRETATION: pre-build prepares the exact-row SQL mechanics while leaving the
numeric migration unbuilt. The alternative, selecting a value now, conflicts with
`00_ARCHITECTURE/control/kalayantra/plan_model.json:21598`: report figures and the
proposal do not authorize a timeout change. `PRE-D-GOCHARA-TIMEOUT` in the surrogate
journal conditionally approves only the independently measured value; SR-A4-01
permits preparation without early production activation.

Before creating a numbered migration:

1. Bind independent read-only executor receipts to the actual registry row/current
   timeout, named longest **completed** run id/status/duration and policy provenance
   (`plan_model.json:21550`). Obtain the effective D-GOCHARA-TIMEOUT outcome and exact
   approved arithmetic. Do not use the test values as live evidence.
2. Replace both tokens with those measured/approved positive integer literals; keep
   the exact asset id, one-column UPDATE and complete readback guards. Allocate a
   fresh number above current origin/main and every open `kalayantra/*` branch in
   **both** migration directories, checking the protected list at that time. This job
   lists remote heads but deliberately reserves no migration number.
3. Replay the rendered migration on the authentic current-main disposable baseline
   through the full runner, then independently review that exact head. The included
   SQL suite replays genuine historical migrations 167/202/223/342/417/560/562;
   it proves mechanics, **not current-main baseline readiness or a live value**.
4. Preserve R9 hold, retained data, J landing phase, live-build migration collision
   and lease checks, G8 backup/restore, dry-run/request-bound acceptance and
   quiescence. Wait for a running leased build to release before migration. The
   registry lock is concurrency protection; it grants no lease or dispatch authority.
5. Use protected merge/deployment policy and independently accept deployed commit,
   migration/value and every-other-column/neighbour readbacks before guarded DONE.
   A budget update never dispatches a build or lifts a hold.

The SQL leaves transaction ownership with the runner, rejects missing/alias-only
and unexpected baselines, permits an exact replay, and verifies the entire registry
against a snapshot with only the approved target column changed. It aborts on
wrong-table, wrong-row, extra-column, broad-update and trigger-side-effect mutations.

The Postgres suite runs under the existing mandatory `kala-db-tests` directory
selection; the governance test pins that coverage and mutates weakening attempts.
No registry seed, writer, contract or census input changes, so no aggregate output
requires regeneration. The cockpit still owes independent review and all activation
gates above; this preparation does not earn the item's guarded completion steps.
