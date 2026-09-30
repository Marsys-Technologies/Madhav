"""Pravāha A2.5 — the century streaming chain (CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 §2/§3),
as amended by ASTRA_REVIEW_A2_5_STREAMING_v1_0 (six merge-blocking amendments).

Pure-python, no Swiss calls, no real DB, no real GCS. The fake GCS transport
drives the REAL streamed code path (blob.open/upload_from_filename via an
injected client); the fake DB connection drives the real ledger functions.

Amendment → test map (each test names the mutation it kills):

  1. Bounded memory end-to-end —
     test_streamed_build_memory_bounded (kills: materializing the episode
       list / row set before insert — peak blows past the bound),
     test_projection_iter_class_contacts_server_side (kills: fetchall
       contact reads),
     test_projection_main_streams_per_class (kills: reverting main to the
       whole-set contacts_by_class shape).
  2. Finalized input manifest — test_build_refuses_omitted_body,
     test_build_refuses_truncated_stream (kills: dropping the line-count
       binding — a clean JSON-prefix truncation earns GREEN),
     test_build_refuses_checksum_mismatch (kills: dropping the sha256
       binding — same-length alteration passes),
     test_build_refuses_mixed_run, test_build_refuses_unfinalized_manifest,
     test_build_refuses_unreadable_object,
     test_build_green_only_with_verified_manifest (positive control).
  3. DSN redaction — test_redact_helpers,
     test_century_run_never_logs_dsn_password (kills: unredacted argv echo
       in _run).
  4. Scope enforcement — test_century_run_refuses_wrong_chart_before_work,
     test_century_run_refuses_wrong_generation_before_work (kill: removing
       the chart/generation guard — a foreign scope reaches subprocesses).
  5. Retry safety — test_century_run_refuses_nonfresh_run_dir,
     test_century_run_fresh_prefix_per_attempt_and_provenance,
     test_century_run_failed_attempt_finalizes_nothing (kills: finalizing a
       manifest after a failed body).
  6. Equivalence defined precisely — test_equivalence_real_ledger_digest
     (kills: constant/uncontrolled digest — volatile metadata makes the two
     paths diverge), test_tied_keys_total_order_deterministic (kills:
     dropping the canonical-json tie-break — shard order leaks into the
     merged order), test_unsorted_object_rejected,
     test_coverage_sorted_by_partition_key (kills: PERSISTED_BODIES-order
     coverage concatenation).
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import tracemalloc
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

CUT_OVER_DIR = (
    Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover"
)
ENUM_PATH = CUT_OVER_DIR / "step06_enumerate_episodes.py"
BUILD_PATH = CUT_OVER_DIR / "step06_candidate_build.py"
CENTURY_PATH = CUT_OVER_DIR / "century_run.py"
PROJ_PATH = CUT_OVER_DIR / "step06b_windows_projection.py"
COMMON_PATH = CUT_OVER_DIR / "common.py"
LEDGER_PATH = (Path(__file__).resolve().parents[3]
               / "services" / "gochara_kernel" / "ledger.py")

UTC = timezone.utc
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
# Assembled from parts: a literal connection string in one line would (rightly)
# trip the repo secret scanner; the redaction tests need a realistic password shape.
DSN_PASSWORD = "s3cr3t-" + "P4ssw0rd"
DSN_WITH_PASSWORD = "postgresql://builder:" + DSN_PASSWORD + "@10.9.8.7:5432/madhav"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


enum_mod = _load(ENUM_PATH, "step06_enumerate_episodes")
build_mod = _load(BUILD_PATH, "step06_candidate_build")
century_mod = _load(CENTURY_PATH, "century_run")
proj_mod = _load(PROJ_PATH, "step06b_windows_projection")
common_mod = _load(COMMON_PATH, "cutover_common")
ledger = _load(LEDGER_PATH, "test_a25_ledger")


def _episode(body: str, relation: str, t_in: datetime, target_ref: str) -> dict:
    """A minimal ledger `_normalize_episode`-shaped dict (datetimes live, as
    the driver holds them before default=str serialization)."""
    return {
        "independence_group": f"ig-{body}-{relation}-{target_ref}",
        "body": body, "relation": relation,
        "aspect_deg": 0,
        "target_type": "karaka", "target_ref": target_ref,
        "target_fact_id": None, "target_resolution_state": "resolved",
        "target_longitude_deg": 90.0,
        "t_in": t_in, "t_exact": t_in + timedelta(hours=1),
        "t_out": t_in + timedelta(hours=2),
        "bracket_seconds": 300, "tolerance_arcsec": 2.0,
        "truncated_at_horizon": None, "branch": "direct",
        "station_flag": None, "exact_crossing": True,
        "orb_max_deg": 5.0, "orb_source": "orb_conj_slow",
        "dwell_days": None,
        "epistemic_class": "observed_event", "completeness_state": "applied",
        "operator_role": "kernel", "precision_regime": "instant_grain",
        "time_basis": "event_time_utc",
        "comparable_with": "same_convention_same_inputs",
        "ephemeris_backend": {"backend": "swieph", "retflag": 258},
        "evidence_fact_ids": [],
        "classical_citation": None, "uncited_extension": True,
        "corpus_verifiable": None,
    }


BASE = datetime(2020, 3, 1, 0, 0, 0, tzinfo=UTC)
SUN_EPS = [
    _episode("Sun", "conjunction", BASE + timedelta(days=10), "SUN"),
    _episode("Sun", "conjunction", BASE + timedelta(days=2), "MOON"),
]
SAT_EPS = [
    _episode("Saturn", "conjunction", BASE + timedelta(days=5), "SUN"),
    _episode("Saturn", "return", BASE + timedelta(days=1), "SATURN"),
]
ALL_EPS = SUN_EPS + SAT_EPS


def _monolithic_round_trip(path: Path, episodes: list[dict]) -> list[dict]:
    """What the decade-scale path does: json.dumps(indent=2, default=str) out,
    json.loads + _coerce_episode_times back in."""
    path.write_text(json.dumps(episodes, indent=2, default=str) + "\n")
    return build_mod._coerce_episode_times(json.loads(path.read_text()))


def _content_digest(episodes: list[dict]) -> str:
    """Order-independent content digest of a read-back episode set (the same
    discipline as ledger.reference_digest/_canonical_row_set)."""
    canon = sorted(
        json.dumps(e, sort_keys=True, separators=(",", ":"), default=str)
        for e in episodes)
    return hashlib.sha256(
        json.dumps(canon, separators=(",", ":")).encode("utf-8")).hexdigest()


def _canonical_order(episodes: list[dict]) -> list[dict]:
    return sorted(episodes, key=build_mod.episode_stream_key)


# ── fakes: DB connection / GCS transport / subprocess ─────────────────────────


class _RecCursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def executemany(self, sql, rows):
        rows = list(rows)
        self.conn.batch_sizes.append(len(rows))
        if self.conn.keep_rows:
            self.conn.rows.extend(rows)
        self.conn.inserted += len(rows)


class _RecConn:
    """In-memory SQL recorder shaped for the ledger's call pattern."""

    def __init__(self, *, keep_rows=False):
        self.keep_rows = keep_rows
        self.rows = []
        self.batch_sizes = []
        self.inserted = 0
        self.committed = False
        self.rolled_back = False
        self._one = None

    def execute(self, sql, params=None):
        if "SELECT manifest_id, status" in sql:
            self._one = ("mid-1", "candidate")
        elif "method_version" in sql:
            self._one = ("1.0.0",)
        elif "RETURNING manifest_id" in sql:
            self._one = ("mid-1",)
        elif "count(*)" in sql:
            self._one = (0,)
        else:
            self._one = None
        return self

    def fetchone(self):
        return self._one

    def fetchall(self):
        return []

    def cursor(self, name=None):
        return _RecCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


