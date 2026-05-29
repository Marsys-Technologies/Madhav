"""
natal_engine — JH-equivalent deterministic natal chart engine.

Pure-Python module. NO LLM imports anywhere (enforced by test_no_llm.py).
Owns the compute path that unit 1.2 locks against the pinned Jagannatha Hora
oracle (G1).

Public surface: `compute_chart(inputs, engine_version, ayanamsha_id) -> dict`.

The returned dict satisfies `schema.CHART_OUTPUT_SCHEMA` and can be appended
as one JSONL line.

Determinism contract: same `inputs` + `engine_version` + `ayanamsha_id`
⇒ byte-identical output across runs (modulo `computed_at_iso` if a fresh
timestamp is used; pass an explicit `computed_at_iso` to fix that too).
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

import swisseph as swe

from .ascendant import compute_ascendant
from .ayanamsha_registry import (
    AYANAMSHA_REGISTRY,
    apply_ayanamsha,
    ayanamsha_value_deg,
    list_ayanamsha_ids,
)
from .dashas import compute_vimshottari_mahadasha
from .dignities import refine_dignities
from .houses import compute_houses_whole_sign
from .panchanga import compute_panchanga
from .positions import compute_graha_states, compute_lilith_states, compute_node_states, compute_outer_bodies, set_ayanamsha
from .provenance import build_provenance
from .schema import CHART_OUTPUT_SCHEMA, Inputs, validate_chart_output
from .sensitive_points import compute_sensitive_points
from .vargas import compute_vargas

# Unit 1.2 (G1 parity) — engine identity stamped on every output's provenance.
ENGINE_VERSION_DEFAULT = "natal_engine/0.2.0-jh-parity"
# Canonical sidereal-zero — see ayanamsha_registry.AYANAMSHA_REGISTRY["jh_true_chitra"].
AYANAMSHA_DEFAULT = "jh_true_chitra"


def _hours_to_timedelta(hours: float):
    from datetime import timedelta
    return timedelta(hours=hours)


def _parse_inputs(inputs: dict[str, Any]) -> tuple[Inputs, datetime, float]:
    """Coerce caller's inputs dict to the canonical Inputs dataclass + jd_ut.

    Required keys: datetime_iso (ISO-8601 local time, with or without offset),
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


def _vara_local(local_wall_dt: datetime, tz_offset_hours: float) -> int:
    """Vara is computed from the LOCAL civil weekday at birth (Sunday → Ravivara).

    `datetime.weekday()` returns Mon=0..Sun=6. We pass that index through
    `panchanga._vara_from_weekday(...)`.
    """
    return local_wall_dt.weekday()


