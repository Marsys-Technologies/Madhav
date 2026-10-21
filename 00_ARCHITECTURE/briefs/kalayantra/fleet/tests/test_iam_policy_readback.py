"""C-06: `iam_policy_readback` — a read-only, argument-free measurement of the IAM facts of acts 12, 13 and 14 of the Gochara verification-job runbook,
printing the `ky.iam_readback/1` line that `assemble_precentury.py j4c-a55m --iam-readback` (`judge_iam`) reads.

One oracle per distinct production claim; each cites its source. No `gcloud`, credential, network or database is touched: the script's `runner` is a
double that returns gcloud `--format=json` output in the documented REST shapes (Cloud Logging API `LogView`: name, description, createTime, updateTime,
filter; Cloud IAM `Policy`: version, bindings[{role, members, condition}], etag, auditConfigs), and one end-to-end test runs the script as a subprocess
against a stub `gcloud` on PATH.

  I1  exactly FOUR fixed gcloud calls, in this order, each `--format=json` and none with an argument from the caller         (spec: IAM_READBACK_KIND_SPEC.md)
  I2  a call outside the list, or a verb that is not a read, is refused BEFORE the runner sees it
  I3  the output is parsed into the typed record: act 12 (view + its own policy), act 13 (job policy), project-level roles of github-actions@ only
  I4  a field this reader does not know is refused: a policy field, a binding field (a `condition`), a view field
  I5  a response that cannot be read as what it claims (other view, no filter, malformed role/members, gcloud failure, non-JSON) REFUSES the whole record
  I6  a policy gcloud returns with no `bindings` key is the empty policy: a measured zero, not a refusal
  I7  the constants are the ones the repository's own workflows use (view, bucket, location, job, region, project, identity)
  I8  the table binds the kind exactly, DISABLED, and the real `validate` refuses a disabled kind and any argument
  I9  end to end through the CLI: one JSON line, exit 0 / 1, stderr of gcloud never relayed, any argument exits 2 before a call
"""
import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
SCRIPT = FLEET / "iam_policy_readback.py"

spec = importlib.util.spec_from_file_location("iam_policy_readback_under_test", SCRIPT)
IR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IR)

ACTOR = "serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com"
OTHER = "serviceAccount:someone-else@madhav-astrology.iam.gserviceaccount.com"
VIEW_NAME = "projects/madhav-astrology/locations/global/buckets/_Default/views/gochara_verification_job"
FILTER = 'resource.type="cloud_run_job" AND resource.labels.job_name="gochara-verification-job"'
FIXED = [   # the four calls of the spec, written out here independently of the script's CALLS
    ["gcloud", "logging", "views", "describe", "gochara_verification_job", "--bucket=_Default", "--location=global", "--project=madhav-astrology", "--format=json"],
    ["gcloud", "logging", "views", "get-iam-policy", "gochara_verification_job", "--bucket=_Default", "--location=global", "--project=madhav-astrology", "--format=json"],
    ["gcloud", "run", "jobs", "get-iam-policy", "gochara-verification-job", "--region=asia-south1", "--project=madhav-astrology", "--format=json"],
    ["gcloud", "projects", "get-iam-policy", "madhav-astrology", "--format=json"],
]
NOW = IR.dt.datetime(2026, 10, 21, 5, 0, 0, tzinfo=IR.dt.timezone.utc)


def view_body(**over):
    body = {"name": VIEW_NAME, "filter": FILTER, "description": "the verification job's logs", "createTime": "2026-10-21T01:00:00.123Z", "updateTime": "2026-10-21T01:00:00.123Z"}
    body.update(over)
    return body


def policy(*bindings, **over):
    body = {"bindings": [{"role": r, "members": list(m)} for r, m in bindings], "etag": "BwZabc=", "version": 1}
    body.update(over)
    return body


def good_responses():
    return [
        view_body(),
        policy(("roles/logging.viewAccessor", [ACTOR])),
        policy(("roles/run.jobsExecutorWithOverrides", [ACTOR])),
        policy(("roles/cloudsql.client", [ACTOR, OTHER]), ("roles/run.developer", [ACTOR]), ("roles/owner", ["user:owner@example.invalid"]), ("roles/run.admin", [OTHER])),
    ]


class Gcloud:
    """Answers the four fixed calls in order; records every argv."""

    def __init__(self, responses=None, rc=None, raw=None):
        self.responses = list(good_responses() if responses is None else responses)
        self.rc, self.raw, self.calls = rc or {}, raw or {}, []

    def __call__(self, argv):
        index = len(self.calls)
        self.calls.append(list(argv))
        out = self.raw.get(index, json.dumps(self.responses[index]))
        return subprocess.CompletedProcess(argv, self.rc.get(index, 0), stdout=out, stderr="ERROR: noisy identity victim@example.invalid ya29.LEAK")


