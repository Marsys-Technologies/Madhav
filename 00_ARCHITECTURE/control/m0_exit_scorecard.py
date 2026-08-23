#!/usr/bin/env python3
"""m0_exit_scorecard.py — NIRMĀṆA M0-T17.

Measures the twelve M0 exit criteria (v3.0 Phase 0 exit list, adopted verbatim by
v4.0 §14.1's M0 acceptance column, plus v4.1's two additions) against the LIVE
system, and regenerates:

    00_ARCHITECTURE/control/m0_exit_scorecard.json   (machine-readable)
    00_ARCHITECTURE/control/M0_EXIT_SCORECARD_v1_0.md (human-readable)

Design rules this script obeys, and why:

  * READ-ONLY. `default_transaction_read_only` is set on the session and only
    SELECTs are issued. No DDL, no DML, ever.
  * NEVER imports platform/scripts/migrate.ts or asset_registry_seed.ts
    (DECISIONS D-9, D-13). The seed .ts is read as TEXT and regex-parsed.
  * NEVER prints, echoes or persists DATABASE_URL (charter P4). The url is read
    from platform/.env.local exactly as measure_assets.py does and is held in a
    local only.
  * INHERITS NO NUMBER. Every figure below is re-derived by this script. Where a
    sibling M0 artifact states a figure for the same quantity, that figure is
    carried in the record as `sibling_value` and, if it differs, the record is
    marked `disagreement: true` and BOTH are reported. Two angles disagreeing is
    a failure, not a thing to average.
  * A CRITERION WITH NO DETECTOR IS NOT SATISFIED. Per CLAUDE.md §N.8 and charter
    H4, this script emits NOT-MEASURABLE (never PASS) for any criterion whose
    detector cannot produce a non-zero answer, and states what is missing.

Statuses emitted:
    PASS            a detector ran and returned zero.
    FAIL            a detector ran and returned non-zero.
    NOT-MEASURABLE  no detector exists that could return non-zero. Not a pass.
    BLOCKED         a detector exists but cannot run yet; `blocked_by` says why.

Usage:  python3 00_ARCHITECTURE/control/m0_exit_scorecard.py
"""
from __future__ import annotations

import ast
import datetime
import json
import pathlib
import re
import subprocess
import sys

import psycopg
import psycopg.rows

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTROL = ROOT / "00_ARCHITECTURE" / "control"
OUT_JSON = CONTROL / "m0_exit_scorecard.json"
OUT_MD = CONTROL / "M0_EXIT_SCORECARD_v1_0.md"

PASS, FAIL, NM, BLOCKED = "PASS", "FAIL", "NOT-MEASURABLE", "BLOCKED"

notes: list[str] = []


def _db_url() -> str:
    """Read DATABASE_URL the way measure_assets.py does. Never logged (P4)."""
    for line in (ROOT / "platform/.env.local").read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            m = re.match(r"^\s*DATABASE_URL\s*=\s*(.+)$", line)
            if m:
                return m.group(1).strip().strip("\"'")
    raise SystemExit("DATABASE_URL not found in platform/.env.local")


