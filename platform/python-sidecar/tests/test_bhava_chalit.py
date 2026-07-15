"""
test_bhava_chalit.py — Lane B-1 (D-1.5b): real bhāva-chalit cusps + fake-cusp quarantine.

Doctrine (DR-2): whole-sign house_d1 STAYS PRIMARY and untouched; chalit is a FULL
SECOND DATA LAYER, purely additive. B.10: no fabricated precision survives.

Coverage:
  (a) Cusps computed for the native reproduce independently (Sripati + Placidus),
      and the sandhi type-specimen fires: Moon whole-sign H11 -> Sripati chalit H12.
  (b) The two fake-cusp sites no longer emit equal-house (30°-apart) cusps — they emit
      real Placidus cusps (KP CUSP_1 == ascendant; spacing is non-uniform).
  (c) The KP cusp sub-lord is the REAL 249-division Vimshottari sub-lord, never the
      old nakshatra-lord approximation; when real cusps are absent, an honest
      EXTERNAL_COMPUTATION_REQUIRED marker is emitted (never a fabricated cusp).
"""
from __future__ import annotations

import pytest

NATIVE_INPUTS = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.2961,
    "longitude_deg": 85.8245,
    "place_name": "Bhubaneswar",
    "subject_label": "Abhisek",
}


@pytest.fixture(scope="module")
def chart_output():
    from pyjhora_adapter.compute import compute_chart
    return compute_chart(inputs=NATIVE_INPUTS, ayanamsha_id="lahiri")


# ── (a) Independent recomputation + the sandhi type-specimen ──────────────────

class TestCuspComputation:
    def test_bhava_chalit_present(self, chart_output):
        bc = chart_output.get("bhava_chalit")
        assert bc is not None
        assert bc["sandhi_orb_deg"] == 3.0
        assert len(bc["sripati"]["madhyas"]) == 12
        assert len(bc["sripati"]["cusps"]) == 12
        assert len(bc["placidus"]["cusp_boundaries"]) == 12

    def test_sripati_cusps_match_independent_recompute(self, chart_output):
        """Recompute Sripati madhyas straight from PyJHora and compare."""
        from pyjhora_adapter._jhora import drik, utils
        from pyjhora_adapter._ayanamsha import resolve_mode
        mode, _ = resolve_mode("lahiri")
        drik.set_ayanamsa_mode(mode)
        jd = utils.julian_day_number(drik.Date(1984, 2, 5), (10, 43, 0))
        place = drik.Place("subject", 20.2961, 85.8245, 5.5)
        expected = [x % 360.0 for x in drik.bhaava_madhya_sripathi(jd, place)]
        got = chart_output["bhava_chalit"]["sripati"]["madhyas"]
        for e, g in zip(expected, got):
            assert abs(e - g) < 1e-6

    def test_placidus_cusps_match_independent_recompute(self, chart_output):
        from pyjhora_adapter._jhora import drik, utils
        from pyjhora_adapter._ayanamsha import resolve_mode
        mode, _ = resolve_mode("lahiri")
        drik.set_ayanamsa_mode(mode)
        jd = utils.julian_day_number(drik.Date(1984, 2, 5), (10, 43, 0))
        place = drik.Place("subject", 20.2961, 85.8245, 5.5)
        expected = [x % 360.0 for x in drik.bhaava_madhya_swe(jd, place, house_code="P")]
        got = chart_output["bhava_chalit"]["placidus"]["cusp_boundaries"]
        for e, g in zip(expected, got):
            assert abs(e - g) < 1e-6

    def test_placidus_cusp1_is_ascendant(self, chart_output):
        """KP/Placidus cusp 1 == ascendant longitude (real-cusp sanity)."""
        asc = chart_output["ascendant"]["longitude_deg"]
        cusp1 = chart_output["bhava_chalit"]["placidus"]["cusp_boundaries"][0]
        assert abs((asc - cusp1) % 360.0) < 1e-6

    def test_moon_sandhi_specimen(self, chart_output):
        """ACCEPTANCE CRITERION: Moon whole-sign H11 -> Sripati chalit H12."""
        moon = next(g for g in chart_output["grahas"] if g["name"] == "Moon")
        assert moon["house"] == 11, "Moon must be whole-sign H11"
        mc = chart_output["bhava_chalit"]["graha_chalit"]["Moon"]
        assert mc["chalit_house"] == 12, "Moon Sripati chalit must be H12 (the specimen)"
        assert mc["whole_sign_house"] == 11
        assert mc["sandhi_flag"] is True
        assert "wholesign_chalit_divergence" in mc["sandhi_reasons"]

    def test_forensic_sanity(self, chart_output):
        sun = next(g for g in chart_output["grahas"] if g["name"] == "Sun")
        moon = next(g for g in chart_output["grahas"] if g["name"] == "Moon")
        assert sun["sign"] == "Capricorn"
        assert moon["nakshatra"] == "Purva Bhadrapada"
        assert chart_output["ascendant"]["sign"] == "Aries"

    def test_wholesign_house_untouched(self, chart_output):
        """DR-2: whole-sign house assignment is unchanged (arithmetic from lagna sign)."""
        asc_sign0 = int(chart_output["ascendant"]["sign_id"]) - 1
        for g in chart_output["grahas"]:
            planet_sign0 = int(g["sign_id"]) - 1
            assert g["house"] == ((planet_sign0 - asc_sign0) % 12) + 1


