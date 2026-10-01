#!/usr/bin/env python3
"""nikasha_stale_certs.py — Suvarna E5.5: the stale-certification detector (certification currency contract).

Track E brief 7 / arch 12.16. E5.1 (`nikasha_certify.py`) writes certification records; this module decides when one
has gone stale, writes that decision into the same append-only ledger, and records how far it has looked.

  (1) SEMANTIC ROW FINGERPRINT. `fingerprint_rows(rows, declaration)` is sha256 over the asset's rows (already
      scoped to the chart, or global for L0, by the caller) in natural-key order, each row as canonical JSON of its
      declared semantic columns, under a header that hashes the declaration itself (table, scope, key, mode, columns,
      embeddings). Volatile columns (surrogate ids, timestamps, build/attempt ids) are excluded AS DECLARED PER
      ASSET. EMBEDDINGS ARE NOT HASHED: a vector is a float cloud (1e-7 of noise flips a rounded digit in a third of
      rows), so an embedding column is excluded and the fingerprint covers its SOURCE columns plus the declared
      `model_id` (`embedding: {column, source_columns, model_id}`); a NULL embedding is fine. Canonical form: aware
      datetimes in UTC (naive ones are refused unless the column is declared `naive_utc_columns`), -0.0 and
      Decimal('-0') as zero, Decimals exact at any precision, jsonb objects that look like our markers escaped, text
      with an unpaired surrogate refused. An idempotent rebuild that changes no semantic column leaves the
      fingerprint unchanged. Anything unreadable (a missing declared column, a duplicate or NULL natural key, a NaN,
      bytes, a failed query) RAISES: it never reads as "not stale". `load_rows` / `table_fingerprint` are the thin
      read-only loader: one fixed-shape SELECT built from identifiers that passed a regex whitelist, the chart id
      only ever a bound parameter.
  (2) CERTIFICATE GENERATION IDS. A record is stale when (a) a writer hash it recorded no longer matches, or the
      asset's writer file set gained or lost a file, (b) its semantic fingerprint no longer matches, (c) an upstream
      certificate it cites is no longer the latest generation (unless the latest carries the SAME semantic
      fingerprint and is itself current: a generation bump with identical output invalidates nothing downstream), or
      is itself stale, invalidated or not passing; (d) the registry moved, for the assets the caller names (a
      registry observation without `assets` is refused: a revision bump must not invalidate every gate certificate).
      Staleness propagates down the citation graph; only what changed is invalidated.
  (3) INVALIDATION WATERMARK. `invalidate()` appends invalidation events and a watermark event to the ledger.
      `watermark_ok` / `current_certificates` refuse a ledger that holds certificates E5.5 has not evaluated, which
      is what `elevated_assets` needs to raise on. `observed_at_seq` (the chain head taken BEFORE observing) caps what
      one run claims to have covered.
  (4) BOUNDED RE-WALKS. At most `MAX_REWALKS` (2, a constant, not an argument) invalidating walks per layer over the
      WHOLE ledger; the third raises `RewalkLimitExceeded` carrying the findings, writes nothing (no watermark
      either), for Strategic Suvarna. The count restarts for one layer only at an `epoch_reset` event, written by
      `new_epoch()` / `new-epoch --layer L --decision N-xx`: that is the STRATEGIST'S act (the decision id is
      recorded; the ledger and git history are the audit, the tool cannot know who is typing).

LEDGER LINE SHAPES. All are EVENTS in E5.1's vocabulary (`nikasha_certify.append_records` / `parse_records`): a
`type` that is not "cert" and NO `cert_key`. E5.1 chains (`prev_sha256`) and numbers (`seq`) every line and verifies
the whole ledger on every read and write; this module never serialises, hashes or numbers a line itself: every append
goes through `nc.append_records`, every read through `nc.read_records` / `nc.parse_records`. An event is not in E5.1's
certificate index, so it can neither shadow nor be mistaken for a certificate.

  invalidation  {"type": "invalidation", "asset": <asset>, "layer": "L0".."L5", "invalidates": "<cert_id>",
                 "reason": [{"code": "writer_hash"|"writer_file_added"|"writer_file_removed"|
                             "semantic_fingerprint"|"registry"|"upstream_generation"|"upstream_stale"|
                             "upstream_not_passing", ...detail}],
                 "walk": <int, one per invalidating run>, "detected_by": "nikasha_stale_certs.py",
                 "detected_on": <tz-aware ISO>, "record_version": 1, "seq": .., "prev_sha256": ..}
  watermark     {"type": "watermark", "asset": "_ledger", "covers_seq": <E5.1 seq of the last record the evaluation
                 covered; 0 for a schema-only ledger>, "certs_processed": <certificates with seq <= covers_seq>,
                 "last_cert_id": <cert_id of the last of them | null>, "commit": <repo commit the evaluation ran at>,
                 "evaluated_on": <tz-aware ISO>, "record_version": 1, "seq": .., "prev_sha256": ..}
  epoch_reset   {"type": "epoch_reset", "asset": "_ledger", "layer": "L0".."L5", "decision": "N-28",
                 "reset_on": <tz-aware ISO>, "record_version": 1, "seq": .., "prev_sha256": ..}

The watermark is OK iff the ledger's last watermark line is truthful (`certs_processed` / `last_cert_id` match the
certificates with seq <= `covers_seq`, `covers_seq` is below the line's own seq and not behind the previous
watermark) and NO certificate has seq > `covers_seq`. A certificate appended between this module's read and its
append is therefore "behind", never a lie. An invalidated certificate is not current until a new generation is
certified (E5.1). Events are outputs: they never make the watermark behind. A repeated invalidation of one
certificate (two racing runs) is tolerated and counted once; the first wins.

Usage:
  nikasha_stale_certs.py invalidate --ledger L --observed obs.json --commit <sha> [--observed-at-seq N]
                                    [--registry-assets a,b]
  nikasha_stale_certs.py new-epoch --ledger L --layer L2 --decision N-28        (the strategist's act)
  nikasha_stale_certs.py watermark-ok --ledger L        (or --ref R --repo P [--path ledger path in the repo])
  nikasha_stale_certs.py fingerprint --declarations decl.json --asset A --rows rows.json
obs.json = {"assets": {asset: {"writer_hashes": {path: sha256}, "writer_paths": [every current writer file],
            "semantic_fingerprint": sha256}}, "registry"?: {"revision": n, "fingerprint": sha256}}
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
import nikasha_certify as nc  # noqa: E402  (E5.1: strict ledger reader, the one append path)

MAX_REWALKS = 2
RECORD_VERSION = 1
HEADER_VERSION = 2
DETECTED_BY = "nikasha_stale_certs.py"
CERT_KINDS = ("gate", "addition")
EVENT_TYPES = ("invalidation", "watermark", "epoch_reset")
PASSING = ("PASS", "N/A")
DEFAULT_LEDGER_IN_REPO = "00_ARCHITECTURE/control/asset_certs.jsonl"

_IDENT = re.compile(r"[a-z_][a-z0-9_]{0,62}")          # the whitelist: lower-case SQL-safe identifiers, never quoted-through
_ASSET = re.compile(r"[a-z][a-z0-9_]*")
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/@^~{}-]*")  # a git ref/sha; never starts with '-', so never an option
_SHA256 = re.compile(r"[0-9a-f]{64}")
_DECISION = re.compile(r"N-[0-9]{1,6}[A-Za-z0-9._-]{0,24}")
# Copies of E5.1's id grammar and path check (E5.1 keeps them private); a parity test pins them to the originals.
_CERT_ID = re.compile(r"([a-z][a-z0-9_]*)\|(gate|addition)\|([A-Za-z0-9][A-Za-z0-9_.-]*)@([1-9][0-9]*)")
_DECL_KEYS = ("table", "scope", "scope_column", "natural_key", "semantic_columns", "volatile_columns", "embedding",
              "naive_utc_columns")
_EMBED_KEYS = ("column", "source_columns", "model_id")
FETCH_CHUNK = 5000
MAX_ROWS = 2_000_000
_UTC = dt.timezone.utc


def _check_relpath(p) -> bool:
    return (isinstance(p, str) and bool(p) and not p.startswith("/") and "\\" not in p
            and ".." not in p.split("/") and "" not in p.split("/"))


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

    def __init__(self, layer: str, walks: int, stale: dict, limit: int = MAX_REWALKS):
        self.layer, self.walks, self.stale, self.limit = layer, walks, stale, limit
        super().__init__(f"layer {layer} already has {walks} invalidating walk(s) since its last epoch reset "
                         f"(limit {limit}); {len(stale)} certificate(s) found stale: {sorted(stale)}. Strategic "
                         "Suvarna reviews the cause before any further rebuild (and, if it decides, records "
                         f"`new-epoch --layer {layer} --decision N-xx`); nothing was written")


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


def _embeddings(decl_emb, key, sem, vol, asset) -> list[dict]:
    if decl_emb is None:
        return []
    items = [decl_emb] if isinstance(decl_emb, Mapping) else decl_emb
    if not isinstance(items, (list, tuple)):
        raise BadDeclaration(f"{asset}: embedding must be a mapping or a list of mappings")
    out, cols = [], set()
    for e in items:
        if not isinstance(e, Mapping) or set(e) != set(_EMBED_KEYS):
            raise BadDeclaration(f"{asset}: an embedding entry must be exactly {{column, source_columns, model_id}}")
        col = e["column"]
        if not isinstance(col, str) or not _IDENT.fullmatch(col):
            raise BadDeclaration(f"{asset}: embedding column {col!r} is not an identifier")
        if col in cols:
            raise BadDeclaration(f"{asset}: embedding column {col} is declared twice")
        cols.add(col)
        srcs = _ident_list(e["source_columns"], f"embedding {col} source_columns", asset)
        mid = e["model_id"]
        if not _nonblank(mid) or len(mid) > 200 or mid != mid.strip() or any(ord(c) < 32 for c in mid):
            raise BadDeclaration(f"{asset}: embedding {col} needs a model_id (non-blank text, no control characters)")
        out.append(dict(column=col, source_columns=srcs, model_id=mid))
    for e in out:
        col = e["column"]
        if col in key:
            raise BadDeclaration(f"{asset}: embedding column {col} is part of the natural key")
        if sem is not None and col in sem:
            raise BadDeclaration(f"{asset}: embedding column {col} is excluded from the fingerprint: do not list it "
                                 "among semantic_columns (its source columns and model_id are hashed instead)")
        for s in e["source_columns"]:
            if s in cols:
                raise BadDeclaration(f"{asset}: embedding source column {s} is itself an embedding column")
            if sem is not None and s not in sem and s not in key:
                raise BadDeclaration(f"{asset}: embedding {col} source column {s} is not among semantic_columns")
            if vol is not None and s in vol:
                raise BadDeclaration(f"{asset}: embedding {col} source column {s} is declared volatile")
    return out


def validate_declaration(decl, asset: str = "<asset>") -> dict:
    """The normalised declaration of ONE asset (idempotent on its own output). Required: `table`, `scope`
    ('chart' | 'global'), `natural_key`, and exactly one of `semantic_columns` / `volatile_columns`. Optional:
    `scope_column` (default chart_id), `embedding` ({column, source_columns, model_id} or a list of them),
    `naive_utc_columns` (timestamp columns stored without a zone, known to be UTC). Raises BadDeclaration."""
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
    emb = _embeddings(decl.get("embedding"), key, sem, vol, asset)
    naive = decl.get("naive_utc_columns")
    naive = _ident_list(naive, "naive_utc_columns", asset, allow_empty=True) if naive is not None else []
    return dict(table=table, scope=scope, scope_column=scope_column, natural_key=key, semantic_columns=sem,
                volatile_columns=vol, embedding=emb, naive_utc_columns=naive)


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


def _text(s: str, path: str) -> str:
    try:
        s.encode("utf-8")
    except UnicodeEncodeError:
        raise UnreadableInput(f"{path}: text with an unpaired surrogate has no canonical form") from None
    return s


def _decimal(v: decimal.Decimal, path: str) -> dict:
    """Exact, precision-independent canonical form of a Decimal: sign, significant digits without trailing zeros, and
    the exponent (`1.50` and `1.5` are both 15E-1; any zero is 0; no context rounding at 28 digits)."""
    if not v.is_finite():
        raise UnreadableInput(f"{path}: non-finite Decimal")
    sign, digits, exp = v.as_tuple()
    ds = "".join(map(str, digits)).lstrip("0")
    if not ds:
        return {"$decimal": "0"}
    stripped = ds.rstrip("0")
    exp += len(ds) - len(stripped)
    return {"$decimal": f"{'-' if sign else ''}{stripped}E{exp}"}


def _canon(v, path: str, naive_utc: bool = False):
    """A JSON-able canonical form of a database value; raises UnreadableInput for what has none."""
    if v is None or isinstance(v, (bool, int)):
        return v
    if isinstance(v, str):
        return _text(v, path)
    if isinstance(v, float):
        if not math.isfinite(v):
            raise UnreadableInput(f"{path}: non-finite float {v!r}")
        return 0.0 if v == 0 else v                                  # -0.0 is zero
    if isinstance(v, decimal.Decimal):
        return _decimal(v, path)
    if isinstance(v, dt.datetime):
        if v.tzinfo is None or v.utcoffset() is None:
            if not naive_utc:
                raise UnreadableInput(f"{path}: a naive datetime has no instant: declare the column in "
                                      "naive_utc_columns if it is stored as UTC without a zone")
            v = v.replace(tzinfo=_UTC)
        return v.astimezone(_UTC).isoformat()                        # the same instant is the same value
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, dt.time):
        if v.utcoffset() is not None:
            raise UnreadableInput(f"{path}: a time with a zone cannot be normalised without a date")
        if not naive_utc:
            raise UnreadableInput(f"{path}: a naive time: declare the column in naive_utc_columns")
        return v.isoformat()
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, (list, tuple)):
        return [_canon(x, path, naive_utc) for x in v]
    if isinstance(v, Mapping):
        if not all(isinstance(k, str) for k in v):
            raise UnreadableInput(f"{path}: non-text key in a mapping value")
        out = {_text(k, path): _canon(x, path, naive_utc) for k, x in v.items()}
        # our own markers start with "$": an object of the data that does too is wrapped, so it can never collide
        return {"$obj": out} if any(k.startswith("$") for k in out) else out
    raise UnreadableInput(f"{path}: {type(v).__name__} has no canonical form")


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
    key, sem, vol, emb = d["natural_key"], d["semantic_columns"], d["volatile_columns"], d["embedding"]
    emb_cols = {e["column"] for e in emb}
    naive = set(d["naive_utc_columns"])
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
        columns = sorted(shape - set(vol) - emb_cols)
        for e in emb:
            absent = sorted(set(e["source_columns"]) - shape)
            if absent:
                raise UnreadableInput(f"embedding {e['column']}: source column(s) {absent} are not in the rows")
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
            kv.append(_canon(r[k], f"row {i}.{k}", k in naive))
        payload = {c: _canon(r[c], f"row {i}.{c}", c in naive) for c in columns}
        keyed.append((_dumps(kv), _dumps(payload)))
    keyed.sort()
    for a, b in zip(keyed, keyed[1:]):
        if a[0] == b[0]:
            raise UnreadableInput(f"natural key {a[0]} occurs more than once: the declared key is not a key")
    header = _dumps(dict(
        v=HEADER_VERSION, table=d["table"], scope=d["scope"],
        scope_column=d["scope_column"] if d["scope"] == "chart" else None, natural_key=key,
        mode="semantic" if sem is not None else "volatile", columns=sorted(sem if sem is not None else vol),
        embedding=sorted((dict(column=e["column"], source_columns=sorted(e["source_columns"]), model_id=e["model_id"])
                          for e in emb), key=lambda e: e["column"]),
        naive_utc_columns=sorted(naive)))
    h = hashlib.sha256()
    h.update(header.encode("utf-8") + b"\n")
    for _k, line in keyed:
        h.update(_k.encode("utf-8") + b"\t" + line.encode("utf-8") + b"\n")
    return h.hexdigest()


# ─────────────────────────── the read-only loader ───────────────────────────

def build_select(decl) -> str:
    """The ONE SELECT this module ever issues, in one of three fixed shapes (explicit columns, `*`, with or without
    the chart scope). Every identifier already matched the lower-case whitelist, so double-quoting cannot be
    escaped; the chart id is the `%s` parameter, never text. In semantic mode only the key and semantic columns are
    selected: an embedding column is never read."""
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


def load_rows(conn, decl, chart_id=None, *, max_rows: int = MAX_ROWS, cursor_name: str | None = None) -> list[dict]:
    """Read the asset's rows through an open DB-API connection: one parameterised SELECT, no write.

    Transaction discipline: this runs in the CALLER's transaction. It never commits and never rolls back (the caller
    owns the transaction: after a failed query a PostgreSQL transaction is aborted and the caller must roll back;
    run it on a read-only connection, `SET TRANSACTION READ ONLY`). It closes only the cursor it opened. A query
    failure, a result with no column description, or more than `max_rows` rows raises UnreadableInput; it never
    returns [] for a failure. The rows are materialised: for a very large table pass `cursor_name` (a server-side,
    named cursor, fetched in chunks) and a `max_rows` that fits memory, or fingerprint in the database."""
    d = validate_declaration(decl)
    if isinstance(max_rows, bool) or not isinstance(max_rows, int) or max_rows < 1:
        raise UnreadableInput("max_rows must be a positive int")
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
        cur = conn.cursor(name=cursor_name) if cursor_name else conn.cursor()
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
            if len(rows) > max_rows:
                raise UnreadableInput(f"{d['table']} has more than max_rows={max_rows} rows: stream it with a "
                                      "server-side cursor (cursor_name) or raise the guard knowingly")
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


def table_fingerprint(conn, decl, chart_id=None, **load_kwargs) -> str:
    d = validate_declaration(decl)
    return fingerprint_rows(load_rows(conn, d, chart_id, **load_kwargs), d)


# ═══════════════ ledger reading ═══════════════

@dataclass
class Ledger:
    certs: list = field(default_factory=list)            # certificate records in file order (each carries E5.1's seq)
    pos: dict = field(default_factory=dict)              # cert_id -> index in certs
    by_key: dict = field(default_factory=dict)           # cert_key -> [records] in generation order
    invs: list = field(default_factory=list)
    inv_targets: dict = field(default_factory=dict)      # invalidated cert_id -> first invalidation record
    wms: list = field(default_factory=list)
    resets: list = field(default_factory=list)           # epoch_reset events
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


def read_ledger_file(path) -> Ledger:
    """The ledger at `path`, read through E5.1's shared-lock reader (never a plain read) and verified."""
    try:
        return _ledger_from_records(nc.read_records(nc.resolve_ledger_path(path)))
    except nc.CertificationRefused as e:
        raise _wrap(e) from e


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
        elif r.get("type") == "epoch_reset":
            _check_epoch_reset(r, n)
            lg.resets.append(r)
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
    if (isinstance(w, bool) or not isinstance(w, int) or w < 1
            or not isinstance(reason, list) or not reason
            or not all(isinstance(x, dict) and _nonblank(x.get("code")) for x in reason)):
        raise LedgerShapeError(f"seq {n}: invalidation needs walk >= 1 and a non-empty reason list")


