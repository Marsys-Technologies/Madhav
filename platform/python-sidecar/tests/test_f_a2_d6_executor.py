"""The F-A2 D6 executor (00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening/d6_f_a2_key_widening_DRAFT.py).

Reviewed blocker (#2858): the executor ran under `SET LOCAL search_path = pg_catalog, pg_temp`, where
`pg_get_triggerdef` prints schema-QUALIFIED text, so the trigger-attestation digest it stored differed from the one
the deploy gate (data-plane-ownership-status.ts) recomputes under the DEFAULT search_path. After COMMIT the gate threw
"Protected trigger inventory or definition drift detected", while the executor's own check (same path) said ALL HOLD.

These tests:
 * reproduce that mismatch (digest under the old path != digest under the gate's path) and prove the executor now
   catches it as a commit condition (the OLD executor has no `SEARCH_PATH` / `gate_mirror` and returns True);
 * prove the apply on the fixed path leaves the gate's own queries false, recomputed independently under the default path;
 * cover the HARD RULE check (writer deploys first) without a database, and that the gate queries/lists are copies of the
   gate's source.

The database tests are opt-in: set F_A2_PG_DSN to a SUPERUSER DSN of a DISPOSABLE cluster; they create and drop their own
database. The model is a stand-in built from the same statements the plan uses (a function carrying the one hunk, the
guard/capture triggers, the attestation tables with their append-only triggers); it is run as a NON-superuser administrator
with no table privilege, as production's administrator is.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
EXEC = REPO / "00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening/d6_f_a2_key_widening_DRAFT.py"


def _load():
    spec = importlib.util.spec_from_file_location("d6_f_a2_exec", EXEC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


d6 = _load()
COMMIT = "0123456789abcdef0123456789abcdef01234567"


# --------------------------------------------------------------------------- no database needed

def _runner(image_tag: str, digest: str):
    def run(argv: list[str]) -> str:
        if argv[0] == "gcloud":
            return f"asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:{image_tag}"
        if argv[0] == "git":
            return json.dumps({"writers": {"ga_vargas": digest}})
        raise AssertionError(argv)
    return run


def test_writer_first_rule_passes_only_for_the_new_writer_image() -> None:
    problems, line = d6.writer_check(COMMIT, _runner(COMMIT, d6.WRITER_DIGEST))
    assert problems == [] and COMMIT[:12] in line
    # the job still runs an older image
    problems, _ = d6.writer_check(COMMIT, _runner("f" * 40, d6.WRITER_DIGEST))
    assert any("not commit" in p for p in problems)
    # the commit's inventory carries a different ga_vargas digest (writer changed after the plan was frozen)
    problems, _ = d6.writer_check(COMMIT, _runner(COMMIT, "0" * 64))
    assert any("frozen against" in p for p in problems)


def test_writer_first_rule_fails_closed() -> None:
    assert d6.writer_check(None)[0], "no --writer-commit: refuse"

    def broken(argv: list[str]) -> str:
        raise RuntimeError("gcloud failed: permission denied")

    problems, line = d6.writer_check(COMMIT, broken)
    assert problems and line == "UNVERIFIED"


def _ts_query(name: str) -> str:
    text = (REPO / "platform/scripts/data-plane-ownership-status.ts").read_text(encoding="utf-8")
    m = re.search(r"const %s = await pool\.query<\{ unsafe: boolean \}>\(`(.*?)`" % name, text, re.S)
    assert m, f"{name} not found in data-plane-ownership-status.ts"
    return m.group(1)


def _squash(sql: str) -> str:
    return re.sub(r"\s+", "", sql)


def test_the_gate_queries_equal_the_gates_own_source_after_normalisation() -> None:
    """Real drift fails: the three queries are compared with the gate's source, placeholders and %% normalised."""
    ts_shape = _ts_query("triggerShape").replace("$1::text[]", "%(tables)s::text[]")
    ts_surface = _ts_query("triggerSurface").replace("$1::text[]", "%(tables)s::text[]")
    ts_fn = _ts_query("functionDigests").replace("$1::text[]", "%(owners)s::text[]").replace("$2::text[]", "%(lifecycle)s::text[]")
    assert _squash(d6.GATE_TRIGGER_SHAPE.replace("%%", "%")) == _squash(ts_shape.replace("%%", "%"))
    assert _squash(d6.GATE_TRIGGER_SURFACE) == _squash(ts_surface)
    assert _squash(d6.GATE_FUNCTION_DIGESTS.replace("%%", "%")) == _squash(ts_fn)


