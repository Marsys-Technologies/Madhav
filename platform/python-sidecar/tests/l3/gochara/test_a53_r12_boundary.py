"""A5.3 — Codex round 12, R12-1: ONE explicit candidate boundary, shared by the approval brief, the publication digest and the sealing
recompute.

The brief hashed seven output tables and nothing else. Codex's reproduction: change the coverage facts only — the approval digest stayed the
same, the publication content digest changed, and the OLD approval passed the recompute. Also outside it: the manifest's `ephemeris_backend`
and `writer_asset_id`, and the legacy `kala_gochara_contacts` / `kala_gochara_windows` relations. Now each is inside the boundary (or, for the
legacy rows, forbidden), and every old approval is refused BEFORE publication — each case below leaves the gate EMPTY, so only the boundary
can catch it."""
from __future__ import annotations

import json

import pytest

from services.gochara_kernel import candidate_boundary as cb
from services.gochara_kernel import ledger as gk_ledger
from services.gochara_kernel import seal_brief as sb
from services.gochara_kernel import seal_flow
from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import (CLS, _bypass, _run, built, login, rworld)  # noqa: F401
from .test_a53_r11_seal_brief import APPROVAL, _brief_as_verifier, _sealer_stand_ins, _verified  # noqa: F401
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401


def _approved(w):
    _verified(w)
    return _brief_as_verifier(w, sealing_commit=APPROVAL["sealing_commit"])["sha256"]


def _gate_empty(w):
    assert vj.candidate_gate_on_candidate_manifest(w.conn, CHART_ID, GEN) == [], "the gate must STAY empty for this to prove anything"


def _refused_before_publication(w, approved):
    with pytest.raises(sb.ApprovalMismatch):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            seal_flow.seal_with_approval(w.conn, chart_id=CHART_ID, generation=GEN, approved_digest=approved, **APPROVAL)
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0


@pytest.mark.parametrize("sql", [
    "UPDATE public.kala_gochara_coverage SET unsearched_reason = 'a coverage fact changed after approval'",
    "UPDATE public.kala_gochara_coverage SET unavailable_inputs = unavailable_inputs || '{\"vedha\": \"declared unavailable\"}'::jsonb",
    "UPDATE public.kala_gochara_coverage SET targets_unresolved = targets_unresolved + 1, targets_resolved = targets_resolved - 1"
    " WHERE targets_resolved > 0 AND partition_kind = 'event_class'",
    "UPDATE public.kala_gochara_coverage SET resolution = resolution + 1",
])
def test_a_coverage_only_change_with_an_empty_gate_invalidates_the_approval_before_publication(built, sql):
    w = built
    approved = _approved(w)
    before = sb.payload_digest(sb.build_payload(w.conn, CHART_ID, GEN, sealing_commit=APPROVAL["sealing_commit"]))
    assert before == approved
    # the publication digest the OLD approval did not cover moves with it
    pub_before = cb.publication_content_digest(w.conn, CHART_ID, GEN)
    _bypass(w, (sql, ()))
    _gate_empty(w)
    assert cb.publication_content_digest(w.conn, CHART_ID, GEN) != pub_before
    assert sb.payload_digest(sb.build_payload(w.conn, CHART_ID, GEN, sealing_commit=APPROVAL["sealing_commit"])) != approved
    _refused_before_publication(w, approved)


@pytest.mark.parametrize("sql", [
    "UPDATE public.kala_gochara_publication SET writer_asset_id = 'another_writer'",
    "UPDATE public.kala_gochara_publication SET ephemeris_backend = ephemeris_backend || '{\"backend\": \"moshier\"}'::jsonb",
])
def test_a_publication_identity_only_change_invalidates_the_approval_before_publication(built, sql):
    w = built
    approved = _approved(w)
    _bypass(w, (sql, ()))
    _gate_empty(w)
    _refused_before_publication(w, approved)


def _legacy_windows_table(w):
    w.conn.execute("CREATE TABLE IF NOT EXISTS public.kala_gochara_windows (chart_id uuid, generation text, intensity numeric)")
    w.conn.execute("GRANT SELECT (chart_id, generation) ON public.kala_gochara_windows TO gochara_verifier")


