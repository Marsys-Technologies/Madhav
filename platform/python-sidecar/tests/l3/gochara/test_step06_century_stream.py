"""Pravāha A2.5 — the century streaming chain (CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 §2/§3),
as amended by ASTRA_REVIEW_A2_5_STREAMING v1.0 (six amendments) and v1.1 (the
six round-2 amendments).

Pure-python, no Swiss calls, no real DB, no real GCS. The fake GCS transport
drives the REAL streamed code path (blob.open / upload_from_filename with
if_generation_match through an injected client); the fake DB connection
drives the real ledger functions; the fake Popen drives the real driver
loop; one test spawns a REAL child process to prove child-output redaction
is streaming.

Round-2 amendment → test map (each test names the mutation it kills):

  r2-1 Memory bounded across the complete chain —
     test_streamed_build_memory_bounded (materializing the episode/row/id
       list before insert),
     test_class_context_streams_instants_bounded +
       test_class_context_never_fetchall (fetchall / per-class instant lists),
     test_projection_sweep_memory_bounded_disjoint_contacts +
       test_projection_sweep_memory_disproportionate_dense_class (retaining
       the class's contacts; the stated residual per contact),
     test_projection_sweep_equivalent_to_whole_class (any sweep that is not
       the pinned computation),
     test_projection_main_streams_per_class (reverting main),
     test_century_run_requires_external_staging (the local-retention route),
     test_memory_guard_forwarded_to_every_child +
       test_memory_guard_exceeded_aborts_before_manifest +
       test_apply_memory_guard_and_guarded_main (dropping the guard).
  r2-2 Verifiable manifest completeness and provenance —
     test_build_green_only_with_verified_manifest (positive control), then
     the reviewer's counterexamples, each refused with no commit and no
     GREEN: missing source snapshot, orb 999 vs 5.0, empty object without a
     completion receipt, receipt/object count disagreement, empty coverage,
     shortened coverage horizon, a Sun object carrying a Mercury contact,
     missing/unreadable dedupe sidecar, mixed-source receipts, missing
     ephemeris checksums, plus the round-1 set (omitted body, truncated
     stream, checksum mismatch, mixed run, unfinalized, unreadable object);
     driver side: test_century_run_refuses_body_without_receipt,
     test_century_run_refuses_mixed_source_bodies,
     test_century_run_manifest_binds_receipts_and_provenance (the driver's
       manifest must pass the build's own verifier end-to-end).
  r2-3 Complete credential redaction —
     test_redact_text_covers_all_credential_forms, test_parser_errors_redacted,
     test_child_output_redacted_and_streamed (a REAL child, streaming proven
       by a file handshake), test_uncaught_exception_and_connection_failure_redacted,
     test_century_run_never_logs_dsn_password.
  r2-4 Fresh, immutable attempt artifacts —
     test_new_attempt_id_collision_resistant, test_century_run_refuses_existing_attempt_dir,
     test_uploads_are_create_only, test_second_attempt_cannot_overwrite_finalized_objects.
  r2-5 Real identity, dedupe and digest —
     test_dedupe_explicit_identities_and_survivors (constant contact id;
       disabled dedupe), test_real_manifest_digest_controlled_metadata
       (constant digest; a digest that ignores content).
  r2-6 Exception classification — test_unique_violation_routes_to_exit_5.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import io
import json
import random
import sys
import tracemalloc
import types
from datetime import date, datetime, timedelta, timezone
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
S6A_PATH = CUT_OVER_DIR / "step06a_class_context.py"
LEDGER_PATH = (Path(__file__).resolve().parents[3]
               / "services" / "gochara_kernel" / "ledger.py")

UTC = timezone.utc
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
# Assembled from parts: a literal connection string in one line would (rightly)
# trip the repo secret scanner; the redaction tests need a realistic password shape.
DSN_PASSWORD = "s3cr3t-" + "P4ssw0rd"
DSN_WITH_PASSWORD = "postgresql://builder:" + DSN_PASSWORD + "@10.9.8.7:5432/madhav"
# a distinctive local password: its literal is registered for redaction by
# every script that parses it, so it must not be a substring of ordinary log
# text (e.g. 'local' inside 'localhost')
LOCAL_PASSWORD = "wp6-l0cal-" + "pw"
LOCAL_DSN = "postgresql://wp6:" + LOCAL_PASSWORD + "@localhost:55433/wp6"


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
s6a_mod = _load(S6A_PATH, "step06a_class_context")
ledger = _load(LEDGER_PATH, "test_a25_ledger")
# the SAME `common` instance the scripts import (their secret registry)
common_mod = importlib.import_module("common")

CONVENTION_ID = ledger.convention_id_for(build_mod.CONVENTION_VECTOR)
METHOD_VERSION = build_mod.CONVENTION_VECTOR["method_version"]


@pytest.fixture(autouse=True)
def _fresh_secret_registry():
    common_mod.clear_registered_secrets()
    yield
    common_mod.clear_registered_secrets()


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

CENTURY_HORIZON_TEXT = ("[1984-02-05T00:00:00+00:00,"
                        "2084-02-05T00:00:00+00:00)")

# run-level provenance the synthetic receipts carry (what step06 would bind)
SNAPSHOT = {
    "chart_id": CANONICAL_CHART,
    "resonance_map_sha256": "sha256:" + "a" * 64,
    "resonance_map_rows": 12,
    "resolution_facts_sha256": "sha256:" + "b" * 64,
    "upstream_fingerprints": {"house_vedha": {"rules": "sha256:x"},
                              "moorti": {"table": "sha256:y"}},
}
EPHEMERIS = {
    "path": "/ephe",
    "files": {"sepl_18.se1": "sha256:" + "1" * 64,
              "semo_18.se1": "sha256:" + "2" * 64,
              "seas_18.se1": "sha256:" + "3" * 64},
    "backends": {},
}
CONFIGURATION = {"orb_deg": 5.0, "refine": True,
                 "candidate_flags": dict(enum_mod.CANDIDATE_FLAGS),
                 "ephe_path": "/ephe"}


def _monolithic_round_trip(path: Path, episodes: list[dict]) -> list[dict]:
    """What the decade-scale path does: json.dumps(indent=2, default=str) out,
    json.loads + _coerce_episode_times back in."""
    path.write_text(json.dumps(episodes, indent=2, default=str) + "\n")
    return build_mod._coerce_episode_times(json.loads(path.read_text()))


def _content_digest(episodes: list[dict]) -> str:
    canon = sorted(
        json.dumps(e, sort_keys=True, separators=(",", ":"), default=str)
        for e in episodes)
    return hashlib.sha256(
        json.dumps(canon, separators=(",", ":")).encode("utf-8")).hexdigest()


def _canonical_order(episodes: list[dict]) -> list[dict]:
    return sorted(episodes, key=build_mod.episode_stream_key)


def _body_episodes(body: str, n: int, *, start: datetime = BASE) -> list[dict]:
    return [_episode(body, "conjunction", start + timedelta(days=3 * i),
                     f"{body.upper()}-{i}")
            for i in range(n)]


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
        if self.conn.raise_on_insert is not None:
            raise self.conn.raise_on_insert
        self.conn.batch_sizes.append(len(rows))
        if self.conn.keep_rows:
            self.conn.rows.extend(rows)
        self.conn.inserted += len(rows)


class _RecConn:
    """In-memory SQL recorder shaped for the ledger's call pattern."""

    def __init__(self, *, keep_rows=False, raise_on_insert=None):
        self.keep_rows = keep_rows
        self.raise_on_insert = raise_on_insert
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


class _PreconditionFailed(Exception):
    """google.api_core.exceptions.PreconditionFailed stand-in (HTTP 412)."""
    code = 412


