"""C46 — the gochara_v5_test_slice marker (Stream A's spec M20261003T181323-f9c7 §3).

What this file proves:

  (a) ABSENT marker = today's behaviour BYTE-IDENTICAL: with no build_runs row,
      with a manifest that lacks the key, and with a manifest carrying only
      other keys, plan_substeps returns the pinned golden plan (298 substeps,
      key+label digest computed from the pre-change writer at
      origin/pravaha/a53-am5-inventory);
  (b) both run shapes: 'one_class_full' narrows the plan to exactly the one
      class over the full DEFAULT_HORIZON; 'all_classes_1y' keeps all 26
      scored classes over the marker's 1-year horizon (the runtime horizon is
      the marker's, and a contradicting ctx.config horizon is refused);
  (c) every refusal is named: malformed marker, wrong schema, unknown run,
      extra or missing field, classes not in SCORED_CLASSES (empty, unknown,
      duplicated), a horizon that is malformed, naive, inverted or outside
      DEFAULT_HORIZON, and the run-shape rules (subset for all_classes_1y,
      >1 year span; several classes or a non-full horizon for one_class_full)
      — each raises TestSliceRefusal, never a guess;
  (d) execution honours the slice: a grain of a class the marker does not
      name is not built (plan-level absence, no chart lock taken);
  (e) the marker is read from build_runs.plan_manifest via ctx.build_id +
      ctx.db_conn (never ctx.config), and the sliced candidate manifest's
      input vector carries stored_scope='test_slice' plus the marker digest —
      so the verification entry point REFUSES IT BY NAME (proven on a real
      disposable database with the verifier's own entry), while the
      unsliced vector is byte-identical to before (no test_slice key,
      stored_scope='stored_non_moon') and verify_live round-trips a sliced
      vector without drift.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pipeline.orchestrator.writers.ka_gochara_v5 as writer_mod  # noqa: E402
from pipeline.orchestrator.writers import ContextSpec, SubStep  # noqa: E402
from services.gochara_kernel import input_vector as iv  # noqa: E402

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

#: The golden plan of the pre-change writer (origin/pravaha/a53-am5-inventory,
#: 298 substeps) — sha256 of the canonical JSON of [[key, label], ...].
GOLDEN_PLAN_DIGEST = "0a7298509d92fc32d485113aed85a3f0c296e1ddb2db170b43f89d4d4695069a"
GOLDEN_PLAN_STEPS = 298


def _digest_of(manifest):
    """What dispatch stores in plan_manifest_digest for this manifest (JSON text is parsed first, as the writer does)."""
    if isinstance(manifest, str):
        try:
            manifest = json.loads(manifest)
        except ValueError:
            return "x"
    return writer_mod._manifest_digest(manifest)


class _ManifestConn:
    """Recording fake: answers the build_runs read with a fixed plan_manifest;
    any lifecycle call is a failure."""

    def __init__(self, manifest=None, digest="auto"):
        self.manifest = manifest
        self.digest = digest              # "auto" = the manifest's own canonical digest (what dispatch stores)
        self.statements: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        manifest = self.manifest
        digest = _digest_of(manifest) if self.digest == "auto" else self.digest
        absent = "asset_throughput" in sql          # the state guard's read: no orchestrator row in a unit test (skip-on-absent)

        class _R:
            def fetchone(self):
                return None if absent else (manifest, digest) if manifest is not None else None

            def fetchall(self):
                return []

        return _R()

    def commit(self):
        raise AssertionError("writer committed ctx.db_conn")

    def rollback(self):
        raise AssertionError("writer rolled back ctx.db_conn")

    def close(self):
        raise AssertionError("writer closed ctx.db_conn")


def _ctx(manifest=None, **config) -> ContextSpec:
    return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="test-build",
                       db_conn=_ManifestConn(manifest),
                       config={"chart_id": CHART_ID, **config}, dry_run=False)


def _marker(**over):
    m = {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": "one_class_full",
         "horizon": ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"],
         "classes": [writer_mod.SCORED_CLASSES[0]]}
    m.update(over)
    return m


def _plan_digest(ctx) -> tuple[int, str]:
    steps = writer_mod.GocharaV5Writer().plan_substeps(ctx)
    canon = json.dumps([[s.key, s.label] for s in steps],
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return len(steps), hashlib.sha256(canon.encode("utf-8")).hexdigest()


# ── (a) absent marker = byte-identical default path ──────────────────────────


def test_no_build_runs_row_is_the_golden_plan():
    assert _plan_digest(_ctx()) == (GOLDEN_PLAN_STEPS, GOLDEN_PLAN_DIGEST)


def test_manifest_without_the_key_is_the_golden_plan():
    assert _plan_digest(_ctx({"plan": [], "waves": []})) == (GOLDEN_PLAN_STEPS, GOLDEN_PLAN_DIGEST)


def test_manifest_with_only_other_keys_is_the_golden_plan():
    assert _plan_digest(_ctx({"gochara_v5_test_slice_v2": {"x": 1}, "other": 2})) == (
        GOLDEN_PLAN_STEPS, GOLDEN_PLAN_DIGEST)


def test_manifest_as_json_text_is_read():
    """psycopg may hand jsonb back as text — the marker is found either way."""
    steps = writer_mod.GocharaV5Writer().plan_substeps(_ctx(json.dumps(
        {writer_mod.TEST_SLICE_KEY: _marker()})))
    keys = [s.key for s in steps]
    assert f"verify:{writer_mod.SCORED_CLASSES[0]}" in keys


def test_the_marker_is_read_from_build_runs_by_build_id_never_from_config():
    ctx = _ctx(None)
    ctx.config[writer_mod.TEST_SLICE_KEY] = _marker()     # a config key must be IGNORED
    writer_mod.GocharaV5Writer().plan_substeps(ctx)
    read = [sql for sql, _ in ctx.db_conn.statements if "build_runs" in sql]
    assert read and "%s" in read[0]
    assert ctx.db_conn.statements[0][1] == ("test-build",)


# ── (b) the two run shapes ────────────────────────────────────────────────────


def test_one_class_full_plans_exactly_one_class():
    cls = writer_mod.SCORED_CLASSES[3]
    steps = writer_mod.GocharaV5Writer().plan_substeps(_ctx(
        {writer_mod.TEST_SLICE_KEY: _marker(classes=[cls])}))
    keys = [s.key for s in steps]
    assert keys[:12] == (["rules", "convention"]
                         + [f"body:{b}" for b in writer_mod.SUBSTRATE_BODIES]
                         + ["manifest", "snapshot"])
    rest = keys[12:]
    per = 1 + 1 + len(writer_mod.RECORD_PATHS) + len(writer_mod.WINDOW_PATHS) + 1
    assert len(rest) == per
    assert rest[0] == f"inventory:{cls}" and rest[1] == f"coverage:{cls}"
    assert rest[2:6] == [f"record:{cls}:{p}" for p in writer_mod.RECORD_PATHS]
    assert rest[6:-1] == [f"window:{cls}:{p}" for p in writer_mod.WINDOW_PATHS]
    assert rest[-1] == f"verify:{cls}"
    others = [c for c in writer_mod.SCORED_CLASSES if c != cls]
    assert not any(k for k in keys for c in others if k.endswith(f":{c}") or f":{c}:" in k)


def test_all_classes_1y_keeps_every_class_and_the_markers_horizon():
    marker = _marker(run="all_classes_1y",
                     horizon=["2025-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"],
                     classes=list(writer_mod.SCORED_CLASSES))
    ctx = _ctx({writer_mod.TEST_SLICE_KEY: marker})
    assert _plan_digest(ctx) == (GOLDEN_PLAN_STEPS, GOLDEN_PLAN_DIGEST)
    slice_ = writer_mod._test_slice(writer_mod._native_ctx(ctx))
    assert slice_.run == "all_classes_1y"
    from datetime import datetime, timezone
    assert slice_.horizon == (datetime(2025, 1, 1, tzinfo=timezone.utc),
                              datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert writer_mod._effective_horizon(ctx, slice_) == slice_.horizon


def test_marker_horizon_governs_and_a_config_horizon_equal_to_it_is_accepted():
    ctx = _ctx({writer_mod.TEST_SLICE_KEY: _marker()},
               horizon=list(writer_mod.DEFAULT_HORIZON))
    slice_ = writer_mod._test_slice(writer_mod._native_ctx(ctx))
    assert writer_mod._effective_horizon(ctx, slice_) == writer_mod.DEFAULT_HORIZON


def test_a_config_horizon_contradicting_the_marker_is_refused():
    from datetime import datetime, timezone
    ctx = _ctx({writer_mod.TEST_SLICE_KEY: _marker()},
               horizon=(datetime(2000, 1, 1, tzinfo=timezone.utc),
                        datetime(2001, 1, 1, tzinfo=timezone.utc)))
    slice_ = writer_mod._test_slice(writer_mod._native_ctx(ctx))
    with pytest.raises(writer_mod.TestSliceRefusal, match="contradicts"):
        writer_mod._effective_horizon(ctx, slice_)


def test_without_a_marker_the_config_horizon_still_governs():
    from datetime import datetime, timezone
    cfg = (datetime(2000, 1, 1, tzinfo=timezone.utc), datetime(2001, 1, 1, tzinfo=timezone.utc))
    ctx = _ctx(None, horizon=cfg)
    assert writer_mod._effective_horizon(ctx, None) == cfg
    assert writer_mod._effective_horizon(_ctx(horizon=writer_mod.DEFAULT_HORIZON), None) == writer_mod.DEFAULT_HORIZON


# ── (c) every refusal is named ────────────────────────────────────────────────

REFUSALS = {
    "marker_not_an_object": ("not an object", ["not", "a", "dict"]),
    "wrong_schema": ("schema", _marker(schema="gochara_v5_test_slice/0")),
    "unknown_run": ("unknown run", _marker(run="two_classes_full")),
    "extra_field": ("unexpected field", _marker(notes="please")),
    "missing_field": ("missing field", {"schema": writer_mod.TEST_SLICE_SCHEMA,
                                        "run": "one_class_full",
                                        "horizon": _marker()["horizon"]}),
    "classes_not_a_list": ("classes", _marker(classes="courage")),
    "classes_empty": ("classes", _marker(classes=[])),
    "class_not_scored": ("not scored classes", _marker(classes=["birth_anchor"])),
    "class_unknown": ("not scored classes", _marker(classes=["invented_class"])),
    "class_duplicated": ("twice", _marker(run="all_classes_1y",
                                          horizon=["2025-01-01T00:00:00+00:00",
                                                   "2026-01-01T00:00:00+00:00"],
                                          classes=list(writer_mod.SCORED_CLASSES)
                                          + [writer_mod.SCORED_CLASSES[0]])),
    "horizon_not_a_pair": ("not a pair", _marker(horizon=["1998-01-01T00:00:00+00:00"])),
    "horizon_not_strings": ("not a pair", _marker(horizon=[1, 2])),
    "horizon_unparseable": ("ISO 8601", _marker(horizon=["jan", "feb"])),
    "horizon_naive": ("naive", _marker(horizon=["1998-01-01T00:00:00",
                                                "2084-02-05T00:00:00"])),
    "horizon_inverted": ("empty or inverted", _marker(
        horizon=["2084-02-05T00:00:00+00:00", "1998-01-01T00:00:00+00:00"])),
    "horizon_before_default": ("outside DEFAULT_HORIZON", _marker(
        horizon=["1997-12-31T00:00:00+00:00", "2084-02-05T00:00:00+00:00"])),
    "horizon_after_default": ("outside DEFAULT_HORIZON", _marker(
        horizon=["1998-01-01T00:00:00+00:00", "2084-02-06T00:00:00+00:00"])),
    "all_classes_subset": ("all_classes_1y", _marker(
        run="all_classes_1y",
        horizon=["2025-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"],
        classes=list(writer_mod.SCORED_CLASSES[:25]))),
    "all_classes_over_one_year": ("1-year", _marker(
        run="all_classes_1y",
        horizon=["2024-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"],
        classes=list(writer_mod.SCORED_CLASSES))),
    "one_class_two_classes": ("exactly one class", _marker(
        classes=list(writer_mod.SCORED_CLASSES[:2]))),
    "one_class_short_horizon": ("full DEFAULT_HORIZON", _marker(
        horizon=["2025-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"])),
}


@pytest.mark.parametrize("case", sorted(REFUSALS), ids=sorted(REFUSALS))
def test_every_malformed_marker_is_a_named_refusal(case):
    match, marker = REFUSALS[case]
    with pytest.raises(writer_mod.TestSliceRefusal, match=match):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx({writer_mod.TEST_SLICE_KEY: marker}))


def test_the_refusal_names_the_marker_key():
    with pytest.raises(writer_mod.TestSliceRefusal, match=writer_mod.TEST_SLICE_KEY):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx({writer_mod.TEST_SLICE_KEY: {}}))


# ── (d) execution honours the slice ──────────────────────────────────────────


def test_a_grain_outside_the_marker_is_refused_by_name_never_skipped():
    """Fable P1 (scenario B): this branch used to RETURN success. The plan is fixed at asset start; a substep for a class the marker
    now read does not name means the stored plan_manifest changed — refused, and nothing but the chart lock and the marker read
    was issued (and the state guard's read-only SELECT of asset_throughput, which precedes everything)."""
    cls = writer_mod.SCORED_CLASSES[0]
    other = writer_mod.SCORED_CLASSES[1]
    ctx = _ctx({writer_mod.TEST_SLICE_KEY: _marker(classes=[cls])})
    ctx = writer_mod._native_ctx(ctx)
    with pytest.raises(writer_mod.TestSliceRefusal, match=r"not in the run's validated marker"):
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=f"record:{other}:P1"))
    assert all(("build_runs" in sql) or ("ka_gochara_lock_chart" in sql) or ("SELECT state FROM public.asset_throughput" in sql) for sql, _ in ctx.db_conn.statements)


