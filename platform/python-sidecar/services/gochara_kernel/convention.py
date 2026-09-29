"""Convention vector, relation tables, orbs and tolerances (WP1_CONTRACTS.md).

Everything here is pinned by WP1_CONTRACTS.md and the ruling sheet; the kernel
never invents an orb, a tolerance, or a dṛṣṭi angle.
"""
from __future__ import annotations

import hashlib
import json

# ── Convention vector (WP1_CONTRACTS.md §1.1) ────────────────────────────────

CONVENTION_VECTOR = {
    "zodiac": "sidereal",
    "ayanamsha": "lahiri_chitrapaksha",
    "sidereal_method": "swe_flg_sidereal",
    "node_model": "mean",
    "node_source": "swiss_mean_node_flg_sidereal",
    "epoch_convention": "noon_ut_knot_abscissa",
    "time_scale": "ut_to_tt_swe_deltat",
    "house_system": "whole_sign",
    "ephemeris_mode": "flg_swieph",
}


def canonical_convention_id() -> str:
    """WP1_CONTRACTS.md §1.1 — canonical JSON sha256 of the pinned vector.

    `ephemeris_backend` is deliberately NOT hashed (it is an environmental
    observation, not a method choice — WP1 §1.1).
    """
    canonical = json.dumps(
        CONVENTION_VECTOR, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── Per-graha special dṛṣṭi angles (WP1_CONTRACTS.md §7 + §2.2 N-14 note) ────
# Doctrine: BPHS ch.26 (bphs_vol1_rsanthanam_djvu.txt:16496-16505); dṛṣṭi-koṇa
# graduation ch.26 śl.6-8 (:16514-16529). N-14 (RULED): Rāhu/Ketu cast NO
# dṛṣṭi — not the 7th either — so their angle set is EMPTY. The nodes remain
# full conjunction/ingress/kakṣyā/return agents and targets. This supersedes
# the served SPECIAL_DRISHTI_DEG nodal entries (services/gochara_grammar/
# primitives.py:193-194, F-29).
SPECIAL_DRISHTI_DEG: dict[str, list[float]] = {
    "Mars": [90.0, 180.0, 210.0],
    "Jupiter": [120.0, 180.0, 240.0],
    "Saturn": [60.0, 180.0, 270.0],
    "Sun": [180.0],
    "Moon": [180.0],
    "Mercury": [180.0],
    "Venus": [180.0],
    "Rahu": [],
    "Ketu": [],
}


def drishti_angles(body: str) -> tuple[float, ...]:
    """The dṛṣṭi angles `body` casts. Empty tuple for Rāhu/Ketu (N-14)."""
    return tuple(SPECIAL_DRISHTI_DEG[body])


# ── Kakṣyā lord order (WP1_CONTRACTS.md §8) ─────────────────────────────────
# The order the served code uses at BOTH code sites (gochara_grammar/
# primitives.py:625 fixture and ga_writers/ga_strength_writer.py:89-91 L1
# writer). Doctrine itself is uncited_extension=true pending WP8/M-7 (G-10):
# the honest source statement is in WP1_CONTRACTS.md §8.
KAKSHYA_LORD_ORDER: tuple[str, ...] = (
    "Saturn",   # kakṣyā 1: 0°00′–3°45′ of the sign
    "Jupiter",  # 2: 3°45′–7°30′
    "Mars",     # 3: 7°30′–11°15′
    "Sun",      # 4: 11°15′–15°00′
    "Venus",    # 5: 15°00′–18°45′
    "Mercury",  # 6: 18°45′–22°30′
    "Moon",     # 7: 22°30′–26°15′
    "Lagna",    # 8: 26°15′–30°00′
)
KAKSHYA_CELL_DEG = 3.75  # equal-eighths grid (F-27: L1's grid is the same)

# ── Orb table (WP1_CONTRACTS.md §7) ──────────────────────────────────────────
# Degree-exact contact with an orb is practice ([P]); every numeric orb is
# uncited_extension=true with orb_source named. orb_legacy_box is the activity
# baseline the projection reproduces span-aware until M-1 rules (NOT a kernel
# geometry parameter — the kernel emits episodes at orb_max_deg).
ORB_TABLE: dict[str, dict] = {
    "orb_conj_slow": {"relation": "conjunction", "body_class": "slow", "orb_max_deg": 1.0},
    "orb_conj_moon": {"relation": "conjunction", "body_class": "moon", "orb_max_deg": 3.0},
    "orb_drishti_slow": {"relation": "drishti_contact", "body_class": "slow", "orb_max_deg": 1.0},
    "orb_drishti_moon": {"relation": "drishti_contact", "body_class": "moon", "orb_max_deg": 3.0},
    "orb_return_slow": {"relation": "return", "body_class": "slow", "orb_max_deg": 0.5},
    "orb_return_moon": {"relation": "return", "body_class": "moon", "orb_max_deg": 2.0},
    "orb_kakshya": {"relation": "kakshya_cell_crossing", "body_class": "all", "orb_max_deg": 0.1},
    "orb_ingress": {"relation": "sign_ingress/nakshatra_ingress/residence", "body_class": "all", "orb_max_deg": 0.0},
}

SIGN_DEG = 30.0
NAKSHATRA_DEG = 40.0 / 3.0  # 13°20′

# ── Tolerances (WP1_CONTRACTS.md §9, pinned per relation class) ─────────────
# A dṛṣṭi exact and a conjunction exact do NOT share one ε by construction —
# the classes are pinned separately even where the numbers coincide, so M-1's
# WP8 evidence can tighten one class without silently re-pinning the other.
TOLERANCE_TABLE: dict[str, dict] = {
    "exact_slow": {"relations": ("conjunction", "drishti_contact", "return"),
                   "tolerance_arcsec": 2.0, "bracket_seconds": 300},
    "exact_moon": {"relations": ("conjunction", "drishti_contact", "return"),
                   "tolerance_arcsec": 5.0, "bracket_seconds": 60},
    "boundary_slow": {"relations": ("sign_ingress", "nakshatra_ingress", "kakshya_cell_crossing"),
                      "tolerance_arcsec": 2.0, "bracket_seconds": 300},
    "boundary_moon": {"relations": ("sign_ingress", "nakshatra_ingress", "kakshya_cell_crossing"),
                      "tolerance_arcsec": 5.0, "bracket_seconds": 60},
}

MOON_BODIES = frozenset({"Moon"})


def declared_tolerance(body: str, relation: str) -> dict:
    """The declared (tolerance_arcsec, bracket_seconds) for (body, relation)."""
    is_moon = body in MOON_BODIES
    kind = "boundary" if relation in TOLERANCE_TABLE["boundary_slow"]["relations"] else "exact"
    row = TOLERANCE_TABLE[f"{kind}_{'moon' if is_moon else 'slow'}"]
    return {"tolerance_arcsec": row["tolerance_arcsec"], "bracket_seconds": row["bracket_seconds"]}


# ── .se1 checksums (WP1_CONTRACTS.md §10 / plan §4.1) ───────────────────────
# Verbatim from WP1_CONTRACTS.md §10 (the test harness re-verifies them against
# the files on disk before any gate-grade comparison runs — F-14).
SE1_CHECKSUMS = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
    "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
}
