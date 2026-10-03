"""A5.3 — the '5.0' input vector (AM-16; Codex round 6, R6) on the REAL schema (1081 + 1152–1157 +
1206 applied; a fresh database per test).

What is proven here: the vector has a versioned schema and binds the registry (payloads, ordered
prerequisites, soft-factor memberships, applicability, the sealed-version census), the node series
and ephemeris actually consumed, both orb policies, the rulings and the governing implementation; the
registry digest is derived TWICE by code that shares nothing (Python over typed rows vs Postgres'
own canonical JSON + sha256) and the two must agree; and every result-bearing change — a membership
reorder with identical row payloads, a node-series-only change, a window-algorithm change — changes
the identity or is refused. Historical replay checks the ORIGINAL bound inputs.
"""
from __future__ import annotations

import copy
import sys
import textwrap
import uuid
from pathlib import Path

import pytest

from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import input_vector_verifier as ivv
from services.gochara_kernel import rule_registry as rr
from services.gochara_rules import registry as rules_registry

from .test_a53_inventory import create_am5_database, drop_am5_database

REFS = list(rr.BOUND_PATH_REFS)
RULINGS = [{"id": "ST-P5-HOLD-20261001"}, {"id": "ST-H-UNKNOWN-20261002"}]


@pytest.fixture()
def db():
    import psycopg
    admin, name, dsn = create_am5_database("ivec")
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
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
    """A probe stand-in for the directories of dummy files: reports every .se1 there. The REAL probe —
    which asks the Swiss library which files it opens — is tested against the real files below."""
    return {f.name: str(f) for f in Path(ephe).glob("*.se1")}


def _vector(conn, ephe, **kw):
    kw.setdefault("files_probe", _dir_probe)
    kw.setdefault("series_probe", lambda ephe: "ab" * 32)
    return iv.build_input_vector(conn, sky_convention_id=_sky(conn), ephe_path=ephe,
                                 path_refs=kw.pop("refs", REFS), rulings=kw.pop("rulings", RULINGS), **kw)


def _ivv(db, stored, ephe, **kw):
    """The independent input check with the verifier's OWN probes stubbed for the directory of dummy files (the real
    probes are tested against the real files below)."""
    kw.setdefault("jd_range", (2451545.0, 2470000.0))
    kw.setdefault("census_probe", lambda e, lo, hi: {f.name: iv._file_sha(f) for f in Path(e).glob("*.se1")})
    kw.setdefault("series_probe", lambda e: "ab" * 32)
    kw.setdefault("backend_probe", lambda e: ("swieph", stored["ephemeris"]["swe_version"]))
    kw.setdefault("absolute_probe", lambda e: ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG)       # the real one is tested against the real files
    return ivv.verify_inputs(db, stored, ephe_path=ephe, modules=iv.IMPLEMENTATION_MODULES, path_refs=REFS, **kw)


def _sky(conn) -> str:
    """The sky convention persisted by the real substrate store (its content is what the vector digests)."""
    from services.gochara_kernel.substrate import SkyEventStore
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", ("482012f1-710e-4a25-994a-93821f5871aa",))
        return SkyEventStore(conn).register_convention()


# ── the vector and its two derivations ───────────────────────────────────────────────────────────────

def test_the_vector_binds_every_named_component_and_is_deterministic(db, ephe):
    v = _vector(db, ephe, l0_consumed=("bg_transit_rules",))
    assert v["schema"] == iv.VECTOR_SCHEMA
    assert set(v["ephemeris"]) == {"backend", "swe_version", "files", "probe_digest", "library_sha256", "platform"}
    assert len(v["ephemeris"]["library_sha256"]) == 64                       # the loaded library ARTIFACT, bound
    assert v["ephemeris"]["platform"] == iv.platform_identity() and "-" in v["ephemeris"]["platform"]
    assert set(v) == {"schema", "stored_scope", "result_policy", "sky_convention", "registry", "node", "ephemeris",
                      "l0", "orb_policy", "rulings_digest", "implementation"}
    assert v["result_policy"] == "all_null_candidate/1"
    assert set(v["sky_convention"]) == {"id", "content_digest"} and len(v["sky_convention"]["content_digest"]) == 64
    assert set(v["l0"]) == {"bg_transit_rules"}                 # bg_transit_av_gates: P5 is held, not consumed
    assert v["stored_scope"] == "stored_non_moon"
    assert v["node"]["model"] == "mean" and v["ephemeris"]["backend"] == "swieph"
    assert set(v["ephemeris"]["files"]) == {"sepl_18.se1", "semo_18.se1", "seas_18.se1"}
    assert set(v["implementation"]) == {"geometry", "evaluation", "window"}
    assert v["registry"]["census"] == [[p, "1.0.0"] for p, _ in REFS]
    assert v["orb_policy"]["activity"] == {"1.0.0": "undeclared"}   # today: no ratified activity orb anywhere
    assert _vector(db, ephe, l0_consumed=("bg_transit_rules",)) == v      # deterministic


def test_the_registry_digest_agrees_between_the_python_and_the_sql_derivations(db):
    py = iv.registry_digest(db, REFS)
    sql = ivv.sql_registry_digest(db, REFS)
    assert py == sql and len(py) == 64
    ivv.verify_registry_digest(db, REFS, py)


def test_a_disagreeing_independent_derivation_fails_the_build(db):
    with pytest.raises(RuntimeError, match="DISAGREES"):
        ivv.verify_registry_digest(db, REFS, "0" * 64)


def test_the_two_derivations_still_agree_when_a_successor_with_applicability_is_bound(db, monkeypatch):
    _bind_successor(db, monkeypatch)
    refs = list(rr.BOUND_PATH_REFS)
    assert iv.registry_digest(db, refs) == ivv.sql_registry_digest(db, refs)


def _bind_successor(conn, monkeypatch, ratified=None):
    """Bind Stream B's ACTUAL 1.1.0 rows (#2897/#2901/#2907) beside the 1.0.0 ones and seed them. `ratified`
    = (decision_ref, orb_deg) re-declares the activity_kernel@1.1.0 row's flat selector as ND-ORB-ratified,
    built through the shared codec's own invariant (`kernel_flat_problems`) — the catalogue has no ratified
    orb yet, so this is the one row not taken verbatim."""
    from services.gochara_rules import flat_selector as fs

    from ._bound_1_1_0 import bind_successors
    if ratified:
        factors = dict(rules_registry.FACTORS)
        flat = {**factors[("activity_kernel", "1.1.0")]["operand_selector"],
                "orb_state": fs.ORB_RATIFIED, "orb_decision_ref": ratified[0], "orb_deg": ratified[1]}
        assert fs.kernel_flat_problems(flat) == []
        factors[("activity_kernel", "1.1.0")] = dict(factors[("activity_kernel", "1.1.0")],
                                                     operand_selector=flat,
                                                     applicability=fs.decode_kernel(flat))
        monkeypatch.setattr(rules_registry, "FACTORS", factors)
    bind_successors(monkeypatch)
    rr.RuleRegistryStore(conn).seed()


# ── result-bearing changes change the identity (frozen vectors) ──────────────────────────────────────

