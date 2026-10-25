"""SR-RESUME-NOW (OWNER-RESUMABLE-REQUIRED-20261025): the century build's writer-side RESUME — the committed-substep ledger (migration 1410).

The frozen orchestrator never feeds `completed_keys`, so a failed century build used to restart from zero. The writer now records each substep in
`ka_gochara_build_ledger` INSIDE the substep's transaction and, on the next dispatch, plans only what is not recorded — after proving the program, the horizon,
the manifest and every recorded substep's rows unchanged. Every test below drives the REAL writer through the REAL orchestrator driver
(`asset_runner._drive_substeps`, called as production calls it: no `completed_keys`, a SAVEPOINT and a commit per substep) on the real migration chain.

CLAIMS, each with its own fail-on-revert oracle (the planted reversion is named in the docstring):
  A. no ledger => today's behaviour: a non-century run records nothing and plans the whole plan; a ledger-active fresh build leaves the chain byte-equal to it
  B. kill at substep N + resume == a fresh build, byte for byte, AND the recorded substeps (manifest, snapshot among them) provably did not run again
  C. a resume under a different program (implementation digest, writer digest), horizon, plan, or manifest (incl. its horizon_basis pin) REFUSES by name, writing nothing
  D. tamper: a recorded substep's rows changed / a ledger gap / an orphan chain row => refused naming the substep
  E. atomicity: an aborted substep leaves NO ledger row and no data
  F. the century teardown clears the ledger
  G. the sealer refuses a generation several executions produced (the seal does not yet record the producer list)
Governing sources: root CLAUDE.md §N.2 (frozen contract), §N.3 (per-chart delete-then-insert), §N.8 (a signal is earned by a detector that can read false);
migration 436's header (completed_keys never fed); the ruling SR-RESUME-NOW.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import build_ledger as bl
from services.gochara_kernel import input_vector as iv

from .conftest import EPHE_PATH
from .test_a53_inventory import CHART_ID
from .test_a55_replace_chain import CLASSES, PATHS, SHORT, LONG, _World, template  # noqa: F401  (template is a fixture)

GEN = writer_mod.GENERATION
MIGRATION = Path(__file__).resolve().parents[4] / "migrations" / "1410_ka_gochara_build_ledger.sql"

PLAN_KEYS = {writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP}
for _c in CLASSES:
    PLAN_KEYS |= {f"inventory:{_c}", f"coverage:{_c}"} | {f"record:{_c}:{p}" for p in PATHS}
    PLAN_KEYS |= {f"window:{_c}:{p}" for p in PATHS if p in writer_mod.WINDOW_PATHS}


class _Subset(writer_mod.GocharaV5Writer):
    """The REAL writer over a SUBSET plan (the manifest, the snapshot, two classes' inventory / coverage / record / window grains): the full plan is the full
    build, which a unit test must not run. `_full_plan` is the one place the plan is built, so the ledger's ordinals, plan digest and prefix check all see this
    subset as THE plan. `kill_after` raises once the named substep has written its data AND its ledger row (so the orchestrator's savepoint must undo both)."""
    kill_after = None
    extra: tuple = ()

    def __init__(self):
        self.ran: list[str] = []

    def _full_plan(self, classes):                                   # an instance method here: the base's is static, the call site is `self._full_plan(...)`
        plan = [st for st in writer_mod.GocharaV5Writer._full_plan(classes) if st.key in PLAN_KEYS]
        return plan + [SubStep(key=k, label=k) for k in self.extra]

    def run_substep(self, ctx, step):
        self.ran.append(step.key)
        result = super().run_substep(ctx, step)
        if step.key == self.kill_after:
            raise RuntimeError(f"injected kill after {step.key}")
        return result


class _Harness:
    def __init__(self, template):
        import psycopg
        from psycopg.rows import dict_row
        self.w = _World(template)
        self.w.conn.execute(MIGRATION.read_text())
        self.w.conn.execute("CREATE TABLE public.build_runs (id uuid PRIMARY KEY, created_at timestamptz NOT NULL DEFAULT now(),"
                            " plan_manifest jsonb, plan_manifest_digest text)")
        self.w.conn.execute("CREATE TABLE public.asset_throughput (chart_id uuid, asset_id text, state text, last_built_at timestamptz,"
                            " rows_written integer, last_error text)")
        self.w.conn.execute("INSERT INTO public.asset_throughput VALUES (%s::uuid, %s, 'building', now(), 0, NULL)", (CHART_ID, writer_mod.ASSET_ID))
        self.conn = psycopg.connect(self.w.dsn, autocommit=False, row_factory=dict_row, connect_timeout=3)      # the orchestrator's connection
        self.chart = uuid.UUID(CHART_ID)

    def close(self):
        self.conn.close()
        self.w.close()

    def _ctx(self, horizon, century, birth=False):
        run_id = str(uuid.uuid4())
        config = {"chart_id": self.chart, "ephe_path": EPHE_PATH}
        if birth:                                                      # what the production orchestrator always supplies; the harness omits it (no pin is derived)
            config["birth_params"] = {"datetime_iso": "1984-02-05T10:43:00+05:30"}
        if century:
            manifest = {writer_mod.CENTURY_CONFIG_KEY: {
                "schema": writer_mod.CENTURY_CONFIG_SCHEMA, "final_rules": False, "defer_in_build_verify": False,
                "horizon": [horizon[0].isoformat(), horizon[1].isoformat()], "result_policy": "all_null_candidate/1"}}
            self.w.conn.execute("INSERT INTO public.build_runs (id, plan_manifest, plan_manifest_digest) VALUES (%s::uuid, %s::jsonb, %s)",
                                (run_id, json.dumps(manifest), writer_mod._manifest_digest(manifest)))
        else:
            config.update(gochara_v5_final_rules=False, horizon=horizon)
        return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=run_id, db_conn=self.conn, dry_run=False, config=config)

    def dispatch(self, writer, horizon=SHORT, century=True, birth=False):
        """One dispatch exactly as the orchestrator makes it; a failure is rolled back as the orchestrator does."""
        from pipeline.orchestrator import asset_runner
        ctx = self._ctx(horizon, century, birth)
        try:
            asset_runner._drive_substeps(self.conn, self.conn.cursor(), ctx.build_id, self.chart, writer_mod.ASSET_ID, writer, ctx)
        except BaseException:
            self.conn.rollback()
            raise
        return ctx.build_id

    def plan(self, writer, horizon=SHORT, century=True, birth=False):
        ctx = self._ctx(horizon, century, birth)
        try:
            return [s.key for s in writer.plan_substeps(ctx)]
        finally:
            self.conn.rollback()                                            # a plan is a read; end its transaction

    # state, read on the autocommit connection (committed rows only)
    def ledger(self):
        return [r[0] for r in self.w.conn.execute(
            f"SELECT substep_key FROM public.{bl.TABLE} WHERE chart_id = %s::uuid AND generation = %s ORDER BY ordinal", (CHART_ID, GEN)).fetchall()]

    def chain(self):
        """(rows, content digest) of every generation-scoped table, volatile columns excluded — the byte-identity oracle."""
        out = {}
        with bl.pinned_session(self.w.conn):
            for t, extra in (("kala_gochara_publication", ""), ("ka_gochara_search_input_snapshot", ""), ("ka_gochara_search_inventory", ""),
                             ("ka_gochara_search_path_pin", ""), ("ka_gochara_search_obligation", ""), ("ka_gochara_search_interval", ""),
                             ("kala_gochara_coverage", " AND partition_kind = 'event_class'"), ("ka_gochara_relationship_record", ""),
                             ("ka_gochara_record_prerequisite", ""), ("ka_gochara_contact", ""), ("ka_gochara_eval_window", ""),
                             ("ka_gochara_eval_window_record", "")):
                out[t] = bl.table_digest(self.w.conn, t, "chart_id = %s AND generation = %s" + extra, (CHART_ID, GEN))
        return out


@pytest.fixture()
def h(template):
    harness = _Harness(template)
    try:
        yield harness
    finally:
        harness.close()


@pytest.fixture(scope="module")
def fresh(template):
    """The FRESH century build's chain digests, built once: the control every resume must equal."""
    harness = _Harness(template)
    try:
        writer = _Subset()
        harness.dispatch(writer)
        yield {"chain": harness.chain(), "ledger": harness.ledger(), "ran": list(writer.ran)}
    finally:
        harness.close()


def _plan_order():
    return [st.key for st in _Subset()._full_plan(writer_mod.SCORED_CLASSES)]


def test_the_ledger_pins_the_same_text_rendering_settings_as_the_seal_brief():
    """The writer cannot import the sealing side, so build_ledger restates PINNED_SETTINGS: this ties the copy to the original."""
    from services.gochara_kernel import seal_brief
    assert bl.PINNED_SETTINGS == seal_brief.PINNED_SETTINGS


# ── A. no ledger => today's behaviour ───────────────────────────────────────────────────────────────────────────────────────────

def test_a_fresh_century_build_records_every_substep_and_leaves_the_chain_byte_equal_to_a_ledger_free_build(h, fresh, template):
    """The ledger is bookkeeping: it changes no chain byte. The control is a NON-century run of the same plan (no ledger rows, the pre-change path).
    Revert: make the ledger leak into the chain (e.g. a century run that writes different rows) and the digests differ; make `_ledger_active` always True and the
    non-century run below records rows."""
    plain = _Harness(template)
    try:
        writer = _Subset()
        plain.dispatch(writer, century=False)
        assert plain.ledger() == [], "a non-century run recorded ledger rows: it must keep its whole-build replay semantics"
        assert plain.plan(_Subset(), century=False) == _plan_order(), "a non-century run's plan must be the whole plan"
        assert plain.chain() == fresh["chain"], "the ledger changed the chain"
    finally:
        plain.close()
    assert fresh["ledger"] == _plan_order() == fresh["ran"], "every substep of a fresh century build records itself, in plan order"


def test_a_complete_ledger_plans_nothing_and_every_recorded_scope_still_measures_equal(h, fresh):
    """The end state of a clean build is resumable-to-nothing (the orchestrator's SATYA-DIPA probe reads an empty plan as complete), and the scopes re-measure equal
    (no false tamper on a healthy chain: the digests exclude exactly the write-time columns)."""
    writer = _Subset()
    h.dispatch(writer)
    assert h.plan(_Subset()) == []
    entries = bl.load(h.w.conn, CHART_ID, GEN)
    bl.verify_chain(h.w.conn, CHART_ID, GEN, entries)
    assert {e.substep_key for e in entries if e.scope is None} == set(), "a chain substep recorded no scope"


def test_a_global_substep_records_an_honest_null_scope(h):
    """`convention` owns no chart x generation rows: its scope is NULL (never an invented digest), and it is still recorded with its binding."""
    writer = writer_mod.GocharaV5Writer()
    ctx = h._ctx(SHORT, True)
    writer.run_substep(ctx, SubStep(key=writer_mod.CONVENTION_SUBSTEP, label="convention"))
    h.conn.commit()
    (entry,) = bl.load(h.w.conn, CHART_ID, GEN)
    assert (entry.substep_key, entry.scope, entry.scope_digest, entry.manifest_id, entry.ordinal) == (writer_mod.CONVENTION_SUBSTEP, None, None, None, 1)


def test_a_century_run_on_a_schema_without_the_ledger_is_refused_by_name_and_the_sealer_read_does_not_abort(h):
    """A century run that cannot record its progress must not run unrecoverable (migration 1410 not applied): `build_ledger_absent`. The sealer's producer read on such a
    schema answers 'none' without aborting its transaction. Revert: swallow the absence in `load` => the run proceeds with no ledger."""
    h.w.conn.execute(f"DROP TABLE public.{bl.TABLE}")
    with pytest.raises(bl.ResumeRefused) as exc:
        h.plan(_Subset())
    assert exc.value.code == "build_ledger_absent"
    with h.w.conn.transaction():
        assert bl.producer_executions(h.w.conn, CHART_ID, GEN) == []
        h.w.conn.execute("SELECT 1")                                # the transaction is still usable


def test_the_century_marker_is_the_writers_own_and_a_caller_cannot_set_it(h):
    """A harness cannot switch a run into century mode (and its ledger) by config. Revert: accept the key from ctx.config => no refusal."""
    ctx = h._ctx(SHORT, False)
    ctx.config[writer_mod.CENTURY_STAGED_KEY] = True
    with pytest.raises(writer_mod.CenturyConfigRefusal, match="by nothing else"):
        _Subset().plan_substeps(ctx)
    h.conn.rollback()


# ── B. kill at substep N + resume == fresh ────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kill_after", ["snapshot", f"inventory:{CLASSES[0]}", f"record:{CLASSES[0]}:P2", f"coverage:{CLASSES[1]}"])
def test_kill_at_substep_n_then_resume_equals_a_fresh_build_and_does_not_rerun_recorded_substeps(h, fresh, kill_after):
    """THE oracle. Dispatch 1 dies right after `kill_after` wrote its data and its ledger row (the savepoint undoes both). Dispatch 2 resumes: the chain ends byte-equal to a
    fresh build, and the substeps recorded before the kill — the head (manifest, snapshot) above all — are NOT run again. Equality alone would also hold for a whole-plan
    replay (G-7: a replay equals a fresh build), so the detector is the skip witness: the list of substeps dispatch 2 ran, and the xmin of the rows dispatch 1 committed.
    Revert: plan_substeps ignores the ledger (full replay) => the witness fails (manifest/snapshot run twice, xmin moves)."""
    order = _plan_order()
    first = _Subset()
    first.kill_after = kill_after
    with pytest.raises(RuntimeError, match="injected kill"):
        h.dispatch(first)
    recorded = h.ledger()
    assert recorded == order[:order.index(kill_after)], "the killed substep must NOT be recorded (its transaction was rolled back); every earlier one must"
    contacts_before = dict(h.w.conn.execute("SELECT contact_id::text, xmin::text FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchall())

    second = _Subset()
    h.dispatch(second)
    assert second.ran == order[order.index(kill_after):], "the resume must run exactly the substeps that were not recorded"
    ran = first.ran + second.ran
    assert ran.count(writer_mod.MANIFEST_SUBSTEP) == 1, "the manifest substep ran twice: the resume silently rebound the manifest"
    assert ran.count(writer_mod.SNAPSHOT_SUBSTEP) == (2 if kill_after == writer_mod.SNAPSHOT_SUBSTEP else 1), "the snapshot substep (the chain replace) ran again after it was recorded"
    contacts_after = dict(h.w.conn.execute("SELECT contact_id::text, xmin::text FROM public.ka_gochara_contact WHERE generation = %s", (GEN,)).fetchall())
    assert all(contacts_after[k] == v for k, v in contacts_before.items()), "rows dispatch 1 committed were rewritten by the resume"
    assert h.chain() == fresh["chain"], "kill + resume is not byte-equal to a fresh build"
    assert h.ledger() == order
    produced = bl.producer_executions(h.w.conn, CHART_ID, GEN)
    assert len(produced) == (2 if recorded else 1), "the ledger must name both producer runs"


# ── C. a different program / horizon / plan / manifest refuses by name ────────────────────────────────────────────────────────────────

def _killed(h, kill_after=f"record:{CLASSES[0]}:P2"):
    first = _Subset()
    first.kill_after = kill_after
    with pytest.raises(RuntimeError, match="injected kill"):
        h.dispatch(first)
    return h.chain(), h.ledger()


def _refused_with_nothing_written(h, code, expect_in_message=(), writer=None, **kw):
    chain, ledger = h.chain(), h.ledger()
    writer = writer or _Subset()
    with pytest.raises(bl.ResumeRefused) as exc:
        h.dispatch(writer, **kw)
    assert exc.value.code == code, str(exc.value)
    for text in expect_in_message:
        assert text in str(exc.value), (text, str(exc.value))
    assert writer.ran == [], "a refused resume must run no substep"
    assert (h.chain(), h.ledger()) == (chain, ledger), "a refused resume wrote something"
    return exc.value


def test_a_resume_under_a_different_source_digest_refuses_naming_both_digests(h, monkeypatch):
    """A governed module changed between the kill and the resume (a program fix): the implementation digest the ledger recorded is not the one running now.
    Revert: drop the implementation_digest check in `check_binding` => this reaches only the deeper live-input check (next test), so the first-layer assertions fail."""
    from services.gochara_kernel import window_gate
    _killed(h)
    real = window_gate.implementation_digest
    monkeypatch.setattr(window_gate, "implementation_digest", lambda *a, **k: "f" * 64 if real(*a, **k) else real(*a, **k))
    err = _refused_with_nothing_written(h, "resume_program_changed", ("implementation_digest", "recorded", "running now", "f" * 64))
    assert set(err.keys) >= {"manifest", "snapshot"}


def test_a_resume_whose_governed_source_changed_is_refused_by_the_live_input_check_naming_the_component(h, monkeypatch):
    """The second layer: the manifest's own input vector (implementation digests per stage, ephemeris, runtime library, registry) re-derived live. Revert: do not call
    `_verify_live_inputs` at plan time => the resume is planned and the refusal only comes (if at all) at the first substep, after the plan was accepted."""
    _killed(h)
    real = iv._module_source_digest
    monkeypatch.setattr(iv, "_module_source_digest",
                        lambda name: real(name) + "x" if name == "services.gochara_kernel.evaluator" else real(name))
    _refused_with_nothing_written(h, "resume_program_changed", ("implementation.evaluation", "InputDrift"))


def test_a_resume_under_a_different_writer_digest_refuses(h, monkeypatch):
    _killed(h)
    monkeypatch.setattr(writer_mod, "_writer_digest", lambda: "0" * 64)
    _refused_with_nothing_written(h, "resume_program_changed", ("writer_digest",))


def test_a_resume_under_a_different_horizon_refuses(h):
    _killed(h)
    _refused_with_nothing_written(h, "resume_horizon_changed", ("recorded horizon",), horizon=LONG)


def test_a_resume_under_a_changed_plan_refuses(h):
    _killed(h)
    writer = _Subset()
    writer.extra = ("window:marriage:P3_extra",)                       # a longer plan: the recorded keys are still its prefix, the plan digest is not
    _refused_with_nothing_written(h, "resume_plan_changed", ("plan_digest",), writer=writer)


def test_a_resume_refuses_a_manifest_whose_horizon_basis_pin_changed(h):
    """FB-2 / SR-J4E-POSTRUN-READBACKS: a resume skips the manifest substep, so the pin the manifest carries must survive unchanged — the vector digest the ledger
    recorded covers `horizon_basis`. Revert: check_manifest compares only the manifest id => this edit is accepted and the chain is built on a re-pinned manifest."""
    _killed(h)
    with h.w.conn.transaction():
        h.w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector, '{horizon_basis}',"
                         " '{\"basis\": \"edited\"}'::jsonb) WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN))
    _refused_with_nothing_written(h, "resume_manifest_changed", ("horizon_basis",))


def test_a_published_manifest_is_never_resumed(h):
    _killed(h)
    with h.w.conn.transaction():
        h.w.conn.execute("SET LOCAL session_replication_role = replica")
        h.w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'published' WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN))
    _refused_with_nothing_written(h, "resume_manifest_not_candidate")


def test_a_chain_without_a_horizon_basis_pin_is_non_resumable(h):
    """SR-J4E-HORIZON-BASIS: a chain whose manifest carries no pin (built before the pin was written for century runs; here the harness supplies no birth parameters, so
    none is derived) cannot be resumed by a run that COULD pin. Refused by name, nothing written. Revert: drop `require_horizon_basis` => the resume proceeds on an
    unpinned manifest and the completion gate would read FALSE at the end of it."""
    _killed(h)
    assert h.w.conn.execute("SELECT input_generation_vector->'horizon_basis' IS NULL FROM public.kala_gochara_publication WHERE generation = %s", (GEN,)).fetchone()[0]
    _refused_with_nothing_written(h, "resume_horizon_basis_unpinned", ("non-resumable",), birth=True)


def test_the_resume_reads_the_pin_back_from_the_manifest_and_checks_it_describes_the_built_horizon(h):
    """A pin that does not describe the horizon the substeps were built over is refused (`resume_horizon_basis_mismatch`); one that does is accepted. The ledger's vector
    digest is re-bound to the edited manifest so that ONLY the pin check can decide. Revert: skip the horizon comparison => the mismatching pin is accepted."""
    _killed(h)
    entries = bl.load(h.w.conn, CHART_ID, GEN)
    lo, hi = (x.astimezone(timezone.utc).isoformat() for x in SHORT)

    def pin(horizon):
        with h.w.conn.transaction():
            h.w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector, '{horizon_basis}', %s::jsonb)"
                             " WHERE chart_id = %s AND generation = %s", (json.dumps({"schema": "horizon_basis/1", "horizon": horizon}), CHART_ID, GEN))
        vec = bl.manifest_identity(h.w.conn, CHART_ID, GEN)[2]
        with h.w.conn.transaction():
            h.w.conn.execute(f"UPDATE public.{bl.TABLE} SET vector_sha256 = %s WHERE manifest_id IS NOT NULL", (vec,))
        return bl.load(h.w.conn, CHART_ID, GEN)
    with pytest.raises(bl.ResumeRefused) as exc:
        bl.check_manifest(h.w.conn, CHART_ID, GEN, pin([lo, "2099-01-01T00:00:00+00:00"]), require_horizon_basis=True)
    assert exc.value.code == "resume_horizon_basis_mismatch"
    bl.check_manifest(h.w.conn, CHART_ID, GEN, pin([lo, hi]), require_horizon_basis=True)


