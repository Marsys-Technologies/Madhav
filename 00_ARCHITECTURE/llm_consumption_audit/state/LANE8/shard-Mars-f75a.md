# Lane 8 shard — Mars dossier · chart 1c826d5a (last4 f75a)

dossier_id: Mars_1c826d5a
resume_after_row_id: F01493
rows_total: 75  (60 Appendix-B floor + 15 discovered)
rows_done: 75
status: done
findings_count: 6

## Method
- Facet list from `ledgers/facets.jsonl` (entity=Mars, 75 rows: F00013 … F01493).
- SHAPER #3: `wire_reachable` consumed from `state/CONCEPT_RETRIEVABILITY_MATRIX.jsonl`
  channel — `reachable-surgical` ⇒ TRUE; `served-only-by-down-pipeline` and
  `truly-unreachable` ⇒ FALSE. NOT re-probed.
- `held_in_db` spot-checked on chart 1c826d5a via read-only `chart_facts` (subject `MAR`),
  `chart_dashas` (system_id), `chart_divisionals`.
- Channel anchors: chart_facts / chart_divisionals / chart_dashas = **reachable-surgical**;
  kala_* / phala_* / mimamsa_* / bodha_(non-msr) = **served-only-by-down-pipeline**;
  reference_* / bg_medical / bg_transit / bodha_contradictions / bodha_rm_chart_summary =
  **truly-unreachable**; bodha_msr_signals = mixed (32 surgical / 83 down-pipeline).

## Key DB confirmations (chart 1c826d5a, subject MAR)
- graha_position keys = {longitude_sidereal, sign, sign_lord, nakshatra, nakshatra_lord,
  pada, house_d1, retrograde_flag, combustion_state} — **no declination/latitude/ayana** ⇒ F6/F8 nonexistence.
- Full shadbala tree (sthana/dig/kala/cheshta/drik/naisargika/total), ishta/kashta,
  vimsopaka×4, ashtakavarga (bindu/pinda_sarva/sodhita), all 5 avastha sets, gandanta,
  dignity_per_varga, karaka (chara/karakamsa/web), dispositor_tree, saham (2800),
  upagraha/gulika-mandi, KP lords+cuspal significators+ruling-planets, tara_bala,
  yoga_label(41)/dosha_label(110), tri-deva, pranic strength — all present under MAR/CF.
- chart_dashas system_id ∈ {vimshottari, vimshottari_kp, yogini, chara_karaka, kalachakra,
  ashtottari, mudda, naisargika} ⇒ F44/F46 held+surgical.
- esoteric_point_mrityu = single chart-level `MRITYU_SPHUTA` only — **no per-graha
  mrityu-bhaga degree check** ⇒ F13 confirms anchor R-47 (mrityu-bhaga computed nowhere per graha).

## Per-facet matrix (held | wire | 2-call | usable | channel)

