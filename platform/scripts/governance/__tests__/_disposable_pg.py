"""_disposable_pg.py -- a DISPOSABLE PostgreSQL for the governance tests that need a real database.

WHY: a live-SQL defect (the `json_agg` multi-line read, the empty-trailing-field psql parse) is invisible to every mocked test. Those
real-SQL tests used to need the off-production rehearsal cluster and so SKIPPED wherever it was absent, i.e. in CI. This helper starts a
throw-away cluster of its own instead, so they run anywhere PostgreSQL binaries are installed.

WHAT IT DOES (and nothing else):
  * finds server binaries: SUVARNA_PG_BIN (optional override), `pg_config --bindir`, /usr/lib/postgresql/*/bin (Debian/Ubuntu, the CI
    runner), /opt/homebrew/opt/postgresql@*/bin and /opt/homebrew/bin (Homebrew), /usr/local/opt/postgresql@*/bin, `initdb` on PATH;
  * `initdb`s a temp cluster in a private temp dir, `pg_ctl start` on a random free port bound to 127.0.0.1 ONLY (its unix socket lives
    in the temp dir), creates one database, and hands out a connection URL;
  * ALWAYS stops the cluster and deletes the temp dir (atexit + the session fixture's finalizer; idempotent);
  * refuses to be pointed at anything else: the cluster's own identity (data_directory under its temp dir, 127.0.0.1, its port, not
    5432 / 55432 / the env-configured port) is verified at start.

SKIP vs FAIL: it SKIPS (with a visible reason) ONLY when no PostgreSQL server binaries exist at all. If binaries exist but the cluster will
not start, it FAILS LOUDLY (PGStartError carrying the pg_ctl / initdb log tail): a broken Postgres must never read as "skipped".

USE:  from _disposable_pg import disposable_pg, point_psql_at   # noqa: F401  (the fixture must be importable in the test module)
      def test_x(disposable_pg, monkeypatch): point_psql_at(disposable_pg, monkeypatch); ...
It holds NO credentials: the cluster is `trust`-auth, loopback-only, and gone when the session ends.
"""
from __future__ import annotations

import atexit
import json
import glob
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))      # `_pg_watchdog` sits next to this module

FORBIDDEN_PORTS = {5432, 55432}          # production-shaped / rehearsal ports: never ours
DB_NAME = "suvarna_disposable"
DB_USER = "suvarna_disposable"
START_TIMEOUT = 90


class PGUnavailable(Exception):
    """No PostgreSQL server binaries exist at all: the ONLY condition under which a test may skip."""


class PGStartError(RuntimeError):
    """Binaries exist but the disposable cluster could not be created or started (or is not what it claims to be): a loud failure."""


def _version_key(p: str):
    m = re.findall(r"\d+", p)
    return [int(x) for x in m] or [0]


def _has_server(d: Path) -> bool:
    return (d / "initdb").is_file() and (d / "pg_ctl").is_file()


