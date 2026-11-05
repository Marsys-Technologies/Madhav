# Transcription of BPHS (Santhanam) Ch.66 rekhaprada lists (as printed in chunks bphs_pg0846..0857) and dot lists
import re,subprocess,json
ALL=['S','M','Ma','Me','J','V','Sa','A']
name={'S':'sun','M':'moon','Ma':'mars','Me':'mercury','J':'jupiter','V':'venus','Sa':'saturn','A':'lagna'}
def P(s): return s.split()
# REKHA lists: target -> {house: contributors}
R={}
R['S']={1:P('Sa Ma S'),2:P('Sa Ma S'),8:P('Sa Ma S'),5:P('J Me'),3:P('Me M A'),4:P('A S Sa Ma'),10:P('A S Sa Ma Me M'),11:P('S M Ma Me J Sa A'),12:P('A V Me'),6:P('A V Me J M'),7:P('S Ma Sa V'),9:P('S Ma Sa Me J')}
R['M']={1:P('Me M J'),2:P('J Ma'),3:P('Me S M Ma Sa V A'),4:P('J V Me'),5:P('Ma Me V Sa'),6:P('S M Ma Sa A'),7:P('S M J Me V'),8:P('S Me J'),9:P('V M'),10:P('S Me J V M A Ma'),11:ALL,12:[]}
R['Ma']={1:P('A Sa Ma'),2:P('Ma'),3:P('A Me M S'),4:P('Sa Ma'),5:P('Me S'),6:P('Me M J S A V'),7:P('Sa Ma'),8:P('Sa Ma V'),9:P('Sa'),10:P('Ma S J Sa A'),11:ALL,12:P('J V')}
R['Me']={1:P('A Sa Ma V Me'),2:P('A Ma M V Sa'),3:P('V Me'),4:P('A M Sa V Ma'),5:P('Me Sa V'),6:P('J Me S M A'),7:P('Ma Sa'),8:P('Ma Sa A M V J'),9:P('Sa Ma S Me V'),10:P('A Sa Me M'),11:ALL,12:P('J Me S')}
R['J']={5:P('V M A Me Sa'),6:P('V A Me Sa'),7:P('A Ma J S M'),8:P('J S Ma'),9:P('V S A M Me'),10:P('J Me Ma S V A'),11:[c for c in ALL if c!='Sa'],12:P('Sa')}
R['V']={1:P('A V M'),2:P('A V M'),3:P('A V M Me Sa Ma'),4:P('A V M Sa Ma'),5:P('A Me M J Sa V'),6:P('Me Ma'),7:[],8:P('V S M J A Sa'),9:[c for c in ALL if c!='S'],10:P('V J Sa'),11:ALL,12:P('Ma M S')}
R['Sa']={1:P('S A'),2:P('S'),3:P('A M Ma Sa'),4:P('A S'),5:P('J Sa Ma'),6:[c for c in ALL if c!='S'],7:P('S'),8:P('S Me'),9:P('Me'),10:P('S Ma A Me'),11:ALL,12:P('Ma Me J V')}
R['A']={1:P('Sa Me V J Ma'),2:P('Me J V'),3:P('A S M Ma V Sa'),4:P('S Me J V Sa'),5:P('J V'),6:[c for c in ALL if c!='V'],7:P('J'),8:P('Me V'),9:P('J V'),10:[c for c in ALL if c!='V'],11:[c for c in ALL if c!='V'],12:P('S M')}
# DOT lists (second, independent paragraph)
D={}
D['S']={1:P('A M J V Me'),2:P('A M J V Me'),3:P('S Sa J V Ma'),4:P('Me M V J'),5:P('S Sa M A Ma V'),6:P('S Sa Ma'),7:P('A Me J M'),8:P('A M J V Me'),9:P('A M V'),10:P('J V'),11:P('V'),12:P('S M Ma J Sa')}
D['M']={1:P('A S Ma Sa V'),2:P('A Me S M Sa V'),3:P('J'),4:P('S Sa M A Ma'),5:P('A M J S'),6:P('V Me J'),7:P('Ma A Sa'),8:P('Ma A Sa V M'),9:P('A S Ma Sa Me J'),10:P('Sa'),11:[],12:ALL}
D['Ma']={1:P('S M Me J V'),2:P('A S M Me J V Sa'),3:P('V Ma J Sa'),4:P('S M Me J V A'),5:P('M Ma J V A'),6:P('Ma Sa'),7:P('Me M S V J A'),8:P('Me M S A J'),9:P('S M Ma Me J V A'),10:P('V M Me'),11:[],12:P('S Sa Me M A Ma')}
D['Me']={1:P('S M J'),2:P('J S Me'),3:P('A S Ma Sa M J'),4:P('Me S J'),5:P('J Ma M Sa A'),6:P('V Sa Ma'),7:P('Me M A S V J'),8:P('Me S'),9:P('J M A'),10:P('S J V'),11:[],12:P('A M Ma Sa V')}
D['J']={1:P('V M Sa'),2:P('Sa'),3:P('A Ma M Me V'),4:P('V Sa M'),5:P('S J Ma'),6:P('J Ma S M'),7:P('Me V Sa'),8:P('A Sa V M Me'),9:P('Sa Ma J'),10:P('M Sa'),11:P('Sa'),12:[c for c in ALL if c!='Sa']}
D['V']={1:P('S Ma Me J Sa'),2:P('S Ma Me J Sa'),3:P('J S'),4:P('S Me J'),5:P('S Ma'),6:P('V S M Sa A J'),7:ALL,8:P('Ma Me'),9:P('S'),10:P('A Ma Me M S'),11:[],12:P('A Sa Me V J')}
D['Sa']={1:P('M Ma Me J V Sa'),2:P('M Ma Me J V Sa A'),3:P('J S Me V'),4:P('M Ma Me J V Sa'),5:P('V S M Me A'),6:P('S'),7:P('M Ma Me J V Sa A'),8:P('M Ma J V Sa A'),9:P('S M Ma J V Sa A'),10:P('M J V Sa'),11:[],12:P('A M Sa S')}
D['A']={1:P('A S M'),2:P('A Ma M S Sa'),3:P('J Me'),4:P('A M Ma'),5:P('A M Ma Me Sa S'),6:P('V'),7:[c for c in ALL if c!='J'],8:P('A S M Ma J Sa'),9:P('A S M Ma Me Sa'),10:P('V'),11:P('V'),12:P('A Ma Me J V Sa')}
def db():
    out=subprocess.run(['/Users/Dev/suvarna-evidence/TrackI/ifl0/rq.sh',"select constant_id,value_text from reference_constants where category='ashtakavarga'"],capture_output=True,text=True).stdout.splitlines()[1:-1]
    return {l.split('|')[0]:[int(x) for x in l.split('|')[1].split(',')] for l in out}
