"""Explicit, connection-local synthetic settlement for J-4e/J-3c rehearsals.

madhav-6d ruling (2)(b), 2026-10-16: this is NEVER an L1_SETTLED receipt.
No environment switch changes production loaders; callers must opt in and use
this wrapper for the suite-owned throwaway connection. No database lifecycle,
transaction, role or chart row is changed here.
"""
from __future__ import annotations

from copy import deepcopy
import ipaddress
import os
from pathlib import Path
import re
from uuid import UUID

SOURCE = 'SYNTHETIC-REHEARSAL-ONLY'
QUALIFICATION = 'snapshot stage rehearsed on synthetic settlement'


def _target_identity(conn, job_id):
    """The harness's endpoint/server/ky.job custody proof, never name alone."""
    ci = os.environ.get('GITHUB_ACTIONS') == 'true'
    endpoint = (conn.info.host, conn.info.port)
    name = conn.info.dbname
    allowed_endpoint = endpoint == ('127.0.0.1', 55433) or (
        ci and endpoint == ('localhost', 5432))
    if (not allowed_endpoint or not re.fullmatch(
            r'(?:ky_rehearse_[a-z0-9_]+|kala_ci_[0-9a-f]{32})', name)):
        raise ValueError('synthetic settlement requires a guarded rehearsal target')
    # Query metadata only AFTER the client endpoint check, as in the harness.
    row = conn.execute("""SELECT current_database(), inet_server_addr()::text,
        inet_server_port(), oid, shobj_description(oid,'pg_database'),
        current_setting('session_replication_role')
        FROM pg_catalog.pg_database WHERE datname=current_database()""").fetchone()
    if row is None:
        raise ValueError('rehearsal target identity unavailable')
    database, raw_address, port, oid, comment, replication_role = row
    address = ipaddress.ip_interface(raw_address).ip if raw_address else None
    address = (getattr(address, 'ipv4_mapped', None) or address) if address else None
    ci_bridge = ci and address is not None and address.version == 4 and any(
        address in ipaddress.ip_network(net) for net in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))
    if database != name or port != endpoint[1] or address is None or not (address.is_loopback or ci_bridge):
        raise ValueError('connected rehearsal target identity refused')
    if replication_role != 'origin':
        raise ValueError('rehearsal target load session must be at origin')
    if comment != 'ky.job=' + job_id:
        raise ValueError('rehearsal database job ownership refused')
    return database, oid


def _job_id():
    scratch = os.environ.get('JOB_SCRATCH', '')
    if not scratch or not Path(scratch).is_absolute():
        raise ValueError('absolute JOB_SCRATCH required for rehearsal ownership')
    return Path(scratch).name


class _SyntheticSettlementConnection:
    """Transparent caller-owned connection; authority cannot leak to another one."""

    def __init__(self, conn, record, receipt, identity, job_id, *, enabled=False):
        if enabled is not True:
            raise ValueError('explicit synthetic rehearsal gate required')
        self._conn = conn
        self._record = deepcopy(record)
        self._receipt = receipt
        self._identity = identity
        self._job_id = job_id
        self._uses = 0

    def __getattr__(self, name):
        return getattr(self._conn, name)

    @property
    def synthetic_record(self):
        return deepcopy(self._record)

    def settlement(self, chart_id):
        if _target_identity(self._conn, self._job_id) != self._identity:
            raise ValueError('rehearsal database identity changed')
        if str(chart_id) != self._record['chart_id']:
            raise ValueError('synthetic settlement belongs to another chart')
        # Assert the receipt at consumption as well, so caller edits cannot
        # strip synthetic provenance or promote rehearsal into acceptance.
        self._uses += 1
        self._receipt.update(dasha_settlement=self.synthetic_record,
                             synthetic_settlement_used=True, production_acceptance=False)
        return self.synthetic_record

    def run_substep(self, writer, ctx, step):
        """Call the real substep and qualify its snapshot only on observed use.

        The harness retains transaction/savepoint ownership. Dry-run/no-op
        snapshots that never consume synthetic authority earn no qualification.
        The stage outcome is independent from production acceptance.
        """
        if ctx.db_conn is not self:
            raise ValueError('rehearsal context must use its guarded connection')
        before = self._uses
        outcome = 'failed'
        try:
            result = writer.run_substep(ctx, step)
            outcome = 'completed'
            return result
        finally:
            if step.key == 'snapshot' and self._uses > before:
                self._receipt.update(snapshot_settlement_qualification=QUALIFICATION,
                                     snapshot_stage_outcome=outcome, production_acceptance=False)


