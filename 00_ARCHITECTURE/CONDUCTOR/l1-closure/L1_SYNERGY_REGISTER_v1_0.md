---
artifact: L1_SYNERGY_REGISTER_v1_0.md
canonical_id: L1_SYNERGY_REGISTER
version: 1.0
status: COMPLETE
phase: Phase 4 (Cross-Asset Synergy Hunt)
date: 2026-06-18
grounded_in: >
  asset_registry_seed.ts (10 registered ga_* assets),
  ga_structural_writer.py count_sql analysis,
  ga_condition_writer.py / ga_strength_writer.py / ga_vargas_writer.py (per_varga categories),
  L1_INTEGRITY_FINDINGS_v1_0.md (Phase 1 audit),
  L1_ENRICHMENT_REGISTER_v1_0.md (Phase 3),
  OPEN_ITEMS_REGISTER_v1_0.md (A0-2, A0-3, B6)
---

# L1 Synergy Register v1.0 — Cross-Asset Analysis

## Classification

- **BUG**: Correctness defect requiring immediate fix before L1 closure
- **GAP**: Missing coverage that reduces L1 completeness; fix before or during closure
- **SYNERGY**: Cross-asset relationship opportunity — value for L2 Bodha; record, act later
- **ARCH**: Architectural pattern established by this enrichment that L2 should inherit

Findings ordered: BUGs first (blocking), then GAPSs, then SYNERGYs and ARCHs.

---

## BUG-1 — ga_structural count_sql sweeps enrichment-added per_varga rows (COCKPIT INFLATION)

**Severity: HIGH — blocker for L1 closure**

The B12 fix (migration 308) removed `graha_position` and `graha_sign_attributes` from ga_structural count_sql. But two LIKE patterns in that count_sql now sweep rows written by other enrichment assets:

**Pattern 1: `fact_category LIKE 'graha_avastha_%'`**
- Written by ga_structural_writer: `graha_avastha_baladi`, `graha_avastha_deeptaadi`, `graha_avastha_jagradadi`, `graha_avastha_sayanadi`, `graha_avastha_lajjitadi` (D1, 5 categories × 9 × 5 = 225 rows)
- ALSO matched (written by ga_condition_writer): `graha_avastha_baladi_per_varga`, `graha_avastha_deeptaadi_per_varga`, `graha_avastha_jagradadi_per_varga`, `graha_avastha_sayanadi_per_varga`, `graha_avastha_lajjitadi_per_varga` (per-varga, 5 categories × 9 × 30+ vargas × 5 = ~6,750 rows)
- Impact: ga_structural count_sql counts ~6,750 ga_condition rows as its own

**Pattern 2: `fact_category LIKE '%_per_varga'`**
- Written by ga_structural_writer: NONE (ga_structural does not write `*_per_varga` rows)
- Matches ga_strength rows: `ashtakavarga_bindu_per_varga`, `ashtakavarga_pinda_sarva_per_varga`, `graha_sthana_bala_per_varga`, `graha_drik_bala_per_varga`, `graha_kala_bala_per_varga`, `graha_cheshta_bala_per_varga` (~8,180 rows)
- Matches ga_condition rows: same 5 avastha_*_per_varga categories (~6,750 rows)
- Matches ga_vargas rows: `graha_dignity_per_varga` in chart_divisionals — does NOT affect count_sql (chart_divisionals vs chart_facts; count_sql queries chart_facts only) ✓
- Impact: ga_structural count_sql counts ~14,930 rows it did not write

**Pattern 3: `nakshatra_pada_sensitive` in both ga_structural IN clause AND ga_sensitive count_sql**
- Per migration 307 comment: nakshatra_pada_sensitive = 80 rows present in prod; written by ga_structural_writer (in its original fact family). Added to ga_sensitive count_sql in migration 307 to fix a missed coverage gap.
- Result: 80 rows double-counted between ga_structural and ga_sensitive in the cockpit.

**Total over-count in ga_structural count_sql after enrichment: ~15,010 extra rows**
This means the 87,169 floor (set before enrichment) is actually ~72,159 ga_structural-owned rows + ~15,010 over-counted enrichment rows. The floor and count_sql are internally inconsistent.

**Fix required (migration 309):**
Tighten ga_structural count_sql to EXCLUDE per_varga subcategories:
```sql
-- Replace:  fact_category LIKE 'graha_avastha_%'
-- With:     fact_category LIKE 'graha_avastha_%' AND fact_category NOT LIKE '%_per_varga'

-- Replace:  fact_category LIKE '%_per_varga'
-- With:     DELETE THIS LINE (ga_structural writes no _per_varga rows)

-- Remove:   'nakshatra_pada_sensitive' from ga_structural IN clause
--           (written by ga_structural_writer, but also in ga_sensitive count_sql → remove from one)
--           Recommend: keep in ga_structural (writer owns it); remove from ga_sensitive
```

