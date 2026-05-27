"""
test_scaffold.py — Module imports, compute_chart shape, provenance, harness presence.

Covers unit 1.1 acceptance criteria 1, 2, 3 (parity collection).
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

NATIVE_INPUTS = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "place_name": "Bhubaneswar",
    "subject_label": "Abhisek Mohanty",
}


def test_module_imports_cleanly() -> None:
    """natal_engine must be importable as a pure module (no FastAPI etc)."""
    mod = importlib.import_module("natal_engine")
    assert hasattr(mod, "compute_chart"), "compute_chart missing from natal_engine"
    assert hasattr(mod, "ENGINE_VERSION_DEFAULT")
    assert hasattr(mod, "AYANAMSHA_DEFAULT")
    assert mod.ENGINE_VERSION_DEFAULT == "natal_engine/0.1.0-scaffold"


def test_compute_chart_emits_schema_valid_jsonl_for_native() -> None:
    """compute_chart returns a schema-valid dict for the native birth data."""
    from natal_engine import compute_chart

    out = compute_chart(NATIVE_INPUTS)

    # compute_chart validates internally when validate=True; reach further to
    # assert the visible shape so a future schema regression is obvious here.
    assert set(out.keys()) >= {
        "provenance", "inputs", "ascendant", "houses", "grahas",
        "vargas", "dashas", "panchanga", "sensitive_points",
    }
    assert len(out["houses"]) == 12
    assert len(out["grahas"]) == 9
    assert {g["name"] for g in out["grahas"]} == {
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    }
    assert "D1" in out["vargas"] and "D9" in out["vargas"]
    assert out["dashas"]["system"] == "vimshottari"
    assert len(out["dashas"]["mahadasha_sequence"]) == 9
    # Sanity-check against FORENSIC v8.0 panchanga spot-check (5/5 documented
    # in CLAUDE.md §E Phase 4C entry, build phase-4c-enrich-20260521-r2):
    assert out["panchanga"]["tithi"] == "Shukla Tritiya"
    assert out["panchanga"]["vara"] == "Ravivara"
    assert out["panchanga"]["nakshatra"] == "Purva Bhadrapada"
    assert out["panchanga"]["yoga"] == "Shiva"
    assert out["panchanga"]["karana"] == "Garaja"


def test_provenance_block_is_complete() -> None:
    """Provenance must carry non-empty engine_version + ayanamsha_config_id."""
    from natal_engine import compute_chart

    out = compute_chart(NATIVE_INPUTS)
    prov = out["provenance"]
    assert prov["engine_version"], "engine_version empty"
    assert prov["ayanamsha_config_id"], "ayanamsha_config_id empty"
    assert prov["chart_id"].startswith("chart_"), "chart_id must be content-addressed"
    assert len(prov["inputs_hash"]) == 64, "inputs_hash should be sha256 hex"
    assert prov["computed_at_iso"], "computed_at_iso empty"


def test_provenance_is_deterministic() -> None:
    """Same inputs + engine + ayanamsha → same chart_id + inputs_hash."""
    from natal_engine import compute_chart

    a = compute_chart(NATIVE_INPUTS)["provenance"]
    b = compute_chart(NATIVE_INPUTS)["provenance"]
    assert a["chart_id"] == b["chart_id"]
    assert a["inputs_hash"] == b["inputs_hash"]


def test_engine_version_propagates_to_provenance() -> None:
    """Caller-supplied engine_version must reach provenance verbatim."""
    from natal_engine import compute_chart

    out = compute_chart(NATIVE_INPUTS, engine_version="natal_engine/test-override")
    assert out["provenance"]["engine_version"] == "natal_engine/test-override"


def test_jh_parity_test_exists_and_is_collectable() -> None:
    """Acceptance criterion 3: test_jh_parity.py must be present + collectable
    by pytest, and currently skip (jh_oracle.json absent)."""
    here = Path(__file__).resolve().parent
    parity_file = here / "test_jh_parity.py"
    assert parity_file.is_file(), f"test_jh_parity.py missing at {parity_file}"

    # Sub-collect via pytest's machinery so we know it is actually collectable
    # (importable + has a recognised test). We use a subprocess to keep state
    # clean and to verify the same CLI behaviour the conductor will see.
    import subprocess
    import sys

    res = subprocess.run(
        [sys.executable, "-m", "pytest", str(parity_file), "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=str(here.parent.parent),  # platform/python-sidecar/
    )
    assert res.returncode == 0, f"collect-only failed: {res.stdout}\n{res.stderr}"
    assert "test_parity_against_oracle" in res.stdout, (
        f"expected test_parity_against_oracle in collection output, got: {res.stdout}"
    )


def test_jh_oracle_fixture_loader_is_present_and_reports_missing() -> None:
    """The loader exists and correctly reports the gate-red state."""
    from natal_engine.fixtures.jh_oracle_loader import (
        JHOracleMissingError,
        jh_oracle_present,
        load_jh_oracle,
    )

    assert jh_oracle_present() is False, "unit 1.1 ships without jh_oracle.json"
    with pytest.raises(JHOracleMissingError):
        load_jh_oracle()
