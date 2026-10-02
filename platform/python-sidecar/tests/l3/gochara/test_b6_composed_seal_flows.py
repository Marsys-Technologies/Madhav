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
Known-defect markers (strict xfail — they flip to failures the day Stream A fixes them): R9-6.1 (the shipped inventory store DELETEs the
verification table as the builder) and R9-9 (the geometry self-check probes 1 s from an edge the solver locates to 1 arcsecond).
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
from .test_a53_inventory import CHART_ID
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

def _store_without_verification_delete(mp):
    """STAND-IN for Stream A's pending R9-6.1 change: the builder holds no DELETE on the verification table (PC-4), so the store must not
    DELETE it (the 1206 FK now cascades from the header)."""
    mp.setattr(inventory_store, "_CLASS_TABLES_DELETE_ORDER",
               tuple(t for t in inventory_store._CLASS_TABLES_DELETE_ORDER if "verification" not in t))


def _widened_geometry(mp):
    """STAND-IN for Stream A's pending fix of R9-9: `verify_member_geometry` probes 1 SECOND from each stored contact edge, but the contact
    solver's declared accuracy is 1 ARCSECOND (arcs.DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC) — ~24 s of Sun time, ~12 min of Saturn time — so on the
    REAL sky the writer's own window phase rejects its own correct contacts. The stand-in widens the default margin to one hour (the verifier
    caps it at a quarter of the span)."""
    orig = wv.verify_member_geometry

    def widened(conn, **kw):
        kw.setdefault("probe_seconds", 3600.0)
        return orig(conn, **kw)
    mp.setattr(wv, "verify_member_geometry", widened)


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
    with psycopg.connect(cw.ADMIN_DSN, autocommit=True, connect_timeout=3) as c:
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
    _store_without_verification_delete(mp)
    _widened_geometry(mp)
    gen, w = _real_world(mp, tmp_path_factory.mktemp("eph"), create)
    try:
        build_as_builder(w)
        w.conn.close()
        if keep:
            import psycopg
            with psycopg.connect(cw.ADMIN_DSN, autocommit=True, connect_timeout=3) as c:
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
    _store_without_verification_delete(monkeypatch)
    _widened_geometry(monkeypatch)
    gen, w = _real_world(monkeypatch, tmp_path, lambda: cw.composed_clone(built_template))
    apply_extra_grants(w.conn)                        # the verifier's/sealer's derived sets (the template may predate an EXTRA change)
    try:
        yield w
    finally:
        gen.close()


@pytest.fixture()
def cbuilt_shipped(built_template, monkeypatch, tmp_path):
    """The same clone WITHOUT the two stand-ins: Stream A's code as shipped."""
    gen, w = _real_world(monkeypatch, tmp_path, lambda: cw.composed_clone(built_template))
    apply_extra_grants(w.conn)
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


@pytest.mark.xfail(strict=True, raises=RuntimeError,
                   reason="R9-6.1: the shipped inventory store still DELETEs the verification table as the builder; remove this xfail when "
                          "Stream A drops it from _CLASS_TABLES_DELETE_ORDER")
def test_the_shipped_inventory_store_rebuilds_as_the_restricted_builder(cbuilt_shipped):
    try:
        with as_role(cbuilt_shipped.conn, cw.BUILDER):
            cbuilt_shipped.step("inventory:marriage")
    except RuntimeError as exc:
        if "ka_gochara_search_inventory_verification" not in str(exc):
            pytest.fail(f"failed for a DIFFERENT reason than R9-6.1: {exc}")       # a wrong-reason failure must not hide as the known defect
        raise


@pytest.mark.xfail(strict=True, raises=RuntimeError,
                   reason="R9-9: the shipped geometry self-check (1 s probes) is tighter than the solver's 1-arcsecond accuracy, so a real-sky "
                          "build rejects its own contacts; remove when Stream A scales the probe margin to the solver tolerance and the body's speed")
