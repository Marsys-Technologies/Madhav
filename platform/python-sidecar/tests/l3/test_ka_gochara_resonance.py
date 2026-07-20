"""Tests for ka_gochara_resonance (D-5 Lane G-1 — Resonance Map)."""
import re
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_gochara_resonance.writer import (
    TARGET_EVENT_CLASSES,
    _base_row,
    _build_arudha_rows,
    _build_bhava_rows,
    _build_dasha_portfolio_rows,
    _build_karaka_rows,
    _build_lord_rows,
    _build_mechanism_rows,
    _build_sensitive_degree_rows,
    _build_yoga_rows,
    _parse_house_ints,
    build_resonance_rows,
)

WRITER_PATH = Path(__file__).parent.parent.parent / "services/ka_gochara_resonance/writer.py"
SHIM_PATH = Path(__file__).parent.parent.parent / "pipeline/orchestrator/writers/ka_gochara_resonance.py"
MIGRATION_PATH = (
    Path(__file__).parent.parent.parent.parent / "migrations/459_gochara_resonance_map.sql"
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


# ── Pure helper unit tests ────────────────────────────────────────────────────

class TestParseHouseInts:
    def test_numeric_strings(self):
        assert _parse_house_ints(["7", "2"]) == [2, 7]

    def test_drops_non_numeric(self):
        assert _parse_house_ints(["8L", "maraka lords (2L/7L)", "4"]) == [4]

    def test_dedupes_and_sorts(self):
        assert _parse_house_ints(["11", "2", "11"]) == [2, 11]

    def test_empty(self):
        assert _parse_house_ints([]) == []
        assert _parse_house_ints(None) == []


class TestBuildBhavaLordKaraka:
    def test_bhava_rows(self):
        rows = _build_bhava_rows("marriage", ["7", "2"], "BPHS ch.7 (vivaha)")
        assert {r["target_ref"] for r in rows} == {"2", "7"}
        assert all(r["target_type"] == "bhava" for r in rows)
        assert all(r["classical_citation"] == "BPHS ch.7 (vivaha)" for r in rows)
        assert all(r["uncited_extension"] is False for r in rows)

    def test_lord_rows_dedupe(self):
        rows = _build_lord_rows("major_gain", ["2L", "11L", "2L"], "BPHS ch.2,11")
        assert len(rows) == 2
        assert {r["target_ref"] for r in rows} == {"2L", "11L"}

    def test_karaka_rows(self):
        rows = _build_karaka_rows("marriage", ["Venus"], "BPHS ch.7 (vivaha)")
        assert len(rows) == 1
        assert rows[0]["target_ref"] == "Venus"
        assert rows[0]["target_type"] == "karaka"

    def test_bhava_rows_no_citation_still_shaped(self):
        """A citation-less call still produces valid rows (caller decides
        uncited_extension upstream — this helper always marks False, matching
        its real callsite where an ontology citation is always attempted)."""
        rows = _build_bhava_rows("x", ["1"], None)
        assert rows[0]["classical_citation"] is None
        assert rows[0]["uncited_extension"] is False


class TestBuildMechanismRows:
    def test_mechanism_rows_from_transit_rules(self):
        transit_rows = [
            {"id": 34, "rule_type": "favourable", "graha": "venus", "primary_house": 2,
             "classical_citation": "BPHS Ch.29 (Gochara Phala — Transit Results)"},
            {"id": 47, "rule_type": "unfavourable", "graha": "venus", "primary_house": 7,
             "classical_citation": "BPHS Ch.29 (Gochara Phala — Transit Results)"},
        ]
        rows = _build_mechanism_rows("marriage", transit_rows)
        assert len(rows) == 2
        fav = next(r for r in rows if r["target_ref"] == "venus:favourable:h2")
        assert fav["weight"] == 1.0
        assert fav["source_rule_id"] == 34
        assert fav["uncited_extension"] is False
        unfav = next(r for r in rows if r["target_ref"] == "venus:unfavourable:h7")
        assert unfav["weight"] == -1.0

    def test_double_transit_weight(self):
        rows = _build_mechanism_rows("major_gain", [
            {"id": 133, "rule_type": "double_transit", "graha": "Jupiter", "primary_house": 2,
             "classical_citation": "Phaladeepika ch.26 §double-gochara"},
        ])
        assert rows[0]["weight"] == 0.75
        # graha is lowercased in target_ref regardless of source casing
        assert rows[0]["target_ref"] == "jupiter:double_transit:h2"

    def test_empty_transit_rules(self):
        assert _build_mechanism_rows("marriage", []) == []


class TestExtensionTargetTypes:
    """sensitive_degree / arudha / yoga_constituent / dasha_lord_portfolio are
    this writer's own synthesis: always uncited_extension=True, citation=None
    (§ writer.py module docstring — never dress an inferred event-class
    linkage up as classically-cited just because the underlying primitive is)."""

    def test_sensitive_degree_rows(self):
        rows = _build_sensitive_degree_rows("marriage", [
            {"fact_id": "abc123", "fact_subject": "VEN", "fact_key": "mrityu_bhaga"},
        ])
        assert len(rows) == 1
        assert rows[0]["target_type"] == "sensitive_degree"
        assert rows[0]["target_ref"] == "abc123"
        assert rows[0]["classical_citation"] is None
        assert rows[0]["uncited_extension"] is True

    def test_arudha_rows(self):
        rows = _build_arudha_rows("marriage", [{"fact_id": "arudha1", "fact_subject": "ARUDHA_A7"}])
        assert rows[0]["uncited_extension"] is True
        assert rows[0]["classical_citation"] is None

    def test_yoga_rows(self):
        rows = _build_yoga_rows("major_gain", [{"yoga_canonical_id": "dhana_yoga_2_5_9_11"}])
        assert rows[0]["target_ref"] == "dhana_yoga_2_5_9_11"
        assert rows[0]["uncited_extension"] is True

    def test_dasha_portfolio_rows_dedupe(self):
        rows = _build_dasha_portfolio_rows("major_gain", [
            {"lord_graha": "Jupiter"}, {"lord_graha": "Jupiter"}, {"lord_graha": "Mercury"},
        ])
        assert len(rows) == 2
        assert {r["target_ref"] for r in rows} == {"Jupiter", "Mercury"}


class TestBuildResonanceRows:
    def test_combines_all_target_types(self):
        rows = build_resonance_rows(
            "marriage",
            houses=["7", "2"], lords=["7L"], karakas=["Venus"],
            ontology_citation="BPHS ch.7 (vivaha)",
            transit_rule_rows=[
                {"id": 34, "rule_type": "favourable", "graha": "venus", "primary_house": 2,
                 "classical_citation": "BPHS Ch.29"},
            ],
            sensitive_fact_rows=[{"fact_id": "f1", "fact_subject": "VEN", "fact_key": "mrityu_bhaga"}],
            arudha_fact_rows=[{"fact_id": "f2", "fact_subject": "ARUDHA_A7"}],
            yoga_firing_rows=[{"yoga_canonical_id": "some_yoga"}],
            dasha_rows=[{"lord_graha": "Venus"}],
        )
        target_types = {r["target_type"] for r in rows}
        assert target_types == {
            "bhava", "lord", "karaka", "mechanism_node",
            "sensitive_degree", "arudha", "yoga_constituent", "dasha_lord_portfolio",
        }

    def test_dedup_on_target_type_and_ref(self):
        """Two identical (target_type, target_ref) pairs collapse to one row —
        matches the table's UNIQUE(chart_id, event_class, target_type, target_ref)."""
        rows = build_resonance_rows(
            "marriage", houses=["7", "7"], lords=[], karakas=[],
        )
        bhava_refs = [r["target_ref"] for r in rows if r["target_type"] == "bhava"]
        assert bhava_refs == ["7"]

    def test_citation_or_uncited_extension_invariant(self):
        """Every produced row satisfies: classical_citation IS NOT NULL OR
        uncited_extension = true — the DB CHECK constraint's Python-side mirror."""
        rows = build_resonance_rows(
            "major_gain",
            houses=["2", "11"], lords=["2L", "11L"], karakas=["Jupiter", "Mercury"],
            ontology_citation="BPHS ch.2,11 (dhana-bhava)",
            transit_rule_rows=[
                {"id": 26, "rule_type": "favourable", "graha": "jupiter", "primary_house": 2,
                 "classical_citation": "BPHS Ch.29"},
            ],
            sensitive_fact_rows=[{"fact_id": "s1", "fact_subject": "JUP", "fact_key": "gandanta"}],
            arudha_fact_rows=[{"fact_id": "a1", "fact_subject": "ARUDHA_A2"}],
            yoga_firing_rows=[{"yoga_canonical_id": "dhana_yoga_house_lords"}],
            dasha_rows=[{"lord_graha": "Jupiter"}],
        )
        assert len(rows) > 0
        for row in rows:
            assert row["classical_citation"] is not None or row["uncited_extension"] is True, row

    def test_empty_inputs_yield_no_rows(self):
        assert build_resonance_rows("x") == []


# ── Writer contract (static-source-grep, matches existing L3 test convention) ─

class TestWriterContractGrep:
    def test_writer_contract_no_commit(self):
        source = WRITER_PATH.read_text()
        assert re.findall(r"\.commit\(\)", source) == []

    def test_writer_contract_no_rollback(self):
        source = WRITER_PATH.read_text()
        assert re.findall(r"\.rollback\(\)", source) == []

    def test_writer_contract_no_asset_throughput_write(self):
        source = WRITER_PATH.read_text()
        assert re.findall(r"INSERT INTO asset_throughput|UPDATE asset_throughput", source) == []

    def test_writer_registers_correct_asset_id(self):
        source = WRITER_PATH.read_text()
        assert "@register(\"ka_gochara_resonance\")" in source

    def test_writer_does_not_touch_ka_gochara(self):
        """This is a fresh, distinct asset — must never write ka_gochara's table
        or reference its asset_id."""
        source = WRITER_PATH.read_text()
        assert "'ka_gochara'" not in source
        assert '"ka_gochara"' not in source

    def test_delete_scoped_to_chart_id(self):
        source = WRITER_PATH.read_text()
        assert "DELETE FROM gochara_resonance_map WHERE chart_id = %s" in source

    def test_shim_imports_from_services_package(self):
        source = SHIM_PATH.read_text()
        assert "from services.ka_gochara_resonance.writer import KaGocharaResonanceWriter" in source


# ── Migration static checks ────────────────────────────────────────────────────

class TestMigrationIdempotency:
    def test_migration_file_exists(self):
        assert MIGRATION_PATH.exists(), MIGRATION_PATH

    def test_create_table_if_not_exists(self):
        sql = MIGRATION_PATH.read_text()
        assert "CREATE TABLE IF NOT EXISTS gochara_resonance_map" in sql

    def test_indexes_if_not_exists(self):
        sql = MIGRATION_PATH.read_text()
        for stmt in re.findall(r"CREATE (?:UNIQUE )?INDEX[^\n]*", sql):
            assert "IF NOT EXISTS" in stmt, stmt

    def test_no_destructive_ops(self):
        sql = MIGRATION_PATH.read_text()
        # DROP appears only inside the commented-out manual ROLLBACK section
        body = sql.split("-- ROLLBACK:")[0] if "-- ROLLBACK:" in sql else sql
        active_lines = [l for l in body.splitlines() if not l.strip().startswith("--")]
        active_sql = "\n".join(active_lines)
        assert "DROP TABLE" not in active_sql
        assert "TRUNCATE" not in active_sql

    def test_asset_registry_insert_is_upsert(self):
        sql = MIGRATION_PATH.read_text()
        assert "ON CONFLICT (asset_id) DO UPDATE SET" in sql

    def test_citation_or_extension_check_constraint_present(self):
        sql = MIGRATION_PATH.read_text()
        assert "gochara_resonance_map_citation_or_flag" in sql
        assert "classical_citation IS NOT NULL OR uncited_extension = true" in sql

    def test_wrapped_in_single_transaction(self):
        sql = MIGRATION_PATH.read_text()
        assert sql.strip().count("BEGIN;") >= 1
        assert "COMMIT;" in sql


# ── Fake-cursor/conn integration test (script-matched, DB-free — matches the
# existing l3/test_ka_kalasutra.py convention) ─────────────────────────────────

class _FakeCursor:
    def __init__(self, script, sink, row_factory=None):
        self._script = script
        self._sink = sink
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        normalized = " ".join(sql.split())
        if normalized.startswith("DELETE FROM gochara_resonance_map"):
            self._sink.setdefault("deletes", []).append(params)
            self._result = []
            return
        for matcher, rows in self._script:
            if matcher in normalized:
                self._result = list(rows)
                return
        self._result = []

    def executemany(self, sql, rows):
        normalized = " ".join(sql.split())
        if normalized.startswith("INSERT INTO gochara_resonance_map"):
            self._sink.setdefault("inserted", []).extend(rows)

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None


class _FakeConn:
    def __init__(self, script, sink):
        self._script = script
        self._sink = sink

    def cursor(self, *a, **k):
        return _FakeCursor(self._script, self._sink)


class _Ctx:
    def __init__(self, conn, chart_id, dry_run=False):
        self.db_conn = conn
        self.config = {"chart_id": chart_id}
        self.dry_run = dry_run


_MARRIAGE_ONTOLOGY = {
    "event_class_id": "marriage",
    "signature_model": {"houses": ["7", "2"], "lords": ["7L"], "karakas": ["Venus"]},
    "citations": ["BPHS ch.7 (vivaha)"],
}
_MAJOR_GAIN_ONTOLOGY = {
    "event_class_id": "major_gain",
    "signature_model": {"houses": ["2", "11"], "lords": ["2L", "11L"], "karakas": ["Jupiter", "Mercury"]},
    "citations": ["BPHS ch.2,11 (dhana-bhava)"],
}
_CAREER_ONTOLOGY = {
    "event_class_id": "career_advancement",
    "signature_model": {"houses": ["10", "11"], "lords": ["10L", "11L"], "karakas": ["Sun"]},
    "citations": ["BPHS ch.10", "Phaladeepika ch.10"],
}


def _fixture_script():
    """One (event_class_id-parametrized) ontology row per query — the fake
    cursor keys off the SQL text only, so this fixture returns the SAME
    3-class list every time `FROM brahma_event_ontology` fires, and the
    writer is exercised with a single representative event_class per full run
    to keep the script deterministic (see test below)."""
    return [
        ("FROM brahma_event_ontology", [_MARRIAGE_ONTOLOGY]),
        ("FROM bg_transit_rules", [
            {"id": 34, "rule_type": "favourable", "graha": "venus", "primary_house": 2,
             "classical_citation": "BPHS Ch.29 (Gochara Phala — Transit Results)"},
            {"id": 47, "rule_type": "unfavourable", "graha": "venus", "primary_house": 7,
             "classical_citation": "BPHS Ch.29 (Gochara Phala — Transit Results)"},
        ]),
        ("FROM chart_facts", [{"fact_id": "f1", "fact_subject": "VEN", "fact_key": "mrityu_bhaga"}]),
        ("FROM ga_yoga_firings", [{"yoga_canonical_id": "dhana_yoga_house_lords"}]),
        ("FROM chart_dashas", [{"lord_graha": "Venus"}]),
    ]


def test_writer_inserts_expected_rows_for_fixture_chart():
    from pipeline.orchestrator.writers.ka_gochara_resonance import KaGocharaResonanceWriter

    sink: dict = {}
    conn = _FakeConn(_fixture_script(), sink)
    result = KaGocharaResonanceWriter().run(_Ctx(conn, CHART_ID))

    # Every fetch (ontology x3 event classes) hits the SAME fixture script
    # (one ontology row, keyed only by SQL text) — so each of the 3 target
    # event classes resolves to the "marriage" shape's target sets. The fake
    # cursor keys purely on SQL substring, so both chart_facts queries
    # (sensitive_degree_check AND arudha_pada) match "FROM chart_facts" and
    # get the SAME fixture row — this mirrors that in the manual recompute
    # below (arudha_fact_rows = the same fixture row as sensitive_fact_rows).
    # Total row count = 3 event classes x rows-per-class from build_resonance_rows.
    from services.ka_gochara_resonance.writer import build_resonance_rows
    _shared_fact_row = {"fact_id": "f1", "fact_subject": "VEN", "fact_key": "mrityu_bhaga"}
    per_class = len(build_resonance_rows(
        "marriage",
        houses=["7", "2"], lords=["7L"], karakas=["Venus"],
        ontology_citation="BPHS ch.7 (vivaha)",
        transit_rule_rows=[
            {"id": 34, "rule_type": "favourable", "graha": "venus", "primary_house": 2,
             "classical_citation": "BPHS Ch.29 (Gochara Phala — Transit Results)"},
            {"id": 47, "rule_type": "unfavourable", "graha": "venus", "primary_house": 7,
             "classical_citation": "BPHS Ch.29 (Gochara Phala — Transit Results)"},
        ],
        sensitive_fact_rows=[_shared_fact_row],
        arudha_fact_rows=[_shared_fact_row],
        yoga_firing_rows=[{"yoga_canonical_id": "dhana_yoga_house_lords"}],
        dasha_rows=[{"lord_graha": "Venus"}],
    ))
    assert result.rows_inserted == per_class * len(TARGET_EVENT_CLASSES)
    assert len(sink["inserted"]) == result.rows_inserted
    assert len(sink["deletes"]) == 1
    assert sink["deletes"][0] == (CHART_ID,)


def test_writer_idempotent_rerun_deletes_before_reinsert():
    """Idempotency (§N.3): a second run issues its own DELETE before
    re-inserting — a rebuild REPLACES, never accretes."""
    from pipeline.orchestrator.writers.ka_gochara_resonance import KaGocharaResonanceWriter

    sink: dict = {}
    conn = _FakeConn(_fixture_script(), sink)
    writer = KaGocharaResonanceWriter()
    first = writer.run(_Ctx(conn, CHART_ID))

    sink2: dict = {}
    conn2 = _FakeConn(_fixture_script(), sink2)
    second = writer.run(_Ctx(conn2, CHART_ID))

    assert first.rows_inserted == second.rows_inserted
    assert len(sink2["deletes"]) == 1
    # A fresh run's insert count matches the first run's exactly — no accretion
    # (each run starts from its own DELETE-then-INSERT, never appending).
    assert len(sink2["inserted"]) == len(sink["inserted"])


def test_writer_every_row_has_citation_or_uncited_extension():
    from pipeline.orchestrator.writers.ka_gochara_resonance import KaGocharaResonanceWriter

    sink: dict = {}
    conn = _FakeConn(_fixture_script(), sink)
    KaGocharaResonanceWriter().run(_Ctx(conn, CHART_ID))

    assert sink["inserted"], "writer produced no rows to check"
    for row in sink["inserted"]:
        assert row["classical_citation"] is not None or row["uncited_extension"] is True, row


def test_writer_dry_run_no_writes():
    from pipeline.orchestrator.writers.ka_gochara_resonance import KaGocharaResonanceWriter

    sink: dict = {}
    conn = _FakeConn(_fixture_script(), sink)
    result = KaGocharaResonanceWriter().run(_Ctx(conn, CHART_ID, dry_run=True))
    assert result.rows_inserted == 0
    assert "deletes" not in sink
    assert "inserted" not in sink
