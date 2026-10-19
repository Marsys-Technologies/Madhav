"""A5.3 — Codex round 13, R13-2 (rank 1) and R13-5: the approved state is STABLE THROUGH COMMIT, and the sealer's own identity check.

R13-2: the seal's checks are reads; a read is no lock against a concurrent writer, and a deferred check can be run early (`SET CONSTRAINTS ALL
IMMEDIATE`). 1240 therefore makes every WRITER of the claimed boundary take the chart seal lock in the database — build coverage, the
publication identity, the legacy projection relations and the brief insert included — so a concurrent writer BLOCKS until the sealing transaction
commits and is then refused by the sealed-state guard. Every schedule here runs with TWO real connections as the real roles (builder / verifier /
sealer logins), no owner privileges, and — except the one marked MUTATION — no disabled triggers.

R13-5: `check_sealer_identity` refuses membership in every role that owns the Gochara tables (NOINHERIT membership included) and any table- or
column-level write grant on the verification tables and the brief table, proved with real sealer logins."""
from __future__ import annotations

import threading
import time

import psycopg
import pytest

# G8: this suite is NOT about the class census; it opts out BY NAME (see conftest.g8_census_opt_out and the guard in test_g8_class_census.py).
G8_CENSUS_OPT_OUT_REASON = "exercises the sealed-generation boundary after a real seal on a deliberate one-class marriage world"
pytestmark = pytest.mark.usefixtures("g8_census_opt_out")
from psycopg.conninfo import make_conninfo

from services.gochara_kernel import ledger as gk_ledger  # noqa: F401
from services.gochara_kernel import seal_brief as sb
from services.gochara_kernel import seal_flow as sf
from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import built, rworld  # noqa: F401
from .test_a53_r11_seal_brief import APPROVAL, EXECUTION, BRIEF_IDS, _brief_as_verifier, _sealer_stand_ins, _verified, _appr  # noqa: F401
from .test_a53_verification_job import PASSWORD
from .test_a53_window_verification_gate import SPANS, _boot_p3  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky  # noqa: F401

LATE_COVERAGE = ("INSERT INTO public.kala_gochara_coverage SELECT (jsonb_populate_record(NULL::public.kala_gochara_coverage,"
                 " to_jsonb(c) || jsonb_build_object('partition_key', 'zz_late_partition'))).* FROM public.kala_gochara_coverage c"
                 " WHERE c.partition_kind = 'event_class' LIMIT 1")
LATE_PUBLICATION_IDENTITY = "UPDATE public.kala_gochara_publication SET writer_asset_id = writer_asset_id || '-late'"
LATE_BRIEF = ("INSERT INTO public.ka_gochara_seal_brief (chart_id, generation, manifest_id, brief_digest, state_digest, runner_identity,"
              " producer_commit, image_digest, execution_id) VALUES (%s::uuid, %s, gen_random_uuid(), repeat('e', 64), repeat('0', 64),"
              " '{\"commit\": \"t\", \"implementation_digest\": \"t\"}'::jsonb, 't', 'sha256:' || repeat('1', 64), 'late-exec')")


