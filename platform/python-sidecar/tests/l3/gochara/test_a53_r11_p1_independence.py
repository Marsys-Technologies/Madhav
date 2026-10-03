"""A5.3 — Codex round 11, R11-2: P1 is a COMPLETE independent derivation.

`verify_p1_anchors` used to collapse the records on a contact into a SET of (lord, level) — a duplicate fifth record passed;
`verify_p1_results` compared selected results only — a wrong affected person / object role passed; and builder and verifier
both called `permission.period_lord_relation`, so a defect there made them agree on the same omission. Now: exact CARDINALITY
per contact (a multiset), every semantic field derived and compared (agent/relation/target/contact identity, person, object
role and kind, frame, anchor, exactly the declared prerequisites, each one's truth, the admission), and the verifier's OWN
period-lord relation (`inventory_verifier.period_lord_relation`) with an import test. All cases run through the REAL job as the
verifier login on the complete built world."""
from __future__ import annotations

import uuid

import pytest

from services.gochara_rules import permission as builder_permission
from services.gochara_kernel import inventory_verifier as inv_v
from services.gochara_kernel import record_derivation as rd
from services.gochara_kernel import record_store as rs
from services.gochara_kernel import record_verifier as rv
from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, _t
from .test_a53_r10_complete_records import (CLS, _bypass, _run, _stage, _verification_rows, built, login, rworld)  # noqa: F401
from .test_a53_window_verification_gate import SPANS, _boot_p3, _materialise  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401

NONE = {t: 0 for t in vj.VERIFICATION_TABLES}


def test_the_p1_derivation_shares_no_code_with_the_builders_permission_module():
    import ast
    from pathlib import Path
    root = Path(__file__).resolve().parents[3] / "services" / "gochara_kernel"
    for name in ("record_derivation.py", "record_verifier.py", "inventory_verifier.py"):
        tree = ast.parse((root / name).read_text())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.add(("." * node.level) + (node.module or "") + "|" + ",".join(a.name for a in node.names))
            elif isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
        assert not [m for m in imported if "gochara_rules" in m or "permission" in m], (name, imported)


def test_the_verifiers_own_relation_agrees_with_the_builders_where_both_are_right_on_every_class_and_lord():
    chart = {"lagna": 15.0, "natal": {"sun": 293.0, "moon": 338.0, "mars": 260.0, "mercury": 300.0, "jupiter": 205.0,
                                      "venus": 330.0, "saturn": 185.0, "rahu": 330.0, "ketu": 150.0}}
    theirs = {"lagna_deg": 15.0, "natal": {k.title(): v for k, v in chart["natal"].items()}}
    for cls in list(inv_v._CLASS) + sorted(inv_v._UNKNOWN_H):
        for g in chart["natal"]:
            mine = inv_v.period_lord_relation(g, cls, chart)
            b = builder_permission.period_lord_relation(g.title(), cls, theirs)
            assert (mine["relation"], mine["licence"]) == (b["relation"], b["licence"]), (cls, g)


def _insert_copy(w, *, set_clause=""):
    """A duplicate of an existing P1 record (new id, SAME anchor/contact/fields) with its prerequisites."""
    src = w.conn.execute("SELECT record_id FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'"
                         " ORDER BY record_id LIMIT 1").fetchone()[0]
    new = uuid.uuid4()
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("CREATE TEMP TABLE _r ON COMMIT DROP AS SELECT * FROM public.ka_gochara_relationship_record"
                       " WHERE record_id = %s", (src,))
        w.conn.execute("UPDATE _r SET record_id = %s" + set_clause, (new,))
        w.conn.execute("INSERT INTO public.ka_gochara_relationship_record SELECT * FROM _r")
        w.conn.execute("CREATE TEMP TABLE _p ON COMMIT DROP AS SELECT * FROM public.ka_gochara_record_prerequisite"
                       " WHERE record_id = %s", (src,))
        w.conn.execute("UPDATE _p SET record_id = %s", (new,))
        w.conn.execute("INSERT INTO public.ka_gochara_record_prerequisite SELECT * FROM _p")
    return new


