"""carriage_d3.py: the generic D3 (independent re-derivation) engine for the Carr gate (SS N-73 (2): for an asset that COMPUTES a value, the applicable
carriage check is D3, a second route to the same value; N-101: D3 PASS needs every row, a same-code re-derivation never passes, a tolerance is a declaration).

Pure functions. No database, no network, no clock: asset_census.py passes in the rows it read read-only, so every case is testable from fixtures. An asset DECLARES
its D3 in asset_declarations.json (`carriage.applies = "D3"`, nature computation | derivation, plus a `carriage.spec`); an asset without a spec is never measured here.

METHODS (like carriage_d1.KERNELS): a CLOSED registry of reviewed re-derivation routes. A spec names one by `method`; an unknown id is refused. A method states, in code and
in its `rule_text`: the tables it may run on (a false `computation` declaration cannot borrow a method built for another table), its `independence` class
(`independent_formula` | `relation` | `same_code`), the maximum tolerance it will accept per column (a declared tolerance above it is refused), the conventions the
re-derivation depends on and the spec must DECLARE (e.g. the ephemeris position convention), the reads it needs, and an optional backend probe (the reference leg's
ephemeris identity, recorded in the record, never assumed). Adding a method is a reviewed edit (a new PR with its own pin), never a declaration. The methods live in
`carriage_d3_methods.py` (they import the astronomy library; this module does not).

THE SPEC (validated by `validate_spec`, read by `d3_measure`):
  method           the id of a method in METHODS
  table            the asset's own table (the registry target_table; asserted by the caller)
  read             {columns: [...], where: [{column, equals: v} | {column, in: [v, ...]}], chart_scoped: bool, inputs?: {table, columns, id_column}}: the STATED read, closed (no SQL).
                   `inputs` is a second read of the chart's own birth parameters (one row: WHERE id_column = <census chart>), required iff the method names an `inputs_table`
  key              the logical-row key columns (after the method's `logical_rows`): the identity of a row in every record
  columns          {logical column: {kind: circular_deg | circular_30 | linear | exact, tol: number, basis: text}}: what is re-derived, the comparator and the DECLARED tolerance
  strata           optional: one logical column the record groups its counts by (reporting; a verdict never rests on a sample)
  sample           optional: {per_stratum: n, seed: text}: re-derive only n rows per stratum (deterministic by hash). A sampled run can never read PASS.
  expected_rows    the number of logical rows the table must hold (completeness: a dropped row is not a PASS), or the string "method": the method's own INDEPENDENT completeness check
                   (it re-enumerates the events and compares counts), for a table whose horizon rolls
  conventions      {name: {value, evidence}}: every convention the method names as required, declared with a pointer
  uncovered        [{column, reason, evidence}]: logical columns the method does not re-derive, declared; any entry caps PARTIAL
  backend          {allowed: [names], basis: text}: the reference leg backends the declared tolerance covers (only for a method that probes a backend)
  (a method may also mark a re-derived value AMBIGUOUS: {column: {note, neighbours: [values]}}, within a reviewed margin of a classification boundary; ONLY a stored value in `neighbours` is then accepted, listed in boundary_tolerated)
  boundary         optional {column: {source: logical column, width: number, cells: n}}: a discrete value derived from a continuous one is accepted at a cell edge only when the
                   stored cell is the NEIGHBOUR of the reference cell (modulo `cells`) and the reference value is within the declared tolerance of the edge (listed, never silent)
A PASS needs: an `independent_formula` method AND every logical row re-derived (no sample) AND row count equal to `expected_rows` AND zero mismatch AND no uncovered
column AND the backend (when probed) in the declared allowed set. A mismatch is PARTIAL naming up to 20 rows (D1 shape); if NO checked row agrees it is FAIL. Anything that
cannot be established (unknown method, a method not allowed on the table, a missing convention, an unreadable backend, no rows, the reference engine absent) is NO_DETECTOR,
never PASS, and the reason is in the record.

STATED READS (a D3 measurement makes exactly the SELECT(s) in the spec's `read`, listed in every record as `reads`): the asset's own table restricted to the declared
columns and closed predicate (and `chart_id = <census chart>` when chart_scoped), plus the optional `inputs` read of the same table.

WHAT A D3 PASS DOES AND DOES NOT SAY (stated in every record, `claims`): the second route is a different CODE PATH, not necessarily different data (the reference
ephemeris leg shares the ephemeris with the writer; the record names the backend); a tolerance is the declared one with its stated basis; a D3 PASS says nothing about
whether the declared convention is the right one (it is a declared fact the strategist reviews); completeness is only what `expected_rows` declares.
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import re

NO_DET, PASS_V, PARTIAL, FAIL = "NO_DETECTOR", "PASS", "PARTIAL", "FAIL"
INDEPENDENCE = ("independent_formula", "relation", "same_code")
KINDS = ("circular_deg", "circular_30", "linear", "exact")
_PERIOD = {"circular_deg": 360.0, "circular_30": 30.0}      # circular_30: a degree-in-sign, which wraps at the sign edge
MAX_NAMED = 20
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SCOPE_VALUE = re.compile(r"[A-Za-z0-9_.:+\- ]{1,80}")
MAX_WHERE = 4
MAX_WHERE_VALUES = 16


class SpecError(ValueError):
    """A D3 spec is malformed."""


# ───────────────────────── comparison primitives ─────────────────────────

def ang_diff(a: float, b: float, period: float = 360.0) -> float:
    """Smallest absolute difference of two angles in degrees on a circle of the given period (360 for a longitude, 30 for a degree in a sign)."""
    d = abs(a - b) % period
    return min(d, period - d)


def compare_value(kind: str, stored, ref, tol):
    """(agree, residual|None). `exact` compares with ==; the numeric kinds need two finite numbers (bool and str are not numbers). None vs None agree only for `exact`."""
    if kind == "exact":
        if stored is None and ref is None:
            return True, None
        if isinstance(stored, bool) != isinstance(ref, bool):
            return False, None
        return stored == ref, None
    if stored is None and ref is None:
        return True, None            # not claimed and not derivable: nothing disagrees
    ok = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
    if not (ok(stored) and ok(ref)):
        return False, None
    r = ang_diff(float(stored), float(ref), _PERIOD[kind]) if kind in _PERIOD else abs(float(stored) - float(ref))
    return r <= tol, r


def tol_for(tol, row: dict):
    """The tolerance in force for one logical row: a number, or {default, by: {column, values: {value: number}}} (a tolerance DECLARED per key value, e.g. per body: a
    true node and a planet do not share one ephemeris envelope)."""
    if isinstance(tol, dict):
        by = tol.get("by")
        if by is not None:
            v = row.get(by["column"])
            if isinstance(v, str) and v in by["values"]:
                return by["values"][v]
        return tol["default"]
    return tol


def _num_ok(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0


def rank_key(seed: str, key: str) -> bytes:
    return hashlib.sha256(f"{seed}|{key}".encode("utf-8")).digest()


def rows_digest(items) -> str:
    """sha256 over the canonical JSON of the logical rows read (the identity of the population a verdict was reached on)."""
    return hashlib.sha256(json.dumps(items, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


# ───────────────────────── spec validation (pure syntax) ─────────────────────────

def _where_problem(w, where: str):
    if not (isinstance(w, list) and len(w) <= MAX_WHERE):
        return f"{where} must be a list of at most {MAX_WHERE} closed conditions"
    for c in w:
        if not (isinstance(c, dict) and isinstance(c.get("column"), str) and _IDENT.fullmatch(c["column"]) and len(c) == 2 and (set(c) - {"column"}) <= {"equals", "in"}):
            return f"{where} entries are {{column, equals: v}} or {{column, in: [v, ...]}}"
        op = next(iter(set(c) - {"column"}))
        vals = [c[op]] if op == "equals" else c[op]
        if not (isinstance(vals, list) and 1 <= len(vals) <= MAX_WHERE_VALUES and all(isinstance(x, str) and _SCOPE_VALUE.fullmatch(x) for x in vals)):
            return f"{where} values must be 1..{MAX_WHERE_VALUES} plain strings ([A-Za-z0-9_.:+- ], no quote or SQL)"
    return None


def validate_spec(spec, where: str, methods=None, asset_id=None) -> dict:
    """The spec, or SpecError naming the offending field. Pure syntax plus the method's own declared limits; it does not look at any database."""
    methods = load_methods() if methods is None else methods
    if not isinstance(spec, dict):
        raise SpecError(f"{where}.spec must be an object")
    req = {"method", "table", "read", "key", "columns", "expected_rows", "conventions", "uncovered"}
    opt = {"strata", "sample", "backend", "boundary"}
    if sorted(set(spec) - req - opt):
        raise SpecError(f"{where}.spec: unknown field(s) {sorted(set(spec) - req - opt)}")
    if sorted(req - set(spec)):
        raise SpecError(f"{where}.spec: missing field(s) {sorted(req - set(spec))}")
    m = methods.get(spec["method"]) if isinstance(spec["method"], str) else None
    if m is None:
        raise SpecError(f"{where}.spec.method {spec['method']!r} is not a method of the closed registry METHODS {sorted(methods)}")
    if asset_id is not None and asset_id not in m["assets"]:
        raise SpecError(f"{where}.spec.method {spec['method']!r} serves {list(m['assets'])}, not {asset_id!r}: a computation declaration cannot borrow a method built for another asset")
    if not (isinstance(spec["table"], str) and _IDENT.fullmatch(spec["table"])):
        raise SpecError(f"{where}.spec.table must be a table identifier")
    if spec["table"] not in m["tables"]:
        raise SpecError(f"{where}.spec.table {spec['table']!r} is not a table method {spec['method']!r} may run on {list(m['tables'])}: a computation declaration cannot borrow a method built for another table")
    rd = spec["read"]
    if not (isinstance(rd, dict) and {"columns", "where", "chart_scoped"} <= set(rd) <= {"columns", "where", "chart_scoped", "inputs"}
            and isinstance(rd["columns"], list) and rd["columns"] and all(isinstance(c, str) and _IDENT.fullmatch(c) for c in rd["columns"])
            and isinstance(rd["chart_scoped"], bool)):
        raise SpecError(f"{where}.spec.read must be {{columns: [...], where: [...], chart_scoped: bool, inputs?: {{where: [...]}}}}")
    bad = _where_problem(rd["where"], f"{where}.spec.read.where")
    if bad:
        raise SpecError(bad)
    it = m.get("inputs_table")
    if it is None and "inputs" in rd:
        raise SpecError(f"{where}.spec.read.inputs is not used by method {spec['method']!r}")
    if it is not None:
        ri = rd.get("inputs")
        if not (isinstance(ri, dict) and set(ri) == {"table", "columns", "id_column"} and ri["table"] == it["table"] and isinstance(ri["id_column"], str)
                and _IDENT.fullmatch(ri["id_column"]) and isinstance(ri["columns"], list) and set(it["columns"]) <= set(ri["columns"])
                and all(isinstance(c, str) and _IDENT.fullmatch(c) for c in ri["columns"])):
            raise SpecError(f"{where}.spec.read.inputs must be {{table: {it['table']!r}, columns: (at least {list(it['columns'])}), id_column}}: the method needs the chart's birth parameters")
    if not (isinstance(spec["key"], list) and spec["key"] and all(isinstance(c, str) and _IDENT.fullmatch(c) for c in spec["key"]) and len(set(spec["key"])) == len(spec["key"])):
        raise SpecError(f"{where}.spec.key must be a non-empty list of distinct logical column names")
    cols = spec["columns"]
    if not (isinstance(cols, dict) and cols):
        raise SpecError(f"{where}.spec.columns must map each re-derived logical column to {{kind, tol, basis}}")
    for c, d in cols.items():
        if not (isinstance(c, str) and _IDENT.fullmatch(c) and isinstance(d, dict) and set(d) == {"kind", "tol", "basis"} and d["kind"] in KINDS
                and isinstance(d["basis"], str) and len(d["basis"].split()) >= 3 and "\n" not in d["basis"]):
            raise SpecError(f"{where}.spec.columns[{c}] must be {{kind: {list(KINDS)}, tol, basis}} with a stated basis (at least 3 words)")
        if d["kind"] == "exact":
            if d["tol"] != 0 or isinstance(d["tol"], bool):
                raise SpecError(f"{where}.spec.columns[{c}]: an exact comparison has tolerance 0")
        elif _num_ok(d["tol"]):
            pass
        elif (isinstance(d["tol"], dict) and set(d["tol"]) == {"default", "by"} and _num_ok(d["tol"]["default"]) and isinstance(d["tol"]["by"], dict)
              and set(d["tol"]["by"]) == {"column", "values"} and d["tol"]["by"]["column"] in spec["key"] and isinstance(d["tol"]["by"]["values"], dict)
              and d["tol"]["by"]["values"] and all(isinstance(k, str) and _num_ok(v) for k, v in d["tol"]["by"]["values"].items())):
            pass
        else:
            raise SpecError(f"{where}.spec.columns[{c}].tol must be a finite non-negative number or {{default, by: {{column: a key column, values: {{value: number}}}}}}")
        mx = m["max_tol"].get(c)
        if mx is None:
            raise SpecError(f"{where}.spec.columns[{c}]: method {spec['method']!r} does not re-derive column {c!r} (its columns: {sorted(m['max_tol'])})")
        decl = [d["tol"]] if not isinstance(d["tol"], dict) else [d["tol"]["default"]] + list(d["tol"]["by"]["values"].values())
        lim = [mx] if not isinstance(mx, dict) else [mx["default"]]
        keyed = [(None, d["tol"] if not isinstance(d["tol"], dict) else d["tol"]["default"])]
        if isinstance(d["tol"], dict):
            keyed += list(d["tol"]["by"]["values"].items())
        for kv, t in keyed:
            cap = mx if not isinstance(mx, dict) else (mx["values"].get(kv, mx["default"]) if kv is not None else mx["default"])
            if t > cap:
                raise SpecError(f"{where}.spec.columns[{c}].tol {t} exceeds the method's reviewed maximum {cap}: a tolerance is a declaration, never a fudge")
    if sorted(set(spec["key"]) & set(cols)):
        raise SpecError(f"{where}.spec.key and spec.columns must be disjoint")
    er = spec["expected_rows"]
    if er == "method":
        if m.get("completeness") is None:
            raise SpecError(f"{where}.spec.expected_rows 'method' needs a method with an independent completeness check; {spec['method']!r} has none")
    elif not (isinstance(er, int) and not isinstance(er, bool) and er >= 1):
        raise SpecError(f"{where}.spec.expected_rows must be a positive integer (or 'method': the method's own independent completeness check, for a table with a rolling horizon)")
    cv = spec["conventions"]
    need = set(m["required_conventions"])
    if not (isinstance(cv, dict) and set(cv) == need and all(isinstance(v, dict) and set(v) == {"value", "evidence"} and isinstance(v["value"], str) and v["value"].strip()
                                                              and isinstance(v["evidence"], str) and v["evidence"].strip() for v in cv.values())):
        raise SpecError(f"{where}.spec.conventions must declare exactly {sorted(need)} each as {{value, evidence}}: the re-derivation depends on them and they are part of the claim")
    for name, v in cv.items():
        allowed = m["required_conventions"][name]
        if allowed is not None and v["value"] not in allowed:
            raise SpecError(f"{where}.spec.conventions[{name}].value {v['value']!r} is not one the method implements {list(allowed)}")
    un = spec["uncovered"]
    if not (isinstance(un, list) and all(isinstance(u, dict) and set(u) == {"column", "reason", "evidence"} and all(isinstance(u[k], str) and u[k].strip() for k in u)
                                         and len(u["reason"].split()) >= 3 for u in un)):
        raise SpecError(f"{where}.spec.uncovered must be a list of {{column, reason, evidence}} (a real reason of at least 3 words)")
    if {u["column"] for u in un} & set(cols):
        raise SpecError(f"{where}.spec.uncovered names a column that is also re-derived")
    if "strata" in spec and not (isinstance(spec["strata"], str) and (spec["strata"] in cols or spec["strata"] in spec["key"])):
        raise SpecError(f"{where}.spec.strata must name a key or re-derived logical column")
    if "sample" in spec:
        sm = spec["sample"]
        if not (isinstance(sm, dict) and set(sm) == {"per_stratum", "seed"} and isinstance(sm["per_stratum"], int) and not isinstance(sm["per_stratum"], bool)
                and sm["per_stratum"] >= 1 and isinstance(sm["seed"], str) and sm["seed"].strip() and "strata" in spec):
            raise SpecError(f"{where}.spec.sample must be {{per_stratum: n >= 1, seed}} and needs `strata`")
    if m.get("backend_probe") is not None:
        bk = spec.get("backend")
        if not (isinstance(bk, dict) and set(bk) == {"allowed", "basis"} and isinstance(bk["allowed"], list) and bk["allowed"]
                and all(a in m["backends"] for a in bk["allowed"]) and isinstance(bk["basis"], str) and len(bk["basis"].split()) >= 3):
            raise SpecError(f"{where}.spec.backend must be {{allowed: a non-empty subset of {list(m['backends'])}, basis}}: the declared tolerance must say which reference backends it covers")
    elif "backend" in spec:
        raise SpecError(f"{where}.spec.backend is only for a method that probes a backend")
    if "boundary" in spec:
        b = spec["boundary"]
        if not (isinstance(b, dict) and all(k in cols and cols[k]["kind"] == "exact" and isinstance(v, dict) and set(v) == {"source", "width", "cells"} and v["source"] in cols
                                            and cols[v["source"]]["kind"] != "exact" and isinstance(v["width"], (int, float)) and not isinstance(v["width"], bool) and v["width"] > 0
                                            and isinstance(v["cells"], int) and not isinstance(v["cells"], bool) and v["cells"] >= 3
                                            for k, v in b.items())):
            raise SpecError(f"{where}.spec.boundary maps an exact column to {{source: a numeric re-derived column, width, cells (>= 3)}}")
    return spec


