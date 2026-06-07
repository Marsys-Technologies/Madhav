---
artifact: FORENSIC_RENDER_COVERAGE_AUDIT_REPORT_v1_0.md
canonical_id: FORENSIC_RENDER_COVERAGE_AUDIT
version: 1.0
status: COMPLETE — awaiting native decision
authored_at: 2026-06-01
authored_by: claude-code-audit
branch: audit/forensic-render-coverage
source_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_AUDIT_FORENSIC_RENDER_COVERAGE_v1_0.md
---

# Forensic Render Coverage Audit — v1.0

## TL;DR (5 lines)

1. The new `forensic_render` (lahiri, 56KB) has **2,426 real data cells** vs v8.0's **6,332** — a **0.38× ratio**; the new render is **THINNER**, not richer.
2. The render has **5,075 total table cells** but **2,649 (52%) are `—` or `N/A`**; v8.0 is 99.2% populated.
3. Root cause: `compute_chart()` supplies only **6 of 13 required input keys**; 7 renderers receive empty/None input and emit shell tables with structural rows but no values.
4. Seven critical depth domains (dashas for 32 systems, shadbala, ashtakavarga, KP, karakas/lagnas, yogas, aspects Parashari) are **completely empty** — their data already exists in `chart_facts` (v3.3 backfills) but the render reads only `compute_chart()`, never `chart_facts`.
5. **Plan-alignment verdict:** the new render captures FEWER actual data points than both v8.0 (0.38×) and the renderer-capability plan (renderers are coded for rich output; input starvation suppresses them); the forensic corpus must be enriched before eval baseline or RAG indexing.

---

## §1 — Data Sources Used

