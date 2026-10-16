"""Launch bridge behavior. All remote calls are injected; no git/cloud programs run."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
RUN = "11111111-2222-4333-8444-555555555555"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
CREATED = dt.datetime(2031, 1, 1, tzinfo=dt.timezone.utc)
MANIFEST = {"version": "nirmana-run-manifest/v1", "chart_id": CHART,
            "scope": "asset_set", "scope_target": "ka_gochara_v5", "action": "rebuild",
            "waves": [["ka_gochara_v5"]], "assets": [{"asset_id": "ka_gochara_v5", "expected_code_digest": "a" * 64}],
            "gochara_v5_test_slice": {"schema": "gochara_v5_test_slice/1", "run": "one_class_full",
                                     "horizon": ["1998-01-01T00:00:00+00:00", "2026-04-17T00:00:00+00:00"], "classes": ["fixture"]}}
DIGEST = hashlib.sha256(json.dumps(MANIFEST, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(name):
    path = FLEET / (name + ".py")
    assert path.is_file(), f"missing reviewed operation implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def bridge():
    return load("smalltest_launch")


class Connection:
    def __init__(self, **changes):
        self.row = dict(id=RUN, chart_id=CHART, state="planned", scope="asset_set", scope_target="ka_gochara_v5",
                        action="rebuild", plan=["ka_gochara_v5"], triggered_by="gochara-v5-small-test",
                        plan_manifest=copy.deepcopy(MANIFEST), plan_manifest_digest=DIGEST, created_at=CREATED,
                        started_at=None)
        self.row.update(changes)
        self.clock = CREATED + dt.timedelta(seconds=599)
        self.assets = [{"asset_id": "ka_gochara_v5", "state": "queued", "position": 0}]
        self.queries = []

    def execute(self, sql, params=()):
        self.queries.append((sql, params))
        if "clock_timestamp" in sql:
            self.answer = {"db_now": self.clock}
        elif "FROM build_run_assets" in sql:
            self.answer = self.assets
        else:
            self.answer = self.row
        return self

    def fetchone(self):
        return self.answer

    def fetchall(self):
        return self.answer


def launch(bridge, tmp_path, conn=None, launcher=None):
    return bridge.launch_staged(run_id=RUN, expected_manifest=MANIFEST, connection=conn or Connection(),
                                claim_dir=tmp_path, launcher=launcher or (lambda run_id, timeout_s: "brahma-build-pipeline-job-abc12"))


def test_launches_exact_staged_run_and_persists_remote_identity(bridge, tmp_path):
    calls = []
    conn = Connection()
    result = launch(bridge, tmp_path, conn, lambda run_id, timeout_s: calls.append((run_id, timeout_s)) or "brahma-build-pipeline-job-abc12")
    assert calls == [(RUN, 1)]
    assert result["run_id"] == RUN and result["execution_name"] == "brahma-build-pipeline-job-abc12"
    assert result["plan_manifest_digest"] == DIGEST and result["status"] == "LAUNCHED"
    assert result["execute_by"] == "2031-01-01T00:10:00+00:00"
    assert json.loads((tmp_path / (RUN + ".json")).read_text()) == result
    assert any("FOR UPDATE" in sql and params == (RUN,) for sql, params in conn.queries)


@pytest.mark.parametrize("age", [600, 601, -1])
def test_refuses_stale_boundary_or_future_database_time(bridge, tmp_path, age):
    conn = Connection()
    conn.clock = CREATED + dt.timedelta(seconds=age)
    with pytest.raises(bridge.Refused):
        launch(bridge, tmp_path, conn, lambda *a: pytest.fail("must not launch stale run"))


@pytest.mark.parametrize("changes", [dict(id="00000000-2222-4333-8444-555555555555"), dict(chart_id="other"),
    dict(state="running"), dict(started_at=CREATED), dict(triggered_by="other"), dict(scope="chart"),
    dict(scope_target="other"), dict(action="build"), dict(plan=["other"]), dict(plan_manifest_digest="0" * 64),
    dict(plan_manifest={**MANIFEST, "gochara_v5_test_slice": {}}), dict(created_at=CREATED.replace(tzinfo=None))])
def test_refuses_mismatched_or_already_started_run(bridge, tmp_path, changes):
    with pytest.raises(bridge.Refused):
        launch(bridge, tmp_path, Connection(**changes), lambda *a: pytest.fail("must not launch mismatched run"))


def test_refuses_wrong_asset_queue(bridge, tmp_path):
    conn = Connection()
    conn.assets.append({"asset_id": "other", "state": "queued", "position": 1})
    with pytest.raises(bridge.Refused):
        launch(bridge, tmp_path, conn, lambda *a: pytest.fail("must not launch extra asset"))


def test_no_retry_after_success_or_unknown_remote_outcome(bridge, tmp_path):
    for folder, launcher in [(tmp_path / "ok", lambda *a: "brahma-build-pipeline-job-abc12"),
                             (tmp_path / "unknown", lambda *a: (_ for _ in ()).throw(TimeoutError()))]:
        try:
            launch(bridge, folder, launcher=launcher)
        except TimeoutError:
            pass
        with pytest.raises(bridge.Refused):
            launch(bridge, folder, launcher=lambda *a: pytest.fail("duplicate remote launch"))
        assert (folder / (RUN + ".json")).exists()


@pytest.mark.parametrize("execution", ["", "other-job-abc12", "brahma-build-pipeline-job-abc12\nextra", None])
def test_refuses_missing_or_wrong_remote_execution_identity(bridge, tmp_path, execution):
    with pytest.raises(bridge.Refused):
        launch(bridge, tmp_path, launcher=lambda *a: execution)
    assert (tmp_path / (RUN + ".json")).exists(), "ambiguous launch must retain its claim"


def test_launcher_uses_fixed_argv_timeout_and_no_shell(bridge, monkeypatch):
    calls = []
    class Result:
        returncode = 0
        stdout = "brahma-build-pipeline-job-abc12\n"
    monkeypatch.setattr(bridge.subprocess, "run", lambda argv, **kw: calls.append((argv, kw)) or Result())
    assert bridge.cloud_launcher(RUN, 17) == "brahma-build-pipeline-job-abc12"
    argv, kw = calls[0]
    assert argv == ["gcloud", "run", "jobs", "execute", "brahma-build-pipeline-job", "--project=madhav-astrology",
                    "--region=asia-south1", "--args=--run-id," + RUN, "--async", "--format=value(metadata.name)"]
    assert kw["timeout"] == 17 and not kw.get("shell")


def test_table_binds_enabled_p01_dispatch_to_launch_bridge():
    ops = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    op = ops["smalltest_dispatch"]
    assert op["script"].endswith("/smalltest_launch.py"), "staging alone is not dispatch"
    assert op["enabled"] is True and op["needs"] == "builder"
    assert op["allowed_args"] == ["run", "classes", "horizon-start", "horizon-end"]


def test_executor_receipt_carries_structured_launch_identity(tmp_path, monkeypatch):
    executor = load("executor")
    monkeypatch.setattr(executor, "REC", tmp_path)
    monkeypatch.setattr(executor, "log", lambda *a: None)
    body = dict(schema="ky.smalltest_launch/1", status="LAUNCHED", run_id=RUN, chart_id=CHART,
                asset_id="ka_gochara_v5", execution_name="brahma-build-pipeline-job-abc12", plan_manifest_digest=DIGEST)
    req = dict(operation_id="fixture", kind="smalltest_dispatch")
    executor.receipt(req, "COMPLETED", rc=0, out=json.dumps(body) + "\n")
    receipt = json.loads((tmp_path / "fixture.json").read_text())
    assert receipt["launch"]["run_id"] == RUN and receipt["launch"]["execution_name"] == body["execution_name"]
    executor.receipt(req, "COMPLETED", rc=0, out=RUN)
    receipt = json.loads((tmp_path / "fixture.json").read_text())
    assert receipt["status"] == "FAILED", "staging-only exit must not become a launch receipt"


def test_launch_requires_cloud_capability_as_well_as_builder(monkeypatch):
    executor = load("executor")
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    op = {**table["smalltest_dispatch"], "enabled": True, "production": False}
    req = dict(operation_id="cap-test", kind="smalltest_dispatch", item_id="fixture", idempotency_key="fresh",
               requested_by="adhikarin", kyd="fixture", args={})
    monkeypatch.setattr(executor, "seen", lambda *a: False)
    monkeypatch.setattr(executor, "smalltest_policy_problem", lambda req: None)  # this non-production fixture isolates capability admission
    assert executor.validate(req, {"smalltest_dispatch": op}, {"builder": True, "gcloud": False}) == "capability_missing: gcloud"
    assert executor.validate(req, {"smalltest_dispatch": op}, {"builder": True, "gcloud": True}) is None


def test_stage_once_uses_exact_uuid_and_rolls_back_only_readback(bridge, tmp_path, capsys):
    calls = []
    conn = Connection()
    conn.cursor = lambda: conn
    conn.rollback = lambda: calls.append("rollback")
    conn.close = lambda: calls.append("close")
    class Dispatcher:
        def build_slice_marker(self, **kw):
            return MANIFEST["gochara_v5_test_slice"]
        def main(self, argv):
            calls.append(argv)
            print(RUN)
        def _load_inactive_candidate(self, cur):
            return {}
        def build_small_test_manifest(self, **kw):
            return MANIFEST, DIGEST
    result = bridge.run(["--run", "one_class_full", "--classes", "fixture"], dispatcher=Dispatcher(), connect=lambda: conn,
                        launcher=lambda run_id, timeout_s: "brahma-build-pipeline-job-abc12", claim_dir=tmp_path)
    assert calls[0] == ["--i-am-steward", "--after-settled-1", "--execute", "--run", "one_class_full", "--classes", "fixture"]
    assert calls[-2:] == ["rollback", "close"] and result["run_id"] == RUN
    assert json.loads(capsys.readouterr().out)["execution_name"] == "brahma-build-pipeline-job-abc12"


def test_commit_unknown_never_connects_or_launches_or_restages(bridge, tmp_path):
    calls = []
    class Dispatcher:
        def build_slice_marker(self, **kw):
            return {}
        def main(self, argv):
            calls.append(argv)
            raise TimeoutError("commit unknown")
    with pytest.raises(TimeoutError):
        bridge.run(["--run", "one_class_full"], dispatcher=Dispatcher(), connect=lambda: pytest.fail("must lookup first"),
                   launcher=lambda *a: pytest.fail("must not launch"), claim_dir=tmp_path)
    assert len(calls) == 1


def test_existing_executor_refusals_remain_closed(monkeypatch):
    executor = load("executor")
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    req = dict(operation_id="guard", kind="unknown", item_id="fixture", idempotency_key="fresh", requested_by="adhikarin", kyd="fixture", args={})
    assert "unknown kind" in executor.validate(req, table, {"builder": True, "gcloud": True})
    req["kind"] = "smalltest_dispatch"
    table["smalltest_dispatch"] = {**table["smalltest_dispatch"], "enabled": False}
    assert "not enabled" in executor.validate(req, table, {"builder": True, "gcloud": True})
    table["smalltest_dispatch"] = {**table["smalltest_dispatch"], "enabled": True}
    req["args"] = {"execute": "true"}
    assert "disallowed args" in executor.validate(req, table, {"builder": True, "gcloud": True})


def test_clock_is_rechecked_after_durable_claim(bridge, tmp_path, monkeypatch):
    conn = Connection()
    original = bridge._write_claim
    def advance(*args, **kwargs):
        original(*args, **kwargs)
        conn.clock = CREATED + dt.timedelta(minutes=10)
    monkeypatch.setattr(bridge, "_write_claim", advance)
    with pytest.raises(bridge.Refused):
        launch(bridge, tmp_path, conn, lambda *a: pytest.fail("deadline elapsed during claim write"))
    assert (tmp_path / (RUN + ".json")).exists()


def test_receipt_refuses_multiple_or_invalid_launch_records(tmp_path, monkeypatch):
    executor = load("executor")
    monkeypatch.setattr(executor, "REC", tmp_path)
    monkeypatch.setattr(executor, "log", lambda *a: None)
    body = dict(schema="ky.smalltest_launch/1", status="LAUNCHED", run_id=RUN, chart_id=CHART,
                asset_id="ka_gochara_v5", execution_name="brahma-build-pipeline-job-abc12", plan_manifest_digest=DIGEST)
    for out in (json.dumps(body) + "\n" + json.dumps(body), json.dumps({**body, "chart_id": "other"}),
                json.dumps({**body, "execution_name": "other-job"}), json.dumps({**body, "plan_manifest_digest": "missing"})):
        executor.receipt(dict(operation_id="fixture", kind="smalltest_dispatch"), "COMPLETED", rc=0, out=out)
        assert json.loads((tmp_path / "fixture.json").read_text())["status"] == "FAILED"


def test_smalltest_rollback_binding_has_required_steward_intent():
    op = json.loads((FLEET / "executor_ops.json").read_text())["ops"]["smalltest_dispatch_dryrun"]
    assert op["fixed_args"] == ["--i-am-steward", "--after-settled-1", "--dry-run"]
    assert "--execute" not in op["fixed_args"] and op["enabled"] is True
