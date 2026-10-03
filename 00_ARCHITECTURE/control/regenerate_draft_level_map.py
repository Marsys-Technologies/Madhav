#!/usr/bin/env python3
"""regenerate_draft_level_map.py -- Suvarna E6.3 (SS ruling N-97 item 6): the DRAFT, pre-J1 LEVEL_MAP.json and FAMILY_ASSETS.json.

"DRAFT FAMILY_ASSETS and a pre-J1 LEVEL_MAP NOW, marked draft. The wave plan and the L0 wave prep need levels early.
Freeze at J1." Both files are produced by generate_level_map.py (never hand-edited) from three committed inputs:

  registry_input_draft.json  the registry rows [{asset_id, layer, depends_on, active}] the generator reads (--registry-json)
  family_lists_input.json    the six family lists (strategist-owned; unchanged by this tool)
  stamp                      a `_stamp` note carried into BOTH outputs: status DRAFT, the registry revision AND fingerprint
                             (asset_census.REGISTRY_REVISION / registry_fingerprint()) it was generated at, the sha256 of the
                             registry input and where the DAG came from

Where the DAG comes from, OFFLINE (no database, no credential; B.10: nothing is invented):

  * the 127 ACTIVE rows' depends_on = the repo's frozen reconstruction of the live active registry BEFORE migration 1210
    (platform/python-sidecar/tests/fixtures/registry_depends_on_pre_1210.json; its _provenance: md5 of sorted depends_on of
    the 127 active rows matched the live registry at the E6 review) PLUS the 12 edges migration 1210 inserts (parsed from
    platform/migrations/1210_asset_registry_direct_edges.sql). 1210 is the last migration that writes depends_on
    (a guard in test_e6_3_draft_level_map.py scans every later migration for one).
  * cross-checked, in the build session, against the E6 census of origin/main adb0db29d (a read-only live measurement,
    census_fresh/adb0db2): for ALL 127 assets the census's Build.dag "N declared edge(s)" equals len(depends_on) here, and its
    blocking_radius direct and transitive dependent counts equal the ones computed on this graph. The 2026-09-29 plan
    measurement (27 levels, 24/11/4/1 L0 by level, W0 = 65, family positions 1,1,5,12,13) is reproduced exactly.
  * layer = the seed's layer (equal to the census layer for all 127). The seed's depends_on is NOT used: it is bootstrap-only
    and lags the live registry on five assets.
  * inactive rows are present only so the family input's `_notes.inactive` allowance can be checked: the seed's two inactive rows
    and ka_gochara_v3_century_materialize, which the seed marks active but the live registry holds inactive (census L3
    `population_excluded_inactive`, catalog_status CURRENT, is_active false). Inactive rows never enter the level map.

    python3 regenerate_draft_level_map.py --frozen-at 2026-10-03T00:00:00+00:00         # rewrite the three files
    python3 regenerate_draft_level_map.py --check                                         # exit 1 if a committed file differs

Exit: 0 ok · 1 --check found a difference · 2 refused (LevelMapError) · 5 script error.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent

REGISTRY_INPUT_FILE = "registry_input_draft.json"
FAMILY_INPUT_FILE = "family_lists_input.json"
DRAFT_VERSION = "0.2-draft"

FIXTURE = REPO / "platform" / "python-sidecar" / "tests" / "fixtures" / "registry_depends_on_pre_1210.json"
MIGRATION_1210 = REPO / "platform" / "migrations" / "1210_asset_registry_direct_edges.sql"
SEED = REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"
CENSUS = REPO / "platform" / "scripts" / "governance" / "asset_census.py"
GENERATOR = HERE / "generate_level_map.py"

# Registry rows the seed calls active but the live registry holds inactive (evidence: E6 census at origin/main adb0db29d,
# census_L3.json population_excluded_inactive: is_active False, catalog_status CURRENT).
LIVE_INACTIVE_OVERRIDES = ("ka_gochara_v3_century_materialize",)

STAMP_BASIS = (
    "DRAFT. DAG = the 127 active registry rows' depends_on: the repo's frozen live-registry reconstruction before migration "
    "1210 (platform/python-sidecar/tests/fixtures/registry_depends_on_pre_1210.json) plus migration 1210's 12 edges; verified "
    "offline against the E6 census of origin/main adb0db29d (Build.dag declared-edge count and blocking_radius direct and "
    "transitive equal for all 127 assets). Not a live export: the strategist freezes the final files at J1 from a live "
    "export.")


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_level_map_draft", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load_generator()


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
                  for r in rows])


def make_stamp(*, registry_revision: int, registry_fingerprint: str, registry_input_sha256: str) -> dict:
    return {"_stamp": {
        "status": "DRAFT",
        "freeze": "J1: the strategist freezes the final lists and the level map at J1 (SS ruling N-97 item 6)",
        "registry_revision": registry_revision,
        "registry_fingerprint": registry_fingerprint,
        "registry_input": f"00_ARCHITECTURE/control/{REGISTRY_INPUT_FILE}",
        "registry_input_sha256": registry_input_sha256,
        "registry_basis": STAMP_BASIS,
        "regenerate": "python3 00_ARCHITECTURE/control/regenerate_draft_level_map.py --frozen-at <ISO-8601 with timezone>",
    }}


def render(*, frozen_at: str, registry_revision: int, registry_fingerprint: str, version: str = DRAFT_VERSION,
           rows: list[dict] | None = None, family_input=None) -> dict[str, str]:
    """{file name: exact text} for registry_input_draft.json, LEVEL_MAP.json and FAMILY_ASSETS.json. Pure: no clock, no I/O
    beyond reading the committed inputs when they are not injected."""
    rows = derive_registry_rows() if rows is None else rows
    reg_text = registry_input_text(rows)
    stamp = make_stamp(registry_revision=registry_revision, registry_fingerprint=registry_fingerprint,
                       registry_input_sha256=hashlib.sha256(reg_text.encode("utf-8")).hexdigest())
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Regenerate the DRAFT LEVEL_MAP.json / FAMILY_ASSETS.json (E6.3, N-97 item 6).")
    ap.add_argument("--frozen-at", default=None, help="ISO-8601 with timezone; --check reads it from the committed LEVEL_MAP.json")
    ap.add_argument("--version", default=DRAFT_VERSION)
    ap.add_argument("--out-dir", default=str(HERE))
    ap.add_argument("--check", action="store_true", help="compare, write nothing; exit 1 on any difference")
    a = ap.parse_args(argv)
    out = Path(a.out_dir)
    try:
        frozen_at, version = a.frozen_at, a.version
        if a.check:
            cur = G.strict_json_loads((out / G.LEVEL_MAP_FILE).read_text(encoding="utf-8"))
            frozen_at, version = frozen_at or cur["frozen_at"], cur["version"]
        if not frozen_at:
            raise G.LevelMapError("--frozen-at is required (a regeneration is reproducible only with a fixed timestamp)")
        rev, fp = census_pin()
        files = render(frozen_at=frozen_at, registry_revision=rev, registry_fingerprint=fp, version=version)
    except (G.LevelMapError, OSError, ValueError, KeyError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    if a.check:
        bad = [n for n, t in files.items() if not (out / n).exists() or (out / n).read_text(encoding="utf-8") != t]
        for n in bad:
            print(f"DIFFERS: {out / n} (regenerate with --frozen-at {frozen_at})", file=sys.stderr)
        return 1 if bad else 0
    for n, t in files.items():
        (out / n).write_text(t, encoding="utf-8")
    levels = G.strict_json_loads(files[G.LEVEL_MAP_FILE])["levels"]
    print(json.dumps(dict(assets=len(levels), max_level=max(levels.values()), registry_revision=rev, frozen_at=frozen_at)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"regenerate_draft_level_map: script error -- {exc}", file=sys.stderr)
        sys.exit(5)
