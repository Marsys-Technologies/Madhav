---
lane: F-61
title: graha_saptavargaja_bala_component + vimsopaka_bala_per_graha — aggregate null value_num into computed scalar
status: DRAFT
---

## §1 Root-cause (one sentence, mechanism-level)

`_build_shadbala_extension_rows` and `_build_vimsopaka_ext_rows` in `ga_structural_writer.py` explicitly pass `value_num=None` and store only a `constituent_fact_ids` pointer to raw `chart_divisionals.id` UUIDs — the aggregation step (summing the per-varga `fact_value_num` values from those rows into the scalar the `fact_key` names) was never written, so `graha_saptavargaja_bala_component.saptavargaja_score` and `vimsopaka_bala_per_graha.vimsopaka_total` are permanently null for every graha and every ayanamsha.

## §2 Files to change

### `platform/python-sidecar/ga_writers/ga_structural_writer.py`

**Change 1 — new helper `_get_divisional_values` (insert near line 1707, after `_get_divisional_constituent_ids`):**

Add a helper that queries `chart_divisionals` by category + graha suffix and returns both the row `id` UUIDs AND their `fact_value_num` values, with a sum:

```python
def _get_divisional_values(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    fact_category: str,
    graha_suffix: str,
) -> tuple[list[str], float | None]:
    """Return (list_of_chart_divisionals_id_uuids, sum_of_fact_value_num).
    Sum is None if no rows found or all fact_value_num are NULL.
    Replaces _get_divisional_constituent_ids calls in aggregate-score blocks.
    """
    import psycopg.rows as _rows
    with conn.cursor(row_factory=_rows.tuple_row) as cur:
        cur.execute(
            """SELECT id::text, fact_value_num FROM chart_divisionals
               WHERE chart_id = %s AND ayanamsha_id = %s
                 AND fact_category = %s
                 AND split_part(fact_subject, '.', 2) = %s
               ORDER BY fact_subject""",
            (chart_id, ayanamsha_id, fact_category, graha_suffix),
        )
        rows = cur.fetchall()
    ids = [r[0] for r in rows]
    nums = [r[1] for r in rows if r[1] is not None]
    total = round(sum(nums), 4) if nums else None
    return ids, total
```

Why: `_get_divisional_constituent_ids` returns only `id` UUIDs and discards `fact_value_num`; the aggregation needs both the IDs (for citation) and the values (to compute the sum).

**Change 2 — `_build_shadbala_extension_rows`, lines 1425–1448 (graha_saptavargaja_bala_component block):**

Replace the call to `_get_divisional_constituent_ids(...) if conn is not None else []` with `_get_divisional_values(...)`, unpack into `(constituent_ids, saptavargaja_total)`, set `value_num=saptavargaja_total`, and rename the jsonb key from `constituent_fact_ids` to `constituent_divisional_ids` (honest: these are `chart_divisionals.id`, not `chart_facts.fact_id`):

```python
constituent_ids, saptavargaja_total = (
    _get_divisional_values(
        conn, chart_id, ayanamsha_id,
        "varga_saptavargaja_bala_component", subject
    )
    if conn is not None else ([], None)
)
rows.append(_base_row(
    "graha_saptavargaja_bala_component", subject, "saptavargaja_score",
    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
    value_num=saptavargaja_total,
    value_jsonb={
        "source_table": "chart_divisionals",
        "source_category": "varga_saptavargaja_bala_component",
        "constituent_divisional_ids": constituent_ids,
        "note": (
            f"chart_divisionals rows for {subject} across saptavarga set "
            f"({ayanamsha_id}); value_num is sum of fact_value_num"
        ),
    },
    verif=UNVERIFIED_DEFAULT,
    source=f"pyjhora_adapter.ga6_saptavargaja_aggregate/{eng_ver}",
    citation_human=(
        f"{g_name} saptavargaja bala: sum of {len(constituent_ids)} per-varga "
        f"strengths = {saptavargaja_total} ({ayanamsha_id})."
    ),
))
```

Why: sets `value_num` to the legitimate classical sum (SUN=93.75 for lahiri_chitrapaksha per diagnosis), earns the `saptavargaja_score` fact_key label, removes the misleading unresolvable pointer.

**Change 3 — `_build_vimsopaka_ext_rows`, lines 1658–1677 (vimsopaka_bala_per_graha block):**

Same pattern — replace `_get_divisional_constituent_ids` with `_get_divisional_values`, unpack into `(constituent_ids, vimsopaka_total)`, set `value_num=vimsopaka_total`, rename jsonb key:

