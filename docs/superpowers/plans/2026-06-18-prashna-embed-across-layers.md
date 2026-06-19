# Prashna Embed Across Layers — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the `ga_positions` bug that silences ga_prashna, build the explicit-invoke → validate → collect → cast → compute → store Prashna path, flag the multi-chart coupling gate, and author L2–L5 Prashna design.

**Architecture:**
Phase 0 patches the dead SQL query in `ga_prashna_writer.py` (reads `ga_positions` table; must pivot `chart_facts`). Phase 1 adds a FastAPI sidecar router (`routers/prashna.py`) and a Next.js API route (`/api/prashna/route.ts`), covering the full invoke→validate→collect→cast→compute→store loop for single-querent horary. Phase 2 documents the multi-chart coupling gate (the `ga_positions` orchestrator adapter passes no `birth_params`, causing it to hardcode `NATIVE_BIRTH` for all chart_ids). Phase 3 authors the L2–L5 Prashna contribution design document.

**Tech Stack:** Python/psycopg3 (sidecar), FastAPI, Next.js 14 App Router, PostgreSQL (Cloud SQL), TypeScript, pytest.

---

## Pre-work Reference

### Key file paths
| File | Role |
|---|---|
| `platform/python-sidecar/ga_writers/ga_prashna_writer.py` | Computation module — contains the bug (lines 116–121) |
| `platform/python-sidecar/pipeline/orchestrator/writers/ga_prashna.py` | Orchestrator adapter (thin wrapper) |
| `platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_prashna.py` | 18 existing unit tests |
| `platform/python-sidecar/routers/` | FastAPI routers directory |
| `platform/python-sidecar/main.py` | FastAPI app — register new router here |
| `platform/src/app/api/prashna/route.ts` | NEW: Next.js API route |
| `platform/migrations/` | SQL migrations |
| `00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md` | Migration ledger (update after every migration) |

### chart_facts column names for `graha_position`
```
fact_category = 'graha_position'
fact_subject  = graha name (e.g. "Sun", "Moon", "Lagna")
fact_key      = 'longitude_sidereal'  → fact_value_num  (float degrees)
fact_key      = 'retrograde_flag'     → fact_value_text ('retrograde' | 'direct')
```

### Corrected positions query (replace the broken `ga_positions` query)
```python
with conn.cursor() as cur:
    cur.execute("""
        SELECT fact_subject,
               MAX(CASE WHEN fact_key = 'longitude_sidereal' THEN fact_value_num  END),
               MAX(CASE WHEN fact_key = 'retrograde_flag'    THEN fact_value_text END)
        FROM chart_facts
        WHERE chart_id      = %s
          AND ayanamsha_id  = %s
          AND fact_category = 'graha_position'
        GROUP BY fact_subject
    """, (chart_id, ayanamsha_id))
    positions = {
        r[0]: {"longitude": r[1], "retrograde": (r[2] == "retrograde")}
        for r in cur.fetchall()
        if r[1] is not None
    }
```

### Multi-chart coupling identified
`platform/python-sidecar/pipeline/orchestrator/writers/ga_positions.py` line 24:
```python
s = build_ga_positions(
    chart_id=ctx.config['chart_id'],
    build_id=ctx.build_id,
    conn=ctx.db_conn,
    # ← birth_params NOT passed → falls back to NATIVE_BIRTH in ga_positions_writer.py
)
```
`build_ga_positions()` accepts an optional `birth_params` kwarg. The adapter ignores it.
This means running the orchestrator for a non-native `chart_id` computes wrong positions.
**Phase 1 works around this** by calling `build_ga_positions(birth_params=question_params)` directly from the sidecar router, bypassing the orchestrator for the prashna chart build.

---

## Phase 0 — Fix the ga_positions Bug

### Task 1: Fix positions query in ga_prashna_writer.py

**Files:**
- Modify: `platform/python-sidecar/ga_writers/ga_prashna_writer.py:115-131`
- Modify: `platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_prashna.py`

- [ ] **Step 1: Replace the broken query (lines 115–131)**

Open `ga_writers/ga_prashna_writer.py`. Replace the block that starts at line 115 (`# Step 2: Get planetary positions from ga_positions`) through line 131 (end of the `if not positions:` block) with:

