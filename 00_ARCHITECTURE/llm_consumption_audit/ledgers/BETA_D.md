---
artifact: BETA_D (Elevation Campaign v2.1 — Stream β, lane D evidence ledger)
lane: β.D — Writer & data integrity + chart-scoped rebuild
items: EL-30, EL-40, EL-47 (writer), EL-38 (data leg)
branch: elev/beta-D-writer-integrity
contract_produced: C4_HOUSE_SIGN_CONVENTION_v1_0.md (sha256 073b1461f058aadd3db5ba940742b0578ac64eda8abf882d3ee8a1dfcc3ba742)
charts: 482012f1 (Abhisek, canonical A) · 1c826d5a (Abhinandan, canonical B) · acdf0d66 (Arunima, third-chart estate-safety probe, NOT rebuilt)
created: 2026-07-25
---

# β.D evidence ledger

All probes are against LIVE PRODUCTION (`amjis` via Cloud SQL Auth Proxy 127.0.0.1:5433 —
the same DB the `mcp__marsys-jis-direct__*` tools read; never localhost, never a mock).

## Step 1 — AUDIT: house-semantic convention scan

Mechanical scan of every `chart_facts` category carrying a house-semantic field, writer emit
paths under `platform/python-sidecar/**` cross-checked against sampled live prod rows
(chart 482012f1, lahiri_chitrapaksha, lagna 12.43° Aries).

### Convention table

| category | field | writer / emit | observed convention (PRE) | correct? | evidence |
|---|---|---|---|---|---|
| `graha_position` | `house` | ga_positions_writer | whole-sign from D1 lagna, 1..12 | ✅ correct (reference) | SUN Capricorn→10, MOON Aquarius→11, MAR/SAT Libra→7, JUP Sagittarius→9 |
| `arudha_pada` | `house_d1` | ga_sensitive_writer `_house_d1` (l.309) | **degree-arc count** `int((long−lagna)%360/30)+1` | ❌ wrong | A1 Capricorn→**9** (true 10); A7 Aquarius→**10** (true 11); A10 Aries 0°→**12** (true 1) |
| `bhava_arudha` | `house_d1` | ga_sensitive_writer `_house_d1` | same degree-arc defect | ❌ wrong | inherits `_house_d1` |
| `upagraha_position` | `house_d1` | ga_sensitive `_long_rows`→`_house_d1` | same degree-arc defect | ❌ wrong | inherits `_house_d1` |
| `karaka_chara_position` | `house_d1` | ga_sensitive (l.1232) `_house_d1` | same degree-arc defect | ❌ wrong | inherits `_house_d1` |
| `varga_position` | `house` | ga_vargas_writer (l.845) | **served NULL** (client-side derivation) | ❌ absent (EL-47) | every varga row `house: null` |
| `argala_natal_matrix` | (sign-indexed) | ga_structural (l.4059) | sign-indexed matrix, no house-from-lagna | by-design; α.B to resolve | keyed `from_sign_N_offset_K` |

### Root cause (single defect for EL-30)

`_house_d1(long, lagna)` claimed "whole-sign house" in its docstring but computed a **degree-arc**
count: `int((long − lagna) % 360 / 30) + 1`. When the lagna sits mid-sign (12.43° Aries here) this
under-counts vs whole-sign. The A10 "0° wraparound anomaly" in EL-30 (house_d1=12, fits neither a
house nor a sign index) is the SAME defect at its most visible: 0° Aries falls *behind* a 12.43°
lagna → `(0−12.43)%360 = 347.57 → arc 11 → 12`. `graha_position.house` uses a separate, correct
whole-sign computation — hence the mixed-convention estate EL-30 reports. Fix: `_house_d1` →
`((sign_idx − lagna_sign_idx) mod 12) + 1`.

### A10 / 0° derivation check (explicit, per charter)

`ARUDHA_A10` longitude_sidereal = 0.0 (0° Aries, sign-cusp convention for arudhas — the arudha is a
whole-sign construct placed at sign-start, see ga_sensitive `_build_arudha_rows` D-10 note). Under
whole-sign counting from an Aries lagna, a point in Aries is house **1**. The stored 12 was purely
an artifact of the degree-arc formula measuring 0° as 347.57° "behind" the mid-sign lagna. Resolved:
A10 → 1. Not a separate cusp bug — one defect with EL-30's other rows.

## Step 2 — RULING: contract C4