def test_a_membership_only_change_changes_the_registry_digest(monkeypatch):
    """Identical row PAYLOADS, different ORDERED prerequisite memberships (P1's first two swapped):
    only the membership edges differ — the digest must."""
    import psycopg
    digests = []
    for swap in (False, True):
        admin, name, dsn = create_am5_database("ivm")
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
        try:
            with monkeypatch.context() as m:
                if swap:
                    paths = dict(rules_registry.RULE_PATHS)
                    p1 = dict(paths[("P1", "1.0.0")])
                    pre = list(p1["prerequisites"])
                    pre[0], pre[1] = pre[1], pre[0]
                    p1["prerequisites"] = pre
                    paths[("P1", "1.0.0")] = p1
                    m.setattr(rules_registry, "RULE_PATHS", paths)
                rr.RuleRegistryStore(conn).seed()
                digests.append(iv.registry_digest(conn, REFS))
                assert digests[-1] == ivv.sql_registry_digest(conn, REFS)
        finally:
            conn.close()
            drop_am5_database(admin, name)
    assert digests[0] != digests[1]


def test_binding_a_new_sealed_version_changes_the_census_and_so_the_digest(db):
    before = iv.registry_digest(db, REFS)
    assert before == ivv.sql_registry_digest(db, REFS)


def test_a_node_series_only_change_changes_the_vector(db, ephe, tmp_path):
    base = _vector(db, ephe)
    other = tmp_path / "other"
    other.mkdir()
    for name in ("sepl_18.se1", "semo_18.se1", "seas_18.se1"):
        (other / name).write_bytes(name.encode() * 64)
    (other / "semo_18.se1").write_bytes(b"a different lunar-node series")   # ONE file differs
    changed = _vector(db, str(other))
    assert iv.diff_vectors(base, changed) == ["ephemeris.files.semo_18.se1"]


def test_a_node_convention_change_changes_the_vector(db, ephe, monkeypatch):
    from services.gochara_kernel import record_store as rs
    base = _vector(db, ephe)
    monkeypatch.setitem(rs.KALA_CONVENTION_VECTOR, "node_model", "true")
    assert iv.diff_vectors(base, _vector(db, ephe)) == ["node.model"]


def test_an_unbindable_ephemeris_is_refused_not_recorded_as_unknown(db, tmp_path):
    for bad in (None, "", str(tmp_path)):
        with pytest.raises(iv.InputDrift):
            _vector(db, bad)


def test_the_admission_orb_policy_and_the_rulings_are_bound(db, ephe, monkeypatch):
    from services.gochara_kernel import convention
    base = _vector(db, ephe)
    table = copy.deepcopy(convention.ORB_TABLE)
    table["orb_conj_slow"]["orb_max_deg"] = 2.0
    monkeypatch.setattr(convention, "ORB_TABLE", table)
    assert iv.diff_vectors(base, _vector(db, ephe)) == ["orb_policy.admission_digest"]
    monkeypatch.undo()
    assert iv.diff_vectors(base, _vector(db, ephe, rulings=RULINGS + [{"id": "NEW"}])) == ["rulings_digest"]


def test_the_activity_orb_state_is_restated_in_the_vector(db, ephe, monkeypatch):
    _bind_successor(db, monkeypatch)
    v = _vector(db, ephe, refs=list(rr.BOUND_PATH_REFS))
    assert v["orb_policy"]["activity"] == {"1.0.0": "undeclared", "1.1.0": "unratified_nd_orb_open"}


@pytest.fixture()
def modules(tmp_path, monkeypatch):
    """A throwaway 'window construction' module whose source we can change."""
    monkeypatch.syspath_prepend(str(tmp_path))
    name = f"fake_window_{uuid.uuid4().hex[:6]}"
    (tmp_path / f"{name}.py").write_text("PEAK = 'earliest'\n")
    return name, tmp_path / f"{name}.py"


def test_a_window_algorithm_change_changes_the_vector(db, ephe, modules):
    name, path = modules
    mods = {"geometry": (), "evaluation": (), "window": (name,)}
    base = _vector(db, ephe, modules=mods)
    path.write_text("PEAK = 'latest'\n")
    sys.modules.pop(name, None)
    assert iv.diff_vectors(base, _vector(db, ephe, modules=mods)) == ["implementation.window"]


def test_the_real_implementation_closure_resolves_and_is_stable(db, ephe):
    a, b = iv.implementation_digests(), iv.implementation_digests()
    assert a == b and all(len(d) == 64 for d in a.values())


# ── live verification and historical replay ──────────────────────────────────────────────────────────

def _live(conn, stored, ephe, **over):
    kw = dict(sky_convention_id=stored["sky_convention"]["id"], ephe_path=ephe, path_refs=REFS,
              rulings=RULINGS, files_probe=_dir_probe, series_probe=lambda ephe: "ab" * 32)
    kw.update(over)
    iv.verify_live(conn, stored, **kw)


def test_a_live_build_passes_when_the_inputs_are_unchanged_and_names_the_drift_otherwise(db, ephe, tmp_path):
    stored = _vector(db, ephe)
    _live(db, stored, ephe)                                               # unchanged
    with pytest.raises(iv.InputDrift, match="rulings_digest"):
        _live(db, stored, ephe, rulings=RULINGS + [{"id": "NEW"}])
    other = tmp_path / "e2"
    other.mkdir()
    for name in ("sepl_18.se1", "semo_18.se1", "seas_18.se1"):
        (other / name).write_bytes(b"x" + name.encode())
    with pytest.raises(iv.InputDrift, match="ephemeris"):
        _live(db, stored, str(other))
    with pytest.raises(iv.InputDrift, match="schema"):
        _live(db, dict(stored, schema="old/0"), ephe)


def test_a_live_build_refuses_a_registry_that_gained_a_sealed_version(db, ephe, monkeypatch):
    stored = _vector(db, ephe)
    _bind_successor(db, monkeypatch)
    with pytest.raises(iv.InputDrift, match="registry"):
        _live(db, stored, ephe)                                           # the census moved


def _replay(conn, stored, ephe, refs=REFS, **over):
    kw = dict(sky_convention_id=stored["sky_convention"]["id"], ephe_path=ephe,
              rulings=RULINGS, files_probe=_dir_probe, series_probe=lambda ephe: "ab" * 32)
    kw.update(over)
    iv.verify_replay(conn, stored, refs, **kw)


def test_historical_replay_checks_the_original_inputs_not_todays_catalogue(db, ephe, monkeypatch):
    stored = _vector(db, ephe)
    _bind_successor(db, monkeypatch)                                      # a version sealed AFTER the build
    _replay(db, stored, ephe)                                             # the past build still verifies
    assert ivv.sql_registry_digest(db, REFS, stored["registry"]["census"]) == stored["registry"]["digest"]
    with pytest.raises(iv.InputDrift):
        _replay(db, dict(stored, registry=dict(stored["registry"], digest="0" * 64)), ephe)
    with pytest.raises(iv.InputDrift, match="no longer sealed"):
        _replay(db, dict(stored, registry=dict(
            stored["registry"], census=stored["registry"]["census"] + [["P9", "1.0.0"]])), ephe)


