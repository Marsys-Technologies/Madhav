"""local_db.sh v2.0 (KV3-B-LOCALDB; relaunch plan v2.7 §3, §4a.2, §5 Slot DBs; KU-02): session-bound slot databases.

Hermetic: docker, psql, pg_dump and the migration runner are fakes reached through the script's KY_* overrides, the
settings file is a fake, every path lives under pytest's tmp_path, and the PATH of every invocation starts with
tripwires that fail the test if a real tool name is ever resolved. No container or database is started.

What each fake does is recorded in a call log; the tests read that log, so "nothing called" and "no stop, rm or
rename" are observations of what the script asked for, not of its exit code."""
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
SCRIPT = FLEET / "local_db.sh"

IMAGE = "pgvector/pgvector:pg16"
PGDATA = "/var/lib/postgresql/data"
LIVE_RUN = "/Users/Dev/kalayantra/run"
REAL_PGENV = "/Users/Dev/.config/pravaha/pgenv.sh"
FAKE_SECRET = "s3cr3t-Zq9-fixture"
LEAK_MARKS = ("postgresql://", "postgres://", "PGPASSWORD", "DATABASE_URL", ":postgres@", FAKE_SECRET)
RECEIPT_KEYS = {"schema", "slot", "database", "result", "reason", "session_id", "container", "mount_source", "seed",
                "runner_rc", "tables", "kala_tables", "ledger", "unexpected_restore_errors", "tools", "ts"}
BAD_SESSIONS = ["", "..", "a..b", "a/b", "/abs", "a'b", 'a"b', "-a", ".a", "a b", "a\nb", "a" * 65, "a;b", "a$b"]

