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


class _ManifestConn:
    """Recording fake: answers the build_runs read with a fixed plan_manifest;
    any lifecycle call is a failure."""

    def __init__(self, manifest=None):
        self.manifest = manifest
        self.statements: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        manifest = self.manifest

        class _R:
            def fetchone(self):
                return (manifest,) if manifest is not None else None

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
         "horizon": ["1998-01-01T00:00:00+00:00", "2026-04-17T00:00:00+00:00"],
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
    assert writer_mod._effective_horizon(_ctx(), None) == writer_mod.DEFAULT_HORIZON


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
                                                "2026-04-17T00:00:00"])),
    "horizon_inverted": ("empty or inverted", _marker(
        horizon=["2026-04-17T00:00:00+00:00", "1998-01-01T00:00:00+00:00"])),
    "horizon_before_default": ("outside DEFAULT_HORIZON", _marker(
        horizon=["1997-12-31T00:00:00+00:00", "2026-04-17T00:00:00+00:00"])),
    "horizon_after_default": ("outside DEFAULT_HORIZON", _marker(
        horizon=["1998-01-01T00:00:00+00:00", "2026-04-18T00:00:00+00:00"])),
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


def test_a_grain_outside_the_slice_is_not_built():
    cls = writer_mod.SCORED_CLASSES[0]
    other = writer_mod.SCORED_CLASSES[1]
    ctx = _ctx({writer_mod.TEST_SLICE_KEY: _marker(classes=[cls])})
    ctx = writer_mod._native_ctx(ctx)
    res = writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=f"record:{other}:P1"))
    assert res.rows_inserted == 0 and "not in the marker" in res.notes
    # nothing but the chart lock and the marker read was issued — no record-phase work
    assert all(("build_runs" in sql) or ("ka_gochara_lock_chart" in sql)
               for sql, _ in ctx.db_conn.statements)


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
    assert comp == {"schema": writer_mod.TEST_SLICE_SCHEMA, "marker_digest": expect}
    assert len(comp["marker_digest"]) == 64


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
                   " (id text PRIMARY KEY, plan_manifest jsonb)")
    with db.transaction():
        db.execute("INSERT INTO public.build_runs (id, plan_manifest)"
                   " VALUES (%s, %s::jsonb)",
                   (build_id, json.dumps({writer_mod.TEST_SLICE_KEY: marker})))


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


# ── R1b (Stream A's C46b re-review): the scope normalisation applies ONLY to a slice-stamped vector ───────────────

def test_a_default_vector_is_returned_unchanged_by_the_normalisation():
    v = {"stored_scope": iv.STORED_SCOPE, "result_policy": "all_null_candidate/1", "schema": "x"}
    assert writer_mod._scope_normalised(v) == v and writer_mod._scope_normalised(v) is not v


def test_an_unknown_or_tampered_stored_scope_is_NOT_normalised_so_the_default_path_still_refuses_it():
    v = {"stored_scope": "some_unknown_scope", "result_policy": "all_null_candidate/1"}
    assert writer_mod._scope_normalised(v)["stored_scope"] == "some_unknown_scope"


def test_a_slice_stamped_vector_is_normalised_to_the_default_scope_without_the_slice_component():
    v = {"stored_scope": writer_mod.TEST_SLICE_SCOPE, "test_slice": {"schema": writer_mod.TEST_SLICE_SCHEMA, "marker_digest": "ab"},
         "ephemeris": {"files": {"a": "b"}}}
    n = writer_mod._scope_normalised(v)
    assert n["stored_scope"] == iv.STORED_SCOPE and "test_slice" not in n and n["ephemeris"] == v["ephemeris"]
    assert v["stored_scope"] == writer_mod.TEST_SLICE_SCOPE and "test_slice" in v      # the stored vector is untouched


@pytest.mark.parametrize("half", [{"stored_scope": "test_slice"}, {"stored_scope": "stored_non_moon", "test_slice": {"x": 1}}])
def test_a_half_stamped_vector_is_refused_by_name(half):
    with pytest.raises(writer_mod.TestSliceRefusal, match="half-stamped"):
        writer_mod._scope_normalised(half)


def test_verify_live_inputs_still_hands_an_unknown_stored_scope_to_verify_inputs_unchanged(monkeypatch):
    """The default path through the real seam: a stored vector with an unknown scope reaches verify_inputs AS IS."""
    seen = {}

    class _Store:
        def __init__(self, conn): pass
        def manifest_vector(self, chart, gen): return {"stored_scope": "some_unknown_scope", "l0": {}}

    class _Sky:
        def __init__(self, conn): pass
        def register_convention(self): return "sky-1"

    monkeypatch.setattr(writer_mod, "InventoryStore", _Store)
    monkeypatch.setattr(writer_mod, "SkyEventStore", _Sky)
    monkeypatch.setattr(writer_mod.gk_input_vector, "verify_live", lambda *a, **k: None)
    monkeypatch.setattr(writer_mod.gk_input_vector_verifier, "verify_inputs",
                        lambda conn, vec, **k: seen.update(vec=vec))
    writer_mod._verify_live_inputs(_ctx(), CHART_ID)
    assert seen["vec"]["stored_scope"] == "some_unknown_scope"


def test_mutation_without_the_stamp_condition_the_unknown_scope_would_be_masked(monkeypatch):
    """Mutation proof: the pre-R1b helper (unconditional) would have rewritten the unknown scope — this test pins that the
    current helper does not."""
    def pre_r1b(vector):
        v = dict(vector); v["stored_scope"] = iv.STORED_SCOPE; v.pop("test_slice", None); return v
    unknown = {"stored_scope": "some_unknown_scope"}
    assert pre_r1b(unknown)["stored_scope"] == iv.STORED_SCOPE                 # the defect
    assert writer_mod._scope_normalised(unknown)["stored_scope"] == "some_unknown_scope"   # the fix
