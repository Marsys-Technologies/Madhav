"""test_disposable_pg.py -- the disposable-Postgres fixture proves itself.

  * CANARY: the cluster the real-SQL tests talk to is OUR temp cluster and nothing else (127.0.0.1, its own port, not 5432 / 55432 / any
    env-configured port, a data directory inside its own temp dir). It refuses to pass against anything else.
  * SKIP vs FAIL (run in a child pytest so the real fixture decides): no PostgreSQL binaries at all => SKIPPED with a visible reason;
    binaries that exist but a cluster that will not start => ERROR carrying the pg_ctl log tail, NEVER a skip.
  * CLEANUP: a stopped cluster is gone (directory removed, port closed); a failed start leaves no temp dir behind.
"""
from __future__ import annotations

import os
import pathlib
import re
import socket
import stat
import subprocess
import sys
import tempfile

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import _disposable_pg as dpg  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

_ORIG_ENV = dict(os.environ)                                       # captured BEFORE any fixture scrubs PG*/DATABASE_URL


def _env_configured_ports() -> set[int]:
    ports = {5432, 55432}
    for k, v in _ORIG_ENV.items():
        if k == "PGPORT" and v.isdigit():
            ports.add(int(v))
        for m in re.finditer(r"postgres(?:ql)?://[^\s/@]*@?[^\s/:@]+:(\d+)", v or ""):
            ports.add(int(m.group(1)))
    return ports


# ───────────────────────── the canary ─────────────────────────

def test_CANARY_the_cluster_is_our_own_loopback_temp_cluster_and_nothing_else(disposable_pg, monkeypatch):
    point_psql_at(disposable_pg, monkeypatch)
    addr, port, data, db = ac.psql("SELECT host(inet_server_addr()), inet_server_port()::text, current_setting('data_directory'), "
                                   "current_database()")[0]
    assert addr == "127.0.0.1", f"not loopback: {addr!r}"
    assert int(port) == disposable_pg.port, "the server we reached is not the one the fixture started"
    assert int(port) not in _env_configured_ports(), f"port {port} is 5432 / 55432 / env-configured: refusing to run against it"
    root = os.path.realpath(str(disposable_pg.root))
    assert os.path.realpath(data) == os.path.join(root, "data") and os.path.basename(root).startswith("suvarna_pg_"), \
        f"data_directory {data!r} is not inside the fixture's own temp dir {root!r}"
    assert db == disposable_pg.dbname == "suvarna_disposable"
    assert pathlib.Path(root).is_dir() and disposable_pg.url.startswith("postgresql://suvarna_disposable@127.0.0.1:")
    stray = [k for k in os.environ if (k.startswith("PG") or k in ("DATABASE_URL", "POSTGRES_URL")) and k not in disposable_pg.env()]
    assert not stray, f"inherited {stray} still reach the census psql()"


def test_the_cluster_listens_on_loopback_only(disposable_pg):
    out = disposable_pg.psql("SHOW listen_addresses")
    assert out == "127.0.0.1"
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", disposable_pg.port))                # reachable on loopback ...
    finally:
        s.close()


def test_verify_own_cluster_refuses_a_cluster_whose_data_directory_is_not_its_own(disposable_pg, tmp_path):
    imposter = dpg.Cluster(disposable_pg.bin_dir, tmp_path, disposable_pg.port)                 # same server, but a root that is not its own
    with pytest.raises(dpg.PGStartError, match="refusing"):
        dpg.verify_own_cluster(imposter)
    dpg.verify_own_cluster(disposable_pg)                                                         # the real one passes


@pytest.mark.parametrize("ident, ok", [
    ("{data}|127.0.0.1|{port}|suvarna_disposable", True),
    ("{data}|10.0.0.5|{port}|suvarna_disposable", False),            # not loopback
    ("{data}||{port}|suvarna_disposable", False),                    # a unix-socket connection reports no address
    ("{data}|127.0.0.1|5432|suvarna_disposable", False),             # another server's port
    ("/var/lib/postgresql/data|127.0.0.1|{port}|suvarna_disposable", False),   # not our data directory
    ("{data}|127.0.0.1|{port}|postgres", False),                     # not our database
])
def test_verify_own_cluster_checks_address_port_data_directory_and_database(disposable_pg, monkeypatch, ident, ok):
    line = ident.format(data=disposable_pg.data_dir, port=disposable_pg.port)
    monkeypatch.setattr(dpg.Cluster, "psql", lambda self, sql, db=None: line)
    if ok:
        dpg.verify_own_cluster(disposable_pg)
    else:
        with pytest.raises(dpg.PGStartError, match="refusing"):
            dpg.verify_own_cluster(disposable_pg)


def test_a_free_port_is_never_a_forbidden_one(monkeypatch):
    seq = iter([5432, 55432, 40001, 40002])

    class Fake:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def bind(self, addr): pass
        def getsockname(self): return ("127.0.0.1", next(seq))
    monkeypatch.setattr(dpg.socket, "socket", lambda *a, **k: Fake())
    monkeypatch.delenv("PGPORT", raising=False)
    assert dpg._free_port() == 40001
    monkeypatch.setenv("PGPORT", "40002")
    seq2 = iter([40002, 40003])
    Fake.getsockname = lambda self: ("127.0.0.1", next(seq2))
    assert dpg._free_port() == 40003


# ───────────────────────── discovery ─────────────────────────

def _fake_bin(d: pathlib.Path, **scripts):
    d.mkdir(parents=True, exist_ok=True)
    for name, body in scripts.items():
        f = d / name
        f.write_text("#!/bin/sh\n" + body + "\n")
        f.chmod(f.stat().st_mode | stat.S_IXUSR)
    return d