def test_class_of_grain_parses_every_per_class_prefix():
    assert writer_mod._class_of_grain("inventory:courage") == "courage"
    assert writer_mod._class_of_grain("coverage:courage") == "courage"
    assert writer_mod._class_of_grain("verify:courage") == "courage"
    assert writer_mod._class_of_grain("record:courage:P1") == "courage"
    assert writer_mod._class_of_grain("window:courage:P1") == "courage"
    assert writer_mod._class_of_grain("rules") is None
    assert writer_mod._class_of_grain("manifest") is None
    assert writer_mod._class_of_grain("body:Sun") is None


# ── (e) the sliced manifest is unsealable by construction ────────────────────


def test_slice_component_binds_the_marker_digest():
    marker = _marker()
    slice_ = writer_mod._validate_test_slice(marker)
    comp = writer_mod._slice_component(slice_)
    expect = hashlib.sha256(iv.canonical_json(marker).encode("utf-8")).hexdigest()
    assert comp == {"schema": writer_mod.TEST_SLICE_SCHEMA, "marker_digest": expect, "run": marker["run"],
                    "classes": list(slice_.classes), "horizon": [h.isoformat() for h in slice_.horizon]}
    assert len(comp["marker_digest"]) == 64
    # audit (Fable P1 iii): the run shape, the classes and the horizon are readable from the manifest alone
    assert comp["run"] == "one_class_full" and comp["classes"] == [writer_mod.SCORED_CLASSES[0]]
    assert comp["horizon"] == ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]


