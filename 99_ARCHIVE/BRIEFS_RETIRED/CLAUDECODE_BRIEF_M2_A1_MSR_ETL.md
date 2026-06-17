---
brief_id: M2_A1_MSR_ETL
karn_session_name: KARN-W2-R1-MSR-ETL
wave: 2
stream: A
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 1 close
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (migration + extractor extension + re-ingest + verify)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: KARN-W1-R1-PHASE-ALPHA (provides exact 8-column gap list in M1_M2_ACTIVATION_MATRIX §5.3)
  blocks: M2_C1_CHART_FACTS_QUERY (downstream tool needs new columns), M2_E2_EVAL_HARNESS (golden eval needs full signal_type filtering)
parallel_stream_note: |
  Two other Wave-2 briefs run concurrently:
  - KARN-W2-R2-CHART-FACTS-ETL (Stream A, chart_facts §6/§7/§11/§13/§16 + lower P-tiers)
  - KARN-W2-R3-CGM-FULL-EDGES (Stream A, l25_cgm_edges 126 → ~339)
  All three Stream-A but disjoint targets:
  - W2-R1 owns msr_signals + l25_msr_signals
  - W2-R2 owns chart_facts (only)
  - W2-R3 owns l25_cgm_edges (only)
  All three may share migrations directory — coordinate migration numbers:
  W2-R1 = 028, W2-R2 = 029, W2-R3 = 030.
estimated_time: ½–1 day single Claude Code session

scope_summary: |
  W1-R1's Audit 2 surfaced 8 MSR source fields that exist in MSR_v3_0.md
  but are NOT columns in the live `msr_signals` table. Without these,
  the classifier cannot filter by signal_type (yoga vs aspect vs timing),
  by temporal_activation (natal vs dasha vs transit), or by valence
  (benefic vs malefic vs mixed). msr_sql is firing on 100% of queries
  but is returning the full 499 rows undifferentiated.

  Scope:
  1. Migration 028 adds 8 columns to msr_signals (HIGH 4 + MEDIUM 2 + LOW 2).
  2. Extend MSR YAML extractor to populate new columns from source fields.
  3. Re-ingest all 499 signals (delete + re-insert; idempotent).
  4. Mirror sync: l25_msr_signals already has `valence` — confirm parity.
  5. Verify column population rate ≥95% per HIGH column on `abhisek_mohanty`.
  6. Probe to confirm signal_type breakdown across all 499 rows is plausible.

  Net effect: msr_sql becomes filter-capable, classifier can pass
  signal_type[] / temporal_activation[] / valence[] from query intent.

