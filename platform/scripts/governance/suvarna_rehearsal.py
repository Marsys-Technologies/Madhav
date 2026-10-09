#!/usr/bin/env python3
"""suvarna_rehearsal.py -- Suvarna E5.6 / E5.7: the off-production rehearsal harness (the parts that need no production data).

Track E brief 7 (E5.6 rehearsal environment, E5.7 L0 rebuild drill), plan items E5.6 (detector `evidence_verified`,
path `E5.6/REHEARSAL.json`, expect `result == "PASS"`, required key `cases`) and E5.7 (`E5.7/L0_REBUILD_DRILL.json`).
Design: /Users/Dev/suvarna-evidence/E5.6/DESIGN.md. The cluster PROVISIONING scripts (`rehearsal/rehearsal_cluster.sh`,
`apply_schema.sh`, `replay_schema.py`, `rehearsal_guard.py`) are E5.6 phase 1 and are reused, not rewritten; this module adds:

  A. connection policy        every database connection this harness opens goes through `connect_checked`: the rehearsal
                              URL guard (127.0.0.1:55432, db rehearsal*, no password) or, for `--self-test`, the disposable
                              cluster's own loopback endpoint. The PG* / DATABASE_URL environment is scrubbed around the
                              dial (hostaddr/passfile pinned), and the server that ANSWERED is verified (data_directory,
                              address, port, database) before the connection is logged or returned. A refused endpoint opens
                              NO socket; a wrong answering server is closed and logged as refused. The log of opened,
                              verified connections is what the `no_production_write` case is judged on (policy and endpoint
                              must agree; a rehearsal document may hold rehearsal-policy connections only).
  B. cluster lifecycle        init / start / stop / status / reap / adopt for a long-lived rehearsal data dir with an
                              ownership MARKER, an exclusive flock LOCKFILE, and a refusal to ever listen on or trust any
                              address other than 127.0.0.1 (+ the unix socket inside the root). Binaries run under `env -i`.
  C. evidence                 `REHEARSAL.json`: a CLOSED schema; every case is judged by a pure function over its recorded
                              raw measurements (so the validator RE-DERIVES each result and a hand-edited `PASS` fails);
                              a case that was not measured reads UNMEASURED with a `NEEDS_*` reason, never PASS; a
                              `self_test` document can never read PASS and the writer refuses to put one at the detector's path.
  D. self-test                the cases that can run on a disposable PostgreSQL with SYNTHETIC data (no production data, no
                              credential): the idempotent-rebuild semantic fingerprint (E5.5's own `fingerprint_rows`/
                              `table_fingerprint`), the family-intersecting dispatch refusal (through `suvarna_level_wave.run_cli`),
                              the hold refusal (through the tracker's `hold_guard.evaluate`, when `--tracker-dir` names it),
                              and the connection log. Everything that needs the real orchestrator, the replayed schema, the
                              seed or a canary mechanism is a `NEEDS_*` case.
  E. E5.7 comparison          `compare_fingerprint_sets`: production vs rehearsal semantic fingerprints (the SAME definition
                              as E5.5; inputs carry its marker) over a REQUIRED `expected_assets` list. Every difference
                              needs an explanation (reason code valid for the difference kind, >= 40 characters, not
                              repeated across assets) AND an SS-recorded decision id `N-<n>`; an uncovered or unexpected
                              asset, or too large a share of differing assets, fails. The output embeds the inputs, hashes,
                              commit and tool hash; `validate_drill` re-derives it.

Evidence binding (what a forged file cannot do): `generated_by.tool_sha256` must equal the repo tool's sha256 (at the evidence
commit when the repo has it); in `rehearsal` mode each measured case's first evidence pointer is the sha256 of the canonical
record of ITS measured values, and `--evidence-root` re-reads that file. What the TRACKER can additionally require (mode,
schema, a `commit_key`/`commit` pin, `max_age_hours`) is a plan_model.json change owned by Strategic Suvarna, not this tool.

Usage:
  suvarna_rehearsal.py self-test --out PATH [--tracker-dir DIR] [--repo DIR]     (writes a self_test evidence document)
  suvarna_rehearsal.py validate PATH [--evidence-root DIR]                       (exit 0 valid, 2 invalid)
  suvarna_rehearsal.py cluster init|start|stop|status|reap|adopt [--root DIR] [--port N] [--pg-bin DIR] [--remove-data --confirm ROOT]
  suvarna_rehearsal.py compare-fingerprints --pre prod.json --post rehearsal.json --expected assets.json|declarations --rows rows.json --runtime runtime.json [--coverage cov.json] --commit SHA [--explained e.json] [--out drill.json]
  suvarna_rehearsal.py validate-drill PATH
  suvarna_rehearsal.py drill expected|reader-spec|baseline|validate-baseline|rehearsal-fingerprints|compare|status ...   (E5.7 mirror wiring, suvarna_mirror_drill.py)
  (compare-fingerprints --expected declarations  = the DECLARED L0 assets of 00_ARCHITECTURE/control/FINGERPRINT_DECLARATIONS.json)
Exit: 0 ok · 2 refused / invalid · 4 a measured case failed (self-test) · 5 error.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import fcntl
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import uuid
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "rehearsal"))
import rehearsal_guard as rg  # noqa: E402  (E5.6 phase 1: the one URL decision point)

REPO_ROOT = HERE.parents[2]
TOOL_NAME = "suvarna_rehearsal.py"
TOOL_REL = "platform/scripts/governance/suvarna_rehearsal.py"

# ───────────────────────────── constants ─────────────────────────────

LOOPBACK = rg.REHEARSAL_HOST                       # "127.0.0.1": the only host this harness ever targets
# The ONE place the rehearsal root is named (phase-1 layout: <root>/pg data, <root>/sock, <root>/pg.log). The environment
# override exists so tests can use a temp root; production use never sets it.
DEFAULT_ROOT = os.environ.get("E56_REHEARSAL_ROOT_FOR_TESTS") or "/Users/Dev/suvarna/rehearsal"
DEFAULT_PORT = rg.REHEARSAL_PORT                   # 55432
DEFAULT_PG_BIN = "/opt/homebrew/opt/postgresql@15/bin"
FORBIDDEN_PORTS = frozenset({5432, 6432, 6543})    # production-shaped ports: never targeted, whatever the policy
MARKER_NAME = ".suvarna_rehearsal_cluster.json"
MARKER_KIND = "suvarna-rehearsal-cluster"
MARKER_VERSION = 1
LOCK_NAME = "rehearsal.lock"
SOCK_PATH_LIMIT = 90                               # a unix socket path must stay well under ~104 bytes
EVIDENCE_SCHEMA = "suvarna-rehearsal-evidence/v1"
DRILL_SCHEMA = "suvarna-l0-drill-evidence/v1"
DETECTOR_EVIDENCE_PATH = "E5.6/REHEARSAL.json"     # the plan item's evidence_verified path under $SUVARNA_HOME/evidence
HEX64 = re.compile(r"[0-9a-f]{64}")
HEX40 = re.compile(r"[0-9a-f]{40}")


class RehearsalError(Exception):
    """Base class: bad input or a refused action; nothing was changed."""


class EndpointRefused(RehearsalError):
    """A database endpoint the policy does not allow. No socket was opened."""


class LifecycleError(RehearsalError):
    """A cluster lifecycle action was refused (marker, lock, path, address or process identity)."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tool_sha256() -> str:
    return sha256_file(Path(__file__).resolve())


# ═════════════════════════ A. connection policy ═════════════════════════

def rehearsal_policy(url: Any) -> str:
    """The rehearsal URL guard of E5.6 phase 1, unchanged: returns the NORMALISED url or raises ValueError."""
    return rg.normalise_rehearsal_url(url)


def disposable_policy(url: Any) -> str:
    """For `--self-test` only: an explicit loopback URL on a port that is none of the forbidden ones, database
    `suvarna_disposable*`, no password, no query. The disposable fixture itself verifies the server identity."""
    if not isinstance(url, str) or not url or re.search(r"[\s\x00-\x1f\x7f\\]", url):
        raise ValueError("empty URL or whitespace/control character")
    parts = urlsplit(url)
    if parts.scheme not in ("postgres", "postgresql") or parts.query or parts.fragment or parts.password is not None:
        raise ValueError("scheme must be postgres(ql), with no password, query or fragment")
    authority = url.split("://", 1)[1].split("/", 1)[0]
    if authority.rpartition("@")[2].rsplit(":", 1)[0] != LOOPBACK:
        raise ValueError(f"host is not exactly {LOOPBACK}")
    try:
        port = parts.port
    except ValueError:
        port = None
    if port is None or port in FORBIDDEN_PORTS or port == rg.REHEARSAL_PORT:
        raise ValueError(f"port {port!r} is missing or one of the production/rehearsal ports")
    if not re.fullmatch(r"suvarna_disposable[a-z0-9_]*", parts.path.lstrip("/")):
        raise ValueError("database is not suvarna_disposable*")
    return url


POLICIES: dict[str, Callable[[Any], str]] = {"rehearsal": rehearsal_policy, "disposable": disposable_policy}


class ConnectionLog:
    """Every endpoint the harness OPENED and every one it REFUSED (a refusal opens nothing). The `no_production_write`
    case is judged from `opened`."""

    def __init__(self) -> None:
        self.opened: list[dict] = []
        self.refused: list[dict] = []

    def snapshot(self) -> dict:
        return {"opened": [dict(e) for e in self.opened], "refused_count": len(self.refused)}


def _endpoint(url: str) -> dict:
    p = urlsplit(url)
    return {"host": p.hostname or "", "port": p.port or 0, "database": p.path.lstrip("/")}


_SCRUB_NAMES = ("DATABASE_URL", "POSTGRES_URL", "DIRECT_DATABASE_URL")
_ENV_LOCK = threading.Lock()


@contextlib.contextmanager
def scrubbed_pg_env():
    """libpq honours PGHOSTADDR / PGSERVICE / PGPASSFILE / PGOPTIONS ... for anything the URL leaves unset, and the URL itself
    may be shadowed: every PG* variable and DATABASE_URL is removed around a connect and restored after."""
    with _ENV_LOCK:
        saved = {k: v for k, v in os.environ.items() if k.startswith("PG") or k in _SCRUB_NAMES}
        for k in saved:
            del os.environ[k]
        try:
            yield
        finally:
            os.environ.update(saved)


def _psycopg_connect(url: str) -> Any:
    import psycopg  # noqa: PLC0415
    return psycopg.connect(url, hostaddr=LOOPBACK, passfile="/nonexistent/.pgpass", connect_timeout=10)


def _psycopg_available() -> bool:
    """True when the driver imports. Any failure to import it (not installed, blocked, broken) reads as unavailable."""
    try:
        __import__("psycopg")
    except Exception:  # noqa: BLE001
        return False
    return True


def _server_identity(conn: Any) -> dict:
    row = conn.execute("SELECT current_setting('data_directory'), coalesce(host(inet_server_addr()), ''), "
                       "coalesce(inet_server_port(), 0), current_database()").fetchone()
    return {"data_directory": str(row[0]), "host": str(row[1]), "port": int(row[2]), "database": str(row[3])}


def _same_path(a: str, b: str) -> bool:
    return bool(a) and bool(b) and os.path.realpath(a) == os.path.realpath(b)


def _identity_problem(policy: str, ident: Mapping, expect: Mapping | None) -> str | None:
    """None when the server that ANSWERED is the one the policy allows, else why not."""
    if ident["host"] != LOOPBACK or ident["port"] in FORBIDDEN_PORTS:
        return "the server that answered is not on 127.0.0.1 or is on a forbidden port"
    if policy == "rehearsal":
        if ident["port"] != DEFAULT_PORT or not rg.DB_NAME_RE.fullmatch(ident["database"]):
            return "the answering server is not the rehearsal port/database"
        if not _same_path(ident["data_directory"], f"{DEFAULT_ROOT}/pg"):
            return "the answering server's data_directory is not the rehearsal data dir"
        return None
    if policy != "disposable":
        return f"no identity rule for policy {policy!r}"
    if not (isinstance(expect, Mapping) and _same_path(ident["data_directory"], str(expect.get("data_directory", "")))
            and ident["port"] == expect.get("port") and ident["database"].startswith("suvarna_disposable")):
        return "the answering server is not the disposable cluster the fixture started"
    return None


def connect_checked(url: Any, policy: str, log: ConnectionLog, *, connect: Callable[..., Any] | None = None,
                    expect: Mapping | None = None) -> Any:
    """Open a connection ONLY to an endpoint the policy accepts, then VERIFY which server answered (data_directory, address,
    port, database) before the connection is logged or returned. The NORMALISED url is what is dialled, with the PG*
    environment scrubbed and hostaddr/passfile pinned. A refused endpoint, or an answering server that is not the allowed
    one, raises EndpointRefused, is logged as refused and leaves no open connection. `expect` carries the disposable
    cluster's own identity ({data_directory, port}) for the `disposable` policy."""
    if policy not in POLICIES:
        raise EndpointRefused(f"unknown connection policy {policy!r}")
    try:
        normalised = POLICIES[policy](url)
    except ValueError as exc:
        log.refused.append({"policy": policy, "reason": str(exc)[:200]})
        raise EndpointRefused(f"{policy} policy refused the endpoint: {exc}") from exc
    ep = _endpoint(normalised)
    if ep["host"] != LOOPBACK or ep["port"] in FORBIDDEN_PORTS:        # belt and braces over the policy itself
        log.refused.append({"policy": policy, "reason": "host/port outside the allowed set"})
        raise EndpointRefused("endpoint is not loopback or is a forbidden port")
    dial = connect or _psycopg_connect
    with scrubbed_pg_env():
        conn = dial(normalised)
    try:
        ident = _server_identity(conn)
        why = _identity_problem(policy, ident, expect)
    except Exception as exc:  # noqa: BLE001 - an unreadable identity is a refusal, never a pass
        ident, why = None, f"could not verify the answering server ({type(exc).__name__})"
    if why is not None:
        with contextlib.suppress(Exception):
            conn.close()
        log.refused.append({"policy": policy, "reason": why})
        raise EndpointRefused(why)
    log.opened.append({"host": ident["host"], "port": ident["port"], "database": ident["database"], "policy": policy,
                       "data_directory": ident["data_directory"], "verified": True})
    return conn


# ═════════════════════════ B. cluster lifecycle ═════════════════════════

