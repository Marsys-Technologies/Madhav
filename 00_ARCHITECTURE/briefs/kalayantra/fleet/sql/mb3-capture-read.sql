WITH p AS (
SELECT '482012f1-710e-4a25-994a-93821f5871aa'::uuid AS chart_id, '5.0'::text AS generation
)
SELECT 'binding' AS section, jsonb_build_object('chart_id', p.chart_id::text, 'generation', p.generation)::text AS row_json FROM p
UNION ALL
SELECT 'manifest', jsonb_build_object('manifest_id', m.manifest_id::text, 'status', m.status,
  'input_generation_vector', m.input_generation_vector,
  'lo', to_char(lower(m.horizon) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'),
  'hi', to_char(upper(m.horizon) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'))::text
FROM public.kala_gochara_publication m, p WHERE m.chart_id = p.chart_id AND m.generation = p.generation
UNION ALL
SELECT 'sealed', jsonb_build_object('n', count(*))::text
FROM public.ka_gochara_generation_seal s, p WHERE s.chart_id = p.chart_id AND s.generation = p.generation
UNION ALL
SELECT 'published', jsonb_build_object('n', count(*))::text
FROM public.kala_gochara_authority a, p WHERE a.chart_id = p.chart_id AND a.authoritative_generation = p.generation
UNION ALL
SELECT 'contact', jsonb_build_object('contact_id', c.contact_id::text, 'body', c.body, 'relation_kind', c.relation_kind,
  'canonical_target', o.canonical_target,
  't_in', to_char(c.t_in AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'),
  't_out', to_char(c.t_out AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'),
  't_exact', to_char(c.t_exact AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'),
  'delta_lambda', c.delta_lambda::text)::text
FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o ON o.physical_object_id = c.physical_object_id, p
WHERE c.chart_id = p.chart_id AND c.generation = p.generation
UNION ALL
SELECT 'record', jsonb_build_object('record_id', r.record_id::text, 'event_class', r.event_class,
  'affected_person', r.affected_person, 'frame_kind', r.frame_kind, 'frame_arg', r.frame_arg, 'agent', r.agent,
  'relation', r.relation, 'object_id', r.object_id::text, 'object_role', r.object_role,
  'contact_id', r.contact_id::text, 'path_id', r.path_id, 'rule_version', r.rule_version,
  'source_text', r.source_text, 'period_anchor_lord', r.period_anchor_lord,
  'period_anchor_level', r.period_anchor_level, 'admission_state', r.admission_state,
  'operator_role', r.operator_role,
  'temporal_support_intervals', COALESCE((SELECT jsonb_agg(jsonb_build_object(
      'lo', to_char(lower(i.iv) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'),
      'hi', to_char(upper(i.iv) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'),
      'bounds', CASE WHEN isempty(i.iv) THEN NULL ELSE (CASE WHEN lower_inc(i.iv) THEN '[' ELSE '(' END) || (CASE WHEN upper_inc(i.iv) THEN ']' ELSE ')' END) END,
      'empty', isempty(i.iv)) ORDER BY i.ord)
    FROM unnest(r.temporal_support_intervals) WITH ORDINALITY AS i(iv, ord)), '[]'::jsonb),
  'prerequisites', COALESCE((SELECT jsonb_agg(jsonb_build_array(q.predicate_id, q.predicate_rule_version) ORDER BY q.ordinal)
    FROM public.ka_gochara_record_prerequisite q
    WHERE q.record_id = r.record_id AND q.chart_id = r.chart_id AND q.generation = r.generation), '[]'::jsonb))::text
FROM public.ka_gochara_relationship_record r, p WHERE r.chart_id = p.chart_id AND r.generation = p.generation
UNION ALL
SELECT 'window', jsonb_build_object('event_class', w.event_class, 'path_id', w.path_id, 'rule_version', w.rule_version,
  'lo', to_char(lower(w.interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'),
  'hi', to_char(upper(w.interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"'))::text
FROM public.ka_gochara_eval_window w, p WHERE w.chart_id = p.chart_id AND w.generation = p.generation
