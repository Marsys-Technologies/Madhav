"""
serialize.py — JSON serialization for panchang_engine Panchang / PanchangaInstant.

panchang_to_dict(p: Panchang) -> dict
panchanga_instant_to_dict(r: PanchangaInstant) -> dict

Output shape matches PANCHANG_DAILY_v1_0.md §2 (the JSONB column shapes),
ensuring that 4C-2's cache writes/reads are byte-identical to engine-direct
compute output.

Field mapping rules:
  - datetime → ISO 8601 string with Z for UTC
  - Anga → {"id": int, "name": str, "end_utc": "...Z"}
  - Timing → {"label": str, "start_utc": "...Z", "end_utc": "...Z"}
  - PlanetState → flat dict with all fields
  - special_yogas → list[dict] — the detect_all_special_yogas output shape

Phase: 4C-3 / rich-output Task 10
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Panchang, PanchangaInstant, Anga, Timing, PlanetState


def _dt_to_iso(dt: datetime | None) -> str | None:
    """
    Convert a UTC datetime to an ISO 8601 string ending in 'Z'.
    Returns None if dt is None (moonrise/moonset can be None on some days).
    """
    if dt is None:
        return None
    # Ensure we treat the datetime as UTC
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _anga_to_dict(anga: "Anga") -> dict:
    """Serialize an Anga (tithi, nakshatra, yoga, karana, vara) to dict."""
    return {
        "id": anga.id,
        "name": anga.name,
        "end_utc": _dt_to_iso(anga.end_utc),
    }


def _timing_to_dict(timing: "Timing") -> dict:
    """Serialize a Timing (inauspicious/auspicious window) to dict."""
    return {
        "label": timing.label,
        "start_utc": _dt_to_iso(timing.start_utc),
        "end_utc": _dt_to_iso(timing.end_utc),
    }


def _planet_state_to_dict(ps: "PlanetState") -> dict:
    """Serialize a PlanetState to a flat dict matching the PANCHANG_DAILY planets JSONB shape."""
    return {
        "name": ps.name,
        "longitude_sidereal": ps.longitude_sidereal,
        "sign_id": ps.sign_id,
        "sign_name": ps.sign_name,
        "nakshatra_id": ps.nakshatra_id,
        "nakshatra_name": ps.nakshatra_name,
        "nakshatra_pada": ps.nakshatra_pada,
        "retrograde": ps.retrograde,
        "combust": ps.combust,
    }


def _serialize_choghadiya(choghadiya: dict) -> dict:
    """
    Serialize the choghadiya dict.
    choghadiya = {"day": [Timing...], "night": [Timing...]}
    Each list element may be a Timing dataclass or already a dict (defensive).
    """
    result = {}
    for period_key in ("day", "night"):
        entries = choghadiya.get(period_key, [])
        serialized = []
        for entry in entries:
            if hasattr(entry, "label"):
                serialized.append(_timing_to_dict(entry))
            else:
                # Already a dict — pass through with datetime coercion
                serialized.append({
                    k: (_dt_to_iso(v) if isinstance(v, datetime) else v)
                    for k, v in entry.items()
                })
        result[period_key] = serialized
    return result


def _serialize_special_yoga(yoga_dict: dict) -> dict:
    """
    Serialize one special yoga entry.
    Input shape from detect_all_special_yogas:
        {"yoga": str, "start_utc": datetime, "end_utc": datetime,
         "strength": str, "stars": int}  (stars may be absent in some entries)
    Output shape per PANCHANG_DAILY_v1_0.md §2:
        {"yoga": str, "start_utc": "...Z", "end_utc": "...Z", "strength": str, "stars": int}
    """
    out: dict = {}
    for k, v in yoga_dict.items():
        if isinstance(v, datetime):
            out[k] = _dt_to_iso(v)
        else:
            out[k] = v
    return out


def panchang_to_dict(p: "Panchang") -> dict:
    """
    Serialize a Panchang dataclass to a JSON-serializable dict.
    Output matches PANCHANG_DAILY_v1_0.md §2 JSONB column shapes.

    All datetimes become ISO 8601 strings ending in Z (UTC).
    All nested dataclasses (Anga, Timing, PlanetState) are serialized recursively.
    The dict is JSON-serializable — no datetime / dataclass leaks.
    """
    # Planets: list[PlanetState] → keyed by planet name (lowercase) for JSONB shape
    # PANCHANG_DAILY §5 shows: {sun: {...}, moon: {...}, ...}
    planets_dict = {}
    for ps in p.planets:
        key = ps.name.lower()
        planets_dict[key] = _planet_state_to_dict(ps)

    # Inauspicious: list[Timing] → list of dicts
    inauspicious = [_timing_to_dict(t) for t in p.inauspicious]

    # Auspicious: list[Timing] → list of dicts
    auspicious = [_timing_to_dict(t) for t in p.auspicious]

    # Hora: list[Timing] → list of dicts
    hora = [_timing_to_dict(t) for t in p.hora]

    # Special yogas: list[dict] → serialize datetime values inside each dict
    special_yogas = [_serialize_special_yoga(y) for y in p.special_yogas]

    return {
        # Identity
        "date": p.date.isoformat(),
        "lat": p.lat,
        "lon": p.lon,
        "tz_offset_minutes": p.tz_offset_minutes,
        # Sun / Moon timings
        "sunrise_utc": _dt_to_iso(p.sunrise_utc),
        "sunset_utc": _dt_to_iso(p.sunset_utc),
        "moonrise_utc": _dt_to_iso(p.moonrise_utc),
        "moonset_utc": _dt_to_iso(p.moonset_utc),
        # 5 angas
        "tithi": _anga_to_dict(p.tithi),
        "nakshatra": _anga_to_dict(p.nakshatra),
        "yoga": _anga_to_dict(p.yoga),
        "karana_first": _anga_to_dict(p.karana_first),
        "karana_second": _anga_to_dict(p.karana_second),
        "vara": _anga_to_dict(p.vara),
        "paksha": p.paksha,
        # Timings
        "inauspicious": inauspicious,
        "auspicious": auspicious,
        "choghadiya": _serialize_choghadiya(p.choghadiya),
        "hora": hora,
        # Special yogas
        "special_yogas": special_yogas,
        # Planetary positions at sunrise
        "planets": planets_dict,
        # Audit
        "computation_version": p.computation_version,
        "ephemeris_version": p.ephemeris_version,
    }


# ---------------------------------------------------------------------------
# Rich sub-type serializers for PanchangaInstant
# ---------------------------------------------------------------------------

def _anga_attrs_to_dict(a) -> dict | None:
    """Serialize AngaAttributes (lord, deity, anga_type, pct_elapsed)."""
    if a is None:
        return None
    return {
        "lord": a.lord,
        "deity": a.deity,
        "anga_type": a.anga_type,
        "pct_elapsed": a.pct_elapsed,
    }


def _lagna_to_dict(lg) -> dict | None:
    """Serialize LagnaState to dict."""
    if lg is None:
        return None
    return {
        "ascendant_deg": lg.ascendant_deg,
        "ascendant_sign_id": lg.ascendant_sign_id,
        "ascendant_sign_name": lg.ascendant_sign_name,
        "ascendant_nak_id": lg.ascendant_nak_id,
        "ascendant_nak_name": lg.ascendant_nak_name,
        "ascendant_pada": lg.ascendant_pada,
        "mc_deg": lg.mc_deg,
        "mc_sign_id": lg.mc_sign_id,
        "mc_sign_name": lg.mc_sign_name,
        "house_cusps": list(lg.house_cusps) if lg.house_cusps is not None else None,
        "house_system": lg.house_system,
    }


def _sun_moon_dynamics_to_dict(s) -> dict | None:
    """Serialize SunMoonDynamics to dict."""
    if s is None:
        return None
    return {
        "sun_moon_separation_deg": s.sun_moon_separation_deg,
        "moon_illumination_pct": s.moon_illumination_pct,
        "moon_phase_angle_deg": s.moon_phase_angle_deg,
    }


def _vasa_to_dict(v) -> dict | None:
    """Serialize VasaFamily to dict."""
    if v is None:
        return None
    return {
        "agni_vasa": v.agni_vasa,
        "chandra_vasa": v.chandra_vasa,
        "rahu_vasa": v.rahu_vasa,
        "disha_vasa": v.disha_vasa,
        "nakshatra_vasa": v.nakshatra_vasa,
        "bhadra_vasa": v.bhadra_vasa,
    }


def _panchaka_to_dict(p) -> dict | None:
    """Serialize PanchakaState to dict."""
    if p is None:
        return None
    return {
        "active": p.active,
        "panchaka_type": p.panchaka_type,
    }


def _anandadi_to_dict(a) -> dict | None:
    """Serialize AnandadiYoga to dict."""
    if a is None:
        return None
    return {
        "yoga_name": a.yoga_name,
        "yoga_number": a.yoga_number,
        "auspicious": a.auspicious,
    }


def _calendrical_to_dict(c) -> dict | None:
    """Serialize Calendrical to dict."""
    if c is None:
        return None
    return {
        "masa_purnimanta": c.masa_purnimanta,
        "masa_amanta": c.masa_amanta,
        "is_adhika_masa": c.is_adhika_masa,
        "is_kshaya_masa": c.is_kshaya_masa,
        "ritu": c.ritu,
        "ayana": c.ayana,
        "vikram_samvat": c.vikram_samvat,
        "shaka_samvat": c.shaka_samvat,
        "kali_samvat": c.kali_samvat,
        "saptarshi_samvat": c.saptarshi_samvat,
        "jovian_year_name": c.jovian_year_name,
        "jovian_year_number": c.jovian_year_number,
        "sankranti_name": c.sankranti_name,
        "solar_arc_deg": c.solar_arc_deg,
    }


def _shoonya_to_dict(s) -> dict | None:
    """Serialize ShoonyaState to dict."""
    if s is None:
        return None
    return {
        "tithi_shoonya_sign_id": s.tithi_shoonya_sign_id,
        "tithi_shoonya_sign_name": s.tithi_shoonya_sign_name,
        "nakshatra_shoonya_sign_id": s.nakshatra_shoonya_sign_id,
        "nakshatra_shoonya_sign_name": s.nakshatra_shoonya_sign_name,
    }


def _tara_bala_to_dict(t) -> dict | None:
    """Serialize TaraBala to dict."""
    if t is None:
        return None
    return {
        "tara_count": t.tara_count,
        "tara_name": t.tara_name,
        "tara_quality": t.tara_quality,
        "chandra_bala": t.chandra_bala,
        "chandra_bala_quality": t.chandra_bala_quality,
    }


def _window_membership_to_dict(w) -> dict | None:
    """Serialize WindowMembership to dict."""
    if w is None:
        return None
    return {
        "inauspicious_active": list(w.inauspicious_active) if w.inauspicious_active is not None else [],
        "auspicious_active": list(w.auspicious_active) if w.auspicious_active is not None else [],
        "choghadiya_slot": w.choghadiya_slot,
        "hora_planet": w.hora_planet,
        "seconds_to_next_inauspicious": w.seconds_to_next_inauspicious,
        "seconds_to_next_auspicious": w.seconds_to_next_auspicious,
        "seconds_to_next_choghadiya": w.seconds_to_next_choghadiya,
        "seconds_to_next_hora": w.seconds_to_next_hora,
    }


def _micro_timing_to_dict(m) -> dict | None:
    """Serialize MicroTiming to dict."""
    if m is None:
        return None
    return {
        "ghati_from_sunrise": m.ghati_from_sunrise,
        "vighati_from_sunrise": m.vighati_from_sunrise,
        "muhurta_of_day": m.muhurta_of_day,
        "pranapada_sign_id": m.pranapada_sign_id,
        "pranapada_sign_name": m.pranapada_sign_name,
    }


def _serialize_timing_list(timings) -> list:
    """
    Serialize a list of Timing dataclasses to a list of dicts with ISO datetime strings.
    Defensively handles both Timing dataclasses and pre-serialized dicts.
    """
    if not timings:
        return []
    result = []
    for t in timings:
        if hasattr(t, "label"):
            # Timing dataclass
            result.append(_timing_to_dict(t))
        else:
            # Already a dict — coerce any datetime values
            result.append({
                k: (_dt_to_iso(v) if isinstance(v, datetime) else v)
                for k, v in t.items()
            })
    return result


def _anga_with_start_to_dict(anga) -> dict | None:
    """Serialize an Anga to dict. Returns None if anga is None."""
    if anga is None:
        return None
    return {
        "id": anga.id,
        "name": anga.name,
        "end_utc": _dt_to_iso(anga.end_utc),
    }


def panchanga_instant_to_dict(r: "PanchangaInstant") -> dict:
    """
    Serialize a PanchangaInstant dataclass to a JSON-serializable dict.

    All datetimes become ISO 8601 strings. All nested dataclasses are
    expanded to plain dicts. The result passes json.dumps() without error.
    """
    def _planet(p):
        if p is None:
            return None
        return _planet_state_to_dict(p)

    return {
        # Identity
        "instant_utc": _dt_to_iso(r.instant_utc),
        "lat": r.lat,
        "lon": r.lon,
        "tz_offset_minutes": r.tz_offset_minutes,
        # Core angas
        "tithi": _anga_with_start_to_dict(r.tithi),
        "nakshatra": _anga_with_start_to_dict(r.nakshatra),
        "yoga": _anga_with_start_to_dict(r.yoga),
        "karana": _anga_with_start_to_dict(r.karana),
        "karana_next": _anga_with_start_to_dict(r.karana_next),
        "vara": _anga_with_start_to_dict(r.vara),
        "paksha": r.paksha,
        # Planets (list, preserving order)
        "planets": [_planet(p) for p in r.planets] if r.planets else [],
        # Metadata
        "computation_version": r.computation_version,
        "ephemeris_version": r.ephemeris_version,
        "topics_computed": list(r.topics_computed) if r.topics_computed else [],
        # Anga attribute enrichments
        "tithi_attrs": _anga_attrs_to_dict(r.tithi_attrs),
        "nakshatra_attrs": _anga_attrs_to_dict(r.nakshatra_attrs),
        "yoga_attrs": _anga_attrs_to_dict(r.yoga_attrs),
        "karana_attrs": _anga_attrs_to_dict(r.karana_attrs),
        "vara_attrs": _anga_attrs_to_dict(r.vara_attrs),
        # Upagrahas and outer planets
        "upagrahas": [_planet(p) for p in r.upagrahas] if r.upagrahas else [],
        "outer_planets": [_planet(p) for p in r.outer_planets] if r.outer_planets else [],
        # Sun/Moon dynamics
        "sun_moon": _sun_moon_dynamics_to_dict(r.sun_moon),
        # Timing windows (list[Timing] → list[dict])
        "inauspicious_full": _serialize_timing_list(r.inauspicious_full),
        "auspicious_full": _serialize_timing_list(r.auspicious_full),
        # Special yogas (list[dict] with datetimes)
        "special_yogas_instant": [_serialize_special_yoga(y) for y in r.special_yogas_instant]
            if r.special_yogas_instant else [],
        # Panchang-quality sub-types
        "anandadi_yoga": _anandadi_to_dict(r.anandadi_yoga),
        "vasa": _vasa_to_dict(r.vasa),
        "panchaka": _panchaka_to_dict(r.panchaka),
        # Homa windows (list[Timing])
        "homa_windows": _serialize_timing_list(r.homa_windows),
        # Calendrical and shoonya
        "calendrical": _calendrical_to_dict(r.calendrical),
        "shoonya": _shoonya_to_dict(r.shoonya),
        # Tara Bala
        "tara_bala": _tara_bala_to_dict(r.tara_bala),
        # Lagna
        "lagna": _lagna_to_dict(r.lagna),
        # Window membership and micro-timing
        "window_membership": _window_membership_to_dict(r.window_membership),
        "micro_timing": _micro_timing_to_dict(r.micro_timing),
    }
