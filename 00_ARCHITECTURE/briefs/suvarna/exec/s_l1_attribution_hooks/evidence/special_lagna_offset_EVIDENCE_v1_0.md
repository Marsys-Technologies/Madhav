---
artifact: SPECIAL_LAGNA_OFFSET_EVIDENCE
version: 1.0
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna (hora-lagna worker)
lane: special_lagna_offset
pr: "#2971"
date: 2026-10-02
decision: SS accepted the lane in S-L1 (fallback: leaves S-L1 if not review-clean)
changelog:
  - "1.0 (2026-10-02): hook entries, zero-change expectations, findings records, Varnada design (local copy, no swap), #2967 removal list."
---

# special_lagna_offset: evidence note

Hook files: `special_lagna_offset.json` (canonical chart `482012f1`), `special_lagna_offset_other_charts.json` (`1c826d5a`, `cb73cd3d`). Check script: `evidence/special_lagna_offset_check.py` (tests: `platform/scripts/governance/__tests__/test_special_lagna_offset_check.py`, 51 cases, offline).

## 1. What changes (canonical chart, computed in memory from stored values; no birth data read, written or logged)

PyJHora 4.8.6 `drik.special_ascendant` read the Sun `tz` hours after sunrise. `pyjhora_adapter/special_lagnas.py` now reads it AT sunrise for BHAVA/HORA/GHATI/VIGHATI. Offset = the Sun's motion over the timezone offset (+5.5 h on the birth date): 0.23243 deg, identical for all five ayanamshas.

| Rows (special_lagna, canonical) | Count | Expectation |
|---|---|---|
| `longitude_sidereal`, BHAVA/GHATI/HORA/VIGHATI x 5 ayanamshas | 20 | each moves by -0.23243 deg, tolerance +/-0.001 (script C4; continuous, so NOT visible to the flip detector) |
| `near_nakshatra_boundary_flag` | 5 points x 7 keys = 35 | BHAVA surya_siddhanta_classical true->false; GHATI krishnamurti, lahiri_chitrapaksha, true_chitra false->true; VIGHATI raman true->false (script C5; not read by the detector) |
| `formula_provenance_text` | 140 (4 subjects x 7 keys x 5) | all change (corrected citations; script C6; not read by the detector) |
| `sign`, `sign_lord`, `house_d1`, `nakshatra`, `nakshatra_lord`, `pada` | 4 subjects x 20 = 120 | **ZERO CHANGE** (hook entry `exact 0`, script C2): sign 0/20, nakshatra 0/20, pada 0/20, house 0/20 |
| INDU, SREE, VARNADA, every key | 3 subjects x 35 = 105 | **ZERO CHANGE** (hook entry `exact 0` on the class keys; script C3 on every column) |
| row count | 245 per chart | unchanged (hook entry `exact 0` on appeared/disappeared/occurrence_count; script C1) |

Pada answer: no pada changes. The smallest distance from any of the 20 points (old or new position) to a pada edge is 7.6 arcmin, and none of the 20 crosses a sign, nakshatra or pada edge when shifted by 13.9 arcmin. Model check: with the stored longitude, the writer's own classifier reproduces the stored sign/nakshatra/pada on all 20 points, the writer's boundary-flag functions reproduce the stored flags, and a synthesized after-state built from the REAL before-snapshot passes `special_lagna_offset_check.py --compare` (0 failures, 245 rows). The model assumes the stored rows were built with the unfixed adapter and the +5.5 h timezone.

**Varnada: no VARNADA row changes on the canonical chart (0 of 35).** Varnada Lagna depends on the Lagna sign and the Hora Lagna SIGN only, and no Hora Lagna sign changes on this chart in any ayanamsha (sign 0/5). Its longitude is the Lagna's own degree in sign.

Detector-visibility: continuous values (longitude) are counted in the detector's `continuous` block and never blocking; flag columns and provenance text are not read at all. Hence two layers: the hook (class-level zero-change, row counts) and the script (delta, flags, provenance). Tier changes on special_lagna belong to the tiers lane (#2941, two_pass_verified -> single on 245 rows) and are excluded from this hook's zero-change entry on purpose; with no tiers hook loaded they appear as KIND_MISMATCH, with it loaded they are attributed to it.

Offline demonstration (flip_detector.py from branch TI-flip-detector-001, `compare_states`, synthetic 245-row states, hooks loaded from this folder): `--validate-hooks --require-lanes special_lagna_offset,special_lagna_offset_other_charts` valid; expected after-state (20 longitudes move) -> no failure class; one HORA sign flip, one VARNADA pada change, and one disappearing INDU row each -> `EXPECTATION_MISMATCH: 1`.

