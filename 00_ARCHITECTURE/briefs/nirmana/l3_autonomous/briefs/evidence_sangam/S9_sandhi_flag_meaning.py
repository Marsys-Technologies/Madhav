"""F-07/E4. Proposition: L1's sandhi_flag means 'duration < 20 days' — not a junction-zone locator."""
from _common import *
head("S9 — sandhi_flag semantics")
m = grep('ga_writers/ga_dashas_writer.py', r'^\s*sandhi_flag = duration_days < 20\s*$')
if NEG: m = []
prop("sandhi_flag = duration_days < 20 (exact line)", len(m) == 1, f"line={[i for i,_ in m]}")
done()
