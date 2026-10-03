#!/usr/bin/env python3
"""composite_shift_check.py -- W7 hand-check for the composite (label, number) rows the Moshier -> .se1 backend move shifts.

WHY THIS EXISTS (the detector's limit, stated exactly). flip_detector.py reads a row's value as the pair (text, number). A row
that carries BOTH a class label and a continuous number (chart_divisionals varga_position/degree_in_sign: the varga sign + the natal
degree; chart_facts sensitive_degree_check/mrityu_bhaga and /pushkara: fired / not_fired + the orb in degrees; chart_facts
ayurdaya contributions and totals: the longevity class + the years) is classed `class_text` (kind_of: any non-empty text wins), so
ANY move of the number counts as a `value` change. The detector therefore cannot say "the label did not change and the number moved by
at most X". What ephemeris_backend_shift.json CAN express for these rows is a COUNT bound on `value` changes per (table, category,
fact_keys); this script is the other half and is run by hand at W7 on two flip_detector snapshots:

  CS1  the row sets of the three families are identical before and after (nothing appeared, nothing disappeared)
  CS2  every LABEL (text, or the sign column for chart_divisionals) is identical on every paired row: a class flip is a failure
  CS3  every row whose number moved stays inside its PHYSICAL bound (below)
  CS4  every row of the family that is NOT a composite (varga_position sign / sign_id / sign_lord / house_from_varga_lagna /
       formula_id; the other sensitive_degree_check keys; ayurdaya applicable_method / maraka_grahas) is exactly unchanged
  CS5  the number of changed composite rows per family lies in the count bound the hook declares (derive_count_bounds())
  CS6  the "label MUST NOT change" expectation of CS2 is itself DERIVED, row by row, from the BEFORE state: every composite label
       sits further from its class boundary than the physical shift can carry it (label_margins(), below). A label within its
       shift of a boundary is a failure for a human: there CS2's strictness would be an assumption, not physics.

PHYSICAL BOUNDS (derived, not fitted to the rehearsal). The only input that moves is the planetary longitude, by the measured
Moshier -> .se1 difference of the three SHA-pinned .se1 files (SE1_SHIFT_ANALYSIS.md section 3 table, 4 decimals of an arcsecond;
/Users/Dev/suvarna-evidence/Ephemeris/SE1_SHIFT_ANALYSIS.md sha256 22564b863fc7cb3713e5d4b5d88ca5dc7376532fd93a9faa6461c99689ac3403).
The stored number is a function of that longitude with a known slope, rounded to a known step, so |after - before| <= slope * shift + step:
  varga_position degree_in_sign   ga_vargas_writer._compute_varga_positions: deg_in_sign = d1_long % 30.0 for EVERY varga (it is the
                                  NATAL degree in sign, stored round(x, 6) in all 30 vargas): slope 1, step 1e-6 deg. The varga
                                  multiplier (D-n amplifies a longitude x n) acts on the varga SIGN, which CS2 checks does not flip;
                                  it does not act on this number.
  sensitive_degree_check          mrityu_bhaga / pushkara: number = orb_deg / bhaga_orb_deg = abs(degree_in_sign - table degree),
                                  stored round(x, 4): slope 1, step 1e-4 deg.
  ayurdaya contributions          PyJHora aayu with apply_haranas=False: amsayu method 2 = (longitude*60/200) mod 12 -> slope 0.3 y/deg;
                                  pindayu = full_longevity[b]/360 y/deg (arc <= 180 branch: minus, > 180: plus); nisargayu likewise
                                  with its own full-longevity table; stored round(x, 4) y: step 1e-4.
  ayurdaya total_years            round(sum of the 7 unrounded contributions + lagna_years, 4), lagna_years = longitude/30: slope =
                                  sum of the 7 contribution slopes + 1/30 on the Lagna shift, step 1e-4.
The mod-12 wrap of amsayu and the 180-degree branch of pindayu/nisargayu are discontinuities: a longitude within its shift of one would
move a contribution by years, not 1e-4. That is fail-closed here (CS3 reports it for a human); it did not occur in the rehearsal.

LABEL MARGINS (CS6: where the varga multiplier acts). Each label is a step function of the longitude with known boundaries, so it can
change only if the longitude lies within its shift of a boundary:
  varga_position (the varga SIGN)  every one of the 30 vargas of ga_vargas_writer puts its sign boundaries at multiples of 30/n of the D1
                                  longitude (D1 30, D2 hora 15, D3 drekkana 10, all others _compute_general_varga: equal amsas of 30/n).
                                  In VARGA degrees: the D-n longitude n*lambda moves by n * shift (the x n amplification, up to x2700), so
                                  per varga: margin = distance of (n * lambda) mod 30 to 0 / 30, bound = n * (shift + table slack + the
                                  5e-7 deg rounding of the stored D1 degree). lambda = D1 sign * 30 + the stored D1 degree_in_sign.
  sensitive_degree_check           mrityu_bhaga fired iff orb <= the graha's PyJHora tolerance (1/3, 2/3 or 1/4 deg): margin = |orb - tol|;
                                  pushkara fired iff the degree is inside the pushkara navamsa [start, start + 30/9) OR the bhaga orb <= 0.5:
                                  margins = |bhaga_orb - 0.5| and the degree's distance to both navamsa edges. Bound = shift + slack + the
                                  stored rounding (half a 1e-4 step for the orb, 5e-7 for the D1 degree).
  ayurdaya total_years            alpayu < 32 <= madhyayu < 64 <= purnayu (ga_ayurdaya_writer.classify_ayus): margin = distance of the total to
                                  32 / 64, bound = the total's CS3 bound. The contribution rows' label is the method name: no boundary.

COUNT BOUND (CS5 and the hook): max = rows whose body has a NON-ZERO input shift (the only way a row can move at all); min = rows whose
shift is at least one rounding step even after the 4-decimal table slack (an interval longer than the step always contains a rounding
boundary, so the stored value MUST change). Everything else may or may not cross a boundary and is left free.

Usage (offline: two snapshots written by `flip_detector.py --snapshot`; no database, no network, nothing written):
  composite_shift_check.py --compare BEFORE.json.gz AFTER.json.gz       # exit 0 pass, 2 fail
  composite_shift_check.py --derive                                     # prints the count bounds the hook must carry
  composite_shift_check.py --margins BEFORE.json.gz                     # CS6 alone: per family, rows checked / within bound / min margin/bound
Stores and prints derived chart facts only (no birth data): the report names counts and offending keys, never a position.
"""
from __future__ import annotations

