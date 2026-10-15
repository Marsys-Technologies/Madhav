"""C46 / A5.5g — round-2 regressions for PR 3110 (Fable, Stream B and Codex), on a real database wherever the defect lived there.

  * the in-build self-checks of a SLICED build (the `verify:<class>` substep and the P1 anchor check) are told the default
    scope's exclusion and behave exactly like a default build's — never `Unverifiable` for the scope word `test_slice`;
  * `ledger.publish` itself refuses a sliced candidate (the builder can UPDATE the publication table; the seal flow only refuses
    when a seal exists);
  * planning without a connection: a dry run plans the default, a LIVE call is refused by name (CI regression);
  * the REAL migration 595 trigger rejects a manifest change, and — with the trigger bypassed — the writer's own digest/marker
    check still refuses the changed run;
  * a `one_class_full` class A → class B transition ends equal to a fresh run of B;
  * a failure BETWEEN the manifest and the snapshot (a new manifest beside the old chain) is caught by the completeness gate and a
    retry repairs it to a fresh build's state;
  * the default (unsliced) verification control reaches the SAME precondition the sliced refusal is raised at, so the refusal is
    proved to be the slice's and not any unrelated early refusal."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import ledger
from services.gochara_kernel import rule_registry as rr
from services.gochara_kernel import verification_job as vj

from .conftest import EPHE_PATH
from .test_a55_replace_chain import CHART_ID, CLASSES, FULLL, GEN, LONG, SHORT, _World, _same, fresh, template  # noqa: F401
from .test_c46_slice_transitions import ALL_1Y, _SliceWorld, _iso, sworld  # noqa: F401

A, B = CLASSES


def _one_class_marker(cls):
    return {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": "one_class_full", "horizon": _iso(writer_mod.DEFAULT_HORIZON),
            "classes": [cls]}


def _head(w, rid, classes=()):
    w.step_as(writer_mod.MANIFEST_SUBSTEP, rid)
    w.step_as(writer_mod.SNAPSHOT_SUBSTEP, rid)
    for cls in classes:
        w.step_as(f"inventory:{cls}", rid)
        w.step_as(f"coverage:{cls}", rid)


# --- 1. the in-build self-checks of a sliced build -------------------------------------------------------------------------

def _spy_verifiers(monkeypatch):
    seen = {"rederive": [], "anchors": []}
    real_rederive = writer_mod.gk_verifier.rederive_inventory_digest

    def rederive(*a, **k):
        seen["rederive"].append(k.get("excluded_agents", "<absent>"))
        return real_rederive(*a, **k)
    monkeypatch.setattr(writer_mod.gk_verifier, "rederive_inventory_digest", rederive)

    def anchors(*a, **k):
        seen["anchors"].append(k.get("excluded_agents", "<absent>"))
        return {"checked": "spy"}
    monkeypatch.setattr(writer_mod, "verify_p1_anchors", anchors)
    return seen


def _verify_report(template, monkeypatch, sliced):
    """Run manifest, snapshot, inventory and verify of class A over FULLL — as a default build or under an all-classes slice of the
    SAME horizon — returning (the verify step's notes, what the rederivation was told)."""
    w = _SliceWorld(template)
    try:
        seen = _spy_verifiers(monkeypatch)
        # the contact-geometry certification has its own suite (R9-3) and needs the record grains built; it is stubbed identically
        # in both runs so that what differs is ONLY what the inventory re-derivation is told
        monkeypatch.setattr(writer_mod.gk_contact_certify, "certify_contact_geometry",
                            lambda *a, **k: {"obligations_certified": 0, "contacts_expected": 0, "named_limit": "stubbed"})
        if sliced:
            rid = w.run_id(w.marker_for(FULLL))
            horizon = None
        else:
            rid, horizon = w.run_id(None), FULLL
        w.step_as(writer_mod.MANIFEST_SUBSTEP, rid, horizon)
        w.step_as(writer_mod.SNAPSHOT_SUBSTEP, rid, horizon)
        w.step_as(f"inventory:{A}", rid, horizon)
        res = w.step_as(f"verify:{A}", rid, horizon)
        assert len(seen["rederive"]) == 1, seen
        return res.notes, seen["rederive"][0]
    finally:
        w.close()


def test_the_in_build_verify_step_of_a_sliced_build_is_told_the_default_exclusion_and_reports_like_a_default_build(template, monkeypatch):
    """Stream B P1: under `stored_scope = test_slice` the inventory re-derivation raised Unverifiable (an unknown scope word) at the
    first class, so a sliced build could never say its inventory was verified. It must report exactly what a default build reports."""
    default_notes, default_told = _verify_report(template, monkeypatch, sliced=False)
    sliced_notes, sliced_told = _verify_report(template, monkeypatch, sliced=True)
    assert default_told is None                                       # default: the verifier reads the manifest's own scope
    assert list(sliced_told) == ["moon"], sliced_told                  # slice: the DEFAULT scope's exclusion, told explicitly
    assert "not a scope this verifier knows" not in sliced_notes, sliced_notes
    # a slice adds ONE documented segment to the notes: the STRETCH_SINK/1 counts (MEASURING_BUILD_CONTRACT MB-2); everything else is what a default build reports
    import re
    stripped = re.sub(r"; stretch_sink/1: [^;]*?(?=; verification NOT persisted)", "", sliced_notes)
    assert "stretch_sink/1" in sliced_notes and "stretch_sink/1" not in default_notes
    assert stripped == default_notes, f"a sliced verify reported differently from a default one:\n{sliced_notes}\n{default_notes}"


def test_the_in_build_verify_step_would_refuse_a_slice_without_the_told_exclusion(template, monkeypatch):
    """The negative control that makes the test above discriminating: with the exclusion NOT told (the pre-fix behaviour) the same
    sliced step reports the unknown scope."""
    monkeypatch.setattr(writer_mod, "_slice_excluded_agents", lambda _s: None)
    notes, told = _verify_report(template, monkeypatch, sliced=True)
    assert told is None
    assert "not a scope this verifier knows" in notes and "UNVERIFIED" in notes, notes


def _p1_world(template, monkeypatch, marker_of):
    w = _SliceWorld(template)
    monkeypatch.setattr(writer_mod, "verify_p1_support", lambda *a, **k: None)              # their own suites; not what is under test
    monkeypatch.setattr(writer_mod, "verify_p1_house_descriptor", lambda *a, **k: None)
    rid = w.run_id(marker_of(w))
    horizon = None if marker_of(w) is not None else FULLL
    w.step_as(writer_mod.MANIFEST_SUBSTEP, rid, horizon)
    w.step_as(writer_mod.SNAPSHOT_SUBSTEP, rid, horizon)
    w.step_as(f"inventory:{A}", rid, horizon)
    w.step_as(f"coverage:{A}", rid, horizon)
    return w, rid, horizon


def test_the_p1_anchor_check_of_a_sliced_build_is_told_the_default_exclusion(template, monkeypatch):
    """Stream B P1, second call site: the P1 grain's `verify_p1_anchors` read the manifest scope and refused `test_slice`. Under a
    validated marker it is told the default scope's exclusion; a default build passes nothing (the manifest's scope is read)."""
    told = {}
    for name, marker_of in (("default", lambda w: None), ("sliced", lambda w: w.marker_for(FULLL))):
        w = None
        try:
            seen = _spy_verifiers(monkeypatch)
            w, rid, horizon = _p1_world(template, monkeypatch, marker_of)
            closed = writer_mod.p1_minting_closed_reason(w.conn)
            assert closed is None, f"P1 minting is closed here ({closed}); the anchor check would never run and this test would be vacuous"
            w.step_as(f"record:{A}:P1", rid, horizon)
            assert len(seen["anchors"]) == 1, (name, seen)
            told[name] = seen["anchors"][0]
        finally:
            if w is not None:
                w.close()
    assert told["default"] is None, told
    assert list(told["sliced"]) == ["moon"], told


def test_the_p1_anchor_check_would_refuse_a_slice_without_the_told_exclusion(template, monkeypatch):
    """The negative control: the REAL `verify_p1_anchors` (not the spy), with the exclusion not told, refuses the sliced manifest's
    scope — so the test above proves the fix and not a pass-through."""
    from services.gochara_kernel.inventory_verifier import Unverifiable
    monkeypatch.setattr(writer_mod, "_slice_excluded_agents", lambda _s: None)
    w = None
    try:
        w, rid, horizon = _p1_world(template, monkeypatch, lambda w: w.marker_for(FULLL))
        with pytest.raises(Unverifiable, match="not a scope this verifier knows"):
            w.step_as(f"record:{A}:P1", rid, horizon)
    finally:
        if w is not None:
            w.close()


# --- 2. direct publication ---------------------------------------------------------------------------------------------------

def _status(w):
    return w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE generation = %s", (GEN,)).fetchone()[0]


def test_publish_itself_refuses_a_sliced_candidate_by_name_and_leaves_it_a_candidate(sworld):
    """Codex P1: the builder holds UPDATE on the publication table, and `ledger.publish` flipped candidate -> published without
    reading the input vector (the seal flow refuses only when a seal exists). Either marker alone is enough to refuse."""
    rid = sworld.run_id(sworld.marker_for(FULLL))
    sworld.step_as(writer_mod.MANIFEST_SUBSTEP, rid)
    assert _status(sworld) == "candidate"
    with pytest.raises(ledger.TestSlicePublicationRefusal, match="TEST SLICE"):
        ledger.publish(sworld.conn, CHART_ID, GEN)
    assert _status(sworld) == "candidate"
    # the scope word alone, and the component alone (the vector is restored before each, the other marker removed behind the guards)
    original = sworld.conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE generation = %s",
                                   (GEN,)).fetchone()[0]
    for mutate in ("(%s::jsonb) - 'test_slice'",
                   "jsonb_set((%s::jsonb), '{stored_scope}', to_jsonb('stored_non_moon'::text))"):
        with sworld.conn.transaction():
            sworld.conn.execute("SET LOCAL session_replication_role = replica")
            sworld.conn.execute(f"UPDATE public.kala_gochara_publication SET input_generation_vector = {mutate} WHERE generation = %s",
                                (original, GEN))
        vector = sworld.conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication WHERE generation = %s",
                                     (GEN,)).fetchone()[0]
        assert ("test_slice" in vector) != (vector.get("stored_scope") == writer_mod.TEST_SLICE_SCOPE), vector     # exactly one marker left
        with pytest.raises(ledger.TestSlicePublicationRefusal):
            ledger.publish(sworld.conn, CHART_ID, GEN)
        assert _status(sworld) == "candidate"