def test_replay_reuses_the_original_ephemeris_l0_implementation_and_policy_not_only_the_registry(
        db, ephe, tmp_path, monkeypatch):
    """R8-1: the replay rebuilds the WHOLE vector from the inputs available now and compares every component
    with the stored one — and uses the L0 set the ORIGINAL build consumed, not today's choice."""
    stored = _vector(db, ephe, l0_consumed=CONSUME)
    _replay(db, stored, ephe)                                             # the original inputs are all still here
    # L0 changed since the build: a replay cannot reuse the original authority
    db.execute("UPDATE public.bg_transit_rules SET vedha_house = 11 WHERE graha = 'saturn' AND primary_house = 3")
    with pytest.raises(iv.InputDrift, match="l0.bg_transit_rules"):
        _replay(db, stored, ephe)
    db.execute("UPDATE public.bg_transit_rules SET vedha_house = 12 WHERE graha = 'saturn' AND primary_house = 3")
    _replay(db, stored, ephe)
    # a different ephemeris directory
    other = tmp_path / "e3"
    other.mkdir()
    for name in ("sepl_18.se1", "semo_18.se1", "seas_18.se1"):
        (other / name).write_bytes(b"y" + name.encode())
    with pytest.raises(iv.InputDrift, match="ephemeris"):
        _replay(db, stored, str(other))
    # a different series result (library numerics) and a different runtime library artifact
    with pytest.raises(iv.InputDrift, match="ephemeris.probe_digest"):
        _replay(db, stored, ephe, series_probe=lambda e: "cd" * 32)
    monkeypatch.setattr(iv, "library_artifact_sha", lambda: "9" * 64)
    with pytest.raises(iv.InputDrift, match="ephemeris.library_sha256"):
        _replay(db, stored, ephe)
    monkeypatch.undo()
    monkeypatch.setattr(iv, "platform_identity", lambda: "Plan9-mips")
    with pytest.raises(iv.InputDrift, match="ephemeris.platform"):
        _replay(db, stored, ephe)
    monkeypatch.undo()
    # different policy (rulings) and different implementation source
    with pytest.raises(iv.InputDrift, match="rulings_digest"):
        _replay(db, stored, ephe, rulings=RULINGS + [{"id": "NEW"}])
    mods = {"geometry": (), "evaluation": (), "window": ("services.gochara_kernel.window_sweep",)}
    with pytest.raises(iv.InputDrift, match="implementation"):
        _replay(db, stored, ephe, modules=mods)


def test_a_live_check_uses_the_manifests_own_l0_set(db, ephe):
    """The consumed-authority set is part of what a manifest binds: a live check recomputes exactly that set."""
    stored_none = _vector(db, ephe)
    _live(db, stored_none, ephe)                                          # no L0 bound ⇒ none loaded
    stored = _vector(db, ephe, l0_consumed=CONSUME)
    _live(db, stored, ephe)
    db.execute("UPDATE public.bg_transit_rules SET vedha_house = 11 WHERE graha = 'saturn' AND primary_house = 3")
    _live(db, stored_none, ephe)                                          # an unconsumed authority cannot drift it
    with pytest.raises(iv.InputDrift, match="l0.bg_transit_rules"):
        _live(db, stored, ephe)


def test_the_independent_input_check_derives_every_derivable_component_and_names_the_rest(db, ephe):
    stored = _vector(db, ephe, l0_consumed=CONSUME)
    out = _ivv(db, stored, ephe)
    assert set(out["derived"]) == {"registry", "l0", "sky_convention", "ephemeris.files", "ephemeris.census",
                                   "ephemeris.library", "ephemeris.backend", "ephemeris.version", "ephemeris.probe", "ephemeris.absolute_probe",
                                   "schema", "stored_scope", "result_policy", "node", "implementation"}
    # R9-3: everything it does NOT derive is NAMED — the orb tables and rulings (builder code), the span the census was
    # taken over (supplied), and the semantics (not just the vocabulary) of the schema/scope/policy tokens
    assert set(out["not_derived"]) == {"orb_policy", "rulings_digest", "consumed_range", "schema_semantics",
                                       "scope_semantics", "result_policy_semantics"}
    assert set(out["not_derived"]) == set(ivv.NOT_INDEPENDENTLY_DERIVED)
    # each independently derived component is individually caught
    for label, tamper, match in (
            ("l0", lambda v: dict(v, l0={"bg_transit_rules": "0" * 64}), "l0.bg_transit_rules"),
            ("sky", lambda v: dict(v, sky_convention=dict(v["sky_convention"], content_digest="0" * 64)),
             "sky_convention"),
            ("file", lambda v: dict(v, ephemeris=dict(v["ephemeris"], files={
                **v["ephemeris"]["files"], "sepl_18.se1": "0" * 64})), "ephemeris.files.sepl_18.se1"),
            ("library", lambda v: dict(v, ephemeris=dict(v["ephemeris"], library_sha256="0" * 64)),
             "ephemeris.library_sha256"),
            ("platform", lambda v: dict(v, ephemeris=dict(v["ephemeris"], platform="Plan9-mips")),
             "ephemeris.platform"),
            ("backend", lambda v: dict(v, ephemeris=dict(v["ephemeris"], backend="moshier")), "ephemeris.backend"),
            ("version", lambda v: dict(v, ephemeris=dict(v["ephemeris"], swe_version="0.0.0")),
             "ephemeris.swe_version"),
            ("probe", lambda v: dict(v, ephemeris=dict(v["ephemeris"], probe_digest="0" * 64)),
             "ephemeris.probe_digest"),
            ("schema", lambda v: dict(v, schema="ka_gochara_input_vector/2"), "schema: .* is not a named member"),
            ("scope", lambda v: dict(v, stored_scope="stored_all"), "stored_scope: .* is not a named member"),
            ("policy", lambda v: dict(v, result_policy="all_null"), "result_policy: .* is not a named member"),
            ("node", lambda v: dict(v, node=dict(v["node"], model="true")), "node"),
            ("impl", lambda v: dict(v, implementation=dict(v["implementation"], window="0" * 64)),
             "implementation"),
            ("registry", lambda v: dict(v, registry=dict(v["registry"], digest="0" * 64)), "registry.digest")):
        try:
            _ivv(db, tamper(stored), ephe,
                 backend_probe=lambda e: ("swieph", stored["ephemeris"]["swe_version"]))     # the TRUE version
        except RuntimeError as exc:
            import re
            assert re.search(match, str(exc)), (label, str(exc))
        else:
            pytest.fail(f"{label}: the tampered component was NOT refused")
    for key in ("library_sha256", "platform"):          # schema /2+ REQUIRES the identity: absent is refused, not skipped
        missing = dict(stored, ephemeris={k: v for k, v in stored["ephemeris"].items() if k != key})
        with pytest.raises(RuntimeError, match=f"ephemeris.{key}: the vector binds no library identity"):
            _ivv(db, missing, ephe)


