"""I.ARG (L2 half, SS N-61 / N-59 Q-L2-21): bo_karanajala READS L1's argala facts by fact_id.

CLAUDE.md N.5: L2 never re-derives an L1 value. The argala offsets, the paired obstruction offsets, the
Rahu/Ketu reversal and the occupancy all belong to ga_structural (`argala_graha_natal`, one row per
(target graha, source graha)). These tests:

  * feed L2 the rows the REAL L1 builder emits (`ga_structural_writer._build_argala_graha_rows`), so an L1
    contract change is caught here, not in production;
  * pin the output edge schema (columns, direction, relationship_class, cancelled_flag semantics unchanged);
  * pin that the edge set, the cancelled set and the cancelling grahas come from the L1 rows (corrected pairing
    4-10 / 11-3, the 5th offset, node reversal) and every edge cites its L1 fact_id;
  * pin the honest refusal when L1 rows are absent or malformed (never an invented edge);
  * run the fetch SQL against a disposable PostgreSQL (LIKE escaping, category/key pin, ordering).

No production access. Pure-unit except the one disposable-Postgres class.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import sys
from typing import Any

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import ga_writers.ga_structural_writer as l1  # noqa: E402
import pipeline.orchestrator.writers.bo_karanajala as k  # noqa: E402

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"
BUILD_ID = "build-test-argala"
NOW = "2026-10-05T00:00:00+00:00"
NODE_MAP = {("graha", g): f"node-{g.lower()}" for g in k.KNOWN_GRAHAS}


def l1_rows(signs: dict[str, int]) -> list[dict[str, Any]]:
    """The rows the real L1 builder emits for a D1 placement {graha: sign_num}."""
    state = {g: {"sign_num": n} for g, n in signs.items()}
    return l1._build_argala_graha_rows(state, "D1", CHART_ID, "l1-build", AYA, NOW, "pyjhora/1.0.0")


class FakeResult:
    def __init__(self, rows): self._rows = rows
    def fetchall(self): return self._rows


class FakeConn:
    """Returns L1-builder rows shaped as the fetch SELECT returns them (tuples)."""
    def __init__(self, rows, dict_rows=False):
        self._rows, self._dict = rows, dict_rows
        self.sql: list[str] = []
        self.params: list[Any] = []

    def execute(self, sql, params=None):
        self.sql.append(sql)
        self.params.append(params)
        out = []
        for r in self._rows:
            t = (r["fact_id"], r["fact_subject"], r["fact_key"], r["fact_value_jsonb"])
            out.append(dict(zip(("fact_id", "fact_subject", "fact_key", "fact_value_jsonb"), t)) if self._dict else t)
        return FakeResult(out)


def facts_for(signs: dict[str, int]) -> list[dict]:
    return k._fetch_argala_facts(FakeConn(l1_rows(signs)), CHART_ID, AYA)


def edges_for(signs: dict[str, int]) -> list[dict]:
    return k._build_argala_edges(CHART_ID, AYA, BUILD_ID, facts_for(signs), NODE_MAP, NOW)


def edge(edges: list[dict], src: str, tgt: str) -> dict:
    hits = [e for e in edges if e["from_node_id"] == NODE_MAP[("graha", src)]
            and e["to_node_id"] == NODE_MAP[("graha", tgt)]]
    assert len(hits) == 1, f"expected exactly one edge {src}->{tgt}, got {len(hits)}"
    return hits[0]


def no_edge(edges: list[dict], src: str, tgt: str) -> bool:
    return not [e for e in edges if e["from_node_id"] == NODE_MAP[("graha", src)]
                and e["to_node_id"] == NODE_MAP[("graha", tgt)]]


# ── 1. Contract with the real L1 builder ──────────────────────────────────────────────────────────

class TestEdgesAreTheL1Rows:
    SIGNS = {"Sun": 1, "Moon": 2, "Mars": 4, "Mercury": 1, "Jupiter": 11,
             "Venus": 2, "Saturn": 7, "Rahu": 10, "Ketu": 4}

    def test_one_edge_per_l1_row_and_each_cites_its_fact_id(self):
        rows = l1_rows(self.SIGNS)
        assert rows, "fixture produced no L1 rows"
        edges = edges_for(self.SIGNS)
        assert len(edges) == len(rows)
        by_fact = {r["fact_id"]: r for r in rows}
        cited = []
        for e in edges:
            ids = e["constituent_fact_ids_array"]
            assert len(ids) == 1 and ids[0] in by_fact, "edge must cite exactly the L1 fact it was read from"
            cited.append(ids[0])
            j = by_fact[ids[0]]["fact_value_jsonb"]
            assert e["from_node_id"] == NODE_MAP[("graha", j["source_graha"])]
            assert e["to_node_id"] == NODE_MAP[("graha", j["target_graha"])]
            props = json.loads(e["edge_properties_jsonb"])
            assert props["argala_position"] == j["argala_offset"]
            assert props["house_of_karaka_from_subject"] == j["argala_offset"]
            assert props["argala_subject"] == j["target_graha"]
            assert props["argala_karaka"] == j["source_graha"]
        assert sorted(cited) == sorted(by_fact), "every L1 argala row must become exactly one edge"

    def test_edge_schema_is_unchanged(self):
        e = edges_for(self.SIGNS)[0]
        assert e["edge_type"] == "argala"
        assert e["direction"] == "directed"
        assert e["semantic_path_class"] == "argala_intervention"
        assert e["active_duration_class"] == "natal_permanent"
        assert e["relationship_class"] in ("argala_positive", "argala_virodha")
        assert e["is_cross_subsystem"] is False
        assert e["subsystem_from"] == "parashari" and e["subsystem_to"] == "parashari"
        assert e["present_in_traditions_array"] == ["parashari"]
        assert e["cross_system_consensus_count"] == 1
        assert e["underlying_msr_signal_ids_array"] == []
        assert e["verification_pass_status"] == "documented_approximation"
        assert e["citation_ref"] == "BPHS_Ch28/argala"
        assert set(json.loads(e["edge_properties_jsonb"])) == {
            "argala_subject", "argala_karaka", "house_of_karaka_from_subject", "argala_position"}
        assert "constituent_ga_vichara_ids_array" in e and "computed_strength" in e

    def test_no_self_loop_and_unique_pair(self):
        edges = edges_for(self.SIGNS)
        assert all(e["from_node_id"] != e["to_node_id"] for e in edges)
        pairs = [(e["from_node_id"], e["to_node_id"]) for e in edges]
        assert len(pairs) == len(set(pairs))


# ── 2. Behaviour that now comes from L1, not from L2 ─────────────────────────────────────────────

class TestBehaviourComesFromL1:
    def test_second_from_benefic_is_positive_and_uncancelled(self):
        e = edge(edges_for({"Sun": 1, "Moon": 2}), "Moon", "Sun")
        assert e["relationship_class"] == "argala_positive"
        assert e["cancelled_flag"] is False and e["cancelled_by_jsonb"] is None
        assert json.loads(e["edge_properties_jsonb"])["argala_position"] == 2

    def test_malefic_is_virodha_and_cancelled_by_the_12th(self):
        e = edge(edges_for({"Sun": 1, "Saturn": 2, "Jupiter": 12}), "Saturn", "Sun")
        assert e["relationship_class"] == "argala_virodha"
        assert e["cancelled_flag"] is True
        p = json.loads(e["cancelled_by_jsonb"])
        assert p["cancelling_actors"] == ["Jupiter"]
        assert p["cancelling_roots"] == [{"actor": "Jupiter", "node_id": NODE_MAP[("graha", "Jupiter")],
                                          "virodha_position_from_target": 12}]
        assert p["target"] == {"actor": "Saturn", "target": "Sun",
                               "relationship_class": "argala_virodha", "argala_position": 2}
        assert p["original_polarity"] == -1 and p["resulting_role"] == "attenuated_opposition"

    def test_corrected_pairing_4th_is_obstructed_from_the_10th_not_the_3rd(self):
        # N-61: the BPHS pairing is 4-10 (the old L2 map said 4-3).
        three = edges_for({"Sun": 1, "Saturn": 4, "Jupiter": 3})
        assert edge(three, "Saturn", "Sun")["cancelled_flag"] is False, "Jupiter in the 3rd must not cancel the 4th"
        ten = edges_for({"Sun": 1, "Saturn": 4, "Jupiter": 10})
        e = edge(ten, "Saturn", "Sun")
        assert e["cancelled_flag"] is True
        assert json.loads(e["cancelled_by_jsonb"])["cancelling_roots"][0]["virodha_position_from_target"] == 10

    def test_corrected_pairing_11th_is_obstructed_from_the_3rd_not_the_10th(self):
        ten = edges_for({"Sun": 1, "Mars": 11, "Jupiter": 10})
        assert edge(ten, "Mars", "Sun")["cancelled_flag"] is False
        three = edges_for({"Sun": 1, "Mars": 11, "Jupiter": 3})
        e = edge(three, "Mars", "Sun")
        assert e["cancelled_flag"] is True
        assert json.loads(e["cancelled_by_jsonb"])["cancelling_roots"][0]["virodha_position_from_target"] == 3

    def test_fifth_offset_edge_exists_because_l1_lists_it(self):
        e = edge(edges_for({"Sun": 1, "Venus": 5}), "Venus", "Sun")
        assert json.loads(e["edge_properties_jsonb"])["argala_position"] == 5
        assert e["relationship_class"] == "argala_positive"

    def test_node_target_counts_in_reverse(self):
        # Rahu in Aries: its 2nd counted in reverse is Pisces (12). Forward-counting L2 would make Sun in Taurus the
        # 2nd-from-Rahu argala instead; L1 (reverse) makes Sun in Pisces the one.
        edges = edges_for({"Rahu": 1, "Sun": 12, "Mercury": 2})
        e = edge(edges, "Sun", "Rahu")
        assert json.loads(e["edge_properties_jsonb"])["argala_position"] == 2
        assert "counted in reverse" in e["citation_human"]
        assert no_edge(edges, "Mercury", "Rahu"), "forward 2nd of a node is not an argala"

    def test_forward_target_citation_has_no_reverse_note(self):
        e = edge(edges_for({"Sun": 1, "Moon": 2}), "Moon", "Sun")
        assert "reverse" not in e["citation_human"]
        assert e["citation_human"].startswith("Argala: Moon in 2nd from Sun")

    def test_empty_argala_sign_gives_no_edge(self):
        assert no_edge(edges_for({"Sun": 1, "Moon": 3}), "Moon", "Sun")

    def test_malefic_obstructor_only_cancels_malefic_argala(self):
        # Benefic argala with an obstructor stays uncancelled (unchanged L2 semantics; TI-L2-37 is out of scope).
        e = edge(edges_for({"Sun": 1, "Jupiter": 2, "Saturn": 12}), "Jupiter", "Sun")
        assert e["relationship_class"] == "argala_positive" and e["cancelled_flag"] is False
        assert e["cancelled_by_jsonb"] is None

    def test_cancelling_actors_are_sorted(self):
        e = edge(edges_for({"Sun": 1, "Saturn": 2, "Venus": 12, "Jupiter": 12}), "Saturn", "Sun")
        assert json.loads(e["cancelled_by_jsonb"])["cancelling_actors"] == ["Jupiter", "Venus"]

    def test_edge_without_a_node_is_skipped_not_invented(self):
        facts = facts_for({"Sun": 1, "Moon": 2})
        nm = {k_: v for k_, v in NODE_MAP.items() if k_ != ("graha", "Moon")}
        assert k._build_argala_edges(CHART_ID, AYA, BUILD_ID, facts, nm, NOW) == []


# ── 3. Refusals: L1 absent or malformed ──────────────────────────────────────────────────────────

class TestFetchRefusesBadFacts:
    def _row(self, **over):
        r = l1_rows({"Sun": 1, "Moon": 2})[0]
        r = {**r, "fact_value_jsonb": dict(r["fact_value_jsonb"])}
        for key, val in over.items():
            if key in r["fact_value_jsonb"]:
                r["fact_value_jsonb"][key] = val
            else:
                r[key] = val
        return r

    def test_dict_rows_and_json_string_value_are_accepted(self):
        rows = [self._row()]
        rows[0]["fact_value_jsonb"] = json.dumps(rows[0]["fact_value_jsonb"])
        assert len(k._fetch_argala_facts(FakeConn(rows, dict_rows=True), CHART_ID, AYA)) == 1

    @pytest.mark.parametrize("field,bad", [
        ("target_graha", "Pluto"), ("source_graha", None), ("argala_offset", None),
        ("obstruction_offset", "x"), ("obstructor_grahas", "Mars"), ("obstructor_grahas", ["Pluto"]),
    ])
    def test_malformed_fact_raises(self, field, bad):
        with pytest.raises(RuntimeError, match="argala_graha_natal fact_id="):
            k._fetch_argala_facts(FakeConn([self._row(**{field: bad})]), CHART_ID, AYA)

    @pytest.mark.parametrize("bad", [None, "", "sideways", "Forward"])
    def test_missing_or_unknown_count_direction_raises(self, bad):
        r = self._row()
        if bad is None:
            del r["fact_value_jsonb"]["count_direction"]
        else:
            r["fact_value_jsonb"]["count_direction"] = bad
        with pytest.raises(RuntimeError, match="count_direction"):
            k._fetch_argala_facts(FakeConn([r]), CHART_ID, AYA)

    def test_non_object_value_raises(self):
        with pytest.raises(RuntimeError, match="not an object"):
            k._fetch_argala_facts(FakeConn([self._row(fact_value_jsonb=[1])]), CHART_ID, AYA)

    def test_two_rows_for_one_pair_raise(self):
        r = self._row()
        with pytest.raises(RuntimeError, match="second argala row"):
            k._fetch_argala_facts(FakeConn([r, {**r, "fact_id": "other"}]), CHART_ID, AYA)

    def test_fetch_sql_pins_category_key_and_total_order(self):
        c = FakeConn([])
        k._fetch_argala_facts(c, CHART_ID, AYA)
        sql = " ".join(c.sql[0].split())
        assert "fact_category = 'argala_graha_natal'" in sql
        assert "fact_key LIKE" in sql
        assert "ORDER BY fact_subject, fact_key, fact_id" in sql
        assert c.params[0] == [CHART_ID, AYA]


# ── 4. The writer: reads L1, refuses to compute, cites ───────────────────────────────────────────

class _CountConn:
    """Answers the writer's closing rows-present COUNT(*) (WFIX-A) with a fixed figure; every other DB touch is stubbed."""
    def cursor(self):
        return self
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def execute(self, sql, params=None):
        assert sql.lstrip().startswith("SELECT (SELECT count(*) FROM bodha_cgm_edges"), sql
    def fetchone(self):
        return {"n": 7}


