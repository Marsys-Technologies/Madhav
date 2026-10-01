#!/usr/bin/env python3
"""nikasha_stale_certs.py — Suvarna E5.5: the stale-certification detector (certification currency contract).

Track E brief 7 / arch 12.16. E5.1 (`nikasha_certify.py`) writes certification records; this module decides when one
has gone stale, writes that decision into the same append-only ledger, and records how far it has looked.

  (1) SEMANTIC ROW FINGERPRINT. `fingerprint_rows(rows, declaration)` is sha256 over the asset's rows (already
      scoped to the chart, or global for L0, by the caller) in natural-key order, each row as canonical JSON of its
      declared semantic columns. Volatile columns (surrogate ids, timestamps, build/attempt ids) are excluded AS
      DECLARED PER ASSET; embeddings are compared under a declared rounding policy, never byte-equal. An idempotent
      rebuild that changes no semantic column leaves the fingerprint unchanged. Anything unreadable (a missing
      declared column, a duplicate or NULL natural key, a NaN, bytes, a failed query) RAISES: it never reads as
      "not stale". `load_rows` / `table_fingerprint` are the thin read-only loader: one fixed-shape SELECT built
      from identifiers that passed a regex whitelist, the chart id only ever a bound parameter.
  (2) CERTIFICATE GENERATION IDS. A record is stale when (a) a writer hash it recorded no longer matches,
      (b) its semantic fingerprint no longer matches, or (c) an upstream certificate it cites is no longer the
      latest generation, or is itself stale, invalidated or not passing; (d) optionally, the registry revision moved.
      Staleness propagates down the citation graph in one pass (a citation always points at an earlier line);
      only what changed is invalidated.
  (3) INVALIDATION WATERMARK. `invalidate()` appends invalidation lines and a watermark line to the ledger.
      `watermark_ok` / `current_certificates` refuse a ledger that holds certificates E5.5 has not evaluated, which
      is what `elevated_assets` needs to raise on.
  (4) BOUNDED RE-WALKS. At most `MAX_REWALKS` (2) invalidating walks per (layer, acceptance epoch); the third
      raises `RewalkLimitExceeded` carrying the findings, writes nothing (no watermark either), for Strategic Suvarna.

LEDGER LINE SHAPES. Both are EVENTS in E5.1's vocabulary (`nikasha_certify.append_records` / `parse_records`): a
`type` that is not "cert" and NO `cert_key`. E5.1 chains (`prev_sha256`) and numbers (`seq`) every line and verifies
the whole ledger on every read and write; this module never serialises, hashes or numbers a line itself: every append
goes through `nc.append_records`, every read through `nc.read_records` / `nc.parse_records`. An event is not in E5.1's
certificate index, so it can neither shadow nor be mistaken for a certificate.

  invalidation  {"type": "invalidation", "asset": <asset>, "layer": "L0".."L5", "invalidates": "<cert_id>",
                 "reason": [{"code": "writer_hash"|"semantic_fingerprint"|"registry"|"upstream_generation"|
                             "upstream_stale"|"upstream_not_passing", ...detail}],
                 "walk": <int, one per invalidating run>, "epoch": <acceptance epoch id>,
                 "detected_by": "nikasha_stale_certs.py", "detected_on": <tz-aware ISO>, "record_version": 1,
                 "seq": .., "prev_sha256": ..}
  watermark     {"type": "watermark", "asset": "_ledger", "covers_seq": <E5.1 seq of the last record the evaluation
                 read; 0 for a schema-only ledger>, "certs_processed": <certificates with seq <= covers_seq>,
                 "last_cert_id": <cert_id of the last of them | null>, "commit": <repo commit the evaluation ran at>,
                 "evaluated_on": <tz-aware ISO>, "record_version": 1, "seq": .., "prev_sha256": ..}

The watermark is OK iff the ledger's last watermark line is truthful (`certs_processed` / `last_cert_id` match the
certificates with seq <= `covers_seq`, `covers_seq` is below the line's own seq and not behind the previous watermark)
and NO certificate has seq > `covers_seq`. A certificate appended between this module's read and its append is
therefore simply "behind", never a lie. An invalidated certificate is not current until a new generation is
certified (E5.1). Invalidation and watermark lines are outputs: they never make the watermark behind. A repeated
invalidation of one certificate (two racing runs) is tolerated and counted once; the first wins.

Usage:
  nikasha_stale_certs.py invalidate --ledger L --observed obs.json --epoch E1 --commit <sha> [--max-rewalks 2]
  nikasha_stale_certs.py watermark-ok --ledger L        (or --ref R --repo P [--path ledger path in the repo])
  nikasha_stale_certs.py fingerprint --declarations decl.json --asset A --rows rows.json
obs.json = {"assets": {asset: {"writer_hashes": {path: sha256}, "semantic_fingerprint": sha256}}, "registry"?: {...}}
Exit: 0 ok · 2 refused / watermark not ok (nothing written) · 3 re-walk limit reached (strategist review) · 5 error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import decimal
import hashlib
import json
import math
import re
import subprocess
import sys
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asset_census as ac  # noqa: E402
import nikasha_certify as nc  # noqa: E402  (E5.1: strict ledger reader, id grammar, helpers)

MAX_REWALKS = 2
RECORD_VERSION = 1
DETECTED_BY = "nikasha_stale_certs.py"
CERT_KINDS = ("gate", "addition")
EVENT_TYPES = ("invalidation", "watermark")
PASSING = ("PASS", "N/A")
DEFAULT_LEDGER_IN_REPO = "00_ARCHITECTURE/control/asset_certs.jsonl"

_IDENT = re.compile(r"[a-z_][a-z0-9_]{0,62}")          # the whitelist: lower-case SQL-safe identifiers, never quoted-through
_ASSET = re.compile(r"[a-z][a-z0-9_]*")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/@^~{}-]*")  # a git ref/sha; never starts with '-', so never an option
_SHA256 = re.compile(r"[0-9a-f]{64}")
_VECTOR_TEXT = re.compile(r"\s*\[(.*)\]\s*", re.S)
_DECL_KEYS = ("table", "scope", "scope_column", "natural_key", "semantic_columns", "volatile_columns",
              "embedding_policy")
_POLICY_KEYS = ("decimals",)
MAX_DECIMALS = 12
FETCH_CHUNK = 5000


# ─────────────────────────── errors ───────────────────────────

class StaleCertsError(ValueError):
    """Refused or unreadable; nothing was written. `code` is the stable, test-pinned slug."""
    default_code = "stale_certs_error"

    def __init__(self, message: str, code: str | None = None):
        self.code = code or self.default_code
        self.message = message
        super().__init__(f"{self.code}: {message}")


class UnreadableInput(StaleCertsError):
    default_code = "unreadable_input"


class MissingObservation(UnreadableInput):
    default_code = "missing_observation"


class BadDeclaration(StaleCertsError):
    default_code = "bad_declaration"


class LedgerShapeError(StaleCertsError):
    default_code = "bad_ledger"


class WatermarkBehind(StaleCertsError):
    default_code = "watermark_behind"


class RewalkLimitExceeded(StaleCertsError):
    default_code = "rewalk_limit"

    def __init__(self, layer: str, epoch: str, walks: int, stale: dict, limit: int = MAX_REWALKS):
        self.layer, self.epoch, self.walks, self.stale, self.limit = layer, epoch, walks, stale, limit
        super().__init__(f"layer {layer} epoch {epoch!r} already has {walks} invalidating walk(s) (limit {limit}); "
                         f"{len(stale)} certificate(s) found stale: {sorted(stale)}. Strategic Suvarna reviews the "
                         "cause before any further rebuild; nothing was written")


def _nonblank(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


# ═══════════════ (1) declarations and the semantic row fingerprint ═══════════════

def _ident_list(v, what: str, asset: str, allow_empty=False) -> list[str]:
    if not isinstance(v, (list, tuple)) or (not v and not allow_empty):
        raise BadDeclaration(f"{asset}: {what} must be a non-empty list of identifiers")
    out = []
    for x in v:
        if not isinstance(x, str) or not _IDENT.fullmatch(x):
            raise BadDeclaration(f"{asset}: {what} entry {x!r} is not a lower-case identifier [a-z_][a-z0-9_]*")
        if x in out:
            raise BadDeclaration(f"{asset}: {what} lists {x!r} twice")
        out.append(x)
    return out


def validate_declaration(decl, asset: str = "<asset>") -> dict:
    """The normalised declaration of ONE asset (idempotent on its own output). Required: `table`, `scope`
    ('chart' | 'global'), `natural_key`, and exactly one of `semantic_columns` / `volatile_columns`. Optional:
    `scope_column` (default chart_id), `embedding_policy` {column: {"decimals": 0..12}}. Raises BadDeclaration."""
    if not isinstance(decl, Mapping):
        raise BadDeclaration(f"{asset}: a declaration must be a mapping")
    unknown = sorted(set(decl) - set(_DECL_KEYS))
    if unknown:
        raise BadDeclaration(f"{asset}: unknown declaration key(s) {unknown}")
    table = decl.get("table")
    if not isinstance(table, str) or not _IDENT.fullmatch(table):
        raise BadDeclaration(f"{asset}: table {table!r} is not a lower-case identifier")
    scope = decl.get("scope")
    if scope not in ("chart", "global"):
        raise BadDeclaration(f"{asset}: scope must be 'chart' or 'global'")
    scope_column = decl.get("scope_column", "chart_id")
    if not isinstance(scope_column, str) or not _IDENT.fullmatch(scope_column):
        raise BadDeclaration(f"{asset}: scope_column {scope_column!r} is not an identifier")
    key = _ident_list(decl.get("natural_key"), "natural_key", asset)
    sem, vol = decl.get("semantic_columns"), decl.get("volatile_columns")
    if (sem is None) == (vol is None):
        raise BadDeclaration(f"{asset}: declare exactly one of semantic_columns / volatile_columns")
    sem = _ident_list(sem, "semantic_columns", asset) if sem is not None else None
    vol = _ident_list(vol, "volatile_columns", asset, allow_empty=True) if vol is not None else None
    if vol is not None and set(key) & set(vol):
        raise BadDeclaration(f"{asset}: natural_key column(s) {sorted(set(key) & set(vol))} are declared volatile")
    pol = decl.get("embedding_policy") or {}
    if not isinstance(pol, Mapping):
        raise BadDeclaration(f"{asset}: embedding_policy must be a mapping")
    norm_pol = {}
    for col, p in pol.items():
        if not isinstance(col, str) or not _IDENT.fullmatch(col):
            raise BadDeclaration(f"{asset}: embedding column {col!r} is not an identifier")
        if not isinstance(p, Mapping) or set(p) != set(_POLICY_KEYS):
            raise BadDeclaration(f"{asset}: embedding policy of {col} must be exactly {{'decimals': int}}")
        d = p["decimals"]
        if isinstance(d, bool) or not isinstance(d, int) or not 0 <= d <= MAX_DECIMALS:
            raise BadDeclaration(f"{asset}: embedding decimals of {col} must be an int in 0..{MAX_DECIMALS}")
        if vol is not None and (col in vol or col in key):
            raise BadDeclaration(f"{asset}: embedding column {col} is volatile or the key")
        if sem is not None and col not in sem:
            raise BadDeclaration(f"{asset}: embedding column {col} is not among semantic_columns")
        norm_pol[col] = dict(decimals=d)
    return dict(table=table, scope=scope, scope_column=scope_column, natural_key=key, semantic_columns=sem,
                volatile_columns=vol, embedding_policy=norm_pol)


def validate_declarations(doc) -> dict[str, dict]:
    """{asset_id: declaration} -> {asset_id: normalised declaration}; every bad one is named."""
    if not isinstance(doc, Mapping):
        raise BadDeclaration("declarations must be a mapping of asset id -> declaration")
    out = {}
    for asset, d in doc.items():
        if not isinstance(asset, str) or not _ASSET.fullmatch(asset):
            raise BadDeclaration(f"{asset!r} is not an asset id")
        out[asset] = validate_declaration(d, asset)
    return out


def _canon(v, path: str):
    """A JSON-able canonical form of a database value; raises UnreadableInput for what has none."""
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):
        if not math.isfinite(v):
            raise UnreadableInput(f"{path}: non-finite float {v!r}")
        return v
    if isinstance(v, decimal.Decimal):
        if not v.is_finite():
            raise UnreadableInput(f"{path}: non-finite Decimal")
        return {"$decimal": format(v.normalize(), "f")}
    if isinstance(v, (dt.datetime, dt.date, dt.time)):
        return v.isoformat()
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, (list, tuple)):
        return [_canon(x, path) for x in v]
    if isinstance(v, Mapping):
        if not all(isinstance(k, str) for k in v):
            raise UnreadableInput(f"{path}: non-text key in a mapping value")
        return {k: _canon(x, path) for k, x in v.items()}
    raise UnreadableInput(f"{path}: {type(v).__name__} has no canonical form")


def _vector(v, decimals: int, path: str) -> list[float]:
    """An embedding under the declared equivalence: each component rounded to `decimals` places (-0.0 -> 0.0).
    Accepts a list/tuple of numbers or a pgvector-style text '[a,b,c]'."""
    if isinstance(v, str):
        m = _VECTOR_TEXT.fullmatch(v)
        if m is None:
            raise UnreadableInput(f"{path}: not a vector literal")
        try:
            v = [float(x) for x in m.group(1).split(",")] if m.group(1).strip() else []
        except ValueError:
            raise UnreadableInput(f"{path}: not a vector literal") from None
    if not isinstance(v, (list, tuple)):
        raise UnreadableInput(f"{path}: an embedding must be a list of numbers or a vector literal")
    out = []
    for x in v:
        if isinstance(x, bool) or not isinstance(x, (int, float, decimal.Decimal)):
            raise UnreadableInput(f"{path}: non-numeric embedding component {x!r}")
        f = float(x)
        if not math.isfinite(f):
            raise UnreadableInput(f"{path}: non-finite embedding component")
        out.append(round(f, decimals) + 0.0)
    return out


def _dumps(x) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint_rows(rows, decl) -> str:
    """sha256 hex of the asset's semantic content. See the module docstring; raises UnreadableInput on any input
    that cannot be fingerprinted honestly."""
    d = validate_declaration(decl)
    if rows is None or isinstance(rows, (str, bytes, Mapping)):
        raise UnreadableInput("rows must be an iterable of row mappings")
    try:
        rows = list(rows)
    except TypeError:
        raise UnreadableInput("rows must be an iterable of row mappings") from None
    key, sem, vol, pol = d["natural_key"], d["semantic_columns"], d["volatile_columns"], d["embedding_policy"]
    shape = None
    if vol is not None and rows:
        for i, r in enumerate(rows):
            if not isinstance(r, Mapping):
                raise UnreadableInput(f"row {i} is not a mapping")
            ks = frozenset(r)
            if shape is None:
                shape = ks
            elif ks != shape:
                raise UnreadableInput(f"row {i} has a different column set from row 0 (volatile mode needs one)")
        columns = sorted(shape - set(vol))
    elif vol is not None:
        columns = []
    else:
        columns = sorted(set(key) | set(sem))
    keyed = []
    for i, r in enumerate(rows):
        if not isinstance(r, Mapping):
            raise UnreadableInput(f"row {i} is not a mapping")
        missing = [c for c in set(columns) | set(key) if c not in r]
        if missing:
            raise UnreadableInput(f"row {i} lacks declared column(s) {sorted(missing)}")
        kv = []
        for k in key:
            if r[k] is None:
                raise UnreadableInput(f"row {i}: natural key column {k} is NULL")
            kv.append(_canon(r[k], f"row {i}.{k}"))
        payload = {}
        for c in columns:
            payload[c] = (_vector(r[c], pol[c]["decimals"], f"row {i}.{c}") if c in pol
                          else _canon(r[c], f"row {i}.{c}"))
        keyed.append((_dumps(kv), _dumps(payload)))
    keyed.sort()
    for a, b in zip(keyed, keyed[1:]):
        if a[0] == b[0]:
            raise UnreadableInput(f"natural key {a[0]} occurs more than once: the declared key is not a key")
    header = _dumps(dict(v=1, natural_key=key, mode="semantic" if sem is not None else "volatile",
                         columns=sorted(sem if sem is not None else vol), embedding_policy=pol))
    h = hashlib.sha256()
    h.update(header.encode("utf-8") + b"\n")
    for _k, line in keyed:
        h.update(_k.encode("utf-8") + b"\t" + line.encode("utf-8") + b"\n")
    return h.hexdigest()


# ─────────────────────────── the read-only loader ───────────────────────────

def build_select(decl) -> str:
    """The ONE SELECT this module ever issues, in one of three fixed shapes (explicit columns, `*`, with or without
    the chart scope). Every identifier already matched the lower-case whitelist, so double-quoting cannot be
    escaped; the chart id is the `%s` parameter, never text."""
    d = validate_declaration(decl)
    if d["semantic_columns"] is not None:
        cols = list(d["natural_key"]) + [c for c in d["semantic_columns"] if c not in d["natural_key"]]
        select = "SELECT " + ", ".join(f'"{c}"' for c in cols)
    else:
        select = "SELECT *"
    sql = f'{select} FROM "{d["table"]}"'
    if d["scope"] == "chart":
        sql += f' WHERE "{d["scope_column"]}" = %s'
    return sql


def load_rows(conn, decl, chart_id=None) -> list[dict]:
    """Read the asset's rows through an open DB-API connection: one parameterised SELECT, no commit, no write.
    A query failure or a result with no column description raises UnreadableInput; it never returns [] for it."""
    d = validate_declaration(decl)
    if d["scope"] == "chart":
        if not _nonblank(chart_id):
            raise UnreadableInput("a chart-scoped asset needs a chart_id")
        params = (chart_id,)
    else:
        if chart_id is not None:
            raise UnreadableInput("a global (L0) asset is fingerprinted without a chart_id")
        params = None
    sql = build_select(d)
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(sql, params) if params is not None else cur.execute(sql)
        desc = cur.description
        if not desc:
            raise UnreadableInput("the query returned no column description")
        cols = [c[0] for c in desc]
        rows = []
        while True:
            batch = cur.fetchmany(FETCH_CHUNK)
            if not batch:
                break
            for r in batch:
                if len(r) != len(cols):
                    raise UnreadableInput("a result row does not match its column description")
                rows.append(dict(zip(cols, r)))
        return rows
    except StaleCertsError:
        raise
    except Exception as e:  # noqa: BLE001 — any driver failure is "could not read", never "nothing there"
        raise UnreadableInput(f"could not read {d['table']}: {type(e).__name__}: {e}") from e
    finally:
        if cur is not None and hasattr(cur, "close"):
            try:
                cur.close()
            except Exception:  # noqa: BLE001
                pass


def table_fingerprint(conn, decl, chart_id=None) -> str:
    d = validate_declaration(decl)
    return fingerprint_rows(load_rows(conn, d, chart_id), d)


# ═══════════════ ledger reading ═══════════════

@dataclass
class Ledger:
    certs: list = field(default_factory=list)            # certificate records in file order (each carries E5.1's seq)
    pos: dict = field(default_factory=dict)              # cert_id -> index in certs
    by_key: dict = field(default_factory=dict)           # cert_key -> [records] in generation order
    invs: list = field(default_factory=list)
    inv_targets: dict = field(default_factory=dict)      # invalidated cert_id -> first invalidation record
    wms: list = field(default_factory=list)
    last_seq: int = 0                                    # seq of the last record line (0: schema row only)

    @property
    def cert_count(self) -> int:
        return len(self.certs)


def _as_bytes(data) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode("utf-8")
    raise UnreadableInput("ledger content must be bytes or str")


def _wrap(e: "nc.CertificationRefused") -> StaleCertsError:
    """E5.1's refusal, as this module's error (its code is kept: bad_ledger, torn_ledger, ledger_missing, ...)."""
    if e.code in ("ledger_missing", "bad_ledger_path"):
        return UnreadableInput(e.message, e.code)
    return LedgerShapeError(e.message, e.code)


def parse_events(data) -> Ledger:
    """Strict ledger parse for E5.5 / E6.3: E5.1's `parse_records` first (chain, seq, generations, torn tail), then
    the E5.5 event shapes and the watermark's truthfulness. Raises LedgerShapeError."""
    try:
        records = nc.parse_records(_as_bytes(data))
    except nc.CertificationRefused as e:
        raise _wrap(e) from e
    return _ledger_from_records(records)


