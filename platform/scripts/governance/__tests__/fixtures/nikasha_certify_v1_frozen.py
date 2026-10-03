#!/usr/bin/env python3
"""nikasha_certify.py — Suvarna E5.1: write certification records (arch 12.16) into `asset_certs.jsonl`.

A certification record is what an asset's ELEVATED state rests on (plan 1.1), so this writer is mostly a set of
REFUSALS; every PASS or N/A it can emit has a code path that could have made it read otherwise (CLAUDE.md N.8):

  * for kind=gate the VERDICT IS NOT A CALLER ASSERTION. The census is mandatory: the writer reads the verdict,
    basis, N/A cause and applicability facts from the census cell of that asset and criterion. The census is a FILE,
    either the flat single-layer form or the real multi-layer `asset_census.json` ({"L0": {...}, ..., "rollup": ...};
    the layer object is selected by the asset's layer, `rollup` is ignored), and it must be COMMITTED under the one
    constant trusted root `TRUSTED_CENSUS_ROOT` (repo-relative; working tree AND tracked-or-staged in git, the state
    is recorded). It is refused when it is not, when it lacks that asset or cell, when `evidence.census_run_id`
    differs from the layer object's own `generated`, when the layer head carries no registry revision / fingerprint /
    tool_commit (`census_unbound`) or a revision or fingerprint other than the current registry
    (`census_registry_mismatch`), or when a caller-passed verdict/basis/facts differ from the census (a caller
    verdict is only a cross-check). The sha256 of the WHOLE census file is recorded in `evidence.census_sha256`,
    `cross_checked: true` is writer-set on every gate record. kind=addition has no census cell: its verdict is the
    caller's, its N/A is always refused, its basis can never be typed;
  * `verify_ledger_census_hashes(repo, ref)` (CLI `--verify-census-hashes`, run by CI on every PR) re-reads every
    cited census file with `git show <ref>:<path>`, recomputes the sha256 and FAILS on a mismatch, a file that is not
    committed, or one outside the root; it reports NO_DETECTOR (never PASS) when there is nothing to verify;
  * a PASS (or any verdict but NO_DETECTOR) whose criterion has `detector: NONE` is refused;
  * a record with no census run id in its evidence is refused (the id is the census's own `generated` timestamp);
  * an N/A is never typed: it is recorded only when the registry computes it (applicability from the census RECORD's
    facts; a measured cause from the census cell), and only under a rule declared in `asset_census.NA_RULE_DECISIONS`
    (empty today, so every N/A is refused until N-22 declares a rule);
  * the registry, not the caller, supplies the gate, detector, criterion revision and registry fingerprint;
  * a PASS the census rollup itself would not honour (Null.* and Narr.fidelity_test capped at PARTIAL, an
    INCONCLUSIVE record, an unrecognised basis, a basis `declaration` the registry does not define for that
    criterion and asset kind) is refused;
  * a PASS without a semantic fingerprint and VERIFIED writer file hashes (or a documented, census-corroborated
    reason for having none) could never go stale, so it is refused. Writer files are bound to the asset: a hashed file
    must be one the census record lists as that asset's writer (`asset_census._writer_path`), and the census must not
    be older than the commit time of the writer (`census_older_than_writer`; undeterminable => `writer_time_unknown`).
    Upstream certification ids must exist, be the latest generation, and pass.

The ledger is append-only and hash-chained: each record carries `seq` (1-based, 1..N) and `prev_sha256` (the sha256
of the previous line's bytes; the `_schema` row for the first record), verified on every read and write (a torn
last line is `torn_ledger`; `--repair-torn-tail` is the explicit, printed repair). Reads take a shared lock, writes an
exclusive one. A record is identified by `cert_key` = `<asset>|<gate|addition>|<criterion>`, numbered by `generation`
from 1, with `cert_id` = `<cert_key>@<generation>`. Re-writing a measurement whose CURRENCY fields are unchanged
appends nothing; a changed one appends generation+1. Currency fields are the ones E5.5 invalidates on (verdict,
criterion/registry revision, detector, writer hashes and whether they were verified, upstream ids, semantic
fingerprint, N/A computation, basis, inconclusive, transitive_only); `evidence`, `verified_by`, `verified_on`,
`job_image_tag`, `cross_checked`, `seq` and `prev_sha256` are provenance of the generation that first carried them.

PUBLIC API for sibling writers (E5.5 appends invalidation / watermark lines to the same ledger): `append_records(ledger_path,
records) -> int` (the one write path: exclusive lock, whole-ledger verification, `seq`/`prev_sha256` filled, canonical
serialisation, one append, never an edit; `write_certification` uses it too), `chain_head(data) -> (last_seq,
last_line_sha)`, `parse_ledger(data)` (cert index), `parse_records(data)` / `read_records(path)` (every line, events
included), `read_ledger(path)`. A non-certificate line is an event: a `type` in EVENT_TYPES (invalidation, watermark, epoch_reset) and no certificate-only field.

CENSUS LIFECYCLE (read this before citing a census): asset_census.py main() OVERWRITES `control/asset_census.json` on every
run, so that path is not a citable file. Copy the census to a UNIQUE name under TRUSTED_CENSUS_ROOT, e.g. with
`archive_census(src, repo, generated)` (CLI `--archive-census SRC --repo R --generated G`; byte-identical copy to
`00_ARCHITECTURE/control/census/asset_census_<generated>.json`, never overwriting), `git add` it, and cite THAT; never
edit it afterwards. A path already cited with another sha256 is refused (`census_path_reused`), else the ledger would
stay red forever (evidence is not a currency field, so re-certifying would read `unchanged`).
WRITER TIME: the writer-time rule compares the census `generated` with the writer's COMMITTER date (`git log -1
--format=%cI`). A rebase or cherry-pick of the writer moves that date forward, so the census must then be regenerated
(fail-safe: the old census is refused `census_older_than_writer`).
WRITER COMPLETENESS: for an asset the census says has a writer (has_writer=true) a PASS (or measured N/A) must hash
EXACTLY the census-listed writer files (`writer_files_incomplete` otherwise).

RESIDUALS (honest scope; the threat model is accident and agent shortcut, not a hostile writer): the hash chain gives
NO tamper evidence against anyone who can rewrite or truncate the whole file (there is no head anchor); tamper
evidence against a whole-file rewrite is git history on main, not the chain. Census authenticity is: committed under
the trusted root, sha256 stored, CI recomputes it; git history is the anchor. An edit of the last line is visible only
once another record follows. E5.5 reads these records and decides when one has gone stale; this writer only
guarantees it was honest when written and the history intact.

Ledger path: `--ledger` / `ledger_path`, else $NIKASHA_CERTS_LEDGER, else <control dir>/asset_certs.jsonl
(`asset_census.CTRL`, itself overridable with NIKASHA_CONTROL_DIR). A missing ledger is refused unless `--init`; a
symlink or directory at the ledger path is refused (never followed); a zero-byte file under `--init` is initialised.

Usage:
  nikasha_certify.py --asset bg_ontology --layer L0 --criterion Build.registered \
      --census 00_ARCHITECTURE/control/census/asset_census.json --writer-file platform/python-sidecar/.../bg_ontology.py \
      --writer-ref <commit> --semantic-fingerprint <sha256> --verified-by census-run
  nikasha_certify.py --verify-census-hashes --repo . --ref origin/main      (CI)
  nikasha_certify.py --repair-torn-tail --ledger <path>                     (explicit, prints what it removes)
Exit: 0 appended / unchanged / verified (stdout: JSON) · 2 refused (stderr: `REFUSED <code>: ...`; nothing written)
      · 3 verify: NO_DETECTOR (skipped with a reason) · 5 script error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asset_census as ac  # noqa: E402  (read-only use of its registry, applicability and N/A tables)

RECORD_VERSION = 1
VERDICTS = ("PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "ERRORED", "N/A")
KINDS = ("gate", "addition")
ENV_LEDGER = "NIKASHA_CERTS_LEDGER"
# The ONE trusted census root (repo-relative, inside the git work tree). A constant, never a request field, flag or env
# var. A cert may cite only a census file committed (or staged for the same PR) under it.
TRUSTED_CENSUS_ROOT = "00_ARCHITECTURE/control/census/"
LEDGER_RELPATH = "00_ARCHITECTURE/control/asset_certs.jsonl"
MAX_JSON_DEPTH = 64
CALLER_EVIDENCE_KEYS = ("census_run_id", "measured", "inspector_commit", "note")
WRITER_EVIDENCE_KEYS = ("census_file", "census_sha256", "census_git", "census_tool_commit")   # writer-set from the census file; never typed
# Fields E5.5 invalidates on (and so the only fields whose change makes a new generation). Everything else on a
# record is provenance for the generation that first carried it.
CURRENCY_FIELDS = ("verdict", "criterion_version", "registry_revision", "registry_fingerprint",
                   "detector", "writer_hashes", "writer_hashes_verified", "writer_hashes_reason", "upstream_cert_ids",
                   "semantic_fingerprint", "na", "basis", "inconclusive", "transitive_only")
# The documented reasons a PASS may have no writer file when the census record does not state `has_writer`.
WRITER_REASONS = ("service_no_writer", "global_reference_data")
# Where the registry defines a PASS BY DECLARATION (asset_census._measure_target, Build.target rev 2): criterion ->
# the asset kinds it applies to. A census cell carrying basis `declaration` anywhere else is not honoured here.
DECLARATION_BASED = {"Build.target": ("service",)}

_ASSET = re.compile(r"[a-z][a-z0-9_]*")
_ADDITION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_CERT_ID = re.compile(r"([a-z][a-z0-9_]*)\|(gate|addition)\|([A-Za-z0-9][A-Za-z0-9_.-]*)@([1-9][0-9]*)")
_DECLARATION = "declaration"        # the one recognised `basis` (asset_census._check_contribution), case-exact

SCHEMA_DOC = (
    "Certification ledger (arch 12.16; plan 1.1). Append-only and hash-chained: lines are only ever added, never "
    "edited or deleted; each record carries seq (1..N) and prev_sha256, the sha256 of the previous line's bytes (this "
    "row for the first). The chain gives no tamper evidence against a whole-file rewrite or truncation: that anchor is "
    "git history on main. One JSON object per line after this one, written only by nikasha_certify.py. Fields: asset, "
    "layer, kind (gate|addition), gate, criterion, criterion_version, registry_revision, registry_fingerprint, "
    "detector, verdict (PASS|FAIL|PARTIAL|NO_DETECTOR|ERRORED|N/A; a gate's is read from the census cell), basis, na "
    "{rule_id, decision_id, basis, cause, facts}, inconclusive, transitive_only, evidence {census_run_id (required), "
    "measured, inspector_commit, note, and writer-set census_file (repo-relative, committed under the trusted census "
    "root), census_sha256, census_git, census_tool_commit}, cross_checked, job_image_tag, writer_hashes {path: "
    "sha256}, writer_hashes_verified, writer_hashes_reason, upstream_cert_ids, semantic_fingerprint, cert_key, "
    "generation, cert_id, seq, prev_sha256, verified_by, verified_on, record_version. The current record of a cert_key "
    "is its highest generation; whether it is still CURRENT (writer hashes, upstream generations, semantic "
    "fingerprint, registry revision) is E5.5's decision. A line without cert_key carries a `type` in EVENT_TYPES (an event, "
    "e.g. E5.5's invalidation); it is chained and sequenced like every line."
)


class CertificationRefused(ValueError):
    """The request was refused; nothing was written. `code` is the stable, test-pinned reason slug."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _refuse(code: str, message: str):
    raise CertificationRefused(code, message)


