---
artifact: PANCHANG_DAILY_v1_0.md
canonical_id: PANCHANG_DAILY
version: 1.0
status: PLANNED
layer: L1.5
lineage:
  - EPHEMERIS_DAILY
  - classical_muhurta_shastra
authored_by: Claude Code (Sonnet 4.6, session 4C-0)
authored_on: 2026-05-19
lifecycle_note: >
  PLANNED (now) → IN_DEVELOPMENT (4C.1 panchang_engine opens) →
  CURRENT (4C.2 backfill completes — Bhubaneswar + Delhi 1900–2100)
changelog:
  - v1.0 (2026-05-19, session 4C-0): Schema document authored. SQL DDL
    mirrors PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.2 verbatim.
    Status PLANNED — panchang_engine Python module is 4C.1 scope.
---

# PANCHANG_DAILY — Schema Document v1.0

**Canonical ID:** `PANCHANG_DAILY`
**Layer:** L1.5 (derived from L1 ephemeris — computed, deterministic, facts only)
**Computation source:** `platform/sidecar/panchang_engine/` (Phase 4C.1 scope)
**Cloud SQL table:** `panchang_daily`
**Status:** PLANNED — see §7 for lifecycle

---

## §1 — Purpose

`PANCHANG_DAILY` is the canonical daily Panchang state asset for the MARSYS-JIS instrument. It holds the computed astronomical and calendrical state for any `(date, lat, lon)` tuple, derived deterministically from Swiss Ephemeris planetary positions (`EPHEMERIS_DAILY`) plus static classical Muhurta Shastra lookup tables.

**What it is:**
- A fully deterministic L1.5 derivation — given the same inputs and ephemeris version, the output is always identical.
- A cache layer: once computed for a `(date, lat, lon)`, rows persist permanently (they are mathematically fixed; recomputation only on `computation_version` or `ephemeris_version` change).
- The backing store for the `/panchang` UI page and the `query_panchanga` RetrievalTool.

**What it is not:**
- An interpretation layer. No muhurat quality scores, no auspiciousness verdicts, no LLM text live in this table. Pure computed facts.
- A replacement for `FORENSIC`. Panchang is continuous daily state; FORENSIC is a natal snapshot. Different temporal cardinality, different mutation surface.

**Lineage:**

```
L2.5  ── MSR / UCN / CDLM (synthesis — reads PANCHANG_DAILY via query_panchanga)
           ▲
L1.5  ── PANCHANG_DAILY (this asset)
           ▲                   ▲
L1    ── EPHEMERIS_DAILY     classical_muhurta_shastra lookup tables
           ▲
           └── pyswisseph (Swiss Ephemeris Python binding)
```

---

## §2 — Schema (SQL DDL)

*Verbatim from `PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.2`. Any discrepancy between this file and the master plan resolves in favor of the master plan until 4C.2 migration is applied, after which the live DB schema is authoritative.*

```sql
CREATE TABLE panchang_daily (
  -- composite primary key
  date              DATE        NOT NULL,
  lat               NUMERIC(8,4) NOT NULL,
  lon               NUMERIC(8,4) NOT NULL,
  tz_offset_minutes INTEGER     NOT NULL,
  -- derived from sunrise at (lat, lon, date)
  sunrise_utc       TIMESTAMPTZ NOT NULL,
  sunset_utc        TIMESTAMPTZ NOT NULL,
  moonrise_utc      TIMESTAMPTZ,
  moonset_utc       TIMESTAMPTZ,
  -- 5 angas (sunrise-anchored)
  tithi_id          SMALLINT NOT NULL,  -- 1..30
  tithi_end_utc     TIMESTAMPTZ NOT NULL,
  nakshatra_id      SMALLINT NOT NULL,  -- 1..27
  nakshatra_end_utc TIMESTAMPTZ NOT NULL,
  yoga_id           SMALLINT NOT NULL,  -- 1..27
  yoga_end_utc      TIMESTAMPTZ NOT NULL,
  karana_first_id   SMALLINT NOT NULL,  -- 1..11
  karana_second_id  SMALLINT NOT NULL,
  karana_end_utc    TIMESTAMPTZ NOT NULL,
  vara_id           SMALLINT NOT NULL,  -- 1..7
  paksha            VARCHAR(8) NOT NULL,  -- 'shukla'|'krishna'
  -- timings (computed JSON for flexibility)
  inauspicious      JSONB NOT NULL,  -- {rahu_kalam, yamagandam, gulika_kalam, dur_muhurta[]}
  auspicious        JSONB NOT NULL,  -- {abhijit, brahma_muhurta, amrit_kalam, varjyam}
  choghadiya        JSONB NOT NULL,  -- {day: [...], night: [...]}
  hora              JSONB NOT NULL,  -- 24 planetary hours
  -- special yogas (active periods)
  special_yogas     JSONB NOT NULL,  -- [{yoga: "sarvartha_siddhi", start, end, strength}]
  -- planetary positions at sunrise
  planets           JSONB NOT NULL,  -- {sun: {lon, sign, nakshatra, pada, retrograde, combust}, ...}
  -- audit
  computed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  computation_version VARCHAR(16) NOT NULL,  -- panchang_engine.__version__
  ephemeris_version VARCHAR(16) NOT NULL,    -- swisseph version + .se1 hash
  PRIMARY KEY (date, lat, lon)
);
CREATE INDEX idx_panchang_date ON panchang_daily(date);
CREATE INDEX idx_panchang_special_yogas ON panchang_daily USING GIN(special_yogas);
```

