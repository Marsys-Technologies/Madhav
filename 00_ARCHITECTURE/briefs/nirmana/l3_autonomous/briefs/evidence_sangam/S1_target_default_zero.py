"""F-01/R-1 (post-fix). Proposition: semantic triggers no longer silently default to 0.0.
The binder still emits no target_longitude, but the writer resolves it from chart_facts,
and the engine refuses to scan an unresolvable trigger. Evidence class: source reachability."""
from _common import *
head("S1 — unbound transit target is refused, not defaulted to 0.0")
b = grep('services/ka_yojaka/binder.py', r'target_longitude')
e = grep('services/ka_sangam/engine.py', r"unresolvable transit trigger target")
w_resolve = grep('pipeline/orchestrator/writers/ka_sangam.py', r"_fetch_target_fact_cache|chart_facts.*longitude_sidereal|chart_facts.*sripati_madhya")
w_default = grep('pipeline/orchestrator/writers/ka_sangam.py', r"target_longitude_deg', 0\.0")
if NEG: w_resolve = []                                # negative control: pretend writer does not resolve
prop("binder emits no target_longitude", len(b) == 0, f"occurrences={len(b)}")
prop("engine has fail-loud unresolvable-target guard", len(e) >= 1, f"lines={[i for i,_ in e]}")
prop("writer resolves target from L1 chart_facts", len(w_resolve) >= 1, f"lines={[i for i,_ in w_resolve]}")
prop("writer no longer defaults target to 0.0", len(w_default) == 0, f"lines={[i for i,_ in w_default]}")
done("POST-FIX BEHAVIOUR")
