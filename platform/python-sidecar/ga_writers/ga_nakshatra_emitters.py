"""
ga_writers.ga_nakshatra_emitters — Build chart_facts rows for ga_nakshatra.

All functions return list[dict] — rows ready for INSERT into chart_facts.
No DB access here. Takes chart_output from pyjhora_adapter and JOIN data
from reference_nakshatra / reference_nakshatra_pada.

bg_nakshatra is AUTHORITY for static attrs: rows cite nakshatra_id as
source_calculation — they do not recompute static values, they relay them
with provenance so the chain is auditable.
"""
from __future__ import annotations
import json
from typing import Any

from brahmagyan.graha_vocabulary import norm_graha
from ga_writers.ga_nakshatra_compute import (
    compute_kp_lords, compute_gandanta, compute_tara,
    compute_dispositor_chain, compute_center_of_gravity,
    PLANET_CYCLE, TARA_NAMES,
)

# Values sourced from the graha SSoT (brahmagyan/graha_vocabulary) rather
# than hardcoded literals — ADHIṢṬHĀNA Lane A2.
PLANET_TO_SUBJECT: dict[str, str] = {
    name: norm_graha(name)
    for name in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
        "Rahu", "Ketu", "Lagna",
    )
}


def _row(chart_id: str, ayanamsha_id: str, build_id: str,
         fact_category: str, fact_subject: str, fact_key: str,
         value_text: str | None = None, value_num: float | None = None,
         source: str = "ga_nakshatra") -> dict:
    return {
        "chart_id":       chart_id,
        "ayanamsha_id":   ayanamsha_id,
        "build_id":       build_id,
        "fact_category":  fact_category,
        "fact_subject":   fact_subject,
        "fact_key":       fact_key,
        "fact_value_text": value_text,
        "fact_value_num":  value_num,
        "source_calculation": source,
    }


def emit_nakshatra_join(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
    nak_rows: dict[int, dict],     # nakshatra_id → reference_nakshatra row
    pada_rows: dict[tuple, dict],  # (nakshatra_id, pada_number) → reference_nakshatra_pada row
) -> list[dict]:
    """
    Per-body nakshatra attribute JOIN from reference_nakshatra + reference_nakshatra_pada.
    Emits graha_nakshatra_join and graha_pada_join rows.
    source_calculation cites the reference_nakshatra row so the chain is auditable.
    """
    rows: list[dict] = []
    grahas = chart_output.get("grahas", [])
    asc    = chart_output.get("ascendant", {})

    bodies_data = grahas + [{"name": "Lagna", **asc}]

    for body_data in bodies_data:
        bname  = body_data.get("name", "")
        subj   = PLANET_TO_SUBJECT.get(bname)
        if not subj:
            continue
        nak_id = body_data.get("nakshatra_id")
        pada   = body_data.get("pada")
        if not nak_id:
            continue

        nak_ref = nak_rows.get(nak_id, {})
        source  = f"ga_nakshatra:JOIN reference_nakshatra:nakshatra_id={nak_id}"
        cat1    = "graha_nakshatra_join"

        STATIC_KEYS = [
            ("gana",            "gana"),
            ("nadi",            "nadi"),
            ("yoni_en",         "yoni_en"),
            ("yoni_sex",        "yoni_sex"),
            ("varna",           "varna"),
            ("tatva",           "tatva"),
            ("guna",            "guna"),
            ("pakshi",          "pakshi"),
            ("presiding_deity", "presiding_deity"),
            ("shakti",          "shakti"),
            ("motivation",      "motivation"),
            ("symbol",          "symbol"),
            ("vimshottari_lord","nakshatra_lord"),
        ]
        for db_col, fact_key in STATIC_KEYS:
            val = nak_ref.get(db_col)
            if val is not None:
                rows.append(_row(chart_id, ayanamsha_id, build_id, cat1, subj, fact_key,
                                 value_text=str(val), source=source))

        # Always emit nakshatra_id reference
        rows.append(_row(chart_id, ayanamsha_id, build_id, cat1, subj, "nakshatra_id_ref",
                         value_num=float(nak_id), source=source))

        # Pada join
        if pada:
            pada_ref  = pada_rows.get((nak_id, pada), {})
            pada_src  = f"ga_nakshatra:JOIN reference_nakshatra_pada:nakshatra_id={nak_id}:pada={pada}"
            cat2      = "graha_pada_join"
            PADA_KEYS = [
                ("pada_akshara",      "akshara"),
                ("pada_navamsa_sign", "navamsa_sign"),
                ("pada_lord",         "pada_lord"),
            ]
            for db_col, fact_key in PADA_KEYS:
                val = pada_ref.get(db_col)
                if val is not None:
                    rows.append(_row(chart_id, ayanamsha_id, build_id, cat2, subj, fact_key,
                                     value_text=str(val), source=pada_src))
            rows.append(_row(chart_id, ayanamsha_id, build_id, cat2, subj, "pada_number_ref",
                             value_num=float(pada), source=pada_src))

    return rows


