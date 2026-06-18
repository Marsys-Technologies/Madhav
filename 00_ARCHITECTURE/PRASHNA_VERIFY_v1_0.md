---
id: PRASHNA_VERIFY
version: 2.0
status: PASS — MERGEABLE
authored: 2026-06-18
branch: feature/prashna-embed-across-layers
verifier: Claude Code live verification session
---

# Prashna Activation — Live Verification Report v2

## VERDICT: PASS ✅

`ga_prashna_judgment` produced **5 rows** (one per ayanamsha) for the re-cast Prashna chart.
All three F1/F2/F3 gaps from v1 are resolved. The implementation is mergeable.

---

## Changes Since v1

| Fix | File | Change |
|---|---|---|
| F1 | `ga_writers/ga_prashna_writer.py` | Added `_ABBREV_TO_FULL` map; normalized `positions` dict keys at construction + `float()` cast for psycopg3 `Decimal` |
| F2 | `ga_writers/ga_prashna_cast.py` | Removed spurious `charts` INSERT (would fail on NOT NULL `name`/`birth_date`) |
| F3 | `ga_writers/ga_prashna_cast.py` + tests | Added `"what's"`, `"whats"`, `"what're"`, `" sign?"` to `_REJECTION_PATTERNS`; 4 new test cases |

---

## 1. F1 — Graha Name Normalization ✅

Added at module level in `ga_prashna_writer.py`:

```python
_ABBREV_TO_FULL: dict[str, str] = {
    "SUN":      "Sun",
    "MOON":     "Moon",
    "MAR":      "Mars",
    "MER":      "Mercury",
    "JUP":      "Jupiter",
    "VEN":      "Venus",
    "SAT":      "Saturn",
    "RAH_MEAN": "Rahu",
    "KET_MEAN": "Ketu",
    "LAGNA":    "Lagna",
    "ASC":      "Lagna",
    "ASCENDANT": "Lagna",
}
```

Applied at source in the `positions` comprehension:

```python
positions = {
    _ABBREV_TO_FULL.get(r[0], r[0]): {"longitude": float(r[1]), "retrograde": (r[2] == "retrograde")}
    for r in cur.fetchall()
    if r[1] is not None
}
```

`float()` cast added to handle psycopg3's `decimal.Decimal` return for `NUMERIC` columns.
All downstream consumers (`PLANET_DAILY_MOTION`, `PLANET_ORBS`, significator lookup) now see
full names consistently.

---

## 2. F2 — charts INSERT Removed ✅

Removed from `cast_prashna_chart()`:

```python
# REMOVED — charts has NOT NULL (name, birth_date); prashna_charts has no FK to charts
with conn.cursor() as cur:
    cur.execute("INSERT INTO charts (id, created_at) VALUES (%s, NOW()) ON CONFLICT ...", ...)
```

No FK or read path requires a `charts` row for a Prashna chart_id. Cast completes without it.

---

## 3. F3 — Validation Gate ✅

Added to `_REJECTION_PATTERNS`:

```python
"what's",
"whats",
"what're",
" sign?",
```

Gate REJECT/ACCEPT behavior confirmed:

| Question | Expected | Result |
|---|---|---|
| "What's my Moon sign?" | REJECT | ✓ REJECT |
| "whats my lagna?" | REJECT | ✓ REJECT |
| "What're the aspects on my chart?" | REJECT | ✓ REJECT |
| "Will I get this job?" | ACCEPT | ✓ ACCEPT |
| "Will the project succeed this year?" | ACCEPT | ✓ ACCEPT |

---

## 4. End-to-End Cast — PASS ✅

**Cast details:**

| Field | Value |
|---|---|
| prashna_chart_id | `b35046d8-4131-4e0e-8548-3136678fc2bb` |
| question_text | "Will I get the promotion I applied for this quarter?" |
| question_class | career |
| prashna_lagna_method | tajik_moment_lagna |
| question_instant | 2026-06-18T22:00:00+05:30 (16:30:00 UTC) |
| question_lat / lon | 20.2961 / 85.8189 (Bhubaneswar) |
| querent_natal_chart_id | 482012f1-710e-4a25-994a-93821f5871aa |

**`cast_prashna_chart()` returned `rows_inserted = 10`** (5 lagna + 5 judgment rows).

**`ga_prashna_judgment` rows: 5 ✓ NON-ZERO**

| ayanamsha_id | tajik_yoga | judgment | querent | quesited | gap |
|---|---|---|---|---|---|
| krishnamurti | no_direct_aspect | UNCERTAIN | Moon | Saturn | 56.42° |
| lahiri_chitrapaksha | no_direct_aspect | UNCERTAIN | Moon | Saturn | 56.42° |
| raman | no_direct_aspect | UNCERTAIN | Moon | Saturn | 56.42° |
| surya_siddhanta_classical | no_direct_aspect | UNCERTAIN | Moon | Saturn | 56.42° |
| true_chitra | no_direct_aspect | UNCERTAIN | Moon | Saturn | 56.42° |

Judgment is `UNCERTAIN` (Moon and Saturn out of mutual orb at 56.42° gap, mutual orb ~10.6°).
This is a valid, non-None judgment — the significators resolved correctly.

---

## 5. Lagna — PASS ✅

Primary (lahiri_chitrapaksha):

| Field | Value |
|---|---|
| lagna_rashi | Capricorn |
| lagna_degree_in_sign | 28.3875° |
| Not 0°Aries fallback | ✓ PASS |

`LAGNA` → `Lagna` normalization + `float()` cast resolved the `decimal.Decimal % float` error.

---

## 6. Namespace Isolation — PASS ✅

| Check | Result |
|---|---|
| Native 482012f1 `ga_prashna_judgment` rows | 0 ✓ |
| Native 482012f1 in `prashna_charts` | 0 ✓ |

---

## 7. Tests — 26/26 PASS ✅

- 22 original tests (18 `test_ga_prashna` + 4 `test_ga_prashna_cast`): **22/22**
- 4 new F3 gate tests: **4/4**
- Total: **26/26 PASS**

FROZEN orchestrator contract: untouched.
`ga_prashna` in asset_registry: confirmed.
