#!/usr/bin/env python3
"""Validate an already-exported, independently approved offline L1 bundle.

The CLI reads local bytes only. The separate audit_foreign_keys(dsn) API reads
a guarded throwaway database after restore; neither interface exports, restores,
computes chart facts or obtains approval. The independent verifier owns
canonical-source and schema/grant qualification.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
REQUIRED_FILES = ('charts.json', 'chart_facts.json', 'chart_dashas.json', 'life_events.json', 'schema.sql', 'grants.sql')
RESTORED_TABLES = ('charts', 'chart_facts', 'chart_dashas', 'life_events')
PERSONAL_PARENT_REASON = 'intentional: parent personal data excluded by ruling (madhav-6d 2026-10-16)'


def _json(body):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError('duplicate JSON field')
            result[k] = v
        return result
    return json.loads(body, object_pairs_hook=unique)


def validate(directory):
    root = Path(directory).resolve()
    def read(name):
        path = root / name
        if path.is_symlink() or path.resolve().parent != root:
            raise ValueError('snapshot reference escapes bundle')
        try:
            return path.read_bytes()
        except OSError:
            raise ValueError('required snapshot input missing') from None
    raw = read('manifest.json')
    m = _json(raw)
    approval = _json(read('approval.json'))
    digest = hashlib.sha256(raw).hexdigest()
    if not isinstance(m, dict) or not isinstance(approval, dict):
        raise ValueError('snapshot manifest and approval must be objects')
    if (m.get('schema') != 'ky.canonical_l1_snapshot/1' or m.get('chart_id') != CHART
            or m.get('source') != 'governed_offline_export' or m.get('canonical') is not True
            or m.get('builder_role') != 'data_plane_builder'
            or not re.fullmatch(r'[0-9a-f]{40}', str(m.get('source_commit', '')))):
        raise ValueError('canonical source, chart, reviewed commit and builder role required')
    try:
        captured = dt.datetime.fromisoformat(m['captured_at'].replace('Z', '+00:00'))
        if captured.tzinfo is None:
            raise ValueError()
    except (KeyError, ValueError, TypeError, AttributeError):
        raise ValueError('timezone-qualified snapshot timestamp required') from None
    if (approval.get('schema') != 'ky.canonical_l1_snapshot_approval/1'
            or approval.get('result') != 'ACCEPTED' or approval.get('by') not in ('v1', 'v2', 'v3', 'v4')
            or approval.get('manifest_sha256') != digest
            or approval.get('canonical_source_verified') is not True or approval.get('schema_grants_verified') is not True):
        raise ValueError('independent approval of these exact canonical-source/schema/grant bytes required')
    files = m.get('files')
    if not isinstance(files, dict) or set(files) != set(REQUIRED_FILES):
        raise ValueError('exact facts/dashas/chart/events/schema/grants inventory required')
    counts = {}
    for name in REQUIRED_FILES:
        body = read(name)
        f = files[name]
        if (not isinstance(f, dict) or type(f.get('bytes')) is not int or len(body) != f['bytes']
                or hashlib.sha256(body).hexdigest() != f.get('sha256')):
            raise ValueError('snapshot file byte digest/length mismatch')
        if name.endswith('.json'):
            rows = _json(body)
            if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
                raise ValueError('snapshot table must be a JSON array of stored rows')
            identity = {'charts.json': 'id', 'chart_facts.json': 'fact_id',
                        'chart_dashas.json': 'dasha_row_id', 'life_events.json': 'event_id'}[name]
            if (name != 'life_events.json' and not rows) or (name == 'charts.json' and len(rows) != 1):
                raise ValueError('canonical chart/facts/dashas may not be empty')
            ids = [r.get(identity) for r in rows]
            if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
                raise ValueError('stored row identities must be present and unique')
            if any(r.get('id' if name == 'charts.json' else 'chart_id') != CHART for r in rows):
                raise ValueError('snapshot contains another chart')
            counts[name] = len(rows)
        elif not body.strip():
            raise ValueError('deployment schema/grants may not be empty')
    return dict(schema='ky.canonical_l1_snapshot_validation/1', manifest_sha256=digest,
                status='OFFLINE_BYTES_VALIDATED', chart_id=CHART, counts=counts,
                production_acceptance=False)


def audit_foreign_keys(dsn: str) -> dict:
    """Audit every FK with either endpoint in the four restored public tables.

    Call AFTER the suite's single replica-mode load transaction has committed,
    using its own guarded throwaway DSN. This API is read-only and does not
    establish source/schema/grant parity or production readiness. All errors
    return a failed verdict; no connection details or row values are emitted.

    (I) INTERPRETATION: the exact charts.client_id -> public.profiles(id)
    edge is classified without reading profiles. Its unresolved_rows is an
    honest null, whether resolved or dangling; all other edges are measured.
    Any other edge requiring a profiles read is a reported scope defect.
    """
    import ipaddress
    import os

    verdict = dict(schema='ky.canonical_l1_fk_audit/1', status='FK_AUDIT_FAILED',
                   passed=False, constraints=[], errors=[], production_acceptance=False)
    try:
        import psycopg
        from psycopg import sql
    except ImportError:
        verdict['errors'].append('database_driver_unavailable')
        return verdict

    # Parse with libpq's own parser before connecting. The fixture, not this
    # read-only inspector, owns database creation and lifecycle/ownership proof.
    try:
        info = psycopg.conninfo.conninfo_to_dict(dsn)
        local_hosts = {'127.0.0.1', 'localhost', '::1'}
        ci = os.environ.get('GITHUB_ACTIONS') == 'true'
        if (info.get('host') not in local_hosts
                or info.get('hostaddr', '127.0.0.1') not in local_hosts
                or info.get('service')
                or info.get('port') not in ({'55433', '5432'} if ci else {'55433'})
                or not info.get('dbname') or info['dbname'] in ('postgres', 'template0', 'template1')
                or any(os.environ.get(k) for k in ('PGHOST', 'PGHOSTADDR', 'PGSERVICE', 'PGSERVICEFILE'))):
            raise ValueError('unsafe target')
    except (ValueError, psycopg.Error):
        verdict['errors'].append('unsafe_audit_target')
        return verdict

    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            conn.execute("SET LOCAL statement_timeout = '30s'")
            conn.execute("SET LOCAL lock_timeout = '1s'")
            # With RLS active, fail rather than silently count only visible rows.
            conn.execute('SET LOCAL row_security = off')
            name, address, role = conn.execute(
                "SELECT current_database(), inet_server_addr()::text, "
                "current_setting('session_replication_role')").fetchone()
            addr = ipaddress.ip_interface(address).ip if address else None
            addr = (getattr(addr, 'ipv4_mapped', None) or addr) if addr else None
            ci_bridge = (ci and addr is not None and addr.version == 4 and any(
                addr in ipaddress.ip_network(net) for net in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')))
            if name != info['dbname'] or not (addr is not None and (addr.is_loopback or ci_bridge)):
                verdict['errors'].append('unsafe_connected_database')
                return verdict
            if role != 'origin':
                verdict['errors'].append('replication_role_not_origin')
                return verdict
            tables = conn.execute('''
                SELECT c.oid, c.relname FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = ANY(%s) AND c.relkind IN ('r','p')
            ''', (list(RESTORED_TABLES),)).fetchall()
            if {name for _, name in tables} != set(RESTORED_TABLES):
                verdict['errors'].append('missing_restored_tables')
                return verdict
            oids = [oid for oid, _ in tables]
            constraints = conn.execute('''
                SELECT c.oid, c.conname, cn.nspname, child.relname, pn.nspname, parent.relname,
                    ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(num, ord)
                        JOIN pg_catalog.pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.num ORDER BY k.ord),
                    ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k(num, ord)
                        JOIN pg_catalog.pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = k.num ORDER BY k.ord),
                    c.confmatchtype,
                    ARRAY(SELECT format('%%I.%%s', n.nspname, o.oprname)
                        FROM unnest(c.conpfeqop) WITH ORDINALITY k(oid, ord)
                        JOIN pg_catalog.pg_operator o ON o.oid = k.oid
                        JOIN pg_catalog.pg_namespace n ON n.oid = o.oprnamespace ORDER BY k.ord),
                    child.relkind, parent.relkind
                FROM pg_catalog.pg_constraint c
                JOIN pg_catalog.pg_class child ON child.oid = c.conrelid
                JOIN pg_catalog.pg_namespace cn ON cn.oid = child.relnamespace
                JOIN pg_catalog.pg_class parent ON parent.oid = c.confrelid
                JOIN pg_catalog.pg_namespace pn ON pn.oid = parent.relnamespace
                WHERE c.contype = 'f' AND (c.conrelid = ANY(%s) OR c.confrelid = ANY(%s))
                ORDER BY cn.nspname, child.relname, c.conname, c.oid
            ''', (oids, oids)).fetchall()
            for (oid, name, cs, child, ps, parent, child_cols, parent_cols,
                 match, operators, child_kind, parent_kind) in constraints:
                entry = dict(oid=oid, name=name, child=dict(schema=cs, table=child, columns=child_cols),
                             parent=dict(schema=ps, table=parent, columns=parent_cols),
                             classification='unmeasured', unresolved_rows=None)
                verdict['constraints'].append(entry)
                allowed = ((cs, child, child_cols, ps, parent, parent_cols)
                           == ('public', 'charts', ['client_id'], 'public', 'profiles', ['id']))
                if allowed:
                    entry.update(classification='intentional_exclusion', reason=PERSONAL_PARENT_REASON)
                    continue
                if (cs, child) == ('public', 'profiles') or (ps, parent) == ('public', 'profiles'):
                    entry.update(classification='scope_defect', reason='rehearsal must not read public.profiles')
                    verdict['errors'].append('profiles_scope_defect')
                    continue
                if (match not in ('s', 'f') or child_kind not in ('r', 'p') or parent_kind not in ('r', 'p')
                        or not child_cols or len(child_cols) != len(parent_cols) or len(operators) != len(child_cols)):
                    verdict['errors'].append('unsupported_foreign_key')
                    continue
                nonnull = sql.SQL(' AND ').join(sql.SQL('child.{} IS NOT NULL').format(sql.Identifier(c)) for c in child_cols)
                nulls = sql.SQL(' AND ').join(sql.SQL('child.{} IS NULL').format(sql.Identifier(c)) for c in child_cols)
                # Use the FK's actual parent/child equality operators, including
                # cross-type keys, rather than guessing an operator from types.
                equals = sql.SQL(' AND ').join(
                    sql.SQL('parent.{} OPERATOR({}) child.{}').format(
                        sql.Identifier(p), sql.SQL(op), sql.Identifier(c))
                    for c, p, op in zip(child_cols, parent_cols, operators))
                # Ordinary-table FKs exclude inheritance descendants; a
                # partitioned FK parent includes its declarative partitions.
                parent_scan = sql.SQL('ONLY {}' if parent_kind == 'r' else '{}').format(sql.Identifier(ps, parent))
                missing = sql.SQL('({}) AND NOT EXISTS (SELECT 1 FROM {} parent WHERE {})').format(
                    nonnull, parent_scan, equals)
                if match == 'f':
                    missing = sql.SQL('({}) OR (NOT ({}) AND NOT ({}))').format(missing, nonnull, nulls)
                count = conn.execute(sql.SQL('SELECT count(*) FROM {} child WHERE {}').format(
                    sql.Identifier(cs, child), missing)).fetchone()[0]
                entry.update(unresolved_rows=count, classification='violation' if count else 'resolved')
    except (psycopg.Error, ValueError, TypeError):
        # Query errors, permissions/RLS, timeouts and incomplete inspection can
        # never be mistaken for success. Do not leak DSNs or personal row data.
        verdict['errors'].append('database_audit_error')
        return verdict
    verdict['passed'] = not verdict['errors'] and all(
        c['classification'] in ('resolved', 'intentional_exclusion') for c in verdict['constraints'])
    if verdict['passed']:
        verdict['status'] = 'FK_AUDIT_PASSED'
    return verdict


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(validate(args.directory), sort_keys=True))


if __name__ == '__main__':
    main()
