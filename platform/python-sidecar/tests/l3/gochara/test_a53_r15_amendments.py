"""A5.3 — round 15: F-R15-1 (textual identity comparison of a sealed manifest), F-R15-2 (first seal requires result_policy), F-R15-4 (the
single-tier natal disclosure that reads the actual tiers)."""
from __future__ import annotations

import json

import psycopg
import pytest

from services.gochara_kernel import seal_brief as sb

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import built, rworld  # noqa: F401
from .test_a53_r11_seal_brief import _sealer_stand_ins, _verified  # noqa: F401
from .test_a53_r13_sealed_boundary import Schedule, _attested_state_equals_state_now, sched  # noqa: F401
from .test_a53_r12_seal_job import sealable  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky  # noqa: F401


# ── F-R15-1 ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def _state(w):
    return w.conn.execute("SELECT public.ka_gochara_brief_state_digest(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]


@pytest.mark.parametrize("sql", [
    "UPDATE public.kala_gochara_publication SET ephemeris_backend = jsonb_set(ephemeris_backend, '{probe_retflag}', '2.0'::jsonb)",
    "UPDATE public.kala_gochara_publication SET ephemeris_backend = jsonb_set(ephemeris_backend, '{probe_retflag}', '2.00'::jsonb)",
], ids=["5_to_5.0", "5_to_5.00"])
def test_a_numerically_equal_rewrite_of_a_sealed_manifests_identity_is_refused_and_the_digest_does_not_move(sched, sql):
    w = sched.w
    sched.begin_seal()
    sched.commit()
    before = _state(w)
    raw = w.conn.execute("SELECT ephemeris_backend::text FROM public.kala_gochara_publication").fetchone()[0]
    assert "probe_retflag" in raw
    with sched.connect("data_plane_builder") as b:
        with pytest.raises(psycopg.errors.CheckViolation, match="sealed (boundary|lifecycle)"):
            b.execute(sql)
    assert w.conn.execute("SELECT ephemeris_backend::text FROM public.kala_gochara_publication").fetchone()[0] == raw and _state(w) == before


def test_mutation_a_semantic_comparison_would_have_let_the_rewrite_through(built):
    """The detector is the TEXT comparison: jsonb equality calls 5 and 5.0 equal, and the digest hashes the text."""
    w = built
    assert w.conn.execute("SELECT '{\"a\": 5}'::jsonb = '{\"a\": 5.0}'::jsonb").fetchone()[0] is True
    assert w.conn.execute("SELECT '{\"a\": 5}'::jsonb::text = '{\"a\": 5.0}'::jsonb::text").fetchone()[0] is False


# ── F-R15-2 ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_first_seal_of_a_governed_generation_is_refused_without_result_policy_in_the_manifest(sched):
    from services.gochara_kernel import ledger as gk_ledger
    w = sched.w
    w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = input_generation_vector - 'result_policy'")
    with pytest.raises(psycopg.errors.CheckViolation, match="seal_manifest_without_result_policy"):
        with sched.connect("gochara_sealer") as s:
            with s.transaction():
                s.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                gk_ledger.publish(s, CHART_ID, GEN)
                s.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN))
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "candidate"


# ── F-R15-4 ─────────────────────────────────────────────────────────────────────────────────────────────────────────

VERBATIM = ("The ten natal longitudes this generation consumes (LAGNA, SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN; chart_facts "
            "graha_position longitude_sidereal, lahiri) are read at the tier they carry, which is `single` (one derivation, no independent second "
            "pass); they are bound by content digest, not verified by this generation.")


def test_the_sentence_is_printed_only_while_it_is_true_of_the_consumed_rows():
    ten = {s: ["single"] for s in sb.NATAL_SUBJECTS}
    assert sb.natal_disclosure(ten) == VERBATIM == sb.NATAL_SINGLE_TIER_DISCLOSURE
    for broken in ({**ten, "MOON": ["two_pass_verified"]}, {**ten, "SUN": ["single", "classical_match"]},
                   {k: v for k, v in ten.items() if k != "KET_MEAN"}, {**ten, "EXTRA": ["single"]}, {}):
        said = sb.natal_disclosure(broken)
        assert said != VERBATIM and "observed:" in said and "single tier the standard disclosure states" in said
    assert "MOON=two_pass_verified" in sb.natal_disclosure({**ten, "MOON": ["two_pass_verified"]})
    assert "SUN=classical_match/single" in sb.natal_disclosure({**ten, "SUN": ["classical_match", "single"]})


