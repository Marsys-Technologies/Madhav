"""F-01/R-1. Proposition: semantic triggers carry NO target_longitude_deg and Sangam defaults the scan
target to 0.0. Evidence class: source reachability (not live incidence)."""
from _common import *
head("S1 — unbound transit target defaults to 0.0")
b = grep('services/ka_yojaka/binder.py', r'target_longitude')
e = grep('services/ka_sangam/engine.py', r"target_longitude_deg', 0\.0")
w = grep('pipeline/orchestrator/writers/ka_sangam.py', r"target_longitude_deg', 0\.0")
if NEG: b = [(1, 'x')]                                  # negative control: pretend the binder emits it
prop("binder emits no target_longitude", len(b) == 0, f"occurrences={len(b)}")
prop("engine defaults target to 0.0", len(e) >= 1, f"lines={[i for i,_ in e]}")
prop("writer defaults target to 0.0", len(w) >= 1, f"lines={[i for i,_ in w]}")
done()
