# T1 differential test — independent reimplementation vs inspector (sandbox)

## L0 (40 assets)

| asset | check | inspector | ours | class | detail |
|---|---|---|---|---|---|
| bg_dasha_systems | Count.floor | PASS | FAIL | known defect R46 (inspector live=60 from count_sql != table count 20) | live=20, floor=60, delta=-40 |
| bg_dignity_reference | Count.floor | PASS | FAIL | known defect R46 (inspector live=151 from count_sql != table count 9) | live=9, floor=151, delta=-142 |
| bg_doshas | Count.floor | PASS | FAIL | known defect R46 (inspector live=237 from count_sql != table count 79) | live=79, floor=237, delta=-158 |
| bg_ghatana | Count.floor | PASS | FAIL | known defect R46 (inspector live=39 from count_sql != table count 27) | live=27, floor=39, delta=-12 |
| bg_nakshatra | Count.floor | PASS | FAIL | known defect R46 (inspector live=2857 from count_sql != table count 28) | live=28, floor=2857, delta=-2829 |
| bg_prashna_rules | Count.floor | PASS | <absent> | methodology (asset counted via count_sql; no target_table for our plain count) | |
| bg_reference | Count.floor | PASS | FAIL | known defect R46 (inspector live=1242 from count_sql != table count 11) | live=11, floor=1242, delta=-1231 |
| bg_vastu_directions | Count.floor | PASS | FAIL | known defect R46 (inspector live=32 from count_sql != table count 8) | live=8, floor=32, delta=-24 |
| bg_vidhi_floors | Count.floor | PASS | FAIL | known defect R46 (inspector live=423 from count_sql != table count 409) | live=409, floor=423, delta=-14 |
| bg_yogas | Count.floor | PASS | FAIL | known defect R46 (inspector live=784 from count_sql != table count 233) | live=233, floor=784, delta=-551 |

## L1 (19 assets)

| asset | check | inspector | ours | class | detail |
|---|---|---|---|---|---|
| ga_ayurdaya | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=21127, floor=130, delta=+20997 |
| ga_condition | Count.floor | <absent> | FAIL | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=135, floor=2880, delta=-2745 |
| ga_dashas | Count.floor | <absent> | FAIL | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=72818, floor=471767, delta=-398949 |
| ga_medical | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=135, floor=45, delta=+90 |
| ga_nakshatra | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=21127, floor=1813, delta=+19314 |
| ga_panchanga | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=21127, floor=437, delta=+20690 |
| ga_positions | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=21127, floor=1205, delta=+19922 |
| ga_prashna | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=0, floor=0, delta=+0 |
| ga_sade_sati | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=21127, floor=6120, delta=+15007 |
| ga_sensitive | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=21127, floor=8775, delta=+12352 |
| ga_sensitive_degree | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=21127, floor=335, delta=+20792 |
| ga_tajaka | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=780, floor=240, delta=+540 |
| ga_transit_anchors | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=135, floor=45, delta=+90 |
| ga_vargas | Count.floor | <absent> | FAIL | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=0, floor=22092, delta=-22092 |
| ga_vastu | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=120, floor=40, delta=+80 |
| ga_vichara | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=25011, floor=8249, delta=+16762 |
| ga_yoga | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=202, floor=63, delta=+139 |

## L2 (23 assets)

| asset | check | inspector | ours | class | detail |
|---|---|---|---|---|---|
| bo_anveshana | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=3695, floor=500, delta=+3195 |
| bo_arudha | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=7409, floor=15, delta=+7394 |
| bo_bimba | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=1101, floor=140, delta=+961 |
| bo_cdlm_summary | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=15, floor=1, delta=+14 |
| bo_cgm_motifs | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=1811, floor=0, delta=+1811 |
| bo_cgm_paths | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=135, floor=9, delta=+126 |
| bo_chart_gestalt | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=15, floor=1, delta=+14 |
| bo_drishti | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=180, floor=60, delta=+120 |
| bo_grounding | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=2537, floor=0, delta=+2537 |
| bo_karanajala | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=2517, floor=300, delta=+2217 |
| bo_laksana | Count.floor | <absent> | FAIL | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=7409, floor=60000, delta=-52591 |
| bo_laksana_rerank | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=7409, floor=1, delta=+7408 |
| bo_nakshatra_semantic | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=7409, floor=45, delta=+7364 |
| bo_pramana_mapa | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=3, floor=1, delta=+2 |
| bo_pratijna | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=405, floor=0, delta=+405 |
| bo_samskara | Count.floor | <absent> | FAIL | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=7537, floor=60000, delta=-52463 |
| bo_sangati | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=430, floor=70, delta=+360 |
| bo_special_lagna | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=7409, floor=20, delta=+7389 |
| bo_sudarshana | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=7409, floor=45, delta=+7364 |
| bo_upaya | Count.floor | <absent> | FAIL | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=135, floor=180, delta=-45 |
| bo_vargottama_dhana | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=7409, floor=10, delta=+7399 |
| bo_yantra_mechanism | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=1868, floor=1, delta=+1867 |

