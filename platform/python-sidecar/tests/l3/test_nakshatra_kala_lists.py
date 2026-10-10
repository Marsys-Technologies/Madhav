"""One canonical nakshatra spelling across Kala's five 27-name lists (SS N-471).

The L0 lexicon (`brahmagyan.l0_ontology` canonical_name_en == `l0_nakshatra` name_en, exposed
as `brahmagyan.nakshatra_vocabulary.CANONICAL_NAKSHATRA_NAMES`) spells nakshatra 5 / 19 / 23
Mrigasira / Moola / Dhanishtha. The L1 name table (`pyjhora_adapter._names`) wrote
Mrigashira / Mula / Dhanishta before it adopted the lexicon, so a stored natal fact can be in
EITHER spelling; every Kala reader must resolve both, and every Kala emitter must speak the
lexicon's. Each of the five lists is exercised through its REAL function (no database):

  1. services.ka_sangam.engine           _NAK_NAME_TO_IDX / _tara_score_for_nakshatra, and the
                                         writer's _resolve_native_chart_context (the live
                                         RuntimeError for a Moon in nakshatra 19 spelled Mula)
  2. pipeline.transit_search             NAKSHATRAS via _sign_nak
  3. services.kala_permission.permission period_lord_relation (tara from stored lord nakshatras)
  4. services.ka_graha_sancara.engine    NAKSHATRAS via _compute_live (emit-only, space-less)
  5. services.gochara_rules              ashtakavarga.NAKSHATRAS via p5d, p6.nakshatra_index

Nakshatras under test: 5 (Mrigasira), 19 (Moola), 23 (Dhanishtha), both spellings each.
"""
from __future__ import annotations

import sys
import types
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from brahmagyan.nakshatra_vocabulary import (  # noqa: E402
    CANONICAL_NAKSHATRA_NAMES,
    LEGACY_L1_SPELLINGS,
)

NAK_DEG = 360.0 / 27.0

# (nakshatra number, canonical spelling, legacy-L1 spelling)
CASES = [
    (5, "Mrigasira", "Mrigashira"),
    (19, "Moola", "Mula"),
    (23, "Dhanishtha", "Dhanishta"),
]
SPELLINGS = [
    pytest.param(n, spelling, id=f"{n}-{spelling}")
    for n, canon, legacy in CASES
    for spelling in (canon, legacy)
]
UNKNOWN_NAMES = ["Abhijit", "Mulaa", "Moolaa", "", "NotANakshatra"]


def test_case_table_matches_the_lexicon():
    """Guard the fixture itself: the canonical column is the lexicon, the legacy column is L1's."""
    for n, canon, legacy in CASES:
        assert CANONICAL_NAKSHATRA_NAMES[n - 1] == canon
        assert LEGACY_L1_SPELLINGS[legacy] == canon


# ═══════════════════════════════════════════════════════════════════════════
# 1. ka_sangam.engine -- _NAK_NAME_TO_IDX (Moon nakshatra -> janma idx) and tara score
# ═══════════════════════════════════════════════════════════════════════════

class _DictRowCursor:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.sql = sql

    def fetchall(self):
        return self._rows


class _MoonFactsConn:
    """psycopg3 dict_row-shaped chart_facts rows for fact_subject='MOON' (nakshatra + sign)."""

    def __init__(self, moon_nakshatra):
        self._rows = [{"fact_key": "sign", "fact_value_text": "Aquarius"}]
        if moon_nakshatra is not None:
            self._rows.append({"fact_key": "nakshatra", "fact_value_text": moon_nakshatra})

    def cursor(self):
        return _DictRowCursor(self._rows)


def _resolve_native_ctx(moon_nakshatra):
    from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter

    writer = KaSangamWriter.__new__(KaSangamWriter)
    birth_params = {"latitude_deg": 20.2961, "longitude_deg": 85.8245, "tz_offset_hours": 5.5}
    return writer._resolve_native_chart_context(
        _MoonFactsConn(moon_nakshatra), "482012f1-710e-4a25-994a-93821f5871aa", birth_params)


