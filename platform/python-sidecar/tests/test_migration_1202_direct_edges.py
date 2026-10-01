"""
Migration 1202 (Suvarna Track I): direct `depends_on` edges for reads that were ordered only
transitively (E6 `Build.dag` reads-match, T4).

DB-free. What this proves, and what it does not:
  * PROVES: the migration and the TypeScript seed carry the same 27 edges; every id exists; the
    full 127-asset registry graph stays acyclic; every added edge was already implied by an existing
    path (so no build ordering changes); the 3 known BACK-READ edges (which would create cycles) are
    absent; every producer and consumer has a registered writer class.
  * HAS TEETH: the cycle checker is shown to flag a real back-read edge (see the mutation test).
  * DOES NOT PROVE the live registry state (that is the read-only verification SQL run after deploy),
    nor the E6 detector verdicts (the detector lives on the E6 lane; the offline before/after run is
    recorded in the Track I evidence file, not re-run here).

Pre-state graph: tests/fixtures/registry_depends_on_pre_1202.json (frozen reconstruction of the live
active registry; see its `_provenance`). The seed's depends_on is bootstrap-only (a re-seed never
rewrites an existing row), so the seed and the pre-state graph legitimately differ on edges owned by
earlier migrations; this test therefore asserts that the seed CONTAINS every 1202 edge, not that the
two graphs are equal.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from pipeline.orchestrator import dag_edge_guard as g

_REPO = Path(__file__).resolve().parents[3]
_MIGRATION = _REPO / "platform" / "migrations" / "1202_asset_registry_direct_edges.sql"
_SEED = _REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"
_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "registry_depends_on_pre_1202.json"

# Reads whose direct edge would close a cycle (ruled out of 1202; registry/design findings).
_BACK_READS = {
    ("ka_bhavishya_lekha", "ph_nimitta"),
    ("ga_structural", "ga_vichara"),
    ("ga_structural", "ga_yoga"),
}


def _migration_edges() -> list[tuple[str, str]]:
    sql = _MIGRATION.read_text()
    # only the INSERT ... VALUES block that fills the temp table
    m = re.search(r"INSERT INTO _m1202_edges \(asset_id, dep\) VALUES\s*(.*?);", sql, re.S)
    assert m, "edge VALUES block not found in migration 1202"
    return re.findall(r"\(\s*'([a-z0-9_]+)'\s*,\s*'([a-z0-9_]+)'\s*\)", m.group(1))


def _seed_graph() -> dict[str, list[str]]:
    src = _SEED.read_text()
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"asset_id:\s*'([a-z0-9_]+)'", src):
        nxt = re.search(r"asset_id:\s*'", src[m.end():])
        block = src[m.end(): m.end() + nxt.start()] if nxt else src[m.end():]
        d = re.search(r"^[ \t]+depends_on:\s*\[(.*?)\]", block, re.S | re.M)
        if d:
            out[m.group(1)] = re.findall(r"'([a-z0-9_]+)'", d.group(1))
    return out


def _pre_graph() -> dict[str, list[str]]:
    return json.loads(_FIXTURE.read_text())["edges"]


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Return one cycle (list of ids) or None. Iterative DFS, white/grey/black."""
    colour: dict[str, int] = {}
    for root in graph:
        if colour.get(root):
            continue
        stack = [(root, iter(sorted(graph.get(root, ()))))]
        colour[root] = 1
        path = [root]
        while stack:
            node, it = stack[-1]
            for nxt in it:
                if nxt not in graph:
                    continue
                c = colour.get(nxt, 0)
                if c == 1:
                    return path[path.index(nxt):] + [nxt]
                if c == 0:
                    colour[nxt] = 1
                    path.append(nxt)
                    stack.append((nxt, iter(sorted(graph[nxt]))))
                    break
            else:
                colour[node] = 2
                path.pop()
                stack.pop()
    return None


def _reaches(graph: dict[str, list[str]], src: str, dst: str) -> bool:
    seen, todo = set(), [src]
    while todo:
        x = todo.pop()
        for y in graph.get(x, ()):
            if y == dst:
                return True
            if y not in seen:
                seen.add(y)
                todo.append(y)
    return False


def _registered_writers() -> set[str]:
    ids: set[str] = set()
    for root in g._WRITER_ROOTS:
        for f in root.rglob("*.py"):
            if "tests" in f.parts or "__tests__" in f.parts:
                continue
            ids.update(g._REGISTER_RE.findall(f.read_text(errors="ignore")))
    return ids


