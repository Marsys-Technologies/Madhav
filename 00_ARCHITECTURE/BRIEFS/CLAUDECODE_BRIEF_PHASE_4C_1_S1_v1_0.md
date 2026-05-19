---
artifact: CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-19
authored_at: 2026-05-19
session_id: 4C-1-S1
session_name: 4C-1-S1 — panchang_engine Scaffold + Core Math + Drik Fixture v1
executor: Claude Code (VS Code extension / Antigravity)
execution_mode: single session, --dangerously-skip-permissions
worktree:
  name: Panchang
  branch: feature/phase-4c-panchang
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md
operational_brief: 00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md
predecessor_session: 4C-0 (governance sealed 2026-05-19)
target_subphase: 4C.1 (panchang_engine — 3–4 sessions; this brief drives S1 of those)
next_session_anticipated: 4C-1-S2 (special_yogas + muhurat scaffold + extend fixture to 30 days)
---

# CLAUDECODE_BRIEF — Phase 4C-1-S1
## panchang_engine: Scaffold + Ayanamsha + Angas + Timings + Planets + Drik Fixture v1

---

## §0 — How to start this session

**Step 1 — Pull latest on the worktree and confirm clean tree:**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
git status
# Expected: On branch feature/phase-4c-panchang, working tree clean,
#           HEAD at f965486 (4C-0 final commit) or later

git log --oneline -10
# Verify the 10 commits from 4C-0 are present
```

**Step 2 — Copy this brief from the sibling Madhav clone and activate it as the dispatcher:**

```bash
cp ../Madhav/00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md \
   ./00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md

cp ./00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md ./CLAUDECODE_BRIEF.md

