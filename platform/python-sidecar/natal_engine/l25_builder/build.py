"""
natal_engine.l25_builder.build — deterministic L1→L2.5 transform.

Inputs: a `chart_output` dict from natal_engine.compute_chart, plus an
operator-assigned stable `chart_id` (e.g. 'abhisek_mohanty_native_v1').

Outputs: row-shaped dicts for the L2.5 stores. NO Postgres I/O here — the
loader is the I/O surface.

Determinism contract:
  same chart_output (modulo provenance.computed_at_iso) + same chart_id ⇒
  byte-identical canonical-JSONL across runs.

Tested by `tests/test_l25_builder.py` (structural acceptance only — never
runs a model). Deliberately ignores `provenance.computed_at_iso` in the
canonical-JSONL sort so the loader's determinism check survives clock skew.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# ─── Domain taxonomy for CDLM ────────────────────────────────────────────────
# These are the nine MARSYS-JIS canonical domains. The CDLM table links pairs
# of domains by shared structural factors (planets / houses / signs).
_DOMAINS: tuple[str, ...] = (
    "self",          # 1H, Lagna lord
    "wealth",        # 2H, 11H, dhana karaka
    "siblings",      # 3H
    "home",          # 4H
    "creativity",    # 5H
    "health",        # 6H
    "relationship",  # 7H
    "transformation", # 8H
    "dharma",        # 9H, 10H
)

# Houses each domain "owns" — the deterministic shared-factor map.
_DOMAIN_HOUSES: dict[str, tuple[int, ...]] = {
    "self":           (1,),
    "wealth":         (2, 11),
    "siblings":       (3,),
    "home":           (4,),
    "creativity":     (5,),
    "health":         (6,),
    "relationship":   (7,),
    "transformation": (8,),
    "dharma":         (9, 10),
}

# Karaka planets per domain (classical assignments — pure mapping, no LLM).
_DOMAIN_KARAKAS: dict[str, tuple[str, ...]] = {
    "self":           ("Sun",),
    "wealth":         ("Jupiter",),
    "siblings":       ("Mars",),
    "home":           ("Moon",),
    "creativity":     ("Jupiter",),
    "health":         ("Sun", "Mars"),
    "relationship":   ("Venus",),
    "transformation": ("Saturn",),
    "dharma":         ("Sun", "Jupiter", "Saturn"),
}

# ─── Helpers ─────────────────────────────────────────────────────────────────


def _sort_key(d: dict[str, Any], keys: list[str]) -> tuple:
    return tuple(d.get(k, "") for k in keys)


def canonical_jsonl(rows: list[dict[str, Any]], sort_keys: list[str]) -> str:
    """Serialize a list of rows to canonical JSONL (sorted, key-sorted JSON).

    `sort_keys` defines the deterministic row order. Within each row, JSON
    keys are sorted ascending. NaN/Inf are forbidden (json.dumps will raise).
    """
    sorted_rows = sorted(rows, key=lambda r: _sort_key(r, sort_keys))
    return "\n".join(
        json.dumps(r, sort_keys=True, ensure_ascii=False, allow_nan=False)
        for r in sorted_rows
    )


def compute_ucn_signature(payload: dict[str, Any]) -> str:
    """sha256 of the canonical-JSON payload. Stable across identical chart-states."""
    canon = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _provenance_dict(chart_output: dict[str, Any], source_section: str) -> dict[str, Any]:
    prov = chart_output.get("provenance", {})
    return {
        "attribution": "engine",
        "engine_version": prov.get("engine_version", ""),
        "ayanamsha_config_id": prov.get("ayanamsha_config_id", ""),
        "inputs_hash": prov.get("inputs_hash", ""),
        "source_section": source_section,
    }


def _ayanamsha_id(chart_output: dict[str, Any]) -> str:
    # Prefer the top-level `ayanamsha.id`; fall back to provenance.
    a = chart_output.get("ayanamsha", {}).get("id")
    if a:
        return a
    return chart_output.get("provenance", {}).get("ayanamsha_config_id", "")


def _engine_version(chart_output: dict[str, Any]) -> str:
    return chart_output.get("provenance", {}).get("engine_version", "")


def _ascendant_sign_id(chart_output: dict[str, Any]) -> int:
    return int(chart_output["ascendant"]["sign_id"])


def _house_of_sign(sign_id: int, asc_sign_id: int) -> int:
    """Whole-sign: house = ((sign_id - asc_sign_id) mod 12) + 1."""
    return ((sign_id - asc_sign_id) % 12) + 1


def _planet_house_map(chart_output: dict[str, Any]) -> dict[str, int]:
    asc = _ascendant_sign_id(chart_output)
    return {
        str(g["name"]): _house_of_sign(int(g["sign_id"]), asc)
        for g in chart_output.get("grahas", [])
    }


# ─── chart_facts (T1 structural facts) ───────────────────────────────────────


def build_chart_facts(
    chart_output: dict[str, Any], chart_id: str, build_id: str
) -> list[dict[str, Any]]:
    """T1 structural facts: planet / house / panchanga / ascendant / sensitive_point / dasha_balance.

    Returns row dicts keyed by `fact_id`. Each row carries
    (chart_id, ayanamsha_id, engine_version, computed_at_iso) for the
    composite uniqueness.
    """
    rows: list[dict[str, Any]] = []
    ayan = _ayanamsha_id(chart_output)
    ev = _engine_version(chart_output)
    cai = chart_output.get("provenance", {}).get("computed_at_iso", "")

    # Planet facts
    for g in chart_output.get("grahas", []):
        name = str(g["name"]).upper()
        for attr in ("longitude_deg", "sign", "sign_id", "nakshatra", "pada", "dignity_status", "retrograde"):
            if attr not in g:
                continue
            val = g[attr]
            fact = {
                "fact_id": f"PLN.{name}.{attr.upper()}",
                "category": "planet",
                "divisional_chart": "D1",
                "chart_id": chart_id,
                "ayanamsha_id": ayan,
                "engine_version": ev,
                "computed_at_iso": cai,
                "value_text": str(val) if isinstance(val, (str, bool)) else None,
                "value_number": float(val) if isinstance(val, (int, float)) and not isinstance(val, bool) else None,
                "value_json": None,
                "source_section": "engine/grahas",
                "build_id": build_id,
                "provenance": _provenance_dict(chart_output, "engine/grahas"),
            }
            rows.append(fact)

    # House facts
    asc_sign = _ascendant_sign_id(chart_output)
    for h in chart_output.get("houses", []):
        hn = int(h["house_num"])
        fact = {
            "fact_id": f"HSE.{hn:02d}.SIGN_ID",
            "category": "house",
            "divisional_chart": "D1",
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
            "computed_at_iso": cai,
            "value_text": str(h.get("sign", "")),
            "value_number": float(h["sign_id"]),
            "value_json": None,
            "source_section": "engine/houses",
            "build_id": build_id,
            "provenance": _provenance_dict(chart_output, "engine/houses"),
        }
        rows.append(fact)

    # Ascendant
    asc = chart_output["ascendant"]
    rows.append({
        "fact_id": "ASC.LAGNA",
        "category": "ascendant",
        "divisional_chart": "D1",
        "chart_id": chart_id,
        "ayanamsha_id": ayan,
        "engine_version": ev,
        "computed_at_iso": cai,
        "value_text": str(asc.get("sign", "")),
        "value_number": float(asc.get("longitude_deg", 0.0)),
        "value_json": {
            "sign_id": int(asc["sign_id"]),
            "nakshatra": asc.get("nakshatra"),
            "pada": int(asc.get("pada", 0)),
        },
        "source_section": "engine/ascendant",
        "build_id": build_id,
        "provenance": _provenance_dict(chart_output, "engine/ascendant"),
    })

    # Panchanga (5 anga)
    panch = chart_output.get("panchanga", {})
    for anga in ("tithi", "vara", "nakshatra", "yoga", "karana"):
        if anga not in panch:
            continue
        v = panch[anga]
        rows.append({
            "fact_id": f"PNG.{anga.upper()}",
            "category": "panchanga",
            "divisional_chart": "D1",
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
            "computed_at_iso": cai,
            "value_text": str(v) if not isinstance(v, dict) else None,
            "value_number": None,
            "value_json": v if isinstance(v, dict) else None,
            "source_section": "engine/panchanga",
            "build_id": build_id,
            "provenance": _provenance_dict(chart_output, "engine/panchanga"),
        })

    # Sensitive points (gulika, mandi, etc.)
    for sp_name, sp_val in (chart_output.get("sensitive_points") or {}).items():
        rows.append({
            "fact_id": f"SP.{sp_name.upper()}",
            "category": "sensitive_point",
            "divisional_chart": "D1",
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
            "computed_at_iso": cai,
            "value_text": str(sp_val) if not isinstance(sp_val, dict) else None,
            "value_number": None,
            "value_json": sp_val if isinstance(sp_val, dict) else None,
            "source_section": "engine/sensitive_points",
            "build_id": build_id,
            "provenance": _provenance_dict(chart_output, "engine/sensitive_points"),
        })

    # Dasha balance at birth (first MD from vimshottari sequence)
    dashas_obj = chart_output.get("dashas") or {}
    if isinstance(dashas_obj, dict):
        seq = dashas_obj.get("mahadasha_sequence") or []
    elif isinstance(dashas_obj, list):
        seq = dashas_obj
    else:
        seq = []
    if seq:
        first = seq[0]
        rows.append({
            "fact_id": "DSH.BALANCE_AT_BIRTH",
            "category": "dasha_balance",
            "divisional_chart": "D1",
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
            "computed_at_iso": cai,
            "value_text": str(first.get("lord", first.get("planet", ""))),
            "value_number": None,
            "value_json": first if isinstance(first, dict) else None,
            "source_section": "engine/dashas",
            "build_id": build_id,
            "provenance": _provenance_dict(chart_output, "engine/dashas"),
        })

    return rows


# ─── l25_msr_signals (3-column coefficient, no fused score) ──────────────────


def _msr_coefficient(graha: dict[str, Any], asc_sign_id: int) -> tuple[float, float, float]:
    """Decompose the MSR signal coefficient into THREE structural components.

    Returns (deterministic_strength, verification_certainty, computed_salience).
    All in [0, 1]. NO fused score; the three are independent.

    - deterministic_strength: how much classical-rulebook weight the placement
      carries (dignity_status drives this).
    - verification_certainty: how much the underlying numeric is verified by
      JH (we ship with a flat 0.95 — the engine output is JH-parity by G1).
    - computed_salience: structural salience — distance to kendra/trikona
      houses, retrograde state, sign-lord dignity proxy.
    """
    dig = str(graha.get("dignity_status", "unknown"))
    det_map = {
        "exalted": 1.0,
        "moolatrikona": 0.95,
        "own": 0.9,
        "friend": 0.7,
        "neutral": 0.5,
        "enemy": 0.3,
        "debilitated": 0.1,
        "unknown": 0.5,
    }
    det = det_map.get(dig, 0.5)

    # Engine-output is JH-parity at G1; we mark a high constant.
    vc = 0.95

    # Salience: kendra (1,4,7,10) = high, trikona (1,5,9) = high, dusthana
    # (6,8,12) = low. Retrograde adds a salience nudge.
    house = _house_of_sign(int(graha["sign_id"]), asc_sign_id)
    if house in (1, 4, 7, 10):
        base = 0.85
    elif house in (5, 9):
        base = 0.8
    elif house in (2, 3, 11):
        base = 0.55
    else:  # 6, 8, 12
        base = 0.35
    if graha.get("retrograde"):
        base = min(1.0, base + 0.05)
    return (round(det, 4), round(vc, 4), round(base, 4))


def build_l25_msr_signals(
    chart_output: dict[str, Any], chart_id: str, build_id: str
) -> list[dict[str, Any]]:
    """One structural MSR row per graha — the never-drop floor."""
    rows: list[dict[str, Any]] = []
    ayan = _ayanamsha_id(chart_output)
    ev = _engine_version(chart_output)
    asc_sign = _ascendant_sign_id(chart_output)

    # Stable ordering — by graha index in the engine output (which is itself
    # a deterministic Sun→Ketu order from positions.py).
    for idx, g in enumerate(chart_output.get("grahas", []), start=1):
        name = str(g["name"])
        det, vc, sal = _msr_coefficient(g, asc_sign)
        house = _house_of_sign(int(g["sign_id"]), asc_sign)
        sig_id = f"SIG.ENGINE.{name.upper()}.{int(g['sign_id']):02d}.H{house:02d}"
        rows.append({
            "signal_id": sig_id,
            "signal_number": idx,
            "name": f"{name} in {g.get('sign', '')} (H{house})",
            "category": "graha_placement",
            "valence": "structural",
            "weight": None,  # legacy fused-score column; kept NULL on engine rows
            "planets_involved": [name],
            "houses_involved": [house],
            "signs_involved": [str(g.get("sign", ""))],
            "description": (
                f"{name} occupies {g.get('sign','')} (sign_id={g['sign_id']}), "
                f"house {house}, nakshatra {g.get('nakshatra','')} pada {g.get('pada','')}, "
                f"dignity={g.get('dignity_status','unknown')}, "
                f"retrograde={bool(g.get('retrograde', False))}."
            ),
            "source_section": "engine/grahas",
            "build_id": build_id,
            "provenance": _provenance_dict(chart_output, "engine/grahas"),
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
            "deterministic_strength": det,
            "verification_certainty": vc,
            "computed_salience": sal,
        })
    return rows


# ─── l25_cdlm_links (shared-factor graph) ────────────────────────────────────


def _shared_factors_for_pair(
    a: str, b: str, planet_house: dict[str, int], asc_sign_id: int
) -> dict[str, Any]:
    """Compute shared planets/houses/signs for domain pair (a, b)."""
    a_houses = set(_DOMAIN_HOUSES[a])
    b_houses = set(_DOMAIN_HOUSES[b])
    shared_houses = sorted(a_houses & b_houses)

    a_karakas = set(_DOMAIN_KARAKAS[a])
    b_karakas = set(_DOMAIN_KARAKAS[b])
    shared_karakas = sorted(a_karakas & b_karakas)

    # Planets actually occupying both domains' houses in this chart.
    planets_a = {p for p, h in planet_house.items() if h in a_houses}
    planets_b = {p for p, h in planet_house.items() if h in b_houses}
    shared_planets_in_chart = sorted(planets_a & planets_b)

    # Union: karakas + chart-occupants
    all_shared_planets = sorted(set(shared_karakas) | set(shared_planets_in_chart))

    # Shared signs: signs that hold the houses for both domains.
    a_signs = sorted({((h - 1 + asc_sign_id - 1) % 12) + 1 for h in a_houses})
    b_signs = sorted({((h - 1 + asc_sign_id - 1) % 12) + 1 for h in b_houses})
    shared_sign_ids = sorted(set(a_signs) & set(b_signs))

    return {
        "shared_planets": all_shared_planets,
        "shared_houses": shared_houses,
        "shared_signs": [str(s) for s in shared_sign_ids],  # store as TEXT[]
        "shared_factor_count": (
            len(all_shared_planets) + len(shared_houses) + len(shared_sign_ids)
        ),
    }


def build_l25_cdlm_links(
    chart_output: dict[str, Any], chart_id: str, build_id: str
) -> list[dict[str, Any]]:
    """Deterministic CDLM shared-factor graph.

    A link is emitted for every unordered pair (a, b) where a != b and at
    least one structural factor is shared.
    """
    rows: list[dict[str, Any]] = []
    ayan = _ayanamsha_id(chart_output)
    ev = _engine_version(chart_output)
    asc_sign = _ascendant_sign_id(chart_output)
    planet_house = _planet_house_map(chart_output)

    domains = list(_DOMAINS)
    for i in range(len(domains)):
        for j in range(len(domains)):
            if i == j:
                continue
            a, b = domains[i], domains[j]
            sf = _shared_factors_for_pair(a, b, planet_house, asc_sign)
            if sf["shared_factor_count"] == 0:
                continue
            # Strength tier — pure structural, no model judgment.
            sfc = sf["shared_factor_count"]
            if sfc >= 4:
                strength = "strong"
            elif sfc >= 2:
                strength = "moderate"
            else:
                strength = "weak"
            link_id = f"CDLM.{a}.{b}.{ayan}"
            rows.append({
                "link_id": link_id,
                "from_domain": a,
                "to_domain": b,
                "link_type": "shared_factor",
                "strength": strength,
                "source_signals": [],
                "notes": (
                    f"shared planets={sf['shared_planets']}, "
                    f"shared houses={sf['shared_houses']}, "
                    f"shared signs={sf['shared_signs']}"
                ),
                "source_section": "engine/cdlm/shared_factor",
                "build_id": build_id,
                "chart_id": chart_id,
                "ayanamsha_id": ayan,
                "engine_version": ev,
                "shared_planets": sf["shared_planets"],
                "shared_houses": sf["shared_houses"],
                "shared_signs": sf["shared_signs"],
                "shared_factor_count": sf["shared_factor_count"],
            })
    return rows


# ─── l25_cgm_nodes + l25_cgm_edges (structural graph) ────────────────────────


def build_l25_cgm_nodes(
    chart_output: dict[str, Any], chart_id: str, build_id: str
) -> list[dict[str, Any]]:
    """One node per graha + one node per house. Stable IDs."""
    rows: list[dict[str, Any]] = []
    ayan = _ayanamsha_id(chart_output)
    ev = _engine_version(chart_output)
    asc_sign = _ascendant_sign_id(chart_output)

    for g in chart_output.get("grahas", []):
        name = str(g["name"]).upper()
        rows.append({
            "node_id": f"CGM.GRAHA.{name}",
            "node_type": "graha",
            "display_name": str(g["name"]),
            "properties": {
                "longitude_deg": float(g["longitude_deg"]),
                "sign_id": int(g["sign_id"]),
                "sign": g.get("sign"),
                "house": _house_of_sign(int(g["sign_id"]), asc_sign),
                "nakshatra": g.get("nakshatra"),
                "pada": int(g.get("pada", 0)),
                "dignity_status": g.get("dignity_status"),
                "retrograde": bool(g.get("retrograde", False)),
            },
            "source_section": "engine/cgm/graha",
            "build_id": build_id,
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
        })

    for h in chart_output.get("houses", []):
        hn = int(h["house_num"])
        rows.append({
            "node_id": f"CGM.HOUSE.{hn:02d}",
            "node_type": "house",
            "display_name": f"House {hn}",
            "properties": {
                "house_num": hn,
                "sign": h.get("sign"),
                "sign_id": int(h["sign_id"]),
                "cusp_deg": float(h.get("cusp_deg", 0.0)),
            },
            "source_section": "engine/cgm/house",
            "build_id": build_id,
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
        })

    return rows


# Classical lordship per sign_id (1=Aries → Mars, ... 12=Pisces → Jupiter)
_SIGN_LORD: dict[int, str] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


def build_l25_cgm_edges(
    chart_output: dict[str, Any], chart_id: str, build_id: str
) -> list[dict[str, Any]]:
    """Lordship + occupancy edges. Structural, deterministic."""
    rows: list[dict[str, Any]] = []
    ayan = _ayanamsha_id(chart_output)
    ev = _engine_version(chart_output)
    asc_sign = _ascendant_sign_id(chart_output)

    # Lordship edges: each house has a sign-lord graha → graha-rules-house edge.
    for h in chart_output.get("houses", []):
        hn = int(h["house_num"])
        lord = _SIGN_LORD[int(h["sign_id"])]
        rows.append({
            "edge_id": f"CGM.E.RULES.{lord.upper()}.H{hn:02d}",
            "source_node_id": f"CGM.GRAHA.{lord.upper()}",
            "target_node_id": f"CGM.HOUSE.{hn:02d}",
            "edge_type": "rules",
            "strength": 1.0,
            "notes": f"{lord} rules sign {h.get('sign')} which holds house {hn}",
            "source_section": "engine/cgm/lordship",
            "build_id": build_id,
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
        })

    # Occupancy edges: each graha occupies one house.
    for g in chart_output.get("grahas", []):
        name = str(g["name"]).upper()
        house = _house_of_sign(int(g["sign_id"]), asc_sign)
        rows.append({
            "edge_id": f"CGM.E.OCCUPIES.{name}.H{house:02d}",
            "source_node_id": f"CGM.GRAHA.{name}",
            "target_node_id": f"CGM.HOUSE.{house:02d}",
            "edge_type": "occupies",
            "strength": 1.0,
            "notes": f"{g['name']} occupies house {house} ({g.get('sign')})",
            "source_section": "engine/cgm/occupancy",
            "build_id": build_id,
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
        })

    return rows


# ─── l25_rm_resonances (remedy lookup keys) ──────────────────────────────────


def build_l25_rm_resonances(
    chart_output: dict[str, Any], chart_id: str, build_id: str
) -> list[dict[str, Any]]:
    """Emit structural-condition rows that the RM corpus can join against.

    Each row is a structural condition the chart exhibits — e.g.
    'debilitated:Saturn:Aries:H4'. The corpus side resolves the
    remedy/mantra prescription. We do NOT invent prescriptions here.
    """
    rows: list[dict[str, Any]] = []
    ayan = _ayanamsha_id(chart_output)
    ev = _engine_version(chart_output)
    asc_sign = _ascendant_sign_id(chart_output)

    for g in chart_output.get("grahas", []):
        dig = str(g.get("dignity_status", "unknown"))
        # Only emit rows for structurally-noteworthy dignities (the never-drop
        # never floors RM, so this is permitted to be sparse).
        if dig not in ("exalted", "debilitated", "moolatrikona"):
            continue
        name = str(g["name"]).upper()
        sign = str(g.get("sign", ""))
        house = _house_of_sign(int(g["sign_id"]), asc_sign)
        cond = f"{dig}:{name}:{sign}:H{house}"
        resonance_id = f"RM.RES.{cond}.{ayan}"
        rows.append({
            "resonance_id": resonance_id,
            "signal_a_id": f"CGM.GRAHA.{name}",
            "signal_b_id": f"CGM.HOUSE.{house:02d}",
            "resonance_type": "dignity_resonance",
            "strength": "structural",
            "theme": dig,
            "notes": f"{name} {dig} in {sign} (H{house})",
            "source_section": "engine/rm/dignity",
            "build_id": build_id,
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
            "structural_condition": cond,
        })
    return rows


# ─── l25_ucn_sections (computed-signature digest) ────────────────────────────


def build_l25_ucn_sections(
    chart_output: dict[str, Any], chart_id: str, build_id: str
) -> list[dict[str, Any]]:
    """A single signature row per (chart_id, ayanamsha) for now — the
    structural payload hashes the full deterministic state of the chart.

    Future extensions add domain-scoped signatures, but the never-drop floor
    requires at least one row per chart.
    """
    ayan = _ayanamsha_id(chart_output)
    ev = _engine_version(chart_output)
    asc_sign = _ascendant_sign_id(chart_output)

    # Build a STRUCTURAL payload — exclude provenance.computed_at_iso so the
    # digest is stable across runs.
    structural_payload = {
        "ascendant": {
            "sign_id": int(chart_output["ascendant"]["sign_id"]),
            "longitude_deg": float(chart_output["ascendant"]["longitude_deg"]),
            "nakshatra": chart_output["ascendant"].get("nakshatra"),
            "pada": int(chart_output["ascendant"].get("pada", 0)),
        },
        "grahas": [
            {
                "name": g["name"],
                "sign_id": int(g["sign_id"]),
                "longitude_deg": float(g["longitude_deg"]),
                "nakshatra": g.get("nakshatra"),
                "pada": int(g.get("pada", 0)),
                "dignity_status": g.get("dignity_status"),
                "retrograde": bool(g.get("retrograde", False)),
                "house": _house_of_sign(int(g["sign_id"]), asc_sign),
            }
            for g in chart_output.get("grahas", [])
        ],
        "houses": [
            {"house_num": int(h["house_num"]), "sign_id": int(h["sign_id"])}
            for h in chart_output.get("houses", [])
        ],
        "ayanamsha_id": ayan,
    }
    digest = compute_ucn_signature(structural_payload)
    section_id = f"UCN.SIG.{chart_id}.{ayan}"
    return [
        {
            "section_id": section_id,
            "parent_section_id": None,
            "domain": "structural",
            "title": "Computed-signature digest",
            "content": f"sha256 over structural state; digest={digest}",
            "derived_from_signals": [],
            "source_lines": "engine/ucn/computed_signature",
            "build_id": build_id,
            "chart_id": chart_id,
            "ayanamsha_id": ayan,
            "engine_version": ev,
            "computed_signature": digest,
            "signature_payload": structural_payload,
        }
    ]


# ─── all-in-one ──────────────────────────────────────────────────────────────


def build_all(
    chart_output: dict[str, Any], chart_id: str, build_id: str
) -> dict[str, list[dict[str, Any]]]:
    """Return a dict mapping table name → list of row dicts.

    The loader iterates this dict and INSERTs each table's rows into its
    `_staging` mirror, then runs the atomic swap.
    """
    return {
        "chart_facts":         build_chart_facts(chart_output, chart_id, build_id),
        "l25_msr_signals":     build_l25_msr_signals(chart_output, chart_id, build_id),
        "l25_cdlm_links":      build_l25_cdlm_links(chart_output, chart_id, build_id),
        "l25_cgm_nodes":       build_l25_cgm_nodes(chart_output, chart_id, build_id),
        "l25_cgm_edges":       build_l25_cgm_edges(chart_output, chart_id, build_id),
        "l25_rm_resonances":   build_l25_rm_resonances(chart_output, chart_id, build_id),
        "l25_ucn_sections":    build_l25_ucn_sections(chart_output, chart_id, build_id),
    }