# ── (b) Fake-cusp sites now emit REAL Placidus cusps (not equal-house) ────────

class TestNoFakeCusps:
    def _cusp_longs_from_sensitive(self, chart_output):
        from ga_writers import ga_sensitive_writer as gsw
        rows = gsw._build_kp_cuspal_rows(
            {"LAGNA": chart_output["ascendant"]["longitude_deg"]},
            "test-chart", "lahiri_chitrapaksha", "test-build",
            "natal_engine/test", chart_output,
        )
        return {
            r["fact_subject"]: r["fact_value_num"]
            for r in rows if r["fact_key"] == "cusp_longitude_sidereal"
        }

    def test_sensitive_cusps_not_equal_house(self, chart_output):
        """ga_sensitive_writer: cusp longitudes are NOT all 30° apart (fake pattern)."""
        cusps = self._cusp_longs_from_sensitive(chart_output)
        assert len(cusps) == 12
        vals = [cusps[f"CUSP_{n}"] for n in range(1, 13)]
        # Fake equal-house had every gap == exactly 30.0. Assert at least one gap deviates.
        gaps = [((vals[(i + 1) % 12] - vals[i]) % 360.0) for i in range(12)]
        assert any(abs(g - 30.0) > 0.5 for g in gaps), "cusps still equal-house (fake)"

    def test_sensitive_cusp1_is_ascendant(self, chart_output):
        cusps = self._cusp_longs_from_sensitive(chart_output)
        asc = chart_output["ascendant"]["longitude_deg"]
        assert abs((cusps["CUSP_1"] - asc) % 360.0) < 1e-6

    def test_sensitive_cusps_match_placidus(self, chart_output):
        cusps = self._cusp_longs_from_sensitive(chart_output)
        plac = chart_output["bhava_chalit"]["placidus"]["cusp_boundaries"]
        for n in range(1, 13):
            assert abs(cusps[f"CUSP_{n}"] - plac[n - 1]) < 1e-6

    def test_nakshatra_emitter_cusps_not_equal_house(self, chart_output):
        from ga_writers.ga_nakshatra_emitters import emit_kp_lords
        rows = emit_kp_lords("test-chart", "lahiri_chitrapaksha", "test-build", chart_output)
        cusp_rows = [r for r in rows if r["fact_category"] == "cusp_kp_lords"]
        assert cusp_rows, "no cusp_kp_lords rows"
        # None may carry the EXTERNAL marker (real cusps ARE available here)
        assert not any("EXTERNAL_COMPUTATION_REQUIRED" in str(r.get("fact_value_text", ""))
                       for r in cusp_rows)


# ── (c) KP sub-lord is REAL (249-division), never the nakshatra-lord fake ─────

class TestRealSubLord:
    def test_sub_lord_is_real_division(self, chart_output):
        """The stored cusp sub_lord must equal compute_kp_lords()['sub_lord'] for the
        real Placidus cusp — and must NOT be forced equal to the nakshatra (star) lord."""
        from ga_writers import ga_sensitive_writer as gsw
        from ga_writers.ga_nakshatra_compute import compute_kp_lords
        rows = gsw._build_kp_cuspal_rows(
            {"LAGNA": chart_output["ascendant"]["longitude_deg"]},
            "test-chart", "lahiri_chitrapaksha", "test-build",
            "natal_engine/test", chart_output,
        )
        plac = chart_output["bhava_chalit"]["placidus"]["cusp_boundaries"]
        sub_by_cusp = {r["fact_subject"]: r["fact_value_text"]
                       for r in rows if r["fact_key"] == "sub_lord"}
        star_by_cusp = {r["fact_subject"]: r["fact_value_text"]
                        for r in rows if r["fact_key"] == "star_lord"}
        divergences = 0
        for n in range(1, 13):
            expected_sub = compute_kp_lords(plac[n - 1] % 360.0)["sub_lord"]
            assert sub_by_cusp[f"CUSP_{n}"] == expected_sub
            if sub_by_cusp[f"CUSP_{n}"] != star_by_cusp[f"CUSP_{n}"]:
                divergences += 1
        # Real sub-lord differs from star-lord for most cusps; the old fake made them
        # always identical. At least one real divergence proves it is not the fake.
        assert divergences >= 1, "sub_lord never differs from star_lord — still fake"

    def test_no_real_cusps_yields_external_marker_not_fake(self):
        """B.10: when bhava_chalit is absent, an honest EXTERNAL_COMPUTATION_REQUIRED
        marker is emitted rather than fabricated equal-house cusps."""
        from ga_writers import ga_sensitive_writer as gsw
        rows = gsw._build_kp_cuspal_rows(
            {"LAGNA": 12.0}, "test-chart", "lahiri_chitrapaksha", "test-build",
            "natal_engine/test", {},  # no bhava_chalit
        )
        assert rows
        assert all(r["fact_key"] == "cusp_longitude_sidereal" for r in rows)
        assert all(r["fact_value_num"] is None for r in rows)
        assert all("EXTERNAL_COMPUTATION_REQUIRED" in r["fact_value_text"] for r in rows)


