#!/usr/bin/env python3
"""Verify the exact Bodha source membership of the two locally loaded PR images."""
import hashlib
import json
import os
import re
import subprocess

IMAGE_CHECK = """
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
cwd, absent, hashes = json.loads(sys.argv[2])
if str(Path.cwd()) != cwd or root.resolve(strict=True) != root:
    raise SystemExit("unexpected image source location")
for name in absent:
    path = root / name
    if path.exists() or path.is_symlink():
        raise SystemExit("legacy Bodha module is still packaged")
observed = {}
for name in hashes:
    path = root / name
    if not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit("retained Bodha source is not a regular file at its package path")
    observed[name] = hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps([cwd, absent, observed]))
"""


def command(args, *, data=None):
    result = subprocess.run(args, input=data, capture_output=True, timeout=45)
    if result.returncode:
        raise SystemExit("Bodha image membership command failed")
    return result.stdout


def main():
    head = command(["git", "rev-parse", "HEAD"]).decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", head) or head != os.environ.get("GITHUB_SHA"):
        raise SystemExit("Bodha image membership requires the exact PR checkout")

    absent = ["brahmagyan/bodha/l2_embeddings.py", "brahmagyan/bodha/l2_lenses_salience.py"]
    retained = [
        "brahmagyan/bodha/l2_signals_scaffold.py",
        "pipeline/orchestrator/writers/bo_drishti.py",
        "pipeline/orchestrator/writers/bo_samskara.py",
    ]
    hashes = {
        path: hashlib.sha256(command(["git", "show", f"{head}:platform/python-sidecar/{path}"])).hexdigest()
        for path in retained
    }

    for tag, workdir, root in (
        ("amjis-sidecar:pr-check", "/app/python-sidecar", "/app/python-sidecar"),
        ("brahma-pipeline:pr-check", "/app", "/app/platform/python-sidecar"),
    ):
        image = json.loads(command(["docker", "image", "inspect", "--format", "{{json .}}", tag]))
        image_id = image.get("Id")
        if not isinstance(image_id, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
            raise SystemExit("Bodha package has no exact loaded image ID")
        if (image.get("Os"), image.get("Architecture")) != ("linux", "amd64"):
            raise SystemExit("Bodha package has the wrong platform")
        config = image.get("Config")
        if not isinstance(config, dict) or config.get("WorkingDir") != workdir or config.get("Volumes"):
            raise SystemExit("Bodha package has unexpected working directory or volumes")
        expected = [workdir, absent, hashes]
        observed = json.loads(command([
            "docker", "run", "--pull=never", "--rm", "-i", "--network=none", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges", "--platform=linux/amd64",
            "--entrypoint=/usr/bin/env", image_id, "-i", "PATH=/usr/local/bin:/usr/bin:/bin",
            "python", "-BI", "-", root, json.dumps(expected),
        ], data=IMAGE_CHECK.encode()))
        if observed != expected:
            raise SystemExit("Bodha package membership does not match the exact source")
        print("Bodha package verified " + json.dumps({
            "source": head, "tag": tag, "image": image_id, "platform": "linux/amd64",
            "package_root": root, "working_directory": workdir,
            "legacy_absent": absent, "retained_sha256": hashes,
        }, sort_keys=True))


if __name__ == "__main__":
    main()