# ── H. the century run pins its horizon_basis (SR-J4E-HORIZON-BASIS) ─────────────────────────────────────────────────────────────

def _manifest_pin(h, century, monkeypatch=None, pinned_off=False):
    """Run the REAL manifest substep over the ruled century horizon with birth parameters (as the orchestrator supplies) and read back, with the gate's own expression,
    whether the manifest's input vector carries `horizon_basis`."""
    from services.gochara_kernel import horizon as gk_horizon
    ctx = h._ctx(gk_horizon.RULED_HORIZON, century, birth=True)
    writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
    h.conn.commit()
    return h.w.conn.execute("SELECT input_generation_vector->'horizon_basis' FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                            (CHART_ID, GEN)).fetchone()[0]


def test_a_century_run_pins_the_horizon_basis_and_the_unfixed_discriminator_reads_null(h, monkeypatch):
    """The null pattern the pack gates test (`input_generation_vector->'horizon_basis'` NULL) is produced when the century discriminator is reverted (the H2 behaviour)
    and is ABSENT with it; the pin is the ruled-scope + birth-centenary record.
    Revert: `_horizon_basis` returns None unless the run is the measuring slice => the second assertion fails (the revert proof plants exactly that in the writer)."""
    with monkeypatch.context() as m:
        m.setattr(writer_mod, "_horizon_basis", lambda ctx, slice_: None)   # the H2 behaviour: only the measuring slice is pinned, an unmarked run never
        assert _manifest_pin(h, True) is None, "the gate's null pattern was not produced by the unfixed discriminator"
    pin = _manifest_pin(h, True)
    assert pin is not None, "a century run published a candidate with horizon_basis NULL: the completion and teardown gates read FALSE on it"
    assert (pin["schema"], pin["rule"], pin["basis"], pin["birth_date"]) == ("horizon_basis/1", "ruled_scope+birth_centenary", "ruled_horizon", "1984-02-05")
    assert pin["horizon"] == ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"] and pin["chart_id"] == CHART_ID


def test_an_ordinary_run_is_not_pinned_so_its_vector_is_unchanged(h):
    """MB-CODEX-1 ruling 1: an ordinary build (no staged century config, no marker) carries NO basis component — its vector stays what main wrote.
    Revert: pin every run that has a horizon => this assertion fails (and test_mb_horizon_shape_guard / test_mb_ordinary_golden)."""
    assert _manifest_pin(h, False) is None
    vector = bl.manifest_identity(h.w.conn, CHART_ID, GEN)
    assert vector[3] is None
    assert "horizon_basis" not in json.loads(h.w.conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication").fetchone()[0])


# ── D. tamper ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _tamper(h, sql, params=()):
    with h.w.conn.transaction():
        h.w.conn.execute("SET LOCAL session_replication_role = replica")        # the guards are the world under test, not the subject
        h.w.conn.execute(sql, params)


def test_a_changed_row_of_a_recorded_substep_refuses_naming_that_substep(h):
    """Flip ONE column of one committed record. Revert: compare only the row counts (not the content digest) => accepted."""
    _killed(h, kill_after=f"record:{CLASSES[0]}:P3")
    target = f"record:{CLASSES[0]}:P2"
    _tamper(h, "UPDATE public.ka_gochara_relationship_record SET source_page = COALESCE(source_page, '') || '!' WHERE record_id = (SELECT record_id FROM public.ka_gochara_relationship_record"
               " WHERE generation = %s AND event_class = %s AND path_id = 'P2' ORDER BY record_id LIMIT 1)", (GEN, CLASSES[0]))
    err = _refused_with_nothing_written(h, "resume_chain_tampered", (target, "ka_gochara_relationship_record"))
    assert err.keys == (target,)


def test_a_deleted_row_of_a_recorded_substep_refuses_naming_that_substep(h):
    _killed(h, kill_after=f"record:{CLASSES[0]}:P3")
    _tamper(h, "DELETE FROM public.ka_gochara_record_prerequisite WHERE record_id = (SELECT record_id FROM public.ka_gochara_record_prerequisite"
               " WHERE generation = %s ORDER BY record_id LIMIT 1)", (GEN,))
    err = _refused_with_nothing_written(h, "resume_chain_tampered")
    assert err.keys and all(k.startswith("record:") for k in err.keys)


def test_a_ledger_gap_refuses(h):
    _killed(h, kill_after=f"record:{CLASSES[0]}:P3")
    _tamper(h, f"DELETE FROM public.{bl.TABLE} WHERE chart_id = %s::uuid AND generation = %s AND substep_key = %s", (CHART_ID, GEN, f"inventory:{CLASSES[0]}"))
    _refused_with_nothing_written(h, "resume_ledger_not_a_prefix", (f"inventory:{CLASSES[0]}",))


def test_chain_rows_of_an_unrecorded_substep_refuse_as_orphans_naming_it(h):
    """The last recorded substep's ledger row is lost but its rows are not: they belong to no recorded substep. Revert: skip the orphan scan => the resume re-runs the
    grain and (the replace not running) builds beside rows nobody vouches for."""
    _, ledger = _killed(h, kill_after=f"record:{CLASSES[0]}:P3")
    last = ledger[-1]
    _tamper(h, f"DELETE FROM public.{bl.TABLE} WHERE chart_id = %s::uuid AND generation = %s AND substep_key = %s", (CHART_ID, GEN, last))
    err = _refused_with_nothing_written(h, "resume_orphan_rows", (last,))
    assert last in err.keys


# ── E. atomicity ────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_an_aborted_substep_leaves_no_ledger_row_and_no_data(h):
    """Revert: write the ledger row on another connection (it survives the rollback) => a row for a substep whose data is gone."""
    killed = f"record:{CLASSES[0]}:P2"
    _killed(h, kill_after=killed)
    assert killed not in h.ledger()
    scope, _ = bl.measure_scope(h.w.conn, CHART_ID, GEN, killed)
    assert all(t["rows"] == 0 for t in scope["tables"].values()), "the aborted substep left data behind"


# ── F. teardown clears the ledger ───────────────────────────────────────────────────────────────────────────────────────────────

def test_the_century_teardown_scope_deletes_counts_and_locks_the_ledger(h):
    """Revert: drop LEDGER_TABLE from GENERATION_TABLES => the ledger is not in the scope and survives a teardown (the next fresh build would 'resume' a chain that is gone)."""
    import importlib.util
    import sys
    scripts = Path(__file__).resolve().parents[4] / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        spec = importlib.util.spec_from_file_location("teardown_v5_for_ledger_test", scripts / "teardown_v5_small_test_job.py")
        teardown = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(teardown)
    finally:
        sys.path.remove(str(scripts))
    assert ("ka_gochara_build_ledger", "") in teardown.GENERATION_TABLES and "ka_gochara_build_ledger" in teardown.REQUIRED_PRIVILEGES["select_delete"]
    _killed(h)
    assert h.ledger()
    statements = {table: (count_sql, where, params) for table, count_sql, where, params in teardown._scope_statements([])}
    _count_sql, where, params = statements["ka_gochara_build_ledger"]
    with h.w.conn.transaction():
        h.w.conn.execute(f"DELETE FROM ka_gochara_build_ledger WHERE {where}", params)
    assert h.ledger() == []
    assert h.plan(_Subset()) == _plan_order(), "after the teardown the next plan is a fresh build"


# ── G. the sealer refuses a generation several executions built ─────────────────────────────────────────────────────────────────

def test_the_producer_execution_list_names_every_build_run_and_the_sealer_problem_is_named(h):
    """Revert: `resumed_generation_problem` returns None for >1 producers => a resumed generation passes the sealer's check."""
    _killed(h)
    assert bl.resumed_generation_problem(h.w.conn, CHART_ID, GEN) is None, "one execution so far"
    h.dispatch(_Subset())
    why = bl.resumed_generation_problem(h.w.conn, CHART_ID, GEN)
    assert why and why.startswith("resumed_generation_not_sealable") and "2 executions" in why
    runs = [p["build_run_id"] for p in bl.producer_executions(h.w.conn, CHART_ID, GEN)]
    assert len(set(runs)) == 2


def test_the_seal_flow_refuses_a_resumed_generation_before_anything_is_published(monkeypatch):
    """The sealer wires the check in before `publish`. Revert: delete the call from `seal_flow._seal_with_approval` => publish runs and the sentinel raises."""
    from services.gochara_kernel import seal_brief, seal_flow, window_gate

    class Published(Exception):
        pass

    monkeypatch.setattr(seal_brief, "recompute_under_locks", lambda *a, **k: {"code": {"manifest_pinned_implementation_digest": "d"}, "manifest": {"manifest_id": "m"}})
    monkeypatch.setattr(window_gate, "implementation_digest", lambda *a, **k: "d")
    monkeypatch.setattr(seal_brief, "registry_problem", lambda *a, **k: None)
    monkeypatch.setattr(seal_brief, "persisted_brief_problem", lambda *a, **k: None)
    monkeypatch.setattr(seal_flow.build_ledger, "resumed_generation_problem", lambda *a, **k: "resumed_generation_not_sealable: test")
    monkeypatch.setattr(seal_flow.gk_ledger, "publish", lambda *a, **k: (_ for _ in ()).throw(Published()))
    with pytest.raises(seal_brief.ApprovalMismatch, match="resumed_generation_not_sealable"):
        seal_flow._seal_with_approval(object(), chart_id=CHART_ID, generation=GEN, approved_digest="a" * 64, approver_login="x", approval_note="n", run_id=1,
                                      sealing_commit="abcdef0", brief_id=1, producer_execution_id="e")