def test_the_brief_reads_the_actual_tiers_and_prints_the_sentence_only_when_all_ten_are_single(built):
    w = built
    _verified(w)
    from .test_a53_r11_seal_brief import _brief_as_verifier
    one = _brief_as_verifier(w, sealing_commit="abcdef1")
    d = one["payload"]["disclosures"]
    assert d["natal_inputs"] == VERBATIM and set(d["natal_input_tiers"]) == set(sb.NATAL_SUBJECTS)
    assert all(t == ["single"] for t in d["natal_input_tiers"].values())
    # an L1 relabel of ONE consumed row: the next brief prints the observed tiers instead (the disclosure cannot go stale)
    w.conn.execute("UPDATE public.chart_facts SET verification_pass_status = 'two_pass_verified' WHERE fact_subject = 'MOON'")
    payload = sb.build_payload(w.conn, CHART_ID, GEN, sealing_commit="abcdef1")
    d2 = payload["disclosures"]
    assert d2["natal_inputs"] != VERBATIM and "MOON=two_pass_verified" in d2["natal_inputs"]
    assert d2["natal_input_tiers"]["MOON"] == ["two_pass_verified"] and d2["natal_input_tiers"]["SUN"] == ["single"]


# ── R15-4: the conditional TRUNCATE guard is sound only at READ COMMITTED ───────────────────────────────────────────

WINDOWS_ROW = "INSERT INTO public.kala_gochara_windows (chart_id, event_class, generation) VALUES (%s, 'marriage', %s)"


def _two(w):
    return psycopg.connect(w.dsn, autocommit=True), psycopg.connect(w.dsn, autocommit=True)


def test_truncate_under_repeatable_read_is_refused_by_name_even_when_the_table_looks_legacy_only(built):
    """The counterexample: a REPEATABLE READ maintenance transaction takes its snapshot while the table holds only legacy rows; another session
    commits a GOVERNED row; the TRUNCATE (not MVCC-safe) would remove it. The guard refuses to decide outside READ COMMITTED."""
    w = built
    w.conn.execute(WINDOWS_ROW, (CHART_ID, "4.0"))
    maint, other = _two(w)
    try:
        maint.execute("BEGIN ISOLATION LEVEL REPEATABLE READ")
        assert maint.execute("SELECT count(*) FROM public.kala_gochara_windows").fetchone()[0] == 1          # the snapshot: legacy-only
        other.execute(WINDOWS_ROW, (CHART_ID, GEN))                                                          # a governed row arrives and COMMITS
        with pytest.raises(psycopg.errors.CheckViolation, match="boundary_truncate_requires_read_committed"):
            maint.execute("TRUNCATE public.kala_gochara_windows")
        maint.execute("ROLLBACK")
    finally:
        maint.close()
        other.close()
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_windows WHERE generation = %s", (GEN,)).fetchone()[0] == 1   # the row survived


@pytest.mark.parametrize("level", ["REPEATABLE READ", "SERIALIZABLE"])
def test_truncate_outside_read_committed_is_refused_even_on_an_empty_legacy_only_table(built, level):
    w = built
    c = psycopg.connect(w.dsn, autocommit=True)
    try:
        c.execute(f"BEGIN ISOLATION LEVEL {level}")
        with pytest.raises(psycopg.errors.CheckViolation, match="boundary_truncate_requires_read_committed"):
            c.execute("TRUNCATE public.kala_gochara_windows")
        c.execute("ROLLBACK")
    finally:
        c.close()


def test_at_read_committed_a_governed_arrival_either_waits_for_the_truncate_or_is_seen_by_it(built):
    """Both orders at READ COMMITTED: (a) TRUNCATE first — it holds AccessExclusive, the INSERT WAITS and lands afterwards; (b) INSERT first — the
    guard sees the committed governed row and refuses."""
    import threading
    import time
    w = built
    w.conn.execute(WINDOWS_ROW, (CHART_ID, "4.0"))
    # (a) TRUNCATE (legacy-only table) holds the lock; the governed INSERT blocks until it commits, and is NOT lost
    maint, other = _two(w)
    result = {}
    try:
        maint.execute("BEGIN")
        maint.execute("TRUNCATE public.kala_gochara_windows")

        def arrive():
            try:
                other.execute(WINDOWS_ROW, (CHART_ID, GEN))
                result["insert"] = "committed"
            except Exception as exc:  # noqa: BLE001
                result["insert"] = exc
        t = threading.Thread(target=arrive, daemon=True)
        t.start()
        time.sleep(0.5)
        assert "insert" not in result, "the governed INSERT was not blocked by the TRUNCATE's AccessExclusive lock"
        maint.execute("COMMIT")
        t.join(10)
    finally:
        maint.close()
        other.close()
    assert result["insert"] == "committed"
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_windows WHERE generation = %s", (GEN,)).fetchone()[0] == 1
    # (b) the governed row is committed first: the TRUNCATE is refused and the row stays
    with pytest.raises(psycopg.errors.CheckViolation, match="TRUNCATE while governed-generation rows exist"):
        w.conn.execute("TRUNCATE public.kala_gochara_windows")
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_windows WHERE generation = %s", (GEN,)).fetchone()[0] == 1


