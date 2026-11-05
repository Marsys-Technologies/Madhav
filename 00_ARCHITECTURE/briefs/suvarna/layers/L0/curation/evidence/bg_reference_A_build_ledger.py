#!/usr/bin/env python3
# Builds ledger.json for bg_reference_A (read-only research; evidence quotes machine-verified in evidence.py)
import json, re, sys
sys.path.insert(0, '/private/tmp/claude-504/scratch/curation/bg_reference_A')
from evidence import E, get, cshort, tid, page

OUT = '/private/tmp/claude-504/scratch/curation/bg_reference_A/'
ASSET = 'bg_reference'
ED = {'bphs': 'Santhanam trans.', 'phaladeepika': 'Sastri trans. 1950', 'jataka_parijata': 'Sastri trans. 1932-33',
      'uttara_kalamrita': 'P.S. Sastri trans.', 'hora_sara': 'Santhanam trans.', 'saravali': 'attr. Santhanam trans.'}
NAME = {'bphs': 'BPHS', 'phaladeepika': 'Phaladipika', 'jataka_parijata': 'Jataka Parijata',
        'uttara_kalamrita': 'Uttara Kalamrita', 'hora_sara': 'Hora Sara', 'saravali': 'Saravali'}


def load(t):
    return [json.loads(l) for l in open(OUT + 'db_%s.jsonl' % t)]


def ev(key, role='supports', support='FACT', note=None):
    cid, quote, sl = get(key)
    assert quote, key
    d = {'text_id': tid(cid), 'chunk_id': cid, 'page': page(cid), 'sloka_printed': sl, 'quote': quote,
         'role': role, 'support': support, 'ekey': key}
    if note:
        d['note'] = note
    return d


def pd_adh(p):
    p = int(p)
    if 38 <= p <= 46: return 'Adh. I'
    if 71 <= p <= 80: return 'Adh. IV'
    if 193 <= p <= 203: return 'Adh. XV'
    return None


def cite(keys, label=None):
    """Page-anchored citation string pasteable into a citation column (house style)."""
    out = []
    order = []
    grp = {}
    for k in keys:
        cid, quote, sl = get(k)
        t = tid(cid)
        _pg = int(re.search(r'_pg(\d+)_', cid).group(1))
        gk = (t, sl, pd_adh(_pg) if t == 'phaladeepika' else None)
        if gk not in grp:
            grp[gk] = []
            order.append(gk)
        r = cshort(cid)
        if r not in grp[gk]:
            grp[gk].append(r)
    byt = {}
    for (t, sl, adh) in order:
        byt.setdefault(t, []).append((sl, adh, grp[(t, sl, adh)]))
    for t, items in byt.items():
        segs = []
        for sl, adh, refs in items:
            pg = int(refs[0].split(':PG')[1].split(':')[0])
            if sl and '(Notes)' in sl:
                shead = 'Sloka %s as printed, translator note' % sl.replace(' (Notes)', '')
            elif sl:
                shead = 'Sloka %s as printed' % sl
            else:
                shead = 'p.%d' % pg
            head = (adh + ', ' if adh else '') + shead
            segs.append('%s - %s' % (head, ', '.join(refs)))
        out.append('%s, %s (%s)' % (NAME[t], '; '.join(segs), ED[t]))
    return '; '.join(out)


ROWS = []


def row(table, key, claim, current, state, support, corpus, inference=None, proposed=None, action='none', q=None,
        cols=None, notes=None, unsourced_components=False):
    _seen = set(); _c = []
    for _e in corpus:
        _k = (_e['chunk_id'], _e['quote'])
        if _k not in _seen:
            _seen.add(_k); _c.append(_e)
    corpus = _c
    d = {
        'asset': ASSET, 'table': table, 'row_key': key, 'row_count': 1, 'claim': claim,
        'current_citation': current, 'state': state, 'support_class': support, 'corpus': corpus,
        'inference_step': inference, 'proposed_citation': proposed, 'proposed_action': action,
        'acharya_question': q,
    }
    if cols:
        d['column_findings'] = cols
    if notes:
        d['notes'] = notes
    if unsourced_components:
        d['has_unsourced_components'] = True
    ROWS.append(d)


def cf(column, state, note, **kw):
    d = {'column': column, 'state': state, 'note': note}
    d.update(kw)
    return d


# ----------------------------------------------------------------------------------------------------------
# 1. reference_planets
# ----------------------------------------------------------------------------------------------------------
EXALT = {'sun': (1, 10), 'moon': (2, 3), 'mars': (10, 28), 'mercury': (6, 15), 'jupiter': (4, 5), 'venus': (12, 27),
         'saturn': (7, 20)}
MT = {'sun': 5, 'moon': 2, 'mars': 1, 'mercury': 6, 'jupiter': 9, 'venus': 7, 'saturn': 11}
LORDS = {1: 'mars', 2: 'venus', 3: 'mercury', 4: 'moon', 5: 'sun', 6: 'mercury', 7: 'venus', 8: 'mars', 9: 'jupiter',
         10: 'saturn', 11: 'saturn', 12: 'jupiter'}
OWN = {}
for s_, l_ in LORDS.items():
    OWN.setdefault(l_, []).append(s_)
VIM = {'sun': 6, 'moon': 10, 'mars': 7, 'rahu': 18, 'jupiter': 16, 'saturn': 19, 'mercury': 17, 'ketu': 7, 'venus': 20}
BEN = {'sun': False, 'moon': True, 'mars': False, 'mercury': True, 'jupiter': True, 'venus': True, 'saturn': False,
       'rahu': False, 'ketu': False}
MT_KEY = {'sun': 'bphs_mt_sun', 'mars': 'bphs_mt_mars', 'mercury': 'bphs_mt_merc', 'jupiter': 'bphs_mt_jup',
          'venus': 'bphs_mt_ven', 'saturn': 'bphs_mt_sat'}
SIGN_NAME = {1: 'Aries', 2: 'Taurus', 3: 'Gemini', 4: 'Cancer', 5: 'Leo', 6: 'Virgo', 7: 'Libra', 8: 'Scorpio',
             9: 'Sagittarius', 10: 'Capricorn', 11: 'Aquarius', 12: 'Pisces'}
T = 'reference_planets'
KARAK_NOTE = ('karak_domains is a platform thematic tag list (e.g. surgery, technology, vehicles); BPHS Ch.3 sloka 12-13 '
              '(bphs:PG27:C1, OCR-corrupted) names only seven single-word karakatvas, so the array is not a classical '
              'assertion row-by-row')
