"""Keep the legacy private preview out of ordinary Python and Web build contexts."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
PREVIEW = Path("platform/python-sidecar/brahmagyan/mimamsa/bigquery_export_preview.jsonl")
PIPELINE = Path("platform/python-sidecar/Dockerfile.pipeline")


def patterns(ignore_file: Path) -> list[str]:
    if not ignore_file.is_file():
        return []
    return [
        line for line in map(str.strip, ignore_file.read_text().splitlines())
        if line and not line.startswith("#")
    ]


@pytest.mark.parametrize(("context", "dockerfile", "deploy_job"), [
    (Path("."), PIPELINE, "deploy-pipeline-job"),
    (Path("platform"), Path("platform/python-sidecar/Dockerfile"), "deploy-sidecar"),
    (Path("platform"), Path("platform/Dockerfile"), "deploy-web"),
])
def test_preview_is_excluded_from_normal_build_context(context, dockerfile, deploy_job):
    jobs = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())["jobs"]
    for name in ("build-check", deploy_job):
        contexts = [
            Path(step["with"]["context"])
            for step in jobs[name]["steps"]
            if step.get("uses", "").startswith("docker/build-push-action@")
            and Path(step.get("with", {}).get("file", "")) == dockerfile
        ]
        assert contexts == [context], (name, dockerfile)

    context_patterns = patterns(ROOT / context / ".dockerignore")
    specific = ROOT / dockerfile.with_name(dockerfile.name + ".dockerignore")
    if dockerfile == PIPELINE:
        assert specific.is_file()

    effective_patterns = context_patterns
    if specific.is_file():
        effective_patterns = patterns(specific)
        assert effective_patterns[:len(context_patterns)] == context_patterns

    preview = PREVIEW.relative_to(context).as_posix()
    last_exclusion = max((index for index, rule in enumerate(effective_patterns) if rule == preview), default=-1)
    assert last_exclusion >= 0
    # A later negation can re-include the preview through a wildcard.
    later_negations = [rule for rule in effective_patterns[last_exclusion + 1:] if rule.startswith("!")]
    assert not later_negations