def test_default_vector_has_no_test_slice_key_and_the_default_scope():
    """assemble_vector without a slice: the stored shape is byte-identical to before."""
    inp = {"stored_scope": iv.STORED_SCOPE, "result_policy": iv.DEFAULT_RESULT_POLICY,
           "sky_id": "s", "sky_vector": {},
           "registry": {"schema": iv.REGISTRY_DIGEST_SCHEMA, "paths": [], "prerequisites": [],
                        "soft_factors": [], "predicates": [], "factors": [], "census": []},
           "node": {}, "admission_orb": {}, "activity_orb": {}, "rulings": [],
           "impl_modules": {}, "test_slice": None,
           "swe_version": "2.10.03", "library_sha256": "0" * 64, "platform": "p",
           "opened_files": {}, "probe_digest": "1" * 64}
    v = iv.assemble_vector(inp)
    assert "test_slice" not in v and v["stored_scope"] == "stored_non_moon"


def test_sliced_vector_carries_the_scope_and_marker():
    inp = {"stored_scope": writer_mod.TEST_SLICE_SCOPE,
           "result_policy": iv.DEFAULT_RESULT_POLICY,
           "sky_id": "s", "sky_vector": {},
           "registry": {"schema": iv.REGISTRY_DIGEST_SCHEMA, "paths": [], "prerequisites": [],
                        "soft_factors": [], "predicates": [], "factors": [], "census": []},
           "node": {}, "admission_orb": {}, "activity_orb": {}, "rulings": [],
           "impl_modules": {}, "test_slice": {"schema": writer_mod.TEST_SLICE_SCHEMA,
                                              "marker_digest": "ab" * 32},
           "swe_version": "2.10.03", "library_sha256": "0" * 64, "platform": "p",
           "opened_files": {}, "probe_digest": "1" * 64}
    v = iv.assemble_vector(inp)
    assert v["stored_scope"] == "test_slice"
    assert v["test_slice"] == {"schema": writer_mod.TEST_SLICE_SCHEMA,
                               "marker_digest": "ab" * 32}


def test_test_slice_is_not_in_the_verifiers_scope_vocabulary():
    from services.gochara_kernel import input_vector_verifier as ivv
    assert writer_mod.TEST_SLICE_SCOPE not in ivv._KNOWN_SCOPES


# ── (e, on a real disposable database) the verification entry point refuses ──

from .test_a53_inventory import create_am5_database, drop_am5_database  # noqa: E402


@pytest.fixture()
def db():
    import psycopg
    admin, name, dsn = create_am5_database("c46slice")
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    from services.gochara_kernel import rule_registry as rr
    rr.RuleRegistryStore(conn).seed()
    try:
        yield conn
    finally:
        conn.close()
        drop_am5_database(admin, name)


@pytest.fixture()
def ephe(tmp_path):
    for name in ("sepl_18.se1", "semo_18.se1", "seas_18.se1"):
        (tmp_path / name).write_bytes(name.encode() * 64)
    return str(tmp_path)


def _dir_probe(ephe, bodies, lo, hi):
    return {f.name: str(f) for f in Path(ephe).glob("*.se1")}


def _sky(conn) -> str:
    from services.gochara_kernel.substrate import SkyEventStore
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        return SkyEventStore(conn).register_convention()


def _vector(conn, ephe, **kw):
    from services.gochara_kernel import rule_registry as rr
    kw.setdefault("files_probe", _dir_probe)
    kw.setdefault("series_probe", lambda e: "ab" * 32)
    return iv.build_input_vector(conn, sky_convention_id=_sky(conn), ephe_path=ephe,
                                 path_refs=list(rr.BOUND_PATH_REFS),
                                 rulings=[{"id": "ST-P5-HOLD-20261001"}], **kw)