Then re-run count_sql on prod and set floor to the new, tighter count.

**Status: OPEN — migration 309 needed before L1 closure seal.**

---

## BUG-2 — ga_strength count_sql overlaps ga_structural on graha_avastha_baladi_per_varga etc.

**Severity: MEDIUM — cockpit double-count, not a data integrity bug**

After enrichment:
- ga_strength count_sql: `fact_category LIKE 'graha_%_bala_per_varga'` matches `graha_sthana_bala_per_varga`, `graha_drik_bala_per_varga`, `graha_kala_bala_per_varga`, `graha_cheshta_bala_per_varga` ✓ (correct — these are written by ga_strength_writer)
- ga_structural count_sql: `fact_category LIKE '%_per_varga'` also matches those same 4 categories
- Result: ~3,780 rows (4 categories × 9 grahas × 21 vargas × 5 ay) double-counted

**Fix:** Resolved by BUG-1 fix (removing `%_per_varga` from ga_structural count_sql).

---

## GAP-1 — 5 writers built but not registered in asset_registry (cockpit blind spots)

**Severity: HIGH — cockpit shows no row count for 5 live writers**

Writers confirmed active (have @register decorator and actual rows on prod) but absent from `asset_registry_seed.ts`:
- `ga_condition` — per-chart graha condition composites + per-varga avasthas (Amendment 2); substantial output
- `ga_yoga` — Nabhasa yoga classifications (5 rows for 482012f1)
- `ga_vastu` — Vastu chart facts (40 rows for 482012f1)
- `ga_medical` — Medical astrology facts (45 rows for 482012f1)
- `ga_prashna` — Prashna (horary) chart; 0 correct rows in prod (needs investigation)

**Impact:** The orchestrator runs all 5 writers (they build rows) but the cockpit shows no count, no status, no floor check for any of them. This is a hidden L1 blind spot.

**Fix:** Add asset_registry entries for all 5 in `asset_registry_seed.ts` + migration 309 (or 310). At minimum: asset_id, layer='ganita', catalog_status='CURRENT', count_sql per asset, target_floor = achieved count, depends_on. For ga_prashna: catalog_status='INVESTIGATION' or target_floor=0 until the 0-row root cause is resolved.

**Reference:** Phase 1 audit WARN-B1 (open items A0-1). Observation 20913.

---

## GAP-2 — ga_condition.target_floor not set in migration 307

**Severity: MEDIUM — will misfire cockpit floor check**

