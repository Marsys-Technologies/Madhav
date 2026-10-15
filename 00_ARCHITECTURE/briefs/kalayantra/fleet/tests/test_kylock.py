"""kylock.sh (packet KV3-B-KYLOCK; relaunch plan v2.7 §4a.2, §6, §11; KU-02; ruling R2): the atomic role lock.

Every test runs the REAL script against a temporary KY_RUN and a temporary KY_FLEET whose `local_db.sh` is a
double (the real one is never called, and nothing under /Users/Dev/kalayantra is written). Holders are real
processes: the pytest process itself, or an `Agent` — a python process started here that calls kylock.sh exactly
as kyloop.py does. Processes are signalled only when this file started them (a direct, unreaped child through its
Popen handle; anything else only after its pid AND start identity were re-read); every other probe is signal 0
or ps. The tests-only ps hook (KY_LOCK_PS) is used only where a real ps cannot be made to fail, hang or race."""
import ast
import json
import os
import re
import signal
import stat
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
KYLOCK = FLEET / "kylock.sh"
sys.path.insert(0, str(FLEET))

import kycommands  # noqa: E402

PS_ENV = {"LC_ALL": "C", "PATH": "/bin:/usr/bin"}
OWNER_KEYS = {"session_or_run_id", "holder_kind", "pid", "pgid", "process_start", "acquired_at", "child"}
ANOTHER_START = "Thu Jan  1 00:00:00 2015"
LINE_RE = re.compile(r"kylock: (acquire|release|child|status|-) role=\S+ state=\S+ holder=\S+ pid=\S+( \S+=\S+)*\Z")

AGENT = r'''
import json, os, subprocess, sys
sys.path.insert(0, sys.argv[1])
for line in sys.stdin:
    op = json.loads(line)
    if op["op"] == "run":                       # kyloop.py's call form: no env argument, output captured as text
        if "env" in op:
            r = subprocess.run(op["argv"], capture_output=True, text=True, env=dict(os.environ, **op["env"]))
        else:
            r = subprocess.run(op["argv"], capture_output=True, text=True)
        out = {"rc": r.returncode, "out": r.stdout, "err": r.stderr}
    else:
        import kycommands
        out = list(kycommands.holds_role_lock(op["run"], op["role"], op["id"]))
    print(json.dumps(out), flush=True)
'''

LOCAL_DB_DOUBLE = r'''#!/bin/bash
# double of local_db.sh (KV3-B-LOCALDB): records its call, then does what local_db.mode says
here="$(cd "$(dirname "$0")" && pwd -P)"
printf '%s scratch=%s\n' "$*" "${KY_SCRATCH:-}" >> "$here/local_db.calls"
mode=ok; [ -f "$here/local_db.mode" ] && mode="$(cat "$here/local_db.mode")"
case "$mode" in
  ok) echo "container=removed"; exit 0 ;;
  fail) echo "databases of the session are still there" >&2; exit 1 ;;
  hang) echo "$$" > "$here/local_db.pid"; /bin/sleep 600 ;;
esac
exit 3
'''

FAKE_PS = r'''#!/bin/bash
# tests-only ps: `-o <columns> -p <pid>`; a pid with a <pid>.mode file is answered from it, any other by /bin/ps
ctl="__CTL__"; cols="${2:-}"; pid="${4:-}"
n=$(( $(cat "$ctl/$pid.calls" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$ctl/$pid.calls"
if [ -f "$ctl/$pid.mode" ]; then
  read -r mode arg < "$ctl/$pid.mode"
  case "$mode" in
    gone) exit 1 ;;
    fail) echo "ps: cannot answer" >&2; exit 2 ;;
    garbage) echo "?"; exit 0 ;;
    hang) exec /bin/sleep 600 ;;
    shell) [ "$cols" = "ppid=,comm=" ] && { echo "    1 /bin/bash"; exit 0; } ;;
    login) [ "$cols" = "ppid=,comm=" ] && { echo "$arg -zsh"; exit 0; } ;;
    swap) [ "$n" -ge "$arg" ] && [ -f "$ctl/swap.src" ] && /bin/mv -f "$ctl/swap.src" "$(cat "$ctl/swap.dst")"; exit 1 ;;
  esac
fi
exec /bin/ps "$@"
'''


