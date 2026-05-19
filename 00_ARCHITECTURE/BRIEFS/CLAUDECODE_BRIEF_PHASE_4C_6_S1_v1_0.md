---
artifact: CLAUDECODE_BRIEF_PHASE_4C_6_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-19
session_id: 4C-6-S1
session_name: 4C-6-S1 — Muhurat backend: event tables + scoring rubric
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.4.1 + §5.3 (muhurat.py)
predecessor: 4C-5
---

# CLAUDECODE_BRIEF — Phase 4C-6-S1
## Muhurat Finder backend — event quality tables + scoring rubric implementation

First of four sessions for Muhurat Finder. S1 implements the backend math: per-event quality tables for tithi/nakshatra/vara, the scoring rubric, and replaces the muhurat.py scaffold with real `score_muhurat` and `find_muhurat` implementations. S2 adds YAML weights config; S3 adds UI; S4 closes.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f 00_ARCHITECTURE/PHASE_4C_4_CLOSE_v1_0.md
test -f platform/python-sidecar/panchang_engine/muhurat.py
grep -q "SCAFFOLD" platform/python-sidecar/panchang_engine/muhurat.py  # confirm S2's scaffold is there
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §4.4.1 (Muhurat Finder spec — full); §5.3 (muhurat.py + shastra_tables.py); §10 risks
3. `platform/python-sidecar/panchang_engine/muhurat.py` (scaffold to replace)
4. `platform/python-sidecar/panchang_engine/shastra_tables.py` (existing tables — extend, don't replace)
5. `platform/python-sidecar/panchang_engine/types.py` (MuhuratWindow + NatalChart dataclasses)
6. `platform/python-sidecar/panchang_engine/__init__.py` (compute_panchang signature — used to compute candidate days)

## §3 — Scope (10 items)

### Item 1 — Per-event quality tables in `shastra_tables.py`
Add 6 event-specific quality tables, each mapping (tithi_id, nakshatra_id, vara_id) preferences. For MVP events: Vivah, Griha Pravesh, Vyapara, Yatra, Property Purchase, Mantra Initiation. Each table has three sub-dicts:

```python
VIVAH_QUALITY = {
    "tithi": {
        # tithi_id → score 0..1
        2: 0.8, 3: 0.8, 5: 0.9, 7: 0.85, 10: 0.95, 11: 0.85, 12: 0.7, 13: 0.7,
        # Excluded: Chaturthi (4), Navami (9), Chaturdashi (14), Amavasya (30)
        # Source: Muhurta Chintamani 3.2 (marriage tithis)
    },
    "nakshatra": {
        # nakshatra_id → score
        1: 0.5, 4: 0.95, 7: 0.85, 8: 0.95, 10: 0.85, 12: 0.95, 13: 0.95, 21: 0.95, 27: 0.95,
        # Source: Muhurta Chintamani 3.5 (marriage nakshatras)
    },
    "vara": {
        # vara_id → score; 4 (Wed), 5 (Thu), 6 (Fri) preferred; 7 (Sat) avoided
        2: 0.8, 4: 0.9, 5: 0.95, 6: 0.9,
        # Source: classical preference table
    },
}
# Similar GRIHA_PRAVESH_QUALITY, VYAPARA_QUALITY, YATRA_QUALITY,
# PROPERTY_PURCHASE_QUALITY, MANTRA_INITIATION_QUALITY tables
```

Each table cites its classical source in an inline comment. Where multiple sources disagree, use Muhurta Chintamani as authoritative.

**AC.4C6S1.1:** 6 tables populated; each cites a classical source; covers all relevant tithi/nakshatra/vara IDs (no silent zeros for unhandled IDs — explicit 0.0 entries for known-avoided IDs).

### Item 2 — Default scoring weights
Add `DEFAULT_MUHURAT_WEIGHTS` in `shastra_tables.py`:

```python
DEFAULT_MUHURAT_WEIGHTS = {
    "tithi": 0.20,
    "nakshatra": 0.30,
    "vara": 0.10,
    "yoga": 0.15,    # bonus for active auspicious special yoga
    "planet": 0.10,  # bonus for non-combust Jupiter/Venus
    "native": 0.10,  # bonus for high Tara Bala / Chandra Bala (when personalised)
    "avoid_penalty": 1.0,  # FULL penalty when in Rahu/Yama/Gulika/DurMuhurta
}
# Per-event weight overrides land in YAML in 4C-6-S2; defaults here.
```

**AC.4C6S1.2:** Weights table present; sums to ~1.0 across positive contributors; avoid_penalty is 1.0 (knockout for windows in inauspicious times).

### Item 3 — Implement `score_muhurat`
Replace the scaffold in `muhurat.py`. Real implementation:

```python
def score_muhurat(
    panchang: Panchang,
    event: str,
    weights: dict = None,
    native_chart: Optional[NatalChart] = None,
) -> float:
    """Score a Panchang state for a given event. Returns 0..100."""
    weights = weights or DEFAULT_MUHURAT_WEIGHTS
    quality_table = EVENT_TABLES[event]  # dict mapping event → quality table

    # Knockout check
    if _in_inauspicious(panchang):
        return 0.0

    score = 0.0
    score += weights["tithi"]     * quality_table["tithi"].get(panchang.tithi.id, 0.0)
    score += weights["nakshatra"] * quality_table["nakshatra"].get(panchang.nakshatra.id, 0.0)
    score += weights["vara"]      * quality_table["vara"].get(panchang.vara.id, 0.0)

    # Special yoga bonus
    auspicious_yogas = [y for y in panchang.special_yogas if y["strength"] == "auspicious"]
    if auspicious_yogas:
        max_stars = max(y["stars"] for y in auspicious_yogas)
        score += weights["yoga"] * (max_stars / 5.0)

    # Planet bonus (Jupiter and Venus non-combust)
    jupiter = next(p for p in panchang.planets if p.name == "Jupiter")
    venus = next(p for p in panchang.planets if p.name == "Venus")
    if not jupiter.combust:
        score += weights["planet"] * 0.5
    if not venus.combust:
        score += weights["planet"] * 0.5

    # Native overlay
    if native_chart:
        from .tara_bala import compute_tara_bala_score  # add this helper
        score += weights["native"] * compute_tara_bala_score(
            native_chart.birth_nakshatra_id, panchang.nakshatra.id
        )

    return min(100.0, score * 100.0)
```

`_in_inauspicious` is the knockout helper: returns True if any of the Panchang's `inauspicious` windows is currently active relative to the time-of-day being scored. For a daylong score, returns False unless ALL day is inauspicious (rare).

**AC.4C6S1.3:** `score_muhurat` returns a float in 0..100 for any (panchang, event) input; knockout case returns 0.0.

### Item 4 — Implement `find_muhurat`
Real implementation:

```python
def find_muhurat(
    event: str,
    date_from: date,
    date_to: date,
    lat: float,
    lon: float,
    tz_offset_minutes: int,
    native_chart: Optional[NatalChart] = None,
    weights: dict = None,
    top_n: int = 10,
) -> list[MuhuratWindow]:
    """Top auspicious windows for `event` in [date_from, date_to].
    Iterates each day in range, computes Panchang, scores it,
    returns top_n by score with breakdown of why each scored well."""
    if not is_supported_event(event):
        raise ValueError(f"Event '{event}' not in MVP set. Supported: {EVENTS_MVP}")

    candidates = []
    current = date_from
    while current <= date_to:
        panchang = compute_panchang(current, lat, lon, tz_offset_minutes)
        score = score_muhurat(panchang, event, weights, native_chart)
        if score > 0:
            breakdown = _score_breakdown(panchang, event, weights, native_chart)
            window = MuhuratWindow(
                event=event,
                start_utc=panchang.sunrise_utc,
                end_utc=panchang.sunset_utc,  # daylong window for MVP; finer per-muhurta in v2
                star_rating=_score_to_stars(score),
                score=score,
                breakdown=breakdown,
            )
            candidates.append(window)
        current = current + timedelta(days=1)

    candidates.sort(key=lambda w: w.score, reverse=True)
    return candidates[:top_n]
```

`_score_breakdown` returns a dict of contributions per factor for explainability.
`_score_to_stars` maps 0..100 → 1..5 stars (thresholds: 80+ = 5★, 65-80 = 4★, 50-65 = 3★, 35-50 = 2★, 0-35 = 1★).

**AC.4C6S1.4:** `find_muhurat` returns top_n windows sorted by score; breakdown dict populated; star ratings correct.

### Item 5 — Bump engine version
Update `__init__.py`: `__version__ = "1.0.0-S3"` (S3 = muhurat backend live).

### Item 6 — Test suite for backend
`tests/test_muhurat_scoring.py`:
- Known auspicious Vivah day (e.g., a Thursday in Rohini nakshatra with Shukla Panchami) → score ≥ 70
- Known inauspicious day (e.g., Amavasya on Saturday with Bharani nakshatra during Rahu Kalam) → score ≤ 20
- Knockout case (entire day in compound inauspicious windows) → 0.0
- Range query for Vivah Apr-Jun 2026 returns 10 candidates sorted by score
- Each MuhuratWindow has populated breakdown

**AC.4C6S1.5:** ~15 test cases, all PASS.

### Item 7 — `tara_bala` Python helper
Add `panchang_engine/tara_bala.py` (Python-side version of the TS helper for the engine's native overlay). Mirrors the TS computation but called server-side in `score_muhurat`.

**AC.4C6S1.6:** Python tara_bala helper exists; tests confirm same outputs as TS version for 9 sample inputs.

### Item 8 — Sidecar endpoint extension
Add `/api/compute/muhurat` endpoint to sidecar:

```python
class MuhuratRequest(BaseModel):
    event: str
    date_from: date
    date_to: date
    lat: float
    lon: float
    tz_offset_minutes: int
    chart_id: Optional[str] = None
    top_n: int = 10

@app.post("/api/compute/muhurat")
async def compute_muhurat_endpoint(req: MuhuratRequest):
    native_chart = None
    if req.chart_id:
        chart = await fetch_chart(req.chart_id, current_user)
        native_chart = chart_to_natal(chart)
    windows = find_muhurat(req.event, req.date_from, req.date_to,
                           req.lat, req.lon, req.tz_offset_minutes,
                           native_chart=native_chart, top_n=req.top_n)
    return {"ok": True, "windows": [w.__dict__ for w in windows]}
```

**AC.4C6S1.7:** Endpoint live; curl smoke against `/api/compute/muhurat` with sample request returns 10 windows.

### Item 9 — Performance sanity
Range queries scan day-by-day (computing Panchang × N days). For a 90-day range, expect ~30 seconds on cold sidecar. Acceptable for MVP; v2 may add coarser pre-filter. Document baseline latency in `platform/tests/perf/4C6_S1_muhurat_latency.md`.

**AC.4C6S1.8:** Latency baseline documented.

### Item 10 — Close
CURRENT_STATE: `4C-6-S1 PASSED — muhurat backend live`. SESSION_LOG appended. Brief flipped. FINAL_SUMMARY.

**AC.4C6S1.9:** Close protocol complete.

---

## §5 — Constraints
**may_touch:** `platform/python-sidecar/panchang_engine/{muhurat,tara_bala,shastra_tables,__init__}.py`; `platform/python-sidecar/panchang_engine/tests/test_muhurat_scoring.py`; sidecar `main.py` (new endpoint); `platform/tests/perf/4C6_S1_muhurat_latency.md`; governance state files; this brief.
**must_not_touch:** UI components (4C-6-S3 territory); RetrievalTool (Phase 4C-3 sealed); engine modules other than muhurat/tara_bala/shastra_tables/__init__; corpus; master plan.

## §6 — Close checklist
- [ ] 10 ACs PASS; full test suite (engine + new muhurat tests) PASS
- [ ] Sidecar endpoint live and tested
- [ ] Latency baseline documented
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- 6 MVP events from D2 settled 2026-05-19
- DEFAULT_MUHURAT_WEIGHTS in code; YAML override is 4C-6-S2
- Native overlay via NatalChart, populated from chart_id when present
- Daylong windows for MVP; finer-grained per-muhurta in v2

## §9 — Canary
`/api/compute/muhurat` with `{"event": "vivah", "date_from": "2026-06-01", "date_to": "2026-06-30", "lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330}` returns plausibly-ranked windows. Top result should align with a senior acharya's intuition (verify a few manually).

*End — 4C-6-S1.*
