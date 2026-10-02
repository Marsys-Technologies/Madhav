"""A5.3 — independent review F-R12-4: the approval receipt is bound to a brief the VERIFIER persisted.

The receipt's `brief_digest` used to be only a 64-hex string the sealer supplied — nothing tied it to a brief the separate verifier
actually produced for THIS candidate. Now the verifier's `--brief` persists each brief (append-only `ka_gochara_seal_brief`; the
verifier INSERTs, the sealer only SELECTs) with a DATABASE-ATTESTED manifest, state digest, login and time; and the receipt's deferred
trigger requires, at COMMIT, `receipt.brief_digest` to be the CURRENT (latest) persisted brief of the generation for the same manifest,
whose state digest must still be the generation's state. Every case runs on the faithful disposable DB, as the real roles."""
from __future__ import annotations

import json
import re
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from pipeline.orchestrator import seal_job
from services.gochara_kernel import candidate_boundary as cb
from services.gochara_kernel import ledger as gk_ledger
from services.gochara_kernel import seal_brief as sb
from services.gochara_kernel import seal_flow as sf

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import _bypass, _run, built, login, rworld  # noqa: F401
from .test_a53_r11_seal_brief import BRIEF_IDS, EXECUTION, IMAGE, _brief_as_verifier, _producer, _sealer_stand_ins, _verified  # noqa: F401
from .test_a53_r12_seal_job import ACTOR, ATTEMPT, COMMIT, RUN, _approval, _nothing_written, _run_job, sealable  # noqa: F401
from .test_a53_verification_job import PASSWORD
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky  # noqa: F401

MIGRATION = Path(__file__).resolve().parents[3].parent / "migrations" / "1240_gochara_window_verification_gate.sql"


