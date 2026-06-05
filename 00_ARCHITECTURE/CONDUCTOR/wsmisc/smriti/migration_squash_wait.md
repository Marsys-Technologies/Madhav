---
session: migration-squash
type: WAIT_STATE
timestamp: 2026-06-05T07:12:00+05:30
status: BLOCKED
blocking_on: ws2-tag:ws2-depth-build-complete
---

# Migration Squash — Wait State

## Status: BLOCKED on ws2-depth-build-complete tag

WS-2 (feature/ws2-depth-build) is actively running:
- Latest WS-2 commits: brahmagyan.almanac, brahmagyan.ontology, brahmagyan.reference
- WS-2 is in L0 layer build (early phase)
- Tag `ws2-depth-build-complete` not yet present

## Pre-squash preparation completed

Pre-squash schema snapshot taken:
- File: platform/supabase/migrations/_pre_squash_schema_snapshot.sql
- Lines: 6178
- Tables: 81 (current production state before WS-2 schema additions)
- This is the pre-WS-2 baseline; will be superseded by post-WS-2 final snapshot

## Current migration inventory

29 numbered migrations in platform/supabase/migrations/ (057-082 + 157):
- Range: 057_school_signal_coverage.sql → 082_perf_system_materialized_views.sql
- Plus: 157_charts_natural_key_uniq.sql

WS-2 is expected to add migrations for: brahmagyan.* L0 tables (ephemeris, reference, classical_texts, ontology, rule_base, concordance, almanac, remedy_corpus), ganita.* L1 tables, and potentially more.

## Migration squash plan (deferred until tag appears)

When `ws2-depth-build-complete` appears:
1. Take final pg_dump --schema-only → reference schema (supersedes pre_squash snapshot)
2. Author platform/supabase/migrations/0001_brahma_baseline.sql
3. Spin empty Postgres via Docker, apply 0001, pg_dump, diff → zero structural diffs
4. git mv all 057-*.sql + higher → platform/supabase/migrations/_archive/
5. Update migration tracker with squash sentinel

## Polling cadence

Every 15 minutes via:
```bash
git -C /Users/Dev/Vibe-Coding/Apps/MadhavMisc fetch origin --tags 2>/dev/null
git -C /Users/Dev/Vibe-Coding/Apps/MadhavMisc tag -l 'ws2-depth-build-complete' | grep -q . && echo "RELEASED" || echo "WAITING"
```

---
