#!/usr/bin/env python3
"""Attest an immutable, source-SHA-named release directory for the shadow-only
adapter sync worker.

Deliberately separate from ``service.py``'s ``attest_release``: that function is
hard-coupled (via its module-level ``RELEASE_FILES``/``RELEASE_METADATA``) to the
accepted 8787 control-plane release tree. The shadow sync worker ships a smaller,
distinct file set and must never be attestable as (or confused with) an accepted
release. The cryptographic provenance checks -- fetch a fresh, protocol-locked,
config-isolated clone of the real ``origin/main``, confirm the requested source SHA
is an already-merged ancestor, and verify every release file's bytes match that
commit -- are reused unmodified from ``service.py``.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

from service import (
    SOURCE_TRACKER_PATH,
    CANONICAL_MADHAV_ORIGIN,
    _assert_approved_merge_source,
    _canonical_release_dir,
    _owned_regular_file,
)

SHADOW_RELEASE_FILES = ("elevation.py", "elevation_worker.py")
SHADOW_DASHBOARD_RELEASE_FILES = ("elevation.py", "elevation_server.py", "elevation_dashboard.html")
SHADOW_RELEASE_METADATA = {".source-sha", ".release-manifest.json"}
SHADOW_RELEASE_SCHEMA = "pariprashna-shadow-sync-release@1"


def _shadow_release_tree(release_dir: Path, release_files: tuple[str, ...], *, include_metadata: bool, require_read_only: bool) -> tuple[Path, list[Path]]:
    release_dir = _canonical_release_dir(release_dir)
    status = release_dir.lstat()
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
        raise ValueError("release directory must be a real directory, not a symlink")
    if status.st_uid != os.getuid():
        raise ValueError("release directory is not owned by the current Dev account")
    if require_read_only and status.st_mode & 0o222:
        raise ValueError("release directory is mutable")
    expected = set(release_files) | (SHADOW_RELEASE_METADATA if include_metadata else set())
    actual = {entry.name for entry in release_dir.iterdir()}
    if actual != expected:
        raise ValueError("release directory does not contain the exact attested shadow tree")
    files = [release_dir / name for name in sorted(expected)]
    for path in files:
        _owned_regular_file(path, require_read_only=require_read_only)
    return release_dir, files


def attest_shadow_release(release_dir: Path, source_sha: str, source_repo: Path, *, release_files: tuple[str, ...] = SHADOW_RELEASE_FILES) -> Path:
    """Seal an exported, protected-merge shadow release tree before install.

    ``release_files`` scopes the attested tree to exactly the files a given shadow
    component needs (the sync worker's two files by default; pass
    ``SHADOW_DASHBOARD_RELEASE_FILES`` for the dashboard server instead) -- never the
    accepted 8787 control-plane's own file set.
    """
    if len(source_sha) not in {40, 64} or any(char not in "0123456789abcdef" for char in source_sha.lower()):
        raise ValueError("source SHA must be a 40- or 64-character hexadecimal immutable revision")
    release_dir, source_files = _shadow_release_tree(release_dir, release_files, include_metadata=False, require_read_only=False)
    origin_main, origin_remote = _assert_approved_merge_source(source_repo, source_sha, source_files)
    files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files}
    manifest = {
        "schema_version": SHADOW_RELEASE_SCHEMA,
        "source_sha": source_sha,
        "origin_main": origin_main,
        "origin_remote": origin_remote,
        "release_path": str(release_dir),
        "source_tracker_path": SOURCE_TRACKER_PATH,
        "files": files,
    }
    for name, value in ((".source-sha", source_sha + "\n"), (".release-manifest.json", json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")):
        target = release_dir / name
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(value)
            output.flush()
            os.fsync(output.fileno())
    _, sealed_files = _shadow_release_tree(release_dir, release_files, include_metadata=True, require_read_only=False)
    for path in sealed_files:
        os.chmod(path, 0o444)
    os.chmod(release_dir, 0o555)
    return release_dir / ".release-manifest.json"


def assert_shadow_release_attestation(release_dir: Path, source_sha: str, *, release_files: tuple[str, ...] = SHADOW_RELEASE_FILES) -> Path:
    release_dir, files = _shadow_release_tree(release_dir, release_files, include_metadata=True, require_read_only=True)
    if (release_dir / ".source-sha").read_text(encoding="utf-8").strip() != source_sha:
        raise ValueError("release directory does not attest to the requested immutable source SHA")
    try:
        manifest = json.loads((release_dir / ".release-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("release manifest is unreadable") from exc
    expected_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files if path.name in release_files}
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != SHADOW_RELEASE_SCHEMA
        or manifest.get("source_sha") != source_sha
        or manifest.get("release_path") != str(release_dir)
        or not isinstance(manifest.get("origin_main"), str)
        or manifest.get("origin_remote") != CANONICAL_MADHAV_ORIGIN
        or manifest.get("files") != expected_hashes
    ):
        raise ValueError("release manifest does not attest to this immutable source tree")
    return release_dir


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Attest an immutable shadow release directory")
    parser.add_argument("--release-dir", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--component", choices=("worker", "dashboard"), default="worker")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    release_files = SHADOW_DASHBOARD_RELEASE_FILES if args.component == "dashboard" else SHADOW_RELEASE_FILES
    if args.verify_only:
        assert_shadow_release_attestation(args.release_dir, args.source_sha, release_files=release_files)
        print(f"OK: {args.release_dir} attests source_sha={args.source_sha}")
        return
    manifest_path = attest_shadow_release(args.release_dir, args.source_sha, args.source_repo, release_files=release_files)
    print(f"sealed: {manifest_path}")


if __name__ == "__main__":
    main()