class Schedule:
    """The sealer's transaction held open just before COMMIT, with every Python check already done, plus helpers to run a late writer."""

    def __init__(self, w):
        self.w = w
        self.threads: list[threading.Thread] = []
        self.outcome: dict[str, object] = {}
        _verified(w)
        self.digest = _brief_as_verifier(w, sealing_commit=APPROVAL["sealing_commit"])["sha256"]
        _sealer_stand_ins(w)
        for role in ("data_plane_builder", "gochara_verifier", "gochara_sealer"):     # (the helpers above re-lock the logins they use)
            w.conn.execute(f"ALTER ROLE {role} LOGIN PASSWORD '{PASSWORD}'")

    def connect(self, role, app=None):
        extra = {"application_name": app} if app else {}
        return psycopg.connect(make_conninfo(self.w.dsn, user=role, password=PASSWORD, **extra), autocommit=True, connect_timeout=5)

    def begin_seal(self, *, immediate=False):
        """The sealing transaction exactly as `execute_seal` runs it, up to — and not including — COMMIT."""
        self.sealer = self.connect("gochara_sealer")
        self.tx = self.sealer.transaction()
        self.tx.__enter__()
        sb.set_local_timeouts(self.sealer, statement="15min", lock="2min")
        vj.take_locks(self.sealer, CHART_ID)
        sf.seal_with_approval(self.sealer, chart_id=CHART_ID, generation=GEN, approved_digest=self.digest, **_appr(self.digest))
        if immediate:
            self.sealer.execute("SET CONSTRAINTS ALL IMMEDIATE")          # every deferred check runs NOW — nothing is re-checked at COMMIT

    def late_writer(self, name, role, sql, params=()):
        """Start a writer in its own connection and thread; it must BLOCK on the seal lock the sealer holds."""
        def run():
            try:
                c = self.connect(role, app=name)
                try:
                    c.execute(sql, params)
                    self.outcome[name] = "committed"
                finally:
                    c.close()
            except Exception as exc:  # noqa: BLE001 — the outcome IS the test
                self.outcome[name] = exc
        t = threading.Thread(target=run, daemon=True)
        t.start()
        self.threads.append(t)
        deadline = time.time() + 10
        while time.time() < deadline:
            if name in self.outcome:
                return                                                    # it did not block (the caller asserts on the outcome)
            n = self.w.conn.execute("SELECT count(*) FROM pg_stat_activity WHERE application_name = %s AND wait_event_type = 'Lock'",
                                    (name,)).fetchone()[0]
            if n:
                return
            time.sleep(0.05)
        raise AssertionError(f"writer {name} neither blocked nor finished")

    def commit(self):
        self.tx.__exit__(None, None, None)
        self.sealer.close()
        for t in self.threads:
            t.join(15)
            assert not t.is_alive(), "a late writer is still blocked after the sealing transaction committed"

    def close(self):
        for role in ("data_plane_builder", "gochara_verifier", "gochara_sealer"):
            self.w.conn.execute(f"ALTER ROLE {role} NOLOGIN PASSWORD NULL")


@pytest.fixture()
def sched(built):
    s = Schedule(built)
    yield s
    s.close()


