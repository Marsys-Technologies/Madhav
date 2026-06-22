-- 0000_seed_legacy_applied.sql
-- Seeds _migrations_applied for ALL migration files that were applied to the production
-- database before migrate.ts tracking was in place (tracking began at 118_build_events.sql,
-- 2026-06-04). migrate.ts checks filename presence only; sha256 here is the actual file
-- hash for audit trail completeness.
--
-- Categories seeded here:
--   001_baseline.sql             — profiles/RLS baseline, applied via psql pre-tracking
--   081_l0fr_schema.sql          — L0 schema, applied via psql
--   166–230 (supabase/)          — squashed into 0001_brahma_baseline or applied pre-tracking
--   236–241 (supabase/)          — applied pre-tracking (before 118_ tracking started)
--   250_l3_count_sql_param_fix   — applied pre-tracking
--   292–293 (migrations/)        — ga_nakshatra assets, applied pre-tracking
--   brahma_*                     — feature schema files applied via psql pre-tracking
--   ws2_l0_ephemeris/remedy      — L0 reference data, applied pre-tracking
--   174_ganita_graha_sthana      — ganita extension, applied pre-tracking
--   195_ganita_naming            — naming reconciliation, applied pre-tracking
--
-- 0001_brahma_baseline.sql: squash of migrations 057-157, applied 2026-06-05 via psql.
-- Contains psql meta-commands (\restrict, \unrestrict, CREATE SCHEMA without IF NOT EXISTS)
-- that are invalid SQL through pg library — must remain permanently skipped.

