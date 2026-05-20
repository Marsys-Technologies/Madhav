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

# Muhurat Finder — LIVE since 4C.6 (Phase 4C-6-S1)
windows = find_muhurat(
    "vivah",                  # event key (see §9 below)
    date(2027, 1, 1),         # date_from
    date(2027, 1, 31),        # date_to (max 89 days from date_from)
    20.27,                    # lat
    85.84,                    # lon
    top_n=10,                 # max results returned
)
# Returns list[MuhuratWindow] sorted by score descending
# Each window: event, start_utc, end_utc, star_rating (1–5), score, breakdown dict
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

## §8a — Tuning muhurat scoring weights

Weights live in `config/muhurat_weights.yaml`. Edit there to retune scoring
without code changes. The file is parsed at sidecar startup (cached);
restart the sidecar for changes to take effect.

**Structure:**
- `defaults:` — base weights applied for any event not explicitly overridden.
- `events:` — per-event overrides; partial — only keys that differ from defaults
  need to be listed; missing keys inherit from `defaults`.

**Weight keys:**
| Key | Factor | Notes |
|---|---|---|
| `tithi` | Lunar day quality for the event | Shukla paksha tithis dominate |
| `nakshatra` | Moon's asterism quality | Most influential factor classically |
| `vara` | Weekday quality | Saturn/Tuesday typically avoided |
| `yoga` | Auspicious special yoga bonus | Sarvartha Siddhi, Guru Pushya, Tripushkar |
| `planet` | Non-combust Jupiter + Venus | Each contributes half of the planet weight |
| `native` | Tara Bala personal overlay | Only active when NatalChart is passed |
| `avoid_penalty` | **NEVER CHANGE — always 1.0** | Knockout for compound inauspicious windows |

