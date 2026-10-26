"""Read-only probe of the whole-layer verifier login (KY_LAYER_VERIFIER_DATABASE_URL -> DATABASE_URL).

It proves, by measurement, that the login the executor hands to ``layer_verify`` / ``layer_verify_dryrun`` can do exactly what
``services.kala_core.publication.verify`` needs and nothing more. It writes nothing: the connection is read-only, nothing is committed,
and the only locks taken are a transaction-scoped advisory lock on a probe-only key.

Claims, each judged by its own detector (CLAUDE.md N.8; every detector can read false):

* ``identity``        current_user is ``verifier_principal`` AND session_user is the same (the DSN logs in AS the role; ``SET ROLE`` does not count).
* ``role_attributes`` pg_roles: no superuser / createrole / createdb / replication / bypassrls / inherit, can log in, no membership either way
                      except the creating admin's own ADMIN edge on the role (PostgreSQL 16 records it).
* ``schema``          USAGE on schema public, no CREATE.
* ``footprint``       the EFFECTIVE privilege set (grants, PUBLIC and membership, via has_*_privilege) over every relation and sequence in schema
                      public equals EXPECTED_* exactly: ``missing`` lists a privilege verify needs and the role lacks, ``unexpected`` lists any other
                      privilege (a write, a wider read, an ownership). Declared extras (``TOLERATED_READS``) are reported, not failed.
* ``verify_reads``    the exact read statements of ``verify`` / ``verify-dryrun`` are planned and run (with a predicate that matches nothing) and none
                      is denied.
* ``denials``         reads of tables ``verify`` has no business with are DENIED (SQLSTATE 42501); an absent table is ``null`` (not a pass).

Output: one ``ky.layer_verifier_probe/1`` JSON line. Exit 0 only when every check is true; 1 when any check is false or null.
Neither the DSN nor any libpq message is ever printed (a connection failure prints a fixed refusal, exit 3).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg import errors as pgerr

ROLE = 'verifier_principal'
SCHEMA = 'public'
NIL = '00000000-0000-0000-0000-000000000000'

# What publication.verify / verify_candidate / lock_candidate_inputs / publication_admission.rehearse read or write (each line cites its code):
#   kala_layer_candidate        publication._candidate and publication.main: chart_id, build_id, expected_head_generation, state, conventions WHERE build_id, generation (migration 1390)
#   build_runs                  publication._run: the nine named columns (migration 1390)
#   kala_layer_candidate_grain  publication._candidate (grain_key, result_state) and verify.candidate_input_digest (grain_key, input_vector) (migration 1330)
#   kala_layer_verification     verify_candidate INSERT ... ON CONFLICT (chart_id, generation) DO NOTHING RETURNING chart_id (1330 INSERT; 1334 conflict-key SELECT);
#                               publication_admission verify-dryrun observe: count(*) WHERE chart_id, generation
EXPECTED_SELECT: dict[str, frozenset[str] | None] = {      # None = the whole table (table-level SELECT)
    'kala_layer_candidate': frozenset({'chart_id', 'generation', 'build_id', 'expected_head_generation', 'state', 'conventions'}),
    'build_runs': frozenset({'id', 'chart_id', 'scope', 'scope_target', 'action', 'plan', 'state', 'plan_manifest', 'plan_manifest_digest'}),
    'kala_layer_candidate_grain': None,
    'kala_layer_verification': frozenset({'chart_id', 'generation'}),
}
EXPECTED_INSERT: dict[str, frozenset[str] | None] = {'kala_layer_verification': None}
# Read-only SELECTs that other migrations grant verifier_principal ON PURPOSE (1342 and 1387, K2 / K5 candidate tables). verify does not read them; they are
# tolerated (reported under ``tolerated_reads``) and never a write. Any other extra privilege is ``unexpected``.
TOLERATED_READS = frozenset({'kala_f1_target_object', 'kala_f1_relationship', 'kala_kshetra_g2_candidate'})
# Tables verify must NOT reach. A read of each must be denied (42501).
DENIED_READS = ('chart_facts', 'chart_dashas', 'asset_registry', 'kala_layer_head', 'kala_gochara_windows', 'ephemeris_daily')

VERIFY_READS: tuple[tuple[str, str], ...] = (
    ('candidate', 'SELECT chart_id, build_id, expected_head_generation, state, conventions FROM kala_layer_candidate WHERE build_id = %s AND generation = %s'),
    ('build_run', 'SELECT id, chart_id, scope, scope_target, action, plan, state, plan_manifest, plan_manifest_digest FROM build_runs WHERE id = %s'),
    ('grain_status', 'SELECT grain_key, result_state FROM kala_layer_candidate_grain WHERE chart_id = %s AND generation = %s'),
    ('grain_input', 'SELECT grain_key, input_vector FROM kala_layer_candidate_grain WHERE chart_id = %s AND generation = %s ORDER BY grain_key'),
    ('receipt_count', 'SELECT count(*) FROM kala_layer_verification WHERE chart_id = %s AND generation = %s'),
)
VERIFY_READ_PARAMS = {'candidate': (NIL, ''), 'build_run': (NIL,), 'grain_status': (NIL, ''), 'grain_input': (NIL, ''), 'receipt_count': (NIL, '')}
ADVISORY_SQL = 'SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))'     # manifest.lock_candidate_inputs, on a key no candidate can have
ADVISORY_KEY = '["ky-layer-verifier-probe","no-candidate"]'

RELATION_KINDS = ('r', 'p', 'v', 'm', 'f')
TABLE_PRIVS = ('DELETE', 'TRUNCATE', 'TRIGGER')            # table-level only
COLUMN_PRIVS = ('SELECT', 'INSERT', 'UPDATE', 'REFERENCES')


def _check(check_id: str, claim: str, ok: bool | None, **detail: Any) -> dict:
    return {'id': check_id, 'claim': claim, 'pass': ok, **detail}


def identity(conn: Any) -> dict:
    cur, ses = conn.execute('SELECT current_user, session_user').fetchone()
    return _check('identity', 'the login IS verifier_principal (current_user and session_user)', cur == ROLE and ses == ROLE,
                  current_user=cur, session_user=ses)


def role_attributes(conn: Any) -> dict:
    row = conn.execute('SELECT oid, rolsuper, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls, rolinherit, rolcanlogin, rolconnlimit '
                       'FROM pg_roles WHERE rolname = %s', (ROLE,)).fetchone()
    if row is None:
        return _check('role_attributes', 'least-privilege login attributes, no memberships', None, reason='role absent')
    oid, sup, crole, cdb, repl, bypass, inherit, login, limit = row
    bad = [n for n, v in (('superuser', sup), ('createrole', crole), ('createdb', cdb), ('replication', repl), ('bypassrls', bypass), ('inherit', inherit)) if v]
    if not login: bad.append('cannot_login')
    member_of = [r[0] for r in conn.execute('SELECT r.rolname FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.roleid WHERE m.member = %s ORDER BY 1', (oid,))]
    # members OF the role: PostgreSQL 16 records only the creating admin's own ADMIN edge (no inherit, no set); any edge that lets a member become the role is a violation
    flags = 'AND (m.inherit_option OR m.set_option)' if conn.info.server_version >= 160000 else ''
    members = [r[0] for r in conn.execute(f'SELECT m.member::regrole::text FROM pg_auth_members m WHERE m.roleid = %s {flags} ORDER BY 1', (oid,))]
    if member_of: bad.append('member_of:' + ','.join(member_of))
    if members: bad.append('has_members:' + ','.join(members))
    return _check('role_attributes', 'least-privilege login attributes, no memberships', not bad, violations=bad, connection_limit=limit)


def schema_access(conn: Any) -> dict:
    usage, create = conn.execute('SELECT has_schema_privilege(current_user, %s, %s), has_schema_privilege(current_user, %s, %s)', (SCHEMA, 'USAGE', SCHEMA, 'CREATE')).fetchone()
    return _check('schema', 'USAGE on schema public, no CREATE', bool(usage) and not create, usage=usage, create=create)


def measured_privileges(conn: Any) -> dict[str, dict[str, Any]]:
    """{relation: {'owned': bool, 'columns': {priv: set(columns)}, 'table': {priv: bool}, 'sequence': {...}}} for every relation of schema public (effective privileges)."""
    out: dict[str, dict[str, Any]] = {}
    rels = conn.execute('SELECT c.oid, c.relname, c.relowner = (SELECT oid FROM pg_roles WHERE rolname = current_user) FROM pg_class c '
                        'WHERE c.relnamespace = %s::regnamespace AND c.relkind = ANY(%s) ORDER BY c.relname', (SCHEMA, list(RELATION_KINDS))).fetchall()
    for oid, name, owned in rels:
        cols = {p: set() for p in COLUMN_PRIVS}
        for attnum, attname in conn.execute('SELECT attnum, attname FROM pg_attribute WHERE attrelid = %s AND attnum > 0 AND NOT attisdropped', (oid,)).fetchall():
            for p in COLUMN_PRIVS:
                if conn.execute('SELECT has_column_privilege(%s, %s::smallint, %s)', (oid, attnum, p)).fetchone()[0]:
                    cols[p].add(attname)
        allcols = {r[0] for r in conn.execute('SELECT attname FROM pg_attribute WHERE attrelid = %s AND attnum > 0 AND NOT attisdropped', (oid,))}
        tbl = {p: bool(conn.execute('SELECT has_table_privilege(%s, %s)', (oid, p)).fetchone()[0]) for p in TABLE_PRIVS}
        out[name] = {'owned': bool(owned), 'columns': cols, 'all_columns': allcols, 'table': tbl}
    for oid, name in conn.execute("SELECT oid, relname FROM pg_class WHERE relnamespace = %s::regnamespace AND relkind = 'S' ORDER BY 1", (SCHEMA,)).fetchall():
        usage_or_update = [p for p in ('USAGE', 'UPDATE') if conn.execute('SELECT has_sequence_privilege(%s, %s)', (oid, p)).fetchone()[0]]
        if usage_or_update: out['(sequence) ' + name] = {'owned': False, 'columns': {}, 'all_columns': set(), 'table': {}, 'sequence': usage_or_update}
    return out


def footprint(conn: Any) -> dict:
    measured = measured_privileges(conn)
    missing: list[str] = []
    unexpected: list[str] = []
    tolerated: list[str] = []
    for name, m in sorted(measured.items()):
        if 'sequence' in m:
            unexpected.append(f"{name}: {'+'.join(m['sequence'])}")
            continue
        if m['owned']: unexpected.append(f'{name}: OWNED by the role')
        for priv in TABLE_PRIVS:
            if m['table'][priv]: unexpected.append(f'{name}: {priv}')
        for priv, want_map in (('SELECT', EXPECTED_SELECT), ('INSERT', EXPECTED_INSERT), ('UPDATE', {}), ('REFERENCES', {})):
            have = m['columns'][priv]
            want = m['all_columns'] if name in want_map and want_map[name] is None else (want_map.get(name) or frozenset())
            if name in TOLERATED_READS and priv == 'SELECT' and have == m['all_columns']:
                tolerated.append(name); continue
            for col in sorted(have - set(want)): unexpected.append(f'{name}.{col}: {priv}')
            for col in sorted(set(want) - have): missing.append(f'{name}.{col}: {priv}')
    for name in sorted(set(EXPECTED_SELECT) | set(EXPECTED_INSERT)):
        if name not in measured: missing.append(f'{name}: relation absent from schema {SCHEMA}')
    return _check('footprint', 'effective privileges equal exactly what verify needs (no more, no less)', not missing and not unexpected,
                  missing=missing, unexpected=unexpected, tolerated_reads=tolerated)


def _attempt(conn: Any, sql: str, params: tuple) -> tuple[str, str | None]:
    """Run one statement in a savepoint; ('ok'|'denied'|'absent'|'error', sqlstate)."""
    try:
        with conn.transaction():
            conn.execute(sql, params).fetchall()
        return 'ok', None
    except pgerr.InsufficientPrivilege as exc:
        return 'denied', exc.sqlstate
    except (pgerr.UndefinedTable, pgerr.UndefinedColumn) as exc:
        return 'absent', exc.sqlstate
    except psycopg.Error as exc:
        return 'error', exc.sqlstate


def verify_reads(conn: Any) -> dict:
    results = {name: _attempt(conn, sql, VERIFY_READ_PARAMS[name])[0] for name, sql in VERIFY_READS}
    results['advisory_lock'] = _attempt(conn, ADVISORY_SQL, (ADVISORY_KEY,))[0]
    bad = {k: v for k, v in results.items() if v != 'ok'}
    return _check('verify_reads', 'every read statement of verify / verify-dryrun is permitted', not bad, results=results)


def denials(conn: Any) -> dict:
    results = {t: _attempt(conn, f'SELECT 1 FROM {SCHEMA}.{t} WHERE false', ())[0] for t in DENIED_READS}
    ok: bool | None = all(v == 'denied' for v in results.values())
    if not ok and all(v in ('denied', 'absent') for v in results.values()): ok = None      # an absent table proves nothing: null, not green
    return _check('denials', 'reads outside the verifier closure are denied (42501)', ok, results=results)


def run_probe(conn: Any) -> dict:
    conn.read_only = True
    checks = [identity(conn), role_attributes(conn), schema_access(conn), footprint(conn), verify_reads(conn), denials(conn)]
    conn.rollback()
    verdict = 'MATCHES' if all(c['pass'] is True for c in checks) else 'DEVIATES'
    return {'schema': 'ky.layer_verifier_probe/1', 'ts': datetime.now(timezone.utc).isoformat(), 'role': ROLE, 'read_only': True,
            'verdict': verdict, 'checks': checks}


def main(argv: list[str] | None = None) -> int:
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        print(json.dumps({'schema': 'ky.layer_verifier_probe/1', 'verdict': 'REFUSED', 'reason': 'operation-specific DATABASE_URL is required'}))
        return 2
    try:
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            report = run_probe(conn)
    except psycopg.Error:
        # Connection diagnostics may contain secrets: do not echo libpq errors.
        print(json.dumps({'schema': 'ky.layer_verifier_probe/1', 'verdict': 'REFUSED', 'reason': 'database connection or probe failed'}))
        return 3
    print(json.dumps(report, sort_keys=True, default=str))
    return 0 if report['verdict'] == 'MATCHES' else 1


if __name__ == '__main__':
    sys.exit(main())
