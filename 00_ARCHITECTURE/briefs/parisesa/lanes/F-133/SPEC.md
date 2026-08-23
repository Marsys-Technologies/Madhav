---
artifact: F-133_SPEC
lane: F-133
stream: S5 MULA (fix lives in Python sidecar, lease needed from sidecar team)
class: CL-03 (missing horizon predicate) + CL-13 (misleading disclosure)
rs_class: RS-B
writer_asset: null
data_delta: narrow
status: REVISED
spec_writer: SPEC_WRITER
---

# F-133 SPEC: `phala_outlook_get` — horizon-scope mitigations and correct misleading trim_report hint

## 1. Root-cause statement

`mitigation_map()` in `brahmagyan/phala/mitigation.py` has no `date_range` / window-overlap parameter — its SQL carries zero temporal predicate and sorts purely by `obstruction_severity` — so `_fetch_mitigations()` in `outlook.py` cannot thread the `date_range` already computed at line 428–431 into the call, causing arbitrary past rows (including one predating the native's birth by 17.8 years) to outrank in-horizon mitigations, while `layer_provenances.PH-4-2` carries no horizon disclosure and the MCP-layer `trim_report` recover_via hint (in the generic `autoDetectTrimmableSections` fallback at `response_budget.ts:527`) falsely implies `date_range` is an available filter when it currently is not.

## 2. Files to change

### 2a. `platform/python-sidecar/brahmagyan/phala/mitigation.py`

**Why:** `mitigation_map()` has no temporal parameter and no SQL overlap predicate; `window_start`/`window_end` are already SELECTed columns — the data to filter is present, just never applied to WHERE.

**What:**
1. Add `date_range: Optional[dict[str, str]] = None` to `mitigation_map()` signature (after `limit`).
2. When `date_range` is provided, append the standard interval-overlap predicate to `conditions`:
   ```python
   if date_range:
       conditions.append("window_start <= %s::date")
       conditions.append("window_end >= %s::date")
       params.extend([date_range["end"], date_range["start"]])
   ```
   This mirrors `anchors.py::event_anchors()` exactly (overlap = start <= range_end AND end >= range_start).
3. Add `date_range_filter_applied: bool` and `date_range` fields to `provenance_envelope` (True when `date_range` was supplied).
4. No change to `ORDER BY` — severity sort is still meaningful within the filtered window.

### 2b. `platform/python-sidecar/brahmagyan/phala/outlook.py`

**Why:** `_fetch_mitigations()` must receive and forward `date_range`. The PH-4-2 provenance block gains the date_range disclosure automatically from (2a).

**What:**
1. Change `_fetch_mitigations(chart_id: str)` → `_fetch_mitigations(chart_id: str, date_range: dict[str, str])`.
2. Thread into the call: `mitigation_map(conn, chart_id, date_range=date_range)`.
3. Update call site (line 439): `mitigations, mitigations_prov = _fetch_mitigations(chart_id, date_range)`.
4. **No hint-text edit required in this file or in `mitigation.py`.** Neither file contains any `trim_report`/`recover_via`/hint construction (confirmed by source scan). The misleading hint (`"narrower filter/date_range"`) lives exclusively in the generic `autoDetectTrimmableSections` fallback at `response_budget.ts:527`, which is outside this lane's file set. After the SQL predicate fix lands, `date_range` IS now applied by `mitigation_map()`, making the generic hint accurate rather than false — no Python edit is needed to fix the accuracy. The schema-neutral text of `response_budget.ts:527` is separately addressed by F-09 (branch `par/night-F-09`, pending merge) for all callers. **Builder MUST NOT touch `response_budget.ts` or any TS file** — the `phala_outlook.ts:59` explicit sections are already correct (`hint: 'full mitigation/remedy list'`) and do not reference `date_range`.

## 3. Exit test

**File:** `platform/python-sidecar/brahmagyan/phala/__tests__/test_mitigation_horizon.py`

**Command (run from builder worktree root):**
```bash
python -m pytest platform/python-sidecar/brahmagyan/phala/__tests__/test_mitigation_horizon.py -v
```

**FAIL on current code:** `mitigation_map()` raises `TypeError: mitigation_map() got an unexpected keyword argument 'date_range'` when called with `date_range={...}`.

**PASS after fix:** When called with `date_range={"start": "2026-08-16", "end": "2028-02-07"}`, every row in `result["mitigations"]` satisfies `window_start <= 2028-02-07 AND window_end >= 2026-08-16`; rows with `window_end` before `2026-08-16` (e.g., the 1968-09-21 and 1997-11-14 cases) are absent; `provenance_envelope["date_range_filter_applied"]` is `True`.

**Test sketch (builder writes full implementation):**
```python
import pytest
from unittest.mock import MagicMock, patch
from brahmagyan.phala.mitigation import mitigation_map

def _make_row(**kw):
    base = {
        "mitigation_id": "x", "linked_anchor_id": None, "obstruction_id": 1,
        "afflicting_graha": "Sa", "obstruction_severity": 0.8, "intensity_tier": "moderate",
        "program_jsonb": {}, "tradition_options_jsonb": {}, "cross_tradition_corroboration": None,
        "recommended_tier_jsonb": None, "proportionality_basis": None,
        "window_start": "2026-01-01", "window_end": "2027-01-01",
        "re_evaluation_date": None, "classical_citation": "BPHS", "source_citation": "S1",
        "computed_at": "2026-08-16T00:00:00Z",
    }
    base.update(kw)
    return base

def test_mitigation_map_filters_by_date_range():
    """Rows outside the requested horizon must be excluded."""
    in_rows = [
        _make_row(mitigation_id="IN1", window_start="2025-03-29", window_end="2027-09-12"),
        _make_row(mitigation_id="IN2", window_start="2025-03-29", window_end="2027-09-12"),
    ]
    out_rows = [
        _make_row(mitigation_id="OUT1", window_start="1966-04-08", window_end="1968-09-21"),
        _make_row(mitigation_id="OUT2", window_start="1995-06-02", window_end="1997-11-14"),
        _make_row(mitigation_id="OUT3", window_start="2022-07-12", window_end="2024-12-25"),
    ]
    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [in_rows, [{"count": 5}]]
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    result = mitigation_map(
        mock_conn, "fake-chart-id",
        date_range={"start": "2026-08-16", "end": "2028-02-07"}
    )
    ids = {r["mitigation_id"] for r in result["mitigations"]}
    assert ids == {"IN1", "IN2"}, f"Expected only in-horizon rows; got: {ids}"
    assert result["provenance_envelope"]["date_range_filter_applied"] is True
    assert all(r["mitigation_id"] != "OUT1" for r in result["mitigations"])

def test_mitigation_map_no_date_range_returns_all():
    """Backward-compat: omitting date_range preserves original behavior."""
    rows = [_make_row(mitigation_id="A")]
    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = [rows, [{"count": 1}]]
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    result = mitigation_map(mock_conn, "fake-chart-id")
    assert result["provenance_envelope"]["date_range_filter_applied"] is False
```

## 4. Sibling sites covered

| Site | Decision |
|---|---|
| `brahmagyan/phala/mitigation.py::mitigation_map()` | PRIMARY FIX — horizon predicate added |
| `brahmagyan/phala/outlook.py::_fetch_mitigations()` + call site | PRIMARY FIX — threading + disclosure |
| `L4_phala/query_phala_calibration.ts::queryRemedyProgramCapability` (same `phala_mitigation` table, same defect shape) | EXCLUDED — bundled with F-08 per `PAR-F-08-NEEDS-LEASE` precedent; builder MUST NOT touch this file; conductor flag: `PAR-F-133-SIBLING-TO-F-08` |
| `L4_phala/query_prospective_ledger.ts` (no date predicate, different table) | EXCLUDED — different table, not live-reproduced in this lane; flagged for future CL-03 census |
| `L4_phala/query_predictive_anchors.ts` (categorical `horizon_tier`, not date-overlap) | EXCLUDED — different defect shape (categorical vs. absent), different lane needed |
| `brahmagyan/phala/outlook.py::_fetch_auspicious_windows()` (PH-4-4) | EXCLUDED — confirmed correctly windowed (`WHERE date BETWEEN %s AND %s`) per diagnosis §4 |
| `muhurta.py::fetch_muhurta_windows` | EXCLUDED — caller validates `date_range` (max 90 days) before query; not a sibling |
| `platform-mcp/src/lib/response_budget.ts` (generic hint at line 527) | EXCLUDED — no edit needed; post-fix hint becomes accurate; schema-neutral text fix delegated to F-09 (`par/night-F-09`, pending merge) |

## 5. Recurrence guard

In the same test file (`test_mitigation_horizon.py`), add a signature introspection test:

```python
import inspect
from brahmagyan.phala.mitigation import mitigation_map

def test_mitigation_map_has_date_range_param():
    """F-133 recurrence guard: date_range must remain a declared parameter."""
    sig = inspect.signature(mitigation_map)
    assert "date_range" in sig.parameters, (
        "mitigation_map() must declare date_range param — F-133 recurrence guard. "
        "If you are removing this param, re-open F-133 and re-spec."
    )
```

This test fails immediately if a future refactor removes the parameter from the signature, making the regression fail-closed in CI.

## 6. Dependencies and rollback

**Dependencies:**
- **F-08**: Holds lease on `query_phala_calibration.ts`. F-133 is independent of F-08's merge order — different file set. Raise `PAR-F-133-SIBLING-TO-F-08` in the ledger so the conductor can batch the TS sibling fix with F-08.
- **F-09**: Addresses schema-neutral hint text in `response_budget.ts:527` for all callers. F-133 is independent — no Python hint edit needed; post-fix the generic hint is accurate for `phala_outlook_get`.
- **No DB migration**: `window_start` and `window_end` are already columns on `phala_mitigation` (confirmed selected at line 780–781 of current `mitigation.py`). The fix adds a SQL WHERE predicate using existing columns — zero schema change.
- **No rebuild / shadow-only**: `brahmagyan/phala/` is a serving-layer file, not a writer-layer asset. No GA/BO data is written. Shadow run by verifier_v (read-only DB probe asserting in-horizon rows returned, rollback) is sufficient per PROTOCOL Level-0.

**Rollback:** Revert the two Python files. One logical revert, no migration, no rebuild side-effect.

## 7. Coverage table

| Diagnosis claim | Covered by |
|---|---|
| §1 live repro: 8/10 rows outside query_window | Exit test §3 (fabricated rows, same overlap logic); shadow run live probe |
| §2a anchors correctly scoped (contrast case) | Acknowledged; no code change; PH-4-1 excluded from sibling list (§4) |
| §2b mitigations NOT horizon-scoped (primary defect) | §2a: `mitigation_map()` gains `date_range` + SQL WHERE overlap predicate |
| §2c row `47e7fcdf` predates native birth by 17.8 years | §3 exit test: `OUT1` (window_end 1968-09-21) asserted absent in result |
| §2d no disclosure (PH-4-2) | §2a item 3: `date_range_filter_applied` + `date_range` fields added to `provenance_envelope` |
| §2d misleading trim_report hint (`date_range` implied available) | Post-fix: `date_range` IS now applied, so hint is accurate, not false. No Python edit needed (no hint construction in `outlook.py`/`mitigation.py` — confirmed by source scan). Generic text separately fixed by F-09 for all callers. Builder MUST NOT edit `response_budget.ts`. |
| §3 mechanism: `_fetch_mitigations()` missing `date_range` arg | §2b items 1–3: signature + call site fixed |
| §3 mechanism: `mitigation_map()` no param, no SQL predicate | §2a items 1–3: param added, WHERE clause added, provenance updated |
| §4 sibling `query_phala_calibration.ts` (same table) | §4: excluded/bundled F-08; PAR-F-133-SIBLING-TO-F-08 flag raised |
| §4 sibling `query_prospective_ledger.ts` | §4: excluded (different table, not live-reproduced) |
| §4 sibling `query_predictive_anchors.ts` | §4: excluded (different defect shape) |
| §4 PH-4-4 confirmed correctly windowed | §4: excluded, no defect |
| §4 muhurta.py not a sibling | §4: excluded, caller validates |
| §5 S5 alias (`register_p1_aliases.ts`) verified clean | §2: files_to_change are Python sidecar only; no TS alias change |
| `response_budget.ts:527` generic hint | §4 sibling table: excluded; no edit needed; delegated to F-09 |
