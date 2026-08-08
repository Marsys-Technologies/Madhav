"""
ga_strength_writer.py — GA3 ga_strength writer
================================================
Writes shadbala, ashtakavarga, and bhava_bala to `chart_facts`.

Per GA3 brief §6.2 + A3 §3:
  - Shadbala: 7 rows per graha (7 classical grahas) = 49 rows × 5 ayanamshas
  - Ashtakavarga: 12 bindus per graha (7+1 sarva) × 12 houses = 96 rows × 5 ayanamshas
    plus pinda_sodhita/bhinna/sarva per graha = 8×3 = 24 rows × 5 ayanamshas
  - Bhava bala: subscores + total per 12 houses

Pass 1: real PyJHora computation (jhora.horoscope.chart.strength.shad_bala,
jhora.horoscope.chart.charts.vimsopaka_*_of_planets, jhora.horoscope.chart.
ashtakavarga.get_ashtaka_varga/sodhaya_pindas — see pyjhora_adapter/strength.py).
Pass 2: sanity checks on that real output (NOT a second independent
recomputation — PyJHora IS the computation; these are bounds/consistency
guards, not a "verification" claim of independent provenance):
  - Shadbala: magnitude sub-balas (sthana/dig/kala/cheshta/naisargika) >= 0;
    drik bala MAY be signed (net malefic aspect can drive it negative per
    BPHS Ch.26 — this is classically correct); total > 0; sum(sub-balas) ==
    total within tolerance (catches rounding drift / key-set mismatches).
  - Ashtakavarga: sarvashtakavarga = sum of 7 graha bindus per house; sum of
    all sarva bindus = 337 (classical Parashara constant, verified directly
    from PyJHora's const.ashtaka_varga_dict-driven binna computation).

On divergence > tolerance: mark 'divergent_flagged', write CONDUCTOR_HALT_LOG, halt.

FORENSIC gate is inherited from ga_positions (positions must pass first).
For strength, FORENSIC is re-checked on the position subset to verify engine state.

R6 1a-strength fix (M-1/M-2/M-3, see 00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER):
  Shadbala, Vimshopaka Bala, and Ashtakavarga shodhana are now delegated to
  PyJHora's real classical implementations via pyjhora_adapter/strength.py —
  they are NO LONGER hand-rolled heuristics. Rahu/Ketu have no classical
  shadbala under strict Parashara tradition; their sthana (positional dignity)
  and drik (aspects received) are computed as a labeled `computed_extension`
  from the same PyJHora-verified D1 positions (dig/kala/cheshta/naisargika are
  0.0/not_defined_for_nodes for nodes, per tradition).
"""
from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any

from pyjhora_adapter.compute import compute_chart
from pyjhora_adapter import strength as pyjhora_strength
from pyjhora_adapter._names import SIGN_NAMES
from pyjhora_adapter.version import ENGINE_VERSION
from ga_writers._idempotency import replace_prior_chart_facts
from ga_writers._telemetry import update_asset_throughput
from pipeline.orchestrator.birth_params import resolve_birth_params
from ga_writers.ga_positions_writer import (
    CANONICAL_AYANAMSHAS,
    CANONICAL_CHART_ID,
    PLANET_TO_SUBJECT,
    FORBIDDEN_PATTERNS,
    forensic_gate,
    _conn,
    _write_halt_log,
)
from brahmagyan.graha_vocabulary import norm_graha, to_title

logger = logging.getLogger(__name__)

# ── Naisargika bala (fixed classical constants, A3 §3) ───────────────────────
# Source: Brihat Parashara Hora Shastra — fixed irrespective of chart/ayanamsha.
NAISARGIKA_BALA: dict[str, float] = {
    "Sun": 0.600,
    "Moon": 0.519,
    "Jupiter": 0.514,
    "Venus": 0.505,
    "Mercury": 0.500,
    "Saturn": 0.486,
    "Mars": 0.481,
}

# ── Kakṣyā (sub-division) boundaries — fixed classical constants ──────────────
# Each rāśi (30°) is divided into 8 kakṣyās of 3°45′ (3.75°) each, ruled in the
# ascending order Saturn → Jupiter → Mars → Sun → Venus → Mercury → Moon →
# Lagna (kakṣyā 1 = 0°–3°45′ ruled by Saturn ... kakṣyā 8 = 26°15′–30° ruled by
# Lagna). Used for kakṣyā (sub-lord) gochara Aṣṭakavarga transit reading. The
# boundaries are chart-independent (identical across all 12 signs); stored per
# chart×ayanamsha to keep the L1 fact contract uniform. Source: classical
# Aṣṭakavarga Kakṣyā-vibhāga (BPHS Aṣṭakavarga Prakaraṇa / Gochara tradition).
KAKSHYA_LORDS: list[str] = [
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Lagna",
]
KAKSHYA_ARC_DEG: float = 30.0 / 8.0  # 3.75° = 3°45′

# Classical required shadbala (rupa) per graha
SHADBALA_REQUIRED: dict[str, float] = {
    "Sun": 5.0,
    "Moon": 6.0,
    "Mars": 5.0,
    "Mercury": 7.0,
    "Jupiter": 6.5,
    "Venus": 5.5,
    "Saturn": 5.0,
}

# Ashtakavarga invariant: sum of sarvashtakavarga across all 12 houses = 337
SARVA_BINDU_TOTAL = 337


# ── Amendment 1: Divisional planet name mapping ──────────────────────────────
# Maps uppercase planet codes from chart_divisionals.graha to the title-case
# names used by BENEFIC_HOUSES in _derive_ashtakavarga.
# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2 (found via the full-tree census; not one of the originally-
# enumerated retirement targets). "ASC" is a documented extra Ascendant
# storage-name alias the SSoT itself does not carry.
_DIVISIONAL_TO_BENEFIC: dict[str, str] = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "LAGNA")
}
_DIVISIONAL_TO_BENEFIC["ASC"] = "Lagna"


# ── fact_id + citations ──────────────────────────────────────────────────────

def _fact_id(category: str, subject: str, key: str, chart_id: str,
              ayanamsha_id: str, build_id: str) -> str:
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _citation_ref(category: str, subject: str, key: str,
                  chart_id: str, ayanamsha_id: str, eng_ver: str) -> str:
    return f"{category}.{subject}.{key}@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}"


def _citation_human_strength(category: str, subject: str, key: str,
                               value_num: float, ayanamsha_id: str) -> str:
    graha = subject.replace("RAH_MEAN", "Rahu").replace("KET_MEAN", "Ketu")
    house_num = None
    if "-HOUSE_" in subject:
        parts = subject.split("-HOUSE_")
        graha = parts[0].capitalize()
        house_num = parts[1]

    ay = ayanamsha_id.replace("_", " ").title()
    if category == "graha_shadbala_sthana":
        return f"{graha} sthana bala: {value_num:.4f} rupa ({ay})."
    if category == "graha_shadbala_dig":
        return f"{graha} dig bala: {value_num:.4f} rupa ({ay})."
    if category == "graha_shadbala_kala":
        return f"{graha} kala bala: {value_num:.4f} rupa ({ay})."
    if category == "graha_shadbala_cheshta":
        return f"{graha} cheshta bala: {value_num:.4f} rupa ({ay})."
    if category == "graha_shadbala_naisargika":
        return f"{graha} naisargika bala: {value_num:.4f} rupa (ayanamsha-invariant classical)."
    if category == "graha_shadbala_drik":
        return f"{graha} drik bala: {value_num:.4f} rupa ({ay})."
    if category == "graha_shadbala_total":
        req = SHADBALA_REQUIRED.get(graha, 5.0)
        surplus = value_num - req
        direction = "surplus" if surplus >= 0 else "deficit"
        return (f"{graha} total shadbala: {value_num:.4f} rupa "
                f"({direction} {abs(surplus):.2f} vs required {req:.2f} rupa) ({ay}).")
    if category == "graha_ishta_phala":
        return f"{graha} ishta phala: {value_num:.4f} ({ay})."
    if category == "graha_kashta_phala":
        return f"{graha} kashta phala: {value_num:.4f} ({ay})."
    if category.startswith("graha_vimsopaka"):
        vtype = category.replace("graha_vimsopaka_", "").replace("_", "/")
        return f"{graha} vimsopaka ({vtype}): {value_num:.4f}/20 ({ay})."
    if category == "ashtakavarga_bindu" and house_num:
        return f"{graha} ashtakavarga house {house_num}: {int(value_num)} bindu ({ay})."
    if category == "ashtakavarga_bindu_sign" and "-SIGN_" in subject:
        gp, sn = subject.split("-SIGN_")
        sign_name = SIGN_NAMES[int(sn) - 1] if sn.isdigit() and 1 <= int(sn) <= 12 else sn
        return f"{gp.capitalize()} ashtakavarga (sign-keyed) {sign_name}: {int(value_num)} bindu ({ay})."
    if category == "ashtakavarga_trikona_shodhana" and "-SIGN_" in subject:
        gp, sn = subject.split("-SIGN_")
        sign_name = SIGN_NAMES[int(sn) - 1] if sn.isdigit() and 1 <= int(sn) <= 12 else sn
        return f"{gp.capitalize()} trikona-shodhita bindu {sign_name}: {int(value_num)} ({ay})."
    if category == "ashtakavarga_ekadhipathya_shodhana" and "-SIGN_" in subject:
        gp, sn = subject.split("-SIGN_")
        sign_name = SIGN_NAMES[int(sn) - 1] if sn.isdigit() and 1 <= int(sn) <= 12 else sn
        return f"{gp.capitalize()} ekadhipathya-shodhita bindu {sign_name}: {int(value_num)} ({ay})."
    if category == "ashtakavarga_pinda_sodhita":
        return f"{graha} pinda sodhita (trikona shodhana): {int(value_num)} ({ay})."
    if category == "ashtakavarga_pinda_bhinna":
        return f"{graha} pinda bhinna (ekadhipathya shodhana): {int(value_num)} ({ay})."
    if category == "ashtakavarga_pinda_raasi":
        return f"{graha} raasi pinda: {int(value_num)} ({ay})."
    if category == "ashtakavarga_pinda_sarva":
        return f"{graha} sarva pinda: {int(value_num)} ({ay})."
    if category == "ashtakavarga_kakshya_boundary":
        return (f"Kakṣyā {subject.replace('KAKSHYA_','')} ({key}): {value_num} "
                f"(3°45′ arc; lord fixed classical, ayanamsha-invariant).")
    if category == "house_bhava_bala_subscore":
        return f"House {subject.replace('HOUSE_','')} {key}: {value_num:.4f} rupa ({ay})."
    if category == "house_bhava_bala_total":
        return f"House {subject.replace('HOUSE_','')} total bhava bala: {value_num:.4f} rupa ({ay})."
    if category == "house_bhava_bala_ratio":
        return (f"House {subject.replace('HOUSE_','')} bhava bala strength ratio: "
                f"{value_num:.4f} (vs 7.0 rupa minimum) ({ay}).")
    return f"{subject} {category}/{key}: {value_num:.4f} ({ay})."