class _FakeBlob:
    def __init__(self, client, name):
        self.client = client
        self.store = client.store
        self.name = name
        self.size = None

    def upload_from_filename(self, path, if_generation_match=None, **kw):
        self.client.upload_calls.append(
            {"name": self.name, "if_generation_match": if_generation_match})
        if if_generation_match == 0 and self.name in self.store:
            raise _PreconditionFailed(f"412 object {self.name} exists")
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
    real one, including the create-only precondition."""

    def __init__(self):
        self.store: dict[str, bytes] = {}
        self.upload_calls: list[dict] = []

    def bucket(self, name):
        client = self

        class _Bucket:
            def blob(self, blob_name):
                return _FakeBlob(client, f"{name}/{blob_name}")

        return _Bucket()

    def put(self, uri: str, data: bytes) -> None:
        assert uri.startswith("gs://")
        self.store[uri[len("gs://"):]] = data


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


def _patched_build_conn(monkeypatch, conn):
    monkeypatch.setattr(build_mod, "connect",
                        lambda dsn, step, autocommit=True: conn)
    _stub_freshness(monkeypatch)


# ── synthetic enumeration artifacts (what step06 writes per body) ─────────────


def _make_receipt(body: str, ndjson: Path, cov_rows: list[dict], cov_path: Path,
                  dropped: Path | None, *, orb: float = 5.0,
                  snapshot: dict | None = None, ephe: dict | None = None,
                  completed: bool = True) -> dict:
    st = common_mod.file_stats(ndjson)
    n = st["lines"]
    dr = common_mod.file_stats(dropped) if dropped else None
    fresh = lambda d: json.loads(json.dumps(d))  # noqa: E731 — deep copy
    return {
        "artifact": build_mod.RECEIPT_ARTIFACT,
        "version": build_mod.RECEIPT_VERSION,
        "completed": completed,
        "chart_id": CANONICAL_CHART, "generation": "4.1",
        "horizon": CENTURY_HORIZON_TEXT,
        "bodies_enumerated": [body],
        "convention_id": CONVENTION_ID, "method_version": METHOD_VERSION,
        "configuration": fresh({**CONFIGURATION, "orb_deg": orb}),
        "source_snapshot": fresh(snapshot or SNAPSHOT),
        "ephemeris": fresh(ephe or EPHEMERIS),
        "episodes": {"format": "ndjson-append", "path": str(ndjson), **st,
                     "lines_written": n, "episodes_before_dedupe": n + (1 if dropped else 0),
                     "episodes_after_dedupe": n},
        "dedupe": {"rows_dropped": 1 if dropped else 0,
                   "duplicate_groups": 1 if dropped else 0,
                   "dropped_refs_artifact": str(dropped) if dropped else None,
                   "dropped_refs_contacts": 1 if dropped else 0,
                   "dropped_refs_sha256": dr["sha256"] if dr else None,
                   "dropped_refs_bytes": dr["bytes"] if dr else None},
        "coverage": {"path": str(cov_path), "partitions": len(cov_rows),
                     "sha256": build_mod.coverage_binding(cov_rows)},
        "sky_boundary_events": 0,
    }


def _write_manifest_tree(tmp_path: Path, *, episodes_by_body: dict,
                         run_id="run-test-1", finalized=True,
                         omit_files=(), gcs_client: _FakeGCSClient | None = None,
                         coverage_order=None, coverage_rows=None,
                         sidecar_bodies=None, mutate_receipt=None,
                         mutate_manifest=None):
    """Write per-body NDJSON objects + dedupe sidecars + completion receipts +
    coverage + a finalized v1.1 input manifest the way century_run does.
    With `gcs_client` every binding is a gs:// URI backed by the fake store
    (the real streamed read path). Returns (manifest_uri, manifest, files)."""
    episodes_by_body = {b: sorted(eps, key=build_mod.episode_stream_key)
                        for b, eps in episodes_by_body.items()}
    sidecar_bodies = (set(enum_mod.PERSISTED_BODIES) if sidecar_bodies is None
                      else set(sidecar_bodies))
    obj_dir = tmp_path / "objects"
    obj_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"gs://test-bucket/{run_id}"

    def _uri(local: Path, rel: str) -> str:
        if gcs_client is None:
            return str(local)
        uri = f"{prefix}/{rel}"
        gcs_client.put(uri, local.read_bytes())
        return uri

    objects, files, provenance = {}, {}, None
    cov_by_body: dict[str, list[dict]] = {}
    for body in enum_mod.PERSISTED_BODIES:
        eps = episodes_by_body.get(body, [])
        path = obj_dir / f"{body}.ndjson"
        enum_mod.write_episodes_ndjson(str(path), eps, append=False)
        files[body] = path
        dropped = None
        if body in sidecar_bodies:
            dropped = Path(str(path) + ".dropped_refs.json")
            dropped.write_text(json.dumps({f"cid-{body}": {
                "survivor_target_ref": "SUN", "survivor_citation": None,
                "dropped_target_refs": ["MOON"], "dropped_citations": [],
                "dropped_rows": 1}}) + "\n")
        cov_rows = [_coverage_row(body, CENTURY_HORIZON_TEXT)]
        cov_by_body[body] = cov_rows
        cov_path = obj_dir / f"{body}.coverage.json"
        cov_path.write_text(json.dumps(cov_rows, indent=2) + "\n")
        receipt = _make_receipt(body, path, cov_rows, cov_path, dropped)
        if mutate_receipt is not None:
            mutate_receipt(body, receipt)
        receipt_path = obj_dir / f"{body}.receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, default=str) + "\n")
        if provenance is None:
            provenance = build_mod.receipt_provenance(receipt)
        stats = common_mod.file_stats(path)
        r_stats = common_mod.file_stats(receipt_path)
        entry = {**stats, "run_id": run_id,
                 "episodes_after_dedupe": receipt["episodes"]["episodes_after_dedupe"],
                 "uri": _uri(path, f"episodes/{body}.ndjson"),
                 "receipt": {"uri": _uri(receipt_path, f"episodes/{body}.receipt.json"),
                             "bytes": r_stats["bytes"], "sha256": r_stats["sha256"]},
                 "dropped_refs": None}
        if dropped is not None:
            d_stats = common_mod.file_stats(dropped)
            entry["dropped_refs"] = {
                "uri": _uri(dropped, f"episodes/{body}.ndjson.dropped_refs.json"),
                "bytes": d_stats["bytes"], "sha256": d_stats["sha256"]}
        objects[body] = entry
    if coverage_rows is None:
        bodies_order = coverage_order or list(enum_mod.PERSISTED_BODIES)
        coverage = [r for b in bodies_order for r in cov_by_body[b]]
    else:
        coverage = coverage_rows
    partitions_by_body = {b: 0 for b in enum_mod.PERSISTED_BODIES}
    for r in coverage:
        b = r["partition_key"].split(":")[0]
        for pb in partitions_by_body:
            if pb.lower() == b:
                partitions_by_body[pb] += 1
    cov_path = tmp_path / "coverage.json"
    cov_path.write_text(json.dumps(coverage, indent=2, default=str) + "\n")
    manifest = {
        "artifact": build_mod.MANIFEST_ARTIFACT,
        "version": build_mod.MANIFEST_VERSION,
        "finalized": finalized, "run_id": run_id, "attempt_id": run_id,
        "chart_id": CANONICAL_CHART, "generation": "4.1",
        "horizon": CENTURY_HORIZON_TEXT,
        "bodies": list(enum_mod.PERSISTED_BODIES),
        "objects": objects,
        "coverage": {"uri": _uri(cov_path, "coverage.json"),
                     "sha256": build_mod.coverage_binding(coverage),
                     "partitions": len(coverage),
                     "partitions_by_body": partitions_by_body},
        **provenance,
    }
    if mutate_manifest is not None:
        mutate_manifest(manifest)
    for body in omit_files:
        files[body].unlink()
        if gcs_client is not None:
            gcs_client.store.pop(objects[body]["uri"][len("gs://"):], None)
    manifest_path = tmp_path / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    return _uri(manifest_path, "input_manifest.json"), manifest, files


def _build_argv(manifest_uri: str, *, orb: float | None = None) -> list[str]:
    argv = ["--dsn", LOCAL_DSN,
            "--chart-id", CANONICAL_CHART, "--generation", "4.1",
            "--horizon-start", "1984-02-05T00:00:00+00:00",
            "--horizon-end", "2084-02-05T00:00:00+00:00",
            "--input-manifest", manifest_uri]
    if orb is not None:
        argv += ["--orb-deg", str(orb)]
    return argv


def _refused(monkeypatch, tmp_path, capsys, **tree_kwargs) -> tuple[_RecConn, str]:
    """Build a manifest tree with the given mutation and assert the build
    refuses it: exit 3, no commit, no GREEN. Returns (conn, stderr)."""
    conn = _RecConn()
    _patched_build_conn(monkeypatch, conn)
    manifest_uri, _, _ = _write_manifest_tree(tmp_path, **tree_kwargs)
    rc = build_mod.main(_build_argv(manifest_uri))
    out = capsys.readouterr()
    assert rc == 3, out.err
    assert not conn.committed
    assert "GREEN" not in out.out
    return conn, out.err


# ── round-trip identity (pre-existing, total stream key) ─────────────────────


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
    return ["--dsn", LOCAL_DSN,
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


def test_step06_refuses_preexisting_receipt(tmp_path, capsys):
    """A completion receipt is written once per fresh invocation — a
    pre-existing one is another attempt's and refuses before any work."""
    receipt = tmp_path / "Sun.receipt.json"
    receipt.write_text("{}\n")
    rc = enum_mod.main(_argv(
        "--episodes-ndjson-out", str(tmp_path / "a.ndjson"),
        "--coverage-out", str(tmp_path / "c.json"),
        "--receipt-out", str(receipt)))
    assert rc == 3
    assert "receipt" in capsys.readouterr().err


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


# ── century_run guards (amendment 4 + external staging) ────────────────────────


def _no_subprocess(monkeypatch):
    called = []
    monkeypatch.setattr(century_mod.subprocess, "Popen",
                        lambda argv, **kw: called.append(argv) or
                        _FakeProc([], 0))
    return called


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
    called = _no_subprocess(monkeypatch)
    workdir = tmp_path / "century"
    rc = century_mod.main([
        "--dsn", DSN_WITH_PASSWORD,
        "--chart-id", "11111111-2222-3333-4444-555555555555",
        "--gcs-prefix", "gs://test-bucket/p", "--workdir", str(workdir)])
    assert rc == 3
    assert "ADK-0029" in capsys.readouterr().err
    assert not called
    assert not workdir.exists()


def test_century_run_refuses_wrong_generation_before_work(monkeypatch,
                                                          tmp_path, capsys):
    """Amendment 4: any generation other than '4.1' refuses BEFORE any
    filesystem or subprocess work. Kills: removing the generation guard."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    called = _no_subprocess(monkeypatch)
    workdir = tmp_path / "century"
    rc = century_mod.main([
        "--dsn", DSN_WITH_PASSWORD, "--chart-id", CANONICAL_CHART,
        "--generation", "4.0", "--gcs-prefix", "gs://test-bucket/p",
        "--workdir", str(workdir)])
    assert rc == 3
    assert "ADK-0027" in capsys.readouterr().err
    assert not called
    assert not workdir.exists()


def test_century_run_requires_external_staging(monkeypatch, tmp_path, capsys):
    """Round-2 amendment 1: the century path stages EXTERNALLY, always — no
    --gcs-prefix refuses before any filesystem/subprocess work. Kills:
    re-admitting the local-retention route."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    called = _no_subprocess(monkeypatch)
    workdir = tmp_path / "century"
    rc = century_mod.main(["--dsn", DSN_WITH_PASSWORD,
                           "--chart-id", CANONICAL_CHART,
                           "--workdir", str(workdir)])
    assert rc == 3
    assert "external staging" in capsys.readouterr().err
    assert not called
    assert not workdir.exists()


def test_century_run_imports_persisted_bodies():
    assert century_mod.PERSISTED_BODIES == enum_mod.PERSISTED_BODIES
    assert tuple(century_mod.PERSISTED_BODIES) == (
        "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")


# ── driver harness ──────────────────────────────────────────────────────────────


class _FakeProc:
    """What century_run._run needs from Popen: a line-iterable, context-
    managed stdout and wait()."""

    def __init__(self, lines, rc):
        self.stdout = io.StringIO("".join(lines))
        self._rc = rc

    def wait(self):
        return self._rc


def _stub_chain(monkeypatch, *, episodes_by_body=None, fail_on=None,
                record=None, omit_receipt_for=(), snapshot_for=None,
                no_sidecar_for=(), extra_lines=None):
    """Stub Popen for the whole chain: step06 writes the per-body NDJSON +
    dedupe sidecar + coverage + completion receipt (exactly the artifacts
    the real enumerator writes); every child echoes the DSN it received in
    URI AND libpq keyword form (a leaky child); every later step exits 0.
    `record` collects argv vectors."""
    episodes_by_body = episodes_by_body or {}
    record = record if record is not None else []

    def fake_popen(argv, **kw):
        record.append(argv)
        script = Path(argv[1]).name
        dsn = argv[argv.index("--dsn") + 1]
        pw = common_mod.dsn_secrets(dsn)[0] if common_mod.dsn_secrets(dsn) else ""
        lines = [f"{script}: connecting with {dsn}\n",
                 f"{script}: libpq form host=h user=u password={pw} dbname=d\n"]
        if extra_lines:
            lines += list(extra_lines)
        rc = 0
        if script == "step06_enumerate_episodes.py":
            body = argv[argv.index("--bodies") + 1]
            if fail_on == body:
                return _FakeProc(lines + ["REFUSED (ADK-0020): synthetic\n"], 5)
            out = Path(argv[argv.index("--episodes-ndjson-out") + 1])
            eps = sorted(episodes_by_body.get(
                body, _body_episodes(body, 2)),
                key=build_mod.episode_stream_key)
            enum_mod.write_episodes_ndjson(str(out), eps, append=False)
            dropped = None
            if body not in no_sidecar_for:
                dropped = Path(str(out) + ".dropped_refs.json")
                dropped.write_text(json.dumps({"cid-x": {
                    "survivor_target_ref": "SUN", "survivor_citation": None,
                    "dropped_target_refs": ["MOON"], "dropped_citations": [],
                    "dropped_rows": 1}}) + "\n")
            cov_rows = [_coverage_row(body, CENTURY_HORIZON_TEXT)]
            cov = Path(argv[argv.index("--coverage-out") + 1])
            cov.write_text(json.dumps(cov_rows, indent=2, default=str) + "\n")
            if body not in omit_receipt_for:
                receipt = _make_receipt(
                    body, out, cov_rows, cov, dropped,
                    orb=float(argv[argv.index("--orb-deg") + 1]),
                    snapshot=snapshot_for(body) if snapshot_for else None)
                Path(argv[argv.index("--receipt-out") + 1]).write_text(
                    json.dumps(receipt, indent=2, default=str) + "\n")
        return _FakeProc(lines, rc)

    monkeypatch.setattr(century_mod.subprocess, "Popen", fake_popen)
    return record


