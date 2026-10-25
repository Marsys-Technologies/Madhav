"""TR-26 G-completion (SR-J4E-HORIZON-BASIS, SR-J4E-POSTRUN-READBACKS) and the resume-refuses oracle (SR-RESUME-NOW (3)).

TR #2 bypassed the real build entry and never staged a century config, so the century's completion gate read FALSE on `horizon_basis` (an unmarked century manifest carried no pin) and NULL on
`digests_equal_dry_run` (no receipt).  The detectors below are the gate's own predicates (completion_gate.horizon_basis / digests_equal_dry_run, teardown_gate.horizon_basis_if_manifest) re-run on recorded RAW
readbacks.  One oracle per distinct claim; the single planted reversion is named in each docstring; every planted case reads FALSE (or NOT_EVALUATED where the evidence is absent), never PASS."""
import copy
import json
import re
import sys
import uuid
from pathlib import Path

import pytest

import completion as cp
import fixtures as fx
import gates
import trial_slice as ts
from gates import FAIL, NOT_EVALUATED, PASS

RULED = ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]
EXPECTED = "febf7cb3430d341050ceac53c09234a036b170dfbc8c17ee4f914567844deec6"
RUN = "3894cf52-6dcb-413f-b527-feb56d350a58"
PIN = {"schema": "horizon_basis/1", "rule": "ruled_scope+birth_centenary", "basis": "ruled_horizon"}


def cell(**over):
    base = {"status": "candidate", "test_slice": None, "stored_scope": "stored_non_moon", "horizon_basis": PIN,
            "manifest_horizon": '["1998-01-01 05:30:00+05:30","2084-02-05 05:30:00+05:30")'}
    base.update(over)
    return json.dumps(base)


def receipt(**over):
    base = {"asset_id": "ka_gochara_v5", "build_id": RUN, "code_digest": EXPECTED, "partition_key": "__whole_asset__", "receipt_state": "unknown"}
    base.update(over)
    return base


TERMINAL = json.dumps({"assets": json.dumps([{"asset_id": "ka_gochara_v5", "state": "complete", "disposition": "build", "error": None}]),
                       "throughput": json.dumps([{"state": "lit", "last_error": None}])})


# ── (a) horizon_basis ───────────────────────────────────────────────────────────────────────────────────────────

def test_a_pinned_century_shaped_manifest_reads_true():
    assert cp.horizon_basis_check(cell(), RULED)[0] is True


def test_a_century_manifest_without_the_pin_reads_false_the_shape_the_century_run_actually_read():
    """The incident: status candidate, stored_scope stored_non_moon, test_slice null, horizon_basis null, the ruled horizon (readback 31-horizon-basis, J-4f).  Reversion: drop the `not pin` test in horizon_basis_check."""
    state, why = cp.horizon_basis_check(cell(horizon_basis=None), RULED)
    assert state is False and "no horizon_basis pin" in why


def test_a_marked_test_slice_manifest_cannot_satisfy_the_century_check_even_with_a_pin():
    """J-3d's measuring slice carried a pin; a century check that accepted it would be satisfied by the wrong run shape.  Reversion: drop the stored_scope/test_slice discriminator."""
    assert cp.horizon_basis_check(cell(test_slice={"run": "all_classes_full"}), RULED)[0] is False
    assert cp.horizon_basis_check(cell(stored_scope="test_slice"), RULED)[0] is False


def test_a_wrong_horizon_a_non_candidate_status_and_a_non_object_pin_each_read_false():
    """Reversion: compare only the truthiness of the pin."""
    assert cp.horizon_basis_check(cell(manifest_horizon='["1998-01-01","2050-01-01")'), RULED)[0] is False
    assert cp.horizon_basis_check(cell(status="sealed"), RULED)[0] is False
    assert cp.horizon_basis_check(cell(horizon_basis="yes"), RULED)[0] is False
    assert cp.horizon_basis_check(cell(horizon_basis={"schema": "other/1"}), RULED)[0] is False


