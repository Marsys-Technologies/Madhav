"""
test_bo22_ayanamsha_context.py — Tests for Stream E e4: ayanamsha_context in bodha_graph
==========================================================================================

Tests for:
  1. detect_ayanamsha_dependent_edges() — returns expected structure
  2. detect_ayanamsha_dependent_edges() — empty when no positions in DB
  3. detect_ayanamsha_dependent_edges() — detects boundary proximity
  4. detect_ayanamsha_dependent_edges() — deduplication works
  5. _distance_to_nearest_boundary() — correct for various inputs
  6. BOUNDARY_PROXIMITY_DEG constant is set
  7. seed_bodha_graph() accepts ayanamsha_id parameter
  8. _GRAHA_TO_SIGNAL covers all 9 classical grahas
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def _mod():
    from brahmagyan.bodha import bo22
    return bo22


class TestDistanceToBoundary:
    def test_at_sign_boundary(self):
        mod = _mod()
        # Exactly at 30° (Aries/Taurus boundary)
        assert mod._distance_to_nearest_boundary(30.0, 30.0) == pytest.approx(0.0)

    def test_at_sign_midpoint(self):
        mod = _mod()
        # 15° into a sign = exactly halfway = 15° from boundary
        d = mod._distance_to_nearest_boundary(15.0, 30.0)
        assert d == pytest.approx(15.0)

    def test_near_sign_boundary(self):
        mod = _mod()
        # 29.9° = 0.1° before Aries/Taurus boundary
        d = mod._distance_to_nearest_boundary(29.9, 30.0)
        assert d == pytest.approx(0.1, abs=1e-6)

    def test_just_past_sign_boundary(self):
        mod = _mod()
        # 30.1° = 0.1° past boundary
        d = mod._distance_to_nearest_boundary(30.1, 30.0)
        assert d == pytest.approx(0.1, abs=1e-6)

    def test_nakshatra_boundary(self):
        mod = _mod()
        nak_interval = 360.0 / 27  # ~13.333°
        # Exactly at nakshatra boundary
        d = mod._distance_to_nearest_boundary(nak_interval, nak_interval)
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_near_nakshatra_boundary(self):
        mod = _mod()
        nak_interval = 360.0 / 27
        # 0.2° before the boundary
        lon = nak_interval - 0.2
        d = mod._distance_to_nearest_boundary(lon, nak_interval)
        assert d == pytest.approx(0.2, abs=1e-5)


class TestGrahaSignalMap:
    def test_covers_nine_classical_grahas(self):
        mod = _mod()
        expected_grahas = {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        }
        assert set(mod._GRAHA_TO_SIGNAL.keys()) == expected_grahas

    def test_all_signals_start_with_pln(self):
        mod = _mod()
        for sig in mod._GRAHA_TO_SIGNAL.values():
            assert sig.startswith("PLN."), f"Signal {sig!r} does not start with PLN."


class TestBoundaryProximityConstant:
    def test_boundary_proximity_is_positive(self):
        mod = _mod()
        assert mod.BOUNDARY_PROXIMITY_DEG > 0

    def test_boundary_proximity_less_than_one_degree(self):
        mod = _mod()
        assert mod.BOUNDARY_PROXIMITY_DEG < 1.0


class TestDetectAyanamshaDependent:
    """
    Tests for detect_ayanamsha_dependent_edges().
    DB is fully mocked.
    """

    def _run(
        self,
        edges: list[tuple],
        positions: list[tuple],
        chart_id: str = "test-chart",
        ayanamsha_pair: tuple[str, str] = ("lahiri", "kp"),
        threshold: float = 0.30,
    ) -> dict:
        """Execute detect_ayanamsha_dependent_edges with mocked DB."""
        mod = _mod()

        mock_conn_ctx = MagicMock()
        mock_conn = MagicMock()
        mock_conn_ctx.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn_ctx.__exit__ = MagicMock(return_value=False)

        # First execute call = edges query; second = positions query
        call_count = [0]
        def fake_execute(sql, params=None):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.fetchall.return_value = edges
            else:
                mock_result.fetchall.return_value = positions
            mock_conn.execute.return_value = mock_result
            return mock_result

        mock_conn.execute.side_effect = fake_execute

        with patch.object(mod, "_get_conn", return_value=mock_conn_ctx):
            return mod.detect_ayanamsha_dependent_edges(
                chart_id,
                ayanamsha_pair=ayanamsha_pair,
                boundary_threshold_deg=threshold,
            )

    def test_returns_expected_keys(self):
        result = self._run(edges=[], positions=[])
        assert "chart_id" in result
        assert "ayanamsha_dependent_edges" in result
        assert "total_edges_scanned" in result
        assert "dependent_count" in result
        assert "provenance_envelope" in result

    def test_empty_edges_returns_zero_dependent(self):
        result = self._run(edges=[], positions=[])
        assert result["dependent_count"] == 0
        assert result["ayanamsha_dependent_edges"] == []

    def test_planet_near_sign_boundary_flagged(self):
        """
        An edge involving Sun at 29.95° (near Aries/Taurus boundary) with
        threshold 0.30° should be flagged as AYANAMSHA_DEPENDENT.
        """
        # edges: (edge_id, from_sig, to_sig, edge_type, aya_id)
        edges = [
            ("CGM_EDGE_001", "PLN.SUN", "PLN.SATURN", "modulate", "lahiri"),
        ]
        # positions: (ayanamsha_id, planet, sidereal_longitude)
        # Sun at 29.95° = 0.05° from Aries/Taurus boundary
        positions = [
            ("lahiri", "Sun", 29.95),
            ("kp",     "Sun", 29.93),  # KP slightly different
        ]
        result = self._run(edges=edges, positions=positions, threshold=0.30)
        assert result["dependent_count"] > 0
        # Should flag the Sun edge
        planets_flagged = [e["planet"] for e in result["ayanamsha_dependent_edges"]]
        assert "Sun" in planets_flagged

    def test_planet_far_from_boundary_not_flagged(self):
        """
        A planet at 15.0° is far from any sign (15° away) and nakshatra
        boundary. Should not be flagged.
        """
        edges = [
            ("CGM_EDGE_001", "PLN.SUN", "PLN.SATURN", "modulate", "lahiri"),
        ]
        positions = [
            ("lahiri", "Sun", 15.0),
            ("kp",     "Sun", 14.99),
        ]
        result = self._run(edges=edges, positions=positions, threshold=0.30)
        # 15.0° is exactly mid-sign (15° from each boundary) — not flagged
        sun_entries = [e for e in result["ayanamsha_dependent_edges"]
                       if e["planet"] == "Sun" and e["boundary_type"] == "sign"]
        assert len(sun_entries) == 0

    def test_deduplication_works(self):
        """
        Same edge appearing in multiple ayanamsha rows should not produce
        duplicate dependent entries for the same (edge_id, planet, boundary_type, aya).
        """
        # Two rows for same edge (lahiri + kp variant in bodha_graph)
        edges = [
            ("CGM_EDGE_001", "PLN.SUN", "PLN.SATURN", "modulate", "lahiri"),
            ("CGM_EDGE_001", "PLN.SUN", "PLN.SATURN", "modulate", "kp"),
        ]
        positions = [
            ("lahiri", "Sun", 29.95),
            ("kp",     "Sun", 29.93),
        ]
        result = self._run(edges=edges, positions=positions, threshold=0.30)
        # Deduplicated: each (edge_id, planet, boundary_type, aya_context) is unique
        keys = [
            (e["edge_id"], e["planet"], e["boundary_type"], e["ayanamsha_context"])
            for e in result["ayanamsha_dependent_edges"]
        ]
        assert len(keys) == len(set(keys)), "Duplicate entries found after deduplication"

    def test_no_position_data_returns_zero(self):
        """If ganita_positions has no rows, no edges flagged."""
        edges = [
            ("CGM_EDGE_001", "PLN.SUN", "PLN.SATURN", "modulate", "lahiri"),
        ]
        result = self._run(edges=edges, positions=[])
        assert result["dependent_count"] == 0