def spec_read(spec: dict) -> dict:
    """The stated read the census performs: {columns, where, chart_scoped, inputs}. One definition; the census fetcher consumes it."""
    return dict(spec["read"])


# ───────────────────────── the measurement ─────────────────────────

def _claims(spec: dict, method: dict, backend, read_timeout_s=None) -> str:
    return (f"D3 re-derives by method {spec['method']} ({method['independence']}): a different code path, not necessarily different data"
            + (f"; the reference backend read as {backend.get('name')!r}" if isinstance(backend, dict) else "")
            + "; the tolerance is the declared one with its stated basis; the declared conventions "
            + ", ".join(f"{k}={v['value']}" for k, v in spec["conventions"].items())
            + " are part of the claim and are not verified here; completeness is only the declared expected_rows"
            + (f"; the table was read in ONE read-only pass under a {read_timeout_s} second client timeout, nothing truncated (a timeout is an error, never a partial verdict)" if read_timeout_s else ""))


def d3_measure(spec: dict, rows, table, method=None, inputs=None, asset_rows=None, read_timeout_s=None) -> dict:
    """The Carr.D3 measurement record for a declared D3 asset. `rows` the asset's table rows (list of dicts) or None when they could not be read; `inputs` the optional
    inputs read (list of dicts) or None; `asset_rows` the asset's own live row count (count_sql) or None: when it exceeds the rows the declared read covers, the verdict caps PARTIAL; `table` the asset's registry target table; `method` overrides the registry lookup (tests only). The caller has validated `spec`.
    Returns {v, measured, d3: {...}}."""
    m = method if method is not None else load_methods().get(spec["method"])
    if m is None:
        return dict(v=NO_DET, measured=f"NO_DETECTOR: method {spec['method']!r} is not in the closed registry METHODS", d3=dict(method=spec["method"]))
    base = dict(method=spec["method"], independence=m["independence"], rule=m["rule_text"], reads=list(m["reads"]), declared_columns={c: dict(d) for c, d in spec["columns"].items()},
                conventions={k: dict(v) for k, v in spec["conventions"].items()}, expected_rows=spec["expected_rows"], uncovered=[dict(u) for u in spec["uncovered"]],
                sampled=("sample" in spec), method_version=m.get("version"))

    def out(v, text, **ev):
        return dict(v=v, measured=text, d3=dict(base, **ev))

    if table != spec["table"] or table not in m["tables"]:
        return out(NO_DET, f"NO_DETECTOR: the spec names table {spec['table']!r} (method allows {list(m['tables'])}) but the asset's registry target table is {table!r}: D3 does not guess")
    if m["independence"] not in INDEPENDENCE:
        return out(NO_DET, f"NO_DETECTOR: unknown independence class {m['independence']!r}")
    if m["independence"] == "same_code":
        return out(NO_DET, "NO_DETECTOR: a same-code re-derivation never passes (N-101): the second route shares the writer's code, so it could not have disagreed")
    if not isinstance(rows, list):
        return out(NO_DET, "NO_DETECTOR: the asset's table rows could not be read")
    backend = None
    if m.get("backend_probe") is not None:
        try:
            backend = m["backend_probe"]()
        except Exception as exc:   # an absent or broken reference engine is not evidence; the failure type is the reason
            return out(NO_DET, f"NO_DETECTOR: the reference engine is unavailable ({type(exc).__name__}): a leg that cannot run is not evidence")
        base["backend"] = backend
        if not (isinstance(backend, dict) and backend.get("name") in spec["backend"]["allowed"]):
            return out(NO_DET, f"NO_DETECTOR: the reference backend reads {backend!r}, not one of the declared allowed {spec['backend']['allowed']}: a leg that may have fallen back silently is not evidence")
    try:
        logical = m["logical_rows"](rows, inputs)
    except (KeyError, TypeError, ValueError) as exc:
        return out(NO_DET, f"NO_DETECTOR: the rows could not be shaped into logical rows ({type(exc).__name__}: {exc})")
    if not logical:
        return out(NO_DET, f"NO_DETECTOR: table {table} yields no logical row to re-derive")
    keyf = lambda r: "|".join(str(r.get(k)) for k in spec["key"])
    keys = [keyf(r) for r in logical]
    dup = sorted(k for k, n in collections.Counter(keys).items() if n > 1)
    ev = dict(rows_read=len(rows), rows_total=len(logical), population_sha256=rows_digest([[keyf(r), {c: r.get(c) for c in spec["columns"]}] for r in sorted(logical, key=keyf)]), backend=backend)
    strata_col = spec.get("strata")
    by = {}
    for r in logical:
        by.setdefault(r.get(strata_col) if strata_col else None, []).append(r)
    ev["strata"] = {str(k): len(v) for k, v in by.items()} if strata_col else None
    chosen = []
    for s, rs in by.items():
        if "sample" in spec and len(rs) > spec["sample"]["per_stratum"]:
            rs = sorted(rs, key=lambda r: rank_key(spec["sample"]["seed"], keyf(r)))[:spec["sample"]["per_stratum"]]
        chosen += rs
    full = len(chosen) == len(logical)
    try:
        ctx = m["context"](rows, inputs, spec)
    except (KeyError, TypeError, ValueError) as exc:
        return out(NO_DET, f"NO_DETECTOR: the re-derivation inputs could not be read ({type(exc).__name__}: {exc})", **ev)
    mism, agree, resid, tolerated = [], 0, {c: 0.0 for c in spec["columns"]}, []
    for r in chosen:
        try:
            ref = m["ref"](r, ctx)
        except (KeyError, TypeError, ValueError) as exc:
            mism.append(dict(row=keyf(r), columns=[f"error:{type(exc).__name__}"]))
            continue
        bad = []
        for c, d in spec["columns"].items():
            ok, res = compare_value(d["kind"], r.get(c), ref.get(c), tol_for(d["tol"], r))
            if res is not None:
                resid[c] = max(resid[c], res)
            if not ok and c in spec.get("boundary", {}):
                b = spec["boundary"][c]
                lon = ref.get(b["source"])
                sv, rv = r.get(c), ref.get(c)
                adjacent = (isinstance(sv, int) and isinstance(rv, int) and not isinstance(sv, bool) and not isinstance(rv, bool)
                            and (sv - rv) % b["cells"] in (1, b["cells"] - 1))        # the stored cell is the NEIGHBOUR of the reference cell, never a distant one
                if adjacent and isinstance(lon, (int, float)) and not isinstance(lon, bool) and math.isfinite(lon):
                    edge = min(lon % b["width"], b["width"] - (lon % b["width"]))
                    if edge <= tol_for(spec["columns"][b["source"]]["tol"], r):
                        tolerated.append(dict(row=keyf(r), column=c, edge_distance=edge))
                        continue
            amb = ref.get("_ambiguous", {}).get(c) if isinstance(ref.get("_ambiguous"), dict) else None
            if not ok and isinstance(amb, dict) and r.get(c) in amb.get("neighbours", ()):
                tolerated.append(dict(row=keyf(r), column=c, ambiguity=amb["note"]))      # the stored value is the declared NEIGHBOUR of the re-derived one at a classification boundary the method reviewed
                continue
            if not ok:
                bad.append(c)
        if bad or keyf(r) in dup:
            mism.append(dict(row=keyf(r), columns=bad + (["duplicate"] if keyf(r) in dup else [])))
        else:
            agree += 1
    comp = None
    if spec["expected_rows"] == "method":
        try:
            comp_ok, comp = m["completeness"](logical, ctx, spec)
        except (KeyError, TypeError, ValueError) as exc:
            return out(NO_DET, f"NO_DETECTOR: the independent completeness check could not run ({type(exc).__name__}: {exc})", **ev)
        count_ok = bool(comp_ok)
    else:
        count_ok = len(logical) == spec["expected_rows"]
    ev["read_timeout_s"] = read_timeout_s
    ev.update(completeness_problems=comp, asset_rows=asset_rows, rows_checked=len(chosen), rows_agree=agree, n_mismatch=len(mism), mismatches=mism[:MAX_NAMED], max_residual=resid, boundary_tolerated=tolerated[:MAX_NAMED],
              full_population=full, row_count_ok=count_ok, duplicate_keys=dup[:MAX_NAMED], claims=_claims(spec, m, backend, read_timeout_s))
    if mism and agree == 0:
        return out(FAIL, f"D3 FAIL: none of the {len(chosen)} checked row(s) of {table} agree with the {spec['method']} re-derivation. {ev['claims']}", **ev)
    if mism:
        return out(PARTIAL, f"D3 PARTIAL: {len(mism)} of {len(chosen)} checked row(s) disagree beyond the declared tolerance: "
                            + ", ".join(f"{x['row']} ({'/'.join(x['columns'])})" for x in mism[:5]) + f". {ev['claims']}", **ev)
    covers_asset = isinstance(asset_rows, int) and not isinstance(asset_rows, bool) and asset_rows <= len(rows)      # N-156 review MED-2: an unreadable live count is not coverage
    if m["independence"] == "independent_formula" and full and count_ok and not spec["uncovered"] and covers_asset:
        return out(PASS_V, f"D3 PASS: every one of the {len(chosen)} logical row(s) of {table} (the {spec['expected_rows']} declared) re-derived by {spec['method']} within the declared "
                           f"tolerance. {ev['claims']}", **ev)
    why = [w for w, c in (("the method is a relation, not an independent formula", m["independence"] != "independent_formula"),
                          ("only a sample was re-derived", not full),
                          ((f"the independent completeness check names: {'; '.join(comp[:3])}" if comp else f"the table yields {len(logical)} logical row(s) but {spec['expected_rows']} are declared"), not count_ok),
                          ("declared uncovered column(s) " + ", ".join(u["column"] for u in spec["uncovered"]), bool(spec["uncovered"])),
                          ((f"the declared read covers {len(rows)} of the asset's {asset_rows} row(s): the rest are outside every re-derivation" if isinstance(asset_rows, int) and not isinstance(asset_rows, bool)
                            else "the asset's live row count is unreadable, so nothing shows the declared read covers every row it holds"), not covers_asset)) if c]
    return out(PARTIAL, f"D3 PARTIAL: {len(chosen)} checked row(s) agree but the cell cannot read PASS: {'; '.join(why)}. {ev['claims']}", **ev)