def _proc_command(pid: int) -> str | None:
    """`ps -o command=` for a pid under a fixed locale; '' when there is no such process; None when `ps` cannot answer."""
    ps = next((c for c in ("/bin/ps", "/usr/bin/ps") if os.path.exists(c)), None)
    if ps is None:
        return None
    try:
        p = subprocess.run([ps, "-p", str(pid), "-o", "command="], capture_output=True, text=True, timeout=10,
                           env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"})
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    out = p.stdout.strip()
    if p.returncode == 1 and not out:
        return ""
    return out if p.returncode == 0 and out else None


def _is_postmaster_for(command: str, data_dir: Path) -> bool:
    """Token-wise: `<...>/postgres -D <data_dir> ...` (never a substring match)."""
    tok = command.split()
    return (bool(tok) and os.path.basename(tok[0]) == "postgres" and "-D" in tok[:-1]
            and tok[tok.index("-D") + 1] == str(data_dir))


class _Layout:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.data = self.root / "pg"
        self.sock = self.root / "sock"
        self.log = self.root / "pg.log"
        self.marker = self.root / MARKER_NAME
        self.lock = self.root / LOCK_NAME


def _check_root(root: Path, *, create: bool) -> None:
    if not root.is_absolute() or str(root) != os.path.normpath(str(root)):
        raise LifecycleError(f"root {str(root)!r} must be an absolute, normalised path")
    p = root
    while str(p) != "/":                                   # no symlink anywhere on the path
        if p.is_symlink():
            raise LifecycleError(f"refusing: {p} is a symlink")
        p = p.parent
    if root.exists():
        if not root.is_dir():
            raise LifecycleError(f"{root} exists and is not a directory")
        if os.path.realpath(root) != str(root):
            raise LifecycleError(f"{root} does not resolve to itself")
        st = root.stat()
        if st.st_uid != os.getuid():
            raise LifecycleError(f"{root} is not owned by the current user")
        if st.st_mode & 0o077:
            raise LifecycleError(f"{root} must not be accessible to group/other (chmod 700)")
    elif create:
        root.mkdir(parents=True, mode=0o700)
        os.chmod(root, 0o700)
    else:
        raise LifecycleError(f"{root} does not exist")


def read_marker(root: str | Path) -> dict | None:
    """The ownership marker, or None when absent/invalid. Valid = our kind and version, this root, loopback host, an int
    port that is not forbidden, and this uid."""
    lay = _Layout(root)
    try:
        if lay.marker.is_symlink():
            return None
        m = json.loads(lay.marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ok = (isinstance(m, dict) and m.get("kind") == MARKER_KIND and m.get("v") == MARKER_VERSION
          and m.get("root") == str(lay.root) and m.get("host") == LOOPBACK
          and isinstance(m.get("port"), int) and not isinstance(m.get("port"), bool)
          and 1024 <= m["port"] <= 65535 and m["port"] not in FORBIDDEN_PORTS and m.get("uid") == os.getuid())
    return m if ok else None


def _write_marker(lay: _Layout, port: int) -> dict:
    m = {"kind": MARKER_KIND, "v": MARKER_VERSION, "root": str(lay.root), "host": LOOPBACK, "port": port,
         "uid": os.getuid()}
    tmp = lay.marker.with_name(MARKER_NAME + ".tmp")
    tmp.write_text(json.dumps(m, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, lay.marker)
    return m


@contextlib.contextmanager
def _locked(lay: _Layout):
    """Exclusive, non-blocking flock for every mutating lifecycle action: two sessions never race a start/stop/reap, and the
    kernel releases it when a holder dies (no stale lock, no pid-reuse guess)."""
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lay.lock, flags, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise LifecycleError("another lifecycle command holds the rehearsal lock") from None
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())
        yield
    finally:
        os.close(fd)


def _pg_env(home: str, pg_bin: str) -> dict:
    """`env -i`: nothing inherited (no PG*, DATABASE_URL, credential file); a private empty HOME."""
    return {"PATH": f"{pg_bin}:/usr/bin:/bin", "HOME": home, "LANG": "en_US.UTF-8",
            "PGPASSFILE": f"{home}/.no-pgpass", "PGSERVICEFILE": f"{home}/.no-pg-service"}


def _run_pg(argv: list[str], pg_bin: str, *, timeout: int = 180) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory(prefix="rehearsal-home.") as home:
        return subprocess.run(argv, env=_pg_env(home, pg_bin), capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL)


def _bin(pg_bin: str, name: str) -> str:
    p = Path(pg_bin) / name
    if not (p.is_file() and os.access(p, os.X_OK)):
        raise LifecycleError(f"PostgreSQL binary {p} not found or not executable")
    return str(p)


_CONF_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*=?\s*(.*)$")        # postgresql.conf: `name = value` or `name value`
_CONF_INCLUDES = ("include", "include_if_exists", "include_dir")


def _conf_value(raw: str) -> str:
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        end = raw.find(raw[0], 1)
        return raw[1:end] if end > 0 else raw[1:]
    return re.split(r"[\s#]", raw, maxsplit=1)[0]


def check_loopback_config(data_dir: Path) -> None:
    """Refuse to start a cluster whose config could listen on, or trust, any address but 127.0.0.1: every active
    `listen_addresses` (any case, `=` optional) must be exactly 127.0.0.1; `include*` and `hba_file` lines are refused (they
    could re-open it elsewhere); every active pg_hba `host*` rule (any case) must be 127.0.0.1/32."""
    lines: list[str] = []
    for name, required in (("postgresql.conf", True), ("postgresql.auto.conf", False)):
        f = data_dir / name
        try:
            lines += f.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            if required or f.exists():
                raise LifecycleError(f"cannot read {f}: {exc}") from exc
    for ln in lines:
        m = _CONF_LINE.match(ln)
        if not m or ln.lstrip().startswith("#"):
            continue
        key = m.group(1).lower()
        if key in _CONF_INCLUDES or key == "hba_file":
            raise LifecycleError(f"active config line {ln.strip()!r}: refusing (it could re-open listen_addresses or pg_hba elsewhere)")
        if key == "listen_addresses" and _conf_value(m.group(2)) != LOOPBACK:
            raise LifecycleError(f"listen_addresses is {_conf_value(m.group(2))!r}, not exactly '{LOOPBACK}': refusing")
    hba = data_dir / "pg_hba.conf"
    try:
        hba_lines = hba.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise LifecycleError(f"cannot read {hba}: {exc}") from exc
    for ln in hba_lines:
        s = ln.split("#", 1)[0].split()
        if not s:
            continue
        kind = s[0]                                              # pg_hba type keywords are lower-case; anything else is refused
        if kind == "local":
            continue
        if kind.startswith("host"):
            addr = s[3] if len(s) > 3 else ""
            if addr != f"{LOOPBACK}/32":
                raise LifecycleError(f"pg_hba.conf rule {ln.strip()!r} reaches an address other than {LOOPBACK}/32: refusing")
        else:
            raise LifecycleError(f"pg_hba.conf rule {ln.strip()!r} is not a local/host rule: refusing")


def _port_free(port: int) -> bool:
    with socket.socket() as s:
        try:
            s.bind((LOOPBACK, port))
        except OSError:
            return False
    return True


def status_cluster(root: str | Path) -> dict:
    """{'state': 'not_initialised'|'stopped'|'running'|'foreign'|'unknown', ...}. 'running' only when the pid file names a live
    postmaster whose command line carries THIS data dir; a live pid that is not that postmaster is 'foreign', and a `ps`
    that cannot answer is 'unknown' (never read as stopped)."""
    lay = _Layout(root)
    marker = read_marker(root)
    out: dict = {"root": str(lay.root), "marker": marker is not None, "port": (marker or {}).get("port")}
    if not (lay.data / "PG_VERSION").is_file():
        out["state"] = "not_initialised"
        return out
    try:
        pid = int((lay.data / "postmaster.pid").read_text(encoding="utf-8").splitlines()[0].strip())
    except (OSError, IndexError, ValueError):
        out["state"] = "stopped"
        return out
    if not 1 < pid < 2**31:
        out["state"] = "foreign"
        return out
    cmd = _proc_command(pid)
    out["pid"] = pid
    if cmd is None:
        out["state"] = "unknown"
    elif cmd == "":
        out["state"] = "stopped"
    elif _is_postmaster_for(cmd, lay.data):
        out["state"] = "running"
    else:
        out["state"] = "foreign"
    return out


def _check_port(port: Any) -> None:
    if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535 or port in FORBIDDEN_PORTS:
        raise LifecycleError(f"port {port!r} is not allowed")


def init_cluster(root: str | Path, *, port: int = DEFAULT_PORT, pg_bin: str = DEFAULT_PG_BIN) -> dict:
    """initdb a long-lived rehearsal data dir (idempotent). Writes the marker FIRST so a half-finished init is still ours."""
    lay = _Layout(root)
    _check_port(port)
    if len(str(lay.sock / ".s.PGSQL.00000")) > SOCK_PATH_LIMIT:
        raise LifecycleError("root path too long for a unix socket")
    _check_root(lay.root, create=True)
    with _locked(lay):
        marker = read_marker(root)
        if marker is None:
            if lay.marker.exists() or lay.marker.is_symlink():
                raise LifecycleError("an invalid marker is present: refusing to touch it")
            if lay.data.exists() and any(lay.data.iterdir()):
                raise LifecycleError(f"{lay.data} exists, is not empty and has no ownership marker: use `adopt` or remove it")
            marker = _write_marker(lay, port)
        elif marker["port"] != port:
            raise LifecycleError(f"marker says port {marker['port']}, not {port}")
        if (lay.data / "PG_VERSION").is_file():
            return {"action": "init", "result": "already_initialised", "marker": marker}
        lay.sock.mkdir(mode=0o700, exist_ok=True)
        os.chmod(lay.sock, 0o700)
        initdb = _bin(pg_bin, "initdb")
        r = _run_pg([initdb, "-D", str(lay.data), "-U", _user(), "-A", "trust", "--encoding=UTF8"], pg_bin)
        if r.returncode != 0:
            raise LifecycleError(f"initdb failed: {(r.stderr or r.stdout).strip()[-300:]}")
        with open(lay.data / "postgresql.conf", "a", encoding="utf-8") as f:
            f.write(f"\n# --- rehearsal overrides (E5.6, suvarna_rehearsal.py) ---\nlisten_addresses = '{LOOPBACK}'\n"
                    f"port = {port}\nunix_socket_directories = '{lay.sock}'\nunix_socket_permissions = 0700\n"
                    "unix_socket_group = ''\nmax_connections = 40\nfsync = off\nsynchronous_commit = off\nfull_page_writes = off\n")
        (lay.data / "pg_hba.conf").write_text(f"local   all   all                 trust\nhost    all   all   {LOOPBACK}/32  trust\n",
                                              encoding="utf-8")
        check_loopback_config(lay.data)
        return {"action": "init", "result": "initialised", "marker": marker}


def _user() -> str:
    import pwd  # noqa: PLC0415
    return pwd.getpwuid(os.getuid()).pw_name


def start_cluster(root: str | Path, *, pg_bin: str = DEFAULT_PG_BIN) -> dict:
    lay = _Layout(root)
    _check_root(lay.root, create=False)
    marker = read_marker(root)
    if marker is None:
        raise LifecycleError("no valid ownership marker: refusing to start a cluster this harness does not own")
    with _locked(lay):
        if not (lay.data / "PG_VERSION").is_file():
            raise LifecycleError("not initialised; run `cluster init`")
        if lay.data.is_symlink() or os.path.realpath(lay.data) != str(lay.data):
            raise LifecycleError("data dir is a symlink or resolves elsewhere")
        check_loopback_config(lay.data)
        st = status_cluster(root)
        if st["state"] == "running":
            return {"action": "start", "result": "already_running", **st}
        if st["state"] in ("foreign", "unknown"):
            raise LifecycleError(f"postmaster.pid is {st['state']}: refusing to start over it (inspect, then remove by hand)")
        if not _port_free(marker["port"]):
            raise LifecycleError(f"{LOOPBACK}:{marker['port']} is in use by another process")
        opts = (f"-c listen_addresses={LOOPBACK} -p {marker['port']} -c unix_socket_directories={lay.sock} "
                "-c unix_socket_permissions=0700")
        r = _run_pg([_bin(pg_bin, "pg_ctl"), "-D", str(lay.data), "-l", str(lay.log), "-o", opts, "-w", "-t", "60", "start"], pg_bin)
        if r.returncode != 0:
            raise LifecycleError(f"pg_ctl start failed: {(r.stderr or r.stdout).strip()[-300:]}")
        return {"action": "start", "result": "started", **status_cluster(root)}


def stop_cluster(root: str | Path, *, pg_bin: str = DEFAULT_PG_BIN) -> dict:
    lay = _Layout(root)
    _check_root(lay.root, create=False)
    if read_marker(root) is None:
        raise LifecycleError("no valid ownership marker: refusing to stop a cluster this harness does not own")
    with _locked(lay):
        st = status_cluster(root)
        if st["state"] in ("not_initialised", "stopped"):
            return {"action": "stop", "result": "not_running", **st}
        if st["state"] != "running":
            raise LifecycleError(f"postmaster.pid is {st['state']}: refusing to signal it")
        r = _run_pg([_bin(pg_bin, "pg_ctl"), "-D", str(lay.data), "-m", "fast", "-w", "-t", "60", "stop"], pg_bin)
        if r.returncode != 0:
            raise LifecycleError(f"pg_ctl stop failed: {(r.stderr or r.stdout).strip()[-300:]}")
        return {"action": "stop", "result": "stopped", **status_cluster(root)}


def reap_cluster(root: str | Path, *, pg_bin: str = DEFAULT_PG_BIN, remove_data: bool = False, confirm: str | None = None) -> dict:
    """Stop the cluster (when it runs) and, ONLY with `remove_data=True` and `confirm == str(root)`, delete its data dir and
    socket dir. Needs a valid marker; never follows a symlink; never removes the root, the marker or the lockfile."""
    lay = _Layout(root)
    _check_root(lay.root, create=False)
    if read_marker(root) is None:
        raise LifecycleError("no valid ownership marker: refusing to reap")
    if remove_data and confirm != str(lay.root):
        raise LifecycleError("--remove-data needs --confirm <the exact root path>")
    if remove_data and str(lay.root) != DEFAULT_ROOT:
        raise LifecycleError(f"--remove-data only ever deletes under the rehearsal root {DEFAULT_ROOT}")
    if remove_data and not (lay.data / "PG_VERSION").is_file():
        raise LifecycleError("--remove-data needs an initialised data dir (PG_VERSION): refusing to delete anything else")
    stopped = stop_cluster(root, pg_bin=pg_bin)
    removed: list[str] = []
    if remove_data:
        with _locked(lay):
            if status_cluster(root)["state"] not in ("not_initialised", "stopped"):
                raise LifecycleError("the cluster is still alive: refusing to delete its data dir")
            for d in (lay.data, lay.sock):
                if d.is_symlink():
                    raise LifecycleError(f"{d} is a symlink: refusing")
                if d.exists():
                    if os.path.realpath(d) != str(d) or d.parent != lay.root:
                        raise LifecycleError(f"{d} does not resolve to itself under the root: refusing")
                    shutil.rmtree(d)
                    removed.append(str(d))
    return {"action": "reap", "stopped": stopped["result"], "removed": removed}


def adopt_cluster(root: str | Path, *, port: int = DEFAULT_PORT) -> dict:
    """Put a marker on an EXISTING phase-1 cluster (`rehearsal_cluster.sh init`) after checking its config is loopback-only.
    Never changes the data dir."""
    lay = _Layout(root)
    _check_port(port)                                              # BEFORE anything is written: no poison marker
    _check_root(lay.root, create=False)
    with _locked(lay):
        if read_marker(root) is not None:
            return {"action": "adopt", "result": "already_marked"}
        if lay.marker.exists() or lay.marker.is_symlink():
            raise LifecycleError("an invalid marker is present: refusing to touch it")
        if not (lay.data / "PG_VERSION").is_file() or lay.data.is_symlink():
            raise LifecycleError("no initialised, non-symlink data dir to adopt")
        check_loopback_config(lay.data)
        conf = (lay.data / "postgresql.conf").read_text(encoding="utf-8")
        if not re.search(rf"^port\s*=\s*{port}\b", conf, re.M):
            raise LifecycleError(f"postgresql.conf does not set port = {port}")
        return {"action": "adopt", "result": "marked", "marker": _write_marker(lay, port)}


# ═════════════════════════ C. evidence: closed schema, derived results ═════════════════════════

# case id -> (title, required for the E5.6 acceptance, detector name, claim)
CASE_CATALOG: dict[str, dict] = {
    "find_fix_rebuild_certify": {
        "title": "one level: find -> fix -> rebuild -> certify with E5.1-E5.5", "required": True,
        "detector": "stale_after_fix_then_current_after_certify",
        "claim": "after the fix E5.5 marks the certificate stale, the orchestrator rebuild changes the semantic fingerprint, "
                 "a new E5.1 certificate is current, and the orchestrator ran at the evidence commit"},
    "f3_proof": {
        "title": "F3.PROOF: MSR writer delete/reinsert with referencing rows in all seven tables",
        "required": True, "detector": "no_refusal_dangling_recorded_and_restored",
        "claim": "no refusal with referencing rows present in all seven tables, a dangling count recorded and non-vacuous, "
                 "and the downstream rebuild in wave order restores it to zero"},
    "family_dispatch_refused": {
        "title": "a family-intersecting dispatch is refused", "required": True,
        "detector": "run_cli_refusal_with_no_db_contact",
        "claim": "suvarna_level_wave.run_cli refuses an asset set that intersects the family set with exit 4, before any "
                 "database contact or dispatch, and a non-family control carries no family refusal"},
    "hold_refuses_dispatch": {
        "title": "a hold refuses dispatch", "required": True, "detector": "hold_guard_blocks_dispatch_command",
        "claim": "with the hold file present the dispatch command is blocked, without it the same command is allowed, "
                 "and a non-dispatch command is not blocked"},
    "canary_triggers_reversal": {
        "title": "the canary triggers the reversal", "required": True, "detector": "canary_failure_reverses_to_pre_state",
        "claim": "an injected difference fails the canary, the reversal runs, and the post-reversal semantic fingerprint "
                 "equals the pre-operation one"},
    "idempotent_rebuild_fingerprint_unchanged": {
        "title": "an idempotent rebuild leaves the semantic fingerprint unchanged", "required": True,
        "detector": "fingerprint_equal_after_rebuild_and_differs_after_material_change",
        "claim": "a delete-then-insert rebuild that changes only volatile columns leaves the E5.5 fingerprint unchanged, "
                 "another chart's fingerprint unchanged, and a material change moves it"},
    "no_production_write": {
        "title": "no production write: every connection was loopback and allowed", "required": True,
        "detector": "connection_log_all_loopback_allowed",
        "claim": "every connection the harness opened was to 127.0.0.1 on an allowed port, at least one was opened, and a "
                 "non-loopback probe was refused without opening a socket"},
}
REQUIRED_CASES = tuple(k for k, v in CASE_CATALOG.items() if v["required"])
CASE_KEYS = ("id", "title", "result", "basis", "detector", "measured", "fingerprints", "evidence", "unmeasured_reason")
BASES = ("rehearsal_db", "synthetic_fixture")
RESULTS = ("PASS", "FAIL", "UNMEASURED")
_NEEDS = re.compile(r"NEEDS_[A-Z0-9_]{3,60}")


def _h64(v: Any) -> bool:
    return isinstance(v, str) and bool(HEX64.fullmatch(v))


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _keys(m: Any, want: Sequence[str]) -> list[str]:
    if not isinstance(m, Mapping):
        return ["measured is not an object"]
    probs = [f"missing measured key {k!r}" for k in want if k not in m]
    probs += [f"unexpected measured key {k!r}" for k in m if k not in want]
    return probs


def _judge_idempotent(m: Mapping) -> list[str]:
    want = ("fingerprint_before", "fingerprint_after_rebuild", "fingerprint_after_material_change", "other_chart_before",
            "other_chart_after", "rows_before", "rows_after", "volatile_columns_changed")
    p = _keys(m, want)
    if p:
        return p
    p = [f"{k} is not a sha256" for k in want[:5] if not _h64(m[k])]
    if not (_is_int(m["rows_before"]) and _is_int(m["rows_after"]) and m["rows_before"] > 0 and m["rows_after"] == m["rows_before"]):
        p.append("row counts must be equal and positive")
    if m["volatile_columns_changed"] is not True:
        p.append("the rebuild did not change a volatile column: an unchanged table proves nothing")
    if m["fingerprint_before"] != m["fingerprint_after_rebuild"]:
        p.append("the fingerprint moved on an idempotent rebuild")
    if m["fingerprint_after_material_change"] == m["fingerprint_before"]:
        p.append("a material change did not move the fingerprint: the detector is blind")
    if m["other_chart_before"] != m["other_chart_after"]:
        p.append("another chart's fingerprint moved: the rebuild leaked outside its scope")
    return p


def _judge_family(m: Mapping) -> list[str]:
    want = ("intersecting_assets", "refused_assets", "refused_via", "exit_code", "refusal_codes", "connect_calls", "dispatch_calls",
            "control_exit_code", "control_refusal_codes", "control_connect_calls", "missing_file_committing_codes")
    p = _keys(m, want)
    if p:
        return p
    lists_ok = all(isinstance(m[k], list) for k in ("intersecting_assets", "refused_assets", "refused_via", "refusal_codes",
                                                    "control_refusal_codes", "missing_file_committing_codes"))
    if not lists_ok:
        return p + ["a list-valued measurement is not a list"]
    if not m["intersecting_assets"]:
        p.append("no family-intersecting asset was requested")
    if not set(m["intersecting_assets"]) <= set(m["refused_assets"]):
        p.append("a family-intersecting asset was not refused")
    if not {"name_pattern", "family_set"} <= set(m["refused_via"]):
        p.append("both refusal paths (name pattern and family_set) must be exercised and refused")
    if not (_is_int(m["exit_code"]) and m["exit_code"] == 4):
        p.append("the refusal exit code is not 4")
    if "FAMILY_ASSET" not in m["refusal_codes"]:
        p.append("no FAMILY_ASSET refusal")
    if not (_is_int(m["connect_calls"]) and _is_int(m["dispatch_calls"]) and m["connect_calls"] == 0 and m["dispatch_calls"] == 0):
        p.append("the refused request touched the database or dispatched")
    if any(str(c).startswith(("FAMILY_", "SPLITS_")) for c in m["control_refusal_codes"]):
        p.append("the non-family control was refused as a family request: the detector cannot tell")
    if not _is_int(m["control_connect_calls"]):
        p.append("control_connect_calls missing")
    if "FAMILY_FILE_MISSING" not in m["missing_file_committing_codes"]:
        p.append("a committing run with no family file was not refused (fail-open)")
    return p


def _judge_hold(m: Mapping) -> list[str]:
    want = ("hold_guard_sha256", "command", "blocked_with_hold", "blocked_without_hold", "reason_with_hold",
            "non_dispatch_blocked_with_hold")
    p = _keys(m, want)
    if p:
        return p
    if not _h64(m["hold_guard_sha256"]):
        p.append("hold_guard_sha256 is not a sha256")
    if "suvarna_level_wave" not in str(m["command"]):
        p.append("the command tested is not a level-wave dispatch")
    if m["blocked_with_hold"] is not True:
        p.append("the dispatch was not blocked with the hold present")
    if m["blocked_without_hold"] is not False:
        p.append("the dispatch was blocked without a hold: the guard cannot tell hold from no hold")
    if m["non_dispatch_blocked_with_hold"] is not False:
        p.append("a non-dispatch command was blocked: the guard over-refuses")
    return p


def _judge_canary(m: Mapping) -> list[str]:
    want = ("baseline_canary_passed", "injected_difference_failed_canary", "reversal_triggered", "fingerprint_pre",
            "fingerprint_post_reversal")
    p = _keys(m, want)
    if p:
        return p
    if m["baseline_canary_passed"] is not True:
        p.append("the baseline canary did not pass")
    if m["injected_difference_failed_canary"] is not True:
        p.append("an injected difference did not fail the canary")
    if m["reversal_triggered"] is not True:
        p.append("the failed canary did not trigger the reversal")
    if not (_h64(m["fingerprint_pre"]) and m["fingerprint_pre"] == m["fingerprint_post_reversal"]):
        p.append("the post-reversal fingerprint is not the pre-operation one")
    return p


def _judge_f3(m: Mapping) -> list[str]:
    want = ("referencing_tables_populated", "msr_replace_refused", "dangling_after_change", "dangling_tool",
            "dangling_after_downstream_rebuild", "referencing_rows_restored", "downstream_waves", "fk_state")
    p = _keys(m, want)
    if p:
        return p
    t = m["referencing_tables_populated"]
    if not (isinstance(t, Mapping) and len(t) == 7 and all(_is_int(v) and v > 0 for v in t.values())):
        p.append("referencing rows are not present (> 0) in all seven tables")
    if m["msr_replace_refused"] is not False:
        p.append("the MSR delete/reinsert was refused")
    if not (_is_int(m["dangling_after_change"]) and m["dangling_after_change"] > 0):
        p.append("no dangling reference was recorded after a changed signal: the check is vacuous")
    if not (_is_int(m["dangling_after_downstream_rebuild"]) and m["dangling_after_downstream_rebuild"] == 0):
        p.append("the downstream rebuild did not restore referential integrity")
    restored = m["referencing_rows_restored"]
    if not (isinstance(restored, Mapping) and set(restored) == set(t if isinstance(t, Mapping) else {}) and len(restored) == 7
            and all(v is True for v in restored.values())):
        p.append("the referencing rows of all seven tables were not restored by the downstream rebuild (cascaded rows included)")
    if not (isinstance(m["downstream_waves"], list) and m["downstream_waves"]):
        p.append("no downstream waves recorded")
    if not isinstance(m["fk_state"], Mapping):
        p.append("the observed foreign-key state (pg_constraint) is not recorded")
    if not (isinstance(m["dangling_tool"], str) and m["dangling_tool"]):
        p.append("dangling_tool missing")
    return p


def _judge_certify(m: Mapping) -> list[str]:
    want = ("finding_id", "census_run_id", "stale_after_fix_detected", "fingerprint_before", "fingerprint_after_rebuild",
            "certificate_current_after_certify", "certificate_detector_not_none", "orchestrator_commit", "evidence_commit")
    p = _keys(m, want)
    if p:
        return p
    if not (isinstance(m["finding_id"], str) and m["finding_id"] and isinstance(m["census_run_id"], str) and m["census_run_id"]):
        p.append("finding_id / census_run_id missing")
    if m["stale_after_fix_detected"] is not True:
        p.append("E5.5 did not mark the old certificate stale after the fix")
    if not (_h64(m["fingerprint_before"]) and _h64(m["fingerprint_after_rebuild"])
            and m["fingerprint_before"] != m["fingerprint_after_rebuild"]):
        p.append("the rebuild did not change the semantic fingerprint")
    if m["certificate_current_after_certify"] is not True or m["certificate_detector_not_none"] is not True:
        p.append("no current certificate backed by a real detector after the rebuild")
    if not (isinstance(m["orchestrator_commit"], str) and HEX40.fullmatch(m["orchestrator_commit"])
            and m["orchestrator_commit"] == m["evidence_commit"]):
        p.append("the orchestrator did not run at the evidence commit")
    return p


def _entry_problem(e: Any) -> str | None:
    """One opened connection: loopback, allowed port, VERIFIED, and consistent with its policy (a rehearsal entry is the
    rehearsal port/database/data dir, a disposable one a suvarna_disposable* database on another port)."""
    keys = ("host", "port", "database", "policy", "data_directory", "verified")
    if not (isinstance(e, Mapping) and set(e) == set(keys)):
        return f"an opened connection does not have exactly the keys {keys}"
    if e["host"] != LOOPBACK or not _is_int(e["port"]) or e["port"] in FORBIDDEN_PORTS or e["policy"] not in POLICIES:
        return f"an opened connection is not loopback/allowed: {dict(e)!r}"
    if e["verified"] is not True or not (isinstance(e["data_directory"], str) and e["data_directory"]):
        return "an opened connection was not verified against the answering server"
    if not isinstance(e["database"], str):
        return "database is not text"
    if e["policy"] == "rehearsal":
        if e["port"] != DEFAULT_PORT or not rg.DB_NAME_RE.fullmatch(e["database"]) or not _same_path(e["data_directory"], f"{DEFAULT_ROOT}/pg"):
            return "a rehearsal-policy entry is not the rehearsal port/database/data directory"
    elif e["port"] == DEFAULT_PORT or not e["database"].startswith("suvarna_disposable"):
        return "a disposable-policy entry is not a suvarna_disposable* database on a non-rehearsal port"
    return None


def _judge_connections(m: Mapping) -> list[str]:
    want = ("opened", "refused_count", "probe_refused_without_socket")
    p = _keys(m, want)
    if p:
        return p
    opened = m["opened"]
    if not (isinstance(opened, list) and opened):
        return p + ["no connection was recorded: the log proves nothing"]
    p += [x for x in (_entry_problem(e) for e in opened) if x]
    if not _is_int(m["refused_count"]):
        p.append("refused_count is not an integer")
    if m["probe_refused_without_socket"] is not True:
        p.append("a non-loopback probe was not refused without opening a socket")
    return p


JUDGES: dict[str, Callable[[Mapping], list[str]]] = {
    "find_fix_rebuild_certify": _judge_certify, "f3_proof": _judge_f3, "family_dispatch_refused": _judge_family,
    "hold_refuses_dispatch": _judge_hold, "canary_triggers_reversal": _judge_canary,
    "idempotent_rebuild_fingerprint_unchanged": _judge_idempotent, "no_production_write": _judge_connections,
}
assert set(JUDGES) == set(CASE_CATALOG)


def judge_case(case_id: str, measured: Mapping) -> tuple[str, list[str]]:
    """The ONE place a measured case becomes PASS or FAIL: a pure function of the recorded raw values."""
    if case_id not in JUDGES:
        raise RehearsalError(f"unknown case {case_id!r}")
    problems = JUDGES[case_id](measured)
    return ("FAIL" if problems else "PASS"), problems


def case_result(case_id: str, *, measured: Mapping, basis: str, fingerprints: Mapping | None = None,
                evidence: Sequence[Mapping] | None = None) -> dict:
    """A measured case record; its `result` is derived by `judge_case`, never chosen by the caller."""
    spec = CASE_CATALOG[case_id]
    result, _ = judge_case(case_id, measured)
    case = {"id": case_id, "title": spec["title"], "result": result, "basis": basis,
            "detector": {"name": spec["detector"], "claim": spec["claim"]}, "measured": dict(measured),
            "fingerprints": dict(fingerprints or {}), "evidence": [dict(e) for e in (evidence or [])],
            "unmeasured_reason": None}
    if basis == "rehearsal_db":                       # the measurement itself is an evidence file, pinned by its sha256
        case["evidence"].insert(0, measured_record_pointer(case))
    return case


def measured_record_text(case: Mapping) -> str:
    """The canonical text of a case's measurement record. Its sha256 is the case's first evidence pointer, so the pointer
    can only be satisfied by a file that CONTAINS the measured values the judge was run on."""
    return json.dumps({"case": case["id"], "measured": case["measured"], "fingerprints": case["fingerprints"]},
                      sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def measured_record_path(case_id: str) -> str:
    return f"E5.6/{case_id}.measured.json"


def measured_record_pointer(case: Mapping) -> dict:
    return {"path": measured_record_path(case["id"]), "sha256": sha256_text(measured_record_text(case))}


def write_measured_records(doc: Mapping, evidence_root: str | Path) -> list[str]:
    """Write each measured case's record file under `evidence_root` (the files the first pointer names)."""
    out = []
    for c in doc["cases"]:
        if c["result"] == "UNMEASURED":
            continue
        f = Path(evidence_root) / measured_record_path(c["id"])
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(measured_record_text(c), encoding="utf-8")
        out.append(str(f))
    return out


def unmeasured_case(case_id: str, reason: str) -> dict:
    """A case that was not measured: UNMEASURED with a NEEDS_* reason and nothing else; never PASS."""
    if not _NEEDS.fullmatch(reason):
        raise RehearsalError(f"an unmeasured reason must be NEEDS_<WHAT> (got {reason!r})")
    spec = CASE_CATALOG[case_id]
    return {"id": case_id, "title": spec["title"], "result": "UNMEASURED", "basis": None,
            "detector": {"name": spec["detector"], "claim": spec["claim"]}, "measured": {}, "fingerprints": {},
            "evidence": [], "unmeasured_reason": reason}


def derive_summary(cases: Sequence[Mapping]) -> dict:
    by = {c["id"]: c for c in cases if isinstance(c, Mapping) and isinstance(c.get("id"), str)}
    res = [by.get(i, {}).get("result", "UNMEASURED") for i in REQUIRED_CASES]
    return {"required": len(REQUIRED_CASES), "pass": res.count("PASS"), "fail": res.count("FAIL"),
            "unmeasured": res.count("UNMEASURED")}


def derive_result(mode: str, summary: Mapping) -> str:
    """FAIL if any required case failed; PASS only in `rehearsal` mode with every required case PASS; otherwise UNMEASURED.
    A `self_test` document can therefore never read PASS."""
    if summary["fail"]:
        return "FAIL"
    if mode == "rehearsal" and summary["pass"] == summary["required"]:
        return "PASS"
    return "UNMEASURED"


def build_evidence(*, mode: str, commit: str | None, cases: Sequence[Mapping], environment: Mapping,
                   orchestrator_commit: str | None = None, job_image_commit: str | None = None) -> dict:
    ordered = sorted(cases, key=lambda c: list(CASE_CATALOG).index(c["id"]))
    summary = derive_summary(ordered)
    return {"schema": EVIDENCE_SCHEMA, "item": "E5.6", "mode": mode, "result": derive_result(mode, summary),
            "commit": commit, "orchestrator_commit": orchestrator_commit, "job_image_commit": job_image_commit,
            "generated_by": {"tool": TOOL_NAME, "tool_sha256": tool_sha256()}, "environment": dict(environment),
            "required_cases": list(REQUIRED_CASES), "cases": ordered, "summary": summary}


TOP_KEYS = ("schema", "item", "mode", "result", "commit", "orchestrator_commit", "job_image_commit", "generated_by",
            "environment", "required_cases", "cases", "summary")
ENV_KEYS = ("cluster", "schema_replay", "seed")
CLUSTER_KEYS = ("kind", "host", "port", "data_directory", "pg_version")


def _validate_case(c: Any, mode: str) -> list[str]:
    if not isinstance(c, Mapping):
        return ["a case is not an object"]
    cid = c.get("id")
    if not isinstance(cid, str) or cid not in CASE_CATALOG:
        return [f"unknown case id {cid!r}"]
    p = [f"{cid}: key set differs from the closed case schema"] if set(c) != set(CASE_KEYS) else []
    if p:
        return p
    spec = CASE_CATALOG[cid]
    if c["title"] != spec["title"] or c["detector"] != {"name": spec["detector"], "claim": spec["claim"]}:
        p.append(f"{cid}: title/detector differ from the catalog (a case cannot redefine its own detector)")
    if c["result"] not in RESULTS:
        return p + [f"{cid}: result {c['result']!r} is not PASS/FAIL/UNMEASURED"]
    if c["result"] == "UNMEASURED":
        if not (isinstance(c["unmeasured_reason"], str) and _NEEDS.fullmatch(c["unmeasured_reason"])):
            p.append(f"{cid}: UNMEASURED needs a NEEDS_* reason")
        if c["measured"] or c["fingerprints"] or c["evidence"] or c["basis"] is not None:
            p.append(f"{cid}: UNMEASURED must carry no measurement, evidence or basis")
        return p
    if c["unmeasured_reason"] is not None:
        p.append(f"{cid}: a measured case has an unmeasured_reason")
    if c["basis"] not in BASES:
        p.append(f"{cid}: basis {c['basis']!r} is not one of {BASES}")
    if not isinstance(c["measured"], Mapping) or not c["measured"]:
        return p + [f"{cid}: a measured case needs a non-empty `measured` object"]
    derived, why = judge_case(cid, c["measured"])
    if derived != c["result"]:
        p.append(f"{cid}: recorded result {c['result']} but the recorded measurements judge {derived}"
                 + (f" ({why[0]})" if why else ""))
    if not isinstance(c["fingerprints"], Mapping) or not all(_h64(v) for v in c["fingerprints"].values()):
        p.append(f"{cid}: fingerprints must be an object of sha256 values")
    ev = c["evidence"]
    if not isinstance(ev, list) or not all(isinstance(e, Mapping) and set(e) == {"path", "sha256"} and _check_relpath(e["path"])
                                           and _h64(e["sha256"]) for e in ev):
        p.append(f"{cid}: evidence must be a list of {{path (relative), sha256}}")
    if mode == "self_test" and c["basis"] == "rehearsal_db":
        p.append(f"{cid}: a self_test document cannot claim a rehearsal_db basis")
    if mode == "rehearsal" and c["result"] == "PASS":
        if c["basis"] != "rehearsal_db":
            p.append(f"{cid}: a rehearsal PASS needs basis rehearsal_db (a synthetic fixture is not the rehearsal)")
    if mode == "rehearsal" and isinstance(ev, list) and isinstance(c["fingerprints"], Mapping):
        want = measured_record_pointer(c)
        if want not in ev:
            p.append(f"{cid}: the measurement-record pointer {want['path']} is missing or its sha256 is not the record of THESE "
                     "measured values")
    if cid == "no_production_write" and mode == "rehearsal":
        if any(isinstance(e, Mapping) and e.get("policy") != "rehearsal" for e in c["measured"].get("opened", [])):
            p.append(f"{cid}: a rehearsal document may only contain rehearsal-policy connections")
    return p


def _check_relpath(p: Any) -> bool:
    return (isinstance(p, str) and bool(p) and not p.startswith("/") and "\\" not in p
            and ".." not in p.split("/") and "" not in p.split("/"))


def tool_sha256_at_commit(repo: str | Path, commit: str) -> str | None:
    """sha256 of this tool as committed at `commit` (None when the repo/commit/path is not available)."""
    if not (isinstance(commit, str) and HEX40.fullmatch(commit)):
        return None
    try:
        r = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{TOOL_REL}"], capture_output=True, timeout=30, env=_git_env(),
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


def validate_evidence(doc: Any, tool_sha: str | None = None) -> list[str]:
    """Every problem found, [] when the document is valid. Never raises: a malformed document is a problem list.
    `tool_sha` is the sha256 the document's `generated_by.tool_sha256` must equal (default: this running tool file)."""
    try:
        return _validate_evidence(doc, tool_sha if tool_sha is not None else tool_sha256())
    except (KeyError, TypeError, AttributeError, ValueError, IndexError) as exc:
        return [f"malformed document ({type(exc).__name__}: {str(exc)[:120]})"]


def _validate_evidence(doc: Any, expected_tool_sha: str) -> list[str]:
    if not isinstance(doc, Mapping):
        return ["the document is not an object"]
    if set(doc) != set(TOP_KEYS):
        return [f"top-level keys differ from the closed schema: missing {sorted(set(TOP_KEYS) - set(doc))}, "
                f"extra {sorted(set(doc) - set(TOP_KEYS))}"]
    p: list[str] = []
    if doc["schema"] != EVIDENCE_SCHEMA or doc["item"] != "E5.6":
        p.append("schema/item mismatch")
    mode = doc["mode"]
    if mode not in ("rehearsal", "self_test"):
        return p + [f"mode {mode!r} is not rehearsal/self_test"]
    if doc["required_cases"] != list(REQUIRED_CASES):
        p.append("required_cases differ from the catalog")
    gb = doc["generated_by"]
    if not (isinstance(gb, Mapping) and set(gb) == {"tool", "tool_sha256"} and gb["tool"] == TOOL_NAME and _h64(gb["tool_sha256"])):
        p.append("generated_by is malformed")
    elif gb["tool_sha256"] != expected_tool_sha:
        p.append("generated_by.tool_sha256 is not the sha256 of the repo tool (the document was not produced by this tool version)")
    cases = doc["cases"]
    if not isinstance(cases, list):
        return p + ["cases is not a list"]
    ids = [c["id"] if isinstance(c, Mapping) and isinstance(c.get("id"), str) else None for c in cases]
    named = [i for i in ids if i is not None]
    if len(set(named)) != len(named):
        p.append("a case id occurs twice")
    missing = [i for i in REQUIRED_CASES if i not in ids]
    if missing:
        p.append(f"required case(s) absent (an absent case must be written as UNMEASURED): {missing}")
    for c in cases:
        p += _validate_case(c, mode)
        if (isinstance(c, Mapping) and c.get("id") == "find_fix_rebuild_certify" and c.get("result") == "PASS"
                and isinstance(c.get("measured"), Mapping) and c["measured"].get("evidence_commit") != doc["commit"]):
            p.append("find_fix_rebuild_certify.evidence_commit differs from the document commit")
    summary = derive_summary(cases)
    if doc["summary"] != summary:
        p.append(f"summary {doc['summary']!r} differs from the derived {summary!r}")
    want = derive_result(mode, summary)
    if doc["result"] != want:
        p.append(f"top-level result {doc['result']!r} differs from the derived {want!r}")
    env = doc["environment"]
    if not isinstance(env, Mapping) or set(env) != set(ENV_KEYS):
        p.append("environment keys differ from the closed schema")
    else:
        cl = env["cluster"]
        if not (isinstance(cl, Mapping) and set(cl) == set(CLUSTER_KEYS) and cl["host"] == LOOPBACK
                and _is_int(cl["port"]) and cl["port"] not in FORBIDDEN_PORTS and cl["kind"] in ("rehearsal", "disposable")):
            p.append("environment.cluster is malformed, not loopback, or on a forbidden port")
        elif mode == "rehearsal" and not (cl["kind"] == "rehearsal" and cl["port"] == DEFAULT_PORT
                                          and cl["data_directory"] == f"{DEFAULT_ROOT}/pg"):
            p.append("a rehearsal document must name the rehearsal cluster (port 55432, the rehearsal data dir)")
        elif mode == "self_test" and cl["kind"] != "disposable":
            p.append("a self_test document must name a disposable cluster")
    if mode == "rehearsal" and isinstance(env, Mapping):
        rep, seed = env.get("schema_replay"), env.get("seed")
        if not (isinstance(rep, Mapping) and set(rep) == {"files_applied", "files_failed", "report_sha256"}
                and _is_int(rep["files_applied"]) and _is_int(rep["files_failed"]) and _h64(rep["report_sha256"])):
            p.append("a rehearsal document needs environment.schema_replay {files_applied, files_failed, report_sha256}")
        if not (isinstance(seed, Mapping) and set(seed) == {"manifest_sha256", "tables"} and _h64(seed["manifest_sha256"])
                and isinstance(seed["tables"], list) and seed["tables"]):
            p.append("a rehearsal document needs environment.seed {manifest_sha256, tables}")
        for k in ("commit", "orchestrator_commit", "job_image_commit"):
            if not (isinstance(doc[k], str) and HEX40.fullmatch(doc[k])):
                p.append(f"a rehearsal document needs a 40-hex {k}")
        if doc["orchestrator_commit"] != doc["job_image_commit"]:
            p.append("orchestrator_commit must equal job_image_commit (the orchestrator runs from source at the job image's commit)")
        if doc["commit"] != doc["orchestrator_commit"]:
            p.append("commit must equal orchestrator_commit")
    elif mode == "self_test":
        for k in ("orchestrator_commit", "job_image_commit"):
            if doc[k] is not None:
                p.append(f"a self_test document has no {k}")
        if doc["commit"] is not None and not (isinstance(doc["commit"], str) and HEX40.fullmatch(doc["commit"])):
            p.append("commit must be 40-hex or null")
    return p


def check_pointers(doc: Mapping, evidence_root: str | Path) -> list[str]:
    """Every evidence pointer names an existing file under `evidence_root` whose sha256 matches; for each measured case the
    measurement-record file must also PARSE to exactly the case's measured values (no file merely hashing right)."""
    root = Path(evidence_root)
    p: list[str] = []
    for c in doc.get("cases", []):
        for e in c.get("evidence", []):
            f = root / e["path"]
            try:
                if f.is_symlink() or not f.is_file():
                    p.append(f"{c['id']}: evidence file {e['path']} is missing or a symlink")
                elif sha256_file(f) != e["sha256"]:
                    p.append(f"{c['id']}: evidence file {e['path']} does not match its recorded sha256")
                elif e["path"] == measured_record_path(c["id"]):
                    rec = json.loads(f.read_text(encoding="utf-8"))
                    if rec != {"case": c["id"], "measured": c["measured"], "fingerprints": c["fingerprints"]}:
                        p.append(f"{c['id']}: the measurement-record file does not contain this case's measured values")
            except (OSError, ValueError) as exc:
                p.append(f"{c['id']}: evidence file {e['path']} unreadable ({exc})")
    return p


def _is_detector_path(target: Path) -> bool:
    """True for any spelling of the detector's evidence file: realpath'd, case-insensitive, or just that file name."""
    real = os.path.realpath(target).replace(os.sep, "/").lower()
    return real.endswith("/" + DETECTOR_EVIDENCE_PATH.lower()) or os.path.basename(real) == "rehearsal.json"


def write_evidence(doc: Mapping, path: str | Path, *, evidence_root: str | Path | None = None) -> str:
    """Validate, then write atomically (canonical JSON, sorted keys, trailing newline). Refuses an invalid document, a
    `self_test` document at the detector's path (E5.6/REHEARSAL.json, any case or symlinked spelling), and (rehearsal
    mode) any pointer that does not verify."""
    problems = validate_evidence(doc)
    if problems:
        raise RehearsalError("refusing to write an invalid evidence document: " + "; ".join(problems[:5]))
    target = Path(path)
    if doc["mode"] == "self_test" and _is_detector_path(target):
        raise RehearsalError(f"a self_test document may never be written to the detector's path ({DETECTOR_EVIDENCE_PATH})")
    if doc["mode"] == "rehearsal":
        if evidence_root is None:
            raise RehearsalError("a rehearsal document needs --evidence-root so its pointers can be verified")
        pointer_problems = check_pointers(doc, evidence_root)
        if pointer_problems:
            raise RehearsalError("evidence pointers do not verify: " + "; ".join(pointer_problems[:5]))
    text = json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)
    return sha256_text(text)


# ═════════════════════════ E. E5.7: pre/post fingerprint comparison ═════════════════════════

FINGERPRINT_DEFINITION = "nikasha_stale_certs.table_fingerprint/1"     # E5.5's definition: the ONE fingerprint in this campaign
EXPLAIN_CODES_BY_KIND = {
    "fingerprint_differs": ("rolling_horizon", "embedding_equivalence_policy", "seeded_not_rebuilt", "production_ahead_of_commit",
                            "fixed_before_drill", "migration_owned_rows"),
    "missing_in_rehearsal": ("source_unavailable_offline", "not_run_declared"),
    "missing_in_production": ("asset_new_at_commit",),
}
EXPLAIN_CODES = tuple(sorted({c for v in EXPLAIN_CODES_BY_KIND.values() for c in v}))
MIN_DETAIL_CHARS = 40
DEFAULT_LIMITS = (0.0, 0.25)                   # (max_undecided_share, max_difference_share)
DRILL_KEYS = ("schema", "item", "result", "commit", "tool_sha256", "definition", "expected_assets", "production", "rehearsal",
              "explained_input", "inputs", "equal", "differences", "unexplained", "uncovered", "unexpected",
              "explanations_without_difference", "problems", "limits", "coverage", "rows", "empty_both_sides", "seeded", "not_run", "unmeasured", "runtime", "claimed_unverified", "projections", "known_differences", "horizons")
RESULTS_PASS = ("PASS", "PASS_DECLARED_ONLY")   # PASS only when every L0 asset is declared, full and deterministic; otherwise the scoped label
COVERAGE_KEYS = ("declarations_sha256", "units", "declared", "partial", "undeclared", "non_deterministic", "groups", "seeded", "partial_ownership", "not_run_allowed", "expected_differences", "scope")
NON_DETERMINISTIC_FLAGS = ("rolling_horizon", "platform_bound")
CODE_REQUIRES_FLAG = {"rolling_horizon": "rolling_horizon", "source_unavailable_offline": "platform_bound"}   # an explanation code only a flagged unit may carry
# Where the rebuild ran (decision B1: the L0 rebuild runs inside a linux/amd64 Debian container, so platform-bound assets are in the proof). A closed block
# of the rehearsal receipt (`rebuild.runtime`) and of the drill document. A run whose platform is not linux/amd64 leaves the platform-bound units
# CLAIMED_UNVERIFIED (never equal, never counted).
RUNTIME_KEYS = ("platform", "os", "postgres_version", "python_version", "swisseph_version", "collation")
RUNTIME_PLATFORM = "linux/amd64"
_RT_PLATFORM = re.compile(r"[a-z0-9_.-]+/[a-z0-9_.-]+")
_RT_PG = re.compile(r"[0-9]+(\.[0-9]+){0,2}")
_RT_PY = re.compile(r"[0-9]+\.[0-9]+(\.[0-9]+)?")
_RT_COLLATION = re.compile(r"[A-Za-z0-9_.@-]{1,100}")
NOT_RUN_CODE = "not_run_declared"      # decision N-121: a unit the rebuild legitimately did not run (closed list; the unit stays UNMEASURED, never equal)
PARTIAL_OWNERSHIP_CODE = "migration_owned_rows"                                   # the fixed code for a difference on a partly writer-owned table
PARTIAL_OWNERSHIP_DETAIL = ("the table holds rows owned by migrations, not by the writer, which a rebuild from source cannot reproduce: the whole table "
                            "is fingerprinted and this difference is expected (partial: writer-only rows are what the rebuild claim covers)")
_DECISION_ID = re.compile(r"N-[0-9]{1,6}")
_ASSET_ID = re.compile(r"[a-z][a-z0-9_]*")


def fingerprint_set(fingerprints: Mapping[str, str]) -> dict:
    """The envelope a comparison input must have: the definition marker + {asset: sha256}."""
    return {"definition": FINGERPRINT_DEFINITION, "fingerprints": dict(fingerprints)}


def _check_envelope(side: str, env: Any) -> dict:
    if not (isinstance(env, Mapping) and set(env) == {"definition", "fingerprints"}):
        raise RehearsalError(f"{side} must be {{definition, fingerprints}} (use fingerprint_set)")
    if env["definition"] != FINGERPRINT_DEFINITION:
        raise RehearsalError(f"{side} was not made with {FINGERPRINT_DEFINITION}: one fingerprint definition only")
    fp = env["fingerprints"]
    if not (isinstance(fp, Mapping) and all(isinstance(k, str) and _ASSET_ID.fullmatch(k) and _h64(v) for k, v in fp.items())):
        raise RehearsalError(f"{side}.fingerprints must be an object of asset id -> sha256")
    return dict(fp)


def _normal_detail(text: str) -> str:
    return " ".join(text.lower().split())


def _explanation_problem(kind: str, e: Any) -> str | None:
    if not (isinstance(e, Mapping) and {"reason_code", "detail"} <= set(e) <= {"reason_code", "detail", "decision"}):
        return "an explanation is exactly {reason_code, detail[, decision]}"
    if e["reason_code"] not in EXPLAIN_CODES_BY_KIND[kind]:
        return f"reason_code {e['reason_code']!r} is not valid for a {kind} difference (allowed: {EXPLAIN_CODES_BY_KIND[kind]})"
    d = e["detail"]
    if not (isinstance(d, str) and len(d.strip()) >= MIN_DETAIL_CHARS and not any(ord(ch) < 32 for ch in d)):
        return f"detail must be text of at least {MIN_DETAIL_CHARS} characters"
    if "decision" in e and not (isinstance(e["decision"], str) and _DECISION_ID.fullmatch(e["decision"])):
        return "decision must be an SS-recorded decision id N-<n>"
    return None


def _plain_text(v: Any, limit: int) -> bool:
    return isinstance(v, str) and 0 < len(v.strip()) <= limit and v == v.strip() and not any(ord(ch) < 32 for ch in v)


HORIZON_RULE = "N-135"                                    # SS decision: a rolling-horizon difference is expected ONLY when evidence shows the shared range row-for-row equal
HORIZON_BLOCK_KEYS = ("date_column", "min_date", "max_date", "rows", "overlap_cutoff", "overlap_rows", "overlap_sha256")


def _fd_module():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import fingerprint_declarations as fd  # noqa: PLC0415
    return fd


def horizon_block_problem(b: Any) -> str | None:
    """Why `b` is not a valid closed `horizon` block (or None): the keys, the types and every internal consistency rule (rows <-> min/max, the cutoff and the
    overlap). Never raises."""
    if not (isinstance(b, Mapping) and set(b) == set(HORIZON_BLOCK_KEYS)):
        return f"a horizon block is exactly {HORIZON_BLOCK_KEYS}"
    ok = _fd_module().horizon_iso_ok
    if not (isinstance(b["date_column"], str) and _ASSET_ID.fullmatch(b["date_column"])):
        return "date_column must be a column identifier"
    mn, mx, cut = b["min_date"], b["max_date"], b["overlap_cutoff"]
    for k in ("rows", "overlap_rows"):
        if not (isinstance(b[k], int) and not isinstance(b[k], bool) and b[k] >= 0):
            return f"{k} must be an int >= 0"
    if not _h64(b["overlap_sha256"]):
        return "overlap_sha256 must be a sha256"
    if b["overlap_rows"] > b["rows"]:
        return "overlap_rows exceeds rows"
    if (mn is None) != (mx is None) or (b["rows"] == 0) != (mn is None):
        return "min_date and max_date are both null exactly when rows is 0"
    if mn is not None and not (ok(mn) and ok(mx) and len(mn) == len(mx) and mn <= mx):
        return "min_date and max_date must be horizon dates of one format with min_date <= max_date"
    if cut is not None and not (ok(cut) and (mn is None or len(cut) == len(mn))):
        return "overlap_cutoff must be null or a horizon date of the same format as min_date"
    if cut is None and b["overlap_rows"] != 0:
        return "a null overlap_cutoff has no overlap rows"
    if cut is not None and mn is not None:
        if cut < mn and b["overlap_rows"] != 0:
            return "overlap_cutoff precedes min_date but overlap_rows is not 0"
        if cut >= mx and b["overlap_rows"] != b["rows"]:
            return "overlap_cutoff is not before max_date, so every row is in the overlap"
        if cut >= mn and b["overlap_rows"] == 0:
            return "overlap_cutoff reaches min_date, so at least one row is in the overlap"
    return None


def check_horizons(horizons: Any, cov: Mapping) -> dict:
    """{unit: {table, production, rehearsal}} for units flagged rolling_horizon in the coverage; each side a valid horizon block or null (unit not read there)."""
    if horizons is None:
        return {}
    rolling = {u for u, f in cov["non_deterministic"].items() if "rolling_horizon" in f}
    if not (isinstance(horizons, Mapping) and all(
            k in rolling and isinstance(v, Mapping) and set(v) == {"table", "production", "rehearsal"} and isinstance(v["table"], str) and _ASSET_ID.fullmatch(v["table"])
            and all(v[x] is None or horizon_block_problem(v[x]) is None for x in ("production", "rehearsal")) for k, v in horizons.items())):
        raise RehearsalError("horizons must map a unit flagged rolling_horizon to {table, production, rehearsal} (a valid closed horizon block or null)")
    return {k: {"table": horizons[k]["table"], "production": copy.deepcopy(horizons[k]["production"]), "rehearsal": copy.deepcopy(horizons[k]["rehearsal"])}
            for k in sorted(horizons)}


def horizon_evidence(entry: Any) -> tuple[str | None, dict | None]:
    """N-135: (why the evidence does not hold, None) or (None, the evidence record). The rolling_horizon explanation is accepted ONLY when both blocks are
    present, the production overlap is its own max_date, the rehearsal was cut at the PRODUCTION max_date, the rehearsal was built later (max_date >=), and the
    shared range is row-for-row equal (same overlap rows and the same overlap fingerprint): so every extra row is after the production horizon."""
    if not entry:
        return "no horizon blocks were given for the unit", None
    p, r = entry["production"], entry["rehearsal"]
    if p is None:
        return "the production file carries no horizon block for the unit", None
    if r is None:
        return "the rehearsal file carries no horizon block for the unit", None
    if p["date_column"] != r["date_column"]:
        return f"the date columns differ ({p['date_column']} vs {r['date_column']})", None
    if p["rows"] == 0:
        return "production holds no rows: there is no shared range to compare", None
    if p["overlap_cutoff"] != p["max_date"]:
        return "the production overlap_cutoff is not its own max_date", None
    if r["overlap_cutoff"] != p["max_date"]:
        return (f"the rehearsal overlap_cutoff ({r['overlap_cutoff']}) is not the production max_date ({p['max_date']}): the rehearsal block must be computed with the "
                "production file's max_date as its cutoff"), None
    if r["max_date"] is None or r["max_date"] < p["max_date"]:
        return f"the rehearsal max_date ({r['max_date']}) is before the production max_date ({p['max_date']}): the rehearsal was not built later", None
    if r["overlap_rows"] != p["overlap_rows"]:
        return f"the overlap row counts differ (rehearsal {r['overlap_rows']} vs production {p['overlap_rows']}): the shared range is not row-for-row equal", None
    if r["overlap_sha256"] != p["overlap_sha256"]:
        return "the overlap fingerprints differ: the shared range is not row-for-row equal", None
    summary = (f"{HORIZON_RULE}: rows {r['rows']} vs {p['rows']} (rehearsal vs production), built-through dates {r['max_date']} vs {p['max_date']} (rehearsal vs "
               f"production), overlap equal over {p['overlap_rows']} rows (count and fingerprint, through {p['max_date']})")
    return None, {"rule": HORIZON_RULE, "rows_rehearsal": r["rows"], "rows_production": p["rows"], "max_date_rehearsal": r["max_date"], "max_date_production": p["max_date"],
                  "overlap_cutoff": p["max_date"], "overlap_rows": p["overlap_rows"], "overlap_sha256": p["overlap_sha256"], "summary": summary}


def check_projections(projections: Any, cov: Mapping) -> dict:
    """The projection fingerprints of the units that carry a recorded expected difference: {unit: {table, production, rehearsal}} with each side a sha256 or
    null (the unit was not read on that side). A projection is the table's fingerprint with the expected-difference columns IGNORED."""
    if projections is None:
        return {}
    units = {e["unit"]: e for e in cov["expected_differences"]}
    if not (isinstance(projections, Mapping) and all(
            k in units and isinstance(v, Mapping) and set(v) == {"table", "production", "rehearsal"} and v["table"] == units[k]["table"]
            and all(v[x] is None or _h64(v[x]) for x in ("production", "rehearsal")) for k, v in projections.items())):
        raise RehearsalError("projections must map a unit with a recorded expected_difference to {table (the recorded table), production, rehearsal} (sha256 or null)")
    return {k: dict(projections[k]) for k in sorted(projections)}


def runtime_problem(rt: Any) -> str | None:
    """Why `rt` is not a valid closed `runtime` block ({platform 'os/arch', os, postgres_version, python_version, swisseph_version (text or null),
    collation}), or None. Never raises."""
    if not (isinstance(rt, Mapping) and set(rt) == set(RUNTIME_KEYS)):
        return f"runtime must be an object with exactly the keys {RUNTIME_KEYS}"
    if not (isinstance(rt["platform"], str) and _RT_PLATFORM.fullmatch(rt["platform"])):
        return "runtime.platform must be '<os>/<arch>' in lower case (for example linux/amd64)"
    if not _plain_text(rt["os"], 200):
        return "runtime.os must be non-empty text"
    if not (isinstance(rt["postgres_version"], str) and _RT_PG.fullmatch(rt["postgres_version"])):
        return "runtime.postgres_version must be a version number such as 15.18"
    if not (isinstance(rt["python_version"], str) and _RT_PY.fullmatch(rt["python_version"])):
        return "runtime.python_version must be a version number such as 3.11.9"
    if not (rt["swisseph_version"] is None or _plain_text(rt["swisseph_version"], 60)):
        return "runtime.swisseph_version must be text, or null when it is not available"
    if not (isinstance(rt["collation"], str) and _RT_COLLATION.fullmatch(rt["collation"])):
        return "runtime.collation must be the database collation name (for example C or en_US.UTF-8)"
    return None


def check_runtime(rt: Any) -> dict:
    why = runtime_problem(rt)
    if why:
        raise RehearsalError(why)
    return {k: rt[k] for k in RUNTIME_KEYS}


def _unit_list(v: Any) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) and _ASSET_ID.fullmatch(x) for x in v) and len(set(v)) == len(v)