class _Ctx:
    dry_run = False
    build_id = "00000000-0000-0000-0000-000000000001"
    config = {"chart_id": CHART_ID}
    db_conn = object()


@pytest.fixture
def stubbed_writer(monkeypatch):
    """Run BoKaranajalaWriter.run() with every DB touch stubbed; capture the edges handed to _batch_insert."""
    import bodha_writers._idempotency as idem
    captured: dict[str, Any] = {"edges": []}
    monkeypatch.setattr(k, "CANONICAL_AYAS", [AYA])
    monkeypatch.setattr(k, "_fetch_signals", lambda *a: [])
    monkeypatch.setattr(k, "_fetch_node_map", lambda *a: dict(NODE_MAP))
    monkeypatch.setattr(k, "_fetch_graha_sign_numbers", lambda *a: {"Sun": 1, "Moon": 2})
    monkeypatch.setattr(k, "_fetch_graha_sign_fact_ids", lambda *a: {})
    monkeypatch.setattr(k, "_fetch_bhava_lordship_facts", lambda *a: [])
    monkeypatch.setattr(k, "_fetch_occupancy_facts", lambda *a: [])
    monkeypatch.setattr(k, "_fetch_graha_bhava_aspect_facts", lambda *a: [])
    monkeypatch.setattr(k, "ViharaLookups", lambda *a, **kw: None)
    monkeypatch.setattr(k, "_build_arudha_special_lagna_nodes_and_edges", lambda *a, **kw: (0, []))
    monkeypatch.setattr(k, "assign_deterministic_edge_ids", lambda conn, edges: None)
    monkeypatch.setattr(k, "assign_deterministic_contradiction_ids", lambda conn, rows: None)
    monkeypatch.setattr(idem, "replace_prior_cgm_edges", lambda *a: None)
    monkeypatch.setattr(k, "_replace_prior_arudha_special_lagna_nodes", lambda *a: None)
    monkeypatch.setattr(idem, "replace_prior_contradictions", lambda *a: None)
    monkeypatch.setattr(_Ctx, "db_conn", _CountConn())   # WFIX-A: the final rows-present COUNT(*) is a DB touch too

    def _bi(conn, rows, sql):
        if sql is k._EDGE_INSERT:
            captured["edges"] = list(rows)
        return len(rows)
    monkeypatch.setattr(k, "_batch_insert", _bi)
    return captured


