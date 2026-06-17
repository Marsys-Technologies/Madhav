---
canonical_id: L0_SYNERGY_REGISTER
version: "1.0"
status: CURRENT
created: 2026-06-17
author: Claude Code — Phase 4 L0 Closure Pass
branch: fix/l0-closure-integrity
migration_applied: 304_bg_graha_dik.sql
---

# L0 Synergy Register v1.0

Cross-asset synergy analysis for the L0 Brahmagyan layer.
Produced by Phase 4 of the L0 Brahmagyan Closure Pass.

Layer classification rule (absolute):
- STATIC + chart-agnostic → L0 (built here)
- Depends on A SPECIFIC CHART → L1 (logged only)
- Interpretive RELATIONSHIP / synthesis → L2 Bodha (logged only)

---

## §1 L0 Static Synergies BUILT

### SYN-L0-001: bg_graha_dik — Dig Bala Directional Strength Reference

| Field | Value |
|---|---|
| Table | `bg_graha_dik` |
| Rows built | 9 |
| Migration | `platform/migrations/304_bg_graha_dik.sql` |
| Applied | 2026-06-17 |
| Classical source | BPHS Ch.27 (Digbala); Saravali Ch.3 v.10; Brihat Jataka Ch.2 |
| School | parashari (7 grahas); tajika (Rahu); debated (Ketu) |

**What it provides:**
Each graha's peak directional strength house (Dig Bala), the corresponding cardinal direction, and the debility house (opposite). Includes paired graha (where BPHS specifies two grahas sharing a peak house) and a `school_note` column distinguishing universally attested (parashari), Tajika-school (rahu), and debated (ketu) assignments.

**Why it is L0 (not already present):**
- `reference_planets` has no direction or Dig Bala field
- `bg_vastu_directions` maps direction→ruling_graha (inverted, Vastu Shastra framework, Ketu absent)
- `ga_vastu_planet_direction_map` is L1 — chart-keyed with `chart_id`
- The Dig Bala mapping (graha→peak_house) is an immutable classical rule, chart-agnostic, required as static reference for L1 writers computing Dig Bala scores

**Schema:**
```sql
bg_graha_dik(
  id              SERIAL PRIMARY KEY,
  graha           TEXT NOT NULL UNIQUE,
  peak_house      SMALLINT NOT NULL,    -- 1/4/7/10
  peak_direction  TEXT NOT NULL,        -- East/North/South/West
  debility_house  SMALLINT NOT NULL,    -- 180 deg opposite
  paired_graha    TEXT,                 -- shares same peak house
  school_note     TEXT,                 -- parashari|tajika|debated
  classical_citation TEXT NOT NULL,
  created_at      TIMESTAMPTZ
)
```

**Row summary:**

| graha | peak_house | peak_direction | debility_house | school_note |
|---|---|---|---|---|
| sun | 10 | South | 4 | parashari |
| moon | 4 | North | 10 | parashari |
| mars | 10 | South | 4 | parashari |
| mercury | 1 | East | 7 | parashari |
| jupiter | 1 | East | 7 | parashari |
| venus | 4 | North | 10 | parashari |
| saturn | 7 | West | 1 | parashari |
| rahu | 7 | West | 1 | tajika |
| ketu | 4 | North | 10 | debated |

---

## §2 L1 Opportunity Register

These synergies are chart-dependent and should be addressed by L1 writers or L1 query-layer logic.

### L1-OPP-001: Dignity × Transit Rules cross-reference

**Description:** Cross-reference bg_dignity_reference with bg_transit_rules to produce "for a graha in dignity state X transiting house Y, what is the modified phala?" The phala in bg_transit_rules is the BASE result; dignity modulates it. This requires knowing the graha's current longitude (chart-specific at L1 transit time).

**Relevant tables:** `bg_dignity_reference`, `bg_transit_rules`, `bg_transit_vedha`

**Consuming writer:** ga_transit_anchors or a future ga_transit_dignity writer

**Why not L0:** Dignity state of a graha at a specific transit moment is chart+time-dependent.

---

### L1-OPP-002: Nakshatra→Dhatu chain for chart placements

**Description:** For each L1 chart planet placement, derive: planet's nakshatra → nakshatra.vimshottari_lord → bg_medical_mappings.dhatu. Produces a chart-specific graha-dhatu-nakshatra triad.

**Relevant tables:** `reference_nakshatra`, `bg_medical_mappings`, `chart_facts`

**Why not L0:** Requires knowing which nakshatra a specific chart's planets occupy.

---

## §3 L2 Bodha Opportunity Register

These synergies are interpretive and belong in the L2 Bodha layer (bo_* assets).

### L2-OPP-001: Yoga × Dosha Conflict / Cancellation Pairs

**Description:** Identify yoga-dosha pairs where a yoga's formation cancels or intensifies a dosha (e.g., Neechabhanga cancels debilitation dosha; Kala Sarpa may be cancelled by certain exaltations). Requires interpretive synthesis of both yoga conditions and dosha conditions in context of a chart.

**Relevant tables:** `brahma_yoga_catalog`, `brahma_dosha_catalog`, `ga_yoga_firings`

**Target asset:** bo_sangati (the synthesis/cross-reference Bodha asset)

---

### L2-OPP-002: Nakshatra-Specific Remedy Recommendations

**Description:** Recommend remedies based on chart nakshatra placements (Moon nakshatra, Lagna nakshatra, etc.). Application is chart-specific. A static nakshatra-remedy table COULD be built at L0 if classical sources exist (Muhurta Chintamani etc.) but the current brahma_remedy_corpus only supports planet-level remedies.

**Relevant tables:** `brahma_remedy_corpus`, `reference_nakshatra`, `chart_facts`