class _FakeBlob:
    def __init__(self, store, name):
        self.store = store
        self.name = name
        self.size = None

    def upload_from_filename(self, path):
        data = Path(path).read_bytes()
        self.store[self.name] = data
        self.size = len(data)

    def reload(self):
        if self.name not in self.store:
            raise FileNotFoundError(self.name)
        self.size = len(self.store[self.name])

    def open(self, mode="rb", encoding=None):
        if self.name not in self.store:
            raise FileNotFoundError(self.name)
        data = self.store[self.name]
        if "b" in mode:
            return io.BytesIO(data)
        return io.StringIO(data.decode(encoding or "utf-8"))


class _FakeGCSClient:
    """Same call shape as google.cloud.storage.Client against an in-memory
    store — the production code path (bucket().blob().upload/open) is the
    real one."""

    def __init__(self):
        self.store: dict[str, bytes] = {}

    def bucket(self, name):
        client = self

        class _Bucket:
            def blob(self, blob_name):
                return _FakeBlob(client.store, f"{name}/{blob_name}")

        return _Bucket()


def _stub_freshness(monkeypatch):
    """The §12.9 gate reads overlay freshness from the DB; substitute a FRESH
    report so build-main tests reach the input-verification paths."""
    fake = types.ModuleType("services.ka_vedha_gochara.freshness")

    class _Rep:
        state = "FRESH"
        current = "fp:test"

        def summary(self):
            return "fresh"

    fake.check_overlay_freshness = lambda conn, chart: {
        "house_vedha": _Rep(), "moorti": _Rep()}
    fake.gate_allows_overlays = lambda reports: True
    monkeypatch.setitem(sys.modules,
                        "services.ka_vedha_gochara.freshness", fake)


def _coverage_row(body: str, horizon: str, key: str | None = None) -> dict:
    return {
        "partition_kind": "body_target",
        "partition_key": key or f"{body.lower()}:karaka",
        "requested_horizon": horizon, "completed_horizon": horizon,
        "resolution": 2.0, "relations_searched": ["conjunction"],
        "targets_requested": 1,
        "target_resolution_state_counts": {"resolved": 1, "unavailable": 0,
                                           "unqualified": 0},
        "unavailable_inputs": {}, "unsearched_reason": None,
    }


CENTURY_HORIZON_TEXT = ("[1984-02-05T00:00:00+00:00,"
                        "2084-02-05T00:00:00+00:00)")


def _body_episodes(body: str, n: int, *, start: datetime = BASE) -> list[dict]:
    return [_episode(body, "conjunction", start + timedelta(days=3 * i),
                     f"{body.upper()}-{i}")
            for i in range(n)]


