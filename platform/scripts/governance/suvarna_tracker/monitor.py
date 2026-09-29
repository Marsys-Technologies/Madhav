"""Suvarṇa Monitor — the environment checker for the autonomous campaign.

    python -m suvarna_tracker.monitor [--once | --watch SECONDS] [--emit] [--repair] [--json]

Seven checks decide whether the environment the campaign runs in is sound: the DB proxy port, the
read-only credential file's permissions, the laptop's power state, whether sleep is prevented, the
hold switch, free disk space, and the tracker's own health endpoint. Each returns ``ok`` / ``warn`` /
``block``; the overall status is the worst of the seven, and the process exit code mirrors it
(0 / 1 / 2) so this doubles as a CI-style gate.

Design rules:
- **Never fabricate a pass.** A check that cannot measure reports ``warn`` with the reason, never
  ``ok`` (CLAUDE.md §N.8 — a signal without a real detector behind it is null, not green).
- **Never read the credential file's contents.** The credential check only ``os.stat``s it; it never
  opens it, and never prints anything beyond the path-free facts an operator needs (mode, existence).
- **Conservative repair.** ``--repair`` only starts a process that is verifiably not already running,
  and never touches hold / credential / disk / power — those need a human. The hold switch, when on,
  suppresses every repair action, not only the ones it names explicitly.
- **Injectable everything that touches the outside world.** ``Config`` carries the port numbers, the
  paths, and every subprocess/HTTP/disk helper as fields with real defaults, so tests can swap in
  fakes without any real network call beyond 127.0.0.1 and without spawning any real process.
"""
from __future__ import annotations

import argparse
import json
import os

# N-20 (native, 2026-09-29): the read-only credential lives in one file outside every repository,
# owner-only (mode 600). Tools default to it; its contents are never read or printed by these tools.
DEFAULT_PGENV = os.path.expanduser("~/.config/suvarna/pgenv.sh")
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "suvarna_tracker"

from suvarna_tracker.detectors import _run as _det_run  # noqa: E402
from suvarna_tracker.detectors import port_open as _det_port_open  # noqa: E402
from suvarna_tracker.detectors import power_source as _det_power_source  # noqa: E402
from suvarna_tracker.events import append, now_iso  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

CHECK_NAMES = ("db_proxy", "credential", "power", "sleep_prevented", "hold", "disk", "tracker")
STATUS_RANK = {"ok": 0, "warn": 1, "block": 2}


# --------------------------------------------------------------------------------------------
# Default helpers (the real world). Every one of these is a Config field so tests can replace it.
# --------------------------------------------------------------------------------------------

def _default_run_fn(cmd: list[str] | str, timeout: int = 5) -> tuple[int, str]:
    return _det_run(cmd, timeout=timeout)