def _run():
    return k.BoKaranajalaWriter().run(_Ctx())


class TestWriterRun:
    def test_run_emits_the_l1_argala_edges_and_cites_them(self, stubbed_writer, monkeypatch):
        rows = l1_rows({"Sun": 1, "Moon": 2})
        facts = k._fetch_argala_facts(FakeConn(rows), CHART_ID, AYA)
        monkeypatch.setattr(k, "_fetch_argala_facts", lambda *a: facts)
        _run()
        argala = [e for e in stubbed_writer["edges"] if e["edge_type"] == "argala"]
        assert [e["constituent_fact_ids_array"] for e in argala] == [[r["fact_id"]] for r in rows]

    def test_run_never_recomputes_argala_from_sign_numbers(self, stubbed_writer, monkeypatch):
        # graha_signs say Moon is 2nd from Sun (the old L2 computation would emit Moon->Sun); L1 returns one
        # unrelated pair. Only the L1 pair may appear.
        rows = l1_rows({"Mars": 5, "Venus": 6})
        facts = k._fetch_argala_facts(FakeConn(rows), CHART_ID, AYA)
        monkeypatch.setattr(k, "_fetch_argala_facts", lambda *a: facts)
        _run()
        argala = [e for e in stubbed_writer["edges"] if e["edge_type"] == "argala"]
        assert len(argala) == len(rows)
        assert not any(e["from_node_id"] == NODE_MAP[("graha", "Moon")] and e["edge_type"] == "argala"
                       for e in argala)

    def test_run_halts_when_l1_argala_rows_are_absent(self, stubbed_writer, monkeypatch):
        monkeypatch.setattr(k, "_fetch_argala_facts", lambda *a: [])
        with pytest.raises(RuntimeError, match="0 argala_graha_natal rows"):
            _run()
        assert stubbed_writer["edges"] == [], "nothing may be written when the L1 facts are missing"


