#!/usr/bin/env python3
"""kyveto.py — the deterministic veto-window handler of KĀLA-YANTRA v3 (relaunch plan v2.7 §4a.3, §6 SURROGATE
row, §10 "Start (D-7)", §13 "veto expired", pairing rule KW-04; owner decisions D-4 amended, D-7).

    kyveto.py tick [--now ISO] [--authorised-commit C --entrypoints-digest D] [--as HOLDER_ID]
                   [--holder-kind controller|supervisor]          one pass over the pending veto-class decisions
    kyveto.py status [--now ISO] [--authorised-commit C --entrypoints-digest D]        read-only
    kyveto.py fingerprint --target FILE        the target fingerprint the surrogate records at proposal (read-only)

The owner surrogate only PROPOSES a veto-class decision: it appends a PENDING_VETO line to
$KY_RUN/DECISIONS_SURROGATE.jsonl and publishes nothing. This handler — a script, never a model — is the only
actor that makes such a decision effective. The latest line of a decision id is its state; the handler appends
transition lines with "by": "kyveto" and a "reason". For every decision whose latest state is PENDING_VETO (or
that this handler left EFFECTIVE but not yet EXECUTED), under the lock `decision.<id>` and after a FRESH re-read:

  (a) an owner `veto` command for it, QUEUED or APPLIED      → VETOED; the command is marked applied; never executed
  (b) now < veto_deadline                                    → left pending (seconds remaining reported)
  (c) notification.submitted is not exactly true             → FAILED notification_not_submitted
      (also: the deadline is less than 30 minutes after the notification → FAILED veto_window_too_short)
  (d) $KY_ROOT/HOLD, an owner pause (applied, or queued and not yet applied), $KY_RUN/STOP_veto, or a command
      queue that cannot be read                              → left pending, reported "held"; nothing fails
  (e) recheck — the first failure appends FAILED with its named reason: class (hard_stop_never_delegated), record
      immutability across the decision's lines (decision_record_mutated: <field>), authority (authority_unbound /
      authority_unknown / authority_changed), target (target_unbound / unknown_target_kind / target_malformed /
      target_changed), tracker_decision shape, the awaiting item (awaiting_unbound / awaiting_not_open /
      superseded_by_owner_decide / awaiting_already_decided), class hold (class_hold: HOLD_MERGES), the ky CLI
      when a tracker decision must be published, and the class's own prerequisites
  (f) publish, then execute, each through its own kyaction record:
        <id>.publish   `ky decide <D-id> --outcome <o> --as steward --delegated --detail "<id>: <decision>"`
                       (only where target.tracker_decision = {"id", "outcome"} is set); a non-zero exit is
                       FAILED publication_failed, an unobservable one stays unfinished and blocks — never retried
        EFFECTIVE      appended with effective_at once the publication is recorded
        <id>.execute   the class executor; an unfinished record is reconciled against the disk first
        EXECUTED       appended only after the executor's observed result is recorded
      The plan's order is kept (§4a.3: "publishes the effective decision … and executes"): nothing irreversible
      is executed for a decision the tracker refused, and a failed publication is FAILED, never EXECUTED.

Target classes (registry keyed by target.kind; every target carries `fingerprint`, see `kyveto.py fingerprint`):
  capacity            {kind, builders, verifiers[, tracker_decision]} → $KY_RUN/KY_WORKERS, KY_VERIFIERS (atomic)
  plan_bundle_change  {kind, old_commit, new_commit, old_manifest_digest, new_manifest_digest, review_receipts[]
                      [, tracker_decision]} → the next immutable $KY_RUN/ACTIVATION_RECORD.<n>.json
  campaign_start, protected_window        their executors are later deliverables: always FAILED
                      "executor_unavailable: …" — never a faked success
An unknown kind is FAILED unknown_target_kind.

Exactly one handler runs at a time: `--as ID` must name the live owner of $KY_RUN/locks/veto, otherwise the tick
takes that lock for its own duration (and reports "skipped" when another handler holds it).

Environment: KY_ROOT (/Users/Dev/kalayantra), KY_RUN ($KY_ROOT/run), KY_FLEET ($KY_ROOT/fleet_live), KY_BIN
($KY_ROOT/bin/ky), KY_SOURCE_REPO (the git checkout used to compare the owner-decisions blob; when the variable
is absent, DEFAULT_SOURCE_REPO is used only if it exists and is itself a git work tree — otherwise that
comparison is unverifiable and a bundle change is refused), KY_GIT (/usr/bin/git), KY_OWNER_DECISIONS_PATH.
`ky` receives an allow-listed environment only.

Exit codes: 0 pass completed · 1 fingerprint refused · 3 completed, but something needs attention (an unreadable
log or queue, an unreconciled action, an effect that contradicts a veto) · 64 usage · 66 run directory missing ·
75 `--as` does not name the live owner of the veto role lock.   Python >= 3.9, standard library only.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kyaction  # noqa: E402
import kycommands  # noqa: E402

HANDLER = "kyveto"
STATES = ("PROPOSED", "PENDING_VETO", "EFFECTIVE", "EXECUTED", "VETOED", "FAILED")
TERMINAL = ("EXECUTED", "VETOED", "FAILED")
CLASSES = ("routine", "veto", "hard_stop")
VETO_WINDOW_S = 1800                    # the owner's window: 30 minutes from the submitted notification
CAPACITY_CEILING = 15                   # owner policy: at most 15 copies per project per tool
OWNER_DECISIONS_PATH = "00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md"
DEFAULT_SOURCE_REPO = "/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign"     # second line of defence
KY_ENV_NAMES = ("HOME", "USER", "LANG", "TERM", "PATH", "TMPDIR", "KY_ROOT", "KY_RUN", "KY_FLEET")
BASE_FIELDS = ("id", "awaiting", "class", "decision", "rationale", "evidence", "target", "authority",
               "notification", "veto_deadline", "effective_at")
SD_RE, AW_RE = kycommands.SD_RE, kycommands.AW_RE
HEX_COMMIT = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
TRACKER_ID = re.compile(r"^D-[A-Za-z0-9][A-Za-z0-9._-]{0,59}\Z")
TRACKER_OUTCOME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
RECORD_NAME = re.compile(r"^ACTIVATION_RECORD\.([1-9][0-9]{0,5})\.json\Z")


class TargetError(Exception):
    """The target cannot be bound: .reason is the named refusal."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class NotHolder(Exception):
    """`--as` does not name the live owner of the veto role lock."""


class RunMissing(Exception):
    """The run directory does not exist; the handler never creates one."""


