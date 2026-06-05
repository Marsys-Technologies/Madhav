-- Migration 166: Create pyramid_layers table
-- Tracks per-chart build progress across layers and sublayers.
-- This table was present in the original schema (_archive/001_initial_schema.sql)
-- but was not included in the supabase migration sequence.
-- Applied directly to production on 2026-06-05 (V1.3 Stream 4 portal fix).

CREATE TABLE IF NOT EXISTS public.pyramid_layers (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id   uuid NOT NULL REFERENCES public.charts(id) ON DELETE CASCADE,
  layer      text NOT NULL,
  sublayer   text NOT NULL,
  status     text NOT NULL DEFAULT 'not_started'
             CHECK (status IN ('not_started', 'in_progress', 'complete')),
  version    text,
  updated_at timestamptz DEFAULT now(),
  UNIQUE(chart_id, layer, sublayer)
);

CREATE INDEX IF NOT EXISTS pyramid_layers_chart_idx ON public.pyramid_layers(chart_id);
