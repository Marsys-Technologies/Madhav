---
title: Phase 4 Synergy Hunt — Raw Analysis
session: L0 Closure Pass Phase 4
date: 2026-06-17
analyst: Claude Code (agent-ae410d622014c5fb1)
---

# Phase 4 Analysis: Cross-Asset Synergy Investigation

## 1. Schema Inventory

### reference_nakshatra (46 columns)
Key columns for synergy analysis:
- `nakshatra_id` (smallint), `name_en`, `vimshottari_lord` (text), `disha` (text)
- `presiding_deity`, `secondary_deities`, `deity_domain`
- `body_part`, `gana`, `nadi`, `yoni_en`, `varna`, `tatva`, `guna`
- `ruling_planet`, `shakti`, `motivation`
- `is_gandanta`, `is_mula_sangya`, `is_panchaka`, `is_abhijit`

**CRITICAL FINDING:** `vimshottari_lord` already present for all 27 nakshatras (and Abhijit=sun). `disha` also present for all 27 (Abhijit has null disha). This eliminates Candidates H entirely.

### bg_medical_mappings (8 columns)
`id, graha, dosha[], dhatu[], organ_systems[], body_part[], disease_tendency[], classical_citation`
Planet-keyed (7 planets). Covers Ayurvedic graha-body mapping.

### bg_nakshatra_medical (5 columns)
`id, nakshatra_name, nakshatra_number, body_part, classical_citation`
Nakshatra-keyed. 27 rows covering body part per nakshatra.

**FINDING:** reference_nakshatra.body_part ALSO contains body part. bg_nakshatra_medical is a separate table with the same data in a more structured form. No new bridge table needed for A.

### bg_dignity_reference (12 columns)
`id, graha, exaltation_sign/degree, debilitation_sign/degree, moolatrikona_sign/from/to, own_signs[], classical_citation, notes`
Dignity data — chart-agnostic but used in chart-specific L1 computations.

### bg_graha_naisargika_friendship (5 columns)
`id, graha, other_graha, relation, classical_citation`
72 rows (9×8 pairs). Full naisargika friendship table. No gaps found.

### reference_planets (14 columns)
`id(uuid), planet_id, canonical_name_en/sa, exaltation_sign/degree, debilitation_sign, mooltrikona_sign, own_signs[], natural_benefic, karak_domains[], dasha_years, source_citation`
**FINDING:** NO direction/dik field in reference_planets. This confirms the gap.

### bg_vastu_directions (8 columns)
`id, direction, direction_deg, ruling_graha, secondary_graha, element, favorable_color, classical_citation`
8 rows (8 directions). ruling_graha present, but only 8 directions × planet doesn't give a clean graha→direction lookup because:
- Jupiter → Northeast (not a cardinal)
- Ketu → NOT in bg_vastu_directions (only 8 rows: N/S/E/W + 4 intercardinals)
- The table maps direction→graha, NOT graha→direction(+peak_house)