for r in load(T):
    pid = r['planet_id']
    cur = r['source_citation']
    key = {'planet_id': pid}
    if pid in ('ascendant', 'midheaven'):
        row(T, key, 'Chart-angle pseudo-planet: identity row carrying only thematic karak_domains; no dignity data.', cur,
            'not_a_classical_claim', 'NONE', [], proposed=None, action='none',
            cols=[cf('karak_domains', 'not_a_classical_claim', 'platform thematic vocabulary for a chart point; ' + (
                'the lagna/10th-house significations themselves are sourced on reference_houses'))],
            notes=('Platform identity row. planet_id "%s" is not a graha; no exaltation/dignity values are asserted. '
                   'Existing citation names BPHS Ch.7, which in the held Santhanam edition is the chapter that prints '
                   'the kendra/bhava definitions (bphs:PG101:C1) - no adjustment needed.' % pid))
        continue
    if pid in EXALT:
        es, ed = EXALT[pid]
        assert (r['exaltation_sign'], float(r['exaltation_degree'])) == (es, float(ed)), pid
        assert r['debilitation_sign'] == (es + 5) % 12 + 1 or r['debilitation_sign'] == ((es + 6 - 1) % 12) + 1, pid
        assert r['mooltrikona_sign'] == MT[pid], pid
        assert sorted(r['own_signs']) == sorted(OWN[pid]), pid
        assert r['natural_benefic'] == BEN[pid], pid
        assert float(r['dasha_years']) == VIM[pid], pid
        corpus = [ev('bphs_exalt_signs'), ev('bphs_exalt_deg'), ev('bphs_debil7'), ev('pd_exalt_signs'),
                  ev('pd_mt'), ev('pd_lords')]
        if pid in MT_KEY:
            corpus.append(ev(MT_KEY[pid]))
        else:
            corpus.append(ev('jp_mt_moon', note='BPHS Ch.3 Moon moolatrikona clause is lost to OCR (bphs:PG38:C1 skips from Sun to Mars); Phaladipika sl.7 order gives Vrishabha as 2nd of the 7 and Jataka Parijata states it directly'))
        corpus += [ev('bphs_benefic'), ev('bphs_vim_names'), ev('bphs_vim_years'), ev('bphs_vim_table')]
        ckeys = ['bphs_exalt_signs', 'bphs_exalt_deg', 'bphs_debil7', 'pd_mt', 'pd_lords', 'bphs_benefic', 'bphs_vim_names',
                 'bphs_vim_years']
        if pid in MT_KEY:
            ckeys.insert(4, MT_KEY[pid])
        cols = [
            cf('exaltation_sign / exaltation_degree', 'sourced_fact',
               'BPHS Ch.3 sl.49-50: seven exaltation signs and deepest degrees 10,3,28,15,5,27,20 in Sun..Saturn order; matches DB (%s %s deg).' % (SIGN_NAME[es], ed)),
            cf('debilitation_sign', 'sourced_fact', 'BPHS sl.49-50: debilitation is the 7th sign from exaltation (DB %s).' % SIGN_NAME[r['debilitation_sign']]),
            cf('mooltrikona_sign', 'sourced_fact', 'Phaladipika Adh.I sl.7 (ordered list from the Sun) ' + (
                'and BPHS Ch.3 sl.51-54 state %s.' % SIGN_NAME[MT[pid]] if pid in MT_KEY else
                'states Vrishabha for the Moon; BPHS own clause for the Moon is OCR-lost.')),
            cf('own_signs', 'sourced_fact', 'Phaladipika Adh.I sl.6 sign-lord list (Mars,Venus,Mercury,Moon,Sun,Mercury,Venus,Mars,Jupiter,Saturn,Saturn,Jupiter); own sign = sign lorded. Equivalence lordship=own sign is definitional.'),
            cf('natural_benefic', 'sourced_fact', 'BPHS Ch.3 sl.11: Sun, Saturn, Mars, decreasing Moon, Rahu, Ketu are malefics, the rest benefics; Mercury malefic if joined to a malefic' + ('; the Moon is a benefic only when waxing' if pid == 'moon' else '') + '.'),
            cf('dasha_years', 'sourced_fact', 'BPHS Ch.46 sl.15 (printed at bphs:PG499) Vimshottari years 6,10,7,18,16,19,17,7,20; OCR "l\'1" read as 17, corroborated by table bphs:PG500:C1. Existing citation names Ch.3 only; years live in Ch.46.'),
            cf('karak_domains', 'not_a_classical_claim', KARAK_NOTE),
        ]
        row(T, key,
            '%s: exalted %s %s deg, debilitated %s, moolatrikona %s, own signs %s, natural %s, Vimshottari %s yrs.' % (
                pid.title(), SIGN_NAME[es], ed, SIGN_NAME[r['debilitation_sign']], SIGN_NAME[MT[pid]],
                '/'.join(SIGN_NAME[x] for x in sorted(OWN[pid])), 'benefic' if BEN[pid] else 'malefic', VIM[pid]),
            cur, 'sourced_fact', 'FACT', corpus, inference=None,
            proposed=cite(ckeys) + ('; Jataka Parijata, Slokas 26-28 as printed - jataka_parijata:PG45:C1 (Sastri trans. 1932-33)' if pid == 'moon' else ''),
            action='recite', cols=cols,
            notes=('existing_citation_unverifiable at chapter grain ("BPHS Ch.3"): resolved by text search to pages 37-38 (dignities), 26 (benefic/malefic) and, for dasha_years, Ch.46 pages 499-500. '
                   'The chapter label Ch.3 does resolve in the held edition (printed header "Chapter 3" at bphs:PG23/PG38) but does not contain the Vimshottari years.'),
            unsourced_components=False)
        continue
    # nodes
    if pid == 'rahu':
        corpus = [ev('bphs_rahu_ex'), ev('bphs_rahu_debil'), ev('bphs_node_mt', role='note'), ev('bphs_node_own', role='note'),
                  ev('bphs_node_own_alt', role='variant'), ev('bphs_nodes_exalt_views', role='note'), ev('hs_node_views', role='variant'),
                  ev('jp_rahu', role='variant', support='FACT', note='Jataka Parijata (OCR-garbled) gives Rahu: moolatrikona Kumbha, exaltation Mithuna (Gemini), own Kanya - a different view from BPHS Taurus'),
                  ev('bphs_benefic'), ev('bphs_vim_names'), ev('bphs_vim_years'), ev('bphs_vim_table')]
        cols = [
            cf('exaltation_sign', 'sourced_fact', 'BPHS Ch.47 (Rahu Dasa, sl.34-39 as printed, bphs:PG573:C2): "The sign of exaltation of Rahu is Taurus" - matches DB 2 and the DB note "Taurus per Parasara".'),
            cf('debilitation_sign', 'sourced_fact', 'bphs:PG574:C2 names Scorpio as the sign of debilitation (sl.40-43 as printed) - matches DB 8.'),
            cf('exaltation_degree', 'sourced_fact', 'NULL is correct: no deepest-exaltation degree is stated for the nodes (BPHS Ch.3 note says there are different views).'),
            cf('own_signs / mooltrikona_sign', 'omission_not_contradiction',
               'DB stores own_signs={} and mooltrikona_sign NULL; BPHS Ch.47 (bphs:PG574:C1) states Rahu own sign Aquarius and moolatrikona Gemini (some learned: Virgo own). The held text asserts something the DB leaves empty; not counted as contradicted because an empty value is an absence, not a stated different value.'),
            cf('natural_benefic', 'sourced_fact', 'BPHS Ch.3 sl.11: Rahu is a malefic.'),
            cf('dasha_years', 'sourced_fact', 'BPHS Ch.46 sl.15: Rahu 18 years.'),
            cf('karak_domains', 'not_a_classical_claim', KARAK_NOTE),
        ]
        row(T, key, 'Rahu: exalted Taurus (debated; Taurus per Parasara), debilitated Scorpio, malefic, Vimshottari 18 yrs.', cur,
            'sourced_fact', 'FACT', corpus, inference=None,
            proposed=cite(['bphs_rahu_ex', 'bphs_rahu_debil', 'bphs_benefic', 'bphs_vim_years']),
            action='acharya',
            q=('BPHS Ch.47 (bphs:PG574:C1) states Rahu own sign Aquarius and moolatrikona Gemini (some learned: Virgo own), and Ketu own sign Scorpio / moolatrikona Sagittarius (some: Pisces own); Hora Sara notes (hora_sara:PG19:C1) list other texts that differ. '
               'reference_planets stores own_signs={} and mooltrikona_sign=NULL for both nodes. Should the nodes carry sign-lordship per BPHS Ch.47 (and which variant), or does the platform deliberately hold the nodes without sign-lordship?'),
            cols=cols,
            notes=('existing_citation_unverifiable at chapter grain: the cited "BPHS Ch.3" does not contain the node dignities; they are in Ch.47. The row note "Rahu exaltation debated, Taurus per Parasara" is accurate: the held corpus shows BPHS=Taurus (Ch.47), Hora Sara note lists divergent views, Jataka Parijata (OCR-garbled) gives Gemini.'),
            unsourced_components=True)
        continue
    if pid == 'ketu':
        corpus = [ev('bphs_ketu_ex'), ev('bphs_nodes_exalt_views', role='note'), ev('bphs_debil7', role='analogy', support='INFERENCE', note='7th-sign rule is stated for the seven planets only'),
                  ev('hs_node_fall', role='variant', note='Hora Sara note: per Jatakalankaram/Veemesaram both nodes exalted Scorpio and fall in Taurus (cited views, not BPHS)'),
                  ev('bphs_node_mt', role='note'), ev('bphs_node_own', role='note'), ev('bphs_nodes_180'),
                  ev('bphs_benefic'), ev('bphs_vim_names'), ev('bphs_vim_years'), ev('bphs_vim_table')]
        cols = [
            cf('exaltation_sign', 'sourced_fact', 'BPHS Ch.47 (bphs:PG574:C1): "sign of exaltation of Ketu is Scorpio" - matches DB 8.'),
            cf('debilitation_sign', 'sourced_inference', 'No Ketu debilitation sign is stated in BPHS; Taurus (DB 2) follows the 7th-from-exaltation rule of sl.49-50 applied to the node, and is the fall sign cited for Ketu in the Hora Sara note (hora_sara:PG19:C1, citing other texts).'),
            cf('own_signs / mooltrikona_sign', 'omission_not_contradiction', 'BPHS Ch.47 gives Ketu own sign Scorpio and moolatrikona Sagittarius (some: Pisces own); DB holds {} / NULL. See Rahu row question.'),
            cf('natural_benefic', 'sourced_fact', 'BPHS Ch.3 sl.11: Ketu is a malefic.'),
            cf('dasha_years', 'sourced_fact', 'BPHS Ch.46 sl.15: Ketu 7 years.'),
            cf('source_citation note', 'sourced_fact', '"Ketu is South Node (180 deg opposite Rahu)": BPHS Ch.3 note states the nodes are exactly 180 degrees apart (bphs:PG24:C1).'),
            cf('karak_domains', 'not_a_classical_claim', KARAK_NOTE),
        ]
        row(T, key, 'Ketu: exalted Scorpio, debilitated Taurus, malefic, Vimshottari 7 yrs, 180 deg from Rahu.', cur,
            'sourced_inference', 'INFERENCE', corpus,
            inference='debilitation_sign=Taurus is not stated for Ketu in BPHS; it is the 7th sign from the stated exaltation (Scorpio) by the rule of sl.49-50, which is worded for the seven planets.',
            proposed=cite(['bphs_ketu_ex', 'bphs_nodes_180', 'bphs_benefic', 'bphs_vim_years']),
            action='acharya',
            q=('Is Taurus an acceptable Ketu debilitation sign for the reference table? BPHS Ch.47 states only Ketu exalted in Scorpio; the Taurus fall is attested in held sources only via the Hora Sara note citing other works (hora_sara:PG19:C1), and Jataka Parijata/Jatakachintamani variants differ. See also the sign-lordship question on the Rahu row.'),
            cols=cols,
            notes='existing_citation_unverifiable at chapter grain; node dignities are in BPHS Ch.47 (pages 573-574), not Ch.3.',
            unsourced_components=True)

# ----------------------------------------------------------------------------------------------------------
# 2. reference_signs
# ----------------------------------------------------------------------------------------------------------
T = 'reference_signs'
ELEM_STATED = {1: 'fire', 2: 'earth', 3: 'air', 4: 'water', 9: 'fire', 10: 'earth', 11: 'air', 12: 'water'}
ELEM_CYCLE = {1: 'fire', 2: 'earth', 3: 'air', 4: 'water', 5: 'fire', 6: 'earth', 7: 'air', 8: 'water', 9: 'fire',
              10: 'earth', 11: 'air', 12: 'water'}
MOD = {0: 'movable', 1: 'fixed', 2: 'dual'}
BIPED_TEXT = {1: False, 2: False, 3: True, 4: False, 5: False, 6: True, 7: True, 8: False, 9: 'mixed', 10: False,
              11: True, 12: False}
