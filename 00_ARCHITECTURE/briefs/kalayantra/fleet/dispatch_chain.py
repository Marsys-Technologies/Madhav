#!/opt/homebrew/bin/python3
"""A11 dispatch chain — the AUTOMATIC chain from a TR pass to the seal page (SR-A11 / OWNER-ALL-OUT-20261022; PLAN_A10_1 §1 fast main path, §5 seal controller).

One poll per invocation (launchd StartInterval, installed by the cockpit).  stdlib only (+ the sibling `seal_controller`, whose reviewed aggregate detector S5 reuses).
Root CLAUDE.md §N.8: every transition below is gated by a detector over REAL evidence that can read false; a missing or unreadable input is an honest HOLD and no advance.
Speed without lowering a gate: no stage is skipped, no stage advances on a proxy (a PR state, a lane state, an exit code alone), and independent verification is untouched.

THE CHAIN (each poll re-evaluates S0..S5 from evidence, in order, and stops at the first stage whose detector does not read true; markers only make the EMISSIONS exactly-once):
  S0 TRIAL_READY   `trial_ready.json` (platform/scripts/governance/trial_ready.py) at the trial head H: predicate TRIAL_READY/1, exactly T01..T25, every value `true` (recounted here;
                   the file's own `ready` is cross-checked, never trusted), each true check names its evidence;
                   AND precondition `k9_migrations_applied`: 1404_*, 1405_kala_convergence_generation.sql and 1406_kala_obstruction_generation_scope.sql (names read from the repo at H) are all in the
                   target DB's `public._migrations_applied` (executor `migration_readback` receipts; absent from the repo, missing from the ledger or an unreadable ledger = no advance; SR-K9-MIGRATION-WINDOW).
                   -> ACTION arm the 12-class TR (writes the harness command; never runs it).
  S1 TR_PASS_MERGE the TR verdict (`ky.tr_verdict/1`) at H binds THIS trial_ready file by digest, is qualifying (not DIAGNOSTIC), has G-1..G-7 each `true` (recounted; its own verdict is
                   cross-checked) AND the RV-INT part 2 reviewer result is ACCEPTED at H with claims and no blocking finding; the PR (#3841) head is still H, based on main, not a draft.
                   -> ACTION `gh pr merge --auto` (bound to H with --match-head-commit).  Then waits for MERGED.
  S2 MAIN_EQUIV    PR MERGED with merge commit M; M reachable from main (compare API); the required CI workflows are green AT M; the forced image deploy (`deploy.yml`, force_all_services)
                   is a NEW run for M that succeeded; the deployed pipeline image carries M (executor `cloudrun_job_readback` receipt); EQUIVALENCE_RECORD(M) is computed and the decision
                   (`equivalence_record.py compare`, category table) is EQUAL, bound by digest to the TR's record and to M's record.  -> ACTIONS deploy, readback request, record, compare.
  S3 REBIND_ADMIT  executor refreshed to M (CAPABILITIES) + builder/gcloud + production slot free; the v1.7 rebind is evidenced (version, head M, staged digest recomputed, every staged pin M);
                   the admission rehearsal of the FINAL request templates at M is clean (no flags, every control refused its planted defect, every dispatch-path template admitted).
                   -> ACTION century dispatch request (the pack's template, copied byte-for-byte into the executor request queue).
  S4 BUILD_VERIFY  the dispatch receipt is COMPLETED/0 and carries the launch evidence; the Cloud Run execution readback says SUCCEEDED, for this run id and the M image.
                   -> ACTION the sharded verification requests (R8), ALL in the same poll.
  S5 AGG_HANDOFF   every verification receipt COMPLETED/0 at M, and the seal controller's own aggregate detector (`seal_controller.check_aggregate`) reads PASSED.
                   -> ACTION write the adopted-generation file for the seal controller (which pages the surrogate); this program never approves and never seals.

HOLD (any detector false or null): the named reason is written to the status file and PAGEd ONCE per (key, stage, code, reason).  A SOFT hold is a hold whose producer is known to be
in flight (a CI run in progress, a receipt not yet back): same status, but paged only after the stage has been waiting longer than `stall_s`.  Nothing is skipped and nothing is retried
blindly: a non-idempotent action (the deploy dispatch) leaves an INTENT marker before it runs and is never repeated by this program.

MODES: default = EMIT: gh READS run, nothing is mutated; every action is written as a document (`actions/`, `requests/`) and the cockpit performs it.  `--apply` additionally performs the
allow-listed actions this program is authorised to perform itself (listed in ACTIONS with their authority).  `--dry-run` writes NOTHING (no marker, page, action, status) and prints the
would-do sequence.  The harness (TR) and the rebind are never run by this program.  No database, no gcloud, no credential is touched; `gh` uses the cockpit's own login.

Config (JSON `ky.dispatch_chain_config/1`, written by the cockpit) — see DISPATCH_CHAIN_A11.md.  Interpretations (I) are listed there and in result.json.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import seal_controller as sc  # noqa: E402

SCHEMA = "ky.dispatch_chain/1"
CONFIG_SCHEMA = "ky.dispatch_chain_config/1"
REPO_SLUG = "Marsys-Technologies/Madhav"
DEFAULT_CONFIG = "/Users/Dev/kalayantra/run/DISPATCH_CHAIN.json"
DEFAULT_OPS = "/Users/Dev/kalayantra/run/ops"
DEFAULT_ITEM = "A11-DISPATCH-CHAIN"
DEPLOY_WORKFLOW = "deploy.yml"
DEPLOY_PATH = ".github/workflows/deploy.yml"
FLEET = Path(__file__).resolve().parent

TRIAL_READY_PREDICATE = "TRIAL_READY/1"
TRIAL_IDS = tuple("T%02d" % n for n in range(1, 26))            # pinned equal to platform/scripts/governance/trial_ready.py REQUIRED_IDS by a parity test
GATES = tuple("G-%d" % n for n in range(1, 8))                    # G-1..G-7 are the TR's; G-8 is the equivalence (S2)
TR_VERDICT_SCHEMA = "ky.tr_verdict/1"
TR_CLASS_COUNT = 12
RVINT_ITEM = re.compile(r"RV-INT.*(part[-_ ]?2|\bP2\b)", re.I)
REHEARSAL_SCHEMA = "ky.admission_rehearsal/1"
REHEARSAL_SET = "repinned to main, main's table as it is"
REBIND_SCHEMA = "ky.pack_rebind/1"
READBACK_SCHEMA = "ky.cloudrun_readback/1"
LAUNCH_SCHEMA = "ky.century_launch/1"
DECISION_SCHEMA = "ky.equivalence_decision/1"
DISPATCH_KINDS = ("century_dispatch", "orchestrator_rebuild")
VERIFY_KIND = "verification_job"
PRODUCTION_KINDS = DISPATCH_KINDS + (VERIFY_KIND,)
FORBIDDEN_GH_TOKENS = ("--admin", "ci_gate", "data_plane_cutover", "--delete-branch", "--force", "EMERGENCY-OVERRIDE-CI-NOT-GREEN")
CAPS_MAX_AGE_S = 900
STALL_S = 7200
K9_PRECONDITION = "k9_migrations_applied"
K9_MIGRATION_DIR = "platform/migrations"
K9_MIGRATIONS = (("1404", None), ("1405", "1405_kala_convergence_generation.sql"), ("1406", "1406_kala_obstruction_generation_scope.sql"))   # (number, exact name | None = the repo names it)
MIGRATION_LEDGER_HEADER = ["filename", "applied_at", "sha256"]       # readback_sql.sh --migration: SELECT filename, applied_at, sha256 FROM public._migrations_applied

_SHA = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_RUN_UUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")
_EXEC = re.compile(r"[a-z0-9][a-z0-9-]{2,100}")
_LABEL = re.compile(r"[A-Za-z0-9 ._:/-]{1,50}")
_NAME = re.compile(r"[A-Za-z0-9._-]{1,120}\.json")
_TOKEN = re.compile(r"[A-Za-z0-9_./=:,@+{}-]{1,200}")

STAGES = (("S0", "TRIAL_READY"), ("S1", "TR_PASS_MERGE"), ("S2", "MAIN_EQUIVALENCE"), ("S3", "REBIND_ADMIT_DISPATCH"), ("S4", "BUILD_VERIFY_LAUNCH"), ("S5", "AGGREGATE_HANDOFF"))
STAGE_IDS = tuple(s for s, _ in STAGES)

# ── the action catalogue: EVERY action the chain can take, its kind and the authority it rests on ──────────────────────────────────────────────────────────────────────────────
#   kind: harness_command (written, never run) · gh_call · executor_request (a governed request document the executor admits or refuses) · local_tool (read-only, local) · file_write
#   performed_by: "cockpit" = this program only EMITS it; "chain --apply" = this program may run it itself.  retry_safe False = never repeated by this program.
ACTIONS = (
    {"id": "A0.ARM_TR", "stage": "S0", "kind": "harness_command", "performed_by": "cockpit",
     "what": "write the 12-class TR harness command (config trial.arm: where cloud|mac, argv)", "retry_safe": True,
     "authority": "TRIAL_READY/1 true at H (G-0: the TR refuses to start without it); the cockpit starts the TR on the cloud box or the Mac"},
    {"id": "A0.K9_MIGRATION_READBACK", "stage": "S0", "kind": "executor_request", "performed_by": "cockpit",
     "what": "migration_readback --migration <1404|1405|1406 file name> (read-only ledger read), a fresh document every readback_every_s while the ledger is not known to hold the file", "retry_safe": True,
     "authority": "executor_ops.json: migration_readback enabled, production false, requesters adhikarin/v1/v2/sutradhara (the cockpit places the document under a listed lane); SR-K9-MIGRATION-WINDOW"},
    {"id": "A1.PR_UNHOLD", "stage": "S1", "kind": "gh_call", "performed_by": "chain --apply", "retry_safe": True,
     "what": "gh pr edit <N> --repo <R> --remove-label <hold label>",
     "authority": "PLAN_A10_1 §0.1 (#3841 HELD, unhold at TR pass); the cockpit's gh login (PR write)"},
    {"id": "A1.PR_AUTOMERGE", "stage": "S1", "kind": "gh_call", "performed_by": "chain --apply", "retry_safe": True,
     "what": "gh pr merge <N> --repo <R> --auto --squash --match-head-commit <H>",
     "authority": "PLAN_A10_1 §1 rule 1 (merge the moment TR passes), OWNER-MERGE-GROUP-FULL (the full merge-group runs on the final queue identity); the cockpit's gh login"},
    {"id": "A2.DEPLOY", "stage": "S2", "kind": "gh_call", "performed_by": "chain --apply", "retry_safe": False,
     "what": "gh workflow run deploy.yml --repo <R> --ref main -f force_all_services=true  (never ci_gate, never data_plane_cutover)",
     "authority": "PLAN_A10_1 §1 rule 2 (pins + image from main); workflow_dispatch right of the cockpit's gh login; deploy.yml keeps its own CI gate and protected environments"},
    {"id": "A2.IMAGE_READBACK", "stage": "S2", "kind": "executor_request", "performed_by": "cockpit",
     "what": "cloudrun_job_readback (read-only) of the deployed pipeline job image", "retry_safe": True,
     "authority": "executor_ops.json: enabled, production false, requesters adhikarin/v1/v2 (the cockpit places the document under a listed lane, as SC-1 does)"},
    {"id": "A2.EQ_RECORD", "stage": "S2", "kind": "local_tool", "performed_by": "chain --apply", "retry_safe": True,
     "what": "python3 -I equivalence_record.py record --repo <repo> --commit M --pinned-inputs <file> --out main_record.json",
     "authority": "PLAN_A10_1 §3 (EQ_CHECK); reads git objects and one pinned-inputs file, no database, no network"},
    {"id": "A2.EQ_COMPARE", "stage": "S2", "kind": "local_tool", "performed_by": "chain --apply", "retry_safe": True,
     "what": "python3 -I equivalence_record.py compare --trial trial_record.json --main main_record.json --out equivalence_decision.json",
     "authority": "PLAN_A10_1 §3.4/§3.5 (the category table decides); never rewrites a record"},
    {"id": "A3.REBIND", "stage": "S3", "kind": "harness_command", "performed_by": "cockpit",
     "what": "write the v1.7 rebind command (config dispatch.rebind_argv, the pack's repin tooling)", "retry_safe": True,
     "authority": "PLAN_A10_1 §1 rule 3 (W3W4 v1.7 rebind on the existing contracts); mechanical re-derivation of the staged pins to M, run by the cockpit"},
    {"id": "A3.REHEARSAL", "stage": "S3", "kind": "local_tool", "performed_by": "chain --apply", "retry_safe": True,
     "what": "python3 -I admission_rehearsal.py --sandbox <scratch> --staged <dir> --sql <dir> --repo <repo> --main-ref M --out <dir>",
     "authority": "PLAN_A10_1 §8 SW2 (final templates through the real validators on an isolated sandbox); nothing is written to the live KY_ROOT or a database"},
    {"id": "A3.DISPATCH_REQUEST", "stage": "S3", "kind": "executor_request", "performed_by": "chain --apply (queue) / cockpit (copy)",
     "what": "the pack's century dispatch template, copied byte-for-byte to the executor request queue", "retry_safe": True,
     "authority": "executor admission: kind enabled, lease, single V acceptance, dry_run_passed, production fence, merged reviewed commit; EXEC_REFRESH before the fence (PLAN §1 rule 5)"},
    {"id": "A4.VERIFY_REQUEST", "stage": "S4", "kind": "executor_request", "performed_by": "chain --apply (queue) / cockpit (copy)",
     "what": "the pack's sharded verification_job templates (R8), all emitted in the same poll", "retry_safe": True,
     "authority": "executor admission (verification_job: gcloud capability, production fence, merged reviewed commit); the verifier principal is the executor's, not this program's"},
    {"id": "A4.BUILD_READBACK", "stage": "S4", "kind": "executor_request", "performed_by": "cockpit",
     "what": "cloudrun_job_readback --execution <name> (read-only), a fresh document every readback_every_s while the build runs", "retry_safe": True,
     "authority": "executor_ops.json: enabled, production false, requesters adhikarin/v1/v2"},
    {"id": "A5.HANDOFF", "stage": "S5", "kind": "file_write", "performed_by": "chain --apply (else proposed file)",
     "what": "atomically write the adopted-generation file the seal controller (SC-1) reads, then page", "retry_safe": True,
     "authority": "SEAL_CONTROLLER_SC1.md (the adopted file is written by the cockpit); this program writes it only when the aggregate detector reads PASSED"},
)


class Hold(Exception):
    """A detector read false or null.  `soft` = the producer is known to be in flight (paged only after the stall limit)."""

    def __init__(self, code: str, reason: str, soft: bool = False):
        super().__init__(f"{code}: {reason}")
        self.code, self.reason, self.soft = code, reason, soft


# ── helpers ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def parse_ts(s):
    if not isinstance(s, str):
        return None
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def last_json(text: str, schema: str | None = None):
    """The last line of `text` that is a JSON object (carrying `schema` when given)."""
    for ln in reversed([x for x in text.splitlines() if x.strip()]):
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if isinstance(d, dict) and (schema is None or d.get("schema") == schema):
            return d
    return None


def sha_dir(directory: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(directory.glob("*.json")):
        h.update(f.name.encode() + b"\0" + hashlib.sha256(f.read_bytes()).hexdigest().encode() + b"\n")
    return h.hexdigest()


@contextlib.contextmanager
def locked(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    with open(out / ".dispatch_chain.lock", "a+") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        yield


# ── external seams (injected in tests; the defaults are the only places a process is started) ────────────────────────────────────────────────────────────────

class GhCli:
    """The cockpit's own `gh` login.  READS are two fixed shapes; ACTS are exactly the three argv shapes built by `argv_*` below (anything else, or any forbidden token, is refused)."""

    def __init__(self, run=subprocess.run):
        self._run = run

    def _call(self, argv: list[str]):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        return self._run(["gh", *argv], capture_output=True, text=True, timeout=120, env=env)

    def read(self, argv: list[str]):
        is_pr = argv[:2] == ["pr", "view"]
        is_api = len(argv) > 1 and argv[0] == "api" and argv[1].startswith(f"repos/{REPO_SLUG}/")
        if not (is_pr or is_api) or forbidden(argv) or any(t in ("-X", "--method", "-f", "-F", "--input", "--field", "--raw-field") for t in argv):
            raise ValueError(f"gh read refused: {argv[:2]}")
        p = self._call(argv)
        if p.returncode != 0:
            raise OSError(f"gh exited {p.returncode}")
        return json.loads(p.stdout)

    def act(self, argv: list[str]):
        if argv[:2] not in (["pr", "merge"], ["pr", "edit"], ["workflow", "run"]) or forbidden(argv):
            raise ValueError(f"gh act refused: {argv[:3]}")
        p = self._call(argv)
        return p.returncode, (p.stdout or "")[-2000:]


