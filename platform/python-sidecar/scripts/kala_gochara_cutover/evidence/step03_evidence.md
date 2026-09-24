# Step 3 evidence — Guard

Runbook step 3 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Guard — (table, generation) trigger for 'v1'/'3.0' + N-6a century is_active=false
- **Gate:** DELETE/UPDATE/TRUNCATE on protected generations fail loudly; '4.0' writes pass; century cannot dispatch
- **Reversal:** step03_reversal.sql (DROP trigger + restore is_active)
- **DSN target:** production via Cloud SQL proxy 127.0.0.1:5433, database `amjis`, principal `amjis_app`
- **Operator / principal:** subagent (l3/gochara-autonomous-wp0-7, §7.B tranche 1) as `amjis_app`

<!-- Run outcomes are appended below by the step scripts (--evidence). -->

## 2026-09-24 — STOPPED (privilege precondition unmet; gate never reached; production unchanged)

Run order per brief §12.15 (E-014): step 3 first, ahead of steps 0–2.

**Attempted:** `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f step03_guard_n6a.sql`
(DSN = production proxy 127.0.0.1:5433/amjis, credentials sourced from the main
checkout's `platform/.env.local`; values never printed).

**Result:** `ERROR: permission denied for schema public` at the first statement
(`CREATE OR REPLACE FUNCTION kala_gochara_generation_guard()`). The transaction
aborted before any object was created; the in-transaction gate probe never ran.

**Why (verified read-only, same session):**

- `has_schema_privilege('amjis_app','public','CREATE')` = **false**
- `amjis_app`: `rolsuper=false, rolcreatedb=false, rolcreaterole=false`, **no role memberships**
- schema `public` is owned by **`data_plane_schema_owner`** — no credential for that role
  (or `postgres`) exists in any local env file (`platform/.env`, `platform/.env.local`,
  `.env.rag` all carry `amjis_app` only)

`amjis_app` owns `kala_gochara_windows` and can `UPDATE asset_registry` (the strategic
session's is_active half, E-014 addendum 1), but creating the guard function requires
schema-`public` CREATE, which it does not have.

**Post-attempt verification (rollback clean, production byte-identical to pre-state):**

- `to_regprocedure('kala_gochara_generation_guard()')` → NULL (no function)
- triggers on `kala_gochara_windows` → 0
- `ka_gochara_v3_century_materialize.is_active` = false (pre-existing, strategic session — unchanged by this attempt)
- `build_protected_assets` → 0 rows (unchanged)
- `kala_gochara_windows` generations → `v1=38287, 3.0=1830` (unchanged)

**Consequence:** the tranche HALTS here per the brief's failed-gate rule. The durable
(trigger) half of N-6a — the half that survives a re-seed — is unapplied. Production's
current protection remains the fragile half only (`is_active=false`, undone by any
re-seed until PR #2734 merges).

**Escalation:** ESCALATIONS.md **E-015** — the step must be run by a principal with
CREATE on schema public (`data_plane_schema_owner` / `postgres`); exact command and
verification queries recorded there.