class TestKaSangamMoonNakshatraResolution:
    @pytest.mark.parametrize("n,spelling", SPELLINGS)
    def test_moon_in_nakshatra_resolves_under_either_spelling(self, n, spelling):
        ctx = _resolve_native_ctx(spelling)
        assert ctx.janma_nakshatra_idx == n - 1

    @pytest.mark.parametrize("n,spelling", SPELLINGS)
    def test_lookup_table_covers_the_spelling(self, n, spelling):
        from services.ka_sangam.engine import _NAK_NAME_TO_IDX, _NAKSHATRAS_ORDERED

        assert spelling in _NAK_NAME_TO_IDX
        assert _NAK_NAME_TO_IDX[spelling] == n - 1
        assert tuple(_NAKSHATRAS_ORDERED) == CANONICAL_NAKSHATRA_NAMES

    def test_every_canonical_name_resolves_to_its_own_index(self):
        from services.ka_sangam.engine import _NAK_NAME_TO_IDX

        for i, name in enumerate(CANONICAL_NAKSHATRA_NAMES):
            assert _NAK_NAME_TO_IDX[name] == i

    @pytest.mark.parametrize("name", UNKNOWN_NAMES + [None])
    def test_unknown_moon_nakshatra_still_raises_clearly(self, name):
        with pytest.raises(RuntimeError, match="could not resolve Moon nakshatra"):
            _resolve_native_ctx(name)

    @pytest.mark.parametrize("name", UNKNOWN_NAMES)
    def test_unknown_name_is_absent_from_the_table(self, name):
        from services.ka_sangam.engine import _NAK_NAME_TO_IDX

        assert name not in _NAK_NAME_TO_IDX


class TestKaSangamTaraScore:
    @pytest.mark.parametrize("n,spelling", SPELLINGS)
    def test_tara_score_is_spelling_independent(self, n, spelling):
        from services.ka_sangam.engine import _TARA_SCORES, _tara_score_for_nakshatra

        janma = 0  # Ashwini
        expected = _TARA_SCORES[((n - 1 - janma) % 9) + 1]
        assert expected > 0.0, "fixture must discriminate a resolved name from the unknown-name 0.0"
        assert _tara_score_for_nakshatra(spelling, janma) == expected

    def test_unknown_nakshatra_still_scores_zero(self):
        from services.ka_sangam.engine import _tara_score_for_nakshatra

        for name in UNKNOWN_NAMES:
            assert _tara_score_for_nakshatra(name, 0) == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 2. pipeline.transit_search.NAKSHATRAS (emitted by _sign_nak into event rows)
# ═══════════════════════════════════════════════════════════════════════════

class TestTransitSearchNakshatras:
    @pytest.mark.parametrize("n,canon,legacy", CASES)
    def test_sign_nak_emits_the_lexicon_spelling(self, n, canon, legacy):
        from pipeline.transit_search import _sign_nak

        lon = (n - 1) * NAK_DEG + 1.0  # one degree into the nakshatra
        _sign, nak = _sign_nak(lon)
        assert nak == canon
        assert nak != legacy

    def test_list_is_the_lexicon_in_order(self):
        from pipeline.transit_search import NAKSHATRAS

        assert tuple(NAKSHATRAS) == CANONICAL_NAKSHATRA_NAMES
        assert len(NAKSHATRAS) == 27
        for legacy in LEGACY_L1_SPELLINGS:
            assert legacy not in NAKSHATRAS

    def test_sign_nak_wraps_modulo_27_as_before(self):
        from pipeline.transit_search import _sign_nak

        assert _sign_nak(0.5)[1] == "Ashwini"
        assert _sign_nak(359.9)[1] == "Revati"


# ═══════════════════════════════════════════════════════════════════════════
# 3. kala_permission.permission -- tara from the MD/AD lords' stored natal nakshatras
# ═══════════════════════════════════════════════════════════════════════════

def _permission_fixtures():
    from tests.l3.test_kala_permission import FakeConn, _pos_rows

    return FakeConn, _pos_rows


_CHART = "482012f1-710e-4a25-994a-93821f5871aa"


