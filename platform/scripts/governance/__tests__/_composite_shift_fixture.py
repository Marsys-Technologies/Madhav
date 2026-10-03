"""Shared synthetic Moshier-before / .se1-after states for the COMPOSITE (label, number) rows of the ephemeris backend move.

Used by test_s_l1_hooks_expected_state.py (the ephemeris_backend_shift count entries 27 to 29, run through the REAL flip_detector) and by
test_composite_shift_check.py (the W7 hand-check script). Built from the REHEARSAL-LINUX measurement (which rows moved, and by how much)
and the SE1_SHIFT_ANALYSIS.md section 3 input-shift table; every base value is SYNTHETIC (an arbitrary degree / orb / years), so no birth
data and no native position is stored here.

Row formats are the flip_detector snapshot formats:
  chart_facts   [ayanamsha, fact_category, fact_subject, fact_key, text, num, tier]
  divisionals   [ayanamsha, varga, graha, fact_category, fact_key, text, num, sign]
"""
from __future__ import annotations

import copy

AYS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
VARGAS = [f"D{n}" for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 20, 21, 24, 27, 30, 32, 33, 40, 45, 50, 54, 60, 108, 150, 2700)]
GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Lagna"]
# SE1_SHIFT_ANALYSIS.md section 3, se1 minus Moshier, arcsec, columns Sun Moon Mars Mercury Jupiter Venus Saturn Rahu/Ketu Lagna
# (transcribed independently of evidence/composite_shift_check.py; test_composite_shift_check pins the two tables equal).
TABLE = {
    "lahiri_chitrapaksha": (0.0003, -0.6647, -0.1183, 0.0156, -0.2022, -0.0358, 0.1515, 0.0, 0.0),
    "true_chitra": (0.0002, -0.6648, -0.1184, 0.0155, -0.2023, -0.0359, 0.1514, -0.0001, -0.0001),
    "krishnamurti": (0.0003, -0.6647, -0.1183, 0.0156, -0.2022, -0.0358, 0.1515, 0.0, 0.0),
    "raman": (0.0003, -0.6647, -0.1183, 0.0156, -0.2022, -0.0358, 0.1515, 0.0, 0.0),
    "surya_siddhanta_classical": (0.0004, -0.6646, -0.1182, 0.0157, -0.2021, -0.0357, 0.1516, 0.0, 0.0),
}
COLUMN = {"Sun": 0, "Moon": 1, "Mars": 2, "Mercury": 3, "Jupiter": 4, "Venus": 5, "Saturn": 6, "Rahu": 7, "Ketu": 7, "Lagna": 8}


def shift_deg(ay, graha):
    return TABLE[ay][COLUMN[graha]] / 3600.0


SDC_SUBJECT = {"Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER", "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT", "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN"}
SDC_KEYS = {"mrityu_bhaga": "not_fired", "pushkara": "not_pushkara"}
SEVEN_SUBJECTS = ["SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"]
AYU_METHODS = ["amsayu", "nisargayu", "pindayu"]