def _ledger_from_records(records: list) -> Ledger:
    lg = Ledger()
    for r in records:
        n = r["seq"]
        if "cert_key" in r:
            if r.get("kind") not in CERT_KINDS:
                raise LedgerShapeError(f"seq {n}: a certificate of kind {r.get('kind')!r}")
            lg.pos[r["cert_id"]] = len(lg.certs)
            lg.certs.append(r)
            lg.by_key.setdefault(r["cert_key"], []).append(r)
        elif r.get("type") == "invalidation":
            _check_invalidation(r, lg, n)
            lg.invs.append(r)
            lg.inv_targets.setdefault(r["invalidates"], r)
        elif r.get("type") == "watermark":
            _check_watermark_line(r, lg, n)
            lg.wms.append(r)
        else:
            raise LedgerShapeError(f"seq {n}: unknown event type {r.get('type')!r}")
        lg.last_seq = n
    return lg


def _check_invalidation(r: dict, lg: Ledger, n: int) -> None:
    t = r.get("invalidates")
    if not isinstance(t, str) or t not in lg.pos:
        raise LedgerShapeError(f"seq {n}: invalidates {t!r}, which is not a certificate earlier in the ledger")
    target = lg.certs[lg.pos[t]]
    if r.get("asset") != target["asset"] or r.get("layer") != target.get("layer") or r.get("layer") not in ac.LAYERS:
        raise LedgerShapeError(f"seq {n}: invalidation does not agree with the certificate it invalidates")
    w = r.get("walk")
    reason = r.get("reason")
    if (isinstance(w, bool) or not isinstance(w, int) or w < 1 or not _nonblank(r.get("epoch"))
            or not isinstance(reason, list) or not reason
            or not all(isinstance(x, dict) and _nonblank(x.get("code")) for x in reason)):
        raise LedgerShapeError(f"seq {n}: invalidation needs walk >= 1, an epoch and a non-empty reason list")