def test_a_sliced_manifest_is_refused_by_name_at_the_verification_entry_point(db, ephe):
    """The verification job's preconditions call input_vector_verifier.verify_inputs on the
    candidate manifest's vector; a sliced vector is refused naming the unknown scope."""
    from services.gochara_kernel import input_vector_verifier as ivv
    from services.gochara_kernel import rule_registry as rr
    marker = _marker()
    slice_ = writer_mod._validate_test_slice(marker)
    stored = _vector(db, ephe, stored_scope=writer_mod.TEST_SLICE_SCOPE,
                     test_slice=writer_mod._slice_component(slice_))
    assert stored["stored_scope"] == "test_slice"
    assert stored["test_slice"]["marker_digest"] == slice_.digest
    with pytest.raises(RuntimeError, match=r"stored_scope: 'test_slice' is not a named member"):
        ivv.verify_inputs(db, stored, ephe_path=ephe, modules=iv.IMPLEMENTATION_MODULES,
                          path_refs=list(rr.BOUND_PATH_REFS), jd_range=(2451545.0, 2470000.0),
                          census_probe=lambda e, lo, hi: {f.name: iv._file_sha(f)
                                                          for f in Path(e).glob("*.se1")},
                          series_probe=lambda e: "ab" * 32,
                          backend_probe=lambda e: ("swieph", stored["ephemeris"]["swe_version"]),
                          absolute_probe=lambda e: ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG)


def test_verify_live_round_trips_a_sliced_vector_without_drift(db, ephe):
    """The sliced build's own substeps re-pin every consumed input: verify_live rebuilds the
    SAME sliced vector (scope + marker ride the stored vector) and finds no drift."""
    from services.gochara_kernel import rule_registry as rr
    slice_ = writer_mod._validate_test_slice(_marker())
    stored = _vector(db, ephe, stored_scope=writer_mod.TEST_SLICE_SCOPE,
                     test_slice=writer_mod._slice_component(slice_))
    iv.verify_live(db, stored, sky_convention_id=_sky(db), ephe_path=ephe,
                   path_refs=list(rr.BOUND_PATH_REFS), rulings=[{"id": "ST-P5-HOLD-20261001"}],
                   files_probe=_dir_probe, series_probe=lambda e: "ab" * 32)


def test_verify_live_refuses_a_build_that_lost_its_slice(db, ephe):
    """A sliced manifest against a LIVE build whose marker is gone drifts by name — the slice is
    part of the identity, never silently continued without it."""
    from services.gochara_kernel import rule_registry as rr
    slice_ = writer_mod._validate_test_slice(_marker())
    stored = _vector(db, ephe, stored_scope=writer_mod.TEST_SLICE_SCOPE,
                     test_slice=writer_mod._slice_component(slice_))
    # the live rebuild is given NO slice arguments (a run without the marker): the drift names
    # BOTH the scope and the marker component
    with pytest.raises(iv.InputDrift) as exc:
        iv.verify_live(db, stored, sky_convention_id=_sky(db), ephe_path=ephe,
                       path_refs=list(rr.BOUND_PATH_REFS), rulings=[{"id": "ST-P5-HOLD-20261001"}],
                       files_probe=_dir_probe, series_probe=lambda e: "ab" * 32,
                       stored_scope=iv.STORED_SCOPE, test_slice=None)
    assert "stored_scope" in str(exc.value) and "test_slice" in str(exc.value)


# ── R1 (Stream A's C46 review): the sliced build still runs the in-build ─────
# ── independent check — on the SCOPE-NORMALISED copy, never skipped ──────────

from .test_a53_am5_writer import make_ephe  # noqa: E402


def _db_with_marker(db, marker, build_id="b-c46"):
    with db.transaction():
        db.execute("CREATE TABLE IF NOT EXISTS public.build_runs"
                   " (id text PRIMARY KEY, plan_manifest jsonb, plan_manifest_digest text)")
    manifest = {writer_mod.TEST_SLICE_KEY: marker}
    with db.transaction():
        db.execute("INSERT INTO public.build_runs (id, plan_manifest, plan_manifest_digest)"
                   " VALUES (%s, %s::jsonb, %s)",
                   (build_id, json.dumps(manifest), writer_mod._manifest_digest(manifest)))


def _run_substep(db, key, ephe, build_id="b-c46"):
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=build_id, db_conn=db,
                      config={"chart_id": CHART_ID, "ephe_path": ephe}, dry_run=False)
    with db.transaction():
        return writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=key, label=key))


def test_a_sliced_build_runs_verify_inputs_on_the_scope_normalised_copy(db, tmp_path, monkeypatch):
    """R1: the manifest substep under a slice still calls verify_inputs — exactly once, on a copy
    whose scope is the default and which carries no test_slice key, with the ephemeris/registry
    components IDENTICAL to the stored vector's; the stored vector keeps scope + marker so the
    verification job still refuses it by name."""
    from services.gochara_kernel.inventory_store import InventoryStore
    ephe = make_ephe(tmp_path, monkeypatch)
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
    _db_with_marker(db, _marker())
    calls = []

    def spy(conn, vector, **kw):
        calls.append(vector)
        return {"derived": [], "not_derived": []}

    monkeypatch.setattr(writer_mod.gk_input_vector_verifier, "verify_inputs", spy)
    _run_substep(db, writer_mod.MANIFEST_SUBSTEP, ephe)
    assert len(calls) == 1
    normalised = calls[0]
    assert normalised["stored_scope"] == iv.STORED_SCOPE
    assert "test_slice" not in normalised
    with db.transaction():
        stored = InventoryStore(db).manifest_vector(CHART_ID, writer_mod.GENERATION)
    assert stored["stored_scope"] == writer_mod.TEST_SLICE_SCOPE
    assert stored["test_slice"]["marker_digest"]
    assert normalised["ephemeris"] == stored["ephemeris"]
    assert normalised["registry"] == stored["registry"]


def test_a_sliced_manifest_fails_by_name_when_the_ephemeris_is_wrong(db, tmp_path, monkeypatch):
    """R1 mutation: the census the verifier derives disagrees with the bound one → the manifest
    substep raises naming ephemeris.census and NO candidate manifest is published."""
    from services.gochara_kernel import input_vector_verifier as ivv
    from services.gochara_kernel.inventory_store import InventoryStore
    import swisseph as swe
    ephe = make_ephe(tmp_path, monkeypatch)
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
    _db_with_marker(db, _marker())
    monkeypatch.setattr(ivv, "derive_opened_file_census",
                        lambda e, lo, hi: {"sepl_18.se1": "ff" * 32, "semo_18.se1": "ff" * 32})
    monkeypatch.setattr(ivv, "derive_series_probe_digest", lambda e: "cd" * 32)
    monkeypatch.setattr(ivv, "derive_backend_and_version", lambda e: ("swieph", swe.version))
    monkeypatch.setattr(ivv, "derive_absolute_probe", lambda e: ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG)
    with pytest.raises(RuntimeError, match=r"ephemeris\.census"):
        _run_substep(db, writer_mod.MANIFEST_SUBSTEP, ephe)
    with db.transaction():
        assert InventoryStore(db).manifest_vector(CHART_ID, writer_mod.GENERATION) is None


