"""routers/gochara_v5.py -- the read route over a SEALED governed Gochara generation (serving path work item W2).

    POST /api/compute/gochara/v5/windows

A thin HTTP surface over `services.gochara_kernel.serving_reader.read_v5`. The reader decides everything about the
answer; this module only validates the request, opens a READ-ONLY connection, and maps outcomes to HTTP:

  * 200 -- an envelope. A refusal (`refusal.code` set: unknown / unpublished / unsealed / test-slice generation, a
           request outside the served horizon, an inverted range ...) is an ANSWER and is also 200.
  * 422 -- malformed input (not a UUID, an instant without an offset, an unknown field, a limit out of bounds,
           `at_instant` together with a date range).
  * 401 / 503 -- the API key is wrong / the server has no key configured (fail-closed, as `yoga_formation_band`).
  * 503 `gochara_v5_database_unreachable` -- no connection could be opened, or it was lost.
  * 503 `gochara_v5_schema_missing` -- the connected database lacks a table the reader needs.
  * 500 `gochara_v5_read_failed` -- any other failure while reading.
  A failure is never turned into an empty envelope.

Nothing is written: the session is opened with `default_transaction_read_only=on`, one REPEATABLE READ read-only
transaction gives the reader a single snapshot, and it is rolled back (never committed) before the connection closes.
This module is imported only by `main.py`; no registered writer imports it.
"""
from __future__ import annotations

import logging
import os
import secrets
from typing import Annotated, Any
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

from services.gochara_kernel import serving_reader

logger = logging.getLogger(__name__)

router = APIRouter()

STATEMENT_TIMEOUT_MS = 15000
CONNECT_TIMEOUT_S = 5
#: paging bounds of the HTTP surface (the reader itself takes any positive limit, or none)
DEFAULT_LIMIT = 500
MAX_LIMIT = 5000

ERROR_DB_UNREACHABLE = "gochara_v5_database_unreachable"
ERROR_SCHEMA_MISSING = "gochara_v5_schema_missing"
ERROR_READ_FAILED = "gochara_v5_read_failed"

EventClass = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


class V5WindowsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chart_id: UUID
    generation: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,15}$")
    event_classes: list[EventClass] | None = Field(default=None, min_length=1, max_length=64)
    date_from: AwareDatetime | None = None
    date_to: AwareDatetime | None = None
    at_instant: AwareDatetime | None = None
    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)

    @model_validator(mode="after")
    def _instant_or_range(self) -> "V5WindowsRequest":
        if self.at_instant is not None and (self.date_from is not None or self.date_to is not None):
            raise ValueError("at_instant and date_from/date_to are mutually exclusive")
        return self


def _authenticate(x_api_key: str = Header(default="")) -> None:
    """Fail-closed: this route reads chart data, so an unconfigured server key is unavailable, never anonymous
    (same posture as routers/yoga_formation_band.py and routers/nirmana_probe.py)."""
    expected = os.environ.get("PYTHON_SIDECAR_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="sidecar credential not configured")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key)
        if val:
            return val
    raise RuntimeError("no database URL configured")


def _connect() -> Any:
    """A READ-ONLY session: the server refuses any write (`default_transaction_read_only`), and the one transaction
    the reader runs in is REPEATABLE READ so every statement of an answer sees the same snapshot."""
    conn = psycopg.connect(
        _db_url(),
        options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS} -c default_transaction_read_only=on",
        connect_timeout=CONNECT_TIMEOUT_S,
    )
    conn.read_only = True
    conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
    return conn


def _close(conn: Any) -> None:
    for step in ("rollback", "close"):                            # never commit; a failed cleanup must not mask the answer
        try:
            getattr(conn, step)()
        except Exception:  # noqa: BLE001
            logger.warning("[gochara_v5] connection %s failed", step, exc_info=True)


@router.post("/gochara/v5/windows", dependencies=[Depends(_authenticate)])
def gochara_v5_windows(req: V5WindowsRequest) -> dict[str, Any]:
    try:
        conn = _connect()
    except Exception:
        logger.exception("[gochara_v5] database unreachable chart=%s", req.chart_id)
        raise HTTPException(status_code=503, detail={"error": ERROR_DB_UNREACHABLE}) from None
    try:
        return serving_reader.read_v5(
            conn, str(req.chart_id), req.generation, event_classes=req.event_classes,
            date_from=req.date_from, date_to=req.date_to, at_instant=req.at_instant, limit=req.limit)
    except serving_reader.ServingSchemaMissing:
        logger.exception("[gochara_v5] serving schema missing chart=%s generation=%s", req.chart_id, req.generation)
        raise HTTPException(status_code=503, detail={"error": ERROR_SCHEMA_MISSING}) from None
    except psycopg.OperationalError:
        logger.exception("[gochara_v5] connection lost chart=%s generation=%s", req.chart_id, req.generation)
        raise HTTPException(status_code=503, detail={"error": ERROR_DB_UNREACHABLE}) from None
    except Exception:
        logger.exception("[gochara_v5] read failed chart=%s generation=%s", req.chart_id, req.generation)
        raise HTTPException(status_code=500, detail={"error": ERROR_READ_FAILED}) from None
    finally:
        _close(conn)