def _check_watermark_line(r: dict, lg: Ledger, n: int) -> None:
    cov, ep, last = r.get("covers_seq"), r.get("certs_processed"), r.get("last_cert_id")
    if (r.get("asset") != "_ledger" or not _nonblank(r.get("commit")) or isinstance(cov, bool)
            or not isinstance(cov, int) or isinstance(ep, bool) or not isinstance(ep, int)):
        raise LedgerShapeError(f"seq {n}: malformed watermark line")
    covered = [c for c in lg.certs if c["seq"] <= cov]
    want_last = covered[-1]["cert_id"] if covered else None
    if cov < 0 or cov >= n or (lg.wms and cov < lg.wms[-1]["covers_seq"]):
        raise LedgerShapeError(f"seq {n}: watermark covers_seq {cov} is outside 0..{n - 1} or behind the previous watermark")
    if ep != len(covered) or last != want_last:
        raise LedgerShapeError(f"seq {n}: the watermark claims {ep} certificate(s) ending {last!r} up to seq {cov} but "
                               f"the ledger holds {len(covered)} ending {want_last!r}: a watermark that miscounts is a lie")


def _as_ledger(data) -> Ledger:
    return data if isinstance(data, Ledger) else parse_events(data)


# ═══════════════ (2) detection ═══════════════

