"""Adversarial cases for AM-5 (draft v0.6). A LOGIC check of the specified predicates, not Postgres.
Every case asserts its expected outcome; the script exits non-zero if any assertion fails."""
import sys
from am5_model import *
COMP=dict(av="1157:lahiri_av_v1:"+sha("decl-row")[:12],dasha=sha("dasha-demo"),vec={"bg_transit_rules":"d1","bg_transit_av_gates":"d2"},l1=sha("l1-demo"))
P1A=("jupiter","residence","lord","lord_of:7","dasha_lord","self"); P1B=("jupiter","residence","occupant","occupant_of:7","dasha_lord","self")
P5A=("saturn","residence","av_qualifier","house_span:7","lagna","self"); P5B=("saturn","residence","av_qualifier","house_span:8","lagna","self")
B_P6="spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P6"; B_EMPTY="oracle:O-RP-8"
FAILS=[]
def commit(path,ver,obs,cls="marriage"): return [uid(ob_bytes(cls,path,ver,*o)) for o in obs]
def refresh(d): d.verif['marriage']={'digest':sha(inv_preimage(d.inv['marriage']))}
def base(p5a_obs=True, verify=True, pin_p5a="included", p6=True):
    d=DB(); d.registry={("p1","1.0"),("p5a","1.0")}|({("p6","1.0")} if p6 else set()); d.put_snapshot(COMP)
    d.put_inventory("marriage",H,d.snapshot['digest'])
    d.put_pin("marriage","p1","1.0","included",commit("p1","1.0",[P1A,P1B]))
    if p6: d.put_pin("marriage","p6","1.0","excluded",reason="on_demand_tier",basis=B_P6)
    if pin_p5a=="included": d.put_pin("marriage","p5a","1.0","included",commit("p5a","1.0",[P5A,P5B]))
    elif pin_p5a=="computed_empty": d.put_pin("marriage","p5a","1.0","computed_empty",basis=B_EMPTY)
    ids=[d.put_ob("marriage","p1","1.0",o) for o in (P1A,P1B)]
    if pin_p5a=="included" and p5a_obs: ids+=[d.put_ob("marriage","p5a","1.0",o) for o in (P5A,P5B)]
    for i in ids: d.put_iv("marriage",i,H,"searched_complete")
    d.inv['marriage']['partition']=True
    if verify: refresh(d)
    return d
def kinds(v): return sorted({x[1] for x in v})
def expect(name,fn,want):
    try: got=fn()
    except Refused as e: got=("REFUSED",str(e)[:70])
    if isinstance(got,list): got=kinds(got)
    ok=(got==want) if not callable(want) else want(got)
    print(("PASS " if ok else "FAIL ")+name+" -> "+str(got))
    if not ok: FAILS.append(name)
expect("baseline seals clean",lambda: base().violations(),[])
def c1():
    d=base(p5a_obs=False,verify=False); refresh(d); return d.violations()
expect("C1 Codex W2 as written",c1,["committed_set_mismatch"])
expect("C1b included pin, empty commitment",lambda:(lambda d:(d.registry.add(("p5a","1.0")),d.put_snapshot(COMP),d.put_inventory("marriage",H,d.snapshot['digest']),d.put_pin("marriage","p5a","1.0","included",[])))(DB()),lambda g:g[0]=="REFUSED")
def c2():
    d=base(pin_p5a="none"); refresh(d); return d.violations()
expect("C2 absent pin for sealed registry path",c2,["registry_unaccounted_path"])
def c3():
    d=base(pin_p5a="computed_empty"); true=copy.deepcopy(d.inv['marriage'])
    true['pins'][("p5a","1.0")]={'disp':'included','committed':set(commit("p5a","1.0",[P5A,P5B])),'reason':'','ruling':None,'basis':None}
    for o in (P5A,P5B):
        by=ob_bytes("marriage","p5a","1.0",*o); true['obs'][uid(by)]={'path':'p5a','ver':'1.0','bytes':by}
    d.verif['marriage']={'digest':sha(inv_preimage(true))}; return d.violations()
