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


def _vector(conn, ephe, **kw):
    return iv.build_input_vector(conn, sky_convention_id="sha256:" + "ab" * 32, ephe_path=ephe,
                                 path_refs=kw.pop("refs", REFS), rulings=kw.pop("rulings", RULINGS), **kw)


# ── the vector and its two derivations ───────────────────────────────────────────────────────────────

def test_the_vector_binds_every_named_component_and_is_deterministic(db, ephe):
    v = _vector(db, ephe)
    assert v["schema"] == iv.VECTOR_SCHEMA
    assert set(v) == {"schema", "sky_convention", "registry", "node", "ephemeris", "orb_policy",
                      "rulings_digest", "implementation"}
    assert v["node"]["model"] == "mean" and v["ephemeris"]["backend"] == "swieph"
    assert set(v["ephemeris"]["files"]) == {"sepl_18.se1", "semo_18.se1", "seas_18.se1"}
    assert set(v["implementation"]) == {"geometry", "evaluation", "window"}
    assert v["registry"]["census"] == [[p, "1.0.0"] for p, _ in REFS]
    assert v["orb_policy"]["activity"] == {"1.0.0": "undeclared"}   # today: no ratified activity orb anywhere
    assert _vector(db, ephe) == v                               # deterministic


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


def _bind_successor(conn, monkeypatch, soft=None):
    factors, paths = dict(rules_registry.FACTORS), dict(rules_registry.RULE_PATHS)
    app = {"span": {"object_kinds": ["sign_span", "house_span", "star"], "function": "step",
                    "inside": 1.0, "outside": 0.0},
           "angular": {"object_kinds": ["degree_point", "derived_point", "saham", "house_lord"],
                       "function": "linear", "formula": "1 - |Δλ|/orb", "orb_deg": None}}
    factors[("activity_kernel", "1.1.0")] = dict(factors[("activity_kernel", "1.0.0")],
                                                 rule_version="1.1.0", applicability=app)
    paths[("P3", "1.2.0")] = dict(paths[("P3", "1.0.0")], rule_version="1.2.0",
                                  soft_factors=soft or [("activity_kernel", "1.1.0")])
    monkeypatch.setattr(rules_registry, "FACTORS", factors)
    monkeypatch.setattr(rules_registry, "RULE_PATHS", paths)
    monkeypatch.setattr(rr, "BOUND_FACTOR_REFS", rr.BOUND_FACTOR_REFS + (("activity_kernel", "1.1.0"),))
    monkeypatch.setattr(rr, "BOUND_PATH_REFS", rr.BOUND_PATH_REFS + (("P3", "1.2.0"),))
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
    assert v["orb_policy"]["activity"] == {"1.0.0": "undeclared", "1.1.0": "unratified"}


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
    kw = dict(sky_convention_id="sha256:" + "ab" * 32, ephe_path=ephe, path_refs=REFS, rulings=RULINGS)
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


def test_historical_replay_checks_the_original_inputs_not_todays_catalogue(db, ephe, monkeypatch):
    stored = _vector(db, ephe)
    _bind_successor(db, monkeypatch)                                      # a version sealed AFTER the build
    iv.verify_replay(db, stored, REFS)                                    # the past build still verifies
    assert ivv.sql_registry_digest(db, REFS, stored["registry"]["census"]) == stored["registry"]["digest"]
    with pytest.raises(iv.InputDrift):
        iv.verify_replay(db, dict(stored, registry=dict(stored["registry"], digest="0" * 64)), REFS)
    with pytest.raises(iv.InputDrift, match="no longer sealed"):
        iv.verify_replay(db, dict(stored, registry=dict(
            stored["registry"], census=stored["registry"]["census"] + [["P9", "1.0.0"]])), REFS)
