"""
_chart_output_adapter.py — Input shim for FORENSIC.md renderers.

Transforms pyjhora_adapter.compute_chart() output into the dict shape
expected by the 13 ForensicRenderer section renderers.

RULE: This is the ONLY place shape mismatches are fixed. Never modify
the tested renderers to accommodate a shape difference.

Key transformations applied by to_render_input():
  planets       — adds `degree` (alias of degree_in_sign), `dignity`
                  (alias of dignity_status), `varga_positions` from vargas
  houses        — converts flat whole-sign list to 6-system dict with
                  `house`/`lord` keys + occupying_planets
  upagrahas     — maps sensitive_points (gulika/maandi/kaala/…) to
                  renderer keys; adds `degree` alias
  vargas        — converts list-per-varga to nested dict keyed by
                  lowercase body name
  panchanga     — wraps flat tithi/vara/nakshatra/yoga/karana strings
                  into the nested dict the panchanga_renderer expects
  dashas        — converts mahadasha_sequence to per-system dict with
                  next_10_mahas populated for vimshottari
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Classical sign→lord mapping (0-based sign index)
# ---------------------------------------------------------------------------

_SIGN_LORD: dict[int, str] = {
    0: "Mars",      # Aries
    1: "Venus",     # Taurus
    2: "Mercury",   # Gemini
    3: "Moon",      # Cancer
    4: "Sun",       # Leo
    5: "Mercury",   # Virgo
    6: "Venus",     # Libra
    7: "Mars",      # Scorpio
    8: "Jupiter",   # Sagittarius
    9: "Saturn",    # Capricorn
    10: "Saturn",   # Aquarius
    11: "Jupiter",  # Pisces
}

_SIGN_NAMES: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _sign_lord_for(sign: str) -> str:
    """Return lord for a full English sign name."""
    try:
        idx = _SIGN_NAMES.index(sign)
        return _SIGN_LORD[idx]
    except (ValueError, KeyError):
        return "N/A"


# ---------------------------------------------------------------------------
# Per-section adapters
# ---------------------------------------------------------------------------

def _adapt_planets(chart_output: dict) -> list[dict]:
    """
    Normalize the 'planets' list to planets_renderer shape.

    pyjhora provides: degree_in_sign, dignity_status; no varga_positions.
    Renderer expects: degree, dignity, varga_positions{D1,D9,D10}.
    """
    planets = list(chart_output.get("planets") or [])
    vargas_raw = chart_output.get("vargas") or {}

    # Build per-varga body-name → {sign, lord} lookup.
    # vargas_raw[vk] is either a list (pyjhora) or already a dict (adapted).
    varga_idx: dict[str, dict[str, dict[str, str]]] = {}
    for vk, rows in vargas_raw.items():
        if not isinstance(rows, list):
            continue
        lookup: dict[str, dict[str, str]] = {}
        for row in rows:
            name = str(row.get("name", ""))
            key = "lagna" if name == "Lagna" else name.lower()
            sign = str(row.get("sign", ""))
            lookup[key] = {"sign": sign, "lord": _sign_lord_for(sign)}
        varga_idx[vk] = lookup

    out: list[dict] = []
    for p in planets:
        pp = dict(p)
        # degree alias
        if "degree" not in pp:
            pp["degree"] = pp.get("degree_in_sign")
        # dignity alias
        if "dignity" not in pp:
            pp["dignity"] = pp.get("dignity_status")
        # varga_positions for D1/D9/D10
        pid = str(pp.get("id") or "")
        vp: dict[str, dict[str, str]] = {}
        for vk in ("D1", "D9", "D10"):
            vrow = varga_idx.get(vk, {}).get(pid)
            if vrow:
                vp[vk] = vrow
        pp["varga_positions"] = vp
        out.append(pp)
    return out


def _adapt_houses(chart_output: dict) -> dict:
    """
    Convert pyjhora's flat whole-sign house list to the 6-system dict the
    houses_renderer expects.

    Per-house: renames house_number→house, sign_lord→lord; adds
    occupying_planets derived from the planets list.
    All 6 systems receive identical whole-sign data (pyjhora only provides
    whole-sign; the renderer degrades gracefully for missing cusp precision).
    """
    raw_houses = chart_output.get("houses") or []

    # Build occupant map: house_number → [lowercase_planet_id]
    occupants: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for p in (chart_output.get("planets") or []):
        h_val = p.get("house")
        pid = str(p.get("id") or p.get("name", "")).lower()
        if h_val and pid:
            try:
                occupants[int(h_val)].append(pid)
            except (TypeError, ValueError):
                pass

    def _build_list(src: list[dict]) -> list[dict]:
        result: list[dict] = []
        for entry in src:
            h_num = (
                entry.get("house_number")
                or entry.get("house_num")
                or entry.get("house")
            )
            sign = entry.get("sign", "")
            lord = (
                entry.get("lord")
                or entry.get("sign_lord")
                or _sign_lord_for(sign)
            )
            occ = occupants.get(int(h_num) if h_num else 0, []) or None
            result.append({
                "house":              h_num,
                "sign":               sign,
                "lord":               lord,
                "co_lord":            entry.get("co_lord"),
                "nakshatra":          entry.get("nakshatra"),
                "pada":               entry.get("pada"),
                "occupying_planets":  occ,
            })
        return result

    house_list = _build_list(raw_houses)
    return {
        "placidus":   house_list,
        "whole_sign": house_list,
        "equal":      house_list,
        "koch":       house_list,
        "campanus":   house_list,
        "porphyry":   house_list,
    }


def _adapt_upagrahas(chart_output: dict) -> dict:
    """
    Map sensitive_points (gulika, maandi, kaala, mrityu, …) into the
    upagrahas dict the upagrahas_renderer expects.

    Adds `degree` alias for degree_in_sign; skips error entries.
    """
    sens = chart_output.get("sensitive_points") or {}
    out: dict[str, Any] = {}
    for name, data in sens.items():
        if not isinstance(data, dict) or "error" in data:
            continue
        entry = dict(data)
        if "degree" not in entry:
            entry["degree"] = entry.get("degree_in_sign")
        out[name] = entry
    return out


def _adapt_vargas(chart_output: dict) -> dict:
    """
    Convert pyjhora vargas from list-per-varga to nested-dict-per-varga.

    pyjhora: vargas["D1"] = [{"name": "Lagna"|"Sun"|…, "sign": …, …}, …]
    renderer: vargas["D1"] = {"lagna": {"sign": …, "lord": …}, "sun": {…}, …}
    """
    raw = chart_output.get("vargas") or {}
    out: dict[str, Any] = {}
    for vk, rows in raw.items():
        if not isinstance(rows, list):
            # Already adapted or an error entry — pass through
            out[vk] = rows
            continue
        varga_dict: dict[str, Any] = {}
        for row in rows:
            name = str(row.get("name", ""))
            key = "lagna" if name == "Lagna" else name.lower()
            sign = str(row.get("sign", ""))
            lord = _sign_lord_for(sign)
            entry: dict[str, Any] = {"sign": sign, "lord": lord}
            if key != "lagna":
                entry["dignity"] = row.get("dignity_status") or None
                entry["vargottama"] = row.get("vargottama")
            varga_dict[key] = entry
        out[vk] = varga_dict
    return out


def _adapt_panchanga(chart_output: dict) -> dict:
    """
    Convert pyjhora's flat panchanga (tithi/vara/… as plain strings) into
    the nested dict structure the panchanga_renderer expects.

    If panchanga["tithi"] is already a dict, assume it is pre-adapted and
    return the dict as-is.
    """
    raw = chart_output.get("panchanga") or {}

    # Already in nested format — pass through
    if isinstance(raw.get("tithi"), dict):
        return raw

    return {
        "tithi": {
            "name":            raw.get("tithi", ""),
            "pada":            None,
            "lord":            None,
            "paksha":          None,
            "completion_pct":  None,
        },
        "vara": {
            "name":  raw.get("vara", ""),
            "lord":  None,
        },
        "nakshatra": {
            "name":    raw.get("nakshatra", ""),
            "pada":    raw.get("nakshatra_pada"),
            "lord":    raw.get("nakshatra_lord"),
            "sandhi":  None,
        },
        "yoga": {
            "name":   raw.get("yoga", ""),
            "nature": None,
        },
        "karana": {
            "name":   raw.get("karana", ""),
            "lord":   None,
            "nature": None,
        },
    }


def _adapt_dashas(chart_output: dict) -> dict:
    """
    Convert pyjhora's vimshottari mahadasha_sequence to the per-system dict
    the dashas_renderer expects.

    pyjhora: {"system": "vimshottari", "mahadasha_sequence": [{"lord": …, "start_iso": …, …}]}
    renderer: {"vimshottari": {"next_10_mahas": [{lord, start, end, years}, …], …}}

    If the dict already contains system keys (not mahadasha_sequence), return as-is.
    """
    raw = chart_output.get("dashas") or {}

    if "mahadasha_sequence" not in raw:
        return raw

    sequence = raw.get("mahadasha_sequence") or []
    next_10: list[dict] = [
        {
            "lord":  item.get("lord") or item.get("planet"),
            "start": item.get("start_iso"),
            "end":   item.get("end_iso"),
            "years": item.get("years"),
        }
        for item in sequence[:10]
    ]

    return {
        "vimshottari": {
            "birth_nakshatra_balance": None,
            "current_dates": {},
            "next_10_mahas": next_10,
        },
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def to_render_input(chart_output: dict) -> dict:
    """
    Transform pyjhora_adapter.compute_chart() output into the dict shape
    expected by all 13 ForensicRenderer section renderers.

    Call this once before passing chart_output to ForensicRenderer.render().
    All keys not explicitly transformed are passed through unchanged so
    renderers that consume them directly still work.
    """
    out: dict[str, Any] = dict(chart_output)  # shallow copy — pass all keys through

    out["planets"]   = _adapt_planets(chart_output)
    out["houses"]    = _adapt_houses(chart_output)
    out["upagrahas"] = _adapt_upagrahas(chart_output)
    out["vargas"]    = _adapt_vargas(chart_output)
    out["panchanga"] = _adapt_panchanga(chart_output)
    out["dashas"]    = _adapt_dashas(chart_output)

    return out
