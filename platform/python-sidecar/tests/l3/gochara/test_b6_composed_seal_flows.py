"""Composed builder → verifier → sealer flows on the REAL production-ordered stack with ALL guards enabled (Codex R9-6 iv, R9-4).

Unlike the 1240 role suite (1206's seal trigger DISABLED, the build made as a superuser) and the 39-assert rehearsal (object presence
and privileges only), these flows run each act AS ITS PRINCIPAL — the restricted builder builds, the verifier verifies, the sealer
seals — on a database where every object is owned by the migration principal and PUBLIC EXECUTE is revoked (composed_world.py).

Speed: ONE real-sky build as the restricted builder is made once per module (the TEMPLATE database); every test that needs a built
generation works on a byte-for-byte CLONE of it.

Scenarios:
  * the restricted builder builds the whole candidate, and a rebuild REPLACES (row counts unchanged);
  * each of migration 1242's four grants is individually necessary for that rebuild (revoke one -> the rebuild fails naming the table);
    the 1240 window-CHECK helper grant (R9-4) likewise;
  * first seal: builder -> verifier -> sealer with every guard on (the seal is refused before verification, accepted after);
  * a generation sealed BETWEEN 1206 and 1240 (i.e. before 1240 existed) stays sealed and frozen when 1240 is applied, the candidate gate
    reports it honestly as unverified, and no principal can write to it;
  * restricted-role contention on one chart: a builder rebuild racing a seal, in both orders.
WHAT THIS RIG IS AND IS NOT (Codex R12: replaces "no stand-in anywhere"): it is a MIRRORED schema (the real production-ordered migrations on PostgreSQL 15 with the objects owned by the
migration principal, plus hand-built stand-ins for tables outside the Gochara migrations: `charts` with its RLS structure, `chart_grants`, `chart_facts`, `chart_dashas`, `bg_transit_rules`,
the migration ledger and the legacy `kala_gochara_windows`); the verifier/sealer L1 reads are SUPPLIED EXTERNALLY by the harness (the data-plane ACL owner's item, not in 1241); the
verifier AND the sealer are REAL LOGINs (the approved seal runs Stream A's `execute_seal` as the `gochara_sealer` login, whose `sealed_by` the database attests; only the builder and the owner-level
helpers use `SET ROLE` on the harness connection, and the DB-gate attack helper `db_seal_attempt` seals as the owner so that a refusal is the database's); selected tests monkeypatch
`input_vector_verifier.verify_inputs` (a sealed successor added after a build also drifts the registry census, which would refuse first) and the builder's ephemeris callable (the real Swiss
ephemeris is restored for the real-sky builds). The Stream A writer and verifier code, the six migrations and 1241 are the real files.
History: the first two runs carried strict xfails for two Stream A defects this rehearsal found (R9-6.1: the inventory store deleted the verification table as the
builder; R9-10: the P1 anchor certification expected Moon contacts the stored non-Moon scope never writes) and one fixed stand-in (R9-9, the geometry probe margin).
All three are fixed in Stream A's code. Stream A's writer/verifier code runs as shipped; the harness's own stand-ins are listed above (not "none").
"""
from __future__ import annotations

import json
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import inventory_store
from services.gochara_kernel import ledger as gk_ledger
from services.gochara_kernel import record_store as rs
from services.gochara_kernel import window_gate as wg
from services.gochara_kernel import window_verifier as wv

from . import composed_world as cw
from . import test_a53_p1_support as p1s
from .conftest import EPHE_PATH as EPHE  # noqa: E402
from .test_a53_inventory import CHART_ID, PINNED_BUILD
from .test_a53_p1_support import GEN
from .test_a53_window_verification_gate import CLS, SPANS, _boot_p3, _windows  # noqa: F401
from .test_a53_window_verification_roles import _input_digest, _seal  # noqa: F401

UTC = timezone.utc
REAL_CALC = writer_mod.calc_sidereal_lon          # captured before any fixture replaces it: these flows run on the REAL ephemeris

#: {role: {"tables": [[privilege, table], ...], "funcs": [name, ...]}} — privileges DERIVED by running each act as its principal
#: (the derivation loop in the rehearsal record) on top of BASELINE; empty = nothing beyond BASELINE
EXTRA = json.loads(os.environ.get("B6_EXTRA", "{}"))

def apply_extra_grants(conn):
    """The verifier's and sealer's privileges: the REAL migration 1241 (applied once per database, as the owner, after the window — exactly its
    production order), plus the L1 reads (chart_facts, chart_dashas) that 1241 deliberately does NOT carry — an open item for the data-plane ACL
    owner, stood in here by the harness — plus any B6_EXTRA."""
    if not conn.execute("SELECT 1 FROM public._migrations_applied WHERE filename = %s", (cw.M1241,)).fetchone():
        cw.apply_migrations(conn, [cw.M1241])
    for role in (cw.VERIFIER, cw.SEALER):
        for t in ("chart_facts", "chart_dashas"):
            if OMIT != f"{role}|table|SELECT|{t}":
                conn.execute(f"GRANT SELECT ON public.{t} TO {role}")
    for role, s_ in EXTRA.items():
        _grant(conn, role, s_)


OMIT = os.environ.get("B6_OMIT", "")             # "role|table|PRIV|name" or "role|func||name": leave ONE grant out (the necessity sweep)


def _grant(conn, role, spec):
    for priv, table in spec.get("tables", []):
        if OMIT == f"{role}|table|{priv}|{table}":
            continue
        conn.execute(f"GRANT {priv} ON public.{table} TO {role}")
    for fn in spec.get("funcs", []):
        if OMIT == f"{role}|func||{fn}":
            continue
        for (sig,) in conn.execute("SELECT p.oid::regprocedure::text FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace"
                                   " WHERE n.nspname = 'public' AND p.proname = %s", (fn,)).fetchall():
            conn.execute(f"GRANT EXECUTE ON FUNCTION {sig} TO {role}")


# ── stand-ins and fixtures ──────────────────────────────────────────────────────────────────────────────────────

_LAST_SQL = [""]


@pytest.fixture(autouse=True)
def _capture_sql(monkeypatch):
    """Remember the last statement so a privilege denial can be attributed to its verb (SELECT/INSERT/UPDATE/DELETE)."""
    import psycopg
    orig = psycopg.Cursor.execute

    def wrapped(self, query, *a, **k):
        if isinstance(query, str):
            _LAST_SQL[0] = query
        return orig(self, query, *a, **k)
    monkeypatch.setattr(psycopg.Cursor, "execute", wrapped)


@contextmanager
def as_role(conn, role):
    import psycopg
    conn.execute(f"SET ROLE {role}")
    try:
        yield
    except psycopg.errors.InsufficientPrivilege as exc:
        verb = (_LAST_SQL[0].lstrip().split() or ["?"])[0].upper()
        raise RuntimeError(f"ROLE={role}: VERB={verb}: {exc}") from exc     # the derivation loop reads the principal and verb from here
    finally:
        conn.execute("RESET ROLE")


def build_as_builder(w):
    """The build, made by the RESTRICTED builder with the writer's OWN substeps for one class (marriage): convention, manifest, snapshot,
    the eight phase-1 body substrates, the class inventory + coverage, every record grain and every window grain. (No verifier/sealer
    grant is applied here: the TEMPLATE carries only what the real migrations give; each clone applies the derived sets.)"""
    with as_role(w.conn, cw.BUILDER):
        w.boot()
        for body in writer_mod.SUBSTRATE_BODIES:
            w.step(f"{writer_mod.BODY_SUBSTEP_PREFIX}{body}")
        for p in ("P1", "P2", "P3", "P4"):
            w.step(f"record:{CLS}:{p}")
        out = {p: w.step(f"window:{CLS}:{p}") for p in ("P1", "P2", "P3", "P4")}
    return out


def _real_world(mp, tmp_path, create):
    """The AM-5 world fixture on a database made by `create`, with the REAL Swiss ephemeris (the pinned files) in place of the fixture's
    stand-in: the builder's contact solves, the inventory verifier's sampling and the window verifier's probes read the SAME sky."""
    mp.setattr(p1s, "create_am5_database", lambda tag="p1s", faithful=True: create())
    gen = p1s._world(mp, tmp_path, faithful=True)
    w = next(gen)
    mp.setattr(writer_mod, "calc_sidereal_lon", REAL_CALC)
    return gen, w


def _db_exists(name):
    import psycopg
    cw.guard.assert_disposable_dsn(cw.ADMIN_DSN)
    with psycopg.connect(cw.ADMIN_DSN, autocommit=True, connect_timeout=3) as c:
        cw.guard.assert_connected_to(c)
        return c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone() is not None


def _template(tmp_path_factory, stack, keep):
    """ONE real-sky build as the restricted builder on `stack` (minutes). Yields the template database's name; the build's connection is closed
    so the database can be cloned. With `keep` (a database name, from the environment) an existing database of that name is reused and kept."""
    if keep and _db_exists(keep):
        yield keep
        return
    mp = pytest.MonkeyPatch()
    held = {}

    def create():
        admin, name, dsn = cw.composed_create("tmpl", stack)
        held.update(name=name)
        return admin, name, dsn
    gen, w = _real_world(mp, tmp_path_factory.mktemp("eph"), create)
    try:
        build_as_builder(w)
        w.conn.close()
        if keep:
            import psycopg
            cw.guard.assert_disposable_dsn(cw.ADMIN_DSN)
            with psycopg.connect(cw.ADMIN_DSN, autocommit=True, connect_timeout=3) as c:
                cw.guard.assert_connected_to(c)
                c.execute(f'ALTER DATABASE "{held["name"]}" RENAME TO "{keep}"')
            held["name"] = keep
        yield held["name"]
    finally:
        mp.undo()
        if not keep:
            gen.close()                               # the world's own teardown drops the template database (a kept one was renamed away)


@pytest.fixture(scope="module")
def built_template(tmp_path_factory):
    """The full production-ordered stack, built once (B6_KEEP_TEMPLATE=<name> keeps it across runs)."""
    yield from _template(tmp_path_factory, None, os.environ.get("B6_KEEP_TEMPLATE"))


@pytest.fixture(scope="module")
def built_template_between(tmp_path_factory):
    """The stack as it stood BETWEEN 1206 and 1240 (no 1240, no 1241), built once (B6_KEEP_TEMPLATE_BETWEEN=<name> keeps it)."""
    yield from _template(tmp_path_factory, cw.STACK_BETWEEN_1206_AND_1240, os.environ.get("B6_KEEP_TEMPLATE_BETWEEN"))


@pytest.fixture()
def cbuilt(built_template, monkeypatch, tmp_path):
    """A CLONE of the built template: a built, unverified, unsealed generation owned by the migration principal."""
    gen, w = _real_world(monkeypatch, tmp_path, lambda: cw.composed_clone(built_template))
    apply_extra_grants(w.conn)                        # the verifier's/sealer's derived sets (the template may predate an EXTRA change)
    try:
        yield w
    finally:
        gen.close()


def _counts(conn):
    return {t: conn.execute(f"SELECT count(*) FROM public.{t}").fetchone()[0]
            for t in ("ka_gochara_contact", "ka_gochara_relationship_record", "ka_gochara_record_prerequisite",
                      "ka_gochara_eval_window", "ka_gochara_eval_window_record", "ka_gochara_search_inventory")}


# ── 1. the restricted builder builds, and a rebuild REPLACES ────────────────────────────────────────────────────

def test_the_restricted_builder_built_the_whole_candidate_with_nothing_on_the_verification_tables(cbuilt):
    """R9-4: the builder's REAL window INSERT after 1240 (the CHECK helper EXECUTE comes from 1240 itself). The build already happened in
    the template; the clone proves its product and the builder's privilege matrix."""
    w = cbuilt
    c = _counts(w.conn)
    assert c["ka_gochara_relationship_record"] > 0 and c["ka_gochara_search_inventory"] > 0, c
    for table in ("ka_gochara_search_inventory_verification", "ka_gochara_eval_window_verification"):
        for priv in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            assert w.conn.execute("SELECT has_table_privilege(%s, %s, %s)", (cw.BUILDER, f"public.{table}", priv)).fetchone()[0] is False, \
                (table, priv)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0


def test_a_rebuild_by_the_restricted_builder_replaces_never_accretes(cbuilt):
    """The writer's replace-prelude (delete-then-insert per grain/class) with the builder's REAL grants: the orphan-contact delete, the
    record-chain delete, the finalisation updates and the window replace — none of which the first build exercises."""
    w = cbuilt
    before = _counts(w.conn)
    with as_role(w.conn, cw.BUILDER):
        for key in ("inventory:marriage", "coverage:marriage", *[f"record:{CLS}:{p}" for p in ("P1", "P2", "P3", "P4")],
                    *[f"window:{CLS}:{p}" for p in ("P1", "P2", "P3", "P4")]):
            w.step(key)
    assert _counts(w.conn) == before