def lstart(pid):
    r = subprocess.run(["/bin/ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True, env=PS_ENV,
                       timeout=30)
    return r.stdout.strip() or None


def ps_stat(pid):
    """The ps state letters of `pid`, "" when ps positively reports no such process."""
    r = subprocess.run(["/bin/ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, env=PS_ENV,
                       timeout=30)
    return r.stdout.strip()


class Result:
    def __init__(self, rc, out, err):
        self.rc, self.out, self.err = rc, out, err
        lines = out.splitlines()
        assert len(lines) == 1 and LINE_RE.match(lines[0]), "not exactly one status line: %r / %r" % (out, err)
        self.line = lines[0]
        self.verb = lines[0].split()[1]
        self.f = dict(tok.split("=", 1) for tok in lines[0].split()[2:])


class Agent:
    """A long-lived python process of its own session that runs kylock.sh the way kyloop.py does."""

    def __init__(self, world, env):
        self.p = subprocess.Popen([sys.executable, "-B", str(world.agent_py), str(FLEET)], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, env=env, start_new_session=True)
        self.pid = self.p.pid
        self.start = lstart(self.pid)
        assert self.start
        self.ctl = "CTL-PLANNER-%s-%d" % (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), self.pid)

    def ask(self, **op):
        self.p.stdin.write(json.dumps(op) + "\n")
        self.p.stdin.flush()
        return json.loads(self.p.stdout.readline())

    def run(self, argv, env=None):
        return Result(**self.ask(op="run", argv=[str(a) for a in argv], **({"env": env} if env else {})))

    def ky(self, *args, env=None):
        return self.run([KYLOCK, *args], env)

    def exit(self):
        """End it (stdin closed → its loop ends) and reap it: afterwards the pid is positively gone."""
        if self.p.poll() is None:
            self.p.stdin.close()
            try:
                self.p.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.p.kill()                   # our own unreaped child: the pid cannot have been reused
                self.p.wait(timeout=20)


class World:
    def __init__(self, tmp):
        self.tmp = tmp
        self.run, self.fleet, self.scratch, self.ctl = tmp / "run", tmp / "fleet", tmp / "scratch", tmp / "psctl"
        for d in (self.run, self.fleet, self.scratch, self.ctl):
            d.mkdir()
        (self.fleet / "local_db.sh").write_text(LOCAL_DB_DOUBLE)
        self.agent_py = tmp / "agent.py"
        self.agent_py.write_text(AGENT)
        self.fake_ps = tmp / "fake_ps.sh"
        self.fake_ps.write_text(FAKE_PS.replace("__CTL__", str(self.ctl)))
        self.fake_ps.chmod(0o755)
        self.locks = self.run / "locks"
        self.children, self.agents, self.strays = [], [], []

    # ── environment: always the temporary run / fleet / scratch, never an inherited hook ──
    def env(self, drop=(), **over):
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("KY_LOCK_") and k not in ("KY_RUN", "KY_FLEET", "KY_ROOT", "KY_SCRATCH")}
        env.update(KY_RUN=str(self.run), KY_FLEET=str(self.fleet), KY_SCRATCH=str(self.scratch),
                   KY_ROOT=str(self.tmp / "root"))
        env.update({k: str(v) for k, v in over.items()})
        for k in drop:
            env.pop(k, None)
        for k in ("KY_RUN", "KY_ROOT"):
            assert k not in env or env[k].startswith(str(self.tmp)) or over.get(k) is not None
        return env

    def hook(self, **over):
        return {"KY_LOCK_PS": str(self.fake_ps), **{k: str(v) for k, v in over.items()}}

    def ky(self, *args, script=KYLOCK, drop=(), **over):
        r = subprocess.run([str(script), *args], capture_output=True, text=True, env=self.env(drop, **over),
                           timeout=120, stdin=subprocess.DEVNULL)
        return Result(r.returncode, r.stdout, r.stderr)

    # ── processes this test starts ──
    def agent(self):
        a = Agent(self, self.env())
        self.agents.append(a)
        return a

    def sleeper(self):
        """A live process of its own session and group → (Popen, pid, start identity)."""
        p = subprocess.Popen(["/bin/sleep", "600"], start_new_session=True, stdin=subprocess.DEVNULL)
        self.children.append(p)
        start = lstart(p.pid)
        assert start
        return p, p.pid, start

    def dead(self):
        """(pid, start identity) of a process that is positively gone (killed and reaped; its group is empty)."""
        p, pid, start = self.sleeper()
        p.kill()
        p.wait(timeout=20)
        assert ps_stat(pid) == ""
        return pid, start

    def orphan_group(self):
        """A process group whose leader is positively gone while one member lives → (leader pid, leader start)."""
        p = subprocess.Popen(["/bin/sh", "-c", "/bin/sleep 600 & echo $!; read x"], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, text=True, start_new_session=True)
        self.children.append(p)
        member = int(p.stdout.readline())
        leader_start, member_start = lstart(p.pid), lstart(member)
        assert leader_start and member_start
        self.strays.append((member, member_start))
        p.stdin.close()
        p.wait(timeout=20)
        p.stdout.close()
        assert ps_stat(p.pid) == "" and ps_stat(member)
        os.killpg(p.pid, 0)                     # signal 0: the group still has a member
        return p.pid, leader_start

    def cleanup(self):
        for a in self.agents:
            a.exit()
        for p in self.children:
            if p.poll() is None:
                p.kill()                        # a direct, unreaped child: its pid is still its own
            p.wait(timeout=20)
        for pid, start in self.strays:
            if lstart(pid) == start:            # still the very process this test started
                os.kill(pid, signal.SIGKILL)

    # ── the lock on disk ──
    def lock(self, role="planner"):
        return self.locks / role

    def owner(self, role="planner"):
        return json.loads((self.lock(role) / "owner.json").read_text())

    def put(self, doc, role="planner", raw=None):
        """Place a lock by hand, as another actor would have left it; `raw` writes owner.json verbatim."""
        self.lock(role).mkdir(parents=True)
        text = raw if raw is not None else json.dumps(doc, indent=1, sort_keys=True) + "\n"
        (self.lock(role) / "owner.json").write_text(text)
        return text

    def age(self, role="planner"):
        """Make the lock look a quarter of a century old: age never decides anything."""
        for p in (self.lock(role) / "owner.json", self.lock(role)):
            if p.exists():
                os.utime(p, (978307200, 978307200))

    def tree(self):
        out = {}
        for root, dirs, files in os.walk(self.locks):
            for name in [""] + dirs + files:
                p = os.path.join(root, name) if name else root
                st = os.lstat(p)
                data = None
                if stat.S_ISREG(st.st_mode) and st.st_mode & 0o400:
                    with open(p, "rb") as f:
                        data = f.read()
                out[os.path.relpath(p, self.locks)] = (stat.S_IFMT(st.st_mode), st.st_mtime_ns, data)
        return out

    def litter(self):
        """Private directories and graves a call must never leave behind."""
        return sorted(n for n in os.listdir(self.locks) if ".new." in n or ".grave." in n or ".tmp" in n) \
            if self.locks.exists() else []

    def db_calls(self):
        p = self.fleet / "local_db.calls"
        return p.read_text().splitlines() if p.exists() else []

    def ps_mode(self, pid, mode):
        (self.ctl / ("%d.mode" % pid)).write_text(mode + "\n")