# ── R15-6 (i): the live registry is re-derived at seal ─────────────────────────────────────────────────────────────

def test_registry_drift_between_the_brief_and_the_seal_refuses_the_seal(request, capsys):
    from .test_a53_r12_seal_job import _approval, _nothing_written, _run_job
    w = request.getfixturevalue("sealable")
    assert sb.registry_problem(w.conn, CHART_ID, GEN) is None
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")                 # (the registry is edited behind its own guards)
        w.conn.execute("UPDATE public.ka_gochara_rule_path SET score_rule = coalesce(score_rule, '') || ' (edited after verification)'"
                       " WHERE (path_id, rule_version) = (SELECT path_id, rule_version FROM public.ka_gochara_rule_path ORDER BY 1, 2 LIMIT 1)")
    assert sb.registry_problem(w.conn, CHART_ID, GEN) is not None, "the registry edit did not move the digest — pick another column"
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == 3 and "seal_registry_drift" in out["detail"], out
    _nothing_written(w)


# ── R15-6 (ii) and liveness ─────────────────────────────────────────────────────────────────────────────────────────

def test_the_brief_states_that_the_ephemeris_is_bound_through_the_image_digest_and_not_rederived_at_seal(built):
    w = built
    _verified(w)
    from .test_a53_r11_seal_brief import _brief_as_verifier
    said = _brief_as_verifier(w, sealing_commit="abcdef1")["payload"]["disclosures"]["ephemeris_binding"]
    assert said == sb.EPHEMERIS_BINDING_DISCLOSURE
    assert "does NOT re-derive it at seal" in said and "producer.image_digest" in said and "freeze" in said


def test_the_sealing_job_bounds_its_connection_and_its_idle_transaction(monkeypatch, tmp_path, capsys):
    import psycopg as pg
    from pipeline.orchestrator import seal_job
    seen = {}

    def fake_connect(url, **kw):
        seen.update(kw)
        raise pg.OperationalError("stop here")
    monkeypatch.setattr(pg, "connect", fake_connect)
    monkeypatch.setenv(seal_job.ENV_URL, "postgresql://x/y")
    monkeypatch.setenv("GITHUB_RUN_ID", "1")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    approval = tmp_path / "a.json"
    approval.write_text(json.dumps({"schema": "seal_approval/2", "brief_digest": "a" * 64, "brief_id": 1, "producer_execution_id": "e", "run_id": 1,
                                    "run_attempt": 1, "approver_login": "x", "approved_by_note": "ruling:r; actor:a"}))
    try:
        seal_job.main(["--chart", CHART_ID, "--approval-file", str(approval)])
    except pg.OperationalError:
        pass
    assert seen["connect_timeout"] == seal_job.CONNECT_TIMEOUT_SECONDS == 30
    assert seen["keepalives"] == 1 and seen["tcp_user_timeout"] == 60_000 and seen["autocommit"] is True
    assert sb.SEAL_IDLE_IN_TRANSACTION_TIMEOUT == "10min"


def test_the_idle_in_transaction_bound_is_in_force_inside_the_sealing_transaction_and_local_to_it(request, monkeypatch):
    from services.gochara_kernel import seal_flow as sf
    from psycopg.conninfo import make_conninfo
    from .test_a53_r12_seal_job import ACTOR, COMMIT, _approval
    from .test_a53_verification_job import PASSWORD
    w = request.getfixturevalue("sealable")
    seen = {}
    real = sf.seal_with_approval

    def spy(conn, **kw):
        seen["idle"] = conn.execute("SHOW idle_in_transaction_session_timeout").fetchone()[0]
        return real(conn, **kw)
    monkeypatch.setattr(sf, "seal_with_approval", spy)
    with psycopg.connect(make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD), autocommit=True) as c:
        sf.execute_seal(c, chart_id=CHART_ID, generation=GEN, approval=_approval(w.digest), run_id=424242, run_attempt=2,
                        sealing_commit=COMMIT, triggering_actor=ACTOR)
        after = c.execute("SHOW idle_in_transaction_session_timeout").fetchone()[0]
    assert seen["idle"] == "10min" and after == "0"
