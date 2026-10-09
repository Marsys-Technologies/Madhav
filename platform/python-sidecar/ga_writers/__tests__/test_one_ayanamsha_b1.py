"""ONE_AYANAMSHA Phase 1, batch B1 (SS N-309/N-311): the 18 ga_writers files take their ayanamsha set from
`brahmagyan.ayanamsha_scope.ayanamshas_for_chart` with NO behaviour change for the default (all five).

What is pinned here
  * source level (AST, no import, so it runs without psycopg / the engines): the migrated files no longer hold a
    literal list of the ids, import the helper, and their use sites call `ayanamshas_for_chart` instead of looping the
    module constant;
  * the exported constants still equal the OLD literals element for element (three files had a non-canonical order:
    ayurdaya, medical, sensitive_degree);
  * behaviour (imported with `_import_or_skip`, so a missing psycopg / engine skips instead of failing): with a fake
    connection that has no `charts.build_ayanamshas` column every site loops EXACTLY the old list in the old order; with a
    configured subset it loops exactly that subset;
  * SS N-311 golden gate: the rows ga_positions and ga_dashas produce for the DEFAULT set are byte-identical to what the
    code at the B0 base commit (suvarna/ayanamsha-scope @ 2cc2a77e3) produced (sha256 over a canonical serialisation of
    every row, computed by running that base code), and the test demonstrably fails when an ayanamsha is dropped.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib
import json
import logging
from pathlib import Path

import pytest

from brahmagyan import ayanamsha_scope as scope

SIDECAR = Path(__file__).resolve().parents[2]

FIVE = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
# ayurdaya / medical / sensitive_degree historically listed krishnamurti before true_chitra: kept element for element.
OLD_ALT_ORDER = ["lahiri_chitrapaksha", "krishnamurti", "true_chitra", "raman", "surya_siddhanta_classical"]
OLD_ADAPTER_MAP = {
    "lahiri_chitrapaksha": "lahiri",
    "true_chitra": "true_chitra",
    "krishnamurti": "kp",
    "raman": "raman",
    "surya_siddhanta_classical": "surya_siddhanta",
}
CHART = "11111111-2222-3333-4444-555555555555"

USE_SITE_FILES = [
    "ga_writers/ga_positions_writer.py", "ga_writers/ga_dashas_writer.py", "ga_writers/ga_panchanga_writer.py",
    "ga_writers/ga_sade_sati_writer.py", "ga_writers/ga_sensitive_writer.py", "ga_writers/ga_strength_writer.py",
    "ga_writers/ga_structural_writer.py", "ga_writers/ga_tajaka_writer.py", "ga_writers/ga_vargas_writer.py",
]
CONSTANT_ONLY_FILES = [
    "ga_writers/_positions_independent_verifier.py", "ga_writers/ga_ayurdaya_writer.py", "ga_writers/ga_medical_writer.py",
    "ga_writers/ga_prashna_writer.py", "ga_writers/ga_sensitive_degree_writer.py", "ga_writers/ga_yoga_writer.py",
]
# Pure helpers / no real set use: left on the default constant (or untouched), see the PR body.
UNCHANGED_FILES = [
    "ga_writers/ga_condition_writer.py", "ga_writers/ga_daridra_postpass.py", "ga_writers/ga_prashna_cast.py",
]
ALL_B1 = USE_SITE_FILES + CONSTANT_ONLY_FILES + UNCHANGED_FILES


# ── a fake connection that speaks just enough SQL for the helper ──────────────────────────────────────────────────────

class _Cursor:
    def __init__(self, conn):
        self._c, self._row = conn, None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._c.sql.append(sql)
        if "information_schema.columns" in sql:
            self._row = (1,) if self._c.configured is not None else None
        elif "build_ayanamshas" in sql:
            self._row = (self._c.configured,)
        else:
            self._row = None

    def fetchone(self):
        return self._row


class FakeConn:
    """`configured=None`: the charts.build_ayanamshas column does not exist (today's reality). A list: the column exists and
    this chart's value is that list."""

    def __init__(self, configured=None):
        self.configured, self.sql = configured, []
        scope.reset_cache()          # the helper caches the column check for a minute: a new fake connection is a new database

    def cursor(self, *a, **k):
        return _Cursor(self)


@pytest.fixture(autouse=True)
def _fresh_helper_cache():
    scope.reset_cache()
    yield
    scope.reset_cache()


def _import_or_skip(name: str):
    try:
        return importlib.import_module(name)
    except ImportError as exc:                     # psycopg / jhora / swisseph not installed (CI has no psycopg)
        pytest.skip(f"{name} not importable here: {exc}")


# ── source level (AST) pins ───────────────────────────────────────────────────────────────────────────────────────────

def _tree(rel: str) -> ast.AST:
    return ast.parse((SIDECAR / rel).read_text(encoding="utf-8"))


def _literal_hits(node: ast.AST) -> int:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        elts = node.elts
    elif isinstance(node, ast.Dict):
        elts = [k for k in node.keys if k is not None]
    else:
        return 0
    return len({e.value for e in elts if isinstance(e, ast.Constant) and isinstance(e.value, str)} & set(FIVE))


def _imports_scope(tree: ast.AST) -> bool:
    return any(isinstance(n, ast.ImportFrom) and n.module == "brahmagyan.ayanamsha_scope" for n in ast.walk(tree))


def _calls(tree: ast.AST, fname: str) -> list[ast.Call]:
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Name) and f.id == fname) or (isinstance(f, ast.Attribute) and f.attr == fname):
                out.append(n)
    return out