def _check_narration(text_value: str | None, context: str) -> None:
    if text_value is None:
        return
    lower = text_value.lower()
    for pat in FORBIDDEN_PATTERNS:
        if pat in lower:
            raise ValueError(
                f"[NARRATION LINTER] Forbidden pattern '{pat}' in "
                f"fact_value_text='{text_value}' at {context}"
            )


# ── Drik bala from aspect matrix ─────────────────────────────────────────────

_BENEFIC_GRAHAS_DRIK = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_MALEFIC_GRAHAS_DRIK = frozenset({"Saturn", "Mars", "Sun", "Rahu", "Ketu"})
_DRIK_ASPECT_OFFSETS: dict[str, dict[int, float]] = {
    "Saturn":  {3: 0.25, 7: 1.0, 10: 0.75},
    "Jupiter": {5: 1.0,  7: 1.0, 9: 1.0},
    "Mars":    {4: 1.0,  7: 1.0, 8: 1.0},
    "Rahu":    {5: 1.0,  7: 1.0, 9: 1.0},
    "Ketu":    {5: 1.0,  7: 1.0, 9: 1.0},
}
_DRIK_DEFAULT_OFFSETS: dict[int, float] = {7: 1.0}


def _compute_drik_bala(target_graha: str, target_house: int, grahas: list[dict]) -> float:
    """Compute drik bala for a graha from Parashari aspects received.
    Returns float in [0.0, 1.0]: 0.5 baseline ± aspect contributions.
    """
    net = 0.0
    for g in grahas:
        g_name = g["name"]
        if g_name == target_graha:
            continue
        g_house = int(g.get("house", 0))
        if not g_house:
            continue
        offsets = _DRIK_ASPECT_OFFSETS.get(g_name, _DRIK_DEFAULT_OFFSETS)
        for offset, strength in offsets.items():
            aspected_h = ((g_house - 1 + offset - 1) % 12) + 1
            if aspected_h == target_house:
                if g_name in _BENEFIC_GRAHAS_DRIK:
                    net += strength * 0.25
                elif g_name in _MALEFIC_GRAHAS_DRIK:
                    net -= strength * 0.25
    return max(0.0, min(1.0, 0.5 + net))


# ── Shadbala: delegated to PyJHora ────────────────────────────────────────────
# M-1 fix (see MARSYS_DEFECT_GAP_REGISTER): this used to be a hand-rolled
# 0-1 six-bucket heuristic. It now calls jhora.horoscope.chart.strength.
# shad_bala directly via pyjhora_adapter.strength.compute_shadbala.

def _derive_shadbala_from_positions(
    chart_output: dict[str, Any],
    ayanamsha_id: str,
    *,
    jd_ut: float,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, dict[str, float]]:
    """
    Real BPHS shadbala for the 7 classical grahas, delegated to PyJHora.
    Returns {graha_name: {sthana, dig, kala, cheshta, naisargika, drik, total}}.

    Rahu/Ketu have NO classical shadbala under strict Parashara tradition
    (naisargika_na=True flag set on their entries, school='parashara_strict').
    Their sthana (positional dignity) and drik (aspects received) ARE
    computable and are derived here as a labeled `computed_extension` from the
    already PyJHora-verified D1 positions in `chart_output` (BPHS dignity
    table for sthana; Parasari aspect matrix for drik, via
    _compute_drik_bala). dig/kala/cheshta/naisargika are 0.0 for nodes
    (not_defined_for_nodes) — there is no BPHS formula for these for Rahu/Ketu.

    Args:
        chart_output: PyJHora chart output dict with grahas/panchanga (used
            only for the Rahu/Ketu computed_extension fallback below — the
            classical 7 are computed directly from jd_ut/place by PyJHora).
        ayanamsha_id: Ayanamsha identifier string.
        jd_ut: Julian Day (local-wallclock convention, matching
            pyjhora_adapter.compute.compute_chart) for the classical-7
            PyJHora shadbala call. Required — no silent heuristic fallback.
        lat, lon, tz: Birth place, required by PyJHora's shad_bala.
    """
    _NODAL_GRAHAS = frozenset({"Rahu", "Ketu"})
    grahas = chart_output.get("grahas", [])

    result: dict[str, dict[str, float]] = {}

    # ── Classical 7: real PyJHora shadbala (M-1 fix) ─────────────────────
    pj_shadbala = pyjhora_strength.compute_shadbala(jd_ut, ayanamsha_id, lat=lat, lon=lon, tz=tz)
    for name, sb in pj_shadbala.items():
        result[name] = {
            "sthana": sb["sthana"],
            "dig": sb["dig"],
            "kala": sb["kala"],
            "cheshta": sb["cheshta"],
            "naisargika": sb["naisargika"],
            "drik": sb["drik"],
            "total": sb["total"],
        }

    # ── Nodes: no classical shadbala. sthana + drik are computed_extension. ─
    for g in grahas:
        name = g["name"]
        if name not in _NODAL_GRAHAS:
            continue

        house = int(g.get("house", 1))
        dignity = g.get("dignity_status", "neutral")

        # computed_extension: BPHS dignity table (Exaltation=1.0, Own=0.75,
        # Neutral=0.375, Debilitation=0.0) — not from PyJHora's shad_bala
        # (which excludes nodes entirely), but a real classical rule, not a
        # fabricated value.
        sthana_map = {
            "exalted": 1.0,
            "own_sign": 0.75,
            "neutral": 0.375,
            "debilitated": 0.0,
        }
        sthana = sthana_map.get(dignity, 0.375)

        # computed_extension: Parasari aspect matrix (benefic/malefic net),
        # same formula used for the classical 7's fallback context.
        drik = _compute_drik_bala(name, house, grahas)

        total = sthana + drik  # dig/kala/cheshta/naisargika are 0 for nodes

        result[name] = {
            "sthana": round(sthana, 4),
            "dig": 0.0,
            "kala": 0.0,
            "cheshta": 0.0,
            "naisargika": 0.0,
            "drik": round(drik, 4),
            "total": round(total, 4),
            "naisargika_na": True,
            "school": "parashara_strict",
        }

    return result


def _derive_ishta_kashta(
    shadbala: dict[str, dict[str, float]],
    jd_ut: float,
    ayanamsha_id: str,
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, dict[str, float]]:
    """
    computed_extension: Ishta Phala = sqrt(Uchcha Bala x Cheshta Bala);
    Kashta Phala = sqrt((60 - Uchcha Bala) x (60 - Cheshta Bala)) — real BPHS
    formula (both operands in virupas, 0..60).

    R6 1a-strength fix: previously used `sthana_bala` (the FULL 5-component
    Sthana Bala, up to ~300 virupas) as a proxy for Uchcha Bala (one of
    Sthana's 5 sub-components, bounded 0..60) — that scale mismatch caused a
    `math domain error` the moment real (non-degenerate) shadbala values were
    substituted in. Uchcha Bala is now the real per-planet value from
    pyjhora_adapter.strength.compute_uchcha_bala (jhora's own
    strength._uchcha_bala), and Cheshta Bala is the real value already
    computed in `shadbala` (re-expressed in virupas via *60).

    Nodes (Rahu/Ketu) have no classical Uchcha/Cheshta Bala; ishta/kashta are
    not emitted for them (unchanged from before this fix — the writer's row
    builder only calls this for the 7 classical grahas).
    """
    import math

    uchcha_virupas = pyjhora_strength.compute_uchcha_bala(jd_ut, ayanamsha_id, lat=lat, lon=lon, tz=tz)

    result = {}
    for graha in pyjhora_strength.CLASSICAL_PLANETS:
        sb = shadbala.get(graha, {})
        uchcha_60 = uchcha_virupas.get(graha, 0.0)
        cheshta_60 = sb.get("cheshta", 0.0) * 60.0
        ishta = math.sqrt(max(0.0, uchcha_60) * max(0.0, cheshta_60))
        kashta = math.sqrt(max(0.0, 60.0 - uchcha_60) * max(0.0, 60.0 - cheshta_60))
        result[graha] = {
            "ishta": round(ishta, 4),
            "kashta": round(kashta, 4),
        }
    return result


def _derive_vimsopaka(
    jd_ut: float,
    ayanamsha_id: str,
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, dict[str, float]]:
    """
    Real BPHS Vimshopaka Bala for the 7 classical grahas (M-2 fix — see
    MARSYS_DEFECT_GAP_REGISTER). Delegated to PyJHora
    (jhora.horoscope.chart.charts.vimsopaka_*_of_planets via
    pyjhora_adapter.strength.compute_vimsopaka), computed from each planet's
    real per-varga dignity against the classical amsa-weight tables — NOT
    `min(shadbala_total/6*20, 20)`, which consumed zero varga dignity data.
    """
    pj_vims = pyjhora_strength.compute_vimsopaka(jd_ut, ayanamsha_id, lat=lat, lon=lon, tz=tz)
    return {
        name: pj_vims[name]
        for name in pyjhora_strength.CLASSICAL_PLANETS
        if name in pj_vims
    }


# ── Ashtakavarga derivation from positions ───────────────────────────────────