| # | row_id | facet (abbrev) | held | wire | 2c | usable | backing / channel |
|---|--------|----------------|------|------|----|--------|-------------------|
| 1 | F00013 | Sign/dms/bhoga | T | T | T | T | chart_facts graha_position · surgical |
| 2 | F00033 | House WS + bhava-chalit divergence | T | T | T | T | chart_facts position + cusp_kp_lords · surgical |
| 3 | F00053 | Bhava-madhya/sandhi/cusp flavor | T | T | T | T | chart_facts boundary flags + gandanta · surgical |
| 4 | F00073 | Nakshatra/pada/lord + KP star/sub/subsub | T | T | T | T | chart_facts nakshatra/pada/kp_lords · surgical |
| 5 | F00093 | Navatara from Moon & Lagna | T | T | T | T | chart_facts tara_bala · surgical (Lagna-navatara partial) |
| 6 | F00113 | Declination/latitude/rise-set/oriental | F | F | F | F | NOT COMPUTED — nonexistence (class 1) |
| 7 | F00153 | Speed/stationary/retro phase | T | T | T | T | chart_facts retrograde + cheshta_bala · surgical (speed-ratio proxy) |
| 8 | F00173 | Ayana/gola | F | F | F | F | NOT COMPUTED — nonexistence (class 1) |
| 9 | F00193 | Exalt/debil deep-degree; ucha-abhilashi | T | T | T | T | chart_facts dignity_per_varga · surgical |
| 10 | F00213 | Mulatrikona/own/panchadha compound | T | T | T | T | chart_facts dignity + sign_lord · surgical |
| 11 | F00233 | Neecha-bhanga enumeration | F | F | F | F | no NB-grounds category — nonexistence (class 1) |
| 12 | F00253 | Vargottama; pushkara bhaga/navamsha | T | T | T | T | chart_facts vargottama_per_varga · surgical (pushkara partial) |
| 13 | F00273 | Mrityu-bhaga per-graha; yogatara | F | F | F | F | only chart-level MRITYU_SPHUTA — **R-47** nonexistence (class 1) |
| 14 | F00293 | Dagdha/tithi-shunya/mrityu-rashi | T | T | T | T | chart_facts panchanga shoonya_rashi · surgical (dagdha per-graha partial) |
| 15 | F00313 | Sign-type flavor chara/sthira/tattva | F | T | T | T | reference_signs (unreach) but trivially derivable from reachable sign |
| 16 | F00333 | Shadbala complete tree | T | T | T | T | chart_facts graha_shadbala_* · surgical |
| 17 | F00353 | Ishta/Kashta phala | T | T | T | T | chart_facts ishta/kashta_phala · surgical |
| 18 | F00373 | Vimsopaka ×4 + vaiseshikamsha | T | T | T | T | chart_facts vimsopaka_* · surgical |
| 19 | F00393 | Bhava bala owned/occupied | T | T | T | T | chart_facts bhava_bala_* · surgical |
| 20 | F00413 | Pancha-vargiya bala (Tajaka) | F | F | F | F | not computed — nonexistence (class 1) |
| 21 | F00433 | Ashtakavarga BAV/SAV/sodhya/transit | T | T | T | T | chart_facts ashtakavarga_* · surgical (transit-filter partial) |
| 22 | F00453 | Sapta-vargaja dignity/own-varga | T | T | T | T | chart_facts saptavargaja + dignity_per_varga · surgical |
| 23 | F00473 | Combustion + graha yuddha | T | T | T | T | chart_facts combustion + graha_yuddha · surgical |
| 24 | F00493 | Grahan yuti (eclipse assoc) | T | T | T | T | chart_facts eclipse_proximity_natal · surgical |
| 25 | F00513 | Avastha ALL FIVE | T | T | T | T | chart_facts graha_avastha_* (all 5) · surgical |
| 26 | F00533 | Gandanta proximity | T | T | T | T | chart_facts graha_gandanta · surgical |
| 27 | F00553 | Upagraha contact (gulika/mandi/dhuma…) | T | T | T | T | chart_facts upagraha/gulika_mandi/aprakasha · surgical |
| 28 | F00573 | Saham contacts (Tajaka) | T | T | T | T | chart_facts saham_position · surgical |
| 29 | F00593 | Conjunctions + parashari aspects sputa | T | T | T | T | chart_facts aspect_parashari/virupa_drishti · surgical |
| 30 | F00613 | Rashi drishti (Jaimini) | T | T | T | T | chart_facts aspect_jaimini · surgical |
| 31 | F00633 | Sambandha per graha | T | T | T | T | chart_facts sambandha_grade · surgical |
| 32 | F00653 | Dispositor web + chain terminus | T | T | T | T | chart_facts dispositor_tree/chain · surgical |
| 33 | F00673 | Papa/shubha kartari | F | F | F | F | no kartari category — nonexistence (class 1) |
| 34 | F00693 | Argala shubha/papa/virodha ±  | T | T | T | T | chart_facts argala/net_argala · surgical (large; scope by subject) |
| 35 | F00713 | Vedha SBC/nakshatra/latta | F | F | F | F | no SBC-vedha category — nonexistence (class 1) |
| 36 | F00733 | Tara bala from Moon | T | T | T | T | chart_facts tara_bala/graha_tara_bala · surgical |
| 37 | F00753 | Lordships + functional class + yogakaraka | T | T | T | T | chart_facts functional_class/yoga_karaka_flag · surgical |
| 38 | F00773 | Kendradhipati/badhaka/maraka | F | F | F | F | no explicit category — nonexistence (class 1) |
| 39 | F00793 | Naisargika/chara karaka (AK–DK)+karakamsa | T | T | T | T | chart_facts karaka_chara/karakamsa · surgical |
| 40 | F00813 | Arudha involvement | T | T | T | T | chart_facts arudha_pada/bhava_arudha · surgical |
| 41 | F00833 | Yoga participation (every family) | T | T | T | T | chart_facts yoga_label · surgical (deep family view in bodha down-pipeline) |
| 42 | F00853 | Dosha participation | T | T | T | T | chart_facts dosha_label · surgical |
| 43 | F00873 | 22nd drekkana + 64th navamsha | T | T | T | T | chart_divisionals D3/D9 · surgical (lord derived) |
| 44 | F00893 | Vimshottari lordship + windows | T | T | T | T | chart_dashas vimshottari · surgical |
| 45 | F00913 | Dasha-quality context from graha | T | T | T | T | composable: chart_dashas + dignity_per_varga (≤2 calls) |
| 46 | F00933 | Other dasha systems (yogini/chara/asht/kalachakra) | T | T | T | T | chart_dashas multi-system · surgical |
| 47 | F00953 | Transit now / gochara | F | F | F | F | transit not stored (natal chart) — nonexistence (class 1) |
| 48 | F00973 | Sade-sati/dhaiya | F | F | F | F | N/A to Mars entity (Moon/Saturn facet) |
| 49 | F00993 | Double-transit Sat+Jup | F | F | F | F | transit not stored — nonexistence (class 1) |
| 50 | F01013 | Varshaphal role/muntha/year-lord | F | F | F | F | annual Tajaka framework not computed — nonexistence (class 1) |
| 51 | F01033 | Eclipses/stations on natal degree | T | T | T | T | chart_facts eclipse_proximity_natal · surgical |
| 52 | F01053 | **Structural×temporal convergence (R-45)** | T | F | F | F | kala_convergence/bodha_convergence · **served-only-by-down-pipeline** — HBNR (class 1) |
| 53 | F01073 | KP significator ladder + ruling planets | T | T | T | T | chart_facts kp_cuspal_significators/ruling_planets · surgical |
| 54 | F01093 | Nadi roles (jeeva/karma, bhrigu-bindu) | T | T | T | T | chart_facts bhrigu_nadi/esoteric_bhrigu_bindu · surgical |
| 55 | F01113 | **Deity web (nakshatra deity/adhidevata)** | T | F | F | F | reference_nakshatra · **truly-unreachable** — HBNR (class 1) |
| 56 | F01133 | **Remedial mapping + priority vs afflictions** | T | F | F | F | bodha_rm_* · **served-only-by-down-pipeline** — HBNR (class 1) |
| 57 | F01153 | **Medical (avayava/dhatu/dosha/disease)** | T | F | F | F | bg_medical_mappings · **truly-unreachable** — HBNR (class 1) |
| 58 | F01173 | **Sambandha table (varna/guna/tattva…)** | T | F | F | F | reference_planets · **truly-unreachable** — HBNR (class 1) |
| 59 | F01193 | Nodal axis relations | T | T | T | T | chart_facts dispositor/conjunction re Rahu/Ketu · surgical |
| 60 | F01213 | Special-lagna relations + pranapada | T | T | T | T | chart_facts special_lagna/pranapada_sphuta · surgical |
| 61 | F01233 | Panchanga/muhurta window catalog | T | T | T | T | chart_facts panchanga_* · surgical |
| 62 | F01253 | Lal Kitab special point | T | T | T | T | chart_facts lal_kitab_special_point · surgical |
| 63 | F01273 | Maharishi-specific point | T | T | T | T | chart_facts maharsi_specific_point · surgical |
| 64 | F01293 | Chart-level composite/rollup | T | T | T | T | chart_facts center_of_gravity/cluster · surgical |
| 65 | F01313 | Contradiction/convergence meta | T | T | T | T | chart_facts contradiction_pair/convergence_count · surgical |
| 66 | F01333 | Karaka-bhava concordance/overlap | T | T | T | T | chart_facts karaka_bhava_concordance · surgical |
| 67 | F01353 | Western midpoint | T | T | T | T | chart_facts midpoint · surgical |
| 68 | F01373 | Nakshatra co-gravity/tenancy/stats | T | T | T | T | chart_facts nakshatra_cogravity/statistics · surgical |
| 69 | F01393 | Swamsa position | T | T | T | T | chart_facts swamsa_position · surgical |
| 70 | F01413 | Tajika hadda/triraashipathi/vargottama | T | T | T | T | chart_facts tajik_* · surgical |
| 71 | F01433 | Esoteric sensitive-point web | T | T | T | T | chart_facts esoteric_point_* · surgical |
| 72 | F01453 | Pranic strength per graha | T | T | T | T | chart_facts pranic_strength_per_graha · surgical |
| 73 | F01473 | Tri-deva role strength (Jaimini) | T | T | T | T | chart_facts tri_deva_role_strength · surgical |
| 74 | F01493 | Shani special-period catalog | T | T | T | T | chart_facts *_shani_period · surgical (Saturn-scoped; marginal for Mars) |
| 75 | (F01493 dup)| Saturn/Sun-derived special points | T | T | T | T | chart_facts saturn_derived/sun_derived · surgical |