def measure(gcloud=None):
    gcloud = gcloud or Gcloud()
    return IR.measure(gcloud, clock=lambda: NOW), gcloud


def refusal(gcloud):
    with pytest.raises(IR.Refused) as caught:
        IR.measure(gcloud, clock=lambda: NOW)
    return str(caught.value)


# ───────────── I1 four fixed calls ─────────────

def test_i1_exactly_four_fixed_read_only_calls_in_order_and_no_caller_argument():
    record, gcloud = measure()
    assert gcloud.calls == FIXED
    assert all(c[-1] == "--format=json" for c in gcloud.calls)
    assert IR.CALLS == {"view": FIXED[0], "view_policy": FIXED[1], "job_policy": FIXED[2], "project_policy": FIXED[3]}
    assert record["status"] == "MEASURED"
    import inspect
    assert list(inspect.signature(IR.measure).parameters) == ["runner", "clock"]          # nothing from a request reaches a call


# ───────────── I2 nothing but a read ─────────────

def test_i2_a_call_outside_the_list_or_a_mutating_verb_is_refused_before_the_runner_runs(monkeypatch):
    gcloud = Gcloud()
    with pytest.raises(IR.Refused, match="not one of the four fixed calls"):
        IR.gcloud_json("job_set_policy", gcloud)
    mutating = FIXED[2][:3] + ["add-iam-policy-binding"] + FIXED[2][4:] + [f"--member={ACTOR}", "--role=roles/owner"]
    monkeypatch.setitem(IR.CALLS, "job_policy", mutating)
    with pytest.raises(IR.Refused, match="not a read"):
        IR.gcloud_json("job_policy", gcloud)
    monkeypatch.setitem(IR.CALLS, "job_policy", ["gcloud", "run", "jobs", "delete", "gochara-verification-job", "--region=asia-south1"])
    with pytest.raises(IR.Refused, match="not a read"):
        IR.gcloud_json("job_policy", gcloud)
    assert gcloud.calls == []                                                           # the runner never saw any of them
    assert IR.read_verb(FIXED[3]) == "get-iam-policy" and IR.read_verb(FIXED[0]) == "describe"
    assert IR.READ_VERBS == {"describe", "get-iam-policy"}


# ───────────── I3 the typed record ─────────────

def test_i3_output_is_parsed_into_the_typed_record():
    record, _ = measure()
    assert record == {
        "schema": "ky.iam_readback/1", "status": "MEASURED", "measured_at": "2026-10-21T05:00:00Z", "project": "madhav-astrology",
        "act12": {"view": "gochara_verification_job", "bucket": "_Default", "location": "global", "filter": FILTER,
                  "bindings": [{"role": "roles/logging.viewAccessor", "members": [ACTOR]}]},
        "act13": {"job": "gochara-verification-job", "region": "asia-south1",
                  "bindings": [{"role": "roles/run.jobsExecutorWithOverrides", "members": [ACTOR]}]},
        "act14": {},
        "project_level_roles_of_github_actions": ["roles/cloudsql.client", "roles/run.developer"],
    }
    text = json.dumps(record)
    assert "owner@example.invalid" not in text and "someone-else" not in text and "roles/run.admin" not in text and "roles/owner" not in text    # the project policy is filtered to the one member


def test_i3_members_and_bindings_are_ordered_and_a_second_member_on_the_view_is_kept_for_the_judge():
    responses = good_responses()
    responses[1] = policy(("roles/logging.viewer", ["user:b@example.invalid"]), ("roles/logging.viewAccessor", [OTHER, ACTOR]))
    record, _ = measure(Gcloud(responses))
    assert record["act12"]["bindings"] == [{"role": "roles/logging.viewAccessor", "members": [ACTOR, OTHER]},
                                           {"role": "roles/logging.viewer", "members": ["user:b@example.invalid"]}]   # the judge refuses this; the reader must show it


# ───────────── I4 unknown fields ─────────────

@pytest.mark.parametrize("index, body, needle", [
    (1, lambda: policy(("roles/logging.viewAccessor", [ACTOR]), surprise=True), "policy carries a field this reader does not know ('surprise')"),
    (2, lambda: {"bindings": [{"role": "roles/run.jobsExecutorWithOverrides", "members": [ACTOR], "condition": {"expression": "request.time < timestamp('2027-01-01T00:00:00Z')"}}], "etag": "x"},
     "a binding carries a field this reader does not know ('condition')"),
    (3, lambda: policy(("roles/cloudsql.client", [ACTOR]), flavour="new"), "policy carries a field this reader does not know ('flavour')"),
    (0, lambda: view_body(retentionDays=30), "the response carries a field this reader does not know ('retentionDays')"),
])
def test_i4_a_field_the_reader_does_not_know_refuses_the_whole_record(index, body, needle):
    responses = good_responses()
    responses[index] = body()
    assert needle in refusal(Gcloud(responses))