W7: before the rebuild `special_lagna_offset_check.py --snapshot 482012f1-710e-4a25-994a-93821f5871aa --out <path outside the repo>` (reader via `FLIP_READER`); after: `--compare <snapshot> 482012f1-710e-4a25-994a-93821f5871aa` must print `PASS`. For `1c826d5a` / `cb73cd3d` the same script runs C1/C3 plus a 1 deg sanity bound and PRINTS class changes for review (no offline simulation exists for them: their timezone offsets are not known here).

## 2. Definition (BPHS corpus, `classical_text_chunks`, Ch.5 "Special Ascendants", Santhanam ed.)

Bhava (`bphs_pg0061_c01`): "every 5 ghatis (or 120 minutes) constitute one Bhava lagna. Divide the time of birth (in ghatis, vighatis etc.) from Sun-rise by 5 and add the quotient etc. to the Sun's longitude as at Sun rise." Hora (`bphs_pg0062_c01`): "Hora Lagna repeats itself every 2 1/2 ghatis (60 minutes). Divide the time past upto birth from the Sunrise by 2 1/2 and add the quotient … to the longitude of the Sun as at the Sunrise." Ghatika (`bphs_pg0062_c01`): "changes along with every Ghatika (24 minutes) from the Sunrise … number of ghatis past as number of Rasis … Vighatis be divided by 2 to arrive at degrees and minutes … added to the Sun's longitude as at Sunrise." Rates 0.25 / 0.5 / 1.25 deg per minute; worked example (Sun 132 deg, 12 gh 30 vi): 207 / 282 / 147 deg, asserted by a test. (The corpus text is OCR; fractions and the "60 minutes" figure above are reconstructed from the garbled characters and confirmed by the worked example's arithmetic.)

## 3. Findings records (J1 by name)

| id | finding | state | action |
|---|---|---|---|
| (a) VIGHATI_LAGNA rate | 15 deg/min is PyJHora's rate; Vighati Lagna is NOT in the BPHS corpus chunks (no match for any "vighati/vighatika lagna" phrase in `classical_text_chunks`). Only the Sun-at-sunrise BASE is corrected for it. | citation state `unsourced` | J1; the ga_sensitive provenance text now says so |
| (b) not audited | INDU_LAGNA degree-in-sign part (the sign rule's kalas 30,16,6,8,10,12,1 and 9th-lord procedure match Uttara Kalamrita `uttara_kalamrita_pg0093_c01`; the degree convention is not in that text); SREE_LAGNA; PRANAPADA (stored as `esoteric_point_pranapada_sphuta`); the adapter's `bhrigu_bindhu_lagna` and `kunda_lagna` (not emitted into chart_facts by ga_sensitive; stored `esoteric_point_bhrigu_bindu` is a separate writer formula); VARNADA_LAGNA (see next row) | NOT audited | J1 list |
| (b2) VARNADA method | The adapter uses BV Raman `varnada_method=1`. The corpus worked example (BPHS Ch.5, `bphs_pg0064_c01`/`c02`: Libra Lagna, Scorpio Hora Lagna -> Aries) is reproduced by PyJHora method 2 ("Sharma/Santhanam") and 4, NOT by method 1 (which returns Taurus for that example; verified by running the four methods with the inputs stubbed). The Hora input is corrected by this lane; the METHOD is untouched. | open finding, not changed | J1 / SS: a Varnada value change would be a separate decision |
| (c) births before sunrise | PyJHora and this adapter take the sunrise of the birth's own civil date, so a birth BEFORE that day's sunrise gets a negative elapsed time. The usual classical rule counts such a birth from the PREVIOUS day's sunrise (the Hindu day starts at sunrise); the corpus passages above say "from Sun-rise to the time of birth" without addressing it. NOT changed. | open classical question | J1. The canonical chart is not a before-sunrise birth: using only the birth date and local time of record (CLAUDE.md section B) and city-level coordinates (not the stored birth record), sunrise precedes the birth by about 4 hours at three coordinate guesses 1 deg apart, so the fix is unaffected. |
| (d) served change | see section 5 | | runbook |

## 4. Varnada design: local copy, no swap

The first version swapped `drik.hora_lagna` for the corrected function for one `charts.varnada_lagna` call and restored it. That is replaced: `special_lagnas._varnada_lagna_bv_raman` is a line-for-line copy of PyJHora's BV Raman routine (method 1, house 1) that takes its Hora SIGN from the module's corrected `hora_lagna`. **No PyJHora attribute is reassigned anywhere**, so there is nothing to restore and nothing for another caller to observe. Tests: static AST check (no assignment to `drik`/`charts`/`utils`/`const` attributes, no setattr); `drik.hora_lagna` identity-equal to the original after normal exit, after an Exception, and after KeyboardInterrupt / GeneratorExit / SystemExit raised inside the Varnada step (and from inside it); a second thread calling `drik.hora_lagna` while the first is parked inside `compute_special_lagnas` gets the ORIGINAL function and its upstream result; parity with upstream `charts.varnada_lagna` at every sampled instant (about 13,400 grid points, nearly all of them agreeing) where the two Hora signs agree, and divergence only where they differ. Mutation proof: using upstream `drik.hora_lagna` inside the copy, a permanent swap, and a swap without restore each turn tests red.

Other callers of `hora_lagna` in the repo (non-test): none outside `pyjhora_adapter/special_lagnas.py`. Inside PyJHora 4.8.6, `drik.hora_lagna` / `special_ascendant` are called by `horoscope/main.py`, `horoscope/info.py`, `prediction/longevity.py:183`, `chart/house.py:1127`, `chart/charts.py` (varnada family, amsa helper at :2120) and `dhasa/raasi/varnada.py:80`; the sidecar imports only `charts.divisional_chart/rasi_chart/vimsopaka_*/birth_date`, `house._get_compound_relationships_of_planets`, vimsottari/mudda/kalachakra/aayu, none of which reach those. All sidecar Swiss-touching adapter entry points, including the two new functions, are `@serialized_swiss_state` (inventory test `test_swiss_state_boundary` extended).

## 5. What a user sees after the rebuild (runbook sentence)

"After the rebuild, the Hora Lagna longitude in the wealth reading's special-lagna evidence (and in `ganita_special_lagnas_get`) is 0.2324 degrees (about 14 arcminutes) smaller than before, and the Bhava, Ghati and Vighati lagna longitudes shift by the same amount; their sign, nakshatra, pada and house are unchanged, and the near-nakshatra-boundary flag differs on five points."

Readers of the four lagnas: `bo_special_lagna` / `special_lagna_emitter` (house, sign, lords, nakshatra, pada: unchanged), `bo_karanajala` (house_d1, sign, sign_lord: unchanged), `bo_laksana` (generic copy), `brahmagyan/chart_reader_v4`, `ka_kshetra` stage 2 (CGM nodes); TypeScript: `reading_checklist.ts` wealth leg (HORA longitude moves), `ganita_special_lagnas_get` / `facts_store` (generic). `ga_structural` reads `special_lagna_position` (a different category) and `ga_vargas` does not read these rows.

## 6. Coupling with #2967 (do NOT edit #2967; remove in the same commit that brings #2971 in)

File `platform/python-sidecar/tests/test_ga_sensitive_orchestrator_path_shape.py` at #2967 head `3ff7288ed`:

| lines | what | action |
|---|---|---|
| 32-37 | module-docstring bullet describing the strict xfail and the cause test | delete |
| 241-247 | comment block + `_RATES_DEG_PER_MIN`, `_LAHIRI_KEY` | delete (only the two tests below use them) |
| 250-268 | `_independent` (and its `@serialized_swiss_state` decorator) | delete |
| 271-276, 279-280 | `_emitted_longitude`, `_signed_diff` | delete |
| 283-295 | `@pytest.mark.xfail(strict=True, ...)` + parametrize + `test_sunrise_lagnas_match_independent_classical_derivation` (3 cases, XPASS(strict) = FAIL once #2971 lands) | delete (superseded by `tests/test_special_lagna_sunrise_sun.py`) |
| 298-304 | `test_cause_of_offset_is_sun_read_tz_hours_after_sunrise` (3 cases, fails once #2971 lands) | delete |
| 43, 50 | `import os`, `from panchang_engine.swiss_state import serialized_swiss_state` (unused after the above) | delete |

Everything else in that file (lines 41-240: shape, wealth-atom, Trisphuta-gap tests) stays valid under #2971 and keeps pinning the stored shape.

## 7. Not verified

- The class-level and pada effect on the non-canonical charts (no timezone offsets available here).
- That the stored canonical rows were built with the unfixed adapter at +5.5 h (assumed; the model reproduces every stored classifier output and boundary flag).
- Vighati's rate, Indu's degree, Sree, Pranapada, Varnada's method (section 3).
