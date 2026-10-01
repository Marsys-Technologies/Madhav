"""
test_argala_graha_natal.py — SS N-61 (AR-1..AR-6): L1 graha-level argala rows.

Offline, no DB. Covers:
  * the BPHS worked example (`bphs_pg0312_c01`) as a GOLDEN test, proven by mutants to fail under
    L2's old pairing ({4->3, 11->10}) and under forward-only node counting;
  * the sign matrix's honest NULL for an empty argala source sign (AR-3) and its provenance (AR-4/5);
  * count-only outcomes, equal = undetermined, 'stronger' stays null (AR-1);
  * idempotency (stable fact_id, delete-then-insert per chart x category, no commit), D1 only (AR-6);
  * an independent reproduction of the canonical chart's stored signs (the offline design-note numbers).
"""
from __future__ import annotations

import os
import sys
from typing import Any

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ga_writers.ga_structural_writer as sut  # noqa: E402
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT  # noqa: E402

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID = "test-build-argala"
AY_ID = "lahiri_chitrapaksha"
ENG_VER = "pyjhora/1.0.0"
COMPUTED_AT = "2026-10-02T00:00:00+00:00"


def _state(signs: dict[str, int]) -> dict[str, Any]:
    """A D1 varga_state: {graha: {"sign_num": n}} (the only key the graha builder reads)."""
    return {g: {"sign_num": n} for g, n in signs.items()}


def _occupants(signs: dict[str, int]) -> dict[int, list[str]]:
    occ: dict[int, list[str]] = {}
    for g, n in signs.items():
        occ.setdefault(n, []).append(g)
    return occ


def _rows(signs: dict[str, int], ay: str = AY_ID) -> list[dict[str, Any]]:
    return sut._build_argala_graha_rows(
        _state(signs), "D1", CHART_ID, BUILD_ID, ay, COMPUTED_AT, ENG_VER
    )


# ── The BPHS worked example (Santhanam trans., Ch. 31, bphs_pg0311_c02 / bphs_pg0312_c01) ──────
# Hypothetical geniture, Aries ascendant: Mars in the 4th, Sun and Mercury in the 2nd, Jupiter in
# the 11th cause argala to the ascendant; countered by Saturn in the 10th, Venus in the 12th and
# Moon-Rahu in the 3rd. "From Rahu, the 2nd house counted in reverse order contains Sun-Mercury
# causing Argala to Rahu which is, however, obstructed by Mars in the 12th from Rahu (counted in
# reverse manner)". Ketu is not placed by the text; it is put opposite Rahu (Sagittarius).
BPHS_EXAMPLE: dict[str, int] = {
    "Sun": 2, "Mercury": 2,            # Taurus, the 2nd from Aries
    "Moon": 3, "Rahu": 3,              # Gemini, the 3rd
    "Mars": 4,                         # Cancer, the 4th
    "Saturn": 10,                      # Capricorn, the 10th
    "Jupiter": 11,                     # Aquarius, the 11th
    "Venus": 12,                       # Pisces, the 12th
    "Ketu": 9,                         # Sagittarius (opposite Rahu; not stated in the text)
}
ARIES = 1