class Env:
    """Paths and tools, all taken from one mapping (the process environment unless one is given)."""

    def __init__(self, environ=None):
        e = dict(os.environ if environ is None else environ)
        self.environ = e
        self.root = Path(e.get("KY_ROOT") or "/Users/Dev/kalayantra")
        self.run = Path(e.get("KY_RUN") or self.root / "run")
        self.fleet = Path(e.get("KY_FLEET") or self.root / "fleet_live")
        self.ky_bin = Path(e.get("KY_BIN") or self.root / "bin" / "ky")
        self.git = e.get("KY_GIT") or "/usr/bin/git"
        self._repo, self._repo_known = e.get("KY_SOURCE_REPO") or None, "KY_SOURCE_REPO" in e
        self.owner_decisions_path = e.get("KY_OWNER_DECISIONS_PATH") or OWNER_DECISIONS_PATH
        try:
            self.ky_timeout = float(e.get("KYVETO_KY_TIMEOUT_S") or 120)
        except ValueError:
            self.ky_timeout = 120.0


    @property
    def repo(self):
        """The checkout the owner-decisions blob is read from, or None (then nothing is verifiable). An explicit
        KY_SOURCE_REPO is taken as given, even empty; only an absent one falls back to the default, resolved on
        first use so that nothing but a bundle change ever looks at that checkout."""
        if not self._repo_known:
            self._repo, self._repo_known = default_source_repo(self), True
        return self._repo


class Ctx:
    """What a target class may look at: the environment, the deciding id, its authority and the tick's time."""

    def __init__(self, env, decision_id, authority, now):
        self.env, self.decision_id, self.authority, self.now = env, decision_id, authority or {}, now


# ───────────────────────────────────────── the decision log ─────────────────────────────────────────

def _not_json(name):
    raise ValueError("%s is not JSON" % name)


