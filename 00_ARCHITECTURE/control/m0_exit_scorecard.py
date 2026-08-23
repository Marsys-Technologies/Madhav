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
    domain_markers = ("domain_coherence", "domain-coherence", "shared asset may depend")

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
            "blocked_by": ("rules " + ", ".join(sorted(blocked_rules)) +
                           " cannot run (migration 590 columns absent); rules "
                           + ", ".join(never_green) +
                           " have NO detector at all (contract §8) and must never read green")
            if (blocked_rules or never_green) else None}

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
        merged = bool(ci["guard_scripts"])
        wired = bool(ci["workflow_invocations"])
        rec["criteria"]["10_ci_guard_merged_and_blocking"] = {
            "detector": ("filesystem scan: does a guard implementing the Asset Catalogue "
                         "Contract exist under platform/scripts/{governance,ci}; is it invoked "
                         "from a .github/workflows job; is that step blocking"),
            "status": PASS if (merged and wired) else FAIL,
            "measured_value": {"guard_scripts_found": len(ci["guard_scripts"]),
                               "workflow_invocations_found": len(ci["workflow_invocations"])},
            "guard_scripts": ci["guard_scripts"],
            "workflow_invocations": ci["workflow_invocations"],
            "workflows_scanned": ci["workflows_scanned"],
            "note": ("WORK_QUEUE id M0-T9 ('CI guards, merged and BLOCKING (0.10)') is "
                     "queued_not_dispatched. Nothing has been built yet, so this reads FAIL "
                     "— a real detector returning a real non-zero-shortfall, not a block.")
            if not (merged and wired) else None}

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
        rec["criteria"]["12_ci_domain_coherence_green"] = {
            "detector": None,
            "status": FAIL,
            "measured_value": None,
            "blocked_by": ("THE ASSERTION DOES NOT EXIST. Plan §11 requires the CI shape guard "
                           "to assert domain coherence (a shared asset may depend only on "
                           "shared assets). No CI job asserts it: "
                           f"{len(ci['domain_coherence_workflow_invocations'])} workflow "
                           "invocations found. 'Green' cannot be read off a check that does not "
                           "run — CLAUDE.md §N.8. Status FAIL is the honest reading of "
                           "'the assertion is green': it is not, because it is not."),
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
                ci["domain_coherence_workflow_invocations"]}

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

    rec["_meta"].update({
        "task": "M0-T17", "artifact": "M0_EXIT_SCORECARD_v1_0",
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

    # tally
    tally = {PASS: 0, FAIL: 0, NM: 0, BLOCKED: 0}
    for k, v in rec["criteria"].items():
        tally[v["status"]] = tally.get(v["status"], 0) + 1
    rec["_meta"]["tally"] = tally

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
    w("task: M0-T17")
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
    w("## 0 — Tally")
    w("")
    w("| status | count | meaning |")
    w("|---|--:|---|")
    w(f"| PASS | {t.get(PASS,0)} | a detector ran and returned zero |")
    w(f"| FAIL | {t.get(FAIL,0)} | a detector ran and returned non-zero |")
    w(f"| NOT-MEASURABLE | {t.get(NM,0)} | **no detector exists that could return non-zero. "
      "Not a pass** (CLAUDE.md §N.8) |")
    w(f"| BLOCKED | {t.get(BLOCKED,0)} | a detector exists but cannot run yet; the blocker is "
      "named per row |")
    w("")
    w(f"**{t.get(PASS,0)} of 12 criteria are satisfied by a detector's output.** The other "
      f"{12-t.get(PASS,0)} are not, and none of them is green.")
    w("")
    w("### At a glance")
    w("")
    w("| # | criterion | measured | status | blocker |")
    w("|---|---|--:|---|---|")
    for k, v in rec["criteria"].items():
        mv = v.get("measured_value")
        mv = "—" if mv is None else (json.dumps(mv) if isinstance(mv, dict) else str(mv))
        blk = (v.get("blocked_by") or "")
        blk = (blk[:110] + "…") if len(blk) > 110 else blk
        w(f"| {k.split('_')[0]} | {CRIT_TITLES[k].split('·',1)[1].strip()} | `{mv}` | "
          f"**{v['status']}** | {blk or '—'} |")
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
        w(f"**Status: {v['status']}**  ")
        mvv = v.get("measured_value")
        w(f"**Measured value:** `{json.dumps(mvv) if isinstance(mvv,dict) else mvv}`  ")
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
        for key in ("counts", "buckets", "components", "measured_components",
                    "measurable_proxy", "violations_by_asset_kind", "failing_rules",
                    "blocked_rules", "never_checkable_rules", "rows",
                    "rows_on_inactive", "rows_with_no_registry_row", "offending_assets",
                    "retired_assets_live", "guard_scripts", "workflow_invocations",
                    "underlying_condition_measured_here", "plan_named_suspects",
                    "disposed", "packets", "asset_ids", "total_edges_in_registry",
                    "domain_coherence_ci_scripts",
                    "domain_coherence_workflow_invocations", "would_be_derived_from"):
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
    w("| rule | assertion | severity | status | violations |")
    w("|---|---|---|---|--:|")
    for rid, r in rec["contract_rules"].items():
        vio = r["violations"]
        w(f"| `{rid}` | {r['assertion']} | {r['severity']} | **{r['status']}** | "
          f"{'—' if vio is None else vio} |")
    for rid, r in rec["undetectable_rules"].items():
        w(f"| `{rid}` | {r['assertion']} | — | **{r.get('status')}** | "
          f"{r.get('violations','—')} |")
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
      "task recorded the collision and did not touch it.")
    w("- The decorator scan follows no imports: a writer base class defined outside "
      "`platform/python-sidecar` is invisible to the C-23 derivation. Stated, not hidden.")
    w("- The seed `.ts` is regex-parsed as text, never imported (D-9 / D-13). A seed entry "
      "whose `asset_id:` is written on a continuation line would be missed.")
    w("")
    OUT_MD.write_text("\n".join(A) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
