"""A5.3 — Codex round 14, R14-1 / R14-2 / F-R14-4: the sealed generation stays what its seal attested.

R14-1: 1153's contact guard checks sealing on DELETE only (INSERT and enrichment UPDATE proceed) and 1155 deliberately lets a sealed relationship
record's `precision` be re-synced. Both change DIGESTED fields after the seal. 1240 adds the sealed-state refusal to ka_gochara_contact INSERT /
UPDATE and to the record `precision` UPDATE, with an explicit historical scope: a generation sealed before this regime (a manifest WITHOUT a
`result_policy`) keeps the older behaviour. R14-2: the sealed LIFECYCLE is a whitelist (published -> superseded / rolled_back only — never back to
`candidate`), the brief insert refuses whenever a seal EXISTS (not by status), and `ledger.rollback` has an explicit metadata-only route for a sealed
generation. F-R14-4: TRUNCATE is refused on the four boundary relations while they hold governed rows. Real logins, two connections, no owner
privileges and no disabled triggers except where a test says MUTATION."""
from __future__ import annotations

import psycopg
import pytest

from services.gochara_kernel import ledger as gk_ledger

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import built, rworld  # noqa: F401
from .test_a53_r11_seal_brief import _verified  # noqa: F401
from .test_a53_r13_sealed_boundary import LATE_BRIEF, Schedule, _attested_state_equals_state_now, _sealed, sched  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky, _seal  # noqa: F401


def _prepare_contact_in_another_generation(w):
    """Codex's schedule step 1: a valid contact identity and an identical solved reading, prepared in another UNSEALED governed generation."""
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("CREATE TEMP TABLE _nid ON COMMIT DROP AS SELECT gen_random_uuid() AS cid")
        w.conn.execute(
            "INSERT INTO public.ka_gochara_contact_identity SELECT (jsonb_populate_record(NULL::public.ka_gochara_contact_identity,"
            " to_jsonb(i) || jsonb_build_object('contact_id', (SELECT cid FROM _nid), 'occurrence_ordinal', 1000))).*"
            " FROM public.ka_gochara_contact_identity i LIMIT 1")
        w.conn.execute(
            "INSERT INTO public.ka_gochara_contact SELECT (jsonb_populate_record(NULL::public.ka_gochara_contact,"
            " to_jsonb(c) || jsonb_build_object('generation', '5.1', 'contact_id', (SELECT cid FROM _nid), 'occurrence_ordinal', 1000))).*"
            " FROM public.ka_gochara_contact c WHERE c.generation = %s LIMIT 1", (GEN,))


LATE_CONTACT = ("INSERT INTO public.ka_gochara_contact SELECT (jsonb_populate_record(NULL::public.ka_gochara_contact,"
                " to_jsonb(c) || jsonb_build_object('generation', %s::text))).* FROM public.ka_gochara_contact c WHERE c.generation = '5.1'")
ENRICH_CONTACT = "UPDATE public.ka_gochara_contact SET delta_t = coalesce(delta_t, 0.0) WHERE generation = %s"      # a no-op value, still an UPDATE
PRECISION_SYNC = "UPDATE public.ka_gochara_relationship_record SET precision = precision WHERE generation = %s"      # 1155 'precision_sync' shape


