"""Periodic shadow-only adapter synchronization.

The worker writes observations through ``AdapterRunner`` only.  It deliberately
has no evidence-acceptance, progress, gate, or cutover operation.
"""
from __future__ import annotations

import argparse
import threading
import json
import plistlib
import signal
import subprocess
import sys
import hashlib
import http.client
from typing import Any, Callable
from pathlib import Path
from urllib.parse import urlsplit

from elevation import AdapterRunner, ElevationStore


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _run_command(argv: list[str]) -> str:
    result = subprocess.run(argv, check=False, capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"command exited {result.returncode}")
    return result.stdout


def _fetch_loopback_json(url: str) -> dict[str, Any]:
    parsed = urlsplit(url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("runtime probe must be loopback HTTP")
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=10)
    try:
        connection.request("GET", (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else ""), headers={"Host": parsed.netloc})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError(f"runtime probe returned HTTP {response.status}")
        payload = json.loads(response.read())
    finally:
        connection.close()
    if not isinstance(payload, dict):
        raise ValueError("runtime probe did not return an object")
    return payload


def builtin_probes(source_repo: Path, accepted_identity_url: str, *, run_command: Callable[[list[str]], str] = _run_command, fetch_json: Callable[[str], dict[str, Any]] = _fetch_loopback_json) -> dict[str, Callable[[str | None], dict[str, Any]]]:
    """Concrete read-only probes for source-control and the accepted loopback identity."""
    repo = str(source_repo)

    def github(_cursor: str | None) -> dict[str, Any]:
        pulls = json.loads(run_command(["gh", "api", "repos/Marsys-Technologies/Madhav/pulls?state=open&per_page=100"]))
        if not isinstance(pulls, list):
            raise ValueError("GitHub probe did not return a pull-request list")
        payload = {"open_pull_requests": pulls}
        return {"cursor": _digest(payload), "payload": payload}

    def git_worktrees(_cursor: str | None) -> dict[str, Any]:
        worktrees = run_command(["git", "-C", repo, "worktree", "list", "--porcelain"])
        origin_main = run_command(["git", "-C", repo, "rev-parse", "origin/main"]).strip()
        payload = {"origin_main": origin_main, "worktrees_porcelain": worktrees}
        return {"cursor": _digest(payload), "payload": payload}

    def runtime(_cursor: str | None) -> dict[str, Any]:
        payload = fetch_json(accepted_identity_url)
        return {"cursor": _digest(payload), "payload": payload}

    return {"github": github, "git_worktrees": git_worktrees, "runtime": runtime}


def command_probe(command: list[str], *, timeout_seconds: float = 20.0) -> Callable[[str | None], dict[str, Any]]:
    """Adapt one allowlisted argv command to the observation-runner protocol.

    Commands are never shell-interpreted.  They must emit exactly one JSON object
    with a source cursor and object payload; any other result remains an adapter
    failure for ``AdapterRunner`` to report, retry and eventually quarantine.
    """
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("probe command must be a non-empty argv list")

    def probe(_previous_cursor: str | None) -> dict[str, Any]:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout_seconds)
        if result.returncode:
            raise ValueError(result.stderr.strip() or f"probe command exited {result.returncode}")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError("probe command did not emit JSON") from exc
        if not isinstance(payload, dict) or set(payload) != {"cursor", "payload"} or not isinstance(payload["cursor"], str) or not isinstance(payload["payload"], dict):
            raise ValueError("probe command must emit an object cursor and object payload")
        return payload

    return probe


def command_probes(configuration: dict[str, Any]) -> dict[str, Callable[[str | None], dict[str, Any]]]:
    """Build only the six governed adapter probes from a deployment configuration."""
    allowed = set(AdapterRunner.REQUIRED_ADAPTERS)
    if not isinstance(configuration, dict) or set(configuration) - allowed:
        raise ValueError("probe configuration contains an unapproved adapter")
    return {adapter: command_probe(command) for adapter, command in configuration.items()}


def load_command_probes(path: Path) -> dict[str, Callable[[str | None], dict[str, Any]]]:
    """Load an exact JSON map of governed adapter names to argv lists."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("probe configuration must be a regular file")
    try:
        configuration = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("probe configuration is not valid JSON") from exc
    return command_probes(configuration)


def build_sync_launchd_plist(release_dir: Path, runtime: Path, probe_config: Path, *, interval_seconds: int) -> bytes:
    """Build the runnable shadow-only synchronization LaunchAgent definition."""
    if interval_seconds < 30:
        raise ValueError("sync interval must be at least thirty seconds")
    return plistlib.dumps({
        "Label": "com.marsys.pariprashna-assurance.shadow.sync",
        "ProgramArguments": [
            sys.executable, str(release_dir / "elevation_worker.py"),
            "--shadow-db", str(runtime / "elevation.sqlite3"),
            "--probe-config", str(probe_config), "--once",
        ],
        "StartInterval": interval_seconds,
        "RunAtLoad": True,
        "ProcessType": "Background",
        "WorkingDirectory": str(release_dir),
        "StandardOutPath": str(runtime / "sync.log"),
        "StandardErrorPath": str(runtime / "sync.error.log"),
    }, fmt=plistlib.FMT_XML, sort_keys=True)


class ShadowSyncWorker:
    def __init__(self, store: ElevationStore, *, probes: dict[str, Callable[[str | None], dict[str, Any]]], fresh_after_seconds: int = 300):
        self.runner = AdapterRunner(store, probes=probes, fresh_after_seconds=fresh_after_seconds)

    def sync_once(self) -> dict[str, dict[str, Any]]:
        return self.runner.collect_all()

    def run_forever(self, stop: threading.Event, *, interval_seconds: float = 60.0) -> None:
        if interval_seconds <= 0:
            raise ValueError("sync interval must be positive")
        while not stop.is_set():
            self.sync_once()
            stop.wait(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run shadow-only Paripraśna adapter synchronization")
    parser.add_argument("--shadow-db", type=Path, required=True)
    parser.add_argument("--probe-config", type=Path)
    parser.add_argument("--source-repo", type=Path)
    parser.add_argument("--accepted-identity-url")
    parser.add_argument("--interval-seconds", type=float, default=60.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    stop = threading.Event()
    for received in (signal.SIGINT, signal.SIGTERM):
        signal.signal(received, lambda _signum, _frame: stop.set())
    probes: dict[str, Callable[[str | None], dict[str, Any]]] = {}
    if args.source_repo or args.accepted_identity_url:
        if not args.source_repo or not args.accepted_identity_url:
            raise SystemExit("--source-repo and --accepted-identity-url must be provided together")
        probes.update(builtin_probes(args.source_repo, args.accepted_identity_url))
    if args.probe_config:
        configured = load_command_probes(args.probe_config)
        collision = set(probes) & set(configured)
        if collision:
            raise SystemExit(f"probe configuration duplicates built-in adapters: {', '.join(sorted(collision))}")
        probes.update(configured)
    if not probes:
        raise SystemExit("at least one built-in or configured probe is required")
    worker = ShadowSyncWorker(ElevationStore(args.shadow_db), probes=probes)
    if args.once:
        print(json.dumps(worker.sync_once(), sort_keys=True))
        return
    worker.run_forever(stop, interval_seconds=args.interval_seconds)


if __name__ == "__main__":
    main()