def _check_epoch_reset(r: dict, n: int) -> None:
    d = r.get("decision")
    if (r.get("asset") != "_ledger" or r.get("layer") not in ac.LAYERS or not isinstance(d, str)
            or not _DECISION.fullmatch(d)):
        raise LedgerShapeError(f"seq {n}: malformed epoch_reset (needs asset _ledger, a layer and a decision id N-xx)")


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
    """(writer_hashes_observed | None, writer_paths | None, fingerprint_observed | None), raising where the record
    needs what was not supplied or was malformed. A record that records no hashes and no fingerprint needs no
    observation. A record WITH writer hashes needs the asset's full current writer path set too: a writer file added
    since is only visible against it."""
    wants_wh, wants_fp = bool(rec.get("writer_hashes")), rec.get("semantic_fingerprint") is not None
    if not (wants_wh or wants_fp):
        return None, None, None
    o = observed.get(asset)
    if not isinstance(o, Mapping):
        raise MissingObservation(f"no observation for {asset}, which holds certificate {rec['cert_id']}")
    wh = fp = paths = None
    if "writer_paths" in o:
        paths = o["writer_paths"]
        if not isinstance(paths, (list, tuple)) or not all(_check_relpath(p) for p in paths) or len(set(paths)) != len(paths):
            raise UnreadableInput(f"{asset}: observed writer_paths must be a list of distinct repo-relative paths")
    if wants_wh:
        if "writer_hashes" not in o:
            raise MissingObservation(f"{asset}: writer_hashes not observed")
        if paths is None:
            raise MissingObservation(f"{asset}: writer_paths (every current writer file) not observed")
        wh = o["writer_hashes"]
        if not isinstance(wh, Mapping) or not all(isinstance(p, str) and isinstance(h, str) and _SHA256.fullmatch(h)
                                                  for p, h in wh.items()):
            raise UnreadableInput(f"{asset}: observed writer_hashes must map path -> lower-case sha256")
        absent = [p for p in rec["writer_hashes"] if p in paths and p not in wh]
        if absent:
            raise MissingObservation(f"{asset}: writer file(s) {absent} not observed")
    if wants_fp:
        if "semantic_fingerprint" not in o:
            raise MissingObservation(f"{asset}: semantic_fingerprint not observed")
        fp = o["semantic_fingerprint"]
        if not isinstance(fp, str) or not _SHA256.fullmatch(fp):
            raise UnreadableInput(f"{asset}: observed semantic_fingerprint is not 64 lower-case hex ({fp!r})")
    return wh, paths, fp


