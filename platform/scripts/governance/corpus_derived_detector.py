"""corpus_derived_detector.py: the REPRODUCIBILITY detector of the `corpus_derived` declaration form (SS N-431, bg_rules).

WHAT IT PROVES. A table whose rows are the OUTPUT of a committed, sha256-pinned deterministic parser over a text corpus (bg_rules: 27 regular expressions over classical_text_chunks) is not
hand-typed prose and holds no stand-in for a missing value, IF re-running that parser reproduces the stored rows. This module re-runs the pinned parser (through an injected sandbox runner)
over the source chunks the stored rows cite, applies the declared post-processing (`derived`: drop ephemeral keys, keep only rows at or above a threshold constant of the parser, null a foreign
key not found in its reference table, first writer wins on a duplicate key) and compares the result with the stored rows, column by column. Chunks nobody cites must yield no row (the table is the FULL output of the parser): EVERY such chunk is re-run while the source holds at most CAPS['full_scan_chunks'] chunks
(only a re-run can show that a chunk whose rules were all deleted still yields them), else a bounded deterministic sample of them (the declared `scope.uncited_chunks.sample`).

THIS MODULE IS PURE apart from reading the pinned files named in the declaration (to re-hash them and to read one numeric constant by AST). Every other outside effect is injected:
  * `fetch(request: dict) -> value`   the bounded data reads (ops below); the real one is built in asset_census (capped psql), the tests pass fakes;
  * `runner(...)`                     parser_sandbox.run_pinned_parser (R2) or a fake of the same signature (the parser is called with ONE input dict per chunk);
  * `normaliser(entry) -> dict`       asset_census.normalise_corpus_derived (R1) or a fake;
  * `pin_check(entry) -> str | None`  asset_census.corpus_derived_pin_problem (R1) or None.

FETCH OPS (each request is a dict with `op`; the answer is parsed JSON-shaped data; a read that cannot be made to a verdict raises `Unread(reason)`):
  columns  {table}                                      -> [column names in table order] ([] = the table does not exist)
  count    {table, filter}                              -> int            (filter None | {column, equals}: the declared slice of a shared table)
  rows     {table, columns, order_by, limit, offset, filter} -> [ {column: value} ] ordered by `order_by` (the key columns: a total order)
  ids      {table, id_column, order_by}                 -> [id as text] ordered by `order_by` then id (the writer's own chunk order: first writer wins)
  chunks   {table, id_column, columns, ids}             -> [ {column: value} ] for the listed ids (an id that does not exist is simply absent)
  distinct {table, column, limit}                       -> [distinct non-NULL values as text, ordered], at most `limit` + 1 of them

STAGES. A NO_DETECTOR result names the stage that could not complete: declaration | pin | read | spawn | run | output | loaded_files.
It NEVER reads PASS on a truncated, capped or partial read: every cap is checked against the FULL count first, and the number of rows received must equal it.

COMPARISON VALUE NORMALISATION (`values_equal`, documented once, tested):
  * NULL equals only NULL (an empty string, 0 or [] is NOT NULL);
  * booleans equal only booleans (True != 1);
  * numbers (int, float, Decimal) are equal when their DECIMAL values are equal (`Decimal(repr(float))`: 1 == 1.0 == Decimal('1.00'); 0.8 == Decimal('0.8')); there is no tolerance;
  * a list and a tuple are the same array (a PostgreSQL array and a JSON array both arrive as a list); arrays are ORDERED; an object is its set of key/value pairs (nested numbers as above);
  * kind `json` (a declared derived.json_columns column): a text value on either side is parsed as JSON first (the parser emits `json.dumps(...)` strings for jsonb columns, the table returns the
    parsed value); a text that is not JSON stays text and then differs from any container;
  * kind `numeric` (derived.numeric_columns): a numeric text on either side is read as a number;
  * every other column: two TEXT values are compared as text, exactly (no JSON parsing, no case folding) except that two canonical UUID strings are compared case-insensitively.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

PASS, FAIL, NO_DET = "PASS", "FAIL", "NO_DETECTOR"
STAGES = ("declaration", "pin", "read", "spawn", "run", "output", "loaded_files")

# ───────────────────────────── caps (every one is checked against the FULL count before anything is read) ─────────────────────────────
# bg_rules today: 3002 stored rows (~4 MB of jsonb), a few thousand source chunks (~10 MB of text). The caps leave an order of magnitude of headroom and still bound the census' memory.
CAPS = dict(
    stored_rows=50_000,            # stored rows read (the declared slice); past it the table is NOT read, the cells read NO_DETECTOR
    stored_bytes=48 * 1024 * 1024, # JSON bytes of the stored rows read
    source_ids=200_000,            # source chunk ids listed (needed to know which chunks nobody cites, and the writer's chunk order)
    chunks=50_000,                 # source chunks fetched (cited ones plus the uncited sample)
    full_scan_chunks=25_000,       # at most this many source chunks in all (cited + uncited): EVERY uncited chunk is re-run, not a sample (see UNCITED SCAN); 0 turns the full scan off
    chunk_bytes=64 * 1024 * 1024,  # text bytes of the fetched chunks (the sandbox's own max_output_bytes default is 64_000_000)
    distinct=100_000,              # distinct values of an extra-argument / reference column
    rows_page=500,                 # stored rows per statement
    chunks_page=100,               # chunks per statement
)
ASSURANCE = "software-guarded, reviewed code only"     # what a sandbox PASS rests on (SS security review of #3423): printed on every PASS; the runner's own `assurance` is printed when it reports one
# The ONLY parser/adapter pairs this detector will run (SS security review): the pinned, reviewed bg_rules parser, through its pinned ADAPTER. A declaration naming any other (module_root, file,
# function), or pinning fewer than `must_pin` files, is refused at stage `declaration`. The adapter is the census' OWN committed file (brahmagyan/n431_rules_adapter.py; R2's __tests__/_n431_rules_adapter.py is only a test
# fixture of the sandbox). Tests pass their own `allowed`.
BG_RULES_MODULE_ROOT = "platform/python-sidecar"
BG_RULES_ADAPTER = "platform/python-sidecar/brahmagyan/n431_rules_adapter.py"
ALLOWED_PARSERS = (dict(module_root=BG_RULES_MODULE_ROOT, file=BG_RULES_ADAPTER, function="run_chunk",
                        must_pin=("platform/python-sidecar/brahmagyan/l0_rules.py", "platform/python-sidecar/brahmagyan/__init__.py", "platform/python-sidecar/brahmagyan/graha_vocabulary.py",
                                  "platform/python-sidecar/brahmagyan/l0_semantic_release.py", "platform/python-sidecar/brahmagyan/l0_semantic_release_v1.json", BG_RULES_ADAPTER)),)
ITEM_CHUNK_KEY = "chunk"                                       # the key of the chunk row in the one dict each parser call receives; R1's validator reserves the same name (asset_census.CORPUS_DERIVED_ITEM_CHUNK_KEY, pinned by a test)
RUN_TIMEOUT_S = 300                # the sandbox run; the default 120 s is thin for a few thousand chunks through 27 patterns
MAX_FIRST_DIFFERENCES = 5          # the bounded sample of differences reported by the pure comparison (key and column NAMES only, never values)
DIFF_ORDER = ("differs", "extra_stored", "missing_stored", "uncited_chunk_yields_rule", "cited_chunk_absent", "stored_row_cites_no_chunk", "stored_duplicate_key", "derived_key_collision", "blank_leaf")

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:\-]{0,127}")
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_NOT_JSON = object()


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


def _json_text(s):
    try:
        return json.loads(s, parse_float=Decimal)
    except (ValueError, TypeError):
        return s


def _numeric_text(v):
    if isinstance(v, str):
        try:
            d = Decimal(v.strip())
            return d if d.is_finite() else v
        except InvalidOperation:
            return v
    return v


def values_equal(a, b, kind: str = "plain") -> bool:
    """Are two column values equal under the normalisation documented in the module docstring? `kind` is plain | json | numeric."""
    if kind == "json":
        a, b = (_json_text(a) if isinstance(a, str) else a), (_json_text(b) if isinstance(b, str) else b)
    elif kind == "numeric":
        a, b = _numeric_text(a), _numeric_text(b)
    return canonical(a) == canonical(b)


def _plain(v):
    """A JSON-safe rendering of a key value (key values identify a row; they are not content)."""
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float) and math.isfinite(v):
        return v
    return str(v)


def count_blank_leaves(row: dict, json_columns=()) -> int:
    """The number of blank string leaves (empty or whitespace-only text) in one row, json columns walked (text parsed as JSON first). NULL is not blank."""
    n = 0

    def walk(x):
        nonlocal n
        if isinstance(x, str):
            if not x.strip():
                n += 1
        elif isinstance(x, (list, tuple)):
            for y in x:
                walk(y)
        elif isinstance(x, dict):
            for y in x.values():
                walk(y)
    for c, v in row.items():
        walk(_json_text(v) if (c in json_columns and isinstance(v, str)) else v)
    return n


# ───────────────────────────── citation ─────────────────────────────

def cite_id_of(row: dict, cite_column: str, cite_path=None):
    """(id, problem): the source id a stored row cites. The cite column's value is read at `cite_path` (a list of dict keys / array indexes; a text value is parsed as JSON first); with no path the
    value itself is the id. problem is None, "none" (nothing cited / the path does not resolve) or "malformed" (a value that is not a safe id: it can neither be fetched nor be a real chunk id)."""
    v = row.get(cite_column)
    if isinstance(v, str) and cite_path:
        v = _json_text(v)
    for p in cite_path or []:
        try:
            v = v[p]
        except (KeyError, IndexError, TypeError):
            return None, "none"
    if v is None or v == "":
        return None, "none"
    if isinstance(v, bool) or isinstance(v, (list, dict, tuple, float)):
        return None, "malformed"
    s = str(v)
    return (s, None) if _SAFE_ID.fullmatch(s) else (None, "malformed")


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


def derive_rows(raw, decl_norm: dict, ref_sets=None, threshold=None) -> list:
    """The rows the writer STORES from the rows the parser YIELDS (pure): `derived.keep_when` keeps rows whose `key` value is a number >= `threshold`; `derived.drop_keys` are removed; each
    `derived.null_unless_in` column holding a truthy value that is not in its reference set ({(table, ref_column): set of text}) becomes NULL (the writer's FK nulling). Raises ValueError on a
    row that is not an object or whose keep_when value is not a number."""
    der = decl_norm.get("derived") or {}
    drop = set(der.get("drop_keys") or [])
    kw = der.get("keep_when")
    nu = der.get("null_unless_in") or []
    out = []
    for r in raw:
        if not isinstance(r, dict):
            raise ValueError("a parser output row is not an object")
        if kw:
            q = r.get(kw["key"])
            if isinstance(q, bool) or not isinstance(q, (int, float, Decimal)):
                raise ValueError(f"keep_when key {kw['key']} is missing or not a number")
            if threshold is None or q < threshold:
                continue
        row = {k: v for k, v in r.items() if k not in drop}
        for x in nu:
            v = row.get(x["column"])
            if v and str(v) not in (ref_sets or {}).get((x["table"], x["ref_column"]), set()):
                row[x["column"]] = None
        out.append(row)
    return out


def compare_corpus_derived(stored_rows, derived_by_chunk, decl_norm, *, chunk_order=None) -> dict:
    """Compare the stored rows with the (post-processed, see `derive_rows`) parser output. PURE.

    stored_rows      list of dicts (every compared column, the key columns and the cite column);
    derived_by_chunk {chunk_id: [row dict, ...]} for EVERY chunk the parser ran on: the cited ones and the uncited sample. A cited chunk that does not exist in the source is `None`.
    decl_norm        the normalised declaration: key_columns, cite_column, cite_path, ignore_columns, derived.{json_columns, numeric_columns, duplicate_policy}.
    chunk_order      the writer's chunk order (source ids in `source.order_by` order); default: sorted by id.

    Rules. The winner of a key is the FIRST chunk, in `chunk_order`, whose output holds it (duplicate_policy first_wins: the table's unique key + ON CONFLICT DO NOTHING; `refuse`: a second chunk
    yielding the key is a difference). Each stored row must equal its key's winner on EVERY column except ignore_columns (a column present on one side only is a difference; the cite column
    is compared, so a stored row citing a chunk that is not the winner differs on it). Each winner of a CITED chunk must be stored. A winner of a chunk nobody cites (the uncited sample) must not
    exist. A winner holding a blank string leaf is a `blank_leaf` difference. Raises ValueError on malformed input (a row without its key columns, a chunk output that is not a list of objects).
    Returns dict(v, measured, first_differences, counts, difference_counts). v is PASS only when nothing differs and at least one stored row was compared; FAIL when a difference exists;
    NO_DETECTOR when there is no stored row (vacuous)."""
    keys = list(decl_norm["key_columns"])
    cite, cpath = decl_norm["cite_column"], decl_norm.get("cite_path")
    ignore = set(decl_norm.get("ignore_columns") or [])
    der = decl_norm.get("derived") or {}
    jcols, ncols = set(der.get("json_columns") or []), set(der.get("numeric_columns") or [])
    policy = der.get("duplicate_policy") or "first_wins"
    diffs: list[dict] = []

    def diff(kind, **kw):
        diffs.append(dict(kind=kind, **kw))

    def kind_of(c):
        return "json" if c in jcols else "numeric" if c in ncols else "plain"

    def differing(srow, drow):
        cols = (set(srow) | set(drow)) - ignore
        return sorted(c for c in cols if (c in srow) != (c in drow) or not values_equal(srow.get(c), drow.get(c), kind_of(c)))

    stored_by_key: dict = {}
    stored_cite: dict = {}
    claims: set = set()
    for row in stored_rows:
        k = _key_of(row, keys)
        if k in stored_by_key:
            diff("stored_duplicate_key", key=_key_dict(row, keys))
            continue
        stored_by_key[k] = row
        cid, prob = cite_id_of(row, cite, cpath)
        stored_cite[k] = cid
        if cid is None:
            diff("stored_row_cites_no_chunk", key=_key_dict(row, keys), columns=[cite])
        else:
            claims.add(cid)

    order = list(chunk_order) if chunk_order is not None else sorted(derived_by_chunk)
    rank = {c: i for i, c in enumerate(order)}
    run_order = sorted(derived_by_chunk, key=lambda c: (rank.get(c, len(rank)), c))
    winners: dict = {}
    shadowed = 0
    for cid in run_order:
        rows = derived_by_chunk[cid]
        if rows is None:
            if cid in claims:
                diff("cited_chunk_absent", chunk=cid)
            continue
        if not isinstance(rows, (list, tuple)):
            raise ValueError(f"the parser output of chunk {cid} is not a list")
        seen_here: dict = {}
        for r in rows:
            k = _key_of(r, keys)
            if k in seen_here:
                if differing(seen_here[k], r):
                    diff("derived_key_collision", chunk=cid, key=_key_dict(r, keys))
                else:
                    shadowed += 1
                continue
            seen_here[k] = r
            if k in winners:
                if policy == "refuse":
                    diff("derived_key_collision", chunk=cid, key=_key_dict(r, keys))
                else:
                    shadowed += 1
                continue
            winners[k] = (cid, r)

    matched = blank = 0
    for k, srow in stored_by_key.items():
        w = winners.get(k)
        if w is None:
            diff("extra_stored", chunk=stored_cite.get(k), key=_key_dict(srow, keys), columns=[])
            continue
        bad = differing(srow, w[1])
        if bad:
            diff("differs", chunk=w[0], key=_key_dict(srow, keys), columns=bad)
        else:
            matched += 1
    for k, (cid, drow) in winners.items():
        n = count_blank_leaves(drow, jcols)
        if n:
            blank += n
            diff("blank_leaf", chunk=cid, key=_key_dict(drow, keys), columns=sorted(c for c, v in drow.items() if count_blank_leaves({c: v}, jcols)))
        if k in stored_by_key:
            continue
        if cid in claims:
            diff("missing_stored", chunk=cid, key=_key_dict(drow, keys), columns=[])
        else:
            diff("uncited_chunk_yields_rule", chunk=cid, key=_key_dict(drow, keys), columns=[])

    uncited = [c for c in derived_by_chunk if c not in claims]
    counts = dict(stored_rows=len(stored_rows), matched=matched, shadowed=shadowed, cited_chunks=len([c for c in derived_by_chunk if c in claims]), uncited_chunks_run=len(uncited),
                  winners=len(winners), blank_leaves=blank)
    dcounts: dict = {}
    for d in diffs:
        dcounts[d["kind"]] = dcounts.get(d["kind"], 0) + 1
    diffs.sort(key=lambda d: (DIFF_ORDER.index(d["kind"]) if d["kind"] in DIFF_ORDER else len(DIFF_ORDER), str(d.get("chunk")), json.dumps(d.get("key"), sort_keys=True, default=str)))
    first = diffs[:MAX_FIRST_DIFFERENCES]
    if not stored_rows:
        return dict(v=NO_DET, measured="no stored row: nothing was re-derived (a comparison over zero rows is vacuous)", first_differences=[], counts=counts, difference_counts=dcounts)
    if diffs:
        return dict(v=FAIL, measured=f"{len(diffs)} difference(s) between the stored rows and the parser output ({dcounts}); first: {describe_differences(first)}",
                    first_differences=first, counts=counts, difference_counts=dcounts)
    return dict(v=PASS, measured=f"{matched} stored row(s) equal the parser output of their cited chunk(s); {shadowed} shadowed duplicate key(s); {counts['uncited_chunks_run']} uncited chunk(s) yielded no row; no blank value",
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


def sql_literal(s) -> str:
    """A SQL string literal for a declared slice value (standard_conforming_strings: only the quote needs doubling); refuses a backslash, NUL and control characters."""
    if not isinstance(s, str) or not s or any(ord(ch) < 32 or ch == "\\" for ch in s):
        raise ValueError(f"unsafe literal {s!r}")
    return "'" + s.replace("'", "''") + "'"


def filter_sql(flt) -> str | None:
    """`"column"::text = 'value'` for a declared slice {column, equals}; None for no slice."""
    if flt is None:
        return None
    return f'"{ident(flt["column"])}"::text = {sql_literal(flt["equals"])}'


def _where(*conds) -> str:
    cs = [f"({c})" for c in conds if c]
    return (" WHERE " + " AND ".join(cs)) if cs else ""


def columns_sql(table: str) -> str:
    t = ident(table)
    return ("SELECT coalesce(jsonb_agg(a.attname::text ORDER BY a.attnum), '[]'::jsonb)::text FROM pg_attribute a "
            f"WHERE a.attrelid = to_regclass('\"{t}\"') AND a.attnum > 0 AND NOT a.attisdropped")


def count_sql(table: str, *where) -> str:
    return f'SELECT to_jsonb(count(*))::text FROM "{ident(table)}"' + _where(*where)


def rows_sql(table: str, columns, order_by, limit: int, offset: int, *where) -> str:
    cols = ",".join(f'"{ident(c)}"' for c in dict.fromkeys(columns))
    order = ",".join(f'"{ident(c)}"' for c in order_by)
    order_t = ",".join(f't."{ident(c)}"' for c in order_by)
    return (f"SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY {order_t}), '[]'::jsonb)::text FROM "
            f"(SELECT {cols} FROM \"{ident(table)}\"{_where(*where)} ORDER BY {order} LIMIT {int(limit)} OFFSET {int(offset)}) t")


def ids_sql(table: str, id_column: str, order_by=(), *where) -> str:
    t, c = ident(table), ident(id_column)
    cols = ["\"%s\"::text AS i" % c] + [f'"{ident(o)}" AS o{n}' for n, o in enumerate(order_by)]
    keys = [f'x.o{n}' for n in range(len(order_by))] + ["x.i"]
    return f"SELECT coalesce(jsonb_agg(x.i ORDER BY {', '.join(keys)}), '[]'::jsonb)::text FROM (SELECT {', '.join(cols)} FROM \"{t}\"{_where(*where)}) x"


def chunks_sql(table: str, id_column: str, columns, ids, *where) -> str:
    t, c = ident(table), ident(id_column)
    cols = list(dict.fromkeys([c] + list(columns)))
    pairs = ",".join(f"'{ident(x)}', s.\"{ident(x)}\"" + ("::text" if x == c else "") for x in cols)
    lst = ",".join("'" + safe_id(i) + "'" for i in ids)
    return (f"SELECT coalesce(jsonb_agg(jsonb_build_object({pairs}) ORDER BY s.\"{c}\"::text), '[]'::jsonb)::text FROM \"{t}\" s "
            f"WHERE s.\"{c}\"::text IN ({lst})" + "".join(f" AND ({w})" for w in where if w))


def distinct_sql(table: str, column: str, limit: int, *where) -> str:
    t, c = ident(table), ident(column)
    w = _where('"%s" IS NOT NULL' % c, *where)
    return ("SELECT coalesce(jsonb_agg(s.v ORDER BY s.v), '[]'::jsonb)::text FROM (SELECT DISTINCT \"%s\"::text AS v FROM \"%s\"%s ORDER BY 1 LIMIT %d) s" % (c, t, w, int(limit) + 1))


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
        for c in list(s.get("text_columns") or []) + list(s.get("extra_columns") or []) + list(s.get("order_by") or []):
            ident(c)
        p = d["parser"]
        pins = p["pinned_files"]
        if not (isinstance(pins, (list, tuple)) and pins and all(isinstance(x, dict) and isinstance(x.get("path"), str) and isinstance(x.get("sha256"), str) for x in pins)):
            return "parser.pinned_files must be a non-empty list of {path, sha256}"
        if p["file"] not in [x["path"] for x in pins]:
            return "parser.file is not one of the pinned files"
        if not (isinstance(p.get("function"), str) and p["function"] and isinstance(p.get("module_root"), str)):
            return "parser.function / parser.module_root missing"
        if p.get("input_shape", "chunk_row_dict") != "chunk_row_dict":
            return f"unsupported parser.input_shape {p.get('input_shape')!r}"
        for a in p.get("extra_args") or []:
            if a.get("kind") != "distinct_values":
                return f"unsupported extra argument kind {a.get('kind')!r}"
            ident(a["name"]), ident(a["table"]), ident(a["column"])
        der = d.get("derived") or {}
        for x in der.get("null_unless_in") or []:
            ident(x["column"]), ident(x["table"]), ident(x["ref_column"])
        if any(k in set(d.get("ignore_columns") or []) for k in keys) or d["cite_column"] in set(d.get("ignore_columns") or []):
            return "a key or the cite column cannot be an ignored column"
        n = ((d.get("scope") or {}).get("uncited_chunks") or {}).get("sample")
        if not (isinstance(n, int) and not isinstance(n, bool) and n >= 1):
            return "scope.uncited_chunks.sample must be an integer >= 1 (an uncited sample that is skipped would not test that the table is the FULL output of the parser)"
        st = (d.get("scope") or {}).get("stored", "all")
        if st != "all":
            if not (isinstance(st, dict) and set(st) == {"column", "equals"}):
                return "scope.stored must be 'all' or {column, equals}"
            ident(st["column"])
            sql_literal(st["equals"])
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


def build_inputs(decl_norm: dict, chunk_rows, extras: dict) -> list:
    """The sandbox inputs, one per chunk, in order. Shape `chunk_row_dict`: ONE dict per chunk, {"chunk": {id_column, text_columns..., extra_columns...}, <each declared extra argument BY NAME>:
    a sorted list of its distinct values}. The sandbox calls function(item) with that one dict; the pinned ADAPTER function maps it onto the parser's real signature (the committed
    brahmagyan/n431_rules_adapter.run_chunk: `extract_rules_from_chunk(item["chunk"], set(item["valid_text_ids"]))` plus the writer's quality threshold). ONE place to adapt if the item layout changes. Raises ValueError for an unknown shape."""
    shape = (decl_norm.get("parser") or {}).get("input_shape") or "chunk_row_dict"
    if shape != "chunk_row_dict":
        raise ValueError(f"unsupported parser.input_shape {shape!r}")
    if ITEM_CHUNK_KEY in extras:
        raise ValueError(f"an extra argument cannot be named {ITEM_CHUNK_KEY!r}: that key holds the chunk row")
    return [dict({ITEM_CHUNK_KEY: dict(r)}, **{k: list(v) for k, v in extras.items()}) for r in chunk_rows]


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