def test_publish_still_publishes_a_default_candidate(template):
    """The control: the refusal does not over-block — a default (unsliced) candidate of the same shape is published."""
    w = _SliceWorld(template)
    try:
        w.step_as(writer_mod.MANIFEST_SUBSTEP, w.run_id(None), FULLL)
        assert _status(w) == "candidate"
        ledger.publish(w.conn, CHART_ID, GEN)
        assert _status(w) == "published"
    finally:
        w.close()


# --- 3. planning without a connection (the CI regression) --------------------------------------------------------------------

def test_planning_without_a_connection_is_the_default_plan_only_for_a_dry_run(monkeypatch):
    def ctx(dry):
        return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b", db_conn=None, dry_run=dry, config={"chart_id": CHART_ID})
    keys = [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(ctx(True))]
    classes = list(dict.fromkeys(k.split(":")[1] for k in keys if k.startswith("inventory:")))
    assert classes == list(writer_mod.SCORED_CLASSES), "a connection-free dry-run plan is the DEFAULT plan (all 26 classes)"
    first_writer = min(i for i, k in enumerate(keys) if k.startswith(("inventory:", "coverage:", "record:", "window:", "verify:")))
    assert keys.index(writer_mod.MANIFEST_SUBSTEP) < keys.index(writer_mod.SNAPSHOT_SUBSTEP) < first_writer
    with pytest.raises(writer_mod.TestSliceRefusal, match="needs a connection"):
        writer_mod.GocharaV5Writer().plan_substeps(ctx(False))                  # live + no connection: never the default plan


