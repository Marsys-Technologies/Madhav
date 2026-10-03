-- SYNTHETIC rows. The 8 target rows carry production's ids, chart, anchor ids and NON-PRIVATE column values (read from the reader: ids, enums, timestamps
-- are not private) so their non-private fingerprint equals the pinned production fingerprint; every PRIVATE column (falsifier_text, the jsonb columns,
-- source_citation) holds a synthetic marker 'PRIVMARK-...' that the tests assert never appears in any report, log, outcome or evidence file.
-- Run as the cluster superuser, AFTER 02_tables.sql.
INSERT INTO public.phala_anchors (anchor_id, chart_id) VALUES
  ('e9010071-4f59-5a95-b760-dde3e157a99d', '1c826d5a-41cb-4450-b4dc-59d440e5f75a'),
  ('c3e492e7-0b31-5d34-b8f3-e18924598689', '1c826d5a-41cb-4450-b4dc-59d440e5f75a'),
  ('fefc4efc-bccd-5060-b660-76f0d87eab47', '1c826d5a-41cb-4450-b4dc-59d440e5f75a'),
  ('15390d90-01bc-5d3b-9450-57006b57df71', '1c826d5a-41cb-4450-b4dc-59d440e5f75a'),
  ('fdd12c57-14fa-5d70-accf-b3962c865b7f', '1c826d5a-41cb-4450-b4dc-59d440e5f75a'),
  ('11a2180c-e96f-5528-a466-3353ef666447', '1c826d5a-41cb-4450-b4dc-59d440e5f75a'),
  ('8f7c608b-9f78-5531-8d2f-69a1a651a0ea', '1c826d5a-41cb-4450-b4dc-59d440e5f75a'),
  ('df2c08b7-5795-58be-9d7f-324934541754', '1c826d5a-41cb-4450-b4dc-59d440e5f75a');