def check_coverage(coverage: Any, expected: Sequence[str]) -> dict:
    """The closed coverage block of an E5.7 drill (what the verdict covers and what it does not), checked against the expected units.
    Returns a normalised copy; raises RehearsalError. `scope` is DERIVED, never trusted: all_declared_full only when nothing is partial,
    undeclared or non-deterministic."""
    if not (isinstance(coverage, Mapping) and set(coverage) == set(COVERAGE_KEYS)):
        raise RehearsalError(f"coverage must be an object with exactly the keys {COVERAGE_KEYS}")
    c = copy.deepcopy(dict(coverage))
    if not (isinstance(c["declarations_sha256"], str) and _h64(c["declarations_sha256"]) or c["declarations_sha256"] is None):
        raise RehearsalError("coverage.declarations_sha256 must be a sha256 or null")
    if not (_unit_list(c["units"]) and _unit_list(c["declared"]) and c["units"] == sorted(expected)):
        raise RehearsalError("coverage.units must be exactly the sorted expected_assets (the comparison units)")
    if not (isinstance(c["partial"], Mapping) and all(isinstance(k, str) and _unit_list(v) and v for k, v in c["partial"].items())):
        raise RehearsalError("coverage.partial must map an asset to the non-empty list of tables it does not cover")
    if not (isinstance(c["undeclared"], Mapping) and all(isinstance(k, str) and isinstance(v, str) and v for k, v in c["undeclared"].items())):
        raise RehearsalError("coverage.undeclared must map an asset to its reason code")
    nd = c["non_deterministic"]
    if not (isinstance(nd, Mapping) and all(k in c["units"] and isinstance(v, list) and v and set(v) <= set(NON_DETERMINISTIC_FLAGS) and len(set(v)) == len(v)
                                          for k, v in nd.items())):
        raise RehearsalError(f"coverage.non_deterministic must map a unit to a non-empty list of flags from {NON_DETERMINISTIC_FLAGS}")
    if not (isinstance(c["groups"], Mapping) and all(k in c["units"] and _unit_list(v) and len(v) >= 2 for k, v in c["groups"].items())):
        raise RehearsalError("coverage.groups must map a unit to its (at least two) member assets")
    if not (_unit_list(c["seeded"]) and set(c["seeded"]) <= set(c["units"]) and c["seeded"] == sorted(c["seeded"])):
        raise RehearsalError("coverage.seeded must be a sorted list of units from coverage.units (units seeded from production, not rebuilt)")
    po = c["partial_ownership"]
    if not (isinstance(po, Mapping) and all(k in c["units"] and _unit_list(v) and v and v == sorted(v) for k, v in po.items())):
        raise RehearsalError("coverage.partial_ownership must map a unit of coverage.units to the sorted, non-empty list of its partly writer-owned tables")
    nra = c["not_run_allowed"]
    if not (isinstance(nra, Mapping) and all(k in c["units"] and k not in c["groups"] and k not in c["seeded"] and isinstance(v, str)
                                             and re.fullmatch(r"NEEDS_[A-Z0-9_]+", v) for k, v in nra.items()) and list(nra) == sorted(nra)):
        raise RehearsalError("coverage.not_run_allowed must map a sorted, plain (not group, not seeded) unit of coverage.units to its NEEDS_ reason")
    ed = c["expected_differences"]
    if not (isinstance(ed, list) and all(isinstance(e, Mapping) and set(e) == {"unit", "table", "columns", "reference"} and e["unit"] in c["units"]
                                         and isinstance(e["table"], str) and _unit_list(e["columns"]) and e["columns"]
                                         and isinstance(e["reference"], str) and e["reference"].strip() for e in ed)):
        raise RehearsalError("coverage.expected_differences must list {unit, table, columns, reference} records of units in coverage.units")
    scope = "declared_only" if (c["partial"] or c["undeclared"] or c["non_deterministic"] or c["seeded"] or c["partial_ownership"]) else "all_declared_full"
    if c["scope"] != scope:
        raise RehearsalError(f"coverage.scope is derived: it must be {scope!r} for this coverage")
    return c


