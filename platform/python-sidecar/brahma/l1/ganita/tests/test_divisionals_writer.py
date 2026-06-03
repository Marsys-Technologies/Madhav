"""
test_divisionals_writer.py — Brahma GA-1-3: divisionals writer test suite

Tests cover:
  1. Structural invariants (row counts, varga labels, sign names, house range)
  2. D1 (Rashi) FORENSIC benchmark — graha positions must match FORENSIC data
  3. D9 (Navamsha) computation — Lagna/Sun/Moon/Mercury positions
  4. D10 (Dasamsha) Sun in Aries benchmark
  5. Vargottama detection — Mercury is vargottama (D1=Capricorn, D9=Capricorn)
  6. House calculation relative to divisional Lagna
  7. JSONL ingestion path (engine pre-computed vargas)
  8. DB writer round-trip (in-memory mock)
  9. query_divisional guard for unknown varga
  10. All 16 canonical vargas are produced

FORENSIC benchmark (Lahiri, native 1984-02-05 10:43 IST Bhubaneswar):
  D1: Lagna=Aries, Sun=Capricorn, Moon=Aquarius, Mars=Libra, Saturn=Libra
  D9: Lagna=Cancer, Sun=Cancer, Moon=Gemini, Mercury=Capricorn (vargottama)
  D10: Sun=Aries

Commit tag: BRAHMA-GA-1-3
"""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ─── Fixtures ─────────────────────────────────────────────────────────────────

NATIVE_BIRTH = dict(
    chart_id="forensic-native-001",
    birth_datetime_iso="1984-02-05T10:43:00",
    tz_offset_hours=5.5,
    latitude_deg=20.2961,
    longitude_deg=85.8245,
    ayanamsha_id="lahiri",
    build_id="test-ga-1-3",
)


@pytest.fixture(scope="session")
def native_rows():
    """Compute all DivisionalRow objects for the native chart (Lahiri) once."""
    from brahma.l1.ganita.divisionals_writer import build_divisional_rows
    return build_divisional_rows(**NATIVE_BIRTH)


@pytest.fixture(scope="session")
def d1_rows(native_rows):
    return [r for r in native_rows if r.varga == "D1"]


@pytest.fixture(scope="session")
def d9_rows(native_rows):
    return [r for r in native_rows if r.varga == "D9"]


@pytest.fixture(scope="session")
def d10_rows(native_rows):
    return [r for r in native_rows if r.varga == "D10"]


# ─── 1. Structural invariants ─────────────────────────────────────────────────

class TestStructuralInvariants:
    def test_all_16_vargas_produced(self, native_rows):
        """All 16 canonical vargas must be present."""
        from brahma.l1.ganita.divisionals_writer import VARGA_LABELS
        produced = {r.varga for r in native_rows}
        assert produced == VARGA_LABELS, (
            f"Missing vargas: {VARGA_LABELS - produced}"
        )

    def test_total_row_count(self, native_rows):
        """16 vargas × 10 bodies (Lagna + 9 grahas) = 160 rows."""
        assert len(native_rows) == 160

    def test_sign_names_valid(self, native_rows):
        from brahma.l1.ganita.divisionals_writer import SIGNS
        valid = set(SIGNS)
        for row in native_rows:
            assert row.sign in valid, f"Invalid sign '{row.sign}' in {row}"

    def test_sign_number_range(self, native_rows):
        for row in native_rows:
            assert 1 <= row.sign_number <= 12, (
                f"sign_number={row.sign_number} out of range in {row}"
            )

    def test_degree_in_sign_range(self, native_rows):
        for row in native_rows:
            assert 0.0 <= row.degree_in_sign < 30.0, (
                f"degree_in_sign={row.degree_in_sign} out of range"
            )

    def test_house_range_non_lagna(self, native_rows):
        """Non-Lagna grahas must have house 1–12."""
        for row in native_rows:
            if row.graha != "Lagna":
                assert row.house is not None, f"Missing house for {row.graha} in {row.varga}"
                assert 1 <= row.house <= 12, (
                    f"house={row.house} out of range for {row.graha}"
                )

    def test_lagna_house_is_none(self, native_rows):
        """Lagna rows should not carry a house value."""
        for row in native_rows:
            if row.graha == "Lagna":
                assert row.house is None

    def test_source_citation_present(self, native_rows):
        for row in native_rows:
            assert row.source_citation, f"Empty source_citation in {row}"

    def test_vargottama_only_in_d9(self, native_rows):
        """vargottama field is only set (non-None) in D9 rows."""
        for row in native_rows:
            if row.varga != "D9" or row.graha == "Lagna":
                assert row.vargottama is None, (
                    f"vargottama unexpectedly set in {row.varga}/{row.graha}"
                )

    def test_build_id_propagated(self, native_rows):
        for row in native_rows:
            assert row.build_id == "test-ga-1-3"

    def test_ayanamsha_id_propagated(self, native_rows):
        for row in native_rows:
            assert row.ayanamsha_id == "lahiri"


