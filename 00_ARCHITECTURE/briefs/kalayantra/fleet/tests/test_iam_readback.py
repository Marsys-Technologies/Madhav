"""Executor kind `iam_readback` — a read-only IAM evidence read with a FIXED allow-list of four probes (ruling madhav-44; receipts for J-4c-a55m acts 12-14; the fourth,
`secret_version_exists`, is the J-4b-a55j C7 detector, ruling SR-A55J-GAPS).

No gcloud, credential, network or database is touched: the script's `runner` is a double returning documents shaped like `gcloud ... --format=json` output
(a LogView resource, an IAM Policy resource). Distinct production claims, one doctrine-grounded oracle each (the doctrine is the gcloud/IAM resource shapes:
Cloud Logging `LogView` {name, filter, ...}; IAM `Policy` {bindings: [{role, members, condition?}], etag, version}; a conditional binding is not an unconditional grant;
CLAUDE.md §N.7.6 honest null / §N.8 earned signal):
R1 arguments are validated against the fixed allow-list: four probes, exactly each probe's own arguments, closed name shapes, project-fixed members; anything else exits 2 before a call ·
R2 the command builder can only emit `describe` / `get-iam-policy` on the fixed project/bucket/location/region, only the fixed flags; a planted `add-iam-policy-binding` (or any write verb / extra flag / second resource) is refused BEFORE the runner ·
R3 the output is normalised: bindings sorted by role, members de-duplicated and sorted, whatever order gcloud answered in; an absent `bindings` key is a measured zero ·
R4 the project probe filters in process to ONE member and ONE role: `held` is true only for an unconditional binding, no other member or role is printed, a conditional-only grant REFUSES ·
R5 an unreadable record REFUSES whole (wrong view name, unknown field, conditional binding, role twice, non-text member, gcloud failure, non-JSON) and never relays stderr ·
R6 the receipt shape: one `ky.iam_readback_probe/1` line per run, exit 0 MEASURED / 1 REFUSED / 2 bad arguments, through the real executor `validate` and the real CLI with a stub gcloud ·
R7 the J-4c-a55m pass conditions can be read off the three real-shape records (the cockpit's judgement, here only shown to be decidable from the record) ·
R8 the secret probe is METADATA ONLY: the builder cannot emit `access` (planted `versions access` refused before the runner), the secret name is a closed allow-list, the
record carries exists / create time / labels / replication and per version number, state (ENABLED / DISABLED / DESTROYED) and create time and no payload, checksum or
annotation; versions sorted; NOT_FOUND is a measured `exists: false`, any other failure (incl. PERMISSION_DENIED) REFUSES; unknown fields / states / foreign names refuse.
Doctrine: Secret Manager `Secret` {name, createTime, labels, replication, ...} and `SecretVersion` {name, state ENABLED|DISABLED|DESTROYED, createTime, ...} resources;
`versions access` is the only verb that returns a payload (SecretVersion payload is a separate resource).
"""
import copy
import datetime as dt
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
SCRIPT = FLEET / "iam_readback.py"

spec = importlib.util.spec_from_file_location("iam_readback_under_test", SCRIPT)
IR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IR)

NOW = dt.datetime(2026, 10, 22, 21, 0, 0, tzinfo=dt.timezone.utc)
VIEW = "gochara_verification_job"
JOB = "gochara-verification-job"
GH = "serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com"
RUNTIME = "serviceAccount:gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com"
OTHER = "serviceAccount:someone-else@madhav-astrology.iam.gserviceaccount.com"
PERSON = "user:person@example.invalid"
FILTER = 'resource.type="cloud_run_job" AND resource.labels.job_name="gochara-verification-job"'
SECRET = "gochara-sealer-db-url"
OTHER_SECRET = "some-other-secret"                      # a secret id outside the allow-list
VIEW_RESOURCE = f"projects/madhav-astrology/locations/global/buckets/_Default/views/{VIEW}"
LOG_FLAGS = ["--bucket=_Default", "--location=global", "--project=madhav-astrology", "--format=json"]


def view_body(**over):
    body = {"name": VIEW_RESOURCE, "filter": FILTER, "createTime": "2026-10-20T00:00:00Z", "updateTime": "2026-10-20T00:00:00Z"}
    body.update(over)
    return body


def secret_body(**over):
    body = {"name": f"projects/123456789/secrets/{SECRET}", "createTime": "2026-10-20T01:00:00.000000Z", "labels": {"owner": "kalayantra", "used-by": "seal"},
            "replication": {"automatic": {}}, "etag": "\"abc\""}
    body.update(over)
    return body


def version_body(number, state="ENABLED", create="2026-10-21T02:00:00.000000Z", **over):
    body = {"name": f"projects/123456789/secrets/{SECRET}/versions/{number}", "state": state, "createTime": create, "etag": "\"v\"", "replicationStatus": {"automatic": {}}}
    body.update(over)
    return body


def policy(*bindings, **extra):
    body = {"bindings": [{"role": r, "members": m} for r, m in bindings], "etag": "BwZ", "version": 1}
    body.update(extra)
    return body


