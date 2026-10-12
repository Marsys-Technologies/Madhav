"""
tests/l1/test_n350_sensitive_divergence_not_measured.py
=======================================================

SS N-341/N-347 "item 1" (CLAUDE.md N.8 Earned-Signal Principle: an honest NULL beats an
invented value).

`chart_facts.cross_ayanamsha_divergence_arcsec` is meant to hold the MEASURED spread of a
sensitive point across the five ayanamshas. `ga_sensitive_writer.py` never measures it (each
row is built for one ayanamsha at a time), yet it used to default the column to 0.0 and
hard-code 0.0 at six sites. A stored 0.0 reads as "measured zero" -> a false green. The
writer now emits None (stored NULL), matching `ga_vargas_writer.py`.

Two layers (no DB, no PyJHora needed):

  (a) BEHAVIOURAL - build real rows through the writer's row builders for every category
      that used to hard-code the column (karaka_chara_position, kp_cuspal_significators in
      all three of its paths, tajik_hadda_lord, nakshatra_pada_sensitive) plus the two
      shared defaults (`_make_row`, `_long_rows`) and a spread of `_long_rows` consumers.
      The column must be present as a key and be None on every row.

  (b) SOURCE GUARD - parse ga_sensitive_writer.py with `ast` and fail if any keyword
      argument, dict entry, subscript store or parameter default named
      `cross_ayanamsha_divergence_arcsec` is the numeric constant 0 / 0.0. The detector is
      itself proven against synthetic snippets, so a green here cannot be vacuous.

Both layers fail if the 0.0 comes back.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import sys
from typing import Any

import pytest

# Add the sidecar root (parent of tests/) to path so `ga_writers` imports, same style as
# tests/test_ga5_writer.py.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

COLUMN = "cross_ayanamsha_divergence_arcsec"
WRITER_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent / "ga_writers" / "ga_sensitive_writer.py"
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYA_ID = "lahiri_chitrapaksha"
BUILD_ID = "test-build-n350"
ENG_VER = "test-eng"

_LONGS: dict[str, float] = {
    "SUN": 280.0,
    "MOON": 321.0,
    "MAR": 195.0,
    "MER": 275.0,
    "JUP": 120.0,
    "VEN": 300.0,
    "SAT": 210.0,
    "RAH_MEAN": 180.0,
    "KET_MEAN": 0.0,
    "LAGNA": 5.0,
}


def _writer():
    from ga_writers import ga_sensitive_writer
    return ga_sensitive_writer


# ── (a) behavioural ───────────────────────────────────────────────────────────

def _assert_all_none(rows: list[dict[str, Any]], what: str) -> None:
    assert rows, f"{what}: builder returned no rows - test would be vacuous"
    for r in rows:
        where = f"{what}: {r.get('fact_category')}.{r.get('fact_subject')}.{r.get('fact_key')}"
        # Key must be present (the INSERT reads row.get(...); absent would also bind NULL, but
        # the writer contract is an explicit key).
        assert COLUMN in r, f"{where} lacks {COLUMN}"
        assert r[COLUMN] is None, (
            f"{where} stores {COLUMN}={r[COLUMN]!r}; nothing measures a cross-ayanamsha "
            "spread, so it must be None (NULL), never a 0.0 that reads as 'measured zero'"
        )


def test_make_row_default_is_none():
    w = _writer()
    row = w._make_row(
        "upagraha_position", "DHUMA", "longitude_sidereal",
        10.0, None, None, CHART_ID, AYA_ID, BUILD_ID, ENG_VER,
    )
    _assert_all_none([row], "_make_row default")


def test_make_row_param_default_is_none_signature():
    w = _writer()
    default = inspect.signature(w._make_row).parameters[COLUMN].default
    assert default is None, f"_make_row default for {COLUMN} is {default!r}"


def test_long_rows_param_default_is_none_signature():
    w = _writer()
    default = inspect.signature(w._long_rows).parameters[COLUMN].default
    assert default is None, f"_long_rows default for {COLUMN} is {default!r}"


def test_long_rows_default_rows_are_none():
    w = _writer()
    rows = w._long_rows(
        "esoteric_point_yogi", "YOGI_POINT", 123.456,
        CHART_ID, AYA_ID, BUILD_ID, ENG_VER, _LONGS["LAGNA"],
    )
    _assert_all_none(rows, "_long_rows default")


def test_long_rows_does_not_coerce_none_to_zero():
    """An explicit None passed through _long_rows must reach every row unchanged."""
    w = _writer()
    rows = w._long_rows(
        "esoteric_point_yogi", "YOGI_POINT", 123.456,
        CHART_ID, AYA_ID, BUILD_ID, ENG_VER, _LONGS["LAGNA"],
        cross_ayanamsha_divergence_arcsec=None,
    )
    _assert_all_none(rows, "_long_rows explicit None")


def test_explicit_measured_value_still_passes_through():
    """The plumbing is intact: a caller that really measured a spread can still set it."""
    w = _writer()
    row = w._make_row(
        "upagraha_position", "DHUMA", "longitude_sidereal",
        10.0, None, None, CHART_ID, AYA_ID, BUILD_ID, ENG_VER,
        cross_ayanamsha_divergence_arcsec=2.5,
    )
    assert row[COLUMN] == 2.5


def test_karaka_chara_rows_are_none():
    """Former hard-coded site: _build_karaka_rows b_kwargs."""
    w = _writer()
    rows = w._build_karaka_rows(_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, "HALT.md")
    cats = {r["fact_category"] for r in rows}
    assert "karaka_chara_position" in cats
    _assert_all_none(rows, "_build_karaka_rows")


def test_tajik_hadda_rows_are_none():
    """Former hard-coded site: _build_hadda_rows b_kwargs."""
    w = _writer()
    rows = w._build_hadda_rows(_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)
    assert {r["fact_category"] for r in rows} == {"tajik_hadda_lord"}
    _assert_all_none(rows, "_build_hadda_rows")


def test_nakshatra_pada_sensitive_rows_are_none():
    """Former hard-coded site: _build_nakshatra_pada_sensitive_rows b_kwargs."""
    w = _writer()
    rows = w._build_nakshatra_pada_sensitive_rows(_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)
    assert {r["fact_category"] for r in rows} == {"nakshatra_pada_sensitive"}
    _assert_all_none(rows, "_build_nakshatra_pada_sensitive_rows")


def test_kp_cuspal_floor_rows_are_none():
    """Former hard-coded site: EXTERNAL_COMPUTATION_REQUIRED skip-rows (no Placidus cusps)."""
    w = _writer()
    rows = w._build_kp_cuspal_rows(_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, {})
    assert len(rows) == 12
    assert {r["verification_pass_status"] for r in rows} == {w.EXTERNAL_COMPUTATION_REQUIRED}
    _assert_all_none(rows, "_build_kp_cuspal_rows floor path")


def test_kp_cuspal_real_cusp_rows_are_none():
    """Former hard-coded site: per-cusp b_kwargs when Placidus cusps are supplied."""
    w = _writer()
    chart_data = {
        "bhava_chalit": {
            "placidus": {"cusp_boundaries": [5.0 + 30.0 * i + 1.7 * i for i in range(12)]}
        }
    }
    rows = w._build_kp_cuspal_rows(_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, chart_data)
    assert {r["fact_key"] for r in rows} >= {
        "sign_lord", "star_lord", "sub_lord", "cusp_longitude_sidereal", "significators_json",
    }
    assert len(rows) == 12 * 5
    _assert_all_none(rows, "_build_kp_cuspal_rows real-cusp path")


def test_kp_cuspal_parse_error_rows_are_none():
    """Former hard-coded site: KP_PARSE_ERROR skip-rows (a malformed cusp boundary)."""
    w = _writer()
    bounds: list[Any] = [5.0 + 30.0 * i for i in range(12)]
    bounds[3] = "not-a-number"
    chart_data = {"bhava_chalit": {"placidus": {"cusp_boundaries": bounds}}}
    rows = w._build_kp_cuspal_rows(_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, chart_data)
    err = [r for r in rows if r["verification_pass_status"] == w.SKIPPED_MALFORMED_SOURCE]
    assert len(err) == 1, "expected exactly the one malformed cusp to become a parse-error row"
    assert err[0]["fact_value_text"].startswith("KP_PARSE_ERROR")
    _assert_all_none(rows, "_build_kp_cuspal_rows parse-error path")


@pytest.mark.parametrize(
    "builder_name,args",
    [
        ("_build_bhrigu_bindu_rows", (_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)),
        ("_build_yogi_avayogi_rows", (_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)),
        ("_build_swamsa_rows", (_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)),
        ("_build_arudha_rows", (_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)),
        ("_build_karakamsa_rows", (_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)),
    ],
)
def test_long_rows_consumers_are_none(builder_name, args):
    """Builders that rely on the _long_rows default (formerly 0.0) now emit None."""
    w = _writer()
    rows = getattr(w, builder_name)(*args)
    _assert_all_none(rows, builder_name)


# ── (b) source guard ──────────────────────────────────────────────────────────

def _is_numeric_zero(node: ast.AST | None) -> bool:
    """True for the literal 0 / 0.0 (bool excluded; a unary +/- applied to zero counts)."""
    if node is None:
        return False
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return _is_numeric_zero(node.operand)
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
        and node.value == 0
    )


def _is_none(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def scan_divergence_sites(source: str) -> tuple[list[str], list[str]]:
    """Return (zero_sites, none_sites) for COLUMN in `source`.

    Sites inspected: keyword arguments, dict-literal entries, parameter defaults (positional
    and keyword-only) and subscript stores `x["cross_ayanamsha_divergence_arcsec"] = ...`.
    """
    tree = ast.parse(source)
    zero: list[str] = []
    none: list[str] = []

    def record(node: ast.AST | None, label: str, lineno: int) -> None:
        if _is_numeric_zero(node):
            zero.append(f"line {lineno}: {label} = numeric zero")
        elif _is_none(node):
            none.append(f"line {lineno}: {label} = None")

    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == COLUMN:
            record(node.value, f"keyword {COLUMN}", node.value.lineno)
        elif isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == COLUMN:
                    record(v, f'dict entry "{COLUMN}"', v.lineno)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = node.args
            pos = a.posonlyargs + a.args
            for arg, default in zip(pos[len(pos) - len(a.defaults):], a.defaults):
                if arg.arg == COLUMN:
                    record(default, f"parameter default {COLUMN}", default.lineno)
            for arg, default in zip(a.kwonlyargs, a.kw_defaults):
                if arg.arg == COLUMN and default is not None:
                    record(default, f"keyword-only default {COLUMN}", default.lineno)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if (
                    isinstance(t, ast.Subscript)
                    and isinstance(t.slice, ast.Constant)
                    and t.slice.value == COLUMN
                    and node.value is not None
                ):
                    record(node.value, f'subscript store ["{COLUMN}"]', node.value.lineno)
    return zero, none


def test_source_guard_detector_catches_each_form():
    """The guard must not be vacuous: prove it fires on every shape of the old defect."""
    snippets = {
        "keyword": f"f(x, {COLUMN}=0.0)",
        "keyword int": f"f(x, {COLUMN}=0)",
        "dict entry": f'row = {{"{COLUMN}": 0.0}}',
        "positional default": f"def g(a, {COLUMN}: float = 0.0): pass",
        "kw-only default": f"def g(a, *, {COLUMN}: float = 0.0): pass",
        "subscript store": f'row["{COLUMN}"] = 0.0',
        "negative zero": f"f({COLUMN}=-0.0)",
    }
    for label, src in snippets.items():
        zero, _ = scan_divergence_sites(src)
        assert len(zero) == 1, f"detector missed the {label} form: {src}"

    for label, src in {
        "keyword None": f"f({COLUMN}=None)",
        "dict None": f'row = {{"{COLUMN}": None}}',
        "default None": f"def g(a, {COLUMN}: float | None = None): pass",
        "variable passthrough": f"f({COLUMN}={COLUMN})",
        "measured value": f"f({COLUMN}=2.5)",
    }.items():
        zero, _ = scan_divergence_sites(src)
        assert zero == [], f"detector false-positive on {label}: {src}"


def test_ga_sensitive_writer_has_no_zero_divergence_constant():
    source = WRITER_PATH.read_text(encoding="utf-8")
    zero_sites, _ = scan_divergence_sites(source)
    assert not zero_sites, (
        f"{WRITER_PATH.name} hard-codes a numeric zero for {COLUMN} - a stored 0.0 reads as "
        "'measured zero' though nothing measures it (CLAUDE.md N.8). Use None.\n  "
        + "\n  ".join(zero_sites)
    )


def test_ga_sensitive_writer_guard_is_not_vacuous():
    """The writer must still name the column in the places the guard is meant to watch:
    both parameter defaults and the six former hard-coded sites, all explicit None."""
    source = WRITER_PATH.read_text(encoding="utf-8")
    _, none_sites = scan_divergence_sites(source)
    # 2 parameter defaults (_make_row, _long_rows) + 6 former hard-coded literal sites.
    assert len(none_sites) >= 8, (
        f"expected >= 8 explicit-None sites for {COLUMN}, found {len(none_sites)}: {none_sites}"
    )


def test_ga_sensitive_writer_insert_still_names_the_column():
    """The INSERT must keep naming the column (so the DB default 0.0 cannot fill it)."""
    source = WRITER_PATH.read_text(encoding="utf-8")
    assert f"formula_provenance_text, {COLUMN}\n" in source
    assert f'row.get("{COLUMN}")' in source