*(Note: facet_number 74/75 map to F01473/F01493 respectively; the two DISCOVERED Shani/Saturn-Sun rows.)*

## Dossier rollup
- facets_total: 75
- held_in_db: 62 (13 nonexistent: F6,F8,F11,F13,F15,F20,F33,F35,F38,F47,F48,F49,F50)
- wire_reachable: 58
- reachable_in_2_calls: 58
- usable_form: 58
- held_but_not_received (held=T ∧ (¬wire ∨ ¬usable)): **5** — F52, F55, F56, F57, F58
- dossier_completeness_pct: 58/75 = **77.3%**
- **dossier_verdict: PARTIAL** — the structural core (position, dignity, full shadbala,
  all-5 avastha, ashtakavarga, aspects, dispositor, karaka, yoga/dosha, all dasha systems,
  KP, saham, upagraha, nadi, esoteric web) is entirely reachable-surgical and composable at
  acharya depth. Material gaps: the depth-axis-named **structural×temporal convergence**
  (R-45), remedial-priority, medical, deity, and natural-sambandha layers are held but
  served only by the down-pipeline / truly-unreachable channels; plus a nonexistence
  cluster (per-graha mrityu-bhaga R-47, kartari, SBC-vedha, kendradhipati/badhaka/maraka,
  transit/varshaphal). Composable-with-material-gaps ⇒ PARTIAL, not SYNTHESIZABLE.

