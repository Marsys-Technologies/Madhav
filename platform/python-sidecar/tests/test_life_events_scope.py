"""
test_life_events_scope.py -- SS ruling N-105: an L4 read of `life_events` can NEVER return another chart's rows.

The database is an in-memory SQLite stand-in that holds TWO charts' rows and EXECUTES the SQL the code under test
actually issues (so a missing `WHERE chart_id = %s` is a real, observable leak, not a string check). The chart-scoped
security-barrier view of migration 1274 is mirrored by a SQLite view over `app_chart_context()` (a registered function
returning the transaction-local `app.chart_context` GUC the helper sets; NULL when unset: fail closed).

Both directions are tested:
  * positive: a read returns exactly the requested chart's rows (UUID and str inputs), on the view path and the table path;
  * negative control: the SAME fixture, read WITHOUT the scoping, does return both charts' rows (so the fixture can detect a
    removed filter), and a removed filter makes the helper's tests go red (mutation tests below).
Private life-event CONTENT never appears here: rows are synthetic markers.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
import uuid

import psycopg
import pytest

from brahmagyan.phala import life_events_scope as scope
from brahmagyan.phala.life_events_scope import (
    BASE_TABLE, CHART_CONTEXT_GUC, SCOPED_VIEW, VIEW_COLUMNS, ForeignChartRowError,
    build_select_sql, fetch_chart_life_events, normalize_chart_id,
)

CHART_A = uuid.UUID("482012f1-710e-4a25-994a-93821f5871aa")
CHART_B = uuid.UUID("1c826d5a-41cb-4450-b4dc-59d440e5f75a")
CHART_C = uuid.UUID("00000000-0000-4000-8000-0000000000c3")      # a chart with no life events at all


# ───────────────────────────────────────────── SQLite stand-in for a psycopg connection ──────────────────────────────

sqlite3.register_converter("DATE", lambda b: dt.date.fromisoformat(b.decode()))
sqlite3.register_converter("BOOLEAN", lambda b: bool(int(b)))


def event_uuid(chart, n) -> str:
    """A deterministic REAL uuid per (chart, n): ids are uuids in production and the resolver parses them strictly."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"life-event/{chart}/{n}"))