def emit_kp_lords(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
) -> list[dict]:
    """
    KP sub-lords per body AND per house cusp.
    Fact categories: graha_kp_lords, cusp_kp_lords.
    """
    rows: list[dict] = []
    asc    = chart_output.get("ascendant", {})
    grahas = chart_output.get("grahas", [])

    # Per-body
    bodies_data = grahas + [{"name": "Lagna", **asc}]
    for body_data in bodies_data:
        bname = body_data.get("name", "")
        subj  = PLANET_TO_SUBJECT.get(bname)
        if not subj:
            continue
        long = body_data.get("longitude_deg")
        if long is None:
            continue
        kp = compute_kp_lords(float(long))
        src = f"ga_nakshatra:KP:longitude={long:.4f}"
        for key, val in kp.items():
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_kp_lords", subj, key,
                             value_text=val, source=src))

    # Per cusp: REAL Placidus cusp longitudes (KP == Placidus). The prior
    # `(asc_sign0 + h) % 12 * 30` equal-house/sign-boundary cusps were FAKE precision
    # (B.10) and are removed. Real boundaries come from compute_bhava_chalit
    # (drik.bhaava_madhya_swe house_code='P'); cusp[h] = KP cusp of house h+1.
    placidus_bounds = (
        ((chart_output.get("bhava_chalit") or {}).get("placidus") or {}).get("cusp_boundaries")
    )
    if placidus_bounds and len(placidus_bounds) >= 12:
        for h in range(12):
            cusp_long = float(placidus_bounds[h]) % 360.0
            cusp_subj = f"CUSP_{h+1:02d}"
            kp = compute_kp_lords(cusp_long)  # real 249-division sub-lord chain
            src = f"ga_nakshatra:KP:cusp={h+1}:placidus_longitude={cusp_long:.4f}"
            for key, val in kp.items():
                rows.append(_row(chart_id, ayanamsha_id, build_id, "cusp_kp_lords", cusp_subj, key,
                                 value_text=val, source=src))
    else:
        # No fabricated fallback (B.10): emit a visible EXTERNAL_COMPUTATION_REQUIRED
        # marker rather than fake equal-house cusps.
        for h in range(12):
            cusp_subj = f"CUSP_{h+1:02d}"
            rows.append(_row(chart_id, ayanamsha_id, build_id, "cusp_kp_lords", cusp_subj,
                             "sub_lord",
                             value_text="[EXTERNAL_COMPUTATION_REQUIRED] real Placidus cusp "
                                        "unavailable (bhava_chalit absent)",
                             source="ga_nakshatra:KP:cusp:external_required"))

    return rows


def emit_gandanta_flags(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
) -> list[dict]:
    """Gaṇḍānta + degree flags (gandanta severity, vargottama-via-pada)."""
    rows: list[dict] = []
    asc    = chart_output.get("ascendant", {})
    grahas = chart_output.get("grahas", [])

    bodies_data = grahas + [{"name": "Lagna", **asc}]
    for body_data in bodies_data:
        bname = body_data.get("name", "")
        subj  = PLANET_TO_SUBJECT.get(bname)
        if not subj:
            continue
        long = body_data.get("longitude_deg")
        if long is None:
            continue

        g = compute_gandanta(float(long))
        src = f"ga_nakshatra:gandanta:longitude={long:.4f}"
        rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_gandanta", subj, "is_gandanta",
                         value_text=str(g["is_gandanta"]).lower(), source=src))
        if g["is_gandanta"]:
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_gandanta", subj,
                             "arc_minutes_from_junction",
                             value_num=g["arc_minutes_from_junction"], source=src))
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_gandanta", subj,
                             "junction_type", value_text=g["junction_type"], source=src))
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_gandanta", subj,
                             "side", value_text=g["side"], source=src))

        # Vargottama-via-pada: pada navamsa sign == D1 sign
        pada_nav = body_data.get("pada_navamsa_sign")
        d1_sign  = body_data.get("sign")
        if pada_nav and d1_sign:
            is_varg = (pada_nav == d1_sign)
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_degree_flags", subj,
                             "vargottama_via_pada", value_text=str(is_varg).lower(),
                             source="ga_nakshatra:vargottama_pada"))

    return rows