def check_rows(rows: Any, prod: Mapping, reh: Mapping) -> dict:
    """Row counts per unit per table for each side: {unit: {"production": {table: n} | null, "rehearsal": {...} | null}}, present for every
    unit that has a fingerprint on that side, non-negative ints."""
    if not isinstance(rows, Mapping):
        raise RehearsalError("rows must be an object of unit -> {production, rehearsal} per-table row counts")
    out: dict = {}
    for u, v in rows.items():
        if not (isinstance(u, str) and _ASSET_ID.fullmatch(u) and isinstance(v, Mapping) and set(v) == {"production", "rehearsal"}):
            raise RehearsalError("rows entries must be {production, rehearsal} per unit")
        for side in ("production", "rehearsal"):
            t = v[side]
            if t is not None and not (isinstance(t, Mapping) and t and all(isinstance(k, str) and isinstance(n, int) and not isinstance(n, bool) and n >= 0
                                                                         for k, n in t.items())):
                raise RehearsalError(f"rows.{u}.{side} must be null or a non-empty object of table -> non-negative int")
        out[u] = {"production": dict(v["production"]) if v["production"] is not None else None,
                  "rehearsal": dict(v["rehearsal"]) if v["rehearsal"] is not None else None}
    for side, env in (("production", prod), ("rehearsal", reh)):
        for u in env:
            if out.get(u, {}).get(side) is None:
                raise RehearsalError(f"rows.{u}.{side} is missing: a unit with a fingerprint must carry its row counts")
    return out


