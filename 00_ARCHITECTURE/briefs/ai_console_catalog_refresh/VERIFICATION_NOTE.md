# AI Console catalogue refresh — source verification

Status: implemented, independently reviewed, committed in the isolated source
branch; not merged or deployed. This is not production execution evidence.

## Behavior

- Each connected API and authorized CLI has a scoped refresh icon and last-refresh
  timestamp. Stale sources refresh sequentially when the page opens. Server leases,
  a fifteen-minute successful freshness window and a one-minute cooldown bound work.
- APIs use authenticated model-list requests, never generation during refresh.
  Models newly discovered are not labeled individually tested.
- CLI discovery checks the configured execution host's installed version and
  subscription authentication. Codex app-server and Claude control initialization
  supply native model-specific efforts. Refresh does not upgrade CLI binaries.
- Saved choices/defaults/efforts and individual test evidence survive failures.
  Missing capabilities are shown for repair, not silently replaced. Manually tested
  but now-unlisted CLI models retain their proof and expose Model default only.
- Known binary/version changes require an explicit execution test. Same-version
  legacy installations without a stored fingerprint retain prior readiness without
  creating proof; actual execution revalidation establishes the baseline.
- Warm execution caches can acquire newly listed models/efforts without inference,
  only when the installed identity still matches the tested binary.

## Evidence and boundaries

- Actual local Codex metadata discovery returned seven subscription models and
  model-specific effort lists without a turn/prompt request. This Mac's Codex
  installation is not the production VM's installation.
- API discovery/refresh tests use fixtures, not paid keys. No paid API inference was
  made in this feature work. The earlier conversation's cumulative API cost is not
  measured or claimed here.
- Independent migration review: safe after tightening effort-array validation.
  Independent integrated review findings were repaired: legacy rollout downgrade,
  false catalogue-failure status, stale manual effort evidence and warm cache misses.
- Disposable localhost PostgreSQL: 35 tests passed, 2 skipped; migration first apply,
  rerun, rollback, constraints, ownership, grants, epoch/credential fencing and
  listed+manual model disappearance covered. No application database used.
- UI tests cover refresh icons, stale-on-entry behavior, named-only CLI role seeding,
  exact effort choices and retention of cached choices after failures.
- Full source gates and final counts are recorded in SESSION_CLOSE.json. An old
  remote-runner fixture was expanded for the new metadata-only cache-miss path.

Governance drift inspection has two LOW unqualified live chart-schema checks:
the unrelated local database at 127.0.0.1:5433 did not provide authentication.
No chart database credentials, writes or infrastructure changes were undertaken.
These are booked to deployment preflight, not presented as successful live checks.

## Release requirements

1. Green protected PR/merge checks against the exact current main.
2. Recheck live coordination lease and release authority.
3. Back up and ship private-VM `server.mjs` and `catalog-protocol.mjs` as a pair before
   switching the web application; verify the private bridge and retain rollback.
4. Apply migration 1301 through the protected routine migration runner and verify
   it actually applied; no direct production SQL or edit of historical migration 1300.
5. Confirm exact deployed SHA, authenticated refresh/model/effort UI and role-save
   behavior. Real subscription execution and any paid API probe remain separately
   labeled, bounded tests; discovery alone does not prove those execution paths.