@dataclass
class Evaluation:
    stale: dict            # cert_id -> [reason dicts], file order (new findings only)
    current: list          # cert_ids of latest, passing, not-invalidated, not-stale certificates
    invalidated: list      # cert_ids of latest certificates that already carry an invalidation line
    not_certificates: list  # cert_ids of latest records that do not pass (FAIL, PARTIAL, ...)
    flags: dict = field(default_factory=dict)   # cert_id -> [flag] for current certificates that carry a caveat


def certificate_flags(rec: dict) -> list[str]:
    """Caveats a CURRENT certificate carries (never a reason to drop it): the census it cites is not yet committed at
    HEAD (`census_git` staged / unknown); the writer hashes were typed rather than verified; the record was not census
    cross-checked; the census cell was transitive_only / inconclusive; the verdict is a PASS by declaration."""
    out = []
    if rec.get("kind") == "gate" and (rec.get("evidence") or {}).get("census_git") != "committed":
        out.append("census_not_committed")
    if rec.get("writer_hashes") and rec.get("writer_hashes_verified") is not True:
        out.append("writer_hashes_unverified")
    if rec.get("kind") == "gate" and rec.get("cross_checked") is not True:
        out.append("not_cross_checked")
    if rec.get("transitive_only") is True:
        out.append("transitive_only")
    if rec.get("inconclusive") is True:
        out.append("inconclusive")
    if rec.get("basis") == "declaration":
        out.append("basis_declaration")
    return out


