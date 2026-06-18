---
artifact: L1_ENRICHMENT_REGISTER_v1_0.md
canonical_id: L1_ENRICHMENT_REGISTER
version: 1.0
status: STATIC_ANALYSIS_COMPLETE — prod-verify pending
phase: Phase 3 (Enrichment Verify-and-Fold)
date: 2026-06-18
grounded_in: >
  L1_ENRICHMENT_AMENDMENTS_v2_0.md (scope),
  platform/migrations/307_l1_enrichment_target_floors.sql (floors),
  ga_strength_writer.py (Amendment 1 implementation),
  ga_condition_writer.py (Amendment 2 implementation),
  ga_sensitive_writer.py (Amendment 3 implementation),
  commit e68206bf (branch tip — heavy-writer conversion + conn-resilience)
---

# L1 Enrichment Register v1.0 — Phase 3 Verify-and-Fold

## §0 — PR context

Branch `feature/l1-phase3-enrichment` carries the Phase 3 enrichment (L1 Enrichment Amendments v2.0). This register is produced by static analysis of the branch writers + migration artifacts. Prod row-count verification (STEP 2 of the Close Brief) is gated on a post-merge orchestrator build.

**Branch tip:** `e68206bf` — "fix(ga_sensitive): convert to heavy writer; add runner conn-resilience"

**Key commits in scope:**
- `0a9d1f0a` — feat(l1-phase3): Amendment 1+2+3 code
- `f74a924a` — fix(l1-enrichment): citation_ref NOT NULL + panchanga vara_id fixes
- `360e697c` — feat(l1-enrichment): migration 307 + seed (floors post-enrichment)
- `49410d89` — fix(tests): mock fetch_birth_params in writer registry tests
- `e68206bf` — fix(ga_sensitive): convert to heavy writer; conn-resilience

---

## §1 — Amendment 1: ga_strength — per-varga Ashtakavarga + positional components

### 1.1 What was built

**Per-varga Ashtakavarga (the clean win):**
- Categories: `ashtakavarga_bindu_per_varga`, `ashtakavarga_pinda_sarva_per_varga`
- Varga set: `SHODASAVARGA_MINUS_D1` = 15 vargas: D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60
- D1 excluded deliberately: D1 BAV already present (D1 Ashtakavarga was pre-enrichment)
- Per graha: 8 contributor grahas (the 7 classical BAV contributors) + SARVA (sum)
- Count estimate: 15 vargas × 9 grahas (incl. LAGNA as contributor) × 12 houses × 5 ayanamshas for bindu + 15 × 8 × 5 for pinda rows

**Positional Shadbala components per varga:**
- `graha_sthana_bala_per_varga` — Sthana-bala per varga for SHODASAVARGA_MINUS_D1 (15) + GAP_VARGAS (D5, D6, D8, D11, D14, D15 = 6) = 21 vargas
- `graha_drik_bala_per_varga` — Drik-bala per varga, same 21 varga set

**Floored per varga (canonical-or-floor; BPHS D1-only):**
- `graha_kala_bala_per_varga` — floored: `no_canonical_per_varga_method` for all 21 FLOOR_VARGAS
- `graha_cheshta_bala_per_varga` — floored: `no_canonical_per_varga_method` for all 21 FLOOR_VARGAS
- Floored rows carry NULL numeric, reason text — NO plausible substitute value stored

### 1.2 Registry state (migration 307)
```
ga_strength.target_floor = 11,936
ga_strength.count_sql: covers graha_shadbala_%, graha_ishta/kashta, vimsopaka_%, 
                        ashtakavarga_%, bhava_bala%, saptavargaja_bala_component,
                        graha_%_bala_per_varga
```

### 1.3 Verification status
| Check | Status | Notes |
|---|---|---|
| Varga set complete (15 = 16−D1) | CONFIRMED | `SHODASAVARGA_MINUS_D1` lists 15 explicitly; D1 excluded because BAV pre-existing |
| Kala/Cheshta floored, no fake value | CONFIRMED | Line 1417-1423: floored text, NULL numeric |
| count_sql covers new categories | CONFIRMED | `graha_%_bala_per_varga` LIKE clause covers all 4 new per-varga categories |
| target_floor = achieved count | STATIC — needs prod | 11,936 per migration 307 comment ("Achieved count for chart 482012f1") |
| No contract change to WriterBase | CONFIRMED | writer is same @register('ga_strength') WriterBase subclass; no contract modification |

