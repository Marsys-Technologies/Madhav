#!/usr/bin/env python3
"""Validator and append-only writer for 00_ARCHITECTURE/control/asset_dispositions.jsonl (Suvarna E6.3, N-97 item 5).

WHAT THIS IS. `asset_elevation_tracker.elevated_assets(ref, repo)` reads the disposition ledger at a git ref and counts a
terminally dispositioned asset (retire or consolidate, with a decision id and a visible reason) as ELEVATED. That reader
defines the file's contract and has no writer by design. This module is the schema's one validator and the one sanctioned
writer, and it DEFINES NOTHING THE READER ALREADY DEFINES: it loads the reader by path and reuses its constants and its
own parser (`_e63_parse_dispositions`), so "this module says the file is valid" implies "the reader accepts it" (same ref's
registry). The closed disposition vocabulary, the terminal set, the decision-id grammar, the chain rule and the
timestamp rule all live in the reader; `--schema` prints them.

NOTE FOR THE TRACK A LANES (A.L0r ... A.L5) -- HOW TO APPEND. One row per asset per decision, from your brief, through
this tool only; never edit the file by hand and never rewrite, delete or reorder a line (the hash chain and the git
check below reject it). From the repo root, on your lane branch:

    python3 platform/scripts/governance/asset_dispositions.py --append \\
        --asset <registry asset id> --disposition <one of the reader's vocabulary> \\
        --evidence <repo-relative path of your brief>#<section anchor> \\
        --reason "<one visible sentence>" [--decision-id N-<n>] [--addition <id> ...]
    python3 platform/scripts/governance/asset_dispositions.py --check --base origin/main

`--evidence` is required on every row and the file it names must exist when you add the row. Leave `--decision-id` off
for a PROPOSED disposition: a row without a decision id reads `unresolved` to the reader until Strategic Suvarna's
accepting PR (J1) appends the row that carries the decision id. A retire or consolidate is terminal only with a decision
id AND a reason. The LATEST row per asset governs; `additions` are the union over all of an asset's rows. A row that
ends a terminal disposition must cite a different decision id, and an exact repeat of the latest row is refused.
Run `--check --base origin/main` before pushing: it also proves you only appended to what main already has.
With no `--base`, `--check` compares against the merge-base with origin/main when that ref exists; otherwise it falls
back to HEAD and SAYS the prefix check is vacuous (HEAD already holds what you committed). The OK line prints the real
status of the git rule: "prefix rule checked against <sha>", "no ledger at base: prefix rule not applicable" or
"NOT CHECKED: <why>" (a path outside the repo toplevel, not the canonical ledger path, ...). NOT CHECKED exits 1 when
you passed --base yourself or are checking the canonical path. There is no CI caller yet (the workflow files are shared
and not touched here): wire `--check --base origin/main` into a lane's CI when one is added.

THE FILE. Line 1 is the header {"asset": "_schema", "_doc": ...}; then one JSON object per line with `seq` 1..N and
`prev_sha256` (sha256 of the previous line's bytes, newline excluded; the header line's for seq 1), plus asset,
disposition, reason, decision_id, decided_on (timezone-aware ISO-8601), additions (a list, may be empty) and evidence.
Keys outside that set are refused. `evidence` is this module's one addition to the reader's field list (the reader
ignores it): a repo-relative path with an optional #anchor.

CHECKS. Reader-owned (reported as `reader: ...`): JSON strictness, header, chain, asset id syntax and registry
membership, vocabulary, decision-id and decided_on shape, additions. This module adds: header and row key sets, evidence,
no-op duplicate rows, no silent end of a terminal disposition, and (with --base, default HEAD) the git append-only
rule: the committed bytes must be an exact byte-prefix of the file. The registry snapshot is read OFFLINE from the
committed seed (and LEVEL_MAP.json when present) and asset_census.py at --ref (default HEAD) through the reader's own
loaders; if it cannot be read the validator fails closed and says so. --ref is a COMMITTED SNAPSHOT: an asset removed
from the registry at HEAD but present at an older --ref passes here while the reader at HEAD rejects it, so keep --ref at
the commit the reader will be run against.

TORN TAIL. A process killed mid-append (SIGKILL, power loss) can leave a partial last line; --check then reports it as
not strict JSON. Remove ONLY that partial line, never a complete one: truncate the file back to its last newline, e.g.
python3 -c "p='<path>'; b=open(p,'rb').read(); open(p,'wb').write(b[:b.rfind(b'\\n')+1])", then run --check and re-run
your --append.

CLI (exit 0 ok, 1 problems found or an append refused, 2 usage / I/O error):
    asset_dispositions.py --check [path] [--repo R] [--ref HEAD] [--base REF | --no-base]
    asset_dispositions.py --append --asset A --disposition D --evidence P [...] [path]
    asset_dispositions.py --init [path]       (create the header-only file; refuses to overwrite)
    asset_dispositions.py --schema
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
READER_PATH = REPO / "00_ARCHITECTURE/control/asset_elevation_tracker.py"

# The ONLY definitions made here: the key sets of the file, the evidence grammar, and the header text.
HEADER_KEYS = frozenset({"asset", "_doc"})
ROW_FIELDS = ("asset", "disposition", "reason", "decision_id", "decided_on", "additions", "evidence")
CHAIN_KEYS = ("seq", "prev_sha256")
ALLOWED_ROW_KEYS = frozenset(ROW_FIELDS + CHAIN_KEYS)
APPEND_REQUIRED = ("asset", "disposition", "evidence")
_EVIDENCE = re.compile(r"[^\s#]+(#[^\s#]+)?")

_READER = None


class DispositionError(ValueError):
    """An append (or init) was refused; `problems` lists why. Nothing was written."""

    def __init__(self, message, problems=()):
        super().__init__(message + ("".join(f"\n  - {p}" for p in problems)))
        self.problems = list(problems)


def load_reader():
    """The reader module (asset_elevation_tracker.py), loaded by path once. `E6_3_TRACKER_UNDER_TEST` overrides the path
    (the same hook the E6.3 test fixtures honour), honoured ONLY under pytest (PYTEST_CURRENT_TEST set); a production
    run ignores it, so the validator can never be pointed at a different reader. The reader never imports this module."""
    global _READER
    if _READER is None:
        override = os.environ.get("E6_3_TRACKER_UNDER_TEST") if os.environ.get("PYTEST_CURRENT_TEST") else None
        path = Path(override or READER_PATH)
        name = "asset_elevation_tracker_for_dispositions"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        _READER = mod
    return _READER


def schema(reader=None) -> dict:
    """The schema as data: everything the reader owns comes from the reader's constants, nothing is restated."""
    T = reader or load_reader()
    return {
        "path": T.E63_DISPOSITIONS_PATH,
        "header": {"asset": "_schema", "keys": sorted(HEADER_KEYS)},
        "row_fields": list(ROW_FIELDS),
        "chain_keys": list(CHAIN_KEYS),
        "row_keys_closed_set": sorted(ALLOWED_ROW_KEYS),
        "dispositions": sorted(T.E63_DISPOSITIONS),
        "terminal_dispositions": sorted(T.E63_TERMINAL_DISPOSITIONS),
        "decision_id_pattern": T._E63_DECISION.pattern,
        "asset_pattern": T._E63_ASSET.pattern,
        "evidence_pattern": _EVIDENCE.pattern + " (path: repo-relative, no leading slash, no .., no backslash)",
        "chain": "seq is 1..N over the rows after the header; prev_sha256 is the sha256 of the previous line's bytes "
                 "without the newline (the header line's for seq 1)",
        "semantics": "latest row per asset governs; additions are the union over all rows; a null decision_id reads "
                     "unresolved; terminal = retire/consolidate with a decision id and a visible reason",
    }


