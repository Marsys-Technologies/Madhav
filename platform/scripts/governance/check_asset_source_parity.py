#!/usr/bin/env python3
"""check_asset_source_parity.py — the Nirmāṇa M0 three-way source-parity guard.

Nirmāṇa autonomous campaign, WORK_QUEUE id **M0-T9**. Implements the first of M0's
exit criteria (`NIRMANA_ELEVATION_PLAN_v4_0.md` §14.1): the **three-way diff** between

    S1  asset_registry            (live, or a dated committed snapshot)
    S2  @register('<asset_id>')   decorators in the python writer tree
    S3  asset_registry_seed.ts    the seed's asset_id list

============================================================================
WHY THE PARSER IS BORROWED AND NOT REWRITTEN
============================================================================
This guard does NOT re-derive the decorator scan. It imports
`00_ARCHITECTURE/control/census.py`'s `_decorator_ids()` — the M0-T1 census's own
AST-based parse — and runs it. Two separate incidents in this campaign make that
non-negotiable:

  * M0-T1 found that a **regex** decorator scan counted `@register(...)` mentions
    inside docstrings and comments and missed four real writers.
  * M0-T8 hit the mirror-image failure from the other side: its first **AST** pass
    silently dropped the `@register(ASSET_ID)` module-constant form, missing four
    writers of which two were HEAVY.

The lesson common to both is not "use an AST" — it is **a parser that silently drops
what it cannot resolve is a guard with a hole in it**. So rule P-01 below asserts that
the UNRESOLVED list is EMPTY, and the list is printed in full whenever it is not.
`_decorator_ids()` returns an explicit `UNRESOLVED:<ast dump>` marker for every
`@register(...)` argument it cannot resolve to a string, and this guard treats even one
such marker as a hard failure — because an unresolved registration means the writer
census is incomplete by an unknown amount, and every downstream count built on it is
therefore unknown too, not merely slightly off.

`census.py` imports `psycopg` at module scope for its own live-DB sources. The AST
parse needs no database. This guard therefore installs a stub `psycopg` module ONLY if
the real one is unavailable (CI), imports census, and uses nothing but its parsing
helpers. That is stated here so nobody mistakes the stub for a database shortcut: no
query, live or otherwise, is issued through census by this script.

============================================================================
THE THREE-VALUED OUTPUT
============================================================================
Same discipline as `check_asset_catalogue_contract.py`:

    pass | fail | not_checkable

`not_checkable` is never collapsed into `pass`. A leg of the diff whose source cannot
be read (no seed file, no registry snapshot, an unparseable module) makes the rules
that depend on it `not_checkable` — the diff has not been performed, and "not
performed" is not "agreed" (CLAUDE.md §N.8).

Rules
  P-01  BLOCKING  every @register(...) argument resolves — UNRESOLVED list is empty
  P-02  BLOCKING  no production writer id is absent from asset_registry
  P-03  BLOCKING  no asset_registry id is absent from BOTH the writer tree and the seed
  P-04  BLOCKING  no seed id is absent from asset_registry
  P-05  BLOCKING  no asset id is registered by two different production modules
  P-06  BLOCKING  no decorator id outside the six-prefix asset-id grammar in production
                  code (a test-fixture id must live under a test path)

Known, disclosed divergences live in `asset_source_parity_allowlist.json`, itemized,
dated and attributed, one entry per asset. An entry missing a required field is a
guard ERROR, not an accepted exemption (the discipline `migration_number_guard.ts`'s
`disclosed_additions` established).

Exit codes
  0  no rule failed
  1  at least one rule failed
  2  bad usage / unreadable input
  3  guard-level error, or a self-test expectation not met
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
import types

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
CENSUS_PATH = REPO_ROOT / "00_ARCHITECTURE" / "control" / "census.py"
FIXTURES = HERE / "asset_source_parity_fixtures"
ALLOWLIST_PATH = HERE / "asset_source_parity_allowlist.json"
DEFAULT_WRITER_ROOT = REPO_ROOT / "platform" / "python-sidecar"
DEFAULT_SEED = REPO_ROOT / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"
DEFAULT_REGISTRY = HERE / "asset_catalogue_baseline_20260823.json"

PASS, FAIL, NOT_CHECKABLE = "pass", "fail", "not_checkable"


class GuardError(Exception):
    pass


# ─────────────────────────────────────────────────────────────────────────────
def load_census():
    """Import 00_ARCHITECTURE/control/census.py for its AST parse helpers.

    NOT a copy, NOT a re-derivation — the same function M0-T1's census ran.
    """
    try:
        have_psycopg = importlib.util.find_spec("psycopg") is not None
    except Exception:          # noqa: BLE001 — a finder may RAISE, not just return None
        have_psycopg = False
    if not have_psycopg:
        stub = types.ModuleType("psycopg")
        rows = types.ModuleType("psycopg.rows")
        rows.dict_row = None                      # never called: no query is issued
        stub.rows = rows
        sys.modules.setdefault("psycopg", stub)
        sys.modules.setdefault("psycopg.rows", rows)
    if not CENSUS_PATH.exists():
        raise GuardError(f"census.py not found at {CENSUS_PATH} — this guard refuses "
                         f"to re-derive the decorator parse with a regex (M0-T1/M0-T8)")
    spec = importlib.util.spec_from_file_location("nirmana_census", CENSUS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                  # module scope issues no query
    for attr in ("_decorator_ids", "_is_test_path", "SEED_ID_RE", "ASSET_ID_RE"):
        if not hasattr(mod, attr):
            raise GuardError(f"census.py no longer exposes `{attr}` — the parser this "
                             f"guard borrows has moved; reconcile before trusting "
                             f"either")
    return mod


def scan_decorators(census, writer_root: pathlib.Path) -> dict:
    """Returns {'ids': {id: [sites]}, 'unresolved': [...], 'parse_errors': [...]}"""
    import ast
    ids: dict[str, list] = {}
    unresolved: list[dict] = []
    parse_errors: list[dict] = []
    if not writer_root.exists():
        raise GuardError(f"writer root does not exist: {writer_root}")
    for p in sorted(writer_root.rglob("*.py")):
        sp = str(p).replace("\\", "/")
        if any(x in sp for x in ("/venv/", "/node_modules/", "/__pycache__/",
                                 "/.git/", "/.clone/")):
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError as e:
            parse_errors.append({"file": sp, "error": str(e)})
            continue
        try:
            tree = ast.parse(text, filename=str(p))
        except SyntaxError as e:
            parse_errors.append({"file": sp, "line": e.lineno, "error": e.msg})
            continue
        is_test = census._is_test_path(p)
        for aid, lineno, how in census._decorator_ids(tree):
            rel = sp[len(str(REPO_ROOT)) + 1:] if sp.startswith(str(REPO_ROOT)) else sp
            if aid is None:
                unresolved.append({"file": rel, "line": lineno, "resolution": how})
                continue
            ids.setdefault(aid, []).append(
                {"file": rel, "line": lineno, "is_test": is_test, "resolution": how})
    return {"ids": ids, "unresolved": unresolved, "parse_errors": parse_errors}


def scan_seed(census, seed_path: pathlib.Path) -> tuple[set[str] | None, str | None]:
    if not seed_path.exists():
        return None, f"seed file not found at {seed_path}"
    out = set()
    for line in seed_path.read_text(errors="replace").splitlines():
        m = census.SEED_ID_RE.match(line)
        if m:
            out.add(m.group(1))
    if not out:
        return None, f"{seed_path} parsed but yielded 0 asset_id entries"
    return out, None


def read_registry(path: pathlib.Path | None, live: bool) -> tuple[set[str] | None, str | None, dict]:
    if live:
        sys.path.insert(0, str(HERE))
        import check_asset_catalogue_contract as cc          # noqa: PLC0415
        raw = cc.read_live()
        return {a["asset_id"] for a in raw["assets"]}, None, raw.get("_meta", {})
    if path is None or not path.exists():
        return None, f"registry snapshot not found: {path}", {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ({a["asset_id"] for a in raw.get("assets", [])}, None,
            raw.get("_meta", {}) | {"snapshot_file": path.name})


# ─────────────────────────────────────────────────────────────────────────────
REQUIRED_ALLOWLIST_FIELDS = ("class", "owner", "reason", "disclosed_via", "dated")


def load_allowlist(path: pathlib.Path) -> dict:
    if not path.exists():
        raise GuardError(f"allowlist not found: {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    for aid, ent in (doc.get("disclosed_divergences") or {}).items():
        missing = [f for f in REQUIRED_ALLOWLIST_FIELDS if not ent.get(f)]
        if missing:
            raise GuardError(f"allowlist entry '{aid}' is missing required field(s) "
                             f"{missing} — an incomplete disclosure is not a disclosure")
    return doc


def result(status, violations=None, reason=None, detail=None):
    return {"status": status, "violation_count": len(violations or []),
            "violations": violations or [], "reason": reason, "detail": detail or {}}


def run(census, writer_root, seed_path, registry_path, live, allow) -> dict:
    dec = scan_decorators(census, writer_root)
    seed, seed_err = scan_seed(census, seed_path)
    reg, reg_err, reg_meta = read_registry(registry_path, live)
    disclosed = allow.get("disclosed_divergences") or {}

    prod = {aid: [s for s in sites if not s["is_test"]]
            for aid, sites in dec["ids"].items()}
    prod_ids = {aid for aid, sites in prod.items() if sites}
    test_only = {aid for aid, sites in dec["ids"].items() if not prod.get(aid)}

    rules: dict[str, dict] = {}

    # P-01 — the hole this guard exists to refuse
    if dec["parse_errors"]:
        rules["P-01"] = result(FAIL, dec["unresolved"] + [
            {"class": "parse_error", **e} for e in dec["parse_errors"]],
            "a module the parser could not read is an unknown number of missing "
            "registrations, not zero")
    else:
        rules["P-01"] = result(FAIL if dec["unresolved"] else PASS, dec["unresolved"],
                               None, {"registrations_resolved":
                                      sum(len(v) for v in dec["ids"].values())})

    def _excused(aid, cls):
        e = disclosed.get(aid)
        return bool(e and e.get("class") == cls)

    # P-02 — production writer with no registry row
    if reg is None:
        rules["P-02"] = result(NOT_CHECKABLE, [], reg_err)
    else:
        v = [{"asset_id": a, "class": "decorator_not_in_registry",
              "sites": prod[a]} for a in sorted(prod_ids - reg)
             if not _excused(a, "decorator_not_in_registry")]
        rules["P-02"] = result(FAIL if v else PASS, v)

    # P-03 — registry row backed by neither a writer nor the seed
    blocked = [x for x in (reg_err, seed_err) if x]
    if reg is None or seed is None:
        rules["P-03"] = result(NOT_CHECKABLE, [], "; ".join(blocked))
    else:
        v = [{"asset_id": a, "class": "registry_only"}
             for a in sorted(reg - prod_ids - seed)
             if not _excused(a, "registry_only")]
        rules["P-03"] = result(FAIL if v else PASS, v, None, {
            "registry_and_seed_not_decorator": sorted((reg & seed) - prod_ids)})

    # P-04 — seed id with no registry row
    if reg is None or seed is None:
        rules["P-04"] = result(NOT_CHECKABLE, [], "; ".join(blocked))
    else:
        v = [{"asset_id": a, "class": "seed_not_in_registry"}
             for a in sorted(seed - reg) if not _excused(a, "seed_not_in_registry")]
        rules["P-04"] = result(FAIL if v else PASS, v)

    # P-05 — one asset id registered by two production modules
    v = []
    for aid, sites in sorted(prod.items()):
        mods = sorted({s["file"] for s in sites})
        if len(mods) > 1 and not _excused(aid, "duplicate_registration"):
            v.append({"asset_id": aid, "class": "duplicate_registration",
                      "modules": mods})
    rules["P-05"] = result(FAIL if v else PASS, v)

    # P-06 — asset-id grammar in production code
    v = [{"asset_id": aid, "class": "non_asset_shaped_id_in_production",
          "sites": prod[aid]}
         for aid in sorted(prod_ids) if not census.ASSET_ID_RE.match(aid)
         and not _excused(aid, "non_asset_shaped_id_in_production")]
    rules["P-06"] = result(FAIL if v else PASS, v,
                           None, {"test_only_ids_ignored": sorted(test_only)})

    return {"_meta": {"writer_root": str(writer_root), "seed": str(seed_path),
                      "registry": reg_meta},
            "counts": {"registry": len(reg) if reg is not None else None,
                       "decorators_production": len(prod_ids),
                       "decorators_test_only": len(test_only),
                       "seed": len(seed) if seed is not None else None,
                       "unresolved_register_args": len(dec["unresolved"])},
            "unresolved_register_args": dec["unresolved"],
            "rules": rules}


def emit(rep: dict, max_rows: int) -> None:
    print("Asset source parity — registry × @register × seed")
    print("=" * 50)
    print(f"  counts: {json.dumps(rep['counts'])}")
    print(f"  UNRESOLVED @register args: {len(rep['unresolved_register_args'])}")
    for u in rep["unresolved_register_args"][:max_rows]:
        print(f"      - {json.dumps(u)}")
    for rid in sorted(rep["rules"]):
        r = rep["rules"][rid]
        badge = {PASS: "PASS ", FAIL: "FAIL ", NOT_CHECKABLE: "NULL "}[r["status"]]
        print(f"  [{badge}] {rid}  violations={r['violation_count']}")
        for row in r["violations"][:max_rows]:
            print(f"             - {json.dumps(row)}")
        if r["status"] == NOT_CHECKABLE:
            print(f"           not_checkable: {r['reason']}")
    print("  NOTE: not_checkable is NOT a pass — a diff leg that could not be read "
          "has not agreed with anything (CLAUDE.md §N.8).")


def self_test(max_rows: int) -> int:
    census = load_census()
    cases = sorted(p for p in FIXTURES.rglob("expect.json"))
    if not cases:
        print(f"GUARD ERROR — no fixture cases under {FIXTURES}")
        return 3
    failures = 0
    for exp_path in cases:
        case = exp_path.parent
        expect = json.loads(exp_path.read_text(encoding="utf-8"))
        allow_path = case / "allowlist.json"
        allow = load_allowlist(allow_path) if allow_path.exists() else {}
        rep = run(census, case / "writers", case / "seed.ts",
                  case / "registry.json", False, allow)
        bad = []
        for rid, want in sorted((expect.get("rules") or {}).items()):
            got = rep["rules"].get(rid)
            if got is None:
                bad.append(f"{rid}: not implemented")
                continue
            if isinstance(want, str):
                want = {"status": want}
            if got["status"] != want["status"]:
                bad.append(f"{rid}: expected {want['status']}, got {got['status']} "
                           f"({got['reason'] or ''})")
            if "violation_count" in want and got["violation_count"] != want["violation_count"]:
                bad.append(f"{rid}: expected {want['violation_count']} violations, "
                           f"got {got['violation_count']}")
        for k, want_n in (expect.get("counts") or {}).items():
            got_n = (rep["counts"].get(k) if k in rep["counts"]
                     else len(rep.get(k) or []))
            if got_n != want_n:
                bad.append(f"counts.{k}: expected {want_n}, got {got_n}")
        if "unresolved_register_args" in expect:
            n = len(rep["unresolved_register_args"])
            if n != expect["unresolved_register_args"]:
                bad.append(f"unresolved_register_args: expected "
                           f"{expect['unresolved_register_args']}, got {n}")
        rel = case.relative_to(FIXTURES)
        if bad:
            failures += 1
            print(f"  [FIXTURE FAIL] {rel}")
            for b in bad:
                print(f"      - {b}")
            emit(rep, max_rows)
        else:
            print(f"  [FIXTURE OK  ] {rel} — {len(expect.get('rules') or {})} "
                  f"expectations met")
    if failures:
        print(f"\nSELF-TEST FAILED: {failures} case(s) did not behave as declared.")
        return 3
    print("\nself-test OK — including every case built to make a rule FAIL.")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--live", action="store_true",
                    help="Read asset_registry from production (READ-ONLY).")
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY),
                    help="Registry snapshot JSON (default: the dated M0-T9 baseline).")
    ap.add_argument("--writer-root", default=str(DEFAULT_WRITER_ROOT))
    ap.add_argument("--seed", default=str(DEFAULT_SEED))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-rows", type=int, default=10)
    args = ap.parse_args(argv)
    try:
        if args.self_test:
            return self_test(args.max_rows)
        census = load_census()
        allow = load_allowlist(ALLOWLIST_PATH)
        rep = run(census, pathlib.Path(args.writer_root), pathlib.Path(args.seed),
                  pathlib.Path(args.registry), args.live, allow)
        if args.json:
            print(json.dumps(rep, indent=1, ensure_ascii=False))
        else:
            emit(rep, args.max_rows)
        return 1 if any(r["status"] == FAIL for r in rep["rules"].values()) else 0
    except GuardError as e:
        print(f"GUARD ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