**Migration file:** `platform/migrations/060_create_panchang_daily.sql` (Phase 4C.2 scope — do not create before 4C.2 opens).

---

## §3 — Cache Strategy

*Verbatim from `PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.2`.*

- **Bhubaneswar** (lat 20.2961, lon 85.8189) and **Delhi** (lat 28.6139, lon 77.2090): precomputed for 1900–2100 (~146,000 rows × 2 = ~292K rows). Batch backfill job in Phase 4C.2 (~6 hours on Cloud Run).
- **Other coordinates:** computed on demand, written to `panchang_daily` on first request. Subsequent requests for the same `(date, lat, lon)` hit the cache.
- **TTL:** None. Rows are mathematically deterministic — they never change unless `computation_version` or `ephemeris_version` changes. Recomputation is triggered by a schema migration that clears stale rows (not by TTL expiry).
- **Consistency guarantee:** A `(date, lat, lon)` row is either absent (not yet computed) or correct (byte-identical to a fresh computation of the same version). No partial-write states.

---

## §4 — Computation Source

**Module:** `platform/sidecar/panchang_engine/` (Phase 4C.1 scope).

Public API (Python):

```python
def compute_panchang(date: date, lat: float, lon: float, tz_offset: int) -> Panchang:
    """Full Panchang for a single day. Reads EPHEMERIS_DAILY; writes panchang_daily."""

def find_muhurat(event: str, date_from: date, date_to: date, lat: float, lon: float,
                 native_chart: Optional[NatalChart] = None) -> list[MuhuratWindow]:
    """Top auspicious windows for an event in a date range."""

def panchang_range(date_from: date, date_to: date, lat: float, lon: float,
                   tz_offset: int) -> list[Panchang]:
    """Batch compute (for calendar feed and backfill)."""
```

**Sidecar route:** `POST /api/compute/panchanga` — extends existing `platform/src/app/api/compute/[type]/route.ts` (Phase 4C.2).

**Ayanamsha:** Lahiri (default, configurable). All longitude computations use Lahiri ayanamsha unless overridden.

---

## §5 — Field-by-Field Semantics