def _check_registry(registry) -> set:
    """The assets a registry observation applies to. A registry observation names them: a bare revision bump must not
    invalidate every gate certificate."""
    if registry is None:
        return set()
    if not (isinstance(registry, Mapping) and isinstance(registry.get("revision"), int)
            and not isinstance(registry.get("revision"), bool) and isinstance(registry.get("fingerprint"), str)):
        raise UnreadableInput("registry observation must be {revision: int, fingerprint: str, assets: [...]}")
    assets = registry.get("assets")
    if (not isinstance(assets, (list, tuple)) or not assets
            or not all(isinstance(a, str) and _ASSET.fullmatch(a) for a in assets)):
        raise UnreadableInput("a registry observation applies only to the assets the caller names "
                              "(`assets`: a non-empty list of asset ids; CLI --registry-assets)")
    return set(assets)


def _evaluate(lg: Ledger, observed, registry=None) -> Evaluation:
    if not isinstance(observed, Mapping):
        raise UnreadableInput("observed must be a mapping of asset -> observation")
    reg_assets = _check_registry(registry)
    ev = Evaluation(stale={}, current=[], invalidated=[], not_certificates=[])
    status: dict[str, str] = {}
    reasons_of: dict[str, list] = {}

    def resolve(rec: dict) -> str:
        cid = rec["cert_id"]
        if cid in status:
            return status[cid]
        if cid in lg.inv_targets:
            status[cid] = "invalidated"
            return "invalidated"
        if rec["verdict"] not in PASSING:
            status[cid] = "not_cert"
            return "not_cert"
        reasons = []
        wh, paths, fp = _observation(observed, rec["asset"], rec)
        recorded_w = rec.get("writer_hashes") or {}
        if wh is not None:
            for p, recorded in recorded_w.items():
                if p in paths and wh[p] != recorded:
                    reasons.append(dict(code="writer_hash", path=p, recorded=recorded, observed=wh[p]))
        if paths is not None:
            for p in sorted(set(paths) - set(recorded_w)):
                reasons.append(dict(code="writer_file_added", path=p))
            for p in sorted(set(recorded_w) - set(paths)):
                reasons.append(dict(code="writer_file_removed", path=p))
        if fp is not None and fp != rec["semantic_fingerprint"]:
            reasons.append(dict(code="semantic_fingerprint", recorded=rec["semantic_fingerprint"], observed=fp))
        if rec["kind"] == "gate" and rec["asset"] in reg_assets and (
                rec.get("registry_revision") != registry["revision"]
                or rec.get("registry_fingerprint") != registry["fingerprint"]):
            reasons.append(dict(code="registry",
                                recorded=dict(revision=rec.get("registry_revision"),
                                              fingerprint=rec.get("registry_fingerprint")),
                                observed=dict(revision=registry["revision"], fingerprint=registry["fingerprint"])))
        i = lg.pos[cid]
        for u in rec.get("upstream_cert_ids") or []:
            m = _CERT_ID.fullmatch(u) if isinstance(u, str) else None
            if m is None:
                raise LedgerShapeError(f"{cid}: upstream id {u!r} is not a cert id")
            if u not in lg.pos or lg.pos[u] >= i:
                raise LedgerShapeError(f"{cid}: cites {u}, which is not a certificate on an earlier line")
            latest = lg.by_key[nc.cert_key_of(m.group(1), m.group(2), m.group(3))][-1]
            cited = int(m.group(4))
            bumped_same = False
            if latest["generation"] != cited:
                cited_rec = lg.certs[lg.pos[u]]
                # E5.1 mints a new generation when any currency field changes, even with identical output: when the
                # cited generation and the latest carry the SAME semantic fingerprint, the dependents' premise (what
                # the rows say) is unchanged and an idempotent rebuild must invalidate nothing downstream.
                bumped_same = (cited_rec.get("semantic_fingerprint") is not None
                               and cited_rec.get("semantic_fingerprint") == latest.get("semantic_fingerprint"))
                if not bumped_same:
                    reasons.append(dict(code="upstream_generation", upstream=u, cited=cited,
                                        latest=latest["generation"]))
                    continue
            st = resolve(latest)
            extra = dict(cited=u, via="generation_bump_same_output") if bumped_same else {}
            if st == "not_cert":
                reasons.append(dict(code="upstream_not_passing", upstream=latest["cert_id"],
                                    verdict=latest["verdict"], **extra))
            elif st in ("invalidated", "stale"):
                reasons.append(dict(code="upstream_stale", upstream=latest["cert_id"], why=st, **extra))
        status[cid] = "stale" if reasons else "current"
        reasons_of[cid] = reasons
        return status[cid]

    for rec in lg.certs:
        if lg.by_key[rec["cert_key"]][-1] is not rec:
            continue                                            # superseded generation
        cid, st = rec["cert_id"], resolve(rec)
        if st == "invalidated":
            ev.invalidated.append(cid)
        elif st == "not_cert":
            ev.not_certificates.append(cid)
        elif st == "stale":
            ev.stale[cid] = reasons_of[cid]
        else:
            ev.current.append(cid)
            fl = certificate_flags(rec)
            if fl:
                ev.flags[cid] = fl
    return ev