_M1242 = [("DELETE ON public.ka_gochara_relationship_record", "ka_gochara_relationship_record"),
          ("DELETE ON public.ka_gochara_contact", "ka_gochara_contact"),
          ("UPDATE (admission_state) ON public.ka_gochara_relationship_record", "ka_gochara_relationship_record"),
          ("UPDATE (result) ON public.ka_gochara_record_prerequisite", "ka_gochara_record_prerequisite")]


@pytest.mark.parametrize("grant,table", _M1242, ids=["del_record", "del_contact", "upd_admission_state", "upd_prereq_result"])
def test_each_1242_grant_is_individually_necessary_for_the_rebuild_of_a_record_grain(cbuilt, grant, table):
    """1242's four grants, on the REAL migration stack (1242 applied as the real file): revoking any ONE of them makes the builder's
    rebuild of a record grain fail, naming the table."""
    w = cbuilt
    w.conn.execute(f"REVOKE {grant} FROM {cw.BUILDER}")
    try:
        with pytest.raises(RuntimeError, match=f"ROLE={cw.BUILDER}.*permission denied.*{table}"):
            with as_role(w.conn, cw.BUILDER):
                w.step(f"record:{CLS}:P3")
    finally:
        w.conn.execute(f"GRANT {grant} TO {cw.BUILDER}")


def test_the_1240_window_check_helper_grant_is_necessary_for_the_builders_window_insert(cbuilt):
    """R9-4 detector: remove the helper EXECUTE grant (1240 issues it) and the builder's window INSERT fails on exactly that function."""
    w = cbuilt
    w.conn.execute(f"REVOKE EXECUTE ON FUNCTION public.ka_gochara_window_qualification_ok(jsonb) FROM {cw.BUILDER}")
    with pytest.raises(RuntimeError, match=f"ROLE={cw.BUILDER}.*permission denied for function ka_gochara_window_qualification_ok"):
        with as_role(w.conn, cw.BUILDER):
            w.step(f"window:{CLS}:P3")


@pytest.fixture()
def cfresh(monkeypatch, tmp_path):
    """A FRESH production-ordered world (no build yet), Stream A's code as shipped (the harness stand-ins are listed in the module docstring)."""
    gen, w = _real_world(monkeypatch, tmp_path, lambda: cw.composed_create("fresh"))
    apply_extra_grants(w.conn)
    try:
        yield w
    finally:
        gen.close()


def test_the_inventory_store_lets_the_restricted_builder_start_a_build(cfresh):
    """R9-6.1 FIXED (Stream A cc4b481f4): the store no longer deletes the verification table as the builder, so a restricted builder (PC-4 in 1206)
    starts a build on a FRESH world. This was the first strict xfail — now an ordinary test, with Stream A's code as shipped."""
    with as_role(cfresh.conn, cw.BUILDER):
        cfresh.boot()


def test_the_record_phase_accepts_a_real_sky_build_with_moon_anchors(cbuilt):
    """R9-10 FIXED (Stream A dc63af112): every body-enumerating derivation takes the stored scope from the manifest and the Moon is never an
    expected stored agent, so the builder's own P1 anchor certification accepts a correct REAL-sky ledger. This was the second strict xfail."""
    with as_role(cbuilt.conn, cw.BUILDER):
        cbuilt.step(f"record:{CLS}:P1")


def test_the_geometry_self_check_accepts_a_real_sky_window_build_with_no_stand_in(cbuilt):
    """R9-9 (geometry self-check) FIXED (Stream A: the probe margin is derived from the solver tolerance): every window grain is rebuilt on the REAL sky as the
    restricted builder, with Stream A's shipped geometry self-check and NO stand-in. This was the second strict xfail."""
    with as_role(cbuilt.conn, cw.BUILDER):
        for p in ("P1", "P2", "P3", "P4"):
            cbuilt.step(f"window:{CLS}:{p}")


# ── 2. first seal: builder → verifier → sealer, every guard on ──────────────────────────────────────────────────

def _real_position_at(body, t):
    jd = t.timestamp() / 86400.0 + 2440587.5
    return REAL_CALC(body.title(), jd, EPHE)[0]


def _verifier_dsn(w):
    """A LOGIN as the verifier principal (the harness roles are NOLOGIN; trust auth on the disposable cluster)."""
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    d = conninfo_to_dict(w.conn.info.dsn)
    d["user"] = cw.VERIFIER
    return make_conninfo("", **{k: v for k, v in d.items() if k in ("host", "port", "dbname", "user")})


def _run_job(w, args, dsn=None):
    """Stream A's REAL job entry point as a real verifier LOGIN. Returns (exit code, stdout)."""
    import io
    from contextlib import redirect_stdout
    from pipeline.orchestrator import verification_job as job
    w.conn.execute(f"ALTER ROLE {cw.VERIFIER} LOGIN")
    os.environ[job.ENV_URL] = dsn or _verifier_dsn(w)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = job.main(args)
    finally:
        os.environ.pop(job.ENV_URL, None)
        w.conn.execute(f"ALTER ROLE {cw.VERIFIER} NOLOGIN")
    return rc, buf.getvalue().strip()


def verify_as_verifier(w, *extra_args, dsn=None, all_classes=False):
    """Stream A's REAL verification job (`pipeline/orchestrator/verification_job.py`), run as a real verifier LOGIN with the REAL 1241 grants (the harness's L1 reads are supplied externally): the job proves its own identity, records the four window verifications FIRST and then the inventory verification. Returns the
    parsed report; raises RuntimeError on any non-zero exit (a refusal or a disagreement)."""
    import json as _json
    rc, out = _run_job(w, ["--chart", CHART_ID, "--generation", GEN, *([] if all_classes else ["--class", CLS]), "--ephe-path", EPHE, *extra_args], dsn)
    if rc != 0:
        raise RuntimeError(f"verification job exit {rc}: {out[:700]} ... {out[-900:]}" if len(out) > 1700 else f"verification job exit {rc}: {out}")
    return _json.loads(out.splitlines()[-1]) if out else {}


SEALING_COMMIT = "5ea1" + "0" * 36


IMAGE_DIGEST = "sha256:" + "1" * 64
EXECUTION_NAME = "composed-exec-1"


@contextmanager
def _producer_env(sealing_commit, execution=EXECUTION_NAME):
    """What the Cloud Run job definition and Cloud Run itself put in the verification job's environment (ST-WIRE-2): the producing commit, the immutable image digest and the execution
    name. The verifier REFUSES to brief without them (`producer_identity_absent`). In the rig they are set for the duration of one in-process job run."""
    keys = {"GOCHARA_RUNNER_COMMIT": sealing_commit, "GOCHARA_RUNNER_IMAGE_DIGEST": IMAGE_DIGEST, "CLOUD_RUN_EXECUTION": execution}
    old = {k: os.environ.get(k) for k in keys}
    os.environ.update(keys)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _brief_ref(conn, digest):
    """(brief_id, execution_id) of the latest brief the verifier persisted with this digest; for a digest nothing persisted (a fabricated one) a placeholder pair — the database refuses it by name."""
    row = conn.execute("SELECT brief_id, execution_id FROM public.ka_gochara_seal_brief WHERE brief_digest = %s ORDER BY brief_id DESC LIMIT 1", (digest,)).fetchone()
    return tuple(row.values()) if isinstance(row, dict) else (tuple(row) if row else (1, "fabricated"))


def brief_stdout_as_verifier(w, sealing_commit=SEALING_COMMIT, *extra):
    """The verifier job's `--brief` STDOUT (always chunked since Stream A a289b38eb), byte for byte (what Cloud Run would log: the chunk lines, then the compact `BRIEFED` line): raises RuntimeError if it refuses."""
    with _producer_env(sealing_commit):
        rc, out = _run_job(w, ["--chart", CHART_ID, "--generation", GEN, "--brief", "--sealing-commit", sealing_commit, *extra])
    if rc != 0:
        raise RuntimeError(f"brief exit {rc}: {out[:1500]}")
    return out


def brief_as_verifier(w, sealing_commit=SEALING_COMMIT):
    """The verifier-run SEAL BRIEF (`--brief`) as a real verifier login: the compact line (`sha256`, `persisted`, …) plus the full payload read back from `--brief-out` (whose bytes hash to
    the digest — asserted): `{"brief": <payload>, "sha256": <digest>, "persisted": {…}}`; raises RuntimeError if it refuses."""
    import hashlib as _hl
    import json as _json
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "brief.json")
        with _producer_env(sealing_commit):
            rc, out = _run_job(w, ["--chart", CHART_ID, "--generation", GEN, "--brief", "--brief-out", path, "--sealing-commit", sealing_commit])
        if rc != 0:
            raise RuntimeError(f"brief exit {rc}: {out[:1500]}")
        compact = _json.loads(out.splitlines()[-1])
        with open(path, "rb") as f:
            raw = f.read()
    assert compact["status"] == "BRIEFED" and _hl.sha256(raw).hexdigest() == compact["sha256"] and len(raw) == compact["brief_bytes"]
    return {"brief": _json.loads(raw.decode("utf-8")), "sha256": compact["sha256"], "persisted": compact["persisted"]}


def _sealer_dsn(w):
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    d = conninfo_to_dict(w.conn.info.dsn)
    d["user"] = cw.SEALER
    return make_conninfo("", **{k: v for k, v in d.items() if k in ("host", "port", "dbname", "user")})


NOTE = "ruling:NATIVE_DIRECT_RULINGS_20261002#2; actor:steward-as-owner"


def approved_seal_as_sealer(w, digest, sealing_commit=SEALING_COMMIT, approver="steward-as-owner", note=NOTE, actor="steward-as-owner", run_id=26104817, run_attempt=1):
    """The SEALING step as a REAL sealer LOGIN (no more `SET ROLE` on a superuser connection): Stream A's `execute_seal` — the executable caller's own function — on an autocommit
    connection that proves its identity (session_user = current_user = gochara_sealer, no write privilege beyond the seal set), then ONE transaction: locks, policy requirement,
    recompute, brief-persistence check, publish, authoritative seal, receipt (the database attests `sealed_by` / `approved_at`)."""
    import psycopg as pg
    from services.gochara_kernel import seal_flow
    bid, eid = _brief_ref(w.conn, digest)
    approval = {"schema": "seal_approval/2", "brief_digest": digest, "brief_id": bid, "producer_execution_id": eid, "run_id": run_id, "run_attempt": run_attempt, "approver_login": approver,
                "approved_by_note": note}
    w.conn.execute(f"ALTER ROLE {cw.SEALER} LOGIN")
    conn = pg.connect(_sealer_dsn(w), autocommit=True, connect_timeout=3)
    try:
        return seal_flow.execute_seal(conn, chart_id=CHART_ID, generation=GEN, approval=approval, run_id=run_id, run_attempt=run_attempt, sealing_commit=sealing_commit,
                                      triggering_actor=actor)
    finally:
        conn.close()
        w.conn.execute(f"ALTER ROLE {cw.SEALER} NOLOGIN")


def approved_flow(w):
    """verify -> brief -> approved seal, every act as its own principal. Returns (brief, seal result)."""
    verify_as_verifier(w)
    b = brief_as_verifier(w)
    return b, approved_seal_as_sealer(w, b["sha256"])


def seal_as_sealer(w):
    """The complete governed seal: the verifier's brief (persisted), then the approved seal by the real sealer login. Returns the manifest id (a UUID)."""
    import uuid
    b = brief_as_verifier(w)
    return uuid.UUID(approved_seal_as_sealer(w, b["sha256"])["manifest_id"])


def db_seal_attempt(w):
    """A seal attempt at the DATABASE's own gate by a FULL-privilege principal (the migration owner): the brief and the sealing job are bypassed, so a refusal here is the
    database's (the 1206 / 1240 seal triggers), not the brief's. Stream A's `_seal` helper persists a test brief and writes the receipt in the same transaction."""
    from unittest import mock

    from .test_a53_window_verification_roles import _persist_test_brief
    _persist_test_brief(w)                                    # as the VERIFIER login (its `ALTER ROLE … LOGIN` needs the harness superuser, not the owner role)
    with as_role(w.conn, cw.OWNER), mock.patch("tests.l3.gochara.test_a53_window_verification_roles._persist_test_brief", lambda *a, **k: None):
        return _seal(w)


def _refusals():
    """Everything that can REFUSE a seal: the database (psycopg), the brief/verifier job (RuntimeError), the sealing job (SealRefused / ApprovalMismatch)."""
    import psycopg as pg
    from services.gochara_kernel import seal_brief, seal_flow
    return (pg.errors.Error, RuntimeError, seal_brief.ApprovalMismatch, seal_flow.SealRefused)


def _replay_as_sealer(w, manifest):
    """The REPLAY of an existing seal (ka_gochara_seal_generation inserts ON CONFLICT DO NOTHING; the BEFORE triggers — 1206's and 1240's — fire
    first and re-check what they can): idempotent, returns the same manifest, adds no row."""
    with as_role(w.conn, cw.SEALER):
        again = w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
    assert again == manifest
    return again


