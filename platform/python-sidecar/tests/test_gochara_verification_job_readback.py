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
                                      "serviceAccountName": SA, "maxRetries": 0, "timeoutSeconds": 7200,
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


# R14-3: the verification-job contract is ONE file carried by BOTH #2975 (executed-resource check) and #2976 (definition readback). If the two copies ever diverge, one of these two tests fails
# (the pinned digest is the same constant in both PRs; change it in both when the contract is deliberately changed).
CONTRACT_SHA256 = "3cd8ece1dcb0427b1436996b9c1aec6f7eb6509c951bb903398f7474b6a726fd"


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
