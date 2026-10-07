"""Swamsa provenance sentences (ga_sensitive) and the varga aspect labels (ga_vargas) use proper ordinals."""
from __future__ import annotations

import re

import ga_writers.ga_sensitive_writer as sens
import ga_writers.ga_vargas_writer as vg

LONGS = {"LAGNA": 10.0, "SUN": 300.0, "MOON": 335.0, "MAR": 15.0, "MER": 290.0, "JUP": 120.0, "VEN": 330.0, "SAT": 200.0}


def test_swamsa_position_sentences_read_1st_2nd_3rd_not_1th_2th_3th():
    rows = sens._build_swamsa_rows(LONGS, "c", "lahiri_chitrapaksha", "b", "e")
    text = {
        int(r["fact_subject"].rsplit("_", 1)[1]): r["formula_provenance_text"]
        for r in rows
        if r["fact_key"] == "sign"
    }
    assert sorted(text) == list(range(1, 13))
    suffix = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 11: "11th", 12: "12th"}
    for n, word in suffix.items():
        assert f"Swamsa House {n} = {word} from Karakamsa" in text[n]
    assert not any(re.search(r"(^|[^0-9])[123]th\b", t) for t in text.values())


def test_varga_aspect_labels_saturn_third_is_3rd():
    aspects = vg._compute_aspect_matrix({"Saturn": 0, "Mars": 0, "Jupiter": 0, "Sun": 0})
    by_body = {b: sorted(a for bb, _, a in aspects if bb == b) for b in ("Saturn", "Mars", "Jupiter", "Sun")}
    assert by_body["Saturn"] == ["10th", "3rd", "7th"]
    assert by_body["Mars"] == ["4th", "7th", "8th"]
    assert by_body["Jupiter"] == ["5th", "7th", "9th"]
    assert by_body["Sun"] == ["7th"]


def test_no_hardcoded_th_suffix_after_an_interpolation():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "ga_writers"
    for name in ("ga_sensitive_writer.py", "ga_vargas_writer.py"):
        assert not re.findall(r"\}(?:th|st|nd|rd)\b", (root / name).read_text(encoding="utf-8")), name