# ─── 2. D1 FORENSIC benchmark ─────────────────────────────────────────────────

class TestD1FORENSICBenchmark:
    """FORENSIC-grounded anchors for D1 (Rashi) under Lahiri ayanamsha."""

    def _graha(self, d1_rows, graha_name: str):
        row = next((r for r in d1_rows if r.graha == graha_name), None)
        assert row is not None, f"{graha_name} not found in D1"
        return row

    def test_d1_lagna_aries(self, d1_rows):
        """Lagna in Aries (Mesha) — structural fingerprint."""
        lagna = self._graha(d1_rows, "Lagna")
        assert lagna.sign == "Aries", f"D1 Lagna expected Aries, got {lagna.sign}"

    def test_d1_sun_capricorn(self, d1_rows):
        """Sun in Capricorn (Makara) — FORENSIC ref: Shravana nakshatra."""
        sun = self._graha(d1_rows, "Sun")
        assert sun.sign == "Capricorn", f"D1 Sun expected Capricorn, got {sun.sign}"

    def test_d1_moon_aquarius(self, d1_rows):
        """Moon in Aquarius (Kumbha) — FORENSIC ref: Purva Bhadrapada nakshatra."""
        moon = self._graha(d1_rows, "Moon")
        assert moon.sign == "Aquarius", f"D1 Moon expected Aquarius, got {moon.sign}"

    def test_d1_mars_libra(self, d1_rows):
        """Mars in Libra (Tula) — FORENSIC ref."""
        mars = self._graha(d1_rows, "Mars")
        assert mars.sign == "Libra", f"D1 Mars expected Libra, got {mars.sign}"

    def test_d1_saturn_libra(self, d1_rows):
        """Saturn in Libra (Tula) — FORENSIC ref, exalted."""
        saturn = self._graha(d1_rows, "Saturn")
        assert saturn.sign == "Libra", f"D1 Saturn expected Libra, got {saturn.sign}"

    def test_d1_lagna_degree_approximate(self, d1_rows):
        """Lagna degree approximately 12° Aries (±2° tolerance for engine precision)."""
        lagna = self._graha(d1_rows, "Lagna")
        assert 10.0 <= lagna.degree_in_sign <= 14.0, (
            f"D1 Lagna degree {lagna.degree_in_sign} outside expected 10–14° Aries"
        )

    def test_d1_sun_degree_approximate(self, d1_rows):
        """Sun approximately 22° Capricorn (±1° tolerance)."""
        sun = self._graha(d1_rows, "Sun")
        assert 20.0 <= sun.degree_in_sign <= 23.5, (
            f"D1 Sun degree {sun.degree_in_sign} outside expected range"
        )

    def test_d1_rahu_taurus(self, d1_rows):
        """Rahu in Taurus (Vrishabha) — FORENSIC ref."""
        rahu = self._graha(d1_rows, "Rahu")
        assert rahu.sign == "Taurus", f"D1 Rahu expected Taurus, got {rahu.sign}"

    def test_d1_ketu_scorpio(self, d1_rows):
        """Ketu in Scorpio (Vrishchika) — FORENSIC ref, opposite Rahu."""
        ketu = self._graha(d1_rows, "Ketu")
        assert ketu.sign == "Scorpio", f"D1 Ketu expected Scorpio, got {ketu.sign}"

    def test_d1_rahu_ketu_opposite_signs(self, d1_rows):
        """Rahu and Ketu must always be in opposite signs (structural invariant)."""
        rahu = next(r for r in d1_rows if r.graha == "Rahu")
        ketu = next(r for r in d1_rows if r.graha == "Ketu")
        assert (rahu.sign_number - 1 + 6) % 12 == (ketu.sign_number - 1), (
            f"Rahu/Ketu not opposite: Rahu={rahu.sign_number}, Ketu={ketu.sign_number}"
        )

    def test_d1_ten_bodies_present(self, d1_rows):
        """D1 must have exactly 10 bodies: Lagna + 9 grahas."""
        expected = {"Lagna", "Sun", "Moon", "Mars", "Mercury",
                    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        found = {r.graha for r in d1_rows}
        assert found == expected, f"D1 bodies mismatch: found={found}"

    def test_d1_sign_matches_sign_number(self, d1_rows):
        """sign and sign_number must be internally consistent."""
        from brahma.l1.ganita.divisionals_writer import SIGNS
        for row in d1_rows:
            expected_sign = SIGNS[row.sign_number - 1]
            assert row.sign == expected_sign, (
                f"sign/sign_number mismatch: {row.sign} vs {expected_sign}"
            )


# ─── 3. D9 (Navamsha) FORENSIC benchmark ─────────────────────────────────────

class TestD9NavamshaFORENSIC:
    """D9 Navamsha FORENSIC-grounded anchors."""

    def _graha(self, d9_rows, graha_name: str):
        row = next((r for r in d9_rows if r.graha == graha_name), None)
        assert row is not None, f"{graha_name} not found in D9"
        return row

    def test_d9_lagna_cancer(self, d9_rows):
        """D9 Lagna in Cancer — FORENSIC ref."""
        lagna = self._graha(d9_rows, "Lagna")
        assert lagna.sign == "Cancer", f"D9 Lagna expected Cancer, got {lagna.sign}"

    def test_d9_sun_cancer(self, d9_rows):
        """D9 Sun in Cancer — FORENSIC ref."""
        sun = self._graha(d9_rows, "Sun")
        assert sun.sign == "Cancer", f"D9 Sun expected Cancer, got {sun.sign}"

    def test_d9_moon_gemini(self, d9_rows):
        """D9 Moon in Gemini — FORENSIC ref."""
        moon = self._graha(d9_rows, "Moon")
        assert moon.sign == "Gemini", f"D9 Moon expected Gemini, got {moon.sign}"

    def test_d9_mercury_capricorn(self, d9_rows):
        """D9 Mercury in Capricorn — FORENSIC ref (also vargottama with D1)."""
        mercury = self._graha(d9_rows, "Mercury")
        assert mercury.sign == "Capricorn", (
            f"D9 Mercury expected Capricorn, got {mercury.sign}"
        )

    def test_d9_mercury_vargottama_flagged(self, d9_rows):
        """Mercury must be flagged vargottama=True in D9 (D1=Capricorn, D9=Capricorn)."""
        mercury = self._graha(d9_rows, "Mercury")
        assert mercury.vargottama is True, (
            f"Mercury expected vargottama=True, got {mercury.vargottama}"
        )

    def test_d9_non_vargottama_bodies(self, d9_rows):
        """Only Mercury is vargottama; all other non-Lagna grahas must be False."""
        for row in d9_rows:
            if row.graha in ("Lagna",):
                continue  # Lagna vargottama is None per design
            if row.graha == "Mercury":
                continue  # already tested
            assert row.vargottama is False, (
                f"{row.graha} unexpectedly vargottama=True in D9"
            )

    def test_d9_houses_from_cancer_lagna(self, d9_rows):
        """Houses are computed from Cancer (sign 4) as Lagna.
        Sun in Cancer = house 1 from Cancer.
        Moon in Gemini = house 12 from Cancer.
        """
        sun = next(r for r in d9_rows if r.graha == "Sun")
        assert sun.house == 1, f"D9 Sun expected house 1 from Cancer Lagna, got {sun.house}"
        moon = next(r for r in d9_rows if r.graha == "Moon")
        assert moon.house == 12, f"D9 Moon expected house 12 from Cancer Lagna, got {moon.house}"


# ─── 4. D10 (Dasamsha) benchmark ─────────────────────────────────────────────

class TestD10DasamshaFORENSIC:
    """D10 Dasamsha FORENSIC anchor."""

    def test_d10_sun_aries(self, d10_rows):
        """D10 Sun in Aries — FORENSIC ref for career/professional sector."""
        sun = next(r for r in d10_rows if r.graha == "Sun")
        assert sun.sign == "Aries", f"D10 Sun expected Aries, got {sun.sign}"

    def test_d10_ten_bodies(self, d10_rows):
        """D10 must have exactly 10 bodies."""
        assert len(d10_rows) == 10, f"D10 expected 10 rows, got {len(d10_rows)}"


# ─── 5. Vargottama logic unit tests ───────────────────────────────────────────

class TestVargottamaComputation:
    def test_vargottama_same_sign(self):
        from brahma.l1.ganita.divisionals_writer import compute_vargottama
        d1 = [("Sun", 10, 21.0), ("Moon", 11, 27.0)]
        d9 = [("Sun", 10, 5.0), ("Moon", 3, 3.0)]
        result = compute_vargottama(d1, d9)
        assert result["Sun"] is True    # Capricorn in both
        assert result["Moon"] is False  # Aquarius vs Gemini

    def test_vargottama_different_sign(self):
        from brahma.l1.ganita.divisionals_writer import compute_vargottama
        d1 = [("Saturn", 7, 22.0)]
        d9 = [("Saturn", 1, 21.0)]
        result = compute_vargottama(d1, d9)
        assert result["Saturn"] is False

    def test_vargottama_lagna_excluded(self):
        from brahma.l1.ganita.divisionals_writer import compute_vargottama
        d1 = [("Lagna", 1, 12.0), ("Sun", 10, 21.0)]
        d9 = [("Lagna", 1, 21.0), ("Sun", 10, 17.0)]
        result = compute_vargottama(d1, d9)
        assert "Lagna" not in result


# ─── 6. House calculation unit tests ─────────────────────────────────────────

class TestHouseCalculation:
    def test_lagna_is_house_1(self):
        """Graha in lagna sign = house 1."""
        from brahma.l1.ganita.divisionals_writer import compute_house_from_lagna
        assert compute_house_from_lagna(4, 4) == 1  # Cancer lagna, graha in Cancer

    def test_adjacent_sign_is_house_2(self):
        from brahma.l1.ganita.divisionals_writer import compute_house_from_lagna
        assert compute_house_from_lagna(5, 4) == 2  # Leo from Cancer lagna

    def test_opposite_sign_is_house_7(self):
        from brahma.l1.ganita.divisionals_writer import compute_house_from_lagna
        assert compute_house_from_lagna(10, 4) == 7  # Capricorn from Cancer lagna

    def test_wrap_around(self):
        """Pisces lagna, Aries graha = house 2."""
        from brahma.l1.ganita.divisionals_writer import compute_house_from_lagna
        assert compute_house_from_lagna(1, 12) == 2  # Aries (1) from Pisces (12) lagna

    def test_all_houses_in_1_to_12(self):
        from brahma.l1.ganita.divisionals_writer import compute_house_from_lagna
        for lagna_sn in range(1, 13):
            for graha_sn in range(1, 13):
                house = compute_house_from_lagna(graha_sn, lagna_sn)
                assert 1 <= house <= 12, (
                    f"compute_house_from_lagna({graha_sn}, {lagna_sn}) = {house}"
                )


# ─── 7. Engine JSONL ingestion path ──────────────────────────────────────────

class TestEngineJSONLIngestion:
    def test_precomputed_vargas_ingestion(self, tmp_path):
        """JSONL with pre-computed vargas block must be parsed correctly."""
        from brahma.l1.ganita.divisionals_writer import build_divisional_rows_from_engine_jsonl

        # Minimal engine JSONL record with D1 block
        record = {
            "chart_id": "test-engine-001",
            "ayanamsha": {"id": "lahiri"},
            "inputs": {
                "datetime_iso": "1984-02-05T10:43:00",
                "tz_offset_hours": 5.5,
                "latitude_deg": 20.2961,
                "longitude_deg": 85.8245,
            },
            "vargas": [
                {
                    "varga": "D1",
                    "positions": [
                        ["L", [0, 12.42]],    # Lagna in Aries
                        [0, [9, 21.96]],       # Sun in Capricorn
                        [1, [10, 27.06]],      # Moon in Aquarius
                    ],
                },
                {
                    "varga": "D9",
                    "positions": [
                        ["L", [3, 21.79]],    # Lagna in Cancer
                        [0, [3, 17.66]],       # Sun in Cancer
                        [1, [2, 3.50]],        # Moon in Gemini
                    ],
                },
            ],
        }

        jsonl_file = tmp_path / "engine.jsonl"
        jsonl_file.write_text(json.dumps(record) + "\n")

        rows = build_divisional_rows_from_engine_jsonl(str(jsonl_file), build_id="jsonl-test")
        assert len(rows) > 0

        d1 = [r for r in rows if r.varga == "D1"]
        assert any(r.graha == "Lagna" and r.sign == "Aries" for r in d1), (
            "D1 Lagna should be Aries from pre-computed block"
        )
        sun_d1 = next(r for r in d1 if r.graha == "Sun")
        assert sun_d1.sign == "Capricorn"

    def test_empty_jsonl_produces_no_rows(self, tmp_path):
        from brahma.l1.ganita.divisionals_writer import build_divisional_rows_from_engine_jsonl
        jsonl_file = tmp_path / "empty.jsonl"
        jsonl_file.write_text("")
        rows = build_divisional_rows_from_engine_jsonl(str(jsonl_file), build_id="empty")
        assert rows == []

    def test_jsonl_fallback_recompute(self, tmp_path):
        """Record without 'vargas' block triggers recompute from birth inputs."""
        from brahma.l1.ganita.divisionals_writer import build_divisional_rows_from_engine_jsonl

        record = {
            "chart_id": "recompute-001",
            "ayanamsha": {"id": "lahiri"},
            "inputs": {
                "datetime_iso": "1984-02-05T10:43:00",
                "tz_offset_hours": 5.5,
                "latitude_deg": 20.2961,
                "longitude_deg": 85.8245,
            },
            # No 'vargas' key — will recompute
        }
        jsonl_file = tmp_path / "recompute.jsonl"
        jsonl_file.write_text(json.dumps(record) + "\n")

        rows = build_divisional_rows_from_engine_jsonl(
            str(jsonl_file), build_id="recompute", ayanamsha_ids=["lahiri"]
        )
        assert len(rows) == 160  # all 16 vargas × 10 bodies

        d1_lagna = next(
            (r for r in rows if r.varga == "D1" and r.graha == "Lagna"), None
        )
        assert d1_lagna is not None
        assert d1_lagna.sign == "Aries"


# ─── 8. DB writer round-trip (mock) ──────────────────────────────────────────

class TestDBWriter:
    def test_write_rows_returns_count(self, native_rows):
        from brahma.l1.ganita.divisionals_writer import write_rows_to_db, DivisionalRow

        # Build a minimal mock connection
        mock_cur = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cur
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        count = write_rows_to_db(native_rows, mock_conn)
        assert count == len(native_rows) == 160

    def test_write_rows_empty_returns_zero(self):
        from brahma.l1.ganita.divisionals_writer import write_rows_to_db
        mock_conn = MagicMock()
        count = write_rows_to_db([], mock_conn)
        assert count == 0
        mock_conn.commit.assert_not_called()

    def test_write_calls_commit(self, native_rows):
        from brahma.l1.ganita.divisionals_writer import write_rows_to_db

        mock_cur = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cur
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        write_rows_to_db(native_rows[:1], mock_conn)
        mock_conn.commit.assert_called_once()


# ─── 9. query_divisional guard ────────────────────────────────────────────────

class TestQueryDivisionalGuard:
    def test_unknown_varga_raises(self):
        from brahma.l1.ganita.divisionals_writer import query_divisional
        mock_conn = MagicMock()
        with pytest.raises(ValueError, match="Unknown varga"):
            query_divisional(db_conn=mock_conn, chart_id="x", varga="D99")

    def test_known_varga_calls_db(self):
        from brahma.l1.ganita.divisionals_writer import query_divisional

        mock_cur = MagicMock()
        mock_cur.description = [("graha",), ("sign",), ("sign_number",),
                                 ("degree_in_sign",), ("house",), ("vargottama",),
                                 ("ayanamsha_id",), ("varga",), ("source_citation",),
                                 ("build_id",)]
        mock_cur.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cur
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = query_divisional(db_conn=mock_conn, chart_id="x", varga="D9")
        assert result == []
        mock_cur.execute.assert_called_once()


# ─── 10. VARGA_CATALOG completeness ──────────────────────────────────────────

class TestVargaCatalogCompleteness:
    def test_canonical_16_varga_set(self):
        from brahma.l1.ganita.divisionals_writer import VARGA_CATALOG, VARGA_LABELS
        expected_factors = {1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60}
        assert set(VARGA_CATALOG.keys()) == expected_factors

    def test_varga_labels_format(self):
        from brahma.l1.ganita.divisionals_writer import VARGA_CATALOG
        for factor, label in VARGA_CATALOG.items():
            assert label == f"D{factor}", (
                f"VARGA_CATALOG[{factor}] should be 'D{factor}', got '{label}'"
            )

    def test_signs_list_12_entries(self):
        from brahma.l1.ganita.divisionals_writer import SIGNS
        assert len(SIGNS) == 12
        assert SIGNS[0] == "Aries"
        assert SIGNS[11] == "Pisces"

    def test_graha_map_has_lagna_key(self):
        from brahma.l1.ganita.divisionals_writer import GRAHA_MAP
        assert "L" in GRAHA_MAP
        assert GRAHA_MAP["L"] == "Lagna"


# ─── 11. Bootstrap entrypoint sanity ─────────────────────────────────────────

class TestBootstrapEntrypoint:
    def test_bootstrap_native_chart_no_db(self):
        """bootstrap_native_chart without db_conn returns rows but does not write."""
        from brahma.l1.ganita.divisionals_writer import bootstrap_native_chart

        rows = bootstrap_native_chart(
            chart_id="bootstrap-test",
            build_id="ga-1-3-bootstrap-test",
            ayanamsha_ids=["lahiri"],
        )
        assert len(rows) == 160

        # FORENSIC: D1 Lagna must be Aries
        d1_lagna = next(
            (r for r in rows if r.varga == "D1" and r.graha == "Lagna"), None
        )
        assert d1_lagna is not None
        assert d1_lagna.sign == "Aries"

    def test_bootstrap_auto_build_id(self):
        from brahma.l1.ganita.divisionals_writer import bootstrap_native_chart

        rows = bootstrap_native_chart(
            chart_id="auto-id-test",
            ayanamsha_ids=["lahiri"],
        )
        assert all(r.build_id.startswith("ganita-divisionals-") for r in rows)