def test_the_shipped_geometry_self_check_accepts_a_real_sky_window_build(cbuilt_shipped):
    try:
        with as_role(cbuilt_shipped.conn, cw.BUILDER):
            for p in ("P1", "P2", "P3", "P4"):
                cbuilt_shipped.step(f"window:{CLS}:{p}")
    except RuntimeError as exc:
        if "member geometry verification failed" not in str(exc):
            pytest.fail(f"failed for a DIFFERENT reason than R9-9: {exc}")
        raise


# ── 2. first seal: builder → verifier → sealer, every guard on ──────────────────────────────────────────────────

def _real_position_at(body, t):
    jd = t.timestamp() / 86400.0 + 2440587.5
    return REAL_CALC(body.title(), jd, EPHE)[0]


def verify_as_verifier(w, position_at=_real_position_at):
    """The separate verification RUNNER (R9-6): the verifier principal runs the independent derivations on its OWN grants and persists
    the inventory verification (the writer's verify step) and one window verification per included grain."""
    with as_role(w.conn, cw.VERIFIER):
        # ORDER (found by this rehearsal): the class's inventory verification step runs the candidate gate, which REFUSES until every included
        # grain has a window verification — so the runner records the window verifications FIRST, then the inventory verification.
        for path in ("P1", "P2", "P3", "P4"):
            grain = dict(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=path, rule_version="1.0.0")
            rows = writer_mod.RuleRegistryStore(w.conn).bound_factor_rows(path, "1.0.0")
            report = wv.verify_window_semantics(w.conn, factor_rows=rows, **grain)
            wv.verify_member_support(w.conn, **grain)
            wv.verify_member_geometry(w.conn, position_at=position_at, probe_seconds=3600.0, **grain)
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
                wg.record_verification(w.conn, report=report, input_digest=_input_digest(w), **grain)
        note = w.step(f"verify:{CLS}").notes
    return note


def seal_as_sealer(w):
    with as_role(w.conn, cw.SEALER):
        return _seal(w)


def _replay_as_sealer(w, manifest):
    """The REPLAY of an existing seal (ka_gochara_seal_generation inserts ON CONFLICT DO NOTHING; the BEFORE triggers — 1206's and 1240's — fire
    first and re-check what they can): idempotent, returns the same manifest, adds no row."""
    with as_role(w.conn, cw.SEALER):
        again = w.conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]
    assert again == manifest
    return again


def _grants_of_1241():
    """(role, kind, privilege, object) for every privilege the REAL 1241 file grants, parsed from its own GRANT statements."""
    import re
    from .test_a53_record_store import MIGRATIONS
    if not (MIGRATIONS / cw.M1241).exists():
        return []                                      # the integration exhibit without 1241 in the tree: the parametrized tests are skipped
    sql = "\n".join(l for l in (MIGRATIONS / cw.M1241).read_text().split("\n") if not l.strip().startswith("--"))
    out = []
    for head, role in re.findall(r"GRANT\s+(.*?)\s+TO\s+(gochara_\w+);", sql, re.S):
        if head.startswith("EXECUTE ON FUNCTION"):
            for name, args in re.findall(r"public\.(\w+)\(([^)]*)\)", head):
                out.append((role, "func", "EXECUTE", f"{name}({', '.join(a.strip() for a in args.split(',') if a.strip())})"))
        else:
            m = re.match(r"((?:SELECT|INSERT|UPDATE|DELETE)(?:\s*,\s*(?:SELECT|INSERT|UPDATE|DELETE))*)\s+ON\s+(.*)", head, re.S)
            for priv in re.split(r"\s*,\s*", m.group(1)):
                for t in re.findall(r"public\.(\w+)", m.group(2)):
                    out.append((role, "table", priv, t))
    return out


_G1241 = _grants_of_1241()


def test_1241_parses_to_the_expected_number_of_grants():
    if not _G1241:
        pytest.skip("NOT_RUN: migration 1241 is not in this tree")
    assert len(_G1241) == len(set(_G1241)) == 36, len(_G1241)          # sealer: 10 table + 18 function; verifier: 7 table + 1 function


