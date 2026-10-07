"""N-143 option A: L1 row ids that downstream layers cite must be deterministic.

chart_divisionals.id  -> UUID5 over the table's own unique key (this PR; was gen_random_uuid()).
chart_dashas.dasha_row_id -> UUID5 chain (already so since S-L1 #2984); these tests LOCK that
property so a rebuild can never again orphan a Gochara snapshot / L2 citation.

No database is opened: divisionals run through the real ga_vargas row builders and real SQL
text against the FakeDB of test_ga_vargas_key_widening; dashas run the real build_system
(skip_db) with a spy on the stabilisation post-pass.
"""
from __future__ import annotations

import re
import uuid

import pytest
import swisseph as swe

from ga_writers import _deterministic_ids as D
from ga_writers import ga_dashas_writer as DW
from ga_writers import ga_vargas_writer as VW
from ga_writers.__tests__.test_ga_vargas_key_widening import (  # noqa: F401  (fixtures re-used)
    BIRTH, CHART, SEVEN, FakeDB, _deities, _karakas, _legal,
)

BUILD_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BUILD_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
KEY = (CHART, "Sun", "lahiri_chitrapaksha", "D9", "varga_position", "sign", "D9.SUN")


# --------------------------------------------------------------------------
# chart_divisionals.id
# --------------------------------------------------------------------------

def test_divisional_id_is_a_uuid5_pure_function_of_the_key() -> None:
    a, b = D.divisional_row_id(*KEY), D.divisional_row_id(*KEY)
    assert a == b
    parsed = uuid.UUID(a)
    assert parsed.version == 5


def test_every_key_column_participates_and_nothing_else_does() -> None:
    base = D.divisional_row_id(*KEY)
    seen = {base}
    for i in range(len(KEY)):
        k = list(KEY)
        k[i] = str(k[i]) + "x"
        nid = D.divisional_row_id(*k)
        assert nid != base, f"column {D.DIVISIONAL_KEY_COLUMNS[i]} does not feed the id"
        seen.add(nid)
    assert len(seen) == len(KEY) + 1
    row = dict(zip(D.DIVISIONAL_KEY_COLUMNS, KEY))
    noisy = {**row, "build_id": BUILD_A, "verification_pass_status": "two_pass_verified",
             "fact_value_text": "Leo", "fact_value_num": 5.0}
    assert D.divisional_row_id_for(noisy) == D.divisional_row_id_for({**row, "build_id": BUILD_B,
                                                                       "verification_pass_status": "single"})


def test_null_is_distinct_from_empty_string_like_nulls_not_distinct() -> None:
    """The unique index is NULLS NOT DISTINCT: NULL == NULL, but NULL != ''. The id must agree."""
    k_null = list(KEY); k_null[6] = None
    k_empty = list(KEY); k_empty[6] = ""
    assert D.divisional_row_id(*k_null) == D.divisional_row_id(*k_null)
    assert D.divisional_row_id(*k_null) != D.divisional_row_id(*k_empty)


def test_chart_id_uuid_object_and_text_give_the_same_id() -> None:
    k = list(KEY); k[0] = uuid.UUID(CHART)
    assert D.divisional_row_id(*k) == D.divisional_row_id(*KEY)


def test_no_random_id_generator_left_in_the_divisionals_sql() -> None:
    for sql in (VW._UPSERT_SQL, VW._UPSERT_WITH_FACT_ID_SQL):
        assert "gen_random_uuid" not in sql and "uuid_generate" not in sql
        assert re.search(r"VALUES\s*\(\s*%\(id\)s,", sql), "the id must be bound from the writer"


def _build(db: FakeDB, build_id: str, ayas: list[str]) -> dict:
    s = VW.build_ga_vargas(CHART, build_id, conn=db, birth_params=BIRTH, ayanamsha_subset=ayas)
    assert s["status"] == "PASS" and s["rows_collided"] == 0
    return s


