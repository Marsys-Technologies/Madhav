"""
_positions_independent_verifier.py -- N-169 independent second calculation of the natal positions
====================================================================================================

Re-derives, by direct Swiss Ephemeris calls, every `chart_facts` row `ga_positions_writer` is about
to insert for one (chart, ayanamsha) and compares them row by row, so the build itself carries a
real second route (the writer's first route is the PyJHora adapter, `pyjhora_adapter.compute`).
The writer calls `compare_rows` BEFORE inserting anything and raises on any mismatch
(`ga_positions_writer._second_calculation`).

This is a PORT, not an import. The same derivation exists in the governance tree as the reviewed
Carr.D3 method `swisseph_sidereal_positions_v1` (`platform/scripts/governance/carriage_d3_methods.py`,
`positions_context` / `positions_ref`), the engine's reference for the same claim; the governance
tree is not importable from the build image, so the arithmetic is copied here. Tolerances,
conventions and the discrete-cell boundary rule are the ones that method DECLARES in
`asset_declarations.json` (`ga_positions.carriage.spec`): `tests/test_positions_second_calc.py`
holds a parity test that loads both and demands identical values on fixtures. Precedent for a
sidecar-local independent verifier: `_vimshottari_independent_verifier.py`.

INDEPENDENCE AUDIT (what this module imports, and why that does not share the writer's defects):
  - `swisseph` (lazily): the library itself, called directly with this module's own constants and
    arithmetic. NOT imported: `pyjhora_adapter` (the writer's first route and its maps),
    `ga_positions_writer`, `brahmagyan.graha_vocabulary`. The ayanamsha id -> swisseph constant map
    below is this module's own, by constant NAME (the Track A1 `krishnamurti`-resolves-to-Lahiri
    class is exactly what sharing the adapter's map would share).
  - `panchang_engine.swiss_state.swiss_state_scope`: the process-wide Swiss state lock only (no
    astronomy): `set_sid_mode` and every dependent call are one critical section.
  What it shares with the writer is the ephemeris DATA behind the library. The backend: `_derive`
  calls `panchang_engine.swiss_backend.ensure_swiss_backend(jd)` (fail closed: an unset
  SE_EPHE_PATH, a probe that is not `swieph`, or a date outside the corpus raises), inside this
  digest-bound module, so a completed build's receipt binds "the second calculation ran on swieph".

CONVENTIONS (declared, not tuned): position model `true_geometric` (SEFLG_TRUEPOS, the convention
PyJHora's `drik` uses); node model mean node (Ketu = Rahu + 180); house rule whole-sign; bhava
system Sripati quadrant trisection of Placidus cusps, cusps with the sidereal flag only; combustion
orbs Moon 12, Mars 17, Mercury 14, Jupiter 11, Venus 10, Saturn 15; sandhi orb 3.0 degrees.

INPUTS: only `birth_params` (the dict the orchestrator pre-fetches into `ctx.config`):
`datetime_iso` (local wall clock), `latitude_deg`, `longitude_deg`, `tz_offset_hours`.

PRIVACY: nothing in this module's return values or exception messages carries a birth parameter.
A failure to run raises `SecondCalcError` with the exception TYPE only (`from None`, so the chained
original, which can quote an input string, is not in the traceback text the orchestrator records).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

# ── declared tolerances (asset_declarations.json, ga_positions.carriage.spec.columns) ──────────────
TOL_DEG = 0.001                     # circular_deg / circular_30 / linear columns: 3.6 arcsec, the writer's 6-decimal precision with a margin

KIND_CIRCULAR_DEG = "circular_deg"
KIND_CIRCULAR_30 = "circular_30"
KIND_LINEAR = "linear"
KIND_EXACT = "exact"
_PERIOD = {KIND_CIRCULAR_DEG: 360.0, KIND_CIRCULAR_30: 30.0}

# The ayanamsha id -> swisseph sidereal-mode constant, by this module's own table (written out, no attribute lookup by name), keyed by the writer's canonical ids.
# The id vocabulary (the DEFAULT / validation set) is the shared one (ONE_AYANAMSHA, SS N-309/N-311); the swisseph constants stay this module's own.
from brahmagyan.ayanamsha_scope import CANONICAL_FIVE as _CANONICAL_AYANAMSHAS  # noqa: E402


def _sidm(swe: Any, canonical_id: str) -> int | None:
    # positional with the shared canonical order (lahiri, true_chitra, krishnamurti, raman, surya_siddhanta); pinned id-by-id by test_one_ayanamsha_b1
    table = dict(zip(_CANONICAL_AYANAMSHAS, (swe.SIDM_LAHIRI, swe.SIDM_TRUE_CITRA, swe.SIDM_KRISHNAMURTI, swe.SIDM_RAMAN, swe.SIDM_SURYASIDDHANTA)))
    return table.get(canonical_id)


def _body(swe: Any, subject: str) -> int:
    """fact_subject (the writer's vocabulary) -> swisseph body constant; Ketu is the mean node, shifted by 180 degrees where it is derived."""
    return {"SUN": swe.SUN, "MOON": swe.MOON, "MAR": swe.MARS, "MER": swe.MERCURY, "JUP": swe.JUPITER, "VEN": swe.VENUS,
            "SAT": swe.SATURN, "RAH_MEAN": swe.MEAN_NODE, "KET_MEAN": swe.MEAN_NODE}[subject]


_GRAHA_SUBJECTS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")      # the nine grahas, in the writer's order
LAGNA_SUBJECT = "LAGNA"
_BHAVA_SUBJECTS = tuple(f"BHAVA_{h:02d}" for h in range(1, 13))
_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
          "Aquarius", "Pisces")