def candidate_bin_dirs() -> list[Path]:
    out: list[str] = []
    env = os.environ.get("SUVARNA_PG_BIN")
    if env:
        out.append(env)
    try:
        p = subprocess.run(["pg_config", "--bindir"], capture_output=True, text=True, timeout=10)
        if p.returncode == 0 and p.stdout.strip():
            out.append(p.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    for pat in ("/usr/lib/postgresql/*/bin", "/opt/homebrew/opt/postgresql@*/bin", "/usr/local/opt/postgresql@*/bin"):
        out += sorted(glob.glob(pat), key=_version_key, reverse=True)
    out += ["/opt/homebrew/bin", "/usr/local/bin"]
    w = shutil.which("initdb")
    if w:
        out.append(str(Path(w).parent))
    seen, res = set(), []
    for d in out:
        if d not in seen:
            seen.add(d)
            res.append(Path(d))
    return res


def find_bin_dir(candidates: list[Path] | None = None) -> Path | None:
    """The first directory holding BOTH `initdb` and `pg_ctl`, or None when there is no PostgreSQL server install at all."""
    for d in (candidates if candidates is not None else candidate_bin_dirs()):
        if _has_server(Path(d)):
            return Path(d)
    return None


def _tail(path: Path, n: int = 40) -> str:
    try:
        return "\n".join(path.read_text(errors="replace").splitlines()[-n:]) or "(empty log)"
    except OSError:
        return "(no log)"


def _free_port() -> int:
    forbidden = set(FORBIDDEN_PORTS)
    for k in ("PGPORT",):
        if os.environ.get(k, "").isdigit():
            forbidden.add(int(os.environ[k]))
    for _ in range(50):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        if port not in forbidden:
            return port
    raise PGStartError("could not find a free loopback port outside the forbidden set")


class Cluster:
    def __init__(self, bin_dir: Path, root: Path, port: int):
        self.bin_dir, self.root, self.port = bin_dir, root, port
        self.data_dir = root / "data"
        self.sock_dir = root / "sock"
        self.log = root / "postgres.log"
        self.host, self.dbname, self.user = "127.0.0.1", DB_NAME, DB_USER
        self.stopped = False

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.dbname}"

    def env(self) -> dict:
        """The libpq environment that reaches THIS cluster and nothing inherited."""
        return {"PGHOST": self.host, "PGPORT": str(self.port), "PGDATABASE": self.dbname, "PGUSER": self.user,
                "PGPASSFILE": "/nonexistent/.pgpass", "PGSERVICEFILE": "/nonexistent/.pg_service.conf", "PGCONNECT_TIMEOUT": "10"}

    def psql(self, sql: str, db: str | None = None) -> str:
        env = {k: v for k, v in os.environ.items() if not (k.startswith("PG") or k in ("DATABASE_URL", "POSTGRES_URL"))}
        env.update(self.env())
        if db:
            env["PGDATABASE"] = db
        p = subprocess.run([str(self.bin_dir / "psql"), "-tAX", "-q", "-v", "ON_ERROR_STOP=1", "-c", sql], capture_output=True,
                           text=True, env=env, timeout=60)
        if p.returncode != 0:
            raise PGStartError(f"psql failed on the disposable cluster: {p.stderr.strip()[:300]}\n--- log tail ---\n{_tail(self.log)}")
        return p.stdout.strip()

    def stop(self) -> None:
        if self.stopped:
            return
        self.stopped = True
        try:
            if (self.data_dir / "postmaster.pid").exists():
                subprocess.run([str(self.bin_dir / "pg_ctl"), "-D", str(self.data_dir), "-m", "immediate", "-w", "-t", "30", "stop"],
                               capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass
        finally:
            shutil.rmtree(self.root, ignore_errors=True)


def _short_tmp() -> str:
    base = tempfile.gettempdir()
    return base if len(base) <= 40 else "/tmp"          # a unix socket path must stay under ~100 characters (macOS TMPDIR is long)


def _write_owner_marker(root: Path) -> None:
    """Record WHO owns this root (this pytest process: pid + start time) so a watchdog or a later session's sweep can tell an orphan from
    a live run, and never touches a directory it cannot attribute."""
    import _pg_watchdog as wd
    (root / wd.OWNER_MARKER).write_text(json.dumps({"parent_pid": os.getpid(), "parent_start": wd.proc_start(os.getpid()), "root": str(root),
                                                   "created": time.time()}), encoding="utf-8")


def _start_watchdog(cl: "Cluster") -> None:
    """A detached process (own session) that stops the cluster and deletes its root once THIS pytest process is gone, however it died."""
    import _pg_watchdog as wd
    script = Path(wd.__file__).resolve()
    try:
        subprocess.Popen([sys.executable, str(script), str(os.getpid()), wd.proc_start(os.getpid()), str(cl.root), str(cl.bin_dir / "pg_ctl")],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
    except OSError:
        pass                                            # best effort: the atexit/finalizer path still covers a normal exit


def sweep_stale_clusters(base: str | Path | None = None, pg_ctl: str | None = None) -> list[str]:
    """Stop and delete leaked clusters of earlier runs: ONLY `suvarna_pg_*` directories directly under `base` that are owned by this user,
    carry a valid ownership marker, and whose recorded owner process (pid + start time) is gone. A directory without a marker, with a
    live owner, or owned by someone else is never touched. Returns the roots it reaped."""
    import _pg_watchdog as wd
    base_dir = Path(base or _short_tmp())
    reaped: list[str] = []
    try:
        entries = sorted(base_dir.glob("suvarna_pg_*"))
    except OSError:
        return reaped
    for root in entries:
        try:
            if not root.is_dir() or root.is_symlink() or root.stat().st_uid != os.getuid():
                continue
        except OSError:
            continue
        m = wd.read_marker(root)
        if m is None or wd.owner_alive(m["parent_pid"], m["parent_start"]):
            continue
        if wd.reap(root, pg_ctl):
            reaped.append(str(root))
    return reaped


def start_cluster(bin_dir: Path) -> Cluster:
    """initdb + pg_ctl start. Any failure after the binaries were found raises PGStartError with the log tail (never a skip)."""
    try:
        sweep_stale_clusters(pg_ctl=str(Path(bin_dir) / "pg_ctl"))     # leaked clusters of earlier killed runs (marker + dead owner only)
    except Exception:                                                  # noqa: BLE001 - housekeeping must never fail a test run
        pass
    root = Path(tempfile.mkdtemp(prefix="suvarna_pg_", dir=_short_tmp()))
    cl = Cluster(Path(bin_dir), root, 0)
    try:
        _write_owner_marker(root)
        cl.sock_dir.mkdir()
        init = subprocess.run([str(bin_dir / "initdb"), "-D", str(cl.data_dir), "-A", "trust", "-U", DB_USER, "-E", "UTF8", "--no-sync",
                               "--locale=C"], capture_output=True, text=True, timeout=120)
        if init.returncode != 0:
            raise PGStartError(f"initdb failed (binaries at {bin_dir}): {init.stderr.strip()[-600:] or init.stdout.strip()[-600:]}")
        last = ""
        for _attempt in range(5):                                # a random free port can be taken between the probe and the start
            cl.port = _free_port()
            opts = (f"-c listen_addresses=127.0.0.1 -p {cl.port} -c unix_socket_directories={cl.sock_dir} "
                    f"-c fsync=off -c synchronous_commit=off -c full_page_writes=off")
            st = subprocess.run([str(bin_dir / "pg_ctl"), "-D", str(cl.data_dir), "-l", str(cl.log), "-o", opts, "-w", "-t",
                                 str(START_TIMEOUT), "start"], capture_output=True, text=True, timeout=START_TIMEOUT + 30)
            if st.returncode == 0:
                break
            last = f"pg_ctl start failed (port {cl.port}): {st.stderr.strip()[-300:]}\n--- postgres.log tail ---\n{_tail(cl.log)}"
            if "already in use" not in _tail(cl.log, 80).lower():
                raise PGStartError(last)
        else:
            raise PGStartError("pg_ctl could not bind a port after 5 attempts: " + last)
        _start_watchdog(cl)                                              # outlives a SIGKILLed pytest and cleans up after it
        cl.psql(f"CREATE DATABASE {DB_NAME}", db="postgres")
        verify_own_cluster(cl)
        return cl
    except BaseException:
        cl.stop()
        raise


def verify_own_cluster(cl: Cluster) -> None:
    """The cluster must be OUR temp cluster: its data directory lives under our temp root, it listens on 127.0.0.1 and on the port we
    chose, and that port is not 5432 / 55432 / the env-configured one. Raises PGStartError otherwise."""
    ident = cl.psql("SELECT current_setting('data_directory') || '|' || coalesce(host(inet_server_addr()),'') || '|' || "
                    "coalesce(inet_server_port()::text,'') || '|' || current_database()")
    data, addr, port, db = (ident.split("|") + ["", "", "", ""])[:4]
    ok = (os.path.realpath(data) == os.path.realpath(str(cl.data_dir)) and addr == "127.0.0.1" and port == str(cl.port)
          and cl.port not in FORBIDDEN_PORTS and os.environ.get("PGPORT", "") != str(cl.port) and db == DB_NAME)
    if not ok:
        raise PGStartError(f"refusing to use a cluster that is not the disposable one: data={data!r} addr={addr!r} port={port!r} db={db!r}")


_lock = threading.Lock()
_state: dict = {"cluster": None, "error": None, "unavailable": None, "tried": False}


def get_cluster() -> Cluster:
    """The ONE disposable cluster of this process (started on first use, cached). Raises PGUnavailable (skip) when no PostgreSQL server
    binaries exist at all, PGStartError (fail) for every other problem; both outcomes are remembered so a broken start is not retried
    per test."""
    with _lock:
        if not _state["tried"]:
            _state["tried"] = True
            bin_dir = find_bin_dir()
            if bin_dir is None:
                _state["unavailable"] = ("no PostgreSQL server binaries (initdb + pg_ctl) found: looked in SUVARNA_PG_BIN, pg_config --bindir, "
                                         "/usr/lib/postgresql/*/bin, /opt/homebrew/opt/postgresql@*/bin, /opt/homebrew/bin, PATH")
            else:
                try:
                    _state["cluster"] = start_cluster(bin_dir)
                    atexit.register(shutdown)
                except PGStartError as exc:
                    _state["error"] = exc
                except Exception as exc:                          # noqa: BLE001 - anything else is still a loud failure, never a skip
                    _state["error"] = PGStartError(f"{type(exc).__name__}: {exc}")
        if _state["unavailable"]:
            raise PGUnavailable(_state["unavailable"])
        if _state["error"]:
            raise _state["error"]
        return _state["cluster"]


def shutdown() -> None:
    with _lock:
        cl = _state.get("cluster")
        if cl is not None:
            cl.stop()


@pytest.fixture(scope="session")
def disposable_pg():
    """The disposable cluster. SKIPS (visible reason) only when no PostgreSQL binaries exist; a cluster that will not start FAILS."""
    try:
        cl = get_cluster()
    except PGUnavailable as exc:
        pytest.skip(str(exc))
    yield cl
    shutdown()


def point_psql_at(cl: Cluster, monkeypatch) -> None:
    """Make the census's own `psql` subprocesses reach THIS cluster only: inherited PG*/DATABASE_URL names are removed, the connection is
    spelled out, and the cluster's bin directory leads PATH."""
    for k in [k for k in os.environ if k.startswith("PG") or k in ("DATABASE_URL", "POSTGRES_URL")]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("PATH", f"{cl.bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    for k, v in cl.env().items():
        monkeypatch.setenv(k, v)
