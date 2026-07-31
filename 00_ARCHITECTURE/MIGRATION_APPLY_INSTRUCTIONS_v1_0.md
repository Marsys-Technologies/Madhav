---
artifact: MIGRATION_APPLY_INSTRUCTIONS_v1_0.md
version: 1.1
status: CURRENT
produced_during: M3-PRE-D-GOVERNANCE-2026-05-01
authoritative_side: Claude
update_policy: >
  One-shot. Delete or mark SUPERSEDED after migrations 022–031 are applied
  to the live DB and the verification query returns 5/5 expected tables.
consumers:
  - Native (Madhav) — applies migrations before M3-D-VALIDATOR-REDTEAM (D1) opens
  - Next session at M3-D open — re-runs the verification query as a precondition
changelog:
  - v1.0 (2026-05-01, M3-PRE-D-GOVERNANCE-2026-05-01): Initial authoring. Live
    verification query against DATABASE_URL (host: amjis pg, db: amjis, user:
    amjis_app) returned 0/5 of {dasha_periods, signal_states, kp_sublords,
    varshaphala, shadbala} present. Connection itself succeeded (current_database
    + current_user query returned valid values; 59 public tables total). Five
    migrations therefore unapplied: 022, 023, 024, 025, 031. The other five
    migrations (026 audit_events, 027 query_plans, 028 msr_signals_add_columns,
    029 chart_facts_indexes, 030 cgm_edges_indexes) were not directly verified
    by this query (their target tables already pre-existed in the schema), so
    the safe assumption is "may or may not be applied" — applying via Option A
    or Option B below is idempotent for already-applied migrations only if the
    SQL files use `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`;
    inspect each file or use the migration tracker to be safe.
  - v1.1 (2026-05-01): Removed incorrect supabase db push reference. Project
    uses Google Cloud SQL exclusively. Option A replaced with Cloud SQL Auth
    Proxy method.
---

# Migration Apply Instructions — Migrations 022–031

**Status — 2026-05-01**: Live verification of `DATABASE_URL` from
`platform/.env.local` was attempted in `M3-PRE-D-GOVERNANCE-2026-05-01`.
Connection succeeded (DB: `amjis`, user: `amjis_app`, 59 public tables
already present). Verification query found **0 of 5** expected tables:

| Migration | Expected table | Present in live DB? |
|---|---|---|
| `022_dasha_periods.sql` | `dasha_periods` | ❌ MISSING |
| `023_signal_states.sql` | `signal_states` | ❌ MISSING |
| `024_kp_sublords.sql` | `kp_sublords` | ❌ MISSING |
| `025_varshaphala.sql` | `varshaphala` | ❌ MISSING |
| `031_shadbala.sql` | `shadbala` | ❌ MISSING |

The other five migrations (026 audit_events, 027 query_plans, 028
msr_signals_add_columns, 029 chart_facts_indexes, 030 cgm_edges_indexes)
target tables that already existed in the schema; this query did not
distinguish "migration applied" from "table pre-existed". Inspect the
SQL files directly if exact apply-state of those five is required.

**Apply before M3-D-VALIDATOR-REDTEAM (D1) opens.** Run from the
project root `~/Vibe-Coding/Apps/Madhav`.

## Option A — psql via Cloud SQL Auth Proxy (standard method)

This project uses Google Cloud SQL (instance: madhav-astrology:asia-south1:amjis-postgres).
There is no Supabase. Do not use any supabase CLI commands.

The DATABASE_URL in platform/.env.local points to 127.0.0.1:5433 which is the
Cloud SQL Auth Proxy port. Ensure the proxy is running before applying migrations:

  nc -z 127.0.0.1 5433 && echo "Proxy UP" || echo "Proxy DOWN — start it first"

To start the proxy if it is not running:
  cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres --port=5433 &

Once the proxy is up, apply migrations:

  # credential redacted — see SAMAPTI security incident INC-3, 2026-07-30 (this
  # DSN previously held a live `postgres`-role superuser credential, mislabelled
  # as amjis_app; supply your own via the PGPASSWORD-backed secret, never a literal)
  export DATABASE_URL="postgresql://amjis_app:${PGPASSWORD:?}@127.0.0.1:5433/amjis"

  for f in platform/migrations/022_dasha_periods.sql \
            platform/migrations/023_signal_states.sql \
            platform/migrations/024_kp_sublords.sql \
            platform/migrations/025_varshaphala.sql \
            platform/migrations/026_audit_events.sql \
            platform/migrations/027_query_plans.sql \
            platform/migrations/028_msr_signals_add_columns.sql \
            platform/migrations/029_chart_facts_indexes.sql \
            platform/migrations/030_cgm_edges_indexes.sql \
            platform/migrations/031_shadbala.sql; do
    echo "=== Applying $f ==="
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
  done

All migration files are idempotent (CREATE TABLE IF NOT EXISTS,
CREATE INDEX IF NOT EXISTS, ADD COLUMN IF NOT EXISTS). Re-running is safe.

## Option B — psql direct

```bash
DATABASE_URL=$(grep '^DATABASE_URL=' platform/.env.local | head -1 | sed 's/^DATABASE_URL=//' | sed 's/^"//;s/"$//')

for f in platform/migrations/022_dasha_periods.sql \
         platform/migrations/023_signal_states.sql \
         platform/migrations/024_kp_sublords.sql \
         platform/migrations/025_varshaphala.sql \
         platform/migrations/026_audit_events.sql \
         platform/migrations/027_query_plans.sql \
         platform/migrations/028_msr_signals_add_columns.sql \
         platform/migrations/029_chart_facts_indexes.sql \
         platform/migrations/030_cgm_edges_indexes.sql \
         platform/migrations/031_shadbala.sql; do
  echo "=== Applying $f ==="
  psql "$DATABASE_URL" -f "$f"
done
```

Inspect each migration file before re-applying if you suspect 026–030
may already be present; non-idempotent SQL (e.g., a bare `CREATE INDEX`
without `IF NOT EXISTS`, or an `ALTER TABLE ... ADD COLUMN` against a
column that already exists) will error.

## Verification

After apply, run from the project root:

```bash
DATABASE_URL=$(grep '^DATABASE_URL=' platform/.env.local | head -1 | sed 's/^DATABASE_URL=//' | sed 's/^"//;s/"$//')

psql "$DATABASE_URL" -c "
  SELECT table_name
  FROM information_schema.tables
  WHERE table_schema='public'
    AND table_name IN ('dasha_periods','signal_states','kp_sublords','varshaphala','shadbala')
  ORDER BY table_name;"
```

**Expected:** 5 rows.

| table_name |
|---|
| dasha_periods |
| kp_sublords |
| shadbala |
| signal_states |
| varshaphala |

## Closure

Once verification returns 5 rows, set this file's frontmatter
`status: SUPERSEDED` and add a closing changelog entry naming the
session that confirmed the apply. Do not delete the file — keep it as
the audit trail for the M3-PRE-D ↔ M3-D handoff.