SCHEMA = schema()


def header_line(reader=None) -> str:
    T = reader or load_reader()
    doc = (
        "Disposition ledger (E6.3, tier-4 section 0). Append-only and hash-chained like asset_certs.jsonl: line 1 is this "
        "_schema row; every later line is one JSON object with seq (1..N), prev_sha256 (sha256 of the previous line's "
        "bytes, newline excluded; this line's for seq 1), asset, disposition (" + ", ".join(sorted(T.E63_DISPOSITIONS)) +
        "), reason (text or null; a terminal disposition needs a visible reason), decision_id (N-<n>... or null: null "
        "reads unresolved), decided_on (timezone-aware ISO-8601), additions (list, required, may be empty) and evidence "
        "(repo-relative path[#anchor] of the Track A brief or sheet that grounds the row). The LATEST row per asset "
        "governs; additions are the union over all rows; " + "/".join(sorted(T.E63_TERMINAL_DISPOSITIONS)) +
        " is terminal only with a decision id and a reason. Written only through "
        "platform/scripts/governance/asset_dispositions.py (--append) in a strategist-approved PR; never edited, deleted "
        "or reordered. Validate with: python3 platform/scripts/governance/asset_dispositions.py --check --base origin/main."
    )
    return json.dumps({"asset": "_schema", "_doc": doc}, ensure_ascii=True, allow_nan=False)


