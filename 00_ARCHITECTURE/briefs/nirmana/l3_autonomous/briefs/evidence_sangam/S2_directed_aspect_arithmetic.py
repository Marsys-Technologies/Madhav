"""F-02/E1. Proposition: for a DIRECTED special aspect, the aspecting graha sits at (target - angle), but
transit_search searches (target + angle); the Mars and Saturn pairs therefore search the wrong
longitudes, while Jupiter's mirror pair {120,240} coincides and hides the error. Pure arithmetic."""
from _common import *
head("S2 — directed special aspects vs 'target + angle'")
naive = lambda t,a: (t+a)%360; directed = lambda t,a: (t-a)%360
pairs = {"Mars": (90,210), "Saturn": (60,270), "Jupiter": (120,240)}
t = 0
for g,(a1,a2) in pairs.items():
    ns, ds = {naive(t,a1),naive(t,a2)}, {directed(t,a1),directed(t,a2)}
    expect_equal = (g == "Jupiter") ^ NEG                # negative control: expect the opposite for Jupiter
    prop(f"{g} pair search sets {'coincide' if expect_equal else 'differ'}", (ns == ds) == expect_equal, f"naive={sorted(ns)} directed={sorted(ds)}")
i = next(k for k,l in enumerate(src('pipeline/transit_search.py'),1) if 'target_longitude' in l and '+' in l and 'aspect' in l)
prop("scanner documents target+angle search", i > 0, f"transit_search.py:{i}")
done()
