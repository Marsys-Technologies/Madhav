import itertools
rows=[l.strip().split('|') for l in open('fr.txt') if '|' in l]
rows=[r for r in rows if len(r)==3 and r[0]!='graha']
db={(a,b):r for a,b,r in rows}
P=['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']
# UK PG26 explicit list
uk_f={'Sun':['Moon','Mars','Jupiter'],'Moon':['Sun','Mercury'],'Mars':['Sun','Moon','Jupiter'],'Mercury':['Sun','Venus'],'Jupiter':['Sun','Moon','Mars'],'Venus':['Mercury','Saturn'],'Saturn':['Mercury','Venus']}
uk_e={'Sun':['Venus','Saturn'],'Moon':[],'Mars':['Mercury'],'Mercury':['Moon'],'Jupiter':['Mercury','Venus'],'Venus':['Sun','Moon'],'Saturn':['Sun','Moon','Mars']}
bad=[]
for g in P:
  for o in P:
    if g==o: continue
    exp='friend' if o in uk_f[g] else 'enemy' if o in uk_e[g] else 'neutral'
    if db[(g,o)]!=exp: bad.append((g,o,db[(g,o)],exp))
print('UK mismatches 42:',bad, 'present', sum(1 for g in P for o in P if g!=o and (g,o) in db))
# sloka 55 rule
owner={'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon','Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars','Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}
S=list(owner)
mt={'Sun':'Leo','Moon':'Taurus','Mars':'Aries','Mercury':'Virgo','Jupiter':'Sagittarius','Venus':'Libra','Saturn':'Aquarius'}
ex={'Sun':'Aries','Moon':'Taurus','Mars':'Capricorn','Mercury':'Virgo','Jupiter':'Cancer','Venus':'Pisces','Saturn':'Libra'}
bad2=[]
for g in P:
  i=S.index(mt[g])
  fr=set(owner[S[(i+n-1)%12]] for n in (2,4,5,8,9,12))|{owner[ex[g]]}
  en=set(owner[S[(i+n-1)%12]] for n in (3,6,7,10,11))
  for o in P:
    if o==g: continue
    f=o in fr; e=o in en
    exp='friend' if f and not e else 'enemy' if e and not f else 'neutral'
    if db[(g,o)]!=exp: bad2.append((g,o,db[(g,o)],exp,f,e))
print('rule (sl.55 natural only) mismatches:',bad2)
# node rows vs BPHS PG40 (node's view) and SC stanza 108
bphs={'Rahu':{'Sun':'enemy','Moon':'enemy','Mars':'enemy','Jupiter':'friend','Venus':'friend','Saturn':'friend','Mercury':'neutral'},
      'Ketu':{'Sun':'enemy','Moon':'enemy','Mars':'friend','Venus':'friend','Saturn':'friend','Mercury':'neutral','Jupiter':'neutral'}}
for n in ('Rahu','Ketu'):
  for o in P:
    print(n,'->',o,'DB',db[(n,o)],'BPHS',bphs[n][o],'DB-reverse(%s->%s)'%(o,n),db[(o,n)])
