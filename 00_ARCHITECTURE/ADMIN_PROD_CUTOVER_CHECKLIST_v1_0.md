---
artifact: ADMIN_PROD_CUTOVER_CHECKLIST
canonical_id: ADMIN_PROD_CUTOVER_CHECKLIST
version: 1.0
status: READY
date: 2026-06-25
purpose: Push the full admin tab arc (overhaul + in-portal password mgmt) to PROD
operator_note: Migrations and deploy are run BY THE OPERATOR (Abhisek), not Cowork. Cowork cannot apply prod SQL or trigger deploys.
---

# Admin Tab → Production Cutover

Ships both admin workstreams (already on `main`): the overhaul (updated_at fix,
audit log, role mgmt) and in-portal password management.

## What goes to prod
- **Migration 332** `profiles.updated_at` (+ backfill) — required or every
  disable/enable/edit-username 500s in prod.
- **Migration 333** `admin_audit_log` table — required or audit writes silently
  fail (the helper swallows the error, so the tab "works" but logs nothing).
- **Code** (already on `main`): the password feature needs no migration; it ships
  with the deploy.

Both migrations are **idempotent** (`IF NOT EXISTS`) — safe to re-run.

---

## Pre-flight
- [ ] On `main`, `git pull`, confirm HEAD includes the password merge and the two
      migration files exist: `platform/migrations/332_*.sql`, `333_*.sql`.
- [ ] **Snapshot the DB before mutating** (per project rule — snapshot-before-rebuild).
      Take a Cloud SQL backup/export of the prod instance now.

## Step 1 — Start the Cloud SQL Auth Proxy (your machine)
```bash
cd platform/scripts
./start_db_proxy.sh        # brings up cloud-sql-proxy on 127.0.0.1:5433
# leave this running in its own terminal
```
Connection vars come from `.env.rag` (`DB_USER`, `DB_NAME`, `INSTANCE_CONNECTION_NAME`).

## Step 2 — Apply migrations IN ORDER (332 then 333)
> Order matters: 333's `admin_audit_log` FKs to `profiles`; apply 332 first.
> `--single-transaction` so a failure rolls back cleanly. `--set ON_ERROR_STOP=1`
> so it halts on the first error instead of plowing ahead.

```bash
# from repo root, proxy running on :5433
PGPASSWORD="$DB_PASSWORD" psql \
  -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
  --single-transaction --set ON_ERROR_STOP=1 \
  -f platform/migrations/332_profiles_updated_at.sql

PGPASSWORD="$DB_PASSWORD" psql \
  -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
  --single-transaction --set ON_ERROR_STOP=1 \
  -f platform/migrations/333_admin_audit_log.sql
```
**Do NOT** use a bulk `migrate.ts` / deploy auto-migrate — surgical apply only
(project rule N.4).

### Verify schema landed (still on the proxy)
```bash
PGPASSWORD="$DB_PASSWORD" psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" -c \
"SELECT column_name FROM information_schema.columns
 WHERE table_name='profiles' AND column_name='updated_at';"
# expect: updated_at

PGPASSWORD="$DB_PASSWORD" psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" -c \
"SELECT to_regclass('public.admin_audit_log');"
# expect: admin_audit_log (not null)
```

## Step 3 — Deploy the web app
`deploy.yml` auto-deploys on push to `main` **only if CI passes**. `main` currently
has pre-existing CI failures, so the auto `deploy-web` job will likely be SKIPPED.
Use the manual dispatch (it bypasses the CI gate — that's its documented purpose):

- [ ] GitHub → Actions → **deploy.yml** → **Run workflow** → branch `main`
      (this is `workflow_dispatch`, the emergency manual deploy path).
- [ ] Wait for `deploy-web` (and `deploy-sidecar` if relevant) to go green.

> Note: the pre-existing CI red is unrelated to the admin work, but it does mean a
> plain push won't auto-deploy. The manual dispatch is expected here, not a hack.

## Step 4 — Verify the Cloud Run revision is the new one
```bash
gcloud run services describe amjis-web --region asia-south1 \
  --format='value(status.traffic[0].revisionName)'
```
Confirm it matches the `main` HEAD SHA you just deployed (CDN/cache can lag 30–60s).

## Step 5 — Smoke test on PROD (madhav.marsys.in, not localhost)
Admin user-management ACs:
- [ ] **Disable then re-enable** a non-self test user → both succeed (proves the
      332 `updated_at` fix + DB-first PATCH). Previously this 500'd.
- [ ] **Edit username** on a test user → succeeds.
- [ ] **Audit log:** the above actions appear in "Recent admin activity" / Audit
      Log tab (proves 333 table is live).

Password ACs (7):
- [ ] **Create with password** → that user logs in immediately with it.
- [ ] **Create blank password** → reset-link fallback still appears.
- [ ] **Set password** on existing non-self user → new password works, old rejected.
- [ ] **Validation:** <8 chars + mismatch blocked.
- [ ] **Audit:** `set_password` + `create_user{password_set:true}` rows present; no
      plaintext password in `detail`.  `psql ... -c "SELECT action, detail FROM admin_audit_log ORDER BY created_at DESC LIMIT 5;"`
- [ ] **Email reset** still works as secondary option.

Then clean up any throwaway test users you created.

## Rollback
- Code: redeploy the previous Cloud Run revision (`gcloud run services update-traffic
  amjis-web --region asia-south1 --to-revisions <PREV>=100`).
- Schema: 332/333 are additive (new column + new table) — leaving them in place is
  harmless even if you roll the code back. No down-migration needed.

## Post-cutover follow-ups (not blockers)
- Add `autoComplete="new-password"` to the New User + SetPasswordDialog password
  inputs (browser autofill currently pre-fills them on localhost).
- The pre-existing `main` CI failures deserve their own triage session so CI is a
  trustworthy signal again.

*End ADMIN_PROD_CUTOVER_CHECKLIST v1.0.*
