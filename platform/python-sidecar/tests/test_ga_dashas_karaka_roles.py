"""
test_ga_dashas_karaka_roles.py — S-L1 mandatory fix: chart_dashas karaka role columns.

Defect: ga_dashas_writer applied one hard-coded lord -> role dict (Sun AK, Mars AmK,
Mercury BK, Saturn MK, Jupiter PK, Venus GK, Moon DK) to EVERY chart, so
karaka_role_at_period / karakas_active_during_period were identical on all charts and
wrong against each chart's own ga_sensitive karaka_chara_position (CLAUDE.md N.5, N.7
item 3). Fix: the writer READS the chart's own kn_rao_rahu_included assignments by stored
rank, through ga_writers/_karaka_roles.py's vocabulary.

NO DB required: the ga_sensitive read is a stubbed cursor carrying the canonical chart's
(482012f1, Lahiri) stored rows.
"""
from __future__ import annotations

import pathlib
import sys

import pytest
import swisseph as swe

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_dashas_writer as mod  # noqa: E402
from ga_writers._karaka_roles import KARAKA_ABBREVIATIONS_8, KARAKA_SCHOOL_KN_RAO  # noqa: E402

CHART = mod.CANONICAL_CHART_ID
AYAN = "lahiri_chitrapaksha"

# Canonical chart / Lahiri, kn_rao_rahu_included, by stored karaka_rank 1..8
# (ga_sensitive; same rows ga_vargas's tests use): Moon Saturn Sun Venus Mars Rahu Jupiter Mercury.
CANONICAL_ROLES = {
    "Moon": "AK", "Saturn": "AmK", "Sun": "BK", "Venus": "MK",
    "Mars": "PiK", "Rahu": "PK", "Jupiter": "GK", "Mercury": "DK",
}
_RANKED = [
    ("ATMAKARAKA", "Moon"), ("AMATYAKARAKA", "Saturn"), ("BHRATRIKARAKA", "Sun"),
    ("MATRIKARAKA", "Venus"), ("PITRIKARAKA", "Mars"), ("PUTRAKARAKA", "Rahu"),
    ("GNATIKARAKA", "Jupiter"), ("DARAKARAKA", "Mercury"),
]


def _stored_rows(ranked=_RANKED):
    """ga_sensitive rows as stored: (fact_subject, fact_key, fact_value_text, fact_value_num)."""
    rows = []
    for rank, (subject, graha) in enumerate(ranked, start=1):
        rows.append((subject, "assigned_graha", graha, None))
        rows.append((subject, "karaka_rank", None, float(rank)))
    return rows


class _FakeConn:
    """psycopg-shaped stub: conn.cursor(row_factory=...) -> context-managed cursor."""

    def __init__(self, rows):
        self._rows = rows
        self.calls: list[tuple[str, tuple]] = []

    def cursor(self, row_factory=None):
        conn = self

        class _Cur:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def execute(self, sql, params=None): conn.calls.append((sql, tuple(params or ())))
            def fetchall(self): return list(conn._rows)

        return _Cur()


@pytest.fixture(autouse=True)
def _isolated_cache():
    before = dict(mod._KARAKA_ROLE_CACHE)
    mod._KARAKA_ROLE_CACHE.clear()
    yield
    mod._KARAKA_ROLE_CACHE.clear()
    mod._KARAKA_ROLE_CACHE.update(before)


def _load_canonical(chart=CHART, ayan=AYAN):
    mod._activate_karaka_roles(chart, ayan, _FakeConn(_stored_rows()))


def _row(lord, parent_lord=None, system_id="vimshottari", chart=CHART, ayan=AYAN):
    return mod._build_row(
        chart, "build", ayan, system_id, 1 if parent_lord is None else 2, lord,
        mod.date(2000, 1, 1), mod.date(2001, 1, 1), None, parent_lord,
        "two_pass_verified", "ref", "Human citation",
    )