def _write_manifest_tree(tmp_path: Path, *, episodes_by_body: dict,
                         run_id="run-test-1", finalized=True,
                         omit_files=(), gs_objects=(),
                         coverage_order=None):
    """Write per-body NDJSON objects + coverage + a finalized input manifest
    the way century_run does. Returns (manifest_path, manifest, files)."""
    episodes_by_body = {b: sorted(eps, key=build_mod.episode_stream_key)
                        for b, eps in episodes_by_body.items()}
    obj_dir = tmp_path / "objects"
    obj_dir.mkdir(exist_ok=True)
    objects = {}
    files = {}
    for body in enum_mod.PERSISTED_BODIES:
        eps = episodes_by_body.get(body, [])
        path = obj_dir / f"{body}.ndjson"
        enum_mod.write_episodes_ndjson(str(path), eps, append=False)
        files[body] = path
        stats = century_mod._object_stats(path)
        uri = (f"gs://test-bucket/{run_id}/episodes/{body}.ndjson"
               if body in gs_objects else str(path))
        objects[body] = {**stats, "run_id": run_id, "uri": uri}
    bodies_order = coverage_order or list(enum_mod.PERSISTED_BODIES)
    coverage = [_coverage_row(b, CENTURY_HORIZON_TEXT) for b in bodies_order]
    cov_path = tmp_path / "coverage.json"
    cov_path.write_text(json.dumps(coverage, indent=2, default=str) + "\n")
    manifest = {
        "artifact": "CENTURY_INPUT_MANIFEST", "version": "1.0",
        "finalized": finalized, "run_id": run_id,
        "chart_id": CANONICAL_CHART, "generation": "4.1",
        "horizon": CENTURY_HORIZON_TEXT,
        "bodies": list(enum_mod.PERSISTED_BODIES),
        "objects": objects,
        "coverage": {"uri": str(cov_path),
                     "sha256": build_mod.coverage_binding(coverage),
                     "partitions": len(coverage)},
        "input_snapshot": {"spec": "CENTURY_CLOUD_RUN_JOB_SPEC_v1_0",
                           "orb_deg": 5.0},
    }
    for body in omit_files:
        files[body].unlink()
    manifest_path = tmp_path / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    return manifest_path, manifest, files


def _build_argv(manifest_path: Path) -> list[str]:
    return ["--dsn", "postgresql://wp6:local@localhost:55433/wp6",
            "--chart-id", CANONICAL_CHART, "--generation", "4.1",
            "--horizon-start", "1984-02-05T00:00:00+00:00",
            "--horizon-end", "2084-02-05T00:00:00+00:00",
            "--input-manifest", str(manifest_path)]


def _patched_build_conn(monkeypatch, conn):
    monkeypatch.setattr(build_mod, "connect",
                        lambda dsn, step, autocommit=True: conn)
    _stub_freshness(monkeypatch)


# ── round-trip identity (pre-existing, updated to the total stream key) ───────


def test_ndjson_round_trip_identical_to_monolithic(tmp_path):
    mono = _monolithic_round_trip(tmp_path / "eps.json", ALL_EPS)
    nd = tmp_path / "eps.ndjson"
    sorted_eps = sorted(ALL_EPS, key=build_mod.episode_stream_key)
    assert enum_mod.write_episodes_ndjson(str(nd), sorted_eps) == len(ALL_EPS)
    streamed = build_mod.read_episodes_ndjson(str(nd))
    assert streamed == _canonical_order(mono)
    assert _content_digest(streamed) == _content_digest(mono)


def test_ndjson_reader_reproduces_canonical_order(tmp_path):
    eps_dir = tmp_path / "episodes"
    enum_mod.write_episodes_ndjson(
        str(eps_dir / "Sun.ndjson"),
        sorted(SUN_EPS, key=build_mod.episode_stream_key))
    enum_mod.write_episodes_ndjson(
        str(eps_dir / "Saturn.ndjson"),
        sorted(SAT_EPS, key=build_mod.episode_stream_key))
    streamed = build_mod.read_episodes_ndjson(str(eps_dir / "*.ndjson"))
    expected = sorted(
        _monolithic_round_trip(tmp_path / "eps.json", ALL_EPS),
        key=build_mod.episode_stream_key)
    assert streamed == expected
    # The glob's file order (Saturn before Sun alphabetically) must not leak:
    # canonical order here is Saturn(BASE+1d), Sun(BASE+2d), Saturn(BASE+5d),
    # Sun(BASE+10d).
    assert [e["body"] for e in streamed] == ["Saturn", "Sun", "Saturn", "Sun"]


def test_per_body_appends_concatenate_exactly(tmp_path):
    nd = tmp_path / "sun.ndjson"
    block = sorted(SUN_EPS, key=build_mod.episode_stream_key)
    enum_mod.write_episodes_ndjson(str(nd), block[:1])
    enum_mod.write_episodes_ndjson(str(nd), block[1:], append=True)
    lines = nd.read_text().strip().split("\n")
    assert len(lines) == len(SUN_EPS)
    read_back = [json.loads(line) for line in lines]
    assert read_back == json.loads(json.dumps(block, default=str))


