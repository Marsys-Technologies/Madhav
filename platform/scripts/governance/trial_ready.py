"""TRIAL_READY/1 evaluator (PLAN_A10_1 §2, A10.1 B7): one machine-readable predicate over ONE commit.

    python3 platform/scripts/governance/trial_ready.py --repo <clone-or-worktree> --ref <git ref> --out <trial_ready.json> [--workdir <dir>]

Semantics (the whole point; each is pinned by `__tests__/test_trial_ready.py`):
  * `ready` is true iff all 25 required checks T01..T25 are present and every one reads `true`. A check that is missing from the registry, or whose
    evidence cannot be read, is `null` and counts as NOT ready (§N.7.6). `null` is never a pass.
  * A check reads true only from its DETECTOR'S OWN RUN at the commit: the oracle tests ran and passed, the file at the commit says what it must, the
    database answered the question. Never from a lane state, a PR state or a review verdict (§N.8). A check with no bound detector part is `null`.
  * ONE commit: the ref is resolved to a full sha; the work tree must be at that sha with no modified tracked file before AND after the detectors
    ran, else every check reads null (the evidence cannot be attributed to one commit). The registry itself is read from that commit.
  * Skipped tests are not passes: a test oracle that skipped (a missing database, say) reads null.

The detectors live in the registry (`trial_ready_checks.json`, read at the evaluated commit): per check a list of `parts`, all of which must read true.
Part kinds: `pytest`, `git_file`, `db_sql`, `db_migrations`, `json_keys`, `json_field_eq`, `unbound`. A part reads false when its detector ran and the claim
failed, null when the detector could not run or its evidence is unreadable. A `pytest` part may carry `env` (values may use `{repo}`, the evaluated work tree) and
`deselect` (node ids a known environment-dependent test is excluded by, each named and justified in the registry). A `db_migrations` part either lists `prefixes`
or sets `mode: "all"` (every migration file at the commit must be recorded). A `json_field_eq` part reads a JSON record outside the repository (TR-BIND: T21, T24).
Parts combine three-valued: any false -> false; else any null -> null; else true.
A lane that merges adds the binding of its own oracle to the registry in its PR; until then its check is `unbound` and reads null.

The output carries exactly {predicate, head_sha, evaluated_at, checks[{id, claim, value, evidence_ref, sha256}], ready}. The evaluator holds no credential
and prints none: database parts read a loopback DSN from a NAMED environment variable and record only host:port/dbname.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from git_env_scrub import scrubbed  # noqa: E402  (importing it also scrubs this process's repo-locating variables)

PREDICATE = "TRIAL_READY/1"
REQUIRED_IDS: Tuple[str, ...] = tuple("T%02d" % n for n in range(1, 26))
DEFAULT_REGISTRY = "platform/scripts/governance/trial_ready_checks.json"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")
PYTEST_TIMEOUT_S = 1800
DB_TIMEOUT_S = 60
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

Part = Dict[str, Any]
# (value, evidence_ref, digest, detail): value is True / False / None, never anything else
Outcome = Tuple[Optional[bool], Optional[str], Optional[str], str]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _git(repo: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    env = scrubbed()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, env=env, timeout=120, check=check)


def resolve_sha(repo: Path, ref: str) -> Optional[str]:
    try:
        r = _git(repo, "rev-parse", "--verify", "--quiet", "%s^{commit}" % ref)
    except (OSError, subprocess.SubprocessError):
        return None
    sha = r.stdout.decode("utf-8", "replace").strip()
    return sha if r.returncode == 0 and SHA_RE.match(sha) else None


def worktree_state(repo: Path, sha: str) -> Tuple[bool, str]:
    """True iff the work tree's HEAD is `sha` and no tracked file is modified (the tree the detectors run in IS the commit)."""
    try:
        head = _git(repo, "rev-parse", "HEAD").stdout.decode().strip()
        dirty = _git(repo, "status", "--porcelain", "--untracked-files=no")
    except (OSError, subprocess.SubprocessError) as exc:
        return False, "git unreadable: %s" % type(exc).__name__
    if head != sha:
        return False, "work tree HEAD %s is not the evaluated commit %s" % (head[:12], sha[:12])
    if dirty.returncode != 0 or dirty.stdout.strip():
        return False, "work tree has modified tracked files"
    return True, "ok"