def test_same_input_same_ids_across_two_builds(_deities: None, _karakas: None) -> None:
    ayas = ["lahiri_chitrapaksha"]
    db1, db2 = FakeDB(SEVEN), FakeDB(SEVEN)
    _build(db1, BUILD_A, ayas)
    _build(db2, BUILD_B, ayas)
    m1 = {k: r["id"] for k, r in db1.rows.items()}
    m2 = {k: r["id"] for k, r in db2.rows.items()}
    assert m1 and m1 == m2, "a rebuild under a new build id must re-create the identical id per natural key"
    assert {r["build_id"] for r in db1.rows.values()} != {r["build_id"] for r in db2.rows.values()}


def test_rebuild_into_the_same_db_replaces_with_identical_ids(_deities: None, _karakas: None) -> None:
    ayas = ["lahiri_chitrapaksha"]
    db = FakeDB(SEVEN)
    _build(db, BUILD_A, ayas)
    before = {k: r["id"] for k, r in db.rows.items()}
    n = len(db.rows)
    _build(db, BUILD_B, ayas)
    assert len(db.rows) == n, "rebuild replaces, never accretes"
    assert {k: r["id"] for k, r in db.rows.items()} == before


def test_ids_unique_over_all_five_ayanamshas_and_sentinels(_deities: None, _karakas: None) -> None:
    db = FakeDB(SEVEN)
    _build(db, BUILD_A, list(DW.AYANAMSHAS))
    ids = [r["id"] for r in db.rows.values()]
    assert len(ids) == 5 * 7718 + 6
    assert len(set(ids)) == len(ids), "an id collision would make the PK reject a legitimate row"
    assert all(uuid.UUID(i).version == 5 for i in ids)
    for k, r in db.rows.items():  # id == f(natural key) for EVERY stored row
        assert r["id"] == D.divisional_row_id(*k)


def test_per_row_fallback_path_also_carries_the_id(_deities: None) -> None:
    rows = _legal([{"chart_id": CHART, "graha": "Mars", "ayanamsha_id": "lahiri_chitrapaksha",
                    "varga": "D30", "fact_category": "varga_d30_lord_per_amsa",
                    "fact_key": "Mars_0_5", "fact_subject": "D30.S1"}])

    class Broken(FakeDB):
        def cursor(self, **kw):
            cur = super().cursor()

            def boom(sql, r):
                raise RuntimeError("batch refused")
            cur.executemany = boom  # type: ignore[method-assign]
            return cur

    db = Broken(SEVEN)
    assert VW._write_rows_batch(db, rows, set(), VW.new_write_stats()) == 1
    (stored,) = db.rows.values()
    assert stored["id"] == D.divisional_row_id(CHART, "Mars", "lahiri_chitrapaksha", "D30",
                                               "varga_d30_lord_per_amsa", "Mars_0_5", "D30.S1")


# --------------------------------------------------------------------------
# chart_dashas.dasha_row_id (already deterministic: lock it)
# --------------------------------------------------------------------------

MOON = 325.5
BIRTH_JD = swe.julday(1984, 2, 5, 5.21667)
BP = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.2961, "longitude_deg": 85.8245,
      "tz_offset_hours": 5.5, "place_name": "Bhubaneswar", "subject_label": "native"}
AYA = "lahiri_chitrapaksha"
ROLES = {"Moon": "AK", "Saturn": "AmK", "Sun": "BK", "Venus": "MK",
         "Mars": "PiK", "Rahu": "PK", "Jupiter": "GK", "Mercury": "DK"}


def _dasha_rows(monkeypatch: pytest.MonkeyPatch, system: str, build_id: str) -> list[dict]:
    captured: dict = {}
    real = DW.stabilize_hierarchical_uuids

    def spy(rows, **kw):
        out = real(rows, **kw)
        captured["rows"] = rows
        captured["kw"] = kw
        return out

    monkeypatch.setattr(DW, "stabilize_hierarchical_uuids", spy)
    monkeypatch.setattr(DW, "_get_moon_position", lambda aya, birth=None: (MOON, BIRTH_JD))
    DW.set_karaka_roles(DW.CANONICAL_CHART_ID, AYA, ROLES)
    DW.build_system(system, AYA, DW.CANONICAL_CHART_ID, build_id, birth_params=BP, skip_db=True)
    assert captured["kw"]["identity_fields"] == D.DASHA_IDENTITY_FIELDS
    assert captured["kw"]["kind"] == D.DASHA_ID_KIND
    return captured["rows"]


