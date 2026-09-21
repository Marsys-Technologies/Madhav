# READ-ONLY evidence script. No DB, no network, no writes. Needs: swisseph, numpy, scipy.
# Run from anywhere:  python <this file>
"""F3 reproduction: run the REAL w2g arc/contact code exactly as production wires it
(tropical knots -> build_arcs -> ContactSolver.solve(target = SIDEREAL natal degree)),
then ask Swiss Ephemeris what the true Lahiri-sidereal separation is at each 'exact' instant."""
import sys, datetime as dt
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[6] / "platform" / "python-sidecar"))  # worktree root
import swisseph as swe
from services.w2g.arcs import build_arcs
from services.w2g.solver import ContactSolver, InMemoryArcSource

def wrap180(x):
    x = x % 360.0
    return x - 360.0 if x > 180.0 else x

def tropical_series(body_id, start, end):
    jds, lons = [], []
    d = start
    while d <= end:
        jd = swe.julday(d.year, d.month, d.day, 12.0)          # NOON UT, as l0_ephemeris
        lon = swe.calc_ut(jd, body_id, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]
        jds.append(jd); lons.append(round(lon % 360.0, 6))      # 6-dp, as stored
        d += dt.timedelta(days=1)
    return jds, lons

TARGET_SIDEREAL = 291.8   # native's natal Sun, Lahiri sidereal, per l0_ephemeris.py:25 docstring
START, END = dt.date(2015, 1, 1), dt.date(2035, 12, 31)

for name, bid in (("Saturn", swe.SATURN), ("Jupiter", swe.JUPITER), ("Mars", swe.MARS)):
    jds, lons = tropical_series(bid, START, END)
    arcs = build_arcs(name, jds, lons)
    events = ContactSolver(InMemoryArcSource({name: arcs})).solve((name,), [TARGET_SIDEREAL], orb_deg=1.0)
    print(f"\n{name}: {len(arcs)} arcs, {len(events)} 'exact contacts' with target {TARGET_SIDEREAL} (a SIDEREAL degree)")
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    for ev in events[:6]:
        trop = swe.calc_ut(ev.exact_jd, bid, swe.FLG_SWIEPH)[0][0]
        sid = swe.calc_ut(ev.exact_jd, bid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
        y, m, d, _ = swe.revjul(ev.exact_jd)
        print(f"  w2g exact={y}-{m:02d}-{d:02d}  tropical_lon={trop:9.4f}  sidereal_lon={sid:9.4f}  "
              f"TRUE sidereal separation from target = {wrap180(sid-TARGET_SIDEREAL):+8.3f} deg")
    # When does the body REALLY reach the sidereal target? brute-force with Swiss for comparison.
    true_hits = []
    prev = None
    jd = swe.julday(START.year, START.month, START.day, 12.0); end_jd = swe.julday(END.year, END.month, END.day, 12.0)
    while jd < end_jd:
        s = wrap180(swe.calc_ut(jd, bid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] - TARGET_SIDEREAL)
        if prev is not None and prev[1] * s < 0 and abs(s) < 90:
            lo, hi, flo = prev[0], jd, prev[1]
            for _ in range(40):
                mid = (lo + hi) / 2
                fm = wrap180(swe.calc_ut(mid, bid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] - TARGET_SIDEREAL)
                if flo * fm <= 0: hi = mid
                else: lo, flo = mid, fm
            true_hits.append((lo + hi) / 2)
        prev = (jd, s); jd += 0.5
    print("  TRUE sidereal contacts (Swiss):", ", ".join("%d-%02d-%02d" % swe.revjul(t)[:3] for t in true_hits[:6]))
    if events and true_hits:
        nearest = min(abs(events[0].exact_jd - t) for t in true_hits)
        print(f"  first w2g 'contact' is {nearest:,.0f} days from the nearest TRUE contact")