class _Cur:
    def __init__(self, conn):
        self._c = conn
        self._rows: list = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        c = self._c
        c.log.append((" ".join(sql.split()), tuple(params or ())))
        self._rows = []
        s = " ".join(sql.split())
        if "to_regclass" in s:
            self._rows = [{"use_view": c.view_usable}]
            return
        if s.startswith("SELECT current_setting("):
            self._rows = [{"current_setting": c.gucs.get(params[0])}]
            return
        if s.startswith("SELECT set_config("):
            name, value = params
            c.gucs[name] = value
            return
        if c.fail_select is not None and s.startswith("SELECT") and "life_events" in s:
            raise c.fail_select
        py = tuple(str(p) if isinstance(p, (uuid.UUID, dt.date)) else p for p in (params or ()))[: s.count("%s")]
        cur = c.db.execute(s.replace("%s", "?"), py)
        self._rows = [dict(r) for r in cur.fetchall()] if cur.description else []

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConn:
    """psycopg-shaped connection (cursor() as a context manager, dict rows) over SQLite, holding life_events for 2 charts."""

    def __init__(self, *, view_usable: bool = False, fail_select: Exception | None = None):
        self.db = sqlite3.connect(":memory:", isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
        self.db.row_factory = sqlite3.Row
        self.gucs: dict[str, str] = {}
        self.log: list = []
        self.view_usable = view_usable
        self.fail_select = fail_select
        self.db.create_function("app_chart_context", 0, lambda: (self.gucs.get(CHART_CONTEXT_GUC) or None))
        self.db.executescript(
            """
            CREATE TABLE life_events (
                id TEXT NOT NULL, event_id TEXT NOT NULL, event_date DATE NOT NULL, category TEXT NOT NULL,
                description TEXT NOT NULL, domain TEXT, outcome_observed BOOLEAN, chart_id TEXT NOT NULL,
                provenance TEXT, chart_state TEXT, significance TEXT);
            CREATE VIEW life_events_chart_scoped AS
                SELECT id, event_id, event_date, category, domain, chart_id
                FROM life_events WHERE chart_id = app_chart_context();
            CREATE TABLE chart_dashas (chart_id TEXT, system_id TEXT, level_n INT, ayanamsha_id TEXT,
                lord_graha TEXT, start_date DATE, end_date DATE);
            """
        )

    def cursor(self, *a, **k):
        return _Cur(self)

    def add_event(self, chart, n, date, category="career", description=None, outcome=None, domain=None):
        self.db.execute(
            "INSERT INTO life_events (id, event_id, event_date, category, description, domain, outcome_observed, chart_id,"
            " provenance, chart_state, significance) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (event_uuid(chart, n), f"EVT.{str(chart)[:4]}.{n}", date.isoformat(), category,
             description or f"MARKER-{str(chart)[:4]}-{n}", domain or category, outcome, str(chart),
             "PRIVATE-PROVENANCE", "PRIVATE-CHART-STATE", "PRIVATE-SIGNIFICANCE"))

    def add_dasha(self, chart, level, lord, start, end):
        self.db.execute("INSERT INTO chart_dashas VALUES (?,?,?,?,?,?,?)",
                        (str(chart), "vimshottari", level, "lahiri_chitrapaksha", lord, start.isoformat(), end.isoformat()))

    def selects_of_life_events(self):
        return [s for s, _ in self.log if s.startswith("SELECT") and "FROM life_events" in s]


@pytest.fixture
def two_charts():
    c = FakeConn()
    for n, d in enumerate([dt.date(2011, 3, 3), dt.date(2015, 6, 1), dt.date(2019, 1, 9)], start=1):
        c.add_event(CHART_A, n, d, outcome=True if n == 1 else None)
    for n, d in enumerate([dt.date(2012, 7, 7), dt.date(2016, 2, 2)], start=1):
        c.add_event(CHART_B, n, d, category="health", outcome=False)
    return c


def _ids(rows):
    return sorted(r["id"] for r in rows)


A_IDS = sorted(event_uuid(CHART_A, n) for n in (1, 2, 3))
B_IDS = sorted(event_uuid(CHART_B, n) for n in (1, 2))


# ───────────────────────────────────────────────── the helper ────────────────────────────────────────────────────────

def test_normalize_chart_id_accepts_uuid_and_str_and_rejects_everything_else():
    assert normalize_chart_id(CHART_A) is CHART_A
    assert normalize_chart_id(str(CHART_A)) == CHART_A
    assert normalize_chart_id("  " + str(CHART_A) + " ") == CHART_A
    for bad in ("any-chart", "", "482012f1"):
        with pytest.raises(ValueError):
            normalize_chart_id(bad)
    for bad in (None, 17, b"x"):
        with pytest.raises(TypeError):
            normalize_chart_id(bad)


@pytest.mark.parametrize("view_usable", [False, True], ids=["base_table_path", "chart_scoped_view_path"])
@pytest.mark.parametrize("as_str", [False, True], ids=["uuid_input", "str_input"])
def test_read_returns_only_the_requested_charts_rows(two_charts, view_usable, as_str):
    two_charts.view_usable = view_usable
    fetch = lambda ch: fetch_chart_life_events(two_charts, str(ch) if as_str else ch, ("id", "event_date", "category"))
    a, b, c = fetch(CHART_A), fetch(CHART_B), fetch(CHART_C)
    assert _ids(a) == A_IDS and _ids(b) == B_IDS and c == []
    assert {str(r["chart_id"]) for r in a} == {str(CHART_A)} and {str(r["chart_id"]) for r in b} == {str(CHART_B)}
    relation = SCOPED_VIEW if view_usable else BASE_TABLE
    assert all(f"FROM {relation} WHERE chart_id = %s" in s for s in two_charts.selects_of_life_events())