dbv=db()
inv={n:k for k,n in name.items()}
res=[]
for t in ALL:
  for c in ALL:
    rid=f'ashtakavarga_{name[t]}_from_{name[c]}'
    rekha=sorted(h for h in range(1,13) if t in R and h in R[t] and c in R[t][h]) if t!='J' or True else None
    known_r = set(R[t].keys())==set(range(1,13)) if t in R else False
    # houses where rekha text known
    rk={h for h in R[t] if c in R[t][h]}
    rknown=set(R[t].keys())
    dk=None
    if t in D:
        dk={h for h in range(1,13) if c not in D[t][h]}  # rekha by complement of dots
    dbset=set(dbv[rid])
    res.append((rid,sorted(dbset),sorted(rk) if len(rknown)==12 else None,sorted(dk) if dk is not None else None,sorted(rknown)))
bad=0
for rid,dbs,rk,dk,rkn in res:
    flags=[]
    if rk is not None and rk!=dbs: flags.append(f'REKHA!={rk}')
    if dk is not None and dk!=dbs: flags.append(f'DOT!={dk}')
    if rk is not None and dk is not None and rk!=dk: flags.append('TEXT_INTERNAL_CONFLICT')
    if rk is None and dk is None: flags.append('NO_FULL_SOURCE')
    if flags: bad+=1; print(rid,dbs,flags)
print('rows',len(res),'flagged',bad)
json.dump({r[0]:{'db':r[1],'rekha':r[2],'dotcompl':r[3]} for r in res},open('/private/tmp/claude-504/scratch/curation/bg_reference_B/av_compare.json','w'))