def synthetic_settlement_connection(conn, *, chart_id, manifest_sha256, receipt, enabled=False):
    """Bind the restored bundle's single Vimśottarī build, without fabricating a line.

    ``enabled=True`` is the explicit test/rehearsal flag. The suite must first
    restore and compare its approved bundle and tag its newly created database
    with COMMENT ON DATABASE ... IS 'ky.job=<JOB_SCRATCH basename>'. The manifest
    digest is custody metadata, not independent approval or a canonical claim.
    Keep ``receipt`` in the rehearsal's durable evidence/manifest. The raw
    connection and both governed settlement loaders retain their behavior.
    """
    if enabled is not True:
        raise ValueError('explicit synthetic rehearsal gate required')
    if not isinstance(receipt, dict):
        raise ValueError('mutable rehearsal receipt required')
    if not isinstance(manifest_sha256, str) or re.fullmatch(r'[0-9a-f]{64}', manifest_sha256) is None:
        raise ValueError('restored bundle manifest SHA-256 required')
    chart_id = str(UUID(str(chart_id)))
    job_id = _job_id()
    identity = _target_identity(conn, job_id)
    from services.gochara_kernel.dasha_read import assert_single_pinned_build
    builds = assert_single_pinned_build(conn, chart_id)
    if len(builds) != 1:
        raise ValueError('synthetic settlement requires one non-NULL restored Vimshottari build')
    build = str(UUID(builds[0]))
    record = dict(schema='gochara_synthetic_dasha_settlement/1', synthetic=True,
                  chart_id=chart_id, run_id=build,
                  provenance=dict(source=SOURCE, manifest_sha256=manifest_sha256,
                                  database=identity[0], database_oid=identity[1], job_id=job_id))
    receipt.update(dasha_settlement=deepcopy(record), snapshot_settlement_qualification=None,
                   synthetic_settlement_used=False, snapshot_stage_outcome=None, production_acceptance=False)
    return _SyntheticSettlementConnection(conn, record, receipt, identity, job_id, enabled=enabled)


def settlement_for_connection(conn, chart_id, governed_loader):
    """Ordinary targets always use the caller's unchanged governed loader."""
    if isinstance(conn, _SyntheticSettlementConnection):
        return conn.settlement(chart_id)
    return governed_loader(chart_id)


def profiles_scope(conn, *, profile_rows_loaded=None, profile_row_queries=None):
    """Measure row scope, not schema-restore scans of an empty profiles table.

    The harness supplies its loader/SQL census, including explicit SELECTs that
    return no rows. Missing census remains honestly unmeasured (§N.7.6); tuple
    counters alone cannot detect such queries. Counter reads touch pg_catalog
    only. Call after the suite has flushed its session statistics; no profile
    row query is issued here. DDL scan counts are retained as diagnostic data.
    """
    _target_identity(conn, _job_id())
    row = conn.execute('''SELECT seq_scan, coalesce(idx_scan,0), seq_tup_read,
        coalesce(idx_tup_fetch,0) FROM pg_catalog.pg_stat_all_tables
        WHERE schemaname='public' AND relname='profiles' ''').fetchone()
    measured = (row is not None and all(type(n) is int and n >= 0
                for n in (profile_rows_loaded, profile_row_queries)))
    tuple_reads = None if row is None else row[2] + row[3]
    violation = ((tuple_reads is not None and tuple_reads > 0)
                 or any(type(n) is int and n > 0 for n in (profile_rows_loaded, profile_row_queries)))
    passed = False if violation else (True if measured else None)
    return dict(schema='ky.profiles_scope/1', passed=passed,
                profile_rows_loaded=profile_rows_loaded, profile_row_queries=profile_row_queries,
                profile_tuple_reads=tuple_reads, profile_table_scans=None if row is None else row[0] + row[1],
                production_acceptance=False)