def test_negative_control_the_fixture_does_leak_without_the_scoping(two_charts):
    """Without the scoping, a read of this fixture returns BOTH charts' rows: the tests above are discriminating."""
    unscoped = two_charts.db.execute("SELECT id, chart_id FROM life_events ORDER BY event_date").fetchall()
    assert {r["chart_id"] for r in unscoped} == {str(CHART_A), str(CHART_B)} and len(unscoped) == 5


def test_view_fails_closed_when_the_guc_is_unset_or_wrong(two_charts):
    q = "SELECT id FROM life_events_chart_scoped"
    assert two_charts.db.execute(q).fetchall() == []                       # unset -> NULL -> zero rows
    two_charts.gucs[CHART_CONTEXT_GUC] = ""
    assert two_charts.db.execute(q).fetchall() == []                       # empty == unset
    two_charts.gucs[CHART_CONTEXT_GUC] = str(CHART_C)
    assert two_charts.db.execute(q).fetchall() == []                       # a chart with no events
    two_charts.gucs[CHART_CONTEXT_GUC] = str(CHART_B)
    assert sorted(r["id"] for r in two_charts.db.execute(q).fetchall()) == B_IDS


def test_helper_pins_the_guc_for_the_read_and_clears_it_after(two_charts):
    two_charts.view_usable = True
    fetch_chart_life_events(two_charts, CHART_A, ("id",))
    sets = [p for s, p in two_charts.log if s.startswith("SELECT set_config(")]
    assert sets == [(CHART_CONTEXT_GUC, str(CHART_A)), (CHART_CONTEXT_GUC, "")]      # nothing was pinned before: restored to the empty setting
    assert two_charts.gucs[CHART_CONTEXT_GUC] == ""


def test_the_previous_guc_value_is_restored_not_blanked(two_charts):
    """LOW-3 (review): an orchestrator-level pin made before the read is still in place after it."""
    outer = str(CHART_B)
    two_charts.gucs[CHART_CONTEXT_GUC] = outer
    fetch_chart_life_events(two_charts, CHART_A, ("id",))
    assert two_charts.gucs[CHART_CONTEXT_GUC] == outer
    from brahmagyan.phala.life_events_scope import resolve_life_event_text
    resolve_life_event_text(two_charts, CHART_A, event_uuid(CHART_A, 1))
    assert two_charts.gucs[CHART_CONTEXT_GUC] == outer


def test_rows_come_back_ordered_by_event_date_whatever_the_insertion_order():
    c = FakeConn()
    for n, d in ((1, dt.date(2019, 1, 9)), (2, dt.date(2011, 3, 3)), (3, dt.date(2015, 6, 1))):
        c.add_event(CHART_A, n, d)
    rows = fetch_chart_life_events(c, CHART_A, ("id", "event_date"), order_by=("event_date",))
    assert [r["event_date"] for r in rows] == sorted(r["event_date"] for r in rows) and len(rows) == 3


def test_helper_runs_in_its_own_savepoint_and_releases_it(two_charts):
    fetch_chart_life_events(two_charts, CHART_A, ("id",))
    stmts = [s for s, _ in two_charts.log]
    assert stmts[0] == f"SAVEPOINT {scope.SAVEPOINT}" and stmts[-1] == f"RELEASE SAVEPOINT {scope.SAVEPOINT}"