def _rel(p: pathlib.Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


# ─────────────────────────────────────────────────────────────────────────────
# Source scans — re-derived here, not imported from census.py
# ─────────────────────────────────────────────────────────────────────────────
DECORATOR_ROOTS = [ROOT / "platform" / "python-sidecar"]
SEED_TS = ROOT / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"
SEED_ID_RE = re.compile(r"^\s*asset_id:\s*['\"]([A-Za-z0-9_.]+)['\"]")
ASSET_SHAPE = re.compile(r"^(bg|ga|bo|ka|ph|mi)_[a-z0-9_]+$")


def _is_test_path(p: pathlib.Path) -> bool:
    s = str(p).replace("\\", "/")
    return ("/tests/" in s or "/__tests__/" in s or "/test/" in s
            or p.name.startswith("test_") or p.name.endswith("_test.py"))


def scan_decorators() -> dict:
    """AST scan for @register('<id>') applied to a class/function.

    Returns {'production': {id: [sites]}, 'test_only': {...}, 'unresolved': [...],
             'classes': {qualified_class: {...}}}  — the last feeds the C-23
    has_substeps derivation below.
    """
    production: dict[str, list] = {}
    test_only: dict[str, list] = {}
    unresolved: list[str] = []
    classes: dict[str, dict] = {}
    parse_errors: list[str] = []
    files = 0

    for base in DECORATOR_ROOTS:
        if not base.exists():
            parse_errors.append(f"decorator root missing: {_rel(base)}")
            continue
        for p in sorted(base.rglob("*.py")):
            if any(part in {"node_modules", ".venv", "venv", "__pycache__", "build", "dist"}
                   for part in p.parts):
                continue
            files += 1
            try:
                tree = ast.parse(p.read_text(errors="replace"), filename=str(p))
            except (SyntaxError, OSError) as e:
                parse_errors.append(f"{_rel(p)}: {e}")
                continue
            consts: dict[str, str] = {}
            for node in tree.body:
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                        and isinstance(node.value.value, str):
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            consts[tgt.id] = node.value.value
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                        and isinstance(node.value, ast.Constant) \
                        and isinstance(node.value.value, str):
                    consts[node.target.id] = node.value.value
            is_test = _is_test_path(p)

            # class table for the substep derivation
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    key = f"{_rel(p)}::{node.name}"
                    bases = []
                    for b in node.bases:
                        if isinstance(b, ast.Name):
                            bases.append(b.id)
                        elif isinstance(b, ast.Attribute):
                            bases.append(b.attr)
                    methods = {n.name for n in node.body
                               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                    attr_has_substeps = None
                    for n in node.body:
                        tgts = ([t for t in n.targets] if isinstance(n, ast.Assign)
                                else ([n.target] if isinstance(n, ast.AnnAssign) else []))
                        for t in tgts:
                            if isinstance(t, ast.Name) and t.id == "has_substeps" \
                                    and isinstance(n.value, ast.Constant):
                                attr_has_substeps = bool(n.value.value)
                    classes[key] = {"name": node.name, "bases": bases,
                                    "defines_plan_substeps": "plan_substeps" in methods,
                                    "class_attr_has_substeps": attr_has_substeps,
                                    "file": _rel(p), "is_test": is_test, "asset_ids": []}

            for node in ast.walk(tree):
                if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for dec in node.decorator_list:
                    if not isinstance(dec, ast.Call):
                        continue
                    fn = dec.func
                    nm = fn.id if isinstance(fn, ast.Name) else (
                        fn.attr if isinstance(fn, ast.Attribute) else None)
                    if nm != "register" or not dec.args:
                        continue
                    arg = dec.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        aid = arg.value
                    elif isinstance(arg, ast.Name) and arg.id in consts:
                        aid = consts[arg.id]
                    else:
                        unresolved.append(f"{_rel(p)}:{dec.lineno}")
                        continue
                    site = {"file": _rel(p), "line": dec.lineno,
                            "symbol": getattr(node, "name", "?")}
                    (test_only if is_test else production).setdefault(aid, []).append(site)
                    if isinstance(node, ast.ClassDef):
                        key = f"{_rel(p)}::{node.name}"
                        if key in classes:
                            classes[key]["asset_ids"].append(aid)
    return {"production": production, "test_only": test_only,
            "unresolved": unresolved, "classes": classes,
            "parse_errors": parse_errors, "files_scanned": files}


def scan_seed() -> dict:
    """Regex-parse asset_registry_seed.ts as TEXT. Never imported (D-13)."""
    if not SEED_TS.exists():
        return {"ok": False, "ids": [], "reason": f"{_rel(SEED_TS)} not found"}
    ids = []
    for line in SEED_TS.read_text(errors="replace").splitlines():
        m = SEED_ID_RE.match(line)
        if m:
            ids.append(m.group(1))
    if not ids:
        return {"ok": False, "ids": [], "reason": "parsed but yielded 0 asset_id entries"}
    return {"ok": True, "ids": sorted(set(ids)), "raw_count": len(ids)}


def derive_has_substeps(classes: dict) -> dict[str, bool]:
    """asset_id -> writer-class truth for `has_substeps` (C-23).

    CRITICAL, and the first thing this detector got wrong: the FROZEN base class
    `WriterBase` (platform/python-sidecar/pipeline/orchestrator/writers/__init__.py)
    ITSELF defines a default `plan_substeps` returning one sub-step — the
    light-writer path. So "the class has a plan_substeps in its MRO" is true of
    EVERY writer and is not a detector at all; it is a constant wearing a
    detector's clothes (CLAUDE.md §N.8). The truth C-23 is about is whether the
    writer OVERRIDES it.

    Truth = the writer class, or an ancestor OTHER THAN the frozen base, defines
    `plan_substeps`; OR the class (or such an ancestor) sets `has_substeps = True`.

    Limit, stated not hidden: inheritance is resolved by class NAME across the
    scanned tree; imports are not followed, so a base defined outside
    platform/python-sidecar is invisible.
    """
    BASE_NAMES = {"WriterBase"}
    by_name: dict[str, list[dict]] = {}
    for rec in classes.values():
        by_name.setdefault(rec["name"], []).append(rec)

    def resolves(rec: dict, seen: set) -> bool:
        if rec["name"] not in BASE_NAMES:
            if rec["defines_plan_substeps"]:
                return True
            if rec.get("class_attr_has_substeps") is True:
                return True
        for b in rec["bases"]:
            if b in seen or b in BASE_NAMES:
                continue
            seen.add(b)
            for parent in by_name.get(b, []):
                if resolves(parent, seen):
                    return True
        return False

    out: dict[str, bool] = {}
    for rec in classes.values():
        if rec["is_test"]:
            continue
        for aid in rec["asset_ids"]:
            out[aid] = out.get(aid, False) or resolves(rec, set())
    return out


def scan_ci_guards() -> dict:
    """Is a catalogue-conformance CI guard merged AND blocking? (criterion 10/12)

    Detector: (a) does a guard script implementing the Asset Catalogue Contract
    exist on disk; (b) is it invoked from a .github/workflows job; (c) is that
    invocation blocking (no `continue-on-error: true`, not `|| true`).
    """
    wf_dir = ROOT / ".github" / "workflows"
    gov = ROOT / "platform" / "scripts" / "governance"
    ci = ROOT / "platform" / "scripts" / "ci"
    contract_markers = ("ASSET_CATALOGUE_CONTRACT", "catalogue_conformance",
                        "catalogue_contract", "asset_catalogue",
                        "three_way_diff", "three-way diff")
    # M0-T32: the original marker set was ("domain_coherence", "domain-coherence",
    # "shared asset may depend") and matched NOTHING — the shipped guard spells the
    # assertion "domain coherence: a shared asset depends only on shared assets"
    # (X-04, check_asset_catalogue_contract.py:1146). A marker set that cannot match
    # the artifact it is looking for is a detector that can only ever return absent,
    # i.e. the §N.8 defect this scorecard exists to catch, inside the scorecard. The
    # rule id is included because it is the one string that cannot drift from prose.
    domain_markers = ("domain_coherence", "domain-coherence", "domain coherence",
                      "shared asset may depend", "shared asset depends only on shared",
                      '"X-04"', "'X-04'")

    guard_scripts, domain_scripts = [], []
    for d in (gov, ci):
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file() or p.suffix not in (".py", ".ts", ".sh"):
                continue
            try:
                txt = p.read_text(errors="replace")
            except OSError:
                continue
            if any(m in txt for m in contract_markers):
                guard_scripts.append(_rel(p))
            if any(m in txt for m in domain_markers):
                domain_scripts.append(_rel(p))

    wf_hits, wf_domain_hits = [], []
    workflows = sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")) if wf_dir.exists() else []
    for p in workflows:
        txt = p.read_text(errors="replace")
        for g in guard_scripts:
            if pathlib.Path(g).name in txt:
                wf_hits.append({"workflow": _rel(p), "script": g})
        for g in domain_scripts:
            if pathlib.Path(g).name in txt:
                wf_domain_hits.append({"workflow": _rel(p), "script": g})
        if any(m in txt for m in contract_markers):
            wf_hits.append({"workflow": _rel(p), "script": "(inline marker)"})
        if any(m in txt for m in domain_markers):
            wf_domain_hits.append({"workflow": _rel(p), "script": "(inline marker)"})
    return {"guard_scripts": guard_scripts, "workflow_invocations": wf_hits,
            "domain_coherence_scripts": domain_scripts,
            "domain_coherence_workflow_invocations": wf_domain_hits,
            "workflows_scanned": [_rel(p) for p in workflows]}


# ─────────────────────────────────────────────────────────────────────────────
# M0-T27 additions — durability of a repair, and a criterion-10 detector that
# can actually return false on the word "blocking".
#
# WHY THESE EXIST. The first run of this generator (M0-T17) read 0 PASS. Several
# criteria have since moved, and two of the movements are not what they look like:
#
#   (a) A repair written directly to `asset_registry` is only durable if the
#       column it wrote is NOT in `asset_registry_seed.ts`'s
#       `ON CONFLICT (asset_id) DO UPDATE SET` list. Columns in that list are
#       overwritten from EXCLUDED on the next seed run, so a green that rests on
#       one of them is a green the next re-seed silently undoes. That is exactly
#       the class of signal this campaign exists to remove, so the scorecard now
#       measures it instead of assuming it.
#   (b) Criterion 10's own detector asserted "merged AND blocking" while only
#       ever checking "a guard file exists" AND "some workflow names it". The
#       word `blocking` had NO code path behind it — a constant that could not
#       return false, i.e. the §N.8 defect this scorecard was built to catch,
#       inside the scorecard. Fixed below: blocking is now parsed, and `merged`
#       now means merged to the default branch, not present in the worktree.
#
# Both are read-only, and neither imports the seed or migrate.ts (D-9 / D-13).
# ─────────────────────────────────────────────────────────────────────────────
# M0-T27 · falsifiability probes.
#
# A rule that returns zero is only evidence if the query COULD have returned
# non-zero against this database. Two of this campaign's detectors have already
# turned out to be constants that could not fail, so a zero is no longer taken on
# trust: for every rule that reads PASS, the shipped SQL is re-run with ONE
# deliberate mutation that must make it fire. If the mutant still returns zero,
# the zero is not evidence of conformance and is reported as such.
#
# The mutations are read-only text substitutions on the rule's own SQL. Nothing
# is written; the mutant query is never used for a verdict.
MUTATIONS: dict[str, tuple[list[tuple[str, str]], str]] = {
    "C-05": ([("count_sql IS NULL", "count_sql IS NOT NULL")],
             "invert the NULL test: every data/artifact row that HAS a count_sql must fire"),
    "C-09": ([("a.superseded_by IS NOT NULL", "a.superseded_by IS NULL")],
             "invert the NOT NULL test: rows with no supersession must fire, since "
             "NOT EXISTS(... = NULL) is true for all of them"),
    "C-10": ([("data_disposition IS NOT NULL", "data_disposition IS NULL")],
             "invert the NULL test: non-RETIRED rows without a disposition must fire"),
    "C-14": ([("NOT IN (('data','data')", "IN (('data','data')")],
             "invert the membership test: every LEGAL (kind,type) pair must fire"),
    "C-18": ([("WHEN 'global' THEN 'shared'", "WHEN 'global' THEN 'chart'"),
              ("WHEN 'per_chart' THEN 'chart'", "WHEN 'per_chart' THEN 'shared'")],
             "swap the scope→domain mapping: with the expectation inverted every row "
             "must fire"),
    "C-19": ([("WHEN 'brahmagyan' THEN 'R0'", "WHEN 'brahmagyan' THEN 'R5'")],
             "mis-map one layer: every brahmagyan row must fire"),
    "C-12": ([("WHERE NOT EXISTS (SELECT 1 FROM asset_registry b WHERE b.asset_id=d)",
               "WHERE EXISTS (SELECT 1 FROM asset_registry b WHERE b.asset_id=d)")],
             "invert the existence test: every edge that DOES resolve must fire"),
    "C-13a": ([("WHERE asset_id = ANY(depends_on)", "WHERE NOT (asset_id = ANY(depends_on))")],
              "invert the self-edge test: every row without a self-edge must fire"),
    "C-16": ([("service_health IS NOT NULL", "service_health IS NULL")],
             "invert the NULL test: non-service rows with no service_health must fire"),
    "C-24": ([("NOT EXISTS (SELECT 1 FROM information_schema.tables i "
               "WHERE i.table_schema='public' AND i.table_name=t)",
               "EXISTS (SELECT 1 FROM information_schema.tables i "
               "WHERE i.table_schema='public' AND i.table_name=t)")],
             "invert the first arm's existence test: every clear_tables entry that DOES "
             "name a real table must fire"),
}


SEED_LITERAL_FIELDS = {
    # field -> default the seed applies when the key is absent from an entry.
    # Verified against asset_registry_seed.ts's own
    #   `const assetType  = asset.asset_type ?? 'data'`
    #   `const assetKind  = asset.asset_kind ?? 'data'`
    "asset_kind": "data",
    "asset_type": "data",
    "scope": None,      # required per entry; no default to model
    "layer": None,
}


def scan_seed_upsert() -> dict:
    """Which asset_registry columns does the seed WRITE on a re-run?

    Read as TEXT (never imported — D-9/D-13). Returns the INSERT column list and
    the `ON CONFLICT ... DO UPDATE SET` column list. A column in `do_update` is
    reverted to the seed's value on the next seed run; a column absent from
    `insert_columns` is left NULL/default on any row the seed newly inserts.
    """
    out = {"ok": False, "reason": None, "insert_columns": [], "do_update_columns": [],
           "path": _rel(SEED_TS)}
    try:
        txt = SEED_TS.read_text(errors="replace")
    except OSError as e:
        out["reason"] = str(e)
        return out
    m = re.search(r"INSERT\s+INTO\s+asset_registry\s*\((.*?)\)\s*VALUES", txt,
                  re.S | re.I)
    if not m:
        out["reason"] = "no `INSERT INTO asset_registry ( ... ) VALUES` block found"
        return out
    out["insert_columns"] = sorted({c.strip() for c in m.group(1).split(",") if c.strip()})
    u = re.search(r"ON\s+CONFLICT\s*\(\s*asset_id\s*\)\s*DO\s+UPDATE\s+SET(.*?)`", txt,
                  re.S | re.I)
    if not u:
        out["reason"] = "no `ON CONFLICT (asset_id) DO UPDATE SET` block found"
        return out
    body = u.group(1)
    body = re.sub(r"--[^\n]*", "", body)          # strip SQL line comments
    cols = re.findall(r"(?m)^\s*([a-z_][a-z0-9_]*)\s*=", body)
    out["do_update_columns"] = sorted(set(cols))
    out["ok"] = bool(out["insert_columns"] and out["do_update_columns"])
    if not out["ok"]:
        out["reason"] = "parsed, but one of the two column lists came back empty"
    return out


def scan_seed_literals() -> dict:
    """Per-asset literal values the seed would write for the fields in
    SEED_LITERAL_FIELDS, including the seed's own `?? 'data'` defaults.

    Parsed from the text of the seed's `ASSETS` entries — same discipline as
    scan_seed(): each entry is delimited by its own `asset_id:` line.
    """
    out: dict[str, dict] = {}
    try:
        txt = SEED_TS.read_text(errors="replace")
    except OSError:
        return out
    idxs = [(m.start(), m.group(1))
            for m in re.finditer(r"^\s*asset_id:\s*['\"]([A-Za-z0-9_.]+)['\"]", txt, re.M)]
    for i, (pos, aid) in enumerate(idxs):
        end = idxs[i + 1][0] if i + 1 < len(idxs) else len(txt)
        blk = txt[pos:end]
        rowvals = {}
        for field, default in SEED_LITERAL_FIELDS.items():
            hit = re.search(rf"(?<![A-Za-z_]){field}:\s*['\"]([A-Za-z0-9_]+)['\"]", blk)
            rowvals[field] = hit.group(1) if hit else default
            rowvals[field + "_declared"] = bool(hit)
        out[aid] = rowvals
    return out


def columns_referenced(sql: str | None, cols: set[str]) -> list[str]:
    """asset_registry columns a detector SQL names. Word-boundary match against
    the LIVE column set, so a column that does not exist cannot be 'referenced'."""
    if not sql:
        return []
    toks = set(re.findall(r"[a-z_][a-z0-9_]*", sql.lower()))
    return sorted(toks & {c.lower() for c in cols})


NONBLOCKING_MARKERS = ("continue-on-error", "|| true", "|| exit 0", "|| :")


def analyse_ci_blocking(ci: dict) -> dict:
    """Is each guard invocation actually BLOCKING?

    A job (or the step running the guard) carrying `continue-on-error: true`, or
    a run line ending `|| true`, does not gate anything. Parsed with PyYAML where
    available and by line-scan otherwise; when neither can decide, the answer is
    `null` and the criterion does NOT pass on it.
    """
    res = {"parser": None, "invocations": [], "any_blocking": None,
           "all_blocking": None, "undecidable": []}
    try:
        import yaml  # noqa: PLC0415  — optional; absence is reported, not assumed away
        res["parser"] = "pyyaml"
    except Exception:
        yaml = None
        res["parser"] = "line-scan (PyYAML unavailable)"

    wanted = {pathlib.Path(g).name for g in ci["guard_scripts"]}
    for wf_rel in {inv["workflow"] for inv in ci["workflow_invocations"]}:
        p = ROOT / wf_rel
        try:
            txt = p.read_text(errors="replace")
        except OSError as e:
            res["undecidable"].append({"workflow": wf_rel, "why": str(e)})
            continue
        if yaml is not None:
            try:
                doc = yaml.safe_load(txt) or {}
            except Exception as e:
                doc = None
                res["undecidable"].append({"workflow": wf_rel,
                                           "why": f"YAML parse error: {str(e)[:120]}"})
            if isinstance(doc, dict):
                for job_id, job in (doc.get("jobs") or {}).items():
                    if not isinstance(job, dict):
                        continue
                    job_coe = bool(job.get("continue-on-error") is True)
                    for step in (job.get("steps") or []):
                        if not isinstance(step, dict):
                            continue
                        run = str(step.get("run") or "")
                        hit = [g for g in wanted if g in run]
                        if not hit:
                            continue
                        step_coe = bool(step.get("continue-on-error") is True)
                        swallow = any(mk in run for mk in ("|| true", "|| exit 0", "|| :"))
                        res["invocations"].append({
                            "workflow": wf_rel, "job": job_id,
                            "step": step.get("name") or run[:60],
                            "scripts": sorted(hit),
                            "job_continue_on_error": job_coe,
                            "step_continue_on_error": step_coe,
                            "run_line_swallows_exit_code": swallow,
                            "blocking": not (job_coe or step_coe or swallow)})
                continue
        # line-scan fallback
        nonblocking = any(f"{mk}: true" in txt or mk in txt for mk in ("continue-on-error",))
        res["invocations"].append({
            "workflow": wf_rel, "job": None, "step": None,
            "scripts": sorted(g for g in wanted if g in txt),
            "job_continue_on_error": None, "step_continue_on_error": None,
            "run_line_swallows_exit_code": None,
            "blocking": (None if nonblocking else None),
            "note": "line-scan could not attribute continue-on-error to a job/step; "
                    "answer left null rather than guessed"})
    decided = [i["blocking"] for i in res["invocations"] if i["blocking"] is not None]
    res["any_blocking"] = (any(decided) if decided else None)
    res["all_blocking"] = (all(decided) if decided else None)
    return res


def default_branch_presence(paths: list[str]) -> dict:
    """Is the guard/workflow actually MERGED — i.e. present on the default branch?

    `git ls-tree origin/main` is the detector. Present in the worktree on a
    campaign branch is not merged, and criterion 10 says merged.
    """
    out = {"ref": "origin/main", "ok": False, "present": {}, "reason": None}
    try:
        r = subprocess.run(["git", "ls-tree", "-r", "--name-only", "origin/main"],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            out["reason"] = (r.stderr or "git ls-tree failed").splitlines()[0][:160]
            return out
        tree = set(r.stdout.splitlines())
        out["ok"] = True
        out["present"] = {p: (p in tree) for p in paths}
    except Exception as e:
        out["reason"] = str(e).splitlines()[0][:160]
    return out


def github_run_evidence(workflow_files: list[str]) -> dict:
    """Has the workflow ever actually RUN on GitHub? Best-effort via `gh`.

    If `gh` is missing or unauthenticated the answer is null — never assumed
    green, never assumed red. The criterion's verdict does not depend on this
    field; it is corroborating evidence for the reader.
    """
    out = {"available": False, "reason": None, "workflows": {}}
    try:
        probe = subprocess.run(["gh", "auth", "status"], cwd=ROOT,
                               capture_output=True, text=True, timeout=60)
        if probe.returncode != 0:
            out["reason"] = "gh present but not authenticated"
            return out
    except Exception as e:
        out["reason"] = f"gh unavailable: {str(e).splitlines()[0][:120]}"
        return out
    out["available"] = True
    for wf in workflow_files:
        name = pathlib.Path(wf).name
        entry = {"registered_on_default_branch": None, "run_count": None, "detail": None}
        try:
            r = subprocess.run(["gh", "run", "list", "--workflow", name, "--limit", "1"],
                               cwd=ROOT, capture_output=True, text=True, timeout=120)
            combined = (r.stdout or "") + (r.stderr or "")
            if "not found on the default branch" in combined:
                entry["registered_on_default_branch"] = False
                entry["run_count"] = 0
                entry["detail"] = combined.strip().splitlines()[0][:200]
            elif r.returncode == 0:
                entry["registered_on_default_branch"] = True
                entry["run_count"] = len([l for l in r.stdout.splitlines() if l.strip()])
                entry["detail"] = "gh run list returned rows" if entry["run_count"] else \
                    "gh run list returned no rows"
            else:
                entry["detail"] = combined.strip().splitlines()[0][:200] if combined else None
        except Exception as e:
            entry["detail"] = str(e).splitlines()[0][:160]
        out["workflows"][wf] = entry
    return out


def zero_consumer_state() -> dict:
    """Criterion 9's detector: packets asserted, minus packets with a recorded
    ADHIKĀRIN disposition in DECISIONS.jsonl."""
    src = CONTROL / "zero_consumer_evidence.json"
    if not src.exists():
        return {"ok": False, "reason": f"{_rel(src)} missing"}
    data = json.loads(src.read_text())
    if isinstance(data, dict):
        for key in ("packets", "assets", "findings"):
            if key in data and isinstance(data[key], (list, dict)):
                data = data[key]
                break
    if isinstance(data, dict):
        asset_ids = sorted(k for k in data if not k.startswith("_"))
    else:
        asset_ids = sorted({r.get("asset_id") for r in data if isinstance(r, dict)} - {None})

    dec = ROOT / "00_ARCHITECTURE" / "autonomy" / "state" / "DECISIONS.jsonl"
    disposed = {}
    if dec.exists():
        for line in dec.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            subj = str(d.get("subject", ""))
            for aid in asset_ids:
                if d.get("power") == "G1" and aid in subj:
                    disposed.setdefault(aid, []).append(d.get("id"))
    return {"ok": True, "asset_ids": asset_ids, "n_packets": len(asset_ids),
            "disposed": disposed, "n_unresolved": len(asset_ids) - len(disposed)}


# ─────────────────────────────────────────────────────────────────────────────
# Contract rules (§8 of ASSET_CATALOGUE_CONTRACT_v1_0.md), re-transcribed
# ─────────────────────────────────────────────────────────────────────────────
LAYER_PREFIX = ("CASE layer WHEN 'brahmagyan' THEN 'bg_' WHEN 'ganita' THEN 'ga_' "
                "WHEN 'bodha' THEN 'bo_' WHEN 'kala' THEN 'ka_' "
                "WHEN 'phala' THEN 'ph_' WHEN 'mimamsa' THEN 'mi_' END")
LAYER_IDX = ("CASE layer WHEN 'brahmagyan' THEN 'L0' WHEN 'ganita' THEN 'L1' "
             "WHEN 'bodha' THEN 'L2' WHEN 'kala' THEN 'L3' "
             "WHEN 'phala' THEN 'L4' WHEN 'mimamsa' THEN 'L5' END")
LAYER_NAME = ("CASE layer WHEN 'brahmagyan' THEN 'Brahmagyan' WHEN 'ganita' THEN 'Gaṇita' "
              "WHEN 'bodha' THEN 'Bodha' WHEN 'kala' THEN 'Kāla' "
              "WHEN 'phala' THEN 'Phala' WHEN 'mimamsa' THEN 'Mīmāṃsā' END")
LAYER_RUNG = ("CASE layer WHEN 'brahmagyan' THEN 'R0' WHEN 'ganita' THEN 'R1' "
              "WHEN 'bodha' THEN 'R2' WHEN 'kala' THEN 'R3' "
              "WHEN 'phala' THEN 'R4' WHEN 'mimamsa' THEN 'R5' END")

RULES = [
    ("C-01", "asset_id prefix matches layer", "BLOCKING", [], f"""
        SELECT asset_id, layer FROM asset_registry
        WHERE asset_kind <> 'source'
          AND left(asset_id,3) IS DISTINCT FROM ({LAYER_PREFIX}) ORDER BY asset_id"""),
    ("C-02", "layer_index is ^L[0-5]$ and agrees with layer", "BLOCKING", [], f"""
        SELECT asset_id, layer, layer_index FROM asset_registry
        WHERE layer_index IS NULL OR layer_index !~ '^L[0-5]$'
           OR layer_index <> ({LAYER_IDX}) ORDER BY asset_id"""),
    ("C-03", "layer_name is the exact lexicon spelling", "BLOCKING", [], f"""
        SELECT asset_id, layer, layer_name FROM asset_registry
        WHERE layer_name IS DISTINCT FROM ({LAYER_NAME}) ORDER BY asset_id"""),
    ("C-04", "data/artifact => target_table exists", "BLOCKING", [], """
        SELECT a.asset_id, a.asset_kind, a.target_table FROM asset_registry a
        WHERE a.asset_kind IN ('data','artifact')
          AND (a.target_table IS NULL OR NOT EXISTS
               (SELECT 1 FROM information_schema.tables t
                WHERE t.table_schema='public' AND t.table_name=a.target_table))
        ORDER BY a.asset_id"""),
    ("C-05", "data/artifact => count_sql NOT NULL", "BLOCKING", [], """
        SELECT asset_id, asset_kind FROM asset_registry
        WHERE asset_kind IN ('data','artifact') AND count_sql IS NULL ORDER BY asset_id"""),
    ("C-06", "chart-domain count_sql is chart-scoped ($1)", "BLOCKING", [], """
        SELECT asset_id FROM asset_registry
        WHERE scope='per_chart' AND count_sql IS NOT NULL
          AND position('$1' in count_sql)=0 ORDER BY asset_id"""),
    ("C-07", "service rows carry no data-asset fields", "BLOCKING", [], """
        SELECT asset_id, target_table, target_floor FROM asset_registry
        WHERE asset_kind='service' AND (target_table IS NOT NULL OR count_sql IS NOT NULL
              OR target_floor IS NOT NULL OR clear_tables IS NOT NULL) ORDER BY asset_id"""),
    ("C-08", "RETIRED => data_disposition NOT NULL", "BLOCKING", ["data_disposition"], """
        SELECT asset_id FROM asset_registry
        WHERE catalog_status='RETIRED' AND data_disposition IS NULL ORDER BY asset_id"""),
    ("C-09", "superseded_by resolves", "BLOCKING", ["superseded_by"], """
        SELECT a.asset_id, a.superseded_by FROM asset_registry a
        WHERE a.superseded_by IS NOT NULL AND NOT EXISTS
          (SELECT 1 FROM asset_registry b WHERE b.asset_id=a.superseded_by) ORDER BY 1"""),
    ("C-10", "data_disposition only on RETIRED rows", "BLOCKING", ["data_disposition"], """
        SELECT asset_id FROM asset_registry
        WHERE data_disposition IS NOT NULL AND catalog_status<>'RETIRED' ORDER BY asset_id"""),
    ("C-11", "CURRENT depends only on CURRENT/source", "BLOCKING", [], """
        SELECT a.asset_id, d AS dep, b.catalog_status AS dep_status
        FROM asset_registry a CROSS JOIN LATERAL unnest(a.depends_on) AS d
        LEFT JOIN asset_registry b ON b.asset_id=d
        WHERE a.catalog_status='CURRENT'
          AND (b.asset_id IS NULL OR (b.catalog_status<>'CURRENT' AND b.asset_kind<>'source'))
        ORDER BY 1,2"""),
    ("C-12", "every depends_on element resolves", "BLOCKING", [], """
        SELECT a.asset_id, d AS dep FROM asset_registry a
        CROSS JOIN LATERAL unnest(a.depends_on) AS d
        WHERE NOT EXISTS (SELECT 1 FROM asset_registry b WHERE b.asset_id=d) ORDER BY 1,2"""),
    ("C-13a", "no self-edge", "BLOCKING", [], """
        SELECT asset_id FROM asset_registry WHERE asset_id = ANY(depends_on) ORDER BY 1"""),
    ("C-14", "asset_kind / asset_type coherent", "BLOCKING", [], """
        SELECT asset_id, asset_kind, asset_type FROM asset_registry
        WHERE (asset_kind, asset_type) NOT IN
          (('data','data'),('artifact','data'),('service','service'),('source','data'))
        ORDER BY asset_id"""),
    ("C-15", "service => health_probe AND provides_apis", "BLOCKING", [], """
        SELECT asset_id FROM asset_registry
        WHERE asset_kind='service' AND (health_probe IS NULL OR provides_apis IS NULL)
        ORDER BY asset_id"""),
    ("C-16", "non-service => service_health IS NULL", "BLOCKING", [], """
        SELECT asset_id, asset_kind, service_health FROM asset_registry
        WHERE asset_kind<>'service' AND service_health IS NOT NULL ORDER BY asset_id"""),
    ("C-17", "no graded service_health without a probe", "BLOCKING", [], """
        SELECT asset_id, service_health FROM asset_registry
        WHERE service_health IN ('healthy','degraded','unhealthy') AND health_probe IS NULL
        ORDER BY asset_id"""),
    ("C-18", "domain present and derived from scope", "BLOCKING", ["domain"], """
        SELECT asset_id, scope, domain FROM asset_registry
        WHERE domain IS DISTINCT FROM (CASE scope WHEN 'global' THEN 'shared'
                                                  WHEN 'per_chart' THEN 'chart' END)
        ORDER BY asset_id"""),
    ("C-19", "rung present and derived from layer", "BLOCKING", ["rung"], f"""
        SELECT asset_id, layer, rung FROM asset_registry
        WHERE asset_kind <> 'source' AND rung IS DISTINCT FROM ({LAYER_RUNG})
        ORDER BY asset_id"""),
    ("C-20", "CURRENT data/artifact carries a floor", "BLOCKING", [], """
        SELECT asset_id FROM asset_registry
        WHERE catalog_status='CURRENT' AND asset_kind IN ('data','artifact')
          AND target_floor IS NULL ORDER BY asset_id"""),
    ("C-21", "target_floor = 0 => volume_explanation", "BLOCKING", [], """
        SELECT asset_id FROM asset_registry
        WHERE target_floor = 0 AND (volume_explanation IS NULL
              OR btrim(volume_explanation)='') ORDER BY asset_id"""),
    ("C-24", "clear_tables exist and include target_table", "BLOCKING", [], """
        SELECT a.asset_id, t AS listed FROM asset_registry a
        CROSS JOIN LATERAL unnest(a.clear_tables) AS t
        WHERE a.clear_tables IS NOT NULL AND NOT EXISTS
          (SELECT 1 FROM information_schema.tables i
           WHERE i.table_schema='public' AND i.table_name=t)
        UNION ALL
        SELECT asset_id, target_table FROM asset_registry
        WHERE clear_tables IS NOT NULL AND NOT (target_table = ANY(clear_tables))"""),
    ("C-28", "estimated_seconds NOT NULL where a successful build exists", "BLOCKING", [], """
        SELECT r.asset_id FROM asset_registry r
        WHERE r.estimated_seconds IS NULL AND EXISTS
          (SELECT 1 FROM asset_throughput t
           WHERE t.asset_id=r.asset_id AND t.state='lit') ORDER BY 1"""),
]

# Rules the contract itself declares undetectable. NEVER reported as PASS.
UNDETECTABLE = [
    ("C-13b", "depends_on graph acyclic (recursive cycle detection)",
     "implemented below as a Python traversal, not by the contract's inline SQL"),
    ("C-22", "rung-frozen data assets carry integrity_check_sql",
     "vacuous today: 0 rungs frozen. Reported as vacuous, not as a pass."),
    ("C-23", "has_substeps equals the writer-class truth",
     "measured below by an AST derivation with a stated inheritance limit"),
    ("C-25", "co-written target_table => every co-writer declares its partition",
     "NO COLUMN EXISTS. Contract §4.9/§10.3. §N.8: null, never green."),
    ("C-26", "generation-bearing asset declares its authority pointer",
     "NO COLUMN EXISTS. Contract §4.11/§10.3. §N.8: null, never green."),
    ("C-27", "writer_timeout_seconds set from telemetry p95",
     "ADVISORY; not checkable until M2 telemetry. §N.8: null, never green."),
]


def main() -> int:
    started = datetime.datetime.now(datetime.timezone.utc)
    # The previous run's record, if any, so this run can report what MOVED since —
    # not only what moved inside this run. M0-T10 re-runs this generator at freeze
    # time; drift between runs is exactly what it needs to see.
    previous = None
    if OUT_JSON.exists():
        try:
            previous = json.loads(OUT_JSON.read_text())
        except json.JSONDecodeError:
            previous = None
    url = _db_url()
    rec: dict = {"_meta": {}, "criteria": {}, "contract_rules": {},
                 "undetectable_rules": {}, "source_scans": {}}

    try:
        git_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip()
        git_branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
                                    capture_output=True, text=True).stdout.strip()
    except Exception:
        git_sha = git_branch = "UNKNOWN"

    dec_scan = scan_decorators()
    seed = scan_seed()
    substeps = derive_has_substeps(dec_scan["classes"])
    ci = scan_ci_guards()
    zc = zero_consumer_state()

    rec["source_scans"] = {
        "decorators": {
            "roots": [_rel(r) for r in DECORATOR_ROOTS],
            "files_scanned": dec_scan["files_scanned"],
            "production_ids": len(dec_scan["production"]),
            "test_only_ids": sorted(set(dec_scan["test_only"]) - set(dec_scan["production"])),
            "unresolved_sites": dec_scan["unresolved"],
            "parse_errors": dec_scan["parse_errors"],
        },
        "seed_ts": {"path": _rel(SEED_TS), "ok": seed["ok"],
                    "ids": len(seed["ids"]), "reason": seed.get("reason")},
        "ci": ci,
    }

    with psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
        c = conn.cursor()
        c.execute("SET statement_timeout='120s'")
        c.execute("SET default_transaction_read_only = on")

        c.execute("""SELECT column_name FROM information_schema.columns
                     WHERE table_schema='public' AND table_name='asset_registry'""")
        cols = {r["column_name"] for r in c.fetchall()}
        rec["_meta"]["asset_registry_columns_present"] = sorted(cols)
        rec["_meta"]["contract_columns"] = {
            k: (k in cols) for k in ("domain", "rung", "data_disposition", "superseded_by")}

        c.execute("SELECT count(*) n FROM asset_registry")
        n_assets = c.fetchone()["n"]
        c.execute("SELECT count(*) n FROM asset_registry WHERE is_active")
        n_active = c.fetchone()["n"]
        rec["_meta"]["asset_registry_rows"] = n_assets
        rec["_meta"]["asset_registry_active_rows"] = n_active

        c.execute("SELECT asset_id, layer, scope, catalog_status, asset_kind, is_active, "
                  "has_writer, has_substeps, target_table, depends_on "
                  "FROM asset_registry ORDER BY asset_id")
        registry = {r["asset_id"]: r for r in c.fetchall()}

        # ── contract rules ────────────────────────────────────────────────────
        for rid, assertion, sev, needs, sql in RULES:
            missing = [x for x in needs if x not in cols]
            if missing:
                rec["contract_rules"][rid] = {
                    "assertion": assertion, "severity": sev, "status": BLOCKED,
                    "blocked_by": f"column(s) {missing} do not exist in asset_registry "
                                  f"(migration 590 not applied)",
                    "violations": None, "sql": " ".join(sql.split()), "rows": None}
                continue
            try:
                c.execute(sql)
                rows = c.fetchall()
                rec["contract_rules"][rid] = {
                    "assertion": assertion, "severity": sev,
                    "status": PASS if not rows else FAIL,
                    "violations": len(rows), "sql": " ".join(sql.split()),
                    "rows": [{k: (str(v) if not isinstance(v, (int, float, bool, type(None), str, list))
                                  else v) for k, v in r.items()} for r in rows[:60]]}
            except Exception as e:
                rec["contract_rules"][rid] = {
                    "assertion": assertion, "severity": sev, "status": NM,
                    "blocked_by": f"query error: {str(e).splitlines()[0][:200]}",
                    "violations": None, "sql": " ".join(sql.split()), "rows": None}

        for rid, assertion, reason in UNDETECTABLE:
            rec["undetectable_rules"][rid] = {"assertion": assertion, "reason": reason,
                                              "status": NM}

        # C-13b cycle detection (Python traversal over the live edge set)
        edges = {a: list(r["depends_on"] or []) for a, r in registry.items()}
        colour: dict[str, int] = {}
        cycles: list[list[str]] = []

        def dfs(node: str, stack: list[str]) -> None:
            colour[node] = 1
            stack.append(node)
            for nxt in edges.get(node, []):
                if nxt not in edges:
                    continue
                if colour.get(nxt, 0) == 1:
                    cycles.append(stack[stack.index(nxt):] + [nxt])
                elif colour.get(nxt, 0) == 0:
                    dfs(nxt, stack)
            stack.pop()
            colour[node] = 2

        sys.setrecursionlimit(10000)
        for a in edges:
            if colour.get(a, 0) == 0:
                dfs(a, [])
        rec["undetectable_rules"]["C-13b"] = {
            "assertion": "depends_on graph acyclic",
            "reason": "measured here by DFS over the live edge set",
            "status": PASS if not cycles else FAIL,
            "violations": len(cycles), "cycles": cycles[:10]}

        # C-23 has_substeps vs writer-class truth
        c23_rows = []
        for aid, r in registry.items():
            truth = substeps.get(aid)
            if truth is None:
                continue  # no production writer — C-23 has nothing to compare
            if bool(r["has_substeps"]) != bool(truth):
                c23_rows.append({"asset_id": aid, "registry_has_substeps": r["has_substeps"],
                                 "writer_class_truth": truth})
        rec["undetectable_rules"]["C-23"] = {
            "assertion": "has_substeps equals the writer-class truth",
            "reason": ("measured here by AST: the writer class, or an ancestor OTHER THAN "
                       "the frozen `WriterBase`, defines `plan_substeps` or sets "
                       "`has_substeps = True`. WriterBase's OWN default plan_substeps is "
                       "excluded deliberately — every writer inherits it, so counting it "
                       "would make the detector a constant (CLAUDE.md §N.8). Inheritance is "
                       "resolved by class NAME inside platform/python-sidecar; imports are "
                       "not followed, so a base defined outside that tree is invisible."),
            "status": PASS if not c23_rows else FAIL,
            "violations": len(c23_rows), "rows": c23_rows[:60],
            "assets_compared": len(substeps)}

        # ── criterion 1 — three-way diff ─────────────────────────────────────
        reg_ids = set(registry)
        prod_dec = {a for a in dec_scan["production"] if ASSET_SHAPE.match(a)}
        seed_ids = set(seed["ids"]) if seed["ok"] else set()
        if not seed["ok"]:
            c1 = {"status": NM, "blocked_by": f"seed .ts unreadable: {seed.get('reason')}",
                  "measured_value": None}
        else:
            buckets = {
                "registry_only": sorted(reg_ids - prod_dec - seed_ids),
                "decorator_only": sorted(prod_dec - reg_ids - seed_ids),
                "seed_only": sorted(seed_ids - reg_ids - prod_dec),
                "registry+decorator_not_seed": sorted((reg_ids & prod_dec) - seed_ids),
                "registry+seed_not_decorator": sorted((reg_ids & seed_ids) - prod_dec),
                "decorator+seed_not_registry": sorted((prod_dec & seed_ids) - reg_ids),
            }
            total = sum(len(v) for v in buckets.values())
            c1 = {"status": PASS if total == 0 else FAIL, "measured_value": total,
                  "counts": {"registry": len(reg_ids), "production_decorators": len(prod_dec),
                             "seed": len(seed_ids),
                             "in_all_three": len(reg_ids & prod_dec & seed_ids)},
                  "buckets": buckets}
        c1["detector"] = ("this script: SELECT asset_id FROM asset_registry  ×  AST scan of "
                          "@register('<id>') under platform/python-sidecar (production files "
                          "only, asset-shaped ids only)  ×  regex `^\\s*asset_id:` over "
                          "platform/scripts/seed/asset_registry_seed.ts read as TEXT. "
                          "Violations = ids not present in all three.")
        rec["criteria"]["1_three_way_diff"] = c1

        # ── criterion 2 — contract violations per kind ───────────────────────
        by_kind = {}
        for kind in ("data", "artifact", "service", "source"):
            by_kind[kind] = 0
        blocking_total = 0
        blocked_rules, failing_rules = [], []
        for rid, r in rec["contract_rules"].items():
            if r["status"] == FAIL:
                blocking_total += r["violations"]
                failing_rules.append(f"{rid}={r['violations']}")
                for row in (r["rows"] or []):
                    aid = row.get("asset_id")
                    k = registry.get(aid, {}).get("asset_kind")
                    if k in by_kind:
                        by_kind[k] += 1
            elif r["status"] in (BLOCKED, NM):
                blocked_rules.append(rid)
        undet_fail = [rid for rid, r in rec["undetectable_rules"].items()
                      if r.get("status") == FAIL]
        for rid in undet_fail:
            blocking_total += rec["undetectable_rules"][rid].get("violations", 0)
            failing_rules.append(f"{rid}={rec['undetectable_rules'][rid].get('violations')}")
        never_green = [rid for rid in ("C-25", "C-26", "C-27")]
        rec["criteria"]["2_contract_violations_per_kind"] = {
            "detector": ("this script: every §8 detection SQL of "
                         "00_ARCHITECTURE/control/ASSET_CATALOGUE_CONTRACT_v1_0.md, "
                         "run live; plus C-13b (DFS) and C-23 (AST) implemented here."),
            "status": NM if (blocked_rules or never_green) else (
                PASS if blocking_total == 0 else FAIL),
            "measured_value": blocking_total,
            "violations_by_asset_kind": by_kind,
            "failing_rules": sorted(failing_rules),
            "blocked_rules": sorted(blocked_rules),
            "never_checkable_rules": never_green,
            "blocked_by": ("; ".join(
                ([f"rules {', '.join(sorted(blocked_rules))} cannot run "
                  "(asset_registry columns they need are absent)"] if blocked_rules else []) +
                ([f"rules {', '.join(never_green)} have NO detector at all (contract §8) "
                  "and must never read green"] if never_green else []))
            ) if (blocked_rules or never_green) else None}

        # ── criterion 3 — prefix mismatches ──────────────────────────────────
        c01 = rec["contract_rules"]["C-01"]
        rec["criteria"]["3_prefix_mismatches"] = {
            "detector": "C-01 detection SQL (asset_id prefix vs layer), run live",
            "status": c01["status"], "measured_value": c01["violations"],
            "rows": c01["rows"], "sql": c01["sql"]}

        # ── criterion 4 — dangling or DRAFT-targeted edges ───────────────────
        c11, c12 = rec["contract_rules"]["C-11"], rec["contract_rules"]["C-12"]
        c.execute("""SELECT count(*) n FROM asset_registry a
                     CROSS JOIN LATERAL unnest(a.depends_on) AS d""")
        n_edges = c.fetchone()["n"]
        tot4 = (c12["violations"] or 0) + (c11["violations"] or 0)
        rec["criteria"]["4_dangling_or_draft_edges"] = {
            "detector": "C-12 (dangling: dep with no registry row) + C-11 (CURRENT depending "
                        "on a non-CURRENT, non-source asset), both run live",
            "status": PASS if tot4 == 0 else FAIL, "measured_value": tot4,
            "components": {"dangling_C-12": c12["violations"],
                           "draft_targeted_C-11": c11["violations"]},
            "total_edges_in_registry": n_edges,
            "rows": {"C-12": c12["rows"], "C-11": c11["rows"]}}

        # ── criterion 5 — multi-producer partitions ──────────────────────────
        c.execute("""SELECT target_table, count(*) n,
                            array_agg(asset_id ORDER BY asset_id) ids,
                            array_agg(DISTINCT catalog_status) statuses,
                            bool_or(is_active) any_active,
                            count(*) FILTER (WHERE is_active) n_active
                     FROM asset_registry WHERE target_table IS NOT NULL
                     GROUP BY target_table HAVING count(*) > 1
                     ORDER BY target_table""")
        collisions = [dict(r) for r in c.fetchall()]
        n_coll_tables = len(collisions)
        n_coll_active = len([r for r in collisions if r["n_active"] > 1])
        rec["criteria"]["5_multi_producer_partitions"] = {
            "detector": None,
            "status": NM,
            "measured_value": None,
            "blocked_by": ("NO DETECTOR EXISTS. The criterion asserts that no two producers "
                           "write the same (table × generation × partition). The natural-key "
                           "partition declaration HAS NO COLUMN in asset_registry — contract "
                           "§4.9 / §10.3, rule C-25, which the contract itself marks "
                           "'not checkable, never report as passing'. Under CLAUDE.md §N.8 "
                           "this criterion is null, not green."),
            "measurable_proxy": {
                "what_it_is": "target_table shared by more than one registry row — a NECESSARY "
                              "but not sufficient condition for a multi-producer partition. "
                              "A shared table with correctly disjoint partitions is legitimate "
                              "(co-writers), and this proxy cannot tell the two apart.",
                "co_written_target_tables": n_coll_tables,
                "co_written_with_more_than_one_ACTIVE_producer": n_coll_active,
                "detail": collisions,
                "sql": "SELECT target_table, count(*), array_agg(asset_id) FROM asset_registry "
                       "WHERE target_table IS NOT NULL GROUP BY target_table HAVING count(*)>1"}}

        # ── criterion 6 — throughput rows on inactive assets ─────────────────
        c.execute("""SELECT t.asset_id, count(*) rows_n,
                            array_agg(DISTINCT t.state) states,
                            r.is_active, r.catalog_status
                     FROM asset_throughput t
                     JOIN asset_registry r ON r.asset_id=t.asset_id
                     WHERE r.is_active = false
                     GROUP BY t.asset_id, r.is_active, r.catalog_status ORDER BY 1""")
        inactive_rows = [dict(r) for r in c.fetchall()]
        c.execute("""SELECT t.asset_id, count(*) rows_n FROM asset_throughput t
                     LEFT JOIN asset_registry r ON r.asset_id=t.asset_id
                     WHERE r.asset_id IS NULL GROUP BY t.asset_id ORDER BY 1""")
        unregistered_rows = [dict(r) for r in c.fetchall()]
        n6 = sum(r["rows_n"] for r in inactive_rows) + sum(r["rows_n"] for r in unregistered_rows)
        offenders = sorted({r["asset_id"] for r in inactive_rows} |
                           {r["asset_id"] for r in unregistered_rows})
        p1_only = offenders == ["ka_gochara_sweep"]
        rec["criteria"]["6_throughput_on_inactive_assets"] = {
            "detector": "SELECT ... FROM asset_throughput t JOIN asset_registry r USING(asset_id) "
                        "WHERE r.is_active = false  (+ throughput rows with no registry row)",
            "status": BLOCKED if (n6 > 0 and p1_only) else (PASS if n6 == 0 else FAIL),
            "measured_value": n6,
            "offending_assets": offenders,
            "rows_on_inactive": inactive_rows,
            "rows_with_no_registry_row": unregistered_rows,
            "blocked_by": ("CHARTER §2 P1 COLLISION — the only offender is `ka_gochara_sweep`, "
                           "the charter's named unrecoverable asset. Any operation on it is a "
                           "RESERVED power: parked, never decided by an agent. Plan §14.2 "
                           "assigns its lifecycle exit to rung R3, which has not opened. This "
                           "criterion is therefore NOT PASS and NOT FAIL: it is blocked on a "
                           "reserved decision, and this task neither marks it green nor "
                           "resolves it.") if (n6 > 0 and p1_only) else None}

        # ── criterion 7 — retired without data_disposition ───────────────────
        c08 = rec["contract_rules"]["C-08"]
        c.execute("SELECT asset_id, catalog_status FROM asset_registry "
                  "WHERE catalog_status='RETIRED' ORDER BY 1")
        retired = [dict(r) for r in c.fetchall()]
        rec["criteria"]["7_retired_without_disposition"] = {
            "detector": c08["sql"],
            "status": c08["status"] if c08["status"] != BLOCKED else BLOCKED,
            "measured_value": c08["violations"],
            "blocked_by": c08.get("blocked_by"),
            "retired_assets_live": retired,
            "note": ("`data_disposition` does not exist as a column; migration 590 "
                     "(platform/migrations/590_nirmana_m0_catalogue_contract_columns.sql) "
                     "introduces it. Until it applies this criterion has no detector that "
                     "could return non-zero. An unmeasurable criterion is not a satisfied one."
                     ) if c08["status"] == BLOCKED else None}

        # ── criterion 8 — active assets w/o build coverage or a dead flag ────
        no_writer = []
        for aid, r in registry.items():
            if not r["is_active"]:
                continue
            if aid in prod_dec:
                continue
            no_writer.append({"asset_id": aid, "catalog_status": r["catalog_status"],
                              "asset_kind": r["asset_kind"], "has_writer_flag": r["has_writer"]})
        flagged = [x for x in no_writer if x["has_writer_flag"] is False]
        unflagged = [x for x in no_writer if x["has_writer_flag"] is not False]
        # is the has_writer flag itself trustworthy?
        flag_wrong = [{"asset_id": aid, "has_writer": r["has_writer"],
                       "production_decorator": aid in prod_dec}
                      for aid, r in registry.items()
                      if bool(r["has_writer"]) != (aid in prod_dec)]
        rec["criteria"]["8_active_without_coverage_or_dead_flag"] = {
            "detector": None,
            "status": NM,
            "measured_value": None,
            "blocked_by": ("NO 'DEAD FLAG' FIELD IS DEFINED. asset_registry has no column that "
                           "designates a registered-but-dead asset. `has_writer` (boolean) is "
                           "the only candidate, and the contract "
                           "(ASSET_CATALOGUE_CONTRACT_v1_0.md) does not designate it as the "
                           "dead flag — nor does it define one. The criterion's second half "
                           "therefore has no detector, so the criterion as a whole cannot "
                           "return a non-zero answer honestly. Its FIRST half is measured "
                           "below."),
            "measured_components": {
                "active_assets": n_active,
                "active_assets_with_no_production_@register": len(no_writer),
                "of_those_carrying_has_writer=false": len(flagged),
                "of_those_NOT_carrying_has_writer=false": len(unflagged),
                "detail_no_writer": no_writer,
                "has_writer_flag_disagrees_with_decorator_scan": flag_wrong,
                "why_the_candidate_flag_is_not_trustworthy":
                    f"{len(flag_wrong)} rows have has_writer disagreeing with the live "
                    f"decorator scan, so even reading has_writer=false as 'dead' would be "
                    f"reading a flag that is itself wrong on those rows."},
            "detector_sql": ("SELECT asset_id, catalog_status, asset_kind, has_writer FROM "
                             "asset_registry WHERE is_active  -- minus the AST @register set")}

        # ── criterion 9 — unresolved zero-consumer findings ─────────────────
        if not zc.get("ok"):
            rec["criteria"]["9_unresolved_zero_consumer"] = {
                "detector": None, "status": NM, "measured_value": None,
                "blocked_by": zc.get("reason")}
        else:
            rec["criteria"]["9_unresolved_zero_consumer"] = {
                "detector": ("count of zero-consumer packets in "
                             "00_ARCHITECTURE/control/zero_consumer_evidence.json, minus those "
                             "with a recorded ADHIKĀRIN G1 disposition naming them in "
                             "00_ARCHITECTURE/autonomy/state/DECISIONS.jsonl"),
                "status": PASS if zc["n_unresolved"] == 0 else FAIL,
                "measured_value": zc["n_unresolved"],
                "packets": zc["n_packets"], "disposed": zc["disposed"],
                "asset_ids": zc["asset_ids"]}

        # ── criterion 10 — CI guard merged and BLOCKING ─────────────────────
        # M0-T27 REPAIR. The previous detector asserted "merged AND blocking" and
        # computed `PASS if (guard file exists) and (some workflow names it)`. The
        # word BLOCKING had no code path: no input could make that half false, so
        # the moment M0-T9 landed a deliberately NON-blocking workflow the criterion
        # flipped green on a claim nothing checked (CLAUDE.md §N.8, charter H4).
        # It now measures three things, each of which can independently read false:
        #   (a) merged  — present on the DEFAULT BRANCH, not merely in this worktree;
        #   (b) wired   — invoked from a workflow job;
        #   (c) blocking— that job/step carries no `continue-on-error: true` and the
        #                 run line does not swallow the exit code.
        # A null on (c) is not a pass. GitHub run history is carried as corroborating
        # evidence and never as the verdict.
        exists = bool(ci["guard_scripts"])
        wired = bool(ci["workflow_invocations"])
        blocking = analyse_ci_blocking(ci)
        wf_files = sorted({i["workflow"] for i in ci["workflow_invocations"]})
        merged_check = default_branch_presence(sorted(set(ci["guard_scripts"]) | set(wf_files)))
        gh_ev = github_run_evidence(wf_files)
        merged = bool(merged_check["ok"] and merged_check["present"]
                      and all(merged_check["present"].get(g) for g in ci["guard_scripts"]))
        is_blocking = blocking["all_blocking"] is True
        c10_pass = bool(exists and wired and merged and is_blocking)
        shortfall = []
        if not exists:
            shortfall.append("no guard script implementing the contract exists")
        if not wired:
            shortfall.append("no workflow invokes a guard")
        if not merged:
            shortfall.append(
                "the guard/workflow is NOT on the default branch (`origin/main`) — "
                "'merged' means merged, and present-on-the-campaign-branch is not that"
                if merged_check["ok"] else
                f"merged-to-default-branch could not be determined: {merged_check['reason']}")
        if not is_blocking:
            shortfall.append(
                "the invocation is NOT blocking"
                if blocking["all_blocking"] is False else
                "whether the invocation blocks could not be determined; a null is not a pass")
        rec["criteria"]["10_ci_guard_merged_and_blocking"] = {
            "detector": ("(a) does a guard implementing the Asset Catalogue Contract exist "
                         "under platform/scripts/{governance,ci}; (b) is it invoked from a "
                         ".github/workflows job; (c) is that job/step BLOCKING — no "
                         "`continue-on-error: true`, no `|| true` on the run line; and is the "
                         "guard MERGED, i.e. present on `origin/main` per `git ls-tree`. "
                         "PASS requires all four. GitHub run history is corroboration, not "
                         "the verdict."),
            "status": PASS if c10_pass else FAIL,
            "measured_value": {"guard_scripts_found": len(ci["guard_scripts"]),
                               "workflow_invocations_found": len(ci["workflow_invocations"]),
                               "merged_to_default_branch": merged,
                               "invocation_is_blocking": blocking["all_blocking"]},
            "guard_scripts": ci["guard_scripts"],
            "workflow_invocations": ci["workflow_invocations"],
            "workflows_scanned": ci["workflows_scanned"],
            "blocking_analysis": blocking,
            "merged_to_default_branch_check": merged_check,
            "github_run_evidence": gh_ev,
            "shortfall": shortfall,
            "note": ("WORK_QUEUE id M0-T9 shipped the two guard scripts and a workflow that "
                     "invokes them, and shipped it NON-BLOCKING on purpose: "
                     ".github/workflows/nirmana-m0-guards.yml carries "
                     "`continue-on-error: true` on both jobs and says so in its own header. "
                     "Flipping it to blocking is ADHIKĀRIN's call (charter G9) and has not "
                     "been made. So the merged-and-wired halves have genuinely moved and the "
                     "BLOCKING half has not, which is why this stays FAIL rather than "
                     "becoming green on two of its three clauses. "
                     "Shortfall: " + "; ".join(shortfall))
            if not c10_pass else None}

        # ── criterion 11 — every asset carries domain and rung ──────────────
        c18, c19 = rec["contract_rules"]["C-18"], rec["contract_rules"]["C-19"]
        if c18["status"] == BLOCKED or c19["status"] == BLOCKED:
            rec["criteria"]["11_domain_and_rung_present"] = {
                "detector": "C-18 + C-19 detection SQL",
                "status": BLOCKED, "measured_value": None,
                "blocked_by": ("columns `domain` and/or `rung` do not exist in asset_registry "
                               "(migration 590 not applied). Present: "
                               f"{rec['_meta']['contract_columns']}"),
                "would_be_derived_from": {
                    "domain": "scope: global->shared, per_chart->chart (contract §5.1)",
                    "rung": "layer: brahmagyan->R0 ... mimamsa->R5 (contract §5.2)"}}
        else:
            tot11 = (c18["violations"] or 0) + (c19["violations"] or 0)
            rec["criteria"]["11_domain_and_rung_present"] = {
                "detector": "C-18 + C-19 detection SQL",
                "status": PASS if tot11 == 0 else FAIL, "measured_value": tot11,
                "components": {"C-18_domain": c18["violations"], "C-19_rung": c19["violations"]},
                "rows": {"C-18": c18["rows"], "C-19": c19["rows"]}}

        # ── criterion 12 — §11 CI domain-coherence assertion green ──────────
        dom_col = "domain" if "domain" in cols else None
        if dom_col:
            c.execute("""SELECT a.asset_id, a.domain, d AS dep, b.domain AS dep_domain
                         FROM asset_registry a CROSS JOIN LATERAL unnest(a.depends_on) AS d
                         JOIN asset_registry b ON b.asset_id=d
                         WHERE a.domain='shared' AND b.domain<>'shared' ORDER BY 1,3""")
        else:
            c.execute("""SELECT a.asset_id, a.scope, d AS dep, b.scope AS dep_scope
                         FROM asset_registry a CROSS JOIN LATERAL unnest(a.depends_on) AS d
                         JOIN asset_registry b ON b.asset_id=d
                         WHERE a.scope='global' AND b.scope<>'global' ORDER BY 1,3""")
        incoherent = [dict(r) for r in c.fetchall()]
        # ── M0-T32 correction ────────────────────────────────────────────────
        # Readings 1 and 2 of this scorecard recorded `blocked_by: "THE ASSERTION
        # DOES NOT EXIST"`. That was FALSE at the time it was written and is false
        # now: `X-04` ("domain coherence: a shared asset depends only on shared
        # assets", origin "plan §11 (CI shape guard addition)") has been implemented
        # in platform/scripts/governance/check_asset_catalogue_contract.py since
        # M0-T9 (2026-08-23T05:14:37Z) and returns 0 violations against the live
        # database. The scorecard could not see it because its own `domain_markers`
        # tuple matched none of the guard's wording (fixed in scan_ci_guards above).
        # A false claim in the instrument is worse than the gap it described, so it
        # is corrected rather than softened.
        #
        # The criterion still does NOT pass, for a DIFFERENT and now-honest reason:
        # the assertion has never RUN in CI. It is carried by the same guard script
        # and the same workflow as criterion 10, under the same
        # `continue-on-error: true`, and absent from `origin/main` for the same
        # reason. So criterion 12 reduces entirely to criterion 10: nothing
        # criterion-12-specific stands between here and green.
        c12_assertion_exists = bool(ci["domain_coherence_scripts"])
        c12_wired = bool(ci["domain_coherence_workflow_invocations"])
        c12_pass = bool(c12_assertion_exists and c12_wired and merged and is_blocking
                        and len(incoherent) == 0)
        c12_shortfall = []
        if not c12_assertion_exists:
            c12_shortfall.append("no script implements the domain-coherence assertion")
        if not c12_wired:
            c12_shortfall.append("no workflow invokes a script that carries the assertion")
        if not merged:
            c12_shortfall.append("the carrying guard/workflow is NOT on `origin/main` "
                                 "(criterion 10's `merged` half)")
        if not is_blocking:
            c12_shortfall.append("the invocation is NOT blocking, so no run of it can gate "
                                 "anything (criterion 10's `blocking` half)")
        if len(incoherent):
            c12_shortfall.append(f"{len(incoherent)} live domain-coherence violation(s)")
        rec["criteria"]["12_ci_domain_coherence_green"] = {
            "detector": ("rule `X-04` in platform/scripts/governance/"
                         "check_asset_catalogue_contract.py — `domain coherence: a shared "
                         "asset depends only on shared assets`, severity BLOCKING, origin "
                         "`plan §11 (CI shape guard addition)`. PASS requires the assertion "
                         "to EXIST, to be invoked from a workflow, for that invocation to be "
                         "blocking and merged to `origin/main` (criterion 10's two halves), "
                         "and for the underlying condition to measure zero here."),
            "status": PASS if c12_pass else FAIL,
            "measured_value": {"assertion_exists": c12_assertion_exists,
                               "assertion_wired_to_a_workflow": c12_wired,
                               "invocation_is_blocking": is_blocking,
                               "merged_to_default_branch": merged,
                               "live_violations": len(incoherent)},
            "assertion_exists": c12_assertion_exists,
            "has_ever_run_in_ci": None,
            "reduces_to": "10_ci_guard_merged_and_blocking",
            "shortfall": c12_shortfall,
            "corrected_claim": {
                "readings_1_and_2_said": "THE ASSERTION DOES NOT EXIST.",
                "verdict": "FALSE — and false when written.",
                "correcting_task": "M0-T32",
                "correcting_ts": "2026-08-23",
                "evidence": ["platform/scripts/governance/check_asset_catalogue_contract.py "
                             "Rule(\"X-04\", BLOCKING, \"domain coherence: a shared asset "
                             "depends only on shared assets\", x04, origin=\"plan §11 (CI "
                             "shape guard addition)\")",
                             "M0-T31 live guard run 2026-08-23T06:58:51Z: X-04 pass, "
                             "0 violations",
                             "WORK_QUEUE M0-T9 measured_live: X-04 = 0; green_now_list "
                             "includes X-04"],
                "root_cause": ("this generator's `domain_markers` tuple matched none of the "
                               "guard's wording, so its absence-detector could only ever "
                               "return absent — a constant wearing a detector's clothes "
                               "(CLAUDE.md §N.8), inside the scorecard built to catch that "
                               "class."),
                "what_is_actually_true": ("the assertion exists and measures zero; it has "
                                          "never RUN in CI, for exactly criterion 10's "
                                          "reasons. Criterion 12 therefore reduces to "
                                          "criterion 10.")},
            "underlying_condition_measured_here": {
                "what": "shared-domain asset depending on a chart-domain asset",
                "measured_via": ("`domain` column" if dom_col else
                                 "`scope` column (pre-590 equivalent: global<->shared, "
                                 "per_chart<->chart, contract §5.1 is 1:1)"),
                "violations": len(incoherent), "rows": incoherent},
            "plan_named_suspects": ["ka_graha_sancara", "ka_muhurta_seva",
                                    "mi_kula", "mi_vistara"],
            "domain_coherence_ci_scripts": ci["domain_coherence_scripts"],
            "domain_coherence_workflow_invocations":
                ci["domain_coherence_workflow_invocations"],
            "note": ("Criterion 12 reduces to criterion 10. The assertion (X-04) exists and "
                     "returns 0 live; what is missing is a RUN of it that gates — the same "
                     "`continue-on-error: true` and the same absence from `origin/main` that "
                     "hold criterion 10 at FAIL. `has_ever_run_in_ci` is null, not false: "
                     "nothing in this generator queries GitHub run history for a verdict "
                     "(github_run_evidence is corroboration only). Shortfall: "
                     + "; ".join(c12_shortfall)) if not c12_pass else None}

        # ── M0-T27 · falsifiability of every PASSing rule ────────────────────
        mut: dict = {}
        for rid, r in rec["contract_rules"].items():
            if r["status"] != PASS or not r.get("sql"):
                continue
            spec = MUTATIONS.get(rid)
            if not spec:
                mut[rid] = {"proved": None,
                            "why": "no mutation declared for this rule — its zero is "
                                   "NOT proven falsifiable by this script"}
                continue
            subs, why = spec
            sql = r["sql"]
            applied = []
            for find, repl in subs:
                if find not in sql:
                    applied.append({"find": find, "applied": False})
                    continue
                sql = sql.replace(find, repl)
                applied.append({"find": find, "applied": True})
            if not all(a["applied"] for a in applied):
                mut[rid] = {"proved": None, "why": "mutation text did not match the shipped "
                                                   "SQL; nothing proved", "substitutions": applied}
                continue
            try:
                c.execute(sql)
                n = len(c.fetchall())
                mut[rid] = {"proved": n > 0, "mutant_rows": n, "why": why,
                            "mutant_sql": " ".join(sql.split()),
                            "verdict": ("the shipped query CAN return non-zero against this "
                                        "database, so its zero is a measurement"
                                        if n > 0 else
                                        "THE MUTANT ALSO RETURNED ZERO — this rule's zero is "
                                        "NOT evidence of conformance")}
            except Exception as e:
                mut[rid] = {"proved": None, "why": f"mutant query error: "
                                                   f"{str(e).splitlines()[0][:160]}"}
        rec["falsifiability_probe"] = {
            "what_it_is": ("for every contract rule reading PASS, the shipped SQL re-run with "
                           "one deliberate mutation that must make it fire. A zero from a "
                           "query that cannot return non-zero is not evidence "
                           "(CLAUDE.md §N.8). Read-only; the mutant is never used for a "
                           "verdict."),
            "rules": mut,
            "passing_rules_proved_falsifiable": sorted(k for k, v in mut.items()
                                                       if v.get("proved") is True),
            "passing_rules_NOT_proved": sorted(k for k, v in mut.items()
                                               if v.get("proved") is not True)}

        # ── M0-T27 · durability of every green ───────────────────────────────
        # A criterion can go green two ways: because the defect was fixed, or
        # because a column was hand-written that the next `asset_registry_seed.ts`
        # run overwrites from EXCLUDED. The second kind of green is worse than a
        # red, because nothing announces its expiry. This block measures which
        # kind each green is, from three live inputs: the seed's own DO UPDATE
        # column list, the seed's per-asset literals, and the live row values.
        seed_upsert = scan_seed_upsert()
        seed_lits = scan_seed_literals()
        overwritten = set(seed_upsert["do_update_columns"])
        never_inserted = sorted(cols - set(seed_upsert["insert_columns"]) - {"asset_id"})

        c.execute("SELECT asset_id, asset_kind, asset_type, scope, layer "
                  "FROM asset_registry ORDER BY asset_id")
        live_lits = {r["asset_id"]: r for r in c.fetchall()}

        divergent_rows = []
        for aid, live in live_lits.items():
            s = seed_lits.get(aid)
            if not s:
                continue  # no seed entry — the seed cannot revert what it does not write
            for field in SEED_LITERAL_FIELDS:
                if field not in overwritten:
                    continue
                want = s.get(field)
                if want is None:
                    continue  # unmodelled (no literal, no default) — not claimed either way
                if str(live.get(field)) != str(want):
                    divergent_rows.append({
                        "asset_id": aid, "column": field,
                        "live_value": live.get(field), "seed_would_write": want,
                        "seed_declares_it": s.get(field + "_declared")})
        divergent_assets = sorted({r["asset_id"] for r in divergent_rows})
        divergent_by_col: dict[str, set] = {}
        for r in divergent_rows:
            divergent_by_col.setdefault(r["column"], set()).add(r["asset_id"])

        prev_rules = {}
        if previous:
            for src in ("contract_rules", "undetectable_rules"):
                for rid, v in (previous.get(src) or {}).items():
                    prev_rules[rid] = v

        per_rule = {}
        for rid, r in list(rec["contract_rules"].items()):
            refs = columns_referenced(r.get("sql"), cols)
            exposed = sorted(set(refs) & overwritten)
            at_risk = sorted({a for cn in exposed for a in divergent_by_col.get(cn, set())})
            attribution = None
            pv = prev_rules.get(rid)
            if pv and r["status"] == PASS and pv.get("status") == FAIL and pv.get("rows"):
                removed = sorted({x.get("asset_id") for x in pv["rows"] if x.get("asset_id")})
                if removed and set(removed) <= set(divergent_assets):
                    attribution = {
                        "previous_status": pv.get("status"),
                        "previous_violations": pv.get("violations"),
                        "rows_that_stopped_violating": removed,
                        "verdict": ("EVERY row that stopped violating this rule is a row "
                                    "whose live value now differs from what the seed would "
                                    "write. This rule's PASS rests on a repair the next "
                                    "seed run reverts.")}
                elif removed:
                    attribution = {
                        "previous_status": pv.get("status"),
                        "previous_violations": pv.get("violations"),
                        "rows_that_stopped_violating": removed,
                        "rows_also_seed_divergent": sorted(set(removed) & set(divergent_assets)),
                        "verdict": "improvement only PARTLY attributable to seed-divergent rows"}
            per_rule[rid] = {
                "status": r["status"], "violations": r.get("violations"),
                "columns_referenced": refs,
                "seed_overwritable_columns": exposed,
                "seed_divergent_assets_among_them": at_risk,
                "durability": ("n/a — not passing" if r["status"] != PASS else
                               ("NON-DURABLE" if attribution and
                                attribution.get("verdict", "").startswith("EVERY")
                                else ("EXPOSED" if at_risk else "durable"))),
                "attribution": attribution}

        CRIT_RULES = {
            "2_contract_violations_per_kind": sorted(rec["contract_rules"]),
            "3_prefix_mismatches": ["C-01"],
            "4_dangling_or_draft_edges": ["C-11", "C-12"],
            "7_retired_without_disposition": ["C-08"],
            "11_domain_and_rung_present": ["C-18", "C-19"],
        }
        per_crit = {}
        for k, v in rec["criteria"].items():
            rules = CRIT_RULES.get(k, [])
            refs = set()
            for rid in rules:
                refs |= set(per_rule.get(rid, {}).get("columns_referenced", []))
            refs |= set(columns_referenced(v.get("sql") or v.get("detector_sql"), cols))
            exposed = sorted(refs & overwritten)
            at_risk = sorted({a for cn in exposed for a in divergent_by_col.get(cn, set())})
            nondurable_rules = [rid for rid in rules
                                if per_rule.get(rid, {}).get("durability") == "NON-DURABLE"]
            if v["status"] != PASS:
                dur, why = "n/a — not passing", None
            elif nondurable_rules:
                dur = "NON-DURABLE"
                why = (f"constituent rule(s) {nondurable_rules} pass only because of a repair "
                       f"the seed's ON CONFLICT DO UPDATE reverts")
            elif at_risk:
                dur = "EXPOSED"
                why = (f"passes on columns the seed overwrites ({exposed}); "
                       f"{len(at_risk)} live row(s) already differ from the seed's value, so a "
                       f"seed run would move this criterion's inputs")
            else:
                dur = "durable"
                why = ("no column this criterion reads is in the seed's ON CONFLICT DO UPDATE "
                       "list" if refs else
                       "criterion is not sourced from asset_registry columns the seed writes")
            # coverage durability: a column the seed NEVER inserts is NULL on any row
            # the seed newly creates, regardless of what is true of today's rows.
            coverage = sorted(refs & set(never_inserted))
            per_crit[k] = {"status": v["status"], "columns_read": sorted(refs),
                           "seed_overwritable_columns": exposed,
                           "seed_divergent_assets_among_them": at_risk,
                           "constituent_rules": rules,
                           "non_durable_constituent_rules": nondurable_rules,
                           "columns_the_seed_never_inserts": coverage,
                           "durability": dur, "why": why}
            v["durability"] = dur
            if why:
                v["durability_note"] = why
            if coverage and v["status"] == PASS:
                v["durability_coverage_note"] = (
                    f"Columns {coverage} are absent from the seed's INSERT column list and "
                    f"have no NOT NULL / DEFAULT / trigger behind them, so any asset the seed "
                    f"newly inserts lands with them NULL and re-breaks this criterion. "
                    f"Today's rows are safe; the criterion's coverage of FUTURE rows is not "
                    f"enforced by anything.")

        # ── post-reseed projection ───────────────────────────────────────────
        # "EXPOSED" says a criterion reads a column the seed overwrites. It does
        # not say the criterion would BREAK. This answers that directly and
        # read-only: re-run each PASSing rule against a CTE that SHADOWS
        # asset_registry with the values the seed would write for the columns
        # this script can model, and see which rules start firing. Nothing is
        # written; the projection is never used as the reported status.
        projection: dict = {}
        model_cols = sorted(set(SEED_LITERAL_FIELDS) & overwritten)
        proj_rows = [(aid, *(seed_lits[aid].get(f) for f in model_cols))
                     for aid in sorted(seed_lits)
                     if aid in live_lits
                     and any(seed_lits[aid].get(f) is not None for f in model_cols)]
        if proj_rows and model_cols:
            ordered_cols = sorted(cols)
            sel = ", ".join(
                (f"COALESCE(s.{cn}, r.{cn}) AS {cn}" if cn in model_cols else f"r.{cn}")
                for cn in ordered_cols)
            vals = ", ".join(
                "(" + ", ".join(("NULL::text" if v is None else "'" + str(v).replace("'", "''") + "'::text")
                                for v in row) + ")"
                for row in proj_rows)
            prefix = (f"WITH s(asset_id, {', '.join(model_cols)}) AS (VALUES {vals}), "
                      f"asset_registry AS (SELECT {sel} FROM public.asset_registry r "
                      f"LEFT JOIN s ON s.asset_id = r.asset_id) ")
            for rid, r in rec["contract_rules"].items():
                if r["status"] != PASS or not r.get("sql"):
                    continue
                try:
                    c.execute(prefix + r["sql"])
                    n = len(c.fetchall())
                    projection[rid] = {
                        "violations_now": r.get("violations"),
                        "violations_after_a_reseed": n,
                        "would_break": n > 0,
                        "verdict": ("this rule STOPS PASSING once the seed restores its "
                                    "columns" if n > 0 else
                                    "this rule still passes after the seed restores its "
                                    "columns")}
                except Exception as e:
                    projection[rid] = {"violations_now": r.get("violations"),
                                       "violations_after_a_reseed": None,
                                       "would_break": None,
                                       "verdict": f"projection query error: "
                                                  f"{str(e).splitlines()[0][:160]}"}
        # ── M0-T32 · fold the projection back into the PER-RULE durability ───
        # `EXPOSED` says a rule reads a column the seed overwrites and that some
        # live row already differs. The post-reseed projection says something
        # strictly stronger and directly: re-run against the values the seed would
        # write, the rule FIRES. When the projection has proved that, the row must
        # read NON-DURABLE — a rule at zero only because of a repair the next seed
        # run reverts is not passing on its merits, and the rule-detail table was
        # reading EXPOSED for exactly such rows (C-14: 0 now → 8 after a re-seed).
        # Upgrading a label on a detector's proof, never downgrading one.
        for rid, pv_ in projection.items():
            if pv_.get("would_break") is not True or rid not in per_rule:
                continue
            per_rule[rid]["durability"] = "NON-DURABLE"
            per_rule[rid]["non_durable_proof"] = {
                "source": "post_reseed_projection",
                "violations_now": pv_.get("violations_now"),
                "violations_after_a_reseed": pv_.get("violations_after_a_reseed"),
                "verdict": (f"this rule reads {pv_.get('violations_now')} today and "
                            f"{pv_.get('violations_after_a_reseed')} once "
                            "asset_registry_seed.ts restores the columns it owns. Its zero "
                            "is a repair the next seed run reverts, not a fixed defect."),
                "reverted_by": sorted(set(per_rule[rid].get(
                    "seed_divergent_assets_among_them") or [])),
            }

        for k, v in per_crit.items():
            rules = v["constituent_rules"]
            breaks = [rid for rid in rules
                      if (projection.get(rid) or {}).get("would_break") is True]
            unknown = [rid for rid in rules
                       if rid in projection and projection[rid].get("would_break") is None]
            v["rules_that_break_after_a_reseed"] = breaks
            v["rules_whose_projection_failed"] = unknown
            if v["status"] == PASS and breaks:
                v["durability"] = "NON-DURABLE"
                v["why"] = (f"projected forward: constituent rule(s) {breaks} start firing "
                            f"once asset_registry_seed.ts restores the columns it owns")
                rec["criteria"][k]["durability"] = "NON-DURABLE"
                rec["criteria"][k]["durability_note"] = v["why"]
            elif v["status"] == PASS and v["durability"] == "EXPOSED" and rules and not unknown:
                v["why"] = ((v.get("why") or "") +
                            " — projected forward, however, none of its constituent rules "
                            f"({', '.join(rules)}) starts firing after a re-seed, so the "
                            "exposure is real but does not by itself break this criterion")
                rec["criteria"][k]["durability_note"] = v["why"]

        rec["durability"] = {
            "post_reseed_projection": {
                "what_it_is": ("each PASSing rule re-run against a CTE that shadows "
                               "asset_registry with the values asset_registry_seed.ts would "
                               "write, for the columns this script can model "
                               f"({model_cols}). Read-only; never used as a reported status. "
                               "Columns the script cannot model are left at their live values, "
                               "so this is a LOWER BOUND on what a re-seed would break."),
                "modelled_columns": model_cols,
                "seed_rows_projected": len(proj_rows),
                "rules": projection,
                "rules_that_would_break": sorted(k for k, v in projection.items()
                                                 if v.get("would_break") is True)},
            "why_this_exists": (
                "A repair written straight to asset_registry survives only if its column is "
                "absent from asset_registry_seed.ts's `ON CONFLICT (asset_id) DO UPDATE SET` "
                "list. Columns in that list are restored from EXCLUDED on the next seed run. "
                "A green resting on such a column is a green a re-seed silently undoes, which "
                "is strictly worse than a red."),
            "seed_upsert_parse": seed_upsert,
            "columns_the_seed_overwrites_on_reseed": sorted(overwritten),
            "columns_the_seed_never_inserts": never_inserted,
            "live_vs_seed_divergence": {
                "detector": ("for each seed-overwritten column this script can model "
                             f"({sorted(SEED_LITERAL_FIELDS)}), compare the LIVE value against "
                             "the literal the seed declares for that asset (or the seed's own "
                             "`?? 'data'` default when the key is absent). A difference means "
                             "the next seed run changes that cell."),
                "modelled_columns": sorted(set(SEED_LITERAL_FIELDS) & overwritten),
                "divergent_cells": len(divergent_rows),
                "divergent_assets": divergent_assets,
                "rows": divergent_rows},
            "per_rule": per_rule,
            "per_criterion": per_crit}

        # ── re-measure at the end (a migration wave is running concurrently) ─
        c.execute("""SELECT column_name FROM information_schema.columns
                     WHERE table_schema='public' AND table_name='asset_registry'""")
        cols_after = {r["column_name"] for r in c.fetchall()}
        c.execute("SELECT count(*) n FROM asset_registry")
        n_after = c.fetchone()["n"]
        c.execute("""SELECT count(*) n FROM asset_throughput t
                     JOIN asset_registry r ON r.asset_id=t.asset_id WHERE r.is_active=false""")
        n6_after = c.fetchone()["n"]
        try:
            c.execute("SELECT filename, applied_at FROM _migrations_applied "
                      "ORDER BY applied_at DESC LIMIT 5")
            migs = [{"filename": r["filename"], "applied_at": str(r["applied_at"])}
                    for r in c.fetchall()]
        except Exception as e:
            migs = [{"error": str(e).splitlines()[0][:160]}]

    # ── disagreement register ────────────────────────────────────────────────
    # Where a sibling M0 artifact (or the plan) states a figure for a quantity
    # this script also measures, BOTH are recorded. A disagreement between two
    # angles is a failure to be surfaced, never a mean to be taken.
    cr = rec["contract_rules"]
    ur = rec["undetectable_rules"]
    dis = [
        {"quantity": "C-04 — data/artifact rows failing the target_table rule",
         "this_script": cr["C-04"]["violations"],
         "other_source": "ASSET_CATALOGUE_CONTRACT_v1_0.md §6, rule C-04",
         "other_value": 10,
         "reconciliation": ("Both are right about different things. 10 is the count of "
                            "data/artifact rows with target_table NULL. The rule as written "
                            "(and as its own §8 SQL executes) ALSO fails a row whose "
                            "target_table names a table that does not exist — "
                            "`bg_sky_calendar` → `bg_sky_events`, which is absent from "
                            "information_schema.tables. The contract's §6 count reported the "
                            "NULL half only. 11 is the rule's full result."),
         "disagreement": cr["C-04"]["violations"] != 10},
        {"quantity": "C-17 — graded service_health with no health_probe",
         "this_script": cr["C-17"]["violations"],
         "other_source": "ASSET_CATALOGUE_CONTRACT_v1_0.md §6, rule C-17",
         "other_value": 3,
         "reconciliation": ("The contract's §6 cell names 3 assets, all `healthy` "
                            "(ka_dasha_kala, ka_muhurta_seva, ka_tulana). Its own §8 SQL "
                            "matches `IN ('healthy','degraded','unhealthy')`, which also "
                            "catches `ka_graha_sancara` ('unhealthy', no probe). The "
                            "contract's stated count disagrees with the contract's own SQL. "
                            "4 is the SQL's result."),
         "disagreement": cr["C-17"]["violations"] != 3},
        {"quantity": "0.6a — has_substeps false negatives (C-23)",
         "this_script": ur["C-23"].get("violations"),
         "other_source": ("NIRMANA_ELEVATION_PLAN v3.0 §0.6a / v4.0 (states 14) vs "
                          "DERIVED_FIELD_REPAIR_PROPOSAL_v1_0.md §4 (M0-T8, states 12)"),
         "other_value": "plan 14 · M0-T8 12",
         "reconciliation": ("This script's detector and M0-T8's are INDEPENDENT and differ in "
                            "rule — M0-T8 uses (defines plan_substeps AND defines "
                            "run_substep); this one uses (overrides plan_substeps OR sets the "
                            "class attribute has_substeps=True), in both cases EXCLUDING "
                            "WriterBase's own default. Two independent detectors returning 12 "
                            "against the plan's 14 is corroboration; the plan's figure is the "
                            "outlier and is not measured."),
         "disagreement": ur["C-23"].get("violations") != 14},
        {"quantity": "criterion 9 — zero-consumer findings",
         "this_script": rec["criteria"]["9_unresolved_zero_consumer"].get("measured_value"),
         "other_source": ("NIRMANA_ELEVATION_PLAN §1 (states 13) · the plan's own per-asset "
                          "annotations (7) · ZERO_CONSUMER_EVIDENCE_v1_0.md (23 packets)"),
         "other_value": "plan-summary 13 · plan-annotations 7 · M0-T6 packets 23",
         "reconciliation": ("This script counts the M0-T6 packet set and subtracts recorded "
                            "ADHIKĀRIN G1 dispositions; there are none, so unresolved = "
                            "packets. The plan's 13 has no per-asset list behind it and does "
                            "not reconcile with the plan's own annotations. Not averaged, not "
                            "adopted."),
         "disagreement": True},
        {"quantity": "target_table NULL rows (all kinds)",
         "this_script": None,
         "other_source": "CENSUS_REPORT.md §5 (M0-T1) states 14; contract §6 C-04 states 10",
         "other_value": "census 14 (all rows) · contract 10 (data/artifact only)",
         "reconciliation": ("Not a disagreement once scoped: 14 counts every registry row, "
                            "10 counts only the data/artifact rows the rule applies to. "
                            "Recorded so the two figures are not read as a conflict."),
         "disagreement": False},
    ]
    rec["disagreements"] = dis

    finished = datetime.datetime.now(datetime.timezone.utc)
    moved = {
        "contract_columns_changed": sorted(
            (cols_after - cols) | (cols - cols_after)),
        "asset_registry_rows_start": n_assets, "asset_registry_rows_end": n_after,
        "criterion_6_inactive_throughput_rows_start":
            sum(r["rows_n"] for r in inactive_rows),
        "criterion_6_inactive_throughput_rows_end": n6_after,
    }
    moved["anything_moved"] = bool(moved["contract_columns_changed"]) or \
        n_assets != n_after or \
        moved["criterion_6_inactive_throughput_rows_start"] != n6_after

    tally = {PASS: 0, FAIL: 0, NM: 0, BLOCKED: 0}
    for _k, _v in rec["criteria"].items():
        tally[_v["status"]] = tally.get(_v["status"], 0) + 1

    rec["_meta"].update({
        "tally": tally,
        "task": "M0-T32 (re-measurement 3)", "built_by_task": "M0-T17",
        "artifact": "M0_EXIT_SCORECARD_v1_0",
        "generator": _rel(pathlib.Path(__file__)),
        "measured_at_start": started.isoformat(), "measured_at_end": finished.isoformat(),
        "git_branch": git_branch, "git_sha": git_sha,
        "db_access": "READ-ONLY (default_transaction_read_only=on; SELECT only)",
        "recent_migrations_applied": migs,
        "re_measurement_at_end_of_run": moved,
        "asset_registry_columns_at_end": sorted(cols_after),
    })

    # ── what changed since the previous run of this generator ────────────────
    delta = {"previous_run": None, "changed": [], "note": None}
    if previous:
        delta["previous_run"] = previous.get("_meta", {}).get("measured_at_end")
        for k, v in rec["criteria"].items():
            pv = previous.get("criteria", {}).get(k)
            if not pv:
                delta["changed"].append({"criterion": k, "was": "(absent)",
                                         "now": v["status"]})
                continue
            if pv.get("status") != v["status"] or pv.get("measured_value") != v.get("measured_value"):
                delta["changed"].append({
                    "criterion": k,
                    "was": {"status": pv.get("status"), "measured_value": pv.get("measured_value")},
                    "now": {"status": v["status"], "measured_value": v.get("measured_value")}})
        pg = set(previous.get("criteria", {})
                 .get("10_ci_guard_merged_and_blocking", {}).get("guard_scripts") or [])
        ng = set(rec["criteria"]["10_ci_guard_merged_and_blocking"]["guard_scripts"])
        if pg != ng:
            delta["changed"].append({"criterion": "10_ci_guard_merged_and_blocking",
                                     "guard_scripts_added": sorted(ng - pg),
                                     "guard_scripts_removed": sorted(pg - ng)})
        delta["note"] = ("no criterion changed status or value since the previous run"
                         if not delta["changed"] else
                         f"{len(delta['changed'])} change(s) since the previous run")
    else:
        delta["note"] = "no previous m0_exit_scorecard.json — this is a first run"
    rec["_meta"]["delta_vs_previous_run"] = delta

    # ── M0-T27 · reading history ─────────────────────────────────────────────
    # This file is regenerated in place, so before M0-T27 each run ERASED the
    # reading it replaced and kept only a compact diff. The delta is the point of
    # the artifact — M0-T10 re-runs this at freeze time and needs to see movement
    # in BOTH directions — so every reading is now retained here, oldest first.
    # A run that bootstraps history from a previous JSON with no history block
    # (the M0-T17 first reading) reconstructs that entry from the file it read.
    def _snapshot(r: dict, label: str) -> dict:
        return {
            "label": label,
            "task": r.get("_meta", {}).get("task"),
            "measured_at_end": r.get("_meta", {}).get("measured_at_end"),
            "git_sha": (r.get("_meta", {}).get("git_sha") or "")[:12],
            "tally": r.get("_meta", {}).get("tally"),
            "criteria": {k: {"status": v.get("status"),
                             "measured_value": v.get("measured_value"),
                             "durability": v.get("durability")}
                         for k, v in (r.get("criteria") or {}).items()},
            "contract_rules": {rid: {"status": v.get("status"),
                                     "violations": v.get("violations")}
                               for rid, v in (r.get("contract_rules") or {}).items()},
        }

    history = list((previous or {}).get("_meta", {}).get("reading_history") or [])
    if previous and not history:
        history = [_snapshot(previous, "reading 1 — M0-T17 first measurement")]
    history.append(_snapshot(rec, f"reading {len(history) + 1} — {rec['_meta']['task']}"))
    rec["_meta"]["reading_history"] = history
    rec["_meta"]["baseline_reading"] = history[0] if history else None

    OUT_JSON.write_text(json.dumps(rec, indent=1, default=str))
    render_md(rec)
    print(f"criteria: {len(rec['criteria'])}  tally: {tally}")
    print(f"moved during run: {moved['anything_moved']}  ({moved})")
    print(f"wrote {_rel(OUT_JSON)} and {_rel(OUT_MD)}")
    return 0


CRIT_TITLES = {
    "1_three_way_diff": "1 · three-way diff (registry vs `@register` vs seed) = 0",
    "2_contract_violations_per_kind": "2 · contract violations per kind = 0",
    "3_prefix_mismatches": "3 · prefix mismatches = 0",
    "4_dangling_or_draft_edges": "4 · dangling or DRAFT-targeted edges = 0",
    "5_multi_producer_partitions": "5 · multi-producer partitions = 0",
    "6_throughput_on_inactive_assets": "6 · throughput rows on inactive assets = 0",
    "7_retired_without_disposition": "7 · retired assets without a `data_disposition` = 0",
    "8_active_without_coverage_or_dead_flag":
        "8 · active assets with neither build coverage nor a dead flag = 0",
    "9_unresolved_zero_consumer": "9 · unresolved zero-consumer findings = 0",
    "10_ci_guard_merged_and_blocking": "10 · CI guard merged and **blocking**",
    "11_domain_and_rung_present": "11 · every asset carrying `domain` and `rung` *(v4.1)*",
    "12_ci_domain_coherence_green": "12 · the §11 CI domain-coherence assertion green *(v4.1)*",
}

# Figures a sibling M0 artifact states for the same quantity. Carried so a
# disagreement is visible; never used in place of this script's own measurement.
SIBLING_FIGURES = {
    "1_three_way_diff": ("CENSUS_REPORT.md / census.json (M0-T1)",
                         "registry_only 1 · registry+seed_not_decorator 4 · all other "
                         "buckets 0 → 5 ids not in all three"),
    "3_prefix_mismatches": ("CENSUS_REPORT.md §6 (M0-T1) and "
                            "ASSET_CATALOGUE_CONTRACT §6 rule C-01", "1 (`lel_events`)"),
    "4_dangling_or_draft_edges": ("DAG_AUDIT_v1_0.md §1–§2 (M0-T7)",
                                  "dangling 0 · CURRENT→DRAFT 3 → 3"),
    "5_multi_producer_partitions": ("census.json target_table_collisions (M0-T1)",
                                    "5 co-written target_tables"),
    "6_throughput_on_inactive_assets": ("census.json throughput_on_inactive_or_retired (M0-T1)",
                                        "1 asset (`ka_gochara_sweep`), 3 rows"),
    "9_unresolved_zero_consumer": ("ZERO_CONSUMER_EVIDENCE_v1_0.md §0/§2 (M0-T6)",
                                   "23 packets found live; plan §1 states 13; the plan's own "
                                   "per-asset annotations count 7"),
    "11_domain_and_rung_present": ("ASSET_CATALOGUE_CONTRACT §6 rules C-18/C-19 (M0-T2)",
                                   "128 / 128 (columns do not exist)"),
}


def render_md(rec: dict) -> None:
    m = rec["_meta"]
    t = m["tally"]
    A = []
    w = A.append
    w("---")
    w("artifact: M0_EXIT_SCORECARD")
    w("version: 1.0")
    w("status: LIVE-MEASUREMENT")
    w(f"task: {m.get('task', 'M0-T17')}")
    w(f"built_by_task: {m.get('built_by_task', 'M0-T17')}")
    w(f"readings: {len(m.get('reading_history') or [])}")
    w(f"generated: {m['measured_at_end']}")
    w(f"generator: {m['generator']}")
    w("---")
    w("")
    w("# NIRMĀṆA M0 — Exit-Criteria Scorecard v1.0")
    w("")
    w(f"**Measured:** {m['measured_at_start']} → {m['measured_at_end']} (UTC)  ")
    w(f"**Branch / commit:** `{m['git_branch']}` @ `{m['git_sha'][:12]}`  ")
    w(f"**Database access:** {m['db_access']}  ")
    w(f"**Regenerate:** `python3 {m['generator']}`  ")
    w("**Status:** measurement only. This document certifies nothing and closes nothing "
      "(I16 / charter H7). PARĪKṢAKA decides; M0-T10 re-runs the generator at freeze time "
      "rather than trusting this snapshot.")
    w("")
    hist = m.get("reading_history") or []
    base = m.get("baseline_reading") or {}
    bt = (base.get("tally") or {}) if base else {}
    w("## 0 — Tally, then and now")
    w("")
    if base and len(hist) > 1:
        w(f"**then** = `{base.get('label')}`, {base.get('measured_at_end')} @ "
          f"`{base.get('git_sha')}`  ")
        w(f"**now** = `{(hist[-1] or {}).get('label')}`, {m['measured_at_end']} @ "
          f"`{m['git_sha'][:12]}`")
        w("")
        w("| status | then | now | Δ | meaning |")
        w("|---|--:|--:|--:|---|")
        for st, meaning in ((PASS, "a detector ran and returned zero"),
                            (FAIL, "a detector ran and returned non-zero"),
                            (NM, "**no detector exists that could return non-zero. "
                                 "Not a pass** (CLAUDE.md §N.8)"),
                            (BLOCKED, "a detector exists but cannot run yet; the blocker "
                                      "is named per row")):
            a, b = bt.get(st, 0), t.get(st, 0)
            d = b - a
            w(f"| {st} | {a} | {b} | {'+' if d > 0 else ''}{d if d else '—'} | {meaning} |")
    else:
        w("| status | count | meaning |")
        w("|---|--:|---|")
        w(f"| PASS | {t.get(PASS,0)} | a detector ran and returned zero |")
        w(f"| FAIL | {t.get(FAIL,0)} | a detector ran and returned non-zero |")
        w(f"| NOT-MEASURABLE | {t.get(NM,0)} | **no detector exists that could return "
          "non-zero. Not a pass** (CLAUDE.md §N.8) |")
        w(f"| BLOCKED | {t.get(BLOCKED,0)} | a detector exists but cannot run yet; the "
          "blocker is named per row |")
    w("")
    dur = rec.get("durability") or {}
    pc = dur.get("per_criterion") or {}
    nondur = sorted(k for k, v in pc.items() if v.get("durability") == "NON-DURABLE")
    expo = sorted(k for k, v in pc.items() if v.get("durability") == "EXPOSED")
    ndrules = sorted(rid for rid, v in ((rec.get("durability") or {}).get("per_rule") or {}).items()
                     if v.get("durability") == "NON-DURABLE")
    brkrules = ((rec.get("durability") or {}).get("post_reseed_projection") or {}).get(
        "rules_that_would_break") or []
    w(f"**{t.get(PASS,0)} of 12 criteria are satisfied by a detector's output.** The other "
      f"{12-t.get(PASS,0)} are not, and none of them is green.")
    if dur:
        w("")
        w(f"**Criteria whose PASS rests on a NON-DURABLE repair: {len(nondur)}"
          + (f" ({', '.join(nondur)})" if nondur else "") + ". "
          f"Criteria passing on inputs a re-seed would move (EXPOSED): {len(expo)}"
          + (f" ({', '.join(expo)})" if expo else "") + ".** "
          "A repair is *durable* only if the column it wrote is absent from "
          "`asset_registry_seed.ts`'s `ON CONFLICT (asset_id) DO UPDATE SET` list; columns in "
          "that list are restored from `EXCLUDED` on the next seed run. "
          + (f"Contract rules resting on such a repair: `{', '.join(ndrules)}`. "
             if ndrules else "")
          + (f"Rules that a projected re-seed makes start firing again: "
             f"`{', '.join(brkrules)}`. " if brkrules else "")
          + "§3b measures all of this, projects each PASSing rule forward through a "
            "simulated re-seed, and names every cell that would move.")
    w("")
    w("### At a glance — then → now")
    w("")
    w("| # | criterion | then | now | measured | durability | blocker |")
    w("|---|---|---|---|--:|---|---|")
    bc = (base.get("criteria") or {}) if base else {}
    for k, v in rec["criteria"].items():
        mv = v.get("measured_value")
        mv = "—" if mv is None else (json.dumps(mv) if isinstance(mv, dict) else str(mv))
        mv = (mv[:52] + "…") if len(mv) > 52 else mv
        blk = (v.get("blocked_by") or "")
        blk = (blk[:96] + "…") if len(blk) > 96 else blk
        then = (bc.get(k) or {}).get("status", "—")
        arrow = "" if then == v["status"] else " *(moved)*"
        d = (pc.get(k) or {}).get("durability", "—")
        d = f"**{d}**" if d in ("NON-DURABLE", "EXPOSED") else d
        w(f"| {k.split('_')[0]} | {CRIT_TITLES[k].split('·',1)[1].strip()} | {then} | "
          f"**{v['status']}**{arrow} | `{mv}` | {d} | {blk or '—'} |")
    w("")
    if len(hist) > 1:
        w("Every reading this generator has taken is retained in "
          "`m0_exit_scorecard.json` under `_meta.reading_history` (oldest first), so a "
          "re-run adds a reading rather than erasing the one it replaces:")
        w("")
        w("| reading | task | measured | commit | PASS | FAIL | NOT-MEASURABLE | BLOCKED |")
        w("|---|---|---|---|--:|--:|--:|--:|")
        for h in hist:
            ht = h.get("tally") or {}
            w(f"| {h.get('label')} | {h.get('task')} | {h.get('measured_at_end')} | "
              f"`{h.get('git_sha')}` | {ht.get(PASS,0)} | {ht.get(FAIL,0)} | "
              f"{ht.get(NM,0)} | {ht.get(BLOCKED,0)} |")
        w("")
    mv = m["re_measurement_at_end_of_run"]
    w("### Did anything move while this ran?")
    w("")
    w("A migration wave was running concurrently, so every load-bearing quantity was read "
      "again at the end of the run:")
    w("")
    w("| quantity | at start | at end |")
    w("|---|--:|--:|")
    w(f"| `asset_registry` rows | {mv['asset_registry_rows_start']} | "
      f"{mv['asset_registry_rows_end']} |")
    w(f"| throughput rows on inactive assets | "
      f"{mv['criterion_6_inactive_throughput_rows_start']} | "
      f"{mv['criterion_6_inactive_throughput_rows_end']} |")
    w(f"| contract columns added/removed mid-run | — | "
      f"{mv['contract_columns_changed'] or 'none'} |")
    w("")
    w(f"**Anything moved: {'YES — the numbers above are the honest before/after' if mv['anything_moved'] else 'no'}.** "
      f"Contract columns present at end of run: "
      f"`{ {k: (k in set(m['asset_registry_columns_at_end'])) for k in ('domain','rung','data_disposition','superseded_by')} }`.")
    w("")
    d = m.get("delta_vs_previous_run") or {}
    w("### What changed since the previous run of this generator")
    w("")
    w(f"Previous run: `{d.get('previous_run') or 'none'}`. {d.get('note','')}.")
    if d.get("changed"):
        w("")
        w("```json")
        w(json.dumps(d["changed"], indent=1, default=str)[:4000])
        w("```")
    w("")
    w("Filesystem-sourced criteria (10 and 12) can move between runs without any database "
      "change, because sibling tasks are authoring the guards they look for. The block above "
      "is where that shows up; the table above it covers database movement inside a single "
      "run.")
    w("")
    w("Most recent rows of `_migrations_applied`:")
    w("")
    for r in m["recent_migrations_applied"]:
        w(f"- `{r.get('filename', r)}` — {r.get('applied_at','')}")
    w("")
    w("---")
    w("")
    w("## 1 — The twelve criteria")
    w("")
    for k, v in rec["criteria"].items():
        w(f"### {CRIT_TITLES[k]}")
        w("")
        was = (bc.get(k) or {}) if base else {}
        if was:
            wv = was.get("measured_value")
            w(f"**Status: {was.get('status')} → {v['status']}**  ")
            w(f"**Measured value:** `{json.dumps(wv) if isinstance(wv,dict) else wv}` → "
              f"`{json.dumps(v.get('measured_value')) if isinstance(v.get('measured_value'),dict) else v.get('measured_value')}`  ")
        else:
            w(f"**Status: {v['status']}**  ")
            mvv = v.get("measured_value")
            w(f"**Measured value:** `{json.dumps(mvv) if isinstance(mvv,dict) else mvv}`  ")
        if v.get("durability") and v["durability"] != "n/a — not passing":
            w(f"**Durability of this reading: {v['durability']}** — {v.get('durability_note','')}  ")
        if v.get("durability_coverage_note"):
            w(f"**Coverage caveat:** {v['durability_coverage_note']}  ")
        det = v.get("detector") or v.get("detector_sql")
        if det:
            w("")
            w("**Detector**")
            w("")
            w("```")
            for line in str(det).split("\n"):
                w(line)
            w("```")
        else:
            w("")
            w("**Detector: NONE.** See the blocker below. An unmeasurable criterion is not a "
              "satisfied one.")
        if v.get("sql"):
            w("")
            w("```sql")
            w(v["sql"])
            w("```")
        if v.get("blocked_by"):
            w("")
            w(f"**Blocked by / why this is not a pass:** {v['blocked_by']}")
        if v.get("note"):
            w("")
            w(f"**Note:** {v['note']}")
        sib = SIBLING_FIGURES.get(k)
        if sib:
            w("")
            w(f"**Where the number came from:** this script's own live query. A sibling "
              f"artifact — {sib[0]} — reports: {sib[1]}.")
        else:
            w("")
            w("**Where the number came from:** this script's own live measurement. No sibling "
              "artifact states a figure for this quantity.")
        for key in ("shortfall", "blocking_analysis", "merged_to_default_branch_check",
                    "github_run_evidence",
                    "counts", "buckets", "components", "measured_components",
                    "measurable_proxy", "violations_by_asset_kind", "failing_rules",
                    "blocked_rules", "never_checkable_rules", "rows",
                    "rows_on_inactive", "rows_with_no_registry_row", "offending_assets",
                    "retired_assets_live", "guard_scripts", "workflow_invocations",
                    "underlying_condition_measured_here", "plan_named_suspects",
                    "disposed", "packets", "asset_ids", "total_edges_in_registry",
                    "domain_coherence_ci_scripts",
                    "domain_coherence_workflow_invocations", "would_be_derived_from",
                    "corrected_claim", "reduces_to"):
            if key in v and v[key] not in (None, [], {}, ""):
                w("")
                w(f"<details><summary><code>{key}</code></summary>")
                w("")
                w("```json")
                w(json.dumps(v[key], indent=1, default=str)[:9000])
                w("```")
                w("")
                w("</details>")
        w("")
        w("---")
        w("")
    w("## 2 — Contract rule detail (criterion 2's constituents)")
    w("")
    br = (base.get("contract_rules") or {}) if base else {}
    w("| rule | assertion | severity | then | now | violations then → now | durability |")
    w("|---|---|---|---|---|--:|---|")
    prule = (rec.get("durability") or {}).get("per_rule") or {}
    for rid, r in rec["contract_rules"].items():
        vio = r["violations"]
        b = br.get(rid) or {}
        d = (prule.get(rid) or {}).get("durability", "—")
        d = f"**{d}**" if d in ("NON-DURABLE", "EXPOSED") else d
        w(f"| `{rid}` | {r['assertion']} | {r['severity']} | {b.get('status','—')} | "
          f"**{r['status']}** | {b.get('violations','—') if b else '—'} → "
          f"{'—' if vio is None else vio} | {d} |")
    for rid, r in rec["undetectable_rules"].items():
        b = br.get(rid) or {}
        w(f"| `{rid}` | {r['assertion']} | — | {b.get('status','—')} | "
          f"**{r.get('status')}** | {b.get('violations','—') if b else '—'} → "
          f"{r.get('violations','—')} | — |")
    w("")
    w("### Rules that must NEVER read green")
    w("")
    for rid, r in rec["undetectable_rules"].items():
        if r.get("status") == NM:
            w(f"- **`{rid}`** — {r['assertion']}. {r['reason']}")
    w("")
    w("---")
    w("")
    w("## 2b — Disagreement register")
    w("")
    w("Where another artifact states a figure for a quantity measured here, both are shown. "
      "**Nothing below is averaged.** Two angles disagreeing is a finding.")
    w("")
    w("| quantity | this script (measured) | other source | its figure | disagree? |")
    w("|---|--:|---|---|:-:|")
    for d in rec.get("disagreements", []):
        w(f"| {d['quantity']} | `{d['this_script']}` | {d['other_source']} | "
          f"{d['other_value']} | {'**YES**' if d['disagreement'] else 'no'} |")
    w("")
    for d in rec.get("disagreements", []):
        w(f"- **{d['quantity']}** — {d['reconciliation']}")
    w("")
    w("---")
    w("")
    w("## 3 — Source scans behind criterion 1 and criterion 8")
    w("")
    s = rec["source_scans"]
    w("```json")
    w(json.dumps(s, indent=1, default=str)[:6000])
    w("```")
    w("")
    w("---")
    w("")
    fp = rec.get("falsifiability_probe") or {}
    if fp:
        w("## 3a — Falsifiability: could each PASSing detector have returned non-zero?")
        w("")
        w(fp["what_it_is"])
        w("")
        w("| rule | mutation | mutant rows | proved falsifiable |")
        w("|---|---|--:|:-:|")
        for rid, v in fp["rules"].items():
            pr = v.get("proved")
            mark = "**yes**" if pr is True else ("**NO**" if pr is False else "—")
            w(f"| `{rid}` | {v.get('why','')} | {v.get('mutant_rows','—')} | {mark} |")
        w("")
        notp = fp["passing_rules_NOT_proved"]
        if notp:
            w(f"**Not proved falsifiable: `{', '.join(notp)}`.** Their zero is reported as "
              "measured but this script did not demonstrate the query can fire. That is a gap "
              "in the evidence, stated rather than papered over.")
        else:
            w("**Every PASSing rule fired under its mutant.** No zero in this reading comes "
              "from a query that could not have returned non-zero.")
        w("")
        w("---")
        w("")
    w("## 3b — Durability: which greens a re-seed would undo")
    w("")
    if not dur:
        w("_(not measured in this reading)_")
    else:
        w(dur["why_this_exists"])
        w("")
        su = dur["seed_upsert_parse"]
        w(f"Parsed from `{su['path']}` **as text** (never imported — D-9 / D-13): "
          f"parse ok = `{su['ok']}`"
          + (f", reason `{su['reason']}`" if su.get("reason") else "") + ".")
        w("")
        w("| question | answer |")
        w("|---|---|")
        w(f"| columns the seed **overwrites** on every re-run (`DO UPDATE SET`) | "
          f"`{', '.join(dur['columns_the_seed_overwrites_on_reseed'])}` |")
        w(f"| columns the seed **never inserts** (a new seed row lands NULL/default) | "
          f"`{', '.join(dur['columns_the_seed_never_inserts'])}` |")
        lvd = dur["live_vs_seed_divergence"]
        w(f"| live cells that already differ from what the seed would write | "
          f"**{lvd['divergent_cells']}** across {len(lvd['divergent_assets'])} asset(s) |")
        w("")
        w("**Divergence detector**")
        w("")
        w("```")
        w(lvd["detector"])
        w("```")
        w("")
        if lvd["rows"]:
            w("| asset | column | live now | seed would write | seed declares it? |")
            w("|---|---|---|---|:-:|")
            for r in lvd["rows"]:
                w(f"| `{r['asset_id']}` | `{r['column']}` | `{r['live_value']}` | "
                  f"`{r['seed_would_write']}` | "
                  f"{'yes' if r['seed_declares_it'] else 'no — seed default'} |")
        else:
            w("_No modelled cell diverges: on the columns this script can model, the live "
              "values and the seed's values agree, so a re-seed would not move them._")
        w("")
        w("### Rules whose improvement rests on a reverted repair")
        w("")
        rows = [(rid, v) for rid, v in prule.items() if v.get("attribution")]
        if not rows:
            w("_None: no rule that newly passes had all of its former violating rows land in "
              "the seed-divergent set._")
        else:
            w("| rule | then | now | rows that stopped violating | verdict |")
            w("|---|---|---|---|---|")
            for rid, v in rows:
                a = v["attribution"]
                w(f"| `{rid}` | {a['previous_status']} ({a['previous_violations']}) | "
                  f"{v['status']} ({v['violations']}) | "
                  f"{', '.join('`'+x+'`' for x in a['rows_that_stopped_violating'])} | "
                  f"{a['verdict']} |")
        w("")
        prj = dur.get("post_reseed_projection") or {}
        if prj:
            w("### Projected forward: what a re-seed would actually break")
            w("")
            w(prj["what_it_is"])
            w("")
            if prj["rules"]:
                w("| rule | violations now | violations after a re-seed | breaks? |")
                w("|---|--:|--:|:-:|")
                for rid, v in prj["rules"].items():
                    wb = v.get("would_break")
                    w(f"| `{rid}` | {v.get('violations_now')} | "
                      f"{'—' if v.get('violations_after_a_reseed') is None else v['violations_after_a_reseed']} | "
                      f"{'**YES**' if wb else ('—' if wb is None else 'no')} |")
                w("")
                brk = prj["rules_that_would_break"]
                w(f"**Rules that stop passing after a re-seed: "
                  f"{('`' + ', '.join(brk) + '`') if brk else 'none'}.**")
            else:
                w("_No PASSing rule could be projected._")
            w("")
        w("### Per-criterion durability")
        w("")
        w("| # | status | durability | columns read that the seed overwrites | why |")
        w("|---|---|---|---|---|")
        for k, v in pc.items():
            why = (v.get("why") or "—")
            why = (why[:180] + "…") if len(why) > 180 else why
            dd = v["durability"]
            dd = f"**{dd}**" if dd in ("NON-DURABLE", "EXPOSED") else dd
            w(f"| {k.split('_')[0]} | {v['status']} | {dd} | "
              f"`{', '.join(v['seed_overwritable_columns']) or '—'}` | {why} |")
        w("")
        w("<details><summary><code>durability — full record</code></summary>")
        w("")
        w("```json")
        w(json.dumps(dur, indent=1, default=str)[:24000])
        w("```")
        w("")
        w("</details>")
    w("")
    w("---")
    w("")
    w("## 4 — What this scorecard does NOT establish")
    w("")
    w("- It does not certify M0. It measures. Certification is PARĪKṢAKA's (I16 / H7), and "
      "the freeze is M0-T10's.")
    w("- A **PASS** here means one detector returned zero at one instant against one database. "
      "It is not a claim that the underlying property is guaranteed going forward — that is "
      "what criterion 10's CI guard would be for, and criterion 10 does not pass.")
    w("- **NOT-MEASURABLE is not a soft PASS.** Criteria 5 and 8 have no detector at all, and "
      "criterion 2 carries three rules (C-25/C-26/C-27) the contract itself marks "
      "un-checkable. Any dashboard that renders those green is itself the defect this "
      "campaign exists to remove.")
    w("- Criterion 6 is neither PASS nor FAIL. Its single offender is the charter's named "
      "unrecoverable asset; resolving it is a reserved power (P1) and rung R3's work. This "
      "task recorded the collision and did not touch it. **Criterion 7 has the same single "
      "offender** (`ka_gochara_sweep`, the one RETIRED row, now measurably missing a "
      "`data_disposition`): it reads FAIL because a detector ran and returned 1, and that is "
      "the honest status, but the row behind it is equally reserved and equally untouched.")
    w("- A **durable** green in §3b means only that no column the criterion reads is "
      "overwritten by the seed. It is not a guarantee: the seed is one write path among "
      "several, and a migration or a writer can still move the same cell.")
    w("- Criterion 10's detector was REPAIRED in this reading. Its predecessor computed "
      "`PASS if a guard file exists and some workflow names it` while asserting 'merged AND "
      "blocking' — the word *blocking* had no code path, so no input could make that half "
      "false. Against the current tree that constant would have reported PASS. It now parses "
      "`continue-on-error` / `|| true` and checks presence on `origin/main`, and reads FAIL. "
      "The correction is recorded here rather than quietly applied, because a detector that "
      "changed its own answer is exactly the thing a reader must be able to audit.")
    w("- The decorator scan follows no imports: a writer base class defined outside "
      "`platform/python-sidecar` is invisible to the C-23 derivation. Stated, not hidden.")
    w("- The seed `.ts` is regex-parsed as text, never imported (D-9 / D-13). A seed entry "
      "whose `asset_id:` is written on a continuation line would be missed.")
    w("")
    OUT_MD.write_text("\n".join(A) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