```python
    # Step 2: Get planetary positions from chart_facts (graha_position rows written by ga_positions writer)
    with conn.cursor() as _cur:
        _cur.execute("""
            SELECT fact_subject,
                   MAX(CASE WHEN fact_key = 'longitude_sidereal' THEN fact_value_num  END),
                   MAX(CASE WHEN fact_key = 'retrograde_flag'    THEN fact_value_text END)
            FROM chart_facts
            WHERE chart_id      = %s
              AND ayanamsha_id  = %s
              AND fact_category = 'graha_position'
            GROUP BY fact_subject
        """, (chart_id, ayanamsha_id))
        positions = {
            r[0]: {"longitude": r[1], "retrograde": (r[2] == "retrograde")}
            for r in _cur.fetchall()
            if r[1] is not None
        }

    if not positions:
        logger.warning(
            "[ga_prashna_writer] chart_id=%s ayanamsha=%s: prashna chart exists "
            "but chart_facts has no graha_position rows — ensure ga_positions runs before ga_prashna",
            chart_id, ayanamsha_id,
        )
        return None
```

- [ ] **Step 2: Update the existing test that checks the warning message**

In `test_ga_prashna.py`, find the test that checks for the warning string `"ga_positions is empty"` (or similar) and update the expected string to match the new message: `"chart_facts has no graha_position rows"`.

- [ ] **Step 3: Run existing tests to confirm no regression**

```bash
cd platform/python-sidecar
python -m pytest pipeline/orchestrator/writers/__tests__/test_ga_prashna.py -v
```
Expected: all 18 tests PASS (the warning-message test now matches the new string).

- [ ] **Step 4: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_prashna_writer.py \
        platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_prashna.py
git commit -m "fix(ga_prashna): read positions from chart_facts not ga_positions table"
```

---

### Task 2: Migration 320 — fix asset_registry depends_on

The asset_registry currently lists `depends_on = ARRAY['ga_positions', 'bg_prashna_rules']`. The `ga_positions` entry is the correct asset_id (the writer that populates `chart_facts`), so the dependency graph is semantically right. However, the English description references `ga_positions` table directly. Update the description to be accurate.

**Files:**
- Create: `platform/migrations/320_ga_prashna_fix_description.sql`

- [ ] **Step 1: Author the migration**

```sql
-- migration 320 — ga_prashna asset_registry: fix description to reference chart_facts
-- (ga_prashna_writer previously queried ga_positions table directly; now reads chart_facts)
BEGIN;
UPDATE asset_registry
SET english_description =
    'Per-prashna-chart horary judgment: Prashna-Lagna by each method, querent/quesited '
    'significators, Tajik Ithasala/Eesarpha analysis, and fructification timing. Reads '
    'graha positions from chart_facts (written by ga_positions). Returns 0 rows for natal charts.'
WHERE asset_id = 'ga_prashna';
COMMIT;
```

- [ ] **Step 2: Apply to prod via Cloud SQL Console**

Apply `320_ga_prashna_fix_description.sql` through the Cloud SQL Console.

- [ ] **Step 3: Record in migration ledger**

Add entry to `00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md`:
```
| 320 | ga_prashna_fix_description.sql | UPDATE asset_registry description | APPLIED |
```

- [ ] **Step 4: Commit**

```bash
git add platform/migrations/320_ga_prashna_fix_description.sql \
        00_ARCHITECTURE/MIGRATIONS_APPLIED_LOG.md
git commit -m "chore(migration-320): ga_prashna asset_registry description update"
```

---

## Phase 1 — L1 Prashna Path (single-querent, explicit invoke)

### Task 3: Prashna cast module (`ga_writers/ga_prashna_cast.py`)

This module provides the direct build path for a prashna chart: compute positions for the question-moment, then run judgment. It bypasses the orchestrator (which hardcodes NATIVE_BIRTH) and calls the underlying functions directly.

**Files:**
- Create: `platform/python-sidecar/ga_writers/ga_prashna_cast.py`
- Create: `platform/python-sidecar/ga_writers/__tests__/test_ga_prashna_cast.py`

- [ ] **Step 1: Write the failing test first**

Create `ga_writers/__tests__/test_ga_prashna_cast.py`:

```python
"""Tests for ga_prashna_cast — direct prashna chart build path."""
import pytest
from unittest.mock import MagicMock, patch
from ga_writers.ga_prashna_cast import (
    validate_prashna_question,
    cast_prashna_chart,
    VALID_QUESTION_CLASSES,
)