class Gcloud:
    """Answers each call in order; records every argv; stderr carries a fake identity and token that must never reach the record."""

    def __init__(self, *responses, rc=0, raw=None):
        self.responses, self.rc, self.raw, self.calls = list(responses), rc, raw, []

    def __call__(self, argv):
        index = len(self.calls)
        self.calls.append(list(argv))
        out = self.raw if self.raw is not None else json.dumps(self.responses[index])
        return subprocess.CompletedProcess(argv, self.rc, stdout=out, stderr="ERROR: noisy identity victim@example.invalid ya29.LEAK")


def measure(probe, args, gcloud):
    return IR.measure(probe, args, gcloud, clock=lambda: NOW)


def refusal(probe, args, gcloud):
    with pytest.raises(IR.Refused) as caught:
        measure(probe, args, gcloud)
    return str(caught.value)


# ───────────── R1 the fixed allow-list of arguments ─────────────

def test_r1_each_probe_takes_exactly_its_own_arguments_in_closed_shapes():
    assert IR.PROBES == ("logging_view", "run_job_iam", "project_iam_member_role", "secret_version_exists")
    assert IR.validate_args("secret_version_exists", {"secret": SECRET, "view": None}) == {"secret": SECRET}
    assert IR.validate_args("logging_view", {"view": VIEW, "job": None}) == {"view": VIEW}
    assert IR.validate_args("run_job_iam", {"job": JOB}) == {"job": JOB}
    ok = {"member": GH, "role": "roles/cloudsql.client"}
    assert IR.validate_args("project_iam_member_role", ok) == ok
    assert IR.validate_args("project_iam_member_role", {"member": GH, "role": "projects/madhav-astrology/roles/custom.reader"})
    for probe, args in (("logging_view", {}), ("logging_view", {"view": VIEW, "job": JOB}), ("run_job_iam", {"view": VIEW}), ("run_job_iam", {"job": JOB, "role": "roles/x"}),
                        ("project_iam_member_role", {"member": GH}), ("project_iam_member_role", {"role": "roles/owner"}),
                        ("project_iam_member_role", {"member": GH, "role": "roles/owner", "view": VIEW}), ("get_everything", {"view": VIEW}), ("", {}),
                        ("secret_version_exists", {}), ("secret_version_exists", {"secret": SECRET, "job": JOB}), ("secret_version_exists", {"secret": OTHER_SECRET}),
                        ("secret_version_exists", {"secret": f"{SECRET} --version=latest"}), ("secret_version_exists", {"secret": f"projects/1/secrets/{SECRET}"})):
        with pytest.raises(IR.Refused):
            IR.validate_args(probe, args)


@pytest.mark.parametrize("probe,key,value", [
    ("logging_view", "view", "--impersonate-service-account=x"), ("logging_view", "view", "-v"), ("logging_view", "view", "Upper"), ("logging_view", "view", "a b"),
    ("logging_view", "view", "view;rm"), ("logging_view", "view", "../_Default"), ("logging_view", "view", ""),
    ("run_job_iam", "job", "--project=other"), ("run_job_iam", "job", "Job"), ("run_job_iam", "job", "a/b"), ("run_job_iam", "job", "-x"), ("run_job_iam", "job", "a_b"),
])
def test_r1_a_name_outside_its_closed_shape_is_refused(probe, key, value):
    with pytest.raises(IR.Refused):
        IR.validate_args(probe, {key: value})


@pytest.mark.parametrize("member", [PERSON, "serviceAccount:x@other-project.iam.gserviceaccount.com", "group:team@example.invalid", "allUsers", "allAuthenticatedUsers",
                                    "serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com --role=roles/owner", "github-actions@madhav-astrology.iam.gserviceaccount.com",
                                    "serviceAccount:a@madhav-astrology.iam.gserviceaccount.com", ""])
def test_r1_a_member_other_than_a_service_account_of_this_project_is_refused(member):
    with pytest.raises(IR.Refused):
        IR.validate_args("project_iam_member_role", {"member": member, "role": "roles/cloudsql.client"})


@pytest.mark.parametrize("role", ["owner", "roles/", "roles/a b", "roles/a;b", "projects/other/roles/x", "organizations/1/roles/x", "--role=roles/owner", ""])
def test_r1_a_role_outside_the_role_shapes_is_refused(role):
    with pytest.raises(IR.Refused):
        IR.validate_args("project_iam_member_role", {"member": GH, "role": role})


def test_r1_the_cli_exits_2_before_any_call_for_a_bad_or_foreign_argument(tmp_path):
    _stub_gcloud(tmp_path)
    for extra in (["--probe", "logging_view"], ["--probe", "logging_view", "--view", VIEW, "--project", "other"], ["--probe", "run_job_iam", "--job", JOB, "--region", "us-east1"],
                  ["--probe", "run_job_iam", "--job", JOB, "--view", VIEW], ["--probe", "project_iam_member_role", "--member", PERSON, "--role", "roles/owner"],
                  ["--probe", "write_everything"], [], ["--probe", "secret_version_exists"], ["--probe", "secret_version_exists", "--secret", "other-secret"],
                  ["--probe", "secret_version_exists", "--secret", SECRET, "--version", "latest"], ["--probe", "run_job_iam", "--job", "-bad"], ["--prob", "run_job_iam", "--job", JOB], ["--probe", "run_job_iam", "--job", JOB, "extra"]):
        done = _run_cli(tmp_path, extra)
        assert done.returncode == 2, (extra, done.stdout, done.stderr)
        assert done.stdout == ""
    assert not (tmp_path / "calls.log").exists()                                         # no gcloud call was made for any of them