# ── R14-1: Codex's exact schedule, then the post-seal paths ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("immediate", [True, False], ids=["after_SET_CONSTRAINTS_ALL_IMMEDIATE", "after_last_python_check"])
def test_a_builder_contact_insert_prepared_elsewhere_blocks_then_is_refused_after_the_seal_commits(sched, immediate):
    w = sched.w
    _prepare_contact_in_another_generation(w)
    before = w.conn.execute("SELECT count(*) FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchone()[0]
    sched.begin_seal(immediate=immediate)
    sched.late_writer("late_contact", "data_plane_builder", LATE_CONTACT, (GEN,))
    assert "late_contact" not in sched.outcome, "the builder's contact INSERT was not serialized with the sealer"
    sched.commit()
    out = sched.outcome["late_contact"]
    assert isinstance(out, psycopg.errors.CheckViolation) and "sealed boundary" in str(out), out
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchone()[0] == before
    assert _sealed(w) and _attested_state_equals_state_now(w)


def test_mutation_without_the_contact_guard_the_late_contact_commits_after_the_seal(sched):
    """The detector is the guard (1153 refuses sealed DELETE only): disabled, the builder's INSERT commits AFTER the seal and the digest moves."""
    w = sched.w
    _prepare_contact_in_another_generation(w)
    w.conn.execute("ALTER TABLE public.ka_gochara_contact DISABLE TRIGGER ka_gochara_boundary_1_write_guard")
    sched.begin_seal(immediate=True)
    sched.late_writer("late_contact", "data_plane_builder", LATE_CONTACT, (GEN,))
    sched.commit()
    assert sched.outcome["late_contact"] == "committed"
    assert _sealed(w) and not _attested_state_equals_state_now(w)


def test_after_the_seal_a_contact_append_enrichment_and_precision_propagation_are_all_refused(built):
    w = built
    _verified(w)
    _prepare_contact_in_another_generation(w)
    _seal(w)
    for sql, params, what in ((LATE_CONTACT, (GEN,), "contact INSERT"), (ENRICH_CONTACT, (GEN,), "contact enrichment UPDATE"),
                              (PRECISION_SYNC, (GEN,), "precision_sync")):
        with pytest.raises(psycopg.errors.CheckViolation, match="sealed boundary"):
            w.conn.execute(sql, params)
    # DELETE stays refused (by 1240's guard, which fires first, and by 1153's own — either message names the seal), and a candidate stays writable
    with pytest.raises((psycopg.errors.RaiseException, psycopg.errors.CheckViolation), match="SEALED"):
        w.conn.execute("DELETE FROM public.ka_gochara_contact WHERE generation = %s", (GEN,))
    w.conn.execute("UPDATE public.ka_gochara_contact SET delta_t = delta_t WHERE generation = '5.1'")


def test_historical_scope_a_generation_sealed_before_this_regime_keeps_the_older_behaviour(built):
    """A seal whose manifest carries NO `result_policy` (the vector schema of this regime) is a pre-regime seal: the REAL operations — a truncated ->
    exact enrichment flip (NULL-to-value) with its precision propagation, a direct precision restatement, a contact INSERT — behave as in 1153/1155
    (the new refusal does not reach them), by a non-owner holding the privileges; the same operations on a regime seal are refused (test below).
    Seal REPLAY is untouched."""
    w = built
    _enrichable_world(w)
    _prepare_contact_in_another_generation(w)
    _seal(w)
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")                 # (the stored shape of a pre-regime manifest)
        w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = input_generation_vector - 'result_policy'")
    with _builder(w) as b:
        b.execute(ENRICH, (GEN,))                                                       # allowed again: the older behaviour, really executed
        assert b.execute("SELECT delta_t FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchone()[0] == 3e-9
        assert b.execute("SELECT DISTINCT (precision ->> 'delta_t')::float8 FROM public.ka_gochara_relationship_record WHERE generation = %s"
                         " AND contact_id IS NOT NULL", (GEN,)).fetchall() == [(3e-9,)]          # …and its precision propagation really ran
        b.execute(PRECISION_SYNC, (GEN,))                                               # 1155's sealed precision_sync (restating the contact's own value)
        assert b.execute("SELECT DISTINCT (precision ->> 'delta_t')::float8 FROM public.ka_gochara_relationship_record WHERE generation = %s"
                         " AND contact_id IS NOT NULL", (GEN,)).fetchall() == [(3e-9,)]
        b.execute(LATE_CONTACT, (GEN,))                                                 # (1153's INSERT branch never refused it)
    # REPLAY of the seal is untouched by any of this: sealing an already-sealed generation is a no-op that returns the same manifest
    mid = w.conn.execute("SELECT manifest_id FROM public.ka_gochara_generation_seal").fetchone()[0]
    assert w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0] == mid


# ── R14-2: the sealed lifecycle, the brief, and rollback ────────────────────────────────────────────────────────────

def test_a_sealed_manifest_can_never_return_to_candidate_even_for_the_builder_login(sched):
    w = sched.w
    sched.begin_seal()
    sched.commit()
    with sched.connect("data_plane_builder") as b:
        with pytest.raises(psycopg.errors.CheckViolation, match="sealed lifecycle"):
            b.execute("UPDATE public.kala_gochara_publication SET status = 'candidate'")
        b.execute("UPDATE public.kala_gochara_publication SET status = 'published'")             # a no-op on a published manifest: harmless
        assert b.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "published"
        b.execute("UPDATE public.kala_gochara_publication SET status = 'rolled_back'")          # the whitelisted withdrawal
        for back in ("candidate", "published"):                                                  # …and there is no way back
            with pytest.raises(psycopg.errors.CheckViolation, match="sealed lifecycle"):
                b.execute("UPDATE public.kala_gochara_publication SET status = %s", (back,))
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "rolled_back"
    with pytest.raises(psycopg.errors.CheckViolation, match="sealed lifecycle"):
        w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'candidate'")                    # the superuser too (triggers on)


def test_the_whitelisted_sealed_transitions_work_and_retain_every_attested_row(built):
    w = built
    _verified(w)
    _seal(w)
    rows = lambda: [w.conn.execute(f"SELECT count(*) FROM public.{t}").fetchone()[0] for t in (  # noqa: E731
        "ka_gochara_relationship_record", "ka_gochara_eval_window", "ka_gochara_contact", "kala_gochara_coverage",
        "ka_gochara_generation_seal", "ka_gochara_seal_approval", "ka_gochara_seal_brief")]
    before = rows()
    gk_ledger.supersede(w.conn, CHART_ID, GEN)                                                                  # published -> superseded
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "superseded"
    with pytest.raises(psycopg.errors.CheckViolation, match="sealed lifecycle"):                                 # superseded -> published / candidate
        w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'published'")
    assert rows() == before


def test_a_sealed_generation_is_withdrawn_metadata_only_by_ledger_rollback_and_nothing_is_deleted(built):
    w = built
    _verified(w)
    _seal(w)
    rows = lambda: [w.conn.execute(f"SELECT count(*) FROM public.{t}").fetchone()[0] for t in (  # noqa: E731
        "ka_gochara_relationship_record", "ka_gochara_eval_window", "ka_gochara_contact", "kala_gochara_coverage",
        "ka_gochara_generation_seal", "ka_gochara_seal_approval")]
    before = rows()
    gk_ledger.rollback(w.conn, CHART_ID, GEN)
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "rolled_back"
    assert rows() == before and _sealed(w)                                           # the seal, the receipt and every attested row stay
    with pytest.raises(ValueError, match="cannot rollback"):
        gk_ledger.rollback(w.conn, CHART_ID, GEN)                                    # already withdrawn: refused by name


def test_rollback_of_an_unsealed_candidate_still_takes_the_row_deleting_route(built, monkeypatch):
    """The explicit sealed route is metadata-only; an UNSEALED generation keeps the C-1 row-deleting route (monkeypatched to observe it)."""
    w = built
    _verified(w)
    called = []
    monkeypatch.setattr(gk_ledger, "_delete_generation_rows", lambda conn, c, g: called.append((c, g)))
    gk_ledger.rollback(w.conn, CHART_ID, GEN)
    assert called == [(CHART_ID, GEN)]
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "rolled_back"


def test_a_brief_is_refused_whenever_a_seal_exists_even_if_the_status_were_edited(sched):
    """The attest trigger decides by the SEAL ROW, not by the manifest status: with the status forced back to 'candidate' behind the guard's back
    (a trigger-bypassing owner path), a direct verifier INSERT is still refused."""
    w = sched.w
    sched.begin_seal()
    sched.commit()
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'candidate'")
    with sched.connect("gochara_verifier") as v:
        with pytest.raises(psycopg.errors.CheckViolation, match="is SEALED"):
            v.execute(LATE_BRIEF, (CHART_ID, GEN))


# ── F-R14-4: TRUNCATE, and the inventory of what is guarded ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("table", ["kala_gochara_coverage", "kala_gochara_publication", "kala_gochara_windows"])
def test_truncate_of_a_boundary_relation_with_governed_rows_is_refused_and_leaves_them(built, table):
    w = built
    _verified(w)
    if table == "kala_gochara_windows":
        w.conn.execute("INSERT INTO public.kala_gochara_windows (chart_id, event_class, generation) VALUES (%s, 'marriage', %s)", (CHART_ID, GEN))
    n = w.conn.execute(f"SELECT count(*) FROM public.{table}").fetchone()[0]
    with pytest.raises((psycopg.errors.CheckViolation, psycopg.errors.RaiseException), match="TRUNCATE"):
        # (CASCADE where a foreign key points at the table: PostgreSQL refuses a plain TRUNCATE of a referenced table before any trigger runs)
        w.conn.execute(f"TRUNCATE public.{table}" + (" CASCADE" if table != "kala_gochara_windows" else ""))
    assert w.conn.execute(f"SELECT count(*) FROM public.{table}").fetchone()[0] == n


def test_a_boundary_relation_holding_only_legacy_generations_may_still_be_truncated(built):
    w = built
    w.conn.execute("INSERT INTO public.kala_gochara_windows (chart_id, event_class, generation) VALUES (%s, 'marriage', '4.0')", (CHART_ID,))
    w.conn.execute("TRUNCATE public.kala_gochara_windows")
    assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_windows").fetchone()[0] == 0


def test_the_guard_inventory_reads_what_is_guarded_and_shows_a_late_created_relation_as_unguarded(built):
    w = built
    inv = {r[0]: tuple(r[1:]) for r in w.conn.execute("SELECT * FROM public.ka_gochara_boundary_guard_inventory()").fetchall()}
    assert inv == {t: (True, True, True) for t in ("kala_gochara_contacts", "kala_gochara_coverage", "kala_gochara_publication",
                                                   "kala_gochara_windows")}
    w.conn.execute("DROP TABLE public.kala_gochara_windows")                              # a relation created AFTER 1240 ran shows as unguarded
    w.conn.execute("CREATE TABLE public.kala_gochara_windows (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, event_class text,"
                   " generation text NOT NULL, intensity numeric)")
    inv = {r[0]: tuple(r[1:]) for r in w.conn.execute("SELECT * FROM public.ka_gochara_boundary_guard_inventory()").fetchall()}
    assert inv["kala_gochara_windows"] == (True, False, False) and inv["kala_gochara_coverage"] == (True, True, True)


# ── test evidence (round 15): real transitions, real enrichment/propagation, and the chronological upgrade ──────────────────────

STATUSES = ("candidate", "published", "superseded", "rolled_back")


def _reach(w, b, status):
    """Put a SEALED manifest into `status`. superseded / rolled_back: the only legal path (as the builder login). `candidate`: a DELIBERATELY
    INCONSISTENT state (a seal exists beside a candidate manifest — unreachable through the guards; created by the trigger-bypassing owner path)
    so that the guard's decision from that source is tested too."""
    if status in ("superseded", "rolled_back"):
        b.execute("UPDATE public.kala_gochara_publication SET status = %s", (status,))
    elif status == "candidate":
        with w.conn.transaction():
            w.conn.execute("SET LOCAL session_replication_role = replica")
            w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'candidate'")


@pytest.mark.parametrize("src", STATUSES)                                      # 4 sources x 4 targets = 16 pairs (3 reachable + 1 inconsistent source)
@pytest.mark.parametrize("dst", STATUSES)
def test_every_sealed_lifecycle_transition_is_decided_as_the_whitelist_says(sched, src, dst):
    """EVERY (from, to) pair over the CHECK's four statuses (16 = 3 reachable sealed sources + the deliberately inconsistent candidate-with-seal
    source, each x 4 targets), for a sealed generation, as the builder login: allowed iff it is a no-op or published -> superseded / rolled_back."""
    sched.begin_seal()
    sched.commit()
    with sched.connect("data_plane_builder") as b:
        _reach(sched.w, b, src)
        assert b.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == src
        allowed = src == dst or (src == "published" and dst in ("superseded", "rolled_back"))
        if allowed:
            b.execute("UPDATE public.kala_gochara_publication SET status = %s", (dst,))
            assert b.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == dst
        else:
            with pytest.raises(psycopg.errors.CheckViolation, match="sealed lifecycle"):
                b.execute("UPDATE public.kala_gochara_publication SET status = %s", (dst,))
            assert b.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == src


def test_a_second_seal_of_a_sealed_generation_writes_nothing_and_a_duplicate_seal_row_is_refused(sched):
    w = sched.w
    sched.begin_seal()
    sched.commit()
    mid = w.conn.execute("SELECT manifest_id FROM public.ka_gochara_generation_seal").fetchone()[0]
    with sched.connect("gochara_sealer") as s:
        with s.transaction():
            s.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            assert s.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0] == mid   # replay: same manifest
        with pytest.raises(psycopg.errors.Error):                                       # a SECOND seal row for the same (chart, generation)
            s.execute("INSERT INTO public.ka_gochara_generation_seal (chart_id, generation, manifest_id) VALUES (%s::uuid, %s, %s::uuid)",
                      (CHART_ID, GEN, mid))
    for t in ("ka_gochara_generation_seal", "ka_gochara_seal_approval"):
        assert w.conn.execute(f"SELECT count(*) FROM public.{t}").fetchone()[0] == 1