# ── Codex P1-2 / R1b: the slice stamp is bound to the run's VALIDATED marker, never to the vector itself ───────────

def _slice():
    return writer_mod._validate_test_slice(_marker())


def _stamped(**over):
    v = {"stored_scope": writer_mod.TEST_SLICE_SCOPE, "test_slice": writer_mod._slice_component(_slice()),
         "ephemeris": {"files": {"a": "b"}}, "registry": {"digest": "d"}}
    v.update(over)
    return v


def test_without_a_marker_the_vector_is_returned_unchanged_whatever_it_carries():
    """A default context has nothing to normalise; a stamp on its vector is refused downstream by name."""
    for v in ({"stored_scope": iv.STORED_SCOPE, "schema": "x"},
              {"stored_scope": "some_unknown_scope"},
              _stamped()):
        out = writer_mod._scope_normalised(v, None)
        assert out == v and out is not v


def test_with_the_matching_marker_the_exact_pair_is_normalised_and_the_stored_vector_untouched():
    v = _stamped()
    n = writer_mod._scope_normalised(v, _slice())
    assert n["stored_scope"] == iv.STORED_SCOPE and "test_slice" not in n
    assert n["ephemeris"] == v["ephemeris"] and n["registry"] == v["registry"]
    assert v["stored_scope"] == writer_mod.TEST_SLICE_SCOPE and "test_slice" in v


@pytest.mark.parametrize("vector", [
    {"stored_scope": iv.STORED_SCOPE, "ephemeris": {}},                                            # a default vector
    {"stored_scope": writer_mod.TEST_SLICE_SCOPE, "test_slice": {}},                                # empty component
    {"stored_scope": writer_mod.TEST_SLICE_SCOPE,
     "test_slice": {"schema": writer_mod.TEST_SLICE_SCHEMA, "marker_digest": "00" * 32}},           # wrong digest
    {"stored_scope": writer_mod.TEST_SLICE_SCOPE,
     "test_slice": {"schema": "gochara_v5_test_slice/9", "marker_digest": "x"}},                    # wrong schema
    {"stored_scope": writer_mod.TEST_SLICE_SCOPE},                                                  # half stamp: scope only
    {"stored_scope": iv.STORED_SCOPE, "test_slice": {"x": 1}},                                      # half stamp: component only
    {"stored_scope": "some_unknown_scope"},                                                         # tampered scope
], ids=["default", "empty_component", "wrong_digest", "wrong_schema", "scope_only", "component_only", "unknown_scope"])
def test_with_a_marker_anything_but_the_exact_pair_is_a_named_refusal(vector):
    with pytest.raises(writer_mod.TestSliceRefusal, match="not the run's validated marker"):
        writer_mod._scope_normalised(vector, _slice())


class _HorizonConn(_ManifestConn):
    """A fake that also answers the horizon guard's read of the candidate manifest's published horizon."""

    def __init__(self, manifest, horizon):
        super().__init__(manifest)
        self.horizon = horizon

    def execute(self, sql, params=()):
        if "FROM public.kala_gochara_publication" in sql:
            horizon = self.horizon

            class _R:
                def fetchone(self):
                    return (horizon[0], horizon[1])
            return _R()
        return super().execute(sql, params)


def _drift_conn(monkeypatch, stored, marker_manifest, manifest_horizon_override=None):
    """The PRODUCTION caller `_verify_live_inputs` on a fake context, with the REAL verify_live / diff_vectors:
    only the live rebuild (build_input_vector) is replaced by one that honours the stamps it is GIVEN, so what is
    compared is exactly what the caller passed in."""
    class _Store:
        def __init__(self, conn): pass
        def manifest_vector(self, chart, gen): return stored

    class _Sky:
        def __init__(self, conn): pass
        def register_convention(self): return "sky-1"

    seen = {}

    def live(conn, **kw):
        v = {k: v for k, v in stored.items() if k not in ("stored_scope", "test_slice")}
        v["stored_scope"] = kw["stored_scope"]
        if kw.get("test_slice") is not None:
            v["test_slice"] = kw["test_slice"]
        return v

    monkeypatch.setattr(writer_mod, "InventoryStore", _Store)
    monkeypatch.setattr(writer_mod, "SkyEventStore", _Sky)
    monkeypatch.setattr(iv, "build_input_vector", live)
    monkeypatch.setattr(writer_mod.gk_input_vector_verifier, "verify_inputs",
                        lambda conn, vec, **k: seen.update(vec=vec))
    ctx = _ctx(marker_manifest)
    # the manifest's published horizon: the marker's under a slice, the default otherwise (the horizon guard reads it)
    manifest_horizon = _slice().horizon if marker_manifest is not None else writer_mod.DEFAULT_HORIZON
    if manifest_horizon_override is not None:
        manifest_horizon = manifest_horizon_override
    ctx = dataclasses.replace(ctx, db_conn=_HorizonConn(marker_manifest, manifest_horizon))
    if marker_manifest is None:         # a default run is CONFIGURED with its horizon here (an absent one is derived from the database, FB-2: tested in test_horizon_run_path)
        ctx = dataclasses.replace(ctx, config={**ctx.config, "horizon": writer_mod.DEFAULT_HORIZON})
    return ctx, seen


def _base_vector(**over):
    v = {"schema": iv.VECTOR_SCHEMA, "stored_scope": iv.STORED_SCOPE, "l0": {}, "result_policy": None,
         "ephemeris": {"files": {}}, "registry": {"digest": "d"}}
    v.update(over)
    return v


