"""A.4 row 5 / R-3. Proposition (defect present): the writer's lagna lookup DEFAULTS TO 'Aries' — 'this
native's lagna' — on any failure, and retains that fallback. CR-87's defect class, on the lagna read."""
from _common import *
head("S12 — lagna defaults to Aries on failure")
d = grep('pipeline/orchestrator/writers/ka_sangam.py', r"^\s*lagna_sign = 'Aries'\s*$")
c = grep('pipeline/orchestrator/writers/ka_sangam.py', r"Falls back to Aries")
if NEG: d = []
prop("default assignment lagna_sign = 'Aries' exists", len(d) == 1, f"line={[i for i,_ in d]}")
prop("docstring admits the fallback", len(c) >= 1, f"line={[i for i,_ in c]}")
done()
