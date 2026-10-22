"""SR-W3-SHAPE item 3 — a FINAL build may defer its in-build `verify:<class>` to the independent verification job.

Ruling (DECISIONS_SURROGATE SR-W3-SHAPE 3; evidence DESIGN_NOTE_W3 §C): under a strict-boolean config key
`gochara_v5_defer_in_build_verify`, `verify:<class>` returns the NAMED no-op `deferred_to_independent_verification`;
the substep stays in the plan (298 substeps, index = total); the flag is bound into the manifest input vector so a
build that skipped the self-check is distinguishable (§N.8); the flag is refused for any test_slice or measuring run
(there the in-build verify is the only producer of STRETCH_SINK/1). The deferral is safe because the in-build verify
persists nothing (writer `verify:<class>`: "the builder NEVER persists a verification row", R9-6.1) and the separate
job re-derives the same inventory / ledger / contact-geometry digests before it writes the 1206 and 1240 rows
(`services/gochara_kernel/verification_job.py:_verify_class`).

What this file proves (each claim fails on its single planted reversion):

  C1 final shape + flag: `verify:<class>` is the named no-op — nothing re-derived (the inventory digest is NOT
     recomputed), nothing persisted — and the candidate manifest's vector carries `in_build_verify` (DB, real chain);
  C2 flag absent: `verify:<class>` runs as today — the inventory digest IS re-derived — and the vector carries no
     `in_build_verify` key (byte-identical to a build before the flag) (DB, real chain);
  C3 §N.8 binding: a run whose flag disagrees with its manifest drifts by name at the next substep (DB, real chain);
  C4 the plan is unchanged by the flag: 298 substeps, the same keys and labels as the golden plan;
  C5 the flag is refused under every test-slice run shape, the measuring build (`all_classes_full`) included;
  C6 the flag is refused for a build that is not on the final rules ("final builds only");
  C7 a non-boolean flag value is refused, never coerced.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import input_vector as iv

from .test_a53_am5_writer import make_ephe
from .test_a53_inventory import CHART_ID, H0, H1, create_am5_database, drop_am5_database
from .test_c46_v5_test_slice import GOLDEN_PLAN_DIGEST, GOLDEN_PLAN_STEPS, _ctx as _slice_ctx, _marker

MIGRATIONS = Path(__file__).resolve().parents[4] / "migrations"
GEN = writer_mod.GENERATION
FLAG = writer_mod.DEFER_VERIFY_KEY
CLASS = "marriage"          # not an ND-H class: its selection is the same under the final rules


def _plan(ctx):
    steps = writer_mod.GocharaV5Writer().plan_substeps(ctx)
    canon = json.dumps([[s.key, s.label] for s in steps], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return steps, hashlib.sha256(canon.encode("utf-8")).hexdigest()


# ── C4: the plan never changes ──────────────────────────────────────────────────────────────────────────────────────

def test_c4_the_flag_leaves_the_plan_byte_identical_298_substeps_verify_included():
    steps, digest = _plan(_slice_ctx(None, gochara_v5_final_rules=True, result_policy="all_null_candidate/1", **{FLAG: True}))
    assert len(steps) == GOLDEN_PLAN_STEPS == 298
    assert digest == GOLDEN_PLAN_DIGEST
    assert sum(s.key.startswith(writer_mod.VERIFY_SUBSTEP_PREFIX) for s in steps) == len(writer_mod.SCORED_CLASSES)


# ── C5 / C6 / C7: refusals ──────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("run", writer_mod.TEST_SLICE_RUNS)
def test_c5_the_flag_is_refused_under_every_test_slice_run_shape_the_measuring_build_included(run):
    """The measuring build (`all_classes_full`) and both older shapes: the in-build verify is the only producer of the
    stretch sink there (DESIGN_NOTE_W3 §C.3), so the flag is a hard error, never a skip."""
    slice_ = writer_mod.TestSlice(run=run, horizon=(H0, H1), classes=(CLASS,), digest="ab" * 32, marker={})
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None,
                      config={"chart_id": CHART_ID, FLAG: True})
    with pytest.raises(writer_mod.DeferVerifyRefusal, match="defer_verify_refused_for_test_slice"):
        writer_mod._defer_in_build_verify(ctx, slice_)


def test_c5_a_marked_run_is_refused_at_plan_time():
    ctx = _slice_ctx({writer_mod.TEST_SLICE_KEY: _marker()}, **{FLAG: True})
    with pytest.raises(writer_mod.DeferVerifyRefusal, match="defer_verify_refused_for_test_slice"):
        writer_mod.GocharaV5Writer().plan_substeps(ctx)


def test_c6_the_flag_is_refused_for_a_build_that_is_not_on_the_final_rules():
    with pytest.raises(writer_mod.DeferVerifyRefusal, match="defer_verify_requires_final_rules"):
        writer_mod.GocharaV5Writer().plan_substeps(_slice_ctx(None, **{FLAG: True}))


@pytest.mark.parametrize("value", [1, 0, "true", "false", None, [True]])
def test_c7_a_non_boolean_flag_value_is_refused_never_coerced(value):
    with pytest.raises(writer_mod.DeferVerifyRefusal, match="must be a boolean"):
        writer_mod.GocharaV5Writer().plan_substeps(_slice_ctx(None, gochara_v5_final_rules=True, result_policy="all_null_candidate/1", **{FLAG: value}))


def test_absent_and_false_are_the_default_path():
    for config in ({}, {FLAG: False}):
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None, config={"chart_id": CHART_ID, **config})
        assert writer_mod._defer_in_build_verify(ctx, None) is False
        assert writer_mod._verify_component(False) is None


def test_the_component_is_omitted_from_a_default_vector_and_present_when_deferred(monkeypatch):
    base = {"stored_scope": iv.STORED_SCOPE, "result_policy": iv.DEFAULT_RESULT_POLICY, "sky_id": "s", "sky_vector": {},
            "registry": {"census": []}, "node": {}, "ephemeris": {"files": {}}, "admission_orb": {}, "activity_orb": {},
            "rulings": [], "impl_modules": {}}
    monkeypatch.setattr(iv, "registry_digest_of", lambda rows: "d")
    monkeypatch.setattr(iv, "_ephemeris_component", lambda inp: {})
    assert "in_build_verify" not in iv.assemble_vector(base)
    assert "in_build_verify" not in iv.assemble_vector({**base, "in_build_verify": writer_mod._verify_component(False)})
    assert iv.assemble_vector({**base, "in_build_verify": writer_mod._verify_component(True)})["in_build_verify"] == {
        "schema": "gochara_v5_in_build_verify/1", "status": "deferred_to_independent_verification"}


# ── C1 / C2 / C3 on a real disposable database: the writer's own substeps, production code ──────────────────────────

@pytest.fixture()
def am5():
    import psycopg
    admin, name, dsn = create_am5_database("w3defer")
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        # a FINAL build consumes the P1 Form B L0 tables (dignity, combustion orbs, naisargika friendship), and the evaluation-stage independent derivation of each (od1-l0verify) reads
        # them from the database: seed them from the REAL migrations, as test_od1_l0verify does, never from a stand-in
        for migration in ("250_bg_dignity_reference.sql", "1401_l0_node_dignity_friendship.sql"):
            conn.execute((MIGRATIONS / migration).read_text(encoding="utf-8"))
        yield conn
    finally:
        conn.close()
        drop_am5_database(admin, name)


@pytest.fixture()
def chain(am5, monkeypatch, tmp_path):
    """One substep = one transaction, like the orchestrator; only the Swiss probe is faked. `step(key, **config)` runs
    one substep of a FINAL build (gochara_v5_final_rules true) with the extra config given; the rule catalogue is
    seeded by the writer's own `rules` substep under the same profile."""
    ephe = make_ephe(tmp_path, monkeypatch)
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
    derivations = []
    real = writer_mod.gk_verifier.rederive_inventory_digest

    def spy(*a, **k):
        derivations.append(k.get("event_class"))
        return real(*a, **k)

    monkeypatch.setattr(writer_mod.gk_verifier, "rederive_inventory_digest", spy)
    w = writer_mod.GocharaV5Writer()

    def step(key, **config):
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-w3", db_conn=am5,
                          config={"chart_id": CHART_ID, "horizon": (H0, H1), "ephe_path": ephe,
                                  "gochara_v5_final_rules": True, "result_policy": "all_null_candidate/1", **config}, dry_run=False)
        with am5.transaction():
            return w.run_substep(ctx, SubStep(key=key, label=key))

    def head(**config):
        for k in (writer_mod.RULES_SUBSTEP, writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP,
                  writer_mod.SNAPSHOT_SUBSTEP, f"inventory:{CLASS}"):
            step(k, **config)
    return step, head, am5, derivations


