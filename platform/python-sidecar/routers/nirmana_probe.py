"""Authenticated, deployed execution surface for typed Nirmana service probes."""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Literal

import jcs
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from pipeline.orchestrator.service_probes import run_health_probe

logger = logging.getLogger(__name__)
router = APIRouter()

_ASSET_PROBE_TYPES = {
    "bg_panchanga": "panchanga_engine",
    "bg_ephemeris_engine": "ephemeris_engine",
    "ka_graha_sancara": "graha_sancara_forensic",
    "ka_tulana": "tulana_ranking_forensic",
    "ka_dasha_kala": "dasha_kala_proxy_integrity",
    "ka_muhurta_seva": "muhurta_seva_forensic",
}


class ProbeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(min_length=1, max_length=256)
    probe_contract_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    health_probe: dict[str, Any]


class ProbeCheck(BaseModel):
    model_config = ConfigDict(extra="allow")

    check: str = Field(min_length=1, max_length=256)
    passed: bool


class ProbeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["GREEN", "degraded", "down"]
    message: str
    checks: list[ProbeCheck] = Field(min_length=1)


class ProbeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str
    probe_contract_sha256: str
    observed_at: str
    runner_revision: str
    result: ProbeResult


def _contract_digest(health_probe: dict[str, Any]) -> str:
    """Mirror ECMAScript JSON.stringify number/string bytes with sorted keys."""
    try:
        canonical = jcs.canonicalize({"health_probe": health_probe})
    except (OverflowError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Invalid health-probe contract") from exc
    return hashlib.sha256(canonical).hexdigest()


def _authenticate(x_api_key: str = Header(default="")) -> None:
    expected = os.environ.get("PYTHON_SIDECAR_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Probe runner is unavailable")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


def _validate_result(raw_result: Any) -> ProbeResult:
    try:
        result = ProbeResult.model_validate(raw_result)
    except Exception as exc:
        raise RuntimeError("probe returned an invalid result") from exc

    passed = [check.passed for check in result.checks]
    expected_status = "GREEN" if all(passed) else ("degraded" if any(passed) else "down")
    if result.status != expected_status:
        raise RuntimeError("probe result status disagrees with its checks")
    return result


@router.post("/probe", response_model=ProbeResponse, dependencies=[Depends(_authenticate)])
def execute_probe(
    request: ProbeRequest,
) -> ProbeResponse:
    """Execute one allowlisted service probe and bind result to contract + revision."""
    runner_revision = os.environ.get("K_REVISION", "").strip()
    if not runner_revision:
        raise HTTPException(status_code=503, detail="Probe runner is unavailable")

    expected_probe_type = _ASSET_PROBE_TYPES.get(request.asset_id)
    if expected_probe_type is None or request.health_probe.get("probe_type") != expected_probe_type:
        raise HTTPException(status_code=422, detail="Asset and probe type do not match")

    actual_digest = _contract_digest(request.health_probe)
    if not secrets.compare_digest(request.probe_contract_sha256, actual_digest):
        raise HTTPException(status_code=409, detail="Probe contract digest mismatch")

    try:
        result = _validate_result(run_health_probe(request.asset_id, request.health_probe))
    except Exception:
        logger.exception("Nirmana typed probe execution failed for %s", request.asset_id)
        raise HTTPException(status_code=503, detail="Probe execution failed") from None

    observed_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return ProbeResponse(
        asset_id=request.asset_id,
        probe_contract_sha256=actual_digest,
        observed_at=observed_at,
        runner_revision=runner_revision,
        result=result,
    )