SIGN_EV = {
    1: ['bphs_aries', 'bphs_aries_fiery', 'pd_quad'],
    2: ['bphs_taurus', 'bphs_taurus_earthy', 'pd_quad'],
    3: ['bphs_gemini_airy', 'bphs_gemini_biped', 'pd_biped'],
    4: ['bphs_cancer_watery', 'bphs_cancer_feet'],
    5: ['bphs_leo_quad', 'pd_quad'],
    6: ['bphs_virgo_biped'],
    7: ['bphs_libra_biped', 'pd_biped'],
    8: ['bphs_scorpio_centi', 'bphs_scorpio_lord', 'pd_centiped'],
    9: ['bphs_sag', 'bphs_sag_fiery', 'pd_biped'],
    10: ['bphs_cap', 'bphs_cap_earthy'],
    11: ['bphs_aqu_airy', 'bphs_aqu_biped', 'pd_biped'],
    12: ['bphs_pisces', 'bphs_pisces_footless'],
}
SIGN_CITE = {
    1: ['bphs_aries', 'bphs_aries_fiery'], 2: ['bphs_taurus', 'bphs_taurus_earthy'], 3: ['bphs_gemini_airy', 'bphs_gemini_biped'],
    4: ['bphs_cancer_watery', 'bphs_cancer_feet'], 5: ['bphs_leo_quad'], 6: ['bphs_virgo_biped'], 7: ['bphs_libra_biped'],
    8: ['bphs_scorpio_centi', 'bphs_scorpio_lord'], 9: ['bphs_sag', 'bphs_sag_fiery'], 10: ['bphs_cap', 'bphs_cap_earthy'],
    11: ['bphs_aqu_airy', 'bphs_aqu_biped'], 12: ['bphs_pisces', 'bphs_pisces_footless'],
}
for r in load(T):
    n = r['sign_id']
    cur = r['source_citation']
    key = {'sign_id': n}
    assert r['lord'] == LORDS[n], n
    assert r['modality'] == MOD[(n - 1) % 3], n
    assert r['is_odd'] == (n % 2 == 1), n
    assert r['natural_house'] == n, n
    assert r['element'] == ELEM_CYCLE[n], n
    corpus = [ev('pd_lords_signs'), ev('bphs_modality'), ev('bphs_modality_note'), ev('pd_modality'), ev('pd_odd_male')]
    corpus += [ev(k) for k in SIGN_EV[n]]
    corpus.append(ev('bphs_limbs', support='INFERENCE', note='Kalapurusha limbs counted with Aries as 1st: supports natural_house = sign number by inference'))
    cols = [
        cf('lord', 'sourced_fact', 'Phaladipika Adh.I sl.6 lists the sign lords from Mesha onward; %s = %s (matches DB).' % (SIGN_NAME[n], LORDS[n].title()) + (
            ' BPHS Ch.4 sl.15-16 (bphs:PG51:C1) has the lord of Scorpio as "Man" - OCR for Mars - so the Phaladipika line is the clean support.' if n == 8 else '')),
        cf('modality', 'sourced_fact', 'BPHS Ch.4 sl.5-6: Movable, Fixed, Dual are the names given to the 12 signs in order (and note lists the signs); Phaladipika sl.9 repeats Chara/Sthira/Ubhaya.'),
        cf('is_odd', 'sourced_fact', 'BPHS sl.5-6 (male and female successively) and Phaladipika sl.9 ("odd and even ... male and female"): odd signs are male; DB is_odd=%s.' % r['is_odd']),
        cf('natural_house', 'sourced_inference', 'Equating sign n with natural house n rests on the Kalapurusha limb sequence counted from Aries as lagna (BPHS Ch.4 sl.4-4.5 note, Phaladipika sl.4).'),
    ]
    # element
    if n in ELEM_STATED:
        cols.append(cf('element', 'sourced_fact', 'BPHS Ch.4 describes %s as %s.' % (SIGN_NAME[n], ELEM_STATED[n])))
    else:
        cols.append(cf('element', 'sourced_inference', 'Element for %s is not stated in BPHS Ch.4 sl.6-24 or Phaladipika Adh.I; DB value %s completes the fire/earth/air/water cycle exactly confirmed by the 8 signs whose element IS stated (Aries, Taurus, Gemini, Cancer, Sagittarius, Capricorn, Aquarius, Pisces).' % (SIGN_NAME[n], r['element'])))
    # biped
    bt = BIPED_TEXT[n]
    if bt == 'mixed':
        cols.append(cf('is_biped', 'sourced_inference', 'Held texts say Sagittarius is biped in the first half and quadruped in the second half (BPHS Ch.4 sl.17-18; Phaladipika). DB boolean false is only half right; a per-half attribute cannot be expressed.'))
    elif bt == r['is_biped']:
        cols.append(cf('is_biped', 'sourced_fact', 'Text: %s is %s; DB is_biped=%s agrees.' % (SIGN_NAME[n], {1: 'quadruped', 2: 'quadruped', 3: 'biped', 4: 'many-footed (not biped)', 5: 'quadruped', 6: 'biped', 7: 'biped', 8: 'centipede (not biped)', 10: 'first half quadruped, second half footless (not biped)', 11: 'biped', 12: 'footless (not biped)'}[n], r['is_biped'])))
    else:
        cols.append(cf('is_biped', 'contradicted', 'DB is_biped=%s but BPHS Ch.4 sl.6-7 states "It is a quadruped sign" for Aries (bphs:PG49:C1) and Phaladipika Adh.I lists Mesha among the quadruped signs (phaladeepika:PG41:C1).' % r['is_biped']))
    body = {1: 'head', 2: 'face', 3: 'arms (BPHS) / breast (Phaladipika)', 4: 'heart (both)', 5: 'stomach/belly', 6: 'hip', 7: 'space below navel / groins', 8: 'privities', 9: 'thighs', 10: 'knees', 11: 'ankles (BPHS) / calves (Phaladipika)', 12: 'feet'}[n]
    sigstate = 'sourced_inference'
    signote = 'Body part per held texts: %s; DB significations is a platform tag list whose last element is the body part (%s).' % (body, r['significations'][-1])
    if n == 2:
        sigstate = 'omission_not_contradiction'
        signote = 'DB lists "throat"; BPHS Ch.4 and Phaladipika sl.4 give the 2nd sign\'s limb as "face" (not throat). Variance, not a clear contradiction of a stored classical value (significations is a tag list).'
    if n == 4:
        signote = 'DB lists "chest"; Phaladipika sl.4 gives "breast" to the 3rd sign and "heart" to the 4th; BPHS gives "heart" to the 4th. "chest" is a near-synonym of the held "heart/breast".'
    cols.append(cf('significations', sigstate, signote + ' Other tags (e.g. courage, wealth) are platform vocabulary.'))
    cited = cite(SIGN_CITE[n] + ['pd_lords_signs', 'bphs_modality'])
    state = 'sourced_fact'
    support = 'FACT'
    infer = None
    action = 'recite'
    q = None
    if n == 1:
        state, support, action = 'contradicted', 'CONTRADICTS', 'acharya'
        q = ('reference_signs stores Aries (Mesha) with is_biped=true. BPHS Ch.4 sl.6-7 (bphs:PG49:C1) says "It is a quadruped sign" and Phaladipika Adh.I (phaladeepika:PG41:C1) lists Mesha as quadruped. '
             'Should Aries is_biped be false? (And is is_biped intended to mean "human/biped sign" as opposed to quadruped/centipede/footless?)')
    elif n == 9:
        state, support, action = 'sourced_inference', 'INFERENCE', 'acharya'
        infer = 'is_biped=false for Sagittarius is a simplification: the held texts make the first half biped and the second half quadruped, so a single boolean cannot be verified as stated.'
        q = ('Sagittarius is stored is_biped=false, but BPHS Ch.4 sl.17-18 and Phaladipika Adh.I make the first half biped (human) and the second half quadruped. Should the boolean be NULL/mixed, or split by half?')
    elif n in (5, 6, 7, 8):
        state, support = 'sourced_inference', 'INFERENCE'
        infer = 'element (%s) is not stated for %s in the held texts; it is inferred from the 4-element cycle confirmed by the 8 signs where it is stated.' % (r['element'], SIGN_NAME[n])
    if n == 2:
        q = ('reference_signs.significations for Taurus lists "throat"; BPHS Ch.4 and Phaladipika sl.4 name the 2nd sign\'s limb as "face". Keep "throat" (later Kalapurusha tradition: face and neck) or follow the held text?')
        action = 'recite'
    row(T, key, '%s: lord %s, %s, %s, %s sign, %s, natural house %d.' % (SIGN_NAME[n], LORDS[n].title(), r['element'], r['modality'],
                                                                      'odd/male' if r['is_odd'] else 'even/female', 'biped' if r['is_biped'] else 'not biped', n),
        cur, state, support, corpus, inference=infer, proposed=cited, action=action, q=q, cols=cols,
        notes=('existing_citation_unverifiable at chapter grain: "BPHS Ch.6 (Rasi-svarupa-adhyaya)" - in the held Santhanam edition Ch.6 is "The Sixteen Divisions Of A Sign" (bphs:PG66:C1); the sign descriptions are Ch.4 "Zodiacal signs Described" (printed at bphs:PG47:C1). The sign lords are also in Phaladipika Adh.I sl.6.'),
        unsourced_components=(n in (2, 5, 6, 7, 8, 9)))

# ----------------------------------------------------------------------------------------------------------
# 3. reference_houses
# ----------------------------------------------------------------------------------------------------------
T = 'reference_houses'
KEND = {1, 4, 7, 10}; PANA = {2, 5, 8, 11}; APOK = {3, 6, 9, 12}; KONA = {5, 9}; DUST = {6, 8, 12}; UPA = {3, 6, 10, 11}
MARAKA = {2, 7}
KARAKA_PD = {1: ['sun'], 2: ['jupiter'], 3: ['mars'], 4: ['moon', 'mercury'], 5: ['jupiter'], 6: ['saturn', 'mars'],
             7: ['venus'], 8: ['saturn'], 9: ['sun', 'jupiter'], 10: ['jupiter', 'sun', 'mercury', 'saturn'],
             11: ['jupiter'], 12: ['saturn']}
BHAVA_NAMES = {1: 'Thanu', 2: 'Dhana', 3: 'Sahaja', 4: 'Bandhu', 5: 'Putra', 6: 'Ari', 7: 'Yuvati', 8: 'Randhra',
               9: 'Dharma', 10: 'Karma', 11: 'Labha', 12: 'Vyaya'}
