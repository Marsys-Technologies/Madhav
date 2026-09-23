"""F-03/E2 (post-fix). Detector for the ashtakavarga repair:
(a) producer writes a computed_planets receipt and a school-primary label;
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

# (a) producer writes receipt + school-primary label
writer = src('ga_writers/ga_strength_writer.py')
receipt = grep('ga_writers/ga_strength_writer.py', r'ashtakavarga_completeness_receipt')
school = grep('ga_writers/ga_strength_writer.py', r'ashtakavarga_school_primary')
prop("(a) producer emits ashtakavarga_completeness_receipt", len(receipt) >= 1,
     f"lines={[i for i,_ in receipt]}")
prop("(a) producer emits ashtakavarga_school_primary", len(school) >= 1,
     f"lines={[i for i,_ in school]}")
if NEG:
    receipt = []; school = []  # negative control: pretend absent

# (b) reader reads sign-keyed facts and receipt categories
reader = src('pipeline/orchestrator/writers/ka_sangam.py')
has_sign = any('ashtakavarga_bindu_sign' in l for l in reader)
has_receipt_read = any('ashtakavarga_completeness_receipt' in l for l in reader)
has_school_read = any('ashtakavarga_school_primary' in l for l in reader)
prop("(b) Sangam reader reads ashtakavarga_bindu_sign", has_sign)
prop("(b) Sangam reader reads completeness receipt", has_receipt_read)
prop("(b) Sangam reader reads school-primary label", has_school_read)
if NEG:
    has_sign = has_receipt_read = has_school_read = False

# (c) own-BAV verdict bands
def ctx_for(bindus, planet='Jupiter', computed=None):
    if computed is None:
        computed = {planet}
    return EnrichmentContext(
        ashtakavarga_bindu={planet: {1: bindus}},
        ashtakavarga_computed_planets=computed,
    )

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
