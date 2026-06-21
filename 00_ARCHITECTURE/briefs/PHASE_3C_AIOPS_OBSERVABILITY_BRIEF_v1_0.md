---
artifact: PHASE_3C_AIOPS_OBSERVABILITY_BRIEF_v1_0.md
version: 1.0
status: ACTIVE
authored: 2026-05-18
authored_by: Claude Code (analysis/backend-data-pipeline-perf-audit)
parent_plan: 00_ARCHITECTURE/PHASE_3_CARRY_FORWARDS_EXECUTION_PLAN_v1_0.md §E
purpose: >
  Phase 3C investigation + fix proposal: AIOps routing override observability
  hardening. Root cause of 2026-05-15 3-day silent demote + three concrete
  additions to prevent recurrence.
---

# Phase 3C — AIOps Override Observability Hardening Brief

## §A — Investigation Findings

### Finding 1 — `llm_config_audit` already exists but has a coverage gap

**File:** `platform/migrations/050_aiops_config_audit.sql`

The `llm_config_audit` table exists with columns: `id, occurred_at, actor_user_id, action, scope, stack, call_type, before_value, after_value, notes`.

The Control Panel API routes write to this table on:
- `PUT /api/admin/aiops/routing/[stack]/[call_type]` → action `'set_routing'`
- `DELETE /api/admin/aiops/routing/[stack]/[call_type]` → action `'reset_routing'`
- `PUT /api/admin/aiops/audit/[id]/revert` → action `'revert'`

**Coverage gap:** A direct database INSERT/UPDATE/DELETE on `llm_stack_routing_override` (e.g., via psql session, migration, or background job) does **NOT** create an audit entry. The 2026-05-15 regression was exactly this scenario — an override row was inserted directly into the DB, not through the Control Panel API.

### Finding 2 — No `expires_at` column on `llm_stack_routing_override`

The table schema (`047_aiops_routing_override.sql`) has no TTL mechanism:
```sql
CREATE TABLE IF NOT EXISTS llm_stack_routing_override (
  scope TEXT, stack TEXT, call_type TEXT,
  primary_model TEXT, fallback_model TEXT,
  updated_at TIMESTAMPTZ, updated_by TEXT,
  PRIMARY KEY (scope, stack, call_type)
);
```
Once a row is inserted (whether via API or direct DB), it persists indefinitely unless explicitly deleted. AIOps automation that writes an emergency override cannot set a self-expiring time limit.

### Finding 3 — No "active overrides" review query

There is no document or query view that lets the native review currently-active (non-expired) overrides at a glance. The Control Panel UI surfaces override state via `/api/admin/aiops/state` but this requires the UI to be open.

### Finding 4 — `runtime_config.ts` TTL is not enforced

`runtime_config.ts:43` queries:
```sql
SELECT * FROM llm_stack_routing_override WHERE scope = 'global'
```
No `expires_at` filter — even if a TTL column existed, the resolver would not honor it until this query is updated.

---

## §B — Root Cause of 2026-05-15 3-Day Silent Demote

The regression ran 3 days undetected because:
1. An override row was inserted directly into the DB (not via the Control Panel API)
2. No audit log entry was created → no visibility into the insertion
3. No TTL on the row → it persisted until manually diagnosed and deleted
4. No active-override review cadence → no one checked the DB table for 3 days

---

## §C — Three Concrete Additions

### Addition (a) — DB trigger: audit-log ALL mutations to `llm_stack_routing_override`

**Migration:** `platform/migrations/057_aiops_routing_override_trigger.sql`

A PostgreSQL trigger fires AFTER INSERT/UPDATE/DELETE on `llm_stack_routing_override` and writes to `llm_config_audit`. This catches:
- Direct DB inserts (psql, migration, background job)
- API-initiated changes (the API routes will now have DUPLICATE audit entries — acceptable, and can be deduplicated by the `notes='db_trigger'` flag)
- Prevents double-write risk: since the trigger fires separately from the API route, we add a `notes='db_trigger'` flag to distinguish trigger-generated rows from API-generated rows

