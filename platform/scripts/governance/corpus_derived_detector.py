"""corpus_derived_detector.py: the REPRODUCIBILITY detector of the `corpus_derived` declaration form (SS N-431, bg_rules).

WHAT IT PROVES. A table whose rows are the OUTPUT of a committed, sha256-pinned deterministic parser over a text corpus (bg_rules: 27 regular expressions over classical_text_chunks) is not
hand-typed prose and holds no stand-in for a missing value, IF re-running that parser reproduces the stored rows. This module re-runs the pinned parser (through an injected sandbox runner)
over the cited source chunks and compares the output with the stored rows, column by column.

THIS MODULE IS PURE. It imports neither asset_census nor the sandbox. Every outside effect is injected:
  * `fetch(request: dict) -> value`   the bounded data reads (ops below); the real one is built in asset_census (capped psql), the tests pass fakes;
  * `runner(...)`                     parser_sandbox.run_pinned_parser (R2) or a fake of the same signature;
  * `normaliser(entry) -> dict`       corpus_declaration.normalise_corpus_derived (R1) or a fake.

FETCH OPS (each request is a dict with `op`; the answer is parsed JSON-shaped data; a read that cannot be made to a verdict raises `Unread(reason)`):
  columns {table}                                -> [column names in table order] ([] = the table does not exist)
  count   {table}                                -> int
  rows    {table, columns, order_by, limit, offset} -> [ {column: value} ] for rows ordered by `order_by` (total order: the key columns)
  ids     {table, id_column}                     -> [id as text], ordered by id
  chunks  {table, id_column, columns, ids}       -> [ {column: value} ] for the listed ids (an id that does not exist is simply absent)

STAGES. A detector result that is NO_DETECTOR names the stage that could not complete: declaration | read | pin | spawn | run | output | loaded_files.
It NEVER reads PASS on a truncated, capped or partial read: every cap is checked against the full count first, and the number of rows received must equal it.

COMPARISON VALUE NORMALISATION (`values_equal`, documented once, tested):
  * NULL equals only NULL (an empty string, 0 or [] is NOT NULL);
  * booleans equal only booleans (True != 1);
  * numbers (int, float, Decimal) are equal when their DECIMAL values are equal (`Decimal(repr(float))`: 1 == 1.0 == Decimal('1.00'); 0.8 == Decimal('0.8')); there is no tolerance;
  * a list and a tuple are the same array (a PostgreSQL array and a JSON array both arrive as a list); arrays are ORDERED; an object is its set of key/value pairs;
  * a TEXT value on one side and an array/object on the other is read as JSON text (the parser emits `json.dumps(...)` strings for jsonb columns, the table returns the parsed value);
    two TEXT values are compared as text, exactly (no JSON parsing, no case folding) except that two canonical UUID strings are compared case-insensitively.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation

PASS, FAIL, NO_DET = "PASS", "FAIL", "NO_DETECTOR"
STAGES = ("declaration", "read", "pin", "spawn", "run", "output", "loaded_files")

# ───────────────────────────── caps (every one is checked against the FULL count before anything is read) ─────────────────────────────
# bg_rules today: 3002 stored rows (~4 MB of jsonb), a few thousand source chunks (~10 MB of text). The caps leave an order of magnitude of headroom and still bound the census' memory.
CAPS = dict(
    stored_rows=50_000,            # stored rows read (the whole table: scope.stored is "all"); past it the table is NOT read, the cell reads NO_DETECTOR
    stored_bytes=48 * 1024 * 1024, # JSON bytes of the stored rows read
    source_ids=200_000,            # source chunk ids listed (needed to know which chunks nobody cites)
    chunks=50_000,                 # source chunks fetched (cited ones plus the uncited sample)
    chunk_bytes=64 * 1024 * 1024,  # text bytes of the fetched chunks (the sandbox's own max_output_bytes default is 64_000_000)
    rows_page=500,                 # stored rows per statement
    chunks_page=100,               # chunks per statement
)
RUN_TIMEOUT_S = 300                # the sandbox run; the default 120 s is thin for a few thousand chunks through 27 patterns
MAX_FIRST_DIFFERENCES = 5          # the bounded sample of differences reported (key and column NAMES only, never values)
DIFF_ORDER = ("differs", "extra_stored", "missing_stored", "uncited_chunk_yields_rule", "cited_chunk_absent", "stored_row_cites_no_chunk", "stored_duplicate_key", "derived_key_collision")

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:\-]{0,127}")
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


class Unread(Exception):
    """A read that could not be made to a verdict (statement timeout, a role that may not read, an output past the byte cap). The detector reads NO_DETECTOR (stage `read`), never PASS."""


class _Stop(Exception):
    """Internal: ends the detection with a NO_DETECTOR naming `stage`."""
    def __init__(self, stage: str, detail: str):
        super().__init__(detail)
        self.stage, self.detail = stage, detail


# ───────────────────────────── value normalisation ─────────────────────────────

def _dec(x):
    if isinstance(x, Decimal):
        return x
    if isinstance(x, int):
        return Decimal(x)
    return Decimal(repr(float(x)))


def canonical(v):
    """A hashable canonical form of one value (see the module docstring for the rules)."""
    if v is None:
        return ("null",)
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, (int, float, Decimal)):
        try:
            d = _dec(v)
            if not d.is_finite():
                return ("nonfinite", str(d))
            return ("num", format(d.normalize(), "f"))
        except (InvalidOperation, ValueError, OverflowError):
            return ("nonfinite", repr(v))
    if isinstance(v, str):
        return ("str", v.lower() if _UUID.fullmatch(v) else v)
    if isinstance(v, (list, tuple)):
        return ("arr", tuple(canonical(x) for x in v))
    if isinstance(v, dict):
        return ("obj", tuple(sorted(((str(k), canonical(x)) for k, x in v.items()), key=lambda p: p[0])))
    return ("str", str(v))


def _as_json_text(s: str):
    try:
        return json.loads(s, parse_float=Decimal)
    except (ValueError, TypeError):
        return _NOT_JSON


_NOT_JSON = object()


def values_equal(a, b) -> bool:
    """Are two column values equal under the normalisation documented in the module docstring?"""
    ca, cb = isinstance(a, (list, tuple, dict)), isinstance(b, (list, tuple, dict))
    if isinstance(a, str) and cb:
        a = _as_json_text(a)
        if a is _NOT_JSON:
            return False
    elif isinstance(b, str) and ca:
        b = _as_json_text(b)
        if b is _NOT_JSON:
            return False
    return canonical(a) == canonical(b)


def _plain(v):
    """A JSON-safe rendering of a key value (key values identify a row; they are not content)."""
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float) and math.isfinite(v):
        return v
    return str(v)


# ───────────────────────────── citation ─────────────────────────────

def cited_ids(value, cite_key: str = "chunk_id"):
    """(ids, malformed): the source ids a stored row cites in its cite column. A scalar text is one id; a JSON/array/object value is walked and every `cite_key` entry of every object (or every scalar of
    a plain array) is an id. `malformed` is True when a cited value is not a safe id (it can neither be fetched nor be a real chunk id). NULL / empty cites nothing."""
    ids, bad = [], [False]

    def take(x):
        if isinstance(x, str) and _SAFE_ID.fullmatch(x):
            ids.append(x)
        elif isinstance(x, (int,)) and not isinstance(x, bool):
            ids.append(str(x))
        elif x is not None:
            bad[0] = True

    def walk(x, top):
        if x is None:
            return
        if isinstance(x, str):
            s = x.strip()
            if s[:1] in ("[", "{"):
                j = _as_json_text(s)
                if j is not _NOT_JSON:
                    walk(j, top)
                    return
            if s:
                take(s)
            return
        if isinstance(x, (list, tuple)):
            for y in x:
                walk(y, False)
            return
        if isinstance(x, dict):
            if cite_key in x:
                for z in (x[cite_key] if isinstance(x[cite_key], (list, tuple)) else [x[cite_key]]):
                    take(z)
            return
        take(x)
    walk(value, True)
    return list(dict.fromkeys(ids)), bad[0]


# ───────────────────────────── the pure comparison ─────────────────────────────

def _key_of(row: dict, keys) -> tuple:
    if not isinstance(row, dict):
        raise ValueError("a row is not an object")
    miss = [k for k in keys if k not in row]
    if miss:
        raise ValueError(f"a row lacks key column(s) {miss}")
    return tuple(canonical(row[k]) for k in keys)


def _key_dict(row: dict, keys) -> dict:
    return {k: _plain(row.get(k)) for k in keys}


def compare_corpus_derived(stored_rows, derived_by_chunk, decl_norm) -> dict:
    """Compare the stored rows with the parser's output. PURE.

    stored_rows      list of dicts (every compared column, the key columns and the cite column);
    derived_by_chunk {chunk_id: [row dict, ...]} for EVERY chunk the parser ran on: the cited ones and the uncited sample. A cited chunk that does not exist in the source is `None`.
    decl_norm        the normalised declaration: key_columns, cite_column, ignore_columns, optional cite_key (default "chunk_id").

    Rules. For each stored row and each chunk it cites, the parser output of that chunk must hold a row with the same key, equal on EVERY column except ignore_columns (a column present on one side
    only is a difference). Each derived row of a CITED chunk must be stored. A chunk nobody cites (the uncited sample) must yield NO row. A derived row whose key is stored under another chunk that the
    stored row's own derivation confirms is SHADOWED (the table's unique key + ON CONFLICT DO NOTHING keep the first writer): counted, not a difference. Raises ValueError on malformed input
    (a row without its key columns, a derived chunk that is not a list of objects): the caller reads NO_DETECTOR(output).
    Returns dict(v, measured, first_differences, counts, difference_counts). v is PASS only when nothing differs and at least one stored row was compared; FAIL when a difference exists;
    NO_DETECTOR when there is no stored row (vacuous)."""
    keys = list(decl_norm["key_columns"])
    cite = decl_norm["cite_column"]
    ignore = set(decl_norm.get("ignore_columns") or [])
    cite_key = decl_norm.get("cite_key") or "chunk_id"
    diffs: list[dict] = []

    def diff(kind, **kw):
        diffs.append(dict(kind=kind, **kw))

    stored_by_key: dict = {}
    claims: dict = {}                # chunk id -> set of stored keys citing it
    stored_cites: dict = {}          # key -> [chunk ids]
    for row in stored_rows:
        k = _key_of(row, keys)
        if k in stored_by_key:
            diff("stored_duplicate_key", key=_key_dict(row, keys))
            continue
        stored_by_key[k] = row
        ids, bad = cited_ids(row.get(cite), cite_key)
        stored_cites[k] = ids
        if not ids or bad:
            diff("stored_row_cites_no_chunk", key=_key_dict(row, keys), columns=[cite])
        for c in ids:
            claims.setdefault(c, set()).add(k)

    derived_index: dict = {}         # (chunk, key) -> row
    for cid in sorted(derived_by_chunk):
        rows = derived_by_chunk[cid]
        if rows is None:
            if cid in claims:
                diff("cited_chunk_absent", chunk=cid)
            continue
        if not isinstance(rows, (list, tuple)):
            raise ValueError(f"the parser output of chunk {cid} is not a list")
        for r in rows:
            k = _key_of(r, keys)
            if (cid, k) in derived_index:
                if not all(values_equal(derived_index[(cid, k)].get(c), r.get(c)) for c in (set(derived_index[(cid, k)]) | set(r)) - ignore):
                    diff("derived_key_collision", chunk=cid, key=_key_dict(r, keys))
                continue
            derived_index[(cid, k)] = r

    matched = shadowed = 0
    for k, srow in stored_by_key.items():
        for cid in stored_cites.get(k, []):
            if cid in derived_by_chunk and derived_by_chunk[cid] is None:
                continue                             # reported as cited_chunk_absent
            if cid not in derived_by_chunk:          # the caller did not re-derive a cited chunk: it cannot be matched
                diff("extra_stored", chunk=cid, key=_key_dict(srow, keys), columns=[])
                continue
            drow = derived_index.get((cid, k))
            if drow is None:
                diff("extra_stored", chunk=cid, key=_key_dict(srow, keys), columns=[])
                continue
            cols = (set(srow) | set(drow)) - ignore
            bad = sorted(c for c in cols if (c in srow) != (c in drow) or not values_equal(srow.get(c), drow.get(c)))
            if bad:
                diff("differs", chunk=cid, key=_key_dict(srow, keys), columns=bad)
            else:
                matched += 1
    for (cid, k), drow in derived_index.items():
        if k in stored_by_key and cid in stored_cites[k]:
            continue
        if k in stored_by_key:                        # stored under another chunk: shadowed when that chunk's own derivation confirms the row; otherwise already an extra_stored
            if all((c2 in derived_by_chunk and (c2, k) in derived_index) for c2 in stored_cites[k]):
                shadowed += 1
            continue
        if cid in claims:
            diff("missing_stored", chunk=cid, key=_key_dict(drow, keys), columns=[])
        else:
            diff("uncited_chunk_yields_rule", chunk=cid, key=_key_dict(drow, keys), columns=[])

    uncited = sorted(c for c in derived_by_chunk if c not in claims)
    counts = dict(stored_rows=len(stored_rows), matched=matched, shadowed=shadowed, cited_chunks=len([c for c in derived_by_chunk if c in claims]),
                  uncited_chunks_run=len(uncited), derived_rows=len(derived_index))
    dcounts = {}
    for d in diffs:
        dcounts[d["kind"]] = dcounts.get(d["kind"], 0) + 1
    diffs.sort(key=lambda d: (DIFF_ORDER.index(d["kind"]) if d["kind"] in DIFF_ORDER else len(DIFF_ORDER), str(d.get("chunk")), json.dumps(d.get("key"), sort_keys=True, default=str)))
    first = diffs[:MAX_FIRST_DIFFERENCES]
    if not stored_rows:
        return dict(v=NO_DET, measured="no stored row: nothing was re-derived (a comparison over zero rows is vacuous)", first_differences=[], counts=counts, difference_counts=dcounts)
    if diffs:
        return dict(v=FAIL, measured=f"{len(diffs)} difference(s) between the stored rows and the parser output ({dcounts}); first: {describe_differences(first)}",
                    first_differences=first, counts=counts, difference_counts=dcounts)
    return dict(v=PASS, measured=(f"{matched} stored row(s) equal the parser output of their cited chunk(s); {shadowed} shadowed duplicate key(s); {counts['uncited_chunks_run']} uncited chunk(s) yielded no row"),
                first_differences=[], counts=counts, difference_counts=dcounts)


def describe_differences(first) -> str:
    out = []
    for d in first:
        cols = f" columns {d['columns']}" if d.get("columns") else ""
        out.append(f"{d['kind']} key={json.dumps(d.get('key'), sort_keys=True, default=str)} chunk={d.get('chunk')}{cols}".strip())
    return "; ".join(out)


# ───────────────────────────── SQL builders (pure; the real fetch executes them) ─────────────────────────────

def ident(name) -> str:
    if not (isinstance(name, str) and _IDENT.fullmatch(name)):
        raise ValueError(f"malformed identifier {name!r}")
    return name


def safe_id(x) -> str:
    if not (isinstance(x, str) and _SAFE_ID.fullmatch(x)):
        raise ValueError(f"malformed source id {x!r}")
    return x


def columns_sql(table: str) -> str:
    t = ident(table)
    return ("SELECT coalesce(jsonb_agg(a.attname::text ORDER BY a.attnum), '[]'::jsonb)::text FROM pg_attribute a "
            f"WHERE a.attrelid = to_regclass('\"{t}\"') AND a.attnum > 0 AND NOT a.attisdropped")


def count_sql(table: str, where: str | None = None) -> str:
    return f'SELECT count(*)::text FROM "{ident(table)}"' + (f" WHERE ({where})" if where else "")


def rows_sql(table: str, columns, order_by, limit: int, offset: int, where: str | None = None) -> str:
    cols = ",".join(f'"{ident(c)}"' for c in dict.fromkeys(columns))
    order = ",".join(f'"{ident(c)}"' for c in order_by)
    order_t = ",".join(f't."{ident(c)}"' for c in order_by)
    w = f" WHERE ({where})" if where else ""
    return (f"SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY {order_t}), '[]'::jsonb)::text FROM "
            f"(SELECT {cols} FROM \"{ident(table)}\"{w} ORDER BY {order} LIMIT {int(limit)} OFFSET {int(offset)}) t")


def ids_sql(table: str, id_column: str, where: str | None = None) -> str:
    t, c = ident(table), ident(id_column)
    w = f" WHERE ({where})" if where else ""
    return f"SELECT coalesce(jsonb_agg(x.i ORDER BY x.i), '[]'::jsonb)::text FROM (SELECT \"{c}\"::text AS i FROM \"{t}\"{w}) x"


def chunks_sql(table: str, id_column: str, columns, ids, where: str | None = None) -> str:
    t, c = ident(table), ident(id_column)
    cols = list(dict.fromkeys([c] + list(columns)))
    pairs = ",".join(f"'{ident(x)}', s.\"{ident(x)}\"" + ("::text" if x == c else "") for x in cols)
    lst = ",".join("'" + safe_id(i) + "'" for i in ids)
    w = f" AND ({where})" if where else ""
    return (f"SELECT coalesce(jsonb_agg(jsonb_build_object({pairs}) ORDER BY s.\"{c}\"::text), '[]'::jsonb)::text FROM \"{t}\" s "
            f"WHERE s.\"{c}\"::text IN ({lst}){w}")


# ───────────────────────────── the declaration, read through the normaliser only ─────────────────────────────

def _decl_problem(d) -> str | None:
    """Defensive re-check of the NORMALISED declaration's fields this module relies on (R1 owns the schema)."""
    try:
        if not isinstance(d, dict):
            return "the normalised declaration is not an object"
        ident(d["table"])
        keys = d["key_columns"]
        if not (isinstance(keys, (list, tuple)) and keys):
            return "key_columns must be a non-empty list"
        for k in keys:
            ident(k)
        ident(d["cite_column"])
        s = d["source"]
        ident(s["table"])
        ident(s["id_column"])
        for c in list(s.get("text_columns") or []) + list(s.get("extra_columns") or []):
            ident(c)
        p = d["parser"]
        pins = p["pinned_files"]
        if not (isinstance(pins, (list, tuple)) and pins and all(isinstance(x, dict) and isinstance(x.get("path"), str) and isinstance(x.get("sha256"), str) for x in pins)):
            return "parser.pinned_files must be a non-empty list of {path, sha256}"
        if p["file"] not in [x["path"] for x in pins]:
            return "parser.file is not one of the pinned files"
        if not (isinstance(p.get("function"), str) and p["function"] and isinstance(p.get("module_root"), str)):
            return "parser.function / parser.module_root missing"
        if any(k in set(d.get("ignore_columns") or []) for k in keys):
            return "a key column cannot be an ignored column"
        n = ((d.get("scope") or {}).get("uncited_chunks") or {}).get("sample")
        if not (isinstance(n, int) and not isinstance(n, bool) and n >= 1):
            return "scope.uncited_chunks.sample must be an integer >= 1 (an uncited sample that is skipped would not test that the table is the FULL output of the parser)"
        if (d.get("scope") or {}).get("stored", "all") != "all":
            return "scope.stored must be 'all'"
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