expect("C3 false computed_empty (verifier derives non-empty)",c3,["verification_missing_or_mismatch"])
expect("C3b no verification row",lambda: base(pin_p5a="computed_empty",verify=False).violations(),["verification_missing_or_mismatch"])
def c3c():  # writer commits a smaller included set; verifier derives the full set
    d=DB(); d.registry={("p1","1.0")}; d.put_snapshot(COMP); d.put_inventory("marriage",H,d.snapshot['digest'])
    d.put_pin("marriage","p1","1.0","included",commit("p1","1.0",[P1A])); i=d.put_ob("marriage","p1","1.0",P1A); d.put_iv("marriage",i,H,"searched_complete"); d.inv['marriage']['partition']=True
    full=copy.deepcopy(d.inv['marriage']); full['pins'][("p1","1.0")]['committed']=set(commit("p1","1.0",[P1A,P1B])); by=ob_bytes("marriage","p1","1.0",*P1B); full['obs'][uid(by)]={'path':'p1','ver':'1.0','bytes':by}
    d.verif['marriage']={'digest':sha(inv_preimage(full))}; return d.violations()
expect("C3c smaller committed AND stored set",c3c,["verification_missing_or_mismatch"])
expect("C4 obligation without intervals",lambda:(lambda d:(d.inv['marriage'].__setitem__('iv',[r for r in d.inv['marriage']['iv'] if r['ob']!=uid(ob_bytes("marriage","p5a","1.0",*P5B))]),refresh(d),d.violations())[-1])(base()),["obligation_uncovered"])
expect("C5 genuine computed_empty, verifier agrees",lambda: base(pin_p5a="computed_empty").violations(),[])
expect("C7 uncommitted obligation",lambda: base().put_ob("marriage","p5a","1.0",("mars","aspect","lord","lord_of:7","lagna","self")),lambda g:g[0]=="REFUSED")
expect("C8a interval with different input_digest",lambda:(lambda d:d.put_iv("marriage",next(iter(d.inv['marriage']['obs'])),J,"searched_complete",input_=sha("other")))(base()),lambda g:g[0]=="REFUSED")
expect("C8b second snapshot, same generation",lambda: base().put_snapshot(dict(COMP,l1=sha("l1-other"))),lambda g:g[0]=="REFUSED")
expect("C9 L1 drift before seal",lambda: base().violations(l1_now=sha("l1-REBUILT")),["input_snapshot_drift"])
expect("C9b manifest vector changed",lambda: base().violations(vec_now={"bg_transit_rules":"d1","bg_transit_av_gates":"d9"}),["input_vector_mismatch"])
expect("C11 overlapping interval",lambda:(lambda d:d.put_iv("marriage",next(iter(d.inv['marriage']['obs'])),J,"searched_unqualified"))(base()),lambda g:g[0]=="REFUSED")
expect("C12 interval outside horizon",lambda:(lambda d:d.put_iv("marriage",next(iter(d.inv['marriage']['obs'])),("2025-03-01T00:00:00Z","2025-03-02T00:00:00Z"),"searched_complete"))(base()),lambda g:g[0]=="REFUSED")
def c14():
    d=base(verify=False); oid=uid(ob_bytes("marriage","p5a","1.0",*P5A))
    d.inv['marriage']['iv']=[r for r in d.inv['marriage']['iv'] if r['ob']!=oid]; d.put_iv("marriage",oid,H,"missing_inputs"); refresh(d); return d.violations()
expect("C14 missing_inputs interval",c14,["missing_inputs_present","obligation_uncovered"])
# C15 digests differ under changed L1 while targets/paths/convention identical
d1=base(); d2=DB(); d2.registry=d1.registry; d2.put_snapshot(dict(COMP,l1=sha("l1-rebuilt"))); d2.put_inventory("marriage",H,d2.snapshot['digest'])
d2.inv['marriage']['pins']=copy.deepcopy(d1.inv['marriage']['pins']); d2.inv['marriage']['obs']=copy.deepcopy(d1.inv['marriage']['obs'])
expect("C15 changed L1 -> different input and inventory digests",lambda:(d1.snapshot['digest']!=d2.snapshot['digest'] and sha(inv_preimage(d1.inv['marriage']))!=sha(inv_preimage(d2.inv['marriage']))),True)
# C16 full lifecycle: initial seal -> identical replay -> registry advance -> replay -> post-seal mutation -> wrong manifest -> first seal after advance
d=base()
expect("C16.1 initial seal",lambda:d.seal('M1'),"sealed")
expect("C16.2 identical replay",lambda:d.seal('M1'),"replay_noop")
d.registry.add(("p7","1.0"))
expect("C16.3 registry advance, replay again (no registry accounting)",lambda:d.seal('M1'),"replay_noop")
expect("C16.4 replay with a different manifest_id",lambda:d.seal('M2'),lambda g:g[0]=="REFUSED")
expect("C16.5 post-seal mutation (new interval)",lambda:d.put_iv("marriage",next(iter(d.inv['marriage']['obs'])),J,"searched_unqualified"),lambda g:g[0]=="REFUSED")
d2=base(); d2.registry.add(("p7","1.0"))
expect("C16.6 FIRST seal after registry advance is refused",lambda:d2.seal('M1'),lambda g:g[0]=="REFUSED" and "registry_unaccounted_path" in g[1])
# F-2: exclusion evidence bound into the verified preimage
def pre_with(**kw):
    d=base(); p=d.inv['marriage']['pins'][("p6","1.0")]; p.update(kw); return sha(inv_preimage(d.inv['marriage']))