@pytest.mark.parametrize("rel", ALL_B1)
def test_no_literal_list_of_the_five_ids(rel):
    tree = _tree(rel)
    assert [n.lineno for n in ast.walk(tree) if _literal_hits(n) >= 3] == []


@pytest.mark.parametrize("rel", USE_SITE_FILES + CONSTANT_ONLY_FILES)
def test_migrated_file_imports_the_shared_helper(rel):
    assert _imports_scope(_tree(rel)), f"{rel} must take the ayanamsha ids from brahmagyan.ayanamsha_scope"


@pytest.mark.parametrize("rel", USE_SITE_FILES)
def test_use_site_calls_ayanamshas_for_chart(rel):
    assert _calls(_tree(rel), "ayanamshas_for_chart"), f"{rel}: no ayanamshas_for_chart call at its use site"


_CONSTANT_NAMES = {"CANONICAL_AYANAMSHAS", "AYANAMSHAS", "_AYANAMSHA_LIST"}


def _iterates_constant(node: ast.AST) -> bool:
    """True if the loop / comprehension iterable mentions the module-level default constant."""
    return any(isinstance(n, ast.Name) and n.id in _CONSTANT_NAMES for n in ast.walk(node))


@pytest.mark.parametrize("rel", USE_SITE_FILES)
def test_no_loop_still_iterates_the_default_constant(rel):
    offenders = []
    for n in ast.walk(_tree(rel)):
        iters = []
        if isinstance(n, (ast.For, ast.AsyncFor)):
            iters = [n.iter]
        elif isinstance(n, ast.comprehension):
            iters = [n.iter]
        if any(_iterates_constant(i) for i in iters):
            offenders.append(getattr(n, "lineno", getattr(n.iter, "lineno", "?")))
    assert offenders == [], f"{rel}: loops over the default constant at line(s) {offenders}"


def test_pipeline_pure_helpers_keep_the_default_constant():
    """ga_prashna_cast builds a FRESH prashna chart (a new uuid that is not a row of `charts`), so there is no chart scope to
    ask; ga_positions_writer resolves the same default for it. It keeps iterating the exported default."""
    tree = _tree("ga_writers/ga_prashna_cast.py")
    assert any(isinstance(n, ast.For) and _iterates_constant(n.iter) for n in ast.walk(tree))
    assert not _imports_scope(tree)


# ── exported constants == the OLD literals, element for element ───────────────────────────────────────────────────────