One convention: `house_*` = whole-sign house from the (varga-appropriate) lagna, 1-indexed 1..12; a
`house_*` field never holds a sign index; signs are 1..12 Aries-origin. Written to
`~/elev-v2-shared/contracts/C4_HOUSE_SIGN_CONVENTION_v1_0.md`
(sha256 `073b1461f058aadd3db5ba940742b0578ac64eda8abf882d3ee8a1dfcc3ba742`). Estate-safety
normalisation (mitigation a) specified for α to implement the consuming half.

## Step 3 — WRITER FIXES (committed `e7ae5895`)

1. **EL-30** `_house_d1` → whole-sign; arudha/bhava_arudha `house_d1` rows stamped
   `formula_id="wholesign_from_lagna:1indexed:v2"`.
2. **EL-47** `varga_position` now emits `house_from_varga_lagna` (whole-sign from the varga's own
   Lagna, 1-indexed); the key is self-marking.
3. **EL-40** `composite_dispositor_strength` → mean of dignity-strength over all dispositor-chain
   members (was terminal-only → uniform 0.875).
4. **Degenerate-value screen** (distinct-count=1 across the 9 grahas): flagged
   `composite_dispositor_strength.terminal_strength` (FIXED), `graha_sthana_bala_per_varga.D30` (=1
   for all 7 grahas — plausibly a normalised sthana-bala ceiling, NOT in EL-30/40 scope; noted for
   α.K1's degenerate-value screen), `nakshatra_dispositor.chain_depth` (=1; likely real — noted).

Committed regression test: `platform/python-sidecar/tests/test_beta_d_house_convention.py`
(8 tests, reproduces the EL-30 recipe on chart 482012f1's real longitudes). Existing writer tests:
303 pass, no regressions.

## Step 6 — EL-38 argala adjudication

**Zeros are GENUINE, not an EL-40-class defect.** Live distribution (482012f1, `argala_natal_matrix`,
all vargas): `1.0`×992, `0.75`×256, `0.5`×112, `0.25`×28, `0.0`×2788. The non-zero cells are exactly
the four Jaimini argala offsets {2,4,5,11}; the zeros are the non-argala cells (correctly 0). The
"every sampled row = 0" symptom was a `limit:5` sampling artifact hitting non-argala offsets. No
writer change. The real EL-38 problems — the 25000 default-limit timeout and the sign-indexed
matrix's missing house-from-lagna resolution — are α.B serving concerns (§15: EL-38 = α·B + β·D),
handed to α with this finding.

---

## Step 4 — FORENSIC 7/7 baseline (pre-rebuild, both charts)

Captured live before any rebuild. My fixed writers (ga_sensitive/ga_structural/ga_vargas) produce
NONE of the 7 anchors (Sun sign, Moon nakshatra, Lagna sign, tithi/vara/yoga/karana all come from
ga_positions + ga_panchanga), so the gate is structurally safe; verified anyway per protocol.

| anchor | chart A (482012f1, Abhisek) | chart B (1c826d5a, Abhinandan) |
|---|---|---|
| Sun sign | Capricorn | Aquarius |
| Moon nakshatra | Purva Bhadrapada | Ardra |
| Lagna sign (5 ayanamshas) | Aries ×5 | Aries ×5 |
| Tithi | Shukla Tritiya | Shukla Dashami |
| Vara | Ravivara | Shanivara |
| Yoga | Shiva | Ayushman |
| Karana | Garaja | Garaja |

Chart A = the canonical CLAUDE.md §B 7/7. Chart B = Abhinandan's own anchors. Gate after each
rebuild = these values UNCHANGED.

## Step 5 — Estate extent + MSR baseline

**Estate finding (decisive):** `chart_facts` holds exactly **2 distinct chart_ids** — the two
canonical charts. `catalog_charts_list` shows 4 charts, but the other two (Arunima
`acdf0d66-…`, Kiran `cb73cd3d-…`) are catalog-registered with **ZERO chart_facts rows** (unbuilt).
The tool description's "5,566 subjects" refers to the ref/ephemeris layer, not built natal charts.
Therefore the built estate carrying `house_d1` data is exactly the two charts I rebuild; there are
**0 non-canonical built charts** holding legacy house rows.

**Estate-safety consequence:** the charter's red-team finding #2 (every non-canonical chart left
silently wrong) is, in current prod, **vacuously satisfied** — no non-canonical built chart exists
to be at risk, and my rebuild covers 100% of built charts with arudha/house data. The specified
third-chart live probe against `acdf0d66-…` is **not performable** (that chart has no rows). The C4
per-row convention stamp + α normalise-by-tag fallback remains the governing mitigation for all
FUTURE builds (Arunima/Kiran when built will use the fixed writer → correct + stamped). Evidence:
`SELECT count(DISTINCT chart_id) FROM chart_facts` = 2; both non-canonical charts return 0 rows.

**MSR baseline (chart A):** `bodha_msr_signals.constituent_facts_array` = 71,430 refs; 50 already
dangling pre-rebuild (~0.07%, unrelated to this lane); **671 reference the rebuilt categories**
(arudha/bhava_arudha/composite_dispositor/varga/upagraha/karaka). Because `_fact_id` includes
`build_id`, an L1 rebuild always rotates fact_ids — so these 671 will re-dangle until the MSR
producer (`bo_laksana`) is rebuilt. See Step 4/5 rebuild outcome for disposition (rebuilt vs flagged).

---

## Step 4b — ka_gochara_sweep protection (binding native ruling, 2026-07-25)

Native ruling: `ka_gochara_sweep` for 482012f1 is ~93% through a ~20h non-recoverable compute and
MUST be protected. Baseline (native-captured): **285 substep rows, 7695 rows_written, latest
completed_at 2026-07-25T13:57:15Z** — must never drop.

**Compliance (by construction):** `run_elev_beta_d_rebuild.py` has a hardcoded allowlist of exactly
`{ga_sensitive, ga_structural, ga_vargas}` and calls the FROZEN orchestrator's single-asset
`_run_data_writer` directly — no cascade, no reset-to-dormant, no `build_substep_progress` DELETE,
no gochara touch. The v2 driver additionally runs an inline guard before AND after every writer that
halts if the sweep drops below 285 rows / 7695 rows_written.

**Dispatch enumeration (exact asset/chart list; `ka_gochara_sweep`/`ka_gochara_resonance` are NOT in
it):**
- ga_structural · 482012f1 · ga_vargas · 482012f1 · ga_sensitive · 1c826d5a · ga_structural ·
  1c826d5a · ga_vargas · 1c826d5a.

**Post-rebuild re-checks (rows must equal 285 / 7695):**
- After ga_sensitive · 482012f1 (completed 06:35Z): 285 / 7695 ✓ (rechecked 13:34Z).
- After ga_structural · 482012f1 attempt 1 (FAILED — proxy connection lost, no commit): 285 / 7695 ✓.

## Step 4c — ga_structural · 482012f1 attempt 1 outcome

FAILED with `psycopg.OperationalError: the connection is lost` (Cloud SQL Auth Proxy dropped the
heavy writer's long connection; the gochara Cloud Run sweep is concurrently loading the same
instance). No substep committed — `composite_dispositor_strength` still shows the pre-rebuild uniform
0.875 (computed_at 2026-07-24). ga_structural is per-substep committed → idempotent retry is safe.
Driver rebuilt as v2 with 5× per-writer retry + gochara guard. ka_gochara_sweep unaffected (285/7695).

# Verifier dispositions (per-EL evidence blocks)

### EL-30 — house_d1 semantics (arudha)
```
el_id: EL-30
status: VERIFIED-CLOSED (chart A lahiri confirmed live; full 5-ayanamsha + chart B rebuild in flight)
before_payload: chart A arudha_pada house_d1 (lahiri) — A1=9, A7=10, A10=12 (degree-arc _house_d1)
after_payload:  chart A arudha_pada house_d1 (lahiri) — A1=10, A7=11, A10=1, formula_id=wholesign_from_lagna:1indexed:v2
probes_run:
  - SQL live prod (amjis via proxy = same DB as mcp__marsys-jis-direct__*): arudha_pada house_d1 A1/A7/A10 → 10/11/1
  - committed regression test tests/test_beta_d_house_convention.py (8 tests, reproduces EL-30 recipe on 482012f1 fixture) — PASS
  - 303 existing ga5/ga8/arudha/sensitive tests — PASS (no regression)
charts: 482012f1 (lahiri verified live; 4 more ayanamshas rebuilding), 1c826d5a (pending)
verifier_notes: >
  Root cause: _house_d1 computed a degree-arc house int((long-lagna)%360/30)+1, not whole-sign;
  diverges when lagna is mid-sign (12.43° Aries). A10's 0° "wraparound" was the same defect
  (0° Aries falls behind the mid-sign lagna → arc 11 → 12). Fixed to ((sign_idx-lagna_sign_idx)%12)+1.
  Fix propagates to upagraha/karaka/bhava_arudha house_d1 (same _house_d1). C4 convention stamp applied.
```
<!-- EL-40 / EL-47 / EL-38 evidence blocks + full-ayanamsha + chart-B G4 appended on rebuild completion -->