def test_validate_rejects_lookup_question():
    result = validate_prashna_question("What is Jupiter's longitude?")
    assert result["valid"] is False
    assert "not a valid Prashna question" in result["reason"]


def test_validate_accepts_forward_looking_question():
    result = validate_prashna_question("Will I get the job I applied for?")
    assert result["valid"] is True


def test_valid_question_classes_coverage():
    assert "career" in VALID_QUESTION_CLASSES
    assert "marriage" in VALID_QUESTION_CLASSES
    assert "health_illness" in VALID_QUESTION_CLASSES


def test_cast_prashna_chart_returns_chart_id():
    """cast_prashna_chart inserts a prashna_charts row and calls ga_positions + ga_prashna."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("ga_writers.ga_prashna_cast.build_ga_positions") as mock_positions, \
         patch("ga_writers.ga_prashna_cast.seed_prashna_judgment") as mock_judgment:
        mock_positions.return_value = {"total_chart_facts_rows": 50}
        mock_judgment.return_value = 2

        result = cast_prashna_chart(
            conn=mock_conn,
            build_id="test-build-001",
            question_text="Will the project succeed?",
            question_class="career",
            prashna_lagna_method="tajik_moment_lagna",
            question_instant="2026-06-18T22:00:00+05:30",
            question_lat=20.27,
            question_lon=85.84,
            querent_natal_chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        )

    assert "chart_id" in result
    assert result["rows_inserted"] == 10  # 2 rows × 5 ayanamshas
    mock_positions.assert_called_once()
    assert mock_judgment.call_count == 5  # one per ayanamsha
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd platform/python-sidecar
python -m pytest ga_writers/__tests__/test_ga_prashna_cast.py -v
```
Expected: ImportError (module doesn't exist yet).

- [ ] **Step 3: Implement `ga_prashna_cast.py`**

Create `platform/python-sidecar/ga_writers/ga_prashna_cast.py`:

```python
"""
ga_writers/ga_prashna_cast.py
Direct Prashna chart build path (bypasses orchestrator for non-native birth_params).

The orchestrator adapter for ga_positions does not pass birth_params, so it
hardcodes NATIVE_BIRTH for all chart_ids — this is the multi-chart coupling
(see PRASHNA_LAYER_CONTRIBUTION_DESIGN.md §Multi-chart gate).