def _vector(conn):
    from services.gochara_kernel.inventory_store import InventoryStore
    return InventoryStore(conn).manifest_vector(CHART_ID, GEN)


def _verification_rows(conn) -> int:
    return conn.execute("SELECT count(*) FROM public.ka_gochara_search_inventory_verification").fetchone()[0]


def test_c1_final_build_with_the_flag_returns_the_named_no_op_and_the_manifest_records_it(chain):
    step, head, conn, derivations = chain
    head(**{FLAG: True})
    assert _vector(conn)["in_build_verify"] == {"schema": writer_mod.DEFER_VERIFY_SCHEMA,
                                                "status": "deferred_to_independent_verification"}
    res = step(f"verify:{CLASS}", **{FLAG: True})
    assert res.notes.startswith(f"verify {CLASS}: deferred_to_independent_verification")
    assert res.rows_inserted == 0
    assert derivations == []                    # the self-check did not run: no inventory digest re-derived
    assert _verification_rows(conn) == 0


def test_c2_without_the_flag_verify_runs_as_today_and_the_vector_has_no_component(chain):
    """Flag absent: the inventory digest is re-derived (then, as on main in this fixture, the contact-geometry
    certification refuses a class whose contacts were never materialised — the self-check really ran)."""
    step, head, conn, derivations = chain
    head()
    assert "in_build_verify" not in _vector(conn)
    with pytest.raises(RuntimeError, match="contact geometry certification failed"):
        step(f"verify:{CLASS}")
    assert derivations == [CLASS]


def test_c3_a_run_whose_flag_disagrees_with_its_manifest_drifts_by_name(chain):
    """§N.8: the no-op is reachable only when the manifest records the deferral — a flag switched on after the manifest
    (or switched off) is a named drift of `in_build_verify`, never a silent skip of the self-check."""
    step, head, conn, derivations = chain
    head()
    with pytest.raises(iv.InputDrift, match="in_build_verify"):
        step(f"verify:{CLASS}", **{FLAG: True})
    assert derivations == []


def test_c3_a_deferring_manifest_refuses_a_run_that_drops_the_flag(chain):
    step, head, conn, derivations = chain
    head(**{FLAG: True})
    with pytest.raises(iv.InputDrift, match="in_build_verify"):
        step(f"verify:{CLASS}")
