-- V1.3 Production Activation: pyramid_layers
-- Restores the portal-critical table from archived 001_initial_schema.sql.
-- Root cause of every portal 500: clients/[id]/page.tsx queries this table on every load.
-- Idempotent: CREATE TABLE IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS public.pyramid_layers (
  id         uuid primary key default gen_random_uuid(),
  chart_id   uuid not null references public.charts(id) on delete cascade,
  layer      text not null,
  sublayer   text not null,
  status     text not null default 'not_started'
             check (status in ('not_started', 'in_progress', 'complete')),
  version    text,
  updated_at timestamptz default now(),
  unique(chart_id, layer, sublayer)
);

CREATE INDEX IF NOT EXISTS idx_pyramid_layers_chart_id ON public.pyramid_layers(chart_id);
CREATE INDEX IF NOT EXISTS idx_pyramid_layers_layer ON public.pyramid_layers(layer);
