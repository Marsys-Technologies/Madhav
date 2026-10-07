"""TI-laksana-fallbacks-001: bo_laksana must never write a blank piece for a missing value
(CLAUDE.md N.7 item 6 / N.8). Findings of the engine's Null writer scan over bo_laksana.py:
  * `_build_headline_text` location suffix (CR-45 omission rule, now an omission by construction),
  * `_load_vichara_divergence_signals` subject / domain / value_text (`.get(...) or ""`),
  * `_build_signal_row` fact_category / fact_key (`.get(..., "")` on NOT NULL L1 columns).
Behaviour on complete data is pinned byte-for-byte."""
from __future__ import annotations

import json

import pytest

from pipeline.orchestrator.writers import bo_laksana as bo

_NOW = "2026-10-05T00:00:00+00:00"


class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a, **k):
        return None


class _Conn:
    """Minimal psycopg-shaped connection: `execute` returns the chart_vichara rows."""

    def __init__(self, rows):
        self._rows = rows

    def execute(self, sql, params=None):
        return _Cur(self._rows)

    def cursor(self):
        return _Cur([])


def _vrow(**over):
    row = {"subject": "JUPITER", "domain": "wealth",
           "value_text": "JUPITER: D1 exalted vs D9 debilitated — wealth ratification fails in D9",
           "value_num": -1.0, "constituent_facts_array": ["f1", "f2"]}
    row.update(over)
    return row


def _load(rows):
    return bo._load_vichara_divergence_signals(_Conn(rows), "chart-1", "lahiri_chitrapaksha", "b1", _NOW)


# ── divergence loader: rows 2-4 (subject / domain / value_text) ───────────────

def test_complete_divergence_row_is_byte_identical_to_the_pre_fix_output():
    (s,) = _load([_vrow()])
    assert s["signal_type_id"] == "varga_ratification_divergence:JUPITER:wealth"
    assert s["signal_headline_text"] == "JUPITER: D1 exalted vs D9 debilitated — wealth ratification fails in D9"
    assert s["signal_summary_text"] == (
        "category=varga_ratification_divergence | subject=JUPITER | domain=wealth | "
        "value_text=JUPITER: D1 exalted vs D9 debilitated — wealth ratification fails in D9 | value_num=-1.0"
    )
    assert s["citation_human"] == "ga_vichara varga_ratification_divergence: JUPITER in wealth"
    assert s["citation_ref"] == "chart_vichara/JUPITER/wealth"
    assert s["domains_affected_array"] == ["wealth"]
    assert s["domain_salience_jsonb"] == json.dumps({"wealth": 1.2})
    assert json.loads(s["configuration_jsonb"]) == {
        "subject": "JUPITER", "domain": "wealth", "value_text": _vrow()["value_text"]}


@pytest.mark.parametrize("field", ["subject", "domain"])
@pytest.mark.parametrize("blank", [None, "", "   "])
def test_divergence_row_missing_a_natural_key_piece_refuses_loudly_never_writes_blank(field, blank):
    with pytest.raises(ValueError) as ei:
        _load([_vrow(), _vrow(**{field: blank})])
    msg = str(ei.value)
    assert field in msg and "refusing" in msg and "chart-1" in msg


def test_blank_divergence_key_pieces_never_reach_a_signal_even_with_complete_siblings():
    for field in ("subject", "domain"):
        try:
            sigs = _load([_vrow(**{field: None})])
        except ValueError:
            continue
        pytest.fail(f"missing {field} produced signals: {[s['citation_human'] for s in sigs]}")


# ── N-189: a forwarded leaf equals the L1 value (NULL stays NULL, never '') ───

def test_absent_value_text_is_forwarded_as_null_not_empty_string():
    """GOLDEN (N-189): chart_vichara.value_text is nullable and a forwarded leaf; the engine's
    detector compares it strictly with the L1 value, NULL vs '' is DIFFERENT. On main this wrote ''."""
    (s,) = _load([_vrow(value_text=None)])
    cfg = json.loads(s["configuration_jsonb"])
    assert cfg["value_text"] is None, cfg
    assert cfg == {"subject": "JUPITER", "domain": "wealth", "value_text": None}
    # the summary omits the absent clause (as the fact path does): no 'value_text=None', no 'value_text='
    assert s["signal_summary_text"] == (
        "category=varga_ratification_divergence | subject=JUPITER | domain=wealth | value_num=-1.0"
    )
    assert "value_text" not in s["signal_summary_text"]
    assert s["signal_headline_text"] == "JUPITER: divergent varga ratification in wealth"
    assert s["citation_ref"] == "chart_vichara/JUPITER/wealth"


