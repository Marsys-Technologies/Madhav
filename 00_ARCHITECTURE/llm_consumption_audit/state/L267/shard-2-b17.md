# Lane 2 Evidence-Sufficiency — Shard 2-b17 (Group K, Kāla-vidhi)

Worker: Lane 2 EVIDENCE-SUFFICIENCY (P-12 evidence-plan-then-acquire). Deployed MCP connector (read-only).
Charter §7.3 4-point scale. Date of run: 2026-07-12.
Charts: native `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek) · abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a`.
Questions: K1 varshaphal, K2 current-period quality, K3 muhurta best-window, K4 double-transit confirmation for named bhava — each narrow+broad × 2 charts = 16 instances.

trim_seen: TRUE (phala_outlook trim_report present; see F-K1-DROWN / F-K1-TRIM).

---

## Environment discovery (applies across K2/K4)

**SIDECAR DOWN.** `kala_temporal_bundle` (native) returned fully empty:
`timeline_excerpt:[], convergence_windows:[], obstructions:[], snapshot.active_dasha:null, transit_state:"sidecar unavailable — no transit data", kala_readiness.score:null, mode:"fallback_empty", note:"Sidecar unavailable — graceful-empty response (native data removed by D7 remediation)", sidecar_available:false`.
`get_temporal_windows` (both charts, 2026-07-01→2027-02-01) → `activations:[], activation_count:0, predicates:[]`.
So the entire live L3 transit / convergence / kala-snapshot / kala_readiness surface is unavailable at consumption time, while DB-backed tools (`get_dashas`, `kala_life_arc_get`, `ganita_*`) still serve. Honestly self-declared (not class 5), but a class-4 EMPTY SHELL at the surfaces built exactly for "what's active now / where do things converge."

---

## K1 — varshaphal "how is this year"

### Evidence plan
An acharya answering "how is this year" (Tājaka/Varshaphal) needs, in order: (1) current-year annual chart (Varsha kundali) + Muntha sign/house + Munthesa; (2) Varshesha (year lord) and its strength (Harsha Bala / Panchavargiya Bala); (3) Tājika yogas (Ithasala/Ishrafa/Muthashila/Nakta/etc.); (4) Sahams; (5) Mudda-dasha within the year; (6) an interpretation binding the above into a year-quality read; corroborate with (7) Vimshottari dasha + a forward outlook.
Tools: `ganita_tajaka_get` (1–5, L1 raw), `phala_outlook_get` (6–7, interpreted), `get_dashas` (7).

### Acquisition
- `ganita_tajaka_get` native → **264 KB** payload; text field = stub `"[large payload — see structuredContent]"`. Structured content: `varsha_year_lords` (48 rows, all years × 5 ayanamsha), `hadda_lord_facts` (245), `triraashipathi`, `vargottama`; inner `total:293`. Current year row (yr 43, Lahiri, 2026-02-04→2027-02-05): `year_lord:Venus`, `muntha_position_jsonb`={lord Venus, Libra 12.43°, house_from_natal_lagna 7, house_from_varsha_lagna 10}, `applicable_tajik_yogas_array`=["Ishrafa","Dutthottha"], `candidate_lord_jsonb.offices` (Lagnesa Saturn panchavargiya_bala 105; Munthesa Venus, per-varga D1/D2/D3/D9/D12 dignities). Grep on full payload: `muntha` yes, `ithasala/ishrafa` yes, `panchavargiya` yes; **`harsha`=0, `saham`=0, `mudda`=0, `varshesha`=0**.
- `ganita_tajaka_get` abhinandan → 260 KB; current year 42 (2026-03-02→…), `year_lord:Mercury`, yogas ["Ithasala","Ishrafa","Nakta","Dutthottha"].
- `phala_outlook_get` native (12mo) → anchors[5], mitigations[10], auspicious_windows[10], `summary_confidence:0.322`, `trim_report[3]`. **4 of 5 anchors identical**: `transition/transition_discovery_event dir=elevated conf=0.322 band[0.272,0.372] mag=minor` for one window 2026-07-11→2026-10-09 (5th = career/career_discovery, same conf). trim_report: `anchors 100→5 (hard-cap)`, `mitigations 100→10`, `auspicious_windows 30→10`; every `recover_via.instrument:"unknown_tool"`, hint `"call unknown_tool again"`.
- `phala_outlook_get` abhinandan → **identical** `summary_confidence:0.322`, same near-dup anchor set, same `unknown_tool` trim.