def test_unreadable_or_unreferenced_evidence_is_none_never_true():
    assert cp.horizon_basis_check(None, RULED)[0] is None
    assert cp.horizon_basis_check("not json", RULED)[0] is None
    assert cp.horizon_basis_check(cell(), None)[0] is None


# ── (b) provenance ──────────────────────────────────────────────────────────────────────────────────────────────

def test_a_receipt_of_the_run_with_the_expected_digest_reads_true():
    assert cp.provenance_check(RUN, EXPECTED, [receipt()], True)[0] is True


def test_a_completed_run_with_no_receipt_reads_false_that_is_what_bypassing_the_real_entry_looks_like():
    """TR #2's shape: substeps driven directly, no run_asset, the asset 'completed' but no receipt.  Reversion: read an empty list as None (the gate's NULL) instead of FALSE."""
    for none in ([], None):
        state, why = cp.provenance_check(RUN, EXPECTED, none, True)
        assert state is False and "no provenance receipt" in why


def test_a_receipt_with_another_code_digest_reads_false():
    """The planted mismatch.  Reversion: drop the code_digest comparison."""
    state, why = cp.provenance_check(RUN, EXPECTED, [receipt(code_digest="0" * 64)], True)
    assert state is False and "code_digest" in why


def test_a_stale_or_foreign_receipt_reads_false_even_beside_a_good_one():
    """The receipt table keeps the last success per asset: a receipt of another build is the stale-receipt hazard.  Reversion: drop the build_id binding."""
    assert cp.provenance_check(RUN, EXPECTED, [receipt(build_id=str(uuid.uuid4()))], True)[0] is False
    assert cp.provenance_check(RUN, EXPECTED, [receipt(), receipt(build_id=str(uuid.uuid4()))], True)[0] is False


def test_a_run_that_did_not_complete_through_the_entry_or_a_missing_expected_digest_is_none():
    assert cp.provenance_check(RUN, EXPECTED, [receipt()], False)[0] is None
    assert cp.provenance_check(RUN, EXPECTED, [receipt()], None)[0] is None
    assert cp.provenance_check(RUN, None, [receipt()], True)[0] is None


def test_terminal_evidence_must_show_the_asset_complete_and_the_throughput_lit():
    assert cp.terminal_ok(TERMINAL)[0] is True
    bad = json.dumps({"assets": json.dumps([{"asset_id": "ka_gochara_v5", "state": "error", "disposition": "build", "error": "x"}]), "throughput": json.dumps([{"state": "lit", "last_error": None}])})
    assert cp.terminal_ok(bad)[0] is False
    assert cp.terminal_ok(None)[0] is None


# ── the gate (G-8) reads the RAW record ─────────────────────────────────────────────────────────────────────────

def record(**over):
    rec = {"schema": cp.SCHEMA, "horizon_basis": {"readback": cell()},
           "provenance": {"run_id": RUN, "expected_code_digest": EXPECTED, "receipts": [receipt()], "terminal": json.loads(TERMINAL)}}
    rec.update(over)
    return rec


def profile():
    return json.loads((fx.HARNESS / "gate_profile.tr26.json").read_text())


def rep(rec):
    r = fx.report()
    r["completion"] = rec
    return r


def checks(rec):
    return gates.g8_completion_checks(rep(rec), profile())


def test_the_tr26_profile_requires_the_completion_checks_and_both_resume_dimensions():
    p = profile()
    assert p["completion"]["required"] is True and p["completion"]["entry"] == "pipeline.orchestrator.asset_runner.run_asset"
    assert p["determinism"]["kill_resume"]["refusal_dimensions"] == ["source", "library"]


def test_g8_passes_both_completion_checks_on_a_good_record():
    assert [c["status"] for c in checks(record())] == [PASS, PASS]