def test_present_value_text_is_forwarded_verbatim():
    (s,) = _load([_vrow(value_text="  odd  spacing ")])
    assert json.loads(s["configuration_jsonb"])["value_text"] == "  odd  spacing "


def test_null_value_text_changes_no_identity_bearing_piece_except_the_null_leaf():
    full = _load([_vrow()])[0]
    null = _load([_vrow(value_text=None)])[0]
    assert full["signal_type_id"] == null["signal_type_id"]
    assert full["citation_ref"] == null["citation_ref"]
    assert full["domains_affected_array"] == null["domains_affected_array"]


# ── fact rows: rows 5-6 (fact_category / fact_key) ────────────────────────────

def _fact(**over):
    f = {"fact_id": "fid-1", "fact_category": "argala_natal_matrix", "fact_key": "k1",
         "fact_subject": "D30_SIGN_10", "fact_value_text": None, "fact_value_num": 1.0,
         "ayanamsha_id": "lahiri_chitrapaksha", "source_calculation": "x", "formula_id": None,
         "fact_value_jsonb": None}
    f.update(over)
    return f


def _row(f):
    return bo._build_signal_row(f, "chart-1", "b1", {}, {}, {}, _NOW, valid_fact_ids={f["fact_id"]})


def test_complete_fact_row_citation_is_unchanged():
    row = _row(_fact())
    assert row["signal_type_id"] == "argala_natal_matrix:k1"
    assert row["citation_human"] == "L1 chart_facts: argala_natal_matrix/k1"


@pytest.mark.parametrize("column", ["fact_category", "fact_key"])
@pytest.mark.parametrize("bad", ["__absent__", None, "", "  "])
def test_fact_row_without_category_or_key_raises_not_a_blank_citation(column, bad):
    f = _fact()
    if bad == "__absent__":
        del f[column]
    else:
        f[column] = bad
    with pytest.raises(ValueError) as ei:
        _row(f)
    assert column in str(ei.value) and "fid-1" in str(ei.value)


# ── headline location suffix: row 1 (CR-45 omission rule) ─────────────────────

@pytest.mark.parametrize("house,varga,expected", [
    (None, None, "SUN: cat: key = 5 [ga_x]"),
    (7, None, "SUN (H7): cat: key = 5 [ga_x]"),
    (None, "D9", "SUN (D9): cat: key = 5 [ga_x]"),
    (7, "D9", "SUN (H7, D9): cat: key = 5 [ga_x]"),
])
def test_headline_location_suffix_is_omitted_not_blanked(house, varga, expected):
    assert bo._build_headline_text("cat", "key", None, 5.0, "ga_x", fact_subject="Sun",
                                   house=house, varga_id=varga) == expected


def test_headline_without_subject_is_the_anonymous_form():
    assert bo._build_headline_text("cat", "key", "v", None, "ga_x") == "cat: key = v [ga_x]"


def test_writer_has_no_empty_string_default_in_the_scanned_paths():
    """The engine's detector reads `.get(k) or ""`, `.get(k, "")` and `... else ""` on these paths as a
    literal fallback; pin their absence in the three functions so it cannot silently return."""
    import ast
    import inspect
    for fn in (bo._build_headline_text, bo._load_vichara_divergence_signals, bo._build_signal_row):
        src = inspect.getsource(fn)
        tree = ast.parse(src.lstrip() if src.startswith(" ") else src)
        for n in ast.walk(tree):
            if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
                for v in n.values[1:]:
                    if isinstance(v, ast.Constant) and v.value == "":
                        # the only tolerated `or ""` in _build_signal_row are the pre-existing, un-scanned
                        # subject / source_calculation / verification reads, none on the three findings
                        assert fn is bo._build_signal_row, f"{fn.__name__}: `or \"\"` default"
            if isinstance(n, ast.IfExp) and isinstance(n.orelse, ast.Constant) and n.orelse.value == "":
                if fn is bo._build_headline_text and "fact_value_num" in ast.unparse(n):
                    # `val = ... else ""` (the value formatter) is a pre-existing, guarded body piece;
                    # the location-suffix `... else ""` (row 1) is NOT tolerated
                    continue
                pytest.fail(f"{fn.__name__}: `... else \"\"`")
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" \
                    and len(n.args) == 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value == "":
                if fn is bo._build_signal_row:
                    key = n.args[0].value if isinstance(n.args[0], ast.Constant) else None
                    assert key not in ("fact_category", "fact_key"), f"`.get({key!r}, \"\")` returned"
