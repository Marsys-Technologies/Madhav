"""RR-05/E1-E4. Proposition (defect present): with dignity 0 the I-16 kernel returns 0.0 regardless of
support — intense ADVERSE activity is erased, contradicting 'weak/adverse remains applicable'. Calls the
real kernel."""
from _common import *
from services.ka_sangam import engine as E
head("S11 — dignity 0 zeroes the score (adverse activity erased)")
f = E.convergence_score
if NEG: f = lambda nec, sup: 0.5                           # negative control: a kernel that separates activity from valence
z = f([0,1,1], {'constituent_lord_transit':1,'benefic_dristi':1}); nz = f([0.2,1,1], {'constituent_lord_transit':1,'benefic_dristi':1})
prop("dignity 0 → score exactly 0.0 despite full support", z == 0.0, f"score={z}")
prop("dignity 0.2 → nonzero (kernel is multiplicative in dignity)", nz > 0, f"score={nz:.4f}")
done()
