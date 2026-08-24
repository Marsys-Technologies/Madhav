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
SOURCE_TRACKER_PATH = "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"
CANONICAL_MADHAV_ORIGIN = "https://github.com/Marsys-Technologies/Madhav.git"
_MADHAV_ORIGIN_ALIASES = frozenset({
    "https://github.com/Marsys-Technologies/Madhav",
    "ssh://git@github.com/Marsys-Technologies/Madhav",
    "git@github.com:Marsys-Technologies/Madhav",
})
_PROVENANCE_GIT_CONFIG = (
    "-c", "protocol.file.allow=never",
    "-c", "protocol.ext.allow=never",
    "-c", "protocol.git.allow=never",
    "-c", "protocol.ssh.allow=never",
    "-c", "protocol.https.allow=always",
    "-c", "http.sslVerify=true",
    "-c", "http.proxy=",
    "-c", "http.extraHeader=",
)


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


def _canonical_release_dir(path: Path) -> Path:
    candidate = Path(os.path.abspath(path))
    current = Path(candidate.anchor)
    for component in candidate.parts[1:]:
        current /= component
        if current.is_symlink():
            # macOS exposes /var as the fixed system alias for /private/var.  Normalize
            # that platform path, but reject every caller-controlled link component.
            if current == Path("/var") and current.resolve() == Path("/private/var"):
                current = current.resolve()
                continue
            raise ValueError(f"release path contains a symlinked component: {current}")
    return candidate.resolve(strict=True)


def _owned_regular_file(path: Path, *, require_read_only: bool) -> None:
    status = path.lstat()
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        raise ValueError(f"release artifact must be a regular file, not a symlink: {path.name}")
    if status.st_uid != os.getuid():
        raise ValueError(f"release artifact is not owned by the current Dev account: {path.name}")
    if require_read_only and status.st_mode & 0o222:
        raise ValueError(f"release artifact is mutable: {path.name}")


def _release_tree(release_dir: Path, *, include_metadata: bool, require_read_only: bool) -> tuple[Path, list[Path]]:
    release_dir = _canonical_release_dir(release_dir)
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
    return release_dir, files


def _git_output(source_repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(source_repo), *args], check=False, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _reject_git_transport_overrides(source_repo: Path) -> None:
    """Do not let a release checkout rewrite the canonical GitHub transport."""
    rewrites = subprocess.run(["git", "-C", str(source_repo), "config", "--show-origin", "--get-regexp", r"^url\..*\.insteadOf$"], check=False, capture_output=True, text=True)
    if rewrites.returncode not in {0, 1}:
        raise ValueError(rewrites.stderr.strip() or "could not inspect Git transport configuration")
    if rewrites.stdout.strip():
        raise ValueError("source repository config contains forbidden Git URL rewrite rules")


def _provenance_git_output(source_repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(source_repo), *_PROVENANCE_GIT_CONFIG, *args], check=False, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"provenance git {' '.join(args)} failed")
    return result.stdout.strip()


def _canonical_madhav_origin(origin_remote: str) -> str:
    """Return the single persisted origin spelling only for approved GitHub remotes."""
    normalized = origin_remote.strip().rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if normalized not in _MADHAV_ORIGIN_ALIASES:
        raise ValueError("source repository origin must be the canonical Marsys-Technologies/Madhav GitHub remote")
    return CANONICAL_MADHAV_ORIGIN


def _fresh_origin_main(source_repo: Path) -> str:
    """Require an online origin lookup and fetch before trusting origin/main."""
    _reject_git_transport_overrides(source_repo)
    listing = _provenance_git_output(source_repo, "ls-remote", "--exit-code", CANONICAL_MADHAV_ORIGIN, "refs/heads/main").splitlines()
    if len(listing) != 1:
        raise ValueError("source repository did not return exactly one authenticated origin/main tip")
    remote_main = listing[0].split("\t", 1)[0]
    if len(remote_main) not in {40, 64} or any(char not in "0123456789abcdef" for char in remote_main.lower()):
        raise ValueError("source repository returned an invalid origin/main object ID")
    fetched = subprocess.run(["git", "-C", str(source_repo), *_PROVENANCE_GIT_CONFIG, "fetch", "--quiet", CANONICAL_MADHAV_ORIGIN, "refs/heads/main:refs/remotes/origin/main"], check=False, capture_output=True, text=True)
    if fetched.returncode:
        raise ValueError(fetched.stderr.strip() or "could not fetch authenticated origin/main")
    origin_main = _git_output(source_repo, "rev-parse", "--verify", "origin/main^{commit}")
    if origin_main != remote_main:
        raise ValueError("fetched origin/main does not match the freshly authenticated remote tip")
    return origin_main