def _default_http_get(url: str, timeout: float = 3.0) -> tuple[int | None, str, str | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (127.0.0.1 only, by contract)
            return resp.status, resp.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return exc.code, body, None
    except Exception as exc:  # noqa: BLE001 — unreachable/timeout/etc. is data, not a crash
        return None, "", f"{type(exc).__name__}: {exc}"


def _default_launch(argv: list[str], cwd: str | None = None, log_path: str | None = None,
                    env: dict | None = None) -> None:
    """Start a detached process. Never waits; never raises out of the caller's control flow here —
    the caller (a _repair_* function) wraps this so a launch failure becomes a reported string, not
    a crash."""
    log_fh = open(log_path, "ab") if log_path else subprocess.DEVNULL
    try:
        subprocess.Popen(argv, cwd=cwd, stdout=log_fh, stderr=log_fh, stdin=subprocess.DEVNULL,
                         env=env, start_new_session=True, close_fds=True)
    finally:
        if log_path:
            log_fh.close()


def _default_disk_free_bytes(path: str) -> float:
    p = os.path.abspath(path)
    while not os.path.exists(p):
        parent = os.path.dirname(p)
        if not parent or parent == p:
            p = "/"
            break
        p = parent
    st = os.statvfs(p)
    return float(st.f_frsize) * st.f_bavail


# --------------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------------

@dataclass
class Config:
    home: str
    pgenv: str | None = None
    db_port: int = 5433
    tracker_port: int = 8765
    tracker_host: str = "127.0.0.1"
    package_dir: str = HERE
    run_dir: str = ""
    hold_path: str = ""
    state_path: str = ""
    events_path: str = ""
    port_open_fn: Callable[[int], bool] | None = None
    power_source_fn: Callable[[], str] | None = None
    run_fn: Callable[..., tuple[int, str]] | None = None
    http_get_fn: Callable[[str, float], tuple[int | None, str, str | None]] | None = None
    launch_fn: Callable[..., None] | None = None
    disk_free_fn: Callable[[str], float] | None = None

    def __post_init__(self) -> None:
        self.run_dir = self.run_dir or os.path.join(self.home, "run")
        self.hold_path = self.hold_path or os.path.join(self.run_dir, "SUVARNA_HOLD")
        self.state_path = self.state_path or os.path.join(self.run_dir, "monitor_state.json")
        self.events_path = self.events_path or os.path.join(self.run_dir, "EVENTS.jsonl")
        self.port_open_fn = self.port_open_fn or _det_port_open
        self.power_source_fn = self.power_source_fn or _det_power_source
        self.run_fn = self.run_fn or _default_run_fn
        self.http_get_fn = self.http_get_fn or _default_http_get
        self.launch_fn = self.launch_fn or _default_launch
        self.disk_free_fn = self.disk_free_fn or _default_disk_free_bytes

    @property
    def tracker_stop_path(self) -> str:
        return os.path.join(self.run_dir, "TRACKER_STOP")


def default_config() -> Config:
    home = os.environ.get("SUVARNA_HOME", "/Users/Dev/suvarna")
    return Config(
        home=home,
        pgenv=os.environ.get("SUVARNA_PGENV") or DEFAULT_PGENV,
        db_port=int(os.environ.get("SUVARNA_DB_PORT", "5433")),
        tracker_port=int(os.environ.get("SUVARNA_TRACKER_PORT", "8765")),
        events_path=os.environ.get("SUVARNA_EVENTS", os.path.join(home, "run", "EVENTS.jsonl")),
    )


@dataclass
class CheckResult:
    name: str
    status: str          # ok | warn | block
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------------------------
# The seven checks
# --------------------------------------------------------------------------------------------

def check_db_proxy(cfg: Config) -> CheckResult:
    if cfg.port_open_fn(cfg.db_port):
        return CheckResult("db_proxy", "ok", f"port {cfg.db_port} accepting connections")
    return CheckResult("db_proxy", "block", f"port {cfg.db_port} not accepting connections")


def check_credential(cfg: Config) -> CheckResult:
    """Existence + permission bits only — the file's contents are never opened or read, and nothing
    beyond the mode/existence facts below is reported (no path component is printed)."""
    if not cfg.pgenv:
        return CheckResult("credential", "block", "SUVARNA_PGENV is not set")
    try:
        mode = os.stat(cfg.pgenv).st_mode
    except OSError:
        return CheckResult("credential", "block", "credential file does not exist")
    if mode & 0o077:
        return CheckResult("credential", "warn",
                            f"credential file is group- or world-readable (mode {oct(mode & 0o777)})")
    return CheckResult("credential", "ok", "credential file exists with restricted permissions")


_BATTERY_PCT_RE = re.compile(r"(\d+)%")


def check_power(cfg: Config) -> CheckResult:
    src = cfg.power_source_fn()
    if src == "ac":
        return CheckResult("power", "ok", "on AC power")
    if src.startswith("battery"):
        m = _BATTERY_PCT_RE.search(src)
        if not m:
            return CheckResult("power", "warn", f"on battery, level unknown ({src})")
        pct = int(m.group(1))
        if pct < 50:
            return CheckResult("power", "block", f"on battery at {pct}% (below 50%)")
        return CheckResult("power", "warn", f"on battery at {pct}%")
    return CheckResult("power", "warn", f"power source unknown ({src})")


_ASSERTION_RE = re.compile(r"(PreventUserIdleSystemSleep|PreventSystemSleep)\s+(\d+)")


def check_sleep_prevented(cfg: Config) -> CheckResult:
    rc, out = cfg.run_fn(["pgrep", "-x", "caffeinate"], timeout=5)
    if rc == 0 and out.strip():
        return CheckResult("sleep_prevented", "ok", "caffeinate is running")
    rc2, out2 = cfg.run_fn(["pmset", "-g", "assertions"], timeout=5)
    if rc2 == 0 and any(v == "1" for _, v in _ASSERTION_RE.findall(out2)):
        return CheckResult("sleep_prevented", "ok", "a sleep-prevention assertion is active")
    return CheckResult("sleep_prevented", "warn", "sleep is not prevented (no caffeinate, no active assertion)")


def check_hold(cfg: Config) -> CheckResult:
    if os.path.exists(cfg.hold_path):
        return CheckResult("hold", "block", "hold switch on: dispatch nothing new")
    return CheckResult("hold", "ok", "hold switch off")


def check_disk(cfg: Config) -> CheckResult:
    free_gb = cfg.disk_free_fn(cfg.home) / (1024 ** 3)
    if free_gb < 5:
        return CheckResult("disk", "block", f"{free_gb:.1f} GB free (below 5 GB)")
    if free_gb < 20:
        return CheckResult("disk", "warn", f"{free_gb:.1f} GB free (below 20 GB)")
    return CheckResult("disk", "ok", f"{free_gb:.1f} GB free")


def check_tracker(cfg: Config) -> CheckResult:
    url = f"http://{cfg.tracker_host}:{cfg.tracker_port}/api/health"
    status, body, err = cfg.http_get_fn(url, 3.0)
    if err or status is None:
        return CheckResult("tracker", "warn", f"tracker unreachable ({err or 'no response'})")
    try:
        data = json.loads(body) if body else {}
    except ValueError:
        data = {}
    if status == 200 and data.get("ok") is True:
        return CheckResult("tracker", "ok", "tracker healthy")
    return CheckResult("tracker", "warn", f"tracker unhealthy (status {status}, ok={data.get('ok')})")


_CHECK_FNS: dict[str, Callable[[Config], CheckResult]] = {
    "db_proxy": check_db_proxy,
    "credential": check_credential,
    "power": check_power,
    "sleep_prevented": check_sleep_prevented,
    "hold": check_hold,
    "disk": check_disk,
    "tracker": check_tracker,
}


def _safe_check(name: str, cfg: Config) -> CheckResult:
    try:
        return _CHECK_FNS[name](cfg)
    except Exception as exc:  # noqa: BLE001 — a broken check is a warn, never a crash (CLAUDE.md §N.8)
        return CheckResult(name, "warn", f"{name} check raised {type(exc).__name__}: {exc}"[:300])


def run_checks(cfg: Config) -> list[CheckResult]:
    return [_safe_check(name, cfg) for name in CHECK_NAMES]


def overall_status(results: list[CheckResult]) -> str:
    if not results:
        return "ok"
    return max(results, key=lambda r: STATUS_RANK.get(r.status, 1)).status


def exit_code(status: str) -> int:
    return {"ok": 0, "warn": 1, "block": 2}.get(status, 1)


# --------------------------------------------------------------------------------------------
# Repair (conservative: only starts a process verifiably not already running; never touches
# hold / credential / disk / power)
# --------------------------------------------------------------------------------------------

def _repair_tracker(cfg: Config) -> list[str]:
    if os.path.exists(cfg.tracker_stop_path):
        return []  # operator asked the supervisor to stay down — do not second-guess it
    rc, out = cfg.run_fn(["pgrep", "-f", "run_tracker.sh"], timeout=5)
    if rc == 0 and out.strip():
        return ["tracker: run_tracker.sh already running, not restarting"]
    script = os.path.join(cfg.package_dir, "run_tracker.sh")
    try:
        cfg.launch_fn(["bash", script], cwd=cfg.package_dir, log_path=None, env=dict(os.environ))
        return [f"tracker: started {os.path.basename(script)} detached"]
    except Exception as exc:  # noqa: BLE001
        return [f"tracker: repair failed: {type(exc).__name__}: {exc}"]


def _repair_db_proxy(cfg: Config) -> list[str]:
    # Match a proxy on OUR port only: other workstreams run their own proxies on other ports
    # (the Gochara lane uses 55440), and one of those must not stop this repair.
    rc, out = cfg.run_fn(["pgrep", "-f", f"cloud-sql-proxy.*--port[ =]{cfg.db_port}( |$)"], timeout=5)
    if rc == 0 and out.strip():
        return [f"db_proxy: a cloud-sql-proxy for port {cfg.db_port} is already running (starting up?), not starting another"]
    log_path = os.path.join(cfg.run_dir, "proxy.log")
    argv = ["cloud-sql-proxy", "--address", "127.0.0.1", "--port", str(cfg.db_port),
            "madhav-astrology:asia-south1:amjis-postgres"]
    try:
        os.makedirs(cfg.run_dir, exist_ok=True)
        cfg.launch_fn(argv, cwd=None, log_path=log_path, env=None)
        return [f"db_proxy: started cloud-sql-proxy on port {cfg.db_port} detached"]
    except Exception as exc:  # noqa: BLE001
        return [f"db_proxy: repair failed: {type(exc).__name__}: {exc}"]


def _repair_sleep(cfg: Config) -> list[str]:
    rc, out = cfg.run_fn(["pgrep", "-x", "caffeinate"], timeout=5)
    if rc == 0 and out.strip():
        return ["sleep_prevented: caffeinate already running"]
    try:
        cfg.launch_fn(["caffeinate", "-dimsu"], cwd=None, log_path=None, env=None)
        return ["sleep_prevented: started caffeinate -dimsu detached"]
    except Exception as exc:  # noqa: BLE001
        return [f"sleep_prevented: repair failed: {type(exc).__name__}: {exc}"]


def repair(cfg: Config, by_name: dict[str, CheckResult]) -> list[str]:
    """Attempt to fix the checks that can be fixed unattended. The hold switch, when on, suppresses
    every repair action (dispatch nothing new means nothing new — including a repair launch)."""
    if os.path.exists(cfg.hold_path):
        return []
    actions: list[str] = []
    tracker = by_name.get("tracker")
    if tracker is not None and tracker.status != "ok":
        actions += _repair_tracker(cfg)
    db_proxy = by_name.get("db_proxy")
    if db_proxy is not None and db_proxy.status != "ok":
        actions += _repair_db_proxy(cfg)
    sleep = by_name.get("sleep_prevented")
    if sleep is not None and sleep.status != "ok":
        actions += _repair_sleep(cfg)
    return actions


# --------------------------------------------------------------------------------------------
# --emit: heartbeat every run, a note only when the non-ok set changes
# --------------------------------------------------------------------------------------------

_SHORT = {
    ("db_proxy", "block"): "down", ("db_proxy", "warn"): "degraded",
    ("credential", "block"): "missing/insecure", ("credential", "warn"): "too open",
    ("power", "block"): "critical", ("power", "warn"): "battery",
    ("sleep_prevented", "warn"): "not prevented",
    ("hold", "block"): "on",
    ("disk", "block"): "critical", ("disk", "warn"): "low",
    ("tracker", "warn"): "unreachable",
}


def _summary_line(overall: str, results: list[CheckResult]) -> str:
    if overall == "ok":
        return f"ok: {len(results)}/{len(results)}"
    non_ok = [r for r in results if r.status != "ok"]
    parts = [f"{r.name} {_SHORT.get((r.name, r.status), r.status)}" for r in non_ok]
    prefix = "BLOCK" if overall == "block" else "WARN"
    return f"{prefix}: " + "; ".join(parts)


def _load_state(cfg: Config) -> dict:
    try:
        with open(cfg.state_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_state(cfg: Config, state: dict) -> None:
    os.makedirs(cfg.run_dir, exist_ok=True)
    tmp = f"{cfg.state_path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, cfg.state_path)  # atomic


def emit(cfg: Config, results: list[CheckResult], overall: str, repairs: list[str]) -> list[str]:
    """Append a heartbeat every call, plus a note when the non-ok set changed since the last run
    (dedupe via monitor_state.json) and one note per repair action taken. Never raises — every
    failure is caught and returned as a string in the result."""
    errors: list[str] = []
    summary = _summary_line(overall, results)

    def _append(ev: dict, what: str) -> None:
        try:
            append(cfg.events_path, ev)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{what} emit failed: {type(exc).__name__}: {exc}")

    _append({"kind": "heartbeat", "actor": "monitor", "detail": summary}, "heartbeat")

    non_ok = sorted(r.name for r in results if r.status != "ok")
    prev = _load_state(cfg)
    if prev.get("non_ok") != non_ok:
        _append({"kind": "note", "actor": "monitor", "detail": summary}, "note")

    for action in repairs:
        _append({"kind": "note", "actor": "monitor", "detail": f"repair: {action}"}, "repair note")

    try:
        _save_state(cfg, {"non_ok": non_ok, "at": now_iso()})
    except Exception as exc:  # noqa: BLE001
        errors.append(f"state save failed: {type(exc).__name__}: {exc}")
    return errors


# --------------------------------------------------------------------------------------------
# One run, printing, CLI
# --------------------------------------------------------------------------------------------

def run_once(cfg: Config, emit_flag: bool = False, repair_flag: bool = False) -> dict:
    results = run_checks(cfg)
    by_name = {r.name: r for r in results}
    repairs = repair(cfg, by_name) if repair_flag else []
    overall = overall_status(results)
    emit_errors = emit(cfg, results, overall, repairs) if emit_flag else []
    return {
        "generated_at": now_iso(),
        "overall": overall,
        "checks": [r.to_dict() for r in results],
        "repairs": repairs,
        "emit_errors": emit_errors,
    }


def _print_human(report: dict) -> None:
    for c in report["checks"]:
        print(f"{c['status'].upper():5} {c['name']:16} {c['detail']}")
    print(f"overall: {report['overall'].upper()}")
    if report["repairs"]:
        print("repairs:")
        for r in report["repairs"]:
            print(f"  - {r}")
    if report["emit_errors"]:
        print("emit errors:")
        for e in report["emit_errors"]:
            print(f"  - {e}")


def _print(report: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        _print_human(report)


def watch(cfg: Config, seconds: int, emit_flag: bool, repair_flag: bool, as_json: bool) -> None:
    interval = max(15, seconds)
    stop_event = threading.Event()

    def _on_term(signum, frame) -> None:  # noqa: ANN001
        stop_event.set()

    prev_handler = signal.signal(signal.SIGTERM, _on_term)
    try:
        while not stop_event.is_set():
            report = run_once(cfg, emit_flag=emit_flag, repair_flag=repair_flag)
            _print(report, as_json)
            stop_event.wait(interval)
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGTERM, prev_handler)


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suvarṇa Monitor — environment checker for the autonomous campaign")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="run the checks once and exit (default)")
    mode.add_argument("--watch", type=int, metavar="SECONDS", help="loop, re-checking every SECONDS (minimum 15)")
    ap.add_argument("--emit", action="store_true", help="append a heartbeat (and note on change) to the event log")
    ap.add_argument("--repair", action="store_true", help="conservatively try to fix what can be fixed unattended")
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    cfg = default_config()
    if args.watch:
        watch(cfg, args.watch, args.emit, args.repair, args.json)
        return 0
    report = run_once(cfg, emit_flag=args.emit, repair_flag=args.repair)
    _print(report, args.json)
    return exit_code(report["overall"])


if __name__ == "__main__":
    raise SystemExit(main())
