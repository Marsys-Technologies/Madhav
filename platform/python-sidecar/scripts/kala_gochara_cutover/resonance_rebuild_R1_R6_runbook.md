# Resonance-map production rebuild runbook — R-1..R-6 (A5.4 resonance_rebuild_R1_R6)

Sealed doctrine: FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0 T0-12, finding #9
("Production resonance map is pre-WP3c: 154 of 176 sensitive-degree targets
are negative-result checks (E3)"). Corrections: GOCHARA_PLAN_V3_AMENDMENT_v1_0
§121 (G-R resonance corrections R-1..R-6 survive as T0-12/A5.4);
GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §WP3c; WP1_CONTRACTS.md §2.

**ONLY THE NATIVE EXECUTES THIS RUNBOOK.** The production rebuild is a
NATIVE-ONLY write. No agent performs it. Every command below runs on the
governed path (production via the Cloud SQL proxy on 127.0.0.1:5433, principal
`amjis_app`), under the native's own authorization. The writer code
(`services/ka_gochara_resonance/writer.py`, R-1..R-6) is already merged; this
runbook is the data-side rebuild that makes the production map honest.

## 0. Preconditions (read-only)

- Migration `platform/migrations/1080_nirmana_l3_gochara_resonance_target_resolution_state.sql`
  is applied to production (columns `target_resolution_state`,
  `target_qualifier` + CHECK exist). Verify:

  ```sql
  SELECT column_name FROM information_schema.columns
   WHERE table_name = 'gochara_resonance_map'
     AND column_name IN ('target_resolution_state', 'target_qualifier');
  -- expect 2 rows
  ```

- The deployed sidecar image carries the R-1..R-6 writer (FORMULA_VERSION
  `ka_gochara_resonance_v2.2`; header block "WP3c corrections").

## 1. Pre-rebuild snapshot and counts

Chart: `482012f1-710e-4a25-994a-93821f5871aa` (canonical; repeat per chart as
the campaign directs — every statement below is per-chart scoped).

**The snapshot below is itself a production write and is part of the native's
action** (steward M20260930T104810-390a): it is executed by the native on the
governed path immediately before the rebuild, never by a stream. Its rollback
procedure is §4.

```sql
-- [NATIVE ACTION — production write] Rollback anchor (storage only; NOT a
-- servable surface):
CREATE TABLE IF NOT EXISTS gochara_resonance_map_pre_r1r6_backup AS
SELECT * FROM gochara_resonance_map
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';

-- [read-only] Finding-#9 baseline: negative-result sensitive targets (expect 154 of 176):
SELECT COUNT(*) FILTER (WHERE f.fact_value_text IN
         ('not_fired','not_gandanta','not_pushkara','none')) AS negative_targets,
       COUNT(*) AS sensitive_targets_total
  FROM gochara_resonance_map m
  JOIN chart_facts f ON f.fact_id = m.target_ref::uuid
 WHERE m.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
   AND m.target_type = 'sensitive_degree'
   AND f.fact_category = 'sensitive_degree_check';

-- Baseline rows by type:
SELECT target_type, COUNT(*) FROM gochara_resonance_map
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
 GROUP BY target_type ORDER BY target_type;
```

Record both outputs in the evidence file before proceeding.

## 2. Governed rebuild (native executes)

The writer is per-chart delete-then-insert (§N.3 idempotent) inside the
orchestrator's transaction, with a coverage gate that preserves the prior
partition if any of the 26 event classes is missing from
`brahma_event_ontology`. Standard path: enqueue an asset-scope rebuild of
`ka_gochara_resonance` for the chart through the governed pipeline (build_runs
row, `scope='asset'`, `action='rebuild'`, `plan.asset_ids =
["ka_gochara_resonance"]`) and let the orchestrator execute it
(`pipeline/orchestrator/main.py --run-id <uuid>` — the normal Cloud Run job
path). If the standalone lifecycle is used instead, it must follow the
`run_heavy_writer_standalone.py` pattern verbatim: committed
build_runs/build_run_assets fence BEFORE the first destructive write,
terminal records completed only on success.

The writer itself: never commits `ctx.db_conn`, never writes
asset_throughput, validates every target at build time, and returns the R-1..R-6
build record as `WriterResult.notes` JSON — capture that notes JSON into the
evidence file.

## 3. Post-rebuild verification (read-only; ALL must pass)

```sql
-- R-1: negative-result sensitive targets — MUST BE 0:
SELECT COUNT(*) FROM gochara_resonance_map m
  JOIN chart_facts f ON f.fact_id = m.target_ref::uuid
 WHERE m.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
   AND m.target_type = 'sensitive_degree'
   AND f.fact_category = 'sensitive_degree_check'
   AND (f.fact_value_text IN ('not_fired','not_gandanta','not_pushkara','none')
        OR f.fact_value_text NOT IN ('fired','gandanta','papa_kartari','shubha_kartari','pushkara'));

-- R-6: every row carries a valid stored state — MUST BE 0:
SELECT COUNT(*) FROM gochara_resonance_map
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
   AND (target_resolution_state IS NULL
        OR target_resolution_state NOT IN ('resolved','unavailable','unqualified'));

-- R-2: every arudha row keys a fact_key='sign' fact (sign-level interval) — counts must be EQUAL:
SELECT
  (SELECT COUNT(*) FROM gochara_resonance_map
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND target_type='arudha') AS arudha_rows,
  (SELECT COUNT(*) FROM gochara_resonance_map m JOIN chart_facts f ON f.fact_id = m.target_ref::uuid
    WHERE m.chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND m.target_type='arudha'
      AND f.fact_key='sign') AS arudha_keyed_to_sign_facts;

-- R-3: every yoga_constituent ref is a LIVE fired firing — MUST BE 0:
SELECT COUNT(*) FROM gochara_resonance_map m
 WHERE m.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
   AND m.target_type = 'yoga_constituent'
   AND NOT EXISTS (SELECT 1 FROM ga_yoga_firings y
                    WHERE y.chart_id = m.chart_id
                      AND y.ayanamsha_id = 'lahiri_chitrapaksha'
                      AND y.yoga_canonical_id = m.target_ref AND y.fired);

-- R-4/R-5: lord states breakdown + preserved qualifiers (record, no threshold):
SELECT target_resolution_state, COUNT(*) FROM gochara_resonance_map
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND target_type='lord'
 GROUP BY 1 ORDER BY 1;
SELECT target_ref, target_qualifier FROM gochara_resonance_map
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND target_qualifier IS NOT NULL
 ORDER BY 1;

-- After counts by type (compare with §1 baseline):
SELECT target_type, COUNT(*) FROM gochara_resonance_map
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
 GROUP BY target_type ORDER BY target_type;
```

Plus: the writer's `WriterResult.notes` JSON must show
`sensitive_degree.negative_dropped_zero_rows = 154` (this chart's finding-#9
count) and `yoga_constituent.dropped_since_prior_build` naming any yoga id
that stopped firing since the prior build (R-3 drift surfacing, F-21).

## 4. Rollback

Rollback restores **from the §1 backup table** (the native's snapshot). The
rebuild is per-chart scoped (DELETE WHERE chart_id … + INSERT inside one
orchestrator transaction), so a failed build rolls back atomically and the
prior partition is untouched; the coverage gate additionally refuses to
replace the partition on incomplete event-class coverage. If a completed
rebuild must be reversed:

```sql
BEGIN;
DELETE FROM gochara_resonance_map WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
INSERT INTO gochara_resonance_map
SELECT * FROM gochara_resonance_map_pre_r1r6_backup
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
COMMIT;
```

Restoring the backup restores the PRE-WP3c (dishonest) rows — rollback is a
pause for diagnosis, never the end state. The fix direction is always data
forward, never a weakened guard. Drop the backup table only after the rebuilt
map has soaked.

## 5. What this runbook deliberately does NOT do

- No flip, no serving-authority change, no tracker writes.
- No change to `enrichment.py`'s arudha resolution (documented gap; out of scope).
- No re-derivation of chart_facts inputs — the rebuild consumes the chart's
  existing L1 facts; stale L1 inputs surface as honest `unavailable` states,
  which are data for the LEL/T0-13 pass, not defects to patch here.
