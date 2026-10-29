"""N2-ORDINARY-SANGAM-CASCADE: an ordinary (candidate-unbound) ka_sangam rebuild before any published head must not cascade served children.

The defect. SR-K9-BIND B1b refuses an unbound rebuild once a head is published. Before that, the 'legacy' partition of kala_convergence IS the served
copy, and ka_sangam's delete-then-insert (root CLAUDE.md §N.3) gives every row a new convergence_id, so the foreign keys onto kala_convergence
(kala_darshana, kala_obstruction, phala_anchors ON DELETE CASCADE; kala_bhavishya ON DELETE SET NULL; production readback
k9-fk-cascade-readback-20261022T0710Z, migrations 245 / 247 / 363 / 249) silently destroyed the served children. The actions stay CASCADE (migrations
1405 / 1406); the writer now refuses, deleting nothing, when the rows it would replace still have referencing rows (UnboundRewriteCascades).

Claims, one oracle each, each with ONE planted reversion that fails (``BOTH``; root CLAUDE.md §N.8):

  N2a an unbound rebuild with no head REFUSES, with a named reason, when served legacy rows have children in any cascaded table; the legacy rows and
      every child stay byte-identical (B.10: nothing is silently dropped; §N.3: a rebuild replaces only what nothing depends on)
  N2b an unbound rebuild with no head and legacy rows that nothing references still REPLACES them (the guard measures references, not mere presence)
  N2c planning refuses first, read-only, before any ledger or delete
"""
from types import SimpleNamespace

import pytest

from services.kala_core import writer_grain
from tests.l3.kala_db.ka_sangam.test_k9_convergence_scope import (  # noqa: F401  (world is a fixture)
    CHART, NEAR, LIFETIME, apply, build, conv, conv_ids, dump, generations, real_writer, served_world, world)
from tests.l3.kala_db.manifest.test_k9_publication_hardening import BOTH, mutated  # noqa: F401
from tests.l3.kala_db.manifest.test_publication_ops import db  # noqa: F401  (a fixture)
from tests.l3.kala_db.manifest.test_rebuild_control import ctl  # noqa: F401  (a fixture)


def patched(monkeypatch, copy):
    from pipeline.orchestrator.writers import ka_sangam
    monkeypatch.setattr(ka_sangam, 'convergence_generation', copy.convergence_generation)
    monkeypatch.setattr(ka_sangam, 'refuse_unbound_cascade', copy.refuse_unbound_cascade)


def oracle_refuses_with_children(conn):
    legacy_ids = served_world(conn)
    before = dump(conn, 'legacy')
    try:
        build(conn, real_writer(), None, bind=False)
    except writer_grain.UnboundRewriteCascades as exc:
        conn.rollback()
        assert writer_grain.UNBOUND_REWRITE_CASCADES in str(exc), 'the refusal names its reason'
        assert dump(conn, 'legacy') == before, 'a refusal changed a served convergence row or a child of one'
        assert conv_ids(conn, CHART, 'legacy') == legacy_ids
        return
    raise AssertionError('an unbound rebuild cascaded into served children')


@BOTH
def test_n2a_unbound_rebuild_with_served_children_is_refused_and_changes_nothing(world, tmp_path, reverted, monkeypatch):
    apply(world)
    if not reverted:
        return oracle_refuses_with_children(world)
    # reversion: the guard is removed (the pre-N2 behaviour: delete-then-insert cascades)
    copy = mutated(writer_grain, tmp_path, "    if reach:\n        raise UnboundRewriteCascades(", "    if False:\n        raise UnboundRewriteCascades(")
    patched(monkeypatch, copy)
    with pytest.raises(AssertionError, match='cascaded into served children|changed a served'):
        oracle_refuses_with_children(world)


def oracle_replaces_unreferenced(conn):
    old = [conv(conn, generation='legacy'), conv(conn, generation='legacy', tier='lifetime', peak=LIFETIME[0]['peak_date'])]
    conn.commit()
    build(conn, real_writer(), None, bind=False)
    conn.commit()
    new = conv_ids(conn, CHART, 'legacy')
    assert len(new) == len(NEAR) + len(LIFETIME), 'a rebuild replaces the rows, never accretes them'
    assert not set(new) & set(old), 'the unreferenced old rows were replaced'
    assert generations(conn) == ['legacy']


@BOTH
def test_n2b_unbound_rebuild_still_replaces_legacy_rows_that_nothing_references(world, tmp_path, reverted, monkeypatch):
    apply(world)
    if not reverted:
        return oracle_replaces_unreferenced(world)
    # reversion: the guard refuses on the mere presence of legacy rows (a proxy, not a measurement of references)
    copy = mutated(writer_grain, tmp_path, "    reach = served_children_reach(conn, chart_id, 'legacy')\n",
                   "    reach = [('kala_convergence', 'cascade', 1)] if conn.execute(\"SELECT 1 FROM kala_convergence WHERE chart_id = %s\", (chart_id,)).fetchone() else []\n")
    patched(monkeypatch, copy)
    with pytest.raises(ValueError, match=writer_grain.UNBOUND_REWRITE_CASCADES):      # the copy raises its own class of the refusal
        oracle_replaces_unreferenced(world)


def oracle_plan_refuses(conn):
    served_world(conn)
    before = dump(conn, 'legacy')
    ctx = SimpleNamespace(db_conn=conn, build_id=None, dry_run=False, config={'chart_id': CHART})
    try:
        real_writer()().plan_substeps(ctx)
    except writer_grain.UnboundRewriteCascades as exc:
        conn.rollback()
        assert writer_grain.UNBOUND_REWRITE_CASCADES in str(exc)
        assert dump(conn, 'legacy') == before
        return
    raise AssertionError('planning did not refuse')


@BOTH
def test_n2c_planning_refuses_before_any_ledger_or_delete(world, tmp_path, reverted, monkeypatch):
    from pipeline.orchestrator.writers import ka_sangam
    apply(world)
    if not reverted:
        return oracle_plan_refuses(world)
    # reversion: plan_substeps no longer calls the guard (only the per-substep check remains)
    monkeypatch.setattr(ka_sangam, 'refuse_unbound_cascade', lambda *a, **k: None)
    # the planner goes on to load predicates, which the stand-in database does not hold: it fails there, not at the guard
    with pytest.raises(Exception) as caught:
        oracle_plan_refuses(world)
    assert not isinstance(caught.value, writer_grain.UnboundRewriteCascades), 'the planner still refused'