def emit_dispositor_graph(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
    body_nak_lord: dict[str, str],  # body_name → its nakshatra lord's body_name
) -> list[dict]:
    """
    Nakshatra dispositor graph: chains, exchanges, conjunctions, center-of-gravity.
    """
    rows: list[dict] = []

    # Build chains for all bodies
    all_chains: dict[str, dict] = {}
    for body in PLANET_TO_SUBJECT:
        chain = compute_dispositor_chain(body, body_nak_lord)
        all_chains[body] = chain
        subj = PLANET_TO_SUBJECT[body]
        src  = "ga_nakshatra:dispositor_graph"
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_dispositor", subj,
                         "lord_chain", value_text=json.dumps(chain["chain"]), source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_dispositor", subj,
                         "terminus_body", value_text=chain["terminus"], source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_dispositor", subj,
                         "is_cycle", value_text=str(chain["is_cycle"]).lower(), source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_dispositor", subj,
                         "chain_depth", value_num=float(chain["chain_depth"]), source=src))

    # Center of gravity
    cog = compute_center_of_gravity(all_chains)
    rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_cogravity", "CHART",
                     "terminus_body", value_text=cog["terminus_body"],
                     source="ga_nakshatra:cogravity"))
    rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_cogravity", "CHART",
                     "chain_count", value_num=float(cog["chain_count"]),
                     source="ga_nakshatra:cogravity"))

    # Nakshatra exchanges: body A in lord of body B's nakshatra AND vice versa
    bodies = list(PLANET_TO_SUBJECT.keys())
    exchange_idx = 0
    for i, ba in enumerate(bodies):
        for bb in bodies[i+1:]:
            la, lb = body_nak_lord.get(ba), body_nak_lord.get(bb)
            if la == bb and lb == ba:
                subj = f"EXCHANGE_{exchange_idx}"
                rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_exchange", subj,
                                 "body_a", value_text=ba, source="ga_nakshatra:exchange"))
                rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_exchange", subj,
                                 "body_b", value_text=bb, source="ga_nakshatra:exchange"))
                exchange_idx += 1

    # Nakshatra conjunctions: bodies sharing a nakshatra
    body_nak_map: dict[str, list[str]] = {}
    grahas = chart_output.get("grahas", []) + [{"name": "Lagna", **chart_output.get("ascendant", {})}]
    for gd in grahas:
        bname = gd.get("name", "")
        if bname not in PLANET_TO_SUBJECT:
            continue
        nak = gd.get("nakshatra") or ""
        if nak:
            body_nak_map.setdefault(nak, []).append(bname)

    for nak_name, conjunction_bodies in body_nak_map.items():
        if len(conjunction_bodies) >= 2:
            rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_conjunction", nak_name,
                             "bodies_list", value_text=json.dumps(conjunction_bodies),
                             source="ga_nakshatra:conjunction"))

    return rows


def emit_tara_bala(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
) -> list[dict]:
    """Tara bala per body from Moon's nakshatra."""
    rows: list[dict] = []
    grahas = chart_output.get("grahas", [])
    moon_data = next((g for g in grahas if g.get("name") == "Moon"), None)
    if not moon_data:
        return rows

    moon_nak = moon_data.get("nakshatra_id") or 0
    asc      = chart_output.get("ascendant", {})
    bodies   = grahas + [{"name": "Lagna", **asc}]

    for body_data in bodies:
        bname = body_data.get("name", "")
        subj  = PLANET_TO_SUBJECT.get(bname)
        if not subj:
            continue
        nak = body_data.get("nakshatra_id") or 0
        if not nak:
            continue
        t = compute_tara(nak, moon_nak)
        src = f"ga_nakshatra:tara:moon_nak={moon_nak}:body_nak={nak}"
        rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_tara_bala", subj,
                         "tara_count", value_num=float(t["tara_count"]), source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_tara_bala", subj,
                         "tara_position", value_num=float(t["tara_position"]), source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_tara_bala", subj,
                         "tara_name", value_text=t["tara_name"], source=src))

    return rows


def emit_statistics(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
    nak_rows: dict[int, dict],
) -> list[dict]:
    """Per-chart nakshatra statistics (gana/nadi/yoni/tatva distributions)."""
    rows: list[dict] = []
    grahas = chart_output.get("grahas", []) + [{"name": "Lagna", **chart_output.get("ascendant", {})}]

    gana_counts:  dict[str, int] = {}
    nadi_counts:  dict[str, int] = {}
    yoni_counts:  dict[str, int] = {}
    tatva_counts: dict[str, int] = {}

    for body_data in grahas:
        bname = body_data.get("name", "")
        if bname not in PLANET_TO_SUBJECT:
            continue
        nak_id  = body_data.get("nakshatra_id")
        nak_ref = nak_rows.get(nak_id, {}) if nak_id else {}
        for attr, counter in [
            ("gana",  gana_counts),
            ("nadi",  nadi_counts),
            ("yoni_en", yoni_counts),
            ("tatva", tatva_counts),
        ]:
            val = nak_ref.get(attr)
            if val:
                counter[val] = counter.get(val, 0) + 1

    src = "ga_nakshatra:statistics"
    for gana, cnt in gana_counts.items():
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_statistics", "CHART",
                         f"gana_{gana.lower()}_count", value_num=float(cnt), source=src))

    for nadi, cnt in nadi_counts.items():
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_statistics", "CHART",
                         f"nadi_{nadi.lower()}_count", value_num=float(cnt), source=src))

    if gana_counts:
        dominant = max(gana_counts, key=gana_counts.get)
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_statistics", "CHART",
                         "dominant_gana", value_text=dominant, source=src))

    # Nadi affliction: all bodies in same nadi
    if len(nadi_counts) == 1:
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_statistics", "CHART",
                         "nadi_affliction", value_text="true", source=src))

    return rows
