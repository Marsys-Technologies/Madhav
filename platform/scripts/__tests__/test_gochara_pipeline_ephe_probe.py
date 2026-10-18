"""C42 — tests for platform/scripts/gochara-pipeline-ephe-probe.sh.

The probe resolves a Cloud Run job's current image (stubbed gcloud), digests the three pinned
.se1 files inside that image (stubbed docker), and compares the digests with the pins it READS
from platform/python-sidecar/services/gochara_kernel/ephemeris_pins.py (PINNED_SE1_SHA256). These tests stub `gcloud` and `docker`
on PATH, log every invocation, and never touch GCP or a real docker daemon.

Covered: --print runs nothing; the PASS path (digests = the real pinned digests); one MISMATCH and
one MISSING file each exit 1 and name the file; SE_EPHE_PATH is echoed; a describe failure and a
missing tool are exit-2 refusals; the pins genuinely come from conftest.py (a tampered pin
flips the result).
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "platform/scripts/gochara-pipeline-ephe-probe.sh"
PINS_REL = "platform/python-sidecar/services/gochara_kernel/ephemeris_pins.py"
PINS_FILE = REPO / PINS_REL
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


def pinned_digests() -> dict[str, str]:
    text = PINS_FILE.read_text(encoding="utf-8")
    m = re.search(r"PINNED_SE1_SHA256[^=]*= \{([^}]*)\}", text, re.S)
    return dict(re.findall(r'"(\w+\.se1)": "([0-9a-f]{64})"', m.group(1)))


def run_probe(tmp_path: Path, *, digests: str | None, gcloud_fail: bool = False,
              inspect_env: str = "SE_EPHE_PATH=/app/ephe\nSWE_EPHE_PATH=/app/ephe\n",
              drop_tool: str | None = None, mode: str = "--run", script: Path | None = None) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    # Even /usr/bin can contain docker on CI runners. Expose only the exact
    # utilities the probe/stubs need, never a host directory containing CLIs.
    for tool in ("bash", "cat", "dirname", "grep", "awk", "python3"):
        target = sys.executable if tool == "python3" else shutil.which(tool)
        assert target is not None, f"required test utility missing: {tool}"
        link = bin_dir / tool
        if not link.exists():
            link.symlink_to(target)
    if drop_tool:
        (bin_dir / drop_tool).unlink(missing_ok=True)
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
    env["PATH"] = str(bin_dir)
    env["STUB_LOG"] = str(tmp_path / "stub.log")
    env["DIGESTS_FILE"] = str(tmp_path / "digests.txt")
    env["INSPECT_FILE"] = str(tmp_path / "env.txt")
    env.pop("GCLOUD_FAIL", None)
    if gcloud_fail:
        env["GCLOUD_FAIL"] = "1"
    r = subprocess.run([str(bin_dir / "bash"), str(script or SCRIPT), "brahma-build-pipeline-job", "asia-south1", mode],
                       env=env, capture_output=True, text=True, timeout=60)
    log = Path(env["STUB_LOG"])
    r.stub_log = log.read_text(encoding="utf-8") if log.exists() else ""  # type: ignore[attr-defined]
    return r


def good_digests() -> str:
    return "".join(f"{sha}  /app/ephe/{name}\n" for name, sha in sorted(pinned_digests().items()))


def test_print_mode_executes_nothing(tmp_path: Path) -> None:
    r = run_probe(tmp_path, digests=None, mode="--print")
    assert r.returncode == 0, r.stderr
    assert "gcloud run jobs describe brahma-build-pipeline-job" in r.stdout
    assert "docker run --rm --entrypoint sha256sum" in r.stdout
    assert "sepl_18.se1" in r.stdout and "semo_18.se1" in r.stdout and "seas_18.se1" in r.stdout
    assert r.stub_log == ""                       # nothing was executed


def test_run_passes_when_all_three_digests_match_the_pinned_digests(tmp_path: Path) -> None:
    r = run_probe(tmp_path, digests=good_digests())
    assert r.returncode == 0, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert r.stdout.count("OK: ") == 3
    assert "RESULT: all three .se1 digests match the pinned digests (ephemeris_pins.py)" in r.stdout
    assert "SE_EPHE_PATH=/app/ephe" in r.stdout
    assert f"image: {IMAGE}" in r.stdout
    assert "--entrypoint sha256sum" in r.stub_log # the image is digested, never the job


def test_a_single_mismatch_exits_1_and_names_the_file(tmp_path: Path) -> None:
    bad = good_digests().replace(pinned_digests()["semo_18.se1"], "0" * 64)
    r = run_probe(tmp_path, digests=bad)
    assert r.returncode == 1
    assert "MISMATCH: semo_18.se1" in r.stderr
    assert r.stdout.count("OK: ") == 2


def test_a_missing_digest_line_exits_1(tmp_path: Path) -> None:
    incomplete = "".join(l for l in good_digests().splitlines(keepends=True) if "seas_18" not in l)
    r = run_probe(tmp_path, digests=incomplete)
    assert r.returncode == 1
    assert "MISSING: seas_18.se1" in r.stderr


def test_the_pins_come_from_ephemeris_pins_not_the_script(tmp_path: Path) -> None:
    # If the script retyped the pins, a digests file matching those retyped values would PASS
    # forever. Instead the comparison tracks ephemeris_pins.py: digests built from the REAL pins pass,
    # and every pin asserted here equals what ephemeris_pins.py holds today.
    pins = pinned_digests()
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


@pytest.mark.parametrize("host_has_docker", [False, True])
@pytest.mark.parametrize("drop_tool", [None, "docker", "gcloud"])
def test_probe_path_is_isolated_from_host_tools(tmp_path: Path, monkeypatch,
                                               host_has_docker: bool, drop_tool: str | None) -> None:
    host_bin = tmp_path / "host-bin"
    host_bin.mkdir()
    for tool in ("bash", "cat", "dirname", "grep", "awk"):
        target = shutil.which(tool)
        assert target is not None, f"required test utility missing: {tool}"
        (host_bin / tool).symlink_to(target)
    marker = tmp_path / "host-tool-ran"
    for tool in ["host_only_command", "gcloud", *(["docker"] if host_has_docker else [])]:
        stub = host_bin / tool
        stub.write_text(f'#!/bin/sh\necho host-tool-ran > "{marker}"\nexit 99\n', encoding="utf-8")
        stub.chmod(0o755)
    monkeypatch.setenv("PATH", str(host_bin))
    # Exercise the child's actual command lookup, including unneeded host tools.
    wrapper = tmp_path / "probe-wrapper.sh"
    wrapper.write_text(
        'if command -v host_only_command >/dev/null; then\n'
        '  echo "host PATH leaked into probe" >&2; exit 99\nfi\n'
        f'exec bash "{SCRIPT}" "$@"\n', encoding="utf-8")
    r = run_probe(tmp_path, digests=good_digests(), drop_tool=drop_tool, script=wrapper)
    assert r.returncode == (2 if drop_tool else 0), r.stderr
    if drop_tool:
        assert f"REFUSAL: {drop_tool} not on PATH" in r.stderr
        assert r.stub_log == ""
    assert not marker.exists(), "a host tool ran instead of a test stub"


def test_usage_refusal_without_job_and_region() -> None:
    r = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True, timeout=30)
    assert r.returncode == 2
    assert "usage:" in r.stderr


def test_a_tampered_pin_in_the_pins_file_flips_the_result(tmp_path: Path) -> None:
    # Run a COPY of the script inside a throw-away tree whose ephemeris_pins.py carries one altered
    # pin: digests built from the real pins must now MISMATCH on exactly that file.
    tree = tmp_path / "tree"
    (tree / "platform/scripts").mkdir(parents=True)
    (tree / Path(PINS_REL).parent).mkdir(parents=True)
    (tree / "platform/scripts/gochara-pipeline-ephe-probe.sh").write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    real = pinned_digests()["sepl_18.se1"]
    (tree / PINS_REL).write_text(PINS_FILE.read_text(encoding="utf-8").replace(real, "f" * 64), encoding="utf-8")
    r = run_probe(tmp_path, digests=good_digests(), script=tree / "platform/scripts/gochara-pipeline-ephe-probe.sh")
    assert r.returncode == 1
    assert "MISMATCH: sepl_18.se1" in r.stderr


def test_a_missing_pins_file_is_an_exit2_refusal(tmp_path: Path) -> None:
    tree = tmp_path / "tree"
    (tree / "platform/scripts").mkdir(parents=True)
    (tree / "platform/scripts/gochara-pipeline-ephe-probe.sh").write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    r = run_probe(tmp_path, digests=good_digests(), script=tree / "platform/scripts/gochara-pipeline-ephe-probe.sh")
    assert r.returncode == 2 and "REFUSAL: pins file not found" in r.stderr


# A failed process substitution used to leave the comparison loop empty and
# report PASS. Each case below must refuse before any image probe is run.
@pytest.mark.parametrize("pin_source", [
    "not valid python !",                          # parser failure
    "UNRELATED = {}",                             # missing assignment
    "PINNED_SE1_SHA256 = {}",                      # missing corpus
    'PINNED_SE1_SHA256 = {"sepl_18.se1": "bad"}',   # malformed/incomplete pins
])
def test_unreadable_or_incomplete_pins_never_produce_a_false_pass(tmp_path: Path, pin_source: str) -> None:
    tree = tmp_path / "tree"
    script = tree / "platform/scripts/gochara-pipeline-ephe-probe.sh"
    pins = tree / PINS_REL
    script.parent.mkdir(parents=True)
    pins.parent.mkdir(parents=True)
    script.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    pins.write_text(pin_source, encoding="utf-8")
    r = run_probe(tmp_path, digests=good_digests(), script=script)
    assert r.returncode == 2
    assert "REFUSAL: invalid ephemeris pins" in r.stderr
    assert "RESULT:" not in r.stdout
    assert r.stub_log == ""