def test_the_lifecycle_function_list_equals_the_gates_own_argument() -> None:
    text = (REPO / "platform/scripts/data-plane-ownership-status.ts").read_text(encoding="utf-8")
    seg = text[text.index("const functionDigests"):]
    args = seg[seg.index("`, [") + 3:]               # the parameter arrays that follow the query text
    lists = re.findall(r"\[([^\[\]]*)\]", args)
    assert lists[0].count("data_plane_l1_owner") == 1 and lists[0].count("data_plane_l2_owner") == 1
    names = tuple(re.findall(r"'([a-z0-9_]+)'", lists[1]))
    assert names == d6.GATE_LIFECYCLE_FUNCTIONS


def test_gate_table_lists_are_parsed_strictly() -> None:
    tables = d6.load_gate_tables(REPO)
    assert (tables.count("chart_divisionals"), len(tables)) == (1, 41)
    assert "bodha_msr_signals" in tables


def _fake_root(tmp_path: pathlib.Path, body: str) -> pathlib.Path:
    f = tmp_path / "platform/scripts"
    f.mkdir(parents=True)
    (f / "data-plane-ownership-preflight.ts").write_text(body, encoding="utf-8")
    return tmp_path


def test_gate_table_parse_refuses_empty_missing_or_miscounted_lists(tmp_path: pathlib.Path) -> None:
    l2 = ", ".join(f"'t{i}'" for i in range(29))
    l1 = ", ".join(f"'c{i}'" for i in range(11)) + ", 'chart_divisionals'"
    good = f"export const L1_ACTIVE_TABLES = [{l1}] as const\nexport const L2_ACTIVE_TABLES = [{l2}] as const\n"
    assert len(d6.load_gate_tables(_fake_root(tmp_path / "ok", good))) == 41
    with pytest.raises(SystemExit, match="EMPTY"):
        d6.load_gate_tables(_fake_root(tmp_path / "e", good.replace(f"[{l1}]", "[]")))
    with pytest.raises(SystemExit, match="chart_divisionals"):
        d6.load_gate_tables(_fake_root(tmp_path / "m", good.replace("'chart_divisionals'", "'chart_other'")))
    with pytest.raises(SystemExit, match="unexpected gate table counts"):
        d6.load_gate_tables(_fake_root(tmp_path / "c", good.replace(", 't28'", "")))
    # a quoted name inside a comment must not be counted
    with_comment = good.replace("export const L2", "// 'chart_divisionals' 'ghost'\nexport const L2")
    assert "ghost" not in d6.load_gate_tables(_fake_root(tmp_path / "k", with_comment))


def test_writer_commit_must_be_the_full_sha_and_the_tag_must_equal_it() -> None:
    for short in ("0", "abcdef0", COMMIT[:12], COMMIT.upper()):
        problems, line = d6.writer_check(short, _runner(short, d6.WRITER_DIGEST))
        assert problems and line == "REFUSED", short
    zero = "0" * 40
    # a one-character tag (and an empty tag) must not satisfy the check
    for tag in ("0", "", zero[:12]):
        problems, _ = d6.writer_check(zero, _runner(tag, d6.WRITER_DIGEST))
        assert any("not commit" in p for p in problems), tag
    assert d6.writer_check(zero, _runner(zero, d6.WRITER_DIGEST))[0] == []


def test_apply_requires_the_writer_commit_and_the_search_path_keeps_names_unqualified() -> None:
    assert d6.SEARCH_PATH.split(",")[1].strip() == "public", "pg_get_triggerdef must stay unqualified"
    assert d6.GATE_SEARCH_PATH == "public"
    src = EXEC.read_text(encoding="utf-8")
    assert "--apply requires --writer-commit" in src
    assert "SET LOCAL search_path = pg_catalog, pg_temp" not in src


# --------------------------------------------------------------------------- disposable PostgreSQL

DSN = os.environ.get("F_A2_PG_DSN")
needs_pg = pytest.mark.skipif(not DSN, reason="set F_A2_PG_DSN to a superuser DSN of a disposable cluster")
DB = "f_a2_d6_executor_test"
TABLES = ["chart_divisionals"]


def _dsn(db: str, user: str | None = None) -> str:
    import psycopg.conninfo as ci
    info = ci.conninfo_to_dict(DSN)
    info["dbname"] = db
    if user:
        info["user"] = user
    return ci.make_conninfo(**info)