@pytest.mark.parametrize("modname,expected", [
    ("ga_writers.ga_ayurdaya_writer", OLD_ALT_ORDER),
    ("ga_writers.ga_medical_writer", OLD_ALT_ORDER),
    ("ga_writers.ga_sensitive_degree_writer", OLD_ALT_ORDER),
    ("ga_writers.ga_prashna_writer", FIVE),
    ("ga_writers.ga_yoga_writer", FIVE),
    ("ga_writers.ga_panchanga_writer", FIVE),
    ("ga_writers.ga_sade_sati_writer", FIVE),
])
def test_list_constants_equal_the_old_literal_in_the_old_order(modname, expected):
    mod = _import_or_skip(modname)
    assert isinstance(mod.CANONICAL_AYANAMSHAS, list)
    assert mod.CANONICAL_AYANAMSHAS == expected


def test_dashas_default_constant_is_the_old_list():
    dw = _import_or_skip("ga_writers.ga_dashas_writer")
    assert isinstance(dw.AYANAMSHAS, list) and dw.AYANAMSHAS == FIVE


@pytest.mark.parametrize("modname", ["ga_writers.ga_positions_writer", "ga_writers.ga_tajaka_writer"])
def test_adapter_id_maps_equal_the_old_dict_in_the_old_order(modname):
    mod = _import_or_skip(modname)
    assert list(mod.CANONICAL_AYANAMSHAS.items()) == list(OLD_ADAPTER_MAP.items())


def test_verifier_id_set_and_swisseph_table_are_unchanged():
    v = _import_or_skip("ga_writers._positions_independent_verifier")
    assert list(v._CANONICAL_AYANAMSHAS) == FIVE

    class _Swe:                                   # distinct sentinel per constant: the id -> constant pairing is pinned id by id
        SIDM_LAHIRI, SIDM_TRUE_CITRA, SIDM_KRISHNAMURTI, SIDM_RAMAN, SIDM_SURYASIDDHANTA = 1, 27, 5, 3, 21

    assert {i: v._sidm(_Swe, i) for i in FIVE} == {
        "lahiri_chitrapaksha": 1, "true_chitra": 27, "krishnamurti": 5, "raman": 3, "surya_siddhanta_classical": 21,
    }
    assert v._sidm(_Swe, "not_an_ayanamsha") is None


# ── behaviour: ga_positions (scope seam) ──────────────────────────────────────────────────────────────────────────────

def test_positions_items_default_is_the_old_dict_items():
    pw = _import_or_skip("ga_writers.ga_positions_writer")
    assert pw._ayanamsha_items(FakeConn(), CHART) == list(OLD_ADAPTER_MAP.items())


def test_positions_items_follow_a_configured_subset_in_canonical_order():
    pw = _import_or_skip("ga_writers.ga_positions_writer")
    items = pw._ayanamsha_items(FakeConn(["surya_siddhanta_classical", "lahiri_chitrapaksha"]), CHART)
    assert items == [("lahiri_chitrapaksha", "lahiri"), ("surya_siddhanta_classical", "surya_siddhanta")]
    assert pw._ayanamsha_items(FakeConn(["raman"]), CHART) == [("raman", "raman")]


# ── SS N-311 golden gate: ga_positions / ga_dashas rows for the DEFAULT set are byte-identical to the base commit ─────

def _digest(blocks) -> str:
    """sha256 over a canonical serialisation of (key, rows) blocks. `computed_at` is a wall-clock stamp (not part of the
    derivation) and is left out; everything else is serialised with sorted keys."""
    h = hashlib.sha256()
    for key, rows in blocks:
        h.update(json.dumps(key, default=str).encode())
        for r in rows:
            r = {k: v for k, v in r.items() if k != "computed_at"}
            h.update(json.dumps(r, sort_keys=True, default=str, separators=(",", ":")).encode())
            h.update(b"\n")
    return h.hexdigest()