def _enrichable_world(w):
    """A candidate whose contact has NULL enrichable columns (delta_t / delta_lambda) BEFORE verification, so a real NULL -> value enrichment
    exists after the seal. (Set up behind the guards — that is the world being tested, not the operation.)"""
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")
        # a TRUNCATED placeholder (1153 §6.1): exact time unknown, solver 'clipped_truncated' — its legitimate life includes a later enrichment flip
        w.conn.execute("UPDATE public.ka_gochara_contact SET t_exact = NULL, solver_method = 'clipped_truncated', coverage = '{\"truncated\": true}'::jsonb,"
                       " delta_t = NULL, delta_lambda = NULL, precision_regime = NULL WHERE generation = %s", (GEN,))
    _verified(w)
    # a principal that HOLDS the update privileges (the ordinary builder holds neither): the guard, not the ACL, must be what refuses
    w.conn.execute("GRANT UPDATE ON public.ka_gochara_contact TO data_plane_builder")
    w.conn.execute("GRANT UPDATE (precision) ON public.ka_gochara_relationship_record TO data_plane_builder")


ENRICH = ("UPDATE public.ka_gochara_contact SET t_exact = t_in, solver_method = 'swiss_refined', coverage = '{\"truncated\": false}'::jsonb,"
          " delta_t = 3e-9, delta_lambda = 0.00055555557, precision_regime = 'swiss_bisect_tol_1e-9d'"
          " WHERE generation = %s AND t_exact IS NULL")      # the real truncated -> exact NULL-to-value enrichment flip
