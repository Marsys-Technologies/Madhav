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
-- the shadow of phala_pramana: holds the 16 life_event_miss rows production's shadow holds (other ids), none of the bound ones
INSERT INTO public.phala_pramana__ssv_20260728b (pramana_id, chart_id, evidence_type)
  SELECT gen_random_uuid(), '1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'life_event_miss' FROM generate_series(1, 16);
