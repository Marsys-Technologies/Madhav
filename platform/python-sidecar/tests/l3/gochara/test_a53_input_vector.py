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


def _sky(conn) -> str:
    """The sky convention persisted by the real substrate store (its content is what the vector digests)."""
    from services.gochara_kernel.substrate import SkyEventStore
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", ("482012f1-710e-4a25-994a-93821f5871aa",))
        return SkyEventStore(conn).register_convention()


# ── the vector and its two derivations ───────────────────────────────────────────────────────────────

def test_the_vector_binds_every_named_component_and_is_deterministic(db, ephe):
    v = _vector(db, ephe)
    assert v["schema"] == iv.VECTOR_SCHEMA
    assert set(v["ephemeris"]) == {"backend", "swe_version", "files", "probe_digest"}
    assert set(v) == {"schema", "stored_scope", "sky_convention", "registry", "node", "ephemeris", "l0",
                      "orb_policy", "rulings_digest", "implementation"}
    assert set(v["sky_convention"]) == {"id", "content_digest"} and len(v["sky_convention"]["content_digest"]) == 64
    assert set(v["l0"]) == {"bg_transit_rules"}                 # bg_transit_av_gates: P5 is held, not consumed
    assert v["stored_scope"] == "stored_non_moon"
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


def _bind_successor(conn, monkeypatch, soft=None, ratified=None):
    factors, paths = dict(rules_registry.FACTORS), dict(rules_registry.RULE_PATHS)
    app = {"span": {"object_kinds": ["sign_span", "house_span", "star"], "function": "step",
                    "inside": 1.0, "outside": 0.0},
           "angular": {"object_kinds": ["degree_point", "derived_point", "saham", "house_lord"],
                       "function": "linear", "formula": "1 - |Δλ|/orb", "orb_deg": None}}
    if ratified:
        app["angular"].update(orb_decision_ref=ratified[0], orb_deg=ratified[1])
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


# ═══ AM-16 reconciliation with Stream B's model (steward M20261002T014514-c929) ═══════════════════════

from .conftest import EPHE_PATH, _PROBLEMS                              # noqa: E402
from ._import_closure import writer_closure                              # noqa: E402

real_ephemeris = pytest.mark.skipif(bool(_PROBLEMS), reason="NOT_RUN: pinned .se1 files unavailable")


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
def test_an_opened_file_that_is_absent_is_refused_never_bound_as_unknown(db, tmp_path):
    import shutil
    d = tmp_path / "partial"
    d.mkdir()
    shutil.copy(Path(EPHE_PATH) / "semo_18.se1", d / "semo_18.se1")              # sepl_18 missing: Moshier fallback
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


# (2) L0 identities ───────────────────────────────────────────────────────────────────────────────────

def test_l0_binds_the_consumed_vedha_rows_and_says_which_path_consumes_them(db, ephe):
    assert iv.L0_CONSUMED["bg_transit_rules"][0] == "P2"                          # the path that reads it
    assert "bg_transit_av_gates" not in iv.L0_CONSUMED                            # P5 is held: not consumed
    base = _vector(db, ephe)
    assert set(base["l0"]) == {"bg_transit_rules"}


def test_a_changed_vedha_row_moves_l0_and_a_non_vedha_row_or_a_surrogate_id_does_not(db, ephe):
    base = _vector(db, ephe)
    db.execute("INSERT INTO public.bg_transit_rules (rule_type, graha, primary_house, vedha_house, phala,"
               " classical_citation) VALUES ('favourable','sun',6,NULL,'x','c')")          # not consumed
    assert _vector(db, ephe)["l0"] == base["l0"]
    db.execute("UPDATE public.bg_transit_rules SET id = id + 1000")                          # a surrogate key
    assert _vector(db, ephe)["l0"] == base["l0"]
    db.execute("UPDATE public.bg_transit_rules SET vedha_house = 11 WHERE graha = 'saturn' AND rule_type = 'vedha'")
    assert iv.diff_vectors(base, _vector(db, ephe)) == ["l0.bg_transit_rules"]


def test_an_absent_or_empty_l0_table_is_refused(db, ephe):
    db.execute("DELETE FROM public.bg_transit_rules")
    with pytest.raises(iv.InputDrift, match="no consumed rows"):
        _vector(db, ephe)
    db.execute("DROP TABLE public.bg_transit_rules")
    with pytest.raises(iv.InputDrift, match="not readable"):
        _vector(db, ephe)


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

FROZEN = Path(__file__).parent / "fixtures" / "am16_vectors_frozen_v1.json"
#: the INPUTS the frozen vectors were generated from (Stream B's `am16_vectors_model.py` BASE, vendored with
#: the frozen file at campaign/pravaha 425a89218; if either moves, this test is the alarm)
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
    "swe_version": "2.10.03", "stored_scope": "stored_non_moon", "probe_digest": "6ea09e40aad66687" + "0" * 48,
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
    elif case == "probe_digest_only": d["probe_digest"] = "1" * 64
    elif case == "audit_field_only": r["paths"][0]["created_at"] = "t1"
    return d


CASES = ["base", "membership_only", "node_series_only", "window_algorithm_only", "prerequisite_order_only",
         "census_only", "orb_policy_only", "l0_rows_only", "kernel_factor_source", "stored_scope_only",
         "probe_digest_only", "audit_field_only", "unopened_file_only"]


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
            "stored_scope_only": "stored_scope", "probe_digest_only": "ephemeris.probe_digest"}
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
