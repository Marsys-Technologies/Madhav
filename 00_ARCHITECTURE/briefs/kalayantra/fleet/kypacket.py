#!/usr/bin/env python3
"""kypacket.py — admission check of one KĀLA-YANTRA v3 work-order packet.

Relaunch plan v2.7 §8 (packets are "admitted by `kypacket.py check`"), §7 (an oversized packet is rejected at
admission, not at launch), §14 B-1; packet KV3-B-KYPACKET. Read-only, one packet per call, standard library only.
Every decision here is script logic: no model, no network, nothing written.

Usage:
  kypacket.py check <PACKET.md> --repo <absolute repository root>
Exit: 0 admitted · 1 refused · 64 usage · 66 an own input is missing, unreadable or invalid (the repository; git;
      schemas/packet.json, templates/ku_bindings.json and kyschema.py, all read beside this script)
      70 an internal error. Non-zero is never admission.
stdout (exit 0 and 1 only): one JSON object
  {"schema":"ky.packet_check/1","packet":<absolute path>,"id","admitted":<bool>,"packet_sha256":<computed>,
   "size":{"method":"calibrated_byte_bound","bytes","bound":9000,"tokens":null},"labels":[],"reasons":[{"code","detail"}]}
stderr: `refused: <code>: <detail>`, one line per reason.
Environment: KY_GIT (default /usr/bin/git); git only reads (rev-parse, cat-file).

The nine checks. All of them run and every failure is reported; `admitted` is true only when none gave a reason.
A check whose input an earlier check refused (no front matter, no verified source) gives no pass of its own: the
earlier reason already refuses the packet.
  1 format          the name is PACKET_<ID>_v<n>.md and the path is one regular file (not a link); UTF-8; the first
                    line is exactly ```json; the text up to the next line of exactly ``` is one strict JSON object
                                                                           → not_single_file, front_matter_json
  2 schema          kyschema.validate against schemas/packet.json; `id` equals the name's <ID>
                                                                           → schema, name_id_mismatch
  3 packet_sha256   sha256 of the file's bytes with the 64 hex digits of that field's value replaced by 64 zeros
                    (as the B-1 packets are stamped); the field must be the only "packet_sha256" member written in
                    the front matter                                       → packet_sha256 (detail: the computed value)
  4 pins            each spec_sources[].path is a file under the repository hashing to its sha256; where revision
                    is a 40-hex commit, the blob <revision>:<path> exists with that sha256; original_failing_base
                    is a commit; a non-null schema_receipt_id is the schema_receipt_id of a
                    00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v*.json
                      → spec_source_missing, spec_source_sha256, spec_source_revision, commit_unknown,
                        schema_receipt_unresolved
  5 size            file bytes ≤ 9000                                      → oversize
  6 tests           feature: every test_commits[] blob <sha>:<path> exists with sha256 `digest`;
                    bootstrap: acceptance.command names (as one shell word, or as the file of a pytest node id) at
                    least one path listed in d1_paths                      → test_unavailable
  7 excerpts        every fenced block whose info string starts with `excerpt` has content that occurs byte for
                    byte in a spec_sources file whose pin (4, sha256) held; at least one such block
                                                                           → excerpt_not_in_source, no_excerpt
  8 reconciliation  every line starting `Reconciliation:` names, as one backtick span, a spec_sources[].path. This
                    shows the claim is bound to a pinned source, not that it is true.
                                                                           → reconciliation_unpinned
  9 KU bindings     the packet's labels are the REGISTRY labels whose path is in d1_paths; for each clause of
                    ku_bindings.json naming one of them in required_in the packet's bytes contain the clause text
                                                                           → ku_clause_missing (detail: the KU id)
ku_bindings.json itself is an own input: a clause whose text does not hash to its text_sha256, or a required_in
label that is not a REGISTRY key, is exit 66.

The size bound is a calibrated byte bound and is reported as one: 4,000 tokens ÷ 0.444 tokens per byte, the highest
ratio measured with the real program (cards/TOKEN_MEASUREMENT.json) being 0.418. Nothing here measures tokens, so
`size.tokens` is null.

Two hashes exist and both are kept (ruling P19): the front matter's follows check 3; a launch input's packet_sha256
is the plain sha256 of the file and is compared by kyboot.py, not here.
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
KU_BINDINGS_SCHEMA = "ky.ku_bindings/1"

# 4,000 tokens ÷ 0.444 tokens per byte (plan §7/§8: a packet is ≤ 4 k tokens)
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
    "oversize",
    "test_unavailable",
    "excerpt_not_in_source", "no_excerpt",
    "reconciliation_unpinned",
    "ku_clause_missing",
)

FENCE = "```"
FRONT_OPEN = "```json"
EXCERPT_INFO = "excerpt"
RECONCILIATION = "Reconciliation:"
GIT_TIMEOUT_S = 60
# the environment's own repository selection must not replace --repo
GIT_ENV_DROPPED = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR",
                   "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_CEILING_DIRECTORIES")

_NAME = re.compile(r"PACKET_(?P<id>[A-Za-z0-9][A-Za-z0-9._-]{0,63})_v(?P<n>[1-9][0-9]*)\.md\Z")
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SHA_FIELD = re.compile(rb'"packet_sha256"\s*:\s*"([0-9a-f]{64})"')
_SHA_MEMBER = re.compile(rb'"packet_sha256"\s*:')
_BACKTICKS = re.compile(r"`([^`]+)`")


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


def _load_bindings(kyschema, here: Path) -> dict:
    """KU id → (text bytes, required_in labels); every clause hashes to its text_sha256, every label is registered"""
    path = here / "templates" / "ku_bindings.json"
    bindings = _load_own_json(kyschema, path)

    def bad(detail):
        return OwnInputError(f"{path} is invalid: {detail}")

    if not isinstance(bindings, dict) or bindings.get("schema") != KU_BINDINGS_SCHEMA:
        raise bad(f"schema is not {KU_BINDINGS_SCHEMA}")
    clauses = bindings.get("clauses")
    if not isinstance(clauses, dict) or not clauses:
        raise bad("clauses is not a non-empty object")
    out = {}
    for ku, clause in clauses.items():
        if not isinstance(clause, dict):
            raise bad(f"{ku}: not an object")
        text, required_in = clause.get("text"), clause.get("required_in")
        if not isinstance(text, str) or not text:
            raise bad(f"{ku}: text is not a non-empty string")
        try:
            data = text.encode("utf-8")
        except UnicodeEncodeError:
            raise bad(f"{ku}: text is not UTF-8") from None
        if clause.get("text_sha256") != sha256_hex(data):
            raise bad(f"{ku}: sha256(text) {sha256_hex(data)} is not text_sha256 {clause.get('text_sha256')!r}")
        if not isinstance(required_in, list) or not required_in \
                or not all(isinstance(label, str) for label in required_in):
            raise bad(f"{ku}: required_in is not a non-empty list of labels")
        for label in required_in:
            if label not in REGISTRY:
                raise bad(f"{ku}: required_in label {label!r} is not a REGISTRY key")
        out[ku] = (data, tuple(required_in))
    return out


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
        """the bytes of the regular file `path` under the repository root, or None"""
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
    def __init__(self, packet: str, git: Git, kyschema, schema, bindings):
        self.path = os.path.abspath(packet)
        self.git, self.kyschema, self.schema, self.bindings = git, kyschema, schema, bindings
        self.reasons: list = []
        self.raw = None          # the file's bytes
        self.lines = None        # its lines, when it is UTF-8
        self.front = None        # the front matter object
        self.front_span = None   # (start, end) of the front matter text in raw
        self.body_at = None      # index in lines of the first body line
        self.name_id = None
        self.computed = None
        self.labels: list = []
        self.sources: dict = {}  # spec_sources path → bytes, for the sources whose sha256 pin held

    def refuse(self, code: str, detail):
        assert code in REASON_CODES, code
        self.reasons.append({"code": code, "detail": _one_line(detail)})

    def field(self, name, kind):
        """a front matter member of the expected type, else None (the schema check names the fault)"""
        value = self.front.get(name) if isinstance(self.front, dict) else None
        return value if isinstance(value, kind) and not isinstance(value, bool) else None

    def run(self) -> dict:
        self.format()
        if self.front is not None:
            self.schema_and_id()
            self.packet_sha256()
            self.pins()
        self.size()
        if self.front is not None:
            self.test_availability()
            self.excerpts()
            self.reconciliation()
            self.ku_bindings()
        declared = self.field("id", str)
        return {"schema": SCHEMA, "packet": self.path, "id": declared if declared is not None else self.name_id,
                "admitted": not self.reasons, "packet_sha256": self.computed,
                "size": {"method": "calibrated_byte_bound", "bytes": None if self.raw is None else len(self.raw),
                         "bound": BYTE_BOUND, "tokens": None},
                "labels": self.labels, "reasons": self.reasons}

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
        self.front, self.body_at = front, close + 1
        self.front_span = (start, start + len(front_text.encode("utf-8")))

    # 2
    def schema_and_id(self):
        for finding in self.kyschema.validate(self.schema, self.front):
            self.refuse("schema", finding)
        declared = self.front.get("id")
        if self.name_id is not None and isinstance(declared, str) and declared != self.name_id:
            self.refuse("name_id_mismatch", f"id {declared} is not the name's {self.name_id}")

    # 3
    def packet_sha256(self):
        start, end = self.front_span
        front_bytes = self.raw[start:end]
        fields = list(_SHA_FIELD.finditer(front_bytes))
        declared = self.front.get("packet_sha256")
        if len(fields) != 1 or len(_SHA_MEMBER.findall(front_bytes)) != 1 \
                or not isinstance(declared, str) or fields[0].group(1).decode("ascii") != declared:
            self.refuse("packet_sha256", "not computable: the front matter does not write exactly one "
                                         "packet_sha256 member holding 64 hex digits")
            return
        at = start + fields[0].start(1)
        self.computed = sha256_hex(self.raw[:at] + b"0" * 64 + self.raw[at + 64:])
        if self.computed != declared:
            self.refuse("packet_sha256", f"computed {self.computed}, the front matter says {declared}")

    # 4
    def pins(self):
        for source in self.field("spec_sources", list) or []:
            if not isinstance(source, dict):
                continue
            path, pinned, revision = source.get("path"), source.get("sha256"), source.get("revision")
            if not isinstance(path, str) or not isinstance(pinned, str):
                continue
            data = self.git.working_file(path)
            if data is None:
                self.refuse("spec_source_missing", f"{path}: no such file under {self.git.root}")
            elif sha256_hex(data) != pinned:
                self.refuse("spec_source_sha256", f"{path}: the file is {sha256_hex(data)}, the pin is {pinned}")
            else:
                self.sources[path] = data
            if isinstance(revision, str) and _HEX40.match(revision):
                blob = self.git.blob(revision, path)
                if blob is None:
                    self.refuse("spec_source_revision", f"{path}: no blob {revision}:{path}")
                elif sha256_hex(blob) != pinned:
                    self.refuse("spec_source_revision",
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
    def size(self):
        if self.raw is not None and len(self.raw) > BYTE_BOUND:
            self.refuse("oversize", f"{len(self.raw)} bytes, the bound is {BYTE_BOUND}")

    # 6
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
                commit, digest, path = entry["sha"], entry["digest"], entry["path"]
                blob = self.git.blob(commit, path) if _HEX40.match(commit) else None
                if blob is None:
                    self.refuse("test_unavailable", f"{path}: no blob {commit}:{path}")
                elif sha256_hex(blob) != digest:
                    self.refuse("test_unavailable",
                                f"{path}: the blob at {commit} is {sha256_hex(blob)}, the digest is {digest}")
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

    # 7
    def excerpts(self):
        found = 0
        opened = None        # (info string, 1-based line of the opening fence) while inside a fenced block
        content: list = []
        for number, line in enumerate(self.lines[self.body_at:], start=self.body_at + 1):
            if opened is None:
                if line.startswith(FENCE):
                    opened, content = (line[len(FENCE):], number), []
                continue
            if line != FENCE:
                content.append(line)
                continue
            info, at = opened
            opened = None
            if info.startswith(EXCERPT_INFO):
                found += 1
                self.excerpt(info, at, "\n".join(content).encode("utf-8"))
        if opened is not None and opened[0].startswith(EXCERPT_INFO):
            found += 1
            self.refuse("excerpt_not_in_source", f"line {opened[1]} ({opened[0]}): the block is never closed")
        if not found:
            self.refuse("no_excerpt", "no fenced block whose info string starts with 'excerpt'")

    def excerpt(self, info: str, at: int, content: bytes):
        if not content.strip():
            self.refuse("excerpt_not_in_source", f"line {at} ({info}): the block is empty")
        elif not any(content in data for data in self.sources.values()):
            self.refuse("excerpt_not_in_source",
                        f"line {at} ({info}): not byte for byte in any spec_sources file whose pin held")

    # 8
    def reconciliation(self):
        paths = {s.get("path") for s in self.field("spec_sources", list) or [] if isinstance(s, dict)}
        for number, line in enumerate(self.lines, start=1):
            if line.startswith(RECONCILIATION) and not paths.intersection(_BACKTICKS.findall(line)):
                self.refuse("reconciliation_unpinned", f"line {number} names no spec_sources path in backticks")

    # 9
    def ku_bindings(self):
        owned = [p for p in self.field("d1_paths", list) or [] if isinstance(p, str)]
        self.labels = sorted(label for label, path in REGISTRY.items()
                             if any(p.startswith(path) if path.endswith("/") else p == path for p in owned))
        for ku in sorted(self.bindings):
            text, required_in = self.bindings[ku]
            if set(required_in).intersection(self.labels) and text not in self.raw:
                self.refuse("ku_clause_missing", ku)


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
        check = Check(packet, Git(repo), kyschema, _load_schema(kyschema, HERE), _load_bindings(kyschema, HERE))
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
    return EXIT_ADMITTED if report["admitted"] else EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