Migration 307 set floors for ga_strength (11,936) and ga_sensitive (8,610) but NOT ga_condition (Amendment 2 asset). Even if ga_condition were registered (which it isn't — see GAP-1), its floor is unset.

**Fix:** Set after prod build. Expected: ~5 avastha categories (2 built + 3 floored) × 9 grahas × 30 vargas × 5 ayanamshas = ~6,750 rows for per-varga + D1 avastha rows. Run `SELECT count(*) FROM chart_facts WHERE chart_id='482012f1-...' AND fact_category LIKE 'graha_avastha_%'` post-build.

---

## GAP-3 — ga_structural target_floor of 87,169 is wrong after BUG-1 fix

**Severity: HIGH — floor must be reset after count_sql is tightened**

The 87,169 floor was set when the count_sql still included the broad `graha_avastha_%` and `%_per_varga` patterns. After BUG-1 fix (tightened count_sql), the correct floor will be ~72,000 (rough: 87,169 − ~15,010 over-count). Must be re-verified with a live DB count using the corrected count_sql.

---

## GAP-4 — ga_prashna has 0 correct rows — root cause not investigated

**Severity: MEDIUM — silent gap in L1 coverage**

Phase 1 audit confirmed ga_prashna = 0 rows on prod for chart 482012f1. No investigation was done. For a natal chart, ga_prashna may be intentionally empty (prashna = horary, not natal). Or it may be a writer bug. Either way, it needs a documented ruling:
- If intentionally empty for natal: add asset_registry entry with `catalog_status='INTENTIONALLY_EMPTY_FOR_NATAL'` and comment
- If bug: fix and rebuild

---

## SYNERGY-1 — ga_sade_sati × ga_dashas — dasha confluence unlinked

ga_sade_sati has a `sade_sati_concurrent_dasha_overlay` category that describes which dasha lords are active during each Sade Sati phase. This category SHOULD reference the specific `chart_dashas` rows (MD/AD/PD) by their fact_ids — but it currently produces textual overlays without formal citations.

**L2 opportunity:** When bo_laksana (MSR signals) ingests `sade_sati_concurrent_dasha_overlay`, it should link to the relevant `chart_dashas` rows by their PKs. This enables L2 to reason: "during this Sade Sati phase, the native was in Mars MD / Rahu AD — historically the toughest confluence."

**For L1 closure:** Add a `constituent_facts_array` or `citation_ref` from each `sade_sati_concurrent_dasha_overlay` row to its matching `chart_dashas.id` rows. This is the primary cross-table citation gap in L1.

---

## SYNERGY-2 — ga_sensitive (special lagnas) × ga_structural (house assignments)

The 3 newly-built special lagnas (Hora Lagna, Ghati Lagna, Bhava Lagna) store longitudes and signs but have NO house assignment relative to the D1 chart. The lagna at birth (from ga_positions) defines which house each special lagna falls in.

**Enhancement:** `_long_rows` helper in ga_sensitive_writer already computes house position from longitude + lagna. Confirm that the special lagna rows receive their `house_num` field (non-null). If currently NULL, add the assignment — the data is already available in the same substep.

**L2 value:** "Hora Lagna in the 5th house: intellect-karma axis emphasized; consistent with Mercury's Hora-Lagna placement signaling intellectual dharma" — this kind of signal cannot be generated without the house assignment.

---

## SYNERGY-3 — ga_nakshatra × ga_sensitive — KP lord data in two assets

ga_nakshatra writes `graha_kp_lords` and `cusp_kp_lords` (the authoritative KP sublord table for grahas + cusps). ga_sensitive also has a `kp_%` category family (pre-enrichment).

The two KP datasets may overlap or complement. L2 should verify:
- What exactly is in `kp_%` in ga_sensitive vs `graha_kp_lords` in ga_nakshatra?
- Are they the same data or different levels (star/sub/sub-sub/prana from ga_nakshatra vs higher-level KP categories in ga_sensitive)?

Until verified, use ga_nakshatra as the authoritative KP source (it has the full 4-level sublord tree per cusp + graha), and treat ga_sensitive's `kp_%` as legacy coverage until its scope is audited.

---

## SYNERGY-4 — ga_strength × ga_structural — Composite State depends on per-varga strength

ga_structural writes `graha_composite_state_classification` — a D1 aggregate of dignity + strength + avastha. This composite was built BEFORE per-varga strength (ga_strength Amendment 1) and per-varga avastha (ga_condition Amendment 2) existed.

The composite at D1 is still correct (it uses D1 strength/avastha). But the enrichment now enables a more powerful version: the per-varga composite strength for each divisional chart. This is a natural L2 Bodha task (bo_laksana), not an L1 task — L1's job is to provide the per-varga inputs. Flag for L2.

---

## SYNERGY-5 — ga_tajaka × ga_dashas — Varsha-Dasha confluence map

ga_tajaka stores the A7 varsha window (48 years × 5 ayanamshas = 240 rows). Each varsha has a Muntha position and a Vārṣeśa (year-lord). ga_dashas has the full MD/AD tree. No explicit cross-reference links "varsha N" to the active MD/AD in that year.

**High-value L2 map:** "Varsha 40 (2024–25): Vārṣeśa = Venus. Active dasha: Rahu MD / Venus AD. Venus as both year-lord AND antardasha lord = significator confluence; classical Tajaka amplification." This kind of insight requires the cross-reference, which can be computed from birth date + varsha start date vs chart_dashas timestamps.

For L1: add a `constituent_facts_array` on each `l1_tajik_varsha_year_lords` row pointing to the active MD/AD rows in `chart_dashas` for that varsha's date range. Or produce this as a ga_tajaka output category in chart_facts.

---

## SYNERGY-6 — ga_panchanga × ga_sensitive — Panchanga lords ↔ sensitive point convergence

ga_panchanga produces the birth panchanga (Vara lord = Sun, Tithi lord, Nakshatra lord, etc.). ga_sensitive produces the Yogi/Avayogi points and Yogi Graha (lord of Yogi nakshatra). The Yogi Graha being the same as the Vara lord (or Tithi lord or Nakshatra lord) is a classical convergence marker.

This cross-check requires joining two ga_* assets and exists at a fact-row level. L2 bo_sangati (signal correlations) should pick this up.

---

## SYNERGY-7 — ga_nakshatra × ga_sade_sati — Tara Bala shifts during Sade Sati

ga_nakshatra writes `graha_tara_bala` (natal baseline). ga_sade_sati produces the Sade Sati window (Saturn transiting 12th/1st/2nd from natal Moon). During the Sade Sati core (Saturn on natal Moon), the Tara Bala of every graha shifts significantly because the transit Saturn changes the nakshatra relationship.

ga_nakshatra's `tara_bala_natal_baseline` captures the natal state. The transit-modified Tara Bala during active Sade Sati phases is a distinct computation that either belongs in ga_sade_sati (as a `tara_bala_during_sade_sati` overlay) or in a future L3 Kāla asset (transit-layer). Flag for L3 roadmap.

---

## ARCH-1 — The per-varga citation chain: ga_vargas → ga_condition (the L1-authority pattern)

Amendment 2 established the only formal per-varga cross-asset citation in L1:
`chart_divisionals.dignity` (written by ga_vargas_writer) → `graha_avastha_deeptaadi_per_varga` (read and cited by ga_condition_writer)

This is the model for L2+ cross-layer derivations:
1. L1 fact is the authority
2. Derived L2 row carries a `constituent_facts_array` / `citation_ref` pointing to the specific L1 fact_id
3. If L1 fact changes, L2 derivation is rebuilt (not independently re-derived)

**All future L2 Bodha signals that depend on L1 per-varga data MUST follow this pattern.**

---

## ARCH-2 — Floored rows as first-class facts (the canonical-or-floor pattern)

The enrichment established that floored rows (Kala/Cheshta/Vighati/Jagradadi/Sayanadi/Lajjitadi per-varga) carry:
- `fact_value_num = NULL`
- `fact_value_text = 'floored: <reason>'`
- `verification_pass_status = 'floored'`

This is a first-class L1 data pattern. It enables L2 to distinguish "this is unknown" from "this was not computed" from "this is zero." L2 signals MUST honor this distinction — never treat a floored row as a zero-value fact.

---

## Action summary

| ID | Type | Blocking L1 seal? | Action |
|---|---|---|---|
| BUG-1 | BUG | YES | Migration 309: tighten ga_structural count_sql (remove `%_per_varga`, narrow `graha_avastha_%`, resolve nakshatra_pada_sensitive) |
| BUG-2 | BUG | NO | Resolved by BUG-1 |
| GAP-1 | GAP | YES | Migration 309/310: add ga_condition, ga_yoga, ga_vastu, ga_medical, ga_prashna to asset_registry + seed |
| GAP-2 | GAP | YES | Post-prod-build: set ga_condition.target_floor; patch seed + migration |
| GAP-3 | GAP | YES | Post-BUG-1-fix: re-verify ga_structural floor with tightened count_sql; update floor in migration 309 |
| GAP-4 | GAP | SOFT | Document ga_prashna 0-row ruling; add to registry with documented status |
| SYNERGY-1 | SYNERGY | NO | L1 enhancement: add citation_ref from sade_sati_concurrent_dasha_overlay to chart_dashas rows |
| SYNERGY-2 | SYNERGY | NO | Verify special_lagna house_num in ga_sensitive rows; add if NULL |
| SYNERGY-3 | SYNERGY | NO | L2 audit: scope ga_sensitive kp_% vs ga_nakshatra KP sublords; establish authority hierarchy |
| SYNERGY-4 | SYNERGY | NO | L2 roadmap: per-varga composite_state from enrichment inputs; L2 bo_laksana task |
| SYNERGY-5 | SYNERGY | NO | L1 enhancement or L2 map: varsha × dasha cross-reference |
| SYNERGY-6 | SYNERGY | NO | L2 bo_sangati: panchanga lord ↔ sensitive-point convergence signal |
| SYNERGY-7 | SYNERGY | NO | L3 Kāla roadmap: transit-modified Tara Bala during Sade Sati |
| ARCH-1 | ARCH | NO | L2 contract: per-varga cross-asset citation model to inherit |
| ARCH-2 | ARCH | NO | L2 contract: floored rows are first-class facts; not zeros |

**Blocking items for L1 seal: BUG-1, GAP-1, GAP-2, GAP-3.**

---

## Open migration plan

| Migration | Contents |
|---|---|
| 309 | (a) tighten ga_structural count_sql + new floor; (b) add ga_condition, ga_yoga, ga_vastu, ga_medical, ga_prashna to asset_registry; (c) ga_condition.target_floor after prod build |
| Seed patch | asset_registry_seed.ts: add 5 unregistered assets; update ga_structural floor post-BUG-1 fix |

*End of L1 Synergy Register v1.0 — 2026-06-18*
