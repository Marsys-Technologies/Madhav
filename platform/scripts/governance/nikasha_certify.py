#!/usr/bin/env python3
"""nikasha_certify.py — Suvarna E5.1: write certification records (arch 12.16) into `asset_certs.jsonl`.

A certification record is what an asset's ELEVATED state rests on (plan 1.1), so this writer is mostly a set of
REFUSALS; every PASS or N/A it can emit has a code path that could have made it read otherwise (CLAUDE.md N.8):

  * for kind=gate the VERDICT IS NOT A CALLER ASSERTION. The census record is mandatory: the writer reads the
    verdict, basis, N/A cause and applicability facts from the census cell of that asset and criterion. It refuses
    when no census is supplied, when it is not a FILE under the control directory (`asset_census.CTRL`) or a census
    archive (`--census-archive-dir` / $NIKASHA_CENSUS_ARCHIVE; default none), when the file lacks that asset or cell,
    when `evidence.census_run_id` differs from the census's own `generated`, when the census head carries a registry
    revision/fingerprint other than the current one, or when a caller-passed verdict/basis/facts differ from the
    census (a caller verdict is only a cross-check). The census file's sha256 is recorded in `evidence.census_sha256`
    and `cross_checked: true` is writer-set on every gate record. kind=addition has no census cell: its verdict is
    the caller's, its N/A is always refused, its basis can never be typed;
  * a PASS (or any verdict but NO_DETECTOR) whose criterion has `detector: NONE` is refused;
  * a record with no census run id in its evidence is refused (the id is the census's own `generated` timestamp;
    hand_row_provenance.py), PASS or not;
  * an N/A is never typed: it is recorded only when the registry computes it. Fact-disproved applicability is
    recomputed here through `asset_census.criterion_applicability` from the CENSUS RECORD's facts; a measured-cause
    N/A needs the census cell that measured it. Both need the rule id declared in `asset_census.NA_RULE_DECISIONS`
    (empty today, so every N/A is refused until N-22 declares a rule — the rollup reads such an N/A as NO_DETECTOR);
  * the registry, not the caller, supplies the gate, detector, criterion revision and registry fingerprint. Today's
    census heads carry no registry revision/fingerprint, so the record says `registry_binding: "census_unbound"`
    (the registry stamped is the one at WRITE time, not provably the one the census ran under);
  * a PASS the census rollup itself would not honour (Null.* and Narr.fidelity_test capped at PARTIAL, an
    INCONCLUSIVE record, an unrecognised basis, a basis `declaration` the registry does not define for that
    criterion and asset kind) is refused;
  * a PASS without a semantic fingerprint and VERIFIED writer file hashes (or a documented, census-corroborated
    reason for having none) could never go stale, so it is refused. Typed hashes count only when verified against
    the repository (`--writer-repo`/`--writer-ref`) or computed here (`--writer-file`); upstream certification ids
    must exist, be the latest generation, and pass.

The ledger is append-only and hash-chained: each record carries `prev_sha256`, the sha256 of the previous line's
bytes (the `_schema` row for the first record); the chain is verified on every read and write (an edit to any
earlier line is refused `bad_ledger`; a torn last line `torn_ledger`). A record is identified by `cert_key` =
`<asset>|<gate|addition>|<criterion>`, numbered by `generation` from 1, with `cert_id` = `<cert_key>@<generation>`.
Re-writing a measurement whose CURRENCY fields are unchanged appends nothing; a changed one appends generation+1.
Currency fields are the ones E5.5 invalidates on (verdict, criterion/registry revision and binding, detector, writer
hashes and whether they were verified, upstream ids, semantic fingerprint, N/A computation, basis, inconclusive,
transitive_only); `evidence`, `verified_by`, `verified_on`, `job_image_tag`, `cross_checked` and `prev_sha256` are
recorded with the first generation and do not make a new one, because a rebuild that changes no semantic column must
leave every downstream certificate current (arch 12.16). E5.5 reads these records; it also decides when a record has
gone stale. This writer only guarantees that it was honest when written and that the history is intact.

Ledger path: `--ledger` / `ledger_path`, else $NIKASHA_CERTS_LEDGER, else <control dir>/asset_certs.jsonl
(`asset_census.CTRL`, itself overridable with NIKASHA_CONTROL_DIR). A missing ledger is refused unless `--init`; a
symlink or directory at the ledger path is refused (never followed); a zero-byte file under `--init` is initialised.

Usage:
  nikasha_certify.py --asset bg_ontology --layer L0 --criterion Build.registered \
      --census <control>/census.json --writer-repo . --writer-file platform/python-sidecar/.../bg_ontology.py \
      --writer-ref <commit> --semantic-fingerprint <sha256> --verified-by census-run
Exit: 0 appended or unchanged (stdout: JSON) · 2 refused (stderr: `REFUSED <code>: ...`; nothing written) ·
      5 script error.
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
import unicodedata
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asset_census as ac  # noqa: E402  (read-only use of its registry, applicability and N/A tables)

RECORD_VERSION = 1
VERDICTS = ("PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "ERRORED", "N/A")
KINDS = ("gate", "addition")
ENV_LEDGER = "NIKASHA_CERTS_LEDGER"
ENV_CENSUS_ARCHIVE = "NIKASHA_CENSUS_ARCHIVE"
CALLER_EVIDENCE_KEYS = ("census_run_id", "measured", "inspector_commit", "note")
WRITER_EVIDENCE_KEYS = ("census_file", "census_sha256")      # set by this writer from the census file it read; never typed
# Fields E5.5 invalidates on (and so the only fields whose change makes a new generation). Everything else on a
# record is provenance for the generation that first carried it.
CURRENCY_FIELDS = ("verdict", "criterion_version", "registry_revision", "registry_fingerprint", "registry_binding",
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
    "edited or deleted; each record's prev_sha256 is the sha256 of the previous line's bytes (this row for the first). "
    "One JSON object per line after this one, written only by nikasha_certify.py. Fields: asset, layer, kind "
    "(gate|addition), gate, criterion, criterion_version, registry_revision, registry_fingerprint, registry_binding "
    "(census_bound|census_unbound|null), detector, verdict (PASS|FAIL|PARTIAL|NO_DETECTOR|ERRORED|N/A; a gate's is "
    "read from the census cell), basis, na {rule_id, decision_id, basis, cause, facts}, inconclusive, transitive_only, "
    "evidence {census_run_id (required), measured, inspector_commit, note, census_file, census_sha256 (the last two "
    "writer-set)}, cross_checked, job_image_tag, writer_hashes {path: sha256}, writer_hashes_verified, "
    "writer_hashes_reason, upstream_cert_ids, semantic_fingerprint, cert_key, generation, cert_id, prev_sha256, "
    "verified_by, verified_on, record_version. The current record of a cert_key is its highest generation; whether it "
    "is still CURRENT (writer hashes, upstream generations, semantic fingerprint, registry revision) is E5.5's decision."
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
    path: str


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


def strict_json_loads(text: str):
    """json.loads that refuses duplicate object keys and NaN/Infinity (ValueError, incl. JSONDecodeError)."""
    return json.loads(text, object_pairs_hook=_no_dup_keys, parse_constant=_no_constant)


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


def _parse(data: bytes):
    """(cert_key -> its records in file order, sha256 of the last non-blank line's bytes). Strict: an unreadable or
    non-UTF-8 line, a duplicate key, a first line that is not the `_schema` row, a second `_schema` row, a record
    with no generation (legacy shape), a cert_id that is not `<cert_key>@<generation>`, a generation sequence that
    is not 1..n, or a `prev_sha256` chain that does not hold all raise `bad_ledger`; a last line with no newline
    that is not valid JSON is a torn write and raises `torn_ledger`. A ledger this writer cannot reason about is not
    appended to."""
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
                                       "it is neither extended nor repaired")
            _refuse("bad_ledger", f"line {n} is not readable JSON ({e})")
    if not rows or not isinstance(rows[0][2], dict) or rows[0][2].get("asset") != "_schema":
        _refuse("bad_ledger", "the first line must be the `_schema` row")
    by_key: dict[str, list[dict]] = {}
    prev = _sha(rows[0][1])
    for n, raw, r in rows[1:]:
        if not isinstance(r, dict):
            _refuse("bad_ledger", f"line {n} is not a JSON object")
        if r.get("asset") == "_schema":
            _refuse("bad_ledger", f"line {n}: a second `_schema` row")
        key, gen, cid = r.get("cert_key"), r.get("generation"), r.get("cert_id")
        if (not isinstance(key, str) or isinstance(gen, bool) or not isinstance(gen, int) or gen < 1
                or cid != f"{key}@{gen}" or not isinstance(r.get("verdict"), str)):
            _refuse("bad_ledger", f"line {n} is not a record this writer can read (cert_key/generation/cert_id)")
        if r.get("prev_sha256") != prev:
            _refuse("bad_ledger", f"line {n}: the hash chain is broken (prev_sha256 is not the sha256 of the previous "
                                  "line): an earlier line was edited, deleted or reordered")
        prev = _sha(raw)
        by_key.setdefault(key, []).append(r)
    for key, recs in by_key.items():
        if [r["generation"] for r in recs] != list(range(1, len(recs) + 1)):
            _refuse("bad_ledger", f"{key}: generations are not 1..{len(recs)} in order")
    return by_key, prev


def parse_ledger(data: bytes) -> dict[str, list[dict]]:
    """cert_key -> its records in file order (see `_parse` for what is refused)."""
    return _parse(data)[0]


def read_ledger(path) -> dict[str, list[dict]]:
    """Read-only helper for E5.5 / E6.3: cert_key -> records. Raises CertificationRefused('bad_ledger' /
    'torn_ledger') as above, including when the hash chain does not hold."""
    p = Path(path)
    if not p.exists():
        _refuse("ledger_missing", f"{p} does not exist")
    return parse_ledger(p.read_bytes())


# ─────────────────────────── field validation ───────────────────────────

def _nonblank(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _valid_run_id(v) -> bool:
    if not isinstance(v, str) or not v or v != v.strip():
        return False
    try:
        return dt.datetime.fromisoformat(v).tzinfo is not None
    except ValueError:
        return False


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

def _trusted_roots(archive_dir):
    roots = [Path(ac.CTRL)]
    a = archive_dir if archive_dir is not None else (os.environ.get(ENV_CENSUS_ARCHIVE) or None)
    if a is not None:
        roots.append(Path(a))
    return [os.path.realpath(r) for r in roots]


def _load_census(census_path, census, archive_dir) -> _CensusSource:
    """The census, read from a FILE under the control dir or a census archive (symlinks resolved first). Its sha256
    is of the bytes read. A dict is accepted only together with its source file and must equal what the file holds."""
    if census_path is None:
        if census is not None:
            _refuse("census_unsourced", "a census dict without its source file cannot be hashed: a census is read "
                                        "from a file under the control dir or a census archive")
        _refuse("census_required", "a gate verdict is read from the census record, not asserted: supply the census "
                                   "file (--census) for this asset and criterion")
    if not isinstance(census_path, (str, os.PathLike)):
        _refuse("bad_census", "the census path must be a path")
    rp = os.path.realpath(census_path)
    if not any(rp == root or rp.startswith(root.rstrip(os.sep) + os.sep) for root in _trusted_roots(archive_dir)):
        _refuse("census_untrusted", f"{rp} is not under the control directory ({ac.CTRL}) or a census archive "
                                    f"(--census-archive-dir / ${ENV_CENSUS_ARCHIVE}): a census written elsewhere "
                                    "could have been made up")
    if not os.path.isfile(rp):
        _refuse("bad_census", f"{rp} is not a file")
    blob = Path(rp).read_bytes()
    try:
        obj = strict_json_loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        _refuse("bad_census", f"{rp} is not strict JSON ({e})")
    if not isinstance(obj, dict):
        _refuse("bad_census", "the census must be a JSON object")
    if census is not None and census != obj:
        _refuse("census_mismatch", "the supplied census dict is not what its source file holds")
    return _CensusSource(obj, _sha(blob), rp)


def _check_census_head(c: dict, layer: str, run_id: str, need_binding: bool):
    """Run id, layer and (gates) the registry the census says it ran under. Returns the registry_binding word."""
    if c.get("generated") != run_id or not _valid_run_id(c.get("generated")):
        _refuse("census_run_id_mismatch", f"evidence.census_run_id {run_id!r} is not the census's own `generated` "
                                          f"{c.get('generated')!r}")
    if c.get("layer") != layer:
        _refuse("census_mismatch", f"census layer {c.get('layer')!r} is not {layer!r}")
    if not need_binding:
        return None
    rr, rf = c.get("registry_revision"), c.get("registry_fingerprint")
    if rr is None and rf is None:
        return "census_unbound"
    if (isinstance(rr, bool) or not isinstance(rr, int) or rr != ac.REGISTRY_REVISION
            or not isinstance(rf, str) or rf != ac.registry_fingerprint()):
        _refuse("census_mismatch", f"the census ran under registry revision {rr!r} / fingerprint {str(rf)[:12]!r}.., "
                                   f"not the current {ac.REGISTRY_REVISION} / {ac.registry_fingerprint()[:12]}..")
    return "census_bound"


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
                 census_archive_dir=None, job_image_tag=None, writer_hashes=None, writer_files=None, writer_repo=None,
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
                json.dumps(facts, allow_nan=False)
        except (TypeError, ValueError):
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
    src, meas, record, binding = None, None, None, None
    if kind == "gate" or census_path is not None or census is not None:
        src = _load_census(census_path, census, census_archive_dir)
        binding = _check_census_head(src.obj, layer, run_id, need_binding=(kind == "gate"))
    cfacts = {}
    transitive_only = False
    if kind == "gate":
        record, meas = _census_record_and_cell(src.obj, asset, criterion)
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
    has_writer = record.get("has_writer") if record is not None and isinstance(record.get("has_writer"), bool) else None
    wh_reason = _writer_evidence(wh, wh_verified, writer_hashes_reason, verdict, na_measured, kind, has_writer)

    cert_key = cert_key_of(asset, kind, criterion)
    ups = _upstream_ids(upstream_cert_ids, cert_key)
    ev = dict(evidence)
    if src is not None:
        ev["census_file"], ev["census_sha256"] = src.path, src.sha256
    rec = dict(
        asset=asset, layer=layer, kind=kind, gate=gate_name, criterion=criterion, criterion_version=crit_version,
        registry_revision=reg_rev, registry_fingerprint=reg_fp, registry_binding=binding, detector=det,
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


def _open_ledger(path: Path, init: bool, rec: dict):
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
        _check_upstream(rec, {})                       # a fresh ledger: upstream ids can only be unknown
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


def write_certification(*, ledger_path=None, init: bool = False, **fields) -> CertResult:
    """Validate, then append one record (or report the identical latest generation). See build_record for the
    fields. The ledger is never rewritten: it is opened for append, under an exclusive lock that also covers the
    read the generation number, the hash chain and the idempotence check depend on."""
    try:
        rec = build_record(**fields)
    except CertificationRefused:
        raise
    except (TypeError, ValueError, AttributeError, KeyError, OverflowError) as e:
        _refuse("bad_request", f"the request is malformed ({type(e).__name__}: {e})")
    path = resolve_ledger_path(ledger_path)
    f, created_new = _open_ledger(path, init, rec)
    try:
        with f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            data = f.read()
            schema_line = json.dumps({"asset": "_schema", "_doc": SCHEMA_DOC}, ensure_ascii=False).encode("utf-8")
            fresh = not data
            if fresh and not init:
                _refuse("bad_ledger", f"{path} is empty (no `_schema` row); pass init=True / --init to initialise it")
            by_key, prev = ({}, _sha(schema_line)) if fresh else _parse(data)
            _check_upstream(rec, by_key)
            latest = (by_key.get(rec["cert_key"]) or [None])[-1]
            if latest is not None and _identity(latest) == _identity(rec):
                return CertResult("unchanged", latest, latest["cert_id"], path)
            gen = 1 if latest is None else latest["generation"] + 1
            rec = dict(rec, generation=gen, cert_id=f"{rec['cert_key']}@{gen}", prev_sha256=prev)
            line = (json.dumps(rec, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
            if fresh:
                line = schema_line + b"\n" + line
            elif not data.endswith(b"\n"):
                line = b"\n" + line
            f.write(line)                  # one write of a fully serialised line, to an append-only descriptor
            f.flush()
            os.fsync(f.fileno())
            return CertResult("appended", rec, rec["cert_id"], path)
    except BaseException:
        if created_new:                    # only a file THIS call created, and only while it is still empty
            try:
                if not os.path.islink(path) and os.stat(path).st_size == 0:
                    os.unlink(path)
            except OSError:
                pass
        raise


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
    ap.add_argument("--census", default=None, help="the census JSON FILE (under the control dir or a census archive) "
                                                    "the verdict is read from; required for a gate")
    ap.add_argument("--census-archive-dir", default=None, help=f"an extra trusted census directory "
                                                                f"(default: ${ENV_CENSUS_ARCHIVE}, else none)")
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


def main(argv=None) -> int:
    a = _parser().parse_args(argv)
    try:
        run_id = a.census_run_id
        if run_id is None and a.census:
            try:
                head = strict_json_loads(Path(a.census).read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, ValueError) as e:
                _refuse("bad_census", f"{a.census} cannot be read as strict JSON ({e})")
            run_id = head.get("generated") if isinstance(head, dict) else None
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
            evidence=evidence, census_path=a.census, census_archive_dir=a.census_archive_dir,
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
