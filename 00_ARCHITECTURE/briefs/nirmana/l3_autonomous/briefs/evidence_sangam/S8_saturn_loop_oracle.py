"""E5 oracle (RR-09 corrected). Records the ACTUAL ephemeris engine (requested SWIEPH; if Moshier is
returned, say so — it is NOT pinned Swiss-file provenance). Refines stations by bisection on speed sign
(tolerance 1 min). Propositions: exactly three SR→SD loops in 2026-2029; for each, an inside point
crosses 3 times and a control just outside crosses once. Independent referee for E5's grouping — but a
crossing count is NOT an orb-interval occupancy proof (SPEC E5(b))."""
import swisseph as swe
from _common import *
head("S8 — Saturn retrograde loops 2026–2029 → E5 oracle points (with provenance)")
swe.set_sid_mode(swe.SIDM_LAHIRI); FL = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
r = swe.calc_ut(swe.julday(2026,1,1), swe.SATURN, FL)
engine = "MOSHIER (fallback — no .se1 files)" if r[1] & swe.FLG_MOSEPH else "SWIEPH files"
print(f"  provenance: swisseph {swe.version}, requested flags {FL}, returned {r[1]} → {engine}; ayanamsha Lahiri; node n/a")
lon = lambda jd: swe.calc_ut(jd, swe.SATURN, FL)[0][0]; spd = lambda jd: swe.calc_ut(jd, swe.SATURN, FL)[0][3]
def refine(a, b):                                          # bisection on speed sign to ~1 minute
    while b - a > 1/1440: m = (a+b)/2; (a, b) = (m, b) if (spd(m) < 0) == (spd(a) < 0) else (a, m)
    return b
rel = lambda x,p: (x-p+180)%360-180
jd0, jd1 = swe.julday(2026,1,1), swe.julday(2029,12,31); prev=None; st=[]; jd=jd0
while jd <= jd1:
    s = spd(jd)
    if prev is not None and (s<0) != (prev<0): j = refine(jd-1, jd); st.append((j, 'SR' if s<0 else 'SD', lon(j)))
    prev = s; jd += 1
loops = [(st[i],st[i+1]) for i in range(len(st)-1) if st[i][1]=='SR' and st[i+1][1]=='SD']
def crossings(point, a, b, step=0.25):                     # quarter-day sampling; counts sign changes of relative longitude
    n=0; p=rel(lon(a),point); t=a+step
    while t <= b:
        c=rel(lon(t),point)
        if p*c < 0 and abs(c-p) < 180: n+=1
        p=c; t+=step
    return n
prop("exactly three SR→SD loops found", len(loops) == 3, f"found={len(loops)}")
for sr, sd in loops:
    span=(sr[2]-sd[2])%360; inside=(sd[2]+span/2)%360; outside=(sr[2]+2.0)%360
    y,m,d,_ = swe.revjul(sr[0]); y2,m2,d2,_ = swe.revjul(sd[0]); a,b = sr[0]-200, sd[0]+200
    ci, co = crossings(inside,a,b), crossings(outside,a,b)
    if NEG: co = 3                                        # negative control: claim the control point also triples
    print(f"  loop SR {y}-{m:02d}-{d:02d} {sr[2]:.3f}° → SD {y2}-{m2:02d}-{d2:02d} {sd[2]:.3f}°  arc {span:.3f}°{' (wraps 0°)' if sd[2]>sr[2] else ''}")
    prop(f"  inside {inside:.3f}° crosses 3×", ci == 3, f"count={ci}")
    prop(f"  control {outside:.3f}° crosses 1×", co == 1, f"count={co}")
done(kind="ORACLE POINTS CONSTRUCTED (Moshier unless stated otherwise)")