def _derive_ashtakavarga(
    jd_ut: float,
    ayanamsha_id: str,
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, Any]:
    """
    Real BPHS Ashtakavarga — raw bindus AND full shodhana (M-3 fix, see
    MARSYS_DEFECT_GAP_REGISTER). Delegated to PyJHora
    (jhora.horoscope.chart.ashtakavarga.get_ashtaka_varga + sodhaya_pindas via
    pyjhora_adapter.strength.compute_ashtakavarga_shodhana) — trikona shodhana
    and ekadhipatya shodhana are both real (previously: `sodhita ≡ raw`,
    trikona skipped entirely per the writer's own prior comment; ekadhipatya
    was faked as `bindus - 1`; no gunakara multiplication was applied at all).

    Returns {"bindus": {graha_name: [12 raw bindus]} (+ "SARVA": [12 sums],
    verified to sum to 337 — the classical Parashara constant), "pinda":
    {graha_name: {"raasi": int, "graha": int, "sodhya": int}}}.
    """
    return pyjhora_strength.compute_ashtakavarga_shodhana(
        jd_ut, ayanamsha_id, lat=lat, lon=lon, tz=tz,
    )


# CLASSICAL_7 planet order (PyJHora const.SUN_TO_SATURN index order).
_AV_CLASSICAL_7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def _derive_ashtakavarga_shodhana_grids(
    jd_ut: float,
    ayanamsha_id: str,
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, dict[str, list[int]]]:
    """
    CR-99a: the intermediate **sign-keyed** śodhana GRIDS — trikoṇa-śodhita and
    ekādhipatya-śodhita bindu arrays per graha — that the pinda totals reduce
    from. Delegated to PyJHora (`ashtakavarga._trikona_sodhana` /
    `._ekadhipatya_sodhana`), NOT hand-rolled, and derived from the SAME raw
    binna the pinda writer uses (no bindu VALUE recompute — §L.3 baseline: this
    reads the classical engine's own reductions, it does not re-derive bindus).

    Arrays are 12-element, **sign-indexed** (index 0 = Aries), matching the raw
    binna convention (the raw bindus feeding this are absolute-rāśi-indexed, not
    house-relative — the very reason CR-99a re-keys by sign).

    Returns {"trikona": {graha: [12]}, "ekadhipatya": {graha: [12]}}.

    NOTE on the mutation trap (documented in pyjhora_adapter/strength.py):
    PyJHora's `_trikona_sodhana`/`_ekadhipatya_sodhana` do a SHALLOW copy of the
    binna outer list then mutate the inner per-sign lists in place. We snapshot
    each grid into fresh int lists immediately after each call, and never read
    `binna` as "raw" afterwards (raw bindus come from the separate
    `_derive_ashtakavarga` call upstream), so no reduced values leak out
    mislabeled.
    """
    from pyjhora_adapter._jhora import charts, utils
    from jhora.horoscope.chart import ashtakavarga as _jhora_av

    place = pyjhora_strength._place(lat, lon, tz)
    pyjhora_strength._set_ayanamsha(ayanamsha_id)

    pp = charts.rasi_chart(jd_ut, place)
    chart_1d = utils.get_house_planet_list_from_planet_positions(pp)

    binna, _samudhaya, _prastara = _jhora_av.get_ashtaka_varga(chart_1d)

    after_trikona = _jhora_av._trikona_sodhana(binna)
    trikona_grid = {
        name: [int(v) for v in after_trikona[i]]
        for i, name in enumerate(_AV_CLASSICAL_7)
    }

    after_ekadhipatya = _jhora_av._ekadhipatya_sodhana(after_trikona, chart_1d)
    ekadhipatya_grid = {
        name: [int(v) for v in after_ekadhipatya[i]]
        for i, name in enumerate(_AV_CLASSICAL_7)
    }

    return {"trikona": trikona_grid, "ekadhipatya": ekadhipatya_grid}


def _derive_bhava_bala(
    jd_ut: float,
    ayanamsha_id: str,
    *,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
) -> dict[str, dict[str, float]]:
    """
    Bhāva Bala (house strength), CR-103. **No hand-rolling** (D-1.5b Lane B-2 rule):
    delegates to PyJHora's classical implementation
    ``jhora.horoscope.chart.strength.bhava_bala(jd, place)`` and its three
    per-source sub-computations.

    DOCUMENTED-APPROXIMATION (Binder amendment, STATE_D-1.5b.md): PyJHora's
    ``bhava_bala`` is a **THREE-source** composition — Bhāva Adhipati Bala
    (``_bhava_adhipathi_bala``) + Bhāva Dig Bala (``_bhava_dig_bala``) + Bhāva
    Dṛk/Dṛṣṭi Bala (``_bhava_drik_bala``) — NOT the full six-source Bhāva Bala of
    BV Raman (Bhāvādhipati + Dig + Dṛṣṭi + and the three that PyJHora does not
    compute). PyJHora's own docstring carries a "not getting BV Raman's book
    values" caveat. Per Adjudicator-doctrine these facts are therefore stamped
    ``verification_pass_status='documented_approximation'`` and cite the
    3-component composition explicitly; they never claim six-source.

    ``bhava_bala(jd, place)`` returns ``[shashtiamsas, rupas, strength_ratios]``
    (each a 12-element list, bhāva 1..12, ascendant-relative). The three
    sub-source functions each return 12-element shashtiamsa (virupa) lists that
    sum to the composed total. This function converts sub-scores and total to
    RUPA (÷60) to match the existing ``unit: "rupa"`` chart_facts contract, and
    surfaces the classical strength ratio (total_rupa ÷ 7.0 minimum).

    Returns {house_key: {bhava_adhipati_bala, bhava_digbala, bhava_drishti_bala,
    total, strength_ratio}} where house_key = "HOUSE_1".."HOUSE_12". Key names
    are unchanged from the prior contract (bhava_drishti_bala == the drik source)
    so mv_chart_bhava_bala_summary keeps resolving.
    """
    from jhora.horoscope.chart import strength as _jhora_strength

    place = pyjhora_strength._place(lat, lon, tz)
    pyjhora_strength._set_ayanamsha(ayanamsha_id)

    _bb, bb_rupas, bb_strength = _jhora_strength.bhava_bala(jd_ut, place)
    bab = _jhora_strength._bhava_adhipathi_bala(jd_ut, place)  # 3-source: adhipati
    bdb = _jhora_strength._bhava_dig_bala(jd_ut, place)         # 3-source: dig
    bdr = _jhora_strength._bhava_drik_bala(jd_ut, place)        # 3-source: drik

    # Key names are kept identical to the pre-existing chart_facts contract
    # (bhava_adhipati_bala / bhava_digbala / bhava_drishti_bala) so downstream
    # consumers — notably mv_chart_bhava_bala_summary — keep resolving. Only the
    # VALUES (now real PyJHora), the status (documented_approximation) and the
    # provenance change. Bhāva Dṛṣṭi Bala == the drik source of PyJHora.
    result: dict[str, dict[str, float]] = {}
    for h in range(12):
        house_key = f"HOUSE_{h + 1}"
        result[house_key] = {
            "bhava_adhipati_bala": round(float(bab[h]) / 60.0, 4),
            "bhava_digbala": round(float(bdb[h]) / 60.0, 4),
            "bhava_drishti_bala": round(float(bdr[h]) / 60.0, 4),
            "total": round(float(bb_rupas[h]), 4),
            "strength_ratio": round(float(bb_strength[h]), 4),
        }

    return result


# ── Two-pass verification ────────────────────────────────────────────────────

class TwoPassVerificationError(RuntimeError):
    """Raised when two-pass divergence exceeds tolerance."""
    pass


def _verify_shadbala(shadbala: dict[str, dict[str, float]], tolerance: float = 0.02) -> str:
    """
    Sanity-check PyJHora's real shadbala output (NOT a second independent
    recomputation — PyJHora IS pass 1; this is bounds/consistency guarding,
    per the R6 1a-strength fix — see MARSYS_DEFECT_GAP_REGISTER M-1):
    1. Magnitude sub-balas (sthana/dig/kala/cheshta/naisargika) must be
       non-negative — these are magnitude-only per BPHS.
    2. drik bala MAY be negative — real, signed, per BPHS Ch.26 Parasari
       graha drishti (net malefic aspect can dominate). Only finiteness is
       checked for drik, not sign.
    3. total > 0.0 for any real chart (a graha with all-zero magnitude
       sub-balas and a hugely negative drik would be a data bug).
    4. sum(sub-balas) ≈ total within tolerance — catches key-set mismatches or
       rounding drift between individual sub-bala rounding and stored total.

    NOTE: `total` is stored as round(sum, 4) and sub-balas are each round(x, 4)
    after a /60 virupa->rupa conversion, so the sum-vs-total check tolerates a
    slightly larger drift than pure 4-decimal rounding would (up to ~0.02 rupa
    across 6 keys) but does NOT constitute an independent recomputation from a
    second code path. The primary guards here are the non-negativity (for
    magnitude sub-balas) and non-zero total checks.
    """
    _MAGNITUDE_KEYS = ["sthana", "dig", "kala", "cheshta", "naisargika"]
    _SIGNED_KEYS = ["drik"]
    sub_bala_keys = _MAGNITUDE_KEYS + _SIGNED_KEYS
    failures = []
    for graha, sb in shadbala.items():
        # Guard 1: magnitude sub-balas must be non-negative
        for key in _MAGNITUDE_KEYS:
            val = sb.get(key, 0.0)
            if val < 0.0:
                failures.append(
                    f"{graha}.{key}={val:.6f} is negative (expected >= 0.0)"
                )

        # Guard 1b: drik (signed) must at least be finite
        for key in _SIGNED_KEYS:
            val = sb.get(key, 0.0)
            if val != val or abs(val) > 10.0:  # NaN check + gross-outlier bound
                failures.append(
                    f"{graha}.{key}={val:.6f} out of plausible drik-bala bounds"
                )

        # Guard 2: total must be positive for a real chart row
        total = sb.get("total", 0.0)
        if total <= 0.0:
            failures.append(
                f"{graha}: total={total:.6f} is zero or negative (data bug)"
            )

        # Guard 3: sum of stored sub-balas must match stored total within tolerance
        # (catches key-set mismatches and rounding drift)
        sub_sum = sum(sb.get(k, 0.0) for k in sub_bala_keys)
        delta = abs(sub_sum - total)
        if delta > tolerance:
            failures.append(
                f"{graha}: sum_sub_balas={sub_sum:.6f} total={total:.6f} "
                f"delta={delta:.6f} exceeds tolerance={tolerance}"
            )

    if failures:
        msg = (
            f"SHADBALA VERIFICATION FAILED:\n"
            + "\n".join(f"  {f}" for f in failures)
        )
        _write_halt_log("VERIFY_SHADBALA", msg)
        raise TwoPassVerificationError(msg)
    # M-22 fix (M-1 evidence): this function's own docstring (above) already
    # admits the sum-vs-total check "does NOT constitute an independent
    # recomputation from a second code path" — it is self-referential
    # (sub-balas are defined to sum to total by construction), so it always
    # passes regardless of whether the underlying shadbala VALUES are a
    # correct classical computation. Per M-1, the shadbala engine itself is
    # a toy heuristic (never calls PyJHora). Returning "two_pass_verified"
    # here claimed an independent classical cross-check that never ran.
    # Demoted to "single_pass" (a real single structural-invariant pass did
    # run; formulas.py VERIFICATION_RESCALE 0.85 vs 1.00). Fixing the
    # underlying shadbala engine is M-1's scope, not this lane's.
    return "single_pass"


