# Source: /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kv3-b-ops-scripts/00_ARCHITECTURE/briefs/kalayantra/fleet/ops/common.py
# Original sha256: df4602cca69ca8603fda47df308e8d68e5df934c2d27fc3695dd24ac9e4edb96; date: 2026-10-14
"""Disabled KV3-B-OPS preparation. Contract output, never an executor receipt.

(I) INTERPRETATIONS and enablement prerequisites are in the two bootstrap packets.
Import and dry-run never connect or write. Execute consumes only DATABASE_URL.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import logging
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qs, unquote, urlsplit

FLEET = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(FLEET))
import operation_adapters as A

Refusal = A.Refusal
# PLANNER_STATE.json:904: the owner's finite post-round rebuild, not every prefix match.
OWNER_ASSETS = (
    'ka_yojaka', 'ka_sangam', 'ka_vighnakara', 'ka_gochara',
    'ka_gochara_v3_century_materialize', 'ka_gochara_v4_41_candidate',
    'ka_gochara_v5', 'ka_vedha_gochara', 'ph_muhurta',
)
KINDS = ('backup_snapshot', 'backup_restore_verify', 'orchestrator_rebuild', 'orchestrator_rebuild_readback')
IDENTIFIER = re.compile(r'^[a-z][a-z0-9_]*$')
SAFE_ID = re.compile(r'^[A-Za-z0-9_.-]{1,80}$')
# runner.py:356-365, asset_runner.py:399/819, migration 291:2 (layer_index).
REGISTRY_SQL = """SELECT asset_id, layer_index, scope, is_active, has_writer,
 COALESCE(depends_on, '{}') AS depends_on, target_table, count_sql,
 integrity_check_sql, target_floor FROM asset_registry ORDER BY asset_id"""
TABLES_SQL = """SELECT n.nspname AS schema, c.relname AS name,
 COALESCE((SELECT json_agg(DISTINCT rn.nspname || '.' || rc.relname ORDER BY rn.nspname || '.' || rc.relname)
 FROM pg_constraint fk JOIN pg_class rc ON rc.oid=fk.confrelid
 JOIN pg_namespace rn ON rn.oid=rc.relnamespace
 WHERE fk.conrelid=c.oid AND fk.contype='f'), '[]'::json) AS depends_on
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='public' AND c.relkind IN ('r','p') ORDER BY c.relname"""


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise Refusal('input', 'the input is not a regular non-symlink file')
    obj = json.loads(p.read_text())
    if A.secret_refusal(obj):
        raise Refusal('secret_value', 'an input contains credential-shaped text')
    return obj


def select_assets(scope):
    if not isinstance(scope, dict) or scope.get('schema') != 'ky.ops_scope/1':
        raise Refusal('scope', 'a reviewed ky.ops_scope/1 registry/table snapshot is required')
    registry = scope.get('registry')
    if not isinstance(registry, list) or not all(isinstance(r, dict) for r in registry):
        raise Refusal('registry', 'the registry snapshot is not a row list')
    indexed = {r.get('asset_id'): r for r in registry}
    if len(indexed) != len(registry):
        raise Refusal('registry', 'duplicate registry asset identifiers')
    rows = []
    for name in OWNER_ASSETS:
        r = indexed.get(name)
        if (r is None or r.get('layer_index') != ('L3' if name.startswith('ka_') else 'L4')
                or r.get('scope') != 'per_chart' or r.get('is_active') is not True or r.get('has_writer') is not True):
            raise Refusal('registry', 'an owner-scoped asset is absent, inactive, not chart-owned, or in the wrong layer')
        deps = r.get('depends_on')
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps) or 'ka_avadhi' in deps:
            raise Refusal('dependencies', 'unresolved dependencies or the excluded ka_avadhi dependency')
        rows.append(r)
    # Preserve owner's phase barriers; topologically sort middle group using live registry edges.
    edges = {r['asset_id']: set(r['depends_on']) & set(OWNER_ASSETS) for r in rows}
    edges['ka_sangam'].add('ka_yojaka')
    edges['ka_vighnakara'].add('ka_sangam')
    for name in OWNER_ASSETS[3:-1]:
        edges[name].add('ka_vighnakara')
    edges['ph_muhurta'].update(OWNER_ASSETS[:-1])
    ordered = []
    while len(ordered) != len(rows):
        ready = next((n for n in OWNER_ASSETS if n not in ordered and edges[n] <= set(ordered)), None)
        if ready is None:
            raise Refusal('dependencies', 'the registry contradicts the owner phase order or contains a cycle')
        ordered.append(ready)
    # The existing on_complete propagates staleness beyond the selected plan.
    affected = set(ordered)
    while True:
        extra = {r.get('asset_id') for r in registry if r.get('is_active') is True
                 and set(r.get('depends_on') or []) & affected} - affected
        if not extra:
            break
        affected.update(extra)
    if any(indexed[n].get('layer_index') in ('L0', 'L1', 'L2') for n in affected):
        raise Refusal('lower_layer', 'downstream staleness would touch a lower-layer asset')
    return ordered, indexed


def select_tables(scope, assets, registry):
    entries = scope.get('tables')
    if not isinstance(entries, list) or not entries:
        raise Refusal('tables', 'a public table/FK inventory is required')
    tables = {}
    for row in entries:
        if (not isinstance(row, dict) or row.get('schema') != 'public'
                or not isinstance(row.get('name'), str) or not IDENTIFIER.fullmatch(row['name'])
                or not isinstance(row.get('depends_on'), list)):
            raise Refusal('tables', 'the inventory contains an unsupported table')
        if row['name'] in tables:
            raise Refusal('tables', 'the inventory contains duplicate tables')
        tables[row['name']] = row
    selected = {n for n in tables if n.startswith(('ka_', 'ph_', 'kala_', 'phala_', 'build_', 'asset_'))}
    for asset in assets:
        name = registry[asset].get('target_table')
        if not isinstance(name, str) or not IDENTIFIER.fullmatch(name) or name not in tables:
            raise Refusal('tables', 'an owner-scoped target table is absent or unsupported')
        selected.add(name)
    selected.update(n for n in ('asset_registry', 'asset_throughput', 'build_runs', 'build_run_assets') if n in tables)
    pending = list(selected)
    while pending:
        for dep in tables[pending.pop()]['depends_on']:
            if not isinstance(dep, str) or not dep.startswith('public.') or dep[7:] not in tables:
                raise Refusal('tables', 'a referenced table lies outside the known public inventory')
            name = dep[7:]
            if name not in selected:
                selected.add(name)
                pending.append(name)
    return sorted(selected)


def connection_env():
    """No connection file, libpq service, .pgpass or secret-bearing argv fallback."""
    value = os.environ.get('DATABASE_URL')
    if not value:
        raise Refusal('connection', 'the executor supplied no DATABASE_URL')
    try:
        u = urlsplit(value)
        query = parse_qs(u.query, strict_parsing=True)
        if (u.scheme not in ('postgres', 'postgresql') or not u.hostname or not u.username
                or not u.password or not u.path.startswith('/') or u.fragment
                or set(query) - {'sslmode'} or any(len(v) != 1 for v in query.values())):
            raise ValueError()
        port = str(u.port or 5432)
        database = unquote(u.path[1:])
        if not IDENTIFIER.fullmatch(database):
            raise ValueError()
        env = A.remote_env()
        env.update(PGHOST=u.hostname, PGPORT=port, PGDATABASE=database,
                   PGUSER=unquote(u.username), PGPASSWORD=unquote(u.password),
                   PGPASSFILE='/dev/null', PGSERVICEFILE='/dev/null', PGCONNECT_TIMEOUT='10')
        if query:
            if query['sslmode'][0] not in ('disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full'):
                raise ValueError()
            env['PGSSLMODE'] = query['sslmode'][0]
        return env
    except (ValueError, TypeError):
        raise Refusal('connection', 'the supplied connection is not a supported explicit environment-only URI') from None


def tool(argv, env):
    try:
        p = subprocess.run(argv, env=env, capture_output=True, timeout=21000)
    except (OSError, subprocess.TimeoutExpired):
        raise Refusal('tool', 'a PostgreSQL tool is unavailable or timed out; no automatic retry') from None
    if p.returncode:
        raise Refusal('tool', 'a PostgreSQL tool failed; diagnostics withheld; no automatic retry')


def state_path(*parts):
    root = Path(os.environ.get('KY_ROOT', ''))
    if not root.is_absolute():
        raise Refusal('storage', 'an absolute executor KY_ROOT is required')
    p = root / 'run' / 'ops'
    for part in parts:
        p /= part
    # Refuse existing links at every boundary, including an input/artifact filename.
    if any(parent.is_symlink() for parent in (p, *p.parents)):
        raise Refusal('storage', 'a state or artifact path contains a symlink')
    return p


def reserve(kind, key, identity):
    path = state_path('adapter_keys', hashlib.sha256(key.encode()).hexdigest()+'.json')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with path.open('x') as f:
            os.chmod(path, 0o600)
            json.dump(dict(kind=kind, identity=identity, status='reserved_no_retry'), f)
    except FileExistsError:
        raise Refusal('idempotency', 'this key was attempted before; interrupted or failed work is never retried') from None


def dump_plan(directory, tables, snapshot):
    base = ['pg_dump', '--no-password', '--no-owner', '--no-privileges', '--format=plain', '--snapshot', snapshot]
    # Complete schema supports dependencies; only bounded data is exported. Exclude extensions? No silent omission.
    schema = base + ['--schema-only', '--section=pre-data', '--file', str(directory/'schema.sql')]
    data = base + ['--data-only', '--file', str(directory/'data.sql')]
    for name in tables:
        data += ['--table', '"public"."'+name+'"']
    constraints = base + ['--schema-only', '--section=post-data', '--file', str(directory/'constraints.sql')]
    return [schema, data, constraints]


def verify_readback(readback, assets, registry):
    rows = readback.get('assets') if isinstance(readback, dict) else None
    if (not isinstance(readback, dict) or readback.get('state') != 'completed' or not isinstance(rows, list) or len(rows) != len(assets)
            or {r.get('asset_id') for r in rows} != set(assets)):
        raise Refusal('readback', 'the run is not completed with an exact asset census')
    for r in rows:
        count = r.get('rows')
        if (r.get('run_state') != 'complete' or r.get('throughput_state') not in ('lit', 'service_ok')
                or isinstance(count, bool) or not isinstance(count, int) or count < 0
                or (count == 0 and registry[r['asset_id']].get('target_floor') != 0)
                or r.get('integrity') is not True):
            raise Refusal('readback', 'an asset has no terminal success, measured count or passing integrity detector')


def execute_serial(runner, run_id, assets):
    """Existing runner + existing execute_dag callback interface; no writer/transaction contract changes.

    One worker, failure/timeout/block sets stop before the next dispatch. Never resume a run.
    The enclosing runner retains its chart lock, frozen-manifest validation and final reconciliation.
    """
    original = runner.execute_dag

    def bounded(**kw):
        if kw.get('plan') != assets:
            raise Refusal('run_scope', 'the runner changed the bounded asset plan before scheduling')
        if kw.get('seed_failed'):
            raise Refusal('run_scope', 'preflight already failed an asset; no writer is dispatched')
        failed = []
        work = kw['run_fn']
        stop = kw.get('should_stop') or (lambda: None)

        def one(asset):
            if failed or asset not in assets:
                raise Refusal('run_scope', 'a worker tried to dispatch beyond the first failure or outside scope')
            try:
                outcome = work(asset)
            except BaseException:
                failed.append(asset)
                raise
            if outcome not in runner._SUCCESS_OUTCOMES:
                failed.append(asset)
            return outcome

        def wrap(callback):
            def callback_stop(asset, *rest):
                failed.append(asset)
                if callback:
                    return callback(asset, *rest)
            return callback_stop

        kw.update(worker_limit=1, run_fn=one, should_stop=lambda: 'stop' if failed else stop(),
                  on_timeout=wrap(kw.get('on_timeout')), on_block=wrap(kw.get('on_block')))
        return original(**kw)

    runner.execute_dag = bounded
    try:
        return runner.execute_run(run_id)
    finally:
        runner.execute_dag = original


def operate(kind, argv, *, transport=None):
    if kind not in KINDS:
        raise Refusal('kind', 'unknown operation kind')
    parser = argparse.ArgumentParser(allow_abbrev=False)
    A.add_mode_arguments(parser)
    allowed = ['scope', 'idempotency-key'] + (['label'] if kind.startswith('backup_') else ['assets', 'run-id'])
    ns = A.parse_request_args(argv, allowed, parser)
    mode = A.resolve_mode(ns.dry_run, ns.execute)
    key = ns.idempotency_key
    if not isinstance(key, str) or not SAFE_ID.fullmatch(key) or key in ('.', '..'):
        raise Refusal('idempotency', 'a safe explicit idempotency key is required')
    if not ns.scope:
        raise Refusal('scope', 'the reviewed scope snapshot path is required')
    scope = read_json(ns.scope)
    assets, registry = select_assets(scope)
    if not kind.startswith('backup_') and ns.assets is not None and ns.assets.split(',') != assets:
        raise Refusal('assets', 'the existing assets argument can only confirm the exact runtime-derived list')
    tables = select_tables(scope, assets, registry)
    identity = dict(script_sha256=sha({p.name: file_sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))}), input_sha256=sha(vars(ns) | {'scope': scope, 'mode': None, 'dry_run': None, 'execute': None}))
    record = dict(schema=A.RECORD_SCHEMA, kind=kind, mode=mode, submitted=False, **identity,
                  idempotency_key=key, chart_id=A.CANONICAL_CHART, assets=assets, tables=tables,
                  scope_sha256=sha(scope), backup_taken=None, restore_verified=None, result_verified=None,
                  preflight={'scope_snapshot_validated': True, 'live_connection_checked': None},
                  registry_sql=REGISTRY_SQL, tables_sql=TABLES_SQL)
    if kind.startswith('backup_'):
        label = ns.label
        if not isinstance(label, str) or not SAFE_ID.fullmatch(label) or label in ('.', '..'):
            raise Refusal('label', 'a safe explicit backup label is required')
        directory = state_path('artifacts', label)
        planned = dump_plan(directory, tables, '<runtime-exported-snapshot>') if kind == 'backup_snapshot' else [
            ['psql', '--no-psqlrc', '--no-password', '--set', 'ON_ERROR_STOP=1', '--single-transaction',
             '--file', str(directory/'schema.sql'), '--file', str(directory/'data.sql'), '--file', str(directory/'constraints.sql')]]
        record.update(label=label, planned_argv=planned)
    else:
        if not isinstance(ns.run_id, str) or not A.RUN_ID.fullmatch(ns.run_id):
            raise Refusal('run_id', 'an explicit pre-staged run UUID is required')
        record.update(run_id=ns.run_id, planned_argv=[[sys.executable, '-B', str(Path(__file__).parent/(kind+'.py')), '--execute', '--scope', str(Path(ns.scope).resolve()), '--idempotency-key', key, '--run-id', ns.run_id]],
                      runtime_call='pipeline.orchestrator.runner.execute_run(run_id)' if kind == 'orchestrator_rebuild' else 'registry count/integrity SQL plus run/throughput census',
                      execution_rule='pre-staged frozen rebuild; registry-exact scope; serial; first failure stops; no retry')
    # Check planned record before opening a connection or reserving anything.
    A.emit(record)
    if mode == 'dry_run':
        return record
    env = connection_env()
    if kind == 'backup_restore_verify' and (env['PGHOST'] != A.LANE_HOST or not A.LANE_DATABASE.fullmatch(env['PGDATABASE'])):
        raise Refusal('lane_target', 'restore requires an already provisioned empty 127.0.0.1 ky_<name> scratch database')
    backup = None
    if kind == 'backup_restore_verify':
        backup = read_json(directory/'manifest.json')
        if (backup.get('schema') != 'ky.logical_backup/1' or backup.get('scope_sha256') != sha(scope)
                or backup.get('tables') != tables or backup.get('status') != 'complete'):
            raise Refusal('backup', 'the named backup is not a completed backup of this exact scope')
        for name in ('schema.sql', 'data.sql', 'constraints.sql'):
            p = directory/name
            if p.is_symlink() or not p.is_file() or file_sha(p) != backup.get('files', {}).get(name):
                raise Refusal('backup', 'a logical dump file is absent or has changed')
    t = transport or Postgres(env)
    try:
        if kind != 'backup_restore_verify' and t.inspect_scope() != scope:
            raise Refusal('scope_drift', 'the runtime registry/table scope differs from the reviewed snapshot')
        if kind.startswith('orchestrator_rebuild'):
            run = t.run_record(ns.run_id)
            if (run.get('chart_id') != A.CANONICAL_CHART or run.get('action') != 'rebuild' or run.get('plan') != assets):
                raise Refusal('run_scope', 'the run chart, rebuild action or exact bounded plan differs')
            if kind == 'orchestrator_rebuild' and (run.get('state') != 'planned' or not t.dependencies_ready(assets)):
                raise Refusal('run_scope', 'the run was attempted or upstream completeness is absent')
        if kind == 'backup_restore_verify' and not t.empty_scratch():
            raise Refusal('lane_target', 'scratch database is not empty; no overwrite, clean, drop or repair')
        reserve(kind, key, identity)
        record['submitted'] = True
        if kind == 'backup_snapshot':
            directory.mkdir(parents=True, mode=0o700, exist_ok=False)
            snapshot = t.snapshot()
            measurements = t.measure(tables)
            planned = dump_plan(directory, tables, snapshot)
            for command in planned:
                tool(command, env)
            files = {name: file_sha(directory/name) for name in ('schema.sql', 'data.sql', 'constraints.sql')}
            if any((directory/name).stat().st_size == 0 for name in files):
                raise Refusal('backup', 'a logical dump is empty')
            for name in files:
                os.chmod(directory/name, 0o600)
            manifest = dict(schema='ky.logical_backup/1', status='complete', snapshot=snapshot, label=label,
                            created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                            scope_sha256=sha(scope), tables=tables, measurements=measurements, files=files,
                            source={k: env[k] for k in ('PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER')}, **identity)
            path = directory/'manifest.json'
            with path.open('x') as f:
                os.chmod(path, 0o600)
                json.dump(manifest, f, indent=2, sort_keys=True)
            record.update(backup_taken=True, planned_argv=planned, manifest_sha256=file_sha(path), measurements=measurements)
        elif kind == 'backup_restore_verify':
            tool(planned[0], env)
            # Release the emptiness-check snapshot before measuring the committed psql restore.
            t.restored()
            measurements = t.measure(tables)
            if measurements != backup['measurements']:
                raise Refusal('restore_mismatch', 'restored row counts or content digests differ from the backup')
            record.update(restore_verified=True, measurements=measurements, manifest_sha256=file_sha(directory/'manifest.json'))
        else:
            if kind == 'orchestrator_rebuild':
                t.execute_rebuild(ns.run_id, assets)
            evidence = t.readback(ns.run_id, assets)
            verify_readback(evidence, assets, registry)
            record.update(result_verified=True, readback=evidence, measurements=t.measure(tables))
        A.emit(record)
        return record
    finally:
        t.close()


def main(kind):
    try:
        print(A.emit(operate(kind, sys.argv[1:])))
        return 0
    except Refusal as exc:
        print(A.emit(dict(schema=A.RECORD_SCHEMA, kind=kind, status='refused', code=exc.code, detail=str(exc))), file=sys.stderr)
        return 2
    except Exception as exc:
        # Driver/process errors may include a DSN or row contents; never print their text.
        print(A.emit(dict(schema=A.RECORD_SCHEMA, kind=kind, status='failed', error_class=type(exc).__name__)), file=sys.stderr)
        return 1


class Postgres:
    """Only constructed in explicit execution. Test fakes implement this narrow transport."""
    def __init__(self, env):
        import psycopg
        import psycopg.rows
        self.conn = psycopg.connect(host=env['PGHOST'], port=env['PGPORT'], dbname=env['PGDATABASE'],
            user=env['PGUSER'], password=env['PGPASSWORD'], passfile='/dev/null', connect_timeout=10,
            sslmode=env.get('PGSSLMODE', 'prefer'), row_factory=psycopg.rows.dict_row)
        self.begin_readonly()
        self.scope = None

    def begin_readonly(self):
        self.conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
        self.conn.execute("SET LOCAL TIME ZONE 'UTC'")
        self.conn.execute("SET LOCAL DateStyle = 'ISO, MDY'")
        self.conn.execute("SET LOCAL extra_float_digits = 3")
        self.conn.execute("SET LOCAL client_encoding = 'UTF8'")

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def inspect_scope(self):
        self.scope = dict(schema='ky.ops_scope/1', registry=self.query(REGISTRY_SQL), tables=self.query(TABLES_SQL))
        return self.scope

    def snapshot(self):
        return self.query('SELECT pg_export_snapshot() AS snapshot')[0]['snapshot']

    def measure(self, tables):
        out = {}
        for name in tables:
            # Stable UTF-8 JSON text, C collation, length-framed rows. Includes duplicates and NULLs.
            cursor = self.conn.execute('SELECT row_to_json(t)::text AS row FROM public."'+name+'" t ORDER BY row_to_json(t)::text COLLATE "C"')
            count, h = 0, hashlib.sha256()
            for row in cursor:
                body = row['row'].encode('utf-8')
                h.update(str(len(body)).encode()+b':'+body)
                count += 1
            out[name] = dict(rows=count, sha256=h.hexdigest())
        return out

    def empty_scratch(self):
        return not self.query("SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%' AND c.relkind IN ('r','p','v','m','S','f') LIMIT 1")

    def restored(self):
        self.conn.rollback()
        self.begin_readonly()

    def dependencies_ready(self, assets):
        indexed = {r['asset_id']: r for r in self.scope['registry']}
        deps = sorted({d for a in assets for d in indexed[a]['depends_on'] if d not in assets})
        for dep in deps:
            if not self.query("SELECT 1 FROM asset_throughput WHERE asset_id=%s AND (chart_id=%s OR chart_id IS NULL) AND state IN ('lit','service_ok')", (dep, A.CANONICAL_CHART)):
                return False
        return True

    def run_record(self, run_id):
        rows = self.query('SELECT id, chart_id::text, action, state, plan FROM build_runs WHERE id=%s', (run_id,))
        return rows[0] if rows else {}

    def execute_rebuild(self, run_id, assets):
        self.conn.rollback()
        sidecar = FLEET.parents[3]/'platform'/'python-sidecar'
        sys.path.insert(0, str(sidecar))
        from pipeline.orchestrator import runner
        # Runner db.py accepts DATABASE_URL; no other connection source is supplied by executor.
        # Pipeline diagnostics may embed driver exception text. Only the measured adapter record is public.
        level = logging.root.manager.disable
        prior_force = os.environ.get('NIRMANA_FORCE_EXECUTE')
        try:
            os.environ['NIRMANA_FORCE_EXECUTE'] = '1'
            logging.disable(sys.maxsize)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                execute_serial(runner, run_id, assets)
        finally:
            logging.disable(level)
            if prior_force is None:
                os.environ.pop('NIRMANA_FORCE_EXECUTE', None)
            else:
                os.environ['NIRMANA_FORCE_EXECUTE'] = prior_force
        self.begin_readonly()

    def readback(self, run_id, assets):
        indexed = {r['asset_id']: r for r in self.scope['registry']}
        runs = self.query('SELECT state FROM build_runs WHERE id=%s AND chart_id=%s', (run_id, A.CANONICAL_CHART))
        result = dict(state=runs[0]['state'] if runs else None, assets=[])
        census = self.query("SELECT bra.asset_id, bra.state AS run_state, t.state AS throughput_state FROM build_run_assets bra LEFT JOIN asset_throughput t ON t.asset_id=bra.asset_id AND t.chart_id=%s WHERE bra.run_id=%s ORDER BY bra.asset_id", (A.CANONICAL_CHART, run_id))
        if len(census) != len(assets) or {r['asset_id'] for r in census} != set(assets):
            raise Refusal('readback', 'the actual run census includes missing, duplicate or extra assets')
        states_by_asset = {r['asset_id']: r for r in census}
        for name in assets:
            states = [states_by_asset[name]]
            r = indexed[name]
            count_sql, integrity_sql = r.get('count_sql'), r.get('integrity_check_sql')
            if not count_sql or not integrity_sql:
                raise Refusal('detector', 'a registry count or integrity detector is missing')
            if '$1' not in count_sql:
                raise Refusal('detector', 'the registry counter is not chart-bound via its existing $1 placeholder')
            counts = self.query(count_sql.replace('$1', '%s'), (A.CANONICAL_CHART,))
            checks = self.query(integrity_sql.replace('$1', '%s'), (A.CANONICAL_CHART,) if '$1' in integrity_sql else ())
            if len(states) != 1 or len(counts) != 1 or len(checks) != 1:
                raise Refusal('detector', 'a readback detector returned ambiguous or absent evidence')
            result['assets'].append(dict(**states[0], rows=next(iter(counts[0].values())), integrity=next(iter(checks[0].values())) is True))
        return result

    def close(self):
        self.conn.rollback()
        self.conn.close()
