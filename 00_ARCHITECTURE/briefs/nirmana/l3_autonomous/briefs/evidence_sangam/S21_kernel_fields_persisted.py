"""Synergy audit #1/#3/#7 (post-fix). Detector for the gaps confirmed at
sangam/stage3 0b439b0c7 and repaired in migration 1085 + writer:

(a) R-6's separation reaches the TABLE: activity, valence, applicability,
    comparability_class, kernel_version, independence_group are in the INSERT
    and bound to window fields — §4.5's never-pool rule needs columns, not
    in-memory attributes;
(b) the INSERT's column count equals its VALUE SLOT count (NOW() counts as a
    slot) — an off-by-one here raises only when real SQL runs;
(c) migration 1085 is additive (ADD COLUMN IF NOT EXISTS only, no DROP/ALTER
    TYPE/UPDATE) and declares contact_uuid's absence rather than shipping a
    NULL column;
(d) the 29-Feb horizon crash is repaired by clamping, not by try/except pass;
(e) the tz offset is taken at the birth instant, with a declared fallback;
(f) ka_vedha_gochara is declared in ka_sangam.depends_on.

Run with NEG=1 for the negative control (evidence-bearing inputs mutated).
"""
import re
import sys
from datetime import date

from _common import *  # noqa: F403
from pipeline.orchestrator.writers.ka_sangam import _add_years

head("S21 — R-6 kernel fields persisted; horizon, tz and vedha edge (synergy audit)")

KERNEL_COLUMNS = ['activity', 'valence', 'applicability',
                  'comparability_class', 'kernel_version', 'independence_group']
IDENTITY_COLUMNS = ['contact_uuid', 'convention_frame', 'identity_state']
LAYER_ENUM = ('self', 'same_convention_same_inputs',
              'same_convention_newer_inputs', 'different_convention')

writer_src = "\n".join(src('pipeline/orchestrator/writers/ka_sangam.py'))
i = writer_src.index('INSERT INTO kala_convergence')
block = writer_src[i:writer_src.index('"""', i)]
cols_part, values_part = block.split('VALUES', 1)


def _split_top_level(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur); cur = ''
        else:
            cur += ch
    out.append(cur)
    return out


cols = [c.strip() for c in _split_top_level(
    cols_part[cols_part.index('(') + 1:cols_part.rindex(')')]) if c.strip()]
vals = [v.strip() for v in _split_top_level(
    values_part[values_part.index('(') + 1:values_part.rindex(')')]) if v.strip()]

_root = __file__.rsplit('/00_ARCHITECTURE/', 1)[0]
mig = open(_root + '/platform/supabase/migrations/1085_kala_convergence_kernel_fields.sql').read()
mig86 = open(_root + '/platform/supabase/migrations/1086_kala_convergence_r5_identity.sql').read()

sys.path.insert(0, _root + '/platform/python-sidecar')
from services.ka_sangam.identity import (  # noqa: E402
    contact_uuid as _cu, frame_vector as _fv, frame_dict as _fd,
    independence_group as _ig,
)
sys.path.insert(0, _root + '/00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/evidence_sangam/r5_harness')
import r5_identity as _H  # noqa: E402

_frame = _fv('lahiri_chitrapaksha')
_args = ('c1', 'separated_v2', 'Saturn', 'f123', 180.0, _frame, 3.2, 'A')
_prod_id, _harness_id = _cu(*_args), _H.contact_uuid(*_args)
_mean_frame = _fv('lahiri_chitrapaksha', node_convention='mean')
_id_true, _id_mean = _cu(*_args[:5], _frame, 3.2, 'A'), _cu(*_args[:5], _mean_frame, 3.2, 'A')
_fdict = _fd(_frame)
_grp_same = _ig('s1', 'Saturn', 'f1') == _ig('s1', 'Saturn', 'f1')
_grp_diff = _ig('s1', 'Saturn', 'f1') != _ig('s2', 'Saturn', 'f1')

from services.ka_sangam.exposure import build_scan_coverage as _bsc  # noqa: E402
from datetime import date as _date  # noqa: E402
_h0, _h1 = _date(2026, 1, 1), _date(2033, 1, 1)
_cov_reasons = [_bsc(_h0, _h1, 0, 0, 0).empty_reason,
                _bsc(_h0, _h1, 5, 0, 0).empty_reason,
                _bsc(_h0, _h1, 5, 9, 0).empty_reason]
_cov_none = _bsc(_h0, _h1, 5, 9, 4).empty_reason
# CALL sites only: the def line matches a bare-name search, which made this
# detector read 3 and fail correct code on its first run.
_cov_in_notes = writer_src.count('notes=_notes_with_coverage(')
_mig87 = open(_root + '/platform/supabase/migrations/1087_kala_convergence_comparable_with.sql').read()
_cw_derived = 'node_convention' in writer_src[writer_src.index('_comparable_with'):
                                              writer_src.index('_comparable_with') + 400]
_cw_both = 'comparability_class' in cols and 'comparable_with' in cols

seed = open(__file__.rsplit('/00_ARCHITECTURE/', 1)[0]
            + '/platform/scripts/seed/asset_registry_seed.ts').read()