def verify_pins(repo_root, pins) -> tuple[str | None, dict]:
    """(problem, {path: text}): every pinned file re-hashed from its bytes on disk (sha256) and equal to the declared digest. Defensive and independent of the runner's own check. The texts of
    the files are returned (decoded) so a constant can be read from the SAME bytes that were hashed."""
    root = Path(repo_root).resolve()
    texts = {}
    for p in pins:
        try:
            fp = (root / p["path"]).resolve()
            if not (fp == root or root in fp.parents) or not fp.is_file():
                return f"pinned file {p['path']} does not exist inside the repository", {}
            data = fp.read_bytes()
        except OSError as exc:
            return f"pinned file {p['path']} cannot be read ({type(exc).__name__})", {}
        if hashlib.sha256(data).hexdigest() != p["sha256"]:
            return f"pinned file {p['path']} no longer hashes to its declared sha256", {}
        texts[p["path"]] = data.decode("utf-8", errors="replace")
    return None, texts


def _assigned_values(tree, name: str) -> list:
    hits = []
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            hits.append(n.value)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name and n.value is not None:
            hits.append(n.value)
    return hits


def _numeric_literal(v) -> bool:
    return isinstance(v, ast.Constant) and isinstance(v.value, (int, float)) and not isinstance(v.value, bool)


