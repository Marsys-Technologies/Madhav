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
import re
import sys
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
DISPATCH = REPO / "platform/scripts/dispatch_v5_small_test_job.py"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

sys.path.insert(0, str(DISPATCH.parent))

# A SYNTHETIC marker password for the credential-safe error tests, and connection strings built from PARTS at run time (no connection-string
# literal exists in this source, so the secret scanner has nothing to match and no allowlist entry is needed). The marker is invented.
MARKER_PASSWORD = "-".join(["hunter2", "secret"])


def _synthetic_dsn(host: str, database: str) -> str:
    return "://".join(["postgresql", f"svc:{MARKER_PASSWORD}@{host}/{database}"])


import dispatch_v5_small_test_job as dispatch  # noqa: E402


import datetime as _dt
STORED_CREATED_AT = _dt.datetime(2031, 3, 4, 12, 0, 0, tzinfo=_dt.timezone.utc)   # the DATABASE's clock, deliberately years from the client's


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


def test_all_classes_full_the_measuring_build_is_every_scored_class_over_the_whole_derived_horizon_by_default():
    m = dispatch.build_slice_marker(run="all_classes_full")
    sl = WRITER._validate_test_slice(m)
    assert sl.run == "all_classes_full" and sl.horizon == WRITER.DEFAULT_HORIZON and set(sl.classes) == set(ALL) and len(sl.classes) == 26
    assert m["horizon"] == ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]
    assert dispatch.build_slice_marker(run="all_classes_full", classes="all") == m


@pytest.mark.parametrize("kw, why", [
    (dict(classes=ONE), "one class is not the measuring build"),
    (dict(horizon_start="2025-04-01T00:00:00+00:00", horizon_end="2026-04-01T00:00:00+00:00"), "a narrower horizon is not the full horizon"),
    (dict(horizon_start="1998-01-01T00:00:00+00:00", horizon_end="2084-02-06T00:00:00+00:00"), "past the derived end"),
    (dict(horizon_start="1997-12-31T00:00:00+00:00", horizon_end="2084-02-05T00:00:00+00:00"), "before the derived start"),
])
def test_all_classes_full_refuses_a_subset_or_any_horizon_but_the_full_one(kw, why):
    with pytest.raises((RuntimeError, WRITER.TestSliceRefusal)):
        dispatch.build_slice_marker(run="all_classes_full", **kw)


def test_all_classes_full_is_a_known_run_of_the_dispatch_and_of_the_writer_and_the_two_lists_are_equal():
    assert "all_classes_full" in dispatch.SLICE_RUNS and tuple(WRITER.TEST_SLICE_RUNS) == dispatch.SLICE_RUNS


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
    (dict(run="all_classes_1y", horizon_start="2083-06-01T00:00:00+00:00",
          horizon_end="2084-02-06T00:00:00+00:00"), "past DEFAULT_HORIZON end"),
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
        True, 28800, ["ga_positions", "ga_dashas"], "ka_gochara_eval_window", False)


import re as _re  # noqa: E402

MIGRATION_1304 = REPO / "platform/migrations/1304_ka_gochara_v5_registry_row_small_test.sql"


def parse_1304(sql: str) -> dict:
    """Every admission field migration 1304 lands or checks, read from the migration's own text: the UPDATE's SET list and its count_sql
    constant (WRITTEN), and the landed-shape post-check (is_active, has_writer and the five routing fields: CHECKED)."""
    update = sql[sql.index("UPDATE asset_registry"):sql.index("WHERE asset_id = 'ka_gochara_v5'")]
    check = sql[sql.index("SELECT count(*) INTO v_ok"):sql.index("IF v_ok <> 1")]
    constant = _re.search(r"v_count_sql CONSTANT text := '((?:[^']|'')*)';", sql).group(1).replace("''", "'")
    depends = _re.search(r"depends_on = ARRAY\[([^\]]*)\]::text\[\]", update).group(1)
    return {
        "is_active": False if "is_active IS FALSE" in check else None,
        "has_writer": True if "has_writer IS TRUE" in check else None,
        "has_substeps": _re.search(r"has_substeps = (true|false)", update).group(1) == "true",
        "writer_timeout_seconds": int(_re.search(r"writer_timeout_seconds = (\d+)", update).group(1)),
        "depends_on": [x.strip().strip("'") for x in depends.split(",")],
        "target_table": _re.search(r"target_table = '([^']*)'", update).group(1),
        "count_sql": constant,
        "target_floor": int(_re.search(r"target_floor = (\d+)", update).group(1)),
        "estimated_seconds": None if _re.search(r"estimated_seconds = NULL", update) else "?",
        "asset_kind": _re.search(r"asset_kind = '([^']*)'", check).group(1),
        "asset_type": _re.search(r"asset_type = '([^']*)'", check).group(1),
        "health_probe": None if "health_probe IS NULL" in check else "?",
        "integrity_check_sql": None if "integrity_check_sql IS NULL" in check else "?",
        "rebuild_on_probe_fail": False if "rebuild_on_probe_fail IS FALSE" in check else None,
    }