SIG_SUP = {
    1: (['body', 'head'], ['self', 'appearance'], ['health', 'vitality', 'temperament', 'fame']),
    2: (['wealth', 'family', 'speech', 'food', 'face'], ['early_education', 'accumulated_assets'], []),
    3: (['younger_siblings', 'courage', 'valour'], [], ['communication', 'short_journeys', 'arms', 'effort', 'skills']),
    4: (['mother', 'home', 'vehicles', 'land'], ['property', 'emotional_happiness'], ['education', 'heart']),
    5: (['children', 'intelligence'], [], ['purva_punya', 'mantra', 'romance', 'speculation', 'creativity']),
    6: (['enemies', 'disease', 'debts'], [], ['obstacles', 'service', 'litigation', 'maternal_relatives (Phaladipika Jnati = PATERNAL relation)']),
    7: (['spouse', 'passion'], ['marriage'], ['business_partnership', 'trade', 'foreign_travel', 'public_dealings']),
    8: (['longevity', 'death'], [], ['inheritance', 'occult', 'sudden_events', 'chronic_illness', 'spouse_wealth', 'research']),
    9: (['father', 'guru', 'dharma', 'fortune'], [], ['higher_learning', 'pilgrimage', 'long_journeys', 'prosperity']),
    10: (['career', 'profession', 'status', 'fame'], ['authority'], ['government', 'father_alt', 'public_action']),
    11: (['gains', 'income', 'elder_siblings'], ['fulfilment_of_desires'], ['friends', 'aspirations', 'recovery']),
    12: (['losses', 'expenditure', 'feet'], ['bed_pleasures', 'sleep', 'isolation'], ['moksha', 'foreign_lands', 'hospitals']),
}
for r in load(T):
    n = r['house_num']
    cur = r['source_citation']
    key = {'house_num': n}
    cat = r['category']
    doc = r['classical_doctrine_jsonb']
    classes = doc.get('classes', [])
    # verify categories & classes against the text sets
    sets = {'kendra': KEND, 'panapara': PANA, 'apoklima': APOK, 'trikona': KONA, 'dusthana': DUST, 'upachaya': UPA, 'maraka': MARAKA, 'trika': DUST}
    cls_notes = []
    for c in classes:
        mem = sets[c]
        if n in mem:
            cls_notes.append(c + ': in held text')
        elif c == 'trikona' and n == 1:
            cls_notes.append('trikona: only by translator notes (UK: "Lagna is both a kona and a kendra"; Hora Sara note: some count Lagna as a trine); BPHS/PD define trikona = 5th, 9th')
        else:
            cls_notes.append(c + ': NOT supported')
    assert all('NOT' not in x for x in cls_notes), (n, cls_notes)
    assert n in sets[cat], (n, cat)
    corpus = [ev('bphs_classes'), ev('bphs_panaphara'), ev('bphs_kona'), ev('bphs_trika'), ev('bphs_upachaya'),
              ev('pd_house_kendra'), ev('pd_house_panaphara'), ev('pd_house_apoklima'), ev('pd_house_dusthana'),
              ev('pd_house_upachaya'), ev('pd_house_trikona'), ev('bphs_bhava_names'), ev('bphs_bhava_ind'),
              ev('pd_house_names1', support='FACT', note='Phaladipika sl.10-16 lists the designations of each house (Vitta/Vidya/... for the 2nd, etc.)'),
              ev('pd_karakas')]
    if 'maraka' in classes:
        corpus.append(ev('bphs_maraka'))
    if n == 1:
        corpus += [ev('uk_lagna_kona', role='note', support='FACT', note='Uttara Kalamrita translator note'), ev('hs_lagna_trine', role='note', note='Hora Sara translator note')]
        corpus += [ev('pd_lagna_strength', role='context', note='Phaladipika Adh.IV sl.6: the strength of the Lagna equals that of its lord - NOT the claimed "lagnesha is the most important graha"'),
                   ev('pd_adh4_s2', role='context', note='Phaladipika Adh.IV sl.2 (the doctrine tag "Ch.4 v.2") concerns Cheshta/Uchcha/Dig bala, not lagna-lord importance')]
    sup, inf, uns = SIG_SUP[n]
    kar_db = r['karakas']
    kar_extra = [k for k in kar_db if k not in KARAKA_PD[n]]
    kar_missing = [k for k in KARAKA_PD[n] if k not in kar_db]
    assert not kar_missing, (n, kar_missing)
    cols = [
        cf('category / classes', 'sourced_fact', 'BPHS Ch.7 sl.33-36 and Phaladipika Adh.I sl.17-18: ' + '; '.join(cls_notes) + ('; category "%s" membership verified.' % cat)),
        cf('name_sa / name_en', 'sourced_fact' if n != 4 else 'sourced_fact',
           'BPHS Ch.7 sl.37-38 names: %s (DB name_sa "%s")%s.' % (BHAVA_NAMES[n], r['name_sa'], '; Phaladipika sl.11-12 also names the 4th "Sukha" (happiness) so DB Sukha is attested' if n == 4 else '')),
        cf('karakas', 'sourced_fact' if not kar_extra else 'sourced_fact_with_superset',
           'Phaladipika Adh.XV sl.17 (and Jataka Parijata sl.51) list karakas %s; DB %s%s.' % (KARAKA_PD[n], kar_db, ('; extra in DB not in held list: %s' % kar_extra) if kar_extra else ' - identical')),
        cf('natural_significations', 'partially_sourced',
           'Named in Phaladipika Adh.I sl.10-16 / BPHS Ch.7 sl.37-38: %s; reasonable readings of held designations (inference): %s; not found in held designations (platform vocabulary / later tradition): %s.' % (sup, inf, uns)),
    ]
    doc_unsourced = []
    for k, v in doc.items():
        if k in ('classes', 'maraka', 'trika', 'upachaya'):
            continue
        doc_unsourced.append('%s=%r' % (k, v))
    cols.append(cf('classical_doctrine_jsonb free-text (note/lordship/phaladeepika)', 'unsourced_marked',
                   'Superlative/qualitative doctrine strings are not stated in the held corpus in these words: ' + '; '.join(doc_unsourced) + ('. The tag phaladeepika="Ch.4 v.2" does not resolve: Phaladipika Adh.IV sl.2 concerns planetary bala (phaladeepika:PG71:C1); house definitions are Adh.I sl.10-18 and karakas Adh.XV sl.17.' if n == 1 else '.')))
    q = None
    action = 'recite'
    if kar_extra:
        q = ('reference_houses.karakas for house %d lists %s in addition to the Phaladipika Adh.XV sl.17 / Jataka Parijata sl.51 karakas %s. Which classical text (if any) supports the extra karaka(s) %s, or should they be marked as platform-added?' % (n, kar_db, KARAKA_PD[n], kar_extra))
        action = 'acharya'
    if n == 1:
        q = (q + ' ' if q else '') + ('House 1 doctrine says "lagnesha is the most important graha" and tags it "phaladeepika Ch.4 v.2": no held chunk states this (Phaladipika Adh.IV sl.2 is about Cheshta/Uchcha/Dig bala; sl.6 says the Lagna strength equals its lord\'s). Is there a classical source, or should the string be marked unsourced?')
        action = 'acharya'
    state = 'sourced_fact'
    support = 'FACT'
    row(T, key, 'House %d (%s): %s house, classes %s, karakas %s, significations per platform tag list.' % (n, BHAVA_NAMES[n], cat, classes, kar_db),
        cur, state, support, corpus, inference=None,
        proposed=cite(['bphs_classes', 'bphs_bhava_names', {'kendra': 'pd_house_kendra', 'panapara': 'pd_house_panaphara', 'apoklima': 'pd_house_apoklima', 'trikona': 'pd_house_trikona', 'dusthana': 'pd_house_dusthana'}[cat], 'pd_karakas'] + (['bphs_maraka'] if 'maraka' in classes else [])),
        action=action, q=q, cols=cols,
        notes='existing citation "BPHS Ch.7; Phaladeepika Ch.4": BPHS Ch.7 resolves (printed "Chapter 7" at bphs:PG100/PG102; kendra/panapara/apoklima/kona/trika/chaturasra/upachaya at sl.33-36 and bhava names at sl.37-38 on bphs:PG101:C1). "Phaladeepika Ch.4" does NOT resolve: Adh.IV is planetary strength; the house definitions are Adh.I sl.10-18 (phaladeepika:PG43-46) and karakas Adh.XV sl.17 (phaladeepika:PG196:C1). Maraka (2nd/7th) is BPHS Ch.44 (bphs:PG440:C1).',
        unsourced_components=True)

# ----------------------------------------------------------------------------------------------------------
# 4. reference_aspects
# ----------------------------------------------------------------------------------------------------------
T = 'reference_aspects'
for r in load(T):
    p = r['planet_id']
    h = r['aspect_house']
    cur = r['source_citation']
    key = {'planet_id': p, 'aspect_house': h}
    special = {'saturn': {3, 10}, 'jupiter': {5, 9}, 'mars': {4, 8}}
    claim = '%s aspects house %d (%s, strength %s, special=%s).' % (p.title(), h, r['aspect_strength'], r['strength_value'], r['is_special'])
    if h == 7 and p in ('sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn'):
        row(T, key, claim, cur, 'sourced_fact', 'FACT', [ev('bphs_asp_7'), ev('uk_asp'), ev('b_drishti_ch26', role='context')],
            proposed=cite(['bphs_asp_7']), action='recite',
            notes='existing_citation_unverifiable at chapter grain but "BPHS Ch.26" RESOLVES: printed "Chapter 26 Evaluation of Planetary Aspects" at bphs:PG253:C1; the 7th-house full aspect is at bphs:PG254:C1 (sloka 2-5 as printed, OCR "2\'5").')
    elif h == 7:  # rahu / ketu
        row(T, key, claim, cur, 'sourced_inference', 'INFERENCE', [ev('bphs_asp_7'), ev('bphs_nodes_shadowy', support='FACT', role='context'), ev('uk_rahu_asp', support='FACT', role='supports') if p == 'rahu' else ev('bphs_asp_7', role='context')],
            inference='BPHS says "All planets aspect the 7th fully"; the nodes are treated as planets for astrological delineation (BPHS Ch.3 note) but the aspect sentence is not worded for them specifically' + ('. For Rahu, the Uttara Kalamrita note (attributing to Parasara) lists the 7th among his full aspects.' if p == 'rahu' else '. No held chunk states Ketu\'s 7th aspect explicitly.'),
            proposed=cite(['bphs_asp_7'] + (['uk_rahu_asp'] if p == 'rahu' else [])), action='recite',
            notes='7th-house aspect for a node follows the general rule; see the 5th/9th rows for the "later tradition" caveat.')
    elif p in special and h in special[p]:
        k = {'saturn': 'uk_asp_sat', 'jupiter': 'uk_asp_jup', 'mars': 'uk_asp_mars'}[p]
        row(T, key, claim, cur, 'sourced_fact', 'FACT', [ev('bphs_asp_special'), ev(k), ev('bphs_asp_slabs', role='context')],
            proposed=cite(['bphs_asp_special']), action='recite',
            notes='BPHS Ch.26 (printed at bphs:PG253:C1) sl.2-5: Saturn 3rd & 10th, Jupiter 5th & 9th, Mars 4th & 8th special aspects; the full-strength value 1.00 is the "special aspect" reading (other planets give 1/4, 1/2, 3/4 on those houses).')
    elif p == 'rahu' and h in (5, 9):
        row(T, key, claim, cur, 'sourced_fact', 'FACT', [ev('uk_rahu_asp'), ev('bphs_rahu_has_asp', role='context', support='FACT', note='BPHS translator note only affirms that Rahu has aspects, without houses')],
            proposed=cite(['uk_rahu_asp']), action='acharya',
            q='The held Uttara Kalamrita note (uttara_kalamrita:PG41:C1) attributes to Parasara: Rahu aspects the 5th, 7th, 9th and 12th fully, 2nd and 10th by half, 3rd and 6th by a quarter. reference_aspects holds Rahu 5/7/9 as full with the note "per later tradition" and has no 12th-house row. (a) Should the 12th full aspect be added for Rahu? (b) May the note "per later tradition" be replaced by "per Parasara as cited in Uttara Kalamrita (translator\'s note)"?',
            notes='existing citation "BPHS Ch.26" does NOT itself state node aspects (Ch.26 sl.2-5 names only the seven planets; the translator note at bphs:PG110:C1 only says "Rahu has aspects"). The 5/9 values are supported by a translator\'s note in a DIFFERENT held text (Uttara Kalamrita), which attributes them to Parasara - contrary to the row note "per later tradition". Support is FACT at the level of that chunk, not BPHS.')
    else:  # ketu 5, 9
        row(T, key, claim, cur, 'unsourced_marked', 'NONE', [ev('bphs_rahu_has_asp', role='context', support='NONE', note='only for Rahu, no houses'), ev('uk_rahu_asp', role='context', support='NONE', note='speaks of Rahu only; says nothing of Ketu')],
            proposed=None, action='mark_unsourced',
            q='No held text states Ketu\'s 5th/9th aspects (the Uttara Kalamrita Parasara-attributed note and the BPHS translator note speak of Rahu only). Is there a classical source for Ketu\'s 5th and 9th aspects, or should these two rows stay marked "unsourced (later tradition)"?',
            notes='The existing note "Rahu/Ketu aspects per later tradition" is honest; the chapter-only citation BPHS Ch.26 does not support Ketu.')

# ----------------------------------------------------------------------------------------------------------
# 5. reference_vargas
# ----------------------------------------------------------------------------------------------------------
T = 'reference_vargas'
NAMEKEY = {'D1': 'bphs_16', 'D2': 'bphs_16', 'D3': 'bphs_16', 'D4': 'bphs_16', 'D7': 'bphs_16', 'D9': 'bphs_16', 'D10': 'bphs_16',
           'D12': 'bphs_16', 'D16': 'bphs_16', 'D20': 'bphs_16', 'D24': 'bphs_16b', 'D27': 'bphs_16b', 'D30': 'bphs_16b',
           'D40': 'bphs_16b', 'D45': 'bphs_16b', 'D60': 'bphs_16b'}
