"""F-03 / E2: (a) L1 already writes sign-keyed AV rows; the engine reads only the legacy HOUSE-keyed category.
(b) Synthetic non-Aries chart: a HOUSE-keyed map looked up by transit SIGN returns another sign's bindus.
Both live charts are Aries lagna (house N == sign N), which hides (b). No DB; synthetic, injective data."""
from _common import *
head("S3 — ashtakavarga frame: what L1 writes vs what Sangam reads; non-Aries synthetic")
gs = grep('ga_writers/ga_strength_writer.py', r'ashtakavarga_bindu_sign|-SIGN_|-HOUSE_')
print("ga_strength_writer.py lines writing HOUSE/SIGN keys:", [i for i,_ in gs][:8])
ws = grep('pipeline/orchestrator/writers/ka_sangam.py', r"fact_category = 'ashtakavarga_bindu'")
print("ka_sangam.py reads category:", [(i,l.strip()) for i,l in ws])
lagna_sign = 10                                          # Capricorn rising → house 1 = sign 10
bindus_by_sign = {s: [4,2,6,1,7,3,5,0,8,2,5,6][s-1] for s in range(1,13)}   # synthetic BAV; sign1=4, sign10=2
house_keyed = {h: bindus_by_sign[((lagna_sign-1 + h-1) % 12) + 1] for h in range(1,13)}
ts = 1
print(f"  synthetic lagna=Capricorn(10); Saturn transits sign {ts} (Aries)")
print(f"  correct BAV (sign-keyed) for sign {ts}         : {bindus_by_sign[ts]}")
print(f"  HOUSE-keyed map[{ts}] (house 1 = Capricorn)      : {house_keyed[ts]}   ← returns Capricorn's bindus for an Aries transit")
aries = {h: bindus_by_sign[h] for h in range(1,13)}
print(f"  same lookup on an ARIES-lagna chart          : {aries[ts]} == {bindus_by_sign[ts]}  (frames coincide; bug invisible)")
assert house_keyed[ts] != bindus_by_sign[ts] and aries[ts] == bindus_by_sign[ts]
print("VERDICT: CONFIRMED — read `ashtakavarga_bindu_sign`; falsifier requires a non-Aries synthetic chart")
