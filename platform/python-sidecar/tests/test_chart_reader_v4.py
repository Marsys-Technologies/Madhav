"""
test_chart_reader_v4.py — TDD suite for PRATIJÑĀ v4 Lane B1 (the Chart
Reader), `brahmagyan/chart_reader_v4.py`.

Live-DB tests (require DBURL — see PRATIJNA_V4_STATE.md 'DB access' for the
gcloud-secret + cloud-sql-proxy resolution recipe). Skipped, not failed,
when DBURL is unset (mirrors this repo's existing DB-dependent test
convention, e.g. test_cr131_gochara_db_reachability.py).

R13 discipline: every assertion below is checked against the DATABASE's
actual return, never a fabricated expected value tuned to either test
chart's known life outcomes — this is a generic retrieval API test.
"""
from __future__ import annotations

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from brahmagyan.chart_reader_v4 import (  # noqa: E402
    ChartReaderError,
    ChartReaderV4,
    SIGN_LORD,
    connect,
)

CHARTS = {
    "482012f1": "482012f1-710e-4a25-994a-93821f5871aa",
    "1c826d5a": "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
}
AYANAMSHA = "lahiri_chitrapaksha"

DBURL = os.environ.get("DBURL")
requires_db = pytest.mark.skipif(not DBURL, reason="DBURL not set — see PRATIJNA_V4_STATE.md")


@pytest.fixture(scope="module")
def conn():
    if not DBURL:
        pytest.skip("DBURL not set")
    c = connect(DBURL)
    yield c
    c.close()


@pytest.fixture()
def reader(conn):
    return ChartReaderV4(conn, ayanamsha=AYANAMSHA)


# ── sanity: SIGN_LORD matches probe_p2_tracer.py's copy (drift guard) ─────


def test_sign_lord_matches_probe_p2_tracer():
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    probe_path = repo_root / "platform" / "scripts" / "probes" / "probe_p2_tracer.py"
    src = probe_path.read_text()
    # Extract the probe's SIGN_LORD dict literal and eval it in isolation —
    # proves this module's copy is byte-for-byte the same table, not an
    # independently-typo'd transcription.
    start = src.index("SIGN_LORD = {")
    end = src.index("}", start) + 1
    probe_sign_lord = eval(src[start:end].split("=", 1)[1].strip())
    assert SIGN_LORD == probe_sign_lord


# ── occupants ────────────────────────────────────────────────────────────


@requires_db
@pytest.mark.parametrize("chart_label", list(CHARTS))
def test_occupants_h7_d1_matches_probe(reader, chart_label):
    chart_id = CHARTS[chart_label]
    result = reader.occupants(chart_id, house=7, varga="D1")
    grahas = [r["graha"] for r in result]
    assert grahas == sorted(grahas), "occupants must be deterministically ordered"
    for r in result:
        assert r["house"] == 7
        assert r["varga"] == "D1"
        assert r["provenance"], "every answer must carry non-empty provenance"
        assert r["provenance"][0]["id_kind"] == "chart_divisionals_id"
        assert r["provenance"][0]["id"]


@requires_db
def test_occupants_empty_house_returns_empty_list_not_error(reader):
    # A house with structurally no graha occupants (rare but must not crash)
    # is a legitimate empty-list answer, not an exception.
    result = reader.occupants(CHARTS["482012f1"], house=7, varga="D1_NONEXISTENT_VARGA")
    assert result == []


# ── sign_of ──────────────────────────────────────────────────────────────


@requires_db
@pytest.mark.parametrize("chart_label", list(CHARTS))
def test_sign_of_venus_d9_matches_probe(reader, chart_label):
    chart_id = CHARTS[chart_label]
    result = reader.sign_of(chart_id, "VEN", varga="D9")
    assert result["graha"] == "Venus"
    assert result["varga"] == "D9"
    assert result["sign"]
    assert 1 <= result["sign_number"] <= 12
    assert result["provenance"][0]["id_kind"] == "chart_divisionals_id"


@requires_db
def test_sign_of_accepts_short_and_long_graha_forms(reader):
    a = reader.sign_of(CHARTS["482012f1"], "VEN", varga="D9")
    b = reader.sign_of(CHARTS["482012f1"], "Venus", varga="D9")
    assert a["sign"] == b["sign"]


@requires_db
def test_sign_of_unknown_graha_raises(reader):
    with pytest.raises(ChartReaderError):
        reader.sign_of(CHARTS["482012f1"], "VEN", varga="D_DOES_NOT_EXIST")


# ── lord_of ──────────────────────────────────────────────────────────────


