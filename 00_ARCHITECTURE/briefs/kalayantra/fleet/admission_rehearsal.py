#!/usr/bin/env python3
"""KĀLA-YANTRA admission rehearsal (PLAN_A10_1 §8 SW2; A10.1 addition 1): the FINAL request templates through the REAL validators on an isolated fixture.

    python3 -I admission_rehearsal.py --sandbox DIR --staged TEMPLATES/staged --sql TEMPLATES/sql [--repo PATH] [--main-ref origin/main] [--repin] [--out DIR]

What is REAL (read from the repository's `--main-ref`, never from a working tree):
  executor.py            its own `validate()`, `request_digest`, `dry_run_check`, `signer_acceptance_problem`, `lease_live`, `apply_generated_overlay` (loaded from main's bytes)
  executor_ops.json      the operations table (kinds, enabled, requesters, allowed_args, needs)
  head_operation.py      the head-change policy, exec'd by the executor from the request's `reviewed_commit` (`git show`)
  readback_sql.sh        main's script, run on the sandbox: its own SQL-digest refusal (it stops at "SQL digest mismatch" before any connection)
  backup_v5_small_test_job.py + v5_small_test_shared.py   main's scoped-backup argument parser, scope files and pinned scope digests
  provenance_inventory   the A5 D-33 generated-overlay generator the executor runs in a production tree (`apply_generated_overlay`, generate + --check)
What is a STAND-IN (every one is named in the report's `stand_ins`): the D-FLIP event in the sandbox ledger, the ACTIVE lease row on the sandbox
`origin/campaign-coordination`, a verifier lane's acceptance receipt (written by the harness, JUDGED by the executor's own `signer_acceptance_problem`), the dry-run
receipts of completed dry runs (no executor ran them; built with the executor's digest rules), the capability set (`--capabilities`), and the token inputs of the templates.

Isolation: the sandbox is a directory the caller names. The executor module is loaded with KY_ROOT inside it and KY_SOURCE_REPO = a sandbox git repository that only
BORROWS main's objects (objects/info/alternates; read-only) and carries refs the harness made. Nothing is written to /Users/Dev/kalayantra, to the source repository, or
to a database: the sandbox must not lie inside the live KY_ROOT or inside the source repository (refused), and `Rehearsal.assert_isolated()` re-checks every executor path.

Gates, in order; ALL are evaluated, the first problem is the primary reason (a refusal for the wrong reason proves nothing):
  render   a template token has no input / the SQL template does not exist                               -> completion_missing | render_missing
  executor the real validate()                                                                            -> kind_disabled | requester_not_allowed | reviewed_commit_not_on_main | completion_missing | ...
  pin      reviewed_commit and every source_binding digest equal what main holds now                      -> stale_pin
  sql      readback_sql: main's script accepts the file digest the request cites                          -> sql_sha256_mismatch
  scope    backup_snapshot: a scope is named, the script's parser takes it, its digest is pinned          -> scope_missing | scope_unknown | scope_mismatch
           (SR-A12-BACKUP-REMOVAL: the gate stays for a template that names a backup_snapshot; its negative controls retired with the dump)
  overlay  production kinds: the executor's generated-overlay generator builds and checks at the commit  -> overlay_absent
The executor itself does NOT check source_binding pins and admits any reviewed_commit that is an ancestor of main: stale pins are refused by the pin gate here (the
report shows `executor_alone` for every case so that stays visible).

Negative controls (`controls()`): one clean base template per claim, ONE planted defect each; a control passes iff the base is ADMITTED and the defect is REFUSED with the
named code as the primary reason. A control whose defect is ADMITTED is the harness FLAG `VALIDATOR_ADMITS` (exit 1): that is how a validator that admits a stale pin shows.
Stdlib only; Python 3.9 compatible (the executor is).
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
FLEET_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet"
EXEC_REL = FLEET_REL + "/executor.py"
OPS_REL = FLEET_REL + "/executor_ops.json"
HEAD_REL = FLEET_REL + "/head_operation.py"
COORD_REL = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
SIDECAR_REL = "platform/python-sidecar"
GENERATED_REL = "platform/src/generated"
OVERLAY_MODULE_REL = SIDECAR_REL + "/pipeline/orchestrator/provenance_inventory.py"
SCRIPTS_REL = "platform/scripts"
READBACK_REL = FLEET_REL + "/readback_sql.sh"
LIVE_KY_ROOT = Path("/Users/Dev/kalayantra")
MARKER = ".admission-rehearsal-sandbox"
REPO_LOCATING_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")
ALL_CAPS = {"layer_verifier": True, "builder": True, "owner": True, "pgenv": True, "gcloud": True, "none": True}
WINDOW_SCOPE = "w5w6_union"          # the scope of the flip window's one dump (PLAN_A10_1 §7; M-W56-6)
SCOPE_KINDS = ("backup_snapshot", "backup_restore_verify")
TOKEN = re.compile(r"@([A-Z0-9]+):([A-Za-z0-9_:.-]+)@")
# production kind -> (its dry-run kind, the FIRE input that carries the receipt reference, the reference shape). Other `accepted_*` inputs are opaque to the executor.
LINKS = {
    "publish_head": ("publish_head_dryrun", "dry_run_receipt", "path"),
    "rollback_head": ("rollback_head_dryrun", "dry_run_receipt", "path"),
    "orchestrator_rebuild": ("orchestrator_rebuild_dryrun", "accepted_dryrun_receipt", "name"),
    "scheduler_pause": ("scheduler_pause_dryrun", "accepted_pause_dryrun_receipt", "name"),
    "scheduler_resume": ("scheduler_resume_dryrun", "accepted_resume_dryrun_receipt", "name"),
    "layer_verify": ("layer_verify_dryrun", "accepted_verify_dryrun_receipt", "name"),
    "layer_publish": ("layer_publish_dryrun", "accepted_publish_dryrun_receipt", "name"),
    "layer_rollback": ("layer_rollback_dryrun", "accepted_rollback_dryrun_receipt", "name"),
    "orchestrator_rebuild_teardown": ("orchestrator_rebuild_teardown_dryrun", "accepted_teardown_dryrun_receipt", "name"),
}
# kinds that cite something else already admitted: a cancel is admitted only for a rebuild in flight (SR-CANCEL-LANE)
PREREQ = {"orchestrator_rebuild_cancel": ["orchestrator_rebuild"], "orchestrator_rebuild_cancel_dryrun": ["orchestrator_rebuild"]}
COMPLETION_PUBLISHERS = ("publish_head_completions", "publish_teardown_completions")   # called from the executor's main loop (M-W56-16; SR-TEARDOWN-COMPLETION)
# the executor's refusal texts -> the named reason codes of this report (first match wins; anything else is `executor_other`)
EXECUTOR_CODES = (
    (r"is not enabled", "kind_disabled"),
    (r"may not request", "requester_not_allowed"),
    (r"reviewed_commit is not merged to main", "reviewed_commit_not_on_main"),
    (r"names a different reviewed_commit", "reviewed_commit_mismatch"),
    (r"dryrun_receipt .* required|dry-run_receipt_required|dry-run_receipt_missing|dry run did not COMPLETE|dry-run receipt|has no enabled read-only dry-run|dry-run_exact_scope|rollback_requires_original", "completion_missing"),
    (r"capability_missing", "capability_missing"),
    (r"disallowed args", "args_not_allowed"),
    (r"unknown kind", "kind_unknown"),
    (r"pre-acceptance receipt|approval|attestation", "acceptance_problem"),
    (r"lease is not", "lease_not_live"),
)


SCRIPT_CACHE: dict = {}       # (object store, main) -> the scoped-backup modules loaded from main's platform/scripts (or None)
OVERLAY_CACHE: dict = {}      # (interpreter, commit, tree) -> None | (code, reason): the overlay build takes ~40 s and depends on nothing else


class Refused(Exception):
    """The rehearsal itself cannot run safely (isolation, missing input): never a verdict about a template."""


class Missing(Exception):
    """A template token has no input (or a template file is absent). `code` names the reason when it is not the plain `render_missing`."""

    def __init__(self, what: str, code: str = "render_missing"):
        super().__init__(what)
        self.code = code


# ---- git (read-only against the source repository; scrubbed environment) ----------------------------------------------------------------------------------------------------
def clean_env(extra: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in REPO_LOCATING_VARS}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1",
               GIT_AUTHOR_NAME="rehearsal", GIT_AUTHOR_EMAIL="rehearsal@invalid", GIT_COMMITTER_NAME="rehearsal", GIT_COMMITTER_EMAIL="rehearsal@invalid",
               GIT_AUTHOR_DATE="2026-01-01T00:00:00Z", GIT_COMMITTER_DATE="2026-01-01T00:00:00Z")
    env.update(extra or {})
    return env


def git(repo, *args: str, data: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(["git", "-C", str(repo), *args], input=data, capture_output=True, env=clean_env(), timeout=300)
    if check and p.returncode: raise Refused("git " + " ".join(args[:3]) + " failed: " + p.stderr.decode(errors="replace")[:200])
    return p


def sha256(data) -> str:
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def in_work_tree(path: Path) -> bool:
    """True when `path` (which need not exist yet) lies inside any git work tree: a rehearsal never builds scratch inside a project folder."""
    probe = Path(path).resolve()
    while not probe.exists(): probe = probe.parent
    return subprocess.run(["git", "-C", str(probe), "rev-parse", "--is-inside-work-tree"], capture_output=True, env=clean_env(), timeout=30).returncode == 0


class Verdict:
    """One request through the gates. `problems` is ordered (executor, pin, sql, scope, overlay); `executor_alone` is the real validate() on its own."""

    def __init__(self, req: dict | None):
        self.req = req
        self.problems: list = []
        self.executor_alone = None       # None = not asked, "ADMITTED" or the executor's text
        self.unmeasured: list = []        # gates that could not be measured here: an honest null, never a pass

    def add(self, gate: str, code: str, reason: str) -> None:
        self.problems.append({"gate": gate, "code": code, "reason": reason})

    @property
    def admitted(self) -> bool: return not self.problems
    @property
    def code(self) -> str: return self.problems[0]["code"] if self.problems else "ADMITTED"
    @property
    def reason(self) -> str: return self.problems[0]["reason"] if self.problems else ""

    def as_dict(self) -> dict:
        return {"admitted": self.admitted, "code": self.code, "reason": self.reason, "problems": self.problems, "executor_alone": self.executor_alone,
                "unmeasured": self.unmeasured}


class Rehearsal:
    """A sandbox, the executor loaded from main's bytes on it, and the gates."""

    def __init__(self, sandbox, repo, main_ref: str = "origin/main", capabilities: dict | None = None, python: str | None = None,
                 window_scope: str = WINDOW_SCOPE, run_overlay: bool = True):
        self.sandbox = Path(sandbox).resolve()
        self.repo = Path(repo).resolve()
        if inside(self.sandbox, LIVE_KY_ROOT) or self.sandbox == self.repo or inside(self.sandbox, self.repo) or in_work_tree(self.sandbox):
            raise Refused(f"the sandbox {self.sandbox} lies inside the live KY_ROOT or inside a git work tree (a project folder): name a scratch folder")
        self.caps = dict(ALL_CAPS if capabilities is None else capabilities)
        self.window_scope = window_scope
        self.run_overlay = run_overlay
        self.python = python or (str(LIVE_KY_ROOT / "venv/bin/python") if (LIVE_KY_ROOT / "venv/bin/python").exists() else sys.executable)
        for var in REPO_LOCATING_VARS: os.environ.pop(var, None)          # the executor under test runs git from this process environment
        os.environ["GIT_OPTIONAL_LOCKS"] = "0"
        if self.sandbox.exists():
            if any(self.sandbox.iterdir()) and not (self.sandbox / MARKER).exists(): raise Refused(f"{self.sandbox} exists, is not empty and is not a rehearsal sandbox (no {MARKER}); refusing to empty it")
            shutil.rmtree(self.sandbox)
        self.sandbox.mkdir(parents=True)
        (self.sandbox / MARKER).write_text("admission_rehearsal sandbox: safe to delete\n")
        self.main = git(self.repo, "rev-parse", "--verify", main_ref + "^{commit}").stdout.decode().strip()
        self.objects = self._common_objects()
        self.ky = self.sandbox / "ky"
        self.git_dir = self.sandbox / "git"
        self.stand_ins = {}
        self.notes: list = []
        self._make_git()
        self.ex = self._load_executor()
        self.ho = self.ex.head_policy({"reviewed_commit": self.main})      # head_operation.py of main, exactly as the executor reads it
        self.assert_isolated()
        self._make_ledger()
        self.table_asis = self.ex.load_table()
        if not self.table_asis: raise Refused(f"{OPS_REL} is not readable at {main_ref}")
        self.table = self.table_asis
        self.now = dt.datetime.now(dt.timezone.utc)
        self.inputs = self._fixture_inputs()

    # ---- sandbox ----------------------------------------------------------------------------------------------------------------------------------------------------------
    def _common_objects(self) -> Path:
        common = Path(git(self.repo, "rev-parse", "--git-common-dir").stdout.decode().strip())
        return ((self.repo / common) if not common.is_absolute() else common).resolve() / "objects"

    def blob(self, path: str, rev: str | None = None) -> bytes | None:
        p = git(self.git_dir if (self.git_dir / ".git").exists() else self.repo, "show", f"{rev or self.main}:{path}", check=False)
        return p.stdout if p.returncode == 0 else None

    def _tree_commit(self, files: dict, parents=(), message: str = "rehearsal fixture", repo=None) -> str:
        """A commit holding `files` {path: bytes}, built with plumbing in the sandbox repository (no index, no worktree)."""
        def mktree(entries):
            return git(repo or self.git_dir, "mktree", data=("\n".join(entries) + "\n").encode()).stdout.decode().strip()
        def build(prefix: str, items: dict) -> str:
            entries, dirs = [], {}
            for path, data in sorted(items.items()):
                head, _, rest = path.partition("/")
                if rest: dirs.setdefault(head, {})[rest] = data
                else: entries.append(f"100644 blob {git(repo or self.git_dir, 'hash-object', '-w', '--stdin', data=data).stdout.decode().strip()}\t{head}")
            for head, sub in sorted(dirs.items()): entries.append(f"040000 tree {build(prefix + head + '/', sub)}\t{head}")
            return mktree(entries)
        tree = build("", files)
        args = ["commit-tree", tree, "-m", message]
        for parent in parents: args += ["-p", parent]
        return git(repo or self.git_dir, *args).stdout.decode().strip()

    def _make_git(self) -> None:
        """origin.git (bare; ONLY the fixture lease branch) and the clone the executor uses as its git handle. The executor's `lease_live` runs `git fetch origin campaign-coordination`, so an
        origin must exist; it is kept tiny so that fetch is fast. The clone BORROWS main's objects (objects/info/alternates, read-only) and gets origin/main from a ref the harness sets."""
        origin = self.sandbox / "origin.git"
        git(self.sandbox, "init", "-q", "--bare", "-b", "main", str(origin))
        git(self.sandbox, "init", "-q", "-b", "main", str(self.git_dir))
        info = self.git_dir / ".git" / "objects" / "info"
        info.mkdir(parents=True, exist_ok=True)
        (info / "alternates").write_text(str(self.objects) + "\n")
        if git(self.git_dir, "cat-file", "-t", self.main, check=False).stdout.strip() != b"commit": raise Refused(f"commit {self.main} is not readable through the borrowed object store")
        self.lease_id = "REHEARSAL-LEASE"
        ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
        expiry = (dt.datetime.now(ist) + dt.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
        lease = (f"# rehearsal fixture\n\n## 1. Leases\n\n| lease | a | b | c | expires | state |\n|---|---|---|---|---|---|\n| {self.lease_id} | x | y | z | {expiry} | ACTIVE |\n\n## 2. Other\n")
        git(origin, "update-ref", "refs/heads/campaign-coordination", self._tree_commit({COORD_REL: lease.encode()}, message="lease fixture", repo=origin))
        git(self.git_dir, "remote", "add", "origin", str(origin))
        git(self.git_dir, "fetch", "-q", "origin", "campaign-coordination")
        git(self.git_dir, "update-ref", "refs/remotes/origin/main", self.main)
        if git(self.git_dir, "rev-parse", "origin/main").stdout.decode().strip() != self.main: raise Refused("the sandbox origin/main is not the pinned main")
        self.stand_ins["lease"] = f"ACTIVE lease row {self.lease_id} on the sandbox origin/campaign-coordination (expires in 8 h)"

    def _load_executor(self):
        src = self.blob(EXEC_REL)
        if src is None: raise Refused(f"{EXEC_REL} is not readable at {self.main}")
        self.executor_sha256 = sha256(src)
        path = self.sandbox / "exec" / "executor.py"
        path.parent.mkdir(parents=True)
        path.write_bytes(src)
        saved = {k: os.environ.get(k) for k in ("KY_ROOT", "KY_SOURCE_REPO")}
        os.environ.update(KY_ROOT=str(self.ky), KY_SOURCE_REPO=str(self.git_dir))
        try:
            spec = importlib.util.spec_from_file_location("ky_admission_rehearsal_" + uuid.uuid4().hex[:8], path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            for k, v in saved.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
        mod.PY = self.python
        for d in (mod.REQ, mod.REC, mod.DONE, mod.ACC, mod.INFLIGHT, mod.TMP, mod.KY_ROOT / "logs", mod.OPS / "sql", mod.OPS / "verdicts"): d.mkdir(parents=True, exist_ok=True)
        return mod

    def assert_isolated(self) -> None:
        ex = self.ex
        for name in ("KY_ROOT", "RUN", "OPS", "REQ", "REC", "DONE", "ACC", "INFLIGHT", "TMP", "FENCE", "SEEN", "PACK_ALLOWLIST"):
            p = getattr(ex, name)
            if not inside(Path(p), self.sandbox) or inside(Path(p), LIVE_KY_ROOT): raise Refused(f"executor path {name}={p} is not inside the sandbox")
        if Path(ex.GIT).resolve() != self.git_dir.resolve(): raise Refused(f"executor git handle {ex.GIT} is not the sandbox repository")

    def _make_ledger(self) -> None:
        self.event = {"kind": "decision", "actor": "steward", "decision": "D-FLIP", "state": "delegated", "outcome": "approved",
                      "detail": "REHEARSAL fixture for the request-shape check; not a decision", "ts": self.iso(dt.datetime.now(dt.timezone.utc))}
        (self.ex.OPS.parent / "EVENTS.jsonl").write_text(json.dumps(self.event) + "\n")
        self.stand_ins["d_flip_event"] = "a fixture D-FLIP approved event in the sandbox run/EVENTS.jsonl (the real ledger is never read)"
        self.stand_ins["acceptance"] = "a verifier lane's acceptance receipt written by the harness; JUDGED by the executor's own signer_acceptance_problem"
        self.stand_ins["dryrun_receipts"] = "completed dry-run receipts built with the executor's digest rules (no executor ran them)"
        self.stand_ins["capabilities"] = "capability set: " + ", ".join(f"{k}={v}" for k, v in sorted(self.caps.items()))

    @staticmethod
    def iso(t: dt.datetime) -> str: return t.replace(microsecond=0).isoformat()

    def _fixture_inputs(self) -> dict:
        now, h = self.now, lambda s: sha256(s)
        uu = lambda s: str(uuid.uuid5(uuid.NAMESPACE_URL, "ky-rehearsal/" + s))
        expected = {"generation": "3.0", "flipped_at": "2026-10-15T09:30:00+00:00", "flipped_by": "REHEARSAL", "evidence_ref": "REHEARSAL"}
        plan = "ka_yojaka,ka_vedha_gochara,ka_gochara_resonance,ka_gochara,ka_sangam,ka_vighnakara"
        return {
            "SEAL": {"expected_head": expected, "manifest_id": uu("manifest"), "change_at": self.iso(now + dt.timedelta(minutes=5)), "decision_event_sha256": self.ho["sha"](self.event)},
            "FIRE": {"lease_id": self.lease_id, "expires_at": self.iso(now + dt.timedelta(hours=6)), "backup_label": "rehearsal_label", "backup_capture_sha256": h("capture"),
                     "backup_gate_verdict_sha256": h("gate"), "resume_by": (now + dt.timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "preflight_receipt": {"name": "REHEARSAL-preflight.json", "sha256": h("pre")},
                     "scope_hash_receipts": [{"name": "REHEARSAL-scope-a.json", "sha256": h("a")}, {"name": "REHEARSAL-scope-b.json", "sha256": h("b")}],
                     "abort_or_stall_verdict": {"name": "REHEARSAL-stall.json", "sha256": h("stall")}},
            "K9IN": {"run_id": uu("run"), "generation": "REHEARSAL-K9-GEN", "assets": plan, "independently_derived_digest": h("digest"), "expected_head": "NONE",
                     "published_generation": "REHEARSAL-K9-GEN", "rollback_generation": "REHEARSAL-PREV", "teardown_scope_sha256": h("scope"), "owner_authority_line": "REHEARSAL-AUTH"},
        }

    # ---- tables ------------------------------------------------------------------------------------------------------------------------------------------------------------
    def provision(self, kinds) -> dict:
        """The table with `kinds` enabled in memory: what the table reads after the kinds a plan provisions are merged (a what-if, never a verdict about main)."""
        table = copy.deepcopy(self.table_asis)
        for kind in kinds:
            if kind in table: table[kind]["enabled"] = True
        return table

    # ---- rendering (token substitution; the same rules as the pre-stage tools/render.py) ---------------------------------------------------------------------------------------
    def _need(self, ns: str, key: str):
        try: return self.inputs[ns][key]
        except (KeyError, TypeError): raise Missing(f"{ns}.{key}")

    def _head_change(self, req: dict) -> dict:
        if req["kind"].startswith("rollback_"): return self._need("SEAL", "rollback_head_change")
        return {"expected_head": self._need("SEAL", "expected_head"), "target": {"generation": "5.0", "manifest_id": self._need("SEAL", "manifest_id")}, "change_at": self._need("SEAL", "change_at")}

    def _resolve(self, ns: str, key: str, req: dict):
        if ns == "SEAL":
            if key == "head_change": return self._head_change(req)
            hc = self._head_change(req)
            if key == "expected_head_sha256": return self.ho["sha"](hc["expected_head"])
            if key == "manifest_id": return hc["target"]["manifest_id"] or "none"
            if key == "previous_head": return hc["target"]["generation"]
        return self._need(ns, key)

    def _sub(self, value, req: dict):
        if isinstance(value, dict): return {k: self._sub(v, req) for k, v in value.items()}
        if isinstance(value, list): return [self._sub(v, req) for v in value]
        if isinstance(value, str):
            m = TOKEN.fullmatch(value)
            if m and m.group(1) in ("SEAL", "FIRE", "K9IN"): return self._resolve(m.group(1), m.group(2), req)
        return value

    def _render_sql(self, text: str) -> str:
        for m in set(re.findall(r"@K94:([A-Za-z0-9_]+)@", text)):
            if m not in self.inputs["K9IN"]: raise Missing("K9IN." + m)
            text = text.replace(f"@K94:{m}@", str(self.inputs["K9IN"][m]))
        text = text.replace("@PIN:main@", self.main)
        left = sorted(set(re.findall(r"@[A-Z0-9]+:[A-Za-z0-9_:.-]+@", text)))
        if left: raise Missing("unresolved SQL placeholders " + ", ".join(left))
        if "\\" in text or not re.match(r"\s*(SELECT|WITH)\b", text, re.I): raise ValueError("unsafe readback SQL")
        return text

    def render(self, template: dict, sql_dir: Path | None, repin: bool = False) -> dict:
        """A submittable body from a staged template. The reviewed_commit is NOT overwritten unless `repin` (a stale pin must stay visible to the pin gate)."""
        req = copy.deepcopy(template)
        if "sql_file" in (req.get("args") or {}):
            name = req["args"]["sql_file"].rsplit("/", 1)[-1]
            tpl = (Path(sql_dir) / (name + ".tpl")) if sql_dir else None
            if not (tpl and tpl.is_file()): raise Missing(f"SQL template {name}", "scope_missing" if "scope" in name else "sql_template_missing")
            text = req_sql = tpl.read_text()
            if name.startswith("w6-j6-"): text = text.rstrip("\n") + f"\n-- reviewed_commit: {self.main}\n"       # fill_at_submit.render_sql
            else: text = self._render_sql(req_sql)                                                                   # k9/fill.render_sql
            digest = sha256(text)
            (self.ex.OPS / "sql").mkdir(parents=True, exist_ok=True)
            (self.ex.OPS / "sql" / name).write_text(text)
            req["args"]["sql-sha256"] = digest
            req["sql_sha256"] = digest
        out = self._sub(req, req)
        if repin: self.repin(out)
        if out.get("acceptance_receipt"): out["acceptance_receipt"] = str(self.ex.ACC / Path(out["acceptance_receipt"]).name)      # a template may name the live acceptance folder: never read it
        left = sorted(set(a + ":" + b for a, b in TOKEN.findall(json.dumps(out))))
        if left: raise Missing("unresolved " + ", ".join(left))
        return out

    def repin(self, req: dict) -> dict:
        """Re-derive reviewed_commit and the source_binding digests from main (what tools/repin.sh does after a main move)."""
        req["reviewed_commit"] = self.main
        sb = req.get("source_binding")
        if isinstance(sb, dict):
            row = self.table_asis.get(req["kind"]) or {}
            script = sb.get("script") or row.get("script")
            if "reviewed_commit" in sb: sb["reviewed_commit"] = self.main
            if script and "script_sha256" in sb and self.blob(script) is not None: sb["script_sha256"] = sha256(self.blob(script))
            if "executor_ops_row_sha256" in sb and row: sb["executor_ops_row_sha256"] = sha256(json.dumps(row, sort_keys=True))
            if "executor_ops_sha256" in sb: sb["executor_ops_sha256"] = sha256(self.blob(OPS_REL))
            if isinstance(sb.get("migration_sha256"), dict):
                for p in sb["migration_sha256"]:
                    if self.blob(p) is not None: sb["migration_sha256"][p] = sha256(self.blob(p))
        return req

    # ---- gates ------------------------------------------------------------------------------------------------------------------------------------------------------------
    def pin_problem(self, req: dict) -> tuple | None:
        """(code, reason) when a pin is not what main holds NOW; None when every pin binds. Measured against the sandbox's origin/main, file by file."""
        if req.get("reviewed_commit") != self.main:
            return "stale_pin", f"reviewed_commit {str(req.get('reviewed_commit'))[:12]} is not main {self.main[:12]}"
        sb = req.get("source_binding")
        if not isinstance(sb, dict): return None
        if sb.get("reviewed_commit", self.main) != self.main: return "stale_pin", f"source_binding.reviewed_commit {str(sb['reviewed_commit'])[:12]} is not main {self.main[:12]}"
        row = self.table_asis.get(req.get("kind")) or {}
        script = sb.get("script") or row.get("script")
        if "script_sha256" in sb:
            data = self.blob(script) if script else None
            if data is None: return "stale_pin", f"source_binding script {script} does not exist at main"
            if sha256(data) != sb["script_sha256"]: return "stale_pin", f"source_binding.script_sha256 of {script} differs from main's file"
        if "executor_ops_row_sha256" in sb and sha256(json.dumps(row, sort_keys=True)) != sb["executor_ops_row_sha256"]:
            return "stale_pin", f"source_binding.executor_ops_row_sha256 of {req.get('kind')} differs from main's table row"
        if "executor_ops_sha256" in sb and sha256(self.blob(OPS_REL)) != sb["executor_ops_sha256"]:
            return "stale_pin", "source_binding.executor_ops_sha256 differs from main's table"
        if isinstance(sb.get("migration_sha256"), dict):
            for path, digest in sorted(sb["migration_sha256"].items()):
                data = self.blob(path)
                if data is None or sha256(data) != digest: return "stale_pin", f"source_binding.migration_sha256 of {path} differs from main's file"
        return None

    def sign(self, req: dict) -> dict:
        """A verifier lane's acceptance of exactly this request (stand-in; the executor judges it)."""
        acc = {"result": "ACCEPTED", "operation_id": req["operation_id"], "by": "v1", "reviewed_commit": req.get("reviewed_commit"), "ts": self.iso(dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=5)),
               "request_sha256": self.ex.request_digest(req), "rows": {}, "checks": {"restore_verified": True, "dry_run_passed": True}}
        path = self.ex.ACC / f"{req['operation_id']}.json"
        path.write_text(json.dumps(acc))
        req["acceptance_receipt"] = str(path)
        self.stand_in_owner_go(req)
        return req

    def stand_in_owner_go(self, req: dict) -> None:
        """OWNER-BUILD-GO-REQUIRED-20261023: the executor refuses a century dispatch or a production rebuild without the owner's go file. A rehearsal judges the TEMPLATE, never the owner's yes, so a
        stand-in go bound to exactly this request is written in the sandbox (the executor's own owner_go_problem judges it). An executor without the gate (an older main) has no OWNER_GO_KINDS: nothing is written."""
        if req.get("kind") not in getattr(self.ex, "OWNER_GO_KINDS", ()): return
        self.ex.OWNER_GO_DIR.mkdir(parents=True, exist_ok=True)
        go = {"schema": self.ex.OWNER_GO_SCHEMA, "operation_id": req["operation_id"], "kind": req["kind"], "item_id": req.get("item_id"), "request_sha256": self.ex.request_digest(req),
              "reviewed_commit": req.get("reviewed_commit"), "owner_yes": True, "owner_words": "REHEARSAL stand-in: not the owner's words", "transcript_citation": "rehearsal sandbox (no transcript)",
              "written_by": self.ex.OWNER_GO_WRITER, "written_at": self.iso(dt.datetime.now(dt.timezone.utc))}
        (self.ex.OWNER_GO_DIR / f"{req['operation_id']}.json").write_text(json.dumps(go))
        self.stand_ins["owner_go"] = "a stand-in owner go (run/ops/owner_go) bound to each gated request by the harness; the owner's real yes is never rehearsed and is still required to dispatch"

    def executor_problem(self, req: dict, table: dict) -> str | None:
        try: return self.ex.validate(req, table, self.caps)
        except Exception as exc: return f"HARNESS_EXCEPTION {type(exc).__name__}: {str(exc)[:160]}"

    @staticmethod
    def executor_code(reason: str) -> str:
        for pattern, code in EXECUTOR_CODES:
            if re.search(pattern, reason): return code
        return "executor_other"

    def sql_problem(self, req: dict) -> tuple | None:
        """readback_sql: main's own script judges the file digest the request cites (it refuses before any connection); None = the digest and the file were accepted."""
        args = req.get("args") or {}
        if req.get("kind") != "readback_sql" or "sql_file" not in args: return None
        cited = args.get("sql-sha256") or args.get("sql_sha256")
        if not cited: return "sql_sha256_missing", "the request cites no sql-sha256"
        if req.get("sql_sha256") not in (None, cited): return "sql_sha256_mismatch", "sql_sha256 and args.sql-sha256 differ"
        script = self.sandbox / "exec" / "readback_sql.sh"
        if not script.exists():
            data = self.blob(READBACK_REL)
            if data is None: return "sql_script_absent", f"{READBACK_REL} is not at main"
            script.write_bytes(data)
        pgenv = self.sandbox / "pgenv.sh"
        pgenv.write_text("export PGHOST=127.0.0.1 PGPORT=9 PGCONNECT_TIMEOUT=1 PGUSER=rehearsal\n")     # a closed local port: the script stops at the connection, after its own digest gate
        venv = self.ky / "venv"
        if not venv.exists():
            if (Path(self.python).parent.parent / "pyvenv.cfg").exists(): venv.symlink_to(Path(self.python).parent.parent)
            else:
                (venv / "bin").mkdir(parents=True)
                (venv / "bin" / "python").symlink_to(self.python)
        env = {"PATH": os.environ.get("PATH", ""), "HOME": str(self.sandbox), "KY_ROOT": str(self.ky), "KY_READBACK_PGENV": str(pgenv), "LANG": "C"}
        sql_rel = "run/ops/sql/" + args["sql_file"].rsplit("/", 1)[-1]      # always the sandbox's copy, whatever directory the template names
        p = subprocess.run(["bash", str(script), "--sql-file", sql_rel, "--sql-sha256", str(cited)], capture_output=True, text=True, env=env, timeout=60)
        err = (p.stderr or "").strip()
        if "No module named" in err: return "UNMEASURED", "the sandbox interpreter cannot import the script's driver: " + err.splitlines()[-1][:120]
        for text, code in (("SQL digest mismatch", "sql_sha256_mismatch"), ("SQL digest requires one file and a SHA-256", "sql_sha256_invalid"), ("SQL file not found", "sql_file_missing"),
                           ("must resolve beneath run/ops/sql", "sql_path_refused"), ("backslash is not allowed", "sql_content_refused"), ("one SELECT/WITH statement required", "sql_content_refused")):
            if text in err: return code, err.splitlines()[-1][:160]
        return None      # nothing refused before the connection (which the sandbox cannot make, by design)

    def _scripts(self):
        """main's platform/scripts, extracted once into the sandbox, and the two modules the scoped backup uses (loaded under private names)."""
        key = (str(self.objects), self.main)
        if key in SCRIPT_CACHE: return SCRIPT_CACHE[key]
        tree = self.sandbox / "scripts_tree"
        if self.archive([SCRIPTS_REL], tree) != 0:
            SCRIPT_CACHE[key] = None
            return None
        scripts = tree / SCRIPTS_REL
        before = set(sys.modules)
        sys.path.insert(0, str(scripts))
        try:
            mods = []
            for name in ("backup_v5_small_test_job", "v5_small_test_shared"):
                spec = importlib.util.spec_from_file_location("rehearsal_" + name, scripts / (name + ".py"))
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                mods.append(mod)
            result = tuple(mods)
        except Exception as exc:
            self.notes.append(f"scope gate unmeasured: {type(exc).__name__}: {str(exc)[:120]}")
            result = None
        finally:
            sys.path.remove(str(scripts))
            for k in set(sys.modules) - before: sys.modules.pop(k, None) if k.startswith("rehearsal_") or k == "v5_small_test_shared" else None
        SCRIPT_CACHE[key] = result
        return result

    def scope_problem(self, req: dict) -> tuple | None:
        if req.get("kind") not in SCOPE_KINDS: return None
        scope = (req.get("args") or {}).get("scope")
        if not scope: return "scope_missing", f"{req['kind']} names no scope: the script's default is 'full', the window's dump is '{self.window_scope}'"
        mods = self._scripts()
        if mods is None: return "UNMEASURED", "the scoped-backup script could not be loaded from main"
        backup, shared = mods
        try:
            with contextlib.redirect_stderr(io.StringIO()): backup._parse_args(["--operation", "snapshot", "--label", "rehearsal", "--scope", str(scope), "--dry-run"])
        except SystemExit: return "scope_unknown", f"the script's own parser refuses --scope {scope}"
        if scope == "full": pass
        else:
            try: digest = backup.load_scope(name=scope)["sha256"]
            except Exception as exc: return "scope_unknown", f"scope file for {scope}: {type(exc).__name__}"
            if digest != shared.SCOPED_BACKUP_SCOPE_SHA256S.get(scope): return "scope_unknown", f"scope {scope} is not pinned by the reviewed policy digest"
        if scope != self.window_scope: return "scope_mismatch", f"scope {scope} is not the window's scope {self.window_scope}"
        return None

    def archive(self, paths, dest: Path, commit: str | None = None) -> int:
        dest.mkdir(parents=True, exist_ok=True)
        a = subprocess.Popen(["git", "-C", str(self.git_dir), "archive", commit or self.main, *paths], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=clean_env())
        t = subprocess.run(["tar", "-x", "-C", str(dest)], stdin=a.stdout, capture_output=True)
        a.stdout.close()
        a.wait()
        return a.returncode or t.returncode

    def overlay_tree(self, commit: str, remove: str | None = None) -> Path:
        tree = self.sandbox / "overlay" / (commit[:12] + ("-minus-" + Path(remove).name if remove else ""))
        if tree.exists(): shutil.rmtree(tree)
        if self.archive([SIDECAR_REL, GENERATED_REL], tree, commit) != 0: raise Refused(f"git archive of {SIDECAR_REL} at {commit[:12]} failed")
        if remove: (tree / remove).unlink()
        return tree

    def overlay_problem(self, commit: str, tree: Path | None = None) -> tuple | None:
        """The executor's own `apply_generated_overlay` on a tree of `commit` (generate, then --check in a second process). Cached per commit unless `tree` is given."""
        if not self.run_overlay: return "UNMEASURED", "overlay gate switched off (--skip-overlay)"
        key = (self.python, commit, str(tree) if tree else None)
        if key not in OVERLAY_CACHE:
            root = tree or self.overlay_tree(commit)
            env = {"PATH": os.environ.get("PATH", ""), "HOME": str(self.sandbox), "LANG": "C", "SE_EPHE_PATH": os.environ.get("SE_EPHE_PATH", str(LIVE_KY_ROOT / "ephe"))}
            proof, why = self.ex.apply_generated_overlay(root, commit, env, timeout=300)
            OVERLAY_CACHE[key] = None if proof else ("overlay_absent", "generated overlay refused: " + why)
        return OVERLAY_CACHE[key]

    def judge(self, req: dict, table: dict | None = None, sign: bool = True, overlay_tree: Path | None = None) -> Verdict:
        """Every gate on one request. Production kinds are signed (stand-in) before the executor judges them."""
        table = table or self.table
        v = Verdict(req)
        op = table.get(req.get("kind")) or {}
        body = copy.deepcopy(req)
        if op.get("production") and sign: self.sign(body)
        why = self.executor_problem(body, table)
        v.executor_alone = why or "ADMITTED"
        if why: v.add("executor", self.executor_code(why), why)
        pin = self.pin_problem(req)
        if pin: v.add("pin", *pin)
        for gate, fn in (("sql", self.sql_problem), ("scope", self.scope_problem)):
            r = fn(req)
            if r and r[0] == "UNMEASURED": v.unmeasured.append(f"{gate}: {r[1]}")
            elif r: v.add(gate, *r)
        if op.get("production"):
            rc = str(req.get("reviewed_commit"))
            known = re.fullmatch(r"[0-9a-f]{40}", rc) and git(self.git_dir, "cat-file", "-t", rc, check=False).stdout.strip() == b"commit"
            r = self.overlay_problem(rc if known else self.main, overlay_tree)
            if r and r[0] == "UNMEASURED": v.unmeasured.append(f"overlay: {r[1]}")
            elif r: v.add("overlay", *r)
        return v

    # ---- completion receipts (stand-in; the executor's digest rules) ------------------------------------------------------------------------------------------------------------
    def head_proof(self, req: dict, dry: bool) -> dict:
        ho = self.ho
        retained = {t: {"rows": 1, "sha256": sha256(t)} for t in ho["RETAINED_TABLES"]}
        return dict(schema="ky.head_change/1", status="ROLLED_BACK" if dry else "COMMITTED_AWAITING_READBACK", rollback_confirmed=dry, operation_id=req["operation_id"],
                    request_sha256=ho["request_digest"](req), chart_id=req["chart_id"], reviewed_commit=req["reviewed_commit"], head_change=req["head_change"],
                    before=req["head_change"]["expected_head"], after=ho["replacement"](req), retained_rows_equal=True, retained_before=retained, retained_after=retained)

    def _jdump(self, path: Path, value) -> None: path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

    def fake_completion(self, req: dict) -> dict:
        ex = self.ex
        oid = req["operation_id"]
        proof = self.head_proof(req, True) if req["kind"] == "publish_head_dryrun" or req["kind"] == "rollback_head_dryrun" else None
        out = f"REHEARSAL: no executor ran this request\n{json.dumps(proof or {'status': 'DRY_RUN'}, sort_keys=True)}\n"
        (ex.REC / f"{oid}.output.txt").write_text(out)
        rec = {"kind": req["kind"], "item_id": req["item_id"], "operation_id": oid, "request_sha256": ex.request_digest(req), "reviewed_commit": req["reviewed_commit"],
               "status": "COMPLETED", "exit_code": 0, "output_sha256": sha256(out), "fixture": "REHEARSAL"}
        if proof: rec["head_change"] = proof
        self._jdump(ex.REC / f"{oid}.json", rec)
        self._jdump(ex.DONE / f"{oid}.json", req)
        return rec

    def register_dryrun(self, req: dict) -> None:
        """An ADMITTED `<kind>_dryrun` leaves its completed receipt, and the FIRE input the production twin cites."""
        rec = self.fake_completion(req)
        path = self.ex.REC / f"{req['operation_id']}.json"
        for prod, (dry, key, shape) in LINKS.items():
            if dry == req["kind"]:
                ref = {"path": str(path), "sha256": sha256(path.read_bytes())} if shape == "path" else {"name": path.name, "sha256": sha256(path.read_bytes())}
                self.inputs["FIRE"][key] = ref

    def register_publish(self, req: dict) -> None:
        """An ADMITTED publish_head leaves its committed receipt: the rollback pair's `rollback_of`, restore head and verdict bind it."""
        ex = self.ex
        committed = {"kind": "publish_head", "item_id": req["item_id"], "operation_id": req["operation_id"], "request_sha256": self.ho["request_digest"](req), "status": "AWAITING_READBACK",
                     "head_change": self.head_proof(req, False)}
        path = ex.REC / f"{req['operation_id']}.json"
        self._jdump(path, committed)
        seal = self.inputs["SEAL"]
        seal["rollback_head_change"] = {"expected_head": self.ho["replacement"](req), "restore_head": seal["expected_head"],
                                        "target": {"generation": seal["expected_head"]["generation"], "manifest_id": str(uuid.uuid5(uuid.NAMESPACE_URL, "ky-rehearsal/previous-manifest"))},
                                        "change_at": self.iso(self.now + dt.timedelta(minutes=30))}
        fire = self.inputs["FIRE"]
        fire["rollback_of"] = {"path": str(path), "sha256": sha256(path.read_bytes())}
        verdict = {"schema": "ky.rollback_verdict/1", "verdict": "ROLLBACK", "target": "5.0"}
        vpath = ex.OPS / "verdicts" / "REHEARSAL-verdict.json"
        self._jdump(vpath, verdict)
        fire["verdict"] = {"name": vpath.name, "sha256": sha256(vpath.read_bytes())}

    def register_inflight(self, req: dict) -> None:
        self._jdump(self.ex.INFLIGHT / f"{req['operation_id']}.json", {"kind": req["kind"], "operation_id": req["operation_id"], "args": req.get("args")})
        self.inputs["FIRE"]["inflight_rebuild"] = {"operation_id": req["operation_id"], "run_id": (req.get("args") or {}).get("run-id")}

    # ---- a template set -----------------------------------------------------------------------------------------------------------------------------------------------------
    def run_set(self, staged_dir, sql_dir=None, repin: bool = False, table: dict | None = None) -> list:
        """Every staged template through render + the gates, dry runs first, dependencies resolved by repeating until nothing more renders. Returns rows."""
        table = table or self.table
        loaded = {f.name: json.loads(f.read_text()) for f in sorted(Path(staged_dir).glob("*.json"))}
        wave = lambda t: 2 if any(w in str(t.get("kind")) for w in ("cancel", "rollback", "teardown")) else (1 if (table.get(t.get("kind")) or {}).get("production") else 0)
        templates = dict(sorted(loaded.items(), key=lambda kv: (wave(kv[1]), kv[0])))      # reads and dry runs, then the writes, then the abort paths that cite them
        rows = {name: {"template": name, "kind": t.get("kind"), "operation_id": t.get("operation_id"), "item_id": t.get("item_id"),
                       "staged_pin": t.get("reviewed_commit"), "staged_pin_stale": t.get("reviewed_commit") != self.main} for name, t in templates.items()}
        done: set = set()
        for _ in range(len(templates) + 2):
            progressed = False
            for name, t in templates.items():
                if name in done: continue
                try: req = self.render(t, Path(sql_dir) if sql_dir else None, repin)
                except Missing as exc:
                    rows[name]["verdict"] = {"admitted": False, "code": exc.code, "reason": f"missing {exc}", "problems": [{"gate": "render", "code": exc.code, "reason": f"missing {exc}"}], "executor_alone": None, "unmeasured": []}
                    continue
                except ValueError as exc:
                    rows[name]["verdict"] = {"admitted": False, "code": "render_refused", "reason": str(exc), "problems": [{"gate": "render", "code": "render_refused", "reason": str(exc)}], "executor_alone": None, "unmeasured": []}
                    done.add(name); continue
                v = self.judge(req, table)
                rows[name]["verdict"] = v.as_dict()
                rows[name]["production"] = bool((table.get(req["kind"]) or {}).get("production"))
                done.add(name); progressed = True
                if v.admitted or all(p["gate"] == "pin" for p in v.problems):      # stale-pinned only: still well formed, so its twin is judged on its own pins, not on a cascade
                    if req["kind"].endswith("_dryrun"): self.register_dryrun(req)
                    if req["kind"] == "publish_head": self.register_publish(req)
                    if req["kind"] == "orchestrator_rebuild": self.register_inflight(req)
            if not progressed: break
        # a template still waiting on a token whose producer never ran: say which completion is missing
        for name, row in rows.items():
            v = row.get("verdict")
            if v and v["code"] == "render_missing" and re.search(r"FIRE\.(dry_run_receipt|accepted_\w*dryrun_receipt|rollback_of|verdict)|SEAL\.rollback_head_change", v["reason"]):
                v["code"] = "completion_missing"
                v["problems"][0]["code"] = "completion_missing"
                v["reason"] += " (the completed dry run / committed publish it must cite was not admitted)"
        return list(rows.values())

    # ---- negative controls --------------------------------------------------------------------------------------------------------------------------------------------------
    def wiring(self) -> list:
        """The completion publishers exist AND the executor's main loop calls them (a function nothing calls publishes nothing)."""
        tree = ast.parse(Path(self.ex.__file__).read_text())      # the executor text actually loaded (a planted reversion is visible here)
        defs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        main_fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
        called = {c.func.id for c in ast.walk(main_fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)} if main_fn else set()
        return [{"publisher": p, "defined": p in defs, "called_from_main": p in called, "ok": p in defs and p in called} for p in COMPLETION_PUBLISHERS]

    def controls(self, staged_dir, sql_dir=None, repin: bool = True, only=None) -> list:
        """One clean base per claim, ONE planted defect each. A control is `ok` iff the base is ADMITTED and the defect is REFUSED with the named code as the primary reason.
        `only` limits the run to the named controls (the oracles use it); the base templates are rendered and admitted exactly as in a full run."""
        templates = {}
        for f in sorted(Path(staged_dir).glob("*.json")):
            t = json.loads(f.read_text())
            templates.setdefault(t.get("kind"), (f.name, t))
        results: list = []
        want = lambda name: only is None or name in only

        def base_of(kind: str, table=None, prep=None):
            """Render + admit the first template of `kind` (with its dry-run twin first when it has one); returns (request, verdict) or (None, reason)."""
            if kind not in templates: return None, f"no template of kind {kind} in the set"
            chain = ([LINKS[kind][0]] if kind in LINKS else []) + PREREQ.get(kind, [])
            for dep in chain:
                if dep not in templates: return None, f"no template of kind {dep} in the set (its completion is missing)"
                r, v = base_of(dep, table)
                if r is None: return None, v
                if not v.admitted: return None, f"the dry run it cites ({dep}) is not admitted: {v.code}: {v.reason[:120]}"
            try: req = self.render(templates[kind][1], Path(sql_dir) if sql_dir else None, repin)
            except Missing as exc: return None, f"missing {exc}"
            v = self.judge(req, table)
            if v.admitted and kind.endswith("_dryrun"): self.register_dryrun(req)
            if v.admitted and kind == "publish_head": self.register_publish(req)
            return req, v

        def control(name: str, claim: str, expect: str, kind: str, plant, table_base=None, table_defect=None, sign: bool = True):
            if not want(name): return
            row = {"control": name, "claim": claim, "expect_code": expect, "base_kind": kind}
            if expect == "overlay_absent" and not self.run_overlay:
                row.update(status="NOT_RUN", ok=None, detail="overlay gate switched off (--skip-overlay): an honest null, not a pass"); results.append(row); return
            req, v = base_of(kind, table_base)
            if req is None:
                row.update(status="BASE_UNAVAILABLE", ok=False, detail=v); results.append(row); return
            row["base_admitted"] = v.admitted
            row["base_verdict"] = v.code
            if not v.admitted:
                row.update(status="BASE_NOT_ADMITTED", ok=False, detail=v.reason); results.append(row); return
            bad = copy.deepcopy(req)
            extra = plant(bad) or {}
            if sign: bad.pop("acceptance_receipt", None)
            vb = self.judge(bad, table_defect or table_base, sign=sign, overlay_tree=extra.get("overlay_tree"))
            row.update(defect=extra.get("note", ""), code=vb.code, reason=vb.reason, executor_alone=vb.executor_alone, problems=[p["code"] for p in vb.problems])
            if vb.admitted: row.update(status="VALIDATOR_ADMITS", ok=False)
            elif vb.code != expect: row.update(status="WRONG_REASON", ok=False)
            else: row.update(status="REFUSED", ok=True)
            results.append(row)

        uniq = lambda s: lambda r: r.update(operation_id=r["operation_id"] + ".ctl-" + s, idempotency_key=r.get("idempotency_key", "k") + ".ctl-" + s)

        def stale(r):
            parent = git(self.git_dir, "rev-parse", "--verify", self.main + "~1^{commit}", check=False).stdout.decode().strip()
            if not parent: raise Refused("main has no parent commit to stand for a stale pin")
            uniq("stale")(r); r["reviewed_commit"] = parent
            if isinstance(r.get("source_binding"), dict) and "reviewed_commit" in r["source_binding"]: r["source_binding"]["reviewed_commit"] = parent
            return {"note": f"reviewed_commit set to main~1 ({parent[:12]}), an ancestor of main"}
        control("stale_pin", "a pin older than main is refused", "stale_pin", "readback_sql", stale)

        # SR-A12-BACKUP-REMOVAL: the `scope_missing` and `scope_unknown` controls retired with the dump (no window takes a backup_snapshot any more); `scope_problem`
        # stays for a template that still names one. `overlay_absent` and `reviewed_commit_mismatch` test general admission, so they ride on `orchestrator_rebuild`
        # (a production kind with a dry-run twin) and still refuse for their own reasons.
        def no_overlay(r):
            return {"note": "the reviewed commit's tree without the overlay generator (platform/python-sidecar/.../provenance_inventory.py)",
                    "overlay_tree": self.overlay_tree(r["reviewed_commit"], remove=OVERLAY_MODULE_REL)}
        control("overlay_absent", "a production kind needs a buildable generated overlay", "overlay_absent", "orchestrator_rebuild", no_overlay)

        disabled = [k for k in templates if (self.table_asis.get(k) or {}).get("enabled") is False]
        if want("kind_disabled"):
            if not disabled:
                results.append({"control": "kind_disabled", "claim": "a kind main's table has disabled is refused", "expect_code": "kind_disabled", "status": "NOT_APPLICABLE", "ok": None,
                                "detail": "no template in the set names a kind that main's table has disabled"})
            for n, kind in enumerate(disabled):      # the base is the same kind read from the table with it enabled: the ONE defect is `enabled:false`; the first kind whose base is admitted carries the control
                control("kind_disabled", "a kind main's table has disabled is refused", "kind_disabled", kind, lambda r, kind=kind: {"note": f"{kind} read from main's own table (enabled:false); the base reads the table with it enabled"},
                        table_base=self.provision([kind] + PREREQ.get(kind, [])), table_defect=self.table_asis)
                if results[-1]["status"] not in ("BASE_UNAVAILABLE", "BASE_NOT_ADMITTED") or n == len(disabled) - 1: break
                results.pop()

        def drop_dryrun(r):
            uniq("dry")(r); r.pop("dryrun_receipt", None); return {"note": "dryrun_receipt removed"}
        control("completion_missing_rebuild", "an orchestrator_rebuild cites its completed dry run", "completion_missing", "orchestrator_rebuild", drop_dryrun)

        def drop_dryrun_head(r):
            uniq("dryh")(r); r.pop("dry_run_receipt", None); return {"note": "dry_run_receipt removed"}
        control("completion_missing_flip", "a publish_head cites its completed, rolled-back dry run", "completion_missing", "publish_head", drop_dryrun_head)

        def off_main(r):
            commit = git(self.git_dir, "commit-tree", self.main + "^{tree}", "-p", self.main, "-m", "off-main rehearsal commit").stdout.decode().strip()
            uniq("offmain")(r); r["reviewed_commit"] = commit
            if isinstance(r.get("source_binding"), dict) and "reviewed_commit" in r["source_binding"]: r["source_binding"]["reviewed_commit"] = commit
            return {"note": f"reviewed_commit {commit[:12]} is a child of main that main does not contain"}
        control("reviewed_commit_not_on_main", "a reviewed_commit main does not contain is refused", "reviewed_commit_not_on_main", "orchestrator_rebuild_dryrun", off_main)

        # the acceptance is written for main~1 while the request cites main: sign() uses the request's commit, so the control signs by hand
        def mismatch(r):
            uniq("rcmis")(r)
            body = copy.deepcopy(r)
            self.sign(body)
            path = Path(body["acceptance_receipt"])
            acc = json.loads(path.read_text())
            acc["reviewed_commit"] = git(self.git_dir, "rev-parse", self.main + "~1").stdout.decode().strip()
            path.write_text(json.dumps(acc))
            r["acceptance_receipt"] = str(path)
            return {"note": "the acceptance receipt names main~1, the request names main"}
        control("reviewed_commit_mismatch", "a signed acceptance must name the request's own reviewed_commit", "reviewed_commit_mismatch", "orchestrator_rebuild", mismatch, sign=False)

        def flip_sql(r):
            uniq("sql")(r)
            digest = r["args"]["sql-sha256"]
            flipped = ("0" if digest[0] != "0" else "1") + digest[1:]
            r["args"]["sql-sha256"] = flipped
            r["sql_sha256"] = flipped
            return {"note": "the first hex digit of the cited sql digest flipped"}
        control("sql_sha256_mismatch", "a readback cites the digest of the SQL file it runs", "sql_sha256_mismatch", "readback_sql", flip_sql)

        def outsider(r):
            uniq("req")(r); r["requested_by"] = "outsider-lane"; return {"note": "requested_by = a lane the kind's requesters do not list"}
        control("requester_not_allowed", "only a listed lane requests a kind", "requester_not_allowed", "cloudrun_job_readback" if "cloudrun_job_readback" in templates else "readback_sql", outsider)
        return results


# ---- report ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
def flags(report: dict) -> list:
    out = [f"{c['control']}: {c['status']}" + (f" ({c.get('code')})" if c.get("code") else "") for c in report["controls"] if c.get("ok") is False]
    out += [f"completion publisher {w['publisher']}: defined={w['defined']} called_from_main={w['called_from_main']}" for w in report["wiring"] if not w["ok"]]
    return out


def markdown(report: dict) -> str:
    L = ["# Admission rehearsal", "", f"main `{report['main']}` · executor sha256 `{report['executor_sha256'][:16]}…`", ""]
    L += ["## Verdict", "", "FLAGS: " + ("none — every validator refused its planted defect for the named reason" if not report["flags"] else "; ".join(report["flags"])), ""]
    L += ["## Negative controls (one planted defect each)", "", "| control | claim | expected | got | executor alone | status |", "|---|---|---|---|---|---|"]
    for c in report["controls"]:
        L.append(f"| {c['control']} | {c['claim']} | `{c['expect_code']}` | `{c.get('code', '-')}` | {str(c.get('executor_alone', '-'))[:60]} | **{c['status']}** |")
    L += ["", "## Completion publishers wired into the executor's main loop", ""] + [f"- `{w['publisher']}`: defined={w['defined']}, called from main={w['called_from_main']}" for w in report["wiring"]]
    for name, rows in report.get("sets", {}).items():
        adm = [r for r in rows if r.get("verdict", {}).get("admitted")]
        L += ["", f"## Template set — {name}: {len(adm)} of {len(rows)} admitted", ""]
        reasons: dict = {}
        for r in rows:
            v = r.get("verdict", {})
            if not v.get("admitted"): reasons.setdefault(v.get("code", "?"), []).append(r)
        for code, rs in sorted(reasons.items()):
            L.append(f"- `{code}` × {len(rs)}: " + ", ".join(f"{r['template'].split('.json')[0]}" for r in rs[:12]) + (" …" if len(rs) > 12 else ""))
    L += ["", "## Stand-ins", ""] + [f"- **{k}**: {v}" for k, v in sorted(report["stand_ins"].items())]
    if report.get("notes"): L += ["", "## Notes", ""] + [f"- {n}" for n in report["notes"]]
    return "\n".join(L) + "\n"


def rehearse(args) -> dict:
    caps = None
    if args.capabilities == "live": caps = json.loads((LIVE_KY_ROOT / "run/ops/CAPABILITIES.json").read_text())
    elif args.capabilities not in ("all", None): caps = json.loads(Path(args.capabilities).read_text())
    main = git(args.repo, "rev-parse", "--verify", args.main_ref + "^{commit}").stdout.decode().strip()      # resolved ONCE: origin/main moves while a long rehearsal runs, and every phase must judge the same commit
    fresh = lambda tag: Rehearsal(str(Path(args.sandbox)) + "-" + tag, args.repo, main, caps, python=args.python, run_overlay=not args.skip_overlay)      # one sandbox per phase: receipts never leak between phases
    sql = Path(args.sql) if args.sql else None
    rc = fresh("controls")
    report = {"schema": "ky.admission_rehearsal/1", "main": rc.main, "executor_sha256": rc.executor_sha256, "stand_ins": rc.stand_ins,
              "capabilities": {k: rc.caps[k] for k in sorted(rc.caps)}, "sets": {}}
    report["controls"] = rc.controls(args.staged, sql, repin=True)
    report["wiring"] = rc.wiring()
    notes = list(rc.notes)
    rc_as = fresh("staged")
    report["sets"]["as staged, against main today (stale pins visible)"] = rc_as.run_set(args.staged, sql, repin=False)
    rp = fresh("repinned")
    report["sets"]["repinned to main, main's table as it is"] = rp.run_set(args.staged, sql, repin=True)
    used = {json.loads(f.read_text()).get("kind") for f in Path(args.staged).glob("*.json")}
    provisioned = sorted(k for k, v in rp.table_asis.items() if v.get("enabled") is False and k in used)
    pv = fresh("provisioned")
    report["sets"]["repinned, with " + ", ".join(provisioned) + " enabled (what-if)"] = pv.run_set(args.staged, sql, repin=True, table=pv.provision(provisioned))
    report["notes"] = sorted(set(notes + rc_as.notes + rp.notes + pv.notes))
    report["flags"] = flags(report)
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sandbox", required=True, help="a directory under the job's scratch; emptied and rebuilt (NEVER the live KY_ROOT or the repository)")
    ap.add_argument("--staged", required=True); ap.add_argument("--sql", default=None)
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[3]))
    ap.add_argument("--main-ref", default="origin/main")
    ap.add_argument("--capabilities", default="all", help="all (stand-in: every capability true) | live (read-only copy of the live CAPABILITIES.json) | a JSON file")
    ap.add_argument("--python", default=None, help="interpreter for the overlay generator and the readback script's driver (default: the live venv, else this one)")
    ap.add_argument("--skip-overlay", action="store_true"); ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    try: report = rehearse(a)
    except Refused as exc:
        print("REFUSED:", exc, file=sys.stderr)
        return 2
    out = Path(a.out) if a.out else Path(a.sandbox).parent / (Path(a.sandbox).name + "-report")
    out.mkdir(parents=True, exist_ok=True)
    (out / "REHEARSAL.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    (out / "REHEARSAL.md").write_text(markdown(report))
    print(markdown(report))
    return 1 if report["flags"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
