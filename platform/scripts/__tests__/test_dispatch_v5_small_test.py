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
    def __init__(self, *, dependents=None, registry_row=None, row_missing=False, commit_error=None, rollback_error=None,
                 fail_on=None):
        self.statements: list[str] = []
        self.params: list[tuple] = []
        self.commits: list[int] = []
        self.rollbacks: list[int] = []
        self.dependents = dependents if dependents is not None else []
        self.registry_row = dict(dispatch.EXPECTED_REGISTRY_ROW) if registry_row is None else registry_row
        self.row_missing = row_missing
        self.commit_error, self.rollback_error, self.fail_on = commit_error, rollback_error, fail_on
        harness = self

        class FakeCur:
            def execute(self, sql, params=None):
                harness.statements.append(sql)
                harness.params.append(params)
                self._last = sql
                if harness.fail_on and harness.fail_on in sql:
                    raise Exception('could not connect: postgresql://svc:hunter2-secret@db.example/prod refused')

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
                if harness.commit_error:
                    raise harness.commit_error

            def rollback(self):
                harness.rollbacks.append(len(harness.statements))
                if harness.rollback_error and len(harness.rollbacks) == 1:
                    raise harness.rollback_error

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


BASE = ["--i-am-steward", "--after-settled-1", "--run", "all_classes_1y",
        "--horizon-start", START, "--horizon-end", END]
BASE_ARGV = BASE + ["--execute"]                      # staging for real needs explicit intent (P2-7)


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
    out = _run_main(h, BASE + ["--dry-run"], capsys)
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


# ── round 2 (ASTRA, PR 3098 P2-6 / P2-7 applied to the dispatch): intent, environment, credentials ─────────────────────────────

def test_without_execute_the_default_is_a_dry_run_that_writes_nothing(capsys):
    h = _Harness()
    out = _run_main(h, BASE, capsys)                  # no --execute, no --dry-run
    assert not h.commits and len(h.rollbacks) == 1
    assert "[dry-run]" in out.err and json.loads(out.out)["asset_id"] == "ka_gochara_v5"


def test_only_execute_commits(capsys):
    h = _Harness()
    _run_main(h, BASE + ["--execute"], capsys)
    assert len(h.commits) == 1 and not h.rollbacks


def test_dry_run_and_execute_are_mutually_exclusive(capsys):
    h = _Harness()
    with pytest.raises(SystemExit) as exc:
        _run_main(h, BASE + ["--dry-run", "--execute"], capsys)
    assert exc.value.code == 2 and h.statements == []


def test_execute_still_needs_both_steward_flags(capsys):
    h = _Harness()
    with pytest.raises(SystemExit) as exc:
        _run_main(h, ["--run", "all_classes_1y", "--horizon-start", START, "--horizon-end", END, "--execute"], capsys)
    assert exc.value.code == 2 and h.statements == []


def _run_cli(harness, argv, capsys, *, connect_error=None, database_url="postgresql://fake/fake"):
    fake_psycopg = types.ModuleType("psycopg")
    fake_rows = types.ModuleType("psycopg.rows")
    fake_rows.dict_row = object()
    fake_psycopg.rows = fake_rows
    connects = []

    def connect(*a, **k):
        connects.append(a)
        if connect_error:
            raise connect_error
        return harness.conn
    fake_psycopg.connect = connect
    saved = {k: v for k, v in sys.modules.items() if k.startswith("psycopg")}
    prior = os.environ.get("DATABASE_URL")
    try:
        sys.modules["psycopg"], sys.modules["psycopg.rows"] = fake_psycopg, fake_rows
        if database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = database_url
        code = _load_fresh().cli(argv)
        return code, capsys.readouterr(), connects
    finally:
        for name in ("psycopg", "psycopg.rows"):
            sys.modules.pop(name, None)
        sys.modules.update(saved)
        if prior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior


def test_the_database_url_comes_only_from_the_process_environment(capsys):
    h = _Harness()
    code, streams, connects = _run_cli(h, BASE_ARGV, capsys, database_url=None)
    assert code == 2 and connects == [] and "DATABASE_URL is not set" in streams.err
    source = DISPATCH.read_text(encoding="utf-8")
    assert ".env.local" not in source.replace("no longer reads `.env.local`", "") and "open(" not in source