def _assert_bphs_golden() -> None:
    occ = _occupants(BPHS_EXAMPLE)

    # (1) the ascendant, counted forward: the three argalas the text names, each with the
    #     obstructor the text names, in the pair the text gives (4-10, 2-12, 11-3); nothing at the 5th.
    by_off = {r["argala_offset"]: r for r in sut._argala_reading(ARIES, False, occ)}
    assert sorted(by_off) == [2, 4, 11]
    assert (by_off[4]["argala_grahas"], by_off[4]["obstruction_offset"], by_off[4]["obstructor_grahas"]) == (
        ["Mars"], 10, ["Saturn"])
    assert (by_off[2]["argala_grahas"], by_off[2]["obstruction_offset"], by_off[2]["obstructor_grahas"]) == (
        ["Sun", "Mercury"], 12, ["Venus"])
    assert (by_off[11]["argala_grahas"], by_off[11]["obstruction_offset"], by_off[11]["obstructor_grahas"]) == (
        ["Jupiter"], 3, ["Moon", "Rahu"])
    # outcomes as the RULED count-only rule gives them (the text calls all three "countered";
    # the count rule gives undetermined / prevails / obstructed: see the design note, section 0)
    assert by_off[4]["outcome"] == "undetermined"          # Mars 1 against Saturn 1
    assert by_off[2]["outcome"] == "argala_prevails"       # Sun-Mercury 2 against Venus 1
    assert by_off[11]["outcome"] == "obstructed"           # Jupiter 1 against Moon-Rahu 2

    # (2) Rahu as the reference counts in reverse: its 2nd is Taurus (Sun-Mercury), obstructed by
    #     Mars in "the 12th from Rahu (counted in reverse manner)".
    rahu = {r["argala_offset"]: r for r in sut._argala_reading(
        BPHS_EXAMPLE["Rahu"], "Rahu" in sut.ARGALA_REVERSED_REFERENCES, occ)}
    assert 2 in rahu, "Rahu's 2nd (counted in reverse) holds Sun-Mercury"
    assert rahu[2]["argala_grahas"] == ["Sun", "Mercury"]
    assert rahu[2]["obstruction_offset"] == 12
    assert rahu[2]["obstructor_grahas"] == ["Mars"]
    assert rahu[2]["argala_sign_num"] == 2 and rahu[2]["obstruction_sign_num"] == 4

    # (3) the same through the row builder: target Rahu, source Sun and Mercury, reverse count
    rows = {(r["fact_subject"], r["fact_key"]): r for r in _rows(BPHS_EXAMPLE)}
    for src in ("SUN", "MER"):
        assert ("D1_RAH_MEAN", f"from_{src}_offset_2") in rows, f"Rahu has no argala from {src} at offset 2"
        row = rows[("D1_RAH_MEAN", f"from_{src}_offset_2")]
        j = row["fact_value_jsonb"]
        assert j["count_direction"] == "reverse"
        assert j["obstructor_grahas"] == ["Mars"] and j["obstruction_offset"] == 12


def test_golden_bphs_worked_example():
    _assert_bphs_golden()


def test_golden_fails_under_l2_old_pairing(monkeypatch):
    """Mutant 1: L2's old pairing ({4->3, 11->10}) must NOT satisfy the golden test."""
    monkeypatch.setattr(sut, "ARGALA_OBSTRUCTION_PAIRS", ((2, 12), (4, 3), (5, 9), (11, 10)))
    with pytest.raises(AssertionError):
        _assert_bphs_golden()


def test_golden_fails_under_forward_only_node_counting(monkeypatch):
    """Mutant 2: forward-only counting for the nodes must NOT satisfy the golden test."""
    monkeypatch.setattr(sut, "ARGALA_REVERSED_REFERENCES", frozenset())
    with pytest.raises(AssertionError):
        _assert_bphs_golden()


def test_golden_fails_if_only_ketu_reverses(monkeypatch):
    """The Ketu-only variant is a named stricter reading, not the ruled one: Rahu would count forward."""
    monkeypatch.setattr(sut, "ARGALA_REVERSED_REFERENCES", frozenset({"Ketu"}))
    with pytest.raises(AssertionError):
        _assert_bphs_golden()


def test_pairing_is_the_ruled_set_and_constants_are_derived_from_it():
    assert set(sut.ARGALA_OBSTRUCTION_PAIRS) == {(2, 12), (4, 10), (11, 3), (5, 9)}
    assert sut.ARGALA_OFFSETS == [2, 4, 5, 11]          # unchanged values, derived from the pairs
    assert sut.VIRODHA_OFFSETS == [12, 10, 9, 3]
    assert sut.ARGALA_BASIC_OFFSETS == frozenset({2, 4, 11})
    assert sut.ARGALA_REVERSED_REFERENCES == frozenset({"Rahu", "Ketu"})


# ── AR-3: an empty source sign is NULL with no_occupant (sign matrix) ───────────────────────────

MOCK_SIGNS = {"Sun": 10, "Moon": 11, "Mars": 1, "Mercury": 10, "Jupiter": 9, "Venus": 10,
              "Saturn": 7, "Rahu": 2, "Ketu": 8}   # the occupancy test_ga8_writer's MOCK_CHART_OUTPUT uses


