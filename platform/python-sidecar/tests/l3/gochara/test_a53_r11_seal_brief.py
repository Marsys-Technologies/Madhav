"""A5.3 — Codex round 11, R11-3 (job side): the SEAL BRIEF, its canonical COMPLETE APPROVAL PAYLOAD, the sealing-time recompute
and the approval receipt.

Defects answered: `--report-only` skipped the gate while naming the combined function as its source; nothing produced the approval
artefact; and re-checking a gate result cannot establish that the approved candidate is unchanged — two different valid candidates
both give an empty gate. The payload (`seal_approval_payload/1`, agreed with Stream B in SEAL_APPROVAL_PAYLOAD_v1_0) therefore hashes the
manifest identity, the policy, the persisted attestations, the runner/code identity, the migration-ledger evidence AND the
generation-wide OUTPUT IDENTITY (every column of every record, prerequisite, contact, window, member link, path pin and inventory
header). The sealing transaction recomputes it under the seal locks and refuses on any difference BEFORE publishing."""
from __future__ import annotations

import json

import pytest

from pipeline.orchestrator import verification_job as entry
from services.gochara_kernel import seal_brief as sb
from services.gochara_kernel import seal_flow
from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import (CLS, _bypass, _job_position, _kwargs, _run, built, login, rworld)  # noqa: F401
from .test_a53_verification_job import PASSWORD
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal, as_role  # noqa: F401

APPROVAL = dict(approver_login="owner-login", run_id=987654321, run_attempt=1, approval_note="steward under owner ruling #2",
                sealing_commit="seal-commit-abc")


def _verified(w):
    assert _run(w)["status"] == "VERIFIED"


def _brief_as_verifier(w, **kw):
    with login(w, "gochara_verifier") as conn:
        with conn.transaction():
            out = sb.brief(conn, CHART_ID, GEN, **kw)
            out["persisted"] = sb.persist_brief(conn, out)          # F-R12-4: what the CLI's --brief does
            return out


def test_no_brief_is_produced_for_an_unverified_candidate_and_the_reasons_are_named(built):
    with pytest.raises(sb.BriefRefused) as exc:
        _brief_as_verifier(built)
    assert exc.value.code == "candidate_not_approvable"
    assert any("window_verification_missing" in v for v in exc.value.violations), exc.value.violations


def test_a_verified_candidate_yields_a_complete_deterministic_payload_read_with_the_verifiers_own_privileges(built):
    w = built
    _verified(w)
    one, two = _brief_as_verifier(w, sealing_commit="c1"), _brief_as_verifier(w, sealing_commit="c1")
    assert one["sha256"] == two["sha256"] == sb.payload_digest(one["payload"])              # deterministic, self-consistent
    p = one["payload"]
    assert p["schema"] == "seal_approval_payload/1" and p["chart_id"] == CHART_ID and p["generation"] == GEN
    assert p["manifest"]["status"] == "candidate" and p["manifest"]["manifest_id"] and p["result_policy"]
    assert p["candidate_gate"]["violations"] == [] and "candidate_adapter" in p["candidate_gate"]["source"]
    (cls,) = p["classes"]
    assert cls["event_class"] == CLS and {g["path_id"] for g in cls["grains"]} == {"P1", "P2", "P3", "P4"}
    assert all(g["status"] == "VERIFIED" and g["runner"]["commit"] and g["derivation_inputs_digest"] for g in cls["grains"])
    assert set(p["generation_output_identity"]["tables"]) == set(sb.OUTPUT_TABLES)
    assert p["generation_output_identity"]["tables"]["ka_gochara_contact"]["rows"] >= 1
    assert p["code"]["sealing_commit"] == "c1" and p["code"]["verification_runners"]
    assert [m["migration"] for m in p["ledger"]] == list(sb.LEDGER_MIGRATIONS)
    assert p["seal_is_not_a_flip"] and p["disclosures"]["named_limits"]
    assert sb.payload_digest(_brief_as_verifier(w, sealing_commit="c2")["payload"]) != one["sha256"]   # the commit is in it


