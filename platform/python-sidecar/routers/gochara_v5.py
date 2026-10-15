"""Read-only HTTP surface for an explicitly named sealed Gochara generation.

Refusals are answers (200); malformed input is 422; deployment/read faults are
named 5xx responses. Neither the database URL nor exception text is returned.
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
DEFAULT_LIMIT = 500
MAX_LIMIT = 5000
ERROR_DB_UNREACHABLE = 'gochara_v5_database_unreachable'
ERROR_SCHEMA_MISSING = 'gochara_v5_schema_missing'
ERROR_READ_FAILED = 'gochara_v5_read_failed'
EventClass = Annotated[str, StringConstraints(pattern=r'^[a-z][a-z0-9_]{0,63}$')]


class V5WindowsRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    chart_id: UUID
    generation: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]{0,15}$')
    event_classes: list[EventClass] | None = Field(default=None, min_length=1, max_length=64)
    date_from: AwareDatetime | None = None
    date_to: AwareDatetime | None = None
    at_instant: AwareDatetime | None = None
    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, strict=True)

    @model_validator(mode='after')
    def _instant_or_range(self):
        if self.at_instant is not None and (self.date_from is not None or self.date_to is not None):
            raise ValueError('instant and range are mutually exclusive')
        return self


def _authenticate(x_api_key: str = Header(default='')):
    expected = os.environ.get('PYTHON_SIDECAR_API_KEY', '')
    if not expected:
        raise HTTPException(503, detail='sidecar credential not configured')
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(401, detail='Invalid API key')


def _db_url():
    for name in ('DATABASE_URL', 'DIRECT_DATABASE_URL', 'POSTGRES_URL'):
        value = os.environ.get(name)
        if value:
            return value
    raise RuntimeError('no database URL configured')


def _close(conn):
    for name in ('rollback', 'close'):
        try:
            getattr(conn, name)()
        except Exception:
            # Cleanup faults must not replace the domain response or disclose a URL.
            logger.warning('[gochara_v5] connection %s failed', name)


def _connect():
    conn = psycopg.connect(_db_url(), connect_timeout=CONNECT_TIMEOUT_S,
                          options=f'-c statement_timeout={STATEMENT_TIMEOUT_MS} -c default_transaction_read_only=on')
    try:
        conn.read_only = True
        conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
    except Exception:
        _close(conn)
        raise
    return conn


@router.post('/gochara/v5/windows', dependencies=[Depends(_authenticate)])
def gochara_v5_windows(req: V5WindowsRequest) -> dict[str, Any]:
    try:
        conn = _connect()
    except Exception:
        raise HTTPException(503, detail={'error': ERROR_DB_UNREACHABLE}) from None
    try:
        return serving_reader.read_v5(conn, str(req.chart_id), req.generation,
            event_classes=req.event_classes, date_from=req.date_from, date_to=req.date_to,
            at_instant=req.at_instant, limit=req.limit)
    except serving_reader.ServingSchemaMissing:
        raise HTTPException(503, detail={'error': ERROR_SCHEMA_MISSING}) from None
    except psycopg.OperationalError:
        raise HTTPException(503, detail={'error': ERROR_DB_UNREACHABLE}) from None
    except Exception:
        raise HTTPException(500, detail={'error': ERROR_READ_FAILED}) from None
    finally:
        _close(conn)