def test_find_bin_dir_needs_both_initdb_and_pg_ctl(tmp_path):
    only_initdb = _fake_bin(tmp_path / "a", initdb="exit 0")
    both = _fake_bin(tmp_path / "b", initdb="exit 0", pg_ctl="exit 0")
    assert dpg.find_bin_dir([]) is None
    assert dpg.find_bin_dir([tmp_path / "missing", only_initdb]) is None
    assert dpg.find_bin_dir([only_initdb, both]) == both
    dpg.find_bin_dir()                                                                              # the real discovery runs without raising


def test_candidates_cover_the_ci_runner_and_homebrew_layouts(monkeypatch):
    monkeypatch.setenv("SUVARNA_PG_BIN", "/x/override")
    c = [str(p) for p in dpg.candidate_bin_dirs()]
    assert c[0] == "/x/override" and "/opt/homebrew/bin" in c
    import glob as _glob
    monkeypatch.setattr(dpg.glob, "glob", lambda pat: {"/usr/lib/postgresql/*/bin": ["/usr/lib/postgresql/14/bin", "/usr/lib/postgresql/16/bin"]}.get(pat, []))
    c = [str(p) for p in dpg.candidate_bin_dirs()]
    assert c.index("/usr/lib/postgresql/16/bin") < c.index("/usr/lib/postgresql/14/bin")            # newest first


# ───────────────────────── skip vs fail, through the REAL fixture in a child pytest ─────────────────────────

CHILD = '''
import sys
sys.path.insert(0, {tests!r})
import _disposable_pg as p
p.candidate_bin_dirs = lambda: {cands!r}
from _disposable_pg import disposable_pg

def test_needs_postgres(disposable_pg):
    raise AssertionError("the body must not run when the fixture skips or errors")
'''


def _child(tmp_path, cands):
    f = tmp_path / "test_child.py"
    f.write_text(CHILD.format(tests=str(HERE), cands=[str(c) for c in cands]))
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTEST")}
    return subprocess.run([sys.executable, "-m", "pytest", str(f), "-q", "--no-header", "-p", "no:cacheprovider", "-rsE"],
                          capture_output=True, text=True, env=env, timeout=240, cwd=str(tmp_path))


def test_no_binaries_at_all_SKIPS_with_a_visible_reason(tmp_path):
    r = _child(tmp_path, [tmp_path / "nothing-here"])
    out = r.stdout + r.stderr
    assert r.returncode == 0 and "1 skipped" in out and "no PostgreSQL server binaries" in out, out[-1500:]
    assert "error" not in out.lower().replace("0 errors", "")


def test_binaries_that_exist_but_initdb_fails_is_a_LOUD_error_never_a_skip(tmp_path):
    bd = _fake_bin(tmp_path / "bin", initdb='echo "initdb: cannot create the cluster (boom-initdb)" >&2; exit 1', pg_ctl="exit 0", psql="exit 0")
    r = _child(tmp_path, [bd])
    out = r.stdout + r.stderr
    assert r.returncode != 0 and "skipped" not in out and "boom-initdb" in out and "1 error" in out, out[-1500:]


def test_binaries_that_exist_but_the_cluster_will_not_start_is_a_LOUD_error_with_the_log_tail(tmp_path):
    bd = _fake_bin(tmp_path / "bin",
                   initdb='while [ $# -gt 0 ]; do [ "$1" = "-D" ] && mkdir -p "$2"; shift; done; exit 0',
                   pg_ctl='while [ $# -gt 0 ]; do [ "$1" = "-l" ] && LOG="$2"; shift; done; echo "FATAL:  boom-pgctl-log-line" > "$LOG"; exit 1',
                   psql="exit 0")
    before = set(pathlib.Path(dpg._short_tmp()).glob("suvarna_pg_*"))
    r = _child(tmp_path, [bd])
    out = r.stdout + r.stderr
    assert r.returncode != 0 and "skipped" not in out and "boom-pgctl-log-line" in out and "1 error" in out, out[-1500:]
    assert set(pathlib.Path(dpg._short_tmp()).glob("suvarna_pg_*")) == before, "a failed start left its temp dir behind"


def test_start_cluster_with_a_broken_pg_ctl_raises_PGStartError_in_process_and_cleans_up(tmp_path):
    bd = _fake_bin(tmp_path / "bin", initdb='while [ $# -gt 0 ]; do [ "$1" = "-D" ] && mkdir -p "$2"; shift; done; exit 0',
                   pg_ctl='while [ $# -gt 0 ]; do [ "$1" = "-l" ] && LOG="$2"; shift; done; echo "FATAL:  boom-in-process" > "$LOG"; exit 1', psql="exit 0")
    before = set(pathlib.Path(dpg._short_tmp()).glob("suvarna_pg_*"))
    with pytest.raises(dpg.PGStartError, match="boom-in-process"):
        dpg.start_cluster(bd)
    assert set(pathlib.Path(dpg._short_tmp()).glob("suvarna_pg_*")) == before


# ───────────────────────── cleanup ─────────────────────────

def test_a_stopped_cluster_is_gone_directory_removed_and_port_closed(disposable_pg):
    second = dpg.start_cluster(disposable_pg.bin_dir)                 # a second throw-away cluster, stopped right away
    root, port = second.root, second.port
    assert root.is_dir() and second.psql("SELECT 1") == "1"
    second.stop()
    assert not root.exists()
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=1).close()
    second.stop()                                                      # idempotent