def _observation(observed, asset: str, rec: dict):
    """(writer_hashes_observed | None, fingerprint_observed | None), raising where the record needs what was not
    supplied or was malformed. A record that records no hashes and no fingerprint needs no observation."""
    wants_wh, wants_fp = bool(rec.get("writer_hashes")), rec.get("semantic_fingerprint") is not None
    if not (wants_wh or wants_fp):
        return None, None
    o = observed.get(asset)
    if not isinstance(o, Mapping):
        raise MissingObservation(f"no observation for {asset}, which holds certificate {rec['cert_id']}")
    wh = fp = None
    if wants_wh:
        if "writer_hashes" not in o:
            raise MissingObservation(f"{asset}: writer_hashes not observed")
        wh = o["writer_hashes"]
        if not isinstance(wh, Mapping) or not all(isinstance(p, str) and isinstance(h, str) and _SHA256.fullmatch(h)
                                                  for p, h in wh.items()):
            raise UnreadableInput(f"{asset}: observed writer_hashes must map path -> lower-case sha256")
        absent = [p for p in rec["writer_hashes"] if p not in wh]
        if absent:
            raise MissingObservation(f"{asset}: writer file(s) {absent} not observed")
    if wants_fp:
        if "semantic_fingerprint" not in o:
            raise MissingObservation(f"{asset}: semantic_fingerprint not observed")
        fp = o["semantic_fingerprint"]
        if not isinstance(fp, str) or not _SHA256.fullmatch(fp):
            raise UnreadableInput(f"{asset}: observed semantic_fingerprint is not 64 lower-case hex ({fp!r})")
    return wh, fp


