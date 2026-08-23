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

============================================================================
SNAPSHOT FRESHNESS — M0-T42, finding F-T40-1
============================================================================
THE DEFECT, IN ITS PUREST FORM. This guard's registry leg (S1) defaults to
`asset_catalogue_baseline_20260823.json` — a snapshot captured at 05:09:17Z — and CI
runs it with no `--registry` argument, so CI has always read that file. It shipped with
NO freshness detector of any kind, and it EXITS 0 on it. Measured at 08:44Z on
2026-08-23: `check_asset_source_parity.py` with no arguments printed six PASS rules and
returned 0, with no age, no date, and no `staleness` key anywhere in `--json`.

That is worse than the sibling defect M0-T42's predecessor fixed. The catalogue guard
(F-T36-2) at least FAILED loudly on its fossil, so a reader had a reason to look. This
one produced a **green** from data hours out of date — a status with no detector behind
the thing it claims, which is CLAUDE.md §N.8's defect class sitting inside the
mechanism built to catch it. The raw material was even present and simply never read:
`_meta.registry.read_at` was already being carried through into the report.

WHY `--registry <snapshot>` EXISTS — established before it was touched, and it is the
same finding M0-T40 established for `--baseline`. It is NOT a mistake and NOT a
shortcut. This guard's live registry leg calls `check_asset_catalogue_contract.read_live()`,
which reads `DATABASE_URL` out of `platform/.env.local` — a file that does not exist in
GitHub Actions, which has no route to production and no credential for one.
`.github/workflows/nirmana-m0-guards.yml` runs `--self-test` and the bare repo scan and
never `--live`. So "switch CI to `--live`" is not a fix here either; it is a job that
cannot run. The dated snapshot is a deliberate accommodation to that constraint. What
was broken is the accommodation shipping without the one thing that makes it honest.

THE FIX, AND WHOSE IT IS. Both detectors are M0-T40's, IMPORTED rather than
reimplemented — `migration_declared_registry_columns()` and `snapshot_staleness()` from
`check_asset_catalogue_contract.py`, which this module already imports for its live
read. A third copy of a freshness rule is a third thing to drift.

  1. AGE — `_meta.read_at` against `--max-age-hours` (default: the sibling's
     DEFAULT_MAX_SNAPSHOT_AGE_HOURS, so the two guards cannot disagree about what old
     means). A snapshot with no parseable `read_at` is stale by definition: an age that
     cannot be measured is not a young age. A registry leg that could not be READ AT
     ALL is stale for the same reason — the rules over it are `not_checkable`, and
     "not measured" must not exit 0 either.
  2. SCHEMA-BEHIND — every `ALTER TABLE asset_registry ADD COLUMN` in THIS checkout's
     `platform/migrations/*.sql`. A snapshot missing one provably predates a migration
     sitting in the same checkout. A proof of staleness, not an estimate. Measured for
     the shipped baseline: `declared − baseline` = the four migration-590 columns
     exactly; `declared − live(08:44Z)` = ∅.

REPORTED IN EVERY MODE, ENFORCED IN SNAPSHOT MODE. The rule results are still printed
in full, first, in every mode — suppressing them would hide data, which is the opposite
defect. Only the exit changes, and only for snapshot/baseline input. `--live` is
measured and reported but never failed on age, because it is a statement about
production by definition.

WHAT NEITHER DETECTOR CAN DO, stated rather than glossed: neither can prove a snapshot
is CURRENT — only that it is not. The output therefore never says "fresh", only "no
staleness detected". And the honest limit of the whole fix: a stale snapshot still
CANNOT DETECT a defect introduced after it was taken. Nothing can; a snapshot taken
before a change cannot contain it, and any mechanism claiming otherwise would be
fabricating. What changed is that the guard no longer lets a fossil be READ AS A
CURRENT VERDICT. That is the entire available honest fix from an environment with no
database.