si = seed.index("asset_id: 'ka_sangam'")
sj = seed.index('\n    depends_on: [', si)
depends = re.findall(r"'([^']+)'", seed[sj:seed.index(']', sj)])

# NEG mutates evidence-bearing inputs, then the propositions read the mutated system.
if NEG:  # noqa: F405
    cols = [c for c in cols if c not in KERNEL_COLUMNS]
    vals = vals[:-6]
    mig = mig.replace('ADD COLUMN IF NOT EXISTS', 'DROP COLUMN')
    depends = [d for d in depends if d != 'ka_vedha_gochara']
    writer_src = writer_src.replace('_birth_instant_for_offset', 'datetime_now_only')
    mig86 = mig86.replace('contact_uuid', 'nothing')
    _harness_id = 'mismatched'
    _id_mean = _id_true
    _fdict = dict(_fdict, ephemeris_backend='swieph', house_frame='placidus')
    _grp_diff = False
    _cov_reasons = [None, None, None]
    _cov_none = 'invented_reason'
    _cov_in_notes = 0
    _mig87 = _mig87.replace("'different_convention'", "'mostly_comparable'")
    _cw_derived = False
    _cw_both = False

missing = [c for c in KERNEL_COLUMNS if c not in cols]
prop("(a) all six R-6 kernel columns persisted in the INSERT", not missing, f"missing={missing}")  # noqa: F405
prop("(a) kernel_version bound from the window, not a literal",  # noqa: F405
     bool(re.search(r"w\.get\('kernel_version'\)", writer_src)))
prop("(b) column count == value slot count", len(cols) == len(vals), f"{len(cols)} cols / {len(vals)} slots")  # noqa: F405
prop("(c) migration 1085 is additive only",  # noqa: F405
     'ADD COLUMN IF NOT EXISTS' in mig and 'DROP COLUMN' not in mig
     and 'ALTER COLUMN' not in mig and not re.search(r'\bUPDATE\b', mig))
prop("(c) migration declares contact_uuid's absence and why", 'contact_uuid' in mig and 'frame vector' in mig)  # noqa: F405
prop("(d) 29-Feb clamps to 28 in a non-leap target year", _add_years(date(2024, 2, 29), 7) == date(2031, 2, 28))  # noqa: F405
prop("(d) 29-Feb preserved when the target year IS leap", _add_years(date(2024, 2, 29), 4) == date(2028, 2, 29))  # noqa: F405
prop("(e) tz offset evaluated at the birth instant", '_birth_instant_for_offset' in writer_src  # noqa: F405
     and bool(re.search(r'utcoffset\(_at or datetime\.now\(\)\)', writer_src)))
prop("(f) ka_vedha_gochara declared in ka_sangam.depends_on", 'ka_vedha_gochara' in depends, f"{len(depends)} edges")  # noqa: F405

# --- #6/#10: R-5 identity over R-3's frame ---
missing_id = [c for c in IDENTITY_COLUMNS if c not in cols]
prop("(g) identity columns persisted (contact_uuid, convention_frame, identity_state)",  # noqa: F405
     not missing_id, f"missing={missing_id}")
prop("(g) migration 1086 ships identity and frame TOGETHER",  # noqa: F405
     'contact_uuid' in mig86 and 'convention_frame' in mig86)
prop("(h) production identity == the qualified harness identity",  # noqa: F405
     _prod_id == _harness_id, f"prod={_prod_id}")
prop("(h) two convention frames never coalesce into one identity", _id_true != _id_mean)  # noqa: F405
prop("(i) frame declares its gaps, never claims an unasserted backend",  # noqa: F405
     _fdict['ephemeris_backend'] == 'unasserted' and _fdict['house_frame'] == 'unavailable',
     f"{_fdict}")
prop("(i) frame records the SCANNER's node convention, so the M-1 mismatch stays visible",  # noqa: F405
     _fdict['node_convention'] == 'true_node')
prop("(j) independence_group: same root testimony groups, different does not",  # noqa: F405
     _grp_same and _grp_diff)

# --- #4: scan coverage — empty is no longer indistinguishable from failure ---
prop("(k) three distinct empty reasons, none of them 'unknown'",  # noqa: F405
     len(set(_cov_reasons)) == 3 and all(r and r != 'unknown' for r in _cov_reasons),
     f"{_cov_reasons}")
prop("(k) no empty_reason when windows were emitted", _cov_none is None)  # noqa: F405
prop("(k) both substeps carry coverage AND the exposure manifest in notes",  # noqa: F405
     _cov_in_notes == 2 and "'scan_coverage'" in writer_src and "'exposure_manifest'" in writer_src,
     f"{_cov_in_notes} call sites")

# --- #2/#8: the layer comparability relation, read at source ---
prop("(l) CHECK carries exactly the four layer values (WP1_CONTRACTS §6)",  # noqa: F405
     all(f"'{v}'" in _mig87 for v in LAYER_ENUM))
prop("(l) comparable_with is DERIVED from the frame, never defaulted", _cw_derived)  # noqa: F405
prop("(l) grouping key and relation coexist — the rename would have lost the grouping",  # noqa: F405
     _cw_both)

done(kind="POST-FIX BEHAVIOUR")  # noqa: F405