def test_production_caller_a_default_run_accepts_a_default_vector_and_a_sliced_run_a_sliced_one(monkeypatch):
    ctx, seen = _drift_conn(monkeypatch, _base_vector(), None)
    writer_mod._verify_live_inputs(ctx, CHART_ID)
    assert seen["vec"]["stored_scope"] == iv.STORED_SCOPE
    sliced = _base_vector(stored_scope=writer_mod.TEST_SLICE_SCOPE, test_slice=writer_mod._slice_component(_slice()))
    ctx, seen = _drift_conn(monkeypatch, sliced, {writer_mod.TEST_SLICE_KEY: _marker()})
    writer_mod._verify_live_inputs(ctx, CHART_ID)
    assert seen["vec"]["stored_scope"] == iv.STORED_SCOPE and "test_slice" not in seen["vec"]   # normalised copy


@pytest.mark.parametrize("stored, manifest, drifts", [
    # a SLICED run meeting a DEFAULT vector (the vector lost its stamp)
    (_base_vector(), {writer_mod.TEST_SLICE_KEY: _marker()}, ("stored_scope", "test_slice")),
    # a DEFAULT run meeting a SLICED vector (the run lost its marker)
    (_base_vector(stored_scope=writer_mod.TEST_SLICE_SCOPE, test_slice={"schema": "gochara_v5_test_slice/1",
                                                                      "marker_digest": "x"}), None,
     ("stored_scope", "test_slice")),
    # forged: the scope says slice, the component is empty
    (_base_vector(stored_scope=writer_mod.TEST_SLICE_SCOPE, test_slice={}), {writer_mod.TEST_SLICE_KEY: _marker()},
     ("test_slice",)),
    # changed: right schema, wrong digest
    (_base_vector(stored_scope=writer_mod.TEST_SLICE_SCOPE,
                  test_slice={"schema": writer_mod.TEST_SLICE_SCHEMA, "marker_digest": "00" * 32}),
     {writer_mod.TEST_SLICE_KEY: _marker()}, ("test_slice",)),
    # a DEFAULT run meeting a tampered unknown scope
    (_base_vector(stored_scope="some_unknown_scope"), None, ("stored_scope",)),
], ids=["sliced_run_default_vector", "default_run_sliced_vector", "forged_empty", "wrong_digest", "default_run_unknown_scope"])
def test_production_caller_refuses_a_missing_changed_or_forged_stamp_by_name(monkeypatch, stored, manifest, drifts):
    ctx, seen = _drift_conn(monkeypatch, stored, manifest)
    with pytest.raises(iv.InputDrift) as exc:
        writer_mod._verify_live_inputs(ctx, CHART_ID)
    for name in drifts:
        assert name in str(exc.value)
    assert "vec" not in seen                  # refused BEFORE the in-build independent check ran


def test_mutation_the_old_caller_copied_the_expectation_from_the_vector_it_was_checking(monkeypatch):
    """The defect, restated as a test: calling verify_live WITHOUT explicit stamps (the pre-fix caller) accepts a
    forged slice stamp, because it compares the vector with a rebuild that copied the vector's own stamp."""
    forged = _base_vector(stored_scope=writer_mod.TEST_SLICE_SCOPE, test_slice={})
    monkeypatch.setattr(iv, "build_input_vector",
                        lambda conn, **kw: {**{k: v for k, v in forged.items() if k not in ("stored_scope", "test_slice")},
                                            "stored_scope": kw["stored_scope"],
                                            **({"test_slice": kw["test_slice"]} if kw.get("test_slice") is not None else {})})
    iv.verify_live(None, forged)                    # no explicit stamps: passes — the hole
    with pytest.raises(iv.InputDrift):              # explicit expectation from the validated marker: refused
        iv.verify_live(None, forged, stored_scope=writer_mod.TEST_SLICE_SCOPE,
                       test_slice=writer_mod._slice_component(_slice()))


# ── Codex P2-3: malformed containers and timestamps are named refusals ────────────────────────────────────────────

class _RowConn:
    """A conn whose build_runs read returns exactly the given row (None = no row)."""

    def __init__(self, row):
        self.row = row

    def execute(self, sql, params=()):
        row = self.row

        class _R:
            def fetchone(self):
                return row
        return _R()


def _ctx_row(row):
    if row is not None and len(row) == 1:
        row = (row[0], None if row[0] is None else _digest_of(row[0]))        # the digest dispatch would have stored
    return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=_RowConn(row),
                       config={"chart_id": CHART_ID}, dry_run=False)


@pytest.mark.parametrize("manifest", [[{writer_mod.TEST_SLICE_KEY: {}}], [], "a-bare-string", 7, True,
                                      json.dumps([{writer_mod.TEST_SLICE_KEY: {}}]), json.dumps(7), "{not json"],
                         ids=["array_with_marker", "empty_array", "string", "number", "bool", "json_array_text",
                              "json_number_text", "invalid_json_text"])
def test_a_present_but_malformed_plan_manifest_is_refused_not_read_as_no_marker(manifest):
    with pytest.raises(writer_mod.TestSliceRefusal, match="plan_manifest"):
        writer_mod.GocharaV5Writer().plan_substeps(_ctx_row((manifest,)))


@pytest.mark.parametrize("row", [None, (None,), ("null",), ({},), (json.dumps({}),)],
                         ids=["no_row", "null_manifest", "json_null_text", "empty_object", "empty_object_text"])
def test_no_row_or_no_manifest_or_an_empty_object_still_means_the_default_plan(row):
    steps = writer_mod.GocharaV5Writer().plan_substeps(_ctx_row(row))
    assert len(steps) == GOLDEN_PLAN_STEPS


@pytest.mark.parametrize("pair", [["0001-01-01T00:00:00+01:00", "2000-01-01T00:00:00+00:00"],
                                  ["2000-01-01T00:00:00+00:00", "9999-12-31T23:59:59-05:00"],
                                  ["2000-01-01T00:00:00+00:00", "2000-01-01T00:00:00+00:00"]],
                         ids=["underflow_on_utc", "overflow_on_utc", "equal_endpoints"])
def test_timestamp_overflow_and_empty_horizons_are_named_refusals(pair):
    with pytest.raises(writer_mod.TestSliceRefusal):
        writer_mod._parse_slice_horizon(pair)


def test_non_string_class_members_are_a_named_refusal():
    for classes in (["marriage", 5], [None], [["marriage"]], "marriage"):
        with pytest.raises(writer_mod.TestSliceRefusal):
            writer_mod._validate_test_slice(_marker(run="all_classes_1y", classes=classes,
                                                    horizon=["2025-01-01T00:00:00+00:00", "2025-12-31T00:00:00+00:00"]))


class _Boom:
    def __init__(self, exc):
        self.exc = exc

    def execute(self, sql, params=()):
        raise self.exc


