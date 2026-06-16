---
brief_id: M2_D56_OBSERVABILITY
karn_session_name: KARN-W1-R3-OBSERVABILITY
wave: 1
stream: E
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-29
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (migrations + writer wiring + deploy + verify)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: none
  blocks: F1 (provenance audit), F2 (eval harness depends on these for measurement)
parallel_stream_note: |
  Three other Wave-1 briefs run concurrently: M2_PHASE_ALPHA (Stream A,
  read-only audit), M2_C6_VECTOR_SEARCH_FILTER (Stream B, retrieval TS),
  M2_B3_CLUSTER_RECLUSTER (Stream C, JSON outputs). All disjoint paths.
  This brief OWNS migrations 026 + 027; no other Wave-1 brief touches migrations.
estimated_time: 1 day single Claude Code session

scope_summary: |
  Two missing observability tables. PROBE 6 confirmed audit_events doesn't
  exist; PROBE 7 confirmed query_plans doesn't exist. The audit writer code
  exists in the codebase per static analysis but the tables it should write
  to are absent. This brief creates the migrations, applies them, wires the
  writers if needed, and verifies that fresh queries populate both tables.

  Migration 026: audit_events (matches the schema audit-writer code expects).
  Migration 027: query_plans (flat-mirror of QueryPlan schema for direct query).

  After this lands, F1 and F2 (later waves) can compute aggregate metrics
  over the audit data, and ad-hoc PROBE 6/7 reruns work cleanly.