# Which of the 90 sensitive_degree_check composite rows moved on the Linux .se1 rehearsal, and by how much (stored 4-decimal numbers).
OBS_SDC = [
    ("krishnamurti", "MOON", "mrityu_bhaga", -0.0002), ("krishnamurti", "MOON", "pushkara", -0.0002), ("krishnamurti", "SAT", "mrityu_bhaga", 0.0001),
    ("krishnamurti", "SAT", "pushkara", -0.0001), ("lahiri_chitrapaksha", "JUP", "mrityu_bhaga", 0.0001), ("lahiri_chitrapaksha", "JUP", "pushkara", 0.0001),
    ("lahiri_chitrapaksha", "MOON", "mrityu_bhaga", -0.0002), ("lahiri_chitrapaksha", "MOON", "pushkara", -0.0002), ("raman", "JUP", "mrityu_bhaga", 0.0001),
    ("raman", "JUP", "pushkara", 0.0001), ("raman", "MOON", "mrityu_bhaga", -0.0002), ("raman", "MOON", "pushkara", -0.0002),
    ("surya_siddhanta_classical", "MOON", "mrityu_bhaga", 0.0002), ("surya_siddhanta_classical", "MOON", "pushkara", 0.0002),
    ("surya_siddhanta_classical", "SAT", "mrityu_bhaga", 0.0001), ("surya_siddhanta_classical", "SAT", "pushkara", 0.0001),
    ("true_chitra", "MOON", "mrityu_bhaga", -0.0002), ("true_chitra", "MOON", "pushkara", -0.0002), ("true_chitra", "SAT", "mrityu_bhaga", 0.0001),
    ("true_chitra", "SAT", "pushkara", -0.0001),
]
# The 12 of the 120 ayurdaya composite rows that moved (stored 4-decimal years).
OBS_AYU = [
    ("krishnamurti", "AMSAYU", "total_years", -0.0001), ("lahiri_chitrapaksha", "AMSAYU", "total_years", -0.0001),
    ("lahiri_chitrapaksha", "MAR", "amsayu_contribution_years", -0.0001), ("lahiri_chitrapaksha", "MOON", "amsayu_contribution_years", -0.0001),
    ("lahiri_chitrapaksha", "PINDAYU", "total_years", -0.0001), ("raman", "AMSAYU", "total_years", -0.0001),
    ("raman", "MOON", "amsayu_contribution_years", -0.0001), ("surya_siddhanta_classical", "AMSAYU", "total_years", -0.0001),
    ("surya_siddhanta_classical", "JUP", "amsayu_contribution_years", -0.0001), ("surya_siddhanta_classical", "MOON", "amsayu_contribution_years", -0.0001),
    ("true_chitra", "AMSAYU", "total_years", -0.0001), ("true_chitra", "JUP", "nisargayu_contribution_years", 0.0001),
]


VARGA_N = [int(v[1:]) for v in VARGAS]
# the largest move any body makes (Moon, 0.6648" + the 0.00005" table slack) plus the 5e-7 deg rounding of a stored D1 degree
MAX_MOVE_DEG = (0.6648 + 0.00005) / 3600.0 + 5e-7


def clear_degree(x):
    """A synthetic natal degree in Aries at or after x that lies at least 4 x n x MAX_MOVE_DEG (varga degrees) from every sign boundary
    of every one of the 30 vargas and 0.01 deg from both Aries pushkara-navamsa edges (20, 23 1/3), so CS6 (the label-margin check)
    has nothing to say about the synthetic base state. Deterministic: steps by 1.37e-4 deg until clear."""
    x = round(x + 0.0123457, 6)
    while not (all(min((n * x) % 30.0, 30.0 - (n * x) % 30.0) > 4 * n * MAX_MOVE_DEG for n in VARGA_N)
               and min(abs(x - 20.0), abs(x - 20.0 - 30.0 / 9.0)) > 0.01):
        x = round(x + 0.000137, 6)
    return x


def _g(x, nd):
    return format(round(x, nd), f".{nd}f")


