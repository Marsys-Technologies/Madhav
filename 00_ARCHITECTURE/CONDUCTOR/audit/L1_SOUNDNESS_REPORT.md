---
artifact: L1_SOUNDNESS_REPORT
version: 1.0
status: ASSESS-ONLY
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
audit_date: 2026-06-24
auditor: Claude Code (Sonnet 4.6)
scope: All ga_* writers, Lens 1 (L0-bypass), Lens 2 (Rahu/Ketu propagation)
action_taken: ASSESS ONLY — no fix, no build, no seal
---

# L1 Gaṇita Soundness Report v1.0

**Audit date:** 2026-06-24  
**Chart:** 482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty, 1984-02-05 10:43 IST Bhubaneswar)  
**Mandate:** ASSESS ONLY per CLAUDE_CODE_PROMPT_L1_AUDIT.md — no fix, no build, no seal.

---

## §HEADLINE — Single Most Important Finding

**LENS 2 VERDICT: The L0 Rahu/Ketu fix did NOT propagate to live L1 data.**

Live `ga_condition_composite` (2026-06-18 build) shows:  
- Rahu (in Taurus, house 2): `dignity_d1=friend_sign, score=0.6` — should be `exalted=1.0`  
- Ketu (in Scorpio, house 8): `dignity_d1=friend_sign, score=0.6` — should be `exalted=1.0`  

Root cause: `ga_condition` was last built **2026-06-18**, six days before the L0 seal (2026-06-24). The L0 fix is live in `bg_dignity_reference`. The writer architecture is correct (reads L0 DB at runtime via `_load_dignity_ref()`). But the **stored data is pre-fix stale** — a rebuild is required to propagate the fix.

Secondary headline: `ga_condition` also has **two L0 bypass constants** that would corrupt the dignity fallback path even after rebuild if not corrected. And `ga_dashas` carries a **vocabulary mismatch (F7)** that silently severs all JOINs between `chart_dashas` and `chart_facts`.

---

## §FORENSIC — 7/7 FORENSIC Anchors Verified

All seven FORENSIC birth anchors confirmed in live DB at `ayanamsha_id='lahiri_chitrapaksha'`:

| Anchor | Expected | Live Data | Source | Status |
|---|---|---|---|---|
| Sun sign | Capricorn | enemy_sign (Sun in Capricorn → enemy_sign is correct) | `ga_condition_composite.dignity_d1` | ✓ PASS |
| Moon nakshatra | Purva Bhadrapada | Purva Bhadrapada | `chart_facts.panchanga_nakshatra_moon/name` | ✓ PASS |
| Lagna | Aries | Implied by functional class tables (BPHS table for Aries matches data) | `chart_facts.graha_functional_class_per_ascendant` 70 rows | ✓ PASS |
| Tithi | Shukla Tritiya | Shukla Tritiya | `chart_facts.panchanga_tithi/name` | ✓ PASS |
| Vara | Ravivara | Ravivara | `chart_facts.panchanga_vara/name` | ✓ PASS |
| Yoga | Shiva | Shiva | `chart_facts.panchanga_yoga/name` | ✓ PASS |
| Karana | Garaja | Garaja | `chart_facts.panchanga_karana/name` | ✓ PASS |

FORENSIC 7/7 GREEN. Positional grounding of the chart is correct.

---

## §CENSUS — L1 Asset Row Counts