INSERT INTO _migrations_applied (filename, sha256) VALUES
  ('0001_brahma_baseline.sql',                     'ec6f564cb7cc43d493edf46124ca2c8d6506b6a2291ed1e013d43c9f7b38adef'),
  ('001_baseline.sql',                              '941b74fd4830f12bce935ad9acc3f127518ea788422c0d59448c3d15515d72c6'),
  ('081_l0fr_schema.sql',                           '921f91aff6b5688a83c286c242188ec97968a0dac792123443973c232f1e3351'),
  ('166_pyramid_layers.sql',                        '59ff61cc4a16c2ae1e58fafffc6cff322d0a89a5a322d4fabeb86d97422af7c5'),
  ('167_asset_registry.sql',                        '362d0ce8d0e49c3caa710ec0ec8fc40725b094ef087c55e753025a3a11733323'),
  ('168_asset_coefficients.sql',                    '93ecc952a2d54511127ca4b0de9f874339e20a013fc5ea34951b889d17499eb3'),
  ('169_asset_throughput.sql',                      '96fde23f22b2e8a118cc4e43286b5474350e93c9e277b975cd3509a7c5c683ec'),
  ('170_layer_approvals.sql',                       '69b515e2bc54e07a727659f95df994421628f00d08acaac9c91d4df18b0caa55'),
  ('171_build_runs.sql',                            'dad12fcbd9701c4c1431ba829308bd1c1c82cf1d8f43625e2f4d8e2741fec6a2'),
  ('172_asset_throughput_volume.sql',               '447764bd5f4e3e4911ece0b28f78260ea5979c4031cb61456f33381fa415e5c8'),
  ('173_drop_legacy_builds.sql',                    '0f1a0a7e499f494c0eb50ae4e91a1da914e27b779b7545d278cb669db85e0c9a'),
  ('174_brahmagyan_naming_reconciliation.sql',      '173152db2607efa51ffd0ffd7ac626b71a3683ec8cdddf1fe2f1d91969a3cc2c'),
  ('174_ganita_graha_sthana.sql',                   '13dd7af88b2aaeab95c6628ce7384374d562be3872c665d591fb7eae073ccd60'),
  ('175_classical_attributions_stub.sql',           '91399c7947ac802ecb18a16c60edc4cac785f74d1b7172023114a7290508202d'),
  ('176_l0_phase_alpha_new_content_tables.sql',     '1724e4c6b34a9b98c4799073997889d864f243364b38556e7f4ec9702025d0f5'),
  ('177_l0_phase_alpha_existing_table_schema.sql',  '8dd0eb57f4a8b36698c7eb50825326d703a99ec03874a1aa2656b5439da7b7c4'),
  ('178_l0_phase_alpha_reference_tables.sql',       '34a65d5f39a8401941aebd8183f3ff05cd1583a6d846103aa690ae23f1dce342'),
  ('179_l0_phase_alpha_asset_registry.sql',         '80a9418aa2fb95c6bc7b580249d1cb4acde5c51aeab44876b07fd47e95b9f794'),
  ('180_bg_reference_count_sql_fix.sql',            'b13c2c8d51b8dd093eefeb0db22963720c2aeb12e23cf280ee03b6aa44bc3025'),
  ('181_asset_registry_clear_tables.sql',           '263d5b6a3c40885da6b183194f5f212a199a5587681d6193f6c818b398252faf'),
  ('182_bg_ephemeris_target_floor_825084.sql',      'fbdf90631ba8b0e364585d796a7b52e65ea49f490891f163430052c51c512414'),
  ('183_bg_texts_and_text_dependent_floors.sql',    'dda01f9078bb4aaac2f641bf13f38b6de46bf536963cdea4a8d9471435bd04b6'),
  ('184_asset_throughput_global_idx.sql',           '983414491f11c7a175678f49a1cfc67d425fa6c4bd2ea317634e75344b9f7b5c'),
  ('185_bg_ontology_floor.sql',                     '9ee685425b95ce67542dcbd463b9737a33141d05e47e85df443ad6cffac37943'),
  ('186_bg_reference_floor.sql',                    'd799cb4473bc3aa590b5a08d809e7be69545d05c5e4a34ed295cdd0ae680dce1'),
  ('187_bg_yogas_floor.sql',                        '5810e15ae184742752bbdb55cf2ae45e64b87761901b2f2be5729171b3871e1a'),
  ('188_bg_dasha_systems_floor.sql',                '511dc1db106434f76df68c0847d48530c8e165874f6550e226eb210250a1f787'),
  ('189_bg_doshas_floor.sql',                       '4ed8dde9837def243fcc2d9c5725afb3835e380d8c55e0537f9a139ff5458e54'),
  ('190_bg_text_index_floor.sql',                   'bbe15ce3c405bcc044619ce0a64f661cda05664842e00dabbcd04741f8dde530'),
  ('191_bg_rules_floor.sql',                        '25a33790df682c5df4be7243a304217e2d93cf5bd29d1cbcc805946dc9dcf99b'),
  ('192_bg_remedies_floor.sql',                     '02c6ada0f303d80ee17751f43bc600dc7b0702a21c5096438ac18628042b469b'),
  ('193_bg_concordance_floor.sql',                  '840152c835cef615940b0838ad7bb177a3225447238d77e00b3ef6d4e81e2235'),
  ('194_bg_compendium_index_floor.sql',             '30fe2bcf29c4c292837eb8cdaab6603d144a989bfce1faa534a72dec7bfd83fd'),
  ('195_bg_texts_nadi_expansion_floor.sql',         'ce8baf0a85b26dac2fa4e369967abd59b1867497b92b307d7d2999cd397dfee6'),
  ('195_ganita_naming_reconciliation.sql',          '358b4558b45652fe5496de6396f34fb3491c4b027c8fc01f18feda1b159f1d78'),
  ('196_bg_text_index_nadi.sql',                    '59f61047e2faa08816d9cc85f6754b79a75e0afd94f69fc602d4331fa426272e'),
  ('197_bg_concordance_nadi.sql',                   '449b3bbdec1d99b09302e9c6ee597eb822d10f2305f6da8549fa7e6ba614f180'),
  ('198_bg_rules_nadi.sql',                         '46519fc459353e2084e424f4dd5f43b27fdd4e823e00ca228863d13e6b0854a4'),
  ('199_bg_remedies_nadi.sql',                      'c2c9bebe95b48e82959613a0d7824dde82f29a1b7bb6ff736d5afa9dae3e6f49'),
  ('200_bg_compendium_index_nadi.sql',              '231a2d9b2a2676a6324ffd6f6cd083ce0c2e52b1679da29ac5a7a3da608fc612'),
  ('201_bg_yogas_nadi.sql',                         '519b0af658583108a2cf42b9751a9fd97b5176a9af3e7b4d04324862525f0aba'),
  ('206_ga3_supporting_tables.sql',                 '6598dda9a914ec2b1ff52b435afcfba7c39e0df0ba4f45e2b2b2ee776391df87'),
  ('207_ga3_materialized_views.sql',                'ccbcf7927a8fa43c818936fcaf5e974f3db1bc3ff7845d23c90f85cef697c5c2'),
  ('208_ga4_panchanga_mv.sql',                      '54ba4eda113fb00ef7e9f25e4fa3b34f448a273ec3eece9388dc7734fea2f59f'),
  ('209_ga5_sensitive_points_mv.sql',               '3a59154c8f7c0a22af92d7e0b3e4b6db02b6879ca2daa39c6d0d6e71c8593cae'),
  ('210_ga6_chart_divisionals_extension.sql',       '1a61013f6b5610b8145ee88e7d4dbf45e9560f456d503fb8d27831afa5fecfbb'),
  ('211_ga7_dashas_kp_sublevel.sql',                '53c58e5ed09de9c196f03a33a7b3b96389b04ee703c25e93fef6021d89e5028f'),
  ('212_ga8_t1_structural.sql',                     'bb43a71c4b0962ce8d03093452acbbfd3cd7fcc40c9a2b6126dfabe109704244'),
  ('213_ga9_sade_sati.sql',                         '30234144d4e381f9e32efdae2d6a4a4059ddffcccb74226ef9687aa1b117ab24'),
  ('214_ga_chartfacts_count_sql.sql',               'e93cfe53ff4b5a97e9b3ef59d0beafe25c6576e7649dbdccb3cba605a4bb647f'),
  ('223_orchestrator_rebuild_probe_dag.sql',        '3877162de30170b0442a46a00c19f07dd93194e22967e29b2799e05b3224411a'),
  ('224_l2_l5_id_underscore_rename.sql',            '685b04f82c96a8ddd89cb02f9f4ade3fc4ec73c90824d3fe26a90a786daa1290'),
  ('225_fix_asset_throughput_pk.sql',               'c45d683f9a14230645452eb62fa6ba5d795475f3b3b86c7a27392e788eb65313'),
  ('226_bodha_spec_tables.sql',                     'b006dd513917458218846fae9ea0f2719ea8008c1a73cfcaa4d330ac43649043'),
  ('227_ga_structural_floor_update.sql',            '5414c1d91e5693575ad9763703bb9157053c067d5b7beeb6be8cf2f201c7cd4c'),
  ('228_reactivate_chart_facts_partitioned_assets.sql', '6b5d5128dda18fd81bfe9afbd729b68241d7789fe698418ff44e6945899dea43'),
  ('230_bodha_registry_reconcile.sql',              'ce6dd718948d9083a1cfc4490d86e8a4f049c88e8e091d48451c4443b9f3f334'),
  ('236_ganita_catalog_current.sql',                '68dd8c334d98598e30064360f31959c95c1eb39efa53a61295592bfba858827f'),
  ('238_bg_nakshatra_tables.sql',                   '3887b67871079f4d48d0e1f40f91cf71ee0839be87d0b9d3968d28c582eeb35c'),
  ('239_bg_nakshatra_registry.sql',                 'ba99c9cc218dc5f6f30b278025bc69af6fb7329114ddf720468bdc96e7581191'),
  ('240_bg_nakshatra_target_floor.sql',             'c8cec61495473df29f2c891c29f3fe1c8635bb988706c4e874e858481cbd5f50'),
  ('241_idle_in_transaction_timeout.sql',           'eac60bf44a97ee34494b29a1cd978a4f0d67e8137e92daf85c4bf566973f8210'),
  ('250_l3_count_sql_param_fix.sql',                '287a007aa22cbd0d8043abb7e7ad990045e73a65fb85f089b8a18cf4189a2246'),
  ('292_ga_nakshatra_registry.sql',                 '39943574018a85258c381069b3d055364f482651b03f927d899f4a0af7287332'),
  ('293_ga_nakshatra_target_floor.sql',             'b357a81deba28a35a1858128770322e2701ffcd9fa63824ce27c232f68158174'),
  ('brahma_bo_2-5.sql',                             '4ae956ef317a26444632d76bbae3c8e20dcfe93015743eec0c5d3d7e9606364b'),
  ('brahma_bo_2-6.sql',                             '5406e6830699bc22de2ca0baca52b1cf3c54c6558a9724d793a0260ba68eb6c2'),
  ('brahma_bo_2-7.sql',                             '7bdb02eb1629b667c1e014657197bcadad0f2d3a0797301c14d7eac01095c202'),
  ('brahma_bo_2-8.sql',                             'e37d59f7c0b4d92ca53d2983ff98f5d2d35289243086b8fc2b1f27635869399c'),
  ('brahma_bodha_bo22.sql',                         '6e857f229e3c66541f052c162763bcbba0780771e12de9c44cfb51a7711ae665'),
  ('brahma_bodha_bo24.sql',                         '8a6552735b452d9ae252e6392f96163e40443129d9097050791489beafe2935d'),
  ('brahma_ganita.sql',                             '2340812bb1644fe3f3d9f5221a44b548454c6058b27f79c7c11d0dd1aaf08813'),
  ('brahma_kala_convergence.sql',                   '2477d1c43d1797f60e9b7b44ab6a4df166e7cd29154ca9511e5b134852b172da'),
  ('brahma_kala_obstruction.sql',                   '4354aa02091e77b424f435b80b745f8e1e169d18be082d2364982281d9698992'),
  ('brahma_kala_timeline.sql',                      'f5beba3d9721d4560ef27c299ba5cb3e9d63794e99037159a9dd678b7580133b'),
  ('brahma_mimamsa_answer_quality.sql',             '282ca905c2a4f888f6d5a2038ae651fa423af1c57a3259d28ca81435c24a6f5b'),
  ('brahma_mimamsa_lel_intake.sql',                 '0c1277e5e447ae893864b11cfde7260d1af7c284f7e5b1be61164179116de8b1'),
  ('brahma_mimamsa_mi_5_5.sql',                     'e7e71d02edd0c48a8a9c1812391064a122940f43f260d5f5aa3b9b0c885aedf1'),
  ('brahma_mimamsa_multiplier.sql',                 '99a2605f29d233a5417b07362e64bb7f383f8d0ae5916fa7b23789789d5adba1'),
  ('brahma_mimamsa_outcome.sql',                    'cc35b5b1c4314b93499fd6c7179f11e3249c7363858af6d8550d75e243b72f10'),
  ('brahma_mimamsa_prediction_ledger.sql',          'b8e0ff0dd1272e37c9e27a23be1f1927f99388b7849781bca32edf51f95f52b2'),
  ('brahma_phala_anchors.sql',                      '45045e6b39c86afa4438fb647a6d5ba48f01b2ba660c5622c28bbc8338849ea7'),
  ('brahma_phala_mitigation.sql',                   '697e24c1067a2b4ea0cb3a08621d3b6b37f6ca88126b757b36366318d3bb2fd6'),
  ('brahma_phala_muhurta.sql',                      '83d5b5082ac70e929baeebccc4fccb6caea0ae81f5372bf3edeba6002ee8769f'),
  ('brahma_phala_rectification.sql',                '89c199f4fc02b3d2d4cd2073e6dbaab68c23a86585b3e32b31849bb658df3e6a'),
  ('ws2_l0_ephemeris.sql',                          'cecfdf0e822f36c0b9f7bbd5880f0f9e636c9681aa200d51e1ae02a60f0b2178'),
  ('ws2_l0_remedy_corpus.sql',                      '61d710dfaeb42a191d2707b61c996452243a96ec65f6090e667420059a98404a')
ON CONFLICT (filename) DO NOTHING;
