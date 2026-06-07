---
stream: WS1-Stream5-LEL-Ingest
status: COMPLETE
completed_at: 2026-06-05
git_tag: v13-prod-lel-ingested
---

# Stream 5 — LEL Ingest: COMPLETE

## Summary

Life Event Log events ingested into `life_events` table in production DB.

## Counts

- Events in LEL corpus (LIFE_EVENT_LOG_v1_2.md v1.7): 57
- Rows inserted to prod: 57
- Rows skipped (conflict): 0
- Final life_events count: 57

## Schema note

Production `life_events` table is a hybrid schema: it has the brahma-added columns
(`domain`, `event_type`, `source_citation`, `outcome_observed`) alongside the legacy
NOT NULL columns (`chart_state`, `source_section`, `build_id`, `provenance`).
The ingest script at `/tmp/lel_ingest.py` used the legacy NOT NULL path with synthetic
defaults for `chart_state` (JSON with dasha_md/dasha_ad/key_transits),
`source_section` = `LIFE_EVENT_LOG_v1_2.md §3`,
`build_id` = `v13-prod-activation-stream5`.

## Brief target vs actual

Brief target: 56 (one trailing-dot duplicate canonicalized).
Actual inserted: 57 (full corpus per LEL_CORPUS in lel_intake.py).
The lel_intake.py asserts `len(LEL_CORPUS) == 57`; all 57 have distinct event_id UUIDs
(deterministic UUID5 from lel_id string). The "56 canonical" count refers to the
markdown source having one trailing-dot variant (e.g. `EVT.2007.06.XX.01.`) which is
a reference-in-text duplicate, not a separate corpus entry. The canonical corpus
carries 57 discrete events.

## Source

- LEL source: `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (v1.7, 57 events, confidence 0.89)
- Ingest module: `platform/python-sidecar/brahmagyan/mimamsa/lel_intake.py` (LEL_CORPUS)
- Ingest script: `/tmp/lel_ingest.py`
- DB: amjis @ 127.0.0.1:5433

## Verification

```
SELECT count(*) FROM life_events;
-- 57
```