def _evaluate(lg: Ledger, observed, registry=None) -> Evaluation:
    if not isinstance(observed, Mapping):
        raise UnreadableInput("observed must be a mapping of asset -> observation")
    if registry is not None and not (isinstance(registry, Mapping) and isinstance(registry.get("revision"), int)
                                     and isinstance(registry.get("fingerprint"), str)):
        raise UnreadableInput("registry observation must be {revision: int, fingerprint: str}")
    ev = Evaluation(stale={}, current=[], invalidated=[], not_certificates=[])
    status: dict[str, str] = {}
    for i, rec in enumerate(lg.certs):
        cid = rec["cert_id"]
        if lg.by_key[rec["cert_key"]][-1] is not rec:
            continue                                            # superseded generation
        if cid in lg.inv_targets:
            status[cid] = "invalidated"
            ev.invalidated.append(cid)
            continue
        if rec["verdict"] not in PASSING:
            status[cid] = "not_cert"
            ev.not_certificates.append(cid)
            continue
        reasons = []
        wh, fp = _observation(observed, rec["asset"], rec)
        if wh is not None:
            for p, recorded in rec["writer_hashes"].items():
                if wh[p] != recorded:
                    reasons.append(dict(code="writer_hash", path=p, recorded=recorded, observed=wh[p]))
        if fp is not None and fp != rec["semantic_fingerprint"]:
            reasons.append(dict(code="semantic_fingerprint", recorded=rec["semantic_fingerprint"], observed=fp))
        if registry is not None and rec["kind"] == "gate" and (
                rec.get("registry_revision") != registry["revision"]
                or rec.get("registry_fingerprint") != registry["fingerprint"]):
            reasons.append(dict(code="registry",
                                recorded=dict(revision=rec.get("registry_revision"),
                                              fingerprint=rec.get("registry_fingerprint")),
                                observed=dict(revision=registry["revision"], fingerprint=registry["fingerprint"])))
        for u in rec.get("upstream_cert_ids") or []:
            m = nc._CERT_ID.fullmatch(u) if isinstance(u, str) else None
            if m is None:
                raise LedgerShapeError(f"{cid}: upstream id {u!r} is not a cert id")
            if u not in lg.pos or lg.pos[u] >= i:
                raise LedgerShapeError(f"{cid}: cites {u}, which is not a certificate on an earlier line")
            ukey = nc.cert_key_of(m.group(1), m.group(2), m.group(3))
            latest = lg.by_key[ukey][-1]
            if latest["generation"] != int(m.group(4)):
                reasons.append(dict(code="upstream_generation", upstream=u, cited=int(m.group(4)),
                                    latest=latest["generation"]))
                continue
            st = status.get(latest["cert_id"])
            if st == "not_cert":
                reasons.append(dict(code="upstream_not_passing", upstream=u, verdict=latest["verdict"]))
            elif st in ("invalidated", "stale"):
                reasons.append(dict(code="upstream_stale", upstream=u, why=st if st == "stale" else "invalidated"))
        if reasons:
            status[cid] = "stale"
            ev.stale[cid] = reasons
        else:
            status[cid] = "current"
            ev.current.append(cid)
            fl = certificate_flags(rec)
            if fl:
                ev.flags[cid] = fl
    return ev