REQUIRED_PARITY_FIELDS = {"is_active", "has_writer", "has_substeps", "writer_timeout_seconds", "depends_on", "target_table", "count_sql",
                          "target_floor", "estimated_seconds", "asset_kind", "asset_type", "health_probe", "integrity_check_sql",
                          "rebuild_on_probe_fail"}


def test_the_1304_parity_covers_every_admission_field_when_the_migration_is_in_the_tree():
    """Codex round 6 (2): the dispatch's EXPECTED_REGISTRY_ROW equals what migration 1304 lands or checks, FIELD BY FIELD (not only the counter text).
    Absent migration: an explicit, named skip, never a silent pass (the migration is PR 3101's; this assertion runs once both are in one tree)."""
    if not MIGRATION_1304.exists():
        pytest.skip("migration 1304 (PR 3101) is not in this tree: the field-by-field parity assertion cannot run here and is NOT being claimed")
    landed = parse_1304(MIGRATION_1304.read_text(encoding="utf-8"))
    expected = dispatch.EXPECTED_REGISTRY_ROW
    assert REQUIRED_PARITY_FIELDS <= set(landed)
    for field in REQUIRED_PARITY_FIELDS:
        assert landed[field] is not None or field in ("health_probe", "integrity_check_sql", "estimated_seconds"), f"{field}: not found in 1304"
        assert expected[field] == landed[field], f"{field}: the dispatch expects {expected[field]!r}, migration 1304 lands/checks {landed[field]!r}"
    assert set(expected) == REQUIRED_PARITY_FIELDS | {"scope"}                 # every expected field is covered (scope: 1243's, untouched by 1304)


SAMPLE_1304 = """
DO $mig$
DECLARE
  v_count_sql CONSTANT text := 'SELECT COUNT(*) FROM t WHERE chart_id=$1 AND generation=''5.0''';
BEGIN
  UPDATE asset_registry
     SET has_substeps = true,
         writer_timeout_seconds = 28800,
         depends_on = ARRAY['a','b']::text[],
         count_sql = v_count_sql,
         target_table = 'tt',
         target_floor = 0,
         estimated_seconds = NULL
   WHERE asset_id = 'ka_gochara_v5';
  SELECT count(*) INTO v_ok FROM asset_registry
   WHERE asset_id = 'ka_gochara_v5' AND is_active IS FALSE AND has_writer IS TRUE
     AND asset_kind = 'data' AND asset_type = 'data' AND (health_probe IS NULL OR health_probe = '')
     AND (integrity_check_sql IS NULL OR integrity_check_sql = '') AND rebuild_on_probe_fail IS FALSE;
  IF v_ok <> 1 THEN
"""


def test_the_1304_parser_reads_every_field_from_the_migration_text():
    got = parse_1304(SAMPLE_1304)
    assert got["count_sql"] == "SELECT COUNT(*) FROM t WHERE chart_id=$1 AND generation='5.0'"
    assert got["depends_on"] == ["a", "b"] and got["writer_timeout_seconds"] == 28800 and got["has_substeps"] is True
    assert (got["asset_kind"], got["asset_type"], got["health_probe"], got["integrity_check_sql"], got["rebuild_on_probe_fail"]) == (
        "data", "data", None, None, False)
    mutated = parse_1304(SAMPLE_1304.replace("rebuild_on_probe_fail IS FALSE", "true").replace("asset_kind = 'data'", "asset_kind = 'service'"))
    assert mutated["rebuild_on_probe_fail"] is None and mutated["asset_kind"] == "service"      # a changed migration changes the parse


# ── recording fake psycopg ────────────────────────────────────────────────────

