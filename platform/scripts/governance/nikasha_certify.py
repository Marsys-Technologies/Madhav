#!/usr/bin/env python3
"""nikasha_certify.py — Suvarna E5.1: write certification records (arch 12.16) into `asset_certs.jsonl`.

A certification record is what an asset's ELEVATED state rests on (plan 1.1), so this writer is mostly a set of
REFUSALS; every PASS or N/A it can emit has a code path that could have made it read otherwise (CLAUDE.md N.8):

  * a PASS (or any verdict but NO_DETECTOR) whose criterion has `detector: NONE` is refused;
  * a record with no census run id in its evidence is refused (the id is the census's own `generated` timestamp;
    hand_row_provenance.py), PASS or not;
  * an N/A is never typed: it is recorded only when the registry computes it. Fact-disproved applicability is
    recomputed here through `asset_census.criterion_applicability`; a measured-cause N/A needs the census record
    that measured it. Both need the rule id declared in `asset_census.NA_RULE_DECISIONS` (empty today, so every
    N/A is refused until N-22 declares a rule — the rollup reads such an N/A as NO_DETECTOR too);
  * the registry, not the caller, supplies the gate, detector, criterion revision and registry fingerprint;
  * a PASS the census rollup itself would not honour (Null.* and Narr.fidelity_test capped at PARTIAL, an
    INCONCLUSIVE record, an unrecognised basis) is refused;
  * a PASS without a semantic fingerprint and writer file hashes (or a stated reason for having none) could never
    go stale, so it is refused; upstream certification ids must exist, be the latest generation, and pass.

The ledger is append-only. A record is identified by `cert_key` = `<asset>|<gate|addition>|<criterion>`, numbered by
`generation` from 1, with `cert_id` = `<cert_key>@<generation>`. Re-writing a measurement whose CURRENCY fields are
unchanged appends nothing; a changed one appends generation+1. Currency fields are the ones E5.5 invalidates on
(verdict, criterion/registry revision, detector, writer hashes, upstream ids, semantic fingerprint, N/A computation,
basis); `evidence`, `verified_by`, `verified_on` and `job_image_tag` are recorded with the first generation and do
not make a new one, because a rebuild that changes no semantic column must leave every downstream certificate
current (arch 12.16). E5.5 reads these records; it also decides when a record has gone stale. This writer only
guarantees that it was honest when written and that the history is intact.

Ledger path: `--ledger` / `ledger_path`, else $NIKASHA_CERTS_LEDGER, else <control dir>/asset_certs.jsonl
(`asset_census.CTRL`, itself overridable with NIKASHA_CONTROL_DIR). A missing ledger is refused unless `--init`.

Usage:
  nikasha_certify.py --asset bg_ontology --layer L0 --criterion Build.registered --verdict PASS \
      --census census.json --writer-file platform/python-sidecar/.../bg_ontology.py --writer-ref <commit> \
      --semantic-fingerprint <sha256> --verified-by census-run
Exit: 0 appended or unchanged (stdout: JSON) · 2 refused (stderr: `REFUSED <code>: ...`; nothing written) ·
      5 script error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asset_census as ac  # noqa: E402  (read-only use of its registry, applicability and N/A tables)

RECORD_VERSION = 1
VERDICTS = ("PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "ERRORED", "N/A")
KINDS = ("gate", "addition")
ENV_LEDGER = "NIKASHA_CERTS_LEDGER"
EVIDENCE_KEYS = ("census_run_id", "measured", "inspector_commit", "census_file", "note")
# Fields E5.5 invalidates on (and so the only fields whose change makes a new generation). Everything else on a
# record is provenance for the generation that first carried it.
CURRENCY_FIELDS = ("verdict", "criterion_version", "registry_revision", "registry_fingerprint", "detector",
                   "writer_hashes", "writer_hashes_reason", "upstream_cert_ids", "semantic_fingerprint", "na", "basis")

_ASSET = re.compile(r"[a-z][a-z0-9_]*")
_ADDITION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_CERT_ID = re.compile(r"([a-z][a-z0-9_]*)\|(gate|addition)\|([A-Za-z0-9][A-Za-z0-9_.-]*)@([1-9][0-9]*)")
_DECLARATION = "declaration"        # the one recognised `basis` (asset_census._check_contribution), case-exact

SCHEMA_DOC = (
    "Certification ledger (arch 12.16; plan 1.1). Append-only: lines are only ever added, never edited or deleted. "
    "One JSON object per line after this one, written only by nikasha_certify.py. Fields: asset, layer, kind "
    "(gate|addition), gate, criterion, criterion_version, registry_revision, registry_fingerprint, detector, verdict "
    "(PASS|FAIL|PARTIAL|NO_DETECTOR|ERRORED|N/A), basis, na {rule_id, decision_id, basis, cause, facts}, evidence "
    "{census_run_id (required), measured, inspector_commit}, job_image_tag, writer_hashes {path: sha256}, "
    "writer_hashes_reason, upstream_cert_ids, semantic_fingerprint, cert_key, generation, cert_id, verified_by, "
    "verified_on, record_version. The current record of a cert_key is its highest generation; whether it is still "
    "CURRENT (writer hashes, upstream generations, semantic fingerprint, registry revision) is E5.5's decision."
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


def parse_ledger(data: bytes) -> dict[str, list[dict]]:
    """cert_key -> its records in file order. Strict: an unreadable line, a first line that is not the `_schema`
    row, a record with no generation (legacy shape), a cert_id that is not `<cert_key>@<generation>`, or a
    generation sequence that is not 1..n all raise `bad_ledger` — a ledger this writer cannot reason about is not
    appended to."""
    text = data.decode("utf-8", errors="replace") if data else ""
    rows = []
    for n, ln in enumerate(text.split("\n"), 1):
        if not ln.strip():
            continue
        try:
            rows.append((n, json.loads(ln)))
        except json.JSONDecodeError as e:
            _refuse("bad_ledger", f"line {n} is not JSON ({e.msg})")
    if not rows or not isinstance(rows[0][1], dict) or rows[0][1].get("asset") != "_schema":
        _refuse("bad_ledger", "the first line must be the `_schema` row")
    by_key: dict[str, list[dict]] = {}
    for n, r in rows:
        if not isinstance(r, dict):
            _refuse("bad_ledger", f"line {n} is not a JSON object")
        if r.get("asset") == "_schema":
            continue
        key, gen, cid = r.get("cert_key"), r.get("generation"), r.get("cert_id")
        if (not isinstance(key, str) or isinstance(gen, bool) or not isinstance(gen, int) or gen < 1
                or cid != f"{key}@{gen}" or not isinstance(r.get("verdict"), str)):
            _refuse("bad_ledger", f"line {n} is not a record this writer can read (cert_key/generation/cert_id)")
        by_key.setdefault(key, []).append(r)
    for key, recs in by_key.items():
        if [r["generation"] for r in recs] != list(range(1, len(recs) + 1)):
            _refuse("bad_ledger", f"{key}: generations are not 1..{len(recs)} in order")
    return by_key


def read_ledger(path) -> dict[str, list[dict]]:
    """Read-only helper for E5.5 / E6.3: cert_key -> records. Raises CertificationRefused('bad_ledger') as above."""
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


def _writer_hashes(wh, reason, verdict, na_measured: bool):
    if wh is None:
        wh = {}
    if not isinstance(wh, dict):
        _refuse("bad_writer_hashes", "writer_hashes must be a mapping of relative path -> lower-case sha256")
    for p, h in wh.items():
        if not _check_relpath(p) or not isinstance(h, str) or not _SHA256.fullmatch(h):
            _refuse("bad_writer_hashes", f"bad writer hash entry {p!r}: need a relative path and 64 lower-case hex")
    if reason is not None and not isinstance(reason, str):
        _refuse("bad_writer_hashes", "writer_hashes_reason, when given, must be text")
    if (verdict == "PASS" or na_measured) and not wh and not _nonblank(reason):
        _refuse("missing_writer_hashes",
                "a PASS (or measured N/A) with no writer file hashes can never go stale on a writer change: give the "
                "hashes, or writer_hashes_reason saying why the asset has no writer file")
    return dict(sorted(wh.items())), (reason.strip() if _nonblank(reason) else None)


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


# ─────────────────────────── the census cross-check ───────────────────────────

def _census_measurement(census, asset: str, layer: str, crit: str, run_id: str):
    """The census's measurement of (asset, crit), or None when the census carries none for it. Any disagreement
    between the census and the request (run id, layer, asset) is `census_mismatch`."""
    if not isinstance(census, dict):
        _refuse("census_mismatch", "census must be the census JSON object")
    if census.get("generated") != run_id:
        _refuse("census_mismatch", f"census run id {census.get('generated')!r} is not the record's {run_id!r}")
    if census.get("layer") != layer:
        _refuse("census_mismatch", f"census layer {census.get('layer')!r} is not {layer!r}")
    recs = [a for a in census.get("assets") or [] if isinstance(a, dict) and a.get("asset_id") == asset]
    if len(recs) != 1:
        _refuse("census_mismatch", f"census holds {len(recs)} records for {asset} (need exactly one)")
    ms = recs[0].get("measurements")
    if not isinstance(ms, dict):
        _refuse("census_mismatch", f"census record for {asset} has no measurements")
    m = ms.get(crit)
    if m is not None and not isinstance(m, dict):
        _refuse("census_mismatch", f"census measurement of {crit} is not an object")
    return m


# ─────────────────────────── N/A: computed, never typed ───────────────────────────

def _computed_na(criterion, layer, facts, na_rule_id, census_meas, census_given):
    """The `na` block for a registry-computed N/A, or CertificationRefused. Two computations exist:
    fact-disproved applicability (recomputed here from the supplied facts) and a cause the census measured
    (needs the census record). Either way the rule id must be DECLARED in NA_RULE_DECISIONS."""
    try:
        ac.validate_na_rule_decisions()
    except ValueError as e:
        _refuse("na_rules_invalid", str(e))
    if not _nonblank(na_rule_id):
        _refuse("na_not_computed", "an N/A needs the rule id the registry computes for it; none was given")
    crit, sep, rule = na_rule_id.partition("#")
    if not sep or crit != criterion:
        _refuse("na_not_computed", f"rule id {na_rule_id!r} is not a rule of {criterion}")
    if rule in ("columns_any", "asset_kinds"):
        ap = ac.criterion_applicability(criterion, layer, facts)
        if ap["state"] != "NOT_APPLICABLE" or ap["rule_id"] != na_rule_id:
            _refuse("na_not_computed",
                    f"the registry computes {ap['state']} (rule {ap['rule_id']!r}) for the supplied facts, not "
                    f"NOT_APPLICABLE under {na_rule_id!r}: {ap['reason']}")
        if census_given and census_meas is not None:
            _refuse("na_not_computed", "the census holds a measured record for this criterion, which takes "
                                       "precedence over any applicability rule (the rollup reads it first)")
        used = {k: facts[k] for k in ("columns", "columns_known", "asset_kind") if k in facts}
        if "columns" in used:
            used["columns"] = sorted(used["columns"])
        na = dict(rule_id=na_rule_id, basis="applicability_facts", cause=None, facts=used)
    elif rule.startswith("measured:"):
        cause = rule[len("measured:"):]
        if cause not in ac.NA_CAUSES.get(criterion, ()):
            _refuse("na_not_computed", f"{cause!r} is not a registered N/A cause of {criterion}")
        if not census_given or census_meas is None or census_meas.get("v") != "N/A" or census_meas.get("cause") != cause:
            _refuse("na_not_computed", f"a measured N/A needs the census record that measured N/A with cause "
                                       f"{cause!r}; it was not supplied or does not say so")
        na = dict(rule_id=na_rule_id, basis="measured_cause", cause=cause, facts=None)
    else:
        _refuse("na_not_computed", f"{na_rule_id!r} is not a rule form this inspector issues")
    if na_rule_id not in ac.NA_RULE_DECISIONS:
        _refuse("na_not_computed", f"N/A rule undecided (N-22): {na_rule_id!r} is not declared in NA_RULE_DECISIONS, "
                                   "so the rollup reads this NO_DETECTOR, not N/A")
    return dict(rule_id=na["rule_id"], decision_id=ac.NA_RULE_DECISIONS[na_rule_id], basis=na["basis"],
                cause=na["cause"], facts=na["facts"])


# ─────────────────────────── the record ───────────────────────────

def build_record(*, asset, layer, criterion, verdict, evidence, verified_by, kind="gate", gate=None, detector=None,
                 criterion_version=None, facts=None, na_rule_id=None, census=None, job_image_tag=None,
                 writer_hashes=None, writer_hashes_reason=None, upstream_cert_ids=(), semantic_fingerprint=None,
                 basis=None, inconclusive=False, verified_on=None) -> dict:
    """Validate everything that needs no ledger and return the record without cert_id/generation. Raises
    CertificationRefused; has no side effect."""
    if kind not in KINDS:
        _refuse("bad_kind", f"kind must be one of {KINDS}")
    if layer not in ac.LAYERS:
        _refuse("bad_layer", f"layer must be one of {sorted(ac.LAYERS)}")
    if not isinstance(asset, str) or not _ASSET.fullmatch(asset):
        _refuse("bad_asset", f"{asset!r} is not an asset id")
    if not asset.startswith(ac.LAYERS[layer]["prefix"]):
        _refuse("asset_layer_mismatch", f"{asset} is not a {layer} asset (prefix {ac.LAYERS[layer]['prefix']!r})")
    if facts is not None and not isinstance(facts, dict):
        _refuse("bad_facts", "facts must be a mapping (columns / asset_kind) or None")
    if verdict not in VERDICTS:
        _refuse("bad_verdict", f"verdict must be one of {VERDICTS}")
    if not _nonblank(verified_by):
        _refuse("bad_verified_by", "verified_by is required (who ran the detector)")
    if job_image_tag is not None and not _nonblank(job_image_tag):
        _refuse("bad_job_image_tag", "job_image_tag is null when unknown, never blank")

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
        if criterion_version is not None and criterion_version != entry["revision"]:
            _refuse("bad_criterion_version", f"{criterion} is at revision {entry['revision']}, not {criterion_version!r}")
        det, gate_name = entry["detector"], entry["gate"]
        crit_version, reg_rev, reg_fp = entry["revision"], ac.REGISTRY_REVISION, ac.registry_fingerprint()
    else:
        if not isinstance(criterion, str) or not _ADDITION.fullmatch(criterion) or criterion in ac.CRITERION_REGISTRY:
            _refuse("bad_criterion_id", f"{criterion!r} is not a well-formed addition id (and must not shadow a "
                                        "registered criterion)")
        if gate is not None:
            _refuse("gate_mismatch", "an addition belongs to no gate")
        if isinstance(criterion_version, bool) or not isinstance(criterion_version, int) or criterion_version < 1:
            _refuse("bad_criterion_version", "an addition record carries its brief's revision as an int >= 1")
        det = detector.strip() if _nonblank(detector) else "NONE"
        if det.upper() == "NONE":
            det = "NONE"
        gate_name, crit_version, reg_rev, reg_fp = None, criterion_version, None, None

    # R1: a NONE detector can only honestly be recorded as NO_DETECTOR
    if det == "NONE" and verdict != "NO_DETECTOR":
        _refuse("detector_none", f"{criterion} has detector NONE: nothing measured it, so {verdict} is refused "
                                 "(only NO_DETECTOR can be recorded)")

    # R2: every record names the census run it rests on
    if not isinstance(evidence, dict) or not _valid_run_id(evidence.get("census_run_id")):
        _refuse("no_census_run_id", "evidence must carry census_run_id: the census's tz-aware ISO `generated` "
                                    "timestamp (a record without a run id is not a record)")
    run_id = evidence["census_run_id"]
    unknown = sorted(set(evidence) - set(EVIDENCE_KEYS))
    if unknown or any(not isinstance(v, str) for v in evidence.values()):
        _refuse("bad_evidence", f"evidence keys must be {EVIDENCE_KEYS} with text values (got {unknown or 'non-text'})")

    # census cross-check (optional for PASS/FAIL..., required for a measured-cause N/A)
    meas = None
    if census is not None:
        meas = _census_measurement(census, asset, layer, criterion, run_id)
        if verdict != "N/A":
            if meas is None:
                _refuse("census_mismatch", f"the census holds no measurement of {criterion} for {asset}")
            if meas.get("v") != verdict:
                _refuse("census_mismatch", f"the census measured {meas.get('v')!r} for {asset} {criterion}, "
                                           f"not {verdict!r}")
        if meas is not None:
            inconclusive = bool(inconclusive) or bool(meas.get("inconclusive"))
            if "basis" in meas:
                if basis is not None and basis != meas["basis"]:
                    _refuse("census_mismatch", "basis disagrees with the census measurement")
                basis = meas["basis"]
    if basis is not None and basis != _DECLARATION:
        _refuse("bad_basis", f"unrecognised basis {basis!r} (the only defined basis is {_DECLARATION!r}, case-exact)")

    # R5: what the census rollup itself would not honour
    if kind == "gate" and verdict == "PASS" and (criterion.startswith("Null.") or criterion == "Narr.fidelity_test"):
        _refuse("capped_verdict", f"{criterion} is capped at PARTIAL (Null: never PASS alone; fidelity_test: "
                                  "structural only)")
    if inconclusive and verdict in ("PASS", "PARTIAL"):
        _refuse("inconclusive", "an INCONCLUSIVE measurement established nothing: it cannot be PASS or PARTIAL")
    if kind == "gate" and verdict == "PASS" and facts is not None:
        if ac.criterion_applicability(criterion, layer, facts)["state"] == "NOT_APPLICABLE":
            _refuse("not_applicable_pass", "the supplied facts disprove this criterion's applicability: a measured "
                                           "PASS contradicts the registry")

    # R3: N/A is computed, never typed
    na = None
    if verdict == "N/A":
        if kind != "gate":
            _refuse("na_not_computed", "an addition has no registry applicability rule: its N/A cannot be computed")
        na = _computed_na(criterion, layer, facts if isinstance(facts, dict) else None, na_rule_id, meas,
                          census is not None)

    # R6: what lets the record go stale
    na_measured = na is not None and na["basis"] == "measured_cause"
    if semantic_fingerprint is not None and (not isinstance(semantic_fingerprint, str)
                                             or not _SHA256.fullmatch(semantic_fingerprint)):
        _refuse("bad_fingerprint", "semantic_fingerprint must be 64 lower-case hex (sha256)")
    if semantic_fingerprint is None and (verdict == "PASS" or na_measured):
        _refuse("missing_fingerprint", "a PASS (or measured N/A) read rows: without a semantic fingerprint a "
                                       "change to those rows could never invalidate it")
    wh, wh_reason = _writer_hashes(writer_hashes, writer_hashes_reason, verdict, na_measured)

    cert_key = cert_key_of(asset, kind, criterion)
    ups = _upstream_ids(upstream_cert_ids, cert_key)
    return dict(
        asset=asset, layer=layer, kind=kind, gate=gate_name, criterion=criterion, criterion_version=crit_version,
        registry_revision=reg_rev, registry_fingerprint=reg_fp, detector=det, verdict=verdict, basis=basis, na=na,
        evidence=dict(evidence), job_image_tag=job_image_tag.strip() if job_image_tag else None, writer_hashes=wh,
        writer_hashes_reason=wh_reason, upstream_cert_ids=ups, semantic_fingerprint=semantic_fingerprint,
        cert_key=cert_key, verified_by=verified_by.strip(),
        verified_on=verified_on or dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        record_version=RECORD_VERSION)


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


def write_certification(*, ledger_path=None, init: bool = False, **fields) -> CertResult:
    """Validate, then append one record (or report the identical latest generation). See build_record for the
    fields. The ledger is never rewritten: it is opened for append, under an exclusive lock that also covers the
    read the generation number and the idempotence check depend on."""
    rec = build_record(**fields)
    path = resolve_ledger_path(ledger_path)
    existed = path.exists()
    if not existed and not init:
        _refuse("ledger_missing", f"{path} does not exist (pass init=True / --init to create it)")
    created = False
    try:
        with open(path, "a+b") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            data = f.read()
            created = not existed and not data
            by_key = {} if created else parse_ledger(data)
            _check_upstream(rec, by_key)
            latest = (by_key.get(rec["cert_key"]) or [None])[-1]
            if latest is not None and _identity(latest) == _identity(rec):
                return CertResult("unchanged", latest, latest["cert_id"], path)
            gen = 1 if latest is None else latest["generation"] + 1
            rec = dict(rec, generation=gen, cert_id=f"{rec['cert_key']}@{gen}")
            line = (json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8")
            if created:
                schema = json.dumps({"asset": "_schema", "_doc": SCHEMA_DOC}, ensure_ascii=False) + "\n"
                line = schema.encode("utf-8") + line
            elif not data.endswith(b"\n"):
                line = b"\n" + line
            f.write(line)                  # one write of a fully serialised line, to an append-only descriptor
            f.flush()
            os.fsync(f.fileno())
            return CertResult("appended", rec, rec["cert_id"], path)
    except BaseException:
        if created:                        # a refused request never leaves a ledger behind, even under --init
            path.unlink(missing_ok=True)
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
    ap.add_argument("--verdict", required=True)
    ap.add_argument("--census", default=None, help="the census JSON this verdict was measured in (cross-checked; "
                                                    "supplies the run id when --census-run-id is absent)")
    ap.add_argument("--census-run-id", default=None)
    ap.add_argument("--measured", default=None)
    ap.add_argument("--inspector-commit", default=None)
    ap.add_argument("--job-image-tag", default=None)
    ap.add_argument("--writer-hash", action="append", default=[], metavar="PATH=SHA256")
    ap.add_argument("--writer-file", action="append", default=[], metavar="PATH", help="hash this repo file")
    ap.add_argument("--writer-repo", default=None)
    ap.add_argument("--writer-ref", default=None, help="hash the committed blob at this ref, not the working tree")
    ap.add_argument("--writer-hashes-reason", default=None)
    ap.add_argument("--upstream", action="append", default=[], metavar="CERT_ID")
    ap.add_argument("--semantic-fingerprint", default=None)
    ap.add_argument("--verified-by", default=None)
    ap.add_argument("--verified-on", default=None)
    ap.add_argument("--na-rule-id", default=None)
    ap.add_argument("--facts-json", default=None, help='applicability facts, e.g. {"columns": ["a"], "asset_kind": "data"}')
    ap.add_argument("--basis", default=None)
    ap.add_argument("--inconclusive", action="store_true")
    return ap


def main(argv=None) -> int:
    a = _parser().parse_args(argv)
    try:
        census = json.loads(Path(a.census).read_text(encoding="utf-8")) if a.census else None
        run_id = a.census_run_id or (census.get("generated") if isinstance(census, dict) else None)
        evidence = {k: v for k, v in dict(census_run_id=run_id, measured=a.measured,
                                          inspector_commit=a.inspector_commit,
                                          census_file=a.census).items() if v is not None}
        wh = {}
        for item in a.writer_hash:
            p, sep, h = item.partition("=")
            wh[p] = h
        if a.writer_file:
            wh.update(hash_writer_files(a.writer_file, repo=a.writer_repo, ref=a.writer_ref))
        facts = json.loads(a.facts_json) if a.facts_json else None
        r = write_certification(
            ledger_path=a.ledger, init=a.init, asset=a.asset, layer=a.layer, kind=a.kind, gate=a.gate,
            criterion=a.criterion, criterion_version=a.criterion_version, detector=a.detector, verdict=a.verdict,
            evidence=evidence, census=census, job_image_tag=a.job_image_tag, writer_hashes=wh,
            writer_hashes_reason=a.writer_hashes_reason, upstream_cert_ids=a.upstream,
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
