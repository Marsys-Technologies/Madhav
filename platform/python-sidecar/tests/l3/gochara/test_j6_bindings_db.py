"""Actual authority adapter on guarded metadata fixtures; never seal/serving acceptance.

The inherited J6r fixture installs synthetic admission metadata before 1379.
No sky calculation or substituted ephemeris; no production connection.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import psycopg
import pytest

from .test_j6r_rehearsal_db import rehearsal_database, db, _heads
from .test_a53_inventory import CHART_ID
from .test_a53_record_store import ADMIN_DSN

ROOT = Path(__file__).resolve().parents[5]
FLEET = ROOT/'00_ARCHITECTURE/briefs/kalayantra/fleet'
sys.path.insert(0, str(FLEET))
import head_operation as head


def fresh_connection(conn):
    """A separate autocommit session on the same database. conn.info.dsn omits the password, which CI's disposable
    Postgres requires, so the admin DSN's password is carried over (none locally: trust auth)."""
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    password = conninfo_to_dict(ADMIN_DSN).get('password')
    return psycopg.connect(make_conninfo(conn.info.dsn, **({'password': password} if password else {})), autocommit=True)


def req(conn, mids, kind='publish_head_dryrun'):
    before = head.read_head(conn, CHART_ID)
    scope = dict(expected_head=before, target=dict(generation='5.0', manifest_id=mids['5.0']),
                 change_at='2026-10-16T01:00:00+00:00')
    return dict(operation_id='local-metadata-only', item_id='J-6', kind=kind, chart_id=CHART_ID,
                requested_by='adhikarin', reviewed_commit='a'*40, head_change=scope,
                args={'generation':'5.0', 'manifest-id':mids['5.0'], 'expected-head-sha256':head.sha(before)})


def test_real_dryrun_executes_cas_and_rolls_back_full_scope(db):
    conn, mids = db
    before = _heads(conn)
    got = head.change_head(conn, req(conn, mids), dry_run=True)
    assert got['status'] == 'ROLLED_BACK' and got['rollback_confirmed'] is True
    assert got['after']['generation'] == '5.0' and got['retained_rows_equal'] is True
    assert _heads(conn) == before
    assert conn.execute("SELECT count(*) FROM public.kala_gochara_publication WHERE chart_id=%s", (CHART_ID,)).fetchone()[0] == 5


def test_committed_flip_then_explicit_rollback_across_fresh_connections(rehearsal_database):
    conn, mids = rehearsal_database
    request = req(conn, mids, 'publish_head')
    before = _heads(conn)
    try:
        proof = head.change_head(conn, request, dry_run=False)
        assert proof['status'] == 'COMMITTED_AWAITING_READBACK' and proof['rollback_confirmed'] is False
        with fresh_connection(conn) as observer:
            assert head.read_head(observer, CHART_ID) == proof['after']
            assert head.observe(observer, request) == head.expected_readback(request)
        rb = copy.deepcopy(request)
        rb['kind'] = 'rollback_head'; rb['item_id'] = 'J-6r'
        rb['head_change'] = dict(expected_head=proof['after'], target=dict(generation='3.0', manifest_id=None),
                                  restore_head=proof['before'], change_at='2026-10-16T02:00:00+00:00')
        rb['args'] = {'generation':'3.0','manifest-id':'none','expected-head-sha256':head.sha(proof['after'])}
        rolled = head.change_head(conn, rb, dry_run=False)
        assert rolled['retained_rows_equal'] is True
        with fresh_connection(conn) as observer:
            assert _heads(observer) == before
            assert head.observe(observer, rb) == head.expected_readback(rb)
    finally:
        # Restore within the fixture only if a negative mutation broke rollback.
        if _heads(conn) != before:
            row = request['head_change']['expected_head']
            conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s, flipped_at=%s,'
                         ' flipped_by=%s,evidence_ref=%s WHERE chart_id=%s',
                         (row['generation'],row['flipped_at'],row['flipped_by'],row['evidence_ref'],CHART_ID))


@pytest.mark.parametrize('corrupt', ['stale_generation', 'stale_audit', 'wrong_manifest', 'candidate', 'unsealed', 'test_slice'])
def test_stale_full_head_and_invalid_target_leave_no_changes(db, corrupt):
    conn, mids = db
    request = req(conn, mids)
    if corrupt == 'stale_generation': request['head_change']['expected_head']['generation'] = 'v1'
    if corrupt == 'stale_audit': request['head_change']['expected_head']['evidence_ref'] = 'other'
    if corrupt == 'wrong_manifest': request['head_change']['target']['manifest_id'] = mids['5.1']
    for key, gen in [('candidate','5.1'),('unsealed','5.2'),('test_slice','5.3')]:
        if corrupt == key: request['head_change']['target'] = dict(generation=gen,manifest_id=mids[gen])
    # Keep the request internally well-formed: these negatives must reach the
    # actual stored-head / publication / seal checks, not fail argument shape.
    target=request['head_change']['target']
    request['args']={'generation':target['generation'],'manifest-id':target['manifest_id'],
                     'expected-head-sha256':head.sha(request['head_change']['expected_head'])}
    before = _heads(conn)
    reason='full_head_compare_and_swap_conflict' if corrupt.startswith('stale') else 'target_not_published'
    with pytest.raises(head.Refused,match=reason):
        head.change_head(conn, request, dry_run=True)
    assert _heads(conn) == before