class Tools:
    """Local read-only tools (equivalence_record.py, admission_rehearsal.py): `python3 -I -B script args`; and one read-only `git ls-tree` of the cockpit's checkout."""

    def __init__(self, python: str = sys.executable, run=subprocess.run):
        self.python, self._run = python, run

    def _exec(self, argv: list[str], timeout: int, extra_env: dict | None = None):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(extra_env or {})
        return self._run(argv, capture_output=True, text=True, timeout=timeout, env=env)

    def run(self, script: str, args: list[str], timeout: int = 3600):
        p = self._exec([self.python, "-I", "-B", str(FLEET / script), *args], timeout)
        return p.returncode, (p.stdout or "")[-4000:], (p.stderr or "")[-2000:]

    def tree_names(self, repo: str, commit: str, directory: str, timeout: int = 60) -> list[str]:
        """The file names directly under `directory` at `commit`.  OSError when git cannot read the commit (an unknown commit is not an empty directory)."""
        p = self._exec(["git", "-C", repo, "ls-tree", "--name-only", commit, directory.rstrip("/") + "/"], timeout, {"GIT_OPTIONAL_LOCKS": "0"})
        if p.returncode != 0:
            raise OSError(f"git ls-tree exited {p.returncode}")
        return [Path(x).name for x in (p.stdout or "").splitlines() if x.strip()]


def forbidden(argv: list[str]) -> bool:
    """A token that must never reach gh from this program (substring match: `ci_gate=EMERGENCY-OVERRIDE-CI-NOT-GREEN` is as forbidden as `ci_gate`)."""
    return any(f in t for f in FORBIDDEN_GH_TOKENS for t in argv)


def argv_pr_view(repo: str, n: int) -> list[str]:
    return ["pr", "view", str(n), "--repo", repo, "--json", "number,state,isDraft,baseRefName,headRefOid,mergeCommit,autoMergeRequest,labels"]


def argv_compare(repo: str, m: str) -> list[str]:
    return ["api", f"repos/{repo}/compare/main...{m}", "-q", "{status: .status, ahead_by: .ahead_by, behind_by: .behind_by}"]


def argv_runs(repo: str, m: str) -> list[str]:
    return ["api", f"repos/{repo}/actions/runs?head_sha={m}&per_page=100",
            "-q", "{runs: [.workflow_runs[] | {id, name, path, event, head_sha, head_branch, status, conclusion, created_at, run_attempt}]}"]


def argv_unhold(repo: str, n: int, label: str) -> list[str]:
    return ["pr", "edit", str(n), "--repo", repo, "--remove-label", label]


def argv_automerge(repo: str, n: int, head: str, method: str = "squash") -> list[str]:
    return ["pr", "merge", str(n), "--repo", repo, "--auto", f"--{method}", "--match-head-commit", head]


def argv_deploy(repo: str) -> list[str]:
    return ["workflow", "run", DEPLOY_WORKFLOW, "--repo", repo, "--ref", "main", "-f", "force_all_services=true"]


# ── config ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def load_config(path) -> dict:
    try:
        c = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Hold("CONFIG_NO_INPUT", f"the chain config is missing: {path}") from None
    except (OSError, ValueError) as exc:
        raise Hold("CONFIG_UNREADABLE", f"the chain config is not readable JSON ({path}): {exc}") from None
    bad = lambda msg: Hold("CONFIG_INVALID", msg)
    if not isinstance(c, dict) or c.get("schema") != CONFIG_SCHEMA:
        raise bad(f"schema is not {CONFIG_SCHEMA}")
    if not isinstance(c.get("chart_id"), str) or not sc._UUID.fullmatch(c["chart_id"]):
        raise bad("chart_id is not a lowercase UUID")
    if not isinstance(c.get("generation"), str) or not sc._GEN.fullmatch(c["generation"]):
        raise bad("generation is missing or has unsafe characters")
    if not isinstance(c.get("repo"), str) or not c["repo"]:
        raise bad("repo (a local checkout holding the merged main objects) is missing")
    trial, pr = c.get("trial"), c.get("pr")
    if not isinstance(trial, dict) or not isinstance(trial.get("head"), str) or not _SHA.fullmatch(trial["head"]):
        raise bad("trial.head is not a 40-hex commit")
    if not isinstance(pr, dict) or not is_int(pr.get("number")) or pr["number"] < 1:
        raise bad("pr.number is missing")
    if pr.get("repo", REPO_SLUG) != REPO_SLUG:
        raise bad(f"pr.repo must be {REPO_SLUG}")
    for lab in pr.get("hold_labels", []):
        if not isinstance(lab, str) or not _LABEL.fullmatch(lab):
            raise bad("pr.hold_labels has an unsafe label")
    if pr.get("merge_method", "squash") not in ("squash", "merge", "rebase"):
        raise bad("pr.merge_method is not squash|merge|rebase")
    arm = trial.get("arm")
    if arm is not None:
        if not isinstance(arm, dict) or arm.get("where") not in ("cloud", "mac") or not isinstance(arm.get("argv"), list) or not arm["argv"] \
                or not all(isinstance(t, str) and _TOKEN.fullmatch(t) for t in arm["argv"]):
            raise bad("trial.arm must be {where: cloud|mac, argv: [safe tokens]}")
    return c


