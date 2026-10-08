"""WFIX-A: a writer's WriterResult must report the rows PRESENT in its declared produced-table set.

The orchestrator records ``rows_written = rows_inserted + rows_updated`` (asset_runner.py). Census
check Build.completion compares that record with the rows actually present in the asset's declared
produced-table set. These writers reported a CHANGED figure instead (an ``executemany`` rowcount, an
insert-only sum, one table of several), so a converged rerun recorded ``rows_written=0`` against a
full table. Every test below pins a writer whose changed-count and present-count DIFFER, runs the
REAL writer ``run`` against a recording connection that serves ``COUNT(*)`` for the produced tables,
and asserts the result carries the present count. They fail on the pre-fix writers.

The connection double answers only the statements the rows-present read issues (plain
``SELECT count(*) AS n FROM "<table>" [WHERE ...]``) from a ``{table-spec: n}`` dict and REFUSES any
count it was not told about, so a writer that counts the wrong table / slice / chart scope fails
loudly instead of passing by accident.
"""
from __future__ import annotations

import re
import sys
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers import ContextSpec

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
_FROM = re.compile(r"\bFROM ([a-z_0-9]+)")


class CountingConn:
    """Recording connection. ``answers`` maps a substring of the (whitespace-normalised) count statement to the number the database
    would answer; a count statement no answer matches is REFUSED, so a writer that counts a table / slice / chart scope its declared
    produced set does not name fails loudly instead of passing by accident. ``count_reads`` records every statement the writer ran
    (and ``tables`` the relations it names)."""

    row_factory = None

    def __init__(self, answers: dict, scripted=None) -> None:
        self.answers = dict(answers)
        self.scripted = scripted or (lambda sql, params: None)
        self.statements: list[tuple[str, tuple]] = []
        self.count_reads: list[tuple[str, tuple]] = []
        self.commits = 0

    # the writer must never commit or close (CLAUDE.md N.2)
    def commit(self):  # pragma: no cover - asserted not called
        self.commits += 1

    def close(self):  # pragma: no cover - asserted not called
        raise AssertionError("a writer must never close ctx.db_conn")

    @property
    def tables(self) -> set[str]:
        return {t for sql, _ in self.count_reads for t in _FROM.findall(sql)}

    def cursor(self, *a, **kw):
        return _Cursor(self)

    def execute(self, sql, params=None):
        cur = _Cursor(self)
        cur.execute(sql, params)
        return cur


class _Cursor:
    rowcount = 0

    def __init__(self, conn: CountingConn) -> None:
        self.conn = conn
        self._row = None
        self._rows: list = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def executemany(self, sql, rows):
        self.conn.statements.append((" ".join(str(sql).split()), ("<many>", len(list(rows)))))

    def execute(self, sql, params=None):
        text = " ".join(str(sql).split())
        params = tuple(params or ())
        self.conn.statements.append((text, params))
        self._row, self._rows = None, []
        scripted = self.conn.scripted(text, params)
        if scripted is not None:
            if isinstance(scripted, list):
                self._rows = scripted
            else:
                self._row = scripted
            return
        if text.startswith(("SELECT count(", "SELECT (SELECT count(")):
            self.conn.count_reads.append((text, params))
            hits = [n for frag, n in self.conn.answers.items() if frag in text]
            if len(hits) != 1:
                raise AssertionError(f"unexpected count read ({len(hits)} answers match): {text} {params}")
            self._row = {"n": hits[0](params) if callable(hits[0]) else hits[0]}

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


def _ctx(asset_id: str, conn: CountingConn, **kw) -> ContextSpec:
    return ContextSpec(asset_id=asset_id, build_id="wfix-a-test", db_conn=conn, **kw)


# ── L0 seeders: the seeder's figure is what the run CHANGED; the result must be what is PRESENT ─────

def test_bg_ontology_reports_the_table_not_the_new_inserts(monkeypatch):
    from pipeline.orchestrator.writers import bg_ontology

    monkeypatch.setattr(bg_ontology, "seed_ontology",
                        lambda *_a, **_k: {"total": 728, "inserted": 0, "skipped": 728, "by_class": {}})
    conn = CountingConn({"FROM brahma_ontology": 728})
    result = bg_ontology.OntologyWriter().run(_ctx("bg_ontology", conn))
    assert result.rows_inserted == 728          # was 0 -> recorded rows_written=0 against 728 live
    assert result.rows_updated == 0              # never double-counted by the orchestrator's insert+update sum
    assert conn.tables == {"brahma_ontology"} and conn.commits == 0