def test_g8_fails_the_horizon_check_for_a_manifest_without_the_pin_and_reads_the_trials_own_horizon():
    """The planted manifest.  Reversion: skip the pin test (horizon_basis_check) -> PASS.  The reference horizon is the TRIAL REPORT's, so a manifest of another horizon fails even if the probe recorded its own."""
    c = checks(record(horizon_basis={"readback": cell(horizon_basis=None), "ruled_horizon": RULED}))
    assert c[0]["status"] == FAIL and c[1]["status"] == PASS
    other = rep(record())
    other["horizon"] = {"start": "1998-01-01T00:00:00+00:00", "end": "2090-01-01T00:00:00+00:00"}
    assert gates.g8_completion_checks(other, profile())[0]["status"] == FAIL


def test_g8_fails_the_provenance_check_for_a_wrong_digest_and_for_a_bypassed_entry():
    """Reversion: judge the probe's own `state` field instead of the raw receipts (the record here carries none and still fails)."""
    bad = record()
    bad["provenance"]["receipts"] = [receipt(code_digest="1" * 64)]
    assert checks(bad)[1]["status"] == FAIL
    none = record()
    none["provenance"]["receipts"] = None
    assert checks(none)[1]["status"] == FAIL
    forged = record()
    forged["provenance"]["receipts"] = [receipt(code_digest="1" * 64)]
    forged["provenance"]["state"] = True
    forged["horizon_basis"]["state"] = True
    assert [c["status"] for c in checks(forged)] == [PASS, FAIL]


def test_g8_is_not_evaluated_without_a_record_a_readback_or_a_real_entry_run_and_adds_nothing_without_the_profile_switch():
    assert [c["status"] for c in gates.g8_completion_checks(fx.report(), profile())] == [NOT_EVALUATED, NOT_EVALUATED]
    assert checks(record(horizon_basis={}))[0]["status"] == NOT_EVALUATED
    assert checks(record(provenance={}))[1]["status"] == NOT_EVALUATED
    p = profile()
    del p["completion"]
    assert gates.g8_completion_checks(rep(record()), p) == []


def test_the_completion_checks_roll_into_g8_through_evaluate():
    """Reversion: do not append g8_completion_checks in evaluate -> the gate never sees an unpinned manifest."""
    table = ts.load_decision_table(None)
    base, second = fx.baseline(), fx.report()
    r = fx.report()
    r["completion"] = record(horizon_basis={"readback": cell(horizon_basis=None)})
    prof = fx.profile()
    prof["completion"] = {"required": True}
    v = gates.evaluate(r, base, prof, second_report=second, decision_table=table)
    g8 = v["gates"]["G-8"]
    assert any(c["status"] == FAIL and "horizon_basis" in c["claim"] for c in g8["checks"]) and g8["status"] == FAIL


# ── the SQL the probe reads with is the pack's ──────────────────────────────────────────────────────────────────

PACK_SQL = Path("/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/packs/W3-v2.0/PACK/century/sql")


@pytest.mark.skipif(not PACK_SQL.is_dir(), reason="the W3 pack is not on this machine")
def test_the_horizon_basis_query_is_the_packs_modulo_the_pinned_literals():
    pack = " ".join((PACK_SQL / "w5-j4e-horizon-basis.sql").read_text().split())
    mine = " ".join(cp.HORIZON_BASIS_SQL.split())
    pack = pack.replace("chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND generation='@PIN:generation@'", "chart_id=%s AND generation=%s")
    assert mine + ";" == pack or mine == pack.rstrip(";")


@pytest.mark.skipif(not PACK_SQL.is_dir(), reason="the W3 pack is not on this machine")
def test_the_receipts_query_is_the_terminal_queries_receipts_subselect():
    terminal = " ".join((PACK_SQL / "w5-j4e-terminal.sql").read_text().split())
    sub = re.search(r"\(SELECT jsonb_agg\(to_jsonb\(p\) ORDER BY p\.build_id\) FROM asset_provenance_receipts p WHERE p\.chart_id=r\.chart_id AND p\.asset_id='ka_gochara_v5'\)", terminal)
    assert sub, "the pack's terminal query no longer has the receipts sub-select this probe mirrors"
    assert "FROM asset_provenance_receipts p WHERE p.chart_id=%s AND p.asset_id=%s" in " ".join(cp.RECEIPTS_SQL.split())