may_touch:
  - platform/migrations/026_audit_events.sql                         # CREATE migration
  - platform/migrations/027_query_plans.sql                          # CREATE migration
  - platform/src/lib/audit/**                                        # if writer wiring missing/broken
  - platform/src/app/api/chat/consume/route.ts                       # if writer call site is missing
  - platform/python-sidecar/pipeline/writers/**                      # only if existing audit writer needs adjustment
  - platform/src/lib/audit/__tests__/**                              # CREATE/extend writer tests
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_D56_OBSERVABILITY.md   # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_D56_VERIFICATION_<DATE>.txt             # CREATE

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)                                       # UI/UX stream
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_PHASE_ALPHA.md        # other Wave-1
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C6_VECTOR_SEARCH_FILTER.md  # other Wave-1
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B3_CLUSTER_RECLUSTER.md   # other Wave-1
  - platform/src/components/**                                       # UI/UX
  - platform/src/app/**                                              # EXCEPT consume/route.ts if writer call site needs adding
  - platform/src/hooks/**                                            # UI/UX
  - platform/src/lib/retrieve/**                                     # not in scope this session
  - platform/src/lib/router/**                                       # not in scope this session
  - platform/src/lib/bundle/**                                       # not in scope
  - platform/src/lib/synthesis/**                                    # not in scope
  - platform/migrations/022-025                                      # Stream A's migration range
  - platform/migrations/001-021                                      # historical, do not modify
  - 025_HOLISTIC_SYNTHESIS/**                                        # source-of-truth
  - 035_DISCOVERY_LAYER/**                                           # off-limits

acceptance_criteria:
  AC.1: |
    Pre-flight grep confirms whether audit writer code exists in the codebase.
    Document findings: which writer file(s), what schema they expect, what is the
    insert SQL look like.
  AC.2: |
    Migration 026 (audit_events) created at platform/migrations/026_audit_events.sql.
    Schema matches the writer's INSERT shape from AC.1 (or, if writer doesn't exist,
    matches a reasonable schema that supports per-tool result counts, latency,
    query_text, query_id, user_id, created_at).
    Mandatory columns: id (uuid), query_id (uuid), query_text (text), tool_bundles (jsonb),
    latency_ms (int), user_id (text), created_at (timestamptz default NOW()).
  AC.3: |
    Migration 027 (query_plans) created at platform/migrations/027_query_plans.sql.
    Schema flat-mirrors the QueryPlan TypeScript interface fields where reasonable.
    Mandatory columns: id, query_plan_id (uuid), query_id (uuid), query_text (text),
    query_class (text), domains (text[]), planets (text[]), houses (int[]),
    forward_looking (boolean), tools_authorized (text[]), graph_seed_hints (text[]),
    edge_type_filter (text[]), audience_tier (text), router_confidence (numeric),
    router_model_id (text), manifest_fingerprint (text), schema_version (text),
    created_at (timestamptz default NOW()).
  AC.4: |
    Both migrations apply cleanly against live DB via psql or via the project's
    migration runner. Verify with:
      \\d audit_events  → returns the table
      \\d query_plans   → returns the table
  AC.5: |
    Writer wiring verified or completed. If existing writer code refers to a
    different table name OR uses a different schema, update writer to match
    the new tables. If no writer exists, scaffold a minimal writer at
    platform/src/lib/audit/audit_writer.ts that writes one row per query to
    audit_events (called from consume/route.ts onFinish callback) and one row
    per classify completion to query_plans (called from the classify step or
    its caller).
  AC.6: |
    Send 5 fresh queries through the deployed Consume tab post-deploy. After
    ~30s, verify:
      SELECT COUNT(*) FROM audit_events WHERE created_at > NOW() - INTERVAL '5 minutes';
        ≥ 5
      SELECT COUNT(*) FROM query_plans WHERE created_at > NOW() - INTERVAL '5 minutes';
        ≥ 5
    Capture both queries' output to M2_D56_VERIFICATION_<DATE>.txt.
  AC.7: |
    npm test passes at pre-existing baseline (no new failures).
  AC.8: |
    Cloud Run revision amjis-web rebuilt and serving 100% via cloud_build_submit.sh.
  AC.9: |
    PROBE 6 + PROBE 7 from retrieval_diagnostic_probes.sql re-run (read-only)
    return non-error results. PROBE 6 shows recent audit_events with tool_bundles.
    PROBE 7 shows recent query_plans with populated fields.
  AC.10: |
    This brief's frontmatter `status` flipped to COMPLETE.
  AC.11: |
    git status shows ONLY: 2 new migration files, possibly audit writer file
    additions/edits, possibly consume/route.ts wiring update, the verification
    txt, this brief's status flip. NO other src/components, src/app (except
    route.ts), src/hooks, src/lib (except audit/), python-sidecar, or other
    migrations modified.

halt_conditions:
  - Auth Proxy unreachable
  - Migration 026 or 027 already exists with conflicting schema (means a different stream beat us; reconcile manually)
  - Writer code path can't be cleanly wired without touching files in must_not_touch
  - npm test introduces NEW failures
  - Cloud Build / Cloud Run deploy failure
  - Branch is not redesign/r0-foundation
  - Pre-existing uncommitted modifications to migrations/** or audit/**
---

# CLAUDECODE_BRIEF — M2_D56_OBSERVABILITY (Wave 1, Stream E)

## §1 — Why this session

PROBE 6 (2026-04-29) errored: `relation "audit_events" does not exist`. PROBE 7 errored: `relation "query_plans" does not exist`. The audit writer code is referenced in the codebase per static analysis (the new query pipeline post-Phase 11A cutover writes to it), but the tables themselves are absent. This means: every query since the new pipeline shipped has had its audit write fail silently. We have no production observability for retrieval health.

Without these tables, F1 (provenance audit) and F2 (eval harness) can compute their metrics only via ad-hoc trace inspection, which doesn't scale.

This brief creates both tables, ensures the writers are wired, and verifies they populate on fresh traffic.

## §2 — Pre-flight self-diagnostics (mandatory)

### §2.1 — Branch + working tree
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
test "$(git branch --show-current)" = "redesign/r0-foundation" || HALT "wrong branch"
git status --short
# HALT if any of these have uncommitted modifications:
#   platform/migrations/026_*.sql  (must not exist yet)
#   platform/migrations/027_*.sql  (must not exist yet)
#   platform/src/lib/audit/**
#   platform/src/app/api/chat/consume/route.ts
```

### §2.2 — Migration range available
```bash
ls platform/migrations/ | grep -E "^02[6-7]_" && HALT "migration 026 or 027 already exists"
ls platform/migrations/ | tail -3
# Confirm next available number is 026 and 027.
```

### §2.3 — DB connectivity (Auth Proxy)
```bash
nc -z 127.0.0.1 5433 || {
  bash platform/scripts/start_db_proxy.sh &
  for i in {1..30}; do nc -z 127.0.0.1 5433 && break; sleep 1; done
  nc -z 127.0.0.1 5433 || HALT "proxy failed"
}

# Confirm tables don't already exist:
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -t -c "SELECT to_regclass('audit_events');" | grep -q "^ *$" || HALT "audit_events already exists"
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -t -c "SELECT to_regclass('query_plans');"  | grep -q "^ *$" || HALT "query_plans already exists"
```

### §2.4 — Existing writer code grep
```bash
# Find audit writer
grep -rn "audit_events" platform/src platform/python-sidecar 2>/dev/null | head -20 > /tmp/audit_grep.txt
grep -rn "query_plans" platform/src platform/python-sidecar 2>/dev/null | head -20 >> /tmp/audit_grep.txt
cat /tmp/audit_grep.txt
# If no matches, the writers don't exist; AC.5 falls to "scaffold minimal writer."
# If matches, those files describe the expected schema; align migrations accordingly.
```

### §2.5 — Test baseline
```bash
cd platform && npm test --silent 2>&1 | tail -5 > /tmp/test_baseline.txt && cat /tmp/test_baseline.txt
```

## §3 — Implementation steps

### §3.1 — Read existing audit writer code (if any)

Per §2.4 grep results, read each file that mentions `audit_events` or `query_plans`. Note:
- The INSERT SQL the writer expects.
- The columns + types it writes.
- The call site (where in the pipeline does the writer fire?).

If the writer doesn't exist, design the minimal one in §3.4.

### §3.2 — Compose migration 026 (audit_events)

Create `platform/migrations/026_audit_events.sql`:

```sql
BEGIN;

CREATE TABLE IF NOT EXISTS audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id UUID NOT NULL,
  query_plan_id UUID,
  query_text TEXT,
  query_class TEXT,
  user_id TEXT,
  chart_id UUID,
  conversation_id UUID,
  tool_bundles JSONB,
  latency_ms INTEGER,
  audit_status TEXT DEFAULT 'ok',
  audit_warnings JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_query_id ON audit_events(query_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_query_class ON audit_events(query_class);

COMMIT;
```

Adapt the column list to whatever the existing audit writer (per §3.1) actually writes, if it's different. The columns above are the minimal required set for downstream eval/integrity briefs.

### §3.3 — Compose migration 027 (query_plans)

Create `platform/migrations/027_query_plans.sql`:

```sql
BEGIN;

CREATE TABLE IF NOT EXISTS query_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_plan_id UUID UNIQUE NOT NULL,
  query_id UUID NOT NULL,
  query_text TEXT NOT NULL,
  query_class TEXT NOT NULL,
  domains TEXT[],
  planets TEXT[],
  houses INTEGER[],
  forward_looking BOOLEAN DEFAULT FALSE,
  audience_tier TEXT,
  tools_authorized TEXT[],
  history_mode TEXT,
  panel_mode BOOLEAN DEFAULT FALSE,
  expected_output_shape TEXT,
  graph_seed_hints TEXT[],
  graph_traversal_depth INTEGER,
  edge_type_filter TEXT[],
  vector_search_filter JSONB,
  dasha_context_required BOOLEAN,
  bundle_directives JSONB,
  router_model_id TEXT,
  router_confidence NUMERIC,
  manifest_fingerprint TEXT,
  schema_version TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_plans_query_id ON query_plans(query_id);
CREATE INDEX IF NOT EXISTS idx_query_plans_created_at ON query_plans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_plans_query_class ON query_plans(query_class);
CREATE INDEX IF NOT EXISTS idx_query_plans_domains ON query_plans USING GIN(domains);

COMMIT;
```

### §3.4 — Apply migrations

Apply via the project's migration runner (look in `platform/scripts/` or `package.json`):

```bash
# Likely:
cd platform
npm run migrate:up
# or
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -f migrations/026_audit_events.sql
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -f migrations/027_query_plans.sql
```

Verify:
```bash
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -c "\d audit_events"
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -c "\d query_plans"
```

### §3.5 — Verify or wire writer

If §3.1 found existing audit writer code:
- Confirm the writer's INSERT SQL matches the migration schema.
- If column names differ, adapt the writer (NOT the migration — the migration is the canonical schema; writer matches it).

If no writer code exists:
- Create `platform/src/lib/audit/audit_writer.ts` with two functions:
  - `writeAuditEvent({ queryId, queryText, queryClass, userId, chartId, conversationId, toolBundles, latencyMs })`
  - `writeQueryPlan(queryPlan: QueryPlan & { queryId: string })`
- Both use the existing `query` helper from `@/lib/db/client`.
- Wire `writeAuditEvent` into `consume/route.ts` `onFinish` callback (after streamText completes).
- Wire `writeQueryPlan` into the classify step's emitStep / completion path.

### §3.6 — Tests

Add unit tests for the writers in `platform/src/lib/audit/__tests__/audit_writer.test.ts`:
- Mock the DB query helper.
- Assert correct SQL + params for each writer.
- Assert error handling on DB failure (the writer must not crash the request).

```bash
cd platform
npm test --silent 2>&1 | tail -5 > /tmp/test_after.txt
diff /tmp/test_baseline.txt /tmp/test_after.txt
# HALT if failure count increased.
```

### §3.7 — Deploy

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
bash platform/scripts/cloud_build_submit.sh
```

Confirm new revision is serving 100%.

### §3.8 — Post-deploy verification

Send 5 queries through the deployed Consume tab. Wait ~30s. Then:

```bash
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -c "SELECT COUNT(*) FROM audit_events WHERE created_at > NOW() - INTERVAL '10 minutes';" \
  -c "SELECT id, query_class, latency_ms, jsonb_array_length(tool_bundles) AS tools FROM audit_events ORDER BY created_at DESC LIMIT 5;" \
  -c "SELECT COUNT(*) FROM query_plans WHERE created_at > NOW() - INTERVAL '10 minutes';" \
  -c "SELECT query_class, domains, planets, tools_authorized FROM query_plans ORDER BY created_at DESC LIMIT 5;" \
  > 00_ARCHITECTURE/BRIEFS/M2_D56_VERIFICATION_$(date +%Y-%m-%d).txt
```

Both COUNT queries must return ≥5. The detail queries must show populated rows.

If COUNT=0 for either table after 5 fresh queries, the writer wiring is broken. HALT and report.

### §3.9 — Re-run PROBE 6 + PROBE 7

```bash
psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -v ON_ERROR_STOP=off \
  -f platform/scripts/retrieval_diagnostic_probes.sql 2>&1 | \
  awk '/PROBE 6|PROBE 7/,/===/'  >> 00_ARCHITECTURE/BRIEFS/M2_D56_VERIFICATION_$(date +%Y-%m-%d).txt
```

Both probes must return non-error results.

### §3.10 — Closing summary + status flip

Standard closing summary per execution plan §3.4. Flip this brief's status to COMPLETE.

## §4 — Hard constraints

- **Migration numbers 026 + 027 only.** Stream A owns 022–025 and adds them in later waves; do not encroach.
- **Schema is the canonical source.** If existing writer code differs, adapt the writer.
- **No edits to retrieve/, router/, bundle/, synthesis/.** Other Wave-1 briefs own those.
- **Halt if pre-flight checks fail.** Especially: the migrations must not pre-exist.

## §5 — Closing checklist

- [ ] Pre-flight §2.1–§2.5 PASS
- [ ] Existing audit writer code grep documented
- [ ] Migration 026 created
- [ ] Migration 027 created
- [ ] Both migrations applied; tables exist
- [ ] Writer code present (existing or scaffolded) and aligned with schema
- [ ] Writer tests pass
- [ ] npm test failure count = baseline
- [ ] Cloud Run deployed
- [ ] 5 fresh queries populate both tables (verified)
- [ ] PROBE 6 + PROBE 7 return clean
- [ ] M2_D56_VERIFICATION_<DATE>.txt has all evidence
- [ ] git status clean of out-of-scope changes
- [ ] Brief status COMPLETE

---

*End of M2_D56_OBSERVABILITY. Status: COMPLETE (2026-04-30).*

## Kickoff prompt

```
You are running KARN-W1-R3-OBSERVABILITY.

Read 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_D56_OBSERVABILITY.md as
the governing scope. Branch is redesign/r0-foundation. Do NOT read
CLAUDECODE_BRIEF.md at the project root — UI/UX stream owns it.

This session is part of Project KARN. For cross-session context:
- 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md (operating rules)
- 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md (history)
- 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §3 (autonomous brief contract)

This brief creates migrations 026 + 027 and wires the audit writers if
needed. Do NOT touch migrations 022-025 (Stream A range) or any other
Wave-1 brief file. Run autonomously per §3 implementation steps. Halt only
on halt_conditions. Complete fully including deploy + post-deploy
verification.

At session close, append a standardized closing entry to
PROJECT_KARN_SESSION_LOG.md per the protocol §2 entry format. Use
karn_session_name = KARN-W1-R3-OBSERVABILITY.
```