def _driver_argv(tmp_path, *, workdir=None, extra=()) -> list[str]:
    return ["--dsn", DSN_WITH_PASSWORD, "--chart-id", CANONICAL_CHART,
            "--generation", "4.1",
            "--workdir", str(workdir or (tmp_path / "century")),
            "--gcs-prefix", "gs://test-bucket/kala_gochara/482012f1/4.1",
            *extra]


def _fixed_attempts(monkeypatch, *ids: str):
    it = iter(ids)
    monkeypatch.setattr(century_mod, "new_attempt_id", lambda: next(it))


# ── round-2 amendment 3: complete credential redaction ─────────────────────────


def test_redact_text_covers_all_credential_forms():
    """Every libpq credential form is redacted by the pattern layer; a form
    the patterns do not anticipate is still scrubbed by the literal layer
    once the DSN is registered. Kills: any single-form redactor."""
    pw = DSN_PASSWORD
    forms = [
        DSN_WITH_PASSWORD,
        f"postgresql://builder@10.9.8.7:5432/madhav?password={pw}&sslmode=require",
        f"postgresql://10.9.8.7/madhav?sslmode=require&password={pw}",
        f"host=10.9.8.7 user=builder password={pw} dbname=madhav",
        f"host=10.9.8.7 password='{pw} sp' dbname=madhav",
        f'password="{pw}" host=x',
        f"PGPASSWORD={pw} psql",
        f"Namespace(dsn='{DSN_WITH_PASSWORD}')",
    ]
    for form in forms:
        out = common_mod.redact_text(form)
        assert pw not in out, form
        assert common_mod.REDACTED in out
    assert common_mod.redact_text(DSN_WITH_PASSWORD) == \
        "postgresql://builder:" + common_mod.REDACTED + "@10.9.8.7:5432/madhav"
    # literal layer: a form no pattern matches
    exotic = f"pw is {pw} here"
    assert pw in common_mod.redact_text(exotic)  # patterns alone miss it
    common_mod.register_dsn_secrets(f"host=h password={pw}")
    assert pw not in common_mod.redact_text(exotic)
    assert common_mod.dsn_secrets(f"host=h password='{pw} sp'") == [f"{pw} sp"]
    argv = ["python", "x.py", "--dsn", DSN_WITH_PASSWORD, "--chart-id", "c",
            f"--dsn={DSN_WITH_PASSWORD}"]
    out = common_mod.redact_argv(argv)
    assert pw not in " ".join(out)
    assert out[2] == "--dsn" and out[3] == common_mod.REDACTED


def test_parser_errors_redacted(capsys):
    """Early validation errors: argparse echoes the offending token — the
    step parser redacts it. Kills: a plain ArgumentParser."""
    with pytest.raises(SystemExit) as exc:
        build_mod.main(["--dsn", DSN_WITH_PASSWORD, "--chart-id", "c",
                        "--orb-deg", DSN_WITH_PASSWORD])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert DSN_PASSWORD not in err
    assert common_mod.REDACTED in err


def test_child_output_redacted_and_streamed(tmp_path, capsys):
    """A REAL child prints the credential in three forms on stdout and
    stderr; century_run._run forwards its output redacted AND streaming —
    proven by a handshake: the child prints READY, then waits for a file
    the parent's per-line hook creates on seeing READY, then prints GO. A
    buffered forwarder never creates the file in time and the child prints
    TIMEOUT instead. Kills: pass-through child output; buffering to exit."""
    flag = tmp_path / "go.flag"
    child = tmp_path / "child.py"
    child.write_text(
        "import os, sys, time\n"
        f"pw = {DSN_PASSWORD!r}\n"
        f"print('uri postgresql://u:' + pw + '@h/db', flush=True)\n"
        "print('READY', flush=True)\n"
        "deadline = time.time() + 10\n"
        f"while not os.path.exists({str(flag)!r}) and time.time() < deadline:\n"
        "    time.sleep(0.02)\n"
        f"print('GO' if os.path.exists({str(flag)!r}) else 'TIMEOUT', flush=True)\n"
        "print('kw host=h password=' + pw + ' dbname=d', file=sys.stderr, flush=True)\n"
        "print('PGPASSWORD=' + pw, file=sys.stderr, flush=True)\n"
        "sys.exit(7)\n")
    seen = []

    def on_line(line):
        seen.append(line)
        if line.strip() == "READY":
            flag.write_text("go\n")

    rc = century_mod._run([sys.executable, str(child)], on_line=on_line)
    assert rc == 7
    text = "".join(seen)
    assert DSN_PASSWORD not in text
    assert text.count(common_mod.REDACTED) >= 3
    assert "GO" in text and "TIMEOUT" not in text
    logged = capsys.readouterr().out
    assert DSN_PASSWORD not in logged  # the "+ argv" command line


def test_uncaught_exception_and_connection_failure_redacted(monkeypatch,
                                                            tmp_path, capsys):
    """A connection failure whose message carries the DSN, and any other
    uncaught exception, are reported through the guarded entry point with
    the credential scrubbed; a MemoryError is reported LOUDLY as exit 3.
    Kills: the interpreter's raw traceback."""
    _stub_freshness(monkeypatch)
    manifest_uri, _, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 1)
                                    for b in enum_mod.PERSISTED_BODIES})

    def boom(dsn, step, autocommit=True):
        raise RuntimeError(f"connection failed: could not connect to {dsn}")

    monkeypatch.setattr(build_mod, "connect", boom)
    argv = _build_argv(manifest_uri)
    argv[argv.index("--dsn") + 1] = DSN_WITH_PASSWORD
    rc = common_mod.run_main_guarded(lambda: build_mod.main(argv))
    err = capsys.readouterr().err
    assert rc == 1
    assert DSN_PASSWORD not in err
    assert "connection failed" in err and common_mod.REDACTED in err

    def oom():
        raise MemoryError()

    rc = common_mod.run_main_guarded(oom)
    assert rc == 3
    assert "MEMORY GUARD" in capsys.readouterr().err


def test_century_run_never_logs_dsn_password(monkeypatch, tmp_path, capsys):
    """Amendment 3 (SECURITY): the password-bearing DSN never reaches
    stdout/stderr — not in the logged command lines, not in the children's
    forwarded output (the fake children echo it in URI and libpq form), not
    in abort diagnostics, not in the chain report. Kills: unredacted argv
    echo; unredacted child-output forwarding; unredacted abort paths."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-a", "att-b")
    _stub_chain(monkeypatch)
    rc = century_mod.main(_driver_argv(tmp_path), gcs_client=_FakeGCSClient())
    captured = capsys.readouterr()
    assert rc == 0, captured.err
    assert DSN_PASSWORD not in captured.out
    assert DSN_PASSWORD not in captured.err
    assert "connecting with postgresql://builder:" + common_mod.REDACTED in captured.out
    assert "password=" + common_mod.REDACTED in captured.out
    # failure diagnostics too: abort a run mid-chain with the password DSN
    _stub_chain(monkeypatch, fail_on="Mars")
    rc = century_mod.main(_driver_argv(tmp_path), gcs_client=_FakeGCSClient())
    captured = capsys.readouterr()
    assert rc == 5
    assert DSN_PASSWORD not in captured.out + captured.err


# ── round-2 amendment 4: fresh, immutable attempt artifacts ────────────────────


def test_new_attempt_id_collision_resistant():
    """Two containers starting in the same second must not share a prefix:
    the id carries 96 random bits beyond the second stamp. Kills: a
    second-resolution id."""
    ids = {century_mod.new_attempt_id() for _ in range(200)}
    assert len(ids) == 200
    one = next(iter(ids))
    assert one.startswith("pravaha-a25-century-")
    stamp, rand = one[len("pravaha-a25-century-"):].split("-")
    datetime.strptime(stamp, "%Y%m%dT%H%M%SZ")
    assert len(rand) == 24 and int(rand, 16) >= 0


def test_century_run_refuses_existing_attempt_dir(monkeypatch, tmp_path, capsys):
    """Exclusive local staging: a pre-existing attempt directory (empty or
    not) refuses the run. Kills: exist_ok=True / the non-empty-only check."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-fixed")
    called = _no_subprocess(monkeypatch)
    (tmp_path / "century" / "att-fixed").mkdir(parents=True)  # empty
    rc = century_mod.main(_driver_argv(tmp_path), gcs_client=_FakeGCSClient())
    assert rc == 3
    assert "retry safety" in capsys.readouterr().err
    assert not called


def test_uploads_are_create_only(monkeypatch, tmp_path):
    """Every remote object is created with if_generation_match=0. Kills:
    dropping the precondition."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-c")
    _stub_chain(monkeypatch)
    client = _FakeGCSClient()
    assert century_mod.main(_driver_argv(tmp_path), gcs_client=client) == 0
    assert client.upload_calls
    assert all(c["if_generation_match"] == 0 for c in client.upload_calls)
    # 8 objects + 8 receipts + 8 sidecars + coverage + manifest
    assert len(client.upload_calls) == 8 * 3 + 2


def test_second_attempt_cannot_overwrite_finalized_objects(monkeypatch,
                                                           tmp_path, capsys):
    """The reviewer's counterexample: a second attempt landing on the same
    prefix used to overwrite Sun and then fail at Mars, invalidating the
    first finalized manifest. Now the second attempt's FIRST upload hits the
    create-only precondition and refuses (exit 3); every object the first
    manifest references is byte-identical afterwards and still verifies.
    Kills: dropping the precondition / non-fresh prefixes."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-same", "att-same")
    client = _FakeGCSClient()
    _stub_chain(monkeypatch)
    assert century_mod.main(_driver_argv(tmp_path, workdir=tmp_path / "w1"),
                            gcs_client=client) == 0
    before = dict(client.store)
    manifest = json.loads(before["test-bucket/kala_gochara/482012f1/4.1/"
                                 "att-same/input_manifest.json"])
    _stub_chain(monkeypatch, fail_on="Mars",
                episodes_by_body={"Sun": _body_episodes("Sun", 5)})  # different Sun
    rc = century_mod.main(_driver_argv(tmp_path, workdir=tmp_path / "w2"),
                          gcs_client=client)
    assert rc == 3
    assert "attempt collision" in capsys.readouterr().err
    assert client.store == before
    sun = manifest["objects"]["Sun"]
    data = client.store[sun["uri"][len("gs://"):]]
    assert "sha256:" + hashlib.sha256(data).hexdigest() == sun["sha256"]
    assert len(data) == sun["bytes"]