FN_BODY = f"""CREATE FUNCTION public.l1_data_plane_capture_row() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp AS $fn$
BEGIN
  /* model of the ga_vargas dependency-identity hunk (migration 1035)
{d6.HUNK_OLD_KEY}  */
  RETURN NEW;
END
$fn$"""


def _build_model() -> None:
    import psycopg
    with psycopg.connect(_dsn("postgres"), autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")
        c.execute(f"CREATE DATABASE {DB}")
        for r in ("data_plane_l1_owner", "data_plane_l2_owner", "amjis_app", "data_plane_builder"):
            c.execute(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{r}') THEN CREATE ROLE {r} NOLOGIN; END IF; END $$")
        c.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='f_a2_admin') "
                  "THEN CREATE ROLE f_a2_admin LOGIN CREATEROLE; END IF; END $$")
        c.execute(f"GRANT CONNECT ON DATABASE {DB} TO f_a2_admin")
    with psycopg.connect(_dsn(DB), autocommit=True) as c:
        c.execute("CREATE EXTENSION pgcrypto")
        # live reality: the administrator has no USAGE on schema public (and no table privilege); only the roles that
        # work in it do
        c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
        c.execute("GRANT USAGE, CREATE ON SCHEMA public TO data_plane_l1_owner, data_plane_l2_owner")
        c.execute("GRANT USAGE ON SCHEMA public TO amjis_app, data_plane_builder")
        c.execute("SET ROLE data_plane_l1_owner")
        c.execute("""CREATE TABLE public.chart_divisionals (id uuid DEFAULT gen_random_uuid() PRIMARY KEY, chart_id uuid NOT NULL,
                     build_id text NOT NULL DEFAULT 'b', graha text, ayanamsha_id text, varga text, fact_category text,
                     fact_key text, fact_subject text)""")
        c.execute("CREATE UNIQUE INDEX chart_divisionals_unique_idx ON public.chart_divisionals "
                  "(chart_id, graha, ayanamsha_id, varga, fact_category, fact_key) NULLS NOT DISTINCT")
        c.execute("INSERT INTO public.chart_divisionals (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject) "
                  "SELECT '482012f1-710e-4a25-994a-93821f5871aa', 'Sun', 'lahiri', 'D1', 'varga_position', 'k'||g, 'D1.S'||g "
                  "FROM generate_series(1,20) g")
        c.execute(FN_BODY)
        for fn in ("l1_data_plane_guard_active_mutation", "l2_data_plane_guard_active_mutation", "l2_data_plane_capture_row",
                   "l1_data_plane_reject_immutable_change"):
            c.execute(f"CREATE FUNCTION public.{fn}() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER "
                      "SET search_path = pg_catalog, public, pg_temp AS $f$ BEGIN RETURN NEW; END $f$")
        c.execute("CREATE TRIGGER l1_data_plane_capture AFTER INSERT OR UPDATE ON public.chart_divisionals FOR EACH ROW "
                  "EXECUTE FUNCTION public.l1_data_plane_capture_row('chart_id','graha','ayanamsha_id','varga','fact_category','fact_key')")
        c.execute("CREATE TRIGGER l1_data_plane_mutation_guard BEFORE INSERT OR UPDATE OR DELETE ON public.chart_divisionals "
                  "FOR EACH ROW EXECUTE FUNCTION public.l1_data_plane_guard_active_mutation()")
        # live ACL (read as suvarna_reader): the L1 attestation tables belong to the L1 owner, the L2 ones to the L2 owner,
        # and data_plane_l1_owner has NO SELECT on the L2 tables; amjis_app has SELECT on all four
        for layer, owner in (("l1", "data_plane_l1_owner"), ("l2", "data_plane_l2_owner")):
            c.execute(f"SET ROLE {owner}")
            c.execute(f"""CREATE TABLE public.{layer}_data_plane_trigger_attestations (table_name text NOT NULL, trigger_name text NOT NULL,
                         trigger_type smallint NOT NULL, enabled "char" NOT NULL, function_oid oid NOT NULL,
                         function_signature text NOT NULL, definition_digest text NOT NULL, PRIMARY KEY(table_name, trigger_name))""")
            c.execute(f"""CREATE TABLE public.{layer}_data_plane_function_attestations (function_signature text PRIMARY KEY,
                         definition_digest text NOT NULL, owner_name text NOT NULL, security_definer boolean NOT NULL, config text[])""")
            c.execute(f"GRANT SELECT ON public.{layer}_data_plane_trigger_attestations, public.{layer}_data_plane_function_attestations TO amjis_app")
            c.execute("RESET ROLE")
        c.execute("SET ROLE data_plane_l1_owner")
        # the attestations, computed the way the gate computes them: under the DEFAULT search_path
        c.execute("SET search_path = public")
        c.execute("""INSERT INTO public.l1_data_plane_trigger_attestations
                     SELECT c.relname,t.tgname,t.tgtype,t.tgenabled,t.tgfoid,t.tgfoid::regprocedure::text,
                            encode(digest(pg_get_triggerdef(t.oid,true),'sha256'),'hex')
                     FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE NOT t.tgisinternal AND c.relname='chart_divisionals'""")
        c.execute("""INSERT INTO public.l1_data_plane_function_attestations
                     SELECT regexp_replace(p.oid::regprocedure::text, '^public\\.', ''),
                            encode(digest(pg_get_functiondef(p.oid),'sha256'),'hex'), pg_get_userbyid(p.proowner), p.prosecdef, p.proconfig
                     FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                     WHERE n.nspname='public' AND (p.proname LIKE 'l1\\_data\\_plane\\_%' OR p.proname LIKE 'l2\\_data\\_plane\\_%')""")
        c.execute("SET search_path = DEFAULT")
        for t in ("l1_data_plane_trigger_attestations", "l1_data_plane_function_attestations"):
            c.execute(f"CREATE TRIGGER {t}_immutable BEFORE UPDATE OR DELETE ON public.{t} FOR EACH ROW "
                      "EXECUTE FUNCTION public.l1_data_plane_reject_immutable_change()")
        c.execute("RESET ROLE")
        c.execute("CREATE TABLE public.build_runs (id serial, chart_id uuid, state text)")
        c.execute("ALTER TABLE public.build_runs OWNER TO amjis_app")
        c.execute("CREATE TABLE public.l1_data_plane_generations (status text)")
        c.execute("ALTER TABLE public.l1_data_plane_generations OWNER TO data_plane_l1_owner")