_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def _fixture_chart_output(i: int) -> dict:
    grahas = []
    for k, n in enumerate(_GRAHAS):
        lon = (37.5 * (k + 1) + 0.37 * i) % 360
        grahas.append({
            "name": n, "longitude_deg": lon, "sign": "Aries", "sign_lord": "Mars", "nakshatra": "Ashwini",
            "nakshatra_lord": "Ketu", "pada": (k % 4) + 1, "house": (k % 12) + 1, "retrograde": k % 3 == 0,
            "combust": k == 3, "degree_in_sign": lon % 30, "sign_id": int(lon // 30) + 1,
        })
    asc = {"longitude_deg": 12.34 + i, "sign": "Aries", "sign_lord": "Mars", "nakshatra": "Ashwini", "pada": 2,
           "sign_id": 1, "degree_in_sign": 12.34 + i}
    cusps = [{"house": h, "start": (30 * (h - 1) + i) % 360.0, "madhya": (30 * (h - 1) + 15 + i) % 360.0,
              "end": (30 * h + i) % 360.0} for h in range(1, 13)]
    gc = {n: {"chalit_house": (k % 12) + 1, "whole_sign_house": (k % 12) + 1, "dist_to_madhya_deg": 3.5 + k,
              "dist_to_nearest_boundary_deg": 1.25 + k, "nearest_boundary": "start" if k % 2 else "end",
              "sandhi_flag": k % 4 == 0, "sandhi_reasons": ["orb"] if k % 4 == 0 else []}
          for k, n in enumerate(_GRAHAS)}
    return {"grahas": grahas, "ascendant": asc,
            "bhava_chalit": {"sripati": {"cusps": cusps}, "placidus": {"cusps": cusps}, "graha_chalit": gc}}


def _positions_digest(pw, items) -> str:
    """The rows build_ga_positions would hand to its second calculation / insert, for the (canonical, adapter) pairs `items`:
    the writer's own pure row builders over a fixed engine-free chart output (varied per ayanamsha, keyed by the id)."""
    blocks = []
    for canonical_id, adapter_id in items:
        co = _fixture_chart_output(FIVE.index(canonical_id))
        rows = pw._build_position_rows(co, "chart-golden", "build-golden", canonical_id, adapter_id, "2026-01-01T00:00:00+00:00")
        rows.extend(pw._build_chalit_rows(co, "chart-golden", "build-golden", canonical_id, "2026-01-01T00:00:00+00:00"))
        blocks.append(((canonical_id, adapter_id), rows))
    return _digest(blocks)


# Computed by running the code at the B0 base commit (suvarna/ayanamsha-scope @ 2cc2a77e3): the loop
# `for canonical_id, adapter_id in CANONICAL_AYANAMSHAS.items()` over this same fixture. 1205 rows.
GOLDEN_POSITIONS_DEFAULT = "cdac296b85157e29da268b53e56bd97f314ddfefc2a99e70c6cc2069b957132b"


def test_positions_default_rows_are_byte_identical_to_the_base_commit(monkeypatch):
    pw = _import_or_skip("ga_writers.ga_positions_writer")
    monkeypatch.setattr(pw, "ENGINE_VERSION", "golden-engine")
    assert _positions_digest(pw, pw._ayanamsha_items(FakeConn(), CHART)) == GOLDEN_POSITIONS_DEFAULT


def test_positions_golden_fails_when_an_ayanamsha_is_dropped(monkeypatch):
    pw = _import_or_skip("ga_writers.ga_positions_writer")
    monkeypatch.setattr(pw, "ENGINE_VERSION", "golden-engine")
    # a configured four-ayanamsha scope drops raman ...
    four = [a for a in FIVE if a != "raman"]
    assert _positions_digest(pw, pw._ayanamsha_items(FakeConn(four), CHART)) != GOLDEN_POSITIONS_DEFAULT
    # ... and so does a regression inside the helper wiring (the writer dropping the last id of the default)
    monkeypatch.setattr(pw, "ayanamshas_for_chart", lambda conn, chart_id: FIVE[:-1])
    assert _positions_digest(pw, pw._ayanamsha_items(FakeConn(), CHART)) != GOLDEN_POSITIONS_DEFAULT


_MOON = {"lahiri_chitrapaksha": 323.7421, "true_chitra": 323.7439, "krishnamurti": 323.7188, "raman": 323.9217,
         "surya_siddhanta_classical": 323.0304}
_BIRTH_JD = 2445736.9
_ROLES = {"Moon": "AK", "Saturn": "AmK", "Sun": "BK", "Venus": "MK", "Mars": "PiK", "Rahu": "PK", "Jupiter": "GK", "Mercury": "DK"}


def _dashas_digest(dw, ayanamshas) -> str:
    """Vimshottari (+ KP sub-periods) and naisargika rows for each ayanamsha, through the writer's own pure compute_*
    functions and the same sandhi / stable-uuid post-passes build_system applies (no DB, no engine call)."""
    blocks = []
    saved = dict(dw._KARAKA_ROLE_CACHE)
    try:
        for aya in ayanamshas:
            dw.set_karaka_roles("chart-golden", aya, _ROLES)
            moon = _MOON[aya]
            vim = dw.compute_vimshottari(moon, _BIRTH_JD, aya, "chart-golden", "build-golden")
            vim = vim + dw.compute_kp_subperiods(vim, "chart-golden", "build-golden", aya)
            nai = dw.compute_naisargika_system(_BIRTH_JD, aya, "chart-golden", "build-golden")
            for sysid, rows in (("vimshottari", vim), ("naisargika", nai)):
                dw.compute_sandhi_post_pass(rows)
                dw.stabilize_hierarchical_uuids(
                    rows, id_field="dasha_row_id", parent_field="parent_row_id",
                    identity_fields=("chart_id", "ayanamsha_id", "system_id", "level_n", "lord_graha", "start_iso", "end_iso",
                                     "kp_sublevel", "kp_sub_lord", "kp_sub_sub_lord"),
                    kind="dasha_interval")
                blocks.append(((aya, sysid), rows))
    finally:
        dw._KARAKA_ROLE_CACHE.clear()
        dw._KARAKA_ROLE_CACHE.update(saved)
    return _digest(blocks)


# Computed by running the code at the B0 base commit over `for aya in AYANAMSHAS` (the old default). 74430 rows.
GOLDEN_DASHAS_DEFAULT = "4069629fe477693abc489cd6779ab7cbecb5728619f7035c1c93df2d5e168e73"


@contextlib.contextmanager
def _fake_dashas_conn(configured=None):
    yield FakeConn(configured)


def test_dashas_default_rows_are_byte_identical_to_the_base_commit(monkeypatch):
    dw = _import_or_skip("ga_writers.ga_dashas_writer")
    monkeypatch.setattr(dw, "_conn", lambda: _fake_dashas_conn())
    ayas = dw._ayanamshas_in_scope(CHART, skip_db=False)
    assert ayas == FIVE
    assert _dashas_digest(dw, ayas) == GOLDEN_DASHAS_DEFAULT
    # in-memory mode has no connection to ask: the default set
    assert dw._ayanamshas_in_scope(CHART, skip_db=True) == FIVE


def test_dashas_golden_fails_when_an_ayanamsha_is_dropped(monkeypatch):
    dw = _import_or_skip("ga_writers.ga_dashas_writer")
    four = [a for a in FIVE if a != "krishnamurti"]
    monkeypatch.setattr(dw, "_conn", lambda: _fake_dashas_conn(four))
    ayas = dw._ayanamshas_in_scope(CHART, skip_db=False)
    assert ayas == four
    assert _dashas_digest(dw, ayas) != GOLDEN_DASHAS_DEFAULT


def test_build_ga_dashas_without_explicit_ayanamshas_uses_the_chart_scope(monkeypatch):
    dw = _import_or_skip("ga_writers.ga_dashas_writer")
    monkeypatch.setattr(dw, "_conn", lambda: _fake_dashas_conn(["raman", "true_chitra"]))
    seen = []
    monkeypatch.setattr(dw, "build_system", lambda sys_, aya, *a, **k: seen.append((sys_, aya)) or {"rows_computed": 0})
    monkeypatch.setattr(dw, "write_dasha_scope_cap_sentinels", lambda *a, **k: 0)
    monkeypatch.setattr(dw, "_run_concurrency_post_pass_db", lambda *a, **k: None)
    dw.build_ga_dashas(CHART, "b", systems=["yogini"], skip_db=False)
    assert [a for _, a in seen] == ["true_chitra", "raman"]
    seen.clear()
    dw.build_ga_dashas(CHART, "b", systems=["yogini"], ayanamshas=["raman"], skip_db=True)     # explicit subset wins, unchanged
    assert [a for _, a in seen] == ["raman"]


# ── behaviour: the build loops take the chart's set ───────────────────────────────────────────────────────────────────

def test_tajaka_builds_the_default_five_in_the_old_order_and_a_configured_subset(monkeypatch):
    tw = _import_or_skip("ga_writers.ga_tajaka_writer")
    adapters = []

    def _compute_chart(inputs, ayanamsha_id):
        adapters.append(ayanamsha_id)
        return {"grahas": [{"name": "Sun", "longitude": 10.0}]}

    def _compute_one(conn, chart_id, canonical_aya, aya_adapter, v, natal, natal_sun, bid, birth=None):
        return {"verification_pass_status": "single", "ephemeris_audit_jsonb": {}, "_muntha_sign": "x",
                "_muntha_house_from_natal": 1, "_muntha_lord": "y", "canonical": canonical_aya}

    monkeypatch.setattr(tw, "compute_chart", _compute_chart)
    monkeypatch.setattr(tw, "_compute_one", _compute_one)
    monkeypatch.setattr(tw, "resolve_birth_params", lambda cid, bp: {"datetime_iso": "1984-02-05T10:43:00"})
    monkeypatch.setattr(tw, "replace_prior_tajik_varsha", lambda conn, rows: 0)
    monkeypatch.setattr(tw, "_insert_rows", lambda conn, rows: len(rows))

    out = tw.build_ga_tajaka(CHART, "b", conn=FakeConn(), reference_year=1985, min_varsha=1, max_varsha=1)
    assert out["ayanamshas"] == FIVE
    assert list(out["per_ayanamsha_counts"]) == FIVE
    assert adapters == ["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"]

    adapters.clear()
    out = tw.build_ga_tajaka(CHART, "b", conn=FakeConn(["krishnamurti", "lahiri_chitrapaksha"]), reference_year=1985,
                             min_varsha=1, max_varsha=1)
    assert out["ayanamshas"] == ["lahiri_chitrapaksha", "krishnamurti"] and adapters == ["lahiri", "kp"]

    adapters.clear()                                                     # an explicit caller subset still wins
    out = tw.build_ga_tajaka(CHART, "b", conn=FakeConn(["raman"]), reference_year=1985, min_varsha=1, max_varsha=1,
                             ayanamshas=["true_chitra"])
    assert out["ayanamshas"] == ["true_chitra"] and adapters == ["true_chitra"]


def test_sensitive_builds_the_default_five_and_a_configured_subset(monkeypatch):
    sw = _import_or_skip("ga_writers.ga_sensitive_writer")
    built = []
    monkeypatch.setattr(sw, "compute_chart", lambda inputs, ayanamsha_id: {"grahas": []})
    monkeypatch.setattr(sw, "check_prerequisites", lambda: {"G14_SAHAM": True, "G44_NADI": True, "G41_LAL_KITAB": True})
    monkeypatch.setattr(sw, "_load_l0_refs", lambda conn: None)
    monkeypatch.setattr(sw, "_insert_rows", lambda conn, rows, commit=False: 0)
    monkeypatch.setattr(sw, "_refresh_mv", lambda conn, commit=False: "ok")

    def _build(*, ayanamsha_key, ayanamsha_id, **kw):
        built.append((ayanamsha_key, ayanamsha_id))
        return []

    monkeypatch.setattr(sw, "_build_all_sensitive_rows_for_ayanamsha", _build)
    out = sw.build_ga_sensitive(CHART, "b", conn=FakeConn(), birth_params={"x": 1})
    assert built == list(OLD_ADAPTER_MAP.items()) and list(out["ayanamshas"]) == list(OLD_ADAPTER_MAP.values())

    built.clear()
    sw.build_ga_sensitive(CHART, "b", conn=FakeConn(["surya_siddhanta_classical", "true_chitra"]), birth_params={"x": 1})
    assert built == [("true_chitra", "true_chitra"), ("surya_siddhanta_classical", "surya_siddhanta")]


def test_sade_sati_loops_the_chart_set(monkeypatch, caplog):
    ss = _import_or_skip("ga_writers.ga_sade_sati_writer")
    monkeypatch.setattr(ss, "_verify_upstream_rows", lambda conn, cid: {"ga3": True})
    monkeypatch.setattr(ss, "_read_moon_sign_per_ayanamsha", lambda conn, cid: {})      # every pass logs "unavailable" and skips
    monkeypatch.setattr(ss, "_read_moon_pada_per_ayanamsha", lambda conn, cid: {})
    monkeypatch.setattr(ss, "_detect_saturn_sign_changes", lambda a, b: [])
    monkeypatch.setattr(ss, "_detect_saturn_retrogrades", lambda a, b: [])
    monkeypatch.setattr(ss, "_refresh_mv", lambda conn: "ok")

    def _visited():
        key = "Moon sign unavailable for ayanamsha "
        return [r.getMessage().split(key)[1].split(",")[0] for r in caplog.records if key in r.getMessage()]

    with caplog.at_level(logging.WARNING, logger=ss.logger.name):
        ss.build_ga_sade_sati(CHART, "b", conn=FakeConn())
        assert _visited() == FIVE
        caplog.clear()
        ss.build_ga_sade_sati(CHART, "b", conn=FakeConn(["raman", "lahiri_chitrapaksha"]))
        assert _visited() == ["lahiri_chitrapaksha", "raman"]


class _Stop(Exception):
    pass


def _first_engine_call(module, monkeypatch, call_builder, expect_adapter_first, configured):
    """Heavy per-ayanamsha loops (strength, structural): stop at the first compute_chart and report which adapter id came
    first plus what the helper was asked. The loop head is the only thing this changes."""
    asked, first = [], []
    real = scope.ayanamshas_for_chart

    def _spy(conn, chart_id):
        asked.append((type(conn).__name__, str(chart_id)))
        return real(conn, chart_id)

    def _compute_chart(*, inputs, ayanamsha_id):
        first.append(ayanamsha_id)
        raise _Stop

    monkeypatch.setattr(scope, "ayanamshas_for_chart", _spy)         # these two builders import it function-locally
    monkeypatch.setattr(module, "compute_chart", _compute_chart)
    monkeypatch.setattr(module, "resolve_birth_params", lambda cid, bp: {"x": 1})
    with pytest.raises(_Stop):
        call_builder(FakeConn(configured))
    assert asked == [("FakeConn", CHART)]
    assert first == [expect_adapter_first]


@pytest.mark.parametrize("configured,first", [(None, "lahiri"), (["surya_siddhanta_classical", "krishnamurti"], "kp")])
def test_strength_loop_starts_at_the_first_ayanamsha_of_the_chart_set(monkeypatch, configured, first):
    sw = _import_or_skip("ga_writers.ga_strength_writer")
    _first_engine_call(sw, monkeypatch, lambda c: sw.build_ga_strength(CHART, "b", conn=c, birth_params={"x": 1}), first, configured)


@pytest.mark.parametrize("configured,first", [(None, "lahiri"), (["surya_siddhanta_classical", "krishnamurti"], "kp")])
def test_structural_loop_starts_at_the_first_ayanamsha_of_the_chart_set(monkeypatch, configured, first):
    st = _import_or_skip("ga_writers.ga_structural_writer")
    monkeypatch.setattr(st, "_load_yoga_catalog", lambda conn: [])
    monkeypatch.setattr(st, "_load_dosha_catalog", lambda conn: [])
    _first_engine_call(st, monkeypatch,
                       lambda c: st.build_ga_structural(CHART, "b", conn=c, birth_params={"x": 1}, skip_upstream_check=True),
                       first, configured)


def test_panchanga_moon_sign_read_is_scoped_to_the_chart_set():
    pg = _import_or_skip("ga_writers.ga_panchanga_writer")
    seen = []

    class _Conn(FakeConn):
        def execute(self, sql, params=None):
            seen.append(params)

            class _R:
                def fetchall(self_inner):
                    return []
            return _R()

    assert pg._read_birth_moon_signs(_Conn(), CHART) == {}
    assert seen[-1] == [CHART, FIVE]
    assert pg._read_birth_moon_signs(_Conn(["true_chitra", "raman"]), CHART) == {}
    assert seen[-1] == [CHART, ["true_chitra", "raman"]]


def test_panchanga_build_asks_the_helper_on_both_connection_paths():
    assert len(_calls(_tree("ga_writers/ga_panchanga_writer.py"), "ayanamshas_for_chart")) == 3   # moon-sign read + owns_conn + injected


def _vargas_run(vw, monkeypatch, configured, subsets):
    rows_written, vis = [], []
    monkeypatch.setattr(vw, "_compute_varga_positions", lambda jd, aya, lat, lon, tz: ({"D1": {}}, []))
    monkeypatch.setattr(vw, "forensic_gate_vargas", lambda all_vargas, aya: {"result": "PASS", "findings": []})
    monkeypatch.setattr(vw, "assert_unique_key_grain", lambda conn: None)
    monkeypatch.setattr(vw, "_read_jaimini_karakas", lambda conn, cid, aya: {})
    monkeypatch.setattr(vw, "_check_already_written", lambda *a, **k: False)
    monkeypatch.setattr(vw, "_build_d30_lord_per_amsa_rows", lambda *a, **k: [])
    monkeypatch.setattr(vw, "_build_cross_varga_harmonic_rows", lambda *a, **k: [])
    monkeypatch.setattr(vw, "VARGA_BATCHES", [])

    def _write(conn, rows, cleared=None, stats=None):
        rows_written.extend((r["ayanamsha_id"], r["fact_subject"]) for r in rows)
        return len(rows)

    monkeypatch.setattr(vw, "_write_rows_batch", _write)
    bp = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.3, "longitude_deg": 85.8, "tz_offset_hours": 5.5}
    conn = FakeConn(configured)
    conn.execute = lambda sql, params=None: vis.append(sql)
    for sub in subsets:
        vw.build_ga_vargas(CHART, "b", conn=conn, birth_params=bp, ayanamsha_subset=sub)
    return rows_written, vis


