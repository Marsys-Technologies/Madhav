"""Internal-consistency tests for the top-level compute_chart contract."""
from __future__ import annotations

from pyjhora_adapter import ENGINE_VERSION, compute_chart

_REQUIRED_KEYS = {
    "provenance", "inputs", "ascendant", "houses", "grahas", "vargas",
    "dashas", "panchanga", "sensitive_points", "ayanamsha",
}


def test_required_keys_present(native_chart):
    for k in _REQUIRED_KEYS:
        assert k in native_chart, f"missing top-level key: {k}"


def test_engine_version_stamped(native_chart):
    assert native_chart["provenance"]["engine_version"] == ENGINE_VERSION
    assert ENGINE_VERSION == "pyjhora/1.0.0"


def test_grahas_shape(native_chart):
    grahas = native_chart["grahas"]
    assert len(grahas) == 9
    required = {
        "name", "longitude_deg", "sign", "sign_lord", "nakshatra",
        "nakshatra_pada", "nakshatra_lord", "retrograde", "combust",
    }
    for g in grahas:
        assert required <= set(g.keys()), f"graha missing keys: {required - set(g.keys())}"


def test_ascendant_shape(native_chart):
    asc = native_chart["ascendant"]
    for k in ("longitude_deg", "sign", "sign_lord", "sign_id"):
        assert k in asc


def test_houses_shape(native_chart):
    houses = native_chart["houses"]
    assert len(houses) == 12
    for i, h in enumerate(houses, start=1):
        assert h["house_number"] == i
        assert "sign" in h and "sign_lord" in h


def test_panchanga_shape(native_chart):
    p = native_chart["panchanga"]
    for anga in ("tithi", "vara", "nakshatra", "yoga", "karana"):
        assert anga in p and isinstance(p[anga], str) and p[anga]


def test_ayanamsha_block(native_chart):
    a = native_chart["ayanamsha"]
    assert a["id"] == "lahiri"
    assert isinstance(a["value_deg"], float)
    assert 23.0 < a["value_deg"] < 24.5  # Lahiri ~23.6 deg in 1984


def test_provenance_fields(native_chart):
    prov = native_chart["provenance"]
    for k in ("engine_version", "ayanamsha_config_id", "computed_at_iso"):
        assert k in prov


def test_determinism_with_fixed_timestamp(native_inputs):
    """Same inputs + same computed_at_iso ⇒ identical grahas/ascendant."""
    kw = dict(ayanamsha_id="lahiri", computed_at_iso="2026-06-01T00:00:00+00:00")
    a = compute_chart(inputs=dict(native_inputs), **kw)
    b = compute_chart(inputs=dict(native_inputs), **kw)
    assert a["grahas"] == b["grahas"]
    assert a["ascendant"] == b["ascendant"]
    assert a["panchanga"] == b["panchanga"]


def test_l25_builder_consumes_output(native_chart):
    """The L2.5 builder must consume the adapter's chart_output without error
    and emit non-empty chart_facts (guards the writer contract)."""
    from pyjhora_adapter import build_all
    rows = build_all(native_chart, "native_test", "build_test_1")
    assert "chart_facts" in rows
    assert len(rows["chart_facts"]) > 0