def test_columns_are_whitelisted_to_the_view_columns(two_charts):
    for private in ("outcome_observed", "description", "provenance", "chart_state", "significance", "source_citation", "recorded_at", "pool_consent"):
        with pytest.raises(ValueError):
            fetch_chart_life_events(two_charts, CHART_A, ("id", private))
    with pytest.raises(ValueError):
        fetch_chart_life_events(two_charts, CHART_A, ("id",), order_by=("provenance",))
    with pytest.raises(ValueError):
        fetch_chart_life_events(two_charts, CHART_A, ())
    assert "provenance" not in VIEW_COLUMNS and "chart_state" not in VIEW_COLUMNS
    assert "description" not in VIEW_COLUMNS                              # SS N-109: no private free text in the builder's window
    assert two_charts.log == []                                            # refused before any statement ran
    assert "outcome_observed" not in VIEW_COLUMNS                          # SS N-112: minimal columns


def test_a_malformed_chart_id_raises_before_any_statement(two_charts):
    with pytest.raises(ValueError):
        fetch_chart_life_events(two_charts, "any-chart", ("id",))
    assert two_charts.log == []


def test_sql_always_carries_the_chart_predicate():
    for rel in (BASE_TABLE, SCOPED_VIEW):
        sql = build_select_sql(rel, ("id", "event_date"), ("event_date",))
        assert f"FROM {rel} WHERE chart_id = %s ORDER BY event_date" in sql and "chart_id" in sql.split("FROM")[0]
    with pytest.raises(ValueError):
        build_select_sql("charts", ("id",), ("id",))


# ── mutations: a removed filter must turn a test red ────────────────────────────────────────────────────────────────

def _unfiltered_sql(relation, columns, order_by):
    cols = list(columns) + (["chart_id"] if "chart_id" not in columns else [])
    return f"SELECT {', '.join(cols)} FROM {relation} ORDER BY {', '.join(order_by)}"          # MUTANT: no WHERE chart_id = %s


def test_mutant_without_the_filter_is_stopped_by_the_runtime_guard(two_charts, monkeypatch):
    """MUTATION: remove the WHERE from the helper's SQL. The statement then leaks chart B's rows to chart A (the fixture
    shows the leak), and the helper's runtime guard turns it into an error, never into rows. Either way a test goes red."""
    monkeypatch.setattr(scope, "build_select_sql", lambda rel, cols, order: _unfiltered_sql(rel, cols, order))
    leak = two_charts.db.execute(_unfiltered_sql(BASE_TABLE, ("id",), ("event_date",))).fetchall()
    assert {r["chart_id"] for r in leak} == {str(CHART_A), str(CHART_B)}            # the mutant's SQL really leaks here
    with pytest.raises(ForeignChartRowError):
        fetch_chart_life_events(two_charts, CHART_A, ("id", "event_date"))


def test_injected_foreign_row_is_refused_and_the_savepoint_rolled_back(two_charts):
    """A database that (wrongly) hands back another chart's row -> ForeignChartRowError, no rows, savepoint rolled back."""
    class LeakyConn(FakeConn):
        def cursor(self, *a, **k):
            cur = _Cur(self)
            real = cur.execute

            def leaky(sql, params=()):
                if sql.startswith("SELECT id, chart_id FROM"):
                    cur._rows = [{"id": "id-4820-1", "chart_id": str(CHART_A)}, {"id": "id-1c82-1", "chart_id": str(CHART_B)}]
                    self.log.append((sql, tuple(params)))
                    return
                real(sql, params)
            cur.execute = leaky
            return cur

    c = LeakyConn()
    with pytest.raises(ForeignChartRowError):
        fetch_chart_life_events(c, CHART_A, ("id",))
    stmts = [s for s, _ in c.log]
    assert f"ROLLBACK TO SAVEPOINT {scope.SAVEPOINT}" in stmts and f"RELEASE SAVEPOINT {scope.SAVEPOINT}" in stmts


@pytest.mark.parametrize("exc", [psycopg.errors.UndefinedTable("no table"), psycopg.errors.InsufficientPrivilege("denied")])
def test_errors_propagate_after_rolling_the_savepoint_back(exc):
    c = FakeConn(fail_select=exc)
    with pytest.raises(type(exc)):
        fetch_chart_life_events(c, CHART_A, ("id",))
    stmts = [s for s, _ in c.log]
    assert f"ROLLBACK TO SAVEPOINT {scope.SAVEPOINT}" in stmts