def module_constant(source: str, name: str):
    """The value of the single numeric literal assigned to module-level `name` in `source` (AST; nothing is run). ValueError if there is not exactly one such literal."""
    hits = _assigned_values(ast.parse(source), name)
    if len(hits) != 1 or not _numeric_literal(hits[0]):
        raise ValueError(f"{name} is not a single numeric literal at module level")
    return hits[0].value


def _find_constant(texts: dict, parser_file: str, name: str):
    """The numeric literal `name`: in the parser file when it assigns the name (a bad assignment there is refused, never rescued by another file), else in exactly one other pinned python file (the
    parser file may be a thin pinned ADAPTER over the module that holds the constant). The same rule as R1's pin check. Raises _Stop(pin) when no pinned file, or more than one, defines it as a
    single numeric literal."""
    order = [parser_file] + [p for p in texts if p != parser_file and p.endswith(".py")]
    found = []
    for p in order:
        try:
            tree = ast.parse(texts[p])
        except (SyntaxError, ValueError):
            continue
        hits = _assigned_values(tree, name)
        if len(hits) == 1 and _numeric_literal(hits[0]):
            found.append((p, hits[0].value))
        if p == parser_file and hits:
            break
    if len(found) != 1:
        raise _Stop("pin", f"keep_when constant {name} is {'defined in several pinned files' if found else 'not a single numeric literal in the parser file or, when the parser file does not assign it, any other pinned python file'}")
    return found[0][1]


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
    return dict(v=NO_DET, stage=stage, measured=f"NO_DETECTOR: corpus_derived stage '{stage}' could not complete: {detail}",
                block=dict(checked=True, verified=False, v=NO_DET, stage=stage, reason=detail, **block))


