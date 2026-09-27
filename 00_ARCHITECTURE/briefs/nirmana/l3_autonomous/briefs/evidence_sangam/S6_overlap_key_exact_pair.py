"""F-13/R-2 POST-FIX detector. Proposition: the exact-(start,end)-pair agreement key is GONE,
and the R-2 oracle gives the two ~305-day-overlap clocks (different endpoints) agreement=2.
Note: elapsed days by subtraction = 305; inclusive date count = 306 (boundary convention S-H)."""
from _common import *
from datetime import date
from types import SimpleNamespace
from services.ka_dasha_kala.intersection import intersect_segments, agreement_for

head("S6 — overlap registers agreement across unequal endpoints (R-2 oracle)")

def _iv(a, b, system, row):
    return SimpleNamespace(start_date=a, end_date=b, system_id=system, level_n=2,
                           lord_graha='Jupiter', dasha_row_id=row, parent_row_id=None)

a = _iv(date(2027, 1, 1), date(2027, 12, 31), 'vim', 'ra')
b = _iv(date(2027, 3, 1), date(2028, 2, 28), 'yog', 'rb')
ov = (min(a.end_date, b.end_date) - max(a.start_date, b.start_date)).days

# 1. The exact-key defect is repaired at the source.
key_refs = grep('services/ka_dasha_kala/service.py', r'_build_overlap_key')

# 2. The oracle computes agreement behaviourally.
segs = intersect_segments([a, b])
sa = agreement_for(a.start_date, a.end_date, segs)
sb = agreement_for(b.start_date, b.end_date, segs)
shared = [s for s in segs if {r.system_id for r in s.supporters} == {'vim', 'yog'}]

if NEG:
    expected = 3            # negative control: interval-count instead of distinct-system count
else:
    expected = 2

prop("intervals overlap", ov > 0, f"elapsed overlap={ov} d (inclusive {ov + 1})")
prop("exact-endpoint key removed from service", len(key_refs) == 0,
     f"occurrences={len(key_refs)}")
prop(f"agreement for A's span == {expected} (distinct systems)",
     sa.count == expected, f"count={sa.count} systems={sa.systems_agreeing}")
prop(f"agreement for B's span == {expected} (distinct systems)",
     sb.count == expected, f"count={sb.count} systems={sb.systems_agreeing}")
prop("exactly one shared atomic segment spanning the overlap",
     len(shared) == 1 and shared[0].start == date(2027, 3, 1)
     and shared[0].end == date(2027, 12, 31),
     f"shared={[((s.start, s.end)) for s in shared]}")
done("POST-FIX BEHAVIOUR")