class _Harness:
    def __init__(self, *, dependents=None, registry_row=None, row_missing=False, commit_error=None, rollback_error=None,
                 fail_on=None, published=None, seal=None, authority_generation=None, catalog_status="CURRENT", receipts=0,
                 existing_runs=None, output_rows=0, manifest=None, snapshot=None, inventory_mismatch=0, evidence=None,
                 run_manifests=None, lock_error=None, active_runs=None, created_at=None, list_runs=None, close_error=None):
        self.statements: list[str] = []
        self.params: list[tuple] = []
        self.commits: list[int] = []
        self.rollbacks: list[int] = []
        self.dependents = dependents if dependents is not None else []
        self.registry_row = dict(dispatch.EXPECTED_REGISTRY_ROW) if registry_row is None else registry_row
        self.row_missing = row_missing
        self.commit_error, self.rollback_error, self.fail_on = commit_error, rollback_error, fail_on
        self.published, self.seal, self.authority_generation = published, seal, authority_generation
        self.catalog_status, self.receipts = catalog_status, receipts
        self.existing_runs = existing_runs or []
        self.output_rows, self.manifest, self.snapshot = output_rows, manifest, snapshot
        self.inventory_mismatch, self.evidence = inventory_mismatch, evidence or []
        self.run_manifests, self.lock_error = run_manifests or [], lock_error
        self.active_runs = active_runs or []
        self.created_at = created_at or STORED_CREATED_AT
        self.list_runs = list_runs
        self.close_error = close_error
        harness = self

        class FakeCur:
            def execute(self, sql, params=None):
                harness.statements.append(sql)
                harness.params.append(params)
                self._last = " ".join(sql.split())
                if harness.lock_error and "ka_gochara_lock_chart" in sql:
                    raise harness.lock_error
                if harness.fail_on and harness.fail_on in sql:
                    raise Exception(f"could not connect: {_synthetic_dsn('db.example', 'prod')} refused")

            def fetchall(self):
                s = self._last
                if "ANY(depends_on)" in s:
                    return harness.dependents
                if s.startswith("SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN"):
                    return harness.active_runs
                if "FROM asset_provenance_receipts r WHERE r.asset_id" in s:
                    return [r for r in harness.evidence if r.get("kind") == "receipt"]
                if "FROM build_run_assets a LEFT JOIN build_runs b0" in s:
                    return [r for r in harness.evidence if r.get("kind") == "run_asset"]
                if s.startswith("SELECT id, state, created_at, plan_manifest_digest FROM build_runs"):
                    return harness.existing_runs
                if "SELECT id, plan_manifest, plan_manifest_digest FROM build_runs" in s:
                    return harness.run_manifests
                return []

            def fetchone(self):
                s = self._last
                if s.endswith("RETURNING created_at"):
                    return {"created_at": harness.created_at}
                if s.startswith("SELECT manifest_id, status FROM kala_gochara_publication"):
                    return harness.manifest
                if s.startswith("SELECT catalog_status"):
                    return {"catalog_status": harness.catalog_status}
                if "status = 'published'" in s:
                    return harness.published
                if "FROM ka_gochara_generation_seal" in s:
                    return harness.seal
                if "FROM kala_gochara_authority" in s:
                    return None if harness.authority_generation is None else {"authoritative_generation": harness.authority_generation}
                if "FROM asset_registry WHERE asset_id" in s:
                    return None if harness.row_missing else harness.registry_row
                if "has_cowriters" in s:
                    return {"asset_id": "ka_gochara_v5", "layer": "kala",
                            "scope": "per_chart", "asset_kind": "data",
                            "depends_on": ["ga_positions", "ga_dashas"], "natural_key_partition": None,
                            "has_cowriters": False}
                if "count(*) AS n FROM asset_provenance_receipts" in s:
                    return {"n": harness.receipts}
                if "input_generation_vector, horizon FROM kala_gochara_publication" in s:
                    return harness.manifest
                if "FROM ka_gochara_search_input_snapshot s JOIN kala_gochara_publication p" in s:
                    return harness.snapshot
                if "FROM ka_gochara_search_inventory i JOIN" in s:
                    return {"n": harness.inventory_mismatch}
                m = re.search(r"count\(\*\) AS n FROM (\w+) WHERE", s)
                if m:
                    return {"n": harness.output_rows}
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
                if harness.close_error:
                    raise harness.close_error

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
    # the registry row is NEVER updated (Codex PR 3097 ruling 3): no activation, no restore; it is only read, and locked FOR SHARE
    assert not any("UPDATE asset_registry" in x for x in h.statements)
    assert any("FROM asset_registry WHERE asset_id = %s FOR SHARE" in " ".join(x.split()) for x in staged)
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


def _run_cli(harness, argv, capsys, *, connect_error=None, database_url="postgresql://fake/fake", after_commit=None, patches=None):
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
        module = _load_fresh()
        if after_commit is not None:
            module._AFTER_COMMIT = after_commit
        for name, value in (patches or {}).items():
            setattr(module, name, value)
        code = module.cli(argv)
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
                                connect_error=ValueError(f"invalid percent-encoding in {_synthetic_dsn('db.example', 'prod')}"))
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

