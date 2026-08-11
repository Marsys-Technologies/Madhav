"""MR-13 — honest valence + calibration_state stamping in
ka_gochara_v3_century_materialize.py (production rows in kala_gochara_windows).

PARIṢKĀRA remediation register, PG-4/PG-5, recon finding F#1.

GAP (before this fix): `_build_row()` hardcoded `"valence": "favourable"` for
EVERY event_class it serves, including the adverse-natured health classes
(`illness_acute`, `chronic_onset`) whose canonical valence per
`brahma_event_ontology.evidence_requirements->>'valence'` (migration 456,
mirrored in `services/gochara_intensity/valence.py::VALENCE_MAP` and
`services/gochara_grammar/event_class_scope.py`'s own docstring) is `'loss'`
— never `'favourable'`/`'gain'`. `surgery`'s canonical valence is `'neutral'`
(a scheduled procedure is not itself a loss event) — also never
`'favourable'`.

`calibration_state` was ALREADY honestly stamped `'structural_prior'` by this
writer (`_build_row` line ~490) — the writer itself never emits
`'empirically_calibrated'`. A SEPARATE, out-of-band raw SQL UPDATE (not part
of any writer code path in this repo) stamped `calibration_state =
'empirically_calibrated'` on all 120 `generation='3.0'` rows in
`kala_gochara_windows` for the two canonical charts, with no real fit ever
having run for those classes (`gochara_v3_calibration` has no admitted-
mechanism fit rows backing a century-materialize class). Re-running this
writer (delete-then-insert, §N.3) restores `calibration_state` to
`'structural_prior'` as a side effect — the fix here is scoped to `valence`;
`calibration_state` needs no code change, only a re-run through this path.

FIX: `_build_row()` now takes `valence`/`is_adverse` as REQUIRED keyword
parameters (no default of `'favourable'`/`False`), derived once per substep
by `_fetch_class_valence()` — a live read of
`brahma_event_ontology.evidence_requirements->>'valence'`, honest-degrade to
a small documented fallback map (transcribed from the same migration 456
values `gochara_intensity.valence.VALENCE_MAP` transcribes) on any read
failure. This is a direct SQL query, NOT an import from
`services.gochara_intensity` / `services.gochara_grammar` — the I2 constraint
(AC6, enforced by `test_w34_century_horizon.py` /
`test_ka_gochara_v3_mutation_guard.py`) forbids the import, not a read of the
shared ontology table this module already reads elsewhere
(`fetch_base_rate_for_class`, `_fetch_resonance_targets`).
"""
from __future__ import annotations

import inspect
import re

import pytest

import pipeline.orchestrator.writers.ka_gochara_v3_century_materialize as mod
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.ka_gochara_v3_century_materialize import (
    ASSET_ID,
    GENERATION_PROD,
    GENERATION_V3,
    PROD_TABLE,
    TABLE,
    GocharaV3CenturyMaterializeWriter,
)

# ---------------------------------------------------------------------------
# Fake DB connection (mirrors test_w34_century_horizon.py's fixture)
# ---------------------------------------------------------------------------


class _FakeCursor:
    def __init__(self, owner: "_FakeConn"):
        self._owner = owner

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        return self._owner.execute(sql, params)

    def fetchall(self):
        return self._owner.rows_for_next

    def fetchone(self):
        rows = self._owner.rows_for_next
        return rows[0] if rows else None


class _FakeConn:
    """Records every SQL statement. Forbids commit/rollback/close (§N.2)."""

    def __init__(self, responder=None):
        self.responder = responder or (lambda sql, params: [])
        self.statements: list[tuple[str, object]] = []
        self.rows_for_next: list[dict] = []

    def cursor(self):
        return _FakeCursor(self)

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        self.rows_for_next = self.responder(sql, params)
        return _FakeCursor(self)

    def commit(self):  # pragma: no cover
        raise AssertionError("writer called commit() — forbidden by §N.2")

    def rollback(self):  # pragma: no cover
        raise AssertionError("writer called rollback() — forbidden by §N.2")

    def close(self):  # pragma: no cover
        raise AssertionError("writer called close() — forbidden by §N.2")


BUILD_STATE_TABLE = "kala_gochara_v2_build_state"

# MR-16: default discovered event classes for plan_substeps' discovery query
# — the 6 classes this file parametrizes over.
_DISCOVERED_CLASSES = [
    "career_advancement", "major_gain", "marriage",
    "illness_acute", "chronic_onset", "surgery",
]


def _ctx(conn, chart_id="482012f1-710e-4a25-994a-93821f5871aa") -> ContextSpec:
    return ContextSpec(
        asset_id=ASSET_ID,
        build_id="test-build-mr13",
        db_conn=conn,
        config={"chart_id": chart_id},
    )


