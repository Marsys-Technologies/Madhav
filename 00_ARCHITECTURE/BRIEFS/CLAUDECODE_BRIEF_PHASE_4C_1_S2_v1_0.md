---
artifact: CLAUDECODE_BRIEF_PHASE_4C_1_S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-19
authored_at: 2026-05-19
session_id: 4C-1-S2
session_name: 4C-1-S2 — special_yogas + 30-day Drik Fixture + Muhurat Scaffold + 4C-1 Close
executor: Claude Code sub-agent (spawned by Conductor)
execution_mode: autonomous, --dangerously-skip-permissions
worktree:
  name: Panchang
  branch: feature/phase-4c-panchang
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.3 + §6 (Phase 4C.1)
operational_brief: 00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md
predecessor_session: 4C-1-S1 (closed cleanly — panchang_engine scaffold + core math + 10-day Drik fixture v1; 10/10 parity PASS; 69 tests; 9 commits)
target_subphase: 4C.1 close (S2 is the closing session for the panchang_engine sub-phase if the 30/30 gate passes; 4C-1-S3 in the queue becomes optional polish or is skipped)
next_session_anticipated: 4C-2 (cache + sidecar wiring — GATED on Phase 4B closing per queue manifest)
---

# CLAUDECODE_BRIEF — Phase 4C-1-S2
## special_yogas + 30-day Drik Fixture + Muhurat Scaffold + 4C-1 Close

---

## §0 — How to start this session (when run autonomously by Conductor)

You are spawned by the Conductor orchestrator (CONDUCTOR-S0 closed at commit `42efa9c`). You inherit a fresh 200K context window. You operate inside the Panchang worktree at `/Users/Dev/Vibe-Coding/Apps/Panchang` on branch `feature/phase-4c-panchang`. You have `--dangerously-skip-permissions`.

When the Conductor passes you this brief, read in order:

1. `CLAUDE.md` (§C mandatory reads)
2. This brief (full)
3. The §2 Mandatory Reads below

Then begin Item 1. Emit `---FINAL_SUMMARY---` per the Conductor's sub-agent prompt template when done.

