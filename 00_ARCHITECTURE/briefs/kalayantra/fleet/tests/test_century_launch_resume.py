"""SR-RESUME-NOW (OWNER-RESUMABLE-REQUIRED-20261025): the launcher mode `century_launch.py --resume`, the staging binding it drives and the executor row that runs it.

Doctrine: root CLAUDE.md §N.8 (each claim measured by a detector that can read false) and §B.10 (no invented value). One oracle per distinct production claim; each passes on the real
launcher and FAILS on a copy of century_launch.py with that ONE claim's line reverted (the planted reversion; the pattern of test_executor_century_resume.py). The staging binding's
own gate and the teardown scope are in platform/scripts/__tests__/test_century_resume_staging.py and test_century_resume_teardown.py.

  L1 a resume refuses, before anything is staged or launched, a request that is not a `century_resume` of the writer program the century contract declares
  L2 a resume stages through the RESUME binding and launches the SAME Cloud Run job as a dispatch, over the same staged century arguments (no new writer argument), and records the
     launch exactly as the dispatch does (ky.century_launch/1)
  L3 the dispatch path is unchanged: without --resume the launcher never reads the request or the contract for a resume, stages through the dispatch binding and launches as before
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
REPO = FLEET.parents[3]
for folder in (FLEET, REPO / "platform/scripts"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import smalltest_launch as bridge  # noqa: E402
import v5_small_test_shared as shared  # noqa: E402

RUN = "33333333-4444-4555-8666-777777777777"
CHART = shared.CHART_ID
EXECUTION = "brahma-build-pipeline-job-res01"
WRITER = "d" * 64
ARGV = ["--final_rules", "true", "--defer_in_build_verify", "true", "--horizon", "1998-01-01T00:00:00+00:00,2084-02-05T00:00:00+00:00",
        "--result_policy", "window_qualification/1"]
STAGING = ["--i-am-steward", "--after-settled-1", "--execute", "--classes", "all", "--final_rules", "true", "--defer_in_build_verify", "true",
           "--horizon", "1998-01-01T00:00:00+00:00,2084-02-05T00:00:00+00:00", "--result_policy", "window_qualification/1"]
MANIFEST = {"version": "nirmana-run-manifest/v1", "chart_id": CHART, "scope": "asset_set", "scope_target": "ka_gochara_v5", "action": "rebuild",
            "gochara_v5_century_config": {"schema": "gochara_v5_century_config/2"}}
DIGEST = hashlib.sha256(bridge.canonical(MANIFEST).encode()).hexdigest()
CONTRACT = {"schema": "ky.century_contract/1", "image": {"writer_source_digest": WRITER}}


def load_launcher(tmp_path, mutation=None):
    """century_launch.py as a module: the real file, or a copy with ONE reversion. The copy sits in a tree shaped like the repository (its platform/ is a link to the real one) so
    its own relative lookups (platform/scripts) resolve."""
    text = (FLEET / "century_launch.py").read_text()
    if mutation:
        old, new = mutation
        if text.count(old) != 1:
            raise RuntimeError(f"mutation anchor not unique: {old!r}")       # a bad anchor must never read as a failed oracle
        text = text.replace(old, new)
    home = tmp_path / "tree" / "00_ARCHITECTURE/briefs/kalayantra/fleet"
    home.mkdir(parents=True)
    (tmp_path / "tree" / "platform").symlink_to(REPO / "platform")
    (home / "century_launch.py").write_text(text)
    spec = importlib.util.spec_from_file_location("century_launch_resume_under_test", home / "century_launch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Dispatcher:
    """The staging binding's interface as the launcher uses it, recording what it is asked."""

    def __init__(self):
        self.staged = []

    def main(self, argv):
        self.staged.append(list(argv))
        print(RUN)

    @staticmethod
    def _load_inactive_candidate(cursor):
        return {"asset_id": "ka_gochara_v5"}

    @staticmethod
    def century_shape(**kwargs):
        return dict(kwargs)

    @staticmethod
    def build_century_manifest(*, candidate, slice_marker):
        return MANIFEST, DIGEST


