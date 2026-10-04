import json, os, sys
from gen_brief import render
from gen_index import build, ORDER
import content_nimitta, content_muhurta_sodhana, content_b, content_c
C = [content_nimitta.NIMITTA, content_muhurta_sodhana.MUHURTA, content_muhurta_sodhana.SODHANA, content_b.PRATIKARA, content_b.SUDDHA, content_b.SANKRAMA, content_c.PRAMANA, content_c.PHALADESA, content_c.RECTIFICATION]
led = json.load(open('/Users/Dev/suvarna-evidence/A_L4/data/ledger_ph.json'))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
for c in C:
    c['ledger_ids'] = sorted({r['gap_id'] for r in led if r['asset'] == c['id']})
    txt = render(c)
    open(f"{OUT}/{c['id']}_ELEVATION_BRIEF_v1_0.md", 'w').write(txt + '\n')
    print(c['id'], len(txt))
open(f"{OUT}/INDEX.md", 'w').write(build(C) + '\n')
print('INDEX', os.path.getsize(f"{OUT}/INDEX.md"))