def evaluate(data, observed, registry=None) -> Evaluation:
    """Pure: which latest certificates are stale given what is observed NOW. `observed` = {asset:
    {"writer_hashes": {path: sha256}, "writer_paths": [every current writer file], "semantic_fingerprint": sha256}}.
    `registry` = {"revision", "fingerprint", "assets": [...]} applies to the named assets only. Raises
    (MissingObservation / UnreadableInput / LedgerShapeError) rather than guess: an unobserved asset is never read
    as unchanged."""
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
    if not _check_relpath(path):
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
    """{layer: number of distinct invalidating walks since that layer's last `epoch_reset`} over the WHOLE ledger
    (layers with none are absent). The only way the count restarts is an `epoch_reset` event."""
    lg = _as_ledger(data)
    since = {}
    for r in lg.resets:
        since[r["layer"]] = max(since.get(r["layer"], 0), r["seq"])
    walks: dict = {}
    for r in lg.invs:
        if r["seq"] > since.get(r["layer"], 0):
            walks.setdefault(r["layer"], set()).add(r["walk"])
    return {layer: len(w) for layer, w in walks.items()}


@dataclass(frozen=True)
class InvalidateResult:
    status: str                 # "appended" | "unchanged"
    invalidated: list           # cert_ids invalidated by this run
    walk: int | None
    watermark: dict | None
    ledger_path: Path