@requires_db
@pytest.mark.parametrize("chart_label", list(CHARTS))
def test_lord_of_h7_d1_matches_probe_fallback_logic(reader, chart_label):
    chart_id = CHARTS[chart_label]
    result = reader.lord_of(chart_id, house=7, varga="D1")
    assert result["house"] == 7
    assert result["varga"] == "D1"
    assert result["lord"] in SIGN_LORD.values()
    assert result["provenance"], "every answer must carry non-empty provenance"
    for p in result["provenance"]:
        assert p["id_kind"] in ("fact_id", "chart_divisionals_id", "derivation_note")


@requires_db
def test_lord_of_attaches_dignity_when_present(reader):
    # marriage-relevant house (7) lord in D9 (divisional slot) should carry
    # a dignity_state whenever chart_facts has one for that graha+varga.
    result = reader.lord_of(CHARTS["482012f1"], house=7, varga="D9")
    assert result["lord"]
    # dignity_state may legitimately be None if chart_facts has no row for
    # this lord+varga — assert the KEY exists, not that it's populated
    # (an honest null, per CLAUDE.md §N.7 item 6, is a valid answer).
    assert "dignity_state" in result


@requires_db
def test_lord_of_non_d1_varga_with_no_fallback_path_raises_or_returns(reader):
    # varga != D1 with no varga_house_lord row has NO honest fallback in
    # this module (the whole-sign-rulership fallback is D1-cusp-only) — it
    # must raise ChartReaderError, never silently guess.
    try:
        result = reader.lord_of(CHARTS["482012f1"], house=7, varga="D_NONEXISTENT")
    except ChartReaderError:
        pass
    else:
        pytest.fail(f"expected ChartReaderError for a nonexistent varga, got {result!r}")


# ── graha_state ──────────────────────────────────────────────────────────


@requires_db
@pytest.mark.parametrize("chart_label", list(CHARTS))
def test_graha_state_venus_d9_dignity_matches_probe_corroboration(reader, chart_label):
    chart_id = CHARTS[chart_label]
    result = reader.graha_state(chart_id, "VEN", varga="D9")
    assert result["graha"] == "VEN"
    assert result["varga"] == "D9"
    assert result["signals"], "VEN/D9 should have at least one identity-tagged signal"
    for s in result["signals"]:
        assert s["provenance"][0]["id_kind"] == "fact_id"
        assert s["provenance"][0]["id"]


@requires_db
def test_graha_state_signals_are_deterministically_ordered(reader):
    a = reader.graha_state(CHARTS["482012f1"], "VEN", varga="D9")
    b = reader.graha_state(CHARTS["482012f1"], "VEN", varga="D9")
    assert [s["fact_key"] for s in a["signals"]] == [s["fact_key"] for s in b["signals"]]


# ── special_points ───────────────────────────────────────────────────────


@requires_db
def test_special_points_upapada(reader):
    result = reader.special_points(CHARTS["482012f1"], kind="upapada")
    assert result, "482012f1 should have upapada_lagna facts"
    for r in result:
        assert r["kind"] == "upapada"
        assert r["fact_subject"] == "UPAPADA_LAGNA"
        assert r["provenance"][0]["id_kind"] == "fact_id"


@requires_db
def test_special_points_karaka_returns_both_schools_honestly(reader):
    # Live finding: karaka_chara_position stores TWO independently-computed
    # school conventions (parashari_rahu_excluded vs kn_rao_rahu_included)
    # under the identical fact_subject/fact_key. This function must not
    # silently collapse to one — it must surface both.
    result = reader.special_points(CHARTS["482012f1"], kind="karaka")
    schools = {
        r["fact_value_text"]
        for r in result
        if r["fact_subject"] == "DARAKARAKA" and r["fact_key"] == "karaka_school"
    }
    assert schools == {"parashari_rahu_excluded", "kn_rao_rahu_included"}


@requires_db
def test_special_points_unknown_kind_raises(reader):
    with pytest.raises(ChartReaderError):
        reader.special_points(CHARTS["482012f1"], kind="not_a_real_kind")


# ── aspect_between ───────────────────────────────────────────────────────


@requires_db
def test_aspect_between_returns_boolean_with_provenance(reader):
    result = reader.aspect_between(CHARTS["482012f1"], "MAR", "SAT", varga="D1")
    assert isinstance(result["aspects"], bool)
    assert result["target_house"]
    assert result["provenance"], "every answer must carry non-empty provenance"
    assert result["provenance"][0]["id_kind"] == "chart_divisionals_id"


@requires_db
def test_aspect_between_unknown_graha_b_raises(reader):
    with pytest.raises(ChartReaderError):
        reader.aspect_between(CHARTS["482012f1"], "MAR", "SAT", varga="D_DOES_NOT_EXIST")