### brahma_remedy_corpus (26 columns)
`remedy_id, planet, domain, remedy_type, prescription_text, mantra_text, gemstone, charity_action, day_of_week, color_associated, confidence, source_canonical_id, source_citation, classical_ref, category, deity, mantra_sanskrit, mantra_transliteration, ingredients_jsonb, timing_rules_jsonb, cost_tier, contraindications, classical_attestation_text, scaffold_status`
**FINDING:** `planet`-keyed only. No `nakshatra` column. No `entity_type` column (contrary to original task prompt — that column doesn't exist). Remedy corpus covers 7 traditional grahas (Sun through Rahu/Ketu via planet field). No nakshatra-specific remedies stored.

### brahma_yoga_catalog (19 columns)
Complex: `canonical_id, name_sa/en, category, formation_rule_jsonb, significations_jsonb, cancellation_conditions, classical_citations, source_chunk_ids, school, rare, bhanga_rules_jsonb, partial_formation_threshold, result_class`
No inherent dosha link columns. Cross-linking would be interpretive.

### brahma_dosha_catalog (14 columns)
`canonical_id, name_sa/en, category, formation_rule_jsonb, effects_text, severity_grades, cancellation_conditions, classical_citations, source_chunk_ids, associated_remedies[], school`
`associated_remedies` is an empty array in current data. Dosha→remedy cross-ref not yet populated.

### bg_vastu_direction_remedials (5 columns)
`id, direction, remedy_type, remedy_description, classical_citation`
Direction-keyed remedials. Pure Vastu reference.

### bg_transit_vedha (9 columns)
`id, primary_graha, primary_transit_house, vedha_graha, vedha_house, vedha_type, classical_note, classical_citation, created_at`
33 rows (favorable house pairs only — the houses that CAN be blocked by vedha).

### bg_transit_rules (8 columns)
`id, rule_type, graha, primary_house, vedha_house, phala, classical_citation, rule_notes`
50 rows (33 favourable + 17 unfavourable). Unfavourable rules don't have vedha_house (NULL).
JOIN confirmed: `bg_transit_rules JOIN bg_transit_vedha ON (graha, primary_house, vedha_house)` — works for favourable rows.

### brahma_dasha_systems (14 columns)
`canonical_id, name_sa/en, total_cycle_years, base_unit, sequence_jsonb, computation_method, computation_pseudocode, conditions_for_use, school, classical_citations, source_chunk_ids, python_impl_module`
Contains full dasha sequence embedded in sequence_jsonb. No separate graha-sequence table needed.

### classical_attributions (11 columns)
`attribution_id, topic_id, topic_canonical_name, topic_category, school, source_text_ids[], source_chunk_ids[], rule_ids[], match_method, match_confidence`
Topic-keyed (not yoga_id or dosha_id). Acts as a classical source attribution table. No direct yoga→attribution join without topic_id alignment.

### ga_vastu_planet_direction_map (11 columns)
`id, chart_id, ayanamsha_id, graha, direction, condition_score, dignity_d1, direction_impact, indication_tier, classical_citation, computed_at`
**CRITICAL:** This table has `chart_id` — it is L1 (chart-specific). The direction data here is computed per-chart, NOT the static Vastu directional rulership.

## 2. Candidate Evaluations

### CANDIDATE A: nakshatra-deity × medical-body-part bridge

**Evaluation:**
- reference_nakshatra has: `presiding_deity`, `deity_domain`, `body_part`
- bg_nakshatra_medical has: `nakshatra_name`, `nakshatra_number`, `body_part`
- These two tables contain overlapping body_part data. A join between them adds no new information — both map nakshatra→body_part from the same classical source (Ashtanga Hridayam/BPHS).
- There is no deity→medical bridge that is distinct from what's in reference_nakshatra.deity_domain.

**Decision: NO BUILD.** Data already present. No unique cross-asset value.

---

### CANDIDATE B: dignity × transit rules

**Evaluation:**
- bg_dignity_reference = static graha dignity data
- bg_transit_rules = which house is favorable/unfavorable for transit
- Combining them requires knowing WHERE a specific graha IS (its dignity in a transit context). That requires knowing the current longitude and the natal chart.

**Decision: L1 OPPORTUNITY — LOG ONLY.** The cross-reference "which transit houses are favourable for a graha given its current dignity" is computed per-chart (or per-transit-date + chart). Not L0-static.

---

### CANDIDATE C: yoga × dosha conflict pairs

**Evaluation:**
- brahma_yoga_catalog and brahma_dosha_catalog both use formation_rule_jsonb
- Identifying which yogas cancel doshas (e.g. Neechabhanga canceling debilitation's dosha) requires interpretive synthesis
- This is textbook L2 Bodha material — the MSR/UCN signals would encode these relationships

**Decision: L2 BODHA OPPORTUNITY — LOG ONLY.**

---

### CANDIDATE D: bg_vastu_directions × reference_planets → graha direction bridge

**Evaluation:**
- bg_vastu_directions maps direction→ruling_graha (8 rows, Ketu absent)
- reference_planets has NO direction field
- ga_vastu_planet_direction_map IS chart-keyed (has chart_id = L1 artifact)
- The STATIC concept of graha→primary direction encompasses two related but distinct classical rules:
  (a) Vastu Shastra directional rulership (who rules each direction) — bg_vastu_directions covers this as direction→graha (inverted)
  (b) Dig Bala (Directional Strength) — which house/direction a graha's strength peaks — NOT in any table

**Key insight:** Dig Bala (BPHS Ch.27) is a foundational L0 static rule: Sun/Mars → 10H (South), Moon/Venus → 4H (North), Mercury/Jupiter → 1H (East), Saturn → 7H (West). This is universal, chart-agnostic, and missing from the DB.

**Decision: BUILD `bg_graha_dik` (Dig Bala directional strength reference).** 9 rows, static, classically attested.

Note: The Vastu direction→graha lookup (bg_vastu_directions) is the INVERSE of what would be needed for a graha→direction table, and it only covers 8/9 grahas (Ketu omitted). The bg_graha_dik table fills the Dig Bala gap specifically.

---

### CANDIDATE E: nakshatra × remedies

**Evaluation:**
- brahma_remedy_corpus has NO entity_type column (contrary to the task description — this column doesn't exist)
- brahma_remedy_corpus is keyed by `planet` field only
- Nakshatra-specific remedies (e.g., Ashwini nakshatra → offer coconut to Ashvini Kumaras) would require knowing WHICH nakshatra is prominent in a chart — a chart-dependent interpretation
- Even if a nakshatra-remedy static lookup table were built, the APPLICATION (which nakshatra matters for THIS native) is L1/L2

**Decision: L2 BODHA OPPORTUNITY — LOG ONLY.** A static nakshatra-remedy table could be built in the future as L0 reference IF a classical source exists. However, with the current remedy corpus keyed only to planets, no bridge is structurally possible without new data.

---

### CANDIDATE F: medical_mappings × nakshatra → dhatu chain

**Evaluation:**
- bg_medical_mappings maps graha→dhatu (e.g., Sun→asthi, Moon→rasa)
- bg_nakshatra_medical maps nakshatra→body_part
- A dhatu chain would be: nakshatra's ruling planet → that planet's dhatu. But this is:
  1. A derived computation (nakshatra.vimshottari_lord → bg_medical_mappings.dhatu), trivially joinable
  2. The APPLICATION to a specific chart requires knowing the chart's nakshatra placements → L1
  3. As a static table it would just redundantly encode nakshatra→lord→dhatu, which is derivable by JOIN

**Decision: L2 BODHA OPPORTUNITY (interpretive chain for specific chart analysis).** The pure join is trivially doable at query time; no table warranted.

---

### CANDIDATE G: bg_transit_vedha × bg_transit_rules → combined transit reference

**Evaluation:**
- bg_transit_rules: 50 rows (33 favourable + 17 unfavourable). Contains phala text.
- bg_transit_vedha: 33 rows. Contains vedha pair information + classical_note.
- JOIN works: `bg_transit_rules r JOIN bg_transit_vedha v ON r.graha=v.primary_graha AND r.primary_house=v.primary_transit_house AND r.vedha_house=v.vedha_house`
- The tables are COMPLEMENTARY (rules has phala text, vedha has classical_note text) but not redundant
- The 17 unfavourable rows in bg_transit_rules have NULL vedha_house — they don't have corresponding vedha entries (unfavourable houses have no vedha blockage concept)
- A combined view/table would be useful but creates maintenance duplication

**Decision: NO BUILD. Structural recommendation instead.** A database VIEW would serve all query needs without data duplication. Flag as Structural Recommendation §4.

---

### CANDIDATE H: nakshatra → Vimshottari dasha lord mapping

**Evaluation:**
- reference_nakshatra.vimshottari_lord is populated for ALL 28 entries (including Abhijit = sun)
- The data is fully present and correct (Ashwini=ketu, Bharani=venus, Krittika=sun... matches Vimshottari order)

**Decision: NO BUILD.** Data already present in reference_nakshatra.

---

### CANDIDATE I: yogas × concordance (classical_attributions)

**Evaluation:**
- classical_attributions is topic_id-keyed (e.g., 'career_general', 'arts_general')
- brahma_yoga_catalog has canonical_id (e.g., yoga names)
- No yoga_id link exists in classical_attributions; the join would require matching yoga names to topic_ids, which is imprecise and interpretive
- The classical_attributions table is an attribution of classical sources to TOPICS, not to specific yogas

**Decision: NO BUILD.** The linkage is too indirect. Structural recommendation: if yoga-specific classical concordance is needed, brahma_yoga_catalog.classical_citations jsonb already contains source references.

## 3. Additional Synergy Hunt

### bg_vastu_directions × reference_nakshatra → nakshatra directional affinity
- reference_nakshatra.disha is already populated for 27 nakshatras
- bg_vastu_directions.ruling_graha connects to reference_nakshatra.ruling_planet
- A three-way join (nakshatra → ruling_planet → vastu_direction) is trivially computed
- No new static table warranted; this is a query-time join

**Decision: NO BUILD.** Trivial at query time.

### brahma_dosha_catalog × brahma_remedy_corpus → dosha-specific remedies
- brahma_dosha_catalog.associated_remedies is currently an empty array for all doshas
- brahma_remedy_corpus has no dosha-specific column
- Populating this cross-reference requires classical research (which remedies specifically address which dosha) — this is DATA CONTENT, not a structural bridge
- AND applying it requires knowing which dosha is active in a specific chart → L1/L2

**Decision: L2 BODHA OPPORTUNITY.** The dosha-remedy cross-ref is inherently chart-application logic.

### bg_prashna_rules × reference_planets → prashna significator cross-reference
- bg_prashna_significators already has `querent_planet` and `quesited_planet` columns
- reference_planets provides canonical planet metadata
- A join is trivially possible at query time
- No new table warranted

**Decision: NO BUILD.** Query-time join sufficient.

## 4. Summary of Decisions

| Candidate | Description | Decision | Reason |
|---|---|---|---|
| A | nakshatra-deity × medical-body-part | NO BUILD | Data already in reference_nakshatra.body_part + bg_nakshatra_medical |
| B | dignity × transit rules | L1 LOG | Requires knowing transit chart position |
| C | yoga × dosha conflict | L2 LOG | Interpretive synthesis |
| D | graha direction bridge (Dig Bala) | **BUILT: bg_graha_dik** | Genuinely missing L0 static data |
| E | nakshatra × remedies | L2 LOG | Chart-dependent application |
| F | medical × nakshatra → dhatu chain | L2 LOG | Chart-dependent interpretation |
| G | transit_vedha × transit_rules combined | STRUCTURAL REC | View recommended, not table |
| H | nakshatra → Vimshottari dasha lord | NO BUILD | Already in reference_nakshatra.vimshottari_lord |
| I | yogas × classical concordance | NO BUILD | Too indirect; yoga.classical_citations already exists |
| ADD-1 | vastu_directions × nakshatra directional | NO BUILD | Trivial query-time join |
| ADD-2 | dosha × remedy cross-ref | L2 LOG | Chart-application dependent |
| ADD-3 | prashna_rules × reference_planets | NO BUILD | Trivial query-time join |

## 5. Notable Absence: Unified Graha-Direction Authority

The project has a fragmented directional picture:
- **bg_vastu_directions**: direction→ruling_graha (Vastu Shastra) — 8 rows, Ketu absent
- **ga_vastu_planet_direction_map**: chart_id-keyed (L1) — NOT static
- **reference_nakshatra.disha**: nakshatra-level direction (27 rows)
- **bg_graha_dik** (NEW): Dig Bala graha→peak_house+direction — 9 rows (this build)

These three static tables cover complementary aspects of the "graha and direction" domain but from different frameworks (Vastu rulership vs. Dig Bala vs. nakshatra disha). A NATIVE SIGN-OFF note is warranted on whether a unified directional authority table is desired.