def _responder(
    *,
    targets: list[str] = ("Venus",),
    stored_fp: str | None = None,
    rows_exist: bool = False,
    ontology_valence: dict[str, str] | None = None,
):
    """Build a query responder for _FakeConn.

    ontology_valence: if given, a dict of event_class -> valence string that
    a query against `brahma_event_ontology` should return (simulating a live
    ontology read). If the event_class is not in the dict, the responder
    returns [] (simulating "no row" -- forces the honest fallback path).
    """
    ontology_valence = ontology_valence or {}

    def responder(sql: str, params=None) -> list[dict]:
        s = sql.lower()
        if "gochara_resonance_map" in s and "distinct" in s and "target_ref" not in s:
            return [{"event_class": ec} for ec in _DISCOVERED_CLASSES]
        if "gochara_resonance_map" in s and "target_ref" in s:
            return [{"target_ref": t} for t in targets]
        if BUILD_STATE_TABLE in s and sql.strip().upper().startswith("SELECT"):
            if stored_fp is None:
                return []
            return [{"class_fingerprint": stored_fp}]
        if TABLE in s and "limit 1" in s:
            return [{"1": 1}] if rows_exist else []
        if "brahma_event_ontology" in s and "valence" in s:
            ec = params[0] if params else None
            if ec in ontology_valence:
                return [{"valence": ontology_valence[ec]}]
            return []
        return []
    return responder


def _patch_common(monkeypatch, boundaries):
    monkeypatch.setattr(mod, "find_threshold_crossings", lambda *a, **k: boundaries)
    monkeypatch.setattr(
        mod, "ClassContext",
        type("FakeClassContext", (), {"fetch": staticmethod(lambda **k: object())}),
        raising=False,
    )
    try:
        import swisseph  # noqa: F401
    except ImportError:
        import types, sys
        sys.modules["swisseph"] = types.ModuleType("swisseph")


def _make_boundary(era_key: str, peak_lambda: float = 0.5):
    from services.gochara_v3.interval_solver import IntervalBoundary
    return IntervalBoundary(
        enter_jd=2445736.5 + 10.0,
        exit_jd=2445736.5 + 20.0,
        peak_jd=2445736.5 + 15.0,
        peak_lambda=peak_lambda,
        era_slice_key=era_key,
    )


def _run_substep_for_class(monkeypatch, event_class: str, *, ontology_valence=None,
                            chart_id="482012f1-710e-4a25-994a-93821f5871aa"):
    """Drive one substep for `event_class` and return the writer's statements."""
    writer = GocharaV3CenturyMaterializeWriter()
    conn_dummy = _FakeConn(_responder(targets=["Venus"]))
    all_steps = writer.plan_substeps(_ctx(conn_dummy, chart_id))
    step = next(s for s in all_steps if s.key.startswith(f"{event_class}::"))
    _, era_key = step.key.split("::", 1)

    conn = _FakeConn(_responder(
        targets=["Venus"], stored_fp=None, ontology_valence=ontology_valence,
    ))
    ctx = _ctx(conn, chart_id)
    _patch_common(monkeypatch, [_make_boundary(era_key)])

    writer.run_substep(ctx, step)
    return conn.statements


_INSERT_TABLE_RE = re.compile(r"INSERT\s+INTO\s+(\S+)", re.IGNORECASE)


def _inserts_for_table(statements, table: str):
    """Statements whose INSERT INTO target is EXACTLY `table` (not a prefix
    match — kala_gochara_windows is a strict prefix of
    kala_gochara_windows_v2, so a naive .startswith() over-matches)."""
    out = []
    for sql, params in statements:
        if not isinstance(params, dict):
            continue
        m = _INSERT_TABLE_RE.match(sql.strip())
        if m and m.group(1).lower() == table.lower():
            out.append(params)
    return out


def _prod_inserts(statements):
    return _inserts_for_table(statements, PROD_TABLE)


def _v2_inserts(statements):
    return _inserts_for_table(statements, TABLE)


# ===========================================================================
# Static-source guard — no hardcoded 'favourable' literal (mirrors MR-04)
# ===========================================================================


def test_build_row_source_has_no_hardcoded_favourable_valence():
    """`_build_row` must never assign the literal 'favourable' to the
    `valence` dict key — that was the exact dishonest default this fix
    removes. The word may still appear in comments/docstrings, but not as
    the RHS of a `"valence":` key assignment."""
    source = inspect.getsource(mod._build_row)
    bad_pattern = re.compile(r'"valence"\s*:\s*"favourable"')
    assert not bad_pattern.search(source), (
        "_build_row still hardcodes \"valence\": \"favourable\" — this must "
        "be derived per event_class, never a fixed literal."
    )


def test_build_row_requires_valence_and_is_adverse_parameters():
    """`_build_row` must accept `valence`/`is_adverse` as real parameters
    (not silently defaulted inside the function body) so every caller is
    forced to supply an honestly-derived value."""
    sig = inspect.signature(mod._build_row)
    assert "valence" in sig.parameters, (
        "_build_row must accept a `valence` parameter — it must not "
        "compute/hardcode this value internally."
    )
    assert "is_adverse" in sig.parameters, (
        "_build_row must accept an `is_adverse` parameter."
    )
    # No hardcoded 'favourable'/False default hiding the same defect one
    # level down at the parameter-default level.
    valence_default = sig.parameters["valence"].default
    assert valence_default in (inspect.Parameter.empty,), (
        f"_build_row's `valence` parameter must not carry a default value "
        f"(forces every call site to supply an honest one); got "
        f"{valence_default!r}"
    )


