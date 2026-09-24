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
from datetime import date

from _common import *  # noqa: F403
from pipeline.orchestrator.writers.ka_sangam import _add_years

head("S21 — R-6 kernel fields persisted; horizon, tz and vedha edge (synergy audit)")

KERNEL_COLUMNS = ['activity', 'valence', 'applicability',
                  'comparability_class', 'kernel_version', 'independence_group']

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

mig = "\n".join(src('../../../../../platform/supabase/migrations/1085_kala_convergence_kernel_fields.sql')) \
    if False else open(
        __file__.rsplit('/00_ARCHITECTURE/', 1)[0]
        + '/platform/supabase/migrations/1085_kala_convergence_kernel_fields.sql').read()

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

done(kind="POST-FIX BEHAVIOUR")  # noqa: F405