# ── new L1 fact categories emitted by ga_positions_writer ─────────────────────

class TestChalitFacts:
    def test_positions_writer_emits_chalit_categories(self, chart_output):
        from ga_writers.ga_positions_writer import _build_chalit_rows
        rows = _build_chalit_rows(chart_output, "test-chart", "test-build",
                                  "lahiri_chitrapaksha", "2026-07-15T00:00:00Z")
        cats = {r["fact_category"] for r in rows}
        assert {"bhava_cusps", "house_chalit", "sandhi_flag"} <= cats
        # 12 houses × 2 systems × 3 edges = 72 bhava_cusps rows
        bhava = [r for r in rows if r["fact_category"] == "bhava_cusps"]
        assert len(bhava) == 72
        # Moon must carry a sandhi_flag=true row (the specimen)
        moon_flag = [r for r in rows if r["fact_category"] == "sandhi_flag"
                     and r["fact_subject"] == "MOON" and r["fact_key"] == "sandhi_flag"]
        assert moon_flag and moon_flag[0]["fact_value_text"] == "true"


# ── Governance: emitted chalit facts must be DECLARED in CHART_FACTS_SCHEMA.json ─
# Guards the drift_detector gate (ga_writers/gates.py): SELECT DISTINCT fact_category
# FROM chart_facts fails on any category/enum/range present in the DB but not declared.

class TestSchemaDeclaration:
    @staticmethod
    def _schema():
        import json
        import pathlib
        p = pathlib.Path(__file__).resolve().parents[1] / "ga_writers" / "CHART_FACTS_SCHEMA.json"
        return json.loads(p.read_text())

    @staticmethod
    def _chalit_rows(chart_output):
        from ga_writers.ga_positions_writer import _build_chalit_rows
        return _build_chalit_rows(chart_output, "test-chart", "test-build",
                                  "lahiri_chitrapaksha", "2026-07-15T00:00:00Z")

    def test_every_emitted_category_is_declared(self, chart_output):
        cats = {r["fact_category"] for r in self._chalit_rows(chart_output)}
        declared = set(self._schema().get("categories", {}).keys())
        undeclared = cats - declared
        assert not undeclared, f"undeclared chalit categories (drift gate would red): {undeclared}"

    def test_every_emitted_subject_is_declared(self, chart_output):
        schema_cats = self._schema()["categories"]
        by_cat: dict[str, set] = {}
        for r in self._chalit_rows(chart_output):
            by_cat.setdefault(r["fact_category"], set()).add(r["fact_subject"])
        for cat, subjects in by_cat.items():
            allowed = set(schema_cats[cat]["applies_to_subjects"])
            assert subjects <= allowed, f"{cat} emits undeclared subjects: {subjects - allowed}"

    def test_every_emitted_key_is_declared_with_matching_type(self, chart_output):
        schema_cats = self._schema()["categories"]
        for r in self._chalit_rows(chart_output):
            spec = schema_cats[r["fact_category"]]["allowed_keys"].get(r["fact_key"])
            assert spec is not None, f"{r['fact_category']}.{r['fact_key']} not declared"
            vt = spec["value_type"]
            if r["fact_value_num"] is not None:
                assert vt == "num", f"{r['fact_category']}.{r['fact_key']} num value vs type {vt}"
                lo, hi = spec["range"]
                assert lo <= r["fact_value_num"] <= hi, (
                    f"{r['fact_category']}.{r['fact_key']}={r['fact_value_num']} out of [{lo},{hi}]")
            if r["fact_value_text"] is not None and vt == "text_enum":
                assert r["fact_value_text"] in spec["enum"], (
                    f"{r['fact_category']}.{r['fact_key']}='{r['fact_value_text']}' not in enum")

    def test_verification_min_matches_emitted_status(self, chart_output):
        """_chalit_row sets verification_pass_status='single'; declared verification_min
        must match so the two-pass gate does not reject these rows."""
        schema_cats = self._schema()["categories"]
        for cat in ("bhava_cusps", "house_chalit", "sandhi_flag"):
            for key_spec in schema_cats[cat]["allowed_keys"].values():
                assert key_spec["verification_min"] == "single"
