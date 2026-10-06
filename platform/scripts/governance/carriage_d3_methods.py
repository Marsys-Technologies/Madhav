"""carriage_d3_methods.py: the reviewed re-derivation methods of the Carr.D3 engine (carriage_d3.py). Loaded by `carriage_d3.load_methods()`; it imports no sibling module:
`register_all(d3)` registers each method into the engine's closed METHODS registry.

Every method here is an INDEPENDENT ROUTE to the same value: it calls the Swiss Ephemeris library directly with its own constants and arithmetic, and it never imports the
writer's code or the adapter's maps (sharing them would share their defects: the Track A1 `krishnamurti`-resolves-to-Lahiri class). What it shares with the writers is the
ephemeris DATA behind the library (the record names the backend). Adding a method is a reviewed edit of this file (a new PR with its own pin), never a declaration.

METHODS
  swisseph_sidereal_positions_v1   chart_facts, the graha_position / graha_sign_attributes family (ga_positions): longitude, degree in sign, sign, nakshatra, pada, whole-sign
                                   house, retrograde flag, for the nine grahas and the Lagna, per ayanamsha. Inputs: the chart's birth parameters (public.charts).
  swisseph_ingress_root_find_v1    bg_sky_calendar, the `ingress` family: the instant a body crosses a sign edge, re-found by an Illinois root-finder over a +-0.2 day bracket (the
                                   writer scans with a 0.5/1.0 day step and 20 bisections), the longitude at the stored instant, the sign entered, the ayanamsha label.

CONVENTIONS are part of every claim and are DECLARED by the spec (the engine refuses a spec that omits one): `position_model` (true_geometric = SEFLG_TRUEPOS, the convention PyJHora's
`drik` uses, jhora/panchanga/drik.py:124; apparent = no flag), `node_model`, `house_rule`, `ayanamsha`. The first clean run of the prototype differed from the writer by 7 to 43
arcsec per planet until `true_geometric` was declared: the convention is a fact the strategist reviews, not a tuning knob.
"""
from __future__ import annotations

import json
import math
import pathlib
import re
from datetime import datetime

BACKENDS = ("swieph", "moseph")
_SIDM_BY_CANONICAL = {   # by swisseph constant NAME, independent of the adapter's map
    "lahiri_chitrapaksha": "SIDM_LAHIRI", "true_chitra": "SIDM_TRUE_CITRA", "krishnamurti": "SIDM_KRISHNAMURTI", "raman": "SIDM_RAMAN",
    "surya_siddhanta_classical": "SIDM_SURYASIDDHANTA", "lahiri": "SIDM_LAHIRI",
}
_BODY = {"SUN": "SUN", "MOON": "MOON", "MAR": "MARS", "MER": "MERCURY", "JUP": "JUPITER", "VEN": "VENUS", "SAT": "SATURN", "RAH_MEAN": "MEAN_NODE", "KET_MEAN": "MEAN_NODE"}
_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_ING_BODY = {"Sun": "SUN", "Moon": "MOON", "Mars": "MARS", "Mercury": "MERCURY", "Jupiter": "JUPITER", "Venus": "VENUS", "Saturn": "SATURN", "Rahu": "TRUE_NODE", "Ketu": "TRUE_NODE"}


def _swe():
    import swisseph as swe
    return swe


_NAKSHATRA_ORDER = ("ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha", "magha", "purvaphalguni", "uttaraphalguni", "hasta",
                    "chitra", "swati", "vishakha", "anuradha", "jyeshtha", "mula", "purvaashadha", "uttaraashadha", "shravana", "dhanishta", "shatabhisha", "purvabhadrapada",
                    "uttarabhadrapada", "revati")
_NAK_ALIASES = {"moola": "mula", "mrigasira": "mrigashira", "dhanishtha": "dhanishta", "ashvini": "ashwini", "aslesha": "ashlesha", "jyestha": "jyeshtha", "visakha": "vishakha"}


def nakshatra_number(name):
    """The 1-based index of a stored nakshatra name in the classical order of the 27, or None. Names are compared after case and separators are folded (letters only) and a small
    fixed table of spelling variants is applied (Moola = Mula, Mrigasira = Mrigashira, ...): the schema copies in this repository spell the 27 names two different ways, and a
    position claim is about WHICH nakshatra, not its spelling. A name outside the list is None (a mismatch, never a skip)."""
    if not isinstance(name, str):
        return None
    k = re.sub(r"[^a-z]", "", name.lower())
    k = _NAK_ALIASES.get(k, k)
    return _NAKSHATRA_ORDER.index(k) + 1 if k in _NAKSHATRA_ORDER else None


def backend_probe() -> dict:
    """The reference leg's ephemeris identity, read from the library's returned FLAG (never the value): the Sun needs the planet file, the true node the Moon file; both must report
    SWIEPH for `swieph`, either reporting MOSEPH reads `moseph`. pyswisseph never fails when the files are missing: it substitutes Moshier and says so only in the flag."""
    swe = _swe()
    flags = []
    for body in (swe.SUN, swe.TRUE_NODE):
        _res, rf = swe.calc_ut(2451545.0, body, swe.FLG_SWIEPH)
        flags.append(rf)
    if all(f & swe.FLG_SWIEPH for f in flags):
        name = "swieph"
    elif any(f & swe.FLG_MOSEPH for f in flags):
        name = "moseph"
    else:
        name = "other"
    return {"name": name, "swisseph_version": getattr(swe, "version", None)}