_SIGN_LORD = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
_NAK_LORD_CYCLE = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
_COMBUST_ORB = {"MOON": 12.0, "MAR": 17.0, "MER": 14.0, "JUP": 11.0, "VEN": 10.0, "SAT": 15.0}
_SANDHI_ORB = 3.0

_NAKSHATRA_ORDER = ("ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha",
                    "magha", "purvaphalguni", "uttaraphalguni", "hasta", "chitra", "swati", "vishakha", "anuradha",
                    "jyeshtha", "mula", "purvaashadha", "uttaraashadha", "shravana", "dhanishta", "shatabhisha",
                    "purvabhadrapada", "uttarabhadrapada", "revati")
_NAK_ALIASES = {"moola": "mula", "mrigasira": "mrigashira", "dhanishtha": "dhanishta", "ashvini": "ashwini",
                "aslesha": "ashlesha", "jyestha": "jyeshtha", "visakha": "vishakha"}

# Discrete value derived from a continuous one: accepted at a cell edge only when the stored cell is the
# NEIGHBOUR of the reference cell and the longitude is within the declared tolerance of the edge
# (asset_declarations.json ga_positions.carriage.spec.boundary). Listed in the result, never silent.
_BOUNDARY = {"sign_num": (30.0, 12), "nakshatra_num": (360.0 / 27, 27), "pada": (360.0 / 108, 4)}

# writer fact_key -> the logical column the derivation produces (the writer's EAV keys, not the logical names)
_KEY_TO_COLUMN = {
    "longitude_sidereal": "longitude_sidereal", "degree_in_sign": "degree_in_sign", "sign_num": "sign_num", "sign": "sign",
    "sign_lord": "sign_lord", "nakshatra": "nakshatra_num", "nakshatra_lord": "nakshatra_lord", "pada": "pada",
    "house_d1": "house_d1", "retrograde_flag": "retrograde_flag", "combustion_state": "combustion_state",
    "chalit_house_sripati": "chalit_house", "whole_sign_house": "whole_sign_house",
    "dist_to_madhya_deg": "dist_to_madhya_deg", "dist_to_nearest_boundary_deg": "dist_to_nearest_boundary_deg",
    "nearest_boundary": "nearest_boundary", "sandhi_flag": "sandhi_flag", "sandhi_reasons": "sandhi_reasons",
}
_CUSP_KEYS = tuple(f"{sy}_{e}" for sy in ("sripati", "placidus") for e in ("start", "madhya", "end"))
_KIND_BY_COLUMN = {
    "longitude_sidereal": KIND_CIRCULAR_DEG, "degree_in_sign": KIND_CIRCULAR_30, "dist_to_madhya_deg": KIND_LINEAR,
    "dist_to_nearest_boundary_deg": KIND_LINEAR,
}
_INT_COLUMNS = ("sign_num", "nakshatra_num", "pada", "house_d1", "chalit_house", "whole_sign_house")

MAX_NAMED = 10                                       # mismatching rows a message names