def key_of(cfg: dict) -> str:
    return f"{cfg['generation']}@{cfg['trial']['head']}"


class Ctx:
    def __init__(self, cfg, ops, out, pages_log, requests_dir, gh, tools, now, apply, dry):
        self.cfg, self.ops, self.out, self.pages_log, self.requests_dir = cfg, Path(ops), Path(out), Path(pages_log), Path(requests_dir)
        self.gh, self.tools, self.now, self.apply, self.dry = gh, tools, now, apply, dry
        self.key = key_of(cfg)
        self.H = cfg["trial"]["head"]
        self.ev = Path(cfg.get("evidence_dir") or self.out / "evidence")
        self.repo_slug = cfg["pr"].get("repo", REPO_SLUG)
        self.M: str | None = None
        self.would: list[dict] = []
        self.evidence: dict = {}

    # evidence paths (conventional names under evidence_dir; `evidence` in the config overrides one by name)
    def path(self, name: str, default: str) -> Path:
        p = (self.cfg.get("evidence") or {}).get(name)
        return Path(p) if p else self.ev / default

    def marker(self, name: str) -> Path:
        return self.out / "markers" / name

    def read_marker(self, name: str):
        p = self.marker(name)
        if not p.exists():
            return None
        with contextlib.suppress(ValueError):
            return json.loads(p.read_text())
        return {"unreadable": True}

    def set_marker(self, name: str, payload: dict) -> None:
        sc.write_marker(self.out, name, {"key": self.key, "ts": sc.utc(self.now), **payload})

    def note(self, action_id: str, state: str, detail) -> None:
        a = next(x for x in ACTIONS if x["id"] == action_id)
        self.would.append({"action": action_id, "stage": a["stage"], "kind": a["kind"], "state": state, "performed_by": a["performed_by"], "authority": a["authority"], "detail": detail})

    def page(self, tag: str, needle_extra: str, text: str) -> bool:
        if self.dry:
            return False
        needle = f"PAGE {tag} key={self.key} {needle_extra}".rstrip() + " "
        try:
            return sc.append_page(self.pages_log, needle, f"{sc.utc(self.now)} {needle}{text}\n")
        except OSError:                                                              # an unwritable log is retried next poll (the needle makes the page exactly-once)
            return False


# ── readers ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def read_json(ctx: Ctx, path: Path, what: str, stage: str, soft_missing: bool = True):
    if not path.exists():
        raise Hold(f"{stage}_NO_INPUT", f"{what} is missing: {path}", soft=soft_missing)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Hold(f"{stage}_UNREADABLE", f"{what} is not readable JSON ({path}): {exc}") from None


def need_receipt(ctx: Ctx, op: str, what: str, stage: str, kind: str | None = None):
    rp = ctx.ops / "receipts" / f"{op}.json"
    if not rp.exists():
        raise Hold(f"{stage}_AWAITING_RECEIPT", f"{what}: no executor receipt for {op} yet", soft=True)
    try:
        rec, text, rsha = sc.read_receipt(ctx.ops, op, what)
    except sc.NotReady as exc:
        raise Hold(f"{stage}_RECEIPT_UNREADABLE", exc.reason) from None
    if rec.get("status") != "COMPLETED" or rec.get("exit_code") != 0:
        raise Hold(f"{stage}_RECEIPT_NOT_COMPLETED", f"{what} {op}: receipt status {rec.get('status')!r}, exit {rec.get('exit_code')!r}, not COMPLETED / 0")
    if kind and rec.get("kind") != kind:
        raise Hold(f"{stage}_RECEIPT_WRONG_KIND", f"{what} {op}: receipt kind {rec.get('kind')!r}, expected {kind!r}")
    return rec, text, rsha


def gh_read(ctx: Ctx, argv: list[str], what: str, stage: str):
    try:
        return ctx.gh.read(argv)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise Hold(f"{stage}_GH_UNREADABLE", f"{what}: the GitHub read failed ({type(exc).__name__}); no evidence, no advance") from None


# ── emission helpers (exactly-once, dry-run-safe) ────────────────────────────────────────────────────────────────────────────────────

def emit_doc(ctx: Ctx, action_id: str, marker_name: str, doc: dict, text: str | None = None, marker_extra: dict | None = None) -> str:
    """A harness-command / action document under actions/, exactly once.  -> NEW | ALREADY | WOULD."""
    if ctx.read_marker(marker_name) is not None:
        ctx.note(action_id, "ALREADY", marker_name)
        return "ALREADY"
    if ctx.dry:
        ctx.note(action_id, "WOULD_EMIT", doc)
        return "WOULD"
    with locked(ctx.out):
        sc.atomic_write(ctx.out / "actions" / f"{marker_name}.json", json.dumps({"schema": SCHEMA, "action": action_id, "key": ctx.key, **doc}, indent=1, sort_keys=True) + "\n")
        if text:
            sc.atomic_write(ctx.out / "actions" / f"{marker_name}.txt", text)
        ctx.set_marker(marker_name, {"action": action_id, **(marker_extra or {})})
    ctx.note(action_id, "EMITTED", doc)
    return "NEW"


def run_gh_action(ctx: Ctx, action_id: str, marker_name: str, argv: list[str], extra: dict | None = None):
    """A gh call the chain is authorised to make itself.  Without --apply it is only written (the cockpit performs it).  -> (state, extra marker payload)."""
    a = next(x for x in ACTIONS if x["id"] == action_id)
    if ctx.read_marker(marker_name) is not None:
        ctx.note(action_id, "ALREADY", marker_name)
        return "ALREADY"
    if ctx.dry:
        ctx.note(action_id, "WOULD_APPLY" if ctx.apply else "WOULD_EMIT", ["gh", *argv])
        return "WOULD"
    if not ctx.apply:
        emit_doc(ctx, action_id, marker_name, {"kind": "gh_call", "argv": ["gh", *argv], "authority": a["authority"], "performed_by": "cockpit"}, " ".join(["gh", *argv]) + "\n", marker_extra=extra)
        return "EMITTED"
    with locked(ctx.out):
        if not a["retry_safe"]:                                                     # intent first: an unknown outcome is never repeated by this program
            ctx.set_marker(marker_name, {"action": action_id, "state": "INTENT", **(extra or {})})
        rc, tail = ctx.gh.act(argv)
        if rc != 0:
            if a["retry_safe"]:
                raise Hold(f"{action_id}_FAILED", f"{action_id} exited {rc} ({tail.strip()[-200:]!r}); it is safe to retry and will be on the next poll")
            raise Hold(f"{action_id}_OUTCOME_UNKNOWN", f"{action_id} exited {rc} after its intent was recorded: reconcile on GitHub; this program never repeats it (clear markers/{marker_name} to allow a retry)")
        ctx.set_marker(marker_name, {"action": action_id, "state": "DONE", **(extra or {})})
    ctx.note(action_id, "APPLIED", ["gh", *argv])
    return "APPLIED"


def emit_request(ctx: Ctx, action_id: str, op: str, doc_bytes: bytes, what: str) -> str:
    """An executor request document to requests_dir/<op>.json, exactly once (never overwritten with other bytes).  Written only on --apply or into the out dir otherwise."""
    marker_name = f"REQ.{op}"
    target = (ctx.requests_dir if ctx.apply else ctx.out / "requests") / f"{op}.json"
    if ctx.read_marker(marker_name) is not None:
        if target.exists() and target.read_bytes() != doc_bytes:
            raise Hold(f"{action_id}_REQUEST_CONFLICT", f"{what}: {target} exists with other bytes than the request this chain emitted; it is never overwritten")
        ctx.note(action_id, "ALREADY", op)
        return "ALREADY"
    if target.exists() and target.read_bytes() != doc_bytes:
        raise Hold(f"{action_id}_REQUEST_CONFLICT", f"{what}: {target} already exists with other bytes; it is never overwritten")
    if ctx.dry:
        ctx.note(action_id, "WOULD_EMIT", {"operation_id": op, "to": str(target)})
        return "WOULD"
    with locked(ctx.out):
        if not target.exists():
            sc.atomic_write(target, doc_bytes.decode("utf-8"))
        ctx.set_marker(marker_name, {"action": action_id, "operation_id": op, "sha256": sc.sha256_bytes(doc_bytes), "target": str(target)})
    ctx.note(action_id, "EMITTED", {"operation_id": op, "to": str(target)})
    return "NEW"