class Connection:
    """The staged run's locked row and queue, as launch_staged reads them (the bridge's own tests use the same shape)."""

    def __init__(self):
        import datetime as dt
        self.created = dt.datetime(2031, 1, 1, tzinfo=dt.timezone.utc)
        self.clock = self.created + dt.timedelta(seconds=30)
        self.row = dict(id=RUN, chart_id=CHART, state="planned", scope="asset_set", scope_target="ka_gochara_v5", action="rebuild", plan=["ka_gochara_v5"],
                        triggered_by="gochara-v5-century", plan_manifest=MANIFEST, plan_manifest_digest=DIGEST, created_at=self.created, started_at=None)
        self.rolled_back = False

    def execute(self, sql, params=()):
        if "clock_timestamp" in sql:
            self.answer = {"db_now": self.clock}
        elif "FROM build_run_assets" in sql:
            self.answer = [{"asset_id": "ka_gochara_v5", "state": "queued", "position": 0}]
        else:
            self.answer = self.row
        return self

    def fetchone(self):
        return self.answer

    def fetchall(self):
        return self.answer

    def cursor(self):
        return object()

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def request(kind="century_resume", writer=WRITER):
    return {"kind": kind, "operation_id": "op-resume", "item_id": "J-4e", "program_identity": {"writer_digest": writer}}


def resume(launcher_module, tmp_path, *, argv=("--resume", *ARGV), req=None, dispatcher=None, launched=None):
    dispatcher = dispatcher or Dispatcher()
    launched = [] if launched is None else launched
    result = launcher_module.run(list(argv), dispatcher=dispatcher, connect=Connection, claim_dir=tmp_path / "claims",
                                 launcher=lambda run_id, timeout_s: launched.append((run_id, timeout_s)) or EXECUTION,
                                 request=req or request(), contract=CONTRACT)
    return result, dispatcher, launched


# ───────────────────────────── L1 the program identity ─────────────────────────────
def oracle_l1_a_resume_of_another_program_refuses_before_any_staging(module, tmp_path):
    result, dispatcher, launched = resume(module, tmp_path / "ok")
    assert result["status"] == "LAUNCHED" and len(dispatcher.staged) == 1 and len(launched) == 1, "control failed — the contract's program is admitted"
    for label, bad in (("another writer program", request(writer="1" * 64)), ("no program identity", {**request(), "program_identity": None}),
                       ("a dispatch request under --resume", request(kind="century_dispatch"))):
        dispatcher, launched = Dispatcher(), []
        with pytest.raises((shared.Refused, bridge.Refused)):
            resume(module, tmp_path / label.replace(" ", "-"), req=bad, dispatcher=dispatcher, launched=launched)
        assert dispatcher.staged == [] and launched == [], f"{label}: something was staged or launched before the refusal"
        assert not (tmp_path / label.replace(" ", "-") / "claims").exists(), f"{label}: a launch claim was written"
    with pytest.raises(shared.Refused, match="program_identity.writer_digest differs from the century contract writer_source_digest"):
        resume(module, tmp_path / "named", req=request(writer="1" * 64))


