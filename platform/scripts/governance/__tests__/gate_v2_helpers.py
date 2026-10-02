"""GATE_V2 test helpers and fixtures (import the fixtures `world` and `staged` from here): PATH shims for gh and psql, a fake pgenv file, a minimal environment. No network, no database, no credential.

The shim `gh` emulates `gh run list [-R repo] ... --limit N [--status S] [--branch B] --json ...` from files in FAKE_DIR (it honours
--limit by truncating, so a gate that asks for a short history really misses a deep run, and --branch by filtering on an entry's
optional `headBranch`; it logs the call and which repo-redirecting variables it sees). The shim `psql` prints
`<PGUSER as seen after sourcing>|<PGDATABASE as seen after sourcing>|<count>` unless psql.raw is given. The real /bin/bash runs the real `source`.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

# single source of truth for the gate files: exec/gate_v2/ (repo-relative); only the tests live here, under the CI-collected folder
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE_DIR = REPO_ROOT / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec" / "gate_v2"
GATE = GATE_DIR / "prerun_gate.py"

GH_SHIM = '''#!%(py)s
import json, os, sys, time
args = sys.argv[1:]
d = os.environ["FAKE_DIR"]
open(os.path.join(d, "calls.log"), "a").write("gh " + " ".join(args) + "\\n")
open(os.path.join(d, "calls.log"), "a").write("ghenv " + " ".join("%%s=%%s" %% (n, os.environ.get(n, "unset")) for n in ("GH_REPO", "GH_HOST", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GITHUB_REPOSITORY")) + " token=" + ("present" if os.environ.get("GH_" + "TOKEN") else "absent") + "\\n")
key, limit, branch = "history", None, None
for i, a in enumerate(args):
    if a == "--status":
        key = "status_" + args[i + 1]
    if a == "--limit":
        limit = int(args[i + 1])
    if a == "--branch":
        branch = args[i + 1]
def f(ext):
    return os.path.join(d, "gh_%%s.%%s" %% (key, ext))
if os.path.exists(f("sleep")):
    time.sleep(float(open(f("sleep")).read()))
if os.path.exists(f("rawb")):
    sys.stdout.buffer.write(open(f("rawb"), "rb").read())
elif os.path.exists(f("raw")):
    sys.stdout.write(open(f("raw")).read())
elif os.path.exists(f("json")):
    data = json.load(open(f("json")))
    if branch is not None:
        data = [x for x in data if x.get("headBranch", branch) == branch]
    sys.stdout.write(json.dumps(data[:limit] if limit is not None else data))
sys.exit(int(open(f("rc")).read()) if os.path.exists(f("rc")) else 0)
'''

PSQL_SHIM = '''#!/bin/sh
d="$FAKE_DIR"
echo "psql $*" >> "$d/calls.log"
echo "env PGUSER=${PGUSER-unset} PGHOST=${PGHOST-unset} PGDATABASE=${PGDATABASE-unset}" >> "$d/calls.log"
if [ -f "$d/psql.sleep" ]; then exec sleep "$(cat "$d/psql.sleep")"; fi
if [ -f "$d/psql.raw" ]; then cat "$d/psql.raw"; elif [ -f "$d/psql.rawb" ]; then cat "$d/psql.rawb"; else printf '%s|%s|%s\\n' "${PGUSER:-none}" "${PGDATABASE:-none}" "$(cat "$d/psql.count")"; fi
if [ -f "$d/psql.rc" ]; then exit "$(cat "$d/psql.rc")"; fi
exit 0
'''

PGENV_OK = "export PGHOST=127.0.0.1\nexport PGUSER=suvarna_reader\nexport PGDATABASE=amjis\nexport GATE_CANARY_VALUE=sekrit-must-never-print\n"


def runs(n, status="completed", start=1000, event="workflow_run", **extra):
    return [dict({"databaseId": start + i, "status": status, "event": event}, **extra) for i in range(n)]


class World:
    def __init__(self, tmp):
        self.tmp = tmp
        self.bin = tmp / "bin"
        self.dir = tmp / "fake"
        self.home = tmp / "home"
        for p in (self.bin, self.dir, self.home / ".config" / "suvarna"):
            p.mkdir(parents=True)
        (self.bin / "gh").write_text(GH_SHIM % {"py": sys.executable})
        (self.bin / "psql").write_text(PSQL_SHIM)
        for n in ("gh", "psql"):
            (self.bin / n).chmod(0o755)
        self.tools = tmp / "tools"                                           # python3 + bash by absolute symlink: no homebrew, no macOS paths
        self.tools.mkdir()
        (self.tools / "python3").symlink_to(sys.executable)
        (self.tools / "bash").symlink_to("/bin/bash")
        self.pgenv = tmp / "pgenv.sh"
        self.pgenv.write_text(PGENV_OK)
        self.gh(history=runs(3))
        self.psql(count=0)

    # --- shim control
    def gh(self, history=None, statuses=None, raw=None, rc=None, sleep=None, raw_status=None, raw_bytes=None):
        """history: list for the plain query; statuses: {status: list}; raw: raw stdout of the plain query; rc/sleep: dict key->value;
        raw_bytes: {key: bytes} written verbatim (key = history or status_<s>)"""
        for p in self.dir.glob("gh_*"):
            p.unlink()
        if history is not None:
            (self.dir / "gh_history.json").write_text(json.dumps(history))
        if raw is not None:
            (self.dir / "gh_history.raw").write_text(raw)
        for s in ("queued", "in_progress", "waiting", "pending", "requested"):
            data = (statuses or {}).get(s, [])
            (self.dir / ("gh_status_%s.json" % s)).write_text(json.dumps(data))
        for s, raw_s in (raw_status or {}).items():
            (self.dir / ("gh_status_%s.raw" % s)).write_text(raw_s)
        for key, v in (raw_bytes or {}).items():
            (self.dir / ("gh_%s.rawb" % key)).write_bytes(v)
        for key, v in (rc or {}).items():
            (self.dir / ("gh_%s.rc" % key)).write_text(str(v))
        for key, v in (sleep or {}).items():
            (self.dir / ("gh_%s.sleep" % key)).write_text(str(v))

    def psql(self, count=None, raw=None, rc=None, sleep=None, raw_bytes=None):
        for n in ("psql.count", "psql.raw", "psql.rawb", "psql.rc", "psql.sleep"):
            (self.dir / n).unlink(missing_ok=True)
        if raw_bytes is not None:
            (self.dir / "psql.rawb").write_bytes(raw_bytes)
        if count is not None:
            (self.dir / "psql.count").write_text(str(count))
        if raw is not None:
            (self.dir / "psql.raw").write_text(raw)
        if rc is not None:
            (self.dir / "psql.rc").write_text(str(rc))
        if sleep is not None:
            (self.dir / "psql.sleep").write_text(str(sleep))

    def calls(self):
        p = self.dir / "calls.log"
        return p.read_text() if p.exists() else ""

    # --- environments
    def env(self, **extra):
        """minimal env, test harness bypass on (GATE_V2_UNDER_TEST=1) with the fake pgenv; no inherited PG*/test variables"""
        e = {"PATH": os.pathsep.join([str(self.bin), str(self.tools), "/usr/bin", "/bin"]), "HOME": str(self.home),
             "FAKE_DIR": str(self.dir), "GATE_V2_UNDER_TEST": "1", "GATE_V2_PGENV": str(self.pgenv), "GATE_V2_TIMEOUT_S": "60"}
        e.update(extra)
        return {k: v for k, v in e.items() if v is not None}

    def operator_env(self, **extra):
        """what an operator has: NO test bypass, the production pgenv path under HOME"""
        e = self.env(**extra)
        for k in ("GATE_V2_UNDER_TEST", "GATE_V2_PGENV", "GATE_V2_TIMEOUT_S"):
            e.pop(k, None)
        e.update({k: v for k, v in extra.items() if v is not None})
        return e


def run_gate(env, gate=GATE):
    return subprocess.run([sys.executable, str(gate)], capture_output=True, text=True, env=env, timeout=120)


@pytest.fixture()
def world(tmp_path):
    return World(tmp_path)


@pytest.fixture()
def staged(tmp_path):
    """run_gated.sh + gate + standards copied next to a STUB target, so a real executor can never start in a test"""
    d = tmp_path / "stage"
    d.mkdir()
    for f in ("run_gated.sh", "prerun_gate.py", "executor_standards.py"):
        shutil.copy(GATE_DIR / f, d / f)
    stub = d / "stub_target.py"
    stub.write_text("#!%s\nimport json, os, pathlib, sys\n"
                    "pathlib.Path(__file__).with_name('ran.json').write_text(json.dumps({'argv': sys.argv[1:], 'launch': os.environ.get('GATE_V2_LAUNCH')}))\n"
                    "sys.stdout.write(json.dumps(sys.argv[1:]))\n" % sys.executable)
    stub.chmod(0o755)
    return d