# --- 4. the real migration-595 trigger ---------------------------------------------------------------------------------------

def _real_595(w):
    """The REAL migration 595 applied to the world's build_runs stub (given the columns it triggers on)."""
    sql = Path(__file__).resolve().parents[4] / "supabase" / "migrations" / "595_nirmana_frozen_run_manifest.sql"
    assert sql.exists(), sql
    with w.conn.transaction():
        w.conn.execute("ALTER TABLE public.build_runs ADD COLUMN IF NOT EXISTS plan jsonb, ADD COLUMN IF NOT EXISTS chart_id uuid,"
                       " ADD COLUMN IF NOT EXISTS state text")
        w.conn.execute(sql.read_text())


def test_the_real_595_trigger_rejects_a_manifest_change_and_with_it_bypassed_the_writers_own_check_still_refuses(sworld):
    """Fable P1 (marker changed mid-run): citation `platform/supabase/migrations/595_nirmana_frozen_run_manifest.sql`, function
    `reject_build_run_manifest_mutation`, trigger `trg_build_runs_manifest_immutable`. Here the REAL SQL is applied and shown to (1)
    reject an UPDATE of the manifest or its digest with check_violation, (2) leave other columns updatable, and — because a trigger
    does not fire under `session_replication_role = replica` (a database superuser can bypass it) — (3) with the bypass used and the
    digest made to follow the new manifest, the writer's own validated-marker check still refuses the grain."""
    import psycopg
    _real_595(sworld)
    a_marker, b_marker = _one_class_marker(A), _one_class_marker(B)
    rid = sworld.run_id(a_marker)
    sworld.step_as(writer_mod.MANIFEST_SUBSTEP, rid)
    sworld.step_as(writer_mod.SNAPSHOT_SUBSTEP, rid)
    new_manifest = json.dumps({writer_mod.TEST_SLICE_KEY: b_marker})
    new_digest = writer_mod._manifest_digest({writer_mod.TEST_SLICE_KEY: b_marker})
    for col, val in (("plan_manifest = %s::jsonb", new_manifest), ("plan_manifest_digest = %s", new_digest)):
        with pytest.raises(psycopg.errors.CheckViolation, match="frozen manifest is immutable"):
            with sworld.conn.transaction():
                sworld.conn.execute(f"UPDATE public.build_runs SET {col} WHERE id = %s", (val, rid))
    with sworld.conn.transaction():
        sworld.conn.execute("UPDATE public.build_runs SET state = 'running' WHERE id = %s", (rid,))      # other columns stay open
    still = sworld.conn.execute("SELECT plan_manifest FROM public.build_runs WHERE id = %s", (rid,)).fetchone()[0]
    assert still == {writer_mod.TEST_SLICE_KEY: a_marker}, "the rejected UPDATEs changed the manifest"
    sworld.step_as(f"inventory:{A}", rid)                                                          # the unchanged run proceeds
    # the bypass: the trigger does not fire for a replica-role session; manifest and digest are rewritten together
    with sworld.conn.transaction():
        sworld.conn.execute("SET LOCAL session_replication_role = replica")
        sworld.conn.execute("UPDATE public.build_runs SET plan_manifest = %s::jsonb, plan_manifest_digest = %s WHERE id = %s",
                            (new_manifest, new_digest, rid))
    assert sworld.conn.execute("SELECT plan_manifest FROM public.build_runs WHERE id = %s", (rid,)).fetchone()[0] == \
        {writer_mod.TEST_SLICE_KEY: b_marker}, "the bypass should have changed the manifest (else this proves nothing)"
    before = sworld.state()
    with pytest.raises(writer_mod.TestSliceRefusal, match="not in the run's validated marker"):
        sworld.step_as(f"coverage:{A}", rid)
    assert sworld.state() == before