def compute_chart(
    inputs: dict[str, Any],
    engine_version: str = ENGINE_VERSION_DEFAULT,
    ayanamsha_id: str | None = None,
    *,
    ayanamsha_config: str | None = None,  # deprecated alias kept for 1.1 callers
    validate: bool = True,
    computed_at_iso: str | None = None,
) -> dict[str, Any]:
    """Compute a natal chart and return a schema-valid dict (JSONL-emittable).

    Parameters
    ----------
    inputs : dict
        Required keys: datetime_iso, tz_offset_hours, latitude_deg,
        longitude_deg, place_name. Optional: subject_label.
    engine_version : str
        Identity string baked into provenance + chart_id.
    ayanamsha_id : str | None
        Registry id from `ayanamsha_registry.AYANAMSHA_REGISTRY`. Defaults to
        AYANAMSHA_DEFAULT (`jh_true_chitra`). Accepts legacy 1.1 strings
        ('lahiri', 'krishnamurti', 'raman', 'lahiri-chitrapaksha-true') for
        back-compat via positions.set_ayanamsha.
    ayanamsha_config : str | None
        Deprecated alias for `ayanamsha_id` (kept for unit 1.1 callers).
    validate : bool
        If True (default), the output is checked against CHART_OUTPUT_SCHEMA
        before returning. Set False for hot paths; tests always validate.
    computed_at_iso : str | None
        If provided, used verbatim in provenance.computed_at_iso (deterministic
        byte-identical output across runs). If None, the current UTC ISO
        timestamp is stamped.
    """
    inp, utc_dt, jd_ut = _parse_inputs(inputs)

    # Resolve ayanamsha (new id > deprecated alias > default)
    effective_ayanamsha = (
        ayanamsha_id if ayanamsha_id is not None
        else ayanamsha_config if ayanamsha_config is not None
        else AYANAMSHA_DEFAULT
    )

    # Apply sidereal mode — registry ids get the SIDM_USER pin path when needed.
    if effective_ayanamsha in AYANAMSHA_REGISTRY:
        ayan_value_deg = apply_ayanamsha(jd_ut, effective_ayanamsha)
    else:
        # Legacy unit-1.1 alias path
        set_ayanamsha(effective_ayanamsha, jd_ut=jd_ut)
        ayan_value_deg = swe.get_ayanamsa_ut(jd_ut)

    grahas = refine_dignities(compute_graha_states(jd_ut))
    ascendant = compute_ascendant(jd_ut, inp.latitude_deg, inp.longitude_deg)
    houses = compute_houses_whole_sign(ascendant)
    vargas = compute_vargas(grahas, ascendant_lon=ascendant.longitude_deg)
    sun = next(g for g in grahas if g.name == "Sun")
    moon = next(g for g in grahas if g.name == "Moon")
    dashas = compute_vimshottari_mahadasha(moon, utc_dt)

    # Vara: use the LOCAL civil weekday (vara cycles by sunrise, but for the
    # natal panchanga we pin to the local civil day per JH convention).
    local_wall_dt = datetime.fromisoformat(inp.datetime_iso)
    if local_wall_dt.tzinfo is not None:
        local_wall_dt = local_wall_dt.replace(tzinfo=None)
    panchanga = compute_panchanga(
        sun, moon, _vara_local(local_wall_dt, inp.tz_offset_hours)
    )

    sensitive = compute_sensitive_points(
        jd_ut, inp.latitude_deg, inp.longitude_deg, grahas, ascendant
    )

    # E-03: emit both True Node (osculating) and Mean Node Rahu/Ketu as
    # separate entries under `node_variants`.  This lives outside `grahas`
    # (which must remain exactly 9 entries per schema) and outside the
    # JSON-Schema validation envelope so the strict `grahas` minItems/maxItems
    # contract is preserved.
    node_variants = compute_node_states(
        jd_ut,
        ayanamsha_deg=ayan_value_deg,
        geo_lat=inp.latitude_deg,
        geo_lon=inp.longitude_deg,
    )

    # E-04: emit Mean Lilith (MEAN_APOG = 12) and True Lilith (OSCU_APOG = 13).
    # These are virtual points on the Moon's orbit (apogee), not real bodies.
    # Stored outside `grahas` to preserve the 9-graha schema invariant.
    lilith_variants = compute_lilith_states(
        jd_ut,
        ayanamsha_deg=ayan_value_deg,
        geo_lat=inp.latitude_deg,
        geo_lon=inp.longitude_deg,
    )

    # E-05: 8 outer planets/asteroids (Chiron, Ceres, Pallas, Juno, Vesta,
    # Uranus, Neptune, Pluto) + 2 numbered asteroids (Sedna, Eris — None when
    # optional ephemeris files are absent).  Stored outside `grahas`.
    outer_bodies = compute_outer_bodies(
        jd_ut,
        ayanamsha_deg=ayan_value_deg,
        geo_lat=inp.latitude_deg,
        geo_lon=inp.longitude_deg,
    )

    provenance = build_provenance(
        inputs=asdict(inp),
        engine_version=engine_version,
        ayanamsha_config_id=effective_ayanamsha,
        computed_at_iso=computed_at_iso,
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
    # Optional non-schema annotation — handy for the parity test invariants.
    # Stored under provenance (schema permits additionalProperties on objects
    # not in the explicit `required`/`properties` enumeration — but the
    # provenance schema is strict. Keep ayan info OUTSIDE provenance.)
    payload["ayanamsha"] = {
        "id": effective_ayanamsha,
        "value_deg": ayan_value_deg,
    }
    # E-03: True Node + Mean Node variants — outside the JSON-Schema envelope
    # so the `grahas` array remains exactly 9 entries.
    payload["node_variants"] = node_variants
    # E-04: Mean Lilith + True Lilith variants — outside the JSON-Schema envelope.
    payload["lilith_variants"] = lilith_variants
    # E-05: Outer planets + asteroids — outside the JSON-Schema envelope.
    # Sedna/Eris may be None when optional ephemeris files are absent.
    payload["outer_bodies"] = outer_bodies

    if validate:
        validate_chart_output(payload)

    return payload


__all__ = [
    "compute_chart",
    "compute_lilith_states",
    "compute_node_states",
    "compute_outer_bodies",
    "ENGINE_VERSION_DEFAULT",
    "AYANAMSHA_DEFAULT",
    "CHART_OUTPUT_SCHEMA",
    "AYANAMSHA_REGISTRY",
    "apply_ayanamsha",
    "ayanamsha_value_deg",
    "list_ayanamsha_ids",
]
