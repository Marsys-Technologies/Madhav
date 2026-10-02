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
History: the first two runs carried strict xfails for two Stream A defects this rehearsal found (R9-6.1: the inventory store deleted the verification table as the
builder; R9-10: the P1 anchor certification expected Moon contacts the stored non-Moon scope never writes) and one fixed stand-in (R9-9, the geometry probe margin).
All three are fixed in Stream A's code; no stand-in and no xfail remains: every test runs Stream A's code as shipped.
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
    """A FRESH production-ordered world (no build yet), Stream A's code as shipped (no stand-in anywhere in this module)."""
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


def verify_as_verifier(w, *extra_args, dsn=None, all_classes=False):
    """Stream A's REAL verification job (`pipeline/orchestrator/verification_job.py`), run as a real verifier LOGIN with the REAL 1241 grants and
    no stand-in: the job proves its own identity, records the four window verifications FIRST and then the inventory verification. Returns the
    parsed report; raises RuntimeError on any non-zero exit (a refusal or a disagreement)."""
    import io
    import json as _json
    from contextlib import redirect_stdout
    from pipeline.orchestrator import verification_job as job
    w.conn.execute(f"ALTER ROLE {cw.VERIFIER} LOGIN")
    os.environ[job.ENV_URL] = dsn or _verifier_dsn(w)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = job.main(["--chart", CHART_ID, "--generation", GEN, *([] if all_classes else ["--class", CLS]), "--ephe-path", EPHE, *extra_args])
    finally:
        os.environ.pop(job.ENV_URL, None)
        w.conn.execute(f"ALTER ROLE {cw.VERIFIER} NOLOGIN")
    out = buf.getvalue().strip()
    if rc != 0:
        raise RuntimeError(f"verification job exit {rc}: {out[:700]} ... {out[-900:]}" if len(out) > 1700 else f"verification job exit {rc}: {out}")
    return _json.loads(out.splitlines()[-1]) if out else {}


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
    assert len(_G1241) == len(set(_G1241)) == 47, len(_G1241)   # sealer: 11 table (incl. the column-level windows read and publication update) + 18 function; verifier: 8 table + 10 function (R10-4 iii: the job's final combined gate)


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
    with pytest.raises(RuntimeError, match=r"permission denied|no_verifier_privilege"):
        verify_as_verifier(w)
        manifest = seal_as_sealer(w)
        _replay_as_sealer(w, manifest)


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
    with pytest.raises(RuntimeError, match=r"permission denied|verification job exit|refused"):
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
                            (f"GRANT SELECT (chart_id) ON public.kala_gochara_contacts TO {cw.VERIFIER}", r"SELECT \(chart_id\) on kala_gochara_contacts: PROHIBITED")):
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
        n = w.conn.execute("SELECT count(*) FROM public.kala_gochara_windows WHERE chart_id = %s AND generation = '5.0'", (CHART_ID,)).fetchone()[0]
        assert n == 2                                            # the count ledger.publish records
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            w.conn.execute("SELECT raw_intensity FROM public.kala_gochara_windows LIMIT 1")


def test_first_seal_builder_then_verifier_then_sealer_with_every_guard_enabled(cbuilt):
    import psycopg
    w = cbuilt
    # before any verification the candidate gate is CLOSED and the seal is refused (the honest "built, not verified" state)
    with pytest.raises(psycopg.errors.Error):
        seal_as_sealer(w)
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
    with pytest.raises(RuntimeError, match="verification job exit [2345]"):             # the real job REFUSES (nothing written)
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
        seal_as_sealer(w)


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
        seal_as_sealer(w)
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
        seal_as_sealer(w)


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
        seal_as_sealer(w)


@pytest.mark.xfail(strict=True, reason="FINDING R11-cand-1 (Stream A, verification_job.run): a GENERATION-level gate violation (event_class '*': input_vector_mismatch, "
                   "convention_bridge_missing, convention_mismatch) is classified `gate_outside_scope` on a --class SUBSET run — the filter tests `event_class is None`, but the "
                   "violations carry '*' — so a subset run reports status VERIFIED / gate [] / exit 0 with a generation-level violation open. The seal still refuses; a full run reports it.")
def test_attack_a_subset_run_must_not_report_verified_with_a_generation_level_violation_open(cbuilt):
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