# --- 5. one_class_full: class A then class B -------------------------------------------------------------------------------------

def _class_state(w):
    inv = w.conn.execute("SELECT event_class, inventory_digest FROM public.ka_gochara_search_inventory WHERE generation = %s ORDER BY 1",
                         (GEN,)).fetchall()
    cov = w.conn.execute("SELECT partition_key, lower(completed_horizon), upper(completed_horizon) FROM public.kala_gochara_coverage"
                         " WHERE generation = %s AND partition_kind = 'event_class' ORDER BY 1", (GEN,)).fetchall()
    vec = w.conn.execute("SELECT input_generation_vector, horizon FROM public.kala_gochara_publication WHERE generation = %s",
                         (GEN,)).fetchone()
    return {"inventory": inv, "coverage": cov, "vector": vec[0], "horizon": vec[1]}


def test_one_class_full_class_a_then_class_b_ends_equal_to_a_fresh_run_of_b(template):
    """Codex: the transitions never ran a `one_class_full` class A -> class B change. The second run replaces the first run's whole
    chain (class A's inventory and coverage are gone), the stamp names B only, and every compared row equals a fresh B-only run's."""
    full = writer_mod.DEFAULT_HORIZON
    w, ctl = _SliceWorld(template), _SliceWorld(template)
    try:
        _head(w, w.run_id(_one_class_marker(A)), (A,))
        assert [r[0] for r in _class_state(w)["inventory"]] == [A]
        _head(w, w.run_id(_one_class_marker(B)), (B,))
        _head(ctl, ctl.run_id(_one_class_marker(B)), (B,))
        got, want = _class_state(w), _class_state(ctl)
        assert [r[0] for r in got["inventory"]] == [B] and [r[0] for r in got["coverage"]] == [B]
        assert got["vector"]["test_slice"]["classes"] == [B] and got["vector"]["stored_scope"] == writer_mod.TEST_SLICE_SCOPE
        assert (got["horizon"].lower, got["horizon"].upper) == tuple(full)
        assert got == want, "A-then-B differs from a fresh B-only run"
    finally:
        w.close()
        ctl.close()