def load_decisions(path):
    """→ (history, problems, unusable). history: {decision id: [its lines, in file order]}.
    problems: lines that cannot be attributed to a decision (not JSON, no SD id) — while any exists NO decision's
    state is known, so the handler makes no transition at all. unusable: {id: reason} for decisions with a line
    whose state is not a decision state (a hard_stop record without a state is not the handler's business)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        return {}, [], {}
    except OSError as e:
        return {}, ["decision log unreadable: %s" % type(e).__name__], {}
    history, problems, unusable = {}, [], {}
    for n, raw in enumerate(data.split(b"\n"), 1):
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw.decode("utf-8"), parse_constant=_not_json)
        except ValueError:
            problems.append("decision log line %d: not JSON" % n)
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str) or not SD_RE.match(obj["id"]):
            problems.append("decision log line %d: no usable decision id" % n)
            continue
        history.setdefault(obj["id"], []).append(obj)
        if obj.get("state") not in STATES and obj.get("class") != "hard_stop":
            unusable.setdefault(obj["id"], "decision log line %d: %s has no usable state" % (n, obj["id"]))
    return history, problems, unusable


def append_line(path, obj):
    """One line, one write, fsynced. A previous writer's unterminated last line never swallows this one."""
    data = (json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        size = os.fstat(fd).st_size
        if size:
            with open(path, "rb") as f:
                f.seek(size - 1)
                if f.read(1) != b"\n":
                    data = b"\n" + data
        if os.write(fd, data) != len(data):
            raise OSError("short append to %s" % path)
        os.fsync(fd)
    finally:
        os.close(fd)


def _state(line):
    return line.get("state") if line.get("state") in STATES else None


def _by_handler_effective(lines):
    for line in lines:
        if _state(line) == "EFFECTIVE" and line.get("by") == HANDLER:
            return line
    return None


def is_candidate(lines):
    """The handler's business: latest PENDING_VETO, or published by this handler and not yet finished."""
    latest = _state(lines[-1]) if lines else None
    return latest == "PENDING_VETO" or (latest == "EFFECTIVE" and _by_handler_effective(lines) is not None)


# ───────────────────────────────────────── authority ─────────────────────────────────────────

def _bundle(commit, digest):
    if isinstance(commit, str) and HEX_COMMIT.match(commit) and isinstance(digest, str) and HEX64.match(digest):
        return {"source_commit": commit, "entrypoints_digest": digest}
    return None


def resolve_authority(env, commit=None, digest=None):
    """→ ({"source_commit", "entrypoints_digest"} | None, source). Arguments win; otherwise
    $KY_RUN/PLANNER_STATE.json `authorised_source` {source_commit | commit, entrypoints_digest}. None = unknown."""
    if commit is not None or digest is not None:
        bundle = _bundle(commit, digest)
        if bundle is None:
            raise ValueError("--authorised-commit (full commit id) and --entrypoints-digest (sha256) go together")
        return bundle, "arguments"
    state, _ = kyaction.read_json(env.run / "PLANNER_STATE.json")
    source = state.get("authorised_source") if isinstance(state, dict) else None
    if isinstance(source, dict):
        bundle = _bundle(source.get("source_commit", source.get("commit")), source.get("entrypoints_digest"))
        if bundle is not None:
            return bundle, "planner_state"
    return None, "unknown"


def _git(env, repo, *args):
    """stdout of a read-only `git -C <repo> rev-parse …`, or None when git fails or cannot be run."""
    try:
        r = subprocess.run([env.git, "-C", str(repo), "rev-parse"] + list(args),
                           capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
                           env={"PATH": env.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C",
                                "HOME": env.environ.get("HOME", "/nonexistent"), "GIT_CONFIG_NOSYSTEM": "1",
                                "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"})
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def default_source_repo(env):
    """DEFAULT_SOURCE_REPO iff that directory exists and git itself says it is the top level of a work tree
    (being merely inside another checkout does not count); otherwise None — never a guess."""
    path = DEFAULT_SOURCE_REPO
    if not isinstance(path, str) or not path or not os.path.isdir(path):
        return None
    top = _git(env, path, "--show-toplevel")
    if not top or os.path.realpath(top) != os.path.realpath(path):
        return None
    return path


def owner_decisions_blob(env, commit):
    """The blob id of the owner-decisions file at a full commit id, or None when it cannot be established."""
    repo = env.repo
    if not repo or not isinstance(commit, str) or not HEX_COMMIT.match(commit):
        return None
    out = _git(env, repo, "--verify", "--quiet", "%s:%s" % (commit, env.owner_decisions_path))
    return out if out and HEX_COMMIT.match(out) else None


# ───────────────────────────────────────── target classes ─────────────────────────────────────────

def _digest(path):
    """sha256 of a file, None when it does not exist; any other read error propagates (the state is unknown)."""
    try:
        with open(path, "rb") as f:
            return kyaction.sha_bytes(f.read())
    except FileNotFoundError:
        return None


def _text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(4096)
    except FileNotFoundError:
        return None


def _shown(text):
    return None if text is None else text.strip()[:32]


class Capacity:
    """target {kind, builders, verifiers}: the pool sizes the dispatcher reads from KY_WORKERS / KY_VERIFIERS."""
    kind = "capacity"
    merge_action = False
    FILES = (("builders", "KY_WORKERS"), ("verifiers", "KY_VERIFIERS"))

    def check(self, p):
        for key in sorted(set(p) - {"kind", "builders", "verifiers", "tracker_decision"}):
            return "unexpected key %s" % key
        for key, _ in self.FILES:
            v = p.get(key)
            if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= CAPACITY_CEILING:
                return "%s must be an integer from 1 to %d" % (key, CAPACITY_CEILING)
        return None

    def observed(self, p, ctx):                # fingerprint = current file contents + requested values
        return {name: _digest(ctx.env.run / name) for _, name in self.FILES}

    def precheck(self, p, ctx):
        return None

    def describe(self, p):
        return "capacity: KY_WORKERS → %d, KY_VERIFIERS → %d" % (p["builders"], p["verifiers"])

    def execute(self, p, ctx):
        result = {}
        for key, name in self.FILES:
            path, want = ctx.env.run / name, str(p[key])
            before = _text(path)
            written = before is None or before.strip() != want
            if written:
                kyaction.write_atomic(path, want + "\n")
            result[name] = {"before": _shown(before), "after": want, "written": written}
        return True, result

    def observer(self, p, ctx):
        try:
            seen = {name: _text(ctx.env.run / name) for _, name in self.FILES}
        except (OSError, ValueError) as e:
            return "unknown", {"error": type(e).__name__}
        shown = {name: _shown(text) for name, text in seen.items()}
        if all(shown[name] == str(p[key]) for key, name in self.FILES):
            return "done", {"observed": shown, "reconciled": True}
        return "not_done", {"observed": shown}


class PlanBundleChange:
    """target {kind, old_commit, new_commit, old_manifest_digest, new_manifest_digest, review_receipts[]}: one more
    link of the activation chain (pairing rule KW-04). It authorises a bundle, never campaign admission."""
    kind = "plan_bundle_change"
    merge_action = False

    def check(self, p):
        for key in sorted(set(p) - {"kind", "old_commit", "new_commit", "old_manifest_digest",
                                    "new_manifest_digest", "review_receipts", "tracker_decision"}):
            return "unexpected key %s" % key
        for key in ("old_commit", "new_commit"):
            if not isinstance(p.get(key), str) or not HEX_COMMIT.match(p[key]):
                return "%s must be a full commit id" % key
        for key in ("old_manifest_digest", "new_manifest_digest"):
            if not isinstance(p.get(key), str) or not HEX64.match(p[key]):
                return "%s must be a sha256 digest" % key
        receipts = p.get("review_receipts")
        if not isinstance(receipts, list) or not receipts or len(set(map(str, receipts))) != len(receipts) \
                or any(not isinstance(r, str) or not r.strip() for r in receipts):
            return "review_receipts must be a non-empty list of distinct paths"
        return None

    def _receipt(self, ctx, raw):
        path = Path(raw)
        return path if path.is_absolute() else ctx.env.run / path

    def _numbered(self, ctx):
        """{n: path} of ACTIVATION_RECORD.<n>.json, or a string naming a file that does not belong."""
        found = {}
        for path in sorted(ctx.env.run.glob("ACTIVATION_RECORD.*.json")):
            m = RECORD_NAME.match(path.name)
            if not m:
                return "unexpected file %s" % path.name
            found[int(m.group(1))] = path
        return found

    def chain(self, ctx):
        """→ ([(n, path, doc)], None) validated from its start, or (None, named reason).

        Every activation record is a link; the chain's root is the trust-root commit itself (no record). The
        un-numbered ACTIVATION_RECORD.json, when present, is link 0 and every numbered link chains after it:
        link 1 MUST name link 0 (file + sha256) as `previous`; a link 1 with `previous: null` beside it is a
        fork. Without link 0 a numbered-only chain is valid when link 1 has `previous: null`. Numbered links are
        contiguous from 1 and each names its predecessor's sha256."""
        found = self._numbered(ctx)
        if isinstance(found, str):
            return None, "activation_chain_invalid: %s" % found
        links, previous = [], None
        root = ctx.env.run / "ACTIVATION_RECORD.json"
        if os.path.lexists(root):
            doc, err = kyaction.read_json(root)
            if err or not isinstance(doc, dict):
                return None, "activation_chain_invalid: ACTIVATION_RECORD.json is unreadable"
            links.append((0, root, doc))
            previous = {"file": root.name, "sha256": kyaction.sha_file(root)}
        for n in range(1, len(found) + 1):
            if n not in found:                               # a gap: fewer files than the highest number
                return None, "activation_chain_invalid: ACTIVATION_RECORD.%d.json is missing from the sequence" % n
            doc, err = kyaction.read_json(found[n])
            if err or not isinstance(doc, dict) or doc.get("n") != n:
                return None, "activation_chain_invalid: %s is unreadable or misnumbered" % found[n].name
            if "previous" not in doc:
                return None, "activation_chain_invalid: %s states no `previous`" % found[n].name
            link = doc["previous"]
            if n == 1 and link is None and previous is not None:
                return None, ("activation_chain_fork: %s has no predecessor although ACTIVATION_RECORD.json exists"
                              % found[n].name)
            if link != previous:                             # None == None only for link 1 of a numbered-only chain
                return None, "activation_chain_invalid: %s does not chain to its predecessor" % found[n].name
            links.append((n, found[n], doc))
            previous = {"file": found[n].name, "sha256": kyaction.sha_file(found[n])}
        return links, None

    def observed(self, p, ctx):
        links, err = self.chain(ctx)
        head = {"error": err} if err else ({"file": links[-1][1].name, "sha256": kyaction.sha_file(links[-1][1])}
                                           if links else None)
        return {"chain_head": head,
                "receipts": [{"path": raw, "sha256": kyaction.sha_file(self._receipt(ctx, raw))}
                             for raw in p["review_receipts"]]}

    def _receipts(self, p, ctx):
        """→ ([{path, sha256, verdict, reviewer_session_id}], None) or (None, named reason)."""
        out = []
        for raw in p["review_receipts"]:
            path = self._receipt(ctx, raw)
            doc, err = kyaction.read_json(path)
            if err == "missing":
                return None, "review_receipt_missing: %s" % raw
            if err or not isinstance(doc, dict):
                return None, "review_receipt_unreadable: %s" % raw
            if doc.get("verdict") != "ACCEPTED" or not isinstance(doc.get("reviewer_session_id"), str) \
                    or not doc["reviewer_session_id"].strip():
                return None, "review_receipt_not_accepted: %s" % raw
            if doc.get("source_commit") != p["new_commit"]:
                return None, "review_receipt_not_bound: %s is not a review of new_commit" % raw
            out.append({"path": str(path), "sha256": kyaction.sha_file(path), "verdict": "ACCEPTED",
                        "reviewer_session_id": doc["reviewer_session_id"]})
        return out, None

    def _verify(self, p, ctx):
        """→ (facts, None) when this change may be activated now, else (None, named reason)."""
        if p["old_commit"] != ctx.authority.get("source_commit"):
            return None, "old_commit_not_authorised_source"
        receipts, reason = self._receipts(p, ctx)
        if reason:
            return None, reason
        links, err = self.chain(ctx)
        if err:
            return None, err                                  # activation_chain_invalid / activation_chain_fork
        head = links[-1] if links else None                   # the true terminal link (link 0 if it is the only one)
        if head is not None:
            doc = head[2]
            if doc.get("new_commit", doc.get("source_commit")) != p["old_commit"]:
                return None, "activation_chain_mismatch: the previous record's new_commit is not old_commit"
            if doc.get("new_manifest_digest", doc.get("final_manifest_digest")) != p["old_manifest_digest"]:
                return None, ("activation_chain_mismatch: the previous record's manifest digest is not "
                              "old_manifest_digest")
        old_blob = owner_decisions_blob(ctx.env, p["old_commit"])
        new_blob = owner_decisions_blob(ctx.env, p["new_commit"])
        if old_blob is None or new_blob is None:
            return None, "owner_decisions_unverifiable"
        if old_blob != new_blob:
            return None, "owner_decisions_changed_owner_only"
        return {"receipts": receipts, "head": head, "old_blob": old_blob, "new_blob": new_blob}, None

    def precheck(self, p, ctx):
        return self._verify(p, ctx)[1]

    def describe(self, p):
        return "authorised bundle: %s → %s (next activation record)" % (p["old_commit"][:12], p["new_commit"][:12])

    def _mine(self, p, ctx):
        """The record this decision already wrote: (result, None), (None, None) when there is none, or
        (None, why) when a record names this decision but is not this change."""
        found = self._numbered(ctx)
        for n, path in sorted(found.items()) if isinstance(found, dict) else []:
            doc, err = kyaction.read_json(path)
            act = doc.get("authorising_act") if isinstance(doc, dict) else None
            if isinstance(act, dict) and act.get("id") == ctx.decision_id:
                if err or any(doc.get(k) != p[k] for k in ("old_commit", "new_commit", "old_manifest_digest",
                                                           "new_manifest_digest")):
                    return None, "%s names this decision but records another change" % path.name
                return {"file": path.name, "path": str(path), "n": n, "sha256": kyaction.sha_file(path)}, None
        return None, None

    def execute(self, p, ctx):
        mine, conflict = self._mine(p, ctx)
        if conflict:
            return False, {"reason": "activation_record_conflict: %s" % conflict}
        if mine:
            return True, mine                                 # idempotent: the same decision, the same record
        facts, reason = self._verify(p, ctx)
        if reason:
            return False, {"reason": reason}
        head = facts["head"]
        n = (head[0] if head else 0) + 1
        path = ctx.env.run / ("ACTIVATION_RECORD.%d.json" % n)
        doc = {"schema": "ky.activation_record/1", "n": n,
               "previous": {"file": head[1].name, "sha256": kyaction.sha_file(head[1])} if head else None,
               "old_commit": p["old_commit"], "new_commit": p["new_commit"],
               "old_manifest_digest": p["old_manifest_digest"], "new_manifest_digest": p["new_manifest_digest"],
               "review_receipts": facts["receipts"],
               "owner_decisions": {"path": ctx.env.owner_decisions_path, "old_blob": facts["old_blob"],
                                   "new_blob": facts["new_blob"]},
               "authorising_act": {"kind": "surrogate_decision", "id": ctx.decision_id},
               "campaign_admission": False, "created_at": ctx.now or kyaction.utc(), "created_by": HANDLER}
        if not kyaction.write_exclusive(path, json.dumps(doc, ensure_ascii=False, indent=1) + "\n", mode=0o444):
            return False, {"reason": "activation_chain_mismatch: %s was written by another actor" % path.name}
        return True, {"file": path.name, "path": str(path), "n": n, "sha256": kyaction.sha_file(path)}

    def observer(self, p, ctx):
        mine, conflict = self._mine(p, ctx)
        if conflict:
            return "unknown", {"error": conflict}
        return ("done", mine) if mine else ("not_done", {"activation_record_for": ctx.decision_id, "found": False})


class Unavailable:
    """A veto class whose executor is a later deliverable. It fails closed, in the recheck and again if it were
    ever reached: a helper's mere presence is not an executor, and no success is ever reported."""
    merge_action = False

    def __init__(self, kind, helper, evidence=()):
        self.kind, self.helper, self.evidence = kind, helper, tuple(evidence)

    def check(self, p):
        return None

    def observed(self, p, ctx):
        return {name: _digest(ctx.env.run / name) for name in self.evidence}

    def _reason(self, ctx):
        if not (ctx.env.fleet / self.helper).is_file():
            return "executor_unavailable: %s" % self.helper
        return "executor_unavailable: the %s executor is a later deliverable; %s alone executes nothing" % (
            self.kind, self.helper)

    def precheck(self, p, ctx):
        return self._reason(ctx)

    def describe(self, p):
        return "%s (no executor installed)" % self.kind

    def execute(self, p, ctx):
        return False, {"reason": self._reason(ctx)}

    def observer(self, p, ctx):
        return "unknown", {"error": self._reason(ctx)}


REGISTRY = {
    "capacity": Capacity(),
    "plan_bundle_change": PlanBundleChange(),
    "campaign_start": Unavailable("campaign_start", "kygate.sh", ("RELEASE_RECEIPT.json", "VERSIONS.json")),
    "protected_window": Unavailable("protected_window", "executor.py"),
}


def bind(target):
    """→ (class, params) of a target, or TargetError with the named refusal. params = target without fingerprint."""
    if not isinstance(target, dict):
        raise TargetError("target_unbound")
    cls = REGISTRY.get(target["kind"]) if isinstance(target.get("kind"), str) else None
    if cls is None:
        raise TargetError("unknown_target_kind")
    params = {k: v for k, v in target.items() if k != "fingerprint"}
    problem = cls.check(params)
    if problem:
        raise TargetError("target_malformed: %s" % problem)
    return cls, params


def fingerprint(target, env, ctx=None):
    """sha256 over the target's parameters (everything but `fingerprint`) and the class's view of the disk state
    it depends on. The surrogate records it at proposal; the handler recomputes it at expiry."""
    cls, params = bind(target)
    try:
        observed = cls.observed(params, ctx or Ctx(env, None, None, None))
        return kyaction.sha_bytes(kyaction.canonical(
            {"schema": "ky.target_fingerprint/1", "target": params, "observed": observed}))
    except (OSError, TypeError, ValueError) as e:
        raise TargetError("target_unreadable: %s" % type(e).__name__) from None


def tracker_decision(params):
    """→ None (nothing to publish) or {"id", "outcome"}; TargetError when it cannot be published exactly."""
    td = params.get("tracker_decision")
    if td is None:
        return None
    if not isinstance(td, dict) or set(td) != {"id", "outcome"} or not isinstance(td["id"], str) \
            or not TRACKER_ID.match(td["id"]) or not isinstance(td["outcome"], str) \
            or not TRACKER_OUTCOME.match(td["outcome"]):
        raise TargetError("tracker_decision_malformed: need {id: D-…, outcome: <token>}")
    return td


# ───────────────────────────────────────── publication ─────────────────────────────────────────

def run_ky(argv, env):
    """Run the tracker CLI once. → ("exited", rc, text) | ("not_started", None, why) | ("unknown", None, why).
    "unknown" (killed, timed out) is NOT a failure: whether the tracker recorded the decision is not known."""
    child = {k: env.environ[k] for k in KY_ENV_NAMES if k in env.environ}
    child.update(KY_ROOT=str(env.root), KY_RUN=str(env.run), KY_FLEET=str(env.fleet))
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=env.ky_timeout, env=child,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return "unknown", None, "no exit status within %gs" % env.ky_timeout
    except OSError as e:
        return "not_started", None, "ky could not be started: %s" % type(e).__name__
    if r.returncode < 0:
        return "unknown", None, "terminated by signal %d" % -r.returncode
    return "exited", r.returncode, kyaction.flat(r.stderr or r.stdout, 300)


def _no_tracker_readback(record):
    return "unknown", "no tracker readback is available to this handler"


# ───────────────────────────────────────── the handler ─────────────────────────────────────────

class Handler:
    def __init__(self, env, now, now_source, authorised, holder, holder_kind, publish_observer, log):
        self.env, self.now, self.now_iso, self.now_source = env, now, kyaction.utc(now), now_source
        self.authorised, self.holder, self.publish_observer = authorised, holder, publish_observer
        self.actor = {"role": "veto", "holder_kind": holder_kind, "controller_id": holder}
        self.applier = {"holder_kind": holder_kind, "controller_id": holder}
        self.log_path = env.run / "DECISIONS_SURROGATE.jsonl"
        self.log = log or (lambda text: print("kyveto: %s" % text, file=sys.stderr))
        self.commands = []

    # ---- small readers
    def holds(self):
        out = []
        if os.path.lexists(self.env.root / "HOLD"):
            out.append("HOLD")
        if os.path.lexists(self.env.run / "STOP_veto"):
            out.append("STOP_veto")
        pause = kycommands.pause_state(self.env.run)
        if pause["state"] == "unknown":
            out.append("command_queue_unreadable")
        elif pause["state"] == "paused":
            out.append("owner_paused")
        elif pause["pending_pause"]:
            out.append("owner_pause_pending")
        return out

    def commands_about(self, name, key, value):
        return [e for e in kycommands.scan(self.env.run)[0]
                if not e["invalid"] and e["doc"]["command"] == name and e["doc"]["state"] in ("QUEUED", "APPLIED")
                and e["doc"]["args"].get(key) == value]

    def veto_command(self, did):
        found = self.commands_about("veto", "decision_id", did)
        return found[0] if found else None

    def published(self, did):
        record = kyaction.peek(self.env.run, did + ".publish")
        return record is not None and record["state"] == "DONE"

    # ---- writers
    def append(self, latest, state, reason, effective_at=None, detail=None):
        line = {k: latest[k] for k in BASE_FIELDS if k in latest}
        line.setdefault("effective_at", None)
        if effective_at is not None:
            line["effective_at"] = effective_at
        line.update(state=state, by=HANDLER, reason=reason, at=kyaction.utc(), session=self.holder)
        if detail:
            line["detail"] = detail
        append_line(self.log_path, line)
        return line

    def failed(self, did, latest, reason, effective_at=None):
        published = self.published(did)
        self.append(latest, "FAILED", reason, effective_at, {"published": True} if published else None)
        out = {"outcome": "failed", "reason": reason}
        if published:                        # the tracker holds a decision that was then not carried out
            out.update(attention=True, published=True)
        return out

    def settle(self, entry, result=None, reject=None):
        """Mark an owner command applied (or rejected) as the fenced owner of the veto role; never twice."""
        if entry["doc"]["state"] != "QUEUED":
            return

        def handler(command):
            if reject:
                raise kycommands.Reject(reject)
            return result

        status, doc = kycommands.apply(self.env.run, entry["doc"]["id"], self.applier, handler, in_order=False,
                                       log=self.log)
        note = {"id": entry["doc"]["id"], "command": entry["doc"].get("command"), "status": status}
        if status in ("refused", "unreconciled"):
            note.update(reason=doc.get("reason"), attention=True)
        elif status == "rejected":
            note["reason"] = (doc.get("result") or {}).get("reason")
        self.commands.append(note)

    # ---- one decision, under its lock
    def guarded(self, did):
        lock = kyaction.acquire_lock(self.env.run, "decision." + did, self.holder, log=self.log)
        if lock is None:
            return {"id": did, "outcome": "locked"}
        try:
            out = self.process(did)
        except (kyaction.ActionError, kycommands.CommandError, OSError) as e:
            out = {"outcome": "blocked", "reason": "error: %s: %s" % (type(e).__name__, kyaction.flat(e, 160)),
                   "attention": True}
        finally:
            kyaction.release_lock(lock)
        return dict(out, id=did)

    def process(self, did):
        history, problems, unusable = load_decisions(self.log_path)       # the fresh handled-state check
        if problems or did in unusable:
            return {"outcome": "blocked", "reason": "decision_log_unreadable", "attention": True}
        lines = history.get(did) or []
        if not is_candidate(lines):
            return {"outcome": "not_pending", "state": _state(lines[-1]) if lines else None}
        awaiting, aw_lock = lines[-1].get("awaiting"), None
        if isinstance(awaiting, str) and AW_RE.match(awaiting):
            aw_lock = kyaction.acquire_lock(self.env.run, "awaiting." + awaiting, self.holder, log=self.log)
            if aw_lock is None:
                return {"outcome": "locked", "reason": "awaiting_item_locked"}
        try:
            return self.decide(did, lines, history)
        finally:
            if aw_lock is not None:
                kyaction.release_lock(aw_lock)

    def decide(self, did, lines, history):
        latest = lines[-1]
        mine = _by_handler_effective(lines)                   # set: published by this handler, not yet finished
        effective_at = mine.get("effective_at") if mine else None
        finished = [_state(line) for line in lines[:-1] if _state(line) in TERMINAL]
        if finished:                                          # a later line never resurrects a finished decision
            self.append(latest, finished[0], "terminal_state_is_final", effective_at)
            return {"outcome": finished[0].lower(), "reason": "terminal_state_is_final"}
        veto = self.veto_command(did)
        if veto:                                              # (a) the owner's veto wins, also at and after expiry
            return self.vetoed(did, latest, veto, effective_at)
        if mine is None:
            deadline = kyaction.parse_utc(latest.get("veto_deadline"))
            if deadline is None:
                return self.failed(did, latest, "veto_deadline_unreadable")
            if self.now < deadline:                           # (b)
                return {"outcome": "pending", "seconds_remaining": int(math.ceil(deadline - self.now)),
                        "veto_deadline": latest["veto_deadline"]}
            notification = latest.get("notification")         # (c)
            if not isinstance(notification, dict) or notification.get("submitted") is not True:
                return self.failed(did, latest, "notification_not_submitted")
            notified = kyaction.parse_utc(notification.get("ts"))
            if notified is None:
                return self.failed(did, latest, "notification_ts_unreadable")
            if deadline - notified < VETO_WINDOW_S:
                return self.failed(did, latest, "veto_window_too_short")
        held = self.holds()                                   # (d)
        if held:
            return {"outcome": "held", "reasons": held}
        ctx = Ctx(self.env, did, latest.get("authority") if isinstance(latest.get("authority"), dict) else None,
                  self.now_iso)
        started = kyaction.peek(self.env.run, did + ".execute") is not None
        if not (mine is not None and started):                # (e) — once execution has begun the disk is ours
            reason = self.recheck(did, lines, history, ctx)
            if reason:
                return self.failed(did, latest, reason, effective_at)
        try:
            cls, params = bind(latest.get("target"))
            td = tracker_decision(params)
        except TargetError as e:
            return {"outcome": "blocked", "reason": "execution_unreconciled: %s" % e.reason, "attention": True}
        veto = self.veto_command(did)                         # a last look before anything is published
        if veto:
            return self.vetoed(did, latest, veto, effective_at)
        if td is not None:                                    # (f) publish …
            out = self.publish(did, latest, td, effective_at)
            if out:
                return out
        if mine is None:
            effective_at = self.now_iso
            latest = self.append(latest, "EFFECTIVE", "veto_window_expired_unvetoed", effective_at,
                                 {"publication": did + ".publish" if td is not None else None,
                                  "now_source": self.now_source})
        veto = self.veto_command(did)                         # a last look before anything is executed
        if veto:
            return self.vetoed(did, latest, veto, effective_at)
        out = self.execute(did, latest, cls, params, ctx, effective_at)     # … then execute
        if out:
            return out
        self.append(latest, "EXECUTED", "executed", effective_at, {"action": did + ".execute"})
        return {"outcome": "executed"}

    def vetoed(self, did, latest, veto, effective_at):
        run, action_id, command_id = self.env.run, did + ".execute", veto["doc"]["id"]
        record = kyaction.peek(run, action_id)
        if record is not None and record["state"] == "INTENDED":
            try:
                cls, params = bind(latest.get("target"))
            except TargetError:
                return {"outcome": "blocked", "reason": "execution_unreconciled", "attention": True}
            ctx = Ctx(self.env, did, latest.get("authority") if isinstance(latest.get("authority"), dict) else None,
                      self.now_iso)
            outcome, record = kyaction.reconcile(run, action_id, lambda r: cls.observer(params, ctx), by=self.holder)
            if outcome == "unknown":
                return {"outcome": "blocked", "reason": "execution_unreconciled", "attention": True}
            if outcome == "not_done":
                record = kyaction.fail(run, action_id, {"reason": "vetoed_before_execution", "command": command_id})
        if record is not None and record["state"] == "DONE":  # the effect is already in place: the veto is too late
            self.append(latest, "EXECUTED", "executed", effective_at, {"action": action_id,
                                                                       "veto_too_late": command_id})
            self.settle(veto, reject="too_late: decision %s was already executed" % did)
            return {"outcome": "executed", "reason": "veto_too_late", "attention": True}
        published = self.published(did)
        self.append(latest, "VETOED", "owner_veto", effective_at, {"command": command_id, "published": published})
        self.settle(veto, result={"decision": did, "outcome": "VETOED"})
        out = {"outcome": "vetoed", "command": command_id}
        if published:                        # the tracker decision is already out and now contradicts the owner
            out.update(attention=True, published=True)
        return out

    def recheck(self, did, lines, history, ctx):
        """None when the decision may be published and executed now, else the named reason it is FAILED."""
        latest = lines[-1]
        if latest.get("class") == "hard_stop":
            return "hard_stop_never_delegated"
        if latest.get("class") not in CLASSES:
            return "class_invalid"
        for field in ("target", "authority", "class", "awaiting"):
            if any(kyaction.canonical(line.get(field)) != kyaction.canonical(latest.get(field)) for line in lines):
                return "decision_record_mutated: %s" % field
        if len({kyaction.canonical(line.get("veto_deadline")) for line in lines
                if line.get("veto_deadline") is not None}) > 1:
            return "decision_record_mutated: veto_deadline"
        authority = latest.get("authority")
        if not isinstance(authority, dict) or _bundle(authority.get("source_commit"),
                                                      authority.get("entrypoints_digest")) is None:
            return "authority_unbound"
        if self.authorised is None:
            return "authority_unknown"
        if _bundle(authority["source_commit"], authority["entrypoints_digest"]) != self.authorised:
            return "authority_changed"
        try:
            cls, params = bind(latest.get("target"))
            td = tracker_decision(params)
            recorded = latest["target"].get("fingerprint")
            if not isinstance(recorded, str) or not HEX64.match(recorded):
                return "target_unbound"
            if fingerprint(latest["target"], self.env, ctx) != recorded:
                return "target_changed"
        except TargetError as e:
            return e.reason
        awaiting = latest.get("awaiting")
        if not isinstance(awaiting, str) or not AW_RE.match(awaiting):
            return "awaiting_unbound"
        if not (self.env.run / "awaiting" / (awaiting + ".json")).is_file():
            return "awaiting_not_open"
        decided = self.commands_about("decide", "awaiting_id", awaiting)
        if decided:
            return "superseded_by_owner_decide: %s" % decided[0]["doc"]["id"]
        for other, theirs in sorted(history.items()):
            if other != did and any(line.get("awaiting") == awaiting and _state(line) in ("EFFECTIVE", "EXECUTED")
                                    for line in theirs):
                return "awaiting_already_decided: %s" % other
        if cls.merge_action and os.path.lexists(self.env.run / "HOLD_MERGES"):
            return "class_hold: HOLD_MERGES"
        if td is not None and not (self.env.ky_bin.is_file() and os.access(self.env.ky_bin, os.X_OK)):
            return "publication_unavailable: no executable ky at %s" % self.env.ky_bin
        return cls.precheck(params, ctx)

    def publish(self, did, latest, td, effective_at):
        run, action_id = self.env.run, did + ".publish"
        argv = ["decide", td["id"], "--outcome", td["outcome"], "--as", "steward", "--delegated", "--detail",
                "%s: %s" % (did, kyaction.flat(latest.get("decision"), 400))]
        status, record = kyaction.begin(
            run, action_id, "tracker_decision_publish", self.actor, {"decision_id": did, "argv": argv},
            {"tracker_decision": td["id"], "outcome": td["outcome"]},
            "tracker decision %s: open → %s (steward, delegated) for %s" % (td["id"], td["outcome"], did))
        if status == "unfinished":           # a restart inside the publication: observe, never repeat blind
            status, record = kyaction.reconcile(run, action_id, self.publish_observer or _no_tracker_readback,
                                                by=self.holder)
            if status == "unknown":
                return {"outcome": "blocked", "reason": "publication_unreconciled", "attention": True}
        if status == "done":
            return None
        if status == "failed":
            earlier = record.get("result") or {}
            return self.failed(did, latest, "publication_failed: %s" % (
                "rc=%d" % earlier["exit_status"] if isinstance(earlier.get("exit_status"), int)
                else kyaction.flat(earlier.get("error"), 120)), effective_at)
        kind, rc, text = run_ky([str(self.env.ky_bin)] + argv, self.env)     # "new" or "not_done"
        if kind == "exited" and rc == 0:
            kyaction.complete(run, action_id, {"exit_status": 0, "output": text})
            return None
        if kind == "exited":
            kyaction.fail(run, action_id, {"exit_status": rc, "output": text})
            return self.failed(did, latest, "publication_failed: rc=%d" % rc, effective_at)
        if kind == "not_started":
            kyaction.fail(run, action_id, {"exit_status": None, "error": text})
            return self.failed(did, latest, "publication_failed: %s" % text, effective_at)
        self.log("%s: `ky decide` gave no exit status (%s); the publication stays unreconciled" % (did, text))
        return {"outcome": "blocked", "reason": "publication_unreconciled", "attention": True}

    def execute(self, did, latest, cls, params, ctx, effective_at):
        run, action_id = self.env.run, did + ".execute"
        status, record = kyaction.begin(
            run, action_id, "veto_decision_execute:" + cls.kind, self.actor,
            {"decision_id": did, "class": latest.get("class"), "authority": latest.get("authority")},
            latest.get("target"), cls.describe(params))
        if status == "unfinished":           # a restart between begin and execution: reconcile first
            status, record = kyaction.reconcile(run, action_id, lambda r: cls.observer(params, ctx), by=self.holder)
            if status == "unknown":
                return {"outcome": "blocked", "reason": "execution_unreconciled", "attention": True}
        if status == "done":
            return None
        if status == "failed":
            return self.failed(did, latest, "execution_failed: %s" % kyaction.flat(
                (record.get("result") or {}).get("reason"), 160), effective_at)
        try:                                 # "new" or "not_done"
            ok, result = cls.execute(params, ctx)
        except Exception as e:
            ok, result = False, {"reason": "executor_error: %s" % type(e).__name__}
        if not ok:
            kyaction.fail(run, action_id, result)
            return self.failed(did, latest, "execution_failed: %s" % kyaction.flat(result.get("reason"), 160),
                               effective_at)
        kyaction.complete(run, action_id, result)
        return None

    # ---- owner commands addressed to the veto role that no pending decision consumed
    def sweep(self):
        history, problems, unusable = load_decisions(self.log_path)
        if problems:
            return
        for entry in kycommands.scan(self.env.run)[0]:
            doc = entry["doc"]
            if doc["role"] != "veto" or doc["state"] != "QUEUED":
                continue
            if entry["invalid"]:
                self.settle(entry)           # kycommands settles it as REJECTED invalid_command
            elif doc["command"] != "veto":
                self.settle(entry, reject="unsupported_by_veto_handler: %s" % doc["command"])
            else:
                did = doc["args"]["decision_id"]
                lines = history.get(did)
                state = _state(lines[-1]) if lines else None
                if not lines:
                    self.settle(entry, reject="unknown_decision")
                elif did in unusable or is_candidate(lines) or state == "PROPOSED":
                    continue                 # settled under the decision lock / not yet in its window: stays queued
                elif state in ("VETOED", "FAILED"):
                    self.settle(entry, result={"decision": did, "outcome": state,
                                               "note": "the decision was already %s" % state})
                else:
                    self.settle(entry, reject="too_late: decision %s is %s" % (did, state))

    def run(self, report):
        history, problems, unusable = load_decisions(self.log_path)
        pause = kycommands.pause_state(self.env.run)
        report["problems"] = problems + sorted(unusable.values()) + ["command queue: %s" % p for p in pause["problems"]]
        report["holds"] = self.holds()
        if not problems:                     # an unattributable line: no decision's state is known → no transition
            for did in sorted(d for d, lines in history.items() if d not in unusable and is_candidate(lines)):
                report["decisions"].append(self.guarded(did))
            try:
                self.sweep()
            except (kyaction.ActionError, kycommands.CommandError, OSError) as e:
                report["problems"].append("command sweep: %s: %s" % (type(e).__name__, kyaction.flat(e, 160)))
        report["commands"] = self.commands
        report["attention"] = bool(report["problems"]) or any(
            x.get("attention") for x in report["decisions"] + report["commands"])


def _now(now):
    if now is None:
        return time.time(), "clock"
    parsed = kyaction.parse_utc(now)
    if parsed is None:
        raise ValueError("--now must be a UTC ISO-8601 timestamp (…Z)")
    return parsed, "argument"


def tick(env=None, now=None, authorised=None, holder=None, holder_kind="controller", publish_observer=None,
         log=None):
    """One pass. `authorised` = {"source_commit", "entrypoints_digest"} or None (then PLANNER_STATE.json is read).
    `holder` must own $KY_RUN/locks/veto; without one the tick fences itself for its own duration. → the report."""
    env = env or Env()
    moment, now_source = _now(now)
    if not env.run.is_dir():
        raise RunMissing(str(env.run))
    if authorised is None:
        authorised, source = resolve_authority(env)
    else:
        authorised, source = resolve_authority(env, authorised.get("source_commit"),
                                               authorised.get("entrypoints_digest"))
    report = {"schema": "ky.veto_tick/1", "now": kyaction.utc(moment), "holder": holder,
              "authority": dict(authorised or {}, source=source), "holds": [], "decisions": [], "commands": [],
              "problems": [], "attention": False}
    own = None
    if holder is None:
        holder = "kyveto-%s-%d" % (kyaction.utc(fmt="%Y%m%dT%H%M%SZ"), os.getpid())
        own = kyaction.acquire_lock(env.run, "veto", holder, log=log)
        if own is None:
            return dict(report, skipped="veto_role_lock_held")
        report["holder"] = holder
    else:
        held, why = kycommands.holds_role_lock(env.run, "veto", holder)
        if not held:
            raise NotHolder(why)
    try:
        Handler(env, moment, now_source, authorised, holder, holder_kind, publish_observer, log).run(report)
    finally:
        if own is not None:
            kyaction.release_lock(own)
    return report


def status(env=None, now=None, authorised=None):
    """Read-only: every decision's state (§13: a surrogate decision IS its state, not a journal line)."""
    env = env or Env()
    moment, _ = _now(now)
    if authorised is None:
        authorised, source = resolve_authority(env)
    else:
        authorised, source = resolve_authority(env, authorised.get("source_commit"),
                                               authorised.get("entrypoints_digest"))
    history, problems, unusable = load_decisions(env.run / "DECISIONS_SURROGATE.jsonl")
    pause = kycommands.pause_state(env.run)
    reader = Handler(env, moment, "status", authorised, "status", "controller", None, None)
    vetoes = {}
    for entry in kycommands.scan(env.run)[0]:
        doc = entry["doc"]
        if not entry["invalid"] and doc["command"] == "veto" and doc["state"] in ("QUEUED", "APPLIED"):
            vetoes.setdefault(doc["args"]["decision_id"], doc["id"])
    decisions = []
    for did, lines in sorted(history.items()):
        latest = lines[-1]
        target, notification = latest.get("target"), latest.get("notification")
        row = {"id": did, "class": latest.get("class"), "state": _state(latest), "by": latest.get("by"),
               "awaiting": latest.get("awaiting"), "kind": target.get("kind") if isinstance(target, dict) else None,
               "veto_deadline": latest.get("veto_deadline"), "effective_at": latest.get("effective_at"),
               "notification_submitted": isinstance(notification, dict) and notification.get("submitted") is True,
               "veto_command": vetoes.get(did), "reason": latest.get("reason")}
        deadline = kyaction.parse_utc(latest.get("veto_deadline"))
        if row["state"] == "PENDING_VETO" and deadline is not None:
            row["seconds_remaining"] = max(0, int(math.ceil(deadline - moment)))
        if latest.get("class") == "veto" and any(_state(line) in ("EFFECTIVE", "EXECUTED")
                                                 and line.get("by") != HANDLER for line in lines):
            row["anomaly"] = "veto_class_made_effective_outside_the_handler"
        decisions.append(row)
    actions, action_problems = kyaction.scan(env.run)
    all_problems = problems + sorted(unusable.values()) + ["command queue: %s" % p for p in pause["problems"]] \
        + ["action record: %s" % p for p in action_problems]
    return {"schema": "ky.veto_status/1", "now": kyaction.utc(moment),
            "authority": dict(authorised or {}, source=source), "holds": reader.holds(),
            "pause": {k: pause[k] for k in ("state", "applied_pause", "pending_pause")}, "decisions": decisions,
            "unfinished_actions": sorted(a["action_id"] for a in actions if a["state"] == "INTENDED"),
            "problems": all_problems,
            "attention": bool(all_problems) or any("anomaly" in row for row in decisions)}


# ───────────────────────────────────────── CLI ─────────────────────────────────────────

USAGE = ("usage: kyveto.py tick [--now ISO] [--authorised-commit C --entrypoints-digest D] [--as HOLDER_ID]\n"
         "                      [--holder-kind controller|supervisor]\n"
         "       kyveto.py status [--now ISO] [--authorised-commit C --entrypoints-digest D]\n"
         "       kyveto.py fingerprint --target FILE")


def _options(argv, allowed):
    out = {}
    while argv:
        if argv[0] not in allowed or len(argv) < 2 or argv[0] in out:
            return None
        out[argv[0]] = argv[1]
        argv = argv[2:]
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    env = Env()
    common = ("--now", "--authorised-commit", "--entrypoints-digest")
    if argv and argv[0] in ("tick", "status"):
        opts = _options(argv[1:], common + (("--as", "--holder-kind") if argv[0] == "tick" else ()))
        if opts is None or opts.get("--holder-kind", "controller") not in ("controller", "supervisor") \
                or ("--as" in opts and not opts["--as"]):
            print(USAGE, file=sys.stderr)
            return 64
        try:
            _now(opts.get("--now"))
            authorised = None
            if "--authorised-commit" in opts or "--entrypoints-digest" in opts:
                authorised, _ = resolve_authority(env, opts.get("--authorised-commit"),
                                                  opts.get("--entrypoints-digest"))
        except ValueError as e:
            print("kyveto: %s\n%s" % (e, USAGE), file=sys.stderr)
            return 64
        if not env.run.is_dir():
            print("kyveto: run directory missing: %s" % env.run, file=sys.stderr)
            return 66
        try:
            if argv[0] == "status":
                report = status(env, opts.get("--now"), authorised)
            else:
                report = tick(env, opts.get("--now"), authorised, opts.get("--as"),
                              opts.get("--holder-kind", "controller"))
        except NotHolder as e:
            print("kyveto: REFUSED %s" % e, file=sys.stderr)
            return 75
        print(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True))
        return 3 if report.get("attention") else 0
    if argv and argv[0] == "fingerprint":
        opts = _options(argv[1:], ("--target",))
        if not opts or "--target" not in opts:
            print(USAGE, file=sys.stderr)
            return 64
        target, err = kyaction.read_json(opts["--target"])
        if err:
            print("kyveto: target file %s" % err, file=sys.stderr)
            return 1
        try:
            print(fingerprint(target, env))
        except TargetError as e:
            print("kyveto: REFUSED %s" % e.reason, file=sys.stderr)
            return 1
        return 0
    print(USAGE, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main())
