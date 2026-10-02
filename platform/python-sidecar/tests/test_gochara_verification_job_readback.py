"""The #2976 definition readback (Codex R13-3): a deployed job that is not EXACTLY the act-6 definition is refused, reason by reason."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
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
                                      "containers": [{"image": f"{REPO}@{DIG}", "command": list(rb.ENTRYPOINT),
                                                      "resources": {"limits": {"memory": "8Gi", "cpu": "2"}},
                                                      "env": [{"name": "GOCHARA_RUNNER_COMMIT", "value": SHA},
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
    (lambda j: task(j).update(serviceAccountName="github-actions@madhav-astrology.iam.gserviceaccount.com"), "service account"),
    (lambda j: task(j)["containers"][0].update(command=["python", "-m", "pipeline.orchestrator.main"]), "command"),  # the builder entry point
    (lambda j: task(j)["containers"][0].update(args=["--chart", "x"]), "args"),
    (lambda j: task(j)["containers"][0]["env"].append({"name": "DATABASE_URL", "value": "x"}), "environment variables"),
    (lambda j: task(j)["containers"][0]["env"].pop(), "environment variables"),
    (lambda j: task(j)["containers"][0]["env"][0].update(value="c" * 40), "RUNNER_COMMIT"),
    (lambda j: task(j)["containers"][0]["env"][1].update(valueFrom={"secretKeyRef": {"name": "data-plane-builder-db-url"}}), "reference to the secret"),
    (lambda j: j["spec"]["template"]["metadata"]["annotations"].update({"run.googleapis.com/cloudsql-instances": INST + ",other:r:i"}), "Cloud SQL"),
    (lambda j: j["spec"]["template"]["metadata"]["annotations"].clear(), "Cloud SQL"),
    (lambda j: j["spec"]["template"]["spec"].update(taskCount=3), "taskCount"),
    (lambda j: task(j).update(maxRetries=3), "maxRetries"),
    (lambda j: task(j).pop("maxRetries"), "maxRetries"),                                                                # absent = the API default (3)
    (lambda j: task(j).update(timeoutSeconds=60), "timeoutSeconds"),
    (lambda j: task(j)["containers"][0]["resources"]["limits"].update(memory="1Gi"), "resource limits"),
])
def test_a_definition_that_is_not_exactly_act_6_is_refused(fn, needle):
    bad = run(edit(fn))
    assert bad and any(needle in b for b in bad), bad


def test_an_unexpected_shape_is_refused_never_passed():
    with pytest.raises(rb.Refused, match="unexpected Job resource shape"):
        run({"spec": {"template": {"spec": {}}}})
    with pytest.raises(rb.Refused, match="not exactly one"):
        run(edit(lambda j: task(j).update(containers=[])))
    with pytest.raises(rb.Refused, match="malformed"):
        rb.check(job(), image_repo=REPO, image_digest="latest", service_account=SA, runner_commit=SHA, secret_name="s", cloudsql_instance=INST, timeout_seconds=1, memory="1", cpu="1")
