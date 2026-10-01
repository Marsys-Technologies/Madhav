import hashlib,uuid,json,copy
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def uid(s):
    b=bytearray(hashlib.sha256(s.encode()).digest()[:16]); b[6]=(b[6]&0x0f)|0x80; b[8]=(b[8]&0x3f)|0x80
    return str(uuid.UUID(bytes=bytes(b)))
import re
BASIS_RE=re.compile(r'^(spec:[A-Za-z0-9_.-]+@[0-9][0-9A-Za-z.]*#[^|\n%]+|ruling:[A-Za-z0-9._-]+|oracle:[A-Za-z0-9._-]+)$')
RULING_RE=re.compile(r'^[A-Za-z0-9._-]+$')
EXCL_REASONS={'not_applicable_to_class','on_demand_tier','disabled_form','inputs_unavailable','tier_withheld_by_ruling'}
DEGRADING={'disabled_form','inputs_unavailable','tier_withheld_by_ruling'}
class Refused(Exception): pass
H=("2025-01-01T00:00:00Z","2025-03-01T00:00:00Z"); J=("2025-01-01T00:00:00Z","2025-02-01T00:00:00Z"); F=("2025-02-01T00:00:00Z","2025-03-01T00:00:00Z")
CONV="sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3"
def ob_bytes(cls,path,ver,agent,rel,role,target,frame,person): return "|".join([cls,path,ver,agent,rel,role,target,frame,person])
def input_digest(c):
    pre="\n".join(sorted([f"av_declarations={c['av']}",f"convention_id={CONV}",f"dasha_digest={c['dasha']}",
        f"input_generation_vector={json.dumps(c['vec'],sort_keys=True,separators=(',',':'))}",f"l1_facts_digest={c['l1']}"]))
    return pre,sha(pre)
def inv_preimage(inv):
    L=[f"convention={CONV}",f"horizon=[{inv['h'][0]},{inv['h'][1]})",f"input={inv['input']}"]
    for (p,v),pin in sorted(inv['pins'].items()):
        L.append(f"pin={p}|{v}|{pin['disp']}|{pin.get('reason','')}|{pin.get('ruling') or ''}|{pin.get('basis') or ''}|{','.join(sorted(pin['committed']))}")
    for oid,o in sorted(inv['obs'].items(), key=lambda kv:kv[1]['bytes']): L.append(f"ob={o['bytes']}")
    return "\n".join(L)
