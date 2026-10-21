"""MB-3: independent stored-column golden, never a 4.1 scoring receipt."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import measuring_capture as mc


def record(**changes):
    return dict(record_id="6e147431-07ad-8c37-8fbf-c2ee632b4882", chart_id="chart", generation="5.0",
                event_class="marriage", affected_person="native", frame_kind="lagna", frame_arg=None,
                agent="saturn", relation="residence", object_id="object", object_role="bhava",
                contact_id="contact", path_id="P3", rule_version="1.0.0", prerequisites=[["p", "1.0.0"]],
                source_text=None, period_anchor_lord=None, period_anchor_level=None,
                admission_state="admitted", operator_role="scored",
                temporal_support_intervals=[["2025-01-10T00:00:00+00:00", "2025-02-20T00:00:00+00:00"]],
                **changes)


def bundle():
    return mc.make_bundle(
        binding={"chart_id": "chart", "generation": "5.0", "run_id": "run", "manifest_id": "manifest",
                 "source_commit": "a" * 40},
        contacts=[{"contact_id": "contact", "body": "saturn", "relation_kind": "residence",
                   "canonical_target": "span:7", "t_in": "2025-01-10T00:00:00+00:00",
                   "t_out": "2025-02-20T00:00:00+00:00", "t_exact": None, "delta_lambda": 0.0001}],
        records=[record()], windows=[], horizon_basis={"schema": "example/1"},
        stretch_sink=[], informational={"input_vector": {"stored_scope": "test_slice"}})


def test_gkey_uses_stored_columns_and_omits_only_chart_and_generation():
    expected = ('{"affected_person":"native","agent":"saturn","contact_id":"contact",'
                '"event_class":"marriage","frame":"lagna","object_id":"object",'
                '"object_role":"bhava","path_id":"P3","prerequisites":[["p","1.0.0"]],'
                '"relation":"residence","rule_version":"1.0.0","source_text":null}')
    got = mc.golden_record(record())
    assert got["gkey"] == expected
    assert got["gkey_sha256"] == hashlib.sha256(expected.encode()).hexdigest()
    other = record()
    other.update(chart_id="other", generation="5.1", record_id="other-id")
    assert mc.golden_record(other)["gkey_sha256"] == got["gkey_sha256"]
    other.update(period_anchor_lord="saturn", period_anchor_level="MD", frame_arg="moon")
    assert json.loads(mc.golden_record(other)["gkey"]).get("period_anchor_level") == "MD"
    assert json.loads(mc.golden_record(other)["gkey"]).get("frame") == "lagna:moon"


@pytest.mark.parametrize("field,value", [
    ("temporal_support_intervals", [["2025-01-10T00:00:01+00:00", "2025-02-20T00:00:00+00:00"]]),
    ("operator_role", "testimony"), ("admission_state", "unqualified"),
])
def test_class_path_digest_detects_support_role_and_admission_changes(field, value):
    before = bundle()
    after = bundle()
    changed = record()
    changed[field] = value
    after = mc.make_bundle(binding=after["digests.json"]["binding"], contacts=[], records=[changed], windows=[],
                           horizon_basis={}, stretch_sink=[], informational={})
    assert before["digests.json"]["records"] != after["digests.json"]["records"]


def test_export_is_order_independent_timezone_canonical_and_does_not_drop_duplicates():
    first = record()
    second = record()
    second["path_id"] = "P2"
    kwargs = dict(binding=bundle()["digests.json"]["binding"], contacts=[], windows=[],
                  horizon_basis={}, stretch_sink=[], informational={})
    a = mc.make_bundle(records=[first, second], **kwargs)
    b = mc.make_bundle(records=[second, first], **kwargs)
    assert a == b
    c = mc.make_bundle(records=[first, first], **kwargs)
    assert len(c["records.jsonl"]) == 2
    assert c["digests.json"]["records"] != mc.make_bundle(records=[first], **kwargs)["digests.json"]["records"]
    assert mc.canonical(datetime(2025, 1, 1, tzinfo=timezone.utc)) == '"2025-01-01T00:00:00+00:00"'
    ist = timezone(timedelta(hours=5, minutes=30))
    assert mc.canonical(datetime(2025, 1, 1, 5, 30, tzinfo=ist)) == '"2025-01-01T00:00:00+00:00"'


def test_export_roundtrip_detects_missing_extra_tampered_and_conflicting_manifest_entries(tmp_path):
    dest = tmp_path / "golden"
    receipt = mc.write_bundle(dest, bundle())
    assert len(receipt["manifest_sha256"]) == 64
    assert mc.verify_bundle(dest) == receipt
    with pytest.raises(FileExistsError):
        mc.write_bundle(dest, bundle())
    original = (dest / "records.jsonl").read_bytes()
    (dest / "records.jsonl").write_bytes(original + b"\n")
    with pytest.raises(mc.CaptureRefused, match="golden_digest_mismatch"):
        mc.verify_bundle(dest)
    (dest / "records.jsonl").write_bytes(original)
    (dest / "extra.json").write_text("{}")
    with pytest.raises(mc.CaptureRefused, match="golden_file_set"):
        mc.verify_bundle(dest)
    (dest / "extra.json").unlink()
    manifest = dest / "MANIFEST.sha256"
    manifest.write_text(manifest.read_text() + manifest.read_text().splitlines()[0] + "\n")
    with pytest.raises(mc.CaptureRefused, match="golden_manifest_invalid"):
        mc.verify_bundle(dest)


def test_export_rejects_naive_nonfinite_and_incomplete_stored_values():
    with pytest.raises(mc.CaptureRefused, match="naive_datetime"):
        mc.canonical(datetime(2025, 1, 1))
    with pytest.raises((ValueError, mc.CaptureRefused)):
        mc.canonical(float("nan"))
    bad = record()
    del bad["source_text"]
    with pytest.raises(mc.CaptureRefused, match="stored_record_missing"):
        mc.golden_record(bad)


def test_export_preserves_range_bounds_and_rejects_empty_infinite_or_closed_support():
    from psycopg.types.range import Range
    lo, hi = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 1, 2, tzinfo=timezone.utc)
    assert mc.canonical(Range(lo, hi, "[)")) == '["2025-01-01T00:00:00+00:00","2025-01-02T00:00:00+00:00"]'
    for interval in (Range(lo, hi, "[]"), Range(None, hi), Range(empty=True)):
        with pytest.raises(mc.CaptureRefused, match="support_interval_unbounded_or_not_half_open"):
            mc.canonical(interval)


def test_export_rejects_symlinks_in_the_golden(tmp_path):
    path = tmp_path / "golden"
    mc.write_bundle(path, bundle())
    stored = path / "contacts.jsonl"
    target = tmp_path / "contacts.jsonl"
    stored.rename(target)
    stored.symlink_to(target)
    with pytest.raises(mc.CaptureRefused, match="golden_file_set"):
        mc.verify_bundle(path)


def test_generation_free_keys_do_not_erase_payload_differences():
    row = record()
    row["object_role"] = "lord"
    assert mc.golden_record(row)["gkey_sha256"] != mc.golden_record(record())["gkey_sha256"]
    row = record()
    row["prerequisites"] = [["other", "1.0.0"]]
    assert mc.golden_record(row)["gkey_sha256"] != mc.golden_record(record())["gkey_sha256"]


def manifest():
    from services.gochara_kernel import measuring_report as mr
    horizon = ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]
    return {"status": "candidate", "lo": horizon[0], "hi": horizon[1], "input_generation_vector": {
        "stored_scope": "test_slice", "test_slice": {"schema": mr.MARKER_SCHEMA, "marker_digest": "d" * 64,
        "run": "all_classes_full", "classes": sorted(mr.SCORED_CLASSES), "horizon": horizon},
        "horizon_basis": {"schema": "horizon_basis/1", "basis": "ruled_horizon", "rule": "ruled_scope+birth_centenary", "horizon": horizon}}}


@pytest.mark.parametrize("field,value,refusal", [
    ("schema", "another/1", "marker_incomplete"), ("marker_digest", "invalid", "marker_incomplete"),
    ("classes", ["marriage"], "class_census_mismatch"),
    ("horizon", ["1998-01-02", "2084-02-05"], "marker_horizon_mismatch"),
])
def test_candidate_marker_validation_checks_schema_digest_census_and_actual_horizon(field, value, refusal):
    m = manifest()
    mc.validate_candidate_manifest(m)
    m["input_generation_vector"]["test_slice"][field] = value
    with pytest.raises(mc.CaptureRefused, match=rf"^{refusal}(?::|$)"):
        mc.validate_candidate_manifest(m)


@pytest.mark.parametrize("section,field,value,refusal", [
    ("manifest", "status", "published", "measuring_build_not_candidate"),
    ("manifest", "hi", "2085-01-01", "horizon_mismatch"),
    ("vector", "stored_scope", "stored_non_moon", "measuring_scope_not_all_classes_full"),
    ("vector", "horizon_basis", None, "horizon_basis_missing"),
    ("marker", "run", "one_class_full", "measuring_scope_not_all_classes_full"),
])
def test_manifest_validation_refuses_wrong_status_scope_horizon_and_missing_basis(section, field, value, refusal):
    m = manifest()
    selected = {"manifest": m, "vector": m["input_generation_vector"], "marker": m["input_generation_vector"]["test_slice"]}[section]
    selected[field] = value
    if field == "hi":
        m["input_generation_vector"]["test_slice"]["horizon"][1] = value
    with pytest.raises(mc.CaptureRefused, match=rf"^{refusal}(?::|$)"):
        mc.validate_candidate_manifest(m)


@pytest.mark.parametrize("readonly,isolation", [("off", "repeatable read"), ("on", "read committed")])
def test_reader_refuses_unsafe_transaction_before_any_candidate_query(readonly, isolation):
    class Settings:
        class info:
            transaction_status = 2  # psycopg.pq.TransactionStatus.INTRANS

        def execute(self, sql, params=None):
            assert sql in ("SHOW transaction_read_only", "SHOW transaction_isolation"), "candidate query before safe snapshot"
            class Row:
                def fetchone(self):
                    return (readonly if sql == "SHOW transaction_read_only" else isolation,)
            return Row()
    with pytest.raises(mc.CaptureRefused, match="capture_requires_read_only_snapshot"):
        _read(Settings(), "chart")


def test_reader_requires_an_active_transaction_even_when_session_defaults_are_read_only_repeatable():
    class SessionDefaults:
        class info:
            transaction_status = 0  # IDLE: each autocommit SELECT would see a new snapshot

        def execute(self, sql, params=None):
            assert sql in ("SHOW transaction_read_only", "SHOW transaction_isolation"), "query without active snapshot"
            class Row:
                def fetchone(self):
                    return ("on" if sql == "SHOW transaction_read_only" else "repeatable read",)
            return Row()

    with pytest.raises(mc.CaptureRefused, match="capture_requires_read_only_snapshot"):
        _read(SessionDefaults(), "chart")


@pytest.fixture(scope="module")
def candidate_db(isolated_kala_db_dsn):
    """Real migrations, real pinned Swiss writer; no production/L1 computation.

    AM5 supplies its existing literal L1 fixtures. The bounded ordinary output
    is subsequently stamped as controlled measuring input for exporter tests;
    that seed is not a successful full measuring run or an acceptance fixture.
    """
    import os
    from pathlib import Path
    import psycopg
    from pipeline.orchestrator.writers import ContextSpec, SubStep
    from pipeline.orchestrator.writers import ka_gochara_v5 as w
    from tests.l3.gochara.test_a53_inventory import CHART_ID, _populate_am5_database
    from tests.l3.gochara.test_a55_replace_chain import SHORT
    from services.gochara_kernel import measuring_report as mr
    from services.gochara_kernel import contact_reconstruct

    conn = psycopg.connect(isolated_kala_db_dsn, autocommit=True)
    # The sibling gochara conftest's C52 cache isolation does not automatically
    # apply in kala_db. Never reuse another module's synthetic position memo.
    contact_reconstruct._CACHE.clear()
    try:
        _populate_am5_database(conn)
        # AM5 predates the legacy authority fixture. Apply its real migrations
        # too; 1236 must keep refusing governed generation authority throughout.
        platform = Path(__file__).resolve().parents[4]
        conn.execute("CREATE TABLE public.kala_gochara_windows (chart_id uuid)")
        conn.execute((platform / "supabase/migrations/527_kala_gochara_generation_authority.sql").read_text())
        conn.execute((platform / "migrations/1236_gochara_authority_refuses_governed_generation.sql").read_text())
        ctx = ContextSpec(asset_id=w.ASSET_ID, build_id="j3-local-rehearsal", db_conn=conn, dry_run=False,
                          config={"chart_id": CHART_ID, "gochara_v5_final_rules": False, "horizon": SHORT, "ephe_path": os.environ["SE_EPHE_PATH"]})
        writer = w.GocharaV5Writer()
        keys = [w.RULES_SUBSTEP, w.CONVENTION_SUBSTEP] + [f"body:{b}" for b in w.SUBSTRATE_BODIES]
        keys += [w.MANIFEST_SUBSTEP, w.SNAPSHOT_SUBSTEP, "inventory:marriage", "coverage:marriage",
                 "record:marriage:P2", "record:marriage:P3", "window:marriage:P2", "window:marriage:P3"]
        for key in keys:
            with conn.transaction():
                writer.run_substep(ctx, SubStep(key=key, label=key))
        vector = conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication").fetchone()[0]
        full = ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]
        vector.update(stored_scope="test_slice", test_slice={"schema": mr.MARKER_SCHEMA, "marker_digest": "d" * 64,
                      "run": "all_classes_full", "classes": sorted(mr.SCORED_CLASSES), "horizon": full},
                      horizon_basis={"schema": "horizon_basis/1", "basis": "ruled_horizon", "rule": "ruled_scope+birth_centenary", "horizon": full})
        with conn.transaction():
            conn.execute("SET LOCAL session_replication_role = replica")
            conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = %s::jsonb,"
                         " horizon = tstzrange(%s::timestamptz, %s::timestamptz, '[)')",
                         (json.dumps(vector), *full))
        yield conn, CHART_ID
    finally:
        conn.close()
        contact_reconstruct._CACHE.clear()


def _read(conn, chart_id):
    return mc.read_candidate(conn, chart_id=chart_id, generation="5.0", run_id="local-rehearsal",
                             source_commit="a" * 40, stretch_sink=[])


def test_read_only_real_migration_capture_twice_and_real_stored_key_equivalence(candidate_db, tmp_path):
    conn, chart = candidate_db
    from services.gochara_kernel.evaluator import record_uuid
    with pytest.raises(mc.CaptureRefused, match="capture_requires_read_only_snapshot"):
        _read(conn, chart)
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        first = _read(conn, chart)
        second = _read(conn, chart)
        assert conn.execute("SHOW transaction_read_only").fetchone()[0] == "on"
    assert first == second
    assert first["records.jsonl"] and first["contacts.jsonl"]
    for row in first["records.jsonl"]:
        key = json.loads(row["gkey"])
        assert str(record_uuid(dict(key, chart_id=chart, generation="5.0"))) == row["record_id"]
        assert record_uuid(dict(key, chart_id=chart, generation="5.1")) != record_uuid(dict(key, chart_id=chart, generation="5.0"))
    # T3.1 requires TWO genuinely stored rows, not just a hypothetical second
    # id. Seed an otherwise identical candidate generation using the actual
    # column types. Replication mode is local fixture setup, never capture.
    tables = ("kala_gochara_publication", "kala_gochara_coverage", "ka_gochara_contact")
    try:
        with conn.transaction():
            conn.execute("SET LOCAL session_replication_role = replica")
            for table in tables:
                update = {"generation": "5.1"}
                if table == "kala_gochara_publication":
                    update["manifest_id"] = "00000000-0000-4000-8000-000000000051"
                conn.execute(f"INSERT INTO public.{table} SELECT (jsonb_populate_record(NULL::public.{table},"
                             f" to_jsonb(original) || %s::jsonb)).* FROM public.{table} original"
                             " WHERE chart_id = %s AND generation = '5.0'", (json.dumps(update), chart))
            for row in first["records.jsonl"]:
                other_id = str(record_uuid(dict(json.loads(row["gkey"]), chart_id=chart, generation="5.1")))
                update = json.dumps({"generation": "5.1", "record_id": other_id})
                for table in ("ka_gochara_relationship_record", "ka_gochara_record_prerequisite"):
                    conn.execute(f"INSERT INTO public.{table} SELECT (jsonb_populate_record(NULL::public.{table},"
                                 f" to_jsonb(original) || %s::jsonb)).* FROM public.{table} original"
                                 " WHERE chart_id = %s AND generation = '5.0' AND record_id = %s",
                                 (update, chart, row["record_id"]))
        with conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            assert _read(conn, chart) == first  # second generation cannot leak into any first-generation file
            other = mc.read_candidate(conn, chart_id=chart, generation="5.1", run_id="local-rehearsal",
                                      source_commit="a" * 40, stretch_sink=[])
        assert other["digests.json"]["records"] == first["digests.json"]["records"]
        assert {r["record_id"] for r in first["records.jsonl"]}.isdisjoint(r["record_id"] for r in other["records.jsonl"])
        assert other["windows.jsonl"] == []  # the second candidate has no windows
        assert first["windows.jsonl"]  # positive control for generation-scoped window reads
    finally:
        with conn.transaction():
            conn.execute("SET LOCAL session_replication_role = replica")
            for table in ("ka_gochara_record_prerequisite", "ka_gochara_relationship_record", "ka_gochara_contact",
                          "kala_gochara_coverage", "kala_gochara_publication"):
                conn.execute(f"DELETE FROM public.{table} WHERE chart_id = %s AND generation = '5.1'", (chart,))
    mc.write_bundle(tmp_path / "one", first)
    mc.write_bundle(tmp_path / "two", second)
    for name in mc.FILES | {"MANIFEST.sha256"}:
        assert (tmp_path / "one" / name).read_bytes() == (tmp_path / "two" / name).read_bytes()
    assert mc.verify_bundle(tmp_path / "one")["acceptance"] is None


@pytest.mark.parametrize("mutation,refusal", [
    ({"stored_scope": "stored_non_moon"}, "measuring_scope_not_all_classes_full"),
    ({"test_slice": {"run": "one_class_full"}}, "measuring_scope_not_all_classes_full"),
    ({"horizon_basis": None}, "horizon_basis_missing"),
    ({"test_slice": {"run": "all_classes_full"}}, "marker_incomplete"),
])
def test_read_candidate_refuses_unstamped_or_incomplete_manifest(candidate_db, mutation, refusal):
    conn, chart = candidate_db
    original = conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication").fetchone()[0]
    try:
        with conn.transaction():
            conn.execute("SET LOCAL session_replication_role = replica")
            conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = %s::jsonb",
                         (json.dumps(dict(original, **mutation)),))
        with conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            with pytest.raises(mc.CaptureRefused, match=rf"^{refusal}(?::|$)"):
                _read(conn, chart)
    finally:
        with conn.transaction():
            conn.execute("SET LOCAL session_replication_role = replica")
            conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = %s::jsonb", (json.dumps(original),))


# ── Route A: the same capture through the existing read-only readback_sql kind ──────────────────────
# SR-J3-READ-KINDS: one SELECT/WITH file (one statement = one snapshot) + an offline reassembler.

READBACK_SQL = (Path(os.environ.get("MB3_CAPTURE_READ_SQL") or
                     Path(__file__).resolve().parents[5] / "00_ARCHITECTURE/briefs/kalayantra/fleet/sql/mb3-capture-read.sql"))


def _readback_tsv(conn, sql):
    """What readback_sql.sh does: executor file rules, read-only, prepared single statement, TSV with header."""
    assert "\\" not in sql and re.match(r"\s*(SELECT|WITH)\b", sql, re.I)
    out = io.StringIO()
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        cur = conn.cursor()
        cur.execute(sql, None, prepare=True)
        writer = csv.writer(out, delimiter="\t", lineterminator="\n")
        writer.writerow([c.name for c in cur.description])
        for row in cur:
            writer.writerow(row)
    return out.getvalue()


def _reassemble(tsv):
    from services.gochara_kernel.measuring_capture_reassemble import reassemble_candidate
    return reassemble_candidate(tsv, run_id="local-rehearsal", source_commit="a" * 40, stretch_sink=[])


def test_readback_route_reassembles_exactly_what_read_candidate_returns(candidate_db, tmp_path):
    """Claim 1: readback_sql output of the one file + reassembler == read_candidate, byte for byte once written."""
    conn, chart = candidate_db
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        live = _read(conn, chart)
    tsv = _readback_tsv(conn, READBACK_SQL.read_text())
    assert _reassemble(tsv) == live
    assert live["records.jsonl"] and live["contacts.jsonl"] and live["windows.jsonl"]
    mc.write_bundle(tmp_path / "live", live)
    mc.write_bundle(tmp_path / "readback", _reassemble(tsv))
    for name in mc.FILES | {"MANIFEST.sha256"}:
        assert (tmp_path / "live" / name).read_bytes() == (tmp_path / "readback" / name).read_bytes()
    # negative control: the oracle can read false (a column mix-up in the SQL is visible)
    wrong = READBACK_SQL.read_text().replace("'t_exact', to_char(c.t_exact", "'t_exact', to_char(c.t_in")
    assert wrong != READBACK_SQL.read_text()
    assert _reassemble(_readback_tsv(conn, wrong)) != live


def _synthetic_tsv(mutate=None):
    m = manifest()
    parts = {
        "binding": [{"chart_id": "chart", "generation": "5.0"}],
        "manifest": [dict(m, manifest_id="manifest")],
        "sealed": [{"n": 0}], "published": [{"n": 0}],
        "contact": [{"contact_id": "c", "body": "saturn", "relation_kind": "residence", "canonical_target": "span:7",
                     "t_in": "2025-01-10T00:00:00.000000+00:00", "t_out": None, "t_exact": None, "delta_lambda": "0.0001"}],
        "record": [dict(record(), temporal_support_intervals=[
            {"lo": "2025-01-10T00:00:00.000000+00:00", "hi": "2025-02-20T00:00:00.000000+00:00", "bounds": "[)", "empty": False}])],
        "window": [],
    }
    for row in parts["record"]:
        for k in ("chart_id", "generation"):
            row.pop(k)
    parts["manifest"][0].pop("input_generation_vector")
    parts["manifest"][0]["input_generation_vector"] = m["input_generation_vector"]
    if mutate:
        mutate(parts)
    out = io.StringIO()
    writer = csv.writer(out, delimiter="\t", lineterminator="\n")
    writer.writerow(["section", "row_json"])
    for section, rows in parts.items():
        for row in rows:
            writer.writerow([section, json.dumps(row)])
    return out.getvalue()


def test_readback_route_synthetic_baseline_assembles():
    assert _reassemble(_synthetic_tsv())["records.jsonl"]


@pytest.mark.parametrize("section,refusal", [("sealed", "measuring_build_sealed"), ("published", "measuring_build_published")])
def test_readback_route_refuses_sealed_or_published_generation(section, refusal):
    """Claim 2: the seal/authority probes still refuse (read_candidate semantics, shared assemble_candidate)."""
    with pytest.raises(mc.CaptureRefused, match=rf"^{refusal}$"):
        _reassemble(_synthetic_tsv(lambda parts: parts.__setitem__(section, [{"n": 1}])))


@pytest.mark.parametrize("section", ["sealed", "published", "binding"])
def test_readback_route_missing_section_is_a_refusal_not_a_zero(section):
    """Claim 3 (N.8 / N.7.6): a probe that never ran must not read as 'not sealed'."""
    with pytest.raises(mc.CaptureRefused, match="readback_section_missing_or_repeated"):
        _reassemble(_synthetic_tsv(lambda parts: parts.__setitem__(section, [])))


def test_readback_route_refuses_closed_support_interval():
    """Claim 4: the half-open support rule survives the readback form (as test_export_preserves_range_bounds)."""
    def close(parts):
        parts["record"][0]["temporal_support_intervals"][0]["bounds"] = "[]"
    with pytest.raises(mc.CaptureRefused, match="support_interval_unbounded_or_not_half_open"):
        _reassemble(_synthetic_tsv(close))