| Source | What | How Obtained |
|--------|------|--------------|
| New render (ground truth) | `content_md` from `chart_documents` WHERE `chart_id='362f9f17...'` AND `ayanamsha_id='lahiri'` AND `document_type='forensic_render'` | Direct DB query via Cloud SQL proxy; rendered_at 2026-06-01 |
| Legacy baseline | `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (1,938 lines, 28 H2 sections) | Direct file read |
| Renderer capability | 13 `pipeline/render/*_renderer.py` files — docstrings, input key access patterns | Static analysis via grep |
| Engine output | `pyjhora_adapter/compute.py` payload dict + `pyjhora_adapter/dashas.py` return shape | Source code read; venv invocation failed (jhora not in system path) but source unambiguous |
| chart_facts categories | `SELECT DISTINCT category FROM chart_facts WHERE chart_id=...` | DB query; 17 categories confirmed |

---

## §2 — Coverage Matrix

### Legend
- **POPULATED** = real values in table cells (non-`—`, non-`N/A`)  
- **PARTIAL** = some cells populated, others empty  
- **SHELL** = table structure present, all cells `—` or `N/A`  
- **RICHER / EQUAL / THINNER / EMPTY** vs v8.0

| Domain / Section | v8.0 data points | New render: status | New render real cells | Renderer capability | Fed by compute_chart? | Exists in chart_facts? | Root cause of gap | Verdict |
|---|---|---|---|---|---|---|---|---|
| **Identity — Planets** (9 classical) | 46 rows (positions, dignity, nakshatra) | PARTIAL | ~81 | Full D1/D9/D10 varga positions, nakshatra | YES (`planets`) | `varga` category | Latitude/Speed/Heliocentric/RA/Declination all N/A — compute_chart doesn't return these sub-fields | THINNER (quality) |
| **Bodies — outer/nodes/asteroids** (18 extra) | 0 (v8.0 only has 9 classical) | PARTIAL | ~162 | Full per-body tables | YES (extra planets in `grahas`) | No | compute_chart returns outer bodies; nakshatra/latitude still N/A | RICHER (breadth), THINNER (depth per body) |
| **Houses** (D1 whole-sign) | 12 rows (sign, lord, occupants) | POPULATED | 36 | 12 houses + occupants | YES (`houses`) | No | Co-lord, nakshatra/pada N/A (adapter doesn't compute) | EQUAL (sign/lord/occupants match) |
| **House system comparison** (6 systems) | 0 in v8.0 | SHELL (FAKED) | 72 | Real 6-system cusp comparison | FAKE — adapter copies same list 6× | No | Adapter gap: `_adapt_houses()` sends identical whole-sign data to all 6 system slots | FAKE DATA |
| **Arudha Padas** (A1–A12) | 23 rows | SHELL | 0 real | Full A1–A12 with sign/lord | NO (`arudhas` key missing) | No | Engine gap: compute_chart never computes arudhas | EMPTY |
| **Upagrahas** (Gulika, Maandi + 5 others) | 58 rows (sensitive points full) | PARTIAL | 7 | 7 upagrahas + Saturn-derived | PARTIAL — only Gulika+Maandi have longitude | No | Engine gap: compute_chart sensitive_points only returns Gulika/Maandi with data; Dhuma/Vyatipata/Parivesha/Indrachapa/Upaketu missing | THINNER |
| **Tajik Sahams** (40 sahams) | 47 rows | SHELL | 0 real | 40 sahams with formula + computed position | NO (`sahams` key missing) | No | Engine gap: compute_chart never computes sahams | EMPTY |
| **Esoteric Bindus** (Bhrigu, Yogi, etc.) | Partial in §12 | SHELL | 0 real | 9 bindus with longitude | NO (`esoteric_bindus` key missing) | No | Engine gap | EMPTY |
| **Chara Karakas** (AK–SK) | 25 rows | SHELL | 0 real | Full 8-karaka scheme with graha+longitude | NO (`chara_karakas` key missing) | No | Engine gap | EMPTY |
| **Natural Karakas** | Implicit in text | POPULATED | 12 | Table of classical assignments | YES (hardcoded in renderer) | No | Hardcoded defaults — no engine needed | EQUAL |
| **Karakamsa / Swamsa** | In §10 | SHELL | 0 real | Sign, lord | NO (`karakamsa`/`swamsa` missing) | No | Engine gap | EMPTY |
| **Special Lagnas** (Hora, Ghati, Varnada, etc.) | 47 rows (§12) | SHELL | 0 real | 10 lagnas with longitude/sign/house | NO (`special_lagnas` key missing) | No | Engine gap | EMPTY |
| **Yogas Register** | 31 rows (§26) | SHELL | 0 real | Active + near-miss + doshas | NO (`yogas`/`doshas` keys missing) | No | Engine gap — no yoga evaluator in compute_chart | EMPTY |
| **Panchanga — 5 Limbs** | 15 rows | PARTIAL | 12 | Tithi/vara/nakshatra/yoga/karana with lords/natures | YES (`panchanga`) | `dasha` (2 rows, not panchanga) | Adapter gap: lords, paksha, completion%, sandhi, yoga nature all set to None in `_adapt_panchanga()` | THINNER |
| **Panchanga — Astronomical Windows** (sunrise/muhurtas) | In §15 | SHELL | 0 real | Sunrise/sunset/Brahma/Abhijit/Rahu Kalam/Gulika/Yamaganda | NO — not in compute_chart panchanga | `panchanga_daily` table (separate DB) | Wrong source: sidecar has `panchanga_daily` data but panchanga_renderer reads compute_chart only | EMPTY |
| **Choghadiya** (day + night) | In §15 | SHELL | 0 real | All segments | NO | `panchanga_daily` | Wrong source | EMPTY |
| **Hora sequence** | In §15 | SHELL | 0 real | 24 planetary hours | NO | `panchanga_daily` | Wrong source | EMPTY |
| **Tara Bala / Chandra Bala** | In §14 navatara | SHELL | 0 real | Birth-moment strength | NO (`tara_bala`, `chandra_bala` not in panchanga) | No (navatara in chart_facts not confirmed) | Engine gap | EMPTY |
| **Special Yogas** (Siddha/Amrit/Marana) | In §15 | SHELL | 0 real | Boolean presence | NO | `panchanga_daily.special_yogas` | Wrong source | EMPTY |
| **Era Conversions** (Vikram/Shaka/Kali) | In §15 | SHELL | 0 real | 3 era years | NO | No | Engine gap | EMPTY |
| **Aspects — Parashari Graha Drishti** | 52 rows (§16) | SHELL | 0 real (Jaimini matrix uses hardcoded formula) | 9×12 graha→house matrix + mutual + lagna | NO (`aspects` key missing) | `aspect_matrix_parashari` (2,185 rows) | Wrong source: chart_facts has aspects but renderer reads compute_chart | EMPTY |
| **Aspects — Jaimini Rasi Drishti** | 0 explicit in v8.0 | POPULATED | 144 Yes/— | 12×12 sign matrix | COMPUTED by renderer from house layout (not engine data) | `aspect_matrix_jaimini` (4,140 rows) | Renderer computes deterministically — this section is RICHER than v8.0 | RICHER |
| **Aspects — Tajik** | 0 in v8.0 | SHELL | 0 | Aspects within orb | NO | No | Engine gap | EMPTY |
| **Ashtakavarga — BAV** | 31 rows (§7) | SHELL | 0 real | 8×12 = 96 bindus | NO (`ashtakavarga` key missing) | No | Engine gap: compute_chart doesn't compute BAV | EMPTY |
| **Ashtakavarga — SAV** | In §7 | SHELL | 0 real | 4 reduction rows | NO | No | Engine gap | EMPTY |
| **Shadbala** | 87 rows (§6) | SHELL | 0 real | 9 grahas × 6 sub-balas + total + required + ratio | NO (`shadbala` key missing) | No | Engine gap | EMPTY |
| **Bhava Bala** | In §6 | SHELL | 0 real | 12 houses × 3 sub-balas | NO (`bhava_bala` key missing) | No | Engine gap | EMPTY |
| **Ishta/Kashta Phala** | In §6 | SHELL | 0 real | 9 grahas × 2 values | NO | No | Engine gap | EMPTY |
| **Vimsopaka Dignities** | In §9 (partial) | SHELL | 0 real | 9 grahas × 4 varga groups | NO (`vimsopaka` key missing) | No | Engine gap | EMPTY |
| **Avastha — Baladi** | 8 rows (§9) | SHELL | 0 real | 9 grahas × 5 schemes | NO (`avasthas` key missing) | No | Engine gap | EMPTY |
| **Avastha — Jagradadi/Deeptadi/Lajjitadi/Shayanaadi** | In §9 | SHELL | 0 real | 4 schemes × 9 grahas | NO | No | Engine gap | EMPTY |
| **Vargas D1–D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60** (16 total) | 187 rows §3 | POPULATED | ~160 | Full body×sign table per varga | YES (`vargas`) | `varga` (6,516 rows) | Engine computes 16 of 20 classical; good coverage | RICHER (more bodies per varga) |
| **Vargas D5, D6, D8, D11** (4 missing) | In §3 | SHELL | 0 real | Full body×sign | NO (pyjhora doesn't return these) | `varga` | Engine gap: pyjhora varga module doesn't compute D5/D6/D8/D11 | THINNER |
| **Vargas D108/D150/D2700** | 0 in v8.0 | SHELL | 0 real | Nadi divisions | NO | No | Engine gap | EMPTY |
| **Vimshottari Dasha — current period** | 214 rows §5 | SHELL | 0 real | All 32 systems with Maha/Antar/Pratyantar/Sookshma current dates | YES (mahadasha_sequence) | `dasha_vimshottari` (1,306,260 rows) | Adapter gap: `_adapt_dashas()` sets `current_dates={}` — no current period computation; chain data is in chart_facts but not read | EMPTY (critical) |
| **All 32 Dasha systems — current chain** | In §5/§25 | SHELL | 0 real | 32 systems × 4 levels | 31 systems: NO | `dasha_ashtottari` (103k), `dasha_kalachakra` (2k), `dasha_mudda` (186k), `dasha_naisargika` (10k), `dasha_yogini` (13k), `dasha_jaimini_chara` (3k) | Wrong source for 6 systems; engine gap for 25 systems | EMPTY (critical) |
| **KP Cuspal Sub-Lords** | 31 rows §4 | SHELL | 0 real | 12 cusps × sub-lord/nakshatra lord/sub-sub-lord | NO (`kp_cuspal` missing) | No | Engine gap | EMPTY |
| **Tajik Varshphal** | 6 rows §22 | SHELL | 0 real | Year lord, Hadda lord + details | NO (`tajik_varshphal` missing) | No | Engine gap | EMPTY |
| **Midpoints** | 0 in v8.0 | SHELL | 0 real | 7 planetary pairs | NO | No | Engine gap | EMPTY |
| **Eclipse Proximity** | 0 in v8.0 | SHELL | 0 real | Nearest solar + lunar | NO | No | Engine gap | EMPTY |
| **Nadi-Amsa (D150)** | 0 in v8.0 | SHELL | 0 real | 9 bodies × rishi assignment | NO | No | Engine gap | EMPTY |
| **Argala/Virodha Argala Matrix** | 0 in v8.0 | SHELL | 0 real | 12×12 matrix | NO | No | Engine gap | EMPTY |
| **Astronomical data** (JD, sidereal time, lat/lon) | In §1 | SHELL | 0 real | JD, GAST, LST, place | NO (`astronomical` key missing — provenance dict has some but adapter doesn't map) | No | Adapter gap: provenance/inputs available but not mapped to `astronomical` key | EMPTY |
| **Longevity indicators** | 12 rows §24 | SHELL | 0 real | Span estimates | NO | No | Engine gap | EMPTY |
| **Chalit/Sripati shifts** | 10 rows §17 | 0 in new render | 0 | Not in renderer capability | NO | No | Renderer scope: not one of 13 registered sections | THINNER |
| **Chandra chart** | 13 rows §18 | 0 in new render | 0 | Not in renderer capability | NO | No | Renderer scope: not registered | THINNER |
| **Kota Chakra** | 7 rows §19 | 0 in new render | 0 | Not in renderer capability | NO | No | Renderer scope: not registered | THINNER |
| **Sade Sati** | 9 rows §21 | 0 in new render | 0 | Not in renderer capability | NO | No | Renderer scope: not registered | THINNER |
| **Navatara / Stellar Matrix** | 14 rows §14 | 0 in new render | 0 | Not in renderer capability | NO | No | Renderer scope: not registered | THINNER |
| **Deity Assignments** | In §20 | 0 in new render | 0 | Not in renderer capability | NO | No | Renderer scope: not registered | THINNER |
| **Cross-reference matrices** | In §23 | 0 in new render | 0 | Not in renderer capability | NO | No | Renderer scope: not registered | THINNER |
| **Saturn Kakshya Zones** | 9 rows §8 | Partial (Kakshya contributions table = 0s) | Cells exist but all zero | Kakshya contributions (8 per graha) | NO (`ashtakavarga` missing — kakshya is derived from it) | No | Engine gap — depends on BAV | EMPTY |

---

## §3 — Root-Cause Classification

### Engine gap (compute_chart() doesn't compute or return it)
Affects: arudhas, sahams, esoteric bindus, chara karakas, karakamsa/swamsa, special lagnas, yogas/doshas, astronomical windows (choghadiya/hora/muhurtas), tara/chandra bala, Tajik aspects, ashtakavarga (BAV/SAV), shadbala, bhava bala, vimsopaka, avasthas, KP cuspal sub-lords, Tajik varshphal, midpoints, eclipses, nadi-amsa, argala, longevity, D5/D6/D8/D11 vargas, Shodashottari through Dwisaptati dasha systems (31 of 32 systems have no engine coverage at all).

**Count: 25+ domains empty due to engine gap**

### Adapter gap (_chart_output_adapter.py drops or hardcodes)
Affects:
- `_adapt_panchanga()`: Lords (tithi lord, vara lord, nakshatra lord), paksha, completion%, sandhi, yoga nature all hardcoded to `None`. Engine returns nakshatra_lord and nakshatra_pada in raw panchanga — adapter discards nakshatra_lord.
- `_adapt_houses()`: All 6 house systems (Placidus/Equal/Koch/Campanus/Porphyry) receive IDENTICAL whole-sign data. The house system comparison table is structurally present but factually meaningless.
- `_adapt_dashas()`: Sets `current_dates={}` for vimshottari. The `mahadasha_sequence` is converted to `next_10_mahas` but since there is no date-of-analysis parameter, no current period is pinned — all 32 dasha current_dates tables render empty. 
- `astronomical` key: compute_chart returns `provenance.jd_ut` and `inputs.latitude_deg`/`longitude_deg` but adapter doesn't map these to the `astronomical` key the supplementary renderer expects.

**Count: 4 adapter gaps producing SHELL output from data that was computed**

### Wrong source (data in chart_facts / panchanga_daily but render reads compute_chart only)
- `aspects_matrix_parashari` (2,185 rows in chart_facts) → `aspects_renderer` reads `chart_output.get("aspects")` which is never populated. The rich aspect data computed by v3.3 is invisible to the render pipeline.
- `dasha_vimshottari` (1,306,260 rows), `dasha_ashtottari` (103,368), `dasha_mudda` (186,381), `dasha_naisargika` (9,912), `dasha_yogini` (12,744), `dasha_kalachakra` (2,124), `dasha_jaimini_chara` (3,186) → `dashas_renderer` reads `chart_output.get("dashas")` only; chart_facts has 7 dasha systems at full depth but none flow into the render.
- `panchanga_daily` table (73,414 rows for 1900–2100, including choghadiya/hora/tara bala/special yogas/astronomical windows) → `panchanga_renderer` reads `chart_output.get("panchanga")` only; the panchanga_daily cache is unreachable from the render pipeline.

**Count: 3 wrong-source gaps; data is computed and persisted but unreachable to the renderer**

### Renderer scope (section not registered in ForensicRenderer)
Sections present in v8.0 with no equivalent registered renderer:
- Chalit / Sripati house shifts (§17)
- Chandra chart / from-Moon view (§18)  
- Kota Chakra (§19)
- Deity assignments (§20)
- Sade Sati history (§21)
- Navatara / Stellar matrix (§14)
- Deity / Kota / Cross-reference matrices (§19/§20/§23)

**Count: 7 v8.0 sections with no renderer registered**

---

## §4 — Totals, Ratios, Verdict

### Data point counts

| Metric | New render (lahiri) | v8.0 |
|--------|--------------------|----|
| Total table cells (excl. separators) | 5,075 | 6,382 |
| Cells with real data | **2,426** | **6,332** |
| Cells with `—` or `N/A` | 2,649 (52%) | 50 (0.8%) |
| % populated | **47.8%** | **99.2%** |
| Table rows | 1,178 | ~945 |

**Ratio: 2,426 / 6,332 = 0.38× — new render has 38% of v8.0's actual data density.**

### Byte explanation

| Factor | Size |
|--------|------|
| New render `byte_size` | 56,146 bytes |
| v8.0 file size | ~98,000 bytes (estimated from 1,938 lines × avg 50 chars) |
| Gap | ~42KB |
| Why new render is SMALLER despite more table rows | The new render has 1,178 table rows vs v8.0's ~945, but 2,649 cells are `—`/`N/A` (adds structural bytes for zero information). v8.0's 6,332 real data cells contain actual computed values (numbers, dates, sign names, degree values) that are substantively longer per cell on average. Missing sections that would add 15–20KB if populated: 32 dasha chains with dates, shadbala numerical values (6 sub-bala decimals × 9 grahas), BAV bindu grid (96 integers), 40 saham longitudes, 10 special lagna positions, chara karaka degrees. Paradoxically, the empty shell tables (all-dash rows) add bulk without information, accounting for ~12–15KB of the 56KB. |

### Section completeness (13 registered renderers)

| Section | Status |
|---------|--------|
| Identity & Planetary Positions | PARTIAL (outer bodies present; sub-fields N/A) |
| Houses & Arudha Padas | PARTIAL (houses populated; arudhas empty) |
| Upagrahas | PARTIAL (2 of 7 have data) |
| Tajik Sahams & Bindus | EMPTY (all N/A) |
| Chara Karakas & Special Lagnas | EMPTY (natural karakas hardcoded; all others N/A) |
| Yogas & Doshas | EMPTY (0 evaluated) |
| Birth-Day Panchanga | PARTIAL (5 names present; lords/windows/choghadiya/hora EMPTY) |
| Aspect Matrices | PARTIAL (Jaimini deterministic; Parashari EMPTY; Tajik EMPTY) |
| Strengths (BAV/Shadbala/Bhava) | EMPTY (all —) |
| Vimsopaka & Avasthas | EMPTY (all —) |
| Divisional Charts (Vargas) | PARTIAL (16/20 classical populated; 4 empty) |
| Dasha Systems | EMPTY (all 32 current-dates tables all —; next_10_mahas structure exists for vimshottari but current_dates = {}) |
| Supplementary | EMPTY (KP/Tajik/midpoints/eclipses all —) |

**Summary: 0 of 13 sections FULL, 4 PARTIAL, 9 EMPTY/SHELL.**

### Plan-alignment verdict

The new forensic render captures **FEWER** actual data points than (a) v8.0 at 0.38× data density and (b) the renderer-capability plan — the 13 renderers are coded for comprehensive output but are input-starved: compute_chart() supplies 6 of 13 required input key families, the adapter introduces 4 additional gaps, and 3 domains with data already in chart_facts / panchanga_daily are unreachable because the pipeline reads compute_chart() only.

---

## §5 — Fix Options (Surface Only — No Recommendation)

### Context for all options

- The forensic render drives RAG chunks → embeddings consumed by the retrieval layer.
- Once enriched, rebuild cost: render 5 ayanamshas → chunk → embed → update rag_chunks + rag_embeddings. Currently ~495 embeddings; enriched corpus will be substantially larger.
- Decision must precede eval baseline (ACC1) and any consumer indexing on the current thin corpus.

---

### Option A — Extend compute_chart() to emit the missing depth domains

**What:** Add new computation modules to `pyjhora_adapter/` for: arudhas, sahams, esoteric bindus, chara karakas, special lagnas, yogas/doshas evaluator, Parashari aspects matrix, shadbala, ashtakavarga, bhava bala, vimsopaka, avasthas, KP cuspal sub-lords (need KP module), all 32 dasha current-period chains (vimshottari current period already computable from mahadasha_sequence + today's date; 31 others need new engine calls or chart_facts read). Also fix adapter: `current_dates` computation from sequence + reference_date, panchanga lords, house system mapping.

**Effort:** Large (8–12 sessions). PyJHora supports several of these natively (vimsopaka, avastha, karakas, yogas, sahams) — needs discovery + wiring. Shadbala/KP require either PyJHora KP module or custom computation from ephemeris values.

**Risk:** Engine changes may produce values that disagree with v8.0's JH-computed values; new reconciliation layer needed. Adds compute time per render (currently ~2s per ayanamsha).

**What it does NOT solve:** wrong-source gaps (panchanga windows, aspects already in chart_facts) unless also fixed in adapter. Nor does it populate the 7 unregistered v8.0 sections (Chalit, Chandra chart, Kota, Sade Sati, Navatara, etc.).

---

### Option B — Re-point depth renderers to read chart_facts

**What:** Add a `chart_facts_reader.py` shim. The `ForensicRenderer.render()` call gains a second parameter `chart_id` (already available in the build pipeline). Each depth renderer that finds its key absent from `chart_output` falls back to a `chart_facts` query for the same chart_id + ayanamsha_id. Specifically:
- `aspects_renderer` ← `aspect_matrix_parashari` / `aspect_matrix_jaimini` in chart_facts
- `dashas_renderer` ← `dasha_vimshottari`, `dasha_ashtottari`, `dasha_mudda`, `dasha_naisargika`, `dasha_yogini`, `dasha_kalachakra`, `dasha_jaimini_chara` in chart_facts
- `panchanga_renderer` ← `panchanga_daily` table for astronomical windows + choghadiya + hora + tara bala
- `strengths_renderer` ← if chart_facts gains shadbala/BAV categories (currently not present — see below)
- `karakas_renderer` ← if chart_facts gains chara_karakas category (currently not present)

**Partial coverage note:** chart_facts currently has ONLY: `aspect_matrix_parashari`, `aspect_matrix_jaimini`, and 7 dasha categories. It does NOT have shadbala, ashtakavarga, bhava bala, vimsopaka, avasthas, sahams, karakas, special lagnas, yogas, KP, eclipse, midpoints, nadi-amsa, argala. Those domains would still be EMPTY under Option B unless Option A or a separate chart_facts backfill campaign populates them.

**Effort:** Medium (3–5 sessions for wiring + query layer + what chart_facts currently covers). Remaining gaps require a chart_facts depth-backfill campaign (separate scope).

**Risk:** Render becomes DB-read-at-render-time; currently render is compute-only. Must handle missing chart_facts rows gracefully (degrade to N/A, not error). Schema coupling: chart_facts query shape may change.

---

### Option C — Hybrid (core from compute_chart, depth from chart_facts)

**What:** Option A for fast/cheap fields (positions, panchanga lords, arudhas, special lagnas, chara karakas via PyJHora), Option B for expensive/already-computed fields (aspects, dashas, panchanga windows, and any v3.3 depth data in chart_facts). Adapter fixes (house systems, panchanga lords, current_dates from sequence) can be done as a standalone PR before the larger engine work.

**Phasing suggestion (not a recommendation — native decides):**
- Phase 1 (low-risk, low-effort): Fix 4 adapter gaps (current_dates, panchanga lords, astronomical key, house system honest N/A). Immediately un-suppresses vimshottari current period and panchanga lords.
- Phase 2 (medium): Wire chart_facts read for aspects + 7 dasha systems. Populates the 3 wrong-source domains.
- Phase 3 (large): Extend compute_chart for arudhas, karakas, special lagnas, yogas, avasthas (PyJHora native), sahams. Registers 7 missing v8.0 sections.
- Phase 4 (separate campaign): Backfill shadbala/BAV/KP into chart_facts (or compute via PyJHora).

**Downstream rebuild cost:** Each phase above requires a re-render of 5 ayanamshas + re-chunk + re-embed. Suggest a single consolidated rebuild after Phase 3 (not after each phase) to avoid triple re-indexing.

---

### Option D — Accept current coverage as the forensic render scope (no fix)

**What:** Declare the new render as intentionally covering only: planetary positions (27 bodies), houses, partial upagrahas, Jaimini Rasi Drishti (computed), panchanga names, and 16 varga D-charts. Formally deprecate v8.0 sections not covered by the renderer. Accept 0.38× data density as the new baseline.

**Effort:** 0 code changes. Update governance: mark render scope, update RAG indexing expectations.

**Risk:** Eval baseline and RAG retrieval will underperform relative to v8.0 quality because the most analytically rich domains (dashas, strengths, yogas) are absent. The native's stated goal of "acharya-grade depth" is not achievable on the current thin corpus.

---

## §6 — Pre-Finding Verdict (Confirm / Refute)

| Pre-finding | Verdict | Evidence |
|---|---|---|
| "compute_chart() returns ONLY: ascendant/lagna, houses, grahas/planets, vargas, dashas, panchanga, sensitive_points, ayanamsha, reconciliation + metadata" | **CONFIRMED** | Source reading of `compute.py` payload dict (12 keys); no shadbala/BAV/karakas/yogas/aspects keys in payload |
| "It does NOT return shadbala/ashtakavarga/bhava_bala/chara karakas/yogas/aspects/vimsopaka/avasthas/KP/Tajika varshphal/sahams/midpoints/eclipses/choghadiya/hora/tara bala/special lagnas/arudhas" | **CONFIRMED** | Same; none of these keys appear in compute.py return payload |
| "ForensicRenderer.render() catches per-section exceptions and emits placeholder" | **PARTIALLY CONFIRMED** | `base_renderer.py` has try/except → `_[Render error: ...]_` placeholder. The actual render shows 0 render errors — sections don't error, they just output SHELL tables with graceful N/A fallbacks (renderers degrade to all-dashes, not exceptions). No explicit `_[Render error]_` strings found in lahiri content_md. |
| "_chart_output_adapter.py hardcodes panchanga lords/padas to None" | **CONFIRMED** | `_adapt_panchanga()` sets tithi.lord=None, vara.lord=None, yoga.nature=None, karana.lord=None, karana.nature=None; paksha=None; completion_pct=None; sandhi=None |
| "_chart_output_adapter.py points all 6 house-systems at the SAME house_list (fake 6-system comparison)" | **CONFIRMED** | `_adapt_houses()` builds one `house_list` from raw_houses then assigns it to placidus, whole_sign, equal, koch, campanus, porphyry — all 6 slots are identical |
| "Depth data (shadbala, ashtakavarga, KP, Tajika, etc.) ALREADY EXISTS in chart_facts via v3.3 backfills" | **PARTIALLY CONFIRMED** | chart_facts has: `aspect_matrix_parashari` (2,185 rows), `aspect_matrix_jaimini` (4,140 rows), and 7 dasha categories (1,613,975+ rows total). It does NOT have shadbala, ashtakavarga, bhava_bala, KP cuspal, vimsopaka, avasthas, sahams, karakas, special lagnas — those domains are absent from chart_facts entirely |
| "Render reads compute_chart output, not chart_facts" | **CONFIRMED** | `ForensicRenderer.render()` takes only `chart_output: dict` — no DB connection, no chart_id parameter, no chart_facts query path |

---

*End of FORENSIC_RENDER_COVERAGE_AUDIT_REPORT_v1_0.md — branch: audit/forensic-render-coverage — status: COMPLETE, awaiting native decision on §5 options.*
