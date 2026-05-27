"""
jh_oracle_loader.py — Loader + validator for the pinned JH oracle fixture.

Usage:
    from natal_engine.fixtures.jh_oracle_loader import (
        load_jh_oracle, jh_oracle_present, JHOracleMissingError,
    )

    if jh_oracle_present():
        oracle = load_jh_oracle()
        # ... diff against engine output

If jh_oracle.json is absent (the unit 1.1 state — gate jh_oracle_pinned RED),
`load_jh_oracle()` raises JHOracleMissingError with an explicit message that
points the native at the action item. `jh_oracle_present()` is a non-raising
boolean used by tests to xfail/skip rather than fail.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_FIXTURES_DIR = Path(__file__).resolve().parent
JH_ORACLE_PATH = _FIXTURES_DIR / "jh_oracle.json"
JH_ORACLE_SCHEMA_PATH = _FIXTURES_DIR / "jh_oracle_schema.json"


class JHOracleMissingError(FileNotFoundError):
    """Raised when jh_oracle.json is not present in fixtures/.

    This is the expected state at unit 1.1 — the JH oracle export is a
    one-time operational input the native must produce. Until then the
    `jh_oracle_pinned` gate (G1) stays RED and unit 1.2 parity cannot run.
    """


class JHOracleInvalidError(ValueError):
    """Raised when jh_oracle.json is present but fails schema validation."""


def jh_oracle_present() -> bool:
    """Non-raising existence check used by parity tests for skip/xfail."""
    return JH_ORACLE_PATH.is_file()


def load_jh_oracle_schema() -> dict[str, Any]:
    if not JH_ORACLE_SCHEMA_PATH.is_file():
        raise FileNotFoundError(
            f"jh_oracle_schema.json missing at {JH_ORACLE_SCHEMA_PATH}; "
            "this should ship with unit 1.1."
        )
    with JH_ORACLE_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jh_oracle(strict: bool = True) -> dict[str, Any]:
    """Load + validate jh_oracle.json. Raises JHOracleMissingError if absent.

    When `strict=True` (default), the loaded JSON is validated against
    `jh_oracle_schema.json` via jsonschema. Validation failures raise
    JHOracleInvalidError with the underlying jsonschema error chained.
    """
    if not JH_ORACLE_PATH.is_file():
        raise JHOracleMissingError(
            "jh_oracle.json not present at "
            f"{JH_ORACLE_PATH}. The pinned Jagannatha Hora export is an "
            "operational input still owed by the native. Until it lands, gate "
            "`jh_oracle_pinned` (G1) is RED and the unit 1.2 parity assertion "
            "is skipped. To unblock: export the native's chart from JH and "
            "save it here in the schema documented at jh_oracle_schema.json."
        )

    with JH_ORACLE_PATH.open("r", encoding="utf-8") as f:
        oracle = json.load(f)

    if strict:
        try:
            import jsonschema
        except ImportError as exc:
            raise JHOracleInvalidError(
                "jsonschema not installed — cannot validate jh_oracle.json"
            ) from exc

        schema = load_jh_oracle_schema()
        try:
            jsonschema.validate(instance=oracle, schema=schema)
        except jsonschema.ValidationError as exc:
            raise JHOracleInvalidError(
                f"jh_oracle.json failed schema validation: {exc.message}"
            ) from exc

    return oracle


__all__ = [
    "JH_ORACLE_PATH",
    "JH_ORACLE_SCHEMA_PATH",
    "JHOracleMissingError",
    "JHOracleInvalidError",
    "jh_oracle_present",
    "load_jh_oracle",
    "load_jh_oracle_schema",
]