class TestKalaPermissionTara:
    @pytest.mark.parametrize("n,spelling", SPELLINGS)
    def test_md_lord_in_nakshatra_resolves_tara(self, n, spelling):
        from panchang_engine.tara_bala import compute_tara_position, get_tara_detail
        from services.kala_permission.permission import period_lord_relation

        FakeConn, _pos_rows = _permission_fixtures()
        conn = FakeConn(position_rows={
            "JUP": _pos_rows("JUP", house_d1=1, nakshatra=spelling),   # the native's Jupiter is in Moola
            "VEN": _pos_rows("VEN", house_d1=4, nakshatra="Ashwini"),
        })
        result = period_lord_relation("Jupiter", "Venus", _CHART, conn=conn)
        assert not any("tara_unresolved" in f for f in result["judgment_flags"])
        detail = get_tara_detail(compute_tara_position(n, 1))
        assert result["tara"] == detail["name"]
        assert result["tara_score"] == detail["score"]

    @pytest.mark.parametrize("n,spelling", SPELLINGS)
    def test_ad_lord_in_nakshatra_resolves_tara(self, n, spelling):
        from panchang_engine.tara_bala import compute_tara_position, get_tara_detail
        from services.kala_permission.permission import period_lord_relation

        FakeConn, _pos_rows = _permission_fixtures()
        conn = FakeConn(position_rows={
            "SAT": _pos_rows("SAT", house_d1=1, nakshatra="Ashwini"),
            "MAR": _pos_rows("MAR", house_d1=8, nakshatra=spelling),
        })
        result = period_lord_relation("Saturn", "Mars", _CHART, conn=conn)
        assert not any("tara_unresolved" in f for f in result["judgment_flags"])
        assert result["tara"] == get_tara_detail(compute_tara_position(1, n))["name"]

    @pytest.mark.parametrize("n,canon,legacy", CASES)
    def test_both_spellings_give_the_identical_relation(self, n, canon, legacy):
        from services.kala_permission.permission import period_lord_relation

        FakeConn, _pos_rows = _permission_fixtures()

        def run(spelling):
            conn = FakeConn(position_rows={
                "JUP": _pos_rows("JUP", house_d1=1, nakshatra=spelling),
                "MER": _pos_rows("MER", house_d1=2, nakshatra="Pushya"),
            })
            return period_lord_relation("Jupiter", "Mercury", _CHART, conn=conn)

        def stable(result):  # fact_ids cite the per-spelling fixture rows, not the algebra
            return {k: v for k, v in result.items() if k != "fact_ids"}

        assert stable(run(canon)) == stable(run(legacy))
        assert run(canon)["tara"] is not None

    @pytest.mark.parametrize("name", ["Abhijit", "Mulaa", "NotANakshatra"])
    def test_unknown_nakshatra_still_flags_tara_unresolved(self, name):
        from services.kala_permission.permission import period_lord_relation

        FakeConn, _pos_rows = _permission_fixtures()
        conn = FakeConn(position_rows={
            "JUP": _pos_rows("JUP", house_d1=1, nakshatra=name),
            "VEN": _pos_rows("VEN", house_d1=4, nakshatra="Ashwini"),
        })
        result = period_lord_relation("Jupiter", "Venus", _CHART, conn=conn)
        assert result["tara"] is None
        assert any("tara_unresolved" in f for f in result["judgment_flags"])

    def test_names_constant_is_the_lexicon(self):
        from services.kala_permission.permission import NAKSHATRA_NAMES_27

        assert tuple(NAKSHATRA_NAMES_27) == CANONICAL_NAKSHATRA_NAMES


# ═══════════════════════════════════════════════════════════════════════════
# 4. ka_graha_sancara.engine.NAKSHATRAS -- emit-only, SPACE-LESS convention
# ═══════════════════════════════════════════════════════════════════════════

# Exactly what the service emitted before this change (index = nakshatra number - 1).
_OLD_EMITTED = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "PurvaPhalguni", "UttaraPhalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "PurvaAshadha", "UttaraAshadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "PurvaBhadrapada", "UttaraBhadrapada", "Revati",
)