@pytest.fixture()
def model():
    _build_model()
    yield
    import psycopg
    with psycopg.connect(_dsn("postgres"), autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")


def _apply(**kw):
    import psycopg
    out: list[str] = []
    with psycopg.connect(_dsn(DB, "f_a2_admin")) as conn:
        ok = d6.run(conn, "apply", out=out.append, writer_commit=COMMIT, gate_tables=TABLES,
                    writer_runner=_runner(COMMIT, d6.WRITER_DIGEST))
        if ok:
            conn.commit()
        else:
            conn.rollback()
    return ok, "\n".join(out)


def _gate_state_under_default_path() -> tuple[bool, bool, bool]:
    """The gate's own queries, recomputed in a fresh session with the DEFAULT search_path, as the owner."""
    import psycopg
    with psycopg.connect(_dsn(DB), autocommit=False) as conn:
        cur = conn.cursor()
        g = d6.gate_mirror(cur, TABLES)
        stored_matches = (g["trigger_digest_stored"] == g["trigger_digest_gate_side"],
                          g["function_digest_stored"] == g["function_digest_gate_side"],
                          not d6.gate_red(g))
        conn.rollback()
    return stored_matches


@needs_pg
def test_the_old_search_path_really_produces_a_different_trigger_digest(model) -> None:
    import psycopg
    with psycopg.connect(_dsn(DB), autocommit=True) as c:
        c.execute("SET search_path = pg_catalog, pg_temp")
        old = c.execute("SELECT pg_get_triggerdef(t.oid,true) FROM pg_trigger t WHERE tgname='l1_data_plane_capture'").fetchone()[0]
        c.execute("SET search_path = public")
        new = c.execute("SELECT pg_get_triggerdef(t.oid,true) FROM pg_trigger t WHERE tgname='l1_data_plane_capture'").fetchone()[0]
    assert "ON public.chart_divisionals" in old and "EXECUTE FUNCTION public.l1_data_plane_capture_row(" in old
    assert "ON chart_divisionals" in new and "EXECUTE FUNCTION l1_data_plane_capture_row(" in new
    assert old != new, "the root cause: the same trigger text differs by search_path, so does its digest"


@needs_pg
def test_apply_on_the_fixed_path_leaves_the_deploy_gate_green(model) -> None:
    assert _gate_state_under_default_path() == (True, True, True), "model is gate-green before the plan"
    ok, out = _apply()
    assert ok, out
    assert "commit conditions: ALL HOLD" in out
    assert "trigger_surface_unsafe=False" in out and "function_digests_unsafe=False" in out
    # independent recomputation in a fresh default-path session AFTER the commit
    assert _gate_state_under_default_path() == (True, True, True)


@needs_pg
def test_the_executor_now_refuses_what_the_old_executor_committed(model, monkeypatch) -> None:
    """Run the plan under the OLD search_path: the stored trigger digest is of the qualified text, so the gate would go
    RED after commit. The old executor (no gate check, same-path recompute) returned ALL HOLD here; this one must not."""
    monkeypatch.setattr(d6, "SEARCH_PATH", "pg_catalog, pg_temp")
    ok, out = _apply()
    assert ok is False
    assert "DEPLOY GATE WOULD GO RED" in out or "gate computes under its own search_path" in out, out
    # nothing was committed: the model is still the six-column, gate-green state
    import psycopg
    with psycopg.connect(_dsn(DB), autocommit=True) as c:
        idx = c.execute("SELECT indexdef FROM pg_indexes WHERE indexname='chart_divisionals_unique_idx'").fetchone()[0]
    assert "fact_subject" not in idx


@needs_pg
def test_apply_is_refused_when_another_chart_has_a_run_or_the_writer_is_not_deployed(model) -> None:
    import psycopg
    with psycopg.connect(_dsn(DB), autocommit=True) as c:
        c.execute("INSERT INTO public.build_runs(state, chart_id) VALUES ('running', '1c826d5a-41cb-4450-b4dc-59d440e5f75a')")
    ok, out = _apply()
    assert ok is False and "ANY chart" in out
    with psycopg.connect(_dsn(DB), autocommit=True) as c:
        c.execute("DELETE FROM public.build_runs")
    with psycopg.connect(_dsn(DB, "f_a2_admin")) as conn:
        out2: list[str] = []
        ok2 = d6.run(conn, "apply", out=out2.append, writer_commit=COMMIT, gate_tables=TABLES,
                     writer_runner=_runner("e" * 40, d6.WRITER_DIGEST))
        conn.rollback()
    assert ok2 is False and any("not commit" in line for line in out2)


@needs_pg
def test_the_model_is_live_faithful_and_would_have_caught_the_l1_owner_gate_role(model) -> None:
    """F1 (second review): the gate unions the L2 attestation tables, which data_plane_l1_owner cannot read. The model now
    reflects the live ACLs, so running the gate's query AS the L1 owner fails exactly as production would, while the
    executor (which runs it as amjis_app) is green."""
    import psycopg
    with psycopg.connect(_dsn(DB)) as conn:
        cur = conn.cursor()
        cur.execute("SET LOCAL ROLE data_plane_l1_owner")
        cur.execute("SET LOCAL search_path = public")
        with pytest.raises(psycopg.errors.InsufficientPrivilege, match="l2_data_plane"):
            cur.execute(d6.GATE_TRIGGER_SURFACE, {"tables": TABLES})
        conn.rollback()
    with psycopg.connect(_dsn(DB, "f_a2_admin")) as conn:
        cur = conn.cursor()
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("SELECT count(*) FROM public.chart_divisionals")  # the administrator holds no table privilege
        conn.rollback()
    assert _gate_state_under_default_path() == (True, True, True)


@needs_pg
def test_a_building_l1_generation_refuses_the_plan(model) -> None:
    import psycopg
    with psycopg.connect(_dsn(DB), autocommit=True) as c:
        c.execute("INSERT INTO public.l1_data_plane_generations(status) VALUES ('building')")
    ok, out = _apply()
    assert ok is False and "still 'building'" in out


@needs_pg
def test_a_short_tag_cannot_commit_the_plan(model) -> None:
    import psycopg
    zero = "0" * 40
    with psycopg.connect(_dsn(DB, "f_a2_admin")) as conn:
        out: list[str] = []
        ok = d6.run(conn, "apply", out=out.append, writer_commit=zero, gate_tables=TABLES,
                    writer_runner=_runner("0", d6.WRITER_DIGEST))
        conn.rollback()
    assert ok is False and any("not commit" in line for line in out)


@needs_pg
def test_the_exclusive_window_is_kept_short_and_measured(model) -> None:
    ok, out = _apply()
    assert ok, out
    m = re.search(r"ACCESS EXCLUSIVE window \(UTC\): \S+ -> \S+; statements inside it: (\d+)", out)
    assert m, out
    assert int(m.group(1)) <= 60, f"{m.group(1)} statements hold ACCESS EXCLUSIVE; keep the window short"
    # the before-snapshot, the probe inserts and the gate-before check all ran BEFORE the window
    assert out.index("writer-first check") < out.index("ACCESS EXCLUSIVE window")

