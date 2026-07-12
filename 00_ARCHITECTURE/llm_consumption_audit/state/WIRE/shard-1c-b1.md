# Shard 1c-b1 — SERVICES census (Lane 1c worker)

status: COMPLETE
worker: Lane 1c SERVICES-census b1 (6 services)
charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1
chart: 482012f1-710e-4a25-994a-93821f5871aa (native)
services_tested: 6/6
date: 2026-07-12

## Environment note
- `:3000` MCP surgical primitives (`/api/mcp/primitives/<tool>`) IS the real consumer path — fully DB-wired, works.
- `:8000` python-sidecar `/api/compute/*` is **NOT DB-configured in this env** (`DATABASE_URL not configured`/`not set`); every DB-dependent sidecar path fails there. Grading done against `:3000` where a whitelisted tool exists; `:8000` used only for cross-path INCONSISTENT checks.
- Surgical whitelist (LCA-2): dashas = `query_dasha_periods` (NOT `query_dashas`); panchanga = `query_panchanga`; varshaphal = `query_varshaphala`/`query_varshphal`; muhurta = `muhurta_finder`/`query_muhurat`. **prashna cast NOT whitelisted** → full-pipeline-only.

## Results

### 1. panchanga (query_panchanga) — FAIL (reachable=true, usable=false)
`ok:true` but `date` param **silently IGNORED**. date=2035-03-15 and date=2040-01-01 both return identical natal **birth-day** panchanga from chart_facts.
- Evidence: `citation_ref="panchanga_abhijit_muhurta.ABHIJIT_MUHURTA_BIRTH_DAY.duration_minutes@...:ay=INVARIANT:eng=panchanga_engine/2.0.0-P2"`; total=200 identical both dates; 221 `panchanga_%` facts in chart_facts.
- Live engine EXISTS (muhurta path computes tithi/nakshatra/yoga for 2026-08) so date-compute is possible but not wired → RETRIEVAL-plane gap.
- **class 2 (WRONG)** primary; **class 5 (DISHONEST)** secondary (invocation echoes date, no "date ignored" flag). Severity HIGH.

### 2. muhurta finder (query_muhurat / muhurta_finder) — SUFFICIENT-WITH-GAPS (reachable=true, usable=true)
`:3000` returns 10 real scored marriage windows. e.g. 2026-08-19→08-21 score 0.68; factors {panchanga_quality .68, dasha_quality .72, transit_quality .65, signal_activation .62}; panchanga_details {tithi Shukla Saptami, vara_lord Mercury, moon_nakshatra Swati, yoga Brahma}. Provenance asset PH-4-4.
- GAP a: **no Tara Bala / Chandra Bala overlay** despite chart_id supplied (test_spec's ask). class 4 partial.
- GAP b: `dasha_details.ad_lord:"unknown"` while md_lord=Mercury resolves. class 4/5 partial.
- GAP c: INCONSISTENT across paths — `:8000` path returns `windows:[]`/`empty_reason:"panchanga_daily has no populated rows"` vs `:3000` 10 windows. class 3. (partly env)
- GAP d: `action_type:"vivah"` (Sanskrit) rejected — only English enum. class 9 lexicon. Severity MED.

### 3. tajika/varshaphal (query_varshaphala / query_varshphal) — FAIL (reachable=true, usable=false)
`ok:true` but `year` param **inert**. year=2030 and year=2045 both return total=1465, identical `ga_tajaka.varsha1` static natal Tajika facts (tajik_hadda_lord/triraashipathi/vargottama). 1225 `tajik_%` facts in DB, all NATAL.
- No annual solar-return chart: no Varsha Lagna, Muntha, Varshesha, Sahams, Tajika aspects, year-specific Mudda dasha.
- **class 4 (EMPTY SHELL)** primary; **class 5 (DISHONEST)** (year echoed, payload year-independent). Severity HIGH.

### 4. prashna cast — FAIL / UNREACHABLE (compute_reachable=false)
- Not whitelisted → full-pipeline-only (ask_madhav), broken per LCA-2.
- `:8000/api/compute/prashna/cast` with valid params → **HTTP 500** (env: no DATABASE_URL for ga_prashna judgment); fails with and without `querent_natal_chart_id`. (422 only on schema-invalid input, confirming endpoint validates then 500s on compute.)
- **class 1 (UNREACHABLE)** primary. Severity HIGH (partly env — flagged).

### 5. Vimshottari dasha (query_dasha_periods) — PASS (reachable=true, usable=true)
Correct MD/AD/PD chain. Mercury MD 2010-08-18→2027-08-18 (house 10, Capricorn, Uttara Ashadha); Saturn AD 2024-12-08→2027-08-18 (house 7, Libra, Vishakha, exalted). Facets: natal house/dignity/nakshatra, sandhi_flag, two_pass_verified, resolvable citation_ref; `next_count:3` honored.
- Minor: `lord_natal_shadbala_total:null`. Not a finding at this altitude.

### 6. Yogini dasha (query_dasha_periods, system_id=yogini) — FAIL — MAJOR (reachable-but-wrong)
`system_id` param **completely IGNORED** → serves VIMSHOTTARI. Confirmed hardcoded across 3 systems: yogini, ashtottari, kalachakra ALL return `facets_applied.system:"vimshottari"`, rows `system_id:"vimshottari"`, lord Mercury.
- Data EXISTS: chart_dashas holds yogini=83,740 (yogini lords Pingala/Dhanya confirmed by SQL), mudda=102,373, chara_karaka=155,135, kalachakra=35,265, ashtottari=32,960, naisargika=21,945, vimshottari_kp=5,760. **~437k rows across 7 non-vimshottari systems UNREACHABLE via the only dasha serving tool.**
- **class 1 (UNREACHABLE)** primary; **class 5 (DISHONEST)** (system_id echoed, vimshottari substituted, no flag); **class 2 (WRONG)**. Severity CRITICAL. New-finding / calibration-anchor candidate.

## Cross-service pattern (systemic)
Three of six surgical tools — `query_panchanga` (date), `query_varshaphala` (year), `query_dasha_periods` (system_id) — **silently ignore their primary discriminating parameter**, echo it in `invocation_params`, and serve a fixed natal/default dataset. Systemic class-5 (DISHONEST SELF-DESCRIPTION): params accepted into the receipt but not routed into the query.
