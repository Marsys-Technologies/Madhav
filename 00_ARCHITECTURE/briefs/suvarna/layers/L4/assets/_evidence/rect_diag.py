#!/usr/bin/env python3
"""A.L4 read-only diagnosis of why phala_rectification.lel_fit_score is 0.0000 on every scored candidate.
Reads life_events, chart_dashas, chart_facts (SELECT only) and calls the repository's pure scoring functions with the writer's inputs and with two corrected inputs."""
import sys, collections
sys.path.insert(0, '/Users/Dev/suvarna-al4/platform/python-sidecar')
from datetime import datetime, timezone
from collect import q, C
import services.ph_rectification.engine as E
rows = q(f"select event_id, event_date, category, domain from life_events where chart_id='{C}' and event_date is not null order by event_date")
facts = q(f"select fact_subject, fact_value_text from chart_facts where chart_id='{C}' and ayanamsha_id='lahiri_chitrapaksha' and fact_category='graha_position' and fact_key='sign'")
SIGN = {"Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,"Virgo":5,"Libra":6,"Scorpio":7,"Sagittarius":8,"Capricorn":9,"Aquarius":10,"Pisces":11}
writer_idx = {r['fact_subject'].capitalize(): SIGN[r['fact_value_text']] for r in facts if r['fact_value_text'] in SIGN}
FULL = {'JUP':'Jupiter','KET_MEAN':'Ketu','MAR':'Mars','MER':'Mercury','MOON':'Moon','RAH_MEAN':'Rahu','SAT':'Saturn','SUN':'Sun','VEN':'Venus'}
fixed_idx = {FULL[r['fact_subject']]: SIGN[r['fact_value_text']] for r in facts if r['fact_subject'] in FULL and r['fact_value_text'] in SIGN}
def lord(d, lvl):
    r = q(f"select lord_graha from chart_dashas where chart_id='{C}' and system_id='vimshottari' and level_n={lvl} and ayanamsha_id='lahiri_chitrapaksha' and start_date<='{d}' and end_date>='{d}' order by start_date limit 1")
    return r[0]['lord_graha'].capitalize() if r else None
evs = []
for r in rows:
    d = r['event_date'][:10]; dt = datetime.fromisoformat(d).replace(tzinfo=timezone.utc)
    md = lord(d, 1)
    if md is None: continue
    ad = lord(d, 2)
    evs.append((r, dt, md, ad))
train = [x for x in evs if x[1] < E._FIREWALL_CUTOFF]
print('life_events with a placeable MD lord:', len(evs), '; pre-2020 (firewall training set):', len(train))
print('writer natal index keys:', sorted(writer_idx), '| resolvable full names among MD lords of training events:', sum(1 for x in train if x[2] in writer_idx), 'of', len(train))
def build(domain_of):
    return [E.TrainingEvent(str(x[0]['event_id']), x[1], domain_of(x[0]), x[2], 'month-exact', x[3]) for x in train]
cases = {
  'as written (compound domain slug + 3-letter fact subjects)': (build(lambda r: r['domain'] or r['category']), writer_idx),
  'category instead of compound domain, writer index': (build(lambda r: r['category']), writer_idx),
  'compound domain, full-name index': (build(lambda r: r['domain'] or r['category']), fixed_idx),
  'category + full-name index (both corrected)': (build(lambda r: r['category']), fixed_idx),
}
for name, (events, idx) in cases.items():
    out = {}
    for sign, i in (('Aries', 0), ('Taurus', 1), ('Pisces', 11)):
        m = E._score_dasha_match(i, events, idx); out[sign] = (m, round(m / (2 * len(events)), 4))
    print(f'{name}: matched,fit by candidate lagna sign ->', out)
print('events whose domain resolves to >=1 significator house (as written / category):',
      sum(1 for e in cases['as written (compound domain slug + 3-letter fact subjects)'][0] if E.domain_significator_houses(e.domain)),
      sum(1 for e in cases['category instead of compound domain, writer index'][0] if E.domain_significator_houses(e.domain)))
print('category values with no significator-house entry:', collections.Counter(x[0]['category'] for x in train if not E.domain_significator_houses(x[0]['category'])))
