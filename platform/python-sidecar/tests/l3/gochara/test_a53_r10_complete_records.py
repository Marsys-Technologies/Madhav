"""A5.3 — Codex round 10, R10-1: expected RECORDS are derived independently, never inferred from surviving output.

Every case runs the REAL `verification_job.run` as the verifier LOGIN over a COMPLETE built world (the builder's own
materialisation: Saturn's Libra residence is a P1 reading under three anchors, a P3 record with the māraka testimony rows,
and a P4 record). The mutations are made on that world AFTER the build, with trigger-bypassing superuser SQL (the database's
own F5/FK guards are a separate defence); the independent verifier must refuse each, naming the stage, and persist nothing.
The pre-fix job returned VERIFIED for the whole-P1 omission (it skipped `verify_p1_anchors` when no anchored record
survived) and derived the expected windows from the stored records, so a whole-P3 omission passed too."""
from __future__ import annotations

import pytest

# G8: this suite is NOT about the class census; it opts out BY NAME (see conftest.g8_census_opt_out and the guard in test_g8_class_census.py).
G8_CENSUS_OPT_OUT_REASON = "exercises complete-record derivation (an underivable path is UNVERIFIED, never a pass) on a deliberate one-class marriage world"
pytestmark = pytest.mark.usefixtures("g8_census_opt_out")

from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_verification_job import (BUILDER, _counts, _job_position, _kwargs, built, login, rworld)  # noqa: F401
from .test_a53_window_verification_gate import CLS, SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401
from .test_a53_p1_support import _t

LIBRA = (_t(1, 10), _t(2, 20))


def _run(w):
    with login(w, "gochara_verifier") as conn:
        return vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(w, _job_position(w, [LIBRA])))


def _bypass(w, *statements):
    """Post-build tampering by a trigger-bypassing superuser (the database guards are the OTHER defence)."""
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        for sql, params in statements:
            w.conn.execute(sql, params)


def _stage(report):
    c = report["classes"][CLS]
    return c.get("status"), c.get("stage"), c.get("detail", "")


def _verification_rows(w):
    return _counts(w.conn, vj.VERIFICATION_TABLES)


def test_the_unmutated_complete_world_is_verified(built):
    report = _run(built)
    assert report["status"] == "VERIFIED", report["classes"]


def test_a_whole_p1_omission_is_refused_by_the_real_job_not_skipped(built):
    w = built
    _bypass(w,
            ("DELETE FROM public.ka_gochara_record_prerequisite WHERE record_id IN"
             " (SELECT record_id FROM public.ka_gochara_relationship_record WHERE path_id = 'P1')", ()),
            ("DELETE FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'", ()))
    report = _run(w)
    status, stage, detail = _stage(report)
    assert (status, stage) == ("DISAGREE", "p1_anchors") and "anchored records stored []" in detail, report["classes"]
    assert report["status"] == "DISAGREE" and report["exit_code"] == vj.EXIT_DISAGREE
    assert _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}          # nothing persisted


def test_a_whole_p3_omission_with_its_windows_is_refused(built):
    w = built
    _bypass(w,
            ("DELETE FROM public.ka_gochara_eval_window_record WHERE window_id IN"
             " (SELECT window_id FROM public.ka_gochara_eval_window WHERE path_id = 'P3')", ()),
            ("DELETE FROM public.ka_gochara_eval_window WHERE path_id = 'P3'", ()),
            ("DELETE FROM public.ka_gochara_record_prerequisite WHERE record_id IN"
             " (SELECT record_id FROM public.ka_gochara_relationship_record WHERE path_id = 'P3')", ()),
            ("DELETE FROM public.ka_gochara_relationship_record WHERE path_id = 'P3'", ()))
    report = _run(w)
    status, stage, detail = _stage(report)
    assert (status, stage) == ("DISAGREE", "records P3") and "is not stored" in detail, report["classes"]
    assert _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}


def test_a_whole_contact_omission_is_refused(built):
    w = built
    cid = w.conn.execute(
        "SELECT contact_id::text FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o"
        " ON o.physical_object_id = c.physical_object_id WHERE c.body = 'saturn' AND c.relation_kind = 'residence'"
        " AND o.canonical_target = 'span:7'").fetchone()[0]
    _bypass(w,
            ("DELETE FROM public.ka_gochara_eval_window_record WHERE record_id IN"
             " (SELECT record_id FROM public.ka_gochara_relationship_record WHERE contact_id = %s::uuid)", (cid,)),
            ("DELETE FROM public.ka_gochara_eval_window", ()),
            ("DELETE FROM public.ka_gochara_record_prerequisite WHERE record_id IN"
             " (SELECT record_id FROM public.ka_gochara_relationship_record WHERE contact_id = %s::uuid)", (cid,)),
            ("DELETE FROM public.ka_gochara_relationship_record WHERE contact_id = %s::uuid", (cid,)),
            ("DELETE FROM public.ka_gochara_contact WHERE contact_id = %s::uuid", (cid,)))
    report = _run(w)
    assert report["classes"][CLS]["status"] == "DISAGREE", report["classes"]
    assert _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}


