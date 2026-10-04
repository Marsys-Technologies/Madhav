"""The 15 L1 data-plane functions as read LIVE from production as suvarna_reader on 2026-10-02 (PostgreSQL 15.18, database amjis):
signature -> (md5(pg_get_functiondef), length, owner, SECURITY DEFINER, proconfig, proacl). The replayed migration 1035 must equal it
(test_replay_is_production_faithful); the plan's 'unchanged' claims for the other 14 are against these md5."""
LIVE_L1_MANIFEST = {
    'authorize_l1_chart_facts_delete(uuid,text[],text[],text[])': ('b81c9f63b322d567eb21054ac281fe29', 1939, 'data_plane_l1_owner', True, '{"search_path=pg_catalog, public, pg_temp"}', '{data_plane_l1_owner=X/data_plane_l1_owner,data_plane_builder=X/data_plane_l1_owner}'),
    'capture_l1_data_plane_dasha_partition(uuid,text,text,integer)': ('eee8d9d4f5fbbbbbd03a9abda7c62385', 5357, 'data_plane_l1_owner', True, '{"search_path=pg_catalog, public, pg_temp"}', '{data_plane_l1_owner=X/data_plane_l1_owner,data_plane_builder=X/data_plane_l1_owner}'),
    'complete_l1_data_plane_partition(uuid,text,text,text,integer)': ('dcab40cf524c39efca628517c14fd9e8', 8647, 'data_plane_l1_owner', True, '{"search_path=pg_catalog, public, pg_temp"}', '{data_plane_l1_owner=X/data_plane_l1_owner,data_plane_builder=X/data_plane_l1_owner}'),
    'l1_data_plane_capture_row()': ('1e079261aa42eb97a1885a48035e7520', 19780, 'data_plane_l1_owner', True, '{"search_path=pg_catalog, public, pg_temp"}', '{data_plane_l1_owner=X/data_plane_l1_owner}'),
    'l1_data_plane_dasha_semantic_payload(chart_dashas)': ('0d4b33b09315cb3cffda146c3bed9de1', 933, 'data_plane_l1_owner', False, '', '{data_plane_l1_owner=X/data_plane_l1_owner}'),
    'l1_data_plane_fact_unit(text,text,jsonb)': ('cbe5275c6f03369835dcb9914f4e4263', 1269, 'data_plane_l1_owner', False, '', '{data_plane_l1_owner=X/data_plane_l1_owner}'),
    'l1_data_plane_guard_active_mutation()': ('33b20202ec3571bc73a0e59b83591cef', 4767, 'data_plane_l1_owner', True, '{"search_path=pg_catalog, public, pg_temp"}', '{data_plane_l1_owner=X/data_plane_l1_owner}'),
    'l1_data_plane_guard_generation_change()': ('5b83daa863c1c81ef8e1401556ffdc31', 2305, 'data_plane_l1_owner', False, '', '{data_plane_l1_owner=X/data_plane_l1_owner}'),
    'l1_data_plane_install_active_guards(text,text[])': ('e9a61c49e56b9adda54ad2df4aafb996', 975, 'data_plane_l1_owner', False, '{"search_path=pg_catalog, public, pg_temp"}', '{data_plane_l1_owner=X/data_plane_l1_owner}'),
    'l1_data_plane_jsonb_has_nonfinite(jsonb)': ('876b4a5ccc248bb34d61dc698ba87b95', 822, 'data_plane_l1_owner', False, '', '{data_plane_l1_owner=X/data_plane_l1_owner}'),
    'l1_data_plane_material_fact_specs(text)': ('eb6b349e7dab96a2affc453d36443c85', 5755, 'data_plane_l1_owner', False, '', '{data_plane_l1_owner=X/data_plane_l1_owner}'),
    'l1_data_plane_reject_immutable_change()': ('f077fd723a03353081fcfa2c5b10e8e7', 221, 'data_plane_l1_owner', False, '', '{data_plane_l1_owner=X/data_plane_l1_owner}'),
    'open_l1_data_plane_generation(uuid,text,text,text,integer,text,text,text,text,text,text)': ('ea6b50d97d2d88f8f1d20701abe37b14', 7276, 'data_plane_l1_owner', True, '{"search_path=pg_catalog, public, pg_temp"}', '{data_plane_l1_owner=X/data_plane_l1_owner,data_plane_builder=X/data_plane_l1_owner}'),
    'rollback_l1_data_plane_generation(uuid,text,text)': ('ed47c9ed9dbc723579d583b53702e04b', 1228, 'data_plane_l1_owner', True, '{"search_path=pg_catalog, public, pg_temp"}', '{data_plane_l1_owner=X/data_plane_l1_owner,data_plane_migrator=X/data_plane_l1_owner}'),
    'select_l1_data_plane_generation(uuid,text,text)': ('94c08ee5d0b695ef9a2715b060270f3f', 3653, 'data_plane_l1_owner', True, '{"search_path=pg_catalog, public, pg_temp"}', '{data_plane_l1_owner=X/data_plane_l1_owner,data_plane_builder=X/data_plane_l1_owner,data_plane_verifier=X/data_plane_l1_owner,data_plane_migrator=X/data_plane_l1_owner,amjis_app=X/data_plane_l1_owner}'),
}
LIVE_ATTESTATION_COUNTS = {'trigger': 23, 'function': 15}
LIVE_CAPTURE_TRIGGER_DIGEST = 'd0064f5ed31f7db91cb239967f783af3a885f21b39aa7c833877989a713768b0'