| Column | Type | Semantics |
|---|---|---|
| `date` | DATE | Calendar date in local timezone (derived from `sunrise_utc + tz_offset_minutes`) |
| `lat` | NUMERIC(8,4) | Geographic latitude, decimal degrees, north positive |
| `lon` | NUMERIC(8,4) | Geographic longitude, decimal degrees, east positive |
| `tz_offset_minutes` | INTEGER | UTC offset in minutes at the given date (accounts for DST if applicable) |
| `sunrise_utc` | TIMESTAMPTZ | Local sunrise expressed as UTC timestamp (Swiss Ephemeris; disc centre, standard refraction) |
| `sunset_utc` | TIMESTAMPTZ | Local sunset expressed as UTC timestamp |
| `moonrise_utc` | TIMESTAMPTZ | Moonrise (nullable — no moonrise on some days in extreme latitudes) |
| `moonset_utc` | TIMESTAMPTZ | Moonset (nullable) |
| `tithi_id` | SMALLINT | 1=Pratipada…15=Purnima/Amavasya (Shukla 1–15, Krishna 1–15; 30 total) — determined at sunrise |
| `tithi_end_utc` | TIMESTAMPTZ | When the current Tithi ends (next Tithi begins) |
| `nakshatra_id` | SMALLINT | 1=Ashwini…27=Revati — Moon's Nakshatra at sunrise |
| `nakshatra_end_utc` | TIMESTAMPTZ | When the current Nakshatra ends |
| `yoga_id` | SMALLINT | 1=Vishkambha…27=Vaidhriti — Yoga = (Sun longitude + Moon longitude) / 13°20'; determined at sunrise |
| `yoga_end_utc` | TIMESTAMPTZ | When the current Yoga ends |
| `karana_first_id` | SMALLINT | 1=Bava…11=Naga — first Karana of the day (half-Tithi; 1 Tithi = 2 Karanas) |
| `karana_second_id` | SMALLINT | Second Karana of the day |
| `karana_end_utc` | TIMESTAMPTZ | End of first Karana (= start of second) |
| `vara_id` | SMALLINT | 1=Ravivara (Sun/Sunday)…7=Shanivara (Saturn/Saturday) — weekday per local date |
| `paksha` | VARCHAR(8) | `'shukla'` (waxing, Tithi 1–15) or `'krishna'` (waning, Tithi 16–30) |
| `inauspicious` | JSONB | `{rahu_kalam: {start, end}, yamagandam: {start, end}, gulika_kalam: {start, end}, dur_muhurta: [{start, end}]}` — all in UTC |
| `auspicious` | JSONB | `{abhijit: {start, end}, brahma_muhurta: {start, end}, amrit_kalam: {start, end}, varjyam: {start, end}}` — all in UTC |
| `choghadiya` | JSONB | `{day: [{name, lord, quality, start, end}×8], night: [{...}×8]}` — 24 Choghadiya periods |
| `hora` | JSONB | `[{hour_num, lord, start, end}×24]` — planetary hours, 1=1st hour after sunrise |
| `special_yogas` | JSONB | `[{yoga: string, start: UTC, end: UTC, strength: "high"|"medium"|"low"}]` — includes Sarvartha Siddhi, Amrit Siddhi, Ravi Pushya, Guru Pushya, Bhadra, etc. |
| `planets` | JSONB | `{sun: {lon: deg, sign: 1..12, nakshatra: 1..27, pada: 1..4, retrograde: bool, combust: bool}, moon: {...}, mars: {...}, mercury: {...}, jupiter: {...}, venus: {...}, saturn: {...}, rahu: {...}, ketu: {...}}` — positions at sunrise, Lahiri ayanamsha |
| `computed_at` | TIMESTAMPTZ | When this row was written (for debugging/audit) |
| `computation_version` | VARCHAR(16) | `panchang_engine.__version__` at time of computation (e.g., `"1.0.0"`) |
| `ephemeris_version` | VARCHAR(16) | Swiss Ephemeris version + `.se1` file hash prefix (e.g., `"2.10.03_a1b2c3"`) |

---

## §6 — Validation Reference

Per `PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.3`, all values are validated before Phase 4C.1 declares CLOSED:

**30-day Drik Panchang cross-check:**

| Field | Required precision |
|---|---|
| Tithi ID (at sunrise) | Exact match |
| Nakshatra ID (at sunrise) | Exact match |
| Yoga ID (at sunrise) | Exact match |
| Tithi/Nakshatra/Yoga transition times | Within 2 minutes |
| Sunrise / Sunset | Within 30 seconds (swisseph is more precise than Drik's displayed value) |
| Special yoga presence/absence | Exact match (boolean) |

**Validation fixture:** `platform/sidecar/panchang_engine/tests/fixtures/drik_panchang_30_days.json` — 30 hand-curated reference days drawn from Drik Panchang's published output for Bhubaneswar.

**Gate (AC.4C.1):** All 30 days pass within tolerance. If any day fails, the failing field is root-caused (ayanamsha offset? sunrise algorithm?) before 4C.1 closes.

---

## §7 — Status Lifecycle

| Status | Trigger | Description |
|---|---|---|
| **PLANNED** ← *current* | 4C-0 governance setup (this session) | Schema document exists; no DB table, no engine code |
| IN_DEVELOPMENT | 4C.1 opens: `panchang_engine` Python module starts | Engine code being written; validation fixtures in progress |
| IN_DEVELOPMENT | 4C.2 opens: DB migration applied | `panchang_daily` table exists; backfill running |
| **CURRENT** | 4C.2 closes: backfill complete, 100-row sample validated | `panchang_daily` has ≥292K rows; `query_panchanga` RetrievalTool callable |

`CAPABILITY_MANIFEST.json` entry status must be updated at each lifecycle transition (schema-conformant update in the respective session).

---

*End of PANCHANG_DAILY_v1_0.md. Schema mirrors `PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.2` verbatim. Status: PLANNED — `panchang_engine` Python module is Phase 4C.1 scope.*