**Target asset:** bo_upaya (the remedy Bodha asset)

**Note for future L0 consideration:** If a classical source for nakshatra-specific remedies is identified (e.g., Muhurta Chintamani Ch.8), a static `bg_nakshatra_remedy` table could be built at L0. Currently deferred.

---

### L2-OPP-003: Dosha × Remedy Cross-Reference Population

**Description:** brahma_dosha_catalog.associated_remedies[] is currently empty for all doshas. Populating this with specific remedy IDs from brahma_remedy_corpus requires classical research on which remedies address which doshas, AND the application is chart-specific (which dosha is activated for this native?).

**Relevant tables:** `brahma_dosha_catalog`, `brahma_remedy_corpus`

**Target asset:** bo_upaya or bo_pramana_mapa

---

### L2-OPP-004: Medical-Graha-Nakshatra Synthesis

**Description:** For a given chart, synthesize the medical picture from: (a) graha placements → bg_medical_mappings → dhatu/dosha, (b) nakshatra placements → bg_nakshatra_medical → body parts, (c) afflictions from chart_facts. The synthesis is the L2 signal.

**Relevant tables:** `bg_medical_mappings`, `bg_nakshatra_medical`, `reference_nakshatra`, `chart_facts`

**Target asset:** bo_laksana or a specialized medical signal in bo_bimba

---

## §4 Structural Recommendations (Requiring Native Sign-Off)

### REC-001: Unified Directional Authority

**Issue:** Three separate static tables cover "graha + direction" from different frameworks:
1. `bg_vastu_directions` — direction→ruling_graha (Vastu Shastra; 8 directions, Ketu absent)
2. `reference_nakshatra.disha` — nakshatra→direction (27 nakshatras)
3. `bg_graha_dik` (NEW Phase 4) — graha→Dig Bala peak house/direction (9 grahas)

These are complementary, not redundant, but can create confusion for query writers. Recommend:
- A governance note clarifying which table to use for which query type
- OR a combined `bg_graha_direction_authority` view that surfaces all three frameworks with a `framework` discriminator column

**Sign-off needed:** Does the native want a unified view, or is the current three-table split acceptable?

---

### REC-002: Transit Table Consolidation (View)

**Issue:** `bg_transit_rules` (50 rows) and `bg_transit_vedha` (33 rows) are complementary but separate. For the 33 favourable transit houses, a natural join is available. For the 17 unfavourable rows, vedha doesn't apply.

**Recommendation:** Create a database VIEW:
```sql
CREATE VIEW bg_transit_combined AS
SELECT
    r.graha,
    r.rule_type,
    r.primary_house,
    r.phala,
    r.classical_citation as rule_citation,
    v.vedha_house,
    v.classical_note as vedha_note,
    v.classical_citation as vedha_citation
FROM bg_transit_rules r
LEFT JOIN bg_transit_vedha v
    ON r.graha = v.primary_graha
   AND r.primary_house = v.primary_transit_house
   AND r.vedha_house = v.vedha_house;
```
This avoids data duplication while providing a convenient query surface.

**Sign-off needed:** Approve creating this VIEW in a dedicated migration (305).

---

### REC-003: brahma_dosha_catalog.associated_remedies Population

**Issue:** The `associated_remedies` array is empty for all dosha entries. This field was designed to point to brahma_remedy_corpus IDs. A data-population task is needed before L2 Bodha can use this field.

**Action needed:** Classical research + data entry task to populate dosha-specific remedy references. This is a DATA task, not a schema task.

**Sign-off needed:** Should this be a standalone session task before L2 Bodha opens?

---

### REC-004: bg_nakshatra_medical vs reference_nakshatra.body_part

**Issue:** Both tables contain nakshatra→body_part data from the same classical sources (Ashtanga Hridayam/BPHS). The values differ slightly (e.g., Ashwini: bg_nakshatra_medical says "feet/knees", reference_nakshatra says "head"). This is a data inconsistency.

**Action needed:** Audit which source is correct per classical reference, standardize, and consider whether bg_nakshatra_medical should be deprecated in favor of reference_nakshatra.body_part.

**Sign-off needed:** Which body_part data is authoritative?

---

## §5 Layer-Classification Notes

### Note 1: Dig Bala (bg_graha_dik) as L0 vs. L1

Dig Bala as a RULE (which house a graha peaks in) is L0-static — it never changes.
Dig Bala as a SCORE for a specific chart (how much Dig Bala does THIS chart's Saturn have?) is L1 — requires knowing Saturn's house placement in the chart.

The bg_graha_dik table built here is correctly L0: it stores the RULE, not the score.

### Note 2: bg_transit_vedha "no vedha_graha" rows

The current bg_transit_vedha schema has `vedha_graha` column but it is NULL for all 33 rows (vedha_type = 'house_pair'). Vedha is house-based (any planet transiting the vedha house blocks the benefit), not planet-specific. This is correct per classical interpretation (BPHS Ch.29).

### Note 3: Rahu/Ketu in bg_vastu_directions

bg_vastu_directions has 8 rows (8 Vastu directions) with Rahu at Southwest. Ketu is absent from bg_vastu_directions because in classical Vastu Shastra, Ketu does not have a dedicated directional rulership (it shares or is excluded). The bg_graha_dik table includes Ketu with `school_note = 'debated'` to be honest about the uncertainty.

### Note 4: classical_attributions not yoga_id linked

The classical_attributions table uses free-text topic_id values (e.g., 'career_general') rather than foreign keys to yoga or dosha canonical_ids. This means yoga-level classical source attribution must go through brahma_yoga_catalog.classical_citations (jsonb) rather than through classical_attributions. This limits the utility of classical_attributions for yoga-specific provenance. Future schema enhancement could add a `yoga_id` column.
