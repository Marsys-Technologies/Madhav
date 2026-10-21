"""PR #3840 review B1: migration 1401 (L0 node moolatrikona/own signs + five node-friendship pairs, SR-DOCTRINE-H) must not
change what the production L1 writer `ga_condition` stores for Rahu/Ketu.

Whether L1 emits a node moolatrikona/own tier, and whether it adopts the five corrected node pairs, is an open L1-owner decision
(`tests/test_f62_moolatrikona_downstream_vocabulary.py`, node pin). `build_ga_condition_substep` reads `bg_dignity_reference` and
`bg_graha_naisargika_friendship` from the DB, so the claim is measured on THAT path (not on `brahmagyan.classify_dignity`, which has
its own node early-exit): the writer is driven with the post-1401 L0 rows (the committed seeds) and compared with the same build on
the migration-250 shape (the L0 rows before 1401, typed here from DISPUTED_PAIRS_250 in the 1401 test).

Doctrine for the consistency check (CLAUDE.md N.5/N.8, one row must not contradict itself): a non-exalted, non-debilitated placement in a sign
whose lord is not the graha reads friend_sign / neutral_sign / enemy_sign exactly when `naisargika_relation` reads friend / neutral / enemy
(BPHS Ch.3 sign-lord friendship, the rule `dignity_d1_from_sign` applies).
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from brahmagyan.l0_dignity_reference import DIGNITY_REFERENCE  # noqa: E402
from ga_writers import ga_condition_writer as w  # noqa: E402
from pipeline.orchestrator.writers import bg_dignity_reference as W  # noqa: E402

CHART = "00000000-0000-0000-0000-00000000c0de"
AYA = "lahiri_chitrapaksha"
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
COLS = [
    "chart_id", "build_id", "ayanamsha_id", "graha", "dignity_d1", "dignity_score_d1", "varga_dignity_spread",
    "varga_dignity_composite", "avastha_baladi", "avastha_jagradadi", "avastha_deeptaadi", "avastha_lajjitaadi",
    "avastha_sayanadi", "motion_state", "speed_degrees_per_day", "is_retrograde", "combustion_arc_from_sun", "is_combust",
    "is_deeply_combust", "naisargika_relation", "tatkalika_relation", "panchadha_relation", "graha_yuddha_with",
    "graha_yuddha_result", "condition_score", "condition_formula_version", "condition_score_breakdown",
    "peak_dasha_periods", "weak_dasha_periods", "computed_at",
]
# the five pairs migration 1401 corrected, with the migration-250 relation they held before
DISPUTED_PAIRS_250 = {("Rahu", "Mercury"): "friend", ("Rahu", "Mars"): "neutral", ("Rahu", "Jupiter"): "neutral",
                      ("Ketu", "Sun"): "neutral", ("Ketu", "Moon"): "neutral"}
NODES = ("Rahu", "Ketu")


class _Cur:
    def __init__(self, conn):
        self._c = conn
        self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        if " ".join(sql.split()).upper().startswith("INSERT INTO GA_CONDITION_COMPOSITE"):
            self._c.inserted.append(params)

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class _Conn:
    def __init__(self):
        self.inserted: list = []

    def cursor(self, row_factory=None):
        return _Cur(self)


def _l0_after_1401() -> tuple[dict, dict]:
    ref = {r["graha"]: {"exaltation_sign": r["exaltation_sign"], "debilitation_sign": r["debilitation_sign"],
                        "moolatrikona_sign": r["moolatrikona_sign"], "own_signs": list(r["own_signs"] or [])}
           for r in DIGNITY_REFERENCE}
    fr: dict = {}
    for g, o, rel, _cite in W._NAISARGIKA_FRIENDSHIP:
        fr.setdefault(g, {})[o] = rel
    return ref, fr


def _l0_before_1401() -> tuple[dict, dict]:
    ref, fr = _l0_after_1401()
    for n in NODES:
        ref[n] = {**ref[n], "moolatrikona_sign": None, "own_signs": []}
    for (g, o), rel in DISPUTED_PAIRS_250.items():
        fr[g][o] = rel
    return ref, fr


def _build(monkeypatch, graha: str, sign: str, l0: tuple[dict, dict]) -> dict:
    ref, fr = l0
    monkeypatch.setattr(w, "_load_dignity_ref", lambda conn: ref)
    monkeypatch.setattr(w, "_load_combustion_orbs", lambda conn: {})
    monkeypatch.setattr(w, "_load_naisargika_friendships", lambda conn: fr)
    monkeypatch.setattr(w, "_load_motion_thresholds", lambda conn: {})
    monkeypatch.setattr(w, "_load_graha_positions", lambda conn, c, a: [{
        "graha": graha, "sign": sign, "degree_in_sign": 5.0, "longitude": SIGNS.index(sign) * 30 + 5.0,
        "house": 1, "is_retrograde": True}])
    monkeypatch.setattr(w, "_load_varga_dignity_spread", lambda conn, c, a, g: {"D9": {"sign": "Libra", "dignity": "Exalted"}})
    monkeypatch.setattr(w, "_load_dasha_periods", lambda *a, **k: (None, None))
    monkeypatch.setattr(w, "_build_per_varga_avastha_rows", lambda *a, **k: [])
    monkeypatch.setattr(w, "_build_d1_avastha_rows", lambda *a, **k: [])
    conn = _Conn()
    assert w.build_ga_condition_substep(CHART, "build-1", AYA, conn) == 1
    row = dict(zip(COLS, conn.inserted[0]))
    row.pop("computed_at")
    return row


@pytest.mark.parametrize("graha", NODES)
@pytest.mark.parametrize("sign", SIGNS)
def test_1401_does_not_change_what_ga_condition_stores_for_a_node(monkeypatch, graha, sign):
    """Rahu in Aquarius stored 'friend_sign' before 1401 and must still (L0 now says own sign; L1 tier is undecided)."""
    after = _build(monkeypatch, graha, sign, _l0_after_1401())
    before = _build(monkeypatch, graha, sign, _l0_before_1401())
    assert after == before, f"{graha} in {sign}: migration 1401 changed the stored ga_condition row"


@pytest.mark.parametrize("graha", NODES)
@pytest.mark.parametrize("sign", SIGNS)
def test_a_stored_node_row_does_not_contradict_itself(monkeypatch, graha, sign):
    """dignity_d1 and naisargika_relation of one row come from the same sign-lord friendship (BPHS Ch.3)."""
    row = _build(monkeypatch, graha, sign, _l0_after_1401())
    if row["dignity_d1"] in ("exalted", "debilitated", "own", "moolatrikona") or w.SIGN_LORDS[sign] == graha:
        return
    assert {"friend": "friend_sign", "neutral": "neutral_sign", "enemy": "enemy_sign"}[row["naisargika_relation"]] == row["dignity_d1"], (
        f"{graha} in {sign}: dignity_d1={row['dignity_d1']} contradicts naisargika_relation={row['naisargika_relation']}")


def test_the_post_1401_l0_rows_really_differ_from_the_pre_1401_rows_so_the_isolation_is_measured():
    """Guards the two tests above against vacuity: the five pairs and the node own/MT signs are different inputs."""
    a_ref, a_fr = _l0_after_1401()
    b_ref, b_fr = _l0_before_1401()
    assert a_ref["Rahu"]["own_signs"] == ["Aquarius"] and b_ref["Rahu"]["own_signs"] == []
    assert a_fr["Rahu"]["Mars"] == "enemy" and b_fr["Rahu"]["Mars"] == "neutral"
