"""SR-K9-PUBLISHABLE round 4, finding D6: an identical rebuild must not read as a changed output.

The defect (rehearsal r4, B2): ka_yojaka's digest covered every retained candidate generation AND the generation label,
so a forced rebuild that rewrote 2,053 byte-identical rows still produced a new digest. `asset_runner` then recorded
`output_changed = true` (`prior != new`, asset_runner.py:1280) and `staleness.py` staled 29-32 downstream assets.

The fix is reader-side, no deletion: a component may declare `newest_candidate_generation`. Then the digest reads only
the generation of the newest layer candidate of the pinned chart (the one the running build wrote, the single build
slot) and the generation label is scope, not content. Superseded generations stay in the table, untouched.

Claims, one oracle each (the property is the owner's requirement, OWNER-K9-RESTORE-20261021 D6; the digest -> output_changed
-> staleness chain is covered by test_owave_wp1_output_changed.py and test_staleness.py; row values are PLANTED labels, B.10):
  S1 an identical rebuild under a new generation digests identically
  S2 a real content change digests differently
  S3 rows of a superseded generation do not enter the digest
  S4 a candidate row that appears or disappears changes the digest
  S5 a spec whose generation column is also content, or that names no chart, is refused (a spec cannot mean less than
     it says, N.8)
  S6 the v3 ka_yojaka spec is a valid reviewed spec and uses the scope
"""
import json
import uuid
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
import pytest

from pipeline.orchestrator import output_digest
from pipeline.orchestrator.provenance import canonical_digest

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
MIGRATIONS = Path(__file__).resolve().parents[5] / 'migrations'
VALUE_COLUMNS = ['chart_id', 'ayanamsha_id', 'signal_id', 'signature_class', 'dasha_eligibility_rule_jsonb',
                 'transit_trigger_jsonb', 'strength_affliction_hook_jsonb', 'derivation_ledger_jsonb',
                 'mechanism_route', 'conclusion_state_jsonb', 'mechanism_id', 'event_class_id']
# The v3 spec: the 1399 (v2) spec with the generation column moved from content to scope.
SPEC = {'version': 'nirmana-output-digest-spec-v1', 'components': [
    {'name': 'kap_candidate_classed', 'relation': 'kala_activation_predicates',
     'key_columns': ['chart_id', 'ayanamsha_id', 'mechanism_id', 'event_class_id'],
     'where_equals': {'chart_id': CHART}, 'where_not_null': ['event_class_id', 'mechanism_id'],
     'value_columns': VALUE_COLUMNS, 'newest_candidate_generation': 'generation'},
    {'name': 'kap_candidate_classless', 'relation': 'kala_activation_predicates',
     'key_columns': ['chart_id', 'ayanamsha_id', 'mechanism_id'],
     'where_equals': {'chart_id': CHART}, 'where_is_null': ['event_class_id'], 'where_not_null': ['mechanism_id'],
     'value_columns': VALUE_COLUMNS, 'newest_candidate_generation': 'generation'}]}
SPEC_SHA = canonical_digest(SPEC)