### Findings / grade
Raw Tājaka annual-chart inputs for the current year ARE served, sidereal, per-ayanamsha (year lord, Muntha, Munthesa, tājika yogas, panchavargiya bala). But: no varshaphal-interpretation tool (translation ungoverned — class 9); Harsha Bala (named in tool description), Sahams, Mudda-dasha absent (facet gaps); the only interpreted forward layer (phala_outlook) is a drowned identical-score wall + broken trim recovery + non-chart-discriminating (identical 0.322 across two charts). 264 KB dump returns all 48 years when only the current year is asked (no year filter).
- **narrow** (both charts): SUFFICIENT-WITH-GAPS — a Tājaka year-read is composable from raw facts; method/translation improvised; sahams/mudda/harsha missing.
- **broad** (both charts): SUFFICIENT-WITH-GAPS — same, plus the forward-anchor width is drowned/undiscriminating.

---

## K2 — current-period quality

### Evidence plan
Needs: (1) running MD/AD/PD lords + their natal dignity/strength/house (classical core of period quality); (2) which MSR signals/yogas are activated by those lords NOW; (3) convergence windows in the current span; (4) a period-quality label/score; (5) forward anchors. Tools: `get_dashas`, `get_temporal_windows`, `kala_temporal_bundle`, `kala_life_arc_get`, `phala_outlook_get`.

### Acquisition
- `get_dashas` native (from 2026-07-01) → Mercury MD / Saturn AD; rows carry `lord_natal_house_d1, lord_natal_dignity_d1, lord_natal_shadbala_total, sandhi_flag`. abhinandan → Saturn MD / Rahu AD (+ Jupiter AD), same depth.
- `kala_life_arc_get` native → current MD parva #19 Mercury 2010–2027 quality **"peak"** avg_effective_score 0.591, themes [intellect,communication,commerce], narrative; current AD parva #28 Saturn 2024–2027 "peak" 0.577, high_convergence_count 217. abhinandan → parva #20 Saturn "peak" 0.616; #29 Jupiter 2026–2029 "peak" 0.606.
- `get_temporal_windows` both charts → `activation_count:0` (EMPTY). `kala_temporal_bundle` native → fully empty (sidecar down, see Environment). `drill_next` → `marsys://tool/L3/query_convergence_windows` (NOT in the 130-tool list) + `.../query_life_arc`.
- INCONSISTENCY: temporal_windows says 0 convergences in current span; life_arc reports 217 high_convergence for the same Saturn-AD span.

### Findings / grade
Period-quality core (MD/AD lord dignity+shadbala + parva quality label/score/themes) IS composable. Missing: live activated-signal set + convergence windows + kala_readiness (all empty — sidecar down); a class-3 inconsistency between the two L3 surfaces.
- **narrow** (both): SUFFICIENT-WITH-GAPS.
- **broad** (both): SUFFICIENT-WITH-GAPS — the depth axis (which signals/yogas fire now, convergence) is entirely empty; static dasha-dignity + parva label still carry a defensible read.

---

## K3 — muhurta best window next N months for X (T-15)

### Evidence plan
Needs: an electional finder scoring candidate windows for a named activity over a horizon, blending panchanga + dasha + transit + chart signals. Tool: `muhurta_finder`/`kala_muhurta_get`.