def test_a_wrong_prerequisite_result_with_a_consistent_admission_is_refused(built):
    """The database's F5 finalisation only requires the admission to match the stored results; it cannot know the stored
    RESULT is wrong. The independent derivation can."""
    w = built
    _bypass(w,
            ("UPDATE public.ka_gochara_record_prerequisite SET result = 'false' WHERE predicate_id ="
             " 'p3_contact_house_or_lord' AND record_id IN (SELECT record_id FROM public.ka_gochara_relationship_record"
             " WHERE path_id = 'P3' AND contact_id IS NOT NULL)", ()),
            ("UPDATE public.ka_gochara_relationship_record SET admission_state = 'not_admitted'"
             " WHERE path_id = 'P3' AND contact_id IS NOT NULL", ()))
    report = _run(w)
    status, stage, detail = _stage(report)
    assert (status, stage) == ("DISAGREE", "records P3") and "p3_contact_house_or_lord" in detail, report["classes"]
    assert _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}


def test_a_wrong_admission_is_refused(built):
    w = built
    _bypass(w, ("UPDATE public.ka_gochara_relationship_record SET admission_state = 'unqualified'"
                " WHERE path_id = 'P3' AND contact_id IS NOT NULL", ()))
    report = _run(w)
    status, stage, detail = _stage(report)
    assert (status, stage) == ("DISAGREE", "records P3") and "admission" in detail, report["classes"]


def test_a_wrong_p1_natal_relationship_result_is_refused(built):
    w = built
    _bypass(w,
            ("UPDATE public.ka_gochara_record_prerequisite SET result = 'unknown' WHERE predicate_id ="
             " 'natal_bhava_relationship' AND record_id IN (SELECT record_id FROM public.ka_gochara_relationship_record"
             " WHERE path_id = 'P1')", ()),
            ("UPDATE public.ka_gochara_relationship_record SET admission_state = 'unqualified' WHERE path_id = 'P1'", ()))
    report = _run(w)
    status, stage, detail = _stage(report)
    assert (status, stage) == ("DISAGREE", "p1_results") and "natal_bhava_relationship" in detail, report["classes"]


def test_the_record_derivation_imports_nothing_from_the_builder():
    """Steward M…111803: the verifier-own derivation shares nothing with the builder beyond L0/L1 data and the sealed
    registry rows it reads — it imports nothing from evaluator / record_store / the writer / the rule-admission modules."""
    import ast
    from pathlib import Path
    src = (Path(__file__).resolve().parents[3] / "services" / "gochara_kernel" / "record_derivation.py").read_text()
    imported = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom):
            imported.add(("." * node.level) + (node.module or ""))
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    forbidden = ("evaluator", "record_store", "ka_gochara_v5", "rule_registry", "substrate", "targets", "materialise",
                 "gochara_rules.admission", "gochara_rules.registry", "gochara_rules.favourable_houses",
                 "gochara_rules.predicates")
    bad = {m for m in imported if any(f in m for f in forbidden)}
    assert not bad, f"the record derivation must be independent of the builder: {bad}"
    # R11-2: it shares NO rule computation with the builder either — the P1 period-lord relation is the verifier's own
    assert not {m for m in imported if "gochara_rules" in m}, imported


def test_a_path_whose_records_cannot_be_derived_is_UNVERIFIED_never_a_pass(built, monkeypatch):
    """A declared prerequisite with no independent derivation in the verifier ⇒ the class is UNVERIFIED (gate closed,
    nothing persisted) — an explicit result, not a disagreement and not a pass."""
    from services.gochara_kernel import record_derivation as rd
    real = rd.declared_predicates
    monkeypatch.setattr(rd, "declared_predicates",
                        lambda conn, path_id, version: real(conn, path_id, version) + (
                            ["a_predicate_the_verifier_cannot_derive"] if path_id == "P3" else []))
    w = built
    report = _run(w)
    c = report["classes"][CLS]
    assert c["status"] == "UNVERIFIED" and "no independent derivation" in c["reason"], c
    assert report["status"] == "NOT_VERIFIED" and _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}
