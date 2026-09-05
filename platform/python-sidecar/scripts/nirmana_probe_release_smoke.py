"""Release smoke for a zero-traffic Nirmana probe-runner candidate revision."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SIDECAR_ROOT = Path(__file__).resolve().parents[1]
if str(SIDECAR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIDECAR_ROOT))

from routers.nirmana_probe import _contract_digest


CONTRACTS_PATH = Path(__file__).with_name("nirmana_probe_contracts.json")


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required environment variable is missing: {name}")
    return value


def _parse_server_time(value: Any, *, request_started: datetime) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RuntimeError("observed_at is not an ISO UTC server timestamp")
    try:
        observed_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError("observed_at is not parseable") from exc
    now = datetime.now(timezone.utc)
    if observed_at < request_started - timedelta(seconds=30) or observed_at > now + timedelta(seconds=30):
        raise RuntimeError("observed_at is outside the authenticated request window")
    return observed_at


def _call_probe(
    *,
    candidate_url: str,
    api_key: str,
    expected_revision: str,
    asset_id: str,
    health_probe: dict[str, Any],
) -> None:
    digest = _contract_digest(health_probe)
    body = json.dumps(
        {
            "asset_id": asset_id,
            "probe_contract_sha256": digest,
            "health_probe": health_probe,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        candidate_url,
        data=body,
        method="POST",
        headers={"content-type": "application/json", "x-api-key": api_key},
    )
    request_started = datetime.now(timezone.utc)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status != 200:
                raise RuntimeError(f"candidate returned HTTP {response.status}")
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"candidate rejected {asset_id} with HTTP {exc.code}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"candidate was unreachable for {asset_id}: {exc.reason}") from None

    if not isinstance(payload, dict):
        raise RuntimeError(f"candidate returned a non-object for {asset_id}")
    if payload.get("asset_id") != asset_id:
        raise RuntimeError(f"candidate asset binding mismatch for {asset_id}")
    if payload.get("probe_contract_sha256") != digest:
        raise RuntimeError(f"candidate contract digest mismatch for {asset_id}")
    if payload.get("runner_revision") != expected_revision:
        raise RuntimeError(f"candidate revision binding mismatch for {asset_id}")
    _parse_server_time(payload.get("observed_at"), request_started=request_started)

    result = payload.get("result")
    if not isinstance(result, dict) or result.get("status") != "GREEN":
        raise RuntimeError(f"candidate probe did not return GREEN for {asset_id}")
    checks = result.get("checks")
    if not isinstance(checks, list) or not checks:
        raise RuntimeError(f"candidate probe returned no checks for {asset_id}")
    if any(not isinstance(check, dict) or check.get("passed") is not True for check in checks):
        raise RuntimeError(f"candidate probe returned a failed check for {asset_id}")


def main() -> int:
    candidate_url = _required_env("NIRMANA_PROBE_CANDIDATE_URL")
    if not candidate_url.startswith("https://") or not candidate_url.endswith("/internal/nirmana/probe"):
        raise RuntimeError("candidate URL must be the deployed HTTPS probe route")
    api_key = _required_env("PYTHON_SIDECAR_API_KEY")
    expected_revision = _required_env("NIRMANA_PROBE_EXPECTED_REVISION")
    contracts = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))

    for asset_id in ("bg_panchanga", "bg_ephemeris_engine", "ka_graha_sancara"):
        health_probe = contracts.get(asset_id)
        if not isinstance(health_probe, dict):
            raise RuntimeError(f"full release contract is missing for {asset_id}")
        _call_probe(
            candidate_url=candidate_url,
            api_key=api_key,
            expected_revision=expected_revision,
            asset_id=asset_id,
            health_probe=health_probe,
        )
        print(f"Nirmana candidate probe passed: {asset_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Nirmana candidate probe failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
