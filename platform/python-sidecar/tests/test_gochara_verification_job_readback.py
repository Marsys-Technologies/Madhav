"""The #2976 definition readback (Codex R13-3): a deployed job that is not EXACTLY the act-6 definition is refused, reason by reason."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import gochara_verification_job_contract as vjc  # noqa: E402
import gochara_verification_job_readback as rb  # noqa: E402

REPO = "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline"
DIG = "sha256:" + "a" * 64
SHA = "b" * 40
SA = "gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com"
INST = "madhav-astrology:asia-south1:amjis-postgres"


def job():
    return {"metadata": {"name": "gochara-verification-job"},
            "spec": {"template": {"metadata": {"annotations": {"run.googleapis.com/cloudsql-instances": INST}},
                                  "spec": {"taskCount": 1, "template": {"spec": {
                                      "serviceAccountName": SA, "maxRetries": 0, "timeoutSeconds": "7200",     # int64 arrives as a decimal STRING (API/SDK shape)
                                      "containers": [{"image": f"{REPO}@{DIG}", "command": list(vjc.ENTRYPOINT),
                                                      "resources": {"limits": {"memory": "8Gi", "cpu": "2"}},
                                                      "env": [{"name": "GOCHARA_RUNNER_COMMIT", "value": SHA}, {"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": DIG},
                                                              {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"name": "gochara-verifier-db-url", "key": "latest"}}}]}]}}}}}}


def run(j=None):
    return rb.check(job() if j is None else j, image_repo=REPO, image_digest=DIG, service_account=SA, runner_commit=SHA, secret_name="gochara-verifier-db-url",
                    cloudsql_instance=INST, timeout_seconds=7200, memory="8Gi", cpu="2")


def edit(fn):
    j = copy.deepcopy(job())
    fn(j)
    return j


def task(j):
    return j["spec"]["template"]["spec"]["template"]["spec"]


def test_the_exact_definition_is_accepted():
    assert run() == []


@pytest.mark.parametrize("fn,needle", [
    (lambda j: task(j)["containers"][0].update(image=f"{REPO}:{SHA}"), "image is"),                                  # a tag
    (lambda j: task(j)["containers"][0].update(image=f"{REPO}@sha256:{'c' * 64}"), "image is"),                      # another digest
    (lambda j: task(j).update(serviceAccountName="github-actions@madhav-astrology.iam.gserviceaccount.com"), "service account is"),
    (lambda j: task(j)["containers"][0].update(command=["python", "-m", "pipeline.orchestrator.main"]), "command"),  # the builder entry point
    (lambda j: task(j)["containers"][0].update(args=["--chart", "x"]), "args"),
    (lambda j: task(j)["containers"][0]["env"].append({"name": "DATABASE_URL", "value": "x"}), "environment variables"),
    (lambda j: task(j)["containers"][0]["env"].pop(), "environment variables"),
    (lambda j: task(j)["containers"][0]["env"][0].update(value="c" * 40), "plain value"),
    (lambda j: task(j)["containers"][0]["env"][1].update(value="sha256:" + "c" * 64), "plain value"),
    (lambda j: task(j)["containers"][0]["env"].pop(1), "environment variables"),
    (lambda j: task(j)["containers"][0]["env"][2].update(valueFrom={"secretKeyRef": {"name": "data-plane-builder-db-url"}}), "reference to the secret"),
    (lambda j: j["spec"]["template"]["metadata"]["annotations"].update({"run.googleapis.com/cloudsql-instances": INST + ",other:r:i"}), "Cloud SQL"),
    (lambda j: j["spec"]["template"]["metadata"]["annotations"].clear(), "Cloud SQL"),
    (lambda j: j["spec"]["template"]["spec"].update(taskCount=3), "taskCount"),
    (lambda j: task(j).update(maxRetries=3), "maxRetries"),
    (lambda j: task(j)["containers"][0].update(command=None), "command"),
    (lambda j: task(j)["containers"][0].update(volumeMounts=[{"name": "s", "mountPath": "/s"}]), "volumeMounts"),
    (lambda j: task(j)["containers"][0].update(envFrom=[{"secretRef": {"name": "x"}}]), "envFrom"),
    (lambda j: task(j).update(volumes=[{"name": "s", "secret": {"secretName": "x"}}]), "volumes"),
    (lambda j: task(j).pop("maxRetries"), "maxRetries"),                                                                # absent = the API default (3)
    (lambda j: task(j).update(timeoutSeconds=60), "timeoutSeconds"),
    (lambda j: task(j)["containers"][0]["resources"]["limits"].update(memory="1Gi"), "memory limit"),
])
def test_a_definition_that_is_not_exactly_act_6_is_refused(fn, needle):
    bad = run(edit(fn))
    assert bad and any(needle in b for b in bad), bad


def test_an_unexpected_shape_is_refused_never_passed():
    with pytest.raises(rb.Refused, match="unexpected Job resource shape"):
        run({"spec": {"template": {"spec": {}}}})
    bad = run(edit(lambda j: task(j).update(containers=[])))
    assert any("not exactly one" in b for b in bad), bad
    with pytest.raises(rb.Refused, match="malformed"):
        rb.check(job(), image_repo=REPO, image_digest="latest", service_account=SA, runner_commit=SHA, secret_name="s", cloudsql_instance=INST, timeout_seconds=1, memory="1", cpu="1")


@pytest.mark.parametrize("ok", ["7200", 7200])
def test_a_documented_int64_string_or_integer_timeout_is_accepted(ok):
    assert run(edit(lambda j: task(j).update(timeoutSeconds=ok))) == []


@pytest.mark.parametrize("bad", [True, "7200.0", 7200.5, float("inf"), float("nan"), " 7200", "+7200", "07200", "7200s", "", None, "7e3", 60, "60"])
def test_a_timeout_that_is_not_exactly_the_deployed_value_is_refused(bad):
    assert any("timeoutSeconds" in b for b in run(edit(lambda j: task(j).update(timeoutSeconds=bad))))


def test_an_absent_timeout_is_refused_not_defaulted():
    assert any("timeoutSeconds" in b for b in run(edit(lambda j: task(j).pop("timeoutSeconds"))))


@pytest.mark.parametrize("lim", [{"memory": "8192Mi", "cpu": "2000m"}, {"memory": "8Gi", "cpu": "2"}])
def test_equivalent_quantity_spellings_are_accepted_by_value(lim):
    assert run(edit(lambda j: task(j)["containers"][0]["resources"].update(limits=lim))) == []


@pytest.mark.parametrize("lim", [{"memory": "8Gi", "cpu": 2}, {"memory": 8589934592, "cpu": "2"}, {"memory": "8gi", "cpu": "2"}, {"memory": "8Gi", "cpu": "2.0"}, {"memory": "8Gi", "cpu": "1"}, {"memory": "8Gi"}])
def test_a_quantity_that_is_not_canonical_or_not_equal_is_refused(lim):
    assert any("limit" in b for b in run(edit(lambda j: task(j)["containers"][0]["resources"].update(limits=lim))))


def test_taskcount_as_a_decimal_string_is_normalised_and_a_malformed_one_is_refused():
    assert run(edit(lambda j: j["spec"]["template"]["spec"].update(taskCount="1"))) == []
    assert any("taskCount" in b for b in run(edit(lambda j: j["spec"]["template"]["spec"].update(taskCount="1.0"))))


@pytest.mark.parametrize("value", ["gochara-verifier-db-url:projects/foreign-project/secrets/another-database",                 # the foreign-project alias
                                   "gochara-verifier-db-url:projects/madhav-astrology/secrets/another-database",                # same project, different secret
                                   "gochara-verifier-db-url:projects/madhav-astrology/secrets/gochara-verifier-db-url",         # self-referential: still the forbidden mechanism
                                   "gochara-verifier-db-url:projects/1/secrets/a,gochara-verifier-db-url:projects/2/secrets/b",  # duplicate / conflicting aliases
                                   ""])
def test_the_secret_remapping_annotation_is_refused_on_the_definition_and_on_the_v2_read(value):
    ann = "run.googleapis.com/secrets"
    assert any("secrets-mapping annotation" in b for b in run(edit(lambda j: j["spec"]["template"]["metadata"]["annotations"].update({ann: value}))))
    kw = dict(image_repo=REPO, image_digest=DIG, service_account=SA, runner_commit=SHA, secret_name="gochara-verifier-db-url", cloudsql_instance=INST, timeout_seconds=7200, memory="8Gi", cpu="2")
    assert any("secrets-mapping annotation" in b for b in rb.check(job(), v2_job={"template": {"template": {"maxRetries": 0}}, "annotations": {ann: value}}, **kw))


@pytest.mark.parametrize("ref", [{"name": "gochara-verifier-db-url"}, {"name": "gochara-verifier-db-url", "key": "1"}, {"name": "gochara-verifier-db-url", "key": ""},
                                 {"name": "gochara-verifier-db-url", "key": "latest", "optional": True}, {"name": "projects/foreign-project/secrets/gochara-verifier-db-url", "key": "latest"}])
def test_the_secret_selector_must_be_exactly_name_and_latest(ref):
    bad = run(edit(lambda j: task(j)["containers"][0]["env"][2].update(valueFrom={"secretKeyRef": ref})))
    assert any("reference to the secret" in b for b in bad), bad


@pytest.mark.parametrize("bad", [False, True, "garbage", "07", "-1", -1, 2**63, "9223372036854775808", 1.5, [], {}])
def test_an_invalid_present_v2_retries_value_refuses_even_when_v1_is_a_valid_zero(bad):
    kw = dict(image_repo=REPO, image_digest=DIG, service_account=SA, runner_commit=SHA, secret_name="gochara-verifier-db-url", cloudsql_instance=INST, timeout_seconds=7200, memory="8Gi", cpu="2")
    assert vjc.retries_from_v2({"template": {"template": {"maxRetries": bad}}}, "job") is vjc.INVALID
    assert any("not a valid non-negative integer" in b for b in rb.check(job(), v2_job={"template": {"template": {"maxRetries": bad}}}, **kw))


def test_absent_is_not_invalid_and_a_non_object_v2_document_is_invalid():
    assert vjc.retries_from_v2({}, "job") is None and vjc.retries_from_v2({"template": {"template": {}}}, "job") is None
    assert vjc.retries_from_v2([], "job") is vjc.INVALID and vjc.retries_from_v2({"template": 3}, "job") is vjc.INVALID


def test_the_int64_domain_is_non_negative_and_bounded():
    assert vjc.parse_int64("9223372036854775807") == 2**63 - 1 and vjc.parse_int64(0) == 0
    assert all(vjc.parse_int64(v) is None for v in (-1, "-1", 2**63, "9223372036854775808", True, "00", 1.0))


# R14-3: the verification-job contract is ONE file carried by BOTH #2975 (executed-resource check) and #2976 (definition readback). If the two copies ever diverge, one of these two tests fails
# (the pinned digest is the same constant in both PRs; change it in both when the contract is deliberately changed).
CONTRACT_SHA256 = "caf6fe767682c9699c12bfe9d91753ecc50400500eb267e7999639ac7d51311f"


def test_the_shared_verification_job_contract_is_the_file_both_prs_carry():
    import hashlib
    import gochara_verification_job_contract as _vjc
    assert hashlib.sha256(Path(_vjc.__file__).read_bytes()).hexdigest() == CONTRACT_SHA256


def test_maxretries_absent_in_v1_is_accepted_only_when_the_v2_representation_carries_a_zero():
    """F-R15-3: v1 may omit a proto3 zero; the v2 REST representation carries `maxRetries` as a union member. Absence is NEVER read as 0."""
    def v1_absent():
        j = copy.deepcopy(job())
        task(j).pop("maxRetries")
        return j
    kw = dict(image_repo=REPO, image_digest=DIG, service_account=SA, runner_commit=SHA, secret_name="gochara-verifier-db-url", cloudsql_instance=INST, timeout_seconds=7200, memory="8Gi", cpu="2")
    assert rb.check(v1_absent(), v2_job={"template": {"template": {"maxRetries": 0}}}, **kw) == []
    assert any("maxRetries" in b for b in rb.check(v1_absent(), v2_job={"template": {"template": {}}}, **kw))               # absent in BOTH
    assert any("maxRetries" in b for b in rb.check(v1_absent(), v2_job={"template": {"template": {"maxRetries": 3}}}, **kw))
    assert any("disagrees" in b for b in rb.check(job(), v2_job={"template": {"template": {"maxRetries": 3}}}, **kw))
    assert any("maxRetries" in b for b in rb.check(v1_absent(), **kw))                                                      # no v2 supplied: strict v1 rule stands
