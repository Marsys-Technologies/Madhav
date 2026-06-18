# L0/L1 Data Investigation — answer from the ACTUAL data, not the specs (v1.1)

**Paste into Claude Code (Antigravity). READ-ONLY. Make NO changes.** Connect to prod (Cloud SQL proxy;
password from Secret Manager `amjis-db-password/3`). Native chart `482012f1-710e-4a25-994a-93821f5871aa`
(`362f9f17` is a dead phantom — never use it). Produce `00_ARCHITECTURE/L0_L1_DATA_INVESTIGATION_v1_0.md`
with, per question: the actual query, the actual result (counts + distinct values + a sample row), and a
one-line factual answer grounded ONLY in what the data shows. No interpretation from documents.

The PURPOSE: empirically baseline what ga_positions / ga_vargas / ga_strength / ga_sensitive / ga_condition /
ga_nakshatra / ga_transit_anchors / ga_medical actually hold TODAY — D1-only or already partial-varga — so the
L1 enrichment expansions (per-varga Shadbala, per-varga dignity, classical sensitive-point completeness) are
sized against reality, not assumption.

---

**Q1 — Graha-sthāna (positions): which charts/positions?**
`SELECT DISTINCT fact_category FROM chart_facts WHERE chart_id=:c AND fact_category LIKE 'graha%'`; +
`SELECT count(*), count(DISTINCT fact_subject) FROM ganita_positions WHERE chart_id=:c`. Is it D1-only, or do
varga positions live here vs in chart_divisionals? Report bodies, ayanamshas, and where varga positions sit.

**Q2 — Varga (chart_divisionals): all 30?**
`SELECT DISTINCT varga FROM chart_divisionals WHERE chart_id=:c ORDER BY varga`. List every distinct varga;
count them; confirm which of the standard 30 (D1,D2,D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D16,D20,D24,D27,D30,D40,
D45,D60 + the supplementary D108/D150/etc.) are present or missing.

**Q3 — Strength (ga_strength): D1 only or per-varga? ⭐ SIZING QUESTION**
`SELECT DISTINCT fact_category FROM chart_facts WHERE chart_id=:c AND (fact_category LIKE '%shadbala%' OR
fact_category LIKE '%vimsopaka%' OR fact_category LIKE '%bala%' OR fact_category LIKE 'ashtakavarga%')`. For
EACH strength type, determine whether the data carries a VARGA DIMENSION (a column / fact_key / fact_subject
component naming a divisional chart) or is purely D1. Specifically answer:
- Is **shadbala** computed D1-only, or already for some vargas? Which six components are present?
- Is **Vimsopaka** present, and which varga-GROUPS (shadvarga-6 / saptavarga-7 / dasavarga-10 / shodasavarga-16)?
- Is **Ashtakavarga** (BAV/SAV bindus) D1-only or per-varga?
Report the EXACT current varga-coverage of each strength type. (This sizes the per-varga Shadbala expansion.)

**Q4 — Sensitive points (ga_sensitive): D1 only? + which points exist? ⭐ DIFF QUESTION**
`SELECT DISTINCT fact_category, count(*) FROM chart_facts WHERE chart_id=:c AND <sensitive-point categories:
upagraha/saham/karaka/arudha/sphuta/special_lagna/yogi/midpoint/kp_/aprakasha/tajik/esoteric/...> GROUP BY 1`.
Two outputs:
(a) Does ANY sensitive-point row carry a varga dimension, or are they all D1 longitudes? (Confirm/deny D1-only;
   note any cited varga cases present — Karakamsa=AK-in-D9, Arudha-in-D9.)
(b) **INVENTORY the actual points present**, then DIFF against this classical universe and report what's
   MISSING: Gulika/Mandi · the 5 sub-Rahu upagrahas (Dhuma/Vyatipata/Parivesha/Indrachapa/Upaketu) · the
   Sun-derived upagrahas (Kala/Mrityu/Artha-Prahara/Yamaghantaka) · Bhrigu Bindu · the 12 bhava-Arudhas +
   Upapada(UL) + A7/A10 · Karakamsa/Swamsa · Pranapada · special lagnas (Hora/Ghati/Bhava/Vighati) · Sphuta
   family (Beeja/Kshetra/Tri/Chatu/Panch-sphuta) · Yogi/Avayogi point + Yogi/Dagdha rashi · the full Saham set
   (Punya/Yasha/Vidya + the ~36 Tajik Sahams — note these may live in ga_tajaka, check that boundary). Output a
   PRESENT / MISSING table for the classical universe. (Also note, separately, whether any cross-system points
   — Part of Fortune, Vertex, Lilith, asteroids — exist; these are the cross-tradition shelf, not core.)

**Q5 — Nakshatra strength: any strength-of-nakshatra metric?**
`SELECT DISTINCT fact_category FROM chart_facts WHERE chart_id=:c AND fact_category LIKE '%nakshatra%'` (the
ga_nakshatra 14 categories). Is there ANY nakshatra-STRENGTH concept — Tara-bala, nakshatra-dispositor strength,
a within-chart nakshatra-statistics score, severity-gradient? Report which nakshatra metrics exist and whether
any is a "strength" measure.

**Q6 — Planetary condition composite (ga_condition / Graha-sthiti): what + which charts? ⭐ SIZING QUESTION**
`\d ga_condition_composite` (or the actual table name) + `SELECT * FROM ga_condition_composite WHERE chart_id=:c
LIMIT 3` (show actual columns + a sample row + the condition_score_breakdown JSONB for one graha). What
components make up the composite (dignity / avastha / combustion / motion / shadbala / varga-spread)? Does the
DIGNITY component already span vargas (a varga dimension), or is the whole composite D1? (This sizes the
per-varga dignity expansion — we add varga-dignity, leave combustion/avastha/motion D1.)

**Q7 — Transit natal anchors (ga_transit_anchors): what does it hold?**
`\d` the transit-anchors table + `SELECT * ... WHERE chart_id=:c LIMIT 5`. What natal points are stored as
anchors (Moon sign/nakshatra, Lagna, grahas, sensitive points, Ashtakavarga bindu maps, Sade-Sati anchors)?
Confirm it stores ANCHORS only (small, per-chart, time-invariant), NOT transit positions over time.

**Q8 — Medical/Ayurvedic (bg_medical_mappings + ga_medical): what does it hold?**
`\d bg_medical_mappings` + sample rows; and the per-chart ga_medical table + sample rows. What mappings exist
(graha→dosha/dhatu/organ; sign/nakshatra/drekkana→body-part; house→health)? What does per-chart ga_medical
compute (dosha-balance, afflicted-parts, disease-yogas)? Show actual rows.

---

**Deliverable:** the report file with all 8 answers grounded in real query output. Flag the three ⭐ sizing
answers prominently (Q3 strength varga-coverage, Q4 sensitive-points present/missing diff, Q6 dignity
varga-coverage) — they directly size the L1 enrichment amendments. No changes to any data or schema.