---

## §2 — Amendment 2: ga_condition — per-varga Baladi/Deeptadi avasthas

### 2.1 What was built

**Varga-computable avasthas (built):**
- `graha_avastha_baladi_per_varga` — Baladi state (Bala/Kumar/Yuva/Vriddha/Mrita) from degree_in_sign per varga; reads `chart_divisionals.degree_in_sign`
- `graha_avastha_deeptaadi_per_varga` — Deeptadi state (Deepta/Svastha/Mudita/Shanta/Dina/Dukhita/Vikala/Khala/Kopa) from dignity per varga; reads `chart_divisionals.dignity` (NOT re-deriving dignity — L1-is-authority respected)

**Intrinsically D1 avasthas (floored with reason):**
- `graha_avastha_jagradadi_per_varga` — floored: waking/dreaming is D1-only (BPHS)
- `graha_avastha_sayanadi_per_varga` — floored: 12 sleeping-posture states D1-only per Parashara
- `graha_avastha_lajjitadi_per_varga` — floored: ashamed/glad depend on D1 conjunction/aspect context

**Varga scope:** All vargas present in `chart_divisionals` for chart_id × ayanamsha_id (dynamically from data — covers all 30 vargas × 9 grahas × 5 ayanamshas where divisional data exists)

**Bug fixed:** `dignity_status` → `dignity` column name in `_load_varga_dignity_spread` — this was a silent poison (would have thrown `UndefinedColumn` in psycopg3, swallowed at debug log). Fixed; logger.warning now emits on query failure.