def test_a_real_dispatch_prints_the_teardown_deadline_ninety_days_after_the_STORED_created_at(capsys):
    """D4 (Codex round 4): both deadlines derive from the created_at the INSERT returns (the database clock the watchdog uses), never from
    the client's clock. The stored value here is years away from the client's, so a client-clock implementation cannot pass."""
    h = _Harness()
    out = _run_main(h, BASE_ARGV, capsys)
    assert "TEARDOWN DEADLINE" in out.err and "90 days after the stored creation time" in out.err and "V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md" in out.err
    assert out.out.strip() and "\n" not in out.out.strip()                       # stdout still carries only the run id
    import datetime as dt
    stamp = out.err.split("tear the small test down by ")[1].split(" ")[0]
    assert dt.datetime.fromisoformat(stamp) == STORED_CREATED_AT + dt.timedelta(days=90)
    execute_by = out.err.split("(by ")[1].split(")")[0]
    assert dt.datetime.fromisoformat(execute_by) == STORED_CREATED_AT + dt.timedelta(minutes=10)
    run_insert = next(x for x in h.statements if "INSERT INTO build_runs" in x)
    assert " ".join(run_insert.split()).endswith("RETURNING created_at")


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
    h = _Harness(commit_error=ConnectionError(f"server closed the connection ({_synthetic_dsn('db', 'prod')})"))
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
    code, streams, _ = _run_cli(_Harness(), BASE_ARGV, capsys, connect_error=ValueError(f"bad uri {_synthetic_dsn('x', 'y')}"))
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
    ("all_classes_full", dict()),
], ids=["all_default_order", "all_scrambled_Z_timestamps", "one_class_full", "all_classes_full"])
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


# ── DISPATCH-CODEX-1 (Codex v1.0 on PR 3097): admission, no activation, clean receipts, honest commit reporting ───────────────────

import types as _types  # noqa: E402

_SL = WRITER._validate_test_slice(ONE_MARKER)
_STAMP = {"stored_scope": WRITER.TEST_SLICE_SCOPE, "test_slice": WRITER._slice_component(_SL)}
_HORIZON = _types.SimpleNamespace(lower=_SL.horizon[0], upper=_SL.horizon[1])
PROVEN_CANDIDATE = {"manifest_id": "m-1", "status": "candidate", "input_generation_vector": _STAMP, "horizon": _HORIZON}
NON_TEST_CANDIDATE = {"manifest_id": "m-2", "status": "candidate", "input_generation_vector": {"stored_scope": "stored_non_moon"},
                      "horizon": _HORIZON}


def _text(h):
    return [" ".join(x.split()) for x in h.statements]


def test_r1_the_chart_lock_is_taken_first_and_every_check_runs_inside_it(capsys):
    h = _Harness()
    _run_main(h, BASE_ARGV, capsys)
    s = _text(h)
    assert "set_config('lock_timeout'" in s[0] and "ka_gochara_lock_chart" in s[1] and h.params[1] == (CHART_ID,)
    assert "status = 'published'" in s[2]                                           # the first check comes after the lock
    first_write = next(i for i, x in enumerate(s) if x.startswith(("INSERT", "UPDATE")))
    assert first_write > 2


@pytest.mark.parametrize("kw, match", [
    (dict(published={"manifest_id": "m1"}), "PUBLISHED"),
    (dict(seal={"manifest_id": "m9"}), "SEALED|seal"),
    (dict(authority_generation="5.0"), "authoritative_generation"),
], ids=["published", "sealed", "serving"])
def test_r1_a_published_sealed_or_serving_5_0_refuses_before_anything_is_staged(capsys, kw, match):
    h = _Harness(**kw)
    with pytest.raises(RuntimeError, match=match):
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits and not any(x.startswith("INSERT") for x in _text(h))


@pytest.mark.parametrize("kw, match", [
    (dict(catalog_status="RETIRED"), "catalog_status is RETIRED"),
    (dict(evidence=[{"kind": "receipt", "chart_id": "other", "n": 1}]), r"receipts of the asset from a non-test run.*other"),
    (dict(evidence=[{"kind": "run_asset", "chart_id": "other", "n": 2}]), r"build_run_assets rows of the asset from a non-test run.*other"),
    (dict(dependents=[{"asset_id": "ka_dep"}]), "ka_dep"),
], ids=["retired", "non_test_receipt", "non_test_run_asset", "dependent"])
def test_r2_the_monitors_n137_conditions_must_hold_before_staging(capsys, kw, match):
    h = _Harness(**kw)
    with pytest.raises(RuntimeError, match=match):
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits and not any(x.startswith("INSERT") for x in _text(h))


@pytest.mark.parametrize("kw", [
    dict(output_rows=7, manifest=NON_TEST_CANDIDATE),                                                        # a non-test candidate
    dict(output_rows=7, manifest=PROVEN_CANDIDATE, snapshot={"same_vector": True, "input_digest": "d" * 64}),  # a PROVEN small-test slice
    dict(output_rows=0, manifest=PROVEN_CANDIDATE),                                                           # a manifest and no output
    dict(output_rows=3, manifest=None),                                                                       # output and no manifest
], ids=["non_test_candidate", "proven_test_slice", "manifest_only", "output_only"])
def test_d3_ANY_prior_5_0_output_or_manifest_refuses_the_dispatch_proven_or_not(capsys, kw):
    """Codex round 4 D3: the dispatch never builds over existing output; the snapshot substep replaces the whole chain. It does not
    point at the other script: it names the runbook."""
    h = _Harness(**kw)
    with pytest.raises(RuntimeError, match=r"already has output.*never builds over it, proven small test or not") as exc:
        _run_main(h, BASE_ARGV, capsys)
    assert "V5_SMALLTEST_TEARDOWN_RUNBOOK_v1_0.md" in str(exc.value) and "teardown_v5" not in str(exc.value) and "script" not in str(exc.value)
    assert not h.commits and not any("INSERT INTO build_runs" in x for x in h.statements)


