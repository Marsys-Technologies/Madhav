"""J-5s: all 26 real-sky classes through separate verification and approved seal.

Synthetic natal/dasha fixture inputs; real pinned Swiss transit corpus; unchanged
1998–2085 substrate, two-day record horizon. This is not A5.7/B5.4 qualification.
No production transport is exercised. Every fixture database is dropped inline.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from pipeline.orchestrator import verification_job as entry, seal_job as seal_entry
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import seal_brief as sb, seal_flow as sf, verification_job as vj
from .test_a53_inventory import CHART_ID, create_am5_database, drop_am5_database
from .test_a53_verification_job import login, PASSWORD
from .conftest import EPHE_PATH, _PROBLEMS

GEN = '5.0'
COMMIT = 'a' * 40
EXECUTION = 'local-j5s-full-class-verifier'
RUN, ATTEMPT = 424242, 1
HERE = Path(__file__).parent


def _counts(conn):
    return {t: conn.execute(f'SELECT count(*) FROM public.{t}').fetchone()[0]
            for t in vj.VERIFICATION_TABLES}


@pytest.fixture(scope='module')
def candidate(tmp_path_factory):
    from datetime import datetime, timezone
    from functools import lru_cache
    if _PROBLEMS:
        pytest.skip('NOT_RUN: pinned Swiss corpus unavailable: ' + '; '.join(_PROBLEMS))
    # Migration 1305 makes the search-input snapshot self-contained (it copies the L1 rows it consumed);
    # seal_brief refuses a first seal on the legacy ids-only shape (snapshot_without_copy), so the
    # candidate must be built on the post-1305 database, as production is.
    admin, name, dsn = create_am5_database('j5s_full', faithful=True, apply_1305=True)
    conn = None
    started = time.monotonic()
    from services.gochara_kernel import implementation_registry as registry
    old_lock = registry.LOCK_PATH
    real_calc = writer_mod.calc_sidereal_lon
    # Generated output is test-only and lives in pytest's scratch directory.
    # The branch's machine-owned lock remains untouched (A5 D-33).
    try:
        registry.LOCK_PATH = tmp_path_factory.mktemp('j5s-generated') / old_lock.name
        registry.write(registry.LOCK_PATH)
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
        w = SimpleNamespace(conn=conn, dsn=dsn)
        # Memoize exact real probes only; every cached value is computed by the
        # production Swiss function against the pinned corpus. No sky stand-in.
        writer_mod.calc_sidereal_lon = lru_cache(maxsize=262144)(real_calc)
        substrate_cache = os.environ.get('J5S_SUBSTRATE_CACHE')
        if substrate_cache:
            cache = Path(substrate_cache)
            assert hashlib.sha256(cache.read_bytes()).hexdigest() == Path(str(cache)+'.sha256').read_text().strip()
            subprocess.run([os.environ['J5S_PG_RESTORE'], '--clean', '--if-exists', '--single-transaction',
                            '--exit-on-error', '--dbname', dsn, str(cache)], check=True, capture_output=True, timeout=120)
            from services.gochara_kernel import input_vector as iv, input_vector_verifier as ivv
            old_vector = conn.execute('SELECT input_generation_vector FROM public.kala_gochara_publication').fetchone()[0]
            assert old_vector['implementation']['geometry'] == ivv.module_digests(iv.IMPLEMENTATION_MODULES)['geometry']
        # The fixture's explicit L1 read stand-ins; no source asset is changed.
        conn.execute((HERE / 'fixtures/l1_read_stand_in_grants.sql').read_text())
        conn.execute('GRANT SELECT ON public.chart_facts, public.chart_dashas, public.bg_transit_rules, '
                     'public.charts, public._migrations_applied TO data_plane_builder, gochara_sealer')
        writer_mod.RuleRegistryStore(conn).seed()
        writer = writer_mod.GocharaV5Writer()
        horizon = (datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 1, 3, tzinfo=timezone.utc))
        with login(w, 'data_plane_builder') as builder:
            ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id='j5s-full-class-local', db_conn=builder,
                              dry_run=False, config={'chart_id': CHART_ID, 'gochara_v5_final_rules': False, 'horizon': horizon, 'ephe_path': EPHE_PATH})
            for step in writer.plan_substeps(ctx):
                if step.key == writer_mod.RULES_SUBSTEP:
                    continue  # the global catalogue is provisioned by the fixture owner
                if substrate_cache and step.key.startswith(writer_mod.BODY_SUBSTEP_PREFIX):
                    continue  # exact geometry implementation and hash-bound real substrate reused
                with builder.transaction():
                    writer.run_substep(ctx, step)
                print(f'J5S build {step.key} ({time.monotonic() - started:.1f}s)', flush=True)
        assert _counts(conn) == {t: 0 for t in vj.VERIFICATION_TABLES}
        classes = [r[0] for r in conn.execute('SELECT event_class FROM public.ka_gochara_search_inventory ORDER BY 1')]
        assert classes == sorted(writer_mod.SCORED_CLASSES) and len(classes) == 26
        w.expected_manifest_id = conn.execute('SELECT manifest_id::text FROM public.kala_gochara_publication '
                                              'WHERE chart_id=%s AND generation=%s', (CHART_ID, GEN)).fetchone()[0]
        # Optional forensic capture happens BEFORE fixture teardown and lifecycle mutation.
        # This is an output only; CI always builds the candidate from real substeps.
        export = os.environ.get('J5S_CANDIDATE_EXPORT')
        if export:
            client = os.environ.get('J5S_PG_DUMP', 'pg_dump')
            subprocess.run([client, '--format=custom', '--file', export, '--dbname', dsn], check=True,
                           capture_output=True, timeout=120)
            Path(export + '.sha256').write_text(hashlib.sha256(Path(export).read_bytes()).hexdigest() + '\n')
        yield w
    finally:
        registry.LOCK_PATH = old_lock
        writer_mod.calc_sidereal_lon = real_calc
        if conn is not None:
            conn.close()
        drop_am5_database(admin, name)


def _verify(w):
    with login(w, 'gochara_verifier') as verifier:
        return vj.run(verifier, chart_id=CHART_ID, generation=GEN, **entry._build_kwargs(verifier, EPHE_PATH))


def _unsealed(conn):
    assert conn.execute('SELECT status FROM public.kala_gochara_publication').fetchone()[0] == 'candidate'
    for table in ('ka_gochara_generation_seal', 'ka_gochara_seal_approval'):
        assert conn.execute(f'SELECT count(*) FROM public.{table}').fetchone()[0] == 0


def test_full_class_builder_denial_corruption_and_manifest_job_bound_seal(candidate, monkeypatch, capsys, tmp_path):
    w, conn = candidate, candidate.conn
    with login(w, 'data_plane_builder') as builder:
        for table in vj.VERIFIER_WRITE_TABLES:
            with pytest.raises(psycopg.errors.InsufficientPrivilege) as denied:
                builder.execute(f'INSERT INTO public.{table} DEFAULT VALUES')
            assert denied.value.sqlstate == '42501'
    assert _counts(conn) == {t: 0 for t in vj.VERIFICATION_TABLES}
    # Invoke the actual independent job entry point, with only its own LOGIN DSN.
    with login(w, 'gochara_verifier'):
        monkeypatch.setenv(entry.ENV_URL, make_conninfo(w.dsn, user='gochara_verifier', password=PASSWORD))
        assert entry.main(['--chart', CHART_ID, '--generation', GEN]) == 0
        report = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert report['status'] == 'VERIFIED' and report['gate'] == []
    assert report['identity']['login'] == 'gochara_verifier'
    assert set(report['classes']) == set(writer_mod.SCORED_CLASSES)
    included = set(conn.execute("SELECT event_class, path_id FROM public.ka_gochara_search_path_pin "
                                "WHERE disposition = 'included'").fetchall())
    attested = set(conn.execute("SELECT event_class, path_id FROM public.ka_gochara_eval_window_verification "
                               "WHERE status = 'VERIFIED'").fetchall())
    assert included and included == attested
    assert _counts(conn)['ka_gochara_search_inventory_verification'] == 26
    before = _counts(conn)
    row = conn.execute("SELECT window_id, interval, event_class FROM public.ka_gochara_eval_window "
                       "WHERE upper(interval)-lower(interval) > interval '2 seconds' "
                       "AND (peak_instant IS NULL OR peak_instant >= lower(interval)+interval '1 second') "
                       "ORDER BY window_id LIMIT 1").fetchone()
    assert row is not None
    wid, interval, cls = row
    with conn.transaction():
        vj.take_locks(conn, CHART_ID)
        conn.execute("UPDATE public.ka_gochara_eval_window SET interval = "
                     "tstzrange(lower(interval)+interval '1 second',upper(interval),'[)') WHERE window_id=%s", (wid,))
    bad = _verify(w)
    assert bad['status'] == 'DISAGREE' and bad['exit_code'] == 3 and bad['gate']
    assert bad['classes'][cls]['status'] == 'DISAGREE'
    assert _counts(conn) == before
    _unsealed(conn)
    with conn.transaction():
        vj.take_locks(conn, CHART_ID)
        conn.execute('UPDATE public.ka_gochara_eval_window SET interval=%s WHERE window_id=%s', (interval, wid))
    assert _verify(w)['status'] == 'VERIFIED'
    monkeypatch.setenv('GOCHARA_RUNNER_COMMIT', COMMIT)
    monkeypatch.setenv('GOCHARA_RUNNER_IMAGE_DIGEST', 'sha256:' + 'b' * 64)
    monkeypatch.setenv('CLOUD_RUN_EXECUTION', EXECUTION)
    # One missing included grain must prevent a full-generation brief.
    victim_class, victim_path = sorted(included)[0]
    with conn.transaction():
        vj.take_locks(conn, CHART_ID)
        conn.execute('DELETE FROM public.ka_gochara_eval_window_verification WHERE event_class=%s AND path_id=%s',
                     (victim_class, victim_path))
    with login(w, 'gochara_verifier') as verifier:
        with pytest.raises(sb.BriefRefused):
            with verifier.transaction():
                sb.brief(verifier, CHART_ID, GEN, sealing_commit=COMMIT)
    assert _verify(w)['status'] == 'VERIFIED'
    with login(w, 'gochara_verifier') as verifier:
        with verifier.transaction():
            brief = sb.brief(verifier, CHART_ID, GEN, sealing_commit=COMMIT)
            persisted = sb.persist_brief(verifier, brief, producer=sb.producer_identity())
    assert persisted['manifest_id'] == w.expected_manifest_id
    assert len(brief['payload']['classes']) == 26
    assert {c['event_class'] for c in brief['payload']['classes']} == set(writer_mod.SCORED_CLASSES)
    assert sb.reassemble_chunks(list(sb.brief_chunk_lines(sb.brief_bytes(brief), brief['sha256'], 4096))) == sb.brief_bytes(brief)
    import sys
    sys.path.insert(0, str(HERE.resolve().parents[3] / 'scripts'))
    import gochara_seal_brief_check as workflow_check
    raw = sb.brief_bytes(brief)
    compact = dict(status='BRIEFED', contract_version=sb.TRANSPORT_CONTRACT, sha256=brief['sha256'],
        persisted=persisted, producer=sb.producer_identity(), brief_bytes=len(raw), brief_chunks=True, brief_file=None)
    assert workflow_check.check(raw, compact, chart_id=CHART_ID, generation=GEN, sealing_commit=COMMIT) == brief['sha256']
    approval = sf.parse_approval(json.dumps(dict(schema='seal_approval/2', brief_digest=brief['sha256'],
        brief_id=persisted['brief_id'], producer_execution_id=EXECUTION, run_id=RUN, run_attempt=ATTEMPT,
        approver_login='local-rehearsal', approved_by_note='ruling:local-j5s; actor:local-rehearsal')))
    with login(w, 'gochara_sealer') as sealer:
        for changes in ({'run_id': RUN + 1}, {'run_attempt': 2}, {'producer_execution_id': 'foreign-execution'},
                        {'brief_id': persisted['brief_id'] + 1}, {'brief_digest': '0' * 64}):
            with pytest.raises((sf.SealRefused, sb.ApprovalMismatch)):
                sf.execute_seal(sealer, chart_id=CHART_ID, generation=GEN, approval={**approval, **changes},
                                run_id=RUN, run_attempt=ATTEMPT, sealing_commit=COMMIT, triggering_actor='local-rehearsal')
            _unsealed(conn)
        mid = w.expected_manifest_id
        assert sb.persisted_brief_problem(sealer, CHART_ID, GEN, '00000000-0000-0000-0000-000000000000',
            brief['sha256'], brief_id=persisted['brief_id'], sealing_commit=COMMIT, execution_id=EXECUTION) is not None
        # An otherwise valid candidate changed after approval is a different payload.
        from psycopg.types.json import Jsonb
        vector = conn.execute('SELECT input_generation_vector FROM public.kala_gochara_publication').fetchone()[0]
        try:
            with conn.transaction():
                vj.take_locks(conn, CHART_ID)
                conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = "
                             "input_generation_vector || '{\"j5s_changed_after_approval\":true}'::jsonb")
            with pytest.raises(sb.ApprovalMismatch):
                sf.execute_seal(sealer, chart_id=CHART_ID, generation=GEN, approval=approval,
                                run_id=RUN, run_attempt=ATTEMPT, sealing_commit=COMMIT, triggering_actor='local-rehearsal')
            _unsealed(conn)
        finally:
            with conn.transaction():
                vj.take_locks(conn, CHART_ID)
                conn.execute('UPDATE public.kala_gochara_publication SET input_generation_vector=%s', (Jsonb(vector),))
        approval_path = tmp_path / 'approval.json'
        approval_path.write_text(json.dumps(approval))
        monkeypatch.setenv(seal_entry.ENV_URL, make_conninfo(w.dsn, user='gochara_sealer', password=PASSWORD))
        monkeypatch.setenv('GITHUB_RUN_ID', str(RUN))
        monkeypatch.setenv('GITHUB_RUN_ATTEMPT', str(ATTEMPT))
        monkeypatch.setenv('GOCHARA_SEALING_COMMIT', COMMIT)
        monkeypatch.setenv('GITHUB_TRIGGERING_ACTOR', 'local-rehearsal')
        assert seal_entry.main(['--chart', CHART_ID, '--generation', GEN, '--approval-file', str(approval_path)]) == 0
        outcome = json.loads(capsys.readouterr().out.splitlines()[-1])
        assert outcome['status'] == 'SEALED'
    # Independent SQL observation, not a process exit: all four manifests, both digests,
    # the verifier execution, database-attested principals, exact run/attempt/commit.
    observed = conn.execute('SELECT p.manifest_id::text,s.manifest_id::text,a.manifest_id::text,b.manifest_id::text, '
        'a.brief_digest,b.brief_digest,a.producer_execution_id,b.execution_id,b.produced_by,a.sealed_by, '
        'a.run_id,a.run_attempt,a.workflow_commit FROM public.kala_gochara_publication p '
        'JOIN public.ka_gochara_generation_seal s USING(chart_id,generation) '
        'JOIN public.ka_gochara_seal_approval a USING(chart_id,generation) '
        'JOIN public.ka_gochara_seal_brief b ON b.brief_id=a.brief_id '
        'WHERE p.chart_id=%s AND p.generation=%s', (CHART_ID, GEN)).fetchone()
    assert observed == (mid, mid, mid, mid, brief['sha256'], brief['sha256'], EXECUTION, EXECUTION,
                        'gochara_verifier', 'gochara_sealer', RUN, ATTEMPT, COMMIT)
    assert outcome['manifest_id'] == mid
    assert conn.execute('SELECT public.ka_gochara_generation_is_sealed(%s,%s)', (CHART_ID, GEN)).fetchone()[0]
    print(json.dumps({'local_only': True, 'classes': 26, 'included_grains': len(included), 'readback': observed}))
