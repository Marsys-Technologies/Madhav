#!/usr/bin/env python3
"""nikasha_plant.py -- Suvarna E1.7: the T1 plant harness, ported to main ("the engine finds what is there").

T1 (NIKASHA_CHANGE_REGISTER_v2_0.md section 1; NIKASHA_TEST_CAMPAIGN_PROMPT_v1_0.md Phase 2): plant a known defect for
every inspector check; the census must fail THAT check for THAT asset and no other; a mutated detector must be noticed
by the suite. The campaign's harness (branch campaign/nikasha-test, harness/plant.py + mutation_test.py) planted into a
sandbox CLONE OF PRODUCTION and read production-shaped baselines from saved files. This port does neither: it runs the REAL
inspector (a byte copy of asset_census.py, run as a subprocess exactly as an operator runs it) against a SYNTHETIC world
built here -- a throw-away PostgreSQL (the governance tests' disposable cluster, never a configured database) holding a
reduced projection of the registry / build tables, one healthy fixture asset per plantable check, and a fixture
repository (writers, capability modules, declarations, a test file) in a temporary git checkout. No production table, row
or credential is read, the inspector runs with a scrubbed environment (no inherited PG*, DATABASE_URL or token), and the
only database either process can reach is the disposable cluster.

WHAT ONE PLANT IS. Each plant is applied to a FRESH clone of the pristine world (a database created from a template, a
copied tree), so nothing needs restoring and a leak between plants is impossible by construction. Three measured facts
replace the campaign's per-plant restore lambdas:
  planted     the clone's tree hash and database fingerprint changed (a plant that changes nothing is not planted);
  restore_ok  the PRISTINE world's identity (tree hash + database fingerprint) is unchanged after the plant;
  collateral  after the full census (every asset), a cell that moved and is neither the plant's declared target(s) nor a
              declared same-asset co-fire: another asset's cell, or an undeclared cell of the same asset.
A plant whose target cell is not at the baseline verdict the plant assumes is refused (it would assert nothing). `detected`
= the target cell moved to a verdict the plant declares, which differs from baseline and opens a gap (FAIL / PARTIAL /
NO_DETECTOR, the inspector's own FAILING tuple).

WHAT IT CANNOT DO, said plainly. `Complete.width` and `Reach.fields` return NOT_GENERIC always (reported, never graded): no
plant can make them fail, so they are declared in `unplantable` under the scorecard's closed reason list. The harness proves
the declaration stays true by asserting the cell reads NOT_GENERIC on every asset of the baseline and of every plant's census
(a reason that stopped being true fails the run). The scorecard counts an unplantable check as NOT covered (T1 is at most
PARTIAL while one is declared): see the E1.7 design note. The fixture schema is a PROJECTION of production (only what the
inspector reads) and it is L0-ONLY (every fixture asset is a bg_ asset measured with `--layer L0`): the plants prove the detector logic,
not that production's schema is the fixture's, nor that the L1-L5 layer conventions (delete-then-insert idempotency, chart-scoped count_sql)
behave the same. `required` = every
registry criterion whose detector is `asset_census.py:measure()`; a registry change that adds one without a plant (or an
unplantable declaration) fails the run (`uncovered_required`) and the unit tests.

MUTATION. A mutated detector must be noticed: for each mutant (a byte copy of the inspector, or of a sibling module it loads by
path, with ONE source line changed) a pristine world is built around it, the matching plant is run on a clone and judged against the CONTROL baseline (what a
correct inspector reads on the clean world); the suite notices iff the plant no longer passes. A mutant the harness could
not run is never "noticed"; an anchor that no longer matches exactly once is a harness error naming it.

EVIDENCE. `run` writes `nikasha_t1_evidence/1` (the shape nikasha_scorecard.py's T1 reader consumes): `plants[]`,
`unplantable`, `mutation.suite_notices`, `inspector_blob_sha256` (the sha256 of asset_census.py's bytes), `harness_file_sha256`
(this file), `runtime_files_sha256` ({path: sha256} of every file whose bytes decide a verdict: the inspector, the D1 engine, the two
narration lints and their allowlists, the DAG guard, the declarations file, the D1 fixture and what it cites), `inspector_tree_dirty` /
`runtime_files_dirty` (git status of those files: the hashes are of the WORKING tree) and `harness_sha256`, a hash over the record's own
fields. THAT HASH IS INTEGRITY, NOT AUTHENTICITY: anyone can recompute it for hand-written fields. A verifier must recompute it, compare
`harness_file_sha256` and every `runtime_files_sha256` entry with `git show <ref>:<path>`, and treat a dirty record as UNMEASURED
(`verify` does exactly this). Authenticity comes only from the CI job that ran `run` producing the artifact. The record carries no
clock, path or measured text (the inspector's text holds a date): same code + same inspector => same bytes.

CLI
  nikasha_plant.py list
  nikasha_plant.py verify EVIDENCE [--ref REF]            (exit 0 consistent with the tree, 2 problems, 5 unreadable)
  nikasha_plant.py run [--only id,id] [--out FILE]      (starts a disposable cluster; exit 0 every plant detected with no
                                                         collateral and restored, every required check covered or declared
                                                         unplantable, no unplantable claim stale, every mutant noticed;
                                                         2 otherwise, reasons on stderr; 5 script error / no PostgreSQL)
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SCHEMA = "nikasha_t1_evidence/1"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]                       # platform/scripts/governance -> the repository root this harness runs from
INSPECTOR_REL = "platform/scripts/governance/asset_census.py"
GEN_REL = "platform/scripts/governance/nikasha_plant.py"
MEASURE_DETECTOR = "asset_census.py:measure()"      # the registry's detector string for a check the census measures itself
LAYER = "L0"                                 # every fixture asset is a Brahmagyan (bg_) asset: one layer, one census run
CHART = "482012f1-710e-4a25-994a-93821f5871aa"   # the census's canonical chart id (the fixture's only chart; a literal, no database)

# The closed reason list of nikasha_scorecard.UNPLANTABLE_REASONS (a reason outside it is refused by the scorecard).
UNPLANTABLE = {
    "Complete.width": "constant_verdict_no_per_asset_input",
    "Reach.fields": "reported_not_graded",
    "Earn.service_state": "needs_external_service",   # E5.7: reads the engine's recorded probe result (service_health / last_selftest_at on the registry row); a disposable plant world has no health_probe or self-test history
    # N-156: Carr.D3 has a real detector, but a D3 method serves only the named real assets (carriage_d3_methods `assets`: ga_positions, bg_sky_calendar) and re-derives through the Swiss
    # Ephemeris library against chart_facts / bg_sky_calendar rows: a synthetic bg_t1_* asset can neither declare a D3 spec nor be re-derived, so no fault can be planted in this disposable world.
    # The detector's faults are caught by its own real-fixture tests (test_c1_3_carriage_d3.py, test_c1_3_census_d3_wiring.py, test_n156_carriage_ceilings.py).
    "Carr.D3": "needs_external_service",
}
NOT_GENERIC = "NOT_GENERIC"
FAILING = ("FAIL", "PARTIAL", "NO_DETECTOR")        # the inspector's own gap-opening verdicts (asset_census.FAILING)

# files of the REAL checkout the inspector loads by path at run time; copied byte-for-byte into every fixture tree
RUNTIME_FILES = (
    INSPECTOR_REL,
    "platform/scripts/governance/carriage_d1.py",
    "platform/scripts/governance/build_window.py",
    "platform/scripts/governance/check_fact_category_pinning.py",
    "platform/scripts/governance/fact_category_pin_allowlist.json",
    "platform/scripts/governance/check_no_raw_token_in_narrative.py",
    "platform/scripts/governance/no_raw_token_narrative_allowlist.json",
    "platform/python-sidecar/pipeline/orchestrator/dag_edge_guard.py",
)
D1_FIXTURE_REL = "platform/scripts/governance/__tests__/fixtures/phaladeepika_latta_d1_fixture.json"
DECLARATIONS_REL = "platform/scripts/governance/asset_declarations.json"
WRITERS_REL = "platform/python-sidecar/pipeline/orchestrator/writers"
CAPS_REL = "platform/src/lib/retrieval/registry/layers/L0_brahmagyan"


# ───────────────────────────── the synthetic world ─────────────────────────────
# One healthy asset per plantable check (plus a dependency anchor and an untouched control). Every plant mutates exactly
# ONE asset's inputs; the census then runs over ALL of them, so a defect that leaks into another asset's cell is seen.

@dataclass(frozen=True)
class AssetSpec:
    slug: str                      # the asset is bg_t1_<slug>, its table bg_t1_<slug>
    deps: tuple = ()               # declared depends_on (other fixture asset ids)
    prose: bool = False            # declares prose_fields ["story_narrative"] (the Narr.* / Null.* assets)
    floor: int = 4                 # registry target_floor (the table holds exactly 4 rows)

    @property
    def aid(self) -> str:
        return f"bg_t1_{self.slug}"


ASSETS = tuple(AssetSpec(s) for s in (
    "reg", "contract", "target", "dag", "cint", "comp", "exer", "hist", "anchor", "idem", "earn", "cost", "floor",
    "depth", "ident", "alias", "ldgr", "dens", "ctl", "integ", "histab", "anchor2")) + (
    AssetSpec("dep", deps=("bg_t1_anchor",)),
    AssetSpec("depstale", deps=("bg_t1_anchor2",)),
) + tuple(AssetSpec(s, prose=True) for s in ("nagree", "nchk", "nfid", "nlint", "nsd", "nbl"))

ROWS = (            # (code, variant, tier, synonyms, classical_citation, note, story_narrative)
    ("c1", "a", "t1", "{s1}", "BPHS 1.1", "first", "row one verified"),
    ("c2", "b", "t1", "{s2}", "BPHS 1.2", "second", "row two verified"),
    ("c3", None, "t2", "{s3}", "BPHS 1.3", "third", "row three verified"),
    ("c4", None, "t2", "{s4}", "BPHS 1.4", "fourth", "row four verified"),
)
# The declared integrity_check_sql HOLDS on the clean world (N-99, registry revision 25: count equality alone is not a completion when an asset
# declares an integrity check; it must hold too): a truthy first value of the first row.
INTEGRITY_SQL = "SELECT bool_and(length({col}) > 0) FROM {t}"
T_RUN = "2026-01-01 00:00:00+00"         # the one build run
T_START, T_END = "2026-01-01 00:00:01+00", "2026-01-01 00:00:10+00"
RUN_ID = "00000000-0000-4000-8000-0000000000e1"

SCHEMA_SQL = """
CREATE TABLE asset_registry (
  asset_id text PRIMARY KEY, layer text NOT NULL, target_table text, count_sql text, integrity_check_sql text,
  target_floor int, depends_on text[] DEFAULT ARRAY[]::text[], has_writer boolean, is_active boolean DEFAULT true,
  dead_flag boolean, catalog_status text, asset_kind text NOT NULL DEFAULT 'data' CHECK (asset_kind IN ('data','service','artifact')));
