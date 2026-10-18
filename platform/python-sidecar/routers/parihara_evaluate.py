"""Scoped, read-only cancellation evaluation; guarded by main.verify_api_key."""
from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator
import psycopg
from psycopg.rows import dict_row

from services.ka_muhurta_seva.parihara_eval import (
    REFERENCE_LOCATION, candidate_times, evaluate_candidate, load_rules,
)

router = APIRouter()


class Candidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_utc: str
    end_utc: str

    @model_validator(mode="after")
    def valid_interval(self):
        candidate_times(self.model_dump())
        return self


class Location(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    tz_offset_minutes: StrictInt = Field(ge=-840, le=840)


class PariharaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate: Candidate
    undertaking: str = Field(min_length=1)
    # Explicit None permits the documented location_missing response, no default place.
    location: Location | None = None
    location_basis: Literal["caller", "lattice_reference_location"] = "caller"
    dosas_present: list[str]

    @model_validator(mode="after")
    def valid_targets_and_origin(self):
        if any(not d.strip() or "*" in d for d in self.dosas_present):
            raise ValueError("dosas_present must name explicit targets, never a wildcard")
        if self.location_basis == "lattice_reference_location" and self.location is not None:
            if self.location.model_dump() != REFERENCE_LOCATION:
                raise ValueError("reference location must equal the disclosed lattice origin")
        return self


def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        value = os.environ.get(key)
        if value:
            return value
    raise RuntimeError("no database URL configured")


def _connect():
    conn = psycopg.connect(_db_url(), row_factory=dict_row, connect_timeout=5,
                           options="-c statement_timeout=10000")
    conn.read_only = True
    return conn


@router.post("/parihara_evaluate")
def parihara_evaluate(req: PariharaRequest) -> dict:
    if req.location is None:
        raise HTTPException(status_code=422, detail={"reason": "location_missing"})
    try:
        with _connect() as conn:
            rules = load_rules(conn, req.undertaking, req.dosas_present)
    except (psycopg.Error, RuntimeError):
        # Schema absence is refused, never interpreted as "no sourced rules".
        raise HTTPException(status_code=503, detail={"reason": "parihara_source_unavailable"}) from None
    return evaluate_candidate(candidate=req.candidate.model_dump(), undertaking=req.undertaking,
                              location=req.location.model_dump(), dosas_present=req.dosas_present,
                              location_basis=req.location_basis, rules=rules)