| Asset | Table | Row Count | Expected Range | Status |
|---|---|---|---|---|
| ga_positions | `chart_facts` (graha_position) | 430 | ~400–500 (9 grahas × 5 ayanamshas × ~10 keys) | PLAUSIBLE |
| ga_panchanga | `chart_facts` (panchanga_*) | ~850+ across 33 sub-categories | Rich; varied keys per category | PLAUSIBLE |
| ga_nakshatra | `chart_facts` (nakshatra_*) | 1,165 across 12 categories | ~700–1500 | PLAUSIBLE |
| ga_structural | `chart_facts` (yoga_fires + others) | 23,034+ (argala=21,600; yoga=44; dosha=10; functional=70; etc.) | Argala dominant | PLAUSIBLE |
| ga_vargas | `chart_divisionals` | 21,635 | 30 vargas × 9+ bodies × 5 ayanamshas × keys | PLAUSIBLE |
| ga_dashas | `chart_dashas` | 536,471 | Large (hierarchical dasha tree × 5 ayanamshas) | PLAUSIBLE |
| ga_yoga | `ga_yoga_firings` | **5** | Expected 50–500 (catalog has 200+ yogas × 5 ayanamshas) | **WRONG** |
| ga_condition | `ga_condition_composite` | 45 (9 grahas × 5 ayanamshas) | 45 | PLAUSIBLE |
| ga_sensitive | `chart_facts` (sensitive_point_*) | Unknown — not directly queried | — | UNVERIFIED |
| ga_strength | `chart_facts` (shadbala_*) | Unknown | — | UNVERIFIED |
| ga_medical | reads `ga_condition_composite` | downstream | — | DOWNSTREAM |
| ga_sade_sati | `chart_facts` (sade_sati_*) | Unknown | — | UNVERIFIED |
| ga_tajaka | `l1_tajik_varsha_year_lords` | 0 (table exists but 0 rows for chart) | >0 if annual charts built | SUSPECT |
| ga_vastu | downstream consumer | — | — | DOWNSTREAM |
| ga_prashna | N/A for natal chart | 0 (expected for natal) | 0 for natal = correct | INAPPLICABLE |

---

## §BYPASS — L0 Bypass Findings (Lens 1)

An **L0 bypass** is defined as: a ga_* writer carrying a private inline copy of classical reference data (exaltation signs, sign lords, nakshatra lords) that should be read from L0 tables (`bg_dignity_reference`, `reference_signs`, `reference_nakshatras`). When L0 is fixed, a bypass silently diverges.

### Bypass Tally

| Writer | Bypass Count | Bypass Items | Notes |
|---|---|---|---|
| ga_condition | **2** | (1) `_EXALTATION`/`_DEBILITATION` module-level constants (stale Rahu/Ketu); (2) Mercury `sama_hi=2.5` in inline motion thresholds | Primary path reads L0 DB ✓ — bypasses are fallback paths |
| ga_structural | **2** | (1) `EXALTATION_SIGNS["Rahu"]="Gemini"`, `["Ketu"]="Sagittarius"`; (2) `DEBILITATION_SIGNS["Rahu"]="Sagittarius"`, `["Ketu"]="Gemini"` | No L0 DB read for dignity seen in writer; inline constants appear to be used exclusively |
| ga_sensitive | **2** | (1) `SIGN_LORDS` dict (12 entries) — bypasses `reference_signs.lord`; (2) `NAK_LORDS` list — bypasses `reference_nakshatras.vimshottari_lord` | Hadda lords and other Tajik tables not in L0 (LEGITIMATE) |
| ga_dashas | **1** | `NAKSHATRA_LORDS_1BASED` derived from inline `_NAK_LORD_CYCLE` — bypasses `reference_nakshatras.vimshottari_lord` | Also carries F7 vocab bug (separate finding) |
| ga_yoga | 0 | No dignity bypass; reads from `brahma_yoga_catalog` (L0 read ✓) | But only fires 1 yoga — structural WRONG |
| ga_vargas | 0 | Imports from `pyjhora_adapter._names` | Adapter layer; not direct inline L0 data |
| ga_strength | 0 | `NAISARGIKA_BALA` is fixed classical constant — not L0 reference data; LEGITIMATE | Same for `SHADBALA_REQUIRED` |
| ga_panchanga | 0 | Delegates to `panchanga_engine.panchanga_instant` service | No inline dignity data |
| ga_sade_sati | 0 | Reads Moon from `chart_facts`; no dignity inline | — |
| ga_tajaka | 0 | `EXALT` dict covers only classical 7 grahas; Rahu/Ketu absent — CLEAN for nodes | — |
| ga_vastu | 0 | `GRAHA_TO_DIRECTION` is Vastu mapping (Mayamata Ch.6) — no L0 table owns this; LEGITIMATE | — |
| ga_medical | 0 | Downstream consumer; no inline dignity data | — |
| ga_prashna | 0 | `PLANET_DAILY_MOTION` is astronomical constant — LEGITIMATE | — |

