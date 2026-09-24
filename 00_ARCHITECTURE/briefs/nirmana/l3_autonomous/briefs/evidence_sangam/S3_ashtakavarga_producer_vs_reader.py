"""F-03/E2 (post-fix). Detector for the ashtakavarga repair:
(a) reader degrades honestly when the producer receipt is absent (B-4 open) and
    produces a verdict when it is present — behavioural, not a source grep (RC-04);
(b) Sangam reader reads sign-keyed facts and the receipt;
(c) own-BAV verdict bands are correct (≥5 support, 4 indeterminate, ≤3 obstruct);
(d) a missing planet is unavailable, not a measured zero;
(e) SAV verdict uses BPHS bands (>30 support, 25-30 indeterminate, <25 obstruct)
    with Phaladīpikā alternate retained.
Run with NEG=1 to execute the negative control (assertions inverted)."""
from _common import *
from services.ka_sangam.engine import (
    EnrichmentContext,
    _c7_ashtakavarga_verdict,
    _sav_verdict,
)

head("S3 — ashtakavarga producer receipt vs reader verdict (E2 post-fix)")

# (a) Producer receipt — BEHAVIOURAL, deliberately NOT a source grep.
#     RC-04 (2026-09-23): (a) previously grepped ga_writers/ga_strength_writer.py for the two
#     receipt categories. That pinned an unauthorized, build-fatal L1 edit in place — reverting the
#     breach turned this suite red, so the evidence DEFENDED the defect instead of detecting it.
#     Its NEG reset also ran AFTER the eager prop() calls, so those two propositions could never
#     fail under NEG=1 (the RRV-15 "sincerity escape", in the very script meant to enforce it).
#     B-4 is OPEN: no L1 producer receipt exists today — RRV-01's stage-3-side join is unimplemented
#     and the producer-column route belongs to the L1 owner. What must hold whichever route lands is
#     the READER's behaviour: receipt absent -> UNAVAILABLE, never a measured zero.
def ctx_for(bindus, planet='Jupiter', computed=None):
    if computed is None:
        computed = {planet}
    return EnrichmentContext(
        ashtakavarga_bindu={planet: {1: bindus}},
        ashtakavarga_computed_planets=computed,
    )

# NEG mutates evidence-bearing INPUT (swaps which planets the receipt reports), then reads the
# real system — never a post-assertion variable reset.
absent_receipt = {'Jupiter'} if NEG else set()
present_receipt = set() if NEG else {'Jupiter'}
v_absent = _c7_ashtakavarga_verdict('Jupiter', 1, ctx_for(6, computed=absent_receipt))
v_present = _c7_ashtakavarga_verdict('Jupiter', 1, ctx_for(6, computed=present_receipt))
prop("(a) planet absent from receipt -> unavailable (None), never measured zero",
     v_absent is None, v_absent)
prop("(a) planet present in receipt -> verdict produced",
     v_present is not None and v_present['verdict'] == 'support', v_present)

# (b) reader reads sign-keyed facts and receipt categories
reader = src('pipeline/orchestrator/writers/ka_sangam.py')
has_sign = any('ashtakavarga_bindu_sign' in l for l in reader)
has_receipt_read = any('ashtakavarga_completeness_receipt' in l for l in reader)
has_school_read = any('ashtakavarga_school_primary' in l for l in reader)
if NEG:  # RRV-15: mutate BEFORE asserting, or the control is a no-op
    has_sign = has_receipt_read = has_school_read = False
prop("(b) Sangam reader reads ashtakavarga_bindu_sign", has_sign)
prop("(b) Sangam reader reads completeness receipt", has_receipt_read)
prop("(b) Sangam reader reads school-primary label", has_school_read)

# (c) own-BAV verdict bands (ctx_for defined above)
support = _c7_ashtakavarga_verdict('Jupiter', 1, ctx_for(5))
indet = _c7_ashtakavarga_verdict('Jupiter', 1, ctx_for(4))
obstruct = _c7_ashtakavarga_verdict('Jupiter', 1, ctx_for(3))
missing = _c7_ashtakavarga_verdict('Jupiter', 1, ctx_for(5, computed=set()))

if NEG:
    support, indet, obstruct, missing = None, None, None, {'verdict': 'support'}

prop("(c) BAV ≥5 → support", support is not None and support['verdict'] == 'support',
     support)
prop("(c) BAV =4 → indeterminate", indet is not None and indet['verdict'] == 'indeterminate',
     indet)
prop("(c) BAV ≤3 → obstruct", obstruct is not None and obstruct['verdict'] == 'obstruct',
     obstruct)
prop("(d) missing planet → unavailable", missing is None, missing)

# (e) SAV verdict bands
sav_support = _sav_verdict(1, EnrichmentContext(
    ashtakavarga_bindu={'SARVA': {1: 31}}, ashtakavarga_school_primary='BPHS'))
sav_indet = _sav_verdict(1, EnrichmentContext(
    ashtakavarga_bindu={'SARVA': {1: 27}}, ashtakavarga_school_primary='BPHS'))
sav_obstruct = _sav_verdict(1, EnrichmentContext(
    ashtakavarga_bindu={'SARVA': {1: 24}}, ashtakavarga_school_primary='BPHS'))
sav_phal = _sav_verdict(1, EnrichmentContext(
    ashtakavarga_bindu={'SARVA': {1: 29}}, ashtakavarga_school_primary='Phaladīpikā'))

if NEG:
    sav_support, sav_indet, sav_obstruct, sav_phal = None, None, None, None

prop("(e) BPHS SAV >30 → support", sav_support is not None and sav_support['verdict'] == 'support',
     sav_support)
prop("(e) BPHS SAV 25-30 → indeterminate", sav_indet is not None and sav_indet['verdict'] == 'indeterminate',
     sav_indet)
prop("(e) BPHS SAV <25 → obstruct", sav_obstruct is not None and sav_obstruct['verdict'] == 'obstruct',
     sav_obstruct)
prop("(e) Phaladīpikā SAV >28 → support", sav_phal is not None and sav_phal['verdict'] == 'support',
     sav_phal)

done(kind="POST-FIX BEHAVIOUR")
