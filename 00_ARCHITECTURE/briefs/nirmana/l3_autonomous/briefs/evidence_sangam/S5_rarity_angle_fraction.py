"""P:58/E6. Proposition (defect present): _rarity_years reports a fixed target's OPPOSITION as recurring
twice per sidereal period (period/2), which is not a recurrence model. Calls the real function."""
from _common import *
from services.ka_sangam import engine as E
head("S5 — rarity_years opposition = period/2 (defect)")
f = E._rarity_years
if NEG: f = lambda p,a: 29.46                             # negative control: a 'fixed' function → defect assertion must FAIL
c, o = f('Saturn', 0.0), f('Saturn', 180.0)
prop("opposition reported at half the conjunction recurrence", abs(o - c/2) < 0.05, f"conj={c} opp={o}")
done()