PROPAGATE = ("UPDATE public.ka_gochara_relationship_record SET precision = '{\"delta_t\": 2e-9, \"delta_lambda\": 0.001, "
             "\"solver_method\": \"swiss_refined\"}'::jsonb WHERE generation = %s AND contact_id IS NOT NULL")


def test_a_real_null_to_value_enrichment_and_a_real_precision_restatement_are_refused_after_the_seal_as_a_non_owner(built):
    w = built
    _enrichable_world(w)
    _seal(w)
    before = w.conn.execute("SELECT to_jsonb(c) FROM public.ka_gochara_contact c WHERE generation = %s", (GEN,)).fetchall()
    prec = w.conn.execute("SELECT precision::text FROM public.ka_gochara_relationship_record WHERE generation = %s ORDER BY record_id", (GEN,)).fetchall()
    with _builder(w) as b:
        with pytest.raises(psycopg.errors.CheckViolation, match="sealed boundary"):
            b.execute(ENRICH, (GEN,))
        with pytest.raises(psycopg.errors.CheckViolation, match="sealed boundary"):
            b.execute(PROPAGATE, (GEN,))
    assert w.conn.execute("SELECT to_jsonb(c) FROM public.ka_gochara_contact c WHERE generation = %s", (GEN,)).fetchall() == before
    assert w.conn.execute("SELECT precision::text FROM public.ka_gochara_relationship_record WHERE generation = %s ORDER BY record_id", (GEN,)).fetchall() == prec