# ---- reading --------------------------------------------------------------------------------------------------
def _read_source(source):
    """-> (bytes, path or None). A PathLike or a one-line str is a path; bytes are content; a str with a newline or a
    list/tuple of lines is text."""
    if isinstance(source, (bytes, bytearray)):
        return bytes(source), None
    if isinstance(source, (list, tuple)):
        return ("".join(str(x).rstrip("\r\n") + "\n" for x in source)).encode("utf-8"), None
    if isinstance(source, str) and "\n" in source:
        return source.encode("utf-8"), None
    return Path(source).read_bytes(), Path(source)


def _toplevel(T, repo):
    try:
        return T._e63_git(repo, ["rev-parse", "--show-toplevel"], "toplevel").decode("utf-8").strip() or str(repo)
    except T.ElevatedInputError:
        return str(repo)


def _locate(path, T, repo):
    """(path relative to the repo toplevel or None, why the git base check cannot apply or None). The directory is
    resolved (so a symlinked directory that leaves the repo is seen); the file itself is judged separately (a symlink)."""
    root = os.path.realpath(_toplevel(T, repo))
    absp = os.path.abspath(str(path))
    rel = os.path.relpath(os.path.join(os.path.realpath(os.path.dirname(absp)), os.path.basename(absp)), root)
    if rel == ".." or rel.startswith(".." + os.sep):
        return None, "the path resolves outside the repository toplevel"
    if rel != T.E63_DISPOSITIONS_PATH:
        return rel, f"{rel} is not the canonical ledger path {T.E63_DISPOSITIONS_PATH}"
    return rel, None


def default_base(T, repo):
    """(ref, note): the merge-base of HEAD with origin/main when that ref exists, else HEAD with an explicit vacuous note."""
    try:
        sha = T._e63_git(repo, ["merge-base", "HEAD", "origin/main"], "merge-base").decode("ascii", "replace").strip()
        if sha:
            return sha, f"merge-base of HEAD and origin/main ({sha[:12]})"
    except T.ElevatedInputError:
        pass
    return "HEAD", "HEAD: no origin/main here, so the prefix check is VACUOUS for committed content (pass --base <ref>)"


def _record_count(data: bytes) -> int:
    return max(0, sum(1 for ln in data.split(b"\n") if ln.strip()) - 1)


def _first_diff_line(a: bytes, b: bytes) -> int:
    la, lb = a.split(b"\n"), b.split(b"\n")
    for i, (x, y) in enumerate(zip(la, lb), 1):
        if x != y:
            return i
    return min(len(la), len(lb))


def _in(v, vocab):
    """Membership that never raises on an unhashable value (a list/dict `disposition`)."""
    return isinstance(v, str) and v in vocab


def _evidence_problem(ev, T):
    if not isinstance(ev, str) or not ev.strip():
        return "evidence is required: a repo-relative path[#anchor] of the brief that grounds this row"
    if ev != ev.strip() or not _EVIDENCE.fullmatch(ev) or not T._e63_relpath_ok(ev.split("#", 1)[0]):
        return f"evidence {ev!r} is not a repo-relative path[#anchor] (no leading slash, no .., no backslash, no spaces)"
    return None