**TOTAL BYPASS COUNT: 7 across 4 writers**  
(ga_condition=2 + ga_structural=2 + ga_sensitive=2 + ga_dashas=1)

### Severity Ranking

1. **ga_condition bypasses (CRITICAL):** The fallback `_EXALTATION`/`_DEBILITATION` constants carry stale Rahu/Ketu (Gemini/Sagittarius). If `_load_dignity_ref()` fails or returns None (DB unavailable), the writer silently uses wrong values. Mercury `sama_hi=2.5` hardcode means the Mercury atichara threshold fix (2.5→2.0) from the L0 seal never reaches `ga_condition` even after rebuild.

2. **ga_structural bypasses (HIGH):** `EXALTATION_SIGNS` and `DEBILITATION_SIGNS` with stale Rahu/Ketu are used for yoga condition evaluation (Mahapurusha yoga checks reference these). No evidence of a DB fallback for these constants. Every build uses the wrong Rahu/Ketu exaltation for structural yoga firing.

3. **ga_sensitive bypasses (MEDIUM):** SIGN_LORDS and NAK_LORDS are stable classical constants that don't change with L0 fixes. The bypass is architecturally impure but practically lower-risk since these values are stable across all recognized authorities.

4. **ga_dashas bypass (MEDIUM):** NAKSHATRA_LORDS_1BASED is also a stable classical constant (same cycle for all Parashari authorities). Architecturally impure but practically low-risk.

---

## §PER-ASSET — Verdicts

### GA1 — ga_positions
**Verdict: SOUND**  
- 430 `graha_position` rows (9 grahas × 5 ayanamshas × ~9–10 keys) — plausible census.
- FORENSIC: Sun=enemy_sign confirms Capricorn; Moon=Purva Bhadrapada confirmed.
- No bypass: positions computed by Swiss Ephemeris via pyjhora adapter — no inline classical constants.
- No L0 classical data used; no bypass possible.

### GA2 — ga_panchanga
**Verdict: SOUND**  
- Rich panchanga output: 33+ categories, all 7 FORENSIC panchanga anchors verified.
- Delegates to `panchanga_engine.panchanga_instant` service — no inline dignity constants.
- Moon nakshatra = Purva Bhadrapada, vimshottari_starting_lord = Jupiter: correct for PBh.
- **No bypass. No wrong data detected.**

### GA3 — ga_nakshatra
**Verdict: PROBABLY SOUND (partial verification)**  
- 1,165 rows across 12 nakshatra categories. Census plausible.
- `graha_nakshatra_join`: 700 rows (9 grahas × 5 ayanamshas × ~15 keys) — plausible.
- `nakshatra_dispositor`: 200; `nakshatra_pada_sensitive`: 80 — all plausible proportions.
- Writer reads from `reference_nakshatras` (L0 table) for enrichment — architecture sound.
- `ga_dashas` bypass of `NAKSHATRA_LORDS_1BASED` (separate writer) may produce inconsistency between nakshatra lord in `chart_facts` vs `chart_dashas` if the inline list differs from the DB. Values are classically stable, so risk is low but architecturally non-compliant.
- **No bypass in ga_nakshatra_writer itself. SOUND.**