@pytest.mark.parametrize("sql", [
    "UPDATE public.ka_gochara_relationship_record SET source_text = 'a different citation' WHERE path_id = 'P3'",
    "UPDATE public.ka_gochara_relationship_record SET source_fact_ids = '[\"other-fact\"]'::jsonb WHERE path_id = 'P3'",
    "UPDATE public.ka_gochara_contact SET coverage = coverage || '{\"note\": 1}'::jsonb WHERE body = 'saturn'",
    "UPDATE public.ka_gochara_relationship_record SET temporal_support_grain = 'other' WHERE path_id = 'P3'"
    " AND contact_id IS NOT NULL",
])
def test_two_different_valid_candidates_with_an_empty_gate_give_different_payload_digests(built, sql):
    """A change the inputs digest and every gate arm do not see (a citation, a source-fact list, a coverage note): the gate
    stays EMPTY — so a gate-only approval would still hold — but the output identity, hence the brief digest, moves."""
    w = built
    _verified(w)
    before = _brief_as_verifier(w)["sha256"]
    _bypass(w, (sql, ()))
    assert vj.candidate_gate_on_candidate_manifest(w.conn, CHART_ID, GEN) == [], "the gate must STAY empty for this to prove anything"
    after = sb.payload_digest(sb.build_payload(w.conn, CHART_ID, GEN))
    assert after != before


def test_the_sealing_recompute_under_the_locks_accepts_the_approved_candidate_and_refuses_a_changed_one(built):
    w = built
    _verified(w)
    approved = _brief_as_verifier(w, sealing_commit="s")["sha256"]
    with w.conn.transaction():
        assert sb.payload_digest(sb.recompute_under_locks(w.conn, CHART_ID, GEN, approved, sealing_commit="s")) == approved
    with pytest.raises(sb.ApprovalMismatch, match="not a sha256"):
        sb.recompute_under_locks(w.conn, CHART_ID, GEN, "not-a-digest")
    _bypass(w, ("UPDATE public.ka_gochara_relationship_record SET source_text = 'changed after approval' WHERE path_id = 'P3'", ()))
    with pytest.raises(sb.ApprovalMismatch, match="changed candidate invalidates the approval"):
        with w.conn.transaction():
            sb.recompute_under_locks(w.conn, CHART_ID, GEN, approved, sealing_commit="s")


def test_the_approved_seal_publishes_seals_and_writes_a_receipt_linked_to_the_seal(built):
    import psycopg
    w = built
    _verified(w)
    approved = _brief_as_verifier(w, sealing_commit=APPROVAL["sealing_commit"])["sha256"]
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        out = seal_flow.seal_with_approval(w.conn, chart_id=CHART_ID, generation=GEN, approved_digest=approved, **APPROVAL)
    assert out["brief_digest"] == approved
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "published"
    row = w.conn.execute("SELECT s.manifest_id::text, a.brief_digest, a.approver_login, a.run_id, a.run_attempt, a.workflow_commit,"
                         " a.manifest_id::text FROM public.ka_gochara_generation_seal s JOIN public.ka_gochara_seal_approval a"
                         " USING (chart_id, generation)").fetchone()
    assert row[0] == row[6] == out["manifest_id"] and row[1:6] == (approved, "owner-login", 987654321, 1, "seal-commit-abc")
    for sql in ("UPDATE public.ka_gochara_seal_approval SET approver_login = 'someone else'",
                "DELETE FROM public.ka_gochara_seal_approval", "TRUNCATE public.ka_gochara_seal_approval"):
        with pytest.raises(psycopg.errors.Error, match="append-only"):
            with w.conn.transaction():
                w.conn.execute(sql)