def test_legacy_generation_five_numeric_rows_are_refused_by_the_gate_the_job_the_brief_and_the_recompute(built):
    w = built
    approved = _approved(w)
    _legacy_windows_table(w)
    w.conn.execute("INSERT INTO public.kala_gochara_windows (chart_id, generation, intensity) VALUES (%s::uuid, %s, 0.73)",
                   (CHART_ID, GEN))
    # (1) the 1240 gate (what the seal trigger runs) names it
    got = {(r[0], r[3]) for r in w.conn.execute(
        "SELECT * FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall()}
    assert ("*", "legacy_projection_rows_present") in got, got
    # (2) the job refuses before it verifies anything
    c = _run(w)["classes"][CLS]
    assert c["status"] == "DISAGREE" and c["stage"] == "generation_output" and "kala_gochara_windows" in c["detail"], c
    # (3) the brief refuses, and (4) the old approval is refused before publication
    with pytest.raises(sb.BriefRefused, match="legacy kala_gochara_windows"):
        _brief_as_verifier(w)
    _refused_before_publication(w, approved)


def test_the_on_demand_moon_receipts_stay_outside_the_boundary_explicitly(built):
    """AM-4: a query-time on-demand Moon partition is NOT build identity — adding one moves neither the approval digest nor the
    publication digest (and the boundary statement says so)."""
    w = built
    approved = _approved(w)
    pub = cb.publication_content_digest(w.conn, CHART_ID, GEN)
    w.conn.execute(
        "INSERT INTO public.kala_gochara_coverage SELECT chart_id, generation, 'moon_on_demand', 'moon:interval:x/y', convention_id,"
        " requested_horizon, completed_horizon, resolution, relations_searched, targets_requested, targets_resolved,"
        " targets_unresolved, target_resolution_state_counts, unavailable_inputs, unsearched_reason, build_id, computed_at"
        " FROM public.kala_gochara_coverage WHERE partition_kind = 'event_class' LIMIT 1")
    assert cb.publication_content_digest(w.conn, CHART_ID, GEN) == pub
    assert sb.payload_digest(sb.build_payload(w.conn, CHART_ID, GEN, sealing_commit=APPROVAL["sealing_commit"])) == approved
    stmt = sb.build_payload(w.conn, CHART_ID, GEN)["boundary"]
    assert "moon_on_demand" in stmt["excluded_on_demand_kinds"] and any("AM-4" in x for x in stmt["not_covered"])


def test_a_write_between_the_recompute_and_the_publication_is_caught_after_publication_and_rolled_back(built, monkeypatch):
    """An UNGUARDED write path (the coverage table has no chart-lock write guard): another session commits a coverage change after the
    sealing transaction's recompute and before its publication. The post-publication re-check under the locks refuses, and the
    transaction rolls the publication back."""
    import psycopg
    w = built
    approved = _approved(w)
    real = seal_flow.gk_ledger.publish

    def interloper(conn, chart, gen):
        with psycopg.connect(w.dsn, autocommit=True, connect_timeout=3) as other:     # no chart lock: nothing makes it wait
            other.execute("SET session_replication_role = replica")
            other.execute("UPDATE public.kala_gochara_coverage SET unsearched_reason = 'changed mid-seal'")
        return real(conn, chart, gen)
    monkeypatch.setattr(seal_flow.gk_ledger, "publish", interloper)
    with pytest.raises(sb.ApprovalMismatch, match="changed between the approval recompute and publication"):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            seal_flow.seal_with_approval(w.conn, chart_id=CHART_ID, generation=GEN, approved_digest=approved, **APPROVAL)
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0


def test_the_payload_binds_the_new_boundary_fields_and_the_exact_publication_digest(built):
    w = built
    _verified(w)
    p = _brief_as_verifier(w, sealing_commit="c")["payload"]
    assert p["manifest"]["writer_asset_id"] and p["manifest"]["ephemeris_backend"]
    assert p["coverage_identity"]["rows"] >= 1 and p["coverage_identity"]["kinds"] == ["body_target", "event_class"]
    assert p["legacy_projection"]["kala_gochara_contacts"] == 0 and "policy" in p["legacy_projection"]
    assert p["publication_content_digest"] == cb.publication_content_digest(w.conn, CHART_ID, GEN)
    assert p["boundary"]["not_covered"] and "covered" in p["boundary"]
    # the digest publication ACTUALLY stores equals the one the approved payload carried
    approved = sb.payload_digest(p)
    _sealer_stand_ins(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("SET LOCAL ROLE gochara_sealer")
        out = seal_flow.seal_with_approval(w.conn, chart_id=CHART_ID, generation=GEN, approved_digest=approved,
                                           **{**APPROVAL, "sealing_commit": "c"})
    assert w.conn.execute("SELECT content_digest FROM public.kala_gochara_publication").fetchone()[0] == p["publication_content_digest"]
    assert out["brief_digest"] == approved