def test_bg_reference_reports_all_eleven_tables_present(monkeypatch):
    from pipeline.orchestrator.writers import bg_reference

    tables = ["reference_planets", "reference_signs", "reference_aspects", "reference_vargas",
              "reference_houses", "reference_strength_systems", "reference_karakas",
              "reference_upagrahas", "reference_constants", "reference_topic_tags", "reference_glossary"]
    monkeypatch.setattr(bg_reference, "seed_reference", lambda *_a, **_k: {t: 0 for t in tables})
    conn = CountingConn({"(SELECT count(*) FROM reference_planets)": 1_242})
    result = bg_reference.ReferenceWriter().run(_ctx("bg_reference", conn))
    assert result.rows_inserted == 1_242         # was 0 (nothing newly inserted)
    assert conn.tables == set(tables)             # exactly the registry count_sql's eleven tables


def test_bg_formula_constants_counts_migration_owned_rows_too(monkeypatch):
    from pipeline.orchestrator.writers import bg_formula_constants as mod

    monkeypatch.setattr(mod, "seed_formula_constants", lambda *_a, **_k: {"brahma_formula_constants": 10})
    conn = CountingConn({"FROM brahma_formula_constants": 17})
    result = mod.FormulaConstantsWriter().run(_ctx("bg_formula_constants", conn))
    assert result.rows_inserted == 17            # was 10 (writer-owned only) against 17 live
    assert conn.tables == {"brahma_formula_constants"}


@pytest.mark.parametrize("asset, expected, read", [
    ("bg_medical_mappings", 21 + 27 + 12, {"bg_medical_mappings", "bg_nakshatra_medical", "bg_sign_medical"}),
    ("bg_nakshatra_medical", 27, {"bg_nakshatra_medical"}),
    ("bg_sign_medical", 12, {"bg_sign_medical"}),
])
def test_medical_writer_reports_each_registered_ids_own_tables(monkeypatch, asset, expected, read):
    from pipeline.orchestrator.writers import bg_medical_mappings as mod

    monkeypatch.setattr(mod, "seed_medical_mappings",
                        lambda **_k: {"bg_medical_mappings": 21, "bg_nakshatra_medical": 27, "bg_sign_medical": 12})
    conn = CountingConn({"(SELECT count(*) FROM bg_medical_mappings)": 60,
                         "AS n FROM bg_nakshatra_medical": 27, "AS n FROM bg_sign_medical": 12})
    result = mod.BgMedicalMappingsWriter().run(_ctx(asset, conn))
    assert result.rows_inserted == expected      # bg_sign_medical was 60 against its own 12 rows
    assert conn.tables == read


@pytest.mark.parametrize("asset, expected", [("bg_transit_rules", 76), ("bg_transit_engine", 9)])
def test_transit_writer_reports_each_registered_ids_own_table(monkeypatch, asset, expected):
    from brahmagyan import l0_transit
    from pipeline.orchestrator.writers import bg_transit_rules as mod

    monkeypatch.setattr(l0_transit, "seed_transit_rules",
                        lambda *_a, **_k: {"bg_transit_engine": 9, "bg_transit_rules": 69, "total": 105})
    conn = CountingConn({"AS n FROM bg_transit_rules": 76, "AS n FROM bg_transit_engine": 9})
    result = mod.BgTransitRulesWriter().run(_ctx(asset, conn))
    assert result.rows_inserted == expected      # was 105 (seeder total across three tables)
    assert conn.tables == {asset}


def test_bg_vidhi_primitives_reports_rows_present_not_rows_changed():
    from pipeline.orchestrator.writers.bg_vidhi_primitives import VidhiPrimitivesWriter

    conn = CountingConn({"FROM vidhi_primitives": 60})
    # every upsert reports rowcount 0 (nothing changed) and nothing is deleted
    result = VidhiPrimitivesWriter().run(_ctx("bg_vidhi_primitives", conn))
    assert result.rows_inserted == 60            # was 0 upserted + 0 deleted


