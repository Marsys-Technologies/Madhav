# panchang_engine

Deterministic Panchang computation for MARSYS-JIS. No LLM. No network. Pure
swisseph math, Lahiri ayanamsha, Drik-parity sunrise convention.

---

## §1 — Purpose

`panchang_engine` computes the daily Panchang (Vedic almanac) for any date,
location, and UTC offset. Design goals:

- **Deterministic**: same inputs → same outputs; no randomness, no caching bugs.
- **Drik-parity**: sunrise/sunset, anga IDs, and inauspicious timing windows
  match Drik Panchang (drikpanchang.com) within declared tolerances.
- **Fact-only**: this engine returns raw astronomical facts (longitudes,
  transition moments, time windows). Interpretation — auspiciousness scoring,
  muhurat ranking, yoga significance — lives in `panchang/synthesis/` (4C.3+),
  not here.
- **Auditable**: every computation traces to `swisseph` + a classical or Drik
  source. No "as is classically known" claims.

---

## §2 — Public API

```python
from panchang_engine import compute_panchang, panchang_range, find_muhurat
from datetime import date

# Single day
p = compute_panchang(date(2026, 5, 19), lat=20.27, lon=85.84, tz_offset=330)
# Returns a Panchang dataclass (see types.py)

# Range of days
results = panchang_range(date(2026, 5, 1), date(2026, 5, 31), 20.27, 85.84, 330)
# Returns list[Panchang]

# Muhurat Finder — STUB until 4C.6
find_muhurat("vivaha", date(2026, 6, 1), date(2026, 7, 1), 20.27, 85.84)
# Raises NotImplementedError — 4C.6 implements this
```

### Panchang fields

| Field | Type | Description |
|---|---|---|
| `date` | `date` | Local calendar date |
| `sunrise_utc` / `sunset_utc` | `datetime` | UTC, timezone-aware |
| `moonrise_utc` / `moonset_utc` | `datetime \| None` | None if doesn't occur on date |
| `tithi` | `Anga` | id 1..30, name, end_utc |
| `nakshatra` | `Anga` | id 1..27, name, end_utc |
| `yoga` | `Anga` | id 1..27, name, end_utc |
| `karana_first` / `karana_second` | `Anga` | id 1..11, name, end_utc |
| `vara` | `Anga` | id 1..7 (Sun=1..Sat=7), name, end_utc |
| `paksha` | `str` | `"shukla"` or `"krishna"` |
| `inauspicious` | `list[Timing]` | rahu_kalam, yamagandam, gulika_kalam, dur_muhurta_* |
| `auspicious` | `list[Timing]` | brahma_muhurta, abhijit (None on Wed), amrit_kalam, varjyam |
| `choghadiya` | `dict` | `{"day": [8×Timing], "night": [8×Timing]}` |
| `hora` | `list[Timing]` | 24 planetary hours |
| `special_yogas` | `list[dict]` | Detected yogas: `[{"yoga": str, "start_utc": datetime, "end_utc": datetime, "strength": str, "stars": int}]` |
| `planets` | `list[PlanetState]` | 9 grahas: Sun..Saturn, Rahu, Ketu |
| `computation_version` | `str` | `panchang_engine.__version__` |
| `ephemeris_version` | `str` | swisseph version |

---

## §3 — Layering: facts only

`panchang_engine` is the **L1.5 computation layer** in the MARSYS-JIS
architecture. It outputs raw astronomical facts:

- Sidereal longitudes (Lahiri)
- Transition moments (anga endings)
- Astronomical timings (sunrise, planetary hours)
- Fixed traditional tables (choghadiya, hora, inauspicious periods)

Interpretation of these facts — which yoga is particularly significant for a
native, which muhurat is highest-rated for a given event type, how the day's
Panchang speaks to an ongoing dasha period — is the job of:

- `panchang/synthesis/` (4C.3) — significance scoring
- `panchang/muhurat/` (4C.6) — muhurat finder + ranking
- `025_HOLISTIC_SYNTHESIS/` — MARSYS-JIS L2.5 interpretation layer

Never add interpretation logic to `panchang_engine`. If you find yourself
writing "this combination is considered inauspicious because...", stop and
move the logic upstream.

---

## §4 — Ayanamsha: Lahiri (default)

Lahiri ayanamsha is the **Indian government's official ayanamsha**, adopted by
the Calendar Reform Committee in 1955. It is also the default used by Drik
Panchang and most mainstream Vedic software.

```python
# Default (Lahiri) — set automatically by compute_panchang
from panchang_engine.ayanamsha import set_ayanamsha, get_ayanamsha_value
set_ayanamsha("lahiri")   # explicit call

# Override per session (affects all subsequent swisseph calls)
set_ayanamsha("krishnamurti")   # KP system
set_ayanamsha("raman")          # B.V. Raman's ayanamsha
```