def readback_request(ctx: Ctx, action_id: str, op: str, args: dict, kind: str = "cloudrun_job_readback", commit: str | None = None) -> str:
    doc = {"operation_id": op, "kind": kind, "item_id": ctx.cfg.get("item_id") or DEFAULT_ITEM, "idempotency_key": op, "requested_by": "dispatch-chain",
           "kyd": ctx.cfg.get("kyd") or DEFAULT_ITEM, "args": args, "reviewed_commit": commit or ctx.M}
    return emit_request(ctx, action_id, op, (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode(), f"readback {op}")


# ── S0: TRIAL_READY/1 at H ───────────────────────────────────────────────────────────────────────────────────────────────────────────

def check_trial_ready(ctx: Ctx) -> dict:
    p = ctx.path("trial_ready", "trial_ready.json")
    doc = read_json(ctx, p, "trial_ready.json", "S0")
    if not isinstance(doc, dict) or doc.get("predicate") != TRIAL_READY_PREDICATE:
        raise Hold("S0_BAD_SHAPE", f"trial_ready.json is not a {TRIAL_READY_PREDICATE} document")
    if doc.get("head_sha") != ctx.H:
        raise Hold("S0_STALE_HEAD", f"trial_ready.json was evaluated at {str(doc.get('head_sha'))[:12]}, not the trial head {ctx.H[:12]}")
    checks = doc.get("checks")
    if not isinstance(checks, list) or not all(isinstance(c, dict) for c in checks):
        raise Hold("S0_BAD_SHAPE", "trial_ready.json carries no checks list")
    ids = [c.get("id") for c in checks]
    if sorted(ids) != sorted(TRIAL_IDS):
        raise Hold("S0_CHECKS_INCOMPLETE", f"the checks are not exactly T01..T25 once each (missing {sorted(set(TRIAL_IDS) - set(ids))}, extra/duplicate {sorted(i for i in set(ids) if ids.count(i) > 1 or i not in TRIAL_IDS)})")
    not_true = sorted(c["id"] for c in checks if c.get("value") is not True)
    if not_true:
        nulls = sorted(c["id"] for c in checks if c.get("value") is None)
        raise Hold("S0_NOT_READY", f"{len(checks) - len(not_true)}/25 checks read true at {ctx.H[:12]}; not true: {', '.join(not_true)} (null: {', '.join(nulls) or 'none'})")
    no_ev = sorted(c["id"] for c in checks if not (isinstance(c.get("evidence_ref"), str) and c["evidence_ref"].strip()))
    if no_ev:
        raise Hold("S0_GREEN_WITHOUT_EVIDENCE", f"checks read true but name no evidence_ref: {', '.join(no_ev)} (a green nothing measured is null)")
    if doc.get("ready") is not True:
        raise Hold("S0_DISAGREEMENT", "all 25 checks read true but the file's own `ready` is not true: the evaluator and the recount disagree")
    return {"head": ctx.H, "trial_ready_sha256": sc.sha256_file(p), "true_checks": 25, "evaluated_at": doc.get("evaluated_at")}


def k9_files_in_repo(ctx: Ctx) -> dict[str, str]:
    """number -> exact migration file name, read from the repo at the evaluated head H (never a literal where the repo can supply it)."""
    try:
        names = ctx.tools.tree_names(ctx.cfg["repo"], ctx.H, K9_MIGRATION_DIR)
    except (OSError, subprocess.SubprocessError):
        raise Hold("S0_K9_REPO_UNREADABLE", f"{K9_PRECONDITION}: {K9_MIGRATION_DIR} cannot be read from the repo at the trial head {ctx.H[:12]}; the migration names are unknown, no advance") from None
    found, absent = {}, []
    for num, exact in K9_MIGRATIONS:
        hit = sorted(n for n in names if n.endswith(".sql") and n.startswith(num + "_") and (exact is None or n == exact))
        if len(hit) > 1:
            raise Hold("S0_K9_FILE_AMBIGUOUS", f"{K9_PRECONDITION}: {len(hit)} files {hit} carry the number {num} at {ctx.H[:12]}")
        if hit:
            found[num] = hit[0]
        else:
            absent.append(exact or f"{num}_*.sql")
    if absent:
        raise Hold("S0_K9_FILE_NOT_IN_REPO", f"{K9_PRECONDITION}: {', '.join(absent)} not present in {K9_MIGRATION_DIR} at the trial head {ctx.H[:12]}: the head does not carry the K9 migrations it is to be dispatched with")
    return found


def check_k9_migrations_applied(ctx: Ctx) -> dict:
    """Precondition `k9_migrations_applied` (SR-K9-MIGRATION-WINDOW): true ONLY when every K9 migration file the repo names at H has a row in the target DB's public._migrations_applied.
    The ledger is read through the executor's `migration_readback` (receipt, never a connection here); a missing or unreadable receipt/ledger is a hold, never a pass (N.8, N.7.6)."""
    files = k9_files_in_repo(ctx)
    gen = re.sub("[^0-9A-Za-z]+", "-", ctx.cfg["generation"])
    epoch = int(ctx.now.timestamp() // int(ctx.cfg.get("readback_every_s", 300)))
    rdir = ctx.ops / "receipts"
    plan = {}
    for num, name in files.items():
        base = f"chain-k9mig-{gen}-{ctx.H[:12]}-{num}-e"
        have = sorted((int(f.name[len(base):-len(".json")]) for f in rdir.glob(base + "*.json") if f.name[len(base):-len(".json")].isdigit()), reverse=True) if rdir.is_dir() else []
        if not have or have[0] < epoch:                                                  # a fresh read-only readback every period while the ledger is not known to hold the file
            readback_request(ctx, "A0.K9_MIGRATION_READBACK", base + str(epoch), {"migration": name}, kind="migration_readback", commit=ctx.H)
        plan[name] = (base, have)
    waiting = sorted(n for n, (_, have) in plan.items() if not have)
    if waiting:
        raise Hold("S0_K9_AWAITING_RECEIPT", f"{K9_PRECONDITION}: no ledger readback yet for {', '.join(waiting)}", soft=True)
    missing, receipts = [], {}
    for name, (base, have) in plan.items():
        _, text, rsha = need_receipt(ctx, base + str(have[0]), f"migration ledger readback of {name}", "S0", "migration_readback")
        try:
            rows = sc.parse_table(text, MIGRATION_LEDGER_HEADER, f"ledger readback of {name}")
        except sc.NotReady as exc:
            raise Hold("S0_K9_LEDGER_UNREADABLE", f"{K9_PRECONDITION}: {exc.reason}") from None
        if name not in {r["filename"] for r in rows}:
            missing.append(name)
        receipts[name] = rsha
    if missing:
        raise Hold("S0_K9_MIGRATIONS_NOT_APPLIED", f"{K9_PRECONDITION}: not in public._migrations_applied of the target DB: {', '.join(missing)}")
    return {"files": files, "receipts": receipts}


def act_arm_tr(ctx: Ctx) -> None:
    arm = ctx.cfg["trial"].get("arm")
    name = f"ARM_TR.{ctx.cfg['generation']}.{ctx.H}"
    if not arm:
        ctx.note("A0.ARM_TR", "NOT_CONFIGURED", "config trial.arm absent: no harness command can be written")
        return
    argv = [t.replace("{head}", ctx.H).replace("{trial_ready}", str(ctx.path("trial_ready", "trial_ready.json"))).replace("{out}", str(ctx.ev)) for t in arm["argv"]]
    emit_doc(ctx, "A0.ARM_TR", name, {"kind": "harness_command", "where": arm["where"], "head": ctx.H, "argv": argv, "runs": False,
                                      "authority": next(a["authority"] for a in ACTIONS if a["id"] == "A0.ARM_TR")}, " ".join(argv) + "\n")
    ctx.page("CHAIN-ARM-TR", f"head={ctx.H[:12]}", f"where={arm['where']} command={ctx.out / 'actions' / (name + '.txt')}")      # exactly-once by its needle; self-repairing if the log was unwritable


# ── S1: the TR verdict, RV-INT part 2, the PR ────────────────────────────────────────────────────────────────────────────────────────────

def check_tr_verdict(ctx: Ctx, ready: dict) -> dict:
    p = ctx.path("tr_verdict", "tr_verdict.json")
    armed = ctx.read_marker(f"ARM_TR.{ctx.cfg['generation']}.{ctx.H}") is not None
    doc = read_json(ctx, p, "the TR verdict", "S1")
    if not isinstance(doc, dict) or doc.get("schema") != TR_VERDICT_SCHEMA:
        raise Hold("S1_VERDICT_BAD_SHAPE", f"the TR verdict is not a {TR_VERDICT_SCHEMA} document")
    if doc.get("head_sha") != ctx.H:
        raise Hold("S1_VERDICT_STALE_HEAD", f"the TR verdict is for {str(doc.get('head_sha'))[:12]}, not the trial head {ctx.H[:12]}")
    if doc.get("trial_ready_sha256") != ready["trial_ready_sha256"]:
        raise Hold("S1_VERDICT_UNBOUND", "the TR verdict does not cite the digest of this trial_ready.json (G-0: the TR must start from TRIAL_READY, no other signal)")
    if doc.get("qualifying") is not True or str(doc.get("label") or "").upper() == "DIAGNOSTIC":
        raise Hold("S1_VERDICT_NOT_QUALIFYING", "the TR verdict is not a qualifying run (DIAGNOSTIC rolling runs are no evidence for G-1..G-7; A10.1 N3)")
    classes = doc.get("classes")
    if not isinstance(classes, list) or len(set(classes)) != TR_CLASS_COUNT or len(classes) != TR_CLASS_COUNT or not all(isinstance(c, str) for c in classes):
        raise Hold("S1_VERDICT_CLASSES", f"the TR verdict does not name exactly {TR_CLASS_COUNT} distinct classes")
    gates = doc.get("gates")
    if not isinstance(gates, dict):
        raise Hold("S1_VERDICT_BAD_SHAPE", "the TR verdict carries no gates object")
    bad = sorted(g for g in GATES if not (isinstance(gates.get(g), dict) and gates[g].get("value") is True))
    if bad:
        nulls = [g for g in bad if not isinstance(gates.get(g), dict) or gates[g].get("value") is None]
        raise Hold("S1_GATES_NOT_PASSED", f"TR gates not true: {', '.join(bad)} (null: {', '.join(nulls) or 'none'})")
    noev = sorted(g for g in GATES if not (isinstance(gates[g].get("evidence_ref"), str) and gates[g]["evidence_ref"].strip()))
    if noev:
        raise Hold("S1_GATE_WITHOUT_EVIDENCE", f"TR gates read true but name no evidence_ref: {', '.join(noev)}")
    if doc.get("verdict") != "PASS":
        raise Hold("S1_VERDICT_DISAGREEMENT", f"G-1..G-7 all read true but the verdict says {doc.get('verdict')!r}, not PASS: the report and the recount disagree")
    rec_sha = doc.get("equivalence_record_sha256")
    trial_rec = ctx.path("trial_record", "trial_record.json")
    if not (isinstance(rec_sha, str) and _HEX64.fullmatch(rec_sha)) or not trial_rec.exists() or sc.sha256_file(trial_rec) != rec_sha:
        raise Hold("S1_TRIAL_RECORD_UNBOUND", "the TR's EQUIVALENCE_RECORD is missing or does not match the digest the verdict cites")
    return {"verdict_sha256": sc.sha256_file(p), "trial_record_sha256": rec_sha, "armed": armed}


def check_rvint(ctx: Ctx) -> dict:
    p = ctx.path("rvint", "rvint_part2.result.json")
    doc = read_json(ctx, p, "the RV-INT part 2 review result", "S1")
    pv = doc.get("proposed_verdict") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("schema") != "ky.job_result/1" or not isinstance(pv, dict):
        raise Hold("S1_RVINT_BAD_SHAPE", "the RV-INT result is not a reviewer ky.job_result/1 with a proposed_verdict")
    if not RVINT_ITEM.search(str(doc.get("item") or "")):
        raise Hold("S1_RVINT_WRONG_ITEM", f"the review item {doc.get('item')!r} is not RV-INT part 2")
    if doc.get("status") != "done":
        raise Hold("S1_RVINT_NOT_DONE", f"the RV-INT job status is {doc.get('status')!r}, not done")
    if pv.get("head") != ctx.H:
        raise Hold("S1_RVINT_STALE_HEAD", f"the RV-INT verdict is for {str(pv.get('head'))[:12]}, not the trial head {ctx.H[:12]}")
    if pv.get("verdict") != "ACCEPTED":
        raise Hold("S1_RVINT_NOT_PASSED", f"the RV-INT part 2 verdict is {pv.get('verdict')!r}, not ACCEPTED")
    if not (isinstance(pv.get("patch_id"), str) and _SHA.fullmatch(pv["patch_id"])):
        raise Hold("S1_RVINT_NO_PATCH_ID", "the RV-INT verdict binds no patch id (A10.1 N1: the review must be bound to the actual patch)")
    if not isinstance(pv.get("claims"), list) or not pv["claims"]:
        raise Hold("S1_RVINT_NO_CLAIMS", "the RV-INT verdict enumerates no claims (D-OWNER-TESTS-20261016 (ii))")
    blocking = [f for f in (pv.get("findings") or []) if isinstance(f, dict) and (f.get("blocking") is True or str(f.get("severity", "")).upper() == "BLOCKING")]
    if blocking:
        raise Hold("S1_RVINT_BLOCKING_FINDING", f"the RV-INT verdict carries {len(blocking)} blocking finding(s)")
    return {"rvint_sha256": sc.sha256_file(p), "patch_id": pv["patch_id"], "claims": len(pv["claims"])}


def read_pr(ctx: Ctx) -> dict:
    pr = gh_read(ctx, argv_pr_view(ctx.repo_slug, ctx.cfg["pr"]["number"]), "PR state", "S1")
    if not isinstance(pr, dict) or pr.get("number") != ctx.cfg["pr"]["number"]:
        raise Hold("S1_PR_UNREADABLE", "the PR readback does not describe the configured PR")
    return pr


def check_pr_and_enqueue(ctx: Ctx) -> dict:
    n, repo = ctx.cfg["pr"]["number"], ctx.repo_slug
    pr = read_pr(ctx)
    state = pr.get("state")
    if state == "CLOSED":
        raise Hold("S1_PR_CLOSED", f"PR #{n} is closed without a merge")
    if pr.get("headRefOid") != ctx.H:
        raise Hold("S1_PR_HEAD_MOVED", f"PR #{n} head is {str(pr.get('headRefOid'))[:12]}, not the tested head {ctx.H[:12]}: untested code must not merge")
    if pr.get("baseRefName") != "main":
        raise Hold("S1_PR_BASE", f"PR #{n} is based on {pr.get('baseRefName')!r}, not main")
    if state == "MERGED":
        mc = (pr.get("mergeCommit") or {}).get("oid")
        if not (isinstance(mc, str) and _SHA.fullmatch(mc)):
            raise Hold("S1_MERGE_COMMIT_UNREADABLE", f"PR #{n} is MERGED but names no merge commit")
        return {"pr_state": "MERGED", "merge_commit": mc}
    if state != "OPEN":
        raise Hold("S1_PR_STATE", f"PR #{n} state is {state!r}")
    if pr.get("isDraft") is True:
        raise Hold("S1_PR_DRAFT", f"PR #{n} is a draft: nothing is enqueued")
    labels = {(lb.get("name") if isinstance(lb, dict) else lb) for lb in (pr.get("labels") or [])}
    held = sorted(labels & set(ctx.cfg["pr"].get("hold_labels", [])))
    for lab in held:
        run_gh_action(ctx, "A1.PR_UNHOLD", f"PR_UNHOLD.{n}.{ctx.H}.{re.sub('[^A-Za-z0-9]+', '-', lab)}", argv_unhold(repo, n, lab))
    if held:
        if ctx.apply and not ctx.dry:
            pr = read_pr(ctx)
            labels = {(lb.get("name") if isinstance(lb, dict) else lb) for lb in (pr.get("labels") or [])}
            held = sorted(labels & set(ctx.cfg["pr"].get("hold_labels", [])))
        if held:
            raise Hold("S1_PR_HELD", f"PR #{n} still carries the hold label(s) {held}", soft=True)
    if pr.get("autoMergeRequest"):
        raise Hold("S1_MERGE_QUEUED", f"PR #{n} has auto-merge enabled and is not merged yet (the full merge-group runs on the final identity)", soft=True)
    st = run_gh_action(ctx, "A1.PR_AUTOMERGE", f"PR_AUTOMERGE.{n}.{ctx.H}", argv_automerge(repo, n, ctx.H, ctx.cfg["pr"].get("merge_method", "squash")))
    raise Hold("S1_MERGE_ENQUEUE_" + st, f"merge of #{n} at {ctx.H[:12]} {'enqueued' if st == 'APPLIED' else 'emitted for the cockpit' if st in ('EMITTED', 'ALREADY') else 'would be enqueued'}", soft=True)


# ── S2: merged, CI green, image deployed, equivalence ──────────────────────────────────────────────────────────────────────────────────

def check_on_main(ctx: Ctx, m: str) -> dict:
    c = gh_read(ctx, argv_compare(ctx.repo_slug, m), "compare main...M", "S2")
    st = c.get("status") if isinstance(c, dict) else None
    if st not in ("identical", "behind"):
        raise Hold("S2_NOT_ON_MAIN", f"the merge commit {m[:12]} is not reachable from main (compare status {st!r})")
    return {"compare_status": st}


def runs_for(ctx: Ctx, m: str) -> list[dict]:
    d = gh_read(ctx, argv_runs(ctx.repo_slug, m), "workflow runs at M", "S2")
    runs = d.get("runs") if isinstance(d, dict) else None
    if not isinstance(runs, list):
        raise Hold("S2_RUNS_UNREADABLE", "the workflow-run readback is not a runs list")
    return [r for r in runs if isinstance(r, dict) and r.get("head_sha") == m]


def check_ci(ctx: Ctx, m: str, runs: list[dict]) -> dict:
    required = ctx.cfg.get("ci", {}).get("required") or []
    if not required:
        raise Hold("S2_CI_NOT_CONFIGURED", "config ci.required names no workflow: main CI green cannot be measured (an honest null)")
    seen = {}
    for name in required:
        mine = sorted((r for r in runs if r.get("name") == name and r.get("head_branch") == "main" and r.get("event") in ("push", "merge_group", "workflow_run")),
                      key=lambda r: (str(r.get("created_at")), r.get("run_attempt") or 0))
        if not mine:
            raise Hold("S2_CI_NOT_STARTED", f"no run of the required workflow {name!r} exists at main {m[:12]} yet", soft=True)
        last = mine[-1]
        if last.get("status") != "completed":
            raise Hold("S2_CI_RUNNING", f"main CI {name!r} at {m[:12]} is {last.get('status')!r}", soft=True)
        if last.get("conclusion") != "success":
            raise Hold("S2_CI_RED", f"main CI {name!r} at {m[:12]} concluded {last.get('conclusion')!r}, not success")
        seen[name] = last.get("id")
    return {"ci_runs": seen}


def check_deploy(ctx: Ctx, m: str, runs: list[dict]) -> dict:
    marker = f"DEPLOY.{m}"
    prior = sorted(r["id"] for r in runs if r.get("path") == DEPLOY_PATH and r.get("event") == "workflow_dispatch" and is_int(r.get("id")))
    run_gh_action(ctx, "A2.DEPLOY", marker, argv_deploy(ctx.repo_slug), extra={"prior_run_ids": prior, "merge_commit": m})
    mk = ctx.read_marker(marker)
    if mk is None:                                                                    # --dry-run only: nothing has been dispatched
        raise Hold("S2_DEPLOY_PENDING_DISPATCH", f"the forced image deploy for {m[:12]} has not been dispatched", soft=True)
    if mk.get("state") == "INTENT":
        raise Hold("S2_DEPLOY_OUTCOME_UNKNOWN", "a deploy dispatch intent is recorded without a result: reconcile on GitHub; this program never repeats it")
    old = set(mk.get("prior_run_ids") or [])
    new = sorted((r for r in runs if r.get("path") == DEPLOY_PATH and r.get("event") == "workflow_dispatch" and r.get("id") not in old), key=lambda r: (str(r.get("created_at")), r["id"]))
    if not new:
        raise Hold("S2_DEPLOY_NO_RUN", f"no NEW deploy.yml dispatch run for {m[:12]} exists beyond the {len(old)} that predate the dispatch", soft=True)
    last = new[-1]
    if last.get("status") != "completed":
        raise Hold("S2_DEPLOY_RUNNING", f"deploy run {last['id']} is {last.get('status')!r}", soft=True)
    if last.get("conclusion") != "success":
        raise Hold("S2_DEPLOY_FAILED", f"deploy run {last['id']} concluded {last.get('conclusion')!r}; this program never redispatches (clear markers/{marker} after reconciling)")
    return {"deploy_run_id": last["id"]}


def check_image(ctx: Ctx, m: str, deploy_run: int) -> dict:
    op = f"chain-image-{re.sub('[^0-9A-Za-z]+', '-', ctx.cfg['generation'])}-{m[:12]}-d{deploy_run}"
    readback_request(ctx, "A2.IMAGE_READBACK", op, {})
    rec, text, rsha = need_receipt(ctx, op, "deployed image readback", "S2", "cloudrun_job_readback")
    d = last_json(text, READBACK_SCHEMA)
    if d is None or d.get("status") != "MEASURED":
        raise Hold("S2_IMAGE_READBACK_BAD", "the image readback is not a MEASURED ky.cloudrun_readback/1 record")
    commit = (d.get("provenance") or {}).get("image_commit")
    if commit != m:
        raise Hold("S2_IMAGE_NOT_M", f"the deployed pipeline image carries commit {str(commit)[:12]}, not the merge commit {m[:12]}: the forced deploy did not reach the job")
    return {"image_operation_id": op, "receipt_sha256": rsha}


def check_equivalence(ctx: Ctx, m: str) -> dict:
    trial_rec, main_rec, dec = ctx.path("trial_record", "trial_record.json"), ctx.path("main_record", "main_record.json"), ctx.path("decision", "equivalence_decision.json")
    pinned = ctx.cfg.get("main", {}).get("pinned_inputs_file")
    if not main_rec.exists():
        if not pinned:
            raise Hold("S2_EQ_NO_PINNED_INPUTS", "config main.pinned_inputs_file is missing: EQUIVALENCE_RECORD(M) cannot be computed")
        args = ["record", "--repo", ctx.cfg["repo"], "--commit", m, "--pinned-inputs", str(pinned), "--out", str(main_rec)]
        run_tool(ctx, "A2.EQ_RECORD", "equivalence_record.py", args, f"EQR.record.{m}", ok_codes=(0, 2))
    ensure_record_of(ctx, main_rec, m)
    if not dec.exists() or decision_stale(ctx, dec, trial_rec, main_rec):
        if dec.exists() and not ctx.dry:
            dec.unlink()                                                              # a decision about other records is never reused
        run_tool(ctx, "A2.EQ_COMPARE", "equivalence_record.py", ["compare", "--trial", str(trial_rec), "--main", str(main_rec), "--out", str(dec)], f"EQR.compare.{sc.sha256_file(main_rec)[:12]}", ok_codes=(0, 3))
    d = read_json(ctx, dec, "the equivalence decision", "S2")
    judge_decision(d, trial_rec, main_rec)
    return {"decision_sha256": sc.sha256_file(dec), "main_record_sha256": d["main_record_sha"], "action": d["action"]["overall"]}


def ensure_record_of(ctx: Ctx, main_rec: Path, m: str) -> None:
    if not main_rec.exists():
        raise Hold("S2_EQ_AWAITING_RECORD", f"EQUIVALENCE_RECORD({m[:12]}) is not computed yet", soft=True)
    try:
        d = json.loads(main_rec.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise Hold("S2_EQ_RECORD_UNREADABLE", f"{main_rec} is not readable JSON") from None
    if (d.get("E6") or {}).get("commit") != m:
        raise Hold("S2_EQ_RECORD_OTHER_COMMIT", f"the main EQUIVALENCE_RECORD was produced at {str((d.get('E6') or {}).get('commit'))[:12]}, not the merge commit {m[:12]}")


def decision_stale(ctx: Ctx, dec: Path, trial_rec: Path, main_rec: Path) -> bool:
    try:
        d = json.loads(dec.read_text(encoding="utf-8"))
        return d.get("trial_record_sha") != sc.sha256_file(trial_rec) or d.get("main_record_sha") != sc.sha256_file(main_rec)
    except (OSError, ValueError):
        return True


def judge_decision(d, trial_rec: Path, main_rec: Path) -> None:
    """The decision is read for what it SAYS and what it is BOUND to; the tool's exit code alone is never the gate."""
    if not isinstance(d, dict) or d.get("schema") != DECISION_SCHEMA:
        raise Hold("S2_EQ_BAD_SHAPE", f"the decision is not a {DECISION_SCHEMA} document")
    if d.get("trial_record_sha") != sc.sha256_file(trial_rec) or d.get("main_record_sha") != sc.sha256_file(main_rec):
        raise Hold("S2_EQ_UNBOUND", "the decision is not bound to the digests of the TR's record and main's record on disk")
    per = d.get("per_category") or {}
    if d.get("decision") != "EQUAL":
        act = d.get("action") or {}
        raise Hold("S2_EQ_DIFFERS", f"EQUIVALENCE_RECORD differs (categories {sorted(c for c in ('E1','E2','E3','E4','E5') if per.get(c) != 'equal')}, E3b {per.get('E3b_coverage')}): minimum action "
                                    f"{act.get('overall')} — {'; '.join(r.get('text', '') for r in act.get('rows', []))} flags {act.get('flags')}")
    wrong = [c for c in ("E1", "E2", "E3", "E4", "E5") if per.get(c) != "equal"]
    if wrong or per.get("E3b_coverage") != "ok":
        raise Hold("S2_EQ_DISAGREEMENT", f"the decision says EQUAL but its own categories are not (not equal: {wrong}, E3b {per.get('E3b_coverage')})")


def run_tool(ctx: Ctx, action_id: str, script: str, args: list[str], marker_name: str, ok_codes: tuple = (0,)) -> None:
    """A local read-only tool.  `ok_codes` are the exit codes that mean "a document was written, read it" (the gate is the document, never the code)."""
    a = next(x for x in ACTIONS if x["id"] == action_id)
    if ctx.dry:
        ctx.note(action_id, "WOULD_RUN" if ctx.apply else "WOULD_EMIT", [script, *args])
        return
    if not ctx.apply:
        emit_doc(ctx, action_id, marker_name, {"kind": "local_tool", "script": script, "args": args, "authority": a["authority"], "performed_by": "cockpit"},
                 f"python3 -I -B {script} " + " ".join(args) + "\n")
        return
    try:
        rc, out, err = ctx.tools.run(script, args)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Hold(f"{action_id}_RUN_FAILED", f"{script} could not run: {type(exc).__name__}") from None
    ctx.note(action_id, "APPLIED", {"script": script, "exit": rc})
    if rc not in ok_codes:
        raise Hold(f"{action_id}_REFUSED", f"{script} {args[0]} exited {rc}: {(err or out).strip()[-300:]}")


# ── S3: executor refresh, rebind, admission rehearsal, the dispatch request ────────────────────────────────────────────────────────────

def check_executor(ctx: Ctx, m: str) -> dict:
    p = Path(ctx.cfg.get("capabilities_file") or ctx.ops / "CAPABILITIES.json")
    c = read_json(ctx, p, "CAPABILITIES.json", "S3")
    if not isinstance(c, dict) or c.get("main_revision") != m or c.get("refresh_state") != "ACTIVE" or c.get("ops_table_on_main") is not True:
        raise Hold("S3_EXECUTOR_NOT_REFRESHED", f"the executor is not ACTIVE on the merged main (main_revision {str(c.get('main_revision') if isinstance(c, dict) else None)[:12]}, state "
                                                f"{c.get('refresh_state') if isinstance(c, dict) else None!r}); it must be refreshed to {m[:12]} before the fence (PLAN §1 rule 5)", soft=True)
    missing = sorted(k for k in ("builder", "gcloud") if c.get(k) is not True)
    if missing:
        raise Hold("S3_CAPABILITY_MISSING", f"the executor lacks capabilities {missing} the century path needs")
    if c.get("production_slot") != "free":
        raise Hold("S3_PRODUCTION_SLOT_BUSY", f"production_slot is {c.get('production_slot')!r}, not free: one century build at a time (PLAN §1 rule 6)")
    ts = parse_ts(c.get("ts"))
    if ts is None or (ctx.now - ts).total_seconds() > int(ctx.cfg.get("capabilities_max_age_s", CAPS_MAX_AGE_S)):
        raise Hold("S3_EXECUTOR_EVIDENCE_STALE", "CAPABILITIES.json is older than the freshness limit (or carries no time): the executor's state is unknown", soft=True)
    return {"executor_revision": c.get("executor_revision")}


def staged_dir(ctx: Ctx) -> Path:
    d = (ctx.cfg.get("dispatch") or {}).get("staged_dir")
    if not d:
        raise Hold("S3_NO_STAGED_DIR", "config dispatch.staged_dir (the final request templates) is missing")
    return Path(d)


def template(ctx: Ctx, name: str, what: str) -> tuple[dict, bytes]:
    if not _NAME.fullmatch(name):
        raise Hold("S3_TEMPLATE_NAME", f"{what}: {name!r} is not a plain template file name")
    p = staged_dir(ctx) / name
    if not p.is_file():
        raise Hold("S3_TEMPLATE_MISSING", f"{what}: the staged template {name} does not exist")
    raw = p.read_bytes()
    try:
        d = json.loads(raw)
    except ValueError:
        raise Hold("S3_TEMPLATE_UNREADABLE", f"{what}: {name} is not JSON") from None
    if not isinstance(d, dict) or not isinstance(d.get("operation_id"), str) or not sc._SAFE_ID.fullmatch(d["operation_id"]):
        raise Hold("S3_TEMPLATE_BAD", f"{what}: {name} has no safe operation_id")
    return d, raw


def check_rebind(ctx: Ctx, m: str) -> dict:
    disp = ctx.cfg.get("dispatch") or {}
    want_v = str(disp.get("pack_version", "1.7"))
    p = ctx.path("rebind", "pack_rebind.json")
    if not p.exists():
        arg = disp.get("rebind_argv")
        if arg and all(isinstance(t, str) and _TOKEN.fullmatch(t) for t in arg):
            argv = [t.replace("{head}", m) for t in arg]
            emit_doc(ctx, "A3.REBIND", f"REBIND.{m}", {"kind": "harness_command", "argv": argv, "runs": False, "main": m,
                                                      "authority": next(a["authority"] for a in ACTIONS if a["id"] == "A3.REBIND")}, " ".join(argv) + "\n")
        raise Hold("S3_REBIND_PENDING", f"the v{want_v} rebind to {m[:12]} is not evidenced yet ({p})", soft=True)
    d = read_json(ctx, p, "the rebind record", "S3")
    if not isinstance(d, dict) or d.get("schema") != REBIND_SCHEMA:
        raise Hold("S3_REBIND_BAD_SHAPE", f"the rebind record is not a {REBIND_SCHEMA} document")
    if str(d.get("pack_version")) != want_v:
        raise Hold("S3_REBIND_VERSION", f"the rebind is pack v{d.get('pack_version')}, not v{want_v}")
    if d.get("main_head") != m:
        raise Hold("S3_REBIND_STALE_HEAD", f"the rebind is bound to {str(d.get('main_head'))[:12]}, not the merge commit {m[:12]}")
    sd = staged_dir(ctx)
    if not sd.is_dir() or d.get("staged_sha256") != sha_dir(sd):
        raise Hold("S3_REBIND_STAGED_CHANGED", "the staged templates are not the ones the rebind record digests (edited after the rebind, or the digest was never measured)")
    stale = []
    for f in sorted(sd.glob("*.json")):
        try:
            t = json.loads(f.read_bytes())
        except ValueError:
            raise Hold("S3_TEMPLATE_UNREADABLE", f"{f.name} is not JSON") from None
        if isinstance(t, dict) and t.get("kind") in PRODUCTION_KINDS and t.get("reviewed_commit") != m:
            stale.append(f.name)
    if stale:
        raise Hold("S3_STALE_PINS", f"staged production templates not pinned to {m[:12]}: {', '.join(stale)}")
    return {"rebind_sha256": sc.sha256_file(p), "staged_sha256": d["staged_sha256"]}


def dispatch_names(ctx: Ctx) -> list[str]:
    disp = ctx.cfg.get("dispatch") or {}
    names = [disp.get("century_template")] + list((ctx.cfg.get("verification") or {}).get("templates") or [])
    if not names[0] or any(not isinstance(n, str) for n in names):
        raise Hold("S3_NO_TEMPLATES", "config dispatch.century_template (and verification.templates) must name staged template files")
    return names


def check_rehearsal(ctx: Ctx, m: str) -> dict:
    p = ctx.path("rehearsal", str(Path("rehearsal") / m[:12] / "REHEARSAL.json"))
    disp = ctx.cfg["dispatch"]
    if not p.exists() or stale_rehearsal(p, m):
        sandbox = Path(disp.get("sandbox_root") or ctx.out / "scratch") / f"admission-{m[:12]}"
        args = ["--sandbox", str(sandbox), "--staged", str(staged_dir(ctx)), "--repo", ctx.cfg["repo"], "--main-ref", m, "--out", str(p.parent)]
        if disp.get("sql_dir"):
            args += ["--sql", str(disp["sql_dir"])]
        if disp.get("capabilities"):
            args += ["--capabilities", str(disp["capabilities"])]
        run_tool(ctx, "A3.REHEARSAL", "admission_rehearsal.py", args, f"REHEARSAL.{m}", ok_codes=(0, 1))
    rep = read_json(ctx, p, "the admission rehearsal report", "S3")
    if not isinstance(rep, dict) or rep.get("schema") != REHEARSAL_SCHEMA:
        raise Hold("S3_REHEARSAL_BAD_SHAPE", f"the rehearsal report is not a {REHEARSAL_SCHEMA} document")
    if rep.get("main") != m:
        raise Hold("S3_REHEARSAL_STALE_MAIN", f"the rehearsal judged main {str(rep.get('main'))[:12]}, not {m[:12]}")
    if rep.get("flags") != []:
        raise Hold("S3_REHEARSAL_FLAGS", f"the rehearsal raised flags: {rep.get('flags')}")
    controls = rep.get("controls")
    if not isinstance(controls, list) or not controls or any(c.get("ok") is not True for c in controls if isinstance(c, dict)) or not all(isinstance(c, dict) for c in controls):
        raise Hold("S3_REHEARSAL_CONTROLS", "the rehearsal's negative controls are missing or one did not refuse its planted defect (a validator that admits a stale pin shows here)")
    rows = (rep.get("sets") or {}).get(REHEARSAL_SET)
    if not isinstance(rows, list) or not rows:
        raise Hold("S3_REHEARSAL_NO_SET", f"the rehearsal carries no {REHEARSAL_SET!r} template set")
    by_name = {r.get("template"): r for r in rows if isinstance(r, dict)}
    refused = []
    for name in dispatch_names(ctx):
        v = (by_name.get(name) or {}).get("verdict")
        if not (isinstance(v, dict) and v.get("admitted") is True):
            refused.append(f"{name}:{(v or {}).get('code', 'not_rehearsed')}")
    if refused:
        raise Hold("S3_TEMPLATES_NOT_ADMITTED", f"dispatch-path templates not admitted by the real validators: {', '.join(refused)}")
    return {"rehearsal_sha256": sc.sha256_file(p), "templates_admitted": len(dispatch_names(ctx))}


def stale_rehearsal(p: Path, m: str) -> bool:
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("main") != m
    except (OSError, ValueError):
        return True


def act_dispatch(ctx: Ctx, m: str) -> dict:
    name = ctx.cfg["dispatch"]["century_template"]
    t, raw = template(ctx, name, "century dispatch")
    if t.get("kind") not in DISPATCH_KINDS:
        raise Hold("S3_DISPATCH_KIND", f"the century template's kind {t.get('kind')!r} is not one of {DISPATCH_KINDS}")
    if t.get("reviewed_commit") != m:
        raise Hold("S3_STALE_PINS", f"the century template is pinned to {str(t.get('reviewed_commit'))[:12]}, not {m[:12]}")
    emit_request(ctx, "A3.DISPATCH_REQUEST", t["operation_id"], raw, "century dispatch")
    return {"operation_id": t["operation_id"], "kind": t["kind"]}


# ── S4: the build is complete -> verification launches ───────────────────────────────────────────────────────────────────────────────

def check_build(ctx: Ctx, m: str, dispatch: dict) -> dict:
    op = dispatch["operation_id"]
    rec, text, rsha = need_receipt(ctx, op, "century dispatch", "S4", dispatch["kind"])
    if rec.get("reviewed_commit") != m:
        raise Hold("S4_DISPATCH_OTHER_COMMIT", f"the dispatch receipt is bound to {str(rec.get('reviewed_commit'))[:12]}, not {m[:12]}")
    launch = last_json(text, LAUNCH_SCHEMA)
    if launch is None or launch.get("status") != "LAUNCHED" or not _RUN_UUID.fullmatch(str(launch.get("run_id"))) or not _EXEC.fullmatch(str(launch.get("execution_name"))):
        raise Hold("S4_NO_LAUNCH_EVIDENCE", "the dispatch receipt carries no LAUNCHED ky.century_launch/1 record with a run id and execution name (completion is never the launch)")
    ex, run_id = launch["execution_name"], launch["run_id"]
    base = f"chain-build-{re.sub('[^0-9A-Za-z]+', '-', ctx.cfg['generation'])}-{m[:12]}-{ex}-e"
    epoch = int(ctx.now.timestamp() // int(ctx.cfg.get("readback_every_s", 300)))
    have = sorted((int(f.name[len(base):-len(".json")]) for f in (ctx.ops / "receipts").glob(base + "*.json")
                   if f.name[len(base):-len(".json")].isdigit()), reverse=True) if (ctx.ops / "receipts").is_dir() else []
    if not have or have[0] < epoch:                                                  # a fresh read-only readback every period while the build is not known to have ended
        readback_request(ctx, "A4.BUILD_READBACK", base + str(epoch), {"execution": ex})
    if not have:
        raise Hold("S4_AWAITING_RECEIPT", f"century dispatch launched run {run_id}; awaiting the first execution readback {base}{epoch}", soft=True)
    _, rtext, rsha2 = need_receipt(ctx, base + str(have[0]), "execution readback", "S4", "cloudrun_job_readback")
    d = last_json(rtext, READBACK_SCHEMA)
    e = d.get("execution") if isinstance(d, dict) else None
    if d is None or d.get("status") != "MEASURED" or not isinstance(e, dict) or e.get("name") != ex:
        raise Hold("S4_READBACK_BAD", "the execution readback is not a MEASURED record of the launched execution")
    if (d.get("provenance") or {}).get("image_commit") != m:
        raise Hold("S4_BUILD_IMAGE_NOT_M", "the execution ran an image that does not carry the merge commit")
    args = e.get("args") or []
    if "--run-id" not in args or args[args.index("--run-id") + 1:][:1] != [run_id]:
        raise Hold("S4_BUILD_OTHER_RUN", f"the execution {ex} was not started for run {run_id}")
    if e.get("outcome") == "FAILED":
        raise Hold("S4_BUILD_FAILED", f"the century build execution {ex} FAILED; teardown/cancel are owner-authorised kinds and are not taken by this program")
    if e.get("outcome") != "SUCCEEDED":
        raise Hold("S4_BUILD_RUNNING", f"the century build execution {ex} is {e.get('outcome')!r}", soft=True)
    return {"run_id": run_id, "execution": ex, "readback_sha256": rsha2, "dispatch_receipt_sha256": rsha}


def act_verification(ctx: Ctx, m: str) -> list[str]:
    names = list((ctx.cfg.get("verification") or {}).get("templates") or [])
    if not names:
        raise Hold("S4_NO_VERIFICATION_TEMPLATES", "config verification.templates names no verification_job template: nothing can launch verification")
    loaded = []
    for n in names:
        t, raw = template(ctx, n, "verification")
        if t.get("kind") != VERIFY_KIND:
            raise Hold("S4_VERIFY_KIND", f"{n}: kind {t.get('kind')!r} is not {VERIFY_KIND}")
        if t.get("reviewed_commit") != m:
            raise Hold("S3_STALE_PINS", f"{n} is pinned to {str(t.get('reviewed_commit'))[:12]}, not {m[:12]}")
        loaded.append((t["operation_id"], raw))
    if len({o for o, _ in loaded}) != len(loaded):
        raise Hold("S4_VERIFY_DUPLICATE_OPS", "two verification templates share an operation id")
    for op, raw in loaded:                                                            # ALL shards in this one poll (R8: the same minute)
        emit_request(ctx, "A4.VERIFY_REQUEST", op, raw, "verification shard")
    return [o for o, _ in loaded]


# ── S5: every verification receipt + the seal controller's own aggregate detector -> hand off ──────────────────────────────────────────

def check_verification_and_aggregate(ctx: Ctx, m: str, ops_ids: list[str]) -> dict:
    seal = ctx.cfg.get("seal") or {}
    for op in ops_ids:
        rec, _, _ = need_receipt(ctx, op, "verification shard", "S5", VERIFY_KIND)
        if rec.get("reviewed_commit") != m:
            raise Hold("S5_VERIFY_OTHER_COMMIT", f"{op}: the receipt is bound to {str(rec.get('reviewed_commit'))[:12]}, not {m[:12]}")
    adopted = adopted_doc(ctx, m, ops_ids)
    scratch = Path(tempfile.mkdtemp(prefix="chain-seal-")) if ctx.dry else Path(seal.get("out") or ctx.out / "seal")
    try:
        sc.check_aggregate(adopted, ctx.ops, scratch)
    except sc.NotReady as exc:
        raise Hold(f"S5_AGGREGATE_{exc.kind}", exc.reason, soft=exc.kind in (sc.AWAITING_READBACK,)) from None
    finally:
        if ctx.dry:
            import shutil
            shutil.rmtree(scratch, ignore_errors=True)
    return {"adopted": adopted}


def adopted_doc(ctx: Ctx, m: str, ops_ids: list[str]) -> dict:
    seal = ctx.cfg.get("seal") or {}
    for k in ("aggregate_file", "expected_classes"):
        if not seal.get(k):
            raise Hold("S5_SEAL_CONFIG", f"config seal.{k} is missing: the aggregate cannot be read")
    a = {"chart_id": ctx.cfg["chart_id"], "generation": ctx.cfg["generation"], "head": m, "verification_operation_id": seal.get("verification_operation_id") or ops_ids[0],
         "aggregate_file": str(seal["aggregate_file"]), "expected_classes": list(seal["expected_classes"]), "repo": ctx.cfg["repo"]}
    for k in ("item_id", "kyd", "reviewed_commit", "expected_approver", "triggering_actor", "quiescence_operation_id", "scripts_dir", "aggregate_readback_operation_id", "expected_class_count"):
        if seal.get(k) is not None:
            a[k] = seal[k]
    if a["verification_operation_id"] not in ops_ids:
        raise Hold("S5_SEAL_CONFIG", "seal.verification_operation_id is not one of the verification templates' operation ids")
    return a


def act_handoff(ctx: Ctx, adopted: dict) -> str:
    target = Path((ctx.cfg.get("seal") or {}).get("adopted_file") or sc.DEFAULT_ADOPTED)
    if target.exists():
        cur = None
        with contextlib.suppress(OSError, ValueError):
            cur = json.loads(target.read_text())
        if isinstance(cur, dict) and (cur.get("generation"), cur.get("head")) == (adopted["generation"], adopted["head"]):
            ctx.note("A5.HANDOFF", "ALREADY", str(target))
            return "ALREADY"
        raise Hold("S5_ADOPTED_FILE_CONFLICT", f"{target} already names another generation/head; it is never overwritten by this program")
    text = json.dumps(adopted, indent=1, sort_keys=True) + "\n"
    if ctx.dry:
        ctx.note("A5.HANDOFF", "WOULD_APPLY" if ctx.apply else "WOULD_EMIT", {"to": str(target if ctx.apply else ctx.out / "ADOPTED_CENTURY.proposed.json")})
        return "WOULD"
    with locked(ctx.out):
        if not ctx.apply:
            sc.atomic_write(ctx.out / "ADOPTED_CENTURY.proposed.json", text)
            ctx.note("A5.HANDOFF", "EMITTED", str(ctx.out / "ADOPTED_CENTURY.proposed.json"))
            ctx.page("CHAIN-HANDOFF-PROPOSED", f"head={adopted['head'][:12]}", f"the aggregate PASSED; the adopted file is proposed at {ctx.out / 'ADOPTED_CENTURY.proposed.json'}: copy it to {target}")
            return "EMITTED"
        sc.atomic_write(target, text)
        sc.load_adopted(target)                                                       # the seal controller's own loader must accept what was written
        ctx.set_marker(f"HANDOFF.{adopted['generation']}.{adopted['head']}", {"adopted_file": str(target), "sha256": sc.sha256_file(target)})
        ctx.note("A5.HANDOFF", "APPLIED", str(target))
    ctx.page("CHAIN-HANDOFF", f"head={adopted['head'][:12]}", f"aggregate PASSED; adopted file {target} written; the seal controller takes over")
    return "NEW"


# ── the poll ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def evaluate(ctx: Ctx, report: list[dict]) -> str:
    """Run S0..S5 in order; each stage's detector must read true before the next is looked at.  Returns the last stage passed; raises Hold at the first that does not."""
    passed = "START"

    def stage(sid: str, fn):
        nonlocal passed
        try:
            ev = fn()
        except Hold as h:
            report.append({"stage": sid, "name": dict(STAGES)[sid], "state": "HOLD", "code": h.code, "reason": h.reason, "soft": h.soft})
            raise
        report.append({"stage": sid, "name": dict(STAGES)[sid], "state": "PASS", "evidence": ev})
        ctx.evidence[sid] = ev
        if not ctx.dry:
            for w in (ctx.out / "markers").glob(f"WAIT.{sid}.*"):                       # the wait is over: the next wait of this stage starts a fresh stall clock
                w.unlink(missing_ok=True)
        passed = sid
        return ev

    def s0():
        ev = check_trial_ready(ctx)
        ev[K9_PRECONDITION] = check_k9_migrations_applied(ctx)
        act_arm_tr(ctx)
        return ev

    ready = stage("S0", s0)

    def s1():
        verdict = check_tr_verdict(ctx, ready)
        rv = check_rvint(ctx)
        pr = check_pr_and_enqueue(ctx)
        return {**verdict, **rv, **pr}

    s1ev = stage("S1", s1)
    ctx.M = m = s1ev["merge_commit"]

    def s2():
        ev = check_on_main(ctx, m)
        runs = runs_for(ctx, m)
        ev.update(check_ci(ctx, m, runs))
        dep = check_deploy(ctx, m, runs)
        ev.update(dep)
        ev.update(check_image(ctx, m, dep["deploy_run_id"]))
        ev.update(check_equivalence(ctx, m))
        return ev

    stage("S2", s2)

    def s3():
        ev = check_executor(ctx, m)
        ev.update(check_rebind(ctx, m))
        ev.update(check_rehearsal(ctx, m))
        ev["dispatch"] = act_dispatch(ctx, m)
        return ev

    s3ev = stage("S3", s3)

    def s4():
        ev = check_build(ctx, m, s3ev["dispatch"])
        ev["verification_operations"] = act_verification(ctx, m)
        return ev

    s4ev = stage("S4", s4)

    def s5():
        ev = check_verification_and_aggregate(ctx, m, s4ev["verification_operations"])
        ev["handoff"] = act_handoff(ctx, ev.pop("adopted"))
        return ev

    stage("S5", s5)
    return passed


def handle_hold(ctx: Ctx, h: Hold, stage_id: str, stall_s: int) -> dict:
    """Page rules: a hard hold pages once per (stage, code, reason); a soft hold pages once, only after the stage has waited longer than stall_s."""
    info = {"paged": False}
    if ctx.dry:
        return info
    tag = hashlib.sha256(f"{h.code}|{h.reason}".encode()).hexdigest()[:12]
    with locked(ctx.out):
        if h.soft:
            wname = f"WAIT.{stage_id}.{h.code}"
            w = ctx.read_marker(wname)
            if w is None:
                ctx.set_marker(wname, {"first_seen": sc.utc(ctx.now)})
                return info
            first = parse_ts(w.get("first_seen"))
            if first is not None and (ctx.now - first).total_seconds() > stall_s:
                info["paged"] = ctx.page("CHAIN-STALL", f"stage={stage_id} code={h.code}", f"waited_over_s={stall_s} reason={h.reason[:300]}")
            return info
        info["paged"] = ctx.page("CHAIN-HOLD", f"stage={stage_id} code={h.code} r={tag}", f"reason={h.reason[:400]}")
    return info


def run(config_path, ops, out, pages_log, requests_dir=None, gh=None, tools=None, now=None, apply=False, dry=False) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    out = Path(out)
    status = {"schema": SCHEMA, "ts": sc.utc(now), "mode": "dry-run" if dry else "apply" if apply else "emit", "state": "HOLD", "stage": "START"}
    report: list[dict] = []
    ctx = None
    try:
        cfg = load_config(config_path)
        ctx = Ctx(cfg, ops, out, pages_log, requests_dir or Path(ops) / "requests", gh or GhCli(), tools or Tools(), now, apply, dry)
        status["key"] = ctx.key
        passed = evaluate(ctx, report)
        status.update(state="HANDED_OFF", stage=passed, kind="HANDED_OFF")
        line = f"DISPATCH-CHAIN {status['ts']} HANDED_OFF key={ctx.key}"
    except Hold as h:
        sid = report[-1]["stage"] if report and report[-1]["state"] == "HOLD" else "START"
        status["stage"] = next((r["stage"] for r in reversed(report) if r["state"] == "PASS"), "START")
        status.update(state="HOLD", kind=h.code, reason=h.reason, soft=h.soft, hold_stage=sid)
        if ctx is not None:
            status.update(handle_hold(ctx, h, sid, int((ctx.cfg.get("stall_s_by_stage") or {}).get(sid, ctx.cfg.get("stall_s", STALL_S)))))
        elif not dry:                                                              # no config, no key: still page, once per code
            with contextlib.suppress(OSError):
                sc.append_page(Path(pages_log), f"PAGE CHAIN-HOLD key=config code={h.code} ", f"{status['ts']} PAGE CHAIN-HOLD key=config code={h.code} reason={h.reason[:300]}\n")
        line = f"DISPATCH-CHAIN {status['ts']} stage={status['stage']} HOLD {h.code}{' (soft)' if h.soft else ''}: {h.reason}"
    reached = {r["stage"] for r in report}
    for sid, name in STAGES:
        if sid not in reached:
            report.append({"stage": sid, "name": name, "state": "NOT_REACHED", "would_do": [a["id"] for a in ACTIONS if a["stage"] == sid]})
    status.update(line=line, stages=report)
    if ctx is not None:
        status["actions"] = ctx.would
    if not dry:
        out.mkdir(parents=True, exist_ok=True)
        sc.atomic_write(out / "CHAIN_STATUS.json", json.dumps(status, indent=1, sort_keys=True, default=str) + "\n")
    return status


def format_plan(status: dict) -> str:
    L = [status["line"], "", f"mode: {status['mode']}", "would-do sequence:"]
    for r in status["stages"]:
        extra = f" — {r['code']}: {r['reason']}" if r["state"] == "HOLD" else ""
        L.append(f"  {r['stage']} {r['name']:<24} {r['state']}{extra}")
        for a in ACTIONS:
            if a["stage"] == r["stage"]:
                taken = [x for x in status.get("actions", []) if x["action"] == a["id"]]
                L.append(f"      {a['id']:<22} {a['kind']:<16} by {a['performed_by']:<28} {taken[0]['state'] if taken else ('(after this stage passes)' if r['state'] != 'PASS' else '(not needed)')}")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", default=os.environ.get("CHAIN_CONFIG", DEFAULT_CONFIG))
    ap.add_argument("--ops", default=os.environ.get("CHAIN_OPS", DEFAULT_OPS))
    ap.add_argument("--out", default=os.environ.get("OUT"))
    ap.add_argument("--pages-log", default=os.environ.get("CHAIN_PAGES_LOG"))
    ap.add_argument("--requests-dir", default=os.environ.get("CHAIN_REQUESTS_DIR"))
    ap.add_argument("--python", default="/opt/homebrew/bin/python3")
    ap.add_argument("--apply", action="store_true", help="also perform the allow-listed actions this program is authorised to perform (see --list-actions)")
    ap.add_argument("--dry-run", action="store_true", help="write nothing; print the would-do sequence")
    ap.add_argument("--list-actions", action="store_true", help="print every action, its kind and its authority, and exit")
    a = ap.parse_args(argv)
    if a.list_actions:
        for x in ACTIONS:
            print(f"{x['id']:<22} {x['stage']} {x['kind']:<16} by {x['performed_by']}\n    {x['what']}\n    authority: {x['authority']}")
        return 0
    if not a.out or not a.pages_log:
        print("dispatch_chain: --out (or $OUT) and --pages-log are required", file=sys.stderr)
        return 2
    if a.apply and a.dry_run:
        print("dispatch_chain: --apply and --dry-run are exclusive", file=sys.stderr)
        return 2
    status = run(a.config, a.ops, a.out, a.pages_log, a.requests_dir, tools=Tools(a.python), apply=a.apply, dry=a.dry_run)
    print(format_plan(status) if a.dry_run else status["line"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
