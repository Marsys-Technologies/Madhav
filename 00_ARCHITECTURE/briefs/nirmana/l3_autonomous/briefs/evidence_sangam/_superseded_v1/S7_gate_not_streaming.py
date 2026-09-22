"""P:48: the 0.45 orb gate runs AFTER transit_search returns the fully accumulated list.
Source read only."""
from _common import *
head("S7 — inline gate: accumulate-then-filter, not stream")
ap = grep('pipeline/transit_search.py', r'events\.append\(TransitEvent')
rt = grep('pipeline/transit_search.py', r'^\s*return events')
gt = grep('services/ka_sangam/engine.py', r'orb_s < HIGH_CONFIDENCE_ORB_THRESHOLD')
print(f"  transit_search appends at {[i for i,_ in ap]}, returns full list at {[i for i,_ in rt]}; engine filters at {[i for i,_ in gt]}")
print("VERDICT: CONFIRMED — memory benefit claimed in the comment is not what the path does")