def _evidence_file_problem(T, root, ev):
    """For a NEW row: the evidence file must exist as a regular file reached through no symlink, and be tracked or staged."""
    rel = ev.split("#", 1)[0]
    real_root = os.path.realpath(root)
    target = os.path.join(real_root, rel)
    if not os.path.lexists(target):
        return f"evidence file {rel!r} does not exist in the working tree"
    if os.path.realpath(target) != target or os.path.islink(target):
        return f"evidence file {rel!r} is, or is reached through, a symlink"
    if not os.path.isfile(target):
        return f"evidence {rel!r} is not a regular file"
    try:
        listed = T._e63_git(real_root, ["--literal-pathspecs", "ls-files", "--", rel], "ls-files")
    except T.ElevatedInputError as e:
        return f"evidence file {rel!r}: cannot ask git whether it is tracked ({e.message})"
    if not listed.strip():
        return f"evidence file {rel!r} is neither tracked nor staged in git (git add it with the row)"
    return None


def _sig(r):
    adds = r.get("additions")
    return json.dumps([r.get("disposition"), r.get("reason"), r.get("decision_id"),
                       sorted(adds) if isinstance(adds, list) and all(isinstance(x, str) for x in adds) else adds,
                       r.get("evidence")], sort_keys=True, default=str)


def _visible(T, reason):
    return bool(T._e63_visible_reason(reason)) if isinstance(reason, str) else False


def _is_terminal(T, r):
    """The reader's definition of a TERMINAL row: retire/consolidate with a decision id AND a visible reason."""
    return _in(r.get("disposition"), T.E63_TERMINAL_DISPOSITIONS) and r.get("decision_id") is not None and _visible(T, r.get("reason"))