def test_the_opened_file_census_is_established_by_the_verifier_not_read_from_the_vector(db, ephe):
    """R9-3: the verifier used to hash the file NAMES the stored vector supplied. Now it derives which files the
    consumed bodies and range open, and the set must EQUAL the stored census (names, then hashes)."""
    stored = _vector(db, ephe)
    assert set(stored["ephemeris"]["files"]) == {"sepl_18.se1", "semo_18.se1", "seas_18.se1"}
    out = _ivv(db, stored, ephe)
    assert "ephemeris.census" in out["derived"]
    # a stored census that OMITS a file the bodies open: every listed hash is right, the SET is wrong
    short = dict(stored, ephemeris=dict(stored["ephemeris"], files={
        k: v for k, v in stored["ephemeris"]["files"].items() if k != "semo_18.se1"}))
    with pytest.raises(RuntimeError, match="ephemeris.census"):
        _ivv(db, short, ephe)
    # a stored census that INVENTS a file nothing opened
    extra = dict(stored, ephemeris=dict(stored["ephemeris"], files={**stored["ephemeris"]["files"],
                                                                    "sepl_24.se1": "0" * 64}))
    with pytest.raises(RuntimeError, match="ephemeris.census"):
        _ivv(db, extra, ephe)
    # with no span supplied the census CANNOT be established, and the report says so rather than claiming it
    no_span = ivv.verify_inputs(db, stored, ephe_path=ephe, modules=iv.IMPLEMENTATION_MODULES, path_refs=REFS,
                                series_probe=lambda e: "ab" * 32,
                                backend_probe=lambda e: ("swieph", stored["ephemeris"]["swe_version"]),
                                absolute_probe=lambda e: ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG)
    assert "ephemeris.census" not in no_span["derived"] and "ephemeris.census" in no_span["not_derived"]


def test_the_library_identity_is_the_loaded_artifact_and_both_derivations_agree():
    import importlib.util

    import swisseph
    a = iv.library_artifact_sha()
    assert a == ivv.runtime_library_digest() and len(a) == 64
    assert a == iv._file_sha(Path(importlib.util.find_spec("swisseph").origin))
    assert a == iv._file_sha(Path(swisseph.__file__))                       # the compiled extension the import loaded
    assert iv.platform_identity() == ivv.runtime_platform()


# ═══ AM-16 reconciliation with Stream B's model (steward M20261002T014514-c929) ═══════════════════════

from .conftest import EPHE_PATH, _PROBLEMS                              # noqa: E402
from ._import_closure import writer_closure                              # noqa: E402

real_ephemeris = pytest.mark.skipif(bool(_PROBLEMS), reason="NOT_RUN: pinned .se1 files unavailable")


@real_ephemeris
def test_the_verifiers_own_census_probe_and_backend_equal_the_builders_on_the_real_files():
    """R9-3 on the REAL files: the verifier's own sampling (its own body list, its own step) finds exactly the files the
    builder's probe records, its own series-probe copy reproduces the builder's digest, and the backend/version agree."""
    import swisseph as swe
    from services.gochara_kernel.substrate import SUBSTRATE_BODIES
    lo, hi = iv.consumed_jd_range(None)
    mine = ivv.derive_opened_file_census(EPHE_PATH, lo, hi)
    builder = {n: iv._file_sha(Path(p)) for n, p in
               iv.probe_opened_files(EPHE_PATH, tuple(SUBSTRATE_BODIES), lo, hi).items()}
    assert mine == builder and "sepl_18.se1" in mine
    assert ivv.derive_series_probe_digest(EPHE_PATH) == iv.probe_series_digest(EPHE_PATH)
    assert ivv.derive_backend_and_version(EPHE_PATH) == ("swieph", swe.version)


# (1) the ephemeris identity is the files the kernel OPENS ─────────────────────────────────────────────

@real_ephemeris
def test_the_probe_reports_exactly_the_files_the_swiss_library_opens_never_seas():
    """Measured on swisseph 2.10.03: Sun/Moon/Saturn/MEAN_NODE open sepl_18 + semo_18 and never seas_18."""
    from services.gochara_kernel.substrate import SUBSTRATE_BODIES
    opened = iv.probe_opened_files(EPHE_PATH, SUBSTRATE_BODIES, 2451545.0, 2470000.0)
    assert set(opened) == {"sepl_18.se1", "semo_18.se1"}
    assert "seas_18.se1" in {p.name for p in Path(EPHE_PATH).glob("*.se1")}     # present, but not an input


@real_ephemeris
def test_a_file_that_is_present_but_not_opened_does_not_move_the_vector(db, tmp_path):
    import shutil
    a, b = tmp_path / "a", tmp_path / "b"
    for d in (a, b):
        d.mkdir()
        for f in ("sepl_18.se1", "semo_18.se1"):
            shutil.copy(Path(EPHE_PATH) / f, d / f)
    shutil.copy(Path(EPHE_PATH) / "seas_18.se1", b / "seas_18.se1")             # an extra, unopened file
    (b / "sepl_99.se1").write_bytes(b"junk that no calc opens")
    va = _vector(db, str(a), files_probe=iv.probe_opened_files)
    vb = _vector(db, str(b), files_probe=iv.probe_opened_files)
    assert va["ephemeris"] == vb["ephemeris"] and set(va["ephemeris"]["files"]) == {"sepl_18.se1", "semo_18.se1"}


@real_ephemeris
def test_an_opened_file_that_is_absent_is_refused_never_bound_as_unknown(db, tmp_path, monkeypatch):
    """C22 isolation (steward M…115203, from #2958): the Swiss C library ALSO searches the SE_EPHE_PATH environment variable
    after `set_ephe_path(<dir>)`, and since #2860 that variable points at the FULL corpus — so a temp dir alone no longer hides
    the Moon file. Both legacy path variables are pinned at the partial directory for the test's duration, the raw Swiss
    precondition runs under `swiss_state_scope`, and the simulation has its own detector: no Moon file may actually be open."""
    import shutil

    import swisseph as real_swe

    from panchang_engine.swiss_state import swiss_state_scope
    d = tmp_path / "partial"
    d.mkdir()
    shutil.copy(Path(EPHE_PATH) / "semo_18.se1", d / "semo_18.se1")              # sepl_18 missing: Moshier fallback
    monkeypatch.setenv("SE_EPHE_PATH", str(d))
    monkeypatch.setenv("SWE_EPHE_PATH", str(d))
    with swiss_state_scope():
        real_swe.set_ephe_path(str(d))
        real_swe.calc_ut(2451545.0, real_swe.SUN, 2 | 256)                      # the raw precondition: Sun, sepl absent
        sun_file = real_swe.get_current_file_data(0)[0]
    assert not (sun_file and Path(sun_file).exists()), (
        f"the missing-sepl simulation is broken: {sun_file!r} was opened (SE_EPHE_PATH leaked a second search path)")
    with pytest.raises(iv.InputDrift, match="not served from the .se1 files|absent"):
        _vector(db, str(d), files_probe=iv.probe_opened_files)


@real_ephemeris
def test_the_probe_follows_file_block_boundaries_and_refuses_the_next_block_when_it_is_absent():
    """sepl_18/semo_18 cover 1800–2400. A range inside one block binds that block's files; a range that
    crosses into the next block must probe PAST the boundary — where the next block's file is absent
    here — and be refused, not silently stop at the first block."""
    ok = iv.probe_opened_files(EPHE_PATH, ("Sun",), 2415020.5, 2597000.0)           # 1900 … ~2399
    assert set(ok) == {"sepl_18.se1", "semo_18.se1"}
    with pytest.raises(iv.InputDrift, match="not served from the .se1 files|absent"):
        iv.probe_opened_files(EPHE_PATH, ("Sun",), 2415020.5, 2634166.5)             # … 2500: next block absent