def test_vargas_sentinels_belong_to_the_first_ayanamsha_of_the_chart_set(monkeypatch):
    vw = _import_or_skip("ga_writers.ga_vargas_writer")
    # default chart, driven the way the orchestrator drives it (one ayanamsha per sub-step): sentinels only on lahiri
    rows, _ = _vargas_run(vw, monkeypatch, None, [[a] for a in FIVE])
    assert rows and {a for a, _ in rows} == {"INVARIANT"} and len(rows) == 6          # D81 + 5 floored bodies, once
    # a chart whose set excludes lahiri: the sentinels move to its FIRST ayanamsha (they used to vanish)
    rows2, _ = _vargas_run(vw, monkeypatch, ["raman", "surya_siddhanta_classical"], [["raman"], ["surya_siddhanta_classical"]])
    assert len(rows2) == 6
    rows3, _ = _vargas_run(vw, monkeypatch, ["raman", "surya_siddhanta_classical"], [["surya_siddhanta_classical"]])
    assert rows3 == []                                                                  # not the first of this chart's set


def test_vargas_without_a_subset_runs_the_chart_set(monkeypatch):
    vw = _import_or_skip("ga_writers.ga_vargas_writer")
    ran = []
    monkeypatch.setattr(vw, "_compute_varga_positions", lambda jd, aya, lat, lon, tz: ran.append(aya) or (_ for _ in ()).throw(_Stop()))
    bp = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.3, "longitude_deg": 85.8, "tz_offset_hours": 5.5}
    with pytest.raises(_Stop):
        vw.build_ga_vargas(CHART, "b", conn=FakeConn(["krishnamurti", "raman"]), birth_params=bp)
    assert ran == ["krishnamurti"]