def invalidate(ledger_path, observed, *, commit, registry=None, now=None, observed_at_seq=None) -> InvalidateResult:
    """Evaluate, then append (through `nc.append_records`: one atomic, chained, numbered write) one invalidation
    event per newly stale certificate and a watermark event. Idempotent: if nothing is newly stale and the watermark
    already covers every certificate that was observed, nothing is appended and no walk is used. Raises RewalkLimitExceeded, before
    writing, when a layer touched already has MAX_REWALKS invalidating walks since its last epoch reset.

    `observed_at_seq`: the chain head (`nc.chain_head(...)[0]`) taken BEFORE the observations were gathered. The
    run then evaluates only certificates with seq <= it and its watermark covers no more: a certificate written
    after the observations were taken is "behind", never judged against observations that predate it. Default: the
    ledger's head as read now (the caller asserts nothing was certified while observing). The read (shared lock) and
    the append (exclusive lock) are separate E5.1 calls; a certificate that lands between them is covered by neither
    this run's evaluation nor its watermark."""
    if not _nonblank(commit):
        raise StaleCertsError("commit is required (the repo commit this evaluation ran at)", "bad_commit")
    path = nc.resolve_ledger_path(ledger_path)
    stamp = now or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        records = nc.read_records(path)
    except nc.CertificationRefused as e:
        raise _wrap(e) from e
    full = _ledger_from_records(records)
    cap = full.last_seq if observed_at_seq is None else observed_at_seq
    if isinstance(cap, bool) or not isinstance(cap, int) or not 0 <= cap <= full.last_seq:
        raise StaleCertsError(f"observed_at_seq {observed_at_seq!r} is not within 0..{full.last_seq} (the ledger head)",
                              "bad_observed_at_seq")
    if full.wms and cap < full.wms[-1]["covers_seq"]:
        raise StaleCertsError(f"observed_at_seq {cap} is behind the existing watermark ({full.wms[-1]['covers_seq']})",
                              "bad_observed_at_seq")
    lg = _ledger_from_records([r for r in records if r["seq"] <= cap])
    lg.inv_targets = dict(full.inv_targets)                      # an invalidation another run appended still counts
    ev = _evaluate(lg, observed, registry)
    layers = {}
    for cid in ev.stale:
        layers.setdefault(lg.certs[lg.pos[cid]]["layer"], []).append(cid)
    counts = rewalk_counts(full)
    for layer in sorted(layers):
        if counts.get(layer, 0) >= MAX_REWALKS:
            raise RewalkLimitExceeded(layer, counts[layer], ev.stale)
    if not ev.stale and full.wms and all(c["seq"] <= full.wms[-1]["covers_seq"] for c in lg.certs):
        return InvalidateResult("unchanged", [], None, None, path)
    walk = (max((r["walk"] for r in full.invs), default=0) + 1) if ev.stale else None
    out = []
    for cid, reasons in ev.stale.items():
        t = lg.certs[lg.pos[cid]]
        out.append(dict(type="invalidation", asset=t["asset"], layer=t["layer"], invalidates=cid, reason=reasons,
                        walk=walk, detected_by=DETECTED_BY, detected_on=stamp, record_version=RECORD_VERSION))
    wm = dict(type="watermark", asset="_ledger", covers_seq=cap, certs_processed=lg.cert_count,
              last_cert_id=lg.certs[-1]["cert_id"] if lg.certs else None, commit=commit, evaluated_on=stamp,
              record_version=RECORD_VERSION)
    try:
        nc.append_records(path, out + [wm])
    except nc.CertificationRefused as e:
        raise _wrap(e) from e
    return InvalidateResult("appended", list(ev.stale), walk, wm, path)