def test_resolve_relation_prefers_the_view_only_when_usable(two_charts):
    assert scope.resolve_relation(two_charts) == BASE_TABLE
    two_charts.view_usable = True
    assert scope.resolve_relation(two_charts) == SCOPED_VIEW


# ───────────────────────────────────────────────── ph_pramana ────────────────────────────────────────────────────────

def _writer():
    from pipeline.orchestrator.writers.ph_pramana import PhPramanaWriter
    return PhPramanaWriter()


@pytest.mark.parametrize("view_usable", [False, True], ids=["base_table", "view"])
def test_ph_pramana_load_lel_is_chart_scoped(two_charts, view_usable):
    two_charts.view_usable = view_usable
    w = _writer()
    a = w._load_lel(two_charts, CHART_A)
    assert sorted(e.lel_jsonb["id"] for e in w._load_lel(two_charts, str(CHART_A))) == A_IDS == sorted(e.lel_jsonb["id"] for e in a)
    assert sorted(e.lel_jsonb["id"] for e in w._load_lel(two_charts, CHART_B)) == B_IDS
    assert w._load_lel(two_charts, CHART_C) == []


def test_ph_pramana_a_chart_with_no_events_cannot_be_given_an_earned_miss(two_charts):
    """THE DEFECT: unscoped, chart C (no events) is classified against A's and B's events and gets 'life_event_miss'.
    Scoped, it has no visibility into any domain -> 'detector_unavailable' (an honest null)."""
    from services.ph_pramana.engine import AnchorForPramana, LelEntry, PramanaContext, derive_pramana_records
    anchor = AnchorForPramana(anchor_id="ANC.X", domain="career", anchor_source="t", falsifier="no career event",
                              window_start=dt.date(2024, 1, 1), window_end=dt.date(2024, 12, 31), peak_date=None,
                              magnitude=None, confidence_high=None, derivation_ledger_jsonb={})
    w = _writer()
    scoped = w._load_lel(two_charts, CHART_C)
    rec = derive_pramana_records(PramanaContext(chart_id=str(CHART_C), today=dt.date(2026, 10, 1), anchors=[anchor], lel_entries=scoped))
    assert rec[0].evidence_type == "detector_unavailable"
    # the pre-fix behaviour, reproduced on the same fixture (every chart's events, no filter), is the contamination:
    leaked = [LelEntry(lel_id=None, event_date=r["event_date"], domain=r["category"], event_summary="", outcome_valence=None, lel_jsonb={})
              for r in two_charts.db.execute("SELECT event_date, category FROM life_events ORDER BY event_date").fetchall()]
    rec_old = derive_pramana_records(PramanaContext(chart_id=str(CHART_C), today=dt.date(2026, 10, 1), anchors=[anchor], lel_entries=leaked))
    assert rec_old[0].evidence_type == "life_event_miss"


def test_ph_pramana_canonical_rows_equal_the_old_unscoped_read_except_the_removed_free_text():
    """Byte-identity for the canonical chart, apart from the ONE intended change (SS N-109): with a single chart's events in the table, the scoped loader
    returns the same entries (same rows, order, dates, domains, valences) as the old unscoped loader; only `lel_jsonb` / `event_summary` differ: the id
    REFERENCE replaces the free-text summary."""
    c = FakeConn()
    for n, d in enumerate([dt.date(2011, 3, 3), dt.date(2011, 3, 3), dt.date(2015, 6, 1), dt.date(2019, 1, 9)], start=1):
        c.add_event(CHART_A, n, d, outcome=[True, False, None, True][n - 1])
    old_rows = c.db.execute("SELECT id, event_date, category, description AS event_summary, outcome_observed FROM life_events ORDER BY event_date").fetchall()
    new = _writer()._load_lel(c, CHART_A)
    assert len(new) == len(old_rows) == 4
    for e, r in zip(new, old_rows):
        assert (e.event_date, e.domain, e.lel_id) == (r["event_date"], str(r["category"] or ''), None)
        assert e.outcome_valence is None                      # SS N-112: not read (the engine never used it; it is not persisted)
        assert e.lel_jsonb == {'id': str(r['id']), 'event_date': str(r['event_date']), 'source_table': 'life_events'}
        assert e.event_summary == '' and 'summary' not in e.lel_jsonb