@pytest.mark.parametrize("role,kind,priv,obj", _G1241, ids=[f"{r.split('_')[1]}-{p.lower()}-{o}" for r, k, p, o in _G1241])
def test_each_grant_of_migration_1241_is_individually_necessary(cbuilt, role, kind, priv, obj):
    """The REAL 1241 file is applied; ONE of its privileges is revoked; the verification-then-seal flow must then FAIL on a permission denial —
    so every grant in the file is demonstrably needed by a flow (nothing speculative)."""
    w = cbuilt
    if kind == "table":
        w.conn.execute(f"REVOKE {priv} ON public.{obj} FROM {role}")
    else:
        w.conn.execute(f"REVOKE EXECUTE ON FUNCTION public.{obj} FROM {role}")
    with pytest.raises(RuntimeError, match=r"permission denied"):
        verify_as_verifier(w)
        manifest = seal_as_sealer(w)
        _replay_as_sealer(w, manifest)


@pytest.mark.parametrize("role", [cw.VERIFIER, cw.SEALER])
@pytest.mark.parametrize("table", ["chart_facts", "chart_dashas"])
def test_the_l1_reads_that_1241_does_not_carry_are_individually_necessary(cbuilt, role, table):
    """The OPEN item for the data-plane ACL owner: without SELECT on these L1 tables the verification-then-seal flow fails."""
    w = cbuilt
    w.conn.execute(f"REVOKE SELECT ON public.{table} FROM {role}")
    with pytest.raises(RuntimeError, match=r"permission denied"):
        verify_as_verifier(w)
        seal_as_sealer(w)


def test_first_seal_builder_then_verifier_then_sealer_with_every_guard_enabled(cbuilt):
    import psycopg
    w = cbuilt
    # before any verification the candidate gate is CLOSED and the seal is refused (the honest "built, not verified" state)
    with pytest.raises(psycopg.errors.Error):
        seal_as_sealer(w)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 0
    note = verify_as_verifier(w)
    assert "verification row written" in note
    manifest = seal_as_sealer(w)
    assert manifest is not None
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 1
    assert _replay_as_sealer(w, manifest) == manifest                    # a replay of the seal is idempotent under every guard
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal").fetchone()[0] == 1


def test_a_second_verification_run_replaces_the_first_before_the_seal(cbuilt):
    """The verification runner can be re-run before a seal (the failed-halfway case): the second run REPLACES the first (one row per grain / class,
    never two) — which is what the verifier's DELETE on the inventory-verification table is for."""
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
    _store_without_verification_delete(monkeypatch)
    _widened_geometry(monkeypatch)
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
    with as_role(w.conn, cw.OWNER):
        w.step(f"verify:{CLS}")                         # 1206's inventory verification only (no window gate exists yet)
        manifest = _seal(w)                             # sealed under 1206's trigger alone
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
    with pytest.raises(RuntimeError, match="no objective/qualification provenance"):
        verify_as_verifier(w)
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_verification").fetchone()[0] == 0
    with pytest.raises(Exception, match="SEALED|sealed"):
        with as_role(w.conn, cw.BUILDER):
            w.step(f"record:{CLS}:P3")
    # a replay of the seal is IDEMPOTENT (1240: "a generation sealed before 1240 replays cleanly") — it returns the same manifest, adds no row
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


def _seal_on(conn):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(conn, CHART_ID, GEN)
        return conn.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN)).fetchone()[0]


def _p3_records(conn):
    return conn.execute("SELECT count(*) FROM public.ka_gochara_relationship_record WHERE event_class = %s AND path_id = 'P3'",
                        (CLS,)).fetchone()[0]


def test_a_builder_rebuild_in_flight_makes_a_racing_seal_wait_then_refuses_it(cbuilt):
    """The builder holds the chart lock mid-rebuild (it deleted the P3 record grain, uncommitted); the sealer's seal BLOCKS on the chart
    lock instead of sealing a half-replaced set, and once the rebuild commits the seal is REFUSED (verification stale or missing)."""
    import psycopg
    w = cbuilt
    verify_as_verifier(w)                                            # a fully verified, unsealed generation
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
        sealer.execute("SELECT public.ka_gochara_seal_generation(%s::uuid, %s)", (CHART_ID, GEN))
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
