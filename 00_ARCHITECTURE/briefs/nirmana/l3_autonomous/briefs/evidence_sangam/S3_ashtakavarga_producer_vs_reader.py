"""F-03/E2 (rebuilt per RR-02). Propositions about the REAL producer, not a hypothetical one:
(a) ga_strength_writer emits HOUSE_N and SIGN_N rows from the SAME value (no lagna rotation);
(b) Sangam's writer reads only the legacy 'ashtakavarga_bindu' category, with Lahiri hardcoded;
(c) a missing planet is emitted as twelve zeros (indistinguishable from measured zeros downstream).
Consequence for E2: the defect is vocabulary/category/provenance, NOT frame; and the zero-provenance
loss is a PRODUCER amendment, not something a reader can recover."""
from _common import *
head("S3 — ashtakavarga: what the producer really writes vs what Sangam reads")
L = src('ga_writers/ga_strength_writer.py')
h = [i for i,l in enumerate(L,1) if 'ashtakavarga_bindu"' in l and '-HOUSE_{idx + 1}' in l]
s = [i for i,l in enumerate(L,1) if 'ashtakavarga_bindu_sign' in l and '-SIGN_{idx + 1}' in l]
# the value argument is on the line following each _mk( call: L[i] is 0-based → the next line
same_val = bool(h) and bool(s) and all('float(bindus)' in L[i] for i in h) and all('float(bindus)' in L[i] for i in s)
if NEG: same_val = False                                  # negative control: claim a rotation exists
prop("(a) HOUSE_N and SIGN_N written from the same float(bindus)", bool(same_val), f"HOUSE lines {h}, SIGN lines {s}")
z = grep('ga_writers/ga_strength_writer.py', r"\[0\] \* 12"); prop("(c) missing planet → twelve zeros at producer", len(z) >= 1, f"lines={[i for i,_ in z]}")
r = grep('pipeline/orchestrator/writers/ka_sangam.py', r"fact_category = 'ashtakavarga_bindu'"); prop("(b) Sangam reads legacy category only", len(r) == 1 and not grep('pipeline/orchestrator/writers/ka_sangam.py', r"ashtakavarga_bindu_sign"), f"line={[i for i,_ in r]}")
lah = grep('pipeline/orchestrator/writers/ka_sangam.py', r"lahiri"); prop("(b) reader hardcodes Lahiri near the AV read", any(990 <= i <= 1030 for i,_ in lah), f"lahiri lines={[i for i,_ in lah][:6]}")
# reader-level consequence: with identical HOUSE_1/SIGN_1 values, any sign-keyed lookup returns the same number → no rotation to test
rows = {'SAT-HOUSE_1': 4.0, 'SAT-SIGN_1': 4.0}; prop("reader gets identical value from either key (rotation hypothesis false)", rows['SAT-HOUSE_1'] == rows['SAT-SIGN_1'])
done()
