"""C42 — tests for platform/scripts/gochara-pipeline-ephe-probe.sh.

The probe resolves a Cloud Run job's current image (stubbed gcloud), digests the three pinned
.se1 files inside that image (stubbed docker), and compares the digests with the pins it READS
from platform/python-sidecar/tests/l3/gochara/conftest.py. These tests stub `gcloud` and `docker`
on PATH, log every invocation, and never touch GCP or a real docker daemon.

Covered: --print runs nothing; the PASS path (digests = the real conftest pins); one MISMATCH and
one MISSING file each exit 1 and name the file; SE_EPHE_PATH is echoed; a describe failure and a
missing tool are exit-2 refusals; the pins genuinely come from conftest.py (a tampered conftest
pin flips the result).
"""
from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/gochara-pipeline-ephe-probe.sh"
CONFTEST = REPO / "platform/python-sidecar/tests/l3/gochara/conftest.py"
IMAGE = "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:deadbeef"

GCLOUD_STUB = """#!/usr/bin/env bash
echo "gcloud $*" >> "$STUB_LOG"
[ -n "$GCLOUD_FAIL" ] && exit 1
echo "%s"
"""

DOCKER_STUB = """#!/usr/bin/env bash
echo "docker $*" >> "$STUB_LOG"
case "$1" in
  run)   cat "$DIGESTS_FILE" ;;
  inspect) [ -n "$INSPECT_FILE" ] && cat "$INSPECT_FILE" || true ;;
  *) exit 1 ;;
esac
"""


def conftest_pins() -> dict[str, str]:
    text = CONFTEST.read_text(encoding="utf-8")
    m = re.search(r"SE1_CHECKSUMS = \{([^}]*)\}", text, re.S)
    return dict(re.findall(r'"(\w+\.se1)": "([0-9a-f]{64})"', m.group(1)))


def run_probe(tmp_path: Path, *, digests: str | None, gcloud_fail: bool = False,
              inspect_env: str = "SE_EPHE_PATH=/app/ephe\nSWE_EPHE_PATH=/app/ephe\n",
              drop_tool: str | None = None, mode: str = "--run") -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    if drop_tool != "gcloud":
        stub = bin_dir / "gcloud"
        stub.write_text(GCLOUD_STUB % IMAGE, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if drop_tool != "docker":
        stub = bin_dir / "docker"
        stub.write_text(DOCKER_STUB, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if digests is not None:
        (tmp_path / "digests.txt").write_text(digests, encoding="utf-8")
    (tmp_path / "env.txt").write_text(inspect_env, encoding="utf-8")

    env = dict(os.environ)
    if drop_tool:
        # a PATH without any real tool dirs: the named tool is genuinely absent
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
    else:
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["STUB_LOG"] = str(tmp_path / "stub.log")
    env["DIGESTS_FILE"] = str(tmp_path / "digests.txt")
    env["INSPECT_FILE"] = str(tmp_path / "env.txt")
    if gcloud_fail:
        env["GCLOUD_FAIL"] = "1"
    r = subprocess.run(["bash", str(SCRIPT), "brahma-build-pipeline-job", "asia-south1", mode],
                       env=env, capture_output=True, text=True, timeout=60)
    log = Path(env["STUB_LOG"])
    r.stub_log = log.read_text(encoding="utf-8") if log.exists() else ""  # type: ignore[attr-defined]
    return r


def good_digests() -> str:
    return "".join(f"{sha}  /app/ephe/{name}\n" for name, sha in sorted(conftest_pins().items()))


def test_print_mode_executes_nothing(tmp_path: Path) -> None:
    r = run_probe(tmp_path, digests=None, mode="--print")
    assert r.returncode == 0, r.stderr
    assert "gcloud run jobs describe brahma-build-pipeline-job" in r.stdout
    assert "docker run --rm --entrypoint sha256sum" in r.stdout
    assert "sepl_18.se1" in r.stdout and "semo_18.se1" in r.stdout and "seas_18.se1" in r.stdout
    assert r.stub_log == ""                       # nothing was executed


def test_run_passes_when_all_three_digests_match_the_conftest_pins(tmp_path: Path) -> None:
    r = run_probe(tmp_path, digests=good_digests())
    assert r.returncode == 0, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert r.stdout.count("OK: ") == 3
    assert "RESULT: all three .se1 digests match the conftest pins" in r.stdout
    assert "SE_EPHE_PATH=/app/ephe" in r.stdout
    assert f"image: {IMAGE}" in r.stdout
    assert "--entrypoint sha256sum" in r.stub_log # the image is digested, never the job


def test_a_single_mismatch_exits_1_and_names_the_file(tmp_path: Path) -> None:
    bad = good_digests().replace(conftest_pins()["semo_18.se1"], "0" * 64)
    r = run_probe(tmp_path, digests=bad)
    assert r.returncode == 1
    assert "MISMATCH: semo_18.se1" in r.stderr
    assert r.stdout.count("OK: ") == 2


def test_a_missing_digest_line_exits_1(tmp_path: Path) -> None:
    incomplete = "".join(l for l in good_digests().splitlines(keepends=True) if "seas_18" not in l)
    r = run_probe(tmp_path, digests=incomplete)
    assert r.returncode == 1
    assert "MISSING: seas_18.se1" in r.stderr


def test_the_pins_come_from_conftest_not_the_script(tmp_path: Path) -> None:
    # If the script retyped the pins, a digests file matching those retyped values would PASS
    # forever. Instead the comparison tracks conftest.py: digests built from the REAL pins pass,
    # and every pin asserted here equals what conftest.py holds today.
    pins = conftest_pins()
    assert len(pins) == 3
    r = run_probe(tmp_path, digests=good_digests())
    assert r.returncode == 0
    script_text = SCRIPT.read_text(encoding="utf-8")
    for sha in pins.values():
        assert sha not in script_text, "a pin is hard-coded in the script — it must be READ"


def test_a_describe_failure_is_an_exit2_refusal(tmp_path: Path) -> None:
    r = run_probe(tmp_path, digests=good_digests(), gcloud_fail=True)
    assert r.returncode == 2
    assert "REFUSAL" in r.stderr


def test_a_missing_tool_is_an_exit2_refusal(tmp_path: Path) -> None:
    r = run_probe(tmp_path, digests=good_digests(), drop_tool="docker")
    assert r.returncode == 2
    assert "REFUSAL: docker not on PATH" in r.stderr


def test_usage_refusal_without_job_and_region() -> None:
    r = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True, timeout=30)
    assert r.returncode == 2
    assert "usage:" in r.stderr