def _spec_of_1241():
    """The jsonb SPEC embedded in the REAL 1241 file (the one source its GRANTs and its closure check both read)."""
    import json as _json
    import re
    from .test_a53_record_store import MIGRATIONS
    if not (MIGRATIONS / cw.M1241).exists():
        return None
    return _json.loads(re.search(r"\$spec\$(.*?)\$spec\$", (MIGRATIONS / cw.M1241).read_text(), re.S).group(1))


def _grants_of_1241():
    """(role, kind, privilege, object, columns) for every privilege of ORIGIN '1241' in the spec (1240's backfilled ones are 1240's reviewed set)."""
    spec = _spec_of_1241()
    if spec is None:
        return []                                      # the integration exhibit without 1241 in the tree: the parametrized tests are skipped
    out = []
    for role, body in spec["roles"].items():
        for tbl, priv, cols, origin in body["tables"]:
            if origin == "1241":
                out.append((role, "table", priv, tbl, tuple(cols) if cols else None))
        for sig, origin in body["functions"]:
            if origin == "1241":
                out.append((role, "func", "EXECUTE", sig, None))
    return out


_G1241 = _grants_of_1241()


def test_1241_spec_has_the_expected_number_of_1241_origin_grants():
    if not _G1241:
        pytest.skip("NOT_RUN: migration 1241 is not in this tree")
    assert len(_G1241) == len(set(_G1241)) == 67, len(_G1241)   # v7 (R15-6): +5 sealer SELECTs on the registry relations the seal-time re-derivation reads (v6 was 62). sealer: 20 table + 22 function (incl. the legacy-projection check and the persisted-brief functions); verifier: 13 table (incl. the legacy relations and the brief table) + 12 function (R10-4 iii: the job's final combined gate)


@pytest.mark.parametrize("role,kind,priv,obj,cols", _G1241, ids=[f"{r.split('_')[1]}-{p.lower()}-{o}" for r, k, p, o, c in _G1241])
def test_each_grant_of_migration_1241_is_individually_necessary(cbuilt, role, kind, priv, obj, cols):
    """The REAL 1241 file is applied; ONE of its privileges is revoked; the verification-then-seal flow must then FAIL on a permission denial —
    so every grant in the file is demonstrably needed by a flow (nothing speculative)."""
    w = cbuilt
    if kind == "table":
        colsql = f" ({', '.join(cols)})" if cols else ""
        w.conn.execute(f"REVOKE {priv}{colsql} ON public.{obj} FROM {role}")
    else:
        w.conn.execute(f"REVOKE EXECUTE ON FUNCTION public.{obj} FROM {role}")
    import psycopg as pg
    with pytest.raises((RuntimeError, pg.errors.InsufficientPrivilege), match=r"permission denied|no_verifier_privilege|brief exit|identity_not_sealer"):
        _, res = approved_flow(w)    # verify, then the verifier's BRIEF, then the sealer's recompute + publish + seal + receipt: every principal's reads and writes
        _replay_as_sealer(w, __import__("uuid").UUID(res["manifest_id"]))     # ...and the seal REPLAY (the replay-side helper functions)


def test_charts_row_level_security_is_evaluated_through_chart_grants_but_neither_principal_reads_charts(cbuilt):
    """Suvarṇa's RLS question (steward M20261002T094148-15d4), mirrored: `charts` has RLS on with a grant policy that reads `chart_grants`, so a role with
    SELECT on `charts` alone is refused ON `chart_grants`; the verification-then-seal flow never reads `charts`, so neither principal needs either table.
    (chart_facts / chart_dashas / bg_transit_rules have RLS OFF in production — a table-level SELECT suffices, proven by the necessity tests.)"""
    w = cbuilt
    w.conn.execute(f"GRANT SELECT ON public.charts TO {cw.VERIFIER}")
    with pytest.raises(RuntimeError, match="permission denied for table chart_grants"):
        with as_role(w.conn, cw.VERIFIER):
            w.conn.execute("SELECT count(*) FROM public.charts").fetchone()
    w.conn.execute(f"REVOKE SELECT ON public.charts FROM {cw.VERIFIER}")
    verify_as_verifier(w)                                      # the real job + the real 1241 + the two L1 reads: no `charts`, no `chart_grants`
    assert seal_as_sealer(w) is not None


@pytest.mark.parametrize("role", [cw.VERIFIER, cw.SEALER])
@pytest.mark.parametrize("table", ["chart_facts", "chart_dashas"])
def test_the_l1_reads_that_1241_does_not_carry_are_individually_necessary(cbuilt, role, table):
    """The OPEN item for the data-plane ACL owner: without SELECT on these L1 tables the verification-then-seal flow fails."""
    w = cbuilt
    w.conn.execute(f"REVOKE SELECT ON public.{table} FROM {role}")
    import psycopg as pg
    with pytest.raises((RuntimeError, pg.errors.InsufficientPrivilege), match=r"permission denied|verification job exit|refused"):
        verify_as_verifier(w)
        seal_as_sealer(w)


def _strip_principals(conn):
    """The state a window applied while the roles did NOT exist leaves behind: 1240's role-conditional grants were SKIPPED, so verifier and sealer hold NOTHING on
    any ka_gochara_/kala_gochara_ relation or function (REVOKE ALL also removes column-level privileges)."""
    for role in (cw.VERIFIER, cw.SEALER):
        conn.execute(f"""DO $$ DECLARE x record; BEGIN
          FOR x IN SELECT c.oid::regclass AS rel FROM pg_class c WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r','p')
                   AND (c.relname LIKE 'ka\\_gochara\\_%' OR c.relname LIKE 'kala\\_gochara\\_%') LOOP
            EXECUTE format('REVOKE ALL ON TABLE %s FROM {role}', x.rel); END LOOP;
          FOR x IN SELECT p.oid::regprocedure AS fn FROM pg_proc p WHERE p.pronamespace = 'public'::regnamespace AND p.proname LIKE 'ka\\_gochara\\_%' LOOP
            EXECUTE format('REVOKE ALL ON FUNCTION %s FROM {role}', x.fn); END LOOP; END $$""")


def _reapply_1241(conn):
    conn.execute("DELETE FROM public._migrations_applied WHERE filename = %s", (cw.M1241,))
    cw.apply_migrations(conn, [cw.M1241])


def test_a_role_created_after_the_window_gets_1240s_skipped_grants_from_1241_and_verifies_and_seals(cbuilt):
    """R10-7 (i): 1240's role-conditional grants are skipped permanently when the owner creates the roles AFTER the window. State reproduced: the window
    applied (the clone), then verifier and sealer hold NOTHING (what the skipped grants leave); 1241 is applied ONCE — it carries 1240's grants as well as its
    own — and the real job verifies and the sealer seals (and replays)."""
    w = cbuilt
    _strip_principals(w.conn)
    for role in (cw.VERIFIER, cw.SEALER):                       # nothing on any gochara object: the verifier cannot even read the window-verification table
        assert w.conn.execute("SELECT has_table_privilege(%s, 'public.ka_gochara_eval_window_verification', 'SELECT')", (role,)).fetchone()[0] is False
    _reapply_1241(w.conn)                                       # the single backfill
    apply_extra_grants(w.conn)                                  # (the L1 reads, stood in for the data-plane owner)
    report = verify_as_verifier(w)
    manifest = seal_as_sealer(w)
    assert manifest is not None and _replay_as_sealer(w, manifest) == manifest


def test_1241_closure_refuses_a_privilege_the_spec_does_not_name_at_table_function_and_column_level(cbuilt):
    """R10-7 (iv): the post-check compares the ENTIRE ACL, so a PROHIBITED privilege held by either principal fails the migration — a table write, a function, and a
    bare column-level read — and applying it again after the extra is removed passes."""
    import psycopg
    w = cbuilt
    for grant, fragment in ((f"GRANT UPDATE ON public.ka_gochara_eval_window TO {cw.VERIFIER}", "UPDATE on ka_gochara_eval_window: PROHIBITED"),
                            (f"GRANT DELETE ON public.ka_gochara_relationship_record TO {cw.SEALER}", "DELETE on ka_gochara_relationship_record: PROHIBITED"),
                            (f"GRANT EXECUTE ON FUNCTION public.ka_gochara_search_av_entry(text) TO {cw.SEALER}", r"EXECUTE on ka_gochara_search_av_entry\(text\): PROHIBITED"),
                            (f"GRANT SELECT (raw_intensity) ON public.kala_gochara_windows TO {cw.SEALER}", r"SELECT \(raw_intensity\) on kala_gochara_windows: PROHIBITED")):
        w.conn.execute(grant)
        with pytest.raises(psycopg.errors.Error, match=fragment):
            _reapply_1241(w.conn)
        w.conn.execute(grant.replace("GRANT", "REVOKE", 1).replace(" TO ", " FROM "))
    _reapply_1241(w.conn)                                       # clean again: the closure passes


def test_1241_closure_refuses_a_missing_required_privilege_only_if_it_cannot_be_granted_and_heals_otherwise(cbuilt):
    """Re-applying 1241 after a required privilege was revoked GRANTS it back (idempotent backfill) and the closure then passes."""
    w = cbuilt
    w.conn.execute(f"REVOKE SELECT ON public.ka_gochara_search_obligation FROM {cw.VERIFIER}")
    _reapply_1241(w.conn)
    assert w.conn.execute("SELECT has_table_privilege(%s, 'public.ka_gochara_search_obligation', 'SELECT')", (cw.VERIFIER,)).fetchone()[0] is True


def test_the_sealers_publication_update_and_legacy_windows_read_are_column_narrow(cbuilt):
    """R10-7 (ii)+(iii): the sealer can set ONLY the four publication columns ledger.publish writes, and read the legacy windows relation ONLY on
    (chart_id, generation) — nothing else of it."""
    import psycopg
    w = cbuilt
    for col in ("status", "published_at", "content_digest", "row_counts"):
        assert w.conn.execute("SELECT has_column_privilege(%s, 'public.kala_gochara_publication', %s, 'UPDATE')", (cw.SEALER, col)).fetchone()[0] is True, col
    for col in ("superseded_at", "manifest_id", "input_generation_vector"):
        assert w.conn.execute("SELECT has_column_privilege(%s, 'public.kala_gochara_publication', %s, 'UPDATE')", (cw.SEALER, col)).fetchone()[0] is False, col
    assert w.conn.execute("SELECT has_table_privilege(%s, 'public.kala_gochara_publication', 'UPDATE')", (cw.SEALER,)).fetchone()[0] is False
    with as_role(w.conn, cw.SEALER):
        n = w.conn.execute("SELECT count(*) FROM public.kala_gochara_windows WHERE chart_id = %s AND generation = '3.0'", (CHART_ID,)).fetchone()[0]
        assert n == 2                                            # the column-narrow read works (the legacy served generation); a governed '5.0' has NO legacy rows (R12-1)
        assert w.conn.execute("SELECT count(*) FROM public.kala_gochara_windows WHERE chart_id = %s AND generation = '5.0'", (CHART_ID,)).fetchone()[0] == 0
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            w.conn.execute("SELECT raw_intensity FROM public.kala_gochara_windows LIMIT 1")


def test_first_seal_builder_then_verifier_then_sealer_with_every_guard_enabled(cbuilt):
    import psycopg
    w = cbuilt
    # before any verification the candidate gate is CLOSED and the seal is refused (the honest "built, not verified" state)
    with pytest.raises(_refusals()):
        seal_as_sealer(w)                                            # (the brief refuses an unverified candidate)
    with pytest.raises(psycopg.errors.Error):
        db_seal_attempt(w)                                           # (and the DATABASE's own gate refuses it too)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    report = verify_as_verifier(w)                               # Stream A's REAL job, as a real verifier login
    # R10-4: the job ENDS in the combined candidate gate and records the runner's identity; both are in the report
    assert report["status"] == "VERIFIED" and report["gate"] == [] and report["gate_source"] == "ka_gochara_candidate_gate_violations", report
    assert report["preconditions"]["runner"]["commit"] and len(report["preconditions"]["runner"]["implementation_digest"]) == 64, report
    manifest = seal_as_sealer(w)
    assert manifest is not None
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 1
    assert _replay_as_sealer(w, manifest) == manifest                    # a replay of the seal is idempotent under every guard
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 1


def test_a_second_verification_run_replaces_the_first_before_the_seal(cbuilt):
    """The verification runner can be re-run before a seal (the failed-halfway case): the second run REPLACES the first (one row per grain / class,
    never two) — WITHOUT any DELETE on the inventory-verification table (1241 grants none; the window verifications are replaced by the verifier's own
    DELETE on 1240's table, pre-seal)."""
    w = cbuilt
    verify_as_verifier(w)
    first = (w.conn.execute("SELECT count(*) FROM public.ka_gochara_search_inventory_verification").fetchone()[0],
             w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0])
    verify_as_verifier(w)
    second = (w.conn.execute("SELECT count(*) FROM public.ka_gochara_search_inventory_verification").fetchone()[0],
              w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0])
    assert first == second and first[0] >= 1 and first[1] == 4, (first, second)
    assert seal_as_sealer(w) is not None                        # and the replaced verification is what the seal accepts


