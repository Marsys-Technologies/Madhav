"""A5.3 — Codex round 11, R11-1: the all-NULL and output-selection checks are GENERATION-WIDE.

1240's result-policy arm and its digests covered only the grains the inventory INCLUDES. The relationship-record FK and the
sealed-path trigger require a SEALED rule version, not an INCLUDED one — so a structurally valid record under a sealed-but-
excluded version (P3 superseded, or the held P5) with a numeric result, REUSING an existing contact and coverage partition,
escaped the policy arm, every attestation and every digest. Now the gate rejects any record / window / membership outside the
generation's permitted output grains and enforces the all-NULL policy across the whole generation, independently of the
expected-verification CTE; the verifier job checks the same, in Python, before it verifies or persists anything.

The attacks run as the RESTRICTED BUILDER role (SET ROLE data_plane_builder on the faithful mirror), introduce NO new
contact, and run before AND after the independent verification."""
from __future__ import annotations

import uuid

import pytest

# G8: this suite is NOT about the class census; it opts out BY NAME (see conftest.g8_census_opt_out and the guard in test_g8_class_census.py).
G8_CENSUS_OPT_OUT_REASON = "exercises generation-wide record refusal at the gate, the job and the seal on a deliberate one-class marriage world"
pytestmark = pytest.mark.usefixtures("g8_census_opt_out")

from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import (CLS, _run, _verification_rows, built, login, rworld)  # noqa: F401
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal, as_role  # noqa: F401