# ── the real build entry, over the production table definitions ─────────────────────────────────────────────────

ADMIN = "postgresql://postgres@127.0.0.1:55433/postgres"
SCHEMA_SQL = ts.EXPORT / "schema.sql"
STUB = "tr26_probe_stub"
STUB_CHART = "00000000-0000-4000-8000-0000000000c1"


@pytest.fixture(scope="module")
def orch_db():
    psycopg = pytest.importorskip("psycopg")
    if not SCHEMA_SQL.is_file():
        pytest.skip("the approved canonical-L1 export (production table definitions) is not on this machine")
    try:
        admin = psycopg.connect(ADMIN, autocommit=True, connect_timeout=3)
    except Exception:                                                                    # noqa: BLE001
        pytest.skip("the local lane cluster 127.0.0.1:55433 is not reachable")
    name = "ky_t26c_" + uuid.uuid4().hex[:8]
    admin.execute(f'CREATE DATABASE "{name}"')
    admin.execute(f"COMMENT ON DATABASE \"{name}\" IS 'ky.job=tr26-completion-tests'")
    try:
        with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{name}", autocommit=True) as c:
            for stmt in cp.orchestrator_ddl(SCHEMA_SQL.read_text()):
                c.execute(stmt)
            c.execute("INSERT INTO charts (id, chart_id, name, birth_date, birth_time, birth_place, birth_lat, birth_lng, timezone_id) VALUES (%s, %s, 'fixture', DATE '2000-01-01', TIME '12:00', 'fixture', 0, 0, 'UTC')",
                      (STUB_CHART, STUB_CHART))
            cp.registry_row(c, STUB, has_substeps=False)
        yield name
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')                  # only the database this fixture created
        admin.close()