def test_a_derived_pramana_row_never_carries_free_text(two_charts):
    """DATA MINIMISATION (SS N-109): the loader never SELECTs `description`, and the derived record carries only the id reference."""
    from services.ph_pramana.engine import AnchorForPramana, PramanaContext, derive_pramana_records
    anchor = AnchorForPramana(anchor_id="ANC.X", domain="career", anchor_source="t", falsifier="a career event",
                              window_start=dt.date(2011, 1, 1), window_end=dt.date(2012, 12, 31), peak_date=None,
                              magnitude=None, confidence_high=None, derivation_ledger_jsonb={})
    entries = _writer()._load_lel(two_charts, CHART_A)
    assert not any("description" in s or "outcome_observed" in s for s in two_charts.selects_of_life_events())
    rec = derive_pramana_records(PramanaContext(chart_id=str(CHART_A), today=dt.date(2026, 10, 1), anchors=[anchor], lel_entries=entries))[0]
    assert rec.evidence_type == "life_event_match" and rec.lel_entry_jsonb is not None
    assert set(rec.lel_entry_jsonb) == {"id", "event_date", "source_table"}
    assert rec.lel_entry_jsonb["id"] in A_IDS
    assert "SYNTHETIC" not in repr(rec) and "MARKER" not in repr(rec)           # no free text anywhere in the derived record


def test_the_id_reference_resolves_to_the_right_chart_scoped_row_and_a_foreign_id_does_not(two_charts):
    from brahmagyan.phala.life_events_scope import resolve_life_event_text
    a1, b1 = event_uuid(CHART_A, 1), event_uuid(CHART_B, 1)
    assert resolve_life_event_text(two_charts, CHART_A, a1) == "MARKER-4820-1"
    assert resolve_life_event_text(two_charts, str(CHART_A), uuid.UUID(a1)) == resolve_life_event_text(two_charts, CHART_A, a1)
    assert resolve_life_event_text(two_charts, CHART_B, b1) == "MARKER-1c82-1"
    # a foreign id (the other chart's event) does not resolve, in either direction; nor does an unknown id or a chart without events
    assert resolve_life_event_text(two_charts, CHART_A, b1) is None
    assert resolve_life_event_text(two_charts, CHART_B, a1) is None
    assert resolve_life_event_text(two_charts, CHART_C, a1) is None
    assert resolve_life_event_text(two_charts, CHART_A, uuid.uuid4()) is None
    # strict inputs and loud failures
    with pytest.raises(ValueError):
        resolve_life_event_text(two_charts, CHART_A, "not-a-uuid")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        resolve_life_event_text(FakeConn(fail_select=psycopg.errors.InsufficientPrivilege("denied")), CHART_A, a1)
    assert two_charts.gucs[CHART_CONTEXT_GUC] == ""                           # pinned for the lookup, cleared after


def test_mutant_resolver_without_the_chart_predicate_would_resolve_a_foreign_id(two_charts):
    """Negative control: the same lookup WITHOUT the chart predicate resolves chart B's event for chart A, so the test above is discriminating."""
    b1 = event_uuid(CHART_B, 1)
    assert two_charts.db.execute("SELECT description FROM life_events WHERE id = ?", (b1,)).fetchone() is not None