# ───────────── I5 unreadable responses refuse ─────────────

@pytest.mark.parametrize("index, body, needle", [
    (0, lambda: view_body(name=VIEW_NAME.replace("gochara_verification_job", "_AllLogs")), "not for the gochara_verification_job view"),
    (0, lambda: view_body(name=VIEW_NAME.replace("_Default", "other")), "not for the gochara_verification_job view"),
    (0, lambda: {k: v for k, v in view_body().items() if k != "filter"}, "filter is missing or not text"),
    (0, lambda: view_body(filter=""), "filter is missing or not text"),
    (0, lambda: view_body(filter=["a"]), "filter is missing or not text"),
    (1, lambda: policy(("viewAccessor", [ACTOR])), "role is missing or not a role name"),
    (1, lambda: {"bindings": [{"members": [ACTOR]}]}, "role is missing or not a role name"),
    (2, lambda: policy(("roles/run.jobsExecutorWithOverrides", [])), "members of roles/run.jobsExecutorWithOverrides are missing or not text"),
    (2, lambda: policy(("roles/run.jobsExecutorWithOverrides", [7])), "are missing or not text"),
    (2, lambda: policy(("roles/run.jobsExecutorWithOverrides", [ACTOR]), ("roles/run.jobsExecutorWithOverrides", [OTHER])), "is bound twice"),
    (3, lambda: {"bindings": "roles/owner"}, "bindings is not a list"),
    (3, lambda: {"bindings": ["roles/owner"]}, "a binding is not an object"),
])
def test_i5_a_response_that_cannot_be_read_as_what_it_claims_refuses_the_whole_record(index, body, needle):
    responses = good_responses()
    responses[index] = body()
    assert needle in refusal(Gcloud(responses))


def test_i5_gcloud_failure_and_non_json_refuse_and_the_error_text_is_not_carried():
    for index in range(4):
        text = refusal(Gcloud(rc={index: 1}))
        assert "gcloud exited 1" in text and "victim@example.invalid" not in text and "ya29" not in text
    assert "not JSON" in refusal(Gcloud(raw={2: "Listed 0 items."}))
    assert "not a JSON object" in refusal(Gcloud(raw={3: "[]"}))

    def broken(argv):
        raise OSError("no gcloud")
    with pytest.raises(IR.Refused, match="could not be run or timed out"):
        IR.measure(broken)


# ───────────── I6 the empty policy ─────────────

def test_i6_a_policy_without_bindings_is_a_measured_zero_not_a_refusal():
    responses = good_responses()
    responses[2] = {"etag": "ACAB"}                                                     # gcloud omits `bindings` when there are none
    responses[3] = {"etag": "ACAB", "version": 3}
    record, _ = measure(Gcloud(responses))
    assert record["status"] == "MEASURED" and record["act13"]["bindings"] == [] and record["project_level_roles_of_github_actions"] == []


# ───────────── I7 the constants are the repository's own ─────────────

def test_i7_the_constants_are_the_ones_the_repository_workflows_use():
    deploy = (REPO / ".github/workflows/gochara-verification-job-deploy.yml").read_text()
    seal = (REPO / ".github/workflows/gochara-seal-approved.yml").read_text()
    assert re.search(r"^\s*VERIFICATION_JOB: gochara-verification-job$", deploy, re.M) and IR.JOB == "gochara-verification-job"
    assert re.search(r"^\s*GOOGLE_CLOUD_REGION: asia-south1$", deploy, re.M) and IR.REGION == "asia-south1"
    assert re.search(r"^\s*WIF_SERVICE_ACCOUNT: github-actions@madhav-astrology\.iam\.gserviceaccount\.com$", deploy, re.M)
    assert IR.GH_ACTOR == "serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com"
    assert "--project madhav-astrology --bucket=_Default --location=global --view=gochara_verification_job" in seal      # the seal reads the log through this very view
    assert (IR.PROJECT, IR.BUCKET, IR.LOCATION, IR.VIEW) == ("madhav-astrology", "_Default", "global", "gochara_verification_job")
    assert IR.VIEW_NAME == VIEW_NAME


# ───────────── I8 the table binding, through the real validate ─────────────

def _executor(tmp_path, monkeypatch):
    monkeypatch.setenv("KY_ROOT", str(tmp_path / "ky"))
    spec_ = importlib.util.spec_from_file_location(f"ky_exec_iam_{abs(hash(str(tmp_path)))}", FLEET / "executor.py")
    module = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(module)
    return module