def test_the_same_enrichment_before_the_seal_and_in_a_pre_regime_generation_really_propagates_precision(built):
    """Control: the operations are real — on a candidate they enrich the contact and the AFTER trigger restates dependent records' precision."""
    w = built
    _enrichable_world(w)
    with _builder(w) as b:
        b.execute(ENRICH, (GEN,))
    assert w.conn.execute("SELECT delta_t FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchone()[0] is not None
    restated = w.conn.execute("SELECT DISTINCT (precision ->> 'delta_t')::float8 FROM public.ka_gochara_relationship_record WHERE generation = %s"
                              " AND contact_id IS NOT NULL", (GEN,)).fetchall()
    assert restated == [(3e-9,)]                                                                              # the propagation really ran


class _builder:
    """A real data_plane_builder LOGIN connection on the world's database."""
    def __init__(self, w):
        self.w = w

    def __enter__(self):
        from psycopg.conninfo import make_conninfo
        from .test_a53_verification_job import PASSWORD
        self.w.conn.execute(f"ALTER ROLE data_plane_builder LOGIN PASSWORD '{PASSWORD}'")
        self.c = psycopg.connect(make_conninfo(self.w.dsn, user="data_plane_builder", password=PASSWORD), autocommit=True)
        return self.c

    def __exit__(self, *exc):
        self.c.close()
        self.w.conn.execute("ALTER ROLE data_plane_builder NOLOGIN PASSWORD NULL")


def test_chronological_upgrade_a_generation_sealed_under_the_pre_1240_schema_then_1240_applied():
    """STATE and TEST what is and is not protected. A generation is sealed under the schema BEFORE 1240 (no receipt, no verification rows, a manifest
    without result_policy); then 1240 (and 1241) are applied on top. PROTECTED from then on: the sealed lifecycle (published -> candidate refused),
    brief insertion (a seal exists), TRUNCATE while governed rows exist, the first-seal rules for any NEW generation. NOT protected / not
    retroactive: the generation has no approval receipt (`ka_gochara_seal_receipt_missing` stays true and a receipt cannot be attached later),
    no verification attestations, and — by the regime scope — its contacts/precision keep the older behaviour. Replay still works.

    NARROWED CLAIM: this test does NOT execute contact enrichment / precision propagation on the upgraded generation (that needs a full contact +
    record world, which the empty pre-1240 mirror does not have); the historical behaviour of those operations is executed for real, as a non-owner,
    by `test_historical_scope_a_generation_sealed_before_this_regime_keeps_the_older_behaviour` on a generation whose manifest has the pre-regime
    shape. What THIS test proves about the upgrade is the lifecycle, brief, TRUNCATE, receipt and replay behaviour listed above."""
    import uuid
    from psycopg.conninfo import make_conninfo
    from .test_a53_inventory import ADMIN_DSN, MIGRATIONS, create_am5_database, drop_am5_database
    from services.gochara_kernel.record_store import RecordStore
    admin, name, dsn = create_am5_database("chron", faithful=True, apply_1240=False)
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            kala = RecordStore(conn).ensure_kala_convention()
            gk_ledger.publish_candidate(conn, CHART_ID, "5.0", kala, {"schema": "pre_1240_vector", "stored_scope": "stored_non_moon"}, {"backend": "swieph"},
                                        "[2020-01-01T00:00:00Z,2021-01-01T00:00:00Z)", writer_asset_id="ka_gochara_v5")
            gk_ledger.publish(conn, CHART_ID, "5.0")
            mid = conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, "5.0")).fetchone()[0]
        assert conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "published"
        # BEFORE 1240: nothing stops a sealed manifest going back to 'candidate' (the R14-2 exposure) — and it can be put back
        conn.execute("UPDATE public.kala_gochara_publication SET status = 'candidate'")
        conn.execute("UPDATE public.kala_gochara_publication SET status = 'published'")
        for fname in ("1240_gochara_window_verification_gate.sql", "1241_gochara_verifier_sealer_inventory_grants.sql"):
            conn.execute((MIGRATIONS / fname).read_text())
        # AFTER 1240
        with pytest.raises(psycopg.errors.CheckViolation, match="sealed lifecycle"):
            conn.execute("UPDATE public.kala_gochara_publication SET status = 'candidate'")                       # PROTECTED
        assert conn.execute("SELECT public.ka_gochara_seal_receipt_missing(%s::uuid, %s)", (CHART_ID, "5.0")).fetchone()[0] is True   # NOT retroactive
        assert conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 0
        with pytest.raises(psycopg.errors.CheckViolation):                                                          # no receipt can be attached later
            with conn.transaction():
                conn.execute("INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id,"
                             " producer_execution_id, approver_login, approved_by_note, run_id, run_attempt, workflow_commit)"
                             " VALUES (%s::uuid, '5.0', %s::uuid, repeat('a', 64), 1, 'e', 'x', 'x', 1, 1, 'abc1234')", (CHART_ID, mid))
        with pytest.raises(psycopg.errors.CheckViolation, match="is SEALED"):                                       # PROTECTED: no brief for a seal
            conn.execute("INSERT INTO public.ka_gochara_seal_brief (chart_id, generation, manifest_id, brief_digest, state_digest, runner_identity,"
                         " producer_commit, image_digest, execution_id) VALUES (%s::uuid, '5.0', %s::uuid, repeat('b', 64), repeat('0', 64),"
                         " '{\"commit\": \"t\", \"implementation_digest\": \"t\"}'::jsonb, 't', 'sha256:' || repeat('1', 64), 'e')", (CHART_ID, mid))
        with pytest.raises(psycopg.errors.CheckViolation, match="TRUNCATE"):                                        # PROTECTED
            conn.execute("TRUNCATE public.kala_gochara_publication CASCADE")
        # REPLAY of the pre-1240 seal still works and writes no receipt
        with conn.transaction():
            conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            assert conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, "5.0")).fetchone()[0] == mid
        assert conn.execute("SELECT count(*) FROM public.ka_gochara_seal_approval").fetchone()[0] == 0
        assert conn.execute("SELECT input_generation_vector ? 'result_policy' FROM public.kala_gochara_publication").fetchone()[0] is False  # regime scope
        conn.close()
    finally:
        drop_am5_database(admin, name)
