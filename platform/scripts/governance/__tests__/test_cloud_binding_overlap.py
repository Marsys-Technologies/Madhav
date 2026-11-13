"""Cloud binding overlap at actual deploy and operator entry points; no provisioning."""
from pathlib import Path
import os
import re
import subprocess
import yaml
import pytest

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = (
    "platform/scripts/backup/provision_logical_export_scheduler.sh",
    "platform/scripts/provision_watchdog_scheduler.sh",
)
BINDINGS = (
    ("PROJECT", "GCP_PROJECT", "GOOGLE_CLOUD_PROJECT", "madhav-astrology"),
    ("REGION", "GCP_REGION", "GOOGLE_CLOUD_REGION", "asia-south1"),
)


def assignment(script: str, variable: str) -> str:
    matches = re.findall(rf'^{variable}=(.+)$', (ROOT / script).read_text(), re.MULTILINE)
    assert len(matches) == 1
    return matches[0]


def resolve(expression: str, env: dict[str, str]) -> str:
    # Only the exact reviewed parameter expansions reach this inert Bash process.
    assert expression in {
        '"${GCP_PROJECT:-${GOOGLE_CLOUD_PROJECT:-madhav-astrology}}"',
        '"${GCP_REGION:-${GOOGLE_CLOUD_REGION:-asia-south1}}"',
        '"${GCP_PROJECT:-madhav-astrology}"',
        '"${GCP_REGION:-asia-south1}"',
    }
    result = subprocess.run(
        ["/bin/bash", "--noprofile", "--norc", "-c", f'VALUE={expression}; printf "%s" "$VALUE"'],
        env={"PATH": "/usr/bin:/bin", **env}, capture_output=True, text=True,
        check=True, timeout=5,
    )
    assert result.stderr == ""
    return result.stdout


@pytest.mark.parametrize("script", SCRIPTS)
@pytest.mark.parametrize("variable,legacy,canonical,default", BINDINGS)
def test_operator_project_and_region_preserve_overlap(script, variable, legacy, canonical, default):
    expression = assignment(script, variable)
    cases = (
        ({}, default),
        ({legacy: "old"}, "old"),
        ({canonical: "new"}, "new"),
        ({legacy: "same", canonical: "same"}, "same"),
        ({legacy: "old", canonical: "new"}, "old"),
        ({legacy: "", canonical: "new"}, "new"),
        ({legacy: "old", canonical: ""}, "old"),
        ({legacy: "", canonical: ""}, default),
        ({legacy: ""}, default),
        ({canonical: ""}, default),
    )
    for env, expected in cases:
        before = dict(env)
        assert resolve(expression, env) == expected
        assert env == before


def test_pipeline_deployment_binds_both_project_names_to_same_existing_value():
    workflow = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())
    steps = workflow["jobs"]["deploy-pipeline-job"]["steps"]
    step = next(row for row in steps if row.get("name") == "Re-point Cloud Run Job at the new image")
    run = step["run"]
    canonical = re.findall(r"(?<![A-Z_])GOOGLE_CLOUD_PROJECT=([^,\s\"\n]+)", run)
    legacy = re.findall(r"(?<![A-Z_])GCP_PROJECT=([^,\s\"\n]+)", run)
    assert len(canonical) == len(legacy) == 1
    assert canonical == legacy == ["madhav-astrology"]


def test_web_deployment_binds_both_project_names_to_same_existing_value():
    workflow = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())
    steps = workflow["jobs"]["deploy-web"]["steps"]
    values = next(row["with"]["env_vars"] for row in steps if "env_vars" in row.get("with", {}) and "GCP_PROJECT=madhav-astrology" in row["with"]["env_vars"])
    canonical = [row.partition("=")[2] for row in values.splitlines() if row.startswith("GOOGLE_CLOUD_PROJECT=")]
    legacy = [row.partition("=")[2] for row in values.splitlines() if row.startswith("GCP_PROJECT=")]
    assert canonical == legacy == ["madhav-astrology"]
