"""
test_l1_bhava_bala_av_completion_d1_5b.py — D-1.5b Lane B-2 tests.

Part A — Bhāva Bala (CR-103): PyJHora-delegated (no hand-roll), 3-source
  (adhipathi+dig+drik) documented-approximation composition. Facts present,
  stamped verification_pass_status='documented_approximation', cite 3-source.

Part B — Aṣṭakavarga completion (CR-99a): sign-keyed BAV/SAV added while the
  house-keyed rows are RETAINED; trikoṇa/ekādhipatya śodhana grids, rāśi-piṇḍa,
  and kakṣyā boundaries added; the underlying bindu VALUES are NOT recomputed
  (sign re-key reuses the exact house-keyed values).
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import ga_writers.ga_strength_writer as sut  # noqa: E402

NATIVE_BIRTH = {
    "datetime_iso": "1984-02-05T10:43:00",
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "tz_offset_hours": 5.5,
    "place_name": "Bhubaneswar",
    "subject_label": "Abhisek",
}
AY = "lahiri_chitrapaksha"
CID = "482012f1-710e-4a25-994a-93821f5871aa"
BID = "test-build-id-d1_5b"
NOW = "2026-07-15T00:00:00+00:00"
ENG = "test-eng"

SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "ga_writers" / "CHART_FACTS_SCHEMA.json"


@pytest.fixture(scope="module")
def native_kw():
    return dict(
        lat=NATIVE_BIRTH["latitude_deg"],
        lon=NATIVE_BIRTH["longitude_deg"],
        tz=NATIVE_BIRTH["tz_offset_hours"],
    )


@pytest.fixture(scope="module")
def jd_ut():
    from pyjhora_adapter.compute import compute_chart
    co = compute_chart(inputs=NATIVE_BIRTH, ayanamsha_id="lahiri")
    return float(co["provenance"]["jd_ut"])


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Part A — Bhāva Bala (CR-103) ─────────────────────────────────────────────

class TestBhavaBalaPyJHora:
    @pytest.fixture(scope="class")
    def bb(self, jd_ut, native_kw):
        return sut._derive_bhava_bala(jd_ut, AY, **native_kw)

    @pytest.fixture(scope="class")
    def bb_rows(self, bb):
        return sut._build_bhava_bala_rows(bb, CID, BID, AY, NOW, ENG, "single_pass")

    def test_twelve_bhavas(self, bb):
        assert len(bb) == 12
        assert set(bb) == {f"HOUSE_{i}" for i in range(1, 13)}

    def test_three_source_subscores_present(self, bb):
        # Binder amendment: PyJHora bhava_bala is a 3-source composition
        # (adhipathi + dig + drik/drishti), NOT six-source. Key names kept
        # identical to the pre-existing contract for MV compatibility.
        for hk, hb in bb.items():
            assert {"bhava_adhipati_bala", "bhava_digbala", "bhava_drishti_bala",
                    "total", "strength_ratio"} <= set(hb), f"{hk}: {hb}"

    def test_total_positive_and_composed(self, bb):
        for hk, hb in bb.items():
            assert hb["total"] > 0, f"{hk} total not positive"
            # total (rupas) == (adhipathi + dig + drik/drishti) [each already /60]
            composed = (hb["bhava_adhipati_bala"] + hb["bhava_digbala"]
                        + hb["bhava_drishti_bala"])
            assert abs(composed - hb["total"]) < 0.05, f"{hk}: {composed} != {hb['total']}"

    def test_rows_are_documented_approximation(self, bb_rows):
        assert bb_rows, "no bhava bala rows"
        for r in bb_rows:
            assert r["verification_pass_status"] == "documented_approximation", (
                f"bhava bala must be documented_approximation, got "
                f"{r['verification_pass_status']} for {r['fact_category']}"
            )

    def test_rows_cite_three_source_composition(self, bb_rows):
        for r in bb_rows:
            assert "3-source:adhipathi+dig+drik" in r["source_calculation"], (
                f"provenance must cite 3-source composition: {r['source_calculation']}"
            )
            assert "pyjhora" in r["source_calculation"].lower()
            # never claims six-source
            assert "six" not in r["source_calculation"].lower()

    def test_no_hand_rolled_heuristic_marker(self):
        src = pathlib.Path(sut.__file__).read_text(encoding="utf-8")
        assert "python_heuristic_approximation.bhava_bala_classical" not in src, (
            "hand-rolled bhava bala source marker must be gone (CR-103 no-hand-roll)"
        )

    def test_categories_present(self, bb_rows):
        cats = {r["fact_category"] for r in bb_rows}
        assert {"house_bhava_bala_subscore", "house_bhava_bala_total",
                "house_bhava_bala_ratio"} <= cats

    def test_bhava_categories_declared_in_schema(self, schema):
        for c in ("house_bhava_bala_subscore", "house_bhava_bala_total",
                  "house_bhava_bala_ratio"):
            assert c in schema["categories"], f"{c} undeclared in CHART_FACTS_SCHEMA.json"


# ── Part B — Aṣṭakavarga completion (CR-99a) ─────────────────────────────────

class TestAshtakavargaCompletion:
    @pytest.fixture(scope="class")
    def av(self, jd_ut, native_kw):
        return sut._derive_ashtakavarga(jd_ut, AY, **native_kw)

    @pytest.fixture(scope="class")
    def grids(self, jd_ut, native_kw):
        return sut._derive_ashtakavarga_shodhana_grids(jd_ut, AY, **native_kw)

    @pytest.fixture(scope="class")
    def rows(self, av, grids):
        return sut._build_ashtakavarga_rows(
            av["bindus"], av["pinda"], CID, BID, AY, NOW, ENG,
            "two_pass_verified", grids=grids,
        )

    def _by(self, rows, cat, tag):
        d = {}
        for r in rows:
            if r["fact_category"] != cat:
                continue
            g, n = r["fact_subject"].split(tag)
            d[(g, int(n))] = r["fact_value_num"]
        return d

    def test_house_keyed_rows_retained(self, rows):
        house = [r for r in rows if r["fact_category"] == "ashtakavarga_bindu"]
        assert len(house) == 96, f"expected 96 house-keyed rows, got {len(house)}"
        assert all("-HOUSE_" in r["fact_subject"] for r in house)

    def test_sign_keyed_rows_added(self, rows):
        sign = [r for r in rows if r["fact_category"] == "ashtakavarga_bindu_sign"]
        assert len(sign) == 96, f"expected 96 sign-keyed rows, got {len(sign)}"
        assert all("-SIGN_" in r["fact_subject"] for r in sign)

    def test_sign_rekey_preserves_bindu_values(self, rows):
        # §L.3 baseline: re-key only — the sign values MUST equal the house values.
        house_vals = self._by(rows, "ashtakavarga_bindu", "-HOUSE_")
        sign_vals = self._by(rows, "ashtakavarga_bindu_sign", "-SIGN_")
        assert house_vals == sign_vals, "sign re-key altered bindu values (forbidden)"

    def test_sarva_invariant_intact(self, rows):
        # SAV over 12 signs must still sum to 337 (bindus untouched).
        sarva = [r["fact_value_num"] for r in rows
                 if r["fact_category"] == "ashtakavarga_bindu_sign"
                 and r["fact_subject"].startswith("SARVA-SIGN_")]
        assert len(sarva) == 12
        assert int(sum(sarva)) == 337

    def test_trikona_shodhana_grid_present(self, rows):
        tri = [r for r in rows if r["fact_category"] == "ashtakavarga_trikona_shodhana"]
        assert len(tri) == 7 * 12, f"expected 84 trikona rows, got {len(tri)}"
        assert all(r["fact_key"] == "reduced_bindus" for r in tri)
        assert all("-SIGN_" in r["fact_subject"] for r in tri)
        assert all(0 <= r["fact_value_num"] <= 8 for r in tri)

    def test_ekadhipatya_shodhana_grid_present(self, rows):
        eka = [r for r in rows if r["fact_category"] == "ashtakavarga_ekadhipathya_shodhana"]
        assert len(eka) == 7 * 12, f"expected 84 ekadhipatya rows, got {len(eka)}"
        assert all(r["fact_key"] == "reduced_bindus" for r in eka)

    def test_pindas_present(self, rows):
        cats = {r["fact_category"] for r in rows}
        assert {"ashtakavarga_pinda_sodhita", "ashtakavarga_pinda_bhinna",
                "ashtakavarga_pinda_sarva", "ashtakavarga_pinda_raasi"} <= cats
        # raasi + graha == sodhya per graha (classical identity)
        raasi = {r["fact_subject"]: r["fact_value_num"] for r in rows
                 if r["fact_category"] == "ashtakavarga_pinda_raasi"}
        graha = {r["fact_subject"]: r["fact_value_num"] for r in rows
                 if r["fact_category"] == "ashtakavarga_pinda_bhinna"}
        sodhya = {r["fact_subject"]: r["fact_value_num"] for r in rows
                  if r["fact_category"] == "ashtakavarga_pinda_sodhita"}
        for g in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"):
            assert abs((raasi[g] + graha[g]) - sodhya[g]) < 0.5, (
                f"{g}: raasi+graha ({raasi[g]}+{graha[g]}) != sodhya {sodhya[g]}"
            )

    def test_kakshya_boundaries_present(self, rows):
        k = [r for r in rows if r["fact_category"] == "ashtakavarga_kakshya_boundary"]
        assert len(k) == 24, f"expected 8 kakshya x 3 keys = 24, got {len(k)}"
        lords = [r["fact_value_text"] for r in k if r["fact_key"] == "lord"]
        assert lords == ["Saturn", "Jupiter", "Mars", "Sun", "Venus",
                         "Mercury", "Moon", "Lagna"]
        # boundaries: 8 arcs of 3.75 deg covering 0..30
        starts = sorted(r["fact_value_num"] for r in k if r["fact_key"] == "start_deg")
        ends = sorted(r["fact_value_num"] for r in k if r["fact_key"] == "end_deg")
        assert starts[0] == 0.0 and ends[-1] == 30.0
        assert all(abs((e - s) - 3.75) < 1e-6 for s, e in zip(starts, ends))

    def test_all_new_categories_declared_in_schema(self, rows, schema):
        emitted = {r["fact_category"] for r in rows}
        for c in emitted:
            assert c in schema["categories"], (
                f"emitted category {c} undeclared in CHART_FACTS_SCHEMA.json "
                f"(drift_detector gate would FAIL)"
            )