# ───────────── R2 the command builder: reads only ─────────────

def test_r2_each_probe_builds_exactly_its_fixed_read_only_commands():
    assert IR.build_command("view", {"view": VIEW}) == ["gcloud", "logging", "views", "describe", VIEW, *LOG_FLAGS]
    assert IR.build_command("view_policy", {"view": VIEW}) == ["gcloud", "logging", "views", "get-iam-policy", VIEW, *LOG_FLAGS]
    assert IR.build_command("job_policy", {"job": JOB}) == ["gcloud", "run", "jobs", "get-iam-policy", JOB, "--region=asia-south1", "--project=madhav-astrology", "--format=json"]
    assert IR.build_command("project_policy", {"member": GH, "role": "roles/x"}) == ["gcloud", "projects", "get-iam-policy", "madhav-astrology", "--format=json"]
    assert IR.build_command("secret", {"secret": SECRET}) == ["gcloud", "secrets", "describe", SECRET, "--project=madhav-astrology", "--format=json"]
    assert IR.build_command("secret_versions", {"secret": SECRET}) == ["gcloud", "secrets", "versions", "list", SECRET, "--project=madhav-astrology", "--format=json"]
    assert set(IR.CALL_SHAPES) == {"view", "view_policy", "job_policy", "project_policy", "secret", "secret_versions"} and IR.READ_VERBS == {"describe", "get-iam-policy", "list"}
    assert IR.CALLS_OF == {"logging_view": ("view", "view_policy"), "run_job_iam": ("job_policy",), "project_iam_member_role": ("project_policy",),
                           "secret_version_exists": ("secret", "secret_versions")}
    for call, args in (("view", {"view": VIEW}), ("view_policy", {"view": VIEW}), ("job_policy", {"job": JOB}), ("project_policy", {}), ("secret", {"secret": SECRET}),
                       ("secret_versions", {"secret": SECRET})):
        assert IR.read_verb(IR.build_command(call, args)) in IR.READ_VERBS


def test_r2_every_probe_run_emits_only_describe_or_get_iam_policy_calls():
    plans = ((("logging_view", {"view": VIEW}), [view_body(), policy()]), (("run_job_iam", {"job": JOB}), [policy()]),
             (("project_iam_member_role", {"member": GH, "role": "roles/cloudsql.client"}), [policy()]),
             (("secret_version_exists", {"secret": SECRET}), [secret_body(), [version_body(1)]]))
    for (probe, args), responses in plans:
        gcloud = Gcloud(*responses)
        measure(probe, args, gcloud)
        assert len(gcloud.calls) == len(IR.CALLS_OF[probe])
        assert {IR.read_verb(c) for c in gcloud.calls} <= {"describe", "get-iam-policy", "list"}
        assert all(c[0] == "gcloud" for c in gcloud.calls)


@pytest.mark.parametrize("verb", ["add-iam-policy-binding", "set-iam-policy", "remove-iam-policy-binding", "delete", "update", "create", "execute"])
def test_r2_a_planted_write_verb_is_refused_before_the_runner_sees_it(monkeypatch, verb):
    shapes = dict(IR.CALL_SHAPES)
    shapes["job_policy"] = ("gcloud", "run", "jobs", verb, "{job}", "--region=asia-south1", "--project=madhav-astrology", "--format=json")
    monkeypatch.setattr(IR, "CALL_SHAPES", shapes)
    gcloud = Gcloud(policy())
    with pytest.raises(IR.Refused, match="not a read"):
        IR.build_command("job_policy", {"job": JOB})
    with pytest.raises(IR.Refused):
        measure("run_job_iam", {"job": JOB}, gcloud)
    assert gcloud.calls == []


def test_r2_the_planted_add_iam_policy_binding_with_member_and_role_flags_is_refused_in_the_cli(tmp_path, monkeypatch):
    mutating = ["gcloud", "projects", "add-iam-policy-binding", "madhav-astrology", f"--member={GH}", "--role=roles/owner"]
    gcloud = Gcloud(policy())
    with pytest.raises(IR.Refused, match="not a read"):
        IR.gcloud_json(mutating, gcloud, "planted")
    assert gcloud.calls == []
    monkeypatch.setattr(IR, "CALL_SHAPES", {**IR.CALL_SHAPES, "project_policy": tuple(mutating)})
    assert IR.cli(["--probe", "project_iam_member_role", "--member", GH, "--role", "roles/owner"], runner=gcloud) == 1
    assert gcloud.calls == []