**Dedup note:** API routes write one `llm_config_audit` row; the trigger writes a second. This is intentional: the API row carries the full user context (actor_user_id = Firebase UID), the trigger row carries `actor_user_id = updated_by` which may be 'system' or 'db_direct'. This gives a complete audit trail.

### Addition (b) — `expires_at` column + resolver enforcement

**Migration:** `platform/migrations/058_aiops_routing_override_ttl.sql`

Adds `expires_at TIMESTAMPTZ DEFAULT NULL` to `llm_stack_routing_override`. NULL = permanent (no expiry). Non-NULL = row is ignored after that timestamp.

**`runtime_config.ts` update (1 line):** Change the routing override SELECT to:
```sql
SELECT * FROM llm_stack_routing_override 
WHERE scope = 'global' AND (expires_at IS NULL OR expires_at > NOW())
```

**Policy:** AIOps automation that writes emergency overrides MUST set `expires_at = NOW() + INTERVAL '72 hours'` as a default. Manual super-admin overrides via the Control Panel may omit `expires_at` (permanent policy overrides).

**Control Panel API update:** The PUT route already sets the row via UPSERT. A `expires_at` parameter (optional, null by default) should be added to `routingOverrideBodySchema` and included in the UPSERT.

### Addition (c) — Active overrides review query

**File:** `00_ARCHITECTURE/aiops_overrides_active.sql`

A SQL file the native can run periodically (or add to a daily monitoring script) to see all currently-active (non-expired) overrides alongside their audit trail.

---

## §D — Governance Amendment

**Amendment:** Add the following to `ONGOING_HYGIENE_POLICIES_v1_0.md §N` (or a new §O if §N is occupied):

> **AIOps Routing Override Policy (Phase 3C, 2026-05-18):**
> 1. All writes to `llm_stack_routing_override` MUST set `expires_at` when the override is temporary (AIOps automation: default 72h; emergency: 4h). Permanent policy overrides (e.g., nim stack synthesis → gemini-2.5-flash) may use NULL.
> 2. All writes SHOULD use the Control Panel API route (`PUT /api/admin/aiops/routing/[stack]/[call_type]`) so that the actor_user_id is captured correctly. Direct DB writes are captured by the trigger but will log `actor_user_id = updated_by` which may be 'system'.
> 3. The `aiops_overrides_active.sql` query MUST be reviewed at each session open when evaluating production state. Add to session-open checklist §G step 0.

---

## §E — Acceptance Gate Assessment

| Gate | Target |
|------|--------|
| `override_writes_logged_to_session_log` | yes — DB trigger (migration 057) captures ALL mutations |
| `override_ttl_or_expiry_added` | yes — migration 058 adds `expires_at` column + resolver enforcement |
| `override_audit_table_or_view_created` | yes — `aiops_overrides_active.sql` query file |
| `governance_amendment_drafted` | yes — amendment text above |

---

## §F — Implementation Checklist

1. Write `platform/migrations/057_aiops_routing_override_trigger.sql`
2. Write `platform/migrations/058_aiops_routing_override_ttl.sql`
3. Update `platform/src/lib/models/runtime_config.ts` — add `expires_at` filter to routing override SELECT
4. Update `platform/src/app/api/admin/aiops/routing/[stack]/[call_type]/route.ts` — add `expires_at` to UPSERT
5. Update `platform/src/app/api/admin/aiops/_parse.ts` or equivalent — add `expires_at` to body schema (optional)
6. Write `00_ARCHITECTURE/aiops_overrides_active.sql`
7. Draft governance amendment (ONGOING_HYGIENE_POLICIES)

All in one commit (§E.3C.3 of the parent plan).

---

*End PHASE_3C_AIOPS_OBSERVABILITY_BRIEF_v1_0.md. Authored 2026-05-18.*