@dataclass(frozen=True)
class CertResult:
    status: str          # "appended" | "unchanged"
    record: dict         # the record appended, or the existing latest generation when unchanged
    cert_id: str
    ledger_path: Path


@dataclass(frozen=True)
class _CensusSource:
    obj: dict
    sha256: str
    path: str          # repo-relative, posix
    git: str           # "committed" | "staged"


# ─────────────────────────── strict JSON ───────────────────────────

def _no_dup_keys(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate key {k!r}")
        d[k] = v
    return d


def _no_constant(name):
    raise ValueError(f"non-finite constant {name}")


def _max_depth(text: str) -> int:
    depth = best = 0
    in_str = esc = False
    for ch in text:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "[{":
            depth += 1
            best = max(best, depth)
        elif ch in "]}":
            depth -= 1
    return best


def strict_json_loads(text: str):
    """json.loads that refuses duplicate object keys, NaN/Infinity and nesting deeper than MAX_JSON_DEPTH
    (ValueError, incl. JSONDecodeError; a RecursionError is a ValueError too, never a crash)."""
    if _max_depth(text) > MAX_JSON_DEPTH:
        raise ValueError(f"nesting deeper than {MAX_JSON_DEPTH}")
    try:
        return json.loads(text, object_pairs_hook=_no_dup_keys, parse_constant=_no_constant)
    except RecursionError as e:
        raise ValueError("nesting too deep") from e


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ─────────────────────────── ledger path, reading ───────────────────────────

def resolve_ledger_path(ledger_path=None, env=None) -> Path:
    env = os.environ if env is None else env
    if ledger_path is not None:
        return Path(ledger_path)
    if env.get(ENV_LEDGER):
        return Path(env[ENV_LEDGER])
    return ac.CTRL / "asset_certs.jsonl"


def cert_key_of(asset: str, kind: str, criterion: str) -> str:
    return f"{asset}|{kind}|{criterion}"


# The line types E5.5's reader dispatches on. A reader that meets any other line raises, and the ledger is append-only,
# so one stray line would brick every later run: adding a type here is a DELIBERATE edit made together with the reader.
EVENT_TYPES = ("invalidation", "watermark", "epoch_reset")
_EVENT_ONLY_FORBIDDEN = ("cert_key", "cert_id", "generation")      # certificate-only fields an event may not carry


def _is_cert_line(r: dict) -> bool:
    key, gen = r.get("cert_key"), r.get("generation")
    return (isinstance(key, str) and not isinstance(gen, bool) and isinstance(gen, int) and gen >= 1
            and r.get("cert_id") == f"{key}@{gen}" and isinstance(r.get("verdict"), str))


def _is_event_line(r: dict, allowed=EVENT_TYPES) -> bool:
    """A non-certification record (E5.5's invalidation / watermark / epoch_reset lines): it MUST name a `type` that is in
    `allowed` (a subset of EVENT_TYPES) and must carry no certificate-only field: no cert_key / cert_id / generation, no
    `verdict` that is a certificate verdict, no `kind` of a certificate (gate/addition). It is chained and sequenced
    like every line, but is not a certificate and is not in the cert index."""
    t = r.get("type")
    if not isinstance(t, str) or t not in allowed:
        return False
    if any(k in r for k in _EVENT_ONLY_FORBIDDEN):
        return False
    if r.get("kind") in KINDS or (isinstance(r.get("verdict"), str) and r["verdict"] in VERDICTS):
        return False
    return True


@dataclass(frozen=True)
class _Parsed:
    by_key: dict          # cert_key -> certificate records in file order
    records: list         # EVERY record line (certificates and events) in file order, schema row excluded
    prev: str             # sha256 of the last non-blank line's bytes (the head of the chain)
    n: int                # number of record lines = the last seq


def _dump(obj) -> bytes:
    """The ONE canonical serialisation of a ledger line (no trailing newline)."""
    return json.dumps(obj, ensure_ascii=False, allow_nan=False).encode("utf-8")


def _parse_full(data: bytes) -> _Parsed:
    """Strict reading of a ledger. Refuses (`bad_ledger`): an unreadable or non-UTF-8 line, a duplicate key, a first
    line that is not the `_schema` row, a second `_schema` row, a line that is neither a certificate (cert_key /
    generation / cert_id / verdict) nor an event (`type`), a generation sequence that is not 1..n per cert_key, a `seq`
    that is not 1..N over the record lines, or a `prev_sha256` chain that does not hold. A last line with no newline
    that is not valid JSON is a torn write: `torn_ledger`. A ledger this writer cannot reason about is not appended to."""
    if not data:
        _refuse("bad_ledger", "the ledger is empty (no `_schema` row)")
    parts = data.split(b"\n")
    tail = parts[-1]                                  # b"" when the file ends with a newline
    raw_lines = parts[:-1] + ([tail] if tail else [])
    rows = []
    for n, raw in enumerate(raw_lines, 1):
        if not raw.strip():
            continue
        try:
            rows.append((n, raw, strict_json_loads(raw.decode("utf-8"))))
        except (UnicodeDecodeError, ValueError) as e:
            if tail and n == len(raw_lines):
                _refuse("torn_ledger", f"line {n} (no trailing newline) is a partial write ({e}): the ledger is torn; "
                                       "it is neither extended nor silently repaired: see --repair-torn-tail")
            _refuse("bad_ledger", f"line {n} is not readable JSON ({e})")
    if not rows or not isinstance(rows[0][2], dict) or rows[0][2].get("asset") != "_schema":
        _refuse("bad_ledger", "the first line must be the `_schema` row")
    by_key: dict[str, list[dict]] = {}
    records: list[dict] = []
    prev = _sha(rows[0][1])
    n_rec = 0
    for n, raw, r in rows[1:]:
        if not isinstance(r, dict):
            _refuse("bad_ledger", f"line {n} is not a JSON object")
        if r.get("asset") == "_schema":
            _refuse("bad_ledger", f"line {n}: a second `_schema` row")
        cert = _is_cert_line(r)
        if not cert and not _is_event_line(r):
            _refuse("bad_ledger", f"line {n} is not a record this writer can read (a certificate needs cert_key/"
                                  "generation/cert_id/verdict; any other line needs a `type`)")
        if isinstance(r.get("seq"), bool) or r.get("seq") != n_rec + 1:
            _refuse("bad_ledger", f"line {n}: seq is {r.get('seq')!r}, expected {n_rec + 1} (seq runs 1..N over the records)")
        if r.get("prev_sha256") != prev:
            _refuse("bad_ledger", f"line {n}: the hash chain is broken (prev_sha256 is not the sha256 of the previous "
                                  "line): an earlier line was edited, deleted or reordered")
        prev = _sha(raw)
        n_rec += 1
        records.append(r)
        if cert:
            by_key.setdefault(r["cert_key"], []).append(r)
    for key, recs in by_key.items():
        if [r["generation"] for r in recs] != list(range(1, len(recs) + 1)):
            _refuse("bad_ledger", f"{key}: generations are not 1..{len(recs)} in order")
    return _Parsed(by_key, records, prev, n_rec)


def _parse(data: bytes):
    """(cert_key -> certificate records, sha256 of the last line, record count): the pre-`_Parsed` private shape."""
    p = _parse_full(data)
    return p.by_key, p.prev, p.n


def parse_ledger(data: bytes) -> dict[str, list[dict]]:
    """PUBLIC. cert_key -> its certificate records in file order, from the ledger's bytes; verifies the whole chain, seq
    and generations (see `_parse_full` for what is refused). Event lines are verified but not returned here: use
    `parse_records` for every line."""
    return _parse_full(data).by_key


def parse_records(data: bytes) -> list[dict]:
    """PUBLIC. EVERY record line (certificates and `type`d events) in file order, after the same verification."""
    return list(_parse_full(data).records)


def chain_head(data: bytes) -> tuple[int, str]:
    """PUBLIC. (last_seq, sha256 of the last non-blank line's bytes) of a ledger given as bytes, after verifying it.
    A ledger holding only the `_schema` row is (0, sha256 of that row)."""
    p = _parse_full(data)
    return p.n, p.prev


def read_ledger(path) -> dict[str, list[dict]]:
    """Read-only helper for E5.5 / E6.3: cert_key -> records. Raises CertificationRefused('bad_ledger' /
    'torn_ledger') as above, including when the hash chain does not hold."""
    p = Path(path)
    if not p.exists():
        _refuse("ledger_missing", f"{p} does not exist")
    return parse_ledger(_read_shared(p))


def _read_shared(p: Path) -> bytes:
    try:
        with open(p, "rb") as f:
            fcntl.flock(f, fcntl.LOCK_SH)          # never see a concurrent append half written
            return f.read()
    except OSError as e:
        _refuse("bad_ledger", f"{p} cannot be read ({e})")


def read_records(path) -> list[dict]:
    """PUBLIC read-only helper: every record line (certificates and events) of the ledger at `path`, verified, read
    under a shared lock."""
    p = Path(path)
    if not p.exists():
        _refuse("ledger_missing", f"{p} does not exist")
    return parse_records(_read_shared(p))


# ─────────────────────────── field validation ───────────────────────────

def _nonblank(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


_RUN_ID = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+(Z|[+-][0-9]{2}:[0-9]{2})")


def _valid_run_id(v) -> bool:
    """A tz-aware ISO timestamp in the one shape the census writes (`T` separator, explicit offset): fromisoformat alone
    accepts any single separator character (NUL, `/`, a space)."""
    if not isinstance(v, str) or not _RUN_ID.fullmatch(v):
        return False
    try:
        dt.datetime.fromisoformat(v)          # a real date/time; the regex above guarantees the explicit offset
    except ValueError:
        return False
    return True


def _check_relpath(p) -> bool:
    return (isinstance(p, str) and bool(p) and not p.startswith("/") and "\\" not in p
            and ".." not in p.split("/") and "" not in p.split("/"))


def _clean_text(s: str) -> str:
    """NFKC-normalise and drop format/control/private/unassigned characters (zero-width joiners, soft hyphens, BOM,
    word joiner...), then strip: what a human reads, not what the bytes are."""
    s = unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in s if unicodedata.category(ch) not in ("Cf", "Cc", "Co", "Cn")).strip()


def _typed_hashes(wh):
    if wh is None:
        return {}
    if not isinstance(wh, dict):
        _refuse("bad_writer_hashes", "writer_hashes must be a mapping of relative path -> lower-case sha256")
    for p, h in wh.items():
        if not _check_relpath(p) or not isinstance(h, str) or not _SHA256.fullmatch(h):
            _refuse("bad_writer_hashes", f"bad writer hash entry {p!r}: need a relative path and 64 lower-case hex")
    return dict(wh)


def hash_writer_files(paths, repo=None, ref=None) -> dict[str, str]:
    """sha256 of each writer file: the working tree, or the committed blob at `ref` (`git show ref:path`) —
    certify the commit that was measured, not whatever the working tree holds now."""
    repo = Path(repo) if repo is not None else Path(ac.ROOT)
    out = {}
    for p in paths:
        if not _check_relpath(p):
            _refuse("bad_writer_hashes", f"{p!r} is not a repo-relative path")
        if ref is None:
            f = repo / p
            if not f.is_file():
                _refuse("bad_writer_hashes", f"{p}: not a file in {repo}")
            blob = f.read_bytes()
        else:
            r = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{p}"], capture_output=True)
            if r.returncode != 0:
                _refuse("bad_writer_hashes", f"{p}: not readable at {ref} in {repo}")
            blob = r.stdout
        out[p] = hashlib.sha256(blob).hexdigest()
    return dict(sorted(out.items()))


def _resolve_writer_hashes(typed, files, repo, ref):
    """(hashes, verified). Hashes computed here from `files` (and from the typed paths when a repo or ref is given)
    are VERIFIED; a typed hash with nothing to check it against is kept but `verified` is False. None when there are
    no hashes at all."""
    typed = _typed_hashes(typed)
    if files is None:
        files = []
    if isinstance(files, (str, bytes)) or not isinstance(files, (list, tuple)):
        _refuse("bad_writer_hashes", "writer_files must be a list of repo-relative paths")
    check_typed = repo is not None or ref is not None
    paths = sorted(set(files) | (set(typed) if check_typed else set()))
    computed = hash_writer_files(paths, repo, ref) if paths else {}
    for p, h in typed.items():
        if p in computed and computed[p] != h:
            _refuse("writer_hash_mismatch", f"{p}: the typed hash {h[:12]}.. is not the file's ({computed[p][:12]}..)")
    out = dict(typed)
    out.update({p: computed[p] for p in files})
    if not out:
        return {}, None
    verified = all(p in computed for p in out)
    return dict(sorted(out.items())), verified


def _writer_evidence(out, verified, reason, verdict, na_measured, kind, has_writer):
    """The reason a PASS may have no writer file must be documented, and refused outright when the census says the
    asset has a writer; hashes that were not verified count as missing for a PASS (or a measured N/A)."""
    if reason is not None and not isinstance(reason, str):
        _refuse("bad_writer_hashes", "writer_hashes_reason, when given, must be text")
    reason = reason.strip() if _nonblank(reason) else None
    if reason is not None:
        if kind == "gate" and has_writer is True:
            _refuse("writer_reason_refused", "the census record says this asset has a writer (has_writer=true): "
                                             "a reason for having no writer file is refused")
        if not (kind == "gate" and has_writer is False) and reason not in WRITER_REASONS:
            _refuse("writer_reason_refused", f"the census record does not say has_writer=false, so the reason must be "
                                             f"one of {WRITER_REASONS}")
    elif verdict == "PASS" or na_measured:
        if not out:
            _refuse("missing_writer_hashes",
                    "a PASS (or measured N/A) with no writer file hashes can never go stale on a writer change: give "
                    "the hashes, or writer_hashes_reason saying why the asset has no writer file")
        if not verified:
            _refuse("unverified_writer_hashes",
                    "the writer hashes were typed and not verified: pass writer_files (computed here) or a repo/ref "
                    "to verify them against; unverified hashes count as missing for a PASS")
    return reason


def _upstream_ids(ids, own_key: str) -> list[str]:
    if ids is None:
        ids = ()
    if isinstance(ids, (str, bytes)) or not isinstance(ids, (list, tuple, set, frozenset)):
        _refuse("bad_upstream", "upstream_cert_ids must be a list of cert ids")
    out = set()
    for u in ids:
        m = _CERT_ID.fullmatch(u) if isinstance(u, str) else None
        if m is None:
            _refuse("bad_upstream", f"{u!r} is not a cert id (<asset>|<gate|addition>|<criterion>@<generation>)")
        if cert_key_of(m.group(1), m.group(2), m.group(3)) == own_key:
            _refuse("upstream_self", f"{u} is this certificate's own key")
        out.add(u)
    return sorted(out)


# ─────────────────────────── the census gate ───────────────────────────

def _git(repo, *args):
    """CompletedProcess of `git -C repo <args>`, or None when git cannot be run."""
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    except OSError:
        return None


def _blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()           # git's object id of a blob


def _trusted_root_rel() -> str:
    r = TRUSTED_CENSUS_ROOT
    if (not isinstance(r, str) or not r or r.startswith("/") or not r.endswith("/") or "\\" in r
            or ".." in r.split("/")):
        _refuse("census_untrusted", f"TRUSTED_CENSUS_ROOT {r!r} is not a repo-relative directory ending in '/'")
    return r


def _census_git_state(root: str, rel: str, blob: bytes) -> str:
    """`committed` (the work-tree bytes are the HEAD blob) or `staged` (in the index, same bytes, not at HEAD);
    otherwise the census is not tracked (`census_untracked`) or differs from what git holds (`census_modified`)."""
    r = _git(root, "ls-files", "-s", "--", rel)
    if r is None or r.returncode != 0:
        _refuse("census_untracked", f"git could not be asked about {rel}")
    entries = [ln.partition("\t")[0].split() for ln in r.stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
    stage0 = [e for e in entries if len(e) == 3 and e[2] == "0"]
    if len(stage0) != 1:
        _refuse("census_untracked", f"{rel} is neither committed nor staged in git: a census a cert cites must be "
                                    "committed under the trusted root (git add it for the same PR)")
    idx_sha = stage0[0][1]
    if idx_sha != _blob_sha(blob):
        _refuse("census_modified", f"{rel} differs from the version git holds: commit or stage the census as it is")
    h = _git(root, "ls-tree", "HEAD", "--", rel)
    head = h.stdout.decode("utf-8", "replace").partition("\t")[0].split() if h is not None and h.returncode == 0 else []
    return "committed" if len(head) == 3 and head[2] == idx_sha else "staged"


def _load_census(census_path, census) -> _CensusSource:
    """The census, read from a FILE committed under TRUSTED_CENSUS_ROOT (symlinks resolved first; tracked or staged in
    git). Its sha256 is of the WHOLE file's bytes. A dict is accepted only together with its source file and must
    equal what the file holds."""
    if census_path is None:
        if census is not None:
            _refuse("census_unsourced", "a census dict without its source file cannot be hashed: a census is read "
                                        "from a file committed under the trusted census root")
        _refuse("census_required", "a gate verdict is read from the census record, not asserted: supply the census "
                                   "file (--census) for this asset and criterion")
    if not isinstance(census_path, (str, os.PathLike)):
        _refuse("bad_census", "the census path must be a path")
    root = os.path.realpath(ac.ROOT)
    troot_rel = _trusted_root_rel()
    troot = os.path.realpath(os.path.join(root, troot_rel))
    rp = os.path.realpath(census_path)
    try:
        inside = rp != troot and os.path.commonpath([rp, troot]) == troot
    except ValueError:
        inside = False
    if not inside:
        _refuse("census_untrusted", f"{rp} is not under the trusted census root {troot_rel} of this repository: a "
                                    "census written elsewhere could have been made up")
    try:
        if not os.path.isfile(rp):
            _refuse("bad_census", f"{rp} is not a file")
        blob = Path(rp).read_bytes()
    except OSError as e:
        _refuse("bad_census", f"{rp} cannot be read ({e})")
    rel = os.path.relpath(rp, root).replace(os.sep, "/")
    state = _census_git_state(root, rel, blob)
    try:
        obj = strict_json_loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        _refuse("bad_census", f"{rel} is not strict JSON ({e})")
    if not isinstance(obj, dict):
        _refuse("bad_census", "the census must be a JSON object")
    if census is not None and census != obj:
        _refuse("census_mismatch", "the supplied census dict is not what its source file holds")
    return _CensusSource(obj, _sha(blob), rel, state)


def _select_layer(obj: dict, layer: str) -> dict:
    """The census object of `layer`: the real multi-layer asset_census.json ({"L0": {...}, "rollup": ...}) is indexed
    by the layer key (`rollup`, `scope` are ignored), the flat single-layer form is the object itself."""
    if "assets" in obj and "generated" in obj:
        return obj
    c = obj.get(layer)
    if not isinstance(c, dict):
        _refuse("census_mismatch", f"the census file has no {layer!r} layer object (keys: {sorted(map(str, obj))[:8]})")
    return c


def _check_census_head(c: dict, layer: str, run_id: str, need_stamp: bool):
    """Run id, layer and (gates) the stamp the census tool put on its head: registry revision + fingerprint (must be
    the current registry) and tool_commit. A census without them is `census_unbound`."""
    if c.get("generated") != run_id or not _valid_run_id(c.get("generated")):
        _refuse("census_run_id_mismatch", f"evidence.census_run_id {run_id!r} is not the census's own `generated` "
                                          f"{c.get('generated')!r}")
    if c.get("layer") != layer:
        _refuse("census_mismatch", f"census layer {c.get('layer')!r} is not {layer!r}")
    if not need_stamp:
        return None
    rr, rf, tc = c.get("registry_revision"), c.get("registry_fingerprint"), c.get("tool_commit")
    if rr is None or rf is None or tc is None:
        _refuse("census_unbound", "the census head carries no registry_revision / registry_fingerprint / tool_commit "
                                  "stamp: it is not provably the registry this record is stamped with")
    if not isinstance(tc, str) or not re.fullmatch(r"[0-9a-f]{7,64}", tc):
        _refuse("census_unbound", f"tool_commit {tc!r} is not a git commit id")
    if (isinstance(rr, bool) or not isinstance(rr, int) or rr != ac.REGISTRY_REVISION
            or not isinstance(rf, str) or rf != ac.registry_fingerprint()):
        _refuse("census_registry_mismatch", f"the census ran under registry revision {rr!r} / fingerprint "
                                            f"{str(rf)[:12]!r}.., not the current {ac.REGISTRY_REVISION} / "
                                            f"{ac.registry_fingerprint()[:12]}..")
    return tc


def _census_record_and_cell(c: dict, asset: str, crit: str):
    recs = [a for a in c.get("assets") or [] if isinstance(a, dict) and a.get("asset_id") == asset]
    if len(recs) != 1:
        _refuse("census_mismatch", f"census holds {len(recs)} records for {asset} (need exactly one)")
    ms = recs[0].get("measurements")
    if not isinstance(ms, dict):
        _refuse("census_mismatch", f"census record for {asset} has no measurements")
    cell = ms.get(crit)
    if cell is not None and not isinstance(cell, dict):
        _refuse("census_mismatch", f"census cell {crit} is not an object")
    return recs[0], cell


def _allowed_writer_paths(record: dict) -> set:
    """Repo-relative paths of the asset's writer files, as the census itself lists them (names relative to writers/ or
    the sidecar root), resolved by asset_census's own `_writer_path`."""
    names = record.get("writer_files")
    out = set()
    if isinstance(names, list):
        root = os.path.realpath(ac.ROOT)
        for n in names:
            if _check_relpath(n):
                rel = os.path.relpath(os.path.realpath(str(ac._writer_path(n))), root)
                if not rel.startswith(".."):
                    out.add(rel.replace(os.sep, "/"))
    return out


def _writer_commit_time(repo, ref, path):
    """Commit time of the last commit that touched `path` at `ref` (HEAD when no ref; then an uncommitted change to
    the file is undeterminable), or None."""
    r = _git(repo, "log", "-1", "--format=%cI", ref or "HEAD", "--", path)
    if r is None or r.returncode != 0 or not r.stdout.strip():
        return None
    if ref is None:
        st = _git(repo, "status", "--porcelain", "--", path)
        if st is None or st.returncode != 0 or st.stdout.strip():
            return None
    try:
        t = dt.datetime.fromisoformat(r.stdout.decode().strip())
    except ValueError:
        return None
    return t if t.tzinfo is not None else None


def _norm_fact(k, v):
    if k == "columns" and isinstance(v, (list, tuple, set, frozenset)) and all(isinstance(c, str) for c in v):
        return sorted(c.strip() for c in v)
    return v


def _facts_from_census(record: dict, caller_facts):
    cf = ac.facts_for_asset(record)
    if caller_facts:
        for k, v in caller_facts.items():
            if k not in cf or _norm_fact(k, v) != _norm_fact(k, cf[k]):
                _refuse("facts_conflict", f"caller fact {k}={v!r} is not what the census record carries "
                                          f"({cf.get(k, 'not carried')!r}): applicability facts come from the census")
    return cf


# ─────────────────────────── N/A: computed, never typed ───────────────────────────

def _computed_na(criterion, layer, facts, na_rule_id, cell):
    """The `na` block for a registry-computed N/A, or CertificationRefused. Two computations exist: a cause the
    census cell measured (the cell says N/A with that cause) and fact-disproved applicability (recomputed here from
    the census record's facts; only where the census holds no cell, since a measurement outranks any applicability
    rule). Either way the rule id must be DECLARED in NA_RULE_DECISIONS."""
    try:
        ac.validate_na_rule_decisions()
    except ValueError as e:
        _refuse("na_rules_invalid", str(e))
    if cell is not None and cell.get("v") == "N/A":
        cause = cell.get("cause")
        if not isinstance(cause, str) or cause not in ac.NA_CAUSES.get(criterion, ()):
            _refuse("na_not_computed", f"the census cell says N/A with cause {cause!r}, which is not a registered N/A "
                                       f"cause of {criterion}")
        rid = f"{criterion}#measured:{cause}"
        if na_rule_id is not None and na_rule_id != rid:
            _refuse("na_not_computed", f"rule id {na_rule_id!r} is not the one the census cell's cause yields ({rid!r})")
        na = dict(rule_id=rid, basis="measured_cause", cause=cause, facts=None)
    else:
        # (a census cell that is not N/A never reaches here: build_record refuses a caller N/A over a measured record)
        if not _nonblank(na_rule_id):
            _refuse("na_not_computed", "an N/A needs the rule id the registry computes for it; none was given")
        crit, sep, rule = na_rule_id.partition("#")
        if not sep or crit != criterion:
            _refuse("na_not_computed", f"rule id {na_rule_id!r} is not a rule of {criterion}")
        if rule in ("columns_any", "asset_kinds"):
            ap = ac.criterion_applicability(criterion, layer, facts)
            if ap["state"] != "NOT_APPLICABLE" or ap["rule_id"] != na_rule_id:
                _refuse("na_not_computed",
                        f"the registry computes {ap['state']} (rule {ap['rule_id']!r}) for the census record's facts, "
                        f"not NOT_APPLICABLE under {na_rule_id!r}: {ap['reason']}")
            used = {k: facts[k] for k in ("columns", "columns_known", "asset_kind") if k in facts}
            if "columns" in used:
                used["columns"] = sorted(used["columns"])
            na = dict(rule_id=na_rule_id, basis="applicability_facts", cause=None, facts=used)
        elif rule.startswith("measured:"):
            _refuse("na_not_computed", f"a measured N/A needs the census cell that measured N/A with cause "
                                       f"{rule[len('measured:'):]!r}; the census holds no such cell")
        else:
            _refuse("na_not_computed", f"{na_rule_id!r} is not a rule form this inspector issues")
    if na["rule_id"] not in ac.NA_RULE_DECISIONS:
        _refuse("na_not_computed", f"N/A rule undecided (N-22): {na['rule_id']!r} is not declared in NA_RULE_DECISIONS, "
                                   "so the rollup reads this NO_DETECTOR, not N/A")
    return dict(rule_id=na["rule_id"], decision_id=ac.NA_RULE_DECISIONS[na["rule_id"]], basis=na["basis"],
                cause=na["cause"], facts=na["facts"])


# ─────────────────────────── the record ───────────────────────────

def build_record(*, asset, layer, criterion, evidence, verified_by, verdict=None, kind="gate", gate=None, detector=None,
                 criterion_version=None, facts=None, na_rule_id=None, census=None, census_path=None,
                 job_image_tag=None, writer_hashes=None, writer_files=None, writer_repo=None,
                 writer_ref=None, writer_hashes_reason=None, upstream_cert_ids=(), semantic_fingerprint=None,
                 basis=None, inconclusive=False, verified_on=None) -> dict:
    """Validate everything that needs no ledger and return the record without cert_id/generation/prev_sha256. Raises
    CertificationRefused; has no side effect (it reads the census file and the writer files)."""
    if not isinstance(kind, str) or kind not in KINDS:
        _refuse("bad_kind", f"kind must be one of {KINDS}")
    if not isinstance(layer, str) or layer not in ac.LAYERS:
        _refuse("bad_layer", f"layer must be one of {sorted(ac.LAYERS)}")
    if not isinstance(asset, str) or not _ASSET.fullmatch(asset):
        _refuse("bad_asset", f"{asset!r} is not an asset id")
    if not asset.startswith(ac.LAYERS[layer]["prefix"]):
        _refuse("asset_layer_mismatch", f"{asset} is not a {layer} asset (prefix {ac.LAYERS[layer]['prefix']!r})")
    if facts is not None:
        try:
            ok = isinstance(facts, dict)
            if ok:
                ok = _max_depth(json.dumps(facts, allow_nan=False)) <= MAX_JSON_DEPTH
        except (TypeError, ValueError, RecursionError):
            ok = False
        if not ok:
            _refuse("bad_facts", "facts must be a JSON-serialisable mapping (columns / asset_kind) or None")
    if verdict is None and kind == "gate":
        pass                                          # a gate verdict is read from the census cell below
    elif not isinstance(verdict, str) or verdict not in VERDICTS:
        _refuse("bad_verdict", f"verdict must be one of {VERDICTS}" + (" (a gate may omit it: the census supplies it)"
                                                                       if kind == "gate" else ""))
    if not _nonblank(verified_by):
        _refuse("bad_verified_by", "verified_by is required (who ran the detector)")
    if job_image_tag is not None and not _nonblank(job_image_tag):
        _refuse("bad_job_image_tag", "job_image_tag is null when unknown, never blank")
    if verified_on is not None and not _valid_run_id(verified_on):
        _refuse("bad_verified_on", "verified_on, when given, is a tz-aware ISO timestamp")
    if not isinstance(inconclusive, bool):
        _refuse("bad_request", "inconclusive must be a boolean")

    # criterion binding: the REGISTRY supplies gate, detector and revision for a gate record
    if kind == "gate":
        entry = ac.CRITERION_REGISTRY.get(criterion) if isinstance(criterion, str) else None
        if entry is None:
            _refuse("unregistered_criterion", f"{criterion!r} is not in CRITERION_REGISTRY")
        if gate is not None and gate != entry["gate"]:
            _refuse("gate_mismatch", f"{criterion} belongs to gate {entry['gate']!r}, not {gate!r}")
        if layer not in entry["layers"]:
            _refuse("out_of_layer", f"{criterion} is not defined for {layer}")
        if detector is not None and detector != entry["detector"]:
            _refuse("detector_mismatch", f"the registry binds {criterion} to {entry['detector']!r}, not {detector!r}")
        if criterion_version is not None and (isinstance(criterion_version, bool)
                                              or criterion_version != entry["revision"]):
            _refuse("bad_criterion_version", f"{criterion} is at revision {entry['revision']}, not {criterion_version!r}")
        det, gate_name = entry["detector"], entry["gate"]
        crit_version, reg_rev, reg_fp = entry["revision"], ac.REGISTRY_REVISION, ac.registry_fingerprint()
    else:
        if isinstance(criterion, str) and not criterion.isascii():
            _refuse("bad_criterion_id", f"{criterion!r} contains non-ASCII characters (look-alikes of registered ids)")
        if (not isinstance(criterion, str) or not _ADDITION.fullmatch(criterion)
                or _clean_text(criterion).casefold() in {_clean_text(k).casefold() for k in ac.CRITERION_REGISTRY}):
            _refuse("bad_criterion_id", f"{criterion!r} is not a well-formed addition id (and must not shadow a "
                                        "registered criterion, by case or by Unicode form)")
        if gate is not None:
            _refuse("gate_mismatch", "an addition belongs to no gate")
        if isinstance(criterion_version, bool) or not isinstance(criterion_version, int) or criterion_version < 1:
            _refuse("bad_criterion_version", "an addition record carries its brief's revision as an int >= 1")
        if detector is not None and not isinstance(detector, str):
            _refuse("bad_detector", "an addition's detector is text or absent")
        cleaned = _clean_text(detector) if isinstance(detector, str) else ""
        if not any(ch.isalnum() for ch in cleaned) or cleaned.casefold() == "none":
            det = "NONE"
        elif not cleaned.isascii():
            _refuse("bad_detector", f"detector {detector!r} is not ASCII (a look-alike of NONE or of a real detector)")
        else:
            det = cleaned
        gate_name, crit_version, reg_rev, reg_fp = None, criterion_version, None, None

    # R1 (on what the caller said; repeated below on the verdict actually derived): a NONE detector can only
    # honestly be recorded as NO_DETECTOR
    if det == "NONE" and verdict is not None and verdict != "NO_DETECTOR":
        _refuse("detector_none", f"{criterion} has detector NONE: nothing measured it, so {verdict} is refused "
                                 "(only NO_DETECTOR can be recorded)")

    # R2: every record names the census run it rests on
    if not isinstance(evidence, dict) or not _valid_run_id(evidence.get("census_run_id")):
        _refuse("no_census_run_id", "evidence must carry census_run_id: the census's tz-aware ISO `generated` "
                                    "timestamp (a record without a run id is not a record)")
    run_id = evidence["census_run_id"]
    unknown = sorted(repr(k) for k in set(evidence) - set(CALLER_EVIDENCE_KEYS))
    if unknown or any(not isinstance(v, str) for v in evidence.values()):
        _refuse("bad_evidence", f"evidence keys must be {CALLER_EVIDENCE_KEYS} with text values; "
                                f"{WRITER_EVIDENCE_KEYS} are set by this writer from the census file it read, never "
                                f"typed (got {unknown or 'non-text'})")

    # R8: the census gate. A gate reads its verdict from the census cell; an addition may cite a census for its run id
    src, meas, record, tool_commit, head = None, None, None, None, None
    if kind == "gate" or census_path is not None or census is not None:
        src = _load_census(census_path, census)
        head = _select_layer(src.obj, layer)
        tool_commit = _check_census_head(head, layer, run_id, need_stamp=(kind == "gate"))
    cfacts = {}
    transitive_only = False
    if kind == "gate":
        record, meas = _census_record_and_cell(head, asset, criterion)
        cfacts = _facts_from_census(record, facts)
        if meas is not None and (not isinstance(meas.get("v"), str) or meas["v"] not in VERDICTS):
            _refuse("census_mismatch", f"the census cell {criterion} for {asset} reads {meas.get('v')!r}, which is not "
                                       f"a recordable verdict {VERDICTS}")
        if meas is not None:
            if verdict is not None and verdict != meas["v"]:
                if verdict == "N/A":
                    _refuse("na_not_computed", f"the census measured {meas['v']!r} for {asset} {criterion}; a "
                                               "measured record takes precedence over any N/A")
                _refuse("census_mismatch", f"the census measured {meas['v']!r} for {asset} {criterion}, not {verdict!r}")
            if na_rule_id is not None and meas["v"] != "N/A":
                _refuse("na_not_computed", f"an N/A rule id was given but the census measured {meas['v']!r}")
            verdict = meas["v"]
            if basis is not None and basis != meas.get("basis"):
                _refuse("census_mismatch", f"basis {basis!r} disagrees with the census cell ({meas.get('basis')!r})")
            basis = meas.get("basis")
            inconclusive = inconclusive or bool(meas.get("inconclusive"))
            transitive_only = meas.get("transitive_only") is True
        else:
            if not (verdict == "N/A" or (verdict is None and na_rule_id is not None)):
                _refuse("census_cell_missing", f"the census holds no cell {criterion} for {asset}: a gate verdict is "
                                               "read from the census, never asserted (only an applicability N/A the "
                                               "registry computes needs no cell)")
            if basis is not None:
                _refuse("bad_basis", "a basis is taken from the census cell; there is none to take it from")
            verdict = "N/A"                                  # an applicability N/A: confirmed by the registry below
        if det == "NONE" and verdict != "NO_DETECTOR":
            _refuse("detector_none", f"{criterion} has detector NONE: nothing measured it, so {verdict} is refused "
                                     "(only NO_DETECTOR can be recorded)")
    elif basis is not None:
        _refuse("bad_basis", "an addition has no census cell to take a basis from: a typed basis is refused")
    if basis is not None and basis != _DECLARATION:
        _refuse("bad_basis", f"unrecognised basis {basis!r} (the only defined basis is {_DECLARATION!r}, case-exact)")
    if verdict == "PASS" and basis == _DECLARATION:
        kinds = DECLARATION_BASED.get(criterion)
        if kinds is None or record.get("asset_kind") not in kinds:
            _refuse("bad_basis", f"the registry defines no PASS by declaration for {criterion} on an asset of kind "
                                 f"{record.get('asset_kind')!r}")

    # R5: what the census rollup itself would not honour
    if kind == "gate" and verdict == "PASS" and (criterion.startswith("Null.") or criterion == "Narr.fidelity_test"):
        _refuse("capped_verdict", f"{criterion} is capped at PARTIAL (Null: never PASS alone; fidelity_test: "
                                  "structural only)")
    if inconclusive and verdict in ("PASS", "PARTIAL"):
        _refuse("inconclusive", "an INCONCLUSIVE measurement established nothing: it cannot be PASS or PARTIAL")
    if kind == "gate" and verdict == "PASS":
        if ac.criterion_applicability(criterion, layer, cfacts)["state"] == "NOT_APPLICABLE":
            _refuse("not_applicable_pass", "the census record's facts disprove this criterion's applicability: a "
                                           "measured PASS contradicts the registry")

    # R3: N/A is computed, never typed
    na = None
    if verdict == "N/A":
        if kind != "gate":
            _refuse("na_not_computed", "an addition has no registry applicability rule: its N/A cannot be computed")
        na = _computed_na(criterion, layer, cfacts, na_rule_id, meas)

    # R6: what lets the record go stale
    na_measured = na is not None and na["basis"] == "measured_cause"
    if semantic_fingerprint is not None and (not isinstance(semantic_fingerprint, str)
                                             or not _SHA256.fullmatch(semantic_fingerprint)):
        _refuse("bad_fingerprint", "semantic_fingerprint must be 64 lower-case hex (sha256)")
    if semantic_fingerprint is None and (verdict == "PASS" or na_measured):
        _refuse("missing_fingerprint", "a PASS (or measured N/A) read rows: without a semantic fingerprint a "
                                       "change to those rows could never invalidate it")
    wh, wh_verified = _resolve_writer_hashes(writer_hashes, writer_files, writer_repo, writer_ref)
    if kind == "gate" and wh:
        stray = sorted(set(wh) - _allowed_writer_paths(record))
        if stray:
            _refuse("writer_file_unbound", f"{stray} is not a writer file of {asset} according to the census record "
                                           "(its writer_files): a hash of some other file proves nothing about this asset")
        required = _allowed_writer_paths(record)
        if record.get("has_writer") is True and (verdict == "PASS" or na_measured) and set(wh) != required:
            _refuse("writer_files_incomplete", f"the census lists {sorted(required)} as the writer files of {asset} "
                                               f"(has_writer=true) and only {sorted(wh)} were hashed: a PASS must rest "
                                               "on ALL of them")
        if wh_verified:
            repo = writer_repo if writer_repo is not None else ac.ROOT
            gen_t = dt.datetime.fromisoformat(run_id)
            for pth in wh:
                t = _writer_commit_time(repo, writer_ref, pth)
                if t is None:
                    _refuse("writer_time_unknown", f"the commit time of {pth} (at {writer_ref or 'HEAD'}) cannot be "
                                                   "determined (untracked, uncommitted change, or no git): a census "
                                                   "cannot be shown to postdate the writer")
                if gen_t < t:
                    _refuse("census_older_than_writer", f"the census ({run_id}) is older than the last commit of "
                                                        f"{pth} ({t.isoformat()}): it measured an earlier writer")
    has_writer = record.get("has_writer") if record is not None and isinstance(record.get("has_writer"), bool) else None
    wh_reason = _writer_evidence(wh, wh_verified, writer_hashes_reason, verdict, na_measured, kind, has_writer)

    cert_key = cert_key_of(asset, kind, criterion)
    ups = _upstream_ids(upstream_cert_ids, cert_key)
    ev = dict(evidence)
    if src is not None:
        ev["census_file"], ev["census_sha256"], ev["census_git"] = src.path, src.sha256, src.git
        if tool_commit is not None:
            ev["census_tool_commit"] = tool_commit
    rec = dict(
        asset=asset, layer=layer, kind=kind, gate=gate_name, criterion=criterion, criterion_version=crit_version,
        registry_revision=reg_rev, registry_fingerprint=reg_fp, detector=det,
        verdict=verdict, basis=basis, na=na, inconclusive=bool(inconclusive), transitive_only=transitive_only,
        evidence=ev, cross_checked=(kind == "gate"),
        job_image_tag=job_image_tag.strip() if job_image_tag else None, writer_hashes=wh,
        writer_hashes_verified=wh_verified, writer_hashes_reason=wh_reason, upstream_cert_ids=ups,
        semantic_fingerprint=semantic_fingerprint, cert_key=cert_key, verified_by=verified_by.strip(),
        verified_on=verified_on or dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        record_version=RECORD_VERSION)
    try:
        json.dumps(rec, allow_nan=False)
    except (TypeError, ValueError) as e:
        _refuse("bad_record", f"the record cannot be serialised as strict JSON ({e})")
    return rec


def _identity(rec: dict) -> str:
    return json.dumps({k: rec.get(k) for k in CURRENCY_FIELDS}, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _check_upstream(rec: dict, by_key: dict) -> None:
    for u in rec["upstream_cert_ids"]:
        m = _CERT_ID.fullmatch(u)
        key, gen = cert_key_of(m.group(1), m.group(2), m.group(3)), int(m.group(4))
        recs = by_key.get(key)
        if not recs or gen > len(recs):
            _refuse("upstream_unknown", f"{u} is not in the ledger")
        if gen != len(recs):
            _refuse("upstream_stale", f"{u} is generation {gen}, but the ledger's latest for that key is {len(recs)}: "
                                      "a certificate resting on it would be stale at birth")
        if rec["verdict"] == "PASS" and recs[-1]["verdict"] not in ("PASS", "N/A"):
            _refuse("upstream_not_passing", f"{u} reads {recs[-1]['verdict']}: a PASS cannot rest on it")


def _open_ledger(path: Path, init: bool, precheck):
    """(file object, created_new). Never follows a symlink at `path` (a link, even a dangling one, is refused; the
    open itself refuses to follow as well, so a link swapped in after the check cannot redirect the write). A ledger
    that does not exist is created only under `init`, and only after the request was validated against an empty
    ledger, so a refused request never creates (nor later has to delete) a file."""
    if os.path.islink(path):
        _refuse("bad_ledger_path", f"{path} is a symlink: the ledger path is never followed")
    base = os.O_RDWR | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    for _ in range(2):
        try:
            return os.fdopen(os.open(path, base), "a+b"), False
        except FileNotFoundError:
            if not init:
                _refuse("ledger_missing", f"{path} does not exist (pass init=True / --init to create it)")
        except OSError as e:
            if e.errno in (errno.ELOOP, errno.EISDIR):
                _refuse("bad_ledger_path", f"{path} is not a regular file ({os.strerror(e.errno)})")
            raise
        precheck()                                     # validated against an EMPTY ledger before anything is created
        try:
            return os.fdopen(os.open(path, base | os.O_CREAT | os.O_EXCL, 0o644), "a+b"), True
        except FileExistsError:
            continue                                   # lost a creation race (or a link appeared): look again
        except FileNotFoundError:
            _refuse("ledger_missing", f"{path}: its directory does not exist")
        except OSError as e:
            if e.errno in (errno.ELOOP, errno.EISDIR):
                _refuse("bad_ledger_path", f"{path} is not a regular file ({os.strerror(e.errno)})")
            raise
    _refuse("bad_ledger_path", f"{path} could not be opened as a regular file")


def _locked_append(path: Path, init: bool, precheck, build):
    """THE write path: every line the ledger ever receives goes through here. Opens `path` (never following a symlink;
    created only under `init` and only after `precheck()` accepted an empty ledger), takes the exclusive lock, reads and
    VERIFIES the whole ledger (chain, seq, generations; torn => `torn_ledger`), calls `build(parsed) -> (records,
    outcome)`, fills `seq` and `prev_sha256` into each record in order, serialises each with `_dump`, appends them in
    ONE write to the append-only descriptor, fsyncs, and returns `(outcome, written_records)`. It never edits an
    existing byte. A refused request leaves the ledger bytes identical; only a file THIS call created, and only while
    still empty, is removed."""
    f, created_new = _open_ledger(path, init, precheck)
    try:
        with f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            data = f.read()
            schema_line = _dump({"asset": "_schema", "_doc": SCHEMA_DOC})
            fresh = not data
            if fresh and not init:
                _refuse("bad_ledger", f"{path} is empty (no `_schema` row); pass init=True / --init to initialise it")
            parsed = _Parsed({}, [], _sha(schema_line), 0) if fresh else _parse_full(data)
            records, outcome = build(parsed)
            if not records:
                return outcome, []
            prev, n, buf, written = parsed.prev, parsed.n, b"", []
            for r in records:
                n += 1
                full = dict(r, seq=n, prev_sha256=prev)
                try:
                    line = _dump(full)
                except (TypeError, ValueError, RecursionError) as e:
                    _refuse("bad_record", f"a record cannot be serialised as strict JSON ({e})")
                buf += line + b"\n"
                prev = _sha(line)
                written.append(full)
            if fresh:
                buf = schema_line + b"\n" + buf
            elif not data.endswith(b"\n"):
                buf = b"\n" + buf
            f.write(buf)                   # one write of fully serialised lines, to an append-only descriptor
            f.flush()
            os.fsync(f.fileno())
            return outcome, written
    except BaseException:
        if created_new:                    # only a file THIS call created, and only while it is still empty
            try:
                if not os.path.islink(path) and os.stat(path).st_size == 0:
                    os.unlink(path)
            except OSError:
                pass
        raise


def _appendable(r, allowed) -> None:
    """Structural check of one record offered to `append_records` (nothing about certification semantics)."""
    if not isinstance(r, dict):
        _refuse("bad_record", "a ledger record must be a JSON object")
    if r.get("asset") == "_schema":
        _refuse("bad_record", "the `_schema` row is written once, by the writer")
    if "seq" in r or "prev_sha256" in r:
        _refuse("bad_record", "seq and prev_sha256 are filled in by the writer, never given")
    if r.get("kind") in KINDS or r.get("type") in KINDS or any(k in r for k in _EVENT_ONLY_FORBIDDEN):
        _refuse("bad_record", "certificates (kind/type gate or addition, anything with a cert_key / cert_id / generation) "
                              "go only through write_certification, which makes every check; append_records takes "
                              "events only")
    if not _is_event_line(r, allowed):
        _refuse("bad_record", f"a record is an event: a `type` in {tuple(allowed)}, and no certificate-only field "
                              "(cert_key, cert_id, generation, a certificate verdict or kind)")


def append_records(ledger_path, records, allowed_types=EVENT_TYPES, *, init: bool = False) -> int:
    """PUBLIC. Append `records` (a list of dicts) to the ledger as the next lines and return how many were written.
    Takes the exclusive lock, verifies the whole ledger first (chain, seq, generations; a torn ledger is refused
    `torn_ledger`; a symlink or directory at the path `bad_ledger_path`; a missing ledger `ledger_missing` unless
    `init`), fills `seq` and `prev_sha256` for each record (giving either is refused), serialises with the one canonical
    serialisation, appends all of them in a single write, and never edits an existing line. A record is an EVENT: it
    must carry a `type` in `allowed_types` (default and maximum: EVENT_TYPES = invalidation, watermark, epoch_reset, the
    only types E5.5's reader dispatches on; a type outside EVENT_TYPES is refused even if the caller allows it) and no
    certificate-only field (cert_key, cert_id, generation, a certificate verdict, kind gate/addition). Certificates are
    REFUSED here: they go only through `write_certification`, which does every certification check. All-or-nothing: if
    any record is refused nothing is written. An empty list writes nothing and returns 0 without touching the ledger.
    `write_certification` uses the same path."""
    allowed = tuple(allowed_types)
    if not allowed or any(t not in EVENT_TYPES for t in allowed):
        _refuse("bad_record", f"allowed_types must be a non-empty subset of EVENT_TYPES {EVENT_TYPES}: a line type the "
                              "reader does not know would brick the append-only ledger")
    recs = list(records)
    for r in recs:
        _appendable(r, allowed)
    if not recs:
        return 0

    def check(parsed: _Parsed):
        return recs, None

    _, written = _locked_append(resolve_ledger_path(ledger_path), init, lambda: check(_Parsed({}, [], "", 0)), check)
    return len(written)


def write_certification(*, ledger_path=None, init: bool = False, **fields) -> CertResult:
    """Validate, then append one record (or report the identical latest generation). See build_record for the
    fields. The ledger is never rewritten: it goes through `_locked_append` (exclusive lock; the read the generation
    number, the hash chain and the idempotence check depend on is under the same lock)."""
    try:
        rec = build_record(**fields)
    except CertificationRefused:
        raise
    except (TypeError, ValueError, AttributeError, KeyError, OverflowError, RecursionError) as e:
        _refuse("bad_request", f"the request is malformed ({type(e).__name__}: {e})")
    path = resolve_ledger_path(ledger_path)

    def decide(parsed: _Parsed):
        _check_upstream(rec, parsed.by_key)
        cf, csha = rec["evidence"].get("census_file"), rec["evidence"].get("census_sha256")
        if cf is not None:
            for old in (c for recs in parsed.by_key.values() for c in recs):
                oe = old.get("evidence") if isinstance(old.get("evidence"), dict) else {}
                if oe.get("census_file") == cf and oe.get("census_sha256") != csha:
                    _refuse("census_path_reused", f"{old.get('cert_id')} already cites {cf} with sha256 "
                                                  f"{str(oe.get('census_sha256'))[:12]}.., but the file now hashes to "
                                                  f"{csha[:12]}..: a cited census is never edited; copy a regenerated census "
                                                  "to a NEW unique name (archive_census) and cite that")
        latest = (parsed.by_key.get(rec["cert_key"]) or [None])[-1]
        if latest is not None and _identity(latest) == _identity(rec):
            return [], ("unchanged", latest)
        gen = 1 if latest is None else latest["generation"] + 1
        return [dict(rec, generation=gen, cert_id=f"{rec['cert_key']}@{gen}")], ("appended", None)

    (status, latest), written = _locked_append(path, init, lambda: _check_upstream(rec, {}), decide)
    if status == "unchanged":
        return CertResult("unchanged", latest, latest["cert_id"], path)
    return CertResult("appended", written[0], written[0]["cert_id"], path)


# ─────────────────────────── CI verification and the explicit torn-tail repair ───────────────────────────

def _record_vs_cell(rec: dict, blob: bytes):
    """None when the record agrees with the census CELL held in `blob`, else the reason it does not: verdict, basis,
    measured N/A cause, registry stamp, tool_commit and run id."""
    try:
        obj = strict_json_loads(blob.decode("utf-8"))
        if not isinstance(obj, dict):
            return "the census is not a JSON object"
        head = _select_layer(obj, rec.get("layer"))
        record, cell = _census_record_and_cell(head, rec.get("asset"), rec.get("criterion"))
    except (CertificationRefused, UnicodeDecodeError, ValueError) as e:
        return f"the cited census cannot be read for this asset/criterion ({e})"
    ev = rec.get("evidence") if isinstance(rec.get("evidence"), dict) else {}
    if head.get("layer") != rec.get("layer"):
        return f"the census layer object is {head.get('layer')!r}, the record's layer is {rec.get('layer')!r}"
    if head.get("generated") != ev.get("census_run_id"):
        return f"run id {ev.get('census_run_id')!r} is not the census's generated {head.get('generated')!r}"
    if head.get("registry_revision") != rec.get("registry_revision") or head.get("registry_fingerprint") != rec.get(
            "registry_fingerprint"):
        return "the record's registry revision/fingerprint is not the census stamp"
    if head.get("tool_commit") != ev.get("census_tool_commit"):
        return "the record's census_tool_commit is not the census's tool_commit"
    na = rec.get("na") if isinstance(rec.get("na"), dict) else None
    if cell is None:
        if rec.get("verdict") != "N/A" or na is None or na.get("basis") != "applicability_facts":
            return f"the census holds no cell for it but the record says {rec.get('verdict')!r}"
        return None
    if rec.get("verdict") != cell.get("v"):
        return f"the record says {rec.get('verdict')!r}, the census cell says {cell.get('v')!r}"
    if rec.get("basis") != cell.get("basis"):
        return f"the record's basis {rec.get('basis')!r} is not the cell's {cell.get('basis')!r}"
    if cell.get("v") == "N/A" and (na is None or na.get("cause") != cell.get("cause")):
        return "the record's N/A cause is not the cell's"
    return None


def verify_ledger_census_hashes(repo, ref, ledger_relpath=None) -> dict:
    """For every gate record of the ledger AT `ref`: re-read the census file it cites with `git show <ref>:<path>`,
    recompute the sha256 and compare, then compare the record with the census CELL in that blob (verdict, basis, N/A
    cause, registry stamp, tool_commit, run id). Raises CertificationRefused on a hash mismatch
    (`census_hash_mismatch`), a record that differs from its cell (`census_verdict_mismatch`: a doctored record that
    copies a real census_file + sha but says PASS over a FAIL cell), a cited file that is not committed at `ref`
    (`census_not_committed`), one outside TRUSTED_CENSUS_ROOT (`census_outside_root`), a gate record that cites none
    (`census_citation_missing`), an unreadable ledger (`bad_ledger`) or an unknown ref (`bad_ref`). Returns
    {status: "PASS", ...} only when at least one record was verified; when the ledger does not exist yet at `ref`, or
    holds no gate record, it returns {status: "NO_DETECTOR", reason: ...}: nothing was verified, so nothing is reported
    clean. The result always says how many certificates are caller-asserted: `unmeasured_addition` counts the addition
    keys whose LATEST generation reads PASS (information, not a failure)."""
    rel = ledger_relpath or LEDGER_RELPATH
    ok_ref = _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if ok_ref is None or ok_ref.returncode != 0:
        _refuse("bad_ref", f"{ref!r} is not a commit in {repo}")
    r = _git(repo, "show", f"{ref}:{rel}")
    if r is None or r.returncode != 0:
        return dict(status="NO_DETECTOR", checked=0, ref=ref, ledger=rel, unmeasured_addition=0,
                    reason=f"{rel} does not exist at {ref}: there is no ledger to verify yet")
    by_key = parse_ledger(r.stdout)
    troot = _trusted_root_rel()
    blobs: dict[str, bytes | None] = {}
    failures, checked, additions = [], 0, []
    for key in sorted(by_key):
        for rec in by_key[key]:
            if rec.get("kind") == "addition" and rec is by_key[key][-1] and rec.get("verdict") == "PASS":
                additions.append(rec["cert_id"])
            if rec.get("kind") != "gate":
                continue
            checked += 1
            ev = rec.get("evidence") if isinstance(rec.get("evidence"), dict) else {}
            f, h = ev.get("census_file"), ev.get("census_sha256")
            if not isinstance(f, str) or not isinstance(h, str):
                failures.append((rec["cert_id"], "census_citation_missing", "cites no census_file / census_sha256"))
                continue
            norm = os.path.normpath(f).replace(os.sep, "/")
            if f.startswith("/") or norm.startswith("..") or not norm.startswith(troot) or norm != f:
                failures.append((rec["cert_id"], "census_outside_root", f"{f!r} is not a path under {troot}"))
                continue
            if f not in blobs:
                g = _git(repo, "show", f"{ref}:{f}")
                blobs[f] = g.stdout if g is not None and g.returncode == 0 else None
            if blobs[f] is None:
                failures.append((rec["cert_id"], "census_not_committed", f"{f} is not committed at {ref}"))
            elif _sha(blobs[f]) != h:
                failures.append((rec["cert_id"], "census_hash_mismatch",
                                 f"{f} at {ref} hashes to {_sha(blobs[f])[:12]}.., the cert recorded {h[:12]}.."))
            else:
                why = _record_vs_cell(rec, blobs[f])
                if why is not None:
                    failures.append((rec["cert_id"], "census_verdict_mismatch", why))
    if failures:
        detail = "; ".join(f"{c}: {code}: {m}" for c, code, m in failures[:10])
        _refuse(failures[0][1], f"{len(failures)} of {checked} gate record(s) fail census verification at {ref}: {detail}")
    if not checked:
        return dict(status="NO_DETECTOR", checked=0, ref=ref, ledger=rel, unmeasured_addition=len(additions),
                    unmeasured_addition_cert_ids=additions, reason="the ledger holds no gate record: nothing was verified")
    return dict(status="PASS", checked=checked, files=len(blobs), ref=ref, ledger=rel,
                unmeasured_addition=len(additions), unmeasured_addition_cert_ids=additions)


def archive_census(src, repo, generated) -> str:
    """Copy the census file `src` BYTE-IDENTICALLY to the unique name `<TRUSTED_CENSUS_ROOT>asset_census_<generated>.json`
    under `repo` and return that repo-relative path (the caller `git add`s / commits it, then cites it). asset_census.py
    main() overwrites `control/asset_census.json` on every run, so a cited file must be a copy under a UNIQUE name that
    is never edited again. `generated` must be the `generated` of a layer object in `src`. Never overwrites: a different
    file (or a symlink) already at that name is `census_archive_exists`; an identical one is returned as is. The copy is
    atomic: the bytes are written and fsynced to a temp file in the same directory and `os.link`ed to the final name
    (which fails if it exists), then the temp is removed, so a crash leaves no partial file at the final name and
    concurrent archivers of the same census cannot trip each other."""
    if not _valid_run_id(generated):
        _refuse("bad_census", f"generated {generated!r} is not a tz-aware ISO timestamp")
    try:
        blob = Path(src).read_bytes()
        obj = strict_json_loads(blob.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        _refuse("bad_census", f"{src} cannot be read as a strict-JSON census ({e})")
    heads = [obj] if isinstance(obj, dict) and "assets" in obj else [
        v for v in (obj.values() if isinstance(obj, dict) else ()) if isinstance(v, dict)]
    if not any(h.get("generated") == generated for h in heads):
        _refuse("bad_census", f"no layer object of {src} has generated == {generated!r}")
    root = Path(os.path.realpath(repo))
    dest_dir = root / _trusted_root_rel()
    name = "asset_census_" + generated.replace(":", "") + ".json"
    dest = dest_dir / name
    rel = f"{_trusted_root_rel()}{name}"
    tmp = None
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".archive_", suffix=".tmp", dir=dest_dir)   # same directory: same filesystem
        with os.fdopen(fd, "wb") as f:
            f.write(blob)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.link(tmp, dest)          # atomic, and fails if dest exists: dest is either absent or complete, never partial
        except FileExistsError:
            if os.path.islink(dest) or not dest.is_file() or dest.read_bytes() != blob:
                _refuse("census_archive_exists", f"{dest} already exists with different bytes (or is not a regular "
                                                 "file): a cited census is never overwritten")
    except OSError as e:
        _refuse("bad_census", f"{dest} cannot be written ({e})")
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    return rel


def repair_torn_tail(ledger_path, out=None) -> dict:
    """The explicit repair for a torn ledger: truncate an INCOMPLETE final line (no newline, not valid JSON), printing
    it first to `out` (default stdout). Never silent; touches nothing else; refuses (nothing truncated) when the
    ledger without that tail is still unreadable."""
    out = sys.stdout if out is None else out
    path = Path(ledger_path)
    if os.path.islink(path) or not path.is_file():
        _refuse("bad_ledger_path", f"{path} is not a regular file")
    with open(path, "r+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        data = f.read()
        tail = data.rsplit(b"\n", 1)[-1] if data else b""
        if not tail:
            return dict(status="nothing_to_repair", removed_bytes=0)
        try:
            strict_json_loads(tail.decode("utf-8"))
            return dict(status="nothing_to_repair", removed_bytes=0,
                        note="the final line is a complete record that lacks its newline (the writer handles that)")
        except (UnicodeDecodeError, ValueError):
            pass
        _parse(data[:len(data) - len(tail)])        # refuses (bad_ledger) before anything is truncated
        print(f"TORN TAIL ({len(tail)} bytes) removed from {path}: {tail!r}", file=out, flush=True)
        f.truncate(len(data) - len(tail))
        f.flush()
        os.fsync(f.fileno())
    return dict(status="repaired", removed_bytes=len(tail))


# ─────────────────────────── CLI ───────────────────────────

def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Append one certification record to asset_certs.jsonl (E5.1).")
    ap.add_argument("--ledger", default=None, help=f"ledger path (default: ${ENV_LEDGER}, else <control>/asset_certs.jsonl)")
    ap.add_argument("--init", action="store_true", help="create the ledger (with its schema row) if it does not exist")
    ap.add_argument("--asset", required=True)
    ap.add_argument("--layer", required=True)
    ap.add_argument("--kind", default="gate", choices=KINDS)
    ap.add_argument("--gate", default=None)
    ap.add_argument("--criterion", required=True)
    ap.add_argument("--criterion-version", type=int, default=None, help="additions only (a gate's is the registry's)")
    ap.add_argument("--detector", default=None, help="additions only; a gate's detector is the registry's")
    ap.add_argument("--verdict", default=None, help="a gate's verdict is read from the census; this is only a "
                                                    "cross-check that must equal it (required for an addition)")
    ap.add_argument("--census", default=None, help="the census JSON FILE (committed under the trusted census root "
                                                    f"{TRUSTED_CENSUS_ROOT}) the verdict is read from; required for a gate")
    ap.add_argument("--census-run-id", default=None, help="must equal the census's own `generated`; defaults to it")
    ap.add_argument("--measured", default=None)
    ap.add_argument("--inspector-commit", default=None)
    ap.add_argument("--job-image-tag", default=None)
    ap.add_argument("--writer-hash", action="append", default=[], metavar="PATH=SHA256",
                    help="verified against --writer-repo/--writer-ref; unverified hashes do not satisfy a PASS")
    ap.add_argument("--writer-file", action="append", default=[], metavar="PATH", help="hash this repo file")
    ap.add_argument("--writer-repo", default=None)
    ap.add_argument("--writer-ref", default=None, help="hash the committed blob at this ref, not the working tree")
    ap.add_argument("--writer-hashes-reason", default=None)
    ap.add_argument("--upstream", action="append", default=[], metavar="CERT_ID")
    ap.add_argument("--semantic-fingerprint", default=None)
    ap.add_argument("--verified-by", default=None)
    ap.add_argument("--verified-on", default=None)
    ap.add_argument("--na-rule-id", default=None)
    ap.add_argument("--facts-json", default=None, help="cross-check of the census record's applicability facts, e.g. "
                                                       '{"columns": ["a"], "asset_kind": "data"}')
    ap.add_argument("--basis", default=None, help="a cross-check of the census cell's basis; never supplies one")
    ap.add_argument("--inconclusive", action="store_true")
    return ap


def _special_main(argv):
    ap = argparse.ArgumentParser(description="E5.1 ledger maintenance modes")
    ap.add_argument("--verify-census-hashes", action="store_true")
    ap.add_argument("--repair-torn-tail", action="store_true")
    ap.add_argument("--archive-census", default=None, metavar="SRC")
    ap.add_argument("--generated", default=None)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--ref", default="HEAD")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--ledger-relpath", default=None)
    a = ap.parse_args(argv)
    try:
        if a.verify_census_hashes:
            res = verify_ledger_census_hashes(a.repo, a.ref, a.ledger_relpath)
            print(json.dumps(res))
            return 0 if res["status"] == "PASS" else 3
        if a.archive_census:
            print(json.dumps(dict(archived=archive_census(a.archive_census, a.repo, a.generated))))
            return 0
        res = repair_torn_tail(resolve_ledger_path(a.ledger))
        print(json.dumps(res))
        return 0
    except CertificationRefused as e:
        print(f"REFUSED {e.code}: {e.message}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"REFUSED bad_request: {e}", file=sys.stderr)
        return 2


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if "--verify-census-hashes" in argv or "--repair-torn-tail" in argv or "--archive-census" in argv:
        return _special_main(argv)
    a = _parser().parse_args(argv)
    try:
        run_id = a.census_run_id
        if run_id is None and a.census:
            try:
                head = strict_json_loads(Path(a.census).read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, ValueError) as e:
                _refuse("bad_census", f"{a.census} cannot be read as strict JSON ({e})")
            if not isinstance(head, dict):
                _refuse("bad_census", "the census must be a JSON object")
            run_id = _select_layer(head, a.layer).get("generated") if a.layer in ac.LAYERS else None
        evidence = {k: v for k, v in dict(census_run_id=run_id, measured=a.measured,
                                          inspector_commit=a.inspector_commit).items() if v is not None}
        wh = {}
        for item in a.writer_hash:
            p, sep, h = item.partition("=")
            wh[p] = h
        try:
            facts = strict_json_loads(a.facts_json) if a.facts_json else None
        except ValueError as e:
            _refuse("bad_facts", f"--facts-json is not strict JSON ({e})")
        r = write_certification(
            ledger_path=a.ledger, init=a.init, asset=a.asset, layer=a.layer, kind=a.kind, gate=a.gate,
            criterion=a.criterion, criterion_version=a.criterion_version, detector=a.detector, verdict=a.verdict,
            evidence=evidence, census_path=a.census,
            job_image_tag=a.job_image_tag, writer_hashes=wh, writer_files=a.writer_file, writer_repo=a.writer_repo,
            writer_ref=a.writer_ref, writer_hashes_reason=a.writer_hashes_reason, upstream_cert_ids=a.upstream,
            semantic_fingerprint=a.semantic_fingerprint, verified_by=a.verified_by, verified_on=a.verified_on,
            na_rule_id=a.na_rule_id, facts=facts, basis=a.basis, inconclusive=a.inconclusive)
    except CertificationRefused as e:
        print(f"REFUSED {e.code}: {e.message}", file=sys.stderr)
        return 2
    print(json.dumps(dict(status=r.status, cert_id=r.cert_id, generation=r.record["generation"],
                          ledger=str(r.ledger_path))))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"nikasha_certify: script error — {exc}", file=sys.stderr)
        sys.exit(5)