### Acquisition
- `muhurta_finder` native, action_type "marriage", 2026-08-01→2026-10-28 → **20 windows** each with `score` + `factors{panchanga_quality, dasha_quality, transit_quality, signal_activation, panchanga_details{tithi,vara_lord,moon_nakshatra}}`; algorithm panchanga40/dasha30/transit20/signal10; top window 2026-08-19 score 0.68. abhinandan → 20 windows, top 0.622.
- Constraint: `date_range` **max 90 days** (92-day call → 422 error). action_type is a governed enum, disclosed on invalid input: `[marriage, travel, business, medical, education, property, general]` (7 values).

### Findings / grade
Strongest tool in the group — real composite scoring, self-describing factors, sidereal, works on both charts.
- **narrow** (both): SUFFICIENT — a specific activity within ≤3 months is fully served.
- **broad** (both): SUFFICIENT-WITH-GAPS — "next N months" with N>3 forces silent multi-call decomposition (class 9, 90-day cap); an arbitrary "X" must be squeezed into the 7-value enum (taxonomy translation, but enum is disclosed on error = mostly governed).

---

## K4 — double-transit confirmation for a named bhava

### Evidence plan
Needs (Gochara double-transit / Phaladeepika): (1) natal bhava sign + its lord; (2) forward SIDEREAL transit of Jupiter and Saturn; (3) the convergence test — both Jupiter and Saturn simultaneously transiting/aspecting the named bhava AND its lord, with the window; (4) dasha corroboration. Tools: `query_planet_transit`, `ganita_transit_anchors_get`, `ganita_sade_sati_get`, `ref_transit_rules_get`, `kala_temporal_bundle`.

### Acquisition
- `query_planet_transit` Jupiter & Saturn, 2026-07→2027-07 → 366 daily rows each with `tropical_longitude, sign_number, degree_in_sign, nakshatra_number, is_retrograde, speed_dps`. **Sign is TROPICAL**: Saturn tropical_longitude 14.2° (sign_number 1 = tropical Aries) — sidereal (Lahiri ~24°) = Pisces ~20°, which is the astronomically correct Vedic rashi. So served `sign_number` is the wrong frame for Vedic gochara; Jupiter shown "sign 5" (tropical Leo) whole year = sidereal Cancer.
- No `double_transit` / `gochara` composed tool in the 130-tool list. `ref_transit_rules_get` = L0 Gochara RULE definitions (house-from-Moon), not chart transit. `ganita_transit_anchors_get` = static NATAL anchors (sidereal, house-from-Moon), not forward transit. `ganita_sade_sati_get` = Saturn-only transit family, 78 of **total 1259** rows returned (pagination). `kala_temporal_bundle` transit = empty (sidecar down).

### Findings / grade
No served surface computes the Jupiter+Saturn double-transit convergence on a bhava+its lord; the only forward-transit tool serves a tropical frame mislabeled as "sign" (LLM must subtract ayanamsha itself and reconstruct the entire aspect-convergence method). Sidereal longitude is derivable (tropical_longitude − ayanamsha, cross-checked by nakshatra_number) but the composed confirmation is fully improvised.
- **narrow** (both): INSUFFICIENT.
- **broad** (both): INSUFFICIENT.

---

## Class-9 UNGOVERNED-JUDGMENT log
- K1: mapped raw Tājaka facts (year-lord Venus, Muntha 7th/10th, Ishrafa/Dutthottha, panchavargiya 105) → a "how is this year" life-language read with no interpretation tool governing it (taxonomy→life-language translation; method choice Tājaka vs Vimshottari-phala).
- K2: adjudicated the temporal_windows(0-convergence) vs life_arc(217-convergence) conflict myself (evidence adjudication) and chose parva-quality as the answer basis when the activation layer was empty (method choice).
- K3: silently decomposed "next N months" into ≤90-day sub-calls (question decomposition); mapped free-text "X" onto the 7-value action enum (taxonomy translation).
- K4: chose and hand-executed the entire double-transit method (which planets, which aspects onto bhava+lord, convergence window) AND applied an ayanamsha correction to convert the served tropical frame to sidereal (method choice + numerical improvisation the system should govern).