# ── 3. a generation sealed BETWEEN 1206 and 1240 ────────────────────────────────────────────────────────────────

@pytest.fixture()
def between_world(built_template_between, monkeypatch, tmp_path):
    """A clone of a REAL, COMPLETE build made on the stack as it stood between 1206 and 1240 (the real sky: 1206's completeness guard demands a
    fully searched generation)."""
    gen, w = _real_world(monkeypatch, tmp_path, lambda: cw.composed_clone(built_template_between))
    try:
        yield w
    finally:
        gen.close()


def test_a_generation_sealed_before_1240_existed_stays_sealed_frozen_and_honestly_unverified_when_1240_arrives(between_world):
    """Before 1240 (and therefore before 1241, which needs 1240's objects) the verifier and sealer principals hold nothing from Gochara
    migrations, so the generation is verified (1206's inventory verification) and sealed by the OWNER (the migration principal) — the only
    principal that can. Then 1240 and 1241 arrive in their real order."""
    import psycopg
    w = between_world
    assert w.conn.execute("SELECT to_regclass('public.ka_gochara_eval_window_verification')").fetchone()[0] is None   # 1240 not yet applied
    assert _p3_records(w.conn) > 0
    from services.gochara_kernel import inventory_verifier as inv_v
    with as_role(w.conn, cw.OWNER):
        # 1206's inventory verification only (no window gate exists yet). The builder is report-only since R9-6.1 and Stream A's job needs
        # 1240/1241 objects, so before them only the owner can write the row — with the digest the database itself recomputes.
        digest = w.conn.execute("SELECT public.ka_gochara_search_inventory_digest(%s::uuid, %s, %s)", (CHART_ID, GEN, CLS)).fetchone()[0]
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            w.conn.execute("SELECT public.ka_gochara_lock_global_shared()")
            inv_v.write_verification(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, rederived_digest=digest)
        manifest = _seal(w, receipt=False)              # sealed under 1206's trigger alone (the receipt table does not exist yet: 1240 has not arrived)
    assert manifest is not None
    seal_row = w.conn.execute("SELECT * FROM public.ka_gochara_generation_seal").fetchall()
    c_before = _counts(w.conn)

    cw.apply_migrations(w.conn, [cw.M1240, cw.M1241])   # 1240 then 1241 arrive AFTER the seal, as the owner, the real files
    apply_extra_grants(w.conn)
    assert w.conn.execute("SELECT public.ka_gochara_generation_is_sealed(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0] is True
    assert w.conn.execute("SELECT * FROM public.ka_gochara_generation_seal").fetchall() == seal_row    # the seal row is untouched
    assert _counts(w.conn) == c_before                                                                  # the frozen set is untouched
    # the candidate gate reports the pre-1240 generation HONESTLY: no window verification exists — a reason, not an error
    reasons = w.conn.execute("SELECT * FROM public.ka_gochara_window_verification_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall()
    assert reasons, "a generation sealed before 1240 has no window verification: the gate must say so"
    # nobody can change it any more: not a (now-provisioned) verifier's window verification, not the builder's rebuild
    # ... and it can never GAIN a verification: its windows predate 1240's objective/qualification provenance columns, so the independent window
    # verifier cannot derive a result for them — the honest, permanent "unverified" state (a sealed generation is never rebuilt in place)
    with pytest.raises(RuntimeError, match="verification job exit [2345]"):             # the real job REFUSES (nothing written)
        verify_as_verifier(w)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 0
    with pytest.raises(Exception, match="SEALED|sealed"):
        with as_role(w.conn, cw.BUILDER):
            w.step(f"record:{CLS}:P3")
    # a replay of the seal is IDEMPOTENT (1240: "a generation sealed before 1240 replays cleanly") — it returns the same manifest, adds no row, and (the receipt trigger is
    # AFTER INSERT: it fires only for a row actually inserted) needs NO receipt
    assert _replay_as_sealer(w, manifest) == manifest
    assert w.conn.execute("SELECT * FROM public.ka_gochara_generation_seal").fetchall() == seal_row


# ── 4. restricted-role contention on one chart ──────────────────────────────────────────────────────────────────

def _open(w, role):
    import psycopg
    c = psycopg.connect(w.conn.info.dsn, autocommit=True, connect_timeout=3)
    c.execute(f"SET ROLE {role}")
    return c


def _waiting(admin, pid, seconds=10.0):
    end = time.time() + seconds
    while time.time() < end:
        row = admin.execute("SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s", (pid,)).fetchone()
        if row and row[0] == "Lock":
            return True
        time.sleep(0.1)
    return False


def _write_test_receipt(conn, manifest):
    """The seal is only committable with an approval receipt (1240's deferred constraint trigger, R11-3 enforced): the race tests below exercise LOCKING, so their raw
    seals write one in the same transaction (as the sealer)."""
    digest = conn.execute("SELECT brief_digest FROM public.ka_gochara_seal_brief WHERE chart_id = %s AND generation = %s ORDER BY brief_id DESC LIMIT 1", (CHART_ID, GEN)).fetchone()[0]
    bid, eid = _brief_ref(conn, digest)
    conn.execute("INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id, approver_login, approved_by_note, run_id,"
                 " run_attempt, workflow_commit) VALUES (%s::uuid, %s, %s::uuid, %s, %s, %s, 'race-test', 'ruling:locking-test; actor:race-test', 1, 1,"
                 " (SELECT producer_commit FROM public.ka_gochara_seal_brief WHERE brief_id = %s)) ON CONFLICT (chart_id, generation) DO NOTHING", (CHART_ID, GEN, manifest, digest, bid, eid, bid))


def _seal_on(conn):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(conn, CHART_ID, GEN)
        m = conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
        _write_test_receipt(conn, m)
        return m


def _p3_records(conn):
    return conn.execute("SELECT count(*) FROM public.ka_gochara_relationship_record WHERE event_class = %s AND path_id = 'P3'",
                        (CLS,)).fetchone()[0]


def test_a_builder_rebuild_in_flight_makes_a_racing_seal_wait_then_refuses_it(cbuilt):
    """The builder holds the chart lock mid-rebuild (it deleted the P3 record grain, uncommitted); the sealer's seal BLOCKS on the chart
    lock instead of sealing a half-replaced set, and once the rebuild commits the seal is REFUSED (verification stale or missing)."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)                                            # a fully verified, unsealed generation
    brief_as_verifier(w)                                             # a persisted brief exists (the receipt must name it)
    assert _p3_records(w.conn) > 0, "the scenario needs P3 records to replace"
    builder, sealer = _open(w, cw.BUILDER), _open(w, cw.SEALER)
    result: dict = {}

    def seal():
        try:
            result["manifest"] = _seal_on(sealer)
        except psycopg.errors.Error as exc:
            result["error"] = exc
    try:
        builder.execute("BEGIN")
        rs.RecordStore(builder).delete_record_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")
        t = threading.Thread(target=seal)
        t.start()
        assert _waiting(w.conn, sealer.info.backend_pid), "the seal must WAIT for the builder's chart lock"
        builder.execute("COMMIT")
        t.join(60)
        assert not t.is_alive()
    finally:
        builder.close()
        sealer.close()
    assert "manifest" not in result and "error" in result, result       # refused: the replaced grain no longer matches its verification
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0


def test_a_seal_in_flight_makes_a_racing_builder_rebuild_wait_then_refuses_it(cbuilt):
    """Reverse order: the sealer has sealed inside an open transaction; the builder's replace BLOCKS on the chart lock, and after the seal
    commits it is REFUSED by the sealed-generation guard — never applied to a published set."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    brief_as_verifier(w)                                             # a persisted brief exists (the receipt must name it)
    builder, sealer = _open(w, cw.BUILDER), _open(w, cw.SEALER)
    result: dict = {}

    def rebuild():
        try:
            with builder.transaction():
                rs.RecordStore(builder).delete_record_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3",
                                                            rule_version="1.0.0")
            result["deleted"] = True
        except Exception as exc:                                    # the writer's own sealed-generation refusal, or the database's
            result["error"] = exc
    try:
        sealer.execute("BEGIN")
        sealer.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(sealer, CHART_ID, GEN)
        _write_test_receipt(sealer, sealer.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0])
        t = threading.Thread(target=rebuild)
        t.start()
        assert _waiting(w.conn, builder.info.backend_pid), "the rebuild must WAIT for the sealer's chart lock"
        sealer.execute("COMMIT")
        t.join(60)
        assert not t.is_alive()
    finally:
        builder.close()
        sealer.close()
    assert "deleted" not in result and "error" in result, result
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 1
    assert _p3_records(w.conn) > 0                                    # the published set is intact


# ── 4. round-10 attacks against AM-24 (Stream A head b904e561e) ───────────────────────────────────────────────────

def _verification_rows(conn):
    return (conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0],
            conn.execute("SELECT count(*) FROM public.ka_gochara_search_inventory_verification").fetchone()[0])


def _drop_p3_grain(conn):
    """The builder 'omitted the whole path': every P3 window, member link, prerequisite and record of the class is gone."""
    q = {"c": CHART_ID, "g": GEN, "e": CLS}
    conn.execute("DELETE FROM public.ka_gochara_eval_window_record WHERE chart_id=%(c)s AND generation=%(g)s AND event_class=%(e)s AND path_id='P3'", q)
    conn.execute("DELETE FROM public.ka_gochara_eval_window WHERE chart_id=%(c)s AND generation=%(g)s AND event_class=%(e)s AND path_id='P3'", q)
    rs.RecordStore(conn).delete_record_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")


def test_attack_total_omission_of_a_path_is_a_disagreement_and_persists_nothing(cbuilt):
    """AM-24 (1), R10-1: a path whose stored record set is EMPTY while the obligations x certified contacts demand records is not 'verified empty': the
    job disagrees (exit 3), no verification row of any grain is written, and the seal is refused."""
    import psycopg
    w = cbuilt
    assert _p3_records(w.conn) > 0
    _drop_p3_grain(w.conn)
    assert _p3_records(w.conn) == 0
    with pytest.raises(RuntimeError, match=r"verification job exit 3"):
        verify_as_verifier(w)
    assert _verification_rows(w.conn) == (0, 0)
    with pytest.raises(psycopg.errors.Error):
        db_seal_attempt(w)


