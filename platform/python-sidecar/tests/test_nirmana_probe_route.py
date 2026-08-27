"""Authenticated deployed Nirmana service-probe runner contract."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import nirmana_probe


API_KEY = "test-probe-runner-key"
PANCHANGA_PROBE = {
    "probe_type": "panchanga_engine",
    "forensic_lat": 20.2961,
    "forensic_expected": {"vara": "Ravivara", "tithi": "Shukla Tritiya"},
}


def _digest(probe: dict) -> str:
    canonical = json.dumps(
        {"health_probe": probe}, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_contract_digest_matches_lifecycle_clients_javascript_canonical_bytes():
    # Generated independently with definitions.ts stableJson + node:crypto.
    assert _digest(PANCHANGA_PROBE) == (
        "457d0d91a9b15f1fd4c559c80419f9efa36bf5e0aaad38d63019776b73e73e87"
    )
    assert nirmana_probe._contract_digest(PANCHANGA_PROBE) == _digest(PANCHANGA_PROBE)


@pytest.mark.parametrize(
    ("numeric", "javascript_digest"),
    [
        (1e-7, "97e0cc047772047fdec8bf771848a7975a590ed3a442a2b8835cdba8919ab0f8"),
        (1e20, "dd9ff4a80519f3f827b82e7de6bcaf660f2a480d087569f46b473514ac8df309"),
        (-0.0, "b845bb190310b83f43e6a0f01a7002d21698a3b3d19fd616dd3724cbf9176a64"),
    ],
)
def test_contract_digest_matches_javascript_numeric_edge_vectors(
    numeric: float, javascript_digest: str
):
    probe = {"probe_type": "panchanga_engine", "numeric": numeric}
    assert nirmana_probe._contract_digest(probe) == javascript_digest


def test_full_frozen_release_contracts_match_javascript_digests():
    contracts_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "nirmana_probe_contracts.json"
    )
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    assert nirmana_probe._contract_digest(contracts["bg_panchanga"]) == (
        "febfe3379c97f5a02f88b56d6eb6894e2f3aa9e50d1081561aaae4b56de7dbf2"
    )
    assert nirmana_probe._contract_digest(contracts["bg_ephemeris_engine"]) == (
        "e94a594d245b97251bc731757b56dac406433e12c8daa4b1df1d478e8e9ae1c4"
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("PYTHON_SIDECAR_API_KEY", API_KEY)
    monkeypatch.setenv("K_REVISION", "amjis-sidecar-01234-abc")
    app = FastAPI()
    app.include_router(nirmana_probe.router, prefix="/internal/nirmana")
    return TestClient(app)


def _post(client: TestClient, *, key: str | None = API_KEY, **overrides):
    body = {
        "asset_id": "bg_panchanga",
        "probe_contract_sha256": _digest(PANCHANGA_PROBE),
        "health_probe": PANCHANGA_PROBE,
        **overrides,
    }
    headers = {"x-api-key": key} if key is not None else {}
    return client.post("/internal/nirmana/probe", json=body, headers=headers)


def test_probe_route_is_mounted_on_deployed_sidecar_app():
    from main import app

    assert any(
        route.path == "/internal/nirmana/probe" and "POST" in (route.methods or set())
        for route in app.routes
    )


@pytest.mark.parametrize("key", [None, "", "wrong-key"])
def test_probe_route_rejects_missing_or_invalid_key_before_execution(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, key: str | None
):
    called = False

    def should_not_run(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("probe must not execute")

    monkeypatch.setattr(nirmana_probe, "run_health_probe", should_not_run)
    response = _post(client, key=key)

    assert response.status_code == 401
    assert called is False


def test_probe_route_fails_closed_when_server_key_is_unconfigured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("PYTHON_SIDECAR_API_KEY")
    response = _post(client)
    assert response.status_code == 503


def test_probe_route_authenticates_before_disclosing_body_validation(client: TestClient):
    response = client.post("/internal/nirmana/probe", json={})
    assert response.status_code == 401


def test_probe_route_rejects_digest_mismatch_before_execution(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    called = False

    def should_not_run(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(nirmana_probe, "run_health_probe", should_not_run)
    response = _post(client, probe_contract_sha256="0" * 64)

    assert response.status_code == 409
    assert called is False


@pytest.mark.parametrize(
    ("asset_id", "probe_type"),
    [
        ("bg_panchanga", "ephemeris_engine"),
        ("bg_ephemeris_engine", "panchanga_engine"),
        ("bg_unknown_service", "panchanga_engine"),
    ],
)
def test_probe_route_rejects_asset_probe_type_mismatch(
    client: TestClient, asset_id: str, probe_type: str
):
    probe = {"probe_type": probe_type}
    response = _post(
        client,
        asset_id=asset_id,
        health_probe=probe,
        probe_contract_sha256=_digest(probe),
    )
    assert response.status_code == 422


def test_probe_route_returns_server_bound_passing_observation(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        nirmana_probe,
        "run_health_probe",
        lambda asset_id, probe: {
            "status": "GREEN",
            "message": "All checks passed",
            "checks": [{"check": "typed_probe", "passed": True}],
        },
    )

    response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "asset_id": "bg_panchanga",
        "probe_contract_sha256": _digest(PANCHANGA_PROBE),
        "observed_at": body["observed_at"],
        "runner_revision": "amjis-sidecar-01234-abc",
        "result": {
            "status": "GREEN",
            "message": "All checks passed",
            "checks": [{"check": "typed_probe", "passed": True}],
        },
    }
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", body["observed_at"])


def test_probe_route_binds_executed_failed_result_without_promoting_it(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        nirmana_probe,
        "run_health_probe",
        lambda *_args: {
            "status": "down",
            "message": "typed check failed",
            "checks": [{"check": "typed_probe", "passed": False}],
        },
    )
    response = _post(client)
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "down"
    assert response.json()["result"]["checks"][0]["passed"] is False


def test_probe_route_fails_closed_without_deployed_runner_revision(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("K_REVISION")
    response = _post(client)
    assert response.status_code == 503


def test_probe_route_sanitizes_unexpected_runner_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        nirmana_probe,
        "run_health_probe",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("secret internal detail")),
    )
    response = _post(client)
    assert response.status_code == 503
    assert "secret internal detail" not in response.text