# ── migration shape ──────────────────────────────────────────────────────────

def test_migration_shape_and_count():
    sql = _MIGRATION.read_text()
    edges = _migration_edges()
    assert len(edges) == 27 and len(set(edges)) == 27, "27 distinct edges expected"
    assert len({a for a, _ in edges}) == 15, "15 consumer assets expected"
    assert "SET LOCAL lock_timeout = '5s';" in sql
    # migrate.ts owns BEGIN/COMMIT; a nested BEGIN/COMMIT would end its transaction early
    code = "\n".join(l for l in sql.splitlines() if not l.lstrip().startswith("--"))
    assert not re.search(r"\b(BEGIN|COMMIT)\b\s*;", code), "migration must not open/close its own transaction"
    # `ON COMMIT DROP` on the temp table is the only DROP allowed
    assert not re.search(r"(?<!COMMIT\s)\b(DROP|TRUNCATE|DELETE\s+FROM|INSERT\s+INTO\s+asset_registry)\b", code, re.I)
    # the only column written on asset_registry is depends_on (SET LOCAL has no `=` after SET)
    sets = re.findall(r"\bSET\s+([a-z_]+)\s*=", code, re.I)
    assert sets == ["depends_on"], sets
    assert not any(a == b for a, b in edges), "self-edge"


def test_back_reads_are_not_added_anywhere():
    edges = set(_migration_edges())
    assert not (edges & _BACK_READS), edges & _BACK_READS
    seed = _seed_graph()
    for a, d in _BACK_READS:
        assert d not in seed.get(a, []), (a, d)


# ── ids exist; seed and migration agree ──────────────────────────────────────

def test_every_edge_id_exists_in_seed_and_pre_state():
    seed, pre = _seed_graph(), _pre_graph()
    for a, d in _migration_edges():
        assert a in seed and d in seed, (a, d, "missing from seed")
        assert a in pre and d in pre, (a, d, "missing from active registry (inactive/absent asset)")


def test_seed_contains_every_migration_edge():
    seed = _seed_graph()
    missing = [(a, d) for a, d in _migration_edges() if d not in seed[a]]
    assert not missing, f"seed does not carry migration 1202 edges: {missing}"


def test_migration_is_not_a_noop_against_pre_state():
    pre = _pre_graph()
    already = [(a, d) for a, d in _migration_edges() if d in pre[a]]
    assert not already, f"edges already present in the pre-state registry: {already}"


# ── graph properties ─────────────────────────────────────────────────────────

def test_registry_graph_acyclic_after_edges():
    pre = {a: set(v) for a, v in _pre_graph().items()}
    assert _find_cycle(pre) is None, "pre-state fixture itself has a cycle"
    post = {a: set(v) for a, v in pre.items()}
    for a, d in _migration_edges():
        post[a].add(d)
    assert _find_cycle(post) is None


def test_seed_graph_acyclic():
    """The seed runs its own cycle check at runSeed(); mirror it so a bad seed edit fails in CI,
    not at the next deploy-time reseed."""
    seed = {a: set(v) for a, v in _seed_graph().items()}
    assert len(seed) >= 125
    assert _find_cycle(seed) is None


def test_every_added_edge_was_already_implied_transitively():
    """Ordering cannot change: each new direct edge A->P duplicates an existing path A ~> P."""
    pre = _pre_graph()
    novel = [(a, d) for a, d in _migration_edges() if not _reaches(pre, a, d)]
    assert not novel, f"edges that introduce a NEW ordering constraint: {novel}"


def test_producers_and_consumers_have_registered_writers():
    writers = _registered_writers()
    ids = {x for e in _migration_edges() for x in e}
    missing = sorted(i for i in ids if i not in writers)
    assert not missing, f"asset(s) with no @register writer (nothing builds them): {missing}"


# ── the checker can fail (teeth) ─────────────────────────────────────────────

def test_cycle_checker_flags_a_known_back_read():
    pre = {a: set(v) for a, v in _pre_graph().items()}
    for a, d in _BACK_READS:
        mutated = {k: set(v) for k, v in pre.items()}
        mutated[a].add(d)
        cyc = _find_cycle(mutated)
        assert cyc is not None and a in cyc and d in cyc, (a, d, cyc)