def test_r2_an_extra_flag_a_second_resource_a_foreign_program_or_an_unknown_call_is_refused(monkeypatch):
    gcloud = Gcloud(policy())
    good = IR.build_command("job_policy", {"job": JOB})
    for bad in (good + ["--impersonate-service-account=x@y.iam.gserviceaccount.com"], good + ["--flatten=bindings"], good + ["--account", "x"],
                good[:5] + ["second-job"] + good[5:], ["bash", "-c", "gcloud run jobs get-iam-policy x"], ["gcloud"], [], good + ["--quiet"]):
        with pytest.raises(IR.Refused):
            IR.gcloud_json(bad, gcloud, "planted")
    assert gcloud.calls == []
    with pytest.raises(IR.Refused, match="not one of the fixed calls"):
        IR.build_command("job_set_policy", {"job": JOB})
    assert IR.PROJECT == "madhav-astrology" and "{project}" not in " ".join(w for s in IR.CALL_SHAPES.values() for w in s)       # the project is never an argument


# ───────────── R3 normalisation ─────────────

def test_r3_bindings_are_sorted_by_role_and_members_deduplicated_and_sorted():
    shuffled = policy(("roles/run.viewer", [OTHER, GH, OTHER]), ("roles/logging.viewAccessor", [RUNTIME, GH]), ("roles/cloudsql.client", [GH]))
    record = measure("run_job_iam", {"job": JOB}, Gcloud(shuffled))
    assert record["bindings"] == [{"role": "roles/cloudsql.client", "members": [GH]}, {"role": "roles/logging.viewAccessor", "members": [GH, RUNTIME]},
                                  {"role": "roles/run.viewer", "members": [GH, OTHER]}]
    reordered = policy(("roles/cloudsql.client", [GH]), ("roles/run.viewer", [GH, OTHER]), ("roles/logging.viewAccessor", [GH, RUNTIME]))
    assert measure("run_job_iam", {"job": JOB}, Gcloud(reordered)) == record                # the answer order of gcloud changes nothing


def test_r3_a_policy_with_no_bindings_key_is_a_measured_zero_not_a_refusal():
    record = measure("run_job_iam", {"job": JOB}, Gcloud({"etag": "ACAB"}))
    assert record["status"] == "MEASURED" and record["bindings"] == []


def test_r3_the_view_record_is_typed_and_carries_the_filter_verbatim():
    gcloud = Gcloud(view_body(description="x"), policy(("roles/logging.viewAccessor", [GH])))
    record = measure("logging_view", {"view": VIEW}, gcloud)
    assert record == {"schema": "ky.iam_readback_probe/1", "status": "MEASURED", "probe": "logging_view", "measured_at": "2026-10-22T21:00:00Z", "project": "madhav-astrology",
                      "view": {"name": VIEW, "bucket": "_Default", "location": "global", "filter": FILTER},
                      "bindings": [{"role": "roles/logging.viewAccessor", "members": [GH]}]}
    assert [IR.read_verb(c) for c in gcloud.calls] == ["describe", "get-iam-policy"]


def test_r3_the_job_record_is_typed_and_names_the_region():
    record = measure("run_job_iam", {"job": JOB}, Gcloud(policy(("roles/run.jobsExecutorWithOverrides", [GH]))))
    assert record == {"schema": "ky.iam_readback_probe/1", "status": "MEASURED", "probe": "run_job_iam", "measured_at": "2026-10-22T21:00:00Z", "project": "madhav-astrology",
                      "job": {"name": JOB, "region": "asia-south1"}, "bindings": [{"role": "roles/run.jobsExecutorWithOverrides", "members": [GH]}]}


# ───────────── R4 the project probe: ONE member, ONE role ─────────────

def project_policy():
    return policy(("roles/cloudsql.client", [RUNTIME, OTHER, PERSON]), ("roles/run.developer", [GH]), ("roles/owner", [PERSON]), ("roles/run.admin", [OTHER]))


def test_r4_held_is_true_for_the_one_member_and_role_and_nothing_else_is_printed():
    record = measure("project_iam_member_role", {"member": RUNTIME, "role": "roles/cloudsql.client"}, Gcloud(project_policy()))
    assert record == {"schema": "ky.iam_readback_probe/1", "status": "MEASURED", "probe": "project_iam_member_role", "measured_at": "2026-10-22T21:00:00Z", "project": "madhav-astrology",
                      "member": RUNTIME, "role": "roles/cloudsql.client", "held": True, "bindings": [{"role": "roles/cloudsql.client", "members": [RUNTIME]}]}
    text = json.dumps(record)
    assert OTHER not in text and PERSON not in text and "roles/owner" not in text and "roles/run.admin" not in text


def test_r4_held_is_false_when_the_member_lacks_the_role_even_if_it_holds_another():
    record = measure("project_iam_member_role", {"member": GH, "role": "roles/cloudsql.client"}, Gcloud(project_policy()))
    assert record["held"] is False and record["bindings"] == [] and record["status"] == "MEASURED"
    absent = measure("project_iam_member_role", {"member": GH, "role": "roles/never.granted"}, Gcloud(project_policy()))
    assert absent["held"] is False and absent["bindings"] == []