# (2) L0 identities — the authority the PAIR LOADER consumes (R8-1) ──────────────────────────────────

from services.gochara_rules import vedha_derive  # noqa: E402

from .test_a53_inventory import L0_VEDHA_ROWS  # noqa: E402

CONSUME = ("bg_transit_rules",)


def _vedha_digest(db, ephe):
    return _vector(db, ephe, l0_consumed=CONSUME)["l0"]["bg_transit_rules"]


def test_l0_binds_the_authority_the_pair_loader_consumes_with_the_loaders_own_digest(db, ephe):
    assert iv.L0_CONSUMED["bg_transit_rules"][0] == "P2"                          # the path that reads it
    assert "bg_transit_av_gates" not in iv.L0_CONSUMED                            # P5 is held: not consumed
    loaded = vedha_derive.pairs_from_rows(L0_VEDHA_ROWS)
    assert loaded.census["total"] == 42 and loaded.census["node_rows"] == {"Rahu": 3, "Ketu": 3}
    assert _vedha_digest(db, ephe) == loaded.content_digest                      # all 42 rows, the loader's identity
    # ... derived a second, independent way (Postgres canonical JSON; no loader, no builder code)
    assert ivv.sql_l0_digest(db) == loaded.content_digest


def test_an_authority_the_build_does_not_consume_is_not_a_dependency(db, ephe):
    """`VEDHA_SOURCE` is unbound today: nothing reads the vedha pairs, so the table is neither loaded nor bound —
    its absence or damage cannot block (or silently shape) a build that never uses it."""
    assert _vector(db, ephe)["l0"] == {}
    db.execute("DROP TABLE public.bg_transit_rules")
    assert _vector(db, ephe)["l0"] == {}
    with pytest.raises(iv.InputDrift, match="not readable"):
        _vector(db, ephe, l0_consumed=CONSUME)
    assert db.execute("SELECT 1").fetchone()[0] == 1                 # the failed read did not poison the connection


def test_the_writers_consumption_set_follows_the_vedha_binding(monkeypatch):
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    assert writer_mod.VEDHA_SOURCE is None and writer_mod._l0_consumed() == ()
    monkeypatch.setattr(writer_mod, "VEDHA_SOURCE", lambda *a: None)
    assert writer_mod._l0_consumed() == ("bg_transit_rules",)


def test_row_deletion_pair_alteration_and_citation_alteration_are_each_caught(db, ephe):
    base = _vedha_digest(db, ephe)
    # (a) a pair ALTERED: still a valid authority, a different identity — in both derivations
    db.execute("UPDATE public.bg_transit_rules SET vedha_house = CASE vedha_house WHEN 12 THEN 11 ELSE 12 END"
               " WHERE graha = 'jupiter' AND primary_house = 2")
    moved = _vedha_digest(db, ephe)
    assert moved != base and ivv.sql_l0_digest(db) == moved
    assert iv.diff_vectors(_vector(db, ephe, l0_consumed=CONSUME), _vector(db, ephe, l0_consumed=CONSUME)) == []
    # (b) a citation moved to ANOTHER supported Phaladīpikā XXVI.3–8 line: valid, but the identity moves
    db.execute("UPDATE public.bg_transit_rules SET classical_citation = replace(classical_citation, 'Sloka 7',"
               " 'Sloka 6') WHERE graha = 'jupiter' AND primary_house = 2")
    cited = _vedha_digest(db, ephe)
    assert cited not in (base, moved) and ivv.sql_l0_digest(db) == cited
    # (c) a node row altered (all 42 rows are consumed): the identity moves
    db.execute("UPDATE public.bg_transit_rules SET vedha_house = vedha_house % 12 + 1 WHERE id ="
               " (SELECT min(id) FROM public.bg_transit_rules WHERE graha = 'rahu')")
    node = _vedha_digest(db, ephe)
    assert node not in (base, moved, cited) and ivv.sql_l0_digest(db) == node


def test_a_deleted_row_an_uncited_row_and_a_fabricated_citation_are_refused_by_the_loader(db, ephe):
    for sql, why in (
            ("DELETE FROM public.bg_transit_rules WHERE graha = 'sun' AND primary_house = 3", "incomplete"),
            ("UPDATE public.bg_transit_rules SET classical_citation = 'folk tradition' WHERE graha = 'venus'"
             " AND primary_house = 12", "unsupported or missing citation"),
            ("UPDATE public.bg_transit_rules SET classical_citation = 'Phaladipika Adh. XXVI, Sloka 9 — "
             "phaladeepika:PG324:C1' WHERE graha = 'saturn' AND primary_house = 3", "unsupported or missing citation"),
            ("UPDATE public.bg_transit_rules SET classical_citation = 'Phaladipika Adh. XXVI, Sloka 3 — "
             "phaladeepika:PG322:C1' WHERE graha = 'rahu'", "ND-NODE-VEDHA")):
        db.execute("BEGIN")
        try:
            db.execute(sql)
            with pytest.raises(iv.InputDrift, match=why):
                _vector(db, ephe, l0_consumed=CONSUME)
        finally:
            db.execute("ROLLBACK")
    assert _vedha_digest(db, ephe) == vedha_derive.pairs_from_rows(L0_VEDHA_ROWS).content_digest   # restored


def test_a_non_vedha_row_or_a_surrogate_id_does_not_move_l0(db, ephe):
    base = _vedha_digest(db, ephe)
    db.execute("INSERT INTO public.bg_transit_rules (rule_type, graha, primary_house, vedha_house, phala,"
               " classical_citation) VALUES ('unfavourable','sun',6,NULL,'x','c')")          # carries no vedha house
    assert _vedha_digest(db, ephe) == base
    db.execute("UPDATE public.bg_transit_rules SET id = id + 1000")                          # a surrogate key
    assert _vedha_digest(db, ephe) == base


def test_an_empty_authority_is_refused_not_bound_as_an_empty_digest(db, ephe):
    db.execute("DELETE FROM public.bg_transit_rules")
    with pytest.raises(iv.InputDrift, match="incomplete"):
        _vector(db, ephe, l0_consumed=CONSUME)
    with pytest.raises(RuntimeError, match="no vedha rows"):
        ivv.sql_l0_digest(db)


# (3) the implementation lists cover the writer's import closure ──────────────────────────────────────

def test_the_implementation_stage_lists_cover_the_writers_import_closure():
    listed = {m for mods in iv.IMPLEMENTATION_MODULES.values() for m in mods}
    closure = writer_closure()
    assert closure - listed == set(), (
        "modules the writer imports that sit in NO implementation stage (editing them would not move "
        f"the input vector): {sorted(closure - listed)}")
    assert len({m for mods in iv.IMPLEMENTATION_MODULES.values() for m in mods}) == sum(
        len(m) for m in iv.IMPLEMENTATION_MODULES.values())              # no module listed in two stages