NOT DONE BY THIS TASK: nothing under `.github/` was edited, no guard was wired
blocking, no rule was weakened, and the shared baseline snapshot was NOT regenerated
(see the M0-T42 report — regenerating it is an operator sequencing decision, not a
KĀRAKA's).

Exit codes
  0  no rule failed
  1  at least one rule failed
  2  bad usage / unreadable input
  3  guard-level error, a self-test expectation not met, OR the registry leg was
     provably stale and the guard refuses to certify a fossil as a verdict
"""
from __future__ import annotations

import argparse
import datetime as _dt
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
# The DEFAULT registry leg is the dated snapshot, and CI passes no --registry, so this
# IS what CI reads. It is a fossil the moment production moves; the freshness detectors
# below exist because it shipped without them (F-T40-1).
DEFAULT_REGISTRY = HERE / "asset_catalogue_baseline_20260823.json"

PASS, FAIL, NOT_CHECKABLE = "pass", "fail", "not_checkable"


class GuardError(Exception):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# The sibling guard, imported once — for the live read AND for M0-T40's freshness
# detectors. Borrowed, never re-implemented: the same reason this module borrows
# census.py's parser rather than writing a second one. A third copy of a rule is a
# third thing that can drift out of agreement with the other two.
# Module scope in that file issues no query and imports no psycopg (psycopg is
# imported inside read_live only), so this import is DB-free.
# ─────────────────────────────────────────────────────────────────────────────
_CONTRACT_GUARD = None


def contract_guard():
    global _CONTRACT_GUARD                                   # noqa: PLW0603
    if _CONTRACT_GUARD is None:
        if str(HERE) not in sys.path:
            sys.path.insert(0, str(HERE))
        import check_asset_catalogue_contract as cc          # noqa: PLC0415
        for attr in ("snapshot_staleness", "migration_declared_registry_columns",
                     "emit_staleness", "DEFAULT_MAX_SNAPSHOT_AGE_HOURS", "read_live"):
            if not hasattr(cc, attr):
                raise GuardError(
                    f"check_asset_catalogue_contract no longer exposes `{attr}` — the "
                    f"freshness detector this guard borrows (M0-T40) has moved; "
                    f"reconcile before trusting either guard's exit code")
        _CONTRACT_GUARD = cc
    return _CONTRACT_GUARD


def default_max_age_hours() -> float:
    return float(contract_guard().DEFAULT_MAX_SNAPSHOT_AGE_HOURS)


def measure_staleness(raw: dict | None, live: bool, max_age_hours: float,
                      read_error: str | None = None,
                      now: _dt.datetime | None = None) -> dict:
    """M0-T40's detectors, applied to THIS guard's registry leg.

    `raw is None` means the registry leg could not be read at all. That is stale for
    exactly the reason a missing `read_at` is: the age of the data these rules judge is
    unmeasurable, and an unmeasurable age is not a young age. Its rules go
    `not_checkable`, and a report of "not measured" must not exit 0 either.
    """
    cc = contract_guard()
    st = cc.snapshot_staleness(raw if raw is not None else {},
                               "live" if live else "snapshot", max_age_hours, now=now)
    if raw is None:
        st["registry_unreadable"] = read_error or "registry leg could not be read"
        st["reasons"] = [
            f"the registry leg could not be read at all ({st['registry_unreadable']}), "
            f"so the age of the data these rules judge is unmeasurable — an age that "
            f"cannot be measured is not a young age"
        ] + [r for r in st["reasons"] if "carries no `_meta.read_at`" not in r]
        st["stale"] = True
    return st


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


def read_registry(path: pathlib.Path | None, live: bool
                  ) -> tuple[set[str] | None, str | None, dict, dict | None]:
    """Returns (asset_ids, error, meta, raw_document).

    The RAW document is returned as well, and not merely its `_meta`, because the
    freshness detectors need `registry_columns` — the schema-behind proof reads it.
    Before M0-T42 this function threw the rest of the document away, which is part of
    why the age data was sitting in the report unread.
    """
    if live:
        raw = contract_guard().read_live()
        return {a["asset_id"] for a in raw["assets"]}, None, raw.get("_meta", {}), raw
    if path is None or not path.exists():
        return None, f"registry snapshot not found: {path}", {}, None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ({a["asset_id"] for a in raw.get("assets", [])}, None,
            raw.get("_meta", {}) | {"snapshot_file": path.name}, raw)


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


def run(census, writer_root, seed_path, registry_path, live, allow,
        max_age_hours: float | None = None, now=None) -> dict:
    dec = scan_decorators(census, writer_root)
    seed, seed_err = scan_seed(census, seed_path)
    reg, reg_err, reg_meta, reg_raw = read_registry(registry_path, live)
    staleness = measure_staleness(
        reg_raw, live,
        default_max_age_hours() if max_age_hours is None else max_age_hours,
        read_error=reg_err, now=now)
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
            "staleness": staleness,
            "counts": {"registry": len(reg) if reg is not None else None,
                       "decorators_production": len(prod_ids),
                       "decorators_test_only": len(test_only),
                       "seed": len(seed) if seed is not None else None,
                       "unresolved_register_args": len(dec["unresolved"])},
            "unresolved_register_args": dec["unresolved"],
            "rules": rules}


def exit_code(rep: dict) -> int:
    """THE FOSSIL GATE (F-T40-1). The single place the exit is decided.

    Factored out so the self-test can drive it directly: a mutation that deletes the
    staleness branch has to survive a probe that asserts on this function's output, not
    merely on the detector's. A detector nothing consults is the same unearned signal
    one layer along (§N.8).

    Order matters and is deliberate. Staleness outranks the rule verdicts because it
    says the rule verdicts are about the wrong data — a PASS over a fossil is not a
    weaker pass, it is not a pass at all. The rule results are still PRINTED in full by
    the caller before this is consulted; only the exit changes.
    """
    st = rep.get("staleness") or {}
    if st.get("stale") and st.get("enforced"):
        return 3
    return 1 if any(r["status"] == FAIL for r in rep["rules"].values()) else 0


def emit(rep: dict, max_rows: int) -> None:
    print("Asset source parity — registry × @register × seed")
    print("=" * 50)
    if rep.get("staleness"):
        # Always, in every mode. A silent freshness check is not a check.
        contract_guard().emit_staleness(rep["staleness"])
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


def staleness_wiring_probe() -> int:
    """Prove THIS guard consults the freshness detector, and prove it CAN fail.

    `snapshot_staleness_probe()` (borrowed below) proves the DETECTOR is real. It does
    not prove this guard asks it anything. A detector that exists and is never consulted
    is the same unearned signal one layer along — the exact shape of D-24 part 1's
    `has_substeps` finding — so this probe drives `exit_code()`, the one place the
    verdict is decided, with reports built to make each branch fire.
    """
    print("\n  Freshness-WIRING probe (the detector is consulted by THIS guard's exit "
          "path, not merely defined near it):")
    bad = 0

    def rep(stale, enforced, failing):
        return {"staleness": {"stale": stale, "enforced": enforced},
                "rules": {"P-01": {"status": FAIL if failing else PASS}}}

    def check(label, r, want):
        nonlocal bad
        got = exit_code(r)
        ok = got == want
        print(f"      [{'OK  ' if ok else 'BAD '}] {label}: exit={got}")
        if not ok:
            bad += 1
            print(f"           expected exit {want}")

    check("fresh + all rules pass ⇒ 0", rep(False, True, False), 0)
    check("fresh + a rule fails ⇒ 1", rep(False, True, True), 1)
    check("STALE + all rules pass ⇒ 3 (a green over a fossil is not a green)",
          rep(True, True, False), 3)
    check("STALE + a rule fails ⇒ 3 (refusing to certify outranks the verdict)",
          rep(True, True, True), 3)
    check("live is measured but never enforced on age ⇒ 1 on a real failure",
          rep(True, False, True), 1)
    check("live, stale-but-unenforced, nothing failing ⇒ 0",
          rep(True, False, False), 0)

    # End to end through run(): the report must CARRY the key, or `exit_code` above is
    # reasoning about a field nothing populates.
    census = load_census()
    case = FIXTURES / "pass" / "clean"
    now = _dt.datetime.now(_dt.timezone.utc)
    declared, _files = contract_guard().migration_declared_registry_columns()
    import tempfile                                          # noqa: PLC0415
    with tempfile.TemporaryDirectory() as td:
        fresh_doc = {"_meta": {"read_at": (now - _dt.timedelta(minutes=5)).isoformat()},
                     "registry_columns": sorted(declared) + ["asset_id"],
                     "assets": [{"asset_id": "bg_one"}, {"asset_id": "bg_two"}]}
        old_doc = dict(fresh_doc,
                       _meta={"read_at": (now - _dt.timedelta(hours=100)).isoformat()})
        # THE CASE THAT MATTERS MOST, and the one this probe originally MISSED — caught
        # by mutation M4, which stripped the schema-behind proof out of run()'s output
        # and survived every other check here. The shipped baseline is only ~3.7h old,
        # comfortably inside the 24h age threshold, so AGE NEVER CATCHES IT: the
        # schema-behind proof is the ONLY detector that fires on the real fossil. A
        # detector nothing tests is an unearned signal (§N.8), so it is tested here:
        # young enough to pass the age check, missing a column a migration in this
        # checkout adds.
        young_but_behind = {
            "_meta": {"read_at": (now - _dt.timedelta(minutes=5)).isoformat()},
            "registry_columns": [c for c in (sorted(declared) + ["asset_id"])
                                 if c != sorted(declared)[0]],
            "assets": [{"asset_id": "bg_one"}, {"asset_id": "bg_two"}]}
        for label, doc, want_stale, want_behind in (
                ("fresh", fresh_doc, False, []),
                ("100h old", old_doc, True, []),
                ("5-MINUTES-OLD but schema-behind", young_but_behind, True,
                 [sorted(declared)[0]])):
            p = pathlib.Path(td) / f"{label.replace(' ', '_')}.json"
            p.write_text(json.dumps(doc), encoding="utf-8")
            r = run(census, case / "writers", case / "seed.ts", p, False, {}, now=now)
            st = r.get("staleness")
            ok = (st is not None and st["stale"] is want_stale
                  and st["schema_behind_columns"] == want_behind
                  and exit_code(r) == (3 if want_stale else 0))
            print(f"      [{'OK  ' if ok else 'BAD '}] run() over a {label} registry "
                  f"attaches staleness: {None if st is None else st['stale']} "
                  f"schema_behind={None if st is None else st['schema_behind_columns']} "
                  f"(exit {exit_code(r)})")
            if not ok:
                bad += 1
                print(f"           expected stale={want_stale} "
                      f"schema_behind={want_behind} "
                      f"exit={3 if want_stale else 0}")
        # An unreadable registry leg. The verdict (stale ⇒ exit 3) is NOT the whole
        # claim, and asserting only the verdict lets a mutation that deletes this
        # branch survive — measured, mutation M5. The generic detector reaches `stale`
        # anyway via the absent `read_at`, but it does so with the WRONG REASON: it
        # reports a snapshot that carries no timestamp, when what actually happened is
        # that there was no snapshot. Reporting the correct cause is this branch's
        # entire contribution, so that is what is asserted.
        missing = pathlib.Path(td) / "does_not_exist.json"
        r = run(census, case / "writers", case / "seed.ts", missing, False, {}, now=now)
        st = r["staleness"]
        ok = (st["stale"] and exit_code(r) == 3
              and st.get("registry_unreadable")
              and any("could not be read at all" in x for x in st["reasons"])
              and r["rules"]["P-02"]["status"] == NOT_CHECKABLE)
        print(f"      [{'OK  ' if ok else 'BAD '}] an UNREADABLE registry leg is stale "
              f"too ⇒ exit {exit_code(r)}; P-02={r['rules']['P-02']['status']} "
              f"(not_checkable must not exit 0 either), and says WHY: "
              f"{st.get('registry_unreadable') or '<no cause reported>'}")
        if not ok:
            bad += 1
            print(f"           expected stale + exit 3 + a `registry_unreadable` cause "
                  f"+ P-02 not_checkable; reasons={st['reasons']}")
    return bad


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
        # Fixture registries carry no `_meta.read_at` and only a token
        # `registry_columns`, so both are correctly measured STALE. Declared rather
        # than exempted: a mutation that stops run() attaching staleness fails here.
        for k, want_v in (expect.get("staleness") or {}).items():
            got_v = (rep.get("staleness") or {}).get(k, "<absent>")
            if got_v != want_v:
                bad.append(f"staleness.{k}: expected {want_v}, got {got_v}")
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

    # The freshness detectors (F-T40-1). Two probes, deliberately separate:
    #   * the BORROWED detector's own probe, run here rather than re-implemented, so
    #     both guards are held to one fixture — and so this guard's CI step also states
    #     the shipped baseline's staleness out loud on every run;
    #   * this guard's WIRING, which the borrowed probe says nothing about.
    probe_bad = contract_guard().snapshot_staleness_probe() + staleness_wiring_probe()
    if probe_bad:
        print(f"\nSELF-TEST FAILED: {probe_bad} freshness expectation(s) not met.")
        return 3

    print("\nself-test OK — including every case built to make a rule FAIL, and every "
          "freshness case built to make the fossil gate fire.")
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
    ap.add_argument("--max-age-hours", type=float, default=None,
                    help="Maximum age of the --registry snapshot before the guard "
                         "refuses to report its rules as a verdict (default: the "
                         "sibling catalogue guard's DEFAULT_MAX_SNAPSHOT_AGE_HOURS, so "
                         "the two cannot disagree about what old means). Tightening it "
                         "is always allowed; loosening it does not silence the "
                         "schema-behind detector, which is a proof and not a threshold.")
    args = ap.parse_args(argv)
    try:
        if args.self_test:
            return self_test(args.max_rows)
        census = load_census()
        allow = load_allowlist(ALLOWLIST_PATH)
        rep = run(census, pathlib.Path(args.writer_root), pathlib.Path(args.seed),
                  pathlib.Path(args.registry), args.live, allow,
                  max_age_hours=args.max_age_hours)
        if args.json:
            print(json.dumps(rep, indent=1, ensure_ascii=False))
        else:
            emit(rep, args.max_rows)

        # THE FOSSIL GATE (F-T40-1). The rule results are printed IN FULL above in
        # every mode — suppressing them would hide data, which is the opposite defect.
        # Only the exit changes, and only for snapshot input: `--live` measures
        # production by definition and is never failed on age.
        st = rep["staleness"]
        if st["stale"] and st["enforced"]:
            # The message below says "above", so make that true: stdout is block-
            # buffered under a pipe while stderr is not, and without this flush the
            # refusal prints before the report it refers to.
            sys.stdout.flush()
            print("", file=sys.stderr)
            print("GUARD ERROR — REGISTRY SNAPSHOT STALE: the parity rules above were "
                  "run against a registry leg that is provably not the current "
                  "catalogue.", file=sys.stderr)
            for r in st["reasons"]:
                print(f"  - {r}", file=sys.stderr)
            print("  Before this check existed, this guard EXITED 0 on that input — a "
                  "green produced by a fossil. It still cannot DETECT a divergence "
                  "introduced after the snapshot was taken; nothing can, and claiming "
                  "otherwise would be fabrication. What it refuses to do is exit as "
                  "though a fossil were a current verdict. Regenerate the snapshot "
                  "from an environment that HAS database access — "
                  "`check_asset_catalogue_contract.py --live --snapshot-out "
                  f"{DEFAULT_REGISTRY.name}` — and commit it; CI has no credential and "
                  "cannot do this for itself.", file=sys.stderr)
        return exit_code(rep)
    except GuardError as e:
        print(f"GUARD ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
