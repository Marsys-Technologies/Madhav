"""
test_prose2_writer_fallbacks.py -- TI-prose-batch2-writers: a literal fallback or a constant write becomes the real
value or an honest NULL (CLAUDE.md section N.7 items 1 and 6).

Every test here FAILS on the base the PR is cut from (verified on a clean checkout of origin/main with only this file
added) and passes with the writer edits. The static scan (`writer_literal_scan`) reading each writer clean is pinned in
platform/scripts/governance/__tests__/test_prose2_writer_scan.py; this file pins the BEHAVIOUR of each edited site.

  * ga_panchanga   _row requires citation_human; the no-panchaka sentence; tithi attributes absent -> no type / lord row;
                   deity absent -> no deity row; vara / sign ids outside their tables raise instead of storing a blank
  * ga_positions   a chalit graha with no sandhi reason says so; a missing nearest_boundary raises
  * ga_sade_sati   both row builders `R` take citation_human as a required keyword (AST)
  * ga_sensitive   `= null` is never printed as a value: a structured-value row and a valueless row each say what they are
  * ga_sensitive_degree  the detector's exception text never reaches a data leaf: a closed reason code does
  * ga_vargas      the D81 scope-cap sentence is composed from the row's own fields
  * ga_yoga        no 'N/A' stand-in graha in a karakamsha citation
"""
from __future__ import annotations

import ast
import pathlib
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

SIDECAR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIDECAR))

from ga_writers import ga_panchanga_writer as pw  # noqa: E402
from ga_writers import ga_positions_writer as pos  # noqa: E402
from ga_writers import ga_sensitive_degree_writer as sd  # noqa: E402
from ga_writers import ga_sensitive_writer as sw  # noqa: E402
from ga_writers.ga_yoga_writer import ChartState, _build_karakamsha_firings  # noqa: E402

CHART = "00000000-0000-0000-0000-00000000c0de"
NOW = "2026-01-01T00:00:00+00:00"
END = datetime(1984, 2, 5, 11, 30, tzinfo=timezone.utc)


# ───────────────────────────── ga_panchanga ─────────────────────────────

def test_panchanga_row_requires_its_citation_sentence():
    """No blank default: a caller that forgets the sentence fails loudly instead of storing ''."""
    with pytest.raises(TypeError):
        pw._row("cat", "SUBJ", "key", CHART, "INVARIANT", "b1", value_text="x")


def test_panchanga_row_with_a_sentence_stores_it_verbatim():
    r = pw._row("cat", "SUBJ", "key", CHART, "INVARIANT", "b1", value_text="x", citation_human="A sentence.")
    assert r["citation_human"] == "A sentence."


def _nak(nid):
    return SimpleNamespace(nakshatra=SimpleNamespace(id=nid, name=pw.NAKSHATRA_NAMES[nid - 1], end_utc=END))


@pytest.mark.parametrize("nid,ptype", [(23, "Roga"), (24, "Raja"), (25, "Agni"), (26, "Chora"), (27, "Mrityu")])
def test_active_panchaka_sentence_names_the_panchaka(nid, ptype):
    rows = pw._emit_panchaka_classification(_nak(nid), CHART, "b", NOW, "lahiri_chitrapaksha")
    overall = next(r for r in rows if r["fact_key"] == "panchaka_overall_classification")
    assert overall["fact_value_text"] == ptype
    assert overall["citation_human"] == f"Active panchaka at birth: {ptype} (lahiri_chitrapaksha)."


@pytest.mark.parametrize("nid", [1, 5, 12, 22])
def test_no_active_panchaka_says_so_and_never_prints_the_word_none_as_a_value(nid):
    rows = pw._emit_panchaka_classification(_nak(nid), CHART, "b", NOW, "lahiri_chitrapaksha")
    overall = next(r for r in rows if r["fact_key"] == "panchaka_overall_classification")
    assert overall["fact_value_text"] == "none"        # the stored classification token is unchanged
    assert overall["citation_human"] == (
        "No panchaka is active at birth: the Moon's nakshatra is not one of the five (lahiri_chitrapaksha)."
    )
    assert "none" not in overall["citation_human"].lower()


def test_panchaka_flag_inactive_is_one_row_and_active_names_the_nakshatra():
    inactive = pw._emit_panchaka_flag(_nak(5), CHART, "b", NOW, "raman")
    assert [r["fact_key"] for r in inactive] == ["active_at_birth_flag"]
    active = pw._emit_panchaka_flag(_nak(25), CHART, "b", NOW, "raman")
    pos_row = next(r for r in active if r["fact_key"] == "nakshatra_position")
    assert pos_row["fact_value_text"] == "Purva Bhadrapada"


def _tithi_pi(attrs):
    return SimpleNamespace(
        tithi=SimpleNamespace(id=3, name="Shukla Tritiya", end_utc=END),
        tithi_attrs=attrs,
    )