# --- 6. a failure BETWEEN the manifest and the snapshot -------------------------------------------------------------------------

def _gate_names(w):
    return {v["violation"] for v in vj.candidate_gate_on_candidate_manifest(w.conn, CHART_ID, GEN)}


def test_a_failure_between_the_manifest_and_the_snapshot_is_caught_and_a_retry_repairs_it(sworld, fresh):
    """A new manifest (a different horizon) lands beside the OLD chain and the run dies before the snapshot substep. The old chain
    must not be mistaken for the new candidate's: the candidate gate reports `horizon_manifest_mismatch` for it, and the retry (a
    whole-build replay) ends equal to a fresh build of the new horizon."""
    sworld.full_build(SHORT)
    assert "horizon_manifest_mismatch" not in _gate_names(sworld)
    sworld.step_as(writer_mod.MANIFEST_SUBSTEP, sworld.run_id(None), LONG)                    # the failure: nothing after it ran
    assert sworld.conn.execute("SELECT count(*) FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchone()[0] > 0
    broken = _gate_names(sworld)
    assert "horizon_manifest_mismatch" in broken, broken
    sworld.full_build(LONG)                                                                   # the retry: a whole replay
    assert "horizon_manifest_mismatch" not in _gate_names(sworld)
    _same(sworld.state(), fresh(LONG), "failure between manifest and snapshot, then retry")


# --- 7. the default verification control ----------------------------------------------------------------------------------------

class _Reached(Exception):
    pass


def test_the_default_control_passes_every_refusal_before_the_input_check_and_a_slice_does_not(template, monkeypatch):
    """Codex: the default control accepted unrelated early refusals, so a slice refusal could hide behind another one. Both
    candidates are built the same way; `verify_inputs` (the first stage AFTER the sealed, slice and completeness refusals) is a
    sentinel. The default candidate must REACH it; the sliced one must be refused by name BEFORE it."""
    from services.gochara_kernel import input_vector_verifier as ivv
    armed = {"on": False}
    real = ivv.verify_inputs

    def boom(*a, **k):
        if armed["on"]:
            raise _Reached()
        return real(*a, **k)                                      # the BUILD's own substeps verify their inputs for real
    monkeypatch.setattr(ivv, "verify_inputs", boom)
    outcome = {}
    for name, marker_of in (("default", lambda w: None), ("sliced", lambda w: w.marker_for(FULLL))):
        w = _SliceWorld(template)
        try:
            marker = marker_of(w)
            rid = w.run_id(marker)
            horizon = None if marker is not None else FULLL
            w.step_as(writer_mod.MANIFEST_SUBSTEP, rid, horizon)
            w.step_as(writer_mod.SNAPSHOT_SUBSTEP, rid, horizon)
            w.step_as(f"inventory:{A}", rid, horizon)
            w.step_as(f"coverage:{A}", rid, horizon)
            armed["on"] = True
            try:
                vj.check_preconditions(w.conn, chart_id=CHART_ID, generation=GEN, classes=[A], ephe_path=EPHE_PATH,
                                       modules=iv.IMPLEMENTATION_MODULES, path_refs=list(rr.BOUND_PATH_REFS))
                outcome[name] = "passed"
            except _Reached:
                outcome[name] = "reached_input_check"
            except vj.VerificationRefused as exc:
                outcome[name] = exc.code
            finally:
                armed["on"] = False
        finally:
            w.close()
    assert outcome == {"default": "reached_input_check", "sliced": "test_slice_candidate"}, outcome


# --- 8. round 3 (Codex v1.2): atomic publication, the real verifier past the scope stage, the call-site guard --------------------

class _Recording:
    """Delegates to a real connection and records every statement (and the transactions opened)."""

    def __init__(self, conn):
        self._conn = conn
        self.statements: list[str] = []

    def execute(self, sql, params=None):
        self.statements.append(" ".join(str(sql).split()))
        return self._conn.execute(sql, params)

    def transaction(self):
        self.statements.append("<transaction>")
        return self._conn.transaction()


def test_publish_takes_the_chart_lock_before_its_first_read_in_a_transaction_of_its_own(sworld):
    """Codex round 3 P1: `publish` read the stamp with no lock. The chart transaction lock is now the first thing it does."""
    sworld.step_as(writer_mod.MANIFEST_SUBSTEP, sworld.run_id(None), FULLL)
    rec = _Recording(sworld.conn)
    ledger.publish(rec, CHART_ID, GEN)
    s = rec.statements
    assert s[0] == "<transaction>"
    assert "to_regprocedure('public.ka_gochara_lock_chart(uuid)')" in s[1] and "ka_gochara_lock_chart(%s::uuid)" in s[2]
    first_read = next(i for i, x in enumerate(s) if "FROM kala_gochara_publication" in x)
    assert first_read > 2, s[:5]
    assert _status(sworld) == "published"


def test_the_flip_alone_refuses_a_slice_even_when_the_earlier_checks_and_the_lock_are_bypassed(sworld, monkeypatch):
    """The UPDATE itself is conditional (still a candidate, no test_slice scope word, no component): with the pre-check and the lock
    both disabled, a slice-stamped candidate is still not published, and the refusal is by name."""
    rid = sworld.run_id(sworld.marker_for(FULLL))
    sworld.step_as(writer_mod.MANIFEST_SUBSTEP, rid)
    monkeypatch.setattr(ledger, "_refuse_test_slice_precheck", lambda *a, **k: None, raising=False)
    real_refuse = ledger._refuse_test_slice
    calls = []

    def refuse_only_after_the_flip(conn, manifest_id, generation):
        calls.append(1)
        if len(calls) == 1:
            return None                                              # the PRE-check is bypassed; the post-flip naming still runs
        return real_refuse(conn, manifest_id, generation)
    monkeypatch.setattr(ledger, "_refuse_test_slice", refuse_only_after_the_flip)
    monkeypatch.setattr(ledger, "_take_chart_lock", lambda *a, **k: None)
    with pytest.raises(ledger.TestSlicePublicationRefusal, match="TEST SLICE"):
        ledger.publish(sworld.conn, CHART_ID, GEN)
    assert len(calls) == 2 and _status(sworld) == "candidate"


def test_a_slice_stamped_between_the_publishers_start_and_its_read_is_never_published(sworld):
    """THE interleaving (Codex round 3): a competing session holds the chart lock and replaces the candidate's vector with a slice
    stamp, committing only after the publisher is already waiting. The publisher then reads the NEW vector and refuses; the
    manifest never becomes `published`. (The lock-first read and the conditional flip each close this alone — see the two tests
    above; removing BOTH lets the slice through.)"""
    import json
    import threading
    import time

    import psycopg
    sworld.step_as(writer_mod.MANIFEST_SUBSTEP, sworld.run_id(None), FULLL)          # an ordinary candidate
    assert _status(sworld) == "candidate"
    outcome: list = []

    def publisher():
        conn = psycopg.connect(sworld.dsn, autocommit=True, connect_timeout=3)
        try:
            ledger.publish(conn, CHART_ID, GEN)
            outcome.append("published")
        except BaseException as exc:                                  # noqa: BLE001
            outcome.append(exc)
        finally:
            conn.close()

    rival = psycopg.connect(sworld.dsn, autocommit=False, connect_timeout=3)
    thread = threading.Thread(target=publisher)
    try:
        rival.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        thread.start()
        deadline = time.time() + 20
        while time.time() < deadline:                                 # until the publisher is queued on the chart lock
            if sworld.conn.execute("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted").fetchone()[0]:
                break
            time.sleep(0.05)
        else:
            pytest.fail("the publisher never queued on the chart lock")
        stamp = {"stored_scope": "test_slice", "test_slice": {"run": "one_class_full", "classes": [A], "horizon": ["a", "b"]}}
        rival.execute("SET LOCAL session_replication_role = replica")
        rival.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = input_generation_vector || %s::jsonb"
                      " WHERE generation = %s", (json.dumps(stamp), GEN))
        rival.commit()                                                # releases the lock: the publisher proceeds
        thread.join(30)
    finally:
        rival.close()
    assert not thread.is_alive()
    assert len(outcome) == 1 and isinstance(outcome[0], ledger.TestSlicePublicationRefusal), outcome
    assert _status(sworld) == "candidate"
    assert sworld.conn.execute("SELECT count(*) FROM public.kala_gochara_publication WHERE status = 'published'").fetchone()[0] == 0


