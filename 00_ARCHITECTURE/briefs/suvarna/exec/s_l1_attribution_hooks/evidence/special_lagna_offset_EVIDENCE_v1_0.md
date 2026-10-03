---
artifact: SPECIAL_LAGNA_OFFSET_EVIDENCE
version: 1.2
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna (hora-lagna worker)
lane: special_lagna_offset
pr: "#2971"
date: 2026-10-02
decision: SS accepted the lane in S-L1 (fallback: leaves S-L1 if not review-clean)
changelog:
  - "1.2 (2026-10-03): F-2 of the PR #2984 delta review. The statements that INDU/SREE/VARNADA 'values do not change' / 'ZERO CHANGE on every column' were true of the CLASS values (sign, sign_lord, house_d1, nakshatra, nakshatra_lord, pada), the flags and the provenance text, but not of the longitude number under the Moshier to .se1 backend move (INDU -0.000185 deg, SREE -0.004985 deg, VARNADA 0 to 2.7e-8 deg on True Chitra and Surya Siddhanta; /Users/Dev/suvarna-evidence/Ephemeris/SE1_SHIFT_ANALYSIS.md (sha256 22564b863fc7cb3713e5d4b5d88ca5dc7376532fd93a9faa6461c99689ac3403) section 3 and /Users/Dev/suvarna-evidence/Ephemeris/SPECIAL_LAGNA_AYA_CHECK.md section 3b). Script C3 now holds each longitude to its own declared band (INDU +/-0.00025, SREE +/-0.0055, VARNADA +/-1e-7 deg) and keeps every other column exact; tests added. A correct .se1 rebuild would otherwise have failed the REQUIRED W7 step on 12 rows (5 INDU, 5 SREE, 2 VARNADA)."
  - "1.1 (2026-10-02): R2c2 review fixes. Hook: the optional longitude value entry removed, so a NULL/text longitude fails the detector itself; W7 run of the check script declared REQUIRED; check script refuses to run unless the session is read-only; Vighati/tolerance note; legacy/historical not-changed note; exact Varnada finding with quote, 144-pair result and the canonical five-row table; Varnada readers list."
  - "1.0 (2026-10-02): hook entries, zero-change expectations, findings records, Varnada design (local copy, no swap), #2967 removal list."
---

# special_lagna_offset: evidence note

Hook files: `special_lagna_offset.json` (canonical chart `482012f1`), `special_lagna_offset_other_charts.json` (`1c826d5a`, `cb73cd3d`). Check script: `evidence/special_lagna_offset_check.py` (tests: `platform/scripts/governance/__tests__/test_special_lagna_offset_check.py`, 61 cases, offline). **The W7 run of `special_lagna_offset_check.py` (snapshot before, `--compare` after, on the canonical chart) is REQUIRED: the flip detector alone is not sufficient** (it cannot see the continuous delta, the flag columns or the provenance text). The script REFUSES to run unless the database session reports `transaction_read_only = on` (PGOPTIONS requests it, a `current_setting` query proves it, for `FLIP_READER` and plain `psql` alike).

## 1. What changes (canonical chart, computed in memory from stored values; no birth data read, written or logged)

PyJHora 4.8.6 `drik.special_ascendant` read the Sun `tz` hours after sunrise. `pyjhora_adapter/special_lagnas.py` now reads it AT sunrise for BHAVA/HORA/GHATI/VIGHATI. Offset = the Sun's motion over the timezone offset (+5.5 h on the birth date): 0.23243 deg, identical for all five ayanamshas.