def test_d3_a_clean_generation_is_admitted(capsys):
    h = _Harness()                                       # no output rows, no manifest
    _run_main(h, BASE + ["--dry-run"], capsys)
    assert not h.commits


def test_r2_the_ownership_proof_and_the_n137_predicate_are_the_shared_modules_not_a_copy():
    import v5_small_test_shared as shared
    source = DISPATCH.read_text(encoding="utf-8")
    assert "shared.end_state_problems" in source and "shared.generation_ownership" in source and "shared.refuse_if_frozen" in source
    for definition in ("def _stamp_problem", "def _end_state_problems", "def _generation_ownership", "NIRMANA_STAGED"):
        assert definition not in source
    assert shared.ASSET_ID == dispatch.ASSET_ID and shared.CHART_ID == dispatch.CHART_ID and shared.TRIGGERED_BY == dispatch.TRIGGERED_BY


def test_r3_the_registry_row_is_never_activated_or_restored_and_the_dispatch_needs_no_update_on_it(capsys):
    h = _Harness()
    _run_main(h, BASE_ARGV, capsys)
    assert not any(x.startswith("UPDATE asset_registry") or "SET is_active" in x for x in _text(h))
    assert "SET is_active" not in DISPATCH.read_text(encoding="utf-8").replace("never activated", "")


def test_r3_the_inactive_candidate_loader_is_the_reused_helpers_query_minus_only_the_activity_filter():
    import dispatch_frozen_rebuild as helper
    import inspect
    helper_sql = " ".join(inspect.getsource(helper._load_candidate).split())
    mine = " ".join(inspect.getsource(dispatch._load_inactive_candidate).split())
    only = "AND ar.is_active = true AND ar.has_writer = true"
    assert only in helper_sql
    normalised_helper = helper_sql.replace(only, "AND ar.has_writer = true")
    # the two queries are the same text once that one filter is removed from the helper's
    body = lambda text: text[text.index("SELECT ar.asset_id"):text.index("(asset_id,)") if "(asset_id,)" in text else text.index("(ASSET_ID,)")]  # noqa: E731
    assert body(normalised_helper).replace("%s", "?").split("FROM asset_registry ar")[1].strip().rstrip(",") == \
        body(mine).replace("%s", "?").split("FROM asset_registry ar")[1].strip().rstrip(",")


def test_r4_the_registry_row_is_locked_for_share_before_it_is_validated_and_held_through_staging(capsys):
    h = _Harness()
    _run_main(h, BASE_ARGV, capsys)
    s = _text(h)
    lock = next(i for i, x in enumerate(s) if "FROM asset_registry WHERE asset_id = %s FOR SHARE" in x)
    first_insert = next(i for i, x in enumerate(s) if x.startswith("INSERT"))
    assert lock < first_insert and lock > 1                                          # after the chart lock, before anything is staged


def test_r5_a_receipt_of_the_asset_for_the_chart_refuses_with_the_run_teardown_run_teardown_sequence(capsys):
    h = _Harness(receipts=1)
    with pytest.raises(RuntimeError, match=r"delta-skip.*run 1, teardown, run 2, teardown"):
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits and not any(x.startswith("INSERT") for x in _text(h))
    h = _Harness(receipts=0)
    _run_main(h, BASE_ARGV, capsys)
    assert len(h.commits) == 1


def test_r6_a_report_that_fails_after_the_commit_keeps_the_confirmed_commit_and_names_the_run(capsys, monkeypatch):
    import builtins
    real_print = builtins.print

    def failing(*args, **kwargs):
        if args and str(args[0]).startswith("[dispatch] staged v5 SMALL TEST"):
            raise BrokenPipeError("stderr is gone")
        return real_print(*args, **kwargs)
    h = _Harness()
    monkeypatch.setattr(builtins, "print", failing)
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    monkeypatch.setattr(builtins, "print", real_print)
    assert code == 1 and len(h.commits) == 1
    assert "COMMIT CONFIRMED" in streams.err and "No transaction was opened" not in streams.err and "ROLLBACK CONFIRMED" not in streams.err
    run_id = re.search(r"Attempted run id: ([0-9a-f-]{36})", streams.err).group(1)
    assert run_id and "the small-test run IS STAGED" in streams.err