def test_century_run_fresh_prefix_per_attempt_and_provenance(monkeypatch, tmp_path):
    """Each attempt stages under its OWN attempt id — local dir and GCS
    prefix — with object, receipt, dedupe-provenance sidecar and finalized
    manifest per attempt; local objects are freed after the verified upload.
    Kills: a shared prefix; dropping the receipt/sidecar uploads."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    client = _FakeGCSClient()
    _stub_chain(monkeypatch)
    _fixed_attempts(monkeypatch, "att-1", "att-2")
    assert century_mod.main(_driver_argv(tmp_path), gcs_client=client) == 0
    assert century_mod.main(_driver_argv(tmp_path), gcs_client=client) == 0
    keys = set(client.store)
    for att in ("att-1", "att-2"):
        assert any(f"{att}/episodes/Sun.ndjson" in k for k in keys)
        assert any(k.endswith(f"{att}/episodes/Sun.receipt.json") for k in keys)
        assert any(k.endswith(f"{att}/episodes/Sun.ndjson.dropped_refs.json")
                   for k in keys)
        assert any(k.endswith(f"{att}/input_manifest.json") for k in keys)
    run_dir = tmp_path / "century" / "att-1"
    assert not list((run_dir / "episodes").glob("*.ndjson"))
    assert not list((run_dir / "episodes").glob("*.dropped_refs.json"))


def test_century_run_failed_attempt_finalizes_nothing(monkeypatch, tmp_path):
    """Amendment 5 + §N.8: a body failing mid-chain leaves NO finalized
    manifest and NEVER reaches the candidate build. Kills: writing the
    manifest after a failed body / invoking the build on partial input."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-f")
    record = _stub_chain(monkeypatch, fail_on="Mars")
    client = _FakeGCSClient()
    rc = century_mod.main(_driver_argv(tmp_path), gcs_client=client)
    assert rc == 5
    assert not (tmp_path / "century" / "att-f" / "input_manifest.json").exists()
    assert not any(k.endswith("input_manifest.json") for k in client.store)
    invoked = [Path(a[1]).name for a in record]
    assert "step06_candidate_build.py" not in invoked
    assert "step06b_windows_projection.py" not in invoked


# ── round-2 amendment 2 (driver side): receipts bound, provenance uniform ─────


def test_century_run_refuses_body_without_receipt(monkeypatch, tmp_path, capsys):
    """An exit code is not a completion signal: step06 exiting 0 without
    writing its completion receipt aborts the chain before any manifest.
    Kills: trusting the exit code."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-r")
    record = _stub_chain(monkeypatch, omit_receipt_for=("Venus",))
    client = _FakeGCSClient()
    rc = century_mod.main(_driver_argv(tmp_path), gcs_client=client)
    assert rc == 3
    assert "completion receipt" in capsys.readouterr().err
    assert not any(k.endswith("input_manifest.json") for k in client.store)
    assert "step06_candidate_build.py" not in [Path(a[1]).name for a in record]


def test_century_run_refuses_mixed_source_bodies(monkeypatch, tmp_path, capsys):
    """Eight bodies enumerated against different source states are a
    mixed-source run: the driver binds the first body's snapshot and
    refuses a later body whose receipt disagrees. Kills: not comparing
    provenance across bodies."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-m")

    def snapshot_for(body):
        if body == "Jupiter":
            return {**SNAPSHOT, "resolution_facts_sha256": "sha256:" + "f" * 64}
        return SNAPSHOT

    record = _stub_chain(monkeypatch, snapshot_for=snapshot_for)
    client = _FakeGCSClient()
    rc = century_mod.main(_driver_argv(tmp_path), gcs_client=client)
    assert rc == 3
    assert "mixed-source" in capsys.readouterr().err
    assert not any(k.endswith("input_manifest.json") for k in client.store)
    assert "step06_candidate_build.py" not in [Path(a[1]).name for a in record]


def test_century_run_manifest_binds_receipts_and_provenance(monkeypatch, tmp_path):
    """End-to-end binding: the manifest the driver finalizes and uploads
    must pass the BUILD's own static + receipt verification through the
    fake bucket (the build consumes exactly what the driver wrote), and
    carry every binding round-2 amendment 2 names. Kills: any driver/build
    schema drift; dropping a binding on either side."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-e2e")
    _stub_chain(monkeypatch, no_sidecar_for=("Ketu",))
    client = _FakeGCSClient()
    assert century_mod.main(_driver_argv(tmp_path), gcs_client=client) == 0
    uri = "gs://test-bucket/kala_gochara/482012f1/4.1/att-e2e/input_manifest.json"
    manifest = build_mod.load_input_manifest(uri, gcs_client=client)
    assert manifest["version"] == build_mod.MANIFEST_VERSION
    assert manifest["attempt_id"] == "att-e2e"
    for key in build_mod.PROVENANCE_KEYS:
        assert manifest[key] not in (None, {}, "")
    assert manifest["source_snapshot"] == SNAPSHOT
    assert manifest["ephemeris"]["files"] == EPHEMERIS["files"]
    assert manifest["configuration"]["orb_deg"] == 5.0
    assert manifest["convention_id"] == CONVENTION_ID
    assert manifest["coverage"]["partitions_by_body"] == {
        b: 1 for b in enum_mod.PERSISTED_BODIES}
    for body in enum_mod.PERSISTED_BODIES:
        entry = manifest["objects"][body]
        assert entry["receipt"]["uri"].startswith("gs://") and entry["receipt"]["sha256"]
        assert entry["uri"].endswith(f"att-e2e/episodes/{body}.ndjson")
        assert entry["episodes_after_dedupe"] == entry["lines"] == 2
    assert manifest["objects"]["Ketu"]["dropped_refs"] is None
    assert manifest["objects"]["Sun"]["dropped_refs"]["uri"].endswith(
        "Sun.ndjson.dropped_refs.json")
    uris = build_mod.verify_manifest_static(
        manifest, chart_id=CANONICAL_CHART, generation="4.1",
        horizon_text=CENTURY_HORIZON_TEXT,
        expected_bodies=enum_mod.PERSISTED_BODIES, orb_deg=5.0,
        convention_id=CONVENTION_ID, method_version=METHOD_VERSION)
    receipts = build_mod.verify_manifest_receipts(
        manifest, chart_id=CANONICAL_CHART, generation="4.1",
        horizon_text=CENTURY_HORIZON_TEXT,
        expected_bodies=enum_mod.PERSISTED_BODIES, gcs_client=client)
    assert set(receipts) == set(enum_mod.PERSISTED_BODIES)
    streams = [build_mod.EpisodeObjectStream(u, gcs_client=client, expected_body=b)
               for b, u in zip(enum_mod.PERSISTED_BODIES, uris)]
    assert sum(1 for _ in build_mod.iter_episodes_merged(streams)) == 16
    build_mod.verify_object_stats(streams, manifest, enum_mod.PERSISTED_BODIES)


# ── round-2 amendment 2 (build side): completeness and provenance ─────────────


def test_build_green_only_with_verified_manifest(monkeypatch, tmp_path, capsys):
    """Positive control: a fully finalized, verified v1.1 manifest builds
    and commits — the earned GREEN carries the verification record."""
    conn = _RecConn(keep_rows=True)
    _patched_build_conn(monkeypatch, conn)
    eps = {b: _body_episodes(b, 3) for b in enum_mod.PERSISTED_BODIES}
    manifest_uri, _, _ = _write_manifest_tree(tmp_path, episodes_by_body=eps)
    rc = build_mod.main(_build_argv(manifest_uri))
    out = capsys.readouterr()
    assert rc == 0, out.err
    assert conn.committed
    assert conn.inserted == 24 + 8  # 8 bodies × 3 episodes + 8 coverage rows
    report = json.loads(out.out)
    assert report["input_generation_vector"]["input_manifest_provenance"][
        "source_snapshot"] == SNAPSHOT


def test_build_reads_gs_objects_via_real_streamed_path(monkeypatch, tmp_path):
    """The gs:// consumption path is the real streamed one: manifest,
    coverage, receipts, sidecars and objects all live in the fake bucket
    and are read through blob.open — positive gs control."""
    conn = _RecConn(keep_rows=True)
    _patched_build_conn(monkeypatch, conn)
    client = _FakeGCSClient()
    eps = {b: _body_episodes(b, 2) for b in enum_mod.PERSISTED_BODIES}
    manifest_uri, _, _ = _write_manifest_tree(tmp_path, episodes_by_body=eps,
                                              gcs_client=client)
    assert manifest_uri.startswith("gs://")
    rc = build_mod.main(_build_argv(manifest_uri), gcs_client=client)
    assert rc == 0
    assert conn.inserted == 16 + 8


def test_build_refuses_missing_source_snapshot(monkeypatch, tmp_path, capsys):
    """Reviewer counterexample: removing the input snapshot still earned
    GREEN. Now an unbound source snapshot refuses statically."""
    def mutate(m):
        del m["source_snapshot"]
    _, err = _refused(monkeypatch, tmp_path, capsys,
             episodes_by_body={b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES},
             mutate_manifest=mutate)


def test_build_refuses_configuration_orb_mismatch(monkeypatch, tmp_path, capsys):
    """Reviewer counterexample: orb 999 in the manifest while building with
    5.0 earned GREEN. Now configuration is bound to the build's own orb."""
    def mutate(m):
        m["configuration"]["orb_deg"] = 999.0
    _, err = _refused(monkeypatch, tmp_path, capsys,
             episodes_by_body={b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES},
             mutate_manifest=mutate)
    assert "orb_deg=999.0" in err


def test_build_refuses_empty_object_without_completion_receipt(monkeypatch, tmp_path, capsys):
    """Reviewer counterexample: empty bodies with consistent checksums
    earned GREEN. An empty object needs a verified enumeration explanation
    — its bound completion receipt; without one it refuses."""
    def mutate(m):
        del m["objects"]["Sun"]["receipt"]
    _, err = _refused(monkeypatch, tmp_path, capsys, episodes_by_body={},
             mutate_manifest=mutate)
    assert "completion receipt" in err