def evaluate(data, observed, registry=None) -> Evaluation:
    """Pure: which latest certificates are stale given what is observed NOW. `observed` = {asset:
    {"writer_hashes": {path: sha256}, "semantic_fingerprint": sha256}}. Raises (MissingObservation /
    UnreadableInput / LedgerShapeError) rather than guess: an unobserved asset is never read as unchanged."""
    return _evaluate(_as_ledger(data), observed, registry)


# ═══════════════ (3) watermark ═══════════════

def watermark_status(data) -> dict:
    lg = _as_ledger(data)
    wm = lg.wms[-1] if lg.wms else None
    cov = wm["covers_seq"] if wm else 0
    unevaluated = sum(1 for c in lg.certs if c["seq"] > cov)
    return dict(ok=wm is not None and unevaluated == 0, watermark=wm, unevaluated=unevaluated,
                reason=("no watermark: E5.5 has never evaluated this ledger" if wm is None else
                        (f"{unevaluated} certificate record(s) follow the watermark" if unevaluated else "ok")))


def watermark_ok(data) -> bool:
    """True iff E5.5 has evaluated every certificate in this ledger (its last watermark is truthful and no
    certificate follows it). Raises LedgerShapeError on a ledger it cannot read."""
    return watermark_status(data)["ok"]


def read_ledger_at_ref(ref: str, repo, path: str = DEFAULT_LEDGER_IN_REPO) -> bytes:
    """`git -C repo show ref:path`: the COMMITTED ledger, never the working tree. The ref may not start with '-'
    and the path must be repo-relative; any failure raises UnreadableInput."""
    if not isinstance(ref, str) or not _REF.fullmatch(ref):
        raise UnreadableInput(f"{ref!r} is not a git ref")
    if not nc._check_relpath(path):
        raise UnreadableInput(f"{path!r} is not a repo-relative path")
    r = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"], capture_output=True)
    if r.returncode != 0:
        raise UnreadableInput(f"cannot read {path} at {ref} in {repo}")
    return r.stdout


def watermark_ok_at_ref(ref: str, repo, path: str = DEFAULT_LEDGER_IN_REPO) -> bool:
    return watermark_ok(read_ledger_at_ref(ref, repo, path))


class CurrentCertificates(dict):
    """cert_key -> record, plus `.flags` {cert_key: [caveat, ...]} (see `certificate_flags`): a flagged certificate
    is still current, never dropped."""
    flags: dict


def current_certificates(data, require_watermark: bool = True) -> CurrentCertificates:
    """cert_key -> the latest record of every key whose latest generation passes and is not invalidated. Raises
    LedgerShapeError on a ledger whose hash chain does not hold, and WatermarkBehind unless the watermark covers
    every certificate (`require_watermark=False` is for E5.5 itself). Records are returned as written; caveats are
    in `.flags`."""
    lg = _as_ledger(data)
    if require_watermark:
        st = watermark_status(lg)
        if not st["ok"]:
            raise WatermarkBehind(st["reason"])
    out = CurrentCertificates((k, recs[-1]) for k, recs in lg.by_key.items()
                              if recs[-1]["verdict"] in PASSING and recs[-1]["cert_id"] not in lg.inv_targets)
    out.flags = {k: fl for k, r in out.items() if (fl := certificate_flags(r))}
    return out


# ═══════════════ (4) bounded re-walks ═══════════════

def rewalk_counts(data) -> dict:
    """{(layer, epoch): number of distinct invalidating walks}."""
    lg = _as_ledger(data)
    walks: dict = {}
    for r in lg.invs:
        walks.setdefault((r["layer"], r["epoch"]), set()).add(r["walk"])
    return {k: len(v) for k, v in walks.items()}


@dataclass(frozen=True)
class InvalidateResult:
    status: str                 # "appended" | "unchanged"
    invalidated: list           # cert_ids invalidated by this run
    walk: int | None
    watermark: dict | None
    ledger_path: Path