# ── bg_ephemeris: executemany's rowcount is the LAST batch's changed rows ──────────────────────────

def test_bg_ephemeris_reports_the_table_not_the_last_batch_rowcount(monkeypatch):
    from brahmagyan import l0_ephemeris
    from pipeline.orchestrator.writers import bg_sky_calendar
    from pipeline.orchestrator.writers.bg_ephemeris import BgEphemerisWriter

    monkeypatch.setitem(sys.modules, "swisseph", SimpleNamespace())
    monkeypatch.setattr(l0_ephemeris, "BUILD_START", date(2026, 8, 26))
    monkeypatch.setattr(l0_ephemeris, "BUILD_END", date(2026, 8, 26))
    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/verified/se1")
    monkeypatch.setattr(bg_sky_calendar, "_require_swiss_file_backend", lambda *_a: None)
    monkeypatch.setattr(bg_sky_calendar, "_require_pinned_ephemeris_files", lambda *_a: None)
    monkeypatch.setattr(l0_ephemeris, "_compute_positions_for_date", lambda *_a: [{"date": date(2026, 8, 26)}])

    conn = CountingConn({"FROM ephemeris_daily": 825_084})      # rowcount stays 0: a rerun changed nothing
    result = BgEphemerisWriter().run(_ctx("bg_ephemeris", conn))
    assert result.rows_inserted == 825_084       # was 0 -> recorded rows_written=0 against 825,084 live
    assert conn.tables == {"ephemeris_daily"}


# ── bg_cohort: two produced tables, 10,000 + 100,000 ───────────────────────────────────────────────

def test_bg_cohort_reports_both_produced_tables(monkeypatch):
    from brahmagyan import l0_ephemeris
    from pipeline.orchestrator.writers import bg_cohort as mod

    size = 3
    monkeypatch.setattr(mod, "COHORT_SIZE", size)
    monkeypatch.setitem(sys.modules, "swisseph", SimpleNamespace())
    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/verified/se1")
    monkeypatch.setattr(mod, "_require_reproducible_write_runtime", lambda: None)
    monkeypatch.setattr(mod, "_require_pinned_ephemeris_runtime", lambda _swe, path: path)
    monkeypatch.setattr(mod, "sample_birth_params", lambda *_a, **_k: [
        {"synthetic_id": i, "birth_datetime_utc": datetime(1990, 1, i), "lat": 20.0, "lon": 85.0}
        for i in range(1, size + 1)])
    monkeypatch.setattr(mod, "compute_synthetic_positions", lambda *_a, **_k: {"Moon": {"longitude": 1.0}})
    monkeypatch.setattr(mod, "compute_md_lord_chain", lambda _p: [
        {"md_index": k, "md_lord": "Ke", "start_age_years": 0.0, "end_age_years": 7.0,
         "md_full_years": 7.0, "is_partial": False} for k in range(1, 11)])

    def scripted(sql, _params):
        if "AS cohort_count" in sql:
            return {"cohort_count": size, "cohort_min": 1, "cohort_max": size,
                    "md_count": 10 * size, "invalid_chain_count": 0}
        return None

    conn = CountingConn({}, scripted)

    class _Many(_Cursor):
        def executemany(self, sql, rows):
            rows = list(rows)
            super().executemany(sql, rows)
            self.rowcount = len(rows)

    conn.cursor = lambda *a, **k: _Many(conn)
    result = mod.BgCohortWriter().run(_ctx("bg_cohort", conn))
    assert result.rows_inserted == size + 10 * size   # was `size` (cohort table only): 10,000 vs 110,000 live
    assert f"cohort_rows={size}" in result.notes


# ── bg_texts: chunks + classical_texts ─────────────────────────────────────────────────────────────

def test_bg_texts_reports_chunks_and_text_rows_present():
    from pipeline.orchestrator.writers.bg_texts import TextsWriter

    def scripted(sql, _params):
        if "GROUP BY text_id" in sql:
            return []
        return None

    conn = CountingConn({"(SELECT count(*) FROM classical_text_chunks) + (SELECT count(*) FROM classical_texts)": 10_667,
                         "AS n FROM classical_text_chunks": 10_651}, scripted)       # the second is the writer's own pre-count
    result = TextsWriter().run(_ctx("bg_texts", conn, config={"rebuild_mode": "metadata_only"}))
    assert result.rows_inserted == 10_667        # was 0 -> recorded rows_written=0 against 10,667 live