def check_not_run(not_run: Any, expected: Sequence[str]) -> dict:
    """The build record's `not_run` entries as {unit: NEEDS_ reason} (the drill's input from the verified build record; {} when no record). Structure
    only here: that a unit is on the closed list, that the reason matches and that the rehearsal really has no fingerprint for it are checked by
    the comparison, which reports them as problems (a FAIL), never as an accepted explanation."""
    if not_run is None:
        return {}
    if not (isinstance(not_run, Mapping) and all(isinstance(k, str) and k in expected and isinstance(v, str) and re.fullmatch(r"NEEDS_[A-Z0-9_]+", v)
                                                 for k, v in not_run.items())):
        raise RehearsalError("not_run must be an object of comparison unit -> NEEDS_ reason (from the verified build record)")
    return {k: not_run[k] for k in sorted(not_run)}


def compare_fingerprint_sets(production: Any, rehearsal: Any, explained: Any = None, *, expected_assets: Any, commit: Any, coverage: Any, rows: Any, runtime: Any, not_run: Any = None, projections: Any = None, horizons: Any = None,
                             max_undecided_share: float = DEFAULT_LIMITS[0], max_difference_share: float = DEFAULT_LIMITS[1]) -> dict:
    """E5.7: compare per-unit semantic fingerprints (E5.5's definition; both inputs carry its marker) of production (read as
    suvarna_reader) with the rehearsal rebuild, over the units the drill MUST cover (`expected_assets`, required: declared assets with tables
    of their own and groups). FAIL if any expected unit is on neither side (`uncovered`), any compared unit is outside the expected list,
    any difference is unexplained, an explanation has no difference, an explanation is malformed (reason code valid for the difference
    kind, detail >= 40 characters and not repeated across units; `rolling_horizon` / `source_unavailable_offline` only on a unit flagged
    rolling_horizon / platform_bound in `coverage`), the share of EXPLAINED differences without an SS-recorded decision id `N-<n>` exceeds
    `max_undecided_share` (default 0), the share of differing units exceeds `max_difference_share`, or two equal fingerprints carry different
    row counts. A unit that is EMPTY on both sides (zero rows everywhere) is never `equal`: it is listed in `empty_both_sides` and the
    verdict cannot be PASS (it reads UNMEASURED). SEEDED units (`coverage.seeded`: copied from production, not rebuilt) are SHOWN (key
    `seeded`: unit -> equal | differs kind | empty_both_sides | uncovered) but EXCLUDED from the rebuilt-equals-source claim: an equal
    seeded unit is not in `equal`, never counts toward PASS or PASS_DECLARED_ONLY (a drill whose only equal units are seeded reads
    UNMEASURED: it needs at least one non-seeded unit equal or explained-different). PARTIAL-OWNERSHIP units (`coverage.partial_ownership`:
    tables whose rows are only partly writer-owned) are compared on the WHOLE table, never filtered: a difference there is explained
    AUTOMATICALLY with the fixed code `migration_owned_rows` (expected, not unexplained, not counted in the share limits), the code is
    refused on a unit without the declaration, and such a unit keeps the scope PASS_DECLARED_ONLY. A seeded unit that differs is still reported in
    `differences` but is not `unexplained`, does not count in the share limits and does not by itself fail the drill. RUNTIME (decision B1): `runtime` is the closed
    block of where the rebuild ran (the rehearsal receipt's `rebuild.runtime`); when its platform is not linux/amd64 every platform-bound unit
    (`coverage.non_deterministic` flag platform_bound) that would read equal is listed in `claimed_unverified` instead: never `equal`, never counted
    toward PASS or PASS_DECLARED_ONLY (a platform-bound unit is always flagged non-deterministic, so the verdict is never a bare PASS anyway).
    ROLLING HORIZON (decision N-135): the explanation code `rolling_horizon` is accepted ONLY with `horizons[unit]` evidence: both blocks present and valid, the
    production overlap_cutoff equal to its own max_date, the REHEARSAL overlap_cutoff equal to the production max_date, rehearsal max_date >= production
    max_date, and the shared range row-for-row equal (same overlap_rows and the same overlap_sha256, the E5.5 fingerprint over the rows up to the cutoff); every
    extra rehearsal row is then after the production horizon. An accepted explanation carries `decision` N-135 and an `evidence` record whose `summary`
    reads "N-135: rows 31101 vs 31081 (rehearsal vs production), built-through dates D1 vs D2, overlap equal over N rows"; otherwise the unit stays an unexplained
    difference. A `horizons` entry for a unit not flagged rolling_horizon is refused.
    EXPECTED DIFFERENCES (`coverage.expected_differences`: a recorded difference limited to named columns): a unit that differs and carries such a record can be
    explained ONLY if `projections[unit]` (the table's fingerprint with those columns ignored, both sides) is given and EQUAL; otherwise something else in the unit
    changed, no explanation covers it and a problem says so. `known_differences` lists each record with observed / limited_to_columns / explained.
    NOT-RUN units (decision N-121):
    `not_run` ({unit: NEEDS_ reason}, from the verified build record) plus the explanation code `not_run_declared` (valid only on a
    `missing_in_rehearsal` difference of a unit on the closed list `coverage.not_run_allowed` whose build-record entry is `not_run` with the matching
    reason; refused for a unit outside the list, for a complete asset and for a unit missing for any other reason) explain a missing unit WITHOUT
    measuring it: it is listed in `unmeasured`, is never `equal`, never counts toward PASS or PASS_DECLARED_ONLY (a PASS with any is
    PASS_DECLARED_ONLY) and is not in the share limits. Otherwise PASS, or
    PASS_DECLARED_ONLY whenever `coverage` says any asset is partial, undeclared, non-deterministic or seeded: a bare PASS means every
    L0 asset was declared, full, deterministic and rebuilt. The output embeds both
    fingerprint sets, the explanations, the coverage block, the row counts, input hashes, the commit and the tool hash, and `validate_drill`
    re-derives it."""
    if not (isinstance(commit, str) and HEX40.fullmatch(commit)):
        raise RehearsalError("commit must be 40-hex")
    if isinstance(expected_assets, (str, bytes, Mapping)) or not isinstance(expected_assets, (list, tuple, set, frozenset)):
        raise RehearsalError("expected_assets is required: the list of asset ids the drill must cover")
    exp = list(expected_assets)
    if not exp or not all(isinstance(a, str) and _ASSET_ID.fullmatch(a) for a in exp) or len(set(exp)) != len(exp):
        raise RehearsalError("expected_assets must be a non-empty list of unique asset ids")
    if explained is None:
        explained = {}
    if not isinstance(explained, Mapping):
        raise RehearsalError("explained must be an object of asset id -> explanation")
    for share, name in ((max_undecided_share, "max_undecided_share"), (max_difference_share, "max_difference_share")):
        if isinstance(share, bool) or not isinstance(share, (int, float)) or not 0 <= share <= 1:
            raise RehearsalError(f"{name} must be a number in [0, 1]")
    prod, reh = _check_envelope("production", production), _check_envelope("rehearsal", rehearsal)
    cov = check_coverage(coverage, exp)
    rws = check_rows(rows, prod, reh)
    nr = check_not_run(not_run, exp)
    rt = check_runtime(runtime)
    proj = check_projections(projections, cov)
    hz = check_horizons(horizons, cov)
    on_linux = rt["platform"] == RUNTIME_PLATFORM
    expected = sorted(exp)
    seeded = set(cov["seeded"])
    uncovered_all = [a for a in expected if a not in prod and a not in reh]
    uncovered = [a for a in uncovered_all if a not in seeded]
    unexpected = sorted((set(prod) | set(reh)) - set(expected))
    equal, diffs, problems, empty, seeded_status, claimed = [], [], [], [], {}, []
    for a in expected:
        if a in uncovered_all:
            if a in seeded:
                seeded_status[a] = "uncovered"
            continue
        if a in prod and a in reh and prod[a] == reh[a]:
            if rws[a]["production"] != rws[a]["rehearsal"]:
                problems.append(f"{a}: equal fingerprints but different row counts {rws[a]['production']} vs {rws[a]['rehearsal']}: a fingerprint covers its rows, so one side is wrong")
            elif a in seeded:
                seeded_status[a] = "empty_both_sides" if sum(rws[a]["production"].values()) == 0 else "equal"      # shown, never counted
            elif sum(rws[a]["production"].values()) == 0:
                empty.append(a)                                # equal because both are empty is not equality of content
            elif not on_linux and "platform_bound" in cov["non_deterministic"].get(a, []):
                claimed.append(a)                              # a platform-bound unit rebuilt off linux/amd64: equal-looking, never counted
            else:
                equal.append(a)
            continue
        kind = "missing_in_rehearsal" if a not in reh else "missing_in_production" if a not in prod else "fingerprint_differs"
        if a in seeded:
            seeded_status[a] = kind
        diffs.append({"asset": a, "kind": kind, "production": prod.get(a), "rehearsal": reh.get(a), "explained": None})
    seen: dict[str, str] = {}
    undecided = 0
    auto: set[str] = set()
    for u, why_nr in nr.items():                           # the build record's not_run entries must be on the closed list, carry its reason, and have no rehearsal fingerprint
        if u not in cov["not_run_allowed"]:
            problems.append(f"{u}: not_run in the build record but not in the closed not_run list {sorted(cov['not_run_allowed'])} (decision N-121): an asset cannot become not_run")
        elif why_nr != cov["not_run_allowed"][u]:
            problems.append(f"{u}: not_run needs the reason {cov['not_run_allowed'][u]!r}, the build record says {why_nr!r}")
        elif u in reh:
            problems.append(f"{u}: the build record says not_run but the rehearsal has a fingerprint for it")
    declared_not_run: set[str] = set()
    ed_units = {e["unit"]: e for e in cov["expected_differences"]}
    limited: dict[str, bool] = {}
    for d in diffs:
        if d["kind"] == "fingerprint_differs" and d["asset"] in ed_units:
            pj = proj.get(d["asset"])
            limited[d["asset"]] = bool(pj and pj["production"] is not None and pj["production"] == pj["rehearsal"])
            if not limited[d["asset"]]:
                problems.append(f"{d['asset']}: the difference is not limited to the expected columns {ed_units[d['asset']]['columns']} of "
                                f"{ed_units[d['asset']]['table']}: the fingerprint WITHOUT them "
                                f"{'is not given on both sides' if not pj or pj['production'] is None or pj['rehearsal'] is None else 'still differs'}, so something else "
                                "in the unit changed and the recorded difference cannot explain it")
    for d in diffs:
        if limited.get(d["asset"]) is False:
            continue                                         # not limited to the recorded columns: no explanation can cover it (reported above)
        e = explained.get(d["asset"])
        if e is None:
            if d["kind"] == "fingerprint_differs" and d["asset"] in cov["partial_ownership"]:
                d["explained"] = {"reason_code": PARTIAL_OWNERSHIP_CODE, "detail": PARTIAL_OWNERSHIP_DETAIL}      # fixed, automatic, expected
                auto.add(d["asset"])
            continue
        why = _explanation_problem(d["kind"], e)
        if why:
            problems.append(f"{d['asset']}: {why}")
            continue
        if e["reason_code"] == PARTIAL_OWNERSHIP_CODE and d["asset"] not in cov["partial_ownership"]:
            problems.append(f"{d['asset']}: reason code {PARTIAL_OWNERSHIP_CODE} needs a table declared partial_ownership in this unit "
                            "(coverage.partial_ownership): the declaration is what makes migration-owned rows an expected difference")
            continue
        if e["reason_code"] == NOT_RUN_CODE:
            if d["asset"] not in cov["not_run_allowed"]:
                problems.append(f"{d['asset']}: reason code {NOT_RUN_CODE} is refused: the unit is not in the closed not_run list {sorted(cov['not_run_allowed'])} (N-121)")
                continue
            if d["asset"] not in nr:
                problems.append(f"{d['asset']}: reason code {NOT_RUN_CODE} is refused: the build record has no `not_run` entry for it (a complete asset, an asset "
                                "missing for another reason or no build record is never covered)")
                continue
            if nr[d["asset"]] != cov["not_run_allowed"][d["asset"]]:
                problems.append(f"{d['asset']}: reason code {NOT_RUN_CODE} is refused: the build record's reason {nr[d['asset']]!r} is not "
                                f"{cov['not_run_allowed'][d['asset']]!r}")
                continue
        need = CODE_REQUIRES_FLAG.get(e["reason_code"])
        if need is not None and need not in cov["non_deterministic"].get(d["asset"], []):
            problems.append(f"{d['asset']}: reason code {e['reason_code']} needs the unit to be flagged {need} in the declarations "
                            f"(flags: {cov['non_deterministic'].get(d['asset'], [])})")
            continue
        evidence = None
        if e["reason_code"] == "rolling_horizon":                # N-135: accepted ONLY with the evidence that the shared range is row-for-row equal
            why_h, evidence = horizon_evidence(hz.get(d["asset"]))
            if why_h:
                problems.append(f"{d['asset']}: reason code rolling_horizon is refused ({HORIZON_RULE}): {why_h}")
                continue
            if "decision" in e and e["decision"] != HORIZON_RULE:
                problems.append(f"{d['asset']}: a rolling_horizon explanation is decided by {HORIZON_RULE}; the decision id {e['decision']!r} is not accepted")
                continue
        norm = _normal_detail(e["detail"])
        if norm in seen:
            problems.append(f"{d['asset']}: detail repeats the one given for {seen[norm]} (an explanation is per asset)")
            continue
        seen[norm] = d["asset"]
        d["explained"] = {**e, "decision": HORIZON_RULE, "evidence": evidence} if evidence is not None else dict(e)
        if e["reason_code"] == NOT_RUN_CODE:
            declared_not_run.add(d["asset"])                   # decided by N-121 itself (the closed list); never measured
        elif evidence is not None:
            pass                                               # decided by N-135 itself, on evidence
        elif "decision" not in e and d["asset"] not in seeded:
            undecided += 1
    stray = sorted(set(explained) - {d["asset"] for d in diffs})
    rebuilt = [a for a in expected if a not in seeded]                    # the units the rebuilt-equals-source claim is about
    rebuilt_diffs = [d for d in diffs if d["asset"] not in seeded and d["asset"] not in auto and d["asset"] not in declared_not_run]            # expected (migration-owned) ones are not "too many"
    unexplained = [d["asset"] for d in diffs if d["asset"] not in seeded and d["explained"] is None]
    if rebuilt and undecided / len(rebuilt) > max_undecided_share:
        problems.append(f"{undecided} explained difference(s) have no decision id: over the allowed share {max_undecided_share}")
    if rebuilt and len(rebuilt_diffs) / len(rebuilt) > max_difference_share:
        problems.append(f"{len(rebuilt_diffs)} of {len(rebuilt)} expected assets differ: over the allowed share {max_difference_share}")
    failed = bool(unexplained or stray or uncovered or unexpected or problems)
    measured = len(equal) + sum(1 for d in diffs if d["asset"] not in seeded and d["explained"] is not None and d["asset"] not in declared_not_run)
    result = ("FAIL" if failed else "UNMEASURED" if (empty or measured == 0)
              else ("PASS" if cov["scope"] == "all_declared_full" and not declared_not_run else "PASS_DECLARED_ONLY"))
    return {"schema": DRILL_SCHEMA, "item": "E5.7", "result": result, "commit": commit,
            "tool_sha256": tool_sha256(), "definition": FINGERPRINT_DEFINITION, "expected_assets": expected,
            "production": fingerprint_set(prod), "rehearsal": fingerprint_set(reh), "explained_input": dict(explained),
            "inputs": {"production_sha256": sha256_text(canonical_json(fingerprint_set(prod))),
                       "rehearsal_sha256": sha256_text(canonical_json(fingerprint_set(reh))),
                       "explained_sha256": sha256_text(canonical_json(dict(explained)))},
            "equal": equal, "differences": diffs, "unexplained": unexplained, "uncovered": uncovered, "unexpected": unexpected,
            "explanations_without_difference": stray, "problems": problems,
            "limits": {"max_undecided_share": max_undecided_share, "max_difference_share": max_difference_share,
                       "min_detail_chars": MIN_DETAIL_CHARS},
            "coverage": cov, "rows": rws, "empty_both_sides": empty, "seeded": seeded_status,
            "not_run": nr, "unmeasured": sorted(declared_not_run), "runtime": rt, "claimed_unverified": claimed, "horizons": hz, "projections": proj,
            "known_differences": [{"unit": e["unit"], "table": e["table"], "columns": list(e["columns"]), "reference": e["reference"],
                                   "observed": e["unit"] in limited, "limited_to_columns": limited.get(e["unit"]),
                                   "explained": any(d["asset"] == e["unit"] and d["explained"] is not None for d in diffs)} for e in cov["expected_differences"]]}