def test_r4_a_conditional_only_grant_of_the_member_refuses_but_another_members_condition_does_not():
    cond = policy(("roles/cloudsql.client", [OTHER]))
    cond["bindings"].append({"role": "roles/cloudsql.client", "members": [RUNTIME], "condition": {"title": "t", "expression": "true"}})
    assert "conditional" in refusal("project_iam_member_role", {"member": RUNTIME, "role": "roles/cloudsql.client"}, Gcloud(cond))
    record = measure("project_iam_member_role", {"member": GH, "role": "roles/cloudsql.client"}, Gcloud(cond))      # the condition guards another member: not this member's grant
    assert record["held"] is False
    both = copy.deepcopy(cond)
    both["bindings"].append({"role": "roles/cloudsql.client", "members": [RUNTIME]})
    assert measure("project_iam_member_role", {"member": RUNTIME, "role": "roles/cloudsql.client"}, Gcloud(both))["held"] is True       # an unconditional grant also exists


def test_r4_unrelated_conditional_bindings_of_the_project_policy_do_not_refuse():
    body = project_policy()
    body["bindings"].append({"role": "roles/storage.objectViewer", "members": [OTHER], "condition": {"title": "t", "expression": "true"}})
    assert measure("project_iam_member_role", {"member": RUNTIME, "role": "roles/cloudsql.client"}, Gcloud(body))["held"] is True


# ───────────── R5 an unreadable record refuses whole ─────────────

def test_r5_a_view_of_another_name_or_without_a_text_filter_or_with_an_unknown_field_refuses():
    ok = policy(("roles/logging.viewAccessor", [GH]))
    assert "not for the" in refusal("logging_view", {"view": VIEW}, Gcloud(view_body(name=VIEW_RESOURCE.replace(VIEW, "other_view")), ok))
    assert "not for the" in refusal("logging_view", {"view": VIEW}, Gcloud(view_body(name=VIEW_RESOURCE.replace("global", "us")), ok))
    for bad in (None, "", 5):
        assert "filter" in refusal("logging_view", {"view": VIEW}, Gcloud(view_body(filter=bad), ok))
    assert "does not know" in refusal("logging_view", {"view": VIEW}, Gcloud(view_body(extra="x"), ok))


@pytest.mark.parametrize("body,needle", [
    ({"bindings": [{"role": "roles/run.viewer", "members": [GH], "condition": {"title": "t"}}]}, "does not know"),
    ({"bindings": [{"role": "roles/run.viewer", "members": [GH], "extra": 1}]}, "does not know"),
    ({"bindings": [{"role": "roles/run.viewer", "members": [GH]}, {"role": "roles/run.viewer", "members": [OTHER]}]}, "bound twice"),
    ({"bindings": [{"role": "run.viewer", "members": [GH]}]}, "role"),
    ({"bindings": [{"role": 5, "members": [GH]}]}, "role"),
    ({"bindings": [{"role": "roles/run.viewer", "members": []}]}, "members"),
    ({"bindings": [{"role": "roles/run.viewer", "members": [5]}]}, "members"),
    ({"bindings": [{"role": "roles/run.viewer"}]}, "members"),
    ({"bindings": "x"}, "not a list"), ({"bindings": ["x"]}, "not an object"),
    ({"unexpectedField": 1}, "does not know"),
])
def test_r5_a_policy_that_cannot_be_read_as_what_it_claims_refuses(body, needle):
    assert needle in refusal("run_job_iam", {"job": JOB}, Gcloud(body))


def test_r5_gcloud_failure_non_json_and_non_object_output_refuse_without_relaying_stderr():
    for gcloud, needle in ((Gcloud(rc=1, raw="{}"), "exited 1"), (Gcloud(raw="not json"), "not JSON"), (Gcloud(raw="[]"), "not a JSON object")):
        message = refusal("run_job_iam", {"job": JOB}, gcloud)
        assert needle in message and "ya29" not in message and "victim@example" not in message

    def boom(argv):
        raise OSError("gcloud: command not found")
    with pytest.raises(IR.Refused, match="could not be run"):
        IR.measure("run_job_iam", {"job": JOB}, boom)


# ───────────── R6 receipt shape: the real validate and the real CLI ─────────────

REQ_ARGS = {"logging_view": {"probe": "logging_view", "view": VIEW}, "run_job_iam": {"probe": "run_job_iam", "job": JOB},
            "project_iam_member_role": {"probe": "project_iam_member_role", "member": RUNTIME, "role": "roles/cloudsql.client"},
            "secret_version_exists": {"probe": "secret_version_exists", "secret": SECRET}}


def _executor(tmp_path, monkeypatch):
    monkeypatch.setenv("KY_ROOT", str(tmp_path / "ky"))
    spec_ = importlib.util.spec_from_file_location(f"ky_exec_iamr_{abs(hash(str(tmp_path)))}", FLEET / "executor.py")
    module = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(module)
    return module


def _req(probe="run_job_iam", **over):
    req = {"operation_id": "op-iamr", "kind": "iam_readback", "item_id": "J-4c-a55m", "idempotency_key": "key-iamr", "requested_by": "adhikarin", "kyd": "kyd-1", "args": dict(REQ_ARGS[probe])}
    req.update(over)
    return req