## L3 (23 assets)

| asset | check | inspector | ours | class | detail |
|---|---|---|---|---|---|
| ka_avadhi | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=3620, floor=1169, delta=+2451 |
| ka_bhavishya_lekha | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=100, floor=100, delta=+0 |
| ka_gochara | Build.registered | PASS | FAIL | known defect R43 (literal-grep vs AST read of @register) | grep hits in 2 files |
| ka_gochara | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=40117, floor=83, delta=+40034 |
| ka_gochara_resonance | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_gochara_resonance.py; registry agrees |
| ka_gochara_resonance | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=1595, floor=762, delta=+833 |
| ka_gochara_sweep | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_gochara_sweep.py; registry agrees |
| ka_gochara_sweep | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=40117, floor=16297, delta=+23820 |
| ka_gochara_v3_century_materialize | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_gochara_v3_century_materialize.py; registry agrees |
| ka_gochara_v3_century_materialize | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=1993, floor=914, delta=+1079 |
| ka_jivana_parva | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=309, floor=100, delta=+209 |
| ka_kala_darshana | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=750, floor=750, delta=+0 |
| ka_kalasutra | Count.floor | <absent> | FAIL | known defect R48 (Count.floor absent on L3 in inspector) | live=16925, floor=335403, delta=-318478 |
| ka_kota_chakra | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_kota_chakra.py; registry agrees |
| ka_kota_chakra | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=1170, floor=588, delta=+582 |
| ka_kshetra | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_kshetra.py; registry agrees |
| ka_kshetra | Count.floor | <absent> | FAIL | known defect R48 (Count.floor absent on L3 in inspector) | live=549797, floor=8599775, delta=-8049978 |
| ka_moorti_nirnaya | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_moorti_nirnaya.py; registry agrees |
| ka_moorti_nirnaya | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=143, floor=72, delta=+71 |
| ka_muhurta_seva | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_muhurta_seva.py; registry agrees |
| ka_sangam | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=20497, floor=14868, delta=+5629 |
| ka_sudarshana_varsha | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_sudarshana_varsha.py; registry agrees |
| ka_sudarshana_varsha | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=120, floor=120, delta=+0 |
| ka_taranga | Count.floor | <absent> | FAIL | known defect R48 (Count.floor absent on L3 in inspector) | live=13963, floor=92412, delta=-78449 |
| ka_tithi_pravesha | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_tithi_pravesha.py; registry agrees |
| ka_tithi_pravesha | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=240, floor=120, delta=+120 |
| ka_tulana | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_tulana.py; registry agrees |
| ka_vedha_gochara | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit ka_vedha_gochara.py; registry agrees |
| ka_vedha_gochara | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=355, floor=176, delta=+179 |
| ka_vighnakara | Count.floor | <absent> | PASS | known defect R48 (Count.floor absent on L3 in inspector) | live=747, floor=536, delta=+211 |
| ka_yojaka | Count.floor | <absent> | FAIL | known defect R48 (Count.floor absent on L3 in inspector) | live=7525, floor=50104, delta=-42579 |

## L4 (9 assets)

| asset | check | inspector | ours | class | detail |
|---|---|---|---|---|---|
| ph_muhurta | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=183, floor=134, delta=+49 |
| ph_nimitta | Count.floor | <absent> | FAIL | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=60, floor=139, delta=-79 |
| ph_phaladesa | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=26, floor=13, delta=+13 |
| ph_pratikara | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=1277, floor=536, delta=+741 |
| ph_rectification | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=370, floor=186, delta=+184 |
| ph_sankrama | Count.floor | <absent> | FAIL | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=630, floor=2510, delta=-1880 |
| ph_suddha_sodhana | Count.floor | <absent> | FAIL | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=60, floor=139, delta=-79 |

## L5 (14 assets)

| asset | check | inspector | ours | class | detail |
|---|---|---|---|---|---|
| mi_abhilekha | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=0, floor=0, delta=+0 |
| mi_adhilepa | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=9, floor=0, delta=+9 |
| mi_bhara | Build.registered | FAIL | PASS | known defect R43 (literal-grep vs AST read of @register) | grep hit mi_bhara.py; registry agrees |
| mi_bhara | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=7, floor=0, delta=+7 |
| mi_bhavisya | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=195, floor=0, delta=+195 |
| mi_darshana | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=150, floor=0, delta=+150 |
| mi_gunanaka | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=18, floor=0, delta=+18 |
| mi_jivanaghatana | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=63, floor=0, delta=+63 |
| mi_pariksha | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=174, floor=0, delta=+174 |
| mi_pramana | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=57, floor=0, delta=+57 |
| mi_sambandha | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=47, floor=0, delta=+47 |
| mi_sankalpa | Count.floor | <absent> | PASS | finding T1-F1 (inspector silent: no Count.floor — parameterized or multi-table count_sql) | live=0, floor=0, delta=+0 |

**Totals:** 265 agreements; 99 disagreements classed to known defects; 0 NEW disagreements.
