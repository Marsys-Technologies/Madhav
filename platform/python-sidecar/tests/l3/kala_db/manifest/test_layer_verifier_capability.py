"""LAYER-VERIFIER CAPABILITY lane (SR-PREP-LANES-1 (2)): the grants chain and the read-only probe, measured on the local disposable cluster.

Claims (each with a doctrine source and its OWN single planted reversion, CLAUDE.md N.8 / N.7.6; the reversion is the parametrised case that follows it):

C1  The REAL migration chain 1330 + 1334 + 1390 (+ the schema-USAGE stage of kala-provision-verifier-role.sh) gives verifier_principal exactly the footprint
    ``publication.verify`` / ``verify-dryrun`` need (CLAUDE.md N.2 least privilege; publication.py, verify/__init__.py, publication_admission.py).
        reversions: drop 1330 / 1334 / 1390 from the chain, or revoke schema USAGE -> the probe DEVIATES with the named missing privilege AND the real verify fails.
C2  The role can do nothing beyond that (no write, no wider read, no CREATE, no ownership, no membership, no superuser edge).
        reversions: one extra grant / attribute each -> the probe names it as unexpected.
C3  Run as the real login, the real ``verify`` records the one accepted receipt and the real ``verify-dryrun`` rolls back (end to end, no superuser).
C4  The probe is honest: an absent denial table is null, ``SET ROLE`` is not a login, a connection failure prints a fixed refusal and never the DSN.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from services.kala_core import layer_verifier_probe as probe
from services.kala_core.manifest import attest_grain, open_candidate

SIDECAR = Path(__file__).resolve().parents[4]
MIGRATIONS = SIDECAR.parent / 'migrations'
CHAIN = ('1330_kala_layer_manifest_candidates.sql', '1334_kala_layer_verifier_conflict_read_grant.sql', '1390_kala_layer_operation_verifier_reads.sql')
CANONICAL = '482012f1-710e-4a25-994a-93821f5871aa'
ROLE = 'verifier_principal'


@pytest.fixture(scope='module')
def cluster(isolated_kala_db_dsn):
    """The module's own disposable database plus verifier_principal made able to log in as production's is (NOINHERIT LOGIN); every attribute restored afterwards."""
    admin = psycopg.connect(isolated_kala_db_dsn, autocommit=True)
    row = admin.execute('SELECT rolcanlogin, rolinherit, rolconnlimit FROM pg_roles WHERE rolname = %s', (ROLE,)).fetchone()
    created = row is None
    if created: admin.execute(f'CREATE ROLE {ROLE} NOLOGIN')
    admin.execute(f'ALTER ROLE {ROLE} LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 4')
    try:
        yield admin, isolated_kala_db_dsn
    finally:
        admin.execute('DROP SCHEMA IF EXISTS public CASCADE')
        admin.execute('CREATE SCHEMA public')
        admin.execute(f'DROP OWNED BY {ROLE}')
        if created:
            admin.execute(f'DROP ROLE {ROLE}')
        else:
            login, inherit, limit = row
            admin.execute(f"ALTER ROLE {ROLE} {'LOGIN' if login else 'NOLOGIN'} {'INHERIT' if inherit else 'NOINHERIT'} CONNECTION LIMIT {limit}")
        admin.close()


def build_chain(admin, *, skip=(), usage=True, tolerated=True, no_1330_grants=False):
    """A production-shaped schema: hardened public (no PUBLIC rights), the real migration files, stand-ins only for tables owned by other migrations."""
    admin.execute('DROP SCHEMA IF EXISTS public CASCADE')
    admin.execute('CREATE SCHEMA public')
    admin.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
    admin.execute('''CREATE TABLE build_runs (id uuid PRIMARY KEY, chart_id uuid, scope text, scope_target text, action text, plan jsonb, state text,
        plan_manifest jsonb, plan_manifest_digest text, created_at timestamptz DEFAULT now(), error text)''')
    for table in ('chart_facts', 'chart_dashas', 'asset_registry', 'ephemeris_daily', 'kala_gochara_windows', 'kala_f1_target_object', 'kala_f1_relationship',
                  'kala_kshetra_g2_candidate'):
        admin.execute(f'CREATE TABLE {table} (id int, payload text)')
    for name in CHAIN:
        if name in skip: continue
        text = (MIGRATIONS / name).read_text()
        if no_1330_grants and name == CHAIN[0]: text = text.split('-- A separately dispatched verifier')[0]       # 1330's own two GRANTs reverted
        admin.execute(text)
    if usage: admin.execute(f'GRANT USAGE ON SCHEMA public TO {ROLE}')             # stage grant-usage of kala-provision-verifier-role.sh
    if tolerated:                                                                      # migrations 1342 / 1387 (read-only, deliberate)
        admin.execute(f'GRANT SELECT ON kala_f1_target_object, kala_f1_relationship, kala_kshetra_g2_candidate TO {ROLE}')


def login(dsn):
    return psycopg.connect(make_conninfo(dsn, user=ROLE), autocommit=False)


def report(dsn):
    with login(dsn) as conn:
        return probe.run_probe(conn)


def check(rep, check_id):
    return next(c for c in rep['checks'] if c['id'] == check_id)


def seed_candidate(dsn, generation):
    """A completed canonical-chart candidate, written as the builder would (superuser here); returns (run_id, digest)."""
    plan = {w: [w + ':inputs'] for w in ('ka_yojaka', 'ka_sangam')}
    build = str(uuid.uuid4())
    manifest = dict(version='nirmana-run-manifest/v1', chart_id=CANONICAL, scope='layer', scope_target='L3', action='rebuild', waves=[list(plan)],
                    assets=[dict(asset_id=w, scope='chart', depends_on=[], natural_key_partition=None, has_cowriters=False, expected_code_digest='a' * 64) for w in plan])
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    with psycopg.connect(dsn) as conn:
        c = open_candidate(conn, chart_id=CANONICAL, generation=generation, build_id=build, model_digest='fixture', rule_registry_version='fixture',
                           conventions={'publication_grains': plan})
        conn.execute('INSERT INTO build_runs (id, chart_id, scope, scope_target, action, plan, state, plan_manifest, plan_manifest_digest) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s)',
                     (build, CANONICAL, 'layer', 'L3', 'rebuild', json.dumps(list(plan)), 'completed', json.dumps(manifest), digest))
        for grain in plan.values():
            attest_grain(conn, c, grain_key=grain[0], result_state='zero_rows', input_vector=grain[0] + '-vector')
    keys = sorted(g[0] for g in plan.values())
    return build, hashlib.sha256(json.dumps([(k, k + '-vector') for k in keys], separators=(',', ':')).encode()).hexdigest()


def run_op(module, argv, dsn, monkeypatch, capsys):
    monkeypatch.setenv('DATABASE_URL', make_conninfo(dsn, user=ROLE))
    code = module.main(argv)
    out = capsys.readouterr().out.strip().splitlines()
    return code, json.loads(out[-1])


# ---- C1 / C3: the real chain is exactly enough -----------------------------------------------------------------------------------------------------------


def test_real_grant_chain_matches_the_verify_footprint_exactly(cluster):
    admin, dsn = cluster
    build_chain(admin)
    rep = report(dsn)
    assert rep['verdict'] == 'MATCHES', json.dumps(rep, indent=1)
    fp = check(rep, 'footprint')
    assert fp['missing'] == [] and fp['unexpected'] == []
    assert fp['tolerated_reads'] == ['kala_f1_relationship', 'kala_f1_target_object', 'kala_kshetra_g2_candidate']
    assert all(v == 'ok' for v in check(rep, 'verify_reads')['results'].values())
    assert set(check(rep, 'denials')['results'].values()) == {'denied'}


def test_real_verify_and_dryrun_run_as_the_login_with_only_the_chain_grants(cluster, monkeypatch, capsys):
    from services.kala_core import publication, publication_admission
    admin, dsn = cluster
    build_chain(admin)
    run_id, digest = seed_candidate(dsn, 'g-verify')
    code, out = run_op(publication, ['verify', '--run-id', run_id, '--generation', 'g-verify', '--independently-derived-digest', digest], dsn, monkeypatch, capsys)
    assert (code, out['status'], out['semantic_verification']) == (0, 'INPUT_VERIFICATION_RECORDED', None)
    assert admin.execute("SELECT verifier_principal, result FROM kala_layer_verification WHERE generation = 'g-verify'").fetchall() == [(ROLE, 'accepted')]
    dry_id, dry_digest = seed_candidate(dsn, 'g-dry')
    code, out = run_op(publication_admission, ['verify-dryrun', '--run-id', dry_id, '--generation', 'g-dry', '--independently-derived-digest', dry_digest],
                       dsn, monkeypatch, capsys)
    assert (code, out['dry_run_passed'], out['rollback_confirmed'], out['write_observed_in_transaction']) == (0, True, True, True)
    assert admin.execute("SELECT count(*) FROM kala_layer_verification WHERE generation = 'g-dry'").fetchone() == (0,)


# C1 reversions: ONE per grant source. Each must (a) make the probe DEVIATE with the named privilege and (b) make the real verify fail on the same database.
@pytest.mark.parametrize('reversion, named', [
    ({'no_1330_grants': True}, 'kala_layer_candidate_grain.grain_key: SELECT'),      # 1330 grants reverted: grain read + receipt INSERT lost
    ({'skip': (CHAIN[1],)}, 'kala_layer_verification.chart_id: SELECT'),             # 1334 reverted: RETURNING / conflict-key read lost
    ({'skip': (CHAIN[2],)}, 'kala_layer_candidate.build_id: SELECT'),                # 1390 reverted: candidate + build_runs reads lost
    ({'usage': False}, None),                                                        # grant-usage stage not run
], ids=['no-1330-grants', 'no-1334', 'no-1390', 'no-schema-usage'])
def test_reverting_any_grant_source_is_detected_and_real_verify_fails(cluster, monkeypatch, capsys, reversion, named):
    from services.kala_core import publication
    admin, dsn = cluster
    build_chain(admin, **reversion)
    run_id, digest = seed_candidate(dsn, 'g-rev')
    rep = report(dsn)
    assert rep['verdict'] == 'DEVIATES'
    assert check(rep, 'verify_reads')['pass'] is False          # the second, independent detector (the statements themselves) agrees with the ACL measurement
    if named: assert named in check(rep, 'footprint')['missing']
    else: assert check(rep, 'schema')['pass'] is False
    code, out = run_op(publication, ['verify', '--run-id', run_id, '--generation', 'g-rev', '--independently-derived-digest', digest], dsn, monkeypatch, capsys)
    assert code == 3 and out['status'] == 'REFUSED'
    assert admin.execute("SELECT count(*) FROM kala_layer_verification WHERE generation = 'g-rev'").fetchone() == (0,)


# ---- C2: nothing beyond the footprint ----------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize('sql, check_id, named', [
    ('GRANT UPDATE ON kala_layer_candidate TO verifier_principal', 'footprint', 'kala_layer_candidate.state: UPDATE'),
    ('GRANT DELETE ON kala_layer_verification TO verifier_principal', 'footprint', 'kala_layer_verification: DELETE'),
    ('GRANT INSERT ON kala_layer_candidate_grain TO verifier_principal', 'footprint', 'kala_layer_candidate_grain.grain_key: INSERT'),
    ('GRANT SELECT (created_at) ON build_runs TO verifier_principal', 'footprint', 'build_runs.created_at: SELECT'),
    ('GRANT SELECT ON kala_layer_head TO verifier_principal', 'footprint', 'kala_layer_head.chart_id: SELECT'),
    ('GRANT SELECT ON chart_facts TO verifier_principal', 'denials', None),
    ('GRANT SELECT ON ephemeris_daily TO verifier_principal', 'denials', None),
    ('GRANT INSERT ON kala_f1_relationship TO verifier_principal', 'footprint', 'kala_f1_relationship.id: INSERT'),
    ('GRANT CREATE ON SCHEMA public TO verifier_principal', 'schema', None),
    ('ALTER ROLE verifier_principal CREATEROLE', 'role_attributes', None),
    ('ALTER ROLE verifier_principal INHERIT', 'role_attributes', None),
    ('CREATE ROLE ky_probe_parent NOLOGIN; GRANT ky_probe_parent TO verifier_principal', 'role_attributes', None),
    ('ALTER TABLE kala_layer_verification OWNER TO verifier_principal', 'footprint', 'kala_layer_verification: OWNED by the role'),
], ids=lambda v: v[:48] if isinstance(v, str) else None)
def test_any_extra_privilege_is_detected(cluster, sql, check_id, named):
    admin, dsn = cluster
    build_chain(admin)
    try:
        admin.execute(sql)
        rep = report(dsn)
    finally:
        admin.execute(f'ALTER ROLE {ROLE} NOCREATEROLE NOINHERIT')
        admin.execute('DROP ROLE IF EXISTS ky_probe_parent')
    assert rep['verdict'] == 'DEVIATES' and check(rep, check_id)['pass'] is False
    if named: assert named in check(rep, 'footprint')['unexpected']


# ---- C4: the probe is honest ------------------------------------------------------------------------------------------------------------------------------


def test_set_role_is_not_a_login(cluster):
    admin, dsn = cluster
    build_chain(admin)
    with psycopg.connect(dsn, options=f'-c role={ROLE}') as conn:
        rep = probe.run_probe(conn)
    ident = check(rep, 'identity')
    assert (ident['current_user'], ident['session_user'], ident['pass']) == (ROLE, 'postgres', False)


def test_denial_against_absent_tables_is_null_not_green(cluster, monkeypatch):
    admin, dsn = cluster
    build_chain(admin)
    monkeypatch.setattr(probe, 'DENIED_READS', ('no_such_table_a', 'no_such_table_b'))
    rep = report(dsn)
    assert check(rep, 'denials')['pass'] is None and rep['verdict'] == 'DEVIATES'


def test_the_probe_writes_nothing(cluster):
    admin, dsn = cluster
    build_chain(admin)
    run_id, _ = seed_candidate(dsn, 'g-ro')
    before = admin.execute("SELECT (SELECT count(*) FROM kala_layer_verification), (SELECT count(*) FROM kala_layer_candidate), pg_current_xact_id_if_assigned() IS NULL").fetchone()
    with login(dsn) as conn:
        probe.run_probe(conn)
        assert conn.read_only and conn.execute('SHOW transaction_read_only').fetchone() == ('on',)
    assert admin.execute("SELECT (SELECT count(*) FROM kala_layer_verification), (SELECT count(*) FROM kala_layer_candidate), pg_current_xact_id_if_assigned() IS NULL").fetchone() == before
    assert run_id


def test_cli_prints_one_json_line_and_never_the_connection_string(cluster):
    admin, dsn = cluster
    build_chain(admin)
    good = make_conninfo(dsn, user=ROLE)
    env = {'PATH': '/usr/bin:/bin', 'DATABASE_URL': good}
    done = subprocess.run([sys.executable, '-m', 'services.kala_core.layer_verifier_probe'], cwd=SIDECAR, env=env, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stdout + done.stderr
    lines = done.stdout.strip().splitlines()
    assert len(lines) == 1 and json.loads(lines[0])['schema'] == 'ky.layer_verifier_probe/1' and json.loads(lines[0])['verdict'] == 'MATCHES'
    bad = 'postgresql://verifier_principal:s3cretvalue@127.0.0.1:1/nowhere'
    refused = subprocess.run([sys.executable, '-m', 'services.kala_core.layer_verifier_probe'], cwd=SIDECAR, env={'PATH': '/usr/bin:/bin', 'DATABASE_URL': bad},
                             capture_output=True, text=True, timeout=60)
    assert refused.returncode == 3 and json.loads(refused.stdout)['verdict'] == 'REFUSED'
    assert 's3cretvalue' not in refused.stdout + refused.stderr and '127.0.0.1' not in refused.stdout + refused.stderr
    missing = subprocess.run([sys.executable, '-m', 'services.kala_core.layer_verifier_probe'], cwd=SIDECAR, env={'PATH': '/usr/bin:/bin'}, capture_output=True, text=True, timeout=60)
    assert missing.returncode == 2 and json.loads(missing.stdout)['verdict'] == 'REFUSED'