def _state(w) -> str:
    return w.conn.execute("SELECT public.ka_gochara_brief_state_digest(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]


def _persisted(w) -> list[tuple]:
    return w.conn.execute("SELECT brief_id, brief_digest, manifest_id::text, state_digest, produced_by FROM"
                          " public.ka_gochara_seal_brief ORDER BY brief_id").fetchall()


def _publish_seal_receipt(w, digest, *, manifest=None):
    """Publish + seal + the receipt naming `digest`, in ONE transaction (superuser: the triggers are the defence under test)."""
    brief_id, commit = w.conn.execute("SELECT brief_id, producer_commit FROM public.ka_gochara_seal_brief ORDER BY brief_id DESC LIMIT 1").fetchone() \
        or (1, "abc1234")                                             # (no brief at all: a fabricated receipt)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(w.conn, CHART_ID, GEN)
        mid = w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
        w.conn.execute(
            "INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id, approver_login,"
            " approved_by_note, run_id, run_attempt, workflow_commit) VALUES (%s::uuid, %s, %s::uuid, %s, %s, 'executions/test-exec-1', 'x', 'x', 1, 1, %s)",
            (CHART_ID, GEN, manifest or mid, digest, brief_id, commit))


# ── what is persisted, by whom ────────────────────────────────────────────────────────────────────────────────

def test_the_verifier_persists_the_brief_with_database_attested_columns(built):
    w = built
    _verified(w)
    out = _brief_as_verifier(w, sealing_commit=COMMIT)
    ((bid, digest, manifest, state, by),) = _persisted(w)
    assert digest == out["sha256"] and manifest == out["payload"]["manifest"]["manifest_id"] and by == "gochara_verifier"
    assert state == _state(w) == out["persisted"]["state_digest"] and bid == out["persisted"]["brief_id"]


def test_forged_attested_columns_are_overwritten_and_only_a_candidate_can_be_briefed(built):
    w = built
    _verified(w)
    w.conn.execute(
        "INSERT INTO public.ka_gochara_seal_brief (chart_id, generation, manifest_id, brief_digest, state_digest, runner_identity,"
        " producer_commit, image_digest, execution_id, produced_by, produced_at) VALUES (%s::uuid, %s, gen_random_uuid(), repeat('b', 64),"
        " repeat('c', 64), '{\"commit\": \"t\", \"implementation_digest\": \"t\"}'::jsonb, 't', 'sha256:' || repeat('1', 64), 'e',"
        " 'forged', '2001-01-01T00:00:00Z')", (CHART_ID, GEN))
    (_, digest, manifest, state, by), = _persisted(w)
    assert manifest == w.conn.execute("SELECT manifest_id::text FROM public.kala_gochara_publication").fetchone()[0]
    assert state == _state(w) and by != "forged" and digest == "b" * 64
    w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'published' WHERE chart_id = %s", (CHART_ID,))
    with pytest.raises(psycopg.errors.CheckViolation, match="brief_without_candidate"):
        w.conn.execute(
            "INSERT INTO public.ka_gochara_seal_brief (chart_id, generation, manifest_id, brief_digest, state_digest, runner_identity,"
            " producer_commit, image_digest, execution_id) VALUES (%s::uuid, %s, gen_random_uuid(), repeat('d', 64), repeat('0', 64),"
            " '{\"commit\": \"t\", \"implementation_digest\": \"t\"}'::jsonb, 't', 'sha256:' || repeat('1', 64), 'e')", (CHART_ID, GEN))


def test_the_table_is_append_only(built):
    w = built
    _verified(w)
    _brief_as_verifier(w, sealing_commit=COMMIT)
    for sql in ("UPDATE public.ka_gochara_seal_brief SET brief_digest = repeat('e', 64)", "DELETE FROM public.ka_gochara_seal_brief",
                "TRUNCATE public.ka_gochara_seal_brief"):
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            w.conn.execute(sql)


def test_the_sealer_may_read_the_table_but_not_write_it_and_the_verifier_may_not_change_it(sealable):
    w = sealable
    with login(w, "gochara_sealer") as c:
        assert c.execute("SELECT count(*) FROM public.ka_gochara_seal_brief").fetchone()[0] == 1
        for sql in ("INSERT INTO public.ka_gochara_seal_brief (chart_id, generation, manifest_id, brief_digest, state_digest,"
                    " runner_identity, producer_commit, image_digest, execution_id) VALUES (gen_random_uuid(), 'x', gen_random_uuid(),"
                    " repeat('a', 64), repeat('a', 64), '{}', 't', 'sha256:' || repeat('1', 64), 'e')",
                    "UPDATE public.ka_gochara_seal_brief SET brief_digest = repeat('a', 64)", "DELETE FROM public.ka_gochara_seal_brief"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute(sql)
    with login(w, "gochara_verifier") as c:
        for sql in ("UPDATE public.ka_gochara_seal_brief SET brief_digest = repeat('a', 64)", "DELETE FROM public.ka_gochara_seal_brief"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute(sql)


# ── the receipt must name the CURRENT persisted brief ─────────────────────────────────────────────────────────

def test_a_fabricated_digest_is_refused_at_commit_by_name_and_nothing_remains(built):
    w = built
    _verified(w)
    _brief_as_verifier(w, sealing_commit=COMMIT)
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_not_persisted"):
        _publish_seal_receipt(w, "f" * 64)
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0


def test_no_persisted_brief_at_all_is_refused_and_the_trigger_is_what_refuses(built):
    w = built
    _verified(w)
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_not_persisted"):
        _publish_seal_receipt(w, "a" * 64)
    # MUTATION: without the trigger the same fabricated receipt commits — the detector is the trigger, not an accident of the fixture
    w.conn.execute("ALTER TABLE public.ka_gochara_seal_approval DISABLE TRIGGER ka_gochara_seal_approval_zz_persisted_brief")
    _publish_seal_receipt(w, "a" * 64)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 1


def test_the_receipt_of_the_current_brief_commits(built):
    w = built
    _verified(w)
    out = _brief_as_verifier(w, sealing_commit=COMMIT)
    _publish_seal_receipt(w, out["sha256"])
    assert w.conn.execute("SELECT brief_digest FROM public.ka_gochara_seal_approval").fetchone()[0] == out["sha256"]


def test_a_brief_for_another_manifest_does_not_satisfy_the_receipt(built):
    w = built
    _verified(w)
    out = _brief_as_verifier(w, sealing_commit=COMMIT)
    mid = out["payload"]["manifest"]["manifest_id"]
    other = w.conn.execute("SELECT gen_random_uuid()::text").fetchone()[0]
    fn = "SELECT public.ka_gochara_seal_brief_problem(%s::uuid, %s, %s::uuid, %s)"
    assert w.conn.execute(fn, (CHART_ID, GEN, mid, out["sha256"])).fetchone()[0] is None
    assert w.conn.execute(fn, (CHART_ID, GEN, other, out["sha256"])).fetchone()[0] == "receipt_brief_not_persisted"
    # and at the trigger: a receipt naming another manifest (with the seal-side rules out of the way) is refused by THIS rule
    for trg, table in (("ka_gochara_generation_seal_zz_receipt_required", "ka_gochara_generation_seal"),
                       ("ka_gochara_seal_approval_zz_first_seal", "ka_gochara_seal_approval")):
        w.conn.execute(f"ALTER TABLE public.{table} DISABLE TRIGGER {trg}")
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_not_persisted"):
        _publish_seal_receipt(w, out["sha256"], manifest=other)


def test_a_superseded_brief_is_not_a_bypass_only_the_latest_is_current(built):
    w = built
    _verified(w)
    first = _brief_as_verifier(w, sealing_commit=COMMIT)
    second = _brief_as_verifier(w, sealing_commit="0" * 40)               # same state, a later brief (a different sealing revision)
    assert first["sha256"] != second["sha256"] and len(_persisted(w)) == 2
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_superseded"):
        _publish_seal_receipt(w, first["sha256"])
    _publish_seal_receipt(w, second["sha256"])


def test_a_reverification_that_changes_the_candidate_makes_the_old_brief_unusable(built):
    w = built
    _verified(w)
    old = _brief_as_verifier(w, sealing_commit=COMMIT)
    before = _state(w)
    _verified(w)                                                          # the real job re-verifies: new attestation rows (verified_at)
    assert _state(w) != before, "a re-verification must move the state digest"
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_state_changed"):
        _publish_seal_receipt(w, old["sha256"])
    new = _brief_as_verifier(w, sealing_commit=COMMIT)                    # a fresh brief of the re-verified candidate is usable
    assert new["sha256"] != old["sha256"]
    _publish_seal_receipt(w, new["sha256"])


def test_every_kind_of_change_to_the_candidate_moves_the_state_digest(built):
    w = built
    _verified(w)
    base = _state(w)
    # created_at alone does NOT move it (it is excluded everywhere, as in the brief's own identity digest)
    _bypass(w, ("UPDATE public.ka_gochara_eval_window SET created_at = created_at + interval '1 day'", ()))
    assert _state(w) == base
    seen = {base}
    for label, table, stmt in (
        ("an output row", "ka_gochara_eval_window_record", "DELETE FROM public.ka_gochara_eval_window_record"),
        ("a search-input row", "ka_gochara_search_obligation", "DELETE FROM public.ka_gochara_search_obligation"),
        ("an attestation row", "ka_gochara_eval_window_verification", "DELETE FROM public.ka_gochara_eval_window_verification"),
        ("a build coverage row", "kala_gochara_coverage", "DELETE FROM public.kala_gochara_coverage WHERE partition_kind = 'event_class'"),
        ("the manifest identity", "kala_gochara_publication",
         "UPDATE public.kala_gochara_publication SET writer_asset_id = writer_asset_id || '-x'"),
    ):
        assert w.conn.execute(f"SELECT count(*) FROM public.{table}").fetchone()[0] > 0, f"fixture has no {label} to change"
        _bypass(w, (stmt, ()))
        cur = _state(w)
        assert cur not in seen, f"changing {label} did not move the state digest"
        seen.add(cur)


def test_the_publication_fields_are_not_part_of_the_state(built):
    w = built
    _verified(w)
    base = _state(w)
    w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'published', published_at = now(), content_digest = repeat('9', 64)")
    assert _state(w) == base


def test_the_state_digest_does_not_depend_on_the_calling_sessions_settings(built):
    w = built
    _verified(w)
    base = _state(w)
    for tz, ds, ivs, fd in (("Asia/Kolkata", "ISO, YMD", "postgres_verbose", -1), ("America/Los_Angeles", "ISO, MDY", "sql_standard", 3)):
        w.conn.execute(f"SET TimeZone = '{tz}'")
        w.conn.execute(f"SET DateStyle = '{ds}'")
        w.conn.execute(f"SET IntervalStyle = {ivs}")
        w.conn.execute(f"SET extra_float_digits = {fd}")
        assert _state(w) == base, (tz, ds, ivs, fd)
    w.conn.execute("RESET ALL")
    cfg = w.conn.execute("SELECT proconfig FROM pg_proc WHERE proname = 'ka_gochara_brief_state_digest'").fetchone()[0]
    assert {c.split("=")[0].lower() for c in cfg} >= {"timezone", "datestyle", "intervalstyle", "extra_float_digits"}


# ── F-R13-4: the current brief must have been written by the VERIFIER login ───────────────────────────────────

from contextlib import contextmanager

OTHER = "a53_other_brief_writer"


@contextmanager
def _other_writer(w):
    """A SECOND principal that holds INSERT (and every read the brief needs — it inherits the verifier's grants) but is not the verifier."""
    w.conn.execute(f"DROP ROLE IF EXISTS {OTHER}")
    w.conn.execute(f"CREATE ROLE {OTHER} LOGIN PASSWORD '{PASSWORD}' IN ROLE gochara_verifier")
    conn = None
    try:
        conn = psycopg.connect(make_conninfo(w.dsn, user=OTHER, password=PASSWORD), autocommit=True, connect_timeout=3)
        yield conn
    finally:
        if conn is not None:
            conn.close()
        w.conn.execute(f"DROP ROLE IF EXISTS {OTHER}")


def _brief_as_other(w, c, **kw):
    with c.transaction():
        out = sb.brief(c, CHART_ID, GEN, **kw)
        out["persisted"] = sb.persist_brief(c, out, producer=_producer(kw.get("sealing_commit")))
        BRIEF_IDS[out["sha256"]] = out["persisted"]["brief_id"]
    return out


def test_a_brief_written_by_another_login_that_holds_insert_is_refused_by_name(built):
    w = built
    _verified(w)
    with _other_writer(w) as c:
        out = _brief_as_other(w, c, sealing_commit=COMMIT)
        assert c.execute("SELECT session_user").fetchone()[0] == OTHER
    assert _persisted(w)[0][4] == OTHER                                   # database-attested, not self-declared
    fn = "SELECT public.ka_gochara_seal_brief_problem(%s::uuid, %s, %s::uuid, %s)"
    assert w.conn.execute(fn, (CHART_ID, GEN, out["payload"]["manifest"]["manifest_id"], out["sha256"])).fetchone()[0] \
        == "receipt_brief_not_from_verifier"
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_not_from_verifier"):
        _publish_seal_receipt(w, out["sha256"])
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0
    # MUTATION: without the produced_by rule (the function as it was before F-R13-4) the same receipt commits
    w.conn.execute("ALTER TABLE public.ka_gochara_seal_approval DISABLE TRIGGER ka_gochara_seal_approval_zz_persisted_brief")
    _publish_seal_receipt(w, out["sha256"])
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 1


def test_a_later_foreign_brief_supersedes_the_verifiers_and_neither_approves_the_seal(built):
    w = built
    _verified(w)
    mine = _brief_as_verifier(w, sealing_commit=COMMIT)
    with _other_writer(w) as c:
        theirs = _brief_as_other(w, c, sealing_commit="2" * 40)
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_superseded"):
        _publish_seal_receipt(w, mine["sha256"])
    with pytest.raises(psycopg.errors.CheckViolation, match="receipt_brief_not_from_verifier"):
        _publish_seal_receipt(w, theirs["sha256"])
    again = _brief_as_verifier(w, sealing_commit=COMMIT)                  # the verifier's fresh brief is current again and works
    _publish_seal_receipt(w, again["sha256"])


# ── the job: the sealer refuses early, naming the reason, and the real flow still seals ───────────────────────────

@pytest.fixture()
def unpersisted(built, monkeypatch, tmp_path):
    w = built
    _verified(w)
    with login(w, "gochara_verifier") as conn:                            # a brief is COMPUTED (its digest is right) but never persisted
        with conn.transaction():
            w.digest = sb.brief(conn, CHART_ID, GEN, sealing_commit=COMMIT)["sha256"]
    _sealer_stand_ins(w)
    w.conn.execute(f"ALTER ROLE gochara_sealer LOGIN PASSWORD '{PASSWORD}'")
    monkeypatch.setenv(seal_job.ENV_URL, make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD))
    monkeypatch.setenv("GITHUB_RUN_ID", str(RUN))
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", str(ATTEMPT))
    monkeypatch.setenv("GOCHARA_SEALING_COMMIT", COMMIT)
    monkeypatch.setenv("GITHUB_TRIGGERING_ACTOR", ACTOR)
    w.tmp = tmp_path
    yield w
    w.conn.execute("ALTER ROLE gochara_sealer NOLOGIN PASSWORD NULL")


def test_the_job_refuses_a_digest_the_verifier_never_persisted_before_publishing(unpersisted, capsys):
    w = unpersisted
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_MISMATCH and "receipt_brief_not_persisted" in out["detail"], out
    _nothing_written(w)


def test_a_superseded_approval_is_refused_by_the_job_and_the_latest_seals(sealable, capsys, monkeypatch):
    w = sealable
    later = "1" * 40
    second = _brief_as_verifier(w, sealing_commit=later)                  # `sealable` persisted the first; this one supersedes it
    assert second["sha256"] != w.digest
    code, out = _run_job(w, capsys, _approval(w.digest))
    assert code == sf.EXIT_MISMATCH and "receipt_brief_superseded" in out["detail"], out
    _nothing_written(w)
    monkeypatch.setenv("GOCHARA_SEALING_COMMIT", later)                   # the sealing revision of the latest brief
    code, out = _run_job(w, capsys, _approval(second["sha256"]))
    assert code == sf.EXIT_SEALED, out


# ── the migration's own shape (static) ───────────────────────────────────────────────────────────────────────

def test_the_state_digest_function_covers_exactly_the_output_tables_the_brief_hashes_plus_the_attestations():
    src = MIGRATION.read_text()
    body = src[src.index("CREATE OR REPLACE FUNCTION public.ka_gochara_brief_state_digest"):]
    body = body[:body.index("COMMENT ON FUNCTION public.ka_gochara_brief_state_digest")]
    tables = re.findall(r"'(ka_gochara_[a-z_]+)'", body[body.index("ARRAY["):body.index("] LOOP")])
    assert tuple(tables[:len(sb.OUTPUT_TABLES)]) == sb.OUTPUT_TABLES
    assert set(tables[len(sb.OUTPUT_TABLES):]) == set(sb._VERIFICATION_TABLES) and len(tables) == len(sb.OUTPUT_TABLES) + 2
    kinds = re.search(r"partition_kind IN \(([^)]*)\)", body).group(1)
    assert tuple(re.findall(r"'([a-z_]+)'", kinds)) == cb.BUILD_COVERAGE_KINDS


def test_the_migration_grants_nothing_on_the_new_objects_and_the_sealer_never_gets_a_write():
    src = MIGRATION.read_text()
    for obj in ("ka_gochara_seal_brief", "ka_gochara_brief_state_digest", "ka_gochara_seal_brief_problem"):
        assert not re.search(rf"GRANT[^;]*{obj}", src), f"1240 must grant nothing on {obj} — the grants are 1241's"
    assert "ka_gochara_seal_brief" not in " ".join(sf.SEALER_WRITE_ALLOWED)


def test_the_job_refuses_a_foreign_brief_before_publishing(built, monkeypatch, tmp_path, capsys):
    w = built
    _verified(w)
    with _other_writer(w) as c:
        digest = _brief_as_other(w, c, sealing_commit=COMMIT)["sha256"]
    _sealer_stand_ins(w)
    w.conn.execute(f"ALTER ROLE gochara_sealer LOGIN PASSWORD '{PASSWORD}'")
    try:
        monkeypatch.setenv(seal_job.ENV_URL, make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD))
        monkeypatch.setenv("GITHUB_RUN_ID", str(RUN))
        monkeypatch.setenv("GITHUB_RUN_ATTEMPT", str(ATTEMPT))
        monkeypatch.setenv("GOCHARA_SEALING_COMMIT", COMMIT)
        monkeypatch.setenv("GITHUB_TRIGGERING_ACTOR", ACTOR)
        w.tmp = tmp_path
        code, out = _run_job(w, capsys, _approval(digest))
        assert code == sf.EXIT_MISMATCH and "receipt_brief_not_from_verifier" in out["detail"], out
        _nothing_written(w)
    finally:
        w.conn.execute("ALTER ROLE gochara_sealer NOLOGIN PASSWORD NULL")