# ===========================================================================
# Functional — per-event_class valence is honestly derived, not favourable
# ===========================================================================


ONTOLOGY_VALENCE_FIXTURE = {
    "career_advancement": "gain",
    "major_gain": "gain",
    "marriage": "neutral",
    "illness_acute": "loss",
    "chronic_onset": "loss",
    "surgery": "neutral",
}


@pytest.mark.parametrize("event_class,expected_valence,expected_adverse", [
    ("career_advancement", "gain", False),
    ("major_gain", "gain", False),
    ("marriage", "neutral", False),
    ("illness_acute", "loss", True),
    ("chronic_onset", "loss", True),
    ("surgery", "neutral", False),
])
def test_prod_row_valence_matches_ontology_per_class(
    monkeypatch, event_class, expected_valence, expected_adverse,
):
    """Every one of the 6 event classes gets its OWN canonical valence from
    brahma_event_ontology (live-read fixture here) — never a blanket
    'favourable'/'gain'. Adverse health classes (illness_acute,
    chronic_onset) must resolve to valence='loss', is_adverse=True."""
    statements = _run_substep_for_class(
        monkeypatch, event_class, ontology_valence=ONTOLOGY_VALENCE_FIXTURE,
    )
    prod_rows = _prod_inserts(statements)
    assert len(prod_rows) == 1, f"expected 1 prod row for {event_class}, got {len(prod_rows)}"
    row = prod_rows[0]
    assert row["valence"] == expected_valence, (
        f"{event_class}: expected valence={expected_valence!r}, got {row['valence']!r}"
    )
    assert row["is_adverse"] == expected_adverse, (
        f"{event_class}: expected is_adverse={expected_adverse!r}, got {row['is_adverse']!r}"
    )
    assert row["valence"] != "favourable", (
        f"{event_class}: 'favourable' is not a valid kala_gochara_windows "
        f"valence value (schema is gain|loss|neutral|mixed) — the old defect."
    )


def test_illness_acute_never_favourable_even_on_ontology_read_failure(monkeypatch):
    """When the live brahma_event_ontology read fails/returns nothing (fixture
    with no ontology_valence entries -- simulates connectivity failure), the
    honest fallback for illness_acute must still resolve to 'loss', never
    'favourable' -- an unreachable ontology must never silently launder an
    adverse class into a favourable-looking row."""
    statements = _run_substep_for_class(monkeypatch, "illness_acute", ontology_valence={})
    prod_rows = _prod_inserts(statements)
    assert len(prod_rows) == 1
    assert prod_rows[0]["valence"] == "loss"
    assert prod_rows[0]["is_adverse"] is True


def test_surgery_never_favourable_even_on_ontology_read_failure(monkeypatch):
    """Same honest-fallback discipline for 'surgery' (canonical 'neutral')."""
    statements = _run_substep_for_class(monkeypatch, "surgery", ontology_valence={})
    prod_rows = _prod_inserts(statements)
    assert len(prod_rows) == 1
    assert prod_rows[0]["valence"] == "neutral"
    assert prod_rows[0]["valence"] != "favourable"


def test_v2_staging_rows_carry_the_same_honest_valence(monkeypatch):
    """The calibration/staging table (kala_gochara_windows_v2) rows must
    carry the SAME honestly-derived valence as the production rows -- both
    come from the same _build_row call per boundary."""
    statements = _run_substep_for_class(
        monkeypatch, "illness_acute", ontology_valence=ONTOLOGY_VALENCE_FIXTURE,
    )
    v2_rows = _v2_inserts(statements)
    assert len(v2_rows) == 1
    assert v2_rows[0]["valence"] == "loss"
    assert v2_rows[0]["is_adverse"] is True


# ===========================================================================
# calibration_state — writer path already honest; regression-lock it
# ===========================================================================


@pytest.mark.parametrize("event_class", [
    "career_advancement", "major_gain", "marriage",
    "illness_acute", "chronic_onset", "surgery",
])
def test_prod_row_calibration_state_is_always_structural_prior(monkeypatch, event_class):
    """calibration_state must be 'structural_prior' for every class this
    writer serves -- 'empirically_calibrated' may ONLY be earned by a real
    fit (MR-14, not this writer's job). Regression lock against the writer
    path ever regaining a hardcoded 'empirically_calibrated'."""
    statements = _run_substep_for_class(
        monkeypatch, event_class, ontology_valence=ONTOLOGY_VALENCE_FIXTURE,
    )
    prod_rows = _prod_inserts(statements)
    assert len(prod_rows) == 1
    assert prod_rows[0]["calibration_state"] == "structural_prior", (
        f"{event_class}: calibration_state must be 'structural_prior' "
        f"(never fabricated 'empirically_calibrated'), got "
        f"{prod_rows[0]['calibration_state']!r}"
    )
