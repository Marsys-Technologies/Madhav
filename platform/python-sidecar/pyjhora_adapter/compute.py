"""
compute.py — PyJHora-backed natal chart computation.

Implements compute_chart(). Returns a dict matching
the existing chart_output structure so every downstream writer + the L2.5
builder work unchanged.

JD convention: PyJHora's drik/charts/dasha functions consume a Julian Day built
from LOCAL wall-clock time via utils.julian_day_number(date, time); the Place's
timezone drives the internal UT conversion. We therefore pass local wall-clock
(not UTC) — this matches PyJHora's whole calculation stack and reproduces the
native chart (Lagna Aries, Moon in Purva Bhadrapada) for 1984-02-05 10:43 IST.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import dignities, houses, panchanga, positions, sensitive_points, vargas
from . import dashas as _dashas
from ._ayanamsha import resolve_mode
from ._jhora import drik, utils
from .reconciliation import reconcile
from .version import ENGINE_VERSION


def _parse_local_wallclock(datetime_iso: str) -> datetime:
    dt = datetime.fromisoformat(datetime_iso)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


def compute_chart(
    inputs: dict[str, Any],
    engine_version: str = ENGINE_VERSION,
    ayanamsha_id: str | None = None,
    *,
    ayanamsha_config: str | None = None,  # deprecated alias kept for old callers
    validate: bool = True,  # accepted for signature parity; no-op (no JSON schema)
    computed_at_iso: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Compute a natal chart with PyJHora and return a chart_output dict."""
    eff_ayan = (
        ayanamsha_id if ayanamsha_id is not None
        else ayanamsha_config if ayanamsha_config is not None
        else "lahiri"
    )
    mode_str, sidm_int = resolve_mode(eff_ayan)

    lat = float(inputs["latitude_deg"])
    lon = float(inputs["longitude_deg"])
    tz = float(inputs["tz_offset_hours"])
    place_name = str(inputs.get("place_name", ""))
    subject_label = str(inputs.get("subject_label", ""))
    dt_iso = str(inputs["datetime_iso"])

    local_dt = _parse_local_wallclock(dt_iso)
    dob = drik.Date(local_dt.year, local_dt.month, local_dt.day)
    tob = (local_dt.hour, local_dt.minute, local_dt.second)
    jd_ut = utils.julian_day_number(dob, tob)

    # Pin sidereal mode once for this process, then read ayanamsa value.
    drik.set_ayanamsa_mode(mode_str)
    ayan_value_deg = float(drik.get_ayanamsa_value(jd_ut))

    kw = dict(lat=lat, lon=lon, tz=tz)

    grahas = dignities.refine(positions.compute_positions(jd_ut, eff_ayan, **kw))
    ascendant = houses.compute_ascendant(jd_ut, eff_ayan, **kw)
    house_list = houses.compute_houses(ascendant)

    # Assign whole-sign house to each graha.
    asc_sign0 = int(ascendant["sign_id"]) - 1
    for g in grahas:
        planet_sign0 = int(g["sign_id"]) - 1
        g["house"] = ((planet_sign0 - asc_sign0) % 12) + 1
    varga_map = vargas.compute_vargas(jd_ut, eff_ayan, **kw)
    dasha_map = _dashas.compute_dashas(jd_ut, eff_ayan, **kw)
    panch = panchanga.compute_panchanga(jd_ut, eff_ayan, **kw)
    sens = sensitive_points.compute_sensitive_points(jd_ut, eff_ayan, **kw)
    recon = reconcile(ascendant, house_list, grahas)

    cai = computed_at_iso or datetime.now(timezone.utc).isoformat()

    inputs_clean = {
        "datetime_iso": dt_iso,
        "tz_offset_hours": tz,
        "latitude_deg": lat,
        "longitude_deg": lon,
        "place_name": place_name,
        "subject_label": subject_label,
    }

    provenance = {
        "engine_version": engine_version,
        "ayanamsha_config_id": eff_ayan,
        "ayanamsha_mode": mode_str,
        "computed_at_iso": cai,
        "jd_ut": jd_ut,
    }

    payload: dict[str, Any] = {
        "provenance": provenance,
        "inputs": inputs_clean,
        "birth_datetime": dt_iso,  # alias for defensive writers
        "ascendant": ascendant,
        "lagna": ascendant,        # alias for dashas_writer
        "houses": house_list,
        "grahas": grahas,
        # 'planets' alias: id=lowercase name, sign_num=0-based sign index.
        # Required by t1_structural_writer, sade_sati_writer.
        "planets": [
            {**g, "id": g["name"].lower(), "sign_num": int(g["sign_id"]) - 1}
            for g in grahas
        ],
        "vargas": varga_map,
        "dashas": dasha_map,
        "panchanga": panch,
        "sensitive_points": sens,
        "ayanamsha": {
            "id": eff_ayan,
            "value_deg": ayan_value_deg,
            "mode": mode_str,
            "sidm": sidm_int,
        },
        "reconciliation": recon,
    }
    return payload