USEKEY = {'D1': ['bphs_vuse0'], 'D2': ['bphs_vuse_hora'], 'D3': ['bphs_vuse0'], 'D4': ['bphs_vuse1'], 'D7': ['bphs_vuse1'],
          'D9': ['bphs_vuse1'], 'D10': ['bphs_vuse1b', 'bphs_vnote'], 'D12': ['bphs_vuse1b'], 'D16': ['bphs_vuse_conv'],
          'D20': ['bphs_vuse_conv'], 'D24': ['bphs_vuse2'], 'D27': ['bphs_vuse2', 'bphs_bhamsa'], 'D30': ['bphs_vuse2'],
          'D40': ['bphs_vuse3'], 'D45': ['bphs_vuse3'], 'D60': ['bphs_vuse3']}
SIGSTATE = {
    'D1': ('physique from the ascendant (Ch.7 sl.1-8)', 'platform extension "all life matters"'),
    'D2': ('wealth from Hora', 'secondary "Lakshmi + Surya horas": BPHS sl.5-6 gives the Sun and Moon horas; "Lakshmi" is not in the held text'),
    'D3': ('happiness through co-born from Drekkana', '"courage; communication" are platform extensions'),
    'D4': ('fortunes from Chaturthamsa', '"property; fixed assets; home" not stated in the held passage'),
    'D7': ('sons and grandsons from Saptamamsa', None),
    'D9': ('spouse from Navamsa', '"dharma; spiritual development; inner nature; most important divisional" not stated here'),
    'D10': ('power and position from Dasamsa (translator: livelihood)', None),
    'D12': ('parents from Dvadasamsa', None),
    'D16': ('conveyances from Shodasamsa (translator: and related happiness)', None),
    'D20': ('worship, spiritual progress, religious activities from Vimsamsa', None),
    'D24': ('learning / academic achievements from Chaturvimsamsa', None),
    'D27': ('strength and weakness from Bhamsa (Nakshatramsa / Saptavimsamsa)', None),
    'D30': ('evil effects from Trimsamsa', '"health issues" an extension'),
    'D40': ('auspicious and inauspicious effects from Khavedamsa', '"Maternal ancestry" NOT stated in the held text'),
    'D45': ('all indications from Akshavedamsa', '"Paternal ancestry" NOT stated in the held text'),
    'D60': ('all indications from Shashtiamsa', '"Past-life karma; most subtle influences" NOT stated in the held text'),
}
for r in load(T):
    v = r['varga_id']
    cur = r['source_citation']
    key = {'varga_id': v}
    assert r['varga_number'] == r['division_count'] == int(v[1:])
    if v in NAMEKEY:
        corpus = [ev(NAMEKEY[v])]
        if v == 'D4':
            pass
        corpus += [ev(k) for k in USEKEY[v]]
        s1, extra = SIGSTATE[v]
        cols = [
            cf('varga_id / canonical_name_en / division_count', 'sourced_fact', 'BPHS Ch.6 sl.2-4 names the 16 vargas incl. this one (division count follows the name: %s = 1/%d of a sign).' % (r['canonical_name_en'], r['division_count'])),
            cf('primary_signification', 'sourced_fact' if not extra else 'partially_sourced',
               'Held (BPHS Ch.7 sl.1-8, bphs:PG90-91): %s.%s DB: "%s".' % (s1, (' Not in held text: ' + extra + '.') if extra else '', r['primary_signification'])),
        ]
        if v == 'D27':
            cols.append(cf('canonical_name_en', 'sourced_fact', 'BPHS heading "BHAMSA (NAKSHATRAMSA OR SAPTAVIMSAMSA)" (bphs:PG77:C1) supports the alias Nakshatramsha.'))
        partial = bool(extra)
        q = None
        action = 'recite'
        if v in ('D40', 'D45', 'D60'):
            q = 'DB gives %s the signification "%s". BPHS Ch.7 sl.1-8 says only "%s". Which classical source supports the ancestral/karmic signification, or should that part be marked as later-tradition?' % (v, r['primary_signification'], s1)
            action = 'acharya'
        row(T, key, '%s %s: 1/%d of a sign; %s.' % (v, r['canonical_name_en'], r['division_count'], r['primary_signification']), cur,
            'sourced_fact', 'FACT', corpus, proposed=cite([NAMEKEY[v]] + USEKEY[v]), action=action, q=q, cols=cols,
            notes='existing_citation_unverifiable at chapter grain: "BPHS Ch.6 (Shodasha-varga-adhyaya)" resolves for the NAME list (printed "Chapter 6 The Sixteen Divisions Of A Sign", bphs:PG66:C1/PG67:C1); the SIGNIFICATIONS are in Ch.7 sl.1-8 (printed "Chapter 7 Divisional Consideration", bphs:PG90:C1; list continues bphs:PG91:C1).',
            unsourced_components=partial)
    elif v == 'D5':
        row(T, key, 'D5 Panchamsha: 1/5 of a sign; spiritual merit, past-life credit, children.', cur, 'sourced_inference', 'INFERENCE',
            [ev('bphs_16', role='context', support='NONE', note='the BPHS Ch.6 list of 16 vargas does NOT include a Panchamsa (D5)'),
             ev('sar_panchamsa', support='FACT', note='Saravali names a Panchamsa'), ev('sar_panchamsa_note', support='FACT')],
            inference='The name Panchamsa and a 5-fold, 6-degree division appear in the held Saravali (sloka 63 and note), which supports the name/count but is not the cited BPHS Ch.6 and is described there as "a little different from Trimsamsa"; the stored signification is not stated.',
            proposed=cite(['sar_panchamsa', 'sar_panchamsa_note']), action='acharya',
            q='BPHS Ch.6 sl.2-4 names 16 vargas and does not include D5 (Panchamsha), D6 (Shashthamsha) or D8 (Ashtamsha). Saravali sl.63 (saravali:PG136:C2) mentions a Panchamsa but treats it as a Trimsamsa-like 6-degree division. Should D5/D6/D8 stay in reference_vargas with a non-BPHS source, or be marked as unsourced later-tradition vargas?',
            cols=[cf('division_count', 'sourced_inference', 'Saravali Panchamsa = 6 degrees = 1/5 of a sign.'), cf('primary_signification', 'unsourced_marked', 'Not stated in any held chunk.')],
            notes='The existing citation "BPHS Ch.6 (Shodasha-varga-adhyaya)" is mis-scoped for D5: the held BPHS Ch.6 list has 16 divisions and omits D5.', unsourced_components=True)
    else:  # D6, D8
        row(T, key, '%s %s: 1/%d of a sign; %s.' % (v, r['canonical_name_en'], r['division_count'], r['primary_signification']), cur,
            'unsourced_marked', 'NONE', [ev('bphs_16', role='context', support='NONE', note='the BPHS Ch.6 list of 16 vargas does NOT include this division')],
            proposed=None, action='mark_unsourced',
            q='BPHS Ch.6 sl.2-4 names 16 vargas and does not include D5, D6 (Shashthamsha) or D8 (Ashtamsha); no other held text names %s. Should this varga stay in reference_vargas, and with what source (or marked later-tradition/unsourced)?' % r['canonical_name_en'],
            cols=[cf('all classical columns', 'unsourced_marked', 'No held chunk names or defines this division or its signification.')],
            notes='The citation "BPHS Ch.6 (Shodasha-varga-adhyaya)" does not support this row: the 16 vargas of Ch.6 exclude it. Searched all 8 held English texts for Shashthamsa/Ashtamsa/Panchamsa variants.', unsourced_components=True)