def test_the_real_p1_anchor_verifier_gets_past_the_scope_stage_under_a_slice_when_told_the_exclusion(sworld):
    """Codex round 3 (narrow test): the positive P1 test used a spy. Here the REAL `verify_p1_anchors` runs on a sliced manifest up
    to the ephemeris: told the default exclusion it reaches `position_at` (a sentinel proves the scope stage passed); told nothing
    it refuses the scope word. (The geometry itself is not run: P1 cannot pass on the stubbed L1 — a named limit.)"""
    from services.gochara_kernel import record_verifier as rv
    from services.gochara_kernel.inventory_verifier import Unverifiable
    rid = sworld.run_id(sworld.marker_for(FULLL))
    _head(sworld, rid, (A,))

    class _Reached(Exception):
        pass

    def position_at(body, t):
        raise _Reached()
    with pytest.raises(Unverifiable, match="not a scope this verifier knows"):
        rv.verify_p1_anchors(sworld.conn, chart_id=CHART_ID, generation=GEN, event_class=A, position_at=position_at)
    with pytest.raises(_Reached):
        rv.verify_p1_anchors(sworld.conn, chart_id=CHART_ID, generation=GEN, event_class=A, position_at=position_at,
                             excluded_agents=writer_mod._slice_excluded_agents(writer_mod._validate_test_slice(sworld.marker_for(FULLL))))


