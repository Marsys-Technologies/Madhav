"""A5.3 — Codex round 9, R9-2: verification proves the COMPLETE output set and stays current.

(i)  the independent verifier derives the full expected MEMBERSHIP set per window (admitted scored records overlapping
     it) and compares both directions with the stored links — it no longer reads the stored links back and reports
     `membership` verified;
(ii) 1240's `derivation_inputs_digest` binds every derivation input of the grain (records, prerequisites, contacts,
     snapshot input identity, manifest vector, policy) — built independently in Python AND recomputed in SQL — so
     Codex's attack (after verification, insert a valid admitted record inside the window and omit its membership link)
     makes the stored verification stale at the seal; the gate also compares expected vs stored membership both ways;
(iii) is in `test_a53_p1_contact_completeness.py` (the P1 anchor check starts from the expected CONTACT set).
"""
from __future__ import annotations

import hashlib
import uuid

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import window_gate as wg
from services.gochara_kernel import window_verifier as wv

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, world  # noqa: F401
from .test_a53_window_verification_gate import (CLS, _boot_p3, _consistent_sky, _qualification_policy,  # noqa: F401
                                                _violations, _windows)

GRAIN = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")


def _built(w):
    _boot_p3(w)
    _windows(w)
    assert _violations(w) == set()                      # a legitimately verified candidate: the gate is empty


def _verify(w):
    return wv.verify_window_semantics(
        w.conn, factor_rows=writer_mod.RuleRegistryStore(w.conn).bound_factor_rows("P3", "1.0.0"), **GRAIN)


def _sql_digest(w):
    return w.conn.execute("SELECT public.ka_gochara_eval_window_inputs_digest(%s::uuid, %s, %s, %s, %s)",
                          (CHART_ID, GEN, CLS, "P3", "1.0.0")).fetchone()[0]


def _insert_second_admitted_record(w):
    """A VALID admitted scored record whose support lies inside the existing window: a copy of the P3 record under a
    new id (same agent and contact — a role alias), with its prerequisite rows — and NO membership link (the
    reviewer's attack)."""
    cols = [r[0] for r in w.conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public'"
        " AND table_name = 'ka_gochara_relationship_record' ORDER BY ordinal_position").fetchall()]
    new = str(uuid.uuid4())
    sel = ", ".join("%s" if c == "record_id" else c for c in cols)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute(f"INSERT INTO public.ka_gochara_relationship_record ({', '.join(cols)})"
                       f" SELECT {sel} FROM public.ka_gochara_relationship_record WHERE path_id = 'P3' LIMIT 1",
                       (new,))
        w.conn.execute(
            "INSERT INTO public.ka_gochara_record_prerequisite"
            " (record_id, chart_id, generation, ordinal, predicate_id, predicate_rule_version, result)"
            " SELECT %s, chart_id, generation, ordinal, predicate_id, predicate_rule_version, result"
            " FROM public.ka_gochara_record_prerequisite WHERE record_id = (SELECT record_id FROM"
            " public.ka_gochara_relationship_record WHERE path_id = 'P3' AND record_id <> %s LIMIT 1)", (new, new))
    return new


# ── (i) the verifier derives the full expected membership ────────────────────────────────────────────

def test_the_verifier_reports_membership_verified_only_when_it_derived_and_compared_it(world):
    w = world
    _built(w)
    assert "membership" in _verify(w)["fields_verified"]