| Rows (special_lagna, canonical) | Count | Expectation |
|---|---|---|
| `longitude_sidereal`, BHAVA/GHATI/HORA/VIGHATI x 5 ayanamshas | 20 | each moves by -0.23243 deg, tolerance +/-0.001 (script C4; continuous, so NOT visible to the flip detector) |
| `near_nakshatra_boundary_flag` | 5 points x 7 keys = 35 | BHAVA surya_siddhanta_classical true->false; GHATI krishnamurti, lahiri_chitrapaksha, true_chitra false->true; VIGHATI raman true->false (script C5; not read by the detector) |
| `formula_provenance_text` | 140 (4 subjects x 7 keys x 5) | all change (corrected citations; script C6; not read by the detector) |
| `sign`, `sign_lord`, `house_d1`, `nakshatra`, `nakshatra_lord`, `pada` | 4 subjects x 20 = 120 | **ZERO CHANGE** (hook entry `exact 0`, script C2): sign 0/20, nakshatra 0/20, pada 0/20, house 0/20 |
| INDU, SREE, VARNADA, every key | 3 subjects x 35 = 105 | **CLASS ZERO CHANGE** (hook entry `exact 0` on the class keys; script C3 compares sign, sign_lord, house_d1, nakshatra, nakshatra_lord, pada, flags and provenance text EXACTLY). The `longitude_sidereal` number of these three moves by a measured, tiny amount under the Moshier to .se1 backend move and is held to its own band by C3: INDU +/-0.00025 deg (measured -0.000185, the Moon's shift), SREE +/-0.0055 deg (measured -0.004985, 27 x the Moon's shift), VARNADA +/-1e-7 deg (measured 0 on three ayanamshas, -2.6e-8 true_chitra, +1.2e-8 surya_siddhanta) |
| row count | 245 per chart | unchanged (hook entry `exact 0` on appeared/disappeared/occurrence_count of longitude; script C1) |

Pada answer: no pada changes. The smallest distance from any of the 20 points (old or new position) to a pada edge is 7.6 arcmin, and none of the 20 crosses a sign, nakshatra or pada edge when shifted by 13.9 arcmin. Model check: with the stored longitude, the writer's own classifier reproduces the stored sign/nakshatra/pada on all 20 points, the writer's boundary-flag functions reproduce the stored flags, and a synthesized after-state built from the REAL before-snapshot passes `special_lagna_offset_check.py --compare` (0 failures, 245 rows). The model assumes the stored rows were built with the unfixed adapter and the +5.5 h timezone.

**Varnada: no VARNADA class value changes on the canonical chart (0 of 30 class rows).** Varnada Lagna depends on the Lagna sign and the Hora Lagna SIGN only, and no Hora Lagna sign changes on this chart in any ayanamsha (sign 0/5). Its longitude is the Lagna's own degree in sign, so it moves only as far as the Lagna does under the backend move: 0 on Lahiri, Krishnamurti and Raman, about 3e-8 deg on True Chitra and Surya Siddhanta (script C3 band +/-1e-7 deg).

Detector-visibility: continuous values (longitude) are counted in the detector's `continuous` block and never blocking, BUT a longitude that becomes NULL or text is a class `value` change; the hook deliberately declares NO entry for the longitude value, so the detector itself FAILS it (`KIND_MISMATCH`, verified offline for NULL and for text). The hook format has no null-count expectation, which is why this route is used instead. Flag columns and provenance text are not read at all. Hence two layers: the hook (class-level zero-change, row counts) and the script (delta, flags, provenance). Tier changes on special_lagna belong to the tiers lane (#2941, two_pass_verified -> single on 245 rows) and are excluded from this hook's zero-change entry on purpose; with no tiers hook loaded they appear as KIND_MISMATCH, with it loaded they are attributed to it.

Offline demonstration (flip_detector.py from branch TI-flip-detector-001, `compare_states`, synthetic 245-row states, hooks loaded from this folder): `--validate-hooks --require-lanes special_lagna_offset,special_lagna_offset_other_charts` valid; expected after-state (20 longitudes move) -> no failure class; one HORA sign flip, one VARNADA pada change, and one disappearing INDU row each -> `EXPECTATION_MISMATCH: 1`.

W7: before the rebuild `special_lagna_offset_check.py --snapshot 482012f1-710e-4a25-994a-93821f5871aa --out <path outside the repo>` (reader via `FLIP_READER`); after: `--compare <snapshot> 482012f1-710e-4a25-994a-93821f5871aa` must print `PASS`. For `1c826d5a` / `cb73cd3d` the same script runs C1/C3 plus a 1 deg sanity bound and PRINTS class changes for review (no offline simulation exists for them: their timezone offsets are not known here).

## 2. Definition (BPHS corpus, `classical_text_chunks`, Ch.5 "Special Ascendants", Santhanam ed.)