def blob(repo: Path, sha: str, path: str) -> Optional[bytes]:
    try:
        r = _git(repo, "show", "%s:%s" % (sha, path))
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def tree_names(repo: Path, sha: str, directory: str) -> Optional[List[str]]:
    try:
        r = _git(repo, "ls-tree", "--name-only", sha, directory.rstrip("/") + "/")
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return [Path(x).name for x in r.stdout.decode("utf-8", "replace").splitlines() if x]


# ── part detectors ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _d_unbound(ctx: "Ctx", part: Part) -> Outcome:
    return None, None, None, "unbound: %s" % part.get("needs", "no detector is bound to this part yet")


def _d_git_file(ctx: "Ctx", part: Part) -> Outcome:
    path = part.get("path")
    ref = "git:%s:%s" % (ctx.sha[:12], path)
    data = blob(ctx.repo, ctx.sha, path) if isinstance(path, str) and path else None
    if data is None:
        return None, ref, None, "file not present at the commit"
    text = data.decode("utf-8", "replace")
    want, forbid = list(part.get("contains", [])), list(part.get("absent", []))
    if not want and not forbid:
        return None, ref, _sha256(data), "git_file part declares nothing to look for"
    ok = all(w in text for w in want) and not any(f in text for f in forbid)
    return ok, ref, _sha256(data), "contains/absent checked"


def _pytest_outcome(junit: Path, rc: int) -> Tuple[Optional[bool], List[List[str]], str]:
    """Read the junit file: false only when a test FAILED; error/skip/collection trouble/no file is null (the oracle did not run to a verdict)."""
    try:
        root = ET.parse(str(junit)).getroot()
    except (OSError, ET.ParseError):
        return None, [], "no readable junit result (pytest exit %d)" % rc
    cases: List[List[str]] = []
    failed = errored = skipped = 0
    for tc in root.iter("testcase"):
        name = "%s::%s" % (tc.get("classname", ""), tc.get("name", ""))
        if tc.find("failure") is not None:
            failed += 1
            cases.append([name, "failed"])
        elif tc.find("error") is not None:
            errored += 1
            cases.append([name, "error"])
        elif tc.find("skipped") is not None:
            skipped += 1
            cases.append([name, "skipped"])
        else:
            cases.append([name, "passed"])
    cases.sort()
    if failed:
        return False, cases, "%d test(s) failed" % failed
    if errored or skipped or rc != 0 or not cases:
        return None, cases, "no verdict: errors=%d skipped=%d exit=%d collected=%d" % (errored, skipped, rc, len(cases))
    return True, cases, "%d passed" % len(cases)


def _d_pytest(ctx: "Ctx", part: Part) -> Outcome:
    tests = [t for t in part.get("tests", []) if isinstance(t, str) and t]
    cwd_rel = part.get("cwd", ".")
    ref = "pytest:%s:%s@%s" % (cwd_rel, ",".join(tests), ctx.sha[:12])
    if not tests:
        return None, ref, None, "pytest part names no test"
    if not ctx.tree_ok:
        return None, ref, None, "work tree is not the commit: %s" % ctx.tree_reason
    for t in tests:                                  # an oracle that is not in the commit is unreadable evidence, not a pass
        if blob(ctx.repo, ctx.sha, ((cwd_rel + "/") if cwd_rel != "." else "") + t.split("::")[0]) is None:
            return None, ref, None, "oracle %s is not present at the commit" % t.split("::")[0]
    cwd = ctx.repo / cwd_rel
    out = ctx.workdir / ("pytest-%s" % _sha256(ref.encode())[:12])
    shutil.rmtree(str(out), ignore_errors=True)
    out.mkdir(parents=True)
    junit = out / "junit.xml"
    deselect = [d for d in part.get("deselect", []) if isinstance(d, str) and d]
    cmd = [ctx.python, "-m", "pytest", "-p", "no:cacheprovider", "--basetemp=%s" % (out / "tmp"), "--junitxml=%s" % junit, "-q", *tests]
    for d in deselect:
        cmd += ["--deselect", d]
    env = scrubbed()
    env["TMPDIR"] = str(out)
    for k, v in (part.get("env") or {}).items():
        env[str(k)] = str(v).replace("{repo}", str(ctx.repo))
    try:
        r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, timeout=int(part.get("timeout_s", PYTEST_TIMEOUT_S)))
        rc = r.returncode
    except (OSError, subprocess.SubprocessError) as exc:
        return None, ref, None, "pytest could not run: %s" % type(exc).__name__
    value, cases, detail = _pytest_outcome(junit, rc)
    return value, ref, _sha256(_canon({"tests": tests, "deselect": deselect, "cases": cases})), detail