This module calls build_ga_positions and seed_prashna_judgment directly,
passing the question-moment birth_params explicitly.
"""
from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from ga_writers.ga_positions_writer import build_ga_positions, CANONICAL_AYANAMSHAS
from ga_writers.ga_prashna_writer import seed_prashna_judgment

logger = logging.getLogger(__name__)

VALID_QUESTION_CLASSES = {
    "marriage", "career", "litigation_legal", "lost_object", "health_illness",
    "finance_wealth", "travel_journey", "property_land", "children_progeny",
    "death_longevity", "spiritual_religious", "enemy_conflict",
}

# Keywords that indicate a lookup / chart-data question (not a Prashna question)
_LOOKUP_PATTERNS = [
    "longitude", "degree", "sign of", "house of", "what is", "what are",
    "tell me about", "describe", "explain", "show me",
]

# Forward-looking markers (presence of any → likely a genuine Prashna question)
_PRASHNA_MARKERS = [
    "will ", "shall ", "should ", "can i ", "would ", "when will",
    "is it possible", "are the chances", "do i have",
]


def validate_prashna_question(question_text: str) -> dict[str, Any]:
    """
    Deterministic validation: is this a genuine horary/Prashna-type question?
    Returns {"valid": bool, "reason": str}.
    A Prashna question is forward-looking (event, decision, yes/no outcome).
    A lookup question (asking for chart data) is NOT a valid Prashna question.
    """
    lower = question_text.lower().strip()

    for pat in _LOOKUP_PATTERNS:
        if pat in lower:
            return {
                "valid": False,
                "reason": (
                    f"This is not a valid Prashna question — it appears to ask for chart data "
                    f"(matched: '{pat}'). A Prashna question asks about a future event or outcome, "
                    f"e.g. 'Will I get the promotion?'"
                ),
            }

    has_prashna_marker = any(marker in lower for marker in _PRASHNA_MARKERS)
    if not has_prashna_marker and len(lower) < 20:
        return {
            "valid": False,
            "reason": (
                "This does not appear to be a forward-looking question. "
                "Please phrase your question as a yes/no horary inquiry, "
                "e.g. 'Will the contract be signed this month?'"
            ),
        }

    return {"valid": True, "reason": ""}


def cast_prashna_chart(
    conn: Any,
    build_id: str,
    question_text: str,
    question_class: str,
    prashna_lagna_method: str,
    question_instant: str,
    question_lat: float,
    question_lon: float,
    querent_natal_chart_id: str | None = None,
    kp_number: int | None = None,
    querent_direction: str | None = None,
    active_nostril: str | None = None,
) -> dict[str, Any]:
    """
    Cast a Prashna chart: create charts + prashna_charts rows, build positions,
    run ga_prashna judgment. Returns {chart_id, rows_inserted, judgment_summary}.

    Does NOT commit — caller owns the transaction.
    """
    if question_class not in VALID_QUESTION_CLASSES:
        raise ValueError(f"Unknown question_class '{question_class}'. Valid: {VALID_QUESTION_CLASSES}")

    # Parse question_instant to birth_params format
    # question_instant is ISO-8601 string (e.g. "2026-06-18T22:00:00+05:30")
    from dateutil.parser import parse as parse_dt
    dt = parse_dt(question_instant)
    dt_utc = dt.astimezone(timezone.utc)

    birth_params = {
        "year": dt_utc.year,
        "month": dt_utc.month,
        "day": dt_utc.day,
        "hour": dt_utc.hour,
        "minute": dt_utc.minute,
        "second": dt_utc.second,
        "latitude": question_lat,
        "longitude": question_lon,
        "tz_offset": 0.0,  # UTC after normalization
    }

    # Create charts row (question-moment chart)
    prashna_chart_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO charts (id, created_at)
            VALUES (%s, NOW())
            ON CONFLICT (id) DO NOTHING
            """,
            (prashna_chart_id,),
        )

    # Create prashna_charts row
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO prashna_charts (
                chart_id, question_text, question_class, prashna_lagna_method,
                question_instant, question_lat, question_lon,
                querent_natal_chart_id, kp_number, querent_direction, active_nostril
            ) VALUES (%s, %s, %s, %s, %s::timestamptz, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (chart_id) DO NOTHING
            """,
            (
                prashna_chart_id, question_text, question_class, prashna_lagna_method,
                question_instant, question_lat, question_lon,
                querent_natal_chart_id, kp_number, querent_direction, active_nostril,
            ),
        )

    # Build ga_positions for the prashna chart (question-moment birth_params)
    build_ga_positions(
        chart_id=prashna_chart_id,
        build_id=build_id,
        conn=conn,
        birth_params=birth_params,
    )

    # Run ga_prashna judgment for each ayanamsha
    total_rows = 0
    judgment_by_ayanamsha: dict[str, Any] = {}
    for ayanamsha_id in CANONICAL_AYANAMSHAS:
        rows = seed_prashna_judgment(conn, prashna_chart_id, ayanamsha_id, build_id)
        total_rows += rows
        if rows > 0:
            from ga_writers.ga_prashna_writer import compute_prashna_judgment
            judgment_by_ayanamsha[ayanamsha_id] = compute_prashna_judgment(
                conn, prashna_chart_id, ayanamsha_id
            )

    # Primary judgment = lahiri_chitrapaksha (canonical default)
    primary = judgment_by_ayanamsha.get("lahiri_chitrapaksha")

    return {
        "chart_id": prashna_chart_id,
        "rows_inserted": total_rows,
        "primary_judgment": primary,
        "judgment_by_ayanamsha": judgment_by_ayanamsha,
    }
```

- [ ] **Step 4: Run tests**

```bash
cd platform/python-sidecar
python -m pytest ga_writers/__tests__/test_ga_prashna_cast.py -v
```
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_prashna_cast.py \
        platform/python-sidecar/ga_writers/__tests__/test_ga_prashna_cast.py
git commit -m "feat(prashna): add ga_prashna_cast direct build module with validation"
```

---

### Task 4: FastAPI sidecar router (`routers/prashna.py`)

**Files:**
- Create: `platform/python-sidecar/routers/prashna.py`
- Modify: `platform/python-sidecar/main.py`

- [ ] **Step 1: Create `routers/prashna.py`**

DB connection pattern: use `psycopg.connect(os.environ["DATABASE_URL"])` as a context manager — same as `routers/panchang.py` lines 55–60. `compute_prashna_judgment` is confirmed exported from `ga_prashna_writer.py` at line 90.

```python
"""
routers/prashna.py
FastAPI router: POST /api/compute/prashna/cast

Explicit-invoke Prashna path:
  1. Validate question (deterministic rules)
  2. Cast question-moment chart + run ga_prashna judgment
  3. Return structured judgment
Namespace-isolated — never touches the native's natal chart_facts stream.
"""
from __future__ import annotations
import os
import uuid
import logging
from typing import Any, Optional
import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class PrashnaRequest(BaseModel):
    question_text: str = Field(..., min_length=10, max_length=1000)
    question_class: str
    prashna_lagna_method: str = "tajik_moment_lagna"
    question_instant: str  # ISO-8601 (e.g. "2026-06-18T22:00:00+05:30")
    question_lat: float = Field(..., ge=-90.0, le=90.0)
    question_lon: float = Field(..., ge=-180.0, le=180.0)
    querent_natal_chart_id: Optional[str] = None
    kp_number: Optional[int] = Field(None, ge=1, le=249)
    querent_direction: Optional[str] = None
    active_nostril: Optional[str] = None


class PrashnaResponse(BaseModel):
    chart_id: str
    valid: bool
    validation_reason: str
    rows_inserted: int
    primary_judgment: Optional[dict[str, Any]]


@router.post("/cast", response_model=PrashnaResponse)
async def cast_prashna(req: PrashnaRequest):
    """Cast a Prashna (horary) chart and return the judgment."""
    from ga_writers.ga_prashna_cast import validate_prashna_question, cast_prashna_chart

    # Step 1: Validate question
    validation = validate_prashna_question(req.question_text)
    if not validation["valid"]:
        return PrashnaResponse(
            chart_id="",
            valid=False,
            validation_reason=validation["reason"],
            rows_inserted=0,
            primary_judgment=None,
        )

    # Step 2: Cast + compute — same DB connection pattern as routers/panchang.py
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")

    build_id = str(uuid.uuid4())
    try:
        with psycopg.connect(db_url) as conn:
            result = cast_prashna_chart(
                conn=conn,
                build_id=build_id,
                question_text=req.question_text,
                question_class=req.question_class,
                prashna_lagna_method=req.prashna_lagna_method,
                question_instant=req.question_instant,
                question_lat=req.question_lat,
                question_lon=req.question_lon,
                querent_natal_chart_id=req.querent_natal_chart_id,
                kp_number=req.kp_number,
                querent_direction=req.querent_direction,
                active_nostril=req.active_nostril,
            )
            conn.commit()
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[prashna router] cast failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return PrashnaResponse(
        chart_id=result["chart_id"],
        valid=True,
        validation_reason="",
        rows_inserted=result["rows_inserted"],
        primary_judgment=result.get("primary_judgment"),
    )
```

- [ ] **Step 2: Register router in main.py**

In `platform/python-sidecar/main.py`, after the last `app.include_router(...)` call, add:

```python
# L1 Prashna — horary cast + judgment (namespace-isolated, never writes to native natal stream)
from routers import prashna as prashna_router
app.include_router(prashna_router.router, prefix="/api/compute/prashna", dependencies=[Depends(verify_api_key)])
```

- [ ] **Step 3: Verify sidecar starts without error**

```bash
cd platform/python-sidecar
python -c "from main import app; print('OK')"
```
Expected: `OK` (no import errors).

- [ ] **Step 4: Commit**

```bash
git add platform/python-sidecar/routers/prashna.py \
        platform/python-sidecar/main.py
git commit -m "feat(prashna): add FastAPI /api/compute/prashna/cast sidecar router"
```

---

### Task 5: Next.js API route (`/api/prashna/route.ts`)

**Files:**
- Create: `platform/src/app/api/prashna/route.ts`

- [ ] **Step 1: Check how existing routes call the sidecar**

Read one existing route that calls the Python sidecar (e.g. `platform/src/app/api/panchang/route.ts`) to understand the sidecar base URL, auth headers, and error-handling pattern. Follow that pattern exactly.

- [ ] **Step 2: Create `platform/src/app/api/prashna/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { getServerUser } from '@/lib/auth'  // follow existing auth pattern

const SIDECAR_BASE = process.env.PYTHON_SIDECAR_URL ?? 'http://localhost:8000'
const SIDECAR_API_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

export async function POST(req: NextRequest) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  let body: unknown
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const sidecarRes = await fetch(`${SIDECAR_BASE}/api/compute/prashna/cast`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': SIDECAR_API_KEY,
    },
    body: JSON.stringify(body),
  })

  const data = await sidecarRes.json()

  if (!sidecarRes.ok) {
    return NextResponse.json(
      { error: data?.detail ?? 'Sidecar error' },
      { status: sidecarRes.status },
    )
  }

  return NextResponse.json(data)
}
```

> **NOTE:** Replace `getServerUser` and import paths with whatever the project uses for auth (check another API route). The auth pattern must match existing routes.

- [ ] **Step 3: Type-check**

```bash
cd platform
npx tsc --noEmit
```
Expected: 0 errors for the new file.

- [ ] **Step 4: Commit**

```bash
git add platform/src/app/api/prashna/route.ts
git commit -m "feat(prashna): add Next.js /api/prashna POST route"
```

---

### Task 6: End-to-end smoke test (Phase 1 verify)

- [ ] **Step 1: Confirm Phase 0 fix is live**

Cast a test Prashna chart directly via Python (no API) and confirm ga_prashna produces non-zero rows:

```python
# run from platform/python-sidecar/
from tests.conftest import get_test_conn  # or however the test suite gets a connection
from ga_writers.ga_prashna_cast import cast_prashna_chart
import uuid

conn = get_test_conn()
result = cast_prashna_chart(
    conn=conn,
    build_id=str(uuid.uuid4()),
    question_text="Will the project launch succeed this quarter?",
    question_class="career",
    prashna_lagna_method="tajik_moment_lagna",
    question_instant="2026-06-18T22:00:00+05:30",
    question_lat=20.27,
    question_lon=85.84,
    querent_natal_chart_id="482012f1-710e-4a25-994a-93821f5871aa",
)
print(f"chart_id={result['chart_id']}")
print(f"rows_inserted={result['rows_inserted']}")  # Must be > 0
print(f"judgment={result['primary_judgment']}")
conn.rollback()  # smoke test only — don't pollute prod
```

Expected: `rows_inserted=10` (2 rows × 5 ayanamshas), `judgment` is a non-None dict with `judgment_text` in `{"YES", "NO", "UNCERTAIN"}`.

- [ ] **Step 2: Confirm namespace isolation**

```python
# verify prashna chart_id's rows do NOT appear in the native's natal fact stream
with conn.cursor() as cur:
    cur.execute(
        "SELECT COUNT(*) FROM chart_facts WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' "
        "AND fact_category = 'graha_position'"
    )
    native_count = cur.fetchone()[0]
    print(f"native chart_facts rows unchanged: {native_count}")  # Must be same as before

    cur.execute(
        "SELECT COUNT(*) FROM ga_prashna_judgment WHERE chart_id = %s",
        (result['chart_id'],),
    )
    prashna_count = cur.fetchone()[0]
    print(f"prashna judgment rows: {prashna_count}")  # Must be > 0
conn.rollback()
```

- [ ] **Step 3: Confirm validation gate rejects a lookup**

```python
from ga_writers.ga_prashna_cast import validate_prashna_question
v = validate_prashna_question("What is Jupiter's longitude in my chart?")
assert v["valid"] is False, f"Expected invalid, got: {v}"
print("Validation gate: PASS (rejected lookup question)")

v2 = validate_prashna_question("Will I get the job offer this month?")
assert v2["valid"] is True, f"Expected valid, got: {v2}"
print("Validation gate: PASS (accepted genuine Prashna question)")
```

- [ ] **Step 4: Commit smoke results note**

No code change needed. Add a one-line comment to the Phase 1 section of this plan marking it verified, then commit the plan update.

---

## Phase 2 — Multi-Chart Coupling Design (GATE document)

### Task 7: Author multi-chart coupling gate doc

**Files:**
- Create: `00_ARCHITECTURE/PRASHNA_MULTICHART_GATE_v1_0.md`

- [ ] **Step 1: Author the gate document**

```markdown
---
id: PRASHNA_MULTICHART_GATE
version: 1.0
status: CURRENT
authored: 2026-06-18
---
# Prashna Multi-Chart Coupling Gate

## What is gated
Full activation of "ANY querent, ANY subject" Prashna (Phase 2 of the brief) is
gated on the multi-chart platform rebuild ([[project-multichart-platform-rebuild]]).

## Root cause identified
`platform/python-sidecar/pipeline/orchestrator/writers/ga_positions.py` line 24:

```python
s = build_ga_positions(
    chart_id=ctx.config['chart_id'],
    build_id=ctx.build_id,
    conn=ctx.db_conn,
    # birth_params NOT passed → falls back to NATIVE_BIRTH
)
```

`build_ga_positions()` in `ga_positions_writer.py` has the signature:
`def build_ga_positions(chart_id, build_id, conn, birth_params=None)`.
When `birth_params=None`, it defaults to `NATIVE_BIRTH` (the hardcoded native).

**Effect**: Running the orchestrator for a non-native `chart_id` writes WRONG
positions (native's birth chart) under that chart_id.

## Phase 1 workaround (in place)
`ga_prashna_cast.py` calls `build_ga_positions(birth_params=question_params)`
directly, bypassing the orchestrator adapter. This works for the Prashna chart
because ga_prashna only needs ga_positions and bg_prashna_rules — not the full
L1 writer suite.

## What multi-chart requires
1. `orchestrator/writers/ga_positions.py`: pass `birth_params` read from the
   `charts` table for `ctx.config['chart_id']`.
2. All other orchestrator adapters that hardcode NATIVE_BIRTH (ga_structural,
   ga_strength, etc.) need the same `ctx.config['birth_params']` plumbing.
3. `ctx.config` (ContextSpec) needs a `birth_params` field populated from the
   `charts` table at build-run creation time.

## How to activate full Prashna (any querent)
When multi-chart is built:
1. Remove the workaround in `ga_prashna_cast.py` and use the orchestrator
   build trigger instead.
2. The `/api/prashna` route triggers an orchestrator build run scoped to
   `[ga_positions, bg_prashna_rules, ga_prashna]` for the prashna chart_id.
3. Gate: `querent_natal_chart_id` can be any registered chart_id (not just
   the native 482012f1).
```

- [ ] **Step 2: Commit**

```bash
git add 00_ARCHITECTURE/PRASHNA_MULTICHART_GATE_v1_0.md
git commit -m "docs(prashna): document multi-chart coupling gate for full horary activation"
```

---

## Phase 3 — L2–L5 Prashna Contribution Design

### Task 8: Author `PRASHNA_LAYER_CONTRIBUTION_DESIGN.md`

**Files:**
- Create: `00_ARCHITECTURE/PRASHNA_LAYER_CONTRIBUTION_DESIGN.md`

- [ ] **Step 1: Author the design document**

```markdown
---
id: PRASHNA_LAYER_CONTRIBUTION_DESIGN
version: 1.0
status: CURRENT
authored: 2026-06-18
---
# Prashna Layer Contribution Design (L2–L5)

Prashna is NAMESPACE-ISOLATED. The natal bo_* assets (L2 Bodha) NEVER read
ga_prashna. Each layer's Prashna contribution is a SEPARATE synthesis run
scoped to the prashna chart_id.

---

## L2 Bodha — Prashna Synthesis (DESIGN NOW, BUILD AFTER NATAL L2)

**Asset id:** `bo_prashna_bodha` (future, not yet registered)

**What it does:** A Bodha-style synthesis scoped to the PRASHNA chart (not the
native's natal chart). It reads ga_prashna_judgment + ga_prashna_lagna for the
prashna chart_id and produces a structured interpretation document.

**Scoping rule:** Uses ONLY `prashna_charts.chart_id` as its scope. Never
touches `bo_laksana`, `bo_bimba`, or any other natal Bodha asset.

**Input L1 facts consumed:**
- `ga_prashna_judgment.chart_id = prashna_chart_id` (all 5 ayanamshas)
- `ga_prashna_lagna.chart_id = prashna_chart_id`
- `bg_prashna_rules` (static reference — question class significators + yogas)

**Output:** A single `bodha_prashna` table row per (chart_id, ayanamsha_id)
with the structured judgment in JSONB.

**Build gate:** Build AFTER natal `bo_laksana` exists (reuse the WriterBase
machinery). Do NOT build before natal L2 is scaffolded.

---

## L3 Kāla — Prashna Fructification Timing (DESIGN NOW, BUILD WITH L3)

**Asset id:** `ka_prashna_timing` (future)

**What it does:** Takes the `ga_prashna_judgment.fructification_value` (the
longitudinal gap in degrees) and converts it to a calendar event window using
the Ithasala timing rules from `bg_prashna_fructification_rules`.

**Output:** An event window with `earliest_date`, `most_likely_date`,
`latest_date`, `confidence_band` (as percentage), and `timing_basis` (which
rule + sign quality applied).

**Timing formula (classical, deterministic):**
- Movable sign (Aries/Cancer/Libra/Capricorn): gap_degrees → days
- Fixed sign (Taurus/Leo/Scorpio/Aquarius): gap_degrees → months
- Dual sign (Gemini/Virgo/Sagittarius/Pisces): gap_degrees → days (lighter weight)

**Source citation:** Tājika Nīlakaṇṭhī Ch. 5 (Phala Kāla); Prashna Mārga Ch. 7

**Build gate:** Build with L3 Kāla campaign.

---

## L4 Phala — Prashna Answer Surface (DESIGN NOW, BUILD WITH L4)

**Asset id:** `ph_prashna_answer` (future)

**What it does:** Produces the STANDALONE Prashna ANSWER for delivery to the
querent. No natal appendix. Format:

```json
{
  "question": "Will I get the job offer this month?",
  "answer": "YES",
  "confidence": "moderate",
  "timing_window": "within 8–12 days",
  "primary_yoga": "ithasala",
  "significators": {"querent": "Moon", "quesited": "Mercury"},
  "classical_basis": "Tājika Nīlakaṇṭhī Ch. 4–5",
  "caveats": ["Out-of-sect Moon reduces confidence"]
}
```

**Sources:** `ph_prashna_answer` consumes `ga_prashna_judgment` (L1 raw
judgment), `ka_prashna_timing` (L3 timing window), and `bg_prashna_rules`
(classical basis).

**Build gate:** Build with L4 Phala campaign. The generative LLM MAY be used
HERE (for the `caveats` field only) — the judgment itself (`answer`, `timing_window`,
`primary_yoga`) remains DETERMINISTIC from L1/L3 data.

---

## L5 Mīmāṃsā — Outcome Tracking (DEFERRED per native decision)

Outcome capture (was the horary answer right?) is DEFERRED.
No hook, table, or migration reserved now.

When the native decides to activate L5 outcome tracking for Prashna:
- Add `prashna_outcome_log` table (question_id, resolved_at, actual_outcome, notes)
- Wire into the L5 Mīmāṃsā evaluation pipeline alongside natal predictions
- Source: same `ph_prashna_answer` asset_id as the claim being evaluated

---

## Namespace Isolation Invariant

The following MUST remain true forever:
- `bo_laksana`, `bo_bimba`, `bo_karanajala`, `bo_samskara`, `bo_sangati`,
  `bo_samvada`, `bo_upaya`, `bo_pramana_mapa` — NEVER read `ga_prashna.*`
- Natal L2 synthesis is scoped to `chart_id = 482012f1-...` (or future multi-chart
  native charts) — NEVER to prashna chart_ids
- `ga_prashna_judgment`, `ga_prashna_lagna` — ONLY consumed by Prashna-scoped
  assets (`bo_prashna_bodha`, `ka_prashna_timing`, `ph_prashna_answer`)
```

- [ ] **Step 2: Commit**

```bash
git add 00_ARCHITECTURE/PRASHNA_LAYER_CONTRIBUTION_DESIGN.md
git commit -m "docs(prashna): author L2-L5 Prashna layer contribution design"
```

---

## Final Checklist

- [ ] Phase 0 fix confirmed: `ga_prashna_writer.py` reads `chart_facts` (not `ga_positions` table)
- [ ] All 18 existing `test_ga_prashna.py` tests still pass
- [ ] Migration 320 applied + ledger updated
- [ ] Phase 1: `cast_prashna_chart()` produces non-zero rows for a test question
- [ ] Phase 1: Validation gate rejects a lookup, accepts a Prashna question
- [ ] Phase 1: Namespace isolation confirmed (no native natal stream contamination)
- [ ] Phase 1: FastAPI router registered in `main.py`, sidecar starts clean
- [ ] Phase 1: Next.js route compiles with 0 TypeScript errors
- [ ] Phase 2: Multi-chart coupling gate documented
- [ ] Phase 3: L2–L5 design document authored
- [ ] FROZEN orchestrator contract UNTOUCHED (no changes to WriterBase, orchestrator, or SubStep)
- [ ] CI green (existing test suites pass)