def test_attack_a_record_result_changed_after_verification_makes_the_seal_refuse(cbuilt):
    """AM-24 (2)+(3), R10-2: a number written into a record's RESULT after verification changes the inputs digest (inputs/2 covers every result field) and the
    manifest policy forbids a numeric result at all: the seal is refused and no seal row exists."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    rid = w.conn.execute("SELECT record_id FROM public.ka_gochara_relationship_record WHERE event_class=%s AND path_id='P3' ORDER BY record_id LIMIT 1",
                         (CLS,)).fetchone()[0]
    w.conn.execute("UPDATE public.ka_gochara_relationship_record SET severity = 0.5 WHERE record_id = %s", (rid,))
    with pytest.raises(psycopg.errors.Error, match=r"stale|record_result_not_policy|window_verification|verification"):
        db_seal_attempt(w)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0


def test_attack_a_record_result_present_before_verification_is_a_disagreement(cbuilt):
    """R10-2 (policy arm), pre-verification: the job itself refuses to attest a record carrying a numeric result under the all-NULL manifest policy."""
    w = cbuilt
    rid = w.conn.execute("SELECT record_id FROM public.ka_gochara_relationship_record WHERE event_class=%s AND path_id='P3' ORDER BY record_id LIMIT 1",
                         (CLS,)).fetchone()[0]
    w.conn.execute("UPDATE public.ka_gochara_relationship_record SET evidence_for_occurrence = 1.0 WHERE record_id = %s", (rid,))
    with pytest.raises(RuntimeError, match=r"verification job exit 3"):
        verify_as_verifier(w)
    assert _verification_rows(w.conn) == (0, 0)


def test_attack_the_runner_identity_is_recorded_and_a_row_naming_other_code_is_refused_at_the_seal(cbuilt):
    """AM-24 (4), R10-4: every window-verification row names the runner (commit, implementation digest, login); the digest equals the one the manifest pinned; a
    row rewritten to name different code makes the seal refuse (`window_verification_runner_not_pinned`)."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    rows = w.conn.execute("SELECT runner_identity FROM public.ka_gochara_eval_window_verification").fetchall()
    assert len(rows) == 4 and all(r[0]["commit"] and len(r[0]["implementation_digest"]) == 64 for r in rows), rows
    assert all(r[0].get("login") == cw.VERIFIER for r in rows), rows
    pinned = w.conn.execute("SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(input_generation_vector -> 'implementation'))"
                            " FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0]
    assert {r[0]["implementation_digest"] for r in rows} == {pinned}
    # the table is insert-only (UPDATE refused): a changed row is DELETE + INSERT — what a verifier principal that wrote a row naming other code would have done
    w.conn.execute("CREATE TEMP TABLE b6_v AS SELECT * FROM public.ka_gochara_eval_window_verification")
    w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification")
    w.conn.execute("UPDATE b6_v SET runner_identity = jsonb_set(runner_identity, '{implementation_digest}', to_jsonb(repeat('0', 64)))")
    w.conn.execute("INSERT INTO public.ka_gochara_eval_window_verification SELECT * FROM b6_v")
    with pytest.raises(psycopg.errors.Error, match=r"runner_not_pinned|window_verification"):
        db_seal_attempt(w)


def _unbridge_the_candidate_manifest(w):
    """Break what the job's Python re-derivation of the published-only arms reads: the CANDIDATE manifest's legacy convention has no bridge row (the bridge is
    insert-only, so a NEW legacy convention row is inserted and the manifest pointed at it)."""
    conv = w.conn.execute("SELECT convention_id FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0]
    w.conn.execute("CREATE TEMP TABLE b6_conv AS SELECT * FROM public.kala_gochara_convention WHERE convention_id = %s", (conv,))
    w.conn.execute("UPDATE b6_conv SET convention_id = 'b6-unbridged-convention'")
    w.conn.execute("INSERT INTO public.kala_gochara_convention SELECT * FROM b6_conv")
    w.conn.execute("UPDATE public.kala_gochara_publication SET convention_id = 'b6-unbridged-convention' WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN))


def test_attack_the_jobs_published_only_arms_are_enforced_by_the_seal_and_by_a_full_run(cbuilt):
    """The job re-derives three arms of the completeness function against the CANDIDATE manifest (that function reads only a published one). Break what one of them
    reads: a FULL run (every class, the operator's run) reports it and exits 3, and the seal refuses on the real function."""
    import psycopg
    w = cbuilt
    _unbridge_the_candidate_manifest(w)
    with pytest.raises(RuntimeError, match=r"verification job exit 3.*convention_bridge_missing"):
        verify_as_verifier(w, all_classes=True)
    with pytest.raises(psycopg.errors.Error):
        db_seal_attempt(w)


def test_attack_a_subset_run_must_not_report_verified_with_a_generation_level_violation_open(cbuilt):
    """FINDING R11-cand-1 (found by this suite, FIXED by Stream A `d4609f181`): a generation-level gate violation (event_class '*') on a --class SUBSET run used to
    be filed as `gate_outside_scope` and the run reported VERIFIED / exit 0. It now exits 3. (Was a strict xfail until the fix landed.)"""
    w = cbuilt
    _unbridge_the_candidate_manifest(w)
    with pytest.raises(RuntimeError, match=r"verification job exit 3"):
        verify_as_verifier(w)                                   # --class marriage (a subset of the generation's classes)


def _waiting_login(admin, rolname, seconds=60.0):
    end = time.time() + seconds
    while time.time() < end:
        row = admin.execute("SELECT 1 FROM pg_stat_activity WHERE usename = %s AND wait_event_type = 'Lock'", (rolname,)).fetchone()
        if row:
            return True
        time.sleep(0.2)
    return False


def test_attack_a_verification_run_waits_for_a_rebuild_in_flight_and_judges_the_committed_state(cbuilt):
    """R10-3, verifier-vs-builder: the builder holds the chart lock mid-rebuild (it dropped the P3 record grain, uncommitted); the REAL job, started now, WAITS
    for the chart lock before it reads anything; after the builder commits it judges the COMMITTED state — the omitted path — and disagrees. Nothing from the
    pre-commit state is attested."""
    import psycopg
    w = cbuilt
    admin = psycopg.connect(w.conn.info.dsn, autocommit=True, connect_timeout=3)
    builder = _open(w, cw.BUILDER)
    out: dict = {}

    def run():
        try:
            out["report"] = verify_as_verifier(w)
        except RuntimeError as exc:
            out["error"] = exc
    try:
        builder.execute("BEGIN")
        rs.RecordStore(builder).delete_record_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3", rule_version="1.0.0")
        t = threading.Thread(target=run)
        t.start()
        assert _waiting_login(admin, cw.VERIFIER), "the verification job must WAIT for the builder's chart lock"
        builder.execute("COMMIT")
        t.join(300)
        assert not t.is_alive()
    finally:
        builder.close()
    assert "report" not in out and "error" in out, out
    assert _verification_rows(admin) == (0, 0)
    admin.close()


def _login_dsn(w, user, options=None):
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    d = conninfo_to_dict(w.conn.info.dsn)
    d = {k: v for k, v in d.items() if k in ("host", "port", "dbname")}
    d["user"] = user
    if options:
        d["options"] = options
    return make_conninfo("", **d)


def test_identity_negatives_column_grant_elevated_session_and_builder_membership(cbuilt):
    """R10-5: the job's identity self-check refuses (exit 4, nothing written) a verifier that (a) holds a COLUMN-level write on a builder table, (b) is an elevated
    session (a login that SET ROLEs to the verifier) and (c) is a login that is a member of the builder."""
    w = cbuilt
    # (a) a bare column-level UPDATE — invisible to has_table_privilege
    w.conn.execute(f"GRANT UPDATE (note) ON public.ka_gochara_search_path_pin TO {cw.VERIFIER}")
    try:
        with pytest.raises(RuntimeError, match=r"verification job exit 4.*identity_not_separate"):
            verify_as_verifier(w)
    finally:
        w.conn.execute(f"REVOKE UPDATE (note) ON public.ka_gochara_search_path_pin FROM {cw.VERIFIER}")
    # (b) a distinct login, member of the verifier, running under `SET ROLE` (startup option) — session_user != current_user
    w.conn.execute(f"CREATE ROLE b6_elevated LOGIN IN ROLE {cw.VERIFIER}")
    # (c) a login that is a member of the builder
    w.conn.execute(f"CREATE ROLE b6_builder_member LOGIN IN ROLE {cw.BUILDER}")
    try:
        with pytest.raises(RuntimeError, match=r"verification job exit 4.*identity_not_separate.*differs from current_user"):
            verify_as_verifier(w, dsn=_login_dsn(w, "b6_elevated", f"-c role={cw.VERIFIER}"))
        with pytest.raises(RuntimeError, match=r"verification job exit 4.*identity_not_separate.*builder"):
            verify_as_verifier(w, dsn=_login_dsn(w, "b6_builder_member"))
    finally:
        w.conn.execute("DROP ROLE IF EXISTS b6_elevated")
        w.conn.execute("DROP ROLE IF EXISTS b6_builder_member")
    assert _verification_rows(w.conn) == (0, 0)


def test_attack_a_registry_selection_or_inventory_change_after_verification_cannot_be_sealed(cbuilt):
    """AM-24 (2)+(3): the registry SELECTION (the path pins) and the inventory are dependencies of the verified windows. Change what the selection says after
    verification (an excluded pin's ruling, a pin's disposition via delete+insert) — either the database refuses the change itself, or the seal refuses the
    stale attestation; a sealed set never rests on a selection that differs from the one verified."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    pins = w.conn.execute("SELECT path_id, rule_version, disposition FROM public.ka_gochara_search_path_pin WHERE chart_id=%s AND generation=%s AND event_class=%s"
                          " ORDER BY path_id, rule_version", (CHART_ID, GEN, CLS)).fetchall()
    assert pins, "the scenario needs path pins"
    outcomes = []
    for path_id, version, disposition in pins:
        try:
            w.conn.execute("UPDATE public.ka_gochara_search_path_pin SET basis = COALESCE(basis, '') || ' (changed after verification)'"
                           " WHERE chart_id=%s AND generation=%s AND event_class=%s AND path_id=%s AND rule_version=%s", (CHART_ID, GEN, CLS, path_id, version))
            outcomes.append((path_id, "update-accepted"))
        except psycopg.errors.Error as exc:
            outcomes.append((path_id, "update-refused-by-guard"))
            break
    print("PIN_OUTCOMES", outcomes)
    changed = any(o == "update-accepted" for _, o in outcomes)
    if changed:
        with pytest.raises(psycopg.errors.Error):
            seal_as_sealer(w)
        assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    else:
        assert outcomes and outcomes[0][1] == "update-refused-by-guard", outcomes


# ── 5. round 11, R11-1: output outside the permitted grains (Stream A 8c1c0ab63) — the attack as the RESTRICTED BUILDER, real job, real seal ──────────

def _r11_helpers():
    from .test_a53_r11_generation_wide import _attack, _contact_count, _foreign_grain, _gate
    return _attack, _contact_count, _foreign_grain, _gate


@pytest.mark.parametrize("path", ["P3", "P5"])
def test_attack_r11_1_a_record_in_a_sealed_but_excluded_version_or_held_path_with_a_number_is_refused_before_verification(cbuilt, path, monkeypatch):
    """Codex R11-1 counterexample, composed: as the restricted builder, a structurally valid record under a sealed-but-EXCLUDED version (P3 successor) or the HELD
    P5, REUSING an existing contact (no new contact), a numeric result, a consistent admission. The combined gate names `output_grain_not_permitted` and
    `record_result_not_policy`; the REAL job (a real verifier login) refuses it (exit 3, stage generation_output) and persists NOTHING; the seal is refused."""
    import psycopg
    from services.gochara_kernel import input_vector_verifier as ivv
    attack, contact_count, foreign_grain, gate = _r11_helpers()
    w = cbuilt
    grain = foreign_grain(w, path, None)
    # a sealed SUCCESSOR added after the build also drifts the manifest's registry census, which the job's independent input derivation would refuse first
    # (`stale_inputs`); isolate THIS check by letting that derivation pass (the same isolation Stream A's own test uses)
    monkeypatch.setattr(ivv, "verify_inputs", lambda *a, **k: {})
    n = contact_count(w)
    attack(w, *grain)
    assert contact_count(w) == n                                                   # NO new contact
    got = gate(w)
    assert (CLS, grain[0], grain[1], "output_grain_not_permitted") in got and (CLS, grain[0], grain[1], "record_result_not_policy") in got, (grain, got)
    with pytest.raises(RuntimeError, match=r"verification job exit 3.*generation_output"):
        verify_as_verifier(w)
    assert _verification_rows(w.conn) == (0, 0)
    with pytest.raises(psycopg.errors.Error):
        db_seal_attempt(w)


@pytest.mark.parametrize("path", ["P3", "P5"])
def test_attack_r11_1_the_same_attack_after_verification_is_refused_at_the_seal_by_name(cbuilt, path):
    """After a VERIFIED run the included grains' digests do NOT move (the attack reuses an existing contact), which is exactly why the grain-restricted gate let it
    through; the generation-wide arm now refuses the seal BY NAME."""
    import psycopg
    attack, contact_count, foreign_grain, gate = _r11_helpers()
    w = cbuilt
    assert verify_as_verifier(w)["status"] == "VERIFIED"
    grain = foreign_grain(w, path, None)
    before = gate(w)
    attack(w, *grain)
    got = gate(w) - before
    assert (CLS, grain[0], grain[1], "output_grain_not_permitted") in got and (CLS, grain[0], grain[1], "record_result_not_policy") in got, got
    assert not any(v[3] == "window_verification_inputs_changed" for v in gate(w))
    # P5 (held): refused BY NAME by the generation-wide arm. P3 (a sealed successor added after the build): 1206's own registry census (`registry_unaccounted_path`)
    # ALSO refuses it, and its guard fires first on the real seal — a second line of defence; the gate arm above names it either way.
    with pytest.raises(psycopg.errors.Error, match="output_grain_not_permitted" if path == "P5" else "output_grain_not_permitted|registry_unaccounted_path"):
        db_seal_attempt(w)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0


# ── 6. round 11: the approved seal (R11-3) and complete P1 record validation (R11-2), as the real principals ────────────────────────────────

def _receipt(conn):
    return conn.execute("SELECT brief_digest, approver_login, run_id, run_attempt, workflow_commit, sealed_by, manifest_id::text FROM public.ka_gochara_seal_approval").fetchall()


def test_the_approved_seal_publishes_seals_and_writes_a_durable_receipt_naming_the_approved_digest(cbuilt):
    """verify (verifier login) -> brief (verifier login: candidate adapter + persisted attestations + generation-wide output identity + ledger evidence)
    -> approved seal (sealer role): recompute under the seal locks, publish, authoritative SQL seal, receipt — in ONE transaction."""
    w = cbuilt
    b, res = approved_flow(w)
    p = b["brief"]
    assert p["schema"] == "seal_approval_payload/1" and p["candidate_gate"]["violations"] == [] and p["manifest"]["status"] == "candidate"
    # the output identity covers (at least) the seven round-11 tables PLUS the round-12 boundary additions (Codex R12-1 / Fable R12-2): the build's snapshot, obligations and intervals
    assert set(p["generation_output_identity"]["tables"]) >= {"ka_gochara_relationship_record", "ka_gochara_record_prerequisite", "ka_gochara_contact",
                                                              "ka_gochara_eval_window", "ka_gochara_eval_window_record", "ka_gochara_search_path_pin",
                                                              "ka_gochara_search_inventory", "ka_gochara_search_input_snapshot", "ka_gochara_search_obligation",
                                                              "ka_gochara_search_interval"}
    assert [e["migration"] for e in p["ledger"]] == ["1204", "1206", "1232", "1233", "1240", "1241"] and all(e["applied"] for e in p["ledger"]), p["ledger"]
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0] == "published"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 1
    rows = _receipt(w.conn)
    # the sealer is a REAL LOGIN now and the database ATTESTS `sealed_by` (session_user) and `approved_at` — whatever an INSERT names for them is overwritten
    assert rows == [(b["sha256"], "steward-as-owner", 26104817, 1, SEALING_COMMIT, cw.SEALER, res["manifest_id"])], rows


def test_the_receipt_is_append_only_even_for_the_owner(cbuilt):
    import psycopg
    w = cbuilt
    approved_flow(w)
    for stmt in ("UPDATE public.ka_gochara_seal_approval SET approver_login = 'someone-else'", "DELETE FROM public.ka_gochara_seal_approval",
                 "TRUNCATE public.ka_gochara_seal_approval"):
        with pytest.raises(psycopg.errors.Error, match="append-only"):
            w.conn.execute(stmt)
    assert len(_receipt(w.conn)) == 1
    assert w.conn.execute("SELECT public.ka_gochara_seal_receipt_missing(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0] is False


def test_attack_a_candidate_changed_after_the_brief_whose_gate_is_still_empty_invalidates_the_approval(cbuilt):
    """R11-3 (iii): two DIFFERENT valid candidates both give an empty gate. A citation field no gate arm and no inputs/2 digest reads is changed AFTER the brief:
    the candidate adapter still reports nothing (a fresh brief is produced), the new brief digest DIFFERS, and the sealer REFUSES the old approval before
    publishing anything: status stays `candidate`, no seal row, no receipt. The fresh digest then seals (positive control)."""
    from services.gochara_kernel import seal_brief
    w = cbuilt
    verify_as_verifier(w)
    old = brief_as_verifier(w)
    rid = w.conn.execute("SELECT record_id FROM public.ka_gochara_relationship_record WHERE event_class=%s AND path_id='P3' ORDER BY record_id LIMIT 1", (CLS,)).fetchone()[0]
    w.conn.execute("UPDATE public.ka_gochara_relationship_record SET source_text = COALESCE(source_text, '') || ' (edited after the brief)' WHERE record_id = %s", (rid,))
    new = brief_as_verifier(w)                                    # still approvable: the gate sees nothing
    assert new["brief"]["candidate_gate"]["violations"] == [] and new["sha256"] != old["sha256"]
    with pytest.raises(seal_brief.ApprovalMismatch, match="not what was approved"):
        approved_seal_as_sealer(w, old["sha256"])
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0 and _receipt(w.conn) == []
    approved_seal_as_sealer(w, new["sha256"])
    assert len(_receipt(w.conn)) == 1


def test_a_brief_is_refused_for_an_unverified_candidate_and_a_re_verification_after_the_brief_makes_the_brief_stale(cbuilt):
    w = cbuilt
    with pytest.raises(RuntimeError, match=r"brief exit 3.*candidate_not_approvable"):
        brief_as_verifier(w)                                      # built, never verified
    verify_as_verifier(w)
    b = brief_as_verifier(w)
    verify_as_verifier(w)                                         # a second run REPLACES the attestations (new verified_at): the old brief is stale
    from services.gochara_kernel import seal_brief
    with pytest.raises(seal_brief.ApprovalMismatch):
        approved_seal_as_sealer(w, b["sha256"])
    assert _receipt(w.conn) == []


def test_attack_a_raw_seal_by_the_real_sealer_without_a_receipt_is_refused_at_commit_by_name(cbuilt):
    """R11-3, ENFORCED (Stream A bf369fcaa): the sealer role can still CALL the authoritative seal directly, but 1240's deferred constraint trigger refuses to COMMIT a
    first seal with no approval receipt naming THIS manifest. The whole transaction (the publication flip and the seal row) is rolled back: status stays `candidate`,
    no seal row, no receipt. A receipt for ANOTHER manifest does not satisfy it. A REPLAY of an approved seal needs no new receipt."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    with pytest.raises(psycopg.errors.Error, match="approval_receipt_missing"):
        with as_role(w.conn, cw.SEALER):
            _seal(w, receipt=False)
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0 and _receipt(w.conn) == []
    # a receipt that names ANOTHER manifest does not satisfy the trigger
    with pytest.raises(psycopg.errors.Error, match="approval_receipt_missing"):
        with as_role(w.conn, cw.SEALER):
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                gk_ledger.publish(w.conn, CHART_ID, GEN)
                w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN))
                w.conn.execute("INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id, approver_login, approved_by_note,"
                               " run_id, run_attempt, workflow_commit) VALUES (%s::uuid, %s, gen_random_uuid(), repeat('b', 64), 1, 'x', 'x', 'wrong manifest', 1, 1, 'c')", (CHART_ID, GEN))
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    # the approved path still works, and its replay needs no new receipt
    b = brief_as_verifier(w)
    res = approved_seal_as_sealer(w, b["sha256"])
    _replay_as_sealer(w, __import__("uuid").UUID(res["manifest_id"]))
    assert len(_receipt(w.conn)) == 1
    assert w.conn.execute("SELECT public.ka_gochara_seal_receipt_missing(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0] is False


def _copy_p1_record(w, *, person=None, flip_role=None):
    """As the RESTRICTED BUILDER, in one transaction: a copy of an existing P1 anchored record (the SAME contact, anchor and prerequisites — a duplicate), optionally
    with another affected person. No new contact."""
    src = w.conn.execute("SELECT record_id FROM public.ka_gochara_relationship_record WHERE event_class=%s AND path_id='P1' AND contact_id IS NOT NULL"
                         " AND period_anchor_level = 'md' ORDER BY record_id LIMIT 1", (CLS,)).fetchone()[0]
    new = __import__("uuid").uuid4()
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        with as_role(w.conn, cw.BUILDER):
            w.conn.execute("CREATE TEMP TABLE _p1src ON COMMIT DROP AS SELECT * FROM public.ka_gochara_relationship_record WHERE record_id = %s", (src,))
            w.conn.execute("UPDATE _p1src SET record_id = %s" + (", affected_person = %s" if person else ""), (new, person) if person else (new,))
            w.conn.execute("INSERT INTO public.ka_gochara_relationship_record SELECT * FROM _p1src")
            w.conn.execute("INSERT INTO public.ka_gochara_record_prerequisite (record_id, chart_id, generation, ordinal, predicate_id, predicate_rule_version, result)"
                           " SELECT %s, chart_id, generation, ordinal, predicate_id, predicate_rule_version, result FROM public.ka_gochara_record_prerequisite WHERE record_id = %s",
                           (new, src))
    return new


@pytest.mark.parametrize("person", [None, "father"], ids=["duplicate_record", "wrong_affected_person"])
def test_attack_r11_2_a_duplicate_or_wrong_person_p1_record_is_a_disagreement_not_a_verification(cbuilt, person):
    """R11-2: the P1 verifier compares exact record CARDINALITY and the affected person / object role against its own derivation. A duplicate anchored record, or a
    record naming the wrong affected person, made by the restricted builder with no new contact, makes the real job exit 3 and persist nothing."""
    w = cbuilt
    contacts = w.conn.execute("SELECT count(*) FROM public.ka_gochara_contact").fetchone()[0]
    _copy_p1_record(w, person=person)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_contact").fetchone()[0] == contacts
    with pytest.raises(RuntimeError, match=r"verification job exit 3"):
        verify_as_verifier(w)
    assert _verification_rows(w.conn) == (0, 0)



def test_attack_r12_1_legacy_generation_5_numeric_rows_are_refused_by_the_gate_the_brief_and_the_seal(cbuilt):
    """R12-1 (Stream A's `legacy_projection_rows_present` arm): the candidate boundary extends beyond the governed tables: legacy projection rows for generation '5.0' with numeric intensities must make the candidate unapprovable (refused before the
    brief is produced, and again at the seal)."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    w.conn.execute("INSERT INTO public.kala_gochara_windows(chart_id, generation, raw_intensity, signed_intensity) VALUES (%s,'5.0',1.0,1.0)", (CHART_ID,))
    assert any("legacy_projection_rows_present" in str(v) for v in w.conn.execute(
        "SELECT * FROM public.ka_gochara_candidate_gate_violations(%s::uuid, %s)", (CHART_ID, GEN)).fetchall())
    with pytest.raises(RuntimeError, match=r"brief exit 3"):
        brief_as_verifier(w)
    with pytest.raises(psycopg.errors.Error):
        db_seal_attempt(w)



def _sealer_raw(w, statements):
    """A RAW transaction by the real sealer LOGIN, bypassing the sealing job (what a modified or malicious workflow could do): `statements(conn)` runs inside ONE transaction."""
    import psycopg as pg
    w.conn.execute(f"ALTER ROLE {cw.SEALER} LOGIN")
    conn = pg.connect(_sealer_dsn(w), autocommit=True, connect_timeout=3)
    try:
        with conn.transaction():
            return statements(conn)
    finally:
        conn.close()
        w.conn.execute(f"ALTER ROLE {cw.SEALER} NOLOGIN")


def _raw_receipt(conn, digest, **extra):
    manifest = conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
    bid, eid = _brief_ref(conn, digest)
    conn.execute("INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id, approver_login, approved_by_note, run_id,"
                 " run_attempt, workflow_commit) VALUES (%s::uuid, %s, %s::uuid, %s, %s, %s, 'raw-sealer', 'ruling:raw; actor:raw-sealer', 1, 1, %s)",
                 (CHART_ID, GEN, manifest, digest, bid, eid, SEALING_COMMIT))


def test_attack_f_r12_4_the_real_sealer_commits_a_first_seal_with_a_fabricated_digest_and_is_refused_by_name(cbuilt):
    """F-R12-4: the receipt must name a brief the VERIFIER persisted. The real sealer login, with every privilege it legitimately holds and no sealing job, writes a well-formed but
    FABRICATED 64-hex digest: the deferred constraint trigger refuses the COMMIT (`receipt_brief_not_persisted`) — nothing is left: status stays candidate, no seal row, no receipt."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    brief_as_verifier(w)

    def attack(conn):
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(conn, CHART_ID, GEN)
        _raw_receipt(conn, "f" * 64)
    with pytest.raises(psycopg.errors.Error, match="receipt_brief_not_persisted"):
        _sealer_raw(w, attack)
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0 and _receipt(w.conn) == []


def test_attack_f_r12_4_a_superseded_brief_cannot_be_used_but_the_latest_can(cbuilt):
    """F-R12-4: a REAL re-verification replaces the attestations (new `verified_at`), so the brief persisted before it is superseded (and its state changed): the sealing job refuses its digest
    before publishing, a raw sealer commit naming it is refused by the database, and the FRESH brief seals."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    old = brief_as_verifier(w)
    verify_as_verifier(w)                                           # the verifier re-attests: the old brief no longer describes the current state
    new = brief_as_verifier(w)
    assert new["sha256"] != old["sha256"]
    with pytest.raises(_refusals()):
        approved_seal_as_sealer(w, old["sha256"])                   # the sealing job: refused before publishing
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0] == "candidate"

    def attack(conn):
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(conn, CHART_ID, GEN)
        _raw_receipt(conn, old["sha256"])
    with pytest.raises(psycopg.errors.Error, match="receipt_brief_(superseded|state_changed)"):
        _sealer_raw(w, attack)                                     # ...and the database refuses it too
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0 and _receipt(w.conn) == []
    res = approved_seal_as_sealer(w, new["sha256"])
    assert _receipt(w.conn)[0][0] == new["sha256"] and res["brief_digest"] == new["sha256"]


def test_the_database_attests_the_receipts_sealer_and_time_whatever_the_insert_names(cbuilt):
    """Receipt attribution is database-attested (Stream A): a raw INSERT naming another `sealed_by` and an old `approved_at` has both overwritten — the receipt records the real login and the commit-time clock."""
    w = cbuilt
    verify_as_verifier(w)
    b = brief_as_verifier(w)

    def forge(conn):
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(conn, CHART_ID, GEN)
        manifest = conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
        bid, eid = _brief_ref(conn, b["sha256"])
        conn.execute("INSERT INTO public.ka_gochara_seal_approval (chart_id, generation, manifest_id, brief_digest, brief_id, producer_execution_id, approver_login, approved_by_note, run_id,"
                     " run_attempt, workflow_commit, sealed_by, approved_at) VALUES (%s::uuid, %s, %s::uuid, %s, %s, %s, 'raw', 'ruling:raw; actor:raw', 1, 1, %s, 'somebody-else',"
                     " '2000-01-01T00:00:00Z')", (CHART_ID, GEN, manifest, b["sha256"], bid, eid, SEALING_COMMIT))
    _sealer_raw(w, forge)
    row = w.conn.execute("SELECT sealed_by, approved_at > now() - interval '1 hour' FROM public.ka_gochara_seal_approval").fetchone()
    assert row == (cw.SEALER, True), row


def test_attack_f_r12_2_a_coverage_disclosure_edited_after_the_brief_with_an_empty_gate_changes_the_digest_and_refuses_the_old_approval(cbuilt):
    """Fable R12-2: `kala_gochara_coverage`'s disclosure fields are read by no gate arm. Edited AFTER the brief, the gate is still empty, the NEW brief digest differs, and the sealer
    refuses the OLD approval before publishing anything (status stays `candidate`, no seal row, no receipt); the fresh digest then seals (positive control)."""
    from services.gochara_kernel import seal_brief
    w = cbuilt
    verify_as_verifier(w)
    old = brief_as_verifier(w)
    n = w.conn.execute("UPDATE public.kala_gochara_coverage SET unsearched_reason = COALESCE(unsearched_reason, '') || ' (edited after the brief)' WHERE chart_id = %s AND generation = %s",
                       (CHART_ID, GEN)).rowcount
    assert n > 0
    new = brief_as_verifier(w)
    assert new["brief"]["candidate_gate"]["violations"] == [] and new["sha256"] != old["sha256"]
    with pytest.raises(seal_brief.ApprovalMismatch, match="not what was approved"):
        approved_seal_as_sealer(w, old["sha256"])
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0 and _receipt(w.conn) == []
    approved_seal_as_sealer(w, new["sha256"])
    assert len(_receipt(w.conn)) == 1


def test_the_brief_digest_does_not_depend_on_the_sessions_timezone_setting(cbuilt):
    """Fable R12-6: the brief (verifier login, Cloud Run) and the recompute (sealer login, GitHub runner) are different sessions. A role-level `timezone` on the verifier must not move the
    digest, and the approved seal by the sealer (default timezone) must still accept it."""
    w = cbuilt
    verify_as_verifier(w)
    base = brief_as_verifier(w)
    w.conn.execute(f"ALTER ROLE {cw.VERIFIER} SET timezone = 'Asia/Kolkata'")
    try:
        shifted = brief_as_verifier(w)
    finally:
        w.conn.execute(f"ALTER ROLE {cw.VERIFIER} RESET timezone")
    assert shifted["sha256"] == base["sha256"]
    approved_seal_as_sealer(w, shifted["sha256"])
    assert len(_receipt(w.conn)) == 1


def test_the_sealing_job_refuses_a_login_that_is_not_the_bare_sealer(cbuilt):
    """Fable R12-5: the sealing step proves its identity before anything is done. A superuser, a login that is a MEMBER of the sealer (session_user is not the sealer), and a sealer that
    holds an extra write privilege are each refused with `identity_not_sealer` — nothing published, no receipt."""
    import psycopg as pg
    from services.gochara_kernel import seal_flow
    w = cbuilt
    verify_as_verifier(w)
    b = brief_as_verifier(w)
    bid, eid = _brief_ref(w.conn, b["sha256"])
    approval = {"schema": "seal_approval/2", "brief_digest": b["sha256"], "brief_id": bid, "producer_execution_id": eid, "run_id": 1, "run_attempt": 1, "approver_login": "x", "approved_by_note": NOTE}

    def attempt(conn):
        return seal_flow.execute_seal(conn, chart_id=CHART_ID, generation=GEN, approval=approval, run_id=1, run_attempt=1, sealing_commit=SEALING_COMMIT, triggering_actor="steward-as-owner")
    # (a) a superuser (the harness connection's own role is not the sealer)
    c = pg.connect(w.conn.info.dsn, autocommit=True)
    try:
        with pytest.raises(seal_flow.SealRefused, match="identity_not_sealer"):
            attempt(c)
    finally:
        c.close()
    # (b) a login that is a member of the sealer
    w.conn.execute(f"CREATE ROLE b6_sealer_member LOGIN IN ROLE {cw.SEALER}")
    try:
        c = pg.connect(_login_dsn(w, "b6_sealer_member"), autocommit=True, connect_timeout=3)
        try:
            with pytest.raises(seal_flow.SealRefused, match="identity_not_sealer"):
                attempt(c)
        finally:
            c.close()
    finally:
        w.conn.execute("DROP ROLE IF EXISTS b6_sealer_member")
    # (c) the sealer itself, holding a write privilege beyond the seal set
    w.conn.execute(f"GRANT UPDATE (note) ON public.ka_gochara_search_path_pin TO {cw.SEALER}")
    w.conn.execute(f"ALTER ROLE {cw.SEALER} LOGIN")
    try:
        c = pg.connect(_sealer_dsn(w), autocommit=True, connect_timeout=3)
        try:
            with pytest.raises(seal_flow.SealRefused, match="identity_not_sealer"):
                attempt(c)
        finally:
            c.close()
    finally:
        w.conn.execute(f"ALTER ROLE {cw.SEALER} NOLOGIN")
        w.conn.execute(f"REVOKE UPDATE (note) ON public.ka_gochara_search_path_pin FROM {cw.SEALER}")
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0 and _receipt(w.conn) == []


def test_cross_pr_round_trip_the_real_brief_stdout_through_the_real_extractor_check_approval_and_seal_job(cbuilt, tmp_path):
    """F-R13-1 (the seam bug): the sealing workflow's scripts (PR #2975) had only ever seen a FIXTURE brief. Here the REAL `--brief` stdout (Stream A head 7e81f2870: chunk
    lines, then the compact `BRIEFED` line) as a real verifier login goes, shaped as Cloud Run log entries, through the REAL extractor and the REAL check, the REAL approval extraction,
    and the REAL gated orchestrator script, which runs the REAL `seal_job` as a subprocess on the sealer login — and the receipt names the digest the verifier persisted."""
    # G6 (steward M20261002T230554-65a7): the composed fixture's daśā rows are ONE pinned build — else the writer's and verifier's `dasha_builds_mixed` / `dasha_build_not_pinned` refusals fire in this harness
    builds = [r[0] for r in cbuilt.conn.execute("SELECT DISTINCT build_id::text FROM public.chart_dashas WHERE chart_id = %s AND system_id = 'vimshottari' ORDER BY 1", (CHART_ID,)).fetchall()]
    assert builds == [PINNED_BUILD], builds
    import hashlib as _hl
    import json as _json
    import subprocess
    import sys as _sys
    scripts = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "scripts"))
    _sys.path.insert(0, scripts)
    try:
        import gochara_seal_approval as sa  # noqa: F401
        import gochara_seal_brief_check as bc
        import gochara_seal_brief_extract as bx
        import gochara_seal_execution_check as xc
        import gochara_verification_job_contract  # noqa: F401 — xc imports it lazily at call time, after this block removes the path; cache it now
        import gochara_seal_reconcile as rc_
    finally:
        _sys.path.remove(scripts)
    w = cbuilt
    verify_as_verifier(w)
    out = brief_stdout_as_verifier(w, SEALING_COMMIT, "--brief-chunk-bytes", "4096")        # small slices: the multi-chunk path is the one that matters
    lines = out.splitlines()
    compact = _json.loads(lines[-1])
    assert compact["status"] == "BRIEFED" and compact["brief_chunks"] is True and compact["contract_version"] == "seal_brief_transport/1"
    assert set(compact) == {"brief_bytes", "brief_chunks", "brief_file", "contract_version", "persisted", "producer", "sha256", "status"}
    assert compact["producer"] == {"commit": SEALING_COMMIT, "image_digest": IMAGE_DIGEST, "execution_id": EXECUTION_NAME}     # what the job's own environment carried
    assert sum(1 for l in lines if l.startswith('{"b64"')) > 1
    # the REAL Cloud Run representation: a JSON object printed on stdout is parsed into the entry's ROOT jsonPayload (R13-1); arrival order is not relied on
    def struct(v):
        """Cloud Run's protobuf Struct: key order is lost and EVERY number is a double (3 -> 3.0)."""
        if isinstance(v, bool) or v is None or isinstance(v, str):
            return v
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, dict):
            return {k: struct(v[k]) for k in sorted(v, reverse=True)}
        return [struct(x) for x in v]
    logs = [{"textPayload": "starting"}, *[{"jsonPayload": struct(_json.loads(l)), "labels": {"run.googleapis.com/execution_name": EXECUTION_NAME}} for l in reversed(lines)], {"textPayload": "done"}]
    raw, comp = bx.extract(logs)                                                           # the REAL extractor
    digest = bc.check(raw, comp, chart_id=CHART_ID, generation=GEN, sealing_commit=SEALING_COMMIT)    # the REAL check
    assert digest == compact["sha256"] == _hl.sha256(raw).hexdigest()
    from services.gochara_kernel import seal_brief
    assert bc.canon(_json.loads(raw)) == raw.decode("utf-8") == seal_brief.canonical_json(_json.loads(raw))    # the two canonical encoders agree on the REAL brief
    brief_file, compact_file, envelope_file, approvals = tmp_path / "brief.json", tmp_path / "brief.compact.json", tmp_path / "brief.envelope.json", tmp_path / "approvals.json"
    brief_file.write_bytes(raw)
    compact_file.write_text(_json.dumps(comp))
    run_id, attempt = 26104899, 2
    brief_id = comp["persisted"]["brief_id"]
    # STAND-IN (the one place this rig does not run the real thing): the Cloud Run execution resource. The envelope is built through the REAL `gochara_seal_execution_check` from an execution
    # description in the documented shape; the first real execution is the proof of that shape.
    img = IMAGE_DIGEST
    sa = "gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com"
    args = ["--chart", CHART_ID, "--generation", GEN, "--brief", "--sealing-commit", SEALING_COMMIT]
    execution = {"metadata": {"name": EXECUTION_NAME}, "spec": {"taskCount": 1, "template": {"spec": {"serviceAccountName": sa, "maxRetries": 0, "timeoutSeconds": "7200", "containers": [{       # int64 arrives as a decimal STRING (API/SDK shape)
        "resources": {"limits": {"cpu": "2", "memory": "8Gi"}},
        "image": f"asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline@{img}", "command": ["python", "-m", "pipeline.orchestrator.verification_job"], "args": args,
        "env": [{"name": "GOCHARA_RUNNER_COMMIT", "value": SEALING_COMMIT}, {"name": "GOCHARA_RUNNER_IMAGE_DIGEST", "value": img},
                {"name": "GOCHARA_VERIFIER_DB_URL", "valueFrom": {"secretKeyRef": {"name": "gochara-verifier-db-url", "key": "latest"}}}]}]}}},
        "status": {"conditions": [{"type": "Completed", "status": "True"}], "succeededCount": 1}}
    verified = xc.check(execution, execution_name=EXECUTION_NAME, image_repo="asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline", image_digest=img, service_account=sa, runner_commit=SEALING_COMMIT, args=args, secret_name="gochara-verifier-db-url")
    xc.bind_producer(verified, comp["producer"], execution_name=EXECUTION_NAME, sealing_commit=SEALING_COMMIT)       # the brief's OWN producer line == the executed resource
    envelope_file.write_text(_json.dumps(xc.build_envelope(verified, run_id=str(run_id), attempt=str(attempt), sealing_commit=SEALING_COMMIT, brief_digest=digest, brief_id=brief_id,
                                                           producer_execution_id=comp["producer"]["execution_id"])))
    approvals.write_text(_json.dumps([{"state": "approved", "user": {"login": "steward-as-owner"}, "environments": [{"name": "gochara-seal"}],
                                      "comment": f"brief-digest: {digest}  run: {run_id}  attempt: {attempt}  brief-id: {brief_id}"}]))
    orch = os.path.join(scripts, "gochara-seal-approved.sh")
    w.conn.execute(f"ALTER ROLE {cw.SEALER} LOGIN")
    try:
        env = {**os.environ, "BRIEF_FILE": str(brief_file), "BRIEF_COMPACT_FILE": str(compact_file), "BRIEF_ENVELOPE_FILE": str(envelope_file), "APPROVALS_FILE": str(approvals), "CHART_ID": CHART_ID, "GENERATION": GEN,
               "EXPECTED_SEALING_COMMIT": SEALING_COMMIT, "EXPECTED_BRIEF_DIGEST": digest, "GITHUB_RUN_ID": str(run_id), "GITHUB_RUN_ATTEMPT": str(attempt),
               "GITHUB_SHA": SEALING_COMMIT, "TRIGGERING_ACTOR": "steward-as-owner", "APPROVAL_FILE": str(tmp_path / "approval.json"),
               "PYTHON_BIN": _sys.executable, "GOCHARA_SEALER_DB_URL": _sealer_dsn(w), "PYTHONPATH": os.getcwd()}
        r = subprocess.run(["bash", orch], env=env, capture_output=True, text=True, timeout=300)
    finally:
        w.conn.execute(f"ALTER ROLE {cw.SEALER} NOLOGIN")
    assert r.returncode == 0, (r.stdout[-1500:], r.stderr[-1500:])
    assert len(_receipt(w.conn)) == 1
    row = w.conn.execute("SELECT brief_digest, run_id, run_attempt, approved_by_note, sealed_by FROM public.ka_gochara_seal_approval").fetchone()
    assert tuple(row) == (digest, run_id, attempt, "ruling:NATIVE_DIRECT_RULINGS_20261002#2; actor:steward-as-owner", cw.SEALER), row
    ids = w.conn.execute("SELECT brief_id, producer_execution_id FROM public.ka_gochara_seal_approval").fetchone()
    assert tuple(ids) == (brief_id, EXECUTION_NAME), ids                                      # the receipt names the SPECIFIC persisted brief and execution (ST-WIRE-2)
    # R13-4: the reconcile step, run AS THE REAL SEALER LOGIN, reads what is actually true after the seal
    w.conn.execute(f"ALTER ROLE {cw.SEALER} LOGIN")
    try:
        import psycopg as pg
        c = pg.connect(_sealer_dsn(w), autocommit=True, connect_timeout=3)
        try:
            pub, seals, recs = rc_.read_state(c, CHART_ID, GEN)
        finally:
            c.close()
    finally:
        w.conn.execute(f"ALTER ROLE {cw.SEALER} NOLOGIN")
    assert rc_.classify(pub, seals, recs, digest=digest, run_id=run_id, attempt=attempt)[0] == "SEALED", (pub, seals, recs)
    assert rc_.classify(pub, seals, recs, digest=digest, run_id=run_id, attempt=attempt + 1)[0] == "INCONSISTENT"


