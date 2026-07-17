"""
tests/l3/test_kala_permission.py — wave/D-3/T-4 PERMISSION lock tests.

Covers:
  1. CR-87 — chart_id (and the other required params) must raise, never
     default/guess.
  2. Period-lord relational algebra type specimens — a kendra pair, a
     dusthana pair, a tara favorable/unfavorable pair (real classical
     nakshatra math via the reused panchang_engine.tara_bala helpers, driven
     through a fake DB connection so no live DB is required — same "pass
     contexts directly, no live DB where avoidable" discipline as
     tests/test_cr87_native_chart_context.py).
  3. Gate-multiplier behavior — low cross-system dasha concordance
     measurably suppresses permission_score vs high concordance, holding
     every other input fixed (proves §2 is a genuine multiplicative gate,
     not a decorative pass-through).
  4. Dasha-lord-capability wiring — a high-warning lord measurably lowers
     capability_term / permission_score vs a clean lord.
  5. Spine-not-found honesty — an unresolvable (md_lord, ad_lord, as_of)
     triple is flagged, not silently treated as fully grounded.

No live DB, no swisseph. `conn` is a hand-rolled fake that routes on SQL
substrings — the same "pass contexts directly to engine functions, avoid a
live DB where avoidable" discipline CR-87's own regression suite uses.
"""
from __future__ import annotations

import os
import sys
from datetime import date
from unittest.mock import MagicMock

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.kala_permission.permission import (  # noqa: E402
    NAKSHATRA_NAMES_27,
    PLANET_TO_SUBJECT,
    _classify_bhava_relation_from_lord,
    compute_permission,
    lord_capability,
    period_lord_relation,
)
from services.ph_nimitta.dasha_consensus import DashaConsensusResult  # noqa: E402

_ABHISEK_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
_ABHINANDAN_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


# ═══════════════════════════════════════════════════════════════════════════
# Fake DB connection — routes conn.execute(sql, params) on SQL substrings.
# ═══════════════════════════════════════════════════════════════════════════

class _FakeCursor:
    def __init__(self, fetchone_val=None, fetchall_val=None):
        self._one = fetchone_val
        self._all = fetchall_val or []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


class FakeConn:
    """Routes each conn.execute() call based on which table/clause the SQL
    text references. `spine_row`, `shadbala_rows`, `vichara_row`,
    `ratif_row`, `position_rows` are all caller-configurable per-test."""

    def __init__(
        self,
        spine_row=None,
        position_rows: dict[str, dict] | None = None,
        shadbala_rows: dict[str, tuple] | None = None,
        vichara_rows: dict[str, tuple] | None = None,
        ratif_rows: dict[str, tuple] | None = None,
    ):
        self.spine_row = spine_row
        self.position_rows = position_rows or {}
        self.shadbala_rows = shadbala_rows or {}
        self.vichara_rows = vichara_rows or {}
        self.ratif_rows = ratif_rows or {}
        self.calls: list[str] = []

    def execute(self, sql: str, params: list):
        self.calls.append(sql)
        if "JOIN chart_dashas ad" in sql:
            return _FakeCursor(fetchone_val=self.spine_row)
        if "graha_position" in sql and "house_d1" in sql:
            subject = params[2]
            row = self.position_rows.get(subject)
            return _FakeCursor(fetchall_val=row or [])
        if "graha_shadbala_total" in sql:
            subject = params[2]
            return _FakeCursor(fetchone_val=self.shadbala_rows.get(subject))
        if "valence_pass" in sql:
            subject = params[2]
            return _FakeCursor(fetchone_val=self.vichara_rows.get(subject))
        if "varga_ratification" in sql:
            subject = params[2]
            return _FakeCursor(fetchone_val=self.ratif_rows.get(subject))
        raise AssertionError(f"FakeConn: unrouted SQL: {sql[:80]}")


