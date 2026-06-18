-- migration 320 — ga_prashna asset_registry: fix description to reference chart_facts
-- (ga_prashna_writer previously queried ga_positions table directly; now reads chart_facts)
BEGIN;
UPDATE asset_registry
SET english_description =
    'Per-prashna-chart horary judgment: Prashna-Lagna by each method, querent/quesited '
    'significators, Tajik Ithasala/Eesarpha analysis, and fructification timing. Reads '
    'graha positions from chart_facts (written by ga_positions). Returns 0 rows for natal charts.'
WHERE asset_id = 'ga_prashna';
COMMIT;
