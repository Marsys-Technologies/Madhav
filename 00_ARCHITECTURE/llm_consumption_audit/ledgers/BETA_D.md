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
EL-30 full completion: chart A all 5 ayanamshas rebuilt (95 stamped arudha house rows, 0 legacy);
chart B rebuilt (arudha A1=11/A7=5/A10=6, stamped v2). FORENSIC 7/7 PASS both charts. **VERIFIED-CLOSED both charts.**

### EL-40 — composite_dispositor_strength discrimination
```
el_id: EL-40
status: VERIFIED-CLOSED (both charts)
before_payload: chart A composite_dispositor_strength = 0.875 for all 9 grahas (distinct=1; terminal-only formula, every chain sinks to Jupiter own-sign)
after_payload:  chart A = 6 distinct values {0.5938,0.625,0.6875,0.7188,0.7917,0.875}; chart B = 5 distinct {0.4167,0.4375,0.45,0.55,0.5625}
probes_run:
  - SQL live prod both charts: count(DISTINCT fact_value_num) = 6 (A), 5 (B) — verify bar (>=3) met
  - regression test TestEL40DispositorChainMean through the real _build_structural_relationship_rows — PASS
charts: 482012f1, 1c826d5a
verifier_notes: mean of dignity-strength over all dispositor-chain members (same dignity→strength map, no new constants). source_calculation stamped ga_structural.dispositor_chain_mean_dignity_strength_v2.
```

### EL-47 — house_from_varga_lagna persistence
```
el_id: EL-47
status: VERIFIED-CLOSED (both charts)
before_payload: varga_position served house:null (client-side derivation required)
after_payload:  chart_divisionals now carries fact_key 'house_from_varga_lagna' (1450 rows/chart); served in ganita_chart_facts_get(divisional_chart=D9).divisional_facts
probes_run:
  - SQL spot-check D9 chart A: house_from_varga_lagna == ((sign_id-lagna_sign_id)%12)+1 for all 10 bodies (every ok=true): LAGNA=1,SUN=1,MER=7,SAT=10,MAR=9,VEN=3,JUP=12,MOON=12,RAH=12,KET=6
  - MCP live: ganita_chart_facts_get(divisional_chart=D9) divisional_facts surfaces varga_position.house_from_varga_lagna
  - regression test TestEL47VargaHouse — PASS
charts: 482012f1, 1c826d5a
verifier_notes: >
  Divisional facts live in the chart_divisionals table (not chart_facts). The new key is
  self-marking (no legacy house_from_varga_lagna exists). The varga_position.house COLUMN stays
  null by design — the register asked for a served house_from_varga_lagna field, which is what is
  emitted + served. Whole-sign from the varga's own Lagna, 1-indexed.
```

### EL-38 — argala all-zero
```
el_id: EL-38
status: NOT-REPRODUCED (as a data defect) — zeros adjudicated genuine; serving half handed to α.B
before_payload: report "every sampled row fact_value_num:0" under limit:5
after_payload:  distribution 1.0×992, 0.75×256, 0.5×112, 0.25×28, 0.0×2788 — 1388 non-zero cells at Jaimini argala offsets {2,4,5,11}
probes_run: SQL GROUP BY fact_value_num on argala_natal_matrix (chart A); D1_SIGN_2 per-offset dump
charts: 482012f1
verifier_notes: >
  The "all-zero" was a limit:5 sampling artifact hitting only non-argala offsets (correctly 0). No
  writer change. The two real EL-38 problems — 25000 default-limit timeout + sign-indexed matrix
  lacking house-from-lagna resolution — are α.B serving concerns (§15 maps EL-38 = α·B + β·D).
  Committed a regression test is N/A (no code change); disposition rests on the raw distribution diff.
```

### DOWNSTREAM — MSR resolution (§N.5)
```
item: MSR drift after L1 rebuild
status: PARKED-HONEST — L2+ auto-flagged stale; restoration requires L2→L5 cascade (outside 3-writer allowlist → native review per ka_gochara ruling)
measurement: >
  Post-rebuild bodha_msr_signals.constituent_facts_array resolution: chart A 59145/71430 dangling
  (82.8%), chart B 61229/69008 (88.7%). Cause: _fact_id is build_id-scoped, so rebuilding
  ga_sensitive/ga_structural/ga_vargas rotates fact_ids across ALL their categories (not just the
  3 changed-value ones) — every MSR ref into those categories dangles. The underlying L1 VALUES are
  correct; only the fact_id links broke.
disposition: >
  _run_data_writer auto-flagged the L2+ dependents stale (ka_avadhi, bo_cdlm_summary, ph_*, mi_*,
  etc. — observed in the rebuild log). Restoring MSR resolution requires rebuilding the L2→L5
  cascade (bo_laksana re-links bodha_msr_signals to current fact_ids; then ka/ph/mi). That is
  OUTSIDE this lane's declared 3-writer allowlist; per the binding native ka_gochara ruling
  ("anything outside the three writers → PARKED-HONEST, wait for native review"), it is NOT run
  here. Follow-up: full 58-asset cascade rebuild via the Cloud Run job once the image carrying
  PR #776 is deployed (or a native-approved local cascade). This is the charter's sanctioned
  "rebuilt OR flagged" state (§5.β.D), disclosed not hidden.
```

## Step 7 — Estate safety final

Built estate = exactly 2 charts (both canonical, both rebuilt + stamped). No non-canonical built
chart holds legacy house rows → the third-chart live probe is vacuously satisfied. C4 per-row stamp
(`formula_id=wholesign_from_lagna:1indexed:v2` on arudha/bhava_arudha; self-marking
`house_from_varga_lagna` key for vargas) + α normalise-by-tag fallback governs all future builds.

## Step 8 — FORENSIC + gochara final

- FORENSIC 7/7 PASS both charts post-rebuild (driver-gated + independently re-run):
  A = Capricorn/Purva Bhadrapada/Aries×5/Shukla Tritiya/Ravivara/Shiva/Garaja;
  B = Aquarius/Ardra/Aries×5/Shukla Dashami/Shanivara/Ayushman/Garaja.
- ka_gochara_sweep (482012f1) protected throughout: baseline 285/7695 → 303/8465 (grew as native's
  sweep completed 303/303; never dropped). Guard ran before/after every writer; never fired.