# --- 9. the public `excluded_agents` argument: only the two writer call sites pass it --------------------------------------------

def _excluded_agents_calls(root: Path):
    """Every call, anywhere under `root`, of the two public functions that take `excluded_agents`, with that keyword present:
    [(file name, function, source of the value)]."""
    import ast
    found = []
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            if func not in ("verify_p1_anchors", "rederive_inventory_digest"):
                continue
            for kw in node.keywords:
                if kw.arg == "excluded_agents":
                    found.append((path.name, func, ast.unparse(kw.value)))
    return found


def test_only_the_two_writer_sites_pass_excluded_agents_and_only_through_the_validated_marker():
    """`excluded_agents` is a public argument: any importing caller could pass a wrong exclusion and verify against it. The only
    non-test call sites that pass it are the writer's two, and both go through `_slice_excluded_agents(slice_)`, which returns
    something only for a marker that passed `_validate_test_slice`."""
    root = Path(__file__).resolve().parents[3]                     # python-sidecar
    calls = [c for c in _excluded_agents_calls(root) if "tests" not in c[0] and not c[0].startswith("test_")]
    prod = [c for c in _excluded_agents_calls(root / "pipeline")] + [c for c in _excluded_agents_calls(root / "services")]
    assert sorted(prod) == sorted([("ka_gochara_v5.py", "rederive_inventory_digest", "_slice_excluded_agents(slice_)"),
                                   ("ka_gochara_v5.py", "verify_p1_anchors", "_slice_excluded_agents(slice_)")]), prod
    assert calls == [] or all(c[0] == "ka_gochara_v5.py" for c in calls)


