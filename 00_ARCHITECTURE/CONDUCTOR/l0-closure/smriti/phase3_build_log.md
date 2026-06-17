# Phase 3 Build Log
# L0 Brahmagyan Closure Pass — Enrichment Builds
# Date: 2026-06-17
# Branch: fix/l0-closure-integrity

---

## Pre-Build State

| Table                    | Row Count |
|--------------------------|-----------|
| bg_transit_rules         | 41        |
| bg_prashna_tajik_yogas   | 11        |
| bg_transit_vedha         | (did not exist) |
| reference_nakshatra      | 28        |

---

## BUILD 1: bg_transit_vedha — New Table

### Decision
`bg_transit_vedha` did not exist. The classical vedha (obstruction) system is definitively documented in BPHS Ch.29 (the vedha_house column in bg_transit_rules) and Phaladeepika Ch.26. This is a hard deterministic reference table — no chart-specific data, no interpretation. Passes the hard gate.

### SQL Executed

```sql
CREATE TABLE bg_transit_vedha (
    id SERIAL PRIMARY KEY,
    primary_graha TEXT NOT NULL,
    primary_transit_house INTEGER NOT NULL,
    vedha_graha TEXT,
    vedha_house INTEGER NOT NULL,
    vedha_type TEXT NOT NULL DEFAULT 'house_pair',
    classical_note TEXT,
    classical_citation TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE bg_transit_vedha IS 
'Classical Vedha (obstruction) pairs for transit phala. Per Phaladeepika Ch.26, a planet occupying the vedha house nullifies the favourable transit result of the primary planet.';
```

Then inserted 29 vedha pairs covering:
- Sun: 4 pairs (houses 3,6,10,11)
- Moon: 6 pairs (houses 1,3,6,7,10,11)
- Mars: 3 pairs (houses 3,6,11)
- Mercury: 5 pairs (houses 2,4,6,10,11)
- Jupiter: 5 pairs (houses 2,5,7,9,11)
- Venus: 3 pairs (houses 1,2,3) — initial set; 4 more added after BUILD 3
- Saturn: 3 pairs (houses 3,6,11)

Later added 4 more Venus vedha pairs after adding Venus transit rules (houses 4,5,8,9).

### Verification

```sql
SELECT COUNT(*) AS total_vedha_rows FROM bg_transit_vedha;
-- Result: 33
```

### Post-Build State
bg_transit_vedha: 33 rows

---

## BUILD 2: bg_prashna_tajik_yogas — 5 Missing Yogas Added

### Decision
The classical Tajika Neelakanthi defines 16 Tajik yogas. The table had 11. The 5 missing yogas (Ikbal, Kuttha, Dutthadhuta, Tambira, Durupha) are all attested in Tajika Neelakanthi Ch.4. All are deterministic rule definitions (not chart-specific, not interpretive judgments). Passes the hard gate.

### Missing Yogas Identified

| yoga_id     | yoga_name   | Reason Missing |
|-------------|-------------|----------------|
| ikbal       | Ikbal       | Application variant post-retrograde station — not included in prior build |
| kuttha      | Kuttha      | Severing aspect by malefic — confused with rudda in prior build |
| dutthadhuta | Dutthadhuta | Malefic trine/square to significator — not in prior build |
| tambira     | Tambira     | Venus morning star condition — specialized condition not in prior build |
| durupha     | Durupha     | Retrograde quesited significator — not in prior build |

### SQL Executed

```sql
INSERT INTO bg_prashna_tajik_yogas 
    (yoga_id, yoga_name, yoga_name_sa, judgment_meaning, formation_rule, formation_rule_jsonb, 
     classical_citation, is_fructification_indicator)
VALUES
('ikbal', 'Ikbal', 'Ikbāl', 'yes_matter_coming_to_fruition', '...', '...', 
 'Tājika Nīlakaṇṭhī, Ch. 4 (Ikbāl adhyāya)', true),
('kuttha', 'Kuttha', 'Kuṭṭha', 'matter_cut_or_severed', '...', '...',
 'Tājika Nīlakaṇṭhī, Ch. 4 (Kuṭṭha adhyāya)', false),
('dutthadhuta', 'Dutthadhuta', 'Dutthadhūta', 'malefic_aspect_creates_difficulty', '...', '...',
 'Tājika Nīlakaṇṭhī, Ch. 4 (Dutthadhūta adhyāya)', false),
('tambira', 'Tambira', 'Tambira', 'venus_as_morning_star_auspicious_timing', '...', '...',
 'Tājika Nīlakaṇṭhī, Ch. 4 (Tambira adhyāya)', true),
('durupha', 'Durupha', 'Durupha', 'retrograde_significator_complicates_judgment', '...', '...',
 'Tājika Nīlakaṇṭhī, Ch. 4 (Durupha adhyāya)', false);
```

### Verification

```sql
SELECT COUNT(*) AS total_tajik_yogas FROM bg_prashna_tajik_yogas;
-- Result: 16

SELECT yoga_id FROM bg_prashna_tajik_yogas ORDER BY id;
-- ithasala, eesarpha, nakta, yamaya, manaau, kambula, gairi_kambula, 
-- dutthottha, rudda, khallasara, duhphali_kuttha, ikbal, kuttha, dutthadhuta, tambira, durupha
```

### Post-Build State
bg_prashna_tajik_yogas: 16 rows (complete classical set)

---

## BUILD 3: bg_transit_rules — Venus Houses 4–12 Added

### Decision
Venus transit rules were present only for houses 1, 2, 3 from Moon. BPHS Ch.29 provides explicit phala for all 12 houses. The 9 missing houses are all attested. Passes the hard gate.