def test_a_changed_candidate_with_an_empty_gate_is_refused_before_anything_is_published(built):
    w = built
    _verified(w)
    approved = _brief_as_verifier(w, sealing_commit=APPROVAL["sealing_commit"])["sha256"]
    _bypass(w, ("UPDATE public.ka_gochara_relationship_record SET source_text = 'edited after the brief' WHERE path_id = 'P3'", ()))
    assert vj.candidate_gate_on_candidate_manifest(w.conn, CHART_ID, GEN) == []
    with pytest.raises(sb.ApprovalMismatch):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            seal_flow.seal_with_approval(w.conn, chart_id=CHART_ID, generation=GEN, approved_digest=approved, **APPROVAL)
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0


def test_a_failure_after_publication_rolls_back_the_publication_the_seal_and_the_receipt(built):
    """Atomic: the approval matched, the publication ran, the seal ran, then the RECEIPT insert failed (the sealer's INSERT on the
    receipt table revoked) — nothing stays half-done: the manifest is still a candidate, no seal row, no receipt."""
    import psycopg
    w = built
    _verified(w)
    approved = _brief_as_verifier(w, sealing_commit=APPROVAL["sealing_commit"])["sha256"]
    _sealer_stand_ins(w)
    w.conn.execute("REVOKE INSERT ON public.ka_gochara_seal_approval FROM gochara_sealer")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            w.conn.execute("SET LOCAL ROLE gochara_sealer")
            seal_flow.seal_with_approval(w.conn, chart_id=CHART_ID, generation=GEN, approved_digest=approved, **APPROVAL)
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 4


def test_the_entry_points_brief_mode_prints_the_payload_and_its_digest_and_refuses_when_not_approvable(built, monkeypatch, capsys):
    from psycopg.conninfo import make_conninfo
    w = built
    w.conn.execute(f"ALTER ROLE gochara_verifier LOGIN PASSWORD '{PASSWORD}'")
    try:
        monkeypatch.setenv(entry.ENV_URL, make_conninfo(w.dsn, user="gochara_verifier", password=PASSWORD))
        assert entry.main(["--chart", CHART_ID, "--brief"]) == vj.EXIT_DISAGREE          # not yet verified: refused, reasons named
        refused = json.loads(capsys.readouterr().out)
        assert refused["status"] == "REFUSED" and refused["code"] == "candidate_not_approvable" and refused["violations"]
        _verified(w)                                                       # (its login helper re-locks the role afterwards)
        w.conn.execute(f"ALTER ROLE gochara_verifier LOGIN PASSWORD '{PASSWORD}'")
        assert entry.main(["--chart", CHART_ID, "--brief", "--sealing-commit", "cli-sha"]) == vj.EXIT_OK
        out = json.loads(capsys.readouterr().out)
        assert out["brief"]["schema"] == "seal_approval_payload/1" and out["brief"]["code"]["sealing_commit"] == "cli-sha"
        assert out["sha256"] == sb.payload_digest(sb.build_payload(w.conn, CHART_ID, GEN, sealing_commit="cli-sha"))
    finally:
        w.conn.execute("ALTER ROLE gochara_verifier NOLOGIN PASSWORD NULL")


def test_the_approved_seal_runs_as_the_real_sealer_role_with_only_the_named_read_grants_beyond_1240_and_1241(built):
    """The whole approved seal (locks → recompute → publish → authoritative seal → receipt) as the SEALER principal. Beyond what
    1240 and 1241 already grant it needs exactly: SELECT on the two L1 tables (the data-plane owner's open ACL item, stood in here)
    and a column-level SELECT on the migration ledger `(filename, sha256, applied_at)` for the payload's `ledger` evidence —
    derived by running the flow and adding one grant per `permission denied` (Stream B's 1241 v4). The receipt INSERT/EXECUTE grants are Stream B's 1241 (stood in by the delta fixture)."""
    w = built
    _verified(w)
    approved = _brief_as_verifier(w, sealing_commit="s")["sha256"]
    w.conn.execute("GRANT SELECT ON public.chart_facts, public.chart_dashas TO gochara_sealer")           # L1 ACL stand-in
    w.conn.execute("GRANT SELECT (filename, sha256, applied_at) ON public._migrations_applied TO gochara_sealer")
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("SET LOCAL ROLE gochara_sealer")
        out = seal_flow.seal_with_approval(w.conn, chart_id=CHART_ID, generation=GEN, approved_digest=approved,
                                           approver_login="owner-login", run_id=42, approval_note="n", sealing_commit="s")
    assert out["brief_digest"] == approved
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 1


