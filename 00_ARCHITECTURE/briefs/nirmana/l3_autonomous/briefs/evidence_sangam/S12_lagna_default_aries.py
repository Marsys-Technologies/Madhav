"""A.4 row 5 / R-3(b). Proposition (post-fix): the writer's lagna lookup is fail-loud.
There is no 'lagna_sign = Aries' default assignment and no fallback docstring."""
from _common import *
head("S12 — lagna lookup is fail-loud, no Aries fallback")
d = grep('pipeline/orchestrator/writers/ka_sangam.py', r"^\s*lagna_sign = 'Aries'\s*$")
c = grep('pipeline/orchestrator/writers/ka_sangam.py', r"Falls back to Aries")
raise_guard = grep('pipeline/orchestrator/writers/ka_sangam.py', r"could not resolve lagna sign")
if NEG: raise_guard = []
prop("default assignment lagna_sign = 'Aries' is removed", len(d) == 0, f"occurrences={len(d)}")
prop("fallback docstring removed", len(c) == 0, f"occurrences={len(c)}")
prop("fail-loud guard exists", len(raise_guard) >= 1, f"lines={[i for i,_ in raise_guard]}")
done("POST-FIX BEHAVIOUR")
