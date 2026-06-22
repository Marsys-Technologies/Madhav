---
artifact: CLAUDECODE_BRIEF_PH_RECTIFICATION_ASCENDANT_FIX.md
canonical_id: CLAUDECODE_BRIEF_PH_RECTIFICATION_ASCENDANT_FIX
version: 1.0
status: READY — scoped diagnostic+fix for the ph_rectification Aries/Capricorn discrepancy
authored_by: Cowork 2026-06-22
operates_on: feature/l4-phala-autonomous (post-R8; head f2a7c654)
blocks: L4 seal (R9) — ph_rectification must produce Aries-stable candidates before seal
runs_in: Antigravity (needs live PyJHora + swisseph ephemeris — NOT reproducible in a lint-only env)
---

# ph_rectification — Ascendant Discrepancy Fix (scoped)

## §0 — The finding (precise, from code audit)
The ph_rectification engine reports the native's offset-0 lagna as **Capricorn**, but the FORENSIC
anchor (and L1 `chart_facts`) is **Aries** across all 5 ayanamshas. The engine is *convention-robust*
(it compares candidates to the offset-0 reference sign, not a hardcoded "Aries"), so it correctly emits
`confidence_label='unresolved'` and never mutates the chart (B.10 honored). **But the underlying
ascendant value is wrong**, so ph_rectification is lit-but-not-informative. This MUST be fixed before seal.

## §1 — What the audit already PROVED (do not re-investigate these)
- **CONTAINED blast radius.** Only 3 files consume `pyjhora_adapter.houses.compute_ascendant`:
  `writers/ph_rectification/__init__.py`, `tests/test_pyjhora_adapter/test_reconciliation.py`,
  `pyjhora_adapter/compute.py`. **L1's FORENSIC Aries is built by `brahmagyan/ganita/l1_positions.py`
  via `swe.houses(jd_utc, NATIVE_LAT, NATIVE_LON, b"P")` — Swiss Ephemeris DIRECTLY, NOT PyJHora.**
  So the foundation is safe; this is a single-asset bug in the new PyJHora ascendant path.
- **Birth data is correct.** engine.py: `RECORDED_BIRTH_UTC = 1984-02-05 05:13:00 UTC` (= 10:43 IST ✓),
  `NATIVE_LAT=20.2961, NATIVE_LON=85.8245, NATIVE_TZ=5.5` — identical to L1. NOT a coordinate/time bug.
- **The writer passes real coords:** `compute_ascendant(jd_ut, ay, lat=NATIVE_LAT, lon=NATIVE_LON, tz=NATIVE_TZ)`
  — NOT null-island. Rule that out.
- **The gap is ~9 signs (Aries→Capricorn ≈ 270°), NOT ~24° — so it is NOT a tropical-vs-sidereal
  ayanamsha-magnitude offset.** Look for a sign-index / JD-convention / unit error, not an ayanamsha bug.
- **Why CI missed it:** `test_pyjhora_adapter/` asserts SHAPE + internal SELF-consistency
  (`house1_lagna_consistent`, `issues==[]`) — it NEVER asserts the sign equals the FORENSIC Aries.
  Same class as the L1 lesson: the engine agreeing with itself ≠ agreeing with ground truth.

## §2 — The diagnostic ladder (run in Antigravity, in order; stop when the cause is found)
1. **Dump the raw return:** call `from jhora.panchanga import drik; drik.set_ayanamsa_mode('LAHIRI');
   asc = drik.ascendant(jd_ut, drik.Place('subject', 20.2961, 85.8245, 5.5))` for the native `jd_ut` and
   `print(repr(asc), len(asc))`. **Confirm the element order.** The adapter assumes
   `asc = [sign_idx, deg_in_sign, nak_idx, pada]` and does `sign_idx = int(asc[0])`. If PyJHora actually
   returns `[longitude_deg, ...]` or `[sign_idx, longitude, ...]` in this version, `int(asc[0])` is a raw
   degree → garbage sign. **This is the prime suspect for a ~9-sign offset.**
