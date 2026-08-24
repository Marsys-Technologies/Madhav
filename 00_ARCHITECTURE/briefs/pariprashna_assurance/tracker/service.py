#!/usr/bin/env python3
"""Install the approved local CG-0 tracker service without replacing any existing job."""
from __future__ import annotations

import argparse
import os
import plistlib
import socket
import subprocess
import sys
from pathlib import Path


SERVICE_LABEL = "com.marsys.pariprashna-assurance-control"
APPROVED_RUNTIME = Path("/Users/Dev/.pariprashna-assurance-control")


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
    runtime_preflight(runtime, APPROVED_RUNTIME, _filevault_status())
    if (release_dir / ".source-sha").read_text(encoding="utf-8").strip() != source_sha:
        raise ValueError("release directory does not attest to the requested immutable source SHA")
    if not (release_dir / "server.py").is_file():
        raise ValueError("release directory does not contain the tracker server")
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
    parser.add_argument("--release-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--runtime", type=Path, default=APPROVED_RUNTIME)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    if not args.install:
        raise SystemExit("pass --install after creating a merged-SHA release directory")
    print(install(args.release_dir, args.runtime, args.source_sha, args.port))


if __name__ == "__main__":
    main()