import collections
import gzip
import json
import sys

CANONICAL = "482012f1-710e-4a25-994a-93821f5871aa"
AYAS = ("lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical")
VARGAS = tuple(f"D{n}" for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 20, 21, 24, 27, 30, 32, 33, 40, 45, 50, 54, 60, 108, 150, 2700))

# Input shift se1 minus Moshier, |arcsec|, per ayanamsha, columns in BODIES order. SE1_SHIFT_ANALYSIS.md section 3 table, verbatim to 4 decimals.
# Rahu/Ketu are the MEAN node (analytic, no ephemeris file): 0 exactly; True Chitra carries -0.0001 through its ayanamsha value. Lagna likewise.
BODIES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Lagna")
SHIFT_ARCSEC = {
    "lahiri_chitrapaksha":       (0.0003, 0.6647, 0.1183, 0.0156, 0.2022, 0.0358, 0.1515, 0.0, 0.0, 0.0),
    "true_chitra":               (0.0002, 0.6648, 0.1184, 0.0155, 0.2023, 0.0359, 0.1514, 0.0001, 0.0001, 0.0001),
    "krishnamurti":              (0.0003, 0.6647, 0.1183, 0.0156, 0.2022, 0.0358, 0.1515, 0.0, 0.0, 0.0),
    "raman":                     (0.0003, 0.6647, 0.1183, 0.0156, 0.2022, 0.0358, 0.1515, 0.0, 0.0, 0.0),
    "surya_siddhanta_classical": (0.0004, 0.6646, 0.1182, 0.0157, 0.2021, 0.0357, 0.1516, 0.0, 0.0, 0.0),
}
TABLE_SLACK_ARCSEC = 0.00005          # the table is rounded to 4 decimals: +-0.00005
ARCSEC_PER_DEG = 3600.0