def test_a_missing_membership_link_is_caught_by_the_verifier_and_the_gate(world):
    w = world
    _built(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_record WHERE path_id = 'P3'")
    with pytest.raises(RuntimeError, match="membership omits"):
        _verify(w)
    assert ("P3", "window_membership_not_expected") in _violations(w)
    assert ("P3", "window_verification_stale") in _violations(w)


def test_an_unexpected_membership_link_is_caught_in_the_other_direction(world):
    """A link for a record that does NOT overlap the window (here: a testimony-role copy) is a member the expected set
    does not contain."""
    w = world
    _built(w)
    new = _insert_second_admitted_record(w)
    with w.conn.transaction():                              # make the copy a non-member kind: testimony, then link it
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("ALTER TABLE public.ka_gochara_relationship_record DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_relationship_record SET operator_role = 'testimony',"
                       " ruling_ref = COALESCE(ruling_ref, 'ST-TEST-20261002') WHERE record_id = %s", (new,))
        w.conn.execute("ALTER TABLE public.ka_gochara_relationship_record ENABLE TRIGGER USER")
        w.conn.execute("ALTER TABLE public.ka_gochara_eval_window_record DISABLE TRIGGER USER")
        w.conn.execute("INSERT INTO public.ka_gochara_eval_window_record (window_id, record_id, chart_id, generation,"
                       " event_class, path_id, rule_version) SELECT window_id, %s, chart_id, generation, event_class,"
                       " path_id, rule_version FROM public.ka_gochara_eval_window_record LIMIT 1", (new,))
        w.conn.execute("ALTER TABLE public.ka_gochara_eval_window_record ENABLE TRIGGER USER")
    with pytest.raises(RuntimeError, match="unexpected"):
        _verify(w)
    assert ("P3", "window_membership_not_expected") in _violations(w)


# ── (ii) the reviewer's attack: a valid record inserted after verification, its link omitted ─────────

def test_a_valid_admitted_record_inserted_after_verification_invalidates_it_at_the_gate(world):
    w = world
    _built(w)
    before = _sql_digest(w)
    new = _insert_second_admitted_record(w)
    # the windows, their content and their existing member ids are UNCHANGED, and so is the expected interval union:
    assert ("P3", "window_verification_stale") not in _violations(w)
    assert ("P3", "window_verification_expected_set_mismatch") not in _violations(w)
    # …yet the verification is no longer current, and the omitted link is itself a violation
    v = _violations(w)
    assert ("P3", "window_verification_inputs_changed") in v
    assert ("P3", "window_membership_not_expected") in v
    assert _sql_digest(w) != before
    with pytest.raises(RuntimeError, match="membership omits"):
        _verify(w)                                              # …and the independent verifier names the omission
    assert new                                                   # (the record exists)


def test_mutation_without_the_inputs_digest_the_attack_passes_the_old_gate(world):
    """Reinstate the pre-R9-2 gate (compare only windows, expected set, member ids): the attack is invisible to it — the
    reason the inputs digest and the expected-membership comparison exist."""
    w = world
    _built(w)
    _insert_second_admitted_record(w)
    old_gate = {v for v in _violations(w)
                if v[1] not in ("window_verification_inputs_changed", "window_membership_not_expected")}
    assert old_gate == set()


@pytest.mark.parametrize("what", ["prerequisite_result", "contact", "manifest_vector", "record_admission"])
def test_every_derivation_input_change_invalidates_the_verification(world, what):
    w = world
    _built(w)
    before = _sql_digest(w)
    w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
    if what == "prerequisite_result":
        w.conn.execute("ALTER TABLE public.ka_gochara_record_prerequisite DISABLE TRIGGER USER")
        w.conn.execute("ALTER TABLE public.ka_gochara_relationship_record DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_record_prerequisite SET result = 'unknown'"
                       " WHERE ordinal = 1 AND record_id IN (SELECT record_id FROM public.ka_gochara_relationship_record"
                       " WHERE path_id = 'P3')")
    elif what == "contact":
        w.conn.execute("ALTER TABLE public.ka_gochara_contact DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_contact SET t_out = t_out + interval '1 second'")
    elif what == "manifest_vector":
        w.conn.execute("ALTER TABLE public.kala_gochara_publication DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector ="
                       " input_generation_vector || '{\"stored_scope\": \"stored_all\"}'::jsonb")
    elif what == "record_admission":
        w.conn.execute("ALTER TABLE public.ka_gochara_relationship_record DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_relationship_record SET house_from_frame = 12 WHERE path_id = 'P3'")
    assert _sql_digest(w) != before
    assert ("P3", "window_verification_inputs_changed") in _violations(w)


# ── the two digests are two derivations of ONE preimage ──────────────────────────────────────────────

def test_the_python_and_sql_derivation_inputs_digests_agree_on_the_real_database(world):
    w = world
    _built(w)
    py = wg.derivation_inputs_digest(w.conn, **GRAIN)
    assert py == _sql_digest(w)
    stored = w.conn.execute("SELECT derivation_inputs_digest FROM public.ka_gochara_eval_window_verification"
                            " WHERE path_id = 'P3'").fetchone()[0]
    assert stored == py                                           # what the verifier bound is what the gate recomputes
    # a grain with NO records still has a digest, and the two derivations agree on it too
    empty = dict(GRAIN, path_id="P2")
    assert wg.derivation_inputs_digest(w.conn, **empty) == w.conn.execute(
        "SELECT public.ka_gochara_eval_window_inputs_digest(%s::uuid, %s, %s, %s, %s)",
        (CHART_ID, GEN, CLS, "P2", "1.0.0")).fetchone()[0]


def test_the_frozen_preimage_and_digest_literal():
    """The canonical preimage the verifier builds, pinned as a literal (the SQL function is its twin)."""
    pre = {"records": [{"id": "r1", "agent": "saturn", "relation": "residence", "kind": "sign_span", "role": "scored",
                        "admission": "admitted", "house": None, "anchor": [None, None], "target": "span:7",
                        "contact": "c1", "supports": [["2025-01-10T00:00:00.000000Z", "2025-02-20T00:00:00.000000Z"]]}],
           "prerequisites": [["r1", 1, "agent_resolved", "1.0.0", "true"]],
           "contacts": [["c1", "2025-01-10T00:00:00.000000Z", None]],
           "input": "a" * 64, "manifest": "b" * 64, "policy": "all_null_candidate/1"}
    literal = wg._canon(pre)
    assert literal == (
        '{"contacts":[["c1","2025-01-10T00:00:00.000000Z",null]],"input":"' + "a" * 64 + '","manifest":"' + "b" * 64
        + '","policy":"all_null_candidate/1","prerequisites":[["r1",1,"agent_resolved","1.0.0","true"]],'
        '"records":[{"admission":"admitted","agent":"saturn","anchor":[null,null],"contact":"c1","house":null,'
        '"id":"r1","kind":"sign_span","relation":"residence","role":"scored","supports":'
        '[["2025-01-10T00:00:00.000000Z","2025-02-20T00:00:00.000000Z"]],"target":"span:7"}]}')
    assert hashlib.sha256(literal.encode()).hexdigest() == hashlib.sha256(wg._canon(pre).encode()).hexdigest()