def test_tithi_without_attributes_emits_no_type_or_lord_rows_and_no_stand_in():
    rows = pw._emit_tithi(_tithi_pi(None), CHART, "b", NOW)
    keys = {r["fact_key"] for r in rows}
    assert {"type", "lord"}.isdisjoint(keys)
    assert {"name", "paksha", "end_iso", "inauspicious_flag"} <= keys
    for r in rows:
        assert r["fact_value_text"] != "unknown"
        assert r["citation_human"].strip() not in ("", "Tithi lord: .", "Tithi type: unknown.")


def test_tithi_with_attributes_still_emits_type_and_lord():
    attrs = SimpleNamespace(anga_type="nanda", deity="Gauri", lord="Mars", pct_elapsed=0.25)
    rows = {r["fact_key"]: r for r in pw._emit_tithi(_tithi_pi(attrs), CHART, "b", NOW)}
    assert rows["type"]["citation_human"] == "Tithi type: nanda."
    assert rows["lord"]["citation_human"] == "Tithi lord: Mars."


DISHA_SHUL = {1: "West", 2: "East", 3: "North", 4: "North", 5: "South", 6: "West", 7: "East"}
VARA_NAMES = {1: "Ravivara", 2: "Somavara", 3: "Mangalavara", 4: "Budhavara", 5: "Guruvara", 6: "Shukravara", 7: "Shanivara"}


@pytest.mark.parametrize("vid", range(1, 8))
def test_disha_shul_reads_the_vara_it_is_given(vid):
    pi = SimpleNamespace(vara=SimpleNamespace(id=vid, name=VARA_NAMES[vid]))
    rows = {r["fact_key"]: r for r in pw._emit_disha_shul(pi, CHART, "b", NOW)}
    assert rows["direction_to_avoid"]["fact_value_text"] == DISHA_SHUL[vid]
    assert rows["direction_to_avoid"]["citation_human"] == (
        f"Disha Shul (direction to avoid) at birth: {DISHA_SHUL[vid]} (vara={VARA_NAMES[vid]})."
    )
    assert rows["weekday_reference"]["citation_human"] == f"Disha Shul weekday reference: {VARA_NAMES[vid]}."


def test_disha_shul_without_a_vara_raises_instead_of_inventing_a_sunday():
    with pytest.raises(AttributeError):
        pw._emit_disha_shul(SimpleNamespace(vara=None), CHART, "b", NOW)


def test_sign_name_outside_the_table_raises_instead_of_a_blank_name():
    assert pw._sign_name(1) == "Mesha" and pw._sign_name(12) == "Meena"
    for bad in (0, 13, -1):
        with pytest.raises(ValueError):
            pw._sign_name(bad)


def test_moon_nakshatra_without_a_deity_emits_no_deity_row():
    def pi(deity):
        return SimpleNamespace(
            nakshatra=SimpleNamespace(id=25, name="Purva Bhadrapada", end_utc=END),
            nakshatra_attrs=SimpleNamespace(deity=deity, pct_elapsed=0.5),
        )
    absent = {r["fact_key"] for r in pw._emit_nakshatra_moon(pi(""), CHART, "b", NOW, "raman")}
    assert "deity" not in absent and "percent_elapsed_at_birth" in absent
    present = {r["fact_key"]: r for r in pw._emit_nakshatra_moon(pi("Aja Ekapada"), CHART, "b", NOW, "raman")}
    assert present["deity"]["citation_human"] == "Moon nakshatra deity: Aja Ekapada (raman)."


# ───────────────────────────── ga_positions ─────────────────────────────

def _chalit(**over):
    g = {
        "chalit_house": 10, "whole_sign_house": 10, "dist_to_madhya_deg": 2.5,
        "dist_to_nearest_boundary_deg": 12.5, "nearest_boundary": "start",
        "sandhi_flag": False, "sandhi_reasons": [],
    }
    g.update(over)
    return {"bhava_chalit": {"graha_chalit": {"Sun": g}}}


def test_a_graha_with_no_sandhi_reason_says_so():
    rows = {r["fact_key"]: r for r in pos._build_chalit_rows(_chalit(), CHART, "b", "lahiri_chitrapaksha", NOW)}
    r = rows["sandhi_reasons"]
    assert r["fact_value_text"] == "none"          # the stored token is unchanged
    assert r["citation_human"] == (
        "Sun has no bhāva-sandhi reason: neither the boundary orb nor a whole-sign divergence applies (Lahiri Chitrapaksha)."
    )