class DB:
    def __init__(s): s.registry=set(); s.snapshot=None; s.inv={}; s.sealed=set(); s.manifest={}; s.verif={}
    def _sealed_guard(s):
        if s.sealed: raise Refused('post-seal mutation refused (generation sealed)')
    # ---- insert-time guards
    def put_snapshot(s,comp):
        s._sealed_guard()
        if s.snapshot: raise Refused("PK(chart,generation): one snapshot per generation")
        pre,d=input_digest(comp); s.snapshot={'comp':comp,'digest':d,'vec':comp['vec']}
    def put_inventory(s,cls,h,input_):
        s._sealed_guard()
        if input_!=s.snapshot['digest']: raise Refused("inventory.input FK snapshot")
        s.inv[cls]={'h':h,'input':input_,'pins':{},'obs':{},'iv':[],'partition':None}
    def put_pin(s,cls,path,ver,disp,committed=(),reason='',ruling=None,basis=None):
        s._sealed_guard()
        if (path,ver) not in s.registry: raise Refused("FK rule_path_seal")
        c=sorted(set(committed))
        if disp=='included' and len(c)<1: raise Refused("pin CHECK: included needs >=1 committed ob_id")
        if disp in('computed_empty','excluded') and c: raise Refused("pin CHECK: computed_empty/excluded commit no ob_id")
        if disp=='included' and (reason or ruling or basis): raise Refused("pin CHECK: included carries no reason/ruling/basis")
        if disp in('computed_empty','excluded') and not basis: raise Refused("pin CHECK: basis required")
        if basis and not BASIS_RE.match(basis): raise Refused("pin CHECK: basis grammar (spec:<artifact>@<ver>#<anchor> | ruling:<id> | oracle:<id>)")
        if disp=='excluded':
            if reason not in EXCL_REASONS: raise Refused("pin CHECK: closed exclusion reason")
            if (reason in DEGRADING) != (ruling is not None): raise Refused("pin CHECK: ruling_ref iff degrading reason")
            if ruling is not None and not RULING_RE.match(ruling): raise Refused("pin CHECK: ruling_ref format")
        elif reason or ruling: raise Refused("pin CHECK: reason/ruling only on excluded")
        s.inv[cls]['pins'][(path,ver)]={'disp':disp,'committed':set(c),'reason':reason,'ruling':ruling,'basis':basis}
    def put_ob(s,cls,path,ver,fields):
        s._sealed_guard()
        by=ob_bytes(cls,path,ver,*fields); oid=uid(by); pin=s.inv[cls]['pins'].get((path,ver))
        if not pin or pin['disp']!='included': raise Refused("obligation needs an 'included' pin")
        if oid not in pin['committed']: raise Refused("obligation ob_id not in pin.committed_ob_ids")
        s.inv[cls]['obs'][oid]={'path':path,'ver':ver,'bytes':by}; return oid
    def put_iv(s,cls,oid,rng,state,input_=None):
        s._sealed_guard()
        inv=s.inv[cls]; input_=input_ or inv['input']
        if input_!=inv['input']: raise Refused("interval FK (chart,gen,input_digest) -> snapshot/inventory")
        if oid not in inv['obs']: raise Refused("interval FK obligation")
        if not(inv['h'][0]<=rng[0]<rng[1]<=inv['h'][1]): raise Refused("interval outside horizon / not [lo,hi)")
        for r in inv['iv']:
            if r['ob']==oid and rng[0]<r['hi'] and r['lo']<rng[1]: raise Refused("overlap trigger")
        inv['iv'].append({'ob':oid,'lo':rng[0],'hi':rng[1],'state':state,'input':input_})
    # ---- seal check
    def seal(s,manifest='M1',l1_now=None,vec_now=None):
        if s.sealed: return s.replay(manifest)
        v=s.violations(True,l1_now,vec_now)
        if v: raise Refused(v)
        s.sealed={'manifest':manifest,'digests':{c:sha(inv_preimage(i)) for c,i in s.inv.items()}}; return 'sealed'
    def replay(s,manifest):
        if manifest!=s.sealed['manifest']: raise Refused("replay: manifest_id differs from the existing seal")
        for c,i in s.inv.items():
            if sha(inv_preimage(i))!=s.sealed['digests'][c]: raise Refused("replay: stored inventory no longer recomputes to its sealed digest")
            if sha(inv_preimage(i))!=s.verif.get(c,{}).get('digest'): raise Refused("replay: verification row missing/mismatch")
        return 'replay_noop'
    def violations(s,first=True, l1_now=None, vec_now=None):
        v=[]
        if first:
            for p in s.registry:
                for cls,inv in s.inv.items():
                    if p not in inv['pins']: v.append((cls,'registry_unaccounted_path',p))
        for cls,inv in s.inv.items():
            if inv['partition'] is None: v.append((cls,'inventory_without_partition',''))
            if sha(inv_preimage(inv))!=s.verif.get(cls,{}).get('digest'): v.append((cls,'verification_missing_or_mismatch',''))
            for p,pin in inv['pins'].items():
                stored={o for o,x in inv['obs'].items() if (x['path'],x['ver'])==p}
                if stored!=pin['committed']: v.append((cls,'committed_set_mismatch',p,sorted(pin['committed']-stored)))
            for oid in inv['obs']:
                cov=[(r['lo'],r['hi']) for r in inv['iv'] if r['ob']==oid and r['state'] in('searched_complete','searched_unqualified')]
                cov.sort(); cur=inv['h'][0]
                for lo,hi in cov:
                    if lo<=cur: cur=max(cur,hi)
                if cur<inv['h'][1]: v.append((cls,'obligation_uncovered',oid[:8]))
                if any(r['ob']==oid and r['state']=='missing_inputs' for r in inv['iv']): v.append((cls,'missing_inputs_present',oid[:8]))
            if inv['input']!=s.snapshot['digest']: v.append((cls,'input_snapshot_mismatch',''))
        if l1_now is not None and l1_now!=s.snapshot['comp']['l1']: v.append(('*','input_snapshot_drift','l1'))
        if vec_now is not None and vec_now!=s.snapshot['vec']: v.append(('*','input_vector_mismatch',''))
        return v