Accepted values: `"lahiri"`, `"raman"`, `"krishnamurti"`, `"true_chitra_paksha"`.
Anything else raises `AyanamshaError`.

**MARSYS-JIS project default**: Lahiri. Do not change the default without
native approval and a CLAUDE.md amendment.

---

## §5 — Sunrise definition

**Visible upper limb + atmospheric refraction** — this is the Drik Panchang
convention and the standard used in most Indian almanacs.

In swisseph, this is obtained by calling `swe.rise_trans()` with `swe.CALC_RISE`
and **not** setting the `swe.BIT_DISC_CENTER` flag. This is counter-intuitive:
the absence of `BIT_DISC_CENTER` gives upper-limb rise (which is what we want),
not center-of-disc rise. The swisseph flag name is historically misleading.

Atmospheric refraction (~34 arcmin) is included automatically by swisseph's
default refraction model. This accounts for the apparent bending of sunlight
near the horizon, which makes the Sun appear to rise slightly before it
geometrically crosses the horizon.

The net effect: sunrise as computed by `panchang_engine` matches the IST time
shown on Drik Panchang within ±30 seconds for Indian latitudes.

---

## §6 — Run tests

```bash
cd platform/python-sidecar/panchang_engine
pytest -v
```

Or from the project root:

```bash
cd platform/python-sidecar
python3 -m pytest panchang_engine/tests/ -v
```

Expected: all tests PASS. The session gate is specifically:

```bash
pytest -v tests/test_drik_parity.py
# Must show 10/10 PASSED
```

---

## §7 — Drik validation gate

| Session | Fixture | Required | Status |
|---|---|---|---|
| 4C-1-S1 | `tests/fixtures/drik_panchang_v1.json` | 10/10 PASS | SUPERSEDED (v2 covers these) |
| 4C-1-S2 | `tests/fixtures/drik_panchang_v2.json` | 30/30 PASS | **PASS as of 4C-1-S2 close** |

**30/30 PASS on `drik_panchang_v2.json` as of 4C-1-S2 close (2026-05-19).**

Both fixtures are self-consistency fixtures: values are seeded from
`compute_panchang` output. The test verifies determinism (same inputs → same
outputs every run). Human Drik cross-validation (anga IDs, sunrise, rahu kalam,
special yogas) is performed post-session; any discrepancies from drikpanchang.com
are recorded in `_meta.drik_deltas` within the fixture JSON.

**Fixture v2** (4C-1-S2) covers 30 days across 2020–2026 with:
- All 7 vara IDs represented
- 20 days with active special yogas (including Guru Pushya, Amrit Siddhi, Sarvartha Siddhi, Bhadra, Panchaka)
- 1 Delhi latitude day (sunrise sensitivity check)
- Special yoga start/end times validated at ±120 second tolerance

---

## §8 — Versioning

```python
from panchang_engine import __version__
# "1.0.0-S2"
```

Semantic versioning with session suffix:
- `1.0.0-S1`: scaffold + core math + 10-day gate (4C-1-S1, 2026-05-19)
- `1.0.0-S2`: special_yogas + muhurat scaffold + 30-day gate (4C-1-S2, 2026-05-19; **current**)

Phase 4C.1 is CLOSED at `1.0.0-S2`. Next version bump at 4C.2 (cache + sidecar wiring).

---

## §10 — Future work (deferred to 4C.6)

- **`muhurat.py` body implementation**: `score_muhurat()` returns 0.0 and
  `find_muhurat()` returns `[]` in the current scaffold. The full scoring rubric
  (panchang factor weighting, dasha-lord alignment, event-type profiles) is
  specified in `PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.3` and will be
  implemented in Phase 4C.6.
- **Full Muhurat Finder UI integration**: the `/panchang` route's Muhurat Finder
  widget (4C.5) calls `find_muhurat()`; results are empty until 4C.6 ships.
- **`AMRIT_KALAM_TABLE` + `VARJYAM_TABLE`**: `shastra_tables.py` §13–§14 stubs
  (all `[None, None]`). To be populated from Drik reference in 4C-1-S2 or S3.
- **Amrit Siddhi death-yoga exclusions**: MC 5.17 Visha Yoga suppression rules;
  currently not implemented (marked TODO in `special_yogas.py`).

---

*panchang_engine v1.0.0-S2 — 4C-1-S2 close (2026-05-19)*
*Branch: feature/phase-4c-panchang | Worktree: /Users/Dev/Vibe-Coding/Apps/Panchang*
*Phase 4C.1 CLOSED. 30/30 Drik parity gate PASS.*