def composite_pair(*, varga_moved=True, sdc_moved=True, ayu_moved=True, varga_sun_crosses=False, varga_all_possible=False):
    """-> (before, after): two {"chart_facts": [...], "divisionals": [...]} snapshots. Everything not named moved is byte-identical.

    varga_sun_crosses: the Sun's natal degree sits right at a 1e-6 rounding boundary, so its 0.08-step shift flips the stored value (150 more rows).
    varga_all_possible: every row whose body has a non-zero input shift moves (the upper bound: the Sun, plus Rahu / Ketu / Lagna on True Chitra)."""
    div_b, div_a, fac_b, fac_a = [], [], [], []
    # ---- chart_divisionals varga_position: 5 ayanamshas x 30 vargas x 10 bodies; the varga SIGN rows ride along unchanged
    planets = {"Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    for ai, ay in enumerate(AYS):
        for gi, g in enumerate(GRAHAS):
            grid = clear_degree(3.0 + (gi * 2.9 + ai * 0.7) % 25.0)          # clear of every varga sign boundary (CS6 silent on the base)
            b = _g(grid, 6)
            d = shift_deg(ay, g)
            if not varga_moved:
                a = b
            elif g in planets:
                a = _g(grid + 0.2e-6 + d, 6)                                  # a planet shifts by >= 4.3 stored steps: the stored value always changes
            elif d != 0.0 and (varga_all_possible or (g == "Sun" and varga_sun_crosses)):
                a = _g(grid + (1e-6 if d > 0 else -1e-6), 6)                    # a sub-step shift that happens to cross a rounding boundary: one stored step
            else:
                a = b
            for v in VARGAS:
                sign = "Aries"
                div_b += [[ay, v, g, "varga_position", "sign", sign, "", sign], [ay, v, g, "varga_position", "sign_id", "", "1", sign],
                          [ay, v, g, "varga_position", "degree_in_sign", "", b, sign], [ay, v, g, "varga_position", "sign_lord", "Mars", "", sign],
                          [ay, v, g, "varga_position", "house_from_varga_lagna", "", "1", sign]]
                div_a += [[ay, v, g, "varga_position", "sign", sign, "", sign], [ay, v, g, "varga_position", "sign_id", "", "1", sign],
                          [ay, v, g, "varga_position", "degree_in_sign", "", a, sign], [ay, v, g, "varga_position", "sign_lord", "Mars", "", sign],
                          [ay, v, g, "varga_position", "house_from_varga_lagna", "", "1", sign]]
    # ---- chart_facts sensitive_degree_check: 5 ayanamshas x 9 grahas x {mrityu_bhaga, pushkara}; a text-only key rides along unchanged
    obs = {(a, s, k): d for a, s, k, d in OBS_SDC} if sdc_moved else {}
    for ai, ay in enumerate(AYS):
        for gi, (g, s) in enumerate(SDC_SUBJECT.items()):
            for ki, (key, label) in enumerate(SDC_KEYS.items()):
                base = round(1.0 + gi * 2.3 + ki * 0.9 + ai * 0.37, 4)
                fac_b.append([ay, "sensitive_degree_check", s, key, label, _g(base, 4), "single"])
                fac_a.append([ay, "sensitive_degree_check", s, key, label, _g(base + obs.get((ay, s, key), 0.0), 4), "single"])
            fac_b.append([ay, "sensitive_degree_check", s, "gandanta", "not_gandanta", "", "single"])
            fac_a.append([ay, "sensitive_degree_check", s, "gandanta", "not_gandanta", "", "single"])
    # ---- chart_facts ayurdaya: 7 grahas x 3 methods + 3 totals per ayanamsha = 24 composite rows, plus the two class rows
    obs = {(a, s, k): d for a, s, k, d in OBS_AYU} if ayu_moved else {}
    for ai, ay in enumerate(AYS):
        for si, s in enumerate(SEVEN_SUBJECTS):
            for mi, m in enumerate(AYU_METHODS):
                key = f"{m}_contribution_years"
                base = round(2.0 + si * 1.7 + mi * 0.45 + ai * 0.21, 4)
                fac_b.append([ay, "ayurdaya", s, key, m, _g(base, 4), "single"])
                fac_a.append([ay, "ayurdaya", s, key, m, _g(base + obs.get((ay, s, key), 0.0), 4), "single"])
        for mi, m in enumerate(AYU_METHODS):
            base = round(30.0 + mi * 3.1 + ai * 0.2, 4)
            fac_b.append([ay, "ayurdaya", m.upper(), "total_years", "madhyayu", _g(base, 4), "single"])
            fac_a.append([ay, "ayurdaya", m.upper(), "total_years", "madhyayu", _g(base + obs.get((ay, m.upper(), "total_years"), 0.0), 4), "single"])
        fac_b += [[ay, "ayurdaya", "CHART", "applicable_method", "pindayu", "", "single"], [ay, "ayurdaya", "CHART", "maraka_grahas", "Mars,Saturn", "", "single"]]
        fac_a += [[ay, "ayurdaya", "CHART", "applicable_method", "pindayu", "", "single"], [ay, "ayurdaya", "CHART", "maraka_grahas", "Mars,Saturn", "", "single"]]
    return {"chart_facts": fac_b, "divisionals": div_b}, {"chart_facts": fac_a, "divisionals": div_a}


def clone(state):
    return copy.deepcopy(state)