@pytest.fixture
def w(tmp_path):
    world = World(tmp_path)
    try:
        yield world
    finally:
        world.cleanup()


def owner_doc(sid, pid, start, kind="controller", child=None, pgid=None):
    return {"session_or_run_id": sid, "holder_kind": kind, "pid": pid, "pgid": pgid if pgid is not None else pid,
            "process_start": start, "acquired_at": "2001-01-01T00:00:00Z", "child": child}


def me():
    return os.getpid(), lstart(os.getpid())


# ───────────────────────────────────────── the script itself ─────────────────────────────────────────

def program():
    text = KYLOCK.read_text()
    head, _, rest = text.partition("<<'KYLOCK_PY'\n")
    body, sep, tail = rest.partition("\nKYLOCK_PY\n")
    assert sep and not tail.strip()
    return head, body


def test_script_is_an_executable_bash_3_2_file_with_one_embedded_stdlib_program():
    assert KYLOCK.read_text().startswith("#!/bin/bash\n") and os.access(KYLOCK, os.X_OK)
    mode = subprocess.run(["git", "ls-files", "-s", "--", str(KYLOCK)], capture_output=True, text=True, cwd=FLEET,
                          timeout=60).stdout.split()
    assert mode and mode[0] == "100755"
    assert subprocess.run(["/bin/bash", "-n", str(KYLOCK)], capture_output=True, timeout=60).returncode == 0
    head, body = program()
    assert "python3" in head and " -I -B " in head
    imported = set()
    for node in ast.walk(ast.parse(body)):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported.add(node.module.split(".")[0])
    assert imported <= set(sys.stdlib_module_names) and not any(m.startswith("ky") for m in imported)
    for forbidden in ("launchctl", "docker", "psql"):
        assert forbidden not in body


# ───────────────────────── 1. acquire as kyloop.py does; the holder is the non-shell caller ─────────────────────────

def test_acquire_as_kyloop_writes_exactly_the_owner_keys_and_the_caller_holds_the_role_lock(w):
    a = w.agent()
    r = a.ky("acquire", "planner", a.ctl)
    assert r.rc == 0 and r.f == {"role": "planner", "state": "acquired", "holder": a.ctl, "pid": str(a.pid)}
    owner = w.owner()
    assert set(owner) == OWNER_KEYS
    assert owner == {"session_or_run_id": a.ctl, "holder_kind": "controller", "pid": a.pid, "pgid": a.pid,
                     "process_start": a.start, "acquired_at": owner["acquired_at"], "child": None}
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", owner["acquired_at"])
    assert os.listdir(w.lock()) == ["owner.json"] and not w.litter()
    # the real predicate the command handler and the veto tick use: true in the holder, false anywhere else
    assert a.ask(op="holds", run=str(w.run), role="planner", id=a.ctl) == [True, None]
    held, reason = kycommands.holds_role_lock(str(w.run), "planner", a.ctl)
    assert held is False and reason.startswith("role_lock_not_owned_by_caller")
    other = w.agent()
    held, reason = other.ask(op="holds", run=str(w.run), role="planner", id=a.ctl)
    assert held is False and reason.startswith("role_lock_not_owned_by_caller")
    assert not w.db_calls()


def test_through_shells_the_holder_is_still_the_non_shell_ancestor(w):
    a = w.agent()
    step = '"$0" "$@"; rc=$?; exit $rc'         # a trailing command: the shell stays between the caller and kylock.sh
    shells = [s for s in ("/bin/sh", "/bin/bash", "/bin/zsh", "/bin/dash", "/bin/ksh") if os.access(s, os.X_OK)]
    assert "/bin/sh" in shells and "/bin/bash" in shells
    argv = []
    for shell in shells:
        argv += [shell, "-c", step]
    r = a.run(argv + [KYLOCK, "acquire", "planner", a.ctl])
    assert r.rc == 0 and r.f["state"] == "acquired" and r.f["pid"] == str(a.pid)
    owner = w.owner()
    assert (owner["pid"], owner["pgid"], owner["process_start"]) == (a.pid, a.pid, a.start)
    assert a.ask(op="holds", run=str(w.run), role="planner", id=a.ctl) == [True, None]
    # … and a cockpit session id through `sh -c` from this (python) process records this process
    r = w.ky("-c", step, str(KYLOCK), "acquire", "conductor", "sess-7f3a.1", script="/bin/sh")
    pid, start = me()
    assert r.rc == 0 and r.f == {"role": "conductor", "state": "acquired", "holder": "sess-7f3a.1", "pid": str(pid)}
    owner = w.owner("conductor")
    assert set(owner) == OWNER_KEYS and owner["holder_kind"] == "cockpit" and owner["child"] is None
    assert (owner["pid"], owner["pgid"], owner["process_start"]) == (pid, os.getpgid(0), start)


def test_a_login_shell_ancestor_is_a_shell_too(w):
    a = w.agent()
    w.ps_mode(a.pid, "login %d" % os.getpid())   # the agent is reported as `-zsh`, child of this process
    r = a.ky("acquire", "planner", "sess-login", env=w.hook())
    assert r.rc == 0 and r.f["pid"] == str(os.getpid()) and r.line.endswith(" test_hook=ps")
    assert w.owner()["pid"] == os.getpid() and w.owner()["process_start"] == me()[1]