def test_r6_table_entry_is_exact_read_only_production_false_and_the_real_validate_holds(tmp_path, monkeypatch):
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    entry = table["iam_readback"]
    assert list(entry)[0] == "enabled" and entry["enabled"] is True
    assert (entry["production"], entry["read_only"], entry["needs"], entry["fixed_args"]) == (False, True, "gcloud", [])
    assert entry["allowed_args"] == ["probe", "view", "job", "member", "role", "secret"]
    assert entry["script"] == "00_ARCHITECTURE/briefs/kalayantra/fleet/iam_readback.py" and (REPO / entry["script"]).is_file()
    assert entry["requesters"] == ["adhikarin", "v1", "v2"] and "also_needs" not in entry and "lease" not in json.dumps(entry)
    ex = _executor(tmp_path, monkeypatch)
    caps = {"gcloud": True}
    for probe in REQ_ARGS:
        assert ex.validate(_req(probe), table, caps) is None, probe
    assert "capability_missing" in ex.validate(_req(), table, {})
    assert "disallowed args" in ex.validate(_req(args={"probe": "run_job_iam", "job": JOB, "project": "other-project"}), table, caps)
    assert "disallowed args" in ex.validate(_req(args={"probe": "run_job_iam", "job": JOB, "region": "us-east1"}), table, caps)
    assert "unsafe" in ex.validate(_req(args={"probe": "run_job_iam", "job": "a b"}), table, caps)
    assert "may not request" in ex.validate(_req(requested_by="sutradhara"), table, caps)
    disabled = copy.deepcopy(table)
    disabled["iam_readback"]["enabled"] = False
    assert "is not enabled" in ex.validate(_req(), disabled, caps)


def _stub_gcloud(directory, responses=None):
    stub = directory / "gcloud"
    stub.write_text("#!/bin/sh\n"
                    f'echo "$@" >> "{directory}/calls.log"\n'
                    'echo "ERROR: noisy token ya29.LEAK for victim@example.invalid" >&2\n'
                    f'case "$*" in *"views describe"*) cat "{directory}/view.json";; *"views get-iam-policy"*) cat "{directory}/view_policy.json";; '
                    f'*"run jobs get-iam-policy"*) cat "{directory}/job_policy.json";; *"projects get-iam-policy"*) cat "{directory}/project_policy.json";; '
                    f'*"secrets versions list"*) cat "{directory}/secret_versions.json";; *"secrets describe"*) cat "{directory}/secret.json";; *) exit 9;; esac\n')
    stub.chmod(0o755)
    bodies = responses or {"view": view_body(), "view_policy": policy(("roles/logging.viewAccessor", [GH])),
                           "job_policy": policy(("roles/run.jobsExecutorWithOverrides", [GH])), "project_policy": project_policy(),
                           "secret": secret_body(), "secret_versions": [version_body(2, "DISABLED"), version_body(1, "ENABLED")]}
    for name, body in bodies.items():
        (directory / f"{name}.json").write_text(json.dumps(body))


def _run_cli(directory, extra):
    env = {"PATH": f"{directory}:/usr/bin:/bin", "HOME": str(directory)}
    return subprocess.run([sys.executable, "-I", str(SCRIPT), *extra], capture_output=True, text=True, env=env, cwd=directory)


def test_r6_cli_prints_one_line_record_for_each_probe_and_calls_only_the_fixed_reads(tmp_path):
    _stub_gcloud(tmp_path)
    expected_calls = {"logging_view": [["logging", "views", "describe", VIEW, *LOG_FLAGS], ["logging", "views", "get-iam-policy", VIEW, *LOG_FLAGS]],
                      "run_job_iam": [["run", "jobs", "get-iam-policy", JOB, "--region=asia-south1", "--project=madhav-astrology", "--format=json"]],
                      "project_iam_member_role": [["projects", "get-iam-policy", "madhav-astrology", "--format=json"]],
                      "secret_version_exists": [["secrets", "describe", SECRET, "--project=madhav-astrology", "--format=json"],
                                                ["secrets", "versions", "list", SECRET, "--project=madhav-astrology", "--format=json"]]}
    for probe, extra in REQ_ARGS.items():
        argv = [x for k, v in extra.items() for x in (f"--{k}", v)]
        calls = tmp_path / "calls.log"
        calls.unlink(missing_ok=True)
        done = _run_cli(tmp_path, argv)
        assert done.returncode == 0, done.stdout + done.stderr
        assert "ya29" not in done.stdout + done.stderr and "victim@example" not in done.stdout + done.stderr
        assert len(done.stdout.strip().splitlines()) == 1
        record = json.loads(done.stdout)
        assert record["schema"] == "ky.iam_readback_probe/1" and record["status"] == "MEASURED" and record["probe"] == probe and record["project"] == "madhav-astrology"
        assert record["measured_at"].endswith("Z") and isinstance(record.get("bindings", record.get("versions")), list)
        assert [c.split() for c in calls.read_text().splitlines()] == expected_calls[probe]
        if probe == "project_iam_member_role":
            assert PERSON not in done.stdout and OTHER not in done.stdout and "roles/owner" not in done.stdout       # the stub's project policy lists them; the filter must not print them