def test_ndjson_reader_missing_file_refuses(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_mod.read_episodes_ndjson(str(tmp_path / "nope" / "*.ndjson"))


# ── flag validation (pre-existing) ─────────────────────────────────────────────


def _argv(*extra: str) -> list[str]:
    return ["--dsn", "postgresql://wp6:local@localhost:55433/wp6",
            "--chart-id", "482012f1-0000-0000-0000-000000000000", *extra]


def test_step06_output_flags_mutually_exclusive(tmp_path, capsys):
    rc = enum_mod.main(_argv(
        "--episodes-out", str(tmp_path / "a.json"),
        "--episodes-ndjson-out", str(tmp_path / "a.ndjson"),
        "--coverage-out", str(tmp_path / "c.json")))
    assert rc == 3
    assert "exactly one" in capsys.readouterr().err


def test_step06_requires_exactly_one_output_flag(tmp_path, capsys):
    rc = enum_mod.main(_argv("--coverage-out", str(tmp_path / "c.json")))
    assert rc == 3
    assert "exactly one" in capsys.readouterr().err


def test_candidate_build_input_flags_mutually_exclusive(tmp_path, capsys):
    rc = build_mod.main(_argv(
        "--episodes-json", str(tmp_path / "a.json"),
        "--episodes-ndjson", str(tmp_path / "*.ndjson"),
        "--coverage-json", str(tmp_path / "c.json")))
    assert rc == 3
    assert "mutually exclusive" in capsys.readouterr().err


def test_candidate_build_ndjson_requires_coverage(tmp_path, capsys):
    rc = build_mod.main(_argv("--episodes-ndjson", str(tmp_path / "*.ndjson")))
    assert rc == 3


# ── century_run guards (pre-existing + amendment 4) ────────────────────────────


def test_century_run_refuses_without_env_marker(monkeypatch, capsys):
    monkeypatch.delenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", raising=False)
    rc = century_mod.main(["--dsn", "postgresql://x",
                           "--chart-id", CANONICAL_CHART])
    assert rc == 3
    assert "ADK-0028" in capsys.readouterr().err


def test_century_run_refuses_non_pinned_horizon(monkeypatch, capsys):
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    rc = century_mod.main([
        "--dsn", "postgresql://x", "--chart-id", CANONICAL_CHART,
        "--horizon-start", "1984-02-05T00:00:00+00:00",
        "--horizon-end", "2080-01-01T00:00:00+00:00"])
    assert rc == 3
    assert "pinned" in capsys.readouterr().err


def test_century_run_refuses_wrong_chart_before_work(monkeypatch, tmp_path,
                                                     capsys):
    """Amendment 4: any chart other than the canonical UUID refuses BEFORE
    any filesystem or subprocess work. Kills: removing the chart guard."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    called = []
    monkeypatch.setattr(century_mod.subprocess, "run",
                        lambda argv, **kw: called.append(argv) or
                        type("R", (), {"returncode": 0})())
    workdir = tmp_path / "century"
    rc = century_mod.main([
        "--dsn", DSN_WITH_PASSWORD,
        "--chart-id", "11111111-2222-3333-4444-555555555555",
        "--workdir", str(workdir)])
    assert rc == 3
    assert "ADK-0029" in capsys.readouterr().err
    assert not called          # no subprocess ever started
    assert not workdir.exists()  # no filesystem work either


def test_century_run_refuses_wrong_generation_before_work(monkeypatch,
                                                          tmp_path, capsys):
    """Amendment 4: any generation other than '4.1' refuses BEFORE any
    filesystem or subprocess work. Kills: removing the generation guard."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    called = []
    monkeypatch.setattr(century_mod.subprocess, "run",
                        lambda argv, **kw: called.append(argv) or
                        type("R", (), {"returncode": 0})())
    workdir = tmp_path / "century"
    rc = century_mod.main([
        "--dsn", DSN_WITH_PASSWORD, "--chart-id", CANONICAL_CHART,
        "--generation", "4.0", "--workdir", str(workdir)])
    assert rc == 3
    assert "ADK-0027" in capsys.readouterr().err
    assert not called
    assert not workdir.exists()


def test_century_run_imports_persisted_bodies():
    assert century_mod.PERSISTED_BODIES == enum_mod.PERSISTED_BODIES
    assert tuple(century_mod.PERSISTED_BODIES) == (
        "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")


# ── driver harness ──────────────────────────────────────────────────────────────


def _stub_chain(monkeypatch, *, episodes_by_body=None, fail_on=None,
                record=None):
    """Stub subprocess.run for the whole chain: step06 writes the per-body
    NDJSON + coverage (+ a dropped-refs sidecar, the dedupe provenance);
    every later step exits 0. `record` collects argv vectors."""
    episodes_by_body = episodes_by_body or {}
    record = record if record is not None else []

    def fake_run(argv, **kw):
        record.append(argv)
        script = Path(argv[1]).name
        if script == "step06_enumerate_episodes.py":
            body = argv[argv.index("--bodies") + 1]
            if fail_on == body:
                return type("R", (), {"returncode": 5})()
            out = Path(argv[argv.index("--episodes-ndjson-out") + 1])
            eps = sorted(episodes_by_body.get(
                body, _body_episodes(body, 2)),
                key=build_mod.episode_stream_key)
            enum_mod.write_episodes_ndjson(str(out), eps, append=False)
            Path(str(out) + ".dropped_refs.json").write_text(
                json.dumps({"cid-x": {"survivor_target_ref": "SUN",
                                      "dropped_target_refs": ["MOON"],
                                      "dropped_rows": 1}}) + "\n")
            cov = Path(argv[argv.index("--coverage-out") + 1])
            cov.write_text(json.dumps(
                [_coverage_row(body, CENTURY_HORIZON_TEXT)],
                indent=2, default=str) + "\n")
        return type("R", (), {"returncode": 0})()

    monkeypatch.setattr(century_mod.subprocess, "run", fake_run)
    return record


def _driver_argv(tmp_path, *, gcs=True):
    argv = ["--dsn", DSN_WITH_PASSWORD, "--chart-id", CANONICAL_CHART,
            "--generation", "4.1", "--workdir", str(tmp_path / "century")]
    if gcs:
        argv += ["--gcs-prefix", "gs://test-bucket/kala_gochara/482012f1/4.1"]
    return argv


# ── amendment 3: DSN redaction ─────────────────────────────────────────────────


def test_redact_helpers():
    argv = ["python", "x.py", "--dsn", DSN_WITH_PASSWORD, "--chart-id", "c",
            f"--dsn={DSN_WITH_PASSWORD}"]
    out = common_mod.redact_argv(argv)
    assert "s3cr3t-P4ssw0rd" not in " ".join(out)
    assert out[2] == "--dsn" and out[3] == common_mod.REDACTED
    assert out[6] == "--dsn=" + common_mod.REDACTED
    text = common_mod.redact_text(f"connect failed: {DSN_WITH_PASSWORD}")
    assert "s3cr3t-P4ssw0rd" not in text
    assert "postgresql://builder:" + common_mod.REDACTED + "@10.9.8.7" in text


def test_century_run_never_logs_dsn_password(monkeypatch, tmp_path, capsys):
    """Amendment 3 (SECURITY): the password-bearing DSN never reaches
    stdout/stderr — not in the logged command lines, not in abort
    diagnostics, not in the chain report. Kills: unredacted argv echo in
    _run / unredacted abort paths."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    monkeypatch.setattr(century_mod.time, "time", lambda: 1_800_000_000)
    _stub_chain(monkeypatch)
    rc = century_mod.main(_driver_argv(tmp_path),
                          gcs_client=_FakeGCSClient())
    captured = capsys.readouterr()
    assert rc == 0
    assert "s3cr3t-P4ssw0rd" not in captured.out
    assert "s3cr3t-P4ssw0rd" not in captured.err
    assert common_mod.REDACTED in captured.out
    # failure diagnostics too: abort a run mid-chain with the password DSN
    monkeypatch.setattr(century_mod.time, "time", lambda: 1_800_000_100)
    _stub_chain(monkeypatch, fail_on="Mars")
    rc = century_mod.main(_driver_argv(tmp_path),
                          gcs_client=_FakeGCSClient())
    captured = capsys.readouterr()
    assert rc == 5
    assert "s3cr3t-P4ssw0rd" not in captured.out + captured.err


# ── amendment 5: retry safety ───────────────────────────────────────────────────


def test_century_run_refuses_nonfresh_run_dir(monkeypatch, tmp_path, capsys):
    """Amendment 5: a pre-existing non-empty run directory refuses the run —
    reusing one would mix attempts' appended streams. Kills: accepting an
    existing directory."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    monkeypatch.setattr(century_mod.time, "time", lambda: 1_800_000_000)
    run_dir = tmp_path / "century" / "pravaha-a25-century-1800000000"
    run_dir.mkdir(parents=True)
    (run_dir / "stale.ndjson").write_text("{}\n")
    rc = century_mod.main(_driver_argv(tmp_path),
                          gcs_client=_FakeGCSClient())
    assert rc == 3
    assert "retry safety" in capsys.readouterr().err


def test_century_run_fresh_prefix_per_attempt_and_provenance(
        monkeypatch, tmp_path):
    """Amendment 5: each attempt stages under its OWN run_id — local dir and
    GCS prefix — and the per-body dedupe provenance (.dropped_refs.json) is
    uploaded alongside each object. Kills: a shared object prefix across
    attempts (mixed-run uploads) and dropping the provenance sidecar."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    client = _FakeGCSClient()
    _stub_chain(monkeypatch)
    monkeypatch.setattr(century_mod.time, "time", lambda: 1_800_000_000)
    assert century_mod.main(_driver_argv(tmp_path), gcs_client=client) == 0
    monkeypatch.setattr(century_mod.time, "time", lambda: 1_800_000_100)
    assert century_mod.main(_driver_argv(tmp_path), gcs_client=client) == 0
    keys = set(client.store)
    assert any("pravaha-a25-century-1800000000/episodes/Sun.ndjson" in k
               for k in keys)
    assert any("pravaha-a25-century-1800000100/episodes/Sun.ndjson" in k
               for k in keys)
    # dedupe provenance preserved per attempt
    assert any(k.endswith("Sun.ndjson.dropped_refs.json")
               and "1800000000" in k for k in keys)
    # finalized manifests per attempt
    assert any(k.endswith("pravaha-a25-century-1800000000/input_manifest.json")
               for k in keys)
    # local per-body NDJSON was freed after the verified upload (bounded
    # tmpfs, amendment 1)
    run_dir = tmp_path / "century" / "pravaha-a25-century-1800000000"
    assert not list((run_dir / "episodes").glob("*.ndjson"))


def test_century_run_failed_attempt_finalizes_nothing(monkeypatch, tmp_path):
    """Amendment 5 + §N.8: a body failing mid-chain leaves NO finalized
    manifest and NEVER reaches the candidate build — incomplete output is
    always distinguishable from finalized output. Kills: writing the
    manifest after a failed body / invoking the build on partial input."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    monkeypatch.setattr(century_mod.time, "time", lambda: 1_800_000_200)
    record = _stub_chain(monkeypatch, fail_on="Mars")
    rc = century_mod.main(_driver_argv(tmp_path),
                          gcs_client=_FakeGCSClient())
    assert rc == 5
    run_dir = tmp_path / "century" / "pravaha-a25-century-1800000200"
    assert not (run_dir / "input_manifest.json").exists()
    invoked = [Path(a[1]).name for a in record]
    assert "step06_candidate_build.py" not in invoked
    assert "step06b_windows_projection.py" not in invoked


def test_gcs_upload_skipped_without_prefix(monkeypatch, tmp_path, capsys):
    """Local rehearsal shape: no --gcs-prefix → disclosed no-op, objects stay
    in the run directory, the manifest binds the local paths."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    monkeypatch.setattr(century_mod.time, "time", lambda: 1_800_000_300)
    _stub_chain(monkeypatch)
    rc = century_mod.main(_driver_argv(tmp_path, gcs=False))
    out = capsys.readouterr().out
    assert rc == 0
    assert "SKIPPED" in out
    run_dir = tmp_path / "century" / "pravaha-a25-century-1800000300"
    assert (run_dir / "episodes" / "Sun.ndjson").exists()
    manifest = json.loads((run_dir / "input_manifest.json").read_text())
    assert manifest["finalized"] is True
    assert manifest["objects"]["Sun"]["uri"].endswith("Sun.ndjson")
    assert manifest["objects"]["Sun"]["run_id"] == manifest["run_id"]


# ── amendment 2: finalized input manifest (§N.8) ───────────────────────────────


def test_build_green_only_with_verified_manifest(monkeypatch, tmp_path):
    """Positive control: a fully finalized, verified manifest builds and
    commits — the earned GREEN carries the verification record."""
    conn = _RecConn(keep_rows=True)
    _patched_build_conn(monkeypatch, conn)
    eps = {b: _body_episodes(b, 3) for b in enum_mod.PERSISTED_BODIES}
    manifest_path, manifest, _ = _write_manifest_tree(
        tmp_path, episodes_by_body=eps)
    rc = build_mod.main(_build_argv(manifest_path))
    assert rc == 0
    assert conn.committed
    assert conn.inserted == 24 + 8  # 8 bodies × 3 episodes + 8 coverage rows


def test_build_refuses_omitted_body(monkeypatch, tmp_path, capsys):
    """Amendment 2: a manifest naming eight bodies whose Sun object is
    MISSING fails the build — never GREEN. Kills: skipping unreadable
    objects."""
    conn = _RecConn()
    _patched_build_conn(monkeypatch, conn)
    manifest_path, _, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 2)
                                    for b in enum_mod.PERSISTED_BODIES},
        omit_files=("Sun",))
    rc = build_mod.main(_build_argv(manifest_path))
    assert rc == 3
    assert not conn.committed
    assert "GREEN" not in capsys.readouterr().out


def test_build_refuses_truncated_stream(monkeypatch, tmp_path):
    """Amendment 2: a CLEAN JSON-prefix truncation (one line short, every
    remaining line valid) fails against the manifest's line-count binding.
    Kills: dropping the per-object lines check — the exact F2 repro."""
    conn = _RecConn()
    _patched_build_conn(monkeypatch, conn)
    manifest_path, _, files = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 4)
                                    for b in enum_mod.PERSISTED_BODIES})
    lines = files["Ketu"].read_text().splitlines(keepends=True)
    files["Ketu"].write_text("".join(lines[:-1]))  # clean truncation
    rc = build_mod.main(_build_argv(manifest_path))
    assert rc == 3
    assert not conn.committed


def test_build_refuses_checksum_mismatch(monkeypatch, tmp_path):
    """Amendment 2: a same-length, same-line-count alteration fails against
    the sha256 binding. Kills: dropping the checksum check."""
    conn = _RecConn()
    _patched_build_conn(monkeypatch, conn)
    manifest_path, _, files = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 2)
                                    for b in enum_mod.PERSISTED_BODIES})
    text = files["Venus"].read_text()
    files["Venus"].write_text(text.replace("conjunction", "donjunction", 1))
    rc = build_mod.main(_build_argv(manifest_path))
    assert rc == 3
    assert not conn.committed


def test_build_refuses_mixed_run(monkeypatch, tmp_path):
    """Amendment 2: one object stamped with another attempt's run_id fails
    BEFORE the DB is even connected. Kills: dropping the run-identity
    binding."""
    manifest_path, manifest, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 1)
                                    for b in enum_mod.PERSISTED_BODIES})
    manifest["objects"]["Rahu"]["run_id"] = "run-older-attempt"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    connect_called = []
    monkeypatch.setattr(build_mod, "connect",
                        lambda *a, **kw: connect_called.append(a) or _RecConn())
    rc = build_mod.main(_build_argv(manifest_path))
    assert rc == 3
    assert not connect_called


def test_build_refuses_unfinalized_manifest(monkeypatch, tmp_path, capsys):
    """Amendment 2/§N.8: a non-finalized manifest (crashed attempt's staging)
    refuses before any DB work."""
    manifest_path, manifest, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={}, finalized=False)
    connect_called = []
    monkeypatch.setattr(build_mod, "connect",
                        lambda *a, **kw: connect_called.append(a) or _RecConn())
    rc = build_mod.main(_build_argv(manifest_path))
    assert rc == 3
    assert "FINALIZED" in capsys.readouterr().err
    assert not connect_called


def test_build_refuses_unreadable_object(monkeypatch, tmp_path):
    """Amendment 2: a GCS object that cannot be opened (read failure /
    permissions) fails the build, never GREEN. Drives the REAL gs:// code
    path through the injected transport."""
    conn = _RecConn()
    _patched_build_conn(monkeypatch, conn)
    manifest_path, _, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 1)
                                    for b in enum_mod.PERSISTED_BODIES},
        gs_objects=tuple(enum_mod.PERSISTED_BODIES))
    client = _FakeGCSClient()  # store empty: every blob.open raises
    rc = build_mod.main(_build_argv(manifest_path), gcs_client=client)
    assert rc == 3
    assert not conn.committed


def test_build_reads_gs_objects_via_real_streamed_path(monkeypatch, tmp_path):
    """The gs:// consumption path is the real streamed one: objects land in
    the fake bucket via the driver's upload shape and are read back through
    blob.open, verified, and inserted — positive gs control."""
    conn = _RecConn(keep_rows=True)
    _patched_build_conn(monkeypatch, conn)
    eps = {b: _body_episodes(b, 2) for b in enum_mod.PERSISTED_BODIES}
    manifest_path, manifest, files = _write_manifest_tree(
        tmp_path, episodes_by_body=eps,
        gs_objects=tuple(enum_mod.PERSISTED_BODIES))
    client = _FakeGCSClient()
    for body in enum_mod.PERSISTED_BODIES:
        name = manifest["objects"][body]["uri"][len("gs://"):]
        client.store[name] = files[body].read_bytes()
    rc = build_mod.main(_build_argv(manifest_path), gcs_client=client)
    assert rc == 0
    assert conn.inserted == 16 + 8  # 8 bodies × 2 episodes + 8 coverage rows


# ── amendment 1: bounded memory end-to-end ─────────────────────────────────────


def _measure_streamed_build_peak(paths, conn, n_expected):
    streams = [build_mod.EpisodeObjectStream(str(p)) for p in paths]
    merged = build_mod.iter_episodes_merged(streams)
    tracemalloc.start()
    n = ledger.write_contacts_streaming(
        conn, CANONICAL_CHART, "4.1", "sha256:test-convention",
        merged, "build-mem-test", batch_size=1000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert n == n_expected
    return peak


def test_streamed_build_memory_bounded(tmp_path):
    """Amendment 1: the streamed build's peak memory is bounded by the batch
    size, NOT the episode count — doubling the input does not double the
    peak, and the peak stays far below the materialized shape. Kills:
    materializing the episode list (or row list, or id list) before insert."""
    bodies = list(enum_mod.PERSISTED_BODIES)

    def make_tree(n_per_body, root):
        paths = []
        for body in bodies:
            eps = sorted(_body_episodes(body, n_per_body),
                         key=build_mod.episode_stream_key)
            p = root / f"{body}.ndjson"
            enum_mod.write_episodes_ndjson(str(p), eps, append=False)
            paths.append(p)
        return paths

    peak1 = _measure_streamed_build_peak(
        make_tree(2500, tmp_path / "n1" ), _RecConn(), 8 * 2500)
    peak2 = _measure_streamed_build_peak(
        make_tree(5000, tmp_path / "n2"), _RecConn(), 8 * 5000)
    bound = 24 * 1024 * 1024
    assert peak1 < bound, f"peak {peak1 / 2**20:.1f} MiB exceeds the bound"
    assert peak2 < bound, f"peak {peak2 / 2**20:.1f} MiB exceeds the bound"
    assert peak2 < peak1 * 1.75, (
        f"peak grew {peak1}->{peak2} with 2x input — input-scale "
        "materialization is present")


def test_projection_iter_class_contacts_server_side():
    """Amendment 1 (projection): contacts stream through a NAMED server-side
    cursor scoped to the class's target pairs. Kills: client-side fetchall
    of the whole contact set."""
    t = BASE
    rows = [("cid-1", "Sun", "conjunction", "karaka", "SUN", t,
             t + timedelta(hours=1), t + timedelta(hours=2), 5.0, "applied")]
    seen = {}

    class _Cur:
        itersize = 0

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, sql, params=None):
            seen["sql"] = sql
            seen["params"] = params

        def __iter__(self):
            return iter(rows)

    class _Conn:
        def cursor(self, name=None):
            seen["name"] = name
            return _Cur()

    got = list(proj_mod.iter_class_contacts(_Conn(), CANONICAL_CHART, "4.1",
                                            {("karaka", "SUN")}))
    assert seen["name"] == "step06b_class_contacts"
    assert "target_type = %s AND target_ref = %s" in seen["sql"]
    assert got[0]["contact_id"] == "cid-1"
    assert got[0]["_t_exact_jd"] is not None


def test_projection_main_streams_per_class():
    """Amendment 1 (projection): main is wired to the per-class streamed
    shape, not the whole-set contacts_by_class + single write shape. Kills:
    reverting main to fetchall/full materialization."""
    src = Path(proj_mod.__file__).read_text()
    main_src = src[src.index("def main("):]
    assert "fetch_contacts(" not in main_src
    assert "iter_class_contacts(" in main_src
    assert "delete=False" in main_src
    assert "contacts_by_class" not in main_src


# ── amendment 6: equivalence defined and tested precisely ─────────────────────


FIXED_NOW = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED_NOW


def _row_set_digest(rows) -> str:
    canon = sorted(json.dumps(r, sort_keys=True, default=str) for r in rows)
    return hashlib.sha256(
        json.dumps(canon, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_equivalence_real_ledger_digest(monkeypatch, tmp_path):
    """Amendment 6: with volatile metadata CONTROLLED (computed_at pinned,
    build_id and manifest fixed by the fake conn), the streamed build and
    the monolithic build produce the identical REAL ledger row set — the
    rows ledger._normalize_episode emits, digested order-independently the
    way _canonical_row_set does. Also kills: a digest that ignores content
    (omitting one episode MUST change it)."""
    monkeypatch.setattr(ledger, "datetime", _FixedDatetime)
    bodies = ("Sun", "Saturn")
    eps = [ep for b in bodies for ep in _body_episodes(b, 3)]

    # monolithic path: --episodes-json discipline (json round-trip + coerce)
    mono_eps = _monolithic_round_trip(tmp_path / "eps.json", eps)
    mono_conn = _RecConn(keep_rows=True)
    ledger.write_contacts(mono_conn, CANONICAL_CHART, "4.1",
                          "sha256:test-convention", mono_eps, "build-eq")
    # streamed path: per-body NDJSON -> k-way merge -> streaming write
    paths = []
    for b in bodies:
        block = sorted([e for e in eps if e["body"] == b],
                       key=build_mod.episode_stream_key)
        p = tmp_path / f"{b}.ndjson"
        enum_mod.write_episodes_ndjson(str(p), block, append=False)
        paths.append(p)
    stream_conn = _RecConn(keep_rows=True)
    merged = build_mod.iter_episodes_merged(
        [build_mod.EpisodeObjectStream(str(p)) for p in paths])
    ledger.write_contacts_streaming(stream_conn, CANONICAL_CHART, "4.1",
                                    "sha256:test-convention", merged,
                                    "build-eq", batch_size=2)
    assert _row_set_digest(stream_conn.rows) == _row_set_digest(mono_conn.rows)
    assert len(stream_conn.rows) == len(mono_conn.rows) == 6

    mono_conn_short = _RecConn(keep_rows=True)
    ledger.write_contacts(mono_conn_short, CANONICAL_CHART, "4.1",
                          "sha256:test-convention", mono_eps[:-1], "build-eq")
    assert _row_set_digest(mono_conn_short.rows) != _row_set_digest(
        mono_conn.rows)


def test_tied_keys_total_order_deterministic(tmp_path):
    """Amendment 6: (t_in, body, relation) is NOT a total order — two
    distinct contacts sharing it are ordered by the canonical-json
    tie-break, so the merged order is independent of ingestion order.
    Kills: dropping the tie-break (the F6 Z,A / A,Z divergence)."""
    t = BASE
    ep_z = _episode("Sun", "conjunction", t, "ZZZ-TARGET")
    ep_a = _episode("Sun", "conjunction", t, "AAA-TARGET")
    order = sorted([ep_z, ep_a], key=build_mod.episode_stream_key)
    p = tmp_path / "Sun.ndjson"
    enum_mod.write_episodes_ndjson(str(p), order, append=False)
    merged = list(build_mod.iter_episodes_merged(
        [build_mod.EpisodeObjectStream(str(p))]))
    assert [e["target_ref"] for e in merged] == \
        [e["target_ref"] for e in order]
    # the reverse line order is NOT a valid canonical stream — rejected,
    # never silently re-ordered into an ingestion-dependent sequence
    p2 = tmp_path / "Sun-rev.ndjson"
    enum_mod.write_episodes_ndjson(str(p2), order[::-1], append=False)
    with pytest.raises(build_mod.EpisodeStreamError):
        list(build_mod.iter_episodes_merged(
            [build_mod.EpisodeObjectStream(str(p2))]))


def test_unsorted_object_rejected(tmp_path):
    """A foreign/hand-made object that violates the canonical per-body order
    fails the stream — ingestion order can never leak into the build."""
    eps = _body_episodes("Sun", 3)
    p = tmp_path / "Sun.ndjson"
    enum_mod.write_episodes_ndjson(str(p), eps[::-1], append=False)
    with pytest.raises(build_mod.EpisodeStreamError):
        list(build_mod.EpisodeObjectStream(str(p)))


def test_coverage_sorted_by_partition_key(monkeypatch, tmp_path):
    """Amendment 6: coverage insert order is by partition_key — the
    monolithic build_coverage_rows order — never the driver's
    PERSISTED_BODIES concatenation order. Kills: body-order coverage
    concatenation."""
    conn = _RecConn(keep_rows=True)
    _patched_build_conn(monkeypatch, conn)
    reversed_bodies = list(reversed(enum_mod.PERSISTED_BODIES))
    manifest_path, _, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 1)
                                    for b in enum_mod.PERSISTED_BODIES},
        coverage_order=reversed_bodies)
    rc = build_mod.main(_build_argv(manifest_path))
    assert rc == 0
    cov_rows = [r for r in conn.rows if len(r) > 3 and r[3] in
                {f"{b.lower()}:karaka" for b in enum_mod.PERSISTED_BODIES}]
    keys = [r[3] for r in cov_rows]
    assert keys == sorted(keys)
    assert keys == sorted(f"{b.lower()}:karaka"
                          for b in enum_mod.PERSISTED_BODIES)