# ---- validation -----------------------------------------------------------------------------------------------
def _validate(source, *, repo=None, ref="HEAD", base=None, rel_path=None, new_from_seq=None, require_base=True, reader=None):
    """-> (problems, base_status). base_status is the REAL state of the git rule: "not requested", "prefix rule checked
    against <sha>", "no ledger at base <sha>: prefix rule not applicable" or "NOT CHECKED: <why>"."""
    T = reader or load_reader()
    repo = str(repo or REPO)
    data, _path = _read_source(source)
    problems = []
    base_status, unchecked, already_reported = "not requested", None, False

    # (a) the ledger must be a regular file (a symlink could be rewritten behind git's back)
    if _path is not None and os.path.islink(_path):
        problems.append(f"{_path} is a symlink: the ledger must be a regular file inside the repository")

    # (b) git append-only: the committed bytes are a prefix of the file
    if base is not None:
        if rel_path is not None or _path is None:
            rel = rel_path or T.E63_DISPOSITIONS_PATH
        else:
            rel, unchecked = _locate(_path, T, repo)
        if unchecked is None:
            try:
                bsha = T._e63_resolve_ref(base, repo)
                bdata = T._e63_show(repo, bsha, rel) if T._e63_exists(repo, bsha, rel) else None
            except T.ElevatedInputError as e:
                problems.append(f"base {base!r}: {e.message}")
                unchecked, already_reported, bdata = f"base {base!r} cannot be read", True, None
            else:
                if bdata is None:
                    base_status = f"no ledger at base {bsha[:12]}: prefix rule not applicable"
                    if new_from_seq is None:
                        new_from_seq = 1
                else:
                    base_status = f"prefix rule checked against {bsha[:12]}"
                    ok = data.startswith(bdata) and (len(data) == len(bdata) or bdata.endswith(b"\n") or data[len(bdata):][:1] == b"\n")
                    if not ok:
                        problems.append(f"history rewritten: {rel} at {base} is not a byte-prefix of this file (first differing "
                                        f"line {_first_diff_line(bdata, data)}); the ledger is append-only")
                    if new_from_seq is None:
                        new_from_seq = _record_count(bdata) + 1
        if unchecked is not None:
            base_status = f"NOT CHECKED: {unchecked}"
            if require_base and not already_reported:
                problems.append(f"base {base!r}: NOT CHECKED: {unchecked}")

    # (c) parse (the reader's strict loader; a torn or non-object line stops everything)
    try:
        rows = T._e63_lines(data, T.E63_DISPOSITIONS_PATH)
    except T.ElevatedInputError as e:
        return problems + [f"reader: {e.message}"], base_status

    # (d) this module's own rules
    hdr = rows[0][2]
    extra = sorted(set(hdr) - HEADER_KEYS)
    if extra:
        problems.append(f"line {rows[0][0]}: unknown header key(s) {extra} (allowed: {sorted(HEADER_KEYS)})")
    if not T._e63_nonblank(hdr.get("_doc")):
        problems.append(f"line {rows[0][0]}: the header needs a non-blank `_doc`")
    root = _toplevel(T, repo)
    for n, raw, _r in rows:
        if len(raw.decode("utf-8").splitlines()) != 1:
            problems.append(f"line {n}: contains a raw line-separator character (U+2028, U+0085, ...) that splits it for "
                            "line-oriented readers; rows are written with escaped non-ASCII")
    latest, seen_chain = {}, set()
    prev, nrec = T._e63_sha(rows[0][1]), 0
    chain_broken = False
    for n, raw, r in rows[1:]:
        k = nrec + 1
        where = f"line {n}"
        try:
            unknown = sorted(set(r) - ALLOWED_ROW_KEYS)
            if unknown:
                problems.append(f"{where}: unknown key(s) {unknown} (closed set: {sorted(ALLOWED_ROW_KEYS)})")
            ev = _evidence_problem(r.get("evidence"), T)
            if ev:
                problems.append(f"{where}: {ev}")
            elif new_from_seq is not None and k >= new_from_seq:
                fp = _evidence_file_problem(T, root, r["evidence"])
                if fp:
                    problems.append(f"{where}: {fp}")
            disp_, dec, asset = r.get("disposition"), r.get("decision_id"), r.get("asset")
            if _in(disp_, T.E63_TERMINAL_DISPOSITIONS) and not _visible(T, r.get("reason")):
                problems.append(f"{where}: a {disp_} row needs a visible reason (text with at least one letter or digit)")
            if isinstance(asset, str):
                before = latest.get(asset)
                if before is not None:
                    bn, br = before
                    if _sig(r) == _sig(br):
                        problems.append(f"{where}: duplicate of line {bn} for {asset}: the latest row already says exactly this")
                    elif _is_terminal(T, br):
                        bd = br.get("disposition")
                        if not _is_terminal(T, r):
                            if _in(disp_, T.E63_TERMINAL_DISPOSITIONS):
                                problems.append(f"{where}: would silently drop {asset}'s terminal {bd} ({br.get('decision_id')}, "
                                                f"line {bn}): a {disp_} row is terminal only with a decision_id AND a visible reason")
                            elif dec is None or dec == br.get("decision_id"):
                                problems.append(f"{where}: ends {asset}'s terminal {bd} ({br.get('decision_id')}, line {bn}) "
                                                "without citing a different decision_id")
                        elif disp_ != bd and dec == br.get("decision_id"):
                            problems.append(f"{where}: changes {asset}'s terminal kind {bd} -> {disp_} under the same decision "
                                            f"{dec} (line {bn}); a change of terminal kind needs a new decision_id")
                latest[asset] = (n, r)
        except Exception as e:                   # noqa: BLE001 - a malformed row must be a problem, never a traceback
            problems.append(f"{where}: could not be analysed ({type(e).__name__}: {e})")
        try:                                     # the reader's own chain rule, so a break reads the same on both sides
            if not chain_broken:
                T._e63_chain_check(r, f"{T.E63_DISPOSITIONS_PATH} line {n}", nrec, prev)
        except T.ElevatedInputError as e:
            problems.append(f"reader: {e.message}")
            seen_chain.add(e.message)
            chain_broken = True
        prev, nrec = T._e63_sha(raw), nrec + 1

    # (e) the reader's own parser, against the offline registry snapshot
    try:
        sha = T._e63_resolve_ref(ref, repo)
        facts = T._e63_registry_facts(repo, sha)
        registry = T._e63_registry_assets(repo, sha)
    except T.ElevatedInputError as e:
        problems.append(f"registry: the committed registry snapshot at {ref!r} cannot be read ({e.message}); asset ids were "
                        "checked for syntax only")
        for n, _raw, r in rows[1:]:
            if not (isinstance(r.get("asset"), str) and T._E63_ASSET.fullmatch(r["asset"])):
                problems.append(f"line {n}: bad asset {r.get('asset')!r}")
    else:
        try:
            T._e63_parse_dispositions(data, facts, registry)
        except T.ElevatedInputError as e:
            if e.message not in seen_chain:
                problems.append(f"reader: {e.message}")
        except Exception as e:                   # noqa: BLE001 - the reader itself crashing on a malformed field type
            problems.append(f"reader: crashed on a malformed row ({type(e).__name__}: {e}); the reader at this commit would "
                            "not accept the file")
    return problems, base_status