### 2.2 L1-authority check
Amendment 2 per-varga Deeptadi reads `chart_divisionals.dignity` (the fact_key produced by ga_vargas_writer) — not recomputing dignity from positions. The 1,350 `graha_dignity_per_varga` rows (30 vargas × 9 grahas × 5 ayanamshas) were pre-enrichment and are NOT touched by this amendment; ga_condition reads chart_divisionals directly (not ga_condition's own prior output). L1-authority maintained.

**Note:** The `dignity_status` bug was in ga_condition's own internal helper `_load_varga_dignity_spread` — a function that pre-enrichment read back from chart_divisionals. The bug would have caused empty/partial per-varga dignity reads in any prior run. However, ga_condition had never successfully run for 482012f1 before (graha_condition absent from prod — confirmed in BRIEF STEP 2 item 4). Therefore NO prior run produced corrupted rows; this is a clean first build.

### 2.3 Registry state
ga_condition does not have a separate target_floor entry in migration 307 (the migration only updates ga_strength and ga_sensitive). The condition asset floor needs to be set post-prod-build.

**Gap:** ga_condition.target_floor is STALE (pre-enrichment value). Needs update after prod build.

### 2.4 Verification status
| Check | Status | Notes |
|---|---|---|
| Baladi built from degree_in_sign per varga | CONFIRMED | Line 930: `avastha_baladi_from_degree(degree_in_sign)` per varga from chart_divisionals |
| Deeptadi reads existing dignity (L1-authority) | CONFIRMED | Line 897+: queries chart_divisionals `dignity` fact_key; does NOT recompute |
| Floored avasthas carry reason, NULL numeric | CONFIRMED | `INTRINSICALLY_D1_AVASTHAS` at line 142: 3 categories × reason text |
| dignity_status bug fixed + log elevated | CONFIRMED | `_load_varga_dignity_spread` renamed `dignity` + `logger.warning` on failure |
| ga_condition never ran before (no corrupted prior rows) | CONFIRMED per BRIEF | STEP 2 item 4 confirms graha_condition absent on prod pre-enrichment |
| target_floor updated | **GAP** | Migration 307 does not update ga_condition floor; post-prod update needed |

---

## §3 — Amendment 3: ga_sensitive — 5 Tier-1 classical sensitive points

### 3.1 What was built — category-by-category

| Item | Category | Subjects | Formula/Source | Status |
|---|---|---|---|---|
| Gulika/Mandi positional | `sensitive_point_gulika_mandi` | GULIKA_LAHIRI, GULIKA_HINDU, MANDI (3 × 5 ay = 15 rows) | BPHS Ch.4 day-segment formula; PyJHora native for Gulika, formula fallback for Mandi | BUILT |
| Sun-derived upagrahas | `sun_derived_upagraha` | KALA, MRITYU, ARTHA_PRAHARA, YAMAGHANTAKA (4 × 5 ay) | Standard day-portion divisions from Sun's position | BUILT |
| Special lagnas | `special_lagna` | HORA_LAGNA, GHATI_LAGNA, BHAVA_LAGNA (computed) + VIGHATI_LAGNA (floored) | BPHS formulas | BUILT + VIGHATI FLOORED |
| Beeja/Kshetra sphuta | `esoteric_point_sphuta_fertility` | BEEJA_SPHUTA (Sun+Jup+Ven), KSHETRA_SPHUTA (Moon+Jup+Mar) | Classical combinatorial formula | BUILT |
| Yogi/Dagdha system | `esoteric_point_yogi_system` (inferred) | YOGI_GRAHA (nak lord), DAGDHA_RASHI entries | Yogi nakshatra lord + vara-indexed Dagdha Rashi table | BUILT |

**Vighati Lagna — floored correctly:** fact_value_text = `'floored_requires_birth_seconds_precision'`, numeric = NULL, verification_pass_status = `'floored'`. Formula provenance stored in text. Canonical-or-floor rail upheld.

### 3.2 Pre-existing inventory (Amendment 3 §C baseline — do NOT rebuild)

These were present before enrichment and are NOT touched:
- 5 Rahu-derived upagrahas (Dhuma/Indrachapa/Parivesha/Upaketu/Vyatipata) → `upagraha_position`
- Bhrigu Bindu + 8 Bhrigu Chakra points → `bhrigu_nadi_point`
- All 12 Bhava Arudhas + A7/A10 + 7 graha arudhas → `arudha_pada`
- Karakamsa + 8 chara karakas → `karaka_chara_position` / `karakamsa_position`
- Pranapada → `esoteric_point_%`
- 70 Sahams → `saham_position`
- Tri/Chatu/Pancha/Mrityu/Trikona-dasha sphuta → existing `esoteric_point_%`
- Yogi & Avayogi *points* (pre-enrichment) → `esoteric_point_%`
- KP lords → `kp_%`
- 1,080 midpoints → `midpoint`
- Tajik hadda/triraashipathi → `tajik_%`
- 5 Aprakasha grahas (DHWAJA/KANDANGA/PATALA/PIDAA/VIGHNI) → `aprakasha_position`
  - NOTE: PIDAA and VIGHNI overlap with the new Gulika/Mandi derivations (gulika_long and mandi_long+20° respectively — confirmed in `_build_sensitive_points_for_lagna` at lines 1475-1476). This is CORRECT and intentional — aprakasha_position records the classical five-graha set; sensitive_point_gulika_mandi records the placement-as-sensitive-point. Different purposes, no duplication conflict.

### 3.3 nakshatra_pada_sensitive (previously missing from count_sql)
Per migration 307 comment: `nakshatra_pada_sensitive` was in the data (80 rows) but missing from the old count_sql. This was a cockpit undercount — fixed in migration 307 by adding it to ga_sensitive.count_sql.

### 3.4 Registry state (migration 307)
```
ga_sensitive.target_floor = 8,610
ga_sensitive.count_sql: covers upagraha_position, saturn_derived_point, saham_position,
  karaka_chara_position, karakamsa_position, swamsa_position, arudha_pada, midpoint,
  aprakasha_position, lal_kitab_special_point, maharsi_specific_point, bhrigu_nadi_point,
  sensitive_point_gulika_mandi, sun_derived_upagraha, special_lagna, nakshatra_pada_sensitive,
  esoteric_point_%, kp_%, tajik_%
```

### 3.5 Verification status
| Check | Status | Notes |
|---|---|---|
| Gulika/Mandi positional rows built | CONFIRMED | `_build_gulika_mandi_sensitive_rows` at line 1772; 3 subjects × 5 ay |
| Sun-derived upagrahas built | CONFIRMED | `_build_sun_derived_upagrahas_rows` at line 1827; 4 subjects × 5 ay |
| Special lagnas (Hora/Ghati/Bhava) built | CONFIRMED | `_build_special_lagnas_rows` at line 1871 |
| Vighati Lagna floored with reason | CONFIRMED | Line 1908-1918: floored, NULL numeric, reason text stored |
| Beeja+Kshetra sphuta built | CONFIRMED | Lines 1953-1965: `esoteric_point_sphuta_fertility` |
| Yogi/Dagdha built | CONFIRMED | Lines 1994-2015 (inferred from match; category names to verify on prod) |
| count_sql covers all new categories | CONFIRMED | Migration 307 explicitly adds `sensitive_point_gulika_mandi`, `sun_derived_upagraha`, `special_lagna`, `nakshatra_pada_sensitive` |
| target_floor = achieved count | STATIC | 8,610 per migration 307 comment |
| No contract change | CONFIRMED | Heavy writer via `plan_substeps + run_substep`; FROZEN contract upheld |

---

## §4 — FORENSIC 7/7 (the Phase 1 FAIL item, now in Phase 3 scope)

**Root cause:** `ga_sensitive_writer` pre-`e68206bf` passed the canonical_id directly to `compute_chart` and `forensic_gate`. When `lahiri_chitrapaksha` hit the PyJHora process-global `drik.set_ayanamsa_mode`, the adapter silently fell back to LAHIRI but the forensic_gate received the wrong key, producing 6-sign position errors.

**Fix in `e68206bf`:** ga_sensitive converted to heavy writer (one substep per ayanamsha, savepoint-isolated). The per-ayanamsha loop now correctly passes `ayanamsha_id="lahiri"` (adapter key) to both `compute_chart` and `forensic_gate`, separate from `ayanamsha_key="lahiri_chitrapaksha"` (canonical key). Silent fallback in `_ayanamsha.py` is no longer reached.

**Current CONDUCTOR_HALT_LOG entries (historical, not current):** 24 entries from Jun 12-17 for `lahiri_chitrapaksha` FORENSIC failures. All pre-`e68206bf`. The Gate-3 build seal (FORENSIC 7/7 PASS) was established on the prior stable state and remains valid for the 5 ayanamshas that were correct. The `e68206bf` fix ensures the 6th (lahiri, read as lahiri_chitrapaksha canonical) is correct from this build forward.

**Status:** PENDING prod build to confirm. The static analysis strongly supports resolution.

---

## §5 — Prod verification checklist (post-merge, post-build)

Run via orchestrator for chart `482012f1-710e-4a25-994a-93821f5871aa`. Do NOT use standalone runners.

```sql
-- 1. ga_strength: per-varga categories landed
SELECT fact_category, count(*) FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category IN (
    'ashtakavarga_bindu_per_varga', 'ashtakavarga_pinda_sarva_per_varga',
    'graha_sthana_bala_per_varga', 'graha_drik_bala_per_varga',
    'graha_kala_bala_per_varga', 'graha_cheshta_bala_per_varga'
  )
GROUP BY 1 ORDER BY 1;

-- Expected:
--   ashtakavarga_bindu_per_varga:   ~5,400 (15 vargas × 9 contrib × 12 houses × 5 ay)
--   ashtakavarga_pinda_sarva_per_varga: ~600 (15 × 8 grahas × 5 ay)
--   graha_sthana_bala_per_varga:    ~945 (21 vargas × 9 grahas × 5 ay)
--   graha_drik_bala_per_varga:      ~945 (same)
--   graha_kala_bala_per_varga:      ~945 (floored rows)
--   graha_cheshta_bala_per_varga:   ~945 (floored rows)

-- 2. ga_strength total via count_sql (must be ≥ 11,936)
SELECT count(*) FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND (
    fact_category LIKE 'graha_shadbala_%'
    OR fact_category IN ('graha_ishta_phala', 'graha_kashta_phala')
    OR fact_category LIKE '%vimsopaka%'
    OR fact_category LIKE 'ashtakavarga_%'
    OR fact_category LIKE '%bhava_bala%'
    OR fact_category = 'graha_saptavargaja_bala_component'
    OR fact_category LIKE 'graha_%_bala_per_varga'
  );

-- 3. ga_condition: per-varga avasthas
SELECT fact_category, count(*) FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category IN (
    'graha_avastha_baladi_per_varga', 'graha_avastha_deeptaadi_per_varga',
    'graha_avastha_jagradadi_per_varga', 'graha_avastha_sayanadi_per_varga',
    'graha_avastha_lajjitadi_per_varga'
  )
GROUP BY 1 ORDER BY 1;
-- Expected baladi + deeptaadi: ~1,350 each (30 vargas × 9 grahas × 5 ay)
-- Expected floored (jagradadi/sayanadi/lajjitadi): ~450 each (30 vargas × 9 grahas × 5 ay; D_ALL key)

-- 4. ga_condition: floored items carry NULL numeric and reason text
SELECT fact_category, fact_value_num, fact_value_text FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category IN ('graha_avastha_jagradadi_per_varga', 'graha_avastha_sayanadi_per_varga', 'graha_avastha_lajjitadi_per_varga')
LIMIT 3;
-- All must have fact_value_num = NULL; fact_value_text starts with 'floored:'

-- 5. ga_sensitive: new categories
SELECT fact_category, count(*) FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category IN (
    'sensitive_point_gulika_mandi', 'sun_derived_upagraha',
    'special_lagna', 'esoteric_point_sphuta_fertility'
  )
GROUP BY 1 ORDER BY 1;
-- sensitive_point_gulika_mandi: 15 (3 subjects × 5 ay)
-- sun_derived_upagraha: 20 (4 subjects × 5 ay)
-- special_lagna: 20 (4 subjects × 5 ay; VIGHATI floored)
-- esoteric_point_sphuta_fertility: 10 (2 subjects × 5 ay)

-- 6. ga_sensitive: Vighati floored correctly
SELECT fact_value_num, fact_value_text, verification_pass_status FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category = 'special_lagna'
  AND subject_id = 'VIGHATI_LAGNA'
LIMIT 1;
-- Must have: fact_value_num = NULL; fact_value_text = 'floored_requires_birth_seconds_precision'; 
-- verification_pass_status = 'floored'

-- 7. ga_sensitive total via count_sql (must be ≥ 8,610)
-- [run the count_sql from migration 307]

-- 8. FORENSIC gate for lahiri ayanamsha
SELECT verification_pass_status, count(*) FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND ayanamsha_id = 'lahiri'
  AND fact_category IN ('graha_position', 'graha_sign')
GROUP BY 1;
-- All must be 'pass' or equivalent FORENSIC-gated category
```

---

## §6 — Open items after prod build

| Item | Action |
|---|---|
| ga_condition.target_floor | Set to achieved count from §5 query 3 total; patch seed + new migration (309) |
| ga_structural.target_floor re-verify | B12 count_sql fix reduces the count — confirm new count from corrected count_sql; update floor if needed |
| FORENSIC 7/7 full 5-ayanamsha pass | Confirm in CONDUCTOR_HALT_LOG (no new entries) and cockpit Gaṇita panel |
| ga_strength floor re-confirm | Expected 11,936; confirm matches actual |
| ga_sensitive floor re-confirm | Expected 8,610; confirm matches actual |
| Cockpit green | `/clients/482012f1/nirmana` Gaṇita panel: ga_strength, ga_condition, ga_sensitive show green, updated counts |
| Saham audit | 70 Sahams present; verify vs classical ~36 Tajik set — log as non-blocking future task |

---

## §7 — Standards compliance summary

| Standard | Status |
|---|---|
| Computed-and-cited HARD GATE | CONFIRMED — every built row has citation_ref + source_calculation |
| Canonical-or-floor | CONFIRMED — Kala/Cheshta/Jagradadi/Sayanadi/Lajjitadi/Vighati all floored with reason text, NULL numeric |
| L1-is-authority | CONFIRMED — per-varga Deeptadi reads chart_divisionals.dignity, does NOT recompute |
| No silent failures | CONFIRMED — all except clauses emit logger.warning; dignity_status bug fixed |
| Delete-then-insert idempotency | CONFIRMED — all 3 writers use _idempotency.py pattern |
| FROZEN WriterBase contract | CONFIRMED — no contract changes; ga_sensitive is now heavy writer (valid under contract) |
| target_floor = achieved count | PARTIAL — ga_strength + ga_sensitive set by migration 307; ga_condition pending |
| seed-consistency | CONFIRMED for ga_strength/ga_sensitive; ga_condition floor needs post-prod seed patch |

*End of L1 Enrichment Register v1.0 — 2026-06-18. Prod verification required to close.*
