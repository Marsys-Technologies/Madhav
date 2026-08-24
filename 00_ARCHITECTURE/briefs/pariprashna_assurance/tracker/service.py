#!/usr/bin/env python3
"""Install the approved local CG-0 tracker service without replacing any existing job."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import socket
import stat
import subprocess
import sys
from pathlib import Path


SERVICE_LABEL = "com.marsys.pariprashna-assurance-control"
APPROVED_RUNTIME = Path("/Users/Dev/.pariprashna-assurance-control")
RELEASE_SCHEMA = "pariprashna-assurance-release@1"
RELEASE_FILES = ("EVENT_SCHEMA_v1_0.json", "README.md", "cli.py", "control.py", "dashboard.html", "demo.py", "server.py", "service.py")
RELEASE_METADATA = {".source-sha", ".release-manifest.json"}


def runtime_preflight(runtime: Path, approved_runtime: Path, filevault_status: str) -> None:
    if runtime != approved_runtime:
        raise ValueError(f"runtime must be the approved path: {approved_runtime}")
    if "filevault is on" not in filevault_status.lower():
        raise ValueError("FileVault protection is not confirmed; do not store campaign evidence")
    runtime.mkdir(parents=True, mode=0o700, exist_ok=True)
    status = runtime.stat()
    if status.st_uid != os.getuid():
        raise ValueError("runtime is not owned by the current Dev account")
    os.chmod(runtime, 0o700)


def build_launchd_plist(release_dir: Path, runtime: Path, port: int = 8787) -> bytes:
    return plistlib.dumps({
        "Label": SERVICE_LABEL,
        "ProgramArguments": [sys.executable, str(release_dir / "server.py"), "--runtime", str(runtime), "--host", "127.0.0.1", "--port", str(port)],
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ProcessType": "Background",
        "WorkingDirectory": str(release_dir),
        "StandardOutPath": str(runtime / "service.log"),
        "StandardErrorPath": str(runtime / "service.error.log"),
    }, fmt=plistlib.FMT_XML, sort_keys=True)


def _filevault_status() -> str:
    return subprocess.run(["/usr/bin/fdesetup", "status"], check=False, capture_output=True, text=True).stdout


def _owned_regular_file(path: Path, *, require_read_only: bool) -> None:
    status = path.lstat()
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        raise ValueError(f"release artifact must be a regular file, not a symlink: {path.name}")
    if status.st_uid != os.getuid():
        raise ValueError(f"release artifact is not owned by the current Dev account: {path.name}")
    if require_read_only and status.st_mode & 0o222:
        raise ValueError(f"release artifact is mutable: {path.name}")


def _release_tree(release_dir: Path, *, include_metadata: bool, require_read_only: bool) -> list[Path]:
    status = release_dir.lstat()
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        raise ValueError("release directory must be a real directory, not a symlink")
    if status.st_uid != os.getuid():
        raise ValueError("release directory is not owned by the current Dev account")
    if require_read_only and status.st_mode & 0o222:
        raise ValueError("release directory is mutable")
    expected = set(RELEASE_FILES) | (RELEASE_METADATA if include_metadata else set())
    actual = {entry.name for entry in release_dir.iterdir()}
    if actual != expected:
        raise ValueError("release directory does not contain the exact attested tracker tree")
    files = [release_dir / name for name in sorted(expected)]
    for path in files:
        _owned_regular_file(path, require_read_only=require_read_only)
    return files


def attest_release(release_dir: Path, source_sha: str) -> Path:
    """Seal an exported protected-merge tracker tree before it can be installed."""
    if len(source_sha) not in {40, 64} or any(char not in "0123456789abcdef" for char in source_sha.lower()):
        raise ValueError("source SHA must be a 40- or 64-character hexadecimal immutable revision")
    release_dir = Path(release_dir)
    source_files = _release_tree(release_dir, include_metadata=False, require_read_only=False)
    files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files}
    manifest = {"schema_version": RELEASE_SCHEMA, "source_sha": source_sha, "files": files}
    for name, value in ((".source-sha", source_sha + "\n"), (".release-manifest.json", json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")):
        target = release_dir / name
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(value)
            output.flush()
            os.fsync(output.fileno())
    for path in _release_tree(release_dir, include_metadata=True, require_read_only=False):
        os.chmod(path, 0o444)
    os.chmod(release_dir, 0o555)
    return release_dir / ".release-manifest.json"


def assert_release_attestation(release_dir: Path, source_sha: str) -> None:
    release_dir = Path(release_dir)
    files = _release_tree(release_dir, include_metadata=True, require_read_only=True)
    if (release_dir / ".source-sha").read_text(encoding="utf-8").strip() != source_sha:
        raise ValueError("release directory does not attest to the requested immutable source SHA")
    try:
        manifest = json.loads((release_dir / ".release-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("release manifest is unreadable") from exc
    expected_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files if path.name in RELEASE_FILES}
    if manifest != {"schema_version": RELEASE_SCHEMA, "source_sha": source_sha, "files": expected_hashes}:
        raise ValueError("release manifest does not attest to this immutable source tree")


def _assert_unclaimed(label: str, port: int, plist_path: Path) -> None:
    if plist_path.exists():
        raise ValueError(f"refusing to replace existing launchd plist: {plist_path}")
    domain = f"gui/{os.getuid()}"
    if subprocess.run(["/bin/launchctl", "print", f"{domain}/{label}"], check=False, capture_output=True).returncode == 0:
        raise ValueError(f"refusing to replace active launchd label: {label}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            raise ValueError(f"refusing to install: 127.0.0.1:{port} is already in use") from exc


def install(release_dir: Path, runtime: Path, source_sha: str, port: int = 8787) -> Path:
    if sys.platform != "darwin":
        raise ValueError("launchd installation is supported only on macOS")
    assert_release_attestation(release_dir, source_sha)
    runtime_preflight(runtime, APPROVED_RUNTIME, _filevault_status())
    plist_path = Path.home() / "Library/LaunchAgents" / f"{SERVICE_LABEL}.plist"
    _assert_unclaimed(SERVICE_LABEL, port, plist_path)
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_bytes(build_launchd_plist(release_dir, runtime, port))
    os.chmod(plist_path, 0o600)
    try:
        subprocess.run(["/bin/launchctl", "bootstrap", f"gui/{os.getuid()}", str(plist_path)], check=True)
    except Exception:
        plist_path.unlink(missing_ok=True)
        raise
    return plist_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--attest-release", action="store_true")
    parser.add_argument("--release-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--runtime", type=Path, default=APPROVED_RUNTIME)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    if args.attest_release and args.install:
        raise SystemExit("choose exactly one of --attest-release or --install")
    if args.attest_release:
        print(attest_release(args.release_dir, args.source_sha))
        return
    if not args.install:
        raise SystemExit("pass --attest-release after exporting a merged SHA, then --install")
    print(install(args.release_dir, args.runtime, args.source_sha, args.port))


if __name__ == "__main__":
    main()