def test_missing_previous_row_never_invents_legacy_default(db):
    conn, mids = db
    request = req(conn, mids)
    conn.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    with pytest.raises(head.Refused, match='previous_head_missing'):
        head.change_head(conn, request, dry_run=True)
    assert conn.execute('SELECT count(*) FROM public.kala_gochara_authority WHERE chart_id=%s',(CHART_ID,)).fetchone()[0] == 0


def test_execute_refuses_outer_transaction_instead_of_claiming_commit(db):
    conn, mids = db
    with pytest.raises(head.Refused, match='idle_autocommit'):
        head.change_head(conn, req(conn,mids,'publish_head'), dry_run=False)


def test_failure_after_update_rolls_back_and_preserves_caller_scope(db, monkeypatch):
    conn, mids = db
    before = _heads(conn)
    real = head.retained
    calls = []
    def changed(c, chart):
        snap = real(c,chart); calls.append(1)
        if len(calls) == 2:
            assert head.read_head(c,CHART_ID)['generation'] == '5.0'
            snap['kala_gochara_publication']['sha256'] = '0'*64
        return snap
    monkeypatch.setattr(head,'retained',changed)
    with pytest.raises(head.Refused, match='retained_rows_changed'):
        head.change_head(conn,req(conn,mids),dry_run=True)
    assert len(calls) == 2 and _heads(conn) == before


def test_readback_target_matches_only_the_exact_published_non_slice_manifest(db):
    # Head at 5.0 with the right generation but another manifest must read target_matches=false.
    conn, mids = db
    request = req(conn, mids, 'publish_head')
    conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s WHERE chart_id=%s',
                 ('5.0', CHART_ID))
    assert head.observe(conn, request)['target_matches'] is True
    other = copy.deepcopy(request)
    other['head_change']['target']['manifest_id'] = mids['5.1']
    other['args']['manifest-id'] = mids['5.1']
    got = head.observe(conn, other)
    assert got['head']['generation'] == '5.0' and got['target_matches'] is False


# ── SR-HEAD-POLICY-KEEP: the executor's own entry point (the enabled ops-table script) on the guarded fixture ──────────────────────────
def _decision(outcome='approved'):
    return dict(kind='decision', decision='D-FLIP', state='delegated', actor='steward', ts='2026-10-16T00:00:00+00:00',
                outcome=outcome, detail='fixture controller decision')


def _cli(conn, mids, tmp_path, monkeypatch, *, events, mutate=lambda r: None, cli_args=None):
    """Run head_operation.main exactly as the executor does (argv from the table's fixed_args + the request's args, the request in
    KY_OPERATION_REQUEST, KY_ROOT, DATABASE_URL), counting connections. Returns (exit code, connection count)."""
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    request = req(conn, mids, 'publish_head_dryrun')
    request['decision_event_sha256'] = head.sha(_decision())
    mutate(request)
    (tmp_path/'run/ops/receipts').mkdir(parents=True, exist_ok=True)
    (tmp_path/'run/EVENTS.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    password = conninfo_to_dict(ADMIN_DSN).get('password')
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    monkeypatch.setenv('KY_OPERATION_REQUEST', json.dumps(request, sort_keys=True, separators=(',', ':')))
    monkeypatch.setenv('DATABASE_URL', make_conninfo(conn.info.dsn, **({'password': password} if password else {})))
    connects = []
    real = psycopg.connect
    monkeypatch.setattr(psycopg, 'connect', lambda *a, **kw: connects.append(1) or real(*a, **kw))
    args = cli_args or request['args']
    argv = ['--kind', 'publish_head', '--dry-run'] + [x for k in ('generation', 'manifest-id', 'expected-head-sha256') for x in ('--'+k, args[k])]
    return head.main(argv), len(connects)


def test_cli_dry_run_passes_the_policy_gate_and_leaves_the_head_untouched(rehearsal_database, tmp_path, monkeypatch, capsys):
    conn, mids = rehearsal_database
    before = _heads(conn)
    code, connects = _cli(conn, mids, tmp_path, monkeypatch, events=[_decision()])
    proof = json.loads(capsys.readouterr().out)
    assert (code, connects) == (0, 1)
    assert proof['status'] == 'ROLLED_BACK' and proof['rollback_confirmed'] is True and proof['after']['generation'] == '5.0'
    assert _heads(conn) == before


@pytest.mark.parametrize('name', ['no_decision', 'refused_decision', 'deferred_decision', 'scope_missing', 'args_do_not_bind_scope', 'cli_args_differ_from_request'])
def test_cli_refuses_before_connecting_when_the_policy_refuses(rehearsal_database, tmp_path, monkeypatch, capsys, name):
    # Claim: a refused request never reaches the database; the policy runs before the connection is opened. Revert = drop the policy call from main().
    conn, mids = rehearsal_database
    before = _heads(conn)
    events = {'no_decision': [], 'refused_decision': [_decision('refused')], 'deferred_decision': [_decision('deferred')]}.get(name, [_decision()])
    mutate = {'scope_missing': lambda r: r.pop('head_change'),
              'args_do_not_bind_scope': lambda r: r['args'].update({'expected-head-sha256': '0'*64})}.get(name, lambda r: None)
    cli_args = None
    if name == 'cli_args_differ_from_request':
        cli_args = dict(req(conn, mids)['args'], generation='5.1')
    code, connects = _cli(conn, mids, tmp_path, monkeypatch, events=events, mutate=mutate, cli_args=cli_args)
    out = capsys.readouterr()
    assert (code, connects, out.out) == (8, 0, '')
    assert _heads(conn) == before
