"""F-08/E4. Proposition: in Mode A, necessary = [dignity, orb, vedha]; the daśā prior is SUPPORTING
('constituent_lord_transit'). Source structure."""
from _common import *
head("S10 — Mode A necessary vs supporting")
n = grep('services/ka_sangam/engine.py', r'necessary = \[dignity_score, orb_s, vedha_factor\]')
s = grep('services/ka_sangam/engine.py', r"'constituent_lord_transit':\s+float\(dasha_score\)")
if NEG: n = []
prop("necessary terms are dignity/orb/vedha", len(n) >= 1, f"lines={[i for i,_ in n]}")
prop("dasha enters as a supporting current", len(s) >= 1 and (not n or min(i for i,_ in s) > min(i for i,_ in n)), f"lines={[i for i,_ in s]}")
done()