def test_a_permission_error_on_the_marker_read_propagates_but_an_absent_table_reads_as_no_marker():
    class InsufficientPrivilege(Exception):
        pass

    class UndefinedTable(Exception):
        pass
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=_Boom(InsufficientPrivilege("denied")),
                      config={"chart_id": CHART_ID}, dry_run=False)
    with pytest.raises(InsufficientPrivilege):
        writer_mod._plan_manifest(ctx)
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=_Boom(UndefinedTable("no table")),
                      config={"chart_id": CHART_ID}, dry_run=False)
    assert writer_mod._plan_manifest(ctx) is None


# ── Codex P2-4: an explicit null horizon keeps main's behaviour without a marker ────────────────────────────────────

def test_without_a_marker_an_absent_horizon_is_underivable_here_and_an_explicit_null_behaves_as_on_main():
    absent = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None, config={"chart_id": CHART_ID},
                         dry_run=False)
    null = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None,
                       config={"chart_id": CHART_ID, "horizon": None}, dry_run=False)
    listed = ["a", "b"]
    given = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None,
                        config={"chart_id": CHART_ID, "horizon": listed}, dry_run=False)
    with pytest.raises(writer_mod.HorizonUnderivable, match="birth date"):
        writer_mod._effective_horizon(absent, None)       # FB-2: absent is DERIVED (or refused by name), never the constant
    assert writer_mod._effective_horizon(null, None) is None            # main passed the null through (and failed later)
    assert writer_mod._effective_horizon(given, None) is listed         # exactly what main returned, not a copy


def test_under_a_marker_a_null_or_contradicting_config_horizon_is_refused_and_an_equal_one_accepted():
    sl = _slice()
    mk = lambda **cfg: ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None,   # noqa: E731
                                   config={"chart_id": CHART_ID, **cfg}, dry_run=False)
    assert writer_mod._effective_horizon(mk(), sl) == sl.horizon
    assert writer_mod._effective_horizon(mk(horizon=sl.horizon), sl) == sl.horizon
    with pytest.raises(writer_mod.TestSliceRefusal):
        writer_mod._effective_horizon(mk(horizon=None), sl)
    with pytest.raises(writer_mod.TestSliceRefusal):
        writer_mod._effective_horizon(mk(horizon=(sl.horizon[0], sl.horizon[0])), sl)


# ── A5.5g invariant (Stream B, round 1 on PR 3132): the slice never touches the snapshot substep ───────────────────

def _plan_keys(manifest=None):
    return [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(_ctx(manifest))]


_SLICE_SHAPES = {
    "one_class_full": _marker(),
    "all_classes_1y": _marker(run="all_classes_1y", classes=list(writer_mod.SCORED_CLASSES),
                              horizon=["2025-01-01T00:00:00+00:00", "2025-12-31T00:00:00+00:00"]),
}


@pytest.mark.parametrize("shape", sorted(_SLICE_SHAPES))
def test_no_slice_plan_drops_reorders_or_conditions_the_snapshot_substep(shape):
    """INVARIANT: the `snapshot` substep is where PR 3132's chain replace lives, so a slice plan must keep it exactly once,
    with the SAME head as the default plan (rules, convention, bodies, manifest, snapshot — nothing dropped, reordered or
    made conditional), and before every substep that writes chain rows. A slice narrows the CLASSES, never the head."""
    default = _plan_keys()
    sliced = _plan_keys({writer_mod.TEST_SLICE_KEY: _SLICE_SHAPES[shape]})
    snap = writer_mod.SNAPSHOT_SUBSTEP
    assert sliced.count(snap) == 1 and default.count(snap) == 1

    def head(plan):
        return plan[:plan.index(snap) + 1]
    assert head(sliced) == head(default)
    writers = [i for i, k in enumerate(sliced) if k.startswith(("inventory:", "coverage:", "record:", "window:", "verify:"))]
    assert writers and min(writers) > sliced.index(snap)


@pytest.mark.parametrize("manifest, stored_kw, other", [
    (None, {}, (writer_mod.DEFAULT_HORIZON[0], writer_mod.DEFAULT_HORIZON[1] - __import__("datetime").timedelta(days=1))),
    ({writer_mod.TEST_SLICE_KEY: _marker()},
     {"stored_scope": writer_mod.TEST_SLICE_SCOPE, "test_slice": {"schema": writer_mod.TEST_SLICE_SCHEMA,
                                                                "marker_digest": "placeholder"}},
     (writer_mod.DEFAULT_HORIZON[0], writer_mod.DEFAULT_HORIZON[1] - __import__("datetime").timedelta(days=1))),
], ids=["default_run", "sliced_run"])
def test_production_caller_refuses_a_horizon_that_is_not_the_manifests_for_a_default_and_a_sliced_run(monkeypatch,
                                                                                                      manifest, stored_kw, other):
    stored = _base_vector(**stored_kw)
    if manifest is not None:
        stored["test_slice"] = writer_mod._slice_component(_slice())
    ctx, seen = _drift_conn(monkeypatch, stored, manifest, manifest_horizon_override=other)
    with pytest.raises(writer_mod.HorizonMismatch, match="horizon guard"):
        writer_mod._verify_live_inputs(ctx, CHART_ID)
    assert "vec" not in seen


# ── Fable P1 on PR 3110: a change of build_runs.plan_manifest DURING a run is refused on every read ─────────────────────

def test_the_manifest_digest_is_the_runners_canonicalisation():
    """The writer cannot import the runner (layering), so its copy of the canonicalisation is pinned equal on real manifests."""
    from pipeline.orchestrator import runner
    samples = [
        {}, {"a": 1}, {"b": [3, 1, 2], "a": {"z": 1, "y": [{"k": "v", "j": None}]}},
        {"version": "nirmana-run-manifest/v1", "chart_id": CHART_ID, "waves": [["ka_gochara_v5"]],
         writer_mod.TEST_SLICE_KEY: _marker()},
        {"unicode": "Gocara-Pratijñā 5.0 — mūrti", "float": 1.5, "bool": True, "nested": {"é": ["ü", {"ß": 0}]}},
    ]
    for m in samples:
        assert writer_mod._manifest_digest(m) == runner._canonical_manifest_digest(m), m