**Pre-flight integrity check (do FIRST before any work):** verify `platform/python-sidecar/panchang_engine/` exists from 4C-1-S1, the 10-day fixture validates, and the engine is in the state S1's final commit left it in:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
ls platform/python-sidecar/panchang_engine/
test -f platform/python-sidecar/panchang_engine/__init__.py
test -f platform/python-sidecar/panchang_engine/special_yogas.py   # exists as stub from S1
test -f platform/python-sidecar/panchang_engine/tests/fixtures/drik_panchang_v1.json
cd platform/python-sidecar/panchang_engine && pytest -q
# Expected: all S1 tests pass — DO NOT proceed if anything fails
```

If pre-flight fails, halt with `HALT_NEEDS_HUMAN` — something has drifted in the worktree since S1 closed.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | 4C-1-S2 |
| Cowork thread name (for SESSION_LOG attribution) | `Phase 4C-1-S2 special_yogas + Drik Fixture v2 + Muhurat Scaffold 2026-05-19` |
| Branch | `feature/phase-4c-panchang` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/Panchang` |
| Sidecar engine path | `platform/python-sidecar/panchang_engine/` (S1 used this; S2 continues here) |
| Execution mode | Autonomous sub-agent, `--dangerously-skip-permissions` |
| Predecessor | 4C-1-S1 (closed cleanly; 9 commits; 10/10 Drik parity; 69 tests) |
| Anticipated next | 4C-2 (queue advances if 4C-1-S3 marked skipped post-close; otherwise 4C-1-S3 polish) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 (active state — Phase 4C ACTIVE, sub-phase 4C-1 OPEN)
3. `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` §5.3 (computation engine spec — re-read for special_yogas + muhurat sections); §6 Phase 4C.1 acceptance criteria; §10 Risks (mitigations relevant to S2)
4. `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S1_v1_0.md` — the predecessor brief (so you know what was scaffolded vs stubbed)
5. `platform/python-sidecar/panchang_engine/__init__.py` (current public API — for the version bump and the `special_yogas` non-empty change)
6. `platform/python-sidecar/panchang_engine/types.py` (the `Panchang` dataclass — `special_yogas` field; the `MuhuratWindow` dataclass for the muhurat scaffold)
7. `platform/python-sidecar/panchang_engine/shastra_tables.py` (current state — see which special-yoga tables are stubs)
8. `platform/python-sidecar/panchang_engine/special_yogas.py` (current state — likely raises NotImplementedError)
9. `platform/python-sidecar/panchang_engine/muhurat.py` (current state — likely raises NotImplementedError)
10. `platform/python-sidecar/panchang_engine/tests/fixtures/drik_panchang_v1.json` (the 10-day fixture from S1 — schema is the template you'll extend)
11. `platform/python-sidecar/panchang_engine/tests/test_drik_parity.py` (S1's parity test — you'll extend its parameterization)
12. `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` (the schema this engine populates — `special_yogas` JSONB field semantics)

Then emit the session_open block (you're inside a Conductor sub-agent so the SESSION_OPEN artifact is implicit — but commit the artifact to `00_ARCHITECTURE/SESSION_LOG.md` at session close).

---

## §3 — Scope (13 items — execute in order; commit after each)

### Item 1 — Pre-flight integrity verification

**What:** Run the pre-flight check from §0 above. Confirm S1's state is intact. If anything fails, halt immediately with `HALT_NEEDS_HUMAN` — do NOT attempt repair work in this session.

**AC.4C1S2.1:** All S1 tests pass; required files exist; commit message reads `4C-1-S2 Item 1: pre-flight integrity OK`.

### Item 2 — Author `shastra_tables.py` special-yoga lookup tables

**What:** Replace the four stub tables flagged in S1 (`SARVARTHA_SIDDHI_TABLE`, `AMRIT_SIDDHI_TABLE`, etc.) and add the remaining tables needed for the MVP yoga set. Final populated list:

```python
# Sarvartha Siddhi Yoga — vara × nakshatra combinations (auspicious for all purposes)
# Source: Muhurta Chintamani 5.16; Drik Panchang's authoritative table
SARVARTHA_SIDDHI_TABLE = {
    1: {3, 5, 8, 11, 19},     # Ravi (Sun): Krittika, Mrigashira, Pushya, Purva Phalguni, Mula
    2: {1, 6, 18, 21, 22},    # Soma (Mon): Ashwini, Ardra, Anuradha, Uttara Ashadha, Shravana
    3: {1, 6, 14},            # Mangala (Tue): Ashwini, Ardra, Chitra
    4: {3, 8, 14, 17, 24},    # Budha (Wed): Krittika, Pushya, Chitra, Anuradha, Shatabhisha
    5: {5, 7, 8, 22, 27},     # Guru (Thu): Mrigashira, Punarvasu, Pushya, Shravana, Revati
    6: {1, 2, 5, 21, 22, 27}, # Shukra (Fri): Ashwini, Bharani, Mrigashira, Uttara Ashadha, Shravana, Revati
    7: {4, 8, 23, 26},        # Shani (Sat): Rohini, Pushya, Swati, Uttara Bhadrapada
}

# Amrita Siddhi Yoga — vara × nakshatra combinations (most auspicious for new beginnings)
# Source: Muhurta Chintamani; tighter set than Sarvartha
AMRIT_SIDDHI_TABLE = {
    1: {8},      # Sun + Pushya = Ravi Pushya component
    2: {4},      # Moon + Rohini
    3: {6},      # Mars + Ardra
    4: {1},      # Mercury + Ashwini
    5: {8},      # Jupiter + Pushya = Guru Pushya component
    6: {27},     # Venus + Revati
    7: {25},     # Saturn + Purva Bhadrapada (some sources) — verify against Drik
}

# Ravi Pushya Yoga — Sunday AND Pushya nakshatra simultaneously (rare; ~6-8 times/year)
# This is a special case of Sarvartha Siddhi; tracked separately for prominence in Drik Panchang display
RAVI_PUSHYA = {"vara_id": 1, "nakshatra_id": 8}

# Guru Pushya Yoga — Thursday AND Pushya nakshatra simultaneously (very auspicious for wealth)
GURU_PUSHYA = {"vara_id": 5, "nakshatra_id": 8}

# Tripushkar Yoga — tithi + vara + nakshatra combination yielding "three" multiplier
# (purchases on this day are said to triple). Conditions:
#   tithi_remainder in {2, 7, 12} (i.e., Dvitiya, Saptami, Dwadashi)
#   vara_id in {1, 3, 7} (Sun, Tue, Sat)
#   nakshatra is one of the dvi-svabhava (Krittika, Punarvasu, Uttara Phalguni, Vishakha, Uttara Ashadha, Purva Bhadrapada)
TRIPUSHKAR_TITHIS = {2, 7, 12}
TRIPUSHKAR_VARAS = {1, 3, 7}
TRIPUSHKAR_NAKSHATRAS = {3, 7, 12, 16, 21, 25}

# Dwipushkar Yoga — like Tripushkar but "double" multiplier; nakshatras differ
# Conditions: same tithi + vara set; nakshatras are dvi-svabhava restricted further
DWIPUSHKAR_TITHIS = {2, 7, 12}
DWIPUSHKAR_VARAS = {1, 3, 7}
DWIPUSHKAR_NAKSHATRAS = {5, 14, 23}   # Mrigashira, Chitra, Dhanishtha

# Siddha Yoga — auspicious composite of vara + nakshatra (different from Sarvartha Siddhi)
# Source: Muhurta tables; subset of vara-nakshatra space
SIDDHA_YOGA_TABLE = {
    1: {1, 6, 11, 16, 21, 26},
    2: {2, 7, 12, 17, 22, 27},
    3: {3, 8, 13, 18, 23},
    4: {4, 9, 14, 19, 24},
    5: {5, 10, 15, 20, 25},
    6: {1, 6, 11, 16, 21, 26},
    7: {2, 7, 12, 17, 22, 27},
}

# Bhadra Karana (Vishti) — inauspicious; one of the 11 karanas
# Vishti is karana_id == 7 in the movable-karana cycle.
# Detection: any karana_first.id == 7 OR karana_second.id == 7 in the Panchang.
# Bhadra has two flavors — Mukhya (face/start) and Punccha (tail/end) — Drik
# convention: the half-tithi where Bhadra falls is the inauspicious window.
BHADRA_KARANA_ID = 7

# Panchaka Doshas — five inauspicious nakshatras for certain activities
# Source: Brihat Samhita; Drik Panchang display
PANCHAKA_NAKSHATRAS = {23, 24, 25, 26, 27}  # Dhanishtha, Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada, Revati
# When Moon is in these nakshatras AND vara is one of Sat/Sun/Tue, certain activities are avoided
PANCHAKA_VARAS = {7, 1, 3}
```

Add an inline citation comment block at the top of each table referencing the classical source (Muhurta Chintamani / Brihat Samhita) or — where no classical citation is found — Drik Panchang's published tables.

**AC.4C1S2.2:** All 9 tables populated with non-stub data; `shastra_tables.py` imports clean; commit message reads `4C-1-S2 Item 2: special-yoga shastra tables populated`.

### Item 3 — Author `special_yogas.py` detection logic

**What:** Replace S1's NotImplementedError stub with real detection functions. The module exposes:

```python
from datetime import datetime, date
from .types import Anga, Timing
from .shastra_tables import (
    SARVARTHA_SIDDHI_TABLE, AMRIT_SIDDHI_TABLE,
    RAVI_PUSHYA, GURU_PUSHYA,
    TRIPUSHKAR_TITHIS, TRIPUSHKAR_VARAS, TRIPUSHKAR_NAKSHATRAS,
    DWIPUSHKAR_TITHIS, DWIPUSHKAR_VARAS, DWIPUSHKAR_NAKSHATRAS,
    SIDDHA_YOGA_TABLE,
    BHADRA_KARANA_ID,
    PANCHAKA_NAKSHATRAS, PANCHAKA_VARAS,
)

# Each detection function returns a list[Timing] — empty list = yoga not active that day.
# Multiple windows possible per day when nakshatra/tithi transitions split the activity period.

def detect_sarvartha_siddhi(vara_id, nakshatra, sunrise_utc, next_sunrise_utc) -> list[Timing]:
    """Active when vara × nakshatra is in SARVARTHA_SIDDHI_TABLE.
    Window: from sunrise to whichever ends first — nakshatra transition or next sunrise."""

def detect_amrit_siddhi(vara_id, nakshatra, sunrise_utc, next_sunrise_utc) -> list[Timing]:
    """Active when vara × nakshatra matches AMRIT_SIDDHI_TABLE.
    NOTE: Amrit Siddhi is BLOCKED by certain tithi-vara combinations (death yoga overrides).
    Detection should check those exclusions — see Drik Panchang's footnotes for the list."""

def detect_ravi_pushya(vara_id, nakshatra, sunrise_utc, next_sunrise_utc) -> list[Timing]:
    """Sunday + Pushya. Window = nakshatra Pushya duration within Sunday's sunrise-to-next-sunrise."""

def detect_guru_pushya(vara_id, nakshatra, sunrise_utc, next_sunrise_utc) -> list[Timing]:
    """Thursday + Pushya. Same window logic as Ravi Pushya."""

def detect_tripushkar(tithi, vara_id, nakshatra, sunrise_utc, next_sunrise_utc) -> list[Timing]:
    """All three conditions must hold simultaneously.
    Tripushkar requires tithi.id in TRIPUSHKAR_TITHIS, vara_id in TRIPUSHKAR_VARAS,
    nakshatra.id in TRIPUSHKAR_NAKSHATRAS."""

def detect_dwipushkar(tithi, vara_id, nakshatra, sunrise_utc, next_sunrise_utc) -> list[Timing]:
    """Like Tripushkar but with DWIPUSHKAR_NAKSHATRAS."""

def detect_siddha_yoga(vara_id, nakshatra, sunrise_utc, next_sunrise_utc) -> list[Timing]:
    """Active when vara × nakshatra matches SIDDHA_YOGA_TABLE."""

def detect_bhadra(karana_first, karana_second, sunrise_utc, next_sunrise_utc) -> list[Timing]:
    """Active when either karana of the day is Vishti (id=7).
    Window = the half-tithi spanned by the Vishti karana."""

def detect_panchaka(nakshatra, vara_id, sunrise_utc, next_sunrise_utc) -> list[Timing]:
    """Active when nakshatra.id in PANCHAKA_NAKSHATRAS AND vara_id in PANCHAKA_VARAS.
    Window = nakshatra duration within the day."""

# Main entry point — called from compute_panchang() in __init__.py
def detect_all_special_yogas(
    sunrise_utc, sunset_utc, next_sunrise_utc,
    tithi, nakshatra, yoga, karana_first, karana_second, vara,
) -> list[dict]:
    """Returns list of detected yogas with structure:
    [{"yoga": "sarvartha_siddhi", "start_utc": ..., "end_utc": ..., "strength": "auspicious|inauspicious", "stars": 1..5}]
    Iterates through all 9 detection functions; aggregates non-empty results.
    Star rating per yoga:
      - Amrit Siddhi: 5 stars (highest auspicious)
      - Ravi Pushya / Guru Pushya: 5 stars
      - Sarvartha Siddhi: 4 stars
      - Tripushkar: 4 stars
      - Siddha Yoga: 3 stars
      - Dwipushkar: 3 stars
      - Bhadra: inauspicious (no stars; warning flag)
      - Panchaka: inauspicious (no stars; warning flag)"""
```

Implementation notes:
- All windows in UTC; caller converts to local for display
- Yoga windows must clip to within sunrise → next_sunrise; never extend beyond the day's frame
- If a nakshatra transition happens mid-day, the yoga active in the FIRST nakshatra ends at the transition; if the new nakshatra also qualifies, a NEW yoga window starts (don't merge)
- Bhadra exclusions for Amrit Siddhi: check Muhurta Chintamani 5.17 — certain death-yoga combinations override; if uncertain, document the exclusion as a TODO with a placeholder rule that doesn't block S2 close

**AC.4C1S2.3:** All 9 detection functions implemented; `special_yogas.py` no longer raises NotImplementedError; commit message reads `4C-1-S2 Item 3: special_yogas detection logic`.

### Item 4 — Update `__init__.py` — wire special_yogas into compute_panchang

**What:** In S1, `compute_panchang()` left `Panchang.special_yogas = []` as a deliberate stub. Now wire it up:

1. Import `detect_all_special_yogas` from `.special_yogas`
2. In `compute_panchang()`, after computing the 5 angas + timings, call:
   ```python
   special_yogas = detect_all_special_yogas(
       sunrise_utc, sunset_utc, next_sunrise_utc,
       tithi, nakshatra, yoga, karana_first, karana_second, vara,
   )
   ```
3. Pass `special_yogas` into the `Panchang(...)` constructor (was empty list before)
4. Bump `__version__` from `"1.0.0-S1"` to `"1.0.0-S2"`
5. Update the docstring/comment in `compute_panchang` to remove the "S1 stub" note

**AC.4C1S2.4:** `compute_panchang()` returns Panchangs with populated `special_yogas`; `__version__ == "1.0.0-S2"`; commit message reads `4C-1-S2 Item 4: wire special_yogas into compute_panchang + version bump`.

### Item 5 — Test suite for special yogas (`test_special_yogas.py`)

**What:** New test file. For each of the 9 detected yogas, at least 3 test cases:
- **Positive case:** a known day where the yoga IS active (cite Drik Panchang as the oracle)
- **Negative case:** a known day where the yoga is NOT active (different vara or nakshatra)
- **Boundary case:** a day where the activating nakshatra transitions mid-day (verify window clips correctly)

Reference dates (use Bhubaneswar 20.27°N, 85.84°E, tz +05:30):
- Guru Pushya Yoga: Thursday + Pushya — find dates via Drik (typically 8-12/year)
- Ravi Pushya Yoga: Sunday + Pushya — find dates via Drik
- Sarvartha Siddhi: most common; pick 5+ varied combinations
- Amrit Siddhi: rarer (~3-5x/year); cite specific dates from Drik
- Tripushkar/Dwipushkar: rare; cite dates from Drik's 2024-2026 archive
- Bhadra: common (every karana cycle); pick days with Vishti karana
- Panchaka: cite Moon-in-Dhanishtha-on-Saturday-type combinations

Total target: ~30 test cases across 9 yogas. Use `@pytest.mark.parametrize` for compactness.

**AC.4C1S2.5:** `test_special_yogas.py` exists; `pytest tests/test_special_yogas.py -v` reports 100% PASS; commit message reads `4C-1-S2 Item 5: special_yogas test suite — 30 cases pass`.

### Item 6 — Extend Drik fixture v1 → v2 (10 days → 30 days)

**What:** Take the existing `tests/fixtures/drik_panchang_v1.json` and extend to `tests/fixtures/drik_panchang_v2.json`. Add 20 more days. Selection methodology:

- 5 days drawn from each year 2020–2025 (random within the year; vary month + nakshatra coverage)
- 5 days from 2026 (covering remaining months of the year)
- Mix of weekdays — at least one of each vara_id 1..7 must appear
- Include at least 3 days with active special yogas (Guru Pushya, Sarvartha Siddhi, Amrit Siddhi) — pick from Drik's auspicious-day archive
- Include at least 2 days with Bhadra active
- Include at least 1 day at high latitude variant (e.g., Delhi 28.6°N for a sunrise/sunset sensitivity check)

For EACH new day, capture from drikpanchang.com:
- All fields already in v1 (tithi/nakshatra/yoga/karana/vara + transitions; sunrise/sunset/moonrise/moonset; inauspicious + auspicious timings)
- **NEW for v2:** special yogas list per Drik's display, with start/end times for each
- **NEW for v2:** Bhadra periods if any

If drikpanchang.com is unreachable or returns JS-rendered content that WebFetch can't parse, **halt with `HALT_NEEDS_HUMAN`** — do NOT fabricate fixture data. Native will pre-capture the data manually and you'll resume.

**AC.4C1S2.6:** `drik_panchang_v2.json` exists; 30 entries total (10 from v1 + 20 new); special_yogas captured for all 30 days; `_meta` block updated with `total_days: 30` and `version: 2.0`; commit message reads `4C-1-S2 Item 6: Drik fixture extended to 30 days with special-yoga capture`.

### Item 7 — Extend Drik parity test for 30 days + special_yogas assertions

**What:** Update `test_drik_parity.py`:

1. Switch fixture load from `drik_panchang_v1.json` to `drik_panchang_v2.json`
2. Existing tolerances (anga IDs exact, transitions ±2 min, sunrise/sunset ±30 sec) still apply
3. Add new assertions per day:
   - For each special yoga in the Drik fixture: assert our `compute_panchang` returns that yoga in `special_yogas`
   - For each yoga in our output: assert the start/end times are within ±2 min of Drik's published times
   - Assert NO false-positives — if Drik shows no special yogas, our output is `[]`

Parameterize across all 30 days. Use ID per day so failures are diagnosable.

**The 30/30 gate is the canary for closing 4C.1.** If any single fixture day fails — including any single special-yoga mismatch — halt and report. Permitted resolutions:
- Bug in our detection → fix, re-run
- Drik's display rounding (their times are minute-precision; ours are second) → widen tolerance and document
- Drik's table differs from a classical source we cite → declare Drik authoritative and update our table

**AC.4C1S2.7:** `pytest tests/test_drik_parity.py -v` reports 30/30 PASS; commit message reads `4C-1-S2 Item 7: Drik 30/30 parity gate PASS`.

### Item 8 — `muhurat.py` scaffold (entry points only; 4C.6 fills bodies)

**What:** Replace NotImplementedError with a structural scaffold. The functions become callable but return empty/zero results. This lets downstream callers (the future /panchang UI's Muhurat Finder) wire up without errors; the actual scoring lands in 4C.6.

```python
from datetime import date
from typing import Optional
from .types import MuhuratWindow, NatalChart

EVENTS_MVP = ["vivah", "griha_pravesh", "vyapara", "yatra", "property_purchase", "mantra_initiation"]

def is_supported_event(event: str) -> bool:
    """Whether `event` is in the curated MVP set (D2 settled 2026-05-19)."""
    return event in EVENTS_MVP

def score_muhurat(
    date: date, lat: float, lon: float, event: str,
    native_chart: Optional[NatalChart] = None,
) -> float:
    """Return a score 0..100 for the given date+event combination.
    SCAFFOLD ONLY (4C-1-S2): returns 0.0. Full scoring implemented in 4C.6 phase.
    Signature is locked here so 4C.6 can fill the body without API churn."""
    if not is_supported_event(event):
        raise ValueError(f"Event '{event}' not in MVP set. Supported: {EVENTS_MVP}")
    return 0.0

def find_muhurat(
    event: str, date_from: date, date_to: date,
    lat: float, lon: float,
    native_chart: Optional[NatalChart] = None,
) -> list[MuhuratWindow]:
    """Return top auspicious windows for `event` in [date_from, date_to].
    SCAFFOLD ONLY (4C-1-S2): returns []. Full implementation in 4C.6 phase."""
    if not is_supported_event(event):
        raise ValueError(f"Event '{event}' not in MVP set. Supported: {EVENTS_MVP}")
    return []
```

Add 3 trivial tests in `test_muhurat.py`:
- `is_supported_event("vivah") == True`
- `is_supported_event("invalid") == False`
- `find_muhurat("vivah", date(2026,1,1), date(2026,1,31), 20.27, 85.84) == []`

**AC.4C1S2.8:** `muhurat.py` scaffold present (no NotImplementedError); 3 tests pass; commit message reads `4C-1-S2 Item 8: muhurat.py scaffold (4C.6 fills bodies)`.

### Item 9 — Update README.md

**What:** Update `platform/python-sidecar/panchang_engine/README.md`:

- §7 — Drik validation gate: update from "10/10 on `drik_panchang_v1.json` (S1); 30/30 on `drik_panchang_v2.json` (S2)" to "30/30 PASS on `drik_panchang_v2.json` as of 4C-1-S2 close"
- §8 — Versioning: bump to `1.0.0-S2`
- §9 — Remove the "4C-1-S2 TODOs" section; everything's done
- Add a new §10 — "Future work (deferred to 4C.6)" noting `muhurat.py` body implementation, full Muhurat Finder scoring rubric

**AC.4C1S2.9:** README updated; commit message reads `4C-1-S2 Item 9: README updates for S2 close`.

### Item 10 — Flip PANCHANG_DAILY_v1_0 status in CAPABILITY_MANIFEST.json

**What:** Open `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`. Find the `PANCHANG_DAILY_v1_0` entry added in 4C-0. Change `status: "PLANNED"` → `status: "IN_DEVELOPMENT"`. The asset's `path` still points to `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md`; no other field changes.

Add a one-line entry to the manifest's changelog (if it has one): `2026-05-19 PANCHANG_DAILY_v1_0: PLANNED → IN_DEVELOPMENT (4C-1-S2 — engine computes; cache + backfill pending 4C.2 + Phase 4B prerequisite)`.

**AC.4C1S2.10:** Status flipped; `drift_detector.py` exits 0; commit message reads `4C-1-S2 Item 10: PANCHANG_DAILY status PLANNED → IN_DEVELOPMENT`.

### Item 11 — Mirror discipline MP.2 propagation

**What:** Because Item 10 touched `CAPABILITY_MANIFEST.json`, the Gemini-side surface must adapt-parity update per MP.2.

1. Open `.gemini/project_state.md`. Find the existing `PANCHANG_DAILY_v1_0` entry (added in 4C-0's mirror step).
2. Update the status field to mirror the manifest's new value.
3. Run `python platform/scripts/governance/mirror_enforcer.py` (or whatever the project's mirror enforcement command is). Expected: exit 0.

If `mirror_enforcer.py` exits non-zero, halt with `HALT_NEEDS_HUMAN` — there's a mirror desync that needs Cowork-level review (per GOVERNANCE_INTEGRITY_PROTOCOL §K.3).

**AC.4C1S2.11:** `.gemini/project_state.md` PANCHANG_DAILY entry shows `IN_DEVELOPMENT`; `mirror_enforcer.py` exits 0; commit message reads `4C-1-S2 Item 11: MP.2 mirror propagation`.

### Item 12 — Phase 4C.1 close protocol

**What:** With the 30/30 Drik gate passing and all engine functionality landed, 4C-1 closes here. Execute the close protocol:

1. Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` Phase 4C block:
   - `last_session_id: 4C-1-S2`
   - Add to Phase 4C sub-phase tracker: `4C.1 CLOSED 2026-05-19`
   - `next_session_objective: 4C-2 (GATED on Phase 4B closing)`
2. Append `00_ARCHITECTURE/SESSION_LOG.md` with the 4C-1-S2 atomic block (open + body + close)
3. Update `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md` §B state tracker: 4C.1 row to CLOSED (cite commit hash)
4. Author a short close artifact: `00_ARCHITECTURE/PHASE_4C_1_CLOSE_v1_0.md` — one-page summary of what 4C.1 delivered (the engine, the 30-day Drik gate, version 1.0.0-S2)
5. Update the Conductor queue `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml`:
   - 4C-1-S2 entry: `status: passed`
   - 4C-1-S3 entry: `status: skipped`, `skip_reason: "4C-1-S2 closed 4C.1 cleanly with 30/30 gate; S3 polish not required"`
   - 4C-2 entry: re-verify `requires_external_gate: phase_4b_closed` is still set

**AC.4C1S2.12:** All 5 close protocol steps complete; CURRENT_STATE + SESSION_LOG + Phase 4 master plan §B all reflect 4C.1 CLOSED; queue manifest updated; commit message reads `4C-1-S2 Item 12: Phase 4C.1 close protocol — 4C.1 CLOSED`.

### Item 13 — Session-close + handoff

**What:**
1. Flip the frontmatter of THIS brief from `status: READY` → `status: COMPLETE`
2. Emit FINAL_SUMMARY per Conductor sub-agent prompt template
3. Final commit message: `4C-1-S2: session close — 4C.1 CLOSED at 30/30 Drik parity; next Conductor halt at 4C-2 (gated on 4B)`

**AC.4C1S2.13:** Brief flipped; FINAL_SUMMARY emitted; final commit landed.

---

## §4 — Mirror discipline

**MP.2 active this session** (Item 11) — `CAPABILITY_MANIFEST.json` status flip triggers `.gemini/project_state.md` parity update. No other mirrors triggered.

---

## §5 — Constraints

**may_touch (in `/Users/Dev/Vibe-Coding/Apps/Panchang`):**

- `platform/python-sidecar/panchang_engine/**` (all engine work)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (Item 10 status flip only)
- `.gemini/project_state.md` (Item 11 MP.2 propagation only)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (Item 12 Phase 4C block update)
- `00_ARCHITECTURE/SESSION_LOG.md` (Item 12 append)
- `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md` §B (Item 12 state tracker only)
- `00_ARCHITECTURE/PHASE_4C_1_CLOSE_v1_0.md` (Item 12 new file)
- `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml` (Item 12 queue update — 4C-1-S2 passed, 4C-1-S3 skipped)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_1_S2_v1_0.md` (status flip at session close only)

**must_not_touch:**

- `platform/src/`, `platform/lib/`, `platform/migrations/` (no app code; no schema; that's 4C-2+)
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `035_DISCOVERY_LAYER/**` (corpus frozen)
- `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` (sealed; no in-session edits)
- `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` (sealed; no edits)
- `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md` (orchestrator config — frozen)
- `00_ARCHITECTURE/CONDUCTOR/schemas/**` (frozen)
- Any prior session's closed artifacts (e.g., 4C-1-S1's brief, CONDUCTOR-S0's artifacts)
- `CLAUDE.md` (no §E edits this session)
- `.geminirules` (MP.1 not triggered)
- Anything in another worktree

---

## §6 — Session-close checklist

- [ ] Pre-flight integrity check PASSED (Item 1)
- [ ] All 13 ACs completed (AC.4C1S2.1 through AC.4C1S2.13)
- [ ] `pytest platform/python-sidecar/panchang_engine/tests/ -v` reports 100% PASS
- [ ] `test_drik_parity.py` reports 30/30 PASS (the close-gate)
- [ ] `test_special_yogas.py` reports 100% PASS
- [ ] `mirror_enforcer.py` exits 0 (Item 11)
- [ ] `drift_detector.py` exits 0 (Item 10)
- [ ] `validate_queue.py` exits 0 on `session_queue.yaml` (after Item 12 queue update)
- [ ] 13 scope commits + final close commit on `feature/phase-4c-panchang`
- [ ] CURRENT_STATE Phase 4C block shows `4C.1 CLOSED`
- [ ] SESSION_LOG has 4C-1-S2 atomic entry
- [ ] PHASE_4C_1_CLOSE_v1_0.md exists
- [ ] FINAL_SUMMARY emitted in machine-readable form
- [ ] Queue updated: 4C-1-S2 passed, 4C-1-S3 skipped, 4C-2 next-eligible (will halt on phase_4b_closed external gate)

---

## §7 — LLM stack for this session

| Role | Model | Notes |
|---|---|---|
| Primary inference | Gemini (gemini-2.5-pro for code/YAML, flash for text) | Default |
| Fallback | DeepSeek v4 Pro | |
| Tertiary | NIM | |
| Anthropic/Claude API | **BANNED** | Per memory file 2026-05-19 |

---

## §8 — Context carried (do not re-derive)

- **Ayanamsha = Lahiri.** Set in S1's `ayanamsha.py`; do not change.
- **Rahu = MEAN_NODE.** S1's assertion is in place; honor it.
- **Sunrise definition = visible upper limb + refraction.** S1's convention; do not change.
- **6-event Muhurat MVP:** Vivah, Griha Pravesh, Vyapara, Yatra, Property Purchase, Mantra Initiation. Settled D2 2026-05-19. Lock into `muhurat.py EVENTS_MVP`.
- **Drik 30-day fixture target:** 10 from v1 + 20 new in v2; all from Bhubaneswar + at least one Delhi day for sunrise sensitivity. Captured from drikpanchang.com — if unreachable, halt for native pre-capture.
- **Bhadra exclusions for Amrit Siddhi:** classical sources have minor disagreements. If a v2 fixture day fails because our Amrit Siddhi triggers where Drik suppresses it, treat Drik as authoritative and document the suppression rule. Don't fail the gate over this without halting first.
- **S3 is in the queue but optional.** If S2 closes 4C.1 cleanly (30/30 PASS + all gates), Item 12 marks S3 skipped. If S2 hits any issue and 4C.1 doesn't close cleanly, Item 12 leaves S3 pending and Cowork authors S3 in a follow-up.
- **4C-2 is gated on Phase 4B.** Don't worry about it — the Conductor's external_gates check handles it; orchestrator will halt at 4C-2 with `phase_4b_closed` blocker if 4B hasn't closed.
- **PANCHANG_DAILY status path:** PLANNED → IN_DEVELOPMENT (this session) → CURRENT (4C.2 when the Cloud SQL backfill completes).

---

## §9 — On the canary: 30/30 Drik parity gate

This is THE acceptance gate for 4C.1 close. S1 proved 10/10; S2 must prove 30/30 — including 20 new days AND the new special-yogas dimension.

If 30/30 doesn't pass:
- One or two day failures with diagnosable root cause (e.g., specific yoga detection bug) → fix in-session, re-run
- Systemic failures (e.g., >5 days failing on similar pattern) → halt; the special_yogas table or detection logic needs Cowork-level review
- Drik unreachable / fixture v2 incomplete → halt for native pre-capture; do not fabricate

If the gate passes cleanly: 4C.1 closes here, the queue advances, and the Conductor halts next at 4C-2 with a `phase_4b_closed` external-gate blocker (which is expected — Phase 4B is its own pending workstream).

---

## §10 — On what happens AFTER this session

When 4C-1-S2 closes:

1. **Conductor advances the queue.** 4C-1-S2 marked passed. 4C-1-S3 marked skipped (per Item 12). Next eligible entry is 4C-2.
2. **4C-2 halts on external gate.** Phase 4B hasn't closed; the orchestrator emits a `HALT — external gate not satisfied: phase_4b_closed` banner. This is expected behavior, not a failure.
3. **Native decides:** either (a) prioritize Phase 4B as a parallel workstream so 4C-2 unblocks, or (b) skip 4C-2 and jump to 4C-3 (`query_panchanga` RetrievalTool — doesn't depend on the SQL cache, can work directly against the engine for now).
4. **Either path requires Cowork.** Phase 4B brief authoring is its own conversation; 4C-3 brief authoring is its own conversation. Conductor stays halted until one of those briefs is authored, staged, and the queue updated.

---

*End of CLAUDECODE_BRIEF_PHASE_4C_1_S2_v1_0.md — authored 2026-05-19 in Cowork session after Conductor halt at 4C-1-S2.*
*Executor: Conductor sub-agent. Branch: feature/phase-4c-panchang. Worktree: /Users/Dev/Vibe-Coding/Apps/Panchang. Session: 4C-1-S2.*
*Closing session for Phase 4C.1 if 30/30 Drik parity gate passes; otherwise S3 covers polish.*
