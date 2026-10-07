import json, collections
from datetime import datetime, timezone, timedelta
UTC=timezone.utc
old=json.load(open("spans_old.json")); new=json.load(open("spans_new.json"))
assert len(old)==len(new)
diff=[]
for o,n in zip(old,new):
    assert o[:4]==n[:4]
    if o[4]!=n[4] or o[5]!=n[5]: diff.append((o,n))
print("roots", len(old), "| spans bit-identical (repr of both ends):", len(old)-len(diff), "| differing:", len(diff))
JD0=2440587.5
def t(jd): return datetime.fromtimestamp((float(jd)-JD0)*86400, UTC)
for o,n in diff:
    da=(float(n[4])-float(o[4]))*24; db=(float(n[5])-float(o[5]))*24
    print("  DIFF", o[0],o[1],o[2][6:14], "root", t(o[3]).isoformat()[:16], "start moves %.2f h, end moves %.2f h"%(da, db), "| arc", t(o[6]).isoformat()[:16], t(o[7]).isoformat()[:16])
rows=json.load(open("/Users/Dev/pravaha/run/HORIZON_EDGE_STRETCHES_20261005.json"))
def merged(spans_by, key, A, B):
    spans=sorted(s for s in spans_by[key] if s[0]<B and A<s[1])
    if not spans: return None
    m=[list(spans[0][:2])]
    for a,b,_ in spans[1:]:
        if abs((a-m[-1][1]).total_seconds())<2: m[-1][1]=max(m[-1][1],b)
        else: m.append([a,b])
    return m
def build(lst):
    by=collections.defaultdict(list)
    for r in lst: by[tuple(r[:3])].append((t(r[4]),t(r[5]),t(r[3])))
    return by
D0,D1=datetime(1998,1,1,tzinfo=UTC),datetime(2085,1,1,tzinfo=UTC)
for name,lst in (("NEW (PR 3156)",new),("OLD (main)",old)):
    by=build(lst); matched=bad=grazes=edge=0; badlist=[]
    for r in rows:
        A=datetime.fromisoformat(r["A"]); B=datetime.fromisoformat(r["B"])
        if A<=D0 or B>=D1: edge+=1; continue
        m=merged(by,(r["agent"],r["rel"],r["target"]),A,B)
        if m is None: grazes+=1; continue
        ok=len(m)==1 and abs((m[0][0]-A).total_seconds())<1800 and abs((m[0][1]-B).total_seconds())<1800
        if ok: matched+=1
        else: bad+=1; badlist.append((r["agent"],r["rel"],r["target"][6:14],A.isoformat()[:16],B.isoformat()[:16],[(x.isoformat()[:16],y.isoformat()[:16]) for x,y in m]))
    print(name,"whole domain: stretches",len(rows),"| matched (<30 min at both ends):",matched,"| graze (no root):",grazes,"| touching the domain edge:",edge,"| MISMATCH:",bad)
    for b in badlist[:8]: print("     MISMATCH",b)
    ov=0
    for k,v in by.items():
        v=sorted(v)
        for (a1,b1,_),(a2,b2,_) in zip(v,v[1:]):
            if a2<b1-timedelta(seconds=1): ov+=1
    print("   overlapping spans of one obligation:",ov)