def invalidate(ledger_path, observed, *, epoch, commit, registry=None, now=None,
               max_rewalks: int = MAX_REWALKS) -> InvalidateResult:
    """Evaluate, then append (through `nc.append_records`: one atomic, chained, numbered write) one invalidation line
    per newly stale certificate and a watermark line. Idempotent: if nothing is newly stale and the watermark already
    covers the ledger, nothing is appended and no walk is used. Raises RewalkLimitExceeded, before writing, when any
    layer touched already has `max_rewalks` invalidating walks in this epoch. The read (shared lock) and the append
    (exclusive lock) are separate E5.1 calls: a certificate that lands between them is covered by neither this
    run's evaluation nor its watermark (`covers_seq`), so it reads as "behind", never as evaluated."""
    if not _nonblank(epoch):
        raise StaleCertsError("epoch is required (the acceptance epoch id)", "bad_epoch")
    if not _nonblank(commit):
        raise StaleCertsError("commit is required (the repo commit this evaluation ran at)", "bad_commit")
    if isinstance(max_rewalks, bool) or not isinstance(max_rewalks, int) or max_rewalks < 1:
        raise StaleCertsError("max_rewalks must be an int >= 1", "bad_max_rewalks")
    path = nc.resolve_ledger_path(ledger_path)
    stamp = now or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        lg = _ledger_from_records(nc.read_records(path))
    except nc.CertificationRefused as e:
        raise _wrap(e) from e
    ev = _evaluate(lg, observed, registry)
    layers = {}
    for cid in ev.stale:
        layers.setdefault(lg.certs[lg.pos[cid]]["layer"], []).append(cid)
    counts = rewalk_counts(lg)
    for layer in sorted(layers):
        if counts.get((layer, epoch), 0) >= max_rewalks:
            raise RewalkLimitExceeded(layer, epoch, counts[(layer, epoch)], ev.stale, max_rewalks)
    if not ev.stale and watermark_status(lg)["ok"]:
        return InvalidateResult("unchanged", [], None, None, path)
    walk = (max((r["walk"] for r in lg.invs), default=0) + 1) if ev.stale else None
    out = []
    for cid, reasons in ev.stale.items():
        t = lg.certs[lg.pos[cid]]
        out.append(dict(type="invalidation", asset=t["asset"], layer=t["layer"], invalidates=cid, reason=reasons,
                        walk=walk, epoch=epoch, detected_by=DETECTED_BY, detected_on=stamp,
                        record_version=RECORD_VERSION))
    wm = dict(type="watermark", asset="_ledger", covers_seq=lg.last_seq, certs_processed=lg.cert_count,
              last_cert_id=lg.certs[-1]["cert_id"] if lg.certs else None, commit=commit, evaluated_on=stamp,
              record_version=RECORD_VERSION)
    try:
        nc.append_records(path, out + [wm])
    except nc.CertificationRefused as e:
        raise _wrap(e) from e
    return InvalidateResult("appended", list(ev.stale), walk, wm, path)


# ═══════════════ CLI ═══════════════

def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="E5.5 stale-certification detector")
    sub = ap.add_subparsers(dest="cmd", required=True)
    inv = sub.add_parser("invalidate")
    inv.add_argument("--ledger", default=None)
    inv.add_argument("--observed", required=True, help="JSON: {assets: {...}, registry?: {...}}")
    inv.add_argument("--epoch", required=True)
    inv.add_argument("--commit", required=True)
    inv.add_argument("--max-rewalks", type=int, default=MAX_REWALKS)
    inv.add_argument("--now", default=None)
    wm = sub.add_parser("watermark-ok")
    wm.add_argument("--ledger", default=None)
    wm.add_argument("--ref", default=None, help="read the COMMITTED ledger at this git ref instead of the file")
    wm.add_argument("--repo", default=None)
    wm.add_argument("--path", default=DEFAULT_LEDGER_IN_REPO)
    fp = sub.add_parser("fingerprint")
    fp.add_argument("--declarations", required=True)
    fp.add_argument("--asset", required=True)
    fp.add_argument("--rows", required=True, help="JSON list of row objects (already chart-scoped)")
    return ap


def main(argv=None) -> int:
    a = _parser().parse_args(argv)
    try:
        if a.cmd == "invalidate":
            doc = json.loads(Path(a.observed).read_text(encoding="utf-8"))
            r = invalidate(a.ledger, doc.get("assets", {}), epoch=a.epoch, commit=a.commit,
                           registry=doc.get("registry"), now=a.now, max_rewalks=a.max_rewalks)
            print(json.dumps(dict(status=r.status, invalidated=r.invalidated, walk=r.walk, ledger=str(r.ledger_path))))
            return 0
        if a.cmd == "watermark-ok":
            data = (read_ledger_at_ref(a.ref, a.repo or nc.ac.ROOT, a.path) if a.ref
                    else _as_bytes(nc.resolve_ledger_path(a.ledger).read_bytes()))
            st = watermark_status(data)
            print(json.dumps(dict(ok=st["ok"], unevaluated=st["unevaluated"], reason=st["reason"])))
            return 0 if st["ok"] else 2
        decls = validate_declarations(json.loads(Path(a.declarations).read_text(encoding="utf-8")))
        if a.asset not in decls:
            raise BadDeclaration(f"{a.asset} is not declared")
        rows = json.loads(Path(a.rows).read_text(encoding="utf-8"))
        print(json.dumps(dict(asset=a.asset, semantic_fingerprint=fingerprint_rows(rows, decls[a.asset]))))
        return 0
    except RewalkLimitExceeded as e:
        print(f"REFUSED {e.code}: {e.message} [layer={e.layer}]", file=sys.stderr)
        return 3
    except StaleCertsError as e:
        print(f"REFUSED {e.code}: {e.message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"nikasha_stale_certs: script error — {exc}", file=sys.stderr)
        sys.exit(5)
