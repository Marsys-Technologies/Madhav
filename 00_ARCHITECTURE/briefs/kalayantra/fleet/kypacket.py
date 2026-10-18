#!/usr/bin/env python3
"""kypacket.py — admission check of one KĀLA-YANTRA v3 work-order packet.

Relaunch plan v2.7 §8 (packets are "admitted by `kypacket.py check`"), §14 B-1; packet KV3-B-KYPACKET; Amendment A8
(2026-10-17): a pin is satisfied by the blob at its pinned revision, and by nothing else — the working tree is not
consulted. Read-only, one packet per call, standard library only. Every decision here is script logic: no model, no
network, nothing written.

Usage:
  kypacket.py check <PACKET.md> --repo <absolute repository root>
Exit: 0 admitted · 1 refused · 64 usage · 66 an own input is missing, unreadable or invalid (the repository; git;
      schemas/packet.json and kyschema.py, both read beside this script) · 70 an internal error. Non-zero is never
      admission.
stdout (exit 0 and 1 only): one JSON object
  {"schema":"ky.packet_check/1","packet":<absolute path>,"id","admitted":<bool>,"packet_sha256":<sha256 of the file>,
   "size":{"method":"calibrated_byte_bound","bytes","bound":9000,"tokens":null},"labels":[],
   "reasons":[{"code","detail"}],"warnings":[{"code","detail"}]}
stderr: `refused: <code>: <detail>`, one line per reason, then `warning: <code>: <detail>`, one line per warning.
Environment: KY_GIT (default /usr/bin/git); git only reads (rev-parse, cat-file).

The five checks. All of them run and every failure is reported; `admitted` is true only when none gave a reason. A
warning is reported beside the reasons and refuses nothing. A check whose input an earlier check refused (no front
matter) gives no pass of its own: the earlier reason already refuses the packet.
  1 format          the name is PACKET_<ID>_v<n>.md and the path is one regular file (not a link); UTF-8; the first
                    line is exactly ```json; the text up to the next line of exactly ``` is one strict JSON object
                                                                           → not_single_file, front_matter_json
  2 schema          kyschema.validate against schemas/packet.json; `id` equals the name's <ID>
                                                                           → schema, name_id_mismatch
  3 one member      the front matter writes exactly one "packet_sha256" member, holding the 64 hex digits the parsed
                    field holds. Its value is not recomputed here (A8): the launch input's packet_sha256 is the
                    plain sha256 of the file and is compared by kyboot.py   → packet_sha256
  4 pins            each spec_sources[] whose `revision` is a 40-hex commit: the commit exists, the blob
                    <revision>:<path> exists, and its sha256 is the pinned one. A `revision` that is not a commit
                    (a document version such as "v2.7") pins nothing the repository can answer for: the warning
                    `spec_source_unpinned`, not a refusal. original_failing_base is a commit; a non-null
                    schema_receipt_id is the schema_receipt_id of a 00_ARCHITECTURE/control/kalayantra/
                    SCHEMA_RECEIPT_v*.json (read from the repository root, where the receipts live)
                      → spec_source_revision (no such commit), spec_source_missing (no such blob at it),
                        spec_source_sha256 (another blob), commit_unknown, schema_receipt_unresolved
  5 tests           feature: every test_commits[] blob <sha>:<path> exists (its `digest` is carried for the launch
                    input, not pinned here); bootstrap: acceptance.command names (as one shell word, or as the file
                    of a pytest node id) at least one path listed in d1_paths  → test_unavailable
  size (a warning)  file bytes > 9000 → `oversize`; the packet is admitted all the same.

`labels` are the REGISTRY labels whose path is in d1_paths — what the packet owns, for the reader; nothing is bound to
them here.

Gone with A8 (each refused what the pinned source already answers for, or what the builder re-reads anyway): the
working-tree hash of a spec source, the front matter's self-hash, the byte-for-byte excerpt check, the "every
Reconciliation line names a pinned path" check, the KU clause text check (templates/ku_bindings.json is no own
input), the size refusal and the test_commits digest pin.

The size bound is a calibrated byte bound and is reported as one: 4,000 tokens ÷ 0.444 tokens per byte, the highest
ratio measured with the real program (cards/TOKEN_MEASUREMENT.json) being 0.418. Nothing here measures tokens, so
`size.tokens` is null.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

SCHEMA = "ky.packet_check/1"
USAGE = "usage: kypacket.py check <PACKET.md> --repo <absolute repository root>"
EXIT_ADMITTED, EXIT_REFUSED, EXIT_USAGE, EXIT_OWN_INPUT, EXIT_INTERNAL = 0, 1, 64, 66, 70

HERE = Path(__file__).resolve().parent
F = "00_ARCHITECTURE/briefs/kalayantra/fleet"
T = "platform/scripts/governance/pravaha_tracker"
RECEIPT_DIR = "00_ARCHITECTURE/control/kalayantra"
RECEIPT_GLOB = "SCHEMA_RECEIPT_v*.json"

# 4,000 tokens ÷ 0.444 tokens per byte (plan §7/§8: a packet is ≤ 4 k tokens); since A8 a bound to warn about
BYTE_BOUND = 9000

# component label → the path that carries it; a value ending in "/" is carried by every path under it
REGISTRY = {
    "kyverdicts": f"{F}/kyverdicts.py",
    "kylock": f"{F}/kylock.sh",
    "kyversion": f"{F}/kyversion.sh",
    "local-db": f"{F}/local_db.sh",
    "preflight-v3": f"{F}/preflight.sh",
    "finalize-v3": f"{F}/finalize.sh",
    "dispatcher-ready-receipts": f"{F}/kyd_admit.py",
    "kyloop-crash-cleanup": f"{F}/kyloop.py",   # B-0c part 2; ruling P21
    "tracker-semantics": f"{T}/",
}

REASON_CODES = (
    "not_single_file", "front_matter_json",
    "schema", "name_id_mismatch",
    "packet_sha256",
    "spec_source_missing", "spec_source_sha256", "spec_source_revision", "commit_unknown",
    "schema_receipt_unresolved",
    "test_unavailable",
)
WARNING_CODES = ("spec_source_unpinned", "oversize")

FENCE = "```"
FRONT_OPEN = "```json"
GIT_TIMEOUT_S = 60
# the environment's own repository selection must not replace --repo
GIT_ENV_DROPPED = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR",
                   "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_CEILING_DIRECTORIES")

_NAME = re.compile(r"PACKET_(?P<id>[A-Za-z0-9][A-Za-z0-9._-]{0,63})_v(?P<n>[1-9][0-9]*)\.md\Z")
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_SHA_FIELD = re.compile(rb'"packet_sha256"\s*:\s*"([0-9a-f]{64})"')
_SHA_MEMBER = re.compile(rb'"packet_sha256"\s*:')


class OwnInputError(Exception):
    """an own input is missing, unreadable or invalid: exit 66, never a verdict on the packet"""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _one_line(text) -> str:
    return " ".join(str(text).split())


# --------------------------------------------------------------------------------------------------------------
# own inputs
# --------------------------------------------------------------------------------------------------------------
def _load_kyschema(here: Path):
    path = here / "kyschema.py"
    try:
        spec = importlib.util.spec_from_file_location("kyschema", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.load_json_text, module.validate  # noqa: B018 — both must exist
    except Exception as bad:  # a module that cannot be imported, whatever the cause, is an invalid own input
        raise OwnInputError(f"cannot import {path}: {_one_line(bad) or type(bad).__name__}") from None
    return module


def _load_own_json(kyschema, path: Path):
    try:
        return kyschema.load_json_text(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError) as unreadable:
        raise OwnInputError(f"cannot read {path}: {_one_line(unreadable)}") from None
    except (ValueError, RecursionError) as bad:
        raise OwnInputError(f"{path} is not strict JSON: {_one_line(bad)}") from None


def _load_schema(kyschema, here: Path):
    path = here / "schemas" / "packet.json"
    schema = _load_own_json(kyschema, path)
    try:
        kyschema.validate(schema, {})   # lints the schema; what it says of {} is not used
    except (ValueError, TypeError, RecursionError) as bad:
        raise OwnInputError(f"{path} is refused by kyschema: {_one_line(bad)}") from None
    return schema


class Git:
    """read-only git on one repository root"""

    def __init__(self, repo: str, environ=None):
        environ = os.environ if environ is None else environ
        self.program = environ.get("KY_GIT") or "/usr/bin/git"
        self.env = {k: v for k, v in environ.items() if k not in GIT_ENV_DROPPED}
        self.env["GIT_OPTIONAL_LOCKS"] = "0"
        if not os.path.isabs(repo):
            raise OwnInputError(f"--repo is not an absolute path: {repo}")
        if not os.path.isdir(repo):
            raise OwnInputError(f"--repo is not a directory: {repo}")
        self.root = os.path.realpath(repo)
        code, out = self.run("rev-parse", "--show-toplevel")
        top = out.decode("utf-8", "replace").rstrip("\n")
        if code != 0 or not top or os.path.realpath(top) != self.root:
            raise OwnInputError(f"--repo is not a git repository root: {repo}")

    def run(self, *args):
        try:
            done = subprocess.run([self.program, "--no-replace-objects", "-C", self.root, *args], env=self.env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  timeout=GIT_TIMEOUT_S)
        except (OSError, subprocess.TimeoutExpired) as failed:
            raise OwnInputError(f"cannot run git ({self.program}): {_one_line(failed)}") from None
        return done.returncode, done.stdout

    def blob(self, commit: str, path: str):
        """the bytes of <commit>:<path>, or None when no such blob exists"""
        code, out = self.run("cat-file", "blob", f"{commit}:{path}")
        return out if code == 0 else None

    def is_commit(self, name: str) -> bool:
        return self.run("cat-file", "-e", f"{name}^{{commit}}")[0] == 0

    def working_file(self, path: str):
        """the bytes of the regular file `path` under the repository root, or None (the receipts are read so)"""
        if not path or os.path.isabs(path) or "\\" in path or any(p in ("", ".", "..") for p in path.split("/")):
            return None
        full = os.path.realpath(os.path.join(self.root, path))
        if os.path.commonpath([self.root, full]) != self.root or not os.path.isfile(full):
            return None
        try:
            return Path(full).read_bytes()
        except OSError:
            return None


# --------------------------------------------------------------------------------------------------------------
# the packet
# --------------------------------------------------------------------------------------------------------------
class Check:
    def __init__(self, packet: str, git: Git, kyschema, schema):
        self.path = os.path.abspath(packet)
        self.git, self.kyschema, self.schema = git, kyschema, schema
        self.reasons: list = []
        self.warnings: list = []
        self.raw = None          # the file's bytes
        self.lines = None        # its lines, when it is UTF-8
        self.front = None        # the front matter object
        self.front_span = None   # (start, end) of the front matter text in raw
        self.name_id = None
        self.labels: list = []

    def refuse(self, code: str, detail):
        assert code in REASON_CODES, code
        self.reasons.append({"code": code, "detail": _one_line(detail)})

    def warn(self, code: str, detail):
        assert code in WARNING_CODES, code
        self.warnings.append({"code": code, "detail": _one_line(detail)})

    def field(self, name, kind):
        """a front matter member of the expected type, else None (the schema check names the fault)"""
        value = self.front.get(name) if isinstance(self.front, dict) else None
        return value if isinstance(value, kind) and not isinstance(value, bool) else None

    def run(self) -> dict:
        self.format()
        if self.front is not None:
            self.schema_and_id()
            self.one_member()
            self.pins()
            self.test_availability()
            self.labelled()
        self.size()
        declared = self.field("id", str)
        return {"schema": SCHEMA, "packet": self.path, "id": declared if declared is not None else self.name_id,
                "admitted": not self.reasons, "packet_sha256": None if self.raw is None else sha256_hex(self.raw),
                "size": {"method": "calibrated_byte_bound", "bytes": None if self.raw is None else len(self.raw),
                         "bound": BYTE_BOUND, "tokens": None},
                "labels": self.labels, "reasons": self.reasons, "warnings": self.warnings}

    # 1
    def format(self):
        name = os.path.basename(self.path)
        match = _NAME.match(name)
        if match:
            self.name_id = match.group("id")
        else:
            self.refuse("not_single_file", f"the name is not PACKET_<ID>_v<n>.md: {name}")
        if os.path.islink(self.path) or not os.path.isfile(self.path):
            self.refuse("not_single_file", f"not one regular file: {self.path}")
            return
        try:
            self.raw = Path(self.path).read_bytes()
        except OSError as unreadable:
            self.refuse("not_single_file", f"unreadable: {unreadable}")
            return
        try:
            text = self.raw.decode("utf-8")
        except UnicodeDecodeError as bad:
            self.refuse("front_matter_json", f"the file is not UTF-8: {bad}")
            return
        self.lines = text.split("\n")
        if self.lines[0] != FRONT_OPEN:
            self.refuse("front_matter_json", f"the first line is not exactly {FRONT_OPEN}")
            return
        try:
            close = self.lines.index(FENCE, 1)
        except ValueError:
            self.refuse("front_matter_json", f"no line of exactly {FENCE} closes the front matter")
            return
        front_text = "\n".join(self.lines[1:close])
        try:
            front = self.kyschema.load_json_text(front_text)
        except (ValueError, RecursionError) as bad:
            self.refuse("front_matter_json", f"the front matter is not strict JSON: {bad}")
            return
        if not isinstance(front, dict):
            self.refuse("front_matter_json", "the front matter is not one JSON object")
            return
        start = len((FRONT_OPEN + "\n").encode("utf-8"))
        self.front = front
        self.front_span = (start, start + len(front_text.encode("utf-8")))

    # 2
    def schema_and_id(self):
        for finding in self.kyschema.validate(self.schema, self.front):
            self.refuse("schema", finding)
        declared = self.front.get("id")
        if self.name_id is not None and isinstance(declared, str) and declared != self.name_id:
            self.refuse("name_id_mismatch", f"id {declared} is not the name's {self.name_id}")

    # 3
    def one_member(self):
        start, end = self.front_span
        front_bytes = self.raw[start:end]
        fields = list(_SHA_FIELD.finditer(front_bytes))
        declared = self.front.get("packet_sha256")
        if len(fields) != 1 or len(_SHA_MEMBER.findall(front_bytes)) != 1 \
                or not isinstance(declared, str) or fields[0].group(1).decode("ascii") != declared:
            self.refuse("packet_sha256", "the front matter does not write exactly one packet_sha256 member "
                                         "holding 64 hex digits")

    # 4
    def pins(self):
        for source in self.field("spec_sources", list) or []:
            if not isinstance(source, dict):
                continue
            path, pinned, revision = source.get("path"), source.get("sha256"), source.get("revision")
            if not isinstance(path, str) or not isinstance(pinned, str):
                continue
            if not isinstance(revision, str) or not _HEX40.match(revision):
                self.warn("spec_source_unpinned", f"{path}: revision {revision!r} is not a commit; the pin {pinned} "
                                                  f"is not checked against the repository")
                continue
            if not self.git.is_commit(revision):
                self.refuse("spec_source_revision", f"{path}: {revision} is not a commit in {self.git.root}")
                continue
            blob = self.git.blob(revision, path)
            if blob is None:
                self.refuse("spec_source_missing", f"{path}: no blob {revision}:{path}")
            elif sha256_hex(blob) != pinned:
                self.refuse("spec_source_sha256",
                            f"{path}: the blob at {revision} is {sha256_hex(blob)}, the pin is {pinned}")
        base = self.field("original_failing_base", str)
        if base is not None and not (_HEX40.match(base) and self.git.is_commit(base)):
            self.refuse("commit_unknown", f"original_failing_base {base} is not a commit in {self.git.root}")
        receipt = self.field("schema_receipt_id", str)
        if receipt is not None and not self.receipt_resolves(receipt):
            self.refuse("schema_receipt_unresolved",
                        f"{receipt} is the schema_receipt_id of no {RECEIPT_DIR}/{RECEIPT_GLOB}")

    def receipt_resolves(self, receipt: str) -> bool:
        folder = Path(self.git.root) / RECEIPT_DIR
        for candidate in sorted(folder.glob(RECEIPT_GLOB)):
            data = self.git.working_file(f"{RECEIPT_DIR}/{candidate.name}")
            if data is None:
                continue
            try:
                document = self.kyschema.load_json_text(data.decode("utf-8"))
            except (ValueError, RecursionError):
                continue
            if isinstance(document, dict) and document.get("schema_receipt_id") == receipt:
                return True
        return False

    # 5
    def test_availability(self):
        kind = self.front.get("kind")
        if kind == "feature":
            commits = self.field("test_commits", list)
            if not commits:
                self.refuse("test_unavailable", "a feature packet names no test_commits")
                return
            for entry in commits:
                if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) for k in ("sha", "digest",
                                                                                                    "path")):
                    self.refuse("test_unavailable", f"malformed test_commits entry: {json.dumps(entry)}")
                    continue
                commit, path = entry["sha"], entry["path"]
                blob = self.git.blob(commit, path) if _HEX40.match(commit) else None
                if blob is None:
                    self.refuse("test_unavailable", f"{path}: no blob {commit}:{path}")
        elif kind == "bootstrap":
            acceptance = self.field("acceptance", dict) or {}
            command = acceptance.get("command")
            owned = {p for p in self.field("d1_paths", list) or [] if isinstance(p, str)}
            if not isinstance(command, str) or not owned:
                self.refuse("test_unavailable", "a bootstrap packet names no acceptance.command or no d1_paths")
                return
            try:
                words = shlex.split(command)
            except ValueError:
                words = command.split()
            if not any(word.split("::", 1)[0] in owned for word in words):
                self.refuse("test_unavailable", "acceptance.command names no path listed in d1_paths")

    # labels (reported, not bound)
    def labelled(self):
        owned = [p for p in self.field("d1_paths", list) or [] if isinstance(p, str)]
        self.labels = sorted(label for label, path in REGISTRY.items()
                             if any(p.startswith(path) if path.endswith("/") else p == path for p in owned))

    # size (a warning since A8)
    def size(self):
        if self.raw is not None and len(self.raw) > BYTE_BOUND:
            self.warn("oversize", f"{len(self.raw)} bytes, the calibrated bound is {BYTE_BOUND}")


# --------------------------------------------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------------------------------------------
def parse(argv):
    """(packet, repo), or None when the command line is not the contract's"""
    if len(argv) != 4 or argv[0] != "check":
        return None
    rest = argv[1:]
    if rest.count("--repo") != 1 or rest.index("--repo") == 2:
        return None
    at = rest.index("--repo")
    repo = rest.pop(at + 1)
    rest.pop(at)
    packet = rest[0]
    if packet.startswith("--") or repo.startswith("--"):
        return None
    return packet, repo


def main(argv=None) -> int:
    parsed = parse(list(sys.argv[1:] if argv is None else argv))
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return EXIT_USAGE
    packet, repo = parsed
    try:
        kyschema = _load_kyschema(HERE)
        check = Check(packet, Git(repo), kyschema, _load_schema(kyschema, HERE))
        report = check.run()
    except OwnInputError as bad:
        print(f"kypacket: {_one_line(bad)}", file=sys.stderr)
        return EXIT_OWN_INPUT
    except Exception as crashed:  # no verdict was reached; never let a traceback's exit 1 read as a refusal
        print(f"kypacket: internal error: {type(crashed).__name__}: {_one_line(crashed)}", file=sys.stderr)
        return EXIT_INTERNAL
    print(json.dumps(report, ensure_ascii=False))
    for reason in report["reasons"]:
        print(f"refused: {reason['code']}: {reason['detail']}", file=sys.stderr)
    for warning in report["warnings"]:
        print(f"warning: {warning['code']}: {warning['detail']}", file=sys.stderr)
    return EXIT_ADMITTED if report["admitted"] else EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