VARGA_STEP_DEG = 1e-6                 # round(deg_in_sign, 6)
SDC_STEP_DEG = 1e-4                   # round(orb, 4)
AYU_STEP_YEARS = 1e-4                 # round(years, 4)

# divisionals graha column <-> chart_facts subject code (graha_vocabulary SSoT) <-> BODIES
DIV_BODY = {b: b for b in BODIES}
FACT_BODY = {"SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MER": "Mercury", "JUP": "Jupiter", "VEN": "Venus", "SAT": "Saturn",
             "RAH_MEAN": "Rahu", "KET_MEAN": "Ketu", "LAGNA": "Lagna"}
SEVEN = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT")
# PyJHora const.pindayu_full_longevity_of_planets / nisargayu_full_longevity_of_planets, Sun..Saturn (the writer docstring cites them;
# the test pins these two tuples to jhora.const so they cannot drift).
PINDAYU_FULL = (19, 25, 15, 12, 15, 21, 20)
NISARGAYU_FULL = (20, 1, 2, 9, 18, 20, 50)
AMSAYU_SLOPE = 60.0 / 200.0           # years per degree, method 2

# CS6 label boundaries (the writers delegate to PyJHora const; the test pins these to jhora.const and to the writers' own code).
SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
D1_DEG_ROUNDING = 5e-7                # half of the 1e-6 step of the stored D1 degree_in_sign
ORB_ROUNDING = 5e-5                   # half of the 1e-4 step of the stored orb
MRITYU_TOL = {"Sun": 1 / 3, "Moon": 2 / 3, "Mars": 0.25, "Mercury": 2 / 3, "Jupiter": 0.25, "Venus": 0.25, "Saturn": 0.25,
              "Rahu": 0.25, "Ketu": 0.25}   # const.mrityu_bhaga_tolerances, columns 0..8 (ga_sensitive_degree_writer._MB_COL)
PUSHKARA_NAVAMSA_START = (20, 20 / 3, 50 / 3, 0) * 3   # const.pushkara_navamsa, per sign
PUSHKARA_NAVAMSA_ARC = 30.0 / 9.0
PUSHKARA_BHAGA_ORB = 0.5
AYUS_BOUNDARIES = (32.0, 64.0)        # ga_ayurdaya_writer.classify_ayus

SDC_KEYS = ("mrityu_bhaga", "pushkara")
AYU_CONTRIB_KEYS = {"amsayu_contribution_years": "amsayu", "nisargayu_contribution_years": "nisargayu", "pindayu_contribution_years": "pindayu"}
AYU_TOTAL_SUBJECT = {"AMSAYU": "amsayu", "NISARGAYU": "nisargayu", "PINDAYU": "pindayu"}
AYU_KEYS = tuple(AYU_CONTRIB_KEYS) + ("total_years",)


def shift_deg(ay, body):
    return SHIFT_ARCSEC[ay][BODIES.index(body)] / ARCSEC_PER_DEG


def _slack_deg():
    return TABLE_SLACK_ARCSEC / ARCSEC_PER_DEG


def _sure(ay, body, step_deg, slope=1.0):
    """The shift is at least one rounding step even at the low end of the 4-decimal table entry: the stored value MUST change."""
    s = SHIFT_ARCSEC[ay][BODIES.index(body)]
    return s > 0 and slope * (s - TABLE_SLACK_ARCSEC) / ARCSEC_PER_DEG >= step_deg


def _possible(ay, body):
    return SHIFT_ARCSEC[ay][BODIES.index(body)] > 0


