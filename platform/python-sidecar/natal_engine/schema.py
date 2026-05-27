"""
schema.py — Canonical output schema for the natal_engine.

The engine emits a single JSON object per chart that can be appended as a JSONL
line. The schema is defined here twice:

1. As a JSON-Schema dict (`CHART_OUTPUT_SCHEMA`) — for validation via
   `jsonschema.validate(...)`. This is the authoritative contract.
2. As lightweight dataclasses (`GrahaState`, `Ascendant`, `House`, ...) for
   in-process construction with type-safety. The dataclasses serialise to dicts
   that satisfy the JSON-Schema.

We deliberately avoid Pydantic here because:
- pydantic is in `requirements.txt` for the sidecar runtime, but is not in the
  developer venv used for unit-tests.
- The natal_engine is a *pure module* (no FastAPI) and must remain importable
  with only stdlib + pyswisseph + jsonschema.

The schema is intentionally conservative: every field that the unit-1.2
JH-parity comparison will need is listed here, even if the underlying
computation is a stub today (e.g. Gulika/Mandi). That way unit 1.2 only has to
fill in numeric values, not extend the schema.

Provenance per MASTER_PLAN §15.2: every chart carries `chart_id`,
`engine_version`, `ayanamsha_config_id`, `inputs_hash`, `computed_at_iso`.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# JSON Schema (authoritative contract)
# ---------------------------------------------------------------------------

_GRAHA_SCHEMA = {
    "type": "object",
    "required": [
        "name", "longitude_deg", "sign", "sign_id",
        "nakshatra", "nakshatra_id", "pada",
        "retrograde", "speed_deg_per_day", "dignity_status",
    ],
    "properties": {
        "name": {"type": "string"},
        "longitude_deg": {"type": "number", "minimum": 0.0, "exclusiveMaximum": 360.0},
        "sign": {"type": "string"},
        "sign_id": {"type": "integer", "minimum": 1, "maximum": 12},
        "nakshatra": {"type": "string"},
        "nakshatra_id": {"type": "integer", "minimum": 1, "maximum": 27},
        "pada": {"type": "integer", "minimum": 1, "maximum": 4},
        "retrograde": {"type": "boolean"},
        "speed_deg_per_day": {"type": "number"},
        "dignity_status": {
            "type": "string",
            "enum": [
                "exalted", "moolatrikona", "own", "friend",
                "neutral", "enemy", "debilitated", "unknown",
            ],
        },
    },
}

_HOUSE_SCHEMA = {
    "type": "object",
    "required": ["house_num", "cusp_deg", "sign", "sign_id"],
    "properties": {
        "house_num": {"type": "integer", "minimum": 1, "maximum": 12},
        "cusp_deg": {"type": "number", "minimum": 0.0, "exclusiveMaximum": 360.0},
        "sign": {"type": "string"},
        "sign_id": {"type": "integer", "minimum": 1, "maximum": 12},
    },
}

_ASCENDANT_SCHEMA = {
    "type": "object",
    "required": ["longitude_deg", "sign", "sign_id", "nakshatra", "nakshatra_id", "pada"],
    "properties": {
        "longitude_deg": {"type": "number", "minimum": 0.0, "exclusiveMaximum": 360.0},
        "sign": {"type": "string"},
        "sign_id": {"type": "integer", "minimum": 1, "maximum": 12},
        "nakshatra": {"type": "string"},
        "nakshatra_id": {"type": "integer", "minimum": 1, "maximum": 27},
        "pada": {"type": "integer", "minimum": 1, "maximum": 4},
    },
}

_PROVENANCE_SCHEMA = {
    "type": "object",
    "required": [
        "chart_id", "engine_version", "ayanamsha_config_id",
        "inputs_hash", "computed_at_iso",
    ],
    "properties": {
        "chart_id": {"type": "string", "minLength": 1},
        "engine_version": {"type": "string", "minLength": 1},
        "ayanamsha_config_id": {"type": "string", "minLength": 1},
        "inputs_hash": {"type": "string", "minLength": 1},
        "computed_at_iso": {"type": "string", "minLength": 1},
    },
}

_INPUTS_SCHEMA = {
    "type": "object",
    "required": ["datetime_iso", "tz_offset_hours", "latitude_deg", "longitude_deg", "place_name"],
    "properties": {
        "datetime_iso": {"type": "string"},
        "tz_offset_hours": {"type": "number"},
        "latitude_deg": {"type": "number", "minimum": -90.0, "maximum": 90.0},
        "longitude_deg": {"type": "number", "minimum": -180.0, "maximum": 180.0},
        "place_name": {"type": "string"},
        "subject_label": {"type": "string"},
    },
}

CHART_OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "MARSYS-JIS Natal Engine — Chart Output",
    "type": "object",
    "required": [
        "provenance", "inputs", "ascendant", "houses", "grahas",
        "vargas", "dashas", "panchanga", "sensitive_points",
    ],
    "properties": {
        "provenance": _PROVENANCE_SCHEMA,
        "inputs": _INPUTS_SCHEMA,
        "ascendant": _ASCENDANT_SCHEMA,
        "houses": {
            "type": "array",
            "minItems": 12,
            "maxItems": 12,
            "items": _HOUSE_SCHEMA,
        },
        "grahas": {
            "type": "array",
            "minItems": 9,
            "maxItems": 9,
            "items": _GRAHA_SCHEMA,
        },
        "vargas": {
            "type": "object",
            "description": "Map of varga code (D1, D2, ... D60) → per-graha sign placements.",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "required": ["sign_id", "sign"],
                    "properties": {
                        "sign_id": {"type": "integer", "minimum": 1, "maximum": 12},
                        "sign": {"type": "string"},
                    },
                },
            },
        },
        "dashas": {
            "type": "object",
            "required": ["system", "mahadasha_sequence"],
            "properties": {
                "system": {"type": "string"},
                "mahadasha_sequence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["lord", "start_iso", "end_iso"],
                        "properties": {
                            "lord": {"type": "string"},
                            "start_iso": {"type": "string"},
                            "end_iso": {"type": "string"},
                        },
                    },
                },
            },
        },
        "panchanga": {
            "type": "object",
            "required": ["tithi", "vara", "nakshatra", "yoga", "karana"],
            "properties": {
                "tithi": {"type": "string"},
                "vara": {"type": "string"},
                "nakshatra": {"type": "string"},
                "yoga": {"type": "string"},
                "karana": {"type": "string"},
            },
        },
        "sensitive_points": {
            "type": "object",
            "description": "Gulika, Mandi, Upapada Lagna, and related. Stub in 1.1; filled in 1.2.",
            "additionalProperties": True,
        },
    },
}


# ---------------------------------------------------------------------------
# Dataclasses (typed in-process construction)
# ---------------------------------------------------------------------------

@dataclass
class Provenance:
    chart_id: str
    engine_version: str
    ayanamsha_config_id: str
    inputs_hash: str
    computed_at_iso: str


@dataclass
class Inputs:
    datetime_iso: str
    tz_offset_hours: float
    latitude_deg: float
    longitude_deg: float
    place_name: str
    subject_label: str = ""


@dataclass
class GrahaState:
    name: str
    longitude_deg: float
    sign: str
    sign_id: int
    nakshatra: str
    nakshatra_id: int
    pada: int
    retrograde: bool
    speed_deg_per_day: float
    dignity_status: str  # one of enum in schema


@dataclass
class Ascendant:
    longitude_deg: float
    sign: str
    sign_id: int
    nakshatra: str
    nakshatra_id: int
    pada: int


@dataclass
class House:
    house_num: int
    cusp_deg: float
    sign: str
    sign_id: int


@dataclass
class ChartOutput:
    provenance: Provenance
    inputs: Inputs
    ascendant: Ascendant
    houses: list[House]
    grahas: list[GrahaState]
    vargas: dict[str, dict[str, dict[str, Any]]]
    dashas: dict[str, Any]
    panchanga: dict[str, str]
    sensitive_points: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Validator helper
# ---------------------------------------------------------------------------

def validate_chart_output(payload: dict[str, Any]) -> None:
    """Validate a chart payload against CHART_OUTPUT_SCHEMA.

    Raises jsonschema.ValidationError on failure.
    """
    import jsonschema  # local import to keep module-import cheap
    jsonschema.validate(instance=payload, schema=CHART_OUTPUT_SCHEMA)