def test_a_controller_identity_naming_another_pid_is_refused_and_nothing_is_written(w):
    a = w.agent()
    for ident in ("CTL-PLANNER-20261012T000000Z-%d" % (a.pid + 1), "CTL-PLANNER-20261012T000000Z-%d" % os.getpid(),
                  "CTL-PLANNER", "CTL-PLANNER-20261012T000000Z-0%d" % a.pid, "CTL-PLANNER-x"):
        r = a.ky("acquire", "planner", ident)
        assert r.rc == 70 and r.f["state"] == "refused", r.line
        assert not w.lock().exists() and not w.litter() and "CTL" in r.err
    assert not w.locks.exists() or os.listdir(w.locks) == []


@pytest.mark.parametrize("ident", ["", "..", "a..b", "a/b", "/abs", 'a"b', "a'b", "a b", "a\nb", ".hidden", "-x",
                                   "x" * 65, "a$b", "ä"])
def test_an_identity_outside_the_grammar_is_refused_by_every_verb(w, ident):
    for args in (("acquire", "planner", ident), ("release", "planner", ident), ("child", "planner", ident, "pending")):
        r = w.ky(*args)
        assert r.rc == 70 and r.f["state"] == "refused" and r.f["holder"] == "-", r.line
    assert not w.locks.exists() and not w.db_calls()


@pytest.mark.parametrize("role", ["", "Planner", "1planner", "a-b", "..", "a/b", "p" * 33, "planner\n"])
def test_a_role_outside_the_grammar_is_refused(w, role):
    for args in (("acquire", role, "sess-1"), ("release", role, "sess-1"), ("status", role)):
        r = w.ky(*args)
        assert r.rc == 70 and r.f["state"] == "refused" and r.f["role"] == "-", r.line
    assert not w.locks.exists()


@pytest.mark.parametrize("args", [(), ("acquire",), ("acquire", "planner"), ("acquire", "planner", "s", "extra"),
                                  ("release", "planner"), ("child", "planner", "s"), ("status",),
                                  ("status", "planner", "s"), ("steal", "planner", "s"), ("--help",)])
def test_usage_errors_are_64_and_touch_nothing(w, args):
    r = w.ky(*args)
    assert r.rc == 64 and r.f["state"] == "usage" and "usage" in r.err
    assert not w.locks.exists()


def test_an_unidentifiable_holder_is_refused_and_nothing_is_written(w):
    for mode in ("fail", "shell", "garbage", "gone"):   # ancestry unreadable · nothing but shells up to pid 1
        w.ps_mode(os.getpid(), mode)
        r = w.ky("acquire", "planner", "sess-1", **w.hook())
        assert r.rc == 70 and r.f["state"] == "refused" and r.f["pid"] == "-" and r.line.endswith(" test_hook=ps")
        assert not w.locks.exists() or os.listdir(w.locks) == []


# ───────────────────────── 2. a live holder is never displaced; exactly one of many gets it ─────────────────────────

def test_a_second_live_instance_is_refused_75_and_the_lock_is_unchanged(w):
    a, b = w.agent(), w.agent()
    assert a.ky("acquire", "planner", a.ctl).rc == 0
    before = w.tree()
    r = b.ky("acquire", "planner", b.ctl)
    assert r.rc == 75 and r.f == {"role": "planner", "state": "live", "holder": a.ctl, "pid": str(a.pid)}
    assert a.ctl in r.err
    r = w.ky("acquire", "planner", "sess-cockpit")
    assert r.rc == 75 and r.f["state"] == "live" and r.f["holder"] == a.ctl
    assert w.tree() == before and not w.litter() and not w.db_calls()
    assert a.ask(op="holds", run=str(w.run), role="planner", id=a.ctl) == [True, None]


def test_a_live_cockpit_is_refused_76_and_the_lock_is_unchanged(w):
    a, b = w.agent(), w.agent()
    assert a.ky("acquire", "planner", "sess-A").rc == 0 and w.owner()["holder_kind"] == "cockpit"
    before = w.tree()
    r = b.ky("acquire", "planner", b.ctl)
    assert r.rc == 76 and r.f == {"role": "planner", "state": "cockpit", "holder": "sess-A", "pid": str(a.pid)}
    r = b.ky("acquire", "planner", "sess-B")
    assert r.rc == 76 and r.f["state"] == "cockpit"
    assert w.tree() == before and not w.litter() and not w.db_calls()


def test_a_live_owner_record_without_holder_kind_or_child_reads_as_a_non_cockpit(w):
    p, pid, start = w.sleeper()                 # as kyaction.py writes it: neither holder_kind nor child
    w.put({"session_or_run_id": "ACT-1", "pid": pid, "pgid": pid, "process_start": start, "acquired_at": "x"})
    w.age()
    before = w.tree()
    r = w.ky("acquire", "planner", "sess-1")
    assert r.rc == 75 and r.f == {"role": "planner", "state": "live", "holder": "ACT-1", "pid": str(pid)}
    assert w.ky("status", "planner").f["state"] == "live" and w.tree() == before


def test_the_same_holder_acquiring_again_is_told_it_holds_it_and_nothing_is_rewritten(w):
    assert w.ky("acquire", "planner", "sess-1").rc == 0
    before = w.tree()
    r = w.ky("acquire", "planner", "sess-1")
    assert r.rc == 0 and r.f == {"role": "planner", "state": "acquired", "holder": "sess-1", "pid": str(os.getpid()),
                                 "already_held": "1"}
    assert w.tree() == before
    r = w.ky("acquire", "planner", "sess-2")    # the same process under another session id is not the owner
    assert r.rc == 76 and w.tree() == before


