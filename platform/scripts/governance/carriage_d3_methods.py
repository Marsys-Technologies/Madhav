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

_POS_KEYS = {"longitude_sidereal": "longitude_sidereal", "degree_in_sign": "degree_in_sign", "sign_num": "sign_num", "pada": "pada", "house_d1": "house_d1",
             "retrograde_flag": "retrograde_flag", "nakshatra": "nakshatra"}


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _int(v):
    return int(round(v)) if isinstance(v, (int, float)) and not isinstance(v, bool) and float(v).is_integer() else None


def positions_logical_rows(rows, inputs):
    """One logical row per (fact_subject, ayanamsha_id): the EAV rows of the declared read folded into logical columns. A key the writer did not write for a subject stays absent
    (None): the method then derives None for it, so only a claimed fact is compared, and a claimed fact that is missing is a mismatch."""
    by = {}
    for r in rows:
        subj, ay, key = r["fact_subject"], r["ayanamsha_id"], r["fact_key"]
        if key not in _POS_KEYS:
            continue
        d = by.setdefault((subj, ay), dict(subject=subj, ayanamsha=ay))
        if key == "longitude_sidereal" or key == "degree_in_sign":
            d[key] = _num(r.get("fact_value_num"))
        elif key in ("sign_num", "pada", "house_d1"):
            d[key] = _int(r.get("fact_value_num"))
        elif key == "retrograde_flag":
            d[key] = r.get("fact_value_text")
        elif key == "nakshatra":
            t = r.get("fact_value_text")
            d["nakshatra_num"] = nakshatra_number(t)
    out = []
    for d in by.values():
        for c in ("longitude_sidereal", "degree_in_sign", "sign_num", "nakshatra_num", "pada", "house_d1", "retrograde_flag"):
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