def d3_evidence_problem(meas) -> str:
    """"" when a Carr.D3 measurement carries the evidence a D3 PASS/PARTIAL needs, else what is missing (a bare {v: PASS} is not a D3 result). Recomputes nothing from the
    database: it catches a record that dropped its own evidence or claims a PASS its own fields contradict (not a forgery barrier)."""
    ev = meas.get("d3") if isinstance(meas, dict) else None
    if not isinstance(ev, dict):
        return "no `d3` evidence"
    if not (isinstance(ev.get("population_sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", ev["population_sha256"])):
        return "no population_sha256 (the rows were not read)"
    if ev.get("independence") not in INDEPENDENCE or ev.get("independence") == "same_code":
        return f"independence {ev.get('independence')!r} cannot support a D3 verdict"
    if not (isinstance(ev.get("rows_total"), int) and ev["rows_total"] >= 1 and isinstance(ev.get("rows_checked"), int) and ev["rows_checked"] >= 1):
        return "no rows were re-derived"
    if not (isinstance(ev.get("conventions"), dict) and ev["conventions"]):
        return "the record states no declared convention"
    if meas.get("v") == PASS_V:
        if ev.get("independence") != "independent_formula":
            return "PASS but the method is not an independent formula"
        if not (ev.get("full_population") is True and ev.get("rows_checked") == ev.get("rows_total") and ev.get("sampled") is False):
            return "PASS but not every logical row was re-derived"
        if not (ev.get("n_mismatch") == 0 and ev.get("rows_agree") == ev.get("rows_checked") and ev.get("row_count_ok") is True):
            return "PASS but not every row agrees under the declared row count"
        if ev.get("uncovered"):
            return "PASS but the spec declares uncovered column(s)"
        ar = ev.get("asset_rows")
        if not (isinstance(ar, int) and not isinstance(ar, bool)):
            return "PASS but the asset's live row count was not read, so coverage of every row the asset holds is not shown"
        if ar > ev.get("rows_read", 0):
            return "PASS but the declared read covers fewer rows than the asset holds"
        if "backend" in ev and ev["backend"] is not None and not (isinstance(ev["backend"], dict) and ev["backend"].get("name")):
            return "PASS but the reference backend is not named"
    return ""


# ───────────────────────── the method registry (closed) ─────────────────────────
METHOD_HOOKS = ("tables", "assets", "completeness", "independence", "max_tol", "required_conventions", "reads", "logical_rows", "context", "ref", "rule_text", "version", "inputs_table")
METHODS: dict = {}


def register_method(mid: str, **hooks) -> None:
    """Register a reviewed method (called at import by carriage_d3_methods.py; a method that lacks a hook is refused at registration, never a KeyError at measurement)."""
    missing = sorted(h for h in METHOD_HOOKS if h not in hooks)
    if missing or mid in METHODS or hooks.get("independence") not in INDEPENDENCE:
        raise SpecError(f"register_method({mid!r}): missing hook(s) {missing}, duplicate id, or unknown independence {hooks.get('independence')!r}")
    METHODS[mid] = dict(hooks)


def load_methods():
    """Import the reviewed methods once: carriage_d3_methods.py defines `register_all(d3)` and registers each method into THIS module's METHODS (it imports no sibling).
    Returns METHODS."""
    import importlib.util
    import pathlib
    import sys
    if not METHODS:
        p = pathlib.Path(__file__).resolve().parent / "carriage_d3_methods.py"
        spec = importlib.util.spec_from_file_location("carriage_d3_methods_loaded", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.register_all(sys.modules[__name__])
    return METHODS
