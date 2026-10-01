"""test_canonical_formulas_vs_writer.py -- the canonical-formula constant must name exactly the formula ids
`ga_sensitive_writer.py` actually emits.

The constant (brahmagyan/canonical_formulas.py, mirrored in TS) is only useful if a reader that pins
`formula_id = <canonical>` pins a value the writer really writes. A typo there (or a writer rename) would
make every canonical pin read zero rows. This test reads the WRITER SOURCE and checks the constant against
it, in both directions for the Yogi / Avayogi / Mrityu families (whose formula ids are spelled out in
`(value, "formula_id", "provenance text")` tuples) and by presence for the school-keyed families
(karaka, Brahma / Shiva / Vishnu), whose ids are the two chara-karaka schools.

Source-reading only: no DB, no writer import (the writer pulls heavy deps).
"""
from __future__ import annotations

import importlib.util
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[3]
WRITER = REPO / "platform/python-sidecar/ga_writers/ga_sensitive_writer.py"
CONST = REPO / "platform/python-sidecar/brahmagyan/canonical_formulas.py"


def _const():
    spec = importlib.util.spec_from_file_location("canonical_formulas_vs_writer", CONST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _writer_text() -> str:
    return WRITER.read_text(encoding="utf-8")


def _tuple_formula_ids(text: str, first_marker: str, last_marker: str) -> set:
    """Formula ids from `(value, "formula_id", "provenance")` tuples between two writer markers."""
    start = text.index(first_marker)
    end = text.index(last_marker, start) + len(last_marker)
    return set(re.findall(r'\(\s*\w+\s*,\s*"([a-z0-9_]+)"\s*,\s*"', text[start:end]))


def test_yogi_avayogi_mrityu_ids_in_the_writer_equal_the_constants():
    c = _const().CANONICAL_FORMULAS
    emitted = _tuple_formula_ids(_writer_text(), '(yogi_v1, "bphs_93_20"', '(day birth)"')
    declared = set()
    for cat in ("esoteric_point_yogi", "esoteric_point_avayogi", "esoteric_point_mrityu"):
        declared |= set(_const().all_formulas_of(cat))
    assert emitted == declared, (sorted(emitted), sorted(declared))
    assert c["esoteric_point_yogi"]["canonical"] in emitted


def test_every_declared_formula_id_is_a_quoted_literal_in_the_writer():
    text = _writer_text()
    for cat, spec in _const().CANONICAL_FORMULAS.items():
        for fid in _const().all_formulas_of(cat):
            assert f'"{fid}"' in text, f"{cat}: formula_id {fid!r} is not emitted by ga_sensitive_writer.py"


def test_every_declared_category_is_a_category_the_writer_emits():
    text = _writer_text()
    for cat in _const().CANONICAL_FORMULAS:
        assert f'"{cat}"' in text or f"'{cat}'" in text, f"{cat} is not a category ga_sensitive_writer.py emits"


def test_the_two_chara_karaka_schools_are_exactly_the_karaka_formulas():
    text = _writer_text()
    k = _const().all_formulas_of("karaka_chara_position")
    assert sorted(k) == ["kn_rao_rahu_included", "parashari_rahu_excluded"]
    # the karaka section emits both schools as the (school, ...) first element of its loop tuples
    assert re.search(r'\(\s*"parashari_rahu_excluded"\s*,', text) and re.search(r'\(\s*"kn_rao_rahu_included"\s*,', text)
    # Brahma / Shiva / Vishnu are keyed by the same two schools
    for cat in ("esoteric_point_brahma", "esoteric_point_shiva", "esoteric_point_vishnu"):
        assert sorted(_const().all_formulas_of(cat)) == sorted(k), cat


def test_the_canonical_karaka_school_is_the_one_ga_structural_pins():
    """ga_structural's karaka-web reader pins `_CANONICAL_KARAKA_SCHOOL` (the existing L1 convention, section N.5); the
    constant's canonical karaka school must be that same id."""
    s = (REPO / "platform/python-sidecar/ga_writers/ga_structural_writer.py").read_text(encoding="utf-8")
    assert re.search(r"_CANONICAL_KARAKA_SCHOOL\s*=\s*['\"]" + re.escape(_const().CANONICAL_KARAKA_SCHOOL) + r"['\"]", s)