class TestReaderGolden:
    def test_stored_ranks_map_to_the_eight_scheme_abbreviations(self):
        got = mod._read_karaka_roles(_FakeConn(_stored_rows()), CHART, AYAN)
        assert got == CANONICAL_ROLES
        # rank 6 = Rahu = PK (not Jupiter); the old constant said Jupiter PK, Moon DK, Sun AK
        assert got["Rahu"] == "PK"
        assert got["Moon"] == "AK" and got["Mercury"] == "DK"
        assert [got[g] for g in ("Mars", "Rahu", "Jupiter", "Mercury")] == ["PiK", "PK", "GK", "DK"]
        assert tuple(got[g] for _, g in _RANKED) == KARAKA_ABBREVIATIONS_8

    def test_mapping_is_by_stored_rank_not_subject_label(self):
        # Pre-rebuild labels (rank 5 = PUTRAKARAKA ... rank 8 = STRIKARAKA) still map by rank.
        old = ["ATMAKARAKA", "AMATYAKARAKA", "BHRATRIKARAKA", "MATRIKARAKA",
               "PUTRAKARAKA", "GNATIKARAKA", "DARAKARAKA", "STRIKARAKA"]
        ranked = [(subj, g) for subj, (_, g) in zip(old, _RANKED)]
        assert mod._read_karaka_roles(_FakeConn(_stored_rows(ranked)), CHART, AYAN) == CANONICAL_ROLES

    def test_query_is_pinned_and_totally_ordered(self):
        conn = _FakeConn(_stored_rows())
        mod._read_karaka_roles(conn, CHART, AYAN)
        (sql, params), = conn.calls
        assert "fact_category = 'karaka_chara_position'" in sql
        assert "fact_key IN ('assigned_graha', 'karaka_rank')" in sql
        assert "formula_id = %s" in sql
        assert "ORDER BY fact_subject, fact_key, fact_id" in sql
        assert params == (CHART, AYAN, KARAKA_SCHOOL_KN_RAO) == (CHART, AYAN, "kn_rao_rahu_included")

    def test_absent_ga_sensitive_rows_raise_naming_the_dependency(self):
        with pytest.raises(mod.KarakaDependencyMissing, match="ga_sensitive"):
            mod._read_karaka_roles(_FakeConn([]), CHART, AYAN)

    def test_partial_duplicated_or_unpaired_rows_raise(self):
        rows = _stored_rows()
        with pytest.raises(mod.KarakaDependencyMissing, match="permutation"):
            mod._read_karaka_roles(_FakeConn(rows[:-2]), CHART, AYAN)
        with pytest.raises(mod.KarakaDependencyMissing, match="duplicated"):
            mod._read_karaka_roles(_FakeConn(rows + rows[:1]), CHART, AYAN)
        with pytest.raises(mod.KarakaDependencyMissing, match="malformed"):
            mod._read_karaka_roles(_FakeConn(rows + [("X", "assigned_graha", "Sun", None)]), CHART, AYAN)

    def test_non_graha_assignment_raises(self):
        ranked = list(_RANKED)
        ranked[7] = ("DARAKARAKA", "Ketu")  # Ketu is not a karaka-eligible graha
        with pytest.raises(mod.KarakaDependencyMissing, match="8 distinct grahas"):
            mod._read_karaka_roles(_FakeConn(_stored_rows(ranked)), CHART, AYAN)


class TestRolesAtPeriod:
    def test_golden_roles_for_lord(self):
        _load_canonical()
        assert mod._get_karaka_role(CHART, AYAN, "Moon") == "AK"
        assert mod._get_karaka_role(CHART, AYAN, "Mercury") == "DK"
        assert mod._get_karaka_role(CHART, AYAN, "Rahu") == "PK"
        assert mod._get_karaka_role(CHART, AYAN, "Ketu") is None  # no role in the 8-scheme
        row = _row("Moon")
        assert row["karaka_role_at_period"] == "AK"
        assert _row("Mercury")["karaka_role_at_period"] == "DK"
        assert _row("Rahu")["karaka_role_at_period"] == "PK"
        assert _row("Ketu")["karaka_role_at_period"] is None

    def test_old_constant_is_gone_and_old_values_are_not_reproduced(self):
        assert not hasattr(mod, "_JAIMINI_KARAKAS")
        _load_canonical()
        # the removed constant said Sun AK / Moon DK / Jupiter PK; this chart's own roles differ
        assert _row("Sun")["karaka_role_at_period"] == "BK"
        assert _row("Jupiter")["karaka_role_at_period"] == "GK"

    def test_karakas_active_uses_the_same_read_in_a_stated_order(self):
        _load_canonical()
        # Order = _KARAKAS_ACTIVE_GRAHA_ORDER (Sun Mars Mercury Saturn Jupiter Venus Moon Rahu),
        # not lord-first: lord Mercury, parent Moon -> Mercury before Moon.
        assert mod._get_karakas_active(CHART, AYAN, "Mercury", "Moon") == ["Mercury:DK", "Moon:AK"]
        assert mod._get_karakas_active(CHART, AYAN, "Moon", "Mercury") == ["Mercury:DK", "Moon:AK"]
        assert _row("Mercury", "Moon")["karakas_active_during_period"] == ["Mercury:DK", "Moon:AK"]
        # lord == parent_lord appears once; Ketu contributes nothing, Rahu is role-bearing
        assert mod._get_karakas_active(CHART, AYAN, "Jupiter", "Jupiter") == ["Jupiter:GK"]
        assert mod._get_karakas_active(CHART, AYAN, "Ketu", "Moon") == ["Moon:AK"]
        assert mod._get_karakas_active(CHART, AYAN, "Rahu", "Venus") == ["Venus:MK", "Rahu:PK"]
        assert mod._get_karakas_active(CHART, AYAN, "Ketu", None) == []
        assert _row("Ketu")["karakas_active_during_period"] is None

    def test_roles_differ_per_chart_and_ayanamsha(self):
        """No shared constant: the same lord gets each chart's / ayanamsha's own role,
        and a build of one key never reads another's."""
        swapped = [(s, {"Moon": "Sun", "Sun": "Moon"}.get(g, g)) for s, g in _RANKED]
        mod._activate_karaka_roles(CHART, AYAN, _FakeConn(_stored_rows()))
        mod._activate_karaka_roles("other-chart", AYAN, _FakeConn(_stored_rows(swapped)))
        mod._activate_karaka_roles(CHART, "raman", _FakeConn(_stored_rows(swapped)))
        assert _row("Moon")["karaka_role_at_period"] == "AK"
        assert _row("Moon", chart="other-chart")["karaka_role_at_period"] == "BK"
        assert _row("Moon", ayan="raman")["karaka_role_at_period"] == "BK"
        assert _row("Sun", chart="other-chart")["karaka_role_at_period"] == "AK"
        # interleaved: the first key is unchanged
        assert _row("Moon")["karaka_role_at_period"] == "AK"

    def test_every_build_reloads_its_own_key(self):
        """A ga_sensitive rebuild between two builds in one process is picked up."""
        _load_canonical()
        assert _row("Moon")["karaka_role_at_period"] == "AK"
        swapped = [(s, {"Moon": "Sun", "Sun": "Moon"}.get(g, g)) for s, g in _RANKED]
        mod._activate_karaka_roles(CHART, AYAN, _FakeConn(_stored_rows(swapped)))
        assert _row("Moon")["karaka_role_at_period"] == "BK"