def build_inputs(decl_norm: dict, chunk_rows) -> list:
    """The sandbox inputs, one per chunk, in order. Shape `chunk` (the default): the chunk row as a dict {id_column, text_columns..., extra_columns...}, which is the first argument
    of l0_rules.extract_rules_from_chunk. ONE place to adapt when R1's `input_shape` vocabulary is final. Raises ValueError for a shape this detector does not know."""
    shape = (decl_norm.get("parser") or {}).get("input_shape")
    if shape in (None, "chunk", "chunk_dict", "row"):
        return [dict(r) for r in chunk_rows]
    raise ValueError(f"unsupported parser.input_shape {shape!r}")


def pins_summary(decl_norm: dict) -> list:
    return [dict(path=x["path"], sha256=x["sha256"]) for x in decl_norm["parser"]["pinned_files"]]


def _norm_path(p, root=None) -> str:
    s = str(p).replace("\\", "/")
    r = str(root).replace("\\", "/").rstrip("/") + "/" if root else None
    if r and s.startswith(r):
        s = s[len(r):]
    while s.startswith("./"):
        s = s[2:]
    return s


def sample_uncited(source_ids, cited_set, n: int) -> tuple[list, int]:
    """(sample, total uncited): the uncited ids (source ids nobody cites), in id order, every k-th with k = max(1, total // n), at most n of them. Deterministic."""
    unc = sorted(i for i in source_ids if i not in cited_set)
    if not unc:
        return [], 0
    k = max(1, len(unc) // n)
    return unc[::k][:n], len(unc)


# ───────────────────────────── the detector ─────────────────────────────

def _no(stage: str, detail: str, **block) -> dict:
    assert stage in STAGES, stage
    return dict(v=NO_DET, stage=stage, measured=f"NO_DETECTOR: corpus_derived stage '{stage}' could not complete: {detail}", block=dict(checked=True, verified=False, v=NO_DET, stage=stage, reason=detail, **block))


def _size(x) -> int:
    return len(json.dumps(x, default=str, ensure_ascii=False).encode("utf-8"))


def detect_corpus_derived(entry, *, fetch, runner, normaliser, repo_root, caps=None, run_timeout_s: int = RUN_TIMEOUT_S) -> dict:
    """Re-derive the stored rows of the declared table with the pinned parser and compare. Returns dict(v, stage, measured, block); `v` is PASS / FAIL / NO_DETECTOR; `stage` (NO_DETECTOR only)
    names the stage that did not complete; `block` is the record the six cells carry (checked, verified, counts, parser pins, first_differences)."""
    cap = dict(CAPS, **(caps or {}))
    try:
        return _detect(entry, fetch, runner, normaliser, repo_root, cap, run_timeout_s)
    except _Stop as s:
        return _no(s.stage, s.detail)
    except Unread as exc:
        return _no("read", str(exc))


def _detect(entry, fetch, runner, normaliser, repo_root, cap, run_timeout_s) -> dict:
    try:
        d = normaliser(entry)
    except Exception as exc:                          # the normaliser is R1's: whatever it refuses is a declaration problem, never a verdict
        raise _Stop("declaration", f"the declaration is refused by the normaliser ({type(exc).__name__}: {str(exc)[:200]})")
    bad = _decl_problem(d)
    if bad:
        raise _Stop("declaration", bad)
    table, keys, cite = d["table"], list(d["key_columns"]), d["cite_column"]
    ignore = list(d.get("ignore_columns") or [])
    src = d["source"]
    stable, sid = src["table"], src["id_column"]
    scols = list(dict.fromkeys(list(src.get("text_columns") or []) + list(src.get("extra_columns") or [])))
    n_sample = d["scope"]["uncited_chunks"]["sample"]
    pins = pins_summary(d)
    pblock = dict(file=d["parser"]["file"], function=d["parser"]["function"], module_root=d["parser"]["module_root"], pinned_files=pins)

    # ── stored rows: ALL of them, every compared column ──
    tcols = fetch(dict(op="columns", table=table))
    if not (isinstance(tcols, list) and tcols):
        raise _Stop("declaration", f"table {table} does not exist or has no readable column")
    miss = [c for c in keys + [cite] if c not in tcols]
    if miss:
        raise _Stop("declaration", f"table {table} has no column {miss}")
    read_cols = [c for c in tcols if c not in set(ignore) or c == cite]
    n = fetch(dict(op="count", table=table))
    if not (isinstance(n, int) and not isinstance(n, bool) and n >= 0):
        raise _Stop("read", f"unreadable row count of {table}: {n!r}")
    if n > cap["stored_rows"]:
        raise _Stop("read", f"{table} holds {n} rows, past the read cap of {cap['stored_rows']}: not read")
    if n == 0:
        raise _Stop("read", f"{table} holds no row: nothing to re-derive (vacuous)")
    stored, nbytes, off = [], 0, 0
    while off < n:
        page = fetch(dict(op="rows", table=table, columns=read_cols, order_by=keys, limit=cap["rows_page"], offset=off))
        if not isinstance(page, list) or not page:
            raise _Stop("read", f"the read of {table} stopped at {off} of {n} rows: not read")
        nbytes += _size(page)
        if nbytes > cap["stored_bytes"]:
            raise _Stop("read", f"the stored rows of {table} exceed the byte cap of {cap['stored_bytes']}: not read")
        stored.extend(page)
        off += cap["rows_page"]
    if len(stored) != n or fetch(dict(op="count", table=table)) != n:
        raise _Stop("read", f"{table} read {len(stored)} row(s) of {n} (or the row count changed during the read): not read")

    # ── the cited chunks and the uncited sample ──
    cite_key = d.get("cite_key") or "chunk_id"
    cited = []
    for r in stored:
        if not isinstance(r, dict):
            raise _Stop("read", "a stored row is not an object")
        cited.extend(cited_ids(r.get(cite), cite_key)[0])
    cited = sorted(set(cited))
    nsrc = fetch(dict(op="count", table=stable))
    if not (isinstance(nsrc, int) and not isinstance(nsrc, bool) and nsrc >= 0):
        raise _Stop("read", f"unreadable row count of {stable}: {nsrc!r}")
    if nsrc > cap["source_ids"]:
        raise _Stop("read", f"{stable} holds {nsrc} rows, past the id-list cap of {cap['source_ids']}: the uncited chunks cannot be established, not read")
    allids = fetch(dict(op="ids", table=stable, id_column=sid))
    if not isinstance(allids, list) or len(allids) != nsrc:
        raise _Stop("read", f"the id list of {stable} holds {len(allids) if isinstance(allids, list) else 'no'} of {nsrc} ids: not read")
    idset = set(allids)
    present = [c for c in cited if c in idset]
    absent = [c for c in cited if c not in idset]
    sample, n_uncited = sample_uncited(idset, set(cited), n_sample)
    want = present + sample
    if len(want) > cap["chunks"]:
        raise _Stop("read", f"{len(want)} chunks to fetch, past the cap of {cap['chunks']}: not read")
    got, cbytes = {}, 0
    for i in range(0, len(want), cap["chunks_page"]):
        ids = want[i:i + cap["chunks_page"]]
        page = fetch(dict(op="chunks", table=stable, id_column=sid, columns=scols, ids=ids))
        if not isinstance(page, list):
            raise _Stop("read", f"the chunk read of {stable} returned no list")
        cbytes += _size(page)
        if cbytes > cap["chunk_bytes"]:
            raise _Stop("read", f"the source chunks exceed the byte cap of {cap['chunk_bytes']}: not read")
        for r in page:
            if isinstance(r, dict) and isinstance(r.get(sid), str):
                got[r[sid]] = r
    lost = [c for c in want if c not in got]
    if lost:
        raise _Stop("read", f"{len(lost)} chunk(s) listed but not returned (e.g. {lost[0]}): not read")

    # ── re-run the pinned parser in the sandbox ──
    order = want
    try:
        inputs = build_inputs(d, [got[c] for c in order])
    except ValueError as exc:
        raise _Stop("declaration", str(exc))
    try:
        res = runner(repo_root, d["parser"]["module_root"], d["parser"]["pinned_files"], d["parser"]["file"], d["parser"]["function"], inputs, timeout_s=run_timeout_s)
    except Exception as exc:
        raise _Stop("spawn", f"the sandbox runner raised {type(exc).__name__}: {str(exc)[:200]}")
    if not isinstance(res, dict) or res.get("ok") is not True:
        err = res.get("error") if isinstance(res, dict) else repr(res)
        st = res.get("stage") if isinstance(res, dict) else None
        raise _Stop(st if st in ("pin", "spawn", "run", "output") else "run", f"the sandbox did not complete: {str(err)[:300]}")
    declared = {_norm_path(p["path"]) for p in d["parser"]["pinned_files"]}
    loaded = res.get("loaded_repo_files")
    if not isinstance(loaded, (list, tuple)):
        raise _Stop("loaded_files", "the sandbox did not report the repository files it loaded")
    extra = sorted({_norm_path(x, repo_root) for x in loaded} - declared)
    if extra:
        raise _Stop("loaded_files", f"the parser loaded repository file(s) that are not pinned: {extra[:3]}")
    outs = res.get("outputs")
    if not isinstance(outs, list) or len(outs) != len(order):
        raise _Stop("output", f"the sandbox returned {len(outs) if isinstance(outs, list) else 'no'} output(s) for {len(order)} chunk(s)")
    derived = {}
    for c, o in zip(order, outs):
        if not (isinstance(o, list) and all(isinstance(x, dict) for x in o)):
            raise _Stop("output", f"the parser output of chunk {c} is not a list of rows")
        derived[c] = o
    for c in absent:
        derived[c] = None
    try:
        cmp = compare_corpus_derived(stored, derived, d)
    except ValueError as exc:
        raise _Stop("output", f"the parser output cannot be aligned with the stored rows: {exc}")
    counts = dict(cmp["counts"], uncited_total=n_uncited, uncited_sampled=len(sample), cited_present=len(present), cited_absent=len(absent), source_rows=nsrc)
    block = dict(checked=True, verified=cmp["v"] == PASS, v=cmp["v"], table=table, key_columns=keys, cite_column=cite, ignore_columns=ignore, parser=pblock,
                 rows_rederived=cmp["counts"]["matched"], cited_chunks=len(present), uncited_sampled=len(sample), uncited_total=n_uncited, shadowed=cmp["counts"]["shadowed"],
                 differences=sum(cmp["difference_counts"].values()), first_differences=cmp["first_differences"], counts=counts, caps={k: cap[k] for k in ("stored_rows", "stored_bytes", "chunks", "chunk_bytes")},
                 elapsed_s=res.get("elapsed_s"))
    if cmp["v"] == NO_DET:
        return dict(v=NO_DET, stage="output", measured=f"NO_DETECTOR: corpus_derived: {cmp['measured']}", block=dict(block, stage="output", reason=cmp["measured"]))
    head = (f"re-ran the pinned parser {pblock['file']}:{pblock['function']} ({len(pins)} pinned file(s)) over {len(present)} cited chunk(s) and {len(sample)} of {n_uncited} uncited chunk(s) of {stable}; "
            f"stored table {table}: {len(stored)} row(s) compared on every column except {ignore}; ")
    return dict(v=cmp["v"], stage=None, measured=head + cmp["measured"], block=block)
