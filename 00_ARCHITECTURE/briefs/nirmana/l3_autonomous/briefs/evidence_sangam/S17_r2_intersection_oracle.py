"""R-2 clock-intersection oracle falsifier suite. Propositions: atomic segments carry
supporter/parent identity; agreement counts DISTINCT directly co-supporting systems (never
transitive merging, never interval count); nested levels of one system do not inflate;
degenerate [d,d) is an evaluated zero; boundary convention is S-H; sub-day datetimes flow
through the same code path."""
from _common import *
from datetime import date, datetime
from types import SimpleNamespace
from services.ka_dasha_kala.intersection import (
    BOUNDARY_CONVENTION, intersect_segments, agreement_for,
)

head("S17 — R-2 intersection oracle falsifier cases")

def _iv(a, b, system, row, level=2, parent=None):
    return SimpleNamespace(start_date=a, end_date=b, system_id=system, level_n=level,
                           lord_graha='Jupiter', dasha_row_id=row, parent_row_id=parent)

# Case 1: anti-transitive chain. A overlaps B, B overlaps C, A and C never touch.
A = _iv(date(2027, 1, 1), date(2027, 6, 30), 'vim', 'rA')
B = _iv(date(2027, 5, 1), date(2027, 10, 31), 'yog', 'rB')
C = _iv(date(2027, 9, 1), date(2028, 2, 28), 'chara', 'rC')
chain = intersect_segments([A, B, C])
sa = agreement_for(A.start_date, A.end_date, chain)
sc = agreement_for(C.start_date, C.end_date, chain)
direct_ac = any({'vim', 'chara'} <= {r.system_id for r in s.supporters} for s in chain)
if NEG:
    sa_expected = sc_expected = 3   # negative control: transitive/interval-count semantics
else:
    sa_expected = sc_expected = 2   # distinct systems only

# Case 2: nested levels, same system — distinct-system count, parent identity carried.
l1 = _iv(date(2020, 1, 1), date(2030, 1, 1), 'vim', 'r_l1', level=1)
l3 = _iv(date(2024, 1, 1), date(2025, 1, 1), 'vim', 'r_l3', level=3, parent='r_l1')
oth = _iv(date(2024, 1, 1), date(2025, 1, 1), 'yog', 'r_o')
nested = intersect_segments([l1, l3, oth])
nsum = agreement_for(l3.start_date, l3.end_date, nested)
nshared = [s for s in nested if {r.system_id for r in s.supporters} == {'vim', 'yog'}]

# Case 3: degenerate interval — real, evaluated zero.
deg = _iv(date(2027, 5, 1), date(2027, 5, 1), 'vim', 'rD')
deg_ag = agreement_for(deg.start_date, deg.end_date, intersect_segments([deg]))

# Case 4: S-H boundary — contiguous intervals partition; end point is NOT covered.
x = _iv(date(2027, 1, 1), date(2027, 6, 30), 'vim', 'rx')
y = _iv(date(2027, 6, 30), date(2027, 12, 31), 'yog', 'ry')   # starts exactly at x's end
contig = intersect_segments([x, y])

# Case 5: sub-day datetime boundaries flow through the same path.
dx = _iv(datetime(2027, 3, 1, 6, 0), datetime(2027, 3, 1, 18, 0), 'vim', 'rdx')
dy = _iv(datetime(2027, 3, 1, 12, 0), datetime(2027, 3, 2, 0, 0), 'yog', 'rdy')
subday = intersect_segments([dx, dy])
dshared = [s for s in subday
           if {r.system_id for r in s.supporters} == {'vim', 'yog'}]

prop("boundary convention declared as [start, end) (S-H)",
     BOUNDARY_CONVENTION == '[start, end)', f"convention={BOUNDARY_CONVENTION}")
prop(f"chain: A agrees with {sa_expected} systems (no transitive merge)",
     sa.count == sa_expected and sa.systems_agreeing == ('vim', 'yog'),
     f"count={sa.count} systems={sa.systems_agreeing}")
prop(f"chain: C agrees with {sc_expected} systems (no transitive merge)",
     sc.count == sc_expected and sc.systems_agreeing == ('chara', 'yog'),
     f"count={sc.count} systems={sc.systems_agreeing}")
prop("chain: A and C never directly share a segment",
     not direct_ac, f"direct_ac={direct_ac}")
prop("nested: same-system levels do not inflate agreement",
     nsum.count == 2, f"count={nsum.count}")
prop("nested: shared segment carries levels {1,2,3} + parent identity",
     len(nshared) == 1
     and {r.level_n for r in nshared[0].supporters} == {1, 2, 3}
     and {r.dasha_row_id: r.parent_row_id for r in nshared[0].supporters}['r_l3'] == 'r_l1',
     f"levels={{{', '.join(str(r.level_n) for r in nshared[0].supporters)}}}" if nshared else "no shared seg")
prop("degenerate [d,d) is an evaluated zero (not unavailable)",
     deg_ag.count == 0, f"count={deg_ag.count}")
prop("S-H: contiguous intervals partition; end point not co-covered",
     len(contig) == 2
     and {r.system_id for r in contig[0].supporters} == {'vim'}
     and {r.system_id for r in contig[1].supporters} == {'yog'}
     and contig[0].end == date(2027, 6, 30) and contig[1].start == date(2027, 6, 30),
     f"segments={[(s.start, s.end, tuple(r.system_id for r in s.supporters)) for s in contig]}")
prop("sub-day datetime boundaries intersect atomically",
     len(dshared) == 1 and dshared[0].start == datetime(2027, 3, 1, 12, 0)
     and dshared[0].end == datetime(2027, 3, 1, 18, 0),
     f"shared={[(s.start, s.end) for s in dshared]}")
done("POST-FIX BEHAVIOUR")