def _loopback_dsn(spec: Part) -> Tuple[Optional[str], Optional[str], str]:
    """(dsn, credential-free label, reason). Never remote, never printed: only host:port/dbname leaves this function."""
    name = spec.get("dsn_env")
    dsn = os.environ.get(name, "") if isinstance(name, str) and name else ""
    if not dsn:
        return None, None, "%s is not set" % (name or "dsn_env")
    try:
        u = urlsplit(dsn)
        host, port, db = u.hostname, u.port, (u.path or "").lstrip("/")
    except ValueError:
        return None, None, "DSN is not a URL"
    label = "db:%s:%s/%s" % (host, port, db)
    if host not in LOOPBACK_HOSTS:
        return None, label, "refuses a non-loopback database"
    return dsn, label, "ok"


def _psql() -> Optional[str]:
    found = shutil.which("psql")
    if found:
        return found
    for cand in sorted(Path("/opt/homebrew/opt").glob("postgresql@*/bin/psql"), reverse=True):
        return str(cand)
    return None


def _run_sql(dsn: str, sql: str) -> Tuple[Optional[str], str]:
    exe = _psql()
    if not exe:
        return None, "psql not found"
    env = scrubbed()
    env["PGOPTIONS"] = "-c default_transaction_read_only=on"         # an evaluator reads, it never writes
    try:
        r = subprocess.run([exe, "-X", "-q", "-tA", "-v", "ON_ERROR_STOP=1", "--dbname", dsn, "-c", sql],
                           env=env, capture_output=True, timeout=DB_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "psql could not run: %s" % type(exc).__name__
    if r.returncode != 0:
        return None, "database not readable (psql exit %d)" % r.returncode
    return r.stdout.decode("utf-8", "replace").strip(), "ok"


def _d_db_sql(ctx: "Ctx", part: Part) -> Outcome:
    dsn, label, why = _loopback_dsn(part)
    ref = label or "db:unconfigured"
    sql = part.get("sql")
    if dsn is None or not isinstance(sql, str) or not sql.strip():
        return None, ref, None, why if dsn is None else "db_sql part has no sql"
    out, why = _run_sql(dsn, sql)
    if out is None or out == "":
        return None, ref, None, why if out is None else "the query returned no row"
    return out == str(part.get("expect", "t")), ref, _sha256(_canon({"sql": sql, "out": out})), "answered"


def _d_db_migrations(ctx: "Ctx", part: Part) -> Outcome:
    """Every migration file at the commit whose name starts with one of `prefixes` (or, with `mode: "all"`, EVERY `.sql` file in `dir`) must exist AND be recorded
    in `_migrations_applied` (platform/scripts/migrate.ts TRACKER_DDL). A prefix with no file at the commit reads false: the commit's list and the ledger differ.
    `all` presumes a lane DB built with the protected files applied (TR-BIND B4): a protected file that was skipped reads as missing, never as fine."""
    dsn, label, why = _loopback_dsn(part)
    ref = label or "db:unconfigured"
    mode = part.get("mode", "prefixes")
    prefixes = [p for p in part.get("prefixes", []) if isinstance(p, str) and p]
    names = tree_names(ctx.repo, ctx.sha, part.get("dir", "platform/migrations"))
    if mode not in ("prefixes", "all") or dsn is None or names is None or (mode == "prefixes" and not prefixes):
        return None, ref, None, why if dsn is None else "migration list at the commit is unreadable or the part declares nothing to compare"
    wanted: List[str] = []
    if mode == "all":
        wanted = sorted(n for n in names if n.endswith(".sql"))
        if not wanted:                                    # an empty list at the commit is no evidence that the ledger is complete
            return None, ref, None, "the commit lists no migration file"
    else:
        for p in prefixes:
            hit = sorted(n for n in names if n.startswith(p) and n.endswith(".sql"))
            if not hit:
                return False, ref, _sha256(_canon({"prefixes": prefixes, "files": []})), "no migration file %s* at the commit" % p
            wanted.extend(hit)
    out, why = _run_sql(dsn, "SELECT filename FROM _migrations_applied ORDER BY filename")
    if out is None:
        return None, ref, None, why
    applied = set(out.splitlines())
    missing = [w for w in wanted if w not in applied]
    return not missing, ref, _sha256(_canon({"mode": mode, "wanted": wanted, "missing": missing})), "%d of %d missing" % (len(missing), len(wanted))


def _d_json_keys(ctx: "Ctx", part: Part) -> Outcome:
    """An allocation ledger (outside the repository) must record each key under `object` with a non-empty value."""
    path = part.get("path")
    ref = "file:%s" % path
    try:
        data = Path(path).read_bytes()
        obj = json.loads(data.decode("utf-8"))
        node = obj[part.get("object", "allocated")]
    except (OSError, TypeError, ValueError, KeyError, AttributeError):
        return None, ref, None, "ledger unreadable"
    keys = [str(k) for k in part.get("keys", [])]
    if not keys or not isinstance(node, dict):
        return None, ref, _sha256(data), "json_keys part has nothing to read"
    return all(bool(node.get(k)) for k in keys), ref, _sha256(data), "ledger read"


def _dig(obj: Any, dotted: str) -> Tuple[bool, Any]:
    for key in dotted.split("."):
        if not isinstance(obj, dict) or key not in obj:
            return False, None
        obj = obj[key]
    return True, obj


def _d_json_field_eq(ctx: "Ctx", part: Part) -> Outcome:
    """A JSON record outside the repository (a readiness report, a verdict) must hold each named field with the declared value. `equals_head: true` compares the
    field with the commit the evaluator resolved, so a record made for ANY other head reads false; `{head}` in `path` names a per-head file. A missing or
    unparsable file, a missing field and a JSON null all read null (no evidence); a present field with another value (or another type: 1 is not true) reads false."""
    raw = part.get("path")
    path = raw.replace("{head}", ctx.sha) if isinstance(raw, str) else None
    ref = "file:%s" % path
    fields = [f for f in part.get("fields", []) if isinstance(f, dict) and isinstance(f.get("field"), str) and f["field"]]
    try:
        data = Path(path).read_bytes()                    # type: ignore[arg-type]
        obj = json.loads(data.decode("utf-8"))
    except (OSError, TypeError, ValueError):
        return None, ref, None, "record unreadable"
    if not fields or any(("equals" in f) == bool(f.get("equals_head")) for f in fields):
        return None, ref, _sha256(data), "json_field_eq part declares each field with exactly one of equals / equals_head"
    verdicts: List[Optional[bool]] = []
    for f in fields:
        found, got = _dig(obj, f["field"])
        want = ctx.sha if f.get("equals_head") else f["equals"]
        if not found or got is None:
            verdicts.append(None)
        else:
            verdicts.append(type(got) is type(want) and got == want)
    return combine(verdicts), ref, _sha256(data), "%d field(s) read" % len(fields)


DETECTORS = {
    "unbound": _d_unbound,
    "git_file": _d_git_file,
    "pytest": _d_pytest,
    "db_sql": _d_db_sql,
    "db_migrations": _d_db_migrations,
    "json_keys": _d_json_keys,
    "json_field_eq": _d_json_field_eq,
}


class Ctx:
    def __init__(self, repo: Path, sha: str, workdir: Path, python: str, tree_ok: bool, tree_reason: str):
        self.repo, self.sha, self.workdir, self.python = repo, sha, workdir, python
        self.tree_ok, self.tree_reason = tree_ok, tree_reason


def combine(values: List[Optional[bool]]) -> Optional[bool]:
    """Three-valued AND: a false wins, then a null; true needs at least one part and every part true. An empty list is null, never true."""
    if any(v is False for v in values):
        return False
    if not values or any(v is not True for v in values):
        return None
    return True


def run_part(ctx: Ctx, part: Any) -> Outcome:
    fn = DETECTORS.get(part.get("kind")) if isinstance(part, dict) else None
    if fn is None:
        return None, None, None, "unknown detector kind"
    try:
        value, ref, digest, detail = fn(ctx, part)
    except Exception as exc:                              # a detector that blows up has not run to a verdict
        return None, None, None, "detector raised %s" % type(exc).__name__
    return (True if value is True else False if value is False else None), ref, digest, detail


def run_check(ctx: Ctx, spec: Dict[str, Any]) -> Dict[str, Any]:
    parts = spec.get("parts")
    results = [run_part(ctx, p) for p in parts] if isinstance(parts, list) else []
    value = combine([r[0] for r in results])
    refs = [r[1] for r in results if r[1]]
    digests = [{"part": i, "sha256": r[2]} for i, r in enumerate(results)]
    return {"id": spec.get("id"), "claim": spec.get("claim"), "value": value,
            "evidence_ref": "; ".join(refs) if refs else None,
            "sha256": _sha256(_canon(digests)) if results and all(r[2] for r in results) else None}


def load_registry(repo: Path, sha: str, rel: str) -> Dict[str, Dict[str, Any]]:
    """id -> spec, from the registry AT THE COMMIT. A duplicated id is poisoned (None): two detectors for one claim is not a detector."""
    data = blob(repo, sha, rel)
    if data is None:
        return {}
    try:
        checks = json.loads(data.decode("utf-8"))["checks"]
    except (ValueError, KeyError, TypeError):
        return {}
    out: Dict[str, Any] = {}
    for c in checks if isinstance(checks, list) else []:
        cid = c.get("id") if isinstance(c, dict) else None
        if isinstance(cid, str):
            out[cid] = None if cid in out else c
    return out


def evaluate(repo: Path, ref: str, workdir: Path, python: Optional[str] = None, registry: str = DEFAULT_REGISTRY,
             now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    repo = Path(repo)
    sha = resolve_sha(repo, ref)
    if sha is None:
        raise ValueError("cannot resolve %r to a commit in %s" % (ref, repo))
    workdir = Path(workdir).resolve()                     # a pytest part runs with another cwd: a relative scratch path would put its junit file somewhere else (null)
    workdir.mkdir(parents=True, exist_ok=True)
    tree_ok, reason = worktree_state(repo, sha)
    ctx = Ctx(repo, sha, workdir, python or sys.executable, tree_ok, reason)
    specs = load_registry(repo, sha, registry)

    checks: List[Dict[str, Any]] = []
    for cid in list(REQUIRED_IDS) + sorted(i for i in specs if i not in REQUIRED_IDS):
        spec = specs.get(cid)
        if spec is None:                                  # absent (or duplicated) in the registry: the check cannot read true
            checks.append({"id": cid, "claim": None, "value": None, "evidence_ref": None, "sha256": None})
        else:
            checks.append(run_check(ctx, spec))

    stable, _ = worktree_state(repo, sha)
    if not stable:                                        # the detectors moved or dirtied the tree: nothing can be attributed to one commit
        for c in checks:
            c["value"] = None
    stamp = (now or datetime.datetime.now(datetime.timezone.utc)).astimezone(datetime.timezone.utc)
    return {"predicate": PREDICATE, "head_sha": sha, "evaluated_at": stamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "checks": checks, "ready": is_ready(checks)}


def is_ready(checks: List[Dict[str, Any]]) -> bool:
    by_id: Dict[str, int] = {}
    for c in checks:
        by_id[c["id"]] = by_id.get(c["id"], 0) + 1
    return all(by_id.get(i) == 1 for i in REQUIRED_IDS) and all(c["value"] is True for c in checks)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True, help="a local clone or worktree checked out at --ref")
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out", required=True, help="where trial_ready.json is written")
    ap.add_argument("--workdir", help="scratch for detector runs (default: next to --out)")
    ap.add_argument("--python", help="interpreter that runs pytest parts (default: this one)")
    ap.add_argument("--registry", default=DEFAULT_REGISTRY)
    args = ap.parse_args(argv)
    out = Path(args.out)
    try:
        out.unlink()                                      # a stale ready:true from an earlier commit must never survive a failed run
    except FileNotFoundError:
        pass
    try:
        result = evaluate(Path(args.repo), args.ref, Path(args.workdir) if args.workdir else out.parent / (out.stem + ".work"),
                          args.python, args.registry)
    except ValueError as exc:
        print("trial_ready: %s" % exc, file=sys.stderr)
        return 2
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(out))
    n_true = sum(1 for c in result["checks"] if c["value"] is True)
    print("trial_ready: %s head=%s true=%d/%d ready=%s" % (PREDICATE, result["head_sha"][:12], n_true, len(result["checks"]), result["ready"]))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