def test_the_call_site_guard_can_fail(tmp_path):
    """The guard is only worth having if it detects a third caller."""
    (tmp_path / "rogue.py").write_text("from x import verify_p1_anchors\nverify_p1_anchors(c, excluded_agents=('moon',))\n")
    assert _excluded_agents_calls(tmp_path) == [("rogue.py", "verify_p1_anchors", "('moon',)")]


# --- 10. round 4 (steward ruling on Codex v1.3): the lock and the slice condition are for GOVERNED generations only -------------

OTHER_CHART = "11111111-2222-3333-4444-555555555555"


def _legacy_candidate(w, chart, generation="4.1"):
    from services.gochara_kernel import record_store as rs
    convention = rs.RecordStore(w.conn).ensure_kala_convention()
    return ledger.publish_candidate(w.conn, chart, generation, convention, {"k": "v"}, {"backend": "swieph"},
                                    "[2020-01-01,2030-01-01)")


def test_the_gochara_5_lock_refuses_any_chart_but_the_canonical_one(sworld):
    """The premise of the regression: `ka_gochara_lock_chart` (1153) refuses every other chart, so a lock taken for a legacy flip of
    another chart would fail before the candidate was read."""
    import psycopg
    with pytest.raises(psycopg.errors.Error):
        with sworld.conn.transaction():
            sworld.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (OTHER_CHART,))


@pytest.mark.parametrize("chart", [OTHER_CHART, CHART_ID], ids=["non_canonical_chart", "canonical_chart"])
def test_a_legacy_generation_publishes_exactly_as_before_for_any_chart_with_no_lock_and_no_transaction_block(sworld, chart):
    """Steward ruling (Codex v1.3): legacy 3.x/4.x publication (step08_flip --chart-id other) must behave as on main. The recording
    wrapper shows no transaction block, no lock probe and no slice read; the row is published by the original flip."""
    _legacy_candidate(sworld, chart)
    rec = _Recording(sworld.conn)
    ledger.publish(rec, chart, "4.1")
    assert "<transaction>" not in rec.statements
    assert not any("ka_gochara_lock_chart" in s for s in rec.statements)
    assert not any("input_generation_vector" in s for s in rec.statements)            # no slice check, no conditional flip
    status = sworld.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '4.1'",
                                 (chart,)).fetchone()[0]
    assert status == "published"


def test_a_governed_generation_still_locks_first_and_a_legacy_one_is_told_apart_by_the_generation_alone(sworld):
    sworld.step_as(writer_mod.MANIFEST_SUBSTEP, sworld.run_id(None), FULLL)
    rec = _Recording(sworld.conn)
    ledger.publish(rec, CHART_ID, GEN)                            # '5.0'
    assert rec.statements[0] == "<transaction>" and "ka_gochara_lock_chart(%s::uuid)" in rec.statements[2]
    assert [ledger._candidate_boundary().is_governed(g) for g in ("3.0", "4.1", "5.0", "5.9", "6.0")] == [False, False, True, True, True]


def test_a_legacy_manifest_is_not_given_the_slice_condition(sworld):
    """A legacy vector never carries the slice words, and the flip is the original one: a legacy row whose vector happens to hold a
    `test_slice` key still publishes (the condition is a governed-generation rule)."""
    _legacy_candidate(sworld, CHART_ID)
    with sworld.conn.transaction():
        sworld.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = input_generation_vector || '{\"test_slice\": {}}'::jsonb"
                            " WHERE generation = '4.1'")
    ledger.publish(sworld.conn, CHART_ID, "4.1")
    assert sworld.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE generation = '4.1'").fetchone()[0] == "published"
