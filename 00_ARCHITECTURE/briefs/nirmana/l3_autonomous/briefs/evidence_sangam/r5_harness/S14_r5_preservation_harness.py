"""S14 / SPEC R-5 — Phase-1 disposable preservation harness (plan §4 step 2).

Proposition (post-fix behaviour): on the schema-faithful disposable DB, the
D-R5-1 identity design survives all seven §6.3 attacks — empty rebuild,
moved date, one-to-many split, many-to-one merge, ambiguous match (fail-closed,
adjudicated re-run reattaches exactly then), interrupted/resumed rebuild
(byte-identical journal replay), and unchanged-count content-swap (manifest
catches the per-id difference the count/hash design misses). Runs r5_attacks.

NEG=1 negative control: flips r5_harness.FAIL_CLOSED_AMBIGUOUS, so rule 3 of
the rebuild algorithm silently re-attaches the ambiguous candidate to the first
plausible original — attack 5's propositions (originals retained, claims still
bound, flag present) then read FALSE. The mutation is in the evidence-bearing
decision logic itself (RRV-15 discipline), never a bare exit(1)."""

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))            # r5_harness/ (r5_identity, r5_attacks)
sys.path.insert(0, str(_HERE.parent))     # evidence_sangam/ (_common)

from _common import NEG, head, prop, done  # noqa: E402
import r5_harness  # noqa: E402
import r5_attacks  # noqa: E402

head("S14 — R-5 identity/history preservation: seven §6.3 attacks on the disposable harness")

if NEG:
    # evidence-bearing mutation: rule 3 stops failing closed, so the ambiguous
    # candidate is silently re-pointed — attack 5's evidence must read false.
    r5_harness.FAIL_CLOSED_AMBIGUOUS = False

for attack_name, assertions in r5_attacks.run_all_attacks():
    for (pname, cond, detail) in assertions:
        prop(f"{attack_name}: {pname}", cond, detail)

done("POST-FIX BEHAVIOUR PRESENT")