Bhava (`bphs_pg0061_c01`): "every 5 ghatis (or 120 minutes) constitute one Bhava lagna. Divide the time of birth (in ghatis, vighatis etc.) from Sun-rise by 5 and add the quotient etc. to the Sun's longitude as at Sun rise." Hora (`bphs_pg0062_c01`): "Hora Lagna repeats itself every 2 1/2 ghatis (60 minutes). Divide the time past upto birth from the Sunrise by 2 1/2 and add the quotient … to the longitude of the Sun as at the Sunrise." Ghatika (`bphs_pg0062_c01`): "changes along with every Ghatika (24 minutes) from the Sunrise … number of ghatis past as number of Rasis … Vighatis be divided by 2 to arrive at degrees and minutes … added to the Sun's longitude as at Sunrise." Rates 0.25 / 0.5 / 1.25 deg per minute; worked example (Sun 132 deg, 12 gh 30 vi): 207 / 282 / 147 deg, asserted by a test. (The corpus text is OCR; fractions and the "60 minutes" figure above are reconstructed from the garbled characters and confirmed by the worked example's arithmetic.)

## 3. Findings records (J1 by name)

| id | finding | state | action |
|---|---|---|---|
| (a) VIGHATI_LAGNA rate | 15 deg/min is PyJHora's rate; Vighati Lagna is NOT in the BPHS corpus chunks (no match for any "vighati/vighatika lagna" phrase in `classical_text_chunks`). Only the Sun-at-sunrise BASE is corrected for it. | citation state `unsourced` | J1; the ga_sensitive provenance text now says so |
| (b) not audited | INDU_LAGNA degree-in-sign part (the sign rule's kalas 30,16,6,8,10,12,1 and 9th-lord procedure match Uttara Kalamrita `uttara_kalamrita_pg0093_c01`; the degree convention is not in that text); SREE_LAGNA; PRANAPADA (stored as `esoteric_point_pranapada_sphuta`); the adapter's `bhrigu_bindhu_lagna` and `kunda_lagna` (not emitted into chart_facts by ga_sensitive; stored `esoteric_point_bhrigu_bindu` is a separate writer formula); VARNADA_LAGNA (see next row) | NOT audited | J1 list |
| (b2) VARNADA method | **Varnada Lagna: adapter uses BV Raman (method 1); corpus example reproduced by methods 2 and 4; no canonical row changes from the offset fix.** Full text and the canonical five-row table in section 3a. | open finding, SS decision (pre-existing), NOT changed | J1 / owner list |
| (c) births before sunrise | PyJHora and this adapter take the sunrise of the birth's own civil date, so a birth BEFORE that day's sunrise gets a negative elapsed time. The usual classical rule counts such a birth from the PREVIOUS day's sunrise (the Hindu day starts at sunrise); the corpus passages above say "from Sun-rise to the time of birth" without addressing it. NOT changed. | open classical question | J1. The canonical chart is not a before-sunrise birth: using only the birth date and local time of record (CLAUDE.md section B) and city-level coordinates (not the stored birth record), sunrise precedes the birth by about 4 hours at three coordinate guesses 1 deg apart, so the fix is unaffected. |
| (d) served change | see section 5 | | runbook |

### 3a. Varnada Lagna: method vs the corpus (finding F1, pre-existing, NOT changed)

**Varnada Lagna: adapter uses BV Raman (method 1); corpus example reproduced by methods 2 and 4; no canonical row changes from the offset fix.**

Corpus rule (BPHS Ch.5, `bphs_pg0064_c01`, Varnada, Santhanam ed.; OCR noise cleaned, wording otherwise verbatim): "If the natal ascendant is an odd sign count directly from Aries to natal ascendant. If the natal ascendant is an even sign, count from Pisces to the natal ascendant, in the reverse order. Similarly, if the Hora Lagna is an odd one, count from Aries to Hora lagna in direct order. If the Hora Lagna is an even one, count from Pisces to Hora Lagna in the reverse order. If both the products are odd signs or even signs, then add both the figures. If one is odd and the other is even, then know the difference between the two products. If the latest product, in this process, is an odd one, count so many signs from Aries in a direct manner; if an even one, count so many signs from Pisces in reverse order. The sign so known will be the Varnada for the ascendant." Worked example in the text: Libra Lagna, Scorpio Hora Lagna -> Aries.

Results (this lane, PyJHora 4.8.6 `charts.varnada_lagna` with inputs stubbed, an independent implementation of the rule quoted above): Libra Lagna + Scorpio Hora -> methods 1 and 3 give Taurus, methods 2 and 4 give Aries (the corpus answer). Over all 144 (Lagna sign, Hora sign) pairs, method 2 matches the corpus rule 144/144, method 1 (the adapter's) 36/144 (methods 3 and 4: 36 and 21 of 144 under my implementation of the rule; the independent reviewer R2c2 reproduced 144/144 and 36/144 for methods 2 and 1).

Canonical chart, stored signs only, all five ayanamshas (the offset fix changes none of these):

| ayanamsha | Lagna | Hora | stored Varnada | PyJHora method 1 | PyJHora method 2 | corpus rule |
|---|---|---|---|---|---|---|
| lahiri_chitrapaksha | Aries | Gemini | Cancer | Cancer | Sagittarius | Sagittarius |
| true_chitra | Aries | Gemini | Cancer | Cancer | Sagittarius | Sagittarius |
| krishnamurti | Aries | Gemini | Cancer | Cancer | Sagittarius | Sagittarius |
| raman | Aries | Gemini | Cancer | Cancer | Sagittarius | Sagittarius |
| surya_siddhanta_classical | Aries | Gemini | Cancer | Cancer | Sagittarius | Sagittarius |

One fact for SS: on the canonical chart the stored VARNADA_LAGNA sign (Cancer) differs from what the corpus rule and PyJHora method 2 give (Sagittarius), in every ayanamsha. Not changed by this lane (a method change is a separate, value-changing decision).

Where VARNADA_LAGNA is served or read (grep of platform/src, platform-mcp/src, python-sidecar):
- Served: `ganita_special_lagnas_get` (platform-mcp `register_p1_aliases.ts:2204-2253`: every special_lagna row, all subjects and keys, display only); the reading family `readSpecialLagnaFamily` (platform-mcp `registry_bridge.ts:1295,1463`, label "Special lagnas (Bhava/Ghati/Hora/Sree/Varnada) + Ārūḍha Lagna": prints "Varnada Lagna in <sign>", display only, no judgment); `facts_store.ts` / the `special_lagna` concept alias / generic category passthroughs (rows by category, display). Not individually traced: chart_snapshot, dossier, reading notes, graha_portrait (grep finds no VARNADA-specific code in them).
- Downstream, sign/house used: `bo_karanajala` reads house_d1/sign/sign_lord of EVERY special_lagna subject including VARNADA and emits a CGM node plus a `special_lagna_house` edge (base weight 0.6, "occupies its house"), so Varnada's sign-derived house feeds the Bodha graph and, via `ka_kshetra/stage2_promise.py` (`special_lagna` carried as `karaka` nodes), the stage-2 route graph. `bo_laksana` passes special_lagna facts through its position-category handling (a sign value text is mapped to its classical sign lord when attributing a lord; generic). `brahmagyan/chart_reader_v4.special_points(kind='special_lagna')` returns the raw facts (display).
- NOT readers: `bo_special_lagna` / `special_lagna_emitter` emit only INDU/SREE/GHATI/HORA (`_TARGET_LAGNAS`; VARNADA, BHAVA, VIGHATI deliberately not emitted); the wealth leg `reading_checklist.ts` has `WEALTH_SPECIAL_LAGNAS = ['INDU_LAGNA','SREE_LAGNA','HORA_LAGNA']` (VARNADA is NOT in it); `register_d8_assess_domain.ts` reads INDU only.

### 3b. Other notes (not changed)

- Vighati tolerance: all seven special_lagna subjects keep `tolerance_arcsec = 1.0` (pre-existing, `ga_sensitive_writer.py` `_build_special_lagnas_rows`). One second of sunrise-time uncertainty is 0.25 deg = 900 arcsec for Vighati (15 deg/min), 75 arcsec for Ghati, 30 for Hora and 15 for Bhava, so the 1 arcsec claim is meaningless for all four. Evidence note + J1 list only; no code change.
- Legacy code not changed: `brahmagyan/ganita/l1_sensitive_points.py` has a hand-rolled `compute_special_lagnas` (Lagna-based proxies, importer: `tests/test_l1_sensitive_points.py` only) that is NOT on the S-L1 path; the historical `evals/omega7/**/DC-W-*.json` harness runs embed previously served lagna values and are records, not live data. Neither is touched.

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