```python
constituent_ids, vimsopaka_total = _get_divisional_values(
    conn, chart_id, ayanamsha_id,
    "varga_vimsopaka_contribution", subject
)
rows.append(_base_row(
    "vimsopaka_bala_per_graha", subject, "vimsopaka_total",
    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
    value_num=vimsopaka_total,
    value_jsonb={
        "source_table": "chart_divisionals",
        "source_category": "varga_vimsopaka_contribution",
        "constituent_divisional_ids": constituent_ids,
        "note": (
            f"chart_divisionals rows for {subject} across shodasavarga set "
            f"({ayanamsha_id}); value_num is sum of fact_value_num"
        ),
    },
    verif=UNVERIFIED_DEFAULT,
    source=f"pyjhora_adapter.ga6_vimsopaka_aggregate/{eng_ver}",
    citation_human=(
        f"{g_name} vimsopaka bala (shodasavarga): sum of {len(constituent_ids)} "
        f"per-varga contributions = {vimsopaka_total} ({ayanamsha_id})."
    ),
))
```

Why: closes the confirmed sibling defect; `vimsopaka_total` (shodasavarga sum across 15-20 varga contributions) was equally null across all grahas/ayanamshas.

## §3 Exit test

**File:** `platform/python-sidecar/ga_writers/__tests__/test_ga_structural_saptavargaja_aggregate.py`

**Command:** `python -m pytest platform/python-sidecar/ga_writers/__tests__/test_ga_structural_saptavargaja_aggregate.py -v`

**Fails on current code:** `_get_divisional_values` does not exist (AttributeError), and even if patched via the existing `_get_divisional_constituent_ids`, `value_num=None` is hardcoded — the assertions on `total is not None` and `total == 93.75` fail.

**Passes after fix:** new helper exists and returns `(ids, 93.75)` from the fake cursor; assertions pass.

```python
"""Exit test for F-61: graha_saptavargaja_bala_component.saptavargaja_score
and vimsopaka_bala_per_graha.vimsopaka_total must be computed scalars after fix.
Fails on current code (_get_divisional_values absent + value_num=None hardcoded).
"""
from __future__ import annotations
from ga_writers import ga_structural_writer as sut

# Per-varga rows from diagnosis (SUN, lahiri_chitrapaksha): sum = 93.75
_DIV_TABLE = [
    ("uuid-d1",  "varga_saptavargaja_bala_component", "D1.SUN",   7.5),
    ("uuid-d2",  "varga_saptavargaja_bala_component", "D2.SUN",  30.0),
    ("uuid-d3",  "varga_saptavargaja_bala_component", "D3.SUN",   3.75),
    ("uuid-d9",  "varga_saptavargaja_bala_component", "D9.SUN",  22.5),
    ("uuid-d12", "varga_saptavargaja_bala_component", "D12.SUN",  7.5),
    ("uuid-d60", "varga_saptavargaja_bala_component", "D60.SUN", 22.5),
    # vimsopaka sample
    ("uuid-v1",  "varga_vimsopaka_contribution",      "D1.SUN",   3.5),
    ("uuid-v2",  "varga_vimsopaka_contribution",      "D2.SUN",   1.5),
]

class _FakeCursor:
    def __init__(self, table): self._table = table; self._rows = []
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def execute(self, sql, params):
        _chart_id, _ayanamsha_id, fact_category, graha_suffix = params
        self._rows = [
            (r[0], r[3]) for r in self._table
            if r[1] == fact_category and r[2].split(".")[1] == graha_suffix
        ]
    def fetchall(self): return self._rows

class _FakeConn:
    def __init__(self, table): self._table = table
    def cursor(self, *a, row_factory=None, **k): return _FakeCursor(self._table)


def test_get_divisional_values_returns_ids_and_sum():
    """_get_divisional_values must exist and return (ids, sum) — fails if helper absent."""
    conn = _FakeConn(_DIV_TABLE)
    ids, total = sut._get_divisional_values(
        conn, "chart-id", "lahiri_chitrapaksha",
        "varga_saptavargaja_bala_component", "SUN"
    )
    assert total is not None, "value_num must not be None after fix (was hardcoded None)"
    assert total == 93.75, f"SUN saptavargaja sum expected 93.75, got {total}"
    assert len(ids) == 6


def test_get_divisional_values_vimsopaka():
    conn = _FakeConn(_DIV_TABLE)
    ids, total = sut._get_divisional_values(
        conn, "chart-id", "lahiri_chitrapaksha",
        "varga_vimsopaka_contribution", "SUN"
    )
    assert total is not None, "vimsopaka value_num must not be None after fix"
    assert total == 5.0, f"SUN vimsopaka sample sum expected 5.0, got {total}"
    assert len(ids) == 2


def test_no_hardcoded_value_num_none_in_saptavargaja_block():
    """Recurrence guard: saptavargaja block must not pass value_num=None to _base_row."""
    import inspect
    src = inspect.getsource(sut._build_shadbala_extension_rows)
    sapta_start = src.find("graha_saptavargaja_bala_component")
    sapta_block = src[sapta_start:] if sapta_start != -1 else src
    assert "value_num=None" not in sapta_block, (
        "graha_saptavargaja_bala_component must not hardcode value_num=None — "
        "regression to unearned null saptavargaja_score (F-61)"
    )


def test_no_hardcoded_value_num_none_in_vimsopaka_block():
    """Recurrence guard: vimsopaka block must not pass value_num=None to _base_row."""
    import inspect
    src = inspect.getsource(sut._build_vimsopaka_ext_rows)
    assert "value_num=None" not in src, (
        "vimsopaka_bala_per_graha must not hardcode value_num=None — "
        "regression to unearned null vimsopaka_total (F-61)"
    )
```