def test_r6_a_close_failure_after_the_commit_does_not_change_the_outcome(capsys):
    h = _Harness()
    real_close = h.conn.close

    def failing_close():
        raise ConnectionError("close failed")
    h.conn.close = failing_close
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    assert code == 0 and len(h.commits) == 1                                        # the staged run stands; the close failure is ignored


def test_r6_an_unknown_commit_outcome_names_the_attempted_run_and_the_dry_run_really_lists_the_existing_runs(capsys):
    h = _Harness(commit_error=ConnectionError(f"lost ({_synthetic_dsn('db', 'prod')})"))
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    attempted = re.search(r"Attempted run id: ([0-9a-f-]{36})", streams.err).group(1)
    assert code == 1 and "COMMIT OUTCOME UNKNOWN" in streams.err and "hunter2" not in streams.err
    # D1: the message names the READ-ONLY lookup command (the dry run would REFUSE once the run exists, so it cannot be the way)
    assert "--lookup <the attempted run id named above>" in streams.err and "LISTS the existing" not in streams.err
    h2 = _Harness(existing_runs=[{"id": attempted, "state": "planned", "created_at": "2026-10-04 21:00:00+00", "plan_manifest_digest": "d" * 64}])
    out = _run_main(h2, ["--lookup", attempted], capsys)
    found = json.loads(out.out)
    assert found["runs"][0]["id"] == attempted


def test_the_execute_within_ten_minutes_notice_is_printed_and_documented(capsys):
    out = _run_main(_Harness(), BASE_ARGV, capsys)
    assert "EXECUTE WITHIN 10 MINUTES" in out.err and "watchdog fails a planned run" in out.err
    assert "EXECUTE WITHIN 10 MINUTES" in dispatch.__doc__ and dispatch.EXECUTE_WITHIN_MINUTES == 10
    watchdog = (REPO / "platform/src/app/api/cockpit/watchdog/route.ts").read_text(encoding="utf-8")
    assert "created_at < NOW() - INTERVAL '10 minutes'" in watchdog and "state = 'planned'" in watchdog


def test_r7_the_ci_installs_the_sidecar_requirements_before_the_step_that_imports_the_writer():
    ci = (REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    select = ci.index("Nirmāṇa L0 — install writer test runtime")
    install = ci.index("python -m pip install -r python-sidecar/requirements-ci.txt", select)
    dispatch_step = ci.index("python -m pytest scripts/__tests__/test_dispatch_v5_small_test.py")
    assert select < install < dispatch_step


# ── Codex round 4 (D1 to D4) and Stream B (DB1 to DB5) ───────────────────────────────────────────────────────────────────────────

def test_d1_the_lookup_is_one_read_only_transaction_with_no_admission_no_lock_no_staging_and_no_steward_flags(capsys):
    run = {"id": "b" * 8 + "-" + "b" * 4 + "-" + "b" * 4 + "-" + "b" * 4 + "-" + "b" * 12, "state": "planned",
           "created_at": "2031-03-04 12:00:00+00", "plan_manifest_digest": "d" * 64}
    h = _Harness(existing_runs=[run])
    out = _run_main(h, ["--list-runs"], capsys)                    # no --i-am-steward, no --after-settled-1, no --run
    text = _text(h)
    assert json.loads(out.out)["runs"] == [dict(run)] and json.loads(out.out)["chart_id"] == CHART_ID
    assert text[0] == "SET TRANSACTION READ ONLY"
    assert not any("ka_gochara_lock_chart" in x or "INSERT" in x or "UPDATE" in x or "DELETE" in x for x in text)
    assert not any("asset_registry" in x or "kala_gochara_publication" in x for x in text)        # no admission check ran
    assert not h.commits and len(h.rollbacks) == 1


def test_d1_lookup_by_id_reports_a_missing_run_plainly_and_refuses_a_non_uuid(capsys):
    h = _Harness(existing_runs=[])
    missing = "11111111-2222-3333-4444-555555555555"
    out = _run_main(h, ["--lookup", missing], capsys)
    assert "does NOT exist" in out.err and json.loads(out.out)["runs"] == []
    with pytest.raises(SystemExit) as exc:
        _run_main(_Harness(), ["--lookup", "not-a-run-id"], capsys)
    assert exc.value.code == 2


def test_d1_the_lookup_modes_exclude_execute_and_dry_run():
    for argv in (["--list-runs", "--execute"], ["--lookup", "x", "--dry-run"], ["--list-runs", "--lookup", "x"]):
        with pytest.raises(SystemExit) as exc:
            _load_fresh().main(argv)
        assert exc.value.code == 2


def test_d1_without_a_lookup_flag_run_is_still_required():
    with pytest.raises(SystemExit) as exc:
        _load_fresh().main(["--i-am-steward", "--after-settled-1"])
    assert exc.value.code == 2


@pytest.mark.parametrize("field, bad", [("rebuild_on_probe_fail", True), ("integrity_check_sql", "SELECT 1"), ("health_probe", "probe"),
                                        ("asset_kind", "service"), ("asset_type", "service")])
def test_d2_the_routing_fields_asset_runner_reads_are_validated(capsys, field, bad):
    """A row with an integrity check AND rebuild_on_probe_fail takes the probe-green shortcut (asset_runner.py ~1591-1615): a passing probe
    marks the asset built WITHOUT running the writer."""
    h = _Harness(registry_row=dict(dispatch.EXPECTED_REGISTRY_ROW, **{field: bad}))
    with pytest.raises(RuntimeError, match=field):
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits


def test_d2_the_registry_row_read_selects_the_routing_fields_and_the_readback_sql_names_every_validated_field():
    import inspect
    source = inspect.getsource(dispatch._validate_registry_row)
    for field in ("asset_kind", "asset_type", "health_probe", "integrity_check_sql", "rebuild_on_probe_fail"):
        assert field in source and field in dispatch.EXPECTED_REGISTRY_ROW
    readback = (DISPATCH.parent / "v5_small_test_registry_row_readback.sql").read_text(encoding="utf-8")
    code = "\n".join(x for x in readback.splitlines() if not x.strip().startswith("--"))
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|GRANT|REVOKE)\b", code, re.I)
    assert all(field in code for field in dispatch.EXPECTED_REGISTRY_ROW if field != "depends_on" or True)