def _verify_ashtakavarga(
    bav: dict[str, list[int]], tolerance: int = 2
) -> str:
    """
    Verify ashtakavarga invariants:
    1. Sarvashtakavarga sum = 337 (±tolerance).
    2. SARVA = sum of 7 individual graha bindus per house.
    Returns 'two_pass_verified' on pass.
    """
    failures = []

    # Check 1: sarva sum
    sarva = bav.get("SARVA", [])
    sarva_total = sum(sarva)
    if abs(sarva_total - SARVA_BINDU_TOTAL) > tolerance:
        failures.append(
            f"Sarvashtakavarga total={sarva_total}, expected={SARVA_BINDU_TOTAL} "
            f"(±{tolerance})"
        )

    # Check 2: SARVA = sum of individual grahas
    grahas_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    for h_idx in range(12):
        expected = sum(bav.get(g, [0]*12)[h_idx] for g in grahas_order)
        actual = sarva[h_idx] if h_idx < len(sarva) else 0
        if abs(actual - expected) > 0:
            failures.append(
                f"SARVA house {h_idx+1}: actual={actual}, sum_grahas={expected}"
            )

    if failures:
        msg = "ASHTAKAVARGA TWO-PASS DIVERGENCE:\n" + "\n".join(f"  {f}" for f in failures)
        _write_halt_log("TWO_PASS_ASHTAKAVARGA", msg)
        raise TwoPassVerificationError(msg)
    # M-22 fix (M-3 evidence): checks 1+2 above verify the RAW Bhinnashtaka-
    # varga bindu arithmetic is internally consistent (SARVA=337, SARVA=sum
    # of 7 graha arrays) — a real cross-check, but ONLY of the raw bindu
    # sums. Per M-3, the "sodhita" (shodhana-reduced) pinda this feeds skips
    # trikona shodhana entirely (sodhita ≡ raw, comment admits) and fakes
    # ekadhipatya as bindus−1 — neither is checked here. "two_pass_verified"
    # overstated what was actually verified (raw-bindu arithmetic, not
    # shodhana correctness). Demoted to "single_pass". Fixing the shodhana
    # step itself is M-3's scope, not this lane's.
    return "single_pass"


# ── Rows builders ────────────────────────────────────────────────────────────