# ───────────────────────── method 1: graha positions (chart_facts family) ─────────────────────────
# Covers EVERY row ga_positions owns (its count_sql: graha_position, graha_sign_attributes, bhava_cusps, house_chalit, sandhi_flag): longitude, degree in sign, sign number and
# name, sign lord, nakshatra and its lord, pada, whole-sign house, retrograde flag, combustion state; the twelve Sripati and Placidus bhava cusps (start / madhya / end);
# the Sripati chalit house, arcs to the madhya and the nearest boundary, the nearest boundary, the sandhi flag and its reasons. The fixed classical tables below (sign lords,
# the Vimshottari nakshatra-lord cycle, the combustion orbs) are declared conventions, written here independently of the adapter's tables.

_SIGN_LORD = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
_NAK_LORD_CYCLE = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
_COMBUST_ORB = {"MOON": 12.0, "MAR": 17.0, "MER": 14.0, "JUP": 11.0, "VEN": 10.0, "SAT": 15.0}
_SANDHI_ORB = 3.0
_GRAHAS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
_NUM_KEYS = {"longitude_sidereal": "longitude_sidereal", "degree_in_sign": "degree_in_sign", "sign_num": "sign_num", "pada": "pada", "house_d1": "house_d1",
             "chalit_house_sripati": "chalit_house", "whole_sign_house": "whole_sign_house", "dist_to_madhya_deg": "dist_to_madhya_deg",
             "dist_to_nearest_boundary_deg": "dist_to_nearest_boundary_deg"}
_INT_COLS = ("sign_num", "pada", "house_d1", "chalit_house", "whole_sign_house")
_TEXT_KEYS = {"sign": "sign", "sign_lord": "sign_lord", "nakshatra_lord": "nakshatra_lord", "retrograde_flag": "retrograde_flag", "combustion_state": "combustion_state",
              "nearest_boundary": "nearest_boundary", "sandhi_flag": "sandhi_flag", "sandhi_reasons": "sandhi_reasons"}
_CUSP_KEYS = {f"{sy}_{e}": f"{sy}_{e}" for sy in ("sripati", "placidus") for e in ("start", "madhya", "end")}
POSITION_COLUMNS = ("longitude_sidereal", "degree_in_sign", "sign_num", "sign", "sign_lord", "nakshatra_num", "nakshatra_lord", "pada", "house_d1", "retrograde_flag", "combustion_state",
                    "chalit_house", "whole_sign_house", "dist_to_madhya_deg", "dist_to_nearest_boundary_deg", "nearest_boundary", "sandhi_flag", "sandhi_reasons") + tuple(_CUSP_KEYS)
_POS_CATEGORIES = ("graha_position", "graha_sign_attributes", "bhava_cusps", "house_chalit", "sandhi_flag")


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _int(v):
    return int(round(v)) if isinstance(v, (int, float)) and not isinstance(v, bool) and float(v).is_integer() else None


def positions_logical_rows(rows, inputs):
    """One logical row per (fact_subject, ayanamsha_id): the EAV rows of the declared read folded into logical columns (every column of POSITION_COLUMNS, None where the writer
    stored nothing). A key the writer did not write for a subject stays None: the method derives None for it, so only a claimed fact is compared, and a claimed fact that is
    missing where the method derives a value is a mismatch. A row of a category or key outside the known set is a mismatch-by-construction (the logical row carries `unknown_keys`)."""
    by = {}
    for r in rows:
        subj, ay, key, cat = r["fact_subject"], r["ayanamsha_id"], r["fact_key"], r.get("fact_category")
        d = by.setdefault((subj, ay), dict(subject=subj, ayanamsha=ay, unknown_keys=[]))
        if cat == "bhava_cusps" and key in _CUSP_KEYS:
            d[_CUSP_KEYS[key]] = _num(r.get("fact_value_num"))
        elif key in _NUM_KEYS:
            c = _NUM_KEYS[key]
            d[c] = _int(r.get("fact_value_num")) if c in _INT_COLS else _num(r.get("fact_value_num"))
        elif key in _TEXT_KEYS:
            d[_TEXT_KEYS[key]] = r.get("fact_value_text")
        elif key == "nakshatra":
            d["nakshatra_num"] = nakshatra_number(r.get("fact_value_text"))
        else:
            d["unknown_keys"].append(f"{cat}.{key}")
    out = []
    for d in by.values():
        for c in POSITION_COLUMNS:
            d.setdefault(c, None)
        out.append(d)
    return sorted(out, key=lambda d: (d["ayanamsha"], d["subject"]))


def _birth_instant(row: dict):
    """(jd_ut, lat, lon) from one public.charts row, by the library's own Julian-day function and the stdlib time zone database (not the writer's conversion)."""
    from zoneinfo import ZoneInfo
    swe = _swe()
    d = str(row["birth_date"])[:10]
    t = str(row["birth_time"])[:8]
    t = t if len(t) == 8 else t + ":00"
    naive = datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M:%S")
    off = ZoneInfo(str(row["timezone_id"])).utcoffset(naive)
    if off is None:
        raise ValueError("the time zone has no offset at the birth instant")
    hours = naive.hour + naive.minute / 60 + naive.second / 3600 - off.total_seconds() / 3600
    return swe.julday(naive.year, naive.month, naive.day, hours), float(row["birth_lat"]), float(row["birth_lng"])


def positions_context(rows, inputs, spec):
    if not (isinstance(inputs, list) and len(inputs) == 1):
        raise ValueError("exactly one public.charts row is required for the birth parameters")
    jd, lat, lon = _birth_instant(inputs[0])
    pm = spec["conventions"]["position_model"]["value"]
    swe = _swe()
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED | (swe.FLG_TRUEPOS if pm == "true_geometric" else 0)
    return dict(jd=jd, lat=lat, lon=lon, flags=flags, cache={})


