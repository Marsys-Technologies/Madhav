"""F-06/E3. Proposition: under uniform Moon motion (27.3 d), conjunction+opposition contacts in a 60-day
window number 5, exceeding v0.1's bound ceil(60/27.3)+1 = 4. Arithmetic counterexample only — NOT an
ephemeris count for a dated parent (that is a SPEC fixture)."""
import math
from _common import *
head("S4 — Moon contact count vs the withdrawn bound")
P = 27.3
for days, expect in ((60,5),(90,7)):
    n = sum(1 for k in range(0, 100) if k*P/2 <= days); bound = math.ceil(days/P)+1
    if NEG: expect = bound
    prop(f"{days}-day window: contacts == {expect} and > bound {bound}", n == expect and n > bound, f"n={n}")
done()
