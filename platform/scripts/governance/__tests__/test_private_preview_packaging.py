"""Keep the legacy private preview out of ordinary Python and Web build contexts."""

from collections import Counter
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
PREVIEW = Path("platform/python-sidecar/brahmagyan/mimamsa/bigquery_export_preview.jsonl")
PIPELINE = Path("platform/python-sidecar/Dockerfile.pipeline")
SIDECAR = Path("platform/python-sidecar/Dockerfile")
WEB = Path("platform/Dockerfile")

CGM_ACTION = "./.github/actions/build-verified-cgm-image"
DIRECT_BUILD = "docker/build-push-action@"
OUTER_BUILDS = {
    "build-check": [(DIRECT_BUILD, WEB), (CGM_ACTION, SIDECAR), (CGM_ACTION, PIPELINE)],
    "deploy-web": [(DIRECT_BUILD, WEB)],
    "deploy-sidecar": [(CGM_ACTION, SIDECAR)],
    "deploy-pipeline-job": [(CGM_ACTION, PIPELINE)],
}
BUILD_INPUTS = ("context", "file", "push", "load", "tags", "cache-from", "cache-to")


def assert_exact_cgm_delegate(action: dict) -> None:
    assert set(action["inputs"]) == set(BUILD_INPUTS)
    assert action["inputs"]["push"]["default"] == "false"
    assert action["inputs"]["load"]["default"] == "false"
    assert action["runs"]["using"] == "composite"
    delegate, probe = action["runs"]["steps"]
    assert delegate == {
        "id": "build",
        "uses": "docker/build-push-action@v6",
        "with": {key: "${{ inputs." + key + " }}" for key in BUILD_INPUTS},
    }
    assert "uses" not in probe and "if" not in probe and "continue-on-error" not in probe
    assert probe["run"] == 'python3 "$GITHUB_ACTION_PATH/probe_registration.py" verify-build'


def assert_outer_build_inventory(job: str, steps: list[dict]) -> None:
    actual = []
    for step in steps:
        uses = step.get("uses", "")
        if uses.startswith(DIRECT_BUILD):
            uses = DIRECT_BUILD
        if uses in (DIRECT_BUILD, CGM_ACTION):
            actual.append((uses, Path(step.get("with", {}).get("file", ""))))
    assert Counter(actual) == Counter(OUTER_BUILDS[job]), (job, actual)


def effective_contexts(steps: list[dict], dockerfile: Path, builder: str) -> list[Path]:
    contexts = []
    for step in steps:
        inputs = step.get("with", {})
        if Path(inputs.get("file", "")) != dockerfile:
            continue
        assert "if" not in step and "continue-on-error" not in step
        if builder == CGM_ACTION:
            assert step.get("uses") == builder
            assert set(inputs) <= set(BUILD_INPUTS)
        else:
            assert step.get("uses", "").startswith(builder)
        contexts.append(Path(inputs["context"]))
    return contexts


def patterns(ignore_file: Path) -> list[str]:
    if not ignore_file.is_file():
        return []
    return [
        line for line in map(str.strip, ignore_file.read_text().splitlines())
        if line and not line.startswith("#")
    ]


@pytest.mark.parametrize(("context", "dockerfile", "deploy_job"), [
    (Path("."), PIPELINE, "deploy-pipeline-job"),
    (Path("platform"), SIDECAR, "deploy-sidecar"),
    (Path("platform"), WEB, "deploy-web"),
])
def test_preview_is_excluded_from_normal_build_context(context, dockerfile, deploy_job):
    jobs = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())["jobs"]
    builder = DIRECT_BUILD
    if deploy_job != "deploy-web":
        builder = CGM_ACTION
        assert_exact_cgm_delegate(yaml.safe_load((ROOT / builder / "action.yml").read_text()))
    for name in ("build-check", deploy_job):
        steps = jobs[name]["steps"]
        assert_outer_build_inventory(name, steps)
        assert effective_contexts(steps, dockerfile, builder) == [context], (name, dockerfile)

    assert_preview_exclusion(ROOT, context, dockerfile)


def assert_preview_exclusion(root: Path, context: Path, dockerfile: Path) -> None:
    context_patterns = patterns(root / context / ".dockerignore")
    specific = root / dockerfile.with_name(dockerfile.name + ".dockerignore")
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


@pytest.mark.parametrize("change", ["context", "file", "load", "push", "cache-to", "if", "extra-builder"])
def test_preview_guard_rejects_composite_build_bypass(change):
    action = yaml.safe_load((ROOT / CGM_ACTION / "action.yml").read_text())
    delegate = action["runs"]["steps"][0]
    if change == "extra-builder":
        action["runs"]["steps"].append(delegate)
    elif change == "if":
        delegate["if"] = "false"
    else:
        delegate["with"][change] = "wrong"
    with pytest.raises((AssertionError, ValueError)):
        assert_exact_cgm_delegate(action)


@pytest.mark.parametrize("mutation", [None, "missing-specific", "wrong-precedence", "reinclude"])
def test_pipeline_effective_ignore_still_refuses_preview(tmp_path, mutation):
    context_ignore = tmp_path / ".dockerignore"
    context_ignore.write_text("node_modules\n")
    specific = tmp_path / PIPELINE.with_name(PIPELINE.name + ".dockerignore")
    specific.parent.mkdir(parents=True)
    if mutation != "missing-specific":
        prefix = "" if mutation == "wrong-precedence" else "node_modules\n"
        suffix = "!**/*.jsonl\n" if mutation == "reinclude" else ""
        specific.write_text(f"{prefix}{PREVIEW.as_posix()}\n{suffix}")
    if mutation:
        with pytest.raises(AssertionError):
            assert_preview_exclusion(tmp_path, Path("."), PIPELINE)
    else:
        assert_preview_exclusion(tmp_path, Path("."), PIPELINE)



@pytest.mark.parametrize("job", ["build-check", "deploy-pipeline-job"])
@pytest.mark.parametrize("dockerfile", [None, "./Dockerfile"])
def test_preview_guard_rejects_extra_outer_build(job, dockerfile):
    jobs = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())["jobs"]
    inputs = {"context": "."}
    if dockerfile is not None:
        inputs["file"] = dockerfile
    steps = jobs[job]["steps"] + [{"uses": DIRECT_BUILD + "v6", "with": inputs}]
    # File-specific matching alone still sees the expected guarded build.
    assert effective_contexts(steps, PIPELINE, CGM_ACTION) == [Path(".")]
    with pytest.raises(AssertionError):
        assert_outer_build_inventory(job, steps)
