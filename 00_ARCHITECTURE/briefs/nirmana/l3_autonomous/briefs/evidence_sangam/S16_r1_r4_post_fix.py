"""R-1/R-4 post-fix detector. Proposition: Mode B (a) stamps target availability,
carries target provenance in constituent_factors, and (b) withdraws
benefic_dristi/transit_to_transit from the scored supporting dict while keeping
lineage _withdrawn reason keys."""
from _common import *
head("S16 — Mode B R-1 provenance + R-4 withdrawal")

# Mode B supporting dict must no longer contain the withdrawn keys.
mode_b_supporting = grep('services/ka_sangam/engine.py',
                         r"'benefic_dristi':\s*c_dristi|'transit_to_transit':\s*c9")
# But they must still be computed for lineage.
lineage_dristi = grep('services/ka_sangam/engine.py', r"'c_benefic_dristi': round\(c_dristi")
lineage_t2t = grep('services/ka_sangam/engine.py', r"'c9_transit_to_transit': round\(c9")
withdrawn_dristi = grep('services/ka_sangam/engine.py', r"'c_benefic_dristi_withdrawn'")
withdrawn_t2t = grep('services/ka_sangam/engine.py', r"'c9_transit_to_transit_withdrawn'")
target_avail = grep('services/ka_sangam/engine.py',
                    r"'target': 'computed' if _has_target_provenance\(transit_trig\)")
target_prov = grep('services/ka_sangam/engine.py',
                   r"\{'target_provenance': _target_provenance_dict\(transit_trig\)\}")

if NEG:
    mode_b_supporting = [(1, 'x')]  # negative control: pretend keys still present

prop("Mode B supporting dict excludes withdrawn keys", len(mode_b_supporting) == 0,
     f"occurrences={len(mode_b_supporting)}")
prop("benefic_dristi lineage key still computed", len(lineage_dristi) >= 1,
     f"lines={[i for i,_ in lineage_dristi]}")
prop("transit_to_transit lineage key still computed", len(lineage_t2t) >= 1,
     f"lines={[i for i,_ in lineage_t2t]}")
prop("c_benefic_dristi_withdrawn reason key present", len(withdrawn_dristi) >= 1,
     f"lines={[i for i,_ in withdrawn_dristi]}")
prop("c9_transit_to_transit_withdrawn reason key present", len(withdrawn_t2t) >= 1,
     f"lines={[i for i,_ in withdrawn_t2t]}")
prop("Mode B availability stamps target", len(target_avail) >= 1,
     f"lines={[i for i,_ in target_avail]}")
prop("Mode B constituent_factors carries target_provenance", len(target_prov) >= 1,
     f"lines={[i for i,_ in target_prov]}")
done("POST-FIX BEHAVIOUR")