# ───────────────────────────── L2 the binding and the job ─────────────────────────────
def oracle_l2_a_resume_stages_through_the_resume_binding_and_launches_the_same_job(module, tmp_path, monkeypatch):
    assert module.staging_binding(True).__name__ == "dispatch_v5_century_resume_job" and module.staging_binding(False).__name__ == "dispatch_v5_century_job"
    result, dispatcher, launched = resume(module, tmp_path)
    assert dispatcher.staged == [STAGING], "the staging request is the dispatch's, argument for argument: the writer is handed no resume argument"
    assert launched == [(RUN, 570)] and result["execution_name"] == EXECUTION
    assert (result["schema"], result["status"], result["run_id"], result["chart_id"], result["asset_id"], result["plan_manifest_digest"]) == (
        "ky.century_launch/1", "LAUNCHED", RUN, CHART, "ka_gochara_v5", DIGEST)
    assert json.loads((tmp_path / "claims" / (RUN + ".json")).read_text()) == result
    # the job: the default launcher is the century one, and it executes the very command the dispatch's launch plan states
    assert module.run.__kwdefaults__["launcher"] is module.century_cloud_launcher
    import dispatch_v5_century_job as dispatch
    seen = []
    monkeypatch.setattr(bridge.subprocess, "run", lambda argv, **kw: seen.append(argv) or type("R", (), {"returncode": 0, "stdout": EXECUTION + "\n"})())
    assert module.century_cloud_launcher(RUN, 30) == EXECUTION
    assert seen == [dispatch.launch_plan(RUN)["argv"]]


def test_the_resume_binding_exposes_what_the_launcher_drives():
    import dispatch_v5_century_resume_job as binding
    for name in ("main", "century_shape", "build_century_manifest", "_load_inactive_candidate"):
        assert callable(getattr(binding, name)), name
    import dispatch_v5_century_job as dispatch
    assert binding.century_shape is dispatch.century_shape
    # the manifest the launcher expects is the century manifest PLUS the explicit resume binding (SR-RESUME-EXPLICIT-BINDING): the resume binding's own builder, never the dispatch's
    assert binding.build_century_manifest is not dispatch.build_century_manifest and binding.build_century_manifest.__module__ == binding.__name__


# ───────────────────────────── L3 the dispatch path ─────────────────────────────
def oracle_l3_the_dispatch_path_is_unchanged(module, tmp_path):
    untouched = type("Untouched", (dict,), {"get": lambda self, *a: pytest.fail("the dispatch path read the resume request")})()
    dispatcher, launched = Dispatcher(), []
    result = module.run(list(ARGV), dispatcher=dispatcher, connect=Connection, claim_dir=tmp_path / "claims",
                        launcher=lambda run_id, timeout_s: launched.append(run_id) or EXECUTION, request=untouched, contract=None)
    assert dispatcher.staged == [STAGING] and launched == [RUN]
    assert (result["schema"], result["status"], result["execution_name"]) == ("ky.century_launch/1", "LAUNCHED", EXECUTION)
    again, _, _ = resume(module, tmp_path / "resume")
    assert {k: v for k, v in again.items() if k not in ("created_at", "execute_by")} == {k: v for k, v in result.items() if k not in ("created_at", "execute_by")}, \
        "the resume launch record is the dispatch's, field for field"


ORACLES = {
    "l1": (oracle_l1_a_resume_of_another_program_refuses_before_any_staging,
           ("        resume_preflight(request, contract)          # a program identity other than the contract's refuses here, before any staging", "        pass")),
    "l2": (oracle_l2_a_resume_stages_through_the_resume_binding_and_launches_the_same_job,
           ("    if resume:\n        import dispatch_v5_century_resume_job as binding", "    if False:\n        import dispatch_v5_century_resume_job as binding")),
    "l3": (oracle_l3_the_dispatch_path_is_unchanged, ("    if args.resume:\n        resume_preflight(request, contract)", "    if True:\n        resume_preflight(request, contract)")),
}


def call(oracle, module, tmp_path, monkeypatch):
    if "monkeypatch" in oracle.__code__.co_varnames[:oracle.__code__.co_argcount]:
        return oracle(module, tmp_path, monkeypatch)
    return oracle(module, tmp_path)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_launcher(tmp_path, monkeypatch, claim):
    call(ORACLES[claim][0], load_launcher(tmp_path), tmp_path / "run", monkeypatch)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, mutation = ORACLES[claim]
    with pytest.raises((AssertionError, pytest.fail.Exception, shared.Refused, bridge.Refused)) as caught:
        call(oracle, load_launcher(tmp_path / "copy", mutation), tmp_path / "run", monkeypatch)
    assert "mutation anchor" not in str(caught.value)