## Findings (root-caused)

### HELD-BUT-NOT-RECEIVED (5) — all primary class 1 UNREACHABLE

**FIND-M1 · F52 · Structural×temporal convergence unreachable (R-45 rediscovery)**
- class 1 UNREACHABLE (served-only-by-down-pipeline). severity HIGH. layer: MCP contract / serving-query.
- Mars's yoga/promise temporal-ripeness (recent-past + near-future) lives in
  `kala_convergence` / `bodha_convergence`, both channel=`served-only-by-down-pipeline` —
  no surgical MCP path a consuming LLM can call. The Charter §1 depth axis names this facet
  explicitly ("structural×temporal convergence past/near-future"); its absence from the wire
  is the single most consequential gap for Mars synthesis. Dedupe: extends anchor R-45.

**FIND-M2 · F55 · Deity web unreachable**
- class 1 UNREACHABLE (truly-unreachable). severity MED. layer: MCP contract.
- Nakshatra deity / adhidevata-pratyadhidevata / ishta-devata path held in
  `reference_nakshatra` (truly-unreachable). ishta-devata karakamsa anchor IS reachable, but
  the deity resolution table is not. Dedupe: new.

**FIND-M3 · F56 · Remedial mapping + affliction-priority unreachable**
- class 1 UNREACHABLE (served-only-by-down-pipeline). severity MED-HIGH. layer: serving-query.
- Chart-specific gemstone/mantra/yantra/dana and "does served remedial priority reflect
  Mars's actual afflictions" live in `bodha_rm_*` (down-pipeline; `bodha_rm_chart_summary`
  truly-unreachable). Generic `brahma_remedy_corpus` is surgical but not chart-scoped. Dedupe: new.

**FIND-M4 · F57 · Medical significations unreachable**
- class 1 UNREACHABLE (truly-unreachable). severity MED. layer: MCP contract.
- Avayava/dhatu/tridosha/disease mappings from Mars afflictions held in
  `bg_medical_mappings` (truly-unreachable). Dedupe: new.

**FIND-M5 · F58 · Natural sambandha table unreachable**
- class 1 UNREACHABLE (truly-unreachable). severity LOW-MED. layer: MCP contract.
- Mars's varna/guna/tattva/gender/direction/season/taste/metal/grain/color held in
  `reference_planets` (truly-unreachable); `graha_sign_attributes` holds only degree/sign_num.
  Dedupe: new.

### UNREACHABLE-BY-NONEXISTENCE (data-plane gaps; feed §6 concept-completeness, class 1)
Not counted in held-but-not-received (held_in_db=false), logged for concept-completeness:
- **FIND-M6 · F13 · Per-graha mrityu-bhaga not computed (R-47 rediscovery).** Only a single
  chart-level `MRITYU_SPHUTA` exists; no per-graha per-sign mrityu-bhaga degree check.
  class 1 nonexistence, severity MED. Dedupe: **confirms anchor R-47.**
- F6/F8 coordinate geometry (declination/kranti, latitude/shara, oriental-occidental,
  ayana/gola) — not in `graha_position`.
- F11 neecha-bhanga grounds enumeration; F20 Tajaka pancha-vargiya bala; F33 papa/shubha
  kartari; F35 Sarvatobhadra/latta vedha; F38 kendradhipati-dosha/badhaka/maraka;
  F47/F49 transit + double-transit; F50 varshaphal/muntha — none computed.
  (F48 sade-sati N/A to Mars entity — scope note, not a finding.)

## Coverage self-declaration
Mars dossier — chart 1c826d5a: **audited** (75/75 rows graded, all four columns populated).
