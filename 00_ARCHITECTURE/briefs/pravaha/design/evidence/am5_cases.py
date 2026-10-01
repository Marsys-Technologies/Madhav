from am5_model import *
import sys
COMP=dict(av="1157:lahiri_av_v1:"+sha("decl-row")[:12],dasha=sha("dasha-demo"),vec={"bg_transit_rules":"d1","bg_transit_av_gates":"d2"},l1=sha("l1-demo"))
P1A=("jupiter","residence","lord","lord_of:7","dasha_lord","self"); P1B=("jupiter","residence","occupant","occupant_of:7","dasha_lord","self")
P5A=("saturn","residence","av_qualifier","house_span:7","lagna","self"); P5B=("saturn","residence","av_qualifier","house_span:8","lagna","self")
def commit(path,ver,obs,cls="marriage"): return [uid(ob_bytes(cls,path,ver,*o)) for o in obs]
def base(p5a_obs=True, verify=True, pin_p5a="included"):
    d=DB(); d.registry={("p1","1.0"),("p5a","1.0")}; d.put_snapshot(COMP)
    d.put_inventory("marriage",H,d.snapshot['digest'])
    d.put_pin("marriage","p1","1.0","included",commit("p1","1.0",[P1A,P1B]))
    if pin_p5a=="included": d.put_pin("marriage","p5a","1.0","included",commit("p5a","1.0",[P5A,P5B]))
    elif pin_p5a=="computed_empty": d.put_pin("marriage","p5a","1.0","computed_empty")
    ids=[d.put_ob("marriage","p1","1.0",o) for o in (P1A,P1B)]
    if pin_p5a=="included" and p5a_obs: ids+= [d.put_ob("marriage","p5a","1.0",o) for o in (P5A,P5B)]
    for i in ids: d.put_iv("marriage",i,H,"searched_complete")
    d.inv['marriage']['partition']=True
    if verify: d.verif['marriage']={'digest':sha(inv_preimage(d.inv['marriage']))}
    return d
def run(name,fn):
    try:
        r=fn(); print(f"{name}: {r}")
    except Refused as e: print(f"{name}: REFUSED AT INSERT -> {e}")
print("baseline:",base().violations())
# C1 Codex W2 exactly: P5a pinned included, committed ids declared, obligations never inserted, P1 fully covered, partition same, digest recomputed from stored rows
def c1():
    d=base(p5a_obs=False, verify=False)
    d.verif['marriage']={'digest':sha(inv_preimage(d.inv['marriage']))}  # verifier that just hashes stored rows
    return d.violations()
run("C1 W2 as written",c1)
# C1b: attacker tries to dodge by committing nothing for an included pin
run("C1b included pin with empty commitment",lambda: DB().__class__ and (lambda d:(d.registry.add(("p5a","1.0")),d.put_snapshot(COMP),d.put_inventory("marriage",H,d.snapshot['digest']),d.put_pin("marriage","p5a","1.0","included",[])))(DB()))
# C2 pin absent for a sealed registry path
def c2():
    d=base(pin_p5a="none"); d.verif['marriage']={'digest':sha(inv_preimage(d.inv['marriage']))}; return d.violations()
run("C2 absent pin",c2)
# C3 computed_empty declared but real derivation is non-empty; verifier derives the true set
def c3():
    d=base(pin_p5a="computed_empty")
    true=copy.deepcopy(d.inv['marriage']); true['pins'][("p5a","1.0")]={'disp':'included','committed':set(commit("p5a","1.0",[P5A,P5B])),'reason':''}
    for o in (P5A,P5B):
        by=ob_bytes("marriage","p5a","1.0",*o); true['obs'][uid(by)]={'path':'p5a','ver':'1.0','bytes':by}
    d.verif['marriage']={'digest':sha(inv_preimage(true))}   # independent re-derivation
    return d.violations()
run("C3 false computed_empty",c3)
# C3b computed_empty with no verification row
def c3b():
    d=base(pin_p5a="computed_empty",verify=False); return d.violations()
run("C3b no verification row",c3b)
# C5 genuinely empty set: verifier agrees
def c5():
    d=base(pin_p5a="computed_empty"); return d.violations()
run("C5 genuine computed_empty, verifier agrees",c5)
# C4 obligations present, intervals absent for one
def c4():
    d=base(verify=False)
    d.inv['marriage']['iv']=[r for r in d.inv['marriage']['iv'] if r['ob']!=uid(ob_bytes("marriage","p5a","1.0",*P5B))]
    d.verif['marriage']={'digest':sha(inv_preimage(d.inv['marriage']))}; return d.violations()
