"""C37 — stubbed-connection unit tests for platform/scripts/dispatch_v5_small_test_job.py.

No database, no production: `psycopg` is replaced by a recording fake, so the real statement order of
main() is exercised end-to-end. The slice marker is checked against the REAL writer
(pipeline.orchestrator.writers.ka_gochara_v5): the marker the dispatch builds must be ACCEPTED by the
writer's own validator for BOTH runs, and every shape the writer refuses must be refused before any
database connection. The registry row is checked against the migration-1304 shape (a pre-1304 row is
refused, a missing row is refused, no INSERT into asset_registry is ever issued).
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
DISPATCH = REPO / "platform/scripts/dispatch_v5_small_test_job.py"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

sys.path.insert(0, str(DISPATCH.parent))
import dispatch_v5_small_test_job as dispatch  # noqa: E402


def _load_fresh():
    return importlib.reload(dispatch)


# ── the steward flag refusal (before ANY import of psycopg / DB touch) ───────

def test_refuses_without_both_steward_flags(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    common = ["--run", "all_classes_1y", "--horizon-start", "2025-04-01T00:00:00+00:00",
              "--horizon-end", "2026-04-01T00:00:00+00:00"]
    for argv in (common, ["--i-am-steward"] + common, ["--after-settled-1"] + common):
        with pytest.raises(SystemExit) as exc:
            _load_fresh().main(argv)
        assert exc.value.code == 2


# ── build_slice_marker: the WRITER is the oracle ─────────────────────────────

WRITER = dispatch._writer()
ALL = list(WRITER.SCORED_CLASSES)
ONE = ALL[0]
START, END = "2025-04-01T00:00:00+00:00", "2026-04-01T00:00:00+00:00"
MARKER = {"schema": "gochara_v5_test_slice/1", "run": "all_classes_1y",
          "horizon": [START, END], "classes": ALL}
FULL = [x.astimezone(__import__("datetime").timezone.utc).isoformat() for x in WRITER.DEFAULT_HORIZON]
ONE_MARKER = {"schema": "gochara_v5_test_slice/1", "run": "one_class_full",
              "horizon": FULL, "classes": [ONE]}


def test_all_classes_1y_marker_is_accepted_by_the_writer_and_names_every_scored_class():
    m = dispatch.build_slice_marker(run="all_classes_1y", horizon_start=START, horizon_end=END)
    assert m == MARKER and len(m["classes"]) == 26
    assert set(m) == {"schema", "run", "horizon", "classes"}      # no extra fields, ever
    sl = WRITER._validate_test_slice(m)                           # the writer's own verdict
    assert sl.run == "all_classes_1y" and set(sl.classes) == set(ALL)


def test_one_class_full_marker_is_accepted_by_the_writer_and_defaults_to_the_full_horizon():
    m = dispatch.build_slice_marker(run="one_class_full", classes=ONE)
    assert m == ONE_MARKER
    sl = WRITER._validate_test_slice(m)
    assert sl.run == "one_class_full" and sl.horizon == WRITER.DEFAULT_HORIZON and sl.classes == (ONE,)


def test_classes_all_equals_the_default_and_a_comma_list_is_stripped():
    assert dispatch.build_slice_marker(run="all_classes_1y", classes="all", horizon_start=START,
                                       horizon_end=END) == MARKER
    m = dispatch.build_slice_marker(run="one_class_full", classes=f" {ONE} ")
    assert m["classes"] == [ONE]


def test_non_utc_offsets_are_stored_in_utc():
    m = dispatch.build_slice_marker(run="all_classes_1y", horizon_start="2025-04-01T05:30:00+05:30",
                                    horizon_end="2026-04-01T05:30:00+05:30")
    assert m["horizon"] == [START, END]


@pytest.mark.parametrize("kwargs, why", [
    (dict(run="everything", classes="all", horizon_start=START, horizon_end=END), "unknown run"),
    (dict(run="all_classes_1y", horizon_start="2026-01-01T00:00:00", horizon_end=END), "naive start"),
    (dict(run="all_classes_1y", horizon_start="2025-04-01", horizon_end="2026-04-01"), "date-only (no zone)"),
    (dict(run="all_classes_1y", horizon_start="jan", horizon_end=END), "unparseable"),
    (dict(run="all_classes_1y", horizon_start=END, horizon_end=START), "inverted"),
    (dict(run="all_classes_1y", horizon_start=START), "only one bound"),
    (dict(run="all_classes_1y"), "no horizon for the 1-year run"),
    (dict(run="all_classes_1y", horizon_start="2024-01-01T00:00:00+00:00",
          horizon_end="2026-01-01T00:00:00+00:00"), "longer than a year, inside the horizon"),
    (dict(run="all_classes_1y", horizon_start="2026-01-01T00:00:00+00:00",
          horizon_end="2026-04-18T00:00:00+00:00"), "past DEFAULT_HORIZON end"),
    (dict(run="all_classes_1y", classes=f"{ONE}", horizon_start=START, horizon_end=END), "1y run with one class"),
    (dict(run="all_classes_1y", classes="solar", horizon_start=START, horizon_end=END), "not a scored class"),
    (dict(run="all_classes_1y", classes=" , ", horizon_start=START, horizon_end=END), "empty list"),
    (dict(run="one_class_full"), "one_class_full without a class"),
    (dict(run="one_class_full", classes="all"), "one_class_full with every class"),
    (dict(run="one_class_full", classes=f"{ALL[0]},{ALL[1]}"), "one_class_full with two classes"),
    (dict(run="one_class_full", classes=ONE, horizon_start=START, horizon_end=END), "one_class_full not the full horizon"),
    (dict(run="one_class_full", classes=ONE, horizon_start=START), "only one bound"),
], ids=lambda v: v if isinstance(v, str) else "")
def test_every_shape_the_writer_refuses_is_refused_before_a_marker_exists(kwargs, why):
    with pytest.raises((RuntimeError, WRITER.TestSliceRefusal)):
        dispatch.build_slice_marker(**kwargs)


def test_the_dispatch_calls_the_writers_own_validator(monkeypatch):
    """Mutation guard: if the writer starts refusing, the dispatch must follow — it may not carry its own copy of the rules."""
    def refusing(marker):
        raise WRITER.TestSliceRefusal("writer says no")
    monkeypatch.setattr(WRITER, "_validate_test_slice", refusing)
    with pytest.raises(WRITER.TestSliceRefusal, match="writer says no"):
        dispatch.build_slice_marker(run="all_classes_1y", horizon_start=START, horizon_end=END)


def test_manifest_carries_the_slice_marker_and_digests_it_and_the_registry_dependencies():
    candidate = {"asset_id": "ka_gochara_v5", "scope": "per_chart", "depends_on": ["ga_positions", "ga_dashas"],
                 "natural_key_partition": None, "has_cowriters": False}
    manifest, digest = dispatch.build_small_test_manifest(candidate=candidate, slice_marker=MARKER)
    assert manifest["version"] == "nirmana-run-manifest/v1"
    assert manifest["scope_target"] == "ka_gochara_v5"
    assert manifest["chart_id"] == CHART_ID
    assert manifest["gochara_v5_test_slice"] == MARKER
    # the runner requires the frozen manifest's asset_deps to equal the registry's depends_on
    assert manifest["assets"][0]["depends_on"] == dispatch.EXPECTED_REGISTRY_ROW["depends_on"]
    import hashlib
    canonical = json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_expected_registry_row_is_the_1304_values():
    e = dispatch.EXPECTED_REGISTRY_ROW
    assert (e["has_substeps"], e["writer_timeout_seconds"], e["depends_on"], e["target_table"], e["is_active"]) == (
        True, 7200, ["ga_positions", "ga_dashas"], "ka_gochara_eval_window", False)
    sql = (REPO / "platform/migrations/1304_ka_gochara_v5_registry_row_small_test.sql")
    if sql.exists():   # present once PR 3101 is in the tree: the two must agree on the counter text
        assert e["count_sql"].replace("'", "''") in sql.read_text(encoding="utf-8")


# ── recording fake psycopg ────────────────────────────────────────────────────

class _Harness:
    def __init__(self, *, dependents=None, registry_row=None, row_missing=False):
        self.statements: list[str] = []
        self.params: list[tuple] = []
        self.commits: list[int] = []
        self.rollbacks: list[int] = []
        self.dependents = dependents if dependents is not None else []
        self.registry_row = dict(dispatch.EXPECTED_REGISTRY_ROW) if registry_row is None else registry_row
        self.row_missing = row_missing
        harness = self

        class FakeCur:
            def execute(self, sql, params=None):
                harness.statements.append(sql)
                harness.params.append(params)
                self._last = sql

            def fetchall(self):
                if "ANY(depends_on)" in self._last:
                    return harness.dependents
                return []

            def fetchone(self):
                if "FROM asset_registry WHERE asset_id" in self._last:
                    return None if harness.row_missing else harness.registry_row
                if "has_cowriters" in self._last:
                    return {"asset_id": "ka_gochara_v5", "layer": "kala",
                            "scope": "per_chart", "asset_kind": "data",
                            "depends_on": ["ga_positions", "ga_dashas"], "natural_key_partition": None,
                            "has_cowriters": False}
                return None

        class FakeConn:
            autocommit = False

            def cursor(self):
                return FakeCur()

            def commit(self):
                harness.commits.append(len(harness.statements))

            def rollback(self):
                harness.rollbacks.append(len(harness.statements))

            def close(self):
                pass

        self.conn = FakeConn()


def _run_main(harness: _Harness, argv: list[str], capsys):
    fake_psycopg = types.ModuleType("psycopg")
    fake_rows = types.ModuleType("psycopg.rows")
    fake_rows.dict_row = object()
    fake_psycopg.rows = fake_rows
    fake_psycopg.connect = lambda *a, **k: harness.conn
    saved = {k: v for k, v in sys.modules.items() if k.startswith("psycopg")}
    prior_db_url = os.environ.get("DATABASE_URL")
    try:
        sys.modules["psycopg"] = fake_psycopg
        sys.modules["psycopg.rows"] = fake_rows
        os.environ["DATABASE_URL"] = "postgresql://fake/fake"
        _load_fresh().main(argv)
        return capsys.readouterr()
    finally:
        for name in ("psycopg", "psycopg.rows"):
            sys.modules.pop(name, None)
        sys.modules.update(saved)
        if prior_db_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior_db_url


BASE_ARGV = ["--i-am-steward", "--after-settled-1", "--run", "all_classes_1y",
             "--horizon-start", START, "--horizon-end", END]


def test_staging_is_one_transaction_ending_inert(capsys):
    h = _Harness()
    out = _run_main(h, BASE_ARGV, capsys)
    assert len(h.commits) == 1 and not h.rollbacks
    staged = h.statements[: h.commits[0]]
    flips = [s for s in staged if "SET is_active" in s]
    assert flips[0].count("is_active = true") == 1
    assert flips[-1].count("is_active = false") == 1
    assert any("INSERT INTO build_runs" in s and "plan_manifest" in s for s in staged)
    assert any("INSERT INTO build_run_assets" in s for s in staged)
    assert any("asset_throughput" in s and "dormant" in s for s in staged)
    # the staged run names the small-test trigger and carries the slice marker
    run_insert = next(i for i, s in enumerate(h.statements) if "INSERT INTO build_runs" in s)
    params = h.params[run_insert]
    assert params[1] == CHART_ID and params[2] == "ka_gochara_v5"
    assert params[-1] == "gochara-v5-small-test"
    manifest = json.loads(params[4])
    assert manifest["gochara_v5_test_slice"] == MARKER
    assert params[3] == json.dumps(["ka_gochara_v5"])
    # stdout carries ONLY the run_id
    run_id = out.out.strip()
    assert run_id and "\n" not in run_id


def test_dry_run_rolls_back_and_prints_the_plan(capsys):
    h = _Harness()
    out = _run_main(h, BASE_ARGV + ["--dry-run"], capsys)
    assert not h.commits and len(h.rollbacks) == 1
    assert "[dry-run]" in out.err and "nothing written" in out.err
    plan = json.loads(out.out)
    assert plan["triggered_by"] == "gochara-v5-small-test"
    assert plan["asset_id"] == "ka_gochara_v5" and plan["chart_id"] == CHART_ID
    assert plan["plan_manifest"]["gochara_v5_test_slice"] == MARKER


def test_dependents_refuse_the_dispatch(capsys):
    h = _Harness(dependents=[{"asset_id": "some_other_asset"}])
    with pytest.raises(RuntimeError, match="nothing may depend"):
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits
    assert not any("INSERT INTO build_runs" in s for s in h.statements)


def test_no_insert_into_asset_registry_is_ever_issued(capsys):
    h = _Harness()
    _run_main(h, BASE_ARGV, capsys)
    assert not any("INSERT INTO asset_registry" in s for s in h.statements)


@pytest.mark.parametrize("field, bad", [
    ("has_substeps", False), ("writer_timeout_seconds", 600), ("depends_on", []),
    ("depends_on", ["ga_dashas", "ga_positions"]), ("target_table", "kala_gochara_windows"),
    ("count_sql", "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='5.0'"),
    ("is_active", True), ("has_writer", False), ("scope", "global"), ("target_floor", 5),
    ("estimated_seconds", 60),
])
def test_a_row_not_in_the_1304_shape_refuses(capsys, field, bad):
    row = dict(dispatch.EXPECTED_REGISTRY_ROW)
    row[field] = bad
    h = _Harness(registry_row=row)
    with pytest.raises(RuntimeError, match=field):
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits
    assert not any("INSERT INTO build_runs" in s for s in h.statements)


def test_the_pre_1304_row_is_refused(capsys):
    pre = {"scope": "per_chart", "is_active": False, "has_writer": True, "has_substeps": False,
           "writer_timeout_seconds": 600, "depends_on": [], "target_table": "kala_gochara_windows",
           "count_sql": "SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation='5.0'",
           "target_floor": 0, "estimated_seconds": None}
    with pytest.raises(RuntimeError, match="1304"):
        _run_main(_Harness(registry_row=pre), BASE_ARGV, capsys)


def test_a_missing_registry_row_is_refused_not_inserted(capsys):
    h = _Harness(row_missing=True)
    with pytest.raises(RuntimeError, match="no ka_gochara_v5 row"):
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits and not any("INSERT INTO asset_registry" in s for s in h.statements)


def test_a_marker_the_writer_refuses_never_reaches_the_database(capsys):
    """The refusal happens before psycopg is even imported: no connection, no statements, exit 2."""
    h = _Harness()
    bad = ["--i-am-steward", "--after-settled-1", "--run", "all_classes_1y",
           "--horizon-start", "2025-04-01T00:00:00", "--horizon-end", END]       # naive timestamp
    with pytest.raises(SystemExit) as exc:
        _run_main(h, bad, capsys)
    assert exc.value.code == 2
    assert h.statements == [] and not h.commits and not h.rollbacks


def test_one_class_full_stages_a_marker_the_writer_accepts(capsys):
    h = _Harness()
    out = _run_main(h, ["--i-am-steward", "--after-settled-1", "--run", "one_class_full",
                        "--classes", ONE, "--dry-run"], capsys)
    plan = json.loads(out.out)
    assert plan["plan_manifest"]["gochara_v5_test_slice"] == ONE_MARKER
    WRITER._validate_test_slice(plan["plan_manifest"]["gochara_v5_test_slice"])


def test_help_runs(capsys):
    with pytest.raises(SystemExit) as exc:
        _load_fresh().main(["--help"])
    assert exc.value.code == 0
    assert "--i-am-steward" in capsys.readouterr().out