def new_epoch(ledger_path, layer: str, decision: str, *, now=None) -> dict:
    """Append an `epoch_reset` event: the layer's invalidating-walk count restarts. This is the STRATEGIST'S act (the
    cap exists so that a third re-walk gets reviewed before any further rebuild); `decision` is the decision id
    (N-xx) recorded with it. The ledger and git history are the audit: this function cannot know who runs it."""
    if layer not in ac.LAYERS:
        raise StaleCertsError(f"layer must be one of {sorted(ac.LAYERS)}", "bad_layer")
    if not isinstance(decision, str) or not _DECISION.fullmatch(decision):
        raise StaleCertsError(f"decision {decision!r} is not a decision id (N-<number>...)", "bad_decision")
    ev = dict(type="epoch_reset", asset="_ledger", layer=layer, decision=decision,
              reset_on=now or dt.datetime.now().astimezone().isoformat(timespec="seconds"),
              record_version=RECORD_VERSION)
    try:
        nc.append_records(nc.resolve_ledger_path(ledger_path), [ev])
    except nc.CertificationRefused as e:
        raise _wrap(e) from e
    return ev


# ═══════════════ CLI ═══════════════

def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="E5.5 stale-certification detector")
    sub = ap.add_subparsers(dest="cmd", required=True)
    inv = sub.add_parser("invalidate")
    inv.add_argument("--ledger", default=None)
    inv.add_argument("--observed", required=True, help="JSON: {assets: {...}, registry?: {revision, fingerprint}}")
    inv.add_argument("--commit", required=True)
    inv.add_argument("--observed-at-seq", type=int, default=None,
                     help="the ledger's chain-head seq taken BEFORE the observations were gathered")
    inv.add_argument("--registry-assets", default=None, help="comma list: the assets the registry check applies to")
    inv.add_argument("--now", default=None)
    ne = sub.add_parser("new-epoch", help="the strategist's act: restart a layer's re-walk count")
    ne.add_argument("--ledger", default=None)
    ne.add_argument("--layer", required=True)
    ne.add_argument("--decision", required=True, help="decision id, e.g. N-28")
    ne.add_argument("--now", default=None)
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
            registry = doc.get("registry")
            if a.registry_assets is not None:
                if registry is None:
                    raise StaleCertsError("--registry-assets given but the observed file has no registry", "bad_registry")
                registry = dict(registry, assets=[x.strip() for x in a.registry_assets.split(",") if x.strip()])
            r = invalidate(a.ledger, doc.get("assets", {}), commit=a.commit, registry=registry, now=a.now,
                           observed_at_seq=a.observed_at_seq)
            print(json.dumps(dict(status=r.status, invalidated=r.invalidated, walk=r.walk, ledger=str(r.ledger_path))))
            return 0
        if a.cmd == "new-epoch":
            e = new_epoch(a.ledger, a.layer, a.decision, now=a.now)
            print(json.dumps(dict(status="appended", layer=e["layer"], decision=e["decision"])))
            return 0
        if a.cmd == "watermark-ok":
            lg = (parse_events(read_ledger_at_ref(a.ref, a.repo or ac.ROOT, a.path)) if a.ref
                  else read_ledger_file(a.ledger))
            st = watermark_status(lg)
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