def test_the_closure_helper_really_finds_modules_and_the_check_would_notice_an_omission(monkeypatch):
    closure = writer_closure()
    assert {"services.gochara_kernel.window_sweep", "services.gochara_rules.score",
            "services.gochara_rules.drishti"} <= closure
    trimmed = {k: tuple(m for m in v if m != "services.gochara_rules.score")
               for k, v in iv.IMPLEMENTATION_MODULES.items()}
    assert "services.gochara_rules.score" in closure - {m for v in trimmed.values() for m in v}


def test_editing_a_rules_module_moves_the_evaluation_digest(tmp_path, monkeypatch):
    """The point of the coverage: a module in a stage list moves that stage's digest when its source does."""
    monkeypatch.syspath_prepend(str(tmp_path))
    name = f"fake_rule_{uuid.uuid4().hex[:6]}"
    (tmp_path / f"{name}.py").write_text("X = 1\n")
    mods = {"geometry": (), "evaluation": (name,), "window": ()}
    a = iv.implementation_digests(mods)
    (tmp_path / f"{name}.py").write_text("X = 2\n")
    sys.modules.pop(name, None)
    assert iv.implementation_digests(mods)["evaluation"] != a["evaluation"]


# (4) the sky convention's content, and the orb decision ref ────────────────────────────────────────────

def test_the_sky_convention_content_digest_moves_when_the_stored_content_does_with_the_same_id(db, ephe):
    base = _vector(db, ephe)
    cid = base["sky_convention"]["id"]
    try:
        db.execute("UPDATE public.ka_gochara_sky_convention SET method_version = 'tampered' WHERE convention_id = %s",
                   (cid,))
    except Exception:                                    # an immutable ledger refuses the edit — equally fine
        pytest.skip("the convention table refuses an in-place edit here")
    changed = iv.build_input_vector(db, sky_convention_id=cid, ephe_path=ephe, path_refs=REFS,
                                    rulings=RULINGS, files_probe=_dir_probe, series_probe=lambda ephe: "ab" * 32)
    assert iv.diff_vectors(base, changed) == ["sky_convention.content_digest"]      # the id label did not move


def test_a_ratified_activity_orb_is_restated_with_its_decision_ref(db, ephe, monkeypatch):
    _bind_successor(db, monkeypatch, ratified=("ruling:nd_orb_test", 3.0))
    v = _vector(db, ephe, refs=list(rr.BOUND_PATH_REFS))
    assert v["orb_policy"]["activity"]["1.1.0"] == {"orb_deg": 3.0, "orb_decision_ref": "ruling:nd_orb_test"}


# ── the probe and the sky identity against stand-ins (the real-file tests above need the pinned files) ──

class _FakeSwe:
    """A Swiss stand-in with three 1000-day file BLOCKS (jd 0–1000, 1000–2000, 2000–3000). `present`
    names the blocks whose file exists; a calc in an absent block falls back (retflag 4, no file)."""
    SIDM_LAHIRI = 1

    def __init__(self, present):
        self.present = present
        self.current = None
        self.version = "fake"

    def close(self):
        self.current = None

    def set_ephe_path(self, p):
        pass

    def set_sid_mode(self, m):
        pass

    def calc_ut(self, jd, body, flags):
        block = int(jd // 1000)
        self.current = block if block in self.present else None
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0), (2 if self.current is not None else 4)

    def get_current_file_data(self, i):
        if i == 0 and self.current is not None:
            return (f"/fake/ephe/sepl_b{self.current}.se1", self.current * 1000.0,
                    self.current * 1000.0 + 1000.0, 441)
        return ("", 0.0, 0.0, 0)


@pytest.fixture()
def fake_swe(monkeypatch, tmp_path):
    import swisseph
    def install(present):
        fake = _FakeSwe(present)
        for name in ("close", "set_ephe_path", "set_sid_mode", "calc_ut", "get_current_file_data"):
            monkeypatch.setattr(swisseph, name, getattr(fake, name))
        monkeypatch.setattr(swisseph, "version", "fake")
        # the files named by the fake exist on disk so the is_file guard sees them
        monkeypatch.setattr(iv.Path, "is_file", lambda self: True)
        return fake
    return install


def test_the_probe_probes_past_each_block_boundary_the_range_spans(fake_swe):
    fake_swe({0, 1, 2})
    opened = iv.probe_opened_files("/fake/ephe", ("Sun",), 10.0, 2990.0)
    assert set(opened) == {"sepl_b0.se1", "sepl_b1.se1", "sepl_b2.se1"}        # the MIDDLE block is found too


def test_an_absent_middle_block_is_refused_even_though_both_endpoints_are_served(fake_swe):
    fake_swe({0, 2})
    with pytest.raises(iv.InputDrift, match="not served from the .se1 files"):
        iv.probe_opened_files("/fake/ephe", ("Sun",), 10.0, 2990.0)


def test_a_probe_served_by_the_fallback_is_refused_whatever_files_happen_to_be_reported(fake_swe):
    fake = fake_swe({0})
    fake.get_current_file_data = lambda i: ("/fake/ephe/sepl_b0.se1", 0.0, 1000.0, 441) if i == 0 else ("", 0.0, 0.0, 0)
    import swisseph
    swisseph.get_current_file_data = fake.get_current_file_data
    with pytest.raises(iv.InputDrift, match="not served"):
        iv.probe_opened_files("/fake/ephe", ("Sun",), 1500.0, 1600.0)          # block 1 absent → retflag 4


class _SkyConn:
    def __init__(self, content):
        self.content = content

    def execute(self, sql, params=()):
        class R:
            def __init__(s, row):
                s.row = row

            def fetchone(s):
                return s.row
        return R((self.content,) if self.content is not None else None)


def test_the_sky_identity_is_the_id_and_a_digest_of_the_stored_content():
    a = iv.sky_convention_identity(_SkyConn({"convention_id": "c1", "ayanamsha": "lahiri", "grid": "g"}), "c1")
    b = iv.sky_convention_identity(_SkyConn({"convention_id": "c1", "ayanamsha": "lahiri", "grid": "g"}), "c1")
    c = iv.sky_convention_identity(_SkyConn({"convention_id": "c1", "ayanamsha": "krishnamurti", "grid": "g"}), "c1")
    assert a == b and a["id"] == c["id"] == "c1"
    assert a["content_digest"] != c["content_digest"]                            # same label, different content
    with pytest.raises(iv.InputDrift, match="not persisted"):
        iv.sky_convention_identity(_SkyConn(None), "c1")


# ═══ Codex round 7 [9]: frozen expected-byte vectors, the series probe, the writer in the closure ═════════

import copy as _copy                                                   # noqa: E402
import json as _json                                                   # noqa: E402

