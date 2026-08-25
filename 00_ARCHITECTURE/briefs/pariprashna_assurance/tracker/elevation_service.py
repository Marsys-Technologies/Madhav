"""Launchd specification for the isolated Paripraśna elevation dashboard.

This module deliberately creates only a shadow-dashboard job specification.  It
does not install, restart, or replace the accepted P0B/P1 control-plane service.
"""
from __future__ import annotations

import plistlib
import re
import sys
import hashlib
import json
import stat
from pathlib import Path


SHADOW_DASHBOARD_LABEL = "com.marsys.pariprashna-assurance.shadow.dashboard"
APPROVED_SHADOW_RUNTIME = Path("/Users/Dev/.pariprashna-assurance-elevation-shadow")
SHADOW_PORT = 8788
SHADOW_RELEASE_SCHEMA = "pariprashna-assurance-elevation-release@1"
SHADOW_RELEASE_FILES = (
    "ELEVATION_PLAN_v1_0.json", "elevation.py", "elevation_dashboard.html",
    "elevation_operations.py", "elevation_server.py", "elevation_service.py",
)
SHADOW_RELEASE_METADATA = (".source-sha", ".release-manifest.json")


def build_shadow_dashboard_plist(release_dir: Path, runtime: Path, source_sha: str) -> bytes:
    """Return a loopback-only launchd job bound exclusively to the shadow runtime."""
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", source_sha):
        raise ValueError("source SHA must be an immutable hexadecimal Git revision")
    if runtime != APPROVED_SHADOW_RUNTIME:
        raise ValueError(f"shadow runtime must be the approved isolated path: {APPROVED_SHADOW_RUNTIME}")
    arguments = [
        sys.executable,
        str(release_dir / "elevation_server.py"),
        "--shadow-db", str(runtime / "elevation.sqlite3"),
        "--host", "127.0.0.1",
        "--port", str(SHADOW_PORT),
    ]
    return plistlib.dumps({
        "Label": SHADOW_DASHBOARD_LABEL,
        "ProgramArguments": arguments,
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ProcessType": "Background",
        "WorkingDirectory": str(release_dir),
        "StandardOutPath": str(runtime / "dashboard.log"),
        "StandardErrorPath": str(runtime / "dashboard.error.log"),
    }, fmt=plistlib.FMT_XML, sort_keys=True)


def assert_shadow_release_attestation(release_dir: Path, source_sha: str) -> Path:
    """Verify a sealed, exact shadow release before launchd may execute it."""
    manifest_path = release_dir / ".release-manifest.json"
    if not manifest_path.is_file():
        raise ValueError("shadow release is not attested")
    status = release_dir.lstat()
    if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode) or status.st_mode & 0o222:
        raise ValueError("shadow release must be a sealed, non-symlink directory")
    expected = set(SHADOW_RELEASE_FILES) | set(SHADOW_RELEASE_METADATA)
    if {entry.name for entry in release_dir.iterdir()} != expected:
        raise ValueError("shadow release does not contain the exact attested tree")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("shadow release attestation is unreadable") from exc
    if manifest.get("schema_version") != SHADOW_RELEASE_SCHEMA or manifest.get("source_sha") != source_sha:
        raise ValueError("shadow release attestation does not match the requested source SHA")
    if (release_dir / ".source-sha").read_text(encoding="utf-8") != source_sha + "\n":
        raise ValueError("shadow release source SHA marker does not match")
    file_hashes = manifest.get("files")
    if not isinstance(file_hashes, dict) or set(file_hashes) != set(SHADOW_RELEASE_FILES):
        raise ValueError("shadow release attestation has an invalid file set")
    for name in (*SHADOW_RELEASE_FILES, *SHADOW_RELEASE_METADATA):
        artifact = release_dir / name
        artifact_status = artifact.lstat()
        if not stat.S_ISREG(artifact_status.st_mode) or stat.S_ISLNK(artifact_status.st_mode) or artifact_status.st_mode & 0o222:
            raise ValueError(f"shadow release artifact is mutable or invalid: {name}")
    for name in SHADOW_RELEASE_FILES:
        if hashlib.sha256((release_dir / name).read_bytes()).hexdigest() != file_hashes[name]:
            raise ValueError(f"shadow release artifact hash differs: {name}")
    return release_dir