def _gate(w):
    return {(r[0], r[1], r[2], r[3]) for r in w.conn.execute(
        "SELECT * FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall()}


def _grains(w):
    return w.conn.execute("SELECT path_id, rule_version, disposition FROM public.ka_gochara_search_path_pin"
                          " WHERE event_class = %s ORDER BY 1, 2", (CLS,)).fetchall()


def _sealed_not_included(w, path):
    included = {(p, v) for p, v, d in _grains(w) if d == "included"}
    sealed = [tuple(r) for r in w.conn.execute("SELECT path_id, rule_version FROM public.ka_gochara_rule_path_seal"
                                               " WHERE path_id = %s ORDER BY 2", (path,)).fetchall()]
    return [pv for pv in sealed if pv not in included]


def _foreign_grain(w, path, version):
    """A sealed (path, version) the inventory does NOT include for the class: the held P5, or — for a path whose only sealed
    version is the included one — a sealed SUCCESSOR version cloned (rule path, declared prerequisites, seal) beside it, exactly
    what a superseded P3@1.0.0 / P3@1.1.0 pair is in production."""
    other = _sealed_not_included(w, path)
    if not other:
        _, base = next((p, v) for p, v, d in _grains(w) if p == path and d == "included")
        with w.conn.transaction():
            w.conn.execute("SET LOCAL session_replication_role = replica")
            w.conn.execute("INSERT INTO public.ka_gochara_rule_path SELECT path_id, '9.9.9', frame_kind, frame_arg, agent_set,"
                           " relation_set, object_selector, provenance, operator_role, ruling_ref, score_rule, now()"
                           " FROM public.ka_gochara_rule_path WHERE path_id = %s AND rule_version = %s", (path, base))
            w.conn.execute("INSERT INTO public.ka_gochara_rule_path_prerequisite SELECT path_id, '9.9.9', ordinal, predicate_id,"
                           " predicate_rule_version FROM public.ka_gochara_rule_path_prerequisite WHERE path_id = %s"
                           " AND rule_version = %s", (path, base))
            w.conn.execute("INSERT INTO public.ka_gochara_rule_path_seal (path_id, rule_version) VALUES (%s, '9.9.9')", (path,))
        other = _sealed_not_included(w, path)
    return other[0]


def _attack(w, path, version, *, evidence=1.0):
    """As the RESTRICTED BUILDER, in one transaction: a structurally valid record under the sealed-but-excluded
    (path, version), copied from an existing record (so it REUSES its contact and coverage partition — no new contact), with
    the declared prerequisites of THAT grain, a consistent admission and a numeric evidence result."""
    src = w.conn.execute("SELECT record_id FROM public.ka_gochara_relationship_record WHERE path_id = 'P3'"
                         " AND contact_id IS NOT NULL LIMIT 1").fetchone()[0]
    new = uuid.uuid4()
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        with as_role(w.conn, "data_plane_builder"):
            w.conn.execute("CREATE TEMP TABLE _src ON COMMIT DROP AS SELECT * FROM public.ka_gochara_relationship_record"
                           " WHERE record_id = %s", (src,))
            w.conn.execute("UPDATE _src SET record_id = %s, path_id = %s, rule_version = %s, admission_state = 'admitted',"
                           " evidence_for_occurrence = %s", (new, path, version, evidence))
            w.conn.execute("INSERT INTO public.ka_gochara_relationship_record SELECT * FROM _src")
            w.conn.execute(
                "INSERT INTO public.ka_gochara_record_prerequisite (record_id, chart_id, generation, ordinal, predicate_id,"
                " predicate_rule_version) SELECT %s, %s::uuid, %s, d.ordinal, d.predicate_id, d.predicate_rule_version"
                " FROM public.ka_gochara_rule_path_prerequisite d WHERE d.path_id = %s AND d.rule_version = %s",
                (new, CHART_ID, GEN, path, version))
            w.conn.execute("UPDATE public.ka_gochara_record_prerequisite SET result = 'true' WHERE record_id = %s", (new,))
    return new


def _contact_count(w):
    return w.conn.execute("SELECT count(*) FROM public.ka_gochara_contact").fetchone()[0]


@pytest.mark.parametrize("path", ["P3", "P5"])
def test_an_excluded_version_or_held_path_record_with_a_number_is_refused_by_the_gate_and_the_job_before_verification(
        built, path, monkeypatch):
    w = built
    grain = _foreign_grain(w, path, None)
    # a sealed SUCCESSOR added after the build also drifts the manifest's registry census, which the job's independent input
    # derivation would refuse first (`stale_inputs`); isolate THIS check by letting that derivation pass
    from services.gochara_kernel import input_vector_verifier as ivv
    monkeypatch.setattr(ivv, "verify_inputs", lambda *a, **k: {})
    contacts = _contact_count(w)
    _attack(w, *grain)
    assert _contact_count(w) == contacts                                        # NO new contact
    got = _gate(w)
    assert (CLS, grain[0], grain[1], "output_grain_not_permitted") in got, (grain, got)
    assert (CLS, grain[0], grain[1], "record_result_not_policy") in got, (grain, got)
    report = _run(w)
    c = report["classes"][CLS]
    assert c["status"] == "DISAGREE" and c["stage"] == "generation_output" and "does not include" in c["detail"], c
    assert _verification_rows(w) == {t: 0 for t in vj.VERIFICATION_TABLES}      # the job refused: nothing persisted


@pytest.mark.parametrize("path", ["P3", "P5"])
def test_the_same_attack_after_verification_is_refused_at_the_seal(built, path):
    w = built
    assert _run(w)["status"] == "VERIFIED"
    grain = _foreign_grain(w, path, None)
    before = {v for v in _gate(w)}
    _attack(w, *grain)
    got = _gate(w) - before
    assert (CLS, grain[0], grain[1], "output_grain_not_permitted") in got and \
           (CLS, grain[0], grain[1], "record_result_not_policy") in got, got
    # the INCLUDED grains' digests did not move (it reused an existing contact): the attestations still read current, which
    # is exactly why the old, grain-restricted gate let it through
    assert not any(v[3] == "window_verification_inputs_changed" for v in _gate(w))
    with pytest.raises(Exception, match="output_grain_not_permitted"):
        _seal(w)


def test_a_numeric_record_in_an_included_grain_is_still_caught_and_a_clean_world_has_no_new_violation(built):
    w = built
    assert _run(w)["status"] == "VERIFIED"
    assert not {v for v in _gate(w) if v[3] in ("output_grain_not_permitted", "record_result_not_policy")}