def _size(x) -> int:
    return len(json.dumps(x, default=str, ensure_ascii=False).encode("utf-8"))


def detect_corpus_derived(entry, *, fetch, runner, normaliser, repo_root, pin_check=None, caps=None, run_timeout_s: int = RUN_TIMEOUT_S, allowed=None) -> dict:
    """Re-derive the stored rows of the declared table with the pinned parser and compare. Returns dict(v, stage, measured, block); `v` is PASS / FAIL / NO_DETECTOR; `stage` (NO_DETECTOR only)
    names the stage that did not complete; `block` is the record the cells carry (checked, verified, counts, parser pins, first_differences, and R1's fields: table, stored_rows, matched_rows,
    mismatches, chunks_run, uncited_sampled, uncited_yield, blank_leaves, parser{file, function, sha256}, pinned_files, loaded_repo_files)."""
    cap = dict(CAPS, **(caps or {}))
    try:
        return _detect(entry, fetch, runner, normaliser, repo_root, pin_check, cap, run_timeout_s, ALLOWED_PARSERS if allowed is None else allowed)
    except _Stop as s:
        return _no(s.stage, s.detail)
    except Unread as exc:
        return _no("read", str(exc))


def _detect(entry, fetch, runner, normaliser, repo_root, pin_check, cap, run_timeout_s, allowed) -> dict:
    try:
        d = normaliser(entry)
    except Exception as exc:                          # the normaliser is R1's: whatever it refuses is a declaration problem, never a verdict
        raise _Stop("declaration", f"the declaration is refused by the normaliser ({type(exc).__name__}: {str(exc)[:200]})")
    bad = _decl_problem(d)
    if bad:
        raise _Stop("declaration", bad)
    par = d["parser"]
    pins = pins_summary(d)
    ok_pair = [a for a in allowed if a["module_root"] == par["module_root"] and a["file"] == par["file"] and a["function"] == par["function"]]
    if not ok_pair:
        raise _Stop("declaration", f"the parser {par['file']}:{par['function']} (module_root {par['module_root']}) is not one this detector may run: only the reviewed, pinned bg_rules parser through its pinned adapter is allowed")
    missing_pins = sorted(set(ok_pair[0]["must_pin"]) - {p["path"] for p in pins})
    if missing_pins:
        raise _Stop("declaration", f"the declaration does not pin {missing_pins[:3]}: the parser, its closure, its data file and its adapter must all be pinned in the committed declaration")
    # ── the pins: R1's check against the tree (import closure, function, constant), then our own re-hash of every pinned file (data files included) ──
    if pin_check is not None:
        pb = pin_check(entry)
        if pb:
            raise _Stop("pin", str(pb)[:400])
    pb, texts = verify_pins(repo_root, pins)
    if pb:
        raise _Stop("pin", pb)
    der = d.get("derived") or {}
    threshold = None
    if der.get("keep_when"):
        threshold = _find_constant(texts, par["file"], der["keep_when"]["at_least_constant"])
    table, keys, cite, cpath = d["table"], list(d["key_columns"]), d["cite_column"], d.get("cite_path")
    ignore = list(d.get("ignore_columns") or [])
    src = d["source"]
    stable, sid = src["table"], src["id_column"]
    scols = list(dict.fromkeys(list(src.get("text_columns") or []) + list(src.get("extra_columns") or [])))
    sorder = list(src.get("order_by") or [sid])
    n_sample = d["scope"]["uncited_chunks"]["sample"]
    flt = None if (d.get("scope") or {}).get("stored", "all") == "all" else dict(d["scope"]["stored"])
    pblock = dict(file=par["file"], function=par["function"], sha256=next(p["sha256"] for p in pins if p["path"] == par["file"]))

    # ── stored rows: ALL of them (the declared slice), every compared column ──
    tcols = fetch(dict(op="columns", table=table))
    if not (isinstance(tcols, list) and tcols):
        raise _Stop("declaration", f"table {table} does not exist or has no readable column")
    miss = [c for c in keys + [cite] + ([flt["column"]] if flt else []) if c not in tcols]
    if miss:
        raise _Stop("declaration", f"table {table} has no column {miss}")
    read_cols = [c for c in tcols if c not in set(ignore) or c == cite]
    n = fetch(dict(op="count", table=table, filter=flt))
    if not (isinstance(n, int) and not isinstance(n, bool) and n >= 0):
        raise _Stop("read", f"unreadable row count of {table}: {n!r}")
    if n > cap["stored_rows"]:
        raise _Stop("read", f"{table} holds {n} rows, past the read cap of {cap['stored_rows']}: not read")
    if n == 0:
        raise _Stop("read", f"{table} holds no row in the declared slice: nothing to re-derive (vacuous)")
    stored, nbytes, off = [], 0, 0
    while off < n:
        page = fetch(dict(op="rows", table=table, columns=read_cols, order_by=keys, limit=cap["rows_page"], offset=off, filter=flt))
        if not isinstance(page, list) or not page:
            raise _Stop("read", f"the read of {table} stopped at {off} of {n} rows: not read")
        nbytes += _size(page)
        if nbytes > cap["stored_bytes"]:
            raise _Stop("read", f"the stored rows of {table} exceed the byte cap of {cap['stored_bytes']}: not read")
        stored.extend(page)
        off += cap["rows_page"]
    if len(stored) != n or fetch(dict(op="count", table=table, filter=flt)) != n:
        raise _Stop("read", f"{table} read {len(stored)} row(s) of {n} (or the row count changed during the read): not read")

    # ── the cited chunks, the writer's chunk order and the uncited sample ──
    cited = set()
    for r in stored:
        if not isinstance(r, dict):
            raise _Stop("read", "a stored row is not an object")
        cid, _prob = cite_id_of(r, cite, cpath)
        if cid is not None:
            cited.add(cid)
    nsrc = fetch(dict(op="count", table=stable, filter=None))
    if not (isinstance(nsrc, int) and not isinstance(nsrc, bool) and nsrc >= 0):
        raise _Stop("read", f"unreadable row count of {stable}: {nsrc!r}")
    if nsrc > cap["source_ids"]:
        raise _Stop("read", f"{stable} holds {nsrc} rows, past the id-list cap of {cap['source_ids']}: the uncited chunks cannot be established, not read")
    allids = fetch(dict(op="ids", table=stable, id_column=sid, order_by=sorder))
    if not isinstance(allids, list) or len(allids) != nsrc:
        raise _Stop("read", f"the id list of {stable} holds {len(allids) if isinstance(allids, list) else 'no'} of {nsrc} ids: not read")
    idset = set(allids)
    absent = sorted(c for c in cited if c not in idset)
    if absent:
        raise _Stop("read", f"{len(absent)} stored cite(s) do not resolve to a row of {stable} (e.g. {absent[0]}): the stored rows cannot be re-derived")
    present = sorted(cited)
    if not present:
        raise _Stop("read", "no stored row cites a source chunk: there is nothing to re-derive (zero inputs are never a PASS)")
    sample, n_uncited = sample_uncited(idset, cited, n_sample)
    full_scan = len(idset) <= cap["full_scan_chunks"]
    if full_scan:                                     # UNCITED SCAN: a chunk whose rules were ALL deleted is no longer cited by any stored row, so only re-running the parser over it can show that it yields
        sample = sorted(i for i in idset if i not in cited)
    want = present + sample
    if len(want) > cap["chunks"]:
        raise _Stop("read", f"{len(want)} chunks to fetch, past the cap of {cap['chunks']}: not read")
    got, cbytes = {}, 0
    for i in range(0, len(want), cap["chunks_page"]):
        page = fetch(dict(op="chunks", table=stable, id_column=sid, columns=scols, ids=want[i:i + cap["chunks_page"]]))
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

    # ── the extra arguments and the reference sets (bounded distinct reads) ──
    def distinct(t, c):
        vals = fetch(dict(op="distinct", table=t, column=c, limit=cap["distinct"]))
        if not isinstance(vals, list):
            raise _Stop("read", f"the distinct read of {t}.{c} returned no list")
        if len(vals) > cap["distinct"]:
            raise _Stop("read", f"{t}.{c} holds more than {cap['distinct']} distinct values: not read")
        return sorted(str(v) for v in vals)
    extras = {a["name"]: distinct(a["table"], a["column"]) for a in par.get("extra_args") or []}
    ref_sets = {}
    for x in der.get("null_unless_in") or []:
        ref_sets[(x["table"], x["ref_column"])] = set(distinct(x["table"], x["ref_column"]))

    # ── re-run the pinned parser in the sandbox ──
    order = want
    try:
        inputs = build_inputs(d, [got[c] for c in order], extras)
    except ValueError as exc:
        raise _Stop("declaration", str(exc))
    try:
        res = runner(repo_root, par["module_root"], par["pinned_files"], par["file"], par["function"], inputs, timeout_s=run_timeout_s)
    except Exception as exc:
        raise _Stop("spawn", f"the sandbox runner raised {type(exc).__name__}: {str(exc)[:200]}")
    if not isinstance(res, dict) or res.get("ok") is not True:
        err = res.get("error") if isinstance(res, dict) else repr(res)
        st = res.get("stage") if isinstance(res, dict) else None
        more = f" (unpinned files: {res['unpinned_files'][:5]})" if isinstance(res, dict) and isinstance(res.get("unpinned_files"), list) else ""
        raise _Stop(st if st in ("pin", "spawn", "run", "output") else "run", f"the sandbox did not complete: {str(err)[:300]}{more}")
    declared = {_norm_path(p["path"]) for p in par["pinned_files"]}
    loaded = res.get("loaded_repo_files")
    if not isinstance(loaded, (list, tuple)):
        raise _Stop("loaded_files", "the sandbox did not report the repository files it loaded")
    loaded_n = sorted({_norm_path(x, repo_root) for x in loaded})
    extra = sorted(set(loaded_n) - declared)
    if extra:
        raise _Stop("loaded_files", f"the parser loaded repository file(s) that are not pinned: {extra[:3]}")
    if _norm_path(par["file"]) not in loaded_n:
        raise _Stop("loaded_files", f"the sandbox did not report loading the parser file {par['file']}")
    outs = res.get("outputs")
    if not isinstance(outs, list) or len(outs) != len(order):
        raise _Stop("output", f"the sandbox returned {len(outs) if isinstance(outs, list) else 'no'} output(s) for {len(order)} chunk(s)")
    derived = {}
    try:
        for c, o in zip(order, outs):
            if not (isinstance(o, list) and all(isinstance(x, dict) for x in o)):
                raise ValueError(f"the parser output of chunk {c} is not a list of rows")
            derived[c] = derive_rows(o, d, ref_sets, threshold)
        cmp = compare_corpus_derived(stored, derived, d, chunk_order=allids)
    except ValueError as exc:
        raise _Stop("output", f"the parser output cannot be aligned with the stored rows: {exc}")
    assurance = res.get("assurance") if isinstance(res.get("assurance"), str) and res.get("assurance") else ASSURANCE
    dc = cmp["difference_counts"]
    mism = sum(v for k, v in dc.items() if k != "blank_leaf")
    block = dict(checked=True, verified=cmp["v"] == PASS, v=cmp["v"], table=table, key_columns=keys, cite_column=cite, ignore_columns=ignore, parser=pblock,
                 pinned_files=[p["path"] for p in pins], loaded_repo_files=loaded_n,
                 stored_rows=len(stored), matched_rows=cmp["counts"]["matched"], mismatches=mism, chunks_run=len(want), cited_chunks=len(present),
                 uncited_sampled=len(sample), uncited_total=n_uncited, uncited_scan="full" if full_scan else "sample", uncited_yield=dc.get("uncited_chunk_yields_rule", 0), blank_leaves=cmp["counts"]["blank_leaves"],
                 shadowed=cmp["counts"]["shadowed"], first_differences=cmp["first_differences"], difference_counts=dc,
                 assurance=assurance, assurance_from_runner=isinstance(res.get("assurance"), str) and bool(res.get("assurance")),
                 extra_args=sorted(extras), keep_when_threshold=threshold, caps={k: cap[k] for k in ("stored_rows", "stored_bytes", "chunks", "chunk_bytes")}, elapsed_s=res.get("elapsed_s"))
    if cmp["v"] == PASS and (cmp["counts"]["matched"] < 1 or not present or not want):
        cmp = dict(cmp, v=NO_DET, measured="nothing was compared (no matched stored row or no cited chunk): a PASS over zero comparisons is refused")
        block = dict(block, verified=False, v=NO_DET)
    if cmp["v"] == NO_DET:
        return dict(v=NO_DET, stage="output", measured=f"NO_DETECTOR: corpus_derived: {cmp['measured']}", block=dict(block, stage="output", reason=cmp["measured"]))
    head = (f"re-ran the pinned parser {pblock['file']}:{pblock['function']} ({len(pins)} pinned file(s)) over {len(present)} cited chunk(s) and {'all ' + str(n_uncited) if full_scan else str(len(sample)) + ' of ' + str(n_uncited)} uncited chunk(s) of {stable}; "
            f"[assurance: {assurance}] stored table {table}{'' if flt is None else ' (' + flt['column'] + ' = ' + flt['equals'] + ')'}: {len(stored)} row(s) compared on every column except {ignore}; ")
    return dict(v=cmp["v"], stage=None, measured=head + cmp["measured"], block=block)
