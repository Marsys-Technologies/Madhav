-- vichara_token_expression.sql: THE single SQL definition of the deterministic chart_vichara citation token (N-143 option B).
-- No database object: no function, no view, no migration (the routine migrate role cannot CREATE in schema public; SS ruling AVOID DDL).
-- Usage: paste the expression (every line below that is not a comment) as a plain SELECT expression over chart_vichara aliased v:
--     SELECT v.chart_id, v.id, <expression> AS vichara_token FROM chart_vichara v
-- token = first 16 hex chars of sha256 over the UTF-8 canonical JSON of the natural key (ayanamsha_id, vichara_family, subject, actor,
-- target, domain, varga_id, varga, value_text, value_num, value_jsonb, constituent_facts_array), a compact positional JSON array:
-- text fields to_json (NULL -> null); value_num trim_scale(numeric)::text (NULL -> null, NaN -> "NaN"); value_jsonb its own ::text
-- (NULL -> null); constituent_facts_array to_json (NULL -> null, empty -> []). The writer-side definition is
-- platform/python-sidecar/bodha_writers/vichara_token.py; tests/l2/test_vichara_token.py evaluates THIS file on a disposable PostgreSQL
-- and requires equality with the Python token on production-shaped and hostile rows. Measured on production 2026-10-05: 24,261 of 24,261
-- chart_vichara rows equal, 0 collisions. A vichara row whose cited facts change gets a new token (the facts array is part of the key).
left(encode(sha256(convert_to(
    '[' || concat_ws(',',
      coalesce(to_json(v.ayanamsha_id)::text, 'null'),
      coalesce(to_json(v.vichara_family)::text, 'null'),
      coalesce(to_json(v.subject)::text, 'null'),
      coalesce(to_json(v.actor)::text, 'null'),
      coalesce(to_json(v.target)::text, 'null'),
      coalesce(to_json(v.domain)::text, 'null'),
      coalesce(to_json(v.varga_id)::text, 'null'),
      coalesce(to_json(v.varga)::text, 'null'),
      coalesce(to_json(v.value_text)::text, 'null'),
      CASE WHEN v.value_num IS NULL THEN 'null'
           WHEN v.value_num = 'NaN'::numeric THEN '"NaN"'
           ELSE trim_scale(v.value_num)::text END,
      coalesce(v.value_jsonb::text, 'null'),
      coalesce(to_json(v.constituent_facts_array)::text, 'null')
    ) || ']', 'UTF8')), 'hex'), 16)