@pytest.mark.parametrize("stale", [False, True])
def test_of_many_concurrent_acquirers_exactly_one_gets_the_lock(w, stale):
    agents = [w.agent() for _ in range(8)]
    for round_no in range(3):
        if stale:
            pid, start = w.dead()
            w.put(owner_doc("CTL-OLD-%d" % round_no, pid, start))
        gate, results = threading.Barrier(len(agents)), {}

        def go(i, a):
            gate.wait()
            results[i] = a.ky("acquire", "planner", "sess-%d-%d" % (round_no, i))

        threads = [threading.Thread(target=go, args=(i, a)) for i, a in enumerate(agents)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(120)
        assert len(results) == len(agents)
        codes = sorted(r.rc for r in results.values())
        assert codes.count(0) == 1 and set(codes) <= {0, 75, 76}, codes
        winner = next(i for i, r in results.items() if r.rc == 0)
        assert w.owner()["session_or_run_id"] == "sess-%d-%d" % (round_no, winner)
        assert w.owner()["pid"] == agents[winner].pid and not w.litter()
        took = [r.f["took_over"] for r in results.values() if "took_over" in r.f]
        assert took in ([], ["CTL-OLD-%d" % round_no][:stale]) and ("took_over" not in results[winner].f) <= (not took)
        assert agents[winner].ky("release", "planner", "sess-%d-%d" % (round_no, winner)).rc == 0
    assert len(w.db_calls()) == 3               # one per release, none for a takeover or a refusal


# ───────────────────────── 3. positively gone → taken over, verified after the rename ─────────────────────────

def test_a_reused_pid_with_another_start_time_is_not_the_holder(w):
    p, pid, start = w.sleeper()                 # the pid is alive — but it is not the process that took the lock
    assert start != ANOTHER_START
    w.put(owner_doc("CTL-OLD-1", pid, ANOTHER_START))
    assert w.ky("status", "planner").f["state"] == "gone"
    r = w.ky("acquire", "planner", "sess-1")
    assert r.rc == 0 and r.f == {"role": "planner", "state": "acquired", "holder": "sess-1", "pid": str(os.getpid()),
                                 "took_over": "CTL-OLD-1"}
    assert w.owner()["session_or_run_id"] == "sess-1" and w.owner()["pid"] == os.getpid()
    assert p.poll() is None                     # nothing was ever sent to the process now wearing that pid
    assert not w.litter() and not w.db_calls()  # a takeover never runs the database step


def test_a_gone_owner_is_taken_over_also_as_a_zombie_also_with_a_gone_child(w):
    pid, start = w.dead()
    w.put({"session_or_run_id": "ACT-9", "pid": pid, "process_start": start})      # kyaction.py's shape
    r = w.ky("acquire", "planner", "sess-1")
    assert r.rc == 0 and r.f["took_over"] == "ACT-9"
    assert w.ky("release", "planner", "sess-1").rc == 0
    z = subprocess.Popen(["/bin/sleep", "600"], start_new_session=True, stdin=subprocess.DEVNULL)
    w.children.append(z)
    zstart = lstart(z.pid)
    z.kill()                                    # our own child, not reaped: a zombie
    for _ in range(200):
        if ps_stat(z.pid).startswith("Z"):
            break
        time.sleep(0.05)
    assert ps_stat(z.pid).startswith("Z")
    w.put(owner_doc("CTL-ZOMBIE-1", z.pid, zstart))
    r = w.ky("acquire", "planner", "sess-2")
    assert r.rc == 0 and r.f["took_over"] == "CTL-ZOMBIE-1"
    assert w.ky("release", "planner", "sess-2").rc == 0
    cpid, cstart = w.dead()                     # the child's leader is gone and its group has no member
    w.put(owner_doc("CTL-OLD-2", pid, start, child={"run_id": "RUN-1", "pid": cpid, "pgid": cpid,
                                                    "process_start": cstart}))
    assert w.ky("status", "planner").f["state"] == "gone"
    r = w.ky("acquire", "planner", "sess-3")
    assert r.rc == 0 and r.f["took_over"] == "CTL-OLD-2" and w.owner()["child"] is None
    assert len(w.db_calls()) == 2 and not w.litter()


@pytest.mark.parametrize("at_call,how", [(1, "seen before anything is moved"), (2, "put back after the rename")])
def test_a_lock_changing_hands_between_judgement_and_rename_is_left_to_its_new_owner(w, at_call, how):
    pid, start = w.dead()
    w.put(owner_doc("CTL-OLD-1", pid, start))
    b = w.agent()                               # the new owner: a live process, with its true start identity
    theirs = json.dumps(owner_doc(b.ctl, b.pid, b.start), indent=1, sort_keys=True) + "\n"
    (w.ctl / "swap.src").write_text(theirs)
    (w.ctl / "swap.dst").write_text(str(w.lock() / "owner.json"))
    w.ps_mode(pid, "swap %d" % at_call)         # the lock changes hands while the old owner's liveness is being read
    r = w.ky("acquire", "planner", "sess-1", **w.hook())
    assert int((w.ctl / ("%d.calls" % pid)).read_text()) == at_call, how
    assert r.rc == 75 and r.f["state"] == "live" and r.f["holder"] == b.ctl and r.f["pid"] == str(b.pid)
    assert "took_over" not in r.f and r.line.endswith(" test_hook=ps")
    assert (w.lock() / "owner.json").read_text() == theirs and os.listdir(w.lock()) == ["owner.json"]
    assert not w.litter() and not w.db_calls()
    assert b.ask(op="holds", run=str(w.run), role="planner", id=b.ctl) == [True, None]


# ───────────────────────── 4. unknown is never taken over, never removed by age ─────────────────────────

def _bare(w):
    w.lock().mkdir(parents=True)


def _raw(text):
    return lambda w: w.put(None, raw=text) and None


def _unreadable(w):
    pid, start = w.dead()
    w.put(owner_doc("CTL-OLD-1", pid, start))
    (w.lock() / "owner.json").chmod(0)


def _pid(value):
    return lambda w: w.put(owner_doc("CTL-OLD-1", value, ANOTHER_START)) and None


def _live_start(value):
    def build(w):
        p, pid, _ = w.sleeper()
        w.put(owner_doc("CTL-OLD-1", pid, value))
    return build


def _ps(mode):
    def build(w):
        pid, start = w.dead()                   # really gone — but ps is not allowed to say so
        w.put(owner_doc("CTL-OLD-1", pid, start))
        w.ps_mode(pid, mode)
        return w.hook()
    return build


def _child(make):
    def build(w):
        pid, start = w.dead()
        w.put(owner_doc("CTL-OLD-1", pid, start, child=make(w)))
    return build


def _child_alive(w):
    p, pid, start = w.sleeper()
    return {"run_id": "RUN-1", "pid": pid, "pgid": pid, "process_start": start}


def _child_unconfirmed(w):
    p, pid, start = w.sleeper()                 # alive, and its recorded start cannot be compared
    return {"run_id": "RUN-1", "pid": pid, "pgid": pid, "process_start": None}


def _child_group_alive(w):
    leader, start = w.orphan_group()
    return {"run_id": "RUN-1", "pid": leader, "pgid": leader, "process_start": start}


def _child_init_group(w):
    pid, start = w.dead()
    return {"run_id": "RUN-1", "pid": pid, "pgid": 1, "process_start": start}


def _child_ps_failing(w):
    def build(world):
        pid, start = world.dead()
        cpid, cstart = world.dead()
        world.put(owner_doc("CTL-OLD-1", pid, start, child={"run_id": "RUN-1", "pid": cpid, "pgid": cpid,
                                                            "process_start": cstart}))
        world.ps_mode(cpid, "fail")
        return world.hook()
    return build(w)


UNKNOWN = {
    "a bare mkdir lock": _bare,
    "owner.json is not JSON": _raw("{not json"),
    "owner.json is empty": _raw(""),
    "owner.json is not an object": _raw("[1, 2]\n"),
    "owner.json cannot be read": _unreadable,
    "pid null": _pid(None),
    "pid a string": _pid("4242"),
    "pid a boolean": _pid(True),
    "pid zero": _pid(0),
    "pid negative": _pid(-5),
    "pid a float": _pid(4242.0),
    "alive, start identity empty": _live_start(""),
    "alive, start identity missing": _live_start(None),
    "alive, start identity not comparable": _live_start("sometime last week"),
    "ps failing": _ps("fail"),
    "ps answering nonsense": _ps("garbage"),
    "ps hanging": _ps("hang"),
    "gone owner, child pending": _child(lambda w: "pending"),
    "gone owner, child unidentified (text)": _child(lambda w: "RUN-1"),
    "gone owner, child unidentified (empty)": _child(lambda w: {}),
    "gone owner, child unidentified (no pid)": _child(lambda w: {"run_id": "RUN-1", "pid": None, "pgid": None,
                                                                 "process_start": None}),
    "gone owner, child alive": _child(_child_alive),
    "gone owner, child alive and unconfirmed": _child(_child_unconfirmed),
    "gone owner, child leader gone but its group has a member": _child(_child_group_alive),
    "gone owner, child group is pid 1": _child(_child_init_group),
    "gone owner, child ps failing": _child_ps_failing,
}


@pytest.mark.parametrize("case", sorted(UNKNOWN))
def test_an_unknown_owner_is_never_taken_over_however_old(w, case):
    hook = UNKNOWN[case](w) or {}
    w.age()
    before = w.tree()
    r = w.ky("acquire", "planner", "sess-1", **hook)
    assert r.rc == 77 and r.f["state"] == "unknown" and "took_over" not in r.f, (r.line, r.err)
    assert r.err.strip() and r.line.endswith(" test_hook=ps") == bool(hook)
    if case != "ps hanging":                    # (one ps timeout is enough for the suite)
        s = w.ky("status", "planner", **hook)
        assert s.rc == 0 and s.f["state"] == "unknown"
        rel = w.ky("release", "planner", "sess-1", **hook)
        assert rel.rc == 73 and rel.f["state"] == "not_owner"
    assert w.tree() == before and not w.litter() and not w.db_calls()


def test_an_unreadable_lock_directory_is_unknown_never_free(w):
    assert os.geteuid() != 0
    w.locks.mkdir()
    w.locks.chmod(0)
    try:
        s = w.ky("status", "planner")
        assert s.rc == 0 and s.f["state"] == "unknown"
        r = w.ky("acquire", "planner", "sess-1")
        assert r.rc != 0 and r.f["state"] not in ("acquired", "free", "gone", "released")
    finally:
        w.locks.chmod(0o755)
    assert os.listdir(w.locks) == []


# ───────────────────────── 5. release: only proven database removal buries the lock (KU-02) ─────────────────────────

def test_release_runs_the_database_step_once_with_the_identity_and_only_then_the_lock_is_gone(w):
    assert w.ky("acquire", "planner", "sess-1").rc == 0
    r = w.ky("release", "planner", "sess-1")
    assert r.rc == 0 and r.f == {"role": "planner", "state": "released", "holder": "sess-1", "pid": str(os.getpid())}
    assert w.db_calls() == ["close --session sess-1 scratch=%s" % w.scratch]
    assert not w.lock().exists() and not w.litter()
    assert w.ky("status", "planner").f["state"] == "free"
    a = w.agent()                               # … and as kyloop.py calls it
    assert a.ky("acquire", "planner", a.ctl).rc == 0
    r = a.ky("release", "planner", a.ctl)
    assert r.rc == 0 and r.f["state"] == "released" and not w.lock().exists()
    assert w.db_calls()[1:] == ["close --session %s scratch=%s" % (a.ctl, w.scratch)]


def test_release_by_anyone_but_the_recorded_owner_is_73_and_never_runs_the_database_step(w):
    r = w.ky("release", "planner", "sess-1")    # no lock at all
    assert r.rc == 73 and r.f["state"] == "not_owner" and r.f["holder"] == "-"
    a = w.agent()
    assert a.ky("acquire", "planner", a.ctl).rc == 0
    before = w.tree()
    b = w.agent()
    for r in (w.ky("release", "planner", a.ctl),            # the owner's id, from a process that is not the owner
              b.ky("release", "planner", a.ctl),
              b.ky("release", "planner", b.ctl),            # another controller
              a.ky("release", "planner", "sess-x"),         # the owner process, under an id it did not record
              w.ky("release", "planner", "sess-1")):
        assert r.rc == 73 and r.f["state"] == "not_owner" and r.f["holder"] == a.ctl, r.line
    assert w.tree() == before and not w.db_calls() and not w.litter()


def test_release_is_refused_when_the_recorded_start_is_not_the_callers(w):
    pid, _ = me()                               # this pid, this id — but another process's start identity
    w.put(owner_doc("sess-1", pid, ANOTHER_START, kind="cockpit"))
    before = w.tree()
    r = w.ky("release", "planner", "sess-1")
    assert r.rc == 73 and r.f["state"] == "not_owner"
    r = w.ky("child", "planner", "sess-1", "pending")
    assert r.rc == 73 and r.f["state"] == "not_owner"
    assert w.tree() == before and not w.db_calls()


@pytest.mark.parametrize("case", ["failing", "missing", "hanging", "no scratch", "relative scratch", "odd exit"])
def test_release_without_proven_database_removal_keeps_the_lock(w, case):
    assert w.ky("acquire", "planner", "sess-1").rc == 0
    before = w.tree()
    drop, over, ran = (), {}, 1
    if case == "failing":
        (w.fleet / "local_db.mode").write_text("fail")
    elif case == "odd exit":
        (w.fleet / "local_db.mode").write_text("something else")
    elif case == "missing":
        (w.fleet / "local_db.sh").rename(w.fleet / "local_db.sh.away")
        ran = 0
    elif case == "hanging":
        (w.fleet / "local_db.mode").write_text("hang")
        over = {"KY_LOCK_DB_TIMEOUT_S": "1.5"}
    elif case == "no scratch":
        drop, ran = ("KY_SCRATCH",), 0
    else:
        over, ran = {"KY_SCRATCH": "scratch"}, 0
    t0 = time.monotonic()
    r = w.ky("release", "planner", "sess-1", drop=drop, **over)
    assert r.rc == 74 and r.f == dict({"role": "planner", "state": "kept", "holder": "sess-1",
                                       "pid": str(os.getpid())},
                                      **({"test_hook": "db_timeout"} if case == "hanging" else {})), (r.line, r.err)
    assert "sess-1" in r.err and "databases" in r.err                 # names the session whose databases remain
    assert w.tree() == before and not w.litter() and len(w.db_calls()) == ran
    assert w.ky("status", "planner").f["state"] == "cockpit"
    if case == "hanging":
        assert time.monotonic() - t0 < 60
        step = int((w.fleet / "local_db.pid").read_text())
        for _ in range(200):                    # the step this call started was stopped, with its whole group
            if ps_stat(step) == "":
                break
            time.sleep(0.05)
        assert ps_stat(step) == ""
        with pytest.raises(ProcessLookupError):
            os.killpg(step, 0)
    # the lock is still the caller's: once removal is proven, the same call releases it
    if case == "missing":
        (w.fleet / "local_db.sh.away").rename(w.fleet / "local_db.sh")
    (w.fleet / "local_db.mode").write_text("ok")
    r = w.ky("release", "planner", "sess-1")
    assert r.rc == 0 and r.f["state"] == "released" and not w.lock().exists()
    assert len(w.db_calls()) == ran + 1


def test_the_database_step_defaults_to_the_one_beside_the_script(w):
    copy = w.fleet / "kylock.sh"
    copy.write_bytes(KYLOCK.read_bytes())
    copy.chmod(0o755)
    assert w.ky("acquire", "planner", "sess-1", script=copy, drop=("KY_FLEET",)).rc == 0
    r = w.ky("release", "planner", "sess-1", script=copy, drop=("KY_FLEET",))
    assert r.rc == 0 and w.db_calls() == ["close --session sess-1 scratch=%s" % w.scratch]


def test_the_run_directory_defaults_to_run_under_ky_root(w):
    r = w.ky("acquire", "planner", "sess-1", drop=("KY_RUN",))
    assert r.rc == 0 and (w.tmp / "root" / "run" / "locks" / "planner" / "owner.json").is_file()
    assert not w.locks.exists()
    r = w.ky("status", "planner", KY_RUN="relative/run")
    assert r.rc == 64 and r.f["state"] == "usage"


# ───────────────────────────────────────── 6. child and status ─────────────────────────────────────────

def test_child_is_rewritten_atomically_by_the_owner_only(w):
    a = w.agent()
    assert a.ky("acquire", "planner", a.ctl).rc == 0
    first = w.owner()
    r = a.ky("child", "planner", a.ctl, "pending")
    assert r.rc == 0 and r.f == {"role": "planner", "state": "recorded", "holder": a.ctl, "pid": str(a.pid),
                                 "child": "pending"}
    assert w.owner() == dict(first, child="pending") and os.listdir(w.lock()) == ["owner.json"]
    p, pid, start = w.sleeper()
    child = {"run_id": "RUN-20261012T000000Z-planner", "pid": pid, "pgid": pid, "process_start": start}
    r = a.ky("child", "planner", a.ctl, json.dumps(child))
    assert r.rc == 0 and r.f["child"] == child["run_id"] and w.owner() == dict(first, child=child)
    assert a.ask(op="holds", run=str(w.run), role="planner", id=a.ctl) == [True, None]
    before = w.tree()
    b = w.agent()
    for r in (b.ky("child", "planner", a.ctl, "none"), b.ky("child", "planner", b.ctl, "none"),
              w.ky("child", "planner", a.ctl, "none"), a.ky("child", "planner", "sess-x", "none")):
        assert r.rc == 73 and r.f["state"] == "not_owner", r.line
    for bad in ("", "PENDING", "null", "{", "[]", '"pending"', json.dumps(dict(child, extra=1)),
                json.dumps({k: v for k, v in child.items() if k != "pgid"}), json.dumps(dict(child, pid="7")),
                json.dumps(dict(child, pid=True)), json.dumps(dict(child, pgid=0)), json.dumps(dict(child, run_id="")),
                json.dumps(dict(child, process_start=5))):
        r = a.ky("child", "planner", a.ctl, bad)
        assert r.rc == 64 and r.f["state"] == "usage", (bad, r.line)
    assert w.tree() == before
    # a recorded child that is alive keeps a dead owner's lock from being taken over; `none` clears it
    r = a.ky("child", "planner", a.ctl, json.dumps(dict(child, process_start=None)))
    assert r.rc == 0 and w.owner()["child"]["process_start"] is None
    r = a.ky("child", "planner", a.ctl, "none")
    assert r.rc == 0 and r.f["child"] == "none" and w.owner() == first
    assert a.ky("child", "planner", a.ctl, "pending").rc == 0
    a.exit()
    assert w.ky("status", "planner").f["state"] == "unknown"
    assert w.ky("acquire", "planner", "sess-1").rc == 77 and w.owner()["child"] == "pending"
    assert not w.db_calls() and not w.litter()


def test_child_on_a_legacy_owner_record_adds_only_the_child(w):
    pid, start = me()
    legacy = {"session_or_run_id": "sess-1", "pid": pid, "pgid": os.getpgid(0), "process_start": start,
              "acquired_at": "2026-10-12T00:00:00Z"}
    w.put(legacy)
    assert w.ky("child", "planner", "sess-1", "pending").rc == 0
    assert w.owner() == dict(legacy, child="pending")


def test_status_reports_each_state_and_changes_nothing(w):
    r = w.ky("status", "planner")
    assert r.rc == 0 and r.f == {"role": "planner", "state": "free", "holder": "-", "pid": "-"}
    assert not w.locks.exists()                 # not even the locks directory is made
    a = w.agent()
    assert a.ky("acquire", "planner", a.ctl).rc == 0 and a.ky("acquire", "conductor", "sess-A").rc == 0
    pid, start = w.dead()
    w.put(owner_doc("CTL-OLD-1", pid, start), role="veto")
    w.put(owner_doc("CTL-OLD-2", pid, start, child="pending"), role="builder")
    w.lock("bare").mkdir()
    before = w.tree()
    expected = {"planner": ("live", a.ctl, str(a.pid)), "conductor": ("cockpit", "sess-A", str(a.pid)),
                "veto": ("gone", "CTL-OLD-1", str(pid)), "builder": ("unknown", "CTL-OLD-2", str(pid)),
                "bare": ("unknown", "-", "-"), "nobody": ("free", "-", "-")}
    for role, (state, holder, hpid) in expected.items():
        for r in (w.ky("status", role), a.ky("status", role)):
            assert r.rc == 0 and r.f == {"role": role, "state": state, "holder": holder, "pid": hpid}, r.line
    assert w.tree() == before and not w.db_calls()


def test_a_recorded_identity_that_is_not_printable_cannot_forge_the_status_line(w):
    p, pid, start = w.sleeper()
    w.put(owner_doc("x state=free\nkylock: status role=planner state=free", pid, start))
    r = w.ky("status", "planner")
    assert r.rc == 0 and r.f["state"] == "live" and "state=free" not in r.line.split("state=live", 1)[1]


# ───────────────────────────────────────── the tests-only hooks ─────────────────────────────────────────

def test_the_ps_hook_is_announced_on_the_line_and_refused_for_the_real_run_directory(w):
    r = w.ky("status", "planner", **w.hook())
    assert r.rc == 0 and r.f["state"] == "free" and r.line.endswith(" test_hook=ps")
    assert "test_hook" not in w.ky("status", "planner").f
    real = "/Users/Dev/kalayantra/run"
    link = w.tmp / "link"
    link.symlink_to(real)
    # `status` only: even a broken refusal could change nothing there
    for run in (real, real + "/", "/Users/Dev/kalayantra/./run", "/Users/Dev/kalayantra/x/../run", str(link)):
        for over in (w.hook(), {"KY_LOCK_DB_TIMEOUT_S": "1"}):
            r = w.ky("status", "planner", KY_RUN=run, **over)
            assert r.rc == 64 and r.f["state"] == "refused" and "tests-only" in r.err, (run, r.line)
    assert not (w.ctl / ("%d.calls" % os.getpid())).exists()          # the hook was never even run for it
    for over in ({"KY_LOCK_PS": "fake_ps.sh"}, {"KY_LOCK_PS": str(w.tmp / "absent")}, {"KY_LOCK_DB_TIMEOUT_S": "0"},
                 {"KY_LOCK_DB_TIMEOUT_S": "-1"}, {"KY_LOCK_DB_TIMEOUT_S": "soon"}, {"KY_LOCK_DB_TIMEOUT_S": "901"},
                 {"KY_LOCK_DB_TIMEOUT_S": "nan"}):
        r = w.ky("acquire", "planner", "sess-1", **over)
        assert r.rc == 64 and r.f["state"] == "refused", (over, r.line)
    assert not w.locks.exists()
