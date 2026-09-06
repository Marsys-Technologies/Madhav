-- Migration 705: bg_vidhi_primitives -- re-point from_moon_view at a real consumer (F-D21/F-D23).
--
-- L1's W2 DECIDE findings sweep (L1_W1_ANALYSIS_BATCH_D.md, per issue #2122) found:
--   F-D21: from_moon_view dispatches `reference_point` to ganita_chart_facts_get, but no tool
--          anywhere reads that argument (2 repo hits: the primitive's own declaration and its
--          own alt_capability fallback field). ga_transit_anchors (L1's own asset) already
--          stores exactly this data (natal_house_from_moon for 9 grahas x 5 ayanamshas) with its
--          own dedicated tool, ganita_transit_anchors_get -- confirmed to take only chart_id
--          (+ optional ayanamsha_id/graha/limit/offset), no reference_point parameter.
--   F-D23: ga_transit_anchors has zero data-plane consumers campaign-wide.
--
-- Conductor ruling (issue #2122): re-pointing from_moon_view is a routine L0 data-routing
-- correction within L0's own writer (bg_vidhi_primitives.py) and its TS mirror
-- (platform/src/lib/vidhi/registry_data.ts), assigned to L0. This migration corrects the
-- corresponding live_tool/tool_args in the live vidhi_primitives seed row, which migration
-- 462 (VIDHI-PURNATA, applied 2026-08-02) seeded with the stale ganita_chart_facts_get +
-- reference_point pairing and is never re-applied (ON CONFLICT DO UPDATE only fires on a
-- fresh seed re-run, which does not happen in normal operation) -- so the live row needs its
-- own correction, matching the code fix in bg_vidhi_primitives.py + registry_data.ts (+
-- regenerated platform-mcp/src/resources/vidhi/registry_data.ts mirror) in the same PR.
--
-- Verified via a rolled-back replay against live production data before authoring this file.

DO $$
DECLARE
  updated_rows integer := 0;
BEGIN
  IF (SELECT count(*) FROM vidhi_primitives
      WHERE primitive_id='from_moon_view'
        AND live_tool='ganita_chart_facts_get'
        AND tool_args = '{"chart_id":"{chart_id}","reference_point":"moon"}'::JSONB) <> 1 THEN
    RAISE EXCEPTION 'migration 705 refuses: from_moon_view is not in the expected stale state';
  END IF;

  UPDATE vidhi_primitives
     SET live_tool = 'ganita_transit_anchors_get',
         tool_args = '{"chart_id":"{chart_id}"}'::JSONB,
         updated_at = now()
   WHERE primitive_id='from_moon_view'
     AND live_tool='ganita_chart_facts_get'
     AND tool_args = '{"chart_id":"{chart_id}","reference_point":"moon"}'::JSONB;
  GET DIAGNOSTICS updated_rows = ROW_COUNT;
  IF updated_rows <> 1 THEN
    RAISE EXCEPTION 'migration 705 expected to update exactly 1 row, updated %', updated_rows;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM vidhi_primitives WHERE primitive_id='from_moon_view'
      AND live_tool='ganita_transit_anchors_get'
      AND tool_args = '{"chart_id":"{chart_id}"}'::JSONB) THEN
    RAISE EXCEPTION 'migration 705 postflight mismatch';
  END IF;
END $$;