ref=sha(inv_preimage(base().inv['marriage']))
expect("M1 changing basis changes inventory_digest",lambda: pre_with(basis="spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P5a")!=ref,True)
expect("M2 changing ruling_ref changes inventory_digest",lambda: pre_with(ruling="R-9")!=ref,True)
expect("M3 changing exclusion reason changes inventory_digest",lambda: pre_with(reason="not_applicable_to_class")!=ref,True)
def m4():  # writer silently edits an exclusion's basis after verification -> seal must refuse
    d=base(); d.inv['marriage']['pins'][("p6","1.0")]['basis']="spec:GOCHARA_DESIGN_SPECS@1.4#§2.2/P5a"; return d.violations()
expect("M4 basis edited after verification -> seal refuses",m4,["verification_missing_or_mismatch"])
def m5():  # verifier re-derives a DIFFERENT (degrading) exclusion than the writer declared
    d=base(); t=copy.deepcopy(d.inv['marriage']); t['pins'][("p6","1.0")].update(reason="disabled_form",ruling="R-9",basis="ruling:R-9"); d.verif['marriage']={'digest':sha(inv_preimage(t))}; return d.violations()
expect("M5 writer under-declares (non-degrading) what verifier derives as degrading",m5,["verification_missing_or_mismatch"])
def m6a():
    d=base(p6=False); d.registry.add(("p6x","1.0")); d.put_pin("marriage","p6x","1.0","excluded",reason="disabled_form",basis=B_P6)
expect("M6a degrading exclusion without ruling_ref refused (for that reason)",m6a,lambda g:g[0]=="REFUSED" and "ruling_ref" in g[1])
def m6b():
    d=base(p6=False); d.registry.add(("p6x","1.0")); d.put_pin("marriage","p6x","1.0","excluded",reason="disabled_form",ruling="R-9",basis="free prose that is not a reference")
expect("M6b basis outside the closed grammar refused",m6b,lambda g:g[0]=="REFUSED" and "grammar" in g[1])
def m6c():
    d=base(p6=False); d.registry.add(("p6x","1.0")); d.put_pin("marriage","p6x","1.0","excluded",reason="on_demand_tier",ruling="R-9",basis=B_P6)
expect("M6c ruling_ref on a non-degrading reason refused",m6c,lambda g:g[0]=="REFUSED" and "ruling_ref" in g[1])
# W1 vectors
d=DB(); d.registry={("p1","1.0"),("p6","1.0")}; d.put_snapshot(COMP); d.put_inventory("marriage",H,d.snapshot['digest'])
d.put_pin("marriage","p1","1.0","included",commit("p1","1.0",[P1A,P1B])); d.put_pin("marriage","p6","1.0","excluded",reason="on_demand_tier",basis=B_P6)
for o in (P1A,P1B): d.put_ob("marriage","p1","1.0",o)
pre,dg=input_digest(COMP); print("---- INPUT PREIMAGE\n"+pre+"\ninput_digest="+dg)
ip=inv_preimage(d.inv['marriage']); print("---- INVENTORY PREIMAGE\n"+ip+"\ninventory_digest="+sha(ip))
for nm,rows in (("H1",[(uid(ob_bytes("marriage","p1","1.0",*P1A)),*J),(uid(ob_bytes("marriage","p1","1.0",*P1B)),*F)]),("H2",[(uid(ob_bytes("marriage","p1","1.0",*P1A)),*H),(uid(ob_bytes("marriage","p1","1.0",*P1B)),*H)])):
    s2="\n".join(sorted(f"{i}|{a}|{b}|searched_complete|{dg}" for i,a,b in rows)); print("---- LEDGER PREIMAGE "+nm+"\n"+s2+"\nledger_digest="+sha(s2))
print("\n%d assertion(s) failed"%len(FAILS) if FAILS else "\nALL ASSERTIONS PASS"); sys.exit(1 if FAILS else 0)