def test_the_production_table_definitions_are_extracted_once_each_with_the_receipts_conflict_target(orch_db):
    import psycopg
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{orch_db}", autocommit=True) as c:
        have = {r[0] for r in c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")}
        assert set(cp.ORCH_TABLES) <= have
        uniq = c.execute("SELECT count(*) FROM pg_indexes WHERE tablename='asset_provenance_receipts' AND indexdef LIKE '%UNIQUE%(asset_id, scope_key, partition_key)%'").fetchone()[0]
        assert uniq == 1                                                    # the ON CONFLICT target persist_successful_receipt names
    with pytest.raises(ValueError):
        cp.orchestrator_ddl("CREATE TABLE public.charts (\n    a int\n);\n", ("charts", "build_runs"))


def stub_writer():
    """A light single-shot writer standing in for ka_gochara_v5: the claim under test is the ENTRY and its receipt, not the writer."""
    from pipeline.orchestrator.writers import WriterBase, WriterResult

    class StubWriter(WriterBase):
        asset_id = STUB

        def run(self, ctx):
            return WriterResult(asset_id=STUB, rows_inserted=1)
    return StubWriter


def staged_run(c, triggered_by="tr26-completion-test"):
    manifest = {"version": "nirmana-run-manifest/v1", "assets": [{"asset_id": STUB, "expected_code_digest": "a" * 64}]}
    plan = {"version": "nirmana-run-manifest/v1"}
    rid = str(uuid.uuid4())
    c.execute("INSERT INTO build_runs (id, chart_id, scope, scope_target, action, state, plan, triggered_by, plan_manifest, plan_manifest_digest) VALUES (%s,%s,'asset',%s,'rebuild','running',%s::jsonb,%s,%s::jsonb,%s)",
              (rid, STUB_CHART, STUB, json.dumps(plan), triggered_by, json.dumps(manifest), cp.manifest_digest(manifest)))
    return rid


def read_back(cur, rid):
    cur.execute(cp.RECEIPTS_SQL.replace("p.chart_id=%s AND p.asset_id=%s", "p.chart_id=%s AND p.asset_id=%s"), (STUB_CHART, STUB))
    receipts = next(iter(cur.fetchone().values()))
    cur.execute(cp.TERMINAL_SQL, (rid, STUB_CHART, STUB))
    row = cur.fetchone()
    return json.loads(receipts) if receipts else None, {"assets": row["assets"], "throughput": row["throughput"]}


def test_a_build_through_run_asset_writes_the_receipt_the_check_reads_true_and_a_bypass_reads_false(orch_db, monkeypatch):
    """The claim TR #2 could not make.  Real: `asset_runner.run_asset` -> `_run_data_writer` success path -> `asset_provenance_receipts` (production DDL).  Bypass (TR #2's shape): the same writer driven
    directly, the asset marked complete by hand, NO entry -> no receipt -> FALSE.  Reversion: make the probe call the writer's run() directly instead of run_asset -> the first assertion fails."""
    import psycopg
    from psycopg.rows import dict_row
    from pipeline.orchestrator import asset_runner
    from pipeline.orchestrator.writers import ContextSpec
    stub_cls = stub_writer()
    monkeypatch.setattr(asset_runner, "get_writer", lambda asset_id: stub_cls if asset_id == STUB else None)
    monkeypatch.setattr(asset_runner, "discover_all", lambda: None)
    monkeypatch.setattr(asset_runner, "get_writer_source_hash", lambda asset_id: EXPECTED)
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{orch_db}", row_factory=dict_row) as conn:
        cur = conn.cursor()
        rid = staged_run(conn)
        conn.commit()
        asset_runner.run_asset(conn, cur, rid, STUB_CHART, STUB, 0, declared_deps=[], natural_key_partition=None, has_cowriters=False)
        conn.commit()
        receipts, terminal = read_back(cur, rid)
        done = cp.terminal_ok(terminal, STUB)
        assert done[0] is True, done
        assert cp.provenance_check(rid, EXPECTED, receipts, done[0])[0] is True and receipts[0]["build_id"] == rid
        # planted mismatch on the REAL receipt: another expected digest
        assert cp.provenance_check(rid, "b" * 64, receipts, True)[0] is False
        # the bypass: a second run whose asset the harness marks complete by hand, with the receipts of this chart/asset wiped first (a fresh database)
        cur.execute("DELETE FROM asset_provenance_receipts")
        cur.execute("UPDATE build_runs SET state='completed' WHERE id=%s", (rid,))        # production allows one active run per chart (build_runs_one_active_per_chart_idx)
        rid2 = staged_run(conn)
        ctx = ContextSpec(asset_id=STUB, build_id=rid2, db_conn=conn, config={"chart_id": STUB_CHART})
        stub_cls().run(ctx)
        cur.execute("INSERT INTO build_run_assets (run_id, asset_id, position, state, disposition) VALUES (%s,%s,0,'complete','build')", (rid2, STUB))
        cur.execute("UPDATE asset_throughput SET state='lit' WHERE chart_id=%s AND asset_id=%s", (STUB_CHART, STUB))
        conn.commit()
        receipts2, terminal2 = read_back(cur, rid2)
        assert receipts2 is None and cp.terminal_ok(terminal2, STUB)[0] is True
        state, why = cp.provenance_check(rid2, EXPECTED, receipts2, True)
        assert state is False and "no provenance receipt" in why


def test_the_harness_build_path_is_the_bypass_it_never_touches_the_real_entry():
    """Static claim behind the above: trial_slice.build drives q.build_slice (build_id 'trial-slice'), and nothing in the harness imports asset_runner except the completion probe.  Reversion: route build()
    through run_asset (the long main TR would then lose its per-substep deadline and defect handling) -> this and the budget arithmetic both change."""
    import inspect
    src = inspect.getsource(ts.build)
    assert 'build_id="trial-slice"' in src and "run_asset" not in src and "_run_data_writer" not in src and "asset_runner" not in src
    assert "asset_runner.run_asset" in (fx.HARNESS / "completion.py").read_text()