def _assert_approved_merge_source(source_repo: Path, source_sha: str) -> tuple[str, str]:
    source_repo = Path(source_repo).resolve(strict=True)
    origin_remote = _canonical_madhav_origin(_git_output(source_repo, "config", "--get", "remote.origin.url"))
    _git_output(source_repo, "cat-file", "-e", f"{source_sha}^{{commit}}")
    origin_main = _fresh_origin_main(source_repo)
    if subprocess.run(["git", "-C", str(source_repo), "merge-base", "--is-ancestor", source_sha, "origin/main"], check=False).returncode:
        raise ValueError("source SHA is not an immutable commit already merged into origin/main")
    return origin_main, origin_remote


def attest_release(release_dir: Path, source_sha: str, source_repo: Path) -> Path:
    """Seal an exported protected-merge tracker tree before it can be installed."""
    if len(source_sha) not in {40, 64} or any(char not in "0123456789abcdef" for char in source_sha.lower()):
        raise ValueError("source SHA must be a 40- or 64-character hexadecimal immutable revision")
    release_dir, source_files = _release_tree(release_dir, include_metadata=False, require_read_only=False)
    origin_main, origin_remote = _assert_approved_merge_source(source_repo, source_sha)
    for path in source_files:
        result = subprocess.run(["git", "-C", str(Path(source_repo).resolve()), "show", f"{source_sha}:{SOURCE_TRACKER_PATH}/{path.name}"], check=False, capture_output=True)
        if result.returncode or result.stdout != path.read_bytes():
            raise ValueError(f"release artifact does not match the approved merged source: {path.name}")
    files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files}
    manifest = {"schema_version": RELEASE_SCHEMA, "source_sha": source_sha, "origin_main": origin_main, "origin_remote": origin_remote, "release_path": str(release_dir), "files": files}
    for name, value in ((".source-sha", source_sha + "\n"), (".release-manifest.json", json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")):
        target = release_dir / name
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(value)
            output.flush()
            os.fsync(output.fileno())
    _, sealed_files = _release_tree(release_dir, include_metadata=True, require_read_only=False)
    for path in sealed_files:
        os.chmod(path, 0o444)
    os.chmod(release_dir, 0o555)
    return release_dir / ".release-manifest.json"


def assert_release_attestation(release_dir: Path, source_sha: str) -> Path:
    release_dir, files = _release_tree(release_dir, include_metadata=True, require_read_only=True)
    if (release_dir / ".source-sha").read_text(encoding="utf-8").strip() != source_sha:
        raise ValueError("release directory does not attest to the requested immutable source SHA")
    try:
        manifest = json.loads((release_dir / ".release-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("release manifest is unreadable") from exc
    expected_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files if path.name in RELEASE_FILES}
    if not isinstance(manifest, dict) or manifest.get("schema_version") != RELEASE_SCHEMA or manifest.get("source_sha") != source_sha or manifest.get("release_path") != str(release_dir) or not isinstance(manifest.get("origin_main"), str) or manifest.get("origin_remote") != CANONICAL_MADHAV_ORIGIN or manifest.get("files") != expected_hashes:
        raise ValueError("release manifest does not attest to this immutable source tree")
    return release_dir


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
    release_dir = assert_release_attestation(release_dir, source_sha)
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
    parser.add_argument("--source-repo", type=Path)
    parser.add_argument("--runtime", type=Path, default=APPROVED_RUNTIME)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    if args.attest_release and args.install:
        raise SystemExit("choose exactly one of --attest-release or --install")
    if args.attest_release:
        if args.source_repo is None:
            raise SystemExit("--attest-release requires --source-repo at the repository with origin/main evidence")
        print(attest_release(args.release_dir, args.source_sha, args.source_repo))
        return
    if not args.install:
        raise SystemExit("pass --attest-release after exporting a merged SHA, then --install")
    print(install(args.release_dir, args.runtime, args.source_sha, args.port))


if __name__ == "__main__":
    main()