@pytest.fixture(scope="module")
def vim_two_builds():
    mp = pytest.MonkeyPatch()
    saved = dict(DW._KARAKA_ROLE_CACHE)
    try:
        a = _dasha_rows(mp, "vimshottari", BUILD_A)
        b = _dasha_rows(mp, "vimshottari", BUILD_B)
    finally:
        DW._KARAKA_ROLE_CACHE.clear()
        DW._KARAKA_ROLE_CACHE.update(saved)
        mp.undo()
    return a, b


def _natural_key(r: dict) -> tuple:
    return (r["ayanamsha_id"], r["system_id"], r["level_n"], r["start_iso"], r.get("kp_sublevel") or "")


def test_dasha_ids_identical_across_two_builds(vim_two_builds) -> None:
    a, b = vim_two_builds
    assert len(a) == len(b) > 1000
    assert {r["build_id"] for r in a} != {r["build_id"] for r in b}
    assert {_natural_key(r): r["dasha_row_id"] for r in a} == {_natural_key(r): r["dasha_row_id"] for r in b}


def test_dasha_ids_unique_uuid5_and_natural_key_unique(vim_two_builds) -> None:
    a, _ = vim_two_builds
    ids = [r["dasha_row_id"] for r in a]
    assert len(set(ids)) == len(ids)
    assert len({_natural_key(r) for r in a}) == len(a), "chart_dashas_natural_key_kp_idx grain (build_id excluded)"
    assert all(uuid.UUID(i).version == 5 for i in ids)
    assert any(r.get("kp_sublevel") for r in a), "the KP sub-levels are part of the sample"


def test_parent_row_id_always_resolves_to_a_row_of_the_same_build(vim_two_builds) -> None:
    for rows in vim_two_builds:
        by_id = {r["dasha_row_id"]: r for r in rows}
        children = [r for r in rows if r["parent_row_id"] is not None]
        assert children
        for r in children:
            parent = by_id.get(r["parent_row_id"])
            assert parent is not None, f"dangling parent_row_id on {_natural_key(r)}"
            assert parent["build_id"] == r["build_id"]
            assert parent["ayanamsha_id"] == r["ayanamsha_id"]
            if r.get("kp_sublevel"):  # KP sub-periods hang off a vimshottari row or an upper KP row
                assert r["system_id"] == "vimshottari_kp" and parent["system_id"] in ("vimshottari", "vimshottari_kp")
            else:
                assert parent["system_id"] == r["system_id"] and parent["level_n"] == r["level_n"] - 1
        assert all(r["parent_row_id"] is None for r in rows if r["level_n"] == 1 and not r.get("kp_sublevel"))


def test_dasha_id_does_not_depend_on_the_verification_tier(vim_two_builds) -> None:
    a, _ = vim_two_builds
    r = next(x for x in a if x["level_n"] == 2 and not x.get("kp_sublevel"))
    parent = next(x for x in a if x["dasha_row_id"] == r["parent_row_id"])
    vals = [r.get(f) for f in D.DASHA_IDENTITY_FIELDS]
    from ga_writers.data_plane_contracts import stable_uuid
    assert stable_uuid(D.DASHA_ID_KIND, parent["dasha_row_id"], *vals) == r["dasha_row_id"]
    # the identity tuple names no build/tier/value column at all
    assert not {"build_id", "verification_pass_status"} & set(D.DASHA_IDENTITY_FIELDS)


def test_vimshottari_independent_verifier_still_stamps_two_pass_verified(vim_two_builds) -> None:
    from brahmagyan import verification_tiers as T
    a, _ = vim_two_builds
    cover = [r for r in a if r["level_n"] in (1, 2, 3, 4) and r.get("kp_sublevel") is None]
    assert cover
    assert {r["verification_pass_status"] for r in cover} == {T.TWO_PASS_VERIFIED}