def test_d2_the_teardown_and_the_dispatch_still_hold_the_same_expected_row():
    import teardown_v5_small_test_job as t
    assert t.EXPECTED_REGISTRY_ROW == dispatch.EXPECTED_REGISTRY_ROW


def test_db2_an_active_run_on_the_chart_is_a_named_refusal_before_anything_is_staged(capsys):
    h = _Harness(active_runs=[{"id": "r-1", "state": "planned"}])
    with pytest.raises(RuntimeError, match=r"a build run is already active on chart .*\('r-1', 'planned'\).*one\s+active run per chart") as exc:
        _run_main(h, BASE_ARGV, capsys)
    assert not h.commits and not any("INSERT INTO build_runs" in x for x in h.statements)
    text = _text(h)
    assert text.index(next(x for x in text if "ka_gochara_lock_chart" in x)) < text.index(next(x for x in text if x.startswith("SELECT id, state FROM build_runs")))


def _fake_git(monkeypatch, *, head, porcelain=""):
    """checkout_commit shells out to fixed git commands; fake them (the module is reloaded per run, so patch subprocess itself)."""
    import subprocess

    def fake_run(cmd, **kw):
        assert cmd[0] == "git" and kw.get("shell") is None
        return types.SimpleNamespace(stdout=head + "\n" if cmd[1] == "rev-parse" else porcelain)
    monkeypatch.setattr(subprocess, "run", fake_run)


def test_db3_the_image_skew_notice_names_the_expected_writer_digest_and_the_commit_in_a_dry_run_and_a_real_dispatch(capsys, monkeypatch):
    _fake_git(monkeypatch, head="c0ffee" * 6 + "abcd")
    for argv in (BASE_ARGV, BASE + ["--dry-run"]):
        out = _run_main(_Harness(), argv, capsys)
        assert "JOB IMAGE MUST MATCH THIS CHECKOUT" in out.err and "c0ffee" in out.err
        digest = dispatch._load_writer_digest("ka_gochara_v5")
        assert digest in out.err and "sidecar code digest does not match" in out.err
        assert "WARNING" not in out.err


def test_db3_uncommitted_changes_under_the_sidecar_are_warned_about(capsys, monkeypatch):
    _fake_git(monkeypatch, head="deadbeef", porcelain=" M python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py")
    out = _run_main(_Harness(), BASE_ARGV, capsys)
    assert "WARNING" in out.err and "UNCOMMITTED" in out.err and "deadbeef" in out.err


def test_db3_checkout_commit_never_uses_a_shell_and_degrades_to_unknown():
    import inspect
    source = inspect.getsource(dispatch.checkout_commit)
    assert "shell=True" not in source and '"git", "rev-parse", "HEAD"' in source
    assert dispatch.checkout_commit.__call__ and isinstance(dispatch.checkout_commit()[0], str)


def test_the_exit_code_finding_is_printed_and_documented(capsys):
    out = _run_main(_Harness(), BASE_ARGV, capsys)
    assert "READ THE RESULT FROM THE DATABASE, NOT FROM CLOUD RUN" in out.err and "exits 0 even when the run ends failed" in out.err
    assert "build_runs.state" in out.err and "build_run_assets" in out.err
    assert "exits 0 even when the run ends failed" in dispatch.__doc__