def validate_drill(doc: Any, tool_sha: str | None = None, declarations_coverage: Mapping | None = None) -> list[str]:
    """Problems with an E5.7 comparison document ([] = valid): closed keys, the repo tool's hash, and every derived field
    (result, differences, coverage, problems, input hashes) re-derived from the embedded inputs. Never raises."""
    try:
        if not isinstance(doc, Mapping) or set(doc) != set(DRILL_KEYS):
            return ["the drill document is not an object with exactly the closed keys"]
        want_tool = tool_sha if tool_sha is not None else tool_sha256()
        p = [] if doc["tool_sha256"] == want_tool else ["tool_sha256 is not the sha256 of the repo tool"]
        lim = doc["limits"]
        if not (isinstance(lim, Mapping) and set(lim) == {"max_undecided_share", "max_difference_share", "min_detail_chars"}):
            return p + ["limits malformed"]
        again = compare_fingerprint_sets(doc["production"], doc["rehearsal"], doc["explained_input"],
                                         expected_assets=doc["expected_assets"], commit=doc["commit"],
                                         coverage=doc["coverage"], rows=doc["rows"], not_run=doc["not_run"], runtime=doc["runtime"], projections=doc["projections"], horizons=doc["horizons"],
                                         max_undecided_share=lim["max_undecided_share"],
                                         max_difference_share=lim["max_difference_share"])
        again["tool_sha256"] = doc["tool_sha256"]
        if lim["min_detail_chars"] != MIN_DETAIL_CHARS:
            p.append("min_detail_chars differs from the tool's")
        if (lim["max_undecided_share"], lim["max_difference_share"]) != DEFAULT_LIMITS:
            p.append(f"limits were overridden away from the defaults {DEFAULT_LIMITS}: a drill that needs that is the strategist's call, "
                     "not a PASS this validator can give")
        if again != dict(doc):
            p.append("the document differs from the comparison re-derived from its embedded inputs")
        if declarations_coverage is not None and doc["coverage"] != dict(declarations_coverage):
            p.append("the coverage block is not the one the declarations file in use yields: the drill was made under other declarations")
        return p
    except RehearsalError as exc:
        return [f"drill inputs refused: {exc}"]
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        return [f"malformed drill document ({type(exc).__name__}: {str(exc)[:120]})"]