# ── bg_text_index: the registry figure is DISTINCT topic tags, not UPDATEs issued ───────────────────

def test_bg_text_index_reports_distinct_tags_not_updates_issued(monkeypatch):
    from pipeline.orchestrator.writers import bg_text_index as mod

    monkeypatch.setattr(mod, "classify_chunk", lambda *_a, **_k: "career_general")

    def scripted(sql, _params):
        if sql == "SELECT canonical_id FROM reference_topic_tags":
            return [{"canonical_id": "career_general"}]
        if "AND topic_tag IS NULL" in sql:
            return {"count": 0}
        if sql.startswith("SELECT COUNT(*) AS count FROM classical_text_chunks WHERE embedding IS NOT NULL"):
            return {"count": 1}
        if sql.startswith("SELECT chunk_id, content_en, topic_tag"):
            return [{"chunk_id": "c1", "content_en": "career", "topic_tag": "career_general"}]  # already right
        if sql.startswith("SELECT COUNT(DISTINCT topic_tag) AS count"):
            return {"count": 361}
        return None

    conn = CountingConn({}, scripted)
    result = mod.TextIndexWriter().run(_ctx("bg_text_index", conn))
    assert result.rows_inserted == 361           # was `changed` = 0 against 361 live distinct tags


def test_bg_text_index_early_exit_still_reports_the_registry_figure(monkeypatch):
    from pipeline.orchestrator.writers import bg_text_index as mod

    def scripted(sql, _params):
        if sql == "SELECT canonical_id FROM reference_topic_tags":
            return [{"canonical_id": "career_general"}]
        if sql.startswith("SELECT COUNT(*) AS count FROM classical_text_chunks"):
            return {"count": 0}
        return None

    conn = CountingConn({"count(DISTINCT topic_tag)": 0}, scripted)
    result = mod.TextIndexWriter().run(_ctx("bg_text_index", conn))
    assert result.rows_inserted == 0
    assert conn.tables == {"classical_text_chunks"} and len(conn.count_reads) == 1


# ── bg_sky_calendar / bg_muhurta_lattice ───────────────────────────────────────────────────────────

def _fake_swisseph(monkeypatch, module):
    from brahmagyan import l0_ephemeris

    monkeypatch.setitem(sys.modules, "swisseph", SimpleNamespace(julday=lambda *_a: 2_461_000.5))
    monkeypatch.setattr(l0_ephemeris, "_resolve_ephe_path", lambda: "/verified/se1")
    monkeypatch.setattr(module, "_require_swiss_file_backend", lambda *_a: None)
    monkeypatch.setattr(module, "_require_pinned_ephemeris_files", lambda *_a: None)


def test_bg_sky_calendar_reports_the_table_not_the_upsert_rowcount(monkeypatch):
    from pipeline.orchestrator.writers import bg_sky_calendar as mod

    _fake_swisseph(monkeypatch, mod)
    monkeypatch.setattr(mod, "_require_reproducible_write_runtime", lambda: None)
    monkeypatch.setattr(mod, "scan_ingresses", lambda *_a: [])
    monkeypatch.setattr(mod, "scan_stations", lambda *_a: [])
    monkeypatch.setattr(mod, "scan_eclipses", lambda *_a: [])
    monkeypatch.setattr(mod, "scan_double_transits", lambda *_a: [])
    conn = CountingConn({"FROM bg_sky_calendar": 31_102})
    result = mod.BgSkyCalendarWriter().run(_ctx("bg_sky_calendar", conn))
    assert result.rows_inserted == 31_102        # was 0 changed rows against 31,102 live