## §4 Sibling sites covered

**Covered by this fix (2 sites):**
1. `graha_saptavargaja_bala_component` / `saptavargaja_score` — `_build_shadbala_extension_rows`, lines 1425–1448. Primary defect site.
2. `vimsopaka_bala_per_graha` / `vimsopaka_total` — `_build_vimsopaka_ext_rows`, lines 1643–1678. Confirmed sibling — identical null pattern (`value_num=None` hardcoded, pointer to `chart_divisionals.id`, docstring claims aggregation).

**Explicitly excluded (with reason):**
- `graha_vimsopaka_dasavarga/shadvarga/shodasavarga` (GA3-level): diagnosis notes these appeared with populated `fact_value_num` in earlier exploration and are presumptively fine; they are not part of this lane's defect census. Excluded: not confirmed defective.
- `graha_in_house_composite_strength.bphs_weighted`: diagnosis confirms this is correctly implemented — it uses the canonical-or-floor pattern with real `chart_facts.fact_id` references via `_load_shadbala_and_bhava_fact_ids`. Excluded: not a defect.

## §5 Recurrence guard

The last two tests in §3 (`test_no_hardcoded_value_num_none_in_saptavargaja_block` and `test_no_hardcoded_value_num_none_in_vimsopaka_block`) serve as the CI lint guard: they inspect source text and assert `value_num=None` is absent from the aggregate-score blocks. If any future edit reverts to the null pattern, these tests fail closed in CI.

Additional contract: the new `_get_divisional_values` helper's return type annotation (`tuple[list[str], float | None]`) and docstring stating "Replaces `_get_divisional_constituent_ids` calls in aggregate-score blocks" make the intent auditable.

## §6 Dependencies, writer-layer declaration, and rollback

**writer_asset:** `ga_structural`
**data_delta:** `narrow` — exactly 2 fact categories × ~9 grahas × 5 ayanamshas = ~90 rows transition from `fact_value_num=NULL` to computed scalar. No new rows written, no schema change.
**Shadow run required:** YES (writer-layer fix; verifier_v must shadow-run per PROTOCOL.md Level-0 mandate before this lane enters any batch).

**Dependencies:**
- Requires GA6 (`ga_vargas` / `chart_divisionals`) to have been run first for the target chart; diagnosis confirms `varga_saptavargaja_bala_component` and `varga_vimsopaka_contribution` rows are already populated with correct per-varga `fact_value_num`.
- F-62 also touches `ga_structural` (rebuild group G1) but modifies different functions; no code overlap, no ordering dependency between F-61 and F-62.
- No migration: populating previously-null `fact_value_num` in existing writer output; schema unchanged.

**Rollback:** revert the three changes to `ga_structural_writer.py` (remove `_get_divisional_values`, restore `_get_divisional_constituent_ids` calls and `value_num=None` in both builder blocks). No DB schema rollback required — the null pattern is restored on next rebuild.

## §7 Coverage table

| Diagnosis sub-claim | Spec coverage |
|---|---|
| (a) `fact_value_num`/`fact_value_text` null for every graha, every ayanamsha (10/10 rows) | §2 Changes 2+3: `value_num=saptavargaja_total` / `value_num=vimsopaka_total` from aggregation |
| (b) jsonb pointer stores `chart_divisionals.id` (not `chart_facts.fact_id`) — naming/contract mismatch | §2 Changes 2+3: key renamed to `constituent_divisional_ids`; honest about table source |
| (c) per-varga values individually correct; SUN sum = 93.75 confirmed | §3 exit test asserts `total == 93.75` using the exact 6 constituent values from diagnosis |
| (d) no MCP-only path resolves the constituent_ids (broken citation) | §2 Changes 2+3: broken pointer pattern removed; value now served as scalar directly |
| Sibling: `vimsopaka_bala_per_graha.vimsopaka_total` same null defect, docstring claims aggregation | §2 Change 3 + §4: explicitly covered and fixed |
| §N.8 Earned-Signal: `saptavargaja_score` label unearned (no aggregation code path exists) | §2 Change 2: aggregation written; label now earned |
| §N.8 Earned-Signal: `vimsopaka_total` label unearned | §2 Change 3: aggregation written; label now earned |
| `graha_in_house_composite_strength.bphs_weighted` checked-not-affected | §4: explicitly excluded with written reason (correctly implemented) |
| GA3-level vimsopaka categories (presumptively fine, not re-derived in this lane) | §4: explicitly excluded with written reason |