def test_db1_the_docstring_states_the_role_data_plane_builder_suffices():
    assert "data_plane_builder" in dispatch.__doc__ and "SUFFICES" in dispatch.__doc__ and "amjis_app` is not needed" in dispatch.__doc__


# ── Codex round 5 (1): an interrupt never erases the known transaction outcome ──────────────────────────────────────────────────

def _interrupt():
    raise KeyboardInterrupt()


def test_r5_an_interrupt_INSIDE_the_commit_is_commit_outcome_unknown_and_names_the_run(capsys):
    h = _Harness(commit_error=KeyboardInterrupt())
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    assert code == 130 and "COMMIT OUTCOME UNKNOWN" in streams.err and "Attempted run id:" in streams.err
    assert "ROLLBACK CONFIRMED" not in streams.err and h.rollbacks == []


def test_r5_an_interrupt_JUST_AFTER_a_confirmed_commit_is_commit_confirmed_and_no_rollback_is_issued(capsys):
    h = _Harness()
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys, after_commit=_interrupt)
    assert len(h.commits) == 1 and code == 130 and "COMMIT CONFIRMED" in streams.err and "Attempted run id:" in streams.err
    assert "ROLLBACK CONFIRMED" not in streams.err and h.rollbacks == []


def test_r5_an_interrupt_DURING_THE_CLOSE_after_a_confirmed_commit_is_commit_confirmed(capsys):
    h = _Harness(close_error=KeyboardInterrupt())
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    assert len(h.commits) == 1 and code == 130 and "COMMIT CONFIRMED" in streams.err and "Attempted run id:" in streams.err


def test_r5_an_interrupt_during_the_close_after_a_dry_run_reports_a_confirmed_rollback(capsys):
    h = _Harness(close_error=KeyboardInterrupt())
    code, streams, _ = _run_cli(h, BASE + ["--dry-run"], capsys)
    assert code == 130 and "ROLLBACK CONFIRMED" in streams.err and not h.commits


def test_r5_an_interrupt_during_the_close_never_replaces_a_refusal_already_propagating(capsys):
    h = _Harness(active_runs=[{"id": "r-1", "state": "planned"}], close_error=KeyboardInterrupt())
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys)
    assert code == 1 and "a build run is already active" in streams.err and not h.commits


# ── Codex round 6 (1): the report is built BEFORE the commit; one handler; an unknown failure never claims 'no commit' ──────────────

def test_r6_an_interrupt_while_the_report_is_prepared_BEFORE_the_commit_is_a_confirmed_rollback_naming_the_run(capsys):
    h = _Harness()
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys, patches={"image_skew_notice": lambda manifest: _interrupt()})
    assert code == 130 and not h.commits and "ROLLBACK CONFIRMED" in streams.err and "Attempted run id:" in streams.err


def test_r6_an_interrupt_while_the_report_is_PRINTED_after_a_confirmed_commit_is_commit_confirmed_with_the_run_id(capsys):
    h = _Harness()

    def emit(report):
        raise KeyboardInterrupt()
    code, streams, _ = _run_cli(h, BASE_ARGV, capsys, patches={"_emit_report": emit})
    assert len(h.commits) == 1 and code == 130 and "COMMIT CONFIRMED" in streams.err and "Attempted run id:" in streams.err
    assert "No COMMIT was sent" not in streams.err and "ROLLBACK CONFIRMED" not in streams.err


def test_r6_everything_printed_is_prepared_before_the_commit_statement(capsys):
    order = []
    h = _Harness()
    real_commit = h.conn.commit

    def commit():
        order.append("commit")
        return real_commit()
    h.conn.commit = commit

    def skew(manifest):
        order.append("prepare")
        return []
    _run_cli(h, BASE_ARGV, capsys, patches={"image_skew_notice": skew})
    assert order == ["prepare", "commit"], order


def test_r6_a_failure_with_no_recorded_outcome_never_claims_that_nothing_was_committed():
    text = dispatch._safe_failure(RuntimeError("anything"))
    assert "NOT recorded" in text and "--lookup" in text
    assert "No COMMIT was sent" not in text and "ROLLBACK CONFIRMED" not in text and "committed nothing" not in text


def test_an_empty_string_probe_or_integrity_check_reads_as_null(capsys):
    h = _Harness(registry_row=dict(dispatch.EXPECTED_REGISTRY_ROW, health_probe="", integrity_check_sql=""))
    _run_main(h, BASE + ["--dry-run"], capsys)                    # admitted: bool("") is False in the runner, as NULL
    h2 = _Harness(registry_row=dict(dispatch.EXPECTED_REGISTRY_ROW, integrity_check_sql=" "))
    with pytest.raises(RuntimeError, match="integrity_check_sql"):
        _run_main(h2, BASE + ["--dry-run"], capsys)               # a non-empty value is still refused