git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md CLAUDECODE_BRIEF.md
git commit -m "4C-1-S1: stage brief as session dispatcher"
```

**Step 3 — Open `/Users/Dev/Vibe-Coding/Apps/Panchang` in VS Code / Antigravity, launch Claude Code with `--dangerously-skip-permissions`, paste:**

```
Read CLAUDE.md per §C, then read CLAUDECODE_BRIEF.md and execute it.
You are in the Panchang worktree at /Users/Dev/Vibe-Coding/Apps/Panchang
on branch feature/phase-4c-panchang. Active session: 4C-1-S1.
Execute the 12 scope items in §3 in order. Emit session_open handshake
first; commit after each scope item; emit session_close last. Honor the
may_touch / must_not_touch lists in §5 strictly — this session is purely
Python sidecar work, no app code, no migrations.
```

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | 4C-1-S1 |
| Cowork thread name | `Phase 4C-1-S1 panchang_engine Scaffold 2026-05-19` |
| Branch | `feature/phase-4c-panchang` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/Panchang` |
| Execution mode | Single session, `--dangerously-skip-permissions` |
| Predecessor | 4C-0 (10 commits, governance sealed 2026-05-19) |
| Anticipated next | 4C-1-S2 (special_yogas + muhurat scaffold + Drik fixture v2 to 30 days) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 (confirm Phase 4C ACTIVE, sub-phase 4C-1 OPEN)
3. `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` — **full read**; this brief implements §5.3 (computation engine) and §5.2 (schema this targets); §6 Phase 4C.1 acceptance criteria
4. `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` (operational brief — for cross-phase context)
5. `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` (schema doc you'll be computing the contents of)
6. `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` §C.1–§C.6
7. Existing sidecar structure: `ls platform/sidecar/` to confirm where panchang_engine will live alongside any existing modules (ephemeris is the closest sibling — model the test harness on its pattern if it exists)

Then emit SESSION_OPEN per `SESSION_OPEN_TEMPLATE_v1_0.md`.

---

## §3 — Scope (12 items — execute in order; commit after each)

### Item 1 — Directory scaffold

**What:** Create the `panchang_engine` package and test layout:

```
platform/sidecar/panchang_engine/
  __init__.py
  ayanamsha.py
  angas.py
  timings.py
  planets.py
  special_yogas.py   # STUB this session (raises NotImplementedError) — implemented in 4C-1-S2
  muhurat.py         # STUB this session — implemented in 4C.6 phase
  shastra_tables.py  # data file with the static lookup tables; partial population this session
  types.py           # dataclasses: Panchang, Anga, Timing, PlanetState, MuhuratWindow, NatalChart
  exceptions.py      # PanchangEngineError, AyanamshaError, OutOfRangeError, ValidationError
  tests/
    __init__.py
    conftest.py
    test_angas.py
    test_timings.py
    test_planets.py
    test_drik_parity.py
    fixtures/
      drik_panchang_v1.json    # 10-day fixture (this session); extended to 30 in S2
  pyproject.toml or setup.cfg   # if the sidecar uses per-module packaging; otherwise add to parent
  README.md                     # module description, public API, validation gate, run-tests command
```

Add `pyswisseph` to the sidecar's requirements file (whatever it uses — `requirements.txt`, `pyproject.toml`, or `Pipfile`). Confirm import works: `python -c "import swisseph as swe; print(swe.version)"`.

**AC.4C1S1.1:** Directory exists with all listed files; `pyswisseph` importable; `pytest platform/sidecar/panchang_engine/tests/ -q` runs (may pass nothing yet).

### Item 2 — `types.py` — dataclasses

**What:** Define typed structures used across the module:

```python
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

@dataclass(frozen=True)
class Anga:
    id: int               # tithi 1..30; nakshatra 1..27; yoga 1..27; karana 1..11; vara 1..7
    name: str             # e.g. "Shukla Dvitiya", "Bharani"
    end_utc: datetime     # transition moment to the next anga; UTC

@dataclass(frozen=True)
class Timing:
    label: str            # "rahu_kalam", "abhijit", "sunrise", etc.
    start_utc: datetime
    end_utc: datetime

@dataclass(frozen=True)
class PlanetState:
    name: str             # "Sun", "Moon", "Mars", ...
    longitude_sidereal: float  # 0..360 (degrees, ayanamsha-corrected)
    sign_id: int          # 1..12 (Mesha=1)
    sign_name: str
    nakshatra_id: int     # 1..27
    nakshatra_name: str
    nakshatra_pada: int   # 1..4
    retrograde: bool
    combust: bool

@dataclass(frozen=True)
class Panchang:
    date: date
    lat: float
    lon: float
    tz_offset_minutes: int
    sunrise_utc: datetime
    sunset_utc: datetime
    moonrise_utc: Optional[datetime]
    moonset_utc: Optional[datetime]
    tithi: Anga
    nakshatra: Anga
    yoga: Anga
    karana_first: Anga
    karana_second: Anga
    vara: Anga
    paksha: str           # "shukla" or "krishna"
    inauspicious: list[Timing]
    auspicious: list[Timing]
    choghadiya: dict      # {"day": [Timing...], "night": [Timing...]}
    hora: list[Timing]    # 24 planetary hours
    special_yogas: list   # populated in 4C-1-S2; empty list this session
    planets: list[PlanetState]
    computation_version: str
    ephemeris_version: str

@dataclass(frozen=True)
class NatalChart:
    birth_nakshatra_id: int
    birth_lagna_sign_id: int
    moon_sign_id: int
    active_dasha_lord: str    # e.g. "Saturn" — for dasha-aware muhurat scoring (used in 4C.6)

@dataclass(frozen=True)
class MuhuratWindow:
    event: str
    start_utc: datetime
    end_utc: datetime
    star_rating: int      # 1..5
    score: float
    breakdown: dict       # contributions per scoring factor
```

**AC.4C1S1.2:** `types.py` exists; all dataclasses defined and importable; `from panchang_engine.types import *` works.

### Item 3 — `ayanamsha.py` — Lahiri default

**What:**
- Public function `set_ayanamsha(mode: str = "lahiri")` — wrapper over `swe.set_sid_mode(swe.SIDM_LAHIRI)`.
- Constant `DEFAULT_AYANAMSHA = "lahiri"`.
- Validation: accept `"lahiri"`, `"raman"`, `"krishnamurti"`, `"true_chitra_paksha"`; raise `AyanamshaError` for others.
- Compute and expose `get_ayanamsha_value(jd_ut: float) -> float` for diagnostics.
- Inline citation comment: "Lahiri is the Indian government's official ayanamsha (1955 Calendar Reform Committee) and is what Drik Panchang uses by default. PROJECT DEFAULT — overridable per call only via explicit set_ayanamsha()."

**AC.4C1S1.3:** Module imports clean; `set_ayanamsha("lahiri")` sets the mode; `set_ayanamsha("nonsense")` raises `AyanamshaError`; `get_ayanamsha_value(2451545.0)` returns ~23.85 (Lahiri value at J2000).

### Item 4 — `angas.py` — the five angas computation

**What:** Pure math, swisseph-backed. Functions:

```python
def compute_tithi(sun_lon: float, moon_lon: float, asof_utc: datetime) -> Anga:
    """
    Tithi = floor((moon_lon - sun_lon) % 360 / 12) + 1.  Range 1..30.
    Each tithi spans 12° of moon-sun separation. Paksha:
      tithis 1..15 = Shukla (new→full moon).
      tithis 16..30 = Krishna (full→new). Krishna tithis are named 16=Krishna Pratipada,
      ..., 30=Amavasya. Tithi 15 = Purnima.
    Returns end_utc by solving when moon-sun separation crosses next 12° boundary
    (swe.sol_eclipse_when_loc or root-find via swe.calc_ut).
    """

def compute_nakshatra(moon_lon: float, asof_utc: datetime) -> Anga:
    """
    Nakshatra = floor(moon_lon / (360/27)) + 1.  Range 1..27.
    Each nakshatra spans 13°20' (13.333...°). Pada = floor((moon_lon mod 13.333)/3.333) + 1.
    end_utc = moment moon reaches next nakshatra boundary.
    """

def compute_yoga(sun_lon: float, moon_lon: float, asof_utc: datetime) -> Anga:
    """
    Yoga = floor((sun_lon + moon_lon) % 360 / (360/27)) + 1.  Range 1..27.
    end_utc = moment (sun_lon + moon_lon) crosses next 13°20' boundary.
    """

def compute_karana_pair(sun_lon: float, moon_lon: float, asof_utc: datetime, sunrise_utc: datetime) -> tuple[Anga, Anga]:
    """
    Karana = half a tithi (6° of separation). Each tithi has 2 karanas.
    There are 11 karanas: 7 movable (Bava, Balava, Kaulava, Taitila, Garaja, Vanija, Vishti=Bhadra)
    cycle through 56 of the 60 half-tithis, and 4 fixed (Shakuni, Chatushpada, Naga, Kintughna)
    occupy the last 4 half-tithis.
    Returns (karana_at_sunrise, karana_after_first_transition_within_day).
    """

def compute_vara(date: date) -> Anga:
    """
    Vara = day of week (Hindu sunrise-to-sunrise convention).
    1=Ravivara(Sun), 2=Somavara(Mon), 3=Mangalavara(Tue),
    4=Budhavara(Wed), 5=Guruvara(Thu), 6=Shukravara(Fri), 7=Shanivara(Sat).
    end_utc = next sunrise at the location (passed in from timings.py).
    """
```

Implementation notes:
- All longitudes are sidereal (Lahiri). Use `swe.FLG_SIDEREAL | swe.FLG_SWIEPH` flag.
- Boundary crossing for `end_utc`: bisection between sunrise of current day and sunrise of day+2 (covers transitions that fall during the next solar day too). Target precision: ±1 second on the boundary.
- All datetime returns are UTC. Caller's responsibility to convert to local.

**AC.4C1S1.4:** All 5 anga functions implemented; `test_angas.py` covers each with at least 3 cases (a known boundary, a mid-anga, a leap/zero-crossing edge); all tests pass.

### Item 5 — `planets.py` — planetary state

**What:**

```python
def compute_planet_state(planet: int, jd_ut: float) -> PlanetState:
    """
    planet: swe.SUN .. swe.PLUTO; also swe.MEAN_NODE for Rahu (per Phase 4B
    standard — TRUE_NODE was the bug). Ketu = Rahu + 180 (mod 360).
    Returns sidereal longitude, sign, nakshatra+pada, retrograde flag,
    combust flag (Sun within combustion orb per planet — see CLASSICAL_ORBS in
    shastra_tables.py).
    """

NINE_GRAHAS = [swe.SUN, swe.MOON, swe.MARS, swe.MERCURY, swe.JUPITER,
               swe.VENUS, swe.SATURN, swe.MEAN_NODE]  # 8 + derived Ketu = 9

def compute_all_grahas(jd_ut: float) -> list[PlanetState]:
    """Returns 9 PlanetState objects (Sun, Moon, Mars, Mercury, Jupiter,
    Venus, Saturn, Rahu, Ketu) at the given Julian Day."""
```

Combustion orbs (Drik convention) — populate in `shastra_tables.py`:
- Moon: 12°
- Mars: 17°
- Mercury: 14° (direct), 12° (retro)
- Jupiter: 11°
- Venus: 10° (direct), 8° (retro)
- Saturn: 15°
- Mean Node (Rahu/Ketu): not combust (always; document the rule)

**Rahu/Ketu rule:** ALWAYS use `swe.MEAN_NODE` (not `TRUE_NODE`). Add an assertion that catches accidental switches. The Phase 4B campaign is converting `ephemeris_daily` to MEAN_NODE; this module must agree day-1.

**AC.4C1S1.5:** `compute_all_grahas` returns 9 PlanetStates for J2000; Rahu and Ketu are 180° apart; Sun never marked retrograde; Mean Node always marked retrograde (it always is). `test_planets.py` covers the 9-graha contract and the MEAN_NODE assertion.

### Item 6 — `timings.py` — sunrise/sunset, inauspicious, auspicious

**What:** Heavy module. Subdivide into clearly-named helpers:

```python
def compute_sunrise_sunset(date: date, lat: float, lon: float, tz_offset: int) -> tuple[datetime, datetime]:
    """
    swe.rise_trans with flag swe.CALC_RISE | swe.BIT_DISC_CENTER (Drik convention).
    Returns (sunrise_utc, sunset_utc) for the LOCAL date at the given coords.
    For polar latitudes where the sun does not rise/set, raise OutOfRangeError.
    """

def compute_moonrise_moonset(date: date, lat: float, lon: float, tz_offset: int) -> tuple[Optional[datetime], Optional[datetime]]:
    """Same pattern, swe.MOON. May return None when moon doesn't rise or set
    on the local date (this is normal at high latitudes; not an error)."""

def compute_inauspicious_timings(sunrise_utc, sunset_utc, vara_id) -> dict:
    """Returns dict with keys:
      'rahu_kalam'    — Vedic table: Mon=2, Tue=7, Wed=5, Thu=6, Fri=4, Sat=3, Sun=8.
                        Day is divided into 8 equal parts from sunrise to sunset;
                        the indexed part is Rahu Kalam.
      'yamagandam'    — Vedic table: Mon=4, Tue=3, Wed=2, Thu=1, Fri=7, Sat=6, Sun=5.
      'gulika_kalam'  — Vedic table: Mon=6, Tue=5, Wed=4, Thu=3, Fri=2, Sat=1, Sun=7.
      'dur_muhurta'   — variable; up to 2 windows per day. Compute per Drik formula
                        per vara (lookup in shastra_tables.py).
    Each value is a Timing(label, start_utc, end_utc)."""

def compute_auspicious_timings(sunrise_utc, sunset_utc, ...) -> dict:
    """Returns:
      'abhijit'        — 8th muhurta of day (24th of 30 muhurtas). Day split into 15 muhurtas
                         sunrise-to-noon, 15 noon-to-sunset; abhijit is the muhurta around
                         local noon. Not present on Wednesdays.
      'brahma_muhurta' — 96 minutes before sunrise to 48 minutes before sunrise (Drik
                         convention; cite source).
      'amrit_kalam'    — function of tithi and nakshatra (table in shastra_tables.py).
      'varjyam'        — function of nakshatra (table in shastra_tables.py).
    Each value is a Timing or list of Timings."""

def compute_choghadiya(sunrise_utc, sunset_utc, next_sunrise_utc, vara_id) -> dict:
    """8 day-segments + 8 night-segments. Each segment is named one of
    {Amrit, Shubh, Labh, Char, Rog, Kal, Udveg}.
    Lookup table indexed by (vara_id, segment_index) in shastra_tables.py.
    Returns {'day': [Timing...], 'night': [Timing...]} — 16 total."""

def compute_hora(sunrise_utc, next_sunrise_utc, vara_id) -> list[Timing]:
    """24 planetary hours, each spanning 1/24 of the day-and-night.
    Starting hour is the vara lord; sequence is the Chaldean order:
    Sat→Jup→Mar→Sun→Ven→Mer→Moon, repeating.
    Returns 24 Timings labeled 'hora_sun', 'hora_moon', etc."""
```

Note on Day vs Night Choghadiya / Hora boundary: standard is sunrise → sunset = "day", sunset → next sunrise = "night". This requires the next day's sunrise for the night choghadiya end-time. Compute it lazily.

**AC.4C1S1.6:** All 6 functions implemented; `test_timings.py` covers Bhubaneswar (20.27°N, 85.84°E) for a known date (e.g. 2026-05-19) with expected sunrise/sunset windows within 30 sec of Drik's published values; Rahu Kalam for that date matches Drik's published window within 2 min.

### Item 7 — `shastra_tables.py` — static lookup tables (partial population)

**What:** Pure data file. Populate this session:

- `TITHI_NAMES`: dict[int, str] — 30 entries
- `NAKSHATRA_NAMES`: list[str] — 27 entries (Ashwini through Revati)
- `NAKSHATRA_DEITIES`: list[str] — 27 entries
- `NAKSHATRA_LORDS`: list[str] — 27 entries (cyclic Vimshottari sequence)
- `YOGA_NAMES`: list[str] — 27 entries (Vishkambha through Vaidhriti)
- `KARANA_NAMES`: list[str] — 11 entries
- `VARA_NAMES`: dict[int, dict] — 7 entries with name (Sanskrit + English), lord, color
- `SIGN_NAMES`: list[str] — 12 entries (Mesha through Meena)
- `SIGN_LORDS`: list[str] — 12 entries
- `RAHU_KALAM_INDEX`: dict[int, int] — 7 entries (vara_id → 1..8 segment index)
- `YAMAGANDAM_INDEX`: dict[int, int]
- `GULIKA_INDEX`: dict[int, int]
- `CHOGHADIYA_DAY_TABLE`: dict[int, list[str]] — vara_id → 8 names (Mon..Sun)
- `CHOGHADIYA_NIGHT_TABLE`: dict[int, list[str]] — vara_id → 8 names
- `HORA_CYCLE`: list[str] — `["Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"]` (Chaldean order)
- `VARA_HORA_START`: dict[int, str] — vara_id → starting planet at sunrise
- `COMBUSTION_ORBS`: dict[str, dict] — per planet: {"direct": deg, "retro": deg}
- `AMRIT_KALAM_TABLE`: nested dict by tithi × nakshatra (subset to start — extend in S2)
- `VARJYAM_TABLE`: dict by nakshatra
- `DUR_MUHURTA_TABLE`: dict by vara
- Special yoga lookup tables (`SARVARTHA_SIDDHI_TABLE`, `AMRIT_SIDDHI_TABLE`, etc.) — **STUB SHELL ONLY** this session; populated in 4C-1-S2

Every table has an inline comment citing the classical source (Muhurta Chintamani, Brihat Samhita, or Drik Panchang's published reference if no classical citation found).

**AC.4C1S1.7:** `shastra_tables.py` exists; the 18 named tables present and populated; the 4 special-yoga tables are stub shells with `# 4C-1-S2 populates this` comment; module imports clean.

### Item 8 — `__init__.py` — public API

**What:** Declare the public surface:

```python
__version__ = "1.0.0-S1"

from .ayanamsha import set_ayanamsha, get_ayanamsha_value, DEFAULT_AYANAMSHA
from .types import Panchang, Anga, Timing, PlanetState, MuhuratWindow, NatalChart
from .exceptions import (
    PanchangEngineError, AyanamshaError, OutOfRangeError, ValidationError,
)

def compute_panchang(date, lat, lon, tz_offset) -> Panchang:
    """High-level: full Panchang for a single day. See README."""
    # Wire: set_ayanamsha → timings.sunrise/sunset → planets.compute_all_grahas
    #       → angas.compute_* → timings.compute_inauspicious/auspicious/choghadiya/hora
    #       → special_yogas.compute_active (STUB — returns []) → assemble Panchang
    ...

def find_muhurat(event, date_from, date_to, lat, lon, native_chart=None):
    """STUB this session — raises NotImplementedError(
        '4C.6 implements Muhurat Finder. 4C-1-S1 only wires the entry point.')"""
    raise NotImplementedError(...)

def panchang_range(date_from, date_to, lat, lon, tz_offset) -> list[Panchang]:
    """Loop compute_panchang(). For batch use (calendar feed)."""
    ...
```

**AC.4C1S1.8:** `from panchang_engine import compute_panchang, panchang_range` works; calling `compute_panchang(date(2026,5,19), 20.27, 85.84, 330)` returns a fully-populated `Panchang` (special_yogas list is empty — that's expected for S1).

### Item 9 — `exceptions.py`

**What:** Exception class hierarchy:

```python
class PanchangEngineError(Exception):
    """Root exception for all panchang_engine errors."""

class AyanamshaError(PanchangEngineError):
    """Invalid ayanamsha mode or computation failure."""

class OutOfRangeError(PanchangEngineError):
    """Date/location outside computable range (polar latitudes, ephemeris bounds)."""

class ValidationError(PanchangEngineError):
    """Input validation failure (bad lat/lon/date)."""
```

**AC.4C1S1.9:** Module imports clean; exception hierarchy correct.

### Item 10 — Drik Panchang fixture v1 (10 days)

**What:** Author `tests/fixtures/drik_panchang_v1.json`. Ten cherry-picked days that stress different parts of the engine. Recommended selection:

| Date (IST) | Why this day |
|---|---|
| 2025-01-14 | Makara Sankranti — Sun ingress to Capricorn; near-zero Sun longitude transition |
| 2025-03-29 | New Moon (Amavasya); pakshanta boundary |
| 2025-04-13 | Bisuva Sankranti (Mesha) — solar new year |
| 2025-08-09 | Sawan Shivaratri — Monday Krishna Chaturdashi |
| 2025-10-20 | Karwa Chauth — full moon period, complex tithi-nakshatra boundaries |
| 2025-11-15 | Ekadashi (specifically Devuthani) — high-fasting tithi |
| 2026-01-26 | Republic Day (India) — for civic recognizability |
| 2026-02-05 | Native's birthday (Abhisek's natal date) — Bhubaneswar |
| 2026-05-19 | Today — known reference; should match Drik exactly at 20.27°N, 85.84°E |
| 2026-08-15 | Independence Day — Krishna paksha mid |

For each day, capture from drikpanchang.com (Bhubaneswar, IN as location):
- tithi name + Drik's transition end-time
- nakshatra name + transition end-time
- yoga name + transition end-time
- karana first + second
- vara
- sunrise + sunset (HH:MM, local IST)
- moonrise + moonset (where present)
- rahu kalam window
- yamagandam window
- gulika kalam window
- abhijit window (if applicable — not on Wednesdays)

Encode as a JSON list of 10 objects with that schema. Add a `_meta` block at the top: `{"source": "drikpanchang.com", "location": "Bhubaneswar, IN (20.27°N, 85.84°E, tz +05:30)", "captured_at": "<ISO timestamp>", "expected_match_tolerance": {...}}`.

**AC.4C1S1.10:** Fixture JSON exists; 10 entries; schema-conformant; `_meta` block present with location and tolerance.

### Item 11 — Drik parity test (`test_drik_parity.py`)

**What:**

```python
import json
import pytest
from datetime import datetime, date
from panchang_engine import compute_panchang

with open("tests/fixtures/drik_panchang_v1.json") as f:
    FIXTURE = json.load(f)

ENTRIES = FIXTURE["entries"]
TOLERANCES = FIXTURE["_meta"]["expected_match_tolerance"]
# {
#   "anga_id": "exact",
#   "anga_transition": "120 sec",
#   "sunrise_sunset": "30 sec",
#   "rahu_yama_gulika": "120 sec",
# }

@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["date"])
def test_drik_parity_for_day(entry):
    panchang = compute_panchang(
        date.fromisoformat(entry["date"]),
        entry["lat"], entry["lon"], entry["tz_offset_minutes"],
    )
    # Anga IDs: exact match
    assert panchang.tithi.id == entry["expected"]["tithi_id"]
    assert panchang.nakshatra.id == entry["expected"]["nakshatra_id"]
    assert panchang.yoga.id == entry["expected"]["yoga_id"]
    assert panchang.vara.id == entry["expected"]["vara_id"]
    # Anga transition: within 2 minutes
    assert abs((panchang.tithi.end_utc - entry["expected"]["tithi_end_utc"]).total_seconds()) <= 120
    # ... (nakshatra, yoga, karana transitions)
    # Sunrise/sunset: within 30 seconds
    assert abs((panchang.sunrise_utc - entry["expected"]["sunrise_utc"]).total_seconds()) <= 30
    assert abs((panchang.sunset_utc - entry["expected"]["sunset_utc"]).total_seconds()) <= 30
    # Rahu/Yama/Gulika: within 2 minutes start AND end
    # ... (loop the 3 inauspicious timings)
```

**This is the validation gate.** If any single fixture day fails, the failure must be diagnosed before claiming session close. Permitted resolutions:
- Bug in panchang_engine (fix and re-run)
- Bug in fixture capture (re-capture, document the correction in the fixture _meta)
- Drik Panchang itself rounds (rare; document tolerance widening in _meta with reason)

**AC.4C1S1.11:** `pytest tests/test_drik_parity.py -v` reports 10/10 PASS. If any FAIL, the session does NOT claim close — diagnose and resolve or escalate to native.

### Item 12 — README.md + commit message discipline

**What:** Write `platform/sidecar/panchang_engine/README.md`:

- §1 — Purpose: deterministic Panchang computation, Drik-parity, no LLM
- §2 — Public API (the three functions from `__init__.py`)
- §3 — Layering: this engine returns facts only; interpretation happens in `panchang/synthesis/`
- §4 — Ayanamsha: Lahiri default (cite reason)
- §5 — Sunrise definition: visible upper limb + atmospheric refraction (Drik convention) — `BIT_DISC_CENTER` is NOT used despite the swisseph constant name suggesting it; clarify in code comment
- §6 — Run tests: `cd platform/sidecar/panchang_engine && pytest -v`
- §7 — Drik validation gate: 10/10 on `drik_panchang_v1.json` (S1); 30/30 on `drik_panchang_v2.json` (S2); special yogas added S2
- §8 — Versioning: `__version__` tracks (semver) + session suffix until 4C.1 closes
- §9 — TODOs queued for 4C-1-S2: special_yogas implementation, extend fixture to 30 days, muhurat scoring scaffolding

**Commit discipline:** one commit per item above (12 commits). Commit message format: `4C-1-S1 Item N: <one-line summary>`. The README+commit-discipline step is its own commit.

**AC.4C1S1.12:** README present; commits show 12 distinct items; final commit count for the session = 12 + 1 session-close = 13.

---

## §4 — Mirror discipline

**No mirror updates this session.** All changes are inside `platform/sidecar/panchang_engine/` — application code path, not governance. MP.1 + MP.2 do NOT trigger for Python module additions.

If you find yourself touching anything outside `platform/sidecar/` or the test directory, halt and reconsider — that's out of scope for 4C-1-S1.

---

## §5 — Constraints

**may_touch (in `/Users/Dev/Vibe-Coding/Apps/Panchang`):**

- `platform/sidecar/panchang_engine/**` (all new files this session)
- `platform/sidecar/requirements.txt` or `pyproject.toml` (add `pyswisseph` if not present)
- `00_ARCHITECTURE/SESSION_LOG.md` (append 4C-1-S1 entry at session close)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (advance `last_session_id` in the Phase 4C concurrent_workstreams block; do NOT touch the M5 fields)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md` (only to flip frontmatter `status: READY` → `status: COMPLETE` at session-end)
- `CLAUDECODE_BRIEF.md` at worktree root (delete at session end)

**must_not_touch:**

- `platform/src/` (no app code — that's 4C.3+)
- `platform/migrations/` (no schema — that's 4C.2)
- `platform/sidecar/` files outside `panchang_engine/` (don't touch the ephemeris sidecar — Phase 4B owns it)
- `01_FACTS_LAYER/*`, `025_HOLISTIC_SYNTHESIS/*`, `035_DISCOVERY_LAYER/*` (corpus is frozen this session)
- `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` (plan is sealed; no in-session edits)
- `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` (operational brief sealed; no edits)
- `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` (schema doc finalized in 4C-0; no edits)
- `CLAUDE.md`, `CAPABILITY_MANIFEST.json` (governance frozen this session)
- `.geminirules`, `.gemini/project_state.md` (no mirror updates this session)
- Anything on the M5-A worktree's owned paths (cross-stream contamination)

If something in must_not_touch needs to change, halt and report to native — do not attempt cross-stream work in this session.

---

## §6 — Session-close checklist

- [ ] SESSION_OPEN artifact emitted and validates
- [ ] All 12 AC checks completed (AC.4C1S1.1 through AC.4C1S1.12)
- [ ] `pytest platform/sidecar/panchang_engine/tests/ -v` reports 100% pass
- [ ] `test_drik_parity.py` shows 10/10 PASS (the gate)
- [ ] `pyswisseph` is installable; importable; version recorded in commit message
- [ ] 12 scope commits + 1 session-close commit on `feature/phase-4c-panchang`
- [ ] CURRENT_STATE_v1_0.md Phase 4C block updated: `last_session_id: 4C-1-S1`; `next_session_objective: 4C-1-S2 — special_yogas + extend fixture to 30 days + muhurat scaffold`
- [ ] SESSION_LOG.md 4C-1-S1 atomic entry appended
- [ ] CLAUDECODE_BRIEF.md at worktree root removed; staged brief flipped to `status: COMPLETE`
- [ ] SESSION_CLOSE artifact emitted and validates
- [ ] If any Drik fixture day FAILED and is not yet resolved: do NOT claim close; instead emit a `SESSION_HALT` with the failing day + diagnosis + ask native for resolution

---

## §7 — LLM stack for this session

| Role | Model | Notes |
|---|---|---|
| Primary inference | Gemini (gemini-2.5-pro for code, flash for chat tasks) | Default |
| Fallback | DeepSeek v4 Pro | |
| Tertiary | NIM | |
| Anthropic/Claude API | **BANNED** | Per memory file 2026-05-19 |

This session is mostly mechanical Python + swisseph wrapping; minimal LLM token spend expected.

---

## §8 — Context carried (do not re-derive)

- **Ayanamsha = Lahiri.** Drik default; Indian government standard since 1955. Configurable per call but Lahiri is the project default.
- **Rahu = MEAN_NODE (always).** TRUE_NODE was the Phase 4B bug; we agree day-1. Add an assertion that catches accidental switches.
- **Sunrise definition = visible upper limb + atmospheric refraction.** This is Drik's convention; `swe.rise_trans` with `swe.CALC_RISE` flag (NOT `BIT_DISC_CENTER`) gives the right answer. Document this in README §5 (the swisseph naming is misleading).
- **Tolerance gate:** anga IDs exact; anga transitions ±2 min; sunrise/sunset ±30 sec; rahu/yama/gulika ±2 min. Encoded in fixture `_meta`.
- **Special yogas DEFERRED to 4C-1-S2.** `special_yogas.py` is a stub this session; `Panchang.special_yogas = []`. Don't implement; don't test; just scaffold the entry point.
- **Muhurat scoring DEFERRED to 4C.6.** `muhurat.py` is a stub raising NotImplementedError. Just scaffold the entry point and document.
- **Drik fixture days for S1 = 10 cherry-picked dates** (per Item 10 table). S2 extends to 30 with random sampling across 2020–2026.
- **Native's birth coords for fixture parity check:** Bhubaneswar, IN — 20.27°N, 85.84°E, tz +05:30. One fixture day is 2026-02-05 (native's birthday) — gives us a real-corpus parity anchor against FORENSIC.
- **CAPABILITY_MANIFEST `PANCHANG_DAILY_v1_0` status remains PLANNED** at end of this session. Status flips to IN_DEVELOPMENT in 4C-1-S2 (when special yogas land), and to CURRENT in 4C.2 (when the SQL backfill completes).

---

## §9 — On status flip for 4C-1-S1

When all 12 ACs pass and the session-close checklist is complete, flip the frontmatter of THIS brief in the worktree from `status: READY` → `status: COMPLETE`. Per CLAUDE.md §C.0, this signals the dispatcher slot is free for the 4C-1-S2 brief.

```bash
# At end of session:
rm /Users/Dev/Vibe-Coding/Apps/Panchang/CLAUDECODE_BRIEF.md
# Frontmatter flipped on the staged copy via Edit, then committed.
```

---

*End of CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md — authored 2026-05-19 in Cowork session.*
*Executor: Claude Code (Antigravity / VS Code extension). Branch: feature/phase-4c-panchang. Worktree: /Users/Dev/Vibe-Coding/Apps/Panchang. Session: 4C-1-S1.*
*Governing plan: PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.3 (computation engine) + §6 Phase 4C.1.*