def test_scenario_a_a_marker_removed_after_dispatch_is_refused_not_read_as_no_marker():
    """Staged with a marker (plan narrowed), the key is then removed from the row while the stored digest stays: the manifest
    substep used to read 'no marker' and stamp a full-horizon DEFAULT candidate on a one-class plan. Now every read refuses."""
    staged = {writer_mod.TEST_SLICE_KEY: _marker(), "version": "nirmana-run-manifest/v1"}
    stored_digest = writer_mod._manifest_digest(staged)
    tampered = {"version": "nirmana-run-manifest/v1"}                          # the key removed
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=_ManifestConn(tampered, digest=stored_digest),
                      config={"chart_id": CHART_ID}, dry_run=False)
    with pytest.raises(writer_mod.TestSliceRefusal, match="plan_manifest_digest"):
        writer_mod._test_slice(ctx)
    with pytest.raises(writer_mod.TestSliceRefusal, match="plan_manifest_digest"):
        writer_mod.GocharaV5Writer().plan_substeps(ctx)                         # and at plan time


def test_scenario_b_a_marker_replaced_after_dispatch_is_refused():
    a, b = writer_mod.SCORED_CLASSES[0], writer_mod.SCORED_CLASSES[1]
    staged = {writer_mod.TEST_SLICE_KEY: _marker(classes=[a])}
    replaced = {writer_mod.TEST_SLICE_KEY: _marker(classes=[b])}
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b",
                      db_conn=_ManifestConn(replaced, digest=writer_mod._manifest_digest(staged)),
                      config={"chart_id": CHART_ID}, dry_run=False)
    with pytest.raises(writer_mod.TestSliceRefusal, match="plan_manifest_digest"):
        writer_mod._plan_manifest(ctx)
    # and if digest and manifest are replaced TOGETHER, the substeps of the old plan name a class the new marker does not
    ctx2 = writer_mod._native_ctx(ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=_ManifestConn(replaced),
                                              config={"chart_id": CHART_ID}, dry_run=False))
    with pytest.raises(writer_mod.TestSliceRefusal, match="not in the run's validated marker"):
        writer_mod.GocharaV5Writer().run_substep(ctx2, SubStep(key=f"inventory:{a}"))


@pytest.mark.parametrize("digest", [None, "", "not-hex", "0" * 64, 7], ids=["none", "empty", "not_hex", "wrong_digest", "wrong_type"])
def test_a_manifest_with_a_missing_or_wrong_digest_is_refused(digest):
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b",
                      db_conn=_ManifestConn({writer_mod.TEST_SLICE_KEY: _marker()}, digest=digest),
                      config={"chart_id": CHART_ID}, dry_run=False)
    with pytest.raises(writer_mod.TestSliceRefusal, match="plan_manifest_digest"):
        writer_mod._plan_manifest(ctx)


def test_a_default_manifest_with_the_right_digest_still_means_the_default_plan():
    assert len(_plan_keys({"version": "nirmana-run-manifest/v1", "waves": [["ka_gochara_v5"]]})) == GOLDEN_PLAN_STEPS


def test_the_digest_is_read_with_the_manifest_in_one_statement():
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=_ManifestConn({"x": 1}), config={"chart_id": CHART_ID},
                      dry_run=False)
    writer_mod._plan_manifest(ctx)
    sql = ctx.db_conn.statements[0][0]
    assert "plan_manifest" in sql and "plan_manifest_digest" in sql                  # one read: no window between the two


def test_one_year_admits_366_days_and_not_one_second_more():
    """'all_classes_1y' means AT MOST 366 days (a leap year fits): pinned at the boundary."""
    start = "2024-01-01T00:00:00+00:00"
    ok = writer_mod._validate_test_slice(_marker(run="all_classes_1y", classes=list(writer_mod.SCORED_CLASSES),
                                                 horizon=[start, "2025-01-01T00:00:00+00:00"]))          # 366 days (2024 is a leap year)
    assert ok.horizon[1] - ok.horizon[0] == __import__("datetime").timedelta(days=366)
    with pytest.raises(writer_mod.TestSliceRefusal, match="1-year"):
        writer_mod._validate_test_slice(_marker(run="all_classes_1y", classes=list(writer_mod.SCORED_CLASSES),
                                                horizon=[start, "2025-01-01T00:00:01+00:00"]))


# ── Fable P3: the marker read never commits (a savepoint helper that cannot open an outermost transaction) ──────────────

class _Status:
    def __init__(self, name):
        self.name = name


class _SavepointConn:
    """A connection fake: records every statement, fails the test if `transaction()` is used where it must not be."""

    def __init__(self, status, autocommit, fail_read=False):
        self.info = types_namespace(transaction_status=_Status(status))
        self.autocommit = autocommit
        self.statements: list[str] = []
        self.transaction_calls = 0
        self.fail_read = fail_read

    def transaction(self):
        self.transaction_calls += 1
        conn = self

        class _Tx:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *exc):
                return False
        return _Tx()

    def execute(self, sql, params=None):
        self.statements.append(sql)


def types_namespace(**kw):
    import types
    return types.SimpleNamespace(**kw)


def test_on_an_idle_non_autocommit_connection_the_read_uses_a_manual_savepoint_never_transaction():
    conn = _SavepointConn("IDLE", autocommit=False)
    assert writer_mod._in_savepoint(conn, lambda: "row") == "row"
    assert conn.transaction_calls == 0                                              # transaction() would COMMIT at exit
    assert conn.statements == ["SAVEPOINT gochara_v5_marker_read", "RELEASE SAVEPOINT gochara_v5_marker_read"]


def test_a_failing_read_on_an_idle_connection_rolls_back_to_the_savepoint_and_re_raises():
    conn = _SavepointConn("IDLE", autocommit=False)

    def boom():
        raise RuntimeError("relation does not exist")
    with pytest.raises(RuntimeError, match="does not exist"):
        writer_mod._in_savepoint(conn, boom)
    assert conn.transaction_calls == 0
    assert conn.statements == ["SAVEPOINT gochara_v5_marker_read", "ROLLBACK TO SAVEPOINT gochara_v5_marker_read"]


@pytest.mark.parametrize("status, autocommit", [("INTRANS", False), ("INTRANS", True), ("IDLE", True)],
                         ids=["inside_a_transaction", "autocommit_inside", "autocommit_idle"])
def test_inside_a_transaction_or_on_an_autocommit_connection_transaction_is_the_savepoint(status, autocommit):
    conn = _SavepointConn(status, autocommit=autocommit)
    assert writer_mod._in_savepoint(conn, lambda: 1) == 1
    assert conn.transaction_calls == 1 and conn.statements == []


def test_a_connection_without_transaction_support_just_reads():
    class Bare:
        pass
    assert writer_mod._in_savepoint(Bare(), lambda: 5) == 5
