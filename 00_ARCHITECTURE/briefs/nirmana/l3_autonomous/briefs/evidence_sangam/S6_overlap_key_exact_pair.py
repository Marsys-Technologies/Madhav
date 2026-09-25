"""F-13/R-2. Proposition (defect present): the cross-clock agreement key is the exact (start,end) pair,
so two intervals overlapping by ~305 days but with different endpoints get DIFFERENT keys. Calls the real
key function. Note: elapsed days by subtraction = 305; inclusive date count = 306 (boundary convention S-H)."""
from _common import *
from datetime import date
from services.ka_dasha_kala import service as DS
head("S6 — overlap key is exact-endpoint")
class I:
    def __init__(s,a,b): s.start_date, s.end_date = a, b
a, b = I(date(2027,1,1), date(2027,12,31)), I(date(2027,3,1), date(2028,2,28))
key = DS._build_overlap_key
if NEG: key = lambda iv: ('same',)                        # negative control: an intersection-aware key → defect assertion must FAIL
ka, kb = key(a), key(b); ov = (min(a.end_date,b.end_date)-max(a.start_date,b.start_date)).days
prop("intervals overlap", ov > 0, f"elapsed overlap={ov} d (inclusive {ov+1})")
prop("keys differ despite overlap (no agreement possible)", ka != kb, f"A={ka} B={kb}")
done()