@pytest.fixture(scope='module')
def database(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as c:
        c.execute((MIGRATIONS / '1330_kala_layer_manifest_candidates.sql').read_text()
                  .split('-- A separately dispatched verifier')[0])
        c.execute('CREATE TABLE asset_output_digest_specs (asset_id text, spec_sha256 text, spec jsonb, '
                  'retired_at timestamptz)')
        c.execute('CREATE TABLE kala_activation_predicates (chart_id uuid, ayanamsha_id text, signal_id text, '
                  'signature_class text, dasha_eligibility_rule_jsonb jsonb, transit_trigger_jsonb jsonb, '
                  'strength_affliction_hook_jsonb jsonb, derivation_ledger_jsonb jsonb, generation text, '
                  'mechanism_route text, conclusion_state_jsonb jsonb, mechanism_id text, event_class_id text)')
    return isolated_kala_db_dsn


@pytest.fixture
def cur(database):
    with psycopg.connect(database, row_factory=dict_row) as c:
        c.execute('TRUNCATE kala_activation_predicates, kala_layer_candidate_grain, kala_layer_candidate CASCADE')
        c.execute('TRUNCATE asset_output_digest_specs')
        c.execute("INSERT INTO asset_output_digest_specs VALUES ('ka_yojaka', %s, %s::jsonb, NULL)",
                  (SPEC_SHA, json.dumps(SPEC)))
        yield c.cursor()
        c.rollback()


# A planted candidate graph: three mechanisms, one classless; values are labels.
ROWS = [('M1', 'EC1', 'sig-a', 'YOGA'), ('M2', 'EC1', None, 'CLASSIFY_RESIDUAL'), ('M3', None, 'sig-c', 'YOGA')]


def write_generation(cur, generation, *, rows=ROWS, minutes=0, change=None):
    """A rebuild: a new candidate (newer by `minutes`) and its rows. `change` plants one differing value."""
    cur.execute("INSERT INTO kala_layer_candidate (chart_id, generation, build_id, model_digest, rule_registry_version, "
                "conventions, created_at) VALUES (%s,%s,%s,'fixture','fixture','{}'::jsonb, now() + %s * interval '1 minute')",
                (CHART, generation, uuid.uuid4(), minutes))
    for mechanism, event_class, signal, signature in rows:
        ledger = {'mechanism': mechanism, 'witness': 'planted'}
        if change == mechanism:
            ledger['witness'] = 'changed'
        cur.execute("INSERT INTO kala_activation_predicates (chart_id, ayanamsha_id, signal_id, signature_class, "
                    "dasha_eligibility_rule_jsonb, transit_trigger_jsonb, strength_affliction_hook_jsonb, "
                    "derivation_ledger_jsonb, generation, mechanism_route, conclusion_state_jsonb, mechanism_id, "
                    "event_class_id) VALUES (%s,'lahiri',%s,%s,'{}','{}','{}',%s::jsonb,%s,'admitted','{}',%s,%s)",
                    (CHART, signal, signature, json.dumps(ledger), generation, mechanism, event_class))


def digest(cur):
    value, spec_sha = output_digest.compute_output_digest(cur, asset_id='ka_yojaka')
    assert spec_sha == SPEC_SHA
    return value


def test_an_identical_rebuild_under_a_new_generation_digests_identically(cur):
    write_generation(cur, 'candidate:first', minutes=1)
    before = digest(cur)
    write_generation(cur, 'candidate:second', minutes=2)          # same content, a new generation, the older one retained
    assert digest(cur) == before


def test_a_real_content_change_digests_differently(cur):
    write_generation(cur, 'candidate:first', minutes=1)
    before = digest(cur)
    write_generation(cur, 'candidate:second', minutes=2, change='M2')
    assert digest(cur) != before


def test_rows_of_a_superseded_generation_do_not_enter_the_digest(cur):
    write_generation(cur, 'candidate:first', minutes=1)
    write_generation(cur, 'candidate:second', minutes=2)
    before = digest(cur)
    cur.execute("UPDATE kala_activation_predicates SET derivation_ledger_jsonb = '{\"edited\": true}'::jsonb "
                "WHERE generation = 'candidate:first'")
    cur.execute("INSERT INTO kala_activation_predicates (chart_id, ayanamsha_id, generation, mechanism_id, event_class_id) "
                "VALUES (%s,'lahiri','candidate:first','M9','EC9')", (CHART,))
    assert digest(cur) == before


def test_a_candidate_row_that_appears_or_disappears_changes_the_digest(cur):
    write_generation(cur, 'candidate:first', minutes=1)
    before = digest(cur)
    write_generation(cur, 'candidate:second', minutes=2, rows=ROWS[:2])
    assert digest(cur) != before
    write_generation(cur, 'candidate:third', minutes=3, rows=ROWS + [('M4', 'EC1', 'sig-d', 'YOGA')])
    assert digest(cur) != before


@pytest.mark.parametrize('mutate,reason', [
    (lambda c: c['key_columns'].append('generation'), 'scope, not content'),
    (lambda c: c['value_columns'].append('generation'), 'scope, not content'),
    (lambda c: c.pop('where_equals'), 'chart_id'),
    (lambda c: c.update(newest_candidate_generation='Generation'), 'invalid'),
])
def test_a_scope_that_is_also_content_or_has_no_chart_is_refused(mutate, reason):
    spec = json.loads(json.dumps(SPEC))
    mutate(spec['components'][0])
    with pytest.raises(ValueError, match=reason):
        output_digest._validate_spec('ka_yojaka', spec, canonical_digest(spec))


def test_the_v3_ka_yojaka_spec_is_valid_and_scopes_both_components(cur):
    loaded = output_digest.load_output_digest_spec(cur, 'ka_yojaka')
    assert loaded.spec_sha256 == SPEC_SHA
    assert [c['newest_candidate_generation'] for c in loaded.spec['components']] == ['generation', 'generation']
    assert all('generation' not in c['key_columns'] + c['value_columns'] for c in loaded.spec['components'])