def _slope(method, subject):
    i = SEVEN.index(subject)
    return {"amsayu": AMSAYU_SLOPE, "pindayu": PINDAYU_FULL[i] / 360.0, "nisargayu": NISARGAYU_FULL[i] / 360.0}[method]


def derive_count_bounds():
    """{family: (min, max)} of changed `value` rows per family, derived from the shift table and the rounding steps (see the module docstring)."""
    var_min = sum(len(VARGAS) for ay in AYAS for b in BODIES if _sure(ay, b, VARGA_STEP_DEG))
    var_max = sum(len(VARGAS) for ay in AYAS for b in BODIES if _possible(ay, b))
    sdc_bodies = [b for b in BODIES if b != "Lagna"]
    sdc_min = sum(len(SDC_KEYS) for ay in AYAS for b in sdc_bodies if _sure(ay, b, SDC_STEP_DEG))
    sdc_max = sum(len(SDC_KEYS) for ay in AYAS for b in sdc_bodies if _possible(ay, b))
    ayu_min = 0
    for ay in AYAS:
        for s in SEVEN:
            for m in ("amsayu", "pindayu", "nisargayu"):
                if _sure(ay, FACT_BODY[s], AYU_STEP_YEARS, _slope(m, s)):
                    ayu_min += 1
    ayu_max = sum(1 for ay in AYAS for s in SEVEN for _m in AYU_CONTRIB_KEYS if _possible(ay, FACT_BODY[s])) + len(AYAS) * len(AYU_TOTAL_SUBJECT)
    return {"varga_position": (var_min, var_max), "sensitive_degree_check": (sdc_min, sdc_max), "ayurdaya": (ayu_min, ayu_max)}


# ------------------------------------------------------------------------------------------------ pairing
def _num(x):
    return None if x in ("", None) else float(x)


def _occ(rows, keyfn, valfn, keep):
    m = collections.defaultdict(list)
    for r in rows:
        if keep(r):
            m[keyfn(r)].append(valfn(r))
    for k in m:
        m[k].sort(key=lambda v: (v[0] or "", v[1] if v[1] is not None else float("-inf")))
    return m


def _families(state):
    """Key -> sorted [(label, number)] for the three composite families PLUS every other row of the same categories."""
    div = _occ(state["divisionals"], lambda r: (r[0], r[1], r[2], r[3], r[4]), lambda r: (r[5] or r[7], _num(r[6])), lambda r: r[3] == "varga_position")
    fac = _occ(state["chart_facts"], lambda r: (r[0], r[1], r[2], r[3]), lambda r: (r[4], _num(r[5])), lambda r: r[1] in ("sensitive_degree_check", "ayurdaya"))
    return div, fac


def _bound_varga(ay, body):
    return shift_deg(ay, body) + _slack_deg() + VARGA_STEP_DEG


def _bound_sdc(ay, body):
    return shift_deg(ay, body) + _slack_deg() + SDC_STEP_DEG


def _bound_ayu(ay, key, subject):
    if key in AYU_CONTRIB_KEYS:
        m = AYU_CONTRIB_KEYS[key]
        return _slope(m, subject) * (shift_deg(ay, FACT_BODY[subject]) + _slack_deg()) + AYU_STEP_YEARS
    m = AYU_TOTAL_SUBJECT[subject]
    tot = sum(_slope(m, s) * (shift_deg(ay, FACT_BODY[s]) + _slack_deg()) for s in SEVEN)
    return tot + (shift_deg(ay, "Lagna") + _slack_deg()) / 30.0 + AYU_STEP_YEARS


def _d1_longitudes(state):
    """{(ayanamsha, body): D1 sidereal longitude} from the D1 varga_position degree_in_sign rows (sign column + stored degree)."""
    out = {}
    for r in state["divisionals"]:
        if r[1] == "D1" and r[3] == "varga_position" and r[4] == "degree_in_sign" and r[7] in SIGNS and _num(r[6]) is not None:
            out[(r[0], r[2])] = SIGNS.index(r[7]) * 30.0 + float(r[6])
    return out


def _edge_distance(x, period=30.0):
    x = x % period
    return min(x, period - x)


