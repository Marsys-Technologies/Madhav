"""test_l0_asset_snapshot.py -- l0_asset_snapshot.py: read-only per-asset counts + content digests with the dispatch tool's own digest.

Proof map
  parity      the unit the snapshot composes equals the unit `declared_unit_or_refuse` composes for every asset the tool accepts; the snapshot
              reads through gad.read_fingerprint (no digest of its own)
  coverage    every one of the 40 registry assets appears; undeclared ones get a count only
  real SQL    a disposable Postgres: the snapshot of bg_vastu_directions equals the digest the tool's reader returns; a changed row flips it;
              the session is read-only (a write attempt is refused); --compare reads IDENTICAL / CHANGED
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import fingerprint_declarations as fd  # noqa: E402
import l0_asset_snapshot as snap  # noqa: E402
import suvarna_global_asset_dispatch as gad  # noqa: E402
import suvarna_level_wave as slw  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401

REPO = HERE.parents[3]
DECLS = fd.load_declarations()
REGISTRY = json.loads(snap.DEFAULT_REGISTRY_SNAPSHOT.read_text(encoding="utf-8"))
IDS = [r["asset_id"] for r in REGISTRY]


def test_registry_snapshot_has_forty_l0_assets():
    assert len(IDS) == 40 and len(set(IDS)) == 40


def test_unit_matches_the_tools_unit_for_every_asset_the_tool_accepts():
    checked = 0
    for r in REGISTRY:
        a = r["asset_id"]
        if not r["has_writer"]:
            continue
        sibs = gad.writer_siblings(str(REPO), a)
        for allow in (False, True):
            try:
                tool_unit = gad.declared_unit_or_refuse(DECLS, a, sibs, allow_excluded_partial=allow)
            except slw.LevelWaveRefusal:
                continue
            mine, note = snap.unit_for_snapshot(DECLS, a, sibs)
            assert mine == tool_unit, (a, mine, tool_unit)
            checked += 1
    assert checked >= 25


def test_snapshot_uses_the_tools_reader_and_covers_all_assets_with_a_fake_reader():
    calls = []

    def fake_reader(conn, decls, units, **kw):
        calls.append(tuple(units))
        sha = {u: {t: {"sha256": ("%064x" % (len(t) + 1)), "rows": 3} for t in decls.tables(u)} for u in units}
        return {"definition": fd.FINGERPRINT_DEFINITION, "declarations_sha256": decls.sha256,
                "fingerprints": {u: fd.composite_fingerprint({t: v["sha256"] for t, v in sha[u].items()}) for u in units}, "tables": sha}

    class Cur:
        def __init__(self): self.q = None
        def execute(self, q, *a): self.q = q
        def fetchone(self): return (7,)

    class Conn:
        def cursor(self): return Cur()
        def rollback(self): pass
        def close(self): pass

    doc = snap.build_snapshot(repo=str(REPO), registry=REGISTRY, decls=DECLS, connect=lambda: Conn(), reader=fake_reader)
    assert sorted(doc["assets"]) == sorted(IDS)
    declared = [a for a, v in doc["assets"].items() if v["status"] == "declared"]
    assert "bg_vastu_directions" in declared and "bg_cohort" in declared and "bg_ontology" in declared
    for a in ("bg_panchanga", "bg_ephemeris_engine", "bg_sarvatobhadra_grid", "bg_compendium_index"):
        assert doc["assets"][a]["status"] == "undeclared", a
    # the shared-ontology members fingerprint the whole shared table
    assert doc["assets"]["bg_doshas"]["unit"] == "bg_doshas+grp_brahma_ontology"
    assert doc["assets"]["bg_ontology"]["unit"] == "grp_brahma_ontology"
    assert doc["assets"]["bg_transit_rules"]["unit"] == "grp_bg_transit_seed"
    assert calls                                                       # every declared read went through the injected (the tool's) reader


def test_unknown_asset_is_refused():
    with pytest.raises(ValueError):
        snap.build_snapshot(repo=str(REPO), registry=REGISTRY, decls=DECLS, connect=lambda: None, assets=["bg_nope"])


def test_compare_verdicts():
    a = {"assets": {"x": {"status": "declared", "unit": "x", "composite": "a" * 64, "tables": {"t": {"sha256": "a" * 64, "rows": 2}}, "total_rows": 2},
                    "y": {"status": "declared", "unit": "y", "composite": "b" * 64, "tables": {"t": {"sha256": "b" * 64, "rows": 2}}, "total_rows": 2}}}
    b = json.loads(json.dumps(a))
    b["assets"]["y"]["composite"] = "c" * 64
    b["assets"]["y"]["tables"]["t"] = {"sha256": "c" * 64, "rows": 3}
    b["assets"]["y"]["total_rows"] = 3
    v = {r["asset"]: r for r in snap.compare(a, b)}
    assert v["x"]["verdict"] == "IDENTICAL" and v["y"]["verdict"] == "CHANGED" and v["y"]["changed_tables"] == ["t"]


# ───────────────────────── real SQL on a disposable Postgres ─────────────────────────

def _make_tables(cl, units):
    """Create the declared tables of `units` from the committed schema extract (types only) and return {table: column list without identity}."""
    ext = fd.load_schema_extract()["tables"]
    made = {}
    for u in units:
        for t in DECLS.tables(u):
            cols = ext[t]["columns"]
            ddl = ", ".join(f'"{c}" {m["type"]}' + (" GENERATED BY DEFAULT AS IDENTITY" if m["identity"] else "") + (" NOT NULL" if m["not_null"] and not m["identity"] else "")
                            for c, m in sorted(cols.items()))
            cl.psql(f'CREATE TABLE "{t}" ({ddl})')
            made[t] = [c for c, m in sorted(cols.items()) if not m["identity"]]
    return made


def _val(typ, i):
    if typ in ("integer", "bigint", "smallint"):
        return str(i)
    if typ in ("numeric", "double precision", "real"):
        return str(i + 0.5)
    if typ == "boolean":
        return "true"
    if typ.startswith("timestamp"):
        return "'2026-01-0%dT00:00:00'" % (i % 9 + 1)
    if typ == "jsonb" or typ == "json":
        return "'{\"k\": %d}'" % i
    if typ == "date":
        return "'2026-01-0%d'" % (i % 9 + 1)
    return "'v%d'" % i


def test_real_postgres_digest_equals_tools_reader_and_is_read_only(disposable_pg, monkeypatch):
    cl = disposable_pg
    ext = fd.load_schema_extract()["tables"]
    made = _make_tables(cl, ["bg_vastu_directions"])
    for t, cols in made.items():
        nk = DECLS.table_declaration("bg_vastu_directions", t)["natural_key"]
        for i in range(1, 4):
            vals = []
            for c in cols:
                vals.append(("'k%d'" % i) if c in nk and ext[t]["columns"][c]["type"] == "text" else _val(ext[t]["columns"][c]["type"], i))
            cl.psql(f'INSERT INTO "{t}" ({", ".join(chr(34) + c + chr(34) for c in cols)}) VALUES ({", ".join(vals)})')
    for k, v in cl.env().items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    connect = snap._psycopg_ro_connect(None)                              # the libpq-environment path (what rq.sh's pgenv gives)
    doc = snap.build_snapshot(repo=str(REPO), registry=REGISTRY, decls=DECLS, connect=connect, assets=["bg_vastu_directions"])
    rec = doc["assets"]["bg_vastu_directions"]
    assert rec["status"] == "declared" and rec["total_rows"] == 6
    tool = gad.read_fingerprint(connect, DECLS, "bg_vastu_directions")            # the dispatch tool's own function: the same value, byte for byte
    assert rec["composite"] == tool["composite"] and rec["tables"] == tool["tables"]
    # a changed row flips the digest, a rebuild-style id renumbering does not
    cl.psql("UPDATE bg_vastu_directions SET classical_citation = 'changed' WHERE direction = 'k1'")
    after = snap.build_snapshot(repo=str(REPO), registry=REGISTRY, decls=DECLS, connect=connect, assets=["bg_vastu_directions"])
    v = snap.compare(doc, after)[0]
    assert v["verdict"] == "CHANGED" and v["changed_tables"] == ["bg_vastu_directions"] and v["rows_before"] == v["rows_after"] == 6
    cl.psql("UPDATE bg_vastu_directions SET id = id + 1000")
    again = snap.build_snapshot(repo=str(REPO), registry=REGISTRY, decls=DECLS, connect=connect, assets=["bg_vastu_directions"])
    assert snap.compare(after, again)[0]["verdict"] == "IDENTICAL"
    # the session is READ ONLY
    conn = connect()
    try:
        cur = conn.cursor()
        with pytest.raises(Exception) as ei:
            cur.execute("DELETE FROM bg_vastu_directions")
        assert "read-only" in str(ei.value).lower()
        conn.rollback()
    finally:
        conn.close()
    assert cl.psql("SELECT count(*) FROM bg_vastu_directions") == "3"
    # an undeclared asset: a count of its registry target table
    cl.psql("CREATE TABLE bg_sarvatobhadra_grid (x int)")
    und = snap.build_snapshot(repo=str(REPO), registry=REGISTRY, decls=DECLS, connect=connect, assets=["bg_sarvatobhadra_grid"])
    assert und["assets"]["bg_sarvatobhadra_grid"]["status"] == "undeclared" and und["assets"]["bg_sarvatobhadra_grid"]["total_rows"] == 0
