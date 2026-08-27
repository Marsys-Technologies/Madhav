"""Candidate-revision release smoke validation."""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone

import pytest

from routers.nirmana_probe import _contract_digest
from scripts import nirmana_probe_release_smoke as smoke


class _Response(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def test_release_smoke_executes_both_full_contracts_and_binds_candidate(
    monkeypatch: pytest.MonkeyPatch,
):
    candidate_url = "https://probe-tag.run.app/internal/nirmana/probe"
    revision = "amjis-sidecar-probe-deadbeef"
    key = "release-smoke-secret"
    seen_assets: list[str] = []

    monkeypatch.setenv("NIRMANA_PROBE_CANDIDATE_URL", candidate_url)
    monkeypatch.setenv("NIRMANA_PROBE_EXPECTED_REVISION", revision)
    monkeypatch.setenv("PYTHON_SIDECAR_API_KEY", key)

    def fake_urlopen(request, timeout):
        assert request.full_url == candidate_url
        assert request.headers["X-api-key"] == key
        assert timeout == 120
        sent = json.loads(request.data)
        seen_assets.append(sent["asset_id"])
        digest = _contract_digest(sent["health_probe"])
        assert sent["probe_contract_sha256"] == digest
        payload = {
            "asset_id": sent["asset_id"],
            "probe_contract_sha256": digest,
            "runner_revision": revision,
            "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "result": {
                "status": "GREEN",
                "message": "All checks passed",
                "checks": [{"check": "typed_probe", "passed": True}],
            },
        }
        return _Response(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(smoke.urllib.request, "urlopen", fake_urlopen)

    assert smoke.main() == 0
    assert seen_assets == ["bg_panchanga", "bg_ephemeris_engine"]


def test_release_smoke_rejects_green_with_a_failed_check(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(request, timeout):
        sent = json.loads(request.data)
        payload = {
            "asset_id": sent["asset_id"],
            "probe_contract_sha256": sent["probe_contract_sha256"],
            "runner_revision": "candidate-revision",
            "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "result": {
                "status": "GREEN",
                "message": "inconsistent",
                "checks": [{"check": "typed_probe", "passed": False}],
            },
        }
        return _Response(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(smoke.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="failed check"):
        smoke._call_probe(
            candidate_url="https://candidate.run.app/internal/nirmana/probe",
            api_key="hidden",
            expected_revision="candidate-revision",
            asset_id="bg_panchanga",
            health_probe={"probe_type": "panchanga_engine"},
        )