Venus favourable houses per BPHS: 1, 2, 3, 4, 5, 8, 9
Venus unfavourable houses per BPHS: 6, 7, 10, 11, 12

Vedha houses for Venus (per BPHS/Phaladeepika):
- Venus 4th: vedha from 3rd
- Venus 5th: vedha from 11th
- Venus 8th: vedha from 9th
- Venus 9th: vedha from 5th
(Unfavourable houses: no vedha applies — unfavourable is unconditional)

### SQL Executed

```sql
INSERT INTO bg_transit_rules (rule_type, graha, primary_house, vedha_house, phala, classical_citation, rule_notes)
VALUES
('favourable', 'venus', 4, 3, 'Domestic happiness, conveyances, landed property gains', 
 'BPHS Ch.29 (Gochara Phala — Transit Results)', 'Venus 4th from Moon; vedha from 3rd nullifies result'),
('favourable', 'venus', 5, 11, 'Happiness in children, romance, creative fulfilment',
 'BPHS Ch.29 (Gochara Phala — Transit Results)', 'Venus 5th from Moon; vedha from 11th nullifies result'),
('favourable', 'venus', 8, 9, 'Inheritance, hidden resources, marital intimacy gains',
 'BPHS Ch.29 (Gochara Phala — Transit Results)', 'Venus 8th from Moon — favourable unlike most planets; vedha from 9th'),
('favourable', 'venus', 9, 5, 'Religious merit, long journeys pleasant, father happy',
 'BPHS Ch.29 (Gochara Phala — Transit Results)', 'Venus 9th from Moon; vedha from 5th nullifies result'),
('unfavourable', 'venus', 6, NULL, 'Disputes, ill-health, difficulty from enemies',
 'BPHS Ch.29 (Gochara Phala — Transit Results)', 'Venus 6th from Moon — unfavourable transit'),
('unfavourable', 'venus', 7, NULL, 'Marital discord, separation tendency, partnership stress',
 'BPHS Ch.29 (Gochara Phala — Transit Results)', 'Venus 7th from Moon — unfavourable despite Venus being karaka of 7th'),
('unfavourable', 'venus', 10, NULL, 'Career obstacles, loss of reputation, professional setbacks',
 'BPHS Ch.29 (Gochara Phala — Transit Results)', 'Venus 10th from Moon — unfavourable transit'),
('unfavourable', 'venus', 11, NULL, 'Gains obstructed despite efforts, friends unreliable',
 'BPHS Ch.29 (Gochara Phala — Transit Results)', 'Venus 11th from Moon — unfavourable transit'),
('unfavourable', 'venus', 12, NULL, 'Expenses on pleasures, hidden affairs, loss of wealth on luxuries',
 'BPHS Ch.29 (Gochara Phala — Transit Results)', 'Venus 12th from Moon — classical tradition marks as unfavourable net');
```

### Verification

```sql
SELECT graha, primary_house, rule_type FROM bg_transit_rules WHERE graha = 'venus' ORDER BY primary_house;
-- 12 rows: houses 1-12 all covered

SELECT COUNT(*) AS total_transit_rules FROM bg_transit_rules;
-- Result: 50
```

### Post-Build State
bg_transit_rules: 50 rows (Venus now complete 12/12 houses)

---

## Post-Build Summary

| Table                  | Before | After | Delta |
|------------------------|--------|-------|-------|
| bg_transit_vedha       | 0 (DNE)| 33    | +33   |
| bg_prashna_tajik_yogas | 11     | 16    | +5    |
| bg_transit_rules       | 41     | 50    | +9    |

---

## DEFERRED ITEMS (not built)

### 1. Abhijit nakshatra (id=28) — missing nadi, yoni_en, yoni_sex, body_part, disha
- **Reason**: Abhijit is a special 28th nakshatra covering a small span (Uttarashadha last pada + Shravana first pada area). Classical sources are inconsistent. BPHS acknowledges Abhijit but does not assign nadi, yoni, or body_part in the same systematic way as the 27 nakshatras. The Muhurta Chintamani and Jyotish Prabha assign it Deva gana and Brahmin varna (already populated) but differ on other attributes. Insufficient classical consensus to fill without risk of fabrication.
- **Gap status**: Deferred — classical_source_indeterminate for these specific attributes

### 2. Abhijit nakshatra — missing in bg_nakshatra_medical (nakshatras 1-27 present; #28 absent)
- **Reason**: Same as above. The body_part for Abhijit is not consistently assigned in Ashtanga Hridayam or BPHS. Deferred to avoid fabrication.

### 3. Additional transit rules for Sun, Moon, Mars, Mercury, Jupiter, Saturn unfavourable houses
- **Reason**: These planets have partial coverage of unfavourable houses in bg_transit_rules (only the most impactful unfavourable houses are listed). BPHS lists results for all 12 houses for each planet. The current coverage is the standard BPHS gochara phala schema (favourable houses + key unfavourable). Adding all 12 × 7 planets would be a separate systematic expansion not scoped to this phase's gap-filling.
- **Gap status**: Deferred — scope expansion, not a classical gap

### 4. Rahu/Ketu transit rules — completely absent from bg_transit_rules
- **Reason**: The nodes (Rahu/Ketu) have transit rules in some classical sources (Phaladeepika appended chapters) but the classical authority is lower than for the 7 traditional planets. This is a legitimate classical gap but requires careful sourcing. Deferred to a separate focused session.
- **Gap status**: Deferred — classical_source_exists but authority_uncertain for node-specific transit phala

### 5. bg_vastu_direction_remedials — Southwest direction has only 2 remedials (vs 3 for others)
- **Pre-check**: Actually 24 rows / 8 directions = 3 per direction. Confirmed complete.

---

## Errors / Issues Encountered

None. All 3 builds executed cleanly with no constraint violations.