2. **Check the JD convention:** the writer builds `jd_ut = swe.julday(y, m, d, ut_hours)` with UT hours.
   Confirm `drik.ascendant` expects a UT Julian Day (not local, not ET/TT). A JD/time-base mismatch can
   shift the ascendant by hours → many signs.
3. **Check ayanamsha-mode statefulness:** confirm `drik.set_ayanamsa_mode(mode)` actually mutates the
   `drik` state consumed by `drik.ascendant` (PyJHora `drik` is stateful + module-global). If `ascendant`
   reads a different/default mode, you get an offset — but note this alone is too small to explain 9 signs.
4. **Ground-truth compare:** compute the same native ascendant via `swe.houses(jd_utc, lat, lon, b"P")`
   → `ascmc[0]` (tropical) → subtract `swe.get_ayanamsa_ut(jd_utc)` → sidereal → sign. This is EXACTLY
   how L1 gets Aries. The PyJHora adapter MUST match it. Use this as the assertion oracle.

## §3 — The fix
Fix the root cause found in §2 inside `pyjhora_adapter/houses.py::compute_ascendant` (most likely the
`asc[0]` element-order / sign-index extraction, or the JD/mode handoff). Keep the public return shape
identical (`sign`, `sign_id`, `longitude_deg`, `degree_in_sign`, `sign_lord`, `nakshatra`, `pada`).
Do NOT change the ph_rectification engine logic — it is correct; only its ascendant *input* is wrong.

## §4 — The permanent guard (REQUIRED — this is why CI missed it)
Add to `tests/test_pyjhora_adapter/test_reconciliation.py` (or a new `test_ascendant_parity.py`):
```python
def test_native_ascendant_is_aries_all_ayanamshas():
    # FORENSIC 7/7: Lagna = Aries at 10:43 IST 1984-02-05 Bhubaneswar, all 5 ayanamshas.
    for ay in ("lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"):
        asc = compute_ascendant(NATIVE_JD_UT, ay, lat=20.2961, lon=85.8245, tz=5.5)
        assert asc["sign"] == "Aries", f"{ay}: got {asc['sign']}"
```
This parity assertion (engine vs FORENSIC ground truth) is the guard that must exist permanently.

## §5 — Acceptance criteria
- [verify] `drik.ascendant` raw return documented; root cause identified per §2.
- [verify] `compute_ascendant(native, any ayanamsha)["sign"] == "Aries"` — all 5.
- [verify] the new parity test PASSES and would FAIL on the pre-fix code (prove it catches the bug).
- [verify: prod, post-build] ph_rectification: stable candidates now carry Aries lagna; `lel_fit_score`
  non-null for stable candidates; `phala_rectification_best` row present; `auto_action='stage_for_review'`,
  canonical chart `482012f1` UNCHANGED (B.10).
- [verify] L1 `chart_facts` lagna UNTOUCHED (this fix is adapter-only; never touches l1_positions.py).
- [verify] full CI green; no net-new failures vs main.

## §6 — Boundaries
- **Adapter-only fix.** Do NOT touch `l1_positions.py`, the L1 build, or any sealed L0–L3 asset.
- **Do NOT mutate the canonical chart** under any circumstance (B.10 — even if rectification now scores).
- **N4 boundary** unaffected (rectification is offset-scan over the natal ascendant; no dāśā depth).
- If the root cause turns out to be a PyJHora-version bug that can't be fixed adapter-side, STOP and
  report (Tier-2 park + Smṛti) — do NOT work around it by hardcoding Aries (that would defeat generality).

---
*End of ph_rectification ascendant-fix brief. Contained single-asset bug; foundation (L1 Aries) safe.
Find the §2 cause, fix the adapter, add the permanent FORENSIC-parity guard, re-verify, then seal.*
