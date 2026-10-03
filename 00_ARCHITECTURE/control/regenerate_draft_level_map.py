#!/usr/bin/env python3
"""regenerate_draft_level_map.py -- Suvarna E6.3 (SS ruling N-97 item 6): the DRAFT, pre-J1 LEVEL_MAP.json and FAMILY_ASSETS.json.

"DRAFT FAMILY_ASSETS and a pre-J1 LEVEL_MAP NOW, marked draft. The wave plan and the L0 wave prep need levels early.
Freeze at J1." Both files are produced by generate_level_map.py (never hand-edited) from three committed inputs:

  registry_input_draft.json  the registry rows [{asset_id, layer, depends_on, active}] the generator reads (--registry-json)
  family_lists_input.json    the six family lists (strategist-owned; unchanged by this tool)
  stamp                      a `_stamp` note carried into BOTH outputs (see make_stamp for every field)

WHAT THE STAMP BINDS. `registry_revision` / `registry_fingerprint` are asset_census.REGISTRY_REVISION and registry_fingerprint():
they hash the CENSUS CRITERIA registry, NOT the asset_registry dependency graph. A stale census stamp does not say the DAG moved
and a current one does not say it did not. The DAG is bound by `registry_input_sha256` (the committed input rows) and
`dag_sha256` (the active edges); whether those equal the LIVE registry is what the J1 freeze proves (`--freeze`).

Where the DAG comes from, OFFLINE (no database, no credential; B.10: nothing is invented):

  * the 127 ACTIVE rows' depends_on = the repo's frozen reconstruction of the live active registry BEFORE migration 1210
    (platform/python-sidecar/tests/fixtures/registry_depends_on_pre_1210.json; its _provenance: md5 of sorted depends_on of
    the 127 active rows matched the live registry at the E6 review) PLUS the 12 edges migration 1210 inserts (parsed from
    platform/migrations/1210_asset_registry_direct_edges.sql). The exact set of migrations whose SQL mentions depends_on, in BOTH
    migration directories the runner applies, is pinned in registry_depends_on_migrations.json and guarded by the tests.
  * cross-checked, in the build session, against the E6 census of origin/main adb0db29d (a read-only live measurement kept
    OUTSIDE this repo, /Users/Dev/suvarna-evidence/census_fresh/adb0db2; the numbers are recorded here so they do not rest on
    that path): 127 assets (L0..L5 populations 40/19/23/21/9/15); for ALL 127 the census's Build.dag "N declared edge(s)" equals
    len(depends_on) here, and its blocking_radius direct and transitive dependent counts equal the ones computed on this graph;
    census registry_revision 16, fingerprint 8b88e7b26f32fdf8f665533b96357c8c332fb142a7166a6468a0f64ec51cb97c. The 2026-09-29
    plan measurement (27 levels, 24/11/4/1 L0 by level, W0 = 65, family positions 1,1,5,12,13) is reproduced exactly.
  * layer = the seed's layer (equal to the census layer for all 127). The seed's depends_on is NOT used: it is bootstrap-only
    and differs from the live registry on exactly five assets (pinned in a test).
  * inactive rows are present only so the family input's `_notes.inactive` allowance can be checked. ka_gochara_sweep (seed
    inactive, live inactive) and ka_gochara_v3_century_materialize (the seed says active; the live registry holds it inactive:
    census L3 `population_excluded_inactive`) are live rows. ka_gochara_v4_41_candidate is a SEED-ONLY inactive row: the census
    lists it under `phantom_registered` and the live L3 registry total (23) does not include it. It is NOT a live registry row.
    Inactive rows never enter the level map.

    python3 regenerate_draft_level_map.py --frozen-at 2026-10-03T00:00:00+00:00         # rewrite the three files (DRAFT)
    python3 regenerate_draft_level_map.py --check                                         # exit 1 if a committed file differs
    python3 regenerate_draft_level_map.py --check --strict                                # ...and if a DRAFT stamp is stale
    python3 regenerate_draft_level_map.py --check --pre-freeze                            # the J1 gate: fails on any DRAFT or stale stamp
    python3 regenerate_draft_level_map.py --freeze --registry-export live.json --frozen-at <ISO>   # the J1 freeze
    python3 regenerate_draft_level_map.py --write-migration-pin                           # refresh registry_depends_on_migrations.json

Staleness. A file whose `_stamp.status` is DRAFT records the census revision and fingerprint it was generated at; when
asset_census moves on, the draft is STALE but still a valid draft: `--check` prints a `STALE (draft)` line and exits 0 (the
other guards stay hard: the committed files must equal a regeneration made AT THE RECORDED stamp from the committed registry
input, ALL THREE files). `--strict` makes a stale draft exit 1. A stamp whose status is not DRAFT fails on staleness always.
A file can be RELABELLED (status edited), so a relabelled stale file is only warned about by `--check`: `--check --pre-freeze`
is the gate, and it fails on every DRAFT stamp and every stale census stamp.

Overwriting. A write refuses (exit 2) when an existing LEVEL_MAP.json or FAMILY_ASSETS.json is not an unmodified-format DRAFT
(no `_stamp`, a status other than DRAFT, or unreadable) unless `--force`. The three files are written all-or-nothing: every file is
staged first, then replaced, and a failure part-way restores the originals.

The J1 freeze (`--freeze`). Needs `--registry-export`: a JSON list of {asset_id, layer, depends_on, active} rows exported
read-only from the LIVE asset_registry by whoever holds the reader login. The active ids and active edges of the export must equal
those of the committed registry_input_draft.json, else the differences are printed and nothing is written (exit 2): re-derive
the draft from the export, regenerate, and review the diff first. On a match the export becomes the registry input and the
three files are written with status FROZEN, a non-draft version (default 1.0) and a stamp at the CURRENT census pin.

Exit: 0 ok · 1 --check found a difference, or staleness (always when not DRAFT, with --strict for a DRAFT), or --pre-freeze failed
· 2 refused (LevelMapError) · 5 script error.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

REGISTRY_INPUT_FILE = "registry_input_draft.json"
FAMILY_INPUT_FILE = "family_lists_input.json"
MIGRATION_PIN_FILE = "registry_depends_on_migrations.json"
DRAFT_VERSION = "0.2-draft"
FROZEN_VERSION = "1.0"
STATUSES = ("DRAFT", "FROZEN")

FIXTURE = REPO / "platform" / "python-sidecar" / "tests" / "fixtures" / "registry_depends_on_pre_1210.json"
MIGRATION_1210 = REPO / "platform" / "migrations" / "1210_asset_registry_direct_edges.sql"
SEED = REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"
CENSUS = REPO / "platform" / "scripts" / "governance" / "asset_census.py"
GENERATOR = HERE / "generate_level_map.py"
# The two directories platform/scripts/migrate.ts applies (it reads platform/migrations/*.sql and platform/supabase/migrations/*.sql).
MIGRATION_DIRS = ("platform/migrations", "platform/supabase/migrations")

# Registry rows the seed calls active but the live registry holds inactive (evidence: E6 census at origin/main adb0db29d,
# census_L3.json population_excluded_inactive: is_active False, catalog_status CURRENT).
LIVE_INACTIVE_OVERRIDES = ("ka_gochara_v3_century_materialize",)
# Seed-only inactive rows: census L3 `phantom_registered`, not in the live registry total. Present so the family input's
# `_notes.inactive` allowance verifies; never in the level map. (ka_gochara_v5: Pravaha C41's inert A5.3 skeleton, seeded
# by migration 1243, activated only transiently by the steward dispatch.)
SEED_ONLY_INACTIVE = ("ka_gochara_v4_41_candidate", "ka_gochara_v5")

DRAFT_BASIS = (
    "DRAFT. DAG = the 127 active registry rows' depends_on: the repo's frozen live-registry reconstruction before migration "
    "1210 (platform/python-sidecar/tests/fixtures/registry_depends_on_pre_1210.json) plus migration 1210's 12 edges; verified "
    "offline against the E6 census of origin/main adb0db29d (Build.dag declared-edge count and blocking_radius direct and "
    "transitive equal for all 127 assets). Not a live export: the strategist freezes the final files at J1 from a live "
    "export.")
FROZEN_BASIS = (
    "FROZEN at J1 from a live asset_registry export whose active ids and edges equal the committed registry input (regenerate_"
    "draft_level_map.py --freeze).")
STAMP_SCOPE = (
    "registry_revision and registry_fingerprint are asset_census.REGISTRY_REVISION and registry_fingerprint(): they hash the "
    "CENSUS CRITERIA registry, not the asset_registry dependency graph. They say nothing about whether the DAG moved; the DAG "
    "is bound by registry_input_sha256 and dag_sha256.")


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_level_map_draft", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load_generator()
_replace = os.replace            # every replace of the all-or-nothing writer goes through here (a test injects a failure)


# ───────────────────────────── the registry input ─────────────────────────────

def migration_1210_edges(text: str | None = None) -> list[tuple[str, str]]:
    sql = MIGRATION_1210.read_text(encoding="utf-8") if text is None else text
    m = re.search(r"INSERT INTO _m1210_edges \(asset_id, dep\) VALUES\s*(.*?);", sql, re.S)
    if not m:
        raise G.LevelMapError("edge VALUES block not found in migration 1210")
    edges = re.findall(r"\(\s*'([a-z0-9_]+)'\s*,\s*'([a-z0-9_]+)'\s*\)", m.group(1))
    if not edges:
        raise G.LevelMapError("migration 1210 carries no edge")
    return edges


def derive_registry_rows(*, fixture_edges=None, extra_edges=None, seed_rows=None) -> list[dict]:
    """The registry input rows, sorted by asset_id: the 127 active rows (pre-1210 graph + 1210's edges, seed layer) and the
    inactive rows the family input's `_notes.inactive` needs. Every input is injectable for the mutation tests."""
    if fixture_edges is None:
        fixture_edges = json.loads(FIXTURE.read_text(encoding="utf-8"))["edges"]
    if extra_edges is None:
        extra_edges = migration_1210_edges()
    if seed_rows is None:
        seed_rows = G.parse_seed_text(SEED.read_text(encoding="utf-8"))
    seed = {r["asset_id"]: r for r in seed_rows}
    deps = {a: set(d) for a, d in fixture_edges.items()}
    for a, d in extra_edges:
        if a not in deps:
            raise G.LevelMapError(f"migration 1210 edge {a} -> {d}: {a} is not an active row of the pre-1210 graph")
        deps[a].add(d)
    rows = []
    for a in sorted(deps):
        if a not in seed:
            raise G.LevelMapError(f"active asset {a} is not in the seed, so its layer is unknown")
        rows.append(dict(asset_id=a, layer=seed[a]["layer"], depends_on=sorted(deps[a]), active=True))
    inactive = sorted({a for a, r in seed.items() if not r["active"]} | set(LIVE_INACTIVE_OVERRIDES))
    for a in inactive:
        if a in deps:
            raise G.LevelMapError(f"{a} is both active in the graph and inactive in the seed/overrides")
        if a not in seed:
            raise G.LevelMapError(f"inactive asset {a} is not in the seed")
        rows.append(dict(asset_id=a, layer=seed[a]["layer"], depends_on=sorted(seed[a]["depends_on"]), active=False))
    return sorted(G.validate_registry(rows), key=lambda r: r["asset_id"])


def dumps(doc) -> str:
    """The exact serialisation of generate_level_map._write_atomic."""
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def registry_input_text(rows: list[dict]) -> str:
    return dumps([dict(asset_id=r["asset_id"], layer=r["layer"], depends_on=list(r["depends_on"]), active=r["active"])
                  for r in sorted(rows, key=lambda r: r["asset_id"])])


def dag_sha256(rows: list[dict]) -> str:
    """sha256 of the canonical active edge set {asset_id: sorted depends_on} (the DAG the levels are computed from)."""
    edges = {r["asset_id"]: sorted(r["depends_on"]) for r in rows if r["active"]}
    return hashlib.sha256(json.dumps(edges, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


# ───────────────────────────── the stamp and the three files ─────────────────────────────

def make_stamp(*, registry_revision: int, registry_fingerprint: str, registry_input_sha256: str, dag_sha256: str,
               status: str = "DRAFT") -> dict:
    if status not in STATUSES:
        raise G.LevelMapError(f"status must be one of {list(STATUSES)}, got {status!r}")
    draft = status == "DRAFT"
    return {"_stamp": {
        "status": status,
        "freeze": ("J1: the strategist freezes the final lists and the level map at J1 (SS ruling N-97 item 6)" if draft
                   else "FROZEN at J1 (SS ruling N-97 item 6)"),
        "registry_revision": registry_revision,
        "registry_fingerprint": registry_fingerprint,
        "registry_stamp_scope": STAMP_SCOPE,
        "registry_input": f"00_ARCHITECTURE/control/{REGISTRY_INPUT_FILE}",
        "registry_input_sha256": registry_input_sha256,
        "dag_sha256": dag_sha256,
        "registry_basis": DRAFT_BASIS if draft else FROZEN_BASIS,
        "regenerate": ("python3 00_ARCHITECTURE/control/regenerate_draft_level_map.py --frozen-at <ISO-8601 with timezone>" if draft
                       else "python3 00_ARCHITECTURE/control/regenerate_draft_level_map.py --freeze --registry-export <live export json> "
                            "--frozen-at <ISO-8601 with timezone> --force"),
    }}


def render(*, frozen_at: str, registry_revision: int, registry_fingerprint: str, version: str | None = None,
           rows: list[dict] | None = None, family_input=None, status: str = "DRAFT") -> dict[str, str]:
    """{file name: exact text} for registry_input_draft.json, LEVEL_MAP.json and FAMILY_ASSETS.json. Pure: no clock, no I/O
    beyond reading the committed inputs when they are not injected. A DRAFT needs a `-draft` version, a freeze must not have one."""
    if status not in STATUSES:
        raise G.LevelMapError(f"status must be one of {list(STATUSES)}, got {status!r}")
    version = (DRAFT_VERSION if status == "DRAFT" else FROZEN_VERSION) if version is None else version
    if str(version).endswith("-draft") != (status == "DRAFT"):
        raise G.LevelMapError(f"version {version!r} does not match status {status}: a DRAFT version ends in -draft, a freeze's must not")
    rows = derive_registry_rows() if rows is None else rows
    reg_text = registry_input_text(rows)
    stamp = make_stamp(registry_revision=registry_revision, registry_fingerprint=registry_fingerprint,
                       registry_input_sha256=hashlib.sha256(reg_text.encode("utf-8")).hexdigest(),
                       dag_sha256=dag_sha256(rows), status=status)
    if family_input is None:
        family_input = G.load_family_input(HERE / FAMILY_INPUT_FILE)
    lm = G.build_level_map(rows, version=version, frozen_at=frozen_at, registry_revision=registry_revision, notes=stamp)
    fa = G.build_family_assets(family_input, rows, version=version, frozen_at=frozen_at,
                               registry_revision=registry_revision, notes=stamp)
    return {REGISTRY_INPUT_FILE: reg_text, G.LEVEL_MAP_FILE: dumps(lm), G.FAMILY_ASSETS_FILE: dumps(fa)}


def census_pin() -> tuple[int, str]:
    """(REGISTRY_REVISION, registry_fingerprint()) of the asset_census.py in this checkout (imported: it needs no database)."""
    spec = importlib.util.spec_from_file_location("asset_census_for_draft_stamp", CENSUS)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.REGISTRY_REVISION, mod.registry_fingerprint()


def staleness(doc: dict, pin: tuple[int, str]) -> list[str]:
    """How a document's recorded CENSUS revision / fingerprint differ from the current census pin (empty = current). The top-level
    registry_revision and the stamp's are both compared. Says nothing about the DAG."""
    stamp = doc.get("_stamp") if isinstance(doc.get("_stamp"), dict) else {}
    out = []
    for what, have, want in (("registry_revision", doc.get("registry_revision"), pin[0]),
                             ("_stamp.registry_revision", stamp.get("registry_revision"), pin[0]),
                             ("_stamp.registry_fingerprint", stamp.get("registry_fingerprint"), pin[1])):
        if have != want:
            out.append(f"{what} is {have!r}, the census is at {want!r}")
    return out


# ───────────────────────────── overwrite protection and the all-or-nothing writer ─────────────────────────────

def existing_set_refusals(out: Path) -> list[str]:
    """Reasons the files already in `out` may not be overwritten without --force: LEVEL_MAP.json / FAMILY_ASSETS.json that are
    unreadable, carry no `_stamp`, or carry a status other than DRAFT."""
    why = []
    for n in (G.LEVEL_MAP_FILE, G.FAMILY_ASSETS_FILE):
        p = out / n
        if not p.exists():
            continue
        try:
            doc = G.strict_json_loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            why.append(f"{n} is unreadable ({type(e).__name__})")
            continue
        stamp = doc.get("_stamp") if isinstance(doc, dict) else None
        if not isinstance(stamp, dict):
            why.append(f"{n} carries no _stamp (not a file this tool wrote)")
        elif stamp.get("status") != "DRAFT":
            why.append(f"{n} is {stamp.get('status')!r}, not DRAFT")
    return why


def write_set_atomic(out: Path, files: dict[str, str]) -> None:
    """Write every file or none: stage all temp files, replace one by one, and on any failure restore the originals and remove
    the stage. Raises the original error."""
    staged: dict[str, str] = {}
    originals: dict[str, bytes | None] = {}
    replaced: list[str] = []
    try:
        for n, text in files.items():
            fd, tmp = tempfile.mkstemp(dir=str(out), prefix="." + n + ".")
            staged[n] = tmp
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
        for n in files:
            originals[n] = (out / n).read_bytes() if (out / n).exists() else None
        for n in files:
            _replace(staged[n], out / n)
            replaced.append(n)
            staged.pop(n)
    except BaseException:
        for n in reversed(replaced):
            if originals[n] is None:
                (out / n).unlink(missing_ok=True)
            else:
                fd, tmp = tempfile.mkstemp(dir=str(out), prefix="." + n + ".restore.")
                with os.fdopen(fd, "wb") as f:
                    f.write(originals[n])
                _replace(tmp, out / n)
        for tmp in staged.values():
            if os.path.exists(tmp):
                os.unlink(tmp)
        raise


# ───────────────────────────── the migration pin ─────────────────────────────

def _sql_code(text: str) -> str:
    """The SQL with -- and /* */ comments removed (string and dollar-quoted bodies are KEPT: over-reporting is the safe side)."""
    return re.sub(r"/\*.*?\*/", "", re.sub(r"--[^\n]*", "", text), flags=re.S)


def depends_on_migrations(texts: dict[str, dict[str, str]] | None = None) -> dict[str, list[str]]:
    """{migration dir: sorted file names} whose SQL, comments stripped, mentions depends_on (any case). BOTH directories the
    runner applies. `texts` ({dir: {name: sql}}) is injectable for the mutation tests."""
    if texts is None:
        texts = {}
        for d in MIGRATION_DIRS:
            root = REPO / d
            if not root.is_dir():
                raise G.LevelMapError(f"migration directory {d} not found")
            texts[d] = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in root.glob("*.sql")}
    return {d: sorted(n for n, t in files.items() if re.search(r"\bdepends_on\b", _sql_code(t), re.I))
            for d, files in sorted(texts.items())}


def migration_pin_text(found: dict[str, list[str]]) -> str:
    return dumps({"_note": ("The exact set of migrations whose SQL (comments stripped) mentions depends_on, per migration directory "
                            "the runner applies. A new or removed entry means the registry DAG may have moved: update "
                            "registry_input_draft.json and the generated files first, then refresh this pin with "
                            "`regenerate_draft_level_map.py --write-migration-pin`."),
                  "migrations": found})


# ───────────────────────────── the J1 freeze ─────────────────────────────

def export_diff(draft_rows: list[dict], export_rows: list[dict]) -> list[str]:
    """Differences between the ACTIVE ids and ACTIVE edges of two registry row lists (empty = equal)."""
    d = {r["asset_id"]: set(r["depends_on"]) for r in draft_rows if r["active"]}
    e = {r["asset_id"]: set(r["depends_on"]) for r in export_rows if r["active"]}
    out = [f"active asset only in the export: {a}" for a in sorted(set(e) - set(d))]
    out += [f"active asset only in the draft input: {a}" for a in sorted(set(d) - set(e))]
    for a in sorted(set(d) & set(e)):
        out += [f"{a}: edge only in the export: {x}" for x in sorted(e[a] - d[a])]
        out += [f"{a}: edge only in the draft input: {x}" for x in sorted(d[a] - e[a])]
    return out


# ───────────────────────────── CLI ─────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Regenerate / check / freeze the DRAFT LEVEL_MAP.json and FAMILY_ASSETS.json (E6.3).")
    ap.add_argument("--frozen-at", default=None, help="ISO-8601 with timezone; --check reads it from the committed LEVEL_MAP.json")
    ap.add_argument("--version", default=None, help=f"default {DRAFT_VERSION} (draft) or {FROZEN_VERSION} (--freeze)")
    ap.add_argument("--out-dir", default=str(HERE))
    ap.add_argument("--check", action="store_true", help="compare ALL THREE files with a regeneration at the recorded stamp, write "
                    "nothing; a stale DRAFT stamp prints 'STALE (draft)' and still exits 0 (a stale non-DRAFT stamp exits 1)")
    ap.add_argument("--strict", action="store_true", help="with --check: a stale DRAFT stamp exits 1 too")
    ap.add_argument("--pre-freeze", action="store_true", help="with --check: the J1 gate; fails on any DRAFT stamp and any stale census stamp")
    ap.add_argument("--freeze", action="store_true", help="write the FROZEN set from --registry-export (active ids/edges must equal the draft input)")
    ap.add_argument("--registry-export", default=None, help="live asset_registry export: JSON list of {asset_id, layer, depends_on, active}")
    ap.add_argument("--force", action="store_true", help="overwrite files that are not an unmodified DRAFT (a frozen set)")
    ap.add_argument("--write-migration-pin", action="store_true", help=f"rewrite {MIGRATION_PIN_FILE} from the migration directories")
    a = ap.parse_args(argv)
    out = Path(a.out_dir)
    modes = [a.check, a.freeze, a.write_migration_pin]
    if sum(bool(m) for m in modes) > 1:
        print("REFUSED: --check, --freeze and --write-migration-pin are separate modes", file=sys.stderr)
        return 2
    if (a.strict or a.pre_freeze) and not a.check:
        print("REFUSED: --strict and --pre-freeze only apply to --check", file=sys.stderr)
        return 2
    if a.registry_export and not a.freeze:
        print("REFUSED: --registry-export only applies to --freeze", file=sys.stderr)
        return 2
    if a.write_migration_pin:
        try:
            (out / MIGRATION_PIN_FILE).write_text(migration_pin_text(depends_on_migrations()), encoding="utf-8")
        except (G.LevelMapError, OSError) as e:
            print(f"REFUSED: {e}", file=sys.stderr)
            return 2
        return 0
    try:
        frozen_at, version = a.frozen_at, a.version
        pin = census_pin()
        rev, fp, status, cur, rows = pin[0], pin[1], "DRAFT", None, None
        if a.check:
            # a check regenerates AT THE RECORDED stamp, so a stale draft still byte-equals its own regeneration
            cur = G.strict_json_loads((out / G.LEVEL_MAP_FILE).read_text(encoding="utf-8"))
            frozen_at, version = frozen_at or cur["frozen_at"], cur["version"]
            rev, fp, status = cur["registry_revision"], cur["_stamp"]["registry_fingerprint"], cur["_stamp"]["status"]
            rows = G.load_registry_json(out / REGISTRY_INPUT_FILE)
        elif a.freeze:
            if not a.registry_export:
                raise G.LevelMapError("--freeze needs --registry-export (a live asset_registry export)")
            status = "FROZEN"
            export_rows = G.load_registry_json(a.registry_export)
            diff = export_diff(G.load_registry_json(out / REGISTRY_INPUT_FILE), export_rows)
            if diff:
                raise G.LevelMapError("the live export differs from registry_input_draft.json (active ids and edges); nothing "
                                      "written; re-derive the draft from the export and review first:\n  " + "\n  ".join(diff))
            rows = export_rows
        if not frozen_at:
            raise G.LevelMapError("--frozen-at is required (a regeneration is reproducible only with a fixed timestamp)")
        if not a.check:
            refusals = existing_set_refusals(out)
            if refusals and not a.force:
                raise G.LevelMapError("refusing to overwrite a set that is not an unmodified DRAFT (pass --force): " + "; ".join(refusals))
        files = render(frozen_at=frozen_at, registry_revision=rev, registry_fingerprint=fp, version=version, status=status, rows=rows)
    except (G.LevelMapError, OSError, ValueError, KeyError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    if a.check:
        bad = [n for n, t in files.items() if not (out / n).exists() or (out / n).read_text(encoding="utf-8") != t]
        for n in bad:
            print(f"DIFFERS: {out / n} (regenerate with --frozen-at {frozen_at})", file=sys.stderr)
        stale = staleness(cur, pin)
        fail = bool(bad)
        if stale and status == "DRAFT":
            print(f"STALE (draft): {'; '.join(stale)} (regenerate before J1; --strict makes this an error)", file=sys.stderr)
            fail = fail or a.strict
        elif stale:
            print(f"STALE ({status}): {'; '.join(stale)}", file=sys.stderr)
            fail = True
        if a.pre_freeze:
            if status == "DRAFT":
                print("PRE-FREEZE FAIL: the stamp status is DRAFT (a freeze needs --freeze with a live registry export)", file=sys.stderr)
                fail = True
            if stale:
                print("PRE-FREEZE FAIL: the census stamp is stale", file=sys.stderr)
                fail = True
        return 1 if fail else 0
    try:
        write_set_atomic(out, files)
    except OSError as e:
        print(f"ERROR: write failed, originals restored: {type(e).__name__}: {e}", file=sys.stderr)
        return 5
    levels = G.strict_json_loads(files[G.LEVEL_MAP_FILE])["levels"]
    print(json.dumps(dict(assets=len(levels), max_level=max(levels.values()), registry_revision=rev, frozen_at=frozen_at,
                          status=status)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"regenerate_draft_level_map: script error -- {exc}", file=sys.stderr)
        sys.exit(5)