CREATE TABLE asset_throughput (
  asset_id text NOT NULL, chart_id uuid, state text NOT NULL DEFAULT 'dormant', rows_written bigint, rows_per_second double precision,
  last_built_at timestamptz, last_measured_at timestamptz, duration_seconds double precision);
CREATE TABLE build_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, scope text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE build_run_assets (
  run_id uuid NOT NULL REFERENCES build_runs(id), asset_id text NOT NULL, position int NOT NULL, state text NOT NULL,
  disposition text, started_at timestamptz, ended_at timestamptz, error text, PRIMARY KEY (run_id, asset_id));
CREATE TABLE asset_provenance_receipts (build_id uuid, asset_id text);
"""


def table_sql(a: AssetSpec) -> str:
    t = a.aid
    cols = ", story_narrative text" if a.prose else ""
    ins_cols = "code, variant, tier, synonyms, classical_citation, note" + (", story_narrative" if a.prose else "")
    vals = []
    for code, variant, tier, syn, cit, note, story in ROWS:
        v = [f"'{code}'", "NULL" if variant is None else f"'{variant}'", f"'{tier}'", f"'{syn}'", f"'{cit}'", f"'{note}'"]
        if a.prose:
            v.append(f"'{story}'")
        vals.append("(" + ", ".join(v) + ")")
    return (f"CREATE TABLE {t} (id serial PRIMARY KEY, code text NOT NULL, variant text, tier text, synonyms text[], "
            f"classical_citation text, note text{cols}, UNIQUE (code, variant));\n"
            f"INSERT INTO {t} ({ins_cols}) VALUES {', '.join(vals)};\n")


def registry_sql(a: AssetSpec) -> str:
    t = a.aid
    deps = "ARRAY[" + ", ".join(f"'{d}'" for d in a.deps) + "]::text[]" if a.deps else "ARRAY[]::text[]"
    return (f"INSERT INTO asset_registry (asset_id, layer, target_table, count_sql, integrity_check_sql, target_floor, depends_on, has_writer) "
            f"VALUES ('{t}', 'brahmagyan', '{t}', 'SELECT count(*) FROM {t}', '{INTEGRITY_SQL.format(t=t, col='code')}', {a.floor}, {deps}, true);\n"
            f"INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, last_built_at, last_measured_at, duration_seconds) "
            f"VALUES ('{t}', NULL, 'lit', {len(ROWS)}, '{T_END}', '{T_END}', 2.0);\n"
            f"INSERT INTO build_run_assets (run_id, asset_id, position, state, disposition, started_at, ended_at) "
            f"VALUES ('{RUN_ID}', '{t}', 0, 'complete', 'build', '{T_START}', '{T_END}');\n")


def world_sql(assets=ASSETS) -> str:
    out = [SCHEMA_SQL, f"INSERT INTO build_runs (id, chart_id, scope, created_at) VALUES ('{RUN_ID}', '{CHART}', 'layer', '{T_RUN}');\n"]
    for a in assets:
        out.append(table_sql(a))
        out.append(registry_sql(a))
    out.append(d1_sql())
    # the dependency anchor also has a chart-scoped build record: its dependents read THAT row (Build.dep_liveness is graded at the
    # census chart), its own Build.completion reads the global row, so a plant on the chart row moves the dependent's cell only
    for anchor in ("bg_t1_anchor", "bg_t1_anchor2"):
        out.append(f"INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, last_built_at, last_measured_at, duration_seconds) "
                   f"VALUES ('{anchor}', '{CHART}', 'lit', {len(ROWS)}, '{T_END}', '{T_END}', 2.0);\n")
    return "".join(out)


def writer_text(a: AssetSpec) -> str:
    t = a.aid
    extra_col = ", story_narrative" if a.prose else ""
    extra_val = ", %s" if a.prose else ""
    builder = ""
    if a.prose:
        builder = ('def build_story(n):\n    """The narration builder the fidelity test exercises."""\n'
                   '    return {"story_narrative": f"row {n} verified"}\n\n\n')
    return (f'"""Fixture writer for {t} (the nikasha_plant synthetic world: parsed by the inspector, never executed)."""\n'
            "from __future__ import annotations\n\n"
            "from pipeline.orchestrator.writers import ContextSpec, WriterBase, WriterResult, register\n\n"
            f"ROWS = [(\"c1\", \"a\")]\n\n\n{builder}"
            f'@register("{t}")\n'
            f"class Writer(WriterBase):\n"
            f"    def run(self, ctx: ContextSpec) -> WriterResult:\n"
            f"        cur = ctx.db_conn.cursor()\n"
            f"        for r in ROWS:\n"
            f'            cur.execute("INSERT INTO {t} (code, variant, tier, synonyms, classical_citation, note{extra_col}) '
            f'VALUES (%s, %s, %s, %s, %s, %s{extra_val}) ON CONFLICT (code, variant) DO UPDATE SET note = EXCLUDED.note", r)\n'
            f"        return WriterResult(asset_id=ctx.asset_id, rows_inserted=len(ROWS))\n")


WRITER_INIT = '''"""Fixture writer framework stub (the inspector excludes this file from the writer scan)."""
'''


def caps_text(a: AssetSpec) -> str:
    t = a.aid
    return (f"// fixture capability module for {t} (nikasha_plant)\n"
            f"export const CAP_{a.slug.upper()} = {{\n"
            f"  name: '{t}_get',\n"
            f"  density_contract: {{ paginated: true, facets: ['tier'] }},\n"
            f"  sql: 'SELECT code, tier FROM {t} ORDER BY code',\n"
            f"}};\n")


def fidelity_test_text(a: AssetSpec) -> str:
    return ("from pipeline.orchestrator.writers.%s import build_story\n\n\n"
            "def test_story_narrative_is_graded():\n"
            "    out = build_story(1)\n"
            '    assert out["story_narrative"] == "row 1 verified"\n') % a.aid


def declarations_text(assets=ASSETS) -> str:
    """The fixture's asset-declarations file: the real file's own schema keys (so the inspector's validator accepts it) and one entry
    per prose-declaring fixture asset. An undeclared asset is UNKNOWN to the Narr / Null checks (NO_DETECTOR), exactly as in production."""
    real = json.loads((REPO / DECLARATIONS_REL).read_text(encoding="utf-8"))
    doc = {k: v for k, v in real.items() if k != "assets"}
    entries = {}
    for a in assets:
        if not a.prose:
            continue
        wp = f"{WRITERS_REL}/{a.aid}.py"
        line = next(i for i, ln in enumerate(writer_text(a).split("\n"), 1) if 'return {"story_narrative"' in ln)
        entries[a.aid] = {
            "kind": "data", "carriage": {"served_surface": None}, "prose_fields": ["story_narrative"],
            "terminal_by_construction": None, "cross_asset_writes": None, "read_evidence": None, "read_table": None, "read_kind": None,
            "evidence": {"kind": "fixture asset of the nikasha_plant synthetic world; registry kind data", "carriage": None,
                         "prose_fields": f"{wp}:{line} composes the `story_narrative` TEXT column per row by f-string from the row number."},
            "evidence_kind": "writer"}
    entries[D1_AID] = d1_declaration()[0]
    doc["assets"] = entries
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


def tree_files(assets=ASSETS) -> dict:
    """relative path -> text of every synthetic (non-copied) file of the fixture repository."""
    files = {f"{WRITERS_REL}/__init__.py": WRITER_INIT,
             DECLARATIONS_REL: declarations_text(assets),
             "platform-mcp/src/tools/README.md": "fixture serving root (no capability here)\n",
             "platform-mcp/src/lib/README.md": "fixture serving root (no capability here)\n",
             "00_ARCHITECTURE/control/README.md": "fixture control directory\n",
             # Build.history window (SS): the registry identity of each fixture asset is dated by the migration that registers it
             "platform/migrations/001_t1_fixture_registry.sql": "".join(
                 f"INSERT INTO asset_registry (asset_id) VALUES ('{a.aid}');\n" for a in assets)}
    files[f"{WRITERS_REL}/{D1_AID}.py"] = d1_writer_text()
    for rel in d1_declaration()[1]:                      # files the D1 declaration cites (copied byte-for-byte; read by the validator)
        files[rel] = (REPO / rel).read_text(encoding="utf-8")
    for a in assets:
        files[f"{WRITERS_REL}/{a.aid}.py"] = writer_text(a)
        files[f"{CAPS_REL}/{a.aid}.ts"] = caps_text(a)
        if a.prose:
            files[f"platform/python-sidecar/pipeline/orchestrator/__tests__/test_{a.aid}.py"] = fidelity_test_text(a)
    return files


def write_tree(dest: Path, files: dict, overrides: dict | None = None) -> None:
    """The fixture repository: the real runtime files (byte copies; `overrides` {rel: bytes} replaces a runtime file for the mutation test),
    the synthetic files, then one git commit (the census stamps `tool_commit` only from a clean checkout)."""
    overrides = overrides or {}
    unknown = sorted(set(overrides) - set(RUNTIME_FILES))
    if unknown:
        raise HarnessError(f"an override names a file that is not a runtime file of the fixture: {unknown}")
    for rel, text in files.items():                      # synthetic files first: a copy of a runtime file among them (the D1 declaration cites
        out = dest / rel                                 # carriage_d1.py) must never overwrite the runtime copy or a mutant of it
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    for rel in RUNTIME_FILES:
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(overrides[rel] if rel in overrides else (REPO / rel).read_bytes())
    for rel, data in overrides.items():                  # EARNED: a mutant that did not reach the tree would make "noticed" vacuous
        if (dest / rel).read_bytes() != data:
            raise HarnessError(f"the mutated {rel} did not reach the fixture tree")
    # The fixture commit is dated BEFORE the synthetic build history (T_RUN, 2026-01-01) so that history lies inside the Build.history window
    # (the later of the code and the registry-identity dates, both this one commit); the branch is `main`, the ref the window reads.
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(dest), "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_COMMITTER_DATE": "2025-12-31T00:00:00 +0000", "GIT_AUTHOR_DATE": "2025-12-31T00:00:00 +0000"}
    for args in (["init", "-q", "-b", "main"], ["add", "-A"],
                 ["-c", "user.name=nikasha_plant", "-c", "user.email=nikasha_plant@invalid", "commit", "-q", "-m", "fixture"]):
        p = subprocess.run(["git", "-C", str(dest), *args], capture_output=True, env=env)
        if p.returncode != 0:
            raise HarnessError(f"git {args[0]} failed in the fixture tree: {p.stderr.decode('utf-8', 'replace').strip()}")


def tree_hash(root: Path) -> str:
    """sha256 over every file's relative path and bytes (excluding .git, the census output and caches): the pristine world's tree identity."""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_dir() or rel.startswith(".git/") or rel == "census.json" or "__pycache__" in rel:
            continue
        h.update(rel.encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


class HarnessError(Exception):
    """The harness itself could not run (no cluster, a fixture that does not load, an inspector that crashed). Never a verdict."""


class Db:
    """The disposable cluster, wrapped: one cluster for the whole run (a SysV shared-memory slot is scarce on a busy host)."""

    def __init__(self, cluster):
        self.cl = cluster
        self.n = 0

    def sql(self, q: str, db: str) -> str:
        try:
            return self.cl.psql(q, db=db)
        except Exception as exc:                         # PGStartError carries the psql error text
            raise HarnessError(f"fixture SQL failed on {db}: {exc}") from exc

    def create(self, name: str, template: str | None = None) -> None:
        self.sql(f"CREATE DATABASE {name}" + (f" TEMPLATE {template}" if template else ""), "postgres")

    def drop(self, name: str) -> None:
        try:
            self.cl.psql(f"DROP DATABASE IF EXISTS {name}", db="postgres")
        except Exception:                                # best effort: the cluster is deleted at the end anyway
            pass

    def fingerprint(self, db: str) -> str:
        """The database's identity: a hash over the catalog (columns, types, defaults) and every row of every public base table, each in a total
        order. ONE round trip (`query_to_xml` runs the per-table hash inside the server); it is taken several times per plant."""
        q = ("SELECT md5(coalesce(string_agg(t, '|' ORDER BY t), '')) FROM ("
             "SELECT table_name || '=' || (xpath('/row/h/text()', query_to_xml(format("
             "'SELECT coalesce(md5(string_agg(x::text, ''|'' ORDER BY x::text)), '''') AS h FROM %I x', table_name), false, true, '')))[1]::text AS t "
             "FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
             "UNION ALL SELECT 'columns=' || coalesce(string_agg(table_name || '.' || column_name || ':' || data_type || ':' || "
             "coalesce(column_default, ''), '|' ORDER BY table_name, column_name), '') FROM information_schema.columns "
             "WHERE table_schema = 'public') s")
        return self.sql(q, db)


def run_census(db: Db, tree: Path, dbname: str, layer: str = LAYER, assets: str | None = None) -> dict:
    """The inspector, as an operator runs it: `asset_census.py --layer L0 --out census.json` from the fixture tree, against `dbname` on the
    disposable cluster only (a scrubbed environment: no inherited PG*, DATABASE_URL or token). Returns the parsed census JSON."""
    out = tree / "census.json"
    if out.exists():
        out.unlink()
    env = {"PATH": f"{db.cl.bin_dir}{os.pathsep}/usr/bin{os.pathsep}/bin", "PYTHONHASHSEED": "0", "LC_ALL": "C", "HOME": str(tree),
           "NIKASHA_CONTROL_DIR": str(tree / "00_ARCHITECTURE" / "control"), **db.cl.env(), "PGDATABASE": dbname}
    cmd = [sys.executable, str(tree / INSPECTOR_REL), "--layer", layer, "--out", str(out)]
    if assets:
        cmd += ["--assets", assets]
    p = subprocess.run(cmd, capture_output=True, env=env, cwd=str(tree), timeout=900)
    if p.returncode not in (0, 2, 3) or not out.is_file():
        raise HarnessError(f"the inspector did not produce a census (exit {p.returncode}): "
                           f"{(p.stderr or p.stdout).decode('utf-8', 'replace').strip()[-600:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def cells(doc: dict, layer: str = LAYER) -> dict:
    """{asset_id: {check: verdict}} of one layer's census."""
    return {a["asset_id"]: {c: (m or {}).get("v") for c, m in a["measurements"].items()} for a in doc[layer]["assets"]}


def measured(doc: dict, aid: str, check: str, layer: str = LAYER) -> str:
    for a in doc[layer]["assets"]:
        if a["asset_id"] == aid:
            return (a["measurements"].get(check) or {}).get("measured", "<absent>")
    return "<absent>"


# ── the declared-carriage (Carr.D1) asset: the real bg_phaladeepika_latta declaration over the committed corpus fixture ──
D1_AID = "bg_phaladeepika_latta"
D1_TABLE_VERSION = "bg_phaladeepika_latta_v01"
D1_CITATION = "Phaladeepika Adh. XXVI PG339"


def _q(v) -> str:
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def d1_fixture() -> dict:
    return json.loads((REPO / D1_FIXTURE_REL).read_text(encoding="utf-8"))


def d1_sql() -> str:
    fx = d1_fixture()
    out = ["CREATE TABLE bg_phaladeepika_latta (table_version text NOT NULL, graha text NOT NULL, count_from_graha smallint NOT NULL, "
           "direction text NOT NULL CHECK (direction IN ('forward', 'backward')), effect_description text, affliction_condition text NOT NULL, "
           "source_citation text NOT NULL, verse_ref text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), "
           "CONSTRAINT bg_phaladeepika_latta_pk PRIMARY KEY (table_version, graha));\n",
           "CREATE TABLE classical_text_chunks (chunk_id text PRIMARY KEY, text_id text, content_en text, content_sa text, content_sha256 text);\n"]
    for r in fx["bg_phaladeepika_latta"]:
        out.append("INSERT INTO bg_phaladeepika_latta (table_version, graha, count_from_graha, direction, effect_description, affliction_condition, "
                   f"source_citation, verse_ref, created_at) VALUES ({_q(D1_TABLE_VERSION)}, {_q(r['graha'])}, {r['count_from_graha']}, "
                   f"{_q(r['direction'])}, {_q(r['effect_description'])}, {_q(r['affliction_condition'])}, {_q(D1_CITATION)}, {_q(r['verse_ref'])}, "
                   f"'{T_RUN}');\n")
    for c in fx["classical_text_chunks"]:
        out.append(f"INSERT INTO classical_text_chunks VALUES ({_q(c['chunk_id'])}, {_q(c['text_id'])}, {_q(c['content_en'])}, {_q(c['content_sa'])}, "
                   f"{_q(c['content_sha256'])});\n")
    n = len(fx["bg_phaladeepika_latta"])
    t = D1_AID
    out.append(f"INSERT INTO asset_registry (asset_id, layer, target_table, count_sql, integrity_check_sql, target_floor, depends_on, has_writer) "
               f"VALUES ('{t}', 'brahmagyan', '{t}', 'SELECT count(*) FROM {t}', '{INTEGRITY_SQL.format(t=t, col='graha')}', {n}, "
               f"ARRAY[]::text[], true);\n"
               f"INSERT INTO asset_throughput (asset_id, chart_id, state, rows_written, last_built_at, last_measured_at, duration_seconds) "
               f"VALUES ('{t}', NULL, 'lit', {n}, '{T_END}', '{T_END}', 2.0);\n"
               f"INSERT INTO build_run_assets (run_id, asset_id, position, state, disposition, started_at, ended_at) "
               f"VALUES ('{RUN_ID}', '{t}', 0, 'complete', 'build', '{T_START}', '{T_END}');\n")
    return "".join(out)


def d1_writer_text() -> str:
    return (f'"""Fixture writer for {D1_AID} (the nikasha_plant synthetic world: parsed by the inspector, never executed)."""\n'
            "from __future__ import annotations\n\n"
            "from pipeline.orchestrator.writers import ContextSpec, WriterBase, WriterResult, register\n\n"
            "ROWS = []\n\n\n"
            f'@register("{D1_AID}")\n'
            "class Writer(WriterBase):\n"
            "    def run(self, ctx: ContextSpec) -> WriterResult:\n"
            "        cur = ctx.db_conn.cursor()\n"
            "        for r in ROWS:\n"
            f'            cur.execute("INSERT INTO {D1_AID} (table_version, graha, count_from_graha, direction, effect_description, '
            'affliction_condition, source_citation, verse_ref) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) '
            'ON CONFLICT (table_version, graha) DO UPDATE SET direction = EXCLUDED.direction", r)\n'
            "        return WriterResult(asset_id=ctx.asset_id, rows_inserted=len(ROWS))\n")


def d1_declaration() -> tuple[dict, list]:
    """(entry, cited repo files): the REAL declaration of bg_phaladeepika_latta -- its D1 carriage spec, its prose_fields [] and the
    prose_coupling that rests Narr's N/A on Carr.D1 -- minus the three declarations the plants do not need (vocab_alias, ldgr_source,
    null_convention), plus every repo file its evidence cites (the inspector's validator opens them)."""
    real = json.loads((REPO / DECLARATIONS_REL).read_text(encoding="utf-8"))["assets"][D1_AID]
    entry = {k: v for k, v in real.items() if k not in ("vocab_alias", "ldgr_source", "null_convention")}
    cited = sorted(set(re.findall(r"(?:platform|platform-mcp)/[A-Za-z0-9_./-]+\.[a-z]+", json.dumps(entry))))
    return entry, [c for c in cited if (REPO / c).is_file()]


# ───────────────────────────── instances: a fresh clone of the pristine world per plant ─────────────────────────────

class Instance:
    """One clone of the pristine world: a copied tree and a database created from the template. A plant mutates ONLY this."""

    def __init__(self, world: "World", key: str):
        self.world, self.key = world, key
        self.dbname = f"nt_{world.wid}_{key}"
        self.tree = world.work / f"tree_{key}"

    def sql(self, q: str) -> str:
        return self.world.db.sql(q, self.dbname)

    def read(self, rel: str) -> str:
        return (self.tree / rel).read_text(encoding="utf-8")

    def write(self, rel: str, text: str) -> None:
        (self.tree / rel).write_text(text, encoding="utf-8")

    def edit(self, rel: str, old: str, new: str) -> None:
        """Replace `old` by `new` in a tree file; `old` must occur exactly once (a plant that silently edits nothing asserts nothing)."""
        text = self.read(rel)
        if text.count(old) != 1:
            raise HarnessError(f"plant edit anchor {old!r} occurs {text.count(old)} times in {rel} (expected exactly once)")
        self.write(rel, text.replace(old, new))

    def delete(self, rel: str) -> None:
        p = self.tree / rel
        if not p.is_file():
            raise HarnessError(f"plant deletes {rel}, which is not a file of the fixture tree")
        p.unlink()

    def census(self) -> dict:
        return run_census(self.world.db, self.tree, self.dbname)

    def identity(self) -> dict:
        """The clone's tree hash and database fingerprint: a plant that changes neither planted nothing."""
        return dict(tree=tree_hash(self.tree), db=self.world.db.fingerprint(self.dbname))

    def drop(self) -> None:
        self.world.db.drop(self.dbname)
        shutil.rmtree(self.tree, ignore_errors=True)


_WORLD_IDS = itertools.count(1)


class World:
    """The pristine synthetic world (database `nt_base` + a tree) and its identity; clones are taken from it, never run on it."""

    def __init__(self, db: Db, work: Path, assets=ASSETS):
        self.db, self.work, self.assets = db, Path(work), assets
        self.wid = next(_WORLD_IDS)                      # several worlds may share one cluster (a pytest session): names must not collide
        self.base_tree = self.work / "tree_base"
        self.base_db = f"nt_base_{self.wid}"
        self.fp: dict | None = None

    def build(self, overrides: dict | None = None) -> None:
        self.db.create(self.base_db)
        self.db.sql(world_sql(self.assets), self.base_db)
        self.base_tree.mkdir(parents=True)
        write_tree(self.base_tree, tree_files(self.assets), overrides)
        self.fp = self.identity()

    def identity(self) -> dict:
        return dict(tree=tree_hash(self.base_tree), db=self.db.fingerprint(self.base_db))

    def clone(self, key: str) -> Instance:
        inst = Instance(self, key)
        self.db.create(inst.dbname, template=self.base_db)
        shutil.copytree(self.base_tree, inst.tree, symlinks=True)
        return inst

    def pristine(self) -> bool:
        """True iff the pristine world is byte-for-byte what `build` made it (no plant leaked into it)."""
        return self.identity() == self.fp


# ───────────────────────────── plants ─────────────────────────────

@dataclass(frozen=True)
class Plant:
    """One planted defect. `expect`: the verdicts the target cell may read afterwards (each must differ from `base`, each opens a gap);
    `also`: further cells of the SAME asset the plant is declared to move, with their own expected verdicts (a co-fire that is part of
    the one defect: e.g. an emptied table also fails Count.floor); `allow`: same-asset cells that legitimately follow from the defect
    (recorded as same_asset_effects, never collateral). Everything else that moves, on any asset, is collateral."""
    id: str
    check: str
    asset: str                                  # asset id
    desc: str
    apply: Callable[[Instance], None]
    expect: tuple = ("FAIL",)
    base: str = "PASS"                          # the baseline verdict the plant assumes (a plant whose cell is elsewhere is refused)
    also: tuple = ()                            # ((check, (verdicts...)), ...)
    allow: tuple = ()                           # same-asset checks allowed to move


PLANTS: list[Plant] = []


def plant(**kw):
    PLANTS.append(Plant(**kw))


def a(slug: str) -> str:
    return f"bg_t1_{slug}"


def wpath(aid: str) -> str:
    return f"{WRITERS_REL}/{aid}.py"


def reg_update(aid: str, set_clause: str):
    return lambda i: i.sql(f"UPDATE asset_registry SET {set_clause} WHERE asset_id = '{aid}'")


def thr_update(aid: str, set_clause: str, where: str = ""):
    return lambda i: i.sql(f"UPDATE asset_throughput SET {set_clause} WHERE asset_id = '{aid}'" + (f" AND {where}" if where else ""))


def tbl_sql(aid: str, sql: str):
    return lambda i: i.sql(sql.replace("{t}", aid))


plant(id="build_registered", check="Build.registered", asset=a("reg"),
      desc="the registry says has_writer=false while the writer file still carries @register: registry and code disagree",
      apply=reg_update(a("reg"), "has_writer = false"), allow=("Earn.build_record",))
plant(id="build_contract", check="Build.contract", asset=a("contract"),
      desc="CODE: a real ctx.db_conn.commit() call is inserted into the writer's run() (the orchestrator owns the transaction)",
      apply=lambda i: i.edit(wpath(a("contract")), "        cur = ctx.db_conn.cursor()\n", "        cur = ctx.db_conn.cursor()\n        ctx.db_conn.commit()\n"),
      allow=("Build.history",))                                                       # the writer no longer equals main's: no window can be certified
plant(id="build_target", check="Build.target", asset=a("target"),
      desc="target_table is cleared on a writer-backed data asset whose count_sql still names its own table, which no asset declares",
      apply=reg_update(a("target"), "target_table = NULL"),
      allow=("Complete.depth", "Ldgr.source_presence", "Vocab.alias", "Vocab.identity"))   # the table-bound checks lose their substrate
plant(id="build_dag", check="Build.dag", asset=a("dag"),
      desc="depends_on gains an id that is no registry asset (a phantom edge)",
      apply=reg_update(a("dag"), "depends_on = depends_on || 'bg_t1_phantom'::text"), allow=("Build.dep_liveness",))   # the phantom is not lit either
plant(id="build_count_integrity", check="Build.count_integrity", asset=a("cint"), expect=("PARTIAL",),
      desc="integrity_check_sql is cleared (count_sql kept: live count, floor and completion are untouched)",
      apply=reg_update(a("cint"), "integrity_check_sql = NULL"))
plant(id="build_completion", check="Build.completion", asset=a("comp"),
      desc="the build record says rows_written=0 against a populated table (a status with no measurement behind it)",
      apply=thr_update(a("comp"), "rows_written = 0"))
plant(id="build_exercised", check="Build.exercised", asset=a("exer"),
      desc="every build_run_assets row of a writer-backed asset is deleted: the orchestrator has NEVER run it",
      apply=tbl_sql(a("exer"), "DELETE FROM build_run_assets WHERE asset_id = '{t}'"),
      allow=("Build.history", "Cost.baseline", "Earn.build_record"))                  # no run left to judge, time or cost
plant(id="build_history", check="Build.history", asset=a("hist"),
      desc="a later build run ends in state=error for the asset: its latest recorded attempt failed",
      apply=tbl_sql(a("hist"), "INSERT INTO build_runs (id, chart_id, scope, created_at) VALUES ('00000000-0000-4000-8000-0000000000e2', "
                               f"'{CHART}', 'layer', '2026-01-02 00:00:00+00'); INSERT INTO build_run_assets (run_id, asset_id, position, state, "
                               "disposition, started_at, ended_at, error) VALUES ('00000000-0000-4000-8000-0000000000e2', '{t}', 0, 'error', NULL, "
                               "'2026-01-02 00:00:01+00', '2026-01-02 00:00:02+00', 'planted failure')"),
      allow=("Cost.baseline", "Earn.build_record"))                                   # the latest attempt is no longer a completion
plant(id="build_history_aborted", check="Build.history", asset=a("histab"),
      desc="a later build run is ABORTED for the asset (a different failure class from an error: the latest attempt never finished)",
      apply=tbl_sql(a("histab"), "INSERT INTO build_runs (id, chart_id, scope, created_at) VALUES ('00000000-0000-4000-8000-0000000000e2', "
                                 f"'{CHART}', 'layer', '2026-01-02 00:00:00+00'); INSERT INTO build_run_assets (run_id, asset_id, position, state, "
                                 "disposition, started_at, ended_at, error) VALUES ('00000000-0000-4000-8000-0000000000e2', '{t}', 0, 'aborted', NULL, "
                                 "'2026-01-02 00:00:01+00', '2026-01-02 00:00:02+00', NULL)"),
      allow=("Cost.baseline", "Earn.build_record"))
plant(id="build_completion_integrity", check="Build.completion", asset=a("integ"), expect=("PARTIAL",),
      desc="the declared integrity_check_sql stops holding (a blank code on one row; the count still equals rows_written): count equality alone "
           "is not a completion once the asset declares an integrity check (N-99, registry revision 25)",
      apply=tbl_sql(a("integ"), "UPDATE {t} SET code = '' WHERE code = 'c4'"))
plant(id="build_dep_liveness_stale", check="Build.dep_liveness", asset=a("depstale"), expect=("PARTIAL",),
      desc="the declared dependency's build record at the census chart is stale (built, but an upstream has moved since)",
      apply=thr_update(a("anchor2"), "state = 'stale'", f"chart_id = '{CHART}'"))
plant(id="build_dep_liveness", check="Build.dep_liveness", asset=a("dep"),
      desc="the declared dependency's build record at the census chart leaves the lit state (state=error)",
      apply=thr_update(a("anchor"), "state = 'error'", f"chart_id = '{CHART}'"))
plant(id="idem_pattern", check="Idem.pattern", asset=a("idem"), expect=("FAIL",),
      desc="CODE: the writer's upsert clause is removed: a plain INSERT into the asset's own table with no replacement (accretes on rebuild)",
      apply=lambda i: i.edit(wpath(a("idem")), " ON CONFLICT (code, variant) DO UPDATE SET note = EXCLUDED.note", ""),
      allow=("Build.history",))
plant(id="earn_build_record", check="Earn.build_record", asset=a("earn"), expect=("NO_DETECTOR",),
      also=(("Cost.baseline", ("NO_DETECTOR",)),),
      desc="the build record's last_built_at is moved off the attempt's completion (a later write touched it): its duration cannot be attributed",
      apply=thr_update(a("earn"), "last_built_at = last_built_at + interval '1 minute'"))
plant(id="cost_baseline", check="Cost.baseline", asset=a("cost"), expect=("FAIL",),
      also=(("Earn.build_record", ("NO_DETECTOR",)),),
      desc="the completion write carries no duration: no sanctioned baseline build is on record",
      apply=thr_update(a("cost"), "duration_seconds = NULL"))
plant(id="count_floor", check="Count.floor", asset=a("floor"),
      desc="one row is deleted from the target table (live 4 -> 3 against target_floor=4)",
      apply=tbl_sql(a("floor"), "DELETE FROM {t} WHERE code = 'c4'"), allow=("Build.completion",))
plant(id="complete_depth", check="Complete.depth", asset=a("depth"), expect=("PARTIAL",),
      desc="a column of the target table is emptied: NEVER populated on any row",
      apply=tbl_sql(a("depth"), "UPDATE {t} SET note = NULL"))
plant(id="vocab_identity", check="Vocab.identity", asset=a("ident"),
      desc="a row duplicating the declared composite key (code, variant) with a NULL member replaces another row (the unique index admits NULLs)",
      apply=tbl_sql(a("ident"), "DELETE FROM {t} WHERE code = 'c4'; INSERT INTO {t} (code, variant, tier, synonyms, classical_citation, note) "
                                "VALUES ('c3', NULL, 't2', '{s3}', 'BPHS 1.3', 'third')"))
plant(id="vocab_alias", check="Vocab.alias", asset=a("alias"),
      desc="every row's synonyms set is emptied (alias census: all rows lack an alias set)",
      apply=tbl_sql(a("alias"), "UPDATE {t} SET synonyms = '{}'"))
plant(id="ldgr_source_presence", check="Ldgr.source_presence", asset=a("ldgr"), expect=("PARTIAL",),
      desc="the citation column is NULL on one row (populated on 3 of 4)",
      apply=tbl_sql(a("ldgr"), "UPDATE {t} SET classical_citation = NULL WHERE code = 'c1'"))
plant(id="dens_served", check="Dens.served", asset=a("dens"),
      desc="CODE: the served capability module's density_contract declaration is removed (the module still serves the table)",
      apply=lambda i: i.edit(f"{CAPS_REL}/{a('dens')}.ts", "  density_contract: { paginated: true, facets: ['tier'] },\n", ""))
plant(id="narr_agree", check="Narr.agree", asset=a("nagree"),
      desc="the declared prose column is renamed in the table: the declaration names a column the table no longer has",
      apply=tbl_sql(a("nagree"), "ALTER TABLE {t} RENAME COLUMN story_narrative TO story_text"),
      allow=("Narr.checkable", "Null.schema_default", "Null.blank_rows"))
plant(id="narr_checkable", check="Narr.checkable", asset=a("nchk"), expect=("NO_DETECTOR",),
      desc="the declared prose column is NULL on every row: no checkable row remains",
      apply=tbl_sql(a("nchk"), "UPDATE {t} SET story_narrative = NULL"), allow=("Null.blank_rows", "Complete.depth"))
plant(id="narr_fidelity_test", check="Narr.fidelity_test", asset=a("nfid"), base="PARTIAL",
      desc="the test that exercises the narration builder is deleted: no test calls the builder and asserts",
      apply=lambda i: i.delete(f"platform/python-sidecar/pipeline/orchestrator/__tests__/test_{a('nfid')}.py"))
plant(id="narr_lint", check="Narr.lint", asset=a("nlint"),
      desc="CODE: the narrative builder emits a raw internal-token prefix (GRAHA:) into the narrative field",
      apply=lambda i: i.edit(wpath(a("nlint")), 'f"row {n} verified"', 'f"GRAHA: row {n} verified"'),
      allow=("Build.history",))
plant(id="null_schema_default", check="Null.schema_default", asset=a("nsd"), base="PARTIAL",
      desc="the declared prose column gains a non-NULL schema default ('n/a' standing in for NULL)",
      apply=tbl_sql(a("nsd"), "ALTER TABLE {t} ALTER COLUMN story_narrative SET DEFAULT 'n/a'"))
plant(id="null_blank_rows", check="Null.blank_rows", asset=a("nbl"), base="PARTIAL",
      desc="a declared prose cell holds the placeholder 'n/a' instead of NULL",
      apply=tbl_sql(a("nbl"), "UPDATE {t} SET story_narrative = 'n/a' WHERE code = 'c1'"))
plant(id="carr_d1", check="Carr.D1", asset=D1_AID, expect=("PARTIAL",),
      desc="one row's effect text is replaced by another claimant's (the stored text no longer matches the declared passage clause)",
      apply=lambda i: i.sql("UPDATE bg_phaladeepika_latta SET effect_description = (SELECT effect_description FROM bg_phaladeepika_latta "
                            "WHERE graha = 'Venus') WHERE graha = 'Sun'"))


# ───────────────────────────── judging (pure: baseline cells, planted cells -> the plant's record) ─────────────────────────────

def judge(p: Plant, base: dict, post: dict) -> dict:
    """The record of one plant from the clean census cells (`base`) and the planted census cells (`post`), both {asset: {check: verdict}}.
    detected  : the target cell read `p.base` before, reads one of `p.expect` after (a verdict that opens a gap), and every `also` cell
                moved to its declared verdict; a plant whose baseline cell is not `p.base` is refused (detected False, `error` says why).
    collateral: every other cell that moved -- any cell of ANY other asset, and any same-asset cell the plant did not declare."""
    rec = dict(id=p.id, check=p.check, asset=p.asset, desc=p.desc, expect=list(p.expect), planted=True, detected=False,
               verdict_before=base.get(p.asset, {}).get(p.check), verdict_after=post.get(p.asset, {}).get(p.check),
               same_asset_effects={}, collateral=[], error=None)
    targets = {p.check: p.expect, **{c: v for c, v in p.also}}
    declared = set(targets) | set(p.allow)
    b0 = {c: base.get(p.asset, {}).get(c) for c in targets}
    if b0[p.check] != p.base:
        rec["error"] = f"baseline drift: the plant assumes {p.check} reads {p.base!r} on {p.asset}, the clean census reads {b0[p.check]!r}"
        return rec
    moved_ok = []
    for c, exp in targets.items():
        after = post.get(p.asset, {}).get(c)
        moved_ok.append(after in exp and after != b0[c] and after in FAILING)
    rec["detected"] = all(moved_ok)
    for aid in sorted(set(base) | set(post)):
        for c in sorted(set(base.get(aid, {})) | set(post.get(aid, {}))):
            v0, v1 = base.get(aid, {}).get(c), post.get(aid, {}).get(c)
            if v0 == v1 or (aid == p.asset and c in targets):
                continue
            if aid == p.asset and c in declared:
                rec["same_asset_effects"][c] = f"{v0}->{v1}"
            else:
                rec["collateral"].append(f"{aid}/{c}: {v0}->{v1}")
    return rec


UNPLANTABLE_NOT_GENERIC = ("constant_verdict_no_per_asset_input", "reported_not_graded")      # reasons that predict a constant NOT_GENERIC reading


def unplantable_stale(censuses: list, claims: dict = UNPLANTABLE) -> list:
    """Names every declared-unplantable check whose reading no longer matches its reason (a reason that stopped being true: the check became gradeable and so plantable, and the
    declaration would hide a gap in T1). A NOT_GENERIC reason must read constant NOT_GENERIC; `needs_external_service` (Carr.D3, N-156) must read only NO_DETECTOR / N/A on the
    synthetic world (no fixture asset can declare a D3 spec: a PASS, a PARTIAL or any measured verdict there means the claim is stale; NO_DETECTOR or N/A are the only readings)."""
    bad = []
    for check in sorted(claims):
        for cm in censuses:
            vs = {cm[aid][check] for aid in cm if check in cm[aid]}
            if claims[check] in UNPLANTABLE_NOT_GENERIC:
                ok, said = vs == {NOT_GENERIC}, NOT_GENERIC
            else:      # needs_external_service: never a measured verdict in the synthetic world (NO_DETECTOR for an undeclared asset, N/A beside the latta's D1 declaration)
                ok, said = bool(vs) and vs <= {"NO_DETECTOR", "N/A"}, "NO_DETECTOR or N/A"
            if not ok:
                bad.append(f"{check} reads {sorted(map(str, vs))} (declared {claims[check]}: it must read only {said})")
                break
    return bad


# ───────────────────────────── the run: baseline, every plant on a fresh clone, mutation, evidence ─────────────────────────────

_REGISTRY_SNIPPET = r'''
import json, sys
sys.path.insert(0, ".")
import asset_census as a
print(json.dumps(dict(revision=a.REGISTRY_REVISION, fingerprint=a.registry_fingerprint(),
    required=sorted(k for k, v in a.CRITERION_REGISTRY.items() if v.get("detector") == "asset_census.py:measure()")), sort_keys=True))
'''


def registry_facts(inspector_bytes: bytes | None = None) -> dict:
    """revision, fingerprint and the required check set (the registry criteria the census measures itself) of the inspector under test,
    read in an isolated subprocess from a throw-away copy (the harness never imports the module it is testing)."""
    src = inspector_bytes if inspector_bytes is not None else (REPO / INSPECTOR_REL).read_bytes()
    with tempfile.TemporaryDirectory(prefix="nikasha_plant_reg_") as d:
        (Path(d) / "asset_census.py").write_bytes(src)
        p = subprocess.run([sys.executable, "-I", "-c", _REGISTRY_SNIPPET], cwd=d, capture_output=True, timeout=120,
                           env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0", "LC_ALL": "C"})
    if p.returncode != 0:
        raise HarnessError("the inspector's registry could not be read: " + p.stderr.decode("utf-8", "replace").strip()[-300:])
    return json.loads(p.stdout.decode().strip().splitlines()[-1])


def run_one(world: World, p: Plant, base_cells: dict, key: str, extra: list | None = None) -> dict:
    """Apply one plant to a fresh clone, census it, judge it, drop the clone; `restore_ok` = the pristine world is unchanged afterwards."""
    inst = world.clone(key)
    rec = dict(id=p.id, check=p.check, asset=p.asset, planted=False, detected=False, collateral=[], restore_ok=False, error=None,
               harness_error=None)
    try:
        before = inst.identity()
        p.apply(inst)
        planted = inst.identity() != before            # EARNED: a plant that changed nothing is not planted, whatever the census says
        cm = cells(inst.census())
        rec = dict(judge(p, base_cells, cm), harness_error=None)
        if not planted:
            rec.update(planted=False, detected=False, error=(rec["error"] or "") + "the plant changed neither the fixture tree nor the database")
        if extra is not None:
            extra.append(cm)
    except HarnessError as exc:                          # the harness could not run the plant: never a verdict, never "noticed"
        rec["harness_error"] = str(exc)
        rec["error"] = f"HarnessError: {exc}"
    finally:
        inst.drop()
    rec["restore_ok"] = world.pristine()
    return rec


# One mutated copy of the inspector per mutant: ONE comparison changed. The suite notices iff the plant that targets the mutated check
# fails against the mutant (the control, the unmutated inspector, passes it). Anchors are exact source lines; a drifted anchor is a
# harness failure naming it, never a silently skipped mutant.
MUTANTS = (
    dict(id="vocab_identity_inverted", plant="vocab_identity", check="Vocab.identity", file=INSPECTOR_REL,
         old='m["Vocab.identity"] = dict(v=(FAIL if has_dup else PASS),', new='m["Vocab.identity"] = dict(v=(PASS if has_dup else FAIL),'),
    dict(id="count_integrity_ignores_integrity", plant="build_count_integrity", check="Build.count_integrity", file=INSPECTOR_REL,
         old='ok_ci = bool(r["count_sql"]) and r["has_integrity"]', new='ok_ci = bool(r["count_sql"])'),
    dict(id="ldgr_partial_read_as_pass", plant="ldgr_source_presence", check="Ldgr.source_presence", file=INSPECTOR_REL,
         old="v = PASS if present == rows else (FAIL if present == 0 else PARTIAL)",
         new="v = PASS if present >= rows - 1 else (FAIL if present == 0 else PARTIAL)"),
    # sibling modules the inspector loads by path: a detector that lives there must be covered by the mutation check too
    dict(id="carriage_d1_effect_match_blinded", plant="carr_d1", check="Carr.D1", file="platform/scripts/governance/carriage_d1.py",
         old='    e = _norm_effect(eff)\n    if not _effect_ok_text(e):\n        return False\n    key = claimant.strip().lower()\n',
         new='    return True\n    e = _norm_effect(eff)\n    if not _effect_ok_text(e):\n        return False\n    key = claimant.strip().lower()\n'),
    dict(id="raw_token_lint_blinded", plant="narr_lint", check="Narr.lint", file="platform/scripts/governance/check_no_raw_token_in_narrative.py",
         old='_RAW_TOKEN_PREFIX_RE = r"(?:GRAHA|CLASSIFY_RESIDUAL|YOGA|DIGNITY|SUBSYSTEM):"',
         new='_RAW_TOKEN_PREFIX_RE = r"(?:NEVER_MATCHES_ZZZ):"'),
)


def mutate(src: bytes, m: dict) -> bytes:
    text = src.decode("utf-8")
    if text.count(m["old"]) != 1:
        raise HarnessError(f"mutation anchor for {m['id']} occurs {text.count(m['old'])} times in {m.get('file', INSPECTOR_REL)} "
                           f"(expected exactly once): {m['old']!r}")
    return text.replace(m["old"], m["new"]).encode("utf-8")


def run_mutation(work: Path, db: Db, plants_by_id: dict, base_cells: dict, mutants=MUTANTS) -> dict:
    """For each mutant: build a pristine world around the MUTATED file (the inspector, or a sibling module it loads), run the mutant's plant
    on a clone, and judge it. The suite notices a mutant iff the plant no longer passes the suite -- not detected, or the clean cells moved --
    judged against the CONTROL baseline (what a correct inspector reads on the clean world). A mutant the harness could not run is never
    "noticed"."""
    out = []
    for m in mutants:
        rel = m.get("file", INSPECTOR_REL)
        w = World(db, Path(tempfile.mkdtemp(prefix=f"mut_{m['id'][:12]}_", dir=str(work))))
        w.base_db = f"nm_{w.wid}_{m['id'][:20]}"
        try:
            w.build(overrides={rel: mutate((REPO / rel).read_bytes(), m)})
            p = plants_by_id[m["plant"]]
            rec = run_one(w, p, base_cells, f"m_{m['id'][:20]}")
            out.append(noticed_record(m, rec))
        finally:
            db.drop(w.base_db)
    return dict(suite_notices=suite_notices(out), mutants=out)


def noticed_record(m: dict, rec: dict) -> dict:
    """One mutant's result from the mutant plant's run record. `clean` = the suite would have passed the plant; the mutant is noticed iff it
    did not, AND the harness itself ran (a harness_error is a failed run, never a notice)."""
    clean = bool(rec["detected"]) and not rec["collateral"]
    return dict(id=m["id"], check=m["check"], plant=m["plant"], file=m.get("file", INSPECTOR_REL), mutant_detected=clean,
                noticed=(not clean and rec.get("harness_error") is None), mutant_verdict_after=rec.get("verdict_after"), error=rec.get("error"))


def suite_notices(mutants: list) -> bool:
    return bool(mutants) and all(x["noticed"] for x in mutants)


def covered_checks(records: list) -> set:
    """The checks with a plant that was planted, detected, free of collateral and restored: only those count as covered."""
    return {r["check"] for r in records if r.get("planted", True) and r["detected"] and not r["collateral"] and r["restore_ok"]}


def evidence_files() -> list:
    """Every file of the checkout the run reads or copies and whose bytes decide a verdict: the inspector, its run-time siblings (the D1
    engine, the two narration lints and their allowlists, the DAG guard), the real declarations file and the D1 corpus fixture with every
    repo file the D1 declaration cites. All are hashed into the evidence so a verifier can compare each with `git show <ref>:<path>`."""
    return sorted(set(RUNTIME_FILES) | {DECLARATIONS_REL, D1_FIXTURE_REL, GEN_REL} | set(d1_declaration()[1]))


def runtime_files_sha256(root: Path = REPO) -> dict:
    return {rel: hashlib.sha256((Path(root) / rel).read_bytes()).hexdigest() for rel in evidence_files()}


def _git_out(*args) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, env=env, timeout=60)


def dirty_files() -> list | None:
    """The evidence files with tracked modifications in the checkout (git status); None when git cannot answer. The evidence hashes the WORKING
    tree, so a dirty file means the evidence describes code that is not any commit: a consumer must read `inspector_tree_dirty` /
    `runtime_files_dirty` and treat a dirty record as UNMEASURED."""
    try:
        p = _git_out("status", "--porcelain", "--untracked-files=no", "--", *evidence_files())
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    return sorted(ln[3:].strip() for ln in p.stdout.decode("utf-8", "replace").splitlines() if ln.strip())


EVIDENCE_DOC = (
    "INTEGRITY, not authenticity: harness_sha256 is a hash over this record's own fields, so a verifier can detect an edited result but anyone "
    "can recompute it for hand-written fields. A verifier must (1) recompute harness_sha256, (2) compare harness_file_sha256 and every "
    "runtime_files_sha256 entry with `git show <ref>:<path>`, (3) treat inspector_tree_dirty / runtime_files_dirty as UNMEASURED. Authenticity "
    "comes only from the CI job that ran `nikasha_plant.py run` producing the artifact.")


def run_suite(db: Db, work: Path, only: set | None = None, plants=None, mutants=MUTANTS) -> dict:
    """The whole T1 run; returns the `nikasha_t1_evidence/1` document."""
    plants = list(plants if plants is not None else PLANTS)
    work = Path(work)
    files_before = runtime_files_sha256()
    inspector = (REPO / INSPECTOR_REL).read_bytes()
    reg = registry_facts()
    world = World(db, work)
    world.build()
    try:
        # the baseline census is itself taken on a clone: the pristine world is never run on
        inst = world.clone("baseline")
        try:
            base_doc = inst.census()
        finally:
            inst.drop()
        base_cells = cells(base_doc)
        cmaps = [base_cells]
        records = []
        for p in plants:
            if only and p.id not in only:
                continue
            records.append(run_one(world, p, base_cells, f"p_{p.id[:24]}", extra=cmaps))
        stale = unplantable_stale(cmaps)
        mutation = run_mutation(work, db, {p.id: p for p in plants}, base_cells, mutants) if (mutants and not only) else \
            dict(suite_notices=None, mutants=[])
    finally:
        db.drop(world.base_db)
    if runtime_files_sha256() != files_before:
        raise HarnessError("a runtime file changed while the suite ran: the evidence would describe two different trees")
    covered = covered_checks(records)
    required = reg["required"]
    uncovered = sorted(c for c in required if c not in covered and c not in UNPLANTABLE)
    dirty = dirty_files()
    doc = dict(schema=SCHEMA, _doc=EVIDENCE_DOC, inspector_blob_sha256=hashlib.sha256(inspector).hexdigest(),
               harness_file_sha256=files_before[GEN_REL], runtime_files_sha256=files_before,
               inspector_tree_dirty=(None if dirty is None else INSPECTOR_REL in dirty), runtime_files_dirty=dirty,
               registry=dict(revision=reg["revision"], fingerprint=reg["fingerprint"]), partial=bool(only),
               plants=records, unplantable=dict(sorted(UNPLANTABLE.items())), unplantable_stale=stale,
               uncovered_required=uncovered, mutation=mutation)
    doc["harness_sha256"] = run_record_sha256(doc)
    return doc


def run_record_sha256(doc: dict) -> str:
    """sha256 of the canonical run record: the harness file hash, every runtime file hash, the inspector blob, the dirty flags, the registry
    identity, and every plant's verdicts and flags. INTEGRITY, not authenticity (see EVIDENCE_DOC): change a result, a file hash or a flag
    and it changes; but it is computed from the record's OWN fields, so it proves nothing about who produced them. The same code on the
    same inspector gives the same record (no clock, no path, no measured text, which carries a date)."""
    rec = dict(
        harness_file_sha256=doc.get("harness_file_sha256"), runtime_files_sha256=doc.get("runtime_files_sha256"),
        inspector_tree_dirty=doc.get("inspector_tree_dirty"), runtime_files_dirty=doc.get("runtime_files_dirty"),
        inspector_blob_sha256=doc["inspector_blob_sha256"], registry=doc["registry"], partial=doc.get("partial", False),
        plants=[{k: r.get(k) for k in ("id", "check", "asset", "planted", "detected", "verdict_before", "verdict_after", "collateral",
                                        "same_asset_effects", "restore_ok", "error")} for r in doc["plants"]],
        unplantable=doc["unplantable"], unplantable_stale=doc["unplantable_stale"], uncovered_required=doc["uncovered_required"],
        mutation=dict(suite_notices=doc["mutation"].get("suite_notices"),
                      mutants=[{k: m.get(k) for k in ("id", "check", "plant", "file", "noticed", "mutant_detected", "mutant_verdict_after")}
                               for m in doc["mutation"].get("mutants", [])]))
    return hashlib.sha256(json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _blob(rel: str, ref: str | None) -> bytes | None:
    """The bytes of `rel` at `ref` (git show), or in the working tree when `ref` is None; None when absent."""
    if ref is None:
        p = REPO / rel
        return p.read_bytes() if p.is_file() else None
    r = _git_out("show", f"{ref}:{rel}")
    return r.stdout if r.returncode == 0 else None


def verify_evidence(doc, ref: str | None = None) -> list:
    """The problems found when `doc` is checked the way a consumer must check it (empty list = consistent with the tree at `ref`, or the
    working tree). Checks: the schema; the record hash recomputed from the record's own fields; `harness_file_sha256` and every
    `runtime_files_sha256` entry against the file's bytes (git blob at `ref`); the set of hashed files equals the set this harness hashes
    (omitting a file is a problem); `inspector_blob_sha256` equals the inspector's entry; a dirty tree is a problem. This proves the
    evidence matches a tree; WHO produced it is the CI job's claim, not this function's."""
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        return [f"not a {SCHEMA} document"]
    why = []
    try:
        if run_record_sha256(doc) != doc.get("harness_sha256"):
            why.append("harness_sha256 does not equal the hash recomputed from the record's fields")
    except (KeyError, TypeError, AttributeError) as exc:
        return [f"the record is malformed ({type(exc).__name__}: {exc})"]
    files = doc.get("runtime_files_sha256")
    if not isinstance(files, dict):
        return why + ["runtime_files_sha256 is absent"]
    want = set(evidence_files())
    if set(files) != want:
        why.append(f"runtime_files_sha256 names {sorted(set(files) ^ want)} differently from the files this harness hashes")
    for rel in sorted(set(files) & want):
        b = _blob(rel, ref)
        got = None if b is None else hashlib.sha256(b).hexdigest()
        if got != files[rel]:
            why.append(f"{rel}: the evidence records {str(files[rel])[:12]}, the tree {'at ' + ref if ref else ''} has {str(got)[:12]}")
    if doc.get("harness_file_sha256") != files.get(GEN_REL):
        why.append("harness_file_sha256 does not equal the runtime_files_sha256 entry for the harness")
    if doc.get("inspector_blob_sha256") != files.get(INSPECTOR_REL):
        why.append("inspector_blob_sha256 does not equal the runtime_files_sha256 entry for the inspector")
    if doc.get("inspector_tree_dirty") is not False or doc.get("runtime_files_dirty") != []:
        why.append(f"the evidence was produced from a dirty or unknown tree (inspector_tree_dirty={doc.get('inspector_tree_dirty')!r}, "
                   f"runtime_files_dirty={doc.get('runtime_files_dirty')!r}): UNMEASURED")
    return why


def verdict(doc: dict) -> tuple[int, list]:
    """(exit code, reasons): 0 only if every plant was detected with no collateral, every plant restored (pristine world unchanged), every
    required check is covered or declared unplantable, no unplantable claim is stale, and every mutant was noticed."""
    why = []
    for r in doc["plants"]:
        if r.get("error"):
            why.append(f"{r['id']}: {r['error']}")
        elif not r.get("planted", True):
            why.append(f"{r['id']}: nothing was planted")
        elif not r["detected"]:
            why.append(f"{r['id']}: planted defect NOT detected ({r['check']} on {r['asset']}: {r['verdict_before']} -> {r['verdict_after']})")
        if r.get("collateral"):
            why.append(f"{r['id']}: collateral {r['collateral']}")
        if not r.get("restore_ok"):
            why.append(f"{r['id']}: the pristine world changed (not restored)")
    if doc["unplantable_stale"]:
        why += [f"unplantable claim stale: {x}" for x in doc["unplantable_stale"]]
    if doc.get("partial"):                               # a `--only` run is not a T1 record: no coverage or mutation claim is made or judged
        return (0 if not why else 2), why
    if doc["uncovered_required"]:
        why.append(f"required check(s) with no plant and no unplantable declaration: {doc['uncovered_required']}")
    if doc["mutation"].get("suite_notices") is not True:
        why.append("the mutated detector was not noticed by the suite" if doc["mutation"].get("mutants") else "no mutation result")
    return (0 if not why else 2), why


# ───────────────────────────── CLI ─────────────────────────────

def _cluster():
    """The governance tests' disposable PostgreSQL (loopback, trust, temp dir, deleted at exit). The only database this harness can reach."""
    sys.path.insert(0, str(HERE / "__tests__"))
    try:
        import _disposable_pg as dp
    except ImportError as exc:                          # the helper imports pytest
        raise HarnessError(f"the disposable-PostgreSQL helper could not be imported ({exc}): install pytest") from exc
    try:
        return dp.get_cluster(), dp
    except dp.PGUnavailable as exc:
        raise HarnessError(f"no PostgreSQL server binaries: {exc}") from exc
    except dp.PGStartError as exc:
        raise HarnessError(f"the disposable cluster would not start: {exc}") from exc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="E1.7 T1 plant harness (synthetic world, disposable PostgreSQL, no production access)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("run")
    r.add_argument("--only", default=None, help="comma list of plant ids: no mutation run, evidence marked `partial` (not a full T1 record)")
    r.add_argument("--out", default=None, help="write the nikasha_t1_evidence/1 JSON here")
    v = sub.add_parser("verify", help="check an evidence file the way a consumer must (record hash, file hashes against the tree, dirty flags)")
    v.add_argument("evidence")
    v.add_argument("--ref", default=None, help="git ref whose blobs the evidence must match (default: the working tree)")
    args = ap.parse_args(argv)
    if args.cmd == "list":
        for p in PLANTS:
            print(f"{p.id:24s} {p.check:24s} {p.asset}")
        for c, why in sorted(UNPLANTABLE.items()):
            print(f"{'(unplantable)':24s} {c:24s} {why}")
        return 0
    if args.cmd == "verify":
        try:
            doc = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"nikasha_plant: cannot read the evidence: {exc}", file=sys.stderr)
            return 5
        problems = verify_evidence(doc, args.ref)
        for pr in problems:
            print("FAIL:", pr, file=sys.stderr)
        print("evidence consistent with the tree" if not problems else f"{len(problems)} problem(s)")
        return 0 if not problems else 2
    only = set(args.only.split(",")) if args.only else None
    if only and not only <= {p.id for p in PLANTS}:
        print(f"nikasha_plant: unknown plant id(s): {sorted(only - {p.id for p in PLANTS})}", file=sys.stderr)
        return 5
    work = Path(tempfile.mkdtemp(prefix="nikasha_plant_"))

    def _term(signum, _frame):                            # SIGTERM / SIGHUP become SystemExit so the finally block stops the cluster and deletes the
        for sig in (signal.SIGTERM, signal.SIGHUP):       # temp dir (by default they kill the process with no cleanup); SIGINT already raises
            signal.signal(sig, signal.SIG_IGN)            # KeyboardInterrupt. A second signal during the cleanup is ignored.
        raise SystemExit(128 + signum)
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _term)
    try:
        cluster, _dp = _cluster()
        doc = run_suite(Db(cluster), work, only)
    except HarnessError as exc:
        print(f"nikasha_plant: {exc}", file=sys.stderr)
        return 5
    finally:
        shutil.rmtree(work, ignore_errors=True)
        dp = sys.modules.get("_disposable_pg")            # the helper may be mid-start when the signal lands: stop whatever it holds
        if dp is not None:
            dp.shutdown()
    code, why = verdict(doc)
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if args.out:
        tmp = Path(args.out).with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, args.out)
    for rec in doc["plants"]:
        print(f"{'ok ' if rec['detected'] and not rec['collateral'] else 'BAD'} {rec['id']:24s} {rec['check']:24s} "
              f"{rec['verdict_before']} -> {rec['verdict_after']}" + (f"  collateral={rec['collateral']}" if rec["collateral"] else ""))
    print(f"mutation: suite_notices={doc['mutation']['suite_notices']}  harness_sha256={doc['harness_sha256'][:16]}")
    for w in why:
        print("FAIL:", w, file=sys.stderr)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"nikasha_plant: script error: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(5)