def _build_shadbala_rows(
    shadbala: dict[str, dict[str, float]],
    ishta_kashta: dict[str, dict[str, float]],
    vimsopaka: dict[str, dict[str, float]],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
    verif_status: str,
) -> list[dict[str, Any]]:
    rows = []
    category_map = {
        "sthana": "graha_shadbala_sthana",
        "dig": "graha_shadbala_dig",
        "kala": "graha_shadbala_kala",
        "cheshta": "graha_shadbala_cheshta",
        "naisargika": "graha_shadbala_naisargika",
        "drik": "graha_shadbala_drik",
        "total": "graha_shadbala_total",
    }

    classical_grahas = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    for graha_name in classical_grahas:
        subject = PLANET_TO_SUBJECT.get(graha_name, graha_name.upper())
        sb = shadbala.get(graha_name, {})

        # Naisargika bala is ayanamsha-invariant
        for sub_key, category in category_map.items():
            value = sb.get(sub_key, 0.0)
            eff_ayan = "INVARIANT" if sub_key == "naisargika" else ayanamsha_id
            verif = ("classical_match" if sub_key == "naisargika" else verif_status)

            fid = _fact_id(category, subject, "rupa", chart_id, eff_ayan, build_id)
            cref = _citation_ref(category, subject, "rupa", chart_id, eff_ayan, eng_ver)
            chum = _citation_human_strength(category, subject, "rupa", value, eff_ayan)

            rows.append({
                "fact_id": fid,
                "chart_id": chart_id,
                "ayanamsha_id": eff_ayan,
                "build_id": build_id,
                "fact_category": category,
                "fact_subject": subject,
                "fact_key": "rupa",
                "fact_value_text": None,
                "fact_value_num": value,
                "fact_value_jsonb": None,
                "unit": "rupa",
                "citation_ref": cref,
                "citation_human": chum,
                "source_calculation": f"pyjhora_adapter.strength.compute_shadbala/{eng_ver}",
                "verification_pass_status": verif,
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

        # Required rupa for total
        req = SHADBALA_REQUIRED.get(graha_name, 5.0)
        fid_req = _fact_id("graha_shadbala_total", subject, "required_rupa",
                            chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": fid_req,
            "chart_id": chart_id,
            "ayanamsha_id": "INVARIANT",  # Required is a classical constant
            "build_id": build_id,
            "fact_category": "graha_shadbala_total",
            "fact_subject": subject,
            "fact_key": "required_rupa",
            "fact_value_text": None,
            "fact_value_num": req,
            "fact_value_jsonb": None,
            "unit": "rupa",
            "citation_ref": _citation_ref("graha_shadbala_total", subject, "required_rupa",
                                           chart_id, "INVARIANT", eng_ver),
            "citation_human": (
                f"{graha_name} required shadbala: {req:.2f} rupa "
                f"(classical Parashara minimum, ayanamsha-invariant)."
            ),
            "source_calculation": f"classical_parashara_table/{eng_ver}",
            "verification_pass_status": "classical_match",
            "engine_version": eng_ver,
            "computed_at": computed_at,
        })

        # CR-18: achieved/required shadbala ratio. Bare rupas were served without
        # the classical normative band — consumers had to supply BPHS minimums from
        # priors. The ratio (achieved total ÷ required minimum) is the normalized
        # strength: ratio ≥ 1.0 = at/above the Parashara minimum, < 1.0 = deficient.
        # Ayanamsha-dependent (the achieved total varies per ayanamsha; required is a
        # classical constant), so keyed to the live ayanamsha_id, unlike required_rupa.
        achieved_total = sb.get("total", 0.0)
        ratio = (achieved_total / req) if req else None
        if ratio is not None:
            fid_ratio = _fact_id("graha_shadbala_total", subject, "ratio",
                                 chart_id, ayanamsha_id, build_id)
            rows.append({
                "fact_id": fid_ratio,
                "chart_id": chart_id,
                "ayanamsha_id": ayanamsha_id,
                "build_id": build_id,
                "fact_category": "graha_shadbala_total",
                "fact_subject": subject,
                "fact_key": "ratio",
                "fact_value_text": None,
                "fact_value_num": ratio,
                "fact_value_jsonb": None,
                "unit": None,
                "citation_ref": _citation_ref("graha_shadbala_total", subject, "ratio",
                                              chart_id, ayanamsha_id, eng_ver),
                "citation_human": (
                    f"{graha_name} shadbala ratio: {ratio:.3f} "
                    f"({achieved_total:.4f} achieved ÷ {req:.2f} required rupa; "
                    f"{'at/above' if ratio >= 1.0 else 'below'} classical minimum) "
                    f"({ayanamsha_id})."
                ),
                "source_calculation": f"achieved_total_div_required_rupa/{eng_ver}",
                "verification_pass_status": verif_status,
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

        # Ishta/Kashta phala
        ik = ishta_kashta.get(graha_name, {})
        for ik_key, ik_cat in [("ishta", "graha_ishta_phala"), ("kashta", "graha_kashta_phala")]:
            val = ik.get(ik_key, 0.0)
            fid2 = _fact_id(ik_cat, subject, "score", chart_id, ayanamsha_id, build_id)
            rows.append({
                "fact_id": fid2,
                "chart_id": chart_id,
                "ayanamsha_id": ayanamsha_id,
                "build_id": build_id,
                "fact_category": ik_cat,
                "fact_subject": subject,
                "fact_key": "score",
                "fact_value_text": None,
                "fact_value_num": val,
                "fact_value_jsonb": None,
                "unit": None,
                "citation_ref": _citation_ref(ik_cat, subject, "score",
                                               chart_id, ayanamsha_id, eng_ver),
                "citation_human": _citation_human_strength(
                    ik_cat, subject, "score", val, ayanamsha_id),
                "source_calculation": f"computed_extension.ishta_kashta_bphs_sqrt_uchcha_cheshta/{eng_ver}",
                "verification_pass_status": verif_status,
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

        # Vimsopaka
        vm = vimsopaka.get(graha_name, {})
        for vm_type, cat in [
            ("shadvarga", "graha_vimsopaka_shadvarga"),
            ("saptavarga", "graha_vimsopaka_saptavarga"),
            ("dasavarga", "graha_vimsopaka_dasavarga"),
            ("shodasavarga", "graha_vimsopaka_shodasavarga"),
        ]:
            val = vm.get(vm_type, 0.0)
            fid3 = _fact_id(cat, subject, "score", chart_id, ayanamsha_id, build_id)
            rows.append({
                "fact_id": fid3,
                "chart_id": chart_id,
                "ayanamsha_id": ayanamsha_id,
                "build_id": build_id,
                "fact_category": cat,
                "fact_subject": subject,
                "fact_key": "score",
                "fact_value_text": None,
                "fact_value_num": val,
                "fact_value_jsonb": None,
                "unit": None,
                "citation_ref": _citation_ref(cat, subject, "score",
                                               chart_id, ayanamsha_id, eng_ver),
                "citation_human": _citation_human_strength(
                    cat, subject, "score", val, ayanamsha_id),
                "source_calculation": f"pyjhora_adapter.strength.compute_vimsopaka/{eng_ver}",
                "verification_pass_status": verif_status,
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

    # ── Nodal grahas (Rahu / Ketu) ───────────────────────────────────────────
    # Emit one row per sub-bala so the cockpit/retrieval layer sees explicit rows.
    # Sub-balas not defined classically for nodes (dig, kala, cheshta, naisargika)
    # are emitted with value=0 and verification_pass_status='not_defined_for_nodes'.
    # Sthana (positional dignity) and drik (aspects received) ARE computable → use
    # values from the shadbala dict (computed in _derive_shadbala_from_positions).
    NODAL_UNDEFINED_SUBS = frozenset({"dig", "kala", "cheshta", "naisargika"})
    nodal_grahas = ["Rahu", "Ketu"]
    for graha_name in nodal_grahas:
        subject = PLANET_TO_SUBJECT.get(graha_name, graha_name.upper())
        sb = shadbala.get(graha_name, {})
        if not sb:
            continue  # node not in chart output (degenerate case)
        for sub_key, category in category_map.items():
            value = sb.get(sub_key, 0.0)
            eff_ayan = "INVARIANT" if sub_key == "naisargika" else ayanamsha_id
            if sub_key in NODAL_UNDEFINED_SUBS:
                node_verif = "not_defined_for_nodes"
            elif sub_key in ("sthana", "drik", "total"):
                node_verif = verif_status
            else:
                node_verif = verif_status
            fid = _fact_id(category, subject, "rupa", chart_id, eff_ayan, build_id)
            cref = _citation_ref(category, subject, "rupa", chart_id, eff_ayan, eng_ver)
            chum = _citation_human_strength(category, subject, "rupa", value, eff_ayan)
            rows.append({
                "fact_id": fid,
                "chart_id": chart_id,
                "ayanamsha_id": eff_ayan,
                "build_id": build_id,
                "fact_category": category,
                "fact_subject": subject,
                "fact_key": "rupa",
                "fact_value_text": None,
                "fact_value_num": value,
                "fact_value_jsonb": None,
                "unit": "rupa",
                "citation_ref": cref,
                "citation_human": chum,
                "source_calculation": f"computed_extension.nodal_dignity_and_drik_bphs/{eng_ver}",
                "verification_pass_status": node_verif,
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

    return rows


def _build_ashtakavarga_rows(
    bav: dict[str, list[int]],
    pinda: dict[str, dict[str, int]],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str, verif_status: str,
    grids: dict[str, dict[str, list[int]]] | None = None,
) -> list[dict[str, Any]]:
    """
    M-3 fix (see MARSYS_DEFECT_GAP_REGISTER): `pinda` now comes from PyJHora's
    real BPHS shodhana (trikona sodhana + ekadhipatya sodhana + rasimana/
    grahamana gunakara multiplication), NOT `sodhita ≡ raw bindus` /
    `bhinna = bindus - 1`.

    Category mapping (existing chart_facts schema, values now real):
      - ashtakavarga_bindu        -> raw BAV/SAV bindu, HOUSE-keyed subject
        `{subject}-HOUSE_N` (RETAINED unchanged for continuity — see CR-99a).
      - ashtakavarga_pinda_sodhita -> pinda[graha]["sodhya"] (raasi_pinda +
        graha_pinda, the final trikona+ekadhipatya-reduced, gunakara-
        multiplied total — the classical "Sodhya Pinda").
      - ashtakavarga_pinda_bhinna  -> pinda[graha]["graha"] (the graha-pinda
        sub-component, derived from the ekadhipatya-sodhita BAV via the
        grahamana multiplier table — distinct from the raasi-pinda
        sub-component, both real BPHS quantities).
      - ashtakavarga_pinda_sarva   -> sum(raw bindus) per graha (unchanged;
        this was never broken — no shodhana applies to sarva pinda).
    SARVA (the aggregate row) has no classical sodhya/graha pinda of its own;
    we report the sum across the 7 grahas' real values for that row so no
    rows go null, clearly documented here (not a fabricated per-graha value).

    ── CR-99a Aṣṭakavarga completion (D-1.5b Lane B-2), ADDITIVE ──────────────
    The raw ``ashtakavarga_bindu`` arrays are absolute-**rāśi**-indexed (index 0
    = Aries), yet the legacy subject labels them ``-HOUSE_N`` — the wrong key for
    transit (gochara) reading, which moves through SIGNS. This function KEEPS the
    house-keyed rows for continuity and ADDS, from the SAME bindu values (NO
    recompute — §L.3 baseline):
      - ashtakavarga_bindu_sign             : sign-keyed BAV/SAV (`{subject}-SIGN_N`)
      - ashtakavarga_trikona_shodhana       : trikoṇa-śodhita grid, sign-keyed
      - ashtakavarga_ekadhipathya_shodhana  : ekādhipatya-śodhita grid, sign-keyed
      - ashtakavarga_pinda_raasi            : rāśi-piṇḍa (was computed then dropped)
      - ashtakavarga_kakshya_boundary       : 8 kakṣyā sub-arc boundaries (constants)
    """
    rows = []
    grids = grids or {}
    trikona_grid = grids.get("trikona", {})
    ekadhipatya_grid = grids.get("ekadhipatya", {})

    # Values sourced from the graha SSoT (brahmagyan/graha_vocabulary) rather
    # than hardcoded literals — ADHIṢṬHĀNA Lane A2 (found via the full-tree
    # census; not one of the originally-enumerated retirement targets).
    # "SARVA" is the ashtakavarga aggregate row, not a graha.
    planet_subjects = {
        name: norm_graha(name)
        for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    }
    planet_subjects["SARVA"] = "SARVA"

    src = f"pyjhora_adapter.strength.compute_ashtakavarga_shodhana/{eng_ver}"

    def _mk(cat: str, subject: str, key: str, val: float, unit: str,
            *, text: str | None = None, chum: str | None = None) -> None:
        rows.append({
            "fact_id": _fact_id(cat, subject, key, chart_id, ayanamsha_id, build_id),
            "chart_id": chart_id,
            "ayanamsha_id": ayanamsha_id,
            "build_id": build_id,
            "fact_category": cat,
            "fact_subject": subject,
            "fact_key": key,
            "fact_value_text": text,
            "fact_value_num": None if val is None else float(val),
            "fact_value_jsonb": None,
            "unit": unit,
            "citation_ref": _citation_ref(cat, subject, key, chart_id, ayanamsha_id, eng_ver),
            "citation_human": chum if chum is not None else _citation_human_strength(
                cat, subject, key, float(val) if val is not None else 0.0, ayanamsha_id),
            "source_calculation": src,
            "verification_pass_status": verif_status,
            "engine_version": eng_ver,
            "computed_at": computed_at,
        })

    sarva_sodhya_sum = sum(p["sodhya"] for p in pinda.values())
    sarva_graha_sum = sum(p["graha"] for p in pinda.values())
    sarva_raasi_sum = sum(p.get("raasi", 0) for p in pinda.values())

    for planet_name, subject in planet_subjects.items():
        bindus_list = bav.get(planet_name, [0] * 12)

        for idx, bindus in enumerate(bindus_list):
            # RETAINED (continuity): legacy house-keyed subject. The array is
            # actually sign-indexed, so idx+1 is the ABSOLUTE sign number; the
            # `-HOUSE_` label is legacy and preserved verbatim.
            _mk("ashtakavarga_bindu", f"{subject}-HOUSE_{idx + 1}", "bindus",
                float(bindus), "bindu")
            # ADDED (CR-99a): correct sign-keyed row, same value.
            _mk("ashtakavarga_bindu_sign", f"{subject}-SIGN_{idx + 1}", "bindus",
                float(bindus), "bindu")

        # ADDED (CR-99a): trikoṇa + ekādhipatya śodhana grids (7 grahas only;
        # SARVA has no per-graha śodhana). Sign-keyed, same index convention.
        # Category names + `reduced_bindus` key match the (pre-declared)
        # CHART_FACTS_SCHEMA.json entries.
        if planet_name != "SARVA":
            tri = trikona_grid.get(planet_name)
            if tri is not None:
                for idx, v in enumerate(tri):
                    _mk("ashtakavarga_trikona_shodhana", f"{subject}-SIGN_{idx + 1}",
                        "reduced_bindus", float(v), "bindu")
            eka = ekadhipatya_grid.get(planet_name)
            if eka is not None:
                for idx, v in enumerate(eka):
                    _mk("ashtakavarga_ekadhipathya_shodhana", f"{subject}-SIGN_{idx + 1}",
                        "reduced_bindus", float(v), "bindu")

        # Pinda totals for this graha
        if planet_name == "SARVA":
            pinda_sodhita = sarva_sodhya_sum
            pinda_bhinna = sarva_graha_sum
            pinda_raasi = sarva_raasi_sum
        else:
            p = pinda.get(planet_name, {"sodhya": 0, "graha": 0, "raasi": 0})
            pinda_sodhita = p["sodhya"]
            pinda_bhinna = p["graha"]
            pinda_raasi = p.get("raasi", 0)

        _mk("ashtakavarga_pinda_sodhita", subject, "total", float(pinda_sodhita), "bindu")
        _mk("ashtakavarga_pinda_bhinna", subject, "total", float(pinda_bhinna), "bindu")
        # ADDED (CR-99a): raasi pinda — was computed by the engine then dropped.
        _mk("ashtakavarga_pinda_raasi", subject, "total", float(pinda_raasi), "bindu")
        _mk("ashtakavarga_pinda_sarva", subject, "total", float(sum(bindus_list)), "bindu")

    # ADDED (CR-99a): kakṣyā sub-arc boundaries — 8 fixed classical constants
    # (chart-independent; stored per chart×ayanamsha for a uniform L1 contract).
    for k in range(8):
        start_deg = round(k * KAKSHYA_ARC_DEG, 4)
        end_deg = round((k + 1) * KAKSHYA_ARC_DEG, 4)
        lord = KAKSHYA_LORDS[k]
        subj = f"KAKSHYA_{k + 1}"
        chum = (f"Kakṣyā {k + 1}: {start_deg}°–{end_deg}° within each rāśi, "
                f"lord {lord} (fixed classical, ayanamsha-invariant).")
        _mk("ashtakavarga_kakshya_boundary", subj, "lord",
            None, "graha", text=lord, chum=chum)
        _mk("ashtakavarga_kakshya_boundary", subj, "start_deg", start_deg, "degree", chum=chum)
        _mk("ashtakavarga_kakshya_boundary", subj, "end_deg", end_deg, "degree", chum=chum)

    return rows


def _build_bhava_bala_rows(
    bhava_bala: dict[str, dict[str, float]],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str, verif_status: str,
) -> list[dict[str, Any]]:
    rows = []

    # CR-103 / Binder amendment: bhāva bala is a PyJHora 3-source composition
    # (adhipathi + dig + drik) — NOT six-source. These rows are ALWAYS stamped
    # documented_approximation regardless of the writer-global verif_status, and
    # cite the 3-component provenance explicitly (never claim six-source).
    _BB_STATUS = "documented_approximation"
    _BB_SOURCE = (
        f"pyjhora.strength.bhava_bala[3-source:adhipathi+dig+drik]/{eng_ver}"
    )
    subscore_map = {
        "bhava_adhipati_bala": ("house_bhava_bala_subscore", "bhava_adhipati_bala", "rupa"),
        "bhava_digbala": ("house_bhava_bala_subscore", "bhava_digbala", "rupa"),
        "bhava_drishti_bala": ("house_bhava_bala_subscore", "bhava_drishti_bala", "rupa"),
        "total": ("house_bhava_bala_total", "total", "rupa"),
        "strength_ratio": ("house_bhava_bala_ratio", "strength_ratio", "ratio"),
    }

    for house_key, hb in bhava_bala.items():
        for data_key, (cat, fk, unit) in subscore_map.items():
            val = hb.get(data_key, 0.0)
            fid = _fact_id(cat, house_key, fk, chart_id, ayanamsha_id, build_id)
            cref = _citation_ref(cat, house_key, fk, chart_id, ayanamsha_id, eng_ver)
            chum = _citation_human_strength(cat, house_key, fk, val, ayanamsha_id)
            rows.append({
                "fact_id": fid,
                "chart_id": chart_id,
                "ayanamsha_id": ayanamsha_id,
                "build_id": build_id,
                "fact_category": cat,
                "fact_subject": house_key,
                "fact_key": fk,
                "fact_value_text": None,
                "fact_value_num": val,
                "fact_value_jsonb": None,
                "unit": unit,
                "citation_ref": cref,
                "citation_human": chum,
                "source_calculation": _BB_SOURCE,
                "verification_pass_status": _BB_STATUS,
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

    return rows


# ── Amendment 1: Per-varga Ashtakavarga ──────────────────────────────────────

def _derive_ashtakavarga_for_varga(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    varga: str,
) -> dict[str, list[int]]:
    """
    Derive ashtakavarga bindus for a divisional varga using sign positions from
    chart_divisionals.

    Queries chart_divisionals for varga_position rows (fact_key='sign_id') to
    obtain the sign (1-based) of each planet in the given varga, then applies the
    same BENEFIC_HOUSES computation as _derive_ashtakavarga.

    Returns {planet_name: [12 bindus]} + SARVA key, or {} if positions unavailable.
    """
    try:
        rows = conn.execute(
            """
            SELECT fact_subject, fact_value_num
            FROM chart_divisionals
            WHERE chart_id = %s
              AND ayanamsha_id = %s
              AND fact_category = 'varga_position'
              AND fact_key = 'sign_id'
              AND varga = %s
            """,
            (chart_id, ayanamsha_id, varga),
        ).fetchall()
    except Exception as exc:
        logging.warning(
            "[ga_strength_writer] varga=%s query failed: %s", varga, exc
        )
        return {}

    if not rows:
        return {}

    # Build planet_signs: {benefic_name → sign_id_1based}
    # SQL already filters fact_key='sign_id'; rows are (fact_subject, fact_value_num)
    planet_signs: dict[str, int] = {}
    for row in rows:
        if isinstance(row, dict):
            fact_subject = row["fact_subject"]
            fact_value_num = row["fact_value_num"]
        else:
            fact_subject, fact_value_num = row[0], row[1]

        if fact_value_num is None:
            continue

        # fact_subject is "{varga}.{SUBJECT_CODE}" e.g. "D9.SUN"; normalize to uppercase
        parts = fact_subject.split(".")
        subject_code = parts[-1].upper() if len(parts) >= 2 else fact_subject.upper()

        benefic_name = _DIVISIONAL_TO_BENEFIC.get(subject_code)
        if benefic_name is None:
            logging.debug(
                "[ga_strength_writer] _derive_ashtakavarga_for_varga: "
                "unrecognized subject_code=%s (varga=%s); skipping",
                subject_code, varga,
            )
            continue

        sign_id = int(fact_value_num)
        if sign_id < 1 or sign_id > 12:
            continue
        planet_signs[benefic_name] = sign_id

    # Need at least the 7 classical planets + Lagna to compute meaningful AV
    required = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"}
    if not required.issubset(planet_signs.keys()):
        logging.warning(
            "[ga_strength_writer] varga=%s missing planets %s; skipping AV",
            varga, required - planet_signs.keys(),
        )
        return {}

    # BENEFIC_HOUSES is the same table as in _derive_ashtakavarga (BPHS classical).
    BENEFIC_HOUSES: dict[str, dict[str, list[int]]] = {
        "Sun": {
            "Sun":     [1, 2, 4, 7, 8, 9, 10, 11],
            "Moon":    [3, 6, 10, 11],
            "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [5, 6, 9, 11],
            "Venus":   [6, 7, 12],
            "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
            "Lagna":   [3, 4, 6, 10, 11, 12],
        },
        "Moon": {
            "Sun":     [3, 6, 7, 8, 10, 11],
            "Moon":    [1, 3, 6, 7, 10, 11],
            "Mars":    [2, 3, 5, 6, 9, 10, 11],
            "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
            "Jupiter": [1, 4, 7, 8, 10, 11, 12],
            "Venus":   [3, 4, 5, 7, 9, 10, 11],
            "Saturn":  [3, 5, 6, 11],
            "Lagna":   [3, 6, 10, 11],
        },
        "Mars": {
            "Sun":     [3, 5, 6, 10, 11],
            "Moon":    [3, 6, 11],
            "Mars":    [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [3, 5, 6, 11],
            "Jupiter": [6, 10, 11, 12],
            "Venus":   [6, 8, 11, 12],
            "Saturn":  [1, 4, 7, 8, 9, 10, 11],
            "Lagna":   [1, 3, 6, 10, 11],
        },
        "Mercury": {
            "Sun":     [5, 6, 9, 11, 12],
            "Moon":    [2, 4, 6, 8, 10, 11],
            "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [6, 8, 11, 12],
            "Venus":   [1, 2, 3, 4, 5, 8, 9, 11],
            "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
            "Lagna":   [1, 2, 4, 6, 8, 10, 11],
        },
        "Jupiter": {
            "Sun":     [1, 2, 3, 4, 7, 8, 10, 11],
            "Moon":    [2, 5, 7, 9, 11],
            "Mars":    [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
            "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
            "Venus":   [2, 5, 6, 9, 10, 11],
            "Saturn":  [3, 5, 6, 12],
            "Lagna":   [1, 2, 4, 5, 6, 7, 9, 10, 11],
        },
        "Venus": {
            "Sun":     [8, 11, 12],
            "Moon":    [1, 2, 3, 4, 5, 8, 9, 11, 12],
            "Mars":    [3, 4, 6, 9, 11, 12],
            "Mercury": [3, 5, 6, 9, 11],
            "Jupiter": [5, 8, 9, 10, 11],
            "Venus":   [1, 2, 3, 4, 5, 8, 9, 10, 11],
            "Saturn":  [3, 4, 5, 8, 9, 10, 11],
            "Lagna":   [1, 2, 3, 4, 5, 8, 9, 11],
        },
        "Saturn": {
            "Sun":     [1, 2, 4, 7, 8, 10, 11],
            "Moon":    [3, 6, 11],
            "Mars":    [3, 5, 6, 10, 11, 12],
            "Mercury": [6, 8, 9, 10, 11, 12],
            "Jupiter": [5, 6, 11, 12],
            "Venus":   [6, 11, 12],
            "Saturn":  [3, 5, 6, 11],
            "Lagna":   [1, 3, 4, 6, 10, 11],
        },
    }

    result: dict[str, list[int]] = {}
    sarva = [0] * 12

    for planet_name, contributor_map in BENEFIC_HOUSES.items():
        bindus = [0] * 12

        for contributor, benefic_rel_houses in contributor_map.items():
            contrib_sign = planet_signs.get(contributor)
            if contrib_sign is None:
                continue

            for rel_h in benefic_rel_houses:
                abs_sign_0based = (contrib_sign - 1 + rel_h - 1) % 12
                bindus[abs_sign_0based] += 1

        result[planet_name] = bindus
        sarva = [sarva[i] + bindus[i] for i in range(12)]

    result["SARVA"] = sarva
    return result


def _build_ashtakavarga_per_varga_rows(
    bav_varga: dict[str, list[int]],
    varga: str,
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    computed_at: str,
    eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Build chart_facts rows for per-varga ashtakavarga.

    fact_category = "ashtakavarga_bindu_per_varga"
      subject = "{PLANET_CODE}-HOUSE_{N}", fact_key = varga (e.g. "D9")
    fact_category = "ashtakavarga_pinda_sarva_per_varga"
      subject = graha code, fact_key = varga
    """
    rows: list[dict[str, Any]] = []

    # Values sourced from the graha SSoT (brahmagyan/graha_vocabulary) rather
    # than hardcoded literals — ADHIṢṬHĀNA Lane A2 (found via the full-tree
    # census; not one of the originally-enumerated retirement targets).
    # "SARVA" is the ashtakavarga aggregate row, not a graha.
    planet_subjects = {
        name: norm_graha(name)
        for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    }
    planet_subjects["SARVA"] = "SARVA"

    # Verify SARVA = 337
    sarva_list = bav_varga.get("SARVA", [])
    sarva_total = sum(sarva_list)
    if abs(sarva_total - SARVA_BINDU_TOTAL) > 2:
        logging.warning(
            "[ga_strength_writer] varga=%s SARVA=%d expected=%d (floored_sarva_mismatch)",
            varga, sarva_total, SARVA_BINDU_TOTAL,
        )
        bindu_verif = "floored_sarva_mismatch"
    else:
        # M-22 fix: same class as _verify_ashtakavarga above — a single
        # structural invariant (SARVA sum=337) is a real check, but not an
        # independent second computation; the src_calc label two lines
        # below already honestly says "python_heuristic_approximation".
        # Demoted to single_pass to match.
        bindu_verif = "single_pass"

    src_calc = f"python_heuristic_approximation.ashtakavarga_per_varga/{eng_ver}"

    for planet_name, subject in planet_subjects.items():
        bindus_list = bav_varga.get(planet_name, [0] * 12)

        # Per-house bindu rows
        for h_idx, bindus in enumerate(bindus_list):
            house_num = h_idx + 1
            compound_subject = f"{subject}-HOUSE_{house_num}"
            cat = "ashtakavarga_bindu_per_varga"

            fid = _fact_id(cat, compound_subject, varga, chart_id, ayanamsha_id, build_id)
            cref = _citation_ref(cat, compound_subject, varga, chart_id, ayanamsha_id, eng_ver)
            rows.append({
                "fact_id": fid,
                "chart_id": chart_id,
                "ayanamsha_id": ayanamsha_id,
                "build_id": build_id,
                "fact_category": cat,
                "fact_subject": compound_subject,
                "fact_key": varga,
                "fact_value_text": None,
                "fact_value_num": float(bindus),
                "fact_value_jsonb": None,
                "unit": "bindu",
                "citation_ref": cref,
                "citation_human": (
                    f"{planet_name} ashtakavarga house {house_num} in {varga}: "
                    f"{int(bindus)} bindu ({ayanamsha_id})."
                ),
                "source_calculation": src_calc,
                "verification_pass_status": bindu_verif,
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

        # Pinda sarva row
        pinda_cat = "ashtakavarga_pinda_sarva_per_varga"
        pinda_val = sum(bindus_list)
        fid2 = _fact_id(pinda_cat, subject, varga, chart_id, ayanamsha_id, build_id)
        cref2 = _citation_ref(pinda_cat, subject, varga, chart_id, ayanamsha_id, eng_ver)
        rows.append({
            "fact_id": fid2,
            "chart_id": chart_id,
            "ayanamsha_id": ayanamsha_id,
            "build_id": build_id,
            "fact_category": pinda_cat,
            "fact_subject": subject,
            "fact_key": varga,
            "fact_value_text": None,
            "fact_value_num": float(pinda_val),
            "fact_value_jsonb": None,
            "unit": "bindu",
            "citation_ref": cref2,
            "citation_human": (
                f"{planet_name} sarva pinda in {varga}: {int(pinda_val)} ({ayanamsha_id})."
            ),
            "source_calculation": src_calc,
            "verification_pass_status": bindu_verif,
            "engine_version": eng_ver,
            "computed_at": computed_at,
        })

    return rows


# ── Amendment 1: Positional Shadbala for gap-vargas ───────────────────────────

# Dignity → rupa mapping for sthana bala (positional component)
_DIGNITY_TO_RUPA: dict[str, float] = {
    "exalted": 3.0,
    "own_sign": 2.0,
    "moolatrikona": 2.0,
    "friend": 1.5,
    "neutral": 1.0,
    "enemy": 0.5,
    "debilitated": 0.0,
}


def _build_positional_components_per_varga_rows(
    conn: Any,
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    computed_at: str,
    eng_ver: str,
    gap_vargas: list[str],
    verif_status: str,
) -> list[dict[str, Any]]:
    """
    Build sthana and drik bala floor rows for gap vargas (D5, D6, D8, D11, D14, D15).

    For sthana bala: queries chart_divisionals for dignity_status and maps to rupa.
    For drik bala: emits a floored row (varga aspect geometry not available).
    """
    rows: list[dict[str, Any]] = []

    # Values sourced from the graha SSoT's to_title() helper
    # (brahmagyan/graha_vocabulary) rather than hardcoded literals —
    # ADHIṢṬHĀNA Lane A2 (found via the full-tree census; not one of the
    # originally-enumerated retirement targets).
    classical_subjects = {
        code: to_title(code)
        for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT")
    }

    for varga in gap_vargas:
        # Query dignity rows for this varga
        try:
            dignity_rows = conn.execute(
                """
                SELECT fact_subject, fact_value_text
                FROM chart_divisionals
                WHERE chart_id = %s
                  AND ayanamsha_id = %s
                  AND fact_category = 'varga_dignity'
                  AND fact_key = 'dignity'
                  AND varga = %s
                """,
                (chart_id, ayanamsha_id, varga),
            ).fetchall()
        except Exception as exc:
            logging.warning(
                "[ga_strength_writer] gap_varga=%s dignity query failed: %s", varga, exc
            )
            dignity_rows = []

        # Build lookup: subject_code → dignity_status
        dignity_map: dict[str, str] = {}
        for drow in dignity_rows:
            if isinstance(drow, dict):
                fact_subject = drow["fact_subject"]
                dignity_val = drow["fact_value_text"]
            else:
                fact_subject, dignity_val = drow[0], drow[1]
            # fact_subject is "{varga}.{SUBJECT_CODE}" e.g. "D5.SUN"
            parts = fact_subject.split(".")
            subject_code = parts[-1] if len(parts) >= 2 else fact_subject
            if dignity_val:
                dignity_map[subject_code] = dignity_val.lower()

        for subj_code, planet_name in classical_subjects.items():
            # ── Sthana bala per varga ──────────────────────────────────
            dignity_str = dignity_map.get(subj_code, "neutral")
            rupa_val = _DIGNITY_TO_RUPA.get(dignity_str, 1.0)
            sthana_cat = "graha_sthana_bala_per_varga"
            fid_sthana = _fact_id(sthana_cat, subj_code, varga, chart_id, ayanamsha_id, build_id)
            cref_sthana = _citation_ref(sthana_cat, subj_code, varga, chart_id, ayanamsha_id, eng_ver)
            rows.append({
                "fact_id": fid_sthana,
                "chart_id": chart_id,
                "ayanamsha_id": ayanamsha_id,
                "build_id": build_id,
                "fact_category": sthana_cat,
                "fact_subject": subj_code,
                "fact_key": varga,
                "fact_value_text": None,
                "fact_value_num": rupa_val,
                "fact_value_jsonb": None,
                "unit": "rupa",
                "citation_ref": cref_sthana,
                "citation_human": (
                    f"{planet_name} sthana bala in {varga}: {rupa_val:.1f} rupa "
                    f"(dignity={dignity_str}) ({ayanamsha_id})."
                ),
                "source_calculation": f"classical_dignity_table/{eng_ver}",
                "verification_pass_status": verif_status,
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

            # ── Drik bala per varga (floored) ──────────────────────────
            drik_cat = "graha_drik_bala_per_varga"
            fid_drik = _fact_id(drik_cat, subj_code, varga, chart_id, ayanamsha_id, build_id)
            cref_drik = _citation_ref(drik_cat, subj_code, varga, chart_id, ayanamsha_id, eng_ver)
            rows.append({
                "fact_id": fid_drik,
                "chart_id": chart_id,
                "ayanamsha_id": ayanamsha_id,
                "build_id": build_id,
                "fact_category": drik_cat,
                "fact_subject": subj_code,
                "fact_key": varga,
                "fact_value_text": "floored: drik_requires_varga_aspect_geometry",
                "fact_value_num": None,
                "fact_value_jsonb": None,
                "unit": None,
                "citation_ref": cref_drik,
                "citation_human": (
                    f"{planet_name} drik bala in {varga}: floored — "
                    f"varga aspect geometry not available ({ayanamsha_id})."
                ),
                "source_calculation": f"classical_dignity_table/{eng_ver}",
                "verification_pass_status": "floored",
                "engine_version": eng_ver,
                "computed_at": computed_at,
            })

    return rows


# ── Amendment 1: Kala/Cheshta floor rows ─────────────────────────────────────

def _build_kala_cheshta_floor_rows(
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    computed_at: str,
    eng_ver: str,
    floor_vargas: list[str],
) -> list[dict[str, Any]]:
    """
    Emit floor rows for kala_bala and cheshta_bala across all vargas.

    These components have no canonical per-varga method, so they are marked
    floored and stored for completeness and downstream L2 consumption.
    """
    rows: list[dict[str, Any]] = []

    classical_subjects = ["SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"]

    floor_categories = [
        (
            "graha_kala_bala_per_varga",
            "floored: no_canonical_per_varga_method",
            "No canonical Parashara method exists for kala bala in divisional charts.",
        ),
        (
            "graha_cheshta_bala_per_varga",
            "floored: no_canonical_per_varga_method",
            "No canonical Parashara method exists for cheshta bala in divisional charts.",
        ),
    ]

    for varga in floor_vargas:
        for subj_code in classical_subjects:
            for cat, floor_text, provenance_text in floor_categories:
                fid = _fact_id(cat, subj_code, varga, chart_id, ayanamsha_id, build_id)
                cref = _citation_ref(cat, subj_code, varga, chart_id, ayanamsha_id, eng_ver)
                rows.append({
                    "fact_id": fid,
                    "chart_id": chart_id,
                    "ayanamsha_id": ayanamsha_id,
                    "build_id": build_id,
                    "fact_category": cat,
                    "fact_subject": subj_code,
                    "fact_key": varga,
                    "fact_value_text": floor_text,
                    "fact_value_num": None,
                    "fact_value_jsonb": None,
                    "unit": None,
                    "citation_ref": cref,
                    "citation_human": (
                        f"{subj_code} {cat} in {varga}: {floor_text} ({ayanamsha_id})."
                    ),
                    "source_calculation": f"classical_floor/{eng_ver}",
                    "verification_pass_status": "floored",
                    "engine_version": eng_ver,
                    "computed_at": computed_at,
                })

    return rows


# ── chart_facts INSERT ────────────────────────────────────────────────────────

_CHART_FACTS_UPSERT_SQL = """
    INSERT INTO chart_facts
      (fact_id, chart_id, ayanamsha_id, build_id,
       fact_category, fact_subject, fact_key,
       fact_value_text, fact_value_num, fact_value_jsonb,
       unit, citation_ref, citation_human,
       source_calculation, verification_pass_status,
       engine_version, computed_at)
    VALUES
      (%(fact_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
       %(fact_category)s, %(fact_subject)s, %(fact_key)s,
       %(fact_value_text)s, %(fact_value_num)s, %(fact_value_jsonb)s,
       %(unit)s, %(citation_ref)s, %(citation_human)s,
       %(source_calculation)s, %(verification_pass_status)s,
       %(engine_version)s, %(computed_at)s)
    ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
    WHERE formula_id IS NULL
    DO UPDATE SET
      fact_id          = EXCLUDED.fact_id,
      fact_value_num   = EXCLUDED.fact_value_num,
      citation_ref     = EXCLUDED.citation_ref,
      citation_human   = EXCLUDED.citation_human,
      verification_pass_status = EXCLUDED.verification_pass_status,
      engine_version   = EXCLUDED.engine_version,
      computed_at      = EXCLUDED.computed_at
"""


def _insert_chart_facts_rows(conn: Any, rows: list[dict[str, Any]]) -> int:
    # Idempotency: replace this chart's prior rows for the scope being written so a
    # rebuild under a new build_id replaces instead of accreting.
    replace_prior_chart_facts(conn, rows)
    if not rows:
        return 0
    # Batched executemany (same SQL text/params as the prior per-row conn.execute()
    # loop — perf-pre-D3: ~13k rows of single-row round trips was the dominant cost
    # in this writer's ~130s p50; batching removes the per-row network round trip
    # without changing a single value written).
    with conn.cursor() as cur:
        cur.executemany(_CHART_FACTS_UPSERT_SQL, rows)
    return len(rows)


# ── Main build function ───────────────────────────────────────────────────────

def build_ga_strength(
    chart_id: str,
    build_id: str | None = None,
    *,
    conn: Any = None,
    birth_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build ga_strength (shadbala + ashtakavarga + bhava_bala) for chart_id
    across all 5 canonical ayanamshas.

    Two-pass verification: algebraic invariants (shadbala sub-sum, ashtakavarga
    sarva total = 337) must pass before any row is committed.

    Raises RuntimeError on FORENSIC gate failure or TwoPassVerificationError
    on divergence.
    """
    import uuid
    if build_id is None:
        build_id = str(uuid.uuid4())

    from contextlib import nullcontext
    owns_conn = conn is None

    bp = resolve_birth_params(chart_id, birth_params)
    computed_at = datetime.now(timezone.utc).isoformat()
    eng_ver = ENGINE_VERSION

    summary: dict[str, Any] = {
        "chart_id": chart_id,
        "build_id": build_id,
        "ayanamshas": {},
        "total_chart_facts_rows": 0,
        "forensic_pass": False,
        "two_pass_verified": False,
    }

    logger.info(
        "[ga_strength_writer] Starting build chart_id=%s build_id=%s",
        chart_id, build_id,
    )

    with (_conn() if owns_conn else nullcontext(conn)) as conn:
        for canonical_id, adapter_id in CANONICAL_AYANAMSHAS.items():
            logger.info("[ga_strength_writer] Computing ayanamsha=%s", canonical_id)

            chart_output = compute_chart(inputs=bp, ayanamsha_id=adapter_id)

            # FORENSIC gate — native-anchored; asserted only for the native (Phase 3B).
            if chart_id == CANONICAL_CHART_ID:
                forensic_gate(chart_output, canonical_id)
            summary["forensic_pass"] = True

            # jd_ut + place feed PyJHora's real shadbala/vimsopaka/ashtakavarga
            # directly (M-1/M-2/M-3 fix) — jd_ut comes straight from this same
            # compute_chart() call's provenance so it is bit-for-bit the jd
            # already verified against FORENSIC for this ayanamsha/iteration.
            _jd_ut = float(chart_output["provenance"]["jd_ut"])
            _lat = float(bp["latitude_deg"])
            _lon = float(bp["longitude_deg"])
            _tz = float(bp["tz_offset_hours"])

            # ── Derive strength values ──────────────────────────────────
            shadbala = _derive_shadbala_from_positions(
                chart_output, canonical_id, jd_ut=_jd_ut, lat=_lat, lon=_lon, tz=_tz,
            )
            ishta_kashta = _derive_ishta_kashta(shadbala, _jd_ut, canonical_id, lat=_lat, lon=_lon, tz=_tz)
            vimsopaka = _derive_vimsopaka(_jd_ut, canonical_id, lat=_lat, lon=_lon, tz=_tz)
            av_result = _derive_ashtakavarga(_jd_ut, canonical_id, lat=_lat, lon=_lon, tz=_tz)
            bav = av_result["bindus"]
            av_pinda = av_result["pinda"]
            # CR-99a: trikoṇa + ekādhipatya śodhana grids (sign-keyed), derived
            # from the SAME raw bindus (no bindu VALUE recompute — §L.3 baseline).
            av_grids = _derive_ashtakavarga_shodhana_grids(
                _jd_ut, canonical_id, lat=_lat, lon=_lon, tz=_tz,
            )
            # CR-103: bhāva bala via PyJHora library (no hand-roll); documented
            # 3-source approximation stamped inside _build_bhava_bala_rows.
            bhava_bala = _derive_bhava_bala(_jd_ut, canonical_id, lat=_lat, lon=_lon, tz=_tz)

            # ── Two-pass verification ───────────────────────────────────
            try:
                sb_verif = _verify_shadbala(shadbala)
                av_verif = _verify_ashtakavarga(bav)
                # M-22 fix: this previously hardcoded verif_status =
                # "two_pass_verified" regardless of what sb_verif/av_verif
                # actually returned (both variables were computed then
                # discarded) — the literal lied about the tier even when
                # the verifiers themselves (now correctly, post-M-1/M-3 fix)
                # report "single_pass". The row-level stamp must reflect
                # the WORSE (lowest-confidence) of the two verifier
                # outputs, not an unconditional top tier.
                _TIER_RANK = {"two_pass_verified": 2, "single_pass": 1, "documented_approximation": 0}
                verif_status = min(
                    (sb_verif, av_verif), key=lambda t: _TIER_RANK.get(t, 0),
                )
                summary["two_pass_verified"] = (_TIER_RANK.get(verif_status, 0) >= 2)
                logger.info(
                    "[ga_strength_writer] verification PASS (%s): "
                    "shadbala=%s ashtakavarga=%s -> row_verif_status=%s",
                    canonical_id, sb_verif, av_verif, verif_status,
                )
            except TwoPassVerificationError as exc:
                logger.error("[ga_strength_writer] TWO-PASS DIVERGENCE: %s", exc)
                verif_status = "divergent_flagged"
                # Do NOT commit any rows — halt per brief §6.2
                raise

            # ── Build rows ─────────────────────────────────────────────
            all_rows: list[dict[str, Any]] = []
            all_rows.extend(_build_shadbala_rows(
                shadbala, ishta_kashta, vimsopaka,
                chart_id, build_id, canonical_id,
                computed_at, eng_ver, verif_status,
            ))
            all_rows.extend(_build_ashtakavarga_rows(
                bav, av_pinda, chart_id, build_id, canonical_id,
                computed_at, eng_ver, verif_status, grids=av_grids,
            ))
            all_rows.extend(_build_bhava_bala_rows(
                bhava_bala, chart_id, build_id, canonical_id,
                computed_at, eng_ver, verif_status,
            ))

            # ── Amendment 1: Per-varga strength enrichment ─────────────────────────────
            SHODASAVARGA_MINUS_D1 = ["D2","D3","D4","D7","D9","D10","D12","D16","D20","D24","D27","D30","D40","D45","D60"]
            for varga in SHODASAVARGA_MINUS_D1:
                bav_varga = _derive_ashtakavarga_for_varga(conn, chart_id, canonical_id, varga)
                if bav_varga:
                    all_rows.extend(_build_ashtakavarga_per_varga_rows(
                        bav_varga, varga, chart_id, build_id, canonical_id, computed_at, eng_ver
                    ))
                else:
                    logging.warning("[ga_strength_writer] varga=%s missing positions; skipping per-varga AV", varga)

            GAP_VARGAS = ["D5","D6","D8","D11","D14","D15"]
            all_rows.extend(_build_positional_components_per_varga_rows(
                conn, chart_id, build_id, canonical_id, computed_at, eng_ver, GAP_VARGAS, verif_status
            ))

            # ── Amendment BA-P3A: per-varga sthana bala for full Shodasavarga ──────────────
            # Sthana bala (dignity-mapped) for all 15 shodasavarga vargas (D2-D60),
            # label='computed_extension' per canonical-or-floor rule.
            # BPHS Vimshopaka-bala chapter: sthana bala varies per varga per dignity.
            all_rows.extend(_build_positional_components_per_varga_rows(
                conn, chart_id, build_id, canonical_id, computed_at, eng_ver,
                SHODASAVARGA_MINUS_D1, "computed_extension",
            ))

            FLOOR_VARGAS = SHODASAVARGA_MINUS_D1 + GAP_VARGAS
            all_rows.extend(_build_kala_cheshta_floor_rows(
                chart_id, build_id, canonical_id, computed_at, eng_ver, FLOOR_VARGAS
            ))

            # ── Insert ──────────────────────────────────────────────────
            cf_count = _insert_chart_facts_rows(conn, all_rows)

            summary["ayanamshas"][canonical_id] = {
                "chart_facts_rows": cf_count,
                "shadbala_grahas": len(shadbala),
                "ashtakavarga_rows": len([r for r in all_rows
                                          if r["fact_category"].startswith("ashtakavarga")]),
                "bhava_bala_rows": len([r for r in all_rows
                                        if r["fact_category"].startswith("house_bhava_bala")]),
            }
            summary["total_chart_facts_rows"] += cf_count

            logger.info(
                "[ga_strength_writer] ayanamsha=%s cf_rows=%d",
                canonical_id, cf_count,
            )

        if owns_conn:
            conn.commit()

    # Update asset_throughput
    if owns_conn:
        _update_asset_throughput_strength(
            chart_id=chart_id,
            build_id=build_id,
            row_count=summary["total_chart_facts_rows"],
        )

    logger.info(
        "[ga_strength_writer] COMPLETE. Total cf=%d two_pass=%s",
        summary["total_chart_facts_rows"],
        summary["two_pass_verified"],
    )
    return summary


def _update_asset_throughput_strength(
    chart_id: str,
    build_id: str,
    row_count: int,
) -> None:
    with _conn() as conn:
        update_asset_throughput(conn, "ga_strength", chart_id, build_id, row_count)