FROZEN = Path(__file__).parent / "fixtures" / "am16_vectors_frozen_v3.json"
#: the INPUTS the frozen vectors were generated from (Stream B's `am16_vectors_model.py` BASE, vendored with
#: the frozen file v2 at campaign/pravaha 6ba0c5fc7 — schema /2 adds ephemeris.library_sha256 + platform; if either
#: moves, this test is the alarm)
_BASE = {
    "sky_id": "sky:lahiri_sidereal_v1", "sky_vector": {"zodiac": "sidereal", "ayanamsha": "lahiri", "node_model": "mean"},
    "registry": {
        "paths": [{"path_id": "P3", "rule_version": "1.1.0", "agent_set": "dusthana", "created_at": "t0"}],
        "prerequisites": [
            {"path_id": "P3", "rule_version": "1.1.0", "ordinal": 1, "predicate_id": "agent_resolved", "predicate_rule_version": "1.0.0"},
            {"path_id": "P3", "rule_version": "1.1.0", "ordinal": 2, "predicate_id": "in_house_set", "predicate_rule_version": "1.0.0"}],
        "soft_factors": [{"path_id": "P3", "rule_version": "1.1.0", "factor_id": "activity_kernel", "factor_rule_version": "1.1.0"}],
        "predicates": [{"predicate_id": "agent_resolved", "rule_version": "1.0.0", "created_at": "t0"},
                       {"predicate_id": "in_house_set", "rule_version": "1.0.0", "created_at": "t0"}],
        "factors": [{"factor_id": "activity_kernel", "rule_version": "1.1.0", "function": "piecewise_step_linear", "created_at": "t0",
                     "operand_selector": {"operand": "geometry:object_kind_dispatch", "span_kinds": ["sign_span", "house_span", "star"],
                                          "orb_state": "unratified_nd_orb_open", "uncovered_state": "unqualified"}}],
        "census": [["P3", "1.0.0"], ["P3", "1.1.0"]],
    },
    "node": {"model": "mean", "source": "swiss_mean_node_flg_sidereal", "zodiac": "sidereal", "ayanamsha": "lahiri"},
    "swe_version": "2.10.03", "stored_scope": "stored_non_moon", "result_policy": "all_null_candidate/1",
    "probe_digest": "6ea09e40aad66687" + "0" * 48,
    "library_sha256": "5ee1ab0c" + "e" * 56, "platform": "Linux-x86_64",
    "opened_files": {"sepl_18.se1": "a" * 64, "semo_18.se1": "b" * 64},
    "l0_rows": {"bg_transit_rules": [{"graha": "sun", "house": 4, "rule_type": "vedha", "obstructor_house": 10}]},
    "admission_orb": {"orb_table": {"conjunction": 1.0}, "point_orb_source": "convention"},
    "activity_orb": {"1.1.0": "unratified_nd_orb_open"},
    "rulings": [{"id": "ruling:am13"}, {"id": "ruling:am18", "basis": "Phaladīpikā XXVI.3–8 (phaladeepika:PG322:C1)"}],
    "impl_modules": {"geometry": {"arcs": "c" * 64}, "evaluation": {"score": "d" * 64, "kernel_factor": "e" * 64},
                     "window": {"window_sweep": "f" * 64}},
}


def _mutate(case):
    d = _copy.deepcopy(_BASE)
    r = d["registry"]
    if case == "membership_only": r["soft_factors"][0]["path_id"] = "P4"
    elif case == "node_series_only": d["opened_files"]["sepl_18.se1"] = "9" * 64
    elif case == "window_algorithm_only": d["impl_modules"]["window"]["window_sweep"] = "0" * 64
    elif case == "prerequisite_order_only": r["prerequisites"][0]["ordinal"], r["prerequisites"][1]["ordinal"] = 2, 1
    elif case == "census_only": r["census"].append(["P4", "1.0.0"])
    elif case == "orb_policy_only": d["activity_orb"]["1.1.0"] = {"orb_deg": 3.0, "orb_decision_ref": "ruling:nd_orb_x"}
    elif case == "l0_rows_only": d["l0_rows"]["bg_transit_rules"][0]["obstructor_house"] = 9
    elif case == "kernel_factor_source": d["impl_modules"]["evaluation"]["kernel_factor"] = "1" * 64
    elif case == "stored_scope_only": d["stored_scope"] = "stored_all"
    elif case == "result_policy_only": d["result_policy"] = "window_qualification/1"
    elif case == "probe_digest_only": d["probe_digest"] = "1" * 64
    elif case == "library_artifact_only": d["library_sha256"] = "7" * 64
    elif case == "platform_only": d["platform"] = "Darwin-arm64"
    elif case == "audit_field_only": r["paths"][0]["created_at"] = "t1"
    return d


CASES = ["base", "membership_only", "node_series_only", "window_algorithm_only", "prerequisite_order_only",
         "census_only", "orb_policy_only", "l0_rows_only", "kernel_factor_source", "stored_scope_only",
         "probe_digest_only", "audit_field_only", "unopened_file_only", "library_artifact_only", "platform_only",
         "result_policy_only"]


@pytest.mark.parametrize("case", CASES)
def test_assemble_vector_reproduces_the_frozen_literal_bytes_and_hashes(case):
    """The LITERAL canonical JSON of every frozen case, and its sha256, are reproduced byte-for-byte by the
    runtime's own serializer (`assemble_vector`) — a serializer drift (separators, key order, escaping,
    number format, a renamed key) fails here."""
    import hashlib
    frozen = _json.loads(FROZEN.read_text(encoding="utf-8"))[case]
    vec = iv.assemble_vector(_mutate(case))
    literal = iv.canonical_json(vec)
    assert literal == frozen["literal"]
    assert hashlib.sha256(literal.encode("utf-8")).hexdigest() == frozen["sha256"]


def test_the_frozen_registry_preimage_is_reproduced_byte_for_byte():
    import hashlib
    frozen = _json.loads(FROZEN.read_text(encoding="utf-8"))["registry_preimage"]
    literal = iv.canonical_json(iv.registry_preimage(_BASE["registry"]))
    assert literal == frozen["literal"] and hashlib.sha256(literal.encode()).hexdigest() == frozen["sha256"]


def test_every_frozen_case_changes_exactly_the_component_it_should_and_the_unobserved_ones_do_not():
    base = iv.assemble_vector(_mutate("base"))
    want = {"membership_only": "registry.digest", "node_series_only": "ephemeris.files.sepl_18.se1",
            "window_algorithm_only": "implementation.window", "prerequisite_order_only": "registry.digest",
            "census_only": "registry.census", "orb_policy_only": "orb_policy.activity.1.1.0",
            "l0_rows_only": "l0.bg_transit_rules", "kernel_factor_source": "implementation.evaluation",
            "stored_scope_only": "stored_scope", "result_policy_only": "result_policy", "probe_digest_only": "ephemeris.probe_digest",
            "library_artifact_only": "ephemeris.library_sha256", "platform_only": "ephemeris.platform"}
    for case, component in want.items():
        diff = iv.diff_vectors(base, iv.assemble_vector(_mutate(case)))
        # the NAMED component must be among those that moved (a census also moves the digest it is part of)
        assert diff and any(x == component or x.startswith(component + ".") or component.startswith(x)
                            for x in diff), (case, diff)
    assert iv.diff_vectors(base, iv.assemble_vector(_mutate("audit_field_only"))) == []
    assert iv.diff_vectors(base, iv.assemble_vector(_mutate("unopened_file_only"))) == []