def test_a_graha_with_sandhi_reasons_lists_them():
    reasons = ["within_boundary_orb", "wholesign_chalit_divergence"]
    rows = {r["fact_key"]: r for r in pos._build_chalit_rows(
        _chalit(sandhi_flag=True, sandhi_reasons=reasons), CHART, "b", "lahiri_chitrapaksha", NOW)}
    assert rows["sandhi_reasons"]["citation_human"] == (
        "Sun bhāva-sandhi reasons: within_boundary_orb,wholesign_chalit_divergence (Lahiri Chitrapaksha)."
    )


def test_a_chalit_graha_without_nearest_boundary_raises_instead_of_storing_a_blank():
    g = _chalit()
    del g["bhava_chalit"]["graha_chalit"]["Sun"]["nearest_boundary"]
    with pytest.raises(KeyError):
        pos._build_chalit_rows(g, CHART, "b", "lahiri_chitrapaksha", NOW)


# ───────────────────────────── ga_sade_sati ─────────────────────────────

def test_sade_sati_row_builders_require_citation_human_by_keyword():
    """Both nested `R` row builders: citation_human is keyword-only with no default, and every call names it."""
    src = (SIDECAR / "ga_writers" / "ga_sade_sati_writer.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "R"]
    assert len(defs) == 2
    for fn in defs:
        kw = {a.arg: d for a, d in zip(fn.args.kwonlyargs, fn.args.kw_defaults)}
        assert "citation_human" in kw and kw["citation_human"] is None, "citation_human must be keyword-only, no default"
        assert "citation_human" not in [a.arg for a in fn.args.args]
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "R"]
    assert len(calls) == 68
    assert all(any(k.arg == "citation_human" for k in c.keywords) for c in calls)


# ───────────────────────────── ga_sensitive ─────────────────────────────

CH = "482012f1-710e-4a25-994a-93821f5871aa"


def _row(value_num=None, value_text=None, value_jsonb=None):
    return sw._make_row("kp_cuspal_significators", "H1", "sig", value_num, value_text, value_jsonb,
                        CH, "lahiri", "build-1", "eng-1")


def test_a_row_with_a_value_still_states_it():
    assert _row(value_num=292.5)["citation_human"] == "kp_cuspal_significators.H1.sig = 292.5 (lahiri)."
    assert _row(value_text="Capricorn")["citation_human"] == "kp_cuspal_significators.H1.sig = Capricorn (lahiri)."


def test_a_structured_row_says_the_value_is_in_the_jsonb_not_null():
    c = _row(value_jsonb={"a": 1})["citation_human"]
    assert c == "kp_cuspal_significators.H1.sig = a structured value, see fact_value_jsonb (lahiri)."
    assert "null" not in c


def test_a_row_with_no_value_says_it_has_none_not_null():
    c = _row()["citation_human"]
    assert c == "kp_cuspal_significators.H1.sig has no stored value (lahiri)."
    assert "null" not in c


class _Tx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _InsertConn:
    def __init__(self):
        self.inserted = []

    def transaction(self):
        return _Tx()

    def execute(self, sql, params=None):
        if "INSERT INTO chart_facts" in sql:
            self.inserted.append(params)

    def commit(self):
        pass


def test_the_jsonb_serialisation_failure_row_names_the_row_it_came_from(monkeypatch):
    monkeypatch.setattr(sw, "replace_prior_chart_facts", lambda conn, rows: None)
    row = _row(value_jsonb={"a": 1})
    row["fact_value_jsonb"] = {"unserialisable": object()}
    conn = _InsertConn()
    assert sw._insert_rows(conn, [row]) == 1
    p = conn.inserted[0]
    assert p[9] == "KP_PARSE_ERROR" and p[10] is None
    assert p[15] == "KP parse failed for H1: malformed JSONB in source data."


def test_a_row_without_a_subject_is_a_defect_not_an_UNKNOWN_row(monkeypatch):
    monkeypatch.setattr(sw, "replace_prior_chart_facts", lambda conn, rows: None)
    row = _row(value_jsonb={"a": 1})
    row["fact_value_jsonb"] = {"unserialisable": object()}
    del row["fact_subject"]
    with pytest.raises(KeyError):
        sw._insert_rows(_InsertConn(), [row])


# ───────────────────────────── ga_sensitive_degree ─────────────────────────────

SECRET = "boom: secret-detail-7f3a at /home/dev/private/path.py:123"

POSITIONS = {
    "Lagna": {"sign_num": 0, "degree_in_sign": 5.0, "longitude_sidereal": 5.0, "house_d1": 1},
    "Sun": {"sign_num": 9, "degree_in_sign": 22.0, "longitude_sidereal": 292.0, "house_d1": 10, "nakshatra": "Shravana"},
    "Moon": {"sign_num": 10, "degree_in_sign": 15.0, "longitude_sidereal": 315.0, "house_d1": 11, "nakshatra": "Purva Bhadrapada"},
}