class TestDependencyAndNullCases:
    def test_raises_when_ga_sensitive_rows_absent_and_a_role_is_needed(self):
        mod._activate_karaka_roles(CHART, AYAN, _FakeConn([]))  # records, does not raise yet
        with pytest.raises(mod.KarakaDependencyMissing, match="ga_sensitive"):
            _row("Moon")
        with pytest.raises(mod.KarakaDependencyMissing, match="ga_sensitive"):
            _row("Ketu", "Moon")  # a parent lord with a role also needs the read

    def test_raises_when_never_loaded(self):
        with pytest.raises(mod.KarakaDependencyMissing, match="never read"):
            _row("Moon")

    def test_database_errors_propagate_not_swallowed(self):
        class _Boom:
            def cursor(self, row_factory=None):
                raise RuntimeError("connection lost")

        with pytest.raises(RuntimeError, match="connection lost"):
            mod._activate_karaka_roles(CHART, AYAN, _Boom())

    @pytest.mark.parametrize("system_id,lord,parent", [
        ("yogini", "Mangala", None),
        ("yogini", "Pingala", "Mangala"),
        ("chara_karaka", "Aries", None),
        ("kalachakra", "Capricorn", "Aquarius"),
        ("narayana", "Libra", None),
    ])
    def test_yogini_and_sign_lords_stay_null_even_when_roles_are_loaded(self, system_id, lord, parent):
        _load_canonical()
        row = _row(lord, parent, system_id=system_id)
        assert row["karaka_role_at_period"] is None
        assert row["karakas_active_during_period"] is None
        assert "karaka_school" not in row["citation_human"]

    def test_yogini_and_sign_lords_need_no_ga_sensitive_read(self):
        # nothing loaded and nothing absent-recorded: a role-less system still builds
        assert _row("Mangala", None, system_id="yogini")["karaka_role_at_period"] is None
        assert _row("Aries", None, system_id="chara_karaka")["karakas_active_during_period"] is None
        assert _row("Ketu")["karaka_role_at_period"] is None  # a bare Ketu claims no role


class TestProvenance:
    def test_school_is_stamped_on_role_bearing_rows_only(self):
        _load_canonical()
        stamped = _row("Moon")["citation_human"]
        assert stamped == "Human citation; karaka_school=kn_rao_rahu_included (ga_sensitive karaka_chara_position)"
        # a Ketu row with a role-bearing parent carries a karakas_active claim: stamped
        assert "karaka_school=kn_rao_rahu_included" in _row("Ketu", "Moon")["citation_human"]
        # a bare Ketu row claims nothing: unchanged citation
        assert _row("Ketu")["citation_human"] == "Human citation"


_MOON_SID_DEG = 325.5
_BIRTH_JD = swe.julday(1984, 2, 5, 5.21667)


class TestVimshottariEndToEnd:
    def test_every_row_carries_the_chart_roles(self):
        _load_canonical()
        rows = mod.compute_vimshottari(_MOON_SID_DEG, _BIRTH_JD, AYAN, CHART, "build")
        assert rows
        by_id = {r["dasha_row_id"]: r for r in rows}
        for r in rows:
            lord = r["lord_graha"]
            assert r["karaka_role_at_period"] == CANONICAL_ROLES.get(lord)
            parent = by_id[r["parent_row_id"]]["lord_graha"] if r["parent_row_id"] else None
            expected = [
                f"{g}:{CANONICAL_ROLES[g]}"
                for g in ("Sun", "Mars", "Mercury", "Saturn", "Jupiter", "Venus", "Moon", "Rahu")
                if g in (lord, parent)
            ]
            assert r["karakas_active_during_period"] == (expected or None)
        assert {r["karaka_role_at_period"] for r in rows} == set(CANONICAL_ROLES.values()) | {None}
