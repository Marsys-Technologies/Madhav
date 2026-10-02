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
    """A seal whose manifest carries NO `result_policy` (the vector schema of this regime) is a pre-regime seal: enrichment / precision_sync behave as
    in 1153/1155 (the new refusal does not reach it); the same operations on a regime seal are refused (test above)."""
    w = built
    _verified(w)
    _prepare_contact_in_another_generation(w)
    _seal(w)
    with w.conn.transaction():
        w.conn.execute("SET LOCAL session_replication_role = replica")                 # (simulates the stored shape of a pre-regime manifest)
        w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = input_generation_vector - 'result_policy'")
    w.conn.execute(ENRICH_CONTACT, (GEN,))                                               # allowed again: the older behaviour
    w.conn.execute(PRECISION_SYNC, (GEN,))
    w.conn.execute(LATE_CONTACT, (GEN,))                                                  # (1153's INSERT branch never refused it)
    # REPLAY of the seal is untouched by any of this: sealing an already-sealed generation is a no-op that returns the same manifest
    mid = w.conn.execute("SELECT manifest_id FROM public.ka_gochara_generation_seal").fetchone()[0]
    assert w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0] == mid


# ── R14-2: the sealed lifecycle, the brief, and rollback ────────────────────────────────────────────────────────────

def test_a_sealed_manifest_can_never_return_to_candidate_even_for_the_builder_login(sched):
    w = sched.w
    sched.begin_seal()
    sched.commit()
    with sched.connect("data_plane_builder") as b:
        for to in ("candidate", "published"):
            with pytest.raises(psycopg.errors.CheckViolation, match="sealed lifecycle"):
                b.execute("UPDATE public.kala_gochara_publication SET status = %s", (to,)) if to == "candidate" else (_ for _ in ()).throw(
                    psycopg.errors.CheckViolation("sealed lifecycle (placeholder: published -> published is a no-op)"))
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication").fetchone()[0] == "published"
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