@contextmanager
def _fake_transit_states(monkeypatch, nakshatra_number_for_all):
    lon = (nakshatra_number_for_all - 1) * NAK_DEG + 1.0
    pkg = types.ModuleType("temporal")
    pkg.__path__ = []  # behave as a package
    mod = types.ModuleType("temporal.compute_transits")

    def get_transit_states(query_dt, q_date, ayanamsha="lahiri"):
        return {"planets": {
            g: {"sidereal_lon_deg": lon, "speed_deg_per_day": 1.0, "is_retrograde": False}
            for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")}}

    mod.get_transit_states = get_transit_states
    pkg.compute_transits = mod
    monkeypatch.setitem(sys.modules, "temporal", pkg)
    monkeypatch.setitem(sys.modules, "temporal.compute_transits", mod)
    yield


class TestGrahaSancaraNakshatras:
    @pytest.mark.parametrize("n,canon,legacy", CASES)
    def test_live_path_emits_lexicon_spelling_spaceless(self, monkeypatch, n, canon, legacy):
        from services.ka_graha_sancara.engine import _compute_live

        with _fake_transit_states(monkeypatch, n):
            grahas = _compute_live(datetime(2026, 10, 11, tzinfo=timezone.utc), "lahiri")
        for state in grahas.values():
            assert state.nakshatra == canon.replace(" ", "")
            assert state.nakshatra_idx == n - 1

    def test_only_the_three_spelling_differences_change_the_output(self):
        from services.ka_graha_sancara.engine import NAKSHATRAS

        assert len(NAKSHATRAS) == 27
        changed = {i + 1: (old, new) for i, (old, new) in enumerate(zip(_OLD_EMITTED, NAKSHATRAS)) if old != new}
        assert changed == {
            5: ("Mrigashira", "Mrigasira"),
            19: ("Mula", "Moola"),
            23: ("Dhanishta", "Dhanishtha"),
        }

    def test_spacing_convention_is_kept(self):
        from services.ka_graha_sancara.engine import NAKSHATRAS

        assert all(" " not in name for name in NAKSHATRAS)
        assert "PurvaPhalguni" in NAKSHATRAS and "PurvaBhadrapada" in NAKSHATRAS


# ═══════════════════════════════════════════════════════════════════════════
# 5. gochara_rules -- ashtakavarga.NAKSHATRAS (p5d) and p6.nakshatra_index
# ═══════════════════════════════════════════════════════════════════════════

class TestGocharaRulesNakshatras:
    @pytest.mark.parametrize("n,canon,legacy", CASES)
    def test_p5d_names_the_nakshatra_in_the_lexicon_spelling(self, n, canon, legacy):
        from services.gochara_rules.ashtakavarga import p5d

        out = p5d(n, 1)  # (n * 1) % 27 = n
        assert out["state"] == "resolved"
        assert out["nakshatra_index"] == n
        assert out["nakshatra"] == canon

    @pytest.mark.parametrize("n,spelling", SPELLINGS)
    def test_nakshatra_index_resolves_either_spelling(self, n, spelling):
        from services.gochara_rules.p6 import nakshatra_index

        assert nakshatra_index(spelling) == n
        assert nakshatra_index(f"  {spelling.upper()} ") == n  # existing normalisation kept

    def test_nakshatra_index_roundtrips_every_canonical_name(self):
        from services.gochara_rules.p6 import nakshatra_index

        for i, name in enumerate(CANONICAL_NAKSHATRA_NAMES, start=1):
            assert nakshatra_index(name) == i
            assert nakshatra_index(name.replace(" ", "")) == i

    @pytest.mark.parametrize("name", [n for n in UNKNOWN_NAMES])
    def test_unknown_name_still_raises_value_error(self, name):
        from services.gochara_rules.p6 import nakshatra_index

        with pytest.raises(ValueError, match="unknown nak"):
            nakshatra_index(name)

    def test_non_string_still_raises_type_error(self):
        from services.gochara_rules.p6 import nakshatra_index

        with pytest.raises(TypeError):
            nakshatra_index(5)