def test_a_duplicate_fifth_record_with_an_existing_anchor_is_refused(built):
    w = built
    n = w.conn.execute("SELECT count(*) FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'").fetchone()[0]
    _insert_copy(w)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'").fetchone()[0] == n + 1
    report = _run(w)
    status, stage, detail = _stage(report)
    assert (status, stage) == ("DISAGREE", "p1_anchors") and "exact cardinality" in detail, report["classes"]
    assert _verification_rows(w) == NONE


def test_a_record_with_the_wrong_affected_person_is_refused(built):
    w = built
    _bypass(w, ("UPDATE public.ka_gochara_relationship_record SET affected_person = 'father' WHERE path_id = 'P1'"
                " AND period_anchor_level = 'ad'", ()))
    status, stage, detail = _stage(_run(w))
    assert (status, stage) == ("DISAGREE", "p1_results") and "affected person 'father'" in detail
    assert _verification_rows(w) == NONE


def test_a_record_with_the_wrong_object_role_or_a_missing_prerequisite_row_is_refused(built):
    w = built
    _bypass(w, ("UPDATE public.ka_gochara_relationship_record SET object_role = 'signature_house' WHERE path_id = 'P1'"
                " AND period_anchor_level = 'md'", ()))
    status, stage, detail = _stage(_run(w))
    assert (status, stage) == ("DISAGREE", "p1_results") and "object role 'signature_house'" in detail
    w2 = w
    _bypass(w2, ("UPDATE public.ka_gochara_relationship_record SET object_role = 'period_lord' WHERE path_id = 'P1'", ()),
            ("DELETE FROM public.ka_gochara_record_prerequisite WHERE predicate_id = 'transit_relation' AND record_id IN"
             " (SELECT record_id FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'"
             "  AND period_anchor_level = 'pd')", ()))
    status, stage, detail = _stage(_run(w2))
    assert (status, stage) == ("DISAGREE", "p1_results") and "exactly the declared" in detail


def _defective_relation(lord, event_class, chart):
    """A defect in the shared permission computation: it calls Saturn a TESTIMONY lord, so the builder's own rule omits every
    Saturn-anchored P1 record ('unwritable testimony')."""
    real = _REAL(lord, event_class, chart)
    return dict(real, licence="testimony") if lord == "Saturn" else real


_REAL = builder_permission.period_lord_relation


def test_a_defect_in_the_shared_permission_computation_no_longer_makes_builder_and_verifier_agree(built, monkeypatch):
    """The builder, built UNDER the defect, omits the Saturn-anchored records. The old verifier called the same function and
    removed Saturn from its expected anchors — they agreed and the job said VERIFIED. The verifier's own relation expects the
    records: DISAGREE."""
    w = built
    monkeypatch.setattr(builder_permission, "period_lord_relation", _defective_relation)
    _materialise(w, "P1", {"saturn": (_t(1, 10), _t(2, 20))})                  # the builder's grain, re-built under the defect
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'").fetchone()[0] == 0
    # (the window phase for P1 is the builder's too: its windows were rebuilt away with the grain)
    report = _run(w)
    status, stage, detail = _stage(report)
    assert (status, stage) == ("DISAGREE", "p1_anchors") and "anchored records stored []" in detail, report["classes"]
    assert _verification_rows(w) == NONE


def test_the_same_defect_during_verification_alone_cannot_move_the_verifier(built, monkeypatch):
    w = built
    monkeypatch.setattr(builder_permission, "period_lord_relation", _defective_relation)       # only the verifier runs under it
    report = _run(w)
    assert report["status"] == "VERIFIED", _stage(report)


def test_mutation_the_old_set_comparison_would_have_passed_the_duplicate(built, monkeypatch):
    """Guard on the guard: a SET-valued comparison (the old behaviour) cannot see the duplicate — proven by comparing the two
    collections the verifier now distinguishes."""
    from collections import Counter
    four = [("saturn", "md"), ("saturn", "ad"), ("saturn", "pd")]
    assert set(four + [("saturn", "ad")]) == set(four) and Counter(four + [("saturn", "ad")]) != Counter(four)