def label_margins(before):
    """CS6: [(family, key, margin, bound)] for every composite label of `before`; the label can change only where margin <= bound.

    varga_position works in VARGA degrees: the D-n longitude n*lambda moves by n*shift, so margin and bound both carry the factor n."""
    lam = _d1_longitudes(before)
    out = []
    for (ay, body), x in sorted(lam.items()):
        if ay not in SHIFT_ARCSEC or body not in BODIES:
            continue
        move = shift_deg(ay, body) + _slack_deg() + D1_DEG_ROUNDING
        for v in VARGAS:
            n = int(v[1:])
            out.append(("varga_position", (ay, v, body), _edge_distance(n * x), n * move))
    for r in before["chart_facts"]:
        ay, cat, subj, key, num = r[0], r[1], r[2], r[3], _num(r[5])
        if ay not in SHIFT_ARCSEC or num is None:
            continue
        if cat == "sensitive_degree_check" and key in SDC_KEYS and subj in FACT_BODY and subj != "LAGNA":
            body = FACT_BODY[subj]
            move = shift_deg(ay, body) + _slack_deg()
            if key == "mrityu_bhaga":
                out.append(("sensitive_degree_check", (ay, subj, key, "tolerance"), abs(num - MRITYU_TOL[body]), move + ORB_ROUNDING))
                continue
            out.append(("sensitive_degree_check", (ay, subj, key, "bhaga_orb"), abs(num - PUSHKARA_BHAGA_ORB), move + ORB_ROUNDING))
            if (ay, body) not in lam:
                out.append(("sensitive_degree_check", (ay, subj, key, "navamsa_no_d1_row"), 0.0, move))   # fail-closed: no degree, no proof
                continue
            sign_idx, deg = int(lam[(ay, body)] // 30.0) % 12, lam[(ay, body)] % 30.0
            start = PUSHKARA_NAVAMSA_START[sign_idx]
            out.append(("sensitive_degree_check", (ay, subj, key, "navamsa_edge"),
                        min(abs(deg - start), abs(deg - (start + PUSHKARA_NAVAMSA_ARC))), move + D1_DEG_ROUNDING))
        elif cat == "ayurdaya" and key == "total_years" and subj in AYU_TOTAL_SUBJECT:
            out.append(("ayurdaya", (ay, subj, key, "class"), min(abs(num - b) for b in AYUS_BOUNDARIES), _bound_ayu(ay, key, subj)))
    return out


def margin_summary(before):
    """{family: {"rows", "within_bound", "min_ratio"}} -- counts and margin/bound ratios only, never a position."""
    s = {}
    for fam, _k, margin, bound in label_margins(before):
        e = s.setdefault(fam, {"rows": 0, "within_bound": 0, "min_ratio": float("inf")})
        e["rows"] += 1
        e["within_bound"] += int(margin <= bound)
        e["min_ratio"] = min(e["min_ratio"], margin / bound if bound > 0 else float("inf"))
    return s


def check(before, after):
    """-> (violations: list[str], stats: dict). `before` / `after` are flip_detector snapshot dicts (chart_facts, divisionals)."""
    bad = []
    for fam, k, margin, bound in label_margins(before):                                                          # CS6
        if margin <= bound:
            bad.append(f"CS6 {fam} label at {k} is within its physical shift of a class boundary (margin {margin:.6g} <= bound "
                       f"{bound:.6g}): a flip there is physics, not a defect, so CS2's strictness is not derived: human disposition")
    stats = {"varga_position": 0, "sensitive_degree_check": 0, "ayurdaya": 0}
    bd, bf = _families(before)
    ad, af = _families(after)
    for fam, b, a in (("varga_position", bd, ad), ("facts", bf, af)):
        if set(b) != set(a):                                                                                       # CS1
            only_b, only_a = sorted(set(b) - set(a)), sorted(set(a) - set(b))
            bad.append(f"CS1 {fam}: row set differs (only before: {len(only_b)}, only after: {len(only_a)}); first: {(only_b or only_a)[:1]}")
        for k in sorted(set(b) & set(a)):
            x, y = b[k], a[k]
            if len(x) != len(y):
                bad.append(f"CS1 {fam}: occurrence count {len(x)} -> {len(y)} at {k}")
                continue
            for (lx, nx), (ly, ny) in zip(x, y):
                if lx != ly:
                    bad.append(f"CS2 label {lx!r} -> {ly!r} at {k}")                                               # class flip
                    continue
                if nx == ny:
                    continue
                if (nx is None) != (ny is None):
                    bad.append(f"CS4 number appeared/vanished at {k}")
                    continue
                delta = abs(ny - nx)
                if fam == "varga_position":
                    ay, _v, graha, _c, key = k
                    if key != "degree_in_sign":
                        bad.append(f"CS4 non-composite varga_position key moved at {k}: {nx} -> {ny}")
                        continue
                    bound = _bound_varga(ay, DIV_BODY[graha]) if graha in DIV_BODY else None
                    stats["varga_position"] += 1
                else:
                    ay, cat, subj, key = k
                    if cat == "sensitive_degree_check":
                        if key not in SDC_KEYS or subj not in FACT_BODY or subj == "LAGNA":
                            bad.append(f"CS4 non-composite sensitive_degree_check row moved at {k}: {nx} -> {ny}")
                            continue
                        bound = _bound_sdc(ay, FACT_BODY[subj])
                        stats["sensitive_degree_check"] += 1
                    else:
                        if key not in AYU_KEYS or (key == "total_years" and subj not in AYU_TOTAL_SUBJECT) or (key != "total_years" and subj not in SEVEN):
                            bad.append(f"CS4 non-composite ayurdaya row moved at {k}: {nx} -> {ny}")
                            continue
                        bound = _bound_ayu(ay, key, subj)
                        stats["ayurdaya"] += 1
                if bound is None or delta > bound:
                    bad.append(f"CS3 {k}: moved {delta:.9g}, physical bound {bound if bound is None else format(bound, '.9g')}")
    counts = derive_count_bounds()
    for fam, (lo, hi) in counts.items():
        if not lo <= stats[fam] <= hi:
            bad.append(f"CS5 {fam}: {stats[fam]} changed rows, derived bound [{lo}, {hi}]")
    return bad, stats


def load_snapshot(path):
    with gzip.open(path, "rt") as f:
        return json.load(f)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--derive"]:
        print(json.dumps({k: {"min": lo, "max": hi} for k, (lo, hi) in derive_count_bounds().items()}, indent=1, sort_keys=True))
        return 0
    if len(argv) == 2 and argv[0] == "--margins":
        before = load_snapshot(argv[1])
        if before.get("meta", {}).get("chart_id") not in (None, CANONICAL):
            print("REFUSED: the bounds are derived at the canonical chart's instant and are unmeasured for any other chart", file=sys.stderr)
            return 6
        summary = margin_summary(before)
        print(json.dumps(summary, indent=1, sort_keys=True))
        return 0 if summary and all(e["within_bound"] == 0 for e in summary.values()) else 2
    if len(argv) == 3 and argv[0] == "--compare":
        before, after = load_snapshot(argv[1]), load_snapshot(argv[2])
        if before.get("meta", {}).get("chart_id") not in (None, CANONICAL) or after.get("meta", {}).get("chart_id") not in (None, CANONICAL):
            print("REFUSED: the bounds are derived at the canonical chart's instant and are unmeasured for any other chart", file=sys.stderr)
            return 6
        bad, stats = check(before, after)
        print(f"changed composite rows: {stats}; derived count bounds: {derive_count_bounds()}")
        for line in bad[:200]:
            print("FAIL", line)
        print("composite_shift_check:", "PASS" if not bad else f"FAIL ({len(bad)} violations)")
        return 0 if not bad else 2
    print(__doc__.split("Usage", 1)[1] if "Usage" in __doc__ else "usage: --compare BEFORE AFTER | --derive", file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main())