def test_a_connection_error_prints_the_class_and_never_the_text(capsys):
    """Codex P2-6: a malformed-URI error carries the password token; the boundary prints the class only."""
    h = _Harness()
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys,
                                connect_error=ValueError("invalid percent-encoding in postgresql://svc:hunter2-secret@db.example/prod"))
    text = streams.err + streams.out
    assert code == 1 and "ValueError" in streams.err and "hunter2" not in text and "postgresql://" not in text


def test_a_named_refusal_is_printed_and_exits_one(capsys):
    h = _Harness(dependents=[{"asset_id": "ka_some_dependent"}])
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    assert code == 1 and "dispatch refused" in streams.err and "ka_some_dependent" in streams.err
    assert not h.commits


def test_the_cli_keeps_the_steward_exit_code(capsys):
    h = _Harness()
    code, streams, connects = _run_cli(h, ["--run", "all_classes_1y", "--horizon-start", START, "--horizon-end", END], capsys)
    assert code == 2 and connects == []


# ── round 2 (ASTRA v1.1, items 3 and 6, applied to the dispatch): the teardown deadline and honest failure reporting ─────────────

def test_a_real_dispatch_prints_the_teardown_deadline_ninety_days_out(capsys):
    h = _Harness()
    out = _run_main(h, BASE_ARGV, capsys)
    assert "TEARDOWN DEADLINE" in out.err and "90 days from now" in out.err and "V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md" in out.err
    assert out.out.strip() and "\n" not in out.out.strip()                       # stdout still carries only the run id
    import datetime as dt
    stamp = out.err.split("tear the small test down by ")[1].split(" ")[0]
    delta = dt.datetime.fromisoformat(stamp) - dt.datetime.now(dt.timezone.utc)
    assert dt.timedelta(days=89) < delta < dt.timedelta(days=91)


def test_the_dry_run_names_the_deadline_a_real_dispatch_would_print(capsys):
    out = _run_main(_Harness(), BASE + ["--dry-run"], capsys)
    assert "teardown deadline 90 days out" in out.err


def test_the_docstring_tells_the_steward_to_tear_down_within_ninety_days():
    assert dispatch.RETENTION_DAYS == 90
    assert "TEAR THE SMALL TEST DOWN WITHIN 90 DAYS" in dispatch.__doc__ and "V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md" in dispatch.__doc__


def test_a_failure_before_the_commit_reports_a_confirmed_rollback(capsys):
    h = _Harness(fail_on="INSERT INTO build_runs")
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    assert code == 1 and "ROLLBACK CONFIRMED" in streams.err and "COMMIT OUTCOME UNKNOWN" not in streams.err and not h.commits
    assert "hunter2" not in streams.err + streams.out


def test_a_failure_AT_the_commit_is_an_unknown_outcome_never_nothing_committed(capsys):
    """Once COMMIT has been sent nobody may claim the database is unchanged, and no rollback is attempted."""
    h = _Harness(commit_error=ConnectionError("server closed the connection (postgresql://svc:hunter2-secret@db/prod)"))
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    text = streams.err + streams.out
    assert code == 1 and "COMMIT OUTCOME UNKNOWN" in text and "may or may not exist" in text
    assert "ROLLBACK CONFIRMED" not in text and "changed nothing" not in text and "hunter2" not in text
    assert len(h.commits) == 1 and not h.rollbacks


def test_a_failed_rollback_is_reported_as_not_confirmed(capsys):
    h = _Harness(fail_on="INSERT INTO build_runs", rollback_error=ConnectionError("lost"))
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    assert code == 1 and "ROLLBACK NOT CONFIRMED" in streams.err and "ROLLBACK CONFIRMED:" not in streams.err


def test_a_connection_failure_says_no_transaction_was_opened(capsys):
    code, streams, _ = _run_cli(_Harness(), BASE_ARGV, capsys, connect_error=ValueError("bad uri postgresql://svc:hunter2-secret@x/y"))
    assert code == 1 and "No transaction was opened" in streams.err and "hunter2" not in streams.err + streams.out