# One program plays every external tool; the name it is started under selects the part. State lives in world.json,
# every call is appended to calls.jsonl with the names (never the values) of the connection variables it was given.
FAKE_SRC = r'''
import hashlib, json, os, re, shutil, sys
HOME = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.join(HOME, "world.json"); CALLS = os.path.join(HOME, "calls.jsonl")
PGDATA = "/var/lib/postgresql/data"
NINE = (['ERROR:  schema "public" already exists']
        + ['ERROR:  type "public.planner_managed_prashna_jobs" does not exist'] * 6
        + ['ERROR:  type "public.planner_inquiry_lifecycles" does not exist'] * 2)

def load():
    with open(WORLD) as f: return json.load(f)
def save(w):
    with open(WORLD + ".tmp", "w") as f: json.dump(w, f)
    os.replace(WORLD + ".tmp", WORLD)
def log(tool, argv):
    rec = {"tool": tool, "argv": argv, "cwd": os.getcwd(), "has_PGPASSWORD": "PGPASSWORD" in os.environ,
           "has_DATABASE_URL": "DATABASE_URL" in os.environ, "PGHOST": os.environ.get("PGHOST"),
           "MIGRATE_APPLY_PROTECTED": os.environ.get("MIGRATE_APPLY_PROTECTED")}
    with open(CALLS, "a") as f: f.write(json.dumps(rec) + "\n")
def die(rc, msg):
    sys.stderr.write(msg + "\n"); sys.exit(rc)

def docker(argv, w):
    m = w["modes"]
    if m.get("docker_down"): die(1, "Cannot connect to the Docker daemon")
    verb, rest, c = (argv[0] if argv else ""), argv[1:], w["container"]
    if verb == "ps":
        if "-a" not in rest or "name=^/ky-pg$" not in rest: die(64, "fake docker: unexpected ps " + repr(rest))
        if c and c.get("removing"):
            if m.get("removal_polls", 0) == 0:
                w["container"] = c = None; w["dbs"] = {}
            else:
                m["removal_polls"] -= 1
            save(w)
        elif not c and m.get("cleanup_polls"):
            m["cleanup_polls"] -= 1
            if m["cleanup_polls"] == 0:
                shutil.rmtree(m["cleanup_storage"])
                os.unlink(m["cleanup_record"])
            save(w)
        if m.get("hide_removing") and c and c.get("removing"): return 0
        if c: print(c["id"])
        return 0
    if verb == "inspect":
        if not c or rest[-1] not in (c["id"], "ky-pg"): die(1, "Error: No such object")
        print(json.dumps({"Id": c["id"], "Name": "/ky-pg", "State": {"Running": c["running"],
                          "Status": "removing" if c.get("removing") else ("running" if c["running"] else "exited")},
                          "Config": {"Image": c["image"], "Labels": c["labels"], "Env": ["POSTGRES_PASSWORD=postgres"]},
                          "HostConfig": {"PortBindings": c["ports"]}, "Mounts": c["mounts"]}))
        return 0
    if verb == "run":
        if c: die(125, 'Conflict. The container name "/ky-pg" is already in use')
        if m.get("run_fail"): die(125, "fake docker: run failed")
        labels, ports, mounts, i, image = {}, {}, [], 0, None
        while i < len(rest):
            a = rest[i]
            if a == "-d": i += 1
            elif a == "--name": i += 2
            elif a == "--label": k, v = rest[i + 1].split("=", 1); labels[k] = v; i += 2
            elif a == "-e": i += 2
            elif a == "-p":
                ip, host, cont = rest[i + 1].split(":"); ports[cont + "/tcp"] = [{"HostIp": ip, "HostPort": host}]; i += 2
            elif a == "--mount":
                kv = dict(p.split("=", 1) for p in rest[i + 1].split(","))
                if not os.path.isdir(kv["source"]): die(125, "bind source path does not exist")
                mounts.append({"Type": kv["type"], "Source": kv["source"], "Destination": kv["target"]}); i += 2
            elif a.startswith("-"): die(64, "fake docker: unexpected run option " + a)
            else: image = a; i += 1
        if not any(x["Destination"] == PGDATA for x in mounts):   # the image declares a VOLUME: no mount = anonymous volume
            mounts.append({"Type": "volume", "Name": "f" * 64, "Source": "/var/lib/docker/volumes/x/_data", "Destination": PGDATA})
        w["serial"] += 1
        cid = hashlib.sha256(str(w["serial"]).encode()).hexdigest()
        w["container"] = {"id": cid, "image": image, "labels": labels, "ports": ports, "mounts": mounts, "running": True}
        for x in mounts:
            if x["Type"] == "bind":
                with open(os.path.join(x["Source"], "PG_VERSION"), "w") as f: f.write("16\n")
        save(w); print(cid); return 0
    if verb in ("start", "stop", "rm"):
        if not c or rest[-1] not in (c["id"], "ky-pg"): die(1, "Error: No such container")
        if verb == "start":
            if m.get("start_fail"): die(1, "fake docker: cannot start")
            c["running"] = True
        elif verb == "stop":
            if m.get("stop_fail"): die(1, "fake docker: cannot stop")
            c["running"] = False
        else:
            if m.get("rm_fail"): die(1, "fake docker: cannot remove")
            if m.get("rm_noop"): return 0
            if c["running"] and "-f" not in rest: die(1, "cannot remove a running container")
            if m.get("rm_delay"):
                c["removing"] = True; save(w); return 0
            w["container"] = None; w["dbs"] = {}
        save(w); return 0
    die(64, "fake docker: unsupported verb " + verb)

def psql(argv, w):
    m, c = w["modes"], w["container"]
    opts, cmds, files, sep, i = {}, [], [], "|", 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "-p", "-U", "-d", "-v"): opts[a] = argv[i + 1]; i += 2
        elif a == "-F": sep = argv[i + 1]; i += 2
        elif a == "-c": cmds.append(argv[i + 1]); i += 2
        elif a == "-f": files.append(argv[i + 1]); i += 2
        elif re.fullmatch(r"-[XqtA]+", a): i += 1
        else: die(64, "fake psql: unexpected argument " + a)
    if m.get("psql_down") or not c or not c["running"]: die(2, "psql: error: connection refused")
    if c["ports"].get("5432/tcp", [{}])[0].get("HostPort") != opts.get("-p"): die(2, "psql: error: connection refused")
    dbs, d = w["dbs"], opts.get("-d", "postgres")
    if d != "postgres" and d not in dbs: die(2, 'psql: error: FATAL:  database "%s" does not exist' % d)
    for sql in cmds:
        s = " ".join(sql.split())
        if re.fullmatch(r"select 1;?", s, re.I): print(1)
        elif "pg_database d where" in s and s.lower().startswith("select"):
            if m.get("list_fail"): die(2, "psql: error: connection lost")
            for name in sorted(dbs): print(name + sep + dbs[name]["comment"])
        elif re.match(r'CREATE DATABASE "?(\w+)"?;?$', s):
            name = re.match(r'CREATE DATABASE "?(\w+)"?;?$', s).group(1)
            if name in dbs or m.get("create_fail"): die(1, "ERROR:  cannot create database")
            dbs[name] = {"comment": "", "loaded": [], "tables": 0, "kala": 0, "ledger": None, "registry_ok": False}
        elif re.match(r'COMMENT ON DATABASE "?(\w+)"? IS \'(.*)\';?$', s):
            g = re.match(r'COMMENT ON DATABASE "?(\w+)"? IS \'(.*)\';?$', s)
            if m.get("comment_fail"): die(1, "ERROR:  cannot comment")
            dbs[g.group(1)]["comment"] = g.group(2)
        elif re.match(r'DROP DATABASE IF EXISTS "(.+)" WITH \(FORCE\);?$', s):
            name = re.match(r'DROP DATABASE IF EXISTS "(.+)" WITH \(FORCE\);?$', s).group(1)
            if not m.get("drop_noop"): dbs.pop(name.replace('""', '"'), None)
        elif s.startswith("CREATE EXTENSION") or s.startswith("DO "): pass
        elif "from pg_tables" in s:
            if m.get("count_fail"): die(1, "ERROR:  count unavailable")
            print(dbs[d]["kala"] if "kala_" in s else dbs[d]["tables"])
        elif "from _migrations_applied" in s:
            if dbs[d]["ledger"] is None: die(1, 'ERROR:  relation "_migrations_applied" does not exist')
            print(dbs[d]["ledger"])
        else: die(3, "fake psql: unknown sql: " + s)
        save(w)
    for path in files:
        name = os.path.basename(path)
        with open(path) as f: text = f.read()
        dbs[d]["loaded"].append(name)
        if name == "prod_schema.sql":
            if m.get("restore_crash"): save(w); die(2, "psql: error: connection to server was lost")
            dbs[d]["tables"], dbs[d]["kala"] = m.get("tables", 450), m.get("kala", 80)
            for line in NINE + m.get("extra_errors", []): sys.stderr.write("psql:%s:1: %s\n" % (path, line))
        elif name == "migrations_applied_data.sql": dbs[d]["ledger"] = m.get("ledger", 950)
        elif name == "asset_registry_data.sql": dbs[d]["registry_ok"] = "bg_transit_rules" in text
        save(w)
    return 0

def npx(argv, w):
    if argv != ["tsx", "scripts/migrate.ts"]: die(64, "fake npx: unexpected " + repr(argv))
    name = os.environ.get("DATABASE_URL", "").rsplit("/", 1)[-1]
    if "runner_rc" in w["modes"]: die(w["modes"]["runner_rc"], "fake runner: forced exit")
    if w["modes"].get("runner_prints_url"): print("connecting to " + os.environ.get("DATABASE_URL", ""))
    if name not in w["dbs"]: die(1, "fake runner: no such database")
    if not w["dbs"][name]["registry_ok"]:
        die(1, "migration 1320 refused: asset_registry holds no bg_transit_rules row")
    w["dbs"][name]["ledger"] += 5; save(w); print("migrations applied"); return 0

def pg_dump(argv, w):
    m = w["modes"]
    if os.environ.get("PGHOST") != "fake-prod.invalid": die(9, "fake pg_dump: the settings file was not applied")
    out = argv[argv.index("-f") + 1]
    excluded = [argv[i + 1] for i, a in enumerate(argv) if a == "-T"]
    if "--schema-only" in argv:
        for t in m.get("deny", []):
            if "public." + t not in excluded: die(1, "pg_dump: error: permission denied for table " + t)
        text = "CREATE TABLE public.a ();\nCREATE TABLE public.b ();\n"
    elif "public._migrations_applied" in argv: text = "COPY public._migrations_applied FROM stdin;\n1\n\\.\n"
    elif "public.asset_registry" in argv:
        mode = m.get("registry_dump", "ok")
        if mode == "error": die(1, "pg_dump: error: permission denied for table asset_registry")
        if mode == "missing": return 0
        text = "" if mode == "empty" else "COPY public.asset_registry FROM stdin;\nbg_transit_rules\n\\.\n"
    else: die(64, "fake pg_dump: unexpected " + repr(argv))
    with open(out, "w") as f: f.write(text)
    return 0

def main():
    tool, argv = os.path.basename(sys.argv[0]), sys.argv[1:]
    log(tool, argv)
    sys.exit({"docker": docker, "psql": psql, "npx": npx, "pg_dump": pg_dump}[tool](argv, load()))
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def find_leaks(text):
    """The marks a string must never hold: a connection string, a credential variable's name, a password."""
    return [m for m in LEAK_MARKS if m in text]


def split_trace(stderr):
    """`bash -x` output with PS4='+KYX ' → (trace lines, everything else)."""
    trace, rest = [], []
    for line in stderr.splitlines():
        (trace if re.match(r"\++KYX ", line) else rest).append(line)
    return trace, "\n".join(rest)


def sourced_paths(trace):
    """Every file a traced run handed to `source` or `.`."""
    out = []
    for line in trace:
        m = re.match(r"\++KYX (?:source|\.) (\S+)", line)
        if m:
            out.append(m.group(1).strip("'\""))
    return out


def assert_settings_path_unopened(trace, real):
    """The watched path may be named by the one assignment that defines the default, and by nothing that runs."""
    assert real not in sourced_paths(trace), f"the settings path {real} was opened"
    handled = [line for line in trace if real in line and not re.fullmatch(r"\++KYX REAL_PGENV=" + re.escape(real), line)]
    assert not handled, f"the settings path {real} was handled: {handled}"


def mutating(calls):
    """Calls that change something: any docker verb but ps/inspect, any psql file or non-select, the runner, a dump."""
    out = []
    for c in calls:
        a = c["argv"]
        if c["tool"] == "docker":
            if not a or a[0] not in ("ps", "inspect"):
                out.append(c)
        elif c["tool"] == "psql":
            sql = [a[i + 1] for i, x in enumerate(a) if x == "-c"]
            if "-f" in a or any(not s.lstrip().lower().startswith("select") for s in sql):
                out.append(c)
        else:
            out.append(c)
    return out


def docker_verbs(calls):
    return [c["argv"][0] for c in calls if c["tool"] == "docker" and c["argv"]]


class Lab:
    def __init__(self, tmp):
        self.tmp = tmp
        self.fake = tmp / "fake"
        self.run_dir = tmp / "run"
        self.scratch_real = tmp / "scratch_real"
        self.scratch = tmp / "scratch"          # a symlink: R must be the realpath, never the name given
        self.repo = tmp / "repo"
        self.pgenv = tmp / "pgenv.sh"
        self.trip = tmp / "tripwires"
        self.shims = tmp / "shims"
        self.outputs = []
        self.traces = []
        self.expect_tripwire = False
        for d in (self.fake, self.run_dir, self.scratch_real, self.repo / "platform" / "scripts", self.trip,
                  self.shims, tmp / "home"):
            d.mkdir(parents=True)
        self.scratch.symlink_to(self.scratch_real)
        self.R = Path(os.path.realpath(self.scratch))
        (self.repo / "platform" / "scripts" / "migrate.ts").write_text("// fixture\n")
        (self.fake / "fakeworld.py").write_text(FAKE_SRC)
        for tool in ("docker", "psql", "pg_dump", "npx"):
            self._exe(self.fake / tool, f"#!{sys.executable} -B\nimport sys\nsys.path.insert(0, {str(self.fake)!r})\n"
                                        "import fakeworld\nfakeworld.main()\n")
        for tool in ("docker", "psql", "pg_dump", "npx", "launchctl"):
            self._exe(self.trip / tool, f"#!/bin/sh\necho {tool} >> {self.trip}/FIRED\nexit 99\n")
        self._exe(self.shims / "sleep", "#!/bin/sh\nexit 0\n")
        self.pgenv.write_text(f"export PGHOST=fake-prod.invalid\nexport PGPASSWORD={FAKE_SECRET}\n")
        self.world_path = self.fake / "world.json"
        self.calls_path = self.fake / "calls.jsonl"
        self.save({"container": None, "dbs": {}, "modes": {}, "serial": 0})
        self.pools(2, 1)
        self.seed_files()

    @staticmethod
    def _exe(path, text):
        path.write_text(text)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    # ── fixtures ───────────────────────────────────────────────────────────────────────────────────────────────
    def world(self):
        return json.loads(self.world_path.read_text())

    def save(self, w):
        self.world_path.write_text(json.dumps(w))

    def modes(self, **kw):
        w = self.world()
        w["modes"] = kw
        self.save(w)

    def pools(self, workers, verifiers):
        for name, val in (("KY_WORKERS", workers), ("KY_VERIFIERS", verifiers)):
            p = self.run_dir / name
            if val is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_text(f"{val}\n")

    def seed_files(self, registry="COPY public.asset_registry FROM stdin;\nbg_transit_rules\n\\.\n"):
        d = self.run_dir / "schema"
        d.mkdir(exist_ok=True)
        (d / "prod_schema.sql").write_text("CREATE TABLE public.a ();\n")
        (d / "migrations_applied_data.sql").write_text("COPY public._migrations_applied FROM stdin;\n1\n\\.\n")
        if registry is None:
            (d / "asset_registry_data.sql").unlink(missing_ok=True)
        else:
            (d / "asset_registry_data.sql").write_text(registry)

    def plant_container(self, session="OTHER", image=IMAGE, campaign="kalayantra", port="55433", mounts=None,
                        running=True):
        """A ky-pg that exists before the script is asked anything."""
        if mounts is None:
            src = self.R / "db" / session / "pgdata"
            src.mkdir(parents=True, exist_ok=True)
            mounts = [{"Type": "bind", "Source": str(src), "Destination": PGDATA}]
        labels = {"ky.session": session}
        if campaign is not None:
            labels["campaign"] = campaign
        w = self.world()
        w["serial"] += 1
        w["container"] = {"id": hashlib.sha256(f"planted{w['serial']}".encode()).hexdigest(), "image": image,
                          "labels": labels, "ports": {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": port}]},
                          "mounts": mounts, "running": running}
        self.save(w)
        return w["container"]

    def plant_db(self, name, comment):
        w = self.world()
        w["dbs"][name] = {"comment": comment, "loaded": [], "tables": 0, "kala": 0, "ledger": None, "registry_ok": False}
        self.save(w)

    def calls(self):
        if not self.calls_path.exists():
            return []
        return [json.loads(line) for line in self.calls_path.read_text().splitlines()]

    def forget_calls(self):
        self.calls_path.unlink(missing_ok=True)

    def receipt(self, slot):
        return json.loads((self.run_dir / "local_db" / f"{slot}.json").read_text())

    def record_path(self):
        return self.run_dir / "local_db" / "container.json"

    def tree(self):
        """Every path under the run and scratch roots with its size: the 'nothing changed' observation."""
        out = {}
        for root in (self.run_dir, self.scratch_real):
            for p in sorted(root.rglob("*")):
                out[str(p)] = p.stat().st_size if p.is_file() else -1
        return out

    # ── running the script ─────────────────────────────────────────────────────────────────────────────────────
    def env(self, **over):
        e = {"PATH": f"{self.trip}:{self.shims}:/usr/bin:/bin", "HOME": str(self.tmp / "home"),
             "TMPDIR": str(self.tmp), "LANG": "C",
             "KY_ROOT": str(self.tmp / "kyroot"), "KY_RUN": str(self.run_dir), "KY_SCRATCH": str(self.scratch),
             "KY_SOURCE_REPO": str(self.repo), "KY_DOCKER": str(self.fake / "docker"),
             "KY_PSQL": str(self.fake / "psql"), "KY_PG_DUMP": str(self.fake / "pg_dump"),
             "KY_NPX": str(self.fake / "npx"), "KY_PGENV": str(self.pgenv)}
        for k, v in over.items():
            if v is None:
                e.pop(k, None)
            else:
                e[k] = v
        return e

    def run(self, *args, script=SCRIPT, trace=False, live_run=False, **over):
        e = self.env(**over)
        # the harness tripwire: no invocation may leave the settings path to its default, or aim at the live run dir
        pgenv = e.get("KY_PGENV", "")
        if not pgenv or not (pgenv.startswith(str(self.tmp)) or pgenv.startswith("relative")):
            raise AssertionError("real settings path would be opened: KY_PGENV is not a fixture path")
        if not live_run and not e.get("KY_RUN", "").startswith(str(self.tmp)):
            raise AssertionError("KY_RUN is not a fixture path")
        argv = ["/bin/bash"] + (["-x"] if trace else []) + [str(script), *args]
        if trace:
            e["PS4"] = "+KYX "
        p = subprocess.run(argv, env=e, cwd=str(self.tmp), capture_output=True, text=True, timeout=60)
        err = p.stderr
        if trace:
            lines, err = split_trace(p.stderr)
            self.traces.append(lines)
        self.outputs.append((args, p.stdout, err))
        p.err = err
        return p


@pytest.fixture
def lab(tmp_path):
    lab = Lab(tmp_path)
    yield lab
    # suite-wide observations, made after every test
    fired = lab.trip / "FIRED"
    assert fired.exists() == lab.expect_tripwire, "a real tool name was resolved from PATH"
    for args, out, err in lab.outputs:
        assert not find_leaks(out + err), f"{args}: output holds {find_leaks(out + err)}"
    for root in (lab.run_dir, lab.scratch_real):
        for p in root.rglob("*"):
            if p.is_file():
                assert not find_leaks(p.read_text(errors="replace")), f"{p} holds a connection string or password"
    for lines in lab.traces:
        assert_settings_path_unopened(lines, REAL_PGENV)


def ready(lab, slot="b1", session="S1"):
    p = lab.run("db", slot, "--session", session)
    assert p.returncode == 0, p.stdout + p.err
    return lab.receipt(slot)


# ── the detectors have negative fixtures of their own ──────────────────────────────────────────────────────────
def test_leak_detector_flags_a_connection_string_and_a_password():
    assert find_leaks("see postgresql://u:p@h/db") and find_leaks(f"x {FAKE_SECRET} y") and find_leaks("PGPASSWORD=1")
    assert find_leaks("ky_b1 READY: tables=450") == []


def test_mutating_call_detector_separates_reads_from_changes():
    reads = [{"tool": "docker", "argv": ["ps", "-a"]}, {"tool": "docker", "argv": ["inspect", "x"]},
             {"tool": "psql", "argv": ["-At", "-c", "select 1"]}]
    assert mutating(reads) == []
    for change in ({"tool": "docker", "argv": ["start", "x"]}, {"tool": "docker", "argv": ["rename", "a", "b"]},
                   {"tool": "psql", "argv": ["-c", "DROP DATABASE x"]}, {"tool": "psql", "argv": ["-f", "x.sql"]},
                   {"tool": "npx", "argv": ["tsx"]}):
        assert mutating(reads + [change]) == [change]


def test_a_real_tool_name_resolved_from_path_trips_the_wire(lab):
    lab.expect_tripwire = True
    p = lab.run("up", "--session", "S1", KY_DOCKER=None)
    assert p.returncode == 1                      # the tripwire answers 99: docker cannot be observed
    assert (lab.trip / "FIRED").read_text().split() == ["docker"]
    assert lab.calls() == []


def test_harness_refuses_an_invocation_that_would_open_the_real_settings_path(lab):
    with pytest.raises(AssertionError, match="real settings path would be opened"):
        lab.run("seed", KY_PGENV=None)
    with pytest.raises(AssertionError, match="real settings path would be opened"):
        lab.run("seed", KY_PGENV=REAL_PGENV)
    assert lab.calls() == [] and lab.outputs == []


# ── usage, grammar, slots ──────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("args", [[], ["nope"], ["url", "b1"], ["up"], ["up", "S1"], ["db", "b1"], ["db"],
                                  ["reset", "b1"], ["close"], ["check"], ["check", "b1", "extra"],
                                  ["up", "--session", "S1", "extra"], ["slots", "extra"], ["down", "x"]])
def test_usage_errors_exit_64_and_call_nothing(lab, args):
    before = lab.tree()
    p = lab.run(*args)
    assert p.returncode == 64
    assert lab.calls() == [] and lab.tree() == before


@pytest.mark.parametrize("session", BAD_SESSIONS)
@pytest.mark.parametrize("command", [["up"], ["db", "b1"], ["reset", "b1"], ["close"]])
def test_bad_session_is_refused_before_anything_is_called(lab, command, session):
    lab.plant_container(session="S1")
    lab.plant_db("ky_b1", "ky.session=S1")
    before, world = lab.tree(), lab.world()
    p = lab.run(*command, "--session", session)
    assert p.returncode == 2, p.stdout + p.err
    assert lab.calls() == [] and lab.tree() == before and lab.world() == world


@pytest.mark.parametrize("command", [["up"], ["db", "b1"], ["reset", "b1"], ["close"]])
def test_bad_session_is_refused_before_the_environment_is_even_looked_at(lab, command):
    p = lab.run(*command, "--session", "a/b", KY_SCRATCH="relative/never", KY_RUN=str(lab.tmp / "absent-run"))
    assert p.returncode == 2 and "session" in p.err
    assert lab.calls() == [] and not (lab.tmp / "absent-run").exists()


def test_session_flag_without_a_value_is_an_empty_session(lab):
    assert lab.run("close", "--session").returncode == 2
    assert lab.calls() == []


def test_slots_lists_builders_then_verifiers(lab):
    lab.pools(3, 2)
    p = lab.run("slots")
    assert p.returncode == 0 and p.stdout == "b1\nb2\nb3\nv1\nv2\n"
    lab.pools(8, 8)
    assert lab.run("slots").stdout.split() == [f"b{i}" for i in range(1, 9)] + [f"v{i}" for i in range(1, 9)]
    assert lab.calls() == []


@pytest.mark.parametrize("workers,verifiers", [(None, 1), (2, None), (0, 1), (9, 1), (2, 0), (2, 9), ("x", 1),
                                               ("", 1), ("2 3", 1), ("-1", 1), ("1.5", 1), ("02", 1)])
def test_slots_unknown_pool_exits_1_with_no_output(lab, workers, verifiers):
    lab.pools(workers, verifiers)
    p = lab.run("slots")
    assert p.returncode == 1 and p.stdout == "" and p.err == ""


def test_slots_unreadable_pool_file_exits_1_with_no_output(lab):
    (lab.run_dir / "KY_WORKERS").unlink()
    (lab.run_dir / "KY_WORKERS").mkdir()
    p = lab.run("slots")
    assert p.returncode == 1 and p.stdout == "" and p.err == ""


@pytest.mark.parametrize("slot", ["b3", "v2", "b9", "x1", "b", "b1;x", "sutradhara", "../b1", ""])
@pytest.mark.parametrize("command", ["db", "reset"])
def test_unconfigured_slot_is_refused_and_nothing_is_called(lab, command, slot):
    before = lab.tree()
    p = lab.run(command, slot, "--session", "S1")       # pools: b1 b2 v1
    assert p.returncode == 2, p.stdout + p.err
    assert lab.calls() == [] and lab.tree() == before


@pytest.mark.parametrize("command", ["db", "reset"])
def test_missing_pool_file_is_refused_and_nothing_is_called(lab, command):
    lab.pools(None, 1)
    before = lab.tree()
    p = lab.run(command, "b1", "--session", "S1")
    assert p.returncode == 2 and lab.calls() == [] and lab.tree() == before


@pytest.mark.parametrize("over", [{"KY_SCRATCH": None}, {"KY_SCRATCH": "relative/dir"}, {"KY_SCRATCH": "/nonexistent/ky"},
                                  {"KY_DOCKER": "docker-relative"}, {"KY_PSQL": "bin/psql"}, {"KY_NPX": "npx"},
                                  {"KY_PG_PORT": "5433x"}, {"KY_PG_PORT": "0"}, {"KY_RUN": "relative/run"}])
@pytest.mark.parametrize("command", [["up", "--session", "S1"], ["db", "b1", "--session", "S1"],
                                     ["close", "--session", "S1"]])
def test_unusable_environment_is_refused_and_nothing_is_called(lab, command, over):
    before = lab.tree()
    p = lab.run(*command, live_run=True, **over)
    assert p.returncode == 2, p.stdout + p.err
    assert lab.calls() == [] and lab.tree() == before


# ── up ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_up_creates_a_labelled_loopback_container_on_a_bind_mount_under_the_scratch_realpath(lab):
    p = lab.run("up", "--session", "S1")
    assert p.returncode == 0, p.stdout + p.err
    c = lab.world()["container"]
    want = str(lab.R / "db" / "S1" / "pgdata")
    assert str(lab.scratch) != str(lab.R) and want.startswith(str(lab.scratch_real))
    assert c["image"] == IMAGE and c["labels"] == {"campaign": "kalayantra", "ky.session": "S1"}
    assert c["ports"] == {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "55433"}]}
    assert c["mounts"] == [{"Type": "bind", "Source": want, "Destination": PGDATA}]
    run = [x for x in lab.calls() if x["tool"] == "docker" and x["argv"][0] == "run"]
    assert len(run) == 1 and "ky-pg" in run[0]["argv"] and "-v" not in run[0]["argv"]
    assert c["id"][:12] in p.stdout and "S1" in p.stdout
    assert not any(x["has_PGPASSWORD"] or x["has_DATABASE_URL"] for x in lab.calls() if x["tool"] == "docker")


def test_up_honours_the_port_override(lab):
    assert lab.run("up", "--session", "S1", KY_PG_PORT="55999").returncode == 0
    assert lab.world()["container"]["ports"]["5432/tcp"][0]["HostPort"] == "55999"
    assert lab.run("up", "--session", "S1").returncode == 2          # the default port no longer matches: not reused


def test_up_reuses_a_compatible_container_of_another_session_and_starts_it_if_stopped(lab):
    c = lab.plant_container(session="OTHER", running=False)
    p = lab.run("up", "--session", "S1")
    assert p.returncode == 0, p.stdout + p.err
    assert docker_verbs(lab.calls()) == ["ps", "inspect", "start"]
    w = lab.world()["container"]
    assert w["id"] == c["id"] and w["running"] and w["labels"]["ky.session"] == "OTHER"
    assert not (lab.R / "db" / "S1").exists()


def wrong_containers(lab):
    outside = lab.tmp / "outside" / "pgdata"
    outside.mkdir(parents=True)
    escape = lab.R / "db" / "LINK"
    escape.parent.mkdir(parents=True, exist_ok=True)
    escape.symlink_to(lab.tmp / "outside")
    inside = lab.R / "db" / "OK" / "pgdata"
    inside.mkdir(parents=True)
    bind = lambda src, dest=PGDATA: {"Type": "bind", "Source": str(src), "Destination": dest}  # noqa: E731
    return {
        "image": {"image": "postgres:16"},
        "campaign_label_absent": {"campaign": None},
        "campaign_label_other": {"campaign": "elsewhere"},
        "port": {"port": "5432"},
        "anonymous_volume": {"mounts": [{"Type": "volume", "Name": "a" * 64, "Source": "/var/lib/docker/volumes/a/_data",
                                         "Destination": PGDATA}]},
        "no_mount": {"mounts": []},
        "out_of_root_bind": {"mounts": [bind(outside)]},
        "bind_through_a_symlink_out_of_root": {"mounts": [bind(escape / "pgdata")]},
        "bind_is_the_scratch_root": {"mounts": [bind(lab.R)]},
        "bind_is_the_db_directory": {"mounts": [bind(lab.R / "db")]},
        "bind_not_at_pgdata": {"mounts": [bind(inside, "/data")]},
        "second_mount_out_of_root": {"mounts": [bind(inside), bind(outside, "/extra")]},
        "second_mount_anonymous": {"mounts": [bind(inside), {"Type": "volume", "Name": "b" * 64, "Source": "/v",
                                                             "Destination": "/extra"}]},
    }


WRONG = ["image", "campaign_label_absent", "campaign_label_other", "port", "anonymous_volume", "no_mount",
         "out_of_root_bind", "bind_through_a_symlink_out_of_root", "bind_is_the_scratch_root",
         "bind_is_the_db_directory", "bind_not_at_pgdata", "second_mount_out_of_root", "second_mount_anonymous"]


@pytest.mark.parametrize("kind", WRONG)
def test_incompatible_container_is_reported_and_preserved_by_every_command(lab, kind):
    """Wrong mount (anonymous volume, out-of-root bind) and its kin: up exit 2, check exit 1; no stop, rm, rename."""
    lab.plant_container(session="S1", **wrong_containers(lab)[kind])
    lab.plant_db("ky_b1", "ky.session=S1")
    world, before = lab.world(), lab.tree()
    up = lab.run("up", "--session", "S1")
    assert up.returncode == 2 and "INCOMPATIBLE" in up.err
    assert lab.run("db", "b1", "--session", "S1").returncode == 2
    assert lab.run("reset", "b1", "--session", "S1").returncode == 2
    assert lab.run("down").returncode == 2
    check = lab.run("check", "b1")
    assert check.returncode == 1 and check.stdout.startswith("ky_b1 STALE: ")
    close = lab.run("close", "--session", "S1")
    assert close.returncode == 0 and close.stdout == "close session=S1 dropped=0 container=incompatible\n"
    assert set(docker_verbs(lab.calls())) == {"ps", "inspect"}       # no stop, rm, rename, start, run
    assert mutating(lab.calls()) == [] and lab.world() == world and lab.tree() == before


def test_wrong_mount_makes_a_ready_slot_stale(lab):
    r = ready(lab)
    w = lab.world()
    outside = lab.tmp / "outside"
    outside.mkdir()
    w["container"]["mounts"] = [{"Type": "bind", "Source": str(outside), "Destination": PGDATA}]
    lab.save(w)
    p = lab.run("check", "b1")
    assert p.returncode == 1 and p.stdout.startswith("ky_b1 STALE: ")
    assert lab.receipt("b1") == r


def test_up_refuses_a_session_directory_that_leaves_the_scratch_root(lab):
    (lab.R / "db").mkdir()
    (lab.tmp / "outside").mkdir()
    (lab.R / "db" / "S1").symlink_to(lab.tmp / "outside")
    p = lab.run("up", "--session", "S1")
    assert p.returncode == 2 and lab.world()["container"] is None
    assert "run" not in docker_verbs(lab.calls()) and list((lab.tmp / "outside").iterdir()) == []


@pytest.mark.parametrize("modes,verbs", [({"docker_down": True}, ["ps"]), ({"run_fail": True}, ["ps", "run"]),
                                         ({"psql_down": True}, ["ps", "run", "ps", "inspect"])])
def test_up_fails_when_docker_or_the_server_cannot_be_observed(lab, modes, verbs):
    lab.modes(**modes)
    p = lab.run("up", "--session", "S1")
    assert p.returncode == 1 and docker_verbs(lab.calls()) == verbs


# ── db: READY is earned in this invocation ─────────────────────────────────────────────────────────────────────
def test_configured_slot_and_complete_seed_are_ready_with_a_bound_receipt(lab):
    p = lab.run("db", "b1", "--session", "S1")
    assert p.returncode == 0, p.stdout + p.err
    assert p.stdout.startswith("ky_b1 READY: ")
    r, w, d = lab.receipt("b1"), lab.world(), lab.run_dir / "schema"
    assert set(r) == RECEIPT_KEYS
    assert (r["schema"], r["slot"], r["database"], r["result"], r["session_id"]) == \
           ("ky.slot_db/1", "b1", "ky_b1", "READY", "S1")
    assert r["container"] == {"name": "ky-pg", "id": w["container"]["id"], "image": IMAGE, "port": 55433}
    assert r["mount_source"] == str(lab.R / "db" / "S1" / "pgdata")
    assert r["seed"] == {"schema_sha256": sha(d / "prod_schema.sql"),
                         "ledger_sha256": sha(d / "migrations_applied_data.sql"),
                         "registry_sha256": sha(d / "asset_registry_data.sql")}
    assert (r["runner_rc"], r["tables"], r["kala_tables"], r["ledger"], r["unexpected_restore_errors"]) == \
           (0, 450, 80, 955, 0)
    assert r["tools"] == {t: str(lab.fake / t) for t in ("docker", "psql", "pg_dump", "npx")}
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", r["ts"])
    db = w["dbs"]["ky_b1"]
    assert db["comment"] == "ky.session=S1"
    assert db["loaded"] == ["prod_schema.sql", "migrations_applied_data.sql", "asset_registry_data.sql"]
    # the connection is given to the script's own children and to nobody else (plan §3)
    calls = lab.calls()
    runner = [c for c in calls if c["tool"] == "npx"]
    assert len(runner) == 1 and runner[0]["has_DATABASE_URL"] and runner[0]["MIGRATE_APPLY_PROTECTED"] == "1"
    assert runner[0]["cwd"] == os.path.realpath(lab.repo / "platform")
    assert all(c["has_PGPASSWORD"] and not c["has_DATABASE_URL"] for c in calls if c["tool"] == "psql")
    assert not any(c["has_PGPASSWORD"] or c["has_DATABASE_URL"] for c in calls if c["tool"] == "docker")
    # logs live under the scratch root, nowhere else
    assert sorted(x.name for x in (lab.R / "db").iterdir()) == ["S1", "_ky_b1.restore.log", "_ky_b1.runner.log"]
    assert lab.run("check", "b1").returncode == 0


def test_1320_runner_refuses_a_registry_seed_lacking_bg_transit_rules(lab):
    """The 1320 prerequisite failure: FAILED, never READY."""
    lab.seed_files(registry="COPY public.asset_registry FROM stdin;\nsome_other_asset\n\\.\n")
    p = lab.run("db", "b1", "--session", "S1")
    assert p.returncode == 1 and p.stdout.startswith("ky_b1 FAILED: ") and "READY" not in p.stdout + p.err
    r = lab.receipt("b1")
    assert r["result"] == "FAILED" and r["runner_rc"] == 1 and "runner" in r["reason"]
    assert "1320" in (lab.R / "db" / "_ky_b1.runner.log").read_text()
    again = lab.run("db", "b1", "--session", "S1")                   # a FAILED receipt is no provenance
    assert again.returncode == 1 and "READY" not in again.stdout
    assert lab.run("check", "b1").returncode == 1


@pytest.mark.parametrize("name", ["prod_schema.sql", "migrations_applied_data.sql", "asset_registry_data.sql"])
@pytest.mark.parametrize("how", ["missing", "empty"])
def test_missing_or_empty_seed_file_fails_the_database(lab, name, how):
    f = lab.run_dir / "schema" / name
    f.unlink() if how == "missing" else f.write_text("")
    p = lab.run("db", "b1", "--session", "S1")
    assert p.returncode == 1 and p.stdout.startswith("ky_b1 FAILED: ") and "READY" not in p.stdout
    assert "ky_b1" not in lab.world()["dbs"]
    assert lab.receipt("b1")["result"] == "FAILED"
    assert lab.run("check", "b1").returncode == 1


@pytest.mark.parametrize("modes,field", [
    ({"extra_errors": ['ERROR:  relation "public.zzz" does not exist']}, "unexpected_restore_errors"),
    ({"tables": 399}, "tables"), ({"kala": 69}, "kala_tables"), ({"ledger": 894}, "ledger"),
    ({"runner_rc": 3}, "runner_rc")])
def test_each_ready_condition_fails_the_database_alone(lab, modes, field):
    lab.modes(**modes)
    p = lab.run("db", "b1", "--session", "S1")
    assert p.returncode == 1 and p.stdout.startswith("ky_b1 FAILED: ")
    r = lab.receipt("b1")
    assert r["result"] == "FAILED"
    assert r[field] == {"unexpected_restore_errors": 1, "tables": 399, "kala_tables": 69, "ledger": 899,
                        "runner_rc": 3}[field]


def test_a_missing_expected_restore_error_is_as_unexpected_as_an_extra_one(lab):
    assert ready(lab)["unexpected_restore_errors"] == 0
    log = lab.R / "db" / "_ky_b1.restore.log"
    log.write_text("\n".join(log.read_text().splitlines()[1:]) + "\n")
    p = lab.run("db", "b1", "--session", "S1")
    assert p.returncode == 1 and lab.receipt("b1")["unexpected_restore_errors"] == 1
    log.unlink()
    p = lab.run("reset", "b1", "--session", "S1")
    assert p.returncode == 0 and lab.receipt("b1")["unexpected_restore_errors"] == 0


def test_an_unobservable_count_is_null_and_failed_never_zero_or_ready(lab):
    lab.modes(count_fail=True)
    p = lab.run("db", "b1", "--session", "S1")
    r = lab.receipt("b1")
    assert p.returncode == 1 and r["result"] == "FAILED" and r["tables"] is None and r["kala_tables"] is None


def test_missing_source_repo_fails_the_runner_and_the_database(lab):
    p = lab.run("db", "b1", "--session", "S1", KY_SOURCE_REPO=str(lab.tmp / "no-repo"))
    r = lab.receipt("b1")
    assert p.returncode == 1 and r["result"] == "FAILED" and r["runner_rc"] not in (0, None)
    assert [c for c in lab.calls() if c["tool"] == "npx"] == []


@pytest.mark.parametrize("modes", [{"restore_crash": True}, {"create_fail": True}, {"comment_fail": True}])
def test_a_broken_restore_leaves_no_ready_receipt(lab, modes):
    ready(lab)
    lab.modes(**modes)
    p = lab.run("reset", "b1", "--session", "S1")
    assert p.returncode == 1 and "READY" not in p.stdout
    assert lab.receipt("b1")["result"] == "FAILED"
    assert lab.run("check", "b1").returncode == 1


def test_the_receipt_is_removed_before_a_restore_starts(lab):
    ready(lab)
    lab.modes(restore_crash=True)
    shim = lab.tmp / "psql_spy"
    lab._exe(shim, f"#!/bin/sh\ncase \" $* \" in *prod_schema.sql*) ls {lab.run_dir}/local_db > {lab.tmp}/at_restore;; esac\n"
                   f"exec {lab.fake}/psql \"$@\"\n")
    lab.run("reset", "b1", "--session", "S1", KY_PSQL=str(shim))
    assert "b1.json" not in (lab.tmp / "at_restore").read_text().split()


def test_revalidation_of_an_existing_database_needs_its_own_ready_receipt(lab):
    first = ready(lab)
    lab.forget_calls()
    again = ready(lab)
    assert again["container"] == first["container"] and again["ledger"] == first["ledger"] + 5
    sql = " ".join(a for c in lab.calls() if c["tool"] == "psql" for a in c["argv"])
    assert "CREATE DATABASE" not in sql and "DROP DATABASE" not in sql and "prod_schema.sql" not in sql
    (lab.run_dir / "local_db" / "b1.json").unlink()
    p = lab.run("db", "b1", "--session", "S1")
    assert p.returncode == 1 and p.stdout.startswith("ky_b1 FAILED: ") and "reset b1" in p.stdout


@pytest.mark.parametrize("field,value", [("session_id", "S2"), ("container.id", "0" * 64), ("mount_source", "/x"),
                                         ("seed.schema_sha256", "0" * 64), ("seed.ledger_sha256", "0" * 64),
                                         ("seed.registry_sha256", "0" * 64), ("result", "FAILED"), ("slot", "b2"),
                                         ("schema", "ky.slot_db/0")])
def test_an_existing_database_is_not_trusted_on_a_receipt_bound_to_something_else(lab, field, value):
    r = ready(lab)
    node, keys = r, field.split(".")
    for k in keys[:-1]:
        node = node[k]
    node[keys[-1]] = value
    (lab.run_dir / "local_db" / "b1.json").write_text(json.dumps(r))
    lab.forget_calls()
    p = lab.run("db", "b1", "--session", "S1")
    assert p.returncode == 1 and p.stdout.startswith("ky_b1 FAILED: ")
    assert [c for c in lab.calls() if c["tool"] == "npx"] == []
    assert lab.run("check", "b1").returncode == 1


def test_reset_drops_and_recreates_the_sessions_own_database(lab):
    ready(lab)
    (lab.run_dir / "schema" / "prod_schema.sql").write_text("CREATE TABLE public.changed ();\n")
    assert lab.run("db", "b1", "--session", "S1").returncode == 1     # the seed moved under an existing database
    lab.forget_calls()
    p = lab.run("reset", "b1", "--session", "S1")
    assert p.returncode == 0, p.stdout + p.err
    sql = [a for c in lab.calls() if c["tool"] == "psql" for a in c["argv"]]
    assert any(a.startswith("DROP DATABASE") for a in sql) and any(a.startswith("CREATE DATABASE") for a in sql)
    assert lab.receipt("b1")["seed"]["schema_sha256"] == sha(lab.run_dir / "schema" / "prod_schema.sql")
    assert lab.run("check", "b1").returncode == 0


def test_reset_of_an_absent_slot_creates_it(lab):
    assert lab.run("reset", "b2", "--session", "S1").returncode == 0
    assert lab.receipt("b2")["result"] == "READY" and lab.world()["dbs"]["ky_b2"]["comment"] == "ky.session=S1"


# ── check: read-only, and READY only as observed now ───────────────────────────────────────────────────────────
def test_check_is_read_only(lab):
    ready(lab)
    before, world, raw = lab.tree(), lab.world(), (lab.run_dir / "local_db" / "b1.json").read_bytes()
    lab.forget_calls()
    p = lab.run("check", "b1")
    assert p.returncode == 0 and p.stdout.startswith("ky_b1 READY: ")
    assert mutating(lab.calls()) == [] and lab.calls() != []
    assert lab.tree() == before and lab.world() == world
    assert (lab.run_dir / "local_db" / "b1.json").read_bytes() == raw


def stale_cases():
    def seed_changed(lab):
        (lab.run_dir / "schema" / "asset_registry_data.sql").write_text("COPY x;\nbg_transit_rules\nmore\n")

    def seed_gone(lab):
        (lab.run_dir / "schema" / "migrations_applied_data.sql").unlink()

    def container_replaced(lab):
        w = lab.world()
        w["container"]["id"] = "9" * 64
        lab.save(w)

    def container_gone(lab):
        w = lab.world()
        w["container"], w["dbs"] = None, {}
        lab.save(w)

    def container_stopped(lab):
        w = lab.world()
        w["container"]["running"] = False
        lab.save(w)

    def database_gone(lab):
        w = lab.world()
        del w["dbs"]["ky_b1"]
        lab.save(w)

    def mark(value):
        def change(lab):
            w = lab.world()
            w["dbs"]["ky_b1"]["comment"] = value
            lab.save(w)
        return change

    def mount_moved(lab):
        other = lab.R / "db" / "ELSE" / "pgdata"
        other.mkdir(parents=True)
        w = lab.world()
        w["container"]["mounts"][0]["Source"] = str(other)
        lab.save(w)

    def receipt_gone(lab):
        (lab.run_dir / "local_db" / "b1.json").unlink()

    def receipt_garbage(lab):
        (lab.run_dir / "local_db" / "b1.json").write_text("{not json")

    def receipt_failed(lab):
        r = lab.receipt("b1")
        r["result"] = "FAILED"
        (lab.run_dir / "local_db" / "b1.json").write_text(json.dumps(r))

    def receipt_of_another_slot(lab):
        r = lab.receipt("b1")
        r["slot"], r["database"] = "b2", "ky_b2"
        (lab.run_dir / "local_db" / "b1.json").write_text(json.dumps(r))

    def slot_unconfigured(lab):
        lab.pools(None, 1)

    def docker_down(lab):
        lab.modes(docker_down=True)

    def server_down(lab):
        lab.modes(psql_down=True)

    return {"seed_changed": seed_changed, "seed_gone": seed_gone, "container_replaced": container_replaced,
            "container_gone": container_gone, "container_stopped": container_stopped, "database_gone": database_gone,
            "mark_other_session": mark("ky.session=S2"), "mark_removed": mark(""), "mount_moved": mount_moved,
            "receipt_gone": receipt_gone, "receipt_garbage": receipt_garbage, "receipt_failed": receipt_failed,
            "receipt_of_another_slot": receipt_of_another_slot, "slot_unconfigured": slot_unconfigured,
            "docker_down": docker_down, "server_down": server_down}


@pytest.mark.parametrize("case", sorted(stale_cases()))
def test_stale_ready_receipt_is_not_ready(lab, case):
    """A READY receipt whose world moved on: check exit 1, `ky_<slot> STALE: <reason>`, and nothing is touched."""
    ready(lab)
    assert lab.run("check", "b1").returncode == 0
    stale_cases()[case](lab)
    before, world = lab.tree(), lab.world()
    lab.forget_calls()
    p = lab.run("check", "b1")
    assert p.returncode == 1 and re.fullmatch(r"ky_b1 STALE: \S.*\n", p.stdout), p.stdout
    assert mutating(lab.calls()) == [] and lab.tree() == before and lab.world() == world


def test_check_without_a_usable_scratch_root_is_stale_not_ready(lab):
    ready(lab)
    for over in ({"KY_SCRATCH": None}, {"KY_SCRATCH": str(lab.tmp / "elsewhere")}):
        (lab.tmp / "elsewhere").mkdir(exist_ok=True)
        p = lab.run("check", "b1", **over)
        assert p.returncode == 1 and p.stdout.startswith("ky_b1 STALE: ")


@pytest.mark.parametrize("slot", ["x1", "b1;x", "../b1", "b0", ""])
def test_check_refuses_a_malformed_slot(lab, slot):
    p = lab.run("check", slot)
    assert p.returncode == 2 and lab.calls() == []


# ── ownership ──────────────────────────────────────────────────────────────────────────────────────────────────
def test_ownership_conflict_refuses_db_and_reset_and_close_keeps_the_other_sessions_database(lab):
    r = ready(lab, "b1", "S1")
    world, before = lab.world(), lab.tree()
    lab.forget_calls()
    for command in ("db", "reset"):
        p = lab.run(command, "b1", "--session", "S2")
        assert p.returncode == 2, p.stdout + p.err
        assert "READY" not in p.stdout
    assert mutating(lab.calls()) == [] and lab.world() == world and lab.tree() == before
    close = lab.run("close", "--session", "S2")
    assert close.returncode == 0 and close.stdout == "close session=S2 dropped=0 container=handed_over\n"
    w = lab.world()
    assert w["dbs"] == world["dbs"] and w["container"] == world["container"]
    assert lab.receipt("b1") == r
    assert json.loads(lab.record_path().read_text()) == {"owner": "S1", "storage": str(lab.R / "db" / "S1"), "from": "S2"}
    assert not set(docker_verbs(lab.calls())) & {"stop", "rm", "rename", "kill"}
    assert lab.run("check", "b1").returncode == 0


@pytest.mark.parametrize("comment", ["", "ky.session=", "ky.session=a/b", "ky.session=S1 ", "mine", "ky.session=a..b"])
@pytest.mark.parametrize("command", ["db", "reset"])
def test_a_database_without_a_valid_session_mark_is_nobodys_to_reuse(lab, command, comment):
    lab.plant_container(session="S1")
    lab.plant_db("ky_b1", comment)
    world = lab.world()
    p = lab.run(command, "b1", "--session", "S1")
    assert p.returncode == 2 and mutating(lab.calls()) == [] and lab.world() == world
    assert not (lab.run_dir / "local_db" / "b1.json").exists()


# ── close ──────────────────────────────────────────────────────────────────────────────────────────────────────
def test_close_without_a_container_exits_0(lab):
    before = lab.tree()
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=absent\n"
    assert docker_verbs(lab.calls()) == ["ps"] and lab.tree() == before


def vanish(lab):
    """The container goes away outside the script (a crash, an operator's `docker rm`); the files it wrote stay."""
    w = lab.world()
    w["container"], w["dbs"] = None, {}
    lab.save(w)
    lab.forget_calls()


def test_close_without_a_container_removes_the_sessions_storage_and_receipts(lab):
    """Review B-01: `absent` is an observation of S's storage and receipts too, not of docker alone."""
    ready(lab, "b1", "S1")
    storage = lab.R / "db" / "S1"
    (storage / "pgdata" / "base").mkdir()
    (storage / "pgdata" / "base" / "16384").write_text("the closed session's database files\n")
    vanish(lab)
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=absent\n"
    assert not storage.exists() and not (lab.run_dir / "local_db" / "b1.json").exists()
    assert docker_verbs(lab.calls()) == ["ps"] and mutating(lab.calls()) == []
    assert (lab.R / "db").is_dir()                                    # only the storage child goes, logs stay
    assert lab.run("up", "--session", "S1").returncode == 0           # a later session starts from nothing
    assert sorted(x.name for x in (storage / "pgdata").iterdir()) == ["PG_VERSION"]


def test_close_without_a_container_exits_1_when_storage_survives(lab):
    ready(lab, "b1", "S1")
    storage = lab.R / "db" / "S1"
    vanish(lab)
    lab._exe(lab.shims / "rm", "#!/bin/sh\nexit 0\n")                 # a removal that reports success and removes nothing
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=0 container=storage_remains\n"
    assert (storage / "pgdata" / "PG_VERSION").exists()
    (lab.shims / "rm").unlink()
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=absent\n"
    assert not storage.exists()


def test_close_without_a_container_exits_1_when_a_receipt_survives(lab):
    ready(lab, "b1", "S1")
    vanish(lab)
    receipts = lab.run_dir / "local_db"
    receipts.chmod(0o555)                                             # the receipt cannot be unlinked
    try:
        p = lab.run("close", "--session", "S1")
    finally:
        receipts.chmod(0o755)
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=0 container=receipts_remain\n"
    assert lab.receipt("b1")["session_id"] == "S1"
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=absent\n"
    assert not (receipts / "b1.json").exists()


def test_close_without_a_container_does_not_follow_a_symlinked_session_directory(lab):
    outside = lab.tmp / "outside"
    outside.mkdir()
    (outside / "kept").write_text("not the session's\n")
    (lab.R / "db").mkdir()
    (lab.R / "db" / "S1").symlink_to(outside)
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=0 container=storage_remains\n"
    assert (outside / "kept").exists() and (lab.R / "db" / "S1").is_symlink()


def test_close_without_a_container_keeps_another_sessions_receipt_and_storage(lab):
    ready(lab, "b1", "S1")
    r2 = ready(lab, "b2", "S2")
    theirs = lab.R / "db" / "S2" / "pgdata"
    theirs.mkdir(parents=True)
    (theirs / "PG_VERSION").write_text("16\n")
    vanish(lab)
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=absent\n"
    assert not (lab.R / "db" / "S1").exists() and not (lab.run_dir / "local_db" / "b1.json").exists()
    assert lab.receipt("b2") == r2 and (theirs / "PG_VERSION").exists()


def test_close_without_a_container_follows_the_hand_over_record(lab):
    """Storage handed over is the new owner's: the session that gave it away leaves it, its owner on record removes it."""
    ready(lab, "b1", "S1")
    ready(lab, "b2", "S2")
    storage = lab.R / "db" / "S1"
    assert lab.run("close", "--session", "S1").stdout == "close session=S1 dropped=1 container=handed_over\n"
    record = {"owner": "S2", "storage": str(storage), "from": "S1"}
    vanish(lab)
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=absent\n"
    assert (storage / "pgdata" / "PG_VERSION").exists() and json.loads(lab.record_path().read_text()) == record
    p = lab.run("close", "--session", "S2")
    assert p.returncode == 0 and p.stdout == "close session=S2 dropped=0 container=absent\n"
    assert not storage.exists() and not lab.record_path().exists()
    assert list((lab.run_dir / "local_db").glob("*.json")) == []
    assert mutating(lab.calls()) == []


def test_close_without_a_container_exits_1_when_the_hand_over_record_survives(lab):
    ready(lab, "b1", "S1")
    ready(lab, "b2", "S2")
    storage = lab.R / "db" / "S1"
    assert lab.run("close", "--session", "S1").returncode == 0
    vanish(lab)
    receipts = lab.run_dir / "local_db"
    (receipts / "b2.json").unlink()                                   # S2 holds the record and nothing else
    receipts.chmod(0o555)
    try:
        p = lab.run("close", "--session", "S2")
    finally:
        receipts.chmod(0o755)
    assert p.returncode == 1 and p.stdout == "close session=S2 dropped=0 container=record_remains\n"
    assert not storage.exists() and lab.record_path().exists()


def test_close_removes_the_last_sessions_databases_container_and_storage(lab):
    ready(lab, "b1", "S1")
    ready(lab, "v1", "S1")
    storage = lab.R / "db" / "S1"
    assert (storage / "pgdata" / "PG_VERSION").exists()
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=2 container=removed\n"
    w = lab.world()
    assert w["container"] is None and w["dbs"] == {} and not storage.exists()
    assert list((lab.run_dir / "local_db").glob("*.json")) == []
    assert (lab.R / "db").is_dir()                                    # only the storage child goes, logs stay
    assert lab.run("check", "b1").returncode == 1
    assert lab.run("close", "--session", "S1").stdout == "close session=S1 dropped=0 container=absent\n"


def test_label_owner_closes_first_and_the_other_second_container_and_storage_absent(lab):
    ready(lab, "b1", "S1")                                            # S1 runs `up`: the label and the storage are S1's
    r2 = ready(lab, "b2", "S2")
    storage = lab.R / "db" / "S1"
    first = lab.run("close", "--session", "S1")
    assert first.returncode == 0 and first.stdout == "close session=S1 dropped=1 container=handed_over\n"
    w = lab.world()
    assert sorted(w["dbs"]) == ["ky_b2"] and w["container"]["labels"]["ky.session"] == "S1" and storage.is_dir()
    assert json.loads(lab.record_path().read_text()) == {"owner": "S2", "storage": str(storage), "from": "S1"}
    assert not (lab.run_dir / "local_db" / "b1.json").exists() and lab.receipt("b2") == r2
    assert lab.run("check", "b2").returncode == 0                     # the hand-over does not stale the survivor
    assert not set(docker_verbs(lab.calls())) & {"stop", "rm", "rename"}
    second = lab.run("close", "--session", "S2")
    assert second.returncode == 0 and second.stdout == "close session=S2 dropped=1 container=removed\n"
    assert lab.world()["container"] is None and not storage.exists()
    assert not lab.record_path().exists() and list((lab.run_dir / "local_db").glob("*.json")) == []


def test_hand_over_goes_to_the_current_owner_when_it_remains_and_else_to_the_first_remaining_session(lab):
    ready(lab, "b1", "S1")
    ready(lab, "b2", "S3")
    ready(lab, "v1", "S2")
    assert lab.run("close", "--session", "S3").returncode == 0        # S1 holds the label and stays
    assert json.loads(lab.record_path().read_text())["owner"] == "S1"
    assert lab.run("close", "--session", "S1").returncode == 0
    assert json.loads(lab.record_path().read_text()) == {"owner": "S2", "storage": str(lab.R / "db" / "S1"), "from": "S1"}


def test_a_hand_over_that_cannot_be_recorded_is_not_a_close(lab):
    """S's label on a container with no record: exit 1."""
    ready(lab, "b1", "S1")
    ready(lab, "b2", "S2")
    lab.record_path().mkdir()                                         # the atomic replace cannot land
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=1 container=handover_unrecorded\n"
    assert lab.world()["container"] is not None and sorted(lab.world()["dbs"]) == ["ky_b2"]
    lab.record_path().rmdir()
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=handed_over\n"


def test_close_hands_over_a_container_and_removes_the_sessions_own_storage_it_does_not_mount(lab):
    """Review round 2, B-01: with a ky-pg present, exit 0 also observes R/db/S gone when the container mounts another store."""
    ready(lab, "b1", "S1")
    own = lab.R / "db" / "S1"
    (own / "pgdata" / "base").mkdir()
    (own / "pgdata" / "base" / "16384").write_text("the closed session's database files\n")
    vanish(lab)
    r2 = ready(lab, "b2", "S3")                                       # a new container, on R/db/S3
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=handed_over\n"
    assert not own.exists() and (lab.R / "db" / "S3" / "pgdata" / "PG_VERSION").exists()
    assert lab.receipt("b2") == r2 and lab.run("check", "b2").returncode == 0
    assert json.loads(lab.record_path().read_text()) == {"owner": "S3", "storage": str(lab.R / "db" / "S3"), "from": "S1"}
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=handed_over\n"


def test_close_removes_a_container_and_the_sessions_own_storage_it_does_not_mount(lab):
    ready(lab, "b1", "S1")
    own = lab.R / "db" / "S1"
    vanish(lab)
    assert lab.run("up", "--session", "S3").returncode == 0           # no database of anyone's in it
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=removed\n"
    assert lab.world()["container"] is None and not own.exists() and not (lab.R / "db" / "S3").exists()


@pytest.mark.parametrize("others", [True, False])
def test_close_with_a_container_exits_1_when_its_own_unmounted_storage_survives(lab, others):
    ready(lab, "b1", "S1")
    own = lab.R / "db" / "S1"
    vanish(lab)
    if others:
        ready(lab, "b2", "S3")
    else:
        assert lab.run("up", "--session", "S3").returncode == 0
    # S1's storage alone survives a removal that reports success; the container's store really goes
    lab._exe(lab.shims / "rm", f'#!/bin/sh\ncase "$*" in *"{own}"*) exit 0;; esac\nexec /bin/rm "$@"\n')
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=0 container=storage_remains\n"
    assert (own / "pgdata" / "PG_VERSION").exists()
    (lab.shims / "rm").unlink()
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and not own.exists()


def test_close_with_a_container_keeps_storage_on_record_as_another_sessions(lab):
    """R/db/S on record as handed to T is T's to remove, also when the present container mounts something else."""
    ready(lab, "b1", "S1")
    ready(lab, "b2", "S2")
    storage = lab.R / "db" / "S1"
    assert lab.run("close", "--session", "S1").returncode == 0
    record = {"owner": "S2", "storage": str(storage), "from": "S1"}
    vanish(lab)
    lab.plant_container(session="S3")                                 # started outside the script, on R/db/S3
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=removed\n"
    assert (storage / "pgdata" / "PG_VERSION").exists() and json.loads(lab.record_path().read_text()) == record
    p = lab.run("close", "--session", "S2")
    assert p.returncode == 0 and p.stdout == "close session=S2 dropped=0 container=absent\n"
    assert not storage.exists() and not lab.record_path().exists()


def test_a_hand_over_never_overwrites_another_sessions_record_of_other_storage(lab):
    ready(lab, "b1", "S1")
    ready(lab, "b2", "S2")
    storage = lab.R / "db" / "S1"
    assert lab.run("close", "--session", "S1").returncode == 0
    record = {"owner": "S2", "storage": str(storage), "from": "S1"}
    vanish(lab)
    lab.plant_container(session="S3")
    lab.plant_db("ky_v1", "ky.session=S3")
    lab.plant_db("ky_b1", "ky.session=S4")
    p = lab.run("close", "--session", "S4")
    assert p.returncode == 1 and p.stdout == "close session=S4 dropped=1 container=handover_unrecorded\n"
    assert json.loads(lab.record_path().read_text()) == record and (storage / "pgdata" / "PG_VERSION").exists()
    assert lab.run("close", "--session", "S2").returncode == 0        # the owner on record removes its storage
    assert not storage.exists() and json.loads(lab.record_path().read_text())["storage"] == str(lab.R / "db" / "S3")
    p = lab.run("close", "--session", "S4")
    assert p.returncode == 0 and p.stdout == "close session=S4 dropped=0 container=handed_over\n"


# ── a hand-over record outlives its container until the storage it names is gone (review round 2, B-02) ──────────
def handed_over_then_vanished(lab):
    ready(lab, "b1", "S1")
    ready(lab, "b2", "S2")
    assert lab.run("close", "--session", "S1").stdout == "close session=S1 dropped=1 container=handed_over\n"
    record = {"owner": "S2", "storage": str(lab.R / "db" / "S1"), "from": "S1"}
    assert json.loads(lab.record_path().read_text()) == record
    vanish(lab)
    return record


@pytest.mark.parametrize("command", [("up", "--session", "S3"), ("db", "v1", "--session", "S3"),
                                     ("reset", "v1", "--session", "S3"), ("up", "--session", "S1")])
def test_up_refuses_while_another_sessions_handed_over_storage_exists(lab, command):
    record = handed_over_then_vanished(lab)
    storage, before = lab.R / "db" / "S1", lab.tree()
    p = lab.run(*command)
    assert p.returncode == 2 and "S2" in p.err
    assert lab.tree() == before and docker_verbs(lab.calls()) == ["ps"] and mutating(lab.calls()) == []
    assert json.loads(lab.record_path().read_text()) == record and (storage / "pgdata" / "PG_VERSION").exists()


def test_the_owner_on_record_closes_the_handed_over_storage_and_up_proceeds(lab):
    handed_over_then_vanished(lab)
    storage = lab.R / "db" / "S1"
    assert lab.run("db", "v1", "--session", "S3").returncode == 2
    p = lab.run("close", "--session", "S2")
    assert p.returncode == 0 and p.stdout == "close session=S2 dropped=0 container=absent\n"
    assert not storage.exists() and not lab.record_path().exists()
    ready(lab, "v1", "S3")
    p = lab.run("close", "--session", "S3")
    assert p.returncode == 0 and p.stdout == "close session=S3 dropped=1 container=removed\n"
    assert lab.world()["container"] is None and [x.name for x in (lab.R / "db").iterdir() if x.is_dir()] == []


def test_up_by_the_owner_on_record_removes_the_handed_over_storage_and_sees_it_gone(lab):
    handed_over_then_vanished(lab)
    storage = lab.R / "db" / "S1"
    ready(lab, "b2", "S2")
    assert not storage.exists() and not lab.record_path().exists()
    assert lab.world()["container"]["mounts"][0]["Source"] == str(lab.R / "db" / "S2" / "pgdata")


def test_up_by_the_owner_on_record_fails_when_the_handed_over_storage_survives(lab):
    record = handed_over_then_vanished(lab)
    storage = lab.R / "db" / "S1"
    lab._exe(lab.shims / "rm", "#!/bin/sh\nexit 0\n")
    p = lab.run("db", "b2", "--session", "S2")
    assert p.returncode == 1 and "FAILED" in p.stdout
    assert json.loads(lab.record_path().read_text()) == record and storage.exists()
    assert "run" not in docker_verbs(lab.calls())


def test_up_discards_a_hand_over_record_whose_storage_is_gone(lab):
    handed_over_then_vanished(lab)
    shutil.rmtree(lab.R / "db" / "S1")
    ready(lab, "v1", "S3")
    assert not lab.record_path().exists()


def test_up_refuses_an_unreadable_hand_over_record(lab):
    (lab.run_dir / "local_db").mkdir()
    lab.record_path().write_text("{not json")
    before = lab.tree()
    p = lab.run("up", "--session", "S1")
    assert p.returncode == 2 and lab.tree() == before and docker_verbs(lab.calls()) == ["ps"]


def test_close_with_an_unmarked_database_exits_1_and_removes_nothing(lab):
    ready(lab, "b1", "S1")
    lab.plant_db("somebody_elses", "")
    world, before = lab.world(), lab.tree()
    lab.forget_calls()
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=0 container=unmarked_database\n"
    assert "somebody_elses" in p.err
    assert mutating(lab.calls()) == [] and lab.world() == world and lab.tree() == before


def test_stop_without_removal_still_owes_a_close(lab):
    """`down` is not a cleanup: the databases, the container and the storage are all still there afterwards."""
    ready(lab)
    p = lab.run("down")
    assert p.returncode == 0
    w = lab.world()
    assert w["container"] is not None and not w["container"]["running"] and "ky_b1" in w["dbs"]
    assert (lab.R / "db" / "S1" / "pgdata").is_dir() and lab.receipt("b1")["result"] == "READY"
    assert "rm" not in docker_verbs(lab.calls())
    assert lab.run("check", "b1").returncode == 1                     # a stopped server proves nothing
    close = lab.run("close", "--session", "S1")
    assert close.returncode == 0 and close.stdout == "close session=S1 dropped=1 container=removed\n"
    assert lab.world()["container"] is None and not (lab.R / "db" / "S1").exists()


@pytest.mark.parametrize("mode", ["rm_noop", "rm_fail", "stop_fail"])
def test_close_exits_0_only_once_absence_is_observed(lab, mode):
    ready(lab)
    lab.modes(**{mode: True})
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=1 container=not_removed\n"
    assert lab.world()["container"] is not None
    assert (lab.R / "db" / "S1" / "pgdata").is_dir()                  # storage is never pulled from under a container
    lab.modes()
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=0 container=removed\n"
    assert lab.world()["container"] is None and not (lab.R / "db" / "S1").exists()


def test_close_exits_1_when_a_database_survives_its_drop(lab):
    ready(lab)
    lab.modes(drop_noop=True)
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=0 container=databases_remain\n"
    assert lab.world()["container"] is not None and "rm" not in docker_verbs(lab.calls())


def test_close_exits_1_when_storage_survives(lab):
    ready(lab)
    storage = lab.R / "db" / "S1"
    lab._exe(lab.shims / "rm", "#!/bin/sh\nexit 0\n")                 # a removal that reports success and removes nothing
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=1 container=storage_remains\n"
    assert storage.exists() and lab.world()["container"] is None


@pytest.mark.parametrize("modes", [{"docker_down": True}, {"psql_down": True}, {"list_fail": True}])
def test_close_exits_1_when_it_cannot_observe(lab, modes):
    ready(lab)
    lab.modes(**modes)
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 1 and p.stdout == "close session=S1 dropped=0 container=unobservable\n"
    assert "ky_b1" in lab.world()["dbs"] and not set(docker_verbs(lab.calls())) & {"stop", "rm"}


def test_close_removes_a_stale_receipt_of_its_session_and_leaves_other_files_alone(lab):
    ready(lab, "b1", "S1")
    ready(lab, "b2", "S2")
    orphan = lab.receipt("b1")
    orphan["slot"], orphan["database"] = "v1", "ky_v1"
    (lab.run_dir / "local_db" / "v1.json").write_text(json.dumps(orphan))
    (lab.run_dir / "local_db" / "notes.json").write_text('{"session_id": "S1"}')
    assert lab.run("close", "--session", "S1").returncode == 0
    assert sorted(p.name for p in (lab.run_dir / "local_db").iterdir()) == ["b2.json", "container.json", "notes.json"]


def test_close_drops_a_database_of_its_session_whatever_its_name(lab):
    ready(lab, "b1", "S1")
    lab.plant_db('odd"name', "ky.session=S1")
    p = lab.run("close", "--session", "S1")
    assert p.returncode == 0 and p.stdout == "close session=S1 dropped=2 container=removed\n"


def test_down_stops_and_never_cleans_up_and_reports_absence(lab):
    assert lab.run("down").returncode == 0 and docker_verbs(lab.calls()) == ["ps"]
    lab.plant_container(session="S1")
    lab.forget_calls()
    assert lab.run("down").returncode == 0
    assert docker_verbs(lab.calls()) == ["ps", "inspect", "stop", "ps", "inspect"]
    lab.modes(stop_fail=True)
    w = lab.world()
    w["container"]["running"] = True
    lab.save(w)
    assert lab.run("down").returncode == 1


# ── seed ───────────────────────────────────────────────────────────────────────────────────────────────────────
def test_seed_writes_the_three_files_and_reads_only_the_fixture_settings(lab):
    shutil.rmtree(lab.run_dir / "schema")
    p = lab.run("seed", trace=True)
    assert p.returncode == 0, p.stdout + p.err
    d = lab.run_dir / "schema"
    for name in ("prod_schema.sql", "migrations_applied_data.sql", "asset_registry_data.sql"):
        assert (d / name).stat().st_size > 0
    assert sha(d / "prod_schema.sql") in p.stdout and sha(d / "asset_registry_data.sql") in p.stdout
    assert sorted(x.name for x in d.iterdir()) == ["SEEDED_AT", "asset_registry_data.sql", "excluded_tables.txt",
                                                   "migrations_applied_data.sql", "prod_schema.sql"]
    dumps = [c for c in lab.calls() if c["tool"] == "pg_dump"]
    assert len(dumps) == 3 and all(c["PGHOST"] == "fake-prod.invalid" for c in dumps)
    assert [c["tool"] for c in lab.calls()] == ["pg_dump"] * 3        # no docker, no psql, no runner
    assert sourced_paths(lab.traces[-1]) == [str(lab.pgenv)]
    # the seed it wrote is the seed a slot database is then proven against
    assert ready(lab)["seed"]["registry_sha256"] == sha(d / "asset_registry_data.sql")


def test_settings_path_detector_fires_on_the_path_it_watches(lab):
    """Negative fixture for the suite's settings-path watch: aimed at the file this run did open, it fails."""
    assert lab.run("seed", trace=True).returncode == 0
    assert_settings_path_unopened(lab.traces[-1], REAL_PGENV)
    with pytest.raises(AssertionError, match="was opened"):
        assert_settings_path_unopened(lab.traces[-1], str(lab.pgenv))


def test_the_real_settings_path_is_named_once_and_only_as_the_default(lab):
    text = SCRIPT.read_text()
    assert text.count(REAL_PGENV) == 1
    assert re.search(r'^REAL_PGENV=' + re.escape(REAL_PGENV) + r'\b', text, re.M)
    uses = [line for line in text.splitlines() if "REAL_PGENV" in line and not line.startswith("REAL_PGENV=")]
    assert len(uses) == 1 and "${KY_PGENV:-$REAL_PGENV}" in uses[0]


def test_seed_excludes_the_tables_it_may_not_read_and_says_which(lab):
    lab.modes(deny=["planner_secret", "other_hidden"])
    assert lab.run("seed", trace=True).returncode == 0
    assert (lab.run_dir / "schema" / "excluded_tables.txt").read_text().split() == ["public.planner_secret",
                                                                                   "public.other_hidden"]


@pytest.mark.parametrize("mode", ["empty", "missing", "error"])
def test_seed_fails_on_a_missing_or_empty_registry_dump_and_keeps_the_admitted_seed(lab, mode):
    lab.modes(registry_dump=mode)
    before = {p.name: p.read_bytes() for p in (lab.run_dir / "schema").iterdir()}
    p = lab.run("seed", trace=True)
    assert p.returncode == 1 and "seed FAILED" in p.stdout and "ready" not in p.stdout
    assert {x.name: x.read_bytes() for x in (lab.run_dir / "schema").iterdir()} == before
    shutil.rmtree(lab.run_dir / "schema")
    assert lab.run("seed", trace=True).returncode == 1
    assert not list((lab.run_dir / "schema").glob("*.sql"))
    assert lab.run("db", "b1", "--session", "S1").returncode == 1


@pytest.mark.parametrize("var", ["KY_LANE", "KY_ITEM", "JOB_SCRATCH"])
def test_seed_is_refused_inside_a_job(lab, var):
    before = lab.tree()
    for value in ("x", ""):
        p = lab.run("seed", trace=True, **{var: value})
        assert p.returncode == 2
    assert lab.calls() == [] and lab.tree() == before
    assert all(sourced_paths(t) == [] for t in lab.traces)


def test_the_settings_override_is_refused_against_the_live_run_directory(lab):
    for live in (LIVE_RUN, LIVE_RUN + "/", "/Users/Dev/kalayantra/./run", "/Users/Dev/kalayantra/x/../run"):
        p = lab.run("seed", trace=True, live_run=True, KY_RUN=live)
        assert p.returncode == 2, live
    assert lab.calls() == [] and all(sourced_paths(t) == [] for t in lab.traces)


@pytest.mark.parametrize("over", [{"KY_SCRATCH": None}, {"KY_PGENV": "relative/pgenv.sh"}, {"KY_PG_DUMP": "pg_dump"}])
def test_seed_refuses_an_unusable_environment(lab, over):
    before = lab.tree()
    p = lab.run("seed", trace=True, **over)
    assert p.returncode == 2 and lab.calls() == [] and lab.tree() == before


def test_seed_fails_without_its_settings_file(lab):
    lab.pgenv.unlink()
    p = lab.run("seed", trace=True)
    assert p.returncode == 1 and lab.calls() == []


def test_seed_runs_as_a_lone_copy(lab):
    """executor.py extracts the script and runs `bash <copy> seed`: nothing beside it may be needed."""
    alone = lab.tmp / "ops" / "op-1.local_db.sh"
    alone.parent.mkdir()
    shutil.copy(SCRIPT, alone)
    p = lab.run("seed", script=alone, trace=True)
    assert p.returncode == 0, p.stdout + p.err
    assert sorted(x.name for x in alone.parent.iterdir()) == [alone.name]


# ── plan §3: no job holds DATABASE_URL ─────────────────────────────────────────────────────────────────────────
def test_the_script_exports_no_connection_and_has_no_url_command(lab):
    text = SCRIPT.read_text()
    assert not re.search(r"^\s*(export|declare -x)\b.*\b(PGPASSWORD|DATABASE_URL|PW)\b", text, re.M)
    assert not re.search(r"^\s*url\)", text, re.M)
    p = lab.run("url", "b1")
    assert p.returncode == 64 and p.stdout == ""


def test_a_runner_that_prints_its_connection_does_not_leave_it_in_the_log(lab):
    lab.modes(runner_prints_url=True)
    ready(lab)
    log = (lab.R / "db" / "_ky_b1.runner.log").read_text()
    assert "connecting to <local connection>" in log and find_leaks(log) == []


def test_no_output_or_file_holds_a_password_or_url_across_a_whole_life(lab):
    """The per-test watch (see the fixture) reads every output and every file; this walks the full life under it."""
    assert lab.run("seed", trace=True).returncode == 0
    for args in (["up", "--session", "S1"], ["db", "b1", "--session", "S1"], ["check", "b1"],
                 ["db", "b1", "--session", "S1"], ["reset", "b1", "--session", "S1"], ["db", "b2", "--session", "S2"],
                 ["close", "--session", "S1"], ["down"], ["close", "--session", "S2"]):
        assert lab.run(*args).returncode == 0, args
    assert len(lab.outputs) == 10 and any("READY" in out for _, out, _ in lab.outputs)
    files = [p for root in (lab.run_dir, lab.scratch_real) for p in root.rglob("*") if p.is_file()]
    assert len(files) >= 8


@pytest.mark.parametrize("hidden", [False, True])
def test_up_waits_for_previous_compatible_removal_and_name_release(lab, hidden):
    old = lab.plant_container(session="PREVIOUS", running=False)
    lab.modes(rm_delay=True, removal_polls=3, hide_removing=hidden)
    subprocess.run([str(lab.fake / "docker"), "rm", old["id"]], check=True, capture_output=True)
    lab.forget_calls()
    p = lab.run("up", "--session", "S1")
    assert p.returncode == 0, p.stdout + p.err
    c = lab.world()["container"]
    assert c["id"] != old["id"] and c["labels"]["ky.session"] == "S1"
    assert c["mounts"][0]["Source"] == str(lab.R / "db" / "S1" / "pgdata")
    assert not {"start", "stop", "rm", "rename"} & set(docker_verbs(lab.calls()))


def test_up_waits_for_preceding_removal_record_cleanup(lab):
    old = lab.plant_container(session="PREVIOUS", running=False)
    store = lab.R / "db" / "PREVIOUS"
    lab.record_path().parent.mkdir(parents=True)
    lab.record_path().write_text(json.dumps({"owner": "PREVIOUS", "from": "OLDER", "storage": str(store)}))
    lab.modes(rm_delay=True, removal_polls=2, cleanup_polls=2,
              cleanup_storage=str(store), cleanup_record=str(lab.record_path()))
    subprocess.run([str(lab.fake / "docker"), "rm", old["id"]], check=True, capture_output=True)
    lab.forget_calls()
    p = lab.run("up", "--session", "S1")
    assert p.returncode == 0, p.stdout + p.err
    assert not store.exists() and not lab.record_path().exists()
    assert lab.world()["container"]["labels"]["ky.session"] == "S1"


def test_up_removal_wait_is_bounded_and_never_starts_the_removing_container(lab):
    old = lab.plant_container(session="PREVIOUS", running=False)
    w = lab.world(); w["container"]["removing"] = True; lab.save(w)
    lab.modes(removal_polls=1000)
    p = lab.run("up", "--session", "S1")
    assert p.returncode == 1, p.stdout + p.err
    assert "removal" in p.err
    assert lab.world()["container"]["id"] == old["id"]
    assert mutating(lab.calls()) == []
    assert len([c for c in lab.calls() if c["tool"] == "docker" and c["argv"][0] == "ps"]) <= 12


def test_up_never_waits_for_or_touches_a_foreign_removing_container(lab):
    lab.plant_container(image="postgres:16", running=False)
    w = lab.world(); w["container"]["removing"] = True; lab.save(w)
    lab.modes(removal_polls=1000)
    before = lab.tree()
    p = lab.run("up", "--session", "S1")
    assert p.returncode == 2 and "INCOMPATIBLE" in p.err
    assert lab.tree() == before and mutating(lab.calls()) == []
    assert docker_verbs(lab.calls()) == ["ps", "inspect"]