def test_build_refuses_receipt_object_count_disagreement(monkeypatch, tmp_path, capsys):
    """A receipt attesting 3 episodes bound to an object holding 0 lines
    (checksums consistent with the object) refuses: the receipt does not
    describe this object."""
    def mutate_receipt(body, r):
        if body == "Mercury":
            r["episodes"]["lines"] = r["episodes"]["lines_written"] = 3
            r["episodes"]["episodes_after_dedupe"] = 3
    _, err = _refused(monkeypatch, tmp_path, capsys, episodes_by_body={},
             mutate_receipt=mutate_receipt)


def test_build_refuses_empty_coverage(monkeypatch, tmp_path, capsys):
    """Reviewer counterexample: empty coverage earned GREEN."""
    _, err = _refused(monkeypatch, tmp_path, capsys,
             episodes_by_body={b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES},
             coverage_rows=[])


def test_build_refuses_shortened_coverage_horizon(monkeypatch, tmp_path, capsys):
    """Reviewer counterexample: a shortened completed horizon earned GREEN.
    Every partition must be completed over THIS build's horizon."""
    rows = [_coverage_row(b, CENTURY_HORIZON_TEXT) for b in enum_mod.PERSISTED_BODIES]
    rows[3]["completed_horizon"] = "[1984-02-05T00:00:00+00:00,2080-01-01T00:00:00+00:00)"
    _, err = _refused(monkeypatch, tmp_path, capsys,
             episodes_by_body={b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES},
             coverage_rows=rows)
    assert "completed_horizon" in err


def test_build_refuses_foreign_body_in_object(monkeypatch, tmp_path, capsys):
    """Reviewer counterexample: a Sun object containing Mercury contacts
    earned GREEN. Actual body identity is verified line by line."""
    eps = {b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES}
    eps["Sun"] = eps["Sun"] + [_episode("Mercury", "conjunction", BASE, "X")]
    conn, err = _refused(monkeypatch, tmp_path, capsys, episodes_by_body=eps)
    assert conn.rolled_back
    assert "body identity" in err


def test_build_refuses_missing_dedupe_sidecar(monkeypatch, tmp_path, capsys):
    """Reviewer counterexample: missing dedupe sidecars went unchecked. A
    receipt attesting a sidecar with no manifest binding, and a bound
    sidecar that cannot be read, both refuse."""
    def unbind(m):
        m["objects"]["Venus"]["dropped_refs"] = None
    _, err = _refused(monkeypatch, tmp_path, capsys,
             episodes_by_body={b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES},
             mutate_manifest=unbind)
    assert "provenance lost" in err
    client = _FakeGCSClient()
    conn = _RecConn()
    _patched_build_conn(monkeypatch, conn)
    manifest_uri, manifest, _ = _write_manifest_tree(
        tmp_path / "gs", episodes_by_body={b: _body_episodes(b, 1)
                                           for b in enum_mod.PERSISTED_BODIES},
        gcs_client=client)
    client.store.pop(manifest["objects"]["Mars"]["dropped_refs"]["uri"][len("gs://"):])
    rc = build_mod.main(_build_argv(manifest_uri), gcs_client=client)
    assert rc == 3 and not conn.committed


def test_build_refuses_mixed_source_receipts(monkeypatch, tmp_path, capsys):
    """One body's receipt carries a different source snapshot than the
    manifest's run-level provenance: mixed-source input refuses."""
    def mutate_receipt(body, r):
        if body == "Rahu":
            r["source_snapshot"] = {**SNAPSHOT, "resonance_map_sha256": "sha256:" + "e" * 64}
    _, err = _refused(monkeypatch, tmp_path, capsys,
             episodes_by_body={b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES},
             mutate_receipt=mutate_receipt)
    assert "mixed-source" in err


def test_build_refuses_missing_ephemeris_checksums(monkeypatch, tmp_path, capsys):
    def mutate(m):
        m["ephemeris"]["files"] = {}
    _, err = _refused(monkeypatch, tmp_path, capsys,
             episodes_by_body={b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES},
             mutate_manifest=mutate)
    assert "ephemeris" in err


def test_build_refuses_old_manifest_schema(monkeypatch, tmp_path, capsys):
    """A v1.0 manifest (the shape the round-2 review rejected) binds less
    than this build verifies and is refused outright."""
    def mutate(m):
        m["version"] = "1.0"
    _, err = _refused(monkeypatch, tmp_path, capsys,
             episodes_by_body={b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES},
             mutate_manifest=mutate)


def test_build_refuses_omitted_body(monkeypatch, tmp_path, capsys):
    """A manifest naming eight bodies whose Sun object is MISSING fails the
    build — never GREEN."""
    _, err = _refused(monkeypatch, tmp_path, capsys,
             episodes_by_body={b: _body_episodes(b, 2) for b in enum_mod.PERSISTED_BODIES},
             omit_files=("Sun",))


def test_build_refuses_truncated_stream(monkeypatch, tmp_path, capsys):
    """A CLEAN JSON-prefix truncation (one line short, every remaining line
    valid) fails against the line-count binding — the round-1 F2 repro."""
    conn = _RecConn()
    _patched_build_conn(monkeypatch, conn)
    manifest_uri, _, files = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 4)
                                    for b in enum_mod.PERSISTED_BODIES})
    lines = files["Ketu"].read_text().splitlines(keepends=True)
    files["Ketu"].write_text("".join(lines[:-1]))  # clean truncation
    rc = build_mod.main(_build_argv(manifest_uri))
    assert rc == 3
    assert not conn.committed


def test_build_refuses_checksum_mismatch(monkeypatch, tmp_path):
    """A same-length, same-line-count alteration fails against the sha256
    binding."""
    conn = _RecConn()
    _patched_build_conn(monkeypatch, conn)
    manifest_uri, _, files = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 2)
                                    for b in enum_mod.PERSISTED_BODIES})
    text = files["Venus"].read_text()
    files["Venus"].write_text(text.replace("conjunction", "donjunction", 1))
    rc = build_mod.main(_build_argv(manifest_uri))
    assert rc == 3
    assert not conn.committed


def test_build_refuses_mixed_run(monkeypatch, tmp_path):
    """One object stamped with another attempt's run_id fails BEFORE the DB
    is even connected."""
    def mutate(m):
        m["objects"]["Rahu"]["run_id"] = "run-older-attempt"
    manifest_uri, _, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 1)
                                    for b in enum_mod.PERSISTED_BODIES},
        mutate_manifest=mutate)
    connect_called = []
    monkeypatch.setattr(build_mod, "connect",
                        lambda *a, **kw: connect_called.append(a) or _RecConn())
    rc = build_mod.main(_build_argv(manifest_uri))
    assert rc == 3
    assert not connect_called


def test_build_refuses_unfinalized_manifest(monkeypatch, tmp_path, capsys):
    manifest_uri, _, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={}, finalized=False)
    connect_called = []
    monkeypatch.setattr(build_mod, "connect",
                        lambda *a, **kw: connect_called.append(a) or _RecConn())
    rc = build_mod.main(_build_argv(manifest_uri))
    assert rc == 3
    assert "FINALIZED" in capsys.readouterr().err
    assert not connect_called


def test_build_refuses_unreadable_object(monkeypatch, tmp_path):
    """A GCS object that cannot be opened fails the build, never GREEN —
    the REAL gs:// code path through the injected transport."""
    conn = _RecConn()
    _patched_build_conn(monkeypatch, conn)
    client = _FakeGCSClient()
    manifest_uri, manifest, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 1)
                                    for b in enum_mod.PERSISTED_BODIES},
        gcs_client=client)
    client.store.pop(manifest["objects"]["Saturn"]["uri"][len("gs://"):])
    rc = build_mod.main(_build_argv(manifest_uri), gcs_client=client)
    assert rc == 3
    assert not conn.committed


def test_coverage_sorted_by_partition_key(monkeypatch, tmp_path):
    """Coverage insert order is by partition_key — the monolithic
    build_coverage_rows order — never the driver's body order."""
    conn = _RecConn(keep_rows=True)
    _patched_build_conn(monkeypatch, conn)
    manifest_uri, _, _ = _write_manifest_tree(
        tmp_path, episodes_by_body={b: _body_episodes(b, 1)
                                    for b in enum_mod.PERSISTED_BODIES},
        coverage_order=list(reversed(enum_mod.PERSISTED_BODIES)))
    rc = build_mod.main(_build_argv(manifest_uri))
    assert rc == 0
    cov_rows = [r for r in conn.rows if len(r) > 3 and r[3] in
                {f"{b.lower()}:karaka" for b in enum_mod.PERSISTED_BODIES}]
    keys = [r[3] for r in cov_rows]
    assert keys == sorted(keys)


# ── round-2 amendment 6: exception classification ──────────────────────────────


def test_unique_violation_routes_to_exit_5(monkeypatch, tmp_path, capsys):
    """psycopg raises the SQLSTATE subclass (UniqueViolation), which the old
    exact-class-name check missed (exit 1 instead of the documented 5). Now
    psycopg's IntegrityError family and any SQLSTATE 23xxx route to 5; a
    non-integrity error still propagates. Kills: the class-name compare."""
    psycopg = pytest.importorskip("psycopg")
    eps = {b: _body_episodes(b, 1) for b in enum_mod.PERSISTED_BODIES}
    manifest_uri, _, _ = _write_manifest_tree(tmp_path, episodes_by_body=eps)

    class _DuckIntegrity(Exception):
        sqlstate = "23505"

    for exc in (psycopg.errors.UniqueViolation("duplicate key value"),
                psycopg.IntegrityError("integrity"),
                _DuckIntegrity("duck 23505")):
        conn = _RecConn(raise_on_insert=exc)
        _patched_build_conn(monkeypatch, conn)
        rc = build_mod.main(_build_argv(manifest_uri))
        err = capsys.readouterr().err
        assert rc == 5, (type(exc).__name__, err)
        assert conn.rolled_back and not conn.committed
        assert "ADK-0020" in err
    conn = _RecConn(raise_on_insert=RuntimeError("not an integrity error"))
    _patched_build_conn(monkeypatch, conn)
    with pytest.raises(RuntimeError):
        build_mod.main(_build_argv(manifest_uri))
    assert conn.rolled_back
    assert build_mod.is_integrity_error(psycopg.errors.ForeignKeyViolation("fk"))
    assert not build_mod.is_integrity_error(ValueError("x"))


# ── round-2 amendment 1: bounded memory across the complete chain ─────────────


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
    """The streamed build's peak memory is bounded by the batch size, NOT
    the episode count. Kills: materializing the episode/row/id list."""
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
        make_tree(2500, tmp_path / "n1"), _RecConn(), 8 * 2500)
    peak2 = _measure_streamed_build_peak(
        make_tree(5000, tmp_path / "n2"), _RecConn(), 8 * 5000)
    bound = 24 * 1024 * 1024
    assert peak1 < bound and peak2 < bound
    assert peak2 < peak1 * 1.75, (
        f"peak grew {peak1}->{peak2} with 2x input — input-scale "
        "materialization is present")