def test_build_input_vector_goes_through_the_same_serializer(db, ephe):
    """build_input_vector must be assemble_vector over the gathered inputs — one serializer, not two."""
    v = _vector(db, ephe)
    assert iv.canonical_json(v) == iv.canonical_json(json_roundtrip(v))
    assert v["ephemeris"]["probe_digest"] == "ab" * 32


def json_roundtrip(v):
    return _json.loads(_json.dumps(v))


@real_ephemeris
def test_the_runtime_series_probe_equals_stream_bs_independent_probe_implementation():
    import importlib.util
    path = Path("/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/am16_series_equivalence_probe.py")
    if not path.exists():
        pytest.skip("Stream B's probe script is not available here")
    spec = importlib.util.spec_from_file_location("b_probe", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mine = iv.probe_series_digest(EPHE_PATH)
    assert mine == iv.probe_series_digest(EPHE_PATH)                                  # deterministic
    assert mine == mod.series_digest(EPHE_PATH)[0]                                    # = the independent derivation


def test_the_writer_module_itself_is_in_a_stage_list():
    listed = {m for mods in iv.IMPLEMENTATION_MODULES.values() for m in mods}
    assert "pipeline.orchestrator.writers.ka_gochara_v5" in listed
    assert {"services.gochara_kernel.substrate", "services.gochara_kernel.inventory",
            "services.gochara_rules.permission", "services.gochara_rules.frames"} <= listed


def test_a_new_build_without_the_library_identity_is_refused_not_serialized():
    """Schema /2 requires `library_sha256` and `platform`: the serializer has no optional form (a vector that cannot
    distinguish two library builds is not an identity)."""
    for key in ("library_sha256", "platform"):
        bad = {k: v for k, v in _BASE.items() if k != key}
        with pytest.raises(KeyError):
            iv.assemble_vector(bad)
    assert iv.VECTOR_SCHEMA == "ka_gochara_input_vector/3"
    for old in ("ka_gochara_input_vector/1", "ka_gochara_input_vector/2"):
        with pytest.raises(iv.InputDrift, match="schema"):
            iv.verify_live(None, {"schema": old})                                  # an older vector is refused by schema


def test_a_new_build_without_a_named_result_policy_is_refused_not_serialized():
    """R9-1: the result policy is a REQUIRED key of the manifest vector (schema /3) — no optional form, and only a
    NAMED policy can be bound."""
    bad = {k: v for k, v in _BASE.items() if k != "result_policy"}
    with pytest.raises(KeyError):
        iv.assemble_vector(bad)
    with pytest.raises(iv.InputDrift, match="result_policy"):
        iv.assemble_vector({**_BASE, "result_policy": "all_null"})
    assert iv.RESULT_POLICIES == ("all_null_candidate/1", "window_qualification/1")
    assert iv.DEFAULT_RESULT_POLICY == "all_null_candidate/1"
    assert iv.assemble_vector(_BASE)["result_policy"] == "all_null_candidate/1"


# ═══ the public ephemeris component (steward M20261002T043431-8a08; Stream B S1-REQ-EPHEMERIS) ═══════════════

def test_ephemeris_component_is_one_public_function_and_the_vector_uses_it(db, ephe):
    from services.gochara_kernel.substrate import SUBSTRATE_BODIES
    comp = iv.ephemeris_component(ephe, SUBSTRATE_BODIES, 2451545.0, 2470000.0, files_probe=_dir_probe,
                                  series_probe=lambda e: "ab" * 32)
    assert set(comp) == iv.EPHEMERIS_KEYS == {"backend", "swe_version", "library_sha256", "platform", "files",
                                              "probe_digest"}
    assert comp["backend"] == "swieph" and comp["probe_digest"] == "ab" * 32
    assert comp["library_sha256"] == iv.library_artifact_sha() and comp["platform"] == iv.platform_identity()
    assert set(comp["files"]) == {"sepl_18.se1", "semo_18.se1", "seas_18.se1"}
    # the assembled vector carries EXACTLY this component for the same inputs (no second definition)
    from services.gochara_kernel.substrate import SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START
    jd = lambda d: d.timestamp() / 86400.0 + 2440587.5                       # noqa: E731
    v = iv.build_input_vector(db, sky_convention_id=_sky(db), ephe_path=ephe, path_refs=REFS, rulings=RULINGS,
                              files_probe=_dir_probe, series_probe=lambda e: "ab" * 32)
    assert v["ephemeris"] == iv.ephemeris_component(
        ephe, SUBSTRATE_BODIES, jd(SUBSTRATE_DOMAIN_START), jd(SUBSTRATE_DOMAIN_END),
        files_probe=_dir_probe, series_probe=lambda e: "ab" * 32)


def test_ephemeris_component_refuses_a_missing_path_no_opened_file_and_a_moshier_fallback():
    for kw, match in (
            (dict(ephe_path=None), "no ephe_path"),
            (dict(ephe_path="/nonexistent", files_probe=lambda *a: {}), "no .se1 file was opened"),
            (dict(ephe_path="/nonexistent", files_probe=lambda *a: (_ for _ in ()).throw(
                iv.InputDrift("ephemeris: Sun at jd 1.0 was not served from the .se1 files (retflag 4)"))),
             "not served from the .se1 files")):
        with pytest.raises(iv.InputDrift, match=match):
            iv.ephemeris_component(kw.pop("ephe_path"), ("Sun",), 1.0, 2.0, series_probe=lambda e: "ab" * 32, **kw)


def test_assemble_vector_validates_a_pre_shaped_ephemeris_component_against_the_closed_key_set():
    good = {**_BASE}
    for k in ("swe_version", "opened_files", "probe_digest", "library_sha256", "platform"):
        good.pop(k)
    comp = iv.assemble_vector(_BASE)["ephemeris"]
    assert iv.assemble_vector({**good, "ephemeris": comp})["ephemeris"] == comp
    with pytest.raises(iv.InputDrift, match="ephemeris component keys"):
        iv.assemble_vector({**good, "ephemeris": {k: v for k, v in comp.items() if k != "platform"}})


@pytest.mark.parametrize("offset", [0.883956, -0.883956, 1e-6])
def test_a_wrong_absolute_probe_is_refused_by_name_through_the_real_input_check_and_the_pinned_value_passes(db, ephe, offset):
    """(d) The vector's series probe is compared writer-vs-verifier only (a wrong sidereal mode would be consistently wrong on both sides); the
    absolute probe is compared with a CONSTANT. 0.883956 deg is the Fagan-Bradley / Lahiri gap."""
    stored = _vector(db, ephe)
    ok = _ivv(db, stored, ephe, absolute_probe=lambda e: ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG)
    assert "ephemeris.absolute_probe" in ok["derived"]
    with pytest.raises(RuntimeError, match="ephemeris_absolute_probe_mismatch"):
        _ivv(db, stored, ephe, absolute_probe=lambda e: ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG + offset)



@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), None])
def test_a_non_finite_absolute_probe_is_refused_by_name_through_the_real_input_check(db, ephe, bad):
    """R17-H1: NaN compares False against the tolerance, so without a finiteness check a NaN probe would PASS."""
    stored = _vector(db, ephe)
    with pytest.raises(RuntimeError, match="ephemeris_absolute_probe_mismatch"):
        _ivv(db, stored, ephe, absolute_probe=lambda e: bad)