def test_r6_cli_refuses_with_exit_1_and_one_refused_line_that_carries_no_partial_evidence(tmp_path):
    _stub_gcloud(tmp_path, {"job_policy": policy(("roles/run.viewer", [GH]), ("roles/run.viewer", [OTHER]))})
    done = _run_cli(tmp_path, ["--probe", "run_job_iam", "--job", JOB])
    assert done.returncode == 1 and len(done.stdout.strip().splitlines()) == 1
    record = json.loads(done.stdout)
    assert record["status"] == "REFUSED" and record["probe"] == "run_job_iam" and "bindings" not in record and "ya29" not in done.stdout + done.stderr
    assert set(record) == {"schema", "status", "probe", "reason"}


def test_r6_a_view_that_does_not_exist_is_a_gcloud_failure_and_a_refused_record(tmp_path):
    _stub_gcloud(tmp_path)
    (tmp_path / "gcloud").write_text("#!/bin/sh\necho 'ERROR: NOT_FOUND victim@example.invalid' >&2\nexit 1\n")
    done = _run_cli(tmp_path, ["--probe", "logging_view", "--view", "no_such_view"])
    assert done.returncode == 1 and json.loads(done.stdout)["status"] == "REFUSED" and "victim" not in done.stdout + done.stderr


# ───────────── R7 the J-4c-a55m pass conditions are decidable from the records ─────────────

def test_r7_the_three_act_pass_conditions_read_off_the_records():
    view = measure("logging_view", {"view": VIEW}, Gcloud(view_body(), policy(("roles/logging.viewAccessor", [GH]))))
    assert 'job_name="gochara-verification-job"' in view["view"]["filter"]
    assert view["bindings"] == [{"role": "roles/logging.viewAccessor", "members": [GH]}]                  # exactly one binding, exactly one member
    job = measure("run_job_iam", {"job": JOB}, Gcloud(policy(("roles/run.jobsExecutorWithOverrides", [GH]))))
    assert any(b["role"] == "roles/run.jobsExecutorWithOverrides" and GH in b["members"] for b in job["bindings"])
    project = measure("project_iam_member_role", {"member": RUNTIME, "role": "roles/cloudsql.client"}, Gcloud(project_policy()))
    assert project["held"] is True
    two = measure("logging_view", {"view": VIEW}, Gcloud(view_body(), policy(("roles/logging.viewAccessor", [GH]), ("roles/logging.admin", [OTHER]))))
    assert len(two["bindings"]) == 2                                                                      # an extra binding is visible, so "exactly one" can read false


# ───────────── R8 the secret probe: metadata only, never the payload ─────────────

def test_r8_the_builder_cannot_emit_access_and_a_planted_versions_access_is_refused_before_the_runner(monkeypatch):
    emitted = [IR.build_command(c, {"secret": SECRET}) for c in IR.CALLS_OF["secret_version_exists"]]
    assert all("access" not in cmd and IR.read_verb(cmd) in {"describe", "list"} for cmd in emitted) and "access" not in IR.READ_VERBS
    for planted in (["gcloud", "secrets", "versions", "access", "latest", f"--secret={SECRET}", "--project=madhav-astrology"],
                    ["gcloud", "secrets", "versions", "access", "1", f"--secret={SECRET}", "--project=madhav-astrology"],
                    ["gcloud", "secrets", "versions", "list", "access", "--project=madhav-astrology", "--format=json"],      # the word hidden in a resource position
                    ["gcloud", "secrets", "versions", "list", SECRET, "--project=madhav-astrology", "--format=json", "access"]):
        gcloud = Gcloud(secret_body())
        with pytest.raises(IR.Refused):
            IR.gcloud_json(planted, gcloud, "planted")
        assert gcloud.calls == []
    shapes = dict(IR.CALL_SHAPES)
    shapes["secret_versions"] = ("gcloud", "secrets", "versions", "access", "latest", "--secret={secret}", f"--project={IR.PROJECT}", "--format=json")
    monkeypatch.setattr(IR, "CALL_SHAPES", shapes)
    gcloud = Gcloud(secret_body(), [])
    assert IR.cli(["--probe", "secret_version_exists", "--secret", SECRET], runner=gcloud) == 1
    assert all(IR.read_verb(c) != "access" for c in gcloud.calls) and len(gcloud.calls) <= 1       # the describe may have run; the access never reached the runner


def test_r8_other_secret_verbs_are_refused_too(monkeypatch):
    for verb in ("add", "destroy", "disable", "enable", "delete", "set-iam-policy", "create", "update"):
        bad = ["gcloud", "secrets", "versions", verb, SECRET, "--project=madhav-astrology", "--format=json"]
        with pytest.raises(IR.Refused, match="not a read"):
            IR.gcloud_json(bad, Gcloud(), "planted")


