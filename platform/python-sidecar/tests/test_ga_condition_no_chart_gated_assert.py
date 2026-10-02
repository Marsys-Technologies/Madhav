"""
test_ga_condition_no_chart_gated_assert.py -- SS ruling 2026-10-02 (band/X2 lane, finding 4): a fatal
chart-specific guard in a writer that runs for every chart is removed before S-L1 and pinned by a
golden test instead (same ruling as the ga_medical Saturn / Sun assertions).

REMOVED from ga_condition_writer.build_ga_condition_substep: the `if chart_id == CANONICAL_CHART_ID:`
block that `assert`ed (1) the Sun's dignity_d1 not in exalted/moolatrikona/own and (2) the first Saturn
row's dignity_d1 == 'exalted', plus its "FORENSIC PASS" log line, the `forensic_rows` bookkeeping and
the module constant CANONICAL_CHART_ID (no other reader in the file).

This file pins (a) that no chart-id-gated `assert` is left in the writer, (b) that the writer is chart
independent (the canonical chart id with a non-exalted Saturn builds, nothing halts), and (c) the two
facts the removed asserts protected, on the WRITER PATH: build_ga_condition_substep, DB-free, on the
READ canonical inputs of tests/_ga_condition_canonical_inputs.py, for all five ayanamshas: Sun in
Capricorn is dignity_d1 'enemy_sign' (not exalted/moolatrikona/own, not debilitated) and Saturn in
Libra is 'exalted', with the pinned condition_score on each stored row.
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_condition_writer as w  # noqa: E402
from tests import _ga_condition_canonical_inputs as fx  # noqa: E402
from tests.test_ga_condition_fallback_guard import _FakeConn  # noqa: E402

WRITER_SRC = pathlib.Path(w.__file__).read_text(encoding="utf-8")
# the writer's INSERT column order (see `cols` at the INSERT in the writer), up to condition_score
COLS = [
    "chart_id", "build_id", "ayanamsha_id", "graha",
    "dignity_d1", "dignity_score_d1",
    "varga_dignity_spread", "varga_dignity_composite",
    "avastha_baladi", "avastha_jagradadi", "avastha_deeptaadi",
    "avastha_lajjitaadi", "avastha_sayanadi",
    "motion_state", "speed_degrees_per_day", "is_retrograde",
    "combustion_arc_from_sun", "is_combust", "is_deeply_combust",
    "naisargika_relation", "tatkalika_relation", "panchadha_relation",
    "graha_yuddha_with", "graha_yuddha_result",
    "condition_score",
]


# ---- (a) source-level: no chart-id-gated assert -----------------------------------------------

def _mentions_chart_id(node: ast.AST) -> bool:
    return any(
        (isinstance(n, ast.Name) and n.id in ("chart_id", "CANONICAL_CHART_ID"))
        or (isinstance(n, ast.Constant) and isinstance(n.value, str) and "482012f1" in n.value)
        for n in ast.walk(node)
    )


def test_no_assert_sits_under_an_if_on_chart_id():
    tree = ast.parse(WRITER_SRC)
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _mentions_chart_id(node.test):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Assert):
                    offenders.append(inner.lineno)
    assert offenders == [], f"chart-id-gated assert(s) at line(s) {offenders}"


def test_the_ast_check_can_fail_on_a_gated_assert():
    bad = ast.parse("def f(chart_id):\n    if chart_id == CANONICAL_CHART_ID:\n        assert 1 == 2\n")
    hits = [
        i for n in ast.walk(bad) if isinstance(n, ast.If) and _mentions_chart_id(n.test)
        for i in ast.walk(n) if isinstance(i, ast.Assert)
    ]
    assert hits


def test_the_writer_carries_no_canonical_chart_literal_or_forensic_block():
    assert "482012f1" not in WRITER_SRC
    assert not hasattr(w, "CANONICAL_CHART_ID")
    assert "FORENSIC FAIL" not in WRITER_SRC and "FORENSIC PASS" not in WRITER_SRC
    assert "forensic_rows" not in WRITER_SRC


# ---- writer-path harness ------------------------------------------------------------------------

def _wire(monkeypatch, positions, spreads):
    monkeypatch.setattr(w, "_load_dignity_ref", lambda conn: {})
    monkeypatch.setattr(w, "_load_combustion_orbs", lambda conn: fx.COMBUSTION_ORBS)
    monkeypatch.setattr(w, "_load_naisargika_friendships", lambda conn: {})
    monkeypatch.setattr(w, "_load_motion_thresholds", lambda conn: {})
    monkeypatch.setattr(w, "_load_graha_positions", lambda conn, c, a: positions)
    monkeypatch.setattr(w, "_load_varga_dignity_spread", lambda conn, c, a, g: spreads.get(g))
    monkeypatch.setattr(w, "_load_dasha_periods", lambda *a, **k: (None, None))
    monkeypatch.setattr(w, "_build_per_varga_avastha_rows", lambda *a, **k: [])
    monkeypatch.setattr(w, "_build_d1_avastha_rows", lambda *a, **k: [])


def _stored(conn):
    out = {}
    for params in conn.inserted:
        row = dict(zip(COLS, params[:len(COLS)]))
        out[row["graha"]] = (row, params)
    return out


def _canonical_positions(ayanamsha):
    sat, sun = fx.SATURN_CANONICAL[ayanamsha], fx.SUN_CANONICAL[ayanamsha]
    return [
        {"graha": "Sun", "sign": sun["sign"], "degree_in_sign": sun["degree_in_sign"],
         "longitude": sun["longitude"], "is_retrograde": False},
        {"graha": "Saturn", "sign": sat["sign"], "degree_in_sign": sat["degree_in_sign"],
         "longitude": sat["longitude"], "is_retrograde": False},
    ]


def _canonical_spreads(ayanamsha):
    return {
        "Sun": {k: {"dignity": v} for k, v in fx.SUN_CANONICAL[ayanamsha]["spread"].items()},
        "Saturn": {k: {"dignity": v} for k, v in fx.SATURN_CANONICAL[ayanamsha]["spread"].items()},
    }


# ---- (b) chart independence ---------------------------------------------------------------------

@pytest.mark.parametrize("sun_sign,saturn_sign", [("Aries", "Aries"), ("Leo", "Aquarius"), ("Capricorn", "Taurus")])
def test_the_canonical_chart_id_builds_whatever_the_dignities_are(monkeypatch, sun_sign, saturn_sign):
    """Before: the canonical chart id with a Sun in dignity or a non-exalted Saturn halted the build."""
    positions = [
        {"graha": "Sun", "sign": sun_sign, "degree_in_sign": 10.0, "longitude": 10.0, "is_retrograde": False},
        {"graha": "Saturn", "sign": saturn_sign, "degree_in_sign": 10.0, "longitude": 190.0, "is_retrograde": False},
    ]
    spreads = {g: {"D9": {"dignity": "Neutral"}} for g in ("Sun", "Saturn")}
    _wire(monkeypatch, positions, spreads)
    conn = _FakeConn(divisional_rows=1)
    assert w.build_ga_condition_substep(fx.CANONICAL_CHART_ID, "b1", "lahiri_chitrapaksha", conn) == 2


# ---- (c) the facts the removed asserts protected, pinned on the writer path ----------------------

@pytest.mark.parametrize("ayanamsha,sun_pin,saturn_pin", list(zip(fx.AYANAMSHAS, fx.SUN_PINNED_SCORES, fx.SATURN_PINNED_SCORES)))
def test_writer_path_pins_sun_enemy_sign_and_saturn_exalted(monkeypatch, ayanamsha, sun_pin, saturn_pin):
    _wire(monkeypatch, _canonical_positions(ayanamsha), _canonical_spreads(ayanamsha))
    conn = _FakeConn(divisional_rows=1)
    assert w.build_ga_condition_substep(fx.CANONICAL_CHART_ID, "b1", ayanamsha, conn) == 2
    rows = _stored(conn)

    sun_row, sun_params = rows["Sun"]
    assert sun_row["dignity_d1"] not in ("exalted", "moolatrikona", "own")   # the removed assert (1)
    assert sun_row["dignity_d1"] == "enemy_sign" != "debilitated"           # Capricorn: enemy, not debility
    assert sun_row["dignity_score_d1"] == w.DIGNITY_SCORES["enemy_sign"]

    saturn_row, saturn_params = rows["Saturn"]
    assert saturn_row["dignity_d1"] == "exalted"                              # the removed assert (2)

    # and the score the writer stored through the whole path equals the pinned canonical score
    score_idx = COLS.index("condition_score")
    assert sun_params[score_idx] == sun_pin
    assert saturn_params[score_idx] == saturn_pin


def test_the_writer_path_pin_can_fail(monkeypatch):
    """Mutating the Sun's enemy-sign classification must show on the writer-path output."""
    monkeypatch.setitem(w._DEBILITATION, "Sun", "Capricorn")
    _wire(monkeypatch, _canonical_positions("lahiri_chitrapaksha"), _canonical_spreads("lahiri_chitrapaksha"))
    conn = _FakeConn(divisional_rows=1)
    w.build_ga_condition_substep(fx.CANONICAL_CHART_ID, "b1", "lahiri_chitrapaksha", conn)
    assert _stored(conn)["Sun"][0]["dignity_d1"] == "debilitated"