may_touch:
  - platform/migrations/028_msr_signals_add_columns.sql                # CREATE migration
  - platform/python-sidecar/pipeline/extractors/msr_extractor.py       # extend to populate 8 new fields
  - platform/python-sidecar/pipeline/extractors/__tests__/test_msr_extractor.py   # extend tests
  - platform/python-sidecar/pipeline/loaders/msr_loader.py             # column mapping update
  - platform/src/lib/retrieve/msr_sql.ts                               # accept new filter params if classifier emits them
  - platform/src/lib/retrieve/types.ts                                 # MsrSqlInput type extension
  - platform/src/lib/retrieve/__tests__/msr_sql.test.ts                # add filter tests
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A1_MSR_ETL.md           # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_A1_VERIFICATION_<DATE>.txt               # CREATE — population fill rate evidence
  - 00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md                         # update §2 + §7 with new column states

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)                                         # UI/UX stream
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A2_CHART_FACTS_ETL.md   # sibling Wave-2
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B1_CGM_FULL_EDGES.md    # sibling Wave-2
  - platform/migrations/001-027                                        # historical, do not modify
  - platform/migrations/029_*                                          # W2-R2's range
  - platform/migrations/030_*                                          # W2-R3's range
  - platform/python-sidecar/pipeline/extractors/cgm_extractor.py       # W2-R3 territory
  - platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py  # W2-R2 territory
  - platform/src/components/**                                         # UI/UX scope
  - platform/src/app/**                                                # UI/UX scope (consume route untouched here)
  - platform/src/lib/retrieve/cgm_graph_walk.ts                        # explicit
  - platform/src/lib/retrieve/vector_search.ts                         # explicit
  - platform/src/lib/retrieve/pattern_register.ts                      # explicit
  - platform/src/lib/retrieve/resonance_register.ts                    # explicit
  - platform/src/lib/retrieve/cluster_atlas.ts                         # explicit
  - platform/src/lib/retrieve/contradiction_register.ts                # explicit
  - platform/src/lib/retrieve/manifest_query.ts                        # explicit
  - platform/src/lib/retrieve/temporal.ts                              # explicit
  - platform/src/lib/router/**                                         # not in scope this session
  - platform/src/lib/synthesis/**                                      # not in scope
  - 025_HOLISTIC_SYNTHESIS/**                                          # source-of-truth, read-only
  - 035_DISCOVERY_LAYER/**                                             # off-limits
  - 03_DOMAIN_REPORTS/, 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/       # off-limits

acceptance_criteria:
  AC.1: |
    Pre-flight gate (mandatory). Confirm:
      - branch is redesign/r0-foundation
      - working tree clean wrt files this brief targets (other UI/UX uncommitted work is fine)
      - gcloud ADC active; secret `amjis-db-password` (NOT `amjis-app-db-password`) accessible
      - Auth Proxy reachable on 127.0.0.1:5433
      - Current msr_signals row count = 499 (Wave-1 baseline). HALT if not.
  AC.2: |
    Migration 028 created at platform/migrations/028_msr_signals_add_columns.sql.
    Adds these 8 columns to msr_signals (all NULL-able for backward compatibility):
      signal_type           text          -- HIGH (filtering critical)
      temporal_activation   text          -- HIGH (filtering critical)
      valence               text          -- HIGH (already in l25_msr_signals; sync)
      entities_involved     jsonb         -- HIGH (entity-scoped queries)
      supporting_rules      jsonb         -- MEDIUM
      rpt_deep_dive         text          -- MEDIUM
      v6_ids_consumed       jsonb         -- LOW
      prior_id              text          -- LOW
    Plus indexes on the HIGH-priority filter columns:
      CREATE INDEX msr_signals_signal_type_idx ON msr_signals(signal_type);
      CREATE INDEX msr_signals_temporal_activation_idx ON msr_signals(temporal_activation);
      CREATE INDEX msr_signals_valence_idx ON msr_signals(valence);
    Plus a GIN index on entities_involved for jsonb @> queries:
      CREATE INDEX msr_signals_entities_involved_gin ON msr_signals USING GIN (entities_involved);
  AC.3: |
    Migration 028 applied cleanly to live DB.
    \\d msr_signals confirms all 8 new columns present, correctly typed, NULL-able.
    Indexes show in \\di msr_signals_*.
  AC.4: |
    msr_extractor.py extended to read these 8 fields from MSR_v3_0.md YAML signals:
      signal_type        ← from YAML key `signal_type`
      temporal_activation ← from YAML key `temporal_activation`
      valence            ← from YAML key `valence`
      entities_involved  ← from YAML key `entities_involved` (preserve as JSON array)
      supporting_rules   ← from YAML key `supporting_rules` (preserve as JSON array)
      rpt_deep_dive      ← from YAML key `rpt_deep_dive`
      v6_ids_consumed    ← from YAML key `v6_ids_consumed` (preserve as JSON array)
      prior_id           ← from YAML key `prior_id`
    Where the source field is missing on a particular signal, populate NULL (not empty
    string, not empty array — NULL).
  AC.5: |
    msr_loader.py UPSERT statement updated to include the 8 new columns in both INSERT
    column list and ON CONFLICT DO UPDATE SET.
  AC.6: |
    Re-ingest all 499 signals: run the MSR ingest pipeline end-to-end against MSR_v3_0.md.
    Pipeline approach:
      a) UPDATE existing rows by signal_id (NOT delete+insert; preserves UUIDs and FK refs).
      b) Verify post-ingest count = 499 (no rows lost, no duplicates).
      c) is_stale=false for all 499.
  AC.7: |
    Population fill rate verification (HIGH columns must be ≥95%):
      SELECT
        COUNT(*) FILTER (WHERE signal_type IS NOT NULL)::float / COUNT(*) AS signal_type_rate,
        COUNT(*) FILTER (WHERE temporal_activation IS NOT NULL)::float / COUNT(*) AS temporal_rate,
        COUNT(*) FILTER (WHERE valence IS NOT NULL)::float / COUNT(*) AS valence_rate,
        COUNT(*) FILTER (WHERE entities_involved IS NOT NULL)::float / COUNT(*) AS entities_rate
      FROM msr_signals
      WHERE native_id='abhisek_mohanty';
    All four MUST be ≥0.95. If any HIGH column is <0.95 fill rate, halt and report —
    means the source MSR_v3_0 YAML has more sparse signals than expected, OR extractor
    has a bug, OR a column-name mismatch between YAML and extractor mapping.
  AC.8: |
    Plausibility probe — signal_type distribution.
    SELECT signal_type, COUNT(*) FROM msr_signals GROUP BY signal_type ORDER BY COUNT(*) DESC;
    Expected (from MSR_v3_0): yoga, divisional-pattern, jaimini-pattern, aspect, dasha-timing,
    karaka, transit-trigger, ashtakavarga, panchang, sade-sati, more.
    No single signal_type should be >50% of total (that would suggest mass-default fallback).
    Capture distribution to verification txt file.
  AC.9: |
    Plausibility probe — valence distribution.
    SELECT valence, COUNT(*) FROM msr_signals GROUP BY valence ORDER BY COUNT(*) DESC;
    Expected values: benefic, malefic, mixed, neutral. None should be >70% (would suggest
    default-malefic or default-benefic bug).
  AC.10: |
    Plausibility probe — temporal_activation distribution.
    SELECT temporal_activation, COUNT(*) FROM msr_signals GROUP BY temporal_activation ORDER BY COUNT(*) DESC;
    Expected: natal-permanent (largest), dasha-conditional, transit-triggered. No empty string.
  AC.11: |
    msr_sql.ts extended to accept these optional filter params on its input:
      signal_type?: string[]
      temporal_activation?: string[]
      valence?: string[]
      entities_involved_any?: string[]   -- entity ID match using @>
    Each param adds AND clause to the SQL when non-null. Backward compatible: omitting
    params reproduces previous behavior. Add ≥4 tests in msr_sql.test.ts for the new
    filters. Do NOT modify the router prompt yet — that lands in W6 planner integrity.
  AC.12: |
    npm test passes at pre-existing baseline (no new failures relative to amjis-web-00030-4zk
    baseline of 958/13).
  AC.13: |
    Cloud Run revision rebuilt and serving 100% via cloud_build_submit.sh. Capture revision
    name to verification txt.
  AC.14: |
    Send 3 fresh queries through the deployed Consume tab post-deploy to confirm msr_sql
    still fires correctly with new schema. Verify via query_plans table that classifier output
    is unaffected. (msr_sql filter param emission is a W6 concern; this brief just makes the
    columns + filter capability available.)
  AC.15: |
    M1_M2_ACTIVATION_MATRIX.md §2 updated:
      - Mark all 8 previously-missing columns as PRESENT.
      - Update §7 (Current State Snapshot) to show msr_signals fully green wrt columns.
  AC.16: |
    Verification txt at 00_ARCHITECTURE/BRIEFS/M2_A1_VERIFICATION_<DATE>.txt captures:
      - migration apply log
      - per-column fill rate
      - signal_type/valence/temporal_activation distributions
      - 3 sample rows showing populated new fields
      - revision name + deployment confirmation
  AC.17: |
    git status shows ONLY:
      platform/migrations/028_msr_signals_add_columns.sql (new)
      platform/python-sidecar/pipeline/extractors/msr_extractor.py (modified)
      platform/python-sidecar/pipeline/extractors/__tests__/test_msr_extractor.py (modified)
      platform/python-sidecar/pipeline/loaders/msr_loader.py (modified)
      platform/src/lib/retrieve/msr_sql.ts (modified)
      platform/src/lib/retrieve/types.ts (modified)
      platform/src/lib/retrieve/__tests__/msr_sql.test.ts (modified)
      00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A1_MSR_ETL.md (status flip)
      00_ARCHITECTURE/BRIEFS/M2_A1_VERIFICATION_<DATE>.txt (new)
      00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md (modified)
    No other changes.
  AC.18: |
    This brief's frontmatter `status` flipped to COMPLETE.
    Closing summary appended to PROJECT_KARN_SESSION_LOG.md per protocol §3.1.

halt_conditions:
  - Auth Proxy unreachable on 127.0.0.1:5433 after 30s wait
  - gcloud ADC missing OR `amjis-db-password` secret unreadable (note: NOT `amjis-app-db-password`)
  - Branch is not redesign/r0-foundation (DO NOT switch)
  - Migration 028 fails to apply (rollback automatically; capture error)
  - Pre-existing baseline test failures different from 13 (stop and report)
  - Population fill rate <0.95 on any HIGH column after re-ingest (means extractor bug or sparse source)
  - signal_type or valence distribution shows >70% in single bucket (default-fallback bug)
  - msr_signals row count after re-ingest != 499 (data loss or duplicate insertion)
---

# CLAUDECODE_BRIEF — M2_A1_MSR_ETL (Wave 2, Stream A, Run 1)

## §1 — Why this session

Wave-1 Phase Alpha audit (W1-R1, see `00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md §2.1` and §5.3) ground-truthed the gap: `msr_signals` is 499 rows but missing 8 source fields that MSR_v3_0.md carries. Without `signal_type`, the msr_sql tool returns all 499 signals unfiltered, even when the classifier knows the query is about (say) yogas only. Without `temporal_activation`, predictive vs natal queries can't be distinguished at retrieval time. Without `valence`, comparative analysis (benefic vs malefic factors) requires post-hoc interpretation that's unreliable.

This brief closes that gap. After this lands:
- msr_sql becomes filter-capable on three operationally critical dimensions.
- The downstream `chart_facts_query` tool (W4-R3) can cross-reference msr_signals on `entities_involved`.
- The eval harness (W7-R1) can score retrieval precision per signal_type bucket.

**Not in scope:**
- Router prompt changes (classifier learning to emit the new filters). That's W6-R1.
- Domain field expansion from `domain` varchar collapse to `domains[]` jsonb. Tracked separately;
  this brief leaves `domain` as-is per AC.4 column list.

## §2 — Pre-flight self-diagnostics (mandatory)

Run these checks. If ANY fails, halt with a 5-line summary naming the failed check + suggested remediation.

### §2.1 — Branch state
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
test "$(git branch --show-current)" = "redesign/r0-foundation" || HALT "wrong branch"
```

### §2.2 — Working tree state
```bash
git status --short
# HALT only if uncommitted modifications exist on files this brief plans to create or modify
# (other UI/UX uncommitted work is fine; treat as orthogonal).
```

### §2.3 — gcloud auth
```bash
gcloud config list account --format="value(core.account)" | grep -q . || HALT "gcloud not authenticated"
gcloud auth application-default print-access-token > /dev/null 2>&1 || HALT "ADC missing"
```

### §2.4 — Secret name (W1-R1 finding)
```bash
# IMPORTANT: secret is `amjis-db-password`, NOT `amjis-app-db-password`.
PGPASSWORD=$(gcloud secrets versions access latest --secret="amjis-db-password" --project=madhav-astrology 2>/dev/null) || HALT "secret unavailable"
```

### §2.5 — Auth Proxy
```bash
nc -z 127.0.0.1 5433 || {
  bash platform/scripts/start_db_proxy.sh &
  for i in {1..30}; do nc -z 127.0.0.1 5433 && break; sleep 1; done
  nc -z 127.0.0.1 5433 || HALT "proxy failed to start"
}
```

### §2.6 — Baseline DB state
```bash
PGPASSWORD="${PGPASSWORD}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -c "SELECT COUNT(*) FROM msr_signals WHERE native_id='abhisek_mohanty';" -t
# Expected: 499
# HALT if count != 499 (Wave-1 baseline drift)
```

### §2.7 — Tests baseline
```bash
cd platform && npm test 2>&1 | tail -5
# Expected: 958 passed / 13 failed (post-W1-R3 baseline)
# HALT if very different (>2 delta either direction)
```

## §3 — Implementation steps

### §3.1 — Migration 028

Create `platform/migrations/028_msr_signals_add_columns.sql`:

```sql
-- Migration 028 — KARN-W2-R1 — Add 8 source fields to msr_signals
-- Predecessor: KARN-W1-R1-PHASE-ALPHA (Audit 2 finding §5.3)

BEGIN;

-- Add 8 new columns (all NULL-able for backward compat)
ALTER TABLE msr_signals
  ADD COLUMN IF NOT EXISTS signal_type         text,
  ADD COLUMN IF NOT EXISTS temporal_activation text,
  ADD COLUMN IF NOT EXISTS valence             text,
  ADD COLUMN IF NOT EXISTS entities_involved   jsonb,
  ADD COLUMN IF NOT EXISTS supporting_rules    jsonb,
  ADD COLUMN IF NOT EXISTS rpt_deep_dive       text,
  ADD COLUMN IF NOT EXISTS v6_ids_consumed     jsonb,
  ADD COLUMN IF NOT EXISTS prior_id            text;

-- Indexes on HIGH-priority filter columns
CREATE INDEX IF NOT EXISTS msr_signals_signal_type_idx
  ON msr_signals(signal_type) WHERE is_stale=false;
CREATE INDEX IF NOT EXISTS msr_signals_temporal_activation_idx
  ON msr_signals(temporal_activation) WHERE is_stale=false;
CREATE INDEX IF NOT EXISTS msr_signals_valence_idx
  ON msr_signals(valence) WHERE is_stale=false;
CREATE INDEX IF NOT EXISTS msr_signals_entities_involved_gin
  ON msr_signals USING GIN (entities_involved);

COMMIT;
```

Apply:
```bash
PGPASSWORD="${PGPASSWORD}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -f platform/migrations/028_msr_signals_add_columns.sql
```

Verify columns exist:
```bash
PGPASSWORD="${PGPASSWORD}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -c "\d msr_signals" | grep -E '(signal_type|temporal_activation|valence|entities_involved|supporting_rules|rpt_deep_dive|v6_ids_consumed|prior_id)'
# Expect 8 lines.
```

### §3.2 — Extend msr_extractor.py

Locate the YAML→row mapping function in `platform/python-sidecar/pipeline/extractors/msr_extractor.py`. It currently reads keys like `signal_id`, `signal_name`, `domains_affected`, `confidence`, `falsifier`, `classical_source` and produces a dict.

Add reads for the 8 new fields, preserving JSON arrays as Python lists (the loader will serialize to jsonb):

```python
# Add to the row-build dict (after existing fields)
"signal_type":         signal.get("signal_type"),
"temporal_activation": signal.get("temporal_activation"),
"valence":             signal.get("valence"),
"entities_involved":   signal.get("entities_involved"),  # list → jsonb
"supporting_rules":    signal.get("supporting_rules"),    # list → jsonb
"rpt_deep_dive":       signal.get("rpt_deep_dive"),
"v6_ids_consumed":     signal.get("v6_ids_consumed"),     # list → jsonb
"prior_id":            signal.get("prior_id"),
```

Where source field is missing → `None` (NOT empty string, NOT empty array).

Add unit tests in `__tests__/test_msr_extractor.py` covering:
- All 8 fields populated (happy path, sample signal that has them all)
- All 8 fields missing (None preserved)
- Mixed (4 present, 4 missing)

### §3.3 — Extend msr_loader.py

Update INSERT column list AND ON CONFLICT DO UPDATE SET to include the 8 new columns. Use `psycopg2.extras.Json` adapter for the jsonb columns.

Pattern:
```python
INSERT INTO msr_signals (
  signal_id, native_id, ..., classical_basis, falsifier, source_file, source_version, ingested_at,
  signal_type, temporal_activation, valence, entities_involved,
  supporting_rules, rpt_deep_dive, v6_ids_consumed, prior_id
) VALUES (...)
ON CONFLICT (signal_id, native_id) DO UPDATE SET
  ...,
  signal_type         = EXCLUDED.signal_type,
  temporal_activation = EXCLUDED.temporal_activation,
  valence             = EXCLUDED.valence,
  entities_involved   = EXCLUDED.entities_involved,
  supporting_rules    = EXCLUDED.supporting_rules,
  rpt_deep_dive       = EXCLUDED.rpt_deep_dive,
  v6_ids_consumed     = EXCLUDED.v6_ids_consumed,
  prior_id            = EXCLUDED.prior_id,
  ingested_at         = NOW();
```

### §3.4 — Re-ingest all 499 signals

Trigger the MSR ingest pipeline against `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`:

```bash
cd platform/python-sidecar
python -m pipeline.ingest_msr \
  --source ../../025_HOLISTIC_SYNTHESIS/MSR_v3_0.md \
  --native abhisek_mohanty \
  --upsert
```

(If the project uses a different command surface, adapt — the repo's existing ingest entry-point.)

Verify count post-ingest:
```bash
PGPASSWORD="${PGPASSWORD}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -c "SELECT COUNT(*) FROM msr_signals WHERE native_id='abhisek_mohanty';"
# MUST equal 499. HALT if not.
```

### §3.5 — Fill-rate verification (AC.7)

```sql
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE signal_type IS NOT NULL)         AS signal_type_filled,
  COUNT(*) FILTER (WHERE temporal_activation IS NOT NULL) AS temporal_filled,
  COUNT(*) FILTER (WHERE valence IS NOT NULL)             AS valence_filled,
  COUNT(*) FILTER (WHERE entities_involved IS NOT NULL)   AS entities_filled,
  COUNT(*) FILTER (WHERE supporting_rules IS NOT NULL)    AS supporting_filled,
  COUNT(*) FILTER (WHERE rpt_deep_dive IS NOT NULL)       AS rpt_filled,
  COUNT(*) FILTER (WHERE v6_ids_consumed IS NOT NULL)     AS v6_filled,
  COUNT(*) FILTER (WHERE prior_id IS NOT NULL)            AS prior_filled
FROM msr_signals
WHERE native_id='abhisek_mohanty';
```

If any HIGH column < 95% fill, HALT and report. Don't paper over with default values.

### §3.6 — Plausibility probes (AC.8 + AC.9 + AC.10)

```sql
SELECT signal_type, COUNT(*) FROM msr_signals
  WHERE native_id='abhisek_mohanty' GROUP BY signal_type ORDER BY 2 DESC;

SELECT valence, COUNT(*) FROM msr_signals
  WHERE native_id='abhisek_mohanty' GROUP BY valence ORDER BY 2 DESC;

SELECT temporal_activation, COUNT(*) FROM msr_signals
  WHERE native_id='abhisek_mohanty' GROUP BY temporal_activation ORDER BY 2 DESC;
```

If any single value > 70% of total in valence or signal_type → suggests default-fallback bug.

### §3.7 — Extend msr_sql.ts (filter capability only)

Add 4 optional input params to the msr_sql tool (in `platform/src/lib/retrieve/msr_sql.ts` and corresponding `types.ts`):

```typescript
export interface MsrSqlInput {
  // existing fields preserved
  signal_type?: string[];           // NEW
  temporal_activation?: string[];   // NEW
  valence?: string[];               // NEW
  entities_involved_any?: string[]; // NEW — uses jsonb @> with ANY
}
```

SQL WHERE additions (parameterized):
```sql
AND ($N::text[] IS NULL OR signal_type         = ANY($N::text[]))
AND ($M::text[] IS NULL OR temporal_activation = ANY($M::text[]))
AND ($P::text[] IS NULL OR valence             = ANY($P::text[]))
AND ($Q::text[] IS NULL OR entities_involved ?| $Q::text[])
```

Tests in `__tests__/msr_sql.test.ts`:
- AC.11.1: signal_type filter applied
- AC.11.2: temporal_activation filter applied
- AC.11.3: valence filter applied
- AC.11.4: backward compat (no filters → existing behavior)
- AC.11.5: entities_involved_any with jsonb @>
- AC.11.6: SQL injection safety (filter values must be parameterized)

### §3.8 — Build, test, deploy

```bash
cd platform
npm test 2>&1 | tail -10
# AC.12 — confirm baseline 958/13 (or N+/13 from new tests; total failures unchanged)

bash platform/scripts/cloud_build_submit.sh
# AC.13 — capture revision name printed in build logs
```

### §3.9 — Live-deploy verification (AC.14)

Send 3 fresh test queries through the deployed Consume tab. Capture query_plans rows:

```sql
SELECT query_id, query_class, planets, graph_seed_hints, created_at
FROM query_plans
WHERE created_at > NOW() - INTERVAL '5 minutes'
ORDER BY created_at DESC LIMIT 5;
```

Confirm 3 fresh rows. msr_sql.ts new filter params will be NULL until W6 router learns to emit
them — that's fine for this brief.

### §3.10 — Update activation matrix

Edit `00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md`:
- §2.1 mark `signal_type`, `temporal_activation`, `valence`, `entities_involved`,
  `supporting_rules`, `rpt_deep_dive`, `v6_ids_consumed`, `prior_id` as PRESENT.
- §5.3 mark this row as RESOLVED with date.
- §7 update msr_signals row to ✅.

### §3.11 — Status flip + log entry

- Flip `status: PENDING` → `status: COMPLETE` in this brief's frontmatter.
- Append per-brief entry to `00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1.

## §4 — Closing summary template (paste in chat at end)

```
KARN-W2-R1-MSR-ETL closed.
- migration 028 applied: 8 columns + 4 indexes added to msr_signals
- 499 signals re-ingested via UPSERT
- fill rate (HIGH cols): signal_type=X%, temporal_activation=Y%, valence=Z%, entities_involved=W%
- signal_type top buckets: {distribution}
- valence: benefic=A, malefic=B, mixed=C, neutral=D
- temporal_activation: natal-permanent=N, dasha-conditional=M, transit-triggered=P
- msr_sql.ts extended with 4 filter params + 6 tests
- tests: pre 958/13 → post N+6/13 (no new failures)
- Cloud Run revision: amjis-web-XXXXX-YYY
- 3 live-deploy queries verified via query_plans
- M1_M2_ACTIVATION_MATRIX.md §2/§5.3/§7 updated
- next pointer: W2-R2 (chart_facts ETL) parallel; W6-R1 will teach classifier to emit new filters
```

## §5 — Halt-and-report checklist

If any of these fire, write a 10-line halt summary to chat (NOT a verification txt — just stop):
- Pre-flight failure (any of §2.1–§2.7)
- Migration 028 fails to apply
- Re-ingest produces row count != 499
- HIGH column fill rate < 95%
- Distribution shows >70% in single bucket
- Tests baseline drift > 2 failures either direction
- Cloud Build failure
- Post-deploy live queries fail to populate query_plans

---

*End of CLAUDECODE_BRIEF_M2_A1_MSR_ETL. Predecessor: KARN-W1-R1-PHASE-ALPHA. Wave 2.*
