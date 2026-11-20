import json, sys, collections
sys.path.insert(0, '/private/tmp/claude-504/scratch/curation/bg_reference_B')
from lib import *
tags = []
cats = {}
for l in rq("select category, count(*) from reference_topic_tags group by 1 order by 1").splitlines()[1:-1]:
    c, n = l.split('|'); cats[c] = int(n)
assert sum(cats.values()) == 481
why = {
 'placement': "Taxonomy label for an interpretive retrieval topic ('<planet> in <house/sign>'); asserts nothing by itself (description 'Classical effects of ...' is a heading, example_chunks is empty).",
 'lordship': "Taxonomy label ('lord of Nth in Mth'); asserts nothing by itself.",
 'domain': "Taxonomy label for a life-domain/timing facet; asserts nothing by itself.",
 'dasha': "Taxonomy label '<planet> period in <dasha system>'; the dasha systems named (Vimshottari, Kalachakra, Ashtottari, Yogini, Chara Jaimini) exist in the held texts but the tag makes no claim.",
 'transit': "Taxonomy label for a transit topic; asserts nothing by itself.",
}
for c, n in cats.items():
    tags.append(row(ASSET, 'reference_topic_tags', {'category': c}, "Topic-tag taxonomy rows, category '%s' (%d rows); table has no citation column" % (c, n),
                    "(no citation column; columns: canonical_id, name, category, description, example_chunks)", 'not_a_classical_claim', 'NONE', None, None, None, 'none', None,
                    row_count=n, note=why[c] + " example_chunks is '[]' on 481/481 rows (the column meant to hold chunk exemplars is empty).",
                    extra={'row_key_query': "select canonical_id from reference_topic_tags where category='%s' order by canonical_id" % c}))
ALL = []
for f in ('ledger_karakas.json', 'ledger_constants.json', 'ledger_glossary.json'):
    ALL += json.load(open(BASE + '/' + f))
ALL += tags
json.dump(ALL, open(BASE + '/ledger.json', 'w'), indent=1, ensure_ascii=False)
tot = collections.defaultdict(lambda: collections.Counter())
for o in ALL:
    tot[o['table']][o['state']] += o['row_count']
for t, c in tot.items():
    print(t, sum(c.values()), dict(c))
print('objects', len(ALL), 'rows', sum(o['row_count'] for o in ALL))
