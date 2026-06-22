"""
test_u1_dasha_consensus.py — U1 acceptance tests (no live DB; all calls mocked).

Covers U1 acceptance criteria §5:
  AC1: correct distinct-system count from known multi-system window
  AC2: dasha_consensus_systems lists actual concurring systems
  AC3: derivation goes through KaDashaKalaService (no chart_dashas tree-walk)
  AC4: single-system window yields count=1 (floor=1)
  AC5: (prod verification — deferred to integration suite)
  AC6: no new column written; anti-drift (unit-level: no import of chart_dashas writer)
  AC7: consensus via existing service chain only
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_window(system_id: str, count: int, systems: list[str]):
    w = MagicMock()
    w.cross_dasha_agreement.count = count
    w.cross_dasha_agreement.systems_agreeing = systems
    w.system_id = system_id
    return w


def _svc_result(windows):
    r = MagicMock()
    r.windows = windows
    return r


CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYANAMSHA = "lahiri"
TARGET_LORDS = {"Mercury", "Venus"}
W_START = date(2026, 1, 1)
W_END = date(2026, 6, 30)


# ── AC1 + AC2: multi-system window returns correct count + systems ─────────────

class TestMultiSystemConsensus:
    def test_four_systems_agree(self):
        from services.ph_nimitta.dasha_consensus import derive_dasha_consensus
        windows = [
            _make_window("vimshottari", 4, ["vimshottari","yogini","ashtottari","chara_karaka"]),
            _make_window("yogini",      4, ["vimshottari","yogini","ashtottari","chara_karaka"]),
            _make_window("ashtottari",  4, ["vimshottari","yogini","ashtottari","chara_karaka"]),
            _make_window("chara_karaka",4, ["vimshottari","yogini","ashtottari","chara_karaka"]),
        ]
        mock_conn = MagicMock()
        with patch("services.ka_dasha_kala.service.KaDashaKalaService") as MockSvc:
            MockSvc.return_value.query.return_value = _svc_result(windows)
            result = derive_dasha_consensus(mock_conn, CHART_ID, AYANAMSHA, TARGET_LORDS, W_START, W_END)

        assert result.count == 4
        assert set(result.systems_agreeing) == {"vimshottari","yogini","ashtottari","chara_karaka"}
        assert result.high_agreement is True

    def test_two_systems_agree(self):
        from services.ph_nimitta.dasha_consensus import derive_dasha_consensus
        windows = [
            _make_window("vimshottari", 2, ["vimshottari","mudda"]),
            _make_window("mudda",       2, ["vimshottari","mudda"]),
        ]
        mock_conn = MagicMock()
        with patch("services.ka_dasha_kala.service.KaDashaKalaService") as MockSvc:
            MockSvc.return_value.query.return_value = _svc_result(windows)
            result = derive_dasha_consensus(mock_conn, CHART_ID, AYANAMSHA, TARGET_LORDS, W_START, W_END)

        assert result.count == 2
        assert "vimshottari" in result.systems_agreeing
        assert "mudda" in result.systems_agreeing
        assert result.high_agreement is False

    def test_all_seven_agree(self):
        from services.ph_nimitta.dasha_consensus import derive_dasha_consensus, ALL_7_SYSTEMS
        all_sys = sorted(ALL_7_SYSTEMS)
        windows = [_make_window(s, 7, all_sys) for s in all_sys]
        mock_conn = MagicMock()
        with patch("services.ka_dasha_kala.service.KaDashaKalaService") as MockSvc:
            MockSvc.return_value.query.return_value = _svc_result(windows)
            result = derive_dasha_consensus(mock_conn, CHART_ID, AYANAMSHA, TARGET_LORDS, W_START, W_END)

        assert result.count == 7
        assert set(result.systems_agreeing) == ALL_7_SYSTEMS
        assert result.high_agreement is True
        assert result.confidence_multiplier == 1.0


# ── AC4: single-system window → floor=1 ──────────────────────────────────────

class TestFloorBehavior:
    def test_single_system_yields_count_one(self):
        from services.ph_nimitta.dasha_consensus import derive_dasha_consensus
        windows = [_make_window("vimshottari", 1, ["vimshottari"])]
        mock_conn = MagicMock()
        with patch("services.ka_dasha_kala.service.KaDashaKalaService") as MockSvc:
            MockSvc.return_value.query.return_value = _svc_result(windows)
            result = derive_dasha_consensus(mock_conn, CHART_ID, AYANAMSHA, TARGET_LORDS, W_START, W_END)

        assert result.count == 1
        assert result.high_agreement is False

    def test_empty_windows_yields_count_zero(self):
        from services.ph_nimitta.dasha_consensus import derive_dasha_consensus
        mock_conn = MagicMock()
        with patch("services.ka_dasha_kala.service.KaDashaKalaService") as MockSvc:
            MockSvc.return_value.query.return_value = _svc_result([])
            result = derive_dasha_consensus(mock_conn, CHART_ID, AYANAMSHA, TARGET_LORDS, W_START, W_END)

        assert result.count == 0
        assert result.systems_agreeing == []


# ── AC3: derivation goes through KaDashaKalaService, no direct tree-walk ──────

class TestServiceOnlyPath:
    def test_uses_ka_dasha_kala_service(self):
        from services.ph_nimitta.dasha_consensus import derive_dasha_consensus
        mock_conn = MagicMock()
        with patch("services.ka_dasha_kala.service.KaDashaKalaService") as MockSvc:
            MockSvc.return_value.query.return_value = _svc_result([])
            derive_dasha_consensus(mock_conn, CHART_ID, AYANAMSHA, TARGET_LORDS, W_START, W_END)
            MockSvc.assert_called_once_with(mock_conn)
            MockSvc.return_value.query.assert_called_once()

    def test_no_chart_dashas_direct_import(self):
        """AC3/AC7: dasha_consensus must not re-derive a dāśā tree-walk."""
        from pathlib import Path
        # platform/python-sidecar/tests/test_u1_dasha_consensus.py → parents[3] = repo root
        _REPO_ROOT = Path(__file__).resolve().parents[3]
        path = str(
            _REPO_ROOT / "platform" / "python-sidecar" / "services" / "ph_nimitta" / "dasha_consensus.py"
        )
        with open(path) as f:
            source = f.read()
        # Must not re-implement the dāśā tree-walk (the L1 internals)
        assert "walk_eligible_intervals" not in source, \
            "dasha_consensus must not call walk_eligible_intervals directly (AC3/AC7)"
        # Must not write to L1 or L3 tables directly
        assert "INSERT INTO chart_dashas" not in source, \
            "dasha_consensus must not write to chart_dashas (AC6 anti-drift)"
        assert "INSERT INTO kala_convergence" not in source, \
            "dasha_consensus must not write to kala_convergence (AC6 anti-drift)"


# ── G-LADDER confidence multiplier (D21) ──────────────────────────────────────

class TestGLadderMultiplier:
    @pytest.mark.parametrize("count,expected_mult", [
        (0, 0.5),   # 0/7=0 → floor at 0.5
        (1, 0.5),   # 1/7≈0.143 → floor at 0.5
        (3, 0.5),   # 3/7≈0.429 → floor at 0.5
        (4, pytest.approx(4/7, rel=0.01)),  # 4/7≈0.571 > 0.5
        (7, 1.0),   # 7/7=1.0
    ])
    def test_g_ladder_multiplier(self, count, expected_mult):
        from services.ph_nimitta.dasha_consensus import derive_dasha_consensus
        windows = [_make_window("vimshottari", count, ["vimshottari"] * max(1, count))]
        mock_conn = MagicMock()
        with patch("services.ka_dasha_kala.service.KaDashaKalaService") as MockSvc:
            MockSvc.return_value.query.return_value = _svc_result(windows)
            result = derive_dasha_consensus(mock_conn, CHART_ID, AYANAMSHA, TARGET_LORDS, W_START, W_END)

        assert 0.5 <= result.confidence_multiplier <= 1.0
        assert result.confidence_multiplier == pytest.approx(expected_mult, rel=0.01)

    def test_multiplier_capped_at_one(self):
        from services.ph_nimitta.dasha_consensus import derive_dasha_consensus, ALL_7_SYSTEMS
        all_sys = sorted(ALL_7_SYSTEMS)
        windows = [_make_window(s, 7, all_sys) for s in all_sys]
        mock_conn = MagicMock()
        with patch("services.ka_dasha_kala.service.KaDashaKalaService") as MockSvc:
            MockSvc.return_value.query.return_value = _svc_result(windows)
            result = derive_dasha_consensus(mock_conn, CHART_ID, AYANAMSHA, TARGET_LORDS, W_START, W_END)

        assert result.confidence_multiplier <= 1.0


# ── All-7-systems checked is populated ───────────────────────────────────────

class TestSystemsCovered:
    def test_all_systems_checked_lists_7(self):
        from services.ph_nimitta.dasha_consensus import derive_dasha_consensus, ALL_7_SYSTEMS
        mock_conn = MagicMock()
        with patch("services.ka_dasha_kala.service.KaDashaKalaService") as MockSvc:
            MockSvc.return_value.query.return_value = _svc_result([])
            result = derive_dasha_consensus(mock_conn, CHART_ID, AYANAMSHA, TARGET_LORDS, W_START, W_END)

        assert set(result.all_systems_checked) == ALL_7_SYSTEMS

    def test_all_7_canonical_systems_present(self):
        from services.ph_nimitta.dasha_consensus import ALL_7_SYSTEMS
        expected = {
            'vimshottari', 'yogini', 'ashtottari',
            'chara_karaka', 'naisargika', 'mudda', 'kalachakra',
        }
        assert ALL_7_SYSTEMS == expected