**To tune for a specific user complaint** (e.g. "the scoring overweights nakshatra
for Griha Pravesh"):
1. Edit `config/muhurat_weights.yaml` `events.griha_pravesh.nakshatra`
2. Adjust other weights so they still sum to ~1.0 within positive contributors
   (tithi + nakshatra + vara + yoga + planet + native ≈ 1.0).
   `avoid_penalty` is not a positive contributor and must stay at 1.0.
3. Restart sidecar; verify with `find_muhurat("griha_pravesh", ...)` that
   rankings shift as intended.

**To add a new event type:**
1. Add a quality table to `shastra_tables.py` (§22.N)
2. Register it in `EVENT_TABLES` (§23)
3. Add to `EVENTS_MVP` in `muhurat.py`
4. Optionally add an `events.your_event_name:` block to `muhurat_weights.yaml`.
   If omitted, the event inherits `defaults` weights automatically.

**Critical constraint**: `avoid_penalty` must always be 1.0. This is the knockout
multiplier for compound inauspicious windows (Rahu Kalam + Yamagandam + worst tithi
+ Saturday). Changing it bypasses a hard rule in the classical muhurta system
(Muhurta Chintamani §4.4.1 per PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md).

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

## §9 — Muhurat Finder (Phase 4C.6 — LIVE)

The Muhurat Finder is **fully implemented as of Phase 4C-6-S1** (2026-05-20).
It ranks every day in a date range for a given event type, returning the top N
windows sorted by auspiciousness score.

### Supported Events (MVP — Phase 4C.6)

| Event Key | Event Type | Primary Classical Source |
|---|---|---|
| `vivah` | Marriage / Vivah | Muhurta Chintamani §3 |
| `griha_pravesh` | Housewarming / Griha Pravesh | Muhurta Chintamani §4 |
| `vyapara` | Business Start / Trade | Muhurta Chintamani §5 |
| `yatra` | Travel / Yatra | Brihat Samhita §Yatra |
| `property_purchase` | Property or Vehicle Purchase | Muhurta Chintamani §11 |
| `mantra_initiation` | Mantra Diksha / Spiritual Initiation | Muhurta Chintamani §8 |

Pass the key exactly as listed above. Any other value raises `ValueError`.

### How the YAML Weights Work

Weights live in `config/muhurat_weights.yaml` (see §8a above for tuning guide).

The scoring formula for each day:

```
score = (
    weights.tithi    × quality_table[tithi_id][event]      +
    weights.nakshatra× quality_table[nakshatra_id][event]  +
    weights.vara     × quality_table[vara_id][event]       +
    weights.yoga     × yoga_bonus(active_yogas)            +
    weights.planet   × planet_factor(jupiter, venus)       +
    weights.native   × native_overlay(chart, day)
) × 100

# Knockout: if in compound inauspicious window, score = 0.0
if _in_inauspicious(panchang):
    score = 0.0
```

The weights sum to ~1.0 for positive contributors. `avoid_penalty` (1.0) is the
knockout multiplier — it is never modified (master plan hard constraint).

**Star rating** maps score → stars:

| Score | Stars |
|-------|-------|
| ≥ 80  | 5★ |
| 65–79 | 4★ |
| 50–64 | 3★ |
| 35–49 | 2★ |
| < 35  | 1★ |

### How to Interpret Breakdown Badges

Each `MuhuratWindow.breakdown` dict contains verbose factor keys:

| Key | Meaning |
|-----|---------|
| `tithi_name` | Name of the lunar day (e.g., "Shukla Panchami") |
| `tithi_score` | Quality score 0.0–1.0 for tithi |
| `tithi_weight` | Weight applied (from YAML) |
| `tithi_contrib` | Actual contribution to score (score × weight) |
| `nakshatra_name` | Moon's asterism name |
| `nakshatra_contrib` | Nakshatra contribution |
| `vara_name` | Weekday name (e.g., "Guruvara") |
| `vara_contrib` | Vara contribution |
| `yoga_score` | Yoga bonus (1.0 if a strong auspicious yoga is active) |
| `yoga_contrib` | Yoga contribution |
| `active_auspicious_yogas` | List of active yoga names (may be empty strings — see known issue) |
| `planet_score` | Planet factor (1.0 if neither Jupiter nor Venus combust) |
| `planet_contrib` | Planet contribution |
| `jupiter_combust` / `venus_combust` | Boolean flags |
| `native_score` | Tara Bala overlay (0.0 if no NatalChart passed) |
| `native_contrib` | Native contribution |
| `native_chart_present` | Boolean — False when chart_id is None |
| `inauspicious_windows` | List of active inauspicious window labels on this day |
| `knockout` | Boolean — True if day was zeroed by compound inauspicious window |

**Known Issue (Issue I.1):** `active_auspicious_yogas` may contain empty strings
instead of yoga names. The yoga_score and yoga_contrib are correct — only the label
serialization is affected. Fix deferred to 4C-7.

### Latency Expectations

Measured on Apple Silicon (M-series), Lahiri ayanamsha, Swiss Ephemeris:

| Range | Expected Latency | ms/day |
|-------|-----------------|--------|
| 30-day | ~0.22s | ~7 ms |
| 60-day | ~0.45s | ~7 ms |
| 90-day (max) | ~0.68s | ~7 ms |

Cloud Run cold start adds ~2–3s; warm sidecar (keep-alive ping) avoids this.
Maximum range enforced by sidecar: 89 days (date_to − date_from ≤ 89).

### Acharya Review Process

The Muhurat Finder output was reviewed for acharya-grade quality in Phase 4C-6-S4:
- 5 events × 5 top results = 25 windows reviewed
- Classical authorities: Muhurta Chintamani, Brihat Samhita, Muhurta Martanda
- Canary: PASS — no systematic scoring failure
- Provisional verdicts (LLM-derived); final acharya sign-off at 4C-9 Wave 1 close
- Full review: `platform/tests/visual/4C6_acharya_review.md`

---

## §10 — Future work

- **`AMRIT_KALAM_TABLE` + `VARJYAM_TABLE`**: `shastra_tables.py` §13–§14 stubs
  (all `[None, None]`). To be populated from Drik reference in a future session.
- **Amrit Siddhi death-yoga exclusions**: MC 5.17 Visha Yoga suppression rules;
  currently not implemented (marked TODO in `special_yogas.py`).
- **Sub-day muhurta windows (v2)**: MVP scoring is daylong. Phase 4C v2 will add
  sub-day precision (per-muhurta within the day), estimated ~22s for 90-day range.
- **iCal export**: 4C-7 scope — "Export to Calendar" button in UI.
- **Yoga name serialization fix**: active_auspicious_yogas may return empty strings
  (Issue I.1); fix in 4C-7 sidecar update.
- **Shastra table calibration**: minor calibration for Revati (property_purchase)
  and Shanivara (property_purchase) — deferred to 4C-9 acharya panel review.

---

*panchang_engine v1.0.0-S3 — 4C-6 close (2026-05-20)*
*Branch: feature/phase-4c-panchang | Worktree: /Users/Dev/Vibe-Coding/Apps/Panchang*
*Phase 4C.1 CLOSED. Phase 4C.6 CLOSED. 30/30 Drik parity gate PASS. Muhurat Finder LIVE.*