run("C4 obligation without intervals",c4)
# C7 extra uncommitted obligation
run("C7 uncommitted obligation",lambda: base().put_ob("marriage","p5a","1.0",("mars","aspect","lord","lord_of:7","lagna","self")))
# C8 intervals from a different input snapshot
def c8a():
    d=base(); oid=next(iter(d.inv['marriage']['obs'])); d.put_iv("marriage",oid,J,"searched_complete",input_=sha("other-l1-snapshot"))
run("C8a interval bound to different input_digest",c8a)
run("C8b second snapshot in same generation",lambda: base().put_snapshot(dict(COMP,l1=sha("l1-other"))))
# C9 L1 rebuilt after search, before seal
run("C9 L1 drift before seal",lambda: base().violations(l1_now=sha("l1-REBUILT")))
run("C9b manifest input vector changed",lambda: base().violations(vec_now={"bg_transit_rules":"d1","bg_transit_av_gates":"d9"}))
# C11/C12 interval overlap and horizon
def c11():
    d=base(); oid=next(iter(d.inv['marriage']['obs'])); d.put_iv("marriage",oid,J,"searched_unqualified")
run("C11 overlapping interval",c11)
def c12():
    d=base(); oid=next(iter(d.inv['marriage']['obs'])); d.put_iv("marriage",oid,("2025-03-01T00:00:00Z","2025-03-02T00:00:00Z"),"searched_complete")
run("C12 interval outside horizon",c12)
# C14 missing_inputs interval
def c14():
    d=base(verify=False); oid=uid(ob_bytes("marriage","p5a","1.0",*P5A))
    d.inv['marriage']['iv']=[r for r in d.inv['marriage']['iv'] if r['ob']!=oid]
    d.put_iv("marriage",oid,H,"missing_inputs"); d.verif['marriage']={'digest':sha(inv_preimage(d.inv['marriage']))}; return d.violations()
run("C14 missing_inputs interval",c14)
# C15 changed-input retry digest
d1=base(); comp2=dict(COMP,l1=sha("l1-rebuilt"))
d2=DB(); d2.registry=d1.registry; d2.put_snapshot(comp2)
print("C15 same targets/paths/convention, different L1: input digests differ:",d1.snapshot['digest'][:12],d2.snapshot['digest'][:12])
d2.put_inventory("marriage",H,d2.snapshot['digest'])
for k,v in d1.inv['marriage']['pins'].items(): d2.inv['marriage']['pins'][k]=copy.deepcopy(v)
d2.inv['marriage']['obs']=copy.deepcopy(d1.inv['marriage']['obs'])
print("   inventory_digest:",sha(inv_preimage(d1.inv['marriage']))[:16],"vs",sha(inv_preimage(d2.inv['marriage']))[:16])
# C16 seal replay: first seal passes; registry advances; replay uses replay branch (no registry accounting)
d=base(); print("C16 initial seal violations:",d.violations(first=True))
d.registry.add(("p7","1.0"))
print("   registry advance, FIRST-seal predicate (what v0.4 trigger would apply to a replay):",[v for v in d.violations(first=True)])
print("   replay branch (already sealed -> integrity only):",d.violations(first=False))
# W1 preimage publication
d=DB(); d.registry={("p1","1.0"),("p6","1.0")}; d.put_snapshot(COMP); d.put_inventory("marriage",H,d.snapshot['digest'])
d.put_pin("marriage","p1","1.0","included",commit("p1","1.0",[P1A,P1B]))
d.inv['marriage']['pins'][("p6","1.0")]={'disp':'excluded','committed':set(),'reason':'on_demand_tier'}
for o in (P1A,P1B): d.put_ob("marriage","p1","1.0",o)
pre,dg=input_digest(COMP)
print("---- INPUT PREIMAGE\n"+pre+"\ninput_digest="+dg)
ip=inv_preimage(d.inv['marriage']); print("---- INVENTORY PREIMAGE\n"+ip+"\ninventory_digest="+sha(ip))
for nm,rows in (("H1",[(uid(ob_bytes("marriage","p1","1.0",*P1A)),*J),(uid(ob_bytes("marriage","p1","1.0",*P1B)),*F)]),("H2",[(uid(ob_bytes("marriage","p1","1.0",*P1A)),*H),(uid(ob_bytes("marriage","p1","1.0",*P1B)),*H)])):
    s2="\n".join(sorted(f"{i}|{a}|{b}|searched_complete|{dg}" for i,a,b in rows)); print("---- LEDGER PREIMAGE "+nm+"\n"+s2+"\nledger_digest="+sha(s2))