# ----------------------------------------------------------------------------------------------------------
# 6. reference_upagrahas
# ----------------------------------------------------------------------------------------------------------
T = 'reference_upagrahas'
UP = {
    'dhuma': ('bphs_dhuma', 'bphs_dhuma_inausp', 'Sun + 133deg20\''),
    'vyatipata': ('bphs_vyati', 'bphs_vyati_inausp', '360 - Dhuma'),
    'parivesha': ('bphs_pariv', 'bphs_pariv_extreme', 'Vyatipata + 180'),
    'indrachapa': ('bphs_chapa', 'bphs_chapa_inausp', '360 - Parivesha'),
    'upaketu': ('bphs_upaketu', 'bphs_upa_malefic', 'Indrachapa + 16deg40\''),
}
KV_SON = {'gulika': 'bphs_gulika_son', 'yamaghantaka': 'bphs_yama_son', 'ardhaprahara': 'bphs_ardha_son', 'mrityu': 'bphs_mrityu_son', 'kala': 'bphs_kala_son'}
for r in load(T):
    u = r['upagraha_id']
    cur = r['source_citation']
    key = {'upagraha_id': u}
    nat = r['significations']['nature']
    if u in UP:
        fk, nk, form = UP[u]
        corpus = [ev(fk), ev('bphs_upa_malefic', support='FACT'), ev(nk)]
        cols = [
            cf('computation_method', 'sourced_fact', 'BPHS Ch.3 sl.61-64 (printed "6r-64", bphs:PG42:C1): %s - matches DB "%s". (Notes give the same as +133deg20\', +53deg20\', +180, -53deg20\', +16deg40\'.)' % (form, r['computation_method'])),
            cf('parent_planet', 'sourced_inference', 'DB parent "sun": the five are derived by adding fixed arcs to the Sun\'s longitude (chain starting from the Sun); the text names no "parent" explicitly.'),
        ]
        state, support, action, q = 'sourced_fact', 'FACT', 'recite', None
        if u == 'indrachapa':
            cols.append(cf('significations.nature', 'contradicted', 'DB: "%s". BPHS sl.64: Chapa (Indra Dhanus) "who is also inauspicious", and the five are "malefics by nature and cause affliction" (bphs:PG42:C1).' % nat))
            state, support, action = 'contradicted', 'CONTRADICTS', 'acharya'
            q = 'reference_upagrahas.significations.nature for Indrachapa reads "mixed; sudden brilliance then fade". BPHS Ch.3 sl.61-64 (bphs:PG42:C1) calls Indra Chapa "also inauspicious" and all five (Dhuma, Vyatipata, Parivesha, Chapa, Upaketu) "malefics by nature". Should the nature be recorded as malefic?'
        else:
            cols.append(cf('significations.nature', 'sourced_fact_for_polarity', 'DB nature starts "%s": polarity (malefic) agrees with sl.64; the descriptive tail (smoke/obstacles/calamity, etc.) is platform vocabulary, not stated.' % nat))
        row(T, key, '%s: %s; DB nature "%s".' % (r['name_en'], r['computation_method'], nat.split(';')[0]), cur, state, support, corpus,
            proposed=cite([fk, 'bphs_upa_malefic']), action=action, q=q, cols=cols,
            notes='existing citation "BPHS Ch.3": resolves (sl.61-64, bphs:PG42:C1; effects sl.65 at PG43:C1).', unsourced_components=True)
    elif u == 'maandi':
        row(T, key, 'Maandi: Saturn-based; Gulika variant, computed at beginning of Saturn\'s muhurta-portion.', cur, 'sourced_fact', 'FACT',
            [ev('bphs_mandi'), ev('bphs_gulika_beg'), ev('bphs_gulika_pos'), ev('bphs_gulika_son')],
            proposed=cite(['bphs_mandi', 'bphs_gulika_pos']), action='recite',
            cols=[cf('computation_method', 'sourced_fact', 'BPHS note: Gulika and Mandi are one and the same (bphs:PG44:C1); Gulika longitude = degree rising at the start of Gulika/Saturn\'s portion (sl.70, bphs:PG45:C1; Ch.4 note bphs:PG60:C1 confirms "beginning of Saturn\'s Muhurta").'),
                  cf('significations.nature', 'unsourced_marked', 'DB "malefic shadow of Saturn; often equated with Gulika" - the "malefic" polarity of the Kala-vela group is not stated in the held chunks (Gulika house-effects in Ch.25 are mixed); "equated" understates the text, which says identical.')],
            notes='existing citation "BPHS Ch.3; Ch.5": Ch.3 resolves; "Ch.5" in the held edition is the chapter on special lagnas (printed "Chapter 5" at bphs:PG64:C1) and has no Gulika/Mandi text; the Gulika computation is in Ch.3 (sl.67-70) and the Ch.4 notes (bphs:PG54-60).', unsourced_components=True)
    elif u == 'gulika':
        row(T, key, 'Gulika: Saturn-based; rising degree at the start of Saturn\'s portion of the day/night (8-fold division).', cur, 'sourced_fact', 'FACT',
            [ev('bphs_kv5'), ev('bphs_kv_div'), ev('bphs_gulika_pos'), ev('bphs_gulika_son'), ev('bphs_gulika_beg')],
            proposed=cite(['bphs_kv5', 'bphs_kv_div', 'bphs_gulika_pos']), action='recite',
            cols=[cf('computation_method', 'sourced_fact', 'sl.70 (bphs:PG45:C1): the degree ascending at the start of Gulika\'s portion is Gulika\'s longitude; the day/night duration is divided into eight parts, first to the weekday lord, the eighth unlorded (note, bphs:PG44:C1).'),
                  cf('parent_planet', 'sourced_fact', 'Note: "Gulika, son of Saturn".'),
                  cf('significations.nature', 'unsourced_marked', 'DB "strong malefic; poison-point; marks affliction": BPHS Ch.25 sl.62-73 gives mixed house-wise effects (adverse in most houses, favourable in 6th/10th/11th); "poison-point" is not stated.')],
            notes='existing citation "BPHS Ch.3; Ch.5": Ch.3 resolves; "Ch.5" does not (see Maandi row).', unsourced_components=True)
    else:  # ardhaprahara, yamaghantaka, mrityu, kala
        row(T, key, '%s: %s-based kaala-vela; rising degree at that planet\'s portion of the day.' % (r['name_en'], r['parent_planet'].title()), cur,
            'sourced_inference', 'INFERENCE', [ev('bphs_kv5'), ev('bphs_kv_div'), ev(KV_SON[u]), ev('bphs_gulika_pos', support='INFERENCE', role='analogy', note='the explicit longitude rule is given for Gulika only')],
            inference='The sloka that assigns the eight day-portions to the planets is OCR-damaged in the held chunk (bphs:PG44:C1). The note names the five Kala Velas and the eight-part scheme and sl.70 gives the rule explicitly for Gulika; applying "rising degree at the start of that planet\'s portion" to %s is by analogy. The parentage (%s) is stated.' % (r['name_en'], r['parent_planet']),
            proposed=cite(['bphs_kv5', KV_SON[u]]), action='recite',
            cols=[cf('computation_method', 'sourced_inference', 'analogy from the Gulika rule; the "start of portion" detail is explicit only for Gulika.'),
                  cf('parent_planet', 'sourced_fact', 'bphs:PG45:C1 note names the parent.'),
                  cf('significations.nature', 'unsourced_marked', 'DB nature "%s" is not stated in the held text for this kala-vela.' % nat)],
            notes='existing citation "BPHS Ch.3; Ch.5": Ch.3 resolves partially; "Ch.5" does not (see Maandi row).', unsourced_components=True)

# ----------------------------------------------------------------------------------------------------------
# 7. reference_strength_systems
# ----------------------------------------------------------------------------------------------------------
T = 'reference_strength_systems'
S = {}
for r in load(T):
    S[r['strength_id']] = r


def srow(sid, claim, state, support, corpus, cur_note, proposed_keys, action='recite', q=None, cols=None, inference=None, notes=None, uns=False):
    r = S[sid]
    row(T, {'strength_id': sid}, claim, r['source_citation'], state, support, corpus, inference=inference,
        proposed=cite(proposed_keys) if proposed_keys else None, action=action, q=q, cols=cols,
        notes=(notes or '') + (' ' if notes else '') + cur_note, unsourced_components=uns)


CH27 = 'existing_citation_unverifiable at chapter grain, but "BPHS Ch.27" resolves: printed "Chapter 27 Evaluation Of Strengths" at bphs:PG262:C1; sloka located by text search.'

srow('abdadhipa_bala', 'Year-lord strength: 15 virupas to the lord of the year of birth.', 'sourced_fact', 'FACT', [ev('b_vmdh')], CH27, ['b_vmdh'])
srow('masadhipa_bala', 'Month-lord strength: 30 virupas.', 'sourced_fact', 'FACT', [ev('b_vmdh')], CH27, ['b_vmdh'])
srow('varadhipa_bala', 'Day-lord strength: 45 virupas.', 'sourced_fact', 'FACT', [ev('b_vmdh')], CH27, ['b_vmdh'])
srow('horadhipa_bala', 'Hora-lord strength: 60 virupas.', 'sourced_fact', 'FACT', [ev('b_vmdh')], CH27, ['b_vmdh'])
srow('kala_bala', 'Temporal strength = sum of Nathonnatha, Paksha, Tribhaga, Abda/Masa/Vara/Hora, Ayana, Yuddha.', 'sourced_fact', 'FACT',
     [ev('b_kala_list')], CH27, ['b_kala_list'],
     cols=[cf('formula_text', 'sourced_fact', 'BPHS Ch.27 note (bphs:PG267:C1) lists exactly these components: Nathonnatha, Paksha, Tribhaga, Varsha-Masa-Dina-Hora, Ayana, Yudhdha.')])
srow('sthana_bala', 'Positional strength = Uchcha + Saptavargaja + Ojhayugma + Kendradi + Drekkana.', 'sourced_fact', 'FACT',
     [ev('b_sthana_list'), ev('b_sthana')], CH27, ['b_sthana_list', 'b_sthana'])
srow('kendradi_bala', 'Angular strength: 60 in kendra, 30 in panapara, 15 in apoklima.', 'sourced_fact', 'FACT', [ev('b_kendradi')], CH27, ['b_kendradi'],
     cols=[cf('formula_text', 'sourced_fact', 'Notes (bphs:PG265:C1): angle 60, succedent 30, cadent 15 virupas - matches DB.')])
srow('naisargika_bala', 'Natural strength: fixed Sun 60, Moon 51.43, Venus 42.86, Jupiter 34.29, Mercury 25.71, Mars 17.14, Saturn 8.57.', 'sourced_fact', 'FACT',
     [ev('b_naisarg'), ev('b_naisarg2')], CH27, ['b_naisarg', 'b_naisarg2'],
     cols=[cf('formula_text', 'sourced_fact', '60/7 times 1..7 for Saturn..Sun (sl.14) and the table Sun 1.000, Moon 0.857, Venus 0.714, Jupiter 0.571, Mercury 0.429, Mars 0.286, Saturn 0.143 Rupa (bphs:PG275:C1) - DB values agree (rounding).')])
srow('nathonnatha_bala', 'Diurnal/nocturnal strength: Moon/Mars/Saturn strong at night, Sun/Jupiter/Venus by day, Mercury always.', 'sourced_fact', 'FACT',
     [ev('b_nath'), ev('b_nath2')], CH27, ['b_nath', 'b_nath2'])
srow('paksha_bala', 'Lunar-phase strength: benefics gain with the waxing Moon, malefics with the waning.', 'sourced_fact', 'FACT',
     [ev('b_paksha')], CH27, ['b_paksha'],
     cols=[cf('formula_text', 'sourced_fact', 'sl.10-11: benefic Paksha bala = (Moon - Sun)/3; malefic = 60 - benefic value.')])
srow('tribhaga_bala', 'Third-of-day strength: one Rupa to the lord of the day/night third of birth (Mercury 1st, Sun 2nd, Saturn 3rd of day).', 'sourced_fact', 'FACT',
     [ev('b_tribhaga'), ev('b_tribhaga2')], CH27, ['b_tribhaga', 'b_tribhaga2'],
     cols=[cf('formula_text', 'sourced_fact', 'sl.12: Mercury/Sun/Saturn for the day thirds; Moon/Venus/Mars for night thirds; Jupiter gets it at all times (not in DB text - omission only).')])
srow('ojhayugma_bala', 'Odd-even strength: 15 virupas each for Rasi and Navamsa (max 30); Moon/Venus in even signs, others in odd.', 'sourced_fact', 'FACT',
     [ev('b_ojha'), ev('b_ojha15')], CH27, ['b_ojha', 'b_ojha15'])
srow('dig_bala', 'Directional strength: 60 virupas at the strong house, distance from the weak house /3; Jupiter/Mercury 1st, Sun/Mars 10th, Saturn 7th, Moon/Venus 4th.', 'sourced_fact', 'FACT',
     [ev('b_dig'), ev('b_dig_note'), ev('b_dig_note2')], CH27, ['b_dig', 'b_dig_note', 'b_dig_note2'])
srow('graha_drishti_value', 'Planetary aspect value 0-60 virupas by angular distance; full/three-quarter/half/quarter by house distance.', 'sourced_fact', 'FACT',
     [ev('b_drishti_q'), ev('b_drishti_virupa'), ev('b_drishti_ch26', role='context')], 'existing citation "BPHS Ch.26" resolves (printed "Chapter 26" at bphs:PG253:C1).', ['b_drishti_q'],
     notes='Speculum of aspectual values in virupas starts at bphs:PG257:C1.')
srow('drik_bala', 'Aspectual strength: benefic aspects add, malefic subtract (virupas).', 'sourced_inference', 'INFERENCE', [ev('b_drig'), ev('b_drig2')], CH27, ['b_drig'],
     inference='BPHS sl.19 states: reduce one fourth of the Drishti Pinda for malefic aspects, add a fourth for benefic aspects, and super-add the entire aspect of Mercury and Jupiter. The DB summary "benefic minus malefic" is the direction of that rule but omits the one-fourth weighting and the full Mercury/Jupiter addition.',
     cols=[cf('formula_text', 'sourced_inference', 'direction agrees; magnitude rule (1/4 of Drishti pinda; Mercury/Jupiter full) is not captured.')], uns=True)
