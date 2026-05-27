"""
natal_engine — JH-equivalent deterministic natal chart engine.

Pure-Python module. NO LLM imports anywhere (enforced by test_no_llm.py).
Owns the compute path that unit 1.2 will lock against the pinned
Jagannatha Hora oracle (G1).

Public surface: `compute_chart(inputs, engine_version, ayanamsha_config) -> dict`.

The returned dict satisfies `schema.CHART_OUTPUT_SCHEMA` and can be appended
as one JSONL line.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

import swisseph as swe

from .ascendant import compute_ascendant
from .dashas import compute_vimshottari_mahadasha
from .dignities import refine_dignities
from .houses import compute_houses_whole_sign
from .panchanga import compute_panchanga
from .positions import compute_graha_states, set_ayanamsha
from .provenance import build_provenance
from .schema import CHART_OUTPUT_SCHEMA, Inputs, validate_chart_output
from .sensitive_points import compute_sensitive_points
from .vargas import compute_vargas

ENGINE_VERSION_DEFAULT = "natal_engine/0.1.0-scaffold"
AYANAMSHA_DEFAULT = "lahiri"


def _parse_inputs(inputs: dict[str, Any]) -> tuple[Inputs, datetime, float]:
    """Coerce caller's inputs dict to the canonical Inputs dataclass + jd_ut.

    Required keys: datetime_iso (ISO-8601 local time, no offset),
    tz_offset_hours, latitude_deg, longitude_deg, place_name.
    Optional: subject_label.
    """
    inp = Inputs(
        datetime_iso=str(inputs["datetime_iso"]),
        tz_offset_hours=float(inputs["tz_offset_hours"]),
        latitude_deg=float(inputs["latitude_deg"]),
        longitude_deg=float(inputs["longitude_deg"]),
        place_name=str(inputs["place_name"]),
        subject_label=str(inputs.get("subject_label", "")),
    )

    local_dt = datetime.fromisoformat(inp.datetime_iso)
    if local_dt.tzinfo is not None:
        utc_dt = local_dt.astimezone(timezone.utc)
    else:
        # Treat as local wall-clock at inp.tz_offset_hours
        utc_dt = (local_dt - _hours_to_timedelta(inp.tz_offset_hours)).replace(
            tzinfo=timezone.utc
        )

    jd_ut = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
        swe.GREG_CAL,
    )
    return inp, utc_dt, jd_ut


def _hours_to_timedelta(hours: float):
    from datetime import timedelta
    return timedelta(hours=hours)


def compute_chart(
    inputs: dict[str, Any],
    engine_version: str = ENGINE_VERSION_DEFAULT,
    ayanamsha_config: str = AYANAMSHA_DEFAULT,
    validate: bool = True,
) -> dict[str, Any]:
    """Compute a natal chart and return a schema-valid dict (JSONL-emittable).

    Parameters
    ----------
    inputs : dict
        Required keys: datetime_iso, tz_offset_hours, latitude_deg,
        longitude_deg, place_name. Optional: subject_label.
    engine_version : str
        Identity string baked into provenance + chart_id.
    ayanamsha_config : str
        Passed to `positions.set_ayanamsha(...)`. Default 'lahiri'.
    validate : bool
        If True (default), the output is checked against CHART_OUTPUT_SCHEMA
        before returning. Set False for hot paths; tests always validate.
    """
    inp, utc_dt, jd_ut = _parse_inputs(inputs)

    set_ayanamsha(ayanamsha_config)

    grahas = refine_dignities(compute_graha_states(jd_ut))
    ascendant = compute_ascendant(jd_ut, inp.latitude_deg, inp.longitude_deg)
    houses = compute_houses_whole_sign(ascendant)
    vargas = compute_vargas(grahas, ascendant_lon=ascendant.longitude_deg)
    sun = next(g for g in grahas if g.name == "Sun")
    moon = next(g for g in grahas if g.name == "Moon")
    dashas = compute_vimshottari_mahadasha(moon, utc_dt)
    panchanga = compute_panchanga(sun, moon, utc_dt.weekday())
    sensitive = compute_sensitive_points(jd_ut, inp.latitude_deg, inp.longitude_deg, grahas, ascendant)

    provenance = build_provenance(
        inputs=asdict(inp),
        engine_version=engine_version,
        ayanamsha_config_id=ayanamsha_config,
    )

    payload: dict[str, Any] = {
        "provenance": asdict(provenance),
        "inputs": asdict(inp),
        "ascendant": asdict(ascendant),
        "houses": [asdict(h) for h in houses],
        "grahas": [asdict(g) for g in grahas],
        "vargas": vargas,
        "dashas": dashas,
        "panchanga": panchanga,
        "sensitive_points": sensitive,
    }

    if validate:
        validate_chart_output(payload)

    return payload


__all__ = [
    "compute_chart",
    "ENGINE_VERSION_DEFAULT",
    "AYANAMSHA_DEFAULT",
    "CHART_OUTPUT_SCHEMA",
]