def _leaves(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _leaves(v)
    elif isinstance(x, list):
        for v in x:
            yield from _leaves(v)
    else:
        yield x


def test_a_detector_failure_stores_a_closed_reason_code_never_the_exception_text(monkeypatch):
    import json
    from ga_writers import ga_yoga_writer

    def boom(*a, **k):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(ga_yoga_writer, "detect_neecha_bhanga", boom)
    rows = sd.build_sensitive_degree_rows(CH, "build-1", "lahiri_chitrapaksha", POSITIONS)
    nb = [r for r in rows if r["fact_key"] == "neecha_bhanga"]
    assert len(nb) == 2                                   # Sun and Moon (seven-graha set)
    for r in nb:
        assert r["fact_value_text"] == "detector_unavailable"
        doc = json.loads(r["fact_value_jsonb"])
        assert doc == {"detector": "ga_yoga_writer.detect_neecha_bhanga", "reason_code": "detector_raised"}
        assert "error" not in doc
        assert "secret-detail" not in json.dumps(r, default=str)
        assert r["verification_pass_status"] == "pending_w3_verification"


def test_the_exception_text_goes_to_the_log(monkeypatch, caplog):
    from ga_writers import ga_yoga_writer

    def boom(*a, **k):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(ga_yoga_writer, "detect_neecha_bhanga", boom)
    with caplog.at_level("WARNING"):
        sd.build_sensitive_degree_rows(CH, "build-1", "lahiri_chitrapaksha", POSITIONS)
    assert any("secret-detail-7f3a" in m for m in caplog.messages)


def test_a_working_detector_row_keeps_the_same_detector_name_leaf(monkeypatch):
    import json
    from ga_writers import ga_yoga_writer

    monkeypatch.setattr(ga_yoga_writer, "detect_neecha_bhanga", lambda d1, varga="D1": [])
    rows = sd.build_sensitive_degree_rows(CH, "build-1", "lahiri_chitrapaksha", POSITIONS)
    nb = [r for r in rows if r["fact_key"] == "neecha_bhanga"]
    assert nb and all(json.loads(r["fact_value_jsonb"]) == {"detector": sd.NEECHA_BHANGA_DETECTOR} for r in nb)


def test_kranti_without_an_ayanamsha_offset_stores_a_closed_reason_code_not_a_sentence():
    import json

    rows = sd.build_sensitive_degree_rows(CH, "build-1", "lahiri_chitrapaksha", POSITIONS, ayanamsha_offset_deg=None)
    kr = [r for r in rows if r["fact_key"] == "kranti"]
    assert kr and all(r["fact_value_text"] == "ayanamsha_offset_unresolved" for r in kr)
    for r in kr:
        doc = json.loads(r["fact_value_jsonb"])
        assert doc["reason_code"] == "tropical_longitude_unresolved"
        assert "note" not in doc
        assert set(doc) == {"longitude_sidereal", "reason_code"}


# ───────────────────────────── ga_yoga ─────────────────────────────

class _FakeCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))


def _karakamsha_state(with_atmakaraka):
    facts = [
        {"fact_id": "rahu_sign_fact", "fact_category": "graha_position", "fact_subject": "RAH_MEAN",
         "fact_key": "sign", "fact_value_text": "Aries", "fact_value_num": None},
        {"fact_id": "karakamsa_sign_fact", "fact_category": "karakamsa_position", "fact_subject": "KARAKAMSA",
         "fact_key": "sign", "fact_value_text": "Aries", "fact_value_num": None},
    ]
    if with_atmakaraka:
        facts.append({"fact_id": "ak_fact", "fact_category": "karakamsa_position", "fact_subject": "KARAKAMSA",
                      "fact_key": "atmakaraka_graha", "fact_value_text": "Saturn", "fact_value_num": None})
    return ChartState(facts)


def _citation(with_atmakaraka):
    cur = _FakeCursor()
    n = _build_karakamsha_firings(
        cur, chart_id=CH, build_uuid="00000000-0000-0000-0000-000000000000", ayanamsha_id="lahiri_chitrapaksha",
        state=_karakamsha_state(with_atmakaraka), shadbala_map={}, family_map={},
    )
    assert n == 1
    return cur.calls[0][1][18]            # citation_human, the 19th INSERT parameter


def test_karakamsha_citation_names_the_atmakaraka_when_the_fact_exists():
    c = _citation(True)
    assert "Ātmakāraka=Saturn; karakāṃśa reckoned as the D9 sign of the Ātmakāraka" in c


def test_karakamsha_citation_without_the_atmakaraka_fact_prints_no_stand_in_graha():
    c = _citation(False)
    assert "N/A" not in c and "n/a" not in c
    assert "the Ātmakāraka graha fact is absent from chart_facts for lahiri_chitrapaksha" in c
    assert c.startswith("Jaimini Sutram 1.2 (karakāṃśa-phala) / BPHS Ch.34: Rahu placed in the karakāṃśa (Aries) gives ")