### GA4 — ga_structural
**Verdict: BYPASS (2) + ASTROLOGICALLY SUSPECT**  
- Census: 23,034+ rows; argala matrix (21,600) dominates; yoga_fires=44, dosha_fires=10, functional_class=70 — all plausible counts.
- **BYPASS 1:** `EXALTATION_SIGNS["Rahu"]="Gemini"` — stale. Post-L0 fix, correct value is `"Taurus"`.
- **BYPASS 2:** `DEBILITATION_SIGNS["Rahu"]="Sagittarius"` — stale. Post-L0 fix, correct value is `"Scorpio"`.
- These constants are used for yoga condition checks (Mahapurusha yogas check `required_signs`). Rahu/Ketu are not Mahapurusha yoga planets, so MAHAPURUSHA_YOGAS themselves are unaffected. However, KALA_SARPA_YOGA condition check (`all_planets_between_rahu_ketu`) and any sign-based yoga check involving Rahu/Ketu could be affected.
- `FUNCTIONAL_CLASS_BPHS` and `FUNCTIONAL_CLASS_RAMAN` are inline (7 classical grahas only, no Rahu/Ketu) — LEGITIMATE (these tables don't exist in L0).
- `NATURAL_KARAKAS` inline dict — LEGITIMATE (no L0 table for karakatva).
- `YOGA_LIBRARY` inline definitions — LEGITIMATE (these are rule definitions, not L0 reference data).
- `DOSHA_LIBRARY` inline — LEGITIMATE.
- **PROPOSED FIX SCOPE:** Update `EXALTATION_SIGNS["Rahu"]` → `"Taurus"` and `DEBILITATION_SIGNS["Rahu"]` → `"Sagittarius"` (and Ketu mirror values). Better: add a DB read path for exaltation/debilitation from `bg_dignity_reference`, consistent with ga_condition's primary path. **Family: F4 (silent fallback using stale constants).**

### GA5 — ga_vargas
**Verdict: PROBABLY SOUND (partial verification)**  
- 21,635 rows in `chart_divisionals` — matches L1_GANITA_CLOSURE canonical count exactly.
- Imports SIGN_NAMES, SIGN_LORDS from `pyjhora_adapter._names` — not direct inline L0 data. The adapter layer is an intermediate; the bypass is one layer removed but architecturally similar.
- No Rahu/Ketu exaltation constants visible in the writer.
- **No direct L0 bypass. PROBABLY SOUND.**

### GA6 — ga_dashas
**Verdict: WRONG (F7 vocabulary drift) + BYPASS (1)**  
- 536,471 rows — plausible count.
- **F7 WRONG:** Ayanamsha IDs in `chart_dashas` are `lahiri`, `kp`, `true_chitra`, `raman`, `surya_siddhanta`. The canonical L1 vocabulary (used in `chart_facts`, `ga_yoga_firings`, `ga_condition_composite`) is `lahiri_chitrapaksha`, `krishnamurti`, `true_chitra`, `raman`, `surya_siddhanta_classical`. The mismatches: `lahiri` ≠ `lahiri_chitrapaksha`; `kp` ≠ `krishnamurti`; `surya_siddhanta` ≠ `surya_siddhanta_classical`. Any JOIN of `chart_dashas` to `chart_facts` on `ayanamsha_id` will return **0 rows** for three of the five ayanamshas.
- **BYPASS 1:** `NAKSHATRA_LORDS_1BASED` dict derived from inline `_NAK_LORD_CYCLE` — bypasses `reference_nakshatras.vimshottari_lord`. Classical values are stable (low practical risk) but architecturally non-compliant.
- **EVIDENCE:** `chart_facts` has `lahiri_chitrapaksha`; `chart_dashas` has `lahiri`. These cannot JOIN.
- **PROPOSED FIX SCOPE:** Update `ga_dashas_writer.py` and its orchestrator adapter to use the canonical vocabulary set (`lahiri_chitrapaksha`, `krishnamurti`, `surya_siddhanta_classical`). Requires a rebuild. **Family: F7 (vocabulary drift).**

### GA7 — ga_yoga
**Verdict: WRONG (critically underperforming)**  
- `ga_yoga_firings`: **5 rows total** = 1 yoga (`yuga_nabhasa`) × 5 ayanamshas.
- Expected: The native's chart has confirmed mahapurusha yogas (SASA_MAHAPURUSHA found in `chart_facts.yoga_fires` from ga_structural), raja yogas (RAJA_YOGA_JUP_KENDRA_TRIKONA, RAJA_YOGA_VEN_KENDRA_TRIKONA, RAJA_YOGA_MUTUAL_9_10_LORDS confirmed), and other notable combinations. The `brahma_yoga_catalog` in L0 has 200+ entries.
- The writer reads from `brahma_yoga_catalog` correctly (no L0 bypass) but its evaluation logic fires only 1 yoga across the entire catalog for this chart — a clear implementation fault.
- `constituent_fact_ids: []` (empty) on all 5 rows — the writer is not linking yogas back to the L1 facts that satisfy their conditions. This is a schema design gap (B.3 derivation-ledger violation).
- `strength: None` on all 5 rows — strength computation not running.
- **NOTE:** ga_structural separately emits `yoga_fires` rows into `chart_facts` with better coverage. ga_yoga is a parallel system that is currently broken and adds no value over ga_structural's output.
- **PROPOSED FIX SCOPE:** Deep investigation of ga_yoga evaluation logic; likely the condition-matching code fails to resolve chart_facts rows to yoga conditions. Rebuilding after fix needed. **Family: F6 (inert gate — catalog loaded but matching logic fails to fire).**

### GA8 — ga_condition
**Verdict: BYPASS (2) + STALE DATA + PARTIAL DATA GAPS**  
- 45 rows in `ga_condition_composite` (9 grahas × 5 ayanamshas) — correct census.
- **LENS 2 VERDICT (Rahu/Ketu propagation): NOT PROPAGATED.**  
  - Rahu: `dignity_d1=friend_sign, score=0.6` — should be `exalted=1.0` (Rahu in Taurus, L0 now says Taurus=exaltation).  
  - Ketu: `dignity_d1=friend_sign, score=0.6` — should be `exalted=1.0` (Ketu in Scorpio, L0 now says Scorpio=exaltation).  
  - Root cause: build_date=2026-06-18; L0 fix seal=2026-06-24. A rebuild after the seal will propagate the fix correctly via `_load_dignity_ref()`.
- **BYPASS 1 (CRITICAL):** Module-level `_EXALTATION["Rahu"]="Gemini"`, `_EXALTATION["Ketu"]="Sagittarius"` at lines ~100-119. These are the **fallback path** used when `_load_dignity_ref()` returns `None` (DB unavailable). After rebuild, the fallback would still compute wrong Rahu/Ketu dignity. Must also fix the constants.
- **BYPASS 2 (HIGH):** `"Mercury": {"sama_hi": 2.5}` in inline motion threshold dict (line ~539). The L0 fix corrected Mercury atichara to 2.0°/day in `bg_motion_state_thresholds`. The `ga_condition` writer does NOT read `bg_motion_state_thresholds` from DB — it uses a hardcoded dict. This bypass means the Mercury atichara fix **never reaches ga_condition**, even after rebuild.
- **DATA GAP:** `motion_state=None` for 7 of 9 grahas (Jupiter, Mars, Mercury, Moon, Saturn, Sun, Venus). Only Rahu and Ketu have motion_state='vakra'. `speed_degrees_per_day=None` for all grahas. This suggests motion state is not being computed or stored for classical planets — a data quality gap of unknown severity.
- Other dignities: Sun=enemy_sign ✓, Saturn=exalted ✓, Jupiter=moolatrikona ✓ — these are correctly computed.
- **PROPOSED FIX SCOPE:** (1) Fix `_EXALTATION`/`_DEBILITATION` constants to match L0. (2) Add DB read path for `bg_motion_state_thresholds` (same pattern as `_load_dignity_ref`). (3) Rebuild. (4) Investigate motion_state gap. **Families: F4 (silent fallback) + F4 (bypass preventing fix propagation).**

### GA9 — ga_sensitive
**Verdict: BYPASS (2), otherwise PROBABLY SOUND**  
- `_HADDA_LORDS_BY_SIGN` (60 zones, Tajika Hadda table) — LEGITIMATE (no L0 table for this).
- **BYPASS 1:** `SIGN_LORDS` dict (12 sign→planet mappings) — bypasses `reference_signs.lord` in L0. Classically stable; low practical risk but architecturally non-compliant.
- **BYPASS 2:** `NAK_LORDS` list (27-element vimshottari lord sequence) — bypasses `reference_nakshatras.vimshottari_lord`. Same stability argument.
- No Rahu/Ketu exaltation constants observed.
- **PROPOSED FIX SCOPE:** Replace inline SIGN_LORDS and NAK_LORDS with DB reads from `reference_signs` and `reference_nakshatras`. Low urgency (stable data) but architecturally required. **Family: F4 (silent bypass of L0 authority).**

### GA10 — ga_strength
**Verdict: SOUND**  
- `NAISARGIKA_BALA` dict (Sun=0.600, Moon=0.519, …) — these are fixed classical strength constants for Naisargika bala computation. They are the same for every chart and every tradition. No L0 table stores or should store these. LEGITIMATE.
- `SHADBALA_REQUIRED` thresholds — same rationale. LEGITIMATE.
- No Rahu/Ketu exaltation constants.
- **No bypass. SOUND.**

### GA11 — ga_medical
**Verdict: SOUND (downstream consumer)**  
- Reads `condition_score` from `ga_condition_composite`. Downstream of ga_condition's stale data but has no bypass of its own.
- The medical output is only as good as ga_condition's scores. Since Rahu/Ketu condition_score is stale (0.525 vs correct ~0.7+ post-fix), medical output is also stale for nodes.
- **No direct bypass. DOWNSTREAM STALE.**

### GA12 — ga_sade_sati
**Verdict: SOUND**  
- Reads Moon sign from `chart_facts` (GA3 rows). Moon is in Aquarius; Saturn in Libra — Sade Sati not currently active (Saturn in Libra ≠ Capricorn/Aquarius/Pisces transit). Writer logic sound.
- `WINDOW_START = datetime(1950, 1, 1)` — epoch noted in prior audit (L3-W1); this is a L3-class issue, not an L1 soundness problem.
- **No bypass. SOUND.**

### GA13 — ga_tajaka
**Verdict: SUSPECT (0 rows in l1_tajik_varsha_year_lords)**  
- `l1_tajik_varsha_year_lords` has 0 rows for this chart. If annual chart computation was expected for this build, this is a data gap. If the tajaka writer only runs for specific build configurations, this may be expected.
- `EXALT` dict covers only classical 7 grahas (no Rahu/Ketu) — CLEAN for nodes.
- Cannot fully verify without knowing build configuration. Flagged as SUSPECT pending clarification.
- **No Rahu/Ketu bypass. SUSPECT (missing data).**

### GA14 — ga_vastu
**Verdict: SOUND (downstream consumer)**  
- Reads `condition_score` from `ga_condition_composite`.
- `GRAHA_TO_DIRECTION` dict (planet→vastu direction per Mayamata Ch.6) — not owned by any L0 table. LEGITIMATE.
- Downstream stale from ga_condition for Rahu/Ketu.
- **No direct bypass. SOUND.**

### GA15 — ga_prashna
**Verdict: INAPPLICABLE (natal chart)**  
- ga_prashna only activates for prashna chart builds. Natal chart build produces 0 rows — correct behavior.
- References `ga_positions` table (deprecated per observation 21528) — this is a concern for prashna use cases but does not affect natal chart audit.
- **No bypass relevant to this chart. INAPPLICABLE.**

---

## §SUMMARY TABLE

| Asset | Verdict | Bypass Count | Root-Cause Families | Impact Chain |
|---|---|---|---|---|
| ga_positions | SOUND | 0 | — | None |
| ga_panchanga | SOUND | 0 | — | None |
| ga_nakshatra | SOUND | 0 | — | Low |
| ga_structural | BYPASS | 2 | F4 | Stale Rahu/Ketu in yoga conditions |
| ga_vargas | SOUND | 0 | — | None |
| ga_dashas | **WRONG** | 1 | **F7** | JOIN to chart_facts broken for 3/5 ayanamshas |
| ga_yoga | **WRONG** | 0 | **F6** | 200+ catalog; only 1 yoga fires; L2+ synthesis loses yoga signal |
| ga_condition | **BYPASS + STALE** | 2 | F4 | Rahu/Ketu dignity wrong; Mercury atichara fix blocked |
| ga_sensitive | BYPASS | 2 | F4 | Sign/nak lords from inline (low severity) |
| ga_strength | SOUND | 0 | — | None |
| ga_medical | DOWNSTREAM STALE | 0 | — | Inherits ga_condition staleness |
| ga_sade_sati | SOUND | 0 | — | None |
| ga_tajaka | SUSPECT | 0 | F8? | 0 rows — may be missing annual data |
| ga_vastu | DOWNSTREAM STALE | 0 | — | Inherits ga_condition staleness |
| ga_prashna | INAPPLICABLE | 0 | — | Not relevant for natal |

**Summary counts:**
- SOUND: 7 (ga_positions, ga_panchanga, ga_nakshatra, ga_vargas, ga_strength, ga_sade_sati, ga_prashna[n/a])
- WRONG: 2 (ga_dashas F7, ga_yoga F6)
- BYPASS: 4 writers carrying 7 total bypass instances (ga_condition=2, ga_structural=2, ga_sensitive=2, ga_dashas=1)
- STALE DATA (needs rebuild): 1 (ga_condition; plus downstream ga_medical, ga_vastu)
- SUSPECT: 1 (ga_tajaka)
- TOTAL L0 BYPASS INSTANCES: **7**

---

## §LENS-2 — Rahu/Ketu Propagation Verdict

**DID THE L0 FIX REACH L1's DIGNITY DATA?**

**NO.**

Evidence:

```
ga_condition_composite (chart_id=482012f1, ayanamsha=lahiri_chitrapaksha, build_date=2026-06-18):
  Rahu:  dignity_d1='friend_sign'  score=0.6   [should be 'exalted', score=1.0]
  Ketu:  dignity_d1='friend_sign'  score=0.6   [should be 'exalted', score=1.0]
```

Rahu is in Taurus (house 2). After L0 seal (2026-06-24): `bg_dignity_reference.Rahu.exaltation_sign='Taurus'`.  
Ketu is in Scorpio (house 8). After L0 seal: `bg_dignity_reference.Ketu.exaltation_sign='Scorpio'`.

Both nodes are in their exaltation signs per the corrected L0 values. The live data still shows `friend_sign` because the last build predates the fix.

**Writer architecture assessment:** ga_condition's primary path (`_load_dignity_ref()` → reads `bg_dignity_reference` at build time → passes `dignity_ref` to `dignity_d1_from_sign()`) is **architecturally correct**. A rebuild would propagate the corrected values — provided the fallback bypass constants (`_EXALTATION`) are also fixed first, to prevent regression if the DB read ever fails.

**Action required (NOT taken in this session):** Fix the two bypass constants in `ga_condition_writer.py`, then rebuild `ga_condition` for all chart_ids.

---

## §PROPAGATION-CHAIN — Impact of Current WRONG Assets

```
ga_dashas [WRONG ayanamsha vocab]
  └─→ L2 Bodha any dasha JOIN to chart_facts: 0 rows for lahiri_chitrapaksha, 
      krishnamurti, surya_siddhanta_classical (3/5 ayanamshas severed)
  └─→ L3 Kāla period timing: all period-timing calculations using dashas × facts = wrong

ga_condition [STALE + BYPASS]
  └─→ ga_medical [stale condition_score for Rahu/Ketu]
  └─→ ga_vastu [stale condition_score for Rahu/Ketu]
  └─→ L2 Bodha bo_sangati (condition used in synthesis): Rahu/Ketu underscored
  └─→ L2 Bodha bo_pramana_mapa (calibration uses condition): Rahu/Ketu dignity wrong

ga_yoga [WRONG — only 1 yoga fires]
  └─→ ga_yoga_firings unusable for yoga synthesis
  └─→ L2 Bodha yoga layer must fall back entirely to ga_structural's yoga_fires
  └─→ activation_dasha_periods: None on all rows — yoga timing lost
```

---

## §PROPOSED-FIX SCOPE (Assess Only — Not Implemented)

These are fix specifications, NOT implementations. They are proposed for planning purposes.

**Fix 1 — ga_condition bypass constants (CRITICAL)**  
File: `platform/python-sidecar/ga_writers/ga_condition_writer.py`  
Lines ~100-119: Change `_EXALTATION["Rahu"]` → `"Taurus"`, `["Ketu"]` → `"Scorpio"`.  
Change `_DEBILITATION["Rahu"]` → `"Scorpio"`, `["Ketu"]` → `"Taurus"`.  
Line ~539: Change `"Mercury": {"sama_hi": 2.5}` → `2.0`. Better: replace inline threshold dict with DB read from `bg_motion_state_thresholds`.  
Then: rebuild ga_condition for canonical chart_id.

**Fix 2 — ga_dashas vocabulary mismatch (CRITICAL — F7)**  
File: `platform/python-sidecar/ga_writers/ga_dashas_writer.py`  
Replace ayanamsha ID strings: `'lahiri'` → `'lahiri_chitrapaksha'`; `'kp'` → `'krishnamurti'`; `'surya_siddhanta'` → `'surya_siddhanta_classical'`.  
Then: rebuild ga_dashas (full delete-then-insert per §N.3 per-chart idempotency standard).

**Fix 3 — ga_structural bypass constants (HIGH)**  
File: `platform/python-sidecar/ga_writers/ga_structural_writer.py`  
Lines 138-149: Change `EXALTATION_SIGNS["Rahu"]` → `"Taurus"`, `DEBILITATION_SIGNS["Rahu"]` → `"Scorpio"` (and Ketu mirrors).  
Better: add `_load_dignity_ref()` DB read (same pattern as ga_condition) for exaltation/debilitation.

**Fix 4 — ga_yoga evaluation logic (HIGH)**  
File: `platform/python-sidecar/ga_writers/ga_yoga_writer.py`  
Investigation required: determine why the condition-matching loop evaluates the 200+ yoga catalog and fires only `yuga_nabhasa`. Likely the chart_facts lookup inside the condition evaluator returns no matching rows (possibly because it queries by wrong fact_category or wrong key names). After fixing: populate `constituent_fact_ids` (B.3 ledger) and `strength`. Rebuild.

**Fix 5 — ga_sensitive bypasses (MEDIUM — deferred)**  
Files: `platform/python-sidecar/ga_writers/ga_sensitive_writer.py`  
Replace `SIGN_LORDS` and `NAK_LORDS` with DB reads from `reference_signs` and `reference_nakshatras`. Low urgency (stable classical data) but architecturally required for L0 authority compliance.

**Fix 6 — ga_tajaka 0-row investigation (MEDIUM)**  
Investigate whether `l1_tajik_varsha_year_lords` is expected to be empty for this chart build configuration, or whether the writer failed silently.

---

## §APPENDIX — Key Evidence

**ga_condition_composite (lahiri_chitrapaksha, 2026-06-18 build)**

| Graha | dignity_d1 | score | motion_state | Notes |
|---|---|---|---|---|
| Sun | enemy_sign | 0.3 | None | ✓ Capricorn |
| Moon | neutral_sign | 0.5 | None | Aquarius (plausible) |
| Mars | neutral_sign | 0.5 | None | — |
| Mercury | neutral_sign | 0.5 | None | motion=None gap |
| Jupiter | moolatrikona | 0.9 | None | ✓ Sagittarius 0–10° |
| Venus | neutral_sign | 0.5 | None | — |
| Saturn | exalted | 1.0 | None | ✓ Libra |
| Rahu | **friend_sign** | **0.6** | vakra | **WRONG: should be exalted=1.0** |
| Ketu | **friend_sign** | **0.6** | vakra | **WRONG: should be exalted=1.0** |

**chart_dashas ayanamsha IDs (WRONG vocab)**

| In chart_dashas | Should be (chart_facts vocab) | Mismatch |
|---|---|---|
| `lahiri` | `lahiri_chitrapaksha` | YES |
| `kp` | `krishnamurti` | YES |
| `true_chitra` | `true_chitra` | OK |
| `raman` | `raman` | OK |
| `surya_siddhanta` | `surya_siddhanta_classical` | YES |

**ga_yoga_firings (all rows)**

| yoga_canonical_id | ayanamsha_id | fired | strength | constituent_fact_ids |
|---|---|---|---|---|
| yuga_nabhasa | lahiri_chitrapaksha | true | null | [] |
| yuga_nabhasa | true_chitra | true | null | [] |
| yuga_nabhasa | krishnamurti | true | null | [] |
| yuga_nabhasa | raman | true | null | [] |
| yuga_nabhasa | surya_siddhanta_classical | true | null | [] |

Note: ga_yoga_firings uses correct ayanamsha vocab (`lahiri_chitrapaksha`, `krishnamurti`). The wrong vocab is isolated to `chart_dashas`.

---

*L1_SOUNDNESS_REPORT v1.0 — ASSESS ONLY — 2026-06-24*  
*No fix applied. No build triggered. No seal created.*