class SecondCalcError(RuntimeError):
    """The second calculation could not run (not a mismatch). The message carries no birth parameter."""


@dataclass(frozen=True)
class Derived:
    """One independently derived value: its comparator kind and, for a discrete column, the longitude cell it came from."""
    kind: str
    value: Any
    boundary_source_lon: float | None = None


@dataclass
class CompareResult:
    matched: int = 0
    not_matched: int = 0
    not_derived: int = 0
    boundary_tolerated: int = 0
    rows: int = 0                                    # rows the writer offered
    derivable: int = 0                               # distinct (subject, key) the verifier derives for this ayanamsha
    mismatches: list[tuple[str, str, Any, Any]] = field(default_factory=list)   # (fact_subject, fact_key, writer value, verifier value)
    not_derived_rows: list[tuple[str, str, Any]] = field(default_factory=list)  # (fact_subject, fact_key, writer value): rows no derivation exists for


# ───────────────────────────── small helpers (ported) ─────────────────────────────

def nakshatra_number(name: Any) -> int | None:
    """1-based classical index of a stored nakshatra NAME (case/separator folded, fixed spelling-variant table), or None."""
    if not isinstance(name, str):
        return None
    k = re.sub(r"[^a-z]", "", name.lower())
    k = _NAK_ALIASES.get(k, k)
    return _NAKSHATRA_ORDER.index(k) + 1 if k in _NAKSHATRA_ORDER else None


def _fwd(a: float, b: float) -> float:
    return (b - a) % 360.0


def _mid(a: float, b: float) -> float:
    return (a + _fwd(a, b) / 2.0) % 360.0


def _sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _ang_diff(a: float, b: float, period: float) -> float:
    d = abs(a - b) % period
    return min(d, period - d)


def _swe():
    import swisseph as swe
    return swe


def _birth_instant(birth_params: dict[str, Any]) -> tuple[float, float, float]:
    """(jd_ut, latitude, longitude) from the writer's own birth_params dict, by swisseph's Julian-day function."""
    swe = _swe()
    naive = datetime.fromisoformat(str(birth_params["datetime_iso"]))
    if naive.tzinfo is not None:                     # the writer's convention: a local wall clock, the offset a separate field
        naive = naive.replace(tzinfo=None)
    tz = float(birth_params["tz_offset_hours"])
    hours = naive.hour + naive.minute / 60 + naive.second / 3600 - tz
    return swe.julday(naive.year, naive.month, naive.day, hours), float(birth_params["latitude_deg"]), float(birth_params["longitude_deg"])


def _bhavas(plac: list[float]) -> tuple[list[float], list[float]]:
    """(sripati madhyas[12], sripati sandhis[12]) from the Placidus cusps (computed by `_derive`, which owns the Swiss state): Sripati madhyas by
    trisecting each quadrant arc between the angles; sandhi h = midpoint of madhya h and h + 1 (house h spans sandhi h - 1 to sandhi h)."""
    mad = list(plac)
    for a, b in ((0, 3), (3, 6), (6, 9), (9, 0)):
        step = _fwd(plac[a], plac[b]) / 3.0
        mad[(a + 1) % 12] = (plac[a] + step) % 360.0
        mad[(b - 1) % 12] = (plac[b] - step) % 360.0
    sand = [_mid(mad[h], mad[(h + 1) % 12]) for h in range(12)]
    return mad, sand


def _kind(column: str) -> str:
    if column in _KIND_BY_COLUMN:
        return _KIND_BY_COLUMN[column]
    if column.endswith(("_start", "_madhya", "_end")):
        return KIND_CIRCULAR_DEG
    return KIND_EXACT


# ───────────────────────────── the derivation ─────────────────────────────

def derive_reference(birth_params: dict[str, Any], canonical_ayanamsha_id: str) -> dict[tuple[str, str], Derived]:
    """Every (fact_subject, fact_key) -> Derived this verifier can derive for ONE ayanamsha: the nine grahas (18 keys each), the Lagna (7 keys) and
    the twelve bhavas (6 cusp keys each). The set of derivable pairs is this module's own enumeration, independent of what the writer emitted
    (so a row the writer dropped is found missing, not silently absent). Raises SecondCalcError (type only) if it cannot run."""
    if canonical_ayanamsha_id not in _CANONICAL_AYANAMSHAS:
        return {}                                    # an id this module does not know: nothing derivable (the caller counts the rows not_derived)
    try:
        return _derive(birth_params, canonical_ayanamsha_id)
    except SecondCalcError:
        raise
    except Exception as exc:  # noqa: BLE001 - re-raised with the type only: the original message can quote a birth input
        raise SecondCalcError(f"positions second calculation could not run ({type(exc).__name__})") from None


