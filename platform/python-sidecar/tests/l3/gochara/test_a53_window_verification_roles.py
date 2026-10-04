"""A5.3 — migration 1240 on a DEPLOYMENT-FAITHFUL mirror: roles, privileges and the seal trigger (R8-4).

The mirror (the 1206-R6 method): the builder / verifier / sealer principals exist when the migrations run, so their
role-guarded grants apply, and PUBLIC EXECUTE is revoked on every function the migration role creates — exactly what
production's bootstrap does. Contract under test (Stream B's constraints note, steward M20261002T035035-0c4b):
  * the BUILDER holds nothing on the verification table (the writer cannot verify itself);
  * the VERIFIER can derive, verify and persist — with only the migration's explicit grants;
  * the SEALER can run the gate;
  * ONE additive BEFORE INSERT trigger on the seal table, firing after 1206's, refuses a first seal for each of
    {missing row, UNVERIFIED_DYNAMIC, FAILED, count mismatch, stale digest, short field coverage}, accepts all-VERIFIED,
    and REPLAYS a generation sealed before 1240 (no rows) cleanly; a sealed generation is frozen.
1206's own seal trigger is DISABLED on the disposable database to isolate 1240's guard (the full 1206 + 1240 seal is the
protected-window rehearsal's job, which the steward runs).
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import ledger as gk_ledger
from services.gochara_kernel import window_gate as wg
from services.gochara_kernel import window_verifier as wv

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, _world
from .test_a53_window_verification_gate import CLS, SPANS, _boot_p3, _windows

UTC = timezone.utc
SEAL_6 = "ka_gochara_generation_seal_z_search_complete"
SEAL_ZZ = "ka_gochara_generation_seal_zz_window_verified"


@pytest.fixture()
def rworld(monkeypatch, tmp_path):
    yield from _world(monkeypatch, tmp_path, faithful=True)


@pytest.fixture(autouse=True)
def _qualification_policy(rworld):
    """The seal/role flows run under the numbers-enabled policy; the all-NULL policy has its own suites."""
    rworld.result_policy = "window_qualification/1"


@pytest.fixture(autouse=True)
def _consistent_sky(rworld, monkeypatch):
    SPANS.clear()

    def calc(body, jd, ephe):
        t = datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=UTC)
        return (195.0 if any(a <= t < b for a, b in SPANS.get(body.lower(), ())) else 15.0), 2
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", calc)
    # isolate 1240's guard: 1206's completeness trigger is exercised by its own suite
    rworld.conn.execute(f"ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER {SEAL_6}")


@contextmanager
def as_role(conn, role):
    conn.execute(f"SET ROLE {role}")
    try:
        yield
    finally:
        conn.execute("RESET ROLE")


def _report(w, path="P3"):
    return wv.verify_window_semantics(
        w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=path, rule_version="1.0.0",
        factor_rows=writer_mod.RuleRegistryStore(w.conn).bound_factor_rows(path, "1.0.0"))


def _input_digest(w):
    return w.conn.execute("SELECT input_digest FROM public.ka_gochara_search_input_snapshot").fetchone()[0]


def _record(w, path="P3", **over):
    report = {**_report(w, path), **over}
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        wg.record_verification(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=path,
                               rule_version="1.0.0", report=report, input_digest=_input_digest(w))


def _persist_test_brief(w, digest="a" * 64):
    """F-R12-4 / F-R13-4: the receipt must name a brief the VERIFIER persisted. A test that writes a receipt by hand persists one first
    AS THE VERIFIER LOGIN (the database attests its manifest, state and `produced_by`), unless the generation is already published
    (a REPLAY). Call it BEFORE the sealing transaction opens."""
    from .test_a53_verification_job import login
    if w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                      (CHART_ID, GEN)).fetchone()[0] == "candidate":
        with login(w, "gochara_verifier") as c:
            c.execute("INSERT INTO public.ka_gochara_seal_brief (chart_id, generation, manifest_id, brief_digest, state_digest,"
                      " runner_identity, producer_commit, image_digest, execution_id) VALUES (%s::uuid, %s, gen_random_uuid(), %s,"
                      " repeat('0', 64), '{\"commit\": \"t\", \"implementation_digest\": \"t\"}'::jsonb, 'abc1234',"
                      " 'sha256:' || repeat('1', 64), 'executions/test-exec-1')", (CHART_ID, GEN, digest))


def _seal(w, receipt=True):
    """Publish + seal in one transaction (the governed path); returns the manifest id or raises. R11-3: the seal is only
    committable with its approval receipt (1240's deferred constraint trigger), so the helper writes one in the same
    transaction (idempotent for a REPLAY, where the seal row — and its receipt — already exist)."""
    if receipt:
        _persist_test_brief(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(w.conn, CHART_ID, GEN)
        manifest = w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
        if receipt:
            w.conn.execute(
                "INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id, approver_login,"
                " approved_by_note, run_id, run_attempt, workflow_commit) VALUES (%s::uuid, %s, %s::uuid, repeat('a', 64),"
                f" (SELECT coalesce(max(brief_id), 1) FROM public.ka_gochara_seal_brief), 'executions/test-exec-1', 'test-approver', 'test helper', 1, 1, 'abc1234') ON CONFLICT (chart_id, generation) DO NOTHING",
                (CHART_ID, GEN, manifest))
        return manifest


def _built(w):
    _boot_p3(w)
    _windows(w)                                          # superuser: the build + the persisted verification rows


# ── who may write ───────────────────────────────────────────────────────────────────────────────────────────

def test_the_builder_holds_nothing_on_the_verification_table(rworld):
    import psycopg
    w = rworld
    _built(w)
    with as_role(w.conn, "data_plane_builder"):
        for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            assert w.conn.execute("SELECT has_table_privilege(current_user,"
                                  " 'public.ka_gochara_eval_window_verification', %s)",
                                  (privilege,)).fetchone()[0] is False, privilege
        assert wg.can_write_verification(w.conn) is False
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")


def test_the_verifier_derives_verifies_and_persists_with_only_the_migrations_grants(rworld):
    w = rworld
    _built(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")      # superuser clears the rows
    grain = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")
    with as_role(w.conn, "gochara_verifier"):
        assert wg.can_write_verification(w.conn) is True
        rows = writer_mod.RuleRegistryStore(w.conn).bound_factor_rows("P3", "1.0.0")      # reads the bound registry
        report = wv.verify_window_semantics(w.conn, factor_rows=rows, **grain)            # reads windows + members
        wv.verify_member_support(w.conn, **grain)
        wv.verify_member_geometry(
            w.conn, position_at=lambda body, t: 195.0 if SPANS["saturn"][0][0] <= t < SPANS["saturn"][0][1] else 15.0,
            **grain)
        assert wg.expected_windows(w.conn, **grain) == wg.stored_windows(w.conn, **grain)
        digest = _input_digest(w)
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            wg.record_verification(w.conn, report=report, input_digest=digest, **grain)
        assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 1
        # pre-seal DELETE (re-verification replaces) is allowed to the verifier; UPDATE never
        import psycopg
        with pytest.raises(psycopg.errors.Error):
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                w.conn.execute("UPDATE public.ka_gochara_eval_window_verification SET status = 'FAILED'")
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")


def test_the_sealer_runs_the_window_gate_and_the_replay_check(rworld):
    w = rworld
    _built(w)
    # R12-1: the gate's legacy-rows helper is 1240's but its grant is 1241's (closed ACL spec) — stood in here
    w.conn.execute("GRANT EXECUTE ON FUNCTION public.ka_gochara_legacy_projection_rows(uuid, text) TO gochara_sealer")
    with as_role(w.conn, "gochara_sealer"):
        assert wg.candidate_gate(w.conn, CHART_ID, GEN, CLS) == []
        n = w.conn.execute("SELECT count(*) FROM public.ka_gochara_window_verification_replay_violations(%s::uuid, %s)",
                           (CHART_ID, GEN)).fetchone()[0]
        assert n == 0
        assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 4
        import psycopg
        with pytest.raises(psycopg.errors.InsufficientPrivilege):                       # the sealer never writes it
            w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")


def test_each_grant_the_verifier_needs_is_necessary(rworld):
    """The 1206-R6 detector: revoke one EXECUTE the write path relies on and the persistence step fails."""
    import psycopg
    w = rworld
    _built(w)
    grain = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")
    report = _report(w)
    digest = _input_digest(w)
    for fn in ("ka_gochara_lock_chart(uuid)", "ka_gochara_generation_is_sealed(uuid, text)",
               "ka_gochara_lock_global_shared()", "ka_gochara_eval_window_content_digest(uuid, text, text, text, text)"):
        w.conn.execute(f"REVOKE EXECUTE ON FUNCTION public.{fn} FROM gochara_verifier")
        try:
            with as_role(w.conn, "gochara_verifier"):
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    with w.conn.transaction():
                        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")
                        wg.record_verification(w.conn, report=report, input_digest=digest, **grain)
        finally:
            w.conn.execute(f"GRANT EXECUTE ON FUNCTION public.{fn} TO gochara_verifier")


# ── the seal trigger ────────────────────────────────────────────────────────────────────────────────────────

def test_the_new_seal_trigger_fires_after_1206s_and_is_the_only_one_added(rworld):
    names = [r[0] for r in rworld.conn.execute(
        "SELECT tgname FROM pg_trigger WHERE tgrelid = 'public.ka_gochara_generation_seal'::regclass"
        " AND NOT tgisinternal AND tgtype & 4 = 4 AND tgtype & 2 = 2 ORDER BY tgname").fetchall()]    # BEFORE INSERT
    assert names.index(SEAL_ZZ) > names.index(SEAL_6) > names.index("ka_gochara_generation_seal_write_guard")
    assert [n for n in names if "window" in n] == [SEAL_ZZ]


@pytest.mark.parametrize("case", ["missing", "unverified_dynamic", "failed", "count_mismatch", "stale",
                                  "short_fields"])
def test_a_first_seal_is_refused_for_each_window_verification_failure(rworld, case):
    import psycopg
    w = rworld
    _built(w)
    expected_violation = {
        "missing": "window_verification_missing", "unverified_dynamic": "window_verification_not_verified",
        "failed": "window_verification_not_verified", "count_mismatch": "window_verification_count_mismatch",
        "stale": "window_verification_stale", "short_fields": "window_verification_field_coverage_short"}[case]
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        if case == "missing":
            w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'")
        elif case == "count_mismatch" or case == "stale":
            if case == "stale":
                w.conn.execute("UPDATE public.ka_gochara_eval_window SET outcome_valence_for_native = 'mixed'"
                               " WHERE path_id = 'P3'")
            else:
                w.conn.execute("DELETE FROM public.ka_gochara_eval_window WHERE path_id = 'P3'")
    if case == "unverified_dynamic":
        _record(w, status="UNVERIFIED_DYNAMIC", unverified_dynamic=1, fully_reproduced=0)
    elif case == "failed":
        _record(w, status="FAILED", fully_reproduced=0)
    elif case == "short_fields":
        _record(w, fields_verified=[f for f in wv.GOVERNED_FIELDS if f != "outcome_valence_for_native"])
    with pytest.raises(psycopg.errors.Error, match=expected_violation):
        _seal(w)
    # nothing sealed: the refusal rolled the whole attempt back
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0


def test_a_first_seal_is_accepted_when_every_included_grain_is_verified_and_the_generation_is_then_frozen(rworld):
    import psycopg
    w = rworld
    _built(w)
    assert _seal(w) is not None
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 1
    for sql in ("INSERT INTO public.ka_gochara_eval_window_verification SELECT * FROM"
                " public.ka_gochara_eval_window_verification",
                "UPDATE public.ka_gochara_eval_window_verification SET status = 'FAILED'",
                "DELETE FROM public.ka_gochara_eval_window_verification",
                "UPDATE public.ka_gochara_eval_window SET outcome_valence_for_native = 'mixed'",
                "DELETE FROM public.ka_gochara_eval_window"):
        with pytest.raises(psycopg.errors.Error):
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                w.conn.execute(sql)
    # an idempotent replay of the sealed generation passes the guard (rows agree with the frozen windows)
    assert _seal(w) is not None


def test_a_generation_sealed_before_1240_replays_cleanly_without_verification_rows(rworld):
    w = rworld
    _built(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute(f"ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER {SEAL_ZZ}")
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")
    assert _seal(w) is not None                                   # sealed WITHOUT 1240's guard (the pre-1240 world)
    w.conn.execute(f"ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER {SEAL_ZZ}")
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 0
    assert _seal(w) is not None                                   # the replay never retro-requires rows


def test_the_replay_check_flags_a_row_that_no_longer_equals_the_frozen_windows(rworld):
    w = rworld
    _built(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("UPDATE public.ka_gochara_eval_window SET outcome_valence_for_native = 'mixed'"
                       " WHERE path_id = 'P3'")
    n = w.conn.execute("SELECT count(*) FROM public.ka_gochara_window_verification_replay_violations(%s::uuid, %s)",
                       (CHART_ID, GEN)).fetchone()[0]
    assert n == 1


def test_the_candidate_gate_combines_the_completeness_and_the_window_violations(rworld):
    w = rworld
    _built(w)
    rows = w.conn.execute("SELECT event_class, path_id, violation FROM"
                          " public.ka_gochara_candidate_gate_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall()
    kinds = {r[2] for r in rows}
    assert "window_verification_missing" not in kinds            # every included grain is verified ...
    assert kinds & {"verification_missing_or_mismatch", "inventory_without_partition",
                    "missing_inputs_present"}                   # ... but 1206's own checks still speak (no inventory
                                                                # verification row here): the gate is their UNION
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'")
    after = {(r[1], r[2]) for r in w.conn.execute(
        "SELECT event_class, path_id, violation FROM public.ka_gochara_candidate_gate_violations(%s::uuid, %s)",
        (CHART_ID, GEN)).fetchall()}
    assert ("P3", "window_verification_missing") in after


def test_a_replay_is_refused_when_a_row_no_longer_equals_the_sealed_windows(rworld):
    """The replay branch is integrity-only but real: a generation sealed (without 1240's guard) over windows that
    drifted from their verification row cannot be re-sealed once the guard exists."""
    import psycopg
    w = rworld
    _built(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("UPDATE public.ka_gochara_eval_window SET outcome_valence_for_native = 'mixed'"
                       " WHERE path_id = 'P3'")                         # the row is now stale
        w.conn.execute(f"ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER {SEAL_ZZ}")
    assert _seal(w) is not None                                         # sealed with the guard absent
    w.conn.execute(f"ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER {SEAL_ZZ}")
    with pytest.raises(psycopg.errors.Error, match="replay refused .window verification integrity"):
        _seal(w)


def test_a_verification_row_is_refused_while_the_inventory_is_not_finalised(rworld):
    import psycopg
    w = rworld
    _built(w)
    h = "a" * 64
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'")
        w.conn.execute("ALTER TABLE public.ka_gochara_search_inventory DISABLE TRIGGER USER")
        w.conn.execute("UPDATE public.ka_gochara_search_inventory SET inventory_digest = NULL, ledger_digest = NULL, finalized_at = NULL")
        w.conn.execute("ALTER TABLE public.ka_gochara_search_inventory ENABLE TRIGGER USER")
    with pytest.raises(psycopg.errors.Error, match="not FINALISED"):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            w.conn.execute(
                "INSERT INTO public.ka_gochara_eval_window_verification (chart_id, generation, event_class, path_id,"
                " rule_version, verifier_id, verifier_version, status, policy_version, windows_expected,"
                " windows_stored, windows_reproduced, windows_unverified, expected_windows_digest,"
                " stored_windows_digest, windows_content_digest, fields_verified, input_digest,"
                " derivation_inputs_digest)"
                " VALUES (%s,%s,%s,'P3','1.0.0','v','1','VERIFIED','p',1,1,1,0,%s,%s,%s,ARRAY['interval'],%s,%s)",
                (CHART_ID, GEN, CLS, h, h, h, h, h))


def test_the_grants_block_prints_which_principals_it_found_and_which_it_did_not(rworld):
    """A grants block that granted to nobody must be VISIBLE (steward M20261002T042833-a966): re-run the migration's
    own grants DO-block with the sealer renamed away and read the notices."""
    import re
    sql = (__import__("pathlib").Path(__file__).resolve().parents[4] / "migrations"
           / "1240_gochara_window_verification_gate.sql").read_text()
    block = re.search(r"(DO \$\$\nBEGIN\n  IF EXISTS \(SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder'\).*?\n\$\$;)",
                      sql, re.S).group(1)
    notices: list[str] = []
    rworld.conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    rworld.conn.execute(block)
    assert any("verifier grants issued to role gochara_verifier" in n for n in notices)
    assert any("sealer grants issued to role gochara_sealer" in n for n in notices)
    assert any("builder EXECUTE on ka_gochara_window_qualification_ok issued to role data_plane_builder" in n
               for n in notices), notices
    notices.clear()
    rworld.conn.execute("ALTER ROLE data_plane_builder RENAME TO data_plane_builder_away")
    try:
        rworld.conn.execute(block)
    finally:
        rworld.conn.execute("ALTER ROLE data_plane_builder_away RENAME TO data_plane_builder")
    assert any("role data_plane_builder NOT FOUND — NO builder grant was issued" in n for n in notices), notices
    notices.clear()
    rworld.conn.execute("ALTER ROLE gochara_sealer RENAME TO gochara_sealer_away")
    try:
        rworld.conn.execute(block)
    finally:
        rworld.conn.execute("ALTER ROLE gochara_sealer_away RENAME TO gochara_sealer")
    assert any("role gochara_sealer NOT FOUND — NO sealer grants were issued" in n for n in notices), notices
    assert any("verifier grants issued" in n for n in notices)
    notices.clear()
    rworld.conn.execute("ALTER ROLE gochara_verifier RENAME TO gochara_verifier_away")
    try:
        rworld.conn.execute(block)
    finally:
        rworld.conn.execute("ALTER ROLE gochara_verifier_away RENAME TO gochara_verifier")
    assert any("role gochara_verifier NOT FOUND — NO verifier grants were issued" in n for n in notices), notices


def test_when_the_session_role_cannot_write_the_result_the_substeps_record_the_pending_state(rworld, monkeypatch):
    """verification_pending_verifier_principal: never an error, never a builder-written row; the gate stays closed."""
    w = rworld
    _boot_p3(w)
    out = {p: w.step(f"window:{CLS}:{p}") for p in ("P1", "P2", "P3", "P4")}     # the BUILDER's steps only (R9-6.1)
    assert all("verification_pending_verifier_principal" in r.notes and "candidate gate stays closed" in r.notes
               for r in out.values()), [r.notes for r in out.values()]
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 0
    # the pending-state behaviour under test is independent of the contact-geometry certification (its own suite)
    monkeypatch.setattr(writer_mod.gk_contact_certify, "certify_contact_geometry",
                        lambda *a, **k: {"obligations_certified": 0, "contacts_expected": 0, "named_limit": "stubbed"})
    res = w.step(f"verify:{CLS}")
    assert "verification_pending_verifier_principal" in res.notes and "gate stays CLOSED" in res.notes
    import psycopg
    from services.gochara_kernel.window_gate import CandidateGateRefused
    monkeypatch.undo()
    with pytest.raises(CandidateGateRefused, match="window_verification_missing"):
        wg.require_candidate_gate(w.conn, CHART_ID, GEN, CLS)             # the gate itself is closed, by name