# ── 5. No local argala definition survives ───────────────────────────────────────────────────────

class TestNoLocalArgalaDefinition:
    SRC = pathlib.Path(k.__file__).read_text()

    def test_removed_names_are_gone(self):
        for name in ("ARGALA_POSITIONS", "VIRODHA_POSITIONS", "_house_of_b_from_a", "ARGALA_TO_VIRODHA",
                     "_ARGALA_DEFAULT_SIGN_NUMBERS"):
            assert not hasattr(k, name), name
        defined = {n.name for n in ast.walk(ast.parse(self.SRC)) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        assert "_house_of_b_from_a" not in defined
        assigned = {t.id for n in ast.walk(ast.parse(self.SRC)) if isinstance(n, (ast.Assign, ast.AnnAssign))
                    for t in (n.targets if isinstance(n, ast.Assign) else [n.target]) if isinstance(t, ast.Name)}
        assert not assigned & {"ARGALA_POSITIONS", "VIRODHA_POSITIONS", "ARGALA_TO_VIRODHA"}

    def test_builder_takes_l1_facts_not_sign_positions(self):
        import inspect
        params = list(inspect.signature(k._build_argala_edges).parameters)
        assert "graha_signs" not in params and "argala_facts" in params

    def test_writer_reads_the_l1_category_by_fact_id(self):
        assert "argala_graha_natal" in self.SRC
        assert "constituent_fact_ids_array\": [fact[\"fact_id\"]]" in self.SRC


# ── 6. The fetch SQL on a real (disposable) PostgreSQL ───────────────────────────────────────────

from tests.pg_disposable import pg, psql, q, new_db, requires_pg, HAVE_PG  # noqa: E402,F401


@requires_pg
class TestFetchOnRealPostgres:
    def _conn(self, port, db):
        import psycopg
        return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=db, autocommit=True)

    def test_fetch_selects_only_the_category_rows_in_total_order(self, pg):
        db = new_db(pg)
        q(pg, db, """CREATE TABLE chart_facts (fact_id text, chart_id uuid, ayanamsha_id text, fact_category text,
                      fact_subject text, fact_key text, fact_value_jsonb jsonb)""")
        rows = l1_rows({"Sun": 1, "Moon": 2, "Saturn": 4, "Jupiter": 10, "Rahu": 12, "Venus": 5})
        with self._conn(pg, db) as c:
            ins = ("INSERT INTO chart_facts VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)")
            for r in rows:
                c.execute(ins, (r["fact_id"], CHART_ID, AYA, "argala_graha_natal", r["fact_subject"],
                                r["fact_key"], json.dumps(r["fact_value_jsonb"])))
            # noise that a loose selector would pick up
            c.execute(ins, ("n1", CHART_ID, AYA, "argala_graha_natal", "D1_SUN", "summary", "{}"))
            c.execute(ins, ("n2", CHART_ID, AYA, "argala_graha_natal", "D1_SUN", "fromXMARXoffsetX2", "{}"))
            c.execute(ins, ("n3", CHART_ID, AYA, "argala_natal_matrix", "D1_SUN", "from_MAR_offset_2", "{}"))
            c.execute(ins, ("n4", CHART_ID, "raman", "argala_graha_natal", "D1_SUN", "from_MAR_offset_2", "{}"))
            c.execute(ins, ("n5", "11111111-1111-1111-1111-111111111111", AYA, "argala_graha_natal",
                            "D1_SUN", "from_MAR_offset_2", "{}"))
            got = k._fetch_argala_facts(c, CHART_ID, AYA)
        assert sorted(f["fact_id"] for f in got) == sorted(r["fact_id"] for r in rows)
        order = [(r["fact_subject"], r["fact_key"]) for r in sorted(rows, key=lambda r: (r["fact_subject"], r["fact_key"], r["fact_id"]))]
        with self._conn(pg, db) as c:
            ids = [r[0] for r in c.execute(
                "SELECT fact_id FROM chart_facts WHERE fact_category='argala_graha_natal' AND fact_key LIKE 'from\\_%%\\_offset\\_%%' AND chart_id=%s AND ayanamsha_id=%s ORDER BY fact_subject, fact_key, fact_id",
                (CHART_ID, AYA)).fetchall()]
        assert [f["fact_id"] for f in got] == ids
        assert len(order) == len(got)