srow('bhavadhipati_bala', 'House-lord strength: the lord\'s strength is added to the bhava strength.', 'sourced_inference', 'INFERENCE', [ev('b_bhava_lord')], CH27, ['b_bhava_lord'],
     inference='sl.26-29: "superadd the strength acquired by the lord of that Bhava"; reading that strength as the lord\'s Shadbala is an interpretation. "A house is as strong as its dispositor" (DB interpretation) is not stated.',
     cols=[cf('classical_interpretation', 'unsourced_marked', '"A house is as strong as its dispositor" is not stated in the held text.')], uns=True)
srow('bhava_dig_bala', 'House directional strength based on the natural significator occupying the bhava (max 60).', 'contradicted', 'CONTRADICTS',
     [ev('b_bhava_dig')], CH27, ['b_bhava_dig'], action='acharya',
     q='reference_strength_systems.bhava_dig_bala is described as "Based on the natural significator occupying the bhava". BPHS Ch.27 sl.26-29 (bphs:PG285:C1) computes the bhava\'s directional strength from the bhava cusp\'s distance from the 7th/4th/1st/10th house cusp depending on the sign the bhava falls in (divided by 3). Should the description be corrected to the cusp-distance rule, with karaka occupancy treated as a separate strength?',
     cols=[cf('formula_text', 'contradicted', 'DB: "Based on the natural significator occupying the bhava". Held: deduct the 7th cusp (Virgo, Gemini, Libra, Aquarius, first half Sagittarius), the 4th (Aries, Taurus, Leo, first half Capricorn, second half Sagittarius), the ascendant (Cancer, Scorpio) or the 10th (second half Capricorn, Pisces) from the bhava, /3.'),
           cf('max_value', 'sourced_fact', '/3 of up to 180 degrees gives 60 virupas.')], uns=True)
srow('bhava_drishti_bala', 'House aspectual strength: net benefic minus malefic aspect on the bhava cusp.', 'sourced_inference', 'INFERENCE', [ev('b_bhava_asp')], CH27, ['b_bhava_asp'],
     inference='sl.26-29: bhava strength increased by one fourth for a benefic aspect and decreased by one fourth for a malefic aspect; Jupiter/Mercury aspect added in full. DB "net benefic minus malefic" is the direction only.', uns=True)
srow('bhinnashtakavarga', 'Per-planet benefic-point chart across 12 signs from 8 contributors (7 planets + lagna), max 8.', 'sourced_fact', 'FACT',
     [ev('b_asht_incl'), ev('b_asht_illus')], 'existing citation "BPHS Ch.66-72": the ashtakavarga block is printed Chapters 67 (Trikona Shodhana, bphs:PG859:C1), 68 (Ekadhipatya, PG867:C1) and 72 (Samudaya illustration, PG891:C1) - range plausible; chapters 66/69-71 located by sloka not chapter header.', ['b_asht_incl', 'b_asht_illus'],
     cols=[cf('classical_interpretation', 'sourced_fact', 'Eight contributors (planets from the Sun to Saturn plus the Ascendant) confirmed by the illustration (bphs:PG891:C1). Terminology: BPHS calls the benefic point a "rekha" (line) and the malefic a "bindu" (dot) (bphs:PG858:C1); DB unit "bindu" follows modern usage.')])
srow('trikona_shodhana', 'Trinal reduction: reduce bindus within each trine to the minimum of the three (first reduction).', 'sourced_inference', 'INFERENCE',
     [ev('b_trik_def'), ev('b_trik_ch', support='FACT')], 'existing citation "BPHS Ch.66-72" resolves for this row to printed Chapter 67.', ['b_trik_def'],
     inference='Trinal grouping (Aries-Leo-Sagittarius, etc.) and that trikona shodhana comes first are stated (bphs:PG859:C1, PG868:C1). The reduction rule itself is OCR-garbled in the held chunk (bphs:PG860:C1: "the rasi which has lesser number of rekhas ... deducting its number from the total"), so DB wording "to the minimum of the three" cannot be confirmed as equivalent to the BPHS rule (subtract the lowest value from each).', uns=True,
     cols=[cf('formula_text', 'sourced_inference', 'Wording "reduce ... to the minimum of the three" is ambiguous (set equal to the minimum vs subtract the minimum).')])
srow('ekadhipatya_shodhana', 'Single-lordship reduction in signs co-lorded by one planet (second reduction).', 'sourced_fact', 'FACT',
     [ev('b_ekad'), ev('b_ekad2')], 'existing citation "BPHS Ch.66-72" resolves to printed Chapter 68.', ['b_ekad', 'b_ekad2'],
     cols=[cf('classical_interpretation', 'sourced_inference', '"yields shodhya pinda": the held text gets Rasi/Graha/Yoga pinda after both shodhanas (bphs:PG880:C1); the term "Shodhya Pinda" is not printed in the held text.')], uns=True)
srow('shodhya_pinda', 'Reduced aggregate = Rasi-pinda + Graha-pinda after the two reductions; used for ashtakavarga dasha-phala and longevity.', 'sourced_inference', 'INFERENCE',
     [ev('b_pinda'), ev('b_pinda2'), ev('b_asht_longev', support='FACT')], 'existing citation "BPHS Ch.66-72" resolves to the Pinda-sadhana chapters (pages 870-885).', ['b_pinda', 'b_pinda2'],
     inference='The held text calls Rasi Pinda + Graha Pinda the "Yoga Pinda" (bphs:PG874:C1, PG880:C1); the name "Shodhya Pinda" does not appear in the held English text, so identification of DB shodhya_pinda with the Yoga Pinda is by equivalence of definition.', uns=True)
srow('sarvashtakavarga', 'Aggregate ashtakavarga = sum of the 7 bhinnashtakavargas; 337 bindus over 12 signs; max 56 per sign; >28 strong.', 'contradicted', 'CONTRADICTS',
     [ev('b_asht_illus'), ev('b_asht_total'), ev('b_asht_thr'), ev('b_asht_thr2')], 'existing citation "BPHS Ch.66-72" resolves to printed Chapter 72 (bphs:PG890-893).', ['b_asht_total', 'b_asht_thr'], action='acharya',
     q='reference_strength_systems.sarvashtakavarga is defined as the sum of 7 bhinnashtakavargas (337 bindus, max 56 per sign, ">28 strong"). The held BPHS (Ch.72, bphs:PG891:C1) forms the Samudaya total including the Ascendant\'s ashtakavarga (illustration: Sun 3 + Moon 4 + Mars 3 + Mercury 2 + Jupiter 6 + Venus 4 + Saturn 3 + Ascendant 5 = 30) and grades houses >30 strong, 25-30 medium, <25 damaged (bphs:PG890:C1). Which convention should the platform carry, the eight-chart BPHS Samudaya with 30/25 thresholds or the seven-planet 337 total with the 28 mean?',
     cols=[cf('formula_text', 'contradicted', 'DB: 7 bhinnashtakavargas, total 337, max 56. Held: Samudaya includes the Ascendant\'s chart (8 contributors, i.e. max 64 per sign); 337 is not printed in the held text.'),
           cf('classical_interpretation', 'contradicted', 'DB: ">28 bindus is strong". Held: more than 30 rekhas advance a house, 25-30 medium, below 25 damaged.')])
srow('vimsopaka_bala', 'Twenty-point varga strength: weighted dignity score across Shadvarga/Saptavarga/Dashavarga/Shodashavarga schemes.', 'sourced_fact', 'FACT',
     [ev('b_vims'), ev('b_vims2'), ev('b_vims_note')], 'existing citation "BPHS Ch.7" resolves (printed "Chapter 7" at bphs:PG94:C1; sl.17-27).', ['b_vims', 'b_vims2'],
     cols=[cf('formula_text', 'sourced_fact', 'Shadvarga weights 6,2,4,5,2,1 (Rasi, Hora, Drekkana, Navamsa, Dvadasamsa, Trimsamsa) = 20; Saptavarga adds Saptamamsa; Dasavarga, Shodasavarga weights in sl.20-25.')])
srow('vimsottari_weight', 'Dasha weight: Vimshottari years as relative weights, 120-year total.', 'sourced_fact', 'FACT',
     [ev('b_vim_total'), ev('bphs_vim_years'), ev('bphs_vim_names')], 'existing citation "BPHS Ch.46" resolves (printed "Chapter 46" at bphs:PG499:C1, sl.12-16).', ['b_vim_total', 'bphs_vim_names', 'bphs_vim_years'],
     cols=[cf('classical_interpretation', 'not_a_classical_claim', '"Used to weight period-lord influence" is platform usage; the 120-year total and the planet years are classical (BPHS Ch.46).')])
srow('yuddha_bala', 'Planetary-war strength: winner gains, loser loses the difference of Shadbala; criterion within 1 degree, further north/brighter wins.', 'sourced_fact', 'FACT',
     [ev('b_yuddha'), ev('pd_war')], CH27 + ' The war criterion (north / brilliant rays) is Phaladipika Adh.IV sl.2, not BPHS.', ['b_yuddha', 'pd_war'],
     cols=[cf('formula_text', 'sourced_fact', 'sl.20: the difference of the two Shadbalas is added to the victor and deducted from the vanquished.'),
           cf('classical_interpretation', 'sourced_fact', 'Phaladipika: planets posited in the north with brilliant rays are the victors. A BPHS translator note (bphs:PG124:C1) gives a different popular rule (lesser longitude wins) and a latitude rule - alternative views, not contradictions of this row.')])
# --- contradictions in the strength family
srow('uchcha_bala', 'Exaltation strength: 60 x (180 - |long - debilitation point|)/180; max at exact exaltation, zero at exact debilitation.', 'contradicted', 'CONTRADICTS',
     [ev('b_uchcha'), ev('b_uchcha2'), ev('b_uchcha3')], CH27, ['b_uchcha', 'b_uchcha2', 'b_uchcha3'], action='acharya',
     q='reference_strength_systems.uchcha_bala formula_text reads "60 x (180 - |long - debilitation_point|)/180" while its interpretation says "max at exact exaltation, zero at exact debilitation". BPHS Ch.27 sl.1 (bphs:PG263:C1) says: deduct the debilitation point from the longitude, fold to <=180 degrees, and divide by 3 (i.e. 60 x D/180, D = distance from the debilitation point), which is maximal at exaltation. The stored formula is the inverse (maximal at debilitation). Should the formula be corrected to 60 x |long - debilitation_point|/180?',
     cols=[cf('formula_text', 'contradicted', 'DB: 60 x (180 - D)/180 gives 60 at the debilitation point (D=0); held rule: D/3 gives 0 there and 60 at exaltation. The DB formula also contradicts its own classical_interpretation column.'),
           cf('classical_interpretation', 'sourced_fact', '"Max at exact exaltation, zero at exact debilitation" agrees with BPHS.')])