def test_ph_pramana_undefined_table_is_an_empty_log_but_a_privilege_error_is_not():
    assert _writer()._load_lel(FakeConn(fail_select=psycopg.errors.UndefinedTable("absent")), CHART_A) == []
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _writer()._load_lel(FakeConn(fail_select=psycopg.errors.InsufficientPrivilege("denied")), CHART_A)


def test_ph_pramana_source_has_no_unscoped_life_events_read():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "pipeline/orchestrator/writers/ph_pramana.py").read_text()
    assert "FROM life_events" not in src and "fetch_chart_life_events" in src


# ───────────────────────────────────────────────── ph_rectification ──────────────────────────────────────────────────

def _rect_conn(view_usable):
    c = FakeConn(view_usable=view_usable)
    for n, d in enumerate([dt.date(2011, 3, 3), dt.date(2015, 6, 1)], start=1):
        c.add_event(CHART_A, n, d)
    for n, d in enumerate([dt.date(2012, 7, 7), dt.date(2016, 2, 2)], start=1):
        c.add_event(CHART_B, n, d, category="health")
    for ch, lord in ((CHART_A, "venus"), (CHART_B, "moon")):
        c.add_dasha(ch, 1, lord, dt.date(2000, 1, 1), dt.date(2030, 1, 1))
        c.add_dasha(ch, 2, lord, dt.date(2000, 1, 1), dt.date(2030, 1, 1))
    return c


@pytest.mark.parametrize("view_usable", [False, True], ids=["base_table", "view"])
def test_ph_rectification_training_events_are_chart_scoped(view_usable):
    from pipeline.orchestrator.writers.ph_rectification import _load_chart_training_events
    c = _rect_conn(view_usable)
    a = _load_chart_training_events(c, CHART_A)
    b = _load_chart_training_events(c, str(CHART_B))
    assert [e.event_id for e in a] == ["EVT.4820.1", "EVT.4820.2"] and all(e.maha_dasha_lord == "Venus" for e in a)
    assert [e.event_id for e in b] == ["EVT.1c82.1", "EVT.1c82.2"] and all(e.maha_dasha_lord == "Moon" for e in b)
    assert _load_chart_training_events(c, CHART_C) == []


@pytest.mark.parametrize("exc", [psycopg.errors.QueryCanceled("statement timeout"), psycopg.errors.DeadlockDetected("deadlock"),
                                 psycopg.errors.OperationalError("connection lost"), psycopg.errors.InFailedSqlTransaction("aborted"),
                                 psycopg.errors.LockNotAvailable("lock timeout"), RuntimeError("anything else")])
def test_ph_rectification_only_a_schema_gap_degrades_everything_else_is_loud(exc):
    """Review MED-1 (SS N-112): a timeout, deadlock, lost connection or aborted transaction is NOT 'no events'."""
    from pipeline.orchestrator.writers.ph_rectification import _load_chart_training_events
    with pytest.raises(type(exc)):
        _load_chart_training_events(FakeConn(fail_select=exc), CHART_A)


def test_ph_rectification_privilege_foreign_row_and_bad_id_propagate_but_schema_gaps_degrade():
    from pipeline.orchestrator.writers.ph_rectification import _load_chart_training_events
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _load_chart_training_events(FakeConn(fail_select=psycopg.errors.InsufficientPrivilege("denied")), CHART_A)
    with pytest.raises(ValueError):
        _load_chart_training_events(FakeConn(), "any-chart")
    for gap in (psycopg.errors.UndefinedColumn('column "chart_id" does not exist'), psycopg.errors.UndefinedTable("absent")):
        assert _load_chart_training_events(FakeConn(fail_select=gap), CHART_A) == []


def test_ph_rectification_source_has_no_unscoped_life_events_read():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "pipeline/orchestrator/writers/ph_rectification/__init__.py").read_text()
    assert "FROM life_events" not in src and "fetch_chart_life_events" in src
