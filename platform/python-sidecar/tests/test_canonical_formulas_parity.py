"""test_canonical_formulas_parity.py -- the Python and TS canonical-formula constants must be equal.

The constant is mirrored on purpose (a sibling Python module, because brahmagyan/verification_vocab.py
and l0_reference.py are frozen L0 digests; a TS twin next to the retrieval L1 tools). A mirror with no
parity check is two facts waiting to drift, so this test READS BOTH FILES and asserts equality of
every category, the canonical formula, and every variants list (including order), plus the two
scalar constants. A vitest twin (`canonical_formulas_parity.test.ts`, next to the TS file) does the
same from the other side, so the mirror is checked whichever CI job runs.

The TS table is parsed by a deliberately strict regex (one entry per line, the shape documented in
the TS header); a reformat that the regex cannot read FAILS this test rather than silently skipping.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[3]
PY_PATH = REPO / "platform/python-sidecar/brahmagyan/canonical_formulas.py"
TS_PATH = REPO / "platform/src/lib/retrieval/registry/layers/L1_ganita/canonical_formulas.ts"

_ENTRY = re.compile(
    r"^\s{2}(?P<cat>[a-z_]+):\s*\{\s*canonical:\s*(?P<canon>null|'[^']*'),\s*"
    r"variants:\s*\[(?P<vars>[^\]]*)\]\s*\},?\s*$",
    re.M,
)


def _load_py():
    spec = importlib.util.spec_from_file_location("canonical_formulas_under_test", PY_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ts_table(text: str) -> dict:
    start = text.index("export const CANONICAL_FORMULAS")
    block = text[start : text.index("\n}\n", start)]
    out = {}
    for m in _ENTRY.finditer(block):
        canon = None if m.group("canon") == "null" else m.group("canon").strip("'")
        variants = [v.strip().strip("'") for v in m.group("vars").split(",") if v.strip()]
        out[m.group("cat")] = {"canonical": canon, "variants": variants}
    return out


def _ts_scalar(text: str, name: str) -> str:
    m = re.search(r"export const " + name + r" = '([^']*)'", text)
    assert m, f"{name} not found in the TS mirror"
    return m.group(1)


def test_ts_table_is_parseable_and_non_empty():
    table = _ts_table(TS_PATH.read_text(encoding="utf-8"))
    assert len(table) == 7, f"expected the 7 declared categories, parsed {sorted(table)}"


def test_python_and_ts_tables_are_equal():
    py = _load_py().CANONICAL_FORMULAS
    ts = _ts_table(TS_PATH.read_text(encoding="utf-8"))
    py_norm = {c: {"canonical": v["canonical"], "variants": list(v["variants"])} for c, v in py.items()}
    assert json.dumps(py_norm, sort_keys=True) == json.dumps(ts, sort_keys=True)
    # category ORDER is part of the contract too (it is the disclosure / SQL CASE order)
    assert list(py) == list(ts)


def test_variants_lists_match_exactly_and_in_order():
    py = _load_py().CANONICAL_FORMULAS
    ts = _ts_table(TS_PATH.read_text(encoding="utf-8"))
    for cat in py:
        assert list(py[cat]["variants"]) == ts[cat]["variants"], cat


def test_scalar_constants_match():
    py = _load_py()
    text = TS_PATH.read_text(encoding="utf-8")
    assert py.NO_CANONICAL_FORMULA_REASON == _ts_scalar(text, "NO_CANONICAL_FORMULA_REASON")
    assert py.CANONICAL_FORMULA_STATUS == _ts_scalar(text, "CANONICAL_FORMULA_STATUS")


def test_ssdecision_values_are_what_ss_ruled():
    py = _load_py()
    f = py.CANONICAL_FORMULAS
    # Yogi / Avayogi: bphs_93_20 canonical, alt_96_40 a named variant
    for cat in ("esoteric_point_yogi", "esoteric_point_avayogi"):
        assert f[cat]["canonical"] == "bphs_93_20" and f[cat]["variants"] == ["alt_96_40"]
    # Chara karaka: kn_rao_rahu_included canonical (the existing L1 pin), parashari a named variant
    assert f["karaka_chara_position"]["canonical"] == "kn_rao_rahu_included"
    assert f["karaka_chara_position"]["variants"] == ["parashari_rahu_excluded"]
    assert py.CANONICAL_KARAKA_SCHOOL == "kn_rao_rahu_included"
    # Mrityu: NO canonical; all three served
    assert f["esoteric_point_mrityu"]["canonical"] is None
    assert sorted(f["esoteric_point_mrityu"]["variants"]) == ["bphs_ch39", "saravali", "tajik_aapamrityu"]


def test_canonical_is_never_also_a_variant():
    for cat, spec in _load_py().CANONICAL_FORMULAS.items():
        assert spec["canonical"] not in spec["variants"], cat


def test_python_helpers():
    py = _load_py()
    assert py.canonical_formula_of("esoteric_point_yogi") == "bphs_93_20"
    assert py.canonical_formula_of("esoteric_point_mrityu") is None
    assert py.canonical_formula_of("graha_position") is None
    assert py.all_formulas_of("esoteric_point_yogi") == ["bphs_93_20", "alt_96_40"]
    assert py.all_formulas_of("esoteric_point_mrityu") == ["bphs_ch39", "saravali", "tajik_aapamrityu"]
    assert py.all_formulas_of("graha_position") == []
    assert py.is_multi_formula_category("karaka_chara_position")
    assert not py.is_multi_formula_category("karaka_house_lord_overlap_flag")