def _load_declarations(declarations_path: str | Path | None = None):
    import fingerprint_declarations as fd  # noqa: PLC0415
    if fd.FINGERPRINT_DEFINITION != FINGERPRINT_DEFINITION:
        raise RehearsalError("fingerprint_declarations and the harness name different fingerprint definitions")
    try:
        return fd.load_declarations(declarations_path) if declarations_path else fd.load_declarations()
    except fd.DeclarationError as exc:
        raise RehearsalError(f"the fingerprint declarations are refused: {exc}") from exc


def drill_expected_assets(declarations_path: str | Path | None = None) -> list[str]:
    """The comparison units an E5.7 drill must cover: every DECLARED asset with tables of its own plus every GROUP (`grp_<id>`: a shared table
    is compared as one unit) of FINGERPRINT_DECLARATIONS.json (the loader validates the file against the registry snapshot, the schema extract
    and the writer evidence). Undeclared assets are reported by `suvarna_mirror_drill.py expected` and carried in the drill's `coverage`
    block, not silently dropped."""
    return _load_declarations(declarations_path).expected_assets()


def drill_coverage(declarations_path: str | Path | None = None) -> dict:
    """The `coverage` block the drill document embeds (declared / partial / undeclared / non-deterministic / groups / expected differences)."""
    return _load_declarations(declarations_path).drill_coverage()


# ═════════════════════════ D. self-test (disposable PG, synthetic data) ═════════════════════════

def _git_commit(repo: str | Path) -> str | None:
    try:
        p = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30,
                           env=_git_env(), stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    out = p.stdout.strip()
    return out if p.returncode == 0 and HEX40.fullmatch(out) else None


SYNTH_NS = uuid.UUID("5e56e56e-5e56-4e56-8e56-5e56e56e56e5")
SYNTH_DECL = {"table": "e56_synth_asset", "scope": "chart", "natural_key": ["node_key"],
              "volatile_columns": ["id", "build_id", "created_at"]}


def measure_idempotent_rebuild(conn: Any) -> dict:
    """Synthetic table + two synthetic charts. A delete-then-insert rebuild of chart A changes only volatile columns."""
    import nikasha_stale_certs as nsc  # noqa: PLC0415
    a, b = str(uuid.uuid5(SYNTH_NS, "chart-a")), str(uuid.uuid5(SYNTH_NS, "chart-b"))
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS e56_synth_asset")
    cur.execute("CREATE TABLE e56_synth_asset (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, node_key text NOT NULL, "
                "payload jsonb NOT NULL, score numeric(12,4) NOT NULL, build_id text NOT NULL, "
                "created_at timestamptz NOT NULL DEFAULT now(), UNIQUE (chart_id, node_key))")

    def load(chart: str, build: str, bump: str | None = None) -> None:
        for i in range(40):
            score = f"{i * 1.25:.4f}"
            if bump == f"k{i:02d}":
                score = f"{i * 1.25 + 0.5:.4f}"
            cur.execute("INSERT INTO e56_synth_asset (chart_id, node_key, payload, score, build_id) VALUES (%s,%s,%s::jsonb,%s,%s)",
                        (chart, f"k{i:02d}", json.dumps({"i": i, "tag": f"t{i % 7}"}), score, build))
    load(a, "build-1")
    load(b, "build-1")
    conn.commit()
    ids_before = {r[0] for r in conn.execute("SELECT id FROM e56_synth_asset WHERE chart_id = %s", (a,)).fetchall()}
    fp_a0 = nsc.table_fingerprint(conn, SYNTH_DECL, a)
    fp_b0 = nsc.table_fingerprint(conn, SYNTH_DECL, b)
    rows0 = conn.execute("SELECT count(*) FROM e56_synth_asset WHERE chart_id = %s", (a,)).fetchone()[0]
    cur.execute("DELETE FROM e56_synth_asset WHERE chart_id = %s", (a,))     # the per-chart delete-then-insert rebuild (CLAUDE.md N.3)
    load(a, "build-2")
    conn.commit()
    ids_after = {r[0] for r in conn.execute("SELECT id FROM e56_synth_asset WHERE chart_id = %s", (a,)).fetchall()}
    fp_a1 = nsc.table_fingerprint(conn, SYNTH_DECL, a)
    fp_b1 = nsc.table_fingerprint(conn, SYNTH_DECL, b)
    rows1 = conn.execute("SELECT count(*) FROM e56_synth_asset WHERE chart_id = %s", (a,)).fetchone()[0]
    cur.execute("DELETE FROM e56_synth_asset WHERE chart_id = %s", (a,))
    load(a, "build-3", bump="k07")                                              # ONE semantic column changes
    conn.commit()
    fp_a2 = nsc.table_fingerprint(conn, SYNTH_DECL, a)
    conn.execute("DROP TABLE IF EXISTS e56_synth_asset")
    conn.commit()
    return {"fingerprint_before": fp_a0, "fingerprint_after_rebuild": fp_a1, "fingerprint_after_material_change": fp_a2,
            "other_chart_before": fp_b0, "other_chart_after": fp_b1, "rows_before": rows0, "rows_after": rows1,
            "volatile_columns_changed": ids_before.isdisjoint(ids_after) and bool(ids_before)}


def _git_env() -> dict:
    """A scrubbed environment for every git call: nothing inherited (no GIT_*, no user config, no prompts, no locale)."""
    return {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": "/nonexistent", "LC_ALL": "C", "TZ": "UTC",
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0", "GIT_AUTHOR_NAME": "e56", "GIT_AUTHOR_EMAIL": "e56@invalid",
            "GIT_COMMITTER_NAME": "e56", "GIT_COMMITTER_EMAIL": "e56@invalid"}


def _fixture_repo(tmp: Path, family_doc: dict | None) -> Path:
    repo = tmp / "repo"
    repo.mkdir(parents=True)
    env = _git_env()
    run = lambda *a: subprocess.run(["git", "-C", str(repo), *a], env=env, capture_output=True, text=True, check=True)  # noqa: E731
    run("init", "-q", "-b", "main")
    (repo / "README").write_text("e56 fixture\n")
    if family_doc is not None:
        d = repo / "00_ARCHITECTURE" / "control"
        d.mkdir(parents=True)
        (d / "FAMILY_ASSETS.json").write_text(json.dumps(family_doc))
    run("add", "-A")
    run("-c", "commit.gpgsign=false", "commit", "-q", "-m", "fixture")
    return repo