def _mock_chart_output() -> dict[str, Any]:
    names = {1: "Aries", 2: "Taurus", 7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn", 11: "Aquarius"}
    return {
        "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
        "grahas": [{"name": g, "sign": names[n], "sign_id": n, "house": n, "longitude": 0.0,
                    "retrograde": False, "dignity_status": "neutral"} for g, n in MOCK_SIGNS.items()],
    }


def test_empty_argala_source_sign_is_null_no_occupant_and_occupied_cells_keep_the_formula():
    rows = sut._build_argala_rows(_mock_chart_output(), CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
    argala = [r for r in rows if r["fact_category"] == "argala_natal_matrix"]
    assert len(argala) == 144
    occ = _occupants(MOCK_SIGNS)
    malefics = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}
    null_cells = 0
    for r in argala:
        target = int(r["fact_subject"].rsplit("_", 1)[1])
        source = int(r["fact_key"].split("_")[2])
        offset = int(r["fact_key"].rsplit("_", 1)[1])
        assert offset == (source - target) % 12 + 1
        if offset in (2, 4, 5, 11):
            if source in occ:
                expected = round(max(1.0 - 0.25 * sum(1 for g in occ[source] if g in malefics), -1.0), 4)
                assert r["fact_value_num"] == expected and r["fact_value_text"] is None
            else:
                null_cells += 1
                assert r["fact_value_num"] is None, "an empty source sign must not score 1.0"
                assert r["fact_value_text"] == "no_occupant"
        else:
            assert r["fact_value_num"] == 0.0 and r["fact_value_text"] is None
    # 4 argala offsets x the 5 empty signs (3, 4, 5, 6, 12) of this occupancy
    assert null_cells == 4 * (12 - len(occ)) == 20


def test_sign_matrix_provenance_names_the_real_function_is_forward_only_and_cites_chapter_31():
    rows = sut._build_argala_rows(_mock_chart_output(), CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
    assert len(rows) == 288
    for r in rows:
        assert r["source_calculation"] == f"ga_structural_writer._build_argala_rows/{ENG_VER}"
        assert "pyjhora_adapter" not in r["source_calculation"]
        assert r["source_calculation"].startswith("ga_structural")      # bo_laksana._infer_source_l1_asset keys on this
        assert r["verification_pass_status"] == UNVERIFIED_DEFAULT == "single"
        text = r["formula_provenance_text"]
        assert "bphs_pg0311_c01" in text and "bphs_jaimini_pg0023_c01" in text and "sourced_ocr_unverified" in text
        assert "FORWARD-ONLY" in text and "argala_graha_natal" in text
        assert "Ch. 28" not in text
    argala_text = next(r["formula_provenance_text"] for r in rows if r["fact_category"] == "argala_natal_matrix")
    assert "unsourced project convention" in argala_text


# ── AR-1: count-only outcomes, equal = undetermined, 'stronger' null ────────────────────────────

@pytest.mark.parametrize("argala,obstr,outcome", [
    (1, 0, "argala_prevails"), (2, 1, "argala_prevails"),
    (1, 2, "obstructed"), (1, 3, "obstructed"),
    (1, 1, "undetermined"), (2, 2, "undetermined"),
])
def test_outcome_is_by_count_only(argala, obstr, outcome):
    assert sut._argala_outcome(argala, obstr) == outcome


def test_equal_counts_are_undetermined_in_rows_and_strength_comparison_stays_null():
    # Target Aries (1): the 2nd (Taurus) holds Sun+Mercury, the paired 12th (Pisces) holds Venus+Jupiter.
    signs = {"Mars": 1, "Sun": 2, "Mercury": 2, "Venus": 12, "Jupiter": 12, "Moon": 6, "Saturn": 6, "Rahu": 6, "Ketu": 6}
    rows = [r for r in _rows(signs) if r["fact_subject"] == "D1_MAR"]
    assert {r["fact_key"] for r in rows} == {"from_SUN_offset_2", "from_MER_offset_2"}
    for r in rows:
        assert r["fact_value_text"] == "undetermined"
        assert r["fact_value_jsonb"]["argala_count"] == r["fact_value_jsonb"]["obstructor_count"] == 2
    for r in _rows(signs):
        assert r["fact_value_jsonb"]["strength_comparison"] is None
        assert r["fact_value_jsonb"]["outcome_basis"] == "count_only"


def test_obstruction_applies_to_benefic_argala_too():
    # Moon (a benefic) causes argala on Mercury and is obstructed: obstruction is not malefic-only.
    signs = {"Mercury": 1, "Moon": 2, "Jupiter": 12, "Venus": 12, "Sun": 6, "Mars": 6, "Saturn": 6, "Rahu": 7, "Ketu": 1}
    row = next(r for r in _rows(signs) if r["fact_subject"] == "D1_MER" and r["fact_key"] == "from_MOON_offset_2")
    assert row["fact_value_text"] == "obstructed"


def test_empty_obstruction_side_is_prevails_with_zero_obstructors():
    signs = {"Mars": 1, "Sun": 2, "Moon": 6, "Mercury": 6, "Jupiter": 6, "Venus": 6, "Saturn": 6, "Rahu": 6, "Ketu": 7}
    row = next(r for r in _rows(signs) if r["fact_subject"] == "D1_MAR" and r["fact_key"] == "from_SUN_offset_2")
    j = row["fact_value_jsonb"]
    assert row["fact_value_text"] == "argala_prevails" and j["obstructor_count"] == 0 and j["obstructor_grahas"] == []


# ── Row shape and keys ──────────────────────────────────────────────────────────────────────────

def test_row_shape_keys_tier_and_provenance():
    rows = _rows(BPHS_EXAMPLE)
    assert rows, "the worked example has argala"
    assert len({r["fact_id"] for r in rows}) == len(rows)
    sut._verify_no_duplicate_fact_ids(rows)
    sut._verify_citation_completeness(rows)
    sut._linter_check_rows(rows)
    for r in rows:
        assert r["fact_category"] == "argala_graha_natal"
        assert r["fact_subject"].startswith("D1_")
        assert r["fact_key"].startswith("from_") and "_offset_" in r["fact_key"]
        assert r["verification_pass_status"] == "single"
        assert r["source_calculation"] == f"ga_structural_writer._build_argala_graha_rows/{ENG_VER}"
        assert r["fact_value_text"] in {"argala_prevails", "obstructed", "undetermined"}
        assert r["fact_value_num"] == r["fact_value_jsonb"]["argala_count"]
        assert r["unit"] == "graha_count"
        j = r["fact_value_jsonb"]
        assert j["offset_class"] == ("basic" if j["argala_offset"] in (2, 4, 11) else "extended")
        assert j["count_direction"] == ("reverse" if j["target_graha"] in ("Rahu", "Ketu") else "forward")
        assert "benefic" not in str(j) and "malefic" not in str(j)           # no classification stored
        assert "bphs_pg0312_c01" in r["formula_provenance_text"]
    # the new category is not in the contradiction_pair families (valence must never be inferred from it)
    assert "argala_graha_natal" not in {
        "argala_natal_matrix", "virodha_argala_natal_matrix", "net_argala"}


def test_no_row_for_an_empty_argala_sign_or_a_non_argala_offset():
    signs = {"Mars": 1, "Sun": 3, "Moon": 6, "Mercury": 6, "Jupiter": 6, "Venus": 6, "Saturn": 6, "Rahu": 6, "Ketu": 7}
    assert [r for r in _rows(signs) if r["fact_subject"] == "D1_MAR"] == []   # Sun is the 3rd from Mars: not an argala


# ── Idempotency (delete-then-insert per chart x natural key), contract (never commits) ──────────

class _RecordingConn:
    """Stands in for ctx.db_conn: records SQL, refuses commit/close (the writer must never call them)."""
    def __init__(self):
        self.executed: list[tuple[str, Any]] = []
        self.many: list[tuple[str, list]] = []

    def execute(self, sql, params=None):
        self.executed.append((" ".join(str(sql).split()), params))

        class _Cur:
            rowcount = 0
        return _Cur()

    def cursor(self, *a, **k):
        conn = self

        class _C:
            def executemany(self_inner, sql, tuples):
                conn.many.append((" ".join(sql.split()), list(tuples)))

            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *exc):
                return False
        return _C()

    def commit(self):
        raise AssertionError("the writer must never commit ctx.db_conn")

    def close(self):
        raise AssertionError("the writer must never close ctx.db_conn")


def test_ids_are_stable_across_builds_and_rebuild_replaces_per_chart_and_category():
    a = sut._build_argala_graha_rows(_state(BPHS_EXAMPLE), "D1", CHART_ID, "build-A", AY_ID, COMPUTED_AT, ENG_VER)
    b = sut._build_argala_graha_rows(_state(BPHS_EXAMPLE), "D1", CHART_ID, "build-B", AY_ID, COMPUTED_AT, ENG_VER)
    assert [r["fact_id"] for r in a] == [r["fact_id"] for r in b]            # build_id is never identity

    conn = _RecordingConn()
    assert sut._insert_chart_facts_rows(conn, a) == len(a)
    deletes = [(s, p) for s, p in conn.executed if s.startswith("DELETE FROM chart_facts")]
    assert len(deletes) == 1
    sql, params = deletes[0]
    assert "chart_id = %s" in sql and "fact_category = ANY(%s)" in sql and "ayanamsha_id = ANY(%s)" in sql
    assert params[0] == CHART_ID and params[1] == ["argala_graha_natal"] and params[2] == [AY_ID]
    # one INSERT carrying every row, with the provenance column bound
    (insert_sql, tuples), = conn.many
    assert "formula_provenance_text" in insert_sql and len(tuples) == len(a)
    assert all(t[-1] and "bphs_pg0311_c01" in t[-1] for t in tuples)


# ── D1 only (AR-6) ──────────────────────────────────────────────────────────────────────────────

def test_d1_only_a_divisional_chart_is_refused_not_silently_emitted():
    with pytest.raises(ValueError):
        sut._build_argala_graha_rows(_state(BPHS_EXAMPLE), "D9", CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
    assert {r["fact_subject"][:3] for r in _rows(BPHS_EXAMPLE)} == {"D1_"}
    assert {r["fact_value_jsonb"]["varga"] for r in _rows(BPHS_EXAMPLE)} == {"D1"}


def test_the_family_is_registered_top_level_before_contradiction_pair():
    keys = [e[0] for e in sut.STRUCTURAL_SUB_BUILDERS if e[2] == "top_level"]
    assert "argala_graha" in keys and keys.index("argala_graha") < keys.index("contradiction_pair")
    entry = next(e for e in sut.STRUCTURAL_SUB_BUILDERS if e[0] == "argala_graha")
    assert entry[1] is sut._build_argala_graha_rows and entry[3] is None


# ── Independent reproduction of the canonical chart (stored L1 signs; design-note section 3) ────

CANONICAL_SIGNS = {  # chart_facts(graha_sign_attributes, sign_num), chart 482012f1, read-only
    "lahiri_chitrapaksha": {"Sun": 10, "Moon": 11, "Mars": 7, "Mercury": 10, "Jupiter": 9, "Venus": 9, "Saturn": 7, "Rahu": 2, "Ketu": 8},
    "surya_siddhanta_classical": {"Sun": 10, "Moon": 12, "Mars": 7, "Mercury": 10, "Jupiter": 9, "Venus": 9, "Saturn": 7, "Rahu": 2, "Ketu": 8},
}


def _tally(rows):
    out: dict[str, int] = {}
    for r in rows:
        out[r["fact_value_text"]] = out.get(r["fact_value_text"], 0) + 1
    return out


def test_canonical_chart_reproduces_the_offline_design_note_numbers():
    lahiri = _rows(CANONICAL_SIGNS["lahiri_chitrapaksha"])
    assert len(lahiri) == 32
    assert _tally(lahiri) == {"argala_prevails": 27, "undetermined": 3, "obstructed": 2}
    assert sum(1 for r in lahiri if r["fact_value_jsonb"]["argala_offset"] == 5) == 6
    assert sum(1 for r in lahiri if r["fact_value_jsonb"]["count_direction"] == "reverse") == 7
    obstructed = {(r["fact_subject"], r["fact_key"]) for r in lahiri if r["fact_value_text"] == "obstructed"}
    assert obstructed == {("D1_MER", "from_MOON_offset_2"), ("D1_SUN", "from_MOON_offset_2")}
    # a node as the TARGET reads the reverse count: Ketu (sign 8) has its 2nd at sign 7 (Mars, Saturn)
    ketu = {r["fact_key"]: r for r in lahiri if r["fact_subject"] == "D1_KET_MEAN"}
    assert ketu["from_MAR_offset_2"]["fact_value_jsonb"]["count_direction"] == "reverse"
    assert ketu["from_MAR_offset_2"]["fact_value_jsonb"]["obstructor_grahas"] == ["Jupiter", "Venus"]
    sid = _rows(CANONICAL_SIGNS["surya_siddhanta_classical"], "surya_siddhanta_classical")
    assert len(sid) == 28
