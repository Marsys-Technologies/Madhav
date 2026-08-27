"""Static release-order assurance for the sidecar candidate deployment."""
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "deploy.yml"


def _sidecar_job() -> str:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    return workflow.split("  deploy-sidecar:", 1)[1].split("  deploy-mcp:", 1)[0]


def test_pr_build_check_packages_the_regular_serving_sidecar():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    build_check = workflow.split("  build-check:", 1)[1].split("  changes:", 1)[0]
    assert "Build regular sidecar image (load, no push)" in build_check
    assert "file: ./platform/python-sidecar/Dockerfile" in build_check
    assert "push: false" in build_check
    assert "load: true" in build_check


def test_candidate_probes_complete_before_exact_revision_promotion():
    job = _sidecar_job()
    deploy = job.index("Deploy sidecar candidate to Cloud Run (zero traffic)")
    no_traffic = job.index("--no-traffic", deploy)
    configure = job.index("Configure authenticated candidate smoke job", no_traffic)
    execute = job.index("Run authenticated real probes against candidate", configure)
    promote = job.index("Promote verified sidecar candidate", execute)
    assert deploy < no_traffic < configure < execute < promote
    assert '--to-revisions="$EXPECTED_REVISION=100"' in job[promote:]


def test_candidate_smoke_uses_secret_mount_without_runner_plaintext_access():
    job = _sidecar_job()
    assert "--set-secrets=PYTHON_SIDECAR_API_KEY=PYTHON_SIDECAR_API_KEY:1" in job
    assert "gcloud secrets versions access" not in job
    assert "amjis-sidecar-runtime@madhav-astrology.iam.gserviceaccount.com" in job