def _fwd(a, b):
    return (b - a) % 360.0


def _mid(a, b):
    return (a + _fwd(a, b) / 2.0) % 360.0


def _sep(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _bhavas(ctx, ay):
    """(placidus cusps[12], sripati madhyas[12], sripati sandhis[12]) for the birth instant and ayanamsha: Placidus cusps from houses_ex; Sripati madhyas by trisecting each
    quadrant arc between the angles (cusp 1 to 4, 4 to 7, 7 to 10, 10 to 1); sandhi h = midpoint of madhya h and h + 1 (house h spans sandhi h - 1 to sandhi h)."""
    k = ("bhava", ay)
    if k not in ctx["cache"]:
        swe = _swe()
        plac = [c % 360.0 for c in swe.houses_ex(ctx["jd"], ctx["lat"], ctx["lon"], b"P", swe.FLG_SIDEREAL)[0][:12]]       # the declared bhava_flags convention: sidereal only (no true-position flag)
        mad = list(plac)
        for a, b in ((0, 3), (3, 6), (6, 9), (9, 0)):
            step = _fwd(plac[a], plac[b]) / 3.0
            mad[(a + 1) % 12] = (plac[a] + step) % 360.0
            mad[(b - 1) % 12] = (plac[b] - step) % 360.0
        sand = [_mid(mad[h], mad[(h + 1) % 12]) for h in range(12)]
        ctx["cache"][k] = (plac, mad, sand)
    return ctx["cache"][k]


def positions_ref(r, ctx):
    swe = _swe()
    ay, subj = r["ayanamsha"], r["subject"]
    name = _SIDM_BY_CANONICAL.get(ay)
    if name is None:
        raise ValueError(f"unknown ayanamsha id {ay!r}")
    if r.get("unknown_keys"):
        raise ValueError(f"keys the method does not know: {r['unknown_keys']}")
    swe.set_sid_mode(getattr(swe, name))
    ref = {c: None for c in POSITION_COLUMNS}
    plac, mad, sand = _bhavas(ctx, ay)
    if subj.startswith("BHAVA_"):
        h = int(subj[6:]) - 1
        if not 0 <= h < 12:
            raise ValueError("bhava number out of range")
        ref.update(sripati_start=sand[(h - 1) % 12], sripati_madhya=mad[h], sripati_end=sand[h],
                   placidus_start=plac[h], placidus_madhya=_mid(plac[h], plac[(h + 1) % 12]), placidus_end=plac[(h + 1) % 12])
        return ref
    if subj == "LAGNA":
        lon, speed = swe.houses_ex(ctx["jd"], ctx["lat"], ctx["lon"], b"W", ctx["flags"] & ~swe.FLG_SPEED)[1][0] % 360.0, None
    elif subj in _BODY:
        res, _rf = swe.calc_ut(ctx["jd"], getattr(swe, _BODY[subj]), ctx["flags"])
        lon, speed = res[0] % 360.0, res[3]
        if subj == "KET_MEAN":
            lon = (lon + 180.0) % 360.0
    else:
        raise ValueError(f"unknown subject {subj!r}")
    sign_idx = int(lon // 30.0)
    asc_sign = int(swe.houses_ex(ctx["jd"], ctx["lat"], ctx["lon"], b"W", ctx["flags"] & ~swe.FLG_SPEED)[1][0] % 360.0 // 30.0)
    ref.update(longitude_sidereal=lon, degree_in_sign=lon % 30.0, sign_num=sign_idx + 1, sign=_SIGNS[sign_idx], sign_lord=_SIGN_LORD[sign_idx],
               pada=int((lon % (360.0 / 27)) // (360.0 / 108)) + 1, house_d1=((sign_idx - asc_sign) % 12) + 1)
    if subj == "LAGNA":
        return ref
    nak = int(lon // (360.0 / 27))
    sun = swe.calc_ut(ctx["jd"], swe.SUN, ctx["flags"])[0][0] % 360.0
    ref.update(nakshatra_num=nak + 1, nakshatra_lord=_NAK_LORD_CYCLE[nak % 9], retrograde_flag="retrograde" if speed < 0 else "direct",
               combustion_state="combust" if subj in _COMBUST_ORB and _sep(lon, sun) <= _COMBUST_ORB[subj] else "none")
    h = next((i for i in range(12) if _fwd(sand[(i - 1) % 12], lon) < _fwd(sand[(i - 1) % 12], sand[i])), 0)
    ds, de = _sep(lon, sand[(h - 1) % 12]), _sep(lon, sand[h])
    near, dist = ("start", ds) if ds <= de else ("end", de)
    reasons = (["within_boundary_orb"] if dist <= _SANDHI_ORB else []) + (["wholesign_chalit_divergence"] if ref["house_d1"] != h + 1 else [])
    ref.update(chalit_house=h + 1, whole_sign_house=ref["house_d1"], dist_to_madhya_deg=_sep(lon, mad[h]), dist_to_nearest_boundary_deg=dist, nearest_boundary=near,
               sandhi_flag=str(bool(reasons)).lower(), sandhi_reasons=",".join(reasons) or "none")
    return ref


# ───────────────────────── method 2: the sky calendar (bg_sky_calendar), every event family ─────────────────────────
# Covers EVERY row the table holds: ingresses, stations, double-transit minima, solar and lunar eclipses. Per stored event the method re-derives, by its own code on pyswisseph:
#   ingress          the body's distance from the nearest sign edge at the stored instant (the row claims 0), a crossing of that edge within +-0.2 day (Illinois root-finder), the longitude,
#                    speed, sign entered and nakshatra at the stored instant
#   station          the speed at the stored instant (claims 0), a zero of the speed within +-0.5 day, the station type from the speed before, longitude, sign, nakshatra
#   double transit  the minimum separation of the pair within +-2 days (golden section), the separation at the stored instant, the stored orb and the second body's longitude
#   eclipse          greatest-eclipse instant by minimising the shadow-axis distance (solar: fundamental-plane gamma; lunar: Moon-to-anti-Sun angle) with the swecl.c radii, the type
#                    (solar total / annular / annular_total / partial, lunar total / partial / penumbral) from the shadow geometry, the begin and end contacts, the longitude and speed
# and COMPLETENESS independently of the writer: per body the sign entries counted by a 0.25 day scan (Moon) or 1 day scan, the station and minimum counts, and every new and full
# moon tested against the eclipse condition, over [history_start, the latest stored event of the family]; the declared per-family counts must equal the stored ones, so a dropped
# or invented event is a named discrepancy. (expected_rows is therefore "method": a rolling horizon is the table's nature.)

_AU_KM = 149597870.7
_RS, _RM, _RE = 696000.0, 1738.15, 6378.137          # swecl.c DSUN / 2, DMOON / 2, DEARTH / 2 (km)
_ECL_ENL = 1.0 / 0.99                                   # the lunar umbra / penumbra enlargement swecl.c applies (measured: 1.0 mismatches 12 of 311, 1/0.99 mismatches 2 boundary cases)
SKY_COLUMNS = ("event_datetime_s", "target_sign", "sign", "nakshatra_num", "longitude_deg", "speed_dps", "ayanamsha_key", "edge_distance_deg", "station_type", "station_zero_speed", "conj_orb_deg", "conj_offset_deg",
               "planet_b_lon", "eclipse_type", "is_central", "ecl_time_offset_s", "begin_offset_s", "end_offset_s")
_STATION_BODIES = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _illinois(f, a, b, tol=1e-9, maxit=100):
    """Root of f in [a, b] by the Illinois variant of regula falsi; None when f does not change sign over the bracket."""
    fa, fb = f(a), f(b)
    if fa == 0:
        return a
    if fb == 0:
        return b
    if fa * fb > 0:
        return None
    side, c = 0, a
    for _ in range(maxit):
        c = (a * fb - b * fa) / (fb - fa)
        fc = f(c)
        if abs(b - a) < tol or fc == 0:
            return c
        if fc * fb > 0:
            b, fb = c, fc
            if side == -1:
                fa /= 2
            side = -1
        else:
            a, fa = c, fc
            if side == 1:
                fb /= 2
            side = 1
    return c


def _detail(v):
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            return {}
    return v if isinstance(v, dict) else {}


def _epoch_s(v):
    """Seconds since 1970-01-01 of a naive-UTC datetime or its ISO text (the `event_datetime_utc` column as the census reads it: a jsonb string), else None."""
    from datetime import datetime as _dt
    if isinstance(v, str):
        try:
            v = _dt.fromisoformat(v.replace("Z", "").replace("T", " ").split("+")[0])
        except ValueError:
            return None
    if not isinstance(v, _dt):
        return None
    return (v - _dt(1970, 1, 1)).total_seconds()


def _jd_epoch_s(jd):
    """Seconds since 1970-01-01 of a Julian day (UT) by the library's own calendar conversion (swe.revjul), truncated to the second as the writer stores it."""
    from datetime import datetime as _dt, timedelta
    y, m, d, h = _swe().revjul(jd)
    return (_dt(int(y), int(m), int(d)) + timedelta(seconds=int(h * 3600.0)) - _dt(1970, 1, 1)).total_seconds()


def sky_logical_rows(rows, inputs):
    """One logical row per stored event. The claims a row makes about itself are stored as the value the re-derivation must reproduce: an ingress is ON a sign edge (distance 0), a
    station has speed 0, a double-transit row is at the minimum separation, an eclipse row is at its greatest-eclipse instant (offset 0) with its begin / end contacts (offset 0)."""
    out = []
    for r in rows:
        d = _detail(r.get("detail"))
        et = r["event_type"]
        row = dict(event_type=et, primary_body=r["primary_body"], secondary_body=r.get("secondary_body") or "", event_jd=_num(r["event_jd"]), sign=r.get("sign"),
                   event_datetime_s=_epoch_s(r.get("event_datetime_utc")), target_sign=(d.get("target_sign") if r["event_type"] == "ingress" else None),
                   nakshatra_num=nakshatra_number(r.get("nakshatra")) if r.get("nakshatra") else None, longitude_deg=_num(r.get("longitude_deg")), speed_dps=_num(r.get("speed_dps")),
                   ayanamsha_key=r.get("ayanamsha_key"), edge_distance_deg=None, station_type=None, station_zero_speed=None, conj_orb_deg=None, conj_offset_deg=None,
                   planet_b_lon=None, eclipse_type=None, is_central=None, ecl_time_offset_s=None, begin_offset_s=None, end_offset_s=None, _detail=d)
        if et == "ingress":
            row["edge_distance_deg"] = 0.0
        elif et == "station":
            row["station_type"], row["station_zero_speed"] = d.get("station_type"), 0.0
        elif et == "double_transit":
            row["conj_orb_deg"], row["conj_offset_deg"], row["planet_b_lon"] = _num(d.get("orb_deg")), 0.0, _num(d.get("planet_b_lon"))
        elif et in ("eclipse_solar", "eclipse_lunar"):
            row["eclipse_type"], row["ecl_time_offset_s"] = d.get("eclipse_type"), 0.0
            row["is_central"] = d.get("is_central") if et == "eclipse_solar" else None
            row["begin_offset_s"] = 0.0 if d.get("begin_jd") else None
            row["end_offset_s"] = 0.0 if d.get("end_jd") else None
        out.append(row)
    return out


def sky_context(rows, inputs, spec):
    swe = _swe()
    cv = spec["conventions"]
    return dict(flags=swe.FLG_SIDEREAL | swe.FLG_SPEED, ayanamsha=cv["ayanamsha"]["value"], history_start=cv["history_start"]["value"], rows=rows)


def _sid(ctx):
    swe = _swe()
    name = _SIDM_BY_CANONICAL.get(ctx["ayanamsha"])
    if name is None:
        raise ValueError(f"unknown ayanamsha {ctx['ayanamsha']!r}")
    swe.set_sid_mode(getattr(swe, name))


def _lon_speed(ctx, body, t):
    """(sidereal longitude, speed) of a stored-body name at JD t, apparent, true node for Rahu, Ketu = Rahu + 180."""
    swe = _swe()
    res = swe.calc_ut(t, getattr(swe, _ING_BODY[body]), ctx["flags"])[0]
    lon = (res[0] + 180.0) % 360.0 if body == "Ketu" else res[0] % 360.0
    return lon, res[3]


def _golden_min(f, a, b, it=70):
    g = (math.sqrt(5) - 1) / 2
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(it):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = f(d)
    return (a + b) / 2


def _vec(t, body):
    swe = _swe()
    r = swe.calc_ut(t, getattr(swe, body), swe.FLG_SWIEPH | swe.FLG_EQUATORIAL | swe.FLG_J2000 | swe.FLG_XYZ | swe.FLG_TRUEPOS)[0]
    return [r[0] * _AU_KM, r[1] * _AU_KM, r[2] * _AU_KM]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    return math.sqrt(_dot(a, a))


def _solar_geom(t):
    """(gamma, umbra radius u, penumbra radius l1, plane distance z, tan f2): Earth radii; the shadow axis runs Sun -> Moon, the fundamental plane passes through the Earth's centre."""
    S, M = _vec(t, "SUN"), _vec(t, "MOON")
    ax = [m - s for m, s in zip(M, S)]
    D = _norm(ax)
    a = [x / D for x in ax]
    z = _dot([-x for x in M], a)
    perp = [-M[k] - z * a[k] for k in range(3)]
    g = _norm(perp) / _RE
    sf2, sf1 = (_RS - _RM) / D, (_RS + _RM) / D
    c2, c1 = _RM / sf2, _RM / sf1
    tf2 = math.tan(math.asin(sf2))
    return g, (c2 - z) * tf2 / _RE, (c1 + z) * math.tan(math.asin(sf1)) / _RE, z, tf2


def _lunar_state(t):
    """(rho, moon semidiameter, umbra radius, penumbra radius), radians: rho = the Moon's angular distance from the anti-Sun point."""
    S, M = _vec(t, "SUN"), _vec(t, "MOON")
    dS, dM = _norm(S), _norm(M)
    rho = math.acos(max(-1.0, min(1.0, -_dot(S, M) / (dS * dM))))
    s, ps, pm, m = math.asin(_RS / dS), math.asin(_RE / dS), math.asin(_RE / dM), math.asin(_RM / dM)
    return rho, m, _ECL_ENL * (pm + ps - s), _ECL_ENL * (pm + ps + s)


def _bisect(f, a, b, it=60):
    fa = f(a)
    if fa * f(b) > 0:
        return None
    for _ in range(it):
        m = (a + b) / 2
        fm = f(m)
        if (fm > 0) == (fa > 0):
            a, fa = m, fm
        else:
            b = m
    return (a + b) / 2


_SOLAR_NEIGHBOURS = {"partial": ("total", "annular", "annular_total"), "total": ("partial", "annular_total"), "annular": ("partial", "annular_total"), "annular_total": ("total", "annular")}
_LUNAR_NEIGHBOURS = {"total": ("partial",), "partial": ("total", "penumbral"), "penumbral": ("partial",)}


def _solar_type(g, u, us, l1):
    """(type, ambiguity margin in Earth radii). Ambiguous = the type would flip within the margin of the classification boundaries."""
    if g >= 1 + l1:
        return None, float("inf")          # no eclipse: no classification boundary near, so nothing is ambiguous (N-156 review LOW-4)
    if g >= 1 + abs(u):
        return "partial", abs(g - (1 + abs(u)))
    if u > 0:
        return "total", abs(u)
    if us > 0 and g < 1 - abs(u):
        return "annular_total", abs(us)
    return "annular", min(abs(u), abs(us)) if us > 0 else abs(u)


def sky_ref(r, ctx):
    swe = _swe()
    _sid(ctx)
    ref = {c: None for c in SKY_COLUMNS}
    et, body, j = r["event_type"], r["primary_body"], r["event_jd"]
    if not isinstance(j, float):
        raise ValueError("event_jd is not a number")
    sd = lambda l, b: (l - b + 180.0) % 360.0 - 180.0
    ref["ayanamsha_key"] = ctx["ayanamsha"]
    ref["event_datetime_s"] = _jd_epoch_s(j)
    if et == "ingress":
        if body not in _ING_BODY or r["sign"] not in _SIGNS:
            raise ValueError("unknown body or sign")
        l, sp = _lon_speed(ctx, body, j)
        lo_edge = _SIGNS.index(r["sign"]) * 30.0
        up_edge = (lo_edge + 30.0) % 360.0
        edge = lo_edge if abs(sd(l, lo_edge)) <= abs(sd(l, up_edge)) else up_edge     # a retrograde re-entry crosses the sign's upper edge
        t = _illinois(lambda x: sd(_lon_speed(ctx, body, x)[0], edge), j - 0.2, j + 0.2)
        if t is None:
            raise ValueError("no crossing of the nearest sign edge within 0.2 day of the stored instant")
        ref.update(edge_distance_deg=abs(sd(l, edge)), longitude_deg=l, speed_dps=sp, sign=_SIGNS[int(_lon_speed(ctx, body, t + 0.001)[0] // 30.0) % 12],
                   nakshatra_num=int(l // (360.0 / 27)) + 1)
        ref["target_sign"] = ref["sign"]               # the writer stores the sign it searched for in detail.target_sign; it must equal the sign entered
    elif et == "station":
        if body not in _STATION_BODIES:
            raise ValueError("unknown station body")
        l, sp = _lon_speed(ctx, body, j)
        t = _illinois(lambda x: _lon_speed(ctx, body, x)[1], j - 0.5, j + 0.5)
        if t is None:
            raise ValueError("no zero of the speed within 0.5 day of the stored instant")
        before = _lon_speed(ctx, body, t - 0.5)[1]
        ref.update(station_zero_speed=abs(sp), longitude_deg=l, speed_dps=sp, sign=_SIGNS[int(l // 30.0) % 12], nakshatra_num=int(l // (360.0 / 27)) + 1,
                   station_type="retrograde" if before > 0 else "direct")
    elif et == "double_transit":
        other = r["secondary_body"]
        if body not in _ING_BODY or other not in _ING_BODY:
            raise ValueError("unknown body pair")
        sep = lambda x: abs(sd(_lon_speed(ctx, body, x)[0], _lon_speed(ctx, other, x)[0]))
        tmin = _golden_min(sep, j - 2.0, j + 2.0)
        l, sp = _lon_speed(ctx, body, j)
        lb = _lon_speed(ctx, other, j)[0]
        ref.update(conj_orb_deg=sep(tmin), conj_offset_deg=sep(j) - sep(tmin), planet_b_lon=lb, longitude_deg=l, speed_dps=sp, sign=_SIGNS[int(l // 30.0) % 12],
                   nakshatra_num=int(l // (360.0 / 27)) + 1)
    elif et == "eclipse_solar":
        tg = _golden_min(lambda x: _solar_geom(x)[0], j - 0.1, j + 0.1)
        g, u, l1, z, tf2 = _solar_geom(tg)
        us = u + math.sqrt(max(0.0, 1 - g * g)) * tf2
        ty, _m = _solar_type(g, u, us, l1)
        pen = lambda x: _solar_geom(x)[0] - (1 + _solar_geom(x)[2])
        b, e = _bisect(pen, tg - 0.3, tg), _bisect(pen, tg, tg + 0.3)
        sb, se = r["_detail"].get("begin_jd"), r["_detail"].get("end_jd")
        l, sp = _lon_speed(ctx, "Sun", j)
        if ty is not None and _m <= 1.5e-4:
            ref["_ambiguous"] = {"eclipse_type": {"note": f"within {_m:.6f} Earth radii of a solar type boundary", "neighbours": list(_SOLAR_NEIGHBOURS[ty])}}
        elif ty is None and abs(g - (1 + l1)) <= 1.5e-4:
            ref["_ambiguous"] = {"eclipse_type": {"note": "within 1.5e-4 Earth radii of the penumbral limit", "neighbours": ["partial"]}}
        if ty is not None and abs(g - (1 - abs(u))) <= 1.5e-4:
            ref.setdefault("_ambiguous", {})["is_central"] = {"note": "within 1.5e-4 Earth radii of the central limit", "neighbours": [not (g < 1 - abs(u) + 1e-9)]}
        ref.update(eclipse_type=ty, is_central=bool(ty and g < 1 - abs(u) + 1e-9) if ty else None, ecl_time_offset_s=(tg - j) * 86400.0,
                   begin_offset_s=(b - sb) * 86400.0 if (b is not None and sb) else None, end_offset_s=(e - se) * 86400.0 if (e is not None and se) else None,
                   longitude_deg=l, speed_dps=sp, sign=_SIGNS[int(l // 30.0) % 12])
    elif et == "eclipse_lunar":
        tg = _golden_min(lambda x: _lunar_state(x)[0], j - 0.1, j + 0.1)
        rho, m, ru, rp = _lunar_state(tg)
        ty = "total" if rho + m <= ru else "partial" if rho - m < ru else "penumbral" if rho - m < rp else None
        if ty is not None and min(abs(rho + m - ru), abs(rho - m - ru), abs(rho - m - rp)) <= 3.0e-4:             # 3e-4 rad = 62 arcsec of a type boundary
            ref["_ambiguous"] = {"eclipse_type": {"note": "within 62 arcsec of a lunar type boundary", "neighbours": list(_LUNAR_NEIGHBOURS[ty])}}
        elif ty is None and abs(rho - m - rp) <= 3.0e-4:
            ref["_ambiguous"] = {"eclipse_type": {"note": "within 62 arcsec of the penumbral limit", "neighbours": ["penumbral"]}}
        fu = lambda x: (lambda s: s[0] - s[1] - s[2])(_lunar_state(x))
        sb, se = r["_detail"].get("begin_jd"), r["_detail"].get("end_jd")
        b = _bisect(fu, tg - 0.3, tg) if ty in ("total", "partial") else None
        e = _bisect(fu, tg, tg + 0.3) if ty in ("total", "partial") else None
        l, sp = _lon_speed(ctx, "Moon", j)
        ref.update(eclipse_type=ty, ecl_time_offset_s=(tg - j) * 86400.0, begin_offset_s=(b - sb) * 86400.0 if (b is not None and sb) else None,
                   end_offset_s=(e - se) * 86400.0 if (e is not None and se) else None, longitude_deg=l, speed_dps=sp, sign=_SIGNS[int(l // 30.0) % 12])
    else:
        raise ValueError(f"unknown event type {et!r}")
    return ref


def _jd_of(iso: str) -> float:
    y, m, d = (int(x) for x in iso.split("-"))
    return _swe().julday(y, m, d, 0.0)


def sky_completeness(rows, ctx, spec):
    """(ok, problems): per family, the independent event counts over [history_start, the family's latest stored event] against the stored counts."""
    swe = _swe()
    _sid(ctx)
    start = _jd_of(ctx["history_start"])
    by = {}
    for r in rows:
        by.setdefault(r["event_type"], []).append(r)
    problems = []
    early = [r for r in rows if isinstance(r["event_jd"], float) and r["event_jd"] < start - 0.01]
    if early:
        problems.append(f"{len(early)} stored event(s) lie before the declared history_start {ctx['history_start']} (first: {early[0]['event_type']} {early[0]['primary_body']} {early[0]['event_jd']})")

    def span(et):
        js = [r["event_jd"] for r in by.get(et, ()) if r["event_jd"] is not None]
        return (start, max(js)) if js else None

    if span("ingress"):
        _s, end = span("ingress")
        for body in _ING_BODY:
            step = 0.25 if body == "Moon" else 1.0
            counts, t = {}, start
            prev = int(_lon_speed(ctx, body, t)[0] // 30.0)
            while t < end + 1.0:
                nt = t + step
                cur = int(_lon_speed(ctx, body, nt)[0] // 30.0)
                if cur != prev:
                    lo, hi = t, nt
                    for _ in range(40):                      # the instant of the crossing, so an event later than the family's last stored one is not counted
                        mid = (lo + hi) / 2
                        if int(_lon_speed(ctx, body, mid)[0] // 30.0) == prev:
                            lo = mid
                        else:
                            hi = mid
                    if hi <= end + 0.01:
                        counts[cur] = counts.get(cur, 0) + 1
                prev, t = cur, nt
            for i, sg in enumerate(_SIGNS):
                n = sum(1 for r in by["ingress"] if r["primary_body"] == body and r["sign"] == sg and start <= r["event_jd"] <= end)
                if counts.get(i, 0) != n:
                    problems.append(f"ingress {body}->{sg}: {counts.get(i, 0)} independent, {n} stored")
    if span("station"):
        _s, end = span("station")
        for body in _STATION_BODIES:
            counts, t = {"retrograde": 0, "direct": 0}, start
            prev = _lon_speed(ctx, body, t)[1]
            while t < end + 1.0:
                nt = t + 1.0
                cur = _lon_speed(ctx, body, nt)[1]
                if prev * cur < 0:
                    tz = _illinois(lambda x: _lon_speed(ctx, body, x)[1], t, nt)
                    if tz is not None and tz <= end + 0.01:
                        counts["retrograde" if prev > 0 else "direct"] += 1
                prev, t = cur, nt
            for k, v in counts.items():
                n = sum(1 for r in by["station"] if r["primary_body"] == body and r["station_type"] == k and start <= r["event_jd"] <= end)
                if v != n:
                    problems.append(f"station {body} {k}: {v} independent, {n} stored")
    if span("double_transit"):
        _s, end = span("double_transit")
        sd = lambda l, b: (l - b + 180.0) % 360.0 - 180.0
        for pair in sorted({(r["primary_body"], r["secondary_body"]) for r in by["double_transit"]}):
            n_ind, t, inside, best = 0, start, False, None
            sep = lambda x: abs(sd(_lon_speed(ctx, pair[0], x)[0], _lon_speed(ctx, pair[1], x)[0]))
            while t <= end:
                s = sep(t)
                if s <= 1.0:
                    inside = True
                elif inside:
                    n_ind += 1
                    inside = False
                t += 1.0
            n = sum(1 for r in by["double_transit"] if (r["primary_body"], r["secondary_body"]) == pair and start <= r["event_jd"] <= end)
            if inside:
                n_ind += 1
            if n_ind != n:
                problems.append(f"double_transit {pair[0]}-{pair[1]}: {n_ind} independent windows, {n} stored")
    for et, ev_type in (("eclipse_solar", "new"), ("eclipse_lunar", "full")):
        if not span(et):
            continue
        _s, end = span(et)
        target = 0.0 if ev_type == "new" else 180.0
        ph = lambda x: ((swe.calc_ut(x, swe.MOON)[0][0] - swe.calc_ut(x, swe.SUN)[0][0] - target + 180.0) % 360.0) - 180.0
        n_ind, t = 0, start - 1.0
        while t < end + 1.0:
            if ph(t) < 0 <= ph(t + 1.0):
                ts = _illinois(ph, t, t + 1.0)
                if ts is not None:
                    if et == "eclipse_solar":
                        tg = _golden_min(lambda x: _solar_geom(x)[0], ts - 0.25, ts + 0.25)
                        g, u, l1, _z, _t = _solar_geom(tg)
                        hit = g < 1 + l1
                    else:
                        tg = _golden_min(lambda x: _lunar_state(x)[0], ts - 0.25, ts + 0.25)
                        rho, m, _ru, rp = _lunar_state(tg)
                        hit = rho - m < rp
                    if hit and start - 0.01 <= tg <= end + 0.01:
                        n_ind += 1
            t += 1.0
        n = sum(1 for r in by[et] if start <= r["event_jd"] <= end)
        if n_ind != n:
            problems.append(f"{et}: {n_ind} independent, {n} stored")
    return (not problems), problems[:20]


# ───────────────────────── registration ─────────────────────────

def register_all(d3) -> None:
    d3.register_method(
        "swisseph_sidereal_positions_v1", tables=("chart_facts",), assets=("ga_positions",), completeness=None, independence="independent_formula",
        max_tol=dict({c: 0 for c in POSITION_COLUMNS}, longitude_sidereal=0.002, degree_in_sign=0.002, dist_to_madhya_deg=0.002, dist_to_nearest_boundary_deg=0.002,
                     **{c: 0.002 for c in _CUSP_KEYS}),
        required_conventions={"position_model": ("true_geometric", "apparent"), "node_model": ("mean_node",), "house_rule": ("whole_sign",),
                              "bhava_system": ("sripati_quadrant_trisection_and_placidus",), "bhava_flags": ("sidereal_only",), "combustion_orbs": ("moon12_mars17_mercury14_jupiter11_venus10_saturn15",),
                              "sandhi_orb": ("3.0",)},
        reads=("chart_facts: the declared columns where the declared closed predicate holds (chart-scoped)", "charts: one row, the chart's birth parameters"),
        logical_rows=positions_logical_rows, context=positions_context, ref=positions_ref, version="1", backend_probe=backend_probe, backends=BACKENDS,
        inputs_table={"table": "charts", "columns": ("birth_date", "birth_time", "birth_lat", "birth_lng", "timezone_id")},
        rule_text=("per (graha, Lagna or bhava, ayanamsha): the sidereal longitude is re-computed by pyswisseph called directly (sidereal mode chosen by swisseph constant name, mean node, "
                   "Ketu = Rahu + 180, Lagna from houses_ex at the birth instant converted by the stdlib time zone database), under the declared position model; degree in sign, sign, "
                   "nakshatra (the stored name's place in the classical order of the 27, spelling variants folded), pada and whole-sign house are derived from that longitude by arithmetic; the retrograde flag "
                   "is the sign of the longitude speed; sign lord, nakshatra lord and combustion state come from the declared classical tables (sign lords, the Vimshottari nakshatra cycle, the combustion orbs); "
                   "the bhava cusps are the Placidus cusps from houses_ex and the Sripati madhyas by trisecting each quadrant arc between the angles, sandhis at the midpoints of adjacent madhyas; "
                   "a graha's chalit house is the arc between sandhis it lies in, its arcs to the madhya and nearest boundary follow, and the sandhi flag is true when that arc is within the declared "
                   "orb or the chalit house differs from the whole-sign house. A discrete value next to a cell edge is accepted only within the declared tolerance of the edge and listed"))
    d3.register_method(
        "swisseph_sky_events_v1", tables=("bg_sky_calendar",), assets=("bg_sky_calendar",), independence="independent_formula",
        max_tol={"edge_distance_deg": {"default": 0.002, "values": {"Rahu": 0.01, "Ketu": 0.01}}, "longitude_deg": {"default": 0.002, "values": {"Rahu": 0.01, "Ketu": 0.01}},
                 "speed_dps": 0.01, "event_datetime_s": 2.0, "target_sign": 0, "sign": 0, "nakshatra_num": 0, "ayanamsha_key": 0, "station_type": 0, "station_zero_speed": 0.002, "conj_orb_deg": 0.002, "conj_offset_deg": 0.002,
                 "planet_b_lon": 0.002, "eclipse_type": 0, "is_central": 0, "ecl_time_offset_s": 240.0, "begin_offset_s": 240.0, "end_offset_s": 240.0},
        required_conventions={"position_model": ("apparent",), "node_model": ("true_node",), "ayanamsha": ("lahiri",), "eclipse_geometry": ("swecl_radii_fundamental_plane",),
                              "shadow_enlargement": ("1_over_0.99",), "history_start": ("1900-01-01",)},
        reads=("bg_sky_calendar: the declared columns of every row (all event families)",),
        logical_rows=sky_logical_rows, context=sky_context, ref=sky_ref, completeness=sky_completeness, version="2", backend_probe=backend_probe, backends=BACKENDS, inputs_table=None,
        rule_text=("per stored event, by pyswisseph called directly: ingress = the body's distance from the nearest sign edge at the stored instant (claimed 0), a crossing of that edge within "
                   "0.2 day, the longitude, speed, sign entered and nakshatra; station = speed at the stored instant (claimed 0), a zero of the speed within 0.5 day, the type from the speed "
                   "before, longitude, sign, nakshatra; double transit = the pair's minimum separation within 2 days, the separation at the stored instant, the stored orb and second "
                   "longitude; eclipse = the greatest-eclipse instant by minimising the shadow-axis distance (solar: fundamental-plane gamma and umbra radius with the swecl.c radii, "
                   "hybrid when the umbra radius changes sign between the limb and the nearest surface point; lunar: Moon to anti-Sun angle against the umbra and penumbra with the 1/0.99 "
                   "enlargement), the type, is_central, the begin and end contacts, the Sun or Moon longitude and speed; completeness = independent counts of sign entries (0.25 day Moon, "
                   "1 day others), station and minimum windows, and the eclipse condition on every new and full moon, over [history_start, the family's latest stored event]"))