def test_brief_size_report_per_class_and_projected_to_the_real_class_count(cbuilt):
    """F-R13-2 MEASUREMENT (it decided the chunked transport): the brief was one stdout line. Report its bytes by component on the rig (one class, four grains) and the per-class increment, then project to the
    real class count — against Cloud Logging's documented 256 KiB per-entry limit. Asserts only the arithmetic; the numbers are the evidence (printed with -s / in the report)."""
    import json as _json
    w = cbuilt
    verify_as_verifier(w)
    from services.gochara_kernel import seal_brief
    b = brief_as_verifier(w)["brief"]
    total = len(seal_brief.canonical_json(b).encode("utf-8"))          # the brief FILE's bytes (Stream A: the canonical JSON; it travels as 48 KiB chunk lines now)
    classes = b["classes"]
    # per class: the class entry AND its persisted attestation rows (4 window rows + 1 inventory row per class on the rig); everything else is fixed
    per_class = len(_json.dumps(classes[0], sort_keys=True).encode("utf-8")) + len(_json.dumps(b["attestations"], sort_keys=True).encode("utf-8")) // len(classes)
    comps = {k: len(_json.dumps(v, sort_keys=True, default=str).encode("utf-8")) for k, v in b.items()}
    real_classes = w.conn.execute("SELECT count(DISTINCT event_class) FROM public.ka_gochara_search_path_pin").fetchone()[0]
    grains = sum(len(c["grains"]) for c in classes)
    fixed = total - per_class * len(classes)
    LIMIT = 256 * 1024
    for n in (len(classes), real_classes, 26):
        print(f"BRIEF_SIZE classes={n} projected_bytes={fixed + per_class * n} limit={LIMIT} fits={fixed + per_class * n < LIMIT}")
    print(f"BRIEF_SIZE rig: total_bytes={total} classes_in_brief={len(classes)} grains={grains} per_class_bytes={per_class} fixed_bytes={fixed} pinned_classes_in_rig={real_classes}")
    print("BRIEF_SIZE components:", _json.dumps(comps, sort_keys=True))
    assert total > 0 and grains >= 1 and fixed > 0