def test_a_named_refusal_after_the_connection_reports_its_confirmed_rollback(capsys):
    code, streams, _ = _run_cli(_Harness(dependents=[{"asset_id": "ka_dep"}]), BASE_ARGV, capsys)
    assert code == 1 and "ka_dep" in streams.err and "ROLLBACK CONFIRMED" in streams.err


def test_the_script_never_claims_nothing_was_committed():
    assert "othing was committed" not in DISPATCH.read_text(encoding="utf-8")


# ── round 3 (Codex v1.2, item 2): the marker is staged in its CANONICAL form and round-trips through writer and teardown ──────────

def test_a_comma_list_in_any_order_and_any_utc_offset_is_staged_in_the_canonical_form():
    """Sorted (scored-order) classes and +00:00 ISO timestamps, exactly the text the writer's own component stores."""
    scrambled = ",".join(reversed(ALL))
    marker = dispatch.build_slice_marker(run="all_classes_1y", classes=scrambled,
                                         horizon_start="2025-04-01T00:00:00Z", horizon_end="2026-04-01T05:30:00+05:30")
    assert marker["classes"] == ALL == sorted(ALL)
    assert marker["horizon"] == ["2025-04-01T00:00:00+00:00", "2026-04-01T00:00:00+00:00"]
    assert marker == {"schema": "gochara_v5_test_slice/1", "run": "all_classes_1y", "horizon": marker["horizon"], "classes": ALL}


def test_the_staged_marker_is_the_writers_normal_form_so_its_digest_is_the_components():
    marker = dispatch.build_slice_marker(run="all_classes_1y", classes=",".join(reversed(ALL)),
                                         horizon_start="2025-04-01T00:00:00Z", horizon_end="2026-04-01T00:00:00Z")
    sliced = WRITER._validate_test_slice(marker)
    component = WRITER._slice_component(sliced)
    # rebuilding the marker from the stored (normalised) component gives the SAME marker and the SAME digest
    rebuilt = {"schema": component["schema"], "run": component["run"], "horizon": component["horizon"], "classes": component["classes"]}
    assert rebuilt == marker and WRITER._validate_test_slice(rebuilt).digest == sliced.digest == component["marker_digest"]


@pytest.mark.parametrize("run, kw", [
    ("all_classes_1y", dict(classes="all", horizon_start="2025-04-17T00:00:00+00:00", horizon_end="2026-04-17T00:00:00+00:00")),
    ("all_classes_1y", dict(classes=",".join(reversed(ALL)), horizon_start="2025-04-01T00:00:00Z", horizon_end="2026-03-01T00:00:00Z")),
    ("one_class_full", dict(classes=ONE)),
], ids=["all_default_order", "all_scrambled_Z_timestamps", "one_class_full"])
def test_a_dispatched_marker_round_trips_through_the_writer_and_the_teardown_validation(run, kw):
    """What a dispatch stages is accepted by the writer, stamped by the writer's own component, and the TEARDOWN's stamp validation
    accepts that stamp (by reconstruction, with no run row at all). Skipped until the teardown script (PR 3098) is in the tree."""
    teardown_path = DISPATCH.parent / "teardown_v5_small_test_job.py"
    if not teardown_path.exists():
        pytest.skip("teardown_v5_small_test_job.py is not in this tree yet (PR 3098); the round trip is asserted once both are")
    import types as _t
    import teardown_v5_small_test_job as td
    marker = dispatch.build_slice_marker(run=run, **kw)
    sliced = WRITER._validate_test_slice(marker)
    vector = {"stored_scope": WRITER.TEST_SLICE_SCOPE, "test_slice": WRITER._slice_component(sliced)}
    horizon = _t.SimpleNamespace(lower=sliced.horizon[0], upper=sliced.horizon[1])
    problem, source = td._stamp_problem(vector, horizon, [])                          # no surviving run row: the reconstruction path
    assert problem is None and "RECONSTRUCTION" in source
    manifest = {WRITER.TEST_SLICE_KEY: marker}
    problem, source = td._stamp_problem(vector, horizon, [("run-1", manifest, WRITER._manifest_digest(manifest))])
    assert problem is None and "ORIGINAL marker of run run-1" in source               # and against the original preimage