INSERT INTO public.phala_pramana (pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status,
                                  lel_entry_id, lel_entry_jsonb, derivation_ledger_jsonb, source_citation, computed_at) VALUES
  ('649c5828-ba9c-4ca8-9a7f-6ace81fad2e3', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'e9010071-4f59-5a95-b760-dde3e157a99d', 'life_event_miss', 'indirect', 'PRIVMARK-falsifier-1', '{"raw": "PRIVMARK-raw-1"}', 'past_window', NULL, NULL, '{"note": "PRIVMARK-ledger-1"}', 'PRIVMARK-cite-1', '2026-08-12 17:11:25.131301+00'),
  ('767b84b4-4090-4383-a9a9-ada59a509b1d', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'c3e492e7-0b31-5d34-b8f3-e18924598689', 'life_event_miss', 'indirect', 'PRIVMARK-falsifier-2', '{"raw": "PRIVMARK-raw-2"}', 'past_window', NULL, NULL, '{"note": "PRIVMARK-ledger-2"}', 'PRIVMARK-cite-2', '2026-08-12 17:11:25.131301+00'),
  ('a3c855bb-9698-4c43-bb6b-c85ad1ec0a84', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'fefc4efc-bccd-5060-b660-76f0d87eab47', 'life_event_miss', 'indirect', 'PRIVMARK-falsifier-3', '{"raw": "PRIVMARK-raw-3"}', 'past_window', NULL, NULL, '{"note": "PRIVMARK-ledger-3"}', 'PRIVMARK-cite-3', '2026-08-12 17:11:25.131301+00'),
  ('adcfd0d2-e748-4741-9df5-619ad1e8d271', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', '15390d90-01bc-5d3b-9450-57006b57df71', 'life_event_miss', 'indirect', 'PRIVMARK-falsifier-4', '{"raw": "PRIVMARK-raw-4"}', 'past_window', NULL, NULL, '{"note": "PRIVMARK-ledger-4"}', 'PRIVMARK-cite-4', '2026-08-12 17:11:25.131301+00'),
  ('c4fd0d7c-7502-4b63-bb61-8b693c38375b', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'fdd12c57-14fa-5d70-accf-b3962c865b7f', 'life_event_miss', 'indirect', 'PRIVMARK-falsifier-5', '{"raw": "PRIVMARK-raw-5"}', 'past_window', NULL, NULL, '{"note": "PRIVMARK-ledger-5"}', 'PRIVMARK-cite-5', '2026-08-12 17:11:25.131301+00'),
  ('ccdf5abd-6339-48dc-adac-39d8877f2629', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', '11a2180c-e96f-5528-a466-3353ef666447', 'life_event_miss', 'indirect', 'PRIVMARK-falsifier-6', '{"raw": "PRIVMARK-raw-6"}', 'past_window', NULL, NULL, '{"note": "PRIVMARK-ledger-6"}', 'PRIVMARK-cite-6', '2026-08-12 17:11:25.131301+00'),
  ('db6cc6a0-91a5-4f2e-89ea-33c4fd23fc5c', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', '8f7c608b-9f78-5531-8d2f-69a1a651a0ea', 'life_event_miss', 'indirect', 'PRIVMARK-falsifier-7', '{"raw": "PRIVMARK-raw-7"}', 'past_window', NULL, NULL, '{"note": "PRIVMARK-ledger-7"}', 'PRIVMARK-cite-7', '2026-08-12 17:11:25.131301+00'),
  ('f44dea24-ada4-405d-bba7-fe094ce8e1e6', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'df2c08b7-5795-58be-9d7f-324934541754', 'life_event_miss', 'indirect', 'PRIVMARK-falsifier-8', '{"raw": "PRIVMARK-raw-8"}', 'past_window', NULL, NULL, '{"note": "PRIVMARK-ledger-8"}', 'PRIVMARK-cite-8', '2026-08-12 17:11:25.131301+00');

-- the same chart's other rows (production: 3 open + 45 pending, all pending_observation) and the other chart's 4 open rows
INSERT INTO public.phala_anchors (anchor_id, chart_id) SELECT gen_random_uuid(), '1c826d5a-41cb-4450-b4dc-59d440e5f75a' FROM generate_series(1, 48);
INSERT INTO public.phala_anchors (anchor_id, chart_id) SELECT gen_random_uuid(), '482012f1-710e-4a25-994a-93821f5871aa' FROM generate_series(1, 4);
INSERT INTO public.phala_pramana (chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status, derivation_ledger_jsonb, source_citation)
  SELECT a.chart_id, a.anchor_id, 'pending_observation', 'indirect', 'PRIVMARK-falsifier-x', '{"raw": "PRIVMARK-raw-x"}',
         CASE WHEN a.rn <= 3 THEN 'open' ELSE 'pending' END, '{"note": "PRIVMARK-ledger-x"}', 'PRIVMARK-cite-x'
    FROM (SELECT anchor_id, chart_id, row_number() OVER (ORDER BY anchor_id) rn FROM public.phala_anchors
           WHERE chart_id = '1c826d5a-41cb-4450-b4dc-59d440e5f75a' AND anchor_id NOT IN (SELECT anchor_id FROM public.phala_pramana)) a;
INSERT INTO public.phala_pramana (chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status, derivation_ledger_jsonb, source_citation)
  SELECT chart_id, anchor_id, 'pending_observation', 'indirect', 'PRIVMARK-falsifier-y', '{"raw": "PRIVMARK-raw-y"}', 'open', '{"note": "PRIVMARK-ledger-y"}', 'PRIVMARK-cite-y'
    FROM public.phala_anchors WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';

-- the objects the dependents scan reads: rows that do NOT refer to a bound id
INSERT INTO public.build_runs (chart_id, state) VALUES ('1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'completed'), ('482012f1-710e-4a25-994a-93821f5871aa', 'failed'),
  ('482012f1-710e-4a25-994a-93821f5871aa', 'stopped');
INSERT INTO public.mimamsa_predictions (source_pramana_id, body) VALUES ('11111111-1111-4111-8111-111111111111', '{"k": "v"}'), (NULL, '{"k": "w"}');
INSERT INTO public.mimamsa_predictions__ssv_20260728b (source_pramana_id, body) VALUES ('22222222-2222-4222-8222-222222222222', '{"k": "v"}');
INSERT INTO public.mimamsa_anchor_adjustment (derived_from_pramana_ids) VALUES ('["33333333-3333-4333-8333-333333333333"]'), (NULL), ('[]');
INSERT INTO public.mimamsa_convergence_adjustment (derived_from_pramana_ids) VALUES ('["44444444-4444-4444-8444-444444444444"]'), ('{}');
INSERT INTO public.mimamsa_fact_adjustment (derived_from_pramana_ids) VALUES ('["55555555-5555-4555-8555-555555555555", "66666666-6666-4666-8666-666666666666"]');
INSERT INTO public.mimamsa_signal_adjustment (derived_from_pramana_ids) VALUES ('["77777777-7777-4777-8777-777777777777"]');
-- the shadow of phala_pramana (the 2026-07-28 snapshot): 141 rows as in production: the 16 life_event_miss rows of the bound chart (production ids, anchor ids and NON-private
-- values, so their fingerprint equals the pinned production one; every private column holds a PRIVMARK), 3 open + 119 pending rows of the same chart (label proxy) and
-- 3 open rows of the other chart. None of the snapshot's anchor ids exists in phala_anchors (as in production).
INSERT INTO public.phala_pramana__ssv_20260728b (pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status,
                                                 lel_entry_id, lel_entry_jsonb, derivation_ledger_jsonb, source_citation, computed_at)
  SELECT v.pid::uuid, '1c826d5a-41cb-4450-b4dc-59d440e5f75a', v.aid::uuid, 'life_event_miss', 'indirect', 'PRIVMARK-sfalsifier-' || v.pid, ('{"raw": "PRIVMARK-sraw-' || v.pid || '"}')::jsonb,
         'past_window', NULL, NULL, ('{"note": "PRIVMARK-sledger-' || v.pid || '"}')::jsonb, 'PRIVMARK-scite', '2026-07-28 05:01:29.614848+00'
    FROM (VALUES
      ('05a53e0a-54c9-4053-9ca2-b5a272d77019', '8ee9520a-8a5c-40f1-9e47-28c127f87945'), ('12cf1a40-a44e-4cfa-8676-17de3f400a43', '160097d6-46df-46e8-a73a-9021fa14ed0d'),
      ('1fd500d1-e470-4059-95d7-15b7d318b96b', '80b3bb2c-d9d6-43a9-85ee-348305ce5ca1'), ('4649aa1b-20f4-4a7f-90a6-fbf43fb38574', 'bbd7247a-3adb-414e-af84-142c0f7fb673'),
      ('60b833f7-0d0a-43ed-b904-a25450c3f114', 'e245ec8f-ac28-45ea-b9d1-0a0f24c03f08'), ('7af4a789-5f28-4b36-82a7-644a182411f7', '91a15c4e-17e7-4509-a7ea-de1eadd40c25'),
      ('8b147ef7-3d7d-4657-9cf1-0dd652144ee9', '0b71277e-77f0-4492-a845-345b78d70d9f'), ('a2138a26-3f37-480e-bf71-da03931b147b', '443a087b-90d1-4dd5-ab0d-f64517619ad6'),
      ('ac243a04-6c4e-4c80-92b9-5ca8999bd644', '433f5129-8ad5-404a-aabc-d2894cb54c35'), ('c89c4d65-c928-4011-928c-fd2288049bc0', '49f67d39-d190-41ac-b7be-51dc9176a1ee'),
      ('cdd0ef46-6290-4cae-9241-efd89bb109a8', '81c36da1-9697-4f69-bf99-1447dbca59fd'), ('d6a2f982-a44b-4b6c-92e0-bed3fe44e884', 'dc62b08d-5f30-4664-83fe-9c13885cb323'),
      ('e05205a8-44ae-4329-b363-f28dd1c55fb3', '791e3ea8-4b89-4842-96f7-dec60a37555d'), ('e16bb71a-7b1b-4021-a4ac-8f286d6411b6', 'e9a8704f-4ec9-4a49-9d3c-c101137217f4'),
      ('ef1d58d6-03a3-47bb-a2aa-e32c40d2c642', '9af1676a-f485-48ac-a4fd-9c377e5b907a'), ('f9c0087b-529b-4673-a70f-dfc69dba2530', '3ac2f040-b44b-48e9-987c-dc7c3c23a918')
    ) AS v(pid, aid);
INSERT INTO public.phala_pramana__ssv_20260728b (pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status,
                                                 derivation_ledger_jsonb, source_citation, computed_at)
  SELECT gen_random_uuid(), '1c826d5a-41cb-4450-b4dc-59d440e5f75a', gen_random_uuid(), 'pending_observation', 'proxy', 'PRIVMARK-sfalsifier-x', '{"raw": "PRIVMARK-sraw-x"}',
         CASE WHEN g <= 3 THEN 'open' ELSE 'pending' END, '{"note": "PRIVMARK-sledger-x"}', 'PRIVMARK-scite', '2026-07-28 05:01:29.614848+00' FROM generate_series(1, 122) g;
INSERT INTO public.phala_pramana__ssv_20260728b (pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label, falsifier_text, observable_criteria_jsonb, window_status,
                                                 derivation_ledger_jsonb, source_citation, computed_at)
  SELECT gen_random_uuid(), '482012f1-710e-4a25-994a-93821f5871aa', gen_random_uuid(), 'pending_observation', 'proxy', 'PRIVMARK-sfalsifier-y', '{"raw": "PRIVMARK-sraw-y"}',
         'open', '{"note": "PRIVMARK-sledger-y"}', 'PRIVMARK-scite', '2026-07-28 05:01:29.614848+00' FROM generate_series(1, 3);

-- phala_phaladesa (live, 26 rows as in production: 13 per chart) and its snapshot (14 rows: 7 per chart). The ONE target row of the snapshot carries production's id, top anchor,
-- domain, enums and timestamp (so its non-private fingerprint equals the pinned production one); every private column (jsonb, source_citation) holds a PRIVMARK. The canonical chart
-- legitimately has a life_event_miss row in BOTH tables (its own events): it must survive.
INSERT INTO public.phala_phaladesa__ssv_20260728b (phaladesa_id, chart_id, domain, anchor_count, clean_anchor_count, staged_revision_count, anomaly_flag_count, top_anchor_id,
    magnitude, malleability, spillover_domains_jsonb, mitigation_available, muhurta_available, pramana_window_status, evidence_type, precedent_refs_jsonb, contradiction_summary_jsonb,
    derivation_summary_jsonb, narration_status, narration_model, narration_jsonb, derivation_ledger_jsonb, source_citation, computed_at)
  VALUES ('908e3c82-bb53-4457-8642-bf0d5e71460c', '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'relationship', 1, 1, 0, 0, 'bbd7247a-3adb-414e-af84-142c0f7fb673',
          'moderate', 'influenceable', '["relationship", "PRIVMARK-spill"]', false, false, 'past_window', 'life_event_miss', '[]', '{}', '{"note": "PRIVMARK-dsum"}', 'ready', NULL,
          '{"text": "PRIVMARK-narration", "model": "x"}', '{"note": "PRIVMARK-pledger"}', 'PRIVMARK-pcite', '2026-07-28 05:01:51.208762+00');
INSERT INTO public.phala_phaladesa__ssv_20260728b (phaladesa_id, chart_id, domain, anchor_count, clean_anchor_count, staged_revision_count, anomaly_flag_count, top_anchor_id,
    mitigation_available, muhurta_available, pramana_window_status, evidence_type, derivation_summary_jsonb, narration_status, narration_jsonb, derivation_ledger_jsonb, source_citation, computed_at)
  SELECT gen_random_uuid(), c.chart_id, 'career', 1, 1, 0, 0, gen_random_uuid(), false, false, w.ws, w.et, '{"note": "PRIVMARK-dsum-x"}', 'ready', '{"text": "PRIVMARK-narration-x"}',
         '{"note": "PRIVMARK-pledger-x"}', 'PRIVMARK-pcite-x', '2026-07-28 05:01:51.208762+00'
    FROM (VALUES ('1c826d5a-41cb-4450-b4dc-59d440e5f75a'::uuid), ('482012f1-710e-4a25-994a-93821f5871aa'::uuid)) AS c(chart_id),
         (VALUES ('open', 'pending_observation'), ('pending', 'pending_observation'), ('pending', 'pending_observation'), ('pending', 'pending_observation'),
                 ('pending', 'pending_observation'), (NULL, NULL)) AS w(ws, et);
INSERT INTO public.phala_phaladesa__ssv_20260728b (phaladesa_id, chart_id, domain, derivation_summary_jsonb, narration_status, evidence_type, pramana_window_status, top_anchor_id, computed_at)
  VALUES (gen_random_uuid(), '482012f1-710e-4a25-994a-93821f5871aa', 'career', '{}', 'ready', 'life_event_miss', 'past_window', gen_random_uuid(), '2026-07-28 05:01:51.208762+00');
INSERT INTO public.phala_phaladesa (phaladesa_id, chart_id, domain, anchor_count, clean_anchor_count, staged_revision_count, anomaly_flag_count, top_anchor_id, mitigation_available,
    muhurta_available, pramana_window_status, evidence_type, derivation_summary_jsonb, narration_status, narration_jsonb, derivation_ledger_jsonb, source_citation)
  SELECT gen_random_uuid(), c.chart_id, 'career', 1, 1, 0, 0, gen_random_uuid(), false, false, w.ws, w.et, '{"note": "PRIVMARK-dsum-live"}', 'ready', '{"text": "PRIVMARK-narration-live"}',
         '{"note": "PRIVMARK-pledger-live"}', 'PRIVMARK-pcite-live'
    FROM (VALUES ('1c826d5a-41cb-4450-b4dc-59d440e5f75a'::uuid), ('482012f1-710e-4a25-994a-93821f5871aa'::uuid)) AS c(chart_id),
         (VALUES ('open', 'pending_observation'), ('pending', 'pending_observation'), ('pending', 'pending_observation'), ('pending', 'pending_observation'),
                 ('pending', 'pending_observation'), ('pending', 'pending_observation'), (NULL, NULL), (NULL, NULL), (NULL, NULL), (NULL, NULL), (NULL, NULL), (NULL, NULL)) AS w(ws, et);
INSERT INTO public.phala_phaladesa (phaladesa_id, chart_id, domain, anchor_count, clean_anchor_count, staged_revision_count, anomaly_flag_count, mitigation_available,
    muhurta_available, derivation_summary_jsonb, narration_status, derivation_ledger_jsonb, source_citation)
  VALUES (gen_random_uuid(), '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'career', 1, 1, 0, 0, false, false, '{}', 'ready', '{}', 'PRIVMARK');
INSERT INTO public.phala_phaladesa (phaladesa_id, chart_id, domain, anchor_count, clean_anchor_count, staged_revision_count, anomaly_flag_count, top_anchor_id, mitigation_available,
    muhurta_available, pramana_window_status, evidence_type, derivation_summary_jsonb, narration_status, derivation_ledger_jsonb, source_citation)
  VALUES (gen_random_uuid(), '482012f1-710e-4a25-994a-93821f5871aa', 'career', 1, 1, 0, 0, gen_random_uuid(), false, false, 'past_window', 'life_event_miss', '{}', 'ready', '{}', 'PRIVMARK');