def test_stream_as_golden_log_entries_go_through_the_sealing_scripts_unchanged():
    """Stream A's golden LOG ENTRIES (`golden_brief_log_entries_1class.json`: the documented Cloud Logging LogEntry shape, root `jsonPayload`) and golden stdout. CAVEAT (kept in the packet): the
    fixture is BUILT FROM THE DOCUMENTATION, NOT CAPTURED from a real execution — the first real execution (runbook act 6b) is diffed against it. B's REAL extractor reassembles it; B's REAL
    check accepts everything about it except the sealing commit (the fixture's placeholder `cli-sha` is not a revision), which must be the ONE refusal."""
    import hashlib
    import json as _json
    import sys as _sys
    scripts = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "scripts"))
    _sys.path.insert(0, scripts)
    try:
        import gochara_seal_brief_check as bc
        import gochara_seal_brief_extract as bx
    finally:
        _sys.path.remove(scripts)
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "fixtures", "golden_brief_log_entries_1class.json"), encoding="utf-8") as f:
        from_entries = _json.load(f)
    raw, compact = bx.extract(from_entries)
    with open(os.path.join(here, "fixtures", "golden_brief_stdout_1class.txt"), encoding="utf-8") as f:
        raw2, compact2 = bx.extract([{"textPayload": l} for l in f.read().splitlines()])
    assert (raw, compact) == (raw2, compact2)                                                  # the two goldens agree
    assert hashlib.sha256(raw).hexdigest() == compact["sha256"] and len(raw) == compact["brief_bytes"]
    assert compact["contract_version"] == "seal_brief_transport/1" and set(compact["producer"]) == {"commit", "execution_id", "image_digest"}
    p = _json.loads(raw)
    with pytest.raises(bc.Refused, match="not this workflow's reviewed revision"):
        bc.check(raw, compact, chart_id=p["chart_id"], generation=p["generation"], sealing_commit="a" * 40)


