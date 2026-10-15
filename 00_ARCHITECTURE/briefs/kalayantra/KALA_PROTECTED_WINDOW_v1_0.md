---
artifact: KALA_PROTECTED_WINDOW
version: "1.0"
status: CURRENT
produced_on: 2026-10-08
produced_in: Claude Code, owner-approved change after the 2026-10-08 deploy outage (migration 1330)
changelog:
  - "1.0 (2026-10-08): first version: Kāla protected public-schema window, routine-runner skip, CI guard."
---

# Kāla protected public-schema window: operator note

## Why it exists

The routine production migrator (`amjis_app`) has USAGE but **not CREATE** on schema `public`. Migration
1330 (four `CREATE TABLE`s plus a `GRANT USAGE ON SCHEMA public`) merged as an ordinary migration. Every
production deploy then failed at **Apply Routine DB Migrations** with `permission denied for schema public`.
A Kāla migration that creates objects in `public` has to be applied through a protected window, the same way
the Gochara contract tables are.

## What the window applies

It applies every file listed in **`platform/scripts/kala_protected_migrations.txt`**. The list has one filename
per line in ascending order, and `#` starts a comment. The deploy job **Apply Protected Public-Schema
Migrations** (environment `data-plane-production-cutover`) runs three steps:

1. Grant the temporary capability (`jataka-schema-capability.ts grant`).
2. Run `migrate.ts --only <every listed file>`.
3. Revoke the capability (`revoke`). This step always runs, even if step 2 fails.

A listed file that is already applied is skipped: `--only` checks its sha256 and does not execute it. So a
filename is **never removed** from the list.

The routine runner never fails on a listed file. When a listed file is still pending, the routine path logs a
`::warning::` that names the file and the dispatch command, skips the file, and keeps applying the later routine
migrations. A merged Kāla table migration therefore cannot block another campaign's deploy.

## Dispatch

```bash
gh workflow run deploy.yml -f kala_schema_migration=true
```

The usual `ci_gate=require-ci-green` default applies. A required reviewer on the protected environment must
approve the run.

## Precondition

`migrate.ts --only` refuses to skip past an unapplied predecessor. **Every routine migration numbered below the
highest listed file must already be applied**, through an ordinary deploy, before you dispatch the window. If a
routine file between two listed files is pending, let one routine deploy finish first. It applies the routine
files and skips the Kāla ones. Then dispatch.

A routine migration must never depend on a Kāla-window table that is still pending. The routine runner applies
it anyway and it fails. Put such a file on the list too, so that it applies in the same window.

## Batching

- One dispatch applies every pending listed file, in ascending order, in one run. Batch several Kāla migrations
  into one window wherever you can. Each dispatch needs an environment approval.
- Each file is its own transaction. If file *k* fails, files before it stay applied, the capability is still
  revoked, and the job fails. Fix the problem with a **new** migration file, add it to the list, and dispatch
  again. Never edit a file that has already been applied.
- Other protected windows whose highest file is numbered above a pending Kāla file are blocked by the
  predecessor rule. Clear the Kāla window first.

## Builders: add the filename in the same PR

A Kāla migration that creates anything in `public` (TABLE, INDEX, FUNCTION, TYPE, TRIGGER, VIEW, MATERIALIZED
VIEW or SEQUENCE; an unqualified name counts as `public`), or that contains `GRANT … ON SCHEMA`, must add its
filename to `platform/scripts/kala_protected_migrations.txt` **in the same PR as the migration**. A grant-only
file that depends on a listed table belongs on the list as well (example: 1334).

The required **Governance Gates** check (`platform/scripts/governance/check_public_schema_migration_privilege.py`)
fails any routine migration that breaks this rule. It checks files numbered above 1333, the production baseline
on 2026-10-08, and every migration file the PR changes.

## Throwaway databases

Superuser rehearsal and CI databases apply the listed files through the routine path with
`MIGRATE_APPLY_PROTECTED=1`. migrate.ts honours this variable **only** when the `DATABASE_URL` host is
`localhost` or `127.0.0.1`. It is already set in:

- `.github/workflows/fresh_chart_smoke.yml`
- `fleet/local_db.sh`
- `fleet/precheck.sh`