def validate(source, *, repo=None, ref="HEAD", base=None, rel_path=None, new_from_seq=None, require_base=True, reader=None) -> list:
    """The problems found in a disposition ledger, [] when it is valid. `source`: a path, bytes, text or a list of lines.

    repo/ref: the git repository and ref whose COMMITTED registry snapshot (seed, LEVEL_MAP.json, asset_census.py) the
    reader's loaders read OFFLINE. base: a git ref whose committed copy of the ledger (at `rel_path`; for a path source
    the path's own location in the repo, which must be the canonical ledger path; for text the canonical path) must be an
    exact byte-prefix of `source`; None skips that rule. With require_base (default) a base that cannot be applied
    (path outside the repo toplevel, not the canonical path, unresolvable ref) is itself a problem.
    new_from_seq: rows with record number >= this must name an evidence file that exists, is no symlink and is tracked or
    staged (default: the rows beyond the base copy; none when there is no base)."""
    return _validate(source, repo=repo, ref=ref, base=base, rel_path=rel_path, new_from_seq=new_from_seq,
                     require_base=require_base, reader=reader)[0]


# ---- writing --------------------------------------------------------------------------------------------------
def _now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def init(path, *, reader=None) -> str:
    """Create the header-only ledger. Refuses to overwrite an existing file."""
    text = header_line(reader) + "\n"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        raise DispositionError(f"{path} already exists; init never overwrites a ledger") from None
    try:
        os.write(fd, text.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    return text


def _read_fd(fd):
    chunks, off = [], 0
    while True:
        b = os.pread(fd, 1 << 20, off)
        if not b:
            return b"".join(chunks)
        chunks.append(b)
        off += len(b)


def append(path, entry, *, repo=None, ref="HEAD", base="HEAD", rel_path=None, require_base=True, reader=None) -> dict:
    """Append one correctly chained row; return it. Never rewrites history: the existing bytes are validated first (and
    against `base` in git), the would-be file is validated in memory (the evidence file must exist), then ONE line is
    written at the end under an exclusive lock and fsynced; a failed write is truncated back to the old size. `entry`:
    asset, disposition, evidence (required); reason, decision_id, decided_on, additions (optional; decided_on defaults to
    now, UTC). Raises DispositionError (nothing written) when anything is wrong. The path must not be a symlink. With a
    base, the ledger's own location decides which committed copy it is compared with (`_locate`); a base that cannot
    be applied refuses the append when require_base, else the git rule is skipped (the append itself never rewrites)."""
    T = reader or load_reader()
    repo = str(repo or REPO)
    path = str(path)
    if os.path.islink(path):
        raise DispositionError(f"{path} is a symlink: the ledger must be a regular file inside the repository")
    if base is not None and rel_path is None:
        rel_path, why = _locate(path, T, repo)
        if why is not None:
            if require_base:
                raise DispositionError(f"base {base!r}: NOT CHECKED: {why}")
            base = None
    bad = sorted(set(entry) - {"asset", "disposition", "reason", "decision_id", "decided_on", "additions", "evidence"})
    miss = [k for k in APPEND_REQUIRED if k not in entry]
    if bad or miss:
        raise DispositionError("bad entry", ([f"unknown entry key(s) {bad}"] if bad else []) +
                               ([f"missing required key(s) {miss}"] if miss else []))
    try:
        fd = os.open(path, os.O_RDWR)
    except FileNotFoundError:
        raise DispositionError(f"{path} does not exist (run --init to create the header-only ledger)") from None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        old = _read_fd(fd)
        probs = validate(old, repo=repo, ref=ref, base=base, rel_path=rel_path, reader=T)
        if probs:
            raise DispositionError(f"refusing to append: {path} is not a valid ledger", probs)
        rows = T._e63_lines(old, T.E63_DISPOSITIONS_PATH)
        seq = (rows[-1][2]["seq"] if len(rows) > 1 else 0) + 1
        row = {"asset": entry["asset"], "disposition": entry["disposition"], "reason": entry.get("reason"),
               "decision_id": entry.get("decision_id"), "decided_on": entry.get("decided_on") or _now(),
               "additions": list(entry.get("additions") or []), "evidence": entry["evidence"],
               "seq": seq, "prev_sha256": T._e63_sha(rows[-1][1])}
        try:
            payload = (b"" if old.endswith(b"\n") else b"\n") + json.dumps(row, ensure_ascii=True, allow_nan=False).encode("ascii") + b"\n"
        except (TypeError, ValueError) as e:
            raise DispositionError(f"the entry is not JSON-serialisable ({e})") from None
        probs = validate(old + payload, repo=repo, ref=ref, base=base, rel_path=rel_path, new_from_seq=seq, reader=T)
        if probs:
            raise DispositionError(f"refusing to append: the row would make {path} invalid", probs)
        size = len(old)
        try:
            os.lseek(fd, size, os.SEEK_SET)
            view = memoryview(payload)
            while view:
                view = view[os.write(fd, view):]
            os.fsync(fd)
            if _read_fd(fd) != old + payload:
                raise OSError("the file does not read back as written")
        except BaseException:
            os.ftruncate(fd, size)
            os.fsync(fd)
            raise
        return row
    finally:
        os.close(fd)           # also releases the lock


# ---- CLI ------------------------------------------------------------------------------------------------------
def _parser():
    p = argparse.ArgumentParser(prog="asset_dispositions.py", description=__doc__.split("\n\n")[0])
    m = p.add_mutually_exclusive_group(required=True)
    m.add_argument("--check", action="store_true", help="validate the ledger (exit 1 on any problem)")
    m.add_argument("--append", action="store_true", help="append one chained row")
    m.add_argument("--init", action="store_true", help="create the header-only ledger (never overwrites)")
    m.add_argument("--schema", action="store_true", help="print the schema as JSON")
    p.add_argument("path", nargs="?", help="the ledger (default: the canonical path in --repo)")
    p.add_argument("--repo", help="git repository (default: this one)")
    p.add_argument("--ref", default="HEAD", help="git ref whose committed registry snapshot is read offline (default HEAD)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--base", default=None, help="git ref whose committed ledger must be a byte-prefix (default: the "
                   "merge-base with origin/main, else HEAD with a vacuous note)")
    g.add_argument("--no-base", action="store_true", help="skip the git append-only rule")
    p.add_argument("--asset")
    p.add_argument("--disposition")
    p.add_argument("--evidence")
    p.add_argument("--reason")
    p.add_argument("--decision-id", dest="decision_id")
    p.add_argument("--decided-on", dest="decided_on")
    p.add_argument("--addition", action="append", dest="additions", default=[])
    return p


def main(argv=None, reader=None) -> int:
    a = _parser().parse_args(argv)
    T = reader or load_reader()
    if a.schema:
        print(json.dumps(schema(T), indent=2, sort_keys=True))
        return 0
    repo = str(a.repo or REPO)
    path = a.path or os.path.join(repo, T.E63_DISPOSITIONS_PATH)
    try:
        if a.init:
            init(path, reader=T)
            print(f"created {path} (header only)")
            return 0
        explicit = a.base is not None
        if a.no_base:
            base, note = None, "git rule skipped (--no-base)"
        elif explicit:
            base, note = a.base, f"base {a.base} (explicit)"
        else:
            base, note = default_base(T, repo)
            note = "default base: " + note
        strict = explicit or a.path is None        # a base the user asked for, or the canonical ledger itself, must be checkable
        if a.append:
            if not (a.asset and a.disposition and a.evidence):
                print("--append needs --asset, --disposition and --evidence", file=sys.stderr)
                return 2
            entry = {"asset": a.asset, "disposition": a.disposition, "evidence": a.evidence, "reason": a.reason,
                     "decision_id": a.decision_id, "additions": a.additions}
            if a.decided_on:
                entry["decided_on"] = a.decided_on
            row = append(path, entry, repo=repo, ref=a.ref, base=base, require_base=strict, reader=T)
            print(f"appended seq {row['seq']}: {row['asset']} -> {row['disposition']}")
            return 0
        problems, status = _validate(Path(path), repo=repo, ref=a.ref, base=base, require_base=strict, reader=T)
    except DispositionError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if problems:
        for pr in problems:
            print(f"PROBLEM: {pr}")
        print(f"FAIL: {len(problems)} problem(s) in {path} ({status})")
        return 1
    print(f"OK: {path} ({_record_count(Path(path).read_bytes())} record(s); git rule: {status}; {note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