def measure_family_refusal() -> dict:
    """Drive `suvarna_level_wave.run_cli` (its own refusal path) with a request that intersects a fixture family set. The
    `connect` and `dispatch` it is given RAISE: a refusal that reached the database or dispatched would be loud."""
    import suvarna_level_wave as slw  # noqa: PLC0415
    fam = {"family_gochara": ["ka_fixture_gochara"], "family_sangam": ["ka_fixture_sangam"], "family_kshetra": [],
           "family_readers_L3": [], "family_readers_L4": [], "family_readers_L5": [],
           "family_set": ["ka_fixture_gochara", "ka_fixture_sangam"]}
    calls = {"connect": 0, "dispatch": 0}

    def connect():
        calls["connect"] += 1
        raise AssertionError("the refused request touched the database")

    def dispatch(*a, **k):
        calls["dispatch"] += 1
        raise AssertionError("the refused request dispatched")

    def run(repo: Path, assets: str, *, commit: bool) -> tuple[int, list[dict]]:
        argv = ["--chart-id", str(uuid.uuid5(SYNTH_NS, "chart-a")), "--assets", assets, "--repo", str(repo),
                "--family-ref", "main"] + (["--commit", "--mode", "single-run"] if commit else [])
        out = io.StringIO()
        code = slw.run_cli(slw.build_parser().parse_args(argv), connect=connect, git=_git_with_env, out=out, dispatch=dispatch,
                           live_reader=lambda: "0" * 40)       # injected: a rehearsal never calls gcloud
        last = [json.loads(ln) for ln in out.getvalue().splitlines() if ln.strip().startswith("{")][-1]
        return code, [dict(r) for r in last.get("refusals", [])]

    with tempfile.TemporaryDirectory(prefix="e56_family.") as td:
        with_file = _fixture_repo(Path(td) / "a", fam)
        no_file = _fixture_repo(Path(td) / "b", None)
        code, refs = run(with_file, "bo_fixture_a,ka_fixture_gochara,ka_gochara_fixture", commit=False)
        connects_after_refusal, dispatches = calls["connect"], calls["dispatch"]
        ctl_code, ctl_refs = run(with_file, "bo_fixture_a,bo_fixture_b", commit=False)
        _mc, missing_refs = run(no_file, "bo_fixture_a", commit=True)
    codes, ctl_codes, missing_codes = ([str(r.get("code")) for r in x] for x in (refs, ctl_refs, missing_refs))
    famrefs = [r for r in refs if r.get("code") == "FAMILY_ASSET"]
    return {"intersecting_assets": ["ka_fixture_gochara", "ka_gochara_fixture"],
            "refused_assets": sorted({str(r.get("asset")) for r in famrefs}), "refused_via": sorted({str(r.get("via")) for r in famrefs}),
            "exit_code": code, "refusal_codes": sorted(set(codes)),
            "connect_calls": connects_after_refusal, "dispatch_calls": dispatches, "control_exit_code": ctl_code,
            "control_refusal_codes": sorted(set(ctl_codes)), "control_connect_calls": calls["connect"] - connects_after_refusal,
            "missing_file_committing_codes": sorted(set(missing_codes))}


def _git_with_env(repo: str, args: Sequence[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False, timeout=30,
                          stdin=subprocess.DEVNULL, env=_git_env())


def measure_hold(tracker_dir: str | Path) -> dict:
    """The tracker's own `hold_guard.evaluate`, imported read-only from `tracker_dir` (the governance dir holding
    `suvarna_tracker/`), against a throw-away SUVARNA_HOME."""
    import importlib  # noqa: PLC0415
    tdir = str(Path(tracker_dir).resolve())
    guard_file = Path(tdir) / "suvarna_tracker" / "hold_guard.py"
    if not guard_file.is_file():
        raise RehearsalError(f"{guard_file} not found")
    old_flag, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    sys.path.insert(0, tdir)
    stale = [k for k in sys.modules if k == "suvarna_tracker" or k.startswith("suvarna_tracker.")]
    saved = {k: sys.modules.pop(k) for k in stale}
    try:
        hg = importlib.import_module("suvarna_tracker.hold_guard")
        cmd = "python3 platform/scripts/governance/suvarna_level_wave.py --chart-id x --assets bo_fixture_a --commit"
        with tempfile.TemporaryDirectory(prefix="e56_hold.") as home:
            (Path(home) / "run").mkdir()
            off, _ = hg.evaluate("Bash", {"command": cmd}, home=home)
            (Path(home) / "run" / "SUVARNA_HOLD").write_text("e56 self-test hold\n")
            on, reason = hg.evaluate("Bash", {"command": cmd}, home=home)
            benign, _ = hg.evaluate("Bash", {"command": "git status --short"}, home=home)
        return {"hold_guard_sha256": sha256_file(guard_file), "command": cmd, "blocked_with_hold": bool(on),
                "blocked_without_hold": bool(off), "reason_with_hold": str(reason)[:200],
                "non_dispatch_blocked_with_hold": bool(benign)}
    finally:
        for k in [k for k in sys.modules if k == "suvarna_tracker" or k.startswith("suvarna_tracker.")]:
            sys.modules.pop(k, None)
        sys.modules.update(saved)
        with contextlib.suppress(ValueError):
            sys.path.remove(tdir)
        sys.dont_write_bytecode = old_flag


def measure_connections(log: ConnectionLog) -> dict:
    """The log of opened connections, plus a probe: a non-loopback endpoint must be refused and open no socket."""
    probes = {"called": 0}

    def must_not_connect(*a, **k):
        probes["called"] += 1
        raise AssertionError("a refused endpoint opened a connection")

    refused = 0
    for url in ("postgresql://u@10.0.0.5:5432/rehearsal", "postgresql://u@localhost:55432/rehearsal"):
        try:
            connect_checked(url, "rehearsal", log, connect=must_not_connect)
        except EndpointRefused:
            refused += 1
    return {"opened": [dict(e) for e in log.opened], "refused_count": len(log.refused),
            "probe_refused_without_socket": refused == 2 and probes["called"] == 0}


NEEDS_BY_CASE = {
    "find_fix_rebuild_certify": "NEEDS_REHEARSAL_ORCHESTRATOR_RUN",
    "f3_proof": "NEEDS_REHEARSAL_SCHEMA_WITH_1036",
    "canary_triggers_reversal": "NEEDS_CANARY_REVERSAL_MECHANISM",
}


def run_self_test(*, tracker_dir: str | Path | None = None, repo: str | Path = REPO_ROOT,
                  connect_url: str | None = None, pg_info: Mapping | None = None,
                  unavailable_reason: str = "NEEDS_DISPOSABLE_PG") -> dict:
    """The cases that can run offline on a disposable PostgreSQL with synthetic data. `connect_url`/`pg_info` ({port,
    data_directory}) come from the repo's `_disposable_pg` fixture; without them the database cases are UNMEASURED with
    `unavailable_reason` (NEEDS_DISPOSABLE_PG, or NEEDS_PSYCOPG when the driver is not installed). Every connection goes
    through `connect_checked` (scrubbed environment, answering-server identity verified, logged)."""
    log = ConnectionLog()
    cases: list[dict] = []
    pg_version = ""
    if connect_url:
        if not (isinstance(pg_info, Mapping) and pg_info.get("data_directory") and _is_int(pg_info.get("port"))):
            raise RehearsalError("a disposable connection needs the fixture's identity {data_directory, port}")
        conn = connect_checked(connect_url, "disposable", log,
                               expect={"data_directory": pg_info["data_directory"], "port": pg_info["port"]})
        try:
            pg_version = str(conn.execute("SHOW server_version").fetchone()[0])
            try:
                cases.append(case_result("idempotent_rebuild_fingerprint_unchanged", measured=measure_idempotent_rebuild(conn),
                                         basis="synthetic_fixture"))
            except ImportError:
                cases.append(unmeasured_case("idempotent_rebuild_fingerprint_unchanged", "NEEDS_PYTHON_DEPENDENCIES"))
        finally:
            conn.close()
    else:
        cases.append(unmeasured_case("idempotent_rebuild_fingerprint_unchanged", unavailable_reason))
    try:
        cases.append(case_result("family_dispatch_refused", measured=measure_family_refusal(), basis="synthetic_fixture"))
    except ImportError:
        cases.append(unmeasured_case("family_dispatch_refused", "NEEDS_PYTHON_DEPENDENCIES"))
    if tracker_dir:
        cases.append(case_result("hold_refuses_dispatch", measured=measure_hold(tracker_dir), basis="synthetic_fixture"))
    else:
        cases.append(unmeasured_case("hold_refuses_dispatch", "NEEDS_TRACKER_HOLD_GUARD"))
    if log.opened:
        cases.append(case_result("no_production_write", measured=measure_connections(log), basis="synthetic_fixture"))
    else:
        cases.append(unmeasured_case("no_production_write", unavailable_reason))
    for cid, reason in NEEDS_BY_CASE.items():
        cases.append(unmeasured_case(cid, reason))
    info = pg_info if (connect_url and isinstance(pg_info, Mapping)) else {}          # port 0 = no cluster was started
    cluster = {"kind": "disposable", "host": LOOPBACK, "port": int(info.get("port", 0)),
               "data_directory": str(info.get("data_directory", "")), "pg_version": pg_version}
    env = {"cluster": cluster, "schema_replay": None, "seed": None}
    return build_evidence(mode="self_test", commit=_git_commit(repo), cases=cases, environment=env)


def _disposable_cluster() -> tuple[str, dict] | None:
    """Start the repo's disposable cluster fixture (`__tests__/_disposable_pg.py`). None when no PostgreSQL binaries exist.
    (The fixture's own CREATE DATABASE bootstrap uses its psql; every connection the HARNESS makes goes through the log.)"""
    sys.path.insert(0, str(HERE / "__tests__"))
    try:
        import _disposable_pg as dpg  # noqa: PLC0415
    except ImportError:
        return None
    try:
        cl = dpg.get_cluster()
    except dpg.PGUnavailable:
        return None
    return cl.url, {"port": cl.port, "data_directory": str(cl.data_dir), "_cluster": cl}


# ═════════════════════════ CLI ═════════════════════════

def _print(obj: Any) -> None:
    print(json.dumps(obj, sort_keys=True, indent=2))


def _cmd_cluster(a: argparse.Namespace) -> int:
    pg_bin = a.pg_bin
    try:
        if a.action == "init":
            out = init_cluster(a.root, port=a.port, pg_bin=pg_bin)
        elif a.action == "start":
            out = start_cluster(a.root, pg_bin=pg_bin)
        elif a.action == "stop":
            out = stop_cluster(a.root, pg_bin=pg_bin)
        elif a.action == "status":
            out = status_cluster(a.root)
        elif a.action == "reap":
            out = reap_cluster(a.root, pg_bin=pg_bin, remove_data=a.remove_data, confirm=a.confirm)
        else:
            out = adopt_cluster(a.root, port=a.port)
    except LifecycleError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    _print(out)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog=TOOL_NAME, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("self-test")
    st.add_argument("--out", required=True)
    st.add_argument("--tracker-dir")
    st.add_argument("--repo", default=str(REPO_ROOT))
    v = sub.add_parser("validate")
    v.add_argument("path")
    v.add_argument("--evidence-root")
    v.add_argument("--repo", default=str(REPO_ROOT))
    vd = sub.add_parser("validate-drill")
    vd.add_argument("path")
    vd.add_argument("--declarations", nargs="?", const="default", help="also require the coverage block to be the one these declarations yield "
                                                                      "(no value: the committed FINGERPRINT_DECLARATIONS.json)")
    c = sub.add_parser("cluster")
    c.add_argument("action", choices=("init", "start", "stop", "status", "reap", "adopt"))
    c.add_argument("--root", default=DEFAULT_ROOT)
    c.add_argument("--port", type=int, default=DEFAULT_PORT)
    c.add_argument("--pg-bin", default=DEFAULT_PG_BIN)
    c.add_argument("--remove-data", action="store_true")
    c.add_argument("--confirm")
    sub.add_parser("drill", add_help=False)                       # delegated to suvarna_mirror_drill.py (E5.7 mirror wiring)
    cf = sub.add_parser("compare-fingerprints")
    cf.add_argument("--pre", required=True, help="production envelope {definition, fingerprints}")
    cf.add_argument("--post", required=True, help="rehearsal envelope {definition, fingerprints}")
    cf.add_argument("--expected", required=True, help="JSON list of the L0 asset ids the drill must cover, or the word `declarations`")
    cf.add_argument("--commit", required=True)
    cf.add_argument("--explained")
    cf.add_argument("--projections", help="JSON {unit: {table, production, rehearsal}}: the fingerprints WITHOUT the recorded expected-difference columns (needed to explain such a unit)")
    cf.add_argument("--horizons", help="JSON {unit: {table, production, rehearsal}}: the N-135 horizon blocks of the rolling_horizon units (needed to explain such a unit)")
    cf.add_argument("--runtime", required=True, help="JSON of where the rebuild ran: {platform, os, postgres_version, python_version, swisseph_version, collation}")
    cf.add_argument("--rows", required=True, help="JSON {unit: {production: {table: n}, rehearsal: {table: n}}}: the row counts of both sides")
    cf.add_argument("--coverage", help="JSON coverage block (not needed with --expected declarations, which derives it)")
    cf.add_argument("--out")
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "drill":
        import suvarna_mirror_drill as smd  # noqa: PLC0415
        return smd.main(list(argv[1:]))
    a = ap.parse_args(argv)
    rd = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))  # noqa: E731
    try:
        if a.cmd == "cluster":
            return _cmd_cluster(a)
        if a.cmd == "validate":
            try:
                doc = rd(a.path)
            except (OSError, ValueError) as exc:
                _print({"valid": False, "problems": [f"unreadable evidence file ({type(exc).__name__})"]})
                return 2
            commit = doc.get("commit") if isinstance(doc, Mapping) else None
            problems = validate_evidence(doc, tool_sha256_at_commit(a.repo, commit))      # the tool as committed, else this file
            if not problems and a.evidence_root and isinstance(doc, Mapping):
                problems = check_pointers(doc, a.evidence_root)
            if isinstance(doc, Mapping) and doc.get("mode") == "rehearsal" and not a.evidence_root:
                problems.append("a rehearsal document is validated with --evidence-root")
            _print({"valid": not problems, "problems": problems})
            return 0 if not problems else 2
        if a.cmd == "validate-drill":
            try:
                doc = rd(a.path)
            except (OSError, ValueError) as exc:
                _print({"valid": False, "problems": [f"unreadable drill file ({type(exc).__name__})"]})
                return 2
            commit = doc.get("commit") if isinstance(doc, Mapping) else None
            dcov = None
            if a.declarations:
                dcov = drill_coverage(None if a.declarations == "default" else a.declarations)
            problems = validate_drill(doc, tool_sha256_at_commit(REPO_ROOT, commit), declarations_coverage=dcov)
            _print({"valid": not problems, "problems": problems})
            return 0 if not problems else 2
        if a.cmd == "compare-fingerprints":
            if a.expected == "declarations":
                exp, cov = drill_expected_assets(), drill_coverage()
            else:
                if not a.coverage:
                    raise RehearsalError("--coverage is required with an explicit --expected list (a verdict must say what it covers)")
                exp, cov = rd(a.expected), rd(a.coverage)
            out = compare_fingerprint_sets(rd(a.pre), rd(a.post), rd(a.explained) if a.explained else None,
                                           expected_assets=exp, commit=a.commit, coverage=cov, rows=rd(a.rows), runtime=rd(a.runtime),
                                           projections=rd(a.projections) if a.projections else None, horizons=rd(a.horizons) if a.horizons else None)
            if a.out:
                Path(a.out).parent.mkdir(parents=True, exist_ok=True)
                Path(a.out).write_text(json.dumps(out, sort_keys=True, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            _print(out)
            return 0 if out["result"] in RESULTS_PASS else 4
        started, reason = None, "NEEDS_DISPOSABLE_PG"
        if not _psycopg_available():
            reason = "NEEDS_PSYCOPG"                       # the driver is not installed: UNMEASURED, not an error
        else:
            started = _disposable_cluster()
        try:
            doc = run_self_test(tracker_dir=a.tracker_dir, repo=a.repo, connect_url=started[0] if started else None,
                                pg_info=started[1] if started else None, unavailable_reason=reason)
            write_evidence(doc, a.out)
        finally:
            if started:
                started[1]["_cluster"].stop()
        _print({"mode": doc["mode"], "result": doc["result"], "summary": doc["summary"],
                "cases": {c["id"]: c["result"] if c["result"] != "UNMEASURED" else c["unmeasured_reason"] for c in doc["cases"]}})
        return 4 if doc["result"] == "FAIL" else 0
    except RehearsalError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