def test_bg_muhurta_lattice_substep_reports_its_own_year_partition(monkeypatch):
    from pipeline.orchestrator.writers import bg_muhurta_lattice as mod
    from pipeline.orchestrator.writers import SubStep

    _fake_swisseph(monkeypatch, mod)
    monkeypatch.setattr(mod, "compute_horizon", lambda *_a: (date(2026, 8, 1), date(2028, 8, 1)))
    monkeypatch.setattr(mod, "compute_day_factors", lambda _d: [])
    per_year = {(datetime(2026, 1, 1), datetime(2027, 1, 1)): 14_248,
                (datetime(2027, 1, 1), datetime(2028, 1, 1)): 33_986}
    conn = CountingConn({"FROM bg_muhurta_lattice WHERE start_utc >= %s AND start_utc < %s": lambda p: per_year[p]})
    writer = mod.BgMuhurtaLatticeWriter()
    got = [writer.run_substep(_ctx("bg_muhurta_lattice", conn), SubStep(key=f"year:{y}", label=str(y))).rows_inserted
           for y in (2026, 2027)]
    assert got == [14_248, 33_986]               # was 0 / 0 changed rows
    assert sum(got) == 48_234                     # the orchestrator SUMS substeps: disjoint partitions add up exactly


# ── bo_*: chart-scoped declared produced sets ──────────────────────────────────────────────────────

def _bo_ctx(asset, conn):
    return _ctx(asset, conn, config={"chart_id": CHART})


def test_bo_bimba_reports_its_five_owned_node_classes(monkeypatch):
    from pipeline.orchestrator.writers import bo_bimba as mod

    monkeypatch.setattr(mod, "CANONICAL_AYAS", ["lahiri"])
    monkeypatch.setattr(mod, "_fetch_msr_signals", lambda *_a: [{"s": 1}])
    monkeypatch.setattr(mod, "_fetch_graha_positions", lambda *_a: {"Sun": {}})
    monkeypatch.setattr(mod, "_fetch_d1_dignity", lambda *_a: {"Sun": "own"})
    monkeypatch.setattr(mod, "_build_nodes_for_aya", lambda *_a: [{"n": i} for i in range(3)])
    monkeypatch.setattr(mod, "_batch_insert", lambda _c, nodes: len(nodes) + 5)   # insert attempts != rows present
    import bodha_writers._idempotency as idem
    monkeypatch.setattr(idem, "replace_prior_cgm_nodes", lambda *_a: 0)

    conn = CountingConn({"FROM bodha_cgm_nodes WHERE chart_id = %s::uuid AND node_type IN ('graha', 'bhava', 'domain', 'yoga', 'dosha')": 255})
    result = mod.BoBimbaWriter().run(_bo_ctx("bo_bimba", conn))
    assert result.rows_inserted == 255           # bo_bimba's own five classes -- NOT the table's 385 (arudha/special_lagna are bo_karanajala's)
    assert conn.count_reads[0][1] == (CHART,) and "arudha" not in conn.count_reads[0][0]


def test_bo_cgm_motifs_reports_motifs_subgraphs_and_topology(monkeypatch):
    from pipeline.orchestrator.writers import bo_cgm_motifs as mod

    monkeypatch.setattr(mod, "CANONICAL_AYAS", ["lahiri"])
    monkeypatch.setattr(mod, "_write_aya", lambda *_a: (600, 5, 5))
    conn = CountingConn({"(SELECT count(*) FROM bodha_cgm_motifs WHERE chart_id = %s::uuid)": 610})
    result = mod.BoCgmMotifsWriter().run(_bo_ctx("bo_cgm_motifs", conn))
    assert result.rows_inserted == 610           # was 600 (motifs only)
    assert conn.tables == {"bodha_cgm_motifs", "bodha_cgm_sub_graphs", "bodha_cgm_chart_topology_summary"}
    assert conn.count_reads[0][1] == (CHART, CHART, CHART)


def test_bo_karanajala_reports_edges_contradictions_and_its_node_slices(monkeypatch):
    from pipeline.orchestrator.writers import bo_karanajala as mod

    monkeypatch.setattr(mod, "CANONICAL_AYAS", [])      # no ayanamsha loop: only the result assembly is under test
    conn = CountingConn({"(SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = %s::uuid)": 1_031})
    result = mod.BoKaranajalaWriter().run(_bo_ctx("bo_karanajala", conn))
    assert result.rows_inserted == 1_031         # was 901 (edges + contradictions only)
    assert conn.tables == {"bodha_cgm_edges", "bodha_contradictions", "bodha_cgm_nodes"}
    assert "node_type IN ('arudha', 'special_lagna')" in conn.count_reads[0][0] and conn.count_reads[0][1] == (CHART, CHART, CHART)