def _derive(birth_params: dict[str, Any], canonical_ayanamsha_id: str) -> dict[tuple[str, str], Derived]:
    from panchang_engine.swiss_backend import ensure_swiss_backend
    from panchang_engine.swiss_state import swiss_state_scope

    swe = _swe()
    out: dict[tuple[str, str], Derived] = {}
    jd, lat, lon = _birth_instant(birth_params)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_TRUEPOS       # position_model = true_geometric (declared)
    with swiss_state_scope():
        # Fail closed BEFORE any derivation: the `.se1` corpus must be serving this thread for this birth date (no silent Moshier fallback). This call is inside the digest-bound
        # verifier on purpose: the receipt's code digest therefore binds "the second calculation ran on swieph" (SS N-180 Option C).
        ensure_swiss_backend(jd)
        swe.set_sid_mode(_sidm(swe, canonical_ayanamsha_id))
        plac = [c % 360.0 for c in swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)[0][:12]]       # Placidus cusps, sidereal flag only
        mad, sand = _bhavas(plac)
        asc_lon = swe.houses_ex(jd, lat, lon, b"W", flags & ~swe.FLG_SPEED)[1][0] % 360.0
        asc_sign = int(asc_lon // 30.0)
        sun_lon = swe.calc_ut(jd, swe.SUN, flags)[0][0] % 360.0

        for h in range(12):
            subj = _BHAVA_SUBJECTS[h]
            vals = {"sripati_start": sand[(h - 1) % 12], "sripati_madhya": mad[h], "sripati_end": sand[h],
                    "placidus_start": plac[h], "placidus_madhya": _mid(plac[h], plac[(h + 1) % 12]), "placidus_end": plac[(h + 1) % 12]}
            for k, v in vals.items():
                out[(subj, k)] = Derived(KIND_CIRCULAR_DEG, v)

        def _common(lon_sid: float) -> dict[str, Any]:
            sign_idx = int(lon_sid // 30.0)
            return {
                "longitude_sidereal": lon_sid, "degree_in_sign": lon_sid % 30.0, "sign_num": sign_idx + 1, "sign": _SIGNS[sign_idx],
                "sign_lord": _SIGN_LORD[sign_idx], "pada": int((lon_sid % (360.0 / 27)) // (360.0 / 108)) + 1,
                "house_d1": ((sign_idx - asc_sign) % 12) + 1,
            }

        def _put(subj: str, cols: dict[str, Any], lon_sid: float) -> None:
            inv = {v: k for k, v in _KEY_TO_COLUMN.items()}
            for col, val in cols.items():
                out[(subj, inv[col])] = Derived(_kind(col), val, lon_sid if col in _BOUNDARY else None)

        _put(LAGNA_SUBJECT, _common(asc_lon), asc_lon)

        for subj in _GRAHA_SUBJECTS:
            res, _rf = swe.calc_ut(jd, _body(swe, subj), flags)
            lon_sid, speed = res[0] % 360.0, res[3]
            if subj == "KET_MEAN":
                lon_sid = (lon_sid + 180.0) % 360.0
            cols = _common(lon_sid)
            nak = int(lon_sid // (360.0 / 27))
            cols.update(nakshatra_num=nak + 1, nakshatra_lord=_NAK_LORD_CYCLE[nak % 9],
                        retrograde_flag="retrograde" if speed < 0 else "direct",
                        combustion_state="combust" if subj in _COMBUST_ORB and _sep(lon_sid, sun_lon) <= _COMBUST_ORB[subj] else "none")
            h = next((i for i in range(12) if _fwd(sand[(i - 1) % 12], lon_sid) < _fwd(sand[(i - 1) % 12], sand[i])), 0)
            ds, de = _sep(lon_sid, sand[(h - 1) % 12]), _sep(lon_sid, sand[h])
            near, dist = ("start", ds) if ds <= de else ("end", de)
            reasons = (["within_boundary_orb"] if dist <= _SANDHI_ORB else []) + (["wholesign_chalit_divergence"] if cols["house_d1"] != h + 1 else [])
            cols.update(chalit_house=h + 1, whole_sign_house=cols["house_d1"], dist_to_madhya_deg=_sep(lon_sid, mad[h]),
                        dist_to_nearest_boundary_deg=dist, nearest_boundary=near,
                        sandhi_flag=str(bool(reasons)).lower(), sandhi_reasons=",".join(reasons) or "none")
            _put(subj, cols, lon_sid)
    return out


# ───────────────────────────── the comparison ─────────────────────────────

def _stored_value(row: dict[str, Any], column: str) -> Any:
    """The writer row's value in the comparator's terms: a number (an integer column reads as int, None if not integral), the nakshatra NAME read as its
    1-based number, else the text."""
    vn, vt = row.get("fact_value_num"), row.get("fact_value_text")
    if column == "nakshatra_num":
        return nakshatra_number(vt)
    if column in _INT_COLUMNS:
        return int(round(vn)) if isinstance(vn, (int, float)) and not isinstance(vn, bool) and float(vn).is_integer() else None
    if column in ("sign", "sign_lord", "nakshatra_lord", "retrograde_flag", "combustion_state", "nearest_boundary", "sandhi_flag", "sandhi_reasons"):
        return vt
    return float(vn) if isinstance(vn, (int, float)) and not isinstance(vn, bool) else None


def _agree(kind: str, stored: Any, ref: Any) -> bool:
    if kind == KIND_EXACT:
        if isinstance(stored, bool) != isinstance(ref, bool):
            return False
        return stored == ref
    ok = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)  # noqa: E731
    if not (ok(stored) and ok(ref)):
        return False
    r = _ang_diff(float(stored), float(ref), _PERIOD[kind]) if kind in _PERIOD else abs(float(stored) - float(ref))
    return r <= TOL_DEG


def _boundary_ok(column: str, stored: Any, ref: Derived) -> bool:
    b = _BOUNDARY.get(column)
    if b is None or ref.boundary_source_lon is None:
        return False
    width, cells = b
    sv, rv = stored, ref.value
    if not (isinstance(sv, int) and isinstance(rv, int)) or isinstance(sv, bool) or isinstance(rv, bool):
        return False
    if (sv - rv) % cells not in (1, cells - 1):
        return False
    edge = min(ref.boundary_source_lon % width, width - (ref.boundary_source_lon % width))
    return edge <= TOL_DEG


def _shown(v: Any) -> Any:
    return round(v, 6) if isinstance(v, float) else v


def compare_rows(rows: Iterable[dict[str, Any]], derived: dict[tuple[str, str], Derived]) -> CompareResult:
    """Compare every writer row (one ayanamsha) with the independent derivation. A row with no derivation is `not_derived` (never matched). A
    derivable (subject, key) the writer did not offer is `not_matched` (writer value None). `mismatches` lists (subject, key, writer value, verifier value)."""
    res = CompareResult(derivable=len(derived))
    seen: set[tuple[str, str]] = set()
    for r in rows:
        res.rows += 1
        subj, key = r.get("fact_subject"), r.get("fact_key")
        cat = r.get("fact_category")
        ref = derived.get((subj, key)) if (cat == "bhava_cusps") == (key in _CUSP_KEYS) else None
        if ref is None:
            res.not_derived += 1
            if len(res.not_derived_rows) < MAX_NAMED:
                res.not_derived_rows.append((subj, key, _shown(r.get("fact_value_num") if r.get("fact_value_num") is not None else r.get("fact_value_text"))))
            continue
        seen.add((subj, key))
        col = _KEY_TO_COLUMN.get(key, key)
        stored = _stored_value(r, col)
        if _agree(ref.kind, stored, ref.value):
            res.matched += 1
        elif _boundary_ok(col, stored, ref):
            res.matched += 1
            res.boundary_tolerated += 1
        else:
            res.not_matched += 1
            res.mismatches.append((subj, key, r.get("fact_value_text") if col == "nakshatra_num" else _shown(stored),
                                   f"nakshatra_num={ref.value}" if col == "nakshatra_num" else _shown(ref.value)))
    for (subj, key), ref in sorted(derived.items()):
        if (subj, key) not in seen:
            res.not_matched += 1
            res.mismatches.append((subj, key, None, _shown(ref.value)))
    return res