def _attested_state_equals_state_now(w):
    attested = w.conn.execute("SELECT state_digest FROM public.ka_gochara_seal_brief ORDER BY brief_id DESC LIMIT 1").fetchone()[0]
    now = w.conn.execute("SELECT public.ka_gochara_brief_state_digest(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
    return attested == now


def _sealed(w) -> bool:
    return w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 1


# ── (i) / (ii): the builder inserts a build-coverage partition after the sealer's last Python check ────────────────

@pytest.mark.parametrize("immediate", [False, True], ids=["after_last_python_check", "after_SET_CONSTRAINTS_ALL_IMMEDIATE"])
def test_a_builder_coverage_insert_blocks_until_the_seal_commits_and_is_then_refused(sched, immediate):
    w = sched.w
    before = w.conn.execute("SELECT count(*) FROM public.kala_gochara_coverage").fetchone()[0]
    sched.begin_seal(immediate=immediate)
    sched.late_writer("late_coverage", "data_plane_builder", LATE_COVERAGE)
    assert "late_coverage" not in sched.outcome, "the late writer was not blocked by the sealing transaction"
    sched.commit()
    out = sched.outcome["late_coverage"]
    assert isinstance(out, psycopg.errors.CheckViolation) and "sealed boundary" in str(out), out
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_coverage").fetchone()[0] == before
    assert _sealed(w) and _attested_state_equals_state_now(w)               # the seal's attested state IS the state at COMMIT


def test_mutation_without_the_guard_the_late_coverage_row_commits_after_an_immediate_check_and_the_attested_state_is_wrong(sched):
    """The detector is the guard: with it disabled the schedule Codex derived succeeds — the late row commits, the seal commits, and the
    state attested by the receipt is no longer the state of the sealed generation."""
    w = sched.w
    w.conn.execute("ALTER TABLE public.kala_gochara_coverage DISABLE TRIGGER ka_gochara_boundary_1_write_guard")
    sched.begin_seal(immediate=True)
    sched.late_writer("late_coverage", "data_plane_builder", LATE_COVERAGE)
    assert sched.outcome.get("late_coverage") == "committed"                  # nothing blocked it
    sched.commit()
    assert _sealed(w) and not _attested_state_equals_state_now(w)


# ── (iii): the verifier inserts a later brief in the gap ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("immediate", [False, True], ids=["after_last_python_check", "after_SET_CONSTRAINTS_ALL_IMMEDIATE"])
def test_a_verifier_brief_inserted_in_the_gap_blocks_until_the_seal_commits_and_is_then_refused(sched, immediate):
    w = sched.w
    briefs = w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_brief").fetchone()[0]
    sched.begin_seal(immediate=immediate)
    sched.late_writer("late_brief", "gochara_verifier", LATE_BRIEF, (CHART_ID, GEN))      # a DIRECT insert: no job protocol, just the grant
    assert "late_brief" not in sched.outcome, "the verifier's direct INSERT was not serialized with the sealer"
    sched.commit()
    out = sched.outcome["late_brief"]
    assert isinstance(out, psycopg.errors.CheckViolation) and "brief_without_candidate" in str(out), out
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_seal_brief").fetchone()[0] == briefs
    assert _sealed(w) and _attested_state_equals_state_now(w)


# ── publication identity and the legacy projection relations ──────────────────────────────────────────────────────

def test_a_builder_change_of_the_manifest_identity_blocks_then_is_refused(sched):
    w = sched.w
    sched.begin_seal()
    sched.late_writer("late_identity", "data_plane_builder", LATE_PUBLICATION_IDENTITY)
    assert "late_identity" not in sched.outcome
    sched.commit()
    out = sched.outcome["late_identity"]
    assert isinstance(out, psycopg.errors.CheckViolation) and "sealed boundary" in str(out), out
    assert "-late" not in w.conn.execute("SELECT writer_asset_id FROM public.kala_gochara_publication").fetchone()[0]
    assert _sealed(w) and _attested_state_equals_state_now(w)


def test_a_sealed_manifest_may_still_be_superseded_but_never_changes_identity_or_is_deleted(built):
    w = built
    _verified(w)
    w.conn.execute("SELECT 1")
    # seal as the superuser path the other suites use (this test is about what the guard allows AFTER the seal)
    from .test_a53_window_verification_roles import _seal
    _seal(w)
    w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'superseded', superseded_at = now()")        # allowed: status only
    with pytest.raises(psycopg.errors.CheckViolation, match="sealed boundary"):
        w.conn.execute("UPDATE public.kala_gochara_publication SET row_counts = row_counts || '{\"late\": 1}'::jsonb")
    with pytest.raises(psycopg.errors.CheckViolation, match="sealed boundary"):
        w.conn.execute("UPDATE public.kala_gochara_publication SET content_digest = repeat('9', 64)")
    with pytest.raises(psycopg.errors.CheckViolation, match="sealed boundary"):
        w.conn.execute("DELETE FROM public.kala_gochara_publication")


def test_on_demand_moon_coverage_is_not_part_of_the_boundary_and_stays_writable_after_the_seal(built):
    w = built
    _verified(w)
    from .test_a53_window_verification_roles import _seal
    _seal(w)
    w.conn.execute(LATE_COVERAGE.replace("'event_class' LIMIT 1", "'event_class' LIMIT 0"))          # (shape check: the statement itself is valid)
    n = w.conn.execute("SELECT count(*) FROM public.kala_gochara_coverage WHERE partition_kind = 'moon_on_demand'").fetchone()[0]
    w.conn.execute(
        "INSERT INTO public.kala_gochara_coverage SELECT (jsonb_populate_record(NULL::public.kala_gochara_coverage,"
        " to_jsonb(c) || jsonb_build_object('partition_kind', 'moon_on_demand', 'partition_key', 'zz_moon_day'))).*"
        " FROM public.kala_gochara_coverage c WHERE c.partition_kind = 'event_class' LIMIT 1")
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_coverage WHERE partition_kind = 'moon_on_demand'").fetchone()[0] == n + 1
    with pytest.raises(psycopg.errors.CheckViolation, match="sealed boundary"):
        w.conn.execute(LATE_COVERAGE)                                                               # a BUILD partition: refused


def test_the_legacy_projection_relations_are_guarded_for_a_governed_generation_and_free_for_every_other(built):
    """A governed generation's row in a legacy relation takes the chart lock and is refused once sealed; a legacy generation's write is
    untouched — it neither takes the lock nor needs any function privilege."""
    w = built
    _verified(w)
    from .test_a53_window_verification_roles import _seal
    w.conn.execute("INSERT INTO public.kala_gochara_windows (chart_id, event_class, generation) VALUES (%s, 'marriage', '4.0')", (CHART_ID,))
    _seal(w)
    with pytest.raises(psycopg.errors.CheckViolation, match="sealed boundary"):
        w.conn.execute("INSERT INTO public.kala_gochara_windows (chart_id, event_class, generation) VALUES (%s, 'marriage', %s)", (CHART_ID, GEN))
    w.conn.execute("INSERT INTO public.kala_gochara_windows (chart_id, event_class, generation) VALUES (%s, 'marriage', '4.0')", (CHART_ID,))
    w.conn.execute("DELETE FROM public.kala_gochara_windows WHERE generation = '4.0'")


def test_the_inline_governed_test_is_the_same_text_as_ka_gochara_generation_governed(built):
    w = built
    for g in ("5.0", "5.1", "9.9", "10.0", "25.3", "4.0", "4.1", "3.0", "v1", "5", "5.", ".5", "05.0", "5.0.1", "", "x5.0", "5.0x"):
        inline = w.conn.execute("SELECT %s ~ '^([5-9]|[1-9][0-9]+)\\.[0-9]+$'", (g,)).fetchone()[0]
        defined = w.conn.execute("SELECT public.ka_gochara_generation_governed(%s)", (g,)).fetchone()[0]
        assert inline == defined, g
    src = w.conn.execute("SELECT prosrc FROM pg_proc WHERE proname = 'ka_gochara_boundary_write_guard'").fetchone()[0]
    assert "^([5-9]|[1-9][0-9]+)\\.[0-9]+$" in src


# ── R13-5: the sealer's own identity check ────────────────────────────────────────────────────────────────────────

def _check_as_sealer(w):
    w.conn.execute(f"ALTER ROLE gochara_sealer LOGIN PASSWORD '{PASSWORD}'")
    try:
        with psycopg.connect(make_conninfo(w.dsn, user="gochara_sealer", password=PASSWORD), autocommit=True) as c:
            return sf.check_sealer_identity(c)
    finally:
        w.conn.execute("ALTER ROLE gochara_sealer NOLOGIN PASSWORD NULL")


def test_the_clean_sealer_passes_its_own_identity_check(built):
    _sealer_stand_ins(built)
    assert _check_as_sealer(built) == {"login": "gochara_sealer", "session": "gochara_sealer"}


def test_membership_in_an_owner_role_is_refused_even_when_the_membership_is_noinherit(built):
    w = built
    _sealer_stand_ins(w)
    owner = w.conn.execute("SELECT pg_get_userbyid(c.relowner) FROM pg_class c WHERE c.oid = 'public.ka_gochara_contact'::regclass").fetchone()[0]
    w.conn.execute("ALTER ROLE gochara_sealer NOINHERIT")                           # NOINHERIT: no privilege flows, membership still exists
    w.conn.execute(f"GRANT {owner} TO gochara_sealer")
    try:
        with pytest.raises(sf.SealRefused, match=f"member of, {owner}, which OWNS the Gochara tables") as exc:
            _check_as_sealer(w)
        assert exc.value.code == "identity_not_sealer" and exc.value.exit_code == sf.EXIT_IDENTITY
    finally:
        w.conn.execute(f"REVOKE {owner} FROM gochara_sealer")
        w.conn.execute("ALTER ROLE gochara_sealer INHERIT")
    assert _check_as_sealer(w)["login"] == "gochara_sealer"                           # (and the check is clean again afterwards)


@pytest.mark.parametrize("grant,named", [
    ("GRANT INSERT (chart_id) ON public.ka_gochara_eval_window_verification TO gochara_sealer", "INSERT(chart_id) on ka_gochara_eval_window_verification"),
    ("GRANT UPDATE (status) ON public.ka_gochara_eval_window_verification TO gochara_sealer", "UPDATE(status) on ka_gochara_eval_window_verification"),
    ("GRANT INSERT (event_class) ON public.ka_gochara_search_inventory_verification TO gochara_sealer",
     "INSERT(event_class) on ka_gochara_search_inventory_verification"),
    ("GRANT UPDATE (generation) ON public.ka_gochara_search_inventory_verification TO gochara_sealer",
     "UPDATE(generation) on ka_gochara_search_inventory_verification"),
    ("GRANT INSERT (brief_digest) ON public.ka_gochara_seal_brief TO gochara_sealer", "INSERT(brief_digest) on ka_gochara_seal_brief"),
    ("GRANT INSERT ON public.ka_gochara_seal_brief TO gochara_sealer", "INSERT on ka_gochara_seal_brief"),
    ("GRANT INSERT ON public.ka_gochara_eval_window_verification TO gochara_sealer", "INSERT on ka_gochara_eval_window_verification"),
    ("GRANT UPDATE (window_id) ON public.ka_gochara_eval_window TO gochara_sealer", "UPDATE(window_id) on ka_gochara_eval_window"),
])
def test_a_column_or_table_write_on_a_verification_or_brief_table_is_refused_by_the_sealers_check(built, grant, named):
    w = built
    _sealer_stand_ins(w)
    w.conn.execute(grant)
    with pytest.raises(sf.SealRefused, match="beyond the seal set") as exc:
        _check_as_sealer(w)
    assert named in str(exc.value) and exc.value.exit_code == sf.EXIT_IDENTITY