def test_the_missing_receipt_check_is_false_before_a_seal_and_true_only_for_a_pre_1240_seal(built):
    w = built
    _verified(w)
    assert w.conn.execute("SELECT public.ka_gochara_seal_receipt_missing(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0] is False  # not sealed


# ── the receipt is ENFORCED at the first seal (steward M…145007) ───────────────────────────────────────────

def _raw_seal_as_sealer(w):
    """The sealer principal calls the authoritative seal DIRECTLY — publish + seal, no approval receipt."""
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("SET LOCAL ROLE gochara_sealer")
        from services.gochara_kernel import ledger as gk_ledger
        gk_ledger.publish(w.conn, CHART_ID, GEN)
        w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN))


def _sealer_stand_ins(w):
    w.conn.execute("GRANT SELECT ON public.chart_facts, public.chart_dashas TO gochara_sealer")
    w.conn.execute("GRANT SELECT (filename, sha256, applied_at) ON public._migrations_applied TO gochara_sealer")


def test_a_raw_seal_with_no_receipt_is_refused_at_commit_by_name_and_leaves_nothing(built):
    import psycopg
    w = built
    _verified(w)
    _sealer_stand_ins(w)
    with pytest.raises(psycopg.errors.CheckViolation, match="approval_receipt_missing"):
        _raw_seal_as_sealer(w)
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0


def test_a_receipt_for_another_manifest_or_without_a_digest_does_not_satisfy_the_trigger(built):
    import psycopg
    w = built
    _verified(w)
    with pytest.raises(psycopg.errors.CheckViolation, match="approval_receipt_missing"):
        _seal(w, receipt=False)                                        # (superuser path: still no receipt ⇒ refused)
    with pytest.raises(psycopg.errors.CheckViolation, match="approval_receipt_missing"):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            from services.gochara_kernel import ledger as gk_ledger
            gk_ledger.publish(w.conn, CHART_ID, GEN)
            w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN))
            w.conn.execute(                                            # a receipt naming a DIFFERENT manifest
                "INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, approver_login,"
                " approved_by_note, run_id, run_attempt, workflow_commit) VALUES (%s::uuid, %s, gen_random_uuid(),"
                " repeat('a', 64), 'x', 'x', 1, 1, 'x')", (CHART_ID, GEN))
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0


def test_the_approved_seal_still_works_as_the_real_sealer_and_the_replay_needs_no_new_receipt(built):
    w = built
    _verified(w)
    approved = _brief_as_verifier(w, sealing_commit="s")["sha256"]
    _sealer_stand_ins(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("SET LOCAL ROLE gochara_sealer")
        out = seal_flow.seal_with_approval(w.conn, chart_id=CHART_ID, generation=GEN, approved_digest=approved,
                                           approver_login="owner-login", run_id=7, approval_note="n", sealing_commit="s")
    assert out["brief_digest"] == approved
    # REPLAY of the sealed generation: ON CONFLICT DO NOTHING inserts no row, so the receipt trigger never fires
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("SET LOCAL ROLE gochara_sealer")
        w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN))
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 1


def test_a_generation_sealed_before_1240_replays_without_a_receipt(built):
    """Simulate 'sealed before 1240': the receipt trigger did not exist when it was sealed, so it has a seal row and no receipt.
    Replaying it must not demand one."""
    w = built
    _verified(w)
    w.conn.execute("ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER ka_gochara_generation_seal_zz_receipt_required")
    _seal(w, receipt=False)
    w.conn.execute("ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER ka_gochara_generation_seal_zz_receipt_required")
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0
    _seal(w, receipt=False)                                           # the replay: no receipt, no refusal
    assert w.conn.execute("SELECT public.ka_gochara_seal_receipt_missing(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0] is True