def _req(**over):
    req = {"operation_id": "op-iam", "kind": "iam_policy_readback", "item_id": "J-4c-a55m", "idempotency_key": "key-iam", "requested_by": "adhikarin", "kyd": "kyd-1", "args": {}}
    req.update(over)
    return req


def test_i8_table_entry_is_exact_shipped_disabled_and_the_real_validate_holds(tmp_path, monkeypatch):
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    entry = table["iam_policy_readback"]
    assert list(entry)[0] == "enabled" and entry["enabled"] is False                  # shipped disabled: a separately reviewed flip enables it
    assert (entry["production"], entry["read_only"], entry["needs"], entry["fixed_args"], entry["allowed_args"]) == (False, True, "gcloud", [], [])
    assert entry["script"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/iam_policy_readback.py" and (REPO / entry["script"]).is_file()
    assert entry["requesters"] == ["adhikarin", "v1", "v2"] and "also_needs" not in entry
    ex = _executor(tmp_path, monkeypatch)
    caps = {"gcloud": True}
    assert "is not enabled" in ex.validate(_req(), table, caps)                         # disabled: refused today
    live = copy.deepcopy(table)
    live["iam_policy_readback"]["enabled"] = True
    assert ex.validate(_req(), live, caps) is None
    assert "disallowed args" in ex.validate(_req(args={"job": "other-job"}), live, caps)
    assert "disallowed args" in ex.validate(_req(args={"project": "other-project"}), live, caps)
    assert "may not request" in ex.validate(_req(requested_by="sutradhara"), live, caps)


# ───────────── I9 end to end through the CLI ─────────────

def _stub_gcloud(directory):
    stub = directory / "gcloud"
    stub.write_text("#!/bin/sh\n"
                    f'echo "$@" >> "{directory}/calls.log"\n'
                    'echo "ERROR: noisy token ya29.LEAK for victim@example.invalid" >&2\n'
                    f'case "$*" in *"views describe"*) cat "{directory}/view.json";; *"views get-iam-policy"*) cat "{directory}/view_policy.json";; '
                    f'*"run jobs get-iam-policy"*) cat "{directory}/job_policy.json";; *"projects get-iam-policy"*) cat "{directory}/project_policy.json";; *) exit 9;; esac\n')
    stub.chmod(0o755)
    for name, body in zip(("view", "view_policy", "job_policy", "project_policy"), good_responses()):
        (directory / f"{name}.json").write_text(json.dumps(body))


def test_i9_cli_prints_one_line_the_judge_reads_and_refuses_with_exit_1(tmp_path):
    _stub_gcloud(tmp_path)
    env = {"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    done = subprocess.run([sys.executable, "-I", str(SCRIPT)], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "ya29" not in done.stdout + done.stderr and "victim@example" not in done.stdout + done.stderr
    assert len(done.stdout.strip().splitlines()) == 1
    calls = (tmp_path / "calls.log").read_text().splitlines()
    assert [c.split() for c in calls] == [c[1:] for c in FIXED]
    line = json.loads(done.stdout)
    # judge_iam (assemble_precentury.py) reads exactly these keys and values
    assert line["schema"] == "ky.iam_readback/1" and line["status"] == "MEASURED"
    assert {"view", "bucket", "location", "filter", "bindings"} <= set(line["act12"]) and {"job", "region", "bindings"} <= set(line["act13"])
    assert "roles/cloudsql.client" in line["project_level_roles_of_github_actions"] and line["act14"] == {}
    (tmp_path / "job_policy.json").write_text(json.dumps({"bindings": [{"role": "roles/run.jobsExecutorWithOverrides", "members": [ACTOR], "condition": {"title": "t"}}]}))
    (tmp_path / "calls.log").unlink()
    refused = subprocess.run([sys.executable, "-I", str(SCRIPT)], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert refused.returncode == 1 and len(refused.stdout.strip().splitlines()) == 1
    record = json.loads(refused.stdout)
    assert record["status"] == "REFUSED" and "act12" not in record and "ya29" not in refused.stdout + refused.stderr


def test_i9_any_argument_exits_2_before_any_call(tmp_path):
    _stub_gcloud(tmp_path)
    env = {"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)}
    for extra in (["--project", "other"], ["--job", "other-job"], ["extra"], ["--format=yaml"]):
        done = subprocess.run([sys.executable, "-I", str(SCRIPT), *extra], capture_output=True, text=True, env=env, cwd=tmp_path)
        assert done.returncode == 2 and done.stdout == ""
    assert not (tmp_path / "calls.log").exists()
