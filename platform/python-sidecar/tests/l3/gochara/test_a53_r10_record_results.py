"""A5.3 — Codex round 10, R10-2: record results escape neither the all-NULL policy nor freshness.

1155 permits finite numbers in `evidence_for_occurrence` / `evidence_against_occurrence` / `severity` and qualified valence
tokens on a relationship record. Now (a) the independent verifier refuses any such value before it persists, (b) 1240's
seal gate refuses it at the seal (`record_result_not_policy`), and (c) the inputs-digest preimage ('inputs/2', Python ==
SQL) covers the complete semantic dependency set — record results, provenance, ruling, frame, person, support state, and
EVERY contact of the generation (a contact whose records were all removed is still a dependency) — so Codex's attack (after
verification, delete + reinsert the same record id with evidence_for_occurrence = 1, restore its prerequisites/memberships,
retain every previously hashed field) is refused at the seal."""
from __future__ import annotations

from services.gochara_kernel import verification_job as vj
from services.gochara_kernel import window_gate as wg

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, _t
from .test_a53_r10_complete_records import (CLS, LIBRA, _bypass, _job_position, _kwargs, _run, _stage,  # noqa: F401
                                            _verification_rows, built, login, rworld)
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401


def _gate(w):
    return {(r[1], r[3]) for r in w.conn.execute(
        "SELECT * FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall()}


def _grain(path="P3"):
    return dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=path, rule_version="1.0.0")


def _verified(w):
    report = _run(w)
    assert report["status"] == "VERIFIED" and report["gate"] == [], report["classes"]
    return report


def test_a_numeric_record_result_is_refused_by_the_verifier_before_it_persists(built):
    w = built
    _bypass(w, ("UPDATE public.ka_gochara_relationship_record SET evidence_for_occurrence = 1 WHERE path_id = 'P3'"
                " AND contact_id IS NOT NULL", ()))
    report = _run(w)
    status, stage, detail = _stage(report)
    # R11-1: the GENERATION-WIDE check (run first, under the locks) catches it before the per-grain record derivation does
    assert (status, stage) == ("DISAGREE", "generation_output") and "numeric result" in detail, report["classes"]
    assert _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}


def test_a_qualified_valence_or_severity_is_refused_by_the_verifier(built):
    w = built
    _bypass(w, ("UPDATE public.ka_gochara_relationship_record SET outcome_valence_for_native = 'adverse', severity = 0.5"
                " WHERE path_id = 'P4' AND contact_id IS NOT NULL", ()))
    status, stage, detail = _stage(_run(w))
    assert (status, stage) == ("DISAGREE", "generation_output") and "numeric result or a qualified valence" in detail


def test_the_seal_gate_refuses_a_numeric_record_result_in_the_database(built):
    w = built
    _verified(w)
    assert _gate(w) == set()
    _bypass(w, ("UPDATE public.ka_gochara_relationship_record SET evidence_against_occurrence = 2 WHERE path_id = 'P3'"
                " AND contact_id IS NOT NULL", ()))
    assert ("P3", "record_result_not_policy") in _gate(w)


def test_codexs_attack_delete_and_reinsert_the_same_record_with_a_number_is_refused_at_the_seal(built):
    """After verification: copy the record and its prerequisites and memberships aside, delete them, reinsert the SAME record
    id with evidence_for_occurrence = 1 and restore the rest — every field the old preimage hashed is unchanged."""
    w = built
    _verified(w)
    assert _gate(w) == set()
    rid = w.conn.execute("SELECT record_id FROM public.ka_gochara_relationship_record WHERE path_id = 'P3'"
                         " AND contact_id IS NOT NULL").fetchone()[0]
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("CREATE TEMP TABLE _r AS SELECT * FROM public.ka_gochara_relationship_record WHERE record_id = %s", (rid,))
        w.conn.execute("CREATE TEMP TABLE _p AS SELECT * FROM public.ka_gochara_record_prerequisite WHERE record_id = %s", (rid,))
        w.conn.execute("CREATE TEMP TABLE _m AS SELECT * FROM public.ka_gochara_eval_window_record WHERE record_id = %s", (rid,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_record WHERE record_id = %s", (rid,))
        w.conn.execute("DELETE FROM public.ka_gochara_record_prerequisite WHERE record_id = %s", (rid,))
        w.conn.execute("DELETE FROM public.ka_gochara_relationship_record WHERE record_id = %s", (rid,))
        w.conn.execute("UPDATE _r SET evidence_for_occurrence = 1")
        w.conn.execute("INSERT INTO public.ka_gochara_relationship_record SELECT * FROM _r")
        w.conn.execute("INSERT INTO public.ka_gochara_record_prerequisite SELECT * FROM _p")
        w.conn.execute("INSERT INTO public.ka_gochara_eval_window_record SELECT * FROM _m")
    got = _gate(w)
    assert ("P3", "window_verification_inputs_changed") in got and ("P3", "record_result_not_policy") in got, got


import pytest


@pytest.mark.parametrize("assignment", [
    "provenance = 'uncited_extension', ruling_ref = 'D-FAKE'",
    "affected_person = 'father'",
    "frame_kind = 'bhavat_bhavam', frame_arg = '9'",
    "operator_role = 'testimony', provenance = 'uncited_extension', ruling_ref = 'D-PADMIT'",
])
def test_the_inputs_digest_covers_provenance_ruling_frame_person_and_role(built, assignment):
    w = built
    _verified(w)
    _bypass(w, (f"UPDATE public.ka_gochara_relationship_record SET {assignment} WHERE path_id = 'P3'"
                " AND contact_id IS NOT NULL", ()))
    assert ("P3", "window_verification_inputs_changed") in _gate(w), assignment


def test_a_contact_with_no_surviving_record_is_still_a_dependency(built):
    """The old preimage listed only contacts a surviving record referenced. A contact whose records were all removed (or any
    contact field the certification reads, e.g. delta_lambda) now changes the digest."""
    w = built
    _verified(w)
    assert _gate(w) == set()
    _bypass(w, ("UPDATE public.ka_gochara_contact SET delta_lambda = 0.5 WHERE body = 'saturn'", ()))
    assert ("P3", "window_verification_inputs_changed") in _gate(w)


def test_python_and_sql_inputs_digests_agree_with_numbers_provenance_and_an_unreferenced_contact(built):
    w = built
    # an UNREFERENCED contact: delete a record's links so a contact has no record at all, then give a record numbers
    _bypass(w,
            ("UPDATE public.ka_gochara_relationship_record SET evidence_for_occurrence = 0.1, severity = 2.5,"
             " outcome_valence_for_native = 'mixed', provenance = 'uncited_extension', ruling_ref = 'X'"
             " WHERE path_id = 'P3' AND contact_id IS NOT NULL", ()))
    for path in ("P1", "P2", "P3", "P4"):
        grain = _grain(path)
        py = wg.derivation_inputs_digest(w.conn, **grain)
        sql = w.conn.execute("SELECT public.ka_gochara_eval_window_inputs_digest(%s::uuid, %s, %s, %s, %s)",
                             (CHART_ID, GEN, CLS, path, "1.0.0")).fetchone()[0]
        assert py == sql, path
    pre = wg.derivation_inputs_preimage(w.conn, **_grain("P3"))
    assert pre["version"] == "inputs/2" and any(r["evidence_for"] is not None for r in pre["records"])
    assert len(pre["contacts"]) >= 1