def test_r8_the_record_is_metadata_only_typed_and_versions_sorted_by_number():
    gcloud = Gcloud(secret_body(annotations={"note": "private"}), [version_body(10, "DESTROYED"), version_body(2, "DISABLED", "2026-10-21T01:00:00Z"), version_body(9)])
    record = measure("secret_version_exists", {"secret": SECRET}, gcloud)
    assert record == {"schema": "ky.iam_readback_probe/1", "status": "MEASURED", "probe": "secret_version_exists", "measured_at": "2026-10-22T21:00:00Z", "project": "madhav-astrology",
                      "secret": {"name": SECRET, "exists": True, "create_time": "2026-10-20T01:00:00.000000Z", "labels": {"owner": "kalayantra", "used-by": "seal"},
                                 "replication": {"automatic": {}}},
                      "versions": [{"version": 2, "state": "DISABLED", "create_time": "2026-10-21T01:00:00Z"}, {"version": 9, "state": "ENABLED", "create_time": "2026-10-21T02:00:00.000000Z"},
                                   {"version": 10, "state": "DESTROYED", "create_time": "2026-10-21T02:00:00.000000Z"}]}
    text = json.dumps(record)
    assert "private" not in text and "payload" not in text and "etag" not in text and "replicationStatus" not in text
    assert [IR.read_verb(c) for c in gcloud.calls] == ["describe", "list"]


def test_r8_a_secret_with_no_versions_and_no_labels_is_a_measured_zero():
    body = secret_body()
    del body["labels"]
    record = measure("secret_version_exists", {"secret": SECRET}, Gcloud(body, []))
    assert record["status"] == "MEASURED" and record["versions"] == [] and record["secret"]["labels"] == {} and record["secret"]["exists"] is True


class NotFound:
    def __init__(self, stderr):
        self.stderr, self.calls = stderr, []

    def __call__(self, argv):
        self.calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr=self.stderr)


def test_r8_not_found_is_a_measured_absence_and_any_other_failure_refuses():
    absent = NotFound("ERROR: (gcloud.secrets.describe) NOT_FOUND: Secret [projects/1/secrets/gochara-sealer-db-url] not found victim@example.invalid ya29.LEAK")
    record = measure("secret_version_exists", {"secret": SECRET}, absent)
    assert record["status"] == "MEASURED" and record["secret"] == {"name": SECRET, "exists": False} and record["versions"] == [] and len(absent.calls) == 1
    assert "ya29" not in json.dumps(record) and "victim" not in json.dumps(record)
    for stderr in ("ERROR: PERMISSION_DENIED: Permission denied; NOT_FOUND may also apply", "ERROR: UNAVAILABLE", "", "ERROR: the gcloud binary is broken"):
        message = refusal("secret_version_exists", {"secret": SECRET}, NotFound(stderr))
        assert "exited 1" in message and "ya29" not in message
    # a failing version list after a described secret is never an absence
    assert "exited 1" in refusal("secret_version_exists", {"secret": SECRET}, SeqGcloud([(0, json.dumps(secret_body())), (1, "")], stderr="NOT_FOUND"))


class SeqGcloud:
    def __init__(self, steps, stderr=""):
        self.steps, self.stderr, self.calls = list(steps), stderr, []

    def __call__(self, argv):
        code, out = self.steps[len(self.calls)]
        self.calls.append(list(argv))
        return subprocess.CompletedProcess(argv, code, stdout=out, stderr=self.stderr)


@pytest.mark.parametrize("secret,versions,needle", [
    (secret_body(extra=1), [], "does not know"),
    (secret_body(name=f"projects/1/secrets/other-secret"), [], "not for the secret"),
    (secret_body(name=SECRET), [], "not for the secret"),
    (secret_body(createTime=None), [], "createTime"),
    (secret_body(labels={"a": 1}), [], "labels"),
    (secret_body(replication=None), [], "replication"),
    (secret_body(), [version_body(1, extra=1)], "does not know"),
    (secret_body(), [version_body(1, "STATE_UNSPECIFIED")], "state"),
    (secret_body(), [version_body(1, None)], "state"),
    (secret_body(), [version_body(1, create=None)], "createTime"),
    (secret_body(), [version_body(1), version_body(1, "DISABLED")], "listed twice"),
    (secret_body(), [{**version_body(1), "name": "projects/1/secrets/other-secret/versions/1"}], "not of the secret"),
    (secret_body(), [{**version_body(1), "name": f"projects/1/secrets/{SECRET}/versions/latest"}], "not of the secret"),
    (secret_body(), ["x"], "not an object"),
])
def test_r8_a_secret_record_that_cannot_be_read_as_what_it_claims_refuses_whole(secret, versions, needle):
    assert needle in refusal("secret_version_exists", {"secret": SECRET}, Gcloud(secret, versions))


def test_r8_the_version_list_must_be_a_list_and_the_describe_an_object():
    assert "not a JSON list" in refusal("secret_version_exists", {"secret": SECRET}, Gcloud(secret_body(), {}))
    assert "not a JSON object" in refusal("secret_version_exists", {"secret": SECRET}, Gcloud([]))


def test_r8_the_c7_detector_reads_off_the_record_whether_an_enabled_version_exists():
    record = measure("secret_version_exists", {"secret": SECRET}, Gcloud(secret_body(), [version_body(1, "DESTROYED"), version_body(2, "ENABLED")]))
    assert any(v["state"] == "ENABLED" for v in record["versions"])
    none_enabled = measure("secret_version_exists", {"secret": SECRET}, Gcloud(secret_body(), [version_body(1, "DESTROYED"), version_body(2, "DISABLED")]))
    assert not any(v["state"] == "ENABLED" for v in none_enabled["versions"])                      # "an enabled version exists" can read false
