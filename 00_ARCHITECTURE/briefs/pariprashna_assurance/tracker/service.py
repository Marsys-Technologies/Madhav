#!/usr/bin/env python3
"""Install the approved local CG-0 tracker service without replacing any existing job."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import secrets
import socket
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from control import EventStore


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


def _secure_service_logs(runtime: Path) -> None:
    """Create launchd log targets privately before the service can write to them."""
    for name in ("service.log", "service.error.log"):
        descriptor = os.open(runtime / name, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        try:
            status = os.fstat(descriptor)
            if not stat.S_ISREG(status.st_mode) or status.st_uid != os.getuid():
                raise ValueError(f"service log must be a current-user regular file: {name}")
            os.fchmod(descriptor, 0o600)
        finally:
            os.close(descriptor)


def build_launchd_plist(release_dir: Path, runtime: Path, port: int = 8787, *, p1_enabled: bool = False) -> bytes:
    arguments = [sys.executable, str(release_dir / "server.py"), "--runtime", str(runtime), "--p0b-only"]
    if p1_enabled:
        arguments.append("--p1-enabled")
    arguments.extend(("--host", "127.0.0.1", "--port", str(port)))
    return plistlib.dumps({
        "Label": SERVICE_LABEL,
        "ProgramArguments": arguments,
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


def _isolated_git_env() -> dict[str, str]:
    """Remove caller-supplied Git/config/proxy/TLS state from network provenance."""
    environment = {key: value for key, value in os.environ.items() if not (
        key.startswith("GIT_CONFIG_") or key.startswith("GIT_SSL_") or key.startswith("GIT_HTTP_")
        or key in {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_OBJECT_DIRECTORY", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "CURL_CA_BUNDLE", "SSL_CERT_FILE", "SSL_CERT_DIR"}
        or key.lower() in {"http_proxy", "https_proxy", "all_proxy", "no_proxy"}
    )}
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"})
    return environment


def _isolated_git_run(repo: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *_PROVENANCE_GIT_CONFIG, *args], check=False, capture_output=True, text=text, env=_isolated_git_env())


def _isolated_git_output(repo: Path, *args: str) -> str:
    result = _isolated_git_run(repo, *args)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"isolated provenance git {' '.join(args)} failed")
    return result.stdout.strip()


def _canonical_madhav_origin(origin_remote: str) -> str:
    """Return the single persisted origin spelling only for approved GitHub remotes."""
    normalized = origin_remote.strip().rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if normalized not in _MADHAV_ORIGIN_ALIASES:
        raise ValueError("source repository origin must be the canonical Marsys-Technologies/Madhav GitHub remote")
    return CANONICAL_MADHAV_ORIGIN


def _verified_release_source(source_repo: Path, source_sha: str, release_files: list[Path]) -> str:
    """Verify main and the exported tree inside a new config-isolated bare repository."""
    _reject_git_transport_overrides(source_repo)
    with tempfile.TemporaryDirectory(prefix="pariprashna-provenance-") as temporary:
        bare = Path(temporary) / "verified.git"
        initialized = subprocess.run(["git", "init", "--bare", str(bare)], check=False, capture_output=True, text=True, env=_isolated_git_env())
        if initialized.returncode:
            raise ValueError(initialized.stderr.strip() or "could not create isolated provenance repository")
        listing = _isolated_git_output(bare, "ls-remote", "--exit-code", CANONICAL_MADHAV_ORIGIN, "refs/heads/main").splitlines()
        if len(listing) != 1:
            raise ValueError("source repository did not return exactly one authenticated origin/main tip")
        remote_main = listing[0].split("\t", 1)[0]
        if len(remote_main) not in {40, 64} or any(char not in "0123456789abcdef" for char in remote_main.lower()):
            raise ValueError("source repository returned an invalid origin/main object ID")
        fetched = _isolated_git_run(bare, "fetch", "--quiet", CANONICAL_MADHAV_ORIGIN, "refs/heads/main:refs/heads/verified-origin-main")
        if fetched.returncode:
            raise ValueError(fetched.stderr.strip() or "could not fetch authenticated origin/main")
        origin_main = _isolated_git_output(bare, "rev-parse", "--verify", "refs/heads/verified-origin-main^{commit}")
        if origin_main != remote_main:
            raise ValueError("fetched origin/main does not match the freshly authenticated remote tip")
        try:
            _isolated_git_output(bare, "cat-file", "-e", f"{source_sha}^{{commit}}")
        except ValueError as exc:
            raise ValueError("source SHA is not an immutable commit already merged into origin/main") from exc
        ancestor = _isolated_git_run(bare, "merge-base", "--is-ancestor", source_sha, "refs/heads/verified-origin-main")
        if ancestor.returncode:
            raise ValueError("source SHA is not an immutable commit already merged into origin/main")
        for path in release_files:
            result = _isolated_git_run(bare, "show", f"{source_sha}:{SOURCE_TRACKER_PATH}/{path.name}", text=False)
            if result.returncode or result.stdout != path.read_bytes():
                raise ValueError(f"release artifact does not match the approved merged source: {path.name}")
        return origin_main


def _assert_approved_merge_source(source_repo: Path, source_sha: str, release_files: list[Path]) -> tuple[str, str]:
    source_repo = Path(source_repo).resolve(strict=True)
    origin_remote = _canonical_madhav_origin(_git_output(source_repo, "config", "--get", "remote.origin.url"))
    origin_main = _verified_release_source(source_repo, source_sha, release_files)
    return origin_main, origin_remote


def attest_release(release_dir: Path, source_sha: str, source_repo: Path) -> Path:
    """Seal an exported protected-merge tracker tree before it can be installed."""
    if len(source_sha) not in {40, 64} or any(char not in "0123456789abcdef" for char in source_sha.lower()):
        raise ValueError("source SHA must be a 40- or 64-character hexadecimal immutable revision")
    release_dir, source_files = _release_tree(release_dir, include_metadata=False, require_read_only=False)
    origin_main, origin_remote = _assert_approved_merge_source(source_repo, source_sha, source_files)
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


def _assert_upgradeable_p0b_service(plist_path: Path, runtime: Path, port: int) -> tuple[Path, str]:
    """Refuse every service except the exact deployed P0B-only control plane."""
    try:
        plist = plistlib.loads(plist_path.read_bytes())
    except (OSError, ValueError) as exc:
        raise ValueError("existing control-plane plist is unreadable") from exc
    arguments = plist.get("ProgramArguments") if isinstance(plist, dict) else None
    if plist.get("Label") != SERVICE_LABEL or not isinstance(arguments, list):
        raise ValueError("existing launchd job is not the approved control-plane service")
    if len(arguments) != 9 or not isinstance(arguments[1], str):
        raise ValueError("existing launchd job is not the exact P0B-only service eligible for P1 enablement")
    old_release = Path(arguments[1]).parent
    try:
        old_sha = (old_release / ".source-sha").read_text(encoding="utf-8").strip()
        assert_release_attestation(old_release, old_sha)
    except (OSError, ValueError) as exc:
        raise ValueError("existing P0B release lacks a valid immutable attestation") from exc
    expected = [arguments[0], str(old_release / "server.py"), "--runtime", str(runtime), "--p0b-only", "--host", "127.0.0.1", "--port", str(port)]
    if arguments != expected:
        raise ValueError("existing launchd job is not the exact P0B-only service eligible for P1 enablement")
    return old_release, old_sha


def _write_private_file(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, content)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _replace_private_file(path: Path, content: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    _write_private_file(temporary, content)
    os.replace(temporary, path)
    os.chmod(path, 0o600)


def upgrade_p1(release_dir: Path, runtime: Path, source_sha: str, pre_snapshot: Path, post_snapshot: Path, port: int = 8787) -> dict[str, str]:
    """Atomically replace only the approved P0B service with an attested P1-enabled release."""
    if sys.platform != "darwin":
        raise ValueError("launchd P1 enablement is supported only on macOS")
    release_dir = assert_release_attestation(release_dir, source_sha)
    runtime_preflight(runtime, APPROVED_RUNTIME, _filevault_status())
    plist_path = Path.home() / "Library/LaunchAgents" / f"{SERVICE_LABEL}.plist"
    _assert_upgradeable_p0b_service(plist_path, runtime, port)
    domain = f"gui/{os.getuid()}"
    if subprocess.run(["/bin/launchctl", "print", f"{domain}/{SERVICE_LABEL}"], check=False, capture_output=True).returncode != 0:
        raise ValueError("the approved P0B service is not loaded; refusing an unproven replacement")
    store = EventStore(runtime, p0b_only=True)
    if not store.verify_replay()["ok"]:
        raise ValueError("P0B replay integrity is not clean; refusing P1 enablement")
    with store.connection() as con:
        if not EventStore._p0_to_p1_dependency_resolved(con):
            raise ValueError("P0-to-P1 dependency is unresolved; refusing P1 enablement")
    pre = store.export_snapshot(pre_snapshot)
    previous_plist = plist_path.read_bytes()
    backup_plist = plist_path.with_name(f"{plist_path.name}.p0b-backup-{source_sha[:12]}")
    _write_private_file(backup_plist, previous_plist)
    replacement = build_launchd_plist(release_dir, runtime, port, p1_enabled=True)
    temporary_plist = plist_path.with_name(f".{plist_path.name}.{source_sha[:12]}.p1.tmp")
    _write_private_file(temporary_plist, replacement)
    switched = False
    try:
        subprocess.run(["/bin/launchctl", "bootout", domain, str(plist_path)], check=True)
        os.replace(temporary_plist, plist_path)
        subprocess.run(["/bin/launchctl", "bootstrap", domain, str(plist_path)], check=True)
        switched = True
        enabled = EventStore(runtime, p0b_only=True, p1_enabled=True)
        if not enabled.verify_replay()["ok"]:
            raise ValueError("P1-enabled service replay integrity is not clean")
        enabled.provision_p1_credentials()
        post = enabled.export_snapshot(post_snapshot)
        return {"pre_snapshot": pre["path"], "post_snapshot": post["path"], "backup_plist": str(backup_plist)}
    except Exception as activation_error:
        temporary_plist.unlink(missing_ok=True)
        try:
            if switched:
                subprocess.run(["/bin/launchctl", "bootout", domain, str(plist_path)], check=True)
            _replace_private_file(plist_path, previous_plist)
            subprocess.run(["/bin/launchctl", "bootstrap", domain, str(plist_path)], check=True)
        except Exception as rollback_error:
            raise RuntimeError(f"P1 enablement failed and P0B rollback failed; preserved plist backup: {backup_plist}") from rollback_error
        raise activation_error


def install(release_dir: Path, runtime: Path, source_sha: str, port: int = 8787, *, p1_enabled: bool = False) -> Path:
    if sys.platform != "darwin":
        raise ValueError("launchd installation is supported only on macOS")
    release_dir = assert_release_attestation(release_dir, source_sha)
    runtime_preflight(runtime, APPROVED_RUNTIME, _filevault_status())
    _secure_service_logs(runtime)
    plist_path = Path.home() / "Library/LaunchAgents" / f"{SERVICE_LABEL}.plist"
    _assert_unclaimed(SERVICE_LABEL, port, plist_path)
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_bytes(build_launchd_plist(release_dir, runtime, port, p1_enabled=p1_enabled))
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
    parser.add_argument("--upgrade-p1", action="store_true")
    parser.add_argument("--p1-enabled", action="store_true")
    parser.add_argument("--release-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--source-repo", type=Path)
    parser.add_argument("--runtime", type=Path, default=APPROVED_RUNTIME)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--pre-snapshot", type=Path)
    parser.add_argument("--post-snapshot", type=Path)
    args = parser.parse_args()
    if sum((args.attest_release, args.install, args.upgrade_p1)) != 1:
        raise SystemExit("choose exactly one of --attest-release, --install, or --upgrade-p1")
    if args.attest_release:
        if args.source_repo is None:
            raise SystemExit("--attest-release requires --source-repo at the repository with origin/main evidence")
        print(attest_release(args.release_dir, args.source_sha, args.source_repo))
        return
    if args.install:
        print(install(args.release_dir, args.runtime, args.source_sha, args.port, p1_enabled=args.p1_enabled))
        return
    if args.pre_snapshot is None or args.post_snapshot is None:
        raise SystemExit("--upgrade-p1 requires distinct --pre-snapshot and --post-snapshot paths")
    if args.pre_snapshot == args.post_snapshot:
        raise SystemExit("--upgrade-p1 snapshot paths must be distinct")
    print(json.dumps(upgrade_p1(args.release_dir, args.runtime, args.source_sha, args.pre_snapshot, args.post_snapshot, args.port), sort_keys=True))


if __name__ == "__main__":
    main()