def _pos_rows(subject: str, house_d1: int, nakshatra: str) -> list:
    return [
        ("house_d1", float(house_d1), None, f"fact-house-{subject}"),
        ("nakshatra", None, nakshatra, f"fact-nak-{subject}"),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# 1. CR-87 — required params, no defaults
# ═══════════════════════════════════════════════════════════════════════════

class TestCR87RequiredParams:
    def test_missing_chart_id_raises(self):
        with pytest.raises(ValueError, match="chart_id is required"):
            compute_permission(
                chart_id="", md_lord="Jupiter", ad_lord="Venus",
                as_of=date(2027, 1, 1), conn=FakeConn(),
            )

    def test_none_chart_id_raises(self):
        with pytest.raises(ValueError, match="chart_id is required"):
            compute_permission(
                chart_id=None, md_lord="Jupiter", ad_lord="Venus",
                as_of=date(2027, 1, 1), conn=FakeConn(),
            )

    def test_missing_md_lord_raises(self):
        with pytest.raises(ValueError, match="md_lord and ad_lord"):
            compute_permission(
                chart_id=_ABHISEK_CHART_ID, md_lord="", ad_lord="Venus",
                as_of=date(2027, 1, 1), conn=FakeConn(),
            )

    def test_missing_as_of_raises(self):
        with pytest.raises(ValueError, match="as_of is required"):
            compute_permission(
                chart_id=_ABHISEK_CHART_ID, md_lord="Jupiter", ad_lord="Venus",
                as_of=None, conn=FakeConn(),
            )

    def test_missing_conn_raises(self):
        with pytest.raises(ValueError, match="conn is required"):
            compute_permission(
                chart_id=_ABHISEK_CHART_ID, md_lord="Jupiter", ad_lord="Venus",
                as_of=date(2027, 1, 1), conn=None,
            )

    def test_period_lord_relation_also_requires_chart_id(self):
        with pytest.raises(ValueError, match="chart_id is required"):
            period_lord_relation("Jupiter", "Venus", "", conn=FakeConn())


# ═══════════════════════════════════════════════════════════════════════════
# 2. Period-lord relational algebra type specimens
# ═══════════════════════════════════════════════════════════════════════════

class TestBhavaClassification:
    """Pure-function specimens for _classify_bhava_relation_from_lord."""

    def test_same_house_is_kendra_trikona(self):
        assert _classify_bhava_relation_from_lord(1) == "kendra_trikona"

    def test_house_4_is_kendra(self):
        assert _classify_bhava_relation_from_lord(4) == "kendra"

    def test_house_7_is_kendra(self):
        assert _classify_bhava_relation_from_lord(7) == "kendra"

    def test_house_5_is_trikona(self):
        assert _classify_bhava_relation_from_lord(5) == "trikona"

    def test_house_8_is_dusthana(self):
        assert _classify_bhava_relation_from_lord(8) == "dusthana"

    def test_house_12_is_dusthana(self):
        assert _classify_bhava_relation_from_lord(12) == "dusthana"

    def test_house_2_is_neutral(self):
        assert _classify_bhava_relation_from_lord(2) == "neutral"


class TestPeriodLordRelationSpecimens:
    """Worked specimens through period_lord_relation() with a fake conn.

    Chart-facts values below are SYNTHETIC (clearly labeled) — not queried
    from a live DB, since this lane's test suite avoids a live DB where
    avoidable (CR-87 test precedent). House/nakshatra numbers are chosen to
    produce known classical relations, not derived from the real chart.
    """

    def test_kendra_pair(self):
        # MD-lord in H1, AD-lord in H4 (from MD-lord) -> kendra.
        conn = FakeConn(position_rows={
            "JUP": _pos_rows("JUP", house_d1=1, nakshatra="Ashwini"),
            "VEN": _pos_rows("VEN", house_d1=4, nakshatra="Ashwini"),
        })
        result = period_lord_relation("Jupiter", "Venus", _ABHISEK_CHART_ID, conn=conn)
        assert result["relative_house"] == 4
        assert result["relation"] == "kendra"

    def test_dusthana_pair(self):
        # MD-lord in H2, AD-lord in H8 (from MD-lord: (8-2)%12+1 = 7 -> kendra).
        # Recompute for an actual dusthana outcome: MD-lord H1, AD-lord H8.
        conn = FakeConn(position_rows={
            "SAT": _pos_rows("SAT", house_d1=1, nakshatra="Ashwini"),
            "MAR": _pos_rows("MAR", house_d1=8, nakshatra="Ashwini"),
        })
        result = period_lord_relation("Saturn", "Mars", _ABHISEK_CHART_ID, conn=conn)
        assert result["relative_house"] == 8
        assert result["relation"] == "dusthana"

    def test_tara_favorable_specimen(self):
        # MD-lord natal nakshatra = Ashwini (id 1), AD-lord natal nakshatra =
        # Pushya (id 8). tara_count = ((8-1) % 27) + 1 = 8 -> tara position
        # 8 = "Mitra" (auspicious) per panchang_engine.tara_bala._TARA_QUALITY.
        conn = FakeConn(position_rows={
            "JUP": _pos_rows("JUP", house_d1=1, nakshatra="Ashwini"),
            "MER": _pos_rows("MER", house_d1=2, nakshatra="Pushya"),
        })
        result = period_lord_relation("Jupiter", "Mercury", _ABHISEK_CHART_ID, conn=conn)
        assert result["tara"] == "Mitra"
        assert result["tara_quality"] == "auspicious"
        assert result["tara_favorable"] is True

    def test_tara_unfavorable_specimen(self):
        # MD-lord natal nakshatra = Ashwini (id 1), AD-lord natal nakshatra =
        # Krittika (id 3). tara_count = ((3-1) % 27) + 1 = 3 -> tara position
        # 3 = "Vipat" (inauspicious).
        conn = FakeConn(position_rows={
            "JUP": _pos_rows("JUP", house_d1=1, nakshatra="Ashwini"),
            "SUN": _pos_rows("SUN", house_d1=2, nakshatra="Krittika"),
        })
        result = period_lord_relation("Jupiter", "Sun", _ABHISEK_CHART_ID, conn=conn)
        assert result["tara"] == "Vipat"
        assert result["tara_quality"] == "inauspicious"
        assert result["tara_favorable"] is False

    def test_unresolved_flagged_not_fabricated(self):
        conn = FakeConn(position_rows={})  # no rows for either lord
        result = period_lord_relation("Jupiter", "Venus", _ABHISEK_CHART_ID, conn=conn)
        assert result["relation"] == "unresolved"
        assert result["relative_house"] is None
        assert any("bhava_relation_unresolved" in f for f in result["judgment_flags"])
        assert any("tara_unresolved" in f for f in result["judgment_flags"])

    def test_all_27_nakshatra_names_match_the_shared_ordering(self):
        """Sanity: the copied NAKSHATRA_NAMES_27 constant is the canonical
        27-name ordering (Ashwini first, Revati last) — a drift here would
        silently break every tara computation."""
        assert len(NAKSHATRA_NAMES_27) == 27
        assert NAKSHATRA_NAMES_27[0] == "Ashwini"
        assert NAKSHATRA_NAMES_27[-1] == "Revati"
        assert NAKSHATRA_NAMES_27[24] == "Purva Bhadrapada"  # FORENSIC anchor, §B


# ═══════════════════════════════════════════════════════════════════════════
# 3. Gate-multiplier behavior
# ═══════════════════════════════════════════════════════════════════════════

class TestConcordanceGateSuppressesPermission:
    """Low cross-system dasha concordance must measurably suppress
    permission_score relative to high concordance, holding spine/relation/
    capability fixed — proving the gate is multiplicative on the WHOLE
    score, not one nudge among many."""

    def _base_conn(self):
        spine_row = ("md-row-1", date(2020, 1, 1), date(2036, 1, 1),
                     "ad-row-1", date(2027, 1, 1), date(2028, 6, 1))
        return FakeConn(
            spine_row=spine_row,
            position_rows={
                "JUP": _pos_rows("JUP", house_d1=1, nakshatra="Ashwini"),
                "VEN": _pos_rows("VEN", house_d1=1, nakshatra="Ashwini"),  # kendra_trikona, tara=Janma(neutral)
            },
            shadbala_rows={"JUP": ("sb-jup", 5.0), "VEN": ("sb-ven", 5.0)},
            vichara_rows={},
            ratif_rows={},
        )

    def _run_with_consensus(self, monkeypatch, count: int, confidence: float, high: bool):
        conn = self._base_conn()
        fake_result = DashaConsensusResult(
            count=count, systems_agreeing=["vimshottari"] * count,
            confidence_multiplier=confidence, high_agreement=high,
            all_systems_checked=sorted(
                {"vimshottari", "yogini", "ashtottari", "chara_karaka",
                 "naisargika", "mudda", "kalachakra"}
            ),
        )
        monkeypatch.setattr(
            "services.kala_permission.permission.derive_dasha_consensus",
            lambda **kwargs: fake_result,
        )
        return compute_permission(
            chart_id=_ABHISEK_CHART_ID, md_lord="Jupiter", ad_lord="Venus",
            as_of=date(2027, 6, 1), conn=conn,
        )

    def test_low_agreement_suppresses_relative_to_high_agreement(self, monkeypatch):
        low = self._run_with_consensus(monkeypatch, count=1, confidence=0.5, high=False)
        high = self._run_with_consensus(monkeypatch, count=7, confidence=1.0, high=True)

        assert low["gate_multiplier"] == pytest.approx(0.5)
        assert high["gate_multiplier"] == pytest.approx(1.0)
        assert low["permission_score"] < high["permission_score"]
        # Exact ratio: gate_multiplier is the ONLY thing that differs between
        # these two calls, so permission_score must scale by exactly 0.5/1.0.
        assert low["permission_score"] == pytest.approx(high["permission_score"] * 0.5)
        assert any("low_dasha_concordance" in f for f in low["judgment_flags"])

    def test_low_agreement_flag_absent_when_high(self, monkeypatch):
        high = self._run_with_consensus(monkeypatch, count=7, confidence=1.0, high=True)
        assert not any("low_dasha_concordance" in f for f in high["judgment_flags"])


# ═══════════════════════════════════════════════════════════════════════════
# 4. Dasha-lord-capability wiring
# ═══════════════════════════════════════════════════════════════════════════

class TestLordCapabilityWiring:
    def test_high_warning_lord_lowers_capability_term(self, monkeypatch):
        spine_row = ("md-row-1", date(2020, 1, 1), date(2036, 1, 1),
                     "ad-row-1", date(2027, 1, 1), date(2028, 6, 1))
        position_rows = {
            "JUP": _pos_rows("JUP", house_d1=1, nakshatra="Ashwini"),
            "VEN": _pos_rows("VEN", house_d1=1, nakshatra="Ashwini"),
        }
        clean_conn = FakeConn(
            spine_row=spine_row, position_rows=position_rows,
            shadbala_rows={"JUP": ("sb-jup", 5.0), "VEN": ("sb-ven", 5.0)},
            vichara_rows={}, ratif_rows={},
        )
        # AD-lord (Venus) is a dusthana_lord + functional malefic + low
        # ratification -> warning_score should hit the max (3 of the 3
        # scorable-without-percentile terms; shadbala percentile is not
        # computable at single-lord scope, see lord_capability()'s docstring).
        warned_conn = FakeConn(
            spine_row=spine_row, position_rows=position_rows,
            shadbala_rows={"JUP": ("sb-jup", 5.0), "VEN": ("sb-ven", 5.0)},
            vichara_rows={
                "VEN": ("dusthana_lord", "temporal_malefic", ["vf-1"]),
            },
            ratif_rows={"VEN": (0.5, ["career"])},
        )

        fake_result = DashaConsensusResult(
            count=7, systems_agreeing=["vimshottari"], confidence_multiplier=1.0,
            high_agreement=True, all_systems_checked=[],
        )
        monkeypatch.setattr(
            "services.kala_permission.permission.derive_dasha_consensus",
            lambda **kwargs: fake_result,
        )

        clean = compute_permission(
            chart_id=_ABHISEK_CHART_ID, md_lord="Jupiter", ad_lord="Venus",
            as_of=date(2027, 6, 1), conn=clean_conn,
        )
        warned = compute_permission(
            chart_id=_ABHISEK_CHART_ID, md_lord="Jupiter", ad_lord="Venus",
            as_of=date(2027, 6, 1), conn=warned_conn,
        )

        assert warned["dasha_lord_capability"]["ad_lord"]["warning_tier"] in ("elevated", "high")
        assert warned["components"]["capability_term"] < clean["components"]["capability_term"]
        assert warned["permission_score"] < clean["permission_score"]

    def test_lord_capability_direct_call(self):
        conn = FakeConn(
            shadbala_rows={"SAT": ("sb-sat", 3.2)},
            vichara_rows={"SAT": ("maraka", "natural_malefic", ["vf-2"])},
            ratif_rows={"SAT": (0.8, ["health"])},
        )
        cap = lord_capability(conn, _ABHISEK_CHART_ID, "lahiri_chitrapaksha", "Saturn")
        assert cap["lord"] == "Saturn"
        assert cap["lord_subject"] == PLANET_TO_SUBJECT["Saturn"]
        assert cap["house_class"] == "maraka"
        assert cap["warning_tier"] in ("elevated", "high")
        assert "sb-sat" in cap["fact_ids"]

    def test_lord_capability_requires_chart_id(self):
        with pytest.raises(ValueError, match="chart_id is required"):
            lord_capability(FakeConn(), "", "lahiri_chitrapaksha", "Saturn")


# ═══════════════════════════════════════════════════════════════════════════
# 5. Spine-not-found honesty
# ═══════════════════════════════════════════════════════════════════════════

class TestSpineNotFound:
    def test_unresolvable_spine_discounts_and_flags(self, monkeypatch):
        conn = FakeConn(
            spine_row=None,  # no chart_dashas row-pair matches
            position_rows={
                "JUP": _pos_rows("JUP", house_d1=1, nakshatra="Ashwini"),
                "VEN": _pos_rows("VEN", house_d1=1, nakshatra="Ashwini"),
            },
            shadbala_rows={"JUP": ("sb-jup", 5.0), "VEN": ("sb-ven", 5.0)},
        )
        fake_result = DashaConsensusResult(
            count=7, systems_agreeing=[], confidence_multiplier=1.0,
            high_agreement=True, all_systems_checked=[],
        )
        monkeypatch.setattr(
            "services.kala_permission.permission.derive_dasha_consensus",
            lambda **kwargs: fake_result,
        )
        result = compute_permission(
            chart_id=_ABHISEK_CHART_ID, md_lord="Jupiter", ad_lord="Venus",
            as_of=date(2099, 1, 1), conn=conn,
        )
        assert result["components"]["spine_found"] is False
        assert result["components"]["base_spine_strength"] == pytest.approx(0.3)
        assert any("spine_not_found" in f for f in result["judgment_flags"])
        # Still produces a bounded score, never fabricates a "fully grounded" 1.0 spine term.
        assert 0.0 <= result["permission_score"] <= 1.0


# ═══════════════════════════════════════════════════════════════════════════
# 6. Two-chart shape sanity (CR-87 spirit: two different chart_ids driven
#    through the same function must not silently collapse to one identity —
#    here proven by asserting each call is scoped by the chart_id it was
#    given, via the FakeConn call log, since the fake has no real per-chart
#    data to diverge on numerically).
# ═══════════════════════════════════════════════════════════════════════════

class TestTwoChartIdentityNotCollapsed:
    def test_chart_id_actually_threaded_into_queries(self, monkeypatch):
        conn = FakeConn(
            spine_row=("md-row-1", date(2020, 1, 1), date(2036, 1, 1),
                       "ad-row-1", date(2027, 1, 1), date(2028, 6, 1)),
            position_rows={
                "JUP": _pos_rows("JUP", house_d1=1, nakshatra="Ashwini"),
                "VEN": _pos_rows("VEN", house_d1=1, nakshatra="Ashwini"),
            },
            shadbala_rows={"JUP": ("sb-jup", 5.0), "VEN": ("sb-ven", 5.0)},
        )
        seen_chart_ids: list[str] = []
        orig_execute = conn.execute

        def _spy_execute(sql, params):
            seen_chart_ids.append(params[0])
            return orig_execute(sql, params)
        conn.execute = _spy_execute

        fake_result = DashaConsensusResult(
            count=7, systems_agreeing=[], confidence_multiplier=1.0,
            high_agreement=True, all_systems_checked=[],
        )
        monkeypatch.setattr(
            "services.kala_permission.permission.derive_dasha_consensus",
            lambda **kwargs: fake_result,
        )
        compute_permission(
            chart_id=_ABHINANDAN_CHART_ID, md_lord="Jupiter", ad_lord="Venus",
            as_of=date(2027, 6, 1), conn=conn,
        )
        assert seen_chart_ids, "no queries were made"
        assert all(cid == _ABHINANDAN_CHART_ID for cid in seen_chart_ids), (
            "CR-87 shape: every query must be scoped to the caller-supplied "
            "chart_id, never a different/default chart."
        )