def test_the_sealing_job_refuses_owner_membership_and_column_grants_on_the_verification_and_brief_tables(cbuilt):
    """Codex R13-5 (the adopted sealer self-check omitted two prohibited capabilities): (a) a sealer that is a MEMBER of a role that OWNS the Gochara tables — NOINHERIT membership included —
    and (b) a sealer holding only a COLUMN-level write on a VERIFICATION table or on the brief table are each refused with `identity_not_sealer`, nothing published, no receipt."""
    import psycopg as pg
    from services.gochara_kernel import seal_flow
    w = cbuilt
    verify_as_verifier(w)
    b = brief_as_verifier(w)
    bid, eid = _brief_ref(w.conn, b["sha256"])
    approval = {"schema": "seal_approval/2", "brief_digest": b["sha256"], "brief_id": bid, "producer_execution_id": eid, "run_id": 1, "run_attempt": 1, "approver_login": "x", "approved_by_note": NOTE}

    def attempt():
        w.conn.execute(f"ALTER ROLE {cw.SEALER} LOGIN")
        try:
            c = pg.connect(_sealer_dsn(w), autocommit=True, connect_timeout=3)
            try:
                with pytest.raises(seal_flow.SealRefused, match="identity_not_sealer"):
                    seal_flow.execute_seal(c, chart_id=CHART_ID, generation=GEN, approval=approval, run_id=1, run_attempt=1, sealing_commit=SEALING_COMMIT, triggering_actor="steward-as-owner")
            finally:
                c.close()
        finally:
            w.conn.execute(f"ALTER ROLE {cw.SEALER} NOLOGIN")
    # (a) membership of the table-owning role (the sealer is NOINHERIT: only pg_has_role(..., 'MEMBER') sees it)
    w.conn.execute(f"GRANT {cw.OWNER} TO {cw.SEALER}")
    try:
        attempt()
    finally:
        w.conn.execute(f"REVOKE {cw.OWNER} FROM {cw.SEALER}")
    # (b) a column-only write on each of: a verification table (window), the other verification table (inventory), the brief table
    for table, col, priv in (("ka_gochara_eval_window_verification", "chart_id", "INSERT"), ("ka_gochara_search_inventory_verification", "chart_id", "UPDATE"),
                             ("ka_gochara_seal_brief", "state_digest", "UPDATE")):
        w.conn.execute(f"GRANT {priv} ({col}) ON public.{table} TO {cw.SEALER}")
        try:
            attempt()
        finally:
            w.conn.execute(f"REVOKE {priv} ({col}) ON public.{table} FROM {cw.SEALER}")
    assert w.conn.execute("SELECT status FROM public.kala_gochara_publication WHERE chart_id=%s AND generation=%s", (CHART_ID, GEN)).fetchone()[0] == "candidate"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0 and _receipt(w.conn) == []


def test_attack_on_a_sealed_generation_the_manifests_result_policy_cannot_be_removed_or_altered_by_the_builder_or_the_sealer(cbuilt):
    """Steward round-15 attack: Stream A's sealed-contact guard keys its SCOPE on the manifest's `result_policy` key (a sealed manifest without it is treated as a PRE-regime seal and
    the older, looser behaviour applies). So on a SEALED generation, removing or altering that key would silently re-open the contact/record write path. Each of: removing the key,
    changing its value, and replacing the whole vector, attempted (a) as the RESTRICTED BUILDER and (b) as the REAL SEALER login, must be REFUSED, and the manifest must be unchanged."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    seal_as_sealer(w)
    before = w.conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    assert '"result_policy"' in before
    attacks = ("UPDATE public.kala_gochara_publication SET input_generation_vector = input_generation_vector - 'result_policy' WHERE chart_id = '%s' AND generation = '%s'" % (CHART_ID, GEN),
               "UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector, '{result_policy}', '\"numeric_policy/1\"') WHERE chart_id = '%s' AND generation = '%s'" % (CHART_ID, GEN),
               "UPDATE public.kala_gochara_publication SET input_generation_vector = '{}'::jsonb WHERE chart_id = '%s' AND generation = '%s'" % (CHART_ID, GEN))
    for stmt in attacks:                                                                  # (a) the restricted builder (a savepoint per attempt, so the connection stays usable)
        with pytest.raises((psycopg.errors.Error, RuntimeError)):
            with as_role(w.conn, cw.BUILDER):
                with w.conn.transaction():
                    w.conn.execute(stmt)
    for stmt in attacks:                                                                  # (b) the real sealer login
        with pytest.raises(psycopg.errors.Error):
            _sealer_raw(w, lambda conn, st=stmt: conn.execute(st))
    after = w.conn.execute("SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    assert after == before


def test_the_boundary_guard_inventory_reports_every_boundary_relation_existing_and_guarded(cbuilt):
    """Runbook §4.1 W5 / Stream A's `ka_gochara_boundary_guard_inventory()`: four rows, each (exists, write_guarded, truncate_guarded) = (true, true, true) in the composed world."""
    rows = cbuilt.conn.execute("SELECT * FROM public.ka_gochara_boundary_guard_inventory()").fetchall()
    got = [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in rows]
    assert len(got) == 4 and all(r[1:] == (True, True, True) for r in got), got


def test_attack_the_sealed_manifest_guard_refuses_even_a_role_that_HOLDS_the_column_privilege(cbuilt):
    """Fable F-R15-5(d) / steward: the earlier sealer-login attack on the manifest's `result_policy` proves the COLUMN ACL (the sealer has no UPDATE on `input_generation_vector`), not the
    GUARD. Here the sealer is GRANTED that column privilege (the harness superuser grants it; the real 1241 does not) so the ACL no longer refuses — and the publication guard on the SEALED
    generation must refuse the removal, the alteration and the replacement ITSELF (named refusal, manifest unchanged). The grant is revoked afterwards."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)
    seal_as_sealer(w)
    q = "SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s"
    before = w.conn.execute(q, (CHART_ID, GEN)).fetchone()[0]
    attacks = ("UPDATE public.kala_gochara_publication SET input_generation_vector = input_generation_vector - 'result_policy' WHERE chart_id = '%s' AND generation = '%s'" % (CHART_ID, GEN),
               "UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector, '{result_policy}', '\"numeric_policy/1\"') WHERE chart_id = '%s' AND generation = '%s'" % (CHART_ID, GEN),
               "UPDATE public.kala_gochara_publication SET input_generation_vector = '{}'::jsonb WHERE chart_id = '%s' AND generation = '%s'" % (CHART_ID, GEN))
    w.conn.execute(f"GRANT UPDATE (input_generation_vector) ON public.kala_gochara_publication TO {cw.SEALER}")
    try:
        # first prove the privilege is REAL: the ACL no longer stands in the way (a harmless same-value update on a candidate is not available here, so check the catalog)
        assert w.conn.execute("SELECT has_column_privilege(%s, 'public.kala_gochara_publication', 'input_generation_vector', 'UPDATE')", (cw.SEALER,)).fetchone()[0] is True
        for stmt in attacks:
            with pytest.raises(psycopg.errors.Error) as exc:
                _sealer_raw(w, lambda conn, st=stmt: conn.execute(st))
            assert not isinstance(exc.value, psycopg.errors.InsufficientPrivilege), ("the ACL refused, not the guard", str(exc.value)[:200])
            assert "seal" in str(exc.value).lower() or "guard" in str(exc.value).lower() or "lifecycle" in str(exc.value).lower() or "refused" in str(exc.value).lower(), str(exc.value)[:300]
    finally:
        w.conn.execute(f"REVOKE UPDATE (input_generation_vector) ON public.kala_gochara_publication FROM {cw.SEALER}")
    assert w.conn.execute(q, (CHART_ID, GEN)).fetchone()[0] == before