class _InstantStreamConn:
    """A stream connection whose named cursor yields (class, t_exact) rows
    lazily; fetchall is a trap."""

    def __init__(self, n_by_class: dict[str, int]):
        self.n_by_class = n_by_class
        self.cursor_names = []

    def cursor(self, name=None):
        conn = self
        conn.cursor_names.append(name)

        class _Cur:
            itersize = 0

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def execute(self, sql, params=None):
                assert "ORDER BY m.event_class" in sql
                assert "t_exact IS NOT NULL" in sql

            def __iter__(self):
                for cls in sorted(conn.n_by_class):
                    for i in range(conn.n_by_class[cls]):
                        yield (cls, BASE + timedelta(hours=i))

            def fetchall(self):
                raise AssertionError("fetchall materializes the instants")

        return _Cur()


def _stub_class_context_seams(monkeypatch, fires_every=1000):
    class _T:
        pass

    monkeypatch.setattr(s6a_mod, "fetch_resonance_targets",
                        lambda conn, chart_id, cls: [_T()] if cls != "omitted" else [])
    monkeypatch.setattr(s6a_mod.enrichment, "enrich_targets",
                        lambda conn, targets: targets)
    monkeypatch.setattr(s6a_mod.valence, "is_adverse",
                        lambda conn, cls: (False, "gain"))
    counter = {"n": 0}

    def compute_permission(swe, conn, cid, cls, targets, t_jd, dasha_periods=None):
        counter["n"] += 1
        active = ["vimshottari"] if counter["n"] % fires_every == 0 else []
        return 0.0, {"systems_active": active}

    monkeypatch.setattr(s6a_mod.perm, "compute_permission", compute_permission)
    return counter


def _class_context_peak(monkeypatch, n_by_class):
    _stub_class_context_seams(monkeypatch)
    conn = _InstantStreamConn(n_by_class)
    tracemalloc.start()
    contexts, omitted, seen = s6a_mod.stream_class_contexts(
        None, None, conn, CANONICAL_CHART, "4.1", [])
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak, contexts, omitted, seen, conn