def positions_ref(r, ctx):
    swe = _swe()
    ay, subj = r["ayanamsha"], r["subject"]
    name = _SIDM_BY_CANONICAL.get(ay)
    if name is None:
        raise ValueError(f"unknown ayanamsha id {ay!r}")
    swe.set_sid_mode(getattr(swe, name))

    def lagna_sign():
        k = ("lagna", ay)
        if k not in ctx["cache"]:
            asc = swe.houses_ex(ctx["jd"], ctx["lat"], ctx["lon"], b"W", ctx["flags"] & ~swe.FLG_SPEED)[1][0] % 360.0
            ctx["cache"][k] = asc
        return ctx["cache"][k]

    if subj == "LAGNA":
        lon, speed = lagna_sign(), None
    elif subj in _BODY:
        res, _rf = swe.calc_ut(ctx["jd"], getattr(swe, _BODY[subj]), ctx["flags"])
        lon, speed = res[0] % 360.0, res[3]
        if subj == "KET_MEAN":
            lon = (lon + 180.0) % 360.0
    else:
        raise ValueError(f"unknown subject {subj!r}")
    sign_num = int(lon // 30.0) + 1
    ref = dict(longitude_sidereal=lon, degree_in_sign=lon % 30.0, sign_num=sign_num)
    if subj != "LAGNA":
        ref["nakshatra_num"] = int(lon // (360.0 / 27)) + 1
        ref["retrograde_flag"] = "retrograde" if speed < 0 else "direct"
    else:
        ref["nakshatra_num"] = None
        ref["retrograde_flag"] = None
    ref["pada"] = int((lon % (360.0 / 27)) // (360.0 / 108)) + 1
    ref["house_d1"] = ((sign_num - (int(lagna_sign() // 30.0) + 1)) % 12) + 1
    return ref


# ───────────────────────── method 2: sky-calendar ingress events ─────────────────────────

def ingress_logical_rows(rows, inputs):
    """One logical row per stored ingress event. `edge_distance_deg` is what an ingress row CLAIMS about itself: at its stored instant the body is ON a sign edge (distance 0), so
    the stored claim is 0.0 and the reference supplies the measured distance. (The event time is not compared as a time: a time tolerance is not backend-invariant, it scales
    with the body's speed; a position tolerance at the stored instant is. For a body of speed v, a position tolerance t is a time tolerance of t / v.)"""
    return [dict(primary_body=r["primary_body"], sign=r["sign"], event_jd=_num(r["event_jd"]), edge_distance_deg=0.0, longitude_deg=_num(r.get("longitude_deg")),
                 ayanamsha_key=r.get("ayanamsha_key"), event_type=r.get("event_type")) for r in rows]


def ingress_context(rows, inputs, spec):
    swe = _swe()
    cv = spec["conventions"]
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED | (swe.FLG_TRUEPOS if cv["position_model"]["value"] == "true_geometric" else 0)
    return dict(flags=flags, ayanamsha=cv["ayanamsha"]["value"])


def _illinois(f, a, b, tol=1e-9, maxit=100):
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


def ingress_ref(r, ctx):
    swe = _swe()
    name = _SIDM_BY_CANONICAL.get(ctx["ayanamsha"])
    if name is None:
        raise ValueError(f"unknown ayanamsha {ctx['ayanamsha']!r}")
    swe.set_sid_mode(getattr(swe, name))
    body = _ING_BODY.get(r["primary_body"])
    if body is None or r["sign"] not in _SIGNS:
        raise ValueError("unknown body or sign")

    def lon(t):
        v = swe.calc_ut(t, getattr(swe, body), ctx["flags"])[0][0]
        return (v + 180.0) % 360.0 if r["primary_body"] == "Ketu" else v % 360.0

    sd = lambda l, b: (l - b + 180.0) % 360.0 - 180.0
    j = r["event_jd"]
    if not isinstance(j, float):
        raise ValueError("event_jd is not a number")
    lo_edge = _SIGNS.index(r["sign"]) * 30.0
    up_edge = (lo_edge + 30.0) % 360.0
    l = lon(j)
    edge = lo_edge if abs(sd(l, lo_edge)) <= abs(sd(l, up_edge)) else up_edge       # the writer's "ingress" also records a retrograde re-entry across the sign's upper edge
    t = _illinois(lambda x: sd(lon(x), edge), j - 0.2, j + 0.2)
    if t is None:
        raise ValueError("no crossing of the nearest sign edge within 0.2 day of the stored instant")
    entered = _SIGNS[int(lon(t + 0.001) // 30.0) % 12]
    return dict(edge_distance_deg=abs(sd(l, edge)), longitude_deg=l, sign=entered, ayanamsha_key=ctx["ayanamsha"])


# ───────────────────────── registration ─────────────────────────

def register_all(d3) -> None:
    d3.register_method(
        "swisseph_sidereal_positions_v1", tables=("chart_facts",), independence="independent_formula",
        max_tol={"longitude_sidereal": 0.002, "degree_in_sign": 0.002, "sign_num": 0, "nakshatra_num": 0, "pada": 0, "house_d1": 0, "retrograde_flag": 0},
        required_conventions={"position_model": ("true_geometric", "apparent"), "node_model": ("mean_node",), "house_rule": ("whole_sign",)},
        reads=("chart_facts: the declared columns where the declared closed predicate holds (chart-scoped)", "charts: one row, the chart's birth parameters"),
        logical_rows=positions_logical_rows, context=positions_context, ref=positions_ref, version="1", backend_probe=backend_probe, backends=BACKENDS,
        inputs_table={"table": "charts", "columns": ("birth_date", "birth_time", "birth_lat", "birth_lng", "timezone_id")},
        rule_text=("per (graha or Lagna, ayanamsha): the sidereal longitude is re-computed by pyswisseph called directly (sidereal mode chosen by swisseph constant name, mean node, "
                   "Ketu = Rahu + 180, Lagna from houses_ex at the birth instant converted by the stdlib time zone database), under the declared position model; degree in sign, sign, "
                   "nakshatra (the stored name's place in the classical order of the 27, spelling variants folded), pada and whole-sign house are derived from that longitude by arithmetic; the retrograde flag "
                   "is the sign of the longitude speed. A discrete value next to a cell edge is accepted only within the declared tolerance of the edge and listed"))
    d3.register_method(
        "swisseph_ingress_root_find_v1", tables=("bg_sky_calendar",), independence="independent_formula",
        max_tol={"edge_distance_deg": {"default": 0.002, "values": {"Rahu": 0.01, "Ketu": 0.01}}, "longitude_deg": {"default": 0.002, "values": {"Rahu": 0.01, "Ketu": 0.01}},
                 "sign": 0, "ayanamsha_key": 0},
        required_conventions={"position_model": ("apparent", "true_geometric"), "node_model": ("true_node",), "ayanamsha": ("lahiri",)},
        reads=("bg_sky_calendar: the declared columns where event_type = 'ingress'",),
        logical_rows=ingress_logical_rows, context=ingress_context, ref=ingress_ref, version="1", backend_probe=backend_probe, backends=BACKENDS, inputs_table=None,
        rule_text=("per stored ingress event: the longitude is re-computed at the stored instant (pyswisseph called directly) and its distance from the nearest sign edge must be within "
                   "the declared tolerance (the stored row claims the body is ON the edge; the true node is declared a wider tolerance than the planets: SE1_SHIFT_ANALYSIS measured "
                   "its Moshier versus se1 shift at 18 arcsec); a crossing of that edge must exist within +-0.2 day of the stored instant (an Illinois root-finder on the signed distance); "
                   "the sign entered is the sign of the longitude 0.001 day after the re-found crossing; the stored ayanamsha label must equal the declared one"))