srow('saptavargaja_bala', 'Seven-varga strength points: moolatrikona 45, own 30, great-friend 22.5, friend 15, neutral 7.5, enemy 3.75, great-enemy 1.875.', 'contradicted', 'CONTRADICTS',
     [ev('b_sapta'), ev('b_sapta2'), ev('b_sapta3'), ev('b_sapta_vargas')], CH27, ['b_sapta', 'b_sapta2', 'b_sapta3'], action='acharya',
     q='reference_strength_systems.saptavargaja_bala lists great-friend 22.5, friend 15, neutral 7.5, enemy 3.75, great-enemy 1.875. The held BPHS Ch.27 sl.2-4 (bphs:PG264:C1) gives moolatrikona 45, own 30, extreme friend 20, friend 15, neutral 10, enemy 4, extreme enemy 2 virupas. Moolatrikona/own/friend agree; the other four values differ. Which table should the platform carry (the BPHS values as held, or the modern 22.5/7.5/3.75/1.875 convention)?',
     cols=[cf('classical_interpretation', 'contradicted', 'great-friend 22.5 vs held 20; neutral 7.5 vs 10; enemy 3.75 vs 4; great-enemy 1.875 vs 2. Moolatrikona 45, own 30, friend 15 agree. The seven vargas (Rasi, Hora, Decanate, Saptamamsa, Navamsa, Dvadasamsa, Trimsamsa) agree with the DB list D1,D2,D3,D7,D9,D12,D30.')])
srow('drekkana_bala', 'Decanate strength 15 virupas: male planets in 1st drekkana, neutral in 2nd, female in 3rd.', 'contradicted', 'CONTRADICTS',
     [ev('b_drek'), ev('b_drek_note')], CH27, ['b_drek', 'b_drek_note'], action='acharya',
     q='reference_strength_systems.drekkana_bala says "male planets in 1st drekkana, neutral in 2nd, female in 3rd". BPHS Ch.27 sl.6 (bphs:PG265:C1/C2) says male, female and hermaphrodite planets respectively get the quarter Rupa in the first, second and third decanates (Male planet in 1st; Female planet in 2nd; Eunuch planet in 3rd). Should the 2nd/3rd assignment be swapped to female-2nd, neutral-3rd?',
     cols=[cf('formula_text', 'contradicted', 'DB swaps the female/neutral decanates relative to the held text.')])
srow('ayana_bala', 'Declination strength (max 60 virupas); northern declination favours most planets; replaces cheshta for Sun/Moon.', 'contradicted', 'CONTRADICTS',
     [ev('b_ayana'), ev('b_ayana_dir'), ev('b_cheshta_sm'), ev('b_cheshta_moon')], CH27, ['b_ayana', 'b_cheshta_sm', 'b_cheshta_moon'], action='acharya',
     q='reference_strength_systems (ayana_bala and cheshta_bala) say Ayana bala replaces Cheshta bala for the Sun AND the Moon. BPHS Ch.27 sl.18 (bphs:PG283:C1) says the Sun\'s Cheshta bala equals his Ayana bala but the Moon\'s Paksha bala is her Cheshta bala. Should the Moon\'s Cheshta-substitute be Paksha bala? (Also: the Sun\'s Ayana bala is doubled in BPHS, so max 60 holds for the other planets only.)',
     cols=[cf('classical_interpretation', 'contradicted', '"replaces cheshta for Sun/Moon": true for the Sun; for the Moon BPHS substitutes Paksha bala.'),
           cf('max_value', 'omission_not_contradiction', 'Sun\'s Ayana bala is multiplied by 2 in BPHS, exceeding 60.'),
           cf('formula_text', 'sourced_fact', 'Computed from declination (Kranti) with the plus/minus rule per planet (bphs:PG276:C1).')])
srow('cheshta_bala', 'Motional strength from speed/retrogression (max 60); retrograde planets gain; Sun/Moon use Ayana bala.', 'contradicted', 'CONTRADICTS',
     [ev('b_cheshta_8'), ev('b_cheshta_k'), ev('b_cheshta_sm'), ev('b_cheshta_moon')], CH27, ['b_cheshta_8', 'b_cheshta_sm', 'b_cheshta_moon'], action='acharya',
     q='See ayana_bala: cheshta_bala says "Sun/Moon use Ayana bala"; BPHS Ch.27 sl.18 gives the Moon Paksha bala as her Cheshta bala. Correct the Moon?',
     cols=[cf('classical_interpretation', 'contradicted', '"Sun/Moon use Ayana bala": Moon uses Paksha bala per sl.18.'),
           cf('formula_text', 'sourced_fact', 'Cheshta kendra /3 (sl.24-25); eight motions with strengths 60,30,15,30,15,7.5,45,30 (sl.22-23); retrograde (Vakra) = 60.')])
srow('ishta_phala', 'Benefic result = sqrt(Uchcha bala x Cheshta bala), max 60.', 'contradicted', 'CONTRADICTS',
     [ev('b_ishta_a'), ev('b_ishta'), ev('b_ch28')], 'existing citation "BPHS Ch.27": the held edition prints "Chapter 28 Ishta And Kashta Balas" (bphs:PG288:C1) - label mismatch.', ['b_ishta_a', 'b_ishta'], action='acharya',
     q='reference_strength_systems.ishta_phala formula is sqrt(Uchcha bala x Cheshta bala). BPHS Ch.28 sl.6 (bphs:PG289:C1) defines it as: reduce 1 from each of Cheshta Rasmi and Uchcha Rasmi, multiply by 10 and add, half of the sum is Ishta phala (Kashta = 60 - Ishta). The stored geometric-mean formula is the modern Shadbala-text formula. Which should the platform carry, and should the citation be Ch.28?',
     cols=[cf('formula_text', 'contradicted', 'geometric mean vs held half-sum of 10 x (rasmi - 1) terms.')])
srow('kashta_phala', 'Malefic result = 60 - Ishta phala.', 'sourced_fact', 'FACT', [ev('b_kashta'), ev('b_ch28')],
     'existing citation "BPHS Ch.27": the held edition prints this in "Chapter 28 Ishta And Kashta Balas" (bphs:PG288:C1) - label mismatch.', ['b_kashta'],
     notes='The definition 60 - Ishta is stated; its dependence on the Ishta formula inherits the ishta_phala question.')

# ----------------------------------------------------------------------------------------------------------

FLIP = {
    ('reference_signs', 'sign_id', 1): ['bphs_aries', 'pd_quad'],
    ('reference_upagrahas', 'upagraha_id', 'indrachapa'): ['bphs_chapa_inausp', 'bphs_upa_malefic'],
    ('reference_strength_systems', 'strength_id', 'bhava_dig_bala'): ['b_bhava_dig'],
    ('reference_strength_systems', 'strength_id', 'sarvashtakavarga'): ['b_asht_illus', 'b_asht_total', 'b_asht_thr', 'b_asht_thr2'],
    ('reference_strength_systems', 'strength_id', 'uchcha_bala'): ['b_uchcha', 'b_uchcha2', 'b_uchcha3'],
    ('reference_strength_systems', 'strength_id', 'saptavargaja_bala'): ['b_sapta', 'b_sapta2', 'b_sapta3'],
    ('reference_strength_systems', 'strength_id', 'drekkana_bala'): ['b_drek', 'b_drek_note'],
    ('reference_strength_systems', 'strength_id', 'ayana_bala'): ['b_cheshta_moon'],
    ('reference_strength_systems', 'strength_id', 'cheshta_bala'): ['b_cheshta_moon'],
    ('reference_strength_systems', 'strength_id', 'ishta_phala'): ['b_ishta_a', 'b_ishta'],
}
CONTRA = {
    ('reference_signs', 'sign_id', 1): ('is_biped = true', 'Aries is a quadruped sign (BPHS Ch.4 sl.6-7; Phaladipika Adh.I list of quadruped signs)'),
    ('reference_upagrahas', 'upagraha_id', 'indrachapa'): ('nature "mixed; sudden brilliance then fade"', 'Indra Chapa is inauspicious; the five (Dhuma, Vyatipata, Parivesha, Chapa, Upaketu) are malefics by nature (BPHS Ch.3 sl.61-64)'),
    ('reference_strength_systems', 'strength_id', 'bhava_dig_bala'): ('"Based on the natural significator occupying the bhava"', 'bhava dig bala from the bhava cusp\'s distance from the 7th/4th/1st/10th cusp depending on the sign the bhava falls in, /3 (BPHS Ch.27 sl.26-29)'),
    ('reference_strength_systems', 'strength_id', 'sarvashtakavarga'): ('sum of 7 bhinnashtakavargas, total 337, max 56, >28 strong', 'Samudaya total includes the Ascendant\'s chart (illustration 3+4+3+2+6+4+3+5=30); >30 strong, 25-30 medium, <25 damaged (BPHS Ch.72)'),
    ('reference_strength_systems', 'strength_id', 'uchcha_bala'): ('60 x (180 - |long - debil|)/180', 'distance from debilitation point (<=180 deg) divided by 3, i.e. 60 x D/180 (BPHS Ch.27 sl.1; worked example Sun at Pisces 12deg15 = 50.25 virupas)'),
    ('reference_strength_systems', 'strength_id', 'saptavargaja_bala'): ('great-friend 22.5, neutral 7.5, enemy 3.75, great-enemy 1.875', 'great-friend 20, neutral 10, enemy 4, great-enemy 2 virupas (BPHS Ch.27 sl.2-4); moolatrikona 45, own 30, friend 15 agree'),
    ('reference_strength_systems', 'strength_id', 'drekkana_bala'): ('male 1st, neutral 2nd, female 3rd drekkana', 'male 1st, female 2nd, hermaphrodite/eunuch 3rd (BPHS Ch.27 sl.6 and note)'),
    ('reference_strength_systems', 'strength_id', 'ayana_bala'): ('Ayana bala replaces Cheshta bala for Sun/Moon', 'Sun\'s Cheshta bala = his Ayana bala but Moon\'s Cheshta bala = her Paksha bala (BPHS Ch.27 sl.18)'),
    ('reference_strength_systems', 'strength_id', 'cheshta_bala'): ('Sun/Moon use Ayana bala', 'Sun uses Ayana bala; Moon uses Paksha bala (BPHS Ch.27 sl.18)'),
    ('reference_strength_systems', 'strength_id', 'ishta_phala'): ('sqrt(Uchcha bala x Cheshta bala)', 'half of [10 x (Cheshta rasmi - 1) + 10 x (Uchcha rasmi - 1)] (BPHS Ch.28 sl.6)'),
}
for r in ROWS:
    k = list(r['row_key'].items())[0]
    kk = (r['table'], k[0], k[1])
    if kk in FLIP:
        for c in r['corpus']:
            if c.get('ekey') in FLIP[kk]:
                c['role'] = 'contradicts'; c['support'] = 'CONTRADICTS'
    if kk in CONTRA:
        r['contradiction'] = {'db_says': CONTRA[kk][0], 'held_text_says': CONTRA[kk][1]}
    if r['state'] == 'contradicted':
        assert kk in CONTRA, kk

json.dump(ROWS, open(OUT + 'ledger.json', 'w'), indent=1, ensure_ascii=False)
from collections import Counter
print(len(ROWS))
print(Counter(r['table'] for r in ROWS))
print(Counter(r['state'] for r in ROWS))