def test_class_context_streams_instants_bounded(monkeypatch):
    """Class-context preparation no longer retains the class instants:
    growing the instant count 20k -> 40k -> 80k leaves the peak flat.
    Kills: fetchall / per-class instant lists."""
    peaks = []
    for n in (20_000, 40_000, 80_000):
        peak, contexts, omitted, seen, conn = _class_context_peak(
            monkeypatch, {"marriage": n, "career": n // 4, "omitted": 10})
        peaks.append(peak)
        assert contexts["marriage"]["sampled_instants"] == n
        assert contexts["career"]["sampled_instants"] == n // 4
        assert omitted == [{"event_class": "omitted",
                            "reason": omitted[0]["reason"],
                            "candidate_instants": 10}]
        assert seen == 3
        assert conn.cursor_names == [s6a_mod.CLASS_INSTANTS_CURSOR]
    assert peaks[2] < 512 * 1024, f"peak {peaks[2]} bytes is not bounded"
    assert peaks[2] < peaks[0] * 1.25, (
        f"peak grew {peaks[0]}->{peaks[2]} with 4x instants — instants are retained")


def test_class_context_never_fetchall():
    """The instant read is a NAMED server-side cursor consumed class by
    class; the null-exact count is an SQL COUNT (fetchone). Kills: the
    fetchall shape."""
    conn = _InstantStreamConn({"a": 3})
    groups = [(cls, list(it)) for cls, it in
              s6a_mod.iter_class_contact_instants(conn, CANONICAL_CHART, "4.1")]
    assert [(c, len(g)) for c, g in groups] == [("a", 3)]
    assert conn.cursor_names == [s6a_mod.CLASS_INSTANTS_CURSOR]

    class _CountConn:
        def execute(self, sql, params=None):
            assert "count(*)" in sql and "t_exact IS NULL" in sql
            return self

        def fetchone(self):
            return (2,)

        def fetchall(self):
            raise AssertionError("fetchall")

    assert s6a_mod.count_null_exact_classes(_CountConn(), CANONICAL_CHART, "4.1") == 2
    src = Path(s6a_mod.__file__).read_text()
    main_src = src[src.index("def main("):]
    assert ".fetchall(" not in main_src
    assert "stream_class_contexts(" in main_src


# — projection: the component sweep —

H0 = datetime(2026, 1, 1, tzinfo=UTC)
H1 = datetime(2027, 1, 1, tzinfo=UTC)
HORIZON_JD = (proj_mod.jd_of(H0), proj_mod.jd_of(H1))


def _contact(i: int, t_in: datetime, t_exact: datetime | None, t_out: datetime,
             ref: str = "Venus", body: str = "Saturn") -> dict:
    d = {"contact_id": f"c{i:05d}", "body": body, "relation": "conjunction",
         "target_type": "karaka", "target_ref": ref, "orb_max_deg": 5.0,
         "completeness_state": "applied", "_primitive": "degree_contact",
         "_t_in_jd": proj_mod.jd_of(t_in),
         "_t_exact_jd": proj_mod.jd_of(t_exact) if t_exact else None,
         "_t_out_jd": proj_mod.jd_of(t_out)}
    d["_span_lo"], d["_span_hi"] = proj_mod.contact_span(d)
    return d


def _random_contacts(seed: int, *, density: float = 1.0) -> list[dict]:
    rng = random.Random(seed)
    contacts = []
    i = 0
    t = H0 - timedelta(days=5)   # the first one is truncated across horizon start
    while t < H1 + timedelta(days=3):
        span = timedelta(days=rng.uniform(2, 25))
        ex = t + span * rng.uniform(0.2, 0.8)
        contacts.append(_contact(i, t, None if rng.random() < 0.05 else ex,
                                 t + span, ref=rng.choice(["Venus", "Mars"])))
        i += 1
        t += timedelta(days=rng.uniform(0.5, 20) / density)
    return sorted(contacts, key=lambda c: (c["_span_lo"], c["contact_id"]))


class _UuidCounter:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return f"u{self.n}"


def _sweep(class_ctx, contacts_iter, fetch_in, gate):
    collected = []

    def write_rows(rows):
        collected.extend(rows)
        return len(rows), 0

    rep, tiers, nw, ns = proj_mod.project_class_streamed(
        class_ctx, contacts_iter, HORIZON_JD, gate, write_rows, fetch_in)
    return collected, rep, tiers, nw


@pytest.mark.parametrize("seed,density", [(7, 1.0), (11, 1.0), (23, 3.0)])
def test_projection_sweep_equivalent_to_whole_class(monkeypatch, seed, density):
    """The component sweep IS the pinned whole-class computation: on random
    contact sets (overlapping spans, a horizon-truncated contact, no-exact
    contacts, dense overlap at density 3) it yields byte-identical rows in
    the same order and the same summed report. Kills: any sweep step that
    is not the whole-class series/component/peak computation (window
    eviction too early, missing breakpoints, refinement over the wrong
    contacts, a non-first era peak, …)."""
    contacts = _random_contacts(seed, density=density)
    ctx = proj_mod.ClassContext("marriage", [0.9, 0.5], {"vimshottari": True},
                                weight_by_target_ref={"Venus": 0.9, "Mars": 0.5})
    gate = proj_mod.make_quality_gate_for_date([], {})
    counter = _UuidCounter()
    monkeypatch.setattr(proj_mod._uuid, "uuid4", counter)
    rows_whole, rep_whole = proj_mod.project_class_windows(
        ctx, contacts, HORIZON_JD, gate)
    counter.n = 0

    def fetch_in(lo, hi):
        return [c for c in contacts if c["_span_lo"] <= hi and c["_span_hi"] >= lo]

    rows_sweep, rep_sweep, tiers, nw = _sweep(ctx, iter(contacts), fetch_in, gate)
    assert rows_sweep == rows_whole
    assert nw == len(rows_whole) > 0
    assert rep_whole["components"] >= (4 if density == 1.0 else 1)
    for k in proj_mod._SUMMED_REPORT_KEYS:
        assert rep_sweep[k] == rep_whole.get(k, 0), k
    assert sum(tiers.values()) == len(rows_whole)
    assert rep_sweep["era_raw_intensity_sum"] == pytest.approx(
        sum(r["raw_intensity"] for r in rows_whole if r["resolution"] == "era"))
    assert rep_sweep["contact_window_peak"] < len(contacts)


def _disjoint_contacts(n: int, spacing_days: float = 10.0, span_days: float = 2.0):
    for i in range(n):
        t_in = H0 + timedelta(days=1 + i * spacing_days)
        yield _contact(i, t_in, t_in + timedelta(days=span_days / 2),
                       t_in + timedelta(days=span_days))


def _disjoint_fetch(n: int, spacing_days: float = 10.0, span_days: float = 2.0):
    def fetch_in(lo, hi):
        first = max(0, int((lo - HORIZON_JD[0] - 1 - span_days) // spacing_days) - 1)
        last = min(n, int((hi - HORIZON_JD[0]) // spacing_days) + 2)
        return [c for c in (
            _contact(i, H0 + timedelta(days=1 + i * spacing_days),
                     H0 + timedelta(days=1 + i * spacing_days + span_days / 2),
                     H0 + timedelta(days=1 + i * spacing_days + span_days))
            for i in range(first, last))
            if c["_span_lo"] <= hi and c["_span_hi"] >= lo]
    return fetch_in


def _sweep_peak(ctx, gate, contacts_iter, fetch_in, horizon):
    def write_rows(rows):
        return len(rows), 0

    tracemalloc.start()
    rep, tiers, nw, ns = proj_mod.project_class_streamed(
        ctx, contacts_iter, horizon, gate, write_rows, fetch_in)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak, rep, nw


# a fixed 40-year evaluation horizon for the memory probes: like the century's,
# it does not grow with the contact count (the per-date quality-gate cache and
# the lazily generated grid are horizon-sized constants, not input-sized)
PROBE_HORIZON_JD = (HORIZON_JD[0], HORIZON_JD[0] + 40 * 365.25)


def test_projection_sweep_memory_bounded_disjoint_contacts():
    """Growing synthetic inputs: N disjoint contacts (each its own
    component) for N = 300 / 600 / 1200 leave the sweep's peak retained
    memory flat — the class is never held. Kills: retaining the class's
    contacts or its rows."""
    ctx = proj_mod.ClassContext("marriage", [0.9], {"vimshottari": True},
                                weight_by_target_ref={"Venus": 0.9})
    gate = proj_mod.make_quality_gate_for_date([], {})
    peaks = {}
    for n in (300, 600, 1200):
        gate = proj_mod.make_quality_gate_for_date([], {})  # fresh per-date cache
        peak, rep, nw = _sweep_peak(ctx, gate, _disjoint_contacts(n),
                                    _disjoint_fetch(n), PROBE_HORIZON_JD)
        peaks[n] = peak
        assert rep["components"] == n and nw >= n
        assert rep["contact_window_peak"] <= 2
    assert peaks[1200] < 16 * 1024 * 1024, f"peak {peaks[1200]} bytes is not bounded"
    assert peaks[1200] < peaks[300] * 1.2, (
        f"peak grew {peaks[300]}->{peaks[1200]} with 4x contacts — the class "
        "is retained")


def test_projection_sweep_memory_disproportionate_dense_class():
    """One disproportionately large, continuously-active class (spans of 10
    days every 2 days: every contact overlaps the next, one component
    across the horizon). Retained contacts stay at the overlap depth (≈ 6)
    regardless of N; the only growth is the component's compact series —
    the STATED residual, asserted here at < 400 bytes per contact (vs the
    ~700-byte contact dicts + per-class row lists the rejected shape kept)
    and inherent to the pinned P90 admission, which needs the run's whole
    value distribution; the driver's memory guard covers the worst case."""
    ctx = proj_mod.ClassContext("marriage", [0.9], {"vimshottari": True},
                                weight_by_target_ref={"Venus": 0.9})
    gate = proj_mod.make_quality_gate_for_date([], {})
    results = {}
    for n in (400, 1600):
        gate = proj_mod.make_quality_gate_for_date([], {})  # fresh per-date cache
        peak, rep, nw = _sweep_peak(
            ctx, gate, _disjoint_contacts(n, spacing_days=2.0, span_days=10.0),
            _disjoint_fetch(n, spacing_days=2.0, span_days=10.0),
            PROBE_HORIZON_JD)
        results[n] = (peak, rep)
        assert rep["components"] == 1
        assert rep["contact_window_peak"] <= 7
        assert rep["longest_component_points"] >= n  # one run across the whole class
    slope = (results[1600][0] - results[400][0]) / 1200
    assert slope < 400, f"{slope:.0f} bytes per contact retained in the dense case"
    assert results[1600][0] < 16 * 1024 * 1024


def test_projection_iter_class_contacts_server_side():
    """Contacts stream through a NAMED server-side cursor scoped to the
    class's target pairs, ORDERED by span start. Kills: client-side
    fetchall; an unordered stream (the sweep needs span order)."""
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
    assert "ORDER BY LEAST(t_in, COALESCE(t_exact, t_in)), contact_id" in seen["sql"]
    assert got[0]["contact_id"] == "cid-1"
    assert got[0]["_span_lo"] == got[0]["_t_in_jd"]


def test_projection_main_streams_per_class():
    """main is wired to the sweep: SQL-counted class contacts, the streamed
    per-class projection with the pass-2 range fetch, no materializing
    read anywhere in the module. Kills: reverting main."""
    src = Path(proj_mod.__file__).read_text()
    main_src = src[src.index("def main("):]
    assert "def fetch_contacts(" not in src
    assert "fetch_contacts(" not in main_src
    assert "cls_contacts" not in main_src
    assert "count_class_contacts(" in main_src
    assert "project_class_streamed(" in main_src
    assert "fetch_class_contacts_intersecting(" in main_src
    assert "iter_era_rows(" in main_src
    assert "era_rows.extend" not in main_src


def test_delta_report_streams_era_rows_from_iterable():
    """The delta report's per-window section consumes an era-row iterable
    once (a generator — never a retained list) and the per-class mean comes
    from the class report's scalar sum."""
    rep = {"event_class": "marriage", "promise": 0.9, "promise_target_count": 1,
           "permission": 0.25, "permission_systems_active": ["vimshottari"],
           "tara_modifier": 1.0, "tara_skip_reason": "x", "w30_modifier": 1.0,
           "w30_skip_reason": "y", "class_valence": "mixed",
           "class_is_adverse": False, "context_source": "test", "components": 2,
           "peaks_admitted": 2, "peaks_retained": 2, "era_windows": 2,
           "month_windows": 2, "day_windows": 2, "quality_gates_fired": 0,
           "mean_quality_gates": 1.0, "era_raw_intensity_sum": 0.5}

    def era_rows():
        for d, raw in ((date(2026, 2, 1), 0.2), (date(2026, 8, 1), 0.3)):
            yield {"resolution": "era", "event_class": "marriage", "peak_date": d,
                   "raw_intensity": raw, "signed_intensity": raw, "valence": "gain"}

    text = "\n".join(proj_mod.iter_delta_report_lines(
        chart_id="c", generation="4.1", baseline="3.0", class_reports=[rep],
        era_rows=era_rows(), baseline_rows=[], flags={}, fingerprints=None,
        run_meta={}))
    assert "| 0.250000 | 0 | — | — |" in text   # mean raw 4.0 = 0.5 / 2 eras
    assert "2026-02-01" in text and "2026-08-01" in text


# — the memory guard —


def test_memory_guard_forwarded_to_every_child(monkeypatch, tmp_path):
    """Every child of the chain receives --memory-guard-bytes (default 14
    GiB; --memory-guard-gib overrides). Kills: dropping the forward."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-g1", "att-g2")
    record = _stub_chain(monkeypatch)
    assert century_mod.main(_driver_argv(tmp_path), gcs_client=_FakeGCSClient()) == 0
    assert len(record) == 8 + 3
    for argv in record:
        assert argv[argv.index("--memory-guard-bytes") + 1] == str(14 * (1 << 30))
    record = _stub_chain(monkeypatch)
    assert century_mod.main(_driver_argv(tmp_path, extra=("--memory-guard-gib", "2")),
                            gcs_client=_FakeGCSClient()) == 0
    for argv in record:
        assert argv[argv.index("--memory-guard-bytes") + 1] == str(2 * (1 << 30))


def test_memory_guard_exceeded_aborts_before_manifest(monkeypatch, tmp_path, capsys):
    """The driver measures the children's peak RSS after every step and
    refuses to continue past one that exceeded the guard — before any
    manifest is finalized or any later step runs. Kills: not measuring."""
    monkeypatch.setenv("PRAVAHA_CENTURY_RUN_AUTHORIZED", "1")
    _fixed_attempts(monkeypatch, "att-oom")
    record = _stub_chain(monkeypatch)
    guard = 2 * (1 << 30)
    monkeypatch.setattr(century_mod, "peak_rss_bytes",
                        lambda children=False: guard + 1)
    client = _FakeGCSClient()
    rc = century_mod.main(_driver_argv(tmp_path, extra=("--memory-guard-gib", "2")),
                          gcs_client=client)
    out = capsys.readouterr()
    assert rc == 3
    assert "memory guard" in out.err
    assert len(record) == 1  # Sun only; nothing after the exceeded step
    assert not any(k.endswith("input_manifest.json") for k in client.store)
    report = json.loads(out.out[out.out.index("{"):])
    assert report["steps"][0]["memory_guard"] == "EXCEEDED"
    assert report["steps"][0]["children_peak_rss_bytes"] == guard + 1


def test_apply_memory_guard_and_guarded_main(monkeypatch, capsys):
    """apply_memory_guard sets RLIMIT_AS to the requested bytes (recorded
    through a patched setrlimit); the step parser applies it from
    --memory-guard-bytes and discloses it; a platform refusal is reported
    honestly, never claimed applied."""
    import resource
    calls = []
    monkeypatch.setattr(resource, "getrlimit",
                        lambda which: (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    monkeypatch.setattr(resource, "setrlimit",
                        lambda which, limits: calls.append((which, limits)))
    disclosure = common_mod.apply_memory_guard(123456789)
    assert disclosure == {"applied": True, "limit_bytes": 123456789, "reason": None}
    assert calls == [(resource.RLIMIT_AS, (123456789, 123456789))]
    parser = common_mod.step_parser(6, "x")
    ns = parser.parse_args(["--dsn", LOCAL_DSN, "--memory-guard-bytes", "5000"])
    assert ns.memory_guard["applied"] is True and calls[-1][1] == (5000, 5000)
    assert common_mod.apply_memory_guard(0)["applied"] is False

    def refuses(which, limits):
        raise ValueError("not permitted")

    monkeypatch.setattr(resource, "setrlimit", refuses)
    d = common_mod.apply_memory_guard(10)
    assert d["applied"] is False and "not permitted" in d["reason"]


# ── round-2 amendment 5: real identity, dedupe and digest ─────────────────────


def _expected_contact_id(*, body, target_type, target_ref, relation, aspect_deg,
                         t_exact, t_in, target_fact_id=None,
                         chart_id=CANONICAL_CHART, convention_id=CONVENTION_ID,
                         method_version=METHOD_VERSION):
    """An INDEPENDENT re-derivation of WP1_CONTRACTS §3.2 written from the
    contract text, not from ids.py — the explicit expected identity
    (target_identity is `fact:<id>` when the target resolved to a fact,
    else `ref:<target_ref>`)."""
    def floor_minute(t: datetime) -> str:
        epoch = int(t.timestamp()) - int(t.timestamp()) % 60
        return datetime.fromtimestamp(epoch, tz=UTC).strftime("%Y-%m-%dT%H:%M:00Z")
    identity = (f"fact:{target_fact_id}" if target_fact_id is not None
                else f"ref:{target_ref}")
    payload = {
        "chart_id": chart_id, "convention_id": convention_id, "body": body,
        "target_kind": target_type, "target_identity": identity,
        "relation": relation, "aspect_deg": round(float(aspect_deg) % 360.0, 4),
        "method_version": method_version,
    }
    if t_exact is None:
        payload["t_exact"] = None
        payload["t_in"] = floor_minute(t_in)
    else:
        payload["t_exact"] = floor_minute(t_exact)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_dedupe_explicit_identities_and_survivors(tmp_path):
    """The reviewer's eight-body fixture shape — per body one unique contact
    plus one physical contact reached through two map rows (aliases with
    different target_ref/weight and DIVERGENT citations): 24 inputs, 16
    survivors, explicit survivors by the ruled weight rule, explicit
    contact ids re-derived independently from the §3.2 contract and agreed
    by BOTH production implementations (ids.contact_id via the enumerator's
    _contact_id_of, and ledger.compute_contact_id), citation NULLed with
    the group's citations recoverable in the sidecar. Kills: a constant
    contact id (24 rows would form ONE group and refuse); disabled dedupe
    (24 ≠ 16); a survival rule other than highest weight."""
    rows, expected = [], {}
    for k, body in enumerate(enum_mod.PERSISTED_BODIES):
        t_u = BASE + timedelta(days=30 * k, hours=1, seconds=17)
        t_a = BASE + timedelta(days=30 * k + 10, hours=5, seconds=59)
        fact = f"fact-{body}-venus"  # two map rows resolving to ONE natal fact
        unique = dict(_episode(body, "conjunction", t_u, f"{body.upper()}-U"),
                      _map_weight=0.7)
        alias_hi = dict(_episode(body, "conjunction", t_a, "ALPHA"),
                        _map_weight=0.9, classical_citation="BPHS 1",
                        target_fact_id=fact, independence_group=f"ig-{body}-physical")
        alias_lo = dict(_episode(body, "conjunction", t_a, "BETA"),
                        _map_weight=0.5, classical_citation="BPHS 2",
                        target_fact_id=fact, independence_group=f"ig-{body}-physical")
        rows += [unique, alias_hi, alias_lo]
        expected[body] = {
            "unique": _expected_contact_id(body=body, target_type="karaka",
                                           target_ref=f"{body.upper()}-U",
                                           relation="conjunction", aspect_deg=0,
                                           t_exact=unique["t_exact"], t_in=t_u),
            # the aliases are ONE physical contact: same fact identity, same
            # minute — the id the survival rule collapses on
            "alias": _expected_contact_id(body=body, target_type="karaka",
                                          target_ref="ALPHA", target_fact_id=fact,
                                          relation="conjunction", aspect_deg=0,
                                          t_exact=alias_hi["t_exact"], t_in=t_a),
        }
        # both production implementations agree with the independent derivation
        for ep, key in ((unique, "unique"), (alias_hi, "alias"), (alias_lo, "alias")):
            assert enum_mod._contact_id_of(ep, CANONICAL_CHART, CONVENTION_ID,
                                           METHOD_VERSION) == expected[body][key]
            assert ledger.compute_contact_id(
                chart_id=CANONICAL_CHART, convention_id=CONVENTION_ID,
                body=body, target_type="karaka",
                target_fact_id=ep.get("target_fact_id"),
                target_ref=ep["target_ref"], relation="conjunction",
                aspect_deg=0, t_exact=ep["t_exact"],
                method_version=METHOD_VERSION, t_in=ep["t_in"]) == expected[body][key]
    ids = {enum_mod._contact_id_of(ep, CANONICAL_CHART, CONVENTION_ID, METHOD_VERSION)
           for ep in rows}
    assert len(ids) == 16  # 8 unique + 8 physical alias groups
    assert ids == {v for e in expected.values() for v in e.values()}
    sidecar = tmp_path / "eps.ndjson.dropped_refs.json"
    survivors, report = enum_mod.dedupe_episodes(
        [dict(ep) for ep in rows], chart_id=CANONICAL_CHART,
        convention_id=CONVENTION_ID, method_version=METHOD_VERSION,
        dropped_refs_path=str(sidecar))
    assert report["episodes_before"] == 24 and report["episodes_after"] == 16
    assert len(survivors) == 16 and report["duplicate_groups"] == 8
    assert report["per_survival_tier"] == {"weight": 8, "weight_tie_lexicographic": 0,
                                           "deeper_tie": 0}
    assert {(s["body"], s["target_ref"]) for s in survivors} == {
        (b, f"{b.upper()}-U") for b in enum_mod.PERSISTED_BODIES} | {
        (b, "ALPHA") for b in enum_mod.PERSISTED_BODIES}
    assert all(s["classical_citation"] is None for s in survivors
               if s["target_ref"] == "ALPHA")
    assert report["groups_with_divergent_citations"] == 8
    dropped = json.loads(sidecar.read_text())
    assert set(dropped) == {e["alias"] for e in expected.values()}
    for entry in dropped.values():
        assert entry["survivor_target_ref"] == "ALPHA"
        assert entry["dropped_target_refs"] == ["BETA"]
        assert entry["dropped_citations"] == ["BPHS 1", "BPHS 2"]
    assert not any("_map_weight" in s for s in survivors)


class _DigestConn:
    """What ledger._canonical_row_set needs: row_to_json rows for the
    contacts and coverage queries."""

    def __init__(self, contact_rows):
        self.contact_rows = contact_rows
        self._pending = None

    def execute(self, sql, params=None):
        if "kala_gochara_contacts" in sql:
            self._pending = [(r,) for r in self.contact_rows]
        else:
            self._pending = []
        return self

    def fetchall(self):
        return self._pending


def _row_to_json(row: tuple) -> dict:
    """row_to_json(c.*) as the driver would deliver it: column-keyed, with
    timestamps as ISO strings."""
    return json.loads(json.dumps(dict(zip(ledger._CONTACT_COLUMNS, row)), default=str))


FIXED_NOW = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


def test_real_manifest_digest_controlled_metadata(tmp_path):
    """The PRODUCTION digest function (ledger._canonical_row_set over
    row_to_json rows) with volatile metadata CONTROLLED (computed_at pinned
    per episode, one build_id, the same candidate manifest): the streamed
    build and the monolithic build yield the identical digest; the digest
    is order-independent; and it CHANGES when one row's content changes or
    one row is missing. Kills: a constant digest; a digest that ignores
    content; an order-dependent digest."""
    bodies = ("Sun", "Saturn")
    eps = [dict(ep, computed_at=FIXED_NOW)
           for b in bodies for ep in _body_episodes(b, 3)]
    mono_eps = _monolithic_round_trip(tmp_path / "eps.json", eps)
    for ep in mono_eps:
        ep["computed_at"] = datetime.fromisoformat(ep["computed_at"])
    mono_conn = _RecConn(keep_rows=True)
    ledger.write_contacts(mono_conn, CANONICAL_CHART, "4.1", CONVENTION_ID,
                          mono_eps, "build-eq")
    paths = []
    for b in bodies:
        block = sorted([e for e in eps if e["body"] == b],
                       key=build_mod.episode_stream_key)
        p = tmp_path / f"{b}.ndjson"
        enum_mod.write_episodes_ndjson(str(p), block, append=False)
        paths.append(p)
    stream_conn = _RecConn(keep_rows=True)
    merged = build_mod.iter_episodes_merged(
        [build_mod.EpisodeObjectStream(str(p), expected_body=b)
         for b, p in zip(bodies, paths)])
    ledger.write_contacts_streaming(stream_conn, CANONICAL_CHART, "4.1",
                                    CONVENTION_ID, merged, "build-eq", batch_size=2)
    assert len(stream_conn.rows) == len(mono_conn.rows) == 6
    mono_json = [_row_to_json(r) for r in mono_conn.rows]
    stream_json = [_row_to_json(r) for r in stream_conn.rows]
    d_mono = ledger._canonical_row_set(_DigestConn(mono_json), CANONICAL_CHART, "4.1")
    d_stream = ledger._canonical_row_set(_DigestConn(stream_json), CANONICAL_CHART, "4.1")
    assert d_mono == d_stream
    assert d_mono.startswith("sha256:")
    shuffled = list(stream_json)
    random.Random(3).shuffle(shuffled)
    assert ledger._canonical_row_set(_DigestConn(shuffled), CANONICAL_CHART, "4.1") == d_mono
    altered = [dict(r) for r in stream_json]
    altered[0]["target_ref"] = "TAMPERED"
    assert ledger._canonical_row_set(_DigestConn(altered), CANONICAL_CHART, "4.1") != d_mono
    assert ledger._canonical_row_set(_DigestConn(stream_json[1:]), CANONICAL_CHART, "4.1") != d_mono
    # the controlled metadata really is controlled: every row's computed_at
    # is the pinned instant and the ids are the §3.2 identities
    assert {r["computed_at"] for r in stream_json} == {str(FIXED_NOW)}
    assert {r["contact_id"] for r in stream_json} == {
        _expected_contact_id(body=e["body"], target_type="karaka",
                             target_ref=e["target_ref"], relation="conjunction",
                             aspect_deg=0, t_exact=e["t_exact"], t_in=e["t_in"])
        for e in eps}


def test_tied_keys_total_order_deterministic(tmp_path):
    """(t_in, body, relation) is NOT a total order — two distinct contacts
    sharing it are ordered by the canonical-json tie-break; the reverse
    line order is rejected, never silently re-ordered."""
    t = BASE
    ep_z = _episode("Sun", "conjunction", t, "ZZZ-TARGET")
    ep_a = _episode("Sun", "conjunction", t, "AAA-TARGET")
    order = sorted([ep_z, ep_a], key=build_mod.episode_stream_key)
    p = tmp_path / "Sun.ndjson"
    enum_mod.write_episodes_ndjson(str(p), order, append=False)
    merged = list(build_mod.iter_episodes_merged(
        [build_mod.EpisodeObjectStream(str(p))]))
    assert [e["target_ref"] for e in merged] == [e["target_ref"] for e in order]
    p2 = tmp_path / "Sun-rev.ndjson"
    enum_mod.write_episodes_ndjson(str(p2), order[::-1], append=False)
    with pytest.raises(build_mod.EpisodeStreamError):
        list(build_mod.iter_episodes_merged(
            [build_mod.EpisodeObjectStream(str(p2))]))


def test_unsorted_object_rejected(tmp_path):
    eps = _body_episodes("Sun", 3)
    p = tmp_path / "Sun.ndjson"
    enum_mod.write_episodes_ndjson(str(p), eps[::-1], append=False)
    with pytest.raises(build_mod.EpisodeStreamError):
        list(build_mod.EpisodeObjectStream(str(p)))


def test_enumerator_provenance_helpers(tmp_path):
    """source_snapshot is a content digest (order-independent over the map
    rows, sensitive to any row) and ephemeris_checksums hashes every .se1
    file under the path — the bindings the receipt carries."""
    facts = enum_mod.ResolutionFacts(positions={"SUN": {"longitude": 1.0}})
    rows = [{"event_class": "a", "weight": 1}, {"event_class": "b", "weight": 2}]
    s1 = enum_mod.source_snapshot(CANONICAL_CHART, rows, facts, {"house_vedha": "fp"})
    s2 = enum_mod.source_snapshot(CANONICAL_CHART, rows[::-1], facts, {"house_vedha": "fp"})
    assert s1 == s2 and s1["resonance_map_rows"] == 2
    s3 = enum_mod.source_snapshot(CANONICAL_CHART, rows[:1], facts, {"house_vedha": "fp"})
    assert s3["resonance_map_sha256"] != s1["resonance_map_sha256"]
    facts2 = enum_mod.ResolutionFacts(positions={"SUN": {"longitude": 2.0}})
    assert enum_mod.source_snapshot(CANONICAL_CHART, rows, facts2, {})[
        "resolution_facts_sha256"] != s1["resolution_facts_sha256"]
    (tmp_path / "sepl_18.se1").write_bytes(b"planets")
    (tmp_path / "semo_18.se1").write_bytes(b"moon")
    (tmp_path / "notes.txt").write_bytes(b"ignored")
    e = enum_mod.ephemeris_checksums(str(tmp_path))
    assert set(e["files"]) == {"sepl_18.se1", "semo_18.se1"}
    assert e["files"]["sepl_18.se1"] == "sha256:" + hashlib.sha256(b"planets").hexdigest()
    assert enum_mod.ephemeris_checksums(str(tmp_path / "missing")) == {
        "path": str(tmp_path / "missing"), "files": {}}
