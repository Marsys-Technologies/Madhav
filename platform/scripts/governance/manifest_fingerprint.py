#!/usr/bin/env python3
"""Compute, check and stamp CAPABILITY_MANIFEST.json's own top-level fingerprint.

Why this exists. The manifest carries `fingerprint` and `generated_at` at its root. Every
per-entry `fingerprint_sha256` is reproducible — it is the sha256 of the file that entry
points at, and `drift_detector.py` recomputes and compares them. The ROOT fingerprint was
not reproducible by anything: no generator existed in the repository, so the field was
stamped by hand, could not be re-derived, and could not fail. Under CLAUDE.md §N.8 that is
not a checksum, it is a number wearing a checksum's clothes.

The definition, fixed here (2026-09-25):

    fingerprint = sha256( canonical_json(entries) )[:16]
    canonical_json = json.dumps(entries, sort_keys=True, separators=(',',':'), ensure_ascii=False)

`entries` is the manifest's own array, as stored, with `entry_count` derived from it. The
root `fingerprint`/`generated_at`/`entry_count` fields are excluded from the input, so
stamping is stable: computing twice in a row gives the same value.

HONEST LIMIT, stated rather than hidden: this algorithm is DEFINED here, not recovered.
Values stamped before 2026-09-25 were produced by an unknown method and this script cannot
reproduce them. The first `--write` therefore changes the value once, legitimately; every
run after that is a real comparison that can fail.

E5.4 (Suvarna Track E, 2026-10-03) — PER-ENTRY ROTATION. `--check`/`--write` only ever covered
the ROOT. Nothing rotated the per-entry fingerprints, so when a file an entry points at changed
the entry stayed stale until a human re-stamped it by hand (drift_detector reports it as
`fingerprint_mismatch`, HIGH, and its remediation text says "rotate", but no tool did).

  --rotate           recompute every path-bearing entry's fingerprint from the file it points at
                     (working tree, or `--ref REV` blobs); rewrite ONLY the entries whose file
                     changed, each listed old -> new; then re-stamp the root ONCE
                     (fingerprint/entry_count/generated_at). A second run changes nothing.
  --check-rotation   read-only; lists every stale entry (id, path, recorded, actual).

What "the entry's fingerprint" means. The field drift_detector/manifest_reader read: the entry's
`fingerprint_sha256` when it has that key, else the legacy `fingerprint` key (the real manifest
uses `fingerprint`; sha256 hex of the file's bytes). If an entry carries both keys, both are
checked and both rotated. An entry with neither is an ERROR, never a silently invented field.
Entries with no `path` key are virtual (the retrieval-tool rows have no file): not fingerprinted,
counted in the report. `last_verified_*` fields are not touched (they name a session this tool
cannot know).

Refusals (exit 5, NOTHING written — all-or-nothing): corrupt manifest JSON; duplicate keys inside
an object; entries not a list; duplicate or missing canonical_id; duplicate path; an absolute path
or one that climbs out of the repo; a pointed-at file that is missing, unreadable, a directory, not
a regular file, or (working tree) a symlink resolving outside the repo / (ref) a symlink or
submodule blob; an unknown `--entry`; a bad `--ref`. Unlike drift_detector (which skips folder
entries), rotation refuses a directory: it has no file bytes to fingerprint and inventing a value
would be B.10.

Deliberate strictness (E5.4 review, LOW-3): drift_detector SKIPS a directory entry, an entry whose path is empty,
and (via its _FUTURE_ARTIFACTS allowlist) a not-yet-existing file; `--rotate` REFUSES them, and refuses duplicate
ids/paths. That is intentional: a skipped entry keeps whatever hash it has, but a rotation that wrote a hash it could not
compute would be inventing a fingerprint (B.10 / §N.8). `--entry ID` scopes AROUND the per-file refusals (missing,
unreadable, directory, outside-symlink pointer of an entry you did not name are not read and not reported). It does NOT
scope around whole-manifest structural refusals (corrupt JSON, duplicate id, duplicate path, malformed/absolute/escaping
path, an unknown id): those make the entry set itself untrustworthy.

ROOT SHAPE, stated plainly (E5.4 review, MEDIUM-1). The root `fingerprint` this tool stamps is
sha256(canonical_json(entries))[:16]. `platform/src/scripts/manifest/build.ts` (`npm run manifest:build`) stamps a
DIFFERENT shape: the full 64-hex sha256 of JSON.stringify(entries) (insertion order, not sorted). The first rotation of
the real manifest therefore changes the root's shape once (64-hex -> 16-hex), accepted by Suvarna Strategic; the next
`manifest:build` changes it back. Nothing consumes the root's shape: the review of this change found manifest_reader.ts
(cache key), bundle_hydrator, consult/route.ts, the audit_event/bundle schemas and parity_validator.ts all treat it as an
opaque string. `generated_at` is stamped in UTC with the shape the file already carries (build.ts writes
`new Date().toISOString()`, i.e. `YYYY-MM-DDTHH:MM:SS.mmmZ`, which is also the default here); it never depends on the
machine's timezone.

Concurrency/safety of the write: `--rotate` refuses a manifest path that is a symlink (it would replace the link with a
regular file), takes an exclusive non-blocking flock on the manifest's DIRECTORY around read -> compare -> replace (the
manifest's own inode is replaced, so locking the file would not work), and, holding that lock, removes stray
`.manifest-rotate-*` temp files left by a crashed earlier run (under the lock no live writer can own one).

The manifest is edited SURGICALLY: only the bytes of the changed fingerprint values and the three
root stamp values are replaced; key order, indentation, line endings and every other byte are
preserved (so an unrelated entry's diff is empty). The patched text is re-parsed and verified
(entries == old entries with just the rotated values; root == canonical definition) before it is
written atomically (temp file in the same directory, fsync, os.replace), and the write is
abandoned if the manifest changed on disk since it was read.

Usage:
  manifest_fingerprint.py --check            exit 0 match · 2 mismatch · 5 error   (read-only, root)
  manifest_fingerprint.py --write            restamp fingerprint/generated_at/entry_count
  manifest_fingerprint.py --check-rotation [--entry ID ...] [--ref REV] [--repo-root DIR]
                                             exit 0 none stale · 2 stale (listed) · 5 error (read-only)
  manifest_fingerprint.py --rotate         [--entry ID ...] [--ref REV] [--repo-root DIR]
                                             exit 0 rotated/no-op · 5 error (nothing written)
Usage errors exit 5 (not argparse's 2, which here means "stale").
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from collections import OrderedDict
from pathlib import Path

try:  # POSIX only; on a platform without it the lock is skipped, everything else still applies
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

MANIFEST = Path(__file__).resolve().parents[3] / "00_ARCHITECTURE" / "CAPABILITY_MANIFEST.json"

# Per-entry fingerprint keys, in the reader's precedence order (manifest_reader.load_manifest_as_ca).
ENTRY_FP_KEYS = ("fingerprint_sha256", "fingerprint")
ROOT_STAMP_KEYS = ("fingerprint", "entry_count", "generated_at")
TEMP_PREFIX = ".manifest-rotate-"


class RotationError(Exception):
    """Anything that must stop a rotate/check-rotation with exit 5 and no write."""


def canonical_fingerprint(entries: list) -> str:
    blob = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _utcnow() -> dt.datetime:
    """Seam for tests: the single source of 'now' (always timezone-aware UTC)."""
    return dt.datetime.now(dt.timezone.utc)


_SECONDS_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _now_stamp(current=None) -> str:
    """UTC, build.ts shape `YYYY-MM-DDTHH:MM:SS.mmmZ` (default); if the file carries the seconds-only `...SSZ` shape, that."""
    now = _utcnow().astimezone(dt.timezone.utc)
    if isinstance(current, str) and _SECONDS_Z.match(current):
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


# --------------------------------------------------------------------------------------
# Loading (strict: duplicate keys are refused, json.loads would silently keep the last)
# --------------------------------------------------------------------------------------

def _no_dup_pairs(pairs):
    seen = set()
    for k, _ in pairs:
        if k in seen:
            raise RotationError(f"manifest JSON has a duplicate key {k!r} inside one object")
        seen.add(k)
    return OrderedDict(pairs)


def _load_text(path: Path):
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RotationError(f"cannot read manifest {path}: {exc}") from exc
    try:
        manifest = json.loads(text, object_pairs_hook=_no_dup_pairs)
    except json.JSONDecodeError as exc:
        raise RotationError(f"manifest {path} is not valid JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise RotationError("manifest root is not a JSON object")
    return raw, text, manifest


# --------------------------------------------------------------------------------------
# Minimal span scanner: finds the character span of selected values WITHOUT re-serialising
# --------------------------------------------------------------------------------------

_WS = " \t\n\r"


def _ws(t: str, i: int) -> int:
    while i < len(t) and t[i] in _WS:
        i += 1
    return i


def _skip_string(t: str, i: int) -> int:
    i += 1
    while i < len(t):
        c = t[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            return i + 1
        i += 1
    raise RotationError("scanner: unterminated string")


def _skip_value(t: str, i: int) -> int:
    i = _ws(t, i)
    if i >= len(t):
        raise RotationError("scanner: unexpected end of text")
    c = t[i]
    if c == '"':
        return _skip_string(t, i)
    if c == "{":
        return _object_members(t, i)[1]
    if c == "[":
        return _array_elements(t, i)[1]
    j = i
    while j < len(t) and t[j] not in ",}] \t\n\r":
        j += 1
    if j == i:
        raise RotationError("scanner: empty scalar")
    return j


def _object_members(t: str, i: int):
    """t[i] == '{'. Returns ([(key, value_start, value_end)], end_index)."""
    members = []
    i = _ws(t, i + 1)
    if t[i] == "}":
        return members, i + 1
    while True:
        i = _ws(t, i)
        if t[i] != '"':
            raise RotationError("scanner: expected object key")
        kend = _skip_string(t, i)
        key = json.loads(t[i:kend])
        i = _ws(t, kend)
        if t[i] != ":":
            raise RotationError("scanner: expected ':'")
        vs = _ws(t, i + 1)
        ve = _skip_value(t, vs)
        members.append((key, vs, ve))
        i = _ws(t, ve)
        if t[i] == ",":
            i += 1
            continue
        if t[i] == "}":
            return members, i + 1
        raise RotationError("scanner: expected ',' or '}'")


def _array_elements(t: str, i: int):
    """t[i] == '['. Returns ([(value_start, value_end)], end_index)."""
    elems = []
    i = _ws(t, i + 1)
    if t[i] == "]":
        return elems, i + 1
    while True:
        vs = _ws(t, i)
        ve = _skip_value(t, vs)
        elems.append((vs, ve))
        i = _ws(t, ve)
        if t[i] == ",":
            i += 1
            continue
        if t[i] == "]":
            return elems, i + 1
        raise RotationError("scanner: expected ',' or ']'")


def locate_spans(text: str):
    """Returns (root_spans: {key: (s, e)}, entry_spans: [{key: (s, e)}]) for the manifest text."""
    i = _ws(text, 0)
    if text[i] != "{":
        raise RotationError("scanner: manifest root is not an object")
    members, _ = _object_members(text, i)
    root = {k: (s, e) for k, s, e in members}
    entry_spans = []
    if "entries" in root:
        s, e = root["entries"]
        if text[s] != "[":
            raise RotationError("scanner: 'entries' is not an array")
        elems, _ = _array_elements(text, s)
        for es, _ee in elems:
            if text[es] != "{":
                raise RotationError("scanner: an entry is not an object")
            m, _ = _object_members(text, es)
            entry_spans.append({k: (vs, ve) for k, vs, ve in m})
    return root, entry_spans


# --------------------------------------------------------------------------------------
# Entry validation and fingerprint sources
# --------------------------------------------------------------------------------------

def _norm_rel(path_value, cid) -> str:
    if not isinstance(path_value, str) or not path_value.strip():
        raise RotationError(f"entry {cid}: 'path' is present but not a non-empty string")
    if "\\" in path_value or path_value.startswith("/") or (len(path_value) > 1 and path_value[1] == ":"):
        raise RotationError(f"entry {cid}: path {path_value!r} is absolute or not a repo-relative POSIX path")
    n = posixpath.normpath(path_value)
    if n == "." or n == ".." or n.startswith("../"):
        raise RotationError(f"entry {cid}: path {path_value!r} climbs out of the repository")
    return n


def validate_entries(manifest) -> list:
    """Structural refusals that apply to every entry. Returns [(index, id, norm_path_or_None)]."""
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise RotationError("manifest 'entries' is missing or not a list")
    out, seen_ids, seen_paths = [], {}, {}
    for idx, e in enumerate(entries):
        if not isinstance(e, dict):
            raise RotationError(f"entries[{idx}] is not an object")
        cid = e.get("canonical_id")
        if not isinstance(cid, str) or not cid:
            raise RotationError(f"entries[{idx}] has no canonical_id")
        if cid in seen_ids:
            raise RotationError(f"duplicate canonical_id {cid!r} (entries[{seen_ids[cid]}] and entries[{idx}])")
        seen_ids[cid] = idx
        rel = None
        if "path" in e:
            rel = _norm_rel(e["path"], cid)
            if rel in seen_paths:
                raise RotationError(f"duplicate path {rel!r} (entries {seen_paths[rel]!r} and {cid!r})")
            seen_paths[rel] = cid
        out.append((idx, cid, rel))
    return out


def _git(repo_root: Path, *args: str, binary: bool = False):
    try:
        r = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, check=False)
    except OSError as exc:
        raise RotationError(f"git unavailable: {exc}") from exc
    return r


def _check_ref(repo_root: Path, ref: str) -> None:
    if ref.startswith("-"):
        raise RotationError(f"refusing --ref {ref!r}: starts with '-'")
    r = _git(repo_root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if r.returncode != 0:
        raise RotationError(f"--ref {ref!r} does not resolve to a commit in {repo_root}")


def read_pointed_file(repo_root: Path, rel: str, ref: str | None) -> bytes:
    """Bytes of the file an entry points at. Raises RotationError (reason only) when it cannot be fingerprinted."""
    if ref is not None:
        r = _git(repo_root, "ls-tree", "-z", ref, "--", rel)
        if r.returncode != 0:
            raise RotationError(f"git ls-tree failed: {r.stderr.decode('utf-8', 'replace').strip()}")
        rec = r.stdout.split(b"\0")[0]
        if not rec:
            raise RotationError(f"missing: {rel!r} does not exist at {ref}")
        meta, _, _name = rec.partition(b"\t")
        mode, typ, sha = meta.decode().split(" ")
        if typ == "tree":
            raise RotationError(f"{rel!r} is a directory at {ref}")
        if typ != "blob" or mode == "120000":
            raise RotationError(f"{rel!r} at {ref} is a symlink or submodule, not a regular file")
        b = _git(repo_root, "cat-file", "blob", sha)
        if b.returncode != 0:
            raise RotationError(f"unreadable: git cat-file failed for {rel!r} at {ref}")
        return b.stdout
    full = repo_root / rel
    if not os.path.lexists(full):
        raise RotationError(f"missing: {rel!r} does not exist")
    resolved = full.resolve()
    root_resolved = repo_root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        raise RotationError(f"{rel!r} resolves outside the repository ({resolved})") from None
    if resolved.is_dir():
        raise RotationError(f"{rel!r} is a directory")
    if not resolved.is_file():
        raise RotationError(f"{rel!r} is not a regular file")
    try:
        return resolved.read_bytes()
    except OSError as exc:
        raise RotationError(f"unreadable: {rel!r}: {exc}") from exc


# --------------------------------------------------------------------------------------
# Rotation planning
# --------------------------------------------------------------------------------------

def plan_rotation(manifest, repo_root: Path, ref: str | None, only_ids=None):
    """Returns (changes, errors, checked, virtual).

    changes: [{index, id, path, field, recorded, actual}] one per stale fingerprint field
    errors:  [{id, path, reason}] one per entry that cannot be fingerprinted
    """
    table = validate_entries(manifest)
    ids = {cid for _, cid, _ in table}
    selected = None
    if only_ids:
        unknown = [i for i in only_ids if i not in ids]
        if unknown:
            raise RotationError(f"--entry names no such canonical_id: {', '.join(unknown)}")
        selected = set(only_ids)
    if ref is not None:
        _check_ref(repo_root, ref)
    entries = manifest["entries"]
    changes, errors, checked, virtual = [], [], 0, 0
    for idx, cid, rel in table:
        if selected is not None and cid not in selected:
            continue
        if rel is None:
            if selected is not None:
                errors.append({"id": cid, "path": None, "reason": "virtual entry (no 'path'): no file to fingerprint"})
            else:
                virtual += 1
            continue
        fields = [k for k in ENTRY_FP_KEYS if k in entries[idx]]
        if not fields:
            errors.append({"id": cid, "path": rel, "reason": "entry has neither 'fingerprint_sha256' nor 'fingerprint'; refusing to invent a field"})
            continue
        try:
            actual = hashlib.sha256(read_pointed_file(repo_root, rel, ref)).hexdigest()
        except RotationError as exc:
            errors.append({"id": cid, "path": rel, "reason": str(exc)})
            continue
        checked += 1
        for f in fields:
            if entries[idx][f] != actual:
                changes.append({"index": idx, "id": cid, "path": rel, "field": f, "recorded": entries[idx][f], "actual": actual})
    return changes, errors, checked, virtual


def _fmt_changes(changes):
    return [f"STALE {c['id']} {c['path']} [{c['field']}] recorded={c['recorded']} actual={c['actual']}" for c in changes]


def _fmt_errors(errors):
    return [f"ERROR {e['id']} {e['path'] if e['path'] is not None else '<no path>'}: {e['reason']}" for e in errors]


def _atomic_write(path: Path, data: bytes, expected_old: bytes) -> None:
    if path.read_bytes() != expected_old:
        raise RotationError("manifest changed on disk while rotating; nothing written (re-run)")
    fd, tmp = tempfile.mkstemp(prefix=TEMP_PREFIX, dir=str(path.parent))
    try:
        try:
            fh = os.fdopen(fd, "wb")
        except BaseException:
            os.close(fd)
            raise
        with fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


@contextmanager
def _directory_lock(directory: Path):
    """Exclusive non-blocking flock on the manifest's DIRECTORY (the manifest inode itself is replaced by os.replace, so a
    lock on the file would protect nothing). Raises RotationError if another rotation holds it."""
    if fcntl is None:  # pragma: no cover
        yield
        return
    fd = os.open(str(directory), os.O_RDONLY)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RotationError(f"another rotation holds the lock on {directory}; nothing written") from exc
        yield
    finally:
        os.close(fd)  # closing releases the flock


def _sweep_stale_temps(directory: Path) -> list:
    """Called WITH the lock held: any `.manifest-rotate-*` regular file is an orphan of a crashed run (a live writer
    would hold the lock). Symlinks and directories with that prefix are not ours and are left alone."""
    removed = []
    for p in sorted(directory.glob(TEMP_PREFIX + "*")):
        if p.is_symlink() or not p.is_file():
            continue
        try:
            p.unlink()
            removed.append(p.name)
        except OSError:
            pass
    return removed


def build_rotated_text(raw_text: str, manifest, changes, stamp_root: bool):
    """Surgically patch raw_text. Returns (new_text, new_entries, new_root_values)."""
    root_spans, entry_spans = locate_spans(raw_text)
    entries = manifest["entries"]
    if len(entry_spans) != len(entries):
        raise RotationError("internal: scanner and parser disagree on the number of entries")
    new_entries = copy.deepcopy(entries)
    edits = []  # (start, end, replacement)
    for c in changes:
        spans = entry_spans[c["index"]]
        if c["field"] not in spans:
            raise RotationError(f"internal: no span for {c['id']}.{c['field']}")
        s, e = spans[c["field"]]
        edits.append((s, e, json.dumps(c["actual"], ensure_ascii=False)))
        new_entries[c["index"]][c["field"]] = c["actual"]
    new_root = {}
    if stamp_root:
        missing = [k for k in ROOT_STAMP_KEYS if k not in root_spans]
        if missing:
            raise RotationError(
                f"manifest root lacks {', '.join(missing)}; surgical restamp will not add keys (run --write once)")
        new_root = {
            "fingerprint": canonical_fingerprint(new_entries),
            "entry_count": len(new_entries),
            "generated_at": _now_stamp(manifest.get("generated_at")),
        }
        for k, v in new_root.items():
            s, e = root_spans[k]
            edits.append((s, e, json.dumps(v, ensure_ascii=False)))
    new_text = raw_text
    for s, e, rep in sorted(edits, key=lambda x: x[0], reverse=True):
        new_text = new_text[:s] + rep + new_text[e:]
    return new_text, new_entries, new_root


def _verify_patched(new_text: str, old_manifest, new_entries, new_root, changes) -> None:
    """Earned-signal self-check: the text we are about to write parses to exactly what we intend."""
    try:
        parsed = json.loads(new_text, object_pairs_hook=_no_dup_pairs)
    except (json.JSONDecodeError, RotationError) as exc:
        raise RotationError(f"internal: patched manifest does not parse ({exc}); nothing written") from exc
    if list(parsed.keys()) != list(old_manifest.keys()):
        raise RotationError("internal: patched manifest root key order differs; nothing written")
    if parsed["entries"] != new_entries or [list(e.keys()) for e in parsed["entries"]] != [list(e.keys()) for e in new_entries]:
        raise RotationError("internal: patched entries differ from the intended entries; nothing written")
    for k, v in old_manifest.items():
        if k in ("entries", *ROOT_STAMP_KEYS):
            continue
        if parsed[k] != v:
            raise RotationError(f"internal: root field {k!r} changed; nothing written")
    if parsed["fingerprint"] != canonical_fingerprint(parsed["entries"]) or parsed["entry_count"] != len(parsed["entries"]):
        raise RotationError("internal: root stamp does not equal the canonical definition; nothing written")
    changed_idx = {c["index"] for c in changes}
    for idx, (old, new) in enumerate(zip(old_manifest["entries"], parsed["entries"])):
        if idx not in changed_idx and old != new:
            raise RotationError(f"internal: unchanged entry {old.get('canonical_id')} was modified; nothing written")


# --------------------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------------------

def _repo_root_for(manifest_path: Path, override: str | None) -> Path:
    if override:
        return Path(override)
    return manifest_path.resolve().parents[1]


def mode_check_rotation(args) -> int:
    path = Path(args.manifest)
    _raw, _text, manifest = _load_text(path)
    repo_root = _repo_root_for(path, args.repo_root)
    changes, errors, checked, virtual = plan_rotation(manifest, repo_root, args.ref, args.entry)
    src = f"ref {args.ref}" if args.ref else "working tree"
    print(f"per-entry check against {src}: {checked} fingerprinted, {virtual} virtual (no path), "
          f"{len({c['id'] for c in changes})} stale, {len(errors)} unreadable")
    for line in _fmt_changes(changes) + _fmt_errors(errors):
        print(line)
    entries = manifest["entries"]
    root_ok = manifest.get("fingerprint") == canonical_fingerprint(entries) and manifest.get("entry_count") == len(entries)
    print(f"root fingerprint (informational, see --check): {'MATCH' if root_ok else 'MISMATCH'}")
    if errors:
        return 5
    if changes:
        print("RESULT: stale entries listed above — run --rotate in the session that changed the files")
        return 2
    print("RESULT: OK — no entry is stale")
    return 0


def mode_rotate(args) -> int:
    path = Path(args.manifest)
    if path.is_symlink():
        raise RotationError(f"manifest path {path} is a symlink; os.replace would swap the link for a regular file. "
                            "Point --manifest at the real file")
    with _directory_lock(path.resolve().parent):
        for name in _sweep_stale_temps(path.resolve().parent):
            print(f"removed stray temp file from a crashed earlier run: {name}")
        return _rotate_locked(args, path)


def _rotate_locked(args, path: Path) -> int:
    raw, text, manifest = _load_text(path)
    repo_root = _repo_root_for(path, args.repo_root)
    changes, errors, checked, virtual = plan_rotation(manifest, repo_root, args.ref, args.entry)
    if errors:
        for line in _fmt_errors(errors):
            print(line)
        print(f"REFUSED: {len(errors)} entr{'y' if len(errors) == 1 else 'ies'} cannot be fingerprinted; nothing written", file=sys.stderr)
        return 5
    entries = manifest["entries"]
    root_ok = manifest.get("fingerprint") == canonical_fingerprint(entries) and manifest.get("entry_count") == len(entries)
    if not changes and root_ok:
        print(f"no-op: {checked} entries checked, none stale, root already matches; nothing written")
        return 0
    new_text, new_entries, new_root = build_rotated_text(text, manifest, changes, stamp_root=True)
    _verify_patched(new_text, manifest, new_entries, new_root, changes)
    _atomic_write(path, new_text.encode("utf-8"), raw)
    for c in changes:
        print(f"ROTATED {c['id']} {c['path']} [{c['field']}]: {c['recorded']} -> {c['actual']}")
    print(f"rotated {len({c['id'] for c in changes})} entr{'y' if len({c['id'] for c in changes}) == 1 else 'ies'}; "
          f"{checked - len({c['id'] for c in changes})} unchanged; root restamped: "
          f"fingerprint={new_root['fingerprint']} (was {manifest.get('fingerprint')})")
    return 0


class _Parser(argparse.ArgumentParser):
    def error(self, message):  # exit 5, not argparse's 2 (2 means "stale" here)
        self.print_usage(sys.stderr)
        print(f"manifest_fingerprint: usage error — {message}", file=sys.stderr)
        sys.exit(5)


def main(argv=None) -> int:
    ap = _Parser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    g.add_argument("--rotate", action="store_true")
    g.add_argument("--check-rotation", action="store_true", dest="check_rotation")
    ap.add_argument("--manifest", default=str(MANIFEST))
    ap.add_argument("--entry", action="append", default=None, metavar="CANONICAL_ID")
    ap.add_argument("--ref", default=None, metavar="REV")
    ap.add_argument("--repo-root", default=None, dest="repo_root")
    args = ap.parse_args(argv)

    if args.rotate or args.check_rotation:
        try:
            return mode_rotate(args) if args.rotate else mode_check_rotation(args)
        except RotationError as exc:
            print(f"manifest_fingerprint: refused — {exc}", file=sys.stderr)
            return 5
    if args.entry or args.ref or args.repo_root:
        ap.error("--entry/--ref/--repo-root apply only to --rotate and --check-rotation")

    path = Path(args.manifest)
    manifest = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
    entries = manifest.get("entries", [])
    observed = canonical_fingerprint(entries)
    declared = manifest.get("fingerprint", "")
    count_declared = manifest.get("entry_count")

    if args.check:
        ok = observed == declared and count_declared == len(entries)
        print(f"entries: {len(entries)} (declared {count_declared})")
        print(f"fingerprint declared: {declared or '<none>'}")
        print(f"fingerprint observed: {observed}")
        print("MATCH" if ok else "MISMATCH — run --write in the session that changed the manifest")
        return 0 if ok else 2

    manifest["entry_count"] = len(entries)
    manifest["fingerprint"] = observed
    manifest["generated_at"] = _now_stamp(manifest.get("generated_at"))
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"stamped: entry_count={len(entries)} fingerprint={observed} (was {declared or '<none>'})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"manifest_fingerprint: script error — {exc}", file=sys.stderr)
        sys.exit(5)
